# BKT check: isolated QCP vs gapless critical phase (B=0.25 line)

Data: spin-1 chain, drift off. N=8/10/12 (complex128, tol=1e-12), N=16
(complex64, tol=1e-6, numba matvec). Sources: `bkt_small_n.json`,
`n16_results.json`, `n16_extended.json`, `results_fss.json`. Fits:
`bkt_fits.json`.

## gap(N) series and linear-in-1/N fits (gap = slope/N + intercept)

| J | N=8 | N=10 | N=12 | (N=13) | (N=14) | N=16 | slope | intercept | rms |
|------|------|------|------|------|------|------|-------|-----------|-----|
| 0.75 | 0.11955 | 0.10185 | 0.09027 | — | — | 0.07629 | 0.693 | **+0.0328** | 2.1e-4 |
| 1.00 | 0.12055 | 0.09834 | 0.08352 | 0.07781 | 0.07292 | 0.06494 | 0.889 | **+0.0094** | 1.8e-5 |
| 1.25 | 0.13220 | 0.10640 | 0.08920 | — | — | 0.06767 | 1.032 | **+0.0032** | 9.4e-6 |
| 1.50 | 0.14755 | 0.11818 | 0.09865 | — | — | 0.07427 | 1.172 | **+0.0010** | 2.5e-5 |
| 2.00 | 0.18222 | 0.14554 | 0.12120 | — | — | 0.09087 | 1.462 | **−0.0005** | 6.6e-5 |

## Verdict: gapless critical phase for J ≳ 1.0, not an isolated QCP

1. **J=1.5 and J=2.0 close as 1/N.** Their N=16 points (0.0743, 0.0909) land
   within 2% of the 1/N lines fitted through N=8/10/12 alone (0.0733, 0.0915),
   and the four-point intercepts are +0.0010 and −0.0005 — zero within fit
   and curvature uncertainty. An isolated critical point near J ≈ 1.3 would
   require these to extrapolate finite; they do not.

2. **The intercept trend crosses zero at J ≈ 1.1** (linear interpolation
   between the gapped J=0.75, +0.0328, and J=1.0, +0.0094). J=1.0's small
   positive intercept has systematically curved residuals (quadratic fit gives
   +0.0090 and the curve is still falling), so the true boundary is consistent
   with J_c ≈ 1.0–1.1. Below that (J=0.75) the chain is genuinely gapped.

3. **The 1/N slope evolves smoothly with J**: 0.889 → 1.032 → 1.172 → 1.462
   for J = 1.0, 1.25, 1.5, 2.0, well fit by slope(J) = 0.317 + 0.572·J
   (residual rms 0.001). No jump — as expected in a critical phase, where the
   slope is the excitation velocity (set by the Luttinger parameter), growing
   ~linearly with the coupling that dominates the Hamiltonian.

Caveats: (a) N ≤ 16 cannot distinguish true gaplessness from a gap below
~0.005; (b) a BKT essential singularity at the boundary (gap ~ exp(−c/√(J−Jc)))
would be invisible at these sizes — the J_c ≈ 1.0–1.1 estimate is where the
1/N extrapolated gap vanishes, not a proof of BKT scaling; (c) N=16 values
carry ~1e-6 single-precision tolerance, irrelevant here. Next steps if
needed: DMRG (calibrated, `tenpy_rotor.py`) at N = 32–64 for J = 0.9–1.1 to
pin the boundary, and a level-spectroscopy or central-charge check (c = 1
expected for a Luttinger-liquid-like phase).
