/* reflex.c -- C mirror of reflex.asm (verification only).
 * 9 doublets x 2 tubules x 512 B; sense/reflex/full tiers; same draws.
 * TSV must match the asm exactly.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define NDBL 9
#define DBIN 512
#define FRM 4608
#define NTR 200

static uint8_t tubA[FRM], tubB[FRM], snapA[FRM], snapB[FRM], bkA[FRM],
    bkB[FRM];
static uint32_t refD[72], refG[8];
static uint32_t tomb[NDBL];
static uint64_t xsst;
static int sd1, sp1, sd2, sp2;
static uint32_t se3b;
static int pacc[12];

static uint64_t xs64(void) {
    uint64_t x = xsst;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    xsst = x;
    return x;
}
static void triple4(const uint8_t *p, int n, uint32_t *a, uint32_t *b,
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
static void build_refs(void) {
    for (int d = 0; d < NDBL; d++)
        for (int t = 0; t < 2; t++) {
            uint32_t a, b, c, e;
            triple4((t ? tubB : tubA) + d * DBIN, DBIN, &a, &b, &c,
                    &e);
            refD[(d * 2 + t) * 4 + 0] = a;
            refD[(d * 2 + t) * 4 + 1] = b;
            refD[(d * 2 + t) * 4 + 2] = c;
            refD[(d * 2 + t) * 4 + 3] = e;
        }
    triple4(tubA, FRM, &refG[0], &refG[1], &refG[2], &refG[3]);
    triple4(tubB, FRM, &refG[4], &refG[5], &refG[6], &refG[7]);
}
static int resdbl(int d, uint32_t r[8]) {
    uint32_t a, b, c, e;
    triple4(tubA + d * DBIN, DBIN, &a, &b, &c, &e);
    r[0] = a - refD[(d * 2 + 0) * 4 + 0];
    r[1] = b - refD[(d * 2 + 0) * 4 + 1];
    r[2] = c - refD[(d * 2 + 0) * 4 + 2];
    r[3] = e - refD[(d * 2 + 0) * 4 + 3];
    triple4(tubB + d * DBIN, DBIN, &a, &b, &c, &e);
    r[4] = a - refD[(d * 2 + 1) * 4 + 0];
    r[5] = b - refD[(d * 2 + 1) * 4 + 1];
    r[6] = c - refD[(d * 2 + 1) * 4 + 2];
    r[7] = e - refD[(d * 2 + 1) * 4 + 3];
    return (r[0] | r[1] | r[2] | r[3] | r[4] | r[5] | r[6] | r[7]) !=
           0;
}
static int sec_bare(uint8_t *p, int n, uint32_t e0, uint32_t e1) {
    int32_t d = (int32_t)e0;
    if (!((d >= 1 && d <= 255) || (d >= -255 && d <= -1)))
        return 0;
    int32_t e1s = (int32_t)e1;
    if (e1s % d != 0)
        return 0;
    int32_t q = e1s / d;
    if (q < 1 || q > n)
        return 0;
    p[q - 1] = (uint8_t)(p[q - 1] - (uint8_t)d);
    return 1;
}
static int sec_gated(uint8_t *p, int n, uint32_t e0, uint32_t e1,
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
static void tombstone(int d) {
    memset(tubA + d * DBIN, 0xAA, DBIN);
    memset(tubB + d * DBIN, 0xAA, DBIN);
    tomb[d] = 1;
}
static int tomb_any(void) {
    for (int i = 0; i < NDBL; i++)
        if (tomb[i])
            return 1;
    return 0;
}
static int memeqT(void) {
    return !memcmp(tubA, bkA, FRM) && !memcmp(tubB, bkB, FRM);
}
/* 0 clean / 1 detected */
static int run_sense(void) {
    uint32_t r[8];
    for (int d = 0; d < NDBL; d++) {
        resdbl(d, r);
        if (r[0] | r[4])
            return 1;
    }
    return 0;
}
/* 0 clean-claim / 1 nonclean. May tombstone. */
static int run_reflex(void) {
    uint32_t r[8];
    memset(tomb, 0, sizeof tomb);
    for (int d = 0; d < NDBL; d++) {
        resdbl(d, r);
        if (!((r[0] | r[1]) | (r[4] | r[5])))
            continue;
        for (int t = 0; t < 2; t++) {
            uint32_t e0 = r[t * 4], e1 = r[t * 4 + 1];
            if (!(e0 | e1))
                continue;
            uint8_t *pp = (t ? tubB : tubA) + d * DBIN;
            sec_bare(pp, DBIN, e0, e1);
            resdbl(d, r);
            e0 = r[t * 4];
            e1 = r[t * 4 + 1];
            if (e0 | e1) {
                tombstone(d);
                break;
            }
        }
    }
    return tomb_any();
}
/* 0 ok / 1 refused. */
static int run_full(void) {
    uint32_t r[8];
    int refused = 0;
    for (int d = 0; d < NDBL; d++) {
        if (!resdbl(d, r))
            continue;
        for (int t = 0; t < 2; t++) {
            if (!(r[t * 4] | r[t * 4 + 1] | r[t * 4 + 2] |
                  r[t * 4 + 3]))
                continue;
            sec_gated((t ? tubB : tubA) + d * DBIN, DBIN,
                      r[t * 4], r[t * 4 + 1], r[t * 4 + 2],
                      r[t * 4 + 3]);
        }
        if (!resdbl(d, r))
            continue;
        int d0 = (r[0] | r[1] | r[2] | r[3]) != 0;
        int d1 = (r[4] | r[5] | r[6] | r[7]) != 0;
        if (d0 && d1) {
            refused = 1;
            continue;
        }
        if (!d0 && !d1)
            continue;
        int t = d0 ? 0 : 1;
        int64_t e1 = (int32_t)r[t * 4], e2 = (int32_t)r[t * 4 + 1],
                e3 = (int32_t)r[t * 4 + 2];
        se3b = r[t * 4 + 3];
        if (search2(DBIN, e1, e2, e3) != 1) {
            refused = 1;
            continue;
        }
        uint8_t *pp = (t ? tubB : tubA) + d * DBIN;
        pp[sp1 - 1] = (uint8_t)(pp[sp1 - 1] - (uint8_t)sd1);
        pp[sp2 - 1] = (uint8_t)(pp[sp2 - 1] - (uint8_t)sd2);
        if (resdbl(d, r)) {
            refused = 1;
            continue;
        }
    }
    if (refused)
        return 1;
    uint32_t a, b, c, e;
    triple4(tubA, FRM, &a, &b, &c, &e);
    if (a != refG[0] || b != refG[1] || c != refG[2] || e != refG[3])
        return 1;
    triple4(tubB, FRM, &a, &b, &c, &e);
    if (a != refG[4] || b != refG[5] || c != refG[6] || e != refG[7])
        return 1;
    return 0;
}
static void inject(int k, int clustered) {
    if (!clustered) {
        for (int i = 0; i < k; i++) {
            int pos = (int)(xs64() % 9216), d;
            int dd = pos / 1024, t = (pos % 1024) / 512,
                o = pos % 512;
            do {
                d = (int)(((xs64() & 255) + 1) & 255);
            } while (!d);
            (t ? tubB : tubA)[dd * 512 + o] ^= (uint8_t)d;
        }
    } else {
        int db1 = (int)(xs64() % 9);
        int db2 = (db1 + 1 + (int)(xs64() & 7)) % 9;
        int split = k / 2;
        for (int i = 0; i < k; i++) {
            int db = (k <= 4) ? db1 : (i < split ? db1 : db2);
            uint64_t r = xs64();
            int t = (int)(r & 1), o = (int)((r >> 1) & 511), d;
            do {
                d = (int)(((xs64() & 255) + 1) & 255);
            } while (!d);
            (t ? tubB : tubA)[db * 512 + o] ^= (uint8_t)d;
        }
    }
}
static int ck, cpat;
static int pacc[12];
static void trial_cell(int k, int pat) {
    ck = k;
    cpat = pat;
    memset(pacc, 0, sizeof pacc);
    for (int t = 0; t < NTR; t++) {
        memcpy(tubA, bkA, FRM);
        memcpy(tubB, bkB, FRM);
        inject(k, pat);
        memcpy(snapA, tubA, FRM);
        memcpy(snapB, tubB, FRM);
        for (int p = 0; p < 3; p++) {
            memcpy(tubA, snapA, FRM);
            memcpy(tubB, snapB, FRM);
            memset(tomb, 0, sizeof tomb);
            int claim = (p == 0) ? run_sense()
                        : (p == 1) ? run_reflex()
                                   : run_full();
            if (tomb_any())
                pacc[p * 4 + 1]++;
            else if (!claim) {
                if (memeqT())
                    pacc[p * 4 + 0]++;
                else
                    pacc[p * 4 + 3]++;
            } else
                pacc[p * 4 + 2]++;
        }
    }
    for (int p = 0; p < 3; p++)
        printf("R %d k=%d %s %d %d %d %d\n", p, k,
               pat ? "clust" : "spread", pacc[p * 4 + 0],
               pacc[p * 4 + 1], pacc[p * 4 + 2], pacc[p * 4 + 3]);
}
int main(void) {
    for (int i = 0; i < FRM; i++) {
        tubA[i] = (uint8_t)(((i * 91 + 17) ^ 0xA5) & 0xFF);
        tubB[i] = tubA[i] ^ 0x55;
    }
    tubA[0] = 0x45;
    tubA[1] = 0x53;
    tubA[2] = 0x46;
    tubA[3] = 0x32;
    tubB[0] = 0x45 ^ 0x55;
    tubB[1] = 0x53 ^ 0x55;
    tubB[2] = 0x46 ^ 0x55;
    tubB[3] = 0x32 ^ 0x55;
    memcpy(bkA, tubA, FRM);
    memcpy(bkB, tubB, FRM);
    build_refs();
    xsst = 0x123456789ULL;
    int ks[] = {1, 2, 3, 4, 6, 8};
    for (int i = 0; i < 6; i++) {
        trial_cell(ks[i], 0);
        trial_cell(ks[i], 1);
    }
    return 0;
}
