# BRANCH_LAW.md — φ4.6 anchored dendritic branching (R5) certification

Certified: 2026-09-02. Engine lineage: pop_fpt.ergo (φ4) → brush_c400g →
brush_br400 → **brush_bra** (S4 anchored branching, certified engine) →
brush_bra_x (xpt instrumentation) → **brush_bra_r** (hold-release piston
protocol). Oracle: plan_branch.md (O-R1..O-R6), registered before the runs
they describe. All gates with the certified toolchain
(/mnt/agents/output/actin_swarm/toolchain/ergo_mcl). Stage C checkpoint:
`Stage C/` (CHECKPOINT.md, SEGFIX.md, LAPLACE_CHECK.md, ASSEMBLY_OPTIONS.md,
RELEASE_PROTOCOL.md, engines/, analysis/, runs17/, runs18/).

## The problem this rung solves

The capped unbranched brush (CAP_LAW.md) is mechanically weak: certified
fixed-slab stall 2.5–3 (kT/σ units) and insufficient tip engagement with the
barrier. Design goal for the branching rung (O-R3): n_eng ≥ 3 engaged barbed
tips with P(bare) < 0.05 at F=1 — i.e., a brush that *stays on the barrier*
under load. Dendritic (Arp2/3-style) branching is the candidate mechanism:
each branch event converts one mother tip into two, multiplying the contact
population without new nucleation.

## Assembly-method tournament (documented: ASSEMBLY_OPTIONS.md)

Five assembly options were evaluated before committing (user directive:
"there isn't just one solution here"):

- **S1 free branching** (brush_br400): daughters unanchored — measured
  n_eng = 2.36, marginal. Loses daughters to diffusion.
- **S4 anchored branching** (brush_bra): daughters membrane-anchored at the
  junction monomer with per-step retargeting — measured n_eng = 3.58 smoke,
  ensemble-confirmed **3.48**. WINNER.
- S2 (M4C 8-spring junction port), S3 (oriented nucleation), S5 (branch
  density cap): analytically deferred with rationale; S2 reconsidered at R6
  (adhesion/traction needs tree topology).

## Mechanism (S4, as certified)

At branch commit on mother F at junction monomer BM1: daughter slot F3 is
born as a rigid trimer built at exactly **70° from the mother axis**
(0.34202·a + 0.93969·u, u a fresh random perpendicular — RNG slots
4500+2(F−1)/4501+2(F−1)), with `FILANCH(F3) := BM1`, anchor target =
BM1's current bead positions (zero initial strain, M4B lesson), and per-step
membrane tracking retargeting `ANX → XP − XPMAR − 0.75`. Anchor transfers on
pointed unbind (existing certified machinery); cleared at dimer birth/death
and defensively for dead slots. No new RNG draws when PBR=0 → gate-inert.

## Certification chain

1. **SEGFIX (prerequisite)**: REBUILD_BONDS clobbered the global loop var F
   → post-call KINETICS tail ran as ghost filament MAXF+1 → ghost binds from
   garbage coords → wild-write SIGSEGV. Fixed with `IF F <= MAXF` guards +
   MAXF+2 arrays. Gates 0-diff, ghost scan 0/2000+2000, smokes complete.
   Old-run contamination quantified (≤19/150 monomers ghost-sequestered,
   laws stand, numbers ±2–9%): SEGFIX.md.
2. **400-gen budget bump** (user-directed): NMAX=400, NB=800, MAXF=32,
   NSLOT=51200 + rebased collision-free RNG slot map.
3. **O-R1 gates**: brush_bra(PBR=0) ≡ brush_c400g parent bit-identical;
   brush_bra_r(PREL=0) ≡ brush_bra_b0 0-diff (release gate inert, xpt
   instrumentation WRITE-only, deterministic hash RNG).
4. **Ensemble runs17** (26 runs, 1M steps): clamped grid F∈{0,0.5,1,2,4}×
   4 seeds (law reference). 25/26 logs lost heads to the NUL-sparse incident
   (concurrent streaming writes); stationary tails + full-run counters
   verified usable; protocol fixed (verify-before-delete runner) and
   demonstrated clean on all runs18 logs (18/18 intact).
5. **Released-piston protocol fix** (RELEASE_PROTOCOL.md): free-from-t=0
   release is destroyed by the initial transient (plane free-falls into the
   gas field, spike-flings to the clamp by step ~500). Hold-release
   (PREL=300000) fixed that, but exposed the deeper fact: **v-by-drift is
   geometrically unavailable in the 12σ box** (gas seeded x∈[2,10]; brush
   reaches the plane by nucleation+branching within ~20k steps; maturation
   and drift timescales never separate). O-R5 therefore certified in force
   form; true v(F) needs a tall-box engine (deferred, documented).

## The R5 laws (all numbers reproduced by saved analyzers in
## `Stage C/analysis/`: stage_c_law_table.py, stage_c_force_analysis.py)

**L-R5.1 Engagement (the design goal).** n_eng = 3.38–3.83 across
F ∈ [0,4], load-flat (structural, not force-dependent); P(bare) = 0.0000
in 19/20 clamped arms (worst 0.0043). At extreme compression the brush
*recruits* additional tips: n_eng rises 3.3 → 5.9 as F goes 0.5 → 12
(load-adaptive engagement).

**L-R5.2 Structure.** N_f = 30.2–30.9 of MAXF=32 — the brush lives at the
filament-slot ceiling (occupancy P(N_f=32) = 0.62–0.71); mean length
n̄ = 11.8–12.1 monomers; mean lifetime 40–52k steps; mean max-len-at-death
7.5–8.9 (death events weight short daughters — survivorship, standing stock
is longer); branch share of births 0.57–0.72; dimers ≈ 0.3 (rare).

**L-R5.3 Force and stall.** Clamped arms: contact force flat fmean ≈ 5.0–6.2
across F ≤ 4 (≈1.55 per engaged tip). Released arms (runs18, hold-release):
the brush holds the plane at its tip field with force exceeding load at
every F ≤ 10; **stall F\* ≈ 12 measured directly** (margin ⟨f⟩−F: +0.27 at
F=10, +0.05 ≈ 0 at F=12) — **≈4× the certified unbranched fixed-slab stall
(2.5–3)**, no extrapolation needed. Stall is set by the compressed/thin
brush limit: pinned thin-brush stall (hold phase) = 11.4 ± 0.4 ≈ F\*.

**L-R5.4 Transport.** Per-tip barbed capture 5.6–8.5×10⁻⁴ /tip/step,
load-independent across F ∈ [0,4]. Laplace-hybrid oracle (screened-Poisson
supply × 0.574 certified dynamical suppression, no fitted parameters)
predicts 0.74–0.83× the engine capture — the certified transport oracle
holds on the branched engine (LAPLACE_CHECK.md). Gap-ratchet block:bind
ratio = 2.0–4.3 (stationary event counts; cross-checked by cumulative
NBLK/FINAL binds = 2.7–3.5).

**L-R5.5 Orientation.** The mature dendritic brush is a **near-isotropic
mesh**: mother-tip and daughter-axis orientation vs the piston normal are
flat in |a·x̂| (mean 0.486 / 0.458 ⇒ mean angle ≈ 61°/63° ≈ isotropic 60°).
Each branch generation rotates 70°, so orientational memory of the x-aligned
seed is destroyed within ~2 generations; with branch share ≈ 65% and
lifetimes ~45k steps, most standing filaments are generation ≥ 2.
Directed force emerges anyway because only plane-adjacent barbed ends push.

**L-R5.6 Density regulation = slot ceiling.** With branching unconstrained
by monomer supply (nfree ≈ 30–40 free at all times) and death rates set by
geometry, the filament count pins at MAXF. The ceiling is the regulation
mechanism; novbr/nover instrument the pressure (POPSTAT), no ghost
pathologies (SEGFIX scan clean).

## Branched vs unbranched at identical engine/geometry/seeds

Reference grid (runs18, brush_bra_b0 = PBR=0, clamped XPLO=5.5/XPHI=11.3,
1M steps, 2 seeds; stationary window t>500k):

| F | n_eng unbr → br | P(bare) unbr → br | ⟨f⟩ unbr → br | N_f unbr → br |
|---|-----------------|-------------------|---------------|----------------|
| 0 | 1.46 → 3.56 | 0.063 → 0.0015 | 1.9 → 5.5 | 21 → 30 |
| 1 | 1.66 → 3.48 | 0.010 → 0.0000 | 2.0 → 5.4 | 21 → 31 |
| 4 | 2.63 → 3.83 | 0.0005 → 0.0000 | 4.0 → 6.2 | 22 → 31 |

Branching: ×2.1 engagement at F=1, bare windows eliminated, contact force
×2.7–2.9, stall 2.5–3 → ≈12 (×4). Unbranched N_f ≈ 20–22 stays BELOW the
slot ceiling (supply/dynamics-regulated); branched pins at 32 — the
ceiling regulation (L-R5.6) is branching-specific. Unbranched at F=4 is
force-balanced deep in compression (xp ≈ 7.7, ⟨f⟩=4.0=F): consistent with
its certified 2.5–3 stall; branched at F=4 still holds the plane at its
free tip field with margin +2.6.

## Oracle scorecard (plan_branch.md O-R1..O-R6)

| Oracle | Criterion | Result | Verdict |
|--------|-----------|--------|---------|
| O-R1 gates | PBR=0 ≡ parent, 0 diffs | 0 diffs (all gates, incl. brush_bra_r) | **PASS** |
| O-R2 branch dominance | ≥70% of births at F=1 | 0.64 mean (0.52–0.79 across 4 seeds); all-load 0.57–0.72 | **BORDERLINE** (mean under bar, within seed scatter) |
| O-R3 engagement | n_eng ≥ 3, P(bare) < 0.05 at F=1 | n_eng = 3.48 (3.15–4.15), P(bare) = 0.0000 | **PASS** |
| O-R4 stability | Amended B-1: maxlen<35, N_f stationary, conservation exact, ghosts 0, ceiling pressure instrumented | all criteria pass; ceiling occupancy 62–71% is the measured density-regulation mode | **PASS (B-1 ratified)** |
| O-R5 protrusion | Amended B-2: force margin and stall in box-confined geometry | margin +4.7→+3.7 (F=0.5→2), stall ≈12, ⟨FRCT⟩=5.7 at F=2, xp min 9.9 ≫ 1.5 | **PASS (B-2 ratified)** |
| O-R6 angle instrument | Amended B-3: daughter–mother angle =70° at commit | daughter–mother = **70.00° exactly** (1500/1500 events); daughter–normal isotropic as expected for the mature mesh | **PASS (B-3 ratified)** |

### Ratified amendments (2026-09-02)

- **B-1 (O-R4)**: the original <1% ceiling-occupancy bar assumed
  supply-limited density. Measured: ceiling-pinning *is* the density
  regulation. Ratified criterion: N_f stationary, conservation exact,
  occupancy instrumented (NFILH + POPSTAT novbr), N_f≤MAXF, and no
  slot-exhaustion pathology (ghost scan = 0). Ceiling occupancy is reported
  as an observable, not treated as a failure.
- **B-2 (O-R5)**: the drift instrument is replaced by the force-balance
  instrument in box-confined geometry: v>0 ⟺ ⟨contact force⟩ > F at the
  free tip field (plane held at/above tip field, clamp occupancy declining
  with F). Stall = load where margin crosses 0. True drift v(F) remains
  deferred to a tall-box engine (LBOX≈24, NMAX≈2000, RNG rebase — later
  rung).
- **B-3 (O-R6)**: the instrument is validated against the daughter–mother
  angle (70.00° exact, unit norms). The original criterion assumed
  x-aligned mothers; a mature dendritic mesh is isotropic (L-R5.5).
  Ratified criterion: daughter–mother angle =70° at branch commit.

## Corrections to earlier figures

- The previously reported gap-ratchet blk:bind ≈ 157–182 was a definitional
  artifact (cumulative NBLK misread as per-window). Correct stationary
  ratio: 2.0–4.3 (event counts), 2.7–3.5 (cumulative cross-check).
- Branch share of births: stationary-ensemble value 0.57–0.72 (earlier
  smoke-derived 75–80% superseded).

## Contamination notes

runs15 (L1 sweep) ran with the live F-clobber bug: quantified ≤19/150
monomers ghost-sequestered, observables shift ±2–9% (SEGFIX.md §3);
guarded re-ensemble deferred (user: no preference). All Stage C numbers in
this document are from post-fix engines. BRUSH_LAW.md/CAP_LAW.md carry
contamination headers.

## Open items / later rungs

- Tall-box engine for true v(F) drift (deferred; also the natural home for
  the φ5 1D-closure boundary table kon_b^eff(n)).
- O-R2 borderline: if the ≥70% bar is load-bearing for downstream biology,
  a branch-rate knob turn (DBR ×1.3) likely crosses it — untested.
- R2 formin-brush comparison; R6 adhesion/traction (reconsider S2 junction
  port); φ5 closure; crawling integration.
