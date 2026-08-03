"""Maps for the (B, J) characterization grid -> maps/{gap,c,eta}_bj.png"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "results_bj_map.json")))
BS = sorted({r["B"] for r in R})
JS = sorted({r["J"] for r in R})


def grid(key):
    G = np.full((len(BS), len(JS)), np.nan)
    for r in R:
        G[BS.index(r["B"]), JS.index(r["J"])] = r.get(key, np.nan)
    return G


def plot(G, title, fname, cmap="viridis", vmin=None, vmax=None):
    fig, ax = plt.subplots(figsize=(7, 5.4))
    im = ax.imshow(G, origin="lower", aspect="auto", cmap=cmap,
                   extent=[JS[0], JS[-1], BS[0], BS[-1]], vmin=vmin, vmax=vmax)
    ax.axhline(0.25, color="r", lw=1.4, label="B = 0.25 (competition line)")
    ax.axvline(1.0, color="r", lw=0.9, ls="--")
    ax.axvline(1.1, color="r", lw=0.9, ls="--", label="J_c ~ 1.0-1.1")
    ax.set_xlabel("J"); ax.set_ylabel("B"); ax.set_title(title)
    ax.legend(fontsize=8, loc="upper right")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "maps", fname), dpi=150)
    print("wrote", fname)


os.makedirs(os.path.join(HERE, "maps"), exist_ok=True)
plot(grid("gap"), "gap E1-E0, rotor N=12", "gap_bj.png")
plot(grid("c"), "central charge c (CC fit), rotor N=12", "c_bj.png",
     cmap="plasma", vmin=0.0, vmax=1.2)
plot(grid("eta"), "correlator exponent eta, rotor N=12", "eta_bj.png",
     cmap="cividis")

# numeric summaries for the verdict
G_gap = grid("gap")
print("B=0.25 row: min gap %.4f at J=%.1f" % (
    np.nanmin(G_gap[BS.index(0.25)]), JS[int(np.nanargmin(G_gap[BS.index(0.25)]))]))
# valley position per J
for J in (0.5, 1.0, 1.5, 2.0):
    col = G_gap[:, JS.index(J)]
    print("J=%.1f: gap-min at B=%.3f (%.4f)" % (J, BS[int(np.nanargmin(col))], np.nanmin(col)))
# c on the line and flanks
G_c = grid("c")
for B in (0.20, 0.225, 0.25, 0.275, 0.30):
    row = G_c[BS.index(B)]
    print("c B=%.3f:" % B, " ".join("%.2f" % v for v in row))
G_eta = grid("eta")
row = G_eta[BS.index(0.25)]
print("eta B=0.25:", " ".join("%.3f" % v for v in row))
