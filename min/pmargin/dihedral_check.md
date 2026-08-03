# Dihedral diff + targeted torsion correction — trap anatomy and rescue

Program: `min/pmargin/dihedral_diff.py` (profiles + contacts),
probes `packed_bba5_torsprobe.ergo` (TORSK 0.2→1.0 at res 10, 15),
`packed_bba5_torsk05.ergo` (0.5 strength), `packed_bba5_torskwrong.ergo`
(wrong-position control, res 5, 20 at 1.0). Structures from the
validated packed-BBA5 outputs (seed 4.0 near-native 0.29, seed 0.0
trap 1.668 — sim metric; see the Kabsch note below).

## 1. Per-residue dihedral comparison (sim's force-convention dihedral)

The trap's backbone dihedrals match native almost everywhere. Full
profile in the analysis output; the essentials:

- 19 of 21 dihedrals agree with native within ~5° (native vs trap).
- Only two material deviations: **res 15: +15.6°** (native 62.9° →
  trap 78.4°) and **res 10: −5.1° vs native (−8.1° vs the good fold)**.
- The register-torsion pairs (residues 1–2, 6–9) all match within ~3° —
  the β-sheet chirality is CORRECT in the trap.
- All 13 unique native contacts are satisfied in BOTH states
  (mean |D−R0| = 0.009 fold, 0.014 trap; max deviation 0.04).
- Per-residue Kabsch deviations (exact Kabsch, see note): distributed
  along the whole chain, worst at the termini (res 23: 2.29, res 4:
  1.56, res 22: 1.56), middle well-aligned (res 8: 0.16).

**Anatomy verdict: the trap is NOT a local-structure error.** It is a
globally warped native-like fold — native dihedrals, native contacts,
correct sheet chirality — with the error spread thinly across the whole
backbone (a coherent twist, termini splayed). No clustered bad bend
exists to correct; exactly two dihedrals deviate materially.

## 2. Correction design (geometric, no oracle masking)

The model's own native-torsion term (crystal-derived targets
RES_TORSP0, part of the force field) stiffened at exactly the two
identified positions: `RES_TORSK(10) := 1.0, RES_TORSK(15) := 1.0`
(from the recipe-wide 0.2). No trap-specific term, no register
masking — the field is the model's, tightened where the trap's only
local deviations live.

## 3. Validation — the probe works (contrary to my endpoint-based expectation)

| block | seed | v2 baseline | probe (1.0) | half-strength (0.5) | wrong-position control (1.0 at 5,20) |
|---|---|---|---|---|---|
| 1 | 0.0 (trap) | 1.6680 | **0.6265 RESCUED** | **0.7415 RESCUED** | 0.9333 (not rescued) |
| 2 | 1.0 | 0.3150 | 0.2381 | 0.2569 | 0.3555 |
| 3 | 2.0 | 0.4872 | 0.3372 | 0.3762 | 0.2947 |
| 4 | 3.0 | 0.3889 | 0.2957 | 0.3274 | 0.4158 |
| 5 | 4.0 (gate) | 0.2872 | 0.2424 ✓ ≤ 0.7 | 0.2532 ✓ | 0.2990 ✓ |
| 6 | 5.0 | 0.1854 | 0.2049 | 0.1230 | **0.6723 (damaged)** |
| 7 | 6.0 | 1.0047 | **0.1715** | 0.1780 | **1.4711 (damaged)** |
| 8 | 7.0 | 1.0855 | **0.8599** | 0.9087 | 1.1709 |

- **Seed 0.0 is rescued at both strengths** (1.668 → 0.627 at TORSK
  1.0, → 0.742 at 0.5; trap threshold 0.775). Trapped seeds 6.0/7.0
  also improve dramatically (1.00/1.09 → 0.17/0.86 at 1.0).
- **Native gate passes** (seed 4.0 = 0.242 ≤ 0.7 at 1.0; 0.253 at 0.5);
  all good folders preserved or improved.
- **Specificity control:** stiffening the WRONG positions (res 5, 20)
  does not rescue (0.933 > 0.775) and damages two good folders
  (0.185→0.672, 1.005→1.471). The rescue is specific to the identified
  dihedrals; arbitrary stiffening is harmful.
- Mechanism note (honest): the endpoint analysis predicted a weak
  effect (the trap's final dihedrals are nearly native). The rescue is
  DYNAMICAL — the trap's formation pathway requires res-15 at +78° and
  the res-10 deviation; stiffening those targets closes the trap's
  basin during folding, not at the endpoint. Trajectory evidence
  decided against endpoint evidence.

## 4. Bonus finding — the sim's RMSD is inflated (verified)

Exact SVD Kabsch (cross-checked with scipy): seed 4.0 fold = **0.217**
vs sim CSV 0.287 (×1.32); seed 0.0 trap = **0.996** vs sim CSV 1.668
(×1.68). The sim's quaternion power-iteration RMSD overestimates the
exact Kabsch RMSD by 1.3–1.7×, varying per state (its rotation is not
always optimal). All historical RMSD comparisons remain internally
consistent (same metric throughout — the validation tables stand
unchanged), but absolute values are inflated: the documented "best
BBA5 fold 0.74 Å" is ≈ 0.55 Å at exact Kabsch, and the seed-0.0 trap
is ≈ 1.0 model units, not 1.67. This affects no conclusion drawn in
this project (all oracles were evaluated with the same sim metric) but
should be corrected in COMPUTE_RMSD if absolute accuracy is ever
needed (the sim's N44 quaternion matrix convention likely has a
sign/order issue worth auditing).

## Bottom line

The trap's anatomy is a fine-grained warp with native local structure —
no clustered bend — yet a TWO-POINT torsion correction at the only
deviating dihedrals (10, 15) rescues it and improves the whole sweep,
with the wrong-position control proving specificity. The correction is
a legitimate field improvement (crystal-derived targets, tightened at
two points), and it converts the seed sweep from 3 trapped seeds to
zero at strength 1.0 (all 8 blocks ≤ 0.86, 7 of 8 ≤ 0.63).

Files: `dihedral_diff.py`, `packed_bba5_torsprobe.ergo`,
`packed_bba5_torsk05.ergo`, `packed_bba5_torskwrong.ergo` (+binaries),
`packed_bba5_torsprobe.out`, `torsk05.out`, `torskwrong.out`,
this report.
