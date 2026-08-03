"""Worker for bulk_map.py: one strip (one B, all J) -> JSON rows file.

Usage: python bulk_worker.py B "J0 J1 ..." mode outfile
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from analysis import entropy_cc, correlator, ground_state
from models.rotor import RotorModel

N = 12


def main():
    B = float(sys.argv[1])
    Js = [float(x) for x in sys.argv[2].split()]
    mode = sys.argv[3]
    outfile = sys.argv[4]
    model = RotorModel()
    rows = []
    for J in Js:
        t0 = time.time()
        if J == 0.0 and abs(B - 0.25) < 1e-12:
            rows.append({"B": B, "J": J, "E0": 0.0, "gap": 0.5,
                         "note": "analytic guard"})
            continue
        gs = ground_state(model, N, {"B": B, "J": J}, tol=1e-8, ncv=16)
        ent = entropy_cc(gs["psi"], N, model.d_site)
        rec = {"B": B, "J": J, "E0": gs["E0"], "gap": gs["gap"],
               "residual": gs["residual"],
               "c": ent["c"], "c_err": ent["c_err"], "cc_rms": ent["rms"],
               "seconds": time.time() - t0}
        idx = Js.index(J)
        if mode == "full" or idx % 4 == 0:
            cor = correlator(model, gs["psi"], N)
            rec["eta"] = cor["fits"]["alg"].get("eta")
            rec["osc_q"] = cor["fits"].get("osc", {}).get("q")
            rec["sign_changes"] = cor["fits"]["sign_changes"]
        rows.append(rec)
    json.dump(rows, open(outfile, "w"), indent=1)


if __name__ == "__main__":
    main()
