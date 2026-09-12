/*
 * v22_compare.c - Apples-to-apples comparison of three residual implementations:
 *   1. scalar       — sq2_triple_xor_residual_full (manually unrolled, scalar source)
 *   2. hand-sse     — sq2_simd_triple_xor_residual_sse (__m128 intrinsics)
 *   3. inline-sse   — wrapper that pulls out a single lane (matches what driver does)
 *
 * Each is exposed as a non-inline function (via __attribute__((noinline))) so
 * its asm body is preserved and labeled. We also keep a "hot" main loop that
 * calls each via a runtime-chosen scale so const-folding can't eat the body.
 */

#define _POSIX_C_SOURCE 199309L   /* for clock_gettime under -std=c11 */
#include <math.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#include "squaragon_v2.h"

/* Force the compiler to emit standalone copies with stable symbols
 * so we can examine each in isolation. */

__attribute__((noinline))
float bench_scalar(const sq2_gate_t *g) {
    return sq2_triple_xor_residual_full(g);
}

#if defined(__SSE__)
__attribute__((noinline))
float bench_handsse(float scale) {
    __m128 v = sq2_simd_triple_xor_residual_sse(scale);
    return _mm_cvtss_f32(v);
}
#endif

int main(int argc, char **argv) {
    /* runtime-dependent scale defeats constant folding */
    float scale = 1.0f + 0.01f * (float)argc;

    sq2_gate_t gate;
    sq2_init(&gate, scale);

    float r_scalar = bench_scalar(&gate);

#if defined(__SSE__)
    float r_handsse = bench_handsse(scale);
#else
    float r_handsse = 0.0f;
#endif

    /* Two separate hot loops so we time each function on its own.
     * Both loops vary their input per iteration to defeat hoisting. */
    int iters = 1000000;
    if (argc > 1) iters = atoi(argv[1]);

    /* Pre-build an array of gates so the scalar loop doesn't pay sq2_init cost. */
    sq2_gate_t *gates = (sq2_gate_t*)malloc(sizeof(sq2_gate_t) * 256);
    for (int k = 0; k < 256; k++) {
        sq2_init(&gates[k], scale + 1e-4f * (float)k);
    }

    struct timespec t0, t1;
    volatile double sink_scalar = 0.0, sink_handsse = 0.0;

    /* SCALAR */
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < iters; i++) {
        sink_scalar += bench_scalar(&gates[i & 0xFF]);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double t_scalar = (t1.tv_sec - t0.tv_sec) + 1e-9 * (t1.tv_nsec - t0.tv_nsec);

#if defined(__SSE__)
    /* HAND-SSE: takes float, not gate */
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < iters; i++) {
        sink_handsse += bench_handsse(gates[i & 0xFF].scale);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double t_handsse = (t1.tv_sec - t0.tv_sec) + 1e-9 * (t1.tv_nsec - t0.tv_nsec);
#else
    double t_handsse = 0.0;
#endif

    free(gates);

    printf("scalar:   r=%g  %.3f ns/call  (sink=%g)\n",
           (double)r_scalar, 1e9 * t_scalar / iters, (double)sink_scalar);
    printf("hand-sse: r=%g  %.3f ns/call  (sink=%g)\n",
           (double)r_handsse, 1e9 * t_handsse / iters, (double)sink_handsse);
    printf("speedup: hand-sse is %.2fx %s than scalar\n",
           t_scalar / t_handsse,
           t_handsse < t_scalar ? "faster" : "slower");
    return 0;
}
