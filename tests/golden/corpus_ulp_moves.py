#!/usr/bin/env python3
"""corpus_ulp_moves.py — quantify output moves for corpus programs whose
recorded baseline differs from a new run.

For each DIFF row, parse every float literal in the baseline
(tests/golden/corpus_baseline/<name>.out) and the new output
(/tmp/corpus_diff_<name>.out) and report the max |diff| in ulps of the
printed (decimal) value — i.e. how much the PRINTED text moved, plus
the bit-level ulp move computed from re-parsing the decimal (an
under-approximation of the true bit move when prints round).

Usage: python3 tests/golden/corpus_ulp_moves.py  (reads /tmp artifacts)
"""
import glob
import os
import re
import struct

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "corpus_baseline")

NUM = re.compile(rb"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")


def floats(blob):
    out = []
    for m in NUM.finditer(blob):
        try:
            out.append(float(m.group(0)))
        except ValueError:
            pass
    return out


def ulps(a, b):
    if a == b:
        return 0
    if a == 0 or b == 0 or (a < 0) != (b < 0):
        # different zero/sign: count crudely via magnitude ladder
        return float("inf")
    ia = struct.unpack("<q", struct.pack("<d", a))[0]
    ib = struct.unpack("<q", struct.pack("<d", b))[0]
    oa = ia ^ 0x8000000000000000 if ia < 0 else ia
    ob = ib ^ 0x8000000000000000 if ib < 0 else ib
    return abs(oa - ob)


def main():
    rows = []
    for newf in sorted(glob.glob("/tmp/corpus_diff_*.out")):
        name = os.path.basename(newf)[len("corpus_diff_"):-len(".out")]
        basef = os.path.join(BASE, name + ".out")
        if not os.path.exists(basef):
            rows.append((name, "no baseline file", None, "-"))
            continue
        blob_a = open(basef, "rb").read()
        blob_b = open(newf, "rb").read()
        # first differing line (chaos-amplification marker)
        la = blob_a.splitlines()
        lb = blob_b.splitlines()
        first_line = next((i + 1 for i, (x, y) in enumerate(zip(la, lb))
                           if x != y), min(len(la), len(lb)) + 1)
        a = floats(blob_a)
        b = floats(blob_b)
        if len(a) != len(b):
            rows.append((name, f"float count {len(a)} -> {len(b)}",
                         None, f"line {first_line}/{len(la)}"))
            continue
        worst = 0
        nmove = 0
        for x, y in zip(a, b):
            d = ulps(x, y)
            if d:
                nmove += 1
                if d is not float("inf") and d > worst:
                    worst = d
                elif d == float("inf"):
                    worst = float("inf")
        rows.append((name, f"{nmove}/{len(a)} floats moved", worst,
                     f"line {first_line}/{len(la)}"))
    print(f"{'program':46s} {'moved':>16s} {'max printed-ulp':>16s}  "
          f"first divergence")
    for name, note, worst, firstln in rows:
        w = "inf (sign/zero)" if worst == float("inf") else \
            (str(worst) if worst is not None else "-")
        print(f"{name:46s} {note:>16s} {w:>16s}  {firstln}")
    print(f"\n({len(rows)} moved programs)")


if __name__ == "__main__":
    main()
