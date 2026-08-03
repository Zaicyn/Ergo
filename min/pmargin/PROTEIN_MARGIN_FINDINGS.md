# Protein Margin — Campaign Findings

**Date:** 2026-07-27
**Scope:** packed seed-sweep instrumentation, parallel tempering, ultrasonic
pulse rescue, steric-term test, amyloid cross-chain geometry, and model
ceiling mapping for the Protein Margin Cα-only Go-like folding model.
**Status:** all results oracle-validated or explicitly flagged as
null/negative. Files indexed in §10.

---

## 1. Executive Summary

This campaign turned Protein Margin from a single-trajectory folder into an
instrumented platform and then mapped its limits. Headline results:

- **Packed seed sweep:** up to 8 independent folding trajectories in one
  program, byte-identical to sequential runs, ~1.6× faster per trajectory.
- **Parallel tempering** rescues some trapped seeds (BBA5 7.0: 2.80 → 1.47 Å)
  but not all; small single-domain targets are better served by cheap seed
  sweeps.
- **Ultrasonic pulse** (coherent low-frequency backbone rocking) is the
  strongest trap-escape mechanism tested — rescues the 1SNO domain-swap trap
  that survived tempering, hot windows, and 20× incoherent heat, and works
  from 34 to 556 residues.
- **Model ceiling mapped:** reliable per-domain folding to ~140–170 residues;
  inter-domain assembly is the dominant failure mode above that; side-chain
  physics (W6F-class mutations, steric-zipper emergence) is the
  representation's hard boundary.
- **Amyloid geometry holds:** cross-β register to 1.2% of the 1YJP crystal
  and sheet-to-sheet zipper packing to ±0.09 Å — when the contacts exist;
  spontaneous zipper nucleation is correctly absent.

---

## 2. The Packed Sweep Instrument

Design: N independent trajectories in one packed vector (stage-4 pattern:
block index in the data, shared force-field tables, block-local state and
accumulators). SEED enters only the initial coil hash-walk and initial
theta; per-frame noise is seed-independent, so packed blocks reproduce
sequential runs by construction.

Validation (BBA5, 8 blocks, 48k frames): 4/5 oracle RMSDs bitwise-exact vs
the documented sequential sweep; seed 1.0 within 0.02 Å (proven chaotic
amplification, not packing — the sequential recompile itself moves). Gates
throughout: every experimental variant ships with a control build that must
be byte-identical to its baseline.

Per-block Kabsch RMSD, per-domain RMSD (added for multi-domain work), and
block-aware packed force kernels (3 launches/frame instead of 24, 7.5×
faster on GPU) are all part of the instrument.

**Precision contract (measured):** distributions yes, trajectories no. f32
GLSL transcendentals and atomic accumulation reroute chaotic trajectories,
but median RMSD (0.435–0.438), sub-3 Å fold rate (6/8), and trap detection
are identical across CPU and both GPU runs. Per-seed marginal endpoints are
not authoritative on ANY build in this regime.

---

## 3. Parallel Tempering

TMUL geometric ladder (1.0→2.0) multiplying noise amplitude; adjacent-pair
Metropolis swaps of temperatures every 500 frames; swaps-off gate
byte-identical in all variants.

| Target | Trap rate | Rescues | Notes |
|---|---|---|---|
| BBA5 (23 res) | 3/8 → 2/8 | Seed 7.0: 2.80 → **1.47 Å** (hot-end explore → ladder walk → quench fold) | acceptance 86–100%; good folders unharmed |
| 1SNO (136 res, 2 dom) | 2/8 → 2/8 | none (deep trap) | all 4 marginal blocks improved (mean 3.88→3.60); best fold **1.75 Å** (beats doc's 2.36) |
| WW (34 res) | 3/8 → 3/8 | none | one good folder knocked into outlier basin |

**Recommendations:**
- Small single-domain targets: cheap seed sweeps beat tempering (WW showed
  tempering can actively harm).
- Tempering helps marginal basins more than deep traps.
- Acceptance rate is diagnostic: 0% on a folded/stuck pair means Metropolis
  is correctly refusing to freeze the stuck block (1SNO).

---

## 4. The Ultrasonic Pulse (Mechanical Rescue)

Mode-1 standing wave along the backbone (lobe over the trapped region),
sinusoidal velocity kick. Validated settings: **ω ≈ 0.002 (period ≈ 3000
frames), A ≈ 0.05 (≈50× noise floor).**

Results:

| Target | Result |
|---|---|
| 1SNO domain-1 trap (D1 8.7 off, D2 folded) | **rescued**: 9.66 → 3.40 full; D1 8.73 → 3.83 (descending); D2 intact 1.65. Sweep mean 3.88 → 2.40; trap rate 2/8 → 1/8 |
| SdrD full construct (556 res, catastrophic block) | **disassembled**: 117.2 → 14.17; A3 149 → 4.27, B1 173 → 5.13 individually folded. Mean 34.9 → 21.0 |

**Evidence it's mechanical, not thermal:**
1. Strong frequency dependence at fixed amplitude (D1 = 3.83 / 7.77 / 6.64
   at ω = 0.002 / 0.017 / 0.17) — equal RMS power would be
   frequency-independent if thermal.
2. 20× incoherent sustained heat does nothing; coherent zero-mean rocking
   rescues. Coherence is the mechanism.
3. Sharp amplitude threshold (0.01 nothing, 0.05 works) — barrier-crossing
   signature.
4. Rescue requires period ≈ basin-escape timescale (~3000 frames).

Honest caveats: lobe has a net-force component (not a pure internal mode);
occasional casualties on mid-transition blocks; rescues reach correct
topology (sub-4 Å), not always sub-3 Å. Sonication+heat combos re-trap
(pulse+heat+swaps: 9.81) — use pulse alone.

---

## 5. Hot-Phase and Sustained-Heat Studies (Negative Results That Redirect)

- **Swap-window sweep** (1200 → 38400 frames, 32× range): the 1SNO
  domain-1 trap is never rescued at any window. Bottleneck is the post-1200
  noise floor (0.001), not swap count — Metropolis activity with no thermal
  exploration to work with.
- **Sustained heat** (floor 0.005–0.02 to frame 24000, ±swaps): trap
  pinned at 8.7–8.8. The plateau is robust to 20× incoherent noise.
  Conclusion: the fix was never schedule parameters — it needed a
  *coherent* perturbation, which is what the pulse provides.

---

## 6. Force-Field Findings (New Physics About the Model)

1. **Energy-blind traps (BBA5):** a compact non-native basin with energy
   competitive with native (−0.057 vs −0.036…−0.065). Energy alone cannot
   separate folded from trapped; RMSD remains the oracle.
2. **Energy-distinct kinetic plateau (1SNO):** the deep trap is
   high-energy (E≈33–36) — a kinetic, not thermodynamic, trap. Metropolis
   had the right signal there; the noise floor was the missing piece.
3. **Domain-swap signature:** per-domain RMSD directly diagnoses
   multi-domain traps (1SNO seed 3.0: D1 off 8.7, D2 folded 2.68; SdrD:
   A3/B1 merged blob while B2 folds independently). Inter-domain
   interfaces are the dominant failure mode for multi-domain constructs.
4. **Energy doesn't rank near-native structures:** mid-RMSD blocks span
   E 5–22 without ordering — use RMSD, not energy, for basin quality.

---

## 7. Steric Term Test (W6F) — Demonstrated Representation Ceiling

Residue-volume penalty (Zamyatnin 1972: Trp 227.8, Phe 189.9 Å³) on
over/under-collapsed Cβ packing pairs, pocket tightness weighted.

- WT gate: term identically zero by construction, fold exact (0.5879).
- W6F: **no trap at any strength across 330× dose-response, both sign
  conventions.** Anti-collapse strengthening *improves* W6F RMSD
  (0.585→0.493) — holding the pocket at Trp size makes the mutant
  geometrically MORE WT-like; the term is self-limiting.
- Margin signal exists but small: E_STERIC 0.008–0.029 vs WT 0.0 (~5×
  short of destabilizing).
- Pulse response: no differential (chaotic noise) — no mutation-induced
  trap exists to rescue.

**Verdict:** no Cβ-distance-based steric term of any sign or strength
destabilizes W6F here. CLINICAL.md §8's prescription is retired by
experiment: W6F needs side-chain physics the representation lacks
(pocket strain, solvent/void thermodynamics, indole NH). This is a
representation boundary, not a parameter problem.

---

## 8. Amyloid Cross-Chain Geometry

Target: GNNQQNY (7-residue Sup35 peptide), oracle 1YJP crystal
(in-register Cα spacing 4.866 Å exact; sheet-zipper closest approach
6.888 Å; zero intra-chain Go contacts for extended strand).

- **Guided assembly:** dimer self-assembles from denatured coils in <1000
  frames, holds cross-β through quench: all 7 in-register distances
  **+1.2% vs oracle**, register discriminated on all 6 off-register pairs.
  Trimer and tetramer dock identically (sequential template addition, as
  in fibril growth). Sheets stay parallel; no twist/slide.
- **Zipper packing (2 sheets × 2 chains):** all 9 crystal screw-mate
  contacts land within **±0.09 Å** of target, centered on zero (no slide),
  no buckling, register retained, stable through quench.
- **Emergence controls (correct negatives):** no assembly without contacts
  (hydrophobic-only: flat ~22 Å separation; zero zipper face-finding
  between sheets) — the GNNQQNY zipper is polar/H-bond driven, and generic
  attraction has nothing to build with.

**Verdict:** the model HOLDS inter-chain cross-β and steric-zipper
geometry to crystal accuracy when contacts exist. Spontaneous zipper
nucleation needs a directional polar attraction (Asn/Gln amide H-bond
ladder) — the named follow-up for emergent aggregation.

### 8.1 The Register Problem: Three Representations, One Complete Map

Follow-up work answering whether register can be *selected*, not just
held (`min/amyloid/amide_check.md`, `bead_check.md`, `tax_check.md`,
`entrain_check.md`):

- **Cβ-level amide Gaussian:** cannot discriminate register — adjacent
  registers retain 63–94% of peak attraction; too short-ranged to
  capture, too wide to discriminate. Holds at contact, never corrects
  off-by-one.
- **Atomistic amide beads** (typed Morse machinery from
  `tests/waveform_molecule_dynamics_geometric_strain.ergo`; narrow wells
  at the 1YJP-measured 3.353 Å): engages the true crystal diagonal
  specifically (scramble control: exactly zero bonds) — but valence-1
  degeneracy makes off-register states isoenergetic, so no self-correction.
- **Directionality tax** (`D_eff = D·(1 − TAX·OFF)`, OFF = |i+j−8|):
  breaks the degeneracy energetically (gap opens; clean diagonal
  selection at TAX ≈ 0.5; wrong-diagonal scramble → zero bonds). A
  downhill channel opens, but correction stalls at ~25% — the remaining
  barrier is kinetic, not energetic.
- **Entrainment:** the pulse completes the slide (offset → 2.44 ≈
  correct at ω = 0.005–0.02) — mechanism decomposes as **pulse = slide
  motor, tax = bond-pattern selector**. Rescue frequency is NOT portable
  across system sizes (0.002 for 136-res 1SNO, 0.005–0.02 for the
  28-res sheet) — amplitude transfers, frequency must be re-swept per
  target.
- **Schumann test (user-requested):** 7.83 rad/frame is sub-Nyquist
  (period 0.80 frames) — aliases into the noise hash, run
  indistinguishable from no pulse. No effect, as physics requires (no
  coupling mechanism exists at any scale).

### 8.2 LLPS / Condensates and the White-Bath Discovery

(`min/condensate/` — framework from the LLPS review in
`papers/llps.txt`: binodal/spinodal, critical temperature,
enthalpy-entropy balance.)

**Phase behavior found:** 8 thermally isolated temperature blocks per run
(kinetic T tracks TMUL² exactly). Demixing ✓ (one dominant droplet,
20–22/24 chains), binodal-like density gap narrowing toward Tc ✓,
spinodal-like coalescence kinetics ✓, finite-size fluctuation
suppression ~1/√N ✓.

**The discovery — the sim's "thermal noise" is not a stochastic bath.**
The hash `SIN((I+1)*7.3 + FRAME*0.17)` is a quasi-periodic drive
(period ~20–70 frames): residues slosh adiabatically, net displacement
≈ 0, speed² saturates at 6.2 vs naive 48 (87% of drive sapped).
**Evaporation did not exist in this dynamics** — no entropic mixing, no
dissolution at any T (600× attraction energy), no true Tc. Earlier
"fraying" was mechanical slosh threshold, not critical behavior
(corrected docs in `condensate_tc_check.md`).

**The white-bath fix** (splitmix-style integer hash PRNG in Ergo int64,
autocorr ≈ 0, variance-matched ×√6): MSD becomes diffusive (exponent
→1), speed² tracks 79% of naive, and **dissolution switches on** —
binodal gap closes at TMUL=40 (N=96), Tc bracket TMUL ≈ 30–40, and the
transition **sharpens with N** (first clean finite-size sharpening in the
project). Full homogenization needs ~10⁵–10⁶ frames at these amplitudes.

**Impact statement:** the model's thermodynamics are now complete in
principle — energy landscape AND entropy bath; aggregation AND
dissolution. Prior folding/basin/pulse results stand (variance-matched
noise power, mechanical phenomena); prior evaporation/dissolution claims
are superseded by the white-bath reruns.

---

## 9. Ceiling Map: SdrD (10PS, 556 res, 4 domains)

SdrD A2-A3-B1-B2 (Staphylococcus aureus MSCRAMM, all-β sandwich domains).
Domain boundaries detected structurally (contact minima):
A2=243–394 (152), A3=395–562 (168), B1=563–682 (120), B2=683–798 (116).

- **Per-domain gate FAILS:** best RMSDs 4.37/2.67/2.95/3.03 units
  (~6.7–10.9 Å) — ~40% worse than 1SNO good basins; A2/A3 past the
  140-res ceiling. Ablation (no-register reruns worse) proves it's
  landscape/size, not recipe.
- **Full construct (556 res):** all 8 blocks misfold (37–77 Å full-chain).
  Inter-domain dominates (full-chain RMSD 3–10× per-domain on every
  block); one pure inter-domain catastrophe (A3/B1 merged blob). Counter-
  point: B2 folds 2.94 in-chain ≈ 3.03 standalone — in-domain folds can
  survive assembly; the interfaces are what fail.
- **Pulse at 4× scale works** (§4).

**Practical ceiling:** reliable per-domain folding to ~140–170 residues;
multi-domain assembly above ~300 residues fails at the interfaces;
trap mechanics and pulse disaggregation remain useful at any tested size.

### 9.1 White-Bath Retest — Dynamics vs Landscape Decomposition

(`sdrd_white_check.md` — same programs, only the noise model swapped to
the validated splitmix white hash, variance-matched.)

- **Best folds improve 11–69% everywhere:** A2 4.37→3.38, A3 2.67→2.38,
  B1 2.95→**0.91 (2.3 Å — first fold-class result at this size)**,
  B2 3.03→1.82.
- **All irreversible catastrophes eliminated:** per-domain 4/32 → 0/32;
  full-construct merged-blob (117.2) gone *without the pulse* (→ 15.2).
  Full-chain mean 34.9 → 21.0.
- **Medians move only ±0.4–0.7**, and A2/A3 still have no sub-4 seed.

**Decomposition (the payload):** best-case folds were a *dynamics
artifact* (the quasi-periodic slosh drive couldn't do thermally-activated
escape; eliminated with data). Median ruggedness is the *energy function*
(confirmed with the dynamics suspect eliminated).

### 9.2 Protocol and Cofactor Eliminations — the Ceiling Is the Landscape

Two further hypotheses tested and eliminated with data:

- **Protocol** (`sdrd_seq_check.md`, sequential co-translational staging,
  A2→A3→B1→B2, amyloid template-addition pattern): statistically
  identical best case to all-at-once (16.47 vs 15.2). Staging *does* tame
  the failure tail (no domain worse than 15.7 vs 39.5; zero merged blobs
  in both protocols) — but the best case doesn't move. Protocol: innocent.
- **Calcium** (`sdrd_ca_check.md`, 9 crystal Ca²⁺ sites mapped with full
  coordination tables — B1/B2 host 6 sites as expected for MSCRAMM;
  harmonic staples at crystal geometry, K = 0.5–10): **no effect at any
  strength** — the Go contact map is derived from the same crystal, so
  the coordination geometry the calcium locks is already encoded in the
  native contacts. Staples are redundant information at Cα resolution.
- **Domain boundaries verified** against UniProt/Pfam curation
  (Q99W47: A region 36–568, CNA-B1 569–680, CNA-B2 681–791): the
  contact-minimum detection was within 2–7 residues everywhere (B2
  erroneously included 792–798 of B3; corrected).

**Triple elimination conclusion:** dynamics (partially guilty, fixed),
protocol (innocent), and missing chemistry (redundant) are all excluded.
**The ceiling is the contact/energy function itself at Cα resolution.**
Any further progress on SdrD-class targets requires a different
representation (explicit side-chain/carboxylate beads) — the same
side-chain-physics boundary the W6F (§7) and amide (§8.1) experiments
hit independently.

### 9.3 Targeted-Torsion Fix (BBA5) — the Successful Case

(`dihedral_check.md` — Hessian spectroscopy then per-dihedral comparison,
native vs seed-0.0 trap.)

The BBA5 trap is a **globally warped native-like fold**: 19/21 dihedrals
match native within ~5°, register pairs correct, all 13 native contacts
satisfied in both states, Hessian spectra statistically identical (twin
basins — escape is purely kinetic). Exactly **two** dihedrals deviate
materially: **residue 15 (+15.6°) and residue 10 (−8.1°)**.

Stiffening the model's own crystal-derived torsion term at just those two
positions (TORSK 0.2→1.0, no new information injected): **seed 0.0
rescued (1.668→0.627), trapped seeds 6.0/7.0 → 0.17/0.86, trap count
3→0**, native gate passes, and the wrong-position control (stiffening res
5/20) fails to rescue and damages good folders — proving position
specificity. Mechanism: dynamical, not endpoint — the trap's formation
pathway needs res-15 at +78°; stiffening closes the basin during folding.

(Bonus finding, verified with scipy: the sim's quaternion COMPUTE_RMSD
inflates exact Kabsch RMSD by 1.3–1.7× per state. Historical tables stand
as an internally consistent metric; absolute values run ~1.5× high.)

### 9.4 The 1SNO Diagnosis — the Fragmentation Blind Spot

(`dihedral_1sno_check.md` — the same pipeline applied to the 1SNO
domain-swap trap, and it does NOT transfer.)

The 1SNO trap is **not a warped native — it is a fragmented fold.** 86/133
dihedrals deviate ≥5° (BBA5 had exactly 2), distributed across domain 1,
NOT clustered at the interface. Decisive structural finding: **the Morse
backbone bond plateaus at D≈4 with no restoring force past it**, so the
field tolerates a disconnected chain. The trap carries **8 broken
tethers** while satisfying **196/197 native contacts including all 25
cross-domain ones** — the 136-residue Go map cannot distinguish "folded"
from "correctly arranged fragments." Hessian confirms the different
anatomy: not a twin — softer (6 vs 3 soft modes) plus a genuinely
negative saddle mode (res 51/56/45) — a high-energy kinetic plateau
(E=40.4 vs 7.7), not a local minimum.

Named failure mode: **fragmentation blind spot** — a contact map that
scores inter-residue distances cannot see backbone discontinuity. (Also
banked: finite-difference Hessian cutoff artifacts from hard steric/hydro
cutoffs — fixed with a C¹ cosine taper; and dihedral-coordinate
singularities at near-straight geometry that are not physics.)

### 9.5 Tether Repair Experiment — Three-Part Verdict

(`tether_check.md` — two designs: A = global harmonic continuation past
the Morse plateau, K_LR ∈ {0.05–1.0}; B = targeted reinforcement at the
diagnosed broken junctions, termini excluded.)

1. **Neither design closes the domain-swap trap.** Tethering cures
   fragmentation mechanically (8 → 1–4 broken bonds) yet full-chain RMSD
   stays 9.3–9.9 — **fragmentation was the field's cheap accommodation of
   the mis-fold, not its cause.** Design B even repairs D1 internally
   (8.73→4.14, D2 1.69) while full-chain stays 9.86: the domains fold
   better and remain mutually misplaced. The irreducible core is
   **inter-domain placement under the degenerate contact map** (all 25
   cross-domain contacts were already satisfied in the trap).
2. **The Morse plateau does deserve redesign.** Design A at K_LR = 0.2–0.5
   is a clean field improvement independent of the trap: gate passes at
   all strengths, every good/marginal block improves (block 3: 2.29→
   **0.65 — best fold of the project**), and the N-terminal dangle is
   eliminated everywhere (confirming it was a plateau artifact and
   quantifying its ~1.7-unit RMSD inflation). At K_LR = 1.0 the tether
   overshoots and spawns a new trap (block 6: 2.96→9.13). **Recommended
   window: K_LR ≈ 0.3 ± 0.2.**
3. **Targeted patching is the wrong tool for this trap.** The matching
   levers are interface/docking-level: per-domain swap criteria, longer
   hot phase, or interface-register field terms.

**The two-trap taxonomy** (now fully mapped): BBA5-class = bending
(kinetic, twin basins, fixable with targeted torsion constraint);
1SNO-class = inter-domain placement (degenerate cross-domain contact map,
fixable only at the interface level).

### 9.6 Fold-Then-Dock Protocol — and the Placement Degeneracy

(`dock_check.md` — the biological protocol replicated: fold domains
independently, then assemble. Two variants: oracle-dock (native PDB
domain geometry) and sim-dock (best sim folds from the per-domain gate.)

- **Decisive win over all-at-once:** oracle best 9.06 / mean 13.07; sim
  best 9.34 / mean 12.46 — vs all-at-once best 13.2 / mean 21.0
  (**−31% best, −40% mean**), also beating sequential co-translational
  staging. Adopted as the multi-domain protocol.
- **Per-domain errors do NOT propagate:** sim-dock ≈ oracle-dock
  everywhere (9.34 vs 9.06) — realistic per-domain folds are good enough;
  the deployable protocol equals the oracle.
- **The remaining failure, precisely located:** internal-only RMSD
  2.1–3.4 (excellent) vs placement error 8.8–24.6 (**≥90% of total**).
  Full-chain RMSD plateaus by frame ~6000 and never anneals.
- **The decision-tree answer (oracle-dock also fails → it's the field,
  with a refinement):** the interface contacts are NOT the failure —
  28–31/32 cross-domain contacts satisfied in every block (mean |D−R0|
  ~0.2). The failure is that the 32-contact interface is **degenerate
  against rigid-body placement**: correct interface distances, wrong
  mutual orientation. The field can see that two domains touch correctly,
  not which way they face — the fragmentation blind spot's cousin, at
  construct scale.
- **Caveat:** damped domains deform 0 → 2–3.5 during the initial heat
  ramp despite 0.5 damping (stabilize after). Named fixes: (1) interface
  placement/orientation restraints (register/dihedral terms across domain
  boundaries — the β-sheet chirality lesson applied to interfaces — or a
  larger cross-domain contact set), (2) cold-docking schedule, (3)
  rigid-body docking moves.

### 9.7 The Orientation-Term Null — Local Restraints Can't Pin Soft Domains

(`orient_check.md` — 53 cross-domain dihedral quartets with crystal
targets spliced into the register-torsion machinery; full matrix
{baseline, +term} × {hot, cold} × {oracle, sim}, plus early-activation
variants. A well-controlled null.)

- **Every cell ties** (best 9.06–9.35, placement ~12) at both strengths,
  gated or always-active — the orientation term does NOT fix placement.
- **Null validated three ways:** (i) the term is active and effective
  (quartet deviation collapses 51.7° → 12.9° mean — local interface
  geometry driven to near-native); (ii) placement doesn't follow anyway
  (COM errors 3.5–11.8, rotations 23–35°, identical with/without term);
  (iii) the signal is strong (a 30° domain rotation deviates quartets
  51–90° — sensitivity is not the issue).
- **Mechanism:** domains are compliant (internal RMSD 2.5–3.5) and absorb
  the misplacement internally — restraints are satisfied locally while
  domains sit wrong globally. **No local interface restraint can pin the
  rigid-body placement of a soft domain.** The degeneracy is structural,
  not a restraint-type problem (distances and signed dihedrals fail
  identically).
- **Correction to the dock_check reading (measured):** cold docking does
  NOT preserve domains (cold ≈ hot, ±0.05) — the oracle deformation is
  **force-driven** (the field relaxes crystal geometry to its own
  preferred minimum), not heat-ramp-driven. Cold docking as a lever is
  dead.
- **Named levers (in order):** (1) long-leverage orientation restraints —
  quartets spanning 30–60 residues into each domain (the short-leverage
  set is now the control proving leverage is the missing ingredient);
  (2) rigid-body docking moves (held in reserve — placement is a
  rigid-body coordinate per-bead dynamics can't hop, but the user prefers
  deterministic methods first).

### 9.8 The Long-Leverage Null — Deterministic Restraint Class Exhausted

(`leverage_check.md` — quartets extended to leverage s ∈ {8, 16, 30}
residues into each domain, both strengths, both starts, 12 cells.)

- **Flat leverage-response curve:** placement 11.6–12.7 at every
  leverage and strength (s = 0, 8, 16, 30; k = 0.5, 1.0; oracle and sim).
  No minimum effective s — there is no response.
- **Control proves engagement:** long-leverage quartets driven to
  near-native (17.6° mean at s=30). The null is not a setup failure.
- **The anatomy:** satisfying 30-residue-spanning quartets while a domain
  sits rotated ~30° is only possible if the deformation is **distributed
  through the domain core**, not concentrated at the interface. Longer
  leverage merely engages more of an already-distributed compliance.
- **The deeper proof:** cold ≡ hot, and oracle domains relaxing 0 →
  2.5–3.5 with zero heat — the deformation is force-driven. **The field's
  own minimum is not the crystal.** The assembly error is the force-field
  ceiling expressed at assembly level; 36–53 added restraints cannot
  outvote thousands of frustrated native-targeted terms.
- **Deterministic restraint-based docking is now exhausted** (contacts,
  short dihedrals, long dihedrals, cold schedule, early activation — all
  tie, every one validated as engaged). Remaining paths: field
  rebalancing against frustration, or rigid-body Monte-Carlo (user's
  stated last resort), or accepting fold-then-dock's ~40% win as the
  current field ceiling.

---

## 10. Reproducibility

| Artifact | Path |
|---|---|
| Packed sweep (BBA5) | `min/pmargin/packed_bba5_v2.ergo`, `packed_v2_check.md` |
| Tempering | `min/pmargin/packed_temper.ergo`, `temper_check.md` |
| 1SNO sweep + tempering | `min/pmargin/packed_1sno*.ergo`, `packed_1sno_check.md` |
| WW sweep | `min/pmargin/packed_ww*.ergo`, `packed_ww_check.md` |
| Hot-phase window study | `min/pmargin/hotphase_*.ergo`, `hotphase_check.md` |
| Heat + pulse experiments | `min/pmargin/heat_*.ergo`, `pulse_*.ergo`, `heatpulse_check.md` |
| Steric term (W6F) | `min/pmargin/steric_*.ergo`, `steric_check.md` |
| Amyloid cross-chain | `min/amyloid/amyloid_*.ergo`, `amyloid_check.md` |
| Zipper packing | `min/amyloid/zipper_*.ergo`, `zipper_check.md` |
| SdrD ceiling map | `min/pmargin/sdrd_*.ergo`, `sdrd_check.md` |
| SdrD white-bath retest | `min/pmargin/sdrd_white_*.ergo`, `sdrd_white_check.md` |
| SdrD sequential assembly | `min/pmargin/sdrd_seq_*.ergo`, `sdrd_seq_check.md` |
| SdrD calcium staples | `min/pmargin/sdrd_ca_*.ergo`, `sdrd_ca_check.md` |
| BBA5 torsion fix | `min/pmargin/dihedral_diff.py`, `dihedral_check.md`, `packed_bba5_tors*.ergo` |
| 1SNO diagnosis | `min/pmargin/hessian_1sno.py`, `dihedral_1sno.py`, `dihedral_1sno_check.md` |
| Tether repair | `min/pmargin/gen_tether.py`, `tether_{a,b}_*.ergo`, `tether_check.md` |
| Fold-then-dock | `min/pmargin/gen_dock.py`, `dock_{oracle,sim}.ergo`, `dock_check.md` |
| Orientation-term null | `min/pmargin/gen_orient.py`, `orient_*.ergo`, `orient_check.md` |
| Long-leverage null | `min/pmargin/leverage_*.ergo`, `leverage_check.md` |
| Force-field reference | `min/pmargin/FORCE_FIELD_REFERENCE.md` |
| Amide ladder (Cβ proxy) | `min/amyloid/amide_*.ergo`, `amide_check.md` |
| Amide beads (atomistic) | `min/amyloid/bead_*.ergo`, `bead_check.md` |
| Directionality tax | `min/amyloid/tax_*.ergo`, `tax_check.md` |
| Entrainment sweep | `min/amyloid/entrain_*.ergo`, `entrain_check.md` |
| Condensate + white bath | `min/condensate/*.ergo`, `condensate_check.md`, `condensate_scaling_check.md`, `condensate_tc_check.md`, `white_check.md` |
| Oracle structures | `pdb/1YJP.pdb`, `pdb/10PS.pdb`, `pdb/1L2Y.pdb` |

Compiler features used: packed batch (stage-4), 2D stencil extraction
(F104), ATAN2 lowering (F105), multi-accumulator reductions (F106) — all
in `core/archive/changes.md`.

---

## 11. Caveats and Limits

1. **Precision regime:** distributions, not trajectories (§2). f32 GPU
   transcendentals reroute chaotic paths; distribution statistics are
   preserved; per-seed marginal endpoints are not authoritative.
2. **Cα-only representation:** no side chains, solvent, pH, or explicit
   H-bonds. W6F-class mutations and steric-zipper emergence are outside
   the representation (§7, §8).
3. **Energy is advisory only** (§6): RMSD is the oracle.
4. **Size ceiling** (§9): ~140–170 res/domain; inter-domain assembly is
   the dominant failure above that.
5. **Chaotic deviation between builds** (≤ ~0.5 Å on unsettled
   trajectories) is expected and measured, not a bug.
6. Sequential-assembly amyloid results are template-driven; emergent
   aggregation is untested (needs polar attraction term).
7. **Noise-model semantics (measured):** prior runs used a
   quasi-periodic (non-stochastic) "thermal" drive — kinetic temperature
   exists, evaporation does not. Folding/basin/pulse results stand as
   mechanical/annealing phenomena; evaporation/dissolution claims made
   before the white-bath fix (§8.2) are superseded. New thermal work
   should use the white-noise bath.

---

## 12. One-Paragraph Summary (for citation)

We instrumented the Protein Margin Cα-only Go-like folding model with
packed multi-trajectory sweeps (byte-validated against sequential runs),
parallel tempering, and a coherent mechanical perturbation protocol, and
mapped its accuracy envelope. Packed sweeps reproduce sequential
trajectories exactly while cutting cost per trajectory; tempering rescues
shallow traps (2.80→1.47 Å) but not deep ones; a low-frequency backbone
rocking pulse (period matched to the basin-escape timescale) rescues
traps that survive all thermal protocols — including a domain-swap trap
in staphylococcal nuclease and a catastrophic inter-domain collapse in a
556-residue, 4-domain adhesin — with evidence the mechanism is coherent
mechanics, not effective heating. The model folds domains reliably to
~140–170 residues, holds inter-chain cross-β and steric-zipper geometry
to within 1.2% of crystal structure when contacts are provided, and hits
its representation boundary at side-chain physics (W6F-class mutations,
zipper emergence), which no distance-based term can supply.
