/* packetbench.c -- stream/packet recovery without resend.
 *
 * Frame = 4096 B = 8 packets x 512 B + 1 XOR parity packet (512 B).
 * Per-packet S0..S3 syndromes (idx 1..512) + gated single-byte SEC per
 * packet; single whole-packet loss rebuilt from parity (known position
 * = erasure, no search). Damage is injected per trial (NTR=200,
 * deterministic xorshift draws), then each policy runs on a snapshot:
 *
 *   UDP    accept damage (bytes_correct = 4096 - damaged, 0 RTT)
 *   ECC    per-packet SEC + parity rebuild (0 RTT, overhead bytes only)
 *   RESEND ground truth: always 4096/4096 at 1 RTT + 4096 resend bytes
 *
 * Cells: spread n-byte errors (n=1..8), burst runs (L=4,16,64,256),
 * whole-packet loss (d=1,2), mixed (1 loss + 2 errors).
 * Report per cell: fullok/200, mean bytes_correct/4096, and the cost
 * model: ECC overhead = 512 B parity + 8x16 B syndromes = 640 B/frame
 * (15.6%) once, vs 4096 B + 1 RTT per resend.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define NP 8
#define PL 512
#define FR (NP * PL)
#define NTR 200

static uint8_t bk[FR], fr[FR], par[PL];
static uint32_t refs[NP][4];

static uint64_t trng = 0x123456789ABCDEF1ull;
static uint64_t trand(void) {
    trng ^= trng << 13;
    trng ^= trng >> 7;
    trng ^= trng << 17;
    return trng;
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
/* gated single-byte SEC on one packet; returns 1 if repaired-or-clean */
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
    for (int i = 0; i < FR; i++)
        bk[i] = (uint8_t)(((i * 67 + 41) ^ 0x3C ^ (i >> 3)) & 0xFF);
    bk[0] = 0x45;
    bk[1] = 0x53;
    bk[2] = 0x46;
    bk[3] = 0x32;
    for (int p = 0; p < NP; p++)
        triple4(bk + p * PL, refs[p]);
    memset(par, 0, PL);
    for (int p = 0; p < NP; p++)
        for (int i = 0; i < PL; i++)
            par[i] ^= bk[p * PL + i];
}
/* damage kinds; lost[] marks erased packets (content zeroed) */
static void dmg_spread(int n) {
    for (int j = 0; j < n; j++) {
        int pos = (int)(trand() % FR), dv;
        do {
            dv = (int)((trand() & 255) + 1) & 255;
        } while (!dv);
        fr[pos] ^= (uint8_t)dv;
    }
}
static void dmg_burst(int len) {
    int st = (int)(trand() % (FR - len));
    for (int j = 0; j < len; j++) {
        int dv;
        do {
            dv = (int)((trand() & 255) + 1) & 255;
        } while (!dv);
        fr[st + j] ^= (uint8_t)dv;
    }
}
/* returns # lost; lost[] flags */
static int dmg_loss(int d, int *lost) {
    int n = 0;
    memset(lost, 0, NP * sizeof(int));
    while (n < d) {
        int p = (int)(trand() % NP);
        if (!lost[p]) {
            lost[p] = 1;
            memset(fr + p * PL, 0, PL);
            n++;
        }
    }
    return n;
}
static int bytes_ok(void) {
    int n = 0;
    for (int i = 0; i < FR; i++)
        n += (fr[i] == bk[i]);
    return n;
}
/* ECC: parity rebuild for single loss, then per-packet SEC.
 * NOTE: parity rebuild needs the parity packet intact; loss cell with
 * d>=1 never damages par (loss = dropped data packets only). */
static void run_ecc(const int *lost, int nloss) {
    /* 1. SEC survivors FIRST: rebuilding from dirty survivors
     * transplants their errors into the rebuilt packet. */
    for (int p = 0; p < NP; p++) {
        if (lost && lost[p])
            continue;
        sec_pkt(fr + p * PL, refs[p]);
    }
    /* 2. parity rebuild from cleaned survivors, then reverify. */
    if (nloss == 1) {
        int lp = 0;
        while (!lost[lp])
            lp++;
        for (int i = 0; i < PL; i++) {
            uint8_t v = par[i];
            for (int p = 0; p < NP; p++)
                if (p != lp)
                    v ^= fr[p * PL + i];
            fr[lp * PL + i] = v;
        }
        sec_pkt(fr + lp * PL, refs[lp]);
    }
}
static void cell_spread(int n) {
    int full = 0;
    long budp = 0, becc = 0;
    for (int t = 0; t < NTR; t++) {
        memcpy(fr, bk, FR);
        dmg_spread(n);
        budp += bytes_ok();
        run_ecc(NULL, 0);
        int bo = bytes_ok();
        becc += bo;
        full += (bo == FR);
    }
    printf("SP n=%d udp=%.1f ecc=%.1f full=%d/200\n", n, budp / 200.0,
           becc / 200.0, full);
}
static void cell_burst(int len) {
    int full = 0;
    long budp = 0, becc = 0;
    for (int t = 0; t < NTR; t++) {
        memcpy(fr, bk, FR);
        dmg_burst(len);
        budp += bytes_ok();
        run_ecc(NULL, 0);
        int bo = bytes_ok();
        becc += bo;
        full += (bo == FR);
    }
    printf("BU L=%d udp=%.1f ecc=%.1f full=%d/200\n", len, budp / 200.0,
           becc / 200.0, full);
}
static void cell_loss(int d) {
    int full = 0;
    long budp = 0, becc = 0;
    int lost[NP];
    for (int t = 0; t < NTR; t++) {
        memcpy(fr, bk, FR);
        int nl = dmg_loss(d, lost);
        budp += bytes_ok();
        run_ecc(lost, nl);
        int bo = bytes_ok();
        becc += bo;
        full += (bo == FR);
    }
    printf("LO d=%d udp=%.1f ecc=%.1f full=%d/200\n", d, budp / 200.0,
           becc / 200.0, full);
}
static void cell_mixed(void) {
    int full = 0;
    long budp = 0, becc = 0;
    int lost[NP];
    for (int t = 0; t < NTR; t++) {
        memcpy(fr, bk, FR);
        int nl = dmg_loss(1, lost);
        /* errors only in surviving packets */
        for (int j = 0; j < 2; j++) {
            int p, pos, dv;
            do {
                p = (int)(trand() % NP);
            } while (lost[p]);
            pos = p * PL + (int)(trand() % PL);
            do {
                dv = (int)((trand() & 255) + 1) & 255;
            } while (!dv);
            fr[pos] ^= (uint8_t)dv;
        }
        budp += bytes_ok();
        run_ecc(lost, nl);
        int bo = bytes_ok();
        becc += bo;
        full += (bo == FR);
    }
    printf("MX 1loss+2err udp=%.1f ecc=%.1f full=%d/200\n", budp / 200.0,
           becc / 200.0, full);
}
int main(void) {
    build();
    for (int n = 1; n <= 8; n++)
        cell_spread(n);
    cell_burst(4);
    cell_burst(16);
    cell_burst(64);
    cell_burst(256);
    cell_loss(1);
    cell_loss(2);
    cell_mixed();
    printf("COST ecc-overhead=%dB/frame resend=4096B+1RTT\n",
           PL + NP * 16);
    return 0;
}
