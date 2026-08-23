#!/usr/bin/env python3
"""
dbm_mirror.py -- distribution-level mirror of the DBM/dendrite campaign
(dbm_radial_e00/e05.ergo), independent of the ergo/mcl toolchain.

Same physics as the ergo originals:
  * Laplace solve by SOR, omega = 2/(1+sin(pi/N)), TOL = 1e-6,
    warm-started after every deposit, phi clamped >= 0 (the NaN fix),
    outer boundary phi = 1 frozen at R >= R1 = N/2 - 2,
    initial field phi = log(max(R,0.5))/log(R1).
  * Growth weights W = phi**eta on empty sites 4-adjacent to the cluster.
  * Roulette pick, ONE deposit per solve, seed at the centre cell.
  * Stop at fixed mass 4001 (your e00/e05/base protocol).

Two deliberate deviations, both documented and distribution-level only:
  1. RNG is splitmix64, not ergo RAND(SEED+G) -- the RAND spec is
     unknown outside mcl, so trajectories cannot be reproduced;
     distributions can ("distributions, not trajectories").
  2. The D estimator was calibrated against your e00 run:
     cumulative mass M(<r) binned at INTEGER radius edges, log-log
     least squares over r in [8, 0.8*rmax]. Bin MIDPOINTS read a
     compact disk low (Eden -> 1.94 instead of 2.00); integer edges
     reproduce your e00 = 2.001 / R2 = 0.9996 on my own Eden cluster
     (I get 2.0015 / 0.99969), so this is almost certainly your
     estimator too.

Usage:
    python3 dbm_mirror.py [eden|e05|e10|all]      (default: all)
Needs:
    numpy, numba        (pip install numba)
Runtime:
    eden ~1 s;  e05 ~15-20 min;  e10 = two seeds, ~2x10-15 min.
Output:
    dbm_mirror_<which>.json  (+ cluster bitmaps dbm_mirror_*_clus.npy)

Reference numbers from DENDRITE_FINDINGS.md (mass-4001 radial table):
    eta=0.0  D = 2.001  R2 = 0.9996   (e00)
    eta=0.5  D = 1.856  R2 = 0.9992   (e05)
    eta=1.0  D = 1.725 / 1.650 / 1.740 across seeds (base / s777* / s31337)
    eta=2.0  D = 1.462  R2 = 0.9951   (e20, boundary-stopped)
    literature window eta=1: D ~ 1.60-1.75
"""

import sys, json, time
import numpy as np
from numba import njit

NDB   = 257
R1DB  = 0.5 * NDB - 2.0                       # 126.5
OMGDB = 2.0 / (1.0 + np.sin(np.pi / NDB))     # ~1.9758
TOLG, SWMAXG = 1e-6, 1200

jjD, iiD = np.meshgrid(np.arange(NDB), np.arange(NDB), indexing='ij')
RR    = np.sqrt((jjD - NDB // 2) ** 2 + (iiD - NDB // 2) ** 2)
MASK  = (RR < R1DB).astype(np.float64)
PHI0  = np.where(RR < R1DB, np.log(np.maximum(RR, 0.5)) / np.log(R1DB), 1.0)


@njit(cache=True, fastmath=False, nogil=True)
def splitmix64(state):
    state = state + np.uint64(0x9E3779B97F4A7C15)
    z = state
    z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    z = z ^ (z >> np.uint64(31))
    return state, z


@njit(cache=True, fastmath=False, nogil=True)
def dbm_grow(PHI0, MASK, RR, eta, seed, OMEGA, TOL, SWMAX, maxdep, rstop):
    N = PHI0.shape[0]
    phi = PHI0.copy()
    clus = np.zeros((N, N), dtype=np.uint8)
    c = N // 2
    clus[c, c] = 1
    phi[c, c] = 0.0
    rng = np.uint64(seed)
    rs = np.empty(maxdep)
    nd = 0
    while nd < maxdep:
        # SOR to convergence (warm-started), clamp phi >= 0, cluster frozen
        for sw in range(SWMAX):
            mx = 0.0
            for j in range(1, N - 1):
                for i in range(1, N - 1):
                    if MASK[j, i] > 0.5 and clus[j, i] == 0:
                        nv = phi[j, i] + OMEGA * (
                            0.25 * (phi[j, i+1] + phi[j, i-1]
                                    + phi[j+1, i] + phi[j-1, i]) - phi[j, i])
                        if nv < 0.0:
                            nv = 0.0
                        d = nv - phi[j, i]
                        if d < 0.0:
                            d = -d
                        if d > mx:
                            mx = d
                        phi[j, i] = nv
            if mx < TOL:
                break
        # weights + roulette
        totw = 0.0
        for j in range(1, N - 1):
            for i in range(1, N - 1):
                if (MASK[j, i] > 0.5 and clus[j, i] == 0
                        and (clus[j, i+1] + clus[j, i-1]
                             + clus[j+1, i] + clus[j-1, i]) > 0):
                    totw += phi[j, i] ** eta
        rng, z = splitmix64(rng)
        target = ((z >> np.uint64(11)) / float(1 << 53)) * totw
        acc = 0.0
        dj, di = -1, -1
        for j in range(1, N - 1):
            for i in range(1, N - 1):
                if (MASK[j, i] > 0.5 and clus[j, i] == 0
                        and (clus[j, i+1] + clus[j, i-1]
                             + clus[j+1, i] + clus[j-1, i]) > 0):
                    acc += phi[j, i] ** eta
                    if acc >= target:
                        dj, di = j, i
                        break
            if dj >= 0:
                break
        if dj < 0:
            break
        clus[dj, di] = 1
        phi[dj, di] = 0.0
        rs[nd] = RR[dj, di]
        nd += 1
        if RR[dj, di] > rstop:
            break
    return clus, rs[:nd]


@njit(cache=True, fastmath=False, nogil=True)
def eden_grow(MASK, RR, seed, maxdep):
    # eta = 0 needs no field solve: every adjacent empty site has weight 1
    N = MASK.shape[0]
    clus = np.zeros((N, N), dtype=np.uint8)
    c = N // 2
    clus[c, c] = 1
    candj = np.empty(maxdep * 8, dtype=np.int64)
    candi = np.empty(maxdep * 8, dtype=np.int64)
    nc = 0
    rng = np.uint64(seed)
    rs = np.empty(maxdep)
    nd = 0
    for (dj, di) in ((c, c+1), (c, c-1), (c+1, c), (c-1, c)):
        candj[nc] = dj; candi[nc] = di; nc += 1
    while nd < maxdep and nc > 0:
        rng, z = splitmix64(rng)
        k = int(z % np.uint64(nc))
        dj, di = candj[k], candi[k]
        nc -= 1
        candj[k] = candj[nc]; candi[k] = candi[nc]
        clus[dj, di] = 1
        rs[nd] = RR[dj, di]; nd += 1
        for (ej, ei) in ((dj, di+1), (dj, di-1), (dj+1, di), (dj-1, di)):
            if (1 <= ej < N-1 and 1 <= ei < N-1 and MASK[ej, ei] > 0.5
                    and clus[ej, ei] == 0):
                dup = False
                for m in range(nc):
                    if candj[m] == ej and candi[m] == ei:
                        dup = True
                        break
                if not dup:
                    candj[nc] = ej; candi[nc] = ei; nc += 1
    return clus, rs[:nd]


def dim_fit(clus, r_lo=8.0, hi_frac=0.8):
    """Calibrated estimator: M(<r) at integer radius edges, fit [8, 0.8*rmax]."""
    c = clus.shape[0] // 2
    jj, ii = np.nonzero(clus)
    r = np.sqrt((jj - c) ** 2 + (ii - c) ** 2)
    rstop = float(r.max())
    edges = np.arange(0, int(rstop) + 2)          # integer bin EDGES
    pts = edges[1:]
    M = np.zeros(len(edges) - 1)
    np.add.at(M, np.minimum(np.digitize(r, edges) - 1, len(M) - 1), 1)
    Mc = np.cumsum(M)
    sel = (pts >= r_lo) & (pts <= hi_frac * rstop) & (Mc > 0)
    A = np.vstack([np.log(pts[sel]), np.ones(sel.sum())]).T
    D, b = np.linalg.lstsq(A, np.log(Mc[sel]), rcond=None)[0]
    pred = D * np.log(pts[sel]) + b
    R2 = 1 - np.sum((np.log(Mc[sel]) - pred) ** 2) / np.sum(
        (np.log(Mc[sel]) - np.log(Mc[sel]).mean()) ** 2)
    return {'mass': int(len(r)), 'rmax': rstop, 'D': float(D), 'R2': float(R2)}


def run(which):
    res = {}
    if which in ('eden', 'all'):
        t0 = time.time()
        cl, _ = eden_grow(MASK, RR, 12345, 4001)
        res['eden_m4001'] = dim_fit(cl)
        res['eden_m4001']['wall_s'] = time.time() - t0
        np.save('dbm_mirror_eden_clus.npy', cl)
    if which in ('e05', 'all'):
        t0 = time.time()
        cl, _ = dbm_grow(PHI0, MASK, RR, 0.5, 12345, OMGDB, TOLG, SWMAXG, 4001, 1e9)
        res['e05_m4001'] = dim_fit(cl)
        res['e05_m4001']['wall_s'] = time.time() - t0
        np.save('dbm_mirror_e05_clus.npy', cl)
    if which in ('e10', 'all'):
        for seed in (999, 31337):
            t0 = time.time()
            cl, _ = dbm_grow(PHI0, MASK, RR, 1.0, seed, OMGDB, TOLG, SWMAXG, 4001, 1e9)
            res[f'e10_s{seed}_m4001'] = dim_fit(cl)
            res[f'e10_s{seed}_m4001']['wall_s'] = time.time() - t0
            np.save(f'dbm_mirror_e10_s{seed}_clus.npy', cl)
    return res


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    res = run(which)
    with open(f'dbm_mirror_{which}.json', 'w') as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
