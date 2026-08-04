#!/usr/bin/env python3
"""analyze_cycloid.py — oracle driver for the hopfion brachistochrone test.

For each case (flat grids as method oracle; Hopf-projected 600-cell and
120-cell base point sets as the refinement pair):

  1. regenerate min/hopfion/hopfion_relax_<tag>.ergo via gen_relax.py
  2. compile with `python -m core` and run TWICE (determinism: byte-identical)
  3. parse the relaxed PATH + cost
  4. fit the analytic cycloid through A (cusp, depth 0) and B:
       x = xA + a (t - sin t),   depth = a (1 - cos t),   t in [0, tB]
     with (xB-xA)/(dB) = (tB - sin tB)/(1 - cos tB) solved by bisection
     (f is monotone increasing on (0, 2pi], f->0 at 0, f(2pi)=pi)
  5. report node-to-curve distances (mean/max, normalized by |A-B|),
     and discrete cost vs analytic cost sqrt(2a)*tB
  6. write min/hopfion/cycloid_report.json + cycloid_<tag>.png

Oracle logic: the flat grids at two spacings must show the method
converging toward the cycloid (error shrinking with h). Only then are the
600-cell (coarse, 30 base points) vs 120-cell (fine, 150 base points)
numbers meaningful as a refinement comparison.
"""
import json
import subprocess
import sys

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "min/hopfion"
CASES = [
    ("grid30", "grid:30"),
    ("grid60", "grid:60"),
    ("grid120", "grid:120"),
    ("c600", f"{ROOT}/base_600.txt"),
    ("c120", f"{ROOT}/base_120.txt"),
]


def run_case(tag, spec):
    subprocess.run([sys.executable, f"{ROOT}/gen_relax.py", spec, tag],
                   check=True, capture_output=True)
    ergo = f"{ROOT}/hopfion_relax_{tag}.ergo"
    binp = f"/tmp/hr_{tag}"
    subprocess.run([sys.executable, "-m", "core", ergo, "-o", binp],
                   check=True, capture_output=True)
    out1 = subprocess.run([binp], check=True, capture_output=True, text=True)
    out2 = subprocess.run([binp], check=True, capture_output=True, text=True)
    deterministic = out1.stdout == out2.stdout
    pts, cost, icost, conv = [], None, None, None
    for line in out1.stdout.splitlines():
        if line.startswith("PATH"):
            pts.append([float(line.split()[2]), float(line.split()[3])])
        elif line.startswith("init cost"):
            icost = float(line.split()[2])
        elif line.startswith("cost"):
            cost = float(line.split()[1])
        elif line.startswith("converged"):
            conv = int(line.split()[-1])
    return np.array(pts), cost, icost, conv, deterministic


def fit_cycloid(A, B):
    """Cusp at A (depth 0), through B. Returns a, tB, s (x-mirror sign).
    depth = 1 - y."""
    s = 1.0 if B[0] >= A[0] else -1.0
    dx = abs(B[0] - A[0])
    dd = (1.0 - B[1]) - (1.0 - A[1])   # = yA - yB
    r = dx / dd
    f = lambda t: (t - np.sin(t)) / (1.0 - np.cos(t))
    lo, hi = 1e-12, 2 * np.pi
    if r >= f(hi):
        tB = hi                      # degenerate: full arch
    else:
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if f(mid) < r:
                lo = mid
            else:
                hi = mid
        tB = 0.5 * (lo + hi)
    a = dd / (1.0 - np.cos(tB))
    return a, tB, s


def curve_points(A, a, tB, s, n=4096):
    t = np.linspace(0.0, tB, n)
    x = A[0] + s * a * (t - np.sin(t))
    y = 1.0 - a * (1.0 - np.cos(t))
    return np.column_stack([x, y])


def dist_to_curve(P, C):
    """Min distance from each row of P to the dense polyline C (segment-
    exact, not just vertex distance)."""
    seg = C[1:] - C[:-1]
    L2 = np.sum(seg ** 2, axis=1)
    out = np.empty(len(P))
    for i, p in enumerate(P):
        w = p - C[:-1]
        t = np.clip(np.sum(w * seg, axis=1) / L2, 0.0, 1.0)
        d = np.min(np.linalg.norm(C[:-1] + t[:, None] * seg - p, axis=1))
        out[i] = d
    return out


def main():
    report = {}
    for tag, spec in CASES:
        P, cost, icost, conv, det = run_case(tag, spec)
        A, B = P[0], P[-1]
        a, tB, s = fit_cycloid(A, B)
        C = curve_points(A, a, tB, s)
        d = dist_to_curve(P, C)                    # path nodes -> curve
        Cs = curve_points(A, a, tB, s, n=256)
        d2 = dist_to_curve(Cs, P)                  # curve samples -> path
        norm = np.linalg.norm(B - A)
        cost_an = np.sqrt(2.0 * a) * tB
        sym_mean = 0.5 * (d.mean() + d2.mean())
        sym_max = max(d.max(), d2.max())
        rep = {
            "nodes": len(P),
            "A": A.tolist(), "B": B.tolist(),
            "a": a, "tB": tB,
            "cost_discrete": cost,
            "cost_dijkstra_init": icost,
            "relax_delta": (icost - cost) if icost is not None else None,
            "cost_analytic": cost_an,
            "cost_rel_err": abs(cost - cost_an) / cost_an,
            "err_mean": float(sym_mean), "err_max": float(sym_max),
            "err_p2c_mean": float(d.mean()), "err_p2c_max": float(d.max()),
            "err_c2p_mean": float(d2.mean()), "err_c2p_max": float(d2.max()),
            "err_mean_rel": float(sym_mean / norm),
            "err_max_rel": float(sym_max / norm),
            "converged_sweep": conv, "deterministic": det,
        }
        report[tag] = rep
        print(f"[{tag}] nodes={len(P)} conv_sweep={conv} det={det}")
        print(f"  cost: dijkstra={icost:.6f} relaxed={cost:.6f} "
              f"(delta={icost - cost:.2e}) analytic={cost_an:.6f} "
              f"rel_err={rep['cost_rel_err']:.4%}")
        print(f"  curve dist (sym Chamfer, |AB|-rel): "
              f"mean={sym_mean:.5f} ({sym_mean/norm:.3%}) "
              f"max={sym_max:.5f} ({sym_max/norm:.3%})")
        print(f"    p2c mean={d.mean():.5f} max={d.max():.5f} | "
              f"c2p mean={d2.mean():.5f} max={d2.max():.5f}")

        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.plot(C[:, 0], C[:, 1], "k-", lw=1.5, label="analytic cycloid")
        ax.plot(P[:, 0], P[:, 1], "r.-", ms=5, lw=0.8, label="discrete geodesic")
        ax.invert_yaxis()
        ax.set_aspect("equal")
        ax.legend()
        ax.set_title(f"{tag}: err_mean={sym_mean:.4f} err_max={sym_max:.4f}")
        fig.tight_layout()
        fig.savefig(f"{ROOT}/cycloid_{tag}.png", dpi=130)
        plt.close(fig)

    gs = [report[t] for t in ("grid30", "grid60", "grid120")]
    hs = np.log(np.array([1 / 29.0, 1 / 59.0, 1 / 119.0]))
    em = np.log(np.array([g["err_mean"] for g in gs]))
    ec = np.log(np.array([g["cost_rel_err"] for g in gs]))
    rate_m = np.polyfit(hs, em, 1)[0]
    rate_c = np.polyfit(hs, ec, 1)[0]
    report["grid_rates"] = {"shape_err_rate": float(rate_m),
                            "cost_err_rate": float(rate_c)}
    with open(f"{ROOT}/cycloid_report.json", "w") as fh:
        json.dump(report, fh, indent=2)
    errs = ", ".join(f"{g['err_mean']:.5f}" for g in gs)
    print(f"\n[method oracle] grid30/60/120 mean-err: {errs}")
    print(f"  fitted rates vs h: shape-err O(h^{rate_m:.2f}), "
          f"cost-err O(h^{rate_c:.2f}) (positive = converging)")
    c6, c1 = report["c600"], report["c120"]
    print(f"[headline] 600-cell base (30 pts) vs 120-cell base (150 pts):")
    print(f"  mean-err {c6['err_mean']:.5f} -> {c1['err_mean']:.5f}  "
          f"ratio {c6['err_mean'] / c1['err_mean']:.2f}x")
    print(f"  max-err  {c6['err_max']:.5f} -> {c1['err_max']:.5f}  "
          f"ratio {c6['err_max'] / c1['err_max']:.2f}x")


if __name__ == "__main__":
    main()
