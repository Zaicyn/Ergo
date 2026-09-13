/* demandbench.c -- parity-on-demand protocol simulation.
 *
 * Routine frame on wire: 4096 B data + 256 B metadata in 3x1460 B
 * segments. Metadata = 128 B syndromes + 64 B parity commitment
 * (keyed tag over P+Q: "these exact parity bytes exist") + 64 B
 * stream authenticator (bond tag over frame+metadata).
 * Sender retains P+Q per unacked frame (1 KB x window).
 * Receiver: SEC from syndromes; clean -> done (0 RTT). Hurt beyond
 * SEC -> fetch parity (+1088 B, +1 RTT), rebuild, check commitment;
 * commitment mismatch or still dirty -> resend fallback (+4096 B,
 * +1 RTT). Baselines: ALWAYS (P+Q routine, 4 segs) and TCP
 * (frame-resend on any damage; SACK would narrow but not close it).
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define NP 8
#define PL 512
#define FR (NP * PL)
#define SEG 1460
#define META 256
#define NSIM 2000

static uint8_t bku[NP][PL], fru[NP][PL], parP[PL], parQ[PL];
static uint32_t refs[NP][4];
static uint8_t gexp[512], glog[256];
static uint64_t bondK;

static uint64_t trng = 0xC0FFEE123456789ull;
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
/* keyed 64-bit tag over a byte string (commitment / authenticator) */
static uint64_t ktag(uint64_t K, const uint8_t *m, size_t n, uint64_t dom) {
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
    bondK = 18050561372206496278ull; /* measured rgba_hs bond key */
}
/* damage models in wire coords (pos -> unit pos%8, off pos/8) */
static void dmg(int kind, int *lost, int *nloss) {
    *nloss = 0;
    memset(lost, 0, NP * sizeof(int));
    if (kind == 0)
        return;
    if (kind <= 3) { /* spread n = 1, 3, 8 */
        int n = kind == 1 ? 1 : kind == 2 ? 3 : 8;
        for (int j = 0; j < n; j++) {
            int pos = (int)(trand() % FR), dv;
            do {
                dv = (int)((trand() & 255) + 1) & 255;
            } while (!dv);
            fru[pos % 8][pos / 8] ^= (uint8_t)dv;
        }
    } else if (kind <= 5) { /* burst L = 6, 64 */
        int len = kind == 4 ? 6 : 64;
        int st = (int)(trand() % (FR - len));
        for (int j = 0; j < len; j++) {
            int pos = st + j, dv;
            do {
                dv = (int)((trand() & 255) + 1) & 255;
            } while (!dv);
            fru[pos % 8][pos / 8] ^= (uint8_t)dv;
        }
    } else if (kind <= 7) { /* loss d = 1, 2 */
        int d = kind - 5, n = 0;
        while (n < d) {
            int p = (int)(trand() % NP);
            if (!lost[p]) {
                lost[p] = 1;
                memset(fru[p], 0, PL);
                n++;
            }
        }
        *nloss = n;
    } else { /* mixed: 1 loss + 2 err */
        int n = 0;
        while (n < 1) {
            int p = (int)(trand() % NP);
            if (!lost[p]) {
                lost[p] = 1;
                memset(fru[p], 0, PL);
                n++;
            }
        }
        *nloss = 1;
        for (int j = 0; j < 2; j++) {
            int pos = (int)(trand() % FR), dv;
            int u = pos % 8, o = pos / 8;
            if (lost[u])
                continue;
            do {
                dv = (int)((trand() & 255) + 1) & 255;
            } while (!dv);
            fru[u][o] ^= (uint8_t)dv;
        }
    }
}
static int bytes_ok(void) {
    int n = 0;
    for (int u = 0; u < NP; u++)
        for (int i = 0; i < PL; i++)
            n += (fru[u][i] == bku[u][i]);
    return n;
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
/* receiver repair attempt; parity[] available iff fetched/routine.
 * returns 1 if frame fully recovered. */
static int repair(const int *lost, int nloss, int have_pq) {
    for (int p = 0; p < NP; p++) {
        if (lost && lost[p])
            continue;
        sec_pkt(fru[p], refs[p]);
    }
    if (lost && nloss >= 1 && nloss <= 2 && have_pq) {
        solve_erase(lost);
        for (int p = 0; p < NP; p++)
            if (lost[p])
                sec_pkt(fru[p], refs[p]);
    }
    return bytes_ok() == FR;
}
int main(void) {
    build();
    /* commitment self-test: tampered parity must fail the promise */
    static uint8_t pqcat[2 * PL], pqtmp[2 * PL];
    memcpy(pqcat, parP, PL);
    memcpy(pqcat + PL, parQ, PL);
    uint64_t promise = ktag(bondK, pqcat, 2 * PL, 0x50524F4D495345ull);
    memcpy(pqtmp, pqcat, 2 * PL);
    pqtmp[100] ^= 0x01;
    if (ktag(bondK, pqtmp, 2 * PL, 0x50524F4D495345ull) == promise) {
        printf("PROMISE-TEST: FAIL (tamper accepted)\n");
        return 1;
    }
    printf("PROMISE-TEST: ok (1B parity tamper rejected)\n");
    /* weights over damage kinds 0..8 (0 = clean handled by f) */
    const int w[9] = { 0, 20, 15, 10, 15, 5, 15, 5, 15 };
    int wsum = 0;
    for (int i = 1; i < 9; i++)
        wsum += w[i];
    printf("%5s %10s %8s %10s %8s %10s %8s\n", "f", "dem-bytes",
           "dem-rtt", "alw-bytes", "alw-rtt", "tcp-bytes", "tcp-rtt");
    const double fs[] = { 0.0, 0.01, 0.05, 0.10, 0.25, 0.50, 0.80 };
    for (int fi = 0; fi < 7; fi++) {
        double f = fs[fi], bd = 0, rd = 0, ba = 0, ra = 0, bt = 0,
               rt = 0;
        for (int t = 0; t < NSIM; t++) {
            memcpy(fru, bku, sizeof fru);
            int lost[NP], nloss = 0, kind = 0;
            double r = (double)(trand() % 1000000) / 1000000.0;
            if (r < f) {
                int pick = (int)(trand() % (uint64_t)wsum), acc = 0;
                for (int k = 1; k < 9; k++) {
                    acc += w[k];
                    if (pick < acc) {
                        kind = k;
                        break;
                    }
                }
                dmg(kind, lost, &nloss);
            }
            int dirty = bytes_ok() != FR;
            /* on-demand: routine + fetch + fallback */
            double cd = FR + META;
            double dd = 0;
            if (dirty && !repair(lost, nloss, 0)) {
                cd += 64 + 2 * PL; /* request + P+Q fetch */
                dd += 1;
                if (!repair(lost, nloss, 1)) {
                    cd += FR; /* resend fallback */
                    dd += 1;
                }
            }
            bd += cd;
            rd += dd;
            /* always-send: routine+P+Q, resend if unrecoverable */
            memcpy(fru, bku, sizeof fru);
            if (kind)
                dmg(kind, lost, &nloss);
            double ca = FR + 2 * PL + NP * 16;
            double da = 0;
            if (dirty && !repair(lost, nloss, 1)) {
                ca += FR;
                da += 1;
            }
            ba += ca;
            ra += da;
            /* tcp: frame resend on any damage */
            double ct = FR + META;
            double dt = 0;
            if (dirty) {
                ct += FR;
                dt += 1;
            }
            bt += ct;
            rt += dt;
        }
        printf("%5.2f %10.0f %8.3f %10.0f %8.3f %10.0f %8.3f\n", f,
               bd / NSIM, rd / NSIM, ba / NSIM, ra / NSIM, bt / NSIM,
               rt / NSIM);
    }
    printf("RETENTION 1KB x 64-frame window = 64KB sender-side\n");
    return 0;
}
