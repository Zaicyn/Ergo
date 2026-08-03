"""Full (B, J) characterization map: rotor chain N=12, 21x21 grid.

Per point: E0, gap (eigsh k=2, arena matvec), CC fit for c, correlator
-> eta (plain algebraic; q=0 established on the line) + oscillatory-fit
flag (PT signature watch off the line). Results -> results_bj_map.json,
incremental. The (B=0.25, J=0) kinetic-only point is computed
analytically (ARPACK diagonal pathology guard, see sweep1.py).
"""

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import entropy_cc, correlator, ground_state
from models.rotor import RotorModel

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results_bj_map.json")
N = 12
BS = [round(0.025 * i, 3) for i in range(21)]
JS = [round(0.1 * i, 2) for i in range(21)]


def main():
    model = RotorModel()
    t0 = time.time()
    try:
        results = json.load(open(OUT))
    except (FileNotFoundError, json.JSONDecodeError):
        results = []
    done = {(r["B"], r["J"]) for r in results}
    for B in BS:
        for J in JS:
            if (B, J) in done:
                continue
            p0 = time.time()
            if J == 0.0 and abs(B - 0.25) < 1e-12:
                rec = {"B": B, "J": J, "E0": 0.0, "gap": 0.5,
                       "note": "analytic (diagonal pathology guard)"}
            else:
                gs = ground_state(model, N, {"B": B, "J": J},
                                  tol=1e-8, ncv=16)
                ent = entropy_cc(gs["psi"], N, model.d_site)
                cor = correlator(model, gs["psi"], N)
                rec = {"B": B, "J": J, "E0": gs["E0"], "gap": gs["gap"],
                       "residual": gs["residual"],
                       "c": ent["c"], "c_err": ent["c_err"],
                       "cc_rms": ent["rms"],
                       "eta": cor["fits"]["alg"].get("eta"),
                       "alg_rms": cor["fits"]["alg"].get("rms"),
                       "osc": cor["fits"].get("osc", {}),
                       "sign_changes": cor["fits"]["sign_changes"],
                       "monotone": cor["fits"]["monotone"]}
            rec["seconds"] = time.time() - p0
            results.append(rec)
            if len(results) % 21 == 0:
                json.dump(results, open(OUT, "w"), indent=1)
                print(f"{len(results)}/441 ({time.time()-t0:.0f}s)",
                      flush=True)
    json.dump(results, open(OUT, "w"), indent=1)
    print(f"done {len(results)} pts in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
