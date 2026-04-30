#!/usr/bin/env python3
"""Cluster resonance signatures from Ergo simulation output.

Reads crystallization signatures from simulation stdout, clusters them
with k-means, and reports the emergent material archetypes.

Usage:
    # Run simulation, capture output:
    timeout 300 ./galaxy_gpu 2>&1 | tee /tmp/sim_output.txt

    # Cluster the signatures:
    python tools/cluster_signatures.py /tmp/sim_output.txt

    # Or pipe directly:
    timeout 300 ./galaxy_gpu 2>&1 | python tools/cluster_signatures.py -

    # Specify number of clusters:
    python tools/cluster_signatures.py /tmp/sim_output.txt --clusters 8

Signature format (8 floats per crystallization event):
    [0] OMEGA      — metabolic energy at death (0.0 - 2.0)
    [1] RHO_NORM   — local density normalized (0.0 - 1.0+)
    [2] FMODE      — flow mode at death (0.0, 1.0, or 2.0)
    [3] V_MAG      — velocity magnitude at death
    [4] R_NORM     — radius normalized to DISK_OUTER_R (0.0 - 1.0+)
    [5] MET_GATE   — metabolic gate coverage (0.2 - 1.5)
    [6] Z_C        — |Z_COUPLING| at ring position (0.0 - 1.0)
    [7] FLOW_W     — |FLOW_W| at ring position (0.0 - 0.34)
"""

import sys
import numpy as np
from pathlib import Path

FIELD_NAMES = [
    "OMEGA", "RHO_NORM", "FMODE", "V_MAG",
    "R_NORM", "MET_GATE", "Z_C", "FLOW_W"
]


def parse_signatures(lines):
    """Extract 8-float signatures from simulation output.

    The census prints SIG_COUNT followed by 8 floats per signature.
    We look for sequences of 8 consecutive float-parseable lines
    that follow a count line.
    """
    signatures = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        # Try to find a signature count (integer followed by 8*N floats)
        try:
            count = int(line)
        except ValueError:
            continue

        # Sanity: count should be reasonable (1-4096)
        if count < 1 or count > 4096:
            continue

        # Check if we have enough lines for count * 8 floats
        if i + count * 8 > len(lines):
            continue

        # Try to parse count signatures
        valid = True
        batch = []
        for s in range(count):
            sig = []
            for f in range(8):
                if i >= len(lines):
                    valid = False
                    break
                try:
                    val = float(lines[i].strip())
                    sig.append(val)
                    i += 1
                except ValueError:
                    valid = False
                    break
            if not valid:
                break
            if len(sig) == 8:
                batch.append(sig)

        if batch:
            signatures.extend(batch)

    return np.array(signatures) if signatures else None


def kmeans(data, k, max_iter=100):
    """Simple k-means clustering. No sklearn dependency."""
    n, d = data.shape

    # Initialize centroids from random data points
    rng = np.random.RandomState(42)
    idx = rng.choice(n, size=k, replace=False)
    centroids = data[idx].copy()

    labels = np.zeros(n, dtype=int)

    for iteration in range(max_iter):
        # Assign each point to nearest centroid
        old_labels = labels.copy()
        for i in range(n):
            dists = np.sum((centroids - data[i]) ** 2, axis=1)
            labels[i] = np.argmin(dists)

        # Check convergence
        if np.all(labels == old_labels):
            break

        # Update centroids
        for c in range(k):
            members = data[labels == c]
            if len(members) > 0:
                centroids[c] = members.mean(axis=0)

    return labels, centroids


def analyze_clusters(data, labels, centroids, k):
    """Print cluster analysis with material-like descriptions."""

    print("\n" + "=" * 70)
    print("EMERGENT MATERIAL ARCHETYPES")
    print("=" * 70)
    print(f"\n{len(data)} crystallization events → {k} clusters\n")

    # Sort clusters by population (largest first)
    counts = [(np.sum(labels == c), c) for c in range(k)]
    counts.sort(reverse=True)

    for rank, (count, c) in enumerate(counts):
        if count == 0:
            continue

        pct = 100.0 * count / len(data)
        center = centroids[c]
        members = data[labels == c]
        stds = members.std(axis=0)

        print(f"── Cluster {rank} (ID={c}, n={count}, {pct:.1f}%) ──")
        print(f"  {'Field':<12} {'Center':>8} {'StdDev':>8}  Description")
        print(f"  {'─'*12} {'─'*8} {'─'*8}  {'─'*30}")

        descriptions = []
        for i, name in enumerate(FIELD_NAMES):
            val = center[i]
            std = stds[i]
            desc = describe_field(name, val)
            print(f"  {name:<12} {val:8.4f} {std:8.4f}  {desc}")
            descriptions.append(desc)

        # Guess a material name from the signature
        material = guess_material(center)
        print(f"\n  → Suggested archetype: {material}\n")


def describe_field(name, val):
    """Human-readable description of a field value."""
    if name == "OMEGA":
        if val < 0.01:
            return "dead (no metabolic energy)"
        elif val < 0.05:
            return "near-floor"
        elif val < 0.2:
            return "low energy"
        elif val < 0.5:
            return "moderate energy"
        else:
            return "high energy"

    elif name == "RHO_NORM":
        if val < 0.1:
            return "sparse (void)"
        elif val < 0.3:
            return "low density"
        elif val < 0.6:
            return "moderate density"
        else:
            return "high density"

    elif name == "FMODE":
        if val < 0.5:
            return "COAST (decayed, gravity only)"
        elif val < 1.5:
            return "ACTIVE (full coupling)"
        else:
            return "FLOW (escape channel)"

    elif name == "V_MAG":
        if val < 1.0:
            return "slow (outer orbit)"
        elif val < 3.0:
            return "moderate orbit"
        elif val < 6.0:
            return "fast (inner orbit)"
        else:
            return "very fast (near core)"

    elif name == "R_NORM":
        if val < 0.1:
            return "core"
        elif val < 0.3:
            return "inner disk"
        elif val < 0.7:
            return "mid disk"
        else:
            return "outer halo"

    elif name == "MET_GATE":
        if val < 0.5:
            return "sparse coverage"
        elif val < 1.0:
            return "partial coverage"
        elif val < 1.3:
            return "good coverage"
        else:
            return "full coverage (all gens)"

    elif name == "Z_C":
        if val < 0.2:
            return "weak coupling"
        elif val < 0.5:
            return "moderate coupling"
        else:
            return "strong coupling"

    elif name == "FLOW_W":
        if val < 0.1:
            return "node (no flow)"
        elif val < 0.2:
            return "weak flow"
        else:
            return "strong flow window"

    return ""


def guess_material(center):
    """Guess a material name from signature center."""
    omega, rho, fmode, vmag, rnorm, mgate, zc, fw = center

    # Core remnant: high velocity, low radius, high density
    if rnorm < 0.2 and vmag > 4.0:
        return "CORE_REMNANT (neutron-star-like)"

    # Dense inner: moderate radius, high density
    if rnorm < 0.4 and rho > 0.4:
        return "DENSE_INNER (white-dwarf-like)"

    # Active death: died while ACTIVE, moderate everything
    if fmode > 0.5 and fmode < 1.5:
        return "ACTIVE_REMNANT (main-sequence death)"

    # Flow death: died in FLOW mode, had escape channel
    if fmode > 1.5:
        return "FLOW_REMNANT (ejection-path death)"

    # Outer halo: low density, slow, large radius
    if rnorm > 0.6 and vmag < 2.0:
        return "HALO_DUST (diffuse outer material)"

    # Coast death: standard decay, nothing special
    if fmode < 0.5:
        if rho > 0.3:
            return "COAST_DENSE (decayed in crowd)"
        else:
            return "COAST_SPARSE (decayed alone)"

    return "UNKNOWN"


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Cluster resonance signatures from Ergo simulation")
    parser.add_argument("input", help="Simulation output file (or - for stdin)")
    parser.add_argument("--clusters", "-k", type=int, default=6,
                        help="Number of clusters (default: 6)")
    parser.add_argument("--raw", action="store_true",
                        help="Print raw signature data")
    args = parser.parse_args()

    # Read input
    if args.input == "-":
        lines = sys.stdin.readlines()
    else:
        lines = Path(args.input).read_text().splitlines()

    # Parse signatures
    data = parse_signatures(lines)

    if data is None or len(data) == 0:
        print("No signatures found in input.")
        print("Make sure the simulation ran long enough for crystallization events.")
        sys.exit(1)

    print(f"Parsed {len(data)} crystallization signatures")

    if args.raw:
        print("\nRaw signatures:")
        print(f"{'OMEGA':>8} {'RHO':>8} {'FMODE':>6} {'V_MAG':>8} "
              f"{'R_NORM':>8} {'MGATE':>8} {'Z_C':>8} {'FLOW_W':>8}")
        for row in data[:50]:  # first 50
            print(" ".join(f"{v:8.4f}" for v in row))
        if len(data) > 50:
            print(f"  ... ({len(data) - 50} more)")

    # Normalize for clustering (each field to 0-1 range)
    data_norm = data.copy()
    mins = data.min(axis=0)
    maxs = data.max(axis=0)
    ranges = maxs - mins
    ranges[ranges < 1e-10] = 1.0  # avoid division by zero
    data_norm = (data - mins) / ranges

    # Cluster
    k = min(args.clusters, len(data))
    if k < 2:
        print("Need at least 2 signatures to cluster.")
        sys.exit(1)

    labels, centroids_norm = kmeans(data_norm, k)

    # Un-normalize centroids for display
    centroids = centroids_norm * ranges + mins

    # Analyze
    analyze_clusters(data, labels, centroids, k)

    # Summary table
    print("=" * 70)
    print("ARCHETYPE SUMMARY (for constants.ergo MAT_* LUTs)")
    print("=" * 70)
    counts = [(np.sum(labels == c), c) for c in range(k)]
    counts.sort(reverse=True)
    print(f"\n{'ID':>3} {'Count':>6} {'%':>6}  {'Material':<30} "
          f"{'COH':>4} {'ENR':>4} {'MOB':>4} {'REA':>4} {'PER':>4}")
    for rank, (count, c) in enumerate(counts):
        if count == 0:
            continue
        center = centroids[c]
        material = guess_material(center)
        # Map signature to nibble-scale material properties (0-15)
        coh = int(np.clip(15 - center[4] * 10, 0, 15))  # closer to center = more coherent
        enr = int(np.clip(center[0] * 15 / 2.0, 0, 15))  # OMEGA → energy
        mob = int(np.clip(center[3] * 2, 0, 15))          # velocity → mobility
        rea = int(np.clip(center[1] * 15, 0, 15))         # density → reactivity
        per = int(np.clip(15 - center[2] * 3, 0, 15))     # COAST = persistent
        print(f"{rank:3d} {count:6d} {100*count/len(data):5.1f}%  {material:<30} "
              f"{coh:4d} {enr:4d} {mob:4d} {rea:4d} {per:4d}")

    print(f"\nTotal signatures: {len(data)}")
    print("Copy the COH/ENR/MOB/REA/PER values into constants.ergo MAT_* DATA statements.")


if __name__ == "__main__":
    main()
