# Central charge from entanglement entropy — universality check

Ground states at B=0.25 (competition line), spin-1 chain, drift off.
N=12: complex128, tol=1e-12. N=16: complex64, k=2, ncv=8, tol=1e-6.
Data: `results_entanglement.json`; eigenvectors: `psi_N{N}_J{J}.npy`;
plot: `entanglement_S.png`. Script: `entanglement.py`.

## Quality flags (Lanczos residual ||Hv − Ev||, flag > 1e-5)

| J | N=12 residual | N=16 residual | flag |
|-----|------|------|------|
| 0.5 | 4.7e-15 | 2.9e-06 | both OK |
| 1.0 | 2.9e-13 | 2.0e-05 | N=16 flagged |
| 1.5 | 2.2e-13 | 5.8e-05 | N=16 flagged |
| 2.0 | 2.4e-14 | 4.9e-05 | N=16 flagged |

The three flagged N=16 points are single-precision artifacts (tol=1e-6 with
|E0| ~ 5–14 sets the residual scale). Cross-checks: their gaps agree with
independent runs (n16_results/n16_extended) to ≤ 9e-6, and the entropy
profiles are smooth with small CC-fit rms — usable, but noted.

## Gauge check (mandatory)

max |ΔS(ℓ)| between the twisted-gauge ground state and its U†-rotated
image at N=12: **1.1e-15** — on-site diagonal unitary leaves entanglement
invariant exactly, as expected. N=16 entropies in the twisted gauge are
therefore the physical ones.

## Calabrese–Cardy fits: S(ℓ) = (c/3) log[(N/π) sin(πℓ/N)] + const

| J | c (N=12) | fit rms | c (N=16) | fit rms |
|-----|------|------|------|------|
| 0.5 (gapped) | 0.58 ± 0.03 | 1.1e-2 | 0.48 ± 0.04 | 1.7e-2 |
| 1.0 | 1.016 ± 0.009 | 2.9e-3 | 1.004 ± 0.008 | 3.3e-3 |
| 1.5 | 1.044 ± 0.010 | 3.3e-3 | 1.034 ± 0.008 | 3.6e-3 |
| 2.0 | 1.052 ± 0.012 | 3.8e-3 | 1.040 ± 0.009 | 4.1e-3 |

## Verdict

- **Critical region is c ≈ 1.** All six (J, N) fits at J = 1.0, 1.5, 2.0
  give c between 1.00 and 1.05, within 1–5 σ of 1 and within ~5% of it
  pointwise. Consistent with a Luttinger-liquid-type (Gaussian, c=1)
  critical phase — matching the earlier z=1, gap ∝ 1/N finding and its
  smoothly varying velocity (the 1/N slope).
- **Gapped control is area-law.** At J=0.5, S(ℓ) plateaus (S saturates at
  ≈ 0.86 for both N=12 and N=16 — no growth with N) and the log fit is
  poor (rms 3–5× larger than any critical fit, and the "c" drifts down
  0.58 → 0.48 from N=12 to N=16 — exactly how a plateau misbehaves under
  a log fit). Clean contrast.
- **Honest limitations:** 6–8 cuts per fit, two sizes, no subleading
  corrections modeled; the c values are estimates at the ±0.02–0.05 level,
  not precision measurements. The N=16 single-precision residuals are
  flagged above. A DMRG run at N = 32–64 (calibrated machinery ready)
  would tighten c to the ±0.01 level if needed.
