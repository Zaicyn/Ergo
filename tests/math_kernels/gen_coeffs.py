#!/usr/bin/env python3
"""gen_coeffs.py — generate and validate the polynomial coefficient sets
for core/runtime/ergo_math_kernels.h.

Method: interpolation at Chebyshev nodes, solved as a power-basis
Vandermonde system at 800-bit precision (mpmath lu_solve), then dense
sup-error validation over the working interval. For these smooth entire
targets, node interpolation lands within ~2x of minimax; the C-side
bit-exact ulp harness (ulp_check.py) is the final authority on the
assembled kernels.

Coefficients print as C hex-float literals — the exact values pasted
into the kernel header. Regenerate + repaste only with a recorded
reason; the header's ulp comments must be re-measured after any change.
"""
from mpmath import (mp, mpf, sin, cos, tan, atan, exp, log, sqrt, pi,
                    lu_solve, matrix)
import struct

mp.prec = 800

LO = mpf("1e-6")     # keeps z^2-denominator targets clear of cancellation


def cheb_fit(f, lo, hi, deg):
    n = deg + 1
    nodes = [(lo + hi) / 2 + (hi - lo) / 2 * mp.cos(pi * (2 * j + 1) / (2 * n))
             for j in range(n)]
    A = matrix(n, n)
    b = matrix(n, 1)
    for i, x in enumerate(nodes):
        xp = mpf(1)
        for j in range(n):
            A[i, j] = xp
            xp *= x
        b[i] = f(x)
    c = lu_solve(A, b)
    return [c[j] for j in range(n)]


def polyval_c(c, x):
    s = mpf(0)
    for a in reversed(c):
        s = s * x + a
    return s


def fit_and_check(name, f, lo, hi, deg):
    c = cheb_fit(f, lo, hi, deg)
    worst = mpf(0)
    for i in range(4001):
        x = lo + (hi - lo) * mpf(i) / 4000
        e = abs(f(x) - polyval_c(c, x))
        if e > worst:
            worst = e
    print(f"{name}: deg {deg}, sup |residual| = {mp.nstr(worst, 3)}")
    return c


def f32_round(x):
    return struct.unpack("f", struct.pack("f", float(x)))[0]


def emit(name, c, f32=False):
    print(f"/* {name} (Chebyshev fit, see gen_coeffs.py) */")
    for i, a in enumerate(c):
        if f32:
            v = f32_round(a)
            print(f"    {v.hex()}f,  /* [{i}] */")
        else:
            print(f"    {float(a).hex()},  /* [{i}] */")


ZMAX = (pi / 4) ** 2              # sin/cos reduced interval z = r^2
SMAX = (sqrt(mpf(2)) - 1) / (sqrt(mpf(2)) + 1)   # s at the log m-window edge

# ---- f64 ----
f = lambda z: (sin(sqrt(z)) - sqrt(z)) / (z * sqrt(z))
p_sin64 = fit_and_check("sin64 P deg6", f, LO, ZMAX, 6)

f = lambda z: (cos(sqrt(z)) - 1 + z / 2) / (z * z)
p_cos64 = fit_and_check("cos64 C deg5", f, LO, ZMAX, 5)

ZA = (mpf(7) / 16) ** 2           # atan direct interval z = t^2
f = lambda z: (atan(sqrt(z)) - sqrt(z)) / (z * sqrt(z))
p_atan64 = fit_and_check("atan64 A deg10", f, LO, ZA, 10)

# log: m=(1+s)/(1-s), log(m) = 2s(1 + z*L(z)), z = s^2
f = lambda z: (log((1 + sqrt(z)) / (1 - sqrt(z))) / (2 * sqrt(z)) - 1) / z
p_log64 = fit_and_check("log64 L deg7", f, LO, SMAX * SMAX, 7)

# ---- f32 ----
f = lambda z: (sin(sqrt(z)) - sqrt(z)) / (z * sqrt(z))
p_sin32 = fit_and_check("sin32 P deg3", f, LO, ZMAX, 3)

f = lambda z: (cos(sqrt(z)) - 1 + z / 2) / (z * z)
p_cos32 = fit_and_check("cos32 C deg3", f, LO, ZMAX, 3)

ZT = tan(pi / 8) ** 2             # atanf direct interval (Cephes split)
f = lambda z: (atan(sqrt(z)) - sqrt(z)) / (z * sqrt(z))
p_atan32 = fit_and_check("atan32 A deg4", f, LO, ZT, 4)

RL = log(2) / 2
f = lambda r: (exp(r) - 1 - r) / (r * r) if r != 0 else mpf("0.5")
p_exp32 = fit_and_check("exp32 P deg5", f, -RL, RL, 5)

f = lambda z: (log((1 + sqrt(z)) / (1 - sqrt(z))) / (2 * sqrt(z)) - 1) / z
p_log32 = fit_and_check("log32 L deg3", f, LO, SMAX * SMAX, 3)

# ---- emit ----
emit("sin64 P", p_sin64)
emit("cos64 C", p_cos64)
emit("atan64 A", p_atan64)
emit("log64 L", p_log64)
emit("sin32 P", p_sin32, f32=True)
emit("cos32 C", p_cos32, f32=True)
emit("atan32 A", p_atan32, f32=True)
emit("exp32 P", p_exp32, f32=True)
emit("log32 L", p_log32, f32=True)

print("\n/* atan64 reduction table splits: atan(0.5), atan(1), atan(1.5), pi/2 */")
for v in [atan(mpf("0.5")), atan(mpf(1)), atan(mpf("1.5")), pi / 2]:
    hi = float(v)
    lo = float(v - mpf(hi))
    print(f"    {hi.hex()}, {lo.hex()},")

# f32 splits used by kernels
print("\n/* f32 constants */")
for nm, v in [("pio2", pi / 2), ("pi", pi), ("pio4", pi / 4),
              ("pi3o4", 3 * pi / 4), ("ln2", log(2))]:
    print(nm, f32_round(v).hex() + "f")
# f32 Cody-Waite split of pi/2 (3 words)
r = pi / 2
w1 = f32_round(r); r -= mpf(w1)
w2 = f32_round(r); r -= mpf(w2)
w3 = f32_round(r); r -= mpf(w3)
print("pio2 f32 3-word:", w1.hex() + "f,", w2.hex() + "f,", w3.hex() + "f,",
      " resid:", mp.nstr(r, 2))
# f32 ln2 split
r = log(2)
h1 = f32_round(r); r -= mpf(h1)
h2 = f32_round(r); r -= mpf(h2)
print("ln2 f32 2-word:", h1.hex() + "f,", h2.hex() + "f,", " resid:", mp.nstr(r, 2))
# pi f64 hi/lo for atan2
r = pi
h1 = float(r); r -= mpf(h1)
print("pi f64 hi/lo:", h1.hex(), ",", float(r).hex())
