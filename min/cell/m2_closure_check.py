#!/usr/bin/env python3
"""m2_closure_check.py — offline validation of cell_unit.ergo's
parity-with-clustering ray-cast closure test against FPOS dumps.

The test: NDIR=162 Fibonacci directions from the amph-bead centroid;
per direction, beads within a RCROSS=1.4 cylinder at t>0 are clustered
along the ray with gap 2.2 (the bilayer's two leaflets = one cluster,
overhangs/folds = 3, ...). A closed genus-0 shell gives an ODD cluster
count in (nearly) every direction; an open sheet/cup has even-count or
zero-hit directions. NCLOSED = (odd directions >= 95% of NDIR).

Usage: python3 min/cell/m2_closure_check.py <log> [<log> ...]
Prints per-log: odd/zero-hit direction counts and the PASS/OPEN call.
"""
import math
import sys

import numpy as np

NDIR = 162
RCROSS = 1.4
GAP = 2.2
ODD_FRAC = 0.95


def load(path):
    out = []
    for line in open(path):
        if line.startswith("FPOS "):
            p = line.split()
            if int(p[1]) in (0, 1):
                out.append((float(p[3]), float(p[4]), float(p[5])))
    return np.array(out)


def parity_counts(H):
    c = H.mean(axis=0)
    golden = math.pi * (3.0 - math.sqrt(5.0))
    odd = zero = 0
    for k in range(NDIR):
        z = 1.0 - 2.0 * (k + 0.5) / NDIR
        r = math.sqrt(max(0.0, 1.0 - z * z))
        th = golden * k
        u = np.array([r * math.cos(th), r * math.sin(th), z])
        t = (H - c) @ u
        d2 = ((H - c) ** 2).sum(axis=1) - t * t
        ts = np.sort(t[(d2 < RCROSS * RCROSS) & (t > 0)])
        if len(ts) == 0:
            zero += 1
            continue
        ncl = 1
        prev = ts[0]
        for x in ts[1:]:
            if x - prev > GAP:
                ncl += 1
            prev = x
        if ncl % 2 == 1:
            odd += 1
    return odd, zero


for path in sys.argv[1:]:
    H = load(path)
    odd, zero = parity_counts(H)
    call = "CLOSED" if odd >= ODD_FRAC * NDIR else "OPEN"
    print(f"{path}: odd {odd}/{NDIR} ({odd/NDIR*100:.1f}%), "
          f"zero-hit {zero} -> {call}")
