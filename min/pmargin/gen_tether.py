#!/usr/bin/env python3
"""gen_tether.py — tether-repair probe variants for the 1SNO fragmented trap.

Base: packed_1sno_struct.ergo (validated packed sweep + structure dump).

DESIGN A (global long-range tether): every backbone bond gets a harmonic
continuation past DCUT=4.0 (where the Morse plateau has ~zero restoring
force):  E_bond = D_e(1-g)^2 + K_LR (D-DCUT)^2  for D > DCUT.
Force added: FM += -2 K_LR (D-DCUT) FORCE_SCALE (attractive), same form
and magnitude scale as the sim's Go contacts (NATIVE_K=1.0), so the
bracket 0.05..1.0 is dynamically precedented/stable.

DESIGN B (targeted junction reinforcement): the same continuation, but
ONLY at the broken junctions found in dihedral_1sno_check.md
(bonds 8, 22, 24, 32, 72, 90, 91; bond i = residues i..i+1). Bond 1 is
EXCLUDED (documented): the N-terminal dangle is genuine physical
flexibility seen in 6/8 blocks, not the fragmentation failure — the
named mid-chain clusters are 22-24-25 and 90-91-92.

Emits: tether_a_k{005,02,05,10}.ergo, tether_b_k{05,10}.ergo
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = (ROOT / "min" / "pmargin" / "packed_1sno_struct.ergo").read_text()

DECL_ANCHOR = "STATIC INTEGER :: BOND_B(NBOND)"
FORCE_ANCHOR = """      E := EXP(-MORSE_A * (D - BACKBONE_R0))
      FM := -2.0 * BACKBONE_D * MORSE_A * (1.0 - E) * E * FORCE_SCALE
"""
FORCE_PATCH = """      E := EXP(-MORSE_A * (D - BACKBONE_R0))
      FM := -2.0 * BACKBONE_D * MORSE_A * (1.0 - E) * E * FORCE_SCALE
      IF D > 4.0 .AND. BOND_KLR(K) > 0.0 THEN
        FM := FM - 2.0 * BOND_KLR(K) * (D - 4.0) * FORCE_SCALE
      ENDIF
"""
INIT_ANCHOR = """      K := (B - 1) * 135 + I
      BOND_A(K) := (B - 1) * NRES + I
      BOND_B(K) := (B - 1) * NRES + I + 1
    ENDDO"""

JUNCTIONS = (8, 22, 24, 32, 72, 90, 91)

def emit(name, default_klr, junction_klr=None, note=""):
    t = BASE
    assert DECL_ANCHOR in t and FORCE_ANCHOR in t and INIT_ANCHOR in t
    t = t.replace(DECL_ANCHOR, DECL_ANCHOR + "\nSTATIC REAL :: BOND_KLR(NBOND)", 1)
    t = t.replace(FORCE_ANCHOR, FORCE_PATCH, 1)
    init = INIT_ANCHOR.replace("    ENDDO",
                               f"      BOND_KLR(K) := {default_klr:.4f}\n    ENDDO")
    if junction_klr is not None:
        sets = "\n".join(
            f"    BOND_KLR((B - 1) * 135 + {j}) := {junction_klr:.4f}" for j in JUNCTIONS)
        init += f"""
    ! targeted junction reinforcement: bonds {JUNCTIONS} (bond 1 excluded —
    ! genuine terminal flexibility, see tether_check.md); inside the outer B loop
{sets}"""
    t = t.replace(INIT_ANCHOR, init, 1)
    t = t.replace("! PACKED_1SNO — 8 folding trajectories (seeds 0.0..7.0) in ONE program.",
                  f"! PACKED_1SNO — 8 folding trajectories (seeds 0.0..7.0) in ONE program.\n"
                  f"! TETHER-REPAIR variant {name}: {note} (gen_tether.py)", 1)
    out = ROOT / "min" / "pmargin" / f"{name}.ergo"
    out.write_text(t)
    print(f"wrote {out}")

for tag, k in (("005", 0.05), ("02", 0.2), ("05", 0.5), ("10", 1.0)):
    emit(f"tether_a_k{tag}", k, None,
         f"DESIGN A global long-range tether, K_LR={k} at every bond past D=4.0")
for tag, k in (("05", 0.5), ("10", 1.0)):
    emit(f"tether_b_k{tag}", 0.0, k,
         f"DESIGN B targeted junction reinforcement, K_LR={k} at bonds 8,22,24,32,72,90,91 only")
