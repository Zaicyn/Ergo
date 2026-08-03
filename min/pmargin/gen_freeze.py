#!/usr/bin/env python3
"""gen_freeze.py — freeze-then-dock: post-fold rigidification.

Base: dock_sim.ergo (deployable fold-then-dock variant, sim folds).
Hypothesis (orient_check.md mechanism): the field satisfies interface
restraints by BENDING the compliant domains (cheap) instead of ROTATING
them (expensive, rigid-body). Fix candidate: ramp each domain's INTERNAL
terms during the docking phase — RES_ANGK, RES_TORSK, BACKBONE_D × M —
removing the ability to soak restraint energy into local bending, so
interface forces express as net translation/rotation.

Design (documented):
- Multiplier M ∈ {3, 5, 10} (×1 gate = dock_sim.out, must reproduce).
- Applied at program start = docking-phase start (the run IS the docking
  phase; domains start pre-folded — simple trigger, documented; no
  per-domain-RMSD stabilization trigger needed).
- RES_ANGK/RES_TORSK multiplied for all residues EXCEPT the interface
  windows ±3 around each boundary (150-156, 318-324, 438-444) — the
  linkers stay live (their 0.9 damping already marks them).
- BACKBONE_D multiplied globally (PARAMETER value change per variant).
- Interface/cross-domain terms (contacts, tether, interface register
  torsions) unchanged. Per-cell FINAL_STRUCTURE_B dump included.
- Known confound (documented): freezing locks the current fold — bounded
  by its RMSD (0.91-3.38); if the field-vs-crystal mismatch is frozen
  in, placement may stay wrong even with rigid domains (that outcome
  maps to field rebalancing, not rigid-frame projection).

Emits: freeze_sim_x{3,5,10}.ergo
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"

BASE = (PM / "dock_sim.ergo").read_text()

INIT_ANCHOR = """CALL INIT_TABLES()
CALL INIT_VD()"""
RIGID = """! freeze-then-dock rigidification (gen_freeze.py): internal terms x__M__
! from docking-phase start, interface windows excluded (linkers live)
DO I = 1, NRES
  K2 := 1
  IF I >= 150 .AND. I <= 156 THEN
    K2 := 0
  ENDIF
  IF I >= 318 .AND. I <= 324 THEN
    K2 := 0
  ENDIF
  IF I >= 438 .AND. I <= 444 THEN
    K2 := 0
  ENDIF
  IF K2 = 1 THEN
    RES_ANGK(I) := RES_ANGK(I) * __M__
    RES_TORSK(I) := RES_TORSK(I) * __M__
  ENDIF
ENDDO
CALL INIT_TABLES()
CALL INIT_VD()"""

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

DECL_ANCHOR = "STATIC INTEGER :: NCX, NSAT"
assert DECL_ANCHOR in BASE and INIT_ANCHOR in BASE and DUMP_ANCHOR in BASE

for m, mtag in ((3, "3"), (5, "5"), (10, "10")):
    t = BASE
    t = t.replace(DECL_ANCHOR, DECL_ANCHOR + "\nSTATIC INTEGER :: K2", 1)
    t = t.replace(INIT_ANCHOR, RIGID.replace("__M__", f"{float(m):.1f}"), 1)
    t = t.replace("PARAMETER REAL :: BACKBONE_D = 1.4",
                  f"PARAMETER REAL :: BACKBONE_D = {1.4 * m:.4f}  ! gen_freeze x{m} rigidified", 1)
    t = t.replace(DUMP_ANCHOR, DUMP_ADD, 1)
    t = t.replace("! PACKED_SDRD_FULL_WHITE_DOCK",
                  f"! PACKED_SDRD_FULL_WHITE_DOCK_FREEZE x{m} (gen_freeze.py)", 1)
    out = PM / f"freeze_sim_x{mtag}.ergo"
    out.write_text(t)
    print(f"wrote {out}")
