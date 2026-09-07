# plan_formin.md — R2: formin-brush vs branched-brush comparison

Registered: 2026-09-02, before any engine build or run. Methodology:
sequential lock-step (oracle designed with the experiment), gates before
smokes, smokes before ensembles, checkpoint to /mnt. Single thread, no
swarm (standing user directive).

## Question

Post-R5 the stochastic branched brush is certified (BRANCH_LAW.md):
engagement n_eng 3.5 load-flat, stall ≈12 via compression recruitment,
isotropic mesh. The single-filament F2 formin is certified
(FORCE_LAW.md): power-stroke ratchet, flat j_on(F) to F=4, individually
unstallable by membrane pressure, slip-grip processivity.

**R2: what does a PROCESSIVE-ELONGATION brush do that the stochastic
branched brush doesn't — and vice versa?** (Biology: filopodia/filament
guidance vs lamellipodium mesh.) Factorial arms isolate the mechanisms:

| arm | PBR (branching) | FORMIN (tether) | status |
|-----|-----|-----|--------|
| A | 1 | 0 | DONE — runs17/runs18 (branched stochastic) |
| B | 0 | 1 | pure processive brush (this rung) |
| C | 1 | 1 | hybrid (this rung) |

## Mechanism (port of the certified F2 element, per-filament)

Engine: `brush_bfm.ergo` = brush_bra_r (SEGFIX + 400-gen + S4 + PREL +
xpt) + per-filament formin channel. Per active filament F, per step, only
when FORMIN=1 (params certified in F2: KF=2.0, S0F=1.25, FMAXT=5.0,
SMAXF=2.0, RGRIP=1.0, KORI=1.0):

- GRIPF(F): 0→1 when barbed tip within RGRIP of plane; yz anchor latched
  at grip moment; 1→0 (slip) when 3D stretch > SMAXF.
- Gripped: yz two-sided spring (2KF, capped FMAXT) to latched yz;
  x one-sided compression spring (tip past XP−S0F only), capped FMAXT,
  reaction added to FRCT (load path to piston, as F2).
- Gripped: tip axis relaxed toward +x at rate KORI (threading/polarization).
- **No RNG draws** → FORMIN=0 must be bit-identical to brush_bra.

New instrumentation (WRITE-only, gate-neutral, excluded from gate filter):
pstn gains trailing `grip %f` field (stationary-window mean gripped count);
`ori STEP mean|a·x̂|` per occ block (orientation polarization, O-F6).

## Registered oracles

- **O-F1 GATES**: brush_bfm(FORMIN=0, PBR=1) ≡ brush_bra and
  brush_bfm(FORMIN=0, PBR=0) ≡ brush_bra_b0 — 0 diffs, 300k steps, seed
  77031. Ghost scan 0 mismatches.
- **O-F2 processivity instrument**: stationary grip fraction (gripped /
  active filaments) ∈ [0.2, 0.6] at F=1 (F2-calibrated slip-grip band).
  Grip ≡ 0 → tether geometry broken; grip ≡ 1 → slip path broken.
- **O-F3 engagement**: arm B n_eng ≥ 3.48 (branched baseline) at F=1.
  Falsification: n_eng < 2 → processive holding does not scale to a brush;
  investigate tether/anchor geometry.
- **O-F4 force class**: per-gripped-tip barbed block:bind ratio ≈ 0
  (< 0.2) at all loads (power-stroke signature: spring retraction clears
  the register) vs the stochastic brush's 2–4. The discriminator is the
  BLOCK ratio, not j_on flatness (both classes have load-flat capture).
- **O-F5 stall** (hold-release force-balance instrument, PREL=300k, as
  certified in runs18): arm B grid F ∈ {4,8,12,16,20}. Registered window
  F_s(B) ∈ [6, 30]: floor from spring/backbone crush (F2 amendment 3),
  ceiling from slip-cap bound FMAXT·⟨n_gripped⟩. Registered mechanism
  discriminator: SLIP stall (grip fraction → 0 as F → F_s) vs CRUSH stall
  (n̄ → floor) vs RECRUITMENT stall (branched signature: n_eng rises with
  compression, margin concave).
- **O-F6 structure**: arm B polarized — stationary mean |a·x̂| ≥ 0.65 vs
  branched isotropic 0.46–0.49 (L-R5.5); n̄(B) ≥ 15 (processive growth).
- **O-F7 stability/conservation** (carried from O-R4 under ratified Amendment B-1):
  census conservation exact, ghost scan 0, N_f ≤ MAXF, occupancy
  instrumented, no SIGSEGV/hang over 1M steps.

## Stage plan

- **Stage F-a (build + gates)**: brush_bfm.ergo; O-F1 gates; compile
  hygiene. (~15 min)
- **Stage F-b (smoke)**: FORMIN=1, PBR=0, F=1, seed 77031, 1M steps:
  survival, O-F2 grip band, O-F7 conservation, first n_eng read. Check in
  before ensemble. (~10 min)
- **Stage F-c (law grid, clamped XPLO=5.5/XPHI=11.3)**: arms B and C,
  F ∈ {0,1,4} × seeds {77031, 84950} = 12 runs, 1M steps. O-F3/O-F4/O-F6.
  (~25 min in 3-worker pool, verify-before-delete runner)
- **Stage F-d (stall grid, hold-release PREL=300k, XPLO=1.5/XPHI=11.4)**:
  arm B: F ∈ {4,8,12,16,20} × 2 seeds = 10 runs; arm C: F ∈ {12,20} × 2
  seeds = 4 runs (additivity test at/above the branched stall). O-F5.
  (~30 min)
- **Stage F-e (write-up)**: FORMIN_LAW.md — processive vs stochastic brush
  laws, oracle scorecard, update ANALYTICS.md; checkpoint zip.

## Amendment F-1 (registered after Stage F-b smoke, before ensemble)

Smoke (FORMIN=1, PBR=0, F=1, seed 77031, 1M steps, clamped) of the direct
F2 port (S0F=1.25, RGRIP=1.0) showed the pre-registered grip-collapse
failure mode plus a geometry pathology:

- grip ≈ 2/22 (0.09, below the O-F2 band): in a brush only the longest
  filaments ever reach the XP−1.0 grasp ring; the F2 element was tuned
  for a single filament nucleated AT the membrane.
- S0F=1.25 parks tethered tips OUTSIDE the engagement window (NENG
  criterion PX > XP−1.0) and far from the contact cushion (XP−0.5): the
  tether acted as a spacer, neng collapsed to 0.2-1.1, fmean 0.6 < F=1,
  plane slow-crushing.

Amended geometry: **S0F 1.25 → 0.75, RGRIP 1.0 → 2.5** (variant F-1a;
F-1b with S0F=1.0 measured and dominated on no axis). Rationale: formins
are membrane-bound processive elongators — the biologically faithful brush
geometry holds tips at the contact zone, and the grasp ring must cover the
brush tip field. FMAXT/SMAXF/KF/KORI unchanged (F2-certified processivity).

Amended smoke (F-1a): grip 5.4/23 = 0.24 (in O-F2 band ✓), plane held
(fmean 2.08 ≥ F=1, xp 10.83 stable), neng 1.56, conservation clean,
full 1M completion. Observed phenotype: few long tethered rods (lenfil
up to 68 — power-stroke retraction keeps their tips fed) + baseline
unbranched-like short brush; tip orientation isotropic (mean |a·x̂| 0.50).

Registered expectation updates: O-F3 (n_eng ≥ 3.48) likely FAILS for arm B
— processive tethering does not multiply membrane-proximal tips the way
branching does; recorded as a scientific result if the ensemble confirms.
O-F6 (polarization ≥ 0.65) likely FAILS at KORI=1.0. O-F5 (stall) is now
the discriminating oracle: slip-cap ceiling FMAXT×n_gripped ≈ 25-30 ≫
branched 12 IF tethers bear load.

## Anticipated failure modes (pre-registered responses)

- Grip collapse in dense brush (tips crowded out of the RGRIP ring by WCA
  neighbors) → diagnose via grip fraction vs N_f; if confirmed, register
  RGRIP widening as Amendment F-x before rerunning.
- yz tether conflicts with S4 base anchors in arm C (double restraint
  over-constrains filament) → compare B vs C engagement; if C < B,
  document as mechanical interference finding.
- Formin brush crushes at low F (spring transmits load to backbone,
  filaments hit length floor) → that IS a registered O-F5 outcome
  (crush-stall mechanism), not a build failure.
