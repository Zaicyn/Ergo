#!/usr/bin/env python3
"""
cluster_sigs.py — Cluster crystal-lane signatures into persistence classes.

Reads stdin output from `galaxy_sig` (produced by main_sig.ergo + sig_dump.ergo).
Expects a 77777-tagged block:

  77777
  <count>
  <ω_1> <ρ_1> <fmode_1> <vmag_1> <rnorm_1> <mgate_1> <zc_1> <fw_1>
  <ω_2> ...
  ...

Runs k-means and reports cluster centers + sizes. Each cluster is a candidate
persistence class.

Usage:
  ./galaxy_sig | python3 cluster_sigs.py [--k N] [--method kmeans|dbscan]
"""

import sys
import argparse
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler

DIMS = [
    "omega",
    "rho",
    "fmode",
    "vmag",
    "rnorm",
    "mgate",
    "zc",
    "fw",
    "gen",
    "energy",
    "ang_mom",
    "bin_pres",
]


def parse_dump(text):
    """Find the 77777 block in the input text, return (N, array[N, len(DIMS)]).

    Supports both the 8-field legacy format (archived logs from before
    2026-05-14) and the 12-field extended format. Detects which by
    counting values after the count line.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    try:
        idx = lines.index("77777")
    except ValueError:
        print("ERROR: no 77777 tag found in input. Did galaxy_sig run?", file=sys.stderr)
        sys.exit(1)
    n = int(lines[idx + 1])
    if n == 0:
        return 0, np.empty((0, len(DIMS)))

    # Try 12-field first (current); fall back to 8-field (legacy)
    flat_full = lines[idx + 2 : idx + 2 + n * len(DIMS)]
    if len(flat_full) == n * len(DIMS):
        flat = flat_full
        legacy_8 = False
    else:
        # Maybe an 8-field legacy log
        flat_legacy = lines[idx + 2 : idx + 2 + n * 8]
        if len(flat_legacy) == n * 8:
            print(
                f"NOTE: detected 8-field legacy log; padding 4 extended fields with NaN.",
                file=sys.stderr,
            )
            # Reshape to 8, then pad to len(DIMS)
            arr8 = np.array([float(x) for x in flat_legacy]).reshape(n, 8)
            pad = np.full((n, len(DIMS) - 8), np.nan)
            return n, np.concatenate([arr8, pad], axis=1)
        print(
            f"ERROR: expected {n * len(DIMS)} values (12-field) or "
            f"{n * 8} values (8-field legacy); got {len(flat_full)}.",
            file=sys.stderr,
        )
        sys.exit(1)
    arr = np.array([float(x) for x in flat]).reshape(n, len(DIMS))
    return n, arr


def describe(arr):
    print(f"\n=== Raw signature stats (N={len(arr)}) ===")
    for i, d in enumerate(DIMS):
        col = arr[:, i]
        print(
            f"  {d:>7}: min={col.min():+.4f} max={col.max():+.4f} "
            f"mean={col.mean():+.4f} std={col.std():+.4f}"
        )


def kmeans_classify(arr, k):
    """Standardize, k-means, report centers in original units."""
    scaler = StandardScaler()
    arr_z = scaler.fit_transform(arr)

    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(arr_z)
    centers_z = km.cluster_centers_
    centers = scaler.inverse_transform(centers_z)

    print(f"\n=== K-Means clustering (k={k}) ===")
    print(f"  Inertia: {km.inertia_:.2f}")
    print(f"  Cluster sizes: {[int((labels == c).sum()) for c in range(k)]}")
    print()
    print(f"  Cluster centers (original units):")
    header = "  " + " ".join(f"{d:>8}" for d in DIMS)
    print(header)
    for c in range(k):
        row = "  " + " ".join(f"{centers[c, i]:+8.4f}" for i in range(len(DIMS)))
        print(f"{row}   n={int((labels == c).sum())}")
    return labels, centers


def dbscan_classify(arr, eps=0.5, min_samples=5):
    scaler = StandardScaler()
    arr_z = scaler.fit_transform(arr)
    db = DBSCAN(eps=eps, min_samples=min_samples)
    labels = db.fit_predict(arr_z)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int((labels == -1).sum())

    print(f"\n=== DBSCAN clustering (eps={eps}, min_samples={min_samples}) ===")
    print(f"  Clusters found: {n_clusters}")
    print(f"  Noise points: {n_noise}/{len(arr)}")
    if n_clusters > 0:
        print()
        print(f"  Cluster centers (original units, computed as mean of members):")
        header = "  " + " ".join(f"{d:>8}" for d in DIMS)
        print(header)
        for c in range(n_clusters):
            members = arr[labels == c]
            row = "  " + " ".join(f"{members.mean(axis=0)[i]:+8.4f}" for i in range(len(DIMS)))
            print(f"{row}   n={len(members)}")
    return labels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=4, help="k for k-means (default 4)")
    ap.add_argument(
        "--method",
        choices=["kmeans", "dbscan", "both"],
        default="both",
        help="clustering method",
    )
    ap.add_argument("--eps", type=float, default=0.5, help="DBSCAN epsilon (default 0.5)")
    ap.add_argument(
        "--min-samples", type=int, default=5, help="DBSCAN min_samples (default 5)"
    )
    ap.add_argument(
        "--scan-k",
        action="store_true",
        help="Sweep k from 2-8 for k-means and report inertia (elbow analysis)",
    )
    args = ap.parse_args()

    text = sys.stdin.read()
    n, arr = parse_dump(text)
    print(f"Read {n} crystal-lane signatures.")

    if n == 0:
        print("No crystals formed. Nothing to cluster.")
        print(
            "(This is the expected pre-port baseline if particles never reach "
            "ω < OMEGA_CRYSTAL_THRESH.)"
        )
        return

    describe(arr)

    if args.scan_k:
        print("\n=== K-Means inertia scan ===")
        for k in range(2, 9):
            scaler = StandardScaler()
            arr_z = scaler.fit_transform(arr)
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            km.fit(arr_z)
            print(f"  k={k}: inertia={km.inertia_:.2f}")

    if args.method in ("kmeans", "both"):
        kmeans_classify(arr, args.k)

    if args.method in ("dbscan", "both"):
        dbscan_classify(arr, args.eps, args.min_samples)


if __name__ == "__main__":
    main()
