#!/usr/bin/env python3
"""gen_zipper.py — two-sheet steric-zipper packing test (GNNQQNY / 1YJP).

Layout: chains 1-2 = sheet 1 (crystal A, A+b), chains 3-4 = sheet 2
(screw mate, screw+b). In-register contacts within each sheet (as the
validated tetramer). Inter-sheet ZIPPER contacts from the REAL 1YJP
screw-mate geometry (extracted from pdb/1YJP.pdb, documented here):

  facing pair (1,3) and (2,4), screw shift m=0:
    A2-S6 7.650 A = 3.0605 u,  A4-S4 6.888 A = 2.7557 u,  A6-S2 7.475 A = 2.9905 u
  facing pair (2,3), screw shift m=-1:
    A2-S6 7.475 A = 2.9905 u,  A4-S4 6.888 A = 2.7557 u,  A6-S2 7.650 A = 3.0605 u
  facing pair (1,4), m=+1: no Cα-Cα < 8 A (closest 9.737 A) -> no contacts

  The 2_1 screw flips x,z so facing chains run ANTI-parallel in
  projection: the zipper is the (2,6),(4,4),(6,2) diagonal around the
  central residue 4, closest approach A4-S4 = 6.888 A = 2.7557 units
  (the value from amyloid_check.md).

Variants:
  zipper_guided.ergo   — in-register + zipper contacts, all chains from coils
  zipper_emergent.ergo — in-register only (zipper contacts compiled out,
                         zipper measurement kept): do the sheets find the
                         face via hydrophobic attraction?

Measurements: in-register GEOM per sheet pair (C step 2), ZGEOM per
zipper contact (actual vs target), ZMIN closest inter-sheet approach,
COM per chain.
"""

from pathlib import Path

import gen_amyloid as G  # re-emits the 4 base files (deterministic); reuse

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "min" / "amyloid"

# zipper contacts: (ZA, ZB, R0 units) — 9 contacts, see header
ZIP = [
    (2, 20, 3.0605), (4, 18, 2.7557), (6, 16, 2.9905),   # pair (1,3), m=0
    (8, 27, 3.0605), (10, 25, 2.7557), (12, 23, 2.9905), # pair (2,4), m=0
    (8, 20, 2.9905), (10, 18, 2.7557), (12, 16, 3.0605), # pair (2,3), m=-1
]
NZ = len(ZIP)

ZIP_FORCE = """  ! Inter-sheet zipper contacts (real 1YJP screw-mate pairs/distances)
  DO M = 1, NZ
    IA := ZA(M)
    IB := ZB(M)
    DX := RES_X(IA) - RES_X(IB)
    DY := RES_Y(IA) - RES_Y(IB)
    DZ := RES_Z(IA) - RES_Z(IB)
    D := SQRT(DX*DX + DY*DY + DZ*DZ)
    IF D > 0.0 THEN
      FM := -2.0 * ZIP_K * (D - ZR0(M))
      RES_VX(IA) := RES_VX(IA) + FM * DX / D * DT * FORCE_SCALE
      RES_VY(IA) := RES_VY(IA) + FM * DY / D * DT * FORCE_SCALE
      RES_VZ(IA) := RES_VZ(IA) + FM * DZ / D * DT * FORCE_SCALE
      RES_VX(IB) := RES_VX(IB) - FM * DX / D * DT * FORCE_SCALE
      RES_VY(IB) := RES_VY(IB) - FM * DY / D * DT * FORCE_SCALE
      RES_VZ(IB) := RES_VZ(IB) - FM * DZ / D * DT * FORCE_SCALE
    ENDIF
  ENDDO
"""

ZIP_MEASURE = """! Zipper geometry: actual vs target per contact + closest approach
DO M = 1, NZ
  IA := ZA(M)
  IB := ZB(M)
  D := SQRT((RES_X(IA) - RES_X(IB))**2 + (RES_Y(IA) - RES_Y(IB))**2 + (RES_Z(IA) - RES_Z(IB))**2)
  WRITE(*, "ZGEOM %d %d %d %.4f %.4f") M, IA, IB, D, ZR0(M)
ENDDO
DMIN := 1.0E9
DO I = 1, 14
  DO J = 15, 28
    D := SQRT((RES_X(I) - RES_X(J))**2 + (RES_Y(I) - RES_Y(J))**2 + (RES_Z(I) - RES_Z(J))**2)
    IF D < DMIN THEN
      DMIN := D
    ENDIF
  ENDDO
ENDDO
WRITE(*, "ZMIN %.4f") DMIN
"""

ZIP_DECLS = """PARAMETER INTEGER :: NZ = 9
PARAMETER REAL :: ZIP_K = 1.00
STATIC INTEGER :: ZA(NZ), ZB(NZ)
STATIC REAL :: ZR0(NZ), DMIN
"""


def build(tag, guided, out_name):
    s = G.TEMPLATE.replace("__TAG__", tag).replace("__NC__", "4")
    s = s.replace("__NTOT__", "28").replace("__NCON__", "14")
    ic = G.ICONTACTS + "\n" + (ZIP_FORCE if guided else
        "  ! (zipper contacts compiled out — emergence variant; measurement kept)")
    s = s.replace("__ICONTACTS__", ic)
    s = s.replace("__INTRAGO__", "")
    # in-register GEOM/TRACE only within sheets (pairs 1-2 and 3-4)
    s = s.replace("DO C = 1, NC - 1\n      D := 0.0", "DO C = 1, NC - 1, 2\n      D := 0.0")
    s = s.replace("DO C = 1, NC - 1\n  DO K = 1, NRES", "DO C = 1, NC - 1, 2\n  DO K = 1, NRES")
    # zipper declarations after IC table decls
    s = s.replace("STATIC REAL :: IC_R0(NCON)",
                  "STATIC REAL :: IC_R0(NCON)\n" + ZIP_DECLS)
    # zipper measurement before the COM block
    s = s.replace("DO C = 1, NC\n  CX := 0.0", ZIP_MEASURE + "\nDO C = 1, NC\n  CX := 0.0")
    # init: shared tables + IC tables (sheet pairs (1,2),(3,4)) + zipper tables
    angk = "\n".join(f"  RES_ANGK({i+1}) := 0.3000" for i in range(7))
    angt = "\n".join(f"  RES_ANGT0({i+1}) := {G.ANG_T0[i]:.6f}" for i in range(7))
    torsk = "\n".join(f"  RES_TORSK({i+1}) := 0.2000" for i in range(7))
    torsp = "\n".join(f"  RES_TORSP0({i+1}) := {G.TORS_P0[i]:.6f}" for i in range(7))
    hydro = "\n".join(f"  RES_HYDRO({i+1}) := {G.HYDRO[i]:.1f}" for i in range(7))
    vd = "\n".join(f"  VDAMP({c+1}) := 0.9" for c in range(4))
    ic_lines = []
    m = 0
    for cp in (0, 2):  # sheet pairs (1,2) and (3,4)
        for k in range(7):
            m += 1
            ic_lines.append(f"  IC_A({m}) := {cp*7 + k + 1}")
            ic_lines.append(f"  IC_B({m}) := {(cp+1)*7 + k + 1}")
            ic_lines.append(f"  IC_R0({m}) := 1.9468")
    zip_lines = []
    for m, (za, zb, zr) in enumerate(ZIP, start=1):
        zip_lines.append(f"  ZA({m}) := {za}")
        zip_lines.append(f"  ZB({m}) := {zb}")
        zip_lines.append(f"  ZR0({m}) := {zr:.4f}")
    inits = [G.coil_chain_lines(c + 1, f"{c * 1.0:.1f}") for c in range(4)]
    init_body = "\n".join([angk, angt, torsk, torsp, hydro, vd, ""]
                          + ic_lines + zip_lines + inits)
    s = s.replace("CALL INIT_ALL()", init_body)
    (OUT / out_name).write_text(s)
    print(f"wrote {out_name}")


build("_ZIPPER_GUIDED", True, "zipper_guided.ergo")
build("_ZIPPER_EMERGENT", False, "zipper_emergent.ergo")
