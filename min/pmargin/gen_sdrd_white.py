#!/usr/bin/env python3
"""gen_sdrd_white.py — SdrD retest with the white-noise bath.

Minimal controlled swap: ONLY the velocity kicks change (validated
splitmix-style integer hash, amplitude variance-matched x2.449 per
white_check.md). Phase noise left as the old sinusoid (documented:
phases are inert at HB_CAP=0 — they gate only H-bonds, which are
disabled in this recipe; the A/B is exactly the velocity-bath model).
Everything else identical: same packed v2 programs, same schedule
(heat cycles to 1200, floor, quench 38400), same seeds.

Note on the quench floor (honest): THERMAL_CURRENT scales both drive
types multiplicatively, so variance matching holds at every schedule
point — what changes is the temporal correlation of the noise, never
its amplitude.

Outputs: sdrd_white_{A2,A3,B1,B2,full}.ergo
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"

OLD_KICKS = """    ! Thermal impulses (velocity kicks, LOCAL index)
    DO I = 1, NRES
      RES_VX(OFF + I) := RES_VX(OFF + I) + THERMAL_CURRENT * SIN((I+1)*7.3 + REAL(FRAME)*0.17)
      RES_VY(OFF + I) := RES_VY(OFF + I) + THERMAL_CURRENT * COS((I+1)*5.7 + REAL(FRAME)*0.31)
      RES_VZ(OFF + I) := RES_VZ(OFF + I) + THERMAL_CURRENT * SIN((I+1)*3.1 + REAL(FRAME)*0.09)
    ENDDO"""

NEW_KICKS = """    ! Thermal impulses (velocity kicks, LOCAL index) — WHITE hash bath
    DO I = 1, NRES
      H := IEOR((OFF + I) * 2654435761, FRAME * 40503)
      H := IEOR(H, ISHFT(H, -30))
      H := H * 6364136223846793005
      H := IEOR(H, ISHFT(H, -27))
      H := H * 6364136223846793005
      H := IEOR(H, ISHFT(H, -31))
      RES_VX(OFF + I) := RES_VX(OFF + I) + THERMAL_CURRENT * 2.449 * (REAL(IAND(H, 65535)) / 65535.0 - 0.5)
      H := IEOR(H, ISHFT(H, -17))
      RES_VY(OFF + I) := RES_VY(OFF + I) + THERMAL_CURRENT * 2.449 * (REAL(IAND(H, 65535)) / 65535.0 - 0.5)
      H := IEOR(H, ISHFT(H, -7))
      RES_VZ(OFF + I) := RES_VZ(OFF + I) + THERMAL_CURRENT * 2.449 * (REAL(IAND(H, 65535)) / 65535.0 - 0.5)
    ENDDO"""

DECL_ANCHOR = "STATIC REAL :: RMSD_B(8)"

for dom in ("A2", "A3", "B1", "B2", "full"):
    src = PM / f"sdrd_{dom}.ergo"
    s = src.read_text()
    assert OLD_KICKS in s, dom
    s = s.replace(OLD_KICKS, NEW_KICKS, 1)
    assert DECL_ANCHOR in s
    s = s.replace(DECL_ANCHOR, DECL_ANCHOR + "\nSTATIC INTEGER :: H", 1)
    s = s.replace(f"! PACKED_SDRD_{dom.upper()}", f"! PACKED_SDRD_{dom.upper()}_WHITE")
    out = PM / f"sdrd_white_{dom}.ergo"
    out.write_text(s)
    print(f"wrote {out}")
