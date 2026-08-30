#!/usr/bin/env python3
"""run_m0_bench.py — M0 O3 perf driver: brute N^2 vs cell-list wall time.

For each N in the sweep, rewrites the @-tagged PARAMETER lines of
min/cell/nlist_bench.ergo into /tmp, compiles CPU (path 1 = brute,
path 2 = cell) and GPU (path 2), times RUNS runs each (median),
prints a CSV table. GPU jobs serialize (one at a time, sequential by
construction). Run from repo root:  python3 min/cell/run_m0_bench.py
"""

import math
import os
import re
import statistics
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TEMPLATE = os.path.join(REPO, "min", "cell", "nlist_bench.ergo")

SWEEP = [500, 1000, 2000, 5000, 10000, 20000]
RUNS = 3
RC = 1.2
SPC = 1.15
MARGIN = 0.6
MAXNBR = 256


def variant(n, path):
    """Return (source_text, label) for one (N, path) bench point."""
    ng = math.ceil(n ** (1.0 / 3.0))
    lbox = (ng - 1) * SPC + 2.0 * MARGIN
    nc = int(lbox / RC)
    ce = lbox / nc
    ncell = nc ** 3
    src = open(TEMPLATE).read()
    subs = [
        (r"PARAMETER INTEGER :: NB = \d+", f"PARAMETER INTEGER :: NB = {n}"),
        (r"PARAMETER INTEGER :: PATH = \d+", f"PARAMETER INTEGER :: PATH = {path}"),
        (r"PARAMETER INTEGER :: NG = \d+", f"PARAMETER INTEGER :: NG = {ng}"),
        (r"PARAMETER REAL :: LBOX = [\d.]+", f"PARAMETER REAL :: LBOX = {lbox:.17g}"),
        (r"PARAMETER INTEGER :: NC = \d+", f"PARAMETER INTEGER :: NC = {nc}"),
        (r"PARAMETER REAL :: CE = [\d.]+", f"PARAMETER REAL :: CE = {ce:.17g}"),
        (r"PARAMETER INTEGER :: NCELL = \d+", f"PARAMETER INTEGER :: NCELL = {ncell}"),
        (r"PARAMETER INTEGER :: NSLOT = \d+", f"PARAMETER INTEGER :: NSLOT = {n * MAXNBR}"),
    ]
    for pat, rep in subs:
        src, cnt = re.subn(pat, rep, src, count=1)
        assert cnt == 1, f"pattern not found: {pat}"
    return src


def build(src, target, out):
    srcp = out + ".ergo"
    with open(srcp, "w") as f:
        f.write(src)
    cmd = [sys.executable, "-m", "core", srcp, "-o", out]
    if target == "spirv":
        cmd += ["--target", "spirv"]
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, timeout=600)
    if r.returncode != 0:
        print(r.stderr.decode(errors="replace")[-2000:])
        raise SystemExit(f"build failed: {out}")


def time_runs(binary, runs):
    ts = []
    line = ""
    for _ in range(runs):
        t0 = time.perf_counter()
        r = subprocess.run([binary], capture_output=True, timeout=3600)
        ts.append(time.perf_counter() - t0)
        line = r.stdout.decode(errors="replace").strip().splitlines()[-1]
    return statistics.median(ts), line


def main():
    print("N,path,target,median_s,summary")
    for n in SWEEP:
        for path, target in ((1, "cpu"), (2, "cpu"), (2, "spirv")):
            if n * MAXNBR * 8 * 2 > 512 * 1024 * 1024 and target == "spirv":
                continue  # keep device buffers comfortably small
            label = f"m0b_{n}_{path}_{target}"
            out = os.path.join("/tmp", label)
            src = variant(n, path)
            build(src, target, out)
            med, line = time_runs(out, RUNS)
            tag = {1: "brute", 2: "cell"}[path]
            tname = {"cpu": "cpu", "spirv": "gpu"}[target]
            print(f"{n},{tag},{tname},{med:.4f},{line}", flush=True)


if __name__ == "__main__":
    main()
