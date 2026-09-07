# φ4 SANDBOX — definition triage results

**Status: triage complete.** Sandbox = pool-coupled Gillespie engine
(`popsim.py`), all rates generated from certified rung tables, zero geometry,
zero fitted parameters. One uncertified input: nucleation rate k_nuc (scanned
as the knob). Purpose: decide what φ4 means before building the engine assay.

## 0. Mirror gate — PASS

Single filament, N_tot=60, V=1728, φ1 reflecting floor, 600k steps:

| observable | sandbox | engine (certified) |
|---|---|---|
| split JB/(JB+JP) | 0.681 | 0.68 |
| aB (barbed tip ATP) | 0.785 | 0.78–0.81 |
| aP (pointed tip ATP) | 0.470 | 0.44–0.48 |
| T (treadmill current) | 1.31e-4/step | 1.4–1.7e-4/step |
| n* | 28.5 | 25–26 |
| c* | 0.0182 | 0.020–0.021 |

n*/c* sit ~10% off, inside φ3's documented ~20% geometry-coupling residual
band (bursts/conformation). The PSPLIT=0.47 assumption (pointed recycling
tracks barbed's) is validated by the exact split.

## A. Population treadmill — CONFIRMED, with a fixed point

N_tot=600, NMAX=60 cap, k_nuc scanned over 3 decades:

| k_nuc | N_f* | n̄ | c* | births | deaths |
|---|---|---|---|---|---|
| 3e-3 | 10.3 | 54.7 | 0.0211 | 7 | 7 |
| 1e-2 | 13.5 | 42.2 | 0.0183 | 23 | 26 |
| 3e-2 | 13.0 | 43.4 | 0.0194 | 65 | 66 |
| 1e-1 | 22.1 | 25.7 | 0.0178 | 181 | 187 |

Stationary filament-number current exists: births = deaths at every
k_nuc, split invariant at 0.68, tip states invariant. At high k_nuc the
collective converges onto the certified single-filament operating point
(n̄ → 25.7, c* → 0.018). **φ2 one octave up is real: the sheet is a
stationary population with a through-current of filaments.**

## B. κ recursion / mean-field closure — EXACT, plus a discovery

Conservation + pinned c* predicts n̄ exactly:

  n̄ = (N_tot − c*·V)/N_f*    →    Δ = 0.00 at all four stationary points

c* moves only 0.0178–0.0211 across 30× in k_nuc. The screening/depletion
feedback acquires NO density dependence: the kernel is scale-invariant at
the population level (DeepSeek's "κ fixed" hypothesis confirmed one octave up).

**Discovery (chemostat experiment):** with c clamped, a single filament
seeded at n=25 COLLAPSES to the floor for c ≤ 0.022 and RUNS AWAY for
c ≥ 0.026. There is no stable fixed point under fixed c — because E(n)
rises with n, bind kinetics are superlinear. Stability comes entirely from
pool conservation (n↑ → c↓). **The unit is stable only inside the
collective.** The recycling loop (rising E) and the depletion loop (c*)
are not two facts; they are one feedback, and it lives at the population
level. This also re-derives φ1's nucleation barrier from the E(n) table:
from n=3, growth requires E ≥ ~1.16 (n ≳ 12) before kinetics win.

## C. Exclusion-as-deletion — DISTINGUISHABLE, signature found

Same k_nuc, same target N_f ≈ 13, two exclusion mechanisms:

| mechanism | N_f* | c* | nucleation-wait CV |
|---|---|---|---|
| hard deletion (cap) | 12.8 | 0.0185 | 0.77 (sub-Poisson) |
| soft suppression ∝(1−N_f/cap) | 10.9 | 0.0217 | 0.93 (near-Poisson) |

Deletion leaves a refractory signature in the nucleation hazard (CV < 1);
dynamic suppression does not. The two are decidable with per-event
nucleation timestamps — already on the φ3→φ4 instrument errata.

## D. Sheet / S2 recursion — NOT TESTABLE in sandbox

Requires an alignment coupling between filaments; no rung has certified
such a coupling. Importing one would be new physics, not reduction.
The engine must supply it — if φ4 goes here, the assay must measure
filament-filament alignment statistics first.

## Verdict for the φ4 assay

φ4 = **the population treadmill with pool-mediated stability**. Three
sharp, engine-testable predictions graduate:
1. births = deaths stationary current; split 0.68 invariant under N_f.
2. c* pinned at the single-filament value regardless of nucleation rate;
   n̄ set by pure conservation.
3. Nucleation waiting-time CV < 1 if niche exclusion is deletion, ≈ 1 if
   dynamic — the instrument already exists on the errata list.

Assay requirement (full engine): nucleation-from-pool kinetics +
per-event bind/nucleation timestamps + anchor-rank logging (φ3 §7 errata).
The single uncertified rate (k_nuc law) must be measured, not assumed.

Artifacts: phi4/popsim.py, phi4/plan.md, this doc.
