/* squaragon_v2_bio.h — SQ2B: biologically-revised Squaragon v2 cell.
 *
 * What the ribosome/transcription/cell campaigns taught, applied to V22:
 *
 *   duplex complementarity  shell 1 stores the base-complement of the
 *                           payload (2-bit pairing A<->T C<->G == byte ^ 0x55).
 *                           Mismatch detection localizes damage PER BYTE
 *                           with no moment arithmetic at all.
 *   strand-directed MMR     each strand carries a self-syndrome over its
 *      (MutS/MutH)           decoded content; on a duplex mismatch the
 *                           strand whose syndrome fails is the damaged one.
 *                           Arbitration is structural — no shell-0-golden.
 *   excision repair (NER)   a damaged codon is RESYNTHESIZED wholesale
 *                           from the intact strand, never byte-patched.
 *   kinetic proofreading    two-stage commit: write both strands, re-read,
 *      (ribosome/Hopfield)   verify duplex + syndromes, THEN mark occupied.
 *                           One retry (the GTP cost), else alloc refused.
 *   hemimethylation         shell 0 is the methylated template, shell 1 the
 *                           nascent strand; a clean sweep ages it. Both-
 *                           syndrome-pass conflicts resolve to the elder.
 *   apoptosis               both strands damaged in one codon: tombstone
 *                           magic, loudly counted. Nothing propagates.
 *   transcription           reads decode from the template; the working
 *                           copy (RNA) is disposable and unchecked.
 *
 * What this buys over V22 and over moment-journal schemes: multi-byte
 * damage confined to one strand is FULLY repairable (the complement
 * strand arbitrates), and localization is per-byte.  What it does NOT
 * fix: coordinated dual-strand consistent corruption (mapped in
 * sq2b_cert.c — the documented exclusion).
 *
 * Conventions honored: no clamping without a physical reason, loud
 * failure over silent, every mechanism scored by an oracle.
 */
#ifndef SQUARAGON_V2_BIO_H
#define SQUARAGON_V2_BIO_H

#include <stdint.h>
#include <string.h>

#ifndef SQB_NB
#define SQB_NB   8
#endif
#ifndef SQB_NR
#define SQB_NR   32
#endif

#define SQB_PAY       152                 /* V22 gate: 144 vertex + scale/bias */
#define SQB_CAPACITY  (SQB_NB * SQB_NR)
#define SQB_COMPLEMENT 0x55               /* 2-bit base-pair complement */
#define SQB_TOMB_MAGIC 0xDEAD5EEDu

/* baked Viviani scatter (SQ4-verified LUT: total=52, HOPFQ=1.97) */
static const int SQB_SCATLT[32] = {
    6, 5, 4, 0, 2, 3, 4, 7, 4, 6, 3, 0, 1, 2, 1, 0,
    3, 6, 4, 7, 4, 3, 2, 0, 4, 5, 6, 5, 4, 0, 2, 3
};

typedef struct {
    uint8_t  g[SQB_PAY];   /* strand content (shell 1 stores complement) */
    uint32_t syn0, syn1;   /* self-syndrome over DECODED content, mod 2^32 */
    uint32_t age;          /* sweeps survived clean (methylation clock) */
    uint32_t tomb;         /* 0 alive, SQB_TOMB_MAGIC apoptosed */
} sqb_codon_t;             /* 168 B */

typedef struct {
    sqb_codon_t c[SQB_NB][SQB_NR][2];   /* [bin][gen][strand] */
    int8_t      occ[SQB_NB][SQB_NR];    /* codon occupied (duplex unit) */
    int         head[SQB_NB];
    int         total;
    long long   proofread_retries;      /* kinetic proofreading energy bill */
    long long   tombstones;             /* apoptosis count */
    long long   slippage;               /* both-pass conflicts, elder won */
} sqb_cell_t;

/* bench-side bookkeeping: which item lives in each codon */
static int sqb_item_at[SQB_NB][SQB_NR];

static inline void sqb_init(sqb_cell_t *t) { memset(t, 0, sizeof(*t)); }

/* deterministic payload for the harness */
static inline void sqb_fill(uint8_t *p, int item) {
    for (int i = 0; i < SQB_PAY; i++)
        p[i] = (uint8_t)((item * 17 + i * 91) ^ 0xA5);
}
static inline int sqb_pay_ok(const uint8_t *p, int item) {
    for (int i = 0; i < SQB_PAY; i++)
        if (p[i] != (uint8_t)((item * 17 + i * 91) ^ 0xA5)) return 0;
    return 1;
}

/* self-syndrome over decoded content */
static inline void sqb_syn(const uint8_t *decoded, uint32_t *s0, uint32_t *s1) {
    uint32_t a = 0, b = 0;
    for (int i = 0; i < SQB_PAY; i++) {
        a += decoded[i];
        b += decoded[i] * (uint32_t)(i + 1);
    }
    *s0 = a; *s1 = b;
}

static inline int sqb_strand_ok(const sqb_codon_t *c, int strand) {
    uint8_t dec[SQB_PAY];
    uint32_t a, b;
    if (strand == 0) {
        sqb_syn(c->g, &a, &b);
    } else {
        for (int i = 0; i < SQB_PAY; i++) dec[i] = (uint8_t)(c->g[i] ^ SQB_COMPLEMENT);
        sqb_syn(dec, &a, &b);
    }
    return a == c->syn0 && b == c->syn1;
}

/* duplex mismatch mask: 1 bit per byte where the pair disagrees */
static inline int sqb_duplex_mismatch(const sqb_codon_t *c0, const sqb_codon_t *c1,
                                      uint8_t *mm /* SQB_PAY bytes, or NULL */) {
    int n = 0;
    for (int i = 0; i < SQB_PAY; i++) {
        int bad = (uint8_t)(c0->g[i] ^ c1->g[i]) != SQB_COMPLEMENT;
        if (mm) mm[i] = (uint8_t)bad;
        n += bad;
    }
    return n;
}

/* write one strand from decoded content */
static inline void sqb_strand_write(sqb_codon_t *c, const uint8_t *decoded, int strand) {
    if (strand == 0) {
        memcpy(c->g, decoded, SQB_PAY);
    } else {
        for (int i = 0; i < SQB_PAY; i++) c->g[i] = (uint8_t)(decoded[i] ^ SQB_COMPLEMENT);
    }
    sqb_syn(decoded, &c->syn0, &c->syn1);
    c->age = 0;
    c->tomb = 0;
}

/* excision resynthesis: rebuild `dst` strand wholesale from `src` */
static inline void sqb_excise(sqb_codon_t *dst, const sqb_codon_t *src, int dst_strand) {
    uint8_t dec[SQB_PAY];
    if (src == dst) return;
    /* decode src */
    if (dst_strand == 1) {          /* src is strand 0 */
        memcpy(dec, src->g, SQB_PAY);
    } else {                        /* src is strand 1 */
        for (int i = 0; i < SQB_PAY; i++) dec[i] = (uint8_t)(src->g[i] ^ SQB_COMPLEMENT);
    }
    uint32_t age = dst->age;        /* age belongs to the codon lineage */
    sqb_strand_write(dst, dec, dst_strand);
    dst->age = age;
}

/* two-stage commit with kinetic proofreading.  Three fused passes over
 * the payload: fill+syn (dec), strand-1 complement write, then ONE
 * re-read verify (duplex consistency + strand-0 syndrome in the same
 * pass — strand-1's syndrome is implied by duplex consistency).
 * Returns 0 on charged (occupied) codon, -1 on refusal after one retry. */
static inline int sqb_proofread_commit(sqb_cell_t *t, int b, int g, int item) {
    uint8_t dec[SQB_PAY];
    uint32_t a = 0, s1 = 0;
    for (int i = 0; i < SQB_PAY; i++) {
        dec[i] = (uint8_t)((item * 17 + i * 91) ^ 0xA5);
        a += dec[i];
        s1 += dec[i] * (uint32_t)(i + 1);
    }
    for (int attempt = 0; attempt < 2; attempt++) {
        sqb_codon_t *c0 = &t->c[b][g][0], *c1 = &t->c[b][g][1];
        memcpy(c0->g, dec, SQB_PAY);
        c0->syn0 = a; c0->syn1 = s1; c0->age = 0; c0->tomb = 0;
        for (int i = 0; i < SQB_PAY; i++)
            c1->g[i] = (uint8_t)(dec[i] ^ SQB_COMPLEMENT);
        c1->syn0 = a; c1->syn1 = s1; c1->age = 0; c1->tomb = 0;
        /* fused re-read verify */
        uint32_t va = 0, vs = 0;
        int mm = 0;
        for (int i = 0; i < SQB_PAY; i++) {
            mm |= ((uint8_t)(c0->g[i] ^ c1->g[i]) != SQB_COMPLEMENT);
            va += c0->g[i];
            vs += c0->g[i] * (uint32_t)(i + 1);
        }
        if (!mm && va == c0->syn0 && vs == c0->syn1) {
            t->occ[b][g] = 1;
            sqb_item_at[b][g] = item;
            return 0;
        }
        t->proofread_retries++;     /* GTP hydrolyzed, discard and retry */
    }
    return -1;                      /* refused: nothing occupied */
}

/* hot path: scatter (+overflow fallback), proofread commit.
 * sqb_alloc_slot also reports the landing slot (recognition cache
 * needs it; scanning for it afterwards costs more than the write). */
static inline int sqb_alloc_slot(sqb_cell_t *t, int id, int item,
                                 int *out_b, int *out_g) {
    int b0 = SQB_SCATLT[id & 31] % SQB_NB;
    int bin = -1;
    for (int k = 0; k < SQB_NB; k++) {
        int b = (b0 + k) % SQB_NB;
        if (t->head[b] < SQB_NR) { bin = b; break; }
    }
    if (bin < 0) return -1;
    int g = t->head[bin];
    if (sqb_proofread_commit(t, bin, g, item) != 0) return -1;
    t->head[bin]++;
    t->total++;
    if (out_b) *out_b = bin;
    if (out_g) *out_g = g;
    return 0;
}
static inline int sqb_alloc(sqb_cell_t *t, int id, int item) {
    return sqb_alloc_slot(t, id, item, NULL, NULL);
}

/* transcription: decode a working copy from the template strand.
 * The RNA copy is disposable — no integrity burden travels with it.
 * Returns 0 on success, 1 if the codon is apoptosed. */
static inline int sqb_transcribe(const sqb_cell_t *t, int b, int g, uint8_t *out) {
    const sqb_codon_t *c0 = &t->c[b][g][0];
    if (c0->tomb == SQB_TOMB_MAGIC) return 1;
    memcpy(out, c0->g, SQB_PAY);
    return 0;
}

/* ---------------- G2 sweep: mismatch repair + methylation ----------------
 * For every occupied codon: localize duplex mismatches per byte,
 * arbitrate by strand self-syndrome, excision-resynthesize the damaged
 * strand, tombstone the doubly-damaged, age the clean.
 * action[b*SQB_NR+g] (if non-NULL): 0 untouched, 1 repaired, 2 tombstoned.
 * Returns codons still failing closure after the sweep (must be 0). */
static inline long long sqb_sweep(sqb_cell_t *t, uint8_t *action) {
    long long unresolved = 0;
    for (int b = 0; b < SQB_NB; b++)
        for (int g = 0; g < SQB_NR; g++) {
            if (!t->occ[b][g]) continue;
            sqb_codon_t *c0 = &t->c[b][g][0], *c1 = &t->c[b][g][1];
            if (action) action[b * SQB_NR + g] = 0;
            if (c0->tomb == SQB_TOMB_MAGIC) continue;   /* already dead */
            int mm = sqb_duplex_mismatch(c0, c1, NULL);
            int ok0 = sqb_strand_ok(c0, 0);
            int ok1 = sqb_strand_ok(c1, 1);
            if (mm == 0 && ok0 && ok1) {
                c0->age++; c1->age++;                   /* methylation clock */
                continue;
            }
            if (action) action[b * SQB_NR + g] = 1;
            if (ok0 && !ok1) {
                sqb_excise(c1, c0, 1);
            } else if (!ok0 && ok1) {
                sqb_excise(c0, c1, 0);
            } else if (ok0 && ok1) {
                /* both syndromes pass but the duplex disagrees:
                 * replication slippage or syndrome collision — the
                 * methylated elder template wins */
                sqb_excise(c1, c0, 1);
                t->slippage++;
            } else {
                /* both strands damaged: apoptosis, loud */
                c0->tomb = SQB_TOMB_MAGIC;
                c1->tomb = SQB_TOMB_MAGIC;
                t->tombstones++;
                if (action) action[b * SQB_NR + g] = 2;
            }
            /* closure verify: the codon must now read clean */
            if (c0->tomb != SQB_TOMB_MAGIC) {
                if (sqb_duplex_mismatch(c0, c1, NULL) != 0 ||
                    !sqb_strand_ok(c0, 0) || !sqb_strand_ok(c1, 1))
                    unresolved++;
            }
        }
    return unresolved;
}

#endif /* SQUARAGON_V2_BIO_H */
