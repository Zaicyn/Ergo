#!/usr/bin/env python3
"""gen_packed_1sno.py — packed 8-seed sweep + parallel tempering for 1SNO.

Builds on the BBA5 packed machinery (imports TEMPLATE and the temper
string constants from gen_packed_bba5 — importing it re-emits the BBA5
files, deterministic and harmless). Substitutes 1SNO sizes/config into
the template, splices tables from tests/waveform_snase_seed_0.0.ergo,
adds per-domain RMSD (CLINICAL.md 6.3: domains 1-98 and 99-136 per
SCALING.md), then applies the same v2 packed-force-kernel surgery and
the temper/gate emission.

Oracle: doc seed sweep tests/waveform_snase_seed_0.0..4.0.out at frame
48000 (raw model units; the doc quotes these numbers as A — true
A/model-unit = mean_ca_ca/1.52 = 2.4999).

Outputs: packed_1sno.ergo (baseline, v2 form), packed_1sno_temper.ergo
(SWAP_EVERY=500), packed_1sno_gate.ergo (SWAP_EVERY=0).
"""

import re
from pathlib import Path

import gen_packed_bba5 as G  # re-emits BBA5 files (deterministic); reuse strings

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "tests" / "waveform_snase_seed_0.0.ergo"

NRES = 136
NBLK = 8
NPTS = NRES * NBLK          # 1088
NBOND = (NRES - 1) * NBLK   # 1080
NANG = (NRES - 2) * NBLK    # 1072
NTORS = (NRES - 3) * NBLK   # 1064

src = SRC.read_text()

m = re.search(r"(  ! Sequence design.*?)\nEND\n", src, flags=re.DOTALL)
assert m
seq_params = m.group(1).rstrip()
assert seq_params.endswith("RETURN")
seq_params = seq_params[: -len("RETURN")].rstrip()

m = re.search(r"SUBROUTINE INIT_NATIVE\(\)\n(.*?)\nEND\n", src, flags=re.DOTALL)
assert m
init_native_body = m.group(1).rstrip()

# ── template with 1SNO substitutions ────────────────────────────────────
t = G.TEMPLATE
t = t.replace("PARAMETER INTEGER :: NRES = 23", f"PARAMETER INTEGER :: NRES = {NRES}")
t = t.replace("PARAMETER INTEGER :: NPTS = 184", f"PARAMETER INTEGER :: NPTS = {NPTS}")
t = t.replace("184, 184", f"{NPTS}, {NPTS}")          # HBOND_MATRIX
t = t.replace("(184)", f"({NPTS})")                   # packed state arrays
t = t.replace("(23, 23)", f"({NRES}, {NRES})")        # NATIVE_CONTACT / NATIVE_R0
for nm in ("RES_ANGK", "RES_ANGT0", "RES_TORSK", "RES_TORSP0", "RES_HYDRO",
           "NATIVE_X", "NATIVE_Y", "NATIVE_Z"):
    t = t.replace(f"{nm}(23)", f"{nm}({NRES})")       # shared 1D tables
t = t.replace("PARAMETER INTEGER :: MAXREG = 6", "PARAMETER INTEGER :: MAXREG = 246")
t = t.replace("PARAMETER INTEGER :: NREG = 6", "PARAMETER INTEGER :: NREG = 246")
t = t.replace("PARAMETER REAL :: NATIVE_CUTOFF = 2.522943",
              "PARAMETER REAL :: NATIVE_CUTOFF = 2.600077")
t = t.replace("IF FRAME > 12000 THEN", "IF FRAME > 38400 THEN")  # quench 0.8x48000
t = t.replace("! PACKED_BBA5 — 8 folding trajectories (seeds 0.0..7.0) in ONE program.",
              "! PACKED_1SNO — 8 folding trajectories (seeds 0.0..7.0) in ONE program.\n"
              "! 1SNO staphylococcal nuclease, 136 residues, two domains (1-98, 99-136).\n"
              "! Per-domain RMSD added per CLINICAL.md 6.3.")
t = t.replace("tests/waveform_bba5_seed_0.0.ergo", "tests/waveform_snase_seed_0.0.ergo")
t = t.replace('WRITE(*, "# PACKED_BBA5 NBLK=8 NRES=23 MAXFRAME=48000 QUENCH=12000")',
              'WRITE(*, "# PACKED_1SNO NBLK=8 NRES=136 MAXFRAME=48000 QUENCH=38400")')
# trace the interesting blocks: 1 (good), 4 (seed 3.0 trap), 5 (seed 4.0 slow)
t = t.replace('WRITE(*, "# TRACE cols: block seed frame rmsd_native (blocks 1,2,5 every 100)")',
              'WRITE(*, "# TRACE cols: block seed frame rmsd_native (blocks 1,4,5 every 200)")')
t = t.replace("IF MOD(FRAME, 100) = 0 THEN", "IF MOD(FRAME, 200) = 0 THEN")
t = t.replace("IF B = 1 .OR. B = 2 .OR. B = 5 THEN", "IF B = 1 .OR. B = 4 .OR. B = 5 THEN")

t = t.replace("__SEQ_PARAMS__", seq_params).replace("__INIT_NATIVE__", init_native_body)

# ── per-domain RMSD: declarations + final-block extension + subroutine ──
t = t.replace("STATIC REAL :: RMSD_B(8)",
              "STATIC REAL :: RMSD_B(8)\nSTATIC REAL :: RMSD_D1(8)\nSTATIC REAL :: RMSD_D2(8)")
FINAL_ANCHOR = """DO B = 1, NBLK
  OFF := (B - 1) * NRES
  CALL COMPUTE_RMSD(OFF)
  RMSD_B(B) := RMSD_NATIVE
ENDDO
DO B = 1, NBLK
  WRITE(*, "FINAL %d %.1f %.4f") B, SEED_TAB(B), RMSD_B(B)
ENDDO"""
assert FINAL_ANCHOR in t
t = t.replace(FINAL_ANCHOR, """DO B = 1, NBLK
  OFF := (B - 1) * NRES
  CALL COMPUTE_RMSD(OFF)
  RMSD_B(B) := RMSD_NATIVE
  CALL COMPUTE_RMSD_RANGE(OFF, 1, 98, 98)
  RMSD_D1(B) := RMSD_NATIVE
  CALL COMPUTE_RMSD_RANGE(OFF, 99, 136, 38)
  RMSD_D2(B) := RMSD_NATIVE
ENDDO
DO B = 1, NBLK
  WRITE(*, "FINAL %d %.1f %.4f") B, SEED_TAB(B), RMSD_B(B)
ENDDO
DO B = 1, NBLK
  WRITE(*, "DOM %d %.1f %.4f %.4f %.4f") B, SEED_TAB(B), RMSD_B(B), RMSD_D1(B), RMSD_D2(B)
ENDDO""")

RMSD_RANGE = """

! ════════════════════════════════════════════════════════════
! COMPUTE_RMSD_RANGE: Kabsch RMSD over residues ILO..IHI (NR = count)
! of one block — per-domain diagnostic (CLINICAL.md 6.3). Native
! centering/covariance restricted to the same subrange.
! ════════════════════════════════════════════════════════════

SUBROUTINE COMPUTE_RMSD_RANGE(OFFB, ILO, IHI, NR)
  INTEGER :: OFFB, ILO, IHI, NR
  INTEGER :: I, ITER
  REAL :: XC, YC, ZC, XN, YN, ZN
  REAL :: SXX, SXY, SXZ, SYX, SYY, SYZ, SZX, SZY, SZZ
  REAL :: N44(4,4), VEC(4), NEWVEC(4), NORM
  REAL :: RX, RY, RZ, NX, NY, NZ
  REAL :: Q0, Q1, Q2, Q3, QQ
  REAL :: R11, R12, R13, R21, R22, R23, R31, R32, R33
  REAL :: TX, TY, TZ, SUM_DIST_SQ

  XC := 0.0
  YC := 0.0
  ZC := 0.0
  DO I = ILO, IHI
    XC := XC + RES_X(OFFB + I)
    YC := YC + RES_Y(OFFB + I)
    ZC := ZC + RES_Z(OFFB + I)
  ENDDO
  XC := XC / REAL(NR)
  YC := YC / REAL(NR)
  ZC := ZC / REAL(NR)

  XN := 0.0
  YN := 0.0
  ZN := 0.0
  DO I = ILO, IHI
    XN := XN + NATIVE_X(I)
    YN := YN + NATIVE_Y(I)
    ZN := ZN + NATIVE_Z(I)
  ENDDO
  XN := XN / REAL(NR)
  YN := YN / REAL(NR)
  ZN := ZN / REAL(NR)

  SXX := 0.0
  SXY := 0.0
  SXZ := 0.0
  SYX := 0.0
  SYY := 0.0
  SYZ := 0.0
  SZX := 0.0
  SZY := 0.0
  SZZ := 0.0
  DO I = ILO, IHI
    RX := RES_X(OFFB + I) - XC
    RY := RES_Y(OFFB + I) - YC
    RZ := RES_Z(OFFB + I) - ZC
    NX := NATIVE_X(I) - XN
    NY := NATIVE_Y(I) - YN
    NZ := NATIVE_Z(I) - ZN
    SXX := SXX + RX * NX
    SXY := SXY + RX * NY
    SXZ := SXZ + RX * NZ
    SYX := SYX + RY * NX
    SYY := SYY + RY * NY
    SYZ := SYZ + RY * NZ
    SZX := SZX + RZ * NX
    SZY := SZY + RZ * NY
    SZZ := SZZ + RZ * NZ
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
  DO ITER = 1, 40
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
  DO I = ILO, IHI
    RX := RES_X(OFFB + I) - XC
    RY := RES_Y(OFFB + I) - YC
    RZ := RES_Z(OFFB + I) - ZC
    TX := R11*RX + R12*RY + R13*RZ
    TY := R21*RX + R22*RY + R23*RZ
    TZ := R31*RX + R32*RY + R33*RZ
    NX := NATIVE_X(I) - XN
    NY := NATIVE_Y(I) - YN
    NZ := NATIVE_Z(I) - ZN
    SUM_DIST_SQ := SUM_DIST_SQ + (TX - NX)**2 + (TY - NY)**2 + (TZ - NZ)**2
  ENDDO
  RMSD_NATIVE := SQRT(SUM_DIST_SQ / REAL(NR))

  RETURN
END
"""
R_END_ANCHOR = "  RMSD_NATIVE := SQRT(SUM_DIST_SQ / REAL(NRES))\n\n  RETURN\nEND"
assert R_END_ANCHOR in t
t = t.replace(R_END_ANCHOR, R_END_ANCHOR + RMSD_RANGE, 1)

# ── v2 packed-force-kernel surgery (same anchors, 1SNO sizes) ───────────
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

WRITE(*, "# PACKED_1SNO NBLK=8 NRES=136 MAXFRAME=48000 QUENCH=38400")"""
assert COIL_ANCHOR in t
t = t.replace(COIL_ANCHOR, """ENDDO
CALL INIT_TABLES()

WRITE(*, "# PACKED_1SNO NBLK=8 NRES=136 MAXFRAME=48000 QUENCH=38400")""")

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

OUT = ROOT / "min" / "pmargin" / "packed_1sno.ergo"
OUT.write_text(t)
print(f"wrote {OUT} ({len(t.splitlines())} lines)")


# ── temper + gate (same string surgery as BBA5, 1SNO header) ────────────
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
    x = x.replace("# PACKED_1SNO NBLK=8", f"# PACKED_1SNO_TEMPER SWAP_EVERY={swap_every} NBLK=8")
    return x


temper = make_temper(t, 500)
OUTT = ROOT / "min" / "pmargin" / "packed_1sno_temper.ergo"
OUTT.write_text(temper)
print(f"wrote {OUTT} ({len(temper.splitlines())} lines)")

gate = make_temper(t, 0)
OUTG = ROOT / "min" / "pmargin" / "packed_1sno_gate.ergo"
OUTG.write_text(gate)
print(f"wrote {OUTG} ({len(gate.splitlines())} lines)")
