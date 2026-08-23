#!/usr/bin/env python3
"""corpus_audit.py — Phase-1 audit of the tracked tests/*.ergo corpus.

Compiles every tracked tests/*.ergo with the current compiler (IR
path), runs each with a bounded timeout, and classifies:

  PASS          compiles, runs exit 0, two runs byte-identical
  PASS-NONDET   compiles, runs exit 0, two runs DIFFER (finding!)
  SLOW          compiles, exceeds the run timeout (long sims)
  GPU-REQUIRED  CPU-path compile/run fails with a GPU-only reason,
                or filename marks it; retried with --target spirv
  FAIL-COMPILE  compiler rejects (message recorded)
  FAIL-RUNTIME  runs but exits nonzero / named runtime error

GPU candidates are compiled+run serially (one Vulkan job at a time).

Writes tests/golden/corpus_audit.json (machine-readable) and prints a
summary. Run from repo root: python3 tests/golden/corpus_audit.py
"""

import concurrent.futures as cf
import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
BINDIR = "/tmp/corpus_audit_bin"
RUN_TIMEOUT = 60
CC_TIMEOUT = 180
PAR_CC = 8
PAR_RUN = 4

GPU_HINTS = ("RING/WARP", "GPU kernels", "--target")


def sh(cmd, timeout, cwd=REPO):
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout,
                           cwd=cwd)
        return r.returncode, r.stdout, r.stderr, time.time() - t0
    except subprocess.TimeoutExpired:
        return None, b"", b"TIMEOUT", time.time() - t0


def last_line(blob):
    txt = blob.decode(errors="replace").strip()
    return txt.splitlines()[-1][:160] if txt else ""


def is_gpu_marked(path):
    base = os.path.basename(path)
    return base.startswith("gpu_") or "_gpu" in base


def compile_one(path, target=None):
    out = os.path.join(
        BINDIR, os.path.basename(path).replace(".ergo", "")
        + ("_spirv" if target else ""))
    cmd = ["python", "-m", "core", path, "-o", out]
    if target:
        cmd += ["--target", target]
    rc, so, se, dt = sh(cmd, CC_TIMEOUT)
    ok = rc == 0 and os.path.exists(out)
    return ok, out, last_line(se) or last_line(so), dt


def run_one(binary, timeout=RUN_TIMEOUT):
    return sh([binary], timeout)


def audit_cpu(path):
    """Compile + run on the CPU path; classify."""
    rec = {"file": path}
    ok, binary, msg, cdt = compile_one(path)
    rec["compile_s"] = round(cdt, 2)
    if not ok:
        rec["cls"] = "FAIL-COMPILE"
        rec["reason"] = msg
        if any(h in msg for h in GPU_HINTS):
            rec["cls"] = "GPU-CANDIDATE"
            rec["reason"] = msg
        return rec, None
    rc1, so1, se1, dt1 = run_one(binary)
    rec["run_s"] = round(dt1, 2)
    if rc1 is None:
        rec["cls"] = "SLOW"
        rec["reason"] = f"exceeds {RUN_TIMEOUT}s run timeout"
        return rec, binary
    if rc1 != 0:
        rec["cls"] = "FAIL-RUNTIME"
        rec["reason"] = last_line(se1) or f"exit {rc1}"
        return rec, binary
    # second run for determinism
    rc2, so2, se2, dt2 = run_one(binary)
    rec["run2_s"] = round(dt2, 2)
    if rc2 != 0:
        rec["cls"] = "FAIL-RUNTIME"
        rec["reason"] = "second run failed: " + last_line(se2)
        return rec, binary
    if so1 != so2:
        rec["cls"] = "PASS-NONDET"
        rec["reason"] = "two runs differ on stdout"
        return rec, binary
    rec["cls"] = "PASS"
    rec["reason"] = ""
    rec["stdout_bytes"] = len(so1)
    return rec, binary


def main():
    os.makedirs(BINDIR, exist_ok=True)
    files = sorted(subprocess.run(
        ["git", "ls-files", "tests/*.ergo"], cwd=REPO,
        capture_output=True, text=True).stdout.split())
    print(f"corpus: {len(files)} tracked tests/*.ergo")

    # ── pass 1: CPU compile, parallel ──
    results = {}
    with cf.ThreadPoolExecutor(PAR_CC) as ex:
        for rec, binary in ex.map(audit_cpu, files):
            results[rec["file"]] = rec
            if rec["cls"] != "PASS":
                print(f"  {rec['cls']:14s} {rec['file']}  {rec['reason']}")

    # ── pass 2: GPU candidates, serial ──
    gpu_files = [f for f in files
                 if results[f]["cls"] == "GPU-CANDIDATE"
                 or (is_gpu_marked(f)
                     and results[f]["cls"] != "PASS")]
    # also: gpu-marked files that PASSED on CPU still get a spirv
    # compile check (their real target is the GPU)
    gpu_files += [f for f in files
                  if is_gpu_marked(f) and results[f]["cls"] == "PASS"
                  and f not in gpu_files]
    for f in gpu_files:
        rec = results[f]
        ok, binary, msg, cdt = compile_one(f, target="spirv")
        rec["gpu_compile_s"] = round(cdt, 2)
        if not ok:
            rec["cls"] = "FAIL-COMPILE"
            rec["reason"] = "spirv: " + msg
            print(f"  GPU FAIL-COMPILE {f}  {msg}")
            continue
        rc, so, se, dt = run_one(binary)
        if rc is None:
            rec["cls"] = "GPU-SLOW"
            rec["reason"] = f"spirv run exceeds {RUN_TIMEOUT}s"
        elif rc != 0:
            rec["cls"] = "GPU-FAIL-RUNTIME"
            rec["reason"] = "spirv: " + (last_line(se) or f"exit {rc}")
        else:
            rec["cls"] = "GPU-PASS"
            rec["reason"] = ""
            rec["stdout_bytes"] = len(so)
        print(f"  {rec['cls']:14s} {f}  {rec['reason']}")

    # ── write the machine-readable report ──
    out = {
        "run_timeout_s": RUN_TIMEOUT,
        "files": [results[f] for f in files],
    }
    dst = os.path.join(REPO, "tests", "golden", "corpus_audit.json")
    with open(dst, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    counts = {}
    for rec in results.values():
        counts[rec["cls"]] = counts.get(rec["cls"], 0) + 1
    print("=" * 68)
    print("CORPUS AUDIT — class counts")
    for cls in sorted(counts):
        print(f"  {cls:16s} {counts[cls]}")
    print(f"report: tests/golden/corpus_audit.json")


if __name__ == "__main__":
    sys.exit(main())
