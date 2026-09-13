/* tierbench.c -- tiered-handshake sizing: how many disclosure tiers can we
 * afford, and which tag construction earns its keep?
 *
 * Model (SecondLife/VRChat-style): strangers see only the "safe" variant
 * (tier 0); higher trust unlocks more tiers, up to the full 4096 B unit.
 * Trust tier t holds subkeys for slices 0..t; slice i key = KDF(bond,
 * tier=i, lanes). Slices are cumulative: tier t reveals the first t+1
 * slices.
 *
 * Experiment A -- tier scaling: T in {1,2,4,8,16,32,64} slices over a
 *   fixed 4096 B unit. Per slice: subkey KDF + keystream + encrypt + tag
 *   (sender) and tag-verify + decrypt (receiver). Reports ns/handshake
 *   and marginal ns/tier. Question: where is the knee?
 * Experiment B -- tag variants: V0 absorb-cheap/mix-per-64B (rgba_dh),
 *   V1 mix-per-16B, V2 mix-per-byte. Metrics: ns/4KB, avalanche (1-bit
 *   flip -> mean Hamming distance of 64-bit tag, ideal 32), tamper
 *   rejection over random 1..4-byte tampers.
 * Experiment C -- disclosure demo: 4 tiers <-> RGBA channels (tier0 = A
 *   presence/safe, +R, +G, +B). Trust-0 party recovers slice 0 exactly
 *   and fails everything above; trust-3 recovers all 4096 B.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define P 1543u
#define G 5u
#define NL 1536u
#define NU 4096u

static uint64_t sm64(uint64_t *s) {
    uint64_t z = (*s += 0x9E3779B97F4A7C15ull);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z ^ (z >> 31);
}
/* deterministic test RNG (xorshift64, fixed seed) */
static uint64_t trng = 0x123456789ABCDEF1ull;
static uint64_t trand(void) {
    trng ^= trng << 13;
    trng ^= trng >> 7;
    trng ^= trng << 17;
    return trng;
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
static uint64_t bond_key(uint32_t S, uint32_t pa, uint32_t pb,
                         uint32_t tier) {
    uint64_t s = ((uint64_t)S << 32) | pa;
    s ^= (uint64_t)pb * 0x9E3779B97F4A7C15ull;
    s ^= (uint64_t)tier * 0xBF58476D1CE4E5B9ull;
    s ^= 0x544945524B445946ull; /* "TIERKDF" */
    return sm64(&s);
}
static void keystream(uint64_t K, uint8_t *ks, size_t n) {
    uint64_t s = K ^ 0x53545245414D5F5Full;
    for (size_t i = 0; i < n; i++)
        ks[i] = (uint8_t)(sm64(&s) & 0xFF);
}
/* V0: absorb cheap, diffuse every 64 B */
static uint64_t tag_v0(uint64_t K, const uint8_t *ct, size_t n) {
    uint64_t h = K ^ 0x5441475F4B4559ull;
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
/* V1: diffuse every 16 B */
static uint64_t tag_v1(uint64_t K, const uint8_t *ct, size_t n) {
    uint64_t h = K ^ 0x5441475F56310ull;
    for (size_t i = 0; i < n; i++) {
        h ^= ct[i] + 0x9E3779B97F4A7C15ull + (h << 6) + (h >> 2) + i;
        if ((i & 15) == 15) {
            uint64_t s = h;
            h = sm64(&s);
        }
    }
    uint64_t s = h ^ (uint64_t)n;
    return sm64(&s);
}
/* V2: diffuse every byte */
static uint64_t tag_v2(uint64_t K, const uint8_t *ct, size_t n) {
    uint64_t h = K ^ 0x5441475F56320ull;
    for (size_t i = 0; i < n; i++) {
        h ^= ct[i] + 0x9E3779B97F4A7C15ull + (h << 6) + (h >> 2) + i;
        uint64_t s = h;
        h = sm64(&s);
    }
    uint64_t s = h ^ (uint64_t)n;
    return sm64(&s);
}
typedef uint64_t (*tagfn)(uint64_t, const uint8_t *, size_t);

static double now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}

static uint8_t pt[NU], ct[NU], dec[NU], ks[NU];

int main(void) {
    for (int i = 0; i < (int)NU; i++)
        pt[i] = (uint8_t)(((i * 67 + 41) ^ 0x3C ^ (i >> 3)) & 0xFF);
    /* fixed bond stand-in (handshake already proven in rgba_dh) */
    uint32_t S = modpow(modpow(G, 1213), 888);
    uint32_t pa = 191, pb = 1257;

    /* ---------- A: tier scaling (tag V1) ---------- */
    printf("A: tier scaling (sender+receiver, 4096 B total)\n");
    printf("%4s %12s %10s\n", "T", "ns/handshake", "ns/tier");
    const int Ts[] = { 1, 2, 4, 8, 16, 32, 64 };
    double prev_ns = 0;
    for (int ti = 0; ti < 7; ti++) {
        int T = Ts[ti], sl = NU / T, iters = 300;
        double t0 = now_ns();
        for (int it = 0; it < iters; it++) {
            for (int s = 0; s < T; s++) {
                uint64_t K = bond_key(S, pa, pb, (uint32_t)s);
                keystream(K, ks, (size_t)sl);
                for (int i = 0; i < sl; i++)
                    ct[s * sl + i] = pt[s * sl + i] ^ ks[i];
                volatile uint64_t tg = tag_v1(K, ct + s * sl, (size_t)sl);
                (void)tg;
            }
            for (int s = 0; s < T; s++) {
                uint64_t K = bond_key(S, pa, pb, (uint32_t)s);
                volatile uint64_t tg = tag_v1(K, ct + s * sl, (size_t)sl);
                (void)tg;
                keystream(K, ks, (size_t)sl);
                for (int i = 0; i < sl; i++)
                    dec[s * sl + i] = ct[s * sl + i] ^ ks[i];
            }
        }
        double ns = (now_ns() - t0) / iters;
        double per = ti ? (ns - prev_ns) / (T - Ts[ti - 1]) : ns;
        printf("%4d %12.0f %10.1f\n", T, ns, per);
        prev_ns = ns;
    }
    if (memcmp(pt, dec, NU))
        printf("A-VERIFY: FAIL\n");
    else
        printf("A-VERIFY: all tier counts round-trip exact\n");

    /* ---------- B: tag variants ---------- */
    printf("B: tag variants (4096 B)\n");
    printf("%4s %10s %10s %10s %10s\n", "tag", "ns/4KB",
           "avalanche", "rej1", "rej1-4");
    tagfn fns[3] = { tag_v0, tag_v1, tag_v2 };
    const char *nm[3] = { "V0", "V1", "V2" };
    for (int v = 0; v < 3; v++) {
        uint64_t K = bond_key(S, pa, pb, 7);
        double t0 = now_ns();
        const int itn = 300;
        for (int it = 0; it < itn; it++) {
            volatile uint64_t tg = fns[v](K, pt, NU);
            (void)tg;
        }
        double ns = (now_ns() - t0) / itn;
        /* avalanche: 200 single-bit flips, mean tag Hamming distance */
        double ham = 0;
        static uint8_t buf[NU];
        for (int t = 0; t < 200; t++) {
            memcpy(buf, pt, NU);
            int pos = (int)(trand() % NU), bit = (int)(trand() % 8);
            uint64_t h0 = fns[v](K, buf, NU);
            buf[pos] ^= (uint8_t)(1u << bit);
            uint64_t h1 = fns[v](K, buf, NU);
            ham += (double)__builtin_popcountll(h0 ^ h1);
        }
        /* rejection: 300x 1-byte + 300x 1..4-byte random tampers */
        int r1 = 0, r14 = 0;
        uint64_t base = fns[v](K, pt, NU);
        for (int t = 0; t < 300; t++) {
            memcpy(buf, pt, NU);
            buf[trand() % NU] ^= (uint8_t)(1 + trand() % 255);
            if (fns[v](K, buf, NU) != base) r1++;
        }
        for (int t = 0; t < 300; t++) {
            memcpy(buf, pt, NU);
            int nb = 1 + (int)(trand() % 4);
            for (int j = 0; j < nb; j++)
                buf[trand() % NU] ^= (uint8_t)(1 + trand() % 255);
            if (fns[v](K, buf, NU) != base) r14++;
        }
        printf("%4s %10.0f %10.2f %7d/300 %7d/300\n", nm[v], ns,
               ham / 200.0, r1, r14);
    }

    /* ---------- C: disclosure demo, 4 tiers <-> RGBA ---------- */
    printf("C: disclosure (4 tiers: 0=A/safe +R +G +B), 1024 B/slice\n");
    const int T4 = 4, sl4 = NU / T4;
    uint64_t tags[4];
    for (int s = 0; s < T4; s++) {
        uint64_t K = bond_key(S, pa, pb, (uint32_t)s);
        keystream(K, ks, (size_t)sl4);
        for (int i = 0; i < sl4; i++)
            ct[s * sl4 + i] = pt[s * sl4 + i] ^ ks[i];
        tags[s] = tag_v1(K, ct + s * sl4, (size_t)sl4);
    }
    /* trust-0 party: holds only slice-0 key */
    {
        uint64_t K0 = bond_key(S, pa, pb, 0);
        int ok0 = (tag_v1(K0, ct, (size_t)sl4) == tags[0]);
        keystream(K0, ks, (size_t)sl4);
        for (int i = 0; i < sl4; i++) dec[i] = ct[i] ^ ks[i];
        int match0 = !memcmp(pt, dec, (size_t)sl4);
        /* slices 1..3 without keys: attacker-guess must fail */
        uint64_t Kbad = bond_key(S, pa, pb, 99);
        int rej = 0;
        for (int s = 1; s < T4; s++)
            if (tag_v1(Kbad, ct + s * sl4, (size_t)sl4) != tags[s])
                rej++;
        printf("trust0: slice0 tag %s, bytes %s; upper slices locked %d/3\n",
               ok0 ? "PASS" : "FAIL", match0 ? "EXACT" : "GARBAGE", rej);
    }
    /* trust-3 party: all keys, full unit */
    {
        int allok = 1;
        for (int s = 0; s < T4; s++) {
            uint64_t K = bond_key(S, pa, pb, (uint32_t)s);
            if (tag_v1(K, ct + s * sl4, (size_t)sl4) != tags[s]) allok = 0;
            keystream(K, ks, (size_t)sl4);
            for (int i = 0; i < sl4; i++)
                dec[s * sl4 + i] = ct[s * sl4 + i] ^ ks[i];
        }
        printf("trust3: all tags %s, full 4096 B %s\n",
               allok ? "PASS" : "FAIL",
               memcmp(pt, dec, NU) ? "GARBAGE" : "EXACT");
    }
    return 0;
}
