"""Sweep round 1: gap maps for all four plugins under one protocol.

Strategy (measured, see sweep1_check.md): GPU batched eigh (cusolver syevj)
was timed at 47.6 s/matrix for 6561-dim complex64 — rejected for this
round; CPU sparse Lanczos on the numba/sparse matvecs is ~1 s/point.
Dense-matrix disk cache (engine/cache/, npz keyed by model+N+params hash,
global byte budget) is implemented for reuse; with 22 GB free disk and
fast dense emitters (~0.1 s) the cache only makes sense for small dims.

Per model: E0, gap (E1-E0); rydberg also E2-E0 (cat-doublet protocol).
Results: results_sweep1.json. Wall times logged per model.
"""

import hashlib
import json
import os
import sys
import time

import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.rotor import RotorModel
from models.xxz import XXZModel
from models.fk import FKModel
from models.rydberg import RydbergModel

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
CACHE_BUDGET = 8e9  # bytes; 22 GB free disk at build time
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "results_sweep1.json")


# ---------- dense cache ----------------------------------------------------

def _cache_key(model_name, N, params):
    s = f"{model_name}|{N}|" + "|".join(
        f"{k}={params[k]!r}" for k in sorted(params))
    return hashlib.sha1(s.encode()).hexdigest()[:20]


def cache_get(model_name, N, params):
    p = os.path.join(CACHE_DIR, _cache_key(model_name, N, params) + ".npz")
    if os.path.exists(p):
        return np.load(p)["H"]
    return None


def cache_put(model_name, N, params, H):
    os.makedirs(CACHE_DIR, exist_ok=True)
    used = sum(os.path.getsize(os.path.join(CACHE_DIR, f))
               for f in os.listdir(CACHE_DIR))
    nbytes = H.nbytes + 1024
    if used + nbytes > CACHE_BUDGET:
        return False
    np.savez_compressed(
        os.path.join(CACHE_DIR, _cache_key(model_name, N, params) + ".npz"),
        H=H)
    return True


# ---------- sweep worker ----------------------------------------------------

def _diagonal_only(model, params):
    """Exactly-diagonal Hamiltonians (all couplings zero) hit an ARPACK
    pathology where eigsh silently returns the second eigenvalue instead
    of the minimum. Detect and shortcut analytically (spectrum = kinetic
    diagonal: E0 = 0, gap = 0.5 for spin-1 rotors)."""
    if model.name == "rotor_spin1":
        return params["J"] == 0.0 and abs(params["B"] - 0.25) < 1e-12
    if model.name == "fk_pendulum":
        return params["J"] == 0.0 and params["V"] == 0.0
    return False


def sweep(model, N, grid, k=2, extra_gap=False):
    pts = []
    t0 = time.time()
    for params in grid:
        if _diagonal_only(model, params):
            rec = {"params": params, "E0": 0.0, "gap": 0.5,
                   "note": "analytic (ARPACK diagonal pathology guard)"}
            pts.append(rec)
            continue
        dim = (len(model.basis(N)) if model.name == "rydberg_blockade"
               else model.d_site ** N)
        A = LinearOperator((dim, dim), matvec=model.make_matvec(N, params),
                           dtype=complex)
        kk = k + 1 if extra_gap else k
        ev = np.sort(eigsh(A, k=kk, which="SA", tol=1e-10,
                           maxiter=5000)[0])
        rec = {"params": params, "E0": float(ev[0]),
               "gap": float(ev[1] - ev[0])}
        if extra_gap:
            rec["gap2"] = float(ev[2] - ev[0])
        pts.append(rec)
    return {"model": model.name, "N": N, "points": pts,
            "seconds": time.time() - t0}


def main():
    results = {"sweeps": [], "notes": {
        "gpu": "batched cusolver eigh measured 47.6 s/matrix at 6561-c64; "
               "rejected for this round, CPU sparse Lanczos used",
        "cache_budget_bytes": CACHE_BUDGET}}

    Bs = [round(0.025 * i, 3) for i in range(21)]
    Js = [round(0.1 * i, 2) for i in range(21)]
    grid = [{"B": B, "J": J} for B in Bs for J in Js]
    r = sweep(RotorModel(), 8, grid)
    results["sweeps"].append(r)
    json.dump(results, open(OUT, "w"), indent=1)
    print(f"[rotor] {len(grid)} pts, {r['seconds']:.0f}s", flush=True)

    Ds = [round(-1.0 + 0.1 * i, 2) for i in range(31)]
    hs = [round(0.1 * i, 2) for i in range(11)]
    grid = [{"Delta": D, "h": h} for D in Ds for h in hs]
    r = sweep(XXZModel(), 12, grid)
    results["sweeps"].append(r)
    json.dump(results, open(OUT, "w"), indent=1)
    print(f"[xxz] {len(grid)} pts, {r['seconds']:.0f}s", flush=True)

    Vs = [round(0.15 * i, 2) for i in range(21)]
    grid = [{"V": V, "J": J, "q": 1} for V in Vs for J in Js]
    r = sweep(FKModel(), 8, grid)
    results["sweeps"].append(r)
    json.dump(results, open(OUT, "w"), indent=1)
    print(f"[fk] {len(grid)} pts, {r['seconds']:.0f}s", flush=True)

    ds = [round(0.1 * i, 2) for i in range(31)]
    grid = [{"Delta": d, "V": 1.0} for d in ds]
    r = sweep(RydbergModel(), 16, grid, extra_gap=True)
    results["sweeps"].append(r)
    json.dump(results, open(OUT, "w"), indent=1)
    print(f"[rydberg] {len(grid)} pts, {r['seconds']:.0f}s", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
