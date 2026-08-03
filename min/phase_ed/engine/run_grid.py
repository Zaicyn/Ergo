"""Grid sweep driver: run analysis over a model's native_grid (or a given
grid), append results to JSON.
"""

import json

from analysis import analyze


def run_grid(model, N, grid, out_path, tag=""):
    try:
        results = json.load(open(out_path))
    except (FileNotFoundError, json.JSONDecodeError):
        results = []
    done = {(r["N"], json.dumps(r["params"], sort_keys=True),
             r.get("model")) for r in results}
    for params in grid:
        key = (N, json.dumps({k: v for k, v in params.items()
                              if isinstance(v, (int, float))},
                             sort_keys=True), model.name)
        if key in done:
            continue
        rec = analyze(model, N, params)
        rec["model"] = model.name
        results.append(rec)
        json.dump(results, open(out_path, "w"), indent=1)
        print(f"[{tag or model.name}] N={N} {params}: E0={rec['E0']:.5f} "
              f"gap={rec['gap']:.5f} c={rec['c']:.3f} "
              f"eta={rec['fits']['alg'].get('eta'):.3f} "
              f"res={rec['residual']:.1e}", flush=True)
    return results
