# φ4 Population Rung — Plan (lock-step, single thread)

Green-lit by user: "lets test the population then."
Methodology constraints (binding): sequential lock-step — oracle designed with the
experiment, single thread, no swarm; certify each stage before building the next;
bit-identity mirror gates; checkpoint everything to /mnt.

## The question
Does the engine, with nucleation at its MEASURED corner (KNUC=1.0, KDIM=2.0,
ν = 4.86e-4/step/box), reproduce the sandbox population treadmill — and does the
60-monomer box behave as the sandbox predicts at the same N_tot?

Key structural fact the oracle must quantify: the box holds 60 monomers;
c*·V ≈ 36 free at steady state leaves ≈ 24 monomers of in-filament mass.
One mature filament (n̄ ≈ 24) exhausts the pool. A second filament would sit at
n̄ ≈ 12 — at/below the growth barrier (needs E ≥ 1.16, n ≳ 12). The sandbox
prediction is therefore sharp: births at ν, but newborns mostly STARVE and
dissolve; N_f oscillates 1↔2; the collective barely exists at this N_tot —
"nucleation is collective-limited, not rate-limited." The population assay at
60 monomers tests the failure regime, which is the falsifiable edge of φ4.

## Stage P0 — Oracle (sandbox, pre-registered predictions)
popsim at engine corner: N_tot=60, V=1728, k_nuc=3e-2 (= measured corner
k_nuc,eq=0.029), dissolve=True, no incumbent privilege (homogeneous population).
Pre-register BEFORE any engine run:
  1. N_f*(t) stationary distribution (expect: mostly 1, excursions to 2, rare 0).
  2. Birth/death currents (equal at stationarity) and turnover time.
  3. Newborn survival curve: P(a newborn trimer reaches n=12, n=25).
  4. c* and split invariance vs the no-nucleation rung.
  5. Inter-birth-interval CV (≈1 memoryless) + per-event timestamps for the
     deletion-test discriminator.
Output: POP_ORACLE.md with the five numbers/tables.

## Stage P1 — Engine surgery (nuc_fpt.ergo → pop_fpt.ergo)
  - Filament table: FILMON(f,j) monomer indices, LENF(f), MAXF slots (~8).
  - Trimer promotion: DIMKIN third-capture registers a living filament
    (3 monomers, 2 junctions — existing dimer+TRI3 spring pattern) instead of
    recycling to pool.
  - Death channel: pointed-end unbind at LENF=3 dissolves the filament
    (3 monomers → pool). No reflecting floor for ANY filament (homogeneous
    population, matches sandbox dissolve=True).
  - Bind/unbind/hydrolysis loops generalize over filaments × 2 tips.
    RNG draw ORDER for the single-filament path must be unchanged
    (loops consume no draws unless events fire).
  - Bonds: REBUILD_BONDS iterates filaments; BP exclusions per junction
    (certified pattern from nuc_fpt).
  - Corner params: KNUC=1.0, KDIM=2.0, DIMERS=1.
  - Diagnostics: census lines (filament birth/death events, STEP, filament id,
    length trajectory), plus existing dim/nuc/dimstat.

## Stage P2 — Mirror gates (certify before ensemble)
  G1: pop_fpt with KNUC=0, seeded trimer ≡ runs7, 0 diffs.
  G2: pop_fpt KNUC=0 ≡ nuc_fpt DIMERS=0 (same seed), 0 diffs.
  G3: promotion logic smoke test at KNUC=500 (soup regime) — no explosion,
      pool conserved, census sane.

## Stage P3 — Ensemble at the corner
16 seeds (77031 + i·7919), KNUC=1.0, KDIM=2.0, long enough for multiple
filament turnovers (shrink n̄≈24 at j≈2.4e-4/step ⇒ lifetime ~1-2e5 steps;
target ≥ 5e5 steps/run). 4-way parallel, certified toolchain.

## Stage P4 — Certification
Engine vs oracle side-by-side: N_f distribution, currents, survival curve,
c*/split, inter-birth CV. Verdict on the three sandbox predictions at engine
scale. Write POPULATION_LAW.md. Then checkpoint zip.

## Explicitly deferred
  - Filament diffusion/alignment mechanics (free chains diffuse; no force
    coupling yet — that's the motility rung).
  - Scaled box (N_tot ~ 600, N_f* ~ 13 true-collective regime) — needs
    Langevin slot/INIT surgery; separate rung if the corner test passes.
