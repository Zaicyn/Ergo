# φ4 Population Rung — Oracle (PRE-REGISTERED, before any engine run)

Date: 2026-09-01. Oracle: popsim_pop.py (popsim + per-filament life history).
Parameters: N_tot=60, V=1728 (the engine box), dissolve=True (homogeneous
population, no incumbent privilege), corner nucleation ν = NU0·(c/C0)^2.6 with
NU0=4.86e-4/step/box, C0=0.0212 (measured, NUCLEATION_LAW.md), plus linear-law
sensitivity k_nuc=NU0/C0=0.0229. 16 seeds (77031+i·7919), t_max=2e6,
t_burn=4e5 (stationary half: 1.6e6 steps/run).

## THE HEADLINE PREDICTION (surprise vs plan sketch)
At the measured corner, nucleation FRAGMENTS the pool: the box self-organizes
into a DWARF population, not one mature incumbent.
Conservation: N_f·n̄ + c*·V = 3.4·6.5 + 0.022·1728 ≈ 22 + 38 = 60. Exact.

## Pre-registered numbers (corner law; linear-law agreement in parens)

| Observable | Oracle value |
|---|---|
| N_f* | 3.42 ± 0.26  (3.19 ± 0.18) |
| n̄ | 6.53 ± 0.90  (6.62 ± 0.80) |
| c* | 0.0220 ± 0.0007  (0.0226 ± 0.0008) — PINNED at the no-nucleation value |
| split | 0.683 ± 0.010  (0.684) — INVARIANT |
| aB / aP | 0.810 / 0.643 — aP ELEVATED vs single-filament 0.44-0.48 (young combs) |
| births = deaths | ≈ 5.7e-4 /step/box at stationarity (≈902 per 1.6e6 steps) |
| inter-birth wait | mean ≈ 1780-1930 steps, CV ≈ 1.0-1.1 (memoryless) |

N_f distribution (time-weighted, corner): P(1)=0.065, P(2)=0.178, P(3)=0.292,
P(4)=0.266, P(5)=0.144, P(6)=0.045, P(7)=0.009. P(N_f=0) < 0.001.

Newborn survival: P(≥8)=0.084, P(≥12)=0.022, P(≥16)=0.009, P(≥25)=0.002.
**98% of newborns die below maturity.** Median lifetime 1.9k steps,
mean 5.9k (survivor-pulled tail). Median max_n = 3 (most never add even one
monomer); mean max_n = 4.4.

Length distribution: monotonic decay from n=3 (26%) — NO peak at the
single-filament n̄=25. The single-filament steady state is NOT the population
steady state at this ν.

## The three sandbox predictions, restated for engine falsification
1. **Stationary birth-death current**: births = deaths within noise, at
   ≈ ν_corner. Split invariant 0.68.
2. **c* pinned** by conservation at ≈0.022 regardless of nucleation; the
   in-filament mass is what fragments, not the pool.
3. **Hazard CV ≈ 1** for inter-birth intervals (memoryless, occupancy-gated
   Poisson) — the deletion-test discriminator.

## Secondary pre-registered findings
- Linear vs quadratic-cube nucleation law: INDISTINGUISHABLE at pinned c*
  (all observables within 1σ). The population buffers the nucleation law's
  c-dependence; only the corner RATE matters. Engine may use either.
- aP = 0.64 (vs 0.45 single-filament) is a pure population effect: rapid
  turnover keeps combs young. If the engine shows aP ≈ 0.45 with nucleation
  on, the engine is NOT in the population regime.

## Engine-side assay notes (for Stage P1)
- Engine must allow dissolution of ALL filaments at n=3 (no reflecting floor).
- Trimer promotion replaces recycling; corner params KNUC=1.0, KDIM=2.0.
- Census diagnostics: per-filament birth/death events with STEP, id, length;
  inter-birth intervals; periodic N_f census for the time-weighted distribution.
- Engine exclusives (sandbox blind): spatial birth map relative to existing
  filaments (autocatalysis test at population level), dimer soup coexistence.
