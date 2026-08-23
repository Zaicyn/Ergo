#!/usr/bin/env python3
"""fock_check.py — independent Fock-operator check for Ne SCF orbitals.

Reads the UD orbital dump from a hf_radial.ergo run and computes,
independently in numpy:
  - per-orbital kinetic T_a (5-point Laplacian, same stencil) and the
    total T = sum occ*T_a  (engine TSUM cross-check)
  - the Fock residual ||F u_a - eps_a u_a|| with the operator built
    from the radial Poisson integrals of the dumped orbitals
    (occupation-weighted direct + the baked exchange coefficients)
Answers: are the orbitals too diffuse (T low), or is the engine's T
printout broken, or is the operator wrong?
"""
import sys

import numpy as np

NR = 16000
RMAX = 40.0
DR = RMAX / (NR - 1)
OCC = {1: 2, 2: 2, 3: 6}
LTAB = {1: 0, 2: 0, 3: 1}
# exchange coefficients per (la, lb): [(k, c)]
CTAB = {(0, 0): [(0, 1.0)], (0, 1): [(1, 1.0)],
        (1, 0): [(1, 1.0 / 3.0)], (1, 1): [(0, 1.0), (2, 0.4)]}


def load(path, ztarget=10.0):
    r = (np.arange(NR) * DR)[::4]
    u = {1: np.zeros(NR // 4), 2: np.zeros(NR // 4), 3: np.zeros(NR // 4)}
    for line in open(path):
        if line.startswith("('UD"):
            p = line.replace("('UD ", "").replace("')", "").split()
            a, i = int(p[0]), int(p[1])
            u[a][(i - 1) // 4] = float(p[3])
    return r, u


def ypois(f, k, r):
    A = np.concatenate([[0.0], np.cumsum(0.5 * (f[1:] * r[1:]**k
                                                + f[:-1] * r[:-1]**k)
                                       * np.diff(r))])
    g = f / np.maximum(r, 1e-300)**(k + 1)
    B = np.concatenate([np.cumsum((0.5 * (g[1:] + g[:-1])
                                   * np.diff(r))[::-1])[::-1], [0.0]])
    return A / np.maximum(r, 1e-300)**(k + 1) + r**k * B


def lap5(u, r):
    d = np.zeros_like(u)
    i = np.arange(3, len(u) - 2)
    dr = r[1] - r[0]
    d[i] = (-u[i-2] + 16*u[i-1] - 30*u[i] + 16*u[i+1] - u[i+2]) / (12*dr*dr)
    for I in (2, len(u) - 2):
        d[I] = (u[I-1] + u[I+1] - 2*u[I]) / dr**2
    return d


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/hf_dump.txt"
    r, u = load(path)
    dr = r[1] - r[0]
    Z = 10.0
    # direct potential
    vh = np.zeros_like(r)
    for b in (1, 2, 3):
        vh += OCC[b] * ypois(u[b]**2, 0, r)
    print("orbital checks (Ne, dumped orbitals, every-4th grid):")
    TT = 0.0
    for a in (1, 2, 3):
        la = LTAB[a]
        kin = -0.5 * (u[a] * lap5(u[a], r) * dr).sum()
        pot = ((-Z / r + la * (la + 1) / (2 * r**2)) * u[a]**2 * dr)[1:].sum()
        TT += OCC[a] * kin
        # exchange source for a
        xa = np.zeros_like(r)
        for b in (1, 2, 3):
            for k, c in CTAB[(la, LTAB[b])]:
                xa += c * ypois(u[a] * u[b], k, r) * u[b]
        fu = -0.5 * lap5(u[a], r) + (-Z / r + la*(la+1)/(2*r**2) + vh) * u[a] - xa
        eps = (u[a] * fu * dr).sum() / (u[a]**2 * dr).sum()
        res = np.sqrt((((fu - eps * u[a])**2) * dr).sum())
        print(f"  orb {a}: T = {kin:.6f}  V = {pot:.6f}  "
              f"eps = {eps:.6f}  Fock resid = {res:.3e}")
    print(f"  TOTAL T = {TT:.6f} (virial wants T = -E = 128.547)")


if __name__ == "__main__":
    main()
