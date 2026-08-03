"""Bulk mapping driver v2: subprocess-per-strip parallelism.

Each strip (one B value, all J) runs as an independent OS process
(`python bulk_worker.py B J0 J1 dJ mode outfile`), capped at MAXP
concurrent processes. Avoids multiprocessing-module traps on Python
3.14 (forkserver stdin crash + parent-hang; numba-fork deadlocks) and
gives each worker its own interpreter/numba state.

Usage:
  python bulk_map.py validate   # 441-pt grid vs results_bj_map.json
  python bulk_map.py region     # 806-pt map -> results_bulk.json
"""

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = "/home/zaiken/Ergo/.venv/bin/python"
N = 12
MAXP = 6
WORKER = os.path.join(HERE, "bulk_worker.py")


def run_strips(jobs, tag):
    """jobs: list of (B, mode). Each strip runs all J from the spec
    embedded in the worker. Returns rows."""
    t0 = time.time()
    running = []
    pending = list(jobs)
    rows = []
    env = dict(os.environ, NUMBA_NUM_THREADS="2")
    while pending or running:
        while pending and len(running) < MAXP:
            B, mode, Js = pending.pop(0)
            out = os.path.join(HERE, f"_strip_{tag}_{B}.json")
            cmd = [PY, WORKER, str(B), " ".join(map(str, Js)), mode, out]
            running.append((subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                env=env), B, out, time.time()))
        time.sleep(2)
        still = []
        for proc, B, out, tstart in running:
            if proc.poll() is not None:
                if os.path.exists(out):
                    rows.extend(json.load(open(out)))
                    os.unlink(out)
                print(f"  strip B={B} done ({time.time()-tstart:.0f}s, "
                      f"{time.time()-t0:.0f}s total)", flush=True)
            else:
                still.append((proc, B, out, tstart))
        running = still
    return rows, time.time() - t0


BS21 = [round(0.025 * i, 3) for i in range(21)]
JS21 = [round(0.1 * i, 2) for i in range(21)]


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if which == "validate":
        rows, dt = run_strips([(B, "full", JS21) for B in BS21], "v")
        ref = {(r["B"], r["J"]): r
               for r in json.load(open(os.path.join(HERE, "results_bj_map.json")))}
        worst_e = worst_g = worst_c = 0.0
        n = 0
        for r in rows:
            if "note" in r:
                continue
            q = ref[(r["B"], r["J"])]
            n += 1
            worst_e = max(worst_e, abs(r["E0"] - q["E0"]))
            worst_g = max(worst_g, abs(r["gap"] - q["gap"]))
            worst_c = max(worst_c, abs(r["c"] - q["c"]))
        print(f"validate: {n}/441 matched | wall {dt:.0f}s (baseline 3015s) | "
              f"worst dE0={worst_e:.2e} dgap={worst_g:.2e} dc={worst_c:.2e}",
              flush=True)
    else:
        BS = [round(0.02 * i, 2) for i in range(26)]
        JS = [round(0.1 * i, 2) for i in range(31)]
        rows, dt = run_strips([(B, "light", JS) for B in BS], "r")
        json.dump({"seconds": dt, "points": rows},
                  open(os.path.join(HERE, "results_bulk.json"), "w"), indent=1)
        print(f"region: {len(rows)} pts in {dt:.0f}s -> results_bulk.json",
              flush=True)


if __name__ == "__main__":
    main()
