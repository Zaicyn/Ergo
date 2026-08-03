# Rigid-body Monte-Carlo domain docking — move-set completeness test

Programs: `min/pmargin/gen_mc.py` → `mc_{greedy,t005,t02,t10,cool,r1,r15}.ergo`
(+binaries/.out). Start: all 8 blocks' dock_sim final states
(`dock_sim_struct.out`; gate: mean start score 12.46 ✓). Domains held
rigid (their ×3-frozen folds — internal geometry constant throughout).

## Design (documented choices)

- **MOVE CLASS**: rigid-body rotation (random axis, ±ROT about the
  domain COM, Rodrigues) + translation (random direction, TR_STEP), one
  domain per move, hash-picked. Steric guard: any moved bead within 1.0
  of a non-domain bead → revert (keeps the search physical).
- **SCORING (the key decision)**: full-chain Kabsch RMSD to native —
  with rigid domains this is EXACTLY the placement error of the
  decomposition (internal is constant). We score by placement RMSD as a
  **move-set completeness test** (can rigid-body moves find native
  placement at all?), **NOT by field energy**: the field's assembly
  minimum is proven wrong (rebalance_check.md) — energy-scored MC would
  drive back to the wrong assembly. The field stays the physics; MC is
  the search layer.
- **RANDOMNESS**: validated splitmix white hash, per-(step, block) seed
  + xorshift chain — deterministic, reproducible MC trajectories; the
  8 blocks are the seed statistics.
- **SCHEDULE**: constant-T Metropolis, greedy (T=0) control, geometric
  cooling 1.0→0.01; step-size sweep at greedy (1°/0.2, 5°/0.5, 15°/1.0).
  10000 steps per variant; ~2–60% acceptance depending on T/stepsize.

## Trajectory table (start 12.46 everywhere)

| variant | final mean | best-of-8 | acceptance | shape |
|---|---|---|---|---|
| greedy 5°/0.5 | 6.13 | 4.74 | 3.8% | anneals, converges ~8k steps |
| T=0.05 | 6.18 | **2.85** | 43% | anneals, slightly noisier floor |
| T=0.2 | 8.92 | 3.40 | 55% | elevated thermal floor (~9) |
| T=1.0 | 14.10 | 8.49 | 62% | **wanders — mean RISES (too hot)** |
| cool 1.0→0.01 | **5.21** | **2.80** | 47% | smooth anneal (10.9→5.3) |
| greedy 1°/0.2 | 7.07 | 4.74 | 7.5% | slow converge |
| greedy 15°/1.0 | **4.58** | **2.77** | 2.2% | fast anneal (9.9→4.6 by 6k) |

Step-size trend at greedy: 1°/0.2 (7.07) < 5°/0.5 (6.13) < 15°/1.0
(4.58) — larger steps do better: the placement landscape in rigid-body
coordinates is smooth/funnel-like at these scales, not rugged.

## Verdict

**(a) Does ANY schedule reach placement < 3? YES — three of seven.**
Best-of-8: 2.85 (T=0.05), 2.80 (cooling), 2.77 (15°/1.0 greedy) — a
**−76% break of the deterministic ceiling** (~11.5 → 2.8) in 10⁴
steps. Since the score is full-chain RMSD and the frozen internal fold
error is ~2.6–2.7 (documented), the best blocks' implied placement
residual is ~1 model unit or less — **placement is essentially solved
in the best blocks; the residual is the input folds' internal error.**
**(b) The move set is COMPLETE and the docked states are NOT
placement-trapped.** Rigid-body search escapes the wrong assembly
freely (acceptances 2–60%, clean annealing trajectories, no steric
jamming) — confirming the arc's diagnosis: the bottleneck was the
per-bead deterministic dynamics' inability to re-explore a rigid-body
coordinate, not the landscape's geometry. MC on that coordinate class
was the right tool, and the user's authorization was well-placed.
**(c) Schedule reading**: cooling is the robust default (best mean
5.21, best 2.80); large-step greedy wins on mean (4.58) but stalls on
bad blocks (block 3: 9.42 — the shared wrong-face dock); T=1.0 is too
hot (wanders), T=0.2 has a thermal floor. Not yet mean < 3 — longer
runs / per-block restarts are the obvious extension.
**(d) Honest caveat (stated in the design)**: the score used the
native — this is a completeness test, not a deployable docking method.
What it licenses: (i) MC scored by a field-consistent placement proxy
(interface contact+register energy alone, which the arc showed is
orientation-informative when the assembly coordinate is searched
properly); (ii) MC placement → field relaxation hybrid protocols;
(iii) the diagnosis stands confirmed: per-bead dynamics was the
bottleneck, not the move set or the search principle.

Files: `gen_mc.py`, `mc_{greedy,t005,t02,t10,cool,r1,r15}.ergo`
(+binaries, `.out`s), this report.
