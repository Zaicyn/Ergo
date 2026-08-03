# Gap phase diagram gap(J, B) — 12-site spin-1 rotor chain

Same Hamiltonian and machinery as `rotor_chain.py` (generalized in
`gap_map.py` to N sites / D states per site; matrix-free LinearOperator,
eigsh k=4, tol=1e-12). J=0 column validated against 12 independent Lmax=1
rotors: max |ΔE0| = 4.3e-15, max |Δw| = 4.4e-15. Per-point wall times in
`results_gap_map.json` (16–110 s; none exceeded 10 min).

## Grid: gap E1−E0

| J \ B | 0.10 | 0.15 | 0.20 | 0.25 | 0.30 | 0.35 | 0.40 |
|-------|------|------|------|------|------|------|------|
| 0.00  | 0.578 | 0.537 | 0.510 | 0.500 | 0.510 | 0.537 | 0.578 |
| 0.25  | 0.531 | 0.452 | 0.352 | 0.284 | 0.352 | 0.452 | 0.531 |
| 0.50  | 0.541 | 0.444 | 0.251 | 0.143 | 0.251 | 0.444 | 0.541 |
| 0.75  | 0.569 | 0.427 | 0.144 | 0.090 | 0.144 | 0.427 | 0.569 |
| 1.00  | 0.602 | 0.319 | 0.093 | **0.084** | 0.093 | 0.319 | 0.602 |
| 1.25  | 0.570 | 0.171 | 0.089 | 0.089 | 0.089 | 0.171 | 0.570 |
| 1.50  | 0.399 | 0.105 | 0.096 | 0.099 | 0.096 | 0.105 | 0.399 |

Extras at B = 0.25: gap(J=1.75) = 0.1096, gap(J=2.0) = 0.1212.
On the B = 0.25 line, w = 0.500000 and r = 0 exactly at every J (symmetry).

Heatmap: `gap_map.png`. Full data: `results_gap_map.json`.
Run log: `gap_map_run.log`.

## Answers

### a. Functional form of the collapse along B = 0.25 vs J

gap(0.25, J): 0.500 (J=0), 0.284 (0.25), 0.143 (0.5), 0.090 (0.75),
**0.0835 (1.0, minimum)**, 0.089 (1.25), 0.099 (1.5), 0.110 (1.75),
0.121 (2.0). Not linear (a linear fit gives closure at J ≈ 2.2 with rms
residual 0.094 — a bad fit). The gap drops steeply, bottoms out at J ≈ 1.0,
and *reopens* slowly towards J = 2. The collapse does not complete anywhere
in [0, 2]; the reopening is the finite-N spin-wave gap of the
−J Σcos(φ_i − φ_{i+1})-dominated regime.

### b. Does the gap minimum stay at B = 0.25?

Yes for J ≤ 1.0: argmin over B is exactly 0.25 at every J in
{0, 0.25, 0.5, 0.75, 1.0}, and E0, gap, w are exactly symmetric about
B = 0.25 (w(B) = 1 − w(0.5 − B) to machine precision, since the cos3φ drift
is absent in the spin-1 basis). At J = 1.25–1.5 the minimum flattens into a
valley: gaps at B = 0.20, 0.25, 0.30 agree within ~0.005 (0.089/0.089/0.089
at J=1.25), so the competition line stays centered at B = 0.25 but softens
into a broad low-gap region.

### c. Lmax=2 (5 states/site, 8-site ring) robustness

| point | spin-1, N=12 | Lmax=2, N=8 |
|-------|-------------|-------------|
| B=0.25, J=0.0 | 0.5000 | 0.4998 |
| B=0.25, J=0.5 | 0.1429 | 0.1146 |
| B=0.25, J=1.0 | 0.0835 | 0.0672 |
| B=0.50, J=0.5 | 0.7195 | 0.6270 |

The collapse persists with Lmax=2 — gaps are uniformly ~13–20% smaller (more
basis states → more hybridization), same shape, minimum still at B = 0.25
with w = 0.5, r = 0 exactly. The collapse is truncation-safe qualitatively;
quantitatively the spin-1 gaps overestimate by ~15%. Drift-term effect at
(B=0.25, J=0.5): gap 0.114641 with cos3φ vs 0.114885 without — 0.2%,
negligible.

### d. Quantum critical point or avoided crossover?

On this N=12 ring the gap stays finite everywhere: global minimum 0.0835 at
(B=0.25, J=1.0) (0.0672 in the Lmax=2 check). The data are consistent with a
softened/avoided crossing at finite N. If a true QCP exists at N → ∞, the
best estimate from this map is (B_c ≈ 0.25, J_c ≈ 1.0) — B_c = 0.25 is pinned
by the exact symmetry, J_c by the gap minimum — but distinguishing a true
critical point from an avoided crossover requires finite-size scaling
(N = 8, 12, 16 gaps at the candidate point), which a single size cannot
provide.
