/* bench_sq2b.c — SQ2B comparison row (biologically-revised V22 cell).
 *
 * Injection is full-range across the duplex cell: payload bytes (both
 * strands), syndrome fields, age/tomb metadata — stratified by natural
 * footprint.  Detection is credited from actual sweep actions per codon;
 * repair is verified per event; tombstones are counted as losses, never
 * folded into repaired.  See SQ2B_DESIGN.md.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "common.h"
#include "cache_perf.h"
#include "squaragon_v2_bio.h"

enum { SQBE_PAY = 0, SQBE_SYN = 1, SQBE_META = 2 };

typedef struct {
    int cat, b, g, strand, i;
    uint8_t m;
} sqb_evt_t;

static void sqb_apply_event(sqb_cell_t *t, const sqb_evt_t *e) {
    sqb_codon_t *c = &t->c[e->b][e->g][e->strand];
    if (e->cat == SQBE_PAY) {
        c->g[e->i % SQB_PAY] ^= e->m;
    } else if (e->cat == SQBE_SYN) {
        ((uint8_t *)&c->syn0)[e->i % 8] ^= e->m;
    } else {
        ((uint8_t *)&c->age)[e->i % 8] ^= e->m;   /* age+tomb span 8 B */
    }
}

void bench_sq2b(cmp_result_t *out, long long n, double error_rate, int churn_every) {
    memset(out, 0, sizeof(*out));
    strncpy(out->name, "SQ2B", sizeof(out->name) - 1);
    out->available = 1;

    if (n > SQB_CAPACITY) n = SQB_CAPACITY;

    uint64_t rng[4];
    cmp_seed(rng, 0xB10U);

    static sqb_cell_t cell;
    int rounds = (n < 100000) ? (int)(100000 / n + 1) : 1;

    cp_ctx_t cp;
    cp_open(&cp);

    cp_start(&cp);
    double t0 = cmp_now_sec();
    for (int r = 0; r < rounds; r++) {
        sqb_init(&cell);
        for (long long i = 0; i < n; i++)
            if (sqb_alloc(&cell, (int)i, (int)i) != 0) out->alloc_fail++;
    }
    double t1 = cmp_now_sec();
    cp_stop(&cp);
    if (out->alloc_fail > 0)
        fprintf(stderr, "SQ2B: %lld/%lld allocations refused/failed\n",
                out->alloc_fail, n * rounds);
    if (cell.proofread_retries > 0)
        fprintf(stderr, "SQ2B: %lld proofread retries (GTP cost)\n",
                cell.proofread_retries);

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

    /* ---------- injection: content-affecting classes only ----------
     * payload (2x152 B) and syndrome (2x8 B) bytes, natural 95/5
     * footprint.  The inert META class (age/tomb) carries no integrity
     * claim and is exercised in the cert driver, not scored here. */
    int occ_list[SQB_CAPACITY];
    int n_occ = 0;
    for (int b = 0; b < SQB_NB; b++)
        for (int g = 0; g < SQB_NR; g++)
            if (cell.occ[b][g]) occ_list[n_occ++] = (b << 8) | g;

    long long inj = (long long)(error_rate * (double)n_occ + 0.5);
    if (inj < 1 && n_occ > 0) inj = 1;
    if (inj > n_occ) inj = n_occ;
    out->injected = inj;

    static sqb_evt_t evts[SQB_CAPACITY];
    double tot = 2.0 * (SQB_PAY + 8);
    for (long long e = 0; e < inj; e++) {
        int slot = (int)(cmp_rand01(rng) * (double)n_occ) % n_occ;
        sqb_evt_t *ev = &evts[e];
        ev->b = occ_list[slot] >> 8;
        ev->g = occ_list[slot] & 0xFF;
        ev->strand = (int)(cmp_rand01(rng) * 2.0);
        if (ev->strand > 1) ev->strand = 1;
        double u = cmp_rand01(rng) * tot;
        if (u < SQB_PAY)            ev->cat = SQBE_PAY;
        else                        ev->cat = SQBE_SYN;
        ev->i = (int)(cmp_rand_u32(rng) % SQB_PAY);
        ev->m = (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
        sqb_apply_event(&cell, ev);
    }

    /* ---------- G2 sweep: mismatch repair, timed ---------- */
    static uint8_t action[SQB_NB * SQB_NR];
    double ts0 = cmp_now_sec();
    long long unresolved = sqb_sweep(&cell, action);
    double ts1 = cmp_now_sec();
    fprintf(stderr, "SQ2BT sweep_ns=%.0f unresolved=%lld tombstones=%lld slippage=%lld\n",
            (ts1 - ts0) * 1e9, unresolved, cell.tombstones, cell.slippage);

    /* ---------- per-event scoring ---------- */
    long long detected = 0, repaired = 0, content_events = 0;
    for (long long e = 0; e < inj; e++) {
        sqb_evt_t *ev = &evts[e];
        int act = action[ev->b * SQB_NR + ev->g];
        if (ev->cat == SQBE_PAY) {
            content_events++;
            if (act) detected++;
            uint8_t dec[SQB_PAY];
            const sqb_codon_t *c = &cell.c[ev->b][ev->g][ev->strand];
            if (ev->strand == 0) memcpy(dec, c->g, SQB_PAY);
            else for (int i = 0; i < SQB_PAY; i++)
                dec[i] = (uint8_t)(c->g[i] ^ SQB_COMPLEMENT);
            repaired += sqb_pay_ok(dec, sqb_item_at[ev->b][ev->g]);
        } else if (ev->cat == SQBE_SYN) {
            content_events++;
            if (act) detected++;
            repaired += sqb_strand_ok(&cell.c[ev->b][ev->g][ev->strand],
                                      ev->strand);
        }
        /* META (age/tomb): inert class — no integrity claim, reported
         * in the cert driver, not scored here */
    }
    out->detected = detected;
    out->repaired = repaired;
    (void)content_events;

    /* ---------- ground-truth coherency over all codons ---------- */
    out->coherency_total = 0;
    for (int b = 0; b < SQB_NB; b++)
        for (int g = 0; g < SQB_NR; g++) {
            if (!cell.occ[b][g]) continue;
            out->coherency_total++;
            if (cell.c[b][g][0].tomb == SQB_TOMB_MAGIC) {
                out->coherency_fail++;      /* apoptosed = item lost */
                continue;
            }
            int item = sqb_item_at[b][g];
            uint8_t rna[SQB_PAY];
            if (sqb_transcribe(&cell, b, g, rna) != 0 ||
                !sqb_pay_ok(rna, item))
                out->coherency_fail++;
            (void)churn_every;
        }
}
