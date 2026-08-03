"""BKT discriminator: N=16 at (B=0.25, J=1.5) and (B=0.25, J=2.0).
Same settings as n16_bridge.py (complex64, k=2 ncv=8, tol=1e-6, continuation).
Appends to n16_extended.json.
"""

import json
import time

import numpy as np

from matvec_fast import FastChain, eigsh_fc

OUT = "n16_extended.json"
N = 16
PLAN = [(0.25, 1.5), (0.25, 2.0)]


def main():
    results = {"params": {"N": N, "dtype": "complex64", "tol": 1e-6},
               "points": []}
    v0 = None
    for B, J in PLAN:
        fc = FastChain(N, B, J, cdtype=np.complex64)
        done = False
        for k, ncv in [(2, 8), (2, 12), (4, 10)]:
            t0 = time.time()
            try:
                evals, evecs = eigsh_fc(fc, k=k, tol=1e-6, ncv=ncv, v0=v0,
                                        maxiter=500)
            except Exception as e:
                print(f"[retry] J={J} k={k} ncv={ncv}: {type(e).__name__}: {e}",
                      flush=True)
                continue
            pt = {"N": N, "B": B, "J": J, "k": k, "ncv": ncv,
                  "E0": float(evals[0]),
                  "gap": float(evals[1] - evals[0]),
                  "seconds": time.time() - t0}
            results["points"].append(pt)
            with open(OUT, "w") as f:
                json.dump(results, f, indent=1)
            print(f"[pt] N=16 B={B} J={J} E0={pt['E0']:.6f} gap={pt['gap']:.6f} "
                  f"({pt['seconds']:.0f}s)", flush=True)
            v0 = evecs[:, 0]
            done = True
            break
        if not done:
            results["points"].append({"N": N, "B": B, "J": J, "failed": True})
            with open(OUT, "w") as f:
                json.dump(results, f, indent=1)
    print("done", flush=True)


if __name__ == "__main__":
    main()
