# Proinsulin MIDY Campaign Report — 2026-08-23

**System:** ergo waveform MD engine (mcl toolchain), 2KQP proinsulin (86-res NMR
structure; model units 1 = 2.5 Å, mean Cα–Cα = 1.52 model units).
**Question:** can contact-mediated capture by misfolding-prone mutant proinsulin
(Akita MIDY, CysA7Tyr) damage wild-type proinsulin folding — the dominant-negative
mechanism of mutant-insulin diabetes — and under what conditions?
**Full audit trail:** MULTIDOMAIN_FINDINGS.md §22–§42.

## Model summary

- Go-like native contact field + Morse backbone + angle/torsion terms, hydrophobic
  packing, hbond formation (cap 2), Cosserat ribbon frame dynamics.
- Breakable harmonic cystine restraints (CSS_K=0.5, R0 from scaled native geometry;
  FD-validated, max err 2.4e-08). Akita variant: CysA7Tyr mutation + A7–B7 bond OFF.
- Non-native mispairing restraints (MIS arrays, per-pair K): intra-mutant wrong bonds
  at 0.25, inter-chain wrong bonds from freed mutant CysA7 to partner-chain
  Cys72/76/85 equivalents at full disulfide strength 0.5.
- Multi-chain systems via CHAIN_BREAK/CHAIN_BREAK2 (junction-guarded backbone terms,
  no cross-chain Go contacts, per-chain anchors). Dimer (172 res), trimer (258 res,
  side-8 triangle start).
- Adaptive substepping (SUBSTEP_D=0.8, max 64): a-priori closest-approach scan,
  force+integrate at DT/NSUB, rooted dampers. Resolved the §31 steric detonation
  (dimwt8_2.0: explosion at frame 870 -> clean fold). No clamps, no caps anywhere.
- Per-chain Kabsch RMSD telemetry (rmsd_c1..c4), engine-native, verified against
  offline Kabsch to printed digits; telemetry runs bitwise-reproduce pre-telemetry
  physics.

## Campaign arc and results

### 1. Single-chain baseline (§22–§24)
Bare field folds 2KQP to RMSD 3.47–4.71 with emergent native-like cystine geometry.
Cystine restraints inert for WT (double-dip confirmed — the field alone places all
pairs at native distance). Akita seam deletion alone does NOT misfold (A7–B7
topologically redundant under the contact map; echo: Hua et al. 2006 find SerA6–A11
deletion likewise folds and secretes).

### 2. Mispairing and pulse (§25–§27)
Wrong-bond restraints (7→76, 7→85 at 0.25) create modest strain (~1 RMSD unit);
7→76 closes on 2/3 seeds. Coherent pulse rescues SOFT traps (akmis seed 0:
4.14→3.16, wrong bond reopens 1.85→3.39) but not compact settled basins.

### 3. Two-chain (§28–§33)
Capture robust: mutant Cys7 approaches WT cysteines to 2.16–2.52 (target 2.0);
Akita dimers stay associated (COM 4.3–10.1 vs WT-WT 17.7–24.8). But WT partner
fold quality undamaged at n=3 — toxicity read negative at two-chain scale.

### 4. Trimer dose series, no stress (§34–§37, §42)
Dose tiers 0M/1M/2M, 3 seeds. Wrong-bond network densest yet (mutant Cys7 at
2.2–3.0 from every partner target; several fully closed). Folding-time channel
negative (seed noise dominates; per-chain telemetry §36–§37).

**Completed factorial (6 seeds in the 2M tier) — the corrected headline:**

| tier | WT chains | n | frac RMSD>5 | mean |
|---|---|---|---|---|
| triwt (0M) | all | 9 | **11%** (1/9) | 4.00 |
| trim1 (1M) | chains 2,3 | 6 | **0%** (0/6) | ~4.2 |
| trim2 (2M) | chain 3 | 6 | **67%** (4/6) | 6.28 (median 5.33) |

Two mutants in a three-chain cluster sextuple the WT marginal-failure fraction
with NO stress applied. One mutant never does. The earlier n=3 negative
(§35) undersampled the 2M tier; the completed factorial reverses it.

### 5. Thermal-floor stress factorial (§38–§41)
Sustained thermal noise (floor 0.1/0.25/0.4 of folding-cycle peak) after frame
76800, schedule provably identical before it (bitwise-verified in all runs).

- **triwt, all floors: untouched.** Settled WT folds are unconditionally stable
  (means 4.00/4.01/4.03/3.99 across floors; no strip events in 12 control runs
  including 1M-at-stress).
- **trim2 under stress: 2 strip events in 6 runs**, both marginal-at-onset folds
  inside the 2-mutant cluster: seed 1 chain 3 (WT) 5.2→8.9 at f25; seed 1 chain 1
  (mutant) 5.1→16.9 at f40.
- Marginality is necessary-looking, not sufficient (seed 3's 6.11 chain survived
  f25). Cluster geometry selects which marginal member goes.

## Conclusions

1. **Dose-dependent dominant-negative effect — POSITIVE at 2/3 mutant dose.**
   A two-mutant cluster raises WT fold-failure/marginality from ~11% to ~67%
   at baseline. Below that dose (one mutant in three chains, or any two-chain
   assay), no effect is detectable.
2. **Stress interaction — POSITIVE, narrow.** Sustained ER-stress analog strips
   exactly the marginal folders inside mutant clusters (WT or mutant genotype);
   settled folds and WT-only systems are immune at every floor tested.
3. **MIDY sketch supported in silico:** mutant proinsulin clusters (i) increase
   the fraction of co-folded WT that lands marginal, and (ii) under sustained ER
   stress the marginal members are destroyed. This matches the clinical pattern
   of stress-precipitated β-cell failure and the literature's gap (dominant-
   negative claims rest on band-intensity co-expression assays, never structural
   measurement of the WT partner).

### 6. Four-chain baseline (§43–§44) — proposed-universality starting point
Two tiers × 3 seeds (seeds matched to the trimer series):

| tier | WT chains | frac RMSD>5 |
|---|---|---|
| 2M/4 (quad2m) | 6 (2/run) | **33%** (2/6) |
| 3M/4 (quad3m) | 3 (1/run) | **33%** (1/3) |

**Baseline dose ladder (WT fold-failure fraction):**

| mutant count / system size | 0M | 1M | 2M | 3M |
|---|---|---|---|---|
| 3-chain | 11% (1/9) | 0% (0/6) | 67% (4/6) | — |
| 4-chain | — | — | 33% (2/6) | 33% (1/3) |

Neither simple model wins: not pure dose-fraction (2M/4 should approach
0–17%), not pure mutant-count (2M/4 should hold at 67%), and 3M/4 shows no
escalation over 2M/4. Best current summary: toxicity peaks in compact
clusters (2M/3) and dilutes with system size at fixed mutant count; no
universal threshold resolved at n=3 seeds per tier. This ladder is the
minimum viable baseline for replication — not a rate estimate.

*Erratum noted: the first quad batch's per-chain telemetry mis-segmented
chains 3–4 (rmsd_c4=0.00); dynamics were unaffected and finals were
recovered offline. Fixed files regenerated; rerun restores the per-chain
time series.*

## Limitations (stated plainly)

- Cα-level Go-like field; no side chains, no ER membrane, chaperones, redox, or
  proteostasis machinery. The "stress" analog is thermal noise, not UPR signaling.
- Mispairing restraints are imposed harmonic bonds, not emergent chemistry —
  the model tests consequences of wrong-bond capture, not its chemical likelihood.
- Strip events: 2/6 in the stressed 2M tier; seed-counts are small throughout.
- Seed 4 chain 3 is a landscape failure independent of stress (13.1 at baseline);
  it inflates the 2M mean but not the marginal-fraction conclusion (4/6 holds
  with it excluded as 3/5).

## Verification highlights

- Every force term FD-validated before use; cystine block max err 2.4e-08.
- Telemetry-only changes bitwise-reproduce pre-change trajectories (checked on
  all nine trimer runs; pre-floor schedule splices bitwise-identical in all 24
  stress/baseline pairs).
- Substepping resolver: zero explosions across 33 trimer-scale runs (max rgyr
  16.9, transient, recovered).
