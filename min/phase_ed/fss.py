"""Finite-size scaling of the gap at the competition point (B=0.25) and
off-line control (B=0.50, J=0.5). Spin-1 rotors, drift off (0.2% effect).

Uses gap_map.RotorChain. Per-point wall-time guard implemented as a deadline
check inside the matvec (raises TimeoutError between ARPACK iterations);
on timeout the point is retried once with k=2, ncv raised. Global budget
governs how many low-priority points are attempted. Results appended to
results_fss.json after every point.
"""

import json
import time

import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh

from gap_map import RotorChain

OUT = "results_fss.json"
GLOBAL_BUDGET = 1680.0      # 28 min
POINT_LIMIT = 720.0         # 12 min per point

T0 = time.time()
CHAINS = {}
PSI = {}                    # (N, B, J) -> ground state, for v0 continuation


def timed_out():
    return time.time() - T0 > GLOBAL_BUDGET


def get_chain(N):
    if N not in CHAINS:
        CHAINS[N] = RotorChain(N, 1, drift=False)
    return CHAINS[N]


def run_point(N, B, J, v0=None, k=4, ncv=None, limit=POINT_LIMIT, tol=1e-12):
    ch = get_chain(N)
    deadline = time.time() + limit
    base_matvec = ch.make_matvec(B, J)
    state = {"n": 0}

    def matvec(v):
        state["n"] += 1
        if state["n"] % 20 == 0 and time.time() > deadline:
            raise TimeoutError(f"point limit {limit}s exceeded")
        return base_matvec(v)

    t0 = time.time()
    kw = dict(k=k, which="SA", tol=tol, maxiter=20000, v0=v0)
    if ncv is not None:
        kw["ncv"] = ncv
    A = LinearOperator((ch.DIM, ch.DIM), matvec=matvec, dtype=complex)
    evals, evecs = eigsh(A, **kw)
    order = np.argsort(evals)
    evals = evals[order]
    psi = evecs[:, order[0]]
    pt = {
        "N": N, "B": B, "J": J, "k": k, "ncv": ncv, "tol": tol,
        "E0": float(evals[0]),
        "gap": float(evals[1] - evals[0]),
        "seconds": time.time() - t0, "matvecs": state["n"],
    }
    return pt, psi


def attempt(results, N, B, J):
    key = (N, B, J)
    v0 = None
    # continuation: nearest already-converged J at the same (N, B)
    for (n2, b2, j2), psi in PSI.items():
        if n2 == N and b2 == B and abs(j2 - J) <= 0.25:
            v0 = psi
            break
    try:
        pt, psi = run_point(N, B, J, v0=v0)
    except TimeoutError as e:
        print(f"[timeout-k4] N={N} B={B} J={J}: {e}; retry k=2 ncv=24",
              flush=True)
        results["points"].append({"N": N, "B": B, "J": J, "failed_k4": True})
        save(results)
        try:
            pt, psi = run_point(N, B, J, v0=v0, k=2, ncv=24,
                                limit=POINT_LIMIT)
        except TimeoutError as e2:
            print(f"[timeout-k2] N={N} B={B} J={J}: {e2}; skipping", flush=True)
            results["points"].append({"N": N, "B": B, "J": J,
                                      "failed_k2": True})
            save(results)
            return
    PSI[key] = psi
    results["points"].append(pt)
    save(results)
    print(f"[pt] N={N} B={B:.2f} J={J:.2f} k={pt['k']} E0={pt['E0']:.6f} "
          f"gap={pt['gap']:.6f} ({pt['seconds']:.0f}s, "
          f"{time.time()-T0:.0f}s elapsed)", flush=True)


def save(results):
    with open(OUT, "w") as f:
        json.dump(results, f, indent=1)


def main():
    results = {"params": {"drift": False, "tol": 1e-12,
                          "global_budget_s": GLOBAL_BUDGET,
                          "point_limit_s": POINT_LIMIT},
               "points": []}
    # priority: complete J=1.0 scaling first (N=8,10,12,14), then control
    # (N<=12 cheap), then J=0.75/1.25 (N<=12), then N=13, then N=14 extras.
    plan = [(N, 0.25, 1.0) for N in (8, 10, 12, 14)]
    plan += [(N, 0.50, 0.5) for N in (8, 10, 12)]      # control
    for J in (0.75, 1.25):
        plan += [(N, 0.25, J) for N in (8, 10, 12)]
    plan += [(13, 0.25, 1.0), (14, 0.50, 0.5),
             (14, 0.25, 0.75), (14, 0.25, 1.25)]

    for N, B, J in plan:
        if timed_out():
            print(f"[budget] skipping remaining; elapsed "
                  f"{time.time()-T0:.0f}s", flush=True)
            break
        attempt(results, N, B, J)
    print("done", flush=True)


if __name__ == "__main__":
    main()
