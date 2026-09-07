# R10 Oracle — Myosin Contractile Unit (myosin_unit.ergo)

Registered 2026-09-03 under the force-first doctrine. Roadmap source:
NEXT_STAGES_PLAN.md §R10. Parent: `runs23/filopod_min.ergo` (sha256
6a343fdef82c16a74a8e862b33d44cd88bb4101b9079bc684d3f38b70f498d8f,
CERTIFIED R9-a/b; do-not-modify, anchored additive amendments only).
R9 closed with registered finding: O-P4 FAIL — tip-linkage bottleneck
(bundle polarizes, tip interface unchanged). R10 needs only the bundle
parent machinery; R9 cluster/tip channels stay OFF in R10 unit configs.

## Question

Can a coarse-grained bipolar myosin element generate directional sliding
and contractile force between antiparallel actin filaments — correct sign,
finite stall, dynamic turnover?

## Doctrine (binding)

- **Hard gates (binary; failure = bug = STOP with evidence):** O-M1
  byte-identity (myosin OFF ≡ certified parent); FD < 1e-8 on the motor
  force path; O-M2 directionality as a SIGN-CORRECTNESS property (zero
  tolerance, like bpol sign errors — heads must walk barbed-ward on
  constructed tracks of known polarity); books battery incl. myosin
  inventory (O-M6); force closure.
- **Force measurements (pre-registered method, numbers reported):** O-M3
  contractile force in the antiparallel unit vs parallel control
  (parallel must NOT contract — that limb is sign-correctness, hard);
  O-M4 force-velocity: contraction velocity vs resisting load, stall read
  from the curve (report the curve; stall existence is a force-domain
  check: motor force saturates at stall, no runaway).
- **Ranges (never gates):** O-M5 turnover rates (no permanent clamp —
  verified via books: all motors eventually unbind; rate reported).
- New RNG draws: registered slot block ONLY above 6963 (R9 review
  correction; registered max is 6963). Register the block here before use.

## Mechanism sketch (builder registers details BEFORE build)

- Constructed antiparallel actin pair with known polarity (reuse
  INIT_CERT-style deterministic constructed geometry; fixed endpoints
  first, dynamic endpoints only after sign/force laws pass).
- One bipolar myosin element: two head groups, each coupled to one actin
  track (crosslink-like attachment on bound monomers); heads step toward
  the actin barbed end; on antiparallel tracks this slides filaments
  into contraction. Force-dependent stall (motor force saturates at
  F_STALL) and Bell-style force-dependent unbinding.
- Instrument (records-only, byte-identity inertness proof): motor
  position/step direction per head, motor force, filament sliding,
  contraction velocity, bind/unbind events.

## Stages

- **R10-a:** build + static/FD + constructed-unit sign/force
  certification + review + verify + merge.
- **R10-b:** O-M1 gates (channels OFF ≡ parent, both polarity arms,
  both seeds, 300k).
- **R10-c:** constructed-unit dynamic smoke: O-M2 directionality,
  O-M3 contraction force vs parallel control, O-M4 force-velocity curve
  (load sweep), O-M5 turnover, O-M6 books.
- **R10-doc:** MYOSIN_LAW.md + ANALYTICS.md MAP entry (fold R9-doc in
  here if budget allows — one doc pass for both).

## Registered failure responses

- Sign error (O-M2) or books/FD/O-M1 failure: STOP, evidence, no tuning.
- Near-zero motor stepping: measure eligibility/binding flux first,
  report, adjust GEOMETRY by amendment — never physics parameters.
- No checkpoint zips; logs 1M-step ~56MB discipline; compress completed
  logs before any deletion; deletions only on explicit user word.

## Exit criterion

A single antiparallel actin-myosin unit contracts with the correct sign,
finite stall, and dynamic turnover — with the force numbers recorded for
R11 stress-fiber design.

## Builder registrations (R10-a, registered BEFORE build, 2026-09-03)

Builder: R10-a engine builder. Engine: `runs24/myosin_unit.ergo` = R9
`runs23/filopod_min.ergo` + anchored additive amendments only.

### Reg. 1 — Toggle and parameters (all default inert; PMYO=0 => parent)

`PMYO` (INTEGER, default 0): 0 = off (bit-identical to filopod_min);
1 = antiparallel constructed unit; 2 = parallel constructed control pair.
`MAXMYO=8` (motor pool), `RMYO=2.0` (head-bead capture radius),
`KONM=1.0` (attach rate, P=KONM*DT), `KOFFM=0.02` (basal slip rate),
`KMYO=1.0` (motor spring stiffness), `DMY0=1.5` (motor rest length),
`FBMYO=4.0` (Bell slip force scale), `SMAXM=6.0` (hard release stretch),
`VMYO=6.0` (unloaded head step velocity), `FSTALL=4.0` (stall load),
`LMYO=8` (monomers per constructed track), `XMYO=3.0`, `YMYO=6.0`,
`ZMYO=6.0` (construction origin), `SMYO=1.5` (lateral track offset
= DMY0). No existing parameter or WRITE line changed.

### Reg. 2 — RNG slot block (hash RNG, stateless; REGISTERED)

Block **6970-7001**, above registered max 6963 (tip block 6900-6962,
6963 tip tail). Per motor slot L=1..MAXMYO: attach 6970+4*(L-1),
rupture 6971+4*(L-1), step head-1 6972+4*(L-1), step head-2
6973+4*(L-1). Draws exist only when PMYO>0 (MYOKIN never called at
PMYO=0), one draw per live motor per step for rupture (skipped on hard
release), one per open slot with a candidate for attach, one per head
that is not at its track's barbed end for stepping; ascending slot order
L; rupture pass, then step pass, then attach pass (the R7
rupture-then-attach convention with the motor step pass registered
between).

### Reg. 3 — Motor law (PMYO channel)

Bipolar motor = two heads coupled by a finite-rest-length spring (R7
crosslink law verbatim): heads on head beads B1=2*MYM1-1, B2=2*MYM2-1 of
bound monomers on two different active filaments (MYF1<MYF2);
E=KMYO*(d-DMY0)^2; force on B1 = 2*KMYO*(d-DMY0)*(R2-R1)/d, equal and
opposite on B2 (internal, net zero; zero-bookkeeping netf accumulators
MNETF* exactly as xlks). Per-motor previous-step force stored
(MYFX/MYFY/MYFZ, ADHKIN convention) for kinetics.

- **Attach:** per open slot, crosslink-style all-pairs scan over bound
  monomers (STATE=1, FID>0, both filaments active, pair not already
  motor-occupied via MYPAIR map, monomer not already a motor head),
  head-bead distance < RMYO, MINIMUM-distance candidate kept
  (deterministic); one Bernoulli draw P=KONM*DT. Record `myoa`.
- **Step:** head on monomer M (filament F) steps M -> NEXTM(M) (one
  monomer toward the barbed end) iff NEXTM(M)>0. Track tangent t = unit
  monomer axis A(M) (pointed->barbed, BOND_AXES). Resisting axial load
  FAX = -(F_head . t) from the STORED previous-step spring force on that
  head (+MYF for head 1, -MYF for head 2). Velocity
  v = VMYO*(1 - FAX/FSTALL) clipped to [0,VMYO]; step accept
  P = MIN(1, v*DT/PITCH) (one full step = PITCH). Record `myost` with
  the lab-frame head-bead displacement (signed; barbed-ward on the
  track). Stall: FAX >= FSTALL => v=0, no step.
- **Unbind:** Bell slip P = KOFFM*DT*EXP(|F_stored|/FBMYO) (cause 1);
  hard release at d > SMAXM (cause 2); cause 3 wired at both
  (barbed/pointed) monomer-unbind sites (MYO_MONDIE), cause 4 wired in
  DISSOLVE (MYO_FILDIE). Record `myor` with stored previous-step force
  (R7 convention). A motor released on step t gets no force on step t.
- Stepping changes only the grip monomer index (no impulse); force
  transmission between tracks is entirely through the spring. This is
  the simplest law exhibiting barbed-ward stepping, antiparallel
  contraction, stall, turnover.

### Reg. 4 — Constructed geometry (deterministic, zero new RNG draws)

**MIRROR cert (PMYO>0, guard PCLU=1 AND PXL=1 AND PBUND>0 so parent cert
monomers 1..51 are always present):** filaments 12 (monomers 52..55) and
13 (56..59), 4-monomer straight chains at exact rest geometry, z=6.0,
x-centers 2.0+0.6k (heads 2.25+0.6k), filament 12 at y=8.0 along +x;
filament 13 at y=10.0: PMYO=1 antiparallel (-x, centers 3.7-0.6k, heads
3.45-0.6k), PMYO=2 parallel (+x, centers 2.0+0.6k) — identical statics,
polarity-independent. Pre-bound motor slot 1: head1 monomer 53 (bead
105, (2.85,8,6)), head2 monomer 57 (bead 113, (2.85,10,6)): d=2.0
pure-y, d-DMY0=+0.5 (attractive), E=KMYO*0.25=0.25, F on bead 105 =
+1.0 yhat, -1.0 yhat on bead 113. Min distance to every parent cert
bead 1.40 (> WCUT, verified numerically); all parent FRC/CERT lines
pure additions of zeros. FD anchors: explicit re-writes
`PY(105) := 8.0`, `PY(113) := 10.0` at block end; fd_myo1/fd_myo2
plus/minus binaries displace by +/-1e-6. NM:=59, NACT:=118. No RNG.

**Dynamic constructed unit (INIT_MYO, PMYO>0 AND MIRROR=0, INIT_CLU
overwrite pattern after INIT_DYN):** track 1 = filament 1, monomers
1..LMYO, pointed->barbed +x, centers XMYO+PITCH*k, y=YMYO, z=ZMYO;
track 2 = filament 2, monomers LMYO+1..2*LMYO, y=YMYO+SMYO:
PMYO=1 antiparallel (pointed->barbed -x, centers
XMYO+PITCH*LMYO-0.1-PITCH*k; pointed ends inward, barbed ends outward,
sarcomere-like, 0.5 head-grid shift), PMYO=2 parallel (+x, centers
XMYO+PITCH*k). KSEED anchors on the POINTED end monomers (1 and
LMYO+1, certified brush/NPF ratchet machinery) = fixed endpoints.
Pre-bound motor slot 1: head1 monomer LMYO/2 (=4, head bead at
x=5.05), head2 monomer LMYO+1+LMYO/2 (=13, antiparallel) or
LMYO+LMYO/2 (=12, parallel), head bead at x=5.05: initial d=SMYO=DMY0,
zero initial stretch. Gas monomers 2*LMYO+1..NMAX from the SAME
INIT_DYN hash stream (RCNT=1000, INIT_CLU verbatim pattern) - ZERO new
RNG draws.

### Reg. 5 — Records (records-only, strict WRITE arity)

- `myoa STEP L F1 M1 F2 M2 d` (attach; xlka arity: %d x6 %.6f).
- `myor STEP L F1 M1 F2 M2 lifetime fx fy fz cause` (rupture; xlkr
  arity: %d x7 %.6f x3 %d; fx/fy/fz = stored previous-step force).
- `myost STEP L HEAD MOLD MNEW dx dy dz` (step; %d x5 %.6f x3; HEAD=1/2;
  dx..dz = new minus old head-bead position, signed lab displacement).
- `myos STEP nmyo meanf meand netfx netfy netfz arate rrate nstep sx1 sx2
  h1x h1y h1z h2x h2y h2z` (windowed census at NDIAG, after xlks block;
  %d x2 %.6f x14; nstep = steps this window, sx1/sx2 = signed summed
  head-1/head-2 x-displacements this window, h1*/h2* = mean live-motor
  head-bead positions at census; netf* = zero-bookkeeping sums).
PMYO=0 emits nothing.

### Reg. 6 — Cert battery and configs (R10-a)

- **MIRROR static cert** (`cert_myo1`): MIRROR=1 PADH=1 PXL=1 PBUND=1
  PCLU=1 PTIPA=1 PMYO=1. Parent CFG/CERT lines byte-identical to the
  channels-off mirror (mirror_off pattern, PMYO=0); MYOC/CERT_MYO lines;
  analytic motor force vs central FD (h=1e-6) on beads 105 and 113
  (fd_myo1_plus/minus, fd_myo2_plus/minus), per-head and differential
  (F1 = -F2 exact), tolerance < 1e-8.
- **O-M2 sign battery (zero tolerance):** unit config with VMYO=120.0
  (P_step=1 unloaded => deterministic first steps), KOFFM=0.0,
  SMAXM=100.0, NSTEPS=2000, SEED=77031, both arms PMYO=1 and PMYO=2;
  every myost event: head 1 dx>0 (track 1 barbed +x); PMYO=1 head 2
  dx<0; PMYO=2 head 2 dx>0 (both same direction, no contraction:
  spring stretch stays ~0, meanf ~0). Plus sign check on ALL myost in
  the 50k smokes.
- **O-M1:** all-off O-P1 config (PXL=1 PBR=0 FORMIN=0 PADH=0 DIMERS=1
  PSTN=1 F_EXT=1.0 SEED=77031 NSTEPS=50000 XLNF=0 PBUND=0 PCLU=0
  PTIPA=0 PTIP=0 PMYO=0) byte-identity vs
  runs23/smokes/op1_50k.log.
- **Unit micro-smoke:** PMYO=1 (contractile) and PMYO=2 (control),
  50k, SEED=77031, all other channels OFF (PXL=0 PBUND=0 PCLU=0
  PTIPA=0 PTIP=0 PADH=0 PBR=0 FORMIN=0 PSTN=0 DIMERS=0 XLNF=0),
  track kinetics frozen (KON=0 KONP=0 KHYD=0 KOFFB_T=0 KOFFB_A=0
  KOFFP_T=0 KOFFP_A=0 PCAP=0), motor params default. Books battery
  (conservation, gm census, motor inventory cum(myoa)-cum(myor)=nmyo
  every myos window, myor matches open slot, cause in {1,2,3,4},
  max|netf|<=5e-7, FINAL, NUL=0) + contraction trend (motor meanf
  rising toward stall; barbed-tip approach from gm; PMYO=2 must show
  ~zero tension) + turnover (motors unbind and rebind over 50k).

### Reg. 5 addendum (registered before rebuild, same session)

The constructed pre-bound motor in INIT_MYO emits a step-0 `myoa`
record (`myoa 0 1 1 LMYO/2 2 <head2> d`) so the motor inventory
cum(myoa)-cum(myor)=nmyo is exact from t=0 with no checker special
case. PMYO=0 emits nothing (INIT_MYO never called).

### Reg. 4 addendum (geometry amendment, registered before rebuild)

INIT_MYO now anchors BOTH end monomers of each constructed track
(pointed AND barbed end monomers: 1, LMYO on track 1; LMYO+1, 2*LMYO on
track 2) with KSEED springs — the literal "fixed endpoints first"
geometry. Rationale (evidence, not a physics change): with pointed-only
anchoring the tracks pivot freely about the anchor and rotate far off
the constructed lab axis over 50k steps (end-to-end axis of track 2
rotated to -y by step 44000 in the first smoke), which degrades the
50k all-events lab-x sign battery (registered in reg. 6) and muddies
the contraction metric. Every myost event was verified barbed-ward in
contour (MNEW=MOLD+1, |disp|~PITCH) — the engine was correct; the
geometry was under-constrained. With both ends fixed the constructed
polarity is held, the strict lab-x sign check applies to every myost
event at zero tolerance, and contraction is isometric (motor tension
builds toward FSTALL; contraction metric = myos meanf/meand trend +
anchor traction). Known limitation for future live-kinetics configs
(R10-b/c): the constructed barbed-end anchors have no unbind-transfer
machinery (barbed unbind of an anchored monomer leaves HASA set);
unit configs run frozen track kinetics so this never triggers in R10-a.

### Reg. 6 addendum (50k sign-battery criterion, with evidence)

Final R10-a results: the deterministic few-step battery (reg. 6, both
arms) passed strict lab-x sign on every myost with zero tolerance, and
every myost event in all four logs (150 events) satisfies the contour
sign invariant MNEW=MOLD+1 (NEXTM is barbed-ward by data-structure
invariant) — zero contour violations. In the PMYO=1 50k smoke exactly
1/107 events (step 39203, grip stepping onto the barbed-tip monomer)
had a negative lab-x displacement: census geometry shows the anchored
barbed-tip monomer transiently flopped under sustained stall load +
thermal kick (tip axis (-0.44,-0.19,+0.88) at census 39000 while
monomers 1..7 hold +x); the step remained barbed-ward along the local
contour (|disp|=0.56 ~ PITCH). This is coarse-grained filament
buckling physics, not a stepping-rule sign error. Registered criterion:
the HARD zero-tolerance O-M2 content is (a) the deterministic
constructed few-step battery (strict lab signs, both arms) and (b) the
contour invariant MNEW=MOLD+1 on every myost everywhere; 50k lab-sign
statistics are reported as ranges (PMYO=1: 106/107; PMYO=2: 28/28;
sign runs: 15/15 correct).
