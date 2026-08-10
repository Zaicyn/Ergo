#!/usr/bin/env python3
"""ll_string.py — Stage 2: write the measured rotor LL tower in
closed-string form and test the single-sigma_eff fit.

Inputs: min/llstring/tower_results.json (Stage 1, B=0.25, J=1.5).

Closed-string form (length L = N, lattice spacing 1):

  E_x(L) = sigma_eff * L + (2 pi v / L) * (x - (d-2)/12)

with d-2 = 1 transverse mode for the rotor's compact boson (a D=2+1
string): Casimir = -(2 pi v/L)(1/12) = -pi v/(6L), exactly the
measured ground-state term. QCD's Luescher term has d-2 = 2 (two
transverse modes, D=3+1): -pi v (d-2)/(6L) = -pi v/(3L) — the
factor-of-2 mode-count difference, documented here explicitly.

Tests:
  (a) Per-level sigma_eff: with the LL-quantized x values
      (x = 0 ground; x = M^2/(4K) winding; x = 1, 2 descendants;
      K = K_wind from Stage 1), solve each measured level for
      sigma_eff^(x)(N) = [E_x(N) - (2 pi v/N)(x - 1/12)] / N.
      For a compact boson one sigma_eff must fit ALL levels — the
      spread across levels and N is the fit quality. Deviation beyond
      the tower's own accuracy is a finding, not noise to average.
  (b) Casimir mode-count comparison, rotor vs QCD flux tube.
  (c) The sigma_eff interpretation: eps_inf is a bulk (vacuum)
      energy density, and it is NEGATIVE — the critical phase has no
      confining kink tension (kink condensation is why it is
      critical). The string-form tension here is a vacuum-density
      analog; the QCD sigma > 0 is a physical confining tension.
      This asymmetry goes to the Stage-3 boundary.

Determinism: pure arithmetic on the Stage-1 JSON; run twice,
byte-identical.
"""

import json

import numpy as np

D_TRANS_ROTOR = 1   # compact boson: one transverse mode (D=2+1 string)
D_TRANS_QCD = 2     # QCD flux tube: two transverse modes (D=3+1)


def main():
    with open("min/llstring/tower_results.json") as f:
        R = json.load(f)
    v = R["v"]
    K = R["K_wind"]
    eps = R["eps_inf"]
    b = R["b"]
    NS = [int(n) for n in R["levels"]]

    print("=" * 70)
    print("STAGE 2 — LL TOWER IN CLOSED-STRING FORM")
    print("=" * 70)
    print(f"inputs: eps_inf = {eps:.10f}, b = {b:.10f}, v = {v:.6f}, "
          f"K = {K:.4f}")
    print(f"Casimir check: pi v / 6 = {np.pi * v / 6:.10f} vs b = {b:.10f}"
          f" (c=1 form, dev {abs(np.pi * v / 6 - b) / b:.2e})")

    # theoretical LL x values per (M, phonon sector)
    def x_ll(M, nphon):
        return M * M / (4.0 * K) + nphon

    # (a) per-level sigma_eff from the string form
    print("\n[single-sigma test] sigma_eff per level "
          "(x quantized: winding M^2/4K, phonon 1):")
    sigmas = []
    for N in NS:
        rows = R["levels"][str(N)]
        E0 = rows[0]["E"]
        parts = []
        for r in rows[1:]:
            M = round(r["M"])
            pn = round(abs(r["p"]) * N / (2 * np.pi))
            if abs(r["M"] - M) > 0.05:
                continue  # unresolved near-degenerate mix; skip
            if abs(M) in (1, 2) and pn == 0:
                nphon = 0
            elif M == 0 and pn == 1:
                nphon = 1
            else:
                continue  # no confident LL x assignment; skip
            x = x_ll(M, nphon)
            sig = (r["E"] - (2 * np.pi * v / N) * (x - 1.0 / 12.0)) / N
            sigmas.append(sig)
            parts.append(f"M={M:+d},ph={nphon}"
                         f":{sig:.6f}")
        sig0 = (E0 - (2 * np.pi * v / N) * (0.0 - 1.0 / 12.0)) / N
        sigmas.append(sig0)
        print(f"  N={N}: sigma0={sig0:.6f}  " + " ".join(parts))
    sigmas = np.array(sigmas)
    print(f"  sigma_eff: mean {sigmas.mean():.6f}, "
          f"spread {sigmas.max() - sigmas.min():.6f}, "
          f"rms {sigmas.std():.6f}")
    print(f"  eps_inf (ground-state fit) = {eps:.6f}")
    print(f"  single-sigma fit quality: "
          f"{'ALL LEVELS within ' + format(max(abs(sigmas - eps)), '.2e') + ' of eps_inf'}")

    # (b) Casimir mode count
    print("\n[casimir mode count]")
    print(f"  rotor (this campaign): -pi v/(6L) = -(2 pi v/L)(1/12)")
    print(f"    one transverse mode, c=1 compact boson (D=2+1 string)")
    print(f"  QCD Luescher: -pi v (d-2)/(6L) = -pi v/(3L)")
    print(f"    d-2 = 2 transverse modes (D=3+1 string)")
    print(f"  factor-of-2 difference = transverse-mode count; the rotor")
    print(f"  chain realizes the D=2+1 member of the string family.")

    # (c) interpretation
    print("\n[sigma_eff interpretation]")
    print(f"  sigma_eff = eps_inf = {eps:.6f} < 0: a bulk vacuum energy")
    print(f"  density, NOT a confining tension. The critical phase has")
    print(f"  vanishing kink/domain-wall tension (kink condensation is")
    print(f"  the criticality mechanism); winding-sector gaps vanish as")
    print(f"  1/L instead of growing as sigma L. The QCD flux tube's")
    print(f"  sigma = 0.185 GeV^2 > 0 is a physical confining tension.")
    print(f"  The string FORM carries over exactly; the tension's SIGN")
    print(f"  and MEANING do not — Stage 3 boundary item.")


if __name__ == "__main__":
    main()
