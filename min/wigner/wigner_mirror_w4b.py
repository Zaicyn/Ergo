#!/usr/bin/env python3
"""wigner_mirror_w4b.py -- Stage W4 mirror, PATCHED basis (2026-08-22).

wigner_mirror_w4.py's 2x1s LCAO was qualitatively wrong for the 2sigma
state below R~2: at small R the exact 2sigma is united-atom 2p-like
(node plane through the bond; the h4p_wig engine found W(0,0) = -0.2675
at R=0.75 where the 2-fn mirror said +0.056). Patch: add a 2p_z STO at
the MIDPOINT with zeta = 3/2 (exact Li2+ 2p as R -> 0):

  basis:  a = 1s on He (z=2)   b = 1s on H (z=1)   c = 2p_z on mid (z=1.5)

Kinetic operators stay multiplicative:
  1s:  -1/2 lap (e^-zr)      = (-z^2/2 + z/r)   e^-zr
  2pz: -1/2 lap (z e^-zr)    = (-z^2/2 + 2z/r)  z e^-zr
so every matrix element is a prolate-spheroidal quadrature of products
(r_mid^2 = (R/2)^2 (mu^2 + nu^2 - 1) closes in mu,nu). Deterministic
Gauss-Legendre, no RNG, run twice -> byte-identical.

States: 1sigma = eigenvalue 1, 2sigma = eigenvalue 2 of the 3x3
generalized problem H c = E S c (H symmetrized after quadrature).

Usage: same CLI as wigner_mirror_w4.py (scan / oracles / compare).
"""
import sys
import numpy as np
from numpy.polynomial.legendre import leggauss

ZA, ZB = 2.0, 1.0          # He at z=-R/2, H at z=+R/2
ZETA = [2.0, 1.0, 1.5]     # 1s_He, 1s_H, 2pz_mid
CTYPE = [0, 0, 1]          # 0 = 1s, 1 = 2p_z

# Wigner grid: same geometry as wigner_mirror.py / wigner_mirror_w4.py
XT = np.linspace(-6, 6, 64)
ZT = np.linspace(-8, 8, 256)
DX = XT[1] - XT[0]
DZ = ZT[1] - ZT[0]
X, Y, ZG = np.meshgrid(XT, XT, ZT, indexing="ij")

NMU, NNU = 128, 96
MU_MAX = 24.0
_mu, _wmu = leggauss(NMU)
_nu, _wnu = leggauss(NNU)


def prolate(R):
    mu = 1.0 + 0.5 * (MU_MAX - 1.0) * (_mu + 1.0)
    wmu = 0.5 * (MU_MAX - 1.0) * _wmu
    MU, NU = np.meshgrid(mu, _nu, indexing="ij")
    W2 = np.outer(wmu, _wnu) * 2.0 * np.pi * (R / 2.0) ** 3 \
        * (MU**2 - NU**2)
    RA = R * (MU + NU) / 2.0
    RB = R * (MU - NU) / 2.0
    RMID = (R / 2.0) * np.sqrt(MU**2 + NU**2 - 1.0)
    ZMID = R * MU * NU / 2.0
    return W2, RA, RB, RMID, ZMID


def basis_vals(R):
    """All basis functions on the prolate grid. Returns list of arrays."""
    W2, RA, RB, RMID, ZMID = prolate(R)
    fa = np.sqrt(ZETA[0]**3 / np.pi) * np.exp(-ZETA[0] * RA)
    fb = np.sqrt(ZETA[1]**3 / np.pi) * np.exp(-ZETA[1] * RB)
    fc = np.sqrt(ZETA[2]**5 / np.pi) * ZMID * np.exp(-ZETA[2] * RMID)
    return [fa, fb, fc], (W2, RA, RB, RMID)


def kinetic_factor(j, R):
    """Function F such that -1/2 lap phi_j = F * phi_j (multiplicative)."""
    _, RA, RB, RMID = basis_vals(R)[1]
    z = ZETA[j]
    if CTYPE[j] == 0:
        r = RA if j == 0 else RB
        return -z * z / 2.0 + z / r
    return -z * z / 2.0 + 2.0 * z / RMID


def states(R):
    F, (W2, RA, RB, _) = basis_vals(R)
    n = len(F)
    S = np.zeros((n, n))
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            S[i, j] = np.sum(W2 * F[i] * F[j])
            KF = kinetic_factor(j, R)
            H[i, j] = np.sum(W2 * F[i] * F[j]
                             * (KF - ZA / RA - ZB / RB))
    H = 0.5 * (H + H.T)  # quadrature symmetrization
    L = np.linalg.cholesky(S)
    Li = np.linalg.inv(L)
    ev, V = np.linalg.eigh(Li @ H @ Li.T)
    C = Li.T @ V
    return ev, C


def psi3d(R, c):
    rA = np.sqrt(X**2 + Y**2 + (ZG + R / 2.0) ** 2)
    rB = np.sqrt(X**2 + Y**2 + (ZG - R / 2.0) ** 2)
    rm = np.sqrt(X**2 + Y**2 + ZG**2)
    pa = np.sqrt(ZETA[0]**3 / np.pi) * np.exp(-ZETA[0] * rA)
    pb = np.sqrt(ZETA[1]**3 / np.pi) * np.exp(-ZETA[1] * rB)
    pc = np.sqrt(ZETA[2]**5 / np.pi) * ZG * np.exp(-ZETA[2] * rm)
    psi = c[0] * pa + c[1] * pb + c[2] * pc
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
    ev, C = states(R)
    E, c = ev[state - 1], C[:, state - 1]
    rho = rho1d(R, c)
    W, p = wigner_from_rdm(rho)
    iz0 = len(ZT) // 2
    ip0 = np.argmin(np.abs(p))
    w00 = W[iz0, ip0]
    pm = (p >= -3.0) & (p <= 3.0) & (np.abs(p) > 0.15)
    w0 = W[iz0][pm]
    pp = p[pm]
    imin = np.argmin(w0)
    return E, w00, pp[imin], w0[imin], c


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "scan":
        print("R        E1              E2              E3")
        for R in [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0,
                  3.5, 4.0, 5.0, 6.0]:
            ev, _ = states(R)
            print(f"{R:6.2f}  {ev[0]:+.10f}  {ev[1]:+.10f}  "
                  f"{ev[2]:+.10f}")
        return
    if len(sys.argv) >= 2 and sys.argv[1] == "oracles":
        print("R      st  E             W(0,0)        p_fringe    W_fringe"
              "    c_a(1sHe) c_b(1sH)  c_c(2p)")
        for R in [0.75, 1.0, 1.5, 2.0, 3.0, 4.0]:
            for st in (1, 2):
                E, w00, pf, wf, c = oracle_row(R, st)
                print(f"{R:5.2f}  {st}   {E:+.10f}  {w00:+.8f}  "
                      f"{pf:+.6f}   {wf:+.8f}   {c[0]:+.4f}  {c[1]:+.4f}"
                      f"  {c[2]:+.4f}")
        print(f"1/pi = {1/np.pi:.16f}")
        return
    if len(sys.argv) >= 5 and sys.argv[1] == "compare":
        path, R, state = sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
        ev, C = states(R)
        rho = rho1d(R, C[:, state - 1])
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
