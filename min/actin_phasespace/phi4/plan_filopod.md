# R9 Oracle — Minimal Parallel Bundle (filopod_min.ergo)

Registered 2026-09-03 under the force-first doctrine (user directive:
"fibers are going to move, rotate differently, be differing lengths — we
can guess at ranges but that's about it"; "the only oracles we can rely
on here are forces"; autonomous execution, no mid-stage decision prompts;
halts only on hard-gate failures, which mean bugs not physics).

Roadmap source: NEXT_STAGES_PLAN.md §R9. Parents: R6 adhesion
(brush_adh.ergo f709fb44…), R7 crosslinking (brush_xlk.ergo a3ed4334…),
R8 bundle polarity (bundle_pol.ergo fb1c8d28…, CERTIFIED through R8-e
under Amendment B-1).

## Question

Can formins, parallel-bundle crosslinking, and tip adhesion organize a
persistent, force-bearing parallel bundle — without myosin?

This is NOT the full filopodium: no membrane tube, no guidance field, no
detailed tip complex. It is the simplest non-contractile bundle assay
validating the shared machinery before R10 myosin.

## Doctrine (binding for all R9 stages)

- **Hard gates (binary; failure = bug = STOP with evidence):**
  force closure (max|netf| = 0), FD vs analytic forces < 1e-8 on any new
  or recombined force path, energy accounting, monomer conservation,
  exact inventories, ghost scan, no nfil discontinuities, instrument
  neutrality (byte-identity under inert amendments), and O-P1 channel-OFF
  byte-identity to the certified R8 parent.
- **O-P4 force is the headline gate:** tip traction/stall vs the
  unbundled control, measured as a force ratio with per-seed spread.
  Registered direction: bundled > unbundled. The registered FACTOR is
  set from the R9-c measurement itself (pre-registered threshold-free:
  the factor is reported, and the bundle is certified force-bearing if
  the per-seed traction distribution is disjoint above the control's,
  or the pooled mean exceeds the control by a factor ≥ 1.5 with
  Neff-corrected significance — the method, not the number, is
  pre-registered).
- **Measurements as ranges (never gates):** bundle axis correlation
  (O-P2 polarization), bundle survival vs ordinary filament lifetime
  (O-P3 persistence; "no immortality" checked via books), monomer and
  filament turnover inside the bundle (O-P5), length distribution,
  rotation/persistence of bundle polarity (R8-certified instruments).
- Sign errors in any polarity record remain zero-tolerance (correctness
  property, not a distribution).

## Mechanism sketch (R9-a builder scope)

Engine candidate: `filopod_min.ergo`, parent `bundle_pol.ergo`
(do-not-modify; anchored additive amendments only).

- Composition, not new physics: R6 adhesion channel + R7 transient
  crosslinks + R8 PBUND=1 parallel gate + the existing FORMIN channel
  used at the distal end.
- New machinery limited to: (a) a seeded/recruited parallel filament
  cluster (deterministic seeding — ZERO new RNG draws, or hash-drawn
  from registered new slots if stochastic seeding is unavoidable);
  (b) tip-zone adhesion placement (distal tip or along shaft, as
  registered by the builder with rationale); (c) tip force/traction
  instrumentation records (records-only, byte-identity inertness proof).
- All existing RNG slot discipline preserved; any new draws get a
  registered slot block documented in this file before build.
- Slip-law carryover from R7/R8 (no law grids — space discipline).
- Log budget: 1M-step logs ~56MB; ensemble total target < 1GB. No zips.

## Stages

- **R9-a:** build + static/FD certification (constructed parallel cluster;
  force closure on all composed paths; O-P1 inertness) + review + merge.
- **R9-b:** O-P1 gates (all new channels OFF ≡ R8 parent, byte-identical,
  both seeds).
- **R9-c:** bundle smoke + O-P4 tip traction/stall vs unbundled control
  (same census, F_EXT registered by builder; seed 77031 first) + books
  battery.
- **R9-d:** measurement ensemble (seeds {77031, 84950} × bundled/
  unbundled; ranges for polarization, persistence, turnover, lengths;
  pooled O-P4 force verdict by the pre-registered method).
- **R9-doc:** PARALLEL_BUNDLE_LAW.md + ANALYTICS.md MAP 8.

## Registered failure responses

- Hard-gate failure: STOP, surface evidence, no parameter tuning.
- Near-zero bundle assembly in R9-c: measure nucleation/eligibility flux
  first, register finding, adjust GEOMETRY (seed cluster size/placement)
  by amendment — never physics parameters.
- Tip adhesion rupture-dominated traction: report the traction
  distribution as-is (ranges); do not strengthen adhesion to hit a number.
- Disk pressure: compress completed-stage logs before any deletion;
  deletions only on explicit user word.

## Exit criterion

A stable, polarized, force-bearing parallel bundle exists without myosin:
books closed, O-P4 force verdict by the pre-registered method, and the
measured ranges recorded in PARALLEL_BUNDLE_LAW.md for the R10 myosin
design (duty cycle vs the R8-certified polarity memory: ~54° RMS/dump,
half-lives 212/284 steps).

## Builder registrations (R9-a, 2026-09-03, before build)

### 1. Seeded parallel cluster geometry (PCLU toggle; deterministic, ZERO new RNG draws)
- `PCLU=0` (default): parent trimer `INIT_DYN` path, bit-identical to R8 parent.
- `PCLU=1`: `INIT_CLU()` re-seeds after `INIT_DYN` (R8-c PCERT overwrite
  pattern; hash RNG is stateless, so the pre-draws consume nothing).
- Cluster: `NFCLU=5` filaments x `LCLU=8` monomers, filament slots 1-5,
  monomer slots 1-40. Axes along +x (pointed -> barbed). Pointed-monomer
  centers at x=2.25 so the pointed tail beads sit exactly on the substrate
  plane x=XADH=2.0 (brush anchoring geometry); barbed-end head beads distal
  at x=6.70, pointing at the piston. Lateral layout: cross pattern
  (y,z) = (6,6), (4.5,6), (7.5,6), (6,4.5), (6,7.5); nearest-neighbor
  spacing 1.5 = DX0 (crosslinks form at zero initial stretch; spacing >
  WCUT, < RXLK=2.0 capture).
- Pointed-end anchoring as in the brush: FILANCH(f)=pointed monomer,
  HASA on both beads, KSEED nucleator-spring anchor targets = seeded
  positions (ANCHORS machinery, unchanged).
- Remaining monomers 41..400: free gas, rejection-sampled by the SAME
  INIT_DYN hash stream (RCNT from 1000, RAND(SN+RCNT), SN=HASH(SEED)) -
  existing slots only, zero new draws; exclusion scan covers cluster beads.
- Rationale: 5x8 gives a PBUND-eligible (FILLEN>=4) parallel core with
  interior monomers from t=0, 360 free monomers for polymerization/turnover,
  and a census small enough for exact bookkeeping.

### 2. FORMIN scoping (no code change)
- The certified R2 FORMIN channel (per-filament processive tether,
  grasp ring PX(barb head) > XP - RGRIP, standoff XP - S0F) is applied
  unchanged. Scoping to the cluster is SPATIAL: the ring criterion selects
  distal barbed ends near the membrane; cluster tips seed at x=6.70 >
  XP0-RGRIP=6.5, so all five cluster tips are gripped from t=0 under
  FORMIN=1. Any brush-nucleated filament reaching the ring is gripped too
  (parent semantics, registered). FORMIN=0 path untouched =>
  FORMIN-off byte-identity to parent on the same census holds by
  construction (additive guards only).

### 3. Tip adhesion (PTIPA toggle; R6 slip-bond channel, distal tip zone)
- Second instance of the certified R6 adhesion channel, verbatim law
  (slip-law carryover, no law grids): 3D harmonic spring F=2*KADH*(A-R),
  E=KADH*d^2, slip rupture P=KOFFA*DT*EXP(|F|/FBA), hard release d>SMAXA,
  one bond per filament, bond tracks the MONOMER (shaft-grip convention).
- Placement: DISTAL TIP ZONE. Eligible element = barbed-end head bead
  B=2*FILBARB(F)-1 with PX(B) >= XTIP - RADH; fixed lab-frame target
  A=(XTIP, y_attach, z_attach) (R6 fixed-target convention).
- `XTIP=9.0` = XP0, the initial membrane (piston rest) plane: the tip
  adhesion models the tip complex gripping the cortical membrane plane the
  bundle pushes against. Along-shaft adhesion remains available via the
  existing PADH channel (pointed-tail capture at XADH), unchanged.
- RNG: NEW REGISTERED SLOT BLOCK 6900-6963: attach 6900+2*(F-1), rupture
  6901+2*(F-1), F=1..MAXF=32. Disjoint from every certified slot (max
  existing 6873, R7 crosslink block). Zero draws when PTIPA=0 (routine
  never called).
- Cause wiring mirrors R6: cause 3 at both barbed/pointed unbind sites
  (TADHM(F)=M), cause 4 in DISSOLVE; records `tipa`/`tipr` (below).
- Composition note (registered): the R7 candidate scan excludes the
  PADH-adhered monomer via an inline parent expression that may not be
  edited under the additive-amendment rule; the tip-adhered monomer
  therefore REMAINS crosslink-eligible. Both are certified force paths and
  superpose exactly; force closure is verified per-path by FD and globally
  by the books battery.

### 4. Tip instrumentation (PTIP toggle; records-only, zero RNG)
- New windowed record at NDIAG cadence (after `xlks`, before `gm`):
  `tip STEP ntip xtip npoly trx try trz fmag`
  - ntip = active seeded-cluster filaments (slots 1..NFCLU; slot-membership
    definition, registered);
  - xtip = mean x of their barbed head beads (tip position, %.6f);
  - npoly = sum of FILLEN over cluster slots (bundle polymerized mass);
  - trx/try/trz = mean substrate traction at tip adhesion bonds over the
    window (sum of -F over bonds and steps / NDIAG; exact bookkeeping, the
    adhs convention; accumulated inside TIP_FORCE, zero when PTIPA=0);
  - fmag = mean |F| per attached bond-step (adhs AFABS convention).
- Records-only: computed from existing state in the DIAG block; no RNG, no
  force, no feedback into dynamics. PTIP=0 (default) emits nothing.
  Inertness by stripped-log byte-identity at R9-c.

### 5. Tip adhesion event records (strict WRITE arity, R6 mirror)
- `tipa STEP F M B ax ay az` (attach; mirrors `adha` arity 7).
- `tipr STEP F M lifetime fx fy fz cause` (rupture; mirrors `adhr` arity 8;
  cause: 1=slip, 2=hard stretch, 3=monomer unbind, 4=filament death).

### 6. MIRROR static-cert construction (PCLU=1 requires PXL=1, PBUND>0)
- INIT_CERT gains an additive constructed cluster (guard `PCLU=1 .AND.
  PXL=1 .AND. PBUND>0`, so parent R7/R8 constructed chains always present,
  no monomer-index gaps): filaments 9 (monomers 40-43, y=6), 10 (44-47,
  y=8) along +x, 11 (48-51, y=10) along -x, all z=2.5, pointed centers
  x=8.0 (9,10) / 9.8 (11), rest geometry, >WCUT from every parent bead and
  all walls. Constructed crosslink slot 2 between monomers 41 and 45
  (d=2.0 pure-y, d-DX0=+0.5); constructed tip bond on filament 9 barbed
  monomer 43 (bead 85 at x=10.05, target XTIP=9.0, pure-x d=-1.05).
- New cert lines: `TIPC` (mirrors ADHC), `CERT_TIP etip %.17e`, and
  `CERT_FPOL <case> M1 M2 ok acc cos` sign battery on the cluster:
  par (41,45) cos=+1, anti (45,49) cos=-1, endmon (40,45) ineligible.
- FD: central differences on single-bead +/-1e-6 displaced MIRROR variants
  (fdplus/fdminus pattern of R6/R7/R8): tip bond bead 85 x (etip),
  crosslink bead 81 y (exl), R6 adhesion constructed bond bead 96 x
  (eadh, PCLU=1 composed config; AMENDED 2026-09-03 per R9-a verifier flag
  — originally registered as parent bead 2 / PCLU=0; the executed check
  exercises the identical adhesion law path in the composed configuration,
  and the bead-2 bond is present and exact in the same dump).
  Gate: |analytic - FD| < 1e-8 per path.

### 7. Registered run configs (R9-a)
- O-P1: PCLU=0 PTIPA=0 PTIP=0 PBUND=0, PXL=1 PBR=0 FORMIN=0 PADH=0
  DIMERS=1 PSTN=1 F_EXT=1.0 SEED=77031 NSTEPS=50000 XLNF=0 ->
  byte-identity vs runs22/smokes/parent_50k.log.
- Cluster smoke: PCLU=1 PBUND=1 PTIPA=1 PTIP=1 FORMIN=1 PXL=1 PADH=0
  PBR=0 DIMERS=1 PSTN=1 F_EXT=1.0 SEED=77031 NSTEPS=50000 XLNF=0 PCAP=1.
  Constructed census at t=0: nfil=5, nbound=40, nfree=360, ndim=0
  (NM=400). PBR=0: branching is out of the minimal-bundle assay scope.
