/* pktcodec.c -- C mirror of pktcodec.asm (verification only).
 * Core packet-codec functions + TSV. Must match the asm byte-for-byte.
 * Cells mirror packetbench.c semantics exactly (same draws, same order).
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define NP 8
#define PL 512
#define FR (NP * PL)
#define NTR 200
#define BONDK 18050561372206496278ull

static uint8_t bku[NP][PL], fru[NP][PL], parP[PL], parQ[PL];
static uint32_t refs[NP][4];
static uint8_t gexp[512], glog[256];
static uint64_t trng = 0x123456789ABCDEF1ull;
static int fails = 0;

static uint64_t trand(void) {
    trng ^= trng << 13;
    trng ^= trng >> 7;
    trng ^= trng << 17;
    return trng;
}
static uint64_t sm64(uint64_t *s) {
    uint64_t z = (*s += 0x9E3779B97F4A7C15ull);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z ^ (z >> 31);
}
static uint8_t gfm(uint8_t a, uint8_t b) {
    uint8_t r = 0;
    while (b) {
        if (b & 1)
            r ^= a;
        uint8_t hi = a & 0x80;
        a <<= 1;
        if (hi)
            a ^= 0x1B;
        b >>= 1;
    }
    return r;
}
static void gf_init(void) {
    uint8_t v = 1;
    for (int i = 0; i < 511; i++) {
        gexp[i] = v;
        if (i < 255)
            glog[v] = (uint8_t)i;
        v = gfm(v, 3);
    }
    gexp[511] = 1;
}
static uint8_t gf_div(uint8_t a, uint8_t b) {
    if (!a)
        return 0;
    int l = (int)glog[a] - (int)glog[b];
    if (l < 0)
        l += 255;
    return gexp[l];
}
static void triple4(const uint8_t *p, uint32_t *s) {
    uint32_t a = 0, b = 0, c = 0, d = 0;
    for (int i = 0; i < PL; i++) {
        uint32_t v = p[i], k = (uint32_t)i + 1;
        a += v;
        b += v * k;
        c += v * k * k;
        d += v * k * k * k;
    }
    s[0] = a;
    s[1] = b;
    s[2] = c;
    s[3] = d;
}
static int sec_pkt(uint8_t *p, const uint32_t *ref) {
    uint32_t s[4];
    triple4(p, s);
    uint32_t e0 = s[0] - ref[0], e1 = s[1] - ref[1];
    uint32_t e2 = s[2] - ref[2], e3 = s[3] - ref[3];
    if (!(e0 | e1 | e2 | e3))
        return 1;
    int32_t d = (int32_t)e0;
    if (!((d >= 1 && d <= 255) || (d >= -255 && d <= -1)))
        return 0;
    int32_t e1s = (int32_t)e1;
    if (e1s % d != 0)
        return 0;
    int32_t q = e1s / d;
    if (q < 1 || q > PL)
        return 0;
    if ((int64_t)d * q * q != (int32_t)e2)
        return 0;
    if ((uint32_t)((int64_t)d * q * q * q) != e3)
        return 0;
    p[q - 1] = (uint8_t)(p[q - 1] - (uint8_t)d);
    triple4(p, s);
    return !((s[0] - ref[0]) | (s[1] - ref[1]) | (s[2] - ref[2]) |
             (s[3] - ref[3]));
}
static uint64_t ktag(uint64_t K, const uint8_t *m, size_t n,
                     uint64_t dom) {
    uint64_t h = K ^ dom;
    for (size_t i = 0; i < n; i++) {
        h ^= m[i] + 0x9E3779B97F4A7C15ull + (h << 6) + (h >> 2) + i;
        if ((i & 63) == 63) {
            uint64_t s = h;
            h = sm64(&s);
        }
    }
    uint64_t s = h ^ (uint64_t)n;
    return sm64(&s);
}
static void build(void) {
    gf_init();
    for (int u = 0; u < NP; u++)
        for (int k = 0; k < PL; k++) {
            int j = 8 * k + u;
            bku[u][k] =
                (uint8_t)(((j * 67 + 41) ^ 0x3C ^ (j >> 3)) & 0xFF);
        }
    bku[0][0] = 0x45;
    bku[1][0] = 0x53;
    bku[2][0] = 0x46;
    bku[3][0] = 0x32;
    for (int u = 0; u < NP; u++)
        triple4(bku[u], refs[u]);
    memset(parP, 0, PL);
    memset(parQ, 0, PL);
    for (int u = 0; u < NP; u++) {
        uint8_t c = gexp[u];
        for (int i = 0; i < PL; i++) {
            parP[i] ^= bku[u][i];
            parQ[i] ^= gfm(c, bku[u][i]);
        }
    }
}
static void dmg_spread(int n) {
    for (int j = 0; j < n; j++) {
        int pos = (int)(trand() % FR), dv;
        do {
            dv = (int)((trand() & 255) + 1) & 255;
        } while (!dv);
        fru[pos % 8][pos / 8] ^= (uint8_t)dv;
    }
}
static void dmg_burst(int len) {
    int st = (int)(trand() % (FR - len));
    for (int j = 0; j < len; j++) {
        int pos = st + j, dv;
        do {
            dv = (int)((trand() & 255) + 1) & 255;
        } while (!dv);
        fru[pos % 8][pos / 8] ^= (uint8_t)dv;
    }
}
static int dmg_loss(int d, int *lost) {
    int n = 0;
    memset(lost, 0, NP * sizeof(int));
    while (n < d) {
        int p = (int)(trand() % NP);
        if (!lost[p]) {
            lost[p] = 1;
            memset(fru[p], 0, PL);
            n++;
        }
    }
    return n;
}
static int used[FR];
static int force_err(const int *lost, int e) {
    int nu = 0;
    memset(used, 0, sizeof used);
    for (int j = 0; j < e; j++) {
        int pos, u;
        do {
            pos = (int)(trand() % FR);
            u = pos % 8;
        } while ((lost && lost[u]) || used[pos]);
        used[pos] = 1;
        int dv;
        do {
            dv = (int)((trand() & 255) + 1) & 255;
        } while (!dv);
        fru[u][pos / 8] ^= (uint8_t)dv;
        nu++;
    }
    return nu;
}
static void solve_erase(const int *lost) {
    int L[2], nl = 0;
    for (int p = 0; p < NP && nl < 2; p++)
        if (lost[p])
            L[nl++] = p;
    if (nl == 1) {
        int a = L[0];
        for (int i = 0; i < PL; i++) {
            uint8_t v = parP[i];
            for (int p = 0; p < NP; p++)
                if (p != a)
                    v ^= fru[p][i];
            fru[a][i] = v;
        }
    } else if (nl == 2) {
        int a = L[0], b = L[1];
        uint8_t ca = gexp[a], cb = gexp[b], den = ca ^ cb;
        for (int i = 0; i < PL; i++) {
            uint8_t pp = parP[i], qq = parQ[i];
            for (int p = 0; p < NP; p++)
                if (p != a && p != b) {
                    pp ^= fru[p][i];
                    qq ^= gfm(gexp[p], fru[p][i]);
                }
            uint8_t ua = gf_div(qq ^ gfm(cb, pp), den);
            fru[a][i] = ua;
            fru[b][i] = pp ^ ua;
        }
    }
}
static void run_ecc(const int *lost, int nloss) {
    for (int p = 0; p < NP; p++) {
        if (lost && lost[p])
            continue;
        sec_pkt(fru[p], refs[p]);
    }
    if (lost && nloss >= 1 && nloss <= 2) {
        solve_erase(lost);
        for (int p = 0; p < NP; p++)
            if (lost[p])
                sec_pkt(fru[p], refs[p]);
    }
}
static int bytes_ok(void) {
    int n = 0;
    for (int u = 0; u < NP; u++)
        for (int i = 0; i < PL; i++)
            n += (fru[u][i] == bku[u][i]);
    return n;
}
#define CHECK(c) do { if (!(c)) fails++; } while (0)
int main(void) {
    build();
    /* K self-tests (no RNG): fix-1, refuse-2, gf roundtrip */
    static uint8_t t[PL];
    int secfix, secref, gfd = 1;
    memcpy(t, bku[2], PL);
    t[100] ^= 0x5A;
    secfix = sec_pkt(t, refs[2]) && !memcmp(t, bku[2], PL);
    memcpy(t, bku[5], PL);
    t[10] ^= 0x11;
    t[400] ^= 0x22;
    secref = !sec_pkt(t, refs[5]);
    {
        const uint8_t aa[] = { 1, 2, 0x53, 0xFF };
        const uint8_t bb[] = { 1, 3, 0x1B, 0x80 };
        for (int i = 0; i < 4 && gfd; i++)
            for (int j = 0; j < 4 && gfd; j++)
                if (gf_div(gfm(aa[i], bb[j]), bb[j]) != aa[i])
                    gfd = 0;
    }
    CHECK(secfix);
    CHECK(secref);
    CHECK(gfd);
    printf("K secfix=%d secref=%d gfdiv=%d\n", secfix, secref, gfd);
    /* cells */
    const char *nm[5] = { "SP1", "BUI8", "LO1", "LO2", "MX" };
    for (int c = 0; c < 5; c++) {
        int full = 0;
        long tot = 0;
        int lost[NP];
        for (int tt = 0; tt < NTR; tt++) {
            memcpy(fru, bku, sizeof fru);
            if (c == 0) {
                dmg_spread(1);
                run_ecc(NULL, 0);
            } else if (c == 1) {
                dmg_burst(8);
                run_ecc(NULL, 0);
            } else if (c == 2) {
                int nl = dmg_loss(1, lost);
                run_ecc(lost, nl);
            } else if (c == 3) {
                int nl = dmg_loss(2, lost);
                run_ecc(lost, nl);
            } else {
                int nl = dmg_loss(1, lost);
                force_err(lost, 2);
                run_ecc(lost, nl);
            }
            int bo = bytes_ok();
            tot += bo;
            full += (bo == FR);
        }
        printf("C %s full=%d tot=%ld\n", nm[c], full, tot);
    }
    /* promise: tampered P+Q must fail */
    static uint8_t pq[2 * PL], pt2[2 * PL];
    memcpy(pq, parP, PL);
    memcpy(pq + PL, parQ, PL);
    uint64_t pc = ktag(BONDK, pq, 2 * PL, 0x50524F4D495345ull);
    memcpy(pt2, pq, 2 * PL);
    pt2[100] ^= 0x01;
    int commit = ktag(BONDK, pt2, 2 * PL, 0x50524F4D495345ull) != pc;
    CHECK(commit);
    printf("P commit=%d\n", commit);
    printf("R %s\n", fails ? "FAIL" : "PASS");
    return fails != 0;
}
