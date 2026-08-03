#!/usr/bin/env python3
"""dihedral_1sno.py — per-residue backbone dihedral comparison for 1SNO:
seed-3.0 domain-swap trap (block 4) vs good folds (block 1 seed 0.0,
block 3 seed 2.0) vs the native reference, from
min/pmargin/packed_1sno_struct.out FINAL_STRUCTURE_B sections.

Dihedral convention: the sim's force convention,
atan2(B2mag*(B1.N2), N1.N2) over Cα i-1,i,i+1,i+2 for i = 2..NRES-2
(133 dihedrals, labeled by the middle residue r = i+1, 1-based).
Also: native-contact satisfaction, per-residue Kabsch displacement
(global alignment), and domain-boundary (res 98/99) clustering stats.
"""

import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
STRUCTS = ROOT / "min" / "pmargin" / "packed_1sno_struct.out"
SRC = ROOT / "tests" / "waveform_snase_seed_0.0.ergo"
NRES = 136
DOM2_START = 99  # domain 1 = 1..98, domain 2 = 99..136 (SCALING.md)

def get_block(out_file, block):
    lines = open(out_file).read().splitlines()
    i = lines.index(f"FINAL_STRUCTURE_B {block}")
    pts, nat = [], []
    for line in lines[i + 1:i + 1 + NRES]:
        p = line.split(",")
        pts.append([float(p[1]), float(p[2]), float(p[3])])
        nat.append([float(p[4]), float(p[5]), float(p[6])])
    return np.array(pts), np.array(nat)

X_G0, X_NAT = get_block(STRUCTS, 1)   # seed 0.0 good (2.05)
X_G2, _ = get_block(STRUCTS, 3)       # seed 2.0 good (2.29)
X_TRAP, _ = get_block(STRUCTS, 4)     # seed 3.0 trap (9.66)

def vlen(v): return float(np.sqrt((v * v).sum()))
def vdot(a, b): return float((a * b).sum())
def vcross(a, b):
    return np.array([a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]])
def vsub(a, b): return a - b

def dihedral(r1, r2, r3, r4):
    b1, b2, b3 = vsub(r2, r1), vsub(r3, r2), vsub(r4, r3)
    n1, n2 = vcross(b1, b2), vcross(b2, b3)
    b2len = vlen(b2)
    if b2len == 0.0: return 0.0
    return math.atan2(b2len * vdot(b1, n2), vdot(n1, n2))

def profile(X):
    return [math.degrees(dihedral(X[i - 1], X[i], X[i + 1], X[i + 2]))
            for i in range(1, NRES - 2)]

def wrap(d):
    while d > 180.0: d -= 360.0
    while d <= -180.0: d += 360.0
    return d

def kabsch_per_res(X, Y):
    """exact SVD Kabsch of X onto Y; returns rmsd, per-residue |dx|"""
    Xc, Yc = X - X.mean(0), Y - Y.mean(0)
    C = Xc.T @ Yc
    V, S, Wt = np.linalg.svd(C)
    d = np.sign(np.linalg.det(V @ Wt))
    D = np.diag([1.0, 1.0, d])
    R = V @ D @ Wt
    Xr = Xc @ R
    dev = np.linalg.norm(Xr - Yc, axis=1)
    return float(np.sqrt((dev ** 2).mean())), dev

pn, p0, p2, pt = profile(X_NAT), profile(X_G0), profile(X_G2), profile(X_TRAP)

print(f"{'res':>3} {'native':>8} {'good0.0':>8} {'good2.0':>8} {'trap3.0':>8} {'Δtrap-nat':>10} {'Δg0-nat':>8} {'Δg2-nat':>8}")
rows = []
for i in range(NRES - 3):
    r = i + 2
    dn, d0, d2, dt = pn[i], p0[i], p2[i], pt[i]
    dtn, d0n, d2n = wrap(dt - dn), wrap(d0 - dn), wrap(d2 - dn)
    rows.append((r, dn, d0, d2, dt, dtn, d0n, d2n))
    if abs(dtn) >= 5.0 or abs(d0n) >= 5.0 or abs(d2n) >= 5.0:
        print(f"{r:>3} {dn:8.1f} {d0:8.1f} {d2:8.1f} {dt:8.1f} {dtn:10.1f} {d0n:8.1f} {d2n:8.1f}")

devs = [(r, dtn, d0n, d2n) for r, dn, d0, d2, dt, dtn, d0n, d2n in rows]
big = [(r, d) for r, d, _, _ in devs if abs(d) >= 5.0]
big10 = [(r, d) for r, d, _, _ in devs if abs(d) >= 10.0]
print(f"\ntrap-vs-native: {sum(1 for _, d, _, _ in devs if abs(d) < 5.0)} of {len(devs)} dihedrals within 5 deg")
print(f"material deviations (>=5 deg): {len(big)}; (>=10 deg): {len(big10)}")
print("ranked |Δtrap−native| (top 15):")
for r, d, d0n, d2n in sorted(devs, key=lambda x: -abs(x[1]))[:15]:
    tag = "BOUNDARY" if 93 <= r <= 104 else ("D1" if r <= 98 else "D2")
    print(f"  res {r:>3}: {d:+7.1f} deg  [{tag}]  (good0.0 {d0n:+5.1f}, good2.0 {d2n:+5.1f} off native)")

for lo, hi, name in ((2, 98, "domain 1"), (99, 135, "domain 2"), (93, 104, "boundary band 93-104")):
    sub = [abs(d) for r, d, _, _ in devs if lo <= r <= hi]
    print(f"|Δtrap-nat| {name}: mean {np.mean(sub):.2f} max {np.max(sub):.2f} n>=5deg {sum(1 for d in sub if d >= 5.0)}")

# good folds' own deviation level (noise floor for "material")
for nm, pv in (("good0.0", p0), ("good2.0", p2)):
    dd = [abs(wrap(a - b)) for a, b in zip(pv, pn)]
    print(f"{nm}-vs-native: mean |Δ| {np.mean(dd):.2f} deg, max {np.max(dd):.2f}, n>=5deg {sum(1 for d in dd if d >= 5.0)}")

# ── native contact satisfaction ─────────────────────────────────────
import re
src = SRC.read_text()
NCON = {}
for i, j, v in re.findall(r"NATIVE_R0\((\d+), (\d+)\) := ([0-9.]+)", src):
    NCON[(int(i), int(j))] = float(v)
NATIVE_CONTACT = [(int(i), int(j)) for i, j in
                  re.findall(r"NATIVE_CONTACT\((\d+), (\d+)\) := 1", src) if int(i) < int(j)]
print(f"\nnative contacts: {len(NATIVE_CONTACT)}")
for nm, X in (("good0.0", X_G0), ("good2.0", X_G2), ("trap3.0", X_TRAP)):
    deltas = []
    worst = []
    for i, j in NATIVE_CONTACT:
        d = vlen(X[i - 1] - X[j - 1]) - NCON[(i, j)]
        deltas.append(abs(d))
        worst.append((abs(d), i, j))
    worst.sort(reverse=True)
    cross = sum(1 for i, j in NATIVE_CONTACT if (i <= 98) != (j <= 98))
    cd = [abs(vlen(X[i - 1] - X[j - 1]) - NCON[(i, j)]) for i, j in NATIVE_CONTACT if (i <= 98) != (j <= 98)]
    print(f"  {nm}: mean |D-R0| {np.mean(deltas):.3f} max {np.max(deltas):.3f} "
          f"satisfied(<0.5) {sum(1 for d in deltas if d < 0.5)}/{len(deltas)}; "
          f"cross-domain contacts {cross}, their mean |D-R0| {np.mean(cd) if cd else 0.0:.3f} max {max(cd) if cd else 0.0:.3f}")
    print(f"    worst 5: " + " ".join(f"{i}-{j}:{w:.2f}" for w, i, j in worst[:5]))

# ── per-residue Kabsch displacement (anatomy) ───────────────────────
for nm, X in (("good0.0", X_G0), ("trap3.0", X_TRAP)):
    rmsd, dev = kabsch_per_res(X, X_NAT)
    order = np.argsort(-dev)
    d1m, d2m = dev[:98].mean(), dev[98:].mean()
    print(f"\n{nm}: exact-Kabsch RMSD {rmsd:.3f}; per-res displacement D1 mean {d1m:.2f} D2 mean {d2m:.2f}")
    print(f"  worst 8 residues: " + " ".join(f"{r + 1}:{dev[r]:.2f}" for r in order[:8]))
