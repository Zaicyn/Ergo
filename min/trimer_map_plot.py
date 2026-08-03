"""Trimer 2D map plots: I(x,y) per Vs + |dI/dV|(x,y) at 790 mV.

Reads min/trimer_map.out (columns X Y VS I_TIP Q_TOT W_SING), writes
min/maps/*.png and min/trimer_map.npz.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "maps")
os.makedirs(OUT, exist_ok=True)

rows = []
for line in open(os.path.join(HERE, "trimer_map.out")):
    if line.startswith("#") or not line.strip():
        continue
    p = line.split()
    rows.append((float(p[0]), float(p[1]), float(p[2]),
                 float(p[3]), float(p[4]), float(p[5])))
data = np.array(rows)
NGX = NGY = 60
X = np.unique(data[:, 0])
Y = np.unique(data[:, 1])
VS_VALUES = sorted(set(data[:, 2]))

grids = {}
for vs in VS_VALUES:
    sel = data[data[:, 2] == vs]
    I = sel[:, 3].reshape(NGY, NGX)
    Q = sel[:, 4].reshape(NGY, NGX)
    W = sel[:, 5].reshape(NGY, NGX)
    grids[vs] = {"I": I, "Q": Q, "W": W}

SITES = [(0.0, 0.0), (1.0, 0.0), (0.5, 0.8660254)]

np.savez(os.path.join(HERE, "trimer_map.npz"),
         X=X, Y=Y, **{f"I_{int(vs)}": grids[vs]["I"] for vs in VS_VALUES},
         **{f"Q_{int(vs)}": grids[vs]["Q"] for vs in VS_VALUES},
         **{f"W_{int(vs)}": grids[vs]["W"] for vs in VS_VALUES})


def plot_field(field, title, fname, cmap="viridis", symmetric=False):
    fig, ax = plt.subplots(figsize=(6, 5))
    vmax = np.abs(field).max() if symmetric else None
    im = ax.imshow(field, origin="lower", aspect="auto", cmap=cmap,
                   extent=[X.min(), X.max(), Y.min(), Y.max()],
                   vmin=-vmax if symmetric else None,
                   vmax=vmax if symmetric else None)
    for sx, sy in SITES:
        ax.plot(sx, sy, "r*", ms=14, mec="white")
    ax.plot(0.5, 0.2886751, "w+", ms=10, mew=2)  # trimer center
    ax.set_xlabel("x (nm)"); ax.set_ylabel("y (nm)")
    ax.set_title(title)
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=150)
    plt.close(fig)
    print("wrote", fname)


for vs in VS_VALUES:
    plot_field(grids[vs]["I"], f"I_tip (x,y), Vs = {int(vs)} mV",
               f"I_map_{int(vs)}mV.png")
    plot_field(grids[vs]["W"], f"W_singlet (x,y), Vs = {int(vs)} mV",
               f"Wsing_map_{int(vs)}mV.png")

# dI/dV at 790 via central difference 770/810 (h = 40 mV)
dIdV = (grids[810.0]["I"] - grids[770.0]["I"]) / 40.0
plot_field(dIdV, "dI/dV (x,y), Vs = 790 mV (central diff, h=40 mV)",
           "dIdV_map_790mV.png", cmap="RdBu_r", symmetric=True)
plot_field(np.abs(dIdV), "|dI/dV| (x,y), Vs = 790 mV",
           "absdIdV_map_790mV.png")

# quick diagnostics for the verdict
print("=== diagnostics ===")
for vs in VS_VALUES:
    I = grids[vs]["I"]
    print(f"Vs={int(vs)}: Imax={I.max():.4f} Imin={I.min():.4f} "
          f"Imax(center region)={I[20:40, 20:40].max():.4f}")
neg = (dIdV < 0)
print(f"dIdV<0 fraction: {neg.mean():.3f}, min dIdV={dIdV.min():.4f}, "
      f"max={dIdV.max():.4f}")
if neg.any():
    yy, xx = np.where(neg)
    print(f"negative region: x in [{X[xx].min():.2f},{X[xx].max():.2f}], "
          f"y in [{Y[yy].min():.2f},{Y[yy].max():.2f}]")
EOF_MARKER = None
