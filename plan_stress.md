# R11 Oracle — Stress Fiber (stress_fiber.ergo)

Registered 2026-09-04 under the force-first doctrine. Roadmap source:
NEXT_STAGES_PLAN.md §R11. Parent: `runs24/myosin_unit.ergo` (sha256
2806ed054ecebf0fe9eb6db93af39d433991dfd97d36b534afdb22c4d923110f,
CERTIFIED R10; do-not-modify, anchored additive amendments only).
User priorities (binding): stress fibers + myosin FIRST; adhesion and
stress testing FIRST; filopodia/tip interactions LOW PRIORITY — the R9
PCLU/PTIPA/PTIP channels stay OFF in R11 (available but unused).

## Question

Can actin bundles, crosslinkers, adhesions, and myosin assemble into a
stable contractile stress fiber anchored to the substrate at both ends?

## Doctrine (binding)

- **Hard gates (failure = bug = STOP with evidence):** O-S1 byte-identity
  (each new channel OFF ≡ R10 parent); FD < 1e-8 on any new force path;
  sign correctness of motor stepping (contour invariant) and of
  antiparallel gating (zero tolerance); O-S7 books (all inventories incl.
  myosin conserved, ghost scan zero, max|netf|=0, no bookkeeping force
  discontinuity).
- **O-S3 contractility is the headline FORCE measurement:** both endpoint
  adhesion groups bear inward traction; fiber tension positive and
  stationary. Method pre-registered by the builder (traction = adhs-
  convention windowed substrate force per end; tension = cross-section
  force sum through the fiber midplane); numbers reported per seed.
- **Ranges (never gates):** O-S2 assembly time from the registered
  initial condition; O-S4 polarity organization (antiparallel enrichment
  around myosin; parallel regions identified); O-S5 homeostasis (length/
  tension boundedness under turnover — reported as distributions; no
  runaway is the force-domain check); O-S6 perturbation outcome
  (registered sever/stretch; outcome classified: repaired / failed-
  measurable, with the numbers).
- RNG: new slot blocks register above 7001 (current max: myosin
  6970–7001).

## Builder scope (register details BEFORE build, "Builder registrations")

1. **Live-kinetics footing (resolves the R10 registered limitation):**
   barbed-end anchor unbind-transfer machinery so tracks can turn over
   under load — the R10 anchors were frozen-kinetics-only. Register the
   transfer rule; FD/books must cover it.
2. **Constructed fiber geometry:** alternating-polarity actin segment
   (register filament count/length/spacing/polarity pattern), both ends
   anchored to substrate adhesion via the R6 channel (register the
   end-anchor geometry — pointed-end adhesion bonds per R6 law).
3. **Myosin ensemble:** PMYO=1 motors binding dynamically along
   antiparallel regions of the fiber (register attach candidacy scope;
   MAXMYO=8 pool exists — register pool size for R11).
4. **Crosslink stabilization:** PXL=1 with PBUND as registered (the R8
   gate; register which polarity mode the fiber uses and why).
5. **Instrumentation (records-only):** per-end traction records
   (adhs-convention), fiber tension (midplane force sum), fiber length,
   myosin distribution along the fiber, actin flow if measurable from
   existing records (do NOT build heavy new instrumentation — prefer
   derived analysis from gm/tip/adhs/myos records).
6. **Perturbation (O-S6):** one registered perturbation (sever at
   midplane OR step-stretch of one anchor), triggered at a registered
   step by a registered parameter, deterministic.

## Stages

- **R11-a:** build + static/FD + constructed sign/force cert + combined
  review/verify + merge.
- **R11-b:** O-S1 gates (channels OFF ≡ R10 parent; matrix PBUND∈{0,1,2}
  × seeds {77031,84950}, 300k; references = runs24/gates om1 logs).
- **R11-c:** fiber smoke + measurements: O-S3 traction/tension, O-S2
  assembly range, O-S4 polarity organization, O-S5 homeostasis, O-S6
  perturbation recovery, O-S7 books. Seeds {77031, 84950}, 1M steps,
  XLNF=0 discipline.
- **R11-doc:** STRESS_FIBER_LAW.md + ANALYTICS.md MAP 10.

## Registered failure responses

- Hard-gate failure: STOP, evidence, no tuning.
- Near-zero assembly (O-S2): measure nucleation/attach flux first;
  geometry amendments only, never physics parameters.
- Traction rupture-dominated at anchors: report distributions as-is
  (the R9 lesson — do not strengthen adhesion to hit a number).
- No zips; 1M logs ~56MB discipline; deletions only on user word.

## Exit criterion

A dynamic adhesion-anchored actin-myosin fiber maintains contractile
tension and transmits inward traction to BOTH substrate attachments —
with the force numbers recorded for the cell-scale stage.

---

## Builder registrations (R11-a, registered before engine build)

Parent: certified `runs24/myosin_unit.ergo` sha256
`2806ed054ecebf0fe9eb6db93af39d433991dfd97d36b534afdb22c4d923110f`.
All amendments anchored-additive; no parent line edited. New toggles
default-OFF (`PSF=0`, `PSEV=0`) ⇒ bit-identical to parent. New RNG
slot block **7010–7073** (SF adhesion attach `7010+2*(F-1)`, rupture
`7011+2*(F-1)`), disjoint from the registered max 7001. Engine:
`runs25/stress_fiber.ergo`.

**Reg. 1 — live-kinetics anchor footing (scope item 1).** The fiber-end
anchors ARE adhesion slip bonds; the R10 constructed-barbed-end KSEED
anchors (and their frozen-kinetics unbind-transfer gap) are replaced
wholesale: INIT_SF sets NO HASA anchors on fiber monomers, so there is
no constructed KSEED anchor whose transfer could be needed. Anchoring =
new SF adhesion channel: the certified R6 slip-bond law **verbatim**
(spring `F=2*KADH*(A-R)` to a fixed on-plane target, `E=KADH*d^2`,
slip `P=KOFFA*DT*EXP(AFD/FBA)` on the CURRENT distance (ADHKIN
convention), hard release `d>SMAXA`, one bond per filament tracking the
MONOMER (shaft grip), cause 3 wired at both monomer-unbind sites, cause
4 in DISSOLVE), with the same R6 parameter set (`KADH/KONA/KOFFA/FBA/
SMAXA/RADH` — no new physics parameters). Load-dependent unbind and
re-attachment are the certified R6 behavior; pointed-end turnover at the
fiber center is free. Rationale: oracle-preferred alternative ("adhesion
bonds ARE the anchors … preferred if cleaner").

**Reg. 2 — end geometry + traction sign analysis (grips barbed ends,
NOT pointed ends).** Certified R10 mechanics: the bipolar motor walks
barbed-ward on both tracks; between antiparallel filaments this slides
each filament **pointed-end-first toward the fiber center** (the motor
spring stretches and pulls each grip toward the other head), i.e.
contraction = barbed ends converge (R10-c isometric unit: inward anchor
traction). Therefore anchors at the **barbed** ends bear INWARD traction
and anchors at pointed ends would bear OUTWARD (extensile) traction —
a pointed-end-grip fiber cannot produce the O-S3 headline. Registered
end geometry (this is the "register the end geometry" delegation):
sarcomere-like — **barbed ends OUTWARD at the two substrate planes,
pointed ends inward**; SF bond grips the **barbed-end head bead**
`B=2*FILBARB(F)-1`, zone-scoped to both planes: attach-eligible when
unattached and `PX(B) <= XADH+RADH` (left plane, end group 0, target
`(XADH, PY(B), PZ(B))`) or `PX(B) >= XSF2-RADH` (right plane, end
group 1, target `(XSF2, PY(B), PZ(B))`). This is exactly the R6 law
with a registered grip element/scope, paralleling R9's PTIPA instance
(barbed-head grip at the tip zone). Inward-traction sign criterion
(adhs convention, traction = `-F` on substrate): left group healthy
contraction ⇒ `trx > 0`; right group ⇒ `trx < 0`.

**Reg. 3 — constructed fiber geometry (PSF channel).** Deterministic
INIT_SF (INIT_CLU/INIT_MYO overwrite pattern; gas monomers
`2*NHF*LSF+1..400` rejection-sampled from the SAME INIT_DYN hash stream
with `RCNT=1000` — ZERO new RNG draws). `NHF=3` filaments per half, 6
total (slots 1..6), `LSF=9` monomers each (monomers 1..54; contour 5.4
per filament). Ring cross-section radius `RSF=1.5` about
`(YSF,ZSF)=(6,6)`, halves alternating around the ring: left half slots
1..3 at (y,z) = (7.5,6), (5.25,7.2990381), (5.25,4.7009619); right
half slots 4..6 at (6.75,7.2990381), (4.5,6), (6.75,4.7009619). Every
adjacent ring pair is an antiparallel L–R pair at distance exactly
1.5 = DX0 = DMY0 (rest length for both crosslinks and motor springs);
same-half (parallel) pairs sit at 1.5*sqrt(3) ≈ 2.598 > RMYO/RXLK =
2.0 (geometrically excluded from motor/link candidacy). Left half: axis
−x (barbed end at the left plane): barbed monomer center 2.75 (head
bead 2.50, inside the left zone), pointed monomer center 7.55. Right
half: axis +x: pointed monomer center 3.45 (pointed tail bead 3.20 >
XADH+RADH=2.75 — NOT R6-eligible at t=0), barbed monomer center 8.25
(head bead 8.50, inside the right zone). Head-bead x-grids of the two
halves coincide (both on the 0.6 grid, same phase), so any same-x L–R
grip pair has `d=1.5` exactly. Overlap region x ∈ [3.45, 7.55] ≈ 4.1.
Right plane `XSF2=9.0` (new geometry parameter; PTIPA stays OFF).
Filament count/contour/polarity/spacing/end positions as above.

**Reg. 4 — myosin ensemble (scope item 3).** PMYO=1; attach candidacy =
the certified R10 MYOKIN all-pairs scan UNCHANGED (any two bound
monomers on two different active filaments, min-distance candidate,
RMYO=2.0 capture, MYPAIR one-motor-per-pair, occupancy exclusion). On
the constructed fiber the only geometrically eligible pairs are the 6
antiparallel L–R ring neighbors. Pool MAXMYO=8 default — bound check
registered: eligible constructed pairs = 6 ≤ 8, no raise. Pre-bound:
3 motors (slots 1–3) on pairs (1,4), (2,5), (3,6), gripping the k=5
monomers (head-bead x = 5.5 on both) at exact rest `d=1.5=DMY0`, with
step-0 `myoa` records so `cum(myoa)-cum(myor)=nmyo` is exact from t=0
(R10 reg. 5 addendum pattern). The other 3 eligible pairs attach
dynamically from t≈0 (demonstrates dynamic attach across the
antiparallel regions).

**Reg. 5 — crosslinks (scope item 4).** PXL=1 with the R8 gate in mode
**PBUND=2** (antiparallel-selective, `cos <= -COSB`): registered because
the fiber's load-bearing overlap is antiparallel and myosin
contractility needs the antiparallel regions crosslinked (oracle scope
item 4). Interaction with assembly: same-half parallel pairs are both
gate-rejected and geometrically out of capture range, so crosslinks form
ONLY between halves in the overlap; they provide the mechanical coupling
that returns a slip-ruptured filament end toward its attach zone.
At construction all 6 adjacent pairs are at exact rest (Δyz=1.5=DX0).
XLMAXF=2 per filament = the 2 adjacent opposite-half neighbors (exactly
saturated by construction); MAXXL=24 ≥ 6.

**Reg. 6 — SF adhesion channel mechanics.** Per-filament bond arrays
(SFAM/SFAB/SFABORN/SFAX/SFAY/SFAZ/SFAE, R6 ADH* pattern). SFAKIN: per
active filament per step draws UAT (slot 7010+2(F−1)) and URP
(7011+2(F−1)) unconditionally (ADHKIN draw convention), ascending F,
called after MYOKIN. Attach Bernoulli `P=MIN(1,KONA*DT)` when eligible
(reg. 2 zones); target on the plane with the attach-time bead (y,z)
(R6 convention — constructed bonds at the zone edge therefore carry the
standard 0.5 initial stretch; they are emitted as step-0 `sfa` events
so `cum(sfa)-cum(sfr)=live bonds` is exact from t=0). Rupture: hard
release `d>SMAXA` (cause 2) else slip (cause 1). End grouping rule
(scope item 5): `SFAE=0` if the bond target is the left plane (XADH),
`1` if right (XSF2), assigned at attach; per-end accumulators in
SFA_FORCE. No exclusion of SFA-gripped monomers from XL/motor candidacy
(spring forces superpose; the R6 pointed-tail XL exclusion does not
extend to the barbed grip — registered). Records (strict WRITE arity):
`sfa STEP F M B tx ty tz E` (attach), `sfr STEP F M lifetime fx fy fz
cause E` (rupture; force = current spring force at release, adhr
convention), `sfas STEP E nb trx try trz fmag arate rrate` (windowed
per-end census, TWO lines per NDIAG window, adhs convention:
trx.. = Σ(−F)/NDIAG substrate traction, fmag = mean |F| per bond-step,
arate/rrate = events/step this window).

**Reg. 7 — fiber instrumentation (scope item 5, records-only, zero
RNG, no force, no feedback).** Windowed `fib` record at NDIAG:
`fib STEP nfil npoly tipxL tipxR flen ten nmyo nxl` — nfil/npoly = count
and ΣFILLEN over constructed slots 1..2*NHF (post-sever remnants in new
slots are reported by the standard `fil` records; registered); tipxL /
tipxR = mean barbed-head-bead x over active slots 1..NHF / NHF+1..2*NHF;
flen = tipxR − tipxL; nmyo/nxl = current counts (derived-record
preference). **Tension definition (registered):** midplane cross-section
force sum at `XSFM=(XADH+XSF2)/2=5.5`: every backbone junction spring
(FILBONDS list), crosslink, or motor spring straddling the midplane
contributes the signed x-force it exerts on the right-side bead,
negated (tension > 0 = contractile); accumulated per step inside
FILBONDS/XLINK_FORCE/MYO_FORCE under `PSF=1 .AND. MIRROR=0` guards
(pure accumulation — forces unchanged), windowed mean /NDIAG. WCA
contacts excluded (collisional, not tension-bearing). Adhesion bonds
never straddle the midplane (excluded by construction). Census records
`census`/`fil` cover per-window fiber census (existing machinery).

**Reg. 8 — perturbation (scope item 6).** PSEV=0 inert default (all
R11-a cert/sign/smoke gates run PSEV=0). PSEV=1: at STEP=SEVSTEP
(default 25000), deterministic midplane sever: every active filament
whose contour straddles XSFM (head-bead positions on both sides) is cut
at the junction nearest the midplane: the barbed-side remnant keeps its
slot (and its SF/R6 bonds — both grip types sit barbed-side/pointed-tip
and are handled as below), the pointed-side remnant becomes a new
filament in the first free slot (ascending scan, deterministic).
Crosslinks and motors touching pointed-remnant monomers are released
with **cause 5 = sever-induced release** (new registered cause code,
PSEV=1 runs only); an R6 ADH bond whose gripped monomer moves to the
remnant TRANSFERS to the new slot (monomer-grip convention, no event);
SF bonds always stay on the kept barbed side. `sev STEP F G MC QC`
record per cut. Zero RNG. REBUILD_BONDS after. R11-a runs one sever
smoke as a machinery/books check; the O-S6 repaired/failed-measurable
classification is R11-c.

**Reg. 9 — MIRROR static cert (R11-a).** (a) mirror_off: MIRROR=1, all
channels OFF ⇒ byte-identical to the R10/R9 `mirror_off.out`. (b)
cert_sf1: the R10 cert stack (PADH=1, PXL=1, PBUND=1, PCLU=1, PTIPA=1,
PMYO=1 — cert-stack footing only, not a filopodia run) + PSF=1, MIRROR=1:
INIT_CERT adds filaments 14 (monomers 60..63, y=4.0, z=6, axis −x,
barbed monomer 63, head bead 125 at (2.5,4,6)) and 15 (monomers 64..67,
y=4.6, z=6, axis +x, barbed monomer 67, head bead 133 at (8.5,4.6,6))
at exact rest geometry, both polarity orientations present, all
distances to parent cert beads > 1.4 > WCUT (verified by placement), so
parent CFG(118)/FRC(118)/CERT/CERT_ADH/CERT_XL/CERT_TIP/CERT_MYO lines
are byte-identical to `runs24/static_cert/cert_myo1.out` (pure zero
additions). Constructed SF bonds: filament 14 → target (XADH,4,6):
d=0.5 pure-x, F(bead 125) = −2.0 x̂, E=0.5; filament 15 → target
(XSF2,4.6,6): d=0.5 pure-x, F(bead 133) = +2.0 x̂, E=0.5; esfa = 1.0.
New cert lines `SFAC` (per bond) + `CERT_SFA esfa`. FD anchors
`PX(125):=2.5`, `PX(133):=8.5`; fd binaries displace ±1e-6; FD target
`∂esfa/∂x = −F_x` = +2.0 (bead 125) / −2.0 (bead 133); tolerance 1e-8.
Channel-isolated convention (R10 limitation 4 carried): FD on the
isolated `esfa` term, justified numerically — total-energy FD is
wall-contact-ulp-dominated (ewca ~7.6e-6); at the constructed anchor
points all other first derivatives vanish (junction/intra springs at
exact rest, no WCA contact, off all walls), so the isolated FD equals
the total-energy FD to ulp.

**Reg. 10 — sign battery (constructed fiber).** Config: PSF=1, VMYO=120,
KOFFM=0, SMAXM=100, KOFFA=0, SMAXA=100 (bonds never rupture — static
anchoring, config-level like KOFFM=0 in R10), frozen kinetics
(KON=KONP=KHYD=KOFFB_T=KOFFB_A=KOFFP_T=KOFFP_A=0, PCAP=0), PBR=0,
PSTN=0, DIMERS=0, PXL=0, PADH=0, NSTEPS=2000. Expectation: motor heads
step barbed-ward on their track: head on a left-half filament (axis −x)
`dx<0`; on a right-half filament (axis +x) `dx>0` — heads walk APART
(contractile loading). HARD criteria (R10 reg. 6 addendum carried):
contour invariant `MNEW=MOLD+1` on 100% of myost events + strict lab
signs on the deterministic constructed-geometry battery (pre-bound
motor events from t=0); lab-sign statistics thereafter reported as
ranges (buckling caveat).

**Reg. 11 — micro-smoke config (O-S7 + behavior report, 50k).**
Anchored copy: PSF=1, PXL=1, PBUND=2, PMYO=1, PADH=1, PBR=0, PSTN=0,
DIMERS=0, NSTEPS=50000 (NDIAG=500, SEED=77031 defaults), kinetics at
certified defaults (live: KON=500, KONP=1.0, KOFFB_T=0.045,
KOFFB_A=0.18, KHYD=0.03, KOFFP_T=0.05, KOFFP_A=0.1), PCAP=1 (default;
registered treadmill footing: absorbing caps (KUNC=0) arrest wall-ward
barbed growth at the planes on the ~1/(KCAP·DT) ≈ 6.7k-step scale while
pointed ends stay live at dynamic equilibrium — a registered
construction-config choice, not a physics change: PCAP=1 is the engine
default). PADH=1 is part of the full channel stack; R6 pointed-tail
bonds are NOT part of the anchor design (fiber pointed ends start
outside the R6 zone); any later R6 attaches (pointed growth) are
visible in adha/adhr/adhs and reported separately — O-S3 per-end
traction reads the SF channel's own `sfas` records. Also a PSEV=1
sever arm (SEVSTEP=25000) as the perturbation machinery check (books +
sev records). Expected physics (registered, ranges not gates): motors
wind to stall-scale tension (|F|~4.3); slip anchors with FBA=1 under
stall-scale loads are rupture-prone (the R9 tip-bottleneck lesson —
traction is linkage-limited); stick-slip attach/rupture cycles with
crosslink-mediated restoration are the expected dynamic; traction while
bonded must be inward-signed at both ends (reg. 2). Distributions
reported as-is; no parameter tuning to hit a number.

**Reg. 12 — O-S1 at build time.** Config = the R10 O-P1 config on the
new engine (anchored copy: PBR=0, F_EXT=1.0, PXL=1, NSTEPS=50000,
PMYO=0, PSF=0, PSEV=0, all other channels default/OFF) ⇒ byte-identical
to `runs23/smokes/op1_50k.log` (sha256 007e6b2b…faa0). CMP gate.

Failure responses (carried, pre-registered): byte-identity break ⇒ find
the unguarded draw/record and fix before any other work; FD or sign
fail ⇒ instrumentation/geometry bug, fix and re-certify; books fail ⇒
STOP; rupture-dominated anchors / assembly pathology ⇒ report
distributions as-is (R9 lesson: never tune physics to hit a number).

## Builder errata (R11-a, post-build, additive to regs. 1-12)

1. **Reg. 4 grip indices (correction):** pre-bound motor grips are the
   head-x=5.5 monomers on both halves: left half k=5 (monomer B0+6:
   6, 15, 24 for pairs (1,4),(2,5),(3,6)); right half k=3 (monomer
   B0+4: 31, 40, 49). Head-bead x=5.5 and d=RSF=DMY0=1.5 exactly on
   both sides as registered; only the "k=5 on both" wording was wrong
   (left/right k differ because the halves' contours run opposite ways).
2. **myor cause 6 = construction overwrite (registered):** with PSF=1,
   INIT_MYO (PMYO>0) runs first and emits its unit's step-0 myoa;
   INIT_SF then overwrites all state. To keep the motor inventory
   record-exact, INIT_SF first releases every live motor with cause 6
   (construction overwrite) via the certified MYO_REL path. Verified:
   cum(myoa)-cum(myor) == nmyo at every myos window in all R11 runs.
3. **INIT_CERT R11 cert block is fully unrolled with literal constants
   (build note):** all parent init routines carry a pre-existing latent
   UB (STATE(I) written over I=1..NB=800; STATE has NMAX=400 entries),
   which gcc -O3 -march=x86-64-v3 exploits; it miscompiled the first
   (loop+derived-arithmetic) version of the R11 cert block (PX(134)
   computed from a stale zero; correct at -O0). Parent cert lines were
   never affected (mirror_off byte-identical, sha 3f3269db..., and
   cert_sf1 parent lines byte-identical). The unrolled literal block is
   immune; parent lines remain untouched (additive diff +811/-0).
4. **INIT_SF gas loop:** verbatim INIT_MYO pattern (bounded
   DO T = 1, 60 attempts, 5 draws per attempt, both beads tested,
   sample box [2, LBOX-2]^3, same RCNT=1000 hash stream). An earlier
   draft with an unbounded acceptance loop was replaced before any run.
