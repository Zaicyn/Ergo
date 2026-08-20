#!/usr/bin/env python3
"""ceiling.py — Stage 2: re-measure the one-electron-ion ceiling with
the exact Dirac-Coulomb (Sommerfeld) corrections, not the (Z alpha)^2
order-of-magnitude.

The old census ceiling (atomhopf): "(Z alpha)^2 correction to Ly-alpha
passes 1% at Z > 13.7" — a pure (Z alpha)^2 = 0.01 estimate. Here we
compute the exact all-orders Dirac corrections:
  - 1s binding:  Schro -Z^2/2  vs Dirac (1 - sqrt(1-(Za)^2)) c^2
  - Ly-alpha:    Schro 3 Z^2/8 vs Dirac bind(1s) - bind(2p1/2)
and find where the Schroedinger error passes 1%.

Engine anchor: dirac_radial.ergo measures Z=14 1s and 2p1/2 directly
(deviations from the formula ~1e-11 Ha); the formula is the validated
closed form, used here across the table. Determinism: pure arithmetic.
"""

C = 137.035999084  # 1/alpha, CODATA (same value the engine carries)


def dirac_bind(Z, n, kap):
    """Exact Sommerfeld binding (Ha), point nucleus, all orders."""
    d = n - abs(kap) + (kap * kap - (Z / C) ** 2) ** 0.5
    e = 1.0 / (1.0 + (Z / C) ** 2 / (d * d)) ** 0.5
    return (1.0 - e) * C * C


def main():
    print("=" * 66)
    print("STAGE 2 — one-electron-ion ceiling, exact Dirac re-measure")
    print("=" * 66)
    print("(old census statement: (Z alpha)^2 = 0.01 at Z = 13.7)")
    print()
    print("   Z    Ly-a err %% (1s-dominated)   1s err %%")
    cross_lya = None
    cross_1s = None
    for Z in range(1, 103):
        sch_lya = 3.0 * Z * Z / 8.0
        dir_lya = dirac_bind(Z, 1, -1) - dirac_bind(Z, 2, 1)
        err_lya = abs(dir_lya - sch_lya) / dir_lya
        sch_1s = Z * Z / 2.0
        dir_1s = dirac_bind(Z, 1, -1)
        err_1s = abs(dir_1s - sch_1s) / dir_1s
        if cross_lya is None and err_lya > 0.01:
            cross_lya = Z
        if cross_1s is None and err_1s > 0.01:
            cross_1s = Z
        if Z in (2, 10, 13, 14, 26, 54, 82, 92):
            print(f"  {Z:3d}    {100 * err_lya:8.4f}"
                  f"                 {100 * err_1s:8.4f}")
    print()
    print(f"  1% Ly-a crossing (exact Dirac): Z = {cross_lya}")
    print(f"  1% 1s  crossing (exact Dirac): Z = {cross_1s}")
    print("  Engine anchors (dirac_radial.ergo, deviations from the")
    print("  formula ~1e-11 Ha): Z=14 1s = 98.257056 Ha, "
          "2p1/2 = 24.580351 Ha")


if __name__ == "__main__":
    main()
