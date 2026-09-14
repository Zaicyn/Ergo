/* packetbench.c v2 -- stream recovery without resend, wire format.
 *
 * PACKING (the 1460 B question): unit = 512 B. 1460/512 = 2.85 units
 * per TCP segment: 2 full units (1024 B) + 436 B spare. One 4096 B
 * frame = 8 units rides in 4 segments; the 4x436 = 1744 B of spare
 * funds P+Q parities (2x512) + 8x16 B syndromes = 1152 B, 592 B left.
 *
 * WIRE FORMAT: depth-8 byte interleave. Unit u holds frame bytes
 * {u+8k}. A channel burst contiguous on the wire of length L<=8 lands
 * 1 byte each in L distinct units -> per-unit SEC fixes all of them.
 * Erasures are solved, not searched: P = row XOR, Q = GF(256) weighted
 * sum (coeffs 2^p) -> any 1-2 whole-unit losses rebuild exactly.
 * Order: SEC survivors -> rebuild from clean data -> reverify.
 *
 * Cells (NTR=200, deterministic draws): SP spread n=1,2,4,8;
 * BU-I interleaved bursts L=4,8,16,64,256; BU64 non-interleaved burst
 * control; LO d=1,2 whole-unit loss; MX 1loss+2err; MX2 2loss+2err;
 * SEG 1460 B wire-interval erasure (the measured limit).
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define NP 8
#define PL 512
#define FR (NP * PL)
#define NTR 200
#define SEG 1460

static uint8_t bku[NP][PL], fru[NP][PL], parP[PL], parQ[PL];
static uint32_t refs[NP][4];
static uint8_t gexp[512], glog[256];
static long cbn[8], cbf[8]; /* collapse buckets by effective error count */
static void bucket(int e, int full) {
    if (e < 0) e = 0;
    if (e > 7) e = 7;
    cbn[e]++;
    cbf[e] += full;
}

static uint64_t trng = 0x123456789ABCDEF1ull;
static uint64_t trand(void) {
    trng ^= trng << 13;
    trng ^= trng >> 7;
    trng ^= trng << 17;
    return trng;
}
/* GF(256), poly 0x11B */
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
        v = gfm(v, 3); /* 3 is primitive (ord 255); 2 is not (ord 51) */
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
static void build(void) {
    gf_init();
    for (int u = 0; u < NP; u++)
        for (int k = 0; k < PL; k++) {
            int j = 8 * k + u; /* frame byte -> unit u, offset k */
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
        uint8_t c = gexp[u]; /* 3^u, distinct nonzero */
        for (int i = 0; i < PL; i++) {
            parP[i] ^= bku[u][i];
            parQ[i] ^= gfm(c, bku[u][i]);
        }
    }
}
/* damage in wire (= frame) coords: pos -> unit pos%8, off pos/8 */
static void dmg_spread(int n) {
    for (int j = 0; j < n; j++) {
        int pos = (int)(trand() % FR), dv, u = pos % 8, o = pos / 8;
        do {
            dv = (int)((trand() & 255) + 1) & 255;
        } while (!dv);
        fru[u][o] ^= (uint8_t)dv;
    }
}
static void dmg_burst(int len) {
    int st = (int)(trand() % (FR - len));
    for (int j = 0; j < len; j++) {
        int pos = st + j, dv, u = pos % 8, o = pos / 8;
        do {
            dv = (int)((trand() & 255) + 1) & 255;
        } while (!dv);
        fru[u][o] ^= (uint8_t)dv;
    }
}
/* forced errors: exactly e distinct byte-flips in non-lost units.
 * Returns effective count (= e; positions distinct by construction). */
static int force_err(const int *lost, int e) {
    int used[FR], nu = 0;
    memset(used, 0, sizeof used);
    for (int j = 0; j < e; j++) {
        int pos, u, tries = 0;
        do {
            pos = (int)(trand() % FR);
            u = pos % 8;
            tries++;
        } while ((lost && lost[u]) || used[pos]);
        (void)tries;
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
/* multi-burst: nb bursts of len L at independent random starts
 * (union damage; overlapping fades allowed, like real channels) */
static void dmg_burstN(int nb, int len) {
    for (int b = 0; b < nb; b++) {
        int st = (int)(trand() % (FR - len));
        for (int j = 0; j < len; j++) {
            int pos = st + j, dv;
            do {
                dv = (int)((trand() & 255) + 1) & 255;
            } while (!dv);
            fru[pos % 8][pos / 8] ^= (uint8_t)dv;
        }
    }
}
/* burst confined to one unit (non-interleaved control) */
static void dmg_burst1(int len) {
    int u = (int)(trand() % NP), st = (int)(trand() % (PL - len));
    for (int j = 0; j < len; j++) {
        int dv;
        do {
            dv = (int)((trand() & 255) + 1) & 255;
        } while (!dv);
        fru[u][st + j] ^= (uint8_t)dv;
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
/* wire-interval erasure (segment damage): zero all unit bytes whose
 * frame position falls in [st, st+len). Returns bytes erased. */
static int dmg_seg(int len) {
    int st = (int)(trand() % (FR - len)), n = 0;
    for (int j = 0; j < len; j++) {
        int pos = st + j;
        fru[pos % 8][pos / 8] = 0;
        n++;
    }
    return n;
}
static int bytes_ok(void) {
    int n = 0;
    for (int u = 0; u < NP; u++)
        for (int i = 0; i < PL; i++)
            n += (fru[u][i] == bku[u][i]);
    return n;
}
/* exact 1-2 erasure solve from P+Q (data already SEC-cleaned) */
static void solve_erase(const int *lost, int nloss) {
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
            /* pp=Ua^Ub; qq=ca.Ua^cb.Ub -> Ua=(qq^cb.pp)/(ca^cb) */
            uint8_t ua = gf_div(qq ^ gfm(cb, pp), den);
            fru[a][i] = ua;
            fru[b][i] = pp ^ ua;
        }
    }
    (void)nloss;
}
static void run_ecc(const int *lost, int nloss) {
    for (int p = 0; p < NP; p++) {
        if (lost && lost[p])
            continue;
        sec_pkt(fru[p], refs[p]);
    }
    if (lost && nloss >= 1 && nloss <= 2) {
        solve_erase(lost, nloss);
        for (int p = 0; p < NP; p++)
            if (lost[p])
                sec_pkt(fru[p], refs[p]); /* reverify, no-op if exact */
    }
}
static void restore(void) {
    memcpy(fru, bku, sizeof fru);
}
#define CELL(name, fmt, ...) \
    { int full = 0; long be = 0; \
      for (int t = 0; t < NTR; t++) { __VA_ARGS__; } \
      printf(name " " fmt " ecc=%.1f full=%d/200\n", be / 200.0, full); }
#define FINISH() \
    { int bo = bytes_ok(); be += bo; full += (bo == FR); }

int main(void) {
    build();
    printf("PACK units/seg=2.85 (2x512+436spare) segs/frame=4 "
           "overhead=%dB spare-left=%dB\n",
           2 * PL + NP * 16, 4 * (SEG - 2 * PL) - (2 * PL + NP * 16));
    { const int ns[] = { 1, 2, 4, 8 };
      for (int ni = 0; ni < 4; ni++) {
          int full = 0; long be = 0;
          for (int tt = 0; tt < NTR; tt++) {
              restore(); dmg_spread(ns[ni]); run_ecc(NULL, 0);
              int bo = bytes_ok(); be += bo; full += (bo == FR);
              bucket(ns[ni], bo == FR);
          }
          printf("SP n=%d ecc=%.1f full=%d/200\n", ns[ni], be / 200.0,
                 full);
      } }
    CELL("BUI", "L=4", restore(); dmg_burst(4); run_ecc(NULL, 0); FINISH());
    CELL("BUI", "L=8", restore(); dmg_burst(8); run_ecc(NULL, 0); FINISH());
    CELL("BUI", "L=16", restore(); dmg_burst(16); run_ecc(NULL, 0); FINISH());
    CELL("BUI", "L=64", restore(); dmg_burst(64); run_ecc(NULL, 0); FINISH());
    CELL("BUI", "L=256", restore(); dmg_burst(256); run_ecc(NULL, 0); FINISH());
    CELL("BU1", "L=64", restore(); dmg_burst1(64); run_ecc(NULL, 0); FINISH());
    /* multi-burst occupancy: predict 2xL2~60%%, 2xL4~12%%, 2xL8=0 */
    CELL("B2", "2xL2", restore(); dmg_burstN(2, 2); run_ecc(NULL, 0); FINISH());
    CELL("B2", "2xL4", restore(); dmg_burstN(2, 4); run_ecc(NULL, 0); FINISH());
    CELL("B3", "3xL2", restore(); dmg_burstN(3, 2); run_ecc(NULL, 0); FINISH());
    CELL("B2", "2xL8", restore(); dmg_burstN(2, 8); run_ecc(NULL, 0); FINISH());
    { int full = 0; long be = 0; int lost[NP];
      for (int tt = 0; tt < NTR; tt++) {
          restore(); int nl = dmg_loss(1, lost); dmg_burstN(1, 4);
          run_ecc(lost, nl); FINISH(); }
      printf("BL L4+LO1 ecc=%.1f full=%d/200\n", be / 200.0, full); }
    { int full = 0; long be = 0; int lost[NP];
      for (int t = 0; t < NTR; t++) {
          restore(); int nl = dmg_loss(1, lost); run_ecc(lost, nl);
          FINISH(); } printf("LO d=1 ecc=%.1f full=%d/200\n", be / 200.0, full); }
    { int full = 0; long be = 0; int lost[NP];
      for (int t = 0; t < NTR; t++) {
          restore(); int nl = dmg_loss(2, lost); run_ecc(lost, nl);
          FINISH(); } printf("LO d=2 ecc=%.1f full=%d/200\n", be / 200.0, full); }
    { int full = 0; long be = 0; int lost[NP];
      for (int t = 0; t < NTR; t++) {
          restore(); int nl = dmg_loss(1, lost);
          int ne = force_err(lost, 2);
          run_ecc(lost, nl);
          int bo0 = bytes_ok(); be += bo0; full += (bo0 == FR);
          bucket(ne, bo0 == FR); }
      printf("MX 1loss+2err ecc=%.1f full=%d/200\n", be / 200.0, full); }
    { int full = 0; long be = 0; int lost[NP];
      for (int t = 0; t < NTR; t++) {
          restore(); int nl = dmg_loss(2, lost);
          int ne = force_err(lost, 2);
          run_ecc(lost, nl);
          int bo0 = bytes_ok(); be += bo0; full += (bo0 == FR);
          bucket(ne, bo0 == FR); }
      printf("MX2 2loss+2err ecc=%.1f full=%d/200\n", be / 200.0, full); }
    { int full = 0; long be = 0;
      for (int t = 0; t < NTR; t++) {
          restore(); dmg_seg(SEG); run_ecc(NULL, 0); FINISH(); }
      printf("SEG 1460B-erasure ecc=%.1f full=%d/200\n", be / 200.0, full); }
    /* GRID: loss D=0..2 x forced errors E=0..3, exact effective counts */
    printf("GRID loss x errors (full/200):\n");
    for (int D = 0; D <= 2; D++) {
        printf("D=%d:", D);
        for (int E = 0; E <= 3; E++) {
            int full = 0; long be = 0; int lost[NP];
            for (int tt = 0; tt < NTR; tt++) {
                restore();
                int nl = 0;
                if (D) nl = dmg_loss(D, lost);
                else memset(lost, 0, sizeof lost);
                int ne = force_err(D ? lost : NULL, E);
                run_ecc(D ? lost : NULL, nl);
                int bo = bytes_ok(); be += bo; full += (bo == FR);
                bucket(ne, bo == FR);
            }
            printf(" E=%d:%d/%.0f", E, full, be / 200.0);
        }
        printf("\n");
    }
    printf("COLLAPSE by effective-error-count (all spread cells):\n");
    for (int e = 0; e <= 4; e++)
        printf("eff=%d n=%ld full=%ld rate=%.3f\n", e, cbn[e], cbf[e],
               cbn[e] ? (double)cbf[e] / (double)cbn[e] : 0.0);
    return 0;
}
