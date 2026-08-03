#!/usr/bin/env python3
"""gen_heatpulse.py — sustained-heat and ultrasonic-pulse variants on 1SNO.

Task 1 (sustained heat): UPDATE_THERMAL's post-cycle floor becomes
HEAT_SUS for FRAME <= 24000 (then 0.001 to quench 38400). Builds:
  heat_010_ctl.ergo  (from packed_1sno_gate.ergo: no swaps, TMUL=1)
  heat_005_swap.ergo / heat_010_swap.ergo / heat_020_swap.ergo
  (from packed_1sno_temper.ergo: TMUL ladder + swaps/500 full window)

Task 2 (ultrasonic pulse): periodic velocity kick added in block loop A
after the thermal impulses:
  kick_x = PULSE_AMP * sin(PULSE_OMEGA*FRAME) * sin(pi*I/(NRES+1))
  (y, z phase-shifted by 2pi/3, 4pi/3). Spatial shape = mode-1 standing
  wave along the backbone (peaks at I=68, covering domain 1 (1-98) and
  near-zero at the C-terminus — chosen because the seed-3.0 trap is a
  domain-1/register error; a global AC kick is translation-invariant
  under Kabsch and would be a null control). Factorial:
  OMEGA in {0.002 (period 3142), 0.017 (370), 0.17 (37, the noise-hash
  scale)} x AMP in {0.002, 0.01, 0.05} (straddling the 0.001 noise
  floor; peak-cycle noise is 1.0). On the no-swap baseline schedule.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"

GATE = (PM / "packed_1sno_gate.ergo").read_text()
TEMPER = (PM / "packed_1sno_temper.ergo").read_text()

THERMAL_OLD = """  ELSE
    THERMAL_CURRENT := HEAT_START
  ENDIF"""


def sustained(src, heat_sus):
    assert THERMAL_OLD in src
    out = src.replace(THERMAL_OLD, f"""  ELSE
    IF FRAME <= 24000 THEN
      THERMAL_CURRENT := {heat_sus}
    ELSE
      THERMAL_CURRENT := HEAT_START
    ENDIF
  ENDIF""")
    out = out.replace("! PACKED_1SNO", f"! PACKED_1SNO HEAT_SUS={heat_sus}", 1)
    return out


# Task 1 builds
(PM / "heat_010_ctl.ergo").write_text(sustained(GATE, "0.01"))
(PM / "heat_005_swap.ergo").write_text(sustained(TEMPER, "0.005"))
(PM / "heat_010_swap.ergo").write_text(sustained(TEMPER, "0.01"))
(PM / "heat_020_swap.ergo").write_text(sustained(TEMPER, "0.02"))
print("wrote heat_010_ctl, heat_005_swap, heat_010_swap, heat_020_swap")

# Task 2 builds
PULSE_DECLS = """PARAMETER REAL :: PULSE_AMP = __AMP__
PARAMETER REAL :: PULSE_OMEGA = __OMG__
"""
PULSE_KICK = """    ! Ultrasonic pulse: mode-1 standing wave along the backbone,
    ! sinusoidal velocity kick, axes phase-shifted by 2pi/3
    DO I = 1, NRES
      RES_VX(OFF + I) := RES_VX(OFF + I) + PULSE_AMP * SIN(PULSE_OMEGA * REAL(FRAME)) * SIN(3.14159265 * REAL(I) / REAL(NRES + 1))
      RES_VY(OFF + I) := RES_VY(OFF + I) + PULSE_AMP * SIN(PULSE_OMEGA * REAL(FRAME) + 2.0943951) * SIN(3.14159265 * REAL(I) / REAL(NRES + 1))
      RES_VZ(OFF + I) := RES_VZ(OFF + I) + PULSE_AMP * SIN(PULSE_OMEGA * REAL(FRAME) + 4.1887902) * SIN(3.14159265 * REAL(I) / REAL(NRES + 1))
    ENDDO

    ! Steric repulsion (|i-j| >= 4, not H-bonded)"""

KICK_ANCHOR = "    ! Steric repulsion (|i-j| >= 4, not H-bonded)"
DECL_ANCHOR = "! ── Per-block seeds and results ──────────────────────────────"

OMEGAS = {"w002": "0.002", "w017": "0.017", "w170": "0.17"}
AMPS = {"a002": "0.002", "a010": "0.01", "a050": "0.05"}

for wk, wv in OMEGAS.items():
    for ak, av in AMPS.items():
        out = GATE
        assert DECL_ANCHOR in out and KICK_ANCHOR in out
        out = out.replace(DECL_ANCHOR,
                          PULSE_DECLS.replace("__AMP__", av).replace("__OMG__", wv)
                          + DECL_ANCHOR)
        out = out.replace(KICK_ANCHOR, PULSE_KICK, 1)
        out = out.replace("! PACKED_1SNO", f"! PACKED_1SNO PULSE amp={av} omega={wv}", 1)
        name = f"pulse_{wk}_{ak}.ergo"
        (PM / name).write_text(out)
        print(f"wrote {name}")
