# M4H — ATP hydrolysis + nucleotide-state-dependent kinetics (barbed-end only)

Mechanism: every monomer carries NUC ∈ {ATP, ADP}. Free pool is ATP (instant
exchange); binding sets NUC=ATP; each bound ATP monomer hydrolyzes with
P = KHYD·DT per step; the terminal barbed monomer unbinds at KOFF_T (ATP,
slow) or KOFF_A (ADP, fast). Pointed machinery stripped (M4a barbed kinetics
unchanged: KON=500 saturated, release at RCAP+0.25=1.65, MLEN>3 floor).
Filament: barbed-end-only, anchored trimer nucleus, N=60 pool, box 12.

## Final parameters

| param | value | note |
|---|---|---|
| KHYD | 0.03 | P = 1.5e-4/step/bound ATP monomer (τ_hyd ≈ 6.7k steps) |
| KOFF_T | 0.045 | 2.25e-4/step, ATP terminal (½ of M4a KOFF) |
| KOFF_A | 0.18 | 9.0e-4/step, ADP terminal (2× M4a KOFF) → nominal contrast 4× |
| pool N | 60 | unchanged from M4a |
| control | KHYD=0, KOFF_T=KOFF_A=0.082 | state-independent; tuned so its dynamic koff_eff matches the hydro build's measured koff_eff → matched mean length |

Tried and rejected: KOFF_A=0.20 (contrast 4.4×): slower equilibration
transient (still climbing at 150k), no better plateau centering. The M4b-WIP
inherited regime (KOFF_T=0.015/KOFF_A=0.03/KHYD=0.2 + pointed) overgrows to
len≈49 — sum of off-rates far below kon·c0, as the briefing's arithmetic
predicts.

Finite-pool arithmetic: measured dynamic koff_eff ≈ 4.2–4.5e-4/step <
kon·c0 ≈ 5.7e-4/step ✓ (no collapse), and above KOFF_T·DT=2.25e-4 alone
(state mixing does the work) ✓.

## Oracle ladder

1. **FD** — forces untouched by the NUC layer; re-run proves no regression:
   max rel error **1.602e-09** (M4a: 1.60e-9), config exercises WCA + intra +
   ladder + anchor + walls. PASS (≤1e-8).
2. **Static byte cert** — M4a cert config (hexamer arc + 10 spiral + close
   pair) plus NUC pattern (bound hexamer carries ADP at monomers 2,4;
   engine MIRROR=1 variant dumps CFG/FRC/NUC/CERT rows):
   CFG max abs diff **1.11e-15**, FRC **4.35e-14** (= M4a's), NUC rows
   byte-identical, CERT energies agree ≤1e-15. PASS (≤1e-11).
3. **Rate calibration** (mirror, isolation legs):

   | rate | measured | nominal | ratio | events |
   |---|---|---|---|---|
   | koff, terminal forced ATP | 2.413e-4 ± 1.4e-5 | 2.25e-4 | 1.073 raw / **≈0.98 corrected** | 289 |
   | koff, terminal forced ADP | 9.762e-4 ± 4.5e-5 | 9.0e-4 | 1.085 raw / **≈0.99 corrected** | 480 |
   | k_hyd | 1.505e-4 ± 8.8e-6 | 1.50e-4 | **1.003** | 294 |
   | kon slope | 2.59e-2 /step/conc | (M4a: 1.73e-2) | park-limited, noisy | 52 binds |

   Correction: the koff legs are decay-to-floor assays — each epoch stops
   after n≈7–12 events, and for a Poisson process E[n/T_n] = p·n/(n−1)
   (T_n ~ Gamma(n,p)), a built-in +7–9% upward estimator bias. Dividing it
   out gives 0.98 / 0.99. The fixed-horizon khyd leg (no stopping bias)
   lands at 1.003, confirming the diagnosis. All within the 10% gate.

   Mean-field (self-consistent: gross on-rate v = kon_slope·c, terminal ATP
   prob p = v/(v+h) since terminal age ~ Exp(v), koff_eff(v) = p·koffT +
   (1−p)·koffA, steady v = koff_eff(v)): **L* = 32.9, p(ATP term) = 0.731,
   cap = v/h = 2.71 monomers** (nominal rates). Observed second-half lmean
   32.5 (engine) / 32.2 (mirror) — the nominal-rates MF lands on the
   plateau; the M4a 0.8× return-capture correction (which would give
   L* = 37.1) does NOT apply here: with the present kon slope calibration
   (2.59e-2 vs M4a's noisy 1.73e-2) the return-capture effect is absorbed
   in the on-rate.

4. **Phenomenon cert** — 300k-step runs (2× the 150k mandate), seeds
   77031/123457/888811, engine + mirror, hydro + matched control;
   statistics over second half (150k steps, 300 diag samples).

## Phenomenon 1: ATP cap profile

ATP fraction vs depth from barbed tip (0 = terminal), pooled over all 6
engine+mirror hydro runs (seeds 77031/123457/888811):

| depth | pooled ATP frac | sem |
|---|---|---|
| 0 | 0.731 | 0.023 |
| 1 | 0.441 | 0.040 |
| 2 | 0.269 | 0.032 |
| 3 | 0.128 | 0.029 |
| 4 | 0.058 | 0.010 |
| 5 | 0.030 | 0.016 |

Exponential e-folding **λ ≈ 2.0 monomers** (depths 0–2); mean ATP count
**natp = 1.6–1.8** (engine 1.59±0.11, mirror 1.80±0.21). The cap lives in
the target 1–3 monomer regime and tracks growth: P(ATP terminal) measured
0.728 pooled vs mean-field turnover prediction v/(v+h) = 0.73 ✓ — the
classic actin aging signature: tip young/ATP, bulk old/ADP.

Mean-field cap ≈ kon·c/KHYD = v/h predicts **2.7** vs measured **1.5** —
the steady-growth estimate overstates by ~1.8×. Mechanism: at stochastic
steady state the tip alternates growth/shrinkage; every unbind exposes a
pre-aged (usually ADP) monomer as the new terminal, erasing the cap from
the tip — the cap is set by *turnover* episodes, not just monotonic burial.
Second refinement: turnover-based p(ATP term) matches (above), so the
mismatch is in the depth profile tail, not the tip state.

## Phenomenon 2: state-dependent dynamics

**koff_eff decomposition** (pooled over all 6 engine+mirror hydro runs,
900k eligible steps): P(ATP term) = 0.728 → mixture prediction
koff_eff = P(ATP)·KOFF_T·DT + P(ADP)·KOFF_A·DT = 4.09e-4;
measured koff_eff = 4.13e-4 → **ratio 1.011** ✓. The dynamics on both sides
are exactly the nucleotide-mixture kinetics they were built with.
Per-state dynamic rates pooled: r_atp = 2.58e-4 (nominal 2.25e-4, 1.15×),
r_adp = 8.29e-4 (nominal 9.0e-4, 0.92×) → measured dynamic contrast
**3.2×** (nominal 4×; deviations are the documented return-capture/park
physics, identical in kind to M4a's 0.8×, slightly state-asymmetric).

**Catastrophe-ish signature** (500-step length increments, second half,
6 hydro vs 6 control runs):

| metric | hydro | control |
|---|---|---|
| mean skew of ΔL | −0.29 ± 0.34 | +0.41 ± 0.18 |
| deepest drop (avg) | −3.3 (−2,−4,−5,−4,−2,−2) | −2.0 (−2,−3,−2,−2,−1,−2) |
| runs with drops ≤ −3 / 500 steps | 4 of 6 | 1 of 6 |

Hydrolysis tilts the increment distribution toward intermittent fast
multi-monomer shrinkage (negative skew, deep drops) — the aging/catastrophe
phenomenology; the skew contrast is suggestive (~1.8σ) at n=6 runs, the
deep-drop frequency clearer (4/6 vs 1/6). Meanwhile the young-ATP-cap
feedback is homeostatic on the mean: at matched mean length, hydro lvar
(9.3±2.5 engine / 11.0±6.4 mirror) is statistically indistinguishable from
the control's (12.4±6.0 / 7.1±2.8) — length variance is dominated by the
near-critical park-limited noise on both sides; the state dependence shows
up in the *shape* of the increments, not the variance magnitude.

## Engine/mirror agreement (second-half means, 300k-step runs)

Hydro build:

| seed | engine lmean | mirror lmean | engine natp | mirror natp |
|---|---|---|---|---|
| 77031 | 31.68 | 28.82 | 1.56 | 1.80 |
| 123457 | 29.43 | 36.98 | 1.41 | 1.43 |
| 888811 | 36.50 | 30.88 | 1.80 | 1.97 |
| mean ± sem | **32.54 ± 2.09** | **32.22 ± 2.45** | **1.59 ± 0.11** | **1.80 ± 0.21** |

→ lmean agreement **0.10σ** (PASS, ≤2σ); natp agreement 0.9σ ✓.
Cap profiles per run agree depth-by-depth within correlated-sample noise.

Matched control (auxiliary, KHYD=0, KOFF=0.082): engine 30.63±1.23 vs
mirror 27.33±1.11 → 1.99σ (inside 2σ); hydro-vs-control mean length matched
within 0.8σ (engine) / 1.8σ (mirror) ✓.

kT: engine 0.49–0.50, mirror 0.40 (nominal 0.4; M4a documented engine range
0.36–0.50 — teleport-register kicks warm the engine side identically).
fmax modest (~50–70 ≪ FCAP=500), no coiling (ee/contour ≈ 0.25–0.3), nout=0.

## Failure modes found and fixed

- Inherited WIP regime overgrowth (len≈49) → re-derived off-rate arithmetic.
- Calibration decay assays run out of events at the MLEN=3 floor →
  epoch-based restarts; surviving +7–9% estimator bias identified as the
  Gamma stopping-time effect E[n/T_n]=p·n/(n−1), corrected above.
- 150k-step runs do NOT equilibrate from a trimer start (mean-field
  relaxation τ ≈ V/kon_slope ≈ 70–100k steps; near-critical drift is slow):
  first 150k legs still climbing. Final protocol: 300k steps, second-half
  statistics. Both sides share the protocol, so comparison stays apples-to-apples.
- pkill -f with a pattern matching the shell's own cmdline kills your shell —
  kill PIDs, not patterns.

## What I'd do differently

- Start dynamic runs from a pre-grown ~20-mer instead of the trimer to buy
  100k steps of equilibration; the τ≈100k relaxation makes 150k-step certs
  marginal for near-critical plateaus (this bit M4a too: engine 20–26 vs
  ODE 15.4 is mostly transient + return capture).
- Put SEED/NSTEPS/params in a runtime config instead of recompiling per
  seed; compile-per-seed works but clutters the run bookkeeping.
- The cap-profile estimator at 500-step sampling has ~30 independent
  samples (hydrolysis correlation time ~6.7k steps); report effective-n
  error bars rather than binomial ones.

## Files

- `hydrolysis.ergo` (MIRROR=0 dynamic), `hydrolysis_cert.ergo` (MIRROR=1 cert
  variant), `hydrolysis_mirror.py` (`--fd/--cert/--cal/--run`; params via env
  KHYD/KOFF_T/KOFF_A/SEED/NMONO).
- `hydro_cert_config.txt`, `hydro_cert_forces.txt`, `hydro_cert_nuc.txt`
  (mirror oracle dumps), `engine_cert_dump.txt` (engine cert stdout),
  `compare_cert.py`.
- `logs/`: all engine/mirror dynamic logs, cal logs, cert dumps.
- `analyze.py` (statistics), `burst.py` (catastrophe increments).
