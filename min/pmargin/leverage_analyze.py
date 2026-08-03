#!/usr/bin/env python3
"""leverage_analyze.py — leverage-response curve: placement vs s at fixed k.

Cells: s=0 (orient_early_{oracle,sim}_k05, the null baseline) and
s ∈ {8,16,30} × k ∈ {0.5,1.0} × {oracle,sim} (leverage_*.out).
Per cell: best/mean full RMSD, mean internal-only, mean placement,
IFACE satisfaction, and per-domain COM placement error + rotation
(best block) from the structure dumps.
"""
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"
NRES = 556
NS = (152, 168, 120, 116)
DOMS = ((1, 152), (153, 320), (321, 440), (441, 556))

CELLS = [
    (0, 0.5, "oracle", "orient_early_oracle_k05.out"),
    (0, 0.5, "sim", "orient_early_sim_k05.out"),
] + [(s, k, init, f"leverage_{init}_s{s}_k{kt}.out")
     for s in (8, 16, 30) for k, kt in ((0.5, "05"), (1.0, "10"))
     for init in ("oracle", "sim")]

def dom_rows(path):
    rows = {}
    for ln in open(path):
        if ln.startswith("DOM "):
            p = ln.split()
            rows[int(p[1])] = tuple(float(x) for x in p[3:8])
    return rows

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
    return V @ D @ Wt, X.mean(0), Y.mean(0)

def rot_angle(R):
    return math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(R) - 1.0) / 2.0))))

print(f"{'s':>3} {'k':>4} {'init':<7} {'best':>6} {'mean':>6} {'intern':>7} {'place':>7} {'bestblk place':>13}")
curve = {}
for s, k, init, fn in CELLS:
    rows = dom_rows(PM / fn)
    fulls = np.array([rows[b][0] for b in sorted(rows)])
    intern, place = [], []
    for b in sorted(rows):
        f, d1, d2, d3, d4 = rows[b]
        i2 = sum(n * d * d for n, d in zip(NS, (d1, d2, d3, d4))) / 556.0
        intern.append(math.sqrt(i2))
        place.append(math.sqrt(max(f * f - i2, 0.0)))
    bb = int(fulls.argmin()) + 1
    curve[(s, k, init)] = (fulls.min(), fulls.mean(), np.mean(intern), np.mean(place), bb)
    print(f"{s:>3} {k:>4.1f} {init:<7} {fulls.min():6.2f} {fulls.mean():6.2f} "
          f"{np.mean(intern):7.2f} {np.mean(place):7.2f} {place[bb - 1]:13.2f}")

print("\nper-domain COM error / rotation (best block):")
for s, k, init, fn in CELLS:
    _, _, _, _, bb = curve[(s, k, init)]
    try:
        X, N = get_block(PM / fn, bb)
    except ValueError:
        print(f"  s={s} k={k} {init}: no dump")
        continue
    Rg, cg, ng = kabsch(X, N)
    parts = []
    for lo, hi in DOMS:
        Rd, cd, nd = kabsch(X[lo - 1:hi], N[lo - 1:hi])
        com_f = X[lo - 1:hi].mean(0)
        g_com = (com_f - cg) @ Rg + ng
        err = np.linalg.norm(g_com - N[lo - 1:hi].mean(0))
        ang = rot_angle(Rd @ Rg.T)
        parts.append(f"{err:.1f}/{ang:.0f}deg")
    print(f"  s={s:>2} k={k} {init:<7} blk{bb}: " + "  ".join(parts))
