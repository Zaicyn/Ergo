/* alignchk.c -- C mirror of alignchk.asm (verification only).
 * Two 4096 B units + W overlap; corrupt/shift/shco trials; ESF-only
 * control vs overlap pipeline. TSV must match the asm exactly.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define NTR 200
#define SMAX 512

static uint8_t unitA[4096], unitB[4096], snapA[4096], snapB[4096],
    bkA[4096], bkB[4096];
static uint32_t refA[4], refB[4];
static uint64_t xsst;
static int cW;
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
/* residuals of unit vs ref into e[4] */
static void unit_resid(const uint8_t *u, const uint32_t *ref,
                       uint32_t *e) {
    uint32_t a, b, c, d;
    triple4(u, 4096, &a, &b, &c, &d);
    e[0] = a - ref[0];
    e[1] = b - ref[1];
    e[2] = c - ref[2];
    e[3] = d - ref[3];
}
static int sec4(uint8_t *p, int n, uint32_t e0, uint32_t e1,
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
static int agreeW(int W, int t) {
    int n = 0;
    for (int i = 0; i < W - t; i++)
        n += (unitA[4096 - W + t + i] == unitB[i]);
    return n;
}
static void build_frame(int W) {
    for (int i = 0; i < 4096; i++) {
        unitA[i] = (uint8_t)((((i * 91 + 17) ^ 0xA5) ^ (i >> 8)) & 0xFF);
        unitB[i] = (uint8_t)(((i * 67 + 41) ^ 0x3C ^ (i >> 8)) & 0xFF);
    }
    unitA[0] = 0x45;
    unitA[1] = 0x53;
    unitA[2] = 0x46;
    unitA[3] = 0x32;
    unitB[0] = 0x45;
    unitB[1] = 0x53;
    unitB[2] = 0x46;
    unitB[3] = 0x32;
    memcpy(unitB, unitA + 4096 - W, (size_t)W);
    memcpy(bkA, unitA, 4096);
    memcpy(bkB, unitB, 4096);
    triple4(unitA, 4096, &refA[0], &refA[1], &refA[2], &refA[3]);
    triple4(unitB, 4096, &refB[0], &refB[1], &refB[2], &refB[3]);
}
static void inject_corr(int k) {
    for (int i = 0; i < k; i++) {
        uint64_t r = xs64();
        int side = (int)(r & 1);
        int pos = (int)((r >> 1) & (uint64_t)(cW - 1)), d;
        do {
            d = (int)(((xs64() & 255) + 1) & 255);
        } while (!d);
        if (!side)
            unitA[4096 - cW + pos] ^= (uint8_t)d;
        else
            unitB[pos] ^= (uint8_t)d;
    }
}
static void apply_shift(int s) {
    memmove(unitB, unitB + s, (size_t)(4096 - s));
    memset(unitB + 4096 - s, 0, (size_t)s);
}
static int memeqAB(void) {
    return !memcmp(unitA, bkA, 4096) && !memcmp(unitB, bkB, 4096);
}
/* ESF-only corrupt verdict: 0 ok-claim / 1 dirty */
static int v_esf_corr(void) {
    uint32_t e[4];
    unit_resid(unitA, refA, e);
    if (e[0] | e[1] | e[2] | e[3]) {
        sec4(unitA, 4096, e[0], e[1], e[2], e[3]);
        unit_resid(unitA, refA, e);
        if (e[0] | e[1] | e[2] | e[3])
            return 1;
    }
    unit_resid(unitB, refB, e);
    if (e[0] | e[1] | e[2] | e[3]) {
        sec4(unitB, 4096, e[0], e[1], e[2], e[3]);
        unit_resid(unitB, refB, e);
        if (e[0] | e[1] | e[2] | e[3])
            return 1;
    }
    return 0;
}
/* overlap corrupt verdict: 0/1 (mirrors asm corr_core: always SEC
 * dirty units, then recheck agree + residuals) */
static int v_ovl_corr(void) {
    uint32_t e[4];
    unit_resid(unitA, refA, e);
    if (e[0] | e[1] | e[2] | e[3])
        sec4(unitA, 4096, e[0], e[1], e[2], e[3]);
    unit_resid(unitB, refB, e);
    if (e[0] | e[1] | e[2] | e[3])
        sec4(unitB, 4096, e[0], e[1], e[2], e[3]);
    if (agreeW(cW, 0) != cW)
        return 1;
    unit_resid(unitA, refA, e);
    if (e[0] | e[1] | e[2] | e[3])
        return 1;
    unit_resid(unitB, refB, e);
    if (e[0] | e[1] | e[2] | e[3])
        return 1;
    return 0;
}
/* ESF-only shift verdict: 0/1 */
static int v_esf_shift(void) {
    uint32_t e[4];
    unit_resid(unitB, refB, e);
    if (!(e[0] | e[1] | e[2] | e[3]))
        return 0;
    sec4(unitB, 4096, e[0], e[1], e[2], e[3]);
    unit_resid(unitB, refB, e);
    return (e[0] | e[1] | e[2] | e[3]) ? 1 : 0;
}
/* find shift: t* or -1 */
static int find_shift(void) {
    int best = -1, bestsc = -1, tied = 0;
    for (int t = 0; t <= SMAX; t++) {
        if (t >= cW || cW - t < 4)
            continue;
        int sc = agreeW(cW, t);
        if (sc > bestsc) {
            best = t;
            bestsc = sc;
            tied = 0;
        } else if (sc == bestsc)
            tied = 1;
    }
    if (tied || best < 0 || bestsc != cW - best)
        return -1;
    return best;
}
/* overlap shift verdict: t* or -1 */
static int v_ovl_shift(void) {
    int t = find_shift();
    if (t < 0)
        return -1;
    memcpy(unitB, unitA + 4096 - cW, (size_t)t);
    memcpy(unitB + t, snapB, (size_t)(4096 - t));
    uint32_t e[4];
    unit_resid(unitB, refB, e);
    if (e[0] | e[1] | e[2] | e[3])
        return -1;
    return t;
}
/* shco verdict: 0 fullok-claim / 1 part / 2 fail */
static int v_shco(void) {
    int t = find_shift();
    if (t < 0)
        return 2;
    memcpy(unitB, unitA + 4096 - cW, (size_t)t);
    memcpy(unitB + t, snapB, (size_t)(4096 - t));
    if (v_ovl_corr())
        return 1;
    return 0;
}
static void corr_cell(int W, int k) {
    cW = W;
    memset(pacc, 0, sizeof pacc);
    for (int t = 0; t < NTR; t++) {
        memcpy(unitA, bkA, 4096);
        memcpy(unitB, bkB, 4096);
        inject_corr(k);
        memcpy(snapA, unitA, 4096);
        memcpy(snapB, unitB, 4096);
        for (int p = 0; p < 2; p++) {
            memcpy(unitA, snapA, 4096);
            memcpy(unitB, snapB, 4096);
            int claim = p ? v_ovl_corr() : v_esf_corr();
            if (!claim) {
                if (memeqAB())
                    pacc[p * 4 + 0]++;
                else
                    pacc[p * 4 + 2]++;
            } else
                pacc[p * 4 + 1]++;
        }
    }
    for (int p = 0; p < 2; p++)
        printf("C %d W=%d k=%d %d %d %d\n", p, W, k, pacc[p * 4],
               pacc[p * 4 + 1], pacc[p * 4 + 2]);
}
/* NTR per cell */
static void shift_cell(int W, int s) {
    cW = W;
    memset(pacc, 0, sizeof pacc);
    for (int t = 0; t < NTR; t++) {
        memcpy(unitA, bkA, 4096);
        memcpy(unitB, bkB, 4096);
        apply_shift(s);
        memcpy(snapA, unitA, 4096);
        memcpy(snapB, unitB, 4096);
        for (int p = 0; p < 2; p++) {
            memcpy(unitA, snapA, 4096);
            memcpy(unitB, snapB, 4096);
            if (!p) {
                int claim = v_esf_shift();
                if (!claim) {
                    if (memeqAB())
                        pacc[1]++;
                    else
                        pacc[2]++;
                } else
                    pacc[1]++;
            } else {
                int ft = v_ovl_shift();
                if (ft < 0)
                    pacc[4 + 1]++;
                else if (memeqAB())
                    pacc[4 + (ft == s ? 0 : 2)]++;
                else
                    pacc[4 + 2]++;
            }
        }
    }
    for (int p = 0; p < 2; p++)
        printf("S %d W=%d s=%d %d %d %d\n", p, W, s, pacc[p * 4],
               pacc[p * 4 + 1], pacc[p * 4 + 2]);
}
static void shco_cell(int W, int s) {
    cW = W;
    memset(pacc, 0, sizeof pacc);
    for (int t = 0; t < NTR; t++) {
        memcpy(unitA, bkA, 4096);
        memcpy(unitB, bkB, 4096);
        apply_shift(s);
        inject_corr(1);
        memcpy(snapA, unitA, 4096);
        memcpy(snapB, unitB, 4096);
        for (int p = 0; p < 2; p++) {
            memcpy(unitA, snapA, 4096);
            memcpy(unitB, snapB, 4096);
            if (!p) {
                /* ESF-only cannot unshift: always fail (runs SEC for parity). */
                (void)v_esf_shift();
                (void)memeqAB();
                pacc[2]++;
            } else {
                int v = v_shco();
                if (!v && memeqAB())
                    pacc[4]++;
                else if (v == 1)
                    pacc[5]++;
                else
                    pacc[6]++;
            }
        }
    }
    for (int p = 0; p < 2; p++)
        printf("M %d W=%d s=%d %d %d %d\n", p, W, s, pacc[p * 4],
               pacc[p * 4 + 1], pacc[p * 4 + 2]);
}
int main(void) {
    xsst = 0x123456789ULL;
    int Ws[] = {64, 256, 512};
    for (int wi = 0; wi < 3; wi++) {
        int W = Ws[wi];
        build_frame(W);
        corr_cell(W, 1);
        corr_cell(W, 2);
        int ss[] = {1, 2, 4, 8, 16, 32, 64, 128, 200, 256, 400, 500};
        int nss[] = {8, 9, 12};
        int ns = nss[wi];
        for (int i = 0; i < ns; i++)
            shift_cell(W, ss[i]);
        shco_cell(W, 4);
        shco_cell(W, 16);
    }
    return 0;
}
