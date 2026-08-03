#!/usr/bin/env python3
"""analyze_rotor_traj.py — exponent tables from the blocked trajectory sweep.

Input: rotor_traj.out, one line per (point, block):
  PT <pt> mode <m> NQ <n> J <j> gphi <g> BLK <b> I <i> coh <c> nph <n>

Blocks are consecutive windows of one long trajectory; the across-block
scatter gives a standard error on each point (blocks are ~120 time units,
comparable to the slowest mixing time ~1/G^2, so the SEM is a lower bound).
Offline aggregation only — all physics was computed in Ergo.
"""
import numpy as np

blocks = {}
for line in open("/home/zaiken/Ergo/min/qbattery/rotor_traj.out"):
    if not line.startswith("PT "):
        continue
    p = line.split()
    key = (int(p[3]), int(p[5]), float(p[7]), float(p[9]))  # mode, nq, j, gp
    blocks.setdefault(key, []).append((float(p[13]), float(p[15]), float(p[17])))

pts = []
for (mode, nq, j, gp), bl in sorted(blocks.items()):
    a = np.array(bl)
    m = a.mean(axis=0)
    s = a.std(axis=0, ddof=1) / np.sqrt(len(a)) if len(a) > 1 else np.full(3, np.nan)
    pts.append({"mode": mode, "nq": nq, "j": j, "gp": gp, "nb": len(a),
                "i": m[0], "i_err": s[0], "coh": m[1], "coh_err": s[1],
                "nph": m[2], "nph_err": s[2]})

def exp_fit(sub):
    ns = np.array([p["nq"] for p in sub], float)
    ys = np.array([p["i"] for p in sub])
    es = np.array([p["i_err"] for p in sub])
    w = ys / np.maximum(es, 1e-9)  # log-space sigma = i_err / i
    slope = np.polyfit(np.log(ns), np.log(ys), 1, w=w)[0]
    # slope std from weighted least squares (covariance via design matrix)
    X = np.vstack([np.log(ns), np.ones_like(ns)]).T
    W = np.diag(w**2)
    cov = np.linalg.inv(X.T @ W @ X)
    return slope, np.sqrt(cov[0, 0])

print("=== points (mean +/- SEM over blocks) ===")
for p in pts:
    label = "rotor  " if p["mode"] == 1 else "emitter"
    print(f"  {label} N={p['nq']} J={p['j']:.2f} gphi={p['gp']:.1f}: "
          f"I={p['i']:.5f}+-{p['i_err']:.5f} ({100*p['i_err']/max(p['i'],1e-12):.0f}%) "
          f"coh={p['coh']:.5f} nph={p['nph']:.4f}")

print("\n=== exponent table (I vs N, weighted log-log fit) ===")
for (mode, j, gp) in sorted(set((p["mode"], p["j"], p["gp"]) for p in pts)):
    sub = sorted([p for p in pts if p["mode"] == mode and p["j"] == j and p["gp"] == gp],
                 key=lambda p: p["nq"])
    if len(sub) < 3:
        continue
    e, de = exp_fit(sub)
    label = "rotor  " if mode == 1 else "emitter"
    print(f"  {label} J={j:.2f} gphi={gp:.1f}: exp(I) = {e:.2f} +/- {de:.2f}   "
          + " ".join(f"N{p['nq']}:{p['i']:.4f}" for p in sub))

print("\n=== coherence-exponent correlation (rotor, gphi=0) ===")
sub = [p for p in pts if p["mode"] == 1 and p["gp"] == 0.0]
li = np.log([p["i"] for p in sub])
lc = np.log([max(p["coh"], 1e-12) for p in sub])
r = np.corrcoef(li, lc)[0, 1]
print(f"  corr(log I, log coh) over {len(sub)} (NQ,J) points: r = {r:.3f}")
for j in (0.0, 0.25, 0.5):
    sj = sorted([p for p in sub if p["j"] == j], key=lambda p: p["nq"])
    print(f"  J={j:.2f}: " + " ".join(f"N{p['nq']} coh={p['coh']:.4f}" for p in sj))

print("\n=== dephasing scan (rotor, J=0.25) ===")
for gp in (0.0, 0.1, 1.0):
    sub2 = sorted([p for p in pts if p["mode"] == 1 and p["j"] == 0.25 and p["gp"] == gp],
                  key=lambda p: p["nq"])
    if len(sub2) >= 3:
        e, de = exp_fit(sub2)
        print(f"  gphi={gp}: exp(I)={e:.2f}+/-{de:.2f}  I: " +
              " ".join(f"N{p['nq']}:{p['i']:.4f}" for p in sub2))
for nq in (2, 3, 4, 5, 6):
    row = {gp: p for gp in (0.0, 0.1, 1.0)
           for p in pts if p["mode"] == 1 and p["j"] == 0.25 and p["gp"] == gp and p["nq"] == nq}
    if len(row) == 3:
        print(f"  N={nq}: I(gp=1)/I(gp=0) = {row[1.0]['i']/max(row[0.0]['i'],1e-12):.1f}x, "
              f"I(gp=0.1)/I(gp=0) = {row[0.1]['i']/max(row[0.0]['i'],1e-12):.2f}x")
