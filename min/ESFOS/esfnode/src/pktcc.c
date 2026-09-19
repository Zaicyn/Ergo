/* pktcc.c -- portable packet-codec core. Bodies verbatim from
 * min/Fasm/Secure/pktcodec.c (same draws not needed here; encode and
 * repair only). Test scaffolding (build/dmg/run_ecc/main) stays there.
 */
#include "pktcc.h"

static uint8_t gexp[512], glog[256];

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

void pktcc_init(void) {
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

void pktcc_parity(const uint8_t units[PKTCC_NP][PKTCC_PL],
                  uint8_t p[PKTCC_PL], uint8_t q[PKTCC_PL]) {
    for (int i = 0; i < PKTCC_PL; i++)
        p[i] = q[i] = 0;
    for (int u = 0; u < PKTCC_NP; u++) {
        uint8_t c = gexp[u];
        for (int i = 0; i < PKTCC_PL; i++) {
            p[i] ^= units[u][i];
            q[i] ^= gfm(c, units[u][i]);
        }
    }
}

void pktcc_ref(const uint8_t *unit, uint32_t ref[4]) {
    uint32_t a = 0, b = 0, c = 0, d = 0;
    for (int i = 0; i < PKTCC_PL; i++) {
        uint32_t v = unit[i], k = (uint32_t)i + 1;
        a += v;
        b += v * k;
        c += v * k * k;
        d += v * k * k * k;
    }
    ref[0] = a;
    ref[1] = b;
    ref[2] = c;
    ref[3] = d;
}

static void triple4(const uint8_t *p, uint32_t *s) {
    pktcc_ref(p, s);
}

int pktcc_sec(uint8_t *p, const uint32_t ref[4]) {
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
    if (q < 1 || q > PKTCC_PL)
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

int pktcc_repair_erase(uint8_t units[PKTCC_NP][PKTCC_PL],
                       const uint8_t p[PKTCC_PL], const uint8_t q[PKTCC_PL],
                       const int lost[PKTCC_NP]) {
    int L[2], nl = 0;
    for (int k = 0; k < PKTCC_NP && nl < 2; k++)
        if (lost[k])
            L[nl++] = k;
    if (nl == 0)
        return 0;
    if (nl == 1) {
        int a = L[0];
        for (int i = 0; i < PKTCC_PL; i++) {
            uint8_t v = p[i];
            for (int u = 0; u < PKTCC_NP; u++)
                if (u != a)
                    v ^= units[u][i];
            units[a][i] = v;
        }
    } else {
        int a = L[0], b = L[1];
        uint8_t ca = gexp[a], cb = gexp[b], den = ca ^ cb;
        for (int i = 0; i < PKTCC_PL; i++) {
            uint8_t pp = p[i], qq = q[i];
            for (int u = 0; u < PKTCC_NP; u++)
                if (u != a && u != b) {
                    pp ^= units[u][i];
                    qq ^= gfm(gexp[u], units[u][i]);
                }
            uint8_t ua = gf_div(qq ^ gfm(cb, pp), den);
            units[a][i] = ua;
            units[b][i] = pp ^ ua;
        }
    }
    return 0;
}
