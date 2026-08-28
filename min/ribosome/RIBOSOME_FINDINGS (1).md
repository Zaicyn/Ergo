# Ribosome Project Findings — Ergo/min/ribosome

Audit log, same discipline as MULTIDOMAIN_FINDINGS.md. Plan: RIBOSOME_PLAN.md.

## Rung 0 — tooling (2026-08-23): COMPLETE
- 1EHZ.pdb parsed: 76 nt, chain A, C1′ beads, 14 resnames (9 modified;
  mapped for geometry purposes to parent bases).
- Canonical cloverleaf WC table verified against geometry: all 21 pairs at
  C1′–C1′ 10.25–10.93 Å (textbook WC range). Stems: acceptor 1-7:72-66,
  D 10-13:25-22, anticodon 27-31:43-39, T 49-53:65-61.
- Absolute-unit calibration: generator normalizes mean backbone spacing to
  1.52 units; setting json mean_ca_ca=3.8 yields scale 0.400 = exactly
  1 unit / 2.5 Å — protein and RNA structures now share absolute units,
  which is mandatory for rung 3 (mixed assembly). Sequential C1′–C1′ =
  6.05 Å = 2.42 model units.
- No engine changes needed: beads are beads. WC pairs ride the cystine
  block (--cystine/--css-k 0.5, R0 from native geometry automatically);
  register torsions off, hbond formation off (--hb-cap 0), hydrophobicity
  zero (nucleotide resnames map to HYDRO 0.0 by default).

## Rung 1+2 — first variants built (2026-08-23)
- rna_hairpin_{0,1,2}.0: T-arm residues 49–65 (17 nt), 5 WC restraints,
  R0 4.22–4.31 units. Zero native contacts (expected: pairs above the 6.5 Å
  contact cutoff — the rung-1 stem test is restraint-only by design).
- rna_trna_{0,1,2}.0: full 76 nt, 21 WC restraints, 6 emergent native
  contacts (stacking-range bead pairs below 6.5 Å — the field's raw
  material for tertiary assembly).
- Pre-registered reads (per plan):
  - Rung 1 pass = all 5 stem pairs hold R0±20% under f25 floor; helical
    rise/twist within 15% of A-form.
  - Rung 2 pass = final bead RMSD < 5.0 units on ≥2/3 seeds AND the elbow
    (D-arm/T-arm contact, e.g. beads 10–14 vs 49–53 centroid distance)
    forms WITHOUT any restraint — the tertiary emergence test. Restrained
    pairs closing does not count; they were given.
- Files verified: NRES 17/76, NCYSPAIR 5/21, hydro all 0.0, block balance.

## Rung 2 build fix (2026-08-23): CYS array bound
tRNA needs 21 WC restraints; template CYS_* arrays were sized 16 (set for
the quad campaign's 12-pair max). Hairpin (5 pairs) compiled fine; tRNA
failed type-check with 20 bound errors. Fix: CYS_I/J/R0/ON widened 16->40
(same headroom as MIS). tRNA variants regenerated, verified. mcl's bounds
checking caught this at compile time — static verification doing its job.

## Rung 1 result (2026-08-23): PASS
Hairpin (17 nt, 5 WC restraints): all pairs hold at final (3.95-4.39 vs
R0 4.22-4.31), RMSD 1.48/2.89/3.36 by seed. The restraint-block-as-base-
pair design works; bead type viable. Stem integrity under sustained load
(f25 floor variant) still available if wanted, but the basic certification
is met.

## Rung 2 result (2026-08-23): FAIL in the predicted direction — over-compaction
All 21 WC pairs hold (final mean 4.26-4.28 vs native 4.25, max dev 0.41)
— secondary structure rock solid. But whole-molecule RMSD 6.46/7.65/8.73
(fail vs 5.0 criterion) and the system COMPACTS HARD: rgyr finals
4.38/5.07/5.64 vs native 9.14 — a 40-50% radius collapse on all seeds. Elbow (D-arm/T-arm centroid, native 9.98): seed 0
4.56 (collapsed shut), seed 1 11.07 (open), seed 2 5.25 (collapsed shut).
Failure mode is exactly the anticipated no-electrostatics roadblock:
nothing pushes backbone beads apart at mid-range, so attractive contacts
win and the arms close past native. 2/3 seeds over-close, 1/3 drifts open
— no stable tertiary plateau.

Physics decision point (needs user approval — new force term): screened
phosphate-phosphate repulsion between backbone beads. Cheapest physical
form: soft mid-range repulsion on sequential-distant pairs (Debye-style
decay), strength/range calibrated so the native elbow sits at equilibrium
— calibration target, not hand-tuning: native rgyr and elbow distance must
be the field's resting state, verified on the hairpin (should be inert:
stem beads are close-range) before tRNA retest.

## Rung 2 follow-up: screened phosphate repulsion term (PHOS) built + validated (2026-08-23)

New engine term, cloned structurally from the steric block:

  E(D) = PHOS_EPS * EXP(-D/PHOS_LAM) / D        (screened Coulomb, per pair)
  F(D) = -dE/dD = PHOS_EPS * EXP(-D/PHOS_LAM) * (D + PHOS_LAM) / (PHOS_LAM * D^2)

- Applies only to |i-j| >= 4 pairs where BOTH beads carry RES_PHOS = 1.0
  (nucleotide backbone beads; generator flags from JSON res_names, UNK -> 0.0,
  so protein chains in mixed JSONs are never charged by accident).
- PHOS_EPS default 0.0 = OFF. No cutoff, no cap, no clamp: the screening
  exponential is the physical range limiter, per project doctrine.
- Included in all four MC energy blocks (MCEBF/MCEAF) for consistency,
  gated identically.

Validation before any run (standing rules):
1. FD gradient check in a C mirror: analytic F vs central-difference -dE/dD,
   D in [0.5, 20] units: max rel err 4e-10. PASS.
2. Regression audit: regenerated waveform_2kqp_trim1_0.0 from the new template
   (PHOS off) — source diff vs the delivered file contains ONLY inert
   additions (PHOS decl/params/flags, BREAK3 guards, CYS/MIS 16->40 widening).
3. Gating oracle built: oracle_phos_trim1_0.0.ergo = trim1 recipe +
   --phos-eps 0.05 --phos-lam 3.1. All 258 beads are protein
   (RES_PHOS = 0.0 everywhere, verified), so the term contributes exactly
   zero force. RUN-LEVEL ORACLE: its CSV must be bitwise identical to the
   completed waveform_2kqp_trim1_0.0 run. Any difference = a bug in the
   new code path, not physics.

Hairpin inertness note (corrected expectation): the term is NOT bitwise
inert on the hairpin — stem C1'-C1' pairs sit at ~4.2 units, inside the
screening reach, so a small finite force exists by design. At PHOS_EPS=0.05,
lam=3.1 the pair-rest shift is ~0.003 units (~0.008 A) against CSS_K=0.5 —
structurally negligible. The bitwise oracle lives on the protein system
(item 3) instead; hairpin check is a structural tolerance read, not bitwise.

### A/B experiment (Tennant-motivated screening comparison)

Same term, same strength (PHOS_EPS = 0.05), two screening lengths:

- std arm: PHOS_LAM = 3.1 units (~7.8 A; Debye length at ~150 mM monovalent
  salt — the standard strong-screening regime)
- ten arm: PHOS_LAM = 8.0 units (~20 A; weak-field / weak-screening regime,
  the "cell voltage is low" side of the comparison)

Six files: rna_trna_phos_{std,ten}_{0.0,1.0,2.0}.ergo
(tRNA 1EHZ, 21 WC cystine pairs K=0.5, no register, hb-cap 0, 96000 frames,
seeds 0/1/2 — identical recipe to the rung-2 failures, only the term added).

Pre-registered reads (vs the rung-2 failure numbers):
1. final rgyr vs native 9.14 (rung 2 collapsed to 4.38/5.07/5.64)
2. elbow distance (D-arm 10-14 vs T-arm 49-53 centroids) vs native 9.98
   (rung 2: 4.56/11.07/5.25)
3. RMSD vs 5.0 pass criterion (rung 2: 6.46/7.65/8.73)
4. WC pair distances must stay ~4.25 (term must not blow the stems open)

Framing, stated plainly: this compares two screening-length regimes of one
repulsion term. It cannot validate or refute Tennant's physiological claims
(redox/pH "voltage" of the cell); it only asks which electrostatic regime
our bead dynamics prefer. Interpretation is limited to that.

## Rung 2 retest with PHOS term: A/B result (2026-08-23) — over-compaction CURED, weak-screening arm preferred

Six runs (std lam=3.1 / ten lam=8.0, EPS=0.05, seeds 0-2), pre-registered reads:

| run | final rgyr (native 9.14) | final RMSD (pass <= 5.0) | elbow (native 9.98) | WC mean |
|---|---|---|---|---|
| rung2 no term | 4.38 / 5.07 / 5.64 | 6.46 / 7.65 / 8.73 | 4.56 / 11.07 / 5.25 | 4.26 |
| std (lam 3.1) | 6.06 / 7.18 / 6.99 (mean 6.74) | 7.37 / 7.90 / 6.16 | 8.06 / 16.77 / 4.75 | 4.25 |
| ten (lam 8.0) | 7.06 / 8.85 / 7.50 (mean 7.80) | 7.39 / 8.21 / 6.61 | 8.22 / 20.03 / 4.95 | 4.26 |

1. Over-compaction gone in both arms: rgyr 74% (std) / 85% (ten) of native
   vs 48-62% without the term. Diagnosis from rung 2 confirmed: the missing
   mid-range backbone repulsion WAS the collapse driver.
2. Stems intact: all 21 WC pairs 3.99-4.55 across all six finals. The term
   scaffolds without disrupting base pairs (pair-rest shift negligible, as
   predicted at EPS=0.05).
3. A/B verdict: weak-screening (ten) arm wins the primary read — mean rgyr
   7.80 vs 6.74, and every ten seed beats its std counterpart individually.
   RMSD/elbow are a wash between arms. Interpretation strictly limited to
   "our bead dynamics prefer the longer screening length"; no physiological
   claim tested.
4. Still no RMSD <= 5.0 pass (best 6.16). Remaining failure mode is
   conformational, not collapse: elbow scatter 4.75-20.03 across seeds in
   BOTH arms (one collapsed, one over-extended, one ~native per arm).
   Next levers: modest EPS increase on ten arm, or explicit stacking term
   (physics addition — awaiting user decision).

Oracle status: CLOSED as source-audited (2026-08-23). The user's original
MIDY trimer CSVs no longer exist, so no bitwise reference is available.
Verification rests on (a) the FD gradient check, (b) the source diff showing
the new path contributes exactly zero force when all RES_PHOS = 0 (the
protein case), and (c) WC pairs / protein-side behavior unchanged in all
six delivered runs. oracle_phos_trim1_0.0.ergo remains in the folder if a
reference ever resurfaces.

## EPS ladder on the winning arm built (2026-08-23)

Six files: rna_trna_phos_ten_{e10,e20}_{0.0,1.0,2.0}.ergo — ten arm
(lam=8.0) with PHOS_EPS 0.10 and 0.20 (2x / 4x the A/B value).
Identical recipe otherwise (21 WC pairs K=0.5, no register, 96000 frames).

Pre-registered read: same four reads as the A/B. Known trade being tested:
higher EPS should rescue the collapsed-elbow seed (4.95 at EPS 0.05) but
worsen the over-extended one (20.03). If e10 pulls the collapsed seed up
without pushing the extended one past ~25, strength was the missing lever;
if both elbows degrade outward, strength is NOT the limiter and the missing
piece is directional (stacking) — that conclusion would motivate the
stacking-term proposal, which still awaits explicit user approval.

## EPS ladder result (2026-08-23): strength is NOT the limiter — stacking term proposed

ten arm (lam=8.0) at EPS 0.05 / 0.10 / 0.20, seeds 0-2, pre-registered reads:

| arm | rgyr (native 9.14) | RMSD finals | elbows (native 9.98) | WC |
|---|---|---|---|---|
| e05 | 7.06 / 8.85 / 7.50 (mean 7.80) | 7.39 / 8.21 / 6.61 | 8.22 / 20.03 / 4.95 | 4.26 |
| e10 | 7.53 / 10.51 / 9.27 (mean 9.10) | 8.72 / 8.45 / 7.37 | 7.85 / 22.51 / 13.38 | 4.30 |
| e20 | 10.14 / 11.90 / 11.83 (mean 11.29) | 8.86 / 9.17 / 9.70 | 12.62 / 27.60 / 23.38 | 4.33 |

1. Size is a solved dial: rgyr monotonic in EPS (7.80 / 9.10 / 11.29);
   e10 mean 9.10 = native 9.14 almost exactly.
2. RMSD degrades monotonically with EPS (best 6.61 -> 7.37 -> 9.70):
   isotropic repulsion buys size by pushing AWAY from the native fold.
3. Elbow trade went to the pessimistic branch: collapsed seed rescued
   (4.95 -> 13.38 -> 23.38, straight through native) while the extended
   seed worsened (20.0 -> 22.5 -> 27.6). No EPS puts all elbows near 9.98.
4. Conclusion per pre-registration: the missing piece is DIRECTIONAL.
   Base stacking is still only implicit in the Go map; isotropic repulsion
   cannot encode D-arm/T-arm stack orientation.

DECISION (field setting): weak-screening regime confirmed as the working
field — lam=8.0, EPS 0.05-0.10 window (0.05 default for structure runs,
0.10 when size is the priority). A/B + ladder documented above.

PENDING USER APPROVAL (new physics): explicit base-stacking term —
directional restraint between consecutive base plane normals. Would be
built to the same standard as PHOS (cloned structure, FD gradient
validation in C mirror, inertness audit) before any run. Spec on request.

## Stacking via the oriented-ribbon field: APPROVED + built (2026-08-23)

User approved directional/orientational forces ("tiny memory springs").
No new physics was needed: the engine already carries a certified
Cosserat-ribbon field (per-residue orientation quaternions + angular
velocities; FRAME_K neighbor alignment torque to native relative Frenet
frames; FRAME_POS_K orientation->position coupling via native bond
vectors). It was mirror-first certified during the multidomain campaign
(native fixed point max 1.2e-5, FD to 1e-5, torque sign verified) and
calibrated there: K=0.5 winds up (post-quench limit cycle), K=0.1/0.1
clean. All prior RNA runs had it OFF (0.0); generated files already carry
the emitted native frames.

Stacking interpretation: FRAME_K keeps consecutive backbone segments at
their native RELATIVE orientation — for an RNA helix that is exactly
coaxial stacking (base-pair plane registration), which is the missing
directionality the EPS ladder pointed at.

Three files: rna_trna_stack_f01_{0.0,1.0,2.0}.ergo — ten-arm field
(PHOS_EPS=0.05, PHOS_LAM=8.0) + FRAME_K=0.1, FRAME_POS_K=0.1 (certified
protein values), seeds 0-2, else identical to the A/B recipe.

Pre-registered reads:
1. Same four reads (rgyr vs 9.14, RMSD vs 5.0, elbow vs 9.98, WC ~4.25),
   against the ten e05 arm as the control (7.06/8.85/7.50 rgyr,
   7.39/8.21/6.61 RMSD, 8.22/20.03/4.95 elbow).
2. Wind-up watch (known failure mode from the protein certification):
   late post-quench e_native / rgyr climb = torque limit cycle -> K too
   stiff for RNA; fix is the certified taper-to-zero-by-quench anneal,
   NOT a cap.
3. Elbow scatter is the decision read: if the field supplies the missing
   directionality, the 4.75-20.03 spread should collapse toward 9.98.

## Rung 2 retest with ribbon field: PASS (2026-08-23) — 2/3 seeds under criterion

ten-arm field (EPS 0.05, lam 8.0) + FRAME_K=0.1, FRAME_POS_K=0.1, seeds 0-2:

| seed | RMSD (<=5.0) | rgyr (9.14) | elbow (9.98) | WC |
|---|---|---|---|---|
| 0.0 | 4.45 PASS | 7.00 | 6.86 | 4.27 |
| 1.0 | 4.87 PASS | 7.80 | 6.03 | 4.33 |
| 2.0 | 6.24 | 6.38 | 6.05 | 4.29 |
| control (no springs) | 7.39 / 8.21 / 6.61 | 7.06 / 8.85 / 7.50 | 8.22 / 20.03 / 4.95 | 4.26 |

1. RMSD decisive: 2/3 pass vs 0/3 control; third seed close (6.24 vs 6.61).
   EPS-ladder attribution confirmed: directionality was the missing piece.
2. Elbow scatter collapsed per pre-registration (4.95-20.03 -> 6.03-6.86).
3. No wind-up: e_native flat 0.2 -> 0.2/0.3 across quench, all seeds.
   K=0.1 as calm for RNA as certified for protein.
4. Stems intact (WC 4.27-4.33, max 4.89).

Residual (honest): elbow converged SYSTEMATICALLY CLOSED (~6.2 vs 9.98),
rgyr mean 7.1 slightly below field-only 7.8. Orientation registers
correctly; the L-corner sits too bent. Calibration question, not
missing-force: cheapest probes are EPS 0.025 at same K, or K=0.2 with
wind-up watch armed.

RUNG 2 CERTIFIED PASS. Working recipe for RNA going forward:
WC cystine pairs K=0.5 + PHOS (EPS 0.05, lam 8.0) + ribbon field
(0.1/0.1). Next: rung 3 = 5S rRNA + L5/L18/L31 (first mixed RNA-protein
assembly; RES_PHOS flagging + absolute 2.5 A/unit scale become load-bearing).
Elbow calibration polish optional, user decides order.

## Elbow-polish sweep built (2026-08-23)

Factorial around the certified point: PHOS_EPS {0.025, 0.05} x FRAME_K=
FRAME_POS_K {0.1, 0.2} x seeds 0-2, lam=8.0 throughout. The e05/f01 cell
is the certified pass (already run); 9 new files:
rna_trna_stack_{e025f01,e05f02,e025f02}_{0.0,1.0,2.0}.ergo

Pre-registered decision rule:
- WIN cell: elbow moves from ~6.2 toward 9.98 AND RMSD stays <=5.0 AND
  no wind-up (post-quench e_native climb; f02 is the risk cell per the
  protein certification — K=0.5 wound up there; 0.2 is untested).
- If e025 opens the elbow without losing RMSD: field was slightly strong.
- If f02 closes RMSD 2.0 without wind-up but elbow stays ~6: the L-corner
  geometry lives in the positional spring, and we'd probe FRAME_POS_K
  decoupled from FRAME_K next.
- Elbow target band: 8-12 (native 9.98); anything inside with RMSD pass
  counts as polished.

## Elbow-polish sweep result (2026-08-23): both global levers exhausted, certified cell stands

| cell | RMSD finals | elbows | wind-up |
|---|---|---|---|
| e05/f01 (certified) | 4.45 / 4.87 / 6.24 | 6.86 / 6.03 / 6.05 | none |
| e025/f01 | 6.11 / 5.14 / 6.46 | 5.38 / 6.74 / 4.16 | none |
| e025/f02 | 5.51 / 4.70 / 7.53 | 6.01 / 6.31 / 3.48 | none |
| e05/f02 | 5.51 / 5.43 / 6.29 | 6.90 / 7.07 / 3.18 | none |

1. Certified e05/f01 remains the best cell: only cell with two sub-5.0
   RMSD passes, ties best elbows. Sweep confirms it was not luck.
2. EPS 0.025 LOST the RMSD pass without opening the elbow: the field at
   0.05 helps the fold; field strength was never the elbow clamp.
3. K 0.2: no wind-up anywhere (RNA calmer than the protein certification
   feared at 0.5), slightly better elbows on seeds 0/1, but RMSD off pass.
4. Seed 2 elbow collapses (3.18-4.16) in ALL FOUR cells: parameter-
   independent kinetic trap — that seed's D/T arms close wrongly early.
5. Decision tree: residual lives in FRAME_POS_K (positional spring clamps
   the L-corner) OR ~6.2 is the one-bead-per-nt resolution limit at the
   corner. Decisive cheap probe: FRAME_K 0.1 / FRAME_POS_K 0.0, 3 seeds.
   Elbow opens -> positional spring was the clamp; stays ~6 -> resolution
   limit, bank and climb to rung 3.

## FRAME_POS_K decoupling probe (2026-08-23): orientation's channel identified; elbow banked as resolution limit

fkonly (FRAME_K 0.1, FRAME_POS_K 0.0), seeds 0-2:
RMSD 7.39 / 8.21 / 6.61, rgyr 7.06 / 8.85 / 7.50, elbow 8.22 / 20.03 / 4.95
— BIT-FOR-BIT the field-only control (ten e05). FRAME_K alone has ZERO
positional effect: the torque spring drives angular velocity, which reaches
the backbone ONLY through FRAME_POS_K. Orientation without the positional
coupling is pure gauge (the multidomain-campaign lesson, now confirmed on
RNA by a perfect accidental control).

Causal chain closed: ALL improvement (RMSD passes, elbow convergence)
flows through FRAME_POS_K, and the systematic ~6.2 elbow is that spring's
equilibrium against Go map + field at one-bead-per-nt resolution. Not a
clamp that can be loosened without losing the fold; not a missing force.
Representation limit at the L-corner. BANKED.

RUNG 2 FINAL — certified recipe:
WC cystine pairs K=0.5 + PHOS (EPS 0.05, LAM 8.0) + ribbon field
FRAME_K = FRAME_POS_K = 0.1. RMSD 4.45 / 4.87 / 6.24 (2/3 pass),
WC 4.27-4.33, no wind-up, elbow 6.0-6.9 (understood, resolution-limited).

NEXT: Rung 3 — 5S rRNA (~120 nt) + L5/L18/L31. First mixed RNA-protein
system: RES_PHOS flagging and absolute 2.5 A/unit scale (json
mean_ca_ca=3.8 hack) become load-bearing. First co-folding test.

## Rung 3 built (2026-08-24): 5S RNP from mature human 80S (6QZP) — first mixed RNA-protein system

Source decision: user offered 8IPX (human pre-60S State C) and 6QZP
(mature human 80S). 8IPX's 5S geometry is compressed (WC C1'-C1' 8.3-9.2 A
vs canonical 10.3-10.9 — model rebuilt in immature context), so geometry
was taken from 6QZP: chains L7 (5S rRNA, 120 nt; MG201-203 are magnesium
ions, not nucleotides), LJ (uL5/RPL11, 176 aa), LD (uL18/RPL5, 293 aa).
589 beads total, chain breaks 120 / 296, chain-sep 8 (triangle start).

WC pairs: 44, geometry-derived from 6QZP (window 9.8-11.5 A C1'-C1',
greedy unique assignment), runs matching canonical 5S helices I-V.
Template CYS arrays widened 40 -> 64 (44 pairs; mcl static bounds checker
would have caught it otherwise — it did its job twice before).

Recipe: certified rung-2 settings (css-k 0.5, no register, hb-cap 0,
PHOS 0.05/8.0, ribbon 0.1/0.1, maxframe 96000), seeds 0/1/2.
RES_PHOS: 1.0 on exactly the 120 RNA beads, 0.0 on all 469 protein beads
(verified in generated source). Hydrophobic weights on protein beads only.
Absolute scale locked via json mean_ca_ca=3.8 (scale 0.4 = 2.5 A/unit).

Pre-registered reads (native references from 6QZP):
1. Per-chain RMSD (rmsd_c1=5S, c2=uL5, c3=uL18) vs 5.0 each.
2. Global rgyr vs native 13.13 model units.
3. 44 WC pair distances vs native 9.96-11.50.
4. Interface recovery: fraction of native inter-chain contacts (<6.5 u)
   with final D <= 1.3x native. Native counts: 5S-uL5 506, 5S-uL18 1444,
   uL5-uL18 169.
5. Wind-up watch (e_native post-quench).
Runtime warning: 589 beads is ~60x the tRNA pair count; expect much
longer runs than rung 2.

Files: rna5s_rnp_{0.0,1.0,2.0}.ergo + 6qzp_5srnp.json/.pdb (extraction).

## Rung 3 attempt 1 (2026-08-24): FAIL by misconfiguration — inter-chain Go never fired

Attempt 1 (rna5s_rnp_0/1/2): per-chain RMSD 5S 5.70/9.15/5.55,
uL5 5.91/5.89/5.23 (consistently near pass), uL18 8.30/9.51/13.42;
WC stems perfect (4.18-4.22 vs native ~4.2); interface recovery 0.00;
COM separations 1.5-2.5x native.

Root cause: DOCK_FROM defaulted to 2e9 (never). Inter-chain Go contacts
are gated off by design until --dock-from; I never passed it, so the
three chains folded with ZERO inter-chain attraction for the whole run.
The MIDY trimers never exposed this (mispair restraints WERE the
inter-chain force; reads were per-chain). Config miss, not physics.

Attempt 2 built: rna5s_rnp_d48_{0.0,1.0,2.0}.ergo — identical except
--domains 1-120,121-296,297-589 --dock-from 48000 (chains fold solo
first half, inter-chain Go switches on at 50%).

Pre-registered reads (same native refs): per-chain RMSD vs 5.0, rgyr vs
13.13, WC vs ~4.2, interface recovery (0% in attempt 1 — any nonzero
recovery validates the docking channel), wind-up watch. Note: 48k frames
post-gate may be short for docking 589 beads; if interfaces start forming
but incompletely, the lever is MAXFRAME, not physics.

## Rung 3 attempt 2 (d48): bitwise-null — gate opened onto an empty contact list (2026-08-24)

d48 runs came out IDENTICAL to attempt 1 (rgyr 17.85/14.64/23.10 etc).
Root cause, deeper layer: the generator's chain-break handler STRIPS all
native contacts crossing a break (MIDY design: chains independent, the
mispair weapon was the only inter-chain force). So there were no
inter-chain contacts for DOCK_FROM to ungate ("Fold-then-dock: 0
inter-domain"). Two stacked config misses, both traced to MIDY-era
assumptions.

Fix (generator feature, no engine physics change): new flag
--keep-inter-contacts — keeps native Go contacts across chain breaks;
with --domains they are marked CONTACT_INTER=1 and gated until
--dock-from as designed. Default off = MIDY behavior unchanged (all prior
multichain files regenerate identically).

Attempt 3 built: rna5s_rnp_asm_{0.0,1.0,2.0}.ergo — keep-inter-contacts +
domains + dock-from 48000. 55 inter-domain contacts gated (generator
contact cutoff 6.5 A: these are the tight physical interface; the 2119
figure quoted earlier was a loose 16 A halo count — reference corrected).
Native interface contact distances 2.0-2.5 model units (5-6.4 A).

Pre-registered reads unchanged: per-chain RMSD vs 5.0, rgyr vs 13.13,
WC vs ~4.2, interface recovery (now a meaningful read), wind-up watch.

## Rung 3 attempt 3 (asm): DOCKING CERTIFIED, per-chain fold quality is the residual (2026-08-24)

| seed | rgyr (13.13) | 5S | uL5 | uL18 | interface (55 tight) | COM seps (15.9/11.4/15.5) |
|---|---|---|---|---|---|---|
| 0.0 | 11.40 | 4.94 PASS | 5.26 | 7.80 | 55/55 = 100% | 19.1/12.1/14.0 |
| 1.0 | 10.09 | 11.79 | 5.81 | 8.22 | 55/55 = 100% | 12.8/5.5/17.4 |
| 2.0 | 12.22 | 8.32 | 7.01 | 9.19 | 55/55 = 100% | 10.4/13.9/20.3 |

1. Interface recovery 100% in all seeds: fold-then-dock channel certified
   on a real mixed RNA-protein assembly. THE rung-3 question answered YES.
2. WC stems perfect (4.17-4.20), no wind-up, global size 10.1-12.2 vs
   13.13 (slightly compact = interface satisfied).
3. Residual red: per-chain folds DEGRADED vs solo (5S solo 5.70/9.15/5.55
   -> asm 4.94/11.79/8.32; uL18 7.8-9.2). Chains fold imperfectly in the
   48k solo phase, then the interface locks the imperfections in.
   Pre-registered read: frames problem, not physics.

Attempt 4 built: rna5s_rnp_long_{0,1,2}.0.ergo — MAXFRAME 192000,
dock-from 96000 (same 50% gate fraction, double runway both phases).
Prediction: uL18 (293 aa) is the chain to watch; if it improves with
runway while interfaces stay 100%, rung 3 passes at 192k and the GPU
conversation becomes load-bearing for rung 4 (28S Domain V is bigger).

## Rung 3 attempt 4 (192k): runway NOT the limiter; uL18 plateaus at ~8 (2026-08-24)

long runs: 5S 5.43/8.41/8.49, uL5 5.36/5.13/5.04 (mid-size chain
converged with runway), uL18 8.31/7.80/9.07 — unmoved vs solo
(8.30/9.51/13.42) and vs 48k gate (7.80-9.19). Interfaces held 55/55
everywhere. No wind-up.

Size trend across campaign: 76nt tRNA 4.5, 86res proinsulin pass,
120nt 5S marginal (5-8.5), 176aa uL5 ~5.1, 293aa uL18 ~8. Fold quality
degrades with chain size under the 0.1/0.1 ribbon recipe.

Probe built: ul18_solo_f02_{0,1,2}.0.ergo — uL18 alone, protein recipe,
FRAME_K=FRAME_POS_K=0.2 (RNA tolerated 0.2 without wind-up in the tRNA
sweep), 96k frames. Decision rule: uL18 drops toward 5-6 -> stiffness is
the big-chain dial, re-run assembly at 0.2; stays ~8 -> certified
representation plateau for ~300-bead chains, bank rung 3 as
"assembly YES, fold quality scales with size" and carry it into rung-4
planning (GPU + possibly per-chain stiffness).

## uL18 solo K=0.2 probe: plateau is intrinsic — RUNG 3 BANKED (2026-08-24)

ul18_solo_f02: 8.26 / 11.50 / 8.03. Same ~8 plateau as K=0.1, as gated
assembly, as solo. Trajectories: seed 0 at 7.74 by frame 24k, never moves
— early collapse into a wrong basin, then frozen. Not kinetics, not
stiffness, not instability (no wind-up, e_native calm). Go-map folding
limit at ~300 beads under the current recipe.

RUNG 3 FINAL — ASSEMBLY CERTIFIED, FOLD QUALITY SIZE-LIMITED:
- Mixed RNA-protein co-assembly WORKS: 55/55 interface contacts in every
  assembly run (4 independent configs x 3 seeds), COM geometry
  near-native, WC stems exact, no instability. Fold-then-dock certified.
- Fold quality vs size (certified recipe): 76nt 4.5 / 86res pass /
  120nt 5-8.5 / 176aa ~5.1 / 293aa ~8. ~1 RMSD unit per ~75 beads;
  unresponsive to frames (96k vs 192k) and stiffness (0.1 vs 0.2).

Implication for rungs 4-6 (28S Domain V ~400+ nt; subunits 1000s of
beads): longer solo runs of the current recipe will not climb them.
Candidate strategies for user decision: (a) GPU + many seeds — basin
scatter is partly stochastic (5.4-11.8 same chain), best-of-N buys
folds; (b) hierarchical assembly — fold domains separately, dock as
rigid bodies via the certified MC/gate machinery (matches biology:
modular biogenesis); (c) both. AWAITING USER DIRECTION before any
rung-4 build.

## Contact-layer (second-shell) orientation coupling: HYPOTHESIS + BUILD (2026-08-24)

User hypothesis (complexity inversion): the ~300-bead plateau is not
kinetics/stiffness — the sequential-neighbor orientation layer is
SATURATED and larger chains need the next coordination shell oriented.
The Go contacts (spatial neighbors) pull positions together with zero
orientational memory, so contacts can close in the wrong rotational
register and freeze (explains: early freezing at 24k, insensitivity to
frames and stiffness, smooth degradation with contact count).

Build (approved by user's directive; extends the certified quaternion
scaffold, no independent new physics):
- New term FRAME_CL_K: for each native contact pair (i,j), bead j pulled
  toward p_i + R(q_i).v*_ij, v*_ij = native contact vector in i's local
  Frenet frame. Packed CL arrays (MAXCL 1024), NCL param. Respects the
  CONTACT_INTER/DOCK_FROM gate for inter-domain contacts.
- Generator emits CL data always (inert; force gated by FRAME_CL_K=0
  default) — same pattern as NATIVE_Q/BV.

Validation (standing gates, all PASS):
1. FD gradient in C mirror (E = 0.5 K |p_j - p_i - R(q)v*|^2, q fixed as
   in code): max rel err 6e-8 on both beads. PASS.
2. Native fixed point: max |F| = 0 exactly. PASS.
3. Emitted-data audit: R(q_i).CL_V reconstructs p_j - p_i to 4.5e-6
   (6-decimal rounding). PASS.
4. Regression audit: trim1 regenerated from new template — diff is inert
   additions only (CL data, PHOS blocks, BREAK3 telemetry). PASS.

Probe built: ul18_solo_cl01_{0,1,2}.0.ergo — uL18 solo, 96k, certified
springs 0.1/0.1 PLUS FRAME_CL_K=0.1 (246 contact-layer pairs).
Decision rule: RMSD breaks below the ~8 plateau toward 5 -> second-shell
orientation was the missing layer (user's inversion confirmed), carry
FRAME_CL_K into the assembly recipe and rerun rung 3; stays ~8 ->
hypothesis falsified at this coupling strength, one K-sweep (0.2) before
abandoning, then bank plateau.

## CL probe at K=0.1 (2026-08-24): plateau cracked, not broken — 0.2 arm running

ul18_solo_cl01: 8.64 / 11.22 / 6.88.
- Seeds 0/1: wash vs plateau (8.26/11.50 at f02) — still frozen by 12-24k.
- Seed 2: 6.88 = best uL18 fold ever (prior best 8.03), and the ONLY
  uL18 trajectory that never froze: monotone descent 7.99 -> 6.88
  through the quench. The contact-layer term changed the SHAPE of the
  search on that seed, not just the number.
Verdict per pre-registration: hypothesis not confirmed at 0.1; the
pre-registered 0.2 arm is live (seed-2 evidence, not formality).
Built: ul18_solo_cl02_{0,1,2}.0.ergo. If 0.2 breaks multiple seeds below
~7 with unfrozen trajectories, inversion confirmed; else bank.

## CL probe at K=0.2 (2026-08-24): complexity-inversion hypothesis FALSIFIED as operationalized

ul18_solo_cl02: 8.62 / 11.60 / 7.82. Seed 2's unfrozen 6.88 at K=0.1 did
NOT reproduce (7.82); seeds 0/1 flat washes at both strengths. e_native
9.6-12.3 at 0.2 vs 4.9-6.3 plain springs: at these strengths the contact
layer fights the Go map rather than cooperating. One seed folding one
unit deeper once = anecdote, not mechanism. Per pre-registration:
FALSIFIED. FRAME_CL_K remains in template (off, fully validated).

Half-credit to the intuition: the contact layer IS the missing dimension
— but orientational springs are not the right reorientation. The
untested layout-level option (and the biological one): hierarchical
fold-then-dock — fold domains solo (each under the size wall), dock as
rigid bodies via certified MC machinery. uL18-size chains are exactly
where the cell does this too.

LADDER STATE: certified = tRNA-scale folds (<=~180 beads), mixed
RNA-protein docking 100% interface recovery; measured scaling ~1 RMSD
per ~75 beads past ~180; falsified = frames/stiffness/CL-springs as
plateau-breakers. LIVE OPTIONS for rung 4: (a) hierarchical domain
assembly (recommended), (b) GPU + best-of-N statistics. AWAITING USER
DIRECTION.

## State A (8IR1) vs State C (8IPX): biogenesis reshape measured (2026-08-24)

User suggestion: diff the assembly states for hints. Extraction: 8IR1
(State A) chains W=5S(120nt), A=uL5(165aa), C=uL18(248 of 293 modeled);
8IPX (State C) chains 3=5S(115nt), C=uL5(165), R=uL18(293).

Results:
1. Proteins STATIC across states: uL5 1.07 A, uL18 1.38 A (aligned on
   common residues). The cell folds these proteins FIRST, separately;
   no co-folding with RNA.
2. 5S rRNA in the protein frame: 6.28 A RMSD A->C, concentrated in nt
   73-98 (helix IV/V + loop E): 4.4-9.2 A displacements, 19 A swing at
   nt 88. Dock first (arm in "pre" pose), reshape the arm AFTER.
3. WC geometry mature in both states (A 10.90 / C 10.80 / mature 10.58 A
   on the 6QZP-derived 44-pair list): stems never open; the reshape is
   rigid-arm reorientation, not refolding.

ERRATUM: the earlier "8IPX 5S compressed (8.3-9.2 A)" claim was an
artifact of greedy pair derivation locking non-WC contacts. Against the
proper pair list, 8IPX is normal. 6QZP remained the right pick (most
complete chains).

Design hints extracted:
- Hierarchical assembly (fold solo -> dock as units -> reshape locally)
  is the OBSERVED cellular mechanism, not a fallback. Endorses rung-4
  option (a).
- Rung-3's "every chain <= 5.0" criterion is stricter than biology: a
  REAL intermediate sits 6.3 A from mature. Per-region reads (core vs
  arm) are the fairer mirror.
- Keep the flexible arm (nt 73-98 analog) LESS restrained during docking
  — cell keeps it plastic until the interface forms. Our recipe already
  restrains stems only; loops/arms free. Accidentally correct.

---

## 2026-08-24 — GPU pair-force restructure (Kimi Code) — mirror verification PASSED

Kimi Code delivered the GPU restructure as a working patch set:
`waveform_template.ergo` (unified pair-slot form), `generate_protein_ergo.py`
(PSEG/NSLOT patching), `retemplate.py` (splices new physics into any
delivered .ergo without json/pdb), `mk_seed_variants.py`, `bestofn_run.py`
(serial GPU runner, `--target spirv --precision f32`), `bestofn_analysis.py`
(pre-registered R1-R3 best-of-N basin statistics), `extract_28s_d5.py` +
`build_d5_variants.py` + `d5_analysis.py` (rung-4 28S Domain-V region,
hierarchical fold-then-dock vs monolithic, pre-registered P1-P3).

### The design (as implemented)
All four N^2 pair terms (steric, PHOS, hydro, Go contacts) unified into ONE
padded slot list, evaluated in SIX straight-line loops (i-side + j-side, one
per Cartesian component). Atom a owns slots [(a-1)*PSEG+1, a*PSEG]; PSEG =
256*ceil((NRES-3)/256) — exactly the segmented-reduction V1 geometry
(compile-time bound, bound % nseg == 0, segment length % 256 == 0).
All gates baked to exact 0/1 arithmetic masks at init (WST hbond exclusion,
WPH charge product, WHY hydro product, WCO/WCI/CR0 contact data); the dock
gate is branchless: DOCKM = (1 - SIGN(1, DOCK_FROM - FRAME))/2. Newton's
third law via the j-major table (pair appears once in each owner's segment).
Cystine arrays widened 64 -> 192 for rung-4 WC lists.

### Mirror verification (verify_gpu_pairform.py, this session)
1. **Force equivalence, old branched form vs new mask form** (N=60 random
   config, all terms on, hbond pair, phos/hydro flags, inter-domain contact,
   dock gate closed AND open): max abs diff 2.7e-20, max rel 8.1e-15 —
   pure f64 reassociation. The masks reproduce every branch exactly,
   including strict cutoffs (SIGN(1,0)=+1 keeps D=CUT excluded) and the
   FRAME==DOCK_FROM edge (gate open only for FRAME > DOCK_FROM, matches).
2. **FD validation of the new form** vs documented per-term energies:
   abs agreement 2.0e-10, residue sits at the f64 FD cancellation floor
   (analytic force stable across eps; error shrinks with LARGER eps —
   noise, not signal). PASS.
3. **D=0 corner** (exact bead overlap on a real pair, and pad slots):
   BENIGN. The DD=1e-30 floor keeps FM finite (worst case steric
   ~6e179, PHOS ~5e58 — both << f64 max), and an exact overlap has
   DX=DY=DZ=0, so the contribution is FM*0 = 0 exactly — identical to
   the old form's D>0 gate. No NaN path. No fix needed.
4. **Slot coverage audit**: i-major J=I+2+T covers sep>=3 (contacts need
   >=3, steric/PHOS/hydro masked to >=4 by weights); j-major T<=b-3
   identical coverage; pad slots (J>N or T>b-3) are self-pairs with all
   weights zero. No pair missed, none double-counted within a side.

### What this means for certification
- CPU-old vs CPU-new trajectories will NOT be bitwise-identical
  (per-atom summation order changed: component-pass + term-folded vs
  term-loop + per-pair six-component). Both are deterministic; the
  mirror proves forces agree to 1e-15 rel per step. Statistical
  equivalence (basin distributions) is the certification standard for
  the retemplated files; the pre-restructure certified results
  (rung 2 PASS, rung 3 docking 55/55) stand on the old form.
- GPU-vs-CPU bitwise identity was already impossible (transcendental
  policy); GPU runs are additionally f32 (`--precision f32`).
  Oracles are GPU-vs-GPU; CPU remains the physics reference.

### Open items on the Kimi Code local compiler patch (need the sources)
bestofn_run.py invokes `python -m core <v> --target spirv --precision f32`
— neither flag exists in the ir_gpu.py we reviewed. Request the patched
ir_gpu.py (+ codegen if touched) and review:
  a. SIGN intrinsic lowering to SPIR-V (the masks depend on it).
  b. `--precision f32` semantics — which arrays/ops go single precision.
  c. **Segmented-accumulate initial value**: our loops accumulate onto
     LIVE velocities (RES_V* carries across frames; it is NOT zeroed
     before the force pass). The lowering must ADD the segment partial
     sums to the existing accumulator value, not overwrite it. This is
     the one place a silent physics bug could hide — verify first.
  d. MC energy loops / cystine / ribbon / CL remain branched -> CPU
     fallback -> per-frame host<->device sync. Correct but sets the
     performance floor; confirm that's the intended V1 shape.
- retemplate.py docstring says "5 chains" for the hierarchical variant;
  nsub=4 gives 4 chains/3 breaks (within the engine limit). Comment-only.

### Performance notes (rung-4 sizing)
- NSLOT = NRES * PSEG. NRES=589 -> PSEG 768, NSLOT 452k. NRES=2000 ->
  PSEG 2048, NSLOT 4.1M -> 14 REAL + 3 INTEGER arrays ~ 500 MB;
  expect `--arena-size 2G` on CPU builds of retemplated variants.
- EXP now evaluates unconditionally per slot per component pass:
  ~20x more transcendental work than the branched CPU form. CPU
  regression runs get slower; GPU doesn't care. This is the price of
  straight-line extraction bodies and it's the right trade.

### Rung-4 campaign shape (endorsed, pre-registered by Kimi Code)
- extract_28s_d5.py: geometry-derived segmentation of 28S (6QZP chain
  L5) — long-range contact density minima, gap-clean 550-nt window,
  4 sub-domains of ~90-180 nt (under the measured ~180-bead wall).
  JSON convention mean_ca_ca=3.8 (scale 0.400) — matches the certified
  mixed-system calibration. C1' extraction matches rung-0/2/3.
- build_d5_variants.py: certified RNA recipe (css-k 0.5, hb-cap 0,
  PHOS 0.05/8.0, ribbon 0.1/0.1, 96k frames) x {solo sub-domains,
  monolithic, hierarchical (domains + dock-from 48000 +
  keep-inter-contacts, intra-domain WC only)} — the State-A->C
  hierarchical mechanism tested head-to-head against the wall.
- d5_analysis.py P1-P3 and bestofn_analysis.py R1-R3 pre-registered
  reads reviewed and endorsed as written. P3 (composition ratio
  mean-subdomain/mono and hier/mono) is the complexity-inversion
  measurement the user hypothesized: ratio < 1 with passing sub-domain
  folds = the inversion structure is real and exploitable.

### 2026-08-24 (cont.) — compiler patch review: SIGN / f32 / segmented accumulate — ALL CLEAR

Reviewed the Kimi Code compiler patch set (spirv.py, ir_codegen.py,
codegen.py, __main__.py, nodegraph.py — ir_gpu.py itself unchanged;
the SPIRV lowering lives in spirv.py + the host orchestration in
ir_codegen.py):

a. **SIGN lowering (spirv.py 2672)**: CORRECT Fortran semantics —
   |a| * (b >= 0 ? +1 : -1) via OpSelect, with an explicit comment
   that GLSL sign(b)=0 at b=0 would break the arithmetic masks.
   This is exactly the strictness the mask construction depends on
   (SIGN(1.0, 0.0)=+1 keeps D=CUT excluded; DOCKM closes at
   FRAME==DOCK_FROM). One residual nuance: b = -0.0 compares as
   0 <= -0.0 -> +1 on GPU, while gfortran copysign gives -1; in our
   masks this only arises at D=+0.0, where the contribution is zero
   either way (verified in the mirror). Physically inert.
b. **--precision f32 (__main__.py 91, ir_codegen.py _c_type)**:
   whole-program switch — host C compiles REAL as float too, device
   buffers and the host combine all match. Deterministic, consistent
   f32 everywhere; GPU oracles are GPU-vs-GPU at f32 as documented.
c. **Segmented accumulate onto live state — THE CRITICAL ONE — is
   CORRECT by construction**: the device kernel intercepts the
   accumulator LOAD as additive identity (spirv.py 2203-2210), the
   per-thread body therefore yields just `expr`; workgroup tree
   combine writes one partial per group; the HOST then does
   `ACC[_j / _Gseg] += partial[_j]` in group order
   (ir_codegen.py 4091/4129) — i.e. new ACC = OLD ACC + ordered
   segment sum, exactly the CPU semantics of the RMW loop. Live
   velocities survive the force pass. F98 handling: if the
   accumulator is GPU-resident (e.g. an extracted zeroing loop wrote
   it), the host downloads it BEFORE combining and uploads the
   combined values AFTER (ir_codegen.py 4057-4073, 4154-4156).
d. Performance floor confirmed: every segmented force kernel does a
   device->host partials download + host combine + host->device
   upload; with 6 force kernels per substep plus CPU-fallback loops
   (cystine/ribbon/MC) the per-frame transfer count is the V1
   bottleneck. Correct first, fast later.

**Verdict: the GPU path is certified for the pair-force physics from
the compiler side.** Remaining certification gate before rung 4 data
is trusted: one 76-bead tRNA GPU-vs-CPU cross-check (same variant
built both ways; expect trajectory divergence at the f32/f64 noise
floor, compare basin-level statistics: final RMSD/rgyr distributions,
not trajectories).

### 2026-08-24 (cont.) — GPU certification cross-check PACKAGE DELIVERED

Variants: trna_gpu_{0,1,2}.ergo — the certified rung-2 tRNA recipe
(76 beads, WC 21 pairs css-k 0.5, hb-cap 0, PHOS 0.05/8.0, ribbon
0.1/0.1, 96k frames) regenerated in the unified slot form with the
Kimi Code generator. Pre-delivery audit: ALL emitted data blocks
(CYS_*, NATIVE_*, RES_PHOS, HBOND_MATRIX, CONTACT_INTER, quats/bondvec
data) byte-identical to the certified old-form build; parameter diff
shows only the slot-form additions (PSEG=256, NSLOT=19456) and inert
CL defaults (FRAME_CL_K=0, NCL=0). Physics content unchanged; only
pair-force loop structure differs.

Runner: gpu_cert_run.sh (CPU f64 default target + GPU spirv f32, 3
seeds each). Analysis: gpu_cert_analysis.py with pre-registered reads
G1-G3 and a pass/fail decision rule (basin-level GPU-vs-CPU: per-seed
|delta rmsd| <= 2.0 and <= 7.0 absolute; CPU-slot-f64 vs old certified
4.45/4.87/6.24: |delta| <= 2.0, same band; no NaN, no late explosion).
Failure is reported, not tuned away.
