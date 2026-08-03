#!/usr/bin/env python3
"""gen_rebalance.py — force-field rebalancing sweep on the deployable dock.

Base: freeze_sim_x3.ergo (dock_sim + adopted ×3 rigidification per
freeze_check.md secondary result). Factorial:
  HYDRO_STRENGTH ∈ {0.0020 (gate), 0.0010, 0.0005, 0.0002}
    — weaken geometry-agnostic packing (Deepseek's direction A)
  local stiffness ∈ {×1 (gate), ×2, ×4} ON TOP of the ×3 freeze,
    applied to RES_ANGK and RES_TORSK together, same interface-window
    exclusion as the freeze (linkers live) — Deepseek's direction B
    (effective multipliers ×3, ×6, ×12 vs recipe)
  BACKBONE_D stays at ×3 everywhere (part of the adopted freeze).
  Interface/cross-domain terms unchanged.
Direction C (separate emission): NATIVE_K ×{2,4} at the factorial's
best cell.

Emits: rebalance_h{100,050,020}_k{2,4}.ergo (the 0.0020×1 gate is
freeze_sim_x3.out; cells named by hydro µ4 and extra stiffness).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"
BASE = (PM / "freeze_sim_x3.ergo").read_text()

FREEZE_LOOP_ANCHOR = """ENDDO
CALL INIT_TABLES()
CALL INIT_VD()"""
EXTRA_LOOP = """ENDDO
! rebalance extra local stiffness x__M__ (gen_rebalance.py), same window exclusion
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

HYDRO_OLD = "PARAMETER REAL :: HYDRO_STRENGTH = 0.0020"
assert HYDRO_OLD in BASE and FREEZE_LOOP_ANCHOR in BASE

def emit(hydro, htag, stiff, stag, extra=None):
    t = BASE
    t = t.replace(HYDRO_OLD,
                  f"PARAMETER REAL :: HYDRO_STRENGTH = {hydro:.4f}  ! gen_rebalance", 1)
    if stiff != 1:
        t = t.replace(FREEZE_LOOP_ANCHOR, EXTRA_LOOP.replace("__M__", f"{float(stiff):.1f}"), 1)
    if extra == "native2":
        t = t.replace("PARAMETER REAL :: NATIVE_K = 1.00",
                      "PARAMETER REAL :: NATIVE_K = 2.00  ! gen_rebalance direction C", 1)
    elif extra == "native4":
        t = t.replace("PARAMETER REAL :: NATIVE_K = 1.00",
                      "PARAMETER REAL :: NATIVE_K = 4.00  ! gen_rebalance direction C", 1)
    t = t.replace("! PACKED_SDRD_FULL_WHITE_DOCK_FREEZE x3 (gen_freeze.py)",
                  f"! PACKED_SDRD_FULL_WHITE_DOCK_REBALANCE h{htag} k{stag}{' ' + extra if extra else ''} (gen_rebalance.py)", 1)
    out = PM / f"rebalance_h{htag}_k{stag}{'_' + extra if extra else ''}.ergo"
    out.write_text(t)
    print(f"wrote {out}")

for hydro, htag in ((0.0010, "100"), (0.0005, "050"), (0.0002, "020")):
    for stiff in (1, 2, 4):
        emit(hydro, htag, stiff, str(stiff))
for stiff in (2, 4):
    emit(0.0020, "200", stiff, str(stiff))
