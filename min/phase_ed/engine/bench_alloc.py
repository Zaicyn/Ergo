"""Milestone A benchmarks: roll-decode matvec vs index-arena vs arena+Z-order.

Correctness gate: N=8 eigenvalues identical to the existing path (< 1e-10).
Throughput: matvecs/sec at N = 8, 12, 14 (3^N), best-of-reps.
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from matvec_fast import FastChain
from index_arena import ArenaMatvec, morton_sigma
from scipy.sparse.linalg import LinearOperator, eigsh


def bench(fn, dim, seconds=2.0):
    rng = np.random.default_rng(0)
    v = rng.standard_normal(dim) + 1j * rng.standard_normal(dim)
    fn(v)  # warm
    t0 = time.time()
    n = 0
    while time.time() - t0 < seconds:
        fn(v)
        n += 1
    return n / (time.time() - t0)


def main():
    out = {"correctness": {}, "throughput_mv_per_s": {}}
    B, J = 0.25, 1.0

    # --- correctness gate, N=8 ---
    fc = FastChain(8, B, J)
    ev_ref = np.sort(eigsh(LinearOperator((fc.DIM, fc.DIM), matvec=fc.matvec,
                                          dtype=complex),
                           k=4, which="SA", tol=1e-12)[0])
    for tag, sigma in (("arena", None), ("arena_z", morton_sigma(8))):
        am = ArenaMatvec(8, B, J, sigma=sigma)
        ev = np.sort(eigsh(LinearOperator((am.DIM, am.DIM), matvec=am.matvec,
                                          dtype=complex),
                           k=4, which="SA", tol=1e-12)[0])
        d = float(np.max(np.abs(ev - ev_ref)))
        out["correctness"][tag] = d
        print(f"[gate] {tag} N=8 max|dE| = {d:.2e}", flush=True)

    # --- throughput ---
    for N in (8, 12, 14):
        fc = FastChain(N, B, J)
        r_roll = bench(fc.matvec, fc.DIM)
        am = ArenaMatvec(N, B, J)
        r_arena = bench(am.matvec, am.DIM)
        amz = ArenaMatvec(N, B, J, sigma=morton_sigma(N))
        r_z = bench(amz.matvec, amz.DIM)
        arena_MB = am.arena.nbytes / 1e6
        out["throughput_mv_per_s"][N] = {
            "roll_decode": r_roll, "arena": r_arena, "arena_z": r_z,
            "arena_bytes": am.arena.nbytes}
        print(f"N={N}: roll {r_roll:.1f} | arena {r_arena:.1f} "
              f"(+{100*(r_arena/r_roll-1):.0f}%) | arena+Z {r_z:.1f} "
              f"({100*(r_z/r_roll-1):+.0f}%) | arena {arena_MB:.1f} MB",
              flush=True)

    import json
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "bench_alloc.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("done", flush=True)


if __name__ == "__main__":
    main()
