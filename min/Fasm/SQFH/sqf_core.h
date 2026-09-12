/* SQF — forward-batch cell: SQ4-speed initial writes, deferred
 * integrity via batched backprop infill.
 *
 * The user's idea: "SQ4's approach for small loops. The INITIAL
 * writes can be raw speed for every new unit... 4-8 units per batch
 * to get that whole 4096.  Forward pass writes with occasional back
 * propagation infill."
 *
 * Geometry: 4096 slots (32 bins x 128), 64 B payload (moment
 * exactness bound from SQM holds).
 *
 * Hot path (flush): raw memcpy + journal bookkeeping.  Nothing is
 * re-read, nothing is solved, nothing confirmed.
 *   Mode A (SQF_EAGER=1): journal = incoming moments at flush
 *     (one SSE pass — anchor is TRUE from birth).
 *   Mode B (SQF_EAGER=0): pure memcpy; the moment baseline is
 *     anchored by the first backprop pass over the slot.  Honest
 *     window: corruption before first backprop is baselined in
 *     (documented, measured — same category as SQM's O6).
 *
 * Backprop (occasional, off the hot path):
 *   incremental (full=0): scan only slots written since the last
 *     pass — the infill of the just-written forward region.
 *   full (full=1): scan every occupied slot (cert / patrol).
 *   Anchored slot with moment mismatch → exact Vandermonde solve on
 *   the delta → infill ONLY the solved bytes → closure re-verify.
 *
 * Integrity machinery (moments, solve) inherited from sqm_core.h.
 */
#ifndef SQF_CORE_H
#define SQF_CORE_H

#include "sqm_core.h"

#ifndef SQF_EAGER
#define SQF_EAGER 1
#endif

#define SQF_BATCH 8                      /* units per forward batch */
#define SQF_NB 32
#define SQF_NR 128
#define SQF_CAPACITY (SQF_NB * SQF_NR)   /* 4096 */

typedef struct {
    uint8_t   pay[SQF_NB][SQF_NR][SQM_PAY];
    sqm_mom_t root[SQF_NB][SQF_NR];      /* journal (anchor) */
    uint8_t   occ[SQF_NB][SQF_NR];
    uint8_t   anchored[SQF_NB][SQF_NR];  /* journal is a true baseline */
    int       head[SQF_NB];
    int       total;

    /* forward batch buffer */
    int     b_id[SQF_BATCH];
    int     b_item[SQF_BATCH];
    uint8_t b_data[SQF_BATCH][SQM_PAY];
    int     b_n;
    int     bp_hw[SQF_NB];               /* per-bin high-water (incremental cursor) */

    /* counters */
    uint64_t fwd_batches, fwd_writes;
    uint64_t bp_passes, bp_anchored, bp_scans, bp_repairs, bp_unresolved;
    uint64_t wr_bytes_hot, rd_bytes_bp, wr_bytes_bp;
} sqf_t;

static int sqf_item_at[SQF_NB][SQF_NR];
static int sqf_slot_of_tab[SQF_CAPACITY * 4];

static void sqf_init(sqf_t *t) {
    memset(t, 0, sizeof *t);
    memset(sqf_item_at, -1, sizeof sqf_item_at);
    memset(sqf_slot_of_tab, -1, sizeof sqf_slot_of_tab);
}

/* ---- hot path: buffer, then flush a whole batch ---- */

static inline void sqf_flush(sqf_t *t) {
    t->fwd_batches++;
    for (int k = 0; k < t->b_n; k++) {
        int id = t->b_id[k];
        int b0 = SQM_SCATLT[id & 31] % SQF_NB, bin = -1;
        for (int j = 0; j < SQF_NB; j++) {
            int b = (b0 + j) % SQF_NB;
            if (t->head[b] < SQF_NR) { bin = b; break; }
        }
        if (bin < 0) continue;                     /* full: loud drop */
        int g = t->head[bin];
        memcpy(t->pay[bin][g], t->b_data[k], SQM_PAY);   /* raw speed */
        t->wr_bytes_hot += SQM_PAY;
#if SQF_EAGER
        sqm_mom(t->b_data[k], 0, SQM_PAY, &t->root[bin][g]);
        t->anchored[bin][g] = 1;                   /* true from birth */
#endif
        t->occ[bin][g] = 1;
        sqf_item_at[bin][g] = t->b_item[k];
        sqf_slot_of_tab[id] = (bin << 8) | g;
        t->head[bin]++;
        t->total++;
        t->fwd_writes++;
    }
    t->b_n = 0;
}

static inline int sqf_write(sqf_t *t, int id, int item,
                            const uint8_t *data) {
    if (id >= SQF_CAPACITY * 4) return -1;
    memcpy(t->b_data[t->b_n], data, SQM_PAY);
    t->b_id[t->b_n] = id;
    t->b_item[t->b_n] = item;
    t->b_n++;
    if (t->b_n == SQF_BATCH) sqf_flush(t);
    return 0;
}

/* ---- backprop infill ---- */
static int sqf_backprop(sqf_t *t, int full) {
    t->bp_passes++;
    int unresolved = 0;
    for (int b = 0; b < SQF_NB; b++) {
        int gs = full ? 0 : t->bp_hw[b];
        for (int g = gs; g < t->head[b]; g++) {
            if (!t->occ[b][g]) continue;
            sqm_mom_t ms;
            sqm_mom(t->pay[b][g], 0, SQM_PAY, &ms);
            t->rd_bytes_bp += SQM_PAY;
            t->bp_scans++;
            if (!t->anchored[b][g]) {
                t->root[b][g] = ms;                /* baseline anchor */
                t->anchored[b][g] = 1;
                t->bp_anchored++;
                continue;
            }
            if (ms.s[0] == t->root[b][g].s[0] &&
                ms.s[1] == t->root[b][g].s[1] &&
                ms.s[2] == t->root[b][g].s[2] &&
                ms.s[3] == t->root[b][g].s[3]) continue;
            sqm_mom_t D;
            for (int k = 0; k < 4; k++)
                D.s[k] = t->root[b][g].s[k] - ms.s[k];
            int p1, d1, p2, d2;
            int npt = sqm_solve(&D, &p1, &d1, &p2, &d2);
            if (npt > 0) {
                uint8_t *pay = t->pay[b][g];
                pay[p1 - 1] = (uint8_t)(pay[p1 - 1] + d1);
                t->wr_bytes_bp += 1;
                if (npt == 2) {
                    pay[p2 - 1] = (uint8_t)(pay[p2 - 1] + d2);
                    t->wr_bytes_bp += 1;
                }
                sqm_mom_t chk;
                sqm_mom(pay, 0, SQM_PAY, &chk);
                t->rd_bytes_bp += SQM_PAY;
                if (chk.s[0] == t->root[b][g].s[0] &&
                    chk.s[1] == t->root[b][g].s[1] &&
                    chk.s[2] == t->root[b][g].s[2] &&
                    chk.s[3] == t->root[b][g].s[3]) { t->bp_repairs++; continue; }
            }
            t->bp_unresolved++;
            unresolved++;
        }
    }
    for (int b = 0; b < SQF_NB; b++) t->bp_hw[b] = t->head[b];
    return unresolved;
}

#endif /* SQF_CORE_H */
