#!/usr/bin/env python3
"""gen_mc.py — rigid-body Monte-Carlo domain docking on the fold-then-dock
final states (dock_sim_struct.out, the ×3-freeze-adjacent deployable dock).

DESIGN (documented prominently):
- MOVE CLASS: rigid-body rotation (random axis, angle +/-ROT_DEG about the
  domain's COM) + translation (random direction, TR_STEP), ONE domain per
  move, domain picked by hash. Steric guard: any moved bead within 1.0 of a
  non-domain bead -> revert (keeps the search physical; native inter-domain
  pairs are >= ~2).
- SCORING (the key decision): full-chain Kabsch RMSD to native — with
  domains held rigid this is EXACTLY the placement error of the
  decomposition (internal is constant). We score by placement RMSD as a
  MOVE-SET COMPLETENESS TEST (can rigid-body moves find native placement
  at all?), NOT by field energy: the field's assembly minimum is proven
  wrong (rebalance_check.md) — energy-scored MC would drive back to the
  wrong assembly. The field stays the physics; MC is the search layer.
- RANDOMNESS: validated splitmix white hash (per-(step,block) seed +
  xorshift chain; deterministic, reproducible trajectories).
- SCHEDULE: Metropolis at constant T (RMSD units; per-move ΔS ~0.1-0.7),
  greedy (T=0) control, and geometric cooling T0->T0/100.
- START: all 8 blocks' dock_sim final states (8 independent MC runs =
  seed statistics), domains rigid (their folds are the ×3-frozen inputs).
- 10000 steps/variant; trajectory every 250 steps.

Emits mc_{greedy,t005,t02,t10,cool,r1,r15}.ergo (step-size sweep at the
greedy schedule: r1=1°/0.2, base=5°/0.5, r15=15°/1.0).
"""
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"
NRES, NBLK = 556, 8

lines = (PM / "dock_sim_struct.out").read_text().splitlines()
X0 = np.zeros((NBLK, NRES, 3))
NAT = None
for b in range(1, NBLK + 1):
    i = lines.index(f"FINAL_STRUCTURE_B {b}")
    pts, nat = [], []
    for ln in lines[i + 1:i + 1 + NRES]:
        p = ln.split(",")
        pts.append([float(p[1]), float(p[2]), float(p[3])])
        nat.append([float(p[4]), float(p[5]), float(p[6])])
    X0[b - 1] = np.array(pts)
    NAT = np.array(nat)

init = ["SUBROUTINE INIT_STATE()", "  INTEGER :: I, K"]
for b in range(NBLK):
    for i in range(NRES):
        k = b * NRES + i + 1
        init.append(f"  X({k}) := {X0[b, i, 0]:.6f}")
        init.append(f"  Y({k}) := {X0[b, i, 1]:.6f}")
        init.append(f"  Z({k}) := {X0[b, i, 2]:.6f}")
for i in range(NRES):
    init.append(f"  NX({i + 1}) := {NAT[i, 0]:.6f}")
    init.append(f"  NY({i + 1}) := {NAT[i, 1]:.6f}")
    init.append(f"  NZ({i + 1}) := {NAT[i, 2]:.6f}")
init.append("END")
INIT_STATE = "\n".join(init)

PROG = """! MC_DOCK — rigid-body Monte-Carlo domain docking (gen_mc.py).
! Scoring: full-chain Kabsch RMSD (placement error at fixed internal
! geometry) — move-set completeness test, NOT field energy.
IMPLICIT NONE

PARAMETER INTEGER :: NRES = 556, NBLK = 8, NPTS = 4448
PARAMETER INTEGER :: NSTEPS = 10000
PARAMETER REAL :: ROT_RAD = __ROT__
PARAMETER REAL :: TR_STEP = __TR__
PARAMETER REAL :: TEMP0 = __T0__
PARAMETER REAL :: COOLK = __COOLK__

STATIC REAL :: X(NPTS), Y(NPTS), Z(NPTS)
STATIC REAL :: NX(NRES), NY(NRES), NZ(NRES)
STATIC REAL :: XOLD(NRES), YOLD(NRES), ZOLD(NRES)
STATIC REAL :: SCORE(NBLK), BST(NBLK)
STATIC INTEGER :: NACC(NBLK), H, ST, B, D, I, J, LO, HI, OFF, CLASH
STATIC REAL :: CX, CY, CZ, UX, UY, UZ, DN, TH, CTH, STH
STATIC REAL :: VX, VY, VZ, RX, RY, RZ, S0, S1, U, TEMP, DD, DDOT, DX, DY, DZ
STATIC REAL :: MSC, MBST
! Kabsch locals
STATIC REAL :: XC, YC, ZC, XN, YN, ZN
STATIC REAL :: SXX, SXY, SXZ, SYX, SYY, SYZ, SZX, SZY, SZZ
STATIC REAL :: N44(4,4), VEC(4), NEWVEC(4), NORM
STATIC REAL :: Q0, Q1, Q2, Q3, QQ
STATIC REAL :: R11, R12, R13, R21, R22, R23, R31, R32, R33
STATIC REAL :: TX, TY, TZ, SUM_DIST_SQ, RMSD_NATIVE

CALL INIT_STATE()
DO B = 1, NBLK
  OFF := (B - 1) * NRES
  CALL COMPUTE_KABSCH(OFF)
  SCORE(B) := RMSD_NATIVE
  BST(B) := RMSD_NATIVE
  NACC(B) := 0
ENDDO
WRITE(*, "# MC_DOCK rot __ROT__ tr __TR__ T0 __T0__ coolk __COOLK__ (gen_mc.py)")
WRITE(*, "# start scores:")
DO B = 1, NBLK
  WRITE(*, "MCSTART %d %.4f") B, SCORE(B)
ENDDO

DO ST = 1, NSTEPS
  TEMP := TEMP0
  IF COOLK > 0.0 THEN
    TEMP := TEMP0 * EXP(0.0 - COOLK * REAL(ST) / REAL(NSTEPS))
  ENDIF
  DO B = 1, NBLK
    OFF := (B - 1) * NRES
    ! white-hash stream for this (step, block)
    H := IEOR(ST * 2654435761, B * 40503)
    H := IEOR(H, ISHFT(H, -30))
    H := H * 6364136223846793005
    H := IEOR(H, ISHFT(H, -27))
    H := H * 6364136223846793005
    H := IEOR(H, ISHFT(H, -31))
    D := 1 + MOD(IAND(H, 65535), 4)
    IF D = 1 THEN
      LO := 1
      HI := 152
    ENDIF
    IF D = 2 THEN
      LO := 153
      HI := 320
    ENDIF
    IF D = 3 THEN
      LO := 321
      HI := 440
    ENDIF
    IF D = 4 THEN
      LO := 441
      HI := 556
    ENDIF
    ! domain COM
    CX := 0.0
    CY := 0.0
    CZ := 0.0
    DO I = LO, HI
      CX := CX + X(OFF + I)
      CY := CY + Y(OFF + I)
      CZ := CZ + Z(OFF + I)
    ENDDO
    CX := CX / REAL(HI - LO + 1)
    CY := CY / REAL(HI - LO + 1)
    CZ := CZ / REAL(HI - LO + 1)
    ! random axis
    H := IEOR(H, ISHFT(H, -17))
    UX := 2.0 * REAL(IAND(H, 65535)) / 65535.0 - 1.0
    H := IEOR(H, ISHFT(H, -7))
    UY := 2.0 * REAL(IAND(H, 65535)) / 65535.0 - 1.0
    H := IEOR(H, ISHFT(H, -13))
    UZ := 2.0 * REAL(IAND(H, 65535)) / 65535.0 - 1.0
    DN := SQRT(UX*UX + UY*UY + UZ*UZ)
    IF DN < 1.0E-9 THEN
      DN := 1.0
    ENDIF
    UX := UX / DN
    UY := UY / DN
    UZ := UZ / DN
    H := IEOR(H, ISHFT(H, -5))
    TH := ROT_RAD
    IF REAL(IAND(H, 65535)) / 65535.0 < 0.5 THEN
      TH := 0.0 - ROT_RAD
    ENDIF
    CTH := COS(TH)
    STH := SIN(TH)
    ! translation direction
    H := IEOR(H, ISHFT(H, -9))
    TX := 2.0 * REAL(IAND(H, 65535)) / 65535.0 - 1.0
    H := IEOR(H, ISHFT(H, -11))
    TY := 2.0 * REAL(IAND(H, 65535)) / 65535.0 - 1.0
    H := IEOR(H, ISHFT(H, -15))
    TZ := 2.0 * REAL(IAND(H, 65535)) / 65535.0 - 1.0
    DN := SQRT(TX*TX + TY*TY + TZ*TZ)
    IF DN < 1.0E-9 THEN
      DN := 1.0
    ENDIF
    TX := TX / DN * TR_STEP
    TY := TY / DN * TR_STEP
    TZ := TZ / DN * TR_STEP
    ! apply move (Rodrigues about COM + translate), saving old positions
    DO I = LO, HI
      XOLD(I) := X(OFF + I)
      YOLD(I) := Y(OFF + I)
      ZOLD(I) := Z(OFF + I)
      VX := X(OFF + I) - CX
      VY := Y(OFF + I) - CY
      VZ := Z(OFF + I) - CZ
      DDOT := UX*VX + UY*VY + UZ*VZ
      RX := VX*CTH + (UY*VZ - UZ*VY)*STH + UX*DDOT*(1.0 - CTH)
      RY := VY*CTH + (UZ*VX - UX*VZ)*STH + UY*DDOT*(1.0 - CTH)
      RZ := VZ*CTH + (UX*VY - UY*VX)*STH + UZ*DDOT*(1.0 - CTH)
      X(OFF + I) := CX + RX + TX
      Y(OFF + I) := CY + RY + TY
      Z(OFF + I) := CZ + RZ + TZ
    ENDDO
    ! steric guard: moved domain vs all non-domain beads
    CLASH := 0
    DO I = LO, HI
      DO J = 1, NRES
        IF J < LO .OR. J > HI THEN
          DX := X(OFF + I) - X(OFF + J)
          DY := Y(OFF + I) - Y(OFF + J)
          DZ := Z(OFF + I) - Z(OFF + J)
          IF DX*DX + DY*DY + DZ*DZ < 1.0 THEN
            CLASH := 1
          ENDIF
        ENDIF
      ENDDO
    ENDDO
    IF CLASH = 1 THEN
      DO I = LO, HI
        X(OFF + I) := XOLD(I)
        Y(OFF + I) := YOLD(I)
        Z(OFF + I) := ZOLD(I)
      ENDDO
    ELSE
      S0 := SCORE(B)
      CALL COMPUTE_KABSCH(OFF)
      S1 := RMSD_NATIVE
      H := IEOR(H, ISHFT(H, -19))
      U := REAL(IAND(H, 65535)) / 65535.0
      IF S1 < S0 .OR. (TEMP0 > 0.0 .AND. U < EXP((S0 - S1) / TEMP)) THEN
        SCORE(B) := S1
        NACC(B) := NACC(B) + 1
        IF S1 < BST(B) THEN
          BST(B) := S1
        ENDIF
      ELSE
        DO I = LO, HI
          X(OFF + I) := XOLD(I)
          Y(OFF + I) := YOLD(I)
          Z(OFF + I) := ZOLD(I)
        ENDDO
      ENDIF
    ENDIF
  ENDDO
  IF MOD(ST, 250) = 0 THEN
    MSC := 0.0
    MBST := 0.0
    DO B = 1, NBLK
      MSC := MSC + SCORE(B)
      MBST := MBST + BST(B)
    ENDDO
    WRITE(*, "MCTRACE %d %.4f %.4f") ST, MSC / REAL(NBLK), MBST / REAL(NBLK)
  ENDIF
ENDDO

DO B = 1, NBLK
  WRITE(*, "MCFINAL %d %.4f %.4f %d") B, SCORE(B), BST(B), NACC(B)
ENDDO
WRITE(*, "# DONE")
STOP

! ════════════════════════════════════════════════════════════
! COMPUTE_KABSCH: full-chain Kabsch RMSD of X/Y/Z (block OFF) vs
! NX/NY/NZ — the sim's quaternion power-iteration convention
! ════════════════════════════════════════════════════════════

SUBROUTINE COMPUTE_KABSCH(OFFB)
  INTEGER :: OFFB
  XC := 0.0
  YC := 0.0
  ZC := 0.0
  XN := 0.0
  YN := 0.0
  ZN := 0.0
  DO I = 1, NRES
    XC := XC + X(OFFB + I)
    YC := YC + Y(OFFB + I)
    ZC := ZC + Z(OFFB + I)
    XN := XN + NX(I)
    YN := YN + NY(I)
    ZN := ZN + NZ(I)
  ENDDO
  XC := XC / REAL(NRES)
  YC := YC / REAL(NRES)
  ZC := ZC / REAL(NRES)
  XN := XN / REAL(NRES)
  YN := YN / REAL(NRES)
  ZN := ZN / REAL(NRES)
  SXX := 0.0
  SXY := 0.0
  SXZ := 0.0
  SYX := 0.0
  SYY := 0.0
  SYZ := 0.0
  SZX := 0.0
  SZY := 0.0
  SZZ := 0.0
  DO I = 1, NRES
    RX := X(OFFB + I) - XC
    RY := Y(OFFB + I) - YC
    RZ := Z(OFFB + I) - ZC
    SXX := SXX + RX * (NX(I) - XN)
    SXY := SXY + RX * (NY(I) - YN)
    SXZ := SXZ + RX * (NZ(I) - ZN)
    SYX := SYX + RY * (NX(I) - XN)
    SYY := SYY + RY * (NY(I) - YN)
    SYZ := SYZ + RY * (NZ(I) - ZN)
    SZX := SZX + RZ * (NX(I) - XN)
    SZY := SZY + RZ * (NY(I) - YN)
    SZZ := SZZ + RZ * (NZ(I) - ZN)
  ENDDO
  N44(1,1) := SXX + SYY + SZZ
  N44(1,2) := SYZ - SZY
  N44(1,3) := SZX - SXZ
  N44(1,4) := SXY - SYX
  N44(2,1) := SYZ - SZY
  N44(2,2) := SXX - SYY - SZZ
  N44(2,3) := SXY + SYX
  N44(2,4) := SXZ + SZX
  N44(3,1) := SZX - SXZ
  N44(3,2) := SXY + SYX
  N44(3,3) := -SXX + SYY - SZZ
  N44(3,4) := SYZ + SZY
  N44(4,1) := SXY - SYX
  N44(4,2) := SXZ + SZX
  N44(4,3) := SYZ + SZY
  N44(4,4) := -SXX - SYY + SZZ
  VEC(1) := 1.0
  VEC(2) := 0.0
  VEC(3) := 0.0
  VEC(4) := 0.0
  DO I = 1, 40
    NEWVEC(1) := N44(1,1)*VEC(1) + N44(1,2)*VEC(2) + N44(1,3)*VEC(3) + N44(1,4)*VEC(4)
    NEWVEC(2) := N44(2,1)*VEC(1) + N44(2,2)*VEC(2) + N44(2,3)*VEC(3) + N44(2,4)*VEC(4)
    NEWVEC(3) := N44(3,1)*VEC(1) + N44(3,2)*VEC(2) + N44(3,3)*VEC(3) + N44(3,4)*VEC(4)
    NEWVEC(4) := N44(4,1)*VEC(1) + N44(4,2)*VEC(2) + N44(4,3)*VEC(3) + N44(4,4)*VEC(4)
    NORM := SQRT(NEWVEC(1)*NEWVEC(1) + NEWVEC(2)*NEWVEC(2) + NEWVEC(3)*NEWVEC(3) + NEWVEC(4)*NEWVEC(4))
    IF NORM > 1.0E-12 THEN
      VEC(1) := NEWVEC(1) / NORM
      VEC(2) := NEWVEC(2) / NORM
      VEC(3) := NEWVEC(3) / NORM
      VEC(4) := NEWVEC(4) / NORM
    ENDIF
  ENDDO
  Q0 := VEC(1)
  Q1 := VEC(2)
  Q2 := VEC(3)
  Q3 := VEC(4)
  QQ := Q0*Q0 + Q1*Q1 + Q2*Q2 + Q3*Q3
  IF QQ > 1.0E-12 THEN
    QQ := SQRT(QQ)
    Q0 := Q0 / QQ
    Q1 := Q1 / QQ
    Q2 := Q2 / QQ
    Q3 := Q3 / QQ
  ENDIF
  R11 := Q0*Q0 + Q1*Q1 - Q2*Q2 - Q3*Q3
  R12 := 2.0*(Q1*Q2 - Q0*Q3)
  R13 := 2.0*(Q1*Q3 + Q0*Q2)
  R21 := 2.0*(Q1*Q2 + Q0*Q3)
  R22 := Q0*Q0 - Q1*Q1 + Q2*Q2 - Q3*Q3
  R23 := 2.0*(Q2*Q3 - Q0*Q1)
  R31 := 2.0*(Q1*Q3 - Q0*Q2)
  R32 := 2.0*(Q2*Q3 + Q0*Q1)
  R33 := Q0*Q0 - Q1*Q1 - Q2*Q2 + Q3*Q3
  SUM_DIST_SQ := 0.0
  DO I = 1, NRES
    RX := X(OFFB + I) - XC
    RY := Y(OFFB + I) - YC
    RZ := Z(OFFB + I) - ZC
    TX := R11*RX + R12*RY + R13*RZ
    TY := R21*RX + R22*RY + R23*RZ
    TZ := R31*RX + R32*RY + R33*RZ
    SUM_DIST_SQ := SUM_DIST_SQ + (TX - (NX(I) - XN))**2 + (TY - (NY(I) - YN))**2 + (TZ - (NZ(I) - ZN))**2
  ENDDO
  RMSD_NATIVE := SQRT(SUM_DIST_SQ / REAL(NRES))
  RETURN
END

__INIT_STATE__
"""

VARIANTS = {
    "greedy": dict(rot=math.radians(5), tr=0.5, t0=0.0, coolk=0.0),
    "t005": dict(rot=math.radians(5), tr=0.5, t0=0.05, coolk=0.0),
    "t02": dict(rot=math.radians(5), tr=0.5, t0=0.2, coolk=0.0),
    "t10": dict(rot=math.radians(5), tr=0.5, t0=1.0, coolk=0.0),
    "cool": dict(rot=math.radians(5), tr=0.5, t0=1.0, coolk=4.605),
    "r1": dict(rot=math.radians(1), tr=0.2, t0=0.0, coolk=0.0),
    "r15": dict(rot=math.radians(15), tr=1.0, t0=0.0, coolk=0.0),
}

for name, p in VARIANTS.items():
    t = (PROG.replace("__ROT__", f"{p['rot']:.6f}")
             .replace("__TR__", f"{p['tr']:.4f}")
             .replace("__T0__", f"{p['t0']:.4f}")
             .replace("__COOLK__", f"{p['coolk']:.4f}")
             .replace("__INIT_STATE__", INIT_STATE))
    out = PM / f"mc_{name}.ergo"
    out.write_text(t)
    print(f"wrote {out} ({len(t.splitlines())} lines)")
