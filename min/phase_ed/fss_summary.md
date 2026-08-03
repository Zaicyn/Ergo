# Finite-size scaling of the gap — competition line B=0.25

Machinery: `fss.py` (uses `gap_map.RotorChain`, spin-1, drift off — measured
0.2% effect), eigsh tol=1e-12 except where noted. Data: `results_fss.json`
(+ N=12, J=0.75/1.25 from `results_gap_map.json`; spin-1 drift is identically
zero so those values carry over). Plot: `fss_gap.png`.

Timing notes: N=14 (3^14 = 4.78M states) did NOT converge at tol=1e-12
within the 12-min point guard (k=4, then k=2/ncv=24 — both logged as
timeouts), which exhausted the 30-min budget before the cheap points ran;
those were recovered in `fss_followup.py`. N=14 succeeded at tol=1e-9,
k=2, ncv=24 in 1261 s (precision still ≪ 1e-4 on the gap; E0 cross-checks
against the trend to <1e-6). N=13 (3^13) converged at tol=1e-12 in 259 s.

## a. gap(N) tables

B = 0.25 (competition line):

| N | J=0.75 | J=1.0 | J=1.25 |
|---|--------|-------|--------|
| 8  | 0.119552 | 0.120548 | 0.132202 |
| 10 | 0.101848 | 0.098344 | 0.106399 |
| 12 | 0.090267 | 0.083523 | 0.089204 |
| 13 | —        | 0.077814 | —        |
| 14 | —        | 0.072916 | —        |

Control, B = 0.50, J = 0.5: N=8: 0.711043, N=10: 0.715961, N=12: 0.719545.

## b. N→∞ extrapolation at B=0.25

Linear fit gap = a/N + b (rms residuals ≤ 6e-5 for all three J — the 1/N
form fits well; 1/√N fits are visibly worse, rms 4–6e-4 and unphysical
negative intercepts):

| J | gap(N→∞), linear in 1/N | rms |
|-----|--------|--------|
| 0.75 | **+0.0316** | 6e-5 |
| 1.00 | **+0.0094** (quadratic: +0.0091) | 1e-5 |
| 1.25 | **+0.0032** | 4e-6 |

At J=1.0 the five-point sequence tracks gap ≈ 1/N remarkably closely
(1/N = 0.1250, 0.1000, 0.0833, 0.0769, 0.0714 vs measured 0.1205, 0.0983,
0.0835, 0.0778, 0.0729); the extrapolated infinite-N gap is +0.009, i.e.
consistent with zero within the curvature uncertainty (the residuals are
systematically curved, so the true intercept is plausibly even smaller).
J=1.25 also extrapolates to ≈0 but on only three sizes (N=8,10,12).
J=0.75 extrapolates to a clearly finite value, +0.032.

## c. Control

At (B=0.50, J=0.5) the gap does not scale down: 0.711 → 0.716 → 0.720 for
N = 8, 10, 12, extrapolating to **+0.736** (linear in 1/N; +0.757 with 1/√N).
The gap closure is specific to the competition line.

## d. Verdict

The data support a true quantum critical point at B_c = 0.25 with
gap ∝ 1/N at J = 1.0 — i.e. gap closure as N→∞ with dynamic exponent
z = 1 (linear-in-1/N beats 1/√N decisively). The extrapolated residual at
J=1.0 is +0.009, an order of magnitude below the smallest measured gap and
consistent with zero given the visible downward curvature of the residuals.
J_c is bracketed between 0.75 (finite extrapolated gap +0.032) and ~1.25
(extrapolates to +0.003 but on only 3 sizes); the best estimate is
J_c ≈ 1.0–1.25. What would settle it: N=13/14 runs at J=0.75 and J=1.25
(to test whether their intercepts survive bigger N), and N=16–18 at J=1.0 —
3^16 = 43M states is beyond this dense-eigsh approach; a DMRG/MPS
implementation is the practical next step. If the J=1.0 intercept is truly
zero, the remaining ambiguity is the width of the critical region, not its
existence.
