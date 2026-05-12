/*
 * v22_parallel.c — V22 multi-threaded throughput driver.
 *
 * Companion to v22_compare.c (single-threaded). This file isolates the
 * OpenMP scaling measurement so the 469 M/s 6-core number cited in
 * Testing/V8_VS_V22_HEAD_TO_HEAD.md is reproducible from in-tree source.
 *
 * Methodology (matches the original measurement exactly):
 *   - 50,000,000 residual computations divided across N threads.
 *   - Per-thread gate array of 256 pre-initialized gates indexed (i & 0xFF)
 *     to defeat constant-folding without paying sq2_init cost in the hot loop.
 *   - hand-SSE path (sq2_simd_triple_xor_residual_sse) — same path benchmarked
 *     in v22_compare.c.
 *   - Wall-clock timing via clock_gettime(CLOCK_MONOTONIC).
 *   - Volatile sink accumulator per thread, reduced at the end, so the
 *     compiler can't eliminate the loop.
 *
 * Invoke as:   ./v22_parallel <total_iters> <nthreads>
 * The doc reports 1, 2, 4, 6, 12 thread sweeps at 50,000,000 total iters.
 *
 * Build: gcc -O3 -march=native -fopenmp -std=c11 -IV22 v22_parallel.c -o v22_parallel -lm
 */

#define _POSIX_C_SOURCE 199309L
#include <math.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <omp.h>

#include "squaragon_v2.h"

int main(int argc, char **argv) {
    long total_iters = 50000000;
    int  nthreads    = 6;

    if (argc > 1) total_iters = atol(argv[1]);
    if (argc > 2) nthreads    = atoi(argv[2]);
    if (total_iters <= 0 || nthreads <= 0) {
        fprintf(stderr, "usage: %s <total_iters> <nthreads>\n", argv[0]);
        return 2;
    }

    omp_set_num_threads(nthreads);

    /* Per-thread gate arrays. Pre-init avoids paying sq2_init cost inside
     * the timed loop, matching the single-threaded v22_compare driver. */
    float scale_base = 1.0f + 0.01f * (float)argc;
    sq2_gate_t gates[256];
    for (int k = 0; k < 256; k++) {
        sq2_init(&gates[k], scale_base + 1e-4f * (float)k);
    }

    /* Per-thread sinks so accumulation has no cross-thread sharing. */
    volatile double sinks[64] = {0};
    if (nthreads > 64) {
        fprintf(stderr, "nthreads must be <= 64\n");
        return 2;
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    #pragma omp parallel
    {
        int tid = omp_get_thread_num();
        double local = 0.0;

        #pragma omp for schedule(static)
        for (long i = 0; i < total_iters; i++) {
            __m128 v = sq2_simd_triple_xor_residual_sse(gates[i & 0xFF].scale);
            local += (double)_mm_cvtss_f32(v);
        }
        sinks[tid] = local;
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double secs = (t1.tv_sec - t0.tv_sec) + 1e-9 * (t1.tv_nsec - t0.tv_nsec);

    double sink_total = 0.0;
    for (int t = 0; t < nthreads; t++) sink_total += sinks[t];

    double mps = (double)total_iters / secs / 1.0e6;
    double ns  = (secs * 1.0e9) / (double)total_iters;
    printf("%2d threads: %ld residuals in %.4f s = %7.1f M/s, %5.2f ns/call (sink=%g)\n",
           nthreads, total_iters, secs, mps, ns, sink_total);
    return 0;
}
