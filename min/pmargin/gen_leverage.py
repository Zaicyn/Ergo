#!/usr/bin/env python3
"""gen_leverage.py — long-leverage interface orientation restraints.

Extends gen_orient.py's short-leverage quartets (s=0, the null baseline of
orient_check.md) to long leverage: for each cross-domain contact (i,j)
spanning boundary bnd, TWO quartets per leverage s:
  (i-s, i, j, j+s)  and  (i, i+s, j-s, j)
with i-s>=1, i+s<=bnd, j-s>bnd, j+s<=556 (documented: same contacts,
same count, same machinery, same p0-from-crystal convention — ONLY the
leverage changes). Leverage s spans ~10-60 residues into each domain, so
satisfying the restraint locally constrains a larger rigid structure —
the named lever against domain compliance absorbing the misplacement.

Protocol: identical to the orientation-term experiment with EARLY
activation (EXTRA_TORSIONS_FROM=0 — the term must guide during docking;
the s=0 early cells orient_early_{oracle,sim}_k05 are the null baseline
and must reproduce). Per-cell FINAL_STRUCTURE_B dump included for the
error-mode decomposition.

Emits: leverage_{oracle,sim}_s{8,16,30}_k{05,10}.ergo (12 files).
"""

import math
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"
NRES = 556
BNDS = (152, 320, 440)
OLD_MAXREG = 1748

def get_native(out_file, block, nres):
    lines = open(out_file).read().splitlines()
    i = lines.index(f"FINAL_STRUCTURE_B {block}")
    return np.array([[float(v) for v in line.split(",")[4:7]]
                     for line in lines[i + 1:i + 1 + nres]])

NAT = np.vstack([
    get_native(PM / "sdrd_white_A2_struct.out", 1, 152),
    get_native(PM / "sdrd_white_A3_struct.out", 1, 168),
    get_native(PM / "sdrd_white_B1_struct.out", 1, 120),
    get_native(PM / "sdrd_white_B2_struct.out", 1, 116),
])

src = (PM / "sdrd_white_full.ergo").read_text()
NATIVE_CONTACT = [(int(i), int(j)) for i, j in
                  re.findall(r"NATIVE_CONTACT\((\d+), (\d+)\) := 1", src) if int(i) < int(j)]

def dihedral(r1, r2, r3, r4):
    b1, b2, b3 = r2 - r1, r3 - r2, r4 - r3
    n1 = np.cross(b1, b2)
    n2 = np.cross(b2, b3)
    b2len = float(np.linalg.norm(b2))
    if b2len == 0.0:
        return 0.0
    return math.atan2(b2len * float(b1 @ n2), float(n1 @ n2))

def quads_for(s):
    qs = []
    for i, j in NATIVE_CONTACT:
        bnd = None
        for b in BNDS:
            if i <= b < j:
                bnd = b
        if bnd is None:
            continue
        if i - s >= 1 and j + s <= NRES:
            qs.append((i - s, i, j, j + s))
        if i + s <= bnd and j - s > bnd:
            qs.append((i, i + s, j - s, j))
    return sorted(set(qs))

REG_ANCHOR = "  REG_P0(1748) := 0.652862\n\n  RETURN"
EARLY_OLD = "PARAMETER INTEGER :: EXTRA_TORSIONS_FROM = 1200"
EARLY_NEW = ("PARAMETER INTEGER :: EXTRA_TORSIONS_FROM = 0  ! gen_leverage: "
             "orientation terms active during assembly docking")

DUMP_ANCHOR = """DO B = 1, NBLK
  WRITE(*, "DOM %d %.1f %.4f %.4f %.4f %.4f %.4f") &
    B, SEED_TAB(B), RMSD_B(B), RMSD_D1(B), RMSD_D2(B), RMSD_D3(B), RMSD_D4(B)
ENDDO"""
DUMP_ADD = DUMP_ANCHOR + """
DO B = 1, NBLK
  OFF := (B - 1) * NRES
  WRITE(*, "FINAL_STRUCTURE_B %d") B
  DO I = 1, NRES
    WRITE(*, "%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f") &
      I, RES_X(OFF + I), RES_Y(OFF + I), RES_Z(OFF + I), NATIVE_X(I), NATIVE_Y(I), NATIVE_Z(I)
  ENDDO
  WRITE(*, "END_FINAL_STRUCTURE_B")
ENDDO"""

def emit(base_file, out_name, s, k_strength):
    qs = quads_for(s)
    nreg = OLD_MAXREG + len(qs)
    t = (PM / base_file).read_text()
    assert REG_ANCHOR in t and DUMP_ANCHOR in t
    x = t.replace("PARAMETER INTEGER :: MAXREG = 1748",
                  f"PARAMETER INTEGER :: MAXREG = {nreg}", 1)
    x = x.replace("PARAMETER INTEGER :: NREG = 1748",
                  f"PARAMETER INTEGER :: NREG = {nreg}", 1)
    lines = []
    for n, q in enumerate(qs, start=OLD_MAXREG + 1):
        p0 = dihedral(*(NAT[t2 - 1] for t2 in q))
        lines.append(f"  REG_A({n}) := {q[0]}\n  REG_B({n}) := {q[1]}\n"
                     f"  REG_C({n}) := {q[2]}\n  REG_D({n}) := {q[3]}\n"
                     f"  REG_K({n}) := {k_strength:.4f}\n  REG_P0({n}) := {p0:.6f}")
    x = x.replace(REG_ANCHOR,
                  "  REG_P0(1748) := 0.652862\n\n"
                  f"  ! long-leverage interface orientation torsions (gen_leverage.py):\n"
                  f"  ! s={s}, k={k_strength}, quartets (i-s,i,j,j+s) and (i,i+s,j-s,j)\n"
                  + "\n".join(lines) + "\n\n  RETURN", 1)
    assert EARLY_OLD in x
    x = x.replace(EARLY_OLD, EARLY_NEW, 1)
    x = x.replace(DUMP_ANCHOR, DUMP_ADD, 1)
    x = x.replace("! PACKED_SDRD_FULL_WHITE_DOCK",
                  f"! PACKED_SDRD_FULL_WHITE_DOCK_LEVERAGE s={s} k={k_strength} (gen_leverage.py)", 1)
    out = PM / f"{out_name}.ergo"
    out.write_text(x)
    return len(qs)

for s in (8, 16, 30):
    for k, ktag in ((0.5, "05"), (1.0, "10")):
        for init, base in (("oracle", "dock_oracle.ergo"), ("sim", "dock_sim.ergo")):
            n = emit(base, f"leverage_{init}_s{s}_k{ktag}", s, k)
            print(f"leverage_{init}_s{s}_k{ktag}: {n} quartets")
