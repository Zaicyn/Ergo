#!/usr/bin/env python3
"""bestofn_run.py — Phase-2 best-of-N serial GPU runner.

Compiles all seed variants (CPU-side) then runs them SERIALLY on the
GPU (one Vulkan job at a time; memory.free checked per run).

Usage:
  python3 min/ribosome/bestofn_run.py <outdir> <variant1.ergo> [variant2.ergo ...]
CSVs land in <outdir>/<name>.csv; a run.log records wall times.
"""

import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def sh(cmd, timeout=None):
    return subprocess.run(cmd, capture_output=True, timeout=timeout,
                          cwd=REPO)


def main():
    outdir = sys.argv[1]
    variants = sys.argv[2:]
    os.makedirs(outdir, exist_ok=True)
    log = open(os.path.join(outdir, "run.log"), "a")

    # compile all (CPU-side)
    bins = []
    for v in variants:
        name = os.path.basename(v).replace(".ergo", "")
        b = os.path.join("/tmp", f"bon_{name}")
        if not os.path.exists(b):
            r = sh(["python", "-m", "core", v, "--target", "spirv",
                    "--precision", "f32", "-o", b], timeout=600)
            if r.returncode != 0:
                log.write(f"BUILD-FAIL {name}: "
                          f"{r.stderr.decode()[-120:]}\n")
                log.flush()
                continue
        bins.append((name, b))

    # serial GPU runs
    for name, b in bins:
        csv_path = os.path.join(outdir, f"{name}.csv")
        if os.path.exists(csv_path):
            continue
        mem = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True).stdout.strip()
        log.write(f"{name}: start, gpu-mem-free {mem} MiB\n")
        log.flush()
        t0 = time.time()
        with open(csv_path, "w") as f:
            r = subprocess.run([b], stdout=f,
                               stderr=subprocess.DEVNULL, cwd=REPO)
        dt = time.time() - t0
        log.write(f"{name}: rc={r.returncode} wall {dt:.1f}s\n")
        log.flush()


if __name__ == "__main__":
    main()
