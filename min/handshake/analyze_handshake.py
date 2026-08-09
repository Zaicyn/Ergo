#!/usr/bin/env python3
"""analyze_handshake.py — oracle driver for the H2+ handshake solver.

Drives:
  1. determinism: production binary run twice, byte-identical.
  2. ATOM oracle (Stage 1): h2p.ergo grid variants (text-substituted
     NX/BOX, scan loop skipped) at dx = {0.25, 0.1667, 0.125}; E vs dx^2
     fit, extrapolation to dx->0, comparison with -0.5 Ha.
  3. Burrau oracle table (Stage 2): E_sigma_g/u(R) vs the sourced
     nonrelativistic table (arXiv:2310.04057 / Burrau-Bates-Wind);
     D_e from E+1/R; split exponent from log(DeltaE/R) vs R.
  4. Spot budget at R=2: sigma_g at three grids, dx^2 extrapolation
     vs the exact -1.1026342.
  5. Stage-3 overlap mixing curves + PNG plots.

Exact reference table (electronic energies, Ha):
  1sigma_g: arXiv:2310.04057 Table I (E_nr column; two-center Dirac
  paper quoting the nonrelativistic benchmark [33] therein).
  2sigma_u at R=2: -0.66753 (Bates & Wind standard tabulation).
  Limits: united sigma_g -> -2.0 (He+ 1s), sigma_u -> -0.5 (He+ 2p);
  separated -> -0.5 both.
"""
import subprocess
import sys

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = "min/handshake/h2p.ergo"

# electronic energies, exact (sourced)
SIGG_EXACT = {0.5: -1.7349880, 1.0: -1.4517863, 1.5: -1.2489899,
              2.0: -1.1026342, 3.0: -0.9108962, 4.0: -0.7960849,
              6.0: -0.6786357, 8.0: -0.6275704}
SIGU_R2 = -0.66753


def sh(cmd, timeout=3600, **kw):
    r = subprocess.run(cmd, shell=isinstance(cmd, str),
                       capture_output=True, text=True, timeout=timeout,
                       **kw)
    if r.returncode != 0:
        raise RuntimeError(f"failed: {cmd}\n{r.stderr[-1500:]}")
    return r.stdout


def build_variant(nx, box, nsteps, scan_rs, tag):
    dx0 = 2.0 * box / nx
    dtau = 0.9 * dx0 * dx0 / 6.0
    nsteps = max(nsteps, int(20.0 / dtau))
    """Text-substitute h2p.ergo into /tmp variant; compile."""
    src = open(SRC).read()
    src = src.replace("INTEGER, PARAMETER :: NX = 128",
                      f"INTEGER, PARAMETER :: NX = {nx}")
    src = src.replace("REAL, PARAMETER :: BOX = 16.0",
                      f"REAL, PARAMETER :: BOX = {box}")
    src = src.replace("REAL, PARAMETER :: DTAU = 0.008",
                      f"REAL, PARAMETER :: DTAU = {dtau:.10f}")
    src = src.replace("INTEGER, PARAMETER :: NSTEPS = 2500",
                      f"INTEGER, PARAMETER :: NSTEPS = {nsteps}")

    src = src.replace("INTEGER, PARAMETER :: NPTS = 2097152",
                      f"INTEGER, PARAMETER :: NPTS = {nx ** 3}")
    src = src.replace("INTEGER, PARAMETER :: NXY = 16384",
                      f"INTEGER, PARAMETER :: NXY = {nx * nx}")
    if scan_rs is None:
        src = src.replace("DO IR = 1, 10", "DO IR = 1, 0")
    else:
        lst = ", ".join(f"{r}" for r in scan_rs)
        src = src.replace("STATIC REAL :: RLIST(10)",
                          f"STATIC REAL :: RLIST({len(scan_rs)})")
        src = src.replace(
            "DATA RLIST / 0.2, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, "
            "12.0 /",
            f"DATA RLIST / {lst} /")
        src = src.replace("DO IR = 1, 10",
                          f"DO IR = 1, {len(scan_rs)}")
    path = f"/tmp/h2p_var_{tag}.ergo"
    with open(path, "w") as f:
        f.write(src)
    sh([sys.executable, "-m", "core", path, "-o", f"/tmp/h2p_{tag}"])
    return f"/tmp/h2p_{tag}"


def parse_atom(out):
    last = None
    for line in out.splitlines():
        if line.startswith("ATOM"):
            last = line.split()
    return float(last[-1])  # E_TOT at final checkpoint


def parse_scan(out):
    E, OVL, CONV = {}, {}, {}
    for line in out.splitlines():
        p = line.split()
        if p[0] == "E":
            E[(float(p[1]), int(p[2]))] = float(p[5])
        elif p[0] == "OVL":
            OVL[(float(p[1]), int(p[2]))] = [float(v) for v in p[3:]]
        elif p[0] == "CONV":
            CONV[(float(p[1]), int(p[2]), int(p[3]))] = float(p[4])
    return E, OVL, CONV


def main():
    # ---- 1. determinism ----
    o1 = sh("/tmp/h2p")
    o2 = sh("/tmp/h2p")
    print(f"[det] production binary twice byte-identical: {o1 == o2}")

    # ---- 2. atom grid convergence ----
    print("\n[oracle: atom] grid convergence (L=16, exact Coulomb):")
    atom = {}
    for nx in (128, 192, 256):
        b = build_variant(nx, 16.0, 2500, None, f"atom{nx}")
        out = sh(b)
        e = parse_atom(out)
        atom[nx] = e
        dx = 32.0 / nx
        print(f"  NX={nx} dx={dx:.4f}: E = {e:.6f} "
              f"(err {e + 0.5:+.2e})")
    dxs = np.array([32.0 / n for n in (128, 192, 256)])
    es = np.array([atom[n] for n in (128, 192, 256)])
    A = np.column_stack([np.ones(3), dxs ** 2])
    coef, *_ = np.linalg.lstsq(A, es, rcond=None)
    print(f"  dx^2 fit: E0 = {coef[0]:.6f} (target -0.5, residual "
          f"{coef[0] + 0.5:+.2e}); slope {coef[1]:.4f}")

    # ---- 3. scan oracles ----
    E, OVL, CONV = parse_scan(o1)
    print("\n[oracle: scan] sigma_g electronic energies vs exact:")
    print(f"  {'R':>5} {'E_comp':>10} {'E_exact':>10} {'dev':>9}")
    for R in sorted(SIGG_EXACT):
        ec = E[(R, 1)]
        ee = SIGG_EXACT[R]
        print(f"  {R:5.1f} {ec:10.6f} {ee:10.6f} {ec - ee:+9.2e}")
    # united/separated limits
    print(f"  united (R=0.2): sigma_g {E[(0.2,1)]:.4f} (limit -2.0); "
          f"sigma_u {E[(0.2,2)]:.4f} (limit -0.5)")
    print(f"  separated (R=12): sigma_g {E[(12.0,1)]:.4f}, sigma_u "
          f"{E[(12.0,2)]:.4f} (limit -0.5)")
    print(f"  sigma_u at R=2: {E[(2.0,2)]:.6f} vs Bates-Wind "
          f"{SIGU_R2} (dev {E[(2.0,2)] - SIGU_R2:+.2e})")
    # D_e
    R_e = 2.0
    d_e = -0.5 - (E[(R_e, 1)] + 1.0 / R_e)
    print(f"  D_e = -0.5 - (E_g(2.0)+1/2) = {d_e:.6f} Ha "
          f"(target 0.10263)")
    # split exponent
    print("\n[oracle: split] DeltaE = E_u - E_g:")
    for R in sorted(SIGG_EXACT):
        de = E[(R, 2)] - E[(R, 1)]
        print(f"  R={R:5.1f}: dE={de:+.5e}")
    Rs = np.array([4.0, 6.0, 8.0, 12.0])
    des = np.array([E[(R, 2)] - E[(R, 1)] for R in Rs])
    sl = np.polyfit(Rs, np.log(des / Rs), 1)[0]
    print(f"  fit log(dE/R) vs R over R=4..12: slope {sl:.4f} "
          f"(~-1 expected for ~R*exp(-R))")
    # convergence checkpoint spread
    print("\n[convergence] max |E(2000)-E(2500)| over scan:")
    mx = 0.0
    for (R, ip, t), e in CONV.items():
        if t == 2500:
            e2 = CONV[(R, ip, 2000)]
            mx = max(mx, abs(e - e2))
    print(f"  {mx:.2e}")

    # ---- 4. R=2 spot budget ----
    print("\n[oracle: R=2 budget] sigma_g at three grids:")
    spot = {}
    for nx in (128, 192, 256):
        b = build_variant(nx, 16.0, 2500, [2.0], f"spot{nx}")
        out = sh(b)
        Ev, _, _ = parse_scan(out)
        spot[nx] = Ev[(2.0, 1)]
        print(f"  NX={nx}: E_g(2) = {spot[nx]:.6f}")
    es = np.array([spot[n] for n in (128, 192, 256)])
    coef, *_ = np.linalg.lstsq(A, es, rcond=None)
    print(f"  dx^2 extrapolation: E0 = {coef[0]:.6f} vs exact "
          f"-1.1026342 (residual {coef[0] + 1.1026342:+.2e})")

    # ---- 5. overlaps + plots ----
    print("\n[stage 3] overlap mixing (|sep_sym|^2 |sep_anti|^2 "
          "|He1s|^2 |He2s|^2 |He2p|^2):")
    for R in (0.2, 0.5, 1.0, 2.0, 4.0, 8.0, 12.0):
        for ip, nm in ((1, "sigma_g"), (2, "sigma_u")):
            o = OVL[(R, ip)]
            sq = [f"{v * v:.3f}" for v in o]
            print(f"  R={R:5.1f} {nm}: " + " ".join(sq))

    fig, ax = plt.subplots(figsize=(7, 4.5))
    Rl = sorted(SIGG_EXACT)
    ax.plot(Rl, [E[(R, 1)] for R in Rl], "o-", label="sigma_g (this work)")
    ax.plot(Rl, [SIGG_EXACT[R] for R in Rl], "s--", label="sigma_g (exact)")
    ax.plot(Rl, [E[(R, 2)] for R in Rl], "^-", label="sigma_u (this work)")
    ax.set_xlabel("R (bohr)")
    ax.set_ylabel("electronic energy (Ha)")
    ax.legend()
    fig.tight_layout()
    fig.savefig("min/handshake/h2p_energy.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(Rs, np.log(des / Rs), "o-")
    ax.set_xlabel("R (bohr)")
    ax.set_ylabel("log(dE / R)")
    ax.set_title(f"sigma split: slope {sl:.3f}")
    fig.tight_layout()
    fig.savefig("min/handshake/h2p_split.png", dpi=130)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    Rs_all = sorted(SIGG_EXACT) + [12.0]
    for ax, (ip, nm) in zip(axes, [(1, "sigma_g"), (2, "sigma_u")]):
        for k, lab in ((0, "|1sL+1sR|^2"), (1, "|1sL-1sR|^2"),
                       (2, "|He+ 1s|^2"), (3, "|He+ 2s|^2"),
                       (4, "|He+ 2p|^2")):
            ax.plot(Rs_all, [OVL[(R, ip)][k] ** 2 for R in Rs_all],
                    ".-", label=lab)
        ax.set_title(nm)
        ax.set_xlabel("R (bohr)")
        ax.legend(fontsize=7)
    axes[0].set_ylabel("squared overlap")
    fig.tight_layout()
    fig.savefig("min/handshake/h2p_overlaps.png", dpi=130)
    plt.close(fig)
    print("\nplots: h2p_energy.png h2p_split.png h2p_overlaps.png")


if __name__ == "__main__":
    main()
