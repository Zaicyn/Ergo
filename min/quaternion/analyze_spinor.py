#!/usr/bin/env python3
"""analyze_spinor.py — spinor double-cover signature oracles.

Extends (does not replace) analyze_prop.py. Oracles:
  1. antiperiodicity gate: K_s(Theta+2pi)/K_s(Theta) = +1 and
     K_sp(Theta+2pi)/K_sp(Theta) = -1, winding AND spectral sides.
  2. Berry-ratio audit: arg(K_sp/K_s) vs Theta at Tt in
     {0.1, 0.25, 0.5, pi/2} (data, no pass/fail).
  3. revival spectra: |K_s|^2, |K_sp|^2 at Theta=pi/3 over
     Tt in (0, 4pi) (data).
  4. cycloid-mapping audit (expected null).
Determinism: binary twice byte-identical; analyzer twice identical.
Regression: analyze_prop.py stdout must be unchanged.
"""
import subprocess
import sys

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, "min/quaternion")
import spectral_ref as sr
from analyze_prop import load_spec, load_wind, sh

DIR = "min/quaternion"
EPS = sr.EPS
TTS = sr.TTS
TT_PI2 = 1.5707963267948966


def main():
    # ---- determinism ----
    sh([sys.executable, "-m", "core", f"{DIR}/winding_s3.ergo", "-o",
        "/tmp/wind3"])
    o1 = sh("/tmp/wind3")
    o2 = sh("/tmp/wind3")
    print(f"[det] Ergo binary twice byte-identical: {o1 == o2}")

    th = sr.theta_grid()
    W4S = load_wind(o1, "W4S")
    W4P = load_wind(o1, "W4P")
    GRID = load_wind(o1, "GRID")
    SGN = load_wind(o1, "SGN")

    # ---- oracle 1: antiperiodicity gate ----
    print("\n[oracle 1] antiperiodicity: ratio K(Theta+2pi)/K(Theta), "
          "masked |K|>1% of max (N=16 winding; spectral cross-check)")
    rows = []
    for ti, Tt in enumerate(TTS, start=1):
        Tc = Tt - 1j * EPS
        # winding side
        Ks1 = GRID[(ti, 16)]
        Ks2 = W4S[ti]
        Kp1 = SGN[ti]
        Kp2 = W4P[ti]
        out = [f"Tt={Tt:5.2f}"]
        for name, A, B in (("scalar", Ks1, Ks2), ("spinor", Kp1, Kp2)):
            mask = np.abs(A) > 0.01 * np.abs(A).max()
            r = B[mask] / A[mask]
            tgt = 1.0 if name == "scalar" else -1.0
            dev = np.abs(r - tgt)
            out.append(f"{name}: median|dev|={np.median(dev):.2e} "
                       f"p95={np.percentile(dev, 95):.2e} "
                       f"max={dev.max():.2e}")
        # spectral side
        Ss1 = sr.k_spec(th, Tt, 500)
        Ss2 = sr.k_spec(th + 2 * np.pi, Tt, 500)
        Sp1 = sr.k_spec_spinor(th, Tt, 500)
        Sp2 = sr.k_spec_spinor(th + 2 * np.pi, Tt, 500)
        for name, A, B in (("spec-scalar", Ss1, Ss2),
                           ("spec-spinor", Sp1, Sp2)):
            mask = np.abs(A) > 0.01 * np.abs(A).max()
            r = B[mask] / A[mask]
            tgt = 1.0 if "scalar" in name else -1.0
            dev = np.abs(r - tgt)
            out.append(f"{name}: median|dev|={np.median(dev):.2e} "
                       f"max={dev.max():.2e}")
        print("  " + " | ".join(out))
        rows.append(out)

    # winding-vs-spectral agreement on the extended grid
    print("  winding-vs-spectral agreement on grid2 (max rel err vs "
          "e^{-iTc} ref):")
    for ti, Tt in enumerate(TTS, start=1):
        Tc = Tt - 1j * EPS
        Ss2 = sr.k_spec(th + 2 * np.pi, Tt, 500)
        Sp2 = sr.k_spec_spinor(th + 2 * np.pi, Tt, 500)
        es = np.abs(W4S[ti] - np.exp(-1j * Tc) * Ss2)
        ep = np.abs(W4P[ti] - np.exp(-1j * Tc) * Sp2)
        print(f"  Tt={Tt:5.2f}: scalar max|d|/max|S|="
              f"{es.max() / np.abs(Ss2).max():.2e}  spinor "
              f"{ep.max() / np.abs(Sp2).max():.2e}")

    # ---- oracle 2: Berry-ratio audit ----
    print("\n[oracle 2] Berry-ratio arg(K_sp/K_s) vs Theta (data):")
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for ax, (ti, Tt) in zip(axes.flat,
                            [(1, 0.1), (2, 0.25), (3, 0.5),
                             (4, TT_PI2)]):
        Ks = GRID[(ti, 16)]
        Kp = SGN[ti]
        mask = (np.abs(Ks) > 1e-3 * np.abs(Ks).max()) & \
               (np.abs(Kp) > 1e-3 * np.abs(Kp).max())
        ph = np.angle(Kp[mask] / Ks[mask])
        ax.scatter(th[mask], ph, s=1)
        ax.axvline(np.pi, color="k", lw=0.5, ls="--")
        ttl = f"Tt={Tt:.4g}" + (" (revival)" if ti == 4 else "")
        ax.set_title(ttl)
        # phase flip across the antipode: circular means in flanking
        # windows (loose mask — the flip is exact parity; amplitudes
        # near the antipode can be small, esp. spinor at Tt=pi/2)
        phf = np.angle(Kp / Ks)
        cms = []
        for lo, hi in ((np.pi - 0.3, np.pi - 0.05),
                       (np.pi + 0.05, np.pi + 0.3)):
            w = (th > lo) & (th < hi)
            cms.append(np.angle(np.exp(1j * phf[w]).mean()))
        flip = abs(abs(cms[1] - cms[0]) - np.pi)
        wsp = (th > np.pi - 0.3) & (th < np.pi + 0.3)
        supp = np.abs(Kp[wsp]).mean() / np.abs(Kp).max()
        print(f"  Tt={Tt:7.5f}: window phases {cms[0]:+.4f} / "
              f"{cms[1]:+.4f} rad; |flip - pi| = {flip:.2e}; "
              f"antipode spinor amplitude suppression {supp:.2e}")
    for ax in axes[-1]:
        ax.set_xlabel("Theta")
    for ax in axes[:, 0]:
        ax.set_ylabel("arg(K_sp/K_s)")
    fig.tight_layout()
    fig.savefig(f"{DIR}/spinor_berry.png", dpi=130)
    plt.close(fig)

    # ---- oracle 3: revival spectra ----
    print("\n[oracle 3] revival spectra at Theta=pi/3, Tt in (0,4pi):")
    th0 = np.pi / 3.0
    Tgrid = np.linspace(0.02, 4 * np.pi, 1500)
    # damping relative to Tt: keep eps=0.01 (complex-time offset);
    # at large Tt the kernel is oscillatory but the sums converge
    # identically in l/k for fixed eps.
    Ks_t = np.array([sr.k_spec(th0, Tt, 800)[0] for Tt in Tgrid])
    Kp_t = np.array([sr.k_spec_spinor(th0, Tt, 800)[0] for Tt in Tgrid])
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    axes[0].plot(Tgrid, np.abs(Ks_t) ** 2, lw=0.7)
    axes[0].set_title("scalar |K_s|^2")
    axes[1].plot(Tgrid, np.abs(Kp_t) ** 2, lw=0.7, color="darkred")
    axes[1].set_title("spinor |K_sp|^2")
    for ax in axes:
        ax.set_xlabel("Tt")
        ax.axvline(np.pi / 2, color="k", lw=0.5, ls="--")
    fig.tight_layout()
    fig.savefig(f"{DIR}/spinor_revival.png", dpi=130)
    plt.close(fig)
    # interferometric contrast numbers
    for name, K in (("scalar", Ks_t), ("spinor", Kp_t)):
        I = np.abs(K) ** 2
        print(f"  {name}: max|K|^2={I.max():.4f} at Tt="
              f"{Tgrid[np.argmax(I)]:.4f}; |K|^2 at Tt=pi/2: "
              f"{np.interp(np.pi/2, Tgrid, I):.4f}; "
              f"mean {I.mean():.4f}")

    # fringe-shift check (claims audit): scalar vs spinor fringe
    # peak positions at the same Tt
    print("  fringe-shift check (|K|^2 peak positions, Theta-pi):")
    thf = np.pi + np.linspace(0.05, 1.0, 20000)
    for Tt in (0.1, 0.25):
        for name, fn in (("scalar", sr.k_spec),
                         ("spinor", sr.k_spec_spinor)):
            K = fn(thf, Tt, 800)
            Ii = np.abs(K) ** 2
            pk = np.where((Ii[1:-1] > Ii[:-2]) & (Ii[1:-1] > Ii[2:]))[0] + 1
            print(f"    Tt={Tt:5.2f} {name}: "
                  f"{np.round(thf[pk][:5] - np.pi, 4)}")

    # ---- oracle 4: cycloid-mapping audit (expected null) ----
    print("\n[oracle 4] cycloid-mapping audit:")
    print("  map: x = a(theta - sin theta), cusp/caustic x=2*pi*a at "
          "theta=2pi")
    print("  under Theta := x/a the cusp sits at Theta=2pi — trivially an")
    print("  S^3 conjugate point (shared 2pi periodicity, not dynamics).")
    print("  The S^3 ANTIPODE caustic (Theta=pi) maps to theta=pi, the")
    print("  cycloid's smooth arch bottom (x=pi*a) — NOT a caustic.")
    # quantitative: kernel fringe positions move with Tt; any
    # cycloid-mapped feature is Tt-invariant. Reuse fringe spacing:
    thf = np.pi + np.linspace(0.05, 1.0, 20000)
    for Tt in (0.1, 0.25):
        K = sr.k_spec(thf, Tt, 800)
        Ii = np.abs(K) ** 2
        pk = np.where((Ii[1:-1] > Ii[:-2]) & (Ii[1:-1] > Ii[2:]))[0] + 1
        if len(pk) > 1:
            print(f"  fringe peaks near antipode at Tt={Tt}: "
                  f"Theta-pi = {np.round(thf[pk][:4] - np.pi, 4)} "
                  f"(moves with Tt => dynamical, not cycloid-geometric)")

    # ---- determinism of the analyzer itself ----
    print("\n[det] analyzer deterministic: (verify by second run diff)")


if __name__ == "__main__":
    main()
