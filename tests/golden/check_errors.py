#!/usr/bin/env python3
"""check_errors.py — R1 golden: teaching error messages.

Compiles bad snippets and asserts each produces its named teaching
message (the parser/checker is the only teacher a new user has — every
message names the construct, the likely cause, and the fix).
Deterministic: fixed case order, substring assertions, no timestamps.
Run from repo root:  python3 tests/golden/check_errors.py
Exits 0 when every case produces its expected message.
"""

import subprocess
import sys
import tempfile
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

CASES = [
    # (name, snippet, expected substring)
    ("single-line IF",
     "IMPLICIT NONE\nREAL :: X\nX := 1.0\nIF (X > 0.0) X := 2.0\nENDIF\n",
     "single-line IF is not supported"),
    ("END DO two words",
     "IMPLICIT NONE\nINTEGER :: I\nDO I = 1, 3\nEND DO\n",
     "ENDDO / ENDIF are one word"),
    ("bare top-level END",
     "IMPLICIT NONE\nWRITE(*,\"('hi')\")\nEND\n",
     "no PROGRAM/END wrapper"),
    ("= as assignment",
     "IMPLICIT NONE\nREAL :: X\nX = 5.0\n",
     "assignment is ':='"),
    ("array expression",
     "IMPLICIT NONE\nREAL :: A(4), B(4), C(4)\nA := B + C\n",
     "no array expressions"),
    ("missing ::",
     "IMPLICIT NONE\nREAL X\n",
     "declarations need '::'"),
    ("PRINT multiple args",
     "IMPLICIT NONE\nPRINT 1.0, 2.0\n",
     "PRINT takes ONE expression"),
    ("subroutine as function",
     "IMPLICIT NONE\nREAL :: Y\nY := MYSUB(1.0)\n"
     "SUBROUTINE MYSUB(X)\n   IMPLICIT NONE\n   REAL :: X\n   X := 2.0\nEND\n",
     "is a SUBROUTINE — it returns nothing"),
    ("STATIC as argument (warning, not error)",
     "IMPLICIT NONE\nSTATIC REAL :: G(4)\nCALL TAKES(G)\n"
     "SUBROUTINE TAKES(A)\n   IMPLICIT NONE\n   REAL :: A(4)\n"
     "   A(1) := 1.0\nEND\n",
     "STATIC array 'G' passed as an argument"),
    ("written scalar dummy given a literal (A6)",
     "IMPLICIT NONE\nCALL SET42(1.0)\n"
     "SUBROUTINE SET42(X)\n   IMPLICIT NONE\n   REAL :: X\n   X := 42.0\nEND\n",
     "scalar dummy that SET42 writes"),
    ("COMPLEX refused (A3)",
     "IMPLICIT NONE\nCOMPLEX :: Z\n",
     "COMPLEX is not supported"),
    ("WRITE bad conversion (A4)",
     "IMPLICIT NONE\nREAL :: X\nX := 1.0\nWRITE(*,\"('bad %q')\") X\n",
     "not supported"),
    ("WRITE arg-count mismatch (A4)",
     "IMPLICIT NONE\nREAL :: X\nX := 1.0\nWRITE(*,\"('%d %d')\") X\n",
     "must match exactly"),
]


def main():
    n_ok = 0
    n_bad = 0
    print("=" * 68)
    print("R1 TEACHING-MESSAGE GOLDENS")
    print("=" * 68)
    for name, snippet, expect in CASES:
        with tempfile.NamedTemporaryFile(
                "w", suffix=".ergo", delete=False) as f:
            f.write(snippet)
            path = f.name
        r = subprocess.run(
            ["python", "-m", "core", path, "-o", "/tmp/ce_bin"],
            cwd=REPO, capture_output=True, text=True, timeout=120)
        blob = r.stdout + r.stderr
        ok = expect in blob
        print(f"  {'OK  ' if ok else 'FAIL'} {name}")
        if not ok:
            n_bad += 1
            print(f"       expected: {expect!r}")
            print(f"       got: {blob.strip().splitlines()[-1][:100]!r}")
        else:
            n_ok += 1
        os.unlink(path)
    print("-" * 68)
    print(f"  {n_ok}/{len(CASES)} teaching messages verified")
    return 1 if n_bad else 0


if __name__ == "__main__":
    sys.exit(main())
