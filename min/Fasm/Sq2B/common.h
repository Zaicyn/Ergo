/* common.h — shared utilities for the allocator/streaming comparison harness.
 *
 * The goal is to compare three scheduling/integrity systems on the same
 * dimensions even though their native APIs differ:
 *   - V8_bounded  : CUDA warp-cooperative slab allocator
 *   - V22         : squaragon cell/DNA allocator + replication repair
 *   - ESF         : framed stream format with weighted-syndrome integrity
 *
 * Metrics collected for each system:
 *   alloc_items/sec, ns/item, error_detection_rate, error_correction_rate,
 *   coherency_failure_rate.
 */

#ifndef ALLOCATOR_CMP_COMMON_H
#define ALLOCATOR_CMP_COMMON_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef __MACH__
#include <mach/mach_time.h>
#endif

#define CMP_NAME_MAX 32

typedef struct {
    char name[CMP_NAME_MAX];
    long long items;            /* slots / codons / frames processed */
    double alloc_sec;           /* wall time for alloc/write phase */
    double alloc_mips;          /* items / sec / 1e6 */
    double ns_per_item;         /* alloc_sec * 1e9 / items */
    long long injected;         /* deliberate errors injected */
    long long detected;         /* errors the system noticed */
    long long repaired;         /* errors the system fixed */
    long long coherency_fail;   /* readback mismatches after churn */
    long long coherency_total;  /* total readback checks */
    long long alloc_fail;       /* allocation attempts silently rejected */
    int available;              /* 1 if this system was built/run */

    /* Cache performance counters (Linux perf_event_open) */
    int cache_available;
    uint64_t l1d_loads;
    uint64_t l1d_misses;
    uint64_t llc_refs;
    uint64_t llc_misses;
    uint64_t instructions;
} cmp_result_t;

static inline double cmp_now_sec(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        fprintf(stderr, "clock_gettime failed\n");
        exit(1);
    }
    return (double)ts.tv_sec + 1e-9 * (double)ts.tv_nsec;
}

static inline uint64_t cmp_xoshiro256ss(uint64_t *s) {
    uint64_t x = s[0] + s[3];
    uint64_t t = s[1] << 17;
    s[2] ^= s[0];
    s[3] ^= s[1];
    s[1] ^= s[2];
    s[0] ^= s[3];
    s[2] ^= t;
    s[3] = (s[3] << 45) | (s[3] >> 19);
    return (x << 17) | (x >> 47);
}

static inline uint32_t cmp_rand_u32(uint64_t *s) {
    return (uint32_t)cmp_xoshiro256ss(s);
}

static inline double cmp_rand01(uint64_t *s) {
    return (cmp_xoshiro256ss(s) >> 11) * (1.0 / (1ULL << 53));
}

static inline void cmp_seed(uint64_t *s, uint64_t seed) {
    s[0] = seed + 0x9E3779B97F4A7C15ULL;
    s[1] = seed ^ 0xBF58476D1CE4E5B9ULL;
    s[2] = seed + 0x94D049BB133111EBULL;
    s[3] = seed ^ 0xF0BA35E12960E9E7ULL;
    for (int i = 0; i < 10; i++) (void)cmp_xoshiro256ss(s);
}

/* Select `inj` unique indices out of [0, total) without replacement via a
 * partial Fisher-Yates shuffle.  Returns a malloc'd array of length inj
 * (caller frees), or NULL on allocation failure.  Use this for error
 * injection so `injected` counts distinct corrupted units and det_% is a
 * true detection rate rather than a collision artifact. */
static inline long long *cmp_pick_unique(long long total, long long inj, uint64_t *rng) {
    if (inj > total) inj = total;
    long long *idx = (long long *)malloc((size_t)total * sizeof(long long));
    if (!idx) return NULL;
    for (long long i = 0; i < total; i++) idx[i] = i;
    for (long long i = 0; i < inj; i++) {
        long long j = i + (long long)(cmp_rand01(rng) * (double)(total - i));
        if (j >= total) j = total - 1;
        long long t = idx[i]; idx[i] = idx[j]; idx[j] = t;
    }
    return idx;
}

static inline void cmp_print_result(const cmp_result_t *r) {
    if (!r->available) {
        printf("%-12s  not built / not run\n", r->name);
        return;
    }
    double det_pct  = r->injected ? 100.0 * (double)r->detected / (double)r->injected : 0.0;
    double rep_pct  = r->detected ? 100.0 * (double)r->repaired / (double)r->detected : 0.0;
    double coh_pct  = r->coherency_total ? 100.0 * (double)r->coherency_fail / (double)r->coherency_total : 0.0;
    printf("%-12s  items=%10lld  alloc=%8.3f M/s  %8.2f ns/item  "
           "det=%6.2f%%  rep=%6.2f%%  coh_fail=%6.4f%% (%lld/%lld)\n",
           r->name, r->items, r->alloc_mips, r->ns_per_item,
           det_pct, rep_pct, coh_pct, r->coherency_fail, r->coherency_total);
    if (r->alloc_fail > 0) {
        printf("%-12s  WARNING: %lld allocation attempts silently rejected "
               "(throughput includes fast-fail no-ops)\n", "", r->alloc_fail);
    }
    if (r->cache_available) {
        double l1_hit = (r->l1d_loads > r->l1d_misses)
            ? 100.0 * (double)(r->l1d_loads - r->l1d_misses) / (double)r->l1d_loads : 0.0;
        double llc_hit = (r->llc_refs > r->llc_misses)
            ? 100.0 * (double)(r->llc_refs - r->llc_misses) / (double)r->llc_refs : 0.0;
        printf("%-12s  cache: L1_hit=%5.2f%%  LLC_hit=%5.2f%%  "
               "L1_miss/item=%.4f  LLC_miss/item=%.4f  instr/item=%.1f\n",
               r->name, l1_hit, llc_hit,
               r->items ? (double)r->l1d_misses / (double)r->items : 0.0,
               r->items ? (double)r->llc_misses / (double)r->items : 0.0,
               r->items ? (double)r->instructions / (double)r->items : 0.0);
    }
}

#endif /* ALLOCATOR_CMP_COMMON_H */
