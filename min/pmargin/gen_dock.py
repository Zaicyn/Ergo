#!/usr/bin/env python3
"""gen_dock.py — fold-then-dock for SdrD: assemble the 556-residue
full chain from pre-folded domains and run the docking dynamics.

Base: sdrd_white_full.ergo (validated packed white-bath full-construct
program; same field, schedule, seeds; only init, damping, tether, and
diagnostics change). Two variants:

  dock_oracle.ergo — domains initialized at their native PDB internal
    geometry (cleanest test: is the interface field sufficient when the
    domains are perfect?).
  dock_sim.ergo — domains initialized at their best per-domain sim folds
    (sdrd_white_*_struct.out: A2 block 8 = 3.38, A3 block 7 = 2.38,
    B1 block 1 = 0.91, B2 block 7 = 1.82), each Kabsch-aligned onto its
    native domain frame (done here offline; per-domain native slices
    verified identical to the full-chain native).

Assembly (both variants): each domain's internal geometry is preserved
rigidly; domain COMs are spread along a per-block white-hash direction
by DSEP=10.0*(D-2.5) model units from the chain COM, so inter-domain
backbone bonds start stretched ~10 units (docking must close them).

Docking dynamics (what the sim supports — documented):
- Per-residue velocity damping RES_VD (amyloid damped-template pattern,
  amyloid_trimer.ergo): 0.5 = strong damping on all domain beads
  (template holds its fold; drifts slowly), 0.9 = normal on the
  interface windows ±3 residues around each boundary
  (150-156, 318-324, 438-444) — the "live linkers". The sim has no
  rigid-body domain DOF; per-bead damping is the implementable
  approximation, exactly the amyloid pattern.
- Backbone tether continuation (the adopted field improvement from
  tether_check.md): harmonic K_LR = 0.3 past D = 4.0 added to the Morse
  kernel — required here because the assembly start stretches the
  inter-domain bonds to ~10 units, deep in the old Morse plateau.
- Same heat schedule (cycles to 1200, floor, quench 38400, 48000
  frames) and white bath as the validated full run.

Diagnostics added: IFACE rows (per block: cross-domain native-contact
count, mean/max |D-R0|, satisfied<0.5) and DTRACE rows (block 1 every
1000 frames: full + per-domain RMSD trajectory — the domain-integrity
differential). Existing FINAL/DOM rows unchanged.
"""

from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"
NRES = 556
DOMS = ((1, 152), (153, 320), (321, 440), (441, 556))
BEST = {"A2": 8, "A3": 7, "B1": 1, "B2": 7}

# ── best sim folds, Kabsch-aligned to the native domain frames ────────
def get_block(out_file, block, nres):
    lines = open(out_file).read().splitlines()
    i = lines.index(f"FINAL_STRUCTURE_B {block}")
    cur, nat = [], []
    for line in lines[i + 1:i + 1 + nres]:
        p = line.split(",")
        cur.append([float(p[1]), float(p[2]), float(p[3])])
        nat.append([float(p[4]), float(p[5]), float(p[6])])
    return np.array(cur), np.array(nat)

def kabsch_onto(X, Y):
    Xc, Yc = X - X.mean(0), Y - Y.mean(0)
    V, S, Wt = np.linalg.svd(Xc.T @ Yc)
    D = np.diag([1.0, 1.0, np.sign(np.linalg.det(V @ Wt))])
    return Xc @ (V @ D @ Wt) + Y.mean(0)

dock = np.zeros((NRES, 3))
native_full = np.zeros((NRES, 3))
for (lo, hi), dom in zip(DOMS, ("A2", "A3", "B1", "B2")):
    X, N = get_block(PM / f"sdrd_white_{dom}_struct.out", BEST[dom], hi - lo + 1)
    dock[lo - 1:hi] = kabsch_onto(X, N)
    native_full[lo - 1:hi] = N
    # consistency: per-domain native == full-chain native slice
print("assembled sim-dock table; per-domain Kabsch rmsd of the folds:")
for (lo, hi), dom in zip(DOMS, ("A2", "A3", "B1", "B2")):
    d = dock[lo - 1:hi] - native_full[lo - 1:hi]
    print(f"  {dom}: {np.sqrt((d ** 2).sum(1).mean()):.3f}")

# ── base program surgery ─────────────────────────────────────────────
base = (PM / "sdrd_white_full.ergo").read_text()

DECL_ANCHOR = "STATIC INTEGER :: H\n"
DECL_ADD = """STATIC INTEGER :: H
STATIC REAL :: DOCK_X(556), DOCK_Y(556), DOCK_Z(556)
STATIC REAL :: RES_VD(4448)
"""
assert DECL_ANCHOR in base
t = base.replace(DECL_ANCHOR, DECL_ADD, 1)

# damping site -> per-residue RES_VD
DAMP_OLD = """    DO I = 1, NRES
      RES_VX(OFF + I) := RES_VX(OFF + I) * VELOCITY_DAMP
      RES_VY(OFF + I) := RES_VY(OFF + I) * VELOCITY_DAMP
      RES_VZ(OFF + I) := RES_VZ(OFF + I) * VELOCITY_DAMP
    ENDDO"""
DAMP_NEW = """    DO I = 1, NRES
      RES_VX(OFF + I) := RES_VX(OFF + I) * RES_VD(OFF + I)
      RES_VY(OFF + I) := RES_VY(OFF + I) * RES_VD(OFF + I)
      RES_VZ(OFF + I) := RES_VZ(OFF + I) * RES_VD(OFF + I)
    ENDDO"""
assert DAMP_OLD in t
t = t.replace(DAMP_OLD, DAMP_NEW, 1)

# tether continuation in the packed Morse kernel (K_LR = 0.3 past 4.0)
MORSE_OLD = """      E := EXP(-MORSE_A * (D - BACKBONE_R0))
      FM := -2.0 * BACKBONE_D * MORSE_A * (1.0 - E) * E * FORCE_SCALE
"""
MORSE_NEW = """      E := EXP(-MORSE_A * (D - BACKBONE_R0))
      FM := -2.0 * BACKBONE_D * MORSE_A * (1.0 - E) * E * FORCE_SCALE
      IF D > 4.0 THEN
        FM := FM - 2.0 * 0.3 * (D - 4.0) * FORCE_SCALE
      ENDIF
"""
assert MORSE_OLD in t
t = t.replace(MORSE_OLD, MORSE_NEW, 1)

# init: replace the INIT_COIL loop with table load + assembly
INIT_OLD = """CALL INIT_SHARED()
DO B = 1, NBLK
  OFF := (B - 1) * NRES
  CALL INIT_COIL(OFF, SEED_TAB(B))
ENDDO
CALL INIT_TABLES()"""
INIT_NEW = """CALL INIT_SHARED()
CALL SET_DOCK_TABLES()
DO B = 1, NBLK
  OFF := (B - 1) * NRES
  CALL INIT_ASSEMBLY(OFF, SEED_TAB(B))
ENDDO
CALL INIT_TABLES()
CALL INIT_VD()"""
assert INIT_OLD in t
t = t.replace(INIT_OLD, INIT_NEW, 1)

# DTRACE: per-domain RMSD trajectory for block 1 every 1000 frames
TRACE_OLD = """  IF MOD(FRAME, 500) = 0 THEN
    DO B = 1, NBLK
      IF B = 1 .OR. B = 2 .OR. B = 5 THEN
        OFF := (B - 1) * NRES
        CALL COMPUTE_RMSD(OFF)
        WRITE(*, "TRACE %d %.1f %d %.4f") B, SEED_TAB(B), FRAME, RMSD_NATIVE
      ENDIF
    ENDDO
  ENDIF"""
TRACE_NEW = TRACE_OLD + """
  IF MOD(FRAME, 1000) = 0 THEN
    OFF := 0
    CALL COMPUTE_RMSD(OFF)
    TR_FULL := RMSD_NATIVE
    CALL COMPUTE_RMSD_RANGE(OFF, 1, 152, 152)
    TR_D1 := RMSD_NATIVE
    CALL COMPUTE_RMSD_RANGE(OFF, 153, 320, 168)
    TR_D2 := RMSD_NATIVE
    CALL COMPUTE_RMSD_RANGE(OFF, 321, 440, 120)
    TR_D3 := RMSD_NATIVE
    CALL COMPUTE_RMSD_RANGE(OFF, 441, 556, 116)
    TR_D4 := RMSD_NATIVE
    WRITE(*, "DTRACE %d %.4f %.4f %.4f %.4f %.4f") FRAME, TR_FULL, TR_D1, TR_D2, TR_D3, TR_D4
  ENDIF"""
assert TRACE_OLD in t
t = t.replace(TRACE_OLD, TRACE_NEW, 1)

# IFACE report after the DOM rows
DOM_ANCHOR = """DO B = 1, NBLK
  WRITE(*, "DOM %d %.1f %.4f %.4f %.4f %.4f %.4f") &
    B, SEED_TAB(B), RMSD_B(B), RMSD_D1(B), RMSD_D2(B), RMSD_D3(B), RMSD_D4(B)
ENDDO"""
IFACE = DOM_ANCHOR + """
! cross-domain native-contact report (interface geometry)
DO B = 1, NBLK
  OFF := (B - 1) * NRES
  NCX := 0
  SX := 0.0
  MX := 0.0
  NSAT := 0
  DO I = 1, NRES - 3
    DO J = I + 3, NRES
      IF NATIVE_CONTACT(I, J) = 1 THEN
        IF (I <= 152 .AND. J > 152) .OR. (I <= 320 .AND. J > 320) .OR. (I <= 440 .AND. J > 440) THEN
          DX := RES_X(OFF + I) - RES_X(OFF + J)
          DY := RES_Y(OFF + I) - RES_Y(OFF + J)
          DZ := RES_Z(OFF + I) - RES_Z(OFF + J)
          DD := ABS(SQRT(DX*DX + DY*DY + DZ*DZ) - NATIVE_R0(I, J))
          NCX := NCX + 1
          SX := SX + DD
          IF DD > MX THEN
            MX := DD
          ENDIF
          IF DD < 0.5 THEN
            NSAT := NSAT + 1
          ENDIF
        ENDIF
      ENDIF
    ENDDO
  ENDDO
  WRITE(*, "IFACE %d %d %.4f %.4f %d") B, NCX, SX / REAL(NCX), MX, NSAT
ENDDO"""
assert DOM_ANCHOR in t
t = t.replace(DOM_ANCHOR, IFACE, 1)

# statics for the new diagnostics
DECL2_ANCHOR = "STATIC REAL :: RMSD_D1(8)"
assert DECL2_ANCHOR in t
t = t.replace(DECL2_ANCHOR, DECL2_ANCHOR + "\nSTATIC REAL :: TR_FULL, TR_D1, TR_D2, TR_D3, TR_D4, SX, MX, DD\nSTATIC INTEGER :: NCX, NSAT", 1)

# ── new subroutines (appended before INIT_TABLES) ────────────────────
SUBS = """
! ════════════════════════════════════════════════════════════
! INIT_VD: per-residue damping — 0.5 strong (domain template),
! 0.9 normal on interface windows ±3 around each boundary
! ════════════════════════════════════════════════════════════

SUBROUTINE INIT_VD()
  DO I = 1, NPTS
    RES_VD(I) := 0.5
  ENDDO
  DO B = 1, NBLK
    OFF := (B - 1) * NRES
    DO I = 150, 156
      RES_VD(OFF + I) := 0.9
    ENDDO
    DO I = 318, 324
      RES_VD(OFF + I) := 0.9
    ENDDO
    DO I = 438, 444
      RES_VD(OFF + I) := 0.9
    ENDDO
  ENDDO
END

! ════════════════════════════════════════════════════════════
! INIT_ASSEMBLY: place pre-folded domains (DOCK tables), zero
! velocities, then spread domain COMs by 10*(D-2.5) along a per-block
! white-hash direction — inter-domain bonds start stretched ~10 units
! ════════════════════════════════════════════════════════════

SUBROUTINE INIT_ASSEMBLY(OFFB, SEEDB)
  INTEGER :: OFFB
  REAL :: SEEDB
  INTEGER :: I, D, LO, HI
  REAL :: CX, CY, CZ, GX, GY, GZ, DX2, DY2, DZ2, DN
  DO I = 1, NRES
    RES_X(OFFB + I) := DOCK_X(I)
    RES_Y(OFFB + I) := DOCK_Y(I)
    RES_Z(OFFB + I) := DOCK_Z(I)
    RES_VX(OFFB + I) := 0.0
    RES_VY(OFFB + I) := 0.0
    RES_VZ(OFFB + I) := 0.0
    RES_THETA(OFFB + I) := 0.3 * RES_X(OFFB + I) + 0.5 * RES_Y(OFFB + I) + 0.7 * RES_Z(OFFB + I) + SEEDB
    RES_OMEGA(OFFB + I) := BASE_OMEGA + 0.5 * SIN(RES_THETA(OFFB + I))
  ENDDO
  H := IEOR(INT(SEEDB * 1000.0) * 2654435761, 777)
  H := IEOR(H, ISHFT(H, -30))
  H := H * 6364136223846793005
  H := IEOR(H, ISHFT(H, -27))
  H := H * 6364136223846793005
  H := IEOR(H, ISHFT(H, -31))
  DX2 := REAL(IAND(H, 65535)) / 65535.0 - 0.5
  H := IEOR(H, ISHFT(H, -17))
  DY2 := REAL(IAND(H, 65535)) / 65535.0 - 0.5
  H := IEOR(H, ISHFT(H, -7))
  DZ2 := REAL(IAND(H, 65535)) / 65535.0 - 0.5
  DN := SQRT(DX2*DX2 + DY2*DY2 + DZ2*DZ2)
  DX2 := DX2 / DN
  DY2 := DY2 / DN
  DZ2 := DZ2 / DN
  GX := 0.0
  GY := 0.0
  GZ := 0.0
  DO I = 1, NRES
    GX := GX + RES_X(OFFB + I)
    GY := GY + RES_Y(OFFB + I)
    GZ := GZ + RES_Z(OFFB + I)
  ENDDO
  GX := GX / REAL(NRES)
  GY := GY / REAL(NRES)
  GZ := GZ / REAL(NRES)
  DO D = 1, 4
    IF D = 1 THEN
      LO := 1
      HI := 152
    ENDIF
    IF D = 2 THEN
      LO := 153
      HI := 320
    ENDIF
    IF D = 3 THEN
      LO := 321
      HI := 440
    ENDIF
    IF D = 4 THEN
      LO := 441
      HI := 556
    ENDIF
    CX := 0.0
    CY := 0.0
    CZ := 0.0
    DO I = LO, HI
      CX := CX + RES_X(OFFB + I)
      CY := CY + RES_Y(OFFB + I)
      CZ := CZ + RES_Z(OFFB + I)
    ENDDO
    CX := CX / REAL(HI - LO + 1)
    CY := CY / REAL(HI - LO + 1)
    CZ := CZ / REAL(HI - LO + 1)
    DO I = LO, HI
      RES_X(OFFB + I) := RES_X(OFFB + I) - CX + GX + DX2 * 10.0 * (REAL(D) - 2.5)
      RES_Y(OFFB + I) := RES_Y(OFFB + I) - CY + GY + DY2 * 10.0 * (REAL(D) - 2.5)
      RES_Z(OFFB + I) := RES_Z(OFFB + I) - CZ + GZ + DZ2 * 10.0 * (REAL(D) - 2.5)
    ENDDO
  ENDDO
END

"""
UT_ANCHOR = ("! ════════════════════════════════════════════════════════════\n"
             "! INIT_TABLES: build block-aware packed index tables (offsets baked)")
assert UT_ANCHOR in t
t = t.replace(UT_ANCHOR, SUBS + UT_ANCHOR, 1)

# ── variant emission ─────────────────────────────────────────────────
def emit(name, set_tables_body, note):
    x = t
    x = x.replace("! PACKED_SDRD_FULL_WHITE", f"! PACKED_SDRD_FULL_WHITE_DOCK — {note}")
    subs = ("\n! ════════════════════════════════════════════════════════════\n"
            "! SET_DOCK_TABLES: assembled pre-folded domain coordinates\n"
            "! ════════════════════════════════════════════════════════════\n\n"
            "SUBROUTINE SET_DOCK_TABLES()\n" + set_tables_body + "END\n\n")
    anchor = ("! ════════════════════════════════════════════════════════════\n"
              "! INIT_VD: per-residue damping")
    assert anchor in x
    x = x.replace(anchor, subs + anchor, 1)
    out = PM / f"{name}.ergo"
    out.write_text(x)
    print(f"wrote {out} ({len(x.splitlines())} lines)")

oracle_body = """  INTEGER :: I
  DO I = 1, NRES
    DOCK_X(I) := NATIVE_X(I)
    DOCK_Y(I) := NATIVE_Y(I)
    DOCK_Z(I) := NATIVE_Z(I)
  ENDDO
"""
emit("dock_oracle", oracle_body, "ORACLE-DOCK: domains at native PDB internal geometry")

lines = ["  INTEGER :: I"]
for i in range(NRES):
    lines.append(f"  DOCK_X({i + 1}) := {dock[i, 0]:.6f}")
    lines.append(f"  DOCK_Y({i + 1}) := {dock[i, 1]:.6f}")
    lines.append(f"  DOCK_Z({i + 1}) := {dock[i, 2]:.6f}")
emit("dock_sim", "\n".join(lines) + "\n",
     "SIM-DOCK: domains at best per-domain sim folds (A2 b8 3.38, A3 b7 2.38, B1 b1 0.91, B2 b7 1.82)")
