#!/usr/bin/env python3
"""d5/csv_dist.py — distribution-level comparison of a 144k-frame run
against the certified CSV (used when byte-identity is impossible by
construction, e.g. GPU-force-extraction f32 build vs a certified
CPU-force trajectory).

Reads (pre-registered for this comparison):
  1. rgyr trajectory envelope: max |rgyr_new - rgyr_cert| / |rgyr_cert|
     over aligned telemetry rows (per-row relative deviation profile).
  2. Dock-window: the frame where e_native jumps (first row with
     e_native > 5x the pre-dock median) in each file.
  3. Final-structure metrics: last telemetry row (rgyr, e_native,
     rmsd_native, nhb) and their relative deviation.
Prints a table; no pass/fail thresholds are invented here — the numbers
are the report.
"""
import csv
import sys


def tele(path):
    rows = list(csv.reader(open(path)))
    hdr = rows[0]
    out = []
    for r in rows[1:]:
        if r and r[0].strip().isdigit() and len(r) == len(hdr):
            out.append({h: r[i] for i, h in enumerate(hdr)})
    return out


def dock_frame(rows):
    pre = [float(r['e_native']) for r in rows
           if 20000 <= int(r['frame']) <= 23900]
    med = sorted(pre)[len(pre) // 2]
    for r in rows:
        if int(r['frame']) > 23900 and float(r['e_native']) > 5 * med:
            return int(r['frame'])
    return None


def main():
    new, cert = tele(sys.argv[1]), tele(sys.argv[2])
    byf_new = {int(r['frame']): r for r in new}
    byf_cert = {int(r['frame']): r for r in cert}
    common = sorted(set(byf_new) & set(byf_cert))
    devs = []
    for f in common:
        a, b = float(byf_new[f]['rgyr']), float(byf_cert[f]['rgyr'])
        if abs(b) > 1e-12:
            devs.append((abs(a - b) / abs(b), f))
    devs.sort(reverse=True)
    print(f"rows aligned: {len(common)}")
    print(f"rgyr rel-dev: median "
          f"{sorted(d[0] for d in devs)[len(devs)//2]:.3e}  "
          f"max {devs[0][0]:.3e} (frame {devs[0][1]})")
    print(f"dock jump frame: new {dock_frame(new)}  certified {dock_frame(cert)}")
    for name, r in (("new", new[-1]), ("certified", cert[-1])):
        print(f"{name}: frame {r['frame']} rgyr {r['rgyr']} "
              f"e_native {r['e_native']} rmsd {r['rmsd_native']} "
              f"nhb {r['nhb']}")


if __name__ == "__main__":
    main()
