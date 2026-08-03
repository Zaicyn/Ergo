"""N=16 bridge run (Part 3): ED with the optimized numba matvec.

Priority order: (B=0.25, J=1.0) [key scaling point, 1/N predicts gap ~0.065],
then (B=0.5, J=0.5) control, then (B=0.25, J=0.75), (B=0.25, J=1.25).
eigsh k=4 -> k=2 fallback, tol=1e-9, ncv raised, wavefunction continuation
between points (same N). Memory: 3^16 = 43 046 721 states = 689 MB/vector
complex128, 344 MB complex64. Storage dtype chosen by the complex64
precision gate from matvec_fast_report.json (gap error < 1e-6 at N=12);
ncv kept small to fit RAM. Results appended to n16_results.json.
"""

import json
import time

import numpy as np

from matvec_fast import FastChain, eigsh_fc

OUT = "n16_results.json"
N = 16
PLAN = [(0.25, 1.0), (0.5, 0.5), (0.25, 0.75), (0.25, 1.25)]

try:
    rep = json.load(open("matvec_fast_report.json"))
    C64_OK = bool(rep.get("c64_pass", False))
except FileNotFoundError:
    C64_OK = False

CDTYPE = np.complex64 if C64_OK else np.complex128
TOL = 1e-9 if not C64_OK else 1e-6   # float32 eps ~ 1e-7; 1e-6 keeps ARPACK sane


def save(results):
    with open(OUT, "w") as f:
        json.dump(results, f, indent=1)


def run(B, J, v0, results):
    fc = FastChain(N, B, J, cdtype=CDTYPE)
    for k, ncv in [(2, 8), (2, 12), (4, 10)]:
        t0 = time.time()
        try:
            evals, evecs = eigsh_fc(fc, k=k, tol=TOL, ncv=ncv, v0=v0,
                                    maxiter=500)
        except Exception as e:
            print(f"[retry] B={B} J={J} k={k} ncv={ncv}: "
                  f"{type(e).__name__}: {e}", flush=True)
            continue
        gap = float(evals[1] - evals[0]) if len(evals) > 1 else None
        pt = {"N": N, "B": B, "J": J, "k": k, "ncv": ncv, "tol": TOL,
              "dtype": str(CDTYPE), "E0": float(evals[0]), "gap": gap,
              "seconds": time.time() - t0}
        results["points"].append(pt)
        save(results)
        print(f"[pt] N=16 B={B} J={J} E0={pt['E0']:.6f} gap={gap} "
              f"({pt['seconds']:.0f}s)", flush=True)
        return evecs[:, 0]
    results["points"].append({"N": N, "B": B, "J": J, "failed": True})
    save(results)
    return None


def main():
    results = {"params": {"N": N, "dtype": str(CDTYPE), "tol": TOL,
                          "c64_gate": C64_OK,
                          "note": "gauge-folded Hamiltonian; eigenvalues are "
                                  "gauge-invariant, eigenvectors are in the "
                                  "twisted gauge"},
               "points": []}
    save(results)
    v0 = None
    for B, J in PLAN:
        psi = run(B, J, v0, results)
        if psi is not None:
            v0 = psi  # continuation to the next point
    print("bridge done", flush=True)


if __name__ == "__main__":
    main()
