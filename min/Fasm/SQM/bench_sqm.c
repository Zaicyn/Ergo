/* bench_sqm.c — SQM comparison row: moment-Merkle minimal-read writes.
 *
 * Workload: n items written, then rewritten R times with SQM_MUT
 * bytes mutated per rewrite (default 1).  Timed region covers the
 * rewrite stream (the regime the design targets).  Instrumentation
 * (SQMT stderr): skip/sec/half/full counts and actual bytes
 * read/written — the amplification numbers are the point.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "common.h"
#include "cache_perf.h"
#include "sqm_core.h"

#ifndef SQM_MUT
#define SQM_MUT 1
#endif
#ifndef SQM_ROUNDS
#define SQM_ROUNDS 400
#endif

void bench_sqm(cmp_result_t *out, long long n, double error_rate, int churn_every) {
    memset(out, 0, sizeof(*out));
    strncpy(out->name, "SQM", sizeof(out->name) - 1);
    out->available = 1;

    if (n > SQM_CAPACITY) n = SQM_CAPACITY;

    uint64_t rng[4];
    cmp_seed(rng, 0x3A11U);

    static sqm_cell_t cell;
    static uint8_t contents[SQM_CAPACITY][SQM_PAY];
    sqm_init(&cell);
    for (long long i = 0; i < n; i++) {
        sqm_fill(contents[i], (int)i);
        if (sqm_write(&cell, (int)i, (int)i, contents[i]) != 0)
            out->alloc_fail++;
    }

    /* rewrite stream with SQM_MUT mutations per write */
    cp_ctx_t cp;
    cp_open(&cp);
    cp_start(&cp);
    double t0 = cmp_now_sec();
    long long total = 0;
    for (int r = 0; r < SQM_ROUNDS; r++) {
        for (long long i = 0; i < n; i++) {
            for (int k = 0; k < SQM_MUT; k++) {
                int pos = (int)(cmp_rand_u32(rng) % SQM_PAY);
                contents[i][pos] ^= (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
            }
            sqm_write(&cell, (int)i, (int)i, contents[i]);
            total++;
        }
    }
    double t1 = cmp_now_sec();
    cp_stop(&cp);

    out->items = total;
    out->alloc_sec = t1 - t0;
    out->alloc_mips = (double)total / out->alloc_sec / 1e6;
    out->ns_per_item = out->alloc_sec * 1e9 / (double)total;
    out->cache_available = cp.available;
    out->l1d_loads = cp.after[CP_L1D_LOADS];
    out->l1d_misses = cp.after[CP_L1D_MISSES];
    out->llc_refs = cp.after[CP_LLC_REFS];
    out->llc_misses = cp.after[CP_LLC_MISSES];
    out->instructions = cp.after[CP_INSTRS];
    cp_close(&cp);

    fprintf(stderr,
            "SQMT mut=%d skip=%lld sec=%lld half=%lld full=%lld | rd=%lld wr=%lld bytes (%.2f rd %.2f wr per write)\n",
            SQM_MUT, cell.skips, cell.sec_writes, cell.half_writes,
            cell.full_writes, cell.bytes_read, cell.bytes_written,
            total ? (double)cell.bytes_read / total : 0.0,
            total ? (double)cell.bytes_written / total : 0.0);

    /* correctness: stored content must equal the live buffer exactly */
    out->coherency_total = 0;
    for (int b = 0; b < SQM_NB; b++)
        for (int g = 0; g < SQM_NR; g++) {
            if (!cell.occ[b][g]) continue;
            out->coherency_total++;
            int item = sqm_item_at[b][g];
            if (memcmp(cell.pay[b][g], contents[item], SQM_PAY) != 0)
                out->coherency_fail++;
        }
    out->injected = 0;
    out->detected = 0;
    out->repaired = 0;
    (void)error_rate; (void)churn_every;
}
