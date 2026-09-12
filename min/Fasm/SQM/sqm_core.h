/* sqm_core.h — SQM: moment-Merkle write-skip cell (ESF moments as
 * address + diff, minimal-read updates).
 *
 * One linear pass over the INCOMING data does three jobs:
 *   recognition   root moments match the journal -> skip, ZERO reads
 *                 of stored content, zero writes.
 *   localization  delta moments -> exact 1/2-point Vandermonde solve
 *                 (Hamming/RS flavour) -> confirm-read only the
 *                 predicted bytes, write only there.
 *   journal       incoming moments ARE the new journal (linearity) —
 *                 no re-read of stored content, ever.
 *
 * Exactness: at SQM_PAY=64 every moment is bounded (s3 <= 255*(2080)^2
 * < 2^32), so the whole system is exact integer arithmetic — no
 * modular ambiguity in the solve.  Documented bound, -D adaptable
 * only below it.
 *
 * Hot-path trust model (honest window): a pure skip never reads stored
 * content, so corruption of stored bytes between sweeps is invisible
 * UNTIL the next update or G2 sweep.  The update path's confirm-read
 * catches disagreement for free (escalates to slice scan).  The G2
 * sweep recomputes and SEC/2-byte repairs.  The window is measured in
 * sqm_cert.c (O6), not hidden.
 *
 * Blindness retreat: s3 catches the (1,-3,3,-1) quads that were 100%
 * blind to SQ5's three moments; the blind class is now the 5-point
 * (1,-4,6,-4,1) pattern — mapped in sqm_cert.c (O5).
 */
#ifndef SQM_CORE_H
#define SQM_CORE_H

#include <stdint.h>
#include <string.h>
#include "esf_syndrome.h"  /* esf_hsum_epi32 + <smmintrin.h> under __SSE4_1__ */

#ifndef SQM_NB
#define SQM_NB   8
#endif
#ifndef SQM_NR
#define SQM_NR   32
#endif
#ifndef SQM_PAY
#define SQM_PAY  64           /* exactness bound: keep at 64 */
#endif

#define SQM_HALF     (SQM_PAY / 2)
#define SQM_CAPACITY (SQM_NB * SQM_NR)

static const int SQM_SCATLT[32] = {
    6, 5, 4, 0, 2, 3, 4, 7, 4, 6, 3, 0, 1, 2, 1, 0,
    3, 6, 4, 7, 4, 3, 2, 0, 4, 5, 6, 5, 4, 0, 2, 3
};

typedef struct { uint64_t s[4]; } sqm_mom_t;   /* exact, never wraps at PAY=64 */

typedef struct {
    uint8_t   pay[SQM_NB][SQM_NR][SQM_PAY];
    sqm_mom_t root[SQM_NB][SQM_NR];
    sqm_mom_t half[SQM_NB][SQM_NR][2];   /* local indices 1..HALF */
    int8_t    occ[SQM_NB][SQM_NR];
    int       head[SQM_NB];
    int       total;
    /* instrumentation */
    long long skips, sec_writes, half_writes, full_writes;
    long long bytes_read, bytes_written;
    long long confirm_escalations;
} sqm_cell_t;

static int sqm_slot_of[SQM_CAPACITY * 4];   /* id -> packed bin<<8|gen, -1 none */
static int sqm_item_at[SQM_NB][SQM_NR];

static inline void sqm_init(sqm_cell_t *t) {
    memset(t, 0, sizeof(*t));
    for (int i = 0; i < SQM_CAPACITY * 4; i++) sqm_slot_of[i] = -1;
}

static inline void sqm_fill(uint8_t *p, int item) {
    for (int i = 0; i < SQM_PAY; i++)
        p[i] = (uint8_t)((item * 17 + i * 91) ^ 0xA5);
}
static inline int sqm_pay_ok(const uint8_t *p, int item) {
    for (int i = 0; i < SQM_PAY; i++)
        if (p[i] != (uint8_t)((item * 17 + i * 91) ^ 0xA5)) return 0;
    return 1;
}

/* moments over a buffer, global indices base+1 .. base+len.
 * SSE4.1 path: 4 u32 lanes are PROVABLY safe at PAY=64 — the worst
 * lane holds 16 terms of at most 255*64^3 ~= 1.07e9 < 2^32.  Same
 * vectorization as the ESF syndrome pass; idx^3 is two mullos. */
static inline void sqm_mom(const uint8_t *p, int base, int len, sqm_mom_t *m) {
#if defined(__SSE4_1__) && (SQM_PAY % 16 == 0)
    if (len % 16 == 0) {
        __m128i vs0 = _mm_setzero_si128(), vs1 = _mm_setzero_si128(),
                vs2 = _mm_setzero_si128(), vs3 = _mm_setzero_si128();
        __m128i idxv = _mm_setr_epi32(base + 1, base + 2, base + 3, base + 4);
        for (int i = 0; i < len; i += 16) {
            __m128i bytes = _mm_loadu_si128((const __m128i *)(p + i));
            __m128i v0 = _mm_cvtepu8_epi32(bytes);
            __m128i v1 = _mm_cvtepu8_epi32(_mm_srli_si128(bytes, 4));
            __m128i v2 = _mm_cvtepu8_epi32(_mm_srli_si128(bytes, 8));
            __m128i v3 = _mm_cvtepu8_epi32(_mm_srli_si128(bytes, 12));
            vs0 = _mm_add_epi32(vs0, _mm_add_epi32(_mm_add_epi32(v0, v1), _mm_add_epi32(v2, v3)));
            __m128i i0 = idxv;
            __m128i i1 = _mm_add_epi32(idxv, _mm_set1_epi32(4));
            __m128i i2 = _mm_add_epi32(idxv, _mm_set1_epi32(8));
            __m128i i3 = _mm_add_epi32(idxv, _mm_set1_epi32(12));
            __m128i x0 = _mm_mullo_epi32(v0, i0), x1 = _mm_mullo_epi32(v1, i1),
                    x2 = _mm_mullo_epi32(v2, i2), x3 = _mm_mullo_epi32(v3, i3);
            vs1 = _mm_add_epi32(vs1, _mm_add_epi32(_mm_add_epi32(x0, x1), _mm_add_epi32(x2, x3)));
            vs2 = _mm_add_epi32(vs2, _mm_add_epi32(
                    _mm_add_epi32(_mm_mullo_epi32(x0, i0), _mm_mullo_epi32(x1, i1)),
                    _mm_add_epi32(_mm_mullo_epi32(x2, i2), _mm_mullo_epi32(x3, i3))));
            vs3 = _mm_add_epi32(vs3, _mm_add_epi32(
                    _mm_add_epi32(_mm_mullo_epi32(x0, _mm_mullo_epi32(i0, i0)),
                                  _mm_mullo_epi32(x1, _mm_mullo_epi32(i1, i1))),
                    _mm_add_epi32(_mm_mullo_epi32(x2, _mm_mullo_epi32(i2, i2)),
                                  _mm_mullo_epi32(x3, _mm_mullo_epi32(i3, i3)))));
            idxv = _mm_add_epi32(idxv, _mm_set1_epi32(16));
        }
        m->s[0] = (uint32_t)esf_hsum_epi32(vs0);
        m->s[1] = (uint32_t)esf_hsum_epi32(vs1);
        m->s[2] = (uint32_t)esf_hsum_epi32(vs2);
        m->s[3] = (uint32_t)esf_hsum_epi32(vs3);
        return;
    }
#endif
    uint64_t s0 = 0, s1 = 0, s2 = 0, s3 = 0;
    for (int i = 0; i < len; i++) {
        uint64_t v = p[i], x = (uint64_t)(base + i + 1);
        s0 += v;
        s1 += v * x;
        s2 += v * x * x;
        s3 += v * x * x * x;
    }
    m->s[0] = s0; m->s[1] = s1; m->s[2] = s2; m->s[3] = s3;
}

static inline int sqm_mom_eq(const sqm_mom_t *a, const sqm_mom_t *b) {
    return memcmp(a, b, sizeof(sqm_mom_t)) == 0;
}

/* Exact 1/2-point Vandermonde solve on moment deltas D[0..3].
 * Returns number of points (1 or 2) with positions p[1..PAY] and
 * deltas d (incoming = stored + d), or 0 if the delta is not a
 * 1-or-2-byte difference. */
static inline int sqm_solve(const sqm_mom_t *D, int *p1, int *d1,
                            int *p2, int *d2) {
    int64_t D0 = (int64_t)D->s[0], D1 = (int64_t)D->s[1],
            D2 = (int64_t)D->s[2], D3 = (int64_t)D->s[3];
    if (D0 == 0) return 0;                 /* s0 must move for <=2 pts */
    /* 1-point: d = D0, p = D1/D0, confirm D2, D3 */
    if (D0 >= -255 && D0 <= 255 && D1 % D0 == 0) {
        int64_t p = D1 / D0;
        if (p >= 1 && p <= SQM_PAY && D2 == D0 * p * p && D3 == D0 * p * p * p) {
            *p1 = (int)p; *d1 = (int)D0;
            return 1;
        }
    }
    /* 2-point: Newton identities, exact integer solve */
    int64_t det = D0 * D2 - D1 * D1;
    if (det != 0) {
        int64_t un = D0 * D3 - D1 * D2;    /* u = p1+p2 numerator-part */
        int64_t vn = D1 * D3 - D2 * D2;    /* v = p1*p2 */
        if (un % det == 0 && vn % det == 0) {
            int64_t u = un / det, v = vn / det;
            int64_t disc = u * u - 4 * v;
            if (disc > 0) {
                /* integer sqrt check */
                int64_t r = 1;
                while (r * r < disc) r++;
                if (r * r == disc) {
                    int64_t a = (u + r) / 2, b = (u - r) / 2;
                    if ((u + r) % 2 == 0 && a >= 1 && b >= 1 &&
                        a <= SQM_PAY && b <= SQM_PAY && a != b) {
                        int64_t da = (a - b) ? (D1 - D0 * b) / (a - b) : 0;
                        if ((D1 - D0 * b) % (a - b) == 0) {
                            int64_t db = D0 - da;
                            if (da >= -255 && da <= 255 && da != 0 &&
                                db >= -255 && db <= 255 && db != 0 &&
                                D2 == da * a * a + db * b * b &&
                                D3 == da * a * a * a + db * b * b * b) {
                                *p1 = (int)a; *d1 = (int)da;
                                *p2 = (int)b; *d2 = (int)db;
                                return 2;
                            }
                        }
                    }
                }
            }
        }
    }
    return 0;
}

/* The write path: minimal reads, minimal writes.
 * incoming is the caller's new content for `id` (we may read it freely;
 * it is being handed to us).  item is the harness pattern id. */
static inline int sqm_write(sqm_cell_t *t, int id, int item,
                            const uint8_t *incoming) {
    int slot = (id < SQM_CAPACITY * 4) ? sqm_slot_of[id] : -1;

    /* root moments: ONE pass over caller data (unavoidable cost).
     * Half journals are computed LAZILY — only on mismatch. */
    sqm_mom_t mi;
    sqm_mom(incoming, 0, SQM_PAY, &mi);

    if (slot >= 0 && sqm_mom_eq(&mi, &t->root[slot >> 8][slot & 0xFF])) {
        t->skips++;
        return 0;                          /* recognition: 0 rd, 0 wr */
    }

    /* mismatch (or first write): halves are computed LAZILY — only
     * when we actually need them (first write / slice path).  On the
     * common small-diff path the solve succeeds and half journals are
     * updated POINTWISE by linearity instead: d·x, d·x², d·x³ at the
     * solved positions — no pass over incoming beyond the root one. */
    sqm_mom_t mh[2];
    int mh_valid = 0;
#define SQM_COMPUTE_HALVES() do { \
    if (!mh_valid) { \
        sqm_mom(incoming, 0, SQM_HALF, &mh[0]); \
        uint64_t H = SQM_HALF; \
        uint64_t s0 = mi.s[0] - mh[0].s[0]; \
        uint64_t g1 = mi.s[1] - mh[0].s[1]; \
        uint64_t g2 = mi.s[2] - mh[0].s[2]; \
        uint64_t g3 = mi.s[3] - mh[0].s[3]; \
        mh[1].s[0] = s0; \
        mh[1].s[1] = g1 - H * s0; \
        mh[1].s[2] = g2 - 2 * H * g1 + H * H * s0; \
        mh[1].s[3] = g3 - 3 * H * g2 + 3 * H * H * g1 - H * H * H * s0; \
        mh_valid = 1; \
    } } while (0)

    if (slot < 0) {                        /* first write: full */
        SQM_COMPUTE_HALVES();
        int b0 = SQM_SCATLT[id & 31] % SQM_NB, bin = -1;
        for (int k = 0; k < SQM_NB; k++) {
            int b = (b0 + k) % SQM_NB;
            if (t->head[b] < SQM_NR) { bin = b; break; }
        }
        if (bin < 0) return -1;
        int g = t->head[bin];
        memcpy(t->pay[bin][g], incoming, SQM_PAY);
        t->root[bin][g] = mi;
        t->half[bin][g][0] = mh[0];
        t->half[bin][g][1] = mh[1];
        t->occ[bin][g] = 1;
        sqm_item_at[bin][g] = item;
        sqm_slot_of[id] = (bin << 8) | g;
        t->head[bin]++;
        t->total++;
        t->full_writes++;
        t->bytes_written += SQM_PAY;
        return 0;
    }

    int b = slot >> 8, g = slot & 0xFF;
    /* (skip was already handled before the lazy halves) */

    /* delta moments (exact) */
    sqm_mom_t D;
    for (int k = 0; k < 4; k++) D.s[k] = mi.s[k] - t->root[b][g].s[k];

    int p1, d1, p2, d2;
    int npt = sqm_solve(&D, &p1, &d1, &p2, &d2);
    if (npt > 0) {
        /* confirm-read ONLY the predicted positions: stored + d must
         * equal incoming there.  Escalation on mismatch = the free
         * corruption tripwire. */
        uint8_t *pay = t->pay[b][g];
        int ok = (uint8_t)(pay[p1 - 1] + d1) == incoming[p1 - 1];
        t->bytes_read += 1;
        if (ok && npt == 2) {
            ok = (uint8_t)(pay[p2 - 1] + d2) == incoming[p2 - 1];
            t->bytes_read += 1;
        }
        if (ok) {
            pay[p1 - 1] = (uint8_t)(pay[p1 - 1] + d1);
            t->bytes_written += 1;
            if (npt == 2) {
                pay[p2 - 1] = (uint8_t)(pay[p2 - 1] + d2);
                t->bytes_written += 1;
            }
            t->root[b][g] = mi;            /* journal = incoming, free */
            /* half journals: pointwise by linearity (no extra pass) */
            for (int k = 0; k < npt; k++) {
                int p = (k == 0) ? p1 : p2;
                int64_t d = (k == 0) ? d1 : d2;
                int h = (p - 1) / SQM_HALF;
                uint64_t x = (uint64_t)((p - 1) % SQM_HALF + 1);
                sqm_mom_t *hj = &t->half[b][g][h];
                hj->s[0] += (uint64_t)d;
                hj->s[1] += (uint64_t)d * x;
                hj->s[2] += (uint64_t)d * x * x;
                hj->s[3] += (uint64_t)d * x * x * x;
            }
            t->sec_writes++;
            return 0;
        }
        t->confirm_escalations++;          /* fall through to slice */
    }

    /* slice path: which halves are dirty? */
    SQM_COMPUTE_HALVES();
    int dirty0 = !sqm_mom_eq(&mh[0], &t->half[b][g][0]);
    int dirty1 = !sqm_mom_eq(&mh[1], &t->half[b][g][1]);
    uint8_t *pay = t->pay[b][g];
    if (dirty0 != dirty1) {                /* exactly one half dirty */
        int h = dirty0 ? 0 : 1;
        uint8_t *sl = pay + h * SQM_HALF;
        const uint8_t *isl = incoming + h * SQM_HALF;
        t->bytes_read += SQM_HALF;
        int nw = 0;
        for (int i = 0; i < SQM_HALF; i++)
            if (sl[i] != isl[i]) { sl[i] = isl[i]; nw++; }
        t->bytes_written += nw;
        t->half_writes++;
    } else {                               /* both halves dirty: rewrite */
        memcpy(pay, incoming, SQM_PAY);
        t->bytes_read += SQM_PAY;
        t->bytes_written += SQM_PAY;
        t->full_writes++;
    }
    t->root[b][g] = mi;
    t->half[b][g][0] = mh[0];
    t->half[b][g][1] = mh[1];
    return 0;
}

/* G2 sweep: recompute-per-slot vs journal, SEC/2-byte repair.
 * Returns unresolved slots. */
static inline long long sqm_sweep(sqm_cell_t *t, uint8_t *action) {
    long long unresolved = 0;
    for (int b = 0; b < SQM_NB; b++)
        for (int g = 0; g < SQM_NR; g++) {
            if (!t->occ[b][g]) continue;
            if (action) action[b * SQM_NR + g] = 0;
            sqm_mom_t cur;
            sqm_mom(t->pay[b][g], 0, SQM_PAY, &cur);
            if (sqm_mom_eq(&cur, &t->root[b][g])) continue;
            if (action) action[b * SQM_NR + g] = 1;
            sqm_mom_t D;
            /* delta stored-minus-journal; repair subtracts it */
            for (int k = 0; k < 4; k++) D.s[k] = cur.s[k] - t->root[b][g].s[k];
            int p1, d1, p2, d2;
            int npt = sqm_solve(&D, &p1, &d1, &p2, &d2);
            if (npt > 0) {
                uint8_t *pay = t->pay[b][g];
                pay[p1 - 1] = (uint8_t)(pay[p1 - 1] - d1);
                if (npt == 2) pay[p2 - 1] = (uint8_t)(pay[p2 - 1] - d2);
                sqm_mom(t->pay[b][g], 0, SQM_PAY, &cur);
                if (sqm_mom_eq(&cur, &t->root[b][g])) {
                    t->half[b][g][0] = (sqm_mom_t){0};
                    t->half[b][g][1] = (sqm_mom_t){0};
                    sqm_mom(t->pay[b][g], 0, SQM_HALF, &t->half[b][g][0]);
                    sqm_mom(t->pay[b][g] + SQM_HALF, 0, SQM_HALF, &t->half[b][g][1]);
                    continue;
                }
            }
            unresolved++;
        }
    return unresolved;
}

#endif /* SQM_CORE_H */
