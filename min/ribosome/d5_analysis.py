#!/usr/bin/env python3
"""d5_analysis.py — Phase-3 hierarchical fold-then-dock analysis.

PRE-REGISTERED READS (written before any run output was analyzed):
  P1. Sub-domain folds: final RMSD of each solo sub-domain run;
      pass = <= 5.0 each (they are all under the ~180-bead wall).
  P2. Assembled RMSD: hierarchical run final global RMSD vs the
      monolithic baseline run final global RMSD.
  P3. COMPOSITION RATIO = mean sub-domain RMSD / monolithic RMSD —
      THE inversion-structure measurement: does hierarchical error
      add (ratio ~1), stay flat (<1), or partially cancel?
  Decision rule (pre-registered):
    - sub-domains <= 5 each AND hierarchical global < monolithic
      global -> "fold local, dock rigid" beats the wall; it is the
      inversion structure for rungs 4-6.
    - else -> deeper representational limit, recorded honestly.

Usage: python3 min/ribosome/d5_analysis.py <dir_with_csvs>
"""

import csv
import os
import sys


def tele(path, colname):
    rows = list(csv.reader(open(path)))
    hdr = rows[0]
    i = hdr.index(colname)
    out = []
    for r in rows[1:]:
        if r and r[0].strip().isdigit() and len(r) == len(hdr):
            out.append(float(r[i]))
    return out


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "/tmp/d5runs"
    solos = {}
    mono = hier = None
    for f in sorted(os.listdir(d)):
        if not f.endswith(".csv"):
            continue
        rmsd = tele(os.path.join(d, f), "rmsd_native")
        if not rmsd:
            continue
        if f.startswith("d5seg"):
            solos[f] = rmsd[-1]
        elif f.startswith("d5_mono"):
            mono = rmsd[-1]
        elif f.startswith("d5_hier"):
            hier = rmsd[-1]
    print("== Phase 3: hierarchical fold-then-dock ==")
    print("P1 sub-domain solo finals (pass <= 5.0):")
    vals = []
    for f, v in solos.items():
        vals.append(v)
        print(f"   {f}: {v:.2f}  {'PASS' if v <= 5.0 else 'fail'}")
    print(f"P2 assembled: monolithic {mono}  vs hierarchical {hier}")
    if vals and mono:
        import statistics
        m = statistics.mean(vals)
        print(f"P3 composition: mean sub-domain RMSD {m:.2f}; "
              f"mono {mono:.2f}; ratio {m / mono:.2f}")
        if hier:
            print(f"   hierarchical/monolithic = {hier / mono:.2f}")


if __name__ == "__main__":
    main()
