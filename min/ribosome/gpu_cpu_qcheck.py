#!/usr/bin/env python3
"""Quick CPU vs GPU correctness check for a list of .ergo sims.

Compiles each file for CPU and GPU (f64), runs a small number of seeded
frames, and compares the last CSV row.  Prints a summary of mismatches.
"""

import argparse
import csv
import os
import subprocess
import sys
import tempfile
import time

REPO = "/home/zaiken/Ergo"


def sh(cmd, cwd=REPO, timeout=300):
    return subprocess.run(cmd, capture_output=True, text=True,
                          timeout=timeout, cwd=cwd)


def compile_and_run(path, target, maxframe, seed):
    base = os.path.basename(path).replace(".ergo", "")
    out = f"/tmp/qcheck_{base}_{target}"
    with open(path) as f:
        src = f.read()
    # Replace SEED and MAXFRAME parameters
    import re
    lines = src.splitlines()
    out_lines = []
    for ln in lines:
        ln = re.sub(r"^(PARAMETER\s+\w+\s+::\s+SEED\s*=\s*)[^\s!]+",
                    rf"\g<1>{seed}", ln)
        ln = re.sub(r"^(PARAMETER\s+\w+\s+::\s+MAXFRAME\s*=\s*)[^\s!]+",
                    rf"\g<1>{maxframe}", ln)
        out_lines.append(ln)
    tmp = f"/tmp/qcheck_{base}_{target}.ergo"
    with open(tmp, "w") as f:
        f.write("\n".join(out_lines))

    cmd = ["python", "-m", "core", tmp, "-o", out, "--precision", "f64"]
    if target == "gpu":
        cmd.extend(["--target", "spirv"])
    r = sh(cmd)
    if r.returncode != 0:
        return {"error": "compile", "stderr": r.stderr[-500:]}

    r = sh([out], cwd="/tmp")
    if r.returncode != 0:
        return {"error": "run", "stderr": r.stderr[-500:]}

    return {"stdout": r.stdout}


def parse_last_row(csv_text):
    lines = csv_text.strip().splitlines()
    if not lines:
        return None
    header = None
    data_rows = []
    for ln in lines:
        if ln.startswith("frame,"):
            header = ln.split(",")
        elif ln.startswith("FINAL_STRUCTURE") or ln.startswith("END_FINAL_STRUCTURE"):
            break
        else:
            data_rows.append(ln)
    if not data_rows or header is None:
        return None
    reader = csv.DictReader([",".join(header)] + [data_rows[-1]])
    return next(iter(reader))


def compare(cpu_row, gpu_row, cols, tol):
    diffs = []
    for c in cols:
        if c not in cpu_row or c not in gpu_row:
            continue
        cv = float(cpu_row[c])
        gv = float(gpu_row[c])
        ad = abs(cv - gv)
        if cv == 0.0 and gv == 0.0:
            rd = 0.0
        elif cv == 0.0:
            rd = abs(gv)
        else:
            rd = ad / abs(cv)
        if ad > tol:
            diffs.append((c, cv, gv, ad, rd))
    return diffs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", help=".ergo files to test")
    parser.add_argument("--maxframe", type=int, default=500)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--seed-start", type=int, default=1000)
    parser.add_argument("--seed-step", type=int, default=37)
    parser.add_argument("--cols", default="rgyr,e_morse,e_angle,e_torsion,e_native",
                        help="Comma-separated columns to compare")
    parser.add_argument("--tol", type=float, default=1e-6,
                        help="Absolute tolerance for mismatch")
    args = parser.parse_args()

    cols = args.cols.split(",")
    seeds = [args.seed_start + i * args.seed_step for i in range(args.seeds)]
    mismatches = []

    for path in args.files:
        print(f"\n=== {path} ===")
        for seed in seeds:
            cpu = compile_and_run(path, "cpu", args.maxframe, seed)
            gpu = compile_and_run(path, "gpu", args.maxframe, seed)
            if "error" in cpu:
                print(f"  seed={seed} CPU {cpu['error']}: {cpu['stderr'][:200]}")
                mismatches.append((path, seed, "cpu_error", cpu['stderr']))
                continue
            if "error" in gpu:
                print(f"  seed={seed} GPU {gpu['error']}: {gpu['stderr'][:200]}")
                mismatches.append((path, seed, "gpu_error", gpu['stderr']))
                continue
            cpu_row = parse_last_row(cpu["stdout"])
            gpu_row = parse_last_row(gpu["stdout"])
            if cpu_row is None or gpu_row is None:
                print(f"  seed={seed} no CSV output")
                mismatches.append((path, seed, "no_csv", ""))
                continue
            diffs = compare(cpu_row, gpu_row, cols, args.tol)
            if diffs:
                print(f"  seed={seed} MISMATCH")
                for c, cv, gv, ad, rd in diffs:
                    print(f"    {c}: cpu={cv:.6f} gpu={gv:.6f} abs={ad:.6e} rel={rd:.6e}")
                mismatches.append((path, seed, diffs))
            else:
                print(f"  seed={seed} OK")

    print("\n=== SUMMARY ===")
    if not mismatches:
        print("No mismatches found.")
        return 0
    print(f"{len(mismatches)} mismatch/error cases:")
    for m in mismatches:
        path, seed, kind, *rest = m
        if kind == "cpu_error":
            print(f"  {path} seed={seed}: CPU compile/run error")
        elif kind == "gpu_error":
            print(f"  {path} seed={seed}: GPU compile/run error")
        elif kind == "no_csv":
            print(f"  {path} seed={seed}: no CSV output")
        else:
            diffs = kind
            print(f"  {path} seed={seed}: {len(diffs)} mismatched columns")
    return 1


if __name__ == "__main__":
    sys.exit(main())
