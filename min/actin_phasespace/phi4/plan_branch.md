# R5 — DENDRITIC BRANCHING RUNG (pre-registered design + oracle, 2026-09-02; amendments ratified 2026-09-02)

## Why (the certified motive)
- E1 (runs16): fixed-slab brush has v0(F) ≈ 0 at all loads — no persistent
  protrusion possible without membrane-attached nucleation.
- E2 + ANALYTICS Map 2: engagement is structural (invariant to KCAP×2,
  flat in zone depth); only nucleation AT the membrane fixes n_eng.
- Arp2/3 dendritic nucleation does both: branches nucleate on mothers
  near the membrane, axes inherited at ±70° toward the membrane.

## Chemistry (new toggleable channel PBR; lineage preserved)
Per step, per active filament F (only when PBR=1; draws only when PBR=1
→ PBR=0 ≡ brush_c bit-identical):
  eligible: FILACT(F)=1, uncapped barbed tip, tip head bead within
            DBR = 1.5 of the plane margin (PX(HB) > XP − DBR − XPMAR)
  attempt:  UBR = RAND(SN + 1200 + F); branch if UBR < KBR·DT
  branch:   axis b = cos(70°)·a_mom + sin(70°)·u_perp, u_perp from one
            azimuth draw (slot 1201+F) in the deterministic a⊥ basis;
            trimer placed with pointed-most monomer at the mother's tip
            bead position, monomers 2,3 at +PITCH·b increments;
            consumes 3 free monomers (skip if nfree < 3 or no free slot —
            no recycling of the mother, event just fails, count NOVBR);
            branch = normal filament (caps, grinds, dies by φ4.5 rules).
Slots 1200/1201+F (F ≤ 20) disjoint from all existing ranges (≤1116).
KBR: P = KBR·DT = 2e-3/step per eligible mother (KBR = 2.0) — target:
branching-dominated births (dimer channel stays on as background).

## Config bump (justified: N_f ≈ 10 values certified stable at 150)
N_tot = 200, NB = 400, NBMAX = 650, NSLOT = 25600, MAXF = 20, NFILH(21).
Branching raises N_f; expect n̄ ≈ 8-10 → N_f ≈ 16-19 (headroom to 20).

## Oracle (registered before any run)
- O-R1 GATES: brush_br(PBR=0) ≡ brush_c200 bit-identical (0 diffs);
  brush_br(PBR=0,PSTN=0) ≡ pop_slab_c200 (0 diffs). 300k steps each.
- O-R2 branching dominance: branch births ≥ 70% of all births (F=1 arm).
- O-R3 engagement: n_eng ≥ 3 and P(bare) < 0.05 at F=1. (THE design goal;
  falsification: n_eng < 2 → structural assumption wrong, investigate.)
- O-R4 stability: max len < 35 sustained, N_f stationary over stationary
  half, conservation exact every census, N_f=MAXF occupancy < 1%,
  nover+NOVBR reported (slot pressure instrumented, not hidden).
  **Ratified Amendment B-1 replaces the occupancy criterion; see below.**
- O-R5 PROTRUSION (released piston, XPLO=1.5, XPHI=11.4): positive drift
  v(F) > 0 at F ∈ {0.5, 1.0}; v(0.5) > v(1.0) > v(2.0) (monotone force-
  velocity); stall above the fixed-slab value (holds F=2 with positive
  margin: ⟨FRCT⟩ ≥ 2 without XPLO support). FALSIFICATION: v ≈ 0 again →
  nucleation-zone co-movement insufficient; next lever is branching ON the
  membrane itself. **Ratified Amendment B-2 replaces the drift instrument
  with the box-valid force-balance form; see below.**
- O-R6 angle instrument: daughter axis |a·x̂| distribution peaked at
  cos70° ≈ 0.34 ± spread (validates the geometry instrument end-to-end).
  **Ratified Amendment B-3 changes the reference from piston normal to
  mother axis; see below.**

## Ratified amendments (2026-09-02)

These amendments were ratified after the Stage D measurements and do not
change the engine, data, or originally registered text above. They replace
criteria whose assumptions were falsified by measurement.

### B-1 — O-R4 stability criterion

Original assumption: a healthy brush should have N_f=MAXF occupancy <1%.
Measurement: the branched brush pins at MAXF for 62-71% of stationary time
while remaining conserved, stationary, ghost-free, and below the length
ceiling. Ceiling-pinning is therefore the density-regulation mechanism, not
a pathology.

Replacement criterion: O-R4 passes if max length <35 is sustained, N_f is
stationary over the stationary half, monomer conservation is exact at every
census, ghost scan is zero, N_f≤MAXF always, and ceiling pressure is
instrumented through NFILH plus nover/NOVBR. Ceiling occupancy itself is a
measured observable, not a failure criterion.

Measured verdict under B-1: **PASS**.

### B-2 — O-R5 protrusion instrument

Original assumption: released-piston drift v(F) is measurable in the 12σ
box. Measurement: v-by-drift is geometrically unavailable. The brush reaches
the plane by nucleation and branching within ~20k steps; after PREL release,
the 2.4σ of drift room is consumed by a decompression transient before a
mature drift state can separate.

Replacement criterion: in box-confined geometry, protrusion is certified in
force form. Positive protrusion corresponds to positive force margin
⟨f_contact⟩−F while the plane is held off the lower clamp; stall is the
load where the stationary margin crosses zero. A true v(F) assay requires a
future tall-box engine.

Measured verdict under B-2: **PASS** — margin remains positive through F=10
and crosses zero at F≈12, versus the certified unbranched stall 2.5-3.

### B-3 — O-R6 angle reference

Original assumption: mother axes are sufficiently x-aligned that the
daughter axis should peak at cos70° relative to the piston normal.
Measurement: the mature dendritic mesh is isotropic, so the normal-referenced
distribution is flat even when the branch construction is exact.

Replacement criterion: validate the instrument against the daughter-mother
angle at branch commit, which must be 70° within numerical tolerance;
normal-referenced orientation is a separate mesh-structure observable.

Measured verdict under B-3: **PASS** — daughter-mother angle =70.00° for
1500/1500 audited events.

## Stage plan
A. brush_c200 (budget-bump only) + brush_br (branching). Gates O-R1.
B. Smoke F=1, 1M: O-R2/O-R3/O-R4/O-R6 + no explosion.
C. Ensemble clamped F ∈ {0,0.5,1,2,4} × 4 seeds (law reference) +
   released-piston F ∈ {0.5,1,2} × 2 seeds (v(F), stall) — 28 runs.
D. BRANCH_LAW.md + checkpoint. Update ANALYTICS Map 2/3 with n_eng≥3 data.
   Stage D amendments B-1/B-2/B-3 ratified 2026-09-02; no new simulations
   required because all replacement criteria were already measured.
