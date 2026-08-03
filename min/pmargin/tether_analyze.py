#!/usr/bin/env python3
"""tether_analyze.py — gate tables + fragmentation/termini anatomy for the
tether-repair variants. Reads min/pmargin/tether_{a_k005,a_k02,a_k05,a_k10,
b_k05,b_k10}.out and packed_1sno_struct.out (baseline).
Per variant: DOM rows (full/D1/D2 per block), broken-bond census per block
(D>3 and D>8), and the bond-1 (N-terminus) length in blocks 1 and 4 —
the termini-floppiness check. Rescue bar: trap block 4 D1 < 3.0.
Gate: good blocks 1/3/8 within +0.5 of baseline full RMSD.
"""
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NRES = 136
VARIANTS = ("a_k005", "a_k02", "a_k05", "a_k10", "b_k05", "b_k10")

def get_block(lines, block):
    i = lines.index(f"FINAL_STRUCTURE_B {block}")
    pts = []
    for line in lines[i + 1:i + 1 + NRES]:
        p = line.split(",")
        pts.append([float(p[1]), float(p[2]), float(p[3])])
    return np.array(pts)

def dom_rows(lines):
    rows = {}
    for ln in lines:
        if ln.startswith("DOM "):
            p = ln.split()
            rows[int(p[1])] = (float(p[3]), float(p[4]), float(p[5]))
    return rows

def census(X):
    bl = np.linalg.norm(X[1:] - X[:-1], axis=1)
    return bl, (bl > 3.0).sum(), (bl > 8.0).sum()

base_lines = (ROOT / "min" / "pmargin" / "packed_1sno_struct.out").read_text().splitlines()
base = dom_rows(base_lines)
print("baseline DOM:", {b: tuple(round(x, 2) for x in v) for b, v in sorted(base.items())})
print()
hdr = f"{'variant':<10} {'trap full/D1/D2':<22} {'rescue?':<8} {'gate 1/3/8 (+0.5)':<22} {'trap bonds>3/>8':<16} {'bond1 blk1/blk4':<16}"
print(hdr)
for v in VARIANTS:
    lines = (ROOT / "min" / "pmargin" / f"tether_{v}.out").read_text().splitlines()
    rows = dom_rows(lines)
    t = rows[4]
    rescue = "YES" if t[1] < 3.0 else "no"
    gate = []
    for b in (1, 3, 8):
        ok = rows[b][0] <= base[b][0] + 0.5
        gate.append(f"{b}:{rows[b][0]:.2f}{'ok' if ok else 'BAD'}")
    X4 = get_block(lines, 4)
    bl4, n3, n8 = census(X4)
    X1 = get_block(lines, 1)
    bl1, _, _ = census(X1)
    print(f"{v:<10} {t[0]:6.2f}/{t[1]:5.2f}/{t[2]:5.2f}     {rescue:<8} {' '.join(gate):<22} "
          f"{n3:>5}/{n8:<5}       {bl1[0]:6.2f}/{bl4[0]:6.2f}")

print("\nper-block full RMSD, all variants (baseline first):")
allv = ("baseline",) + VARIANTS
tab = {v: dom_rows((ROOT / "min" / "pmargin" / ("packed_1sno_struct.out" if v == "baseline" else f"tether_{v}.out")).read_text().splitlines()) for v in allv}
print(f"{'variant':<10}" + "".join(f"  blk{b}" for b in range(1, 9)))
for v in allv:
    print(f"{v:<10}" + "".join(f"  {tab[v][b][0]:4.2f}" for b in range(1, 9)))

print("\nbroken-bond lists (D>3) for the trap block 4, per variant:")
for v in ("baseline",) + VARIANTS:
    lines = (ROOT / "min" / "pmargin" / ("packed_1sno_struct.out" if v == "baseline" else f"tether_{v}.out")).read_text().splitlines()
    X4 = get_block(lines, 4)
    bl = np.linalg.norm(X4[1:] - X4[:-1], axis=1)
    br = [(int(i + 1), round(float(bl[i]), 1)) for i in range(135) if bl[i] > 3.0]
    print(f"  {v:<10} {br}")
