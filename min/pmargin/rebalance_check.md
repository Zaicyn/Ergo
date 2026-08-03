# Force-field rebalancing sweep — factorial + Direction C

Programs: `min/pmargin/gen_rebalance.py` → `rebalance_*.ergo`
(+binaries/.out). Base: `freeze_sim_x3.ergo` (dock_sim + adopted ×3
rigidification; the ×1/0.0020 gate cell is `freeze_sim_x3.out` —
best 8.95, mean 11.90, place 11.55 ✓ reproduces). Deepseek's candidate
knobs: HYDRO_STRENGTH ↓ (geometry-agnostic packing), RES_ANGK/RES_TORSK
↑ (local geometry, on top of the ×3 freeze), NATIVE_K ↑ (outvote
packing). BACKBONE_D fixed at ×3; interface terms untouched.

## Factorial (8 blocks each; best / mean full / internal / placement)

| hydro \ stiff | ×1 | ×2 | ×4 |
|---|---|---|---|
| 0.0020 (gate) | 8.95 / 11.90 / 2.81 / 11.55 | 8.92 / 11.84 / 2.72 / 11.51 | 8.91 / 11.94 / 2.67 / 11.62 |
| 0.0010 | 8.95 / 11.93 / 2.81 / 11.57 | 8.92 / 11.83 / 2.74 / 11.50 | 8.91 / 11.88 / 2.66 / 11.57 |
| 0.0005 | 8.95 / 11.95 / 2.80 / 11.60 | 8.93 / 11.83 / 2.72 / 11.50 | 8.91 / 11.92 / 2.65 / 11.60 |
| 0.0002 | 8.97 / 11.93 / 2.81 / 11.58 | 8.94 / 11.82 / 2.73 / 11.48 | 8.91 / 11.79 / 2.66 / 11.48 |

## Direction C (NATIVE_K at the gate cell)

| NATIVE_K | best | mean | internal | placement | note |
|---|---|---|---|---|---|
| ×1 (gate) | 8.95 | 11.90 | 2.81 | 11.55 | |
| ×2 | 8.99 | 12.11 | 2.82 | 11.76 | inert (within noise) |
| ×4 | 9.00 | **180.5** | 41.2 | 175.7 | **breaks the sim**: block 2 explodes to RMSD 1357.8 — 4× contact springs are beyond the integrator/field balance at DT=0.01 |

## Verdict

**(a) Does any cell move placement? NO.** All 12 factorial cells tie
(best 8.91–8.97, placement 11.48–11.62) across a **10× hydro range**
and **×12 effective local stiffness**; NATIVE_K ×2 ties and ×4 is a
hard ceiling that breaks the dynamics. No cell approaches placement 8,
let alone 3.
**(b) Fold integrity: rebalancing is SAFE** (internal 2.65–2.82
everywhere — no cell breaks the per-domain folds) **but INERT.**
**(c) Frustration relocation: not even that.** Deepseek's caveat
doesn't get the chance to apply — the wrong assembly basin is
insensitive to every single-axis knob at ±50–1000% ranges. The
frustration is not a two-term imbalance a knob can relocate; it is a
collective property of the field (consistent with the whole arc:
cold ≡ hot, rigidification moves 5%, 10× hydro moves 0.1).

**Rebalancing is hereby exhausted.** The full deterministic option set
— contacts, short dihedrals, long dihedrals, cold schedule, early
activation, rigidification, and now parameter rebalancing on both
packing and geometry axes plus the contact-strength axis — all tie or
break. Per the user's preference order, **rigid-body Monte-Carlo
domain moves become the justified last resort**: the placement error
is a rigid-body coordinate the field's per-bead dynamics cannot
re-explore, and no field-side knob changes the field's preferred
(wrong) assembly. Alternative honest stop: accept the current ceiling
(fold-then-dock + ×3 freeze: best 8.95, mean 11.90 vs all-at-once
13.2/21.0).

Files: `gen_rebalance.py`, `rebalance_*.ergo` (+13 binaries, `.out`s),
this report.
