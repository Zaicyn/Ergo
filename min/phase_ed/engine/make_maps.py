"""Gap heatmaps for sweep1 results -> maps/{rotor,xxz,fk,rydberg}_gap.png"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "results_sweep1.json")))
os.makedirs(os.path.join(HERE, "maps"), exist_ok=True)


def gridmap(sw, keyx, keyy, val="gap"):
    xs = sorted({p["params"][keyx] for p in sw["points"]})
    ys = sorted({p["params"][keyy] for p in sw["points"]})
    G = np.full((len(ys), len(xs)), np.nan)
    for p in sw["points"]:
        G[ys.index(p["params"][keyy]), xs.index(p["params"][keyx])] = p[val]
    return np.array(xs), np.array(ys), G


for sw in R["sweeps"]:
    name = sw["model"]
    fig, ax = plt.subplots(figsize=(7, 5))
    if name == "rotor_spin1":
        x, y, G = gridmap(sw, "J", "B")
        im = ax.imshow(G, origin="lower", aspect="auto", cmap="viridis",
                       extent=[x[0], x[-1], y[0], y[-1]])
        ax.axhline(0.25, color="r", lw=1.5, label="competition line B=0.25")
        ax.axvline(1.0, color="r", lw=1, ls="--")
        ax.axvline(1.1, color="r", lw=1, ls="--", label="J_c ~ 1.0-1.1")
        ax.set_xlabel("J"); ax.set_ylabel("B"); ax.legend(fontsize=8)
    elif name == "xxz":
        x, y, G = gridmap(sw, "Delta", "h")
        im = ax.imshow(G, origin="lower", aspect="auto", cmap="viridis",
                       extent=[x[0], x[-1], y[0], y[-1]])
        ax.axvline(1.0, color="r", lw=1.5, label="Delta=1 (BKT)")
        ax.axvline(-1.0, color="w", lw=1, ls="--")
        ax.set_xlabel("Delta"); ax.set_ylabel("h"); ax.legend(fontsize=8)
    elif name == "fk_pendulum":
        x, y, G = gridmap(sw, "J", "V")
        im = ax.imshow(G, origin="lower", aspect="auto", cmap="viridis",
                       extent=[x[0], x[-1], y[0], y[-1]])
        ax.set_xlabel("J"); ax.set_ylabel("V")
    else:  # rydberg
        d = sorted({p["params"]["Delta"] for p in sw["points"]})
        g1 = [p["gap"] for p in sorted(sw["points"],
                                       key=lambda p: p["params"]["Delta"])]
        g2 = [p["gap2"] for p in sorted(sw["points"],
                                        key=lambda p: p["params"]["Delta"])]
        ax.plot(d, g1, "o-", label="E1-E0 (cat doublet)")
        ax.plot(d, g2, "s--", label="E2-E0")
        ax.axvspan(0.5, 1.0, color="r", alpha=0.1, label="transition region")
        ax.set_xlabel("delta"); ax.set_ylabel("gap"); ax.legend(fontsize=8)
        ax.set_yscale("log")
    ax.set_title(f"{name} gap map, N={sw['N']}")
    if name != "rydberg_blockade":
        fig.colorbar(im, ax=ax, label="gap")
    fig.tight_layout()
    short = {"rotor_spin1": "rotor", "xxz": "xxz", "fk_pendulum": "fk",
             "rydberg_blockade": "rydberg"}[name]
    fig.savefig(os.path.join(HERE, "maps", f"{short}_gap.png"), dpi=150)
    print("wrote maps/%s_gap.png" % short)
print("done")
