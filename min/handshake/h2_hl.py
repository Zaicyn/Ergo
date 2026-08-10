#!/usr/bin/env python3
"""h2_hl.py — Stage 1: analytic Heitler-London ladder for H2.

Closed-form 1s-STO Heitler-London E(R, zeta):

    Psi_g = [a(1)b(2) + b(1)a(2)] / sqrt(2(1+S^2))
    E_g = (H_aa + H_ab)/(1+S^2),  E_t = (H_aa - H_ab)/(1-S^2)

with (x = zeta*R, a.u.):
    S   = e^-x (1 + x + x^2/3)
    A   = (1/R)[1 - e^-2x (1 + x)]                      <a|1/r_b|a>
    B   = zeta (1 + x) e^-x                             <a|1/r_b|b>
    J   = (1/R)[1 - e^-2x (1 + 11x/8 + 3x^2/4 + x^3/6)] (aa|r12|bb)
    K   = (zeta/120)(75 - 138x - 72x^2 - 8x^3) e^-2x
          + (2 zeta/(15 x)) [ e^{2x}(3-3x+x^2)^2 Ei(-4x)
          - 2(9-3x^2+x^4) Ei(-2x)
          + e^{-2x}(3+3x+x^2)^2 (gamma_E + ln x) ]      (ab|r12|ab)
    H_aa = 2 E_1s - 2A + J + 1/R,   E_1s = zeta^2/2 - zeta
    H_ab = -zeta^2 S^2 + 2(zeta-1) S B - 2 S B + K + S^2/R

CRITICAL DETAIL: the cross one-electron element <a|h_a|b> for
zeta != 1 is NOT E_1s*S (the 1s STO is an eigenfunction only at
zeta=1). <a|-Laplacian/2|b> = -zeta^2 S/2 + zeta B, so
<a|h_a|b> = -zeta^2 S/2 + (zeta-1) B. At zeta=1 the correction
term 2(zeta-1)SB vanishes and the naive 2 E_1s S^2 - 2SB form is
recovered (rung 1 was right by accident of zeta=1).

Formulas: homes.nano.aau.dk/tgp/master_2024.pdf (S/J/K for 1s STOs).
All integrals verified numerically (prolate quadrature S/A/B to 1e-3,
Poisson-convolution K to 3e-3) at (zeta=1, R=2) and
(zeta=1.166, R=1.406).

Ladder (targets, sourced):
  rung 1 HL minimal (zeta=1):   D_e 3.13-3.16 eV, R_e 1.64 bohr
    [IUPAC 1970 review table: HL/Sugiura 3.13 eV, 0.87 A]
  rung 2 Wang (zeta optimized): D_e 3.78 eV, zeta* 1.166,
    R_e 0.744 A  [Levine QC 13.101: "The optimum value of zeta is
    1.166 at R_e, and D_e and R_e are improved to 3.78 eV and 0.744 A"]
  rung 3 Weinbaum (+ionic CI in {cov, ion}): HL+ionic ~3.2 eV
    (zeta=1) [IUPAC: HL+ionic Weinbaum 3.21 eV, 0.90 A];
    Wang+ionic ~4.0 eV [IUPAC: Wang+ionic Weinbaum 4.00 eV, 0.74 A]
  exact:                        D_e 4.7475 eV, R_e 1.4011 bohr
    [Kolos-Wolniewicz; Coolidge-James 4.72]

Determinism: fixed grids, no RNG; run twice byte-identical.
"""
import numpy as np
from scipy.special import expi

GAMMA = 0.5772156649015329
EV = 27.211386245988
ANG = 0.5291772109


# ---------- closed forms ----------

def S_ovl(z, R):
    x = z * R
    return np.exp(-x) * (1.0 + x + x * x / 3.0)


def A_atr(z, R):
    x = z * R
    return (1.0 - np.exp(-2.0 * x) * (1.0 + x)) / R


def B_atr(z, R):
    x = z * R
    return z * (1.0 + x) * np.exp(-x)


def J_dir(z, R):
    x = z * R
    return (1.0 - np.exp(-2.0 * x) * (1.0 + 11.0 * x / 8.0
                                      + 0.75 * x * x + x ** 3 / 6.0)) / R


def K_exc(z, R):
    x = z * R
    t1 = (z / 120.0) * (75.0 - 138.0 * x - 72.0 * x ** 2 - 8.0 * x ** 3) \
        * np.exp(-2.0 * x)
    t2 = (2.0 * z / (15.0 * x)) * (
        np.exp(2.0 * x) * (3.0 - 3.0 * x + x ** 2) ** 2 * expi(-4.0 * x)
        - 2.0 * (9.0 - 3.0 * x ** 2 + x ** 4) * expi(-2.0 * x)
        + np.exp(-2.0 * x) * (3.0 + 3.0 * x + x ** 2) ** 2
        * (GAMMA + np.log(x)))
    return t1 + t2


def E_hl(z, R, triplet=False):
    E1s = 0.5 * z * z - z
    S = S_ovl(z, R)
    Haa = 2.0 * E1s - 2.0 * A_atr(z, R) + J_dir(z, R) + 1.0 / R
    Hab = -z * z * S * S + 2.0 * (z - 1.0) * S * B_atr(z, R) \
        - 2.0 * S * B_atr(z, R) + K_exc(z, R) + S * S / R
    if triplet:
        return (Haa - Hab) / (1.0 - S * S)
    return (Haa + Hab) / (1.0 + S * S)


# ---------- prolate quadrature + Poisson oracle ----------

def prolate(z, R, n=100, xi_max=12.0):
    xi = 1.0 + (np.arange(n) + 0.5) * ((xi_max - 1.0) / n)
    et = np.linspace(-1.0 + 0.5 / n, 1.0 - 0.5 / n, n)
    XI, ET = np.meshgrid(xi, et, indexing="ij")
    c = R / 2.0
    ra = c * (XI - ET)
    rb = c * (XI + ET)
    jac = c ** 3 * (XI ** 2 - ET ** 2) * 2.0 * np.pi \
        * (xi[1] - xi[0]) * (et[1] - et[0])
    norm = z ** 3 / np.pi
    fa = np.sqrt(norm) * np.exp(-z * ra)
    fb = np.sqrt(norm) * np.exp(-z * rb)
    return fa, fb, jac, XI, ET, c


def quad_oracle(z, R):
    fa, fb, jac, XI, ET, c = prolate(z, R)
    I = lambda f: float((f * jac).sum())
    S_n = I(fa * fb)
    A_n = I(fa * fa / (c * (XI + ET)))
    B_n = I(fa * fb / (c * (XI + ET)))
    # Poisson route for K: field of rho_ab on the prolate grid
    ph = np.linspace(0.0, 2.0 * np.pi, 24, endpoint=False)
    SRC, W = [], []
    rho = fa * fb
    for p in ph:
        XS = c * np.sqrt((XI ** 2 - 1) * (1 - ET ** 2)) * np.cos(p)
        YS = c * np.sqrt((XI ** 2 - 1) * (1 - ET ** 2)) * np.sin(p)
        ZS = c * XI * ET
        SRC.append(np.stack([XS.ravel(), YS.ravel(), ZS.ravel()], axis=1))
        W.append((rho * (jac / len(ph))).ravel())
    SRC = np.concatenate(SRC, axis=0)
    W = np.concatenate(W)
    XX = c * np.sqrt((XI ** 2 - 1) * (1 - ET ** 2))
    ZZ = c * XI * ET
    T = np.stack([XX.ravel(), np.zeros(XX.size), ZZ.ravel()], axis=1)
    out = np.zeros(T.shape[0])
    for k0 in range(0, T.shape[0], 256):
        k1 = min(k0 + 256, T.shape[0])
        d = np.sqrt(((T[k0:k1, None, :] - SRC[None, :, :]) ** 2).sum(axis=2))
        d = np.maximum(d, 0.05)
        out[k0:k1] = (W[None, :] / d).sum(axis=1)
    phi = out.reshape(XX.shape)
    K_n = float((rho * phi * jac).sum())
    # J_dir = (aa|r12|bb): field of rho_bb on rho_aa; also phi_aa for M
    rho_b2 = fb * fb
    W2 = []
    for p in ph:
        W2.append((rho_b2 * (jac / len(ph))).ravel())
    W2 = np.concatenate(W2)
    out2 = np.zeros(T.shape[0])
    for k0 in range(0, T.shape[0], 256):
        k1 = min(k0 + 256, T.shape[0])
        d = np.sqrt(((T[k0:k1, None, :] - SRC[None, :, :]) ** 2).sum(axis=2))
        d = np.maximum(d, 0.05)
        out2[k0:k1] = (W2[None, :] / d).sum(axis=1)
    phi2 = out2.reshape(XX.shape)
    J_n = float((rho2_dummy * phi2 * jac).sum()) if False else \
        float((fa * fa * phi2 * jac).sum())
    # mixed M = <ab|r12|aa> = int rho_ab phi_aa (field of rho_aa)
    W3 = []
    rho_a2 = fa * fa
    for p in ph:
        W3.append((rho_a2 * (jac / len(ph))).ravel())
    W3 = np.concatenate(W3)
    out3 = np.zeros(T.shape[0])
    for k0 in range(0, T.shape[0], 256):
        k1 = min(k0 + 256, T.shape[0])
        d = np.sqrt(((T[k0:k1, None, :] - SRC[None, :, :]) ** 2).sum(axis=2))
        d = np.maximum(d, 0.05)
        out3[k0:k1] = (W3[None, :] / d).sum(axis=1)
    phi3 = out3.reshape(XX.shape)
    M_n = float((rho * phi3 * jac).sum())
    return S_n, A_n, B_n, J_n, K_n, M_n


def E_ion(z, R):
    """Ionic structure energy: a(1)a(2) (or b(1)b(2)).
    (1s1s|1s1s) = 5 zeta/8 (closed form)."""
    E1s = 0.5 * z * z - z
    return 2.0 * E1s - 2.0 * A_atr(z, R) + 5.0 * z / 8.0 + 1.0 / R


def weinbaum(z, R, M):
    """2x2 nonorthogonal CI in {cov, ion}. M = <ab|r12|aa>."""
    S = S_ovl(z, R)
    E1s = 0.5 * z * z - z
    Ec = E_hl(z, R)
    Ei = E_ion(z, R)
    # <ab|H|aa> = 2 E1s S - S(A+B) + M + S/R
    Hx = 2.0 * E1s * S - S * (A_atr(z, R) + B_atr(z, R)) + M + S / R
    N = 2.0 * S * S / (1.0 + S * S)
    Hc = 2.0 * Hx / (1.0 + S * S)
    H = np.array([[Ec, Hc], [Hc, Ei]])
    O = np.array([[1.0, N], [N, 1.0]])
    from scipy.linalg import sqrtm
    from numpy.linalg import eigvals, inv
    w = eigvals(inv(sqrtm(O)) @ H @ inv(sqrtm(O)))
    return float(w.real.min()), H, O


def main():
    print("=" * 66)
    print("H2 HEITLER-LONDON LADDER (analytic, closed-form)")
    print("=" * 66)

    # ---------- internal oracle ----------
    print("\n[oracle: quadrature check]")
    for (z, R) in [(1.0, 2.0), (1.166, 1.4058)]:
        Sn, An, Bn, Jn, Kn, Mn = quad_oracle(z, R)
        print(f"  z={z}, R={R}:")
        print(f"    S {S_ovl(z, R):.5f}/{Sn:.5f}  A {A_atr(z, R):.5f}/{An:.5f}"
              f"  B {B_atr(z, R):.5f}/{Bn:.5f}")
        print(f"    J {J_dir(z, R):.5f}/{Jn:.5f}  K {K_exc(z, R):.5f}/{Kn:.5f}"
              f"  M -/{Mn:.5f}")

    # ---------- ladder ----------
    print("\n[ladder]")
    Rs = np.linspace(1.0, 3.0, 801)
    Es = np.array([E_hl(1.0, r) for r in Rs])
    i = int(np.argmin(Es))
    Re, Ee = Rs[i], Es[i]
    De = -(Ee + 1.0) * EV
    print(f"  rung 1 (HL, zeta=1): R_e = {Re:.3f} bohr = {Re * ANG:.3f} A, "
          f"D_e = {De:.4f} eV")
    print(f"    targets: 3.13-3.16 eV @ 1.64 bohr; missing "
          f"{4.7475 - De:.4f} eV vs exact")
    # rung 2: Wang
    Rw = 1.4058
    zs = np.linspace(1.05, 1.30, 1001)
    Ez = np.array([E_hl(zz, Rw) for zz in zs])
    zstar = zs[int(np.argmin(Ez))]
    Ew = E_hl(zstar, Rw)
    Dw = -(Ew + 1.0) * EV
    print(f"  rung 2 (Wang): zeta* = {zstar:.4f} (target 1.166), "
          f"D_e = {Dw:.4f} eV at R = {Rw:.4f} bohr = {Rw * ANG:.4f} A")
    # Wang equilibrium
    Esw = np.array([E_hl(zstar, r) for r in Rs])
    iw = int(np.argmin(Esw))
    print(f"    Wang R_e at zeta*: {Rs[iw]:.3f} bohr = {Rs[iw] * ANG:.3f} A "
          f"(target 0.744 A); missing {4.7475 - Dw:.4f} eV")
    # rung 3: Weinbaum
    print("  rung 3 (Weinbaum cov+ion CI):")
    for z in (1.0, zstar):
        Mn = quad_oracle(z, Rw)[5]
        Ewb, H, O = weinbaum(z, Rw, Mn)
        Dwb = -(Ewb + 1.0) * EV
        print(f"    zeta={z:.4f}: D_e = {Dwb:.4f} eV at R = {Rw:.4f} bohr "
              f"(M = {Mn:.5f})")
        from scipy.linalg import sqrtm as _sq
        Wf, Vf = np.linalg.eig(np.linalg.inv(_sq(O)) @ H
                               @ np.linalg.inv(_sq(O)))
        c1, c2 = Vf[:, int(np.argmin(Wf.real))].real
        print(f"    cov/ion coefficients: {c1:.4f} / {c2:.4f}")
    print("    targets: HL+ionic ~3.21 eV (IUPAC); Wang+ionic 4.00 eV "
          "(IUPAC); Rosen polarization 4.02 eV (out of ionic scope)")


if __name__ == "__main__":
    main()
