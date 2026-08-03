#!/usr/bin/env python3
"""gen_amyloid.py — sequential amyloid assembly test (GNNQQNY / 1YJP).

Oracle: real microcrystal geometry from pdb/1YJP.pdb — asymmetric unit is
one chain; the in-register neighbor is the crystal b translation
(b = 4.866 A, exactly the literature ~4.8 A). Scaled to model units
(x0.400074, mean Cα-Cα bond = 1.52): inter-strand in-register Cα-Cα
= 1.9468 units (4.866 A); screw-mate (sheet-zipper) closest approach
6.888 A = 2.756 units (the ~10 A sheet spacing is the mean plane
distance; measured closest Cα approach in this crystal is 6.9 A).

Design (sequential assembly per user instinct):
  stage 1: dimer from denatured coils, guided (in-register inter-chain
           Go contacts, INTER_R0 = 1.9468) vs unguided (contacts OFF,
           hydrophobic only — GNNQQNY is polar; only Tyr7 has HYDRO=1.0)
  stage 2: dimer template (chains 1-2 start AT the oracle geometry,
           VDAMP 0.5 strong damping) + chain 3 from coil
  stage 3: trimer template (chains 1-3 damped) + chain 4 from coil

Force field: same recipe as the protein sims (Morse backbone, angles
K=0.3, torsions K=0.2 from real chain-A geometry, steric, hydrophobic,
Go-style harmonic inter-chain contacts INTER_K=1.0). Phase/Kuramoto
machinery omitted (HB_CAP=0 recipe disables it there too — documented).
Thermal: heat cycles to frame 1200, floor 0.001, quench at 9600 of
MAXFRAME=12000.

Outputs: TRACE (mean in-register distance per adjacent pair, every 200),
GEOM (per-pair per-residue k-k and k-(k+1) distances at the end),
COM (chain centers of mass).
"""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "min" / "amyloid"
OUT.mkdir(exist_ok=True)

ORACLE = json.load(open("/tmp/yjp_model.json"))
SCALE = ORACLE["scale"]
CA = ORACLE["chainA"]
BSHIFT = 4.866 * SCALE  # 1.9468 model units

HYDRO = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]  # G N N Q Q N Y


def vsub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def vlen(v): return math.sqrt(sum(x*x for x in v))
def vdot(a, b): return sum(x*y for x, y in zip(a, b))
def vcross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def angle(r1, r2, r3):
    b1, b2 = vsub(r1, r2), vsub(r3, r2)
    l1, l2 = vlen(b1), vlen(b2)
    if l1 == 0 or l2 == 0: return 0.0
    c = max(-1.0, min(1.0, vdot(b1, b2)/(l1*l2)))
    return math.acos(c)


def dihedral(r1, r2, r3, r4):
    b1, b2, b3 = vsub(r2, r1), vsub(r3, r2), vsub(r4, r3)
    n1, n2 = vcross(b1, b2), vcross(b2, b3)
    b2len = vlen(b2)
    if b2len == 0: return 0.0
    return math.atan2(b2len * vdot(b1, n2), vdot(n1, n2))


ANG_T0 = [0.0] + [angle(CA[i-1], CA[i], CA[i+1]) for i in range(1, 6)] + [0.0]
TORS_P0 = [0.0] + [dihedral(CA[i-1], CA[i], CA[i+1], CA[i+2]) for i in range(1, 5)] + [0.0, 0.0]

# intra-chain Go contacts in real chain A (|i-j| >= 4, < 6.5 A = 2.6 units)
INTRA_GO = [(i+1, j+1) for i in range(7) for j in range(i+4, 7)
            if vlen(vsub(CA[i], CA[j])) < 2.6]
print(f"oracle: angles {[f'{a:.3f}' for a in ANG_T0]}")
print(f"oracle: torsions {[f'{t:.3f}' for t in TORS_P0]}")
print(f"oracle: intra-chain Go contacts (|i-j|>=4, <2.6u): {INTRA_GO}")


def shifted(chain, nshift):
    return [[p[0], p[1] + nshift * BSHIFT, p[2]] for p in chain]


TEMPLATE = """! AMYLOID__TAG — GNNQQNY sequential assembly (oracle: 1YJP b-axis
! in-register spacing 4.866 A = 1.9468 model units; screw-mate sheet
! zipper closest Cα-Cα 6.888 A = 2.756 units). NC=__NC__ chains x 7 res.
! Guided: inter-chain in-register Go contacts (INTER_K, INTER_R0).
! Unguided variant: contacts compiled out (hydrophobic only).
IMPLICIT NONE

PARAMETER INTEGER :: NRES = 7
PARAMETER INTEGER :: NC = __NC__
PARAMETER INTEGER :: NTOT = __NTOT__
PARAMETER INTEGER :: MAXFRAME = 12000
PARAMETER REAL :: DT = 0.01
PARAMETER REAL :: FORCE_SCALE = 6.0
PARAMETER REAL :: BASE_DAMP = 0.9
PARAMETER REAL :: HEAT_START = 0.001
PARAMETER REAL :: HEAT_PEAK = 1.0
PARAMETER REAL :: BACKBONE_R0 = 1.52
PARAMETER REAL :: BACKBONE_D = 1.4
PARAMETER REAL :: MORSE_A = 1.0
PARAMETER REAL :: STERIC_SIG = 1.60
PARAMETER REAL :: STERIC_EPS = 0.1
PARAMETER REAL :: STERIC_CUT = 2.5
PARAMETER REAL :: HYDRO_STRENGTH = 0.0020
PARAMETER REAL :: HYDRO_R0 = 4.0
PARAMETER REAL :: HYDRO_CUTOFF = 8.0
PARAMETER REAL :: HYDRO_ALPHA = 1.0
PARAMETER REAL :: NATIVE_K = 1.00
PARAMETER REAL :: INTER_K = 1.00
PARAMETER REAL :: INTER_R0 = 1.9468
PARAMETER INTEGER :: NCON = __NCON__

STATIC REAL :: RES_X(__NTOT__), RES_Y(__NTOT__), RES_Z(__NTOT__)
STATIC REAL :: RES_VX(__NTOT__), RES_VY(__NTOT__), RES_VZ(__NTOT__)
STATIC REAL :: RES_ANGK(7), RES_ANGT0(7), RES_TORSK(7), RES_TORSP0(7)
STATIC REAL :: RES_HYDRO(7), VDAMP(NC)
STATIC INTEGER :: IC_A(NCON), IC_B(NCON)
STATIC REAL :: IC_R0(NCON)
STATIC REAL :: THERMAL_CURRENT

STATIC INTEGER :: I, J, K, C, FRAME, M, IA, IB, L, SAME
STATIC REAL :: DX, DY, DZ, D, E, F, FM, CX, CY, CZ, BX, BY, BZ
STATIC REAL :: UN, VN, CS, UX, UY, UZ, WX, WY, WZ
STATIC REAL :: B1X, B1Y, B1Z, B2X, B2Y, B2Z, B3X, B3Y, B3Z
STATIC REAL :: N1X, N1Y, N1Z, N2X, N2Y, N2Z, N1MAG2, N2MAG2, B2MAG, N1MAG, N2MAG, PHI
STATIC REAL :: DPHI_DR1X, DPHI_DR1Y, DPHI_DR1Z, DPHI_DR4X, DPHI_DR4Y, DPHI_DR4Z
STATIC REAL :: DPHI_DR2X, DPHI_DR2Y, DPHI_DR2Z, DPHI_DR3X, DPHI_DR3Y, DPHI_DR3Z
STATIC REAL :: B1DOT, B3DOT, SCALE_B2, SCALE_B1, SCALE_B3
STATIC REAL :: U1, U2, COSTH, SINTH, PHI2, CANDX, CANDY, CANDZ, DD
STATIC INTEGER :: ATT, J2, OK

CALL INIT_ALL()

WRITE(*, "# AMYLOID__TAG NC=__NC__ NCON=__NCON__ MAXFRAME=12000")
WRITE(*, "# TRACE frame pair mean_kk_dist (every 200)")
WRITE(*, "# GEOM pair k dist_kk dist_kk1 (final)")
WRITE(*, "# COM chain x y z (final)")

DO FRAME = 1, MAXFRAME

  CALL UPDATE_THERMAL(FRAME)

  ! Thermal impulses (velocity kicks)
  DO I = 1, NTOT
    RES_VX(I) := RES_VX(I) + THERMAL_CURRENT * SIN((I+1)*7.3 + REAL(FRAME)*0.17)
    RES_VY(I) := RES_VY(I) + THERMAL_CURRENT * COS((I+1)*5.7 + REAL(FRAME)*0.31)
    RES_VZ(I) := RES_VZ(I) + THERMAL_CURRENT * SIN((I+1)*3.1 + REAL(FRAME)*0.09)
  ENDDO

  ! Steric repulsion (same-chain |i-j| >= 4 or any inter-chain pair)
  DO I = 1, NTOT - 1
    DO J = I + 1, NTOT
      SAME := 0
      IF INT(REAL(I - 1) / REAL(NRES)) = INT(REAL(J - 1) / REAL(NRES)) THEN
        IF J - I < 4 THEN
          SAME := 1
        ENDIF
      ENDIF
      IF SAME = 0 THEN
        DX := RES_X(I) - RES_X(J)
        DY := RES_Y(I) - RES_Y(J)
        DZ := RES_Z(I) - RES_Z(J)
        D := SQRT(DX*DX + DY*DY + DZ*DZ)
        IF D > 0.0 .AND. D < STERIC_CUT THEN
          FM := STERIC_EPS * (STERIC_SIG / D) ** 6
          RES_VX(I) := RES_VX(I) + FM * DX / D * DT * FORCE_SCALE
          RES_VY(I) := RES_VY(I) + FM * DY / D * DT * FORCE_SCALE
          RES_VZ(I) := RES_VZ(I) + FM * DZ / D * DT * FORCE_SCALE
          RES_VX(J) := RES_VX(J) - FM * DX / D * DT * FORCE_SCALE
          RES_VY(J) := RES_VY(J) - FM * DY / D * DT * FORCE_SCALE
          RES_VZ(J) := RES_VZ(J) - FM * DZ / D * DT * FORCE_SCALE
        ENDIF
      ENDIF
    ENDDO
  ENDDO

  ! Hydrophobic attraction (GNNQQNY is polar: only Tyr7 has weight)
  DO I = 1, NTOT - 1
    DO J = I + 1, NTOT
      SAME := 0
      IF INT(REAL(I - 1) / REAL(NRES)) = INT(REAL(J - 1) / REAL(NRES)) THEN
        IF J - I < 4 THEN
          SAME := 1
        ENDIF
      ENDIF
      L := MOD(J - 1, NRES) + 1
      IF SAME = 0 .AND. RES_HYDRO(MOD(I - 1, NRES) + 1) > 0.0 .AND. RES_HYDRO(L) > 0.0 THEN
        DX := RES_X(I) - RES_X(J)
        DY := RES_Y(I) - RES_Y(J)
        DZ := RES_Z(I) - RES_Z(J)
        D := SQRT(DX*DX + DY*DY + DZ*DZ)
        IF D > 0.0 .AND. D < HYDRO_CUTOFF THEN
          FM := -HYDRO_STRENGTH * RES_HYDRO(MOD(I - 1, NRES) + 1) * RES_HYDRO(L) * EXP(-HYDRO_ALPHA * (D - HYDRO_R0))
          RES_VX(I) := RES_VX(I) + FM * DX / D * DT * FORCE_SCALE
          RES_VY(I) := RES_VY(I) + FM * DY / D * DT * FORCE_SCALE
          RES_VZ(I) := RES_VZ(I) + FM * DZ / D * DT * FORCE_SCALE
          RES_VX(J) := RES_VX(J) - FM * DX / D * DT * FORCE_SCALE
          RES_VY(J) := RES_VY(J) - FM * DY / D * DT * FORCE_SCALE
          RES_VZ(J) := RES_VZ(J) - FM * DZ / D * DT * FORCE_SCALE
        ENDIF
      ENDIF
    ENDDO
  ENDDO

__INTRAGO__

__ICONTACTS__

  ! Backbone + angles + torsions, per chain
  DO C = 1, NC
    ! Morse bonds
    DO I = 1, NRES - 1
      IA := (C - 1) * NRES + I
      IB := (C - 1) * NRES + I + 1
      DX := RES_X(IA) - RES_X(IB)
      DY := RES_Y(IA) - RES_Y(IB)
      DZ := RES_Z(IA) - RES_Z(IB)
      D := SQRT(DX*DX + DY*DY + DZ*DZ)
      IF D > 0.0 THEN
        E := EXP(-MORSE_A * (D - BACKBONE_R0))
        FM := -2.0 * BACKBONE_D * MORSE_A * (1.0 - E) * E * FORCE_SCALE
        RES_VX(IA) := RES_VX(IA) + FM * DX / D * DT
        RES_VY(IA) := RES_VY(IA) + FM * DY / D * DT
        RES_VZ(IA) := RES_VZ(IA) + FM * DZ / D * DT
        RES_VX(IB) := RES_VX(IB) - FM * DX / D * DT
        RES_VY(IB) := RES_VY(IB) - FM * DY / D * DT
        RES_VZ(IB) := RES_VZ(IB) - FM * DZ / D * DT
      ENDIF
    ENDDO

    ! Angle bending (shared per-residue targets from real 1YJP chain A)
    DO I = 2, NRES - 1
      IA := (C - 1) * NRES + I
      BX := RES_X(IA - 1) - RES_X(IA)
      BY := RES_Y(IA - 1) - RES_Y(IA)
      BZ := RES_Z(IA - 1) - RES_Z(IA)
      CX := RES_X(IA + 1) - RES_X(IA)
      CY := RES_Y(IA + 1) - RES_Y(IA)
      CZ := RES_Z(IA + 1) - RES_Z(IA)
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
        RES_VX(IA - 1) := RES_VX(IA - 1) - E * UX * DT * FORCE_SCALE
        RES_VY(IA - 1) := RES_VY(IA - 1) - E * UY * DT * FORCE_SCALE
        RES_VZ(IA - 1) := RES_VZ(IA - 1) - E * UZ * DT * FORCE_SCALE
        RES_VX(IA + 1) := RES_VX(IA + 1) - E * WX * DT * FORCE_SCALE
        RES_VY(IA + 1) := RES_VY(IA + 1) - E * WY * DT * FORCE_SCALE
        RES_VZ(IA + 1) := RES_VZ(IA + 1) - E * WZ * DT * FORCE_SCALE
        RES_VX(IA) := RES_VX(IA) + (E * UX + E * WX) * DT * FORCE_SCALE
        RES_VY(IA) := RES_VY(IA) + (E * UY + E * WY) * DT * FORCE_SCALE
        RES_VZ(IA) := RES_VZ(IA) + (E * UZ + E * WZ) * DT * FORCE_SCALE
      ENDIF
    ENDDO

    ! Torsions (shared targets from real 1YJP chain A)
    DO I = 2, NRES - 2
      IA := (C - 1) * NRES + I
      B1X := RES_X(IA) - RES_X(IA - 1)
      B1Y := RES_Y(IA) - RES_Y(IA - 1)
      B1Z := RES_Z(IA) - RES_Z(IA - 1)
      B2X := RES_X(IA + 1) - RES_X(IA)
      B2Y := RES_Y(IA + 1) - RES_Y(IA)
      B2Z := RES_Z(IA + 1) - RES_Z(IA)
      B3X := RES_X(IA + 2) - RES_X(IA + 1)
      B3Y := RES_Y(IA + 2) - RES_Y(IA + 1)
      B3Z := RES_Z(IA + 2) - RES_Z(IA + 1)
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
        RES_VX(IA - 1) := RES_VX(IA - 1) + F * DPHI_DR1X * DT * FORCE_SCALE
        RES_VY(IA - 1) := RES_VY(IA - 1) + F * DPHI_DR1Y * DT * FORCE_SCALE
        RES_VZ(IA - 1) := RES_VZ(IA - 1) + F * DPHI_DR1Z * DT * FORCE_SCALE
        RES_VX(IA) := RES_VX(IA) + F * DPHI_DR2X * DT * FORCE_SCALE
        RES_VY(IA) := RES_VY(IA) + F * DPHI_DR2Y * DT * FORCE_SCALE
        RES_VZ(IA) := RES_VZ(IA) + F * DPHI_DR2Z * DT * FORCE_SCALE
        RES_VX(IA + 1) := RES_VX(IA + 1) + F * DPHI_DR3X * DT * FORCE_SCALE
        RES_VY(IA + 1) := RES_VY(IA + 1) + F * DPHI_DR3Y * DT * FORCE_SCALE
        RES_VZ(IA + 1) := RES_VZ(IA + 1) + F * DPHI_DR3Z * DT * FORCE_SCALE
        RES_VX(IA + 2) := RES_VX(IA + 2) + F * DPHI_DR4X * DT * FORCE_SCALE
        RES_VY(IA + 2) := RES_VY(IA + 2) + F * DPHI_DR4Y * DT * FORCE_SCALE
        RES_VZ(IA + 2) := RES_VZ(IA + 2) + F * DPHI_DR4Z * DT * FORCE_SCALE
      ENDIF
    ENDDO
  ENDDO

  ! Velocity damping (per-chain VDAMP: template chains strongly damped)
  DO I = 1, NTOT
    C := INT(REAL(I - 1) / REAL(NRES)) + 1
    RES_VX(I) := RES_VX(I) * VDAMP(C)
    RES_VY(I) := RES_VY(I) * VDAMP(C)
    RES_VZ(I) := RES_VZ(I) * VDAMP(C)
  ENDDO

  ! Position update
  DO I = 1, NTOT
    RES_X(I) := RES_X(I) + RES_VX(I) * DT
    RES_Y(I) := RES_Y(I) + RES_VY(I) * DT
    RES_Z(I) := RES_Z(I) + RES_VZ(I) * DT
  ENDDO

  ! Trace: mean in-register distance per adjacent chain pair
  IF MOD(FRAME, 200) = 0 THEN
    DO C = 1, NC - 1
      D := 0.0
      DO K = 1, NRES
        IA := (C - 1) * NRES + K
        IB := C * NRES + K
        D := D + SQRT((RES_X(IA) - RES_X(IB))**2 + (RES_Y(IA) - RES_Y(IB))**2 + (RES_Z(IA) - RES_Z(IB))**2)
      ENDDO
      WRITE(*, "TRACE %d %d %.4f") FRAME, C, D / REAL(NRES)
    ENDDO
  ENDIF

ENDDO

! Final geometry table
DO C = 1, NC - 1
  DO K = 1, NRES
    IA := (C - 1) * NRES + K
    IB := C * NRES + K
    D := SQRT((RES_X(IA) - RES_X(IB))**2 + (RES_Y(IA) - RES_Y(IB))**2 + (RES_Z(IA) - RES_Z(IB))**2)
    E := 0.0
    IF K < NRES THEN
      E := SQRT((RES_X(IA) - RES_X(IB + 1))**2 + (RES_Y(IA) - RES_Y(IB + 1))**2 + (RES_Z(IA) - RES_Z(IB + 1))**2)
    ENDIF
    WRITE(*, "GEOM %d %d %.4f %.4f") C, K, D, E
  ENDDO
ENDDO
DO C = 1, NC
  CX := 0.0
  CY := 0.0
  CZ := 0.0
  DO K = 1, NRES
    CX := CX + RES_X((C - 1) * NRES + K)
    CY := CY + RES_Y((C - 1) * NRES + K)
    CZ := CZ + RES_Z((C - 1) * NRES + K)
  ENDDO
  WRITE(*, "COM %d %.4f %.4f %.4f") C, CX / REAL(NRES), CY / REAL(NRES), CZ / REAL(NRES)
ENDDO
WRITE(*, "# DONE")

STOP

SUBROUTINE UPDATE_THERMAL(FRAME)
  INTEGER :: FRAME
  REAL :: FRAC
  THERMAL_CURRENT := HEAT_START
  IF FRAME < 300 THEN
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
  ENDIF
  ! Quench tail: zero thermal noise after frame 9600
  IF FRAME > 9600 THEN
    THERMAL_CURRENT := 0.0
  ENDIF
  RETURN
END
"""

ICONTACTS = """  ! Inter-chain in-register Go contacts (adjacent chains, k <-> k)
  DO M = 1, NCON
    IA := IC_A(M)
    IB := IC_B(M)
    DX := RES_X(IA) - RES_X(IB)
    DY := RES_Y(IA) - RES_Y(IB)
    DZ := RES_Z(IA) - RES_Z(IB)
    D := SQRT(DX*DX + DY*DY + DZ*DZ)
    IF D > 0.0 THEN
      FM := -2.0 * INTER_K * (D - IC_R0(M))
      RES_VX(IA) := RES_VX(IA) + FM * DX / D * DT * FORCE_SCALE
      RES_VY(IA) := RES_VY(IA) + FM * DY / D * DT * FORCE_SCALE
      RES_VZ(IA) := RES_VZ(IA) + FM * DZ / D * DT * FORCE_SCALE
      RES_VX(IB) := RES_VX(IB) - FM * DX / D * DT * FORCE_SCALE
      RES_VY(IB) := RES_VY(IB) - FM * DY / D * DT * FORCE_SCALE
      RES_VZ(IB) := RES_VZ(IB) - FM * DZ / D * DT * FORCE_SCALE
    ENDIF
  ENDDO
"""

INTRAGO = """  ! Intra-chain Go contacts from real 1YJP chain A (none found with
  ! |i-j| >= 4 and Cα-Cα < 2.6 units — extended strand, documented)
  DO M = 1, NGO
    IA := GO_A(M)
    IB := GO_B(M)
    DX := RES_X(IA) - RES_X(IB)
    DY := RES_Y(IA) - RES_Y(IB)
    DZ := RES_Z(IA) - RES_Z(IB)
    D := SQRT(DX*DX + DY*DY + DZ*DZ)
    IF D > 0.0 THEN
      FM := -2.0 * NATIVE_K * (D - GO_R0(M))
      RES_VX(IA) := RES_VX(IA) + FM * DX / D * DT * FORCE_SCALE
      RES_VY(IA) := RES_VY(IA) + FM * DY / D * DT * FORCE_SCALE
      RES_VZ(IA) := RES_VZ(IA) + FM * DZ / D * DT * FORCE_SCALE
      RES_VX(IB) := RES_VX(IB) - FM * DX / D * DT * FORCE_SCALE
      RES_VY(IB) := RES_VY(IB) - FM * DY / D * DT * FORCE_SCALE
      RES_VZ(IB) := RES_VZ(IB) - FM * DZ / D * DT * FORCE_SCALE
    ENDIF
  ENDDO
"""


def coil_chain_lines(c, seed_off):
    """Hash-walk coil init for chain c (index base (c-1)*NRES)."""
    return f"""
  ! Chain {c}: hash-walk coil (seed offset {seed_off})
  RES_X({(c-1)*7+1}) := {10.0 + (c-1)*10.0}
  RES_Y({(c-1)*7+1}) := 10.0
  RES_Z({(c-1)*7+1}) := 10.0
  DO I = 2, NRES
    OK := 0
    ATT := 0
    DO WHILE ATT < 20
      ATT := ATT + 1
      U1 := MOD(ABS(SIN(REAL(I) * 12.9898 + REAL(ATT) * 3.7 + {seed_off}) * 43758.5453), 1.0)
      U2 := MOD(ABS(SIN(REAL(I) * 78.2330 + REAL(ATT) * 1.3 + {seed_off}) * 12543.1230), 1.0)
      COSTH := 2.0 * U1 - 1.0
      SINTH := SQRT(1.0 - COSTH * COSTH)
      PHI2 := 2.0 * 3.14159265 * U2
      CANDX := RES_X({(c-1)*7} + I - 1) + SINTH * COS(PHI2) * BACKBONE_R0
      CANDY := RES_Y({(c-1)*7} + I - 1) + SINTH * SIN(PHI2) * BACKBONE_R0
      CANDZ := RES_Z({(c-1)*7} + I - 1) + COSTH * BACKBONE_R0
      OK := 1
      IF I ≥ 5 THEN
        DO J2 = 1, I - 4
          DD := SQRT((CANDX - RES_X({(c-1)*7} + J2))**2 + (CANDY - RES_Y({(c-1)*7} + J2))**2 + (CANDZ - RES_Z({(c-1)*7} + J2))**2)
          IF DD < 1.55 THEN
            OK := 0
          ENDIF
        ENDDO
      ENDIF
      IF OK = 1 THEN
        ATT := 20
      ENDIF
    ENDDO
    RES_X({(c-1)*7} + I) := CANDX
    RES_Y({(c-1)*7} + I) := CANDY
    RES_Z({(c-1)*7} + I) := CANDZ
  ENDDO
  DO I = 1, NRES
    RES_VX({(c-1)*7} + I) := 0.0
    RES_VY({(c-1)*7} + I) := 0.0
    RES_VZ({(c-1)*7} + I) := 0.0
  ENDDO"""


def oracle_chain_lines(c, nshift):
    """Chain c initialized at the oracle geometry (shift nshift * b)."""
    lines = [f"\n  ! Chain {c}: oracle geometry (shift {nshift} x b = {nshift*1.9468:.4f} units)"]
    for k in range(7):
        x, y, z = shifted(CA, nshift)[k]
        lines.append(f"  RES_X({(c-1)*7+k+1}) := {x:.6f}")
        lines.append(f"  RES_Y({(c-1)*7+k+1}) := {y:.6f}")
        lines.append(f"  RES_Z({(c-1)*7+k+1}) := {z:.6f}")
    lines.append(f"  DO I = 1, NRES")
    lines.append(f"    RES_VX({(c-1)*7} + I) := 0.0")
    lines.append(f"    RES_VY({(c-1)*7} + I) := 0.0")
    lines.append(f"    RES_VZ({(c-1)*7} + I) := 0.0")
    lines.append(f"  ENDDO")
    return "\n".join(lines)


def build(tag, nc, guided, template_chains, vdamp, out_name):
    ntot = nc * 7
    s = TEMPLATE.replace("__TAG__", tag).replace("__NC__", str(nc))
    s = s.replace("__NTOT__", str(ntot)).replace("__NCON__", str((nc - 1) * 7 if guided else 1))
    s = s.replace("__ICONTACTS__", ICONTACTS if guided else "  ! (inter-chain contacts compiled out — unguided variant)")
    s = s.replace("__INTRAGO__", "")
    # parameter tables
    angk = "\n".join(f"  RES_ANGK({i+1}) := 0.3000" for i in range(7))
    angt = "\n".join(f"  RES_ANGT0({i+1}) := {ANG_T0[i]:.6f}" for i in range(7))
    torsk = "\n".join(f"  RES_TORSK({i+1}) := 0.2000" for i in range(7))
    torsp = "\n".join(f"  RES_TORSP0({i+1}) := {TORS_P0[i]:.6f}" for i in range(7))
    hydro = "\n".join(f"  RES_HYDRO({i+1}) := {HYDRO[i]:.1f}" for i in range(7))
    vd = "\n".join(f"  VDAMP({c+1}) := {v}" for c, v in enumerate(vdamp))
    ic = []
    if guided:
        m = 0
        for cp in range(nc - 1):
            for k in range(7):
                m += 1
                ic.append(f"  IC_A({m}) := {cp*7 + k + 1}")
                ic.append(f"  IC_B({m}) := {(cp+1)*7 + k + 1}")
                ic.append(f"  IC_R0({m}) := 1.9468")
    else:
        ic = ["  IC_A(1) := 1", "  IC_B(1) := 1", "  IC_R0(1) := 0.0"]
    inits = []
    for c in range(nc):
        if c < template_chains:
            inits.append(oracle_chain_lines(c + 1, c))
        else:
            inits.append(coil_chain_lines(c + 1, f"{c * 1.0:.1f}"))
    init_body = "\n".join([angk, angt, torsk, torsp, hydro, vd, ""] + ic + inits)
    s = s.replace("CALL INIT_ALL()", init_body)
    (OUT / out_name).write_text(s)
    print(f"wrote {out_name}")


# stage 1: dimer from coils, guided vs unguided
build("_DIMER_GUIDED", 2, True, 0, [0.9, 0.9], "amyloid_dimer_guided.ergo")
build("_DIMER_HYDRO", 2, False, 0, [0.9, 0.9], "amyloid_dimer_hydro.ergo")
# stage 2: dimer template (damped) + chain 3 from coil
build("_TRIMER", 3, True, 2, [0.5, 0.5, 0.9], "amyloid_trimer.ergo")
# stage 3: trimer template (damped) + chain 4 from coil
build("_TETRAMER", 4, True, 3, [0.5, 0.5, 0.5, 0.9], "amyloid_tetramer.ergo")
