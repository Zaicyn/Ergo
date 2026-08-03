#!/usr/bin/env python3
"""Compute per-domain RMSD from an Ergo FINAL_STRUCTURE block."""
import sys
import math
import json
import numpy as np


def parse_final_structure(path):
    """Extract final current/native coordinates from the .ergo output."""
    in_block = False
    rows = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if s == "FINAL_STRUCTURE":
                in_block = True
                continue
            if s == "END_FINAL_STRUCTURE":
                break
            if in_block:
                parts = s.split(",")
                if len(parts) == 7:
                    rows.append([float(x) for x in parts])
    if not rows:
        raise RuntimeError("No FINAL_STRUCTURE block found in " + path)
    arr = np.array(rows)
    idx = arr[:, 0].astype(int)
    cur = arr[:, 1:4]
    nat = arr[:, 4:7]
    return idx, cur, nat


def kabsch(cur, nat):
    """Return rotated current, centered native, and rotation matrix."""
    cur_c = cur - cur.mean(axis=0)
    nat_c = nat - nat.mean(axis=0)
    H = cur_c.T @ nat_c
    U, S, Vt = np.linalg.svd(H)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = U @ Vt
    rotated = cur_c @ R
    return rotated, nat_c, R


def domain_rmsds(rotated, nat_c, domains):
    """Compute RMSD per domain. domains is a list of (name, start, end) in 1-based indices."""
    results = []
    for name, start, end in domains:
        s = start - 1
        e = end
        diff = rotated[s:e] - nat_c[s:e]
        rmsd = np.sqrt((diff ** 2).sum() / (e - s))
        results.append((name, start, end, rmsd))
    return results


def main():
    if len(sys.argv) < 3:
        print("Usage: analyze_domains.py <outfile> <domain_json>")
        print("  domain_json: e.g. '{\"T4_D1\": [1,60], \"T4_D2\": [61,164]}'")
        sys.exit(1)
    path = sys.argv[1]
    domains = json.loads(sys.argv[2])
    domain_list = [(name, r[0], r[1]) for name, r in domains.items()]
    idx, cur, nat = parse_final_structure(path)
    rotated, nat_c, _ = kabsch(cur, nat)
    total_rmsd = np.sqrt(((rotated - nat_c) ** 2).sum() / len(idx))
    print(f"Total RMSD: {total_rmsd:.4f} model units ({total_rmsd*2.5:.2f} Å est.)")
    print()
    print("Domain RMSDs:")
    for name, start, end, rmsd in domain_rmsds(rotated, nat_c, domain_list):
        print(f"  {name} (residues {start}-{end}): {rmsd:.4f} model units ({rmsd*2.5:.2f} Å est.)")


if __name__ == "__main__":
    main()
