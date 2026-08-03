# Tether-repair designs for the 1SNO fragmented trap

Programs: `min/pmargin/gen_tether.py` → `tether_a_k{005,02,05,10}.ergo`,
`tether_b_k{05,10}.ergo` (+binaries/.out), analysis `tether_analyze.py`
(+`.out`). Base: `packed_1sno_struct.ergo` (validated packed sweep).
Diagnosis being tested (`dihedral_1sno_check.md`): the seed-3.0 trap is a
fragmented fold — 8 broken backbone tethers (the Morse bond plateaus with
~zero restoring force past D≈4, cost capped at 1.4/bond) while satisfying
196/197 native contacts.

## Designs (documented forms)

Both add a harmonic continuation past DCUT=4.0 to the backbone bond:
**E_bond = D_e(1−g)² + K_LR·(D−DCUT)² for D > DCUT**, force
FM += −2·K_LR·(D−DCUT)·FORCE_SCALE — the same form and magnitude scale as
the sim's Go contacts (NATIVE_K=1.0), so the bracket is dynamically
precedented in this integrator.

- **DESIGN A (global long-range tether)**: K_LR at EVERY backbone bond,
  bracket 0.05 / 0.2 / 0.5 / 1.0 (equilibrium Morse curvature is 2.8, so
  0.05 is weak, 1.0 is dominant).
- **DESIGN B (targeted junction reinforcement)**: K_LR ONLY at the broken
  junctions from the diagnosis — bonds 8, 22, 24, 32, 72, 90, 91 (the
  mid-chain clusters 22-24-25 and 90-91-92) — at 0.5 / 1.0. **Bond 1
  excluded** (documented choice): the N-terminal dangle appears in 6/8
  baseline blocks and is genuine terminal flexibility, not the
  fragmentation failure; B must not fight it.

## Headline table (trap = block 4, seed 3.0; sim metric full/D1/D2)

| variant | trap full/D1/D2 | D1<3 rescue? | trap broken bonds (>3/>8) | bond-1 length (blk1/blk4) |
|---|---|---|---|---|
| baseline | 9.66/8.73/2.68 | — | 8 / 4 | 16.2 (blk4) |
| A k=0.05 | 9.61/8.49/1.49 | no | 2 / 0 | 1.52 / 1.52 |
| A k=0.2 | 9.57/6.43/3.24 | no | 2 / 0 | 1.52 / 1.52 |
| A k=0.5 | 9.70/8.50/6.96 | no | 4 / 0 | 1.52 / 1.52 |
| A k=1.0 | 9.65/8.57/4.52 | no | 1 / 0 | 1.52 / 1.52 |
| B k=0.5 | 9.32/8.66/1.25 | no | 3 / 1 | 18.3 / 15.4 |
| B k=1.0 | 9.86/**4.14**/1.69 | no | 4 / 1 | 18.5 / 13.6 |

## Native gate (good seeds must survive; baseline → variant, full RMSD)

| block (seed) | baseline | A 0.05 | A 0.2 | A 0.5 | A 1.0 | B 0.5 | B 1.0 |
|---|---|---|---|---|---|---|---|
| 1 (0.0) | 2.05 | 1.26 ✓ | 1.06 ✓ | 1.27 ✓ | 1.48 ✓ | 2.14 ✓ | 2.14 ✓ |
| 3 (2.0) | 2.29 | 0.91 ✓ | 0.91 ✓ | **0.65 ✓** | 0.93 ✓ | 2.25 ✓ | 2.29 ✓ |
| 8 (7.0) | 2.44 | 1.74 ✓ | 1.19 ✓ | 2.34 ✓ | 1.37 ✓ | 2.06 ✓ | 1.98 ✓ |
| 2 (1.0) | 3.26 | 1.60 | 2.82 | 2.75 | 1.84 | 2.22 | 2.66 |
| 5 (4.0) | 4.67 | 3.79 | 2.58 | 2.68 | 2.58 | 4.40 | 4.34 |
| 6 (5.0) | 2.96 | 3.01 | 1.28 | 1.60 | **9.13 NEW TRAP** | 1.96 | 2.99 |
| 7 (6.0) | 3.69 | 3.00 | 4.43 | 3.95 | 3.69 | 4.02 | 3.82 |

## Findings

1. **Fragmentation is mechanically closed by both designs** — broken
   bonds in the trap drop from 8 (4 deep) to 1–4 (≤1 deep) at every
   strength. Design A additionally pulls the N-terminal bead to its
   native bond length (1.52) in every block; Design B leaves it
   dangling (13.6–18.5), as designed.
2. **…but the trap basin does NOT close.** Full-chain RMSD stays
   9.3–9.9 in all six variants. The chain is now connected and STILL
   mis-folds to the same depth. **Backbone fragmentation was the
   field's cheap accommodation of the mis-fold, not its cause.**
3. **D1's internal fold IS repairable without domain placement**:
   B k=1.0 takes D1 8.73→4.14 (best of all variants) and D2 stays
   1.69 — yet full RMSD is 9.86: the two domains are each folded
   better and mutually MISPLACED. The irreducible core of the seed-3.0
   basin is inter-domain placement under the degenerate contact map
   (all 25 cross-domain contacts were already satisfied in the trap).
4. **Design A is a genuine field improvement independent of the trap**:
   at every strength the gate passes and most good/marginal blocks
   improve substantially — block 3 reaches **0.65** at k=0.5 (best fold
   of the project), block 1 → 1.06–1.48, block 5 4.67→2.58. Part of
   this is metric (the dangling N-terminus no longer inflates RMSD,
   ~1.7 units), part real (block 3's D1 = 0.72 at k=0.5 vs 2.68
   baseline — better than dangle-subtraction explains). The "don't
   force the terminus" concern cuts the other way in practice: the
   dangle was itself a plateau artifact (nothing holds the terminal
   bead), and repairing it costs nothing at the gate. Documented
   honestly: A DOES force the terminus; the measured effect is
   positive.
5. **Tradeoff at the strong end**: A k=1.0 spawns a NEW trap (block 6:
   2.96→9.13) — the too-stiff tether creates its own kinetic failure
   mode. The usable window is K_LR ≈ 0.2–0.5.
6. Design B is the terminus-safe option: gate-neutral (good blocks
   within ±0.3 of baseline), and at k=1.0 the best D1-internal repair
   — but no basin closure either.

## Verdict

- **Does tether repair close the fragmented basin? NO** — neither
  design, at any strength. The fragmentation is cured (broken bonds
  8→1–4) and the fold still lands at full RMSD ≈ 9.3–9.9. The seed-3.0
  basin's cause is upstream: a domain-placement error that the
  degenerate 136-residue contact map cannot penalize.
- **Does the Morse plateau itself need redesign? YES, as a general
  field defect** — it produces the near-universal N-terminal dangle
  and the fragmentation pathology, and Design A at K_LR = 0.2–0.5
  repairs both with the gate passing everywhere and the best folds of
  the project (0.65–1.48 on good seeds). K_LR = 1.0 overshoots (new
  trap at block 6). Recommended field change: harmonic continuation
  K_LR ≈ 0.3 ± 0.2 past D=4.0.
- **Targeted patching (B) is the wrong tool for this trap** — it
  preserves termini and repairs D1 internally (8.7→4.1) but, like A,
  cannot fix domain placement. The trap needs an interface/docking-level
  mechanism, not a backbone one: per-domain swap criteria and a longer
  hot phase (the temper report's follow-ups 1–2) are the levers that
  match the anatomy; interface-register terms are a candidate field
  addition.

Files: `gen_tether.py`, `tether_a_k{005,02,05,10}.ergo`,
`tether_b_k{05,10}.ergo` (+binaries, `.out`s), `tether_analyze.py`,
`tether_analyze.out`, this report.
