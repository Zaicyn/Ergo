#!/usr/bin/env python3
"""Ribosome f32 vs f64 basin-distribution stress sweep.

For a given base .ergo file, generate N seeded variants, compile each under
f32 and f64 (CPU and GPU), run them, and compare final-basin distributions.
"""

import argparse
import csv
import os
import random
import statistics
import subprocess
import sys
import tempfile
import time

REPO = "/home/zaiken/Ergo"
OUT = "/tmp/ribosome_sweep"


def sh(cmd, cwd=REPO, timeout=300):
    return subprocess.run(cmd, capture_output=True, text=True,
                          timeout=timeout, cwd=cwd)


def make_variant(base_path, seed, maxframe):
    with open(base_path) as f:
        src = f.read()
    src = replace_parameter(src, "SEED", seed)
    src = replace_parameter(src, "MAXFRAME", maxframe)
    return src


def replace_parameter(src, name, value):
    import re
    pattern = rf"^(PARAMETER\s+\w+\s+::\s+{name}\s*=\s*)[^\s!]+"
    lines = src.splitlines()
    out = []
    for ln in lines:
        out.append(re.sub(pattern, rf"\g<1>{value}", ln))
    return "\n".join(out)


def compile_and_run(src, label, precision, target, out_csv):
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, f"{label}_{precision}_{target}.ergo")
    exe = os.path.join(OUT, f"{label}_{precision}_{target}")
    with open(tmp, "w") as f:
        f.write(src)
    t0 = time.perf_counter()
    cmd = ["python", "-m", "core", tmp, "-o", exe]
    if target == "gpu":
        cmd.extend(["--target", "spirv"])
    cmd.extend(["--precision", precision])
    r = sh(cmd)
    compile_t = time.perf_counter() - t0
    if r.returncode != 0:
        return {"error": "compile", "stderr": r.stderr[-500:]}
    t0 = time.perf_counter()
    r = sh([exe], cwd=OUT)
    run_t = time.perf_counter() - t0
    if r.returncode != 0:
        return {"error": "run", "stderr": r.stderr[-500:]}
    with open(os.path.join(OUT, out_csv), "w") as f:
        f.write(r.stdout)
    row = parse_last_row(r.stdout)
    return {"compile_t": compile_t, "run_t": run_t, "stdout": r.stdout,
            "last_row": row}


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


def sweep(base_path, label, seeds, maxframe, targets=("cpu", "gpu"), precisions=("f32", "f64")):
    print(f"\n=== {label}: {base_path} | MAXFRAME={maxframe} | seeds={len(seeds)} ===")
    results = []
    for seed in seeds:
        src = make_variant(base_path, seed, maxframe)
        for prec in precisions:
            for target in targets:
                out_csv = f"{label}_seed{seed}_{prec}_{target}.csv"
                res = compile_and_run(src, label, prec, target, out_csv)
                row = res.get("last_row", {}) or {}
                res["seed"] = seed
                res["precision"] = prec
                res["target"] = target
                res["csv"] = out_csv
                res.update(row)
                results.append(res)
                status = "OK" if "error" not in res else res["error"]
                print(f"  seed={seed} {prec} {target}: {status} compile={res.get('compile_t', 0):.2f}s run={res.get('run_t', 0):.2f}s")
    return results


def summarize(results, cols=("rmsd_native", "rgyr", "e_torsion", "e_angle")):
    groups = {}
    for r in results:
        if "error" in r:
            continue
        key = (r["precision"], r["target"])
        groups.setdefault(key, []).append(r)
    print("\n--- basin statistics ---")
    header = f"{'precision':>8s} {'target':>6s} {'n':>4s}"
    for c in cols:
        header += f" {c:>14s}_mean {c:>14s}_std"
    print(header)
    for key, rows in sorted(groups.items()):
        vals = {c: [float(r[c]) for r in rows if c in r] for c in cols}
        parts = []
        for c in cols:
            v = vals[c]
            m = statistics.mean(v) if v else 0.0
            s = statistics.stdev(v) if len(v) > 1 else 0.0
            parts.append(f"{m:>16.4f} {s:>16.4f}")
        print(f"{key[0]:>8s} {key[1]:>6s} {len(rows):>4d} " + " ".join(parts))

    print("\n--- run times ---")
    for key, rows in sorted(groups.items()):
        ts = [r["run_t"] for r in rows]
        if ts:
            print(f"{key[0]:>8s} {key[1]:>6s}: mean={statistics.mean(ts):.3f}s "
                  f"min={min(ts):.3f}s max={max(ts):.3f}s")
        else:
            print(f"{key[0]:>8s} {key[1]:>6s}: no timing data")


def main():
    parser = argparse.ArgumentParser(
        description="Ribosome f32 vs f64 basin-distribution sweep.")
    parser.add_argument("base", nargs="?",
                        default=os.path.join(REPO, "min/ribosome/rna_hairpin_0.0.ergo"),
                        help="Base .ergo file")
    parser.add_argument("--label", default="sweep", help="Output label")
    parser.add_argument("--maxframe", type=int, default=2000,
                        help="MAXFRAME override")
    parser.add_argument("--seeds", type=int, default=20,
                        help="Number of seeded runs")
    parser.add_argument("--seed-start", type=int, default=1000)
    parser.add_argument("--seed-step", type=int, default=37)
    parser.add_argument("--targets", default="cpu,gpu",
                        help="Comma-separated list: cpu,gpu")
    parser.add_argument("--precisions", default="f32,f64",
                        help="Comma-separated list: f32,f64")
    parser.add_argument("--cols", default="rmsd_native,rgyr,e_torsion,e_angle",
                        help="Comma-separated columns to summarize")
    args = parser.parse_args()

    os.makedirs(OUT, exist_ok=True)
    seeds = [args.seed_start + i * args.seed_step for i in range(args.seeds)]
    targets = args.targets.split(",")
    precisions = args.precisions.split(",")
    cols = args.cols.split(",")
    res = sweep(args.base, args.label, seeds, args.maxframe,
                targets=targets, precisions=precisions)
    summarize(res, cols=cols)


if __name__ == "__main__":
    main()
