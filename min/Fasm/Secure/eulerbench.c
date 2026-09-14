/* eulerbench.c -- three Euler-flavored optimizations for the wire format.
 *
 * A. UNIT SIZE (calculus): frame F=4096, unit u, n=F/u units, wire =
 *    F + 16n (syndromes) + 2u (P+Q). d(wire)/du = -16F/u^2+2 = 0 ->
 *    u* = sqrt(8F) ~= 181. Burst rating = interleave depth = n.
 *    Table below checks integer sizes (analytic; SEC is size-agnostic).
 * B. GEOMETRIC BURSTS (Euler by derivation + measurement): burst length
 *    L ~ Geometric(mean mu) on {1,2,..}, P(L>k) = (mu/(mu+1))^k ~=
 *    e^(-k/mu). Recovery needs L <= depth (8): predicted full rate =
 *    1-(mu/(mu+1))^8 ~= 1-e^(-8/mu). Measured with the real SEC path.
 * C. FETCH-RETRY BACKOFF (Euler by pedigree): fetch channel drops the
 *    parity with prob q/attempt (bursty model); retry waits b^k
 *    frame-times, give up after K fails -> resend. Sweep base b incl.
 *    e; same give-up rule, mean added latency in frame-times.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

#define NP 8
#define PL 512
#define FR (NP * PL)
#define NTR 200

static uint8_t bku[NP][PL], fru[NP][PL];
static uint32_t refs[NP][4];

static uint64_t trng = 0xE01E7A98012345ull;
static uint64_t trand(void) {
    trng ^= trng << 13;
    trng ^= trng >> 7;
    trng ^= trng << 17;
    return trng;
}
static double drand(void) { /* [0,1) 53-bit */
    return (double)(trand() >> 11) * (1.0 / 9007199254740992.0);
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
}
static int bytes_ok(void) {
    int n = 0;
    for (int u = 0; u < NP; u++)
        for (int i = 0; i < PL; i++)
            n += (fru[u][i] == bku[u][i]);
    return n;
}
int main(void) {
    build();
    /* ---- A: unit-size frontier (analytic) ---- */
    printf("A: unit-size frontier (F=4096, seg=1460)\n");
    printf("%5s %4s %6s %5s %6s %6s\n", "u", "n", "wire", "segs",
           "spare", "rating");
    const int us[] = { 64, 128, 181, 256, 512, 537, 1024 };
    for (int i = 0; i < 7; i++) {
        double u = (double)us[i], n = 4096.0 / u;
        double wire = 4096.0 + 16.0 * n + 2.0 * u;
        int segs = (int)((wire + 1459.0) / 1460.0);
        printf("%5d %4.1f %6.0f %5d %6.0f %6.1f%s\n", us[i], n, wire,
               segs, segs * 1460.0 - wire, n,
               us[i] == 537 ? "  <- 1460/e" : us[i] == 512 ? "  <- now"
                                                           : "");
    }
    printf("A: u* = sqrt(8*4096) = 181.0 (AM-GM: 128x256 tie)\n");
    /* ---- B: geometric bursts vs 1-e^(-8/mu) ---- */
    printf("B: geometric bursts, depth 8: mu, measured, "
           "1-(mu/(mu+1))^8, 1-e^(-8/mu)\n");
    const double mus[] = { 2, 4, 8, 12, 16, 24, 32 };
    for (int mi = 0; mi < 7; mi++) {
        double mu = mus[mi], r = mu / (mu + 1.0);
        int full = 0;
        for (int t = 0; t < NTR; t++) {
            memcpy(fru, bku, sizeof fru);
            double U = drand();
            if (U <= 0.0)
                U = 0.5 / 9007199254740992.0;
            int L = 1 + (int)(log(U) / log(r));
            if (L < 1)
                L = 1;
            if (L > FR)
                L = FR;
            int st = (int)(trand() % (uint64_t)(FR - L + 1));
            for (int j = 0; j < L; j++) {
                int pos = st + j, dv;
                do {
                    dv = (int)((trand() & 255) + 1) & 255;
                } while (!dv);
                fru[pos % 8][pos / 8] ^= (uint8_t)dv;
            }
            for (int p = 0; p < NP; p++)
                sec_pkt(fru[p], refs[p]);
            full += (bytes_ok() == FR);
        }
        double pred = 1.0 - pow(r, 8), eux = 1.0 - exp(-8.0 / mu);
        printf("B: mu=%5.1f meas=%.3f exact=%.3f e-approx=%.3f\n", mu,
               full / 200.0, pred, eux);
    }
    /* ---- C: fetch-retry backoff base ---- */
    printf("C: retry base sweep (q=0.25/attempt, K=4, RTT=10ft, "
           "fetch=0.5ft)\n");
    const double bs[] = { 1.5, 2.0, 2.718281828, 3.0, 4.0 };
    for (int bi = 0; bi < 5; bi++) {
        double b = bs[bi], tot = 0;
        const int N = 20000;
        for (int t = 0; t < N; t++) {
            double c = 0;
            int k;
            for (k = 0; k < 4; k++) {
                if (drand() >= 0.25) {
                    c += 0.5;
                    break;
                }
                c += pow(b, k);
            }
            if (k == 4)
                c += 10.0 + 1.0; /* give up: resend */
            tot += c;
        }
        printf("C: b=%.3f mean-latency=%.3fft\n", b, tot / N);
    }
    return 0;
}
