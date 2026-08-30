#!/usr/bin/env python3
"""mk_rail_variants.py — generate the rail-telemetry variants of
ul18_stag5.ergo (instrumented staged arm + no-gate arm).

Physics is byte-identical to the certified staged program; the variant
adds read-only telemetry:
  - RAILGATES,<n> at init
  - RC,frame,I,J,D per gated contact per dump inside gate windows
    (T_k ± 4000 frames)
  - RB,frame,I,x,y,z per bead per dump inside gate windows
  - FIRSTFORM table at end (first frame each gated contact crosses
    below NATIVE_CUTOFF)
The no-gate arm additionally zeroes the 91 staged CONTACT_INTER frames
(make-live-from-frame-0) before the slot-table bake.

Run: python3 min/ribosome/mk_rail_variants.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ul18_stag5.ergo")

DECL_ANCHOR = "STATIC REAL :: P_G, P2_G, C_G, S_G, FRM"
DECL_ADD = """
! ── RAIL telemetry (read-only; no physics change) ──
STATIC INTEGER :: GATED_I(128), GATED_J(128), GATED_T(128), FIRSTFORM(128)
STATIC INTEGER :: NGATES, GK, GI, GJ"""

# gate-list scan goes immediately after the last staged assignment,
# just before the "! Go-like contacts" data comment
SCAN_ADD = """  ! RAIL: pack the staged contact list (CONTACT_INTER > 1 = gate frame)
  NGATES := 0
  DO I = 1, NRES
    DO J = I + 1, NRES
      IF CONTACT_INTER(I, J) > 1 THEN
        NGATES := NGATES + 1
        GATED_I(NGATES) := I
        GATED_J(NGATES) := J
        GATED_T(NGATES) := CONTACT_INTER(I, J)
        FIRSTFORM(NGATES) := -1
      ENDIF
    ENDDO
  ENDDO
  WRITE(*, "RAILGATES,%d") NGATES
"""
NOGATE_ADD = """  ! NOGATE arm: all staged contacts live from frame 0
  DO GK = 1, NGATES
    CONTACT_INTER(GATED_I(GK), GATED_J(GK)) := 0
    CONTACT_INTER(GATED_J(GK), GATED_I(GK)) := 0
  ENDDO
"""

# telemetry inside the every-10-frames diagnostics block, right after
# the CSV write continuation (anchor: the RMSD_CHAIN write line)
CAD_ANCHOR = "      RMSD_CHAIN(1), RMSD_CHAIN(2), RMSD_CHAIN(3), RMSD_CHAIN(4)"
CAD_ADD = """
  ! RAIL telemetry (read-only)
  DO GK = 1, NGATES
    GI := GATED_I(GK)
    GJ := GATED_J(GK)
    DX := RES_X(GI) - RES_X(GJ)
    DY := RES_Y(GI) - RES_Y(GJ)
    DZ := RES_Z(GI) - RES_Z(GJ)
    D := SQRT(DX*DX + DY*DY + DZ*DZ)
    IF FIRSTFORM(GK) < 0 THEN
      IF D < NATIVE_CUTOFF THEN
        FIRSTFORM(GK) := FRAME
      ENDIF
    ENDIF
  ENDDO
  IF (FRAME >= 20000 .AND. FRAME <= 28000) .OR. (FRAME >= 44000 .AND. FRAME <= 52000) .OR. (FRAME >= 68000 .AND. FRAME <= 76000) .OR. (FRAME >= 100000 .AND. FRAME <= 108000) THEN
    DO GK = 1, NGATES
      GI := GATED_I(GK)
      GJ := GATED_J(GK)
      DX := RES_X(GI) - RES_X(GJ)
      DY := RES_Y(GI) - RES_Y(GJ)
      DZ := RES_Z(GI) - RES_Z(GJ)
      D := SQRT(DX*DX + DY*DY + DZ*DZ)
      WRITE(*, "RC,%d,%d,%d,%.4f") FRAME, GI, GJ, D
    ENDDO
    DO I = 1, NRES
      WRITE(*, "RB,%d,%d,%.6f,%.6f,%.6f") FRAME, I, RES_X(I), RES_Y(I), RES_Z(I)
    ENDDO
  ENDIF"""

END_ANCHOR = 'WRITE(*, "END_FINAL_STRUCTURE")'
END_ADD = """
WRITE(*, "FIRSTFORM_TABLE")
DO GK = 1, NGATES
  WRITE(*, "FF,%d,%d,%d,%d") GATED_I(GK), GATED_J(GK), GATED_T(GK), FIRSTFORM(GK)
ENDDO
WRITE(*, "END_FIRSTFORM")"""


def patch(text, nogate):
    assert DECL_ANCHOR in text
    text = text.replace(DECL_ANCHOR, DECL_ANCHOR + DECL_ADD, 1)
    lines = text.splitlines()
    # scan insertion: right after the last CONTACT_INTER(...) := <gate>
    # assignment (the 72000 block ends the staged map)
    last_ci = max(i for i, ln in enumerate(lines)
                  if re.match(r"\s*CONTACT_INTER\(\d+, \d+\) := \d+", ln))
    add = SCAN_ADD + (NOGATE_ADD if nogate else "")
    lines.insert(last_ci + 1, add.rstrip("\n"))
    text = "\n".join(lines) + "\n"
    assert CAD_ANCHOR in text
    text = text.replace(CAD_ANCHOR, CAD_ANCHOR + CAD_ADD, 1)
    assert END_ANCHOR in text
    text = text.replace(END_ANCHOR, END_ANCHOR + END_ADD, 1)
    return text


def main():
    src = open(SRC).read()
    out1 = patch(src, nogate=False)
    out2 = patch(src, nogate=True)
    p1 = os.path.join(HERE, "ul18_stag5_rail.ergo")
    p2 = os.path.join(HERE, "ul18_stag5_rail_nogate.ergo")
    open(p1, "w").write(out1)
    open(p2, "w").write(out2)
    print(f"wrote {p1} and {p2}")


if __name__ == "__main__":
    main()
