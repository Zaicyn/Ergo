# ANALYTICS.md — sparse mappings extracted from existing data (2026-09-02)

Purpose: answer R3/R4 design questions analytically from runs9-15 + probes,
avoiding parameter scans. Sources: runs15 ensemble (40 runs), cap150b,
brushc_f1_smoke (gm intact), FORCE_LAW.md (F1c per-tip stall).

## MAP 1 — Lifecycle / N_f design law (SOLVED, internally verified)

Data: 739 fdeath + 742 fbirth records in the F=1.0 arm tails (8 seeds).
- Two-regime survival: 68% of newborns die < 10k steps (gambler's-ruin
  infancy at len 3-5); survivors show hazard ≈ 0.021/1k steps ≈ KCAP·DT
  (0.03/1k) — i.e., death is cap-initiated, then pointed grind.
- Mean lifecycle E[τ] = 27.4k steps (fdeath sample) vs N_f/r_birth =
  10.7 / 4e-4 = 26.8k — independent estimators agree within 3%.
- Closed form:  N_f ≈ r_birth(c) · [0.68·τ_infant + 0.32·(1/KCAP + n̄_cap/g_p)]
  with τ_infant ≈ 3.5k, 1/KCAP ≈ 33k, n̄_cap/g_p ≈ 33k, g_p ≈ 3e-4/step.
- KCAP ↔ n̄: length-at-cap ≈ b/KCAP ≈ 10 at KCAP=0.03. Halving KCAP doubles
  n̄ and the survivor lifecycle (→ N_f ≈ 14-15 at N_tot=150 — needs
  MAXF>16 or lower budget). Doubling KCAP: n̄ ≈ 5, N_f ≈ 8.
- No scan needed: any (KCAP, N_tot) point is computable from this map.

## MAP 2 — Engagement is NOT reach-limited (R3 geometry scan ELIMINATED)

Data: n_eng/N_f vs zone depth z = x_p−1 across all five arms:
  z:        9.83   9.29   8.36   6.47   5.19
  n_eng/Nf: 0.063  0.083  0.103  0.137  0.150
Nearly FLAT while z sweeps half the box. Reach models (birth slab U[2,10.5]
+ episode reach, any projection factor η) predict a steep rise (0.12→0.66)
— falsified at any η. Diagnosis from bbind RGAP: new tips land ~3.3 behind
the margin (deep in the brush); tips arrest when CAPPED mid-brush, and
near-plane candidates are SGATE-blocked/ejected. The near-plane zone is
populated only transiently. Consequences:
- XNU_LO tweaks (birth slab nearer the plane) buy almost nothing —
  the R3 geometry scan is analytically ruled out, skipped entirely.
- The only in-engine lever: longer uncapped episodes (KCAP/2) so tips
  grow through to the plane before arrest. One confirmation run suffices.
- The structural fix is dendritic branching (R5): nucleation AT the
  membrane with inherited orientation — engagement by construction.
  This is now the analytically-preferred path, not just biological taste.

## MAP 3 — Force law from gap/attempt statistics (R4 mostly closed)

Data: bbind (success + gap fields) and bblk (blocked) per arm:
- Insertion vs load is FLAT (j/j0 = 1.02-1.04 to F=2; 0.89 at F=4) —
  exponential insertion law falsified (BRUSH_LAW.md).
- Load enters via the blocked fraction: 57% → 66% → 74% → 82% (F=0→2).
- Near-plane insertion flux (the protrusion-relevant channel) is
  non-monotone in the clamped frame (0.8e-4 → 3.0e-4/step): higher load
  presses the piston deeper, raising near-plane attempt rate. A clamped
  piston cannot measure protrusion velocity — this channel answers the
  force-response but not v(F).
- Stall: F_s ≈ 2.5-3 total, ≈ 1.9 per engaged tip — consistent with F1c
  single-filament stall (FORCE_LAW.md); load-sharing prediction:
  F_s(n_eng) ≈ 1.9·n_eng, so n_eng ≈ 3-4 → F_s ≈ 6-8. Tested at R5: see
  update below.

## MAP 2 UPDATE (R5, 2026-09-02) — engagement achieved by branching

The dendritic branching path (preferred above) delivered: S4 anchored
branching gives n_eng = 3.38-3.83 load-flat (F ≤ 4), P(bare) = 0.0000,
vs the unbranched n_eng/N_f ≈ 0.06-0.15 above. Engagement is structural
(branch daughters membrane-anchored at the junction), confirming the Map-2
diagnosis: reach was never the lever; local tip multiplication at the
membrane is. See BRANCH_LAW.md L-R5.1.

## MAP 3 UPDATE (R5) — load-sharing law validated, stall amplified 4×

R5 measured stall F\* ≈ 12 (runs18 force-balance grid F ≤ 12, margin
crosses zero at 11-12; pinned thin-brush anchor 11.4 ± 0.4). The R4
load-sharing law F_s ≈ 1.9·n_eng HOLDS per tip — but n_eng at the stall
point is 5.9, not 3.5: extreme compression recruits additional tips into
contact (load-adaptive engagement, L-R5.1/L-R5.6), so the system stall is
set by the compressed-brush limit ≈ 11.4-12, ≈ 4× the unbranched 2.5-3.
F_s ≈ 1.9-2.0 per tip at stall (12/5.9) — the per-tip law is intact; the
amplification is in the recruitment. With Amendment B-2 ratified, this
force-margin/stall form is the canonical protrusion metric for the 12σ box;
true drift v(F) remains deferred to the tall-box engine.

## MAP 3 UPDATE (R2, 2026-09-02) — processivity buys stall, branching buys engagement

The R2 factorial separates the two mechanisms. A pure formin brush (arm B)
keeps the slip-grip channel in its certified processivity band (grip
fraction 0.25-0.28 at F=1) but does NOT multiply membrane-proximal tips:
n_eng stays 1.56-1.70 at F=1, versus 3.48 for the branched brush. Under
compression the tethered brush recruits both engaged and gripped tips
(n_eng 2.5 → 7.0, grip 7.5 → 17 from F=4 → 20) and stalls at F_s ≈ 14-16.
The mechanism is recruitment-limited, not slip (grip does not collapse) and
not crush (n̄ stays 15-23 rather than falling to the floor).

The hybrid (arm C) is the strong architecture: at F=20 it remains
force-balanced (+0.01 margin in both seeds), with n_eng ≈ 6.8-7.3,
grip ≈ 21.6-24.0, n̄ ≈ 11.2-11.3, and no clamp occupancy. Branching
supplies the dense short-tip mesh; formin supplies processive load paths.
Single-filament power-stroke character does not dominate the brush-level
register by itself: arm B blk:bind per gripped tip is 0.29-0.71, above the
registered <0.2 discriminator, because the ungripped majority still makes
ordinary stochastic blocked attempts. See FORMIN_LAW.md.

## What still needs runs

The ordered R6-R12 roadmap is now registered in `NEXT_STAGES_PLAN.md`.
Remaining analysis-side items:

1. Optional F=13/14/15 bracket if a tighter F_s(B) estimate is needed;
   O-F5 is already decided by the measured 12/16 crossing.
2. Polarization variants only if orientation is load-bearing downstream:
   stronger KORI or a revised membrane-anchor geometry, pre-registered as a
   new amendment.
3. Tall-box engine for true v(F) drift and the φ5 1D-closure boundary table.
4. R6 adhesion/traction (reconsider S2 junction port) and crawling
   integration.

## MAP 5 (R6, 2026-09-02) — substrate adhesion certified: slip-bond traction law

R6 added the PADH substrate-adhesion channel (one dynamic slip bond per
filament at the pointed tail, plane XADH=2.0, capture slab 0.75) and passed
all registered oracles O-A1..O-A5 on the unbranched brush; R6 exit
criterion MET. Headline numbers:

- **Gates:** PADH=0 byte-identical to the certified brush_bfm parent over
  300k steps on three engine generations; MIRROR static cert
  CERT_ADH=28.4232861624127757 = KADH·d² exact, central FD error 5.826e-10.
- **Occupancy/turnover (O-A2):** 0.1824 / 0.1928 / 0.2863 at F=0/1/4
  (window [0.05,0.60]); ≥10k attach and rupture events per arm; attach and
  rupture rates balance to 4 significant figures — a steady-state turnover
  pool, not an arrested layer.
- **Slip law (O-A3):** pooled per-step exposure ML fit over 13,861,254
  exposures and 32,167 slip events gives β_A = 0.995474 ± 0.001413 (95% CI
  [0.992705, 0.998243]) vs nominal 1/FBA = 1.0; expected/observed 0.9984;
  decile calibration tracks; per-arm β ∈ [0.994730, 0.996086] — the
  registered Bell law is measured, load-invariant, and requires the PADHF
  per-step force record to identify.
- **Traction (O-A4):** every adhs window recomputes from per-step adhf
  forces to max err ≤5.82e-07 (%.6f rounding bound) — no phantom force
  source; \|mean trx\| monotone 0.664 → 0.673 → 0.974 (F=0/1/4), sustained
  ≥99.9% of windows.
- **Stability (O-A5):** exact conservation, ghost scan 0, exact adhesion
  inventory on all 16 R6 runs.
- **Release geometry (R6-e):** F=1 pushes the piston to the XPHI=11.3 clamp
  (below stall); F=4 fluctuating balance x≈7-8.5 (near stall); F=8
  compresses to the XPLO=5.5 clamp (above stall) — adhered-brush stall
  bracketed 4 < F* < 8 vs 2.5-3 unbranched without adhesion. B-2
  force-margin remains the ratified 12σ-box criterion; R6-e is not a v(F)
  assay.
- **Known limitation (R6-f, user-approved, R7 handoff):** branched arms
  collapse adhesion occupancy 3.2× (0.0590 PBR=1/FORMIN=0, 0.0627
  PBR=1/FORMIN=1 vs 0.19 unbranched; traction 92.7%/96.1% of windows) —
  pointed tails are consumed at S4 branch junctions and nfil≈30 inflates
  the denominator. Both arms structurally clean. The R6 exit criterion is
  defined on the unbranched brush and fully met; interference resolution
  deferred to R7+, where crosslinking changes mesh architecture.

Full certification: ADHESION_LAW.md. Engine `phi4/brush_adh.ergo` SHA256
f709fb4453a1c6c6405ca33f9600844253ee7e35296acdb208f8d79bbf7075b8 (merge
615c8ae); runs and analyses under `phi4/runs20/`.

## MAP 6 (R7, 2026-09-02) — filamin crosslinking certified: cohesion is contractile

R7 added the PXL filamin-like crosslink channel (transient inter-filament
slip bonds between bound-monomer head beads, min-distance selection within
RXLK=2.0, rest length DX0=1.5, Bell slip rupture) and passed all registered
oracles O-X1..O-X6 (O-X3 as the X-6-registered O-X3a + O-X3b) on the
unbranched brush; R7 exit criterion MET. Headline numbers:

- **Gates:** PXL=0 byte-identical to the certified brush_adh parent over
  300k steps on both arms — log hashes a67e3bbf.../db4b42fb... are exactly
  the R6 gate hashes (lineage continuity). MIRROR static cert CERT_XL=0.25
  = KXLK·(d−DX0)² exact at d=2.0; differential FRC ±1.0 x̂ bitwise; central
  FD error 7.62e-10. RNG slots 4700–6873 disjoint; XLNF per-step force
  record registered at build time.
- **Turnover (O-X2):** occupancy 0.6693–0.7403 across all law-grid arms
  (window [0.1,1.5]); attach/rupture balance ≤ 0.0011; drift ≤ 0.24; ≈10k
  events per run — a steady-state turnover pool, not an arrested mesh.
- **Slip law (O-X6):** pooled per-step exposure ML fit over 47,100,489
  exposures and 42,984 slip events gives β_X = 0.995310 ± 0.002709 (95% CI
  [0.990001, 1.000619]) vs nominal 1/FBX = 1.0; expected/observed 1.0014;
  decile calibration tracks; per-arm β ∈ [0.985842, 1.005299].
- **Cohesion (O-X3 saga):** the registered premise "cohesion ⇒ taller
  brush" FAILED at F4 seed 84950 (XP_ON 6.911 < XP_OFF 7.682); registered
  stop + investigation found a contractile internal-tension network — links
  born compressed (⟨d_birth⟩ 1.24–1.30 < DX0), live stretched (1.85–1.87),
  rupture overstretched (d≈2.45); freely-jointed chains ⇒ tension only; top
  layer pulled down 73–76%; causal growth inhibition (paired p ≤ 2.5e-14).
  After amendments X-4 (underpowered, FAIL) and X-5 (O-X3a mechanism PASS
  all 5 arms; O-X3b 6-seed FAIL), amendment X-6's pooled 10-seed t-test
  PASSED decisively: mean Δx95 = −0.3823, 95% CI [−0.6406,−0.1239],
  t=−3.347, p=0.0043, Wilcoxon 0.0098. Registered finding: shortening
  attenuates with load (F2 −0.38 → F4 −0.13) because tether tension is
  ≈10–20% of F_EXT. A taller crosslinked brush requires bending rigidity
  (R8+ territory).
- **No collapse (O-X4):** rel-rate ratios 1.086/0.936/1.097, displacement
  ratios 0.983/1.002/0.982, cap-pin ≤ 2 consecutive windows in every
  certification arm.
- **Stability (O-X5):** exact conservation, ghost scan 0, exact crosslink
  inventory, and max\|netf\| = 0 zero-bookkeeping on all 44 runs21 logs.
- **Integration (R7-f, diagnostic):** crosslink–adhesion interaction is
  architecture-dependent — branched FORMIN=0: adhesion occupancy 0.0590 →
  0.0767 (+30%), traction 92.7% → 96.5%; hybrid FORMIN=1: 0.0627 → 0.0373
  (−40%), traction 96.1% → 81.2%. Adhesion bonds carry \|F\|≈3.6 vs xlk
  ≈1.4. MAXXL=24 pool pins 7–14 windows in branched meshes (pool-limited;
  registered for R8+, non-gating).

Full certification: CROSSLINK_LAW.md. Engine `phi4/brush_xlk.ergo` SHA256
a3ed43347392aa97f7ad2bde5ad0d7c1ce0e09e244220cedba59edc7ea46944a (merge
7ff0566); runs and analyses under `phi4/runs21/`. Note:
`law_grid_analysis.txt` was regenerated after an analyzer fix (NaN
displacement lines); current version SHA256 94b6585b..., stale version
preserved at `runs21/superseded/law_grid_analysis_nan_stale.txt`.

## MAP 7 (R8, 2026-09-03) — bundle polarity certified: selection ≠ persistence

R8 added the PBUND bundle-polarity gate (deterministic cosθ acceptance on
crosslink attach, tangent t(B)=unit(P(B+1)−P(B−1)) pointed→barbed,
interior + contour≥4 eligibility, COSB=0.5, PBUND=1 parallel / PBUND=2
antiparallel, ZERO new RNG draws, `bpol STEP I J cos` record) and passed
all registered oracles O-B1..O-B5 (O-B4 FAIL as registered, then PASS
under the user-registered three-tier Amendment B-1). R8 exit criterion
MET; R8-f branched-mesh diagnostic COMPLETE under the force-first
doctrine (books PASS, signs PASS; distributions as ranges). R8 fully
closed. Headline numbers:

- **Gates (O-B1):** PBUND=0 byte-identical to the certified brush_xlk
  parent over 300k steps on both arms — log hashes a67e3bbf.../
  db4b42fb... are exactly the R7 (= R6) gate hashes (lineage continuity).
  MIRROR sign battery zero errors (par acc cos +1.0 / anti rej cos −1.0,
  exact reverse PBUND=2; eligibility negatives never attach); CERT_XL =
  0.25 exact; differential force ±1.0 x̂ bitwise; central FD 7.62e-10.
  RNG 25=25 sites, span 4700–6873 untouched; 50k PBUND=0 ≡ parent
  byte-identical (007e6b2b...).
- **Instrument (O-B2):** 100% attach-class purity, zero sign errors
  across all 36k+ accepted attaches of the program (MIRROR battery, 50k
  smokes 369/369 + 416/416, constructed pairs 133/87, brush arms
  8876/8770/9641/8209).
- **Stability (O-B3):** constructed-pair lifetime medians 895.0/831.0
  (n=133/87), ratios 1.65/1.53 vs the R7 median and 0.70/0.60 vs the
  slip-law prediction at measured force — both readings inside the
  registered [0.5, 2.0]; S(10×med)=0; longest < 20× median.
- **Selectivity (O-B4 saga):** the registered unstratified live-fraction
  ≥2.0 criterion FAILED (1.58/1.59 PB1, 1.62/1.64 PB2; all secondary
  windows green) because it conflates selection with persistence:
  crosslinked pairs rotationally diffuse ~54–56° RMS per 500-step dump
  (age-independent, control-identical 53.6° — universal thermal
  diffusion), so class memory (half-lives 212/284 steps = 0.36/0.57×
  lifetime medians; τ_cos ≈ 130/295 steps; first-exit KM 405/428 steps)
  decays 2–3× faster than links turn over and steady-state enrichment
  ceilings at ~1.6 (mixture model obs/pred 0.998–1.016). Amendment B-1
  (user-registered): primary young-link (age<250) enrichment 2.55/2.54
  (PB1), 2.47/2.55 (PB2) — PASS; secondary half-life ≥150 steps and
  ≥0.3× median — PASS; tertiary mixture consistency, diagnostic-only.
  Ground truth (engine-native lpol, stripped-log byte-identity ×3)
  reproduced every load-bearing replay number (enrichment ≤0.006, age
  bins ≤0.005, half-lives ≤2 steps) before registration.
- **No collapse/fusion/leak (O-B5):** conservation exact (400 brush / 39
  constructed), ghost scan 0, crosslink inventory exact (incl. the
  predicted t=0 orphan xlkr), max\|netf\| = 0 every window, nfil
  continuity exact, NUL-free, attempt=1 on every certification log.
- **Registered caveats (non-gating):** replay prepend ambiguity
  verdict-insensitive (worst case 13/6538 samples, ≤0.005 shifts; R9+
  tightening candidate — now includes the R8-f dense-branched
  topology-reconstruction FAIL, bounded by exact-subset ~1e-6 + lpol
  cross-check); eligibility flux thin in constructed geometry
  (3–5e-4/window); age cutoff ≤250 locked (pooling to <500 dilutes PB1
  below 2.0 on physics).
- **R8-f branched-mesh diagnostic (PBUND=2, PBR=1, FORMIN=0, PADH=1,
  F=1, seeds {77031,84950}, 1M; logs f8a093fd.../f4015fbc...):** books
  PASS (conservation exact, ghost 0, xlk + adhesion inventories exact,
  max\|netf\| = 0 over 2000 windows/seed, nfil event-exact); signs PASS
  (24,436 bpol all cos ≤ −0.5, 100% antiparallel). Measured ranges:
  occupancy nxl/nfil 0.3923–0.4328 (R7-f 0.7299, attach rate halved);
  **MAXXL=24 pinning 0/1000 windows both seeds — the R7-f pool watch
  item RESOLVES**; tension xlk live mean \|F\| 0.868–0.917, rupture
  median 1.517–1.683 (max 3.000 = SMAXX boundary), adh \|F\| 2.07–2.52;
  rupture mix slip 80.0–81.5%, endpoint causes ~3× rarer than R7-f;
  lifetimes median 657–718; live antiparallel 0.388 vs branched control
  0.2277 → 1.705–1.706×, half-lives 275–295 steps = 0.41–0.42× medians,
  mixture 0.393/0.408 predicted vs 0.388 observed, lpol cross-check
  (0.383/0.377) agrees. Caveats registered: analyzer
  topology-reconstruction FAIL on dense branched logs (bounded as above;
  flagged-exclusion sensitivity nan, lpol covers); s84950 FINAL lenfil 0
  = filament-1-centric record artifact, mesh healthy (final nfil=31).

Full certification: BUNDLE_LAW.md. Engine `phi4/runs22/bundle_pol.ergo`
SHA256 fb1c8d281b72816304a8bf13e9b66e815ec75200c20803c31879011b46507935
(merge d84f3c6; 2974 lines, +245 vs parent, 0 parent lines touched); runs
and analyses under `phi4/runs22/`. Slip-law carryover from R7 (no XLNF=1
law grid; XLNF=0, ~56 MB logs); nothing zipped pending user go-ahead.

runs22 layout and oracle evidence map:

- `runs22/static_cert/` + `runs22/smokes/` + `runs22/SELFTEST_I.md` —
  R8-a: MIRROR sign battery, spring/FD re-cert, RNG scan, PBUND=0
  byte-identity (O-B2 statics, O-B1 statics).
- `runs22/gates/` — O-B1: both 300k arms byte-identical to archived R7
  parent logs.
- `runs22/ANALYZER_I_VALIDATION.md` + `runs22/analyzer_valid/` — stage_i
  synthetic (8/8) and real-log validation.
- `runs22/r8c/` — O-B2 runtime, O-B3, O-B5 (constructed pairs, PCERT
  diagnostic variant — runs22 only, not in the certified engine).
- `runs22/r8d/` — brush smoke + archived R7 control replay
  (`r7c_control_xlk_on_f1_s77031.analysis.txt`).
- `runs22/r8e/` — O-B4 FAIL as registered (`OB4_DECISION.txt`), ensemble
  analyses, replay sensitivity readouts.
- `runs22/ob4_investigation/` — age-stratified persistence + ceiling
  model (`ob4_report.txt`).
- `runs22/ob4_verification/` — lpol ground truth, stripped-log
  byte-identity proofs, rotation timing (`OB4_VERIFICATION.md`,
  `ob4_lpol_verification.txt`); PLPOL variants runs22-only.
- `runs22/r8f/` — R8-f branched-mesh PBUND=2 diagnostic COMPLETE:
  `R8F_REPORT.md` (f7965feb...), `r8f_age_analysis.txt` (2f8d96d3...),
  `r8f_pinning_results.txt` (98b237fd...), per-seed analyzer reports
  (a72376e5.../478e0098...), logs f8a093fd.../f4015fbc... + lpol
  cross-check logs (7679670e.../5892f80c...).

Key scripts (SHA256):

- `runs22/stage_i_analysis.py` (brush/pair analyzer, live-cosθ replay) —
  4d2b399cc63f5ac4c18b0473e0b6da541820b348bc16fb2d79dbaffd483277ea
- `runs22/r8c/r8c_constructed_analysis.py` (constructed census) —
  529ca9047837850a201f70b44e081ebf23ecad159cb8032ecadae5083e41e5f2
- `runs22/ob4_investigation/ob4_age_analysis.py` (age stratification) —
  53799a775f96734f9318cce07c76a1ed1071dd2c0c682e692dbb7d47403e4110
- `runs22/ob4_verification/lpol_analysis.py` (engine-native ground
  truth) — 70158f94bd2a0607afb85cd49c396e300e05eb3e04ea87de4d86cd15bad26f8e
- `runs22/r8f/stage_i_branched.py` (branched-mesh analyzer wrapper) —
  5e9ed1c917669e7bb2a9e82260e2c8ae36623a06ec13e0c3e453f9f4dd4cd9cc
- `runs22/r8f/r8f_age_analysis.py` (branched persistence, ob4 method) —
  43e959a59d0f05047e9fe3bacf8f3adc3551f8f34a9a73afdc874961cb0f767d
- `runs22/r8f/r8f_pinning_analysis.py` (pool pinning + adhesion + nfil
  continuity) — af12785188b0a60d0595df570d8b9e1eaa0111e0cb882dd4fafa7bbf624991a9

## MAP 8 (R9, 2026-09-03; doc pass 2026-09-04) — minimal parallel bundle certified; O-P4 FAIL = tip-linkage bottleneck

R9 composed the R6 adhesion + R7 crosslink + R8 PBUND=1 gate + FORMIN
channels on a deterministic seeded 5×8 parallel cluster (PCLU), added a
distal tip-zone slip-bond adhesion instance (PTIPA, RNG block
6900–6963) and records-only tip instrumentation (PTIP: tip/tipa/tipr),
and certified the engine through R9-b (all hard gates PASS; O-P1
byte-identity at MIRROR/50k/300k). The headline force oracle **O-P4
FAILED on physics**: pooled traction-magnitude ratios 0.9506 (|tr|) /
0.9436 (|trx|) — wrong direction; distributions never disjoint; the
signed-trx offset +0.3406 (p=0.0317) satisfies neither pre-registered
limb. The bundle polarizes (live parallel 0.374–0.376 vs control
0.238–0.241, ≈1.56×, young-link carried, R8 rotation timing reproduced
on two seeds) but tip-bond occupancy (~9.8 vs ~10.4), rupture |F|
(~2.8, ~97% > FBA=1.0), and formin grip are unchanged — traction is
set by the tip interface, not bundle polarization. Bundling halves
crosslink occupancy (~8 vs ~16) and attach/rupture flux (~10 vs ~21 per
1k), leaves npoly mean/variance seed-dependent, and does not protect
incumbent filaments (5/10 vs 4/10). **R9 exit criterion NOT met; R9
closed with the finding registered (user directive 2026-09-03) as the
R10/R11 design target: strengthen the tip-linkage pathway.**

Full certification: PARALLEL_BUNDLE_LAW.md. Engine
`phi4/runs23/filopod_min.ergo` SHA256
`6a343fdef82c16a74a8e862b33d44cd88bb4101b9079bc684d3f38b70f498d8f`
(3499 lines, +525/0 vs bundle_pol `fb1c8d28...`, merge `df789f3`; all
hashes recomputed this doc pass); runs and analyses under
`phi4/runs23/`. Nothing zipped.

runs23 layout and oracle evidence map:

- `runs23/filopod_min.ergo` + `runs23/SHA256SUMS` — certified engine and
  stage hash manifest. NOTE (doc pass): SHA256SUMS lists
  `build/filopod_min.bin` (`f5814ebf...`) and `build/op1_dyn.ergo`
  (`45902252...`) under a `build/` directory absent from the current
  tree (compile artifacts, reproducible; flagged, nothing deleted this
  pass).
- `runs23/static_cert/` — R9-a: MIRROR-off byte-identity (`3f3269db...`),
  CERT_TIP etip=2.205 exact, FD exl 1.398e-10 / etip 6.756e-10 / eadh
  6.810e-9 (<1e-8, recomputed from outs), CERT_FPOL sign battery zero
  errors (O-P1 statics + doctrine battery).
- `runs23/smokes/` — O-P1 50k byte-identity (`007e6b2b...` = R7/R8
  reference); cluster smoke 50k books PASS (xlk 397/389, tip 422/412,
  recomputed).
- `runs23/gates/` — O-P1 (R9-b): 6/6 child==parent 300k byte-identical,
  PBUND∈{0,1,2} × seeds {77031,84950} (`16c9db1c...`/`5636a7eb...`/
  `b84d72e1...`/`c5444043...`/`cb3e60fe...`/`8ddb802b...`, recomputed);
  provenance caveat: parent refs are R9-b-produced.
- `runs23/r9c/` — R9-c: bundled/control 1M s77031 logs (`2144637e...`/
  `e5a818e4...`), books PASS both arms (counts recomputed),
  `r9c_op4_report.txt` = preliminary O-P4 NEGATIVE + measured ranges
  (O-P4 single-seed, O-P2/O-P3/O-P5 ranges, books battery).
- `runs23/r9d/` — R9-d: s84950 arms (`342c9f16...`/`c59f9684...`) +
  lpol verification (`90b95d84...`, stripped-log byte-identical →
  instrument valid; lpol vs replay ≤0.0013); `R9D_REPORT.md`;
  `r9d_op4_pooled.txt` = FORMAL O-P4 FAIL numbers; polarization replay
  outputs `replay_{b7,c7,b8,c8}.txt` (O-P2; post-burn-in reconciliation
  exact on all 4 arms, flagged dumps all pre-burn-in).

Key scripts (SHA256, all recomputed this doc pass):

- `runs23/clu_smoke_analysis.py` (cluster smoke books battery) —
  980ddd41af96cbec5b7e145771b50a7a52542b06a09cffb699bd3e7d249fcfb9
- `runs23/r9c/clu_books.py` (PBUND-aware books checker, R9-c/d) —
  c4ad58d4142a9bd497900d8b1dcdf59b0842b27a6d740f95537c9ef6c74c9309
- `runs23/r9c/r9c_op4_analysis.py` (single-seed O-P4 + ranges) —
  f588476b67921ab385b76287d73d3298524338c051819a836719e6439bed0ecc
- `runs23/r9d/replay_r9.py` (certified stage_i replay + PCLU topology +
  chained-prepend fallback) —
  5b5fa8fb6b2804517dd0e1b0cb6bb5b2c1ddbbcb0f4bab3828f6d8f6cf3f0b8e
- `runs23/r9d/r9d_pol.py` (polarization replay driver, 4 arms) —
  40edf225d4973a547c782d265bc2f6d51bfa4dff07c08e8d93523e18935c2747
- `runs23/r9d/r9d_op4_pooled.py` (pooled formal O-P4 verdict) —
  6d9b9178ef277b904ad8f36a311b7f33065585ac9d211c3b996137774ed2da98

## MAP 9 (R10, 2026-09-03/04; doc pass 2026-09-04) — myosin contractile unit certified: correct sign, finite stall, Bell turnover

R10 added the PMYO bipolar-motor channel (two heads coupled by the R7
crosslink spring law; contour-based barbed-ward stepping via NEXTM with
stall clip v=VMYO·(1−FAX/FSTALL); Bell slip KOFFM·EXP(|F|/FBMYO); SMAXM
hard release; RNG block 6970–7001; records myoa/myor/myost/myos with
step-0 constructed myoa) on constructed antiparallel/parallel
8-monomer track units with both ends KSEED-anchored (fixed endpoints,
frozen track kinetics). **All oracle classes PASS; R10 exit criterion
MET.** Headline numbers: directionality as a data-structure invariant —
contour sign MNEW=MOLD+1 on 2959/2959 myost events program-wide (150
R10-a + 2809 R10-c, recomputed; the single 1/107 lab-x exception is
registered tip-buckling physics, contour-correct); O-M3 contraction
4.304 vs 0.360 parallel control (12×; parallel-silence hard limb PASS);
O-M4 KSEED anchor-compliance load sweep (registered — F_EXT lives only
in the PSTN piston channel): force saturates 4.30 (max 5.17, no
runaway), velocity collapses 0.50→0.165→0.023 across F≈4.0–4.5, stall
at the FSTALL=4.0 scale; O-M5 balanced turnover, 100% Bell slip
(364/364 cause 1), max lifetime 31154 ≪ 300k — no clamp; O-M6 books
exact on all 7 logs (600 censuses/windows each). R11 design numbers:
stall scale 4, force range 4.30→0.91 over KSEED 5.0→0.1, velocity
0.278→0.081 len/time, turnover 1.1e-4–3.2e-4/step, single-motor
capture-limited occupancy.

Full certification: MYOSIN_LAW.md. Engine `phi4/runs24/myosin_unit.ergo`
SHA256 `2806ed054ecebf0fe9eb6db93af39d433991dfd97d36b534afdb22c4d923110f`
(4247 lines, +748/0 vs filopod_min `6a343fde...`, merge `8beb34d`; all
hashes recomputed this doc pass); runs and analyses under
`phi4/runs24/`. Nothing zipped.

runs24 layout and oracle evidence map:

- `runs24/myosin_unit.ergo` (+ `.bin`) — certified engine; parent
  re-verified untouched after every stage.
- `runs24/static_cert/` — R10-a: mirror byte-identity to R9
  (`3f3269db...`); cert_myo1 parent CFG(102)/FRC(102)/CERT(12) lines
  byte-identical to R9 cert base (recomputed by cmp); CERT_MYO
  emyo=0.25 exact; channel-isolated FD beads 105/113 err
  3.18e-10/7.62e-10 (recomputed) (O-M1 statics + FD gate).
- `runs24/sign/` — O-M2 deterministic sign battery (VMYO=120, KOFFM=0):
  15/15 strict lab signs, both arms (recomputed).
- `runs24/smokes/` — O-M1 50k byte-identity (`007e6b2b...` = R7–R9
  reference, recomputed); unit micro-smokes (books PASS; stall
  saturation meanf 4.2669 over 40k–50k, max 5.06; parallel silent;
  turnover 14/13 and 6/5; lab-sign ranges 106/107, 28/28 — recomputed).
- `runs24/gates/` — O-M1 (R10-b): 6/6 300k byte-identical to the R9-b
  references (same six hashes, recomputed).
- `runs24/r10c/` — R10-c: 7 constructed-unit runs (PMYO=1/2 pair at
  KSEED=5.0 + PMYO=1 sweep KSEED∈{2,1,0.5,0.25,0.1}; 300k, s77031);
  `R10C_REPORT.md` (runs24/ top level) = O-M2 2809/2809, O-M3
  4.304/0.360, O-M4 curve + stall read, O-M5 turnover table, O-M6 books
  (all headline counts recomputed this doc pass from the logs).

Key scripts (SHA256, all recomputed this doc pass):

- `runs24/myo_books.py` (books battery incl. motor inventory) —
  7e1f0ac96dc90fbc8c8605099b275e7e73f72aaa34b4285de416ae2c4cc7f7ab
- `runs24/r10c/r10c_analyze.py` (R10-c analyzer: contour invariant,
  F-V curve, turnover, books) —
  039601924f3d9195495a9c52cee7411e08c7dd2eed9593ccabc39071e34eaea5
## MAP 10 (R11, 2026-09-04; doc pass 2026-09-04) — stress fiber certified: stationary contractile tension, both-ends inward traction, anchor-competition finding

R11 added the PSF constructed-fiber + SF slip-bond anchor channel
(alternating-polarity 6-filament ring, barbed-end grips at both
substrate planes on the certified R6 slip-bond law verbatim; dynamic
PMYO=1 myosin ensemble on the antiparallel overlap; PBUND=2 crosslinks;
PSEV deterministic midplane sever machinery with cause-5 releases;
records sfa/sfr/sfas/fib/sev; RNG block 7010-7073) on the certified R10
parent. **All hard gates PASS; R11 CLOSED with the exit criterion MET
and one registered measured qualification.** Headline: tension positive
and stationary in all 4 1M arms (means 17.26/10.31/10.43/13.25,
93.6-98.3% windows >0); both-ends simultaneous inward traction on
main_s77031 (end0 +0.490 at 75.5% bonded duty, end1 -0.254 at 16.1%,
fmag~2.0 both ends); rupture-dominated anchor competition concentrates
load on one seed-selected anchor in the unperturbed steady state
(s84950: right 98.9% vs left 11.7%); both sever arms REPAIRED
(re-anchored both ends at 84-94% duty, tension transient then ~13
sustained, remnants persist/grow; cause-5 sever-release exercised
program-wide, myor x1 + xlkr x2 in sev_s77031). Hard gates: O-S1 7/7
byte-identical (R11-b), O-S7 books PASS all 4 logs (2000 censuses each,
max|netf|=0), FD 2.8e-10/1.5e-9, frozen-kinetics sign battery 80/80.

Full certification: STRESS_FIBER_LAW.md (incl. laws L-S1..L-S6, the
UB-landmine permanent caution, and doc-pass discrepancy notes). Engine
`phi4/runs25/stress_fiber.ergo` SHA256
`3a6cc866b869de69f09683f3cd61a0c93dba89b8136ea5a05ffef39ef6faed68`
(5058 lines, +811/-0 vs myosin_unit `2806ed05...`, merge `049ff28`; all
hashes recomputed this doc pass); runs and analyses under
`phi4/runs25/`. Nothing zipped.

runs25 layout and oracle evidence map:

- `runs25/stress_fiber.ergo` (+ `.bin`) — certified engine; parent
  re-verified untouched after every stage.
- `runs25/static_cert/` — R11-a: mirror byte-identity to R10/R9
  (`3f3269db...`, recomputed); cert_sf1 parent CFG(118)/FRC(118)/CERT*
  lines byte-identical to cert_myo1.out (recomputed by line extraction);
  SFAC x2 + CERT_SFA esfa=1.0 exact; channel-isolated FD beads 125/133
  err 2.8e-10/1.5e-9 (recomputed from fd_sf{125,133}_{plus,minus}.out).
- `runs25/sign/` — constructed frozen-kinetics sign battery
  (`sign_sf1.log` `cb1e4e96...`): 80/80 contour-invariant AND strict
  lab signs (38/38 left dx<0, 42/42 right dx>0 — recomputed).
- `runs25/smokes/` — O-S1 50k byte-identity (`op1_50k.log`
  `007e6b2b...` = R7-R10 reference, recomputed); reg. 11 micro-smoke
  `sf_50k.log` (`e7576aaf...`: books PASS; tension >0 in 94/100 windows,
  2nd-half mean 9.60, max 58.59; sfr 241 = 239 slip + 2 cause-3, median
  lifetime 385; last right-end attach 9940 — all recomputed); sever-arm
  smoke `sf_sev_50k.log` (`48d3d8a3...`: sev 25000 F6->G7, remnant
  lengths 58/4 exact, 0 cause-5 — the erratum-7 coverage gap);
  construction probes probe0/probe0psf0/probe1 (1-step construction
  verification, 54/54 monomers, max err 7.7e-4).
- `runs25/gates/` — O-S1 (R11-b): 7/7 byte-identical — 6 os1 300k logs
  hash-equal to the runs24 om1 references (`16c9db1c...`/`5636a7eb...`/
  `b84d72e1...`/`c5444043...`/`cb3e60fe...`/`8ddb802b...`, recomputed)
  + os1x_pmyo1_50k.log `0a4ba14c...` = R10-a smoke reference.
- `runs25/r11c/` — R11-c: 4 anchored-copy 1M runs (mains PSEV=0, sever
  arms PSEV=1/SEVSTEP=500, seeds {77031,84950}): main_s77031
  `e72842a9...`, main_s84950 `e5b2b226...`, sev_s77031 `f0a6e71e...`,
  sev_s84950 `8cfd9240...` (all recomputed); `*.analysis.txt` = O-S2..
  O-S7 measurement record (BOOKS PASS x4); determinism chains verified
  (main_s77031 = sf_50k through 50000; sev = main through 499);
  `driver.log` (run record); budget 4/6, reserves unspent.

Key scripts (SHA256, all recomputed this doc pass):

- `runs25/sf_books.py` (R11 books battery incl. SF per-end inventories,
  sever checks, SEVSTEP=25000 hardcoded — mains cross-check) —
  01077b09817bbd017a307d57ee6f30b650260d39c9fd7d86af42fc8dde80541d
- `runs25/r11c/r11c_analyze.py` (R11-c analyzer of record:
  SEVSTEP-parameterized books re-derivation + reg-8 R6-transfer re-key +
  O-S2..O-S6 measurements) —
  36e7c5a27e28eb3529851b70c6cc161398a99f72a6fed31c68f380dfef54b290
