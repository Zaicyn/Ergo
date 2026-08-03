"""Follow-up to fss.py: runs the points the 28-min budget skipped, then
retries N=13 and N=14 at B=0.25, J=1.0 with looser tol (1e-9 is far below
the ~1e-4 precision the scaling analysis needs). Appends to
results_fss.json.
"""

import json
import time

import fss

OUT = "results_fss.json"
T0 = time.time()

results = json.load(open(OUT))

# Cheap skipped points (N <= 12): control and J=0.75/1.25 at N=8,10.
for N, B, J in [
    (8, 0.50, 0.5), (10, 0.50, 0.5), (12, 0.50, 0.5),
    (8, 0.25, 0.75), (10, 0.25, 0.75),
    (8, 0.25, 1.25), (10, 0.25, 1.25),
    (13, 0.25, 1.0),
]:
    fss.attempt(results, N, B, J)

# N=14 retry: k=2, ncv=24, tol=1e-9, generous limit.
try:
    pt, psi = fss.run_point(14, 0.25, 1.0, k=2, ncv=24, limit=2400, tol=1e-9)
    results["points"].append(pt)
    fss.save(results)
    print(f"[pt] N=14 B=0.25 J=1.00 tol=1e-9 E0={pt['E0']:.6f} "
          f"gap={pt['gap']:.6f} ({pt['seconds']:.0f}s)", flush=True)
except TimeoutError as e:
    results["points"].append({"N": 14, "B": 0.25, "J": 1.0,
                              "failed_tol1e9": True})
    fss.save(results)
    print(f"[timeout] N=14 tol=1e-9: {e}", flush=True)

print("followup done", flush=True)
