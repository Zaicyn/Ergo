// ergo_trig32.glsl — the shared f32 sin/cos core (GLSL port).
// =====================================================================
// Bit-identical to core/runtime/ergo_math_kernels.h's _ergo_sinf /
// _ergo_cosf (the certified CPU kernel) and to the SPIR-V compute
// emission (core/backends/spirv.py _emit_trig32_helper).  Same
// coefficients, same expression order, same fma points, same integer
// reduction.
//
// Structure (identical in all three languages):
//   specials:  NaN/Inf -> NaN; |x| < 2^-12 -> identity (sin) / 1 (cos)
//   |x| <= 6400:          f32 3-word Cody-Waite on pi/2,
//                         k via explicitly-fused magic-number rint
//   6400 < |x| <= 1.57e6: f64 3-word Cody-Waite (f64 fma, exact ints)
//   |x| > 1.57e6:         Payne-Hanek window over 2/pi limbs; the
//                         f32-sourced mantissa is 24-bit so all
//                         products fit u64 exactly (no 128-bit needed)
//   kernel: sin(r) = r + r^3*P(r^2); cos(r) = 1 - z/2 + z^2*C(z);
//   quadrant k&3 + input sign fold.
//
// glslc's GLSL profile rejects hexadecimal float literals, so every
// floating constant below is bit-constructed (uintBitsToFloat /
// packDouble2x32) with the hex-float value in a comment.  Exact by
// construction, immune to decimal-parse rounding worries.
//
// Requires (both present on every target we ship): fp64 and int64 in
// shaders.  In Vulkan GLSL that is the two ARB extensions below; the
// device must enable shaderFloat64 + shaderInt64 (ergo's runtime does).
//
// 2026-09-04, the N64-modder contract: one evaluation, both values.

#extension GL_ARB_gpu_shader_fp64 : enable
#extension GL_ARB_gpu_shader_int64 : enable

// ── helpers (bit casts) ──
uint64_t _erg_eb2d(double x) { return packUint2x32(unpackDouble2x32(x)); }
double _erg_ed2b(uint64_t u) { return packDouble2x32(unpackUint2x32(u)); }

// pi/2 splits (identical to the C header; hex-float values in comments).
// Macros: GLSL forbids non-constant-expression global initializers.
#define ERG_PIO2_HI   packDouble2x32(uvec2(0x54442d18u, 0x3ff921fbu)) // 0x1.921fb54442d18p+0
#define ERG_PIO2_MID  packDouble2x32(uvec2(0x33145c07u, 0x3c91a626u)) // 0x1.1a62633145c07p-54
#define ERG_PIO2_LO   packDouble2x32(uvec2(0xb7ed8fbdu, 0x391f1976u)) // 0x1.f1976b7ed8fbcep-110
#define ERG_TWO_OVER_PI packDouble2x32(uvec2(0x6dc9c883u, 0x3fe45f30u)) // 0x1.45f306dc9c883p-1
#define ERG_M52       packDouble2x32(uvec2(0x00000000u, 0x43380000u)) // 0x1.8p+52
#define ERG_2PM64     packDouble2x32(uvec2(0x00000000u, 0x3bf00000u)) // 0x1.0p-64
#define ERG_2PM128    packDouble2x32(uvec2(0x00000000u, 0x37f00000u)) // 0x1.0p-128
#define ERG_2PM192    packDouble2x32(uvec2(0x00000000u, 0x33f00000u)) // 0x1.0p-192

// ── Payne-Hanek, f32-sourced (u64-only; see C header) ──
const uint ERG_2OPI[60] = uint[](
    0xa2f983u, 0x6e4e44u, 0x1529fcu, 0x2757d1u, 0xf534ddu, 0xc0db62u,
    0x95993cu, 0x439041u, 0xfe5163u, 0xabdebbu, 0xc561b7u, 0x246e3au,
    0x424dd2u, 0xe00649u, 0x2eea09u, 0xd1921cu, 0xfe1debu, 0x1cb129u,
    0xa73ee8u, 0x8235f5u, 0x2ebb44u, 0x84e99cu, 0x7026b4u, 0x5f7e41u,
    0x3991d6u, 0x398353u, 0x39f49cu, 0x845f8bu, 0xbdf928u, 0x3b1ff8u,
    0x97ffdeu, 0x05980fu, 0xef2f11u, 0x8b5a0au, 0x6d1f6du, 0x367ecfu,
    0x27cb09u, 0xb74f46u, 0x3f669eu, 0x5fea2du, 0x7527bau, 0xc7ebe5u,
    0xf17b3du, 0x0739f7u, 0x8a5292u, 0xea6bfbu, 0x5fb11fu, 0x8d5d08u,
    0x560330u, 0x46fc7bu, 0x6babf0u, 0xcfbc20u, 0x9af436u, 0x1da9e3u,
    0x91615eu, 0xe61b08u, 0x659985u, 0x5f14a0u, 0x68408du, 0xffd880u);

int _erg_ph32(double ax, out double rp) {
    uint64_t u = _erg_eb2d(ax);
    int e = int(u >> 52) - 1023 + 29;
    uint64_t m = ((u & 0x000fffffffffffffUL) | 0x0010000000000000UL) >> 29;
    int i_lo = (e > 77) ? (e - 77 + 23) / 24 : 0;
    int i_hi = i_lo + 8;
    int F = 24 * i_hi + 76 - e;
    uint64_t acc[10];
    for (int j = 0; j < 10; j++) acc[j] = 0UL;
    for (int i = i_lo; i <= i_hi; i++) {
        uint64_t p = m * uint64_t(ERG_2OPI[i]);   // exact: <= 2^48
        int s = 24 * (i_hi - i);
        int limb = 3 + (s >> 6), off = s & 63;
        uint64_t v0, v1;
        if (off == 0) { v0 = p; v1 = 0UL; }
        else { v0 = p << off; v1 = p >> (64 - off); }
        uint64_t t = acc[limb] + v0;
        uint64_t c = (t < acc[limb]) ? 1UL : 0UL;
        acc[limb] = t;
        t = acc[limb + 1] + v1;
        uint64_t c1 = (t < acc[limb + 1]) ? 1UL : 0UL;
        uint64_t nv = t + c;
        if (nv < t) c1 = 1UL;
        acc[limb + 1] = nv;
        t = acc[limb + 2] + c1;                 // v2 == 0
        uint64_t c2 = ((t < acc[limb + 2]) || ((c1 != 0UL) && (t == acc[limb + 2]))) ? 1UL : 0UL;
        acc[limb + 2] = t;
        acc[limb + 3] += c2;
    }
    int wl = (F >> 6) + 3, wo = F & 63;
    uint64_t above, fr0, fr1, fr2;
    if (wo == 0) {
        above = acc[wl];
        fr0 = acc[wl - 1]; fr1 = acc[wl - 2]; fr2 = acc[wl - 3];
    } else {
        above = (acc[wl] >> wo) | (acc[wl + 1] << (64 - wo));
        fr0 = (acc[wl - 1] >> wo) | (acc[wl] << (64 - wo));
        fr1 = (acc[wl - 2] >> wo) | (acc[wl - 1] << (64 - wo));
        fr2 = (acc[wl - 3] >> wo) | (acc[wl - 2] << (64 - wo));
    }
    int k = int(above & 3UL);
    uint64_t sticky = 0UL;
    for (int j = 0; j < wl - 3; j++) sticky |= acc[j];
    if (wo != 0) sticky |= (acc[wl - 3] & ((1UL << wo) - 1UL));
    uint64_t g0, g1, g2;
    bool neg;
    if ((fr0 >> 63) != 0UL) {
        k += 1;
        neg = true;
        g0 = ~fr0; g1 = ~fr1; g2 = ~fr2;
        if (sticky == 0UL) { g0 += 1UL; if (g0 == 0UL) { g1 += 1UL; if (g1 == 0UL) g2 += 1UL; } }
    } else {
        neg = false;
        g0 = fr0; g1 = fr1; g2 = fr2;
    }
    precise double f0 = double(g0) * ERG_2PM64;
    precise double f1 = double(g1) * ERG_2PM128;
    precise double f2 = double(g2) * ERG_2PM192;
    precise double hi = f0 * ERG_PIO2_HI;
    precise double lo = fma(f0, ERG_PIO2_HI, -hi);
    lo = fma(f1, ERG_PIO2_HI, lo);
    lo = fma(f0, ERG_PIO2_MID, lo);
    lo = fma(f2, ERG_PIO2_HI, lo);
    lo = fma(f0, ERG_PIO2_LO, lo);
    precise double r = hi + lo;
    rp = neg ? -r : r;
    return k & 3;
}

// ── the shared reduction: ax = |x|, finite, ax > 0 ──
// returns k (quadrant in low bits), r = remainder in [-pi/4, pi/4]
int _erg_remod32_gl(float ax, out float rp) {
    if (ax <= 6400.0) {
        // explicitly-fused magic-number rint — matches the C header's
        // contract-proof form bit-for-bit (see ergo_math_kernels.h)
        precise float kd = fma(ax, uintBitsToFloat(0x3f22f983u),  // 2/pi
                       uintBitsToFloat(0x4b400000u))      // 0x1.8p+23
                   - uintBitsToFloat(0x4b400000u);
        precise float r = fma(-kd, uintBitsToFloat(0x3fc90fdbu), ax);  // pi/2 w1
        r = fma(-kd, uintBitsToFloat(0xb33bbd2eu), r);   // -0x1.777a5cp-25
        r = fma(-kd, uintBitsToFloat(0xa6f72cedu), r);   // -0x1.ee59dap-50
        rp = r;
        return int(kd);
    }
    precise double ax64 = double(ax);
    precise double r64;
    int k;
    if (ax64 <= 1572864.0lf) {   // 0x1.8p+20
        precise double kd = fma(ax64, ERG_TWO_OVER_PI, ERG_M52) - ERG_M52;
        precise double r = fma(-kd, ERG_PIO2_HI, ax64);
        r = fma(-kd, ERG_PIO2_MID, r);
        r = fma(-kd, ERG_PIO2_LO, r);
        r64 = r;
        k = int(kd);
    } else {
        k = _erg_ph32(ax64, r64);
    }
    rp = float(r64);
    return k;
}

// ── minimax kernels (identical coefficients to the C header) ──
float _erg_ksin32_gl(float r) {
    precise float z = r * r, v = z * r;
    precise float p = fma(uintBitsToFloat(0x3636df04u), z,      // 0x1.6dbe08p-19
                  uintBitsToFloat(0xb95009d4u));        // -0x1.a013a8p-13
    p = fma(p, z, uintBitsToFloat(0x3c088887u));        // 0x1.11110ep-7
    return fma(v, fma(z, p, uintBitsToFloat(0xbe2aaaabu)), r); // -0x1.555556p-3
}
float _erg_kcos32_gl(float r) {
    precise float z = r * r;
    precise float q = fma(uintBitsToFloat(0xb4929227u), z,      // -0x1.25244ep-22
                  uintBitsToFloat(0x37d00ae2u));        // 0x1.a015c4p-16
    q = fma(q, z, uintBitsToFloat(0xbab60b60u));        // -0x1.6c16c0p-10
    q = fma(q, z, uintBitsToFloat(0x3d2aaaabu));        // 0x1.555556p-5
    precise float zz = z * q;
    return 1.0 - fma(-z, zz, 0.5 * z);
}

// ── the pair (N64 contract: one reduction, both values) ──
vec2 ergo_sincosf32(float x) {
    uint u = floatBitsToUint(x);
    uint au = u & 0x7fffffffu;
    if (au >= 0x7f800000u)
        // NaN/Inf -> NaN.  NOT x - x: the driver folds that to +0.0 under
        // its default fast-math license (NoContraction doesn't cover it).
        // Payload is policy-unspecified; use the x86 x-x canonical qNaN.
        return vec2(uintBitsToFloat(0xffc00000u));
    if (au < 0x39800000u) return vec2(x, 1.0);          // tiny
    precise float r;
    int k = _erg_remod32_gl(uintBitsToFloat(au), r);
    precise float s, c;
    switch (k & 3) {
    case 0:  s = _erg_ksin32_gl(r);  c = _erg_kcos32_gl(r);  break;
    case 1:  s = _erg_kcos32_gl(r);  c = -_erg_ksin32_gl(r); break;
    case 2:  s = -_erg_ksin32_gl(r); c = -_erg_kcos32_gl(r); break;
    default: s = -_erg_kcos32_gl(r); c = _erg_ksin32_gl(r);  break;
    }
    if ((u >> 31) != 0u) s = -s;    // sin odd, cos even
    return vec2(s, c);
}
float ergo_sinf32(float x) { return ergo_sincosf32(x).x; }
float ergo_cosf32(float x) { return ergo_sincosf32(x).y; }
