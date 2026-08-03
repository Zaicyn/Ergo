"""FDTD analysis: fringe spacing on screen + standing-wave node spacing.

Reads min/fdtd/slit.out (cols: scene j intensity) and min/fdtd/sw.out
(cols: i |U|). Smooths profiles (gaussian), finds local maxima (fringes)
or minima (nodes), reports mean spacings vs oracles:
  slit: dy = lambda*260/64 cells (48.75 / 65 / 81.25 for lambda 12/16/20,
        oracle ratio 12:16:20)
  sw:   lambda/2 = 8 cells (tolerance 1)
"""

import numpy as np


def gaussian_smooth(y, sigma=2.0):
    k = int(np.ceil(4 * sigma))
    x = np.arange(-k, k + 1)
    g = np.exp(-0.5 * (x / sigma) ** 2)
    g /= g.sum()
    return np.convolve(y, g, mode="same")


def find_peaks(y, min_prom=0.05):
    y = y.copy()
    rng = y.max() - y.min()
    prom = rng * min_prom if rng > 0 else 1
    cand = [i for i in range(1, len(y) - 1) if y[i] >= y[i - 1] and y[i] >= y[i + 1]]
    peaks = []
    for i in cand:
        if not peaks or y[i] > prom * 0.5 or (i - peaks[-1]) > 3:
            peaks.append(i)
    return np.array(peaks)


def find_minima(y):
    return [i for i in range(1, len(y) - 1) if y[i] <= y[i - 1] and y[i] <= y[i + 1]]


print("=== DOUBLE SLIT ===")
rows = {}
for line in open("slit.out"):
    if line.startswith("#"):
        continue
    sc, j, v = line.split()
    rows.setdefault(int(sc), {})[int(j)] = float(v)

spacings = {}
for sc in sorted(rows):
    prof = np.array([rows[sc][j] for j in range(1, 513)])
    s = gaussian_smooth(prof, sigma=3.0)
    # restrict to central region (exclude sponge edges and low-signal tails)
    core = s[100:412]
    # suppress DC: subtract a broad baseline
    base = gaussian_smooth(core, sigma=25.0)
    osc = core - base
    peaks = find_peaks(osc)
    if len(peaks) > 1:
        sp = np.diff(peaks).mean()
    else:
        sp = float("nan")
    spacings[sc] = sp
    lam = {1: 12, 2: 16, 3: 20}[sc]
    oracle = lam * 260 / 64
    print(f"scene {sc} (lambda={lam}): {len(peaks)} fringes, mean spacing "
          f"{sp:.2f} cells (oracle {oracle:.2f}, delta {abs(sp-oracle)/oracle*100:.1f}%)")
    print(f"  peak positions (first 8): {peaks[:8].tolist()}")

vals = [spacings[s] for s in sorted(spacings)]
print("ratios:", " : ".join(f"{v/vals[0]*12:.1f}" for v in vals),
      "(oracle 12 : 16 : 20)")

print("\n=== STANDING WAVE ===")
xs, us = [], []
for line in open("sw.out"):
    if line.startswith("#"):
        continue
    i, v = line.split()
    xs.append(int(i)); us.append(float(v))
us = np.array(us)
su = gaussian_smooth(us, sigma=1.5)
# cavity between source (40) and mirror (600); nodes inside it
core = su[50:595]
mins = find_minima(core)
mins = [m + 50 for m in mins]
mins = [m for m in mins if su[m] < 0.35 * su.max()]
if len(mins) > 1:
    nsp = np.diff(mins).mean()
else:
    nsp = float("nan")
print(f"nodes at x={mins[:20]}")
print(f"mean node spacing {nsp:.2f} cells (oracle 8.0, tolerance 1)")
