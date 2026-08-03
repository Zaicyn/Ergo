#!/usr/bin/env python3
"""gen_tax.py — directionality tax on amide bonds (register-offset-priced wells).

Tax formula (documented): for an amide bond between residue i (sheet 1)
and residue j (sheet 2) the register offset from the crystal
anti-parallel diagonal (i+j=8, the (2,6),(4,4),(6,2) pattern) is
  OFF = |i + j - 8|   [residues]
and the effective well depth is
  D_eff = D * (1 - TAX * OFF)
At the well bottom this is exactly E = -D + TAX*D*OFF (the prescribed
penalty: wrong pairings possible but expensive). D_eff enters BOTH the
greedy bond choice (each amide O bonds the in-range N with the highest
score DEFF*EXP(-HB_A*(D-HB_R0)), only if score > 0) AND the Morse force
(poor pairings bind weakly, DEFF <= 0 pairs cannot bond). No register
masking, no forcing — any pair may form if it pays.
Bond energy for the gap measurement: E = DEFF * (g^2 - 2g) per bond.
Scramble control: diagonal constant 8 -> 10 (tax prices the WRONG
diagonal; must destabilize the correct register).
Gate: TAX = 0 reproduces the bead model (off-by-one persists).
Everything else identical to gen_amide_beads.py (D = 0.2 base).
"""

from pathlib import Path

import gen_amide_beads as GB  # re-emits bead files (deterministic)
import gen_amyloid as G

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "min" / "amyloid"
B = 1.9468
CA = GB.CA
AMIDE = GB.AMIDE
POLAR = GB.POLAR

TAX_SECTIONS = """  ! ── bead thermal kicks ──
  DO K = 1, NB
    BEAD_VX(K) := BEAD_VX(K) + THERMAL_CURRENT * SIN((K+40)*7.3 + REAL(FRAME)*0.17)
    BEAD_VY(K) := BEAD_VY(K) + THERMAL_CURRENT * COS((K+40)*5.7 + REAL(FRAME)*0.31)
    BEAD_VZ(K) := BEAD_VZ(K) + THERMAL_CURRENT * SIN((K+40)*3.1 + REAL(FRAME)*0.09)
  ENDDO

  ! ── bead tethers (stiff Morse, per-residue crystal r0) ──
  DO M = 1, NTETH
    IA := TETH_A(M)
    IB := TETH_B(M)
    IF IA < 0 THEN
      DX := RES_X(0 - IA) - BEAD_X(IB)
      DY := RES_Y(0 - IA) - BEAD_Y(IB)
      DZ := RES_Z(0 - IA) - BEAD_Z(IB)
    ELSE
      DX := BEAD_X(IA) - BEAD_X(IB)
      DY := BEAD_Y(IA) - BEAD_Y(IB)
      DZ := BEAD_Z(IA) - BEAD_Z(IB)
    ENDIF
    D := SQRT(DX*DX + DY*DY + DZ*DZ)
    IF D > 0.0 THEN
      E := EXP(-2.0 * (D - TETH_R0(M)))
      FM := -2.0 * 2.0 * 2.0 * (1.0 - E) * E * FORCE_SCALE
      IF IA < 0 THEN
        RES_VX(0 - IA) := RES_VX(0 - IA) + FM * DX / D * DT
        RES_VY(0 - IA) := RES_VY(0 - IA) + FM * DY / D * DT
        RES_VZ(0 - IA) := RES_VZ(0 - IA) + FM * DZ / D * DT
      ELSE
        BEAD_VX(IA) := BEAD_VX(IA) + FM * DX / D * DT
        BEAD_VY(IA) := BEAD_VY(IA) + FM * DY / D * DT
        BEAD_VZ(IA) := BEAD_VZ(IA) + FM * DZ / D * DT
      ENDIF
      BEAD_VX(IB) := BEAD_VX(IB) - FM * DX / D * DT
      BEAD_VY(IB) := BEAD_VY(IB) - FM * DY / D * DT
      BEAD_VZ(IB) := BEAD_VZ(IB) - FM * DZ / D * DT
    ENDIF
  ENDDO

  ! ── H-bond formation: greedy valence-1, TAX-AWARE scoring.
  !    D_eff = HB_D * (1 - TAX * |i+j-DIAG|); bond the in-range,
  !    inter-sheet, free N with the highest DEFF*EXP(-HB_A*(D-HB_R0));
  !    no bond if the best score <= 0. Wrong pairings pay per the
  !    formula; no masking. ──
  DO K = 1, 20
    HB_PART(K) := 0
    HB_NUSED(K) := 0
  ENDDO
  DO K = 1, 20
    BSCORE := 0.0
    BEST := 0
    RI := MOD(BEAD_PARENT(2*K-1) - 1, NRES) + 1
    DO M = 1, 20
      IF HB_NUSED(M) = 0 .AND. INT((K - 1) / 10) /= INT((M - 1) / 10) THEN
        D := SQRT((BEAD_X(2*K-1) - BEAD_X(2*M))**2 + (BEAD_Y(2*K-1) - BEAD_Y(2*M))**2 + (BEAD_Z(2*K-1) - BEAD_Z(2*M))**2)
        IF D < HB_RANGE THEN
          RJ := MOD(BEAD_PARENT(2*M) - 1, NRES) + 1
          DEFF := HB_D * (1.0 - TAX * REAL(ABS(RI + RJ - DIAG)))
          SCORE := DEFF * EXP(0.0 - HB_A * (D - HB_R0))
          IF SCORE > BSCORE THEN
            BSCORE := SCORE
            BEST := M
          ENDIF
        ENDIF
      ENDIF
    ENDDO
    IF BEST > 0 THEN
      HB_PART(K) := BEST
      HB_NUSED(BEST) := 1
    ENDIF
  ENDDO

  ! ── H-bond Morse forces at the taxed depth + bond energy ──
  EBOND := 0.0
  DO K = 1, 20
    IF HB_PART(K) > 0 THEN
      IA := 2 * K - 1
      IB := 2 * HB_PART(K)
      RI := MOD(BEAD_PARENT(IA) - 1, NRES) + 1
      RJ := MOD(BEAD_PARENT(IB) - 1, NRES) + 1
      DEFF := HB_D * (1.0 - TAX * REAL(ABS(RI + RJ - DIAG)))
      DX := BEAD_X(IA) - BEAD_X(IB)
      DY := BEAD_Y(IA) - BEAD_Y(IB)
      DZ := BEAD_Z(IA) - BEAD_Z(IB)
      D := SQRT(DX*DX + DY*DY + DZ*DZ)
      IF D > 0.0 THEN
        E := EXP(-HB_A * (D - HB_R0))
        EBOND := EBOND + DEFF * (E * E - 2.0 * E)
        FM := -2.0 * DEFF * HB_A * (1.0 - E) * E * FORCE_SCALE
        BEAD_VX(IA) := BEAD_VX(IA) + FM * DX / D * DT
        BEAD_VY(IA) := BEAD_VY(IA) + FM * DY / D * DT
        BEAD_VZ(IA) := BEAD_VZ(IA) + FM * DZ / D * DT
        BEAD_VX(IB) := BEAD_VX(IB) - FM * DX / D * DT
        BEAD_VY(IB) := BEAD_VY(IB) - FM * DY / D * DT
        BEAD_VZ(IB) := BEAD_VZ(IB) - FM * DZ / D * DT
        ! directionality: CA-N..O and CA-O..N angle at 90 deg (crystal mean)
        IA2 := BEAD_PARENT(IA)
        IB2 := BEAD_PARENT(IB)
        UX := RES_X(IA2) - BEAD_X(IB)
        UY := RES_Y(IA2) - BEAD_Y(IB)
        UZ := RES_Z(IA2) - BEAD_Z(IB)
        WX := BEAD_X(IA) - BEAD_X(IB)
        UN := SQRT(UX*UX + UY*UY + UZ*UZ)
        VN := SQRT(WX*WX + WY*WY + WZ*WZ)
        IF UN > 1.0E-12 .AND. VN > 1.0E-12 THEN
          CS := MAX(-1.0, MIN(1.0, (UX*WX + UY*WY + UZ*WZ) / (UN * VN)))
          F := 2.0 * HB_ANGK * CS
          FX := F * (WX / (UN * VN) - CS * UX / UN / UN)
          FY := F * (UY / (UN * VN) - CS * UY / UN / UN)
          FZ := F * (UZ / (UN * VN) - CS * UZ / UN / UN)
          RES_VX(IA2) := RES_VX(IA2) - FX * DT * FORCE_SCALE
          RES_VY(IA2) := RES_VY(IA2) - FY * DT * FORCE_SCALE
          RES_VZ(IA2) := RES_VZ(IA2) - FZ * DT * FORCE_SCALE
          FX := F * (UX / (UN * VN) - CS * WX / VN / VN)
          FY := F * (UY / (UN * VN) - CS * WY / VN / VN)
          FZ := F * (UZ / (UN * VN) - CS * WZ / VN / VN)
          BEAD_VX(IA) := BEAD_VX(IA) - FX * DT * FORCE_SCALE
          BEAD_VY(IA) := BEAD_VY(IA) - FY * DT * FORCE_SCALE
          BEAD_VZ(IA) := BEAD_VZ(IA) - FZ * DT * FORCE_SCALE
        ENDIF
      ENDIF
    ENDIF
  ENDDO

  ! ── bead damping + position update ──
  DO K = 1, NB
    BEAD_VX(K) := BEAD_VX(K) * VDAMP(1)
    BEAD_VY(K) := BEAD_VY(K) * VDAMP(1)
    BEAD_VZ(K) := BEAD_VZ(K) * VDAMP(1)
    BEAD_X(K) := BEAD_X(K) + BEAD_VX(K) * DT
    BEAD_Y(K) := BEAD_Y(K) + BEAD_VY(K) * DT
    BEAD_Z(K) := BEAD_Z(K) + BEAD_VZ(K) * DT
  ENDDO
"""

TAX_DECLS_EXTRA = """PARAMETER REAL :: TAX = __TAX__
PARAMETER INTEGER :: DIAG = __DIAG__
STATIC REAL :: BSCORE, SCORE, DEFF, EBOND
STATIC INTEGER :: RI, RJ
"""

YTRACE = """  ! sheet-2 register offset trace (COM y of chains 3,4)
  IF MOD(FRAME, 200) = 0 THEN
    CX := 0.0
    DO I = 15, 28
      CX := CX + RES_Y(I)
    ENDDO
    WRITE(*, "YTRACE %d %.4f") FRAME, CX / 14.0
  ENDIF
"""

EBOND_PRINT = """WRITE(*, "EBOND %.6f") EBOND
"""

HB_MEASURE_TAX = EBOND_PRINT + GB.HB_MEASURE


def build(tag, tax, diag, yoff, out_name):
    s = G.TEMPLATE.replace("__TAG__", tag).replace("__NC__", "4")
    s = s.replace("__NTOT__", "28").replace("__NCON__", "14")
    s = s.replace("__ICONTACTS__", G.ICONTACTS)
    s = s.replace("__INTRAGO__", "")
    s = s.replace("DO C = 1, NC - 1\n      D := 0.0", "DO C = 1, NC - 1, 2\n      D := 0.0")
    s = s.replace("DO C = 1, NC - 1\n  DO K = 1, NRES", "DO C = 1, NC - 1, 2\n  DO K = 1, NRES")
    s = s.replace("STATIC REAL :: IC_R0(NCON)",
                  "STATIC REAL :: IC_R0(NCON)\n"
                  + GB.BEAD_DECLS.replace("__HBD__", "0.2")
                  + TAX_DECLS_EXTRA.replace("__TAX__", tax).replace("__DIAG__", diag))
    s = s.replace("STATIC REAL :: U1, U2, COSTH, SINTH, PHI2, CANDX, CANDY, CANDZ, DD",
                  "STATIC REAL :: U1, U2, COSTH, SINTH, PHI2, CANDX, CANDY, CANDZ, DD\n"
                  "STATIC INTEGER :: IA2, IB2\nSTATIC REAL :: FX, FY, FZ")
    s = s.replace("  ! Velocity damping (per-chain VDAMP: template chains strongly damped)",
                  TAX_SECTIONS + "\n  ! Velocity damping (per-chain VDAMP: template chains strongly damped)")
    s = s.replace("  ! Trace: mean in-register distance per adjacent chain pair",
                  YTRACE + "\n  ! Trace: mean in-register distance per adjacent chain pair")
    s = s.replace("DO C = 1, NC\n  CX := 0.0", HB_MEASURE_TAX + "\nDO C = 1, NC\n  CX := 0.0")

    angk = "\n".join(f"  RES_ANGK({i+1}) := 0.3000" for i in range(7))
    angt = "\n".join(f"  RES_ANGT0({i+1}) := {G.ANG_T0[i]:.6f}" for i in range(7))
    torsk = "\n".join(f"  RES_TORSK({i+1}) := 0.2000" for i in range(7))
    torsp = "\n".join(f"  RES_TORSP0({i+1}) := {G.TORS_P0[i]:.6f}" for i in range(7))
    hydro = "\n".join(f"  RES_HYDRO({i+1}) := {G.HYDRO[i]:.1f}" for i in range(7))
    vd = "\n".join(f"  VDAMP({c+1}) := 0.9" for c in range(4))
    ic_lines = []
    m = 0
    for cp in (0, 2):
        for kk in range(7):
            m += 1
            ic_lines.append(f"  IC_A({m}) := {cp*7 + kk + 1}")
            ic_lines.append(f"  IC_B({m}) := {(cp+1)*7 + kk + 1}")
            ic_lines.append(f"  IC_R0({m}) := 1.9468")
    res_list = POLAR
    teth, bparent = [], []
    kb = 0
    for c in range(4):
        for r in res_list:
            kb += 2
            ca_idx = c * 7 + r
            teth.append(f"  TETH_A({len(teth)+1}) := {0 - ca_idx}\n  TETH_B({len(teth)+1}) := {kb-1}\n  TETH_R0({len(teth)+1}) := {AMIDE[r][1]:.4f}")
            teth.append(f"  TETH_A({len(teth)+1}) := {0 - ca_idx}\n  TETH_B({len(teth)+1}) := {kb}\n  TETH_R0({len(teth)+1}) := {AMIDE[r][2]:.4f}")
            teth.append(f"  TETH_A({len(teth)+1}) := {kb-1}\n  TETH_B({len(teth)+1}) := {kb}\n  TETH_R0({len(teth)+1}) := {AMIDE[r][3]:.4f}")
            bparent.append(f"  BEAD_PARENT({kb-1}) := {ca_idx}")
            bparent.append(f"  BEAD_PARENT({kb}) := {ca_idx}")
    s0 = [GB.screw(p) for p in CA]
    chains = [
        [(x, y, z) for x, y, z in CA],
        [(x, y + B, z) for x, y, z in CA],
        [(x, y + yoff, z) for x, y, z in s0],
        [(x, y + B + yoff, z) for x, y, z in s0],
    ]
    init_lines = []
    for c, ch in enumerate(chains):
        lines = [f"\n  ! Chain {c+1}: face-start, sheet2 offset {yoff:.4f}"]
        for k2, (x, y, z) in enumerate(ch):
            lines.append(f"  RES_X({c*7+k2+1}) := {x:.6f}")
            lines.append(f"  RES_Y({c*7+k2+1}) := {y:.6f}")
            lines.append(f"  RES_Z({c*7+k2+1}) := {z:.6f}")
        lines.append("  DO I = 1, NRES")
        lines.append(f"    RES_VX({c*7} + I) := 0.0")
        lines.append(f"    RES_VY({c*7} + I) := 0.0")
        lines.append(f"    RES_VZ({c*7} + I) := 0.0")
        lines.append("  ENDDO")
        init_lines.append("\n".join(lines))
    blines = []
    kb = 0
    for c in range(4):
        for r in res_list:
            kb += 2
            cx, cy, cz = chains[c][r - 1]
            for t, kbb in (("O", kb - 1), ("N", kb)):
                off = AMIDE[r][4] if t == "N" else AMIDE[r][5]
                if c >= 2:
                    # screw mate: side-chain offsets flip in x and z
                    # (the bead files before this fix had sheet-2 beads
                    # on the wrong side of their C-alpha)
                    off = (-off[0], off[1], -off[2])
                blines.append(f"  BEAD_X({kbb}) := {cx + off[0]:.6f}")
                blines.append(f"  BEAD_Y({kbb}) := {cy + off[1]:.6f}")
                blines.append(f"  BEAD_Z({kbb}) := {cz + off[2]:.6f}")
                blines.append(f"  BEAD_VX({kbb}) := 0.0")
                blines.append(f"  BEAD_VY({kbb}) := 0.0")
                blines.append(f"  BEAD_VZ({kbb}) := 0.0")
    init_lines.append("\n".join(blines))
    init_body = "\n".join([angk, angt, torsk, torsp, hydro, vd, ""] + ic_lines
                          + teth + bparent + init_lines)
    s = s.replace("CALL INIT_ALL()", init_body)
    (OUT / out_name).write_text(s)
    print(f"wrote {out_name} (TAX={tax}, DIAG={diag}, yoff={yoff})")


# gate + bracket, off-by-one and correct starts
for tax in ("0.0", "0.1", "0.25", "0.5", "1.0", "2.0"):
    tag = tax.replace(".", "p")
    build(f"_TAX{tag}_OFF1", tax, "8", 1.9468, f"tax_{tag}_off1.ergo")
    build(f"_TAX{tag}_FACE", tax, "8", 0.0, f"tax_{tag}_face.ergo")
# scramble: tax prices the wrong diagonal (i+j=10)
build("_TAX0p5_SCRDIAG", "0.5", "10", 0.0, "tax_0p5_scrdiag_face.ergo")
build("_TAX0p5_SCRDIAG_OFF1", "0.5", "10", 1.9468, "tax_0p5_scrdiag_off1.ergo")
