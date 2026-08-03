#!/usr/bin/env python3
"""gen_condensate_hot.py — reaching Tc: hot ladder + stronger confinement.

Same system as gen_condensate_n.py (GNNQQNY chains, ATT_K = 0.005 per
pair constant, R ∝ N^(1/3), same metrics) with:
  - TMULS = {4, 8, 10, 15, 20, 25, 30, 40}: the 6 hot rungs from the
    task plus 2 sub-Tc anchors (4, 8) for the binodal curve below Tc.
    T = TMUL x 0.01 in sim noise units (0.04..0.40).
  - CONF_K = 0.05 (was 0.01) to hold the hot vapor. Pre-check at the
    hottest rung: implied cluster radius must stay near/below R_BOX;
    if the cloud escapes (as at T=0.1/CONF_K=0.01 in the scaling run),
    CONF_K is raised to 0.1 and the failure is documented.
Outputs: condensate_hot48.ergo (N=48), condensate_hot96.ergo (N=96).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "amyloid"))

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "min" / "condensate"

import gen_condensate as GC

G = GC.G
TMULS = [4.0, 8.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0]


def grid_for(n):
    nx = ny = nz = 1
    while nx * ny * nz < n:
        if nx <= ny and nx <= nz:
            nx += 1
        elif ny <= nz:
            ny += 1
        else:
            nz += 1
    pts = []
    for gx in range(nx):
        for gy in range(ny):
            for gz in range(nz):
                pts.append((30.0 + (gx - (nx - 1) / 2) * 5.0,
                            30.0 + (gy - (ny - 1) / 2) * 5.0,
                            30.0 + (gz - (nz - 1) / 2) * 5.0))
    return pts[:n]


def build(n, conf_k, out_name):
    npb = 7 * n
    ntot = 8 * npb
    r_box = 18.0 * (n / 24.0) ** (1.0 / 3.0)
    grid = grid_for(n)

    angk = "\n".join(f"  RES_ANGK({i+1}) := 0.3000" for i in range(7))
    angt = "\n".join(f"  RES_ANGT0({i+1}) := {G.ANG_T0[i]:.6f}" for i in range(7))
    torsk = "\n".join(f"  RES_TORSK({i+1}) := 0.2000" for i in range(7))
    torsp = "\n".join(f"  RES_TORSP0({i+1}) := {G.TORS_P0[i]:.6f}" for i in range(7))
    tb = "\n".join(f"  TB({b+1}) := {0.01 * m:.5f}   ! TMUL {m}" for b, m in enumerate(TMULS))

    inits = []
    for b in range(8):
        for c in range(n):
            lines = G.coil_chain_lines(c + 1, f"{(c % 24) * 1.0:.1f}")
            base_local = c * 7
            base_global = b * npb + base_local
            lines = lines.replace(f"RES_X({base_local + 1}) := {10.0 + c * 10.0}",
                                  f"RES_X({base_global + 1}) := {grid[c][0]}")
            lines = lines.replace(f"RES_Y({base_local + 1}) := 10.0",
                                  f"RES_Y({base_global + 1}) := {grid[c][1]}")
            lines = lines.replace(f"RES_Z({base_local + 1}) := 10.0",
                                  f"RES_Z({base_global + 1}) := {grid[c][2]}")
            for comp in "XYZ":
                lines = lines.replace(f"RES_{comp}({base_local} + I", f"RES_{comp}({base_global} + I")
                lines = lines.replace(f"RES_{comp}({base_local} + J2", f"RES_{comp}({base_global} + J2")
            inits.append(lines)

    init_body = "\n".join([angk, angt, torsk, torsp, tb, ""] + inits)

    s = GC.TEMPLATE
    s = s.replace("PARAMETER INTEGER :: NCH = 24", f"PARAMETER INTEGER :: NCH = {n}")
    s = s.replace("PARAMETER INTEGER :: NPB = 168", f"PARAMETER INTEGER :: NPB = {npb}")
    s = s.replace("PARAMETER INTEGER :: NTOT = 1344", f"PARAMETER INTEGER :: NTOT = {ntot}")
    s = s.replace("PARAMETER REAL :: R_BOX = 18.0", f"PARAMETER REAL :: R_BOX = {r_box:.4f}")
    s = s.replace("PARAMETER REAL :: CONF_K = 0.01", f"PARAMETER REAL :: CONF_K = {conf_k}")
    s = s.replace("__INIT__", init_body)
    (OUT / out_name).write_text(s)
    print(f"wrote {out_name} (N={n}, R_BOX={r_box:.2f}, CONF_K={conf_k}, TMULS={TMULS})")


build(48, 0.05, "condensate_hot48.ergo")
build(96, 0.05, "condensate_hot96.ergo")
