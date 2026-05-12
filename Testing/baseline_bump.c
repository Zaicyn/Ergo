/*
 * baseline_bump.c — CPU bump-allocator floor measurement.
 *
 * Establishes the "do nothing" baseline for CPU allocation cost. Reports
 * three numbers:
 *
 *   1. Single-thread bump: load offset, add aligned size, return pointer.
 *      Pure increment, no contention. This is the absolute floor — no
 *      real allocator can be faster than this on the same hardware.
 *
 *   2. Multi-thread bump with per-thread arena: each thread bumps its own
 *      offset. Should scale linearly to N cores. This is what V22's
 *      lattice design effectively provides (sharded by geometry).
 *
 *   3. Multi-thread bump with shared atomic counter: all threads hammer
 *      one atomicAdd-equivalent. Contention dominates. This is the
 *      "naive shared counter" anti-pattern that V22's geometry exists
 *      to avoid.
 *
 * The difference between (2) and (3) is the contention cost — i.e., what
 * V22's lattice buys you over a flat shared bump.
 *
 * Build: gcc -O3 -march=native -fopenmp -std=c11 baseline_bump.c -o baseline_bump
 *
 * Methodology:
 *   - 50,000,000 bump_alloc(64) calls per measurement run, matching V22's
 *     iteration count for direct comparability.
 *   - 16-byte alignment on each allocation (matches the brief's spec).
 *   - 1 GB static arena per thread (per-thread case) or shared (atomic case).
 *   - Volatile sink prevents the optimizer from eliminating the loop body.
 *   - clock_gettime(CLOCK_MONOTONIC) for wall-clock timing.
 *   - Each thread count run as a separate sweep: 1, 2, 4, 6, 12.
 */

#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <stdatomic.h>
#include <omp.h>

#define ARENA_BYTES   (1ULL << 30)   /* 1 GB */
#define ALLOC_SIZE    64
#define ALIGN_MASK    15             /* 16-byte alignment */
#define TOTAL_ITERS   50000000

/* Per-thread arena: one big block, each thread owns its slice. We give each
 * thread (ARENA_BYTES / max_threads) bytes of headroom; with 50M × 64B = 3.2 GB
 * of total allocation across all threads, we need to be careful — for the
 * floor we don't actually keep allocations, we just want the bump cost. So we
 * reset each thread's offset modulo a smaller "virtual arena" to prevent
 * actually walking off the end. The bump cost is unchanged. */
#define PER_THREAD_VIRT_BYTES (1ULL << 28)   /* 256 MB rolling window per thread */

static char  _shared_arena[ARENA_BYTES] __attribute__((aligned(64)));
static atomic_uint_fast64_t _shared_offset = 0;

/* Per-thread arenas: we use a single big static array and slice it by tid,
 * but the offset is thread-local. Each thread gets PER_THREAD_VIRT_BYTES of
 * rolling space. */
static char  _per_thread_arena[ARENA_BYTES] __attribute__((aligned(64)));

static inline void* bump_alloc_local(uint64_t* offset, uint64_t base) {
    uint64_t p = (*offset + ALIGN_MASK) & ~(uint64_t)ALIGN_MASK;
    /* Wrap within the virtual per-thread window so we never overflow. */
    if (p + ALLOC_SIZE > PER_THREAD_VIRT_BYTES) p = 0;
    *offset = p + ALLOC_SIZE;
    return (void*)(_per_thread_arena + base + p);
}

static inline void* bump_alloc_shared(void) {
    /* fetch_add returns the *old* value; we treat that as our slot offset.
     * The +ALLOC_SIZE is rolled into the fetch_add argument so the next
     * thread sees the advanced offset. Alignment is implicit because
     * ALLOC_SIZE (64) is already a multiple of ALIGN_MASK+1 (16). */
    uint64_t p = atomic_fetch_add_explicit(&_shared_offset,
                                            (uint64_t)ALLOC_SIZE,
                                            memory_order_relaxed);
    /* Wrap so we don't overflow on long runs. */
    if (p + ALLOC_SIZE > ARENA_BYTES) {
        atomic_store_explicit(&_shared_offset, 0, memory_order_relaxed);
        p = 0;
    }
    return (void*)(_shared_arena + p);
}

static void run_single_thread(long iters) {
    uint64_t offset = 0;
    volatile uintptr_t sink = 0;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long i = 0; i < iters; i++) {
        void* p = bump_alloc_local(&offset, 0);
        sink ^= (uintptr_t)p;
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double secs = (t1.tv_sec - t0.tv_sec) + 1e-9 * (t1.tv_nsec - t0.tv_nsec);
    double mps  = (double)iters / secs / 1.0e6;
    double ns   = (secs * 1.0e9) / (double)iters;
    printf("single-thread (per-arena):  %ld allocs in %.4f s = %7.1f M/s, %5.2f ns/alloc (sink=%lx)\n",
           iters, secs, mps, ns, (unsigned long)sink);
}

static void run_per_thread(long total_iters, int nthreads) {
    omp_set_num_threads(nthreads);
    volatile uintptr_t sinks[64] = {0};

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    #pragma omp parallel
    {
        int tid = omp_get_thread_num();
        uint64_t offset = 0;
        uint64_t base = (uint64_t)tid * PER_THREAD_VIRT_BYTES;
        uintptr_t local_sink = 0;

        #pragma omp for schedule(static)
        for (long i = 0; i < total_iters; i++) {
            void* p = bump_alloc_local(&offset, base);
            local_sink ^= (uintptr_t)p;
        }
        sinks[tid] = local_sink;
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double secs = (t1.tv_sec - t0.tv_sec) + 1e-9 * (t1.tv_nsec - t0.tv_nsec);
    double mps  = (double)total_iters / secs / 1.0e6;
    double ns   = (secs * 1.0e9) / (double)total_iters;

    uintptr_t sink_xor = 0;
    for (int t = 0; t < nthreads; t++) sink_xor ^= sinks[t];
    printf("%2dt per-thread arena:        %ld allocs in %.4f s = %7.1f M/s, %5.2f ns/alloc (sink=%lx)\n",
           nthreads, total_iters, secs, mps, ns, (unsigned long)sink_xor);
}

static void run_shared_atomic(long total_iters, int nthreads) {
    omp_set_num_threads(nthreads);
    atomic_store(&_shared_offset, 0);
    volatile uintptr_t sinks[64] = {0};

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    #pragma omp parallel
    {
        int tid = omp_get_thread_num();
        uintptr_t local_sink = 0;

        #pragma omp for schedule(static)
        for (long i = 0; i < total_iters; i++) {
            void* p = bump_alloc_shared();
            local_sink ^= (uintptr_t)p;
        }
        sinks[tid] = local_sink;
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double secs = (t1.tv_sec - t0.tv_sec) + 1e-9 * (t1.tv_nsec - t0.tv_nsec);
    double mps  = (double)total_iters / secs / 1.0e6;
    double ns   = (secs * 1.0e9) / (double)total_iters;

    uintptr_t sink_xor = 0;
    for (int t = 0; t < nthreads; t++) sink_xor ^= sinks[t];
    printf("%2dt shared atomic counter:   %ld allocs in %.4f s = %7.1f M/s, %5.2f ns/alloc (sink=%lx)\n",
           nthreads, total_iters, secs, mps, ns, (unsigned long)sink_xor);
}

int main(int argc, char **argv) {
    long iters = TOTAL_ITERS;
    if (argc > 1) iters = atol(argv[1]);
    if (iters <= 0) {
        fprintf(stderr, "usage: %s [total_iters]\n", argv[0]);
        return 2;
    }

    printf("CPU bump-allocator floor — %ld iters, 64B allocations, 16B alignment\n", iters);
    printf("Arena: per-thread 256 MB rolling window | Shared 1 GB with atomic counter\n\n");

    printf("--- Single-thread floor (no contention possible) ---\n");
    run_single_thread(iters);

    printf("\n--- Multi-thread per-thread arena (should scale linearly) ---\n");
    for (int n = 1; n <= 12; n = (n == 1) ? 2 : (n == 2) ? 4 : (n == 4) ? 6 : 12) {
        run_per_thread(iters, n);
        if (n == 12) break;
    }

    printf("\n--- Multi-thread shared atomic counter (contention dominates) ---\n");
    for (int n = 1; n <= 12; n = (n == 1) ? 2 : (n == 2) ? 4 : (n == 4) ? 6 : 12) {
        run_shared_atomic(iters, n);
        if (n == 12) break;
    }

    return 0;
}
