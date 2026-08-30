#!/usr/bin/env python3
"""run_contraction.py — contraction-policy verification (op map §4).

Checks:
  1. tests/fusible_stress.ergo: CPU(recipe) == GPU byte-identical, f64
     and f32 — plan A's strong property: deterministic fusible sites
     emit explicit fma/OpFma on both sides, fragile (call-factor) sites
     are barrier-unfused/NoContraction.  The contract=off reference is
     printed as informational (it differs exactly at the deterministic
     fma sites).
  2. tests/gpu_fallback_coil.ergo: CPU == GPU bitwise, f64 and f32
     (coil has no fusible sites — unchanged class).

GPU serializes: run one GPU binary at a time (the runner is sequential
by construction).

Run from repo root:  python3 tests/contraction/run_contraction.py
"""
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
RECIPE = ["-O3", "-fwrapv", "-march=x86-64-v3", "-ffp-contract=off",
          "-fno-math-errno", "-std=c11"]


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True,
                          timeout=kw.pop("timeout", 300), **kw)


def build_ergo(src, out, *flags):
    r = sh([sys.executable, "-m", "core", src, "-o", out, *flags],
           cwd=REPO)
    return r.returncode == 0, r


def run(binpath):
    r = sh([binpath], timeout=300)
    lines = [ln for ln in r.stdout.splitlines()
             if not ln.startswith("[ergo")]
    return "\n".join(lines) + "\n"


def one_precision(precision, label):
    ok = True
    src = "tests/fusible_stress.ergo"
    prec = ["--precision", "f32"] if precision == 32 else []
    ok_g, _ = build_ergo(src, f"/tmp/ctr_stress_gpu_{label}",
                         "--target", "spirv", *prec)
    ok_c, _ = build_ergo(src, f"/tmp/ctr_stress_cpu_{label}", *prec)
    if not (ok_g and ok_c):
        print(f"  FAIL {label}: build failed")
        return False
    gpu = run(f"/tmp/ctr_stress_gpu_{label}")
    cpu_fast = run(f"/tmp/ctr_stress_cpu_{label}")
    # Plan A (2026-08-29 window): deterministic fusible sites emit
    # explicit fma on CPU and OpFma on GPU; fragile sites are
    # barrier-unfused on CPU and NoContraction on GPU.  The strong
    # invariant is now CPU(recipe) == GPU byte-identical.
    if gpu == cpu_fast:
        print(f"  PASS {label}: CPU(recipe) == GPU byte-identical "
              f"(plan A by construction)")
    else:
        n = sum(1 for a, b in zip(gpu.splitlines(), cpu_fast.splitlines())
                if a != b)
        print(f"  FAIL {label}: CPU != GPU ({n} lines differ)")
        ok = False
    return ok


def coil(label, prec):
    prec_flags = ["--precision", "f32"] if prec == 32 else []
    ok_c, _ = build_ergo("tests/gpu_fallback_coil.ergo",
                         f"/tmp/ctr_coil_cpu_{label}", *prec_flags)
    ok_g, _ = build_ergo("tests/gpu_fallback_coil.ergo",
                         f"/tmp/ctr_coil_gpu_{label}", "--target", "spirv",
                         *prec_flags)
    if not (ok_c and ok_g):
        print(f"  FAIL coil {label}: build failed")
        return False
    cpu = run(f"/tmp/ctr_coil_cpu_{label}")
    gpu = run(f"/tmp/ctr_coil_gpu_{label}")
    if cpu == gpu:
        print(f"  PASS coil {label}: CPU == GPU byte-identical")
        return True
    print(f"  FAIL coil {label}: CPU != GPU")
    return False


def main():
    print("CONTRACTION POLICY (compiler-owned FMA — plan A, 2026-08-29 window)")
    ok = True
    ok &= one_precision(64, "f64")
    ok &= one_precision(32, "f32")
    ok &= coil("f64", 64)
    ok &= coil("f32", 32)
    print("POLICY PASS" if ok else "POLICY FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
