#!/usr/bin/env python3
"""gen_condensate.py — LLPS in the packed form: 8 constant-T blocks, one run.

Design (all choices documented in condensate_check.md):
  - 8 blocks x 24 chains x 7 residues (GNNQQNY, validated intra-chain
    machinery: Morse backbone, angles K=0.3, torsions K=0.2 with 1YJP
    chain-A targets). NO Go contacts, NO register torsions.
  - Each block at a CONSTANT temperature TB(B) = TMUL(B) * BASE_T,
    BASE_T = 0.01, TMUL = {0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0}
    (replaces the heat-cycle schedule: a phase diagram needs isotherms).
  - Blocks are thermally isolated (separate state; shared read-only
    tables); verified via per-block velocity-RMS at the end.
  - Confinement: weak harmonic sphere at (30,30,30), R_BOX = 18 u,
    CONF_K = 0.01 (no reflecting walls -> no unphysical spikes).
  - Inter-chain attraction (type-independent): Gaussian well
    FM = -ATT_K * EXP(-1.0 * (D - ATT_R0)^2), ATT_R0 = 2.0, cut 3.0 u,
    ATT_K = 0.005. Steric repulsion kept (inter-chain any pair,
    same-chain |i-j| >= 4).
  - Identical coil layouts across blocks (T is the only variable).
  - MAXFRAME 24000, cluster metrics every 200 frames: largest-cluster
    fraction (contact < 2.8 u ~ 7 A), cluster count, dense vs dilute
    density. Label-propagation union-find over 24 chains per block.
"""

import math
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "amyloid"))
import gen_amyloid as G  # re-emits amyloid bases (deterministic); reuse tables

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "min" / "condensate"
OUT.mkdir(exist_ok=True)

TMULS = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0]

TEMPLATE = """! CONDENSATE — 8 constant-temperature blocks x 24 chains x 7 residues
! (GNNQQNY), LLPS phase-diagram row in ONE run. No Go contacts, no
! register torsions, generic inter-chain Gaussian attraction.
IMPLICIT NONE

PARAMETER INTEGER :: NRES = 7
PARAMETER INTEGER :: NCH = 24
PARAMETER INTEGER :: NBLK = 8
PARAMETER INTEGER :: NPB = 168
PARAMETER INTEGER :: NTOT = 1344
PARAMETER INTEGER :: MAXFRAME = 24000
PARAMETER REAL :: DT = 0.01
PARAMETER REAL :: FORCE_SCALE = 6.0
PARAMETER REAL :: BASE_DAMP = 0.9
PARAMETER REAL :: BASE_T = 0.01
PARAMETER REAL :: BACKBONE_R0 = 1.52
PARAMETER REAL :: BACKBONE_D = 1.4
PARAMETER REAL :: MORSE_A = 1.0
PARAMETER REAL :: STERIC_SIG = 1.60
PARAMETER REAL :: STERIC_EPS = 0.1
PARAMETER REAL :: STERIC_CUT = 2.5
PARAMETER REAL :: ATT_K = 0.03
PARAMETER REAL :: ATT_R0 = 2.0
PARAMETER REAL :: ATT_CUT = 3.0
PARAMETER REAL :: R_BOX = 18.0
PARAMETER REAL :: CONF_K = 0.01
PARAMETER REAL :: CLU_R = 2.8

STATIC REAL :: RES_X(NTOT), RES_Y(NTOT), RES_Z(NTOT)
STATIC REAL :: RES_VX(NTOT), RES_VY(NTOT), RES_VZ(NTOT)
STATIC REAL :: RES_ANGK(7), RES_ANGT0(7), RES_TORSK(7), RES_TORSP0(7)
STATIC REAL :: TB(NBLK)
STATIC INTEGER :: CM(NCH, NCH), LAB(NCH), CNT(NCH)

STATIC INTEGER :: I, J, K, C, C1, C2, M, B, OFF, FRAME, IA, IB, L, SAME
STATIC INTEGER :: BEST, NCL, MX
STATIC REAL :: DX, DY, DZ, D, E, F, FM, CX, CY, CZ, BX, BY, BZ
STATIC REAL :: UN, VN, CS, UX, UY, UZ, WX, WY, WZ
STATIC REAL :: B1X, B1Y, B1Z, B2X, B2Y, B2Z, B3X, B3Y, B3Z
STATIC REAL :: N1X, N1Y, N1Z, N2X, N2Y, N2Z, N1MAG2, N2MAG2, B2MAG, N1MAG, N2MAG, PHI
STATIC REAL :: DPHI_DR1X, DPHI_DR1Y, DPHI_DR1Z, DPHI_DR4X, DPHI_DR4Y, DPHI_DR4Z
STATIC REAL :: DPHI_DR2X, DPHI_DR2Y, DPHI_DR2Z, DPHI_DR3X, DPHI_DR3Y, DPHI_DR3Z
STATIC REAL :: B1DOT, B3DOT, SCALE_B2, SCALE_B1, SCALE_B3
STATIC REAL :: U1, U2, COSTH, SINTH, PHI2, CANDX, CANDY, CANDZ, DD, DR
STATIC REAL :: CCX, CCY, CCZ, RMAX, VRMS, DENSE, DILUTE, FRACV
STATIC INTEGER :: ATT, J2, OK, K1, K2, I1, I2, NC1

__INIT__

WRITE(*, "# CONDENSATE NBLK=8 NCH=24 BASE_T=0.01 ATT_K=0.005 R_BOX=18")
WRITE(*, "# CLU block frame largest_frac nclusters dense_rho dilute_rho")
WRITE(*, "# VEL block mean_speed2 (kinetic-T proxy)")

DO FRAME = 1, MAXFRAME

  DO B = 1, NBLK
    OFF := (B - 1) * NPB

    ! Thermal kicks at the block's CONSTANT temperature
    DO I = 1, NPB
      RES_VX(OFF + I) := RES_VX(OFF + I) + TB(B) * SIN((I+1)*7.3 + REAL(FRAME)*0.17)
      RES_VY(OFF + I) := RES_VY(OFF + I) + TB(B) * COS((I+1)*5.7 + REAL(FRAME)*0.31)
      RES_VZ(OFF + I) := RES_VZ(OFF + I) + TB(B) * SIN((I+1)*3.1 + REAL(FRAME)*0.09)
    ENDDO

    ! Steric repulsion (same-chain |i-j| >= 4 or any inter-chain pair,
    ! same block only)
    DO I = 1, NPB - 1
      DO J = I + 1, NPB
        SAME := 0
        IF INT(REAL(I - 1) / REAL(NRES)) = INT(REAL(J - 1) / REAL(NRES)) THEN
          IF J - I < 4 THEN
            SAME := 1
          ENDIF
        ENDIF
        IF SAME = 0 THEN
          DX := RES_X(OFF + I) - RES_X(OFF + J)
          DY := RES_Y(OFF + I) - RES_Y(OFF + J)
          DZ := RES_Z(OFF + I) - RES_Z(OFF + J)
          D := SQRT(DX*DX + DY*DY + DZ*DZ)
          IF D > 0.0 .AND. D < STERIC_CUT THEN
            FM := STERIC_EPS * (STERIC_SIG / D) ** 6
            RES_VX(OFF + I) := RES_VX(OFF + I) + FM * DX / D * DT * FORCE_SCALE
            RES_VY(OFF + I) := RES_VY(OFF + I) + FM * DY / D * DT * FORCE_SCALE
            RES_VZ(OFF + I) := RES_VZ(OFF + I) + FM * DZ / D * DT * FORCE_SCALE
            RES_VX(OFF + J) := RES_VX(OFF + J) - FM * DX / D * DT * FORCE_SCALE
            RES_VY(OFF + J) := RES_VY(OFF + J) - FM * DY / D * DT * FORCE_SCALE
            RES_VZ(OFF + J) := RES_VZ(OFF + J) - FM * DZ / D * DT * FORCE_SCALE
          ENDIF
        ENDIF
      ENDDO
    ENDDO

    ! Generic inter-chain attraction (Gaussian well, type-independent)
    DO I = 1, NPB - 1
      DO J = I + 1, NPB
        IF INT(REAL(I - 1) / REAL(NRES)) /= INT(REAL(J - 1) / REAL(NRES)) THEN
          DX := RES_X(OFF + I) - RES_X(OFF + J)
          DY := RES_Y(OFF + I) - RES_Y(OFF + J)
          DZ := RES_Z(OFF + I) - RES_Z(OFF + J)
          D := SQRT(DX*DX + DY*DY + DZ*DZ)
          IF D > 0.0 .AND. D < ATT_CUT THEN
            FM := 0.0 - ATT_K * EXP(0.0 - (D - ATT_R0) ** 2)
            RES_VX(OFF + I) := RES_VX(OFF + I) + FM * DX / D * DT * FORCE_SCALE
            RES_VY(OFF + I) := RES_VY(OFF + I) + FM * DY / D * DT * FORCE_SCALE
            RES_VZ(OFF + I) := RES_VZ(OFF + I) + FM * DZ / D * DT * FORCE_SCALE
            RES_VX(OFF + J) := RES_VX(OFF + J) - FM * DX / D * DT * FORCE_SCALE
            RES_VY(OFF + J) := RES_VY(OFF + J) - FM * DY / D * DT * FORCE_SCALE
            RES_VZ(OFF + J) := RES_VZ(OFF + J) - FM * DZ / D * DT * FORCE_SCALE
          ENDIF
        ENDIF
      ENDDO
    ENDDO

    ! Weak harmonic confinement to the sphere at (30,30,30)
    DO I = 1, NPB
      DX := RES_X(OFF + I) - 30.0
      DY := RES_Y(OFF + I) - 30.0
      DZ := RES_Z(OFF + I) - 30.0
      DR := SQRT(DX*DX + DY*DY + DZ*DZ)
      IF DR > R_BOX .AND. DR > 0.0 THEN
        FM := 0.0 - CONF_K * (DR - R_BOX)
        RES_VX(OFF + I) := RES_VX(OFF + I) + FM * DX / DR * DT * FORCE_SCALE
        RES_VY(OFF + I) := RES_VY(OFF + I) + FM * DY / DR * DT * FORCE_SCALE
        RES_VZ(OFF + I) := RES_VZ(OFF + I) + FM * DZ / DR * DT * FORCE_SCALE
      ENDIF
    ENDDO

    ! Backbone + angles + torsions, per chain (shared 1YJP targets)
    DO C = 1, NCH
      IA := OFF + (C - 1) * NRES
      DO I = 1, NRES - 1
        DX := RES_X(IA + I) - RES_X(IA + I + 1)
        DY := RES_Y(IA + I) - RES_Y(IA + I + 1)
        DZ := RES_Z(IA + I) - RES_Z(IA + I + 1)
        D := SQRT(DX*DX + DY*DY + DZ*DZ)
        IF D > 0.0 THEN
          E := EXP(-MORSE_A * (D - BACKBONE_R0))
          FM := -2.0 * BACKBONE_D * MORSE_A * (1.0 - E) * E * FORCE_SCALE
          RES_VX(IA + I) := RES_VX(IA + I) + FM * DX / D * DT
          RES_VY(IA + I) := RES_VY(IA + I) + FM * DY / D * DT
          RES_VZ(IA + I) := RES_VZ(IA + I) + FM * DZ / D * DT
          RES_VX(IA + I + 1) := RES_VX(IA + I + 1) - FM * DX / D * DT
          RES_VY(IA + I + 1) := RES_VY(IA + I + 1) - FM * DY / D * DT
          RES_VZ(IA + I + 1) := RES_VZ(IA + I + 1) - FM * DZ / D * DT
        ENDIF
      ENDDO
      DO I = 2, NRES - 1
        IB := IA + I
        BX := RES_X(IB - 1) - RES_X(IB)
        BY := RES_Y(IB - 1) - RES_Y(IB)
        BZ := RES_Z(IB - 1) - RES_Z(IB)
        CX := RES_X(IB + 1) - RES_X(IB)
        CY := RES_Y(IB + 1) - RES_Y(IB)
        CZ := RES_Z(IB + 1) - RES_Z(IB)
        UN := SQRT(BX*BX + BY*BY + BZ*BZ)
        VN := SQRT(CX*CX + CY*CY + CZ*CZ)
        IF UN > 1.0E-12 .AND. VN > 1.0E-12 THEN
          CS := MAX(-1.0, MIN(1.0, (BX*CX + BY*CY + BZ*CZ) / (UN * VN)))
          E := 2.0 * RES_ANGK(I) * (CS - COS(RES_ANGT0(I)))
          UX := (CX / (UN * VN) - CS * BX / UN / UN)
          UY := (CY / (UN * VN) - CS * BY / UN / UN)
          UZ := (CZ / (UN * VN) - CS * BZ / UN / UN)
          WX := (BX / (UN * VN) - CS * CX / VN / VN)
          WY := (BY / (UN * VN) - CS * CY / VN / VN)
          WZ := (BZ / (UN * VN) - CS * CZ / VN / VN)
          RES_VX(IB - 1) := RES_VX(IB - 1) - E * UX * DT * FORCE_SCALE
          RES_VY(IB - 1) := RES_VY(IB - 1) - E * UY * DT * FORCE_SCALE
          RES_VZ(IB - 1) := RES_VZ(IB - 1) - E * UZ * DT * FORCE_SCALE
          RES_VX(IB + 1) := RES_VX(IB + 1) - E * WX * DT * FORCE_SCALE
          RES_VY(IB + 1) := RES_VY(IB + 1) - E * WY * DT * FORCE_SCALE
          RES_VZ(IB + 1) := RES_VZ(IB + 1) - E * WZ * DT * FORCE_SCALE
          RES_VX(IB) := RES_VX(IB) + (E * UX + E * WX) * DT * FORCE_SCALE
          RES_VY(IB) := RES_VY(IB) + (E * UY + E * WY) * DT * FORCE_SCALE
          RES_VZ(IB) := RES_VZ(IB) + (E * UZ + E * WZ) * DT * FORCE_SCALE
        ENDIF
      ENDDO
      DO I = 2, NRES - 2
        IB := IA + I
        B1X := RES_X(IB) - RES_X(IB - 1)
        B1Y := RES_Y(IB) - RES_Y(IB - 1)
        B1Z := RES_Z(IB) - RES_Z(IB - 1)
        B2X := RES_X(IB + 1) - RES_X(IB)
        B2Y := RES_Y(IB + 1) - RES_Y(IB)
        B2Z := RES_Z(IB + 1) - RES_Z(IB)
        B3X := RES_X(IB + 2) - RES_X(IB + 1)
        B3Y := RES_Y(IB + 2) - RES_Y(IB + 1)
        B3Z := RES_Z(IB + 2) - RES_Z(IB + 1)
        N1X := B1Y*B2Z - B1Z*B2Y
        N1Y := B1Z*B2X - B1X*B2Z
        N1Z := B1X*B2Y - B1Y*B2X
        N2X := B2Y*B3Z - B2Z*B3Y
        N2Y := B2Z*B3X - B2X*B3Z
        N2Z := B2X*B3Y - B2Y*B3X
        N1MAG2 := N1X*N1X + N1Y*N1Y + N1Z*N1Z
        N2MAG2 := N2X*N2X + N2Y*N2Y + N2Z*N2Z
        B2MAG := SQRT(B2X*B2X + B2Y*B2Y + B2Z*B2Z)
        IF N1MAG2 > 1.0E-12 .AND. N2MAG2 > 1.0E-12 .AND. B2MAG > 1.0E-12 THEN
          N1MAG := SQRT(N1MAG2)
          N2MAG := SQRT(N2MAG2)
          PHI := ATAN2(B2MAG*(B1X*N2X + B1Y*N2Y + B1Z*N2Z), N1X*N2X + N1Y*N2Y + N1Z*N2Z)
          F := -2.0 * RES_TORSK(I) * SIN(PHI - RES_TORSP0(I))
          DPHI_DR1X := -B2MAG / N1MAG2 * N1X
          DPHI_DR1Y := -B2MAG / N1MAG2 * N1Y
          DPHI_DR1Z := -B2MAG / N1MAG2 * N1Z
          DPHI_DR4X := B2MAG / N2MAG2 * N2X
          DPHI_DR4Y := B2MAG / N2MAG2 * N2Y
          DPHI_DR4Z := B2MAG / N2MAG2 * N2Z
          B1DOT := B1X*B2X + B1Y*B2Y + B1Z*B2Z
          B3DOT := B3X*B2X + B3Y*B2Y + B3Z*B2Z
          SCALE_B2 := 1.0 / (B2MAG * B2MAG)
          SCALE_B1 := B1DOT * SCALE_B2
          SCALE_B3 := B3DOT * SCALE_B2
          DPHI_DR2X := -(1.0 + SCALE_B1) * DPHI_DR1X + SCALE_B3 * DPHI_DR4X
          DPHI_DR2Y := -(1.0 + SCALE_B1) * DPHI_DR1Y + SCALE_B3 * DPHI_DR4Y
          DPHI_DR2Z := -(1.0 + SCALE_B1) * DPHI_DR1Z + SCALE_B3 * DPHI_DR4Z
          DPHI_DR3X := -(DPHI_DR1X + DPHI_DR2X + DPHI_DR4X)
          DPHI_DR3Y := -(DPHI_DR1Y + DPHI_DR2Y + DPHI_DR4Y)
          DPHI_DR3Z := -(DPHI_DR1Z + DPHI_DR2Z + DPHI_DR4Z)
          RES_VX(IB - 1) := RES_VX(IB - 1) + F * DPHI_DR1X * DT * FORCE_SCALE
          RES_VY(IB - 1) := RES_VY(IB - 1) + F * DPHI_DR1Y * DT * FORCE_SCALE
          RES_VZ(IB - 1) := RES_VZ(IB - 1) + F * DPHI_DR1Z * DT * FORCE_SCALE
          RES_VX(IB) := RES_VX(IB) + F * DPHI_DR2X * DT * FORCE_SCALE
          RES_VY(IB) := RES_VY(IB) + F * DPHI_DR2Y * DT * FORCE_SCALE
          RES_VZ(IB) := RES_VZ(IB) + F * DPHI_DR2Z * DT * FORCE_SCALE
          RES_VX(IB + 1) := RES_VX(IB + 1) + F * DPHI_DR3X * DT * FORCE_SCALE
          RES_VY(IB + 1) := RES_VY(IB + 1) + F * DPHI_DR3Y * DT * FORCE_SCALE
          RES_VZ(IB + 1) := RES_VZ(IB + 1) + F * DPHI_DR3Z * DT * FORCE_SCALE
          RES_VX(IB + 2) := RES_VX(IB + 2) + F * DPHI_DR4X * DT * FORCE_SCALE
          RES_VY(IB + 2) := RES_VY(IB + 2) + F * DPHI_DR4Y * DT * FORCE_SCALE
          RES_VZ(IB + 2) := RES_VZ(IB + 2) + F * DPHI_DR4Z * DT * FORCE_SCALE
        ENDIF
      ENDDO
    ENDDO

    ! Velocity damping + position update
    DO I = 1, NPB
      RES_VX(OFF + I) := RES_VX(OFF + I) * BASE_DAMP
      RES_VY(OFF + I) := RES_VY(OFF + I) * BASE_DAMP
      RES_VZ(OFF + I) := RES_VZ(OFF + I) * BASE_DAMP
      RES_X(OFF + I) := RES_X(OFF + I) + RES_VX(OFF + I) * DT
      RES_Y(OFF + I) := RES_Y(OFF + I) + RES_VY(OFF + I) * DT
      RES_Z(OFF + I) := RES_Z(OFF + I) + RES_VZ(OFF + I) * DT
    ENDDO

    ! Cluster analysis every 200 frames (label-propagation union-find)
    IF MOD(FRAME, 200) = 0 THEN
      DO C1 = 1, NCH
        LAB(C1) := C1
        DO C2 = 1, NCH
          CM(C1, C2) := 0
        ENDDO
      ENDDO
      DO C1 = 1, NCH - 1
        DO C2 = C1 + 1, NCH
          DO K1 = 1, NRES
            DO K2 = 1, NRES
              I1 := OFF + (C1 - 1) * NRES + K1
              I2 := OFF + (C2 - 1) * NRES + K2
              D := SQRT((RES_X(I1) - RES_X(I2))**2 + (RES_Y(I1) - RES_Y(I2))**2 + (RES_Z(I1) - RES_Z(I2))**2)
              IF D < CLU_R THEN
                CM(C1, C2) := 1
                CM(C2, C1) := 1
              ENDIF
            ENDDO
          ENDDO
        ENDDO
      ENDDO
      DO C1 = 1, NCH - 1
        DO C2 = C1 + 1, NCH
          IF CM(C1, C2) = 1 THEN
            M := MIN(LAB(C1), LAB(C2))
            BEST := MAX(LAB(C1), LAB(C2))
            DO C = 1, NCH
              IF LAB(C) = BEST THEN
                LAB(C) := M
              ENDIF
            ENDDO
          ENDIF
        ENDDO
      ENDDO
      DO C = 1, NCH
        CNT(C) := 0
      ENDDO
      DO C = 1, NCH
        CNT(LAB(C)) := CNT(LAB(C)) + 1
      ENDDO
      MX := 0
      BEST := 1
      NCL := 0
      DO C = 1, NCH
        IF CNT(C) > 0 THEN
          NCL := NCL + 1
        ENDIF
        IF CNT(C) > MX THEN
          MX := CNT(C)
          BEST := C
        ENDIF
      ENDDO
      ! largest-cluster COM, radius, densities
      CCX := 0.0
      CCY := 0.0
      CCZ := 0.0
      DO C = 1, NCH
        IF LAB(C) = BEST THEN
          DO K = 1, NRES
            I1 := OFF + (C - 1) * NRES + K
            CCX := CCX + RES_X(I1)
            CCY := CCY + RES_Y(I1)
            CCZ := CCZ + RES_Z(I1)
          ENDDO
        ENDIF
      ENDDO
      NC1 := MX * NRES
      CCX := CCX / REAL(NC1)
      CCY := CCY / REAL(NC1)
      CCZ := CCZ / REAL(NC1)
      RMAX := 0.0
      DO C = 1, NCH
        IF LAB(C) = BEST THEN
          DO K = 1, NRES
            I1 := OFF + (C - 1) * NRES + K
            D := SQRT((RES_X(I1) - CCX)**2 + (RES_Y(I1) - CCY)**2 + (RES_Z(I1) - CCZ)**2)
            IF D > RMAX THEN
              RMAX := D
            ENDIF
          ENDDO
        ENDIF
      ENDDO
      RMAX := RMAX + 1.5
      DENSE := REAL(NC1) / (4.1887902 * RMAX ** 3)
      ! dilute density over box minus cluster volume, free volume floored
      ! at 25% of the box (finite-size guard for large clusters)
      DILUTE := REAL(NPB - NC1) / (4.1887902 * (R_BOX ** 3 - MIN(RMAX ** 3, 0.75 * R_BOX ** 3)))
      FRACV := REAL(MX) / REAL(NCH)
      WRITE(*, "CLU %d %d %.4f %d %.6f %.6f") B, FRAME, FRACV, NCL, DENSE, DILUTE
    ENDIF
  ENDDO
ENDDO

! Per-block kinetic temperature (isolation check)
DO B = 1, NBLK
  OFF := (B - 1) * NPB
  VRMS := 0.0
  DO I = 1, NPB
    VRMS := VRMS + RES_VX(OFF + I)**2 + RES_VY(OFF + I)**2 + RES_VZ(OFF + I)**2
  ENDDO
  WRITE(*, "VEL %d %.6f") B, VRMS / REAL(NPB)
ENDDO
WRITE(*, "# DONE")

STOP
"""

# init: shared tables + per-block constant temperatures + coils on a grid
angk = "\n".join(f"  RES_ANGK({i+1}) := 0.3000" for i in range(7))
angt = "\n".join(f"  RES_ANGT0({i+1}) := {G.ANG_T0[i]:.6f}" for i in range(7))
torsk = "\n".join(f"  RES_TORSK({i+1}) := 0.2000" for i in range(7))
torsp = "\n".join(f"  RES_TORSP0({i+1}) := {G.TORS_P0[i]:.6f}" for i in range(7))
tb = "\n".join(f"  TB({b+1}) := {0.01 * m:.5f}   ! TMUL {m}" for b, m in enumerate(TMULS))

# coil starts: 3x3x3-ish grid inside the box (center 30, spacing 9), same
# layout every block (temperature is the only variable)
GRID = []
for gx in range(3):
    for gy in range(3):
        for gz in range(3):
            GRID.append((30.0 + (gx - 1) * 5.0, 30.0 + (gy - 1) * 5.0, 30.0 + (gz - 1) * 5.0))
assert len(GRID) >= 24

inits = []
for b in range(8):
    for c in range(24):
        lines = G.coil_chain_lines(c + 1, f"{c * 1.0:.1f}")
        # retarget array indices: chain c of block b -> global residue base
        base_local = (c) * 7
        base_global = b * 168 + base_local
        lines = lines.replace(f"RES_X({base_local + 1})", f"RES_X({base_global + 1})")
        lines = lines.replace(f"{{10.0 + (c) * 10.0}}", "")
        lines = lines.replace(f"RES_X({base_global + 1}) := {10.0 + c * 10.0}",
                              f"RES_X({base_global + 1}) := {GRID[c][0]}")
        lines = lines.replace(f"RES_Y({base_local + 1}) := 10.0",
                              f"RES_Y({base_global + 1}) := {GRID[c][1]}")
        lines = lines.replace(f"RES_Z({base_local + 1}) := 10.0",
                              f"RES_Z({base_global + 1}) := {GRID[c][2]}")
        # offset the hash-walk indices to the global base
        lines = lines.replace(f"RES_X({base_local} + I", f"RES_X({base_global} + I")
        lines = lines.replace(f"RES_Y({base_local} + I", f"RES_Y({base_global} + I")
        lines = lines.replace(f"RES_Z({base_local} + I", f"RES_Z({base_global} + I")
        lines = lines.replace(f"RES_X({base_local} + J2", f"RES_X({base_global} + J2")
        lines = lines.replace(f"RES_Y({base_local} + J2", f"RES_Y({base_global} + J2")
        lines = lines.replace(f"RES_Z({base_local} + J2", f"RES_Z({base_global} + J2")
        lines = lines.replace(f"RES_X({base_local} + I)", f"RES_X({base_global} + I)")
        lines = lines.replace(f"RES_Y({base_local} + I)", f"RES_Y({base_global} + I)")
        lines = lines.replace(f"RES_Z({base_local} + I)", f"RES_Z({base_global} + I)")
        inits.append(lines)

init_body = "\n".join([angk, angt, torsk, torsp, tb, ""] + inits)
s = TEMPLATE.replace("__INIT__", init_body)
(OUT / "condensate.ergo").write_text(s)
print(f"wrote {OUT / 'condensate.ergo'} ({len(s.splitlines())} lines)")
