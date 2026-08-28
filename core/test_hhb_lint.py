"""Unit tests for the Hopf Handshake Bound static linter."""

import sys
import os

# Allow running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.lexer import Lexer
from core.parser import Parser
from core.checker import Checker
from core.hhb_lint import HHBLinter, HHBViolation


def _lint(source: str, certified: bool = False) -> list[HHBViolation]:
    tokens = Lexer(source).tokenize()
    tree = Parser(tokens).parse()
    errors = Checker().check(tree)
    if errors:
        raise AssertionError(f"Type check failed: {errors}")
    return HHBLinter(certified=certified).lint(tree)


def test_clean_handshake():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
REAL :: X
VERIFY HANDSHAKE clean DEPTH=1 FRAME_BYTES=256 MAXIT=10 CONSERVE NORM VALUE=0.0 TOL=1.0E-10
DO I = 1, N
  X := X + 1.0
  WRITE(*, "('x %.2e')") X
ENDDO
STOP
"""
    v = _lint(src)
    assert not v, f"Expected no violations, got {v}"


def test_missing_maxit():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
VERIFY HANDSHAKE bad DEPTH=1 FRAME_BYTES=256
DO I = 1, N
ENDDO
STOP
"""
    v = _lint(src)
    kinds = {x.kind for x in v}
    assert "hhb_maxit" in kinds


def test_do_while_rejected():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
REAL :: X
VERIFY HANDSHAKE bad DEPTH=1 FRAME_BYTES=256 MAXIT=10
DO I = 1, N
  DO WHILE (X < 1.0)
    X := X + 0.1
  ENDDO
ENDDO
STOP
"""
    v = _lint(src)
    kinds = {x.kind for x in v}
    assert "hhb_uncounted" in kinds


def test_allocate_rejected():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
REAL, ALLOCATABLE :: A(:)
VERIFY HANDSHAKE bad DEPTH=1 FRAME_BYTES=256 MAXIT=10
DO I = 1, N
  ALLOCATE(A(N))
ENDDO
STOP
"""
    v = _lint(src)
    kinds = {x.kind for x in v}
    assert "hhb_allocate" in kinds


def test_subroutine_call_rejected():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
REAL, ALLOCATABLE :: A(:)
VERIFY HANDSHAKE bad DEPTH=1 FRAME_BYTES=256 MAXIT=10
DO I = 1, N
  CALL FOO
ENDDO
STOP
SUBROUTINE FOO
  REAL, ALLOCATABLE :: B(:)
  ALLOCATE(B(10))
END
"""
    v = _lint(src)
    kinds = {x.kind for x in v}
    assert "hhb_call" in kinds


def test_oracle_missing_warning():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
VERIFY HANDSHAKE bad DEPTH=1 FRAME_BYTES=256 MAXIT=10
DO I = 1, N
ENDDO
STOP
"""
    v = _lint(src, certified=False)
    kinds = {x.kind for x in v}
    assert "hhb_oracle" in kinds
    # In prototype mode this is a warning, not a hard error
    assert not any(x.certified for x in v)


def test_depth_exceeded():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I, J
INTEGER :: STAGE
VERIFY HANDSHAKE bad DEPTH=1 FRAME_BYTES=256 MAXIT=10
IF (STAGE == 1) THEN
  DO I = 1, N
  ENDDO
ELSE
  DO J = 1, N
  ENDDO
ENDIF
STOP
"""
    v = _lint(src)
    kinds = {x.kind for x in v}
    assert "hhb_depth" in kinds


def test_maxit_must_be_static():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: LIMIT
INTEGER :: I
VERIFY HANDSHAKE bad DEPTH=1 FRAME_BYTES=256 MAXIT=LIMIT
DO I = 1, N
ENDDO
STOP
"""
    v = _lint(src)
    kinds = {x.kind for x in v}
    assert "hhb_maxit" in kinds


def test_maxit_parameter_ok():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER, PARAMETER :: LIM = 10
INTEGER :: I
VERIFY HANDSHAKE ok DEPTH=1 FRAME_BYTES=256 MAXIT=LIM
DO I = 1, N
ENDDO
STOP
"""
    v = _lint(src)
    kinds = {v.kind for v in v}
    assert "hhb_maxit" not in kinds


def test_payload_budget():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
REAL :: A, B, C, D, E, F, G, H
VERIFY HANDSHAKE bad DEPTH=1 FRAME_BYTES=16 MAXIT=10 PAYLOAD=(A,B,C,D,E,F,G,H)
DO I = 1, N
ENDDO
STOP
"""
    v = _lint(src)
    kinds = {x.kind for x in v}
    assert "hhb_payload" in kinds


def test_payload_array_static_size():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
REAL :: ARR(N)
VERIFY HANDSHAKE ok DEPTH=1 FRAME_BYTES=256 MAXIT=10 PAYLOAD=(ARR)
DO I = 1, N
ENDDO
STOP
"""
    v = _lint(src)
    kinds = {x.kind for x in v}
    assert "hhb_payload" not in kinds


def test_conserve_requires_tol():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
VERIFY HANDSHAKE bad DEPTH=1 FRAME_BYTES=256 MAXIT=10 CONSERVE NORM
DO I = 1, N
ENDDO
STOP
"""
    v = _lint(src)
    kinds = {x.kind for x in v}
    assert "hhb_conserve" in kinds


def test_oracle_options_ok():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
REAL :: X
VERIFY HANDSHAKE ok DEPTH=1 FRAME_BYTES=256 MAXIT=10 CONSERVE NORM TOL=1.0E-6 ORACLE foo VALUE=X LIMIT=1.0E-6
DO I = 1, N
ENDDO
STOP
"""
    v = _lint(src)
    kinds = {x.kind for x in v}
    assert "hhb_oracle" not in kinds


def test_oracle_missing_limit():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
REAL :: X
VERIFY HANDSHAKE bad DEPTH=1 FRAME_BYTES=256 MAXIT=10 ORACLE foo VALUE=X
DO I = 1, N
ENDDO
STOP
"""
    v = _lint(src)
    kinds = {x.kind for x in v}
    assert "hhb_oracle" in kinds


def test_handshake_block_syntax():
    src = """
IMPLICIT NONE
INTEGER, PARAMETER :: N = 8
INTEGER :: I
REAL :: X
HANDSHAKE block
    DEPTH=1
    FRAME_BYTES=256
    MAXIT=10
    CONSERVE NORM VALUE=0.0 TOL=1.0E-10
    PAYLOAD=(X)
    ORACLE final VALUE=X LIMIT=1.0E-6
  DO I = 1, N
    X := X + 1.0
  ENDDO
ENDHANDSHAKE
STOP
"""
    v = _lint(src)
    assert not v, f"Expected no violations, got {v}"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            print(f"running {name} ...", end=" ")
            fn()
            print("ok")
    print("all tests passed")
