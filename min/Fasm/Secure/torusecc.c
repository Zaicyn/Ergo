/* torusecc.c -- C mirror of torusecc.asm (verification only).
 * Same fill/complement/refs/inject/ladder/verdicts/TSV. Counts must match.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define NBIN 8
#define SBIN 512
#define NTR 500

static uint8_t s0[4096], s1[4096], bk[8192];
static uint32_t refB[48], refC[16], refG[3], refG3;
static uint32_t se3b;
static uint64_t xsst;
static int ck, cpat, ccorr, cref, cmisc;

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
/* returns 1 fixed (applied) / 0 refused. e* are mod-2^32 residuals. */
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
    int32_t e2s = (int32_t)e2;
    if ((int64_t)d * q * q != e2s)
        return 0;
    if ((uint32_t)((int64_t)d * q * q * q) != e3)
        return 0;
    p[q - 1] = (uint8_t)(p[q - 1] - (uint8_t)d);
    return 1;
}
static int sd1, sp1, sd2, sp2;
/* 2-in-one-shell bounded search; returns solution count capped at 2. */
static int search2(const uint8_t *p, int n, int64_t e1, int64_t e2,
                   int64_t e3) {
    (void)p;
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
    for (int s = 0; s < NBIN; s++)
        for (int sh = 0; sh < 2; sh++) {
            uint32_t a, b, c, d;
            triple((sh ? s1 : s0) + s * SBIN, SBIN, &a, &b, &c, &d);
            refB[(s * 2 + sh) * 3 + 0] = a;
            refB[(s * 2 + sh) * 3 + 1] = b;
            refB[(s * 2 + sh) * 3 + 2] = c;
            refC[(s * 2 + sh)] = d;
        }
    triple(s0, 4096, &refG[0], &refG[1], &refG[2], &refG3);
}
static void inject(int k, int clustered) {
    if (!clustered) {
        for (int i = 0; i < k; i++) {
            int pos = (int)(xs64() & 8191);
            int shell = pos >> 12, off = pos & 4095, d;
            do {
                d = (int)(((xs64() & 255) + 1) & 255);
            } while (!d);
            (shell ? s1 : s0)[off] ^= (uint8_t)d;
        }
    } else {
        int sb1 = (int)(xs64() & 7);
        int sb2 = (sb1 + (int)(xs64() & 6) + 1) & 7;
        int split = k / 2, i;
        for (i = 0; i < k; i++) {
            int sb = (k <= 4) ? sb1 : (i < split ? sb1 : sb2);
            uint64_t r = xs64();
            int shell = (int)(r & 1), off = sb * SBIN + (int)((r >> 1) & 511), d;
            do {
                d = (int)(((xs64() & 255) + 1) & 255);
            } while (!d);
            (shell ? s1 : s0)[off] ^= (uint8_t)d;
        }
    }
}
/* residuals of sub-bin s into r[6]; returns nonzero-OR. */
static int resbin(int s, uint32_t r[8]) {
    uint32_t a, b, c, d;
    triple(s0 + s * SBIN, SBIN, &a, &b, &c, &d);
    r[0] = a - refB[(s * 2 + 0) * 3 + 0];
    r[1] = b - refB[(s * 2 + 0) * 3 + 1];
    r[2] = c - refB[(s * 2 + 0) * 3 + 2];
    r[3] = d - refC[(s * 2 + 0)];
    triple(s1 + s * SBIN, SBIN, &a, &b, &c, &d);
    r[4] = a - refB[(s * 2 + 1) * 3 + 0];
    r[5] = b - refB[(s * 2 + 1) * 3 + 1];
    r[6] = c - refB[(s * 2 + 1) * 3 + 2];
    r[7] = d - refC[(s * 2 + 1)];
    return (r[0] | r[1] | r[2] | r[3] | r[4] | r[5] | r[6] | r[7]) != 0;
}
/* returns 0 ok-so-far / 1 refused. */
static int repair_frame(void) {
    int refused = 0;
    for (int s = 0; s < NBIN; s++) {
        uint32_t r[8];
        if (!resbin(s, r))
            continue;
        for (int sh = 0; sh < 2; sh++) {
            if (!(r[sh * 4] | r[sh * 4 + 1] | r[sh * 4 + 2] |
                  r[sh * 4 + 3]))
                continue;
            sec_fix((sh ? s1 : s0) + s * SBIN, SBIN, r[sh * 4],
                    r[sh * 4 + 1], r[sh * 4 + 2], r[sh * 4 + 3]);
        }
        if (!resbin(s, r))
            continue;
        int d0 = (r[0] | r[1] | r[2] | r[3]) != 0;
        int d1 = (r[4] | r[5] | r[6] | r[7]) != 0;
        if (d0 && d1) {
            refused = 1;
            continue;
        }
        if (!d0 && !d1)
            continue;
        int sh = d0 ? 0 : 1;
        int64_t e1 = (int32_t)r[sh * 4], e2 = (int32_t)r[sh * 4 + 1],
                e3 = (int32_t)r[sh * 4 + 2];
        se3b = r[sh * 4 + 3];
        if (search2(NULL, SBIN, e1, e2, e3) != 1) {
            refused = 1;
            continue;
        }
        uint8_t *pp = (sh ? s1 : s0) + s * SBIN;
        pp[sp1 - 1] = (uint8_t)(pp[sp1 - 1] - (uint8_t)sd1);
        pp[sp2 - 1] = (uint8_t)(pp[sp2 - 1] - (uint8_t)sd2);
        if (resbin(s, r)) {
            refused = 1;
            continue;
        }
    }
    if (refused)
        return 1;
    uint32_t a, b, c, d;
    triple(s0, 4096, &a, &b, &c, &d);
    return (a != refG[0] || b != refG[1] || c != refG[2] ||
            d != refG3);
}
static void trial_cell(int k, int pat) {
    int corr = 0, ref = 0, misc = 0;
    for (int t = 0; t < NTR; t++) {
        memcpy(s0, bk, 4096);
        memcpy(s1, bk + 4096, 4096);
        inject(k, pat);
        if (repair_frame())
            ref++;
        else if (!memcmp(s0, bk, 4096) && !memcmp(s1, bk + 4096, 4096))
            corr++;
        else
            misc++;
    }
    printf("T k=%d %s %d %d %d\n", k, pat ? "clust" : "spread", corr,
           ref, misc);
}
int main(void) {
    for (int i = 0; i < 4096; i++) {
        s0[i] = (uint8_t)(((i * 91 + 17) ^ 0xA5) & 0xFF);
        s1[i] = s0[i] ^ 0x55;
    }
    s0[0] = 0x45;
    s0[1] = 0x53;
    s0[2] = 0x46;
    s0[3] = 0x32;
    s1[0] = 0x45 ^ 0x55;
    s1[1] = 0x53 ^ 0x55;
    s1[2] = 0x46 ^ 0x55;
    s1[3] = 0x32 ^ 0x55;
    memcpy(bk, s0, 4096);
    memcpy(bk + 4096, s1, 4096);
    build_refs();
    xsst = 0x123456789ULL;
    int ks[] = {1, 2, 3, 4, 6, 8};
    for (int i = 0; i < 6; i++) {
        trial_cell(ks[i], 0);
        trial_cell(ks[i], 1);
    }
    return 0;
}
