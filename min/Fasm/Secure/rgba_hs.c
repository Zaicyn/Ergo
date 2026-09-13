/* rgba_hs.c -- C mirror of rgba_hs.asm (verification only).
 * TSV must match the asm exactly (compare with diff).
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define P 1543u
#define G 5u
#define NL 1536u
#define NU 4096u
#define NSL 1024u

static uint64_t sm64(uint64_t *s) {
    uint64_t z = (*s += 0x9E3779B97F4A7C15ull);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z ^ (z >> 31);
}
static uint32_t modpow(uint32_t b, uint32_t e) {
    uint32_t r = 1;
    while (e) {
        if (e & 1) r = (r * b) % P;
        b = (b * b) % P;
        e >>= 1;
    }
    return r;
}
static uint32_t priv_of(uint32_t color, uint32_t mag) {
    uint32_t lane = mag % NL;
    uint64_t seed = ((uint64_t)((color >> 24) & 0xFF) << 56) |
                    ((uint64_t)((color >> 16) & 0xFF) << 48) |
                    ((uint64_t)((color >> 8) & 0xFF) << 40) |
                    ((uint64_t)(color & 0xFF) << 32) | lane;
    seed ^= 0xA53C96F182736455ull;
    uint64_t s = seed;
    return 1 + (uint32_t)(sm64(&s) % (P - 1));
}
static uint64_t bond_key(uint32_t S, uint32_t pa, uint32_t pb,
                         uint32_t tier) {
    uint64_t s = ((uint64_t)S << 32) | pa;
    s ^= (uint64_t)pb * 0x9E3779B97F4A7C15ull;
    s ^= (uint64_t)tier * 0xBF58476D1CE4E5B9ull;
    s ^= 0x544945524B445946ull;
    return sm64(&s);
}
static void keystream(uint64_t K, uint8_t *ks, size_t n) {
    uint64_t s = K ^ 0x53545245414D5F5Full;
    for (size_t i = 0; i < n; i++)
        ks[i] = (uint8_t)(sm64(&s) & 0xFF);
}
static uint64_t tag_v0(uint64_t K, const uint8_t *ct, size_t n) {
    uint64_t h = K ^ 0x5441475F4B4559ull;
    for (size_t i = 0; i < n; i++) {
        uint64_t t = ct[i] + 0x9E3779B97F4A7C15ull + (h << 6) + (h >> 2) + i;
        h ^= t;
        if ((i & 63) == 63) {
            uint64_t s = h;
            h = sm64(&s);
        }
    }
    uint64_t s = h ^ (uint64_t)n;
    return sm64(&s);
}
static void build_unit(uint8_t *u, uint32_t color) {
    for (int c = 0; c < 4; c++) {
        uint8_t tint = (uint8_t)((color >> ((3 - c) * 8)) & 0xFF);
        for (int i = 0; i < (int)NSL; i++)
            u[c * NSL + i] =
                (uint8_t)(((i * 67 + 41 + c * 13) ^ tint ^ (i >> 3)) & 0xFF);
    }
}

static uint8_t pt[NU], ct[NU], dec[NU], ks[NU];
static int fails = 0;
#define CHECK(c) do { if (!(c)) fails++; } while (0)

int main(void) {
    uint32_t colA = 0xE23317C4u, colB = 0x4B9DF02Au;
    uint32_t a = priv_of(colA, 1101), b = priv_of(colB, 517);
    uint32_t pa = modpow(G, a), pb = modpow(G, b);
    printf("H 0 priv=%u pub=%u lane=%u\n", a, pa, 1101 % NL);
    printf("H 1 priv=%u pub=%u lane=%u\n", b, pb, 517 % NL);
    uint32_t Sa = modpow(pb, a), Sb = modpow(pa, b);
    CHECK(Sa == Sb);
    uint64_t Ka = bond_key(Sa, pa, pb, 0);
    uint64_t Kb = Ka;
    printf("B bond=%u key=%llu\n", Sa, (unsigned long long)Ka);
    /* dir 0 */
    build_unit(pt, colA);
    keystream(Ka, ks, NU);
    for (int i = 0; i < (int)NU; i++) ct[i] = pt[i] ^ ks[i];
    uint64_t t0 = tag_v0(Ka, ct, NU);
    unsigned v0 = tag_v0(Kb, ct, NU) == t0;
    CHECK(v0);
    keystream(Kb, ks, NU);
    for (int i = 0; i < (int)NU; i++) dec[i] = ct[i] ^ ks[i];
    unsigned e0 = !memcmp(pt, dec, NU);
    CHECK(e0);
    printf("E 0 tag=%llu verify=%u exact=%u\n", (unsigned long long)t0,
           v0, e0);
    /* tamper */
    uint64_t tb = tag_v0(Kb, ct, NU);
    ct[1234] ^= 0x01;
    unsigned tamp = tag_v0(Kb, ct, NU) != tb;
    CHECK(tamp);
    ct[1234] ^= 0x01;
    printf("T tamper=%u\n", tamp);
    /* attacker */
    uint32_t m = priv_of(0, 0);
    uint32_t Sm = modpow(pa, m);
    unsigned xd = Sm != Sa;
    CHECK(xd);
    uint64_t Km = bond_key(Sm, pa, pb, 99);
    keystream(Km, ks, NU);
    for (int i = 0; i < (int)NU; i++) dec[i] = ct[i] ^ ks[i];
    unsigned garb = !!memcmp(pt, dec, NU);
    CHECK(garb);
    unsigned tf = tag_v0(Km, ct, NU) != tb;
    CHECK(tf);
    printf("X bonddiff=%u garbage=%u tagfail=%u\n", xd, garb, tf);
    /* dir 1 */
    build_unit(pt, colB);
    keystream(Kb, ks, NU);
    for (int i = 0; i < (int)NU; i++) ct[i] = pt[i] ^ ks[i];
    uint64_t t1 = tag_v0(Kb, ct, NU);
    keystream(Ka, ks, NU);
    for (int i = 0; i < (int)NU; i++) dec[i] = ct[i] ^ ks[i];
    unsigned v1 = tag_v0(Ka, ct, NU) == t1;
    CHECK(v1);
    unsigned e1 = !memcmp(pt, dec, NU);
    CHECK(e1);
    printf("E 1 tag=%llu verify=%u exact=%u\n", (unsigned long long)t1,
           v1, e1);
    /* 4-tier disclosure over Alice unit */
    build_unit(pt, colA);
    uint64_t tags[4];
    for (int s = 0; s < 4; s++) {
        uint64_t K = bond_key(Sa, pa, pb, (uint32_t)s);
        keystream(K, ks, NSL);
        for (int i = 0; i < (int)NSL; i++)
            ct[s * NSL + i] = pt[s * NSL + i] ^ ks[i];
        tags[s] = tag_v0(K, ct + s * NSL, NSL);
    }
    uint64_t K0 = bond_key(Sa, pa, pb, 0);
    unsigned s0 = tag_v0(K0, ct, NSL) == tags[0];
    CHECK(s0);
    keystream(K0, ks, NSL);
    for (int i = 0; i < (int)NSL; i++) dec[i] = ct[i] ^ ks[i];
    unsigned de0 = !memcmp(pt, dec, NSL);
    CHECK(de0);
    uint64_t Kb2 = bond_key(Sa, pa, pb, 99);
    unsigned locked = 0;
    for (int s = 1; s < 4; s++) {
        if (tag_v0(Kb2, ct + s * NSL, NSL) != tags[s])
            locked++;
        else
            CHECK(0);
    }
    printf("D 0 slice0=%u exact=%u locked=%u\n", s0, de0, locked);
    unsigned allok = 1;
    for (int s = 0; s < 4; s++) {
        uint64_t K = bond_key(Sa, pa, pb, (uint32_t)s);
        if (tag_v0(K, ct + s * NSL, NSL) != tags[s]) {
            allok = 0;
            CHECK(0);
        }
        keystream(K, ks, NSL);
        for (int i = 0; i < (int)NSL; i++)
            dec[s * NSL + i] = ct[s * NSL + i] ^ ks[i];
    }
    unsigned dall = !memcmp(pt, dec, NU);
    CHECK(dall);
    printf("D 3 tags=%u exact=%u\n", allok, dall);
    printf("R %s\n", fails ? "FAIL" : "PASS");
    return fails != 0;
}
