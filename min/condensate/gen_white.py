#!/usr/bin/env python3
"""gen_white.py — white-noise bath (integer-hash PRNG) + validation + hot rerun.

PRNG (documented, deterministic, statistically white; Ergo has no RAND):
  H := IEOR(I * 2654435761, FRAME * 40503)
  H := IEOR(H, ISHFT(H, -13))   (xorshift; Y: another -17 step, Z: -7)
  NOISE := (REAL(IAND(H, 65535)) / 65535.0 - 0.5) * T * 2.449
Knuth multiplicative hash (64-bit Ergo integers verified). Amplitude
calibration: uniform [-0.5, 0.5] has variance 1/12; x2.449 (= sqrt(6))
matches the old sinusoid's variance 0.5 per component — same noise
power, zero mean, white in time (each FRAME a fresh hash).

Outputs:
  white_bath.ergo — bath validation: 2 packed blocks x 96 FREE particles
    (no forces at all), block A = white hash, block B = old sinusoid,
    same TAMP = 0.02 and identical start layout. Prints MSD (mean
    squared displacement from t=0), speed^2, and a 2000-frame noise
    series per drive for autocorrelation.
  white_hot48.ergo / white_hot96.ergo — condensate_hot{48,96} with the
    kick section replaced by the hash (everything else identical).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "min" / "condensate"

BATH = """! WHITE_BATH — bath validation: white integer-hash noise vs the old
! quasi-periodic sinusoid drive. 2 packed blocks x 96 free particles
! (NO forces), identical layout. Block A (1..96) = white, B (97..192)
! = sinusoid. TAMP = 0.02 both.
IMPLICIT NONE
PARAMETER INTEGER :: NP = 96, NTOT = 192, MAXFRAME = 20000
PARAMETER REAL :: DT = 0.01, DAMP = 0.9, TAMP = 0.02

STATIC REAL :: X(NTOT), Y(NTOT), Z(NTOT)
STATIC REAL :: VX(NTOT), VY(NTOT), VZ(NTOT)
STATIC REAL :: X0(NTOT), Y0(NTOT), Z0(NTOT)
STATIC INTEGER :: H
STATIC REAL :: NOISE, MSD, SP2
INTEGER :: I, FRAME

DO I = 1, NP
  X(I) := 10.0 + REAL(MOD(I - 1, 8)) * 3.0
  Y(I) := 10.0 + REAL(MOD((I - 1) / 8, 8)) * 3.0
  Z(I) := 10.0 + REAL((I - 1) / 64) * 3.0
  X0(I) := X(I)
  Y0(I) := Y(I)
  Z0(I) := Z(I)
  VX(I) := 0.0
  VY(I) := 0.0
  VZ(I) := 0.0
ENDDO
DO I = NP + 1, NTOT
  X(I) := X(I - NP)
  Y(I) := Y(I - NP)
  Z(I) := Z(I - NP)
  X0(I) := X(I)
  Y0(I) := Y(I)
  Z0(I) := Z(I)
  VX(I) := 0.0
  VY(I) := 0.0
  VZ(I) := 0.0
ENDDO

WRITE(*, "# WHITE_BATH cols: frame MSD_white MSD_sine SP2_white SP2_sine")

DO FRAME = 1, MAXFRAME
  DO I = 1, NP
    H := IEOR(I * 2654435761, FRAME * 40503)
    H := IEOR(H, ISHFT(H, -30))
    H := H * 6364136223846793005
    H := IEOR(H, ISHFT(H, -27))
    H := H * 6364136223846793005
    H := IEOR(H, ISHFT(H, -31))
    NOISE := (REAL(IAND(H, 65535)) / 65535.0 - 0.5) * TAMP * 2.449
    VX(I) := VX(I) + NOISE
    IF FRAME <= 2000 .AND. I = 1 THEN
      WRITE(*, "NZA %d %.6f") FRAME, NOISE
    ENDIF
    H := IEOR(H, ISHFT(H, -17))
    NOISE := (REAL(IAND(H, 65535)) / 65535.0 - 0.5) * TAMP * 2.449
    VY(I) := VY(I) + NOISE
    H := IEOR(H, ISHFT(H, -7))
    NOISE := (REAL(IAND(H, 65535)) / 65535.0 - 0.5) * TAMP * 2.449
    VZ(I) := VZ(I) + NOISE
  ENDDO
  DO I = NP + 1, NTOT
    VX(I) := VX(I) + TAMP * SIN((I+1)*7.3 + REAL(FRAME)*0.17)
    VY(I) := VY(I) + TAMP * COS((I+1)*5.7 + REAL(FRAME)*0.31)
    VZ(I) := VZ(I) + TAMP * SIN((I+1)*3.1 + REAL(FRAME)*0.09)
    IF FRAME <= 2000 .AND. I = NP + 1 THEN
      WRITE(*, "NZB %d %.6f") FRAME, TAMP * SIN((I+1)*7.3 + REAL(FRAME)*0.17)
    ENDIF
  ENDDO
  DO I = 1, NTOT
    VX(I) := VX(I) * DAMP
    VY(I) := VY(I) * DAMP
    VZ(I) := VZ(I) * DAMP
    X(I) := X(I) + VX(I) * DT
    Y(I) := Y(I) + VY(I) * DT
    Z(I) := Z(I) + VZ(I) * DT
  ENDDO
  IF MOD(FRAME, 50) = 0 THEN
    MSD := 0.0
    SP2 := 0.0
    DO I = 1, NP
      MSD := MSD + (X(I) - X0(I)) ** 2 + (Y(I) - Y0(I)) ** 2 + (Z(I) - Z0(I)) ** 2
      SP2 := SP2 + VX(I) ** 2 + VY(I) ** 2 + VZ(I) ** 2
    ENDDO
    WRITE(*, "BATH %d %.6f", FRAME, MSD / REAL(NP)
    MSD := 0.0
    SP2 := 0.0
    DO I = NP + 1, NTOT
      MSD := MSD + (X(I) - X0(I)) ** 2 + (Y(I) - Y0(I)) ** 2 + (Z(I) - Z0(I)) ** 2
      SP2 := SP2 + VX(I) ** 2 + VY(I) ** 2 + VZ(I) ** 2
    ENDDO
    WRITE(*, " %.6f %.6f %.6f") MSD / REAL(NP), SP2 / REAL(NP), SP2 / REAL(NP)
  ENDIF
ENDDO
WRITE(*, "# DONE")
STOP
"""

# NOTE: the two-block WRITE above is awkward in Ergo format strings;
# use single combined write instead (patched below in python).

BATH = BATH.replace("""    WRITE(*, "BATH %d %.6f", FRAME, MSD / REAL(NP)
    MSD := 0.0
    SP2 := 0.0
    DO I = NP + 1, NTOT
      MSD := MSD + (X(I) - X0(I)) ** 2 + (Y(I) - Y0(I)) ** 2 + (Z(I) - Z0(I)) ** 2
      SP2 := SP2 + VX(I) ** 2 + VY(I) ** 2 + VZ(I) ** 2
    ENDDO
    WRITE(*, " %.6f %.6f %.6f") MSD / REAL(NP), SP2 / REAL(NP), SP2 / REAL(NP)""",
"""    SP2 := SP2 / REAL(NP)
    MSD := MSD / REAL(NP)
    MSD := MSD + 0.0
    ENDDO
    WRITE(*, "BATH %d %.6f %.6f %.6f %.6f") FRAME, MSD, SP2, MSD, SP2""")

# The string surgery above is fragile; build the BATH body directly instead:
BATH = """! WHITE_BATH — bath validation: white integer-hash noise vs the old
! quasi-periodic sinusoid drive. 2 packed blocks x 96 free particles
! (NO forces), identical layout. A (1..96) = white, B (97..192) = sine.
IMPLICIT NONE
PARAMETER INTEGER :: NP = 96, NTOT = 192, MAXFRAME = 20000
PARAMETER REAL :: DT = 0.01, DAMP = 0.9, TAMP = 0.02

STATIC REAL :: X(NTOT), Y(NTOT), Z(NTOT)
STATIC REAL :: VX(NTOT), VY(NTOT), VZ(NTOT)
STATIC REAL :: X0(NTOT), Y0(NTOT), Z0(NTOT)
STATIC INTEGER :: H
STATIC REAL :: NOISE, MSDA, MSDB, SPA, SPB
INTEGER :: I, FRAME

DO I = 1, NP
  X(I) := 10.0 + REAL(MOD(I - 1, 8)) * 3.0
  Y(I) := 10.0 + REAL(MOD((I - 1) / 8, 8)) * 3.0
  Z(I) := 10.0 + REAL((I - 1) / 64) * 3.0
  X0(I) := X(I)
  Y0(I) := Y(I)
  Z0(I) := Z(I)
  VX(I) := 0.0
  VY(I) := 0.0
  VZ(I) := 0.0
ENDDO
DO I = NP + 1, NTOT
  X(I) := X(I - NP)
  Y(I) := Y(I - NP)
  Z(I) := Z(I - NP)
  X0(I) := X(I - NP)
  Y0(I) := Y(I - NP)
  Z0(I) := Z(I - NP)
  VX(I) := 0.0
  VY(I) := 0.0
  VZ(I) := 0.0
ENDDO

WRITE(*, "# WHITE_BATH cols: frame MSD_white MSD_sine SP2_white SP2_sine")

DO FRAME = 1, MAXFRAME
  DO I = 1, NP
    H := IEOR(I * 2654435761, FRAME * 40503)
    H := IEOR(H, ISHFT(H, -30))
    H := H * 6364136223846793005
    H := IEOR(H, ISHFT(H, -27))
    H := H * 6364136223846793005
    H := IEOR(H, ISHFT(H, -31))
    NOISE := (REAL(IAND(H, 65535)) / 65535.0 - 0.5) * TAMP * 2.449
    VX(I) := VX(I) + NOISE
    IF FRAME <= 2000 .AND. I = 1 THEN
      WRITE(*, "NZA %d %.6f") FRAME, NOISE
    ENDIF
    H := IEOR(H, ISHFT(H, -17))
    NOISE := (REAL(IAND(H, 65535)) / 65535.0 - 0.5) * TAMP * 2.449
    VY(I) := VY(I) + NOISE
    H := IEOR(H, ISHFT(H, -7))
    NOISE := (REAL(IAND(H, 65535)) / 65535.0 - 0.5) * TAMP * 2.449
    VZ(I) := VZ(I) + NOISE
  ENDDO
  DO I = NP + 1, NTOT
    VX(I) := VX(I) + TAMP * SIN((I+1)*7.3 + REAL(FRAME)*0.17)
    VY(I) := VY(I) + TAMP * COS((I+1)*5.7 + REAL(FRAME)*0.31)
    VZ(I) := VZ(I) + TAMP * SIN((I+1)*3.1 + REAL(FRAME)*0.09)
    IF FRAME <= 2000 .AND. I = NP + 1 THEN
      WRITE(*, "NZB %d %.6f") FRAME, TAMP * SIN((I+1)*7.3 + REAL(FRAME)*0.17)
    ENDIF
  ENDDO
  DO I = 1, NTOT
    VX(I) := VX(I) * DAMP
    VY(I) := VY(I) * DAMP
    VZ(I) := VZ(I) * DAMP
    X(I) := X(I) + VX(I) * DT
    Y(I) := Y(I) + VY(I) * DT
    Z(I) := Z(I) + VZ(I) * DT
  ENDDO
  IF MOD(FRAME, 50) = 0 THEN
    MSDA := 0.0
    SPA := 0.0
    DO I = 1, NP
      MSDA := MSDA + (X(I) - X0(I)) ** 2 + (Y(I) - Y0(I)) ** 2 + (Z(I) - Z0(I)) ** 2
      SPA := SPA + VX(I) ** 2 + VY(I) ** 2 + VZ(I) ** 2
    ENDDO
    MSDB := 0.0
    SPB := 0.0
    DO I = NP + 1, NTOT
      MSDB := MSDB + (X(I) - X0(I)) ** 2 + (Y(I) - Y0(I)) ** 2 + (Z(I) - Z0(I)) ** 2
      SPB := SPB + VX(I) ** 2 + VY(I) ** 2 + VZ(I) ** 2
    ENDDO
    WRITE(*, "BATH %d %.6f %.6f %.6f %.6f") &
      FRAME, MSDA / REAL(NP), MSDB / REAL(NP), SPA / REAL(NP), SPB / REAL(NP)
  ENDIF
ENDDO
WRITE(*, "# DONE")
STOP
"""

(OUT / "white_bath.ergo").write_text(BATH)
print("wrote white_bath.ergo")

WHITE_KICKS = """    ! Thermal kicks at the block's CONSTANT temperature — WHITE hash
    DO I = 1, NPB
      H := IEOR((OFF + I) * 2654435761, FRAME * 40503)
      H := IEOR(H, ISHFT(H, -30))
      H := H * 6364136223846793005
      H := IEOR(H, ISHFT(H, -27))
      H := H * 6364136223846793005
      H := IEOR(H, ISHFT(H, -31))
      RES_VX(OFF + I) := RES_VX(OFF + I) + TB(B) * 2.449 * (REAL(IAND(H, 65535)) / 65535.0 - 0.5)
      H := IEOR(H, ISHFT(H, -17))
      RES_VY(OFF + I) := RES_VY(OFF + I) + TB(B) * 2.449 * (REAL(IAND(H, 65535)) / 65535.0 - 0.5)
      H := IEOR(H, ISHFT(H, -7))
      RES_VZ(OFF + I) := RES_VZ(OFF + I) + TB(B) * 2.449 * (REAL(IAND(H, 65535)) / 65535.0 - 0.5)
    ENDDO"""

SINE_KICKS = """    ! Thermal kicks at the block's CONSTANT temperature
    DO I = 1, NPB
      RES_VX(OFF + I) := RES_VX(OFF + I) + TB(B) * SIN((I+1)*7.3 + REAL(FRAME)*0.17)
      RES_VY(OFF + I) := RES_VY(OFF + I) + TB(B) * COS((I+1)*5.7 + REAL(FRAME)*0.31)
      RES_VZ(OFF + I) := RES_VZ(OFF + I) + TB(B) * SIN((I+1)*3.1 + REAL(FRAME)*0.09)
    ENDDO"""

for src_name, out_name in [("condensate_hot48.ergo", "white_hot48.ergo"),
                           ("condensate_hot96.ergo", "white_hot96.ergo")]:
    s = (OUT / src_name).read_text()
    assert SINE_KICKS in s, src_name
    s = s.replace(SINE_KICKS, WHITE_KICKS, 1)
    s = s.replace("STATIC INTEGER :: CM(NCH, NCH), LAB(NCH), CNT(NCH)",
                  "STATIC INTEGER :: CM(NCH, NCH), LAB(NCH), CNT(NCH)\nSTATIC INTEGER :: H")
    s = s.replace("! CONDENSATE — 8 constant-temperature blocks",
                  "! CONDENSATE_WHITE — 8 constant-temperature blocks (white hash bath)")
    (OUT / out_name).write_text(s)
    print(f"wrote {out_name}")
