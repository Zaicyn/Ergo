# Long-leverage interface orientation restraints — leverage-response curve

Programs: `min/pmargin/gen_leverage.py` → `leverage_{oracle,sim}_s{8,16,30}_k{05,10}.ergo`
(+binaries/.out, 12 cells), analysis `leverage_analyze.py` (+`.out`).
Protocol identical to the orientation-term experiment (orient_check.md)
with EARLY activation (EXTRA_TORSIONS_FROM=0, the term's best shot);
the s=0 null baseline cells are `orient_early_{oracle,sim}_k05.out`
(gate: they reproduce the matrix numbers). Quartet design: per
cross-domain contact (i,j), (i−s, i, j, j+s) and (i, i+s, j−s, j),
crystal p0 — same contacts, same machinery, ONLY the leverage changes
(53 quartets at s=8, 49 at s=16, 36 at s=30; shrinkage from boundary
constraints).

## Leverage-response curve (placement vs s; mean over 8 blocks)

| s | k | init | best full | mean full | internal | placement |
|---|---|---|---|---|---|---|
| 0 | 0.5 | oracle | 9.08 | 12.92 | 2.57 | 12.64 |
| 0 | 0.5 | sim | 9.29 | 12.08 | 2.99 | 11.69 |
| 8 | 0.5 | oracle | 9.09 | 12.94 | 2.55 | 12.67 |
| 8 | 0.5 | sim | 9.29 | 12.21 | 2.93 | 11.84 |
| 8 | 1.0 | oracle | 9.09 | 12.95 | 2.52 | 12.68 |
| 8 | 1.0 | sim | 9.23 | 12.02 | 2.93 | 11.64 |
| 16 | 0.5 | oracle | 9.01 | 12.87 | 2.55 | 12.60 |
| 16 | 0.5 | sim | 9.33 | 12.14 | 2.97 | 11.75 |
| 16 | 1.0 | oracle | 8.99 | 12.86 | 2.60 | 12.58 |
| 16 | 1.0 | sim | 9.15 | 12.08 | 2.98 | 11.68 |
| 30 | 0.5 | oracle | 9.04 | 12.91 | 2.54 | 12.64 |
| 30 | 0.5 | sim | 9.24 | 12.20 | 2.94 | 11.82 |
| 30 | 1.0 | oracle | 9.05 | 12.86 | 2.55 | 12.59 |
| 30 | 1.0 | sim | 9.23 | 12.06 | 2.91 | 11.69 |

**FLAT.** Placement 11.6–12.7 at every leverage and every strength,
both inits. No response, so no minimum effective s exists.
Per-domain COM errors and rotations (best block) are likewise
invariant: A2 ~7.7/31°, A3 ~11.6/34°, B1 ~3.4/25°, B2 ~7.4/28° across
all cells.

## Control: the long-leverage terms DO engage

Final-state deviation of the restraint's own quartets (best block,
sim, k=1.0): s=8 → **14.1° mean** (5/53 > 30°), s=30 → **17.6° mean**
(4/36 > 30°). At every leverage the term drives its coordinates to
near-native — the same verified-active pattern as the s=0 term
(51.7°→12.9°). The null is not a setup failure at any s.

## Verdict — the compliance mechanism is deeper

Long leverage does not collapse the placement error (nowhere near
< 3). The anatomy, now complete across three experiments:

1. The terms satisfy their restraints LOCALLY at every leverage —
   including quartets spanning 30 residues into each domain — while
   the domains stay rotated 23–39° and translated 3.4–11.8.
2. That is geometrically possible only because the domains' internal
   deformation (2.5–3.5 RMSD) is DISTRIBUTED: the bending that
   reconciles near-native interface geometry with wrong global
   placement is spread through each domain, not concentrated at the
   interface. Longer leverage just engages more of an already
   distributed compliance.
3. Deeper still: the deformation is force-driven (cold ≡ hot, the
   oracle domains relax 0→2.5–3.5 from the crystal with no heat at
   all) — **the field's own minimum is not the crystal**. The
   assembly error is therefore not a restraint-design gap but the
   documented force-field ceiling (sdrd_white_check.md's median
   ruggedness) expressed at the assembly level: 36–53 added restraints
   cannot outvote the thousands of frustrated native-targeted terms
   whose collective minimum is the wrong placement.

**Deterministic restraint-based docking is now exhausted** —
contacts (dock_check), short dihedrals (orient_check), long dihedrals
(this work), cold schedule, and early activation all tie. Remaining
levers, in the user's preference order: (a) field rebalancing to
reduce frustration (global, hard — the angle/torsion/contact/steric
balance that sets the field's minimum); (b) rigid-body Monte-Carlo
domain moves (user's last resort; every deterministic alternative has
now been eliminated); (c) accept fold-then-dock's ~40% improvement
over all-at-once (best 9.06 vs 13.2) as the current field's ceiling.

Files: `gen_leverage.py`, `leverage_*.ergo` (+12 binaries, `.out`s),
`leverage_analyze.py`, `leverage_analyze.out`, this report.
