#!/usr/bin/env python3
"""gen_10ps.py — generalized packed-sweep emitter (SdrD 10PS domains + full construct).

Packs a sequential variant (from tests/generate_protein_ergo.py) into the
v2 packed form (8 blocks, seeds 0.0-7.0, packed force-kernel tables),
reusing the BBA5 machinery. Sizes are PARSED from the sequential file
(NRES, MAXFRAME, MAXREG/NREG, NATIVE_CUTOFF, quench frame). Optional
per-domain RMSD ranges (COMPUTE_RMSD_RANGE, DOM rows) for the full
construct.

Usage: python3 min/pmargin/gen_10ps.py
Outputs: min/pmargin/sdrd_{A2,A3,B1,B2,full}.ergo
"""

import re
from pathlib import Path

import gen_packed_bba5 as G  # re-emits BBA5 files (deterministic); reuse

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"

DOM_RANGES_FULL = [(1, 152, "A2"), (153, 320, "A3"), (321, 440, "B1"), (441, 556, "B2")]


def parse_params(src):
    def grab(pat, cast=str):
        m = re.search(pat, src)
        assert m, pat
        return cast(m.group(1))
    return {
        "nres": grab(r"PARAMETER INTEGER :: NRES = (\d+)", int),
        "maxframe": grab(r"PARAMETER INTEGER :: MAXFRAME = (\d+)", int),
        "maxreg": grab(r"PARAMETER INTEGER :: MAXREG = (\d+)", int),
        "nreg": grab(r"PARAMETER INTEGER :: NREG = (\d+)", int),
        "cutoff": grab(r"PARAMETER REAL :: NATIVE_CUTOFF = ([0-9.]+)"),
        "quench": grab(r"IF FRAME > (\d+) THEN", int),
    }


def pack(seq_path, out_name, tag, dom_ranges=None):
    src = Path(seq_path).read_text()
    p = parse_params(src)
    nres = p["nres"]
    nblk = 8
    npts = nres * nblk

    m = re.search(r"(  ! Sequence design.*?)\nEND\n", src, flags=re.DOTALL)
    assert m
    seq_params = m.group(1).rstrip()
    assert seq_params.endswith("RETURN")
    seq_params = seq_params[: -len("RETURN")].rstrip()
    m = re.search(r"SUBROUTINE INIT_NATIVE\(\)\n(.*?)\nEND\n", src, flags=re.DOTALL)
    assert m
    init_native_body = m.group(1).rstrip()

    t = G.TEMPLATE
    t = t.replace("PARAMETER INTEGER :: NRES = 23", f"PARAMETER INTEGER :: NRES = {nres}")
    t = t.replace("PARAMETER INTEGER :: NPTS = 184", f"PARAMETER INTEGER :: NPTS = {npts}")
    t = t.replace("184, 184", f"{npts}, {npts}")
    t = t.replace("(184)", f"({npts})")
    for nm in ("RES_ANGK", "RES_ANGT0", "RES_TORSK", "RES_TORSP0", "RES_HYDRO",
               "NATIVE_X", "NATIVE_Y", "NATIVE_Z"):
        t = t.replace(f"{nm}(23)", f"{nm}({nres})")
    t = t.replace("(23, 23)", f"({nres}, {nres})")
    t = t.replace("PARAMETER INTEGER :: MAXFRAME = 48000",
                  f"PARAMETER INTEGER :: MAXFRAME = {p['maxframe']}")
    t = t.replace("PARAMETER INTEGER :: MAXREG = 6", f"PARAMETER INTEGER :: MAXREG = {p['maxreg']}")
    t = t.replace("PARAMETER INTEGER :: NREG = 6", f"PARAMETER INTEGER :: NREG = {p['nreg']}")
    t = t.replace("PARAMETER REAL :: NATIVE_CUTOFF = 2.522943",
                  f"PARAMETER REAL :: NATIVE_CUTOFF = {p['cutoff']}")
    t = t.replace("IF FRAME > 12000 THEN", f"IF FRAME > {p['quench']} THEN")
    t = t.replace("after frame 12000", f"after frame {p['quench']}")
    t = t.replace("! PACKED_BBA5 — 8 folding trajectories (seeds 0.0..7.0) in ONE program.",
                  f"! PACKED_{tag} — 8 folding trajectories (seeds 0.0..7.0) in ONE program.")
    t = t.replace("tests/waveform_bba5_seed_0.0.ergo", str(seq_path))
    t = t.replace('WRITE(*, "# PACKED_BBA5 NBLK=8 NRES=23 MAXFRAME=48000 QUENCH=12000")',
                  f'WRITE(*, "# PACKED_{tag} NBLK=8 NRES={nres} MAXFRAME={p["maxframe"]} QUENCH={p["quench"]}")')
    t = t.replace('WRITE(*, "# TRACE cols: block seed frame rmsd_native (blocks 1,2,5 every 100)")',
                  'WRITE(*, "# TRACE cols: block seed frame rmsd_native (blocks 1,2,5 every 500)")')
    t = t.replace("IF MOD(FRAME, 100) = 0 THEN", "IF MOD(FRAME, 500) = 0 THEN")

    t = t.replace("__SEQ_PARAMS__", seq_params).replace("__INIT_NATIVE__", init_native_body)

    # per-domain RMSD (full construct only)
    if dom_ranges:
        t = t.replace("STATIC REAL :: RMSD_B(8)",
                      "STATIC REAL :: RMSD_B(8)\nSTATIC REAL :: RMSD_D1(8)\n"
                      "STATIC REAL :: RMSD_D2(8)\nSTATIC REAL :: RMSD_D3(8)\nSTATIC REAL :: RMSD_D4(8)")
        FINAL_ANCHOR = """DO B = 1, NBLK
  OFF := (B - 1) * NRES
  CALL COMPUTE_RMSD(OFF)
  RMSD_B(B) := RMSD_NATIVE
ENDDO"""
        assert FINAL_ANCHOR in t
        t = t.replace(FINAL_ANCHOR, """DO B = 1, NBLK
  OFF := (B - 1) * NRES
  CALL COMPUTE_RMSD(OFF)
  RMSD_B(B) := RMSD_NATIVE
  CALL COMPUTE_RMSD_RANGE(OFF, 1, 152, 152)
  RMSD_D1(B) := RMSD_NATIVE
  CALL COMPUTE_RMSD_RANGE(OFF, 153, 320, 168)
  RMSD_D2(B) := RMSD_NATIVE
  CALL COMPUTE_RMSD_RANGE(OFF, 321, 440, 120)
  RMSD_D3(B) := RMSD_NATIVE
  CALL COMPUTE_RMSD_RANGE(OFF, 441, 556, 116)
  RMSD_D4(B) := RMSD_NATIVE
ENDDO""")
        DOM_WRITE_ANCHOR = """DO B = 1, NBLK
  WRITE(*, "FINAL %d %.1f %.4f") B, SEED_TAB(B), RMSD_B(B)
ENDDO"""
        assert DOM_WRITE_ANCHOR in t
        t = t.replace(DOM_WRITE_ANCHOR, DOM_WRITE_ANCHOR + """
DO B = 1, NBLK
  WRITE(*, "DOM %d %.1f %.4f %.4f %.4f %.4f %.4f") &
    B, SEED_TAB(B), RMSD_B(B), RMSD_D1(B), RMSD_D2(B), RMSD_D3(B), RMSD_D4(B)
ENDDO""")
        # COMPUTE_RMSD_RANGE subroutine (reuse the 1SNO one verbatim)
        import gen_packed_1sno as G1  # noqa: F401  (re-emits 1SNO files; deterministic)
        from gen_packed_1sno import RMSD_RANGE, R_END_ANCHOR
        assert R_END_ANCHOR in t
        t = t.replace(R_END_ANCHOR, R_END_ANCHOR + RMSD_RANGE, 1)

    # v2 surgery
    n_bond = (nres - 1) * nblk
    n_ang = (nres - 2) * nblk
    n_tors = (nres - 3) * nblk
    DECL_ANCHOR = "! ── Per-block seeds and results ──────────────────────────────"
    DECL_EXTRA = f"""! ── Packed force-kernel tables (v2): block offsets baked in ─────
PARAMETER INTEGER :: NBOND = {n_bond}
PARAMETER INTEGER :: NANG = {n_ang}
PARAMETER INTEGER :: NTORS = {n_tors}
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

    COIL_ANCHOR = f"""ENDDO

WRITE(*, "# PACKED_{tag} NBLK=8 NRES={nres} MAXFRAME={p['maxframe']} QUENCH={p['quench']}")"""
    assert COIL_ANCHOR in t
    t = t.replace(COIL_ANCHOR, f"""ENDDO
CALL INIT_TABLES()

WRITE(*, "# PACKED_{tag} NBLK=8 NRES={nres} MAXFRAME={p['maxframe']} QUENCH={p['quench']}")""")

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
      K := (B - 1) * {nres-1} + I
      BOND_A(K) := (B - 1) * NRES + I
      BOND_B(K) := (B - 1) * NRES + I + 1
    ENDDO
    DO I = 2, NRES - 1
      K := (B - 1) * {nres-2} + (I - 1)
      ANG_A(K) := (B - 1) * NRES + I - 1
      ANG_B(K) := (B - 1) * NRES + I
      ANG_C(K) := (B - 1) * NRES + I + 1
      ANGK_P(K) := RES_ANGK(I)
      ANGT0_P(K) := RES_ANGT0(I)
    ENDDO
    DO I = 2, NRES - 2
      K := (B - 1) * {nres-3} + (I - 1)
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

    out = PM / out_name
    out.write_text(t)
    print(f"wrote {out} ({len(t.splitlines())} lines)")


for dom in ("A2", "A3", "B1", "B2"):
    pack(PM / f"sdrd_{dom}_seq.ergo", f"sdrd_{dom}.ergo", f"SDRD_{dom}")
pack(PM / "sdrd_full_seq.ergo", "sdrd_full.ergo", "SDRD_FULL",
     dom_ranges=DOM_RANGES_FULL)
