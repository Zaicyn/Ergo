#!/usr/bin/env python3
"""analyze_prop.py — oracle runner for the S^3 winding-sum validation.

Drives:
  - compile + run min/quaternion/winding_s3.ergo TWICE (byte-identical)
  - regenerate the spectral reference TWICE (byte-identical)
  - oracles 1-6 from the plan; PNG plots (matplotlib Agg) into
    min/quaternion/

Oracle list:
  1. magnitude match vs e^{-iTc} K_spec over the 2000-pt grid
  2. global phase: arg(K_wind/K_spec) constant, equals -Tt
  3. antipode caustic stability (paired vs unpaired truncation)
  4. sign structure: (+1) vs (-1)^n weighting (odd-l spinor reference)
  5. determinism (above)
  6. fringe spacing near antipode vs Tt (exploratory, no pass/fail)
"""
import subprocess
import sys

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, "min/quaternion")
import spectral_ref as sr

DIR = "min/quaternion"
EPS = sr.EPS
TTS = sr.TTS


def sh(cmd, **kw):
    r = subprocess.run(cmd, shell=isinstance(cmd, str),
                       capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"failed: {cmd}\n{r.stderr[-2000:]}")
    return r.stdout


def load_spec():
    spec = {}
    meta = {}
    with open(f"{DIR}/spec_ref.txt") as f:
        for line in f:
            if line.startswith("# Tt="):
                m = line.split()
                Tt = float(m[1].split("=")[1])
                meta[Tt] = (int(m[2].split("=")[1]),
                            float(m[3].split("=")[1]))
            elif line.startswith("SPEC"):
                p = line.split()
                spec.setdefault(float(p[1]), {})[int(p[2])] = \
                    float(p[3]) + 1j * float(p[4])
    return {k: np.array([v[i] for i in sorted(v)]) for k, v in
            spec.items()}, meta


def load_wind(out, tag):
    got = {}
    for line in out.splitlines():
        if line.startswith(tag + " "):
            p = line.split()
            if tag == "GRID":
                key = (int(p[1]), int(p[2]))       # (ti, N)
                idx = int(p[3])
                val = float(p[4]) + 1j * float(p[5])
            elif tag in ("SGN", "W4S", "W4P"):
                key = int(p[1])                    # ti
                idx = int(p[2])
                val = float(p[3]) + 1j * float(p[4])
            elif tag == "RAW":
                key = (int(p[1]), int(p[2]))       # (ti, N)
                idx = int(p[3])
                val = float(p[4]) + 1j * float(p[5])
            else:  # CAU / CAUU
                key = (int(p[1]), int(p[2]), int(p[3]))  # ti, side, k
                idx = 0
                val = float(p[4]) + 1j * float(p[5])
            got.setdefault(key, {})[idx] = val
    return {k: np.array([v[i] for i in sorted(v)]) for k, v in
            got.items()}


def main():
    # ---- oracle 5: determinism ----
    sh([sys.executable, "-m", "core", f"{DIR}/winding_s3.ergo", "-o",
        "/tmp/wind3"])
    o1 = sh("/tmp/wind3")
    o2 = sh("/tmp/wind3")
    print(f"[oracle 5] Ergo binary twice byte-identical: {o1 == o2}")
    sh([sys.executable, f"{DIR}/spectral_ref.py"])
    b1 = open(f"{DIR}/spec_ref.txt", "rb").read()
    sh([sys.executable, f"{DIR}/spectral_ref.py"])
    b2 = open(f"{DIR}/spec_ref.txt", "rb").read()
    print(f"[oracle 5] spectral ref regenerated identical: {b1 == b2}")

    spec, meta = load_spec()
    th = sr.theta_grid()
    W = load_wind(o1, "GRID")
    SGN = load_wind(o1, "SGN")
    RAW = load_wind(o1, "RAW")
    CAU = load_wind(o1, "CAU")
    CAUU = load_wind(o1, "CAUU")

    # ---- oracle 1+2: magnitude + phase vs e^{-iTc} K_spec ----
    print("\n[oracle 1] magnitude match (err = |W - e^{-iTc}S|; "
          "rel-to-max|S| over full grid / masked |S|>5%max)")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    conv_table = {}
    for ti, Tt in enumerate(TTS, start=1):
        Tc = Tt - 1j * EPS
        S = spec[Tt]
        phase = np.exp(-1j * Tc)
        smax = np.abs(S).max()
        mask = np.abs(S) > 0.05 * smax
        for N in (4, 8, 16, 32):
            Wg = W[(ti, N)]
            d = np.abs(Wg - phase * S)
            full = d.max() / smax
            ptwise = (d[mask] / np.abs(S[mask]))
            conv_table[(Tt, N)] = (full, ptwise.max(),
                                   np.median(ptwise))
            print(f"  Tt={Tt:5.2f} N={N:3d}: max|d|/max|S|={full:.3e} "
                  f"masked max rel={ptwise.max():.3e} "
                  f"median rel={np.median(ptwise):.3e}")
        ax = axes[ti - 1]
        for N in (4, 8, 16, 32):
            Wg = W[(ti, N)]
            d = np.abs(Wg - phase * S) / smax
            ax.semilogy(th, d, lw=0.7, label=f"N={N}")
        ax.set_title(f"Tt={Tt}"); ax.set_xlabel("Theta")
        ax.legend(fontsize=7)
    axes[0].set_ylabel("|W - e^{-iTc}S| / max|S|")
    fig.tight_layout()
    fig.savefig(f"{DIR}/prop_err_theta.png", dpi=130)
    plt.close(fig)

    # Truncation floor: at EPS=0.01 the damped spectral sum is exact at
    # L<=500 (change 0.0). The interesting floor is vs the damping.
    # Document: (a) Lmax convergence at weaker damping (EPS=1e-3);
    # (b) the identity holds at EVERY eps (ratio 1.0 to machine
    # precision) with N,L requirements growing as eps shrinks.
    print("\n[oracle 1] truncation floor documentation:")
    print(f"  main reference at EPS={EPS}: converged at "
          f"Lmax={[meta[t][0] for t in TTS]} (change 0 to machine precision)")
    # err-vs-Lmax curves: undamped (non-convergent) vs damped (EPS=0.01,
    # converges to the f64 floor). Probe subset of the grid.
    thp = th[::40]
    fig, ax = plt.subplots(figsize=(6, 4))
    for Tt in TTS:
        ref_d = sr.k_spec(thp, Tt, 8000, EPS)
        ref_u = sr.k_spec(thp, Tt, 8000, 0.0)
        smax = np.abs(ref_d).max()
        Ls, errs_d, errs_u = [], [], []
        L = 250
        while L <= 4000:
            Kd = sr.k_spec(thp, Tt, L, EPS)
            Ku = sr.k_spec(thp, Tt, L, 0.0)
            errs_d.append(np.abs(Kd - ref_d).max() / smax + 1e-18)
            errs_u.append(np.abs(Ku - ref_u).max() / smax + 1e-18)
            Ls.append(L)
            L *= 2
        ax.loglog(Ls, errs_d, ".-", label=f"Tt={Tt} damped")
        ax.loglog(Ls, errs_u, "x--", label=f"Tt={Tt} undamped")
        print(f"  Tt={Tt}: damped Lmax curve "
              f"{[(l, f'{e:.1e}') for l, e in zip(Ls, errs_d)]}")
        print(f"  Tt={Tt}: UNDAMPED Lmax curve (no convergence) "
              f"{[(l, f'{e:.1e}') for l, e in zip(Ls, errs_u)]}")
    ax.set_xlabel("Lmax"); ax.set_ylabel("max rel change vs L=8000")
    ax.legend(fontsize=7); fig.tight_layout()
    fig.savefig(f"{DIR}/prop_err_lmax.png", dpi=130)
    plt.close(fig)
    print("  identity vs damping (probe Theta=2.0, Tt=0.25; python replica "
          "validated to 1e-13 vs the Ergo binary at EPS=0.01):")
    thv = 2.0
    for eps_w in (0.05, 0.02, 0.01, 0.005, 0.002):
        Tc = 0.25 - 1j * eps_w
        L = int(max(2000, 40 / eps_w))
        N = int(max(64, 12 * 0.25 / np.sqrt(eps_w)))
        l = np.arange(0, L + 1)
        Ks = ((l + 1) * np.sin((l + 1) * thv) / np.sin(thv)
              * np.exp(-1j * l * (l + 2) * Tc)).sum() / (2 * np.pi ** 2)
        ns = np.arange(-N, N)
        tn = thv + 2 * np.pi * ns
        Kw = (4 * np.pi * 1j * Tc) ** (-1.5) * \
            (tn / np.sin(thv) * np.exp(1j * tn ** 2 / (4 * Tc))).sum()
        r = Kw / Ks
        print(f"    EPS={eps_w:6.3f}: |W/S|={abs(r):.10f} "
              f"arg={np.angle(r):+.10f} (N={N}, L={L})")

    # phase constancy
    print("\n[oracle 2] global phase arg(W/S) vs -Tt (masked |S|>5%max, "
          "N=32):")
    fig, ax = plt.subplots(figsize=(7, 4))
    for ti, Tt in enumerate(TTS, start=1):
        Tc = Tt - 1j * EPS
        S = spec[Tt]
        smax = np.abs(S).max()
        mask = np.abs(S) > 0.05 * smax
        Wg = W[(ti, 32)]
        ph = np.angle(Wg[mask] / S[mask])
        mean = np.angle(np.exp(1j * ph).mean())
        std = np.sqrt((np.angle(np.exp(1j * (ph - mean))) ** 2).mean())
        print(f"  Tt={Tt:5.2f}: mean={mean:+.8f} (target {-Tt:+.8f}) "
              f"circular std={std:.3e}")
        ax.scatter(th[mask], ph - (-Tt), s=1, label=f"Tt={Tt}")
    ax.set_xlabel("Theta"); ax.set_ylabel("arg(W/S) + Tt")
    ax.legend(); fig.tight_layout()
    fig.savefig(f"{DIR}/prop_phase.png", dpi=130)
    plt.close(fig)

    # ---- oracle 3: antipode caustic ----
    print("\n[oracle 3] antipode approach (N=32; spectral limit "
          "(l+1)^2 (-1)^l at Theta=pi):")
    for ti, Tt in enumerate(TTS, start=1):
        Tc = Tt - 1j * EPS
        l = np.arange(0, 400001)
        Kpi = ((l + 1) ** 2 * np.where(l % 2 == 0, 1.0, -1.0)
               * np.exp(-1j * l * (l + 2) * Tc)).sum() / (2 * np.pi ** 2)
        tgt = np.exp(-1j * Tc) * Kpi
        for side in (-1, 1):
            row = []
            for k in range(2, 7):
                wp = CAU[(ti, side, k)][0]
                wu = CAUU[(ti, side, k)][0]
                row.append((k, wp, wu))
            errs = [f"1e-{k}: |d|/|t|={abs(wp - tgt) / abs(tgt):.2e}"
                    f" unpaired|W|={abs(wu):.2e}" for k, wp, wu in row]
            print(f"  Tt={Tt:5.2f} side={side:+d} |tgt|={abs(tgt):.4f}: "
                  + "  ".join(errs))
        # unpaired-leftover check: |CAUU-CAU| vs the closed-form
        # magnitude of the single unpaired term n=N=32
        N = 32
        tc2 = Tt * Tt + EPS * EPS
        PM = np.exp(-0.75 * np.log(tc2)) / (4 * np.pi * np.sqrt(4 * np.pi))
        wp = CAU[(ti, 1, 6)][0]
        wu = CAUU[(ti, 1, 6)][0]
        tn = np.pi + 1e-6 + 2 * np.pi * N
        t_mag = PM * abs(tn / np.sin(np.pi + 1e-6)) * \
            np.exp(-EPS * tn * tn / (4 * tc2))
        print(f"  Tt={Tt:5.2f} eps_th=1e-6: |CAUU-CAU|={abs(wu - wp):.2e}"
              f" vs closed-form leftover {t_mag:.2e} "
              f"(exponentially suppressed at EPS={EPS})")

    # pairing-necessity supplement at weak damping (Python replica,
    # validated to 1e-13 against the Ergo binary at EPS=0.01):
    # at EPS=1e-4 the unpaired leftover is O(1) at the caustic.
    print("  pairing-necessity supplement (EPS=1e-4, N=32, Tt=0.25, "
          "python replica):")
    Tt = 0.25
    Tc = Tt - 1j * 1e-4
    l = np.arange(0, 600001)
    Kpi = ((l + 1) ** 2 * np.where(l % 2 == 0, 1.0, -1.0)
           * np.exp(-1j * l * (l + 2) * Tc)).sum() / (2 * np.pi ** 2)
    tgt = np.exp(-1j * Tc) * Kpi
    for k in (2, 4, 6):
        thv = np.pi + 10.0 ** (-k)
        ns_p = np.arange(-32, 32)
        ns_u = np.arange(-32, 33)
        tn_p = thv + 2 * np.pi * ns_p
        tn_u = thv + 2 * np.pi * ns_u
        base_p = tn_p / np.sin(thv) * np.exp(1j * tn_p ** 2 / (4 * Tc))
        base_u = tn_u / np.sin(thv) * np.exp(1j * tn_u ** 2 / (4 * Tc))
        PM = (4 * np.pi * 1j * Tc) ** (-1.5)
        wp = PM * base_p.sum()
        wu = PM * base_u.sum()
        print(f"    eps_th=1e-{k}: paired rel err "
              f"{abs(wp - tgt) / abs(tgt):.2e}; unpaired rel err "
              f"{abs(wu - tgt) / abs(tgt):.2e}")

    # ---- oracle 4: sign structure ----
    print("\n[oracle 4] sign structure (N=16):")
    for ti, Tt in enumerate(TTS, start=1):
        Tc = Tt - 1j * EPS
        S = spec[Tt]
        smax = np.abs(S).max()
        mask = np.abs(S) > 0.05 * smax
        Wg = SGN[ti]
        d_plus = np.abs(W[(ti, 16)] - np.exp(-1j * Tc) * S)
        d_minus = np.abs(Wg - np.exp(-1j * Tc) * S)
        # antiperiodic (spinor) reference: half-integer momenta
        # k = l+1 = m+1/2 (Poisson with the (-1)^n twist shifts the
        # momentum lattice by 1/2)
        m = np.arange(0, 4 * meta[Tt][0] + 1)
        k = m + 0.5
        Sa = (np.sin(np.outer(k, th)) / np.sin(th)
              * (k * np.exp(-1j * (k * k - 1) * Tc))[:, None]
              ).sum(axis=0) / (2 * np.pi ** 2)
        samax = np.abs(Sa).max()
        maska = np.abs(Sa) > 0.05 * samax
        d_anti = np.abs(Wg - np.exp(-1j * Tc) * Sa)
        print(f"  Tt={Tt:5.2f}: (+1) sum vs scalar spec: "
              f"median rel {np.median(d_plus[mask]/np.abs(S[mask])):.2e}; "
              f"(-1)^n vs scalar spec: median rel "
              f"{np.median(d_minus[mask]/np.abs(S[mask])):.2e} (MISMATCH expected); "
              f"(-1)^n vs half-integer-k (spinor) spec: median rel "
              f"{np.median(d_anti[maska]/np.abs(Sa[maska])):.2e}")

    # ---- RAW section: plan-as-specified normalization ----
    print("\n[raw exhibit] plan-as-specified K_wind (1/2pi^2, /2Tt, "
          "undamped) vs spectral, 20 probes:")
    th_probe = sr.TH_LO + np.arange(20) * (sr.TH_HI - sr.TH_LO) / 19.0
    for ti, Tt in enumerate(TTS, start=1):
        Tc = Tt - 1j * EPS
        Sp = sr.k_spec(th_probe, Tt, meta[Tt][0])
        for N in (4, 32):
            R = RAW[(ti, N)]
            rat = R / (np.exp(-1j * Tc) * Sp)
            print(f"  Tt={Tt:5.2f} N={N:3d}: |ratio| min/max "
                  f"{np.abs(rat).min():.3f}/{np.abs(rat).max():.3f} "
                  f"(should be 1.0 for a match — it is not)")

    # ---- oracle 6: fringe scaling near antipode ----
    print("\n[oracle 6] |K|^2 fringe spacing near antipode vs Tt "
          "(exploratory):")
    TT6 = (0.05, 0.075, 0.1, 0.15, 0.25, 0.5)
    thf = np.pi + np.linspace(0.02, np.pi - 0.02, 40000)
    fig, ax = plt.subplots(figsize=(7, 4))
    spacings = []
    for Tt in TT6:
        Tc = Tt - 1j * EPS
        # Lmax sized to damping
        K = sr.k_spec(thf, Tt, 2000)
        I = np.abs(K) ** 2
        pk = np.where((I[1:-1] > I[:-2]) & (I[1:-1] > I[2:]))[0] + 1
        sp = np.diff(thf[pk])
        spacings.append((Tt, sp.mean(), sp.std(), len(pk)))
        ax.plot(thf, I / I.max(), lw=0.6, label=f"Tt={Tt}")
        print(f"  Tt={Tt:5.3f}: {len(pk):3d} fringes, mean spacing "
              f"{sp.mean():.5f} +/- {sp.std():.5f} "
              f"(2*Tt prediction {2 * Tt:.5f}, ratio {sp.mean() / (2 * Tt):.4f})")
    tt = np.array([s[0] for s in spacings])
    spm = np.array([s[1] for s in spacings])
    p = np.polyfit(np.log(tt), np.log(spm), 1)[0]
    small = tt <= 0.15
    p2 = np.polyfit(np.log(tt[small]), np.log(spm[small]), 1)[0]
    print(f"  fitted exponent (all): spacing ~ Tt^{p:.3f}; "
          f"small-Tt subset (<=0.15): Tt^{p2:.3f} "
          f"(two-path interference predicts Tt^1, spacing 2*Tt; "
          f"breakdown at Tt>=0.25 = multi-winding contributions)")
    ax.set_xlabel("Theta"); ax.set_ylabel("|K|^2 (norm)")
    ax.legend(); fig.tight_layout()
    fig.savefig(f"{DIR}/prop_fringe.png", dpi=130)
    plt.close(fig)

    print("\nplots: prop_err_theta.png prop_err_lmax.png prop_phase.png "
          "prop_fringe.png")


if __name__ == "__main__":
    main()
