#!/usr/bin/env python3
"""gen_amide.py — amide ladder term for emergent zipper nucleation.

Well geometry from the REAL 1YJP crystal (no invented distances, see
amyloid/zipper_check.md for the screw-mate analysis):
  amide N<->O across the zipper: 3.353 A (A2.ND2-S6.OD1, a true H-bond),
    4.056/4.075 A (A6-S2), 5.651-7.241 A (A4-S4, A2.OD1-S6.ND2)
  Cbeta-Cbeta of the (2,6),(4,4),(6,2) diagonal: 5.660 / 4.399 / 4.581 A,
    mean 4.880 A = 1.952 model units (x0.400074), spread +/-0.63 A
  -> Gaussian well LAD_R0 = 1.952 u on the Cbeta proxy (aromatic-term
    pattern: CB = Ca + fixed native offset from 1YJP_ca.json),
    LAD_ALPHA = 1.0 (>=78% strength across the crystal spread).

The term: for Asn/Gln residues (positions 2-6 of GNNQQNY; only those
types pass the filter) across the two sheets, attraction
  FM = -LADDER_K * w * EXP(-1.0 * (D - 1.952)^2), D = Cbeta-Cbeta,
register-weighted for the anti-parallel face (the 2_1 screw flips the
facing chain): Delta = i + j - 8; w = 1.0 at Delta=0, 0.5 at |Delta|=1,
0 beyond (documented choice; matches the crystal's closest pairs).

Bracket: LADDER_K in {0.001, 0.002, 0.004, 0.008} = 0.5x/1x/2x/4x
HYDRO_STRENGTH (0.002). Scramble controls at K=0.004:
  (a) wrong types (G/Y counted polar): only (1,7),(7,1) attract —
      must NOT assemble the correct zipper
  (b) inverted register weights (w=1.0 at |Delta|=2, zero at Delta=0)
      — must NOT produce the correct register

Base: the emergent zipper variant (in-register contacts ON within
sheets, inter-sheet contacts OFF), all chains from coils, 12000 frames.
"""

from pathlib import Path

import gen_zipper as GZ  # re-emits zipper+amyloid bases (deterministic)
import gen_amyloid as G

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "min" / "amyloid"

import json
CJ = json.load(open(ROOT / "pdb" / "1YJP_ca.json"))
SCALE = 0.400074
CB_OFF = []
for k in range(7):
    ca = CJ['coords'][k]
    cb = CJ['cb_coords'][k]
    CB_OFF.append([(cb[0]-ca[2]) * SCALE, (cb[1]-ca[3]) * SCALE, (cb[2]-ca[4]) * SCALE])

NRES_PER_CHAIN = 7
POLAR = [2, 3, 4, 5, 6]  # N N Q Q N

# chain pairs across the sheets: (1,3),(1,4),(2,3),(2,4) -> global indices
CHAIN_PAIRS = [(0, 2), (0, 3), (1, 2), (1, 3)]  # 0-based chain indices


def ladder_pairs(mode):
    """(LA_global, LB_global, weight) entries per mode."""
    out = []
    for c1, c2 in CHAIN_PAIRS:
        if mode == "type":
            # scramble (a): wrong types — G(1) and Y(7) count as polar
            cand = [(1, 7, 1.0), (7, 1, 1.0)]
        elif mode == "reg":
            # scramble (b): inverted register — full weight at |Delta|=2
            cand = [(i, j, 1.0) for i in POLAR for j in POLAR
                    if abs(i + j - 8) == 2]
        else:
            cand = [(i, j, 1.0 if i + j == 8 else 0.5)
                    for i in POLAR for j in POLAR if abs(i + j - 8) <= 1]
        for i, j, w in cand:
            out.append((c1 * 7 + i, c2 * 7 + j, w))
    return out


LAD_DECLS = """PARAMETER INTEGER :: NLAD = __NLAD__
PARAMETER REAL :: LADDER_K = __K__
PARAMETER REAL :: LAD_R0 = 1.9520
PARAMETER REAL :: LAD_ALPHA = 1.0
STATIC INTEGER :: LAD_A(NLAD), LAD_B(NLAD)
STATIC REAL :: LAD_W(NLAD)
STATIC REAL :: CB_OFF_X(7), CB_OFF_Y(7), CB_OFF_Z(7)
STATIC INTEGER :: LA, LB
"""

LAD_FORCE = """  ! Amide ladder: type-filtered (N/Q), register-weighted Cbeta attraction
  DO M = 1, NLAD
    IA := LAD_A(M)
    IB := LAD_B(M)
    LA := MOD(IA - 1, NRES) + 1
    LB := MOD(IB - 1, NRES) + 1
    DX := (RES_X(IA) + CB_OFF_X(LA)) - (RES_X(IB) + CB_OFF_X(LB))
    DY := (RES_Y(IA) + CB_OFF_Y(LA)) - (RES_Y(IB) + CB_OFF_Y(LB))
    DZ := (RES_Z(IA) + CB_OFF_Z(LA)) - (RES_Z(IB) + CB_OFF_Z(LB))
    D := SQRT(DX*DX + DY*DY + DZ*DZ)
    IF D > 0.0 .AND. D < HYDRO_CUTOFF THEN
      FM := -LADDER_K * LAD_W(M) * EXP(-LAD_ALPHA * (D - LAD_R0) ** 2)
      RES_VX(IA) := RES_VX(IA) + FM * DX / D * DT * FORCE_SCALE
      RES_VY(IA) := RES_VY(IA) + FM * DY / D * DT * FORCE_SCALE
      RES_VZ(IA) := RES_VZ(IA) + FM * DZ / D * DT * FORCE_SCALE
      RES_VX(IB) := RES_VX(IB) - FM * DX / D * DT * FORCE_SCALE
      RES_VY(IB) := RES_VY(IB) - FM * DY / D * DT * FORCE_SCALE
      RES_VZ(IB) := RES_VZ(IB) - FM * DZ / D * DT * FORCE_SCALE
    ENDIF
  ENDDO
"""


def build(tag, k, mode, out_name, spacing=None, custom_inits=None):
    pairs = ladder_pairs(mode)
    s = G.TEMPLATE.replace("__TAG__", tag).replace("__NC__", "4")
    s = s.replace("__NTOT__", "28").replace("__NCON__", "14")
    s = s.replace("__ICONTACTS__", G.ICONTACTS + "\n" + LAD_FORCE)
    s = s.replace("__INTRAGO__", "")
    s = s.replace("DO C = 1, NC - 1\n      D := 0.0", "DO C = 1, NC - 1, 2\n      D := 0.0")
    s = s.replace("DO C = 1, NC - 1\n  DO K = 1, NRES", "DO C = 1, NC - 1, 2\n  DO K = 1, NRES")
    s = s.replace("STATIC REAL :: IC_R0(NCON)",
                  "STATIC REAL :: IC_R0(NCON)\n"
                  + LAD_DECLS.replace("__NLAD__", str(len(pairs))).replace("__K__", k))
    s = s.replace("DO C = 1, NC\n  CX := 0.0", GZ.ZIP_MEASURE + "\nDO C = 1, NC\n  CX := 0.0")
    # init
    angk = "\n".join(f"  RES_ANGK({i+1}) := 0.3000" for i in range(7))
    angt = "\n".join(f"  RES_ANGT0({i+1}) := {G.ANG_T0[i]:.6f}" for i in range(7))
    torsk = "\n".join(f"  RES_TORSK({i+1}) := 0.2000" for i in range(7))
    torsp = "\n".join(f"  RES_TORSP0({i+1}) := {G.TORS_P0[i]:.6f}" for i in range(7))
    hydro = "\n".join(f"  RES_HYDRO({i+1}) := {G.HYDRO[i]:.1f}" for i in range(7))
    vd = "\n".join(f"  VDAMP({c+1}) := 0.9" for c in range(4))
    cbo = []
    for k2 in range(7):
        cbo.append(f"  CB_OFF_X({k2+1}) := {CB_OFF[k2][0]:.6f}")
        cbo.append(f"  CB_OFF_Y({k2+1}) := {CB_OFF[k2][1]:.6f}")
        cbo.append(f"  CB_OFF_Z({k2+1}) := {CB_OFF[k2][2]:.6f}")
    ic_lines = []
    m = 0
    for cp in (0, 2):
        for kk in range(7):
            m += 1
            ic_lines.append(f"  IC_A({m}) := {cp*7 + kk + 1}")
            ic_lines.append(f"  IC_B({m}) := {(cp+1)*7 + kk + 1}")
            ic_lines.append(f"  IC_R0({m}) := 1.9468")
    lad_lines = []
    for m, (la, lb, w) in enumerate(pairs, start=1):
        lad_lines.append(f"  LAD_A({m}) := {la}")
        lad_lines.append(f"  LAD_B({m}) := {lb}")
        lad_lines.append(f"  LAD_W({m}) := {w:.4f}")
    # zipper measurement tables (measurement only, from gen_zipper ZIP list)
    zip_lines = []
    for m, (za, zb, zr) in enumerate(GZ.ZIP, start=1):
        zip_lines.append(f"  ZA({m}) := {za}")
        zip_lines.append(f"  ZB({m}) := {zb}")
        zip_lines.append(f"  ZR0({m}) := {zr:.4f}")
    s = s.replace("STATIC REAL :: ZR0(NZ), DMIN", "STATIC REAL :: ZR0(NZ), DMIN")
    if custom_inits is not None:
        inits = custom_inits
    else:
        inits = [G.coil_chain_lines(c + 1, f"{c * 1.0:.1f}") for c in range(4)]
        if spacing is not None:
            # close-start variant: bypass diffusional encounter (the sim's
            # timescale cannot show it — documented in amide_check.md)
            for c in range(4):
                old = f"RES_X({c*7+1}) := {10.0 + c*10.0}"
                new = f"RES_X({c*7+1}) := {10.0 + c*spacing}"
                assert old in inits[c], old
                inits[c] = inits[c].replace(old, new)
    init_body = "\n".join([angk, angt, torsk, torsp, hydro, vd, ""] + cbo + ic_lines
                          + lad_lines + zip_lines + inits)
    s = s.replace("CALL INIT_ALL()", init_body)
    # ZMIN/ZGEOM need NZ + ZA/ZB/ZR0 decls: reuse gen_zipper's ZIP_DECLS
    s = s.replace("STATIC REAL :: CB_OFF_X(7), CB_OFF_Y(7), CB_OFF_Z(7)",
                  "STATIC REAL :: CB_OFF_X(7), CB_OFF_Y(7), CB_OFF_Z(7)\n"
                  "PARAMETER INTEGER :: NZ = 9\nPARAMETER REAL :: ZIP_K = 1.00\n"
                  "STATIC INTEGER :: ZA(NZ), ZB(NZ)\nSTATIC REAL :: ZR0(NZ), DMIN")
    (OUT / out_name).write_text(s)
    print(f"wrote {out_name} ({len(pairs)} ladder pairs, mode={mode}, K={k})")


build("_AMIDE_K001", "0.001", "normal", "amide_k001.ergo")
build("_AMIDE_K002", "0.002", "normal", "amide_k002.ergo")
build("_AMIDE_K004", "0.004", "normal", "amide_k004.ergo")
build("_AMIDE_K008", "0.008", "normal", "amide_k008.ergo")
build("_AMIDE_SCR_TYPE", "0.004", "type", "amide_scramble_type.ergo")
build("_AMIDE_SCR_REG", "0.004", "reg", "amide_scramble_reg.ergo")

# close-start variants (5 units between chain starts): the ladder well
# engages at D<~5 u, so this tests register discrimination at contact.
# The far-start versions above never engage (sheets stay 16-22 u apart)
# — that diffusion limit is itself a reported result.
build("_AMIDE_K004_CLOSE", "0.004", "normal", "amide_k004_close.ergo", spacing=5.0)
build("_AMIDE_K008_CLOSE", "0.008", "normal", "amide_k008_close.ergo", spacing=5.0)
build("_AMIDE_SCR_TYPE_CLOSE", "0.004", "type", "amide_scramble_type_close.ergo", spacing=5.0)
build("_AMIDE_SCR_REG_CLOSE", "0.004", "reg", "amide_scramble_reg_close.ergo", spacing=5.0)


# ── face-start variants: sheets AT contact distance (crystal facing
# geometry, no zipper contacts). sheet2_yoff = register offset applied
# to sheet 2 (0 = correct register, 1.9468 = off by one residue).
# This isolates the register-discrimination question from diffusion
# (the sim's timescale cannot show diffusional encounter — documented).
ORACLE_CA = json.load(open("/tmp/yjp_model.json"))["chainA"]


def _screw(p):
    return (-p[0], p[1] + 0.9734, -p[2])


def face_inits(sheet2_yoff):
    B = 1.9468
    s0 = [_screw(p) for p in ORACLE_CA]
    chains = [
        [(x, y, z) for x, y, z in ORACLE_CA],
        [(x, y + B, z) for x, y, z in ORACLE_CA],
        [(x, y + sheet2_yoff, z) for x, y, z in s0],
        [(x, y + B + sheet2_yoff, z) for x, y, z in s0],
    ]
    out = []
    for c, ch in enumerate(chains):
        lines = [f"\n  ! Chain {c+1}: face-start, sheet2 offset {sheet2_yoff:.4f}"]
        for k, (x, y, z) in enumerate(ch):
            lines.append(f"  RES_X({c*7+k+1}) := {x:.6f}")
            lines.append(f"  RES_Y({c*7+k+1}) := {y:.6f}")
            lines.append(f"  RES_Z({c*7+k+1}) := {z:.6f}")
        lines.append("  DO I = 1, NRES")
        lines.append(f"    RES_VX({c*7} + I) := 0.0")
        lines.append(f"    RES_VY({c*7} + I) := 0.0")
        lines.append(f"    RES_VZ({c*7} + I) := 0.0")
        lines.append("  ENDDO")
        out.append("\n".join(lines))
    return out


build("_AMIDE_FACE_K004", "0.004", "normal", "amide_face_k004.ergo",
      custom_inits=face_inits(0.0))
build("_AMIDE_FACE_OFF1_K004", "0.004", "normal", "amide_face_off1_k004.ergo",
      custom_inits=face_inits(1.9468))
build("_AMIDE_FACE_OFF1_K008", "0.008", "normal", "amide_face_off1_k008.ergo",
      custom_inits=face_inits(1.9468))
build("_AMIDE_FACE_OFF1_SCRTYPE", "0.004", "type", "amide_face_off1_scrtype.ergo",
      custom_inits=face_inits(1.9468))
build("_AMIDE_FACE_OFF1_SCRREG", "0.004", "reg", "amide_face_off1_scrreg.ergo",
      custom_inits=face_inits(1.9468))
