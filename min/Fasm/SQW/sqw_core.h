/* sqw_core.h — SQW: write-skip (memoized) duplex cell.
 *
 * Biology: molecular recognition / immune memory.  The cell does not
 * re-synthesize a molecule it already holds: a recognition pass
 * (content hash + exact verify — the antigen check) precedes any
 * synthesis, and a hit skips the ENTIRE duplex proofread write.
 * Recognition is fail-safe: the index is a disposable cache, exact
 * byte-verify arbitrates, so index corruption can only cause a missed
 * skip, never wrong data.
 *
 * New integrity surface vs SQ2B (measured, not assumed):
 *   - blast-radius amplification: one physical codon serves N logical
 *     items; one corruption threatens N reads.  Reported per item AND
 *     per codon.
 *   - refcount is a check-field: stored complement-paired
 *     (lo | ~lo<<16), per-slot detectable.  Repair of a poisoned
 *     refcount is impossible without the logical map — detected,
 *     counted, payload unaffected.
 *   - index needs NO integrity: recognition always verifies byte-exact
 *     before skipping.  Documented fail-safe class.
 */
#ifndef SQW_CORE_H
#define SQW_CORE_H

#include "squaragon_v2_bio.h"

#define SQW_IDX 4096   /* direct-mapped recognition cache, power of 2 */

typedef struct {
    uint64_t h;
    uint8_t  b, g, used;
} sqw_ent_t;

typedef struct {
    sqb_cell_t cell;
    sqw_ent_t  idx[SQW_IDX];
    uint32_t   ref[SQB_NB][SQB_NR];   /* lo16 = count, hi16 = ~count */
    long long  refs_total;            /* counting oracle: == logical items */
    long long  skips;                 /* write-skip hits */
    long long  phys_allocs;           /* actual duplex writes */
} sqw_cell_t;

/* logical item -> slot map (bench bookkeeping) */
static int sqw_item_slot_b[SQB_CAPACITY * 4];
static int sqw_item_slot_g[SQB_CAPACITY * 4];

static inline void sqw_init(sqw_cell_t *w) {
    memset(w, 0, sizeof(*w));
    sqb_init(&w->cell);
}

/* Recognition hash over the decoded payload.  Word-wise, NOT byte-wise:
 * a byte-serial FNV chain is 152 dependent multiply links (~250 ns) —
 * the CRC32C serial-latency lesson.  19 word links + finalizer. */
static inline uint64_t sqw_hash(const uint8_t *p) {
    uint64_t h = 0x9E3779B97F4A7C15ULL;
    for (int i = 0; i < SQB_PAY / 8; i++) {
        uint64_t x;
        memcpy(&x, p + i * 8, 8);
        h = (h ^ x) * 0x100000001b3ULL;
    }
    h ^= h >> 29;
    h *= 0xBF58476D1CE4E5B9ULL;
    h ^= h >> 32;
    return h;
}

static inline int sqw_ref_ok(uint32_t r) {
    return ((r & 0xFFFFu) + (r >> 16)) == 0xFFFFu;
}
static inline uint32_t sqw_ref_inc(uint32_t r) {
    uint32_t lo = (r & 0xFFFFu) + 1;
    return lo | ((~lo & 0xFFFFu) << 16);
}
static inline uint32_t sqw_ref_one(void) { return 1u | (0xFFFEu << 16); }

/* Write-skip alloc: recognition pass first.
 *  1. hash the payload-to-be
 *  2. probe the recognition cache; on candidate, VERIFY byte-exact
 *     against the methylated template (fail-safe arbitration)
 *  3. hit: refcount++, done — no write, no journal, no proofread
 *  4. miss: full SQ2B proofread commit, insert into cache
 * Returns 0 on success (skip or write), -1 on cell full. */
static inline int sqw_alloc(sqw_cell_t *w, int id, int item) {
    uint8_t dec[SQB_PAY];
    sqb_fill(dec, item);
    uint64_t h = sqw_hash(dec);
    sqw_ent_t *e = &w->idx[h & (SQW_IDX - 1)];
    if (e->used && e->h == h) {
        sqb_codon_t *c0 = &w->cell.c[e->b][e->g][0];
        if (c0->tomb != SQB_TOMB_MAGIC &&
            memcmp(c0->g, dec, SQB_PAY) == 0) {
            /* recognition confirmed — skip synthesis entirely */
            w->ref[e->b][e->g] = sqw_ref_inc(w->ref[e->b][e->g]);
            w->refs_total++;
            w->skips++;
            sqw_item_slot_b[item] = e->b;
            sqw_item_slot_g[item] = e->g;
            return 0;
        }
        /* stale/poisoned entry: fall through to physical write.
         * The cache is wrong but nothing propagates — fail-safe. */
    }
    int b = -1, g = -1;
    if (sqb_alloc_slot(&w->cell, id, item, &b, &g) != 0) return -1;
    w->ref[b][g] = sqw_ref_one();
    w->refs_total++;
    w->phys_allocs++;
    e->h = h; e->b = (uint8_t)b; e->g = (uint8_t)g; e->used = 1;
    sqw_item_slot_b[item] = b;
    sqw_item_slot_g[item] = g;
    return 0;
}

/* refcount audit: per-slot pair check + global counting oracle.
 * Returns flagged slots; *sum_ok set to 1 if refs_total matches the
 * on-cell sum (global consistency). */
static inline long long sqw_ref_audit(const sqw_cell_t *w, int *sum_ok) {
    long long bad = 0, sum = 0;
    for (int b = 0; b < SQB_NB; b++)
        for (int g = 0; g < SQB_NR; g++) {
            if (!w->cell.occ[b][g]) continue;
            if (!sqw_ref_ok(w->ref[b][g])) bad++;
            else sum += w->ref[b][g] & 0xFFFFu;
        }
    *sum_ok = (sum == w->refs_total);
    return bad;
}

#endif /* SQW_CORE_H */
