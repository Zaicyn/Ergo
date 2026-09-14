/* allocbench.c -- fixed-size alloc/free churn: glibc malloc vs tcmalloc.
 * SQ4's own numbers come from its FASM binary (SQ4T alloc_ns, invariants
 * included) and are compared, not re-implemented. Build twice:
 *   gcc -O2 ... -o ab_glibc allocbench.c
 *   gcc -O2 ... -o ab_tcm allocbench.c -ltcmalloc
 * Workload: N=100096 allocs (SQ4's count) of SIZE bytes, then free all
 * (batch), plus interleaved churn (alloc/free alternating). Timer is
 * CLOCK_MONOTONIC best-of-5. Touch variants write one word per block
 * (malloc itself never touches memory; SQ4 writes invariants per slot).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <malloc.h>

#define N 100096
#define ROUNDS 5

static double now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}
static void **ptrs;

static double batch(size_t sz, int touch) {
    double best = 1e30;
    for (int r = 0; r < ROUNDS; r++) {
        double t0 = now_ns();
        for (int i = 0; i < N; i++) {
            ptrs[i] = malloc(sz);
            if (touch)
                *(volatile unsigned long *)ptrs[i] = (unsigned long)i;
        }
        for (int i = 0; i < N; i++)
            free(ptrs[i]);
        double dt = now_ns() - t0;
        if (dt < best)
            best = dt;
    }
    return best / N; /* ns per alloc+free pair */
}
static double churn(size_t sz, int touch) {
    double best = 1e30;
    for (int r = 0; r < ROUNDS; r++) {
        double t0 = now_ns();
        for (int i = 0; i < N; i++) {
            ptrs[0] = malloc(sz);
            if (touch)
                *(volatile unsigned long *)ptrs[0] = (unsigned long)i;
            free(ptrs[0]);
        }
        double dt = now_ns() - t0;
        if (dt < best)
            best = dt;
    }
    return best / N;
}
static double alloconly(size_t sz, int touch) {
    double best = 1e30;
    for (int r = 0; r < ROUNDS; r++) {
        double t0 = now_ns();
        for (int i = 0; i < N; i++) {
            ptrs[i] = malloc(sz);
            if (touch)
                *(volatile unsigned long *)ptrs[i] = (unsigned long)i;
        }
        double dt = now_ns() - t0;
        if (dt < best)
            best = dt;
        for (int i = 0; i < N; i++)
            free(ptrs[i]);
    }
    return best / N; /* ns per alloc, no free in timer */
}
static void overhead(size_t sz) {
    void *p = malloc(sz);
    size_t u = malloc_usable_size(p);
    printf("size=%5d usable=%5d overhead=%d\n", (int)sz, (int)u,
           (int)(u - sz));
    free(p);
}
int main(void) {
    ptrs = malloc(sizeof(void *) * N);
    const size_t sizes[] = { 16, 64, 256, 1024, 4096 };
    printf("pattern size: ns/op alloconly, batch, churn (+touch variants)\n");
    for (int i = 0; i < 5; i++) {
        size_t sz = sizes[i];
        printf("%-6s %4d: %8.2f %8.2f %8.2f %8.2f %8.2f %8.2f\n",
               "fixed", (int)sz, alloconly(sz, 0), alloconly(sz, 1),
               batch(sz, 0), batch(sz, 1), churn(sz, 0),
               churn(sz, 1));
    }
    printf("overhead (usable - requested):\n");
    for (int i = 0; i < 5; i++)
        overhead(sizes[i]);
    free(ptrs);
    return 0;
}
