"""Regression test for fragile-FMA SUB lowering.

Bug: a REAL ADD/SUB site whose product contains a call-class factor was
emitted with a fusion barrier, but SUB kept the '-' operator after the
site's sign transform. That turned (2*RAND(s) - 1) into
(2*RAND(s) + 1), shifting vesicle_asm's initial gas wholly outside the
simulation box.

The runtime check below covers both subtraction orientations:
  call-mul - scalar
  scalar - call-mul
"""

import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERGOC = [sys.executable, "-m", "core"]

SOURCE = r'''
IMPLICIT NONE
REAL :: A, B
A := 2.0 * RAND(123) - 1.0
B := 3.0 - 2.0 * RAND(124)
WRITE(*, "%.17e %.17e") A, B
'''

MASK64 = (1 << 64) - 1


def splitmix64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & MASK64
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & MASK64
    return x ^ (x >> 31)


def rand01(seed: int) -> float:
    return (splitmix64(seed) >> 11) * 2.0**-53


def test_fragile_fma_subtraction_orientations():
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "fragile_fma_sub.ergo")
        exe = os.path.join(td, "fragile_fma_sub")
        with open(src, "w") as f:
            f.write(SOURCE)
        subprocess.run(
            ERGOC + [src, "-o", exe], cwd=REPO, check=True,
            capture_output=True, text=True,
        )
        run = subprocess.run([exe], check=True, capture_output=True, text=True)

    got_a, got_b = (float(x) for x in run.stdout.split())
    exp_a = 2.0 * rand01(123) - 1.0
    exp_b = 3.0 - 2.0 * rand01(124)

    if abs(got_a - exp_a) > 1.0e-15:
        raise AssertionError(
            f"left-product SUB mislowered: got {got_a:.17e}, "
            f"expected {exp_a:.17e}; stdout={run.stdout!r}")
    if abs(got_b - exp_b) > 1.0e-15:
        raise AssertionError(
            f"right-product SUB mislowered: got {got_b:.17e}, "
            f"expected {exp_b:.17e}; stdout={run.stdout!r}")


if __name__ == "__main__":
    test_fragile_fma_subtraction_orientations()
    print("fragile-FMA subtraction regression test passed")
