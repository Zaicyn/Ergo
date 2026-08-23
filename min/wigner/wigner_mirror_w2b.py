#!/usr/bin/env python3
"""wigner_mirror_w2b.py -- Stage W4b mirror: two-electron HeH+ 1-RDM Wigner maps.

2-orbital CI over the {1sigma,2sigma} one-electron orbitals of
wigner_mirror_w4b (1s_He + 1s_H + 2p_mid STO LCAO), evaluated on a 128^3
grid.  Singlet block {|aa>,|ab_S>,|bb>} (no parity: all three mix),
triplet |ab_T>.  Slater-Condon rules identical to h2_wig.ergo /
h4_wig.ergo.  Emits structural oracles (energies are 2-orbital-CI level:
the engine's 21-CSF/6-orbital full CI must come in BELOW these singlet
values) plus the heteronuclear dipole observable.

He at z=-R/2 (Z=2), H at z=+R/2 (Z=1).  Same convention as h4_wig.ergo.

Usage:
  python wigner_mirror_w2b.py oracles
  python wigner_mirror_w2b.py map R singlet|triplet > map.txt
  python wigner_mirror_w2b.py compare h4_wig.csv R SP

Deterministic: fixed grids, closed CI, no RNG. Run twice byte-identical.
"""
import sys
import numpy as np

sys.path.insert(0, "/mnt/agents/output")
import wigner_mirror_w4b as m4

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


def orbitals_on_grid(R):
    """Return (a, b): 1sigma, 2sigma orbitals of wigner_mirror_w4b on the grid."""
    E, coeffs = m4.states(R)   # coeffs[i, state]; 1sigma=state 0, 2sigma=state 1
    zeta = m4.ZETA
    RA = np.sqrt(GX**2 + GY**2 + (GZ + R / 2)**2)   # from He at z=-R/2
    RB = np.sqrt(GX**2 + GY**2 + (GZ - R / 2)**2)   # from H  at z=+R/2
    RMID = np.sqrt(GX**2 + GY**2 + GZ**2)
    f1 = np.sqrt(zeta[0]**3 / np.pi) * np.exp(-zeta[0] * RA)   # 1s on He
    f2 = np.sqrt(zeta[1]**3 / np.pi) * np.exp(-zeta[1] * RB)   # 1s on H
    f3 = np.sqrt(zeta[2]**5 / np.pi) * GZ * np.exp(-zeta[2] * RMID)
    chis = [f1, f2, f3]
    a = sum(coeffs[i, 0] * chis[i] for i in range(3))
    b = sum(coeffs[i, 1] * chis[i] for i in range(3))
    a /= np.sqrt((a * a).sum() * DX**3)
    b /= np.sqrt((b * b).sum() * DX**3)
    # re-orthogonalize b against a on the grid (analytic S, grid discretization)
    b -= (a * b).sum() * DX**3 * a
    b /= np.sqrt((b * b).sum() * DX**3)
    return a, b


def ci_st(R):
    a, b = orbitals_on_grid(R)
    V = (-2.0 / np.sqrt(GX**2 + GY**2 + (GZ + R / 2)**2)
         - 1.0 / np.sqrt(GX**2 + GY**2 + (GZ - R / 2)**2))
    h1 = lambda f, g: (-0.5 * (f * lap_fd(g)).sum()
                       + (V * f * g).sum()) * DX**3
    haa, hbb, hab = h1(a, a), h1(b, b), h1(a, b)
    ph_aa, ph_bb, ph_ab = poisson(a * a), poisson(b * b), poisson(a * b)
    AAAA = (ph_aa * a * a).sum() * DX**3
    BBBB = (ph_bb * b * b).sum() * DX**3
    AABB = (ph_aa * b * b).sum() * DX**3
    ABAB = (ph_ab * a * b).sum() * DX**3
    AAAB = (ph_aa * a * b).sum() * DX**3
    ABBB = (ph_bb * a * b).sum() * DX**3
    SQ = np.sqrt(2.0)
    H2 = np.array([[2 * haa + AAAA, SQ * (hab + AAAB), ABAB],
                   [SQ * (hab + AAAB), haa + hbb + AABB + ABAB,
                    SQ * (hab + ABBB)],
                   [ABAB, SQ * (hab + ABBB), 2 * hbb + BBBB]])
    ev, vec = np.linalg.eigh(H2)
    ET = haa + hbb + AABB - ABAB
    c = vec[:, 0]          # (c_Da, c_S, c_Db)
    if c[0] < 0:
        c = -c
    # 1-RDM on the z axis
    Pa = np.einsum("xyz,xyw->zw", a, a) * DX**2
    Pb = np.einsum("xyz,xyw->zw", b, b) * DX**2
    Pab = np.einsum("xyz,xyw->zw", a, b) * DX**2
    gaa = 2 * c[0]**2 + c[1]**2
    gbb = 2 * c[2]**2 + c[1]**2
    gab = SQ * (c[0] + c[2]) * c[1]
    rhoS = gaa * Pa + gbb * Pb + 2 * gab * Pab
    rhoT = Pa + Pb
    # electronic dipole <sum z> from the 1-RDM diagonal
    zdiag = GZ[0, 0, :]
    dS = np.einsum("z,z", zdiag, np.diagonal(rhoS)) * DX
    dT = np.einsum("z,z", zdiag, np.diagonal(rhoT)) * DX
    return ev[0], ET, c, rhoS, rhoT, dS, dT


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
        print("R      ES(2orbCI)   ET(2orbCI)   dip_S(<z>)  dip_T(<z>)"
              "   W00_S(per e-)  W00_T(per e-)")
        for R in [0.75, 1.0, 1.46, 2.0, 3.0, 4.0]:
            ES, ET, c, rhoS, rhoT, dS, dT = ci_st(R)
            WS, p = wigner_rz(rhoS)
            WT, _ = wigner_rz(rhoT)
            iz0 = WS.shape[0] // 2
            ip0 = np.argmin(np.abs(p))
            print(f"{R:5.2f}  {ES:+.8f}  {ET:+.8f}  {dS:+.6f}   {dT:+.6f}"
                  f"   {WS[iz0, ip0] / 2:+.6f}    {WT[iz0, ip0] / 2:+.6e}"
                  f"   c={c[0]:+.4f},{c[1]:+.4f},{c[2]:+.4f}")
        return
    if len(sys.argv) >= 4 and sys.argv[1] == "map":
        R = float(sys.argv[2])
        which = sys.argv[3]
        ES, ET, c, rhoS, rhoT, dS, dT = ci_st(R)
        rho = rhoS if which == "singlet" else rhoT
        W, p = wigner_rz(rho)
        pm = (p >= -3) & (p <= 3)
        for iz in range(0, NN, 2):
            for ip in np.where(pm)[0][::8]:
                print(f"{GX1[iz]:.4f} {p[ip]:.4f} {W[iz, ip] / 2:.10e}")
        return
    if len(sys.argv) >= 5 and sys.argv[1] == "compare":
        path, R, sp = sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
        ES, ET, c, rhoS, rhoT, dS, dT = ci_st(R)
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
