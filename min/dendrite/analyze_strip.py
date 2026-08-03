#!/usr/bin/env python3
"""analyze_strip.py — DBM electrodeposition morphology analysis.

Parses dbm_strip .out files: step series (tip, hmean, rough) + final SNAP.
Battery oracle: eta=0 (Eden) advances a compact layer (tip ~ hmean);
eta>=1 the screening instability drives tips ahead of the mean deposit.

Usage: python3 analyze_strip.py dbm_strip.out dbm_strip_e00.out ...
"""

import re
import sys
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def parse(path):
    steps, tip, hmean, rough = [], [], [], []
    snaps, cur = {}, None
    for line in open(path):
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "step":
            steps.append(int(parts[1]))
            tip.append(float(parts[5]))
            hmean.append(float(parts[7]))
            rough.append(float(parts[9]))
        elif parts[0] == "SNAP":
            cur = int(parts[1])
            snaps[cur] = []
        elif parts[0] == "ENDSNAP":
            cur = None
        elif cur is not None and len(parts) == 2:
            snaps[cur].append((int(parts[0]), int(parts[1])))
    return steps, tip, hmean, rough, snaps


def main():
    fig, axes = plt.subplots(1, len(sys.argv[1:]) + 1,
                             figsize=(5 * (len(sys.argv[1:]) + 1), 4.5))
    for ax, path in zip(axes, sys.argv[1:]):
        steps, tip, hmean, rough, snaps = parse(path)
        tag = path.split("/")[-1].replace(".out", "")
        if steps:
            g0, g1 = len(steps) // 4, len(steps) - 1
            ratio_early = tip[g0] / hmean[g0]
            ratio_late = tip[g1] / hmean[g1]
            print(f"{path}: steps {steps[0]}-{steps[-1]}  "
                  f"tip/hmean {ratio_early:.2f} -> {ratio_late:.2f}  "
                  f"final tip {tip[-1]:.0f} hmean {hmean[-1]:.1f} "
                  f"rough {rough[-1]:.1f}")
        if snaps:
            pts = snaps[max(snaps)]
            ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=0.4, c="k")
            ax.set_title(f"{tag}  mass={len(pts)}")
            ax.set_aspect("equal")
            ax.set_xticks([]); ax.set_yticks([])
    ax = axes[-1]
    for path in sys.argv[1:]:
        steps, tip, hmean, rough, _ = parse(path)
        tag = path.split("/")[-1].replace(".out", "").replace("dbm_strip", "strip")
        if steps:
            ax.plot(steps, tip, label=f"{tag} tip")
            ax.plot(steps, hmean, "--", label=f"{tag} mean")
    ax.set_xlabel("growth step"); ax.set_ylabel("height (rows)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "dbm_strip_compare.png")
    fig.savefig(out, dpi=150)
    print(f"figure: {out}")


if __name__ == "__main__":
    main()
