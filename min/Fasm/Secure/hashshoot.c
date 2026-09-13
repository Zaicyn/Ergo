/* hashshoot.c -- C mirror of hashshoot.asm (verification only).
 * Same frame fill, same three hashes, same avalanche + detection.
 * Outputs must match the asm lines field-for-field (except ns).
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define NFRAME 4096
#define NBLOCK 512
#define NDET 2000

static uint8_t frame[NFRAME], backup[NFRAME];

static uint64_t fnv1a64(const uint8_t *p) {
    uint64_t h = 0xCBF29CE484222325ULL;
    for (int i = 0; i < NFRAME; i++) {
        h ^= p[i];
        h *= 0x100000001B3ULL;
    }
    return h;
}
static uint64_t mix64(uint64_t x) {
    uint64_t z = x;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}
static uint64_t spmix(const uint8_t *p) {
    uint64_t h = 0;
    for (int i = 0; i < NBLOCK; i++) {
        uint64_t b;
        memcpy(&b, p + i * 8, 8);
        h = mix64(h ^ b);
    }
    return h;
}
static uint64_t adhoc(const uint8_t *p) {
    uint64_t h = 166136261U;
    for (int i = 0; i < NBLOCK; i++) {
        uint64_t b;
        memcpy(&b, p + i * 8, 8);
        h = ((h << 13) ^ (h >> 7) ^ b);
    }
    return h;
}
static uint64_t xsst;
static uint64_t xs64(void) {
    uint64_t x = xsst;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    xsst = x;
    return x;
}
typedef uint64_t (*hfn)(const uint8_t *);

static void avalanche(hfn fn, uint64_t h0, long *mean1000, int *mn, int *mx) {
    static long hist[65];
    memset(hist, 0, sizeof hist);
    long sum = 0;
    int lo = 64, hi = 0;
    for (int j = 0; j < 32768; j++) {
        frame[j >> 3] ^= (uint8_t)(1u << (j & 7));
        int d = __builtin_popcountll(fn(frame) ^ h0);
        frame[j >> 3] ^= (uint8_t)(1u << (j & 7));
        hist[d]++;
        sum += d;
        if (d < lo) lo = d;
        if (d > hi) hi = d;
    }
    *mean1000 = sum * 1000L / 32768;
    *mn = lo;
    *mx = hi;
}
static int detect(hfn fn, uint64_t h0) {
    memcpy(backup, frame, NFRAME);
    xsst = 0x123456789ULL;
    int miss = 0;
    for (int t = 0; t < NDET; t++) {
        int k = 2 + (int)(xs64() & 6);
        for (int i = 0; i < k; i++) {
            int pos = (int)(xs64() & 4095);
            int delta = (int)((xs64() & 255) + 1) & 255;
            frame[pos] ^= (uint8_t)delta;
        }
        if (fn(frame) == h0) miss++;
        memcpy(frame, backup, NFRAME);
    }
    return miss;
}
int main(void) {
    for (int i = 0; i < NFRAME; i++)
        frame[i] = (uint8_t)(((i * 91 + 17) ^ 0xA5) & 0xFF);
    frame[0] = 0x45;
    frame[1] = 0x53;
    frame[2] = 0x46;
    frame[3] = 0x32;
    struct {
        const char *nm;
        hfn fn;
    } hs[] = {{"H fnv  ", fnv1a64}, {"H spm  ", spmix}, {"H adh  ", adhoc}};
    for (int h = 0; h < 3; h++) {
        uint64_t h0 = hs[h].fn(frame);
        long m;
        int lo, hi;
        avalanche(hs[h].fn, h0, &m, &lo, &hi);
        int miss = detect(hs[h].fn, h0);
        printf("%s%016llx 0 %ld %d %d %d\n", hs[h].nm,
               (unsigned long long)h0, m, lo, hi, miss);
    }
    return 0;
}
