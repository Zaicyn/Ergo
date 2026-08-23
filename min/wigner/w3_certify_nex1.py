#!/usr/bin/env python3
"""w3_certify_nex1.py -- Stage W3 same-orbitals construction certification,
Ne at physical c (the fourth block; the other three are recorded in
DF_RADIAL2_FINDINGS.md section 7b).

Feeds the certified df_mirror SCF orbitals (Ne x1) through the Stage W3
half-line Wigner construction on both map grids and diffs the result
against the engine's W3MAP rows from df_wig2.csv. Agreement at the
1e-5 level certifies the engine's resample + cosine-DFT map code; the
SCF-level agreement (eps/E to ~1e-4 rel) bounds the rest.

Usage (same directory as df_mirror.py, wigner_mirror_w3.py, df_wig2.csv):
    python3 w3_certify_nex1.py
Expect 10-30 min: the Ne mirror SCF is the slow part.
"""
import importlib.util
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dfm = load("dfm", os.path.join(HERE, "df_mirror.py"))
w3 = load("w3", os.path.join(HERE, "wigner_mirror_w3.py"))

# engine W3MAP rows for (Z=10, cscale=1)
rows = {0: [], 1: []}
for line in open(os.path.join(HERE, "df_wig2.csv")):
    s = line.strip().strip("()").replace("'", " ").split()
    if len(s) != 7 or s[0] != "W3MAP":
        continue
    Z, cs, coord = float(s[1]), float(s[2]), int(s[3])
    if abs(Z - 10.0) < 1e-9 and abs(cs - 1.0) < 1e-9:
        rows[coord].append((float(s[4]), float(s[5]), float(s[6])))
assert rows[0] and rows[1], "no Ne x1 W3MAP rows found in df_wig2.csv"

# certified SCF orbitals
at = dfm.Atom("Ne", 1.0)
at.scf()
occ = [2, 2, 2, 4][: len(at.eps)]
rg = at.rg

# Stage W3 map grids (must match df_wig2 / wigner_mirror_w3)
RMINW, RMAXW, NRW, NTM = 1.0e-6, 12.0, 2048, 1024
rr = RMINW + (np.arange(NRW) + 0.5) * ((RMAXW - RMINW) / NRW)
tt = np.log(RMINW) + np.arange(NTM) * (np.log(RMAXW) - np.log(RMINW)) / (NTM - 1)


def resamp(rnew):
    """engine-style linear-in-r interpolation from the SCF log grid."""
    ix = np.clip(((np.log(rnew) - np.log(rg[0])) / at.h).astype(int),
                 0, len(rg) - 2)
    w = np.clip((rnew - rg[ix]) / (rg[ix + 1] - rg[ix]), 0.0, 1.0)
    return ix, w


rho_r = np.zeros((NRW, NRW))
rho_t = np.zeros((NTM, NTM))
ixr, wr = resamp(rr)
ixt, wt = resamp(np.exp(tt))
for ia in range(len(at.eps)):
    Fr = at.F[ia][ixr] + wr * (at.F[ia][ixr + 1] - at.F[ia][ixr])
    Gr = at.G[ia][ixr] + wr * (at.G[ia][ixr + 1] - at.G[ia][ixr])
    rho_r += occ[ia] * (np.outer(Fr, Fr) + np.outer(Gr, Gr))
    Ft = at.F[ia][ixt] + wt * (at.F[ia][ixt + 1] - at.F[ia][ixt])
    Gt = at.G[ia][ixt] + wt * (at.G[ia][ixt + 1] - at.G[ia][ixt])
    rho_t += occ[ia] * (np.outer(Ft, Ft) + np.outer(Gt, Gt))

for coord, (xg, rho) in [(0, (rr, rho_r)), (1, (tt, rho_t))]:
    Wm, pg, _ = w3.wigner_halfline(xg, rho, None)
    diffs = []
    for x, p, W in rows[coord]:
        ix = np.argmin(np.abs(xg - x))
        ip = np.argmin(np.abs(pg - p))
        diffs.append(W - Wm[ix, ip])
    diffs = np.array(diffs)
    print(f"Ne x1.0 coord{coord}: rows={len(diffs)} "
          f"max|diff|={np.max(np.abs(diffs)):.3e} "
          f"rms={np.sqrt(np.mean(diffs**2)):.3e}", flush=True)
