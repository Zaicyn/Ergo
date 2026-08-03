#!/usr/bin/env python3
"""hessian.py — Hessian spectroscopy of the BBA5 folding landscape.

States: seed 4.0 near-native fold (RMSD 0.29) vs seed 0.0 trap (1.668),
final structures from tests/waveform_bba5_seed_{0.0,4.0}.out.
Energy mirror: the sim's exact terms (from waveform_bba5_seed_0.0.ergo
force sections + COMPUTE_DIAGNOSTICS energy forms):
  Morse bonds D(1-g)^2, g=exp(-A(D-R0)); angles k(cos t - cos t0)^2;
  torsions 2k(1-cos(phi-p0)) (force-convention phi); hydro
  -(S/alpha) H_i H_j exp(-alpha(D-R0)); Go contacts K(D-R0)^2;
  register torsions 2k(1-cos(phi-p0)); steric from the sim's force
  FM = eps(sig/D)^6 along the pair vector  =>  E = eps*sig^6/(5 D^5)
  (inferred and documented).
Hessian: 4-point central differences of E (symmetric by construction),
h convergence tested. numpy.linalg.eigh (documented; trace check as
built-in consistency). Term decomposition by Rayleigh quotient of the
total-H soft eigenvectors against per-term Hessians.
"""

import math
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "tests" / "waveform_bba5_seed_0.0.ergo"

NRES = 23
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

def get_structure(out_file):
    lines = open(out_file).read().splitlines()
    i = lines.index("FINAL_STRUCTURE")
    end = lines.index("END_FINAL_STRUCTURE")
    pts = []
    for line in lines[i + 1:end]:
        p = line.split(",")
        pts.append([float(p[1]), float(p[2]), float(p[3])])
    assert len(pts) == NRES
    return np.array(pts)

X_NATIVE = get_structure(ROOT / "tests" / "waveform_bba5_seed_4.0.out")
X_TRAP = get_structure(ROOT / "tests" / "waveform_bba5_seed_0.0.out")

# ── energy terms ────────────────────────────────────────────────────
def vsub(a, b): return a - b
def vlen(v): return float(np.sqrt((v * v).sum()))
def vdot(a, b): return float((a * b).sum())
def vcross(a, b):
    return np.array([a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]])

def dihedral(r1, r2, r3, r4):
    b1, b2, b3 = vsub(r2, r1), vsub(r3, r2), vsub(r4, r3)
    n1, n2 = vcross(b1, b2), vcross(b2, b3)
    b2len = vlen(b2)
    if b2len == 0.0: return 0.0
    return math.atan2(b2len * vdot(b1, n2), vdot(n1, n2))

def cosang(r1, r2, r3):
    b1, b2 = vsub(r1, r2), vsub(r3, r2)
    l1, l2 = vlen(b1), vlen(b2)
    if l1 == 0 or l2 == 0: return 0.0
    return max(-1.0, min(1.0, vdot(b1, b2) / (l1 * l2)))

def E_morse(X):
    e = 0.0
    for i in range(NRES - 1):
        d = vlen(X[i] - X[i + 1])
        g = math.exp(-MORSE_A * (d - BACKBONE_R0))
        e += BACKBONE_D * (1.0 - g) ** 2
    return e

def E_angle(X):
    e = 0.0
    for i in range(1, NRES - 1):
        c = cosang(X[i - 1], X[i], X[i + 1])
        e += 0.3 * (c - math.cos(ANGT0[i + 1])) ** 2
    return e

def E_torsion(X):
    e = 0.0
    for i in range(1, NRES - 2):
        phi = dihedral(X[i - 1], X[i], X[i + 1], X[i + 2])
        e += 2.0 * 0.2 * (1.0 - math.cos(phi - TORSP0[i + 1]))
    return e

def E_hydro(X):
    e = 0.0
    for i in range(NRES - 3):
        hi = HYDRO.get(i + 1, 0.0)
        if hi <= 0.0: continue
        for j in range(i + 4, NRES):
            hj = HYDRO.get(j + 1, 0.0)
            if hj <= 0.0: continue
            d = vlen(X[i] - X[j])
            if 0.0 < d < HYDRO_CUTOFF:
                e -= (HYDRO_STRENGTH / HYDRO_ALPHA) * hi * hj * math.exp(-HYDRO_ALPHA * (d - HYDRO_R0))
    return e

def E_native(X):
    e = 0.0
    for (i, j) in NATIVE_CONTACT:
        if i < j:
            d = vlen(X[i - 1] - X[j - 1])
            if d > 0.0:
                e += NATIVE_K * (d - NCON[(i, j)]) ** 2
    return e

def E_register(X):
    e = 0.0
    for k in sorted(REG):
        r = REG[k]
        phi = dihedral(X[r['a'] - 1], X[r['b'] - 1], X[r['c'] - 1], X[r['d'] - 1])
        e += 2.0 * r['k'] * (1.0 - math.cos(phi - r['p0']))
    return e

def E_steric(X):
    e = 0.0
    for i in range(NRES - 3):
        for j in range(i + 4, NRES):
            d = vlen(X[i] - X[j])
            if 0.0 < d < STERIC_CUT:
                e += STERIC_EPS * STERIC_SIG ** 6 / (5.0 * d ** 5)
    return e

TERMS = {
    "morse": E_morse, "angle": E_angle, "torsion": E_torsion,
    "hydro": E_hydro, "go": E_native, "register": E_register,
    "steric": E_steric,
}
def E_total(X):
    return sum(f(X) for f in TERMS.values())

# ── Hessian via 4-point central differences ─────────────────────────
def hessian(Efun, X, h):
    n = 3 * NRES
    x = X.reshape(-1).copy()
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            ei = np.zeros(n); ej = np.zeros(n)
            ei[i] = h; ej[j] = h
            e1 = Efun((x + ei + ej).reshape(NRES, 3))
            e2 = Efun((x + ei - ej).reshape(NRES, 3))
            e3 = Efun((x - ei + ej).reshape(NRES, 3))
            e4 = Efun((x - ei - ej).reshape(NRES, 3))
            H[i, j] = H[j, i] = (e1 - e2 - e3 + e4) / (4.0 * h * h)
    return H

def gradient(Efun, X, h):
    n = 3 * NRES
    x = X.reshape(-1).copy()
    g = np.zeros(n)
    for i in range(n):
        ei = np.zeros(n); ei[i] = h
        g[i] = (Efun((x + ei).reshape(NRES, 3)) - Efun((x - ei).reshape(NRES, 3))) / (2.0 * h)
    return g

# ── main analysis ───────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"tables: {len(ANGT0)} ang, {len(TORSP0)} tors, {len(NATIVE_CONTACT)} contacts, {len(REG)} register")
    print(f"E(native) = {E_total(X_NATIVE):.4f}  E(trap) = {E_total(X_TRAP):.4f}")

    # h convergence on a few diagonal elements at the native state
    for h in (1e-3, 1e-4, 1e-5):
        x = X_NATIVE.reshape(-1)
        for idx in (0, 30, 60):
            ei = np.zeros(3 * NRES); ei[idx] = h
            d2 = (E_total((x + ei).reshape(NRES, 3)) - 2 * E_total(X_NATIVE) + E_total((x - ei).reshape(NRES, 3))) / (h * h)
            print(f"  h={h:g} diag[{idx}] 2nd-deriv {d2:.4f}", end="")
        print()

    H_DIAG = 1e-4
    gn = gradient(E_total, X_NATIVE, H_DIAG)
    gt = gradient(E_total, X_TRAP, H_DIAG)
    print(f"|grad| native = {np.linalg.norm(gn):.4f}  trap = {np.linalg.norm(gt):.4f}")

    print("building Hessians (native + trap)...")
    Hn = hessian(E_total, X_NATIVE, H_DIAG)
    Ht = hessian(E_total, X_TRAP, H_DIAG)
    print(f"symmetry: native max|H-H^T| = {np.abs(Hn - Hn.T).max():.2e}, trap = {np.abs(Ht - Ht.T).max():.2e}")

    wn = np.linalg.eigvalsh(Hn)
    wt = np.linalg.eigvalsh(Ht)
    print(f"trace check: native tr(H) {np.trace(Hn):.3f} vs sum(eig) {wn.sum():.3f}; trap {np.trace(Ht):.3f} vs {wt.sum():.3f}")

    np.save("/tmp/hessian_native.npy", Hn)
    np.save("/tmp/hessian_trap.npy", Ht)

    for name, w in (("native", wn), ("trap", wt)):
        med = np.median(w[w > 0.05])
        print(f"{name}: min {w.min():.4f} max {w.max():.3f} median(pos>0.05) {med:.3f}")
        print(f"  first 15 eigenvalues: {np.array2string(w[:15], precision=4, suppress_small=False)}")
        for thr in (1e-3, 1e-2, 5e-2):
            print(f"  |lambda| < {thr:g}: {int(np.sum(np.abs(w) < thr))}")

    # term decomposition at native: Rayleigh quotients of 12 softest modes
    evals_n, evecs_n = np.linalg.eigh(Hn)
    Hterms = {}
    for tname, tf in TERMS.items():
        Hterms[tname] = hessian(tf, X_NATIVE, H_DIAG)
    print("\nterm ownership of the 12 softest native modes (Rayleigh q = v^T H_term v):")
    header = "mode  lambda   " + " ".join(f"{t:>8}" for t in TERMS)
    print(header)
    for m in range(12):
        v = evecs_n[:, m]
        qs = [float(v @ Hterms[t] @ v) for t in TERMS]
        print(f"{m:4d} {evals_n[m]:8.4f} " + " ".join(f"{q:8.3f}" for q in qs))
    print("\nper-term spectra at native (smallest 5 eigenvalues each):")
    for tname in TERMS:
        wt2 = np.linalg.eigvalsh(Hterms[tname])
        print(f"  {tname:>8}: {np.array2string(wt2[:5], precision=4)} (max {wt2.max():.2f})")
