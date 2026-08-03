#!/usr/bin/env python3
"""hessian_1sno.py — Hessian spectroscopy of the 1SNO folding landscape.

States: seed-3.0 domain-swap trap (block 4, full 9.66 / D1 8.73 / D2 2.68)
vs seed-0.0 good fold (block 1, 2.05 / D1 2.34 / D2 0.77), final
structures from min/pmargin/packed_1sno_struct.out (validated packed
baseline + per-block FINAL_STRUCTURE dump). Native = NATIVE_X/Y/Z cols.

Energy mirror: same terms as hessian.py (BBA5), constants verified
identical in tests/waveform_snase_seed_0.0.ergo:
  Morse bonds D(1-g)^2, g=exp(-A(D-R0)); angles 0.3(cos t - cos t0)^2;
  torsions 2k(1-cos(phi-p0)) k=0.2 (force-convention phi);
  hydro -(S/alpha) H_i H_j exp(-alpha(D-R0)), |i-j|>=4;
  Go contacts K(D-R0)^2 on NATIVE_CONTACT pairs;
  register torsions 2k(1-cos(phi-p0)) (246 quads);
  steric eps sig^6/(5 D^5), |i-j|>=4 (HB_CAP=0 in the packed recipe, so
  the sim's HBOND_MATRIX skip never triggers — mirror is exact).
Hessian: mixed central formula H_ij = [E(++)-E(+0)-E(0+)+E(00)]/h^2
(BBA5's 4-point form costs 4x for the same leading accuracy at N=136;
diagonals use the standard 3-point central form; H symmetrized).
h convergence checked on diagonals. numpy.linalg.eigh; trace check.
All energy terms vectorized (numpy) — ~85k evals per Hessian.
"""

import math
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "tests" / "waveform_snase_seed_0.0.ergo"
STRUCTS = ROOT / "min" / "pmargin" / "packed_1sno_struct.out"

NRES = 136
BACKBONE_R0, BACKBONE_D, MORSE_A = 1.52, 1.4, 1.0
STERIC_SIG, STERIC_EPS, STERIC_CUT = 1.60, 0.1, 2.5
HYDRO_STRENGTH, HYDRO_R0, HYDRO_CUTOFF, HYDRO_ALPHA = 0.0020, 4.0, 8.0, 1.0
NATIVE_K = 1.00

# ── parse tables from the source ────────────────────────────────────
src = SRC.read_text()
def get_floats(pattern):
    return [(int(a), float(b)) for a, b in re.findall(pattern, src)]

ANGT0 = dict(get_floats(r"RES_ANGT0\((\d+)\) := ([0-9.\-]+)"))
TORSP0 = dict(get_floats(r"RES_TORSP0\((\d+)\) := ([0-9.\-]+)"))
HYDRO = dict(get_floats(r"RES_HYDRO\((\d+)\) := ([0-9.\-]+)"))
REG = {}
for k, a in re.findall(r"REG_A\((\d+)\) := (\d+)", src):
    REG.setdefault(int(k), {})['a'] = int(a)
for k, a in re.findall(r"REG_B\((\d+)\) := (\d+)", src):
    REG[int(k)]['b'] = int(a)
for k, a in re.findall(r"REG_C\((\d+)\) := (\d+)", src):
    REG[int(k)]['c'] = int(a)
for k, a in re.findall(r"REG_D\((\d+)\) := (\d+)", src):
    REG[int(k)]['d'] = int(a)
for k, v in re.findall(r"REG_K\((\d+)\) := ([0-9.]+)", src):
    REG[int(k)]['k'] = float(v)
for k, v in re.findall(r"REG_P0\((\d+)\) := ([0-9.\-]+)", src):
    REG[int(k)]['p0'] = float(v)
NCON = {}
for i, j, v in re.findall(r"NATIVE_R0\((\d+), (\d+)\) := ([0-9.]+)", src):
    NCON[(int(i), int(j))] = float(v)
NATIVE_CONTACT = set()
for i, j in re.findall(r"NATIVE_CONTACT\((\d+), (\d+)\) := 1", src):
    NATIVE_CONTACT.add((int(i), int(j)))

def get_block(out_file, block):
    """parse FINAL_STRUCTURE_B <block> section -> (cur, native) (NRES,3)"""
    lines = open(out_file).read().splitlines()
    i = lines.index(f"FINAL_STRUCTURE_B {block}")
    pts, nat = [], []
    for line in lines[i + 1:i + 1 + NRES]:
        p = line.split(",")
        pts.append([float(p[1]), float(p[2]), float(p[3])])
        nat.append([float(p[4]), float(p[5]), float(p[6])])
    return np.array(pts), np.array(nat)

X_GOOD, X_NAT = get_block(STRUCTS, 1)   # seed 0.0 good fold
X_TRAP, _ = get_block(STRUCTS, 4)       # seed 3.0 domain-swap trap

# ── precomputed index arrays (1-based tables -> 0-based) ─────────────
BI = np.arange(NRES - 1)                                  # bonds i,i+1
AI = np.arange(1, NRES - 1)                               # angle center i
TI = np.arange(1, NRES - 2)                               # torsion: i-1..i+2
ANG_T0 = np.array([ANGT0[i + 1] for i in AI])
TOR_P0 = np.array([TORSP0[i + 1] for i in TI])
REG_KS = sorted(REG)
RQ = np.array([[REG[k]['a'], REG[k]['b'], REG[k]['c'], REG[k]['d']] for k in REG_KS]) - 1
RK = np.array([REG[k]['k'] for k in REG_KS])
RP = np.array([REG[k]['p0'] for k in REG_KS])
ii, jj = np.triu_indices(NRES, 4)                          # |i-j|>=4 pairs
HP = np.array([HYDRO.get(i + 1, 0.0) * HYDRO.get(j + 1, 0.0) for i, j in zip(ii, jj)])
CI = np.array([i for (i, j) in NATIVE_CONTACT if i < j]) - 1
CJ = np.array([j for (i, j) in NATIVE_CONTACT if i < j]) - 1
CR0 = np.array([NCON[(i + 1, j + 1)] for i, j in zip(CI, CJ)])

def dihedral_batch(P, Q, R, S):
    """dihedrals of quad rows (M,3)x4 -> (M,) force convention"""
    b1, b2, b3 = Q - P, R - Q, S - R
    n1 = np.cross(b1, b2)
    n2 = np.cross(b2, b3)
    b2len = np.linalg.norm(b2, axis=1)
    return np.arctan2(b2len * np.einsum("ij,ij->i", b1, n2),
                      np.einsum("ij,ij->i", n1, n2))

def E_morse(X):
    d = np.linalg.norm(X[BI] - X[BI + 1], axis=1)
    g = np.exp(-MORSE_A * (d - BACKBONE_R0))
    return float(BACKBONE_D * np.sum((1.0 - g) ** 2))

def E_angle(X):
    b1, b2 = X[AI - 1] - X[AI], X[AI + 1] - X[AI]
    c = np.einsum("ij,ij->i", b1, b2) / (np.linalg.norm(b1, axis=1) * np.linalg.norm(b2, axis=1))
    c = np.clip(c, -1.0, 1.0)
    return float(0.3 * np.sum((c - np.cos(ANG_T0)) ** 2))

def E_torsion(X):
    phi = dihedral_batch(X[TI - 1], X[TI], X[TI + 1], X[TI + 2])
    return float(2.0 * 0.2 * np.sum(1.0 - np.cos(phi - TOR_P0)))

def E_register(X):
    phi = dihedral_batch(X[RQ[:, 0]], X[RQ[:, 1]], X[RQ[:, 2]], X[RQ[:, 3]])
    return float(2.0 * np.sum(RK * (1.0 - np.cos(phi - RP))))

def taper(d, cut, w):
    """cosine switch 1 -> 0 over [cut-w, cut]: removes the sim's hard
    cutoff step, which otherwise injects spurious dE/h^2 curvature into
    finite-difference Hessians for pairs sitting within h of the cut
    (verified: trap pair 41-55 at 2.50011 produced a +-1.7e5 mode)."""
    s = np.ones_like(d)
    m = (d > cut - w) & (d < cut)
    s[m] = 0.5 * (1.0 + np.cos(np.pi * (d[m] - (cut - w)) / w))
    s[d >= cut] = 0.0
    return s

def E_hydro(X):
    d = np.linalg.norm(X[ii] - X[jj], axis=1)
    s = taper(d, HYDRO_CUTOFF, 0.1)
    m = (d > 0.0) & (s > 0.0) & (HP > 0.0)
    return float(-(HYDRO_STRENGTH / HYDRO_ALPHA) *
                 np.sum(HP[m] * s[m] * np.exp(-HYDRO_ALPHA * (d[m] - HYDRO_R0))))

def E_native(X):
    d = np.linalg.norm(X[CI] - X[CJ], axis=1)
    return float(NATIVE_K * np.sum((d - CR0) ** 2))

def E_steric(X):
    d = np.linalg.norm(X[ii] - X[jj], axis=1)
    s = taper(d, STERIC_CUT, 0.1)
    m = (d > 0.0) & (s > 0.0)
    return float(STERIC_EPS * STERIC_SIG ** 6 / 5.0 * np.sum(s[m] * d[m] ** -5))

TERMS = {
    "morse": E_morse, "angle": E_angle, "torsion": E_torsion,
    "hydro": E_hydro, "go": E_native, "register": E_register,
    "steric": E_steric,
}
def E_total(X):
    return sum(f(X) for f in TERMS.values())

# ── Hessian: mixed central differences ───────────────────────────────
def hessian(Efun, X, h):
    n = 3 * NRES
    x = X.reshape(-1)
    e0 = Efun(X)
    ep = np.empty(n)
    em = np.empty(n)
    for i in range(n):
        ei = np.zeros(n); ei[i] = h
        ep[i] = Efun((x + ei).reshape(NRES, 3))
        em[i] = Efun((x - ei).reshape(NRES, 3))
    H = np.zeros((n, n))
    np.fill_diagonal(H, (ep - 2.0 * e0 + em) / (h * h))
    for i in range(n):
        ei = np.zeros(n); ei[i] = h
        for j in range(i + 1, n):
            ej = np.zeros(n); ej[j] = h
            epp = Efun((x + ei + ej).reshape(NRES, 3))
            H[i, j] = (epp - ep[i] - ep[j] + e0) / (h * h)
    return (H + H.T) / 2.0 - np.diag(np.diag(H)) + np.diag(np.diag(H))

def gradient(Efun, X, h):
    n = 3 * NRES
    x = X.reshape(-1)
    g = np.zeros(n)
    for i in range(n):
        ei = np.zeros(n); ei[i] = h
        g[i] = (Efun((x + ei).reshape(NRES, 3)) - Efun((x - ei).reshape(NRES, 3))) / (2.0 * h)
    return g

def mode_residue_report(tag, evals, evecs, nmodes=12, top=8):
    print(f"\n{tag}: residue localization of the {nmodes} softest modes")
    print("mode  lambda   top residues (resid:share of |v|^2)")
    for m in range(nmodes):
        v = evecs[:, m].reshape(NRES, 3)
        p = (v * v).sum(axis=1)
        p = p / p.sum()
        order = np.argsort(-p)[:top]
        dom1 = p[:98].sum()
        s = " ".join(f"{r + 1}:{p[r]:.2f}" for r in order)
        print(f"{m:4d} {evals[m]:8.4f}  D1share {dom1:.2f}  {s}")

# ── main analysis ───────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"tables: {len(ANGT0)} ang, {len(TORSP0)} tors, {len(NATIVE_CONTACT)} contacts, {len(REG)} register")
    print(f"E(good) = {E_total(X_GOOD):.4f}  E(trap) = {E_total(X_TRAP):.4f}  E(native-ref) = {E_total(X_NAT):.4f}")

    for h in (1e-3, 1e-4, 1e-5):
        x = X_GOOD.reshape(-1)
        out = []
        for idx in (0, 150, 300):
            ei = np.zeros(3 * NRES); ei[idx] = h
            d2 = (E_total((x + ei).reshape(NRES, 3)) - 2 * E_total(X_GOOD)
                  + E_total((x - ei).reshape(NRES, 3))) / (h * h)
            out.append(f"diag[{idx}]={d2:.4f}")
        print(f"  h={h:g}  " + "  ".join(out))

    H_DIAG = 1e-4
    print(f"|grad| good = {np.linalg.norm(gradient(E_total, X_GOOD, H_DIAG)):.4f}  "
          f"trap = {np.linalg.norm(gradient(E_total, X_TRAP, H_DIAG)):.4f}")

    print("building Hessians (good + trap)...")
    Hg = hessian(E_total, X_GOOD, H_DIAG)
    Ht = hessian(E_total, X_TRAP, H_DIAG)
    print(f"symmetry: good max|H-H^T| = {np.abs(Hg - Hg.T).max():.2e}, trap = {np.abs(Ht - Ht.T).max():.2e}")
    np.save("/tmp/hessian_1sno_good.npy", Hg)
    np.save("/tmp/hessian_1sno_trap.npy", Ht)

    eg, vg = np.linalg.eigh(Hg)
    et, vt = np.linalg.eigh(Ht)
    print(f"trace check: good tr(H) {np.trace(Hg):.3f} vs {eg.sum():.3f}; trap {np.trace(Ht):.3f} vs {et.sum():.3f}")
    for name, w in (("good", eg), ("trap", et)):
        pos = w[w > 0.05]
        print(f"{name}: min {w.min():.4f} max {w.max():.3f} median(pos>0.05) {np.median(pos):.3f}")
        print(f"  first 15 eigenvalues: {np.array2string(w[:15], precision=4)}")
        for thr in (1e-3, 1e-2, 5e-2):
            print(f"  |lambda| < {thr:g}: {int(np.sum(np.abs(w) < thr))}")
    # spectral overlap: are they twins? compare full spectra quantiles
    qs = np.linspace(0.05, 0.95, 19)
    qg, qt = np.quantile(eg, qs), np.quantile(et, qs)
    print("\nspectral quantiles (good vs trap):")
    for q, a, b in zip(qs, qg, qt):
        print(f"  q{q:.2f}  good {a:9.4f}  trap {b:9.4f}  ratio {a / b if b != 0 else float('nan'):6.2f}")

    mode_residue_report("GOOD", eg, vg)
    mode_residue_report("TRAP", et, vt)

    print("\nbuilding per-term Hessians at the good state (term ownership)...")
    Hterms = {tname: hessian(tf, X_GOOD, H_DIAG) for tname, tf in TERMS.items()}
    print("term ownership of the 12 softest good modes (Rayleigh q = v^T H_term v):")
    print("mode  lambda   " + " ".join(f"{t:>8}" for t in TERMS))
    for m in range(12):
        v = vg[:, m]
        qs2 = [float(v @ Hterms[t] @ v) for t in TERMS]
        print(f"{m:4d} {eg[m]:8.4f} " + " ".join(f"{q:8.3f}" for q in qs2))
