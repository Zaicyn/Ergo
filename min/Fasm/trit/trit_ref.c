/* trit_ref.c — C mirror of the FASM trit codec (trit_meta.md Phase 1).
 * Same spec: 5 trits/byte little-endian, 243..255 refused, xoshiro seed.
 * NOTE: trits draw from the LOW 32 bits ((uint32_t)f(s) % 3) to match the
 * asm driver's 32-bit div. Build: gcc -O2 -o trit_ref trit_ref.c */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define NTRITS 1000000
#define NGROUP (NTRITS / 5)

static uint64_t rng[4];
static inline uint64_t fx(void) {
    uint64_t x = rng[0] + rng[3], t = rng[1] << 17;
    rng[2] ^= rng[0]; rng[3] ^= rng[1]; rng[1] ^= rng[2]; rng[0] ^= rng[3];
    rng[2] ^= t; rng[3] = (rng[3] << 45) | (rng[3] >> 19);
    return (x << 17) | (x >> 47);
}
static void seed(uint64_t s) {
    rng[0] = s + 0x9E3779B97F4A7C15ULL; rng[1] = s ^ 0xBF58476D1CE4E5B9ULL;
    rng[2] = s + 0x94D049BB133111EBULL; rng[3] = s ^ 0xF0BA35E12960E9E7ULL;
    for (int i = 0; i < 10; i++) (void)fx();
}

/* returns packed byte, or -1 on bad trit */
static int pack5(const uint8_t t[5]) {
    for (int i = 0; i < 5; i++) if (t[i] > 2) return -1;
    return t[0] + 3 * t[1] + 9 * t[2] + 27 * t[3] + 81 * t[4];
}
/* returns 0 ok / -1 refused */
static int unpack5(unsigned v, uint8_t t[5]) {
    if (v > 242) return -1;
    for (int i = 0; i < 5; i++) { t[i] = (uint8_t)(v % 3); v /= 3; }
    return 0;
}

static uint8_t trits[NTRITS], packed[NGROUP], unpacked[NTRITS];

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + 1e-9 * (double)ts.tv_nsec;
}

int main(void) {
    long fails = 0, total = 0;
    uint8_t t[5];
    for (unsigned v = 0; v < 243; v++) {
        if (unpack5(v, t) != 0 || pack5(t) != (int)v) fails++;
        total++;
    }
    for (unsigned v = 243; v < 256; v++) {
        if (unpack5(v, t) == 0) fails++;
        total++;
    }
    for (int p = 0; p < 5; p++) {
        memset(t, 0, 5); t[p] = 3;
        if (pack5(t) != -1) fails++;
        total++;
    }
    printf("trit selftest fails/total: %ld/%ld\n", fails, total);
    if (fails) return 1;

    seed(0x2026);
    for (int i = 0; i < NTRITS; i++)
        trits[i] = (uint8_t)((uint32_t)fx() % 3u);
    double t0 = now_sec();
    for (int g = 0; g < NGROUP; g++) {
        int v = pack5(trits + 5 * g);
        if (v < 0) { printf("pack failed at group %d\n", g); return 1; }
        packed[g] = (uint8_t)v;
    }
    double t1 = now_sec();
    for (int g = 0; g < NGROUP; g++) {
        if (unpack5(packed[g], unpacked + 5 * g) != 0) {
            printf("unpack refused at group %d\n", g); return 1;
        }
    }
    double t2 = now_sec();
    if (memcmp(trits, unpacked, NTRITS) != 0) {
        printf("round-trip mismatch\n"); return 1;
    }
    uint64_t h = 0xcbf29ce484222325ULL;
    for (int i = 0; i < NGROUP; i++) {
        h ^= packed[i];
        h *= 0x100000001b3ULL;
    }
    printf("digest: %016llx\n", (unsigned long long)h);
    printf("pack out MB/s: %.0f\n", (NGROUP / (t1 - t0)) / 1e6);
    printf("unpack in MB/s: %.0f\n", (NGROUP / (t2 - t1)) / 1e6);
    return 0;
}
