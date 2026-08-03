#!/usr/bin/env python3
"""analyze_qbattery.py — log-log scaling exponents for current and power,
per case (cavity/control), pump W, and kappa regime."""
import numpy as np

rows = []
for line in open("/home/zaiken/Ergo/min/qbattery/qbattery.out"):
    if line.startswith("#"):
        continue
    p = line.split()
    rows.append({"case": p[0], "n": float(p[1]), "w": float(p[2]), "k": float(p[3]),
                 "i": float(p[7]), "vth": float(p[8]), "p": float(p[9])})

def exponents(sub, key):
    x = np.log(np.array([r["n"] for r in sub]))
    y = np.log(np.array([r[key] for r in sub]))
    return np.polyfit(x, y, 1)[0]

print(f"{'case':>8} {'W':>6} {'kappa':>5} {'exp(I)':>7} {'exp(P)':>7} {'P-ratio exp':>11}")
for k in (0.1, 0.5, 2.0):
    for w in (0.001, 0.1, 1.0):
        cav = [r for r in rows if r["case"] == "cavity" and r["w"] == w and r["k"] == k]
        ctl = [r for r in rows if r["case"] == "control" and r["w"] == w and r["k"] == k]
        ei_c, ep_c = exponents(cav, "i"), exponents(cav, "p")
        ei_t, ep_t = exponents(ctl, "i"), exponents(ctl, "p")
        ratio = np.array([c["p"] / t["p"] for c, t in zip(cav, ctl)])
        er = np.polyfit(np.log(np.array([r["n"] for r in cav])), np.log(ratio), 1)[0]
        print(f"{'cavity':>8} {w:>6} {k:>5} {ei_c:>7.2f} {ep_c:>7.2f} {er:>11.2f}")
        print(f"{'control':>8} {w:>6} {k:>5} {ei_t:>7.2f} {ep_t:>7.2f}")
