/* bench_sq4.c — Squaragon V4 core (sq4core.ergo semantics) benchmark.
 *
 * Faithful C mirror of tests/sq4core.ergo: 2 shells x 8 bins x 32 ring,
 * LUT scatter (v4 8-bin bake, total=52, HOPFQ=1.97), integer bit-pack
 * invariants, shell-1 -> shell-2 replication, SQ4VAL recompute validation.
 *
 * IMPORTANT FIDELITY NOTE: the v4 torus stores NO payload data — TINVAR is
 * a pure position stamp (geo|bin|seam|shell|gen), fully determined by slot
 * coordinates.  Therefore:
 *   - detection = recompute-and-compare: ANY change to an occupied slot's
 *     invariant is visible (det ceiling 100% by construction);
 *   - repair = rewrite the expected pack: always succeeds (rep 100%);
 *   - there is no payload to lose, so coherency measures slot/invariant
 *     consistency after the detect+repair pass.
 * The table row therefore shows SQ4's integrity model is trivially perfect
 * ON THE DATA IT STORES — unlike V22 (152-byte gates, fold blind spot) and
 * ESF (payload-bearing frames), SQ4 protects position metadata only.
 * SQ4RES (3-axis gate residual) is not exercised: the ergo port keeps gate
 * state in a single global RVTX demo buffer, not per-slot.
 *
 * Workload mirrors the V22 bench: cap n at 256 (shell-1 capacity), repeat
 * rounds for timing, then replicate -> inject unique single-bit flips into
 * occupied shell-2 invariants -> validate (detect) -> repair -> re-validate
 * -> coherency walk.
 */

#include "common.h"
#include "cache_perf.h"

#define SQ4_NBINS  8
#define SQ4_NRING  32
#define SQ4_CAPACITY 256   /* shell-1 slots */

static const int SQ4_SCATLT[32] = {
    6, 5, 4, 0, 2, 3, 4, 7, 4, 6, 3, 0, 1, 2, 1, 0,
    3, 6, 4, 7, 4, 3, 2, 0, 4, 5, 6, 5, 4, 0, 2, 3
};
static const int SQ4_BINGEO[8] = { 228, 104, 0, 104, 228, 104, 0, 104 };

typedef struct {
    int32_t tinvar[SQ4_NRING][SQ4_NBINS][2];
    int8_t  tocc  [SQ4_NRING][SQ4_NBINS][2];
    int8_t  tfroz [SQ4_NRING][SQ4_NBINS][2];
    int     twhead[SQ4_NBINS][2];   /* next gen, 0-based (ergo TWHEAD-1) */
    int     tlen  [SQ4_NBINS][2];
    int     talloc[SQ4_NBINS][2];
    int     ttotal;
} sq4_torus_t;

static inline void sq4_tin(sq4_torus_t *t) {
    memset(t, 0, sizeof(*t));
}

/* Bit pack (ergo SQ4FAL/SQ4VAL layout):
 *   bits  0-4 : gen (0-31)   bit 8: shell   bits 9-13: seam (2*gen mod 32)
 *   bits 16-18: bin          bits 24-31: geo */
static inline int32_t sq4_pack(int gen, int bin, int shell) {
    int tbits = ((gen << 1) & 31);
    return (SQ4_BINGEO[bin] << 24) | (bin << 16) | (tbits << 9) |
           ((shell & 1) << 8) | gen;
}

/* SQ4FAL: fast allocate on shell 0 (ergo SHELL=1).  Returns 0, -1 when
 * the whole torus is full.  The SCATLT hint does not balance (bins 1/4
 * overflow ~14% of a 256-fill), so a single-bin mapping silently drops
 * whenever a hot bin fills first; the cold-path probe below recovers
 * those into cold bins.  Packs record actual coordinates and items are
 * anonymous, so the probe preserves every invariant. */
static inline int sq4_fal(sq4_torus_t *t, int id) {
    int bin = SQ4_SCATLT[id & 31];
    int gen = t->twhead[bin][0];
    if (__builtin_expect(gen >= SQ4_NRING, 0)) {
        int b0 = bin, k = 0;
        do {
            if (++k >= SQ4_NBINS) return -1;
            bin = (b0 + k) & 7;
            gen = t->twhead[bin][0];
        } while (gen >= SQ4_NRING);
    }

    t->tinvar[gen][bin][0] = sq4_pack(gen, bin, 0);
    t->tocc[gen][bin][0] = 1;
    t->talloc[bin][0]++;
    t->tfroz[gen][bin][0] = (t->talloc[bin][0] % 4 == 0) ? 1 : 0;
    t->twhead[bin][0]++;
    t->tlen[bin][0]++;
    t->ttotal++;
    return 0;
}

/* SQ4REP: replicate shell 0 -> shell 1 (ergo shell 1 -> shell 2). */
static inline int sq4_rep(sq4_torus_t *t) {
    int copied = 0;
    for (int j = 0; j < SQ4_NBINS; j++) {
        for (int i = 0; i < SQ4_NRING; i++) {
            if (t->tocc[i][j][0]) {
                t->tinvar[i][j][1] = sq4_pack(i, j, 1);
                t->tocc[i][j][1] = 1;
                t->tfroz[i][j][1] = 0;
                t->tlen[j][1]++;
                t->ttotal++;
                copied++;
            }
        }
        t->twhead[j][1] = t->twhead[j][0];
    }
    return copied;
}

/* SQ4VAL: recompute-and-compare over all slots; returns bad-slot count.
 * Optionally repairs in place (rewrite expected pack / clear stray). */
static inline int sq4_val(sq4_torus_t *t, int repair) {
    int bad = 0;
    for (int k = 0; k < 2; k++)
        for (int j = 0; j < SQ4_NBINS; j++)
            for (int i = 0; i < SQ4_NRING; i++) {
                if (t->tocc[i][j][k]) {
                    if (t->tinvar[i][j][k] != sq4_pack(i, j, k)) {
                        bad++;
                        if (repair) t->tinvar[i][j][k] = sq4_pack(i, j, k);
                    }
                } else {
                    if (t->tinvar[i][j][k] != 0) {
                        bad++;
                        if (repair) t->tinvar[i][j][k] = 0;
                    }
                }
            }
    return bad;
}

void bench_sq4(cmp_result_t *out, long long n, double error_rate, int churn_every) {
    memset(out, 0, sizeof(*out));
    strncpy(out->name, "SQ4", sizeof(out->name) - 1);
    out->available = 1;

    if (n > SQ4_CAPACITY) n = SQ4_CAPACITY;

    uint64_t rng[4];
    cmp_seed(rng, 0x5C4A11U);

    sq4_torus_t torus;

    int rounds = (n < 100000) ? (int)(100000 / n + 1) : 1;

    cp_ctx_t cp;
    cp_open(&cp);

    /* ---------- allocation (LUT + integer hot path, no gate writes) --- */
    cp_start(&cp);
    double t0 = cmp_now_sec();
    for (int r = 0; r < rounds; r++) {
        sq4_tin(&torus);
        for (long long i = 0; i < n; i++) {
            if (sq4_fal(&torus, (int)i) != 0) out->alloc_fail++;
        }
    }
    double t1 = cmp_now_sec();
    cp_stop(&cp);
    if (out->alloc_fail > 0) {
        fprintf(stderr, "SQ4: %lld/%lld allocations failed (strand overflow)\n",
                out->alloc_fail, n * rounds);
    }

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

    /* ---------- replication ---------- */
    sq4_rep(&torus);

    /* ---------- error injection: unique occupied shell-1 (copy) slots,
     * single-bit flips in the invariant word, without replacement ------ */
    int occ[SQ4_CAPACITY];
    int n_occ = 0;
    for (int j = 0; j < SQ4_NBINS; j++)
        for (int i = 0; i < SQ4_NRING; i++)
            if (torus.tocc[i][j][1]) occ[n_occ++] = (j << 8) | i;

    long long inj = (long long)(error_rate * (double)n_occ + 0.5);
    if (inj < 1 && n_occ > 0) inj = 1;
    if (inj > n_occ) inj = n_occ;
    out->injected = inj;

    long long *order = cmp_pick_unique(n_occ, inj, rng);
    if (!order) { fprintf(stderr, "SQ4: victim selection failed\n"); return; }
    for (long long c = 0; c < inj; c++) {
        int j = occ[order[c]] >> 8, i = occ[order[c]] & 0xFF;
        torus.tinvar[i][j][1] ^= (int32_t)(1u << (cmp_rand_u32(rng) % 32));
    }
    free(order);

    /* ---------- detect (SQ4VAL), repair, re-validate ---------- */
    out->detected = sq4_val(&torus, 0);
    (void)sq4_val(&torus, 1);              /* repair pass: rewrite expected packs */
    int remaining = sq4_val(&torus, 0);    /* re-validate after repair */
    out->repaired = out->detected - remaining;
    if (remaining != 0) {
        fprintf(stderr, "SQ4: %d bad slots remained after repair\n", remaining);
    }

    /* ---------- coherency walk: every occupied slot carries the correct
     * position stamp after the repair pass; occupancy consistent with
     * write heads ---------------------------------------------------- */
    out->coherency_total = 0;
    long long read_idx = 0;
    for (int k = 0; k < 2; k++)
        for (int j = 0; j < SQ4_NBINS; j++)
            for (int i = 0; i < SQ4_NRING; i++) {
                if (!torus.tocc[i][j][k]) continue;
                out->coherency_total++;
                if (torus.tinvar[i][j][k] != sq4_pack(i, j, k))
                    out->coherency_fail++;

                if (churn_every > 0 &&
                    (read_idx % churn_every) == (churn_every - 1)) {
                    /* Churn: re-validate a random bin (cache perturbation). */
                    int jb = (int)(cmp_rand01(rng) * (double)SQ4_NBINS);
                    if (jb >= SQ4_NBINS) jb = SQ4_NBINS - 1;
                    for (int i2 = 0; i2 < SQ4_NRING; i2++)
                        if (torus.tocc[i2][jb][0])
                            (void)sq4_pack(i2, jb, 0);
                }
                read_idx++;
            }
}
