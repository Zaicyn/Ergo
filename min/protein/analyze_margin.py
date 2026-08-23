#!/usr/bin/env python3
"""Analyze Trp-cage final structure vs native PDB 1L2Y.

Parses FINAL_STRUCTURE block from the .ergo CSV output, performs Kabsch
alignment, and reports per-residue deviations and gap diagnostics."""
import sys
import math
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


def kabsch_rmsd(cur, nat):
    """Return RMSD and rotated current coordinates after Kabsch alignment.

    For row-oriented point matrices (N x 3), the optimal rotation that
    minimizes ||cur @ R - nat|| is R = U @ Vt where U S Vt = cur^T nat.
    """
    cur_c = cur - cur.mean(axis=0)
    nat_c = nat - nat.mean(axis=0)
    H = cur_c.T @ nat_c
    U, S, Vt = np.linalg.svd(H)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = U @ Vt
    rotated = cur_c @ R
    rmsd = np.sqrt(((rotated - nat_c) ** 2).sum() / len(cur))
    return rmsd, rotated, nat_c, R


def backbone_angles(coords):
    """Return per-residue backbone angles (degrees) for indices 2..n-1."""
    n = len(coords)
    angs = []
    for i in range(1, n - 1):
        u = coords[i - 1] - coords[i]
        v = coords[i + 1] - coords[i]
        un = np.linalg.norm(u)
        vn = np.linalg.norm(v)
        if un == 0 or vn == 0:
            angs.append(0.0)
            continue
        cs = np.clip(np.dot(u, v) / (un * vn), -1.0, 1.0)
        angs.append(math.degrees(math.acos(cs)))
    return angs


def dihedrals(coords):
    """Return per-residue phi-like dihedrals (degrees) for indices 2..n-2."""
    n = len(coords)
    phis = []
    for i in range(1, n - 2):
        b1 = coords[i] - coords[i - 1]
        b2 = coords[i + 1] - coords[i]
        b3 = coords[i + 2] - coords[i + 1]
        n1 = np.cross(b1, b2)
        n2 = np.cross(b2, b3)
        m1 = np.cross(n1, b2 / np.linalg.norm(b2))
        x = np.dot(n1, n2)
        y = np.dot(m1, n2)
        phi = math.degrees(math.atan2(y, x))
        phis.append(phi)
    return phis


def parse_domains_arg(arg, nres):
    """Parse --domains: '1-98,99-136' or JSON {'D1': [1, 98], ...}."""
    import json, os
    if arg.endswith('.json') or os.path.exists(arg):
        with open(arg) as f:
            data = json.load(f)
        return sorted((int(v[0]), int(v[1])) for v in data.values())
    intervals = []
    for part in arg.split(','):
        a, b = part.split('-')
        intervals.append((int(a), int(b)))
    for s, e in intervals:
        if not (1 <= s <= e <= nres):
            raise ValueError(f"domain {s}-{e} outside 1..{nres}")
    return sorted(intervals)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "tests/waveform_trpcage.csv"
    domains_arg = None
    if "--domains" in sys.argv:
        k = sys.argv.index("--domains")
        domains_arg = sys.argv[k + 1]
    idx, cur, nat = parse_final_structure(path)
    rmsd, rot, nat_c, R = kabsch_rmsd(cur, nat)
    dev = np.sqrt(((rot - nat_c) ** 2).sum(axis=1))

    if domains_arg is not None:
        intervals = parse_domains_arg(domains_arg, len(cur))
        print("Per-domain Kabsch RMSD (each domain aligned independently):")
        for k, (s, e) in enumerate(intervals, start=1):
            m = (idx >= s) & (idx <= e)
            d_rmsd, d_rot, d_nat_c, _ = kabsch_rmsd(cur[m], nat[m])
            d_dev = np.sqrt(((d_rot - d_nat_c) ** 2).sum(axis=1))
            print(f"  D{k} ({s}-{e}, {m.sum()} res): RMSD {d_rmsd:.3f} Å, "
                  f"max dev {d_dev.max():.3f} Å at residue {idx[m][np.argmax(d_dev)]}")
        # interface residues: within 10 positions on either side of each boundary
        iface = np.zeros(len(cur), dtype=bool)
        for s, e in intervals[:-1]:
            iface |= (idx > e - 10) & (idx <= e + 10)
        if iface.any():
            print(f"\nInterface region (±10 res around boundaries), global frame: "
                  f"mean dev {dev[iface].mean():.3f} Å, max {dev[iface].max():.3f} Å "
                  f"at residue {idx[iface][np.argmax(dev[iface])]}")
        print()

    print(f"Kabsch RMSD: {rmsd:.3f} Å")
    print()
    print("Per-residue deviation (Å):")
    for i, d in zip(idx, dev):
        print(f"  {i:2d}: {d:6.3f}")
    print()
    print(f"Max deviation:  {dev.max():.3f} Å at residue {idx[np.argmax(dev)]}")
    print(f"Mean deviation: {dev.mean():.3f} Å")
    print(f"Median deviation: {np.median(dev):.3f} Å")
    print()

    # Identify worst half (residues contributing most to RMSD)
    sq = dev ** 2
    total_sq = sq.sum()
    contrib = 100.0 * sq / total_sq
    print("Residues contributing >5% of total squared deviation:")
    for i, c in sorted(zip(idx, contrib), key=lambda x: -x[1]):
        if c > 5.0:
            print(f"  {i:2d}: {c:5.1f}%  ({dev[i-1]:.3f} Å)")
    print()

    # Local geometry comparison
    cur_angs = backbone_angles(rot)
    nat_angs = backbone_angles(nat_c)
    print("Backbone angles (cur vs native, degrees):")
    for i in range(len(cur_angs)):
        print(f"  {i+2:2d}: {cur_angs[i]:7.2f}  {nat_angs[i]:7.2f}  diff {cur_angs[i]-nat_angs[i]:7.2f}")
    print()

    cur_phi = dihedrals(rot)
    nat_phi = dihedrals(nat_c)
    print("Dihedrals (cur vs native, degrees):")
    for i in range(len(cur_phi)):
        print(f"  {i+2:2d}: {cur_phi[i]:7.2f}  {nat_phi[i]:7.2f}  diff {cur_phi[i]-nat_phi[i]:7.2f}")
    print()

    # Native contact satisfaction
    print("Native long-range contacts (i-j >= 5, Cα-Cα < 6.5 Å):")
    n = len(cur)
    for i in range(n - 5):
        for j in range(i + 5, n):
            d_nat = np.linalg.norm(nat_c[i] - nat_c[j])
            d_cur = np.linalg.norm(rot[i] - rot[j])
            if d_nat < 6.5:
                print(f"  ({i+1:2d},{j+1:2d})  native {d_nat:.2f}  cur {d_cur:.2f}  delta {d_cur-d_nat:+.2f}")


if __name__ == "__main__":
    main()
