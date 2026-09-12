/* int_ref.c -- C mirror of int_codec.inc (compression_plan.md Phase A).
 * Same LCG stream as zztest.asm; digest must match byte-for-byte.
 * Build: gcc -O2 -o int_ref int_ref.c */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define NBUF 65536

static uint32_t zz_enc(int32_t e) {
    return ((uint32_t)e << 1) ^ (uint32_t)(-(e < 0));
}
static int32_t zz_dec(uint32_t s) {
    return (int32_t)((s >> 1) ^ (uint32_t)(-(int32_t)(s & 1u)));
}
static void put_i64(uint8_t *o, int64_t v, int n) {
    for (int i = 0; i < n; i++) { o[i] = (uint8_t)v; v >>= 8; }
}
static int64_t get_i64(const uint8_t *p, int n) {
    uint64_t v = 0;
    for (int i = n - 1; i >= 0; i--) v = (v << 8) | p[i];
    int sh = 64 - 8 * n;
    return (int64_t)(v << sh) >> sh;
}
static int i64width(int64_t v) {
    uint64_t t = (uint64_t)(v ^ (v >> 63));
    if (!t) return 1;
    return (int)((64 - __builtin_clzll(t) + 8) / 8) > 8
        ? 8 : (int)((64 - __builtin_clzll(t) + 8) / 8);
}

static const struct { int64_t v; int w; } TAB[] = {
    {-128,1},{127,1},{0,1},{-1,1},
    {-129,2},{128,2},{-32768,2},{32767,2},
    {-32769,3},{32768,3},{-8388608,3},{8388607,3},
    {-8388609,4},{8388608,4},{-2147483648LL,4},{2147483647,4},
    {-2147483649LL,5},{2147483649LL,5},
    {-549755813888LL,5},{549755813887LL,5},
    {-549755813889LL,6},{549755813889LL,6},
    {-140737488355328LL,6},{140737488355327LL,6},
    {-140737488355329LL,7},{140737488355329LL,7},
    {-36028797018963968LL,7},{36028797018963967LL,7},
    {-36028797018963969LL,8},{36028797018963969LL,8},
    {(int64_t)0x8000000000000000ULL,8},{9223372036854775807LL,8},
};

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + 1e-9 * (double)ts.tv_nsec;
}

int main(void) {
    long fails = 0, total = 0;
    uint8_t b[8];
    for (int v = -128; v < 128; v++) {
        if (zz_dec(zz_enc(v)) != v) fails++;
        total++;
        if (i64width(v) != 1) fails++;
        total++;
    }
    for (unsigned i = 0; i < sizeof(TAB) / sizeof(TAB[0]); i++) {
        if (i64width(TAB[i].v) != TAB[i].w) fails++;
        total++;
        put_i64(b, TAB[i].v, TAB[i].w);
        if (get_i64(b, TAB[i].w) != TAB[i].v) fails++;
        total++;
    }
    printf("zz selftest fails/total: %ld/%ld\n", fails, total);
    if (fails) return 1;

    uint64_t h = 0xcbf29ce484222325ULL;
    for (int i = 0; i < NBUF; i++) {
        int32_t sv = (int32_t)((uint32_t)i * 0x9E3779B1u);
        uint32_t z = zz_enc(sv);
        for (int k = 0; k < 4; k++) {
            h ^= (uint8_t)(z >> (8 * k));
            h *= 0x100000001b3ULL;
        }
        int w = i64width((int64_t)sv);
        h ^= (uint8_t)w;
        h *= 0x100000001b3ULL;
    }
    printf("codec digest: %016llx\n", (unsigned long long)h);

    static int32_t buf[NBUF];
    for (int i = 0; i < NBUF; i++) buf[i] = (int32_t)((uint32_t)i * 0x9E3779B1u);
    double t0 = now_sec();
    volatile uint32_t sink = 0;
    for (int i = 0; i < NBUF; i++) sink ^= zz_dec(zz_enc(buf[i]));
    double t1 = now_sec();
    static uint8_t ob[NBUF][8];
    for (int i = 0; i < NBUF; i++) {
        put_i64(ob[i], buf[i], 4);
        sink ^= (uint32_t)get_i64(ob[i], 4);
    }
    double t2 = now_sec();
    (void)sink;
    printf("zz cycles/Kop: n/a (%.1f ns/op wall)\n", 1e9 * (t1 - t0) / NBUF);
    printf("putget cycles/Kop: n/a (%.1f ns/op wall)\n", 1e9 * (t2 - t1) / NBUF);
    return 0;
}
