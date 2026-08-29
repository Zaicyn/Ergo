#!/usr/bin/env python3
"""ulp_check.py — bit-level accuracy harness for the owned math kernels.

Compares the C kernels (tests/math_kernels/dump.c, compiled per compiler)
against an 800-bit mpmath reference over domain sweeps + edge cases.
Reports max ulp error per kernel per precision, and the gcc-vs-clang
bit-identity verdict over the identical sweep.

Usage: python3 tests/math_kernels/ulp_check.py [kernel ...]
Reference convention: the correctly-rounded answer is float(mp.f(x))
computed at 800 bits — double rounding at that margin is a ~2^-700
event and is discounted in interpretation.  NaN matches NaN; Inf and
signed zero must match exactly.
"""
import os
import struct
import subprocess
import sys

from mpmath import mp, mpf, sin, cos, exp, log, atan2, power, log10, isnan, isinf

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
mp.prec = 800

FLAGS = ["-O3", "-fwrapv", "-march=x86-64-v3", "-ffp-contract=fast",
         "-fno-math-errno", "-std=c11"]


def build(cc):
    out = os.path.join(HERE, f"dump_{cc}")
    subprocess.run(
        [cc, "-o", out, os.path.join(HERE, "dump.c")] + FLAGS +
        ["-DERGO_HAVE_POW", "-DERGO_HAVE_POWF", "-DERGO_HAVE_F32",
         "-lm", f"-I{os.path.join(REPO, 'core', 'runtime')}"],
        check=True)
    return out


def run(binpath, func, inputs):
    """inputs: list of bit-ints (or pairs). Returns list of bit-ints."""
    lines = []
    for v in inputs:
        if isinstance(v, tuple):
            lines.append(f"{func} {v[0]:x} {v[1]:x}")
        else:
            lines.append(f"{func} {v:x}")
    p = subprocess.run([binpath], input="\n".join(lines) + "\n",
                       capture_output=True, text=True, check=True)
    out = []
    for ln in p.stdout.splitlines():
        parts = ln.split()
        out.append(int(parts[-1], 16))
    return out


# ---- bit/ordered-int helpers ----
def b64(d):
    return struct.unpack("<Q", struct.pack("<d", d))[0]


def d64(u):
    return struct.unpack("<d", struct.pack("<Q", u))[0]


def b32(f):
    try:
        return struct.unpack("<I", struct.pack("<f", f))[0]
    except OverflowError:          # value beyond FLT_MAX rounds to ±Inf
        import math
        return 0xff800000 if math.copysign(1.0, f) < 0 else 0x7f800000


def f32(u):
    return struct.unpack("<f", struct.pack("<I", u))[0]


def ord64(u):
    """monotonic ordered-int mapping for f64 bit pattern"""
    return u ^ 0x8000000000000000 if u >> 63 else ~u & 0xFFFFFFFFFFFFFFFF


def ord32(u):
    return u ^ 0x80000000 if u >> 31 else ~u & 0xFFFFFFFF


def ref_bits(func, u, f32mode, name=""):
    """correctly rounded reference bits for input bit-pattern u"""
    if (u << 1) & (0xffffffff if f32mode else 0xffffffffffffffff) == 0:
        # signed-zero input: mpmath normalizes -0 to +0, so fix the
        # zero-argument results by hand (C99 semantics)
        neg = (u >> (31 if f32mode else 63)) & 1
        if name in ("sin", "sinf"):
            return u                       # sin(±0) = ±0
        if name in ("cos", "cosf", "exp", "expf"):
            return b32(1.0) if f32mode else b64(1.0)
        if name in ("log", "logf"):
            return b32(float("-inf")) if f32mode else b64(float("-inf"))
    if f32mode:
        x = mpf(f32(u))          # exact value of the f32 input
    else:
        x = mpf(d64(u))
    v = func(x)
    if isinstance(v, mp.mpc):          # e.g. log(-1) = i*pi -> kernel NaN
        v = float("nan") if v.imag != 0 else v.real
    if f32mode:
        return b32(float(v))     # float() then f32 round — both RNE
    return b64(float(v))


def classcheck(want_u, got_u, f32mode):
    """special-value agreement: NaN/Inf/zero classes"""
    if f32mode:
        w, g = f32(want_u), f32(got_u)
    else:
        w, g = d64(want_u), d64(got_u)
    import math
    if math.isnan(w):
        return math.isnan(g)
    if math.isinf(w):
        return math.isinf(g) and (math.copysign(1, w) == math.copysign(1, g))
    if w == 0.0:
        return g == 0.0 and (math.copysign(1, w) == math.copysign(1, g))
    return None     # not special


def sweep(func_name, mpfunc, inputs, f32mode, bins, label):
    got = {cc: run(bins[cc], func_name, inputs) for cc in bins}
    identical = got["gcc"] == got["clang"]
    worst = 0
    worst_in = None
    special_bad = []
    n = len(inputs)
    for i, u in enumerate(inputs):
        g = got["gcc"][i]
        if isinstance(u, tuple):
            wu = ref_bits2(mpfunc, u, f32mode)
        else:
            wu = ref_bits(mpfunc, u, f32mode, name=label)
        sc = classcheck(wu, g, f32mode)
        if sc is not None:
            if not sc:
                special_bad.append((u, wu, g))
            continue
        od = ord32 if f32mode else ord64
        d = abs(od(g) - od(wu))
        if d > worst:
            worst, worst_in = d, u
    return worst, worst_in, identical, special_bad, n


def ref_bits2(mpfunc, u2, f32mode):
    if f32mode:
        x, y = mpf(f32(u2[0])), mpf(f32(u2[1]))
    else:
        x, y = mpf(d64(u2[0])), mpf(d64(u2[1]))
    v = mpfunc(x, y)
    if f32mode:
        return b32(float(v))
    return b64(float(v))


# ---- input sweeps ----
def linspace_bits(lo, hi, n, f32mode=False):
    out = []
    for i in range(n):
        v = lo + (hi - lo) * i / (n - 1)
        out.append(b32(v) if f32mode else b64(v))
    return out


def logspace_bits(lo, hi, n, f32mode=False):
    import math as m
    out = []
    for i in range(n):
        v = m.exp(m.log(lo) + (m.log(hi) - m.log(lo)) * i / (n - 1))
        out.append(b32(v) if f32mode else b64(v))
    return out


def main():
    only = set(sys.argv[1:])
    bins = {"gcc": build("gcc"), "clang": build("clang")}

    # reference functions at mp precision
    mp_sin, mp_cos, mp_exp, mp_log = sin, cos, exp, log
    mp_atan2 = lambda y, x: atan2(y, x)
    mp_pow = lambda x, y: power(x, y)

    import math as _mm
    import math as _m

    def annex_pow(x, y):           # C99 Annex F table (both precisions)
        N = _mm.nan
        if y == 0.0:
            return 1.0
        if _mm.isnan(x):
            return N
        if _mm.isnan(y):
            return 1.0 if x == 1.0 else N
        if x == 1.0:
            return 1.0
        yint = float(y).is_integer() or abs(y) >= 2**52
        yodd = yint and abs(y) < 2**52 and (int(abs(y)) & 1) == 1
        if x == 0.0:
            neg = _mm.copysign(1.0, x) < 0
            if y > 0:
                return -0.0 if (neg and yodd) else 0.0
            return -_mm.inf if (neg and yodd) else _mm.inf
        if _mm.isinf(x):
            neg = x < 0
            if y > 0:
                return -_mm.inf if (neg and yodd) else _mm.inf
            return -0.0 if (neg and yodd) else 0.0
        if _mm.isinf(y):
            if abs(x) == 1.0:
                return 1.0
            big = abs(x) > 1.0
            pos = y > 0
            return _mm.inf if big == pos else 0.0
        if x < 0 and not yint:
            return N
        return None                # general case -> mpmath

    print(f"{'kernel':10s} {'n':>7s} {'max_ulp':>8s}  worst input | gcc==clang")
    all_ok = True

    def report(name, n, worst, worst_in, ident, bad_specials):
        nonlocal all_ok
        ws = f"{worst_in:x}" if isinstance(worst_in, int) else \
            "(" + ",".join(f"{v:x}" for v in worst_in) + ")" if worst_in else "-"
        print(f"{name:10s} {n:7d} {worst:8d}  {ws} | {ident}")
        if bad_specials:
            all_ok = False
            for u, w, g in bad_specials[:5]:
                us = f"{u:x}" if isinstance(u, int) else \
                    "(" + ",".join(f"{v:x}" for v in u) + ")"
                print(f"    SPECIAL MISMATCH in={us} want={w:x} got={g:x}")

    # ---- sin/cos f64 ----
    if not only or "sin" in only or "cos" in only:
        trig_in = []
        trig_in += linspace_bits(-10 * 3.141592653589793, 10 * 3.141592653589793, 40000)
        trig_in += logspace_bits(1e-8, 1e6, 20000)          # medium path
        trig_in += logspace_bits(1.6e6, 1e300, 20000)       # Payne-Hanek
        # near multiples of pi/2 (reduction stress) at several magnitudes
        for n in list(range(1, 40)) + [12345, 1000003, 67108864]:
            base = n * 1.5707963267948966
            for d in (-2e-16 * abs(base), -1e-16, 0.0, 1e-16, 2e-16 * abs(base)):
                trig_in.append(b64(base + d))
        # huge + denormal + specials
        for v in (1e16, 1e100, 1.7e308, 5e-324, 1e-320, 0.0, -0.0,
                  float("inf"), float("-inf"), float("nan")):
            trig_in.append(b64(v))
        for nm, mf in (("sin", mp_sin), ("cos", mp_cos)):
            w, wi, ident, bad, n = sweep(nm, mf, trig_in, False, bins, nm)
            report(nm, n, w, wi, ident, bad)

    # ---- exp/log f64 ----
    if not only or "exp" in only:
        ein = linspace_bits(-750.0, 715.0, 60000)
        ein += linspace_bits(-745.2, -708.3, 20000)         # denormal outputs
        ein += logspace_bits(1e-300, 700, 10000)
        for v in (0.0, -0.0, 1e-320, 5e-324, float("inf"), float("-inf"),
                  float("nan"), 1.0, -1.0):
            ein.append(b64(v))
        w, wi, ident, bad, n = sweep("exp", mp_exp, ein, False, bins, "exp")
        report("exp", n, w, wi, ident, bad)
    if not only or "log" in only:
        lin = logspace_bits(5e-324, 1.7e308, 80000)
        for i in range(-2000, 2001):                        # near 1.0
            lin.append(b64(1.0 + i * 2 ** -52))
        for v in (0.0, -0.0, 1.0, float("inf"), float("-inf"), float("nan"),
                  -1.0, -1e300):
            lin.append(b64(v))
        w, wi, ident, bad, n = sweep("log", mp_log, lin, False, bins, "log")
        report("log", n, w, wi, ident, bad)

    # ---- atan2 f64 ----
    if not only or "atan2" in only:
        ain = []
        for i in range(30000):    # random magnitudes, all quadrants
            import random
            random.seed(1000 + i)
            y = _m.copysign(_m.exp(random.uniform(-300, 300)),
                            random.choice((1.0, -1.0)))
            x = _m.copysign(_m.exp(random.uniform(-300, 300)),
                            random.choice((1.0, -1.0)))
            ain.append((b64(y), b64(x)))
        # near-axis and ratio-extreme cases
        for tiny in (1e-300, 5e-324, 1e-16):
            for base in (1.0, 1e300, 1e-300):
                ain.append((b64(tiny), b64(base)))
                ain.append((b64(base), b64(tiny)))
                ain.append((b64(-tiny), b64(-base)))
        # special lattice: C99 Annex F table (host math.atan2 is the
        # platform C library's implementation of exactly that table)
        lattice = [0.0, -0.0, 1.0, -1.0, _m.inf, -_m.inf, _m.nan]
        for y in lattice:
            for x in lattice:
                ain.append((b64(y), b64(x)))

        def atan2_ref(u2):
            y, x = d64(u2[0]), d64(u2[1])
            if (y == 0 or _m.isinf(y) or _m.isnan(y) or
                    x == 0 or _m.isinf(x) or _m.isnan(x)):
                return b64(_m.atan2(y, x))
            return ref_bits2(mp_atan2, u2, False)

        got = {cc: run(bins[cc], "atan2", ain) for cc in bins}
        ident = got["gcc"] == got["clang"]
        worst, wi, bad = 0, None, []
        for i, u in enumerate(ain):
            g = got["gcc"][i]
            wu = atan2_ref(u)
            sc = classcheck(wu, g, False)
            if sc is not None:
                if not sc:
                    bad.append((u, wu, g))
                continue
            d = abs(ord64(g) - ord64(wu))
            if d > worst:
                worst, wi = d, u
        report("atan2", len(ain), worst, wi, ident, bad)

    # ---- pow f64 ----
    if not only or "pow" in only:
        import random
        random.seed(77)
        pin = []
        bases = [0.5, 0.9, 0.9999999999999999, 1.0, 1.0000000000000002,
                 1.5, 2.0, 10.0, 1e100, 1e-100, 5e-324, 1e-320,
                 2.2250738585072014e-308]
        exps = [0.5, -0.5, 1.5, 2.0, 3.0, 17.25, -17.25, 100.0, -100.0,
                1e4, -1e4, 65536.0, 0.9999999, 1023.9999999999999]
        for b in bases:
            for e in exps:
                pin.append((b64(b), b64(e)))
                pin.append((b64(-b), b64(e)))
        for i in range(30000):    # random positive base x random exp
            b = _m.exp(random.uniform(-700, 700))
            e = random.uniform(-300, 300)
            pin.append((b64(b), b64(e)))
        # overflow/underflow boundary fuzz
        for i in range(2000):
            b = random.choice((2.0, 10.0, 1.5, 1.0000000000000002))
            e = random.uniform(1020, 1030) * (1024.0 /
                     (math.log2(b) if False else _m.log(b, 2)))
            pin.append((b64(b), b64(e)))
            pin.append((b64(b), b64(-e)))
        import math as _mm2
        lattice = [0.0, -0.0, 1.0, -1.0, -2.0, 2.0, 0.5, -0.5,
                   _mm2.inf, -_mm2.inf, _mm2.nan]
        for b in lattice:
            for e in lattice:
                pin.append((b64(b), b64(e)))

        def pow_ref(u2):
            x, y = d64(u2[0]), d64(u2[1])
            v = annex_pow(x, y)
            if v is not None:
                return b64(v)
            w = mp_pow(mpf(x), mpf(y))
            if isinstance(w, mp.mpc):
                w = float("nan") if w.imag != 0 else w.real
            return b64(float(w))

        got = {cc: run(bins[cc], "pow", pin) for cc in bins}
        ident = got["gcc"] == got["clang"]
        worst, wi, bad = 0, None, []
        for i, u in enumerate(pin):
            g = got["gcc"][i]
            wu = pow_ref(u)
            sc = classcheck(wu, g, False)
            if sc is not None:
                if not sc:
                    bad.append((u, wu, g))
                continue
            d = abs(ord64(g) - ord64(wu))
            if d > worst:
                worst, wi = d, u
        report("pow", len(pin), worst, wi, ident, bad)

    # ---- f32 sweeps ----
    if not only or "f32" in only:
        trig32 = []
        trig32 += linspace_bits(-10 * _m.pi, 10 * _m.pi, 40000, True)
        trig32 += logspace_bits(1e-6, 6400, 15000, True)      # medium
        trig32 += logspace_bits(6500, 1e38, 15000, True)      # promoted path
        for n in list(range(1, 20)) + [1234, 4000]:
            base = n * 1.5707963267948966
            trig32.append(b32(base))
        for v in (1e16, 1e38, 1e-45, 1e-40, 0.0, -0.0,
                  float("inf"), float("-inf"), float("nan")):
            trig32.append(b32(v))
        for nm, mf in (("sinf", mp_sin), ("cosf", mp_cos)):
            w, wi, ident, bad, n = sweep(nm, mf, trig32, True, bins, nm)
            report(nm, n, w, wi, ident, bad)

        e32 = linspace_bits(-104.0, 89.0, 50000, True)
        e32 += linspace_bits(-103.3, -87.3, 10000, True)      # denormal out
        for v in (0.0, -0.0, 1e-45, 1e-40, float("inf"),
                  float("-inf"), float("nan"), 1.0, -1.0):
            e32.append(b32(v))
        w, wi, ident, bad, n = sweep("expf", mp_exp, e32, True, bins, "expf")
        report("expf", n, w, wi, ident, bad)

        l32 = logspace_bits(1.2e-38, 3.4e38, 50000, True)
        l32 += logspace_bits(1e-45, 1.2e-38, 10000, True)     # denormals
        for i in range(-1000, 1001):                          # near 1.0
            l32.append(b32(1.0 + i * 2 ** -23))
        for v in (0.0, -0.0, 1.0, float("inf"), float("-inf"),
                  float("nan"), -1.0):
            l32.append(b32(v))
        w, wi, ident, bad, n = sweep("logf", mp_log, l32, True, bins, "logf")
        report("logf", n, w, wi, ident, bad)

        # atan2 f32
        import random
        random.seed(4242)
        a32 = []
        for i in range(20000):
            y = _m.copysign(_m.exp(random.uniform(-80, 80)),
                            random.choice((1.0, -1.0)))
            x = _m.copysign(_m.exp(random.uniform(-80, 80)),
                            random.choice((1.0, -1.0)))
            a32.append((b32(y), b32(x)))
        lattice = [0.0, -0.0, 1.0, -1.0, _m.inf, -_m.inf, _m.nan]
        for y in lattice:
            for x in lattice:
                a32.append((b32(y), b32(x)))

        def atan2f_ref(u2):
            y, x = f32(u2[0]), f32(u2[1])
            if (y == 0 or _m.isinf(y) or _m.isnan(y) or
                    x == 0 or _m.isinf(x) or _m.isnan(x)):
                return b32(_m.atan2(y, x))
            return ref_bits2(mp_atan2, u2, True)

        got = {cc: run(bins[cc], "atan2f", a32) for cc in bins}
        ident = got["gcc"] == got["clang"]
        worst, wi, bad = 0, None, []
        for i, u in enumerate(a32):
            g = got["gcc"][i]
            wu = atan2f_ref(u)
            sc = classcheck(wu, g, True)
            if sc is not None:
                if not sc:
                    bad.append((u, wu, g))
                continue
            d = abs(ord32(g) - ord32(wu))
            if d > worst:
                worst, wi = d, u
        report("atan2f", len(a32), worst, wi, ident, bad)

        # pow f32
        p32 = []
        bases32 = [0.5, 0.9, 0.99999994, 1.0, 1.0000001, 1.5, 2.0, 10.0,
                   1e30, 1e-30, 1e-45, 1.2e-38]
        exps32 = [0.5, -0.5, 1.5, 2.0, 3.0, 17.25, -17.25, 100.0, -100.0,
                  127.9, -127.9]
        for b in bases32:
            for e in exps32:
                p32.append((b32(b), b32(e)))
                p32.append((b32(-b), b32(e)))
        for i in range(20000):
            b = _m.exp(random.uniform(-85, 85))
            e = random.uniform(-130, 130)
            p32.append((b32(b), b32(e)))
        lattice = [0.0, -0.0, 1.0, -1.0, -2.0, 2.0, 0.5, -0.5,
                   _m.inf, -_m.inf, _m.nan]
        for b in lattice:
            for e in lattice:
                p32.append((b32(b), b32(e)))

        def powf_ref(u2):
            x, y = f32(u2[0]), f32(u2[1])
            v = annex_pow(x, y)          # same C99 table (values, then round)
            if v is not None:
                return b32(v)
            w = mp_pow(mpf(x), mpf(y))
            if isinstance(w, mp.mpc):
                w = float("nan") if w.imag != 0 else w.real
            return b32(float(w))

        got = {cc: run(bins[cc], "powf", p32) for cc in bins}
        ident = got["gcc"] == got["clang"]
        worst, wi, bad = 0, None, []
        for i, u in enumerate(p32):
            g = got["gcc"][i]
            wu = powf_ref(u)
            sc = classcheck(wu, g, True)
            if sc is not None:
                if not sc:
                    bad.append((u, wu, g))
                continue
            d = abs(ord32(g) - ord32(wu))
            if d > worst:
                worst, wi = d, u
        report("powf", len(p32), worst, wi, ident, bad)

    print("ALL-OK" if all_ok else "SPECIAL-CASE FAILURES PRESENT")


if __name__ == "__main__":
    main()
