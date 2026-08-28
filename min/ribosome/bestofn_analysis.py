#!/usr/bin/env python3
"""bestofn_analysis.py — Phase-2 best-of-N basin statistics.

PRE-REGISTERED READS (written before any data was analyzed):
  R1. final-RMSD basin distribution per system (all seeds).
  R2. best-of-N curve: min(final RMSD over the first N seeds), N = 1..N_max.
  R3. freeze-timing distribution: per seed, the last frame with
      rmsd > final_rmsd + 0.1 (the basin-entry frame).
  Decision rule (pre-registered):
    - best-of-N curve dropping toward 5 (or below) by N=10..30 ->
      the ~300-bead plateau is stochastic; statistics buys folds.
    - curve tight around ~8 (all seeds within ~1 of each other, no
      downward trend) -> hard wall; hierarchical is the only path.
    Either answer is a finding.

Usage:
  python3 min/ribosome/bestofn_analysis.py <glob> <column> [label]
  e.g. python3 min/ribosome/bestofn_analysis.py '/tmp/bon/ul18_*.csv' rmsd_native ul18
"""

import csv
import glob
import statistics
import sys


def tele(path, colname):
    rows = list(csv.reader(open(path)))
    hdr = rows[0]
    i = hdr.index(colname)
    fi = hdr.index("frame")
    out = []
    for r in rows[1:]:
        if r and r[0].strip().isdigit() and len(r) == len(hdr):
            out.append((int(r[fi]), float(r[i])))
    return out


def main():
    pattern, colname = sys.argv[1], sys.argv[2]
    label = sys.argv[3] if len(sys.argv) > 3 else pattern
    finals = []
    for path in sorted(glob.glob(pattern)):
        series = tele(path, colname)
        if not series:
            continue
        fin_frame, fin = series[-1]
        # R3: freeze frame = last frame with rmsd > final + 0.1
        freeze = series[0][0]
        for fr, v in series:
            if v > fin + 0.1:
                freeze = fr
        finals.append((path.split("/")[-1], fin, freeze))
    if not finals:
        print("no data")
        return
    finals.sort(key=lambda t: t[0])
    vals = [f[1] for f in finals]
    print(f"== {label} ({colname}), {len(finals)} seeds ==")
    print("R1 basin distribution: "
          f"mean {statistics.mean(vals):.3f}  sd {statistics.stdev(vals):.3f}  "
          f"min {min(vals):.3f}  max {max(vals):.3f}")
    print("   all seeds: " + " ".join(f"{v:.2f}" for v in vals))
    print("R2 best-of-N curve:")
    best = 1e9
    curve = []
    for n, (_, v, _) in enumerate(finals, 1):
        best = min(best, v)
        curve.append((n, best))
    print("   " + "  ".join(f"N={n}:{b:.2f}" for n, b in curve))
    frz = [f[2] for f in finals]
    print("R3 freeze frame: "
          f"median {statistics.median(frz):.0f}  "
          f"min {min(frz)}  max {max(frz)}")
    print("   all freezes: " + " ".join(str(f) for f in frz))
    for (nm, v, fz) in finals:
        print(f"   {nm}  final {v:.3f}  freeze {fz}")


if __name__ == "__main__":
    main()
