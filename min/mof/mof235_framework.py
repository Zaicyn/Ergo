#!/usr/bin/env python3
"""mof235_framework.py — Stage 2: two Fe3O SBUs coupled through the
linker channel (MOF-235 framework).

6 x S=5/2, 6^6 = 46656 states. Sector-wise dense ED by total M
(H conserves M, so the full spectrum = union of M-sector spectra):

    H = C * (intra-trimer pairs in A and B) + CP * (inter-SBU bond)

with C = -2J (molecular convention, J<0 AF) and CP = -2J' (the linker
channel, J' swept as a fraction of |J|: {0.05, 0.1, 0.2}).

Inter-bond simplification (documented): one effective Fe(A)-Fe(B) bond
per SBU pair (MOF-235 has 3 BDC linkers per trimer; folded into the
single swept J').

Oracles:
  1. framework ground state degeneracy and low-T structure vs J'
  2. high-T Curie constant: framework chi_mT == 2 x isolated SBU
     exactly (inter-SBU coupling must NOT touch it)
  3. low-T: inter-SBU coupling must MODIFY the susceptibility
  4. MOF-235 measured points (Sudik 2005): mu_eff/Fe = 3.23 (300 K),
     1.95 (5 K) — compare at the stage-1 fitted J; residual documented
     (FeCl4- counterion contribution suspected, see findings).

Determinism: no RNG; run twice byte-identical.
"""
import sys

import numpy as np

sys.path.insert(0, "min/mof")
from fe3o_ed import build_hamiltonian, ladder_energy, KB_CM, \
    G_LANDE, NA_CM3

S = 2.5
NS = 6
DIM = NS ** 6            # 46656

# stage-1 fitted J (fe3o_ed.py: fit to MOF-235 300 K point)
J_FIT = -30.968


def build_sector_hamiltonians(C, CP):
    """Return dict M -> (H_block, mvals). Intra pairs: (0,1),(1,2),(2,0)
    in A=(0,1,2) and B=(3,4,5); inter bond: site 0 <-> site 3."""
    intra = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)]
    inter = [(0, 3)]
    ms = [S - i for i in range(NS)]
    buckets = {}
    for a in range(NS ** 6):
        conf = []
        x = a
        for _ in range(6):
            conf.append(x % NS)
            x //= NS
        M = sum(ms[i] for i in conf)
        buckets.setdefault(M, []).append(conf)
    out = {}
    for M, confs in buckets.items():
        n = len(confs)
        H = np.zeros((n, n))
        pos = {tuple(c): i for i, c in enumerate(confs)}
        for i, conf in enumerate(confs):
            for (p, q), CC in ([(pq, C) for pq in intra]
                               + [(pq, CP) for pq in inter]):
                mp, mq = conf[p], conf[q]
                H[i, i] += CC * ms[mp] * ms[mq]
                if mp + 1 < NS and mq - 1 >= 0:
                    c2 = conf.copy()
                    c2[p] += 1
                    c2[q] -= 1
                    j = pos[tuple(c2)]
                    amp = 0.5 * CC * np.sqrt(
                        (S + ms[mp]) * (S - ms[mp] + 1)) * np.sqrt(
                        (S - ms[mq]) * (S + ms[mq] + 1))
                    H[j, i] += amp
                if mp - 1 >= 0 and mq + 1 < NS:
                    c2 = conf.copy()
                    c2[p] -= 1
                    c2[q] += 1
                    j = pos[tuple(c2)]
                    amp = 0.5 * CC * np.sqrt(
                        (S - ms[mp]) * (S + ms[mp] + 1)) * np.sqrt(
                        (S + ms[mq]) * (S - ms[mq] + 1))
                    H[j, i] += amp
        out[M] = H
    return out


def full_spectrum(C, CP):
    eigs = []
    for M, H in build_sector_hamiltonians(C, CP).items():
        w = np.linalg.eigvalsh(H)
        eigs.append(np.column_stack([w, np.full(len(w), M)]))
    return np.vstack(eigs)


def chiT(spec, T):
    """chi_m T in cm^3 K/mol, Van Vleck zero field."""
    E0 = spec[:, 0].min()
    w = np.exp(-(spec[:, 0] - E0) / (KB_CM * T))
    MUB = 9.2740100783e-21
    KB = 1.380649e-16
    m2 = (spec[:, 1] ** 2 * w).sum() / w.sum()
    return NA_CM3 * (G_LANDE * MUB) ** 2 / KB * m2


def isolated_chiT(J, T):
    """2 x single-SBU chi_mT from the analytic ladder (fe3o_ed)."""
    from collections import Counter
    cnt = Counter()
    for s12 in np.arange(0, 2 * S + 1e-9, 1.0):
        for stot in np.arange(abs(s12 - S), s12 + S + 1e-9, 1.0):
            cnt[stot] += 1
    states = []
    E0 = ladder_energy(J, 0.5)
    for st, m in cnt.items():
        E = ladder_energy(J, st) - E0
        for MM in np.arange(-st, st + 1e-9, 1.0):
            states.append((E, MM, m))
    MUB = 9.2740100783e-21
    KB = 1.380649e-16
    w = np.array([m * np.exp(-E / (KB_CM * T)) for E, MM, m in states])
    num = sum(mul * MM * MM * np.exp(-E / (KB_CM * T))
              for (E, MM, mul) in states)
    return 2.0 * NA_CM3 * (G_LANDE * MUB) ** 2 / KB * (num / w.sum())


def mu_eff_fe(chiT_val):
    return 2.828 * np.sqrt(chiT_val / 6.0)


def main():
    print("=" * 66)
    print("MOF-235 FRAMEWORK — 2 SBUs, linker-channel coupling J'")
    print("=" * 66)
    Ts = [1, 2, 5, 10, 20, 50, 100, 150, 200, 250, 300, 3000]

    cache = {}
    def spec_for(frac):
        if frac not in cache:
            cache[frac] = full_spectrum(-2 * J_FIT,
                                        -2 * (frac * abs(J_FIT)))
        return cache[frac]

    for frac in (0.0, 0.05, 0.1, 0.2):
        Jp = frac * abs(J_FIT)
        print(f"\n--- J' = {frac}|J_fit| = {Jp:.3f} cm^-1 "
              f"(J = {J_FIT}) ---")
        spec = spec_for(frac)
        print(f"states: {len(spec)}; E_ground = {spec[:, 0].min():.4f}; "
              f"gap to first excitation: "
              f"{np.sort(spec[:, 0])[1] - spec[:, 0].min():.4f}")
        print(f"{'T (K)':>7} {'framework':>10} {'isolated':>10} "
              f"{'mu_eff/Fe fw':>12} {'mu/Fe iso':>10} {'ratio':>7}")
        for T in Ts:
            cf = chiT(spec, T)
            ci = isolated_chiT(J_FIT, T)
            print(f"{T:7.0f} {cf:10.4f} {ci:10.4f} "
                  f"{mu_eff_fe(cf):12.4f} {mu_eff_fe(ci):10.4f} "
                  f"{mu_eff_fe(cf) / mu_eff_fe(ci):7.4f}")

    # oracle: high-T Curie constant equality
    print("\n[oracle] high-T Curie constant: framework(J'=0.1) vs "
          "2 x isolated:")
    spec = spec_for(0.1)
    for T in (3000.0, 30000.0):
        cf = chiT(spec, T)
        ci = isolated_chiT(J_FIT, T)
        print(f"  T={T:6.0f}: framework {cf:.5f} vs isolated {ci:.5f} "
              f"(ratio {cf / ci:.5f})")

    print("\n[oracle] MOF-235 measured (Sudik 2005):")
    spec = spec_for(0.1)
    for T, meas in ((300.0, 3.23), (5.0, 1.95)):
        cf = chiT(spec, T)
        print(f"  mu_eff/Fe({T:3.0f} K) = {mu_eff_fe(cf):.4f} "
              f"(measured {meas})")


if __name__ == "__main__":
    main()
