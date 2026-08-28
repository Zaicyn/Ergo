"""Regression test for the ul18_stag5 f32 SPIR-V hang.

Fresh f32 SPIR-V builds of `min/ribosome/ul18_stag5.ergo` hang between
frame 500 and frame 1000 under the current working tree.  This test
compiles a MAXFRAME=1000 copy and verifies it finishes within a timeout.

2026-08-28 root cause (fixed in b74f029-era commits): NOT a hang — the
misextracted INIT_CHAIN coil loop (DO-WHILE temporaries read as host
push constants) plus a stale host-fallback download wrote zeros over
the position arrays, which NaN'd the physics mid-run (f32). The fixed
build completes MAXFRAME=1000 in ~38s on the RTX 2060 (uniformly
~43 ms/frame, host-sync-bound — the padded segmented-reduction pair
kernels drain per kernel per substep; NSUB stays 1-2, measured).
TIMEOUT_SEC is 120s = >3x the measured workload bound; a real hang
(fence deadlock / host spin) still fails fast against it.
"""

import os
import subprocess
import sys
import tempfile


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERGOC = [sys.executable, "-m", "core"]
SOURCE = os.path.join(REPO, "min", "ribosome", "ul18_stag5.ergo")
TIMEOUT_SEC = 120
MAXFRAME = 1000


def test_stag5_f32_spirv_does_not_hang():
    if not os.path.exists(SOURCE):
        raise AssertionError(f"missing source: {SOURCE}")

    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "ul18_stag5_mf1000.ergo")
        exe = os.path.join(td, "ul18_stag5_mf1000")

        with open(SOURCE, "r") as f:
            text = f.read()
        text = text.replace(
            "PARAMETER INTEGER :: MAXFRAME = 144000",
            f"PARAMETER INTEGER :: MAXFRAME = {MAXFRAME}",
        )
        with open(src, "w") as f:
            f.write(text)

        subprocess.run(
            ERGOC + [src, "--target", "spirv", "--precision", "f32", "-o", exe],
            cwd=REPO, check=True, capture_output=True, text=True,
        )

        try:
            result = subprocess.run(
                [exe], capture_output=True, text=True, timeout=TIMEOUT_SEC,
            )
        except subprocess.TimeoutExpired as exc:
            raise AssertionError(
                f"stag5 f32 SPIR-V did not complete within {TIMEOUT_SEC}s; "
                f"likely hung. stderr={exc.stderr!r}"
            ) from exc

        if result.returncode != 0:
            raise AssertionError(
                f"stag5 f32 SPIR-V exited with rc={result.returncode}; "
                f"stderr={result.stderr!r}"
            )

        lines = result.stdout.splitlines()
        frame_lines = [ln for ln in lines if ln.startswith("10,") or ln.startswith("frame,")]
        if len(frame_lines) < 2:
            raise AssertionError(
                f"stag5 f32 SPIR-V did not emit expected frame output; "
                f"rc={result.returncode}, stdout={result.stdout!r}, "
                f"stderr={result.stderr!r}"
            )


if __name__ == "__main__":
    test_stag5_f32_spirv_does_not_hang()
    print("stag5 f32 SPIR-V hang regression test passed")
