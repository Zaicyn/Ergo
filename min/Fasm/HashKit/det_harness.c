/* det_harness.c -- C mirror of det_harness.asm (counter-mode debug-kit tool).
 * Same seeds, counts, derivations, FNV-1a fold. Outputs must match exactly.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define SEED     0x0123456789ABCDEFULL
#define N_STREAM 100000
#define N_EVENTS 20000

static uint64_t hash_u64(uint64_t seed) {
    uint64_t x = seed + 0x9E3779B97F4A7C15ULL;
    uint64_t z = x;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}
static uint32_t hash_u32(uint64_t seed) { return (uint32_t)(hash_u64(seed) >> 33); }
static double hash_u01(uint64_t seed) {
    return (double)(hash_u64(seed) >> 11) * 1.1102230246251565e-16; /* 2^-53 */
}

static uint64_t fnv = 0xCBF29CE484222325ULL;
static void fold_u64(uint64_t v) {
    for (int i = 0; i < 8; i++) {
        fnv ^= (uint8_t)(v & 0xFF);
        fnv *= 0x100000001B3ULL;
        v >>= 8;
    }
}

int main(void) {
    fnv = 0xCBF29CE484222325ULL;
    for (uint64_t i = 0; i < N_STREAM; i++) {
        fold_u64(hash_u64(SEED + i));
        fold_u64(hash_u32(SEED + i));
        double d = hash_u01(SEED + i);
        uint64_t u;
        memcpy(&u, &d, 8);
        fold_u64(u);
    }
    printf("H stream %016llx\n", (unsigned long long)fnv);

    static uint32_t spotv[15];
    fnv = 0xCBF29CE484222325ULL;
    for (uint64_t k = 0; k < N_EVENTS; k++) {
        uint32_t b = hash_u32(SEED ^ (k * 4 + 0)) & 15;
        uint32_t g = hash_u32(SEED ^ (k * 4 + 1)) & 31;
        uint32_t item = hash_u32(SEED ^ (k * 4 + 2)) & 255;
        uint64_t t = item;
        t = (t << 16) | g;
        t = (t << 8) | b;
        fold_u64(t);
        int slot = -1;
        if (k == 0) slot = 0;
        else if (k == 1) slot = 1;
        else if (k == 2) slot = 2;
        else if (k == 9999) slot = 3;
        else if (k == 19999) slot = 4;
        if (slot >= 0) {
            spotv[slot * 3 + 0] = b;
            spotv[slot * 3 + 1] = g;
            spotv[slot * 3 + 2] = item;
        }
    }
    printf("H events %016llx\n", (unsigned long long)fnv);

    static const uint64_t spotk[5] = {0, 1, 2, 9999, 19999};
    int pass = 0;
    for (int s = 0; s < 5; s++) {
        uint64_t k = spotk[s];
        uint32_t b = hash_u32(SEED ^ (k * 4 + 0)) & 15;
        uint32_t g = hash_u32(SEED ^ (k * 4 + 1)) & 31;
        uint32_t item = hash_u32(SEED ^ (k * 4 + 2)) & 255;
        if (b == spotv[s * 3 + 0] && g == spotv[s * 3 + 1] &&
            item == spotv[s * 3 + 2])
            pass++;
    }
    printf("H spot %d/5\n", pass);
    return 0;
}
