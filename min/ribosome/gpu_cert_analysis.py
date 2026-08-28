#!/usr/bin/env python3
"""gpu_cert_analysis.py — GPU-vs-CPU certification cross-check (tRNA 76-bead).

PRE-REGISTERED READS (written before any GPU output was analyzed):
  G1. Per-seed final rmsd_native: CPU slot-form f64 vs GPU slot-form f32.
  G2. Per-seed final rgyr, both builds.
  G3. Sanity: no NaN/Inf anywhere, monotone-ish quench (no late explosion:
      max rmsd over the last 10% of frames < 1.5x final rmsd + 1.0).
DECISION RULE (pre-registered):
  - CPU-slot-f64 vs the OLD certified rung-2 results (4.45 / 4.87 / 6.24
    for seeds 0/1/2): reassociation-level changes only -> per-seed
    |delta| <= 2.0 and every seed stays in its certified band (<= 7.0).
  - GPU-f32 vs CPU-slot-f64: f32 + tree-combine reordering over 96k
    frames is a chaotic perturbation, so the comparison is BASIN-level,
    not trajectory-level: pass iff each GPU seed finishes within 2.0 of
    its CPU sibling AND <= 7.0 absolute, with G3 clean.
  - Either failure -> the GPU path is NOT certified; report honestly,
    do not tune to pass.

Usage: python3 gpu_cert_analysis.py <dir_with_csvs>
  expects trna_cpu_<s>.csv and trna_gpu_<s>.csv for s = 0,1,2
"""

import csv
import math
import os
import statistics
import sys

OLD_CERT = {0: 4.45, 1: 4.87, 2: 6.24}   # rung-2 certified (old form, f64)


def tele(path, col):
    rows = list(csv.reader(open(path)))
    hdr = rows[0]
    i = hdr.index(col)
    out = []
    for r in rows[1:]:
        if r and r[0].strip().lstrip('-').isdigit() and len(r) == len(hdr):
            v = float(r[i])
            if math.isnan(v) or math.isinf(v):
                return None
            out.append(v)
    return out


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else '.'
    print('== GPU certification cross-check (tRNA 76, slot form) ==')
    print('seed | CPU-f64 final | GPU-f32 final | delta | old-cert | verdict')
    ok_all = True
    for s in (0, 1, 2):
        cpu = tele(os.path.join(d, f'trna_cpu_{s}.csv'), 'rmsd_native')
        gpu = tele(os.path.join(d, f'trna_gpu_{s}.csv'), 'rmsd_native')
        if not cpu or not gpu:
            print(f'  {s}  | MISSING or NaN/Inf  (cpu={bool(cpu)} gpu={bool(gpu)})')
            ok_all = False
            continue
        fc, fg = cpu[-1], gpu[-1]
        n10 = max(1, len(cpu) // 10)
        late_c = max(cpu[-n10:]); late_g = max(gpu[-n10:])
        sane = late_c < 1.5 * fc + 1.0 and late_g < 1.5 * fg + 1.0
        d_gpu = abs(fc - fg)
        d_old = abs(fc - OLD_CERT[s])
        ok = d_gpu <= 2.0 and fg <= 7.0 and d_old <= 2.0 and fc <= 7.0 and sane
        ok_all &= ok
        print(f'  {s}  | {fc:7.3f}       | {fg:7.3f}       | {d_gpu:5.3f} | '
              f'{OLD_CERT[s]:5.2f} (d={d_old:4.2f}) | {"PASS" if ok else "FAIL"}'
              f'{"" if sane else "  [G3 late-explosion]"}')
        rg_c = tele(os.path.join(d, f'trna_cpu_{s}.csv'), 'rgyr')
        rg_g = tele(os.path.join(d, f'trna_gpu_{s}.csv'), 'rgyr')
        if rg_c and rg_g:
            print(f'       rgyr final: cpu {rg_c[-1]:.3f}  gpu {rg_g[-1]:.3f}')
    print()
    print('CERTIFIED' if ok_all else 'NOT CERTIFIED — see per-seed detail')


if __name__ == '__main__':
    main()
