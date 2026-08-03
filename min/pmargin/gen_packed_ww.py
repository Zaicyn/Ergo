#!/usr/bin/env python3
"""gen_packed_ww.py — packed 8-seed sweep + tempering for PIN1 WW domain.

Same machinery as gen_packed_1sno.py, WW sizes/recipe
(TRANSFERABILITY.md: HB_CAP=0, TORSK=0.2, MAXFRAME=24000, quench 19200,
register torsions from 1200; source tests/waveform_ww_v2.ergo, NREG=78).
Single domain — no per-domain RMSD. Oracle: tests/waveform_ww_v2.out
final rmsd 0.8363 raw = 2.10 A at 2.506 A/model-unit (mean_ca_ca 3.809).

Outputs: packed_ww.ergo (baseline), packed_ww_temper.ergo (SWAP_EVERY=500),
packed_ww_gate.ergo (SWAP_EVERY=0).
"""

import re
from pathlib import Path

import gen_packed_bba5 as G  # re-emits BBA5 files (deterministic); reuse strings

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "tests" / "waveform_ww_v2.ergo"

NRES = 34
NBLK = 8
NPTS = NRES * NBLK          # 272
NBOND = (NRES - 1) * NBLK   # 264
NANG = (NRES - 2) * NBLK    # 256
NTORS = (NRES - 3) * NBLK   # 248

src = SRC.read_text()

m = re.search(r"(  ! Sequence design.*?)\nEND\n", src, flags=re.DOTALL)
assert m
seq_params = m.group(1).rstrip()
assert seq_params.endswith("RETURN")
seq_params = seq_params[: -len("RETURN")].rstrip()

m = re.search(r"SUBROUTINE INIT_NATIVE\(\)\n(.*?)\nEND\n", src, flags=re.DOTALL)
assert m
init_native_body = m.group(1).rstrip()

# ── template with WW substitutions ──────────────────────────────────────
t = G.TEMPLATE
t = t.replace("PARAMETER INTEGER :: NRES = 23", f"PARAMETER INTEGER :: NRES = {NRES}")
t = t.replace("PARAMETER INTEGER :: NPTS = 184", f"PARAMETER INTEGER :: NPTS = {NPTS}")
t = t.replace("184, 184", f"{NPTS}, {NPTS}")
t = t.replace("(184)", f"({NPTS})")
for nm in ("RES_ANGK", "RES_ANGT0", "RES_TORSK", "RES_TORSP0", "RES_HYDRO",
           "NATIVE_X", "NATIVE_Y", "NATIVE_Z"):
    t = t.replace(f"{nm}(23)", f"{nm}({NRES})")
t = t.replace("(23, 23)", f"({NRES}, {NRES})")
t = t.replace("PARAMETER INTEGER :: MAXFRAME = 48000",
              "PARAMETER INTEGER :: MAXFRAME = 24000")
t = t.replace("PARAMETER INTEGER :: MAXREG = 6", "PARAMETER INTEGER :: MAXREG = 78")
t = t.replace("PARAMETER INTEGER :: NREG = 6", "PARAMETER INTEGER :: NREG = 78")
t = t.replace("PARAMETER REAL :: NATIVE_CUTOFF = 2.522943",
              "PARAMETER REAL :: NATIVE_CUTOFF = 2.593795")
t = t.replace("IF FRAME > 12000 THEN", "IF FRAME > 19200 THEN")
t = t.replace("after frame 12000", "after frame 19200")
t = t.replace("! PACKED_BBA5 — 8 folding trajectories (seeds 0.0..7.0) in ONE program.",
              "! PACKED_WW — 8 folding trajectories (seeds 0.0..7.0) in ONE program.\n"
              "! PIN1 WW domain, 34 residues, single domain.")
t = t.replace("tests/waveform_bba5_seed_0.0.ergo", "tests/waveform_ww_v2.ergo")
t = t.replace('WRITE(*, "# PACKED_BBA5 NBLK=8 NRES=23 MAXFRAME=48000 QUENCH=12000")',
              'WRITE(*, "# PACKED_WW NBLK=8 NRES=34 MAXFRAME=24000 QUENCH=19200")')
t = t.replace('WRITE(*, "# TRACE cols: block seed frame rmsd_native (blocks 1,2,5 every 100)")',
              'WRITE(*, "# TRACE cols: block seed frame rmsd_native (blocks 1,2,5 every 200)")')
t = t.replace("IF MOD(FRAME, 100) = 0 THEN", "IF MOD(FRAME, 200) = 0 THEN")

t = t.replace("__SEQ_PARAMS__", seq_params).replace("__INIT_NATIVE__", init_native_body)

# ── v2 packed-force-kernel surgery (WW sizes) ───────────────────────────
DECL_ANCHOR = "! ── Per-block seeds and results ──────────────────────────────"
DECL_EXTRA = f"""! ── Packed force-kernel tables (v2): block offsets baked in ─────
PARAMETER INTEGER :: NBOND = {NBOND}
PARAMETER INTEGER :: NANG = {NANG}
PARAMETER INTEGER :: NTORS = {NTORS}
STATIC INTEGER :: BOND_A(NBOND)
STATIC INTEGER :: BOND_B(NBOND)
STATIC INTEGER :: ANG_A(NANG)
STATIC INTEGER :: ANG_B(NANG)
STATIC INTEGER :: ANG_C(NANG)
STATIC REAL :: ANGK_P(NANG)
STATIC REAL :: ANGT0_P(NANG)
STATIC INTEGER :: TORS_A(NTORS)
STATIC INTEGER :: TORS_B(NTORS)
STATIC INTEGER :: TORS_C(NTORS)
STATIC INTEGER :: TORS_D(NTORS)
STATIC REAL :: TORSK_P(NTORS)
STATIC REAL :: TORSP0_P(NTORS)
STATIC INTEGER :: I1, I2, I3, I4

"""
assert DECL_ANCHOR in t
t = t.replace(DECL_ANCHOR, DECL_EXTRA + DECL_ANCHOR)

COIL_ANCHOR = """ENDDO

WRITE(*, "# PACKED_WW NBLK=8 NRES=34 MAXFRAME=24000 QUENCH=19200")"""
assert COIL_ANCHOR in t
t = t.replace(COIL_ANCHOR, """ENDDO
CALL INIT_TABLES()

WRITE(*, "# PACKED_WW NBLK=8 NRES=34 MAXFRAME=24000 QUENCH=19200")""")

M_MORSE = "    ! Morse bonds (backbone)"
M_ANGLE = "    ! Angle bending (backbone angles)"
M_TORS = "    ! Torsion (dihedral) angles"
M_REG = "    ! Cross-strand register torsions"
i_m = t.index(M_MORSE)
i_a = t.index(M_ANGLE)
i_t = t.index(M_TORS)
i_r = t.index(M_REG)
sec_morse, sec_angle, sec_tors = t[i_m:i_a], t[i_a:i_t], t[i_t:i_r]

dedent2 = G.dedent2
rep_indices = G.rep_indices

pk_morse = dedent2(sec_morse).replace(
    "  DO I = 1, NRES-1",
    "  DO K = 1, NBOND\n    I1 := BOND_A(K)\n    I2 := BOND_B(K)")
pk_morse = rep_indices(pk_morse, [("OFF + I+1", "I2"), ("OFF + I", "I1")])

pk_angle = dedent2(sec_angle).replace(
    "  DO I = 2, NRES-1",
    "  DO K = 1, NANG\n    I1 := ANG_A(K)\n    I2 := ANG_B(K)\n    I3 := ANG_C(K)")
pk_angle = rep_indices(pk_angle, [("OFF + I-1", "I1"), ("OFF + I+1", "I3"),
                                  ("OFF + I", "I2")])
pk_angle = pk_angle.replace("RES_ANGK(I)", "ANGK_P(K)")
pk_angle = pk_angle.replace("RES_ANGT0(I)", "ANGT0_P(K)")

pk_tors = dedent2(sec_tors).replace(
    "  DO I = 2, NRES-2",
    "  DO K = 1, NTORS\n    I1 := TORS_A(K)\n    I2 := TORS_B(K)\n"
    "    I3 := TORS_C(K)\n    I4 := TORS_D(K)")
pk_tors = rep_indices(pk_tors, [("OFF + I-1", "I1"), ("OFF + I+1", "I3"),
                                ("OFF + I+2", "I4"), ("OFF + I", "I2")])
pk_tors = pk_tors.replace("RES_TORSK(I)", "TORSK_P(K)")
pk_tors = pk_tors.replace("RES_TORSP0(I)", "TORSP0_P(K)")

t = (t[:i_m]
     + "  ENDDO\n\n"
     + "  ! ── packed force kernels: ONE loop per force type per frame ──\n"
     + pk_morse + "\n" + pk_angle + "\n" + pk_tors + "\n"
     + "  DO B = 1, NBLK\n    OFF := (B - 1) * NRES\n\n"
     + t[i_r:])

INIT_TABLES = f"""! ════════════════════════════════════════════════════════════
! INIT_TABLES: build block-aware packed index tables (offsets baked)
! and packed parameter tables from the shared per-residue params
! ════════════════════════════════════════════════════════════

SUBROUTINE INIT_TABLES()
  INTEGER :: B, I, K
  DO B = 1, NBLK
    DO I = 1, NRES - 1
      K := (B - 1) * {NRES-1} + I
      BOND_A(K) := (B - 1) * NRES + I
      BOND_B(K) := (B - 1) * NRES + I + 1
    ENDDO
    DO I = 2, NRES - 1
      K := (B - 1) * {NRES-2} + (I - 1)
      ANG_A(K) := (B - 1) * NRES + I - 1
      ANG_B(K) := (B - 1) * NRES + I
      ANG_C(K) := (B - 1) * NRES + I + 1
      ANGK_P(K) := RES_ANGK(I)
      ANGT0_P(K) := RES_ANGT0(I)
    ENDDO
    DO I = 2, NRES - 2
      K := (B - 1) * {NRES-3} + (I - 1)
      TORS_A(K) := (B - 1) * NRES + I - 1
      TORS_B(K) := (B - 1) * NRES + I
      TORS_C(K) := (B - 1) * NRES + I + 1
      TORS_D(K) := (B - 1) * NRES + I + 2
      TORSK_P(K) := RES_TORSK(I)
      TORSP0_P(K) := RES_TORSP0(I)
    ENDDO
  ENDDO
END

"""
UT_ANCHOR = ("! ════════════════════════════════════════════════════════════\n"
             "! UPDATE_THERMAL")
assert UT_ANCHOR in t
t = t.replace(UT_ANCHOR, INIT_TABLES + UT_ANCHOR)

OUT = ROOT / "min" / "pmargin" / "packed_ww.ergo"
OUT.write_text(t)
print(f"wrote {OUT} ({len(t.splitlines())} lines)")


def make_temper(src_text, swap_every):
    x = src_text
    anchor = "STATIC INTEGER :: I1, I2, I3, I4\n"
    assert anchor in x
    x = x.replace(anchor, anchor + G.TEMPER_DECLS.replace("__SWAP_EVERY__", str(swap_every)))
    assert "CALL INIT_TABLES()\n" in x
    x = x.replace("CALL INIT_TABLES()\n", G.LADDER_INIT + "\n", 1)
    x = x.replace("TEMP_X := THERMAL_CURRENT * PHASE_NOISE_SCALE",
                  "TEMP_X := THERMAL_CURRENT * TMUL(B) * PHASE_NOISE_SCALE")
    x = x.replace("+ THERMAL_CURRENT * SIN(", "+ THERMAL_CURRENT * TMUL(B) * SIN(")
    x = x.replace("+ THERMAL_CURRENT * COS(", "+ THERMAL_CURRENT * TMUL(B) * COS(")
    x = x.replace("  CALL UPDATE_THERMAL(FRAME)\n",
                  "  CALL UPDATE_THERMAL(FRAME)\n" + G.SWAP_BLOCK, 1)
    assert G.RMSD_ANCHOR in x
    x = x.replace(G.RMSD_ANCHOR, G.COMPUTE_ENERGY + G.RMSD_ANCHOR, 1)
    x = x.replace('WRITE(*, "# DONE")', G.SWAP_STATS, 1)
    x = x.replace("# PACKED_WW NBLK=8", f"# PACKED_WW_TEMPER SWAP_EVERY={swap_every} NBLK=8")
    return x


temper = make_temper(t, 500)
OUTT = ROOT / "min" / "pmargin" / "packed_ww_temper.ergo"
OUTT.write_text(temper)
print(f"wrote {OUTT} ({len(temper.splitlines())} lines)")

gate = make_temper(t, 0)
OUTG = ROOT / "min" / "pmargin" / "packed_ww_gate.ergo"
OUTG.write_text(gate)
print(f"wrote {OUTG} ({len(gate.splitlines())} lines)")


# ══════════════════════════════════════════════════════════════════════
# TASK 2 — hot-phase swap-window variants on 1SNO. Everything identical
# to packed_1sno_temper.ergo except swaps are allowed only while
# FRAME <= SWAP_UNTIL, plus one hotter-ladder variant (LADDER_MAX=3.0)
# at the full window.
# ══════════════════════════════════════════════════════════════════════

snase_temper = (ROOT / "min" / "pmargin" / "packed_1sno_temper.ergo").read_text()
SWAP_IF = "IF SWAP_EVERY > 0 .AND. MOD(FRAME, SWAP_EVERY) = 0 THEN"
assert SWAP_IF in snase_temper

for window in (1200, 6000, 12000, 24000, 38400):
    v = snase_temper.replace(
        SWAP_IF,
        f"IF SWAP_EVERY > 0 .AND. MOD(FRAME, SWAP_EVERY) = 0 .AND. FRAME <= {window} THEN")
    v = v.replace("# PACKED_1SNO_TEMPER SWAP_EVERY=500",
                  f"# PACKED_1SNO_HOTPHASE SWAP_EVERY=500 SWAP_UNTIL={window}")
    out = ROOT / "min" / "pmargin" / f"hotphase_w{window}.ergo"
    out.write_text(v)
    print(f"wrote {out}")

v = snase_temper.replace(
    SWAP_IF,
    "IF SWAP_EVERY > 0 .AND. MOD(FRAME, SWAP_EVERY) = 0 .AND. FRAME <= 38400 THEN")
v = v.replace("PARAMETER REAL :: LADDER_MAX = 2.0",
              "PARAMETER REAL :: LADDER_MAX = 3.0")
v = v.replace("# PACKED_1SNO_TEMPER SWAP_EVERY=500",
              "# PACKED_1SNO_HOTPHASE SWAP_EVERY=500 SWAP_UNTIL=38400 LADDER_MAX=3.0")
out = ROOT / "min" / "pmargin" / "hotphase_w38400_hot3.ergo"
out.write_text(v)
print(f"wrote {out}")
