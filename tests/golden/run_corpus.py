#!/usr/bin/env python3
"""run_corpus.py — corpus regression runner (Phase 3 of the tests/
corpus audit). Compile+run every classified corpus file and diff
stdout against the recorded baseline.

Classes come from tests/golden/corpus_audit.json (Phase 1, reviewed):
  PASS       CPU compile + run, diff vs corpus_baseline/<name>.out
  GPU-PASS   spirv compile + run (serial — one Vulkan job at a time),
             diff vs corpus_baseline/<name>.gpu.out
  SLOW       long sims — excluded unless --slow (300s timeout)
Baselines also carry a sha256 in corpus_baseline.json so the gate is
fast and the git diff shows exactly which outputs moved.

Usage (from repo root):
  python3 tests/golden/run_corpus.py              verify
  python3 tests/golden/run_corpus.py --record     (re)record baselines
  python3 tests/golden/run_corpus.py --slow       include the SLOW class
  python3 tests/golden/run_corpus.py --no-gpu     skip GPU-PASS files
  python3 tests/golden/run_corpus.py --only glob  subset (fnmatch)

Record baselines ONLY after reviewing current outputs for sanity —
the baseline is the oracle.
"""

import concurrent.futures as cf
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
HERE = os.path.join(REPO, "tests", "golden")
AUDIT = os.path.join(HERE, "corpus_audit.json")
BASEDIR = os.path.join(HERE, "corpus_baseline")
MANIFEST = os.path.join(HERE, "corpus_baseline.json")
BINDIR = "/tmp/corpus_run_bin"

CC_TIMEOUT = 180
RUN_TIMEOUT = 60
SLOW_TIMEOUT = 300
PAR_CC = 8
PAR_RUN = 4


def sh(cmd, timeout, cwd=REPO):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout,
                           cwd=cwd)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return None, b"", b"TIMEOUT"


def last_line(blob):
    t = blob.decode(errors="replace").strip()
    return t.splitlines()[-1][:120] if t else ""


def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


def one_cpu(path, slow):
    """Compile (IR) + run one CPU-class file. Returns (status, out,
    note)."""
    name = os.path.basename(path)[:-5]
    binary = os.path.join(BINDIR, name)
    rc, so, se = sh(["python", "-m", "core", path, "-o", binary],
                    CC_TIMEOUT)
    if rc != 0:
        return "BUILD-FAIL", b"", last_line(se)
    timeout = SLOW_TIMEOUT if slow else RUN_TIMEOUT
    rc, so, se = sh([binary], timeout)
    if rc is None:
        return "RUN-TIMEOUT", b"", f"exceeds {timeout}s"
    if rc != 0:
        return "RUN-FAIL", b"", last_line(se) or f"exit {rc}"
    return "OK", so, ""


def one_gpu(path, timeout=RUN_TIMEOUT):
    name = os.path.basename(path)[:-5]
    binary = os.path.join(BINDIR, name + "_spirv")
    rc, so, se = sh(["python", "-m", "core", path, "-o", binary,
                     "--target", "spirv"], CC_TIMEOUT)
    if rc != 0:
        return "BUILD-FAIL", b"", last_line(se)
    rc, so, se = sh([binary], timeout)
    if rc is None:
        return "RUN-TIMEOUT", b"", f"exceeds {timeout}s"
    if rc != 0:
        return "RUN-FAIL", b"", last_line(se) or f"exit {rc}"
    return "OK", so, ""


def main():
    record = "--record" in sys.argv
    slow = "--slow" in sys.argv
    use_gpu = "--no-gpu" not in sys.argv
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--only="):
            only = a.split("=", 1)[1]

    audit = json.load(open(AUDIT))
    entries = {e["file"]: e for e in audit["files"]}
    cpu_files = sorted(f for f, e in entries.items()
                       if e["cls"] == "PASS")
    gpu_files = sorted(f for f, e in entries.items()
                       if e["cls"] == "GPU-PASS")
    slow_files = sorted(f for f, e in entries.items()
                        if e["cls"] == "SLOW")
    gpu_slow_files = sorted(f for f, e in entries.items()
                            if e["cls"] == "GPU-SLOW")
    if only:
        cpu_files = [f for f in cpu_files if fnmatch.fnmatch(f, only)]
        gpu_files = [f for f in gpu_files if fnmatch.fnmatch(f, only)]
        slow_files = [f for f in slow_files if fnmatch.fnmatch(f, only)]
        gpu_slow_files = [f for f in gpu_slow_files
                          if fnmatch.fnmatch(f, only)]
    run_cpu = cpu_files + (slow_files if slow else [])
    if use_gpu and slow:
        gpu_files = gpu_files + gpu_slow_files

    manifest = {}
    if os.path.exists(MANIFEST):
        manifest = json.load(open(MANIFEST))
    os.makedirs(BINDIR, exist_ok=True)
    if record:
        os.makedirs(BASEDIR, exist_ok=True)

    rows = []

    def handle(path, tag, status, out, note):
        name = os.path.basename(path)[:-5]
        key = name + tag
        if status != "OK":
            rows.append((path, status, note))
            return None
        h = sha(out)
        lines = out.decode(errors="replace").splitlines()
        first = lines[0][:100] if lines else ""
        last = lines[-1][:100] if lines else ""
        if record:
            suffix = ".gpu.out" if tag else ".out"
            with open(os.path.join(BASEDIR, name + suffix), "wb") as f:
                f.write(out)
            manifest[key] = {"sha256": h, "bytes": len(out),
                             "first": first, "last": last}
            rows.append((path, "RECORDED", f"{len(out)} B"))
        else:
            base = manifest.get(key)
            if base is None:
                rows.append((path, "MISSING-BASELINE", ""))
            elif base["sha256"] != h:
                actual = f"/tmp/corpus_diff_{name}.out"
                with open(actual, "wb") as f:
                    f.write(out)
                rows.append((path, "DIFF",
                             f"sha {base['sha256']} -> {h}; "
                             f"actual saved to {actual}"))
            else:
                rows.append((path, "MATCH", ""))
        return h

    # CPU files: parallel compile+run
    with cf.ThreadPoolExecutor(PAR_CC) as ex:
        for path, (status, out, note) in zip(
                run_cpu,
                ex.map(lambda f: one_cpu(f, f in slow_files), run_cpu)):
            handle(path, "", status, out, note)

    # GPU files: serial (one Vulkan job at a time)
    gpu_slow_set = set(gpu_slow_files)
    for f in gpu_files:
        t = SLOW_TIMEOUT if f in gpu_slow_set else RUN_TIMEOUT
        status, out, note = one_gpu(f, t)
        handle(f, " (gpu)", status, out, note)

    if record:
        with open(MANIFEST, "w") as f:
            json.dump(manifest, f, indent=1, sort_keys=True)

    print("=" * 68)
    print("CORPUS REGRESSION — compile+run+diff vs baseline"
          + (" (RECORD mode)" if record else ""))
    print("=" * 68)
    bad = 0
    for path, status, note in rows:
        if status not in ("MATCH", "RECORDED"):
            print(f"  {status:16s} {path}  {note}")
            bad += 1
    n = len(rows)
    print("-" * 68)
    verb = "recorded" if record else "matched"
    print(f"  {n - bad}/{n} {verb}; {bad} problems"
          f"  (CPU {len(run_cpu)}, GPU {len(gpu_files)}, "
          f"SLOW {'included' if slow else 'excluded'})")
    if not record and bad:
        print("  DIFF/MISSING rows are the alarm — inspect "
              "tests/golden/corpus_baseline/ before re-recording.")
    return 1 if (bad and not record) else 0


if __name__ == "__main__":
    sys.exit(main())
