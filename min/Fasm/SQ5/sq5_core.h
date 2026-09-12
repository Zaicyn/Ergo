/* sq5_core.h — SQ5 v5 allocator core: counterflow journal design.
 *
 * Shared by bench_sq5.c (comparison row), sq5_cert.c (certification
 * driver), and mirrored independently by sq5_mirror.py.
 *
 * Certification architecture (Wigner-campaign pattern):
 *   - counting oracles (exact by construction): payload/stamp/journal
 *     detection
 *   - measurement oracles (must earn their numbers): repair, arbitration
 *   - documented algebraic blindness: moment-preserving collisions
 *     (3rd-difference quads) are invisible to EVERY residual — mapped,
 *     not hidden.
 */
#ifndef SQ5_CORE_H
#define SQ5_CORE_H

#include <stdint.h>
#include <string.h>
#include "esf_syndrome.h"  /* esf_hsum_epi32 + <smmintrin.h> under __SSE4_1__ */

#ifndef SQ5_NB
#define SQ5_NB   8
#endif
#ifndef SQ5_NR
#define SQ5_NR   32
#endif
#ifndef SQ5_PAY
#define SQ5_PAY  64
#endif

#define SQ5_BINBYTES (SQ5_NR * SQ5_PAY)
#define SQ5_CAPACITY (SQ5_NB * SQ5_NR)
#define SQ5_JRBYTES  ((int)sizeof(sq5_journal_t) * SQ5_NB * 2)
#define SQ5_STAMPBYTES ((int)sizeof(uint32_t) * SQ5_NB * SQ5_NR * 2)
#define SQ5_PAYBYTES (SQ5_NB * SQ5_NR * 2 * SQ5_PAY)

static const int SQ5_SCATLT[32] = {
    6, 5, 4, 0, 2, 3, 4, 7, 4, 6, 3, 0, 1, 2, 1, 0,
    3, 6, 4, 7, 4, 3, 2, 0, 4, 5, 6, 5, 4, 0, 2, 3
};
static const int SQ5_BINGEO[8] = { 228, 104, 0, 104, 228, 104, 0, 104 };

typedef struct {
    uint32_t s0, s1, s2;      /* moment journal, mod-2^32 (ESF convention) */
} sq5_journal_t;

typedef struct {
    uint8_t pay [SQ5_NB][SQ5_NR][2][SQ5_PAY];  /* [bin][gen][shell][byte] */
    uint32_t stamp[SQ5_NB][SQ5_NR][2];
    int8_t  occ  [SQ5_NB][SQ5_NR][2];
    int     twhead[SQ5_NB];
    int     ttotal;
    sq5_journal_t jr[SQ5_NB][2];               /* per-bin per-shell journal */
} sq5_torus_t;

/* Bench-side bookkeeping: which item lives in each slot (pattern check). */
static int sq5_item_at[SQ5_NB][SQ5_NR];

static inline void sq5_tin(sq5_torus_t *t) { memset(t, 0, sizeof(*t)); }

static inline uint32_t sq5_stamp(int bin, int gen, int shell) {
    int tbits = ((gen << 1) & 31);
    return ((uint32_t)SQ5_BINGEO[bin & 7] << 24) | ((uint32_t)bin << 16) |
           ((uint32_t)tbits << 9) | ((uint32_t)(shell & 1) << 8) | (uint32_t)gen;
}

static inline void sq5_fill(uint8_t *p, int item) {
    for (int i = 0; i < SQ5_PAY; i++)
        p[i] = (uint8_t)((item * 17 + i * 91) ^ 0xA5);
}
static inline int sq5_pay_ok(const uint8_t *p, int item) {
    for (int i = 0; i < SQ5_PAY; i++)
        if (p[i] != (uint8_t)((item * 17 + i * 91) ^ 0xA5)) return 0;
    return 1;
}

/* Incremental journal update over one slot's payload (linear add).
 * SSE4.1 path mirrors the ESF v2 syndrome vectorization. */
static inline void sq5_journal_add(sq5_journal_t *j, const uint8_t *p, int gen) {
    uint32_t base = (uint32_t)gen * SQ5_PAY;
#if defined(__SSE4_1__) && (SQ5_PAY % 16 == 0)
    __m128i vs0 = _mm_setzero_si128(), vs1 = _mm_setzero_si128(), vs2 = _mm_setzero_si128();
    __m128i idxv = _mm_setr_epi32((int)base + 1, (int)base + 2, (int)base + 3, (int)base + 4);
    for (int i = 0; i < SQ5_PAY; i += 16) {
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
        vs1 = _mm_add_epi32(vs1, _mm_add_epi32(
            _mm_add_epi32(_mm_mullo_epi32(v0, i0), _mm_mullo_epi32(v1, i1)),
            _mm_add_epi32(_mm_mullo_epi32(v2, i2), _mm_mullo_epi32(v3, i3))));
        vs2 = _mm_add_epi32(vs2, _mm_add_epi32(
            _mm_add_epi32(_mm_mullo_epi32(v0, _mm_mullo_epi32(i0, i0)),
                          _mm_mullo_epi32(v1, _mm_mullo_epi32(i1, i1))),
            _mm_add_epi32(_mm_mullo_epi32(v2, _mm_mullo_epi32(i2, i2)),
                          _mm_mullo_epi32(v3, _mm_mullo_epi32(i3, i3)))));
        idxv = _mm_add_epi32(idxv, _mm_set1_epi32(16));
    }
    j->s0 += esf_hsum_epi32(vs0);
    j->s1 += esf_hsum_epi32(vs1);
    j->s2 += esf_hsum_epi32(vs2);
#else
    for (int i = 0; i < SQ5_PAY; i++) {
        uint32_t v = p[i], idx = base + (uint32_t)i + 1;
        j->s0 += v;
        j->s1 += v * idx;
        j->s2 += v * idx * idx;
    }
#endif
}

/* Scalar recompute of a full bin-shell journal (journal resync path). */
static inline void sq5_journal_recompute(sq5_torus_t *t, int b, int shell) {
    sq5_journal_t j = {0, 0, 0};
    for (int g = 0; g < SQ5_NR; g++) {
        if (!t->occ[b][g][shell]) continue;
        sq5_journal_add(&j, t->pay[b][g][shell], g);
    }
    t->jr[b][shell] = j;
}

/* Hot path: scatter (+fallback), write payload, stamp, journal. */
static inline int sq5_alloc(sq5_torus_t *t, int id, int item) {
    int b0 = SQ5_SCATLT[id & 31] % SQ5_NB;
    int bin = -1;
    for (int k = 0; k < SQ5_NB; k++) {
        int b = (b0 + k) % SQ5_NB;
        if (t->twhead[b] < SQ5_NR) { bin = b; break; }
    }
    if (bin < 0) return -1;
    int gen = t->twhead[bin];
    sq5_fill(t->pay[bin][gen][0], item);
    t->stamp[bin][gen][0] = sq5_stamp(bin, gen, 0);
    t->occ[bin][gen][0] = 1;
    sq5_journal_add(&t->jr[bin][0], t->pay[bin][gen][0], gen);
    sq5_item_at[bin][gen] = item;
    t->twhead[bin]++;
    t->ttotal++;
    return 0;
}

/* Replicate shell 0 -> shell 1 with verify-on-replicate flux check. */
static inline int sq5_rep(sq5_torus_t *t, long long *flux_breaks) {
    int copied = 0;
    for (int b = 0; b < SQ5_NB; b++) {
        for (int g = 0; g < SQ5_NR; g++) {
            if (!t->occ[b][g][0]) continue;
            memcpy(t->pay[b][g][1], t->pay[b][g][0], SQ5_PAY);
            t->stamp[b][g][1] = sq5_stamp(b, g, 1);
            t->occ[b][g][1] = 1;
            sq5_journal_add(&t->jr[b][1], t->pay[b][g][1], g);
            copied++;
        }
        sq5_journal_t *a = &t->jr[b][0], *c = &t->jr[b][1];
        if (a->s0 != c->s0 || a->s1 != c->s1 || a->s2 != c->s2)
            (*flux_breaks)++;
    }
    return copied;
}

/* ---------------- counterflow flux + triangulation ---------------- */

#define SQ5F_R0 1   /* shell-0 stream vs journal-0 residual nonzero */
#define SQ5F_R1 2   /* shell-1 stream vs journal-1 residual nonzero */
#define SQ5F_RX 4   /* cross-shell stream residual nonzero (shells differ) */

/* Counterflow sweep over one bin: forward stream (shell 0), backward
 * stream (shell 1, reversed gen/byte order), three residuals at closure. */
static inline int sq5_flux_bin(const sq5_torus_t *t, int b,
                               uint32_t ds[2][3]) {
    uint32_t a0 = 0, a1 = 0, a2 = 0;
    uint32_t c0 = 0, c1 = 0, c2 = 0;
    for (int g = 0; g < SQ5_NR; g++) {
        int gf = g, gb = SQ5_NR - 1 - g;
        if (t->occ[b][gf][0]) {
            uint32_t base = (uint32_t)gf * SQ5_PAY;
            for (int i = 0; i < SQ5_PAY; i++) {
                uint32_t v = t->pay[b][gf][0][i], idx = base + (uint32_t)i + 1;
                a0 += v; a1 += v * idx; a2 += v * idx * idx;
            }
        }
        if (t->occ[b][gb][1]) {
            uint32_t base = (uint32_t)gb * SQ5_PAY;
            for (int i = SQ5_PAY - 1; i >= 0; i--) {
                uint32_t v = t->pay[b][gb][1][i], idx = base + (uint32_t)i + 1;
                c0 += v; c1 += v * idx; c2 += v * idx * idx;
            }
        }
    }
    int flags = 0;
    ds[0][0] = a0 - t->jr[b][0].s0;
    ds[0][1] = a1 - t->jr[b][0].s1;
    ds[0][2] = a2 - t->jr[b][0].s2;
    ds[1][0] = c0 - t->jr[b][1].s0;
    ds[1][1] = c1 - t->jr[b][1].s1;
    ds[1][2] = c2 - t->jr[b][1].s2;
    if (ds[0][0] || ds[0][1] || ds[0][2]) flags |= SQ5F_R0;
    if (ds[1][0] || ds[1][1] || ds[1][2]) flags |= SQ5F_R1;
    if (a0 != c0 || a1 != c1 || a2 != c2)    flags |= SQ5F_RX;
    return flags;
}

/* classification codes */
enum {
    SQ5C_NONE = 0,
    SQ5C_JOUR0,     /* journal-0 corrupt (streams agree) -> resync */
    SQ5C_JOUR1,
    SQ5C_PAY0,      /* payload shell 0 -> SEC/tier2 */
    SQ5C_PAY1,
    SQ5C_PAY_BOTH,  /* both shells' payload (SEC each; tier2 from repaired) */
    SQ5C_JOUR_PAIR, /* r0+r1, no rx, unequal ds -> both journals suspect */
    SQ5C_ANOMALY    /* rx only: should be impossible via injection */
};

typedef struct {
    int      flags;
    uint32_t ds[2][3];
    int      cls;
    int      sec_p[2];   /* SEC position used per shell, 0 if none */
    int      tier[2];    /* 0 none, 1 SEC, 2 sibling-copy, 3 journal-resync */
    int      unresolved; /* shells left with open flux after repair */
} sq5_decision_t;

/* Tier 1: exact single-error correction via the moment triplet. */
static int sq5_try_sec(sq5_torus_t *t, int b, int shell,
                       const uint32_t ds[3], int *used_p) {
    int32_t d = (int32_t)ds[0];
    if (d != 0 && d >= -255 && d <= 255) {
        int32_t ds1 = (int32_t)ds[1];
        if (ds1 % d == 0) {
            int32_t p = ds1 / d;
            if (p >= 1 && p <= SQ5_BINBYTES) {
                uint32_t expect2 = (uint32_t)((int64_t)d * p * p);
                if (expect2 == ds[2]) {
                    int64_t o = p - 1;
                    int g = (int)(o / SQ5_PAY), i = (int)(o % SQ5_PAY);
                    t->pay[b][g][shell][i] =
                        (uint8_t)((t->pay[b][g][shell][i] - d) & 0xFF);
                    /* Journal is ALREADY correct: ds = corrupt_stream -
                     * journal, so restored content == journal exactly.
                     * (The prototype added ds to the journal here, leaving
                     * it desynced by exactly ds — caught by the closure
                     * oracle O6; the old harness never re-checked flux.) */
                    if (used_p) *used_p = (int)p;
                    return 1;
                }
            }
        }
    }
    return 0;
}

/* Tier 2: sibling-shell copy for multi-byte damage. */
static void sq5_tier2(sq5_torus_t *t, int b, int shell) {
    int good = shell ^ 1;
    memset(&t->jr[b][shell], 0, sizeof(sq5_journal_t));
    for (int g = 0; g < SQ5_NR; g++) {
        if (!t->occ[b][g][good]) continue;
        memcpy(t->pay[b][g][shell], t->pay[b][g][good], SQ5_PAY);
        t->stamp[b][g][shell] = sq5_stamp(b, g, shell);
        t->occ[b][g][shell] = 1;
        sq5_journal_add(&t->jr[b][shell], t->pay[b][g][shell], g);
    }
}

/* Classify a flagged bin.  full=1: three-residual triangulation.
 * full=0: legacy semantics (any shell residual => payload of that
 * shell; rx ignored) — retained to measure what triangulation costs
 * and what it buys. */
static inline void sq5_classify_bin(const sq5_torus_t *t, int b,
                                    sq5_decision_t *d, int full) {
    memset(d, 0, sizeof(*d));
    d->flags = sq5_flux_bin(t, b, d->ds);
    if (!full) {
        if (d->flags & SQ5F_R0) d->cls = SQ5C_PAY0;
        if (d->flags & SQ5F_R1) d->cls = (d->cls == SQ5C_PAY0) ? SQ5C_PAY_BOTH
                                                              : SQ5C_PAY1;
        return;
    }
    switch (d->flags) {
    case 0:                       d->cls = SQ5C_NONE; break;
    case SQ5F_R0:                 d->cls = SQ5C_JOUR0; break;
    case SQ5F_R1:                 d->cls = SQ5C_JOUR1; break;
    case SQ5F_R0|SQ5F_RX:         d->cls = SQ5C_PAY0; break;
    case SQ5F_R1|SQ5F_RX:         d->cls = SQ5C_PAY1; break;
    case SQ5F_R0|SQ5F_R1|SQ5F_RX: d->cls = SQ5C_PAY_BOTH; break;
    case SQ5F_R0|SQ5F_R1:
        /* identical corruption in both shells (streams still equal) is
         * SEC-able on each; unequal ds with agreeing streams means both
         * journals are suspect */
        d->cls = (memcmp(d->ds[0], d->ds[1], 3 * sizeof(uint32_t)) == 0)
                 ? SQ5C_PAY_BOTH : SQ5C_JOUR_PAIR;
        break;
    default:                      d->cls = SQ5C_ANOMALY; break;
    }
}

static void sq5_apply_repair(sq5_torus_t *t, int b, sq5_decision_t *d) {
    switch (d->cls) {
    case SQ5C_JOUR0:
        sq5_journal_recompute(t, b, 0);
        d->tier[0] = 3;
        break;
    case SQ5C_JOUR1:
        sq5_journal_recompute(t, b, 1);
        d->tier[1] = 3;
        break;
    case SQ5C_JOUR_PAIR:
        sq5_journal_recompute(t, b, 0);
        sq5_journal_recompute(t, b, 1);
        d->tier[0] = d->tier[1] = 3;
        break;
    case SQ5C_PAY0:
        if (sq5_try_sec(t, b, 0, d->ds[0], &d->sec_p[0])) d->tier[0] = 1;
        else { sq5_tier2(t, b, 0); d->tier[0] = 2; }
        break;
    case SQ5C_PAY1:
        if (sq5_try_sec(t, b, 1, d->ds[1], &d->sec_p[1])) d->tier[1] = 1;
        else { sq5_tier2(t, b, 1); d->tier[1] = 2; }
        break;
    case SQ5C_PAY_BOTH: {
        int ok0 = sq5_try_sec(t, b, 0, d->ds[0], &d->sec_p[0]);
        int ok1 = sq5_try_sec(t, b, 1, d->ds[1], &d->sec_p[1]);
        d->tier[0] = ok0 ? 1 : 0;
        d->tier[1] = ok1 ? 1 : 0;
        if (ok0 && !ok1) { sq5_tier2(t, b, 1); d->tier[1] = 2; }
        if (ok1 && !ok0) { sq5_tier2(t, b, 0); d->tier[0] = 2; }
        if (!ok0 && !ok1) d->unresolved = 2;
        break;
    }
    default: break;
    }
    /* verify closure */
    if (d->cls != SQ5C_NONE && d->cls != SQ5C_ANOMALY) {
        uint32_t chk[2][3];
        d->unresolved += (sq5_flux_bin(t, b, chk) != 0);
    }
}

/* Stamp integrity: stamps are pure position metadata, exactly
 * recomputable from coordinates (SQ4 semantics).  Returns mismatches;
 * fix=1 repairs in place; badmap (8 u64, NB*NR*2 bits) records slots. */
static inline long long sq5_stamp_check(sq5_torus_t *t, int fix, uint64_t *badmap) {
    long long bad = 0;
    for (int b = 0; b < SQ5_NB; b++)
        for (int g = 0; g < SQ5_NR; g++)
            for (int s = 0; s < 2; s++) {
                if (!t->occ[b][g][s]) continue;
                if (t->stamp[b][g][s] != sq5_stamp(b, g, s)) {
                    bad++;
                    if (badmap) {
                        int slot = (b * SQ5_NR + g) * 2 + s;
                        badmap[slot >> 6] |= 1ULL << (slot & 63);
                    }
                    if (fix) t->stamp[b][g][s] = sq5_stamp(b, g, s);
                }
            }
    return bad;
}

#endif /* SQ5_CORE_H */
