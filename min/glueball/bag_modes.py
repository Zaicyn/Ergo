#!/usr/bin/env python3
"""bag_modes.py — Stage 1: MIT-bag two-gluon glueballs.

Exact cavity-mode arithmetic (no fits):
  TE_l modes:  d/dx [x j_l(x)] = 0   ->  l=1: x = 2.7437 (verified below)
  TM_l modes:  j_l(x) = 0            ->  l=1: x = 4.4934 (verified below)
(j1(x) = sin x / x^2 - cos x / x; roots by bisection on the analytic
functions, printed against the sourced literature values.)

Two-gluon glueball energy (DeGrand, Jaffe, Johnson, Kiskis,
Phys. Rev. D 12 (1975) 2060):

  E(R) = (x1 + x2)/R + (4 pi/3) B R^3 - z0/R

minimized over R:  R*^4 = Omega/(4 pi B),  E_min = (4/3) Omega/R*,
Omega = x1 + x2 - z0.  Parameters are the DeGrand-Jaffe hadron-fit
values (inputs, not tuned to anything):  B^{1/4} = 146 MeV,
z0 = 1.84, and their alpha_s = 0.55 enters only the color-magnetic
splitting which we do NOT recompute — the DeGrand et al. final
(split) masses are quoted as the literature comparison and the
implied magnetic coefficients are reported, not fitted.

  TE+TE -> 0++ and 2++ (degenerate before magnetic splitting)
  TE+TM -> 0-+ and 2-+ (degenerate before magnetic splitting)

LQCD ordering oracle: 0++ ~ 1.6-1.7 GeV < 2++ ~ 2.2-2.4 <
0-+ ~ 2.3-2.6 GeV (BESIII PRL 132, 181901 cites 2.395 +/- 0.014 GeV
for the lightest pseudoscalar).  The bag's known pseudoscalar problem:
TE+TM lands ~ 1.3 GeV, a factor ~2 too light — measured here, not
assumed.

Determinism: pure arithmetic; run twice, byte-identical.
"""

import math


def j1(x):
    return math.sin(x) / x ** 2 - math.cos(x) / x


def d_xj1(x):
    # d/dx [x j1(x)] = d/dx [sin x / x - cos x]
    return (x * math.cos(x) - math.sin(x)) / x ** 2 + math.sin(x)


def bisect(f, a, b, tol=1e-15):
    fa, fb = f(a), f(b)
    assert fa * fb < 0.0
    for _ in range(200):
        m = 0.5 * (a + b)
        fm = f(m)
        if fa * fm <= 0.0:
            b, fb = m, fm
        else:
            a, fa = m, fm
        if b - a < tol:
            break
    return 0.5 * (a + b)


def bag_mass(x1, x2, z0, B14):
    """Return (R* in GeV^-1, E_min in GeV) for Omega = x1+x2-z0."""
    B = B14 ** 4
    omega = x1 + x2 - z0
    R = (omega / (4.0 * math.pi * B)) ** 0.25
    E = 4.0 * omega / (3.0 * R)
    return R, E


def main():
    print("=" * 66)
    print("STAGE 1 — MIT BAG TWO-GLUON GLUEBALLS (arithmetic, no fits)")
    print("=" * 66)

    # cavity zeros
    x_te = bisect(d_xj1, 2.0, 3.5)
    x_tm = bisect(j1, 3.5, 5.0)
    print("\n[cavity zeros, l=1]")
    print(f"  TE_1: d(x j1)/dx = 0  ->  x = {x_te:.6f}  "
          f"(literature 2.7437, dev {x_te - 2.7437:+.5f})")
    print(f"  TM_1: j1(x) = 0     ->  x = {x_tm:.6f}  "
          f"(literature 4.4934, dev {x_tm - 4.4934:+.5f})")

    Z0 = 1.84
    B14 = 0.146  # GeV
    print(f"\n[bag parameters, inputs from DeGrand-Jaffe hadron fit]")
    print(f"  B^(1/4) = {B14 * 1000:.0f} MeV, z0 = {Z0}, "
          f"alpha_s = 0.55 (magnetic split, literature only)")

    combos = [
        ("TE+TE", "0++ / 2++ (degenerate)", 2 * x_te),
        ("TE+TM", "0-+ / 2-+ (degenerate)", x_te + x_tm),
    ]
    print("\n[two-gluon minima]")
    for name, states, xsum in combos:
        R, E = bag_mass(xsum, 0.0, Z0, B14)
        R_fm = R * 0.1973269804
        print(f"  {name} -> {states}:")
        print(f"    Omega = {xsum:.4f} - {Z0} = {xsum - Z0:.4f}, "
              f"R* = {R:.3f} GeV^-1 = {R_fm:.3f} fm")
        print(f"    E_min = {E:.4f} GeV")

    print("\n[literature comparison: DeGrand et al. PRD 12 (1975) 2060,")
    print(" final masses WITH color-magnetic splitting, alpha_s = 0.55]")
    degrand = [("0++", 0.96), ("2++", 1.29), ("0-+", 1.30),
               ("2-+", 1.66)]
    for st, m in degrand:
        print(f"  {st}: {m:.2f} GeV")
    print("  implied magnetic shifts vs our degenerate minima:")
    print(f"    0++: 0.96 vs 0.97 computed (magnetic ~ 0)  ;")
    print(f"    2++: 1.29 vs 0.97 computed -> split +0.33 GeV")
    print(f"    2-+: 1.66 vs 1.30 computed -> split +0.36 GeV")

    print("\n[ordering verdict vs LQCD oracle]")
    print("  LQCD: 0++ ~1.6-1.7 < 2++ ~2.2-2.4 < 0-+ ~2.3-2.6 GeV")
    print("  BESIII X(2370): 2395 +/- 11(stat) +26/-94(syst) MeV, 0-+")
    print("  bag:  0++ = 2++ = 0.97 (pre-split) ; 0-+ = 1.30")
    print("  -> scalar ~40% LIGHT vs LQCD even before splitting;")
    print("     pseudoscalar 1.30 GeV vs LQCD 2.3-2.6: a factor ~1.9")
    print("     too light = the bag model's known pseudoscalar problem")
    print("     (no mechanism pushes 0-+ up; B and z0 are hadron-fit,")
    print("     residual reported, not fitted).")
    print("  -> ordering 0++ ~ 2++ < 0-+ preserved (magnetic splitting")
    print("     separates 0++/2++ the right way: 2++ pushed UP).")


if __name__ == "__main__":
    main()
