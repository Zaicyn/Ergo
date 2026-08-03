#!/usr/bin/env python3
"""orient_errmode.py — WHY doesn't the orientation term work?
For the baseline and early-k05 final states (best block):
1. per-domain rigid transforms vs the global one (rotation vs translation
   anatomy of the placement error),
2. the 53 interface quartets' deviation from native in the final state
   (does the term SEE the error, or is the error invisible to it?),
3. cross-domain contact profile (satisfied vs stretched).
"""
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"
NRES = 556
DOMS = ((1, 152), (153, 320), (321, 440), (441, 556))
DOMNAMES = ("A2", "A3", "B1", "B2")

import re
src = (PM / "sdrd_white_full.ergo").read_text()
NCON = {}
for i, j, v in re.findall(r"NATIVE_R0\((\d+), (\d+)\) := ([0-9.]+)", src):
    NCON[(int(i), int(j))] = float(v)
NATIVE_CONTACT = [(int(i), int(j)) for i, j in
                  re.findall(r"NATIVE_CONTACT\((\d+), (\d+)\) := 1", src) if int(i) < int(j)]
BNDS = (152, 320, 440)

# quartets: recompute exactly as gen_orient (same selection)
def dihedral(r1, r2, r3, r4):
    b1, b2, b3 = r2 - r1, r3 - r2, r4 - r3
    n1 = np.cross(b1, b2); n2 = np.cross(b2, b3)
    b2len = float(np.linalg.norm(b2))
    if b2len == 0.0: return 0.0
    return math.atan2(b2len * float(b1 @ n2), float(n1 @ n2))

def get_block(out_file, block):
    lines = open(out_file).read().splitlines()
    i = lines.index(f"FINAL_STRUCTURE_B {block}")
    cur, nat = [], []
    for line in lines[i + 1:i + 1 + NRES]:
        p = line.split(",")
        cur.append([float(p[1]), float(p[2]), float(p[3])])
        nat.append([float(p[4]), float(p[5]), float(p[6])])
    return np.array(cur), np.array(nat)

def kabsch(X, Y):
    Xc, Yc = X - X.mean(0), Y - Y.mean(0)
    V, S, Wt = np.linalg.svd(Xc.T @ Yc)
    D = np.diag([1.0, 1.0, np.sign(np.linalg.det(V @ Wt))])
    R = V @ D @ Wt
    return R, X.mean(0), Y.mean(0)

def rot_angle(R):
    c = (np.trace(R) - 1.0) / 2.0
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))

for fn, tag in (("dock_sim_struct.out", "baseline sim"),
                ("orient_early_sim_k05_struct.out", "early orient k05")):
    X, N = get_block(PM / fn, 4)   # best block (seed 3.0)
    Rg, cg, ng = kabsch(X, N)
    print(f"\n=== {tag} (block 4) ===")
    print("per-domain placement vs global alignment:")
    quads_all = []
    for (lo, hi), nm in zip(DOMS, DOMNAMES):
        Rd, cd, nd = kabsch(X[lo - 1:hi], N[lo - 1:hi])
        # domain COM placement error under per-domain vs global alignment
        com_final = X[lo - 1:hi].mean(0)
        com_nat = N[lo - 1:hi].mean(0)
        # where the domain's COM goes under the GLOBAL transform:
        g_com = (com_final - cg) @ Rg + ng
        err_com = np.linalg.norm(g_com - com_nat)
        # relative rotation of the domain's own alignment vs global
        ang = rot_angle(Rd @ Rg.T)
        print(f"  {nm}: COM placement err {err_com:6.2f}  relative rotation {ang:6.1f} deg")
    # quartet deviations
    devs = []
    for i, j in NATIVE_CONTACT:
        bnd = None
        for b in BNDS:
            if i <= b < j:
                bnd = b
        if bnd is None:
            continue
        for q in ((i - 1, i, j, j + 1), (i, i + 1, j - 1, j)):
            if q[0] < 1 or q[1] > bnd or q[2] <= bnd or q[3] > NRES:
                continue
            p0 = dihedral(*(N[t - 1] for t in q))
            d = abs(dihedral(*(X[t - 1] for t in q)) - p0)
            d = min(d, 2 * math.pi - d)
            devs.append((math.degrees(d), q))
    devs.sort(reverse=True)
    print(f"interface quartets: n={len(devs)} mean dev {np.mean([d for d, _ in devs]):.1f} deg "
          f"max {devs[0][0]:.1f} (>30deg: {sum(1 for d, _ in devs if d > 30)})")
    print("  worst 6: " + " ".join(f"{q}:{d:.0f}" for d, q in devs[:6]))
    # cross-domain contact profile
    prof = []
    for i, j in NATIVE_CONTACT:
        if any(i <= b < j for b in BNDS):
            dd = abs(np.linalg.norm(X[i - 1] - X[j - 1]) - NCON[(i, j)])
            prof.append((dd, i, j))
    prof.sort(reverse=True)
    print(f"cross contacts: {sum(1 for d, _, _ in prof if d < 0.5)}/{len(prof)} satisfied; "
          f"worst 5: " + " ".join(f"{i}-{j}:{d:.2f}" for d, i, j in prof[:5]))
