/* ergo_math_kernels.h — owned transcendental kernels for Ergo codegen.
 *
 * Kernel standard (Spec/Ergo_Hardware_Op_Map.md §2): fixed-coefficient
 * polynomials (Chebyshev fits generated and validated by
 * tests/math_kernels/gen_coeffs.py against mpmath; exp/log f64 use the
 * classic fdlibm/msun formulations validated the same way), explicit
 * fma()/fmaf() at every contraction point (identical bits under gcc and
 * clang regardless of -ffp-contract), documented argument reduction per
 * kernel, and a measured ulp bound vs an arbitrary-precision reference
 * (tests/math_kernels/ulp_check.py) recorded below.
 *
 * Determinism: integer/bit manipulation is exact; polynomial evaluation
 * is explicit-fma; no libm calls anywhere in the owned path (sqrt used
 * by pow(x, 1/2) lowers to the IEEE-exact hardware sqrtsd); no
 * data-dependent CPU paths beyond the x86-64-v3 baseline (no ifunc, no
 * AVX-512). Same bits every run, every recipe-conforming machine.
 *
 * Measured ulp bounds (vs mpmath 800-bit reference, sweep +
 * domain-edge cases, gcc 16.1.1 / clang 22.1.8 — bit-identical between
 * compilers over every sweep below; tests/math_kernels/RESULTS.md):
 *   f64:  sin <= 2   cos <= 2   exp <= 1   log <= 1   atan2 <= 1   pow <= 1
 *   f32:  sin <= 1   cos <= 1   exp <= 1   log <= 1   atan2 <= 2   pow <= 1
 * (ulp = ulp of the correctly-rounded result; ~653k cases per side,
 * including denormals, ±0, ±Inf, NaN, huge trig arguments through the
 * Payne-Hanek path, near-multiples of pi/2, log near 1.0, and exp
 * denormal-output edges.)
 *
 * Speed context (this machine, scalar calls, recipe flags): owned
 * sin/cos/exp/atan2 run 9.7-14.0 ns vs glibc 10.2-17.2; owned log
 * 14.0 vs glibc 6.3; owned pow 107 ns vs glibc 22.8 (was ~534 with
 * both series fully in dd; the poly-with-dd-head split — dd for the
 * leading terms, plain-f64 Horner tails over exact coefficients —
 * holds the same measured 1-ulp bound; see RESULTS.md).
 *
 * Fallback: define ERGO_MATH_LIBM (or compile with --libm-fallback,
 * which emits libm calls directly) to map every symbol back to the host
 * libm. The fallback breaks cross-libc bit-identity (op map §2) and is
 * announced at build time by the driver.
 */

#ifndef ERGO_MATH_KERNELS_H
#define ERGO_MATH_KERNELS_H

#include <stdint.h>
#include <string.h>
#include <math.h>

#ifdef ERGO_MATH_LIBM

#define _ergo_sin   sin
#define _ergo_cos   cos
#define _ergo_exp   exp
#define _ergo_log   log
#define _ergo_pow   pow
#define _ergo_atan2 atan2
#define _ergo_sinf   sinf
#define _ergo_cosf   cosf
#define _ergo_expf   expf
#define _ergo_logf   logf
#define _ergo_powf   powf
#define _ergo_atan2f atan2f

#else /* owned kernels */

/* ---- bit helpers (memcpy: strict-aliasing clean, compiles to nothing) */
static inline double _ed2b(uint64_t u) { double d; memcpy(&d, &u, 8); return d; }
static inline uint64_t _eb2d(double d) { uint64_t u; memcpy(&u, &d, 8); return u; }
static inline float _ef2b(uint32_t u) { float f; memcpy(&f, &u, 4); return f; }
static inline uint32_t _eb2f(float f) { uint32_t u; memcpy(&u, &f, 4); return u; }

/* round to nearest integer (ties-to-even), |x| < 2^51, no libm:
 * the 1.5*2^52 magic-number trick under default rounding */
static inline double _erint64(double x) {
    const double m = 0x1.8p+52;
    double t = x + m;
    return t - m;
}
static inline float _erint32(float x) {
    const float m = 0x1.8p+23f;
    float t = x + m;
    return t - m;
}

/* 2^n scaling by exponent-field arithmetic, n in [-2098, 1024]:
 * two-step above 1023 (only n = 1024 occurs: from exp near the
 * overflow boundary — the second multiply gets the IEEE overflow
 * rounding right, i.e. Inf exactly when the true value exceeds
 * DBL_MAX + half a final ulp); two-step below n = -1021 so denormal
 * results come out exact */
static inline double _escalbn64(double x, int n) {
    if (n > 1023)
        return (x * 0x1.0p+512) * 0x1.0p+512;
    if (n >= -1021) {
        return x * _ed2b((uint64_t)(n + 1023) << 52);
    }
    return x * _ed2b((uint64_t)(n + 1000 + 1023) << 52) * 0x1.0p-1000;
}
static inline float _escalbn32(float x, int n) {
    if (n > 127)
        return (x * 0x1.0p+64f) * 0x1.0p+64f;   /* n == 128 only */
    if (n >= -125) {
        return x * _ef2b((uint32_t)(n + 127) << 23);
    }
    return x * _ef2b((uint32_t)(n + 24 + 127) << 23) * 0x1.0p-24f;
}

/* ================================================================
 * EXP (f64)
 * Reduction: k = rint(x*log2e), r = x - k*ln2 (2-word fma Cody-Waite),
 * |r| <= ln2/2.  Kernel: fdlibm formulation
 *   c = r - t*P(t), t = r^2;  exp(r) = 1 - ((r*c/(c-2)) - r)
 * validated at 3.4e-19 sup rel error in exact arithmetic
 * (tests/math_kernels/gen_coeffs.py log).  Scale: 2^k bit arithmetic.
 * Domain: NaN->NaN, +Inf->+Inf, -Inf->+0; overflow to +Inf above
 * 0x1.62e42fefa39efp+9 (709.78), underflow to +0 below -745.1332
 * (denormal results in between via two-step scaling).
 * ================================================================ */
static inline double _ergo_exp(double x) {
    uint64_t u = _eb2d(x);
    uint64_t au = u & 0x7fffffffffffffffULL;
    if (au > 0x7ff0000000000000ULL) return x + x;      /* NaN */
    if (u == 0x7ff0000000000000ULL) return x;          /* +Inf */
    if (u == 0xfff0000000000000ULL) return 0.0;        /* -Inf */
    double kd = _erint64(x * 0x1.71547652b82fep+0);    /* log2e */
    if (kd >= 1025.0) return _ed2b(0x7ff0000000000000ULL);
    if (kd <= -1076.0) return 0.0;                     /* result < 2^-1075 */
    int k = (int)kd;
    double r = fma(-kd, 0x1.62e42fee00000p-1, x);      /* ln2_hi */
    r = fma(-kd, 0x1.a39ef35793c76p-33, r);            /* ln2_lo */
    double t = r * r;
    /* fdlibm P1..P5 (verified numerically against their decimal
     * values — see tests/math_kernels/) */
    double p = fma(0x1.6376972bea4d0p-25, t, -0x1.bbd41c5d26bf1p-20);
    p = fma(p, t, 0x1.1566aaf25de2cp-14);              /* P3 */
    p = fma(p, t, -0x1.6c16c16bebd93p-9);              /* P2 */
    p = fma(p, t, 0x1.555555555553ep-3);               /* P1 */
    double c = fma(-t, p, r);                        /* r - t*P(t), fused */
    double res = 1.0 - ((r * c) / (c - 2.0) - r);
    return _escalbn64(res, k);
}

/* ================================================================
 * LOG (f64)
 * Reduction: x = 2^k * m, m in [sqrt(2)/2, sqrt(2)) (denormal inputs
 * pre-scaled by 2^64).  f = m-1 (exact), s = f/(2+f), z = s^2,
 * log(m) = 2s(1 + z*L(z)) in the fdlibm assembly
 *   log = k*ln2_hi - ((hfsq - (s*(hfsq + 2z*L(z)) + k*ln2_lo)) - f)
 * with L a degree-7 Chebyshev fit (gen_coeffs.py, sup residual 1.0e-18).
 * Domain: x<0 -> NaN, ±0 -> -Inf, +Inf -> +Inf, NaN -> NaN; tiny-|f|
 * path for m near 1 (log(1+f) = f - f^2/2 + f^3/3 to <2^-60).
 * ================================================================ */
static inline double _ergo_log(double x) {
    uint64_t u = _eb2d(x);
    uint64_t au = u & 0x7fffffffffffffffULL;
    if (au > 0x7ff0000000000000ULL) return x + x;      /* NaN */
    if (u == 0x7ff0000000000000ULL) return x;          /* +Inf */
    if (au == 0) return _ed2b(0xfff0000000000000ULL);  /* ±0 -> -Inf */
    if (u >> 63) return _ed2b(0x7ff8000000000000ULL);  /* negative -> NaN */
    int k = 0;
    if (u < 0x0010000000000000ULL) {                   /* denormal input */
        x *= 0x1.0p+64;
        k = -64;
        u = _eb2d(x);
    }
    k += (int)(u >> 52) - 1023;
    double m = _ed2b((u & 0x000fffffffffffffULL) | 0x3ff0000000000000ULL);
    /* m is in [1,2); halve above sqrt(2) so m lands in [sqrt2/2, sqrt2)
     * and f = m-1 stays within [-0.293, +0.4143) */
    if (m >= 0x1.6a09e667f3bcdp+0) {                   /* sqrt(2) */
        m *= 0.5;
        k += 1;
    }
    double f = m - 1.0;
    double dk = (double)k;
    if (f == 0.0)
        return fma(dk, 0x1.62e42fee00000p-1, dk * 0x1.a39ef35793c76p-33);
    if (f > -0x1.0p-20 && f < 0x1.0p-20) {             /* log(1+f) */
        double R = f * f * fma(-0x1.5555555555555p-2, f, 0.5);
        return fma(dk, 0x1.62e42fee00000p-1,
                   fma(dk, 0x1.a39ef35793c76p-33, -R) + f);
    }
    double s = f / (2.0 + f);
    double z = s * s;
    /* 2*L(z): coefficients 2/(2n+3) — Chebyshev fit (gen_coeffs.py) */
    double L = fma(0x1.0c03dba686983p-4, z, 0x1.0fbe8ed93e21fp-4);
    L = fma(L, z, 0x1.3b1c35a98d753p-4);
    L = fma(L, z, 0x1.745cf902c7644p-4);
    L = fma(L, z, 0x1.c71c72015e8f8p-4);
    L = fma(L, z, 0x1.2492492476c86p-3);
    L = fma(L, z, 0x1.9999999999a38p-3);
    L = fma(L, z, 0x1.5555555555555p-2);
    double R = 2.0 * (z * L);
    double hfsq = 0.5 * (f * f);
    double sr = fma(s, hfsq + R, dk * 0x1.a39ef35793c76p-33);
    return fma(dk, 0x1.62e42fee00000p-1, -((hfsq - sr) - f));
}

/* ================================================================
 * SIN / COS (f64)
 * Reduction: three paths, all deterministic.
 *   |x| < 2^-27 (sin) / 2^-26 (cos): identity, exactly rounded.
 *   |x| <= 0x1.8p+20 (1.57e6): k = rint(x*2/pi), fma Cody-Waite with a
 *     3-word round-to-nearest split of pi/2 (residual 2^-163; error
 *     <= 2^20 * 2^-110 = 2^-90 per reduction — far below ulp(r)).
 *   larger |x|: Payne-Hanek (below) — exact windowed extraction of
 *     x*(2/pi) against a 1440-bit table of 2/pi; no magnitude limit
 *     short of the f64 format itself.
 * Kernels: sin(r) = r + r^3*P(r^2), cos(r) = 1 - z/2 + z^2*C(z),
 * Chebyshev fits (gen_coeffs.py), sup residual 1.2e-20 / 1.3e-18 on
 * the coefficient function.  cos uses the fdlibm qx tail trick for
 * |r| > 0.3.
 * Domain: NaN -> NaN, ±Inf -> NaN.  f64 bits of the quadrant k are
 * exact everywhere (k mod 4 from the fixed-point window).
 * ================================================================ */
/* pi/2 as a 3-word round-to-nearest split (w0+w1+w2, resid ~2^-163) */
#define _ERG_PIO2_HI  0x1.921fb54442d18p+0
#define _ERG_PIO2_MID 0x1.1a62633145c07p-54
#define _ERG_PIO2_LO  (-0x1.f1976b7ed8fbcp-110)
#define _ERG_TWO_OVER_PI 0x1.45f306dc9c883p-1

static inline double _erg_ksin64(double r) {
    double z = r * r, v = z * r;
    double p = fma(-0x1.ab17d3a88ed82p-41, z, 0x1.61217f0ac6fc1p-33);
    p = fma(p, z, -0x1.ae645412c4435p-26);
    p = fma(p, z, 0x1.71de3a546094ep-19);
    p = fma(p, z, -0x1.a01a01a019938p-13);
    p = fma(p, z, 0x1.1111111111110p-7);
    return fma(v, fma(z, p, -0x1.5555555555555p-3), r);
}
static inline double _erg_kcos64(double r) {
    double z = r * r;
    double q = fma(-0x1.907da3138d5b8p-37, z, 0x1.1eeb68e8acbf7p-29);
    q = fma(q, z, -0x1.27e4fa17d959ep-22);
    q = fma(q, z, 0x1.a01a019f4eaf5p-16);
    q = fma(q, z, -0x1.6c16c16c16967p-10);
    q = fma(q, z, 0x1.5555555555555p-5);
    double zz = z * q;
    uint64_t au = _eb2d(r) & 0x7fffffffffffffffULL;
    if (au < 0x3fd3333333333333ULL)              /* |r| < 0.3 */
        return 1.0 - fma(-z, zz, 0.5 * z);     /* 1 - (0.5z - z^2*C(z)) */
    double qx;
    if (au > 0x3fe9000000000000ULL)              /* |r| > 0.78125 */
        qx = 0.28125;
    else
        qx = _ed2b(au & 0xfffffffff8000000ULL);  /* 5-bit head of |r| */
    double hz = 0.5 * z - qx;
    double a = 1.0 - qx;
    double t1 = fma(-z, zz, hz);                 /* hz - z^2*C(z), fused */
    return a - t1;
}

/* Payne-Hanek for |x| > 0x1.8p+20: y = x*(2/pi) computed in a
 * 256-bit fixed-point window over the 24-bit limbs of 2/pi below.
 * Window [i_lo, i_lo+7]: limbs above i_lo contribute only integer
 * multiples of 4 to y (their least significant bit is >= 2^2), so
 * k mod 4 and the top 192 fraction bits of y are exact.  Uses
 * unsigned __int128 partial products (gcc/clang, identical integer
 * semantics on x86-64; integer arithmetic is exactly defined). */
static const uint32_t _erg_two_over_pi[60] = {
    0xa2f983u, 0x6e4e44u, 0x1529fcu, 0x2757d1u, 0xf534ddu, 0xc0db62u,
    0x95993cu, 0x439041u, 0xfe5163u, 0xabdebbu, 0xc561b7u, 0x246e3au,
    0x424dd2u, 0xe00649u, 0x2eea09u, 0xd1921cu, 0xfe1debu, 0x1cb129u,
    0xa73ee8u, 0x8235f5u, 0x2ebb44u, 0x84e99cu, 0x7026b4u, 0x5f7e41u,
    0x3991d6u, 0x398353u, 0x39f49cu, 0x845f8bu, 0xbdf928u, 0x3b1ff8u,
    0x97ffdeu, 0x05980fu, 0xef2f11u, 0x8b5a0au, 0x6d1f6du, 0x367ecfu,
    0x27cb09u, 0xb74f46u, 0x3f669eu, 0x5fea2du, 0x7527bau, 0xc7ebe5u,
    0xf17b3du, 0x0739f7u, 0x8a5292u, 0xea6bfbu, 0x5fb11fu, 0x8d5d08u,
    0x560330u, 0x46fc7bu, 0x6babf0u, 0xcfbc20u, 0x9af436u, 0x1da9e3u,
    0x91615eu, 0xe61b08u, 0x659985u, 0x5f14a0u, 0x68408du, 0xffd880u,
};

static inline int _erg_ph_reduce(double ax, double *rp) {
    uint64_t u = _eb2d(ax);
    int e = (int)(u >> 52) - 1023;        /* ax = m * 2^(e-52) */
    uint64_t m = (u & 0x000fffffffffffffULL) | 0x0010000000000000ULL;
    int i_lo = (e > 77) ? (e - 77 + 23) / 24 : 0;
    int i_hi = i_lo + 8;                  /* 9 limbs: F >= 215 always, so
                                           * all three fraction windows
                                           * exist (F >= 192 required) */
    int F = 24 * i_hi + 76 - e;           /* y_window = A * 2^-F */
    /* accumulator has a 3-limb zero pad at the bottom so the fraction
     * windows below F never index below acc[0]. */
    uint64_t acc[10] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    for (int i = i_lo; i <= i_hi; i++) {
        unsigned __int128 p = (unsigned __int128)m * _erg_two_over_pi[i];
        int s = 24 * (i_hi - i);
        int limb = 3 + (s >> 6), off = s & 63;
        uint64_t plo = (uint64_t)p, phi = (uint64_t)(p >> 64);
        uint64_t v0, v1, v2;
        if (off == 0) {
            v0 = plo; v1 = phi; v2 = 0;
        } else {
            v0 = plo << off;
            v1 = (plo >> (64 - off)) | (phi << off);
            v2 = phi >> (64 - off);
        }
        uint64_t t = acc[limb] + v0;
        int c = (t < acc[limb]);
        acc[limb] = t;
        t = acc[limb + 1] + v1;
        int c1 = (t < acc[limb + 1]);
        acc[limb + 1] = t + c;
        c1 = c1 | (acc[limb + 1] < t);
        t = acc[limb + 2] + v2 + c1;
        int c2 = (t < acc[limb + 2]) | (c1 & (t == acc[limb + 2]));
        acc[limb + 2] = t;
        acc[limb + 3] += c2;
    }
    /* A = acc (starting at limb 3).  k mod 4 = bits F..F+1 of A;
     * round bit = F-1; fraction = bits below F. */
    int wl = (F >> 6) + 3, wo = F & 63;
    uint64_t above;          /* bits F..F+63 */
    uint64_t fr0, fr1, fr2;  /* three 64-bit fraction windows below F */
    if (wo == 0) {
        above = acc[wl];
        fr0 = acc[wl - 1]; fr1 = acc[wl - 2]; fr2 = acc[wl - 3];
    } else {
        above = (acc[wl] >> wo) | (acc[wl + 1] << (64 - wo));
        fr0 = (acc[wl - 1] >> wo) | (acc[wl] << (64 - wo));
        fr1 = (acc[wl - 2] >> wo) | (acc[wl - 1] << (64 - wo));
        fr2 = (acc[wl - 3] >> wo) | (acc[wl - 2] << (64 - wo));
    }
    int k = (int)(above & 3);
    /* sticky: any fraction bits below the fr2 window (truncated);
     * only used to keep the complement honest — the truncation itself
     * is 2^-192 of y, far below the kernel budget */
    uint64_t sticky = 0;
    for (int j = 0; j < wl - 3; j++) sticky |= acc[j];
    if (wo) sticky |= (acc[wl - 3] & ((1ULL << wo) - 1));
    int neg;
    uint64_t g0, g1, g2;
    if (fr0 >> 63) {          /* round bit set: remainder is negative */
        k += 1;
        neg = 1;
        g0 = ~fr0; g1 = ~fr1; g2 = ~fr2;
        if (!sticky) { g0 += 1; if (g0 == 0) { g1 += 1; if (g1 == 0) g2 += 1; } }
    } else {
        neg = 0;
        g0 = fr0; g1 = fr1; g2 = fr2;
    }
    /* f = ±(g0:g1:g2) * 2^-192, |f| <= 1/2; convert each 64-bit window
     * (RNE per word; total error <= 2^-54 relative) */
    double f0 = (double)g0 * 0x1.0p-64;
    double f1 = (double)g1 * 0x1.0p-128;
    double f2 = (double)g2 * 0x1.0p-192;
    /* r = f * (pi/2), fma-folded against the 3-word split */
    double hi = f0 * _ERG_PIO2_HI;
    double lo = fma(f0, _ERG_PIO2_HI, -hi);
    lo = fma(f1, _ERG_PIO2_HI, lo);
    lo = fma(f0, _ERG_PIO2_MID, lo);
    lo = fma(f2, _ERG_PIO2_HI, lo);
    lo = fma(f0, _ERG_PIO2_LO, lo);
    double r = hi + lo;
    *rp = neg ? -r : r;
    return k & 3;
}

/* shared reduction: ax = |x| > 0, finite.  Returns k (mod-4 quadrant
 * in low bits) and *rp = remainder in [-pi/4, pi/4].  Also used by the
 * f32 large-argument path (f32 inputs promote to f64 exactly). */
/* Payne-Hanek variant for F32-SOURCED arguments (|x| > 0x1.8p+20):
 * identical to _erg_ph_reduce except the 128-bit products become
 * 64-bit: an f32-sourced mantissa has <= 24 significant bits, so
 * m*limb <= 2^48 fits u64 exactly and the high product word is
 * identically zero.  Output is bit-identical to _erg_ph_reduce on every
 * f32-sourced input (exact integer arithmetic is unique).  This is the
 * form that ports 1:1 to GLSL (uint64) and SPIR-V (Int64) for the
 * three-way f32 trig contract (2026-09-04) — no 128-bit type needed. */
static inline int _erg_ph_reduce32(double ax, double *rp) {
    uint64_t u = _eb2d(ax);
    /* f32-sourced double: its 53-bit f64 mantissa field is the 24-bit
     * f32 mantissa left-justified by 29 bits.  Right-justify it and
     * compensate the exponent: ax = m23 * 2^(e'-52) with m23 < 2^24,
     * so m23*limb <= 2^48 fits u64 exactly (high word identically
     * zero) — this is what makes the __int128 unnecessary. */
    int e = (int)(u >> 52) - 1023 + 29;
    uint64_t m = ((u & 0x000fffffffffffffULL) | 0x0010000000000000ULL) >> 29;
    int i_lo = (e > 77) ? (e - 77 + 23) / 24 : 0;
    int i_hi = i_lo + 8;
    int F = 24 * i_hi + 76 - e;
    uint64_t acc[10] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    for (int i = i_lo; i <= i_hi; i++) {
        uint64_t p = m * _erg_two_over_pi[i];   /* exact: <= 2^48 */
        int s = 24 * (i_hi - i);
        int limb = 3 + (s >> 6), off = s & 63;
        uint64_t plo = p;                       /* high word is zero */
        uint64_t v0, v1;
        if (off == 0) {
            v0 = plo; v1 = 0;
        } else {
            v0 = plo << off;
            v1 = plo >> (64 - off);
        }
        uint64_t t = acc[limb] + v0;
        int c = (t < acc[limb]);
        acc[limb] = t;
        t = acc[limb + 1] + v1;
        int c1 = (t < acc[limb + 1]);
        acc[limb + 1] = t + c;
        c1 = c1 | (acc[limb + 1] < t);
        t = acc[limb + 2] + c1;                 /* v2 == 0 for f32 m */
        int c2 = (t < acc[limb + 2]) | (c1 & (t == acc[limb + 2]));
        acc[limb + 2] = t;
        acc[limb + 3] += c2;
    }
    int wl = (F >> 6) + 3, wo = F & 63;
    uint64_t above;
    uint64_t fr0, fr1, fr2;
    if (wo == 0) {
        above = acc[wl];
        fr0 = acc[wl - 1]; fr1 = acc[wl - 2]; fr2 = acc[wl - 3];
    } else {
        above = (acc[wl] >> wo) | (acc[wl + 1] << (64 - wo));
        fr0 = (acc[wl - 1] >> wo) | (acc[wl] << (64 - wo));
        fr1 = (acc[wl - 2] >> wo) | (acc[wl - 1] << (64 - wo));
        fr2 = (acc[wl - 3] >> wo) | (acc[wl - 2] << (64 - wo));
    }
    int k = (int)(above & 3);
    uint64_t sticky = 0;
    for (int j = 0; j < wl - 3; j++) sticky |= acc[j];
    if (wo) sticky |= (acc[wl - 3] & ((1ULL << wo) - 1));
    int neg;
    uint64_t g0, g1, g2;
    if (fr0 >> 63) {
        k += 1;
        neg = 1;
        g0 = ~fr0; g1 = ~fr1; g2 = ~fr2;
        if (!sticky) { g0 += 1; if (g0 == 0) { g1 += 1; if (g1 == 0) g2 += 1; } }
    } else {
        neg = 0;
        g0 = fr0; g1 = fr1; g2 = fr2;
    }
    double f0 = (double)g0 * 0x1.0p-64;
    double f1 = (double)g1 * 0x1.0p-128;
    double f2 = (double)g2 * 0x1.0p-192;
    double hi = f0 * _ERG_PIO2_HI;
    double lo = fma(f0, _ERG_PIO2_HI, -hi);
    lo = fma(f1, _ERG_PIO2_HI, lo);
    lo = fma(f0, _ERG_PIO2_MID, lo);
    lo = fma(f2, _ERG_PIO2_HI, lo);
    lo = fma(f0, _ERG_PIO2_LO, lo);
    double r = hi + lo;
    *rp = neg ? -r : r;
    return k & 3;
}

static inline int _erg_remod64(double ax, double *rp) {
    if (ax <= 0x1.8p+20) {                             /* 1.57e6 */
        double kd = _erint64(ax * _ERG_TWO_OVER_PI);
        double r = fma(-kd, _ERG_PIO2_HI, ax);
        r = fma(-kd, _ERG_PIO2_MID, r);
        r = fma(-kd, _ERG_PIO2_LO, r);
        *rp = r;
        return (int)kd;
    }
    return _erg_ph_reduce(ax, rp);
}

static inline double _ergo_sin(double x) {
    uint64_t u = _eb2d(x);
    uint64_t au = u & 0x7fffffffffffffffULL;
    if (au >= 0x7ff0000000000000ULL) return x - x;     /* NaN/Inf -> NaN */
    if (au < 0x3e40000000000000ULL) return x;          /* |x| < 2^-27 */
    double r;
    int k = _erg_remod64(_ed2b(au), &r);
    double v;
    switch (k & 3) {
    case 0:  v = _erg_ksin64(r);  break;
    case 1:  v = _erg_kcos64(r);  break;
    case 2:  v = -_erg_ksin64(r); break;
    default: v = -_erg_kcos64(r); break;
    }
    return (u >> 63) ? -v : v;
}

static inline double _ergo_cos(double x) {
    uint64_t u = _eb2d(x);
    uint64_t au = u & 0x7fffffffffffffffULL;
    if (au >= 0x7ff0000000000000ULL) return x - x;     /* NaN/Inf -> NaN */
    if (au < 0x3e50000000000000ULL) return 1.0;        /* |x| < 2^-26 */
    double r;
    int k = _erg_remod64(_ed2b(au), &r);
    switch (k & 3) {
    case 0:  return _erg_kcos64(r);
    case 1:  return -_erg_ksin64(r);
    case 2:  return -_erg_kcos64(r);
    default: return _erg_ksin64(r);
    }
}

/* ================================================================
 * ATAN2 (f64)
 * Core atan on z >= 0, fdlibm 4-breakpoint reduction
 * (7/16, 11/16, 19/16, 39/16) with an exact 53-bit atan table, then
 * atan(t) = t + t^3*A(t^2), degree-10 Chebyshev fit (sup residual
 * 9.7e-17 on A).  atan2 assembly per C99 Annex F: zero/Inf/NaN table,
 * ratio guards at 2^60 (t underflow -> z=0; overflow -> z=pi/2),
 * quadrant restore with the pi_hi/pi_lo split.
 * ================================================================ */
static inline double _erg_atan64_core(double z) {
    /* z >= 0, finite */
    if (z < 0x1.0p-27) return z;                       /* atan z = z */
    static const double athi[5] = {
        0.0,
        0x1.dac670561bb4fp-2,   /* atan(0.5) hi */
        0x1.921fb54442d18p-1,   /* atan(1)   hi */
        0x1.f730bd281f69bp-1,   /* atan(1.5) hi */
        0x1.921fb54442d18p+0,   /* pi/2      hi */
    };
    static const double atlo[5] = {
        0.0,
        0x1.a2b7f222f65e2p-56,
        0x1.1a62633145c07p-55,
        0x1.007887af0cbbdp-56,
        0x1.1a62633145c07p-54,
    };
    double at, al, t;
    if (z < 0.4375) { at = 0.0; al = 0.0; t = z; }
    else if (z < 0.6875) {
        at = athi[1]; al = atlo[1];
        t = (z - 0.5) / fma(0.5, z, 1.0);
    } else if (z < 1.1875) {
        at = athi[2]; al = atlo[2];
        t = (z - 1.0) / (z + 1.0);
    } else if (z < 2.4375) {
        at = athi[3]; al = atlo[3];
        t = (z - 1.5) / fma(1.5, z, 1.0);
    } else {
        at = athi[4]; al = atlo[4];
        t = -1.0 / z;
    }
    double z2 = t * t;
    double q = fma(-0x1.1f7e155a43eb3p-6, z2, 0x1.35dd0ddcf833fp-5);
    q = fma(q, z2, -0x1.9c615abcb6137p-5);
    q = fma(q, z2, 0x1.df0ba843fc834p-5);
    q = fma(q, z2, -0x1.10ed20717a226p-4);
    q = fma(q, z2, 0x1.3b1161b7acb63p-4);
    q = fma(q, z2, -0x1.745cff647bca7p-4);
    q = fma(q, z2, 0x1.c71c7136677d7p-4);
    q = fma(q, z2, -0x1.24924923b090cp-3);
    q = fma(q, z2, 0x1.9999999998861p-3);
    q = fma(q, z2, -0x1.5555555555554p-2);
    double cor = (t * z2) * q;                 /* atan(t) - t */
    if (at == 0.0)
        return t + cor;
    return at - ((-cor - al) - t);             /* at + al + atan(t) */
}

static inline double _ergo_atan2(double y, double x) {
    uint64_t uy = _eb2d(y), ux = _eb2d(x);
    uint64_t ay = uy & 0x7fffffffffffffffULL;
    uint64_t ax = ux & 0x7fffffffffffffffULL;
    if (ay > 0x7ff0000000000000ULL || ax > 0x7ff0000000000000ULL)
        return x + y;                                    /* NaN */
    if (ax == 0x7ff0000000000000ULL) {                   /* x = ±Inf */
        if (ay == 0x7ff0000000000000ULL) {               /* y = ±Inf */
            double v = (ux >> 63) ? 0x1.2d97c7f3321d2p+1  /* 3pi/4 */
                                  : 0x1.921fb54442d18p-1; /* pi/4   */
            return (uy >> 63) ? -v : v;
        }
        double v = (ux >> 63) ? 0x1.921fb54442d18p+1 : 0.0;  /* pi : 0 */
        return (uy >> 63) ? -v : v;
    }
    if (ay == 0x7ff0000000000000ULL)                     /* y = ±Inf */
        return (uy >> 63) ? -0x1.921fb54442d18p+0 : 0x1.921fb54442d18p+0;
    if (ax == 0) {                                       /* x = ±0 */
        if (ay == 0) {                                   /* atan2(±0,±0) */
            double v = (ux >> 63) ? 0x1.921fb54442d18p+1 : 0.0;
            return (uy >> 63) ? -v : v;
        }
        return (uy >> 63) ? -0x1.921fb54442d18p+0 : 0x1.921fb54442d18p+0;
    }
    if (ay == 0) {                                       /* y = ±0 */
        double v = (ux >> 63) ? 0x1.921fb54442d18p+1 : 0.0;
        return (uy >> 63) ? -v : v;
    }
    double fay = _ed2b(ay), fax = _ed2b(ax);
    double t = fay / fax;
    double z;
    if (_eb2d(t) >= 0x7ff0000000000000ULL)             /* ratio = +Inf */
        z = 0x1.921fb54442d18p+0 + 0x1.1a62633145c07p-54;  /* pi/2 */
    else
        z = _erg_atan64_core(t);       /* t = 0 -> z = 0: correct */
    if (!(ux >> 63))                                     /* x > 0 */
        return (uy >> 63) ? -z : z;
    /* x < 0: pi - z with the pi_hi/pi_lo split (fdlibm order) */
    if (!(uy >> 63))
        return 0x1.921fb54442d18p+1 - (z - 0x1.1a62633145c07p-53);
    return (z - 0x1.1a62633145c07p-53) - 0x1.921fb54442d18p+1;
}

/* ================================================================
 * POW (f64) — double-double heads, polynomial tails
 *   x^y = sign * 2^(y * log2|x|).  log2 and exp2 carry their leading
 *   terms as (hi, lo) double-double pairs (exact TwoSum/TwoProd via
 *   fma residuals) and their series tails as plain-f64 Horners over the
 *   exact 1/(2n+1) / 1/n! coefficient tables below — the SLEEF-style
 *   poly-with-dd-head structure.  (The first version ran BOTH series
 *   entirely in dd: 22+24 dd terms, ~430-530 ns/call.  The split
 *   keeps the same measured bound — pow max 1 ulp over 234k cases,
 *   incl. a 200k-case extended stress — at ~107 ns/call.)
 * Special cases per C99 Annex F: integer-exponent fast paths
 * (y = 1 -> x, y = 2 -> x*x exactly, y = -1 -> 1/x, y = 0.5 ->
 * sqrt(x)); x < 0 with non-integer y -> NaN; the full zero/Inf/NaN
 * table.  The last ulp at the overflow/underflow boundary comes from
 * IEEE rounding of the final scaling, not from a hard-coded threshold.
 * ================================================================ */
/* TwoSum / TwoProd: exact error-free transformations */
static inline void _dd2_sum(double a, double b, double *hi, double *lo) {
    double s = a + b;
    double bp = s - a;
    *hi = s;
    *lo = (a - (s - bp)) + (b - bp);
}
static inline void _dd2_prod(double a, double b, double *hi, double *lo) {
    double p = a * b;
    *hi = p;
    *lo = fma(a, b, -p);
}
/* dd + dd -> dd (renormalized) */
static inline void _dd_add(double ah, double al, double bh, double bl,
                           double *h, double *l) {
    double sh, sl;
    _dd2_sum(ah, bh, &sh, &sl);
    sl += al + bl;
    _dd2_sum(sh, sl, h, l);
}
/* dd * dd -> dd */
static inline void _dd_mul(double ah, double al, double bh, double bl,
                           double *h, double *l) {
    double ph, pl;
    _dd2_prod(ah, bh, &ph, &pl);
    pl = fma(ah, bl, fma(al, bh, pl));
    _dd2_sum(ph, pl, h, l);
}

/* 1/(2n+1), n = 1..24, hi/lo f64 pairs (gen_coeffs.py) */
static const double _erg_rcp_odd[25][2] = {
    {0.0, 0.0},
    {0x1.5555555555555p-2, 0x1.5555555555555p-56},   /* /3 */
    {0x1.999999999999ap-3, -0x1.999999999999ap-57},  /* /5 */
    {0x1.2492492492492p-3, 0x1.2492492492492p-57},   /* /7 */
    {0x1.c71c71c71c71cp-4, 0x1.c71c71c71c71cp-58},   /* /9 */
    {0x1.745d1745d1746p-4, -0x1.745d1745d1746p-59},  /* /11 */
    {0x1.3b13b13b13b14p-4, -0x1.3b13b13b13b14p-58},  /* /13 */
    {0x1.1111111111111p-4, 0x1.1111111111111p-60},   /* /15 */
    {0x1.e1e1e1e1e1e1ep-5, 0x1.e1e1e1e1e1e1ep-61},   /* /17 */
    {0x1.af286bca1af28p-5, 0x1.af286bca1af28p-59},   /* /19 */
    {0x1.8618618618618p-5, 0x1.8618618618618p-59},   /* /21 */
    {0x1.642c8590b2164p-5, 0x1.642c8590b2164p-60},   /* /23 */
    {0x1.47ae147ae147bp-5, -0x1.eb851eb851eb8p-61},  /* /25 */
    {0x1.2f684bda12f68p-5, 0x1.2f684bda12f68p-59},   /* /27 */
    {0x1.1a7b9611a7b96p-5, 0x1.1a7b9611a7b96p-61},   /* /29 */
    {0x1.0842108421084p-5, 0x1.0842108421084p-60},   /* /31 */
    {0x1.f07c1f07c1f08p-6, -0x1.f07c1f07c1f08p-61},  /* /33 */
    {0x1.d41d41d41d41dp-6, 0x1.0750750750750p-60},   /* /35 */
    {0x1.bacf914c1bad0p-6, -0x1.bacf914c1bad0p-60},  /* /37 */
    {0x1.a41a41a41a41ap-6, 0x1.0690690690690p-60},   /* /39 */
    {0x1.8f9c18f9c18fap-6, -0x1.f3831f3831f38p-61},  /* /41 */
    {0x1.7d05f417d05f4p-6, 0x1.7d05f417d05f4p-62},   /* /43 */
    {0x1.6c16c16c16c17p-6, -0x1.f49f49f49f49fp-61},  /* /45 */
    {0x1.5c9882b931057p-6, 0x1.310572620ae4cp-61},   /* /47 */
    {0x1.4e5e0a72f0539p-6, 0x1.e0a72f0539783p-60},   /* /49 */
};
/* 1/n!, n = 2..26, hi/lo f64 pairs */
static const double _erg_rcp_fact[27][2] = {
    {0.0, 0.0}, {0.0, 0.0},
    {0x1.0000000000000p-1, 0x0.0p+0},                /* 2! */
    {0x1.5555555555555p-3, 0x1.5555555555555p-57},   /* 3! */
    {0x1.5555555555555p-5, 0x1.5555555555555p-59},   /* 4! */
    {0x1.1111111111111p-7, 0x1.1111111111111p-63},   /* 5! */
    {0x1.6c16c16c16c17p-10, -0x1.f49f49f49f49fp-65}, /* 6! */
    {0x1.a01a01a01a01ap-13, 0x1.a01a01a01a01ap-73},  /* 7! */
    {0x1.a01a01a01a01ap-16, 0x1.a01a01a01a01ap-76},  /* 8! */
    {0x1.71de3a556c734p-19, -0x1.c154f8ddc6c00p-73}, /* 9! */
    {0x1.27e4fb7789f5cp-22, 0x1.cbbc05b4fa99ap-76}, /* 10! */
    {0x1.ae64567f544e4p-26, -0x1.c062e06d1f209p-80},/* 11! */
    {0x1.1eed8eff8d898p-29, -0x1.2aec959e14c06p-83},/* 12! */
    {0x1.6124613a86d09p-33, 0x1.f28e0cc748ebep-87}, /* 13! */
    {0x1.93974a8c07c9dp-37, 0x1.05d6f8a2efd1fp-92}, /* 14! */
    {0x1.ae7f3e733b81fp-41, 0x1.1d8656b0ee8cbp-97}, /* 15! */
    {0x1.ae7f3e733b81fp-45, 0x1.1d8656b0ee8cbp-101},/* 16! */
    {0x1.952c77030ad4ap-49, 0x1.ac981465ddc6cp-103},/* 17! */
    {0x1.6827863b97d97p-53, 0x1.eec01221a8b0bp-107},/* 18! */
    {0x1.2f49b46814157p-57, 0x1.2650f61dbdcb4p-112},/* 19! */
    {0x1.e542ba4020225p-62, 0x1.ea72b4afe3c2fp-120},/* 20! */
    {0x1.71b8ef6dcf572p-66, -0x1.d043ae40c4647p-120},/* 21! */
    {0x1.0ce396db7f853p-70, -0x1.aebcdbd20331cp-124},/* 22! */
    {0x1.761b41316381ap-75, -0x1.3423c7d91404fp-130},/* 23! */
    {0x1.f2cf01972f578p-80, -0x1.9ada5fcc1ab14p-135},/* 24! */
    {0x1.3f3ccdd165fa9p-84, -0x1.58ddadf344487p-139},/* 25! */
    {0x1.88e85fc6a4e5ap-89, -0x1.71c37ebd16540p-143},/* 26! */
};

#define _ERG_LN2_HI    0x1.62e42fefa39efp-1
#define _ERG_LN2_LO    0x1.abc9e3b39803fp-56
#define _ERG_INVLN2_HI 0x1.71547652b82fep+0
#define _ERG_INVLN2_LO 0x1.777d0ffda0d24p-56

/* log2(x) as dd, x > 0 finite (denormal pre-scaled by 2^64).
 * Structure (SLEEF-style poly-with-dd-head): the series
 *   L = sum_{n>=0} z^n/(2n+1),  z = s^2, s = (m-1)/(m+1) dd
 * is summed with the first 4 terms (through z^3/7) in dd and the
 * remaining tail z^4*(1/9 + z/11 + ...) as a plain-f64 Horner over
 * the exact 1/(2n+1) coefficients.  The tail is <= z^4/9 <= 8.3e-8,
 * so its f64 rounding contributes ~1e-22 absolute to L — the dd head
 * only needs to carry the big terms.  Total log2 error ~2^-85
 * absolute (measured bound at the pow level is what counts; see
 * RESULTS.md). */
static inline void _erg_log2_dd(double x, double *hp, double *lp) {
    uint64_t u = _eb2d(x);
    int e = 0;
    if (u < 0x0010000000000000ULL) {
        x *= 0x1.0p+64;
        u = _eb2d(x);
        e = -64;
    }
    e += (int)(u >> 52) - 1023;
    double m = _ed2b((u & 0x000fffffffffffffULL) | 0x3ff0000000000000ULL);
    if (m >= 0x1.6a09e667f3bcdp+0) {                   /* sqrt(2) */
        m *= 0.5;
        e += 1;
    }
    double f = m - 1.0;                                /* exact */
    /* d = 2 + f in dd (TwoSum is exact), then s = f/d as a dd
     * division — a plain f64 divide here would cap the whole dd chain
     * at 2^-54 */
    double dh, dl;
    _dd2_sum(2.0, f, &dh, &dl);
    double s = f / dh;
    double sres = fma(-s, dh, f);                      /* division residual */
    double sl = fma(-s, dl, sres) / dh;
    double zh, zl;
    _dd_mul(s, sl, s, sl, &zh, &zl);                   /* z = s^2 dd */
    /* head: 1 + z/3 + z^2/5 + z^3/7 in dd */
    double sh = 1.0, sl2 = 0.0;
    double th = zh, tl = zl;                           /* term z^1 */
    for (int n = 1; n <= 3; n++) {
        double t2h, t2l;
        _dd_mul(th, tl, _erg_rcp_odd[n][0], _erg_rcp_odd[n][1],
                &t2h, &t2l);
        _dd_add(sh, sl2, t2h, t2l, &sh, &sl2);
        _dd_mul(th, tl, zh, zl, &th, &tl);
    }
    /* th,tl now hold z^4.  Tail: sum_{n=4..17} z^(n-4)/(2n+1) in
     * plain f64 (Horner over the exact 1/(2n+1) hi words);
     * truncation at n=18 is ~2e-30, f64 rounding ~1e-22 absolute. */
    double pt = _erg_rcp_odd[17][0];
    for (int n = 16; n >= 4; n--)
        pt = fma(pt, zh, _erg_rcp_odd[n][0]);
    double tail = (th + tl) * pt;                      /* z^4 * P(z) */
    _dd_add(sh, sl2, tail, 0.0, &sh, &sl2);
    /* log(m) = 2s * L (dd) */
    double lh, ll;
    _dd_mul(sh, sl2, 2.0 * s, 2.0 * sl, &lh, &ll);
    /* log2(x) = log(m)/ln2 + e = L * invln2 + e (dd) */
    double qh, ql;
    _dd_mul(lh, ll, _ERG_INVLN2_HI, _ERG_INVLN2_LO, &qh, &ql);
    _dd_add(qh, ql, (double)e, 0.0, hp, lp);
}

/* 2^t for dd t = th+tl, |t| < ~1075; returns f64 (denormal-safe).
 * Same structure: u = f*ln2 in dd (f = t - rint(t) dd), then
 * 2^f = 1 + u + u^2/2 in dd plus the tail u^3*(1/3! + u/4! + ...)
 * as plain-f64 Horner over exact 1/n! coefficients.  Tail omission
 * beyond 1/14! is ~1e-19 relative to the result; f64 tail rounding
 * ~1e-17 absolute — well under the 0.5-ulp final rounding. */
static inline double _erg_exp2_dd(double th, double tl) {
    double nd = _erint64(th);
    int n = (int)nd;
    double fh = th - nd;                               /* exact */
    double fh2, fl2;
    _dd2_sum(fh, tl, &fh2, &fl2);                      /* f in [-0.5, 0.5] */
    double uh, ul;
    _dd_mul(fh2, fl2, _ERG_LN2_HI, _ERG_LN2_LO, &uh, &ul);  /* u = f*ln2 */
    /* head: 1 + u + u^2/2 in dd */
    double sh, sl;
    _dd_add(1.0, 0.0, uh, ul, &sh, &sl);
    double u2h, u2l;
    _dd_mul(uh, ul, uh, ul, &u2h, &u2l);
    double t2h, t2l;
    _dd_mul(u2h, u2l, 0.5, 0.0, &t2h, &t2l);           /* u^2/2 */
    _dd_add(sh, sl, t2h, t2l, &sh, &sl);
    /* tail: u^3 * sum_{i=0..11} u^i/(i+3)!, plain f64 Horner */
    double pt = _erg_rcp_fact[14][0];
    for (int i = 13; i >= 3; i--)
        pt = fma(pt, uh, _erg_rcp_fact[i][0]);
    double u3 = (u2h + u2l) * uh;
    double rl = fma(u3, pt, sl);
    double rh = _escalbn64(sh, n);
    return rh + _escalbn64(rl, n);
}

static inline double _ergo_pow(double x, double y) {
    uint64_t ux = _eb2d(x), uy = _eb2d(y);
    uint64_t ax = ux & 0x7fffffffffffffffULL;
    uint64_t ay = uy & 0x7fffffffffffffffULL;
    /* NaN and Annex F dispatch */
    if (ay == 0) return 1.0;                           /* pow(x, ±0) = 1 */
    if (ax > 0x7ff0000000000000ULL) return x + y;      /* x NaN */
    if (ay > 0x7ff0000000000000ULL)                    /* y NaN */
        return (ux == 0x3ff0000000000000ULL) ? 1.0 : x + y;
    if (ux == 0x3ff0000000000000ULL) return 1.0;       /* x == 1, any y */
    /* y integer analysis (|y| >= 2^52 is an even integer) */
    int y_int = 0, y_odd = 0;
    if (ay < 0x4330000000000000ULL) {                  /* |y| < 2^52 */
        double yr = _erint64(y);
        if (yr == y) {
            y_int = 1;
            int64_t yk = (int64_t)yr;
            y_odd = (int)(yk & 1);
        }
    } else {
        y_int = 1;                                     /* huge: even */
    }
    /* x = ±0 (before the fast paths: pow(-0, 0.5) = +0 etc.) */
    if (ax == 0) {
        if ((int64_t)uy > 0)                           /* y > 0 */
            return (y_odd && (ux >> 63)) ? -0.0 : 0.0;
        /* y < 0 -> +Inf, or -Inf for -0 and odd integer y */
        return (y_odd && (ux >> 63))
            ? -_ed2b(0x7ff0000000000000ULL)
            : _ed2b(0x7ff0000000000000ULL);
    }
    /* x = ±Inf */
    if (ax == 0x7ff0000000000000ULL) {
        double base = ((int64_t)uy > 0) ? _ed2b(0x7ff0000000000000ULL) : 0.0;
        if ((ux >> 63) && y_odd)                       /* -Inf, odd y */
            return ((int64_t)uy > 0) ? -_ed2b(0x7ff0000000000000ULL) : -0.0;
        return base;
    }
    /* fast exact paths (x finite, nonzero here) */
    if (y == 1.0) return x;
    if (y == 2.0) return x * x;
    if (y == -1.0) return 1.0 / x;
    if (y == 0.5) {
        if ((int64_t)ux < 0) return _ed2b(0x7ff8000000000000ULL);
        return sqrt(x);                                /* hardware, exact */
    }
    /* x < 0 finite: non-integer y -> NaN; integer y -> sign */
    int sign = 0;
    if (ux >> 63) {
        if (!y_int) return _ed2b(0x7ff8000000000000ULL);
        sign = y_odd;
    }
    /* y = ±Inf */
    if (ay == 0x7ff0000000000000ULL) {
        if (ax == 0x3ff0000000000000ULL) return 1.0;   /* |x| == 1 */
        int big = ax > 0x3ff0000000000000ULL;          /* |x| > 1 */
        int pos = !((int64_t)uy >> 63);                /* y = +Inf */
        return (big == pos) ? _ed2b(0x7ff0000000000000ULL) : 0.0;
    }
    /* general: |x|^y = 2^(y * log2|x|) in double-double */
    double h, l;
    _erg_log2_dd(_ed2b(ax), &h, &l);
    double th, tl;
    _dd2_prod(y, h, &th, &tl);
    tl = fma(y, l, tl);
    /* overflow/underflow: boundary ulp via the final scaling */
    if (th >= 1024.0) {
        double inf = _ed2b(0x7ff0000000000000ULL);
        return sign ? -inf : inf;
    }
    if (th <= -1075.0) return sign ? -0.0 : 0.0;
    double r = _erg_exp2_dd(th, tl);
    return sign ? -r : r;
}

/* ================================================================
 * f32 set.  Same algorithms at single precision: f32 polynomials
 * evaluated with fmaf (never f64-then-truncate — Part 9.10's spirit:
 * deliberate precision choices).  Trig large-argument path promotes
 * to f64 for the reduction only (exact widening), then evaluates the
 * f32 polynomial on the f64-remainder narrowed once (RNE) — the
 * f64 reduction error is ~2^-90, invisible at f32.
 * ================================================================ */

/* ---- EXP (f32) ----
 * k = rint(x*log2e), r = x - k*ln2 with the 16-trailing-zero f32
 * ln2_hi (k*hi exact) + lo tail; kernel P(r) deg-5 Chebyshev fit
 * (gen_coeffs.py sup residual 1.4e-9 on (exp r - 1 - r)/r^2);
 * exp = 1 + r + r^2*P(r).  Overflow +Inf for k >= 129; +0 for
 * k <= -151; denormal outputs via two-step scaling. */
static inline float _ergo_expf(float x) {
    uint32_t u = _eb2f(x);
    uint32_t au = u & 0x7fffffffU;
    if (au > 0x7f800000U) return x + x;          /* NaN */
    if (u == 0x7f800000U) return x;              /* +Inf */
    if (u == 0xff800000U) return 0.0f;           /* -Inf */
    float kd = _erint32(x * 0x1.7154760000000p+0f);   /* log2e */
    if (kd >= 129.0f) return _ef2b(0x7f800000U);
    if (kd <= -151.0f) return 0.0f;
    int k = (int)kd;
    float r = fmaf(-kd, 0x1.62e3000000000p-1f, x);    /* ln2_hi */
    r = fmaf(-kd, 0x1.2fefa40000000p-17f, r);         /* ln2_lo */
    float z = r * r;
    float p = fmaf(0x1.a124e40000000p-13f, r, 0x1.6d43160000000p-10f);
    p = fmaf(p, r, 0x1.1110e00000000p-7f);
    p = fmaf(p, r, 0x1.5554ea0000000p-5f);
    p = fmaf(p, r, 0x1.5555560000000p-3f);
    p = fmaf(p, r, 0x1.0000000000000p-1f);
    float res = fmaf(z, p, 1.0f + r);
    return _escalbn32(res, k);
}

/* ---- LOG (f32) ----
 * Same structure as f64: x = 2^k*m, m in [sqrt2/2, sqrt2),
 * log(m) = 2s(1 + z*L(z)) with deg-3 Chebyshev L (residual 5.8e-10),
 * fdlibm assembly order.  ln2 split hi has 16 trailing zero bits so
 * k*hi is exact. */
static inline float _ergo_logf(float x) {
    uint32_t u = _eb2f(x);
    uint32_t au = u & 0x7fffffffU;
    if (au > 0x7f800000U) return x + x;          /* NaN */
    if (u == 0x7f800000U) return x;              /* +Inf */
    if (au == 0) return _ef2b(0xff800000U);      /* ±0 -> -Inf */
    if (u >> 31) return _ef2b(0x7fc00000U);      /* negative -> NaN */
    int k = 0;
    if (u < 0x00800000U) {                       /* denormal input */
        x *= 0x1.0p+64f;
        k = -64;
        u = _eb2f(x);
    }
    k += (int)(u >> 23) - 127;
    float m = _ef2b((u & 0x007fffffU) | 0x3f800000U);
    if (m >= 0x1.6a09e60000000p+0f) {            /* sqrt(2) */
        m *= 0.5f;
        k += 1;
    }
    float f = m - 1.0f;
    float dk = (float)k;
    if (f == 0.0f)
        return fmaf(dk, 0x1.62e3000000000p-1f, dk * 0x1.2fefa40000000p-17f);
    if (f > -0x1.0p-13f && f < 0x1.0p-13f) {     /* log(1+f) */
        float R = f * f * fmaf(-0x1.5555560000000p-2f, f, 0.5f);
        return fmaf(dk, 0x1.62e3000000000p-1f,
                    fmaf(dk, 0x1.2fefa40000000p-17f, -R) + f);
    }
    float s = f / (2.0f + f);
    float z = s * s;
    float L = fmaf(0x1.ddcf0a0000000p-4f, z, 0x1.245c420000000p-3f);
    L = fmaf(L, z, 0x1.9999ec0000000p-3f);
    L = fmaf(L, z, 0x1.5555560000000p-2f);
    float R = 2.0f * (z * L);
    float hfsq = 0.5f * (f * f);
    float sr = fmaf(s, hfsq + R, dk * 0x1.2fefa40000000p-17f);
    return fmaf(dk, 0x1.62e3000000000p-1f, -((hfsq - sr) - f));
}

/* ---- SIN / COS (f32) ----
 * |x| <= 6400: k = rint(x*2/pi), 3-word f32 Cody-Waite on pi/2
 * (residual 1.1e-23; k <= 4071, reduction error <= 4.5e-20, far under
 * f32 ulp).  Larger |x|: promote to f64, run the f64 reduction
 * (medium or Payne-Hanek), narrow the remainder once (RNE). */
static inline float _erg_ksin32(float r) {
    float z = r * r, v = z * r;
    float p = fmaf(0x1.6dbe080000000p-19f, z, -0x1.a013a80000000p-13f);
    p = fmaf(p, z, 0x1.11110e0000000p-7f);
    return fmaf(v, fmaf(z, p, -0x1.5555560000000p-3f), r);
}
static inline float _erg_kcos32(float r) {
    float z = r * r;
    float q = fmaf(-0x1.25244e0000000p-22f, z, 0x1.a015c40000000p-16f);
    q = fmaf(q, z, -0x1.6c16c00000000p-10f);
    q = fmaf(q, z, 0x1.5555560000000p-5f);
    float zz = z * q;
    return 1.0f - fmaf(-z, zz, 0.5f * z);    /* 1 - (0.5z - z^2*C(z)) */
}
static inline int _erg_remod32(float ax, float *rp) {
    if (ax <= 6400.0f) {
        /* kd via EXPLICITLY-fused magic-number rint: fma(ax, 2/pi, m) - m.
         * Written fused so the result cannot depend on -ffp-contract:
         * the driver's -O3 -ffp-contract=fast build contracts the plain
         * mul-add to exactly this (verified 2026-09-04: unfused source
         * flips kd by 1 where ax*2/pi sits on a double-rounding
         * boundary).  GLSL/SPIR-V ports emit the same explicit fma. */
        float kd = fmaf(ax, 0x1.45f3060000000p-1f, 0x1.8p+23f) - 0x1.8p+23f;
        float r = fmaf(-kd, 0x1.921fb60000000p+0f, ax);
        r = fmaf(-kd, -0x1.777a5c0000000p-25f, r);
        r = fmaf(-kd, -0x1.ee59da0000000p-50f, r);
        *rp = r;
        return (int)kd;
    }
    double r64;
    int k;
    double ax64 = (double)ax;
    if (ax64 <= 0x1.8p+20) {
        /* medium path, identical to _erg_remod64's first branch except
         * the kd rint is explicitly fused (same reason as tier 1) */
        double kd = fma(ax64, _ERG_TWO_OVER_PI, 0x1.8p+52) - 0x1.8p+52;
        double r = fma(-kd, _ERG_PIO2_HI, ax64);
        r = fma(-kd, _ERG_PIO2_MID, r);
        r = fma(-kd, _ERG_PIO2_LO, r);
        r64 = r;
        k = (int)kd;
    } else {
        /* u64-only PH for f32-sourced args — bit-identical output to
         * _erg_remod64's __int128 path (exact integer arithmetic is
         * unique); this is the form ported to GLSL/SPIR-V (2026-09-04) */
        k = _erg_ph_reduce32(ax64, &r64);
    }
    *rp = (float)r64;
    return k;
}
static inline float _ergo_sinf(float x) {
    uint32_t u = _eb2f(x);
    uint32_t au = u & 0x7fffffffU;
    if (au >= 0x7f800000U) return x - x;       /* NaN/Inf -> NaN */
    if (au < 0x39800000U) return x;            /* |x| < 2^-12 */
    float r;
    int k = _erg_remod32(_ef2b(au), &r);
    float v;
    switch (k & 3) {
    case 0:  v = _erg_ksin32(r);  break;
    case 1:  v = _erg_kcos32(r);  break;
    case 2:  v = -_erg_ksin32(r); break;
    default: v = -_erg_kcos32(r); break;
    }
    return (u >> 31) ? -v : v;
}
static inline float _ergo_cosf(float x) {
    uint32_t u = _eb2f(x);
    uint32_t au = u & 0x7fffffffU;
    if (au >= 0x7f800000U) return x - x;       /* NaN/Inf -> NaN */
    if (au < 0x39800000U) return 1.0f;         /* |x| < 2^-12 */
    float r;
    int k = _erg_remod32(_ef2b(au), &r);
    switch (k & 3) {
    case 0:  return _erg_kcos32(r);
    case 1:  return -_erg_ksin32(r);
    case 2:  return -_erg_kcos32(r);
    default: return _erg_ksin32(r);
    }
}

/* ---- ATAN2 (f32) ----
 * Core atan on z >= 0, Cephes 2-breakpoint reduction (tan(pi/8),
 * tan(3pi/8)); atan(t) = t + t^3*A(t^2), deg-4 Chebyshev fit
 * (residual 1.6e-8 on A).  Annex F special table as f64. */
static inline float _erg_atan32_core(float z) {
    if (z < 0x1.0p-12f) return z;
    float at, t;
    if (z > 0x1.3504f40000000p+1f) {           /* tan(3pi/8) */
        at = 0x1.921fb60000000p+0f;            /* pi/2 */
        t = -1.0f / z;
    } else if (z > 0x1.a8279a0000000p-2f) {    /* tan(pi/8) */
        at = 0x1.921fb60000000p-1f;            /* pi/4 */
        t = (z - 1.0f) / (z + 1.0f);
    } else {
        at = 0.0f;
        t = z;
    }
    float z2 = t * t;
    float q = fmaf(-0x1.08453c0000000p-4f, z2, 0x1.b810240000000p-4f);
    q = fmaf(q, z2, -0x1.2420340000000p-3f);
    q = fmaf(q, z2, 0x1.9997300000000p-3f);
    q = fmaf(q, z2, -0x1.5555540000000p-2f);
    return at + fmaf(t * z2, q, t);
}
static inline float _ergo_atan2f(float y, float x) {
    uint32_t uy = _eb2f(y), ux = _eb2f(x);
    uint32_t ay = uy & 0x7fffffffU, ax = ux & 0x7fffffffU;
    if (ay > 0x7f800000U || ax > 0x7f800000U) return x + y;   /* NaN */
    if (ax == 0x7f800000U) {                                /* x = ±Inf */
        if (ay == 0x7f800000U) {
            float v = (ux >> 31) ? 0x1.2d97c80000000p+1f    /* 3pi/4 */
                                 : 0x1.921fb60000000p-1f;   /* pi/4 */
            return (uy >> 31) ? -v : v;
        }
        float v = (ux >> 31) ? 0x1.921fb60000000p+1f : 0.0f;  /* pi : 0 */
        return (uy >> 31) ? -v : v;
    }
    if (ay == 0x7f800000U)                                  /* y = ±Inf */
        return (uy >> 31) ? -0x1.921fb60000000p+0f : 0x1.921fb60000000p+0f;
    if (ax == 0) {                                          /* x = ±0 */
        if (ay == 0) {
            float v = (ux >> 31) ? 0x1.921fb60000000p+1f : 0.0f;
            return (uy >> 31) ? -v : v;
        }
        return (uy >> 31) ? -0x1.921fb60000000p+0f : 0x1.921fb60000000p+0f;
    }
    if (ay == 0) {
        float v = (ux >> 31) ? 0x1.921fb60000000p+1f : 0.0f;
        return (uy >> 31) ? -v : v;
    }
    float t = _ef2b(ay) / _ef2b(ax);
    float z;
    if (_eb2f(t) >= 0x7f800000U)                            /* ratio = +Inf */
        z = 0x1.921fb60000000p+0f;                          /* pi/2 */
    else
        z = _erg_atan32_core(t);
    if (!(ux >> 31))
        return (uy >> 31) ? -z : z;
    if (!(uy >> 31))
        return 0x1.921fb60000000p+1f - z;                   /* pi - z */
    return z - 0x1.921fb60000000p+1f;                       /* z - pi */
}

/* ---- POW (f32) ----
 * Double-single (f32 pair, ~48-bit significand) mirror of the f64 dd
 * path: log2 and exp2 as (hi,lo) f32 pairs with fmaf TwoProd/TwoSum.
 * Series coefficients 1/(2n+1) and 1/n! in f32 hi/lo pairs
 * (gen_coeffs.py); 12 log terms, 14 exp terms (truncation < 2^-50). */
static inline void _ds2_sumf(float a, float b, float *hi, float *lo) {
    float s = a + b;
    float bp = s - a;
    *hi = s;
    *lo = (a - (s - bp)) + (b - bp);
}
static inline void _ds2_prodf(float a, float b, float *hi, float *lo) {
    float p = a * b;
    *hi = p;
    *lo = fmaf(a, b, -p);
}
static inline void _ds_addf(float ah, float al, float bh, float bl,
                            float *h, float *l) {
    float sh, sl;
    _ds2_sumf(ah, bh, &sh, &sl);
    sl += al + bl;
    _ds2_sumf(sh, sl, h, l);
}
static inline void _ds_mulf(float ah, float al, float bh, float bl,
                            float *h, float *l) {
    float ph, pl;
    _ds2_prodf(ah, bh, &ph, &pl);
    pl = fmaf(ah, bl, fmaf(al, bh, pl));
    _ds2_sumf(ph, pl, h, l);
}

/* 1/(2n+1), n = 1..12, f32 hi/lo (gen_coeffs.py) */
static const float _erg_rcp_odd_f[13][2] = {
    {0.0f, 0.0f},
    {0x1.5555560000000p-2f, -0x1.5555560000000p-27f},   /* /3 */
    {0x1.99999a0000000p-3f, -0x1.99999a0000000p-29f},   /* /5 */
    {0x1.24924a0000000p-3f, -0x1.b6db6e0000000p-28f},   /* /7 */
    {0x1.c71c720000000p-4f, -0x1.c71c720000000p-31f},   /* /9 */
    {0x1.745d180000000p-4f, -0x1.745d180000000p-29f},   /* /11 */
    {0x1.3b13b20000000p-4f, -0x1.89d89e0000000p-29f},   /* /13 */
    {0x1.1111120000000p-4f, -0x1.ddddde0000000p-29f},   /* /15 */
    {0x1.e1e1e20000000p-5f, -0x1.e1e1e20000000p-33f},   /* /17 */
    {0x1.af286c0000000p-5f, -0x1.af286c0000000p-32f},   /* /19 */
    {0x1.8618620000000p-5f, -0x1.e79e7a0000000p-31f},   /* /21 */
    {0x1.642c860000000p-5f, -0x1.bd37a60000000p-31f},   /* /23 */
    {0x1.47ae140000000p-5f, 0x1.eb851e0000000p-31f},    /* /25 */
};
/* 1/n!, n = 2..14, f32 hi/lo */
static const float _erg_rcp_fact_f[15][2] = {
    {0.0f, 0.0f}, {0.0f, 0.0f},
    {0x1.0000000000000p-1f, 0x0.0p+0f},                 /* 2! */
    {0x1.5555560000000p-3f, -0x1.5555560000000p-28f},   /* 3! */
    {0x1.5555560000000p-5f, -0x1.5555560000000p-30f},   /* 4! */
    {0x1.1111120000000p-7f, -0x1.ddddde0000000p-32f},   /* 5! */
    {0x1.6c16c20000000p-10f, -0x1.27d27e0000000p-35f},  /* 6! */
    {0x1.a01a020000000p-13f, -0x1.7f97fa0000000p-39f},  /* 7! */
    {0x1.a01a020000000p-16f, -0x1.7f97fa0000000p-42f},  /* 8! */
    {0x1.71de3a0000000p-19f, 0x1.55b1cc0000000p-45f},   /* 9! */
    {0x1.27e4fc0000000p-22f, -0x1.10ec140000000p-47f},  /* 10! */
    {0x1.ae64560000000p-26f, 0x1.fd51380000000p-52f},   /* 11! */
    {0x1.1eed8e0000000p-29f, 0x1.ff1b120000000p-54f},   /* 12! */
    {0x1.6124620000000p-33f, -0x1.8af25e0000000p-58f},  /* 13! */
    {0x1.93974a0000000p-37f, 0x1.180f940000000p-62f},   /* 14! */
};

#define _ERG_LN2_HI_F    0x1.62e4300000000p-1f
#define _ERG_LN2_LO_F    (-0x1.05c6100000000p-29f)
#define _ERG_INVLN2_HI_F 0x1.7154760000000p+0f
#define _ERG_INVLN2_LO_F 0x1.4ae0c00000000p-26f

static inline void _erg_log2_ds(float x, float *hp, float *lp) {
    uint32_t u = _eb2f(x);
    int e = 0;
    if (u < 0x00800000U) {
        x *= 0x1.0p+64f;
        u = _eb2f(x);
        e = -64;
    }
    e += (int)(u >> 23) - 127;
    float m = _ef2b((u & 0x007fffffU) | 0x3f800000U);
    if (m >= 0x1.6a09e60000000p+0f) {
        m *= 0.5f;
        e += 1;
    }
    float f = m - 1.0f;                                /* exact */
    float dh, dl;
    _ds2_sumf(2.0f, f, &dh, &dl);
    float s = f / dh;
    float sres = fmaf(-s, dh, f);
    float sl = fmaf(-s, dl, sres) / dh;
    float zh, zl;
    _ds_mulf(s, sl, s, sl, &zh, &zl);
    /* head: 1 + z/3 + z^2/5 in ds; tail z^3*(1/7 + z/9 + ...) as
     * plain-f32 Horner over the exact 1/(2n+1) hi words */
    float sh = 1.0f, sl2 = 0.0f;
    float th = zh, tl = zl;
    for (int n = 1; n <= 2; n++) {
        float t2h, t2l;
        _ds_mulf(th, tl, _erg_rcp_odd_f[n][0], _erg_rcp_odd_f[n][1],
                 &t2h, &t2l);
        _ds_addf(sh, sl2, t2h, t2l, &sh, &sl2);
        _ds_mulf(th, tl, zh, zl, &th, &tl);
    }
    float pt = _erg_rcp_odd_f[8][0];
    for (int n = 7; n >= 3; n--)
        pt = fmaf(pt, zh, _erg_rcp_odd_f[n][0]);
    float tail = (th + tl) * pt;                       /* z^3 * P(z) */
    _ds_addf(sh, sl2, tail, 0.0f, &sh, &sl2);
    float lh, ll;
    _ds_mulf(sh, sl2, 2.0f * s, 2.0f * sl, &lh, &ll);
    float qh, ql;
    _ds_mulf(lh, ll, _ERG_INVLN2_HI_F, _ERG_INVLN2_LO_F, &qh, &ql);
    _ds_addf(qh, ql, (float)e, 0.0f, hp, lp);
}

static inline float _erg_exp2_ds(float th, float tl) {
    float nd = _erint32(th);
    int n = (int)nd;
    float fh = th - nd;
    float fh2, fl2;
    _ds2_sumf(fh, tl, &fh2, &fl2);
    float uh, ul;
    _ds_mulf(fh2, fl2, _ERG_LN2_HI_F, _ERG_LN2_LO_F, &uh, &ul);
    /* head: 1 + u + u^2/2 in ds; tail u^3*(1/3! + u/4! + ...) f32 */
    float sh, sl;
    _ds_addf(1.0f, 0.0f, uh, ul, &sh, &sl);
    float u2h, u2l;
    _ds_mulf(uh, ul, uh, ul, &u2h, &u2l);
    float t2h, t2l;
    _ds_mulf(u2h, u2l, 0.5f, 0.0f, &t2h, &t2l);
    _ds_addf(sh, sl, t2h, t2l, &sh, &sl);
    float pt = _erg_rcp_fact_f[8][0];
    for (int i = 7; i >= 3; i--)
        pt = fmaf(pt, uh, _erg_rcp_fact_f[i][0]);
    float u3 = (u2h + u2l) * uh;
    float rl = fmaf(u3, pt, sl);
    float rh = _escalbn32(sh, n);
    return rh + _escalbn32(rl, n);
}

static inline float _ergo_powf(float x, float y) {
    uint32_t ux = _eb2f(x), uy = _eb2f(y);
    uint32_t ax = ux & 0x7fffffffU, ay = uy & 0x7fffffffU;
    if (ay == 0) return 1.0f;                          /* pow(x, ±0) = 1 */
    if (ax > 0x7f800000U) return x + y;                /* x NaN */
    if (ay > 0x7f800000U)                              /* y NaN */
        return (ux == 0x3f800000U) ? 1.0f : x + y;
    if (ux == 0x3f800000U) return 1.0f;                /* x == 1, any y */
    int y_int = 0, y_odd = 0;
    if (ay < 0x4b000000U) {                            /* |y| < 2^23 */
        float yr = _erint32(y);
        if (yr == y) {
            y_int = 1;
            y_odd = (int)((int32_t)yr & 1);
        }
    } else {
        y_int = 1;                                     /* huge: even */
    }
    if (ax == 0) {                                     /* x = ±0 */
        if ((int32_t)uy > 0)
            return (y_odd && (ux >> 31)) ? -0.0f : 0.0f;
        return (y_odd && (ux >> 31)) ? -_ef2b(0x7f800000U)
                                     : _ef2b(0x7f800000U);
    }
    if (ax == 0x7f800000U) {                           /* x = ±Inf */
        float base = ((int32_t)uy > 0) ? _ef2b(0x7f800000U) : 0.0f;
        if ((ux >> 31) && y_odd)
            return ((int32_t)uy > 0) ? -_ef2b(0x7f800000U) : -0.0f;
        return base;
    }
    if (y == 1.0f) return x;
    if (y == 2.0f) return x * x;
    if (y == -1.0f) return 1.0f / x;
    if (y == 0.5f) {
        if ((int32_t)ux < 0) return _ef2b(0x7fc00000U);
        return sqrtf(x);                               /* hardware, exact */
    }
    int sign = 0;
    if (ux >> 31) {                                    /* x < 0 finite */
        if (!y_int) return _ef2b(0x7fc00000U);
        sign = y_odd;
    }
    if (ay == 0x7f800000U) {                           /* y = ±Inf */
        if (ax == 0x3f800000U) return 1.0f;
        int big = ax > 0x3f800000U;
        int pos = !((int32_t)uy >> 31);
        return (big == pos) ? _ef2b(0x7f800000U) : 0.0f;
    }
    float h, l;
    _erg_log2_ds(_ef2b(ax), &h, &l);
    float th, tl;
    _ds2_prodf(y, h, &th, &tl);
    tl = fmaf(y, l, tl);
    if (th >= 128.0f) {
        float inf = _ef2b(0x7f800000U);
        return sign ? -inf : inf;
    }
    if (th <= -150.0f) return sign ? -0.0f : 0.0f;
    float r = _erg_exp2_ds(th, tl);
    return sign ? -r : r;
}

#endif /* ERGO_MATH_LIBM */
#endif /* ERGO_MATH_KERNELS_H */
