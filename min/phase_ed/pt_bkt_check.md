# PT vs BKT: correlation wave vector q on the competition line

C(r) = <e^{i(φ_i − φ_{i+r})}>, B = 0.25, spin-1 chain. ED vectors
(twisted gauge rotated back with U†, verified entanglement-invariant
earlier; the gauge phase cancels in this diagonal correlator up to the
removable e^{-i2πr/N} twist, which we remove exactly), DMRG checkpoints
(MPS `correlation_function('Tm','Tp')`). Data: `results_correlator.json`;
plot: `correlator_C.png`.

## q(J) table — oscillatory fit A·cos(qr+δ)/r^η vs algebraic A/r^η

q_min = π/r_max is the smallest resolvable wave vector (one oscillation over
the fit range). "boundary" means the fit slammed into the q ≥ q_min bound.

| src | N | J | η (alg) | rms_alg | q (osc) | rms_osc | monotone? sign changes? |
|-----|---|---|---------|---------|---------|---------|--------------------------|
| ED | 12 | 0.5 | 0.76 | 5.7e-3 | 0.52 = q_min | 5.1e-2 | yes, 0 |
| ED | 12 | 1.0 | 0.26 | 8.0e-3 | boundary | 1.5e-1 | yes, 0 |
| ED | 12 | 1.5 | 0.22 | 8.4e-3 | boundary | 1.6e-1 | yes, 0 |
| ED | 12 | 2.0 | 0.21 | 8.5e-3 | boundary | 1.7e-1 | yes, 0 |
| ED | 16 | 0.5 | 0.89 | 1.1e-2 | boundary | 2.8e-2 | yes, 0 |
| ED | 16 | 0.75 | 0.41 | 5.3e-3 | boundary | 1.0e-1 | yes, 0 |
| ED | 16 | 1.0 | 0.28 | 7.4e-3 | boundary | 1.4e-1 | yes, 0 |
| ED | 16 | 1.25 | 0.25 | 8.0e-3 | boundary | 1.5e-1 | yes, 0 |
| ED | 16 | 1.5 | 0.23 | 8.2e-3 | boundary | 1.6e-1 | yes, 0 |
| ED | 16 | 2.0 | 0.22 | 8.3e-3 | boundary | 1.6e-1 | yes, 0 |
| DMRG | 18 | 0.5 | 0.93 | 1.4e-2 | boundary | 2.0e-2 | yes, 0 |
| DMRG | 18 | 1.5 | 0.23 | 8.0e-3 | boundary | 1.5e-1 | yes, 0 |
| DMRG | 24 | 0.5 | 1.02 | 1.8e-2 | boundary | 7.4e-3 | yes, 0 |
| DMRG | 24 | 1.5 | 0.24 | 7.6e-3 | boundary | 1.4e-1 | yes, 0 |
| DMRG | 32 | 0.5 | 1.07 | 2.0e-2 | boundary | 2.9e-3 | yes, 0 |
| DMRG | 32 | 1.5 | 0.25 | 7.2e-3 | boundary | 1.3e-1 | yes, 0 |
| DMRG | 48 | 0.5 | 1.12 | 1.9e-2 | 0.19 (sub-resolution) | 2.8e-3 | yes, 0 |
| DMRG | 48 | 1.5 | 0.25 | 6.6e-3 | boundary | 1.2e-1 | yes, 0 |

Key facts: (i) at **every** critical-phase point the oscillatory fit hits
the q_min boundary and its rms is 15–20× WORSE than the plain algebraic fit;
(ii) C(r) is strictly positive and monotone at all J and N, zero sign
changes; (iii) η ≈ 0.21–0.25 in the critical phase (slowly varying with J,
as a Luttinger parameter should), vs η ≈ 0.8–1.1 in the gapped control
(where the decay is really exponential — the algebraic form is just a
parametrization).

## Verdict: BKT, not Pokrovsky–Talapov

PT physics (chiral/3-fold perturbation of the quantum phase model) requires
an incommensurate correlation wave vector q(J) that drifts with coupling
and locks at the boundary. The data show q = 0 (commensurate) at every
measured point from J = 0.5 through J = 2.0 and N = 12 through N = 48:
no oscillation, no zero crossing, no J-dependence of q anywhere — and the
algebraic decay form wins decisively. This is exactly the BKT scenario: on
the competition line in the spin-1 basis the model is the pure quantum
phase model (first harmonic cancels; cos3φ has no matrix elements), whose
commensurate-incommensurate transition is Kosterlitz–Thouless, consistent
with the c ≈ 1 critical phase and z = 1 found earlier.

## Lmax=2 spot check (drift term reappears)

8-site Lmax=2 chain at (B=0.25, J=1.5), with and without the cos3φ drift:
E0 shifts by only 1.7e-3 and C(r) by ≤ 4e-4 — no oscillation appears
(C: 0.7197, 0.6525, 0.6247, 0.6167 with drift vs 0.7198, 0.6528, 0.6251,
0.6171 without — monotone both). The drift amplitude (K_DRIFT/3 = 0.033)
is too weak to imprint q = 2π/3 structure at this size. Caveat: at Lmax=2
the drift term is present in principle, so a PT channel formally opens;
at the physical parameter values its effect is negligible here.

## Caveats

- q resolution is 2π/N; an incommensuration smaller than ~0.13 rad/site
  (N=48) is invisible. Nothing in the data hints at one.
- The N=48 J=0.5 "q = 0.19" osc fit beats algebraic on rms but is a
  curvature-fit artifact on a short monotone exponential series — no sign
  change, no physical oscillation; flagged for completeness.
- N=16 J=0.75/1.25 vectors recomputed for this analysis
  (E0 = −3.590480/−7.749228, matching n16_results within c64 tolerance).
