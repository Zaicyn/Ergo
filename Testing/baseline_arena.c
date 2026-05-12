/*
 * baseline_arena.c — four-variant diagnostic harness for Ergo's arena emit.
 *
 * Built during Pass 2 of the allocator comparison to isolate the per-iter
 * cost of Ergo's bump-with-bounds-check pattern from the cost of the
 * surrounding memory traffic. The harness exists because a naive
 * end-to-end timing of tests/allocate_bench.ergo reported 12.9 ns/alloc
 * — 25× higher than the predicted ~0.5 ns from the SASS — and turned out
 * to be dominated by the cost of writing to fresh DRAM cachelines, not by
 * the allocator itself.
 *
 * The four variants decompose that confusion:
 *
 *   variant=full     full arena emit + per-iter store to A[0] + wrap
 *   variant=nobump   no arena emit (A is pre-computed); per-iter store
 *   variant=nostore  full arena emit; register sink (no memory store)
 *   variant=walk     arena emit + store, no wrap (walks once, no revisit)
 *
 * Apples-to-apples comparison against the CPU bump floor in
 * baseline_bump.c uses `nostore`: both methodologies use a register
 * sink, so the timing isolates the arena emit instructions themselves.
 *
 * Build: gcc -O3 -march=x86-64-v3 -ffp-contract=fast -fno-math-errno -std=c11
 *
 * Reference: Pass 2 of the allocator comparison, documented in
 * Testing/COMPARISON_TABLE.md Sub-table 1 and Sub-table 2.
 */
#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#ifndef ERGO_ARENA_BYTES
#define ERGO_ARENA_BYTES ((size_t)1 << 30)
#endif
static char _ergo_arena[ERGO_ARENA_BYTES] __attribute__((aligned(64)));
static size_t _ergo_arena_offset = 0;

static double run_full(long N) {
    double total = 0.0;
    for (long I = 1; I <= N; I += 1) {
        double *A = NULL;
        {
            size_t _sz = (64) * sizeof(double);
            size_t _aligned = (_sz + 63) & ~(size_t)63;
            if (_ergo_arena_offset + _aligned > ERGO_ARENA_BYTES) _ergo_arena_offset = 0;
            A = (double *)(_ergo_arena + _ergo_arena_offset);
            _ergo_arena_offset += _aligned;
        }
        double v = (double)I;
        A[0] = v;
        total += A[0];
    }
    return total;
}

static double run_nobump(long N) {
    /* No arena emit; A points to a fixed location. The per-iter memory
     * store stays. */
    double total = 0.0;
    double *A = (double *)_ergo_arena;
    for (long I = 1; I <= N; I += 1) {
        double v = (double)I;
        A[0] = v;
        total += A[0];
    }
    return total;
}

static double run_nostore(long N) {
    /* Full arena emit, but no memory store; sink to a register. */
    double total = 0.0;
    uintptr_t sink = 0;
    for (long I = 1; I <= N; I += 1) {
        double *A = NULL;
        {
            size_t _sz = (64) * sizeof(double);
            size_t _aligned = (_sz + 63) & ~(size_t)63;
            if (_ergo_arena_offset + _aligned > ERGO_ARENA_BYTES) _ergo_arena_offset = 0;
            A = (double *)(_ergo_arena + _ergo_arena_offset);
            _ergo_arena_offset += _aligned;
        }
        sink ^= (uintptr_t)A;
        total += (double)I;
    }
    /* Use sink so the compiler can't DCE the arena emit. */
    return total + (double)(sink & 1);
}

static double run_arena_walk(long N) {
    /* Bump emit + write to A[0] each iter, but DON'T wrap — just touch
     * a fresh cacheline per iter walking through the arena. This isolates
     * the "walking through fresh DRAM" cost from the arena emit cost. */
    double total = 0.0;
    /* Reset offset to 0 each invocation. */
    _ergo_arena_offset = 0;
    /* Cap N so we don't exhaust the arena. */
    long max_iters = ERGO_ARENA_BYTES / 512;
    if (N > max_iters) N = max_iters;
    for (long I = 1; I <= N; I += 1) {
        double *A = (double *)(_ergo_arena + _ergo_arena_offset);
        _ergo_arena_offset += 512;
        double v = (double)I;
        A[0] = v;
        total += A[0];
    }
    return total;
}

int main(int argc, char *argv[]) {
    const char *variant = (argc > 1) ? argv[1] : "full";
    long N = (argc > 2) ? atol(argv[2]) : 50000000;

    struct timespec t0, t1;
    double total = 0.0;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    if      (!strcmp(variant, "full"))    total = run_full(N);
    else if (!strcmp(variant, "nobump"))  total = run_nobump(N);
    else if (!strcmp(variant, "nostore")) total = run_nostore(N);
    else if (!strcmp(variant, "walk"))    total = run_arena_walk(N);
    else { fprintf(stderr, "unknown variant '%s'\n", variant); return 2; }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double secs = (t1.tv_sec - t0.tv_sec) + 1e-9 * (t1.tv_nsec - t0.tv_nsec);
    double ns  = (secs * 1.0e9) / (double)N;
    printf("%-8s N=%ld in %.4f s = %.3f ns/iter (total=%g)\n",
           variant, N, secs, ns, total);
    return 0;
}
