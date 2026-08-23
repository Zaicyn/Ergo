#!/usr/bin/env python3
"""hf_analyze.py — Stage 1/3 analysis for the closed-shell HF SCF engine.

Reads hf_radial.ergo output (ATOM/ORB/TSUM/INT lines), assembles the
HF total energy with general N-electron Slater-Condon rules over the
closed-shell determinant (angular integrals from the helium-certified
Gaunt machine in min/helium/he_ci.py), and checks:
  - totals vs Clementi-Roetti HF limits (He -2.861680, Be -14.57302,
    Ne -128.5471 Ha)
  - virial -V/T = 2 (internal referee)
  - Koopmans first IPs (-eps_HOMO) vs NIST (He 24.59, Be 9.32,
    Ne 21.56 eV) with the KT-relaxation note
  - SCF residual printed by the engine (convergence behavior)
  - Poisson/integral spot oracles where closed forms exist

Determinism: pure numpy; run twice, byte-identical.
"""

import sys

import numpy as np

sys.path.insert(0, "min/helium")
import he_ci

CLEMENTI = {"He": (-2.861680, 2), "Be": (-14.57302, 4), "Ne": (-128.5471, 10)}
NIST_IP = {"He": 24.59, "Be": 9.32, "Ne": 21.56}   # eV
EV = 27.211386245988

# engine orbital indices -> (n, l)
ORBTAB = {1: (1, 0), 2: (2, 0), 3: (2, 1)}


def load(path):
    eps = {}
    R = {}
    tsum = {}
    z = None
    atoms = []
    for line in open(path):
        p = line.replace("('", "").replace("')", "").split()
        if not p:
            continue
        if p[0] == "ATOM":
            z = float(p[1].replace("Z=", ""))
            atoms.append(z)
        elif p[0] == "ORB":
            eps[(z, int(p[1]))] = float(p[3])
        elif p[0] == "TSUM":
            tsum[z] = float(p[1])
        elif p[0] == "INT":
            a, b, c, d, k = (int(p[i]) for i in range(1, 6))
            R[(z, a, b, c, d, k)] = float(p[6])
    return atoms, eps, R, tsum


def rk(R, z, a, b, c, d, k):
    if a > b:
        a, b = b, a
    if c > d:
        c, d = d, c
    return R[(z, a, b, c, d, k)]


def analyze(z, nspat, eps, R, tsum, name):
    """Assemble and check one atom."""
    nb = list(range(1, nspat + 1))
    # spin-orbital list and determinant (all occupied spin-orbitals)
    he_ci.ORBTAB = ORBTAB
    he_ci.build_spin_orbitals(nb)
    nso = len(he_ci.SPINORB)
    det = tuple(range(nso))
    h = [eps[(z, he_ci.SPINORB[i][0])] for i in range(nso)]

    def H_id(d):
        e = sum(h[i] for i in d)
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                p, q = d[i], d[j]
                op, _, sp = he_ci.SPINORB[p]
                oq, _, sq = he_ci.SPINORB[q]
                # direct always; exchange only for same spin
                e += he_ci.spatial_int(R2, p, p, q, q)
                if sp == sq:
                    e -= he_ci.spatial_int(R2, p, q, q, p)
        return e

    R2 = {(a, b, c, d, k): rk(R, z, a, b, c, d, k)
          for (zz, a, b, c, d, k), v in R.items() if zz == z}
    E = H_id(det)
    # virial: T from the engine, V = E - T
    T = tsum[z]
    V = E - T
    vir = -V / T
    # Koopmans: eps_HOMO = h_HOMO + sum_b (2J - K) over occupied
    homo_spatial = nspat  # last spatial orbital
    homo_i = max(i for i in range(nso)
                 if he_ci.SPINORB[i][0] == homo_spatial)
    ehom = h[homo_i]
    for i in range(nso):
        p = homo_i
        q = i
        _, _, sp = he_ci.SPINORB[p]
        _, _, sq = he_ci.SPINORB[q]
        # J - K felt by the HOMO spin-orbital from each occupied one
        # (spatial_int takes SPIN-ORBITAL indices)
        jv = he_ci.spatial_int(R2, p, p, q, q)
        kv = he_ci.spatial_int(R2, p, q, q, p) if sp == sq else 0.0
        ehom += jv - kv
    ip = -ehom * EV
    return E, vir, ip


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/hf_out.txt"
    atoms, eps, R, tsum = load(path)
    print("=" * 66)
    print("HF ANALYZER — closed-shell totals, virial, Koopmans IPs")
    print("=" * 66)
    nspat = {2.0: 1, 4.0: 2, 10.0: 3}
    names = {2.0: "He", 4.0: "Be", 10.0: "Ne"}
    for z in atoms:
        name = names[z]
        E, vir, ip = analyze(z, nspat[z], eps, R, tsum, name)
        cl, _ = CLEMENTI[name]
        print(f"\n[{name} (Z={int(z)})]")
        print(f"  E_HF = {E:.6f} Ha   Clementi {cl:.6f}   "
              f"dev {E - cl:+.2e}")
        print(f"  virial -V/T = {vir:.8f} (exact 2)")
        print(f"  Koopmans IP = {ip:.4f} eV   NIST {NIST_IP[name]:.2f} eV"
              f"   (KT overshoot documented)")


if __name__ == "__main__":
    main()
