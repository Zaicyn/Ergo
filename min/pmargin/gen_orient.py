#!/usr/bin/env python3
"""gen_orient.py — interface orientation terms for fold-then-dock.

THE TERM: cross-domain dihedral restraints (register-torsion analog for
interfaces — the β-sheet chirality lesson: distance-only contacts can't
pick a face; signed dihedrals can). Reuses the sim's own register
machinery verbatim (2k(1-cos(phi-p0)), frame gate EXTRA_TORSIONS_FROM=1200).

Quartet selection (documented): for each domain boundary bnd in
{152, 320, 440}, for each native cross-domain contact pair (i,j) with
i<=bnd<j (the 32 IFACE pairs of dock_check.md), emit TWO quartets:
  (i-1, i, j, j+1)  and  (i, i+1, j-1, j)
requiring i-1>=1, i+1<=bnd, j-1>bnd, j+1<=556 (extras stay in the
contacting domains). Each quartet ties the local backbone direction of
one domain at the contact to the other's — signed orientation
constraints. p0 = the crystal dihedral (force convention, atan2 form of
dihedral_1sno.py), k = bracket strength.

MATRIX: {baseline, +orientation} x {hot (existing dock schedule), cold
(quench-only: THERMAL_CURRENT = HEAT_START floor always, 0 after 38400)}.
Hot baselines already exist (dock_oracle.out / dock_sim.out — the gate).
Emits: orient_hot_{oracle,sim}_k05, orient_hot_sim_k10 (bracket),
orient_cold_{oracle,sim}_base, orient_cold_{oracle,sim}_k05.
"""

import math
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"
NRES = 556
BNDS = (152, 320, 440)

# ── native coordinates (per-domain struct outs; slices == full native) ──
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
assert NAT.shape == (NRES, 3)

src = (PM / "sdrd_white_full.ergo").read_text()
NCON = {}
for i, j, v in re.findall(r"NATIVE_R0\((\d+), (\d+)\) := ([0-9.]+)", src):
    NCON[(int(i), int(j))] = float(v)
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

# ── quartet selection ────────────────────────────────────────────────
quads = []
for i, j in NATIVE_CONTACT:
    bnd = None
    for b in BNDS:
        if i <= b < j:
            bnd = b
    if bnd is None:
        continue
    if i - 1 >= 1 and j + 1 <= NRES:
        quads.append((i - 1, i, j, j + 1))
    if i + 1 <= bnd and j - 1 > bnd:
        quads.append((i, i + 1, j - 1, j))
quads = sorted(set(quads))
print(f"{len(quads)} interface quartets from {sum(1 for i, j in NATIVE_CONTACT if any(i <= b < j for b in BNDS))} cross-domain contacts")
for q in quads[:6]:
    print("  e.g.", q, "p0 = %.4f" % dihedral(*(NAT[t - 1] for t in q)))

OLD_MAXREG = 1748
NEW_NREG = OLD_MAXREG + len(quads)

REG_ADD = []
for n, q in enumerate(quads, start=OLD_MAXREG + 1):
    p0 = dihedral(*(NAT[t - 1] for t in q))
    REG_ADD.append((n, q, p0))

def reg_lines(k_strength):
    out = []
    for n, q, p0 in REG_ADD:
        out.append(f"  REG_A({n}) := {q[0]}")
        out.append(f"  REG_B({n}) := {q[1]}")
        out.append(f"  REG_C({n}) := {q[2]}")
        out.append(f"  REG_D({n}) := {q[3]}")
        out.append(f"  REG_K({n}) := {k_strength:.4f}")
        out.append(f"  REG_P0({n}) := {p0:.6f}")
    return "\n".join(out)

# ── surgery on the dock variants ─────────────────────────────────────
REG_ANCHOR = "  REG_P0(1748) := 0.652862\n\n  RETURN"
COLD_OLD = """  IF FRAME < 300 THEN
    FRAC := REAL(FRAME) / 300.0
    THERMAL_CURRENT := HEAT_START + (HEAT_PEAK - HEAT_START) * FRAC
  ELSEIF FRAME < 600 THEN
    FRAC := REAL(FRAME - 300) / 300.0
    THERMAL_CURRENT := HEAT_PEAK - (HEAT_PEAK - HEAT_START) * FRAC
  ELSEIF FRAME < 900 THEN
    FRAC := REAL(FRAME - 600) / 300.0
    THERMAL_CURRENT := HEAT_START + (HEAT_PEAK - HEAT_START) * FRAC
  ELSEIF FRAME < 1200 THEN
    FRAC := REAL(FRAME - 900) / 300.0
    THERMAL_CURRENT := HEAT_PEAK - (HEAT_PEAK - HEAT_START) * FRAC
  ELSE
    THERMAL_CURRENT := HEAT_START
  ENDIF"""
COLD_NEW = """  ! COLD docking (gen_orient.py): no heat ramp — floor noise only;
  ! quench tail (FRAME > 38400 -> 0.0) untouched below.
  THERMAL_CURRENT := HEAT_START"""

def emit(base_file, out_name, k_strength, cold, note):
    t = (PM / base_file).read_text()
    assert REG_ANCHOR in t
    assert "PARAMETER INTEGER :: MAXREG = 1748" in t
    assert "PARAMETER INTEGER :: NREG = 1748" in t
    x = t.replace("PARAMETER INTEGER :: MAXREG = 1748",
                  f"PARAMETER INTEGER :: MAXREG = {NEW_NREG}", 1)
    x = x.replace("PARAMETER INTEGER :: NREG = 1748",
                  f"PARAMETER INTEGER :: NREG = {NEW_NREG}", 1)
    if k_strength is not None:
        x = x.replace(REG_ANCHOR,
                      "  REG_P0(1748) := 0.652862\n\n"
                      "  ! interface orientation torsions (gen_orient.py): cross-domain\n"
                      "  ! quartets (i-1,i,j,j+1) and (i,i+1,j-1,j) at each cross-domain\n"
                      "  ! native contact, crystal dihedral targets\n"
                      + reg_lines(k_strength) + "\n\n  RETURN", 1)
    if cold:
        assert COLD_OLD in x
        x = x.replace(COLD_OLD, COLD_NEW, 1)
    x = x.replace("! PACKED_SDRD_FULL_WHITE_DOCK", f"! PACKED_SDRD_FULL_WHITE_DOCK_ORIENT — {note}", 1)
    out = PM / f"{out_name}.ergo"
    out.write_text(x)
    print(f"wrote {out}")

# hot + orientation (oracle k0.5; sim k0.5 + k1.0 bracket)
emit("dock_oracle.ergo", "orient_hot_oracle_k05", 0.5, False,
     "hot schedule + interface orientation torsions k=0.5 (oracle init)")
emit("dock_sim.ergo", "orient_hot_sim_k05", 0.5, False,
     "hot schedule + interface orientation torsions k=0.5 (sim init)")
emit("dock_sim.ergo", "orient_hot_sim_k10", 1.0, False,
     "hot schedule + interface orientation torsions k=1.0 (sim init, bracket)")
# cold baselines (no orientation term)
emit("dock_oracle.ergo", "orient_cold_oracle_base", None, True,
     "COLD quench-only schedule, baseline field (oracle init)")
emit("dock_sim.ergo", "orient_cold_sim_base", None, True,
     "COLD quench-only schedule, baseline field (sim init)")
# cold + orientation
emit("dock_oracle.ergo", "orient_cold_oracle_k05", 0.5, True,
     "COLD quench-only + interface orientation torsions k=0.5 (oracle init)")
emit("dock_sim.ergo", "orient_cold_sim_k05", 0.5, True,
     "COLD quench-only + interface orientation torsions k=0.5 (sim init)")
