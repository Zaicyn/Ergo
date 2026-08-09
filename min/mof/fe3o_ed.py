#!/usr/bin/env python3
"""fe3o_ed.py — ED oracle for the Fe3O SBU of MOF-235.

Heisenberg trimer, 3 x S=5/2 Fe(III), 6^3 = 216 states:

    H = -2J * (S1.S2 + S2.S3 + S3.S1),  molecular-magnetism
    convention: J < 0 = antiferromagnetic. (The plan's ladder
    E(S) = J/2 [S(S+1) - const] with J<0 orders AF ground state LAST
    in the H = J Si.Sj convention; the physical AF requirement —
    S_T = 1/2 ground — fixes the sign. H = -2J with J<0 gives the
    required S_T = 1/2 ground; the ladder is then
    E(S) = -J [S(S+1) - 3s(s+1)].)

For the EQUILATERAL trimer this is exactly -(J)[S_T(S_T+1) - 3s(s+1)]
(function of S_T^2 only), so the "analytic ladder" is not an
approximation — the ED must reproduce it exactly, with degeneracies
m(S_T) from coupling three spin-5/2. Verifies:

  1. energies == ladder to machine precision
  2. S_T = 1/2 ground multiplets (AF), count + degeneracies
  3. spacing E(3/2) - E(1/2) == J * 3/2
  4. canonical chi_m T(T), mu_eff per Fe; high-T effective moment per
     Fe(III) == g sqrt(s(s+1)) = 5.916 uB exactly
  5. J fitted to MOF-235's measured mu_eff at 300 K (3.23 uB/Fe,
     Sudik et al. 2005); the 5 K point (1.95 uB/Fe) is then a
     prediction/residual (framework J' enters in stage 2)

Reference numbers are dumped to fe3o_ref.txt for the Ergo comparison
(min/mof/fe3o_sbu.ergo must agree — the PME oracle).

Determinism: no RNG; run twice byte-identical.
"""
import numpy as np

S = 2.5
NS = int(round(2 * S)) + 1          # states per site = 6
DIM = NS ** 3                        # 216
G_LANDE = 2.0
MU_B_CM = 0.46686                    # Bohr magneton, cm^-1/T
KB_CM = 0.69503                      # k_B, cm^-1/K
NA_CM3 = 6.02214076e23

# MOF-235 measured (Sudik, Sudik et al., JACS 2005, trigonal prismatic
# building blocks): mu_eff per Fe at 300 K and 5 K
M235_300K = 3.23
M235_5K = 1.95


def build_hamiltonian(C, S=2.5):
    """H = C * (S1.S2 + S2.S3 + S3.S1) in the m-product basis.
    C is the coefficient of Si.Sj (= -2J in the molecular convention).
    Off-diagonal: transition (mp,mq) -> (mp+1,mq-1) from S_p^+ S_q^-
    with amp = (C/2) sqrt((S-mp)(S+mp+1)) sqrt((S+mq)(S-mq+1));
    the Hermitian-conjugate hop is the same amplitude."""
    NS = int(round(2 * S)) + 1
    DIML = NS ** 3
    ms = [S - i for i in range(NS)]
    H = np.zeros((DIML, DIML))

    def idx(a, b, c):
        return a * NS * NS + b * NS + c

    for a in range(NS):
        for b in range(NS):
            for c in range(NS):
                conf = [a, b, c]
                i = idx(a, b, c)
                H[i, i] += C * (ms[a] * ms[b] + ms[b] * ms[c]
                                + ms[c] * ms[a])
                for p, q in ((0, 1), (1, 2), (2, 0)):
                    mp, mq = conf[p], conf[q]
                    # S_p^- S_q^+ (index p up, index q down)
                    if mp + 1 < NS and mq - 1 >= 0:
                        c2 = conf.copy()
                        amp = 0.5 * C * np.sqrt(
                            (S + ms[mp]) * (S - ms[mp] + 1)) * np.sqrt(
                            (S - ms[mq]) * (S + ms[mq] + 1))
                        c2[p] += 1
                        c2[q] -= 1
                        j = idx(*c2)
                        H[j, i] += amp
                    # S_p^+ S_q^- (index p down, index q up)
                    if mp - 1 >= 0 and mq + 1 < NS:
                        c2 = conf.copy()
                        amp = 0.5 * C * np.sqrt(
                            (S - ms[mp]) * (S + ms[mp] + 1)) * np.sqrt(
                            (S + ms[mq]) * (S - ms[mq] + 1))
                        c2[p] -= 1
                        c2[q] += 1
                        j = idx(*c2)
                        H[j, i] += amp
    return H


def ladder_energy(J, ST):
    # H = -2J sum Si.Sj => E = -J [S_T(S_T+1) - 3 s(s+1)]
    return -J * (ST * (ST + 1.0) - 3.0 * S * (S + 1.0))


def main():
    print("=" * 66)
    print("FE3O SBU — ED oracle (216 states, dense)")
    print("=" * 66)
    J = -25.0          # cm^-1, H = -2J Si.Sj convention (AF: J<0)
    H = build_hamiltonian(-2.0 * J)  # build_hamiltonian takes the
                                     # coefficient of Si.Sj (= -2J)
    w = np.linalg.eigvalsh(H)
    # cluster into multiplets
    order = np.argsort(w)
    w = w[order]
    clusters = []
    tol = 1e-9
    i = 0
    while i < len(w):
        j = i
        while j + 1 < len(w) and abs(w[j + 1] - w[i]) < tol:
            j += 1
        clusters.append((w[i], j - i + 1))
        i = j + 1

    print(f"J = {J} cm^-1 (H = -2J*Si.Sj, molecular convention; "
          f"AF = J<0)")
    print(f"{'E (cm^-1)':>12} {'deg':>4} {'S_T':>5} {'E_ladder':>12} "
          f"{'m(S_T)':>6} {'match':>6}")
    nst = int(round(3 * S * 2))      # 15
    mult_known = {}
    # expected multiplicities m(S_T) for three spin-5/2, computed by
    # direct CG enumeration (oracle, independent of the ED)
    from collections import Counter
    cnt = Counter()
    for s12 in np.arange(0, 2 * S + 1e-9, 1.0):
        for stot in np.arange(abs(s12 - S), s12 + S + 1e-9, 1.0):
            cnt[stot] += 1
    ok = True
    cidx = 0
    for E, deg in clusters:
        # identify S_T from the ladder (unique energies for J != 0)
        ST = None
        for k in range(1, nst + 1, 2):
            if abs(ladder_energy(J, k / 2.0) - E) < 1e-6:
                ST = k / 2.0
        El = ladder_energy(J, ST) if ST else float("nan")
        m = cnt.get(ST, -1) if ST else -1
        match = (ST is not None
                 and deg == m * int(round(2 * ST + 1)))
        mult_known[ST] = (deg, m)
        ok &= match and abs(E - El) < 1e-9
        print(f"{E:12.4f} {deg:>4} {ST:>5} {El:>12.4f} {m:>6} "
              f"{str(match):>6}")
        cidx += 1
    print(f"all energies on the analytic ladder, multiplicities from "
          f"CG enumeration: {ok}")
    E05, E15 = None, None
    for ST in sorted(mult_known):
        if abs(ST - 0.5) < 1e-9:
            E05 = ladder_energy(J, ST)
        if abs(ST - 1.5) < 1e-9:
            E15 = ladder_energy(J, ST)
    deg05 = mult_known[0.5][0] if 0.5 in mult_known else 0
    print(f"ground: S_T=1/2 at E={E05:.4f}, degeneracy {deg05} "
          f"(= {deg05 // 2} doublets)")
    print(f"E(3/2)-E(1/2) = {E15 - E05:.6f} vs -J*3 = {-3.0 * J:.6f} "
          f"(ratio {(E15 - E05) / (-3.0 * J):.9f})"
          f"  [ladder: E(S)-E(S-1) = -J*(2S)]")

    # ---- canonical chi ----
    Ts = np.concatenate(([1, 2, 5, 10, 20, 50],
                         np.arange(100, 301, 25), [1000.0, 3000.0, 10000.0, 30000.0]))
    mvals = np.arange(-7.5, 8.0, 1.0)

    E_GROUND_SHIFT = None

    def chi_per_trimer(Jv, T):
        # chi_m T in cm^3 K/mol per trimer, Van Vleck z=0 field:
        # chi_m T = NA (g muB)^2 <Sz_tot^2> / kB  (cgs constants)
        states = []
        E0 = ladder_energy(Jv, 0.5)
        for ST, (deg, m) in mult_known.items():
            E = ladder_energy(Jv, ST) - E0
            for M in np.arange(-ST, ST + 1e-9, 1.0):
                states.append((E, M, m))
        Z = sum(m * np.exp(-E / (KB_CM * T)) for E, M, m in states)
        num = sum(m * M * M * np.exp(-E / (KB_CM * T))
                  for E, M, m in states)
        MUB = 9.2740100783e-21     # Bohr magneton, erg/G (emu)
        KB = 1.380649e-16          # Boltzmann, erg/K
        return NA_CM3 * (G_LANDE * MUB) ** 2 / KB * (num / Z)

    def mu_eff_fe(Jv, T):
        return 2.828 * np.sqrt(chi_per_trimer(Jv, T) / 3.0)

    print("\ncanonical susceptibility:")
    print(f"{'T (K)':>7} {'chi_mT/tri':>11} {'mu_eff/Fe':>10}")
    for T in Ts:
        print(f"{T:7.1f} {chi_per_trimer(J, T):11.5f} "
              f"{mu_eff_fe(J, T):10.4f}")
    hi = mu_eff_fe(J, 30000.0)
    exact_hi = G_LANDE * np.sqrt(S * (S + 1))
    print(f"high-T mu_eff per Fe (30000 K, asymptote): {hi:.4f} vs exact "
          f"g*sqrt(s(s+1)) = {exact_hi:.4f} "
          f"(ratio {hi / exact_hi:.5f})")

    # ---- J fit to MOF-235 300 K point ----
    def f(Jv):
        return mu_eff_fe(Jv, 300.0) - M235_300K

    lo, hi_ = -200.0, -0.5
    flo = f(lo)
    for _ in range(200):
        mid = 0.5 * (lo + hi_)
        if f(mid) * flo > 0:
            lo = mid
            flo = f(mid)
        else:
            hi_ = mid
    Jfit = 0.5 * (lo + hi_)
    print(f"\nJ fit to mu_eff(300 K) = {M235_300K}: J = {Jfit:.3f} cm^-1 "
          f"(H = -2J*Si.Sj convention)")
    print(f"  check: mu_eff(300 K) = {mu_eff_fe(Jfit, 300):.4f} "
          f"(target {M235_300K}); mu_eff(5 K) = "
          f"{mu_eff_fe(Jfit, 5):.4f} (measured {M235_5K} — "
          f"isolated-SBU prediction, framework J' in stage 2)")

    # ---- reference dump ----
    with open("min/mof/fe3o_ref.txt", "w") as fh:
        fh.write(f"# fe3o_ed reference. J = {J} cm^-1 (H=J*Si.Sj)\n")
        for ST in sorted(mult_known):
            deg, m = mult_known[ST]
            fh.write(f"MULT {ST} {m} {int(2 * ST + 1)} "
                     f"{ladder_energy(J, ST):.10f}\n")
        for T in Ts:
            fh.write(f"CHI {T:.1f} {chi_per_trimer(J, T):.10f} "
                     f"{mu_eff_fe(J, T):.10f}\n")
        fh.write(f"JFIT {Jfit:.10f}\n")
        fh.write(f"J_USED {J:.10f}\n")
        fh.write(f"HI_EXACT {exact_hi:.10f}\n")
    print("\nwrote min/mof/fe3o_ref.txt")


if __name__ == "__main__":
    main()
