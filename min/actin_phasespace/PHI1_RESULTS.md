# φ1 — Phase-space rung 1: nucleation / first-passage (single filament, M4a config)

Question: does the quantum-ladder logic (exact analytic oracle → certified
numerical instrument → phenomenon) scale to stochastic scaffold kinetics?
Answer: **yes, and it immediately paid for itself** — the rung produced one
erratum to a certified M4a result, one assay-artifact explanation, and one
precisely localized falsification that defines the missing phase-space
coordinate.

Single thread, oracle/experiment lock-step (per user directive — the rungs
are sequential: nucleation → treadmilling → steady state).

## The oracle

Birth-death chain on filament length n ∈ {3..60}, reflecting floor at the
trimer seed (unbind blocked at MLEN=3):

- birth b(n) = κ·(N−n)/V per step, κ = 1.73e-2 /step/conc (M4a isolated
  calibration), V = 1728
- death d(n) = k_off per step; nominal draw 4.5e-4/step
- **d_eff = 4.5e-4·(1 − P_fast)** with P_fast a *measured* input (see below) —
  this breaks the circularity of the M4a "0.8× nominal" fudge, which had been
  implied from the plateau it was then used to explain.

Exact outputs: stationary distribution, MFPT (sum formula), full
first-passage survival curves (DTMC eigendecomposition), gambler's-ruin
dissolution probabilities, and a DTMC simulator that runs the chain through
the *same observation protocol* as the engine (NDIAG=500 sampling, same
windows) — the protocol-matching turned out to be load-bearing.

## The experiment

`actin_fpt.ergo` — certified M4a engine (physics untouched, verified:
75k–150k window mean 20.10 vs cert 20.14, instrumentation is counters +
writes only) plus:
- first-passage step records FPT10/15/20
- return-capture identity tracking: LASTREL monomer id + release step;
  same-id rebinds counted at ≤1k / ≤5k / ≤20k lag, and split by length at
  release (n < 25 vs ≥ 25)

Ensemble: **64 seeds × 300k steps** (stride 7919 from 77031), ~2 min/run.

## Results

**R0. Return capture, measured.** P_fast(≤1k) = 0.364 ± 0.005;
+0.04 more by 5k; ~0 more by 20k. Two-timescale structure: a released
monomer either wanders back inside RCAP within ~1k steps or never returns.
→ d_eff = 2.86e-4/step.

**R1. Zeroth gate (the erratum).** Chain stationary mean at the *old*
plateau-implied d_eff=3.7e-4: **23.06** vs M4a certified plateau
**23.04 ± 1.43**. Perfect — and thereby exposes the problem: with the
*measured* d_eff=2.86e-4 the chain says the true fixed point is ~32, and
the 64×300k ensemble confirms the system creeps straight through 23
(trajectory at 150k ≈ 21, at 300k ≈ 36). **The M4a "steady state 23" was
slow transit past the stall region, not stationarity.** τ_corr ≈ 1/(κ/V)
≈ 100k steps means 150k runs never equilibrate. ACTIN_SPEC.md §"Phenomenon
cert" should be read with this erratum.

**R2. Nucleation burst = assay artifact, explained.** Engine FPT10 median
3.0k vs chain 24k. Cause: INIT_DYN rejection-samples the gas into the
central [2,10]³ sub-volume — initial local concentration 57/512 = 3.4× the
mean-field value; diffusion mixing time τ ≈ L²/(π²D) ≈ 14k steps. A
time-inhomogeneous chain (c(t) = c∞ + Δc·e^(−t/τ)) absorbs the burst
qualitatively; residual overcorrection (boundary-layer depletion around the
tip) noted, not pursued — φ1 gates are placed post-mixing.

**R3. Post-mixing passage gates — PASS.** Conditional passages (clock starts
at first hit of the lower rung, mixing-complete):

| segment | chain mean | chain median | engine mean | engine median |
|---|---|---|---|---|
| 10→15 | 23.6k | 18.0k | 17.5k ± 3.0k | 14.5k |
| 15→20 | 30.2k | 22.5k | 28.1k ± 4.1k | 18.1k |

15→20 agrees to 0.5σ on means (medians 22.5k vs 18.1k, right-skew
consistent with chain cdf). 10→15 is ~2σ fast — residual mixing-tail
contamination, expected and documented.

**R4. Fluctuation gate — PASS, via protocol matching (pitfall!).** Raw
within-run sd (t>175k): engine 2.87 vs chain stationary sd 5.26 — an
apparent sub-Poissonian "antibunching" signature (Fano 0.24 vs 0.86).
**Spurious**: at τ_corr ≈ 100k, a 125k window samples ~1 correlation time
and the variance estimate is strongly biased down. Chain simulated through
the identical protocol: within-run sd 3.00, across-seed sd of means 3.38 —
engine: 2.87 / 3.51. **PASS.** Lesson recorded: in the near-critical regime
(restoring rate ~1e-5/step), always compare observables through the same
window, never stationary- analytic vs windowed-empirical.

**R5. The falsification — and the missing coordinate.** Protocol-matched
plateau means: chain-sim 28.7 vs engine 34.3 (+5.6, real). Current-profile
analysis j(n) = binds−unbinds per interval, binned by length and epoch
(pitfall: one mislabeled index — `b[1]` for `b_[1]` — halved the length
coordinate and fabricated a two-branch "hysteresis"; caught by a per-file
count cross-check. Always audit a pooled histogram against one raw file.):

- death side: d_eng ≈ 4.3–4.5e-4 = nominal, flat in n ✓; P_return split by
  length at release: 0.360 (n≥25) vs 0.331 (n<25), 1.3σ — **coil-caging of
  released monomers falsified** as the residual mechanism.
- birth side: **b_eng / κ·c = 1.7–1.9×, flat in n across the whole plateau
  (n=23→42)** — but the 15→20 gate (t ≈ 20–70k) matched κ·c exactly.
  → the enhancement is **time-developing**, switching on between ~70k and
  ~150k steps, exactly when contour n·0.6 exceeds LBOX=12 and the filament
  coils. The coil concentrates the G-actin gas locally around the tip.

**The 1D length chain is certified Markovian in the straight-filament regime
(n ≲ 20, contour < LBOX) and falsified beyond it by a measured 1.7–1.9×
birth enhancement. The second phase-space coordinate is conformation
(ee/contour), entering through the birth rate.** This is the φ2/φ3 design
input.

## φ1 gate summary

| gate | oracle | engine | verdict |
|---|---|---|---|
| stationary mean (d_eff implied, R1) | 23.06 | 23.04 ± 1.43 | trivially pass → exposed as circular |
| 15→20 passage mean | 30.2k | 28.1k ± 4.1k | **PASS** (0.5σ) |
| within-run plateau sd (protocol-matched) | 3.00 | 2.87 | **PASS** |
| across-seed mean spread (protocol-matched) | 3.38 | 3.51 | **PASS** |
| plateau mean (protocol-matched) | 28.7 | 34.3 | **FAIL → localized: birth-side, coil onset** |
| P_fast length-dependence | (hypothesis test) | 1.3σ null | coil-caging on release falsified |

## Files

- `bd_oracle.py` — exact oracle (stationary / MFPT / FPT survival / ruin /
  protocol-matched simulator)
- `actin_fpt.ergo` — instrumented assay (M4a physics + FPT/RET counters)
- `runs/fpt_*.log` — 64 × 300k-step ensemble

## φ2 hand-off

1. Add the pointed end (M4b params: KONP=1.0, KOFFB=0.066, KOFFP=0.10,
   releases 1.65/2.5). Oracle becomes a two-end chain: length stationary
   distribution + ratchet velocity T (net pointed flux), both exact.
2. Conformation coordinate must be instrumented from the start (ee/contour
   per DIAG, bin j(n) by coil state) — the φ1 R5 residual is the target.
3. Keep gates post-mixing; FPT clock starts at first-hit of the lower rung.
