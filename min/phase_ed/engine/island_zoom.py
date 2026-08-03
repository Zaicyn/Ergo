"""Island zoom: fine grid over the low-c pocket at (B~0.1, J~2.0),
plus N-scaling at the pocket center and two flank points.

Part 1: B in [0.0, 0.2] step 0.02 (11) x J in [1.5, 2.5] step 0.1 (11),
N=12. Per point: E0, gap, c, eta, q, and per-site forbidden-window
occupation w_i and order parameter r_i (mean + per-site for record).
Part 2: N in {8, 10, 12, 14} at (0.1, 2.0) center, (0.1, 1.6) flank,
(0.2, 2.0) outside: gap and c.

Results -> results_island.json (incremental).
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
from rotor_single import forbidden_projector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results_island.json")


def per_site_observables(model, psi_flat, N):
    """w_i (forbidden-window projector per site) and r_i per site.
    Works on the gauge-untwisted vector (unit-diagonal gauge, entropy
    invariant; projectors need the intended frame)."""
    psi = np.exp(-1j * model.gauge_phases(N)) * psi_flat
    t = psi.reshape((3,) * N)
    refs = 2.0 * np.pi * np.arange(N) / N
    w_i, r_i = [], []
    Tp = np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=complex)
    Tm = Tp.T.copy()
    for i in range(N):
        tm = np.moveaxis(t, i, 0)
        P = forbidden_projector(1, refs[i])
        w_i.append(float(np.real(np.vdot(tm.ravel(),
                       np.tensordot(P, tm, axes=([1], [0])).ravel()))))
        eiph = np.exp(-1j * refs[i]) * Tm
        r_i.append(float(abs(np.vdot(tm.ravel(),
                        np.tensordot(eiph, tm, axes=([1], [0])).ravel()))))
    return w_i, r_i


def analyze_point(model, N, B, J, with_sites=False, tol=1e-8):
    gs = ground_state(model, N, {"B": B, "J": J}, tol=tol, ncv=16)
    ent = entropy_cc(gs["psi"], N, model.d_site)
    cor = correlator(model, gs["psi"], N)
    rec = {"N": N, "B": B, "J": J, "E0": gs["E0"], "gap": gs["gap"],
           "residual": gs["residual"],
           "c": ent["c"], "c_err": ent["c_err"], "cc_rms": ent["rms"],
           "S": {str(k): v for k, v in ent["S"].items()},
           "eta": cor["fits"]["alg"].get("eta"),
           "osc_q": cor["fits"].get("osc", {}).get("q"),
           "sign_changes": cor["fits"]["sign_changes"],
           "monotone": cor["fits"]["monotone"]}
    if with_sites:
        w_i, r_i = per_site_observables(model, gs["psi"], N)
        rec["w_i"] = w_i
        rec["r_i"] = r_i
        rec["w"] = float(np.mean(w_i))
        rec["r"] = float(np.mean(r_i))
    return rec


def main():
    model = RotorModel()
    t0 = time.time()
    results = {"grid": [], "scaling": []}
    if os.path.exists(OUT):
        results = json.load(open(OUT))

    done = {(r["B"], r["J"]) for r in results["grid"]}
    BS = [round(0.02 * i, 2) for i in range(11)]
    JS = [round(1.5 + 0.1 * i, 2) for i in range(11)]
    for B in BS:
        for J in JS:
            if (B, J) in done:
                continue
            rec = analyze_point(model, 12, B, J, with_sites=True)
            results["grid"].append(rec)
            if len(results["grid"]) % 11 == 0:
                json.dump(results, open(OUT, "w"), indent=1)
                print(f"grid {len(results['grid'])}/121 "
                      f"({time.time()-t0:.0f}s)", flush=True)

    done_s = {(r["N"], r["B"], r["J"]) for r in results["scaling"]}
    for B, J in [(0.1, 2.0), (0.1, 1.6), (0.2, 2.0)]:
        for N in (8, 10, 12, 14):
            if (N, B, J) in done_s:
                continue
            rec = analyze_point(model, N, B, J, with_sites=False,
                                tol=1e-8 if N < 14 else 1e-7)
            results["scaling"].append(rec)
            json.dump(results, open(OUT, "w"), indent=1)
            print(f"scaling N={N} B={B} J={J} ({time.time()-t0:.0f}s)",
                  flush=True)

    json.dump(results, open(OUT, "w"), indent=1)
    print(f"done in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
