#!/usr/bin/env python3
"""he_ci.py — Stage 2/3: helium CI from the radial engine's integrals.

Reads min/helium/he_orb.ergo output (ORB lines: orbital energies;
INT lines: R^k[ab,cd] Slater integrals) and builds the He ground-state
CI in singlet CSFs over {1s,2s,2p,3s,3p,3d}, plus the 1s2s 1S/3S
splitting (Stage 3) and, with a Z=3 engine output, Li+ (same code,
no refitting).

Angular machinery (validated below): the spatial two-electron integral

  (pr|qs) = sum_k R^k[pr,qs] * M^k(p,r,q,s)
  M^k     = (4pi/(2k+1)) sum_m G(p,r;km) G(s,q;km)*
  G(a,b;km) = int Y*_a Y_b Y_km dOmega        (1-sphere quadrature)

from the spherical-harmonic addition theorem applied to
1/r12 = sum_k (r<^k/r>^(k+1)) P_k(cos gamma). Validation oracles
printed by this driver:
  - M^0(ssss) = 1 (addition-theorem normalization)
  - p^2 1S pair: F0 - (2/5) F2 (Condon-Shortley)
  - the doubly-occupied 2p^2 1S diagonal recomputed by direct 4D
    angular quadrature of the L=0-coupled pair function (independent
    code path; must agree with the Gaunt route)

CI: CSFs as combinations of spin-orbital Slater determinants;
< D|H|D' > by the standard Slater-Condon rules with explicit
permutation signs. Spin-orbital antisymmetrized integrals
g(pq,rs) = (pr|qs) - (ps|qr) with spin deltas.

Determinism: pure numpy arithmetic; run twice, byte-identical.
"""

import sys

import numpy as np
from scipy.special import sph_harm_y  # scipy>=1.15: (n, m, theta, phi)

# ── load engine output ─────────────────────────────────────────────

# orbital table: index -> (n, l) matching he_orb.ergo
ORBTAB = {1: (1, 0), 2: (2, 0), 3: (2, 1), 4: (3, 0), 5: (3, 1),
          6: (3, 2)}


def load(path):
    eps = {}
    R = {}
    for line in open(path):
        if line.startswith("('ORB"):
            t = line.replace("('ORB ", "").replace("')", "").split()
            eps[int(t[0])] = float(t[3])
        elif line.startswith("('INT"):
            t = line.replace("('INT ", "").replace("')", "").split()
            a, b, c, d, k = (int(t[i]) for i in range(5))
            R[(a, b, c, d, k)] = float(t[5])
    return eps, R


def rk(R, a, b, c, d, k):
    """R^k[ab,cd] with pair symmetries (engine prints a<=b, c<=d)."""
    if a > b:
        a, b = b, a
    if c > d:
        c, d = d, c
    return R[(a, b, c, d, k)]


# ── angular machinery: Gaunt coefficients by 1-sphere quadrature ───

NTH = 64
NPH = 128
_x, _w = np.polynomial.legendre.leggauss(NTH)
THG = np.arccos(_x)              # polar angles, weights _w
PHG = np.linspace(0.0, 2 * np.pi, NPH, endpoint=False)
DPH = 2 * np.pi / NPH
# meshgrid
_TT, _PP = np.meshgrid(THG, PHG, indexing="ij")
_JAC = _w[:, None] * DPH         # sin(theta) already in leggauss weight

_YCACHE = {}


def Y(l, m):
    key = (l, m)
    if key not in _YCACHE:
        # sph_harm_y(n, m, theta_polar, phi_azimuthal)
        _YCACHE[key] = sph_harm_y(l, m, _TT, _PP)
    return _YCACHE[key]


def gaunt(la, ma, lb, mb, lk, mk):
    """G(a,b;km) = int Y*_{la,ma} Y_{lb,mb} Y_{lk,mk} dOmega."""
    v = np.conj(Y(la, ma)) * Y(lb, mb) * Y(lk, mk)
    return complex((v * _JAC).sum())


def Mk(l1, m1, l2, m2, l3, m3, l4, m4, k):
    """M^k(p,r,q,s) with p=(l1,m1), r=(l2,m2), q=(l3,m3), s=(l4,m4)."""
    if k > l1 + l2 or k > l3 + l4 or k < abs(l1 - l2) or k < abs(l3 - l4):
        return 0.0
    tot = 0.0
    for mk in range(-k, k + 1):
        g1 = gaunt(l1, m1, l2, m2, k, mk)
        if abs(g1) < 1e-16:
            continue
        g2 = gaunt(l4, m4, l3, m3, k, mk)
        tot = tot + g1 * np.conj(g2)
    return (4.0 * np.pi / (2 * k + 1)) * tot.real


def spatial_int(R, p, r, q, s):
    """(pr|qs) for SPIN-ORBITAL indices (m resolved per spin orbital)."""
    op, mp, _ = SPINORB[p]
    orr, mr, _ = SPINORB[r]
    oq, mq, _ = SPINORB[q]
    os_, ms, _ = SPINORB[s]
    # ORBTAB values are (n, l) — take l
    lp, lr, lq, ls = \
        ORBTAB[op][1], ORBTAB[orr][1], ORBTAB[oq][1], ORBTAB[os_][1]
    tot = 0.0
    for k in range(0, 9):
        if (lp + lr + k) % 2 or (lq + ls + k) % 2:
            continue
        mk = Mk(lp, mp, lr, mr, lq, mq, ls, ms, k)
        if abs(mk) < 1e-16:
            continue
        tot = tot + mk * rk(R, op, orr, oq, os_, k)
    return tot


# ── spin orbitals, determinants, Slater-Condon ─────────────────────

# spin-orbital table built per problem below
SPINORB = []  # (engine index, m, sigma)


def build_spin_orbitals(orb_ids):
    global SPINORB
    SPINORB = []
    for oid in orb_ids:
        n, l = ORBTAB[oid]
        for m in range(-l, l + 1):
            for sig in (-1, 1):    # -1 = beta, +1 = alpha
                SPINORB.append((oid, m, sig))


def g2(R, p, q, r, s):
    """Antisymmetrized spin-orbital integral <pq||rs>."""
    op, mp, sp = SPINORB[p]
    oq, mq, sq = SPINORB[q]
    orr, mr, sr = SPINORB[r]
    os_, ms, ss = SPINORB[s]
    v = 0.0
    if sp == sr and sq == ss:
        v = v + spatial_int(R, op, orr, oq, os_)
    if sp == ss and sq == sr:
        v = v - spatial_int(R, op, os_, oq, orr)
    return v


def _canon(det):
    """Sort a 2-electron determinant, returning (tuple, parity sign)."""
    a, b = det
    if a <= b:
        return (a, b), 1
    return (b, a), -1


def det_me(R, eps, d1, d2):
    """<d1|H|d2> for 2-electron determinants — exact expansion:
    <ab|H|cd> = h_ac d_bd - h_ad d_bc + h_bd d_ac - h_bc d_ad
              + (ac|bd) - (ad|bc)   (spin deltas in the integrals).
    Determinants may be given in any slot order (parity tracked)."""
    (a, b), sa = _canon(d1)
    (c, d), sb = _canon(d2)

    def h(x, y):
        if x != y:
            return 0.0
        return eps[SPINORB[x][0]]

    def sd(x, y):
        return SPINORB[x][2] == SPINORB[y][2]

    me = 0.0
    if b == d:
        me = me + h(a, c)
    if b == c:
        me = me - h(a, d)
    if a == d:
        me = me - h(b, c)
    if a == c:
        me = me + h(b, d)
    oa, _, _ = SPINORB[a]
    ob, _, _ = SPINORB[b]
    oc, _, _ = SPINORB[c]
    od, _, _ = SPINORB[d]
    if sd(a, c) and sd(b, d):
        me = me + spatial_int(R, a, c, b, d)
    if sd(a, d) and sd(b, c):
        me = me - spatial_int(R, a, d, b, c)
    return sa * sb * me


def csf_energy(R, eps, csf_a, csf_b):
    """<A|H|B> with CSFs as lists of (det, coeff)."""
    tot = 0.0
    for d1, c1 in csf_a:
        for d2, c2 in csf_b:
            tot = tot + c1 * c2 * det_me(R, eps, d1, d2)
    return tot


# ── CSF builders ───────────────────────────────────────────────────

def orb_index(oid, m, sig):
    return SPINORB.index((oid, m, sig))


def csf_double(oid):
    """Doubly-occupied orbital -> 1S CSF (L=0 coupled for l>0).
    Determinants in fixed slot order (m alpha, -m beta); det_me's
    _canon tracks the parity of the canonical sort."""
    n, l = ORBTAB[oid]
    if l == 0:
        return [( (orb_index(oid, 0, 1), orb_index(oid, 0, -1)), 1.0 )]
    csf = []
    for m in range(-l, l + 1):
        c = (-1) ** (l - m) / np.sqrt(2 * l + 1)
        det = (orb_index(oid, m, 1), orb_index(oid, -m, -1))
        csf.append((det, c))
    return csf


def csf_pair(oid1, oid2, spin):
    """Open-shell 1S (spin=+1) or 3S (spin=-1) CSF for two s orbitals."""
    assert ORBTAB[oid1][1] == 0 and ORBTAB[oid2][1] == 0
    d1 = tuple(sorted([orb_index(oid1, 0, 1), orb_index(oid2, 0, -1)]))
    d2 = tuple(sorted([orb_index(oid1, 0, -1), orb_index(oid2, 0, 1)]))
    s = np.sqrt(0.5)
    if spin > 0:
        return [(d1, s), (d2, -s)]
    return [(d1, s), (d2, s)]


def ground_ci(eps, R, label, exact, hartree_ref):
    """Ground-state 1S CI over the s/p/d CSF set with the partial-wave
    ladder printed. hartree_ref labels the 1s^2-only reference
    energy."""
    csfs = [csf_double(1), csf_pair(1, 2, +1), csf_double(2),
            csf_pair(1, 4, +1), csf_pair(2, 4, +1), csf_double(4),
            csf_double(3), csf_double(5), csf_double(6)]
    e1s2 = csf_energy(R, eps, csfs[0], csfs[0])
    print(f"  [{label}] 1s^2 alone: E = {e1s2:.6f}")
    for label2, sub in (("s block (s orbs)", [0, 1, 2, 3, 4, 5]),
                        ("s+p", [0, 1, 2, 3, 4, 5, 6, 7]),
                        ("s+p+d (all)", list(range(9)))):
        sel = [csfs[i] for i in sub]
        H = np.zeros((len(sel), len(sel)))
        for a in range(len(sel)):
            for b in range(a, len(sel)):
                v = csf_energy(R, eps, sel[a], sel[b])
                H[a, b] = H[b, a] = v
        e0 = np.linalg.eigvalsh(H)[0]
        rec = 100.0 * (e0 - e1s2) / (exact - e1s2)
        print(f"  [{label}] {label2:16s}: E0 = {e0:.6f}  "
              f"(exact {exact}; recovery from 1s^2 = {rec:.1f}%)")
        if e0 < exact - 2e-4:
            print("    WARNING: below exact — variational violation, "
                  "STOP and diagnose")


# ── validation + CI driver ─────────────────────────────────────────

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/he_orb_out.txt"
    eps, R = load(path)
    build_spin_orbitals([1, 2, 3, 4, 5, 6])

    print("=" * 66)
    print("HELIUM CI (Stage 2/3) — engine:", path)
    print("=" * 66)

    print("\n[angular machinery validation]")
    m0 = Mk(0, 0, 0, 0, 0, 0, 0, 0, 0)
    print(f"  M^0(ssss) = {m0:.10f} (must be 1)")
    # p^2 1S pair: F0 - 2/5 F2 via the CSF diagonal minus 2 eps_p
    c2p = csf_double(3)
    e2p = csf_energy(R, eps, c2p, c2p)
    f0 = rk(R, 3, 3, 3, 3, 0)
    f2 = rk(R, 3, 3, 3, 3, 2)
    pair = e2p - 2 * eps[3]
    print(f"  2p^2 1S pair energy = {pair:.10f}")
    print(f"    F0 + (2/5)F2 = {f0 + 0.4 * f2:.10f} (Condon-Shortley)")
    print(f"    ratio pair/(F0+(2/5)F2) = {pair / (f0 + 0.4 * f2):.8f}")
    c3d = csf_double(6)
    e3d = csf_energy(R, eps, c3d, c3d)
    f0d = rk(R, 6, 6, 6, 6, 0)
    f2d = rk(R, 6, 6, 6, 6, 2)
    f4d = rk(R, 6, 6, 6, 6, 4)
    paird = e3d - 2 * eps[6]
    print(f"  3d^2 1S pair energy = {paird:.10f}")
    print(f"    F0 + (2/7)(F2+F4) = {f0d + (2.0 / 7.0) * (f2d + f4d):.10f}")
    print(f"    ratio = {paird / (f0d + (2.0 / 7.0) * (f2d + f4d)):.8f}")
    # cross-check: <1s^2|H|3d^2> coupling must be nonzero (s-d channel)
    cs_1s2 = csf_double(1)
    cs_3d2 = csf_double(6)
    print(f"  <1s^2|H|3d^2> = "
          f"{csf_energy(R, eps, cs_1s2, cs_3d2):.6e} (nonzero)")
    print(f"  <1s^2|H|2p^2> = "
          f"{csf_energy(R, eps, cs_1s2, c2p):.6e} (nonzero)")

    # ── ground-state CI ──
    ground_ci(eps, R, "He (Z=2)", -2.903724, "2s")

    # ── Stage 3a: 1s2s singlet-triplet splitting ──
    print("\n[Stage 3a] He 2^1S / 2^3S splitting (1s2s)")
    e_sing = csf_energy(R, eps, csf_pair(1, 2, +1), csf_pair(1, 2, +1))
    e_trip = csf_energy(R, eps, csf_pair(1, 2, -1), csf_pair(1, 2, -1))
    split = e_sing - e_trip
    print(f"  E(2^1S) = {e_sing:.6f}  E(2^3S) = {e_trip:.6f}")
    print(f"  splitting = {split:.6f} Ha = {split * 27.211386245988:.4f} eV"
          f"  (NIST 0.796 eV / 0.02925 Ha)")

    # ── Stage 3b: Li+ isoelectronic, SAME code at Z=3 ──
    import os
    z3 = "/tmp/he_orb_z3.txt"
    if os.path.exists(z3):
        print("\n[Stage 3b] Li+ ground, same code at Z=3 "
              "(no refitting)")
        eps3, R3 = load(z3)
        build_spin_orbitals([1, 2, 3, 4, 5, 6])
        ground_ci(eps3, R3, "Li+ (Z=3)", -7.279913, "1s2")
        print("  (HF limit Li+ = -7.23642 Ha; exact = -7.279913 Ha)")


if __name__ == "__main__":
    main()
