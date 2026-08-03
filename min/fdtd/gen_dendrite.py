#!/usr/bin/env python3
"""gen_dendrite.py — dendritic pattern test, Stage 1: angle sweep.

Two ribbon segments, length L=40 cells, sharing the junction cell (128,128),
ramped DC in phase, current DIVERGING from the junction to the tips
(documented choice: junction is the source, tips are the sinks — charge
ramps - at the junction (outflow 2I), + at both tips). Segment A always
along +x: cells (128..168,128), drive (I,0). Segment B rasterized at
angle theta: cells (128 + round(i cos th), 128 + round(i sin th)),
drive (I cos th, I sin th) per cell. Junction cell driven ONCE with the
vector sum (I(1+cos th), I sin th) and excluded from per-segment force
integrals (documented). Angles: 0, 30, 45, 60, 90, 120, 180 deg;
0 deg degenerates to one straight 2L segment (control), 180 deg to
back-to-back opposite rays.

Per-angle Ergo-side analysis (keeps .out compact):
- FORCE_A/FORCE_B: per-segment integrals F_JxB = sum(jy Hz, -jx Hz)
  (magnetic) and F_JE = sum(jx Ex + jy Ey) (electric drive term) and
  F_RHOE = sum(rho Ex, rho Ey) (force on accumulated charge),
  rho = discrete divergence (Ex(i,j)-Ex(i-1,j) + Ey(i,j)-Ey(i,j-1)).
- CHARGE: rho at junction, tip A, tip B, and sum |rho| over all cells.
- BMIN/EMIN: 16x16 block grids of min|Hz| and min|E| — the void maps.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "fdtd"
L = 40
JC, YC = 128, 128
I_AMP = 0.05

ANGLES = (0, 30, 45, 60, 90, 120, 180)

def cells_for(theta_deg):
    th = math.radians(theta_deg)
    cells = []
    for i in range(1, L + 1):
        x = JC + round(i * math.cos(th))
        y = YC + round(i * math.sin(th))
        if not cells or cells[-1] != (x, y):
            cells.append((x, y))
    return cells

TEMPLATE = """! DENDRITE_ANGLE a=__ANG__ — dendritic pattern Stage 1 (gen_dendrite.py)
IMPLICIT NONE

INTEGER, PARAMETER :: NX = 256, NY = 256
INTEGER, PARAMETER :: NSTEPS = 1500
REAL, PARAMETER :: S = 0.5
INTEGER, PARAMETER :: NSP = 20

STATIC REAL :: HZ(NX, NY), EX(NX, NY), EY(NX, NY)
STATIC REAL :: ABSORB(NX, NY)
STATIC REAL :: RHO(NX, NY), BMIN(16, 16), EMIN(16, 16)

REAL :: SV, RAMPV, FXA, FYA, FEA, FXB, FYB, FEB, FRXA, FRXA2, FRXB, FRXB2, EMAG
INTEGER :: I, J, T, K, BI, BJ

DO J = 1, NY
  DO I = 1, NX
    HZ(I, J) := 0.0
    EX(I, J) := 0.0
    EY(I, J) := 0.0
    ABSORB(I, J) := 1.0
  ENDDO
ENDDO
DO I = 1, NSP
  SV := 0.5 + 0.5 * 0.5 * (1.0 + COS(3.14159265358979 * REAL(NSP + 1 - I) / REAL(NSP + 1)))
  DO J = 1, NY
    ABSORB(I, J) := ABSORB(I, J) * SV
    ABSORB(NX - I + 1, J) := ABSORB(NX - I + 1, J) * SV
  ENDDO
ENDDO
DO J = 1, NSP
  SV := 0.5 + 0.5 * 0.5 * (1.0 + COS(3.14159265358979 * REAL(NSP + 1 - J) / REAL(NSP + 1)))
  DO I = 1, NX
    ABSORB(I, J) := ABSORB(I, J) * SV
    ABSORB(I, NY - J + 1) := ABSORB(I, NY - J + 1) * SV
  ENDDO
ENDDO

DO T = 1, NSTEPS
  DO J = 2, NY - 1
    DO I = 2, NX - 1
      EX(I, J) := (EX(I, J) + S * (HZ(I, J) - HZ(I, J - 1))) * ABSORB(I, J)
      EY(I, J) := (EY(I, J) - S * (HZ(I, J) - HZ(I - 1, J))) * ABSORB(I, J)
    ENDDO
  ENDDO
  RAMPV := 1.0
  IF (T <= 200) THEN
    RAMPV := 0.5 * (1.0 - COS(3.14159265358979 * REAL(T) / 200.0))
  ENDIF
__DRIVE__
  DO J = 1, NY - 1
    DO I = 1, NX - 1
      HZ(I, J) := (HZ(I, J) - S * (EY(I + 1, J) - EY(I, J) - EX(I, J + 1) + EX(I, J))) * ABSORB(I, J)
    ENDDO
  ENDDO
ENDDO

! ---- charge (discrete divergence) ----
DO J = 2, NY - 1
  DO I = 2, NX - 1
    RHO(I, J) := (EX(I, J) - EX(I - 1, J)) + (EY(I, J) - EY(I, J - 1))
  ENDDO
ENDDO

! ---- per-segment force integrals ----
FXA := 0.0
FYA := 0.0
FEA := 0.0
FRXA := 0.0
FRXA2 := 0.0
FXB := 0.0
FYB := 0.0
FEB := 0.0
FRXB := 0.0
FRXB2 := 0.0
__FORCE__

WRITE(*, "CHARGE_J %.6f", ) 
WRITE(*, "# DONE")
STOP
"""

def emit(theta):
    th = math.radians(theta)
    cb = cells_for(theta)
    ca = [(JC + i, YC) for i in range(1, L + 1)]
    drive = []
    # junction cell, driven once with the vector sum
    jx, jy = I_AMP * (1.0 + math.cos(th)), I_AMP * math.sin(th)
    drive.append(f"  EX({JC}, {YC}) := EX({JC}, {YC}) - S * {jx:.5f} * RAMPV")
    drive.append(f"  EY({JC}, {YC}) := EY({JC}, {YC}) - S * {jy:.5f} * RAMPV")
    for x, y in ca[1:]:
        drive.append(f"  EX({x}, {y}) := EX({x}, {y}) - S * {I_AMP:.5f} * RAMPV")
    cx, sy = I_AMP * math.cos(th), I_AMP * math.sin(th)
    for x, y in cb[1:]:
        drive.append(f"  EX({x}, {y}) := EX({x}, {y}) - S * {cx:.5f} * RAMPV")
        if abs(sy) > 1e-9:
            drive.append(f"  EY({x}, {y}) := EY({x}, {y}) - S * {sy:.5f} * RAMPV")
    force = []
    for x, y in ca[1:]:
        force.append(f"  FEA := FEA + {I_AMP:.5f} * EX({x}, {y})")
        force.append(f"  FYA := FYA - {I_AMP:.5f} * HZ({x}, {y})")
        force.append(f"  FRXA := FRXA + RHO({x}, {y}) * EX({x}, {y})")
        force.append(f"  FRXA2 := FRXA2 + RHO({x}, {y}) * EY({x}, {y})")
    for x, y in cb[1:]:
        force.append(f"  FEB := FEB + {cx:.5f} * EX({x}, {y}) + {sy:.5f} * EY({x}, {y})")
        force.append(f"  FXB := FXB + {sy:.5f} * HZ({x}, {y})")
        force.append(f"  FYB := FYB - {cx:.5f} * HZ({x}, {y})")
        force.append(f"  FRXB := FRXB + RHO({x}, {y}) * EX({x}, {y})")
        force.append(f"  FRXB2 := FRXB2 + RHO({x}, {y}) * EY({x}, {y})")
    t = TEMPLATE.replace("__ANG__", str(theta))
    t = t.replace("__DRIVE__", "\n".join(drive))
    t = t.replace("__FORCE__", "\n".join(force))
    # replace the placeholder CHARGE_J write with real metrics
    tipa = ca[-1]
    tipb = cb[-1]
    metrics = f"""
WRITE(*, "FORCE_A %.6f %.6f %.6f %.6f %.6f") FXA, FYA, FEA, FRXA, FRXA2
WRITE(*, "FORCE_B %.6f %.6f %.6f %.6f %.6f") FXB, FYB, FEB, FRXB, FRXB2
WRITE(*, "CHARGE_J %.6f %.6f %.6f %.6f") RHO({JC}, {YC}), RHO({tipa[0]}, {tipa[1]}), RHO({tipb[0]}, {tipb[1]}), 0.0
SV := 0.0
DO J = 2, NY - 1
  DO I = 2, NX - 1
    SV := SV + ABS(RHO(I, J))
  ENDDO
ENDDO
WRITE(*, "CHARGE_TOT %.6f") SV
DO BJ = 1, 16
  DO BI = 1, 16
    BMIN(BI, BJ) := 1.0E+30
    EMIN(BI, BJ) := 1.0E+30
  ENDDO
ENDDO
DO J = 17, NY - 16
  DO I = 17, NX - 16
    BI := 1 + (I - 1) / 16
    BJ := 1 + (J - 1) / 16
    IF ABS(HZ(I, J)) < BMIN(BI, BJ) THEN
      BMIN(BI, BJ) := ABS(HZ(I, J))
    ENDIF
    EMAG := SQRT(EX(I, J) * EX(I, J) + EY(I, J) * EY(I, J))
    IF EMAG < EMIN(BI, BJ) THEN
      EMIN(BI, BJ) := EMAG
    ENDIF
  ENDDO
ENDDO
DO BJ = 1, 16
  WRITE(*, "BMIN %d %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f") BJ, &
    BMIN(1, BJ), BMIN(2, BJ), BMIN(3, BJ), BMIN(4, BJ), BMIN(5, BJ), BMIN(6, BJ), BMIN(7, BJ), BMIN(8, BJ), &
    BMIN(9, BJ), BMIN(10, BJ), BMIN(11, BJ), BMIN(12, BJ), BMIN(13, BJ), BMIN(14, BJ), BMIN(15, BJ), BMIN(16, BJ)
ENDDO
DO BJ = 1, 16
  WRITE(*, "EMIN %d %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f") BJ, &
    EMIN(1, BJ), EMIN(2, BJ), EMIN(3, BJ), EMIN(4, BJ), EMIN(5, BJ), EMIN(6, BJ), EMIN(7, BJ), EMIN(8, BJ), &
    EMIN(9, BJ), EMIN(10, BJ), EMIN(11, BJ), EMIN(12, BJ), EMIN(13, BJ), EMIN(14, BJ), EMIN(15, BJ), EMIN(16, BJ)
ENDDO
WRITE(*, "# DONE")
STOP
"""
    t = t.replace('WRITE(*, "CHARGE_J %.6f", ) \nWRITE(*, "# DONE")\nSTOP\n', metrics)
    out = PM / f"dendrite_a{theta:03d}.ergo"
    out.write_text(t)
    print(f"wrote {out}")

for a in ANGLES:
    emit(a)
