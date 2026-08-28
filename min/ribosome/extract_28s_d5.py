#!/usr/bin/env python3
"""extract_28s_d5.py — Phase-3: extract a domain-scale RNA region from
6QZP chain L5 (28S rRNA) and segment it into foldable sub-domains.

Geometry-derived, documented (no external annotation tool in repo):
  1. Parse chain L5 C1' atoms from 6QZP.cif (mmCIF).
  2. Native contact profile: for each residue i, count native C1'-C1'
     contacts (<11.5 A) from i to residues beyond +/-15 in sequence —
     the LONG-RANGE contact density. Domain boundaries are local
     minima of this profile (regions dense internally, sparse across).
  3. Choose a window of ~450-600 nt whose interior is compact
     (the Domain-V-scale region) and split it at the 2-3 deepest
     interior minima into 3-4 sub-domains of ~120-180 nt each (under
     the ~180-bead wall measured in RIBOSOME_FINDINGS).

Output: JSON segments in the generate_protein_ergo.py format
(coords / res_names / mean_ca_ca), one per sub-domain plus the full
region, and a printed segmentation report.

Usage: python3 min/ribosome/extract_28s_d5.py [--win A:B] [--out prefix]
"""

import argparse
import json
import math
import shlex


def parse_l5_c1p(path, chain="L5"):
    cols = None
    atoms = {}
    with open(path) as f:
        for line in f:
            if line.startswith('_atom_site.'):
                cols = (cols or []) + [line.strip().split('.')[1]]
                continue
            if cols and line.startswith('ATOM'):
                toks = shlex.split(line)
                if not toks:
                    continue
                d = dict(zip(cols, toks))
                if d.get('auth_asym_id') != chain:
                    continue
                if d.get('label_atom_id') != "C1'":
                    continue
                try:
                    seq = int(d['auth_seq_id'])
                except (KeyError, ValueError):
                    continue
                atoms[seq] = (
                    float(d['Cartn_x']), float(d['Cartn_y']),
                    float(d['Cartn_z']), d.get('auth_comp_id', 'N'))
            elif cols and line.startswith('#'):
                break
    return atoms


def dist(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cif', default='min/ribosome/6QZP.cif')
    ap.add_argument('--win', default=None, help='explicit A:B window')
    ap.add_argument('--nsub', type=int, default=4)
    ap.add_argument('--out', default='/tmp/d5seg')
    args = ap.parse_args()

    atoms = parse_l5_c1p(args.cif)
    seqs = sorted(atoms)
    print(f"chain L5: {len(seqs)} C1' residues, seq {seqs[0]}..{seqs[-1]}")

    # long-range contact profile over the modeled sequence
    have = [s for s in seqs]
    pos = {s: atoms[s][:3] for s in have}
    idx = {s: i for i, s in enumerate(have)}
    prof = [0] * len(have)
    cutoff2 = 11.5 ** 2
    for a in range(len(have)):
        xa, ya, za = pos[have[a]]
        for b in range(a + 15, len(have)):
            xb, yb, zb = pos[have[b]]
            d2 = (xa-xb)**2 + (ya-yb)**2 + (za-zb)**2
            if d2 < cutoff2:
                prof[a] += 1
                prof[b] += 1
    # smooth
    W = 15
    sm = [sum(prof[max(0, i-W):i+W+1]) for i in range(len(prof))]

    if args.win:
        lo, hi = (int(x) for x in args.win.split(':'))
        i_lo, i_hi = have.index(lo), have.index(hi)
    else:
        # pick the 550 consecutive MODELED residues with the highest
        # mean long-range contact density (most compact domain-scale
        # region), requiring no internal sequence gap > 20 (a bigger
        # deletion would fake backbone connectivity across an
        # unmodeled expansion segment)
        best, bestv = None, -1
        WLEN = 550
        for i in range(0, len(have) - WLEN, 25):
            gaps = max(have[k + 1] - have[k]
                       for k in range(i, i + WLEN - 1))
            if gaps > 20:
                continue
            v = sum(sm[i:i+WLEN])
            if v > bestv:
                bestv, best = v, i
        if best is None:
            raise SystemExit("no gap-clean 550-nt window found")
        i_lo, i_hi = best, best + WLEN - 1
        lo, hi = have[i_lo], have[i_hi]
    print(f"region window: {lo}..{hi} "
          f"({i_hi - i_lo + 1} modeled nt, max internal seq gap "
          f"{max(have[k+1]-have[k] for k in range(i_lo, i_hi))})")

    # split at density minima near the balanced positions, minimum
    # segment size 90 modeled nt; segments must stay under the
    # ~180-bead wall AND within the 4-chain chain-break limit of the
    # engine (3 breaks)
    seg = sm[i_lo:i_hi + 1]
    nseg = len(seg)
    target = nseg / args.nsub
    splits = []
    for k in range(1, args.nsub):
        c0 = int(k * target)
        lo_b = max(90, c0 - 45)
        hi_b = min(nseg - 90 * (args.nsub - k), c0 + 45)
        window = range(lo_b, hi_b)
        best_c = min(window, key=lambda c: seg[c])
        splits.append(best_c)
    splits.sort()
    bounds = [i_lo] + [i_lo + s for s in splits] + [i_hi + 1]
    print("sub-domain boundaries (seq, smoothed LR-contact density):")
    mean_ca = []
    for a, b in zip(bounds, bounds[1:]):
        s0, s1 = have[a], have[b - 1]
        n = b - a
        # mean sequential spacing for this segment
        d = [dist(pos[have[k]], pos[have[k+1]]) for k in range(a, b-1)]
        mc = sum(d) / len(d) if d else 0.0
        mean_ca.append(mc)
        print(f"  {s0}..{s1}: {n} nt, mean profile {sum(seg[a-i_lo:b-i_lo])/max(1,n):.1f}, mean seq-spacing {mc:.2f} A")
        out = {
            "name": f"28sd5_{s0}_{s1}",
            "residues": n,
            "coords": [[k - a + 1, have[k], pos[have[k]][0],
                        pos[have[k]][1], pos[have[k]][2]]
                       for k in range(a, b)],
            "res_names": [atoms[have[k]][3] for k in range(a, b)],
            "mean_ca_ca": 3.8,
        }
        with open(f"{args.out}_{s0}_{s1}.json", "w") as f:
            json.dump(out, f)
    # full region too (monolithic baseline)
    a, b = bounds[0], bounds[-1]
    out = {
        "name": f"28sd5_{have[a]}_{have[b-1]}",
        "residues": b - a,
        "coords": [[k - a + 1, have[k], pos[have[k]][0],
                    pos[have[k]][1], pos[have[k]][2]]
                   for k in range(a, b)],
        "res_names": [atoms[have[k]][3] for k in range(a, b)],
        "mean_ca_ca": 3.8,
    }
    with open(f"{args.out}_full.json", "w") as f:
        json.dump(out, f)
    print(f"wrote {args.out}_*.json")


if __name__ == "__main__":
    main()
