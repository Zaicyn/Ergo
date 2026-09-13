/* torusecc_d.c -- C mirror of torusecc_d.asm (derived shell).
 * Same fill/refs/inject/ladder/verdicts/TSV. Counts must match.
 * Prints misc trial numbers (t<cell>:<trial>) for autopsy.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define NBIN 8
#define SBIN 512
#define NTR 500

static uint8_t f0[4096], bk[4096];
static uint32_t refB[24], refC[8], refG[3], refG3;
static uint32_t se3b;
static uint64_t xsst;
static int sd1, sp1, sd2, sp2;

static uint64_t xs64(void) {
    uint64_t x = xsst;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    xsst = x;
    return x;
}
static void triple(const uint8_t *p, int n, uint32_t *a, uint32_t *b,
                   uint32_t *c, uint32_t *d) {
    uint32_t s0 = 0, s1 = 0, s2 = 0, s3 = 0;
    for (int i = 0; i < n; i++) {
        uint32_t v = p[i], idx = (uint32_t)i + 1;
        s0 += v;
        s1 += v * idx;
        s2 += v * idx * idx;
        s3 += v * idx * idx * idx;
    }
    *a = s0;
    *b = s1;
    *c = s2;
    *d = s3;
}
static int sec_fix(uint8_t *p, int n, uint32_t e0, uint32_t e1,
                   uint32_t e2, uint32_t e3) {
    int32_t d = (int32_t)e0;
    if (!((d >= 1 && d <= 255) || (d >= -255 && d <= -1)))
        return 0;
    int32_t e1s = (int32_t)e1;
    if (e1s % d != 0)
        return 0;
    int32_t q = e1s / d;
    if (q < 1 || q > n)
        return 0;
    if ((int64_t)d * q * q != (int32_t)e2)
        return 0;
    if ((uint32_t)((int64_t)d * q * q * q) != e3)
        return 0;
    p[q - 1] = (uint8_t)(p[q - 1] - (uint8_t)d);
    return 1;
}
static int search2(int n, int64_t e1, int64_t e2, int64_t e3) {
    int nsol = 0;
    for (int p1 = 1; p1 <= n && nsol < 2; p1++) {
        for (int p2 = p1 + 1; p2 <= n && nsol < 2; p2++) {
            int64_t den = (int64_t)p1 - p2;
            int64_t num = e2 - e1 * p2;
            if (num % den != 0)
                continue;
            int64_t d1 = num / den;
            if (!((d1 >= 1 && d1 <= 255) || (d1 >= -255 && d1 <= -1)))
                continue;
            int64_t d2 = e1 - d1;
            if (!((d2 >= 1 && d2 <= 255) || (d2 >= -255 && d2 <= -1)))
                continue;
            if (d1 * p1 * p1 + d2 * p2 * p2 != e3)
                continue;
            if ((uint32_t)(d1 * p1 * p1 * p1 + d2 * p2 * p2 * p2) !=
                se3b)
                continue;
            nsol++;
            if (nsol == 1) {
                sd1 = (int)d1;
                sp1 = p1;
                sd2 = (int)d2;
                sp2 = p2;
            }
        }
    }
    return nsol;
}
static void build_refs(void) {
    for (int s = 0; s < NBIN; s++) {
        uint32_t a, b, c, d;
        triple(f0 + s * SBIN, SBIN, &a, &b, &c, &d);
        refB[s * 3 + 0] = a;
        refB[s * 3 + 1] = b;
        refB[s * 3 + 2] = c;
        refC[s] = d;
    }
    triple(f0, 4096, &refG[0], &refG[1], &refG[2], &refG3);
}
static void inject(int k, int clustered) {
    if (!clustered) {
        for (int i = 0; i < k; i++) {
            int pos = (int)(xs64() & 4095), d;
            do {
                d = (int)(((xs64() & 255) + 1) & 255);
            } while (!d);
            f0[pos] ^= (uint8_t)d;
        }
    } else {
        int sb1 = (int)(xs64() & 7);
        int sb2 = (sb1 + (int)(xs64() & 6) + 1) & 7;
        int split = k / 2;
        for (int i = 0; i < k; i++) {
            int sb = (k <= 4) ? sb1 : (i < split ? sb1 : sb2);
            uint64_t r = xs64();
            int off = sb * SBIN + (int)(r & 511), d;
            /* NOTE: asm drops the shell bit (single shell here) */
            do {
                d = (int)(((xs64() & 255) + 1) & 255);
            } while (!d);
            f0[off] ^= (uint8_t)d;
        }
    }
}
static int resone(int s, uint32_t r[4]) {
    uint32_t a, b, c, d;
    triple(f0 + s * SBIN, SBIN, &a, &b, &c, &d);
    r[0] = a - refB[s * 3 + 0];
    r[1] = b - refB[s * 3 + 1];
    r[2] = c - refB[s * 3 + 2];
    r[3] = d - refC[s];
    return (r[0] | r[1] | r[2] | r[3]) != 0;
}
static int repair_frame(void) {
    for (int s = 0; s < NBIN; s++) {
        uint32_t r[4];
        if (!resone(s, r))
            continue;
        sec_fix(f0 + s * SBIN, SBIN, r[0], r[1], r[2], r[3]);
        if (!resone(s, r))
            continue;
        int64_t e1 = (int32_t)r[0], e2 = (int32_t)r[1],
                e3 = (int32_t)r[2];
        se3b = r[3];
        if (search2(SBIN, e1, e2, e3) != 1)
            return 1;
        uint8_t *pp = f0 + s * SBIN;
        pp[sp1 - 1] = (uint8_t)(pp[sp1 - 1] - (uint8_t)sd1);
        pp[sp2 - 1] = (uint8_t)(pp[sp2 - 1] - (uint8_t)sd2);
        if (resone(s, r))
            return 1;
    }
    uint32_t a, b, c, d;
    triple(f0, 4096, &a, &b, &c, &d);
    return (a != refG[0] || b != refG[1] || c != refG[2] ||
            d != refG3);
}
static int curcell;
static void trial_cell(int k, int pat) {
    int corr = 0, ref = 0, misc = 0;
    for (int t = 0; t < NTR; t++) {
        memcpy(f0, bk, 4096);
        inject(k, pat);
        if (repair_frame())
            ref++;
        else if (!memcmp(f0, bk, 4096))
            corr++;
        else {
            misc++;
            printf("MISC cell=%d trial=%d\n", curcell, t);
        }
    }
    printf("T k=%d %s %d %d %d\n", k, pat ? "clust" : "spread", corr,
           ref, misc);
    curcell++;
}
int main(void) {
    for (int i = 0; i < 4096; i++)
        f0[i] = (uint8_t)(((i * 91 + 17) ^ 0xA5) & 0xFF);
    f0[0] = 0x45;
    f0[1] = 0x53;
    f0[2] = 0x46;
    f0[3] = 0x32;
    memcpy(bk, f0, 4096);
    build_refs();
    xsst = 0x123456789ULL;
    int ks[] = {1, 2, 3, 4, 6, 8};
    for (int i = 0; i < 6; i++) {
        trial_cell(ks[i], 0);
        trial_cell(ks[i], 1);
    }
    return 0;
}
