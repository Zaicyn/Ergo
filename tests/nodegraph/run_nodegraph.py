#!/usr/bin/env python3
"""run_nodegraph.py — node-graph golden tests (Phase A of
Spec/Ergo_NodeGraph_Design.md: data model → validation → Ergo source
→ binary → verified output).

  1. nernst.json end-to-end: CLI route (python -m core <graph.json>)
     compiles; binary output matches the analytic Nernst potential.
  2. signal_condition.json end-to-end: constants, comparison, Switch
     (IF/ELSE lowering), fan-out — output matches the hand value.
  3. validation negatives: cycle, type mismatch, fan-in, unconnected
     pin, unknown op, undeclared parameter — each reported.
  4. determinism: compile() twice byte-identical; to_json round-trip
     text-stable; --emit-ergo matches the library's compile().

Run from repo root:  python3 tests/nodegraph/run_nodegraph.py
"""

import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from core.nodegraph import Graph, Node, Edge, PinType

ROWS = []


def report(test, status, note=""):
    ROWS.append((test, status, note))


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, timeout=180,
                          cwd=REPO)


def compile_graph(graph_path, out):
    r = sh(["python", "-m", "core", graph_path, "-o", out])
    return r.returncode == 0, r


def run_value(binary):
    r = sh([binary])
    if r.returncode != 0:
        return None
    return float(r.stdout.decode().strip())


def main():
    # ── 1/2: end-to-end graphs ──
    cases = [
        ("nernst", os.path.join(HERE, "nernst.json"),
         61.5 * math.log10(100.0 / 5.0)),
        ("signal_condition",
         os.path.join(HERE, "signal_condition.json"), 15.0),
    ]
    for name, path, expect in cases:
        binary = f"/tmp/ng_{name}"
        ok, r = compile_graph(path, binary)
        if not ok:
            report(name, "FAIL", "compile: "
                   + r.stderr.decode(errors="replace")
                   .strip().splitlines()[-1][:70])
            continue
        got = run_value(binary)
        if got is None:
            report(name, "FAIL", "binary failed")
        elif abs(got - expect) > 1e-5:
            report(name, "FAIL", f"got {got}, want {expect}")
        else:
            report(name, "PASS", f"output {got:.6f} == analytic "
                   f"{expect:.6f}")

    # ── 3: validation negatives ──
    negs = []

    g = Graph("cycle")
    g.add_op("a", "Add")
    g.add_op("b", "Add")
    g.add_edge("a", "out", "b", "a")
    g.add_edge("b", "out", "a", "a")
    g.add_edge("b", "out", "a", "b")
    g.add_edge("a", "out", "b", "b")
    negs.append(("cycle", g, "Cycle detected"))

    g = Graph("type_mismatch")
    g.add_op("n", "Not")
    g.add_op("m", "Mul")
    g.add_edge("n", "out", "m", "a")   # LOGICAL -> REAL pin
    negs.append(("type mismatch", g, "type mismatch"))

    g = Graph("fan_in")
    g.add_op("a", "Add")
    g.add_constant("c0", PinType.REAL, 1.0)
    g.add_constant("c1", PinType.REAL, 2.0)
    g.add_edge("c0", "out", "a", "a")
    g.add_edge("c1", "out", "a", "a")  # second driver of pin a
    negs.append(("fan-in", g, "fan-in not allowed"))

    g = Graph("unconnected")
    g.add_op("a", "Add")
    g.add_constant("c0", PinType.REAL, 1.0)
    g.add_edge("c0", "out", "a", "a")  # pin b left unconnected
    negs.append(("unconnected pin", g, "unconnected input"))

    g = Graph("unknown_op")
    g.add_node(Node(id="x", op="Frobnicate"))
    negs.append(("unknown op", g, "unknown operation"))

    g = Graph("bad_param")
    g.add_op("m", "Mul")
    g.add_constant("c0", PinType.REAL, 1.0)
    g.add_edge("c0", "out", "m", "a")
    g.edges.append(Edge("param", "MISSING", "m", "b"))
    negs.append(("undeclared param", g, "not declared"))

    for name, g, expect in negs:
        errs = g.validate()
        if any(expect in e for e in errs):
            report(f"validate: {name}", "PASS", "")
        else:
            report(f"validate: {name}", "FAIL",
                   f"expected {expect!r} in {errs[:1]}")

    # ── 4: determinism + serialization ──
    g1 = Graph.from_json(open(os.path.join(HERE, "nernst.json")).read())
    if g1.compile() == g1.compile():
        report("compile deterministic", "PASS", "")
    else:
        report("compile deterministic", "FAIL", "two compiles differ")
    j1 = g1.to_json()
    j2 = Graph.from_json(j1).to_json()
    if j1 == j2:
        report("json round-trip", "PASS", "")
    else:
        report("json round-trip", "FAIL", "re-emission differs")
    r = sh(["python", "-m", "core",
            os.path.join(HERE, "nernst.json"), "--emit-ergo"])
    if r.returncode == 0 and \
            r.stdout.decode() == g1.compile():
        report("emit-ergo route", "PASS", "")
    else:
        report("emit-ergo route", "FAIL",
               r.stderr.decode(errors="replace")[:70])

    print("=" * 68)
    print("NODEGRAPH SUITE — graph → validate → Ergo → binary → oracle")
    print("=" * 68)
    for test, status, note in ROWS:
        print(f"  {status:5s} {test:26s} {note}")
    n_fail = sum(1 for r in ROWS if r[1] == "FAIL")
    print("-" * 68)
    print(f"  {len(ROWS) - n_fail} ok, {n_fail} FAIL (of {len(ROWS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
