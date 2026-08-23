#!/usr/bin/env python3
"""wigner_mirror_w2.py -- Stage W2 mirror: two-electron H2 1-RDM Wigner maps.

2-orbital CI (singlet block {|gg>,|uu>}; |gu_S> decouples by parity) over
Slater 1s two-center orbitals, FD Laplacian, zero-padded open-boundary
Poisson. Emits the oracle table from wigner_handshake_spec.md (Stage W2)
and optionally dumps maps.

Usage:
  python wigner_mirror_w2.py oracles           # W2 oracle table
  python wigner_mirror_w2.py map R singlet|triplet > map.txt
       (rows: z p WperElectron, coarse every 2nd grid point)

Deterministic: fixed grids, closed CI, no RNG. Run twice byte-identical.
Runtime ~1 min per R (Poisson FFTs dominate).
"""
import sys
import numpy as np

NN = 128
GX1 = -8.0 + (np.arange(NN) + 0.5) * (16.0 / NN)
DX = GX1[1] - GX1[0]
GX, GY, GZ = np.meshgrid(GX1, GX1, GX1, indexing="ij")


def lap_fd(f):
    return (np.roll(f, 1, 0) + np.roll(f, -1, 0) +
            np.roll(f, 1, 1) + np.roll(f, -1, 1) +
            np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6 * f) / DX**2


_NP2 = 2 * NN
_gi = np.where(np.arange(_NP2) > NN, np.arange(_NP2) - _NP2,
               np.arange(_NP2)) * DX
_KX, _KY, _KZ = np.meshgrid(_gi, _gi, _gi, indexing="ij")
_GK = 1.0 / np.sqrt(_KX**2 + _KY**2 + _KZ**2 + 1e-30)
_GK[0, 0, 0] = 0.0
_FFTG = np.fft.fftn(_GK)
del _KX, _KY, _KZ, _GK


def poisson(rho):
    pad = np.zeros((_NP2, _NP2, _NP2))
    pad[:NN, :NN, :NN] = rho
    out = np.real(np.fft.ifftn(np.fft.fftn(pad) * _FFTG)) * DX**3
    return out[:NN, :NN, :NN]


def ci_st(R, zeta=1.0):
    a = np.exp(-zeta * np.sqrt(GX**2 + GY**2 + (GZ + R / 2)**2))
    b = np.exp(-zeta * np.sqrt(GX**2 + GY**2 + (GZ - R / 2)**2))
    a *= np.sqrt(zeta**3 / np.pi)
    b *= np.sqrt(zeta**3 / np.pi)
    S = (a * b).sum() * DX**3
    g = (a + b) / np.sqrt(2 * (1 + S))
    u = (a - b) / np.sqrt(2 * (1 - S))
    V = (-1 / np.sqrt(GX**2 + GY**2 + (GZ - R / 2)**2)
         - 1 / np.sqrt(GX**2 + GY**2 + (GZ + R / 2)**2))
    h1 = lambda f: (-0.5 * (f * lap_fd(f)).sum() + (V * f * f).sum()) * DX**3
    hg, hu = h1(g), h1(u)
    ph_gg, ph_uu, ph_gu = poisson(g * g), poisson(u * u), poisson(g * u)
    GGGG = (ph_gg * g * g).sum() * DX**3
    UUUU = (ph_uu * u * u).sum() * DX**3
    GGUU = (ph_gg * u * u).sum() * DX**3
    GUGU = (ph_gu * g * u).sum() * DX**3
    H2 = np.array([[2 * hg + GGGG, GUGU], [GUGU, 2 * hu + UUUU]])
    ev, vec = np.linalg.eigh(H2)
    ET = hg + hu + GGUU - GUGU
    c = vec[:, 0]
    if c[0] < 0:
        c = -c
    Pgg = np.einsum("xyz,xyw->zw", g, g) * DX**2
    Puu = np.einsum("xyz,xyw->zw", u, u) * DX**2
    rhoS = 2 * c[0]**2 * Pgg + 2 * c[1]**2 * Puu
    rhoT = Pgg + Puu
    return S, ev[0], ET, c, rhoS, rhoT


def wigner_rz(rho, nfft=2048):
    NZ = rho.shape[0]
    W = np.zeros((NZ, nfft))
    for iz in range(NZ):
        m = min(iz, NZ - 1 - iz)
        k = np.arange(-m, m + 1)
        ry = rho[iz - k, iz + k]
        buf = np.zeros(nfft)
        buf[0:m + 1] = ry[m:]
        buf[nfft - m:] = ry[:m]
        W[iz] = np.fft.fft(buf).real * DX / np.pi
    p = np.fft.fftshift(-np.pi * np.fft.fftfreq(nfft, d=DX))
    return np.fft.fftshift(W, axes=1), p


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "oracles":
        print("R      c_uu^2    W00_S(per e-)  W00_T(per e-)")
        for R in [0.5, 1.0, 1.401, 2.0, 3.0, 4.0, 6.0]:
            S, ES, ET, c, rhoS, rhoT = ci_st(R)
            WS, p = wigner_rz(rhoS)
            WT, _ = wigner_rz(rhoT)
            iz0 = WS.shape[0] // 2
            ip0 = np.argmin(np.abs(p))
            print(f"{R:5.2f}  {c[1]**2:.6f}   {WS[iz0, ip0] / 2:+.6f}"
                  f"      {WT[iz0, ip0] / 2:+.6e}")
        return
    if len(sys.argv) >= 4 and sys.argv[1] == "map":
        R = float(sys.argv[2])
        which = sys.argv[3]
        S, ES, ET, c, rhoS, rhoT = ci_st(R)
        rho = rhoS if which == "singlet" else rhoT
        W, p = wigner_rz(rho)
        pm = (p >= -3) & (p <= 3)
        for iz in range(0, NN, 2):
            for ip in np.where(pm)[0][::8]:
                print(f"{GX1[iz]:.4f} {p[ip]:.4f} {W[iz, ip] / 2:.10e}")
        return
    if len(sys.argv) >= 5 and sys.argv[1] == "compare":
        # engine rows: ('W2MAP R SP z p W'), SP 1=singlet 2=triplet
        path, R, sp = sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
        S, ES, ET, c, rhoS, rhoT = ci_st(R)
        rho = rhoS if sp == 1 else rhoT
        W, p = wigner_rz(rho)
        worst, n = 0.0, 0
        for line in open(path):
            line = line.strip().strip("()").replace("'", " ")
            f = line.split()
            if len(f) != 6 or f[0] != "W2MAP":
                continue
            if abs(float(f[1]) - R) > 1e-9 or int(f[2]) != sp:
                continue
            z_e, p_e, w_e = float(f[3]), float(f[4]), float(f[5])
            iz = np.argmin(np.abs(GX1 - z_e))
            ip = np.argmin(np.abs(p - p_e))
            worst = max(worst, abs(W[iz, ip] - w_e))
            n += 1
        print(f"compared {n} W2MAP rows, max abs diff = {worst:.6e}")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
