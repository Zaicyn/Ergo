#!/usr/bin/env python3
"""h2_ci.py — Stage 2/3: grid full-CI for H2 from h2_orb.ergo output.

Reads ORB (one-electron energies h_i), INT (ij|kl integrals) and THETA
(sigma_i Theta(z<0) sigma_j) from the h2_orb binary output; builds the
spin-adapted CI in the 6 grid orbitals (mixed sigma/pi_x symmetry — the
ground state resolves itself as 1Sg+):

  singlet CSFs: |ii> (6), |ij>_S = (ij+ji)/sqrt2 (15), dim 21
  triplet CSFs: |ij>_T (15), dim 15

  Singlet:  diag(ii) = 2 h_i + (ii|ii) + 1/R
            diag(ij_S) = h_i + h_j + (ii|jj) + (ij|ji) + 1/R
            <ii|jj> = (ij|ij)   [pair double-excitation, exchange-like]
            <ii|jk_S> = sqrt2 (ij|ik)
            <ij_S|kl_S> = (ik|jl) + (il|jk)
  Triplet:  diag(ij_T) = h_i + h_j + (ii|jj) - (ij|ji) + 1/R
            <ij_T|kl_T> = (ik|jl) - (il|jk)

Oracles:
  (sg sg|sg sg) at the smallest grid R (united-atom He+ 1s limit
  5Z/8 = 1.25 Ha for reference; no closed form at finite R)
  D_e ladder with orbital count (2, 4, 6 orbitals) toward 4.7475 eV
  R_e vs 1.4011 bohr; triplet curve must be repulsive (STOP else)
Stage 3: ionic fraction from the CI ground via THETA (both electrons
  on the same side) and the singlet-triplet split.

Determinism: engine has no RNG (fixed sweep/step counts); a reduced
single-R (1.4014 bohr) variant of the engine is run twice and
byte-compared here (orb_det1.txt vs orb_det2.txt); analyzer run twice,
byte-identical.
"""
import numpy as np

EV = 27.211386245988
ORB_OUT = "/tmp/orb_out.txt"
ORB_DET1 = "/tmp/orb_det1.txt"
ORB_DET2 = "/tmp/orb_det2.txt"


def load(path):
    H, INT, TH = {}, {}, {}
    for line in open(path):
        p = line.split()
        if not p:
            continue
        if p[0] == "ORB":
            H.setdefault(float(p[1]), {})[int(p[2]) - 1] = float(p[5])
        elif p[0] == "INT":
            R, i, j, k, l = float(p[1]), int(p[2]) - 1, int(p[3]) - 1, \
                int(p[4]) - 1, int(p[5]) - 1
            INT.setdefault(R, {})[(i, j, k, l)] = float(p[6])
        elif p[0] == "THETA":
            R, i, j = float(p[1]), int(p[2]) - 1, int(p[3]) - 1
            TH.setdefault(R, {})[(i, j)] = float(p[4])
    return H, INT, TH


def get_int(R, ints, i, j, k, l):
    def s(a, b):
        return (a, b) if a <= b else (b, a)
    return ints[s(i, j) + s(k, l)]


def build_ci(hi, ints, nuse, R):
    n = nuse
    csf_s = [(i, i) for i in range(n)] + \
        [(i, j) for i in range(n) for j in range(i + 1, n)]
    csf_t = [(i, j) for i in range(n) for j in range(i + 1, n)]
    dim_s = len(csf_s)
    Hs = np.zeros((dim_s, dim_s))
    for a, (i, j) in enumerate(csf_s):
        for b, (k, l) in enumerate(csf_s[a:], start=a):
            if i == j and k == l:
                v = get_int(R, ints, i, k, i, k)
            elif i == j:
                v = np.sqrt(2.0) * get_int(R, ints, i, k, i, l)
            elif k == l:
                v = np.sqrt(2.0) * get_int(R, ints, k, i, k, j)
            else:
                v = get_int(R, ints, i, k, j, l) \
                    + get_int(R, ints, i, l, j, k)
            Hs[a, b] = Hs[b, a] = v
        # b-loop diagonal already carries the full two-electron part
        # ((ii|ii) resp. (ii|jj)+(ij|ji)); add one-electron + 1/R only
        if i == j:
            Hs[a, a] += 2.0 * hi[i] + 1.0 / R
        else:
            Hs[a, a] += hi[i] + hi[j] + 1.0 / R
    dim_t = len(csf_t)
    Ht = np.zeros((dim_t, dim_t))
    for a, (i, j) in enumerate(csf_t):
        for b, (k, l) in enumerate(csf_t[a:], start=a):
            v = get_int(R, ints, i, k, j, l) \
                - get_int(R, ints, i, l, j, k)
            Ht[a, b] = Ht[b, a] = v
        Ht[a, a] += hi[i] + hi[j] + 1.0 / R
    Es = np.linalg.eigvalsh(Hs)
    Et = np.linalg.eigvalsh(Ht)
    cs = np.linalg.eigh(Hs)[1][:, 0]
    return Es.min(), Et.min(), cs, csf_s


def ionic_fraction(cs, csf_s, theta, nuse):
    """P(both electrons same side) / total, from the ground-CSF
    expectation of Theta1 Theta2. For product CSF ii: P = t_ii^2.
    Cross terms factorize into one-electron Theta integrals."""
    t = {}
    for (i, j), v in theta.items():
        t[(i, j)] = v
        t[(j, i)] = v
    P_same = 0.0
    for a, (i, j) in enumerate(csf_s):
        ca = cs[a]
        if i == j:
            P_same += ca * ca * t[(i, i)] * t[(i, i)]
        else:
            # sym singlet ij: P_same_diag = t_ii t_jj + t_ij^2
            P_same += ca * ca * (t[(i, i)] * t[(j, j)]
                                 + t[(i, j)] ** 2)
        for b in range(a + 1, len(csf_s)):
            k, l = csf_s[b]
            cb = cs[b]
            if i == j and k == l:
                P_same += 2.0 * ca * cb * t[(i, k)] ** 2
            elif i == j:
                P_same += 2.0 * ca * cb * np.sqrt(2.0) * t[(i, k)] * t[(i, l)]
            elif k == l:
                P_same += 2.0 * ca * cb * np.sqrt(2.0) * t[(k, i)] * t[(k, j)]
            else:
                P_same += 2.0 * ca * cb * (t[(i, k)] * t[(j, l)]
                                           + t[(i, l)] * t[(j, k)])
    return P_same


def main():
    # determinism of the engine: reduced single-R variant run twice
    o1 = open(ORB_DET1, "rb").read()
    o2 = open(ORB_DET2, "rb").read()
    print(f"[det] engine (R=1.4014 variant) twice byte-identical: "
          f"{o1 == o2}")

    H, INT, TH = load(ORB_OUT)

    # oracle: self-Coulomb at the smallest grid R (He+ 1s limit 1.25)
    print("\n[oracle: self-Coulomb (sg sg|sg sg) at small R]")
    Rmin = min(INT)
    v = [v for (i, j, k, l), v in INT[Rmin].items()
         if (i, j, k, l) == (0, 0, 0, 0)][0]
    print(f"  R={Rmin}: (1sg 1sg|1sg 1sg) = {v:.6f} "
          f"(He+ 1s united-atom limit 1.25, dev {v - 1.25:+.3f})")

    # CI ladder
    print("\n[CI ladder] D_e with orbital count:")
    for nu in (2, 4, 6):
        rows = []
        for R in sorted(H):
            es, et, cs, csf = build_ci(H[R], INT[R], nu, R)
            rows.append((R, es, et, cs, csf))
        Rmin_row = min(rows, key=lambda r: r[1])
        de = -(Rmin_row[1] + 1.0) * EV
        print(f"  {nu} orbitals: D_e = {de:.4f} eV at R = "
              f"{Rmin_row[0]:.2f} bohr (singlet min "
              f"{Rmin_row[1]:.6f} Ha)")
        print(f"    recovery vs exact 4.7475: {100.0 * de / 4.7475:.1f}%")
    print("    triplet minimum energies (repulsive check):")
    for nu in (2, 6):
        ets = []
        for R in sorted(H):
            es, et, _, _ = build_ci(H[R], INT[R], nu, R)
            ets.append((R, et))
        print(f"    {nu} orbitals: "
              + " ".join(f"{r}:{e:.4f}" for r, e in ets))
        emin = min(ets, key=lambda x: x[1])
        print(f"    triplet min {emin[1]:.6f} Ha at R={emin[0]} "
              f"vs dissociation -1.0 Ha: "
              f"{'REPULSIVE OK' if emin[1] > -1.0 else 'BOUND - STOP'}")

    # Stage 3: maps at 6 orbitals
    print("\n[stage 3] maps at 6 orbitals:")
    for R in sorted(H):
        es, et, cs, csf = build_ci(H[R], INT[R], 6, R)
        pf = 2.0 * ionic_fraction(cs, csf, TH[R], 6)
        print(f"  R={R:5.1f}: E_s={es:.6f} E_t={et:.6f} "
              f"split={(et - es) * EV:+.3f} eV  ionic={pf:.4f}")


if __name__ == "__main__":
    main()
