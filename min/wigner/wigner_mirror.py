#!/usr/bin/env python3
"""wigner_mirror.py -- reference mirror for the Wigner handshake instrument.

Computes W(z,p) along the bond axis for two-center 1s-combo states
(sigma_g / sigma_u) from analytic orbitals on a 3D grid, and prints the
oracle table used by wigner_handshake_spec.md. Also compares an ergo
engine WMAP dump (lines: WMAP R par z p W) against the mirror maps.

Usage:
  python wigner_mirror.py oracles            # print oracle table
  python wigner_mirror.py compare wmap.txt R par   # max abs diff vs engine

Deterministic: fixed grids, no RNG. Run twice -> byte-identical.
"""
import sys
import numpy as np

XT = np.linspace(-6, 6, 64)
ZT = np.linspace(-8, 8, 256)
DX = XT[1] - XT[0]
DZ = ZT[1] - ZT[0]
X, Y, ZG = np.meshgrid(XT, XT, ZT, indexing="ij")


def rho1d(R, par, zeta=1.0):
    """Reduced coherence rho(z,z') = int dxdy psi*(x,y,z') psi(x,y,z)."""
    a = np.exp(-zeta * np.sqrt(X**2 + Y**2 + (ZG + R / 2) ** 2))
    b = np.exp(-zeta * np.sqrt(X**2 + Y**2 + (ZG - R / 2) ** 2))
    a *= np.sqrt(zeta**3 / np.pi)
    b *= np.sqrt(zeta**3 / np.pi)
    s = (a + b) if par == 1 else (a - b)
    rho = np.einsum("xyz,xyw->zw", s, s) * DX * DX
    return rho / (np.trace(rho) * DZ)


def wigner_from_rdm(rho, nfft=2048):
    """W(z,p) = (1/pi) int dy e^{2ipy} rho(z-y, z+y); p ascending."""
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


def oracle_row(R, par):
    rho = rho1d(R, par)
    W, p = wigner_from_rdm(rho)
    iz0 = len(ZT) // 2
    ip0 = np.argmin(np.abs(p))
    pm = (p >= -3) & (p <= 3)
    w0 = W[iz0, pm]
    pp = p[pm]
    w00 = W[iz0, ip0]
    wmin = w0.min()
    pmin = pp[np.argmin(w0)]
    vis = abs(wmin) / w0.max()
    return w00, pmin, wmin, vis


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "oracles":
        print("R      par  W(0,0)         p_fringe    W_fringe     visibility")
        for R in [0.5, 1.0, 1.401, 2.0, 3.0, 4.0, 6.0]:
            for par, nm in [(1, "g"), (-1, "u")]:
                w00, pmin, wmin, vis = oracle_row(R, par)
                print(f"{R:5.2f}  {nm}   {w00:+.8f}   {pmin:+.6f}   "
                      f"{wmin:+.8f}   {vis:.6f}")
        print(f"1/pi = {1/np.pi:.16f}")
        return
    if len(sys.argv) >= 5 and sys.argv[1] == "compare":
        path, R, par = sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
        rho = rho1d(R, par)
        W, p = wigner_from_rdm(rho)
        worst = 0.0
        n = 0
        for line in open(path):
            # engine output lines may carry a literal ('...') wrapper
            line = line.strip().strip("()").replace("'", " ")
            f = line.split()
            if len(f) != 6 or f[0] != "WMAP":
                continue
            if abs(float(f[1]) - R) > 1e-9 or int(f[2]) != par:
                continue
            z_e, p_e, w_e = float(f[3]), float(f[4]), float(f[5])
            iz = np.argmin(np.abs(ZT - z_e))
            ip = np.argmin(np.abs(p - p_e))
            worst = max(worst, abs(W[iz, ip] - w_e))
            n += 1
        print(f"compared {n} WMAP rows, max abs diff = {worst:.6e}")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
