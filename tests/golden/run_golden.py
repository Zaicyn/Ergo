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
    # 2026-09-04: the two plan-A-window entries (buc_colony,
    # laplace_annulus) were REMOVED — their IR-vs-legacy divergence was
    # root-caused to the fragile-FMA SUB mislowering (2*RAND(s)-1
    # computed as +1), fixed in fc721c2; both paths have matched
    # byte-exact since. (The 8-29 plan-A attribution was wrong —
    # recorded honestly in KNOWN_DIVERGENCES.md.)
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

    # Render codegen compile check (2026-09-04, B2): --render without
    # --target must compile a particle-SoA program (compile only —
    # running it opens a window). Pre-fix the particle epilogue
    # referenced undeclared _color_buf / grid buffers.
    rop = os.path.join(REPO, "tests", "render_only_particles.ergo")
    if os.path.exists(rop):
        out = "/tmp/render_only_particles_gate"
        r = sh([sys.executable, "-m", "core", rop, "--render",
                "-o", out], timeout=300)
        print("-" * 68)
        print("  RENDER COMPILE CHECK (tests/render_only_particles.ergo):")
        if r.returncode == 0 and os.path.exists(out):
            print("    PASS      render-only particle --render compiles")
        else:
            print("    FAIL      render-only particle --render "
                  "compile failed — investigate before release.")
            print(r.stderr.decode(errors="replace")[-800:])

    # W0 capture regression (2026-09-05): offscreen PNG dump,
    # double-run byte-compare + nonblack content.  Runs the render-only
    # MRE twice with ERGO_OFFSCREEN=1 ERGO_SHOT_EVERY=10 in two scratch
    # dirs (headless, no window).  Spec/Ergo_Render_Capture_W0_Design.md.
    if os.path.exists(rop):
        import glob as _glob
        import shutil as _shutil
        import zlib as _zlib
        print("-" * 68)
        print("  CAPTURE REGRESSION (W0 offscreen PNG dump):")
        ok = True
        shots = []
        for tag in ("w0cap_a", "w0cap_b"):
            d = f"/tmp/{tag}"
            _shutil.rmtree(d, ignore_errors=True)
            os.makedirs(d)
            r = sh(["/tmp/render_only_particles_gate"],
                   timeout=120, cwd=d,
                   env={**os.environ, "ERGO_OFFSCREEN": "1",
                        "ERGO_SHOT_EVERY": "10", "ERGO_ORBIT": "0"})
            got = sorted(_glob.glob(os.path.join(d, "shot_*.png")))
            if r.returncode != 0 or not got:
                ok = False
                print(f"    FAIL      {tag}: rc={r.returncode} "
                      f"shots={len(got)}")
                print(r.stderr.decode(errors="replace")[-400:])
            shots.append(got)
        if ok:
            a, b = shots
            if len(a) != len(b):
                ok = False
                print(f"    FAIL      shot count differs "
                      f"({len(a)} vs {len(b)})")
            else:
                import filecmp
                moved = [os.path.basename(x) for x, y in zip(a, b)
                         if not filecmp.cmp(x, y, shallow=False)]
                if moved:
                    ok = False
                    print(f"    FAIL      double-run PNGs differ: {moved[:3]}")
        if ok:
            # nonblack: decode the last shot's IDAT (stored blocks) and
            # require some nonzero pixel byte
            raw = open(a[-1], "rb").read()
            pos, idat = 8, b""
            while pos < len(raw):
                ln = int.from_bytes(raw[pos:pos + 4], "big")
                typ = raw[pos + 4:pos + 8]
                if typ == b"IDAT":
                    idat += raw[pos + 8:pos + 8 + ln]
                pos += 12 + ln
            data = _zlib.decompress(idat)
            if not any(b_ for i, b_ in enumerate(data)
                       if b_ and (i % (800 * 3 + 1)) != 0):
                ok = False
                print("    FAIL      capture is all black")
        if ok:
            print(f"    PASS      offscreen double-run byte-identical, "
                  f"nonblack ({len(shots[0])} shots)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
