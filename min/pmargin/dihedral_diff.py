#!/usr/bin/env python3
"""dihedral_diff.py — per-residue backbone dihedral comparison:
seed-4.0 near-native fold vs seed-0.0 trap vs PDB native reference.

Structures from tests/waveform_bba5_seed_{4.0,0.0}.out FINAL_STRUCTURE
rows (cols: idx, cur x/y/z, native x/y/z). Dihedral convention: the
sim's force convention, atan2(B2mag*(B1.N2), N1.N2) over Cα i-1,i,i+1,i+2
for i = 2..NRES-2 (21 dihedrals, residue index = middle pair start).
Also checks overlap with the sim's register-torsion pairs (REG tables).
"""

import math
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NRES = 23

def get_structure(out_file, native=False):
    lines = open(out_file).read().splitlines()
    i = lines.index("FINAL_STRUCTURE")
    end = lines.index("END_FINAL_STRUCTURE")
    pts = []
    for line in lines[i + 1:end]:
        p = line.split(",")
        pts.append([float(p[4 if native else 1]), float(p[5 if native else 2]), float(p[6 if native else 3])])
    assert len(pts) == NRES
    return np.array(pts)

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

def vsub(a, b): return a - b

def profile(X):
    return [math.degrees(dihedral(X[i - 1], X[i], X[i + 1], X[i + 2]))
            for i in range(1, NRES - 2)]

def wrap(d):
    while d > 180.0: d -= 360.0
    while d <= -180.0: d += 360.0
    return d

X_FOLD = get_structure(ROOT / "tests" / "waveform_bba5_seed_4.0.out")
X_TRAP = get_structure(ROOT / "tests" / "waveform_bba5_seed_0.0.out")
X_NAT = get_structure(ROOT / "tests" / "waveform_bba5_seed_4.0.out", native=True)

pf, pt, pn = profile(X_FOLD), profile(X_TRAP), profile(X_NAT)

src = (ROOT / "tests" / "waveform_bba5_seed_0.0.ergo").read_text()
RA = {int(k): int(v) for k, v in re.findall(r"REG_A\((\d+)\) := (\d+)", src)}
RB = {int(k): int(v) for k, v in re.findall(r"REG_B\((\d+)\) := (\d+)", src)}
RC = {int(k): int(v) for k, v in re.findall(r"REG_C\((\d+)\) := (\d+)", src)}
RD = {int(k): int(v) for k, v in re.findall(r"REG_D\((\d+)\) := (\d+)", src)}
REG = [(RA[k], RB[k], RC[k], RD[k]) for k in sorted(RA)]
reg_residues = sorted(set(x for quad in REG for x in quad[1:3]))

print(f"register torsion quadruplets: {REG}")
print(f"register middle residues: {reg_residues}\n")
print(f"{'res':>3} {'native':>8} {'fold4.0':>8} {'trap0.0':>8} {'Δtrap-nat':>10} {'Δfold-nat':>10} {'Δtrap-fold':>11} {'reg?':>4}")
rows = []
for i in range(NRES - 2):
    r = i + 2  # dihedral at residues (i+1..i+4), label by i+2 (1-based middle)
    dn, df, dt = pn[i], pf[i], pt[i]
    dtn, dfn, dtf = wrap(dt - dn), wrap(df - dn), wrap(dt - df)
    mark = "REG" if (r in reg_residues) else ""
    rows.append((r, dn, df, dt, dtn, dfn, dtf, mark))
    print(f"{r:>3} {dn:8.1f} {df:8.1f} {dt:8.1f} {dtn:10.1f} {dfn:10.1f} {dtf:11.1f} {mark:>4}")

rows.sort(key=lambda x: -abs(x[4]))
print("\nranked |Δtrap−native|:")
for r, dn, df, dt, dtn, dfn, dtf, mark in rows[:8]:
    print(f"  res {r}: {dtn:+.1f} deg (native {dn:.1f} -> trap {dt:.1f}; fold is {dfn:+.1f} off native) {mark}")
