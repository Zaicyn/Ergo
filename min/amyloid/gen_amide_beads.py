#!/usr/bin/env python3
"""gen_amide_beads.py — hybrid Cα + explicit amide-bead model.

EXTRACTED BOND MACHINERY (from tests/waveform_molecule_dynamics_geometric_strain.ergo,
documented in bead_check.md):
  element tables: radius C .76 H .31 O .66 N .71; homonuclear depth
    C 1.00 H 1.25 O 0.42 N 0.46; valence C4 H1 O2 N3; angle K
    C .35 O .25 N .30; angle targets C 109.47 O 104.45 N 107.3 deg
  combining rules: r0(A,B,BO)=(rA+rB)(1-0.12(BO-1)),
    D(A,B,BO)=sqrt(D_AA*D_BB)(1+0.8(BO-1))
  Morse: E = D(g^2-2g), g = exp(-a(r-r0)), a=1.0
  formation: distance < 2.5 AND phase alignment > 0.80 AND valence free
  breaking: stress > 0.05 / order 0 / angle strain > 0.5 / out of range
  angle: E = k(cos t - cos t0)^2 with analytic gradient
  SIMPLIFICATION for the hybrid (documented): the protein sims have no
  phase machinery, so formation is DISTANCE-gated with a greedy
  valence-1 rule (each amide O bonds its closest free N in range),
  keeping typed Morse + valence + angle terms from the molecule
  framework. Geometric-mean depth adapted: D_HB bracketed 0.1/0.2/0.4
  (the covalent-mean 0.44 is the top of the bracket; H-bonds are
  weaker than covalent).

HYBRID: 4 chains x 7 Cα (proven amyloid force field, in-register
contacts within sheets) + 40 amide beads (per polar residue 2-6: one N
bead, one O bead). Each amide group is a rigid-ish triangle of stiff
Morse tethers at PER-RESIDUE crystal values (1YJP):
  Asn: CA-N 1.37-1.41, CA-O 1.19-1.23, N-O 0.90-0.91
  Gln: CA-N 1.92-1.98, CA-O 1.73-1.74, N-O 0.91
H-bond: N..O across sheets, Morse D = HB_D, r0 = 1.341 u (3.353 A, the
measured A2.ND2-S6.OD1 H-bond), a = 3.0 (narrow); valence 1 per bead
(greedy closest-in-range 1.8 u); directionality angle terms at donor
(CA-N..O) and acceptor (CA-O..N) with 90 deg target (crystal mean
92.7/94.5 of the two true H-bonds).

Tests: face start correct / off-by-one / far (coils) / scramble
(beads on G1,Y7 instead of N/Q).
"""

import json
import math
from pathlib import Path

import gen_amyloid as G  # re-emits base files (deterministic); reuse

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "min" / "amyloid"

SCALE = 1.52 / 3.7993
ORACLE = json.load(open("/tmp/yjp_model.json"))
CA = ORACLE["chainA"]
B = 1.9468

# per-residue amide geometry from 1YJP (measured, model units):
# res -> (type, CA-N, CA-O, N-O, offN(x,y,z), offO(x,y,z))
AMIDE = {
    2: ("N", 1.377, 1.189, 0.908, (-0.6729, 0.0468, -1.2002), (-0.6013, -0.7245, -0.7261)),
    3: ("N", 1.414, 1.229, 0.906, (0.7689, -0.4757, 1.0870), (0.5965, 0.4085, 0.9934)),
    4: ("Q", 1.981, 1.742, 0.917, (0.9466, -0.2909, -1.7163), (0.9442, 0.5521, -1.3558)),
    5: ("Q", 1.918, 1.726, 0.907, (-0.6885, 0.3305, 1.7599), (-0.9986, -0.4145, 1.3450)),
    6: ("N", 1.369, 1.215, 0.892, (-0.6545, 0.5749, -1.0558), (-0.4133, -0.2825, -1.1070)),
}
POLAR = [2, 3, 4, 5, 6]
# scramble control: pseudo-amide beads on G1/Y7 (physically meaningless —
# that is the point of the control), reusing the Gln geometry
AMIDE[1] = AMIDE[4]
AMIDE[7] = AMIDE[4]

BEAD_DECLS = """! ── Amide beads (hybrid layer) ──────────────────────────────────
PARAMETER INTEGER :: NB = 40
PARAMETER INTEGER :: NTETH = 60
PARAMETER REAL :: HB_D = __HBD__
PARAMETER REAL :: HB_R0 = 1.3410
PARAMETER REAL :: HB_A = 3.0
PARAMETER REAL :: HB_RANGE = 1.8
PARAMETER REAL :: HB_ANGK = 0.3
STATIC REAL :: BEAD_X(NB), BEAD_Y(NB), BEAD_Z(NB)
STATIC REAL :: BEAD_VX(NB), BEAD_VY(NB), BEAD_VZ(NB)
STATIC INTEGER :: BEAD_PARENT(NB)
STATIC INTEGER :: TETH_A(NTETH), TETH_B(NTETH)
STATIC REAL :: TETH_R0(NTETH)
STATIC INTEGER :: HB_PART(20), HB_NUSED(20)
STATIC INTEGER :: NHB, BEST
STATIC REAL :: DMIN2
"""

BEAD_SECTIONS = """  ! ── bead thermal kicks ──
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

  ! ── H-bond formation: greedy valence-1, distance-gated,
  !    INTER-SHEET only (same-amide and same-sheet pairs excluded —
  !    intra-sheet binding is provided by the in-register contacts) ──
  DO K = 1, 20
    HB_PART(K) := 0
    HB_NUSED(K) := 0
  ENDDO
  DO K = 1, 20
    DMIN2 := 1.0E9
    BEST := 0
    DO M = 1, 20
      IF HB_NUSED(M) = 0 .AND. INT((K - 1) / 10) /= INT((M - 1) / 10) THEN
        D := SQRT((BEAD_X(2*K-1) - BEAD_X(2*M))**2 + (BEAD_Y(2*K-1) - BEAD_Y(2*M))**2 + (BEAD_Z(2*K-1) - BEAD_Z(2*M))**2)
        IF D < HB_RANGE .AND. D < DMIN2 THEN
          DMIN2 := D
          BEST := M
        ENDIF
      ENDIF
    ENDDO
    IF BEST > 0 THEN
      HB_PART(K) := BEST
      HB_NUSED(BEST) := 1
    ENDIF
  ENDDO

  ! ── H-bond Morse forces (narrow well, typed N..O) ──
  DO K = 1, 20
    IF HB_PART(K) > 0 THEN
      IA := 2 * K - 1
      IB := 2 * HB_PART(K)
      DX := BEAD_X(IA) - BEAD_X(IB)
      DY := BEAD_Y(IA) - BEAD_Y(IB)
      DZ := BEAD_Z(IA) - BEAD_Z(IB)
      D := SQRT(DX*DX + DY*DY + DZ*DZ)
      IF D > 0.0 THEN
        E := EXP(-HB_A * (D - HB_R0))
        FM := -2.0 * HB_D * HB_A * (1.0 - E) * E * FORCE_SCALE
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

HB_MEASURE = """! H-bond list + count
NHB := 0
DO K = 1, 20
  IF HB_PART(K) > 0 THEN
    NHB := NHB + 1
  ENDIF
ENDDO
WRITE(*, "NHB_FINAL %d") NHB
DO K = 1, 20
  IF HB_PART(K) > 0 THEN
    IA := 2 * K - 1
    IB := 2 * HB_PART(K)
    D := SQRT((BEAD_X(IA) - BEAD_X(IB))**2 + (BEAD_Y(IA) - BEAD_Y(IB))**2 + (BEAD_Z(IA) - BEAD_Z(IB))**2)
    WRITE(*, "HB %d %d %.4f") IA, IB, D
  ENDIF
ENDDO
"""

HB_TRACE = """  ! H-bond count trace
  IF MOD(FRAME, 200) = 0 THEN
    NHB := 0
    DO K = 1, 20
      IF HB_PART(K) > 0 THEN
        NHB := NHB + 1
      ENDIF
    ENDDO
    WRITE(*, "HBTRACE %d %d") FRAME, NHB
  ENDIF
"""


def screw(p):
    return (-p[0], p[1] + 0.9734, -p[2])


def build(tag, hbd, start, yoff, scramble, out_name):
    s = G.TEMPLATE.replace("__TAG__", tag).replace("__NC__", "4")
    s = s.replace("__NTOT__", "28").replace("__NCON__", "14")
    s = s.replace("__ICONTACTS__", G.ICONTACTS)
    s = s.replace("__INTRAGO__", "")
    s = s.replace("DO C = 1, NC - 1\n      D := 0.0", "DO C = 1, NC - 1, 2\n      D := 0.0")
    s = s.replace("DO C = 1, NC - 1\n  DO K = 1, NRES", "DO C = 1, NC - 1, 2\n  DO K = 1, NRES")
    # bead declarations
    s = s.replace("STATIC REAL :: IC_R0(NCON)",
                  "STATIC REAL :: IC_R0(NCON)\n" + BEAD_DECLS.replace("__HBD__", hbd))
    # working scalars for angle math
    s = s.replace("STATIC REAL :: U1, U2, COSTH, SINTH, PHI2, CANDX, CANDY, CANDZ, DD",
                  "STATIC REAL :: U1, U2, COSTH, SINTH, PHI2, CANDX, CANDY, CANDZ, DD\n"
                  "STATIC INTEGER :: IA2, IB2\n"
                  "STATIC REAL :: FX, FY, FZ")
    # bead sections: insert before chain damping
    s = s.replace("  ! Velocity damping (per-chain VDAMP: template chains strongly damped)",
                  BEAD_SECTIONS + "\n  ! Velocity damping (per-chain VDAMP: template chains strongly damped)")
    # HB trace before the chain-pair TRACE block
    s = s.replace("  ! Trace: mean in-register distance per adjacent chain pair",
                  HB_TRACE + "\n  ! Trace: mean in-register distance per adjacent chain pair")
    # HB list before COM block
    s = s.replace("DO C = 1, NC\n  CX := 0.0", HB_MEASURE + "\nDO C = 1, NC\n  CX := 0.0")

    # init tables
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

    # bead init: tethers (Cα parent = -index; bead-bead = +index) + positions
    res_list = [1, 7] if scramble else POLAR
    teth, bpos, bparent = [], [], []
    kb = 0
    for c in range(4):
        for r in res_list:
            kb += 2  # O bead kb-1, N bead kb
            ca_idx = c * 7 + r
            teth.append(f"  TETH_A({len(teth)+1}) := {0 - ca_idx}\n  TETH_B({len(teth)+1}) := {kb-1}\n  TETH_R0({len(teth)+1}) := {AMIDE[r][1]:.4f}")
            teth.append(f"  TETH_A({len(teth)+1}) := {0 - ca_idx}\n  TETH_B({len(teth)+1}) := {kb}\n  TETH_R0({len(teth)+1}) := {AMIDE[r][2]:.4f}")
            teth.append(f"  TETH_A({len(teth)+1}) := {kb-1}\n  TETH_B({len(teth)+1}) := {kb}\n  TETH_R0({len(teth)+1}) := {AMIDE[r][3]:.4f}")
            bparent.append(f"  BEAD_PARENT({kb-1}) := {ca_idx}")
            bparent.append(f"  BEAD_PARENT({kb}) := {ca_idx}")
            bpos.append((kb - 1, c, r, "O"))
            bpos.append((kb, c, r, "N"))
    # NTETH check
    n_teth_expected = len(res_list) * 4 * 3
    assert len(teth) == n_teth_expected, (len(teth), n_teth_expected)

    # chain + bead positions
    s0 = [screw(p) for p in CA]
    if start == "face":
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
        for kb2, c, r, t in bpos:
            off = AMIDE[r][4] if t == "N" else AMIDE[r][5]
            cx, cy, cz = chains[c][r - 1]
            blines.append(f"  BEAD_X({kb2}) := {cx + off[0]:.6f}")
            blines.append(f"  BEAD_Y({kb2}) := {cy + off[1]:.6f}")
            blines.append(f"  BEAD_Z({kb2}) := {cz + off[2]:.6f}")
            blines.append(f"  BEAD_VX({kb2}) := 0.0")
            blines.append(f"  BEAD_VY({kb2}) := 0.0")
            blines.append(f"  BEAD_VZ({kb2}) := 0.0")
        init_lines.append("\n".join(blines))
    else:  # coils
        init_lines = [G.coil_chain_lines(c + 1, f"{c * 1.0:.1f}") for c in range(4)]
        # beads at parent coil + offset (crude start, tethers re-equilibrate)
        blines = ["  DO I = 1, NB\n    BEAD_VX(I) := 0.0\n    BEAD_VY(I) := 0.0\n    BEAD_VZ(I) := 0.0\n  ENDDO"]
        for kb2, c, r, t in bpos:
            off = AMIDE[r][4] if t == "N" else AMIDE[r][5]
            blines.append(f"  BEAD_X({kb2}) := RES_X({c*7+r}) + {off[0]:.6f}")
            blines.append(f"  BEAD_Y({kb2}) := RES_Y({c*7+r}) + {off[1]:.6f}")
            blines.append(f"  BEAD_Z({kb2}) := RES_Z({c*7+r}) + {off[2]:.6f}")
        init_lines.append("\n".join(blines))

    init_body = "\n".join([angk, angt, torsk, torsp, hydro, vd, ""] + ic_lines
                          + teth + bparent + init_lines)
    s = s.replace("CALL INIT_ALL()", init_body)
    (OUT / out_name).write_text(s)
    print(f"wrote {out_name} (HB_D={hbd}, start={start}, yoff={yoff}, scramble={scramble})")


build("_BEAD_FACE_K02", "0.2", "face", 0.0, False, "bead_face_k02.ergo")
build("_BEAD_FACE_K01", "0.1", "face", 0.0, False, "bead_face_k01.ergo")
build("_BEAD_FACE_K04", "0.4", "face", 0.0, False, "bead_face_k04.ergo")
build("_BEAD_FACE_OFF1_K02", "0.2", "face", 1.9468, False, "bead_face_off1_k02.ergo")
build("_BEAD_FAR_K02", "0.2", "coil", 0.0, False, "bead_far_k02.ergo")
build("_BEAD_SCRAMBLE_K02", "0.2", "face", 0.0, True, "bead_face_scramble_k02.ergo")
