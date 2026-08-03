#!/usr/bin/env python3
"""gen_sdrd_seq.py — sequential co-translational SdrD assembly (white bath).

One program, all 556 residues, domain-staged activation (the amyloid
template-addition pattern, in one run so state carries over):
  stage 1 (frames 1-12000):    A2 folds alone (rest frozen in coil)
  stage 2 (frames 12001-24000): + A3 denatured; A2 = damped template
  stage 3 (frames 24001-36000): + B1; A2/A3 = template
  stage 4 (frames 36001-48000): + B2; A2/A3/B1 = template
Freezing: domains not yet activated get VDAMP=0 and no kicks (velocity
zeroed every frame -> positions fixed). Template domains (earlier
stages) get VDAMP=0.5 (amyloid damped-template pattern). The domain
folding in the current stage gets 0.9. Thermal schedule unchanged
(heat cycles 1-1200, floor 0.001, quench 38400 — documented: stage 1
gets the hot cycles; later stages fold at the floor, matching the
domain-sweep regime).

CURATED domain boundaries (UniProt/Pfam curation per the task; the
contact-minimum detection was within 2-7 residues):
  A2 = construct 1-152 (res 243-394, contact-minimum approx)
  A3 = 153-325 (res 395-568; A region ends 568)
  B1 = 326-437 (res 569-680, CNA-B1 CURATED)
  B2 = 438-555 (res 681-791, CNA-B2 CURATED; res 792-798 = tail,
       folds with B2, unscored)
Per-domain RMSD uses these ranges; stage-end SDOM rows every 12000
frames for all 8 blocks. Base: sdrd_white_full.ergo (white hash bath).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"
SRC = PM / "sdrd_white_full.ergo"
OUT = PM / "sdrd_seq_full.ergo"

s = SRC.read_text()

# 1. declarations
DECL_ANCHOR = "STATIC REAL :: RMSD_B(8)\nSTATIC INTEGER :: H"
assert DECL_ANCHOR in s
s = s.replace(DECL_ANCHOR, DECL_ANCHOR + """
PARAMETER INTEGER :: STAGE_FR = 12000
STATIC REAL :: VD
STATIC INTEGER :: DOMI, CURST""", 1)

# 2. domain index helper injected at the top of block loop A (kicks) and damp
DOMI_CODE = """      DOMI := 1
      IF I > 152 THEN
        DOMI := 2
      ENDIF
      IF I > 325 THEN
        DOMI := 3
      ENDIF
      IF I > 437 THEN
        DOMI := 4
      ENDIF"""

# 3. freeze-gate the kicks
OLD_KICKS_HEAD = """    ! Thermal impulses (velocity kicks, LOCAL index) — WHITE hash bath
    DO I = 1, NRES
      H := IEOR((OFF + I) * 2654435761, FRAME * 40503)"""
NEW_KICKS_HEAD = """    ! Thermal impulses (velocity kicks, LOCAL index) — WHITE hash bath,
    ! domain-staged: domains activate at FRAME >= (DOMI-1)*STAGE_FR
    DO I = 1, NRES
""" + DOMI_CODE + """
      IF FRAME >= (DOMI - 1) * STAGE_FR THEN
      H := IEOR((OFF + I) * 2654435761, FRAME * 40503)"""
assert OLD_KICKS_HEAD in s
s = s.replace(OLD_KICKS_HEAD, NEW_KICKS_HEAD, 1)

KICKS_TAIL = """      RES_VZ(OFF + I) := RES_VZ(OFF + I) + THERMAL_CURRENT * 2.449 * (REAL(IAND(H, 65535)) / 65535.0 - 0.5)
    ENDDO"""
assert KICKS_TAIL in s
s = s.replace(KICKS_TAIL, """      RES_VZ(OFF + I) := RES_VZ(OFF + I) + THERMAL_CURRENT * 2.449 * (REAL(IAND(H, 65535)) / 65535.0 - 0.5)
      ENDIF
    ENDDO""", 1)

# 4. staged damping
OLD_DAMP = """    ! Velocity damping
    DO I = 1, NRES
      RES_VX(OFF + I) := RES_VX(OFF + I) * VELOCITY_DAMP
      RES_VY(OFF + I) := RES_VY(OFF + I) * VELOCITY_DAMP
      RES_VZ(OFF + I) := RES_VZ(OFF + I) * VELOCITY_DAMP
    ENDDO"""
NEW_DAMP = """    ! Velocity damping (domain-staged: frozen VD=0 / template VD=0.5 /
    ! current-stage VD=0.9; CURST = current stage index)
    DO I = 1, NRES
""" + DOMI_CODE + """
      CURST := INT(REAL(FRAME - 1) / REAL(STAGE_FR)) + 1
      VD := 0.9
      IF DOMI > CURST THEN
        VD := 0.0
      ENDIF
      IF DOMI < CURST THEN
        VD := 0.5
      ENDIF
      RES_VX(OFF + I) := RES_VX(OFF + I) * VD
      RES_VY(OFF + I) := RES_VY(OFF + I) * VD
      RES_VZ(OFF + I) := RES_VZ(OFF + I) * VD
    ENDDO"""
assert OLD_DAMP in s
s = s.replace(OLD_DAMP, NEW_DAMP, 1)

# 5. stage-end SDOM rows every STAGE_FR frames (all blocks)
OLD_TRACE = """  ! Per-frame RMSD trace for blocks 1, 2, 5 every 100 frames
  IF MOD(FRAME, 500) = 0 THEN
    DO B = 1, NBLK
      IF B = 1 .OR. B = 2 .OR. B = 5 THEN
        OFF := (B - 1) * NRES
        CALL COMPUTE_RMSD(OFF)
        WRITE(*, "TRACE %d %.1f %d %.4f") B, SEED_TAB(B), FRAME, RMSD_NATIVE
      ENDIF
    ENDDO
  ENDIF"""
NEW_TRACE = """  ! Stage-end per-domain RMSD for all blocks (curated boundaries)
  IF MOD(FRAME, STAGE_FR) = 0 THEN
    DO B = 1, NBLK
      OFF := (B - 1) * NRES
      CALL COMPUTE_RMSD(OFF)
      RMSD_B(B) := RMSD_NATIVE
      CALL COMPUTE_RMSD_RANGE(OFF, 1, 152, 152)
      RMSD_D1(B) := RMSD_NATIVE
      CALL COMPUTE_RMSD_RANGE(OFF, 153, 325, 173)
      RMSD_D2(B) := RMSD_NATIVE
      CALL COMPUTE_RMSD_RANGE(OFF, 326, 437, 112)
      RMSD_D3(B) := RMSD_NATIVE
      CALL COMPUTE_RMSD_RANGE(OFF, 438, 555, 118)
      RMSD_D4(B) := RMSD_NATIVE
      WRITE(*, "SDOM %d %d %.1f %.4f %.4f %.4f %.4f %.4f") &
        FRAME, B, SEED_TAB(B), RMSD_B(B), RMSD_D1(B), RMSD_D2(B), RMSD_D3(B), RMSD_D4(B)
    ENDDO
  ENDIF"""
assert OLD_TRACE in s
s = s.replace(OLD_TRACE, NEW_TRACE, 1)

# 6. curated ranges in the FINAL block
s = s.replace("CALL COMPUTE_RMSD_RANGE(OFF, 153, 320, 168)",
              "CALL COMPUTE_RMSD_RANGE(OFF, 153, 325, 173)", 1)
s = s.replace("CALL COMPUTE_RMSD_RANGE(OFF, 321, 440, 120)",
              "CALL COMPUTE_RMSD_RANGE(OFF, 326, 437, 112)", 1)
s = s.replace("CALL COMPUTE_RMSD_RANGE(OFF, 441, 556, 116)",
              "CALL COMPUTE_RMSD_RANGE(OFF, 438, 555, 118)", 1)

# 7. header + output header
s = s.replace("! PACKED_SDRD_FULL_WHITE",
              "! PACKED_SDRD_SEQ_WHITE — sequential co-translational assembly (domain-staged)")

OUT.write_text(s)
print(f"wrote {OUT} ({len(s.splitlines())} lines)")
