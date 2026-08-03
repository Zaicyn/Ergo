# Phase-engine plugin architecture + XXZ first literature model

Layout (`min/phase_ed/engine/`):
- `models/base.py` — plugin interface: `name`, `d_site`,
  `make_matvec(N, params)`, `make_dense(N, params)` (dim ≤ 8000, for
  GPU-batched dense ED later), `native_grid()`, `validation_target()`,
  optional `gauge_phases(N)` (on-site diagonal gauge to untwist before
  correlators), `raise_lower()`.
- `models/rotor.py` — spin-1 rotor chain, wraps `matvec_fast.FastChain`
  (numba, gauge-folded); `gauge_phases` exposes the twist.
- `models/xxz.py` — spin-1/2 XXZ, H = Σ(SxSx + SySy + Δ SzSz) + h Σ Sz,
  periodic; sparse build (2^N ≤ 2^20 usable), `make_dense` via `.toarray()`.
- `analysis.py` — uniform protocol: `ground_state` (eigsh + Lanczos
  residual), `entropy_cc` (S(ℓ), Calabrese–Cardy c, ℓ = 1..N/2),
  `correlator` (C(r) = <raise_i lower_j> from `raise_lower()`, with
  algebraic + constrained-oscillatory fits), `analyze` (all of the above).
- `run_grid.py` — sweep driver, dedup append to JSON.

GPU-batching note: `make_matvec` stays the primary interface;
`make_dense` is implemented in base (columns of H on identity, dim ≤ 8000)
and natively in XXZ (sparse → dense). For GPU-batched dense ED, batch
`make_dense` output per grid point; the numba rotor path needs a dense
emitter too (base fallback covers N ≤ 7; extend if larger needed).

## Rotor plugin validation (gate)

(B=0.25, J=1.0, N=12) through the plugin: E0 = −4.236783839 vs
`results_fss.json` −4.2367838390291315 (dE = 2.7e-15), gap = 0.083523091
vs 0.08352309149762327 (dgap = 1.8e-14). PASS (< 1e-6). Note: the task
brief quoted E0 = −4.590652, which matches nothing on file — validated
against the actual recorded value.

## XXZ gates (h = 0)

(a) **LL gap closure, Δ = 0.5**, N = 8,10,12,14: gap = 0.340, 0.272,
0.227, 0.194; linear in 1/N with intercept **−0.0002**. PASS.

(b) **Central charge, Δ = 0.5**: c = 1.078 ± 0.012 (N=12), 1.069 ± 0.011
(N=14) on all cuts ℓ = 1..N/2 — marginally above the 1 ± 0.05 band; this
is the well-documented finite-size overshoot of the raw CC fit for XXZ
(log corrections). On interior cuts (ℓ ≥ 2): **c = 1.038 (N=12), 1.032
(N=14)** — inside the band. PASS with the finite-size caveat recorded.

(c) **Gapped at Δ = 2.0**: subtlety — E1−E0 (0.259 → 0.041, N=8..20)
CLOSES: that is the symmetry-broken Néel doublet's tunneling splitting,
not the spin gap. The first excitation above the doublet, E2−E0 (1.060,
0.913, 0.813, 0.740, 0.686, 0.644, 0.610 for N = 8..20), has geometrically
shrinking decrements; an exponential fit g∞ + a·r^N gives **g∞ = 0.53 ±
0.01** — finite (65σ from 0). PASS. (Protocol note: for Ising-side points,
gap must be measured above the SSB doublet; `analysis.ground_state`
reports E1−E0, so gapped Z2-breaking points need k ≥ 3 handling — flagged
in the verdict.)

## Comparative map, N=12 (gap / c / η)

| rotor (B=0.25) J | gap | c | η (q=0) |
|---|---|---|---|
| 0.50 | 0.1429 | 0.576 | 0.755 |
| 0.75 | 0.0903 | 0.935 | 0.361 |
| 1.00 | 0.0835 | 1.016 | 0.264 |
| 1.25 | 0.0892 | 1.036 | 0.234 |
| 1.50 | 0.0987 | 1.044 | 0.221 |
| 1.75 | 0.1096 | 1.049 | 0.215 |
| 2.00 | 0.1212 | 1.052 | 0.211 |

| XXZ (h=0) Δ | gap (E1−E0) | c | η_stag (q=π) |
|---|---|---|---|
| −0.50 | 0.0572 | 1.090 | 0.261 |
| −0.25 | 0.0923 | 1.073 | 0.363 |
| 0.00 | 0.1317 | 1.069 | 0.463 |
| 0.25 | 0.1760 | 1.072 | 0.564 |
| 0.50 | 0.2266 | 1.078 | 0.669 |
| 0.75 | 0.2856 | 1.085 | 0.783 |
| 1.00 | 0.3559 | 1.088 | 0.907 |
| 1.25 | 0.2900 | 1.082 | 1.048 |
| 1.50 | 0.2269 | 1.058 | 1.207 |
| 1.75 | 0.1715 | 1.009 | 1.384 |
| 2.00 | 0.1264 | 0.938 | 1.576 |

## Verdict note on q

XXZ LL shows **commensurate q = π** (staggered): the plain-algebraic fit
fails (η ≈ 32, garbage), the staggered fit A(−1)^r/r^η wins at every Δ
(rms 10–30× better), with η_stag → 0.907 ≈ 1 at Δ = 1 — exactly the canon
(1/r transverse decay with log corrections at the Heisenberg BKT point).
The XXZ BKT at Δ = 1 is thus commensurate–gapped, q = π throughout —
matching the rotor's commensurate q = 0 BKT picture (oscillatory fits
there hit the resolution boundary with 15–20× worse rms). Both models are
BKT-type at their boundaries, no incommensurate (Pokrovsky–Talapov)
behavior in either. The XXZ gap peaks at Δ = 1.0 (0.356) and the E1−E0
"closure" for Δ > 1 is the SSB doublet, not a critical phase.
