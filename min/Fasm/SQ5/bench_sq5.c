/* bench_sq5.c — SQ5 comparison row (uses sq5_core.h).
 *
 * Injection is FULL-RANGE across the whole allocator state, stratified
 * by footprint: payload bytes, stamp bytes, and journal bytes are all
 * corruptible (the check-field coverage the first-pass harness lacked).
 * Detection is credited from actual flux/stamp flags, not assumed;
 * repair is verified post-hoc per event.  See SQ5_CERTIFICATION.md.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "common.h"
#include "cache_perf.h"
#include "sq5_core.h"

/* event categories */
enum { SQ5E_PAY = 0, SQ5E_STAMP = 1, SQ5E_JOUR = 2 };

typedef struct {
    int cat, b, g, shell, i, nbytes;
    uint8_t m[2];            /* XOR masks (pay: per byte; else single) */
} sq5_evt_t;

/* Apply one corruption event (shared semantics with sq5_mirror.py). */
static void sq5_apply_event(sq5_torus_t *t, const sq5_evt_t *e) {
    if (e->cat == SQ5E_PAY) {
        for (int k = 0; k < e->nbytes; k++)
            t->pay[e->b][e->g][e->shell][(e->i + k * 7) % SQ5_PAY] ^= e->m[k];
    } else if (e->cat == SQ5E_STAMP) {
        uint8_t *sp = (uint8_t *)&t->stamp[e->b][e->g][e->shell];
        sp[e->i & 3] ^= e->m[0];
    } else {
        uint8_t *jp = (uint8_t *)&t->jr[e->b][e->shell];
        jp[e->i % (int)sizeof(sq5_journal_t)] ^= e->m[0];
    }
}

void bench_sq5(cmp_result_t *out, long long n, double error_rate, int churn_every) {
    memset(out, 0, sizeof(*out));
    strncpy(out->name, "SQ5", sizeof(out->name) - 1);
    out->available = 1;

    if (n > SQ5_CAPACITY) n = SQ5_CAPACITY;

    uint64_t rng[4];
    cmp_seed(rng, 0x5C5F11U);

    static sq5_torus_t torus;
    int rounds = (n < 100000) ? (int)(100000 / n + 1) : 1;

    cp_ctx_t cp;
    cp_open(&cp);

    /* ---------- allocation: hot path with incremental journaling ------ */
    cp_start(&cp);
    double t0 = cmp_now_sec();
    for (int r = 0; r < rounds; r++) {
        sq5_tin(&torus);
        for (long long i = 0; i < n; i++) {
            if (sq5_alloc(&torus, (int)i, (int)i) != 0) out->alloc_fail++;
        }
    }
    double t1 = cmp_now_sec();
    cp_stop(&cp);
    if (out->alloc_fail > 0)
        fprintf(stderr, "SQ5: %lld/%lld allocations failed (cell full)\n",
                out->alloc_fail, n * rounds);

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

    /* ---------- replication with counterflow flux check ---------------- */
    long long flux_breaks = 0;
    sq5_rep(&torus, &flux_breaks);
    if (flux_breaks > 0)
        fprintf(stderr, "SQ5: %lld flux breaks during replication\n", flux_breaks);

    /* ---------- full-range injection, stratified by footprint ----------
     * Target byte drawn uniformly from (pay | stamp | journal) space, so
     * check fields face corruption at their natural rate.  Payload events
     * are 80% single-byte / 20% double-byte.  Uniqueness per category. */
    int occ_list[SQ5_CAPACITY];
    int n_occ = 0;
    for (int b = 0; b < SQ5_NB; b++)
        for (int g = 0; g < SQ5_NR; g++)
            if (torus.occ[b][g][0]) occ_list[n_occ++] = (b << 8) | g;

    long long inj = (long long)(error_rate * (double)n_occ + 0.5);
    if (inj < 1 && n_occ > 0) inj = 1;
    if (inj > n_occ) inj = n_occ;
    out->injected = inj;

    static sq5_evt_t evts[SQ5_CAPACITY];
    double tot_bytes = (double)(SQ5_PAYBYTES + SQ5_STAMPBYTES + SQ5_JRBYTES);
    double p_pay = SQ5_PAYBYTES / tot_bytes;
    double p_stamp = SQ5_STAMPBYTES / tot_bytes;
    for (long long e = 0; e < inj; e++) {
        double u = cmp_rand01(rng);
        sq5_evt_t *ev = &evts[e];
        if (u < p_pay) {
            int slot = (int)(cmp_rand01(rng) * (double)n_occ) % n_occ;
            ev->cat = SQ5E_PAY;
            ev->b = occ_list[slot] >> 8;
            ev->g = occ_list[slot] & 0xFF;
            ev->shell = (int)(cmp_rand01(rng) * 2.0);
            if (ev->shell > 1) ev->shell = 1;
            ev->nbytes = (cmp_rand01(rng) < 0.8) ? 1 : 2;
            ev->i = (int)(cmp_rand_u32(rng) % SQ5_PAY);
            for (int k = 0; k < ev->nbytes; k++)
                ev->m[k] = (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
        } else if (u < p_pay + p_stamp) {
            int slot = (int)(cmp_rand01(rng) * (double)n_occ) % n_occ;
            ev->cat = SQ5E_STAMP;
            ev->b = occ_list[slot] >> 8;
            ev->g = occ_list[slot] & 0xFF;
            ev->shell = (int)(cmp_rand01(rng) * 2.0);
            if (ev->shell > 1) ev->shell = 1;
            ev->nbytes = 1;
            ev->i = (int)(cmp_rand_u32(rng) % 4);
            ev->m[0] = (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
        } else {
            ev->cat = SQ5E_JOUR;
            ev->b = (int)(cmp_rand_u32(rng) % SQ5_NB);
            ev->g = 0;
            ev->shell = (int)(cmp_rand01(rng) * 2.0);
            if (ev->shell > 1) ev->shell = 1;
            ev->nbytes = 1;
            ev->i = (int)(cmp_rand_u32(rng) % sizeof(sq5_journal_t));
            ev->m[0] = (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
        }
        sq5_apply_event(&torus, ev);
    }

    /* ---------- detect (counterflow triangulation) + repair ------------
     * Decisions are recorded per bin BEFORE any repair, so detection
     * credit comes from actual flags, and the detect+repair pass is
     * timed separately (SQ5T stderr line) for overhead accounting. */
    static sq5_decision_t dec[SQ5_NB];
    uint64_t stamp_badmap[8];
    memset(stamp_badmap, 0, sizeof(stamp_badmap));

    double td0 = cmp_now_sec();
    for (int b = 0; b < SQ5_NB; b++)
        sq5_classify_bin(&torus, b, &dec[b], 1);
    long long stamp_flagged = sq5_stamp_check(&torus, 0, stamp_badmap);
    double td1 = cmp_now_sec();
    for (int b = 0; b < SQ5_NB; b++)
        sq5_apply_repair(&torus, b, &dec[b]);
    long long stamp_fixed = sq5_stamp_check(&torus, 1, NULL);
    double td2 = cmp_now_sec();
    fprintf(stderr, "SQ5T detect_ns=%.0f repair_ns=%.0f stamp_flagged=%lld\n",
            (td1 - td0) * 1e9, (td2 - td1) * 1e9, stamp_flagged);

    /* ---------- per-event scoring ------------------------------------- */
    long long detected = 0, repaired = 0;
    for (long long e = 0; e < inj; e++) {
        sq5_evt_t *ev = &evts[e];
        int det = 0, rep = 0;
        if (ev->cat == SQ5E_PAY) {
            /* detected if this bin's classification implicates the
             * event's shell (or both) */
            const sq5_decision_t *d = &dec[ev->b];
            if ((ev->shell == 0 &&
                 (d->cls == SQ5C_PAY0 || d->cls == SQ5C_PAY_BOTH)) ||
                (ev->shell == 1 &&
                 (d->cls == SQ5C_PAY1 || d->cls == SQ5C_PAY_BOTH)))
                det = 1;
            int item = sq5_item_at[ev->b][ev->g];
            rep = sq5_pay_ok(torus.pay[ev->b][ev->g][ev->shell], item);
        } else if (ev->cat == SQ5E_STAMP) {
            int slot = (ev->b * SQ5_NR + ev->g) * 2 + ev->shell;
            det = (int)((stamp_badmap[slot >> 6] >> (slot & 63)) & 1ULL);
            rep = (torus.stamp[ev->b][ev->g][ev->shell] ==
                   sq5_stamp(ev->b, ev->g, ev->shell));
        } else {
            const sq5_decision_t *d = &dec[ev->b];
            if (d->flags & (ev->shell == 0 ? SQ5F_R0 : SQ5F_R1)) det = 1;
            /* journal must now match a recompute from content */
            sq5_journal_t want = {0, 0, 0};
            for (int g = 0; g < SQ5_NR; g++)
                if (torus.occ[ev->b][g][ev->shell])
                    sq5_journal_add(&want, torus.pay[ev->b][g][ev->shell], g);
            rep = (want.s0 == torus.jr[ev->b][ev->shell].s0 &&
                   want.s1 == torus.jr[ev->b][ev->shell].s1 &&
                   want.s2 == torus.jr[ev->b][ev->shell].s2);
        }
        detected += det;
        repaired += rep;
    }
    out->detected = detected;
    out->repaired = repaired;
    (void)stamp_fixed;

    /* ---------- ground-truth coherency over all slots ------------------ */
    out->coherency_total = 0;
    long long read_idx = 0;
    for (int b = 0; b < SQ5_NB; b++)
        for (int g = 0; g < SQ5_NR; g++) {
            if (!torus.occ[b][g][0]) continue;
            out->coherency_total++;
            int item = sq5_item_at[b][g];
            for (int s = 0; s < 2; s++) {
                if (!sq5_pay_ok(torus.pay[b][g][s], item)) {
                    out->coherency_fail++;
                    break;
                }
            }
            if (churn_every > 0 &&
                (read_idx % churn_every) == (churn_every - 1)) {
                uint32_t dsx[2][3];
                (void)sq5_flux_bin(&torus, (int)(cmp_rand01(rng) * SQ5_NB) % SQ5_NB,
                                   dsx);
            }
            read_idx++;
        }
}
