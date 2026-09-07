# plan_crosslink.md — R7 filamin-like crosslinking and mechanical cohesion rung

Registered: 2026-09-02, before any R7 engine build or run. Methodology:
sequential lock-step; oracle and experiment designed together; gates before
smokes; smokes before ensembles; checkpoint to `/mnt`. Swarm delegation for
implementation, gates, and parallelizable runs remains authorized under the
R6 workflow amendment; stage ordering remains lock-step.

Amendment X-1 (2026-09-02, after R7-c smoke): **instrument clarification.**
The `geo` record is `geo STEP FILLEN(1)` — filament 1's monomer count, not
brush height. The engine-native brush-height instrument is the piston
position `XP` in the `xpt` record: in the free-piston configuration
(PREL=0) the piston equilibrates at brush contact, so stationary mean XP is
the brush height at force balance. O-X3's gate therefore reads: stationary
mean `XP_ON > XP_OFF` for both seeds, ratio ≤ 1.5 (sanity). R7-c evidence at
F_EXT=1 already shows the predicted sign (XP 10.97 ON vs 9.77 OFF).
Clarification only — no criterion, threshold, or mechanism changes.

Amendment X-2 (2026-09-02): **language correction.** Smoke and law-grid
arms run with the free equilibrating piston (`PREL=0`), as actually executed
in R6-d/R7-c; earlier "clamped piston" wording in plan_adhesion.md described
intent, not the executed configuration. Stationary ensembles are taken
post-burn-in after the piston equilibrates, so all R6 O-A2..O-A5 results
stand. Only the release grid (PREL=300k) uses a genuinely clamped-then-free
protocol.

Amendment X-3 (2026-09-02, after the R7-d law grid): **O-X3 degeneracy
guard.** The R7-d F_EXT=4 seed-84950 ON arm pinned the piston at the lower
clamp (XPLO=5.5), showing that at high load one or both cohesion arms can
saturate against the clamp, where an XP comparison carries no information.
O-X3 therefore runs paired arms at `F_EXT ∈ {2, 4}` × seeds {77031, 84950}.
Any seed×load comparison in which BOTH arms end pinned at a clamp is
recorded as saturated and excluded; the gate requires ≥1 non-degenerate
comparison per seed, every non-degenerate comparison satisfying
`XP_ON > XP_OFF` with ratio ≤ 1.5. The R7-c F_EXT=1 pair (10.97 vs 9.77)
stands as an additional non-degenerate data point.

Amendment X-4 (2026-09-02, after the O-X3 geometry/sign investigation;
user-approved): **O-X3 re-registration — contractile cohesion.**
The investigation (`runs21/cohesion/OX3_INVESTIGATION.md`) established that
transient slip-bond crosslinks on freely-jointed chains form a **contractile
internal-tension network**: links are born compressed
(⟨d_birth⟩≈1.23–1.30 < DX0=1.5 by min-distance candidate selection), live
stretched (⟨d_live⟩≈1.85–1.87 > DX0), and rupture overstretched (d≈2.45);
with no bending rigidity, links act only in tension and pull the brush's top
layer down (73–76% of upper endpoints; ≈10–20% of F_EXT tether load on the
engaged zone), and causally inhibit filament growth (Δlen +0.02..+0.06 →
−0.05..−0.10 around attach, paired p ≤ 1.7e-7). The original O-X3 premise
("cohesion ⇒ taller brush") and its XP instrument (clamp-censored at
XPLO/XPHI; the R7-c F_EXT=1 comparison reverses under stationary means,
10.753 ON vs 10.866 OFF) were the defects — not the engine. O-X3 is
therefore re-registered as follows:

- **Instrument:** censor-free **x95 reach** — the 95th percentile of monomer
  x-coordinates per `gm` dump, stationary window (steps > 500k) — computed
  from existing logs. Piston XP is retired as the cohesion instrument.
- **Registered expectation (sign flipped):** the crosslinked brush is
  SHORTER at force balance. Gate: `x95_ON < x95_OFF` for both seeds
  {77031, 84950} at both F_EXT ∈ {2, 4}, each comparison with effect size
  ≥ 0.3 and significance ≥ 3σ after autocorrelation correction (effective
  sample size documented per arm).
- **Supporting diagnostic (cohesion as collective force transmission):**
  clamped-arm piston force (FRCT) spike incidence ON ≫ OFF; top-layer
  tether-load budget.
- The R7-c F_EXT=1 XP comparison is retracted as gate evidence.
- Neff ≥ 200/arm is the target for any future ±0.2-resolution claim;
  existing-log Neff is reported as-is.
- The `geo`=FILLEN(1) excursion in the F4 s84950 ON arm (filament-1
  monomer-pool concentration, 18–21%) is registered as an instrument
  artifact: no engine action.
- A "taller crosslinked brush" requires bending rigidity first (R8+
  bundle-polarity territory); out of R7 scope.

Amendment X-5 (2026-09-02, after the X-4 re-score failed; user-approved):
**O-X3 split into a mechanism certification (O-X3a) and a powered
macroscopic ensemble (O-X3b).** The X-4 re-score
(`runs21/cohesion/OX4_RESCORE.txt`) showed the x95 gate is underpowered at
two seeds (Neff 23–50/arm vs the 200 target) and the macroscopic effect is
load-dependent (null at F4 s77031), while the microscopic contractility
evidence is overwhelming. O-X3 therefore splits:

- **O-X3a — contractile-mechanism certification (gate, existing logs).**
  Computed per ON arm of the five cohesion/smoke pairs (F_EXT ∈ {1,2,4},
  seeds as available), from xlka/xlkr/gm/fil records:
  1. strain cycle: ⟨d_birth⟩ < DX0=1.5 AND ⟨d_live⟩ > DX0 AND
     median rupture extension d_rup > DX0 — all three inequalities in every
     evaluated arm;
  2. top-layer tension: fraction of live links pulling their upper endpoint
     downward > 65% per arm;
  3. causal growth inhibition: paired filament Δlen (5k steps post-attach
     minus 5k pre-attach) < 0 with paired p ≤ 0.01 in every arm.
  All three must hold in EVERY evaluated ON arm. The FRCT spike-incidence
  diagnostic from X-4 is retracted (incidence is symmetric; only clamp
  magnitude differs in 3/4 cells).
- **O-X3b — macroscopic seed ensemble (gate, new runs).** Seeds
  {77031, 84950, 6203, 34567, 92869, 55631} × F_EXT ∈ {2,4}, paired
  PXL=1/PXL=0, 1M steps, PREL=0, PBR=0, FORMIN=0, PADH=0, XLNF=0 (the four
  existing seed×load cells count; 16 new runs). Instrument: x95 reach over
  bound (filament) monomers, steps > 500k (X-4's all-vs-bound ambiguity is
  resolved to bound monomers, the physical brush). Gate per load:
  (i) ≥ 5/6 seeds with Δx95 = x95_ON − x95_OFF < 0;
  (ii) one-sample t over the six seed-Δ values: mean < 0 at p < 0.05;
  (iii) per-arm Neff and pooled effect reported as-is.
  The F_EXT=1 smoke pair remains context. Load-dependence (effect
  attenuation at F_EXT=4) is a registered possibility; if F_EXT=4 fails
  while F_EXT=2 passes cleanly, O-X3b may be re-scoped by amendment with
  the load-dependence documented as a finding.
- Both O-X3a and O-X3b must pass before R7-f and the docs/archive stage.
  No engine changes authorized by this amendment.

Amendment X-6 (2026-09-02, after the O-X3b 6-seed re-score; user-approved):
**O-X3b re-scoped to a powered pooled test at F_EXT=2; F_EXT=4 registered
as a load-attenuation finding.** The 6-seed re-score
(`runs21/cohesion/OX3B_RESCORE.txt`) showed the contractile shortening is
real but seed-heterogeneous at F_EXT=2 (4/6 seeds negative; pooled
one-sample t p=0.0449) and attenuated to null at F_EXT=4 (mean −0.127,
p=0.136) — expected, since the registered tether-load budget is only
≈10–20% of F_EXT, so external compression dominates at high load. The ≥5/6
per-seed sign-count criterion is retired: it is the wrong statistic for a
real-on-average but seed-heterogeneous effect. O-X3b is re-registered as:

- **Registered statistic:** one-sample one-sided t-test over the per-seed
  Δx95 values (bound monomers, steps > 500k, as before), mean < 0 at
  p < 0.05. No per-seed sign-count requirement; per-seed values and Neff
  reported as-is.
- **Ensemble:** the six existing F_EXT=2 seeds {77031, 84950, 6203, 34567,
  92869, 55631} plus four new F_EXT=2 seeds {44729, 73553, 91229, 28387}
  (paired PXL=1/PXL=0, 1M steps, same configuration as X-5) — 8 new runs,
  evaluated as a single 10-seed test.
- **F_EXT=4 load attenuation is a registered FINDING, not a gate cell:**
  contractile cohesion measurably shortens the brush at low-to-moderate
  load and attenuates toward null as external compression dominates
  (6-seed mean −0.127, p=0.136). Documented in CROSSLINK_LAW.md.
- O-X3b passes iff the 10-seed F_EXT=2 pooled test passes. O-X3a
  (mechanism certification, already PASS) is unaffected.

Parent oracle: `plan_adhesion.md` (R6, certified). Roadmap:
`NEXT_STAGES_PLAN.md` §R7 (oracle classes O-X1..O-X5 sketched there are
ratified here in full, plus O-X6 added by this registration).

## 1. Question

Can transient filamin-like crosslinks make the brush **mechanically cohesive**
— tougher under load — without freezing it into an irreversible aggregate?

R6 certified dynamic substrate adhesion in the unbranched brush and recorded
a known limitation: in the branched mesh, pointed tails are consumed at
branch junctions, so adhesion occupancy collapses (0.059 vs 0.19 baseline)
and traction becomes intermittent. Crosslinking is the mechanism that
stabilizes mesh-scale structure; it must be certified before bundle polarity
(R8), myosin (R10), and stress fibers (R11) can be interpreted mechanically.

## 2. Certified starting point

Parent engine: `brush_adh.ergo` (SHA256
`f709fb4453a1c6c6405ca33f9600844253ee7e35296acdb208f8d79bbf7075b8`, merge
commit `615c8ae`), certified under O-A1..O-A5.

Inherited certified properties:

- exact monomer conservation and clean ghost scans (O-A5);
- dynamic substrate adhesion with certified slip law β_A = 0.9955 ± 0.0014
  and exact traction bookkeeping (O-A3/O-A4);
- unbranched brush, branched brush, formin brush, and hybrid arms;
- hold-release piston protocol (PREL) and clamped-piston geometry;
- deterministic hash RNG `SN := HASH(SEED+STEP)` with collision-mapped slots
  (verified map: Langevin 1–2400, kinetics 3000–3127, hydrolysis 3200–3600,
  dimers 3700/3702/3710–4110, piston 4200, cap 4300+F, uncap 4400+F,
  branching 4500–4563, adhesion 4600–4663; **4700+ free**);
- WRITE-only instrumentation does not perturb trajectories;
- verified runner pattern `runs20/runner_r6.sh` (wipe-immune, /tmp stream →
  verify → cp → re-verify → retry → status file).

Engine internals relevant to R7 (surveyed 2026-09-02, read-only):

- monomer `m` ↦ head bead `2m-1` (barbed side), tail bead `2m` (pointed);
  `NB=800`, `NMAX=400`, `MAXF=32`;
- filament walk: `M := FILPNT(F)` then `M := NEXTM(M)`;
- inter-bead forces today: WCA excluded volume on all bead pairs within
  `WCUT=0.5612` via cell list; **no attractive inter-filament force exists**;
  the crosslink spring is the first;
- DIMKIN already performs an all-pairs free-monomer scan
  (O(NM²/2) ≈ 80k checks) every step, so an all-pairs bound-monomer
  candidate scan of the same order is affordable in the interpreter;
- main-loop order: INTEGRATE → BOND_AXES → KINETICS (ends with DIMKIN, then
  ADHKIN) → census → CELL_BUILD/NBR_BUILD → FORCE_PAIR → APPLY_BB →
  FILBONDS → ANCHORS → WALLS → ADHESION_FORCE → PISTON → diagnostics.

R7 begins with the **unbranched, no-formin arm** (`PBR=0`, `FORMIN=0`,
`DIMERS=1`) to isolate crosslinking. Adhesion is OFF (`PADH=0`) in all
certification arms; `PADH=1` appears only in the R7-f integration
diagnostics. Branched/hybrid integration are diagnostic follow-on arms, not
part of the first pass/fail gate.

## 3. Scope decision

The first crosslinker is deliberately minimal:

- filamin-like flexible stabilizer: one spring class, finite rest length;
- **inter-filament links only** — intra-filament links are excluded from R7
  scope (a later rung may register them);
- **at most one crosslink per filament pair** — keeps RNG slots, inventory,
  and rupture iteration trivially explicit;
- per-filament link cap `XLMAXF=2` and global pool `MAXXL=24` — bounded
  occupancy so freezing is detectable as saturation;
- slip-bond (Bell-law) rupture only; no catch bonds;
- no bundle-polarity selectivity (that is R8);
- no myosin, no membrane tube.

## 4. Geometry and mechanism

Engine candidate: **`brush_xlk.ergo = brush_adh + PXL channel`**.

### 4.1 Eligible elements and candidate scan

A crosslink connects the **head beads** `B1=2*M1-1`, `B2=2*M2-1` of two
bound monomers `M1`, `M2` on two different active filaments
`F1 = FID(M1) < F2 = FID(M2)`.

Eligibility, all required:

1. both monomers bound to active filaments (`FID > 0`, `FILACT = 1`);
2. `F1 ≠ F2` (inter-filament only);
3. neither monomer carries the substrate adhesion bond of its filament
   (`ADHM(F) = 0` or `M ≠ ADHM(F)`) — registered double-anchor precedence
   (plan_adhesion.md §8 mode 4): the adhesion bond keeps its monomer, the
   crosslinker must find another;
4. no existing crosslink on the filament pair `(F1, F2)`;
5. both filaments below the per-filament cap `XLMAXF`;
6. head-bead distance `d = |R(B2) − R(B1)| < RXLK`.

Candidate scan (in XLINKKIN, after rupture kinetics): all-pairs over bound
monomers, `M1 < M2` ascending; for each eligible open filament pair keep the
**minimum-distance** candidate (deterministic selection, no extra RNG).
Cost is O(NIN²/2), the same order as the certified DIMKIN scan.

### 4.2 Attachment

For each open eligible filament pair with a candidate, one draw per step:

```text
UAT := RAND(SN + 4700 + 2*(F1*(MAXF+2) + F2))
attach iff UAT < KONX * DT
```

On attachment the link takes the first free pool slot `L ∈ 1..MAXXL` and
records `F1, M1, F2, M2, born-step`. Attachment is instantaneous (no
conformational search); the rest length `DX0` is a property of the linker,
not of the attachment geometry.

### 4.3 Spring and rupture

Crosslink spring with finite rest length `DX0`:

```text
d   = |R(B2) − R(B1)|
E   = KXLK * (d − DX0)²
F on B1 = 2 * KXLK * (d − DX0) * (R(B2) − R(B1)) / d
F on B2 = −F on B1        (internal force, net zero on the system)
```

Sign convention: `d > DX0` attractive (pulls beads together), `d < DX0`
repulsive. `DX0 = 1.5 > WCUT = 0.5612`, so the crosslink rest geometry never
fights WCA sterics.

Rupture kinetics (XLINKKIN, per existing link per step, evaluated with the
**stored previous-step force** — same convention as ADHKIN, since kinetics
run before force assembly):

```text
slip:        URP := RAND(SN + 4701 + 2*(F1*(MAXF+2) + F2))
             rupture iff URP < KOFFX * DT * EXP(|F_stored| / FBX)
hard release: d > SMAXX  (current positions)
```

Non-slippage removal paths, wired wherever the parent clears monomer or
filament state (both unbind sites and DISSOLVE, mirroring the R6 causes 3/4
wiring):

```text
cause 3: an endpoint monomer unbinds from its filament
cause 4: an endpoint filament dies
```

A link ruptured by any path receives no force on the rupture step; its
last applied force is reported in the `xlkr` record (the R6 convention).

### 4.4 Registered parameters

| parameter | value | meaning |
|---|---|---|
| PXL | 0/1 | crosslink channel; default 0 = bit-identical to `brush_adh` |
| RXLK | 2.0 | head-bead capture radius |
| KONX | 1.0 | attachment rate per eligible open pair |
| KOFFX | 0.05 | basal slip rupture rate |
| KXLK | 1.0 | crosslink spring stiffness (softer than adhesion KADH=2.0; filamin is flexible) |
| DX0 | 1.5 | crosslink rest length (> WCUT; never fights sterics) |
| FBX | 1.0 | Bell slip force scale |
| SMAXX | 3.0 | hard-release stretch |
| XLMAXF | 2 | per-filament link cap |
| MAXXL | 24 | global link pool size |
| XLNF | 0/1 | WRITE-only per-step crosslink-force record; default 0 inert |

XLNF is registered **at build time** (the R6 PADHF lesson: per-step force
records must exist before the law grid, not retrofitted after a cancelled
ensemble).

### 4.5 RNG slots

Verified free range: 4700+. R7 claims:

```text
attach:  4700 + 2*(F1*(MAXF+2) + F2)     span 4700–6872
rupture: 4701 + 2*(F1*(MAXF+2) + F2)     span 4701–6873
```

`F1 < F2`, so the pair index `F1*(MAXF+2)+F2 ≤ 31*34+32 = 1086`; the claimed
span 4700–6873 is disjoint from every parent slot (max parent slot 4663).
No draws occur when `PXL=0`. Init-only draws from `HASH(SEED)` (not
`HASH(SEED+STEP)`) cannot collide with per-step slots.

### 4.6 State and inventory

```text
STATIC INTEGER :: NXL                          ! live link count
STATIC INTEGER :: XLACT(MAXXL+2)               ! slot live flag
STATIC INTEGER :: XLF1(MAXXL+2), XLM1(MAXXL+2) ! endpoint 1
STATIC INTEGER :: XLF2(MAXXL+2), XLM2(MAXXL+2) ! endpoint 2
STATIC INTEGER :: XLBORN(MAXXL+2)
STATIC INTEGER :: XLNUM(MAXF+2)                ! per-filament link count (cap XLMAXF)
STATIC REAL    :: XLFX(MAXXL+2), XLFY(MAXXL+2), XLFZ(MAXXL+2)  ! stored force
```

Inventory invariants (checked by the analyzer every window): `NXL` equals
the number of live `XLACT` slots; every live slot has both endpoints bound
to the recorded filaments; `XLNUM(F)` equals the number of live links
touching `F` and never exceeds `XLMAXF`; event reconstruction
(`xlka` minus `xlkr` by cause) equals the live count, with final-open links
matching the last `xlks` record (the R6 final-open convention).

## 5. Instrumentation

### Event records

```text
xlka STEP L F1 M1 F2 M2 d
xlkr STEP L F1 M1 F2 M2 lifetime fx fy fz cause
```

`cause`: 1 = slip, 2 = hard stretch, 3 = monomer unbind, 4 = filament death.

### Windowed records (NDIAG = 500)

```text
xlks STEP nxl meanf meand netfx netfy netfz attach_rate rupture_rate
```

`netf*` is the sum of crosslink forces applied in the window — an internal
force, so this is a **zero-bookkeeping** instrument: |netf| must vanish to
rounding. Accumulators are zeroed after each emit (the adhs pattern).

### Per-step force records (XLNF = 1, MIRROR = 0 only)

```text
xlkf STEP L F1 F2 fx fy fz
```

Written immediately after the spring force is computed for a live link;
WRITE-only; the R6 PADHF pattern. This record is what makes O-X6 an exact
per-step exposure fit rather than a rupture-step proxy.

### Static certification (MIRROR = 1)

`INIT_CERT` is extended (the R6 adhesion-bond precedent): a second short
filament is constructed with a static crosslink of known, pure-x stretch
`d ≠ DX0`. Required outcomes:

- `PXL=0` MIRROR dump byte-identical to the `brush_adh` MIRROR dump;
- `PXL=1`: `CERT_XL` energy equals `KXLK*(d−DX0)²` bitwise; differential
  `FRC` on the two linked beads equals `±2*KXLK*(d−DX0)*û` bitwise; all
  other forces/energies unchanged;
- central finite-difference error of the crosslink force vs energy
  `< 1e-8`;
- slot scan confirms 4700–6873 collision-free and `PXL=0` performs no
  crosslink draws.

## 6. Registered oracles

### O-X1 — engine gates

`PXL=0` ≡ `brush_adh` byte-identical over 300k steps, both gate arms
(`PBR=0,FORMIN=0` and `PBR=1,FORMIN=1`), 600/600 clean censuses, NUL-free,
FINAL present. No ensemble before both arms pass on the final merged source.

### O-X2 — dynamic equilibrium

Stationary (post-burn-in) crosslink population is alive and balanced:

- mean occupancy `nxl/nfil ∈ [0.1, 1.5]` (bounded away from zero and from
  the `XLMAXF=2` cap);
- attach/rupture balance `|attach − rupture| / mean < 5%`;
- ≥ 20 stationary attachments and ≥ 20 ruptures per run;
- occupancy stationary: first-half vs second-half post-burn means within
  50% (no monotone drift to saturation or extinction).

### O-X3 — cohesion

Paired design, same seeds, clamped piston, `F_EXT=4`, `DIMERS=1`, `PBR=0`,
`FORMIN=0`, `PADH=0`, arms `PXL=0` vs `PXL=1`:

- **gate:** stationary mean brush height (from `geo` records) satisfies
  `H_ON > H_OFF` for both seeds {77031, 84950}, and `H_ON/H_OFF ≤ 1.5`
  (stiffening, not a rigidity artifact);
- diagnostic: hold-release (`PREL=300k`) arm at `F_EXT=4` — the ON piston
  excursion is smaller than the OFF excursion (R6-e geometry).

If the sign is wrong (crosslinked brush shorter), stop and register a
geometry/sign investigation before any amendment.

### O-X4 — no collapse

Crosslinking must not freeze the mesh:

- stationary monomer release rate (`rel` events) ≥ 50% of the paired
  `PXL=0` arm;
- median per-monomer per-window displacement (from `gm` dumps) ≥ 0.25 × the
  `PXL=0` arm (no dynamical freeze);
- `nxl` never pinned at the effective cap (`min(MAXXL, XLMAXF·nfil/2)`) for
  more than 5 consecutive windows;
- census conservation exact throughout.

### O-X5 — stability and inventory

- monomer conservation `nbound + nfree + 2*ndim = 400` exact; ghost scan 0;
- crosslink inventory exact per §4.6 across every window of every run;
- zero-bookkeeping: |netfx|, |netfy|, |netfz| of every `xlks` window ≤
  5e-7·(1 + nrec/500) (the %.6f rounding bound, adhs-closure analogue);
- no SIGSEGV, hang, NUL corruption, or missing FINAL over 1M steps.

### O-X6 — slip-bond law

Registered at the same standing as O-A3. From `XLNF=1` law-grid logs:

- per-step exposure ML fit of `μ = KOFFX·DT·exp(β_X·|F|)` with offset
  `log(KOFFX·DT)` fixed; every live-link step contributes one exposure at
  its instantaneous |F|; cause-1 `xlkr` steps are terminal exposures;
  causes 2/3/4 and final-open links are right-censored at their last prior
  `xlkf`;
- registered window **β_X ∈ [0.5, 2.0]** (nominal FBX = 1.0);
- force-decile calibration (observed vs expected event rate) reported;
- per-F_EXT arm homogeneity reported.

## 7. Stage plan

New run directory: `phi4/runs21/`. Runner: copy of the verified
`runner_r6.sh` pattern. Analyzers: `stage_h_analysis.py` (smoke/pair) and
`stage_h_law_analysis.py` (law grid), adapted from the certified `stage_g_*`
analyzers and re-validated on synthetic cases before first use.

### Stage R7-a — build, static certification, review, merge

1. Branch `r7-xlk-impl` from the certified master in the coordination repo.
2. Implement the PXL channel per §4–§5, including XLNF and MIRROR cert.
3. Compile with the certified toolchain; MIRROR static cert per §5; FD
   validation; RNG slot scan.
4. Independent reviewer subagent; verifier subagent; merge only on PASS.

### Stage R7-b — O-X1 gates

Both arms, 300k, byte-identical vs `brush_adh` at matched parameters, on the
final merged source. Delegated; results verified before any smoke.

### Stage R7-c — brush smoke

```text
PXL=1, PBR=0, FORMIN=0, DIMERS=1, PSTN=1, PADH=0
F_EXT=1, seed=77031, 1M steps, clamped piston
```

Pass: crosslinks form and rupture continuously; O-X2 occupancy window;
O-X4 no-collapse checks vs the paired OFF arm; O-X5 structural/inventory
clean. There is no single-filament unit smoke (crosslinks are inter-filament
by definition); the two-filament unit case is covered exactly by the MIRROR
cert.

### Stage R7-d — law grid

Clamped piston, unbranched arm, `XLNF=1`:

```text
F_EXT ∈ {0,1,4} × seeds {77031,84950}
```

Decides O-X2, O-X5, O-X6. Measurements: occupancy/turnover, attachment
waiting time, rupture hazard vs force, force spectrum, link-pair map,
filament population relative to PXL=0.

### Stage R7-e — cohesion arms

Only after the law grid passes:

```text
paired PXL=0 / PXL=1, seeds {77031,84950}, F_EXT=4, clamped   (O-X3 gate)
paired PXL=0 / PXL=1, seed 77031, F_EXT=4, PREL=300k release  (diagnostic)
```

Decides O-X3 and O-X4.

### Stage R7-f — integration diagnostics

One-seed smokes, after the base mechanism passes:

1. `PBR=1, FORMIN=0, PADH=1, PXL=1` — branched mesh + adhesion + crosslinks;
2. `PBR=1, FORMIN=1, PADH=1, PXL=1` — hybrid + adhesion + crosslinks.

Primary diagnostic (the R6-f handoff question): does crosslinking stabilize
branched-mesh adhesion — occupancy and sustained-traction recovery relative
to the R6-f baselines (occupancy 0.0590/0.0627, traction 92.7%/96.1%)?
These are not oracle arms unless promoted by a later amendment.

## 8. Anticipated failure modes and registered responses

1. **Aggregate freeze**
   - Cause: KONX too high, KOFFX too low, caps too loose.
   - Response: register a rate amendment (halve KONX or XLMAXF→1); do not
     proceed to R8 on a frozen mesh.
2. **Zero or near-zero occupancy**
   - Cause: bound-monomer head beads rarely within RXLK=2.0.
   - Response: measure eligibility flux first; then register a narrow
     RXLK amendment. Do not silently widen the geometry.
3. **WCA/steric fighting**
   - Cause: rest geometry inside the repulsive core.
   - Response: DX0 = 1.5 > WCUT by registration; if oscillation is observed
     anyway, register a DX0 amendment with the displacement evidence.
4. **Adhesion–crosslink double occupancy**
   - Cause: same monomer claimed by both bonds.
   - Response: registered precedence — the adhesion-carrying monomer is
     ineligible for crosslinking (§4.1 rule 3). Any violation is a bug:
     fix and rerun O-X1/O-X5.
5. **RNG-slot collision**
   - Cause: claimed span overlaps a future or legacy channel.
   - Response: rebase before smoke; OFF-gate must remain exact.
6. **Inventory leak on endpoint death/unbind**
   - Cause: link not cleared at dissolution or pointed unbind.
   - Response: fix and rerun O-X1/O-X5; affected ensemble logs are
     quarantined.
7. **Intra-filament links**
   - Out of R7 scope by registration; if observed, it is a bug in the
     F1 ≠ F2 guard, not a feature.

## 9. Deliverables

- `brush_xlk.ergo`
- gate logs and 0-diff certificates
- `runs21/` ensemble using the verified runner pattern
- `stage_h_analysis.py`, `stage_h_law_analysis.py` and analysis outputs
- `CROSSLINK_LAW.md`
- `ANALYTICS.md` update
- verified R7 checkpoint archive

## 10. Exit criterion for R7

R7 passes when a dynamic filamin-like crosslink channel is gate-clean,
forms and ruptures continuously with a certified slip law, produces
measurable cohesion without freezing the mesh, and preserves every monomer,
filament, adhesion, and crosslink inventory oracle in the unbranched brush.
Only then does the project proceed to R8 bundle polarity.
