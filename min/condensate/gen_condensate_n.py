#!/usr/bin/env python3
"""gen_condensate_n.py — finite-size scaling: N in {24, 48, 96} chains/block.

Same physics as gen_condensate.py (8 constant-T blocks, Gaussian
inter-chain attraction ATT_K = 0.005 per PAIR, harmonic sphere).
Scaling protocol (documented):
  - ATT_K is kept per-pair constant: the pair potential is a two-bead
    property; coordination (and thus extensive binding) grows with
    bulk density, which is held constant — N-dependence should enter
    only through droplet fluctuations (~1/sqrt(N)) and surface/volume.
  - R_BOX scales as N^(1/3): 18.0 / 22.67 / 28.57 for N = 24/48/96,
    holding initial bulk density constant.
  - Grid starts: spacing 5 u in all cases (grid occupies ~4-6% of box
    volume at every N).
Cost: N=96 -> 5376 residues, ~7 min estimated (reported in the check).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "amyloid"))

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "min" / "condensate"

import gen_condensate as GC  # re-emits the 24-chain base (deterministic)

G = GC.G

TMULS = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0]


def grid_for(n):
    # choose nx, ny, nz with product >= n, spacing 5
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


def build(n, out_name):
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
    s = s.replace("STATIC INTEGER :: CM(NCH, NCH), LAB(NCH), CNT(NCH)",
                  "STATIC INTEGER :: CM(NCH, NCH), LAB(NCH), CNT(NCH)")
    s = s.replace("__INIT__", init_body)
    (OUT / out_name).write_text(s)
    print(f"wrote {out_name} (N={n}, NPB={npb}, NTOT={ntot}, R_BOX={r_box:.2f})")


build(48, "condensate_n48.ergo")
build(96, "condensate_n96.ergo")
