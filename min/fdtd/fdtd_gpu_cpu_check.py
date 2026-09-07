#!/usr/bin/env python3
"""CPU vs GPU correctness check for FDTD .ergo files.

Compiles each file for CPU (host-only) and GPU (SPIR-V), runs the same
number of steps, and compares the produced grid output line-by-line.

Original copied from min/ribosome/gpu_cpu_qcheck.py; adapted for FDTD
output format (three-column i j value) and files that use NSTEPS instead
of SEED/MAXFRAME.
"""

import argparse
import os
import re
import subprocess
import sys

REPO = "/home/zaiken/Ergo"


def sh(cmd, cwd=REPO, timeout=300):
    return subprocess.run(cmd, capture_output=True, text=True,
                        timeout=timeout, cwd=cwd)


def compile_and_run(path, target, nsteps):
    base = os.path.basename(path).replace(".ergo", "")
    out = f"/tmp/fdtd_check_{base}_{target}"
    with open(path) as f:
        src = f.read()
    lines = src.splitlines()
    out_lines = []
    for ln in lines:
        # Override NSTEPS parameter if requested
        if nsteps is not None:
            ln = re.sub(r"^(INTEGER,\s*PARAMETER\s*::\s*NSTEPS\s*=\s*)\d+",
                        rf"\g<1>{nsteps}", ln)
        out_lines.append(ln)
    tmp = f"/tmp/fdtd_check_{base}_{target}.ergo"
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


def clean_output(text):
    """Strip GPU driver info header and empty lines."""
    lines = []
    for ln in text.splitlines():
        if ln.startswith("[ergo_vk]"):
            continue
        if ln.strip() == "":
            continue
        lines.append(ln.rstrip())
    return lines


def parse_line(line):
    """Parse a three-column FDTD output line: i j value."""
    parts = line.split()
    if len(parts) != 3:
        return None
    try:
        return int(parts[0]), int(parts[1]), float(parts[2])
    except ValueError:
        return None


def compare_outputs(cpu_text, gpu_text, tol):
    cpu_lines = clean_output(cpu_text)
    gpu_lines = clean_output(gpu_text)

    if len(cpu_lines) != len(gpu_lines):
        return [("line_count", len(cpu_lines), len(gpu_lines), 0.0, 0.0)]

    diffs = []
    for i, (c, g) in enumerate(zip(cpu_lines, gpu_lines)):
        cpu_p = parse_line(c)
        gpu_p = parse_line(g)
        if cpu_p is None or gpu_p is None:
            if c != g:
                diffs.append((f"line_{i+1}", c, g, 0.0, 0.0))
            continue
        ci, cj, cv = cpu_p
        gi, gj, gv = gpu_p
        if ci != gi or cj != gj:
            diffs.append((f"line_{i+1}_index", (ci, cj), (gi, gj), 0.0, 0.0))
            continue
        ad = abs(cv - gv)
        if cv == 0.0 and gv == 0.0:
            rd = 0.0
        elif cv == 0.0:
            rd = abs(gv)
        else:
            rd = ad / abs(cv)
        if ad > tol:
            diffs.append((f"line_{i+1}_value", cv, gv, ad, rd))
    return diffs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", help=".ergo files to test")
    parser.add_argument("--nsteps", type=int, default=None,
                        help="Override NSTEPS parameter")
    parser.add_argument("--tol", type=float, default=1e-9,
                        help="Absolute tolerance for field value mismatch")
    args = parser.parse_args()

    mismatches = []

    for path in args.files:
        print(f"\n=== {path} ===")
        cpu = compile_and_run(path, "cpu", args.nsteps)
        gpu = compile_and_run(path, "gpu", args.nsteps)
        if "error" in cpu:
            print(f"  CPU {cpu['error']}: {cpu['stderr'][:200]}")
            mismatches.append((path, "cpu_error", cpu['stderr']))
            continue
        if "error" in gpu:
            print(f"  GPU {gpu['error']}: {gpu['stderr'][:200]}")
            mismatches.append((path, "gpu_error", gpu['stderr']))
            continue

        diffs = compare_outputs(cpu["stdout"], gpu["stdout"], args.tol)
        if diffs:
            print(f"  MISMATCH ({len(diffs)} lines)")
            for d in diffs[:10]:
                name, cv, gv, ad, rd = d
                print(f"    {name}: cpu={cv} gpu={gv} abs={ad:.6e} rel={rd:.6e}")
            if len(diffs) > 10:
                print(f"    ... and {len(diffs) - 10} more")
            mismatches.append((path, diffs))
        else:
            print(f"  OK ({len(clean_output(cpu['stdout']))} lines, identical)")

    print("\n=== SUMMARY ===")
    if not mismatches:
        print("No mismatches found.")
        return 0
    print(f"{len(mismatches)} mismatch/error cases:")
    for m in mismatches:
        path, kind, *rest = m
        if kind == "cpu_error":
            print(f"  {path}: CPU compile/run error")
        elif kind == "gpu_error":
            print(f"  {path}: GPU compile/run error")
        else:
            diffs = kind
            print(f"  {path}: {len(diffs)} mismatched lines")
    return 1


if __name__ == "__main__":
    sys.exit(main())
