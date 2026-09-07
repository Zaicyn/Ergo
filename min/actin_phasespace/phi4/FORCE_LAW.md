# FORCE RUNG F1 — bare ratchet vs membrane load: certification

Parent: pop_fpt.ergo (DIMERS=0 single filament ≡ runs7). Engine: piston_fpt.ergo.
Pre-registered oracle (zero free params, plan_force.md):
  v(F) = PITCH·(j_on·e^{−Fδ/kT} − j_off), j_on=5.58e-4, j_off=3.59e-4,
  δ=PITCH=0.6, kT=0.4 ⇒ F_stall = ln(j_on/j_off)/1.5 = **0.294**, v0=1.19e-4 σ/step.

## Finding A — teleport insertion is force-blind (runs10a, CERTIFIED negative)
96-run ensemble (6 arms × 16 seeds, 300k steps, no insertion gate):
j_on flat ~5.0–5.5e-4 across F_ext = 0 → 0.6; no stall; F_stall = ∞.
Binds under contact rise 0.3% → 6.4% with load: the register teleports mass
INTO the load zone without steric check; no work is done against the
membrane; the piston is just shoved.
**A register that places mass without checking sterics cannot couple to force.**

## F1 fix — SGATE (gap-limited insertion, Mogilner-Oster)
Barbed bind blocked when the new head lands inside the piston contact zone
(PX(HP) > XP − XPMAR); insertion fires only when a thermal fluctuation of
the tip opens the gap. No RNG draws added. NBLK counter on pstn line.
Gate G-F1 re-run on the SGATE build: **PSTN=0 ≡ runs7, 0 diffs.**
(Process note: a broad sed on `DIMERS = 1` corrupted kinetic guards and
produced a spurious gate fail; caught by head-of-log diff. Parameter sed
must target the exact PARAMETER line.)

## Finding B — SGATE ensemble (runs11): oracle FALSIFIED, mechanism identified
96/96 FINAL, 1M steps, stationary half >500k, XPLO=5.5 (protective).

Measured (stationary half, 16-seed means):

| F_ext | j_on (e-4) | j_off (e-4) | v_fil (e-4) | ⟨FRCT⟩ | blk/att | clamp occ |
|-------|-----------|-------------|-------------|--------|---------|-----------|
| 0.0   | 4.92±0.18 | 3.55±0.15   | +0.82±0.14  | 0.097  | 0.13    | 0.00 |
| 0.1   | 5.06±0.23 | 3.55±0.16   | +0.91±0.14  | 0.129  | 0.48    | 0.29 |
| 0.2   | 5.06±0.24 | 3.62±0.15   | +0.86±0.19  | 0.145  | 0.54    | 0.46 |
| 0.293 | 4.99±0.22 | 3.61±0.17   | +0.83±0.13  | 0.151  | 0.54    | 0.56 |
| 0.4   | 5.02±0.28 | 3.66±0.21   | +0.82±0.21  | 0.146  | 0.54    | 0.67 |
| 0.6   | 5.01±0.24 | 3.60±0.26   | +0.84±0.19  | 0.179  | 0.56    | 0.71 |

Oracle predicted j_on = 5.58→2.27 e-4 and stall at 0.294. Observed: j_on
flat within ±2% everywhere; no stall at any load. **The exponential
force–velocity law does not emerge from SGATE alone.** Three causes,
all quantified:

1. **Candidate trapping (supply saturation).** KON·DT = 2.5 → saturated
   (every capture-zone candidate commits-or-blocks). On a block, the
   candidate has already been teleported to the register and is NOT
   reverted: it stays within RCAP of the tip and is retried every step.
   Attempt rate rises 5.7e-4 (bulk) → 1.1e-3/step (wall); blocking half
   the attempts exactly cancels the doubled supply. j_on is pinned by
   supply, not by force.
2. **Deterministic piston (no membrane fluctuations).** XP integrates
   FRCT−F_EXT with no thermal noise. Insertion into a fluctuation-opened
   gap is work-free; the Boltzmann factor e^{−Fδ/kT} never enters the
   commit probability. The gap statistics are set by tip dynamics, not by
   the load. The one floating, force-balanced arm (F=0.1: ⟨FRCT⟩=0.129≈F,
   xp=7.6 off-clamp) shows j_on *unsuppressed* (5.06 vs 4.92 e-4).
3. **Clamp load-bearing.** For F≥0.2 the piston parks on the XPLO clamp
   46–71% of stationary time; the clamp bears the load deficit
   (⟨FRCT⟩ ≈ 0.15–0.18 ≪ F), truncating the gap distribution and removing
   load dependence.

Side effect of (1): **membrane leakage** — blocked candidates are left
inside/beyond the plane; at F≥0.1 roughly half the free pool
(17–28 of ~35) sits beyond the membrane at the final frame. The plane is
a sieve for the bath (only the tip ever feels it).

v_xp ≈ 0 in all arms and is not a usable velocity observable: the chain
is freely hinged (F0), the tip axis decorrelates in <500 steps, and the
barbed net current is absorbed by conformation + pointed-end loss rather
than translated into +x piston drift.

## Verdict
F1 oracle falsified twice, both times informatively:
- v1: no steric gate ⇒ no coupling (F_stall = ∞).
- v2 (SGATE): steric gate necessary but NOT sufficient — without
  revert-on-block and a thermally fluctuating membrane, the commit
  probability carries no work factor.

## F1b repair (pre-registered before building)
Minimal honest assay, piston2_fpt.ergo:
1. **Revert-on-block**: blocked candidate restored to its pre-teleport
   coordinates (no RNG, no trapping, no leakage).
2. **Thermal piston**: XP += PMU·(FRCT−F_EXT)·DT + √(12·D_p·DT)·(U−1/2),
   D_p = kT·PMU = 0.2 (fluctuation–dissipation), U = RAND(SN+800) — new
   slot, drawn only when PSTN=1, so G-F1 (PSTN=0 ≡ runs7) is untouched.
3. XPLO=5.5 protective only.
Oracle (unchanged physics, zero free params):
  j_on(F)/j_on(0) = e^{−F·δ_eff/kT}, δ_eff = PITCH = 0.6 pre-registered;
  F_stall = 0.294. Auxiliary acceptance criteria: clamp occupancy <5% in
  operating arms; leakage ≈ 0; ⟨FRCT⟩ ≈ F_ext in stationary half.
Falsification: flat j_on(F) again, or exponent δ_eff far from 0.6.

## F1b ensemble (runs12): oracle falsified a third time — root cause found
96/96 FINAL, 1M steps, revert-on-block + thermal piston (DP=kT·PMU, slot 800).
Gate G-F1b: PSTN=0 ≡ runs7, 0 diffs.

Repair audit: clamp occupancy FIXED (0.2%→5.2% across arms, was 29–71%);
leakage down (13/34 vs 28/37 in smoke, residual = natural bath diffusion —
accepted abstraction, plane touches only tip beads); block fraction now
honest (65%→82% of attempts). Force balance ⟨FRCT⟩≈0.10 at F=0.1 ✓.

But j_on STILL flat: 4.97 → 4.86 e-4 across F = 0→0.6 (oracle: 5.58→2.27).
Event-resolved diagnostics locate the root cause:

1. **Engagement (contact dwell) is ~1%** (TFHIST: bin-0 dwell 7.9M/8M).
   Contact is abrupt (bins 0.1–0.9 empty; force jumps straight to ≥0.9
   with KPST=100). Arm-averaged suppression is bounded by engagement.
2. **Gap-resolved commit spectrum is anti-ratchet**: small-gap commit
   rate RISES with F (0–0.1σ bin: 2.3e-6 → 6.8e-6, 3×) while large-gap
   commits fall (2.8e-4 → 1.8e-4). The membrane is pressed closer, so
   commits RECORD smaller gaps — but the total rate is conserved.
3. **Root cause: supply-limited insertion + retry-until-success.**
   KON·DT=2.5 saturated: every captured candidate commits at the FIRST
   clear-register instant; a blocked candidate stays in the capture zone
   and retries every step. The commit rate = candidate supply rate, and
   the gate only redistributes WHERE commits happen. A steric gate cannot
   throttle a retrying candidate below supply. Physically: a real monomer
   that clashes with the membrane bounces back to the bulk; the next
   attempt is a FRESH arrival (memoryless Poisson). Our engine keeps the
   same monomer on the shelf until it succeeds.

## F1c repair (pre-registered before building)
piston3_fpt.ergo = piston2 + **ejection cooldown**:
- COOL(M) flag: set on block; cooled monomers are skipped by the capture
  scan; flag clears when M is found outside RCAP of the tip (pure logic,
  no RNG ⇒ PSTN=0 stays bit-identical to runs7). Single-filament scope
  (force rung is DIMERS=0; population×force integration revisits).
- bbind extended with register-gap field RGAP=(XP−XPMAR)−PX(HP); new bblk
  line logs blocked attempts' RGAP (additive ⇒ gate-filtered).
Oracle (physics unchanged):
  (i)  j_on(0) returns to the runs7 bulk rate 5.58±0.3 e-4 (the F=0 plane
       no longer throttles via retries);
  (ii) attempt-gap distribution exponential with scale set by kT/F;
  (iii) j_on(F)/j_on(0) = exp(−F·δ_eff/kT), δ_eff = PITCH·D_p/(D_p+D_tip)
        ≤ 0.6 registered as a window [0.15, 0.6]; report fitted δ_eff;
  (iv) stall exists and is finite.
Falsification: j_on(F) flat AGAIN after ejection ⇒ supply-limit diagnosis
wrong at a deeper level; or non-exponential form.

## F1c ensemble (runs13): ejection works; the geometry verdict
24 runs (3 arms {0.0, 0.293, 0.6} × 8 seeds, 1M steps), 24/24 FINAL.
- blk/att now honest: 5.6% (F=0) → 10.4% (0.293) → 10.1% (0.6). Genuine
  fresh-capture clashes; load doubles them (membrane pressed in) —
  directionally correct mechanics.
- j_on(0) = 4.97±0.29 e-4 vs registered 5.58±0.3: near-bulk (residual −11%
  = 5.6% blocked attempts + cooled candidates' supply lag). Retry pathology
  cured (was: blocks ≈ commits × 5).
- Attempt-gap stream is complete (KON saturated ⇒ every capture reaches the
  SGATE decision): P(g≤0) 5.6%→10.4%; distribution broad, not a pressed
  exponential — the piston is diffusion-dominated (per-step Péclet ~0.016)
  and ~90% of attempts happen with the plane >1σ away.
- Arm-level j_on flat (4.97/4.87/4.99): suppression bounded by the ~10%
  engaged fraction. No finite stall measurable in this geometry.

**F1 (bare ratchet) rung conclusion.** Microphysics certified correct
(SGATE + revert + ejection + thermal piston; G-F1a/b/c all 0-diffs vs runs7).
The bare freely-hinged filament vs free membrane does NOT and cannot show a
macroscopic force-velocity law: the tip engages the plane only ~10% of
attempts. The Brownian-ratchet exponential is a property of the ENGAGED
ensemble. Force-clamp on a remote plane is the wrong assay — the tip must
be HELD at the membrane. That is precisely the formin's job (F2).

## Stage F2 — formin gate (pre-registered oracle, built after this line)
formin_fpt.ergo = piston3 + FORMIN element (PSTN=1, FORMIN=1):
- 3D harmonic tether: filament-1 barbed-tip head bead to anchor point
  A = (XP − S0, YA, ZA), YA/ZA = nucleator yz — holds the tip at standoff
  S0 = 0.4σ from the plane AND coaxial (base anchored at same yz ⇒ a_x≈1,
  full PITCH projection). KF = 10 (σ_gap = sqrt(kT/KF) = 0.2σ).
  Reaction x-component on piston (load path); slip cap |F_t| ≤ 5.0
  (processivity limit). No RNG draws. Tether tracks FILBARB(1) ⇒
  processive by construction. yz components = membrane tension (ignored).
- SGATE unchanged: register must clear XP − XPMAR. At rest the tip sits
  at gap S0 = 0.4 < PITCH = 0.6 ⇒ register overshoots by 0.2σ ⇒ insertions
  need thermal gap-opening against spring + load ⇒ work enters the commit
  probability by construction of the geometry, not by a dialed rate.
- Gap statistics: Gaussian(S0 − F/KF, sqrt(kT/KF)) ⇒ commit fraction
  ~erfc — exponential-in-F mid-range; measured δ_eff is emergent.
Oracle (zero free params beyond geometry):
 1. Engagement ~100%: tip within tethering range of XP−S0 all stationary
    steps (σ_t = 0.2σ).
 2. Alignment: barbed axis x-projection ≈ 1 (coaxial tether).
 3. j_on(F) = j_on(0)·exp(−F·δ_eff/kT), δ_eff ∈ [0.1, 0.6] registered
    window (geometry estimate: clearance deficit 0.2σ up to full PITCH).
 4. Finite stall: F_s = 0.294·(0.6/δ_eff) ∈ [0.29, 1.76].
 5. Tension arm F=−0.2: j_on capped at bulk supply (no super-bulk
    acceleration — supply-limited ceiling; mDia1 tension window is gated
    chemistry we have not built).
 6. v_xp now measurable: coaxial tethered growth pushes the piston;
    v_xp ≈ v_fil = PITCH·(j_on − j_off) cross-check.
 7. Force balance: ⟨FRCT + tether x-reaction⟩ = F_ext in stationary half.
Arms: F_ext ∈ {−0.2, 0.0, 0.1, 0.2, 0.293, 0.4, 0.6, 1.0} × 8 seeds, 1M steps.
Gates: G-F2a PSTN=1,FORMIN=0 ≡ piston3 runs13 (bit-identical, same config);
       G-F2b PSTN=0 ≡ runs7.
Falsification: no finite stall with full engagement ⇒ the gap-work picture
itself is wrong in this engine; δ_eff far outside window ⇒ geometry wrong.

### F2 amendment (still pre-build): standoff arithmetic
Corrected after working the gate geometry. Steric boundary for insertion is
the contact cushion at XP − XPMAR (bead-radius 0.5): the register
(tip + PITCH·a_x, a_x ≈ 1 coaxial) must clear it ⇒ zero-force clearance
requires tether rest S0 ≥ XPMAR + PITCH = 1.1σ. S0 = 0.4 (first sketch)
would block ~all commits even at F=0 — wrong.
Final: **S0 = 1.25, KF = 10** (σ_x = sqrt(kT/2KF) = 0.141σ), FMAXT = 5.0.
Registered prediction (no free params): Gaussian-tail law
  j_on(F)/j_on(0) = Φ((μ0 + F/2KF)/σ_eff) / Φ(μ0/σ_eff),
  μ0 = S0 − XPMAR − PITCH = 0.15σ (clearance margin),
  σ_eff ∈ [0.141 (tether only), ~0.45 (tether + chain tip wander)].
  P(0) ≈ 0.86 (14% basal occlusion by the ring — physical).
  Mid-range log-slope δ_eff = kT·μ0/σ_eff² ∈ [0.15, 1.5]·0.6/kT-scaled —
  emergent, measured. Stall where j_on = j_off: estimate F_s ≈ 1.5–2.5
  (outside the bare-ratchet 0.294 — formin works against HIGHER load;
  that IS the biological point). Registered stall window widened to
  F_s ∈ [0.5, 4.0]; the form must be the Gaussian tail above, not flat.

### F2 amendment 2 (still pre-ensemble): spring stiffness sets the force scale
v3/v4 smokes exposed two mechanical flaws, fixed before the ensemble:
1. Two-sided x-tether: a lagging tip pulled the piston LEFT (tension side),
   accelerating the creep — positive-feedback crush spiral (lenfil→3).
   Fix (v4): x-tether one-sided (compression only); yz grip and threading
   remain two-sided. Bonus: F=0 arm now releases the piston to wander off
   and the filament grows free — j_on(0) = clean bulk baseline.
2. Force scale: margin compression = F/(2KF). KF=10 needs F≈3 to close the
   μ0=0.15σ margin — gate never bites (smoke: 179 commits at F=2.0 ≈ bulk).
   **KF=2.0** (2KF=4/σ): margin(F) = 0.15 − F/4, σ_spring = sqrt(kT/2KF)
   = 0.32σ. Predicted per-attempt commit probability (Gaussian tail,
   no free params): P(0)=0.68, P(0.3)=0.59, P(1.0)=0.38, P(2.0)=0.14;
   j_on = supply·P with supply = bulk 5.58e-4 ⇒ stall (j_on = j_off =
   3.59e-4) at **F_s ≈ 0.9** (registered window [0.5, 4.0] ✓);
   δ_eff = kT·μ0/(2KF·σ²)·... log-slope at 0 gives δ_eff ≈ 0.15
   (window [0.1, 0.6] ✓). Contact-borne regime (tip intrudes the cushion)
   only for F ≳ 3.
Ring geometry now: S0=1.25, KF=2.0, RGRIP=1.0 (yz-tracking grasp),
SMAXF=2.0 (slip release), KORI=1.0 (threading), FMAXT=5.0 (slip cap).
Law fit on engaged arms (grip>80%); F=0 arm = free-filament control.

### F2 amendment 3 (pre-ensemble): the formin changes the ratchet class
v4 smokes (gates G-F2a/G-F2b re-run, 0 diffs): engagement achieved
(grip 36-44% of windows at F=0.293-1.0, force balance ⟨FRCT⟩≈F when
gripped), filaments survive (lenfil 11-22), slip-grip works. But j_on
stays ≈ bulk at F=0.293/1.0/2.0 (166/156/179 commits per 300k) with
blocks ≈ 0 — the one-sided spring RETRACTS the tip after each insertion
(chain growth pushes the new tip into the spring; spring relaxes it back,
clearing the next register). The register therefore never sees the load:
**a processive spring-coupled cap converts the Brownian ratchet into a
power-stroke ratchet** — work F·δ is paid post-insertion by chain growth
(piston pushed out, force balance holds) instead of gating gap-opening.
Registered prediction for the ensemble:
  - Spring-borne regime (F < 2KF·(S0−XPMAR−PITCH-margin)... i.e. F ≲ 3):
    j_on(F) ≈ flat ≈ bulk × engagement; blocks rare; ⟨FRCT⟩ = F when
    gripped; v_xp tracks net barbed growth during gripped episodes.
  - Contact-borne crush regime (F ≳ 3-4): piston pressed onto the tip/wad,
    blocks rise, lenfil → floor, v → 0 (crush stall — set by spring/backbone
    transmission, NOT by kT/δ).
Falsifiable distinction: Brownian class = exponential j_on(F), stall 0.29;
power-stroke class = flat j_on(F) then mechanical crush at F ≳ 3.

## F2 ensemble (runs14): CERTIFIED — the formin cap is a power-stroke ratchet
48/48 FINAL (6 arms × 8 seeds, 1M steps, stationary half). Gates: G-F2a
FORMIN=0 ≡ piston3 (0 diffs, 1M steps), G-F2b PSTN=0 ≡ runs7 (0 diffs).

| F_ext | j_on (e-4) | j_off (e-4) | ⟨FRCT⟩ | grip | lenfil | blk (e-4) |
|-------|-----------|-------------|--------|------|--------|-----------|
| 0.0   | 4.79±0.18 | 3.77±0.17   | +0.12  | 0.29 | 26.5   | 0.11 |
| 0.293 | 4.81±0.29 | 3.55±0.19   | +0.13  | 0.38 | 24.6   | 0.08 |
| 0.6   | 4.69±0.25 | 3.59±0.20   | +0.16  | 0.38 | 21.8   | 0.12 |
| 1.0   | 5.00±0.16 | 3.74±0.28   | +0.15  | 0.32 | 21.9   | 0.13 |
| 2.0   | 4.85±0.16 | 3.62±0.29   | +0.19  | 0.36 | 21.2   | 0.16 |
| 4.0   | 4.82±0.18 | 3.69±0.19   | +0.21  | 0.35 | 22.2   | 0.17 |

Verdicts against the registered predictions:
- j_on(F) FLAT 0→4.0 (power-stroke class, amendment 3) ✓ — the registered
  Gaussian-tail suppression (amendment 2) is falsified; mechanism: the
  one-sided spring retracts the tip after each commit, clearing the next
  register; blocks stay ≈2% of attempts at all loads.
- Force balance when gripped ✓ (⟨FRCT⟩≈F during gripped windows; arm means
  diluted by grip duty cycle ≈ 0.35).
- Survival under load ✓ — lenfil 21-27 at all arms; no crush even at F=4
  (14× the bare-ratchet stall 0.294). Registered crush-onset at F≳3-4 is
  FALSIFIED: the one-sided grip lets the tip retract into the lee of the
  parked piston and keep growing; the box clamp (XPLO) caps how hard the
  membrane can bear down — the F≥1 arms are clamp-adjacent and their
  insertions are partially work-free (documented artifact).
- v_xp ≈ 0 all arms: piston quasi-static, worm absorbs growth — piston
  drift is not a usable velocity observable in this geometry (F0 freely-
  hinged finding holds).

## FORCE/MEMBRANE RUNG — final synthesis
Four architectures, four certified results, each mechanism identified:
1. F1a teleport insertion: force-blind (F_stall=∞). Steric gate necessary.
2. F1b SGATE alone: flat — candidate trapping + deterministic membrane +
   clamp load-bearing (all quantified).
3. F1c +revert+ejection+thermal piston: honest bare assay; microphysics
   correct (blocks scale with load 5.6%→10.4%); macroscopic law
   unmeasurable — engagement ~10% (freely-hinged tip rarely meets plane).
4. F2 formin processive cap: engagement via slip-grip; load transmitted;
   but spring retraction converts Brownian gating → power-stroke: the
   capped tip is UNSTALLABLE by membrane pressure (flat j_on to F=4).

The exponential Brownian force-velocity law (insertion thermally gated
against load) requires the gap to close at rate ∝F with NO spring
retraction and engagement ~1 — i.e. direct membrane-on-tip contact for a
statistically dominating fraction of time. A single freely-hinged worm in
a 12σ box cannot provide this; a BRUSH of short filaments against the
membrane can. → next rung: φ4 population × membrane (lamellipodium):
multi-filament load sharing, membrane resting on the brush, per-filament
SGATE. The formin's measured power-stroke character (flat j_on under
load, work paid per insertion post-hoc) is the baseline for lamellipodium
formin physics.
