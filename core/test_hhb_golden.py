"""Golden test: HANDSHAKE block vs hand-lowered equivalent.

Verifies that the emitted boundary checks do not perturb numerics:
the handshake program and its hand-lowered equivalent must produce
bitwise-identical output for both f64 and f32 precisions.
"""

import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERGOC = [sys.executable, "-m", "core"]

HANDSHAKE_SRC = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
REAL :: X
X := 0.0
HANDSHAKE simple
    DEPTH=1
    FRAME_BYTES=256
    MAXIT=10
    PAYLOAD=(X)
    ORACLE X VALUE=0.8 LIMIT=1.0E-3
  DO I = 1, N
    X := X + 0.1
  ENDDO
ENDHANDSHAKE
WRITE(*, "('X = %.6e')") X
"""

MANUAL_SRC = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
REAL :: X
X := 0.0
DO I = 1, N
  X := X + 0.1
ENDDO
IF (ABS(X - 0.8) > 1.0E-3) THEN
  WRITE(*, "('HHB_SCANFAIL handshake=simple kind=ORACLE name=X line=0')")
  STOP
ENDIF
WRITE(*, "('X = %.6e')") X
"""

MULTI_HANDSHAKE_SRC = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 4
INTEGER :: I
REAL :: A, B, M, C
A := 0.0
B := 1.0
C := 2.0
HANDSHAKE two_stage
    DEPTH=2
    FRAME_BYTES=256
    MAXIT=10
    PAYLOAD=(M, C)
    CONSERVE NORM VALUE=C TOL=1.0E-6
    ORACLE A VALUE=0.5 LIMIT=1.0E-3
  DO I = 1, N
    A := A + 0.125
  ENDDO
  M := A
  DO I = 1, N
    B := B - 0.125
  ENDDO
ENDHANDSHAKE
WRITE(*, "('A = %.6e B = %.6e M = %.6e C = %.6e')") A, B, M, C
"""

MULTI_MANUAL_SRC = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 4
INTEGER :: I
REAL :: A, B, M, C
A := 0.0
B := 1.0
C := 2.0
! entry capture for CONSERVE NORM
IF (ABS(C - C) > 1.0E-6) THEN
  WRITE(*, "('HHB_SCANFAIL handshake=two_stage kind=CONSERVE name=NORM line=0')")
  STOP
ENDIF
DO I = 1, N
  A := A + 0.125
ENDDO
M := A
IF (ABS(A - 0.5) > 1.0E-3) THEN
  WRITE(*, "('HHB_SCANFAIL handshake=two_stage kind=ORACLE name=A line=0')")
  STOP
ENDIF
IF (ABS(C - C) > 1.0E-6) THEN
  WRITE(*, "('HHB_SCANFAIL handshake=two_stage kind=CONSERVE name=NORM line=0')")
  STOP
ENDIF
DO I = 1, N
  B := B - 0.125
ENDDO
IF (ABS(A - 0.5) > 1.0E-3) THEN
  WRITE(*, "('HHB_SCANFAIL handshake=two_stage kind=ORACLE name=A line=0')")
  STOP
ENDIF
IF (ABS(C - C) > 1.0E-6) THEN
  WRITE(*, "('HHB_SCANFAIL handshake=two_stage kind=CONSERVE name=NORM line=0')")
  STOP
ENDIF
WRITE(*, "('A = %.6e B = %.6e M = %.6e C = %.6e')") A, B, M, C
"""


def _compile_and_run(source: str, precision: str) -> tuple[str, int]:
    with tempfile.TemporaryDirectory() as td:
        src_path = os.path.join(td, "test.ergo")
        exe_path = os.path.join(td, "test")
        with open(src_path, "w") as f:
            f.write(source)
        subprocess.run(
            ERGOC + [src_path, "-o", exe_path, "--precision", precision],
            cwd=REPO, check=True, capture_output=True, text=True,
        )
        result = subprocess.run([exe_path], capture_output=True, text=True)
        return result.stdout, result.returncode


def _check_pair(name: str, h_src: str, m_src: str):
    for prec in ("f64", "f32"):
        h_out, h_rc = _compile_and_run(h_src, prec)
        m_out, m_rc = _compile_and_run(m_src, prec)
        if h_out != m_out:
            print(f"FAIL {name} {prec}: outputs differ")
            print("HANDSHAKE:", repr(h_out))
            print("MANUAL:   ", repr(m_out))
            sys.exit(1)
        if h_rc != 0:
            print(f"FAIL {name} {prec}: handshake exited {h_rc}, output {h_out!r}")
            sys.exit(1)
        print(f"OK {name} {prec}: {h_out!r}")


def main():
    _check_pair("single-stage", HANDSHAKE_SRC, MANUAL_SRC)
    _check_pair("multi-stage", MULTI_HANDSHAKE_SRC, MULTI_MANUAL_SRC)
    print("golden test passed")


if __name__ == "__main__":
    main()
