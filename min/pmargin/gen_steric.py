#!/usr/bin/env python3
"""gen_steric.py — steric underpacking penalty for Trp-cage WT vs W6F.

Base file: tests/waveform_trpcage_cb4.ergo (identical to the ar0.05
variant; WT folds to 0.5879). The W6F mutant is built on the SAME base
for apples-to-apples comparison (the older Protein_Margin/trpcage_w6f_cb.
ergo uses a different, fixed-distance aromatic loop; its Phe value
AROMATIC_MULT(6)=0.30 is adopted).

Term (design, documented):
- Residue volumes from Zamyatnin (1972): Trp 227.8, Phe 189.9,
  Tyr 193.6 A^3. STERIC_DV(i) = max(0, V_native(i) - V_placed(i));
  WT: all zero (term identically off -> WT gate is bitwise by
  construction). W6F: STERIC_DV(6) = 227.8 - 189.9 = 37.9 A^3.
- Force: for each Cbeta-Cbeta packing partner pair (D < 8.0) that has
  over-collapsed (D < D0 = native CB-CB distance), a repulsive force
    FS = STERIC_K * (DV_i + DV_j) * (D0 - D) / D0
  i.e. an underpacked residue cannot hold its native packing partners
  as tightly; the pocket loosens. Pocket tightness enters through the
  number of formed partners (each carries the repulsion) — no separate
  tightness table.
- Diagnostic energy E_STERIC = K*(DV_i+DV_j)*(D0-D)^2/(2*D0) accumulated
  per frame (accounting only, no feedback into forces).

Variants: steric_wt (K=0.001, gate), steric_w6f_k{3e4,1e3,5e3},
pulse_steric_{wt,w6f} (validated 1SNO pulse omega=0.002, A=0.05,
mode-1 backbone standing wave, on the K chosen after the sweep).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"
BASE = (ROOT / "tests" / "waveform_trpcage_cb4.ergo").read_text()

DECL_ANCHOR = "STATIC REAL :: AROMATIC_MULT(36)\n"
assert DECL_ANCHOR in BASE

STERIC_DECLS = """STATIC REAL :: STERIC_DV(36)
PARAMETER REAL :: STERIC_K = __K__
STATIC REAL :: FS, E_STERIC
"""

FORCE_ANCHOR = "        IF D > 0.0 .AND. D0 > 0.0 .AND. D < 8.0 THEN"
assert FORCE_ANCHOR in BASE

STERIC_FORCE = FORCE_ANCHOR + """
          ! Steric underpacking penalty: void in a native pocket —
          ! an underpacked residue cannot hold native packing partners
          IF D < D0 THEN
            FS := STERIC_K * (STERIC_DV(I) + STERIC_DV(J)) * (D0 - D) / D0
            E_STERIC := E_STERIC + STERIC_K * (STERIC_DV(I) + STERIC_DV(J)) * &
              (D0 - D) ** 2 / (2.0 * D0)
            RES_VX(I) := RES_VX(I) + FS * DX / D * DT * FORCE_SCALE
            RES_VY(I) := RES_VY(I) + FS * DY / D * DT * FORCE_SCALE
            RES_VZ(I) := RES_VZ(I) + FS * DZ / D * DT * FORCE_SCALE
            RES_VX(J) := RES_VX(J) - FS * DX / D * DT * FORCE_SCALE
            RES_VY(J) := RES_VY(J) - FS * DY / D * DT * FORCE_SCALE
            RES_VZ(J) := RES_VZ(J) - FS * DZ / D * DT * FORCE_SCALE
          ENDIF"""

# reset the diagnostic accumulator each frame, before the aromatic loop
AROM_LOOP_ANCHOR = "  ! Aromatic packing (Cβ-derived side-chain centers)"
assert AROM_LOOP_ANCHOR in BASE

E_PRINT_ANCHOR = '! Final structure dump for gap analysis'
assert E_PRINT_ANCHOR in BASE


def build(k, w6f, pulse, out_name):
    s = BASE
    s = s.replace(DECL_ANCHOR, DECL_ANCHOR + STERIC_DECLS.replace("__K__", k), 1)
    s = s.replace(FORCE_ANCHOR, STERIC_FORCE, 1)
    s = s.replace(AROM_LOOP_ANCHOR, "  E_STERIC := 0.0\n\n" + AROM_LOOP_ANCHOR, 1)
    s = s.replace(E_PRINT_ANCHOR,
                  'WRITE(*, "STERIC_E %.6f") E_STERIC\n\n' + E_PRINT_ANCHOR, 1)
    if w6f:
        s = s.replace("  AROMATIC_MULT(6) := 2.00",
                      "  AROMATIC_MULT(6) := 0.30   ! Phe (adopted from trpcage_w6f_cb.ergo)\n"
                      "  STERIC_DV(6) := 37.9   ! Trp 227.8 - Phe 189.9 A^3 (Zamyatnin 1972)", 1)
        s = s.replace("! WAVEFORM_TRPCAGE - trpcage protein variant with native RMSD",
                      f"! STERIC_W6F — trpcage W6F + underpacking penalty K={k}")
    else:
        s = s.replace("! WAVEFORM_TRPCAGE - trpcage protein variant with native RMSD",
                      f"! STERIC_WT — trpcage WT + underpacking penalty K={k} (DV=0, gate)")
    if pulse:
        kick = """  ! Ultrasonic pulse (validated 1SNO params): mode-1 backbone
  ! standing wave, omega=0.002, A=0.05, axes phase-shifted 2pi/3
  DO I = 1, NRES
    RES_VX(I) := RES_VX(I) + 0.05 * SIN(0.002 * REAL(FRAME)) * SIN(3.14159265 * REAL(I) / REAL(NRES + 1))
    RES_VY(I) := RES_VY(I) + 0.05 * SIN(0.002 * REAL(FRAME) + 2.0943951) * SIN(3.14159265 * REAL(I) / REAL(NRES + 1))
    RES_VZ(I) := RES_VZ(I) + 0.05 * SIN(0.002 * REAL(FRAME) + 4.1887902) * SIN(3.14159265 * REAL(I) / REAL(NRES + 1))
  ENDDO

  ! Steric repulsion (|i-j| >= 4, not H-bonded)"""
        s = s.replace("  ! Steric repulsion (|i-j| >= 4, not H-bonded)", kick, 1)
    (PM / out_name).write_text(s)
    print(f"wrote {out_name}")


build("0.001", False, False, "steric_wt.ergo")
build("0.0003", True, False, "steric_w6f_k3e4.ergo")
build("0.001", True, False, "steric_w6f_k1e3.ergo")
build("0.005", True, False, "steric_w6f_k5e3.ergo")

k_sel = sys.argv[1] if len(sys.argv) > 1 else "0.001"
build(k_sel, False, True, "pulse_steric_wt.ergo")
build(k_sel, True, True, "pulse_steric_w6f.ergo")
print(f"pulse variants at K={k_sel}")
