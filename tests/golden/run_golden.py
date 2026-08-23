#!/usr/bin/env python3
"""run_golden.py — A2 golden-output harness: both codegen paths, one verdict.

Compiles each corpus program through the IR path (default, supported)
and the legacy AST path (deprecated; driver use_ir=False), runs both,
and compares stdout byte-exact. The paths have known drift — expected
divergences are listed in KNOWN (with notes in KNOWN_DIVERGENCES.md);
a divergence NOT in KNOWN is reported as NEW (the burn-down alarm).

Deterministic: fixed corpus order, no timestamps, no absolute paths in
the report. Exit 0 when the harness itself ran to completion; read the
table for the verdicts.

Run from repo root:  python3 tests/golden/run_golden.py
"""

import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, REPO)

CORPUS = [
    "tests/alloc_smoke.ergo",
    "tests/allocate_bench.ergo",
    "tests/buc_colony.ergo",
    "tests/do_neg_step.ergo",
    "tests/dot_product.ergo",
    "tests/func_implicit_return.ergo",
    "tests/int64.ergo",
    "tests/loopvar_after.ergo",
    "tests/prng.ergo",
    "tests/sq2core.ergo",
    "tests/sq3core.ergo",
    "tests/sub_scalar_ref.ergo",
    "tests/test_first.ergo",
    "tests/write_formats.ergo",
    "min/fdtd/stencil_test.ergo",
    "min/dendrite/laplace_annulus.ergo",
]

# Expected divergences (details: KNOWN_DIVERGENCES.md). Anything else
# that differs is reported as NEW.
KNOWN = {
    # "tests/example.ergo": "reason",
}

RUN_TIMEOUT = 60  # seconds per binary


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=False,
                          timeout=kw.pop("timeout", 120), **kw)


def build_ir(path, out):
    r = sh(["python", "-m", "core", path, "-o", out], cwd=REPO)
    return r.returncode == 0, r


def build_legacy(path, out):
    # In-process (no CLI route by design); deprecation warning expected.
    code = (
        "from core.driver import compile_file; "
        f"compile_file({path!r}, output={out!r}, use_ir=False)"
    )
    r = sh([sys.executable, "-c", code], cwd=REPO)
    return r.returncode == 0, r


def main():
    rows = []
    for rel in CORPUS:
        ir_bin = "/tmp/golden_ir.bin"
        leg_bin = "/tmp/golden_leg.bin"
        ok_ir, r_ir = build_ir(rel, ir_bin)
        ok_leg, r_leg = build_legacy(rel, leg_bin)
        if not ok_ir or not ok_leg:
            note = ""
            if not ok_ir and ok_leg:
                # e.g. COMPLEX: IR raises cleanly, legacy lowers — a
                # documented known divergence class
                msg = (r_ir.stderr or b"").decode(errors="replace")
                note = "IR raises: " + msg.strip().splitlines()[-1][:60] \
                    if msg.strip() else "IR build failed"
                status = "KNOWN" if rel in KNOWN else "BUILD-DIVERGE"
            elif not ok_leg and ok_ir:
                msg = (r_leg.stderr or b"").decode(errors="replace")
                note = "legacy build fails: " + \
                    (msg.strip().splitlines()[-1][:60]
                     if msg.strip() else "?")
                status = "KNOWN" if rel in KNOWN else "BUILD-DIVERGE"
            else:
                note = "both builds fail"
                status = "KNOWN" if rel in KNOWN else "BUILD-DIVERGE"
            rows.append((rel, status, note))
            continue
        out_ir = sh([ir_bin], timeout=RUN_TIMEOUT).stdout
        out_leg = sh([leg_bin], timeout=RUN_TIMEOUT).stdout
        if out_ir == out_leg:
            rows.append((rel, "MATCH", ""))
        else:
            first = next(i for i, (a, b) in
                         enumerate(zip(out_ir, out_leg)) if a != b)
            note = f"outputs differ at byte {first}"
            status = "KNOWN" if rel in KNOWN else "NEW-DIVERGENCE"
            rows.append((rel, status, note))

    print("=" * 68)
    print("A2 GOLDEN HARNESS — IR vs legacy, byte-exact stdout")
    print("=" * 68)
    for rel, status, note in rows:
        print(f"  {status:14s} {rel}" + (f"  ({note})" if note else ""))
    n_match = sum(1 for r in rows if r[1] == "MATCH")
    n_known = sum(1 for r in rows if r[1] == "KNOWN")
    n_new = sum(1 for r in rows if r[1] not in ("MATCH", "KNOWN"))
    print("-" * 68)
    print(f"  {n_match} match, {n_known} known divergences, "
          f"{n_new} NEW divergences (of {len(rows)})")
    if n_new:
        print("  NEW divergences are the burn-down alarm — investigate "
              "before release.")

    # Stream suite (tests/stream/: file I/O Part 10 + .esf format) —
    # IR-only features, so they live outside the IR-vs-legacy corpus
    # but run as part of the golden gate.
    stream = os.path.join(REPO, "tests", "stream", "run_stream.py")
    if os.path.exists(stream):
        r = sh([sys.executable, stream], timeout=600)
        tail = r.stdout.decode(errors="replace").strip().splitlines()
        print("-" * 68)
        print("  STREAM SUITE (tests/stream/):")
        for ln in tail:
            print("  " + ln)
        if any(ln.lstrip().startswith("FAIL ") for ln in tail):
            print("  stream suite FAIL — investigate before release.")

    # Corpus regression (tests/golden/run_corpus.py): the audited
    # tests/ corpus compiled+run and diffed against recorded
    # baselines (SLOW class excluded from the default gate).
    corpus = os.path.join(REPO, "tests", "golden", "run_corpus.py")
    if os.path.exists(corpus):
        r = sh([sys.executable, corpus], timeout=1800)
        tail = r.stdout.decode(errors="replace").strip().splitlines()
        print("-" * 68)
        print("  CORPUS REGRESSION (tests/golden/run_corpus.py):")
        for ln in tail:
            print("  " + ln)
        if r.returncode != 0:
            print("  corpus regression FAILED — investigate before "
                  "release; re-record baselines only after review.")

    # Nodegraph suite (tests/nodegraph/: graph JSON → Ergo → binary
    # → oracle; Phase A of the node-graph design)
    ng = os.path.join(REPO, "tests", "nodegraph", "run_nodegraph.py")
    if os.path.exists(ng):
        r = sh([sys.executable, ng], timeout=600)
        tail = r.stdout.decode(errors="replace").strip().splitlines()
        print("-" * 68)
        print("  NODEGRAPH SUITE (tests/nodegraph/):")
        for ln in tail:
            print("  " + ln)
        if any(ln.lstrip().startswith("FAIL ") for ln in tail):
            print("  nodegraph suite FAIL — investigate before release.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
