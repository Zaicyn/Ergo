#!/usr/bin/env python3
"""orient_analyze.py — the orientation-term matrix table.

Cells: hot baseline (dock_oracle/dock_sim, existing), hot+orient k0.5/k1.0,
cold baseline, cold+orient k0.5 — oracle and sim inits.
Per cell: best/mean full RMSD, mean internal-only RMSD, mean placement
contribution, mean IFACE satisfaction, and the trap-block check.
"""
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"
NS = (152, 168, 120, 116)

CELLS = [
    ("hot base", "oracle", "dock_oracle.out"),
    ("hot base", "sim", "dock_sim.out"),
    ("hot orient k0.5", "oracle", "orient_hot_oracle_k05.out"),
    ("hot orient k0.5", "sim", "orient_hot_sim_k05.out"),
    ("hot orient k1.0", "sim", "orient_hot_sim_k10.out"),
    ("cold base", "oracle", "orient_cold_oracle_base.out"),
    ("cold base", "sim", "orient_cold_sim_base.out"),
    ("cold orient k0.5", "oracle", "orient_cold_oracle_k05.out"),
    ("cold orient k0.5", "sim", "orient_cold_sim_k05.out"),
]

def parse(path):
    dom, iface = {}, {}
    for ln in open(path):
        if ln.startswith("DOM "):
            p = ln.split()
            dom[int(p[1])] = tuple(float(x) for x in p[3:8])
        elif ln.startswith("IFACE "):
            p = ln.split()
            iface[int(p[1])] = (int(p[2]), float(p[3]), float(p[4]), int(p[5]))
    return dom, iface

print(f"{'cell':<18}{'init':<8}{'best':>7}{'mean':>7}{'intern':>8}{'place':>8}{'IFACE sat':>10}")
for cell, init, fn in CELLS:
    dom, iface = parse(PM / fn)
    fulls = np.array([dom[b][0] for b in sorted(dom)])
    intern = []
    place = []
    sat = []
    for b in sorted(dom):
        f, d1, d2, d3, d4 = dom[b]
        ds = (d1, d2, d3, d4)
        i2 = sum(n * d * d for n, d in zip(NS, ds)) / 556.0
        intern.append(np.sqrt(i2))
        place.append(np.sqrt(max(f * f - i2, 0.0)))
        sat.append(iface[b][3] / iface[b][0])
    print(f"{cell:<18}{init:<8}{fulls.min():7.2f}{fulls.mean():7.2f}"
          f"{np.mean(intern):8.2f}{np.mean(place):8.2f}{np.mean(sat)*100:9.0f}%")

print("\nper-block full RMSD (all cells):")
hdr = f"{'cell':<18}{'init':<8}" + "".join(f"  blk{b}" for b in range(1, 9))
print(hdr)
for cell, init, fn in CELLS:
    dom, _ = parse(PM / fn)
    print(f"{cell:<18}{init:<8}" + "".join(f"  {dom[b][0]:4.1f}" for b in sorted(dom)))

print("\nper-block per-domain RMSD means (A2 A3 B1 B2), all cells:")
for cell, init, fn in CELLS:
    dom, _ = parse(PM / fn)
    ds = np.array([[dom[b][k] for k in range(1, 5)] for b in sorted(dom)])
    print(f"{cell:<18}{init:<8}" + " ".join(f"{m:5.2f}" for m in ds.mean(0)))
