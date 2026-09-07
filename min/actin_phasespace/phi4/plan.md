# φ4 Sandbox — plan

Question: what does φ4 even mean? Triage candidate definitions on a simplified
model before touching the full engine.

## Stage 1 — the sandbox (popsim)
Pool-coupled Gillespie engine. State = filaments (length n_i + nucleotide
bit-string) + pool count m. Conservation: m + Σn_i = N_tot. NO geometry —
every rate generated from certified tables:
- barbed bind: E(n)·SMOL·c (E(n) = certified transport-rung table)
- pointed bind: 0.47·E(n)·SMOL·c (from certified split 0.68; flagged assumption)
- unbinds: KOFFB_T/A·DT, KOFFP_T/A·DT by tip bit (φ3)
- hydrolysis: KHYD·DT per bound monomer (φ3)
- nucleation: k_nuc·c → trimer (the ONE uncertified rate — it is the scanned knob)
- dissolution: filament dies at n ≤ 3

## Stage 2 — mirror gate (lock-step certification)
N_tot = 60, V = 1728, single seed, nucleation off. Sandbox must reproduce the
certified single-filament fixed point: n* ≈ 25–26, c* ≈ 0.020–0.021,
T ≈ 1.4–1.7e-4/step, split 0.68, tip ATP fractions a_B ≈ 0.78–0.81,
a_P ≈ 0.44–0.48. FAIL = fix the sandbox before any population claim.

## Stage 3 — definitions battery
- A: population treadmill. Scan k_nuc; measure N_f*, c*, P(n), birth/death
  currents, stationarity. Prediction: fixed point exists, mean-field from
  certified laws predicts it.
- B: κ recursion. c*(N_f) vs analytic 1D fixed-point closure. Deviation =
  collective physics beyond mean field.
- C: exclusion-as-deletion. Hard niche capacity vs soft competition;
  discriminator = nucleation waiting-time hazard (censored Poisson vs
  suppressed rate).
- D: sheet/S2 recursion. FLAG ONLY — needs an uncertified alignment coupling;
  sandbox cannot speak to it without importing new physics.

## Stage 4 — verdict doc
PHI4_SANDBOX_RESULTS.md: which candidate definitions produce sharp,
engine-testable predictions. Survivors define the real φ4 assay.

Standing constraints: single thread, lock-step, no swarm; all artifacts
checkpointed to /mnt/agents/output/actin_phasespace/phi4/.
