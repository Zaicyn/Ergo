#!/usr/bin/env python3
"""wigner_mirror_w4.py -- Stage W4 mirror: heteronuclear handshake (HeH2+).

One electron, two centers: He (Z=2) at z=-R/2, H (Z=1) at z=+R/2.
No inversion symmetry -> no parity. States are 1sigma (ground) and 2sigma
(excited) from a 2x2 generalized eigenproblem in the 1s-STO basis
  phi_A = sqrt(zA^3/pi) exp(-zA rA),  zA=2 ;  phi_B, zB=1
with matrix elements integrated deterministically in prolate spheroidal
coordinates (Gauss-Legendre; no RNG, run twice -> byte-identical).

With zeta=Z the matrix elements collapse:
  H_AA = -zA^2/2 - ZB <1/rB>_AA       H_BB = -zB^2/2 - ZA <1/rA>_BB
  H_AB = -zB^2/2 S_AB - ZA <1/rA>_AB (and symmetric check via zA)

Oracles: E(R) scan (picks the engine R list), then per (R, state) the
bond-axis Wigner map W(z,p) built exactly as in wigner_mirror.py:
reduced coherence rho(z,z') = int dxdy psi psi', direct FFT DFT,
full-Nyquist p so WNORM=1 is exact.

Heteronuclear observables (the W4 physics):
  - W(0,0) is no longer +/-1/pi: it measures the asymmetry of the bond
    midpoint coherence.
  - fringes are asymmetric: p_fringe(z>0 side) != |p_fringe(z<0 side)|.
  - the 2sigma "node pocket" drifts off origin toward the H side.

Usage:
  python wigner_mirror_w4.py scan              # E(R) for both states
  python wigner_mirror_w4.py oracles           # Wigner oracle table
  python wigner_mirror_w4.py compare wmap.txt R state   # state: 1 or 2
"""
import sys
import numpy as np
from numpy.polynomial.legendre import leggauss

ZA, ZB = 2.0, 1.0          # He at z=-R/2, H at z=+R/2
ZETA_A, ZETA_B = 2.0, 1.0  # 1s-STO exponents (= Z: H_AB collapses)

# Wigner grid: same geometry as wigner_mirror.py
XT = np.linspace(-6, 6, 64)
ZT = np.linspace(-8, 8, 256)
DX = XT[1] - XT[0]
DZ = ZT[1] - ZT[0]
X, Y, ZG = np.meshgrid(XT, XT, ZT, indexing="ij")

# prolate spheroidal quadrature (deterministic)
NMU, NNU, NPHI = 96, 64, 16
MU_MAX = 24.0  # mu = (rA+rB)/R; covers the box for R >= 0.5
_mu, _wmu = leggauss(NMU)
_nu, _wnu = leggauss(NNU)


def mat_elems(R):
    """S_AB, <1/rA>_AB, <1/rB>_AA, <1/rA>_BB by prolate quadrature."""
    # mu in [1, MU_MAX]: map Gauss nodes
    mu = 1.0 + 0.5 * (MU_MAX - 1.0) * (_mu + 1.0)
    wmu = 0.5 * (MU_MAX - 1.0) * _wmu
    nu, wnu = _nu, _wnu
    MU, NU = np.meshgrid(mu, nu, indexing="ij")
    W2 = np.outer(wmu, wnu) * 2.0 * np.pi * (R / 2.0) ** 3 * (MU**2 - NU**2)
    RA = R * (MU + NU) / 2.0
    RB = R * (MU - NU) / 2.0
    na = np.sqrt(ZETA_A**3 / np.pi)
    nb = np.sqrt(ZETA_B**3 / np.pi)
    PA = na * np.exp(-ZETA_A * RA)
    PB = nb * np.exp(-ZETA_B * RB)
    def integ(F):
        return np.sum(W2 * F)
    S = integ(PA * PB)
    IAB_A = integ(PA * PB / RA)
    IAB_B = integ(PA * PB / RB)
    IAA_B = integ(PA * PA / RB)
    IBB_A = integ(PB * PB / RA)
    return S, IAB_A, IAB_B, IAA_B, IBB_A


def states(R):
    """Solve the 2x2 generalized eigenproblem. Returns (E1, E2, c1, c2)."""
    S, IAB_A, IAB_B, IAA_B, IBB_A = mat_elems(R)
    HAA = -ZETA_A**2 / 2.0 - ZB * IAA_B
    HBB = -ZETA_B**2 / 2.0 - ZA * IBB_A
    HAB = -ZETA_B**2 / 2.0 * S - ZA * IAB_A
    H = np.array([[HAA, HAB], [HAB, HBB]])
    Sm = np.array([[1.0, S], [S, 1.0]])
    # generalized eigh via Cholesky
    L = np.linalg.cholesky(Sm)
    Li = np.linalg.inv(L)
    Ht = Li @ H @ Li.T
    ev, V = np.linalg.eigh(Ht)
    C = Li.T @ V
    return ev[0], ev[1], C[:, 0], C[:, 1]


def psi3d(R, c):
    """Bonding/antibonding orbital on the 3D grid, normalized to 1."""
    rA = np.sqrt(X**2 + Y**2 + (ZG + R / 2.0) ** 2)
    rB = np.sqrt(X**2 + Y**2 + (ZG - R / 2.0) ** 2)
    pa = np.sqrt(ZETA_A**3 / np.pi) * np.exp(-ZETA_A * rA)
    pb = np.sqrt(ZETA_B**3 / np.pi) * np.exp(-ZETA_B * rB)
    psi = c[0] * pa + c[1] * pb
    nrm = np.sqrt(np.sum(psi * psi) * DX * DX * DZ)
    return psi / nrm


def rho1d(R, c):
    psi = psi3d(R, c)
    rho = np.einsum("xyz,xyw->zw", psi, psi) * DX * DX
    return rho / (np.trace(rho) * DZ)


def wigner_from_rdm(rho, nfft=2048):
    NZ = rho.shape[0]
    W = np.zeros((NZ, nfft))
    for iz in range(NZ):
        m = min(iz, NZ - 1 - iz)
        k = np.arange(-m, m + 1)
        ry = rho[iz - k, iz + k]
        buf = np.zeros(nfft)
        buf[0 : m + 1] = ry[m:]
        buf[nfft - m :] = ry[:m]
        W[iz] = np.fft.fft(buf).real * DZ / np.pi
    p = -np.pi * np.fft.fftfreq(nfft, d=DZ)
    return np.fft.fftshift(W, axes=1), np.fft.fftshift(p)


def oracle_row(R, state):
    E1, E2, c1, c2 = states(R)
    c, E = (c1, E1) if state == 1 else (c2, E2)
    rho = rho1d(R, c)
    W, p = wigner_from_rdm(rho)
    iz0 = len(ZT) // 2
    ip0 = np.argmin(np.abs(p))
    w00 = W[iz0, ip0]
    # fringe scan: p in [-3, 3] excluding a small core window
    pm = (p >= -3.0) & (p <= 3.0) & (np.abs(p) > 0.15)
    w0 = W[iz0][pm]
    pp = p[pm]
    imin = np.argmin(w0)
    # charge asymmetry: population on each center (Mulliken halves)
    S, *_ = mat_elems(R)
    popA = c[0] ** 2 + c[0] * c[1] * S
    return E, w00, pp[imin], w0[imin], popA


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "scan":
        print("R        E_1sigma        E_2sigma")
        for R in [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0,
                  3.5, 4.0, 5.0, 6.0, 8.0]:
            E1, E2, _, _ = states(R)
            print(f"{R:6.2f}  {E1:+.10f}  {E2:+.10f}")
        print("united atom (R->0): E1 -> -Z^2/2 with Z=3 (Li2+) = -4.5")
        print("separated (R->inf): E1 -> -2.0 (He+ 1s), E2 -> -0.5 (H 1s)")
        return
    if len(sys.argv) >= 2 and sys.argv[1] == "oracles":
        print("R      st  E             W(0,0)        p_fringe    W_fringe"
              "    popA(He)")
        for R in [0.75, 1.0, 1.5, 2.0, 3.0, 4.0]:
            for st in (1, 2):
                E, w00, pf, wf, pa = oracle_row(R, st)
                print(f"{R:5.2f}  {st}   {E:+.10f}  {w00:+.8f}  "
                      f"{pf:+.6f}   {wf:+.8f}   {pa:.6f}")
        print(f"1/pi = {1/np.pi:.16f}")
        return
    if len(sys.argv) >= 5 and sys.argv[1] == "compare":
        path, R, state = sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
        E1, E2, c1, c2 = states(R)
        rho = rho1d(R, c1 if state == 1 else c2)
        W, p = wigner_from_rdm(rho)
        worst, n = 0.0, 0
        for line in open(path):
            line = line.strip().strip("()").replace("'", " ")
            f = line.split()
            if len(f) != 6 or f[0] != "WMAP":
                continue
            if abs(float(f[1]) - R) > 1e-9 or int(f[2]) != state:
                continue
            iz = np.argmin(np.abs(ZT - float(f[3])))
            ip = np.argmin(np.abs(p - float(f[4])))
            worst = max(worst, abs(W[iz, ip] - float(f[5])))
            n += 1
        print(f"compared {n} WMAP rows, max abs diff = {worst:.6e}")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
