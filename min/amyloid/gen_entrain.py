#!/usr/bin/env python3
"""gen_entrain.py — longer anneal + entrainment pulse sweep on the tax run.

Base: tax_0p5_off1.ergo (TAX=0.5, off-by-one start, the run that began
correcting and stalled at ~25%). Changes:
  - MAXFRAME 12000 -> 50000, quench 9600 -> 40000 (0.8x, standard
    recipe; documented: without moving the quench, frames past 9600
    have zero noise and "longer anneal" would be meaningless)
  - optional backbone pulse (mode-1 standing wave across the packed
    28-residue vector, A=0.05, applied to C-alpha velocities; amide
    beads follow through their tethers)
Frequency sweep omega (rad/frame): 0.0005, 0.002 (validated rescue
frequency), 0.005, 0.02, and "schumann" = 7.83 rad/frame.
SCHUMANN MAPPING (documented): the sim has no physical time unit; the
labeled point takes the number literally in the sim's omega units.
At DT=0.01 the period is 2*pi/7.83 = 0.80 frames < 1 frame, i.e.
sub-Nyquist — the sine aliases into a deterministic noise hash.
There is no established physical coupling of Schumann resonances to
molecular dynamics; this is one labeled point in the sweep.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = (ROOT / "min" / "amyloid" / "tax_0p5_off1.ergo").read_text()

PULSE_DECLS = """PARAMETER REAL :: PULSE_AMP = 0.05
PARAMETER REAL :: PULSE_OMEGA = __OMG__
"""

PULSE_KICK = """  ! Entrainment pulse: mode-1 standing wave across the packed vector
  DO I = 1, NTOT
    RES_VX(I) := RES_VX(I) + PULSE_AMP * SIN(PULSE_OMEGA * REAL(FRAME)) * SIN(3.14159265 * REAL(I) / REAL(NTOT + 1))
    RES_VY(I) := RES_VY(I) + PULSE_AMP * SIN(PULSE_OMEGA * REAL(FRAME) + 2.0943951) * SIN(3.14159265 * REAL(I) / REAL(NTOT + 1))
    RES_VZ(I) := RES_VZ(I) + PULSE_AMP * SIN(PULSE_OMEGA * REAL(FRAME) + 4.1887902) * SIN(3.14159265 * REAL(I) / REAL(NTOT + 1))
  ENDDO

  ! Steric repulsion (same-chain |i-j| >= 4 or any inter-chain pair)"""


def build(out_name, omega=None):
    s = BASE
    s = s.replace("PARAMETER INTEGER :: MAXFRAME = 12000",
                  "PARAMETER INTEGER :: MAXFRAME = 50000")
    s = s.replace("IF FRAME > 9600 THEN", "IF FRAME > 40000 THEN")
    s = s.replace("after frame 9600", "after frame 40000")
    if omega is not None:
        s = s.replace("STATIC REAL :: BSCORE, SCORE, DEFF, EBOND",
                      "STATIC REAL :: BSCORE, SCORE, DEFF, EBOND\n"
                      + PULSE_DECLS.replace("__OMG__", omega))
        anchor = "  ! Steric repulsion (same-chain |i-j| >= 4 or any inter-chain pair)"
        assert anchor in s
        s = s.replace(anchor, PULSE_KICK, 1)
    s = s.replace("! AMYLOID_TAX0p5_OFF1", f"! AMYLOID_ENTRAIN omega={omega}")
    (ROOT / "min" / "amyloid" / out_name).write_text(s)
    print(f"wrote {out_name} (omega={omega})")


build("entrain_anneal.ergo", None)
build("entrain_w0005.ergo", "0.0005")
build("entrain_w002.ergo", "0.002")
build("entrain_w005.ergo", "0.005")
build("entrain_w02.ergo", "0.02")
build("entrain_schumann.ergo", "7.83")
