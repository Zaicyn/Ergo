#!/usr/bin/env python3
"""analyze_dbm.py — fractal dimension of DBM clusters from mass-radius scaling.

Parses a dbm_radial .out file, takes the last SNAP block (largest cluster),
computes M(r) = number of cluster sites within r of the seed, and fits
log M = D * log r + const over the scaling window [R_LO, R_HI_FRAC*rmax].

Oracle (literature): 2D Laplacian growth at eta=1 gives D ~ 1.6-1.75
(square-lattice anisotropy tolerated); eta=0 (Eden) gives D -> 2;
eta=2 gives sparse needles (D -> 1).

Usage: python3 analyze_dbm.py dbm_radial.out [dbm_radial2.out ...]
"""

import math
import sys

R_LO = 4.0          # exclude discreteness-dominated core
R_HI_FRAC = 0.7     # exclude boundary-influenced rim


def parse(path):
    grid = None
    snaps = {}        # step -> list[(i, j)]
    cur = None
    eta = None
    for line in open(path):
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "dbm_radial":
            grid = int(parts[2])
            eta = float(parts[8])
        elif parts[0] == "SNAP":
            cur = int(parts[1])
            snaps[cur] = []
        elif parts[0] == "ENDSNAP":
            cur = None
        elif cur is not None and len(parts) == 2:
            snaps[cur].append((int(parts[0]), int(parts[1])))
    return grid, eta, snaps


def fractal_D(pts, cx, cy):
    rs = sorted(math.hypot(i - cx, j - cy) for i, j in pts)
    n = len(rs)
    rmax = rs[-1]
    rhi = R_HI_FRAC * rmax
    # M(r) on a log-spaced set of r values (index of bisect)
    import bisect
    xs, ys = [], []
    r = R_LO
    while r < rhi:
        m = bisect.bisect_right(rs, r)
        if m > 0:
            xs.append(math.log(r))
            ys.append(math.log(m))
        r *= 1.15
    # least-squares slope
    k = len(xs)
    sx = sum(xs); sy = sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    d = (k * sxy - sx * sy) / (k * sxx - sx * sx)
    b = (sy - d * sx) / k
    # R^2
    ybar = sy / k
    ss_tot = sum((y - ybar) ** 2 for y in ys)
    ss_res = sum((y - (d * x + b)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return d, r2, rmax, n


def main():
    for path in sys.argv[1:]:
        grid, eta, snaps = parse(path)
        if not snaps:
            print(f"{path}: no snapshots found")
            continue
        step = max(snaps)
        pts = snaps[step]
        c = 0.5 * (grid + 1)
        d, r2, rmax, n = fractal_D(pts, c, c)
        verdict = ""
        if eta == 1.0:
            verdict = "  (oracle: 1.60-1.75)" + ("  PASS" if 1.55 <= d <= 1.80 else "  CHECK")
        print(f"{path}: eta={eta} grid={grid} step={step} mass={n} "
              f"rmax={rmax:.1f}  D={d:.3f} (R^2={r2:.4f}){verdict}")


if __name__ == "__main__":
    main()
