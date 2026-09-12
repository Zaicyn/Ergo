/* bench_sqw.c — SQW comparison row: write-skip (memoized) duplex cell.
 *
 * Workload is duplication-parameterized (-DSQW_DUP permille, default
 * 500 = half the logical stream repeats an existing payload).  Logical
 * n items map onto <= SQB_CAPACITY physical codons; write-skips are
 * counted and printed (SQWT stderr line).
 *
 * Injection: full-range over payload + syndrome + refcount bytes
 * (natural footprint).  The recognition cache is also corruptible but
 * is a documented fail-safe inert class (exact-verify arbitrates) and
 * is not scored.  Item-level scoring: every logical item must read its
 * pattern back from its (possibly shared) codon.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "common.h"
#include "cache_perf.h"
#include "sqw_core.h"

#ifndef SQW_DUP
#define SQW_DUP 500   /* permille of the logical stream that duplicates */
#endif

enum { SQWE_PAY = 0, SQWE_SYN = 1, SQWE_REF = 2 };
typedef struct { int cat, b, g, strand, i; uint8_t m; } sqw_evt_t;

static void sqw_apply_event(sqw_cell_t *w, const sqw_evt_t *e) {
    sqb_codon_t *c = &w->cell.c[e->b][e->g][e->strand];
    if (e->cat == SQWE_PAY)      c->g[e->i % SQB_PAY] ^= e->m;
    else if (e->cat == SQWE_SYN) ((uint8_t *)&c->syn0)[e->i % 8] ^= e->m;
    else                         ((uint8_t *)&w->ref[e->b][e->g])[e->i & 3] ^= e->m;
}

void bench_sqw(cmp_result_t *out, long long n, double error_rate, int churn_every) {
    memset(out, 0, sizeof(*out));
    strncpy(out->name, "SQW", sizeof(out->name) - 1);
    out->available = 1;

    if (n > SQB_CAPACITY) n = SQB_CAPACITY;

    uint64_t rng[4];
    cmp_seed(rng, 0xD0B5U);

    /* logical stream: exactly U unique payloads (shuffled), the other
     * n-U draws repeat pool members — controlled duplication, not
     * birthday-collided */
    int U = (int)((long long)n * (1000 - SQW_DUP) / 1000);
    if (U < 1) U = 1;
    static int stream[SQB_CAPACITY];
    for (int i = 0; i < U; i++) stream[i] = i;
    for (int i = U - 1; i > 0; i--) {   /* Fisher-Yates */
        int j = (int)(cmp_rand_u32(rng) % (uint32_t)(i + 1));
        int tmp = stream[i]; stream[i] = stream[j]; stream[j] = tmp;
    }
    for (int i = U; i < n; i++)
        stream[i] = (int)(cmp_rand_u32(rng) % (uint32_t)U);

    static sqw_cell_t w;
    int rounds = (n < 100000) ? (int)(100000 / n + 1) : 1;

    cp_ctx_t cp;
    cp_open(&cp);
    cp_start(&cp);
    double t0 = cmp_now_sec();
    for (int r = 0; r < rounds; r++) {
        sqw_init(&w);
        for (long long i = 0; i < n; i++)
            if (sqw_alloc(&w, (int)i, stream[i]) != 0) out->alloc_fail++;
    }
    double t1 = cmp_now_sec();
    cp_stop(&cp);

    long long total_items = n * rounds;
    out->items = total_items;
    out->alloc_sec = t1 - t0;
    out->alloc_mips = (double)total_items / out->alloc_sec / 1e6;
    out->ns_per_item = out->alloc_sec * 1e9 / (double)total_items;
    out->cache_available = cp.available;
    out->l1d_loads = cp.after[CP_L1D_LOADS];
    out->l1d_misses = cp.after[CP_L1D_MISSES];
    out->llc_refs = cp.after[CP_LLC_REFS];
    out->llc_misses = cp.after[CP_LLC_MISSES];
    out->instructions = cp.after[CP_INSTRS];
    cp_close(&cp);
    fprintf(stderr, "SQWT dup=%d skips=%lld phys=%lld (%.1f%% skipped)\n",
            SQW_DUP, w.skips, w.phys_allocs,
            w.skips + w.phys_allocs ? 100.0 * w.skips / (w.skips + w.phys_allocs) : 0.0);

    /* replication sweep state: cell already holds duplex codons */

    /* ---------- injection: occupied codons, content + ref bytes ------ */
    int occ_list[SQB_CAPACITY];
    int n_occ = 0;
    for (int b = 0; b < SQB_NB; b++)
        for (int g = 0; g < SQB_NR; g++)
            if (w.cell.occ[b][g]) occ_list[n_occ++] = (b << 8) | g;

    long long inj = (long long)(error_rate * (double)n_occ + 0.5);
    if (inj < 3 && n_occ >= 3) inj = 3;   /* floor: keep the row's event
        count comparable across dedup levels (occupancy shrinks with
        write-skip; per-byte threat rate is unchanged) */
    if (inj < 1 && n_occ > 0) inj = 1;
    if (inj > n_occ) inj = n_occ;
    out->injected = inj;

    static sqw_evt_t evts[SQB_CAPACITY];
    for (long long e = 0; e < inj; e++) {
        int slot = (int)(cmp_rand01(rng) * (double)n_occ) % n_occ;
        sqw_evt_t *ev = &evts[e];
        ev->b = occ_list[slot] >> 8;
        ev->g = occ_list[slot] & 0xFF;
        ev->strand = (int)(cmp_rand01(rng) * 2.0);
        if (ev->strand > 1) ev->strand = 1;
        double u = cmp_rand01(rng) * (2.0 * SQB_PAY + 16 + 4);
        if (u < SQB_PAY)            ev->cat = SQWE_PAY;
        else if (u < SQB_PAY + 8)   ev->cat = SQWE_SYN;
        else                        ev->cat = SQWE_REF;
        ev->i = (int)(cmp_rand_u32(rng) % SQB_PAY);
        ev->m = (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
        sqw_apply_event(&w, ev);
    }

    /* ---------- G2 sweep (duplex MMR) + refcount audit, timed -------- */
    static uint8_t action[SQB_NB * SQB_NR];
    double ts0 = cmp_now_sec();
    long long unresolved = sqb_sweep(&w.cell, action);
    int sum_ok = 0;
    long long ref_bad = sqw_ref_audit(&w, &sum_ok);
    double ts1 = cmp_now_sec();
    fprintf(stderr, "SQWT sweep_ns=%.0f unresolved=%lld tombs=%lld ref_bad=%lld refsum_ok=%d\n",
            (ts1 - ts0) * 1e9, unresolved, w.cell.tombstones, ref_bad, sum_ok);

    /* ---------- scoring: content events only; REF is a separate class
     * (detected exactly by the complement pair, unrepairable without
     * the logical map) and is reported on the SQWT audit line ------- */
    long long detected = 0, repaired = 0, content_events = 0;
    for (long long e = 0; e < inj; e++) {
        sqw_evt_t *ev = &evts[e];
        if (ev->cat == SQWE_REF) continue;
        content_events++;
        if (action[ev->b * SQB_NR + ev->g]) detected++;
        uint8_t dec[SQB_PAY];
        const sqb_codon_t *c = &w.cell.c[ev->b][ev->g][ev->strand];
        if (ev->strand == 0) memcpy(dec, c->g, SQB_PAY);
        else for (int i = 0; i < SQB_PAY; i++)
            dec[i] = (uint8_t)(c->g[i] ^ SQB_COMPLEMENT);
        repaired += sqb_pay_ok(dec, sqb_item_at[ev->b][ev->g]);
    }
    out->injected = content_events;
    out->detected = detected;
    out->repaired = repaired;

    /* item-level ground truth: every logical item reads its pattern */
    out->coherency_total = 0;
    for (long long i = 0; i < n; i++) {
        int item = stream[i];
        int b = sqw_item_slot_b[item], g = sqw_item_slot_g[item];
        out->coherency_total++;
        const sqb_codon_t *c0 = &w.cell.c[b][g][0];
        if (c0->tomb == SQB_TOMB_MAGIC || !sqb_pay_ok(c0->g, item))
            out->coherency_fail++;
    }
    (void)churn_every;
}
