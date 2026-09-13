/* rgba_dh.c -- quick prototype: RGBA secret-color handshake between two
 * 4096 B units, bond becomes the transient session key (agree + encrypt).
 *
 * Locked-in reading of the RGBA proposal (toy scale, upgrade path noted):
 * - Unit = 4096 B viewed as RGBA: 4 channels x 1024 B.
 * - Secret per party: color = 4 bytes (R,G,B,A, one per channel) +
 *   magnitude m in [0,1535] (S=1536 coalesced lanes; lane domain-
 *   separates the KDF so GPU lanes stay coalesced).
 * - Modified-DH, standard shape: toy group p=1543 ("15xx" prime),
 *   g=5 (verified primitive, order 1542 = 2*3*257). Private scalar
 *   x = 1 + splitmix64(color||mag) mod (p-1). Public = g^x mod p.
 *   Bond S = g^{ab} mod p, must agree on both sides.
 * - Bond -> transient key K = splitmix64(S||pubA||pubB||colors||lanes);
 *   keystream = splitmix stream from K (4096 B); ct = pt XOR ks;
 *   tag = 8-byte keyed splitmix-stream hash over ct.
 * - Upgrade path for real use: swap (p,g) for RFC 3526 1536-bit MODP
 *   (the "1.5k" group), splitmix-KDF -> HKDF-SHA256, XOR stream ->
 *   AES-GCM/ChaCha20-Poly1305. The handshake SHAPE stays identical.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define P 1543u
#define G 5u
#define NL 1536u          /* coalesced lanes */
#define NU 4096u
#define NCH 1024u

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
/* private scalar from secret color + magnitude lane */
static uint32_t priv_of(uint8_t R, uint8_t Gr, uint8_t B, uint8_t A,
                        uint32_t mag) {
    uint64_t seed = ((uint64_t)R << 56) | ((uint64_t)Gr << 48) |
                    ((uint64_t)B << 40) | ((uint64_t)A << 32) |
                    (uint64_t)(mag % NL);
    seed ^= 0xA53C96F182736455ull;
    uint64_t s = seed;
    return 1 + (uint32_t)(sm64(&s) % (P - 1));
}
/* bond -> transient 64-bit key, domain-separated by lanes + colors */
static uint64_t bond_key(uint32_t S, uint32_t pa, uint32_t pb,
                         uint32_t colA, uint32_t colB,
                         uint32_t la, uint32_t lb) {
    uint64_t s = ((uint64_t)S << 32) | pa;
    s ^= (uint64_t)pb * 0x9E3779B97F4A7C15ull;
    s ^= (uint64_t)colA << 17;
    s ^= (uint64_t)colB << 41;
    s ^= ((uint64_t)la * NL + lb) * 0xBF58476D1CE4E5B9ull;
    s ^= 0x5452414E5349414Eull; /* "TRANSIAN" */
    return sm64(&s);
}
static void keystream(uint64_t K, uint8_t *ks, size_t n) {
    uint64_t s = K ^ 0x53545245414D5F5Full; /* "STREAM__" */
    for (size_t i = 0; i < n; i++)
        ks[i] = (uint8_t)(sm64(&s) & 0xFF);
}
/* keyed 8-byte tag over ciphertext */
static uint64_t tag_of(uint64_t K, const uint8_t *ct, size_t n) {
    uint64_t h = K ^ 0x5441475F4B4559ull; /* "TAG_KEY" */
    for (size_t i = 0; i < n; i++) {
        h ^= ct[i] + 0x9E3779B97F4A7C15ull + (h << 6) + (h >> 2) + i;
        if ((i & 63) == 63) {
            uint64_t s = h;
            h = sm64(&s);
        }
    }
    uint64_t s = h ^ (uint64_t)n;
    return sm64(&s);
}
static void build_unit(uint8_t *u, uint8_t r, uint8_t g, uint8_t b,
                       uint8_t a) {
    /* RGBA: channel c (each 1024 B) tinted by its secret byte + index */
    const uint8_t tint[4] = { r, g, b, a };
    for (int c = 0; c < 4; c++)
        for (int i = 0; i < (int)NCH; i++)
            u[c * NCH + i] =
                (uint8_t)(((i * 67 + 41 + c * 13) ^ tint[c] ^ (i >> 3)) & 0xFF);
}

static int fails = 0;
#define CHECK(cond, msg) do { \
    if (cond) printf("ok   %s\n", msg); \
    else { printf("FAIL %s\n", msg); fails++; } } while (0)

int main(void) {
    /* --- secrets: Alice color+mag, Bob color+mag --- */
    uint8_t aR = 0xE2, aG = 0x33, aB = 0x17, aA = 0xC4;
    uint32_t amag = 1024 + 77;             /* lane 1101 of 1536 */
    uint8_t bR = 0x4B, bG = 0x9D, bB = 0xF0, bA = 0x2A;
    uint32_t bmag = 512 + 5;               /* lane 517 of 1536 */
    uint32_t colA = ((uint32_t)aR << 24) | ((uint32_t)aG << 16) |
                    ((uint32_t)aB << 8) | aA;
    uint32_t colB = ((uint32_t)bR << 24) | ((uint32_t)bG << 16) |
                    ((uint32_t)bB << 8) | bA;

    uint32_t a = priv_of(aR, aG, aB, aA, amag);
    uint32_t b = priv_of(bR, bG, bB, bA, bmag);
    uint32_t pa = modpow(G, a), pb = modpow(G, b);
    printf("A priv=%u pub=%u lane=%u\n", a, pa, amag % NL);
    printf("B priv=%u pub=%u lane=%u\n", b, pb, bmag % NL);

    /* --- handshake: bond computed independently on both sides --- */
    uint32_t Sa = modpow(pb, a);           /* Alice: pubB^a */
    uint32_t Sb = modpow(pa, b);           /* Bob:   pubA^b */
    CHECK(Sa == Sb, "bond agreement (g^ab both sides)");
    printf("bond S=%u\n", Sa);
    uint64_t Ka = bond_key(Sa, pa, pb, colA, colB, amag % NL, bmag % NL);
    uint64_t Kb = bond_key(Sb, pa, pb, colA, colB, amag % NL, bmag % NL);
    CHECK(Ka == Kb, "transient key agreement");

    /* --- Alice encrypts her 4096 B RGBA unit to Bob --- */
    static uint8_t pt[NU], ct[NU], dec[NU], ks[NU];
    build_unit(pt, aR, aG, aB, aA);
    keystream(Ka, ks, NU);
    for (int i = 0; i < (int)NU; i++) ct[i] = pt[i] ^ ks[i];
    uint64_t tag = tag_of(Ka, ct, NU);
    printf("tag=%016llX\n", (unsigned long long)tag);

    /* Bob verifies + decrypts */
    CHECK(tag_of(Kb, ct, NU) == tag, "tag verifies on Bob side");
    keystream(Kb, ks, NU);
    for (int i = 0; i < (int)NU; i++) dec[i] = ct[i] ^ ks[i];
    CHECK(!memcmp(pt, dec, NU), "round-trip byte-identical 4096 B");

    /* tamper: flip one ciphertext byte -> tag must reject */
    ct[1234] ^= 0x01;
    CHECK(tag_of(Kb, ct, NU) != tag, "1-byte tamper rejected");
    ct[1234] ^= 0x01; /* restore */

    /* wrong secret: Mallory (different color) derives another bond */
    uint32_t m = priv_of(0x00, 0x00, 0x00, 0x00, 0);
    uint32_t Sm = modpow(pa, m);
    CHECK(Sm != Sa, "attacker bond differs");
    uint64_t Km = bond_key(Sm, pa, pb, 0, colB, 0, bmag % NL);
    keystream(Km, ks, NU);
    for (int i = 0; i < (int)NU; i++) dec[i] = ct[i] ^ ks[i];
    CHECK(memcmp(pt, dec, NU) != 0, "attacker decrypt is garbage");
    CHECK(tag_of(Km, ct, NU) != tag, "attacker tag fails");

    /* both directions: Bob -> Alice works too */
    build_unit(pt, bR, bG, bB, bA);
    keystream(Kb, ks, NU);
    for (int i = 0; i < (int)NU; i++) ct[i] = pt[i] ^ ks[i];
    tag = tag_of(Kb, ct, NU);
    keystream(Ka, ks, NU);
    for (int i = 0; i < (int)NU; i++) dec[i] = ct[i] ^ ks[i];
    CHECK(tag_of(Ka, ct, NU) == tag && !memcmp(pt, dec, NU),
          "Bob->Alice direction round-trips");

    printf(fails ? "RESULT: %d FAILURES\n" : "RESULT: ALL PASS\n", fails);
    return fails != 0;
}
