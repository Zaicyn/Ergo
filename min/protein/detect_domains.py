#!/usr/bin/env python3
"""detect_domains.py

Automatically detect protein domain boundaries from a Cα/Cβ JSON file.

Algorithm (recursive ratio-based min-cut):
  1. Build a Cα-Cα contact map using a distance cutoff.
  2. For a contiguous segment, consider every possible cut position p.
  3. For each cut, compute the number of contacts C that cross the cut.
  4. Compare C to the expected number of crossing contacts for a random cut
     of the same segment sizes: E = M * nL * nR / (N*(N-1)/2), where M is the
     total number of contacts and N is the segment length.
  5. The cut score is C / E. A score well below 1.0 indicates a genuine domain
     boundary (far fewer cross-domain contacts than random).
  6. Recursively apply the best cut while the score is below --threshold and
     both subsegments are at least --min-size residues.
  7. Output the resulting contiguous domains as JSON.

Usage:
    python3 tools/detect_domains.py --json pdb/2LZM_ca.json
    python3 tools/detect_domains.py --json pdb/4I1H_ca.json --cutoff 8.0 --threshold 0.12

Output (JSON):
    {"D1": [1, 60], "D2": [61, 164]}
"""

import argparse
import json
import math
import sys
from typing import List, Tuple, Dict


def parse_ca_json(path: str):
    """Read the Cα/Cβ JSON produced by extract_pdb_ca.py."""
    with open(path) as f:
        data = json.load(f)
    coords = []
    for row in data['coords']:
        # row: [seq_index, pdb_resnum, ca_x, ca_y, ca_z]
        coords.append((float(row[2]), float(row[3]), float(row[4])))
    return coords, data.get('name', 'protein')


def vec_dist(a, b):
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2)


def build_contacts(coords, cutoff: float) -> List[Tuple[int, int]]:
    """Return all Cα-Cα contacts as (i, j) with 0 <= i < j < n."""
    contacts = []
    n = len(coords)
    for i in range(n):
        for j in range(i + 1, n):
            if vec_dist(coords[i], coords[j]) <= cutoff:
                contacts.append((i, j))
    return contacts


def count_crossing_contacts(l: int, r: int, p: int, contacts: List[Tuple[int, int]]) -> int:
    """Count contacts with one endpoint in [l, p] and the other in [p+1, r]."""
    c = 0
    for i, j in contacts:
        if l <= i <= p and p + 1 <= j <= r:
            c += 1
    return c


def best_cut(l: int, r: int, contacts: List[Tuple[int, int]],
             min_size: int, total_n: int, total_m: int) -> Tuple[int, float]:
    """
    Find the cut in [l, r] with the smallest observed/expected crossing ratio.
    Returns (p, ratio) where p is the last residue of the left subsegment (0-based).
    """
    seg_len = r - l + 1
    best_ratio = float('inf')
    best_p = None
    n_pairs = seg_len * (seg_len - 1) / 2.0

    for p in range(l + min_size - 1, r - min_size + 1):
        n_left = p - l + 1
        n_right = r - p
        c = count_crossing_contacts(l, r, p, contacts)
        expected = total_m * (n_left * n_right) / n_pairs if n_pairs > 0 else 0.0
        if expected <= 0.0:
            continue
        ratio = c / expected
        if ratio < best_ratio:
            best_ratio = ratio
            best_p = p

    return best_p, best_ratio


def split(l: int, r: int, contacts: List[Tuple[int, int]],
          threshold: float, min_size: int, total_n: int, total_m: int,
          depth: int = 0) -> List[Tuple[int, int]]:
    """Recursively split [l, r] while the best cut is significant."""
    if r - l + 1 < 2 * min_size:
        return [(l, r)]

    best_p, best_ratio = best_cut(l, r, contacts, min_size, total_n, total_m)
    if best_p is None or best_ratio >= threshold:
        return [(l, r)]

    left = split(l, best_p, contacts, threshold, min_size, total_n, total_m, depth + 1)
    right = split(best_p + 1, r, contacts, threshold, min_size, total_n, total_m, depth + 1)
    return left + right


def detect_domains(coords, cutoff: float = 8.0, threshold: float = 0.12,
                   min_size: int = 60) -> Dict:
    """Detect contiguous domains and return diagnostic information."""
    n = len(coords)
    contacts = build_contacts(coords, cutoff)
    total_m = len(contacts)
    intervals = split(0, n - 1, contacts, threshold, min_size, n, total_m)
    intervals = sorted(intervals, key=lambda x: x[0])

    # also record the boundary scores for each interval (if any)
    interval_scores = []
    for l, r in intervals:
        if r - l + 1 >= 2 * min_size:
            _, ratio = best_cut(l, r, contacts, min_size, n, total_m)
        else:
            ratio = float('inf')
        interval_scores.append((l + 1, r + 1, ratio))

    return {
        'intervals': intervals,
        'domains': boundaries_to_domains(intervals),
        'scores': interval_scores,
        'cutoff': cutoff,
        'threshold': threshold,
        'min_size': min_size,
        'total_contacts': total_m,
    }


def boundaries_to_domains(intervals: List[Tuple[int, int]]) -> Dict[str, List[int]]:
    """Convert 0-based inclusive intervals to 1-based domain definitions."""
    domains = {}
    for idx, (l, r) in enumerate(intervals, start=1):
        domains[f"D{idx}"] = [l + 1, r + 1]
    return domains


def main():
    parser = argparse.ArgumentParser(
        description='Detect protein domains from a Cα contact map using ratio-based min-cut')
    parser.add_argument('--json', required=True, help='Cα/Cβ JSON file')
    parser.add_argument('--cutoff', type=float, default=8.0,
                        help='Cα-Cα contact cutoff in Å (default 8.0)')
    parser.add_argument('--threshold', type=float, default=0.12,
                        help='Maximum observed/expected crossing ratio for a domain boundary '
                             '(default 0.12)')
    parser.add_argument('--min-size', type=int, default=60,
                        help='Minimum domain size in residues (default 60)')
    parser.add_argument('--out', help='Output JSON file (default stdout)')
    parser.add_argument('--verbose', action='store_true', help='Print diagnostic scores')
    args = parser.parse_args()

    coords, name = parse_ca_json(args.json)
    result = detect_domains(coords, args.cutoff, args.threshold, args.min_size)

    domains = result['domains']
    print(f"Detected {len(domains)} domain(s) for {name} ({len(coords)} residues):")
    print(f"  Parameters: cutoff={args.cutoff} Å, threshold={args.threshold}, "
          f"min_size={args.min_size}")
    for dname, (s, e) in domains.items():
        print(f"  {dname}: residues {s}-{e} ({e - s + 1} residues)")
    print()

    if args.verbose:
        print("Interval scores (best observed/expected crossing ratio within each domain):")
        for s, e, ratio in result['scores']:
            if math.isfinite(ratio):
                print(f"  {s}-{e}: {ratio:.4f}")
            else:
                print(f"  {s}-{e}: too small to split")
        print()

    out = json.dumps(domains, indent=2)
    if args.out:
        with open(args.out, 'w') as f:
            f.write(out)
        print(f"Wrote {args.out}")
    else:
        print(out)


if __name__ == '__main__':
    main()
