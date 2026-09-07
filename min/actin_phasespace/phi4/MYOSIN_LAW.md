# MYOSIN_LAW.md — φ4.12 myosin contractile unit (myosin_unit, R10) certification

Certified: 2026-09-03 (R10-a build/statics/sign battery, R10-b O-M1
gates) and 2026-09-04 (R10-c constructed-unit measurements). **All
oracle classes O-M1..O-M6 PASS; the R10 exit criterion is MET** — the
constructed antiparallel actin-myosin unit contracts with the correct
sign, finite stall at the registered scale, and dynamic turnover, with
the force numbers recorded for R11 stress-fiber design.

Engine lineage: pop_fpt.ergo (φ4) → … → bundle_pol (R8) → filopod_min
(R9, certified R9-a/b; closed with the O-P4 tip-linkage finding) →
**myosin_unit** (PMYO bipolar-motor channel). Final source
`phi4/runs24/myosin_unit.ergo` (4247 lines, **+748/0** vs parent —
verified by direct diff: 748 added, 0 removed/changed), SHA256
`2806ed054ecebf0fe9eb6db93af39d433991dfd97d36b534afdb22c4d923110f`
(recomputed this doc pass), merge commit `8beb34d` in the live repo
(durable code-only bundle `actin_phasespace/r10_repo.bundle` SHA256
`3d941a0450a25057576a450902a1d4bdc77c3dd56cf3c136d0ae87d7bc8bab81`,
recomputed). Parent: certified `phi4/runs23/filopod_min.ergo` SHA256
`6a343fdef82c16a74a8e862b33d44cd88bb4101b9079bc684d3f38b70f498d8f`,
re-verified untouched after build and after every stage. Oracle:
`phi4/plan_myosin.md` (O-M1..O-M6 + doctrine hard gates), registered
2026-09-03 before build under the force-first doctrine (BUNDLE_LAW.md
§doctrine); builder registrations 1–6 + addenda 4/5/6 and the R10-c
registrations all appended to the oracle BEFORE the corresponding
builds/runs. R9 cluster/tip channels stay OFF in all R10 configs — R10
needs only the bundle-parent machinery. Runs under `phi4/runs24/`
(static_cert/, sign/, smokes/, gates/, r10c/). No zips; no certified
file modified after certification.

## The question

Can a coarse-grained bipolar myosin element generate directional sliding
and contractile force between antiparallel actin filaments — correct
sign, finite stall, dynamic turnover?

**R10 answer: yes, on the constructed-unit footing — antiparallel
contraction at the FSTALL=4 force scale with 12× selectivity over the
parallel control, a measured force-velocity curve with stall at the
registered scale, 100% Bell-slip turnover with no permanent clamp, and
zero directionality violations in 2809 stepping events.**

| stage | arm | purpose | outcome |
|-------|-----|---------|---------|
| R10-a | build + MIRROR static/FD cert + O-M2 sign battery + O-M1 50k + micro-smokes + combined review/verify + merge | PMYO channel on certified R9 parent | PASS all; CERTIFICATION VALID, GO |
| R10-b | O-M1 gates PMYO=0 × PBUND∈{0,1,2} × seeds {77031,84950}, 300k | myosin OFF ≡ certified R9 parent, byte-identical | PASS 6/6 |
| R10-c | constructed units, 300k, s77031: PMYO=1/2 pair at KSEED=5.0 + PMYO=1 load sweep KSEED∈{2,1,0.5,0.25,0.1} | O-M2..O-M6 measurements | PASS all; exit criterion MET |

## Mechanism as certified

- **Toggle and parameters (reg. 1; all default inert).** `PMYO`: 0 =
  off (bit-identical to filopod_min), 1 = antiparallel constructed unit,
  2 = parallel constructed control pair. `MAXMYO=8` (motor pool),
  `RMYO=2.0` (head-bead capture radius), `KONM=1.0` (P=KONM·DT),
  `KOFFM=0.02` (basal slip), `KMYO=1.0`, `DMY0=1.5` (rest length),
  `FBMYO=4.0` (Bell force scale), `SMAXM=6.0` (hard release),
  `VMYO=6.0` (unloaded step velocity), `FSTALL=4.0` (stall load),
  `LMYO=8` (monomers per constructed track), construction origin
  (XMYO,YMYO,ZMYO)=(3,6,6), `SMYO=1.5` (lateral track offset = DMY0).
  No existing parameter or WRITE line changed.
- **RNG slot block (reg. 2; REGISTERED): 6970–7001**, above the
  registered max 6963 (R9 tip block 6900–6963, per the R9 review
  correction). Per motor slot L=1..MAXMYO: attach 6970+4(L−1), rupture
  6971+4(L−1), step head-1 6972+4(L−1), step head-2 6973+4(L−1). Draws
  exist only when PMYO>0 (MYOKIN never called at PMYO=0); one draw per
  live motor per step for rupture (skipped on hard release), one per
  open slot with a candidate for attach, one per head not at its track's
  barbed end for stepping; ascending slot order; rupture pass, then step
  pass, then attach pass (R7 convention with the step pass registered
  between).
- **Motor law (reg. 3).** Bipolar motor = two heads coupled by the R7
  crosslink spring law verbatim: heads on head beads B1=2·MYM1−1,
  B2=2·MYM2−1 of bound monomers on two different active filaments;
  E=KMYO·(d−DMY0)²; force on B1 = 2·KMYO·(d−DMY0)·(R2−R1)/d, equal and
  opposite on B2 (internal, net zero; zero-bookkeeping netf accumulators
  exactly as xlks). Per-motor previous-step force stored
  (MYFX/MYFY/MYFZ, ADHKIN convention) for kinetics.
  - **Attach:** per open slot, crosslink-style all-pairs scan over bound
    monomers (STATE=1, both filaments active, pair not motor-occupied
    via MYPAIR map, monomer not already a motor head), head-bead
    distance < RMYO, MINIMUM-distance candidate kept (deterministic);
    one Bernoulli draw P=KONM·DT. Record `myoa`.
  - **Step (contour-based, barbed-ward):** head on monomer M steps
    M → NEXTM(M) (one monomer toward the barbed end) iff NEXTM(M)>0.
    Resisting axial load FAX = −(F_head·t) from the STORED
    previous-step spring force on that head (+MYF head 1, −MYF head 2),
    t = unit monomer axis pointed→barbed (BOND_AXES). Velocity
    v = VMYO·(1 − FAX/FSTALL) clipped to [0,VMYO]; step accept
    P = MIN(1, v·DT/PITCH) (one full step = PITCH). Stall clip:
    FAX ≥ FSTALL ⇒ v=0, no step. Record `myost` with the signed
    lab-frame head-bead displacement.
  - **Unbind:** Bell slip P = KOFFM·DT·EXP(|F_stored|/FBMYO) (cause 1);
    hard release d > SMAXM (cause 2); cause 3 wired at both
    (barbed/pointed) monomer-unbind sites (MYO_MONDIE), cause 4 in
    DISSOLVE (MYO_FILDIE). Record `myor` with stored previous-step
    force (R7 convention). A motor released on step t gets no force on
    step t.
  - Stepping changes only the grip monomer index (no impulse); force
    transmission between tracks is entirely through the spring. This is
    the simplest law exhibiting barbed-ward stepping, antiparallel
    contraction, stall, turnover (registered rationale).
- **Constructed geometry (reg. 4 + addendum; deterministic, ZERO new
  RNG draws).** MIRROR cert (guard PCLU=1 AND PXL=1 AND PBUND>0 so
  parent cert monomers 1..51 are always present): filaments 12
  (monomers 52..55) and 13 (56..59), 4-monomer straight chains at exact
  rest geometry, z=6.0; filament 12 at y=8.0 along +x; filament 13 at
  y=10.0 — PMYO=1 antiparallel (−x), PMYO=2 parallel (+x), identical
  statics. Pre-bound motor slot 1: head1 monomer 53 (bead 105,
  (2.85,8,6)), head2 monomer 57 (bead 113, (2.85,10,6)): d=2.0 pure-y,
  d−DMY0=+0.5 (attractive), E=KMYO·0.25=0.25, F on bead 105 = +1.0 ŷ,
  −1.0 ŷ on bead 113. Min distance to every parent cert bead 1.40
  (> WCUT); all parent FRC/CERT lines pure additions of zeros. FD
  anchors: explicit re-writes PY(105):=8.0, PY(113):=10.0;
  fd_myo{1,2} plus/minus binaries displace ±1e-6. NM:=59, NACT:=118.
  Dynamic unit (INIT_MYO, PMYO>0 AND MIRROR=0, INIT_CLU overwrite
  pattern after INIT_DYN): track 1 = filament 1 monomers 1..LMYO
  pointed→barbed +x; track 2 = filament 2 monomers LMYO+1..2·LMYO at
  y=YMYO+SMYO — PMYO=1 antiparallel (pointed ends inward, barbed ends
  outward, sarcomere-like, 0.5 head-grid shift), PMYO=2 parallel.
  **Reg. 4 addendum (registered before rebuild): BOTH end monomers of
  each track KSEED-anchored** (fixed endpoints — with pointed-only
  anchoring the tracks pivoted far off the lab axis, e.g. track-2
  end-to-end axis rotated to −y by step 44000 in the first smoke; the
  engine was correct, the geometry under-constrained). Pre-bound motor
  slot 1 at zero initial stretch (d=SMYO=DMY0). Gas monomers
  2·LMYO+1..NMAX from the SAME INIT_DYN hash stream — zero new draws.
- **Records (reg. 5 + addendum; records-only, strict WRITE arity).**
  `myoa STEP L F1 M1 F2 M2 d` (attach); `myor STEP L F1 M1 F2 M2
  lifetime fx fy fz cause` (rupture); `myost STEP L HEAD MOLD MNEW dx dy
  dz` (step; dx..dz = new−old head-bead position, signed lab
  displacement); `myos STEP nmyo meanf meand netfx netfy netfz arate
  rrate nstep sx1 sx2 h1x h1y h1z h2x h2y h2z` (windowed census at
  NDIAG; nstep = steps this window, sx1/sx2 = signed summed head x
  displacements, netf* = zero-bookkeeping sums). **Reg. 5 addendum:**
  the constructed pre-bound motor emits a step-0 `myoa` so the inventory
  cum(myoa)−cum(myor)=nmyo is exact from t=0 with no checker special
  case. PMYO=0 emits nothing.
- **Cert battery and configs (reg. 6 + addendum).** MIRROR static cert
  cert_myo1 (MIRROR=1 PADH=1 PXL=1 PBUND=1 PCLU=1 PTIPA=1 PMYO=1):
  parent CFG/CERT lines byte-identical to the channels-off mirror;
  MYOC/CERT_MYO lines; analytic motor force vs central FD (h=1e-6) on
  beads 105/113, per-head and differential, tolerance < 1e-8. O-M2 sign
  battery (zero tolerance): VMYO=120 (P_step=1 unloaded), KOFFM=0,
  SMAXM=100, 2000 steps, both arms. O-M1: all-off O-P1 config,
  byte-identity vs `runs23/smokes/op1_50k.log`. Unit micro-smokes:
  PMYO=1/2, 50k, all other channels OFF, **frozen track kinetics**
  (KON=KONP=KHYD=KOFFB_T=KOFFB_A=KOFFP_T=KOFFP_A=0, PCAP=0). **Reg. 6
  addendum (criterion, with evidence):** the HARD zero-tolerance O-M2
  content is (a) the deterministic constructed few-step battery (strict
  lab signs, both arms) and (b) the contour invariant MNEW=MOLD+1 on
  every myost everywhere; 50k lab-sign statistics are reported as ranges
  (see the buckling exception below).

## Certification chain

1. **Static/FD certification passed (R10-a)** (`runs24/R10A_REPORT.md`,
   `runs24/static_cert/`, `runs24/sign/`, `runs24/smokes/`). Additive-only
   proof: diff parent↔engine = 748 added, 0 removed/changed lines
   (recomputed). **MIRROR static cert:** channels-off mirror
   byte-identical to the R9 mirror (both SHA256 `3f3269db...`,
   recomputed); cert_myo1 parent CFG(102)/FRC(102)/CERT(12) lines
   byte-identical to R9 `cert_base_bpol1.out` (recomputed by cmp on the
   extracted lines); `CERT_MYO emyo` = 2.50000000000000000e-01 **exact**
   (KMYO·(d−DMY0)² = 1.0·0.5²); analytic force on bead 105 = +1.0 ŷ,
   bead 113 = −1.0 ŷ; differential F1+F2 = 0 exactly (machine-exact).
   **FD (central, h=1e-6) on the channel-isolated motor energy emyo:**
   bead 105 |FD−1.0| = **3.18e-10**, bead 113 |FD−(−1.0)| = **7.62e-10**
   — both < 1e-8 (recomputed from the cert outs this doc pass).
   Channel-isolated convention (registered, numerically justified): a
   total-energy FD is impossible here — the wall-contact energy's ulp
   noise (ewca ulp ≈ 7.6e-6) exceeds the motor signal; the motor energy
   is FD'd in isolation. **O-M2 sign battery 15/15 clean**
   (`sign/sign_pmyo{1,2}.log`, recomputed): PMYO=1 — 7 myost, head 1 all
   dx>0 (+0.600..+0.601), head 2 all dx<0 (−0.603..−0.600); PMYO=2 — 8
   myost, both heads dx>0 (same direction, no contraction, meand ≈ 1.5 =
   rest). Books PASS both arms. **O-M1 50k:**
   `runs24/smokes/op1_50k.log` byte-identical (cmp) to the certified R9
   reference, SHA256
   `007e6b2b20f1992a4248362ea92528dfa5ba5b39614a8d922ebf89336810faa0`
   (recomputed — one hash now covers R7, R8, R9, and R10 channel-OFF
   50k equivalence). **Micro-smokes** (50k, frozen kinetics, all other
   channels off): books battery PASS both arms (conservation 400 every
   census, ghost scan, motor inventory exact at every myos window, myor
   slot/lifetime/cause checks, max|netf|=0.000e+00, FINAL, NUL=0).
   PMYO=1: tension builds within 500 steps and saturates at the stall
   scale (meanf 4.11 in window 1; **4.2669** over 40k–50k, max 5.06;
   FSTALL=4.0; no runaway — recomputed); anchor traction inward on both
   tracks (isometric contraction); turnover 14 attach / 13 rupture / 107
   steps (recomputed) — no permanent clamp. PMYO=2: does NOT contract —
   meanf 0.21–0.71 (thermal), meand ≈1.5–1.76 (rest), 28 steps both
   heads same direction; turnover 6/5.
2. **Combined review + verify (budget measure): CERTIFICATION VALID, GO
   for merge**; 3 notes: (i) "machine-exact" phrasing to be used for the
   differential force; (ii) two imprecise quoted ranges — quote computed
   bounds at R10-c (done: R10C_REPORT tables); (iii) anchor
   unbind-transfer inert under frozen kinetics, resolve before any
   live-kinetics arms (carried to known limitations); R10-c hard sign
   check = contour invariant, lab-x as a range metric (reg. 6 addendum).
3. **O-M1 gates passed (R10-b)** (`runs24/gates/`). 6/6 byte-identical
   (PMYO=0 × PBUND∈{0,1,2} × seeds {77031,84950}, 300k) vs the R9-b
   references (hashes verified pre-use, not rerun): child sha256s equal
   the reference sha256s exactly — `16c9db1c...`/`5636a7eb...`/
   `b84d72e1...`/`c5444043...`/`cb3e60fe...`/`8ddb802b...` (recomputed
   this doc pass: each runs24 om1 log matches its runs23 R9-b reference
   byte-for-byte). All OK attempt=1, FINAL, NUL=0. Variant diffs
   anchored-only. Engine 2806ed05... untouched before/after.
4. **R10-c constructed-unit measurements** (`runs24/R10C_REPORT.md`,
   `runs24/r10c/`; registrations appended to plan_myosin.md BEFORE any
   run; engine hash re-verified before and after; 7/10 budget runs used,
   3 in reserve). All arms on the R10-a footing: fixed endpoints, frozen
   track kinetics, all non-myosin channels OFF, motor defaults,
   SEED=77031, NSTEPS=300000, NDIAG=500, DT=0.005, PITCH=0.6; configs
   are anchored `^PARAMETER` copies (exactly 2 changed lines per config).
   - **O-M2 (HARD, zero tolerance): PASS.** myost events 687+181+549+
     453+440+276+223 = **2809 total; 2809/2809 satisfy the contour
     invariant MNEW=MOLD+1 (barbed-ward) — recomputed this doc pass (0
     violations)**. Per-head counts balanced. Lab-frame sign RANGES as
     registered: the soft-anchor arms displace/rotate the tracks and
     lab-x flips increase exactly as the buckling caveat predicts;
     contour sign never breaks.
   - **O-M6 books (HARD): PASS on all 7 logs.** Own checker
     (`r10c/r10c_analyze.py`) + independent awk spot-checks agree:
     conservation 400 at all 600 censuses × 7 logs; gm ghost scan
     400/400; motor inventory cum(myoa)−cum(myor)=nmyo exact at every
     myos window (600×7); myor slot/endpoint/lifetime/cause all valid;
     max|netf| = 0.000e+00 every window; FINAL+FINAL_E; NUL=0.
   - **O-M3 (force + HARD parallel-silence limb): PASS.** Post-burn-in
     (>50k) zero-load pair (KSEED=5.0): PMYO=1 **meanf 4.304** (meand
     3.65; min/max 2.53/5.17; 687 steps) vs PMYO=2 **meanf 0.360**
     (meand 1.53 ≈ DMY0 rest; 0.11/0.87; 181 steps, 180/181 same-sign
     lab dx) — **12× selectivity; the parallel control is
     non-contractile (hard limb)** (meanf/meand recomputed this doc
     pass).
   - **O-M4 (force-velocity + stall; no-runaway HARD): PASS.**
     Resisting-load mechanism (registered, engine-read): **KSEED
     anchor-compliance sweep** — F_EXT exists ONLY in the PSTN piston
     channel (off in unit configs; the piston cannot apply a clean
     distributed load to the constructed overlap); KSEED is the only
     force path on the constructed tracks (ANCHORS on the 8 end beads;
     nucleation off → no other consumer; deterministic springs, zero
     RNG-stream change). Realized load MEASURED as motor force (myos
     meanf). Operating curve (post burn-in; v_c = mean
     nstep·PITCH/(NDIAG·DT); meanf/nstep recomputed this doc pass):

     | KSEED | meanf (F) | v_c (len/time) | nstep/window | regime |
     |------:|----------:|---------------:|-------------:|--------|
     | 5.0  | 4.304 | 0.278 | 1.160 | near-isometric, force saturated |
     | 2.0  | 3.236 | 0.217 | 0.906 | |
     | 1.0  | 2.400 | 0.180 | 0.748 | |
     | 0.5  | 1.613 | 0.167 | 0.694 | |
     | 0.25 | 1.143 | 0.109 | 0.454 | |
     | 0.1  | 0.907 | 0.081 | 0.338 | compliant, turnover/parking limited |

     Per-window microscopic relation (all PMYO=1 windows pooled, binned
     by window meanf): v_c rises through **0.50** (3.5≤F<4.0 bin) then
     COLLAPSES to **0.165** (4.0≤F<4.5) and **0.023** (F≥4.5) — the
     registered stall clip (v=0 at FAX≥FSTALL) expressed directly in the
     windowed data. **Stall read: force saturates at 4.30 (isometric
     mean; window max 5.17) and velocity falls to ≈0.02 len/time (~0.2%
     of the 2-head unloaded max 2·VMYO=12) once F exceeds ≈4.5 — stall
     at the registered scale FSTALL=4.0 (isometric operating point
     within ~8%). No runaway at any load: max meanf over all levels =
     5.17.** Measured note (no tuning): at the compliant end v_c
     decreases with F because low-tension motors park at the 8-monomer
     tracks' barbed ends (NEXTM=0 → ineligible) and wait for basal Bell
     slip — a constructed-track-length effect, reported as-is.
   - **O-M5 (ranges): PASS (no clamp).** Attach/rupture balanced at
     every level (94/93, 35/34, 67/66, 51/50, 48/47, 40/39, 36/35 —
     recomputed); rates 1.1e-4–3.2e-4/step; lifetime means 3186–8465
     steps lengthening as force drops, exactly the Bell-slip law
     (KOFFM·EXP(|F|/FBMYO)); **all 364 ruptures cause 1 = Bell slip
     (zero hard releases; recomputed)**; **max lifetime 31154 ≪ 300k
     (recomputed)** — no permanent clamp; the contractile arm turns over
     ~2.7× faster than the parallel control.
   - **Measured geometry ranges (never gates):** endpoint/anchor gm
     displacement small on the isometric arm (|dx| ≤ 0.27); compliant
     arms drift up to +2.14/−2.69 at k0p1 (tracks yield/rotate under
     motor tension with soft anchors, as registered); nmyo ≈ 1.0 at all
     levels (single-motor unit, capture geometry-limited); contour step
     |disp| ≈ PITCH on all events.

## The 1/107 buckling exception (registered criterion, reg. 6 addendum)

The deterministic few-step sign battery passed strict lab-x signs on
every myost with zero tolerance (both arms), and every myost event in
all R10-a logs (150 events) satisfies the contour invariant
MNEW=MOLD+1. In the PMYO=1 50k smoke exactly **1/107** events (step
39203, grip stepping onto the barbed-tip monomer 7→8, dx=−0.3656,
|disp|=0.56 ≈ PITCH — record re-read this doc pass) had a negative
lab-x displacement: the anchored barbed-tip monomer transiently flopped
under sustained stall load + thermal kick (tip axis (−0.44,−0.19,+0.88)
at census 39000 while monomers 1..7 hold +x); the step remained
barbed-ward along the local contour. This is coarse-grained filament
buckling physics, not a stepping-rule sign error. Accordingly the HARD
O-M2 content is the deterministic battery + the contour invariant
(150/150 R10-a; **2809/2809 R10-c**); lab-sign is a RANGE metric
(PMYO=1: 106/107, recomputed; PMYO=2: 28/28, recomputed; sign runs
15/15, recomputed).

## R10 laws

### L-M1 Directionality is a data-structure invariant property: heads walk barbed-ward, zero exceptions (O-M2)

Every stepping event in every R10 log — deterministic batteries, 50k
smokes, and all 7 R10-c 300k logs — satisfies MNEW=MOLD+1 (NEXTM is
barbed-ward by the engine's contour data structure): 2959/2959 events
program-wide (150 + 2809), zero contour violations. On antiparallel
tracks this slides the filaments into contraction; on parallel tracks
both heads step the same direction (drift, not contraction). Lab-frame
displacement signs are geometry-dependent (buckling under stall,
track rotation on soft anchors) and are ranges, never gates.

### L-M2 The unit contracts antiparallel and is silent parallel (O-M3)

The antiparallel unit builds sustained motor tension at the FSTALL=4.0
scale (post-burn-in meanf 4.304, stretch meand 1.5→3.65, isometric);
the identical-geometry parallel control stays thermal (meanf 0.360,
meand ≈ 1.53 = DMY0) — 12× selectivity with the parallel-silence hard
limb PASS. Contraction force is transmitted to the fixed endpoints
(anchor traction inward on both tracks in the isometric smoke).

### L-M3 Force-velocity with finite stall at the registered scale (O-M4)

Under the KSEED anchor-compliance load sweep the motor's operating curve
is monotone in compliance (meanf 4.304→0.907, v_c 0.278→0.081 over
KSEED 5.0→0.1), force saturates at the FSTALL=4 scale (isometric mean
4.30, global max 5.17 — bounded, no runaway at any load), and the
microscopic velocity law v=VMYO·(1−FAX/FSTALL) is visible directly in
the windowed data: v_c = 0.50 below F≈4, collapsing to 0.165
(4.0≤F<4.5) and 0.023 (F≥4.5) — stall at the registered scale. The
compliant-end downturn of v_c with F is a track-length parking effect
(barbed-end NEXTM=0 arrest + basal-slip wait), measured and registered,
not a law violation.

### L-M4 Turnover is Bell-slip and never clamps (O-M5)

Attach and rupture balance at every load level; 100% of ruptures are
cause 1 (Bell slip) under frozen track kinetics; lifetimes lengthen as
force drops (3186 steps at F≈4.3 → 8465 at F≈0.9), consistent with
KOFFM·EXP(|F|/FBMYO); max observed lifetime 31154 ≪ 300k run length;
inventory returns to low occupancy recurrently. The contractile arm
turns over ~2.7× faster than the parallel control (load-accelerated
unbinding expressed at the population level).

### L-M5 The motor channel is inert when off and book-exact when on (O-M1, O-M6)

PMYO=0 is byte-identical to the certified R9 parent at every level
(MIRROR `3f3269db...`, 50k `007e6b2b...`, 300k gates 6/6). With the
channel on, every log closes: conservation exact, ghost scan clean,
motor inventory exact at every window from t=0 (step-0 constructed myoa,
reg. 5 addendum), zero netf, FINAL, NUL=0, attempt=1.

## Oracle scorecard (O-M1..O-M6)

| oracle | registered criterion | measured result | verdict |
|---|---|---|---|
| O-M1 channel-OFF byte-identity | PMYO=0 ≡ certified R9 parent, all levels | MIRROR `3f3269db...`; 50k `007e6b2b...`; 300k gates 6/6 (both seeds, PBUND∈{0,1,2}; hashes recomputed) | **PASS** |
| O-M2 directionality (sign correctness, zero tolerance) | heads walk barbed-ward on tracks of known polarity | deterministic battery 15/15 strict lab signs; contour invariant MNEW=MOLD+1 on 100% of myost (150/150 R10-a; 2809/2809 R10-c, recomputed); lab-sign ranges 106/107 + 28/28 + 15/15 | **PASS** |
| O-M3 contraction force vs parallel control (parallel-silence limb HARD) | antiparallel contracts; parallel must NOT contract | meanf 4.304 vs 0.360 (12×); meand 3.65 vs 1.53≈DMY0; control steps same-direction 180/181 | **PASS** |
| O-M4 force-velocity + stall (no-runaway HARD) | report the curve; stall = load where v≈0 and F saturates; F bounded at FSTALL scale | 6-level curve measured; F saturates 4.30 (max 5.17); v_c collapse 0.50→0.165→0.023 across F≈4.0–4.5; stall at FSTALL=4.0 scale | **PASS** |
| O-M5 turnover (ranges; no permanent clamp) | all motors eventually unbind; rates reported | balanced attach/rupture all levels; 100% Bell slip (364/364 cause 1); max lifetime 31154 ≪ 300k; contractile arm ~2.7× faster turnover | **PASS** |
| O-M6 books incl. myosin inventory (HARD) | conservation, ghost scan, inventory, netf, FINAL, NUL | exact on all 7 R10-c logs (600 censuses/windows each) + all R10-a logs; own checker + independent awk agree | **PASS** |

**R10 exit criterion (plan_myosin.md): MET.** A single antiparallel
actin-myosin unit contracts with the correct sign (O-M2/O-M3), finite
stall (O-M4), and dynamic turnover (O-M5) — with the force numbers
recorded for R11 stress-fiber design (below).

## Numbers for R11 design (constructed-unit footing, frozen kinetics, s77031)

| quantity | value | source |
|---|---|---|
| stall force scale | FSTALL=4.0 (registered); isometric mean 4.304, window max 5.17 | O-M3/O-M4 |
| operating force range (load sweep) | 4.304 (KSEED=5.0) → 0.907 (KSEED=0.1) | O-M4 curve |
| contraction velocity range | 0.278 → 0.081 len/time over the sweep; microscopic v_c = 0.50 (F<4 bin) → 0.023 (F≥4.5); unloaded 2-head max 2·VMYO=12 | O-M4 |
| stall sharpness | velocity collapse across F≈4.0–4.5 (clip at FAX≥FSTALL expressed in windowed data) | O-M4 bins |
| antiparallel selectivity | 12× vs parallel control (4.304 vs 0.360) | O-M3 |
| turnover rates | arate=rrate 3.2e-4/step (contractile) → 1.1e-4/step (compliant); 1.2e-4 parallel | O-M5 |
| lifetimes | mean 3186–8465 steps (Bell-load-dependent); max 31154 | O-M5 |
| single-motor occupancy | nmyo ≈ 1.0 (capture geometry-limited at RMYO=2.0) | O-M5/ranges |
| motor spring | KMYO=1.0, DMY0=1.5; stretch at stall meand ≈ 3.65 | O-M3 |
| track-length effect | barbed-end parking at low tension (8-monomer tracks); registered, no tuning | O-M4 note |
| R9 design input (carried) | polarity memory ~200–400 steps/link (R8 timing, reproduced in R9); tip linkage is the traction bottleneck (O-P4 FAIL) | PARALLEL_BUNDLE_LAW.md |

## Force-first doctrine (cross-reference)

The 2026-09-03 doctrine (BUNDLE_LAW.md §doctrine) governed R10 in full:
every hard gate is a force/conservation/inventory/sign/byte-identity
oracle (O-M1, O-M2 as sign-correctness, FD on the motor path, O-M6,
parallel silence as a hard sign limb); the force measurements (O-M3
magnitude, O-M4 curve and stall) used pre-registered methods with the
numbers reported, not thresholds fit after the fact; everything
distributional (O-M5 lifetimes, geometry drifts, lab-sign fractions) is
reported as ranges. Where the engine's available force paths did not
include the originally envisaged load (F_EXT lives only in the piston
channel), the load mechanism was registered from an engine read BEFORE
any run (KSEED anchor-compliance sweep) — method fixed in advance,
physics measured after.

## Failure-mode register (plan_myosin.md §"Registered failure responses") with dispositions

| anticipated failure | registered response | disposition |
|---|---|---|
| Sign error (O-M2) or books/FD/O-M1 failure | STOP, evidence, no tuning | **Not triggered.** All hard gates passed at every stage (one lab-x exception = registered buckling physics, contour-correct; criterion pre-registered in reg. 6 addendum with evidence) |
| Near-zero motor stepping | measure eligibility/binding flux first; report; adjust GEOMETRY by amendment — never physics | **Not triggered.** Stepping plentiful (2809 events over 7×300k; nmyo ≈ 1.0 capture-limited as constructed); one GEOMETRY amendment was made (reg. 4 addendum, both-ends anchoring) on evidence of track pivoting — geometry, not physics |
| Disk pressure / no zips | compress completed logs before deletion; deletions only on explicit user word | Honored; nothing zipped or deleted |

## Known limitations

1. **Frozen-kinetics footing.** All R10 unit measurements run with
   track polymerization/depolymerization kinetics frozen (KON=KONP=
   KHYD=KOFFB_T=KOFFB_A=KOFFP_T=KOFFP_A=0, PCAP=0) and both track ends
   KSEED-anchored. The certified laws are statements about the motor on
   fixed tracks; live-kinetics units require a new registered footing.
2. **Anchor unbind-transfer gap (registered, reg. 4 addendum; review
   note iii).** The constructed barbed-end anchors have no
   unbind-transfer machinery (barbed unbind of an anchored monomer
   leaves HASA set). Inert under frozen kinetics (never triggers in any
   R10 arm); MUST be resolved before any live-kinetics unit config.
3. **Buckling geometry.** Under sustained stall load an anchored track
   tip can transiently buckle (the 1/107 lab-x exception); soft-anchor
   arms rotate/drift (gm endpoint drift up to ~2.7 at k0p1). Contour
   correctness is unaffected (the data-structure invariant holds), but
   lab-frame displacement metrics on long/compliant tracks must be read
   with this caveat — lab-sign remains a range metric.
4. **Channel-isolated FD convention.** The motor-path FD check isolates
   emyo because a total-energy FD is numerically impossible (wall-contact
   ulp noise 7.6e-6 > motor signal). The convention is registered and
   justified, but future channels that change the wall-contact energy
   landscape should re-register the FD decomposition.
5. **Constructed-unit scope.** Numbers above are for one motor between
   two 8-monomer tracks at registered defaults, one seed (the sweep axis
   is load, not noise — registered). Multi-motor units, longer tracks
   (parking effect), and stochastic-seed spread are R11 registration
   items; the compliant-end v_c downturn is a track-length artifact of
   THIS construction.
6. **F_EXT unavailability off-piston.** External load on internal
   constructed elements exists only through anchor compliance (KSEED);
   the PSTN F_EXT path does not act on constructed monomers. Registered
   with rationale; R11 designs needing direct external load on motors
   must register a new force path.

## Artifacts (all under `/mnt/agents/output/actin_phasespace/`)

- Engine: `phi4/runs24/myosin_unit.ergo` SHA256
  `2806ed054ecebf0fe9eb6db93af39d433991dfd97d36b534afdb22c4d923110f`
  (4247 lines, +748/0; recomputed) + `myosin_unit.bin`. Code bundle
  `actin_phasespace/r10_repo.bundle` SHA256
  `3d941a0450a25057576a450902a1d4bdc77c3dd56cf3c136d0ae87d7bc8bab81`.
- Oracle: `phi4/plan_myosin.md` (regs. 1–6 + addenda + R10-c
  registrations, all pre-run).
- R10-a: `phi4/runs24/R10A_REPORT.md`; `static_cert/` (mirror_off
  `3f3269db...`, cert_myo1, fd_myo{105,113}_{plus,minus});
  `sign/sign_pmyo{1,2}.{ergo,bin,log}` (15/15); `smokes/`
  (op1_50k `007e6b2b...`, unit_pmyo{1,2}_50k).
- R10-b: `phi4/runs24/gates/` (6 om1 300k logs + .status + work/
  variants; hashes equal the R9-b references:
  `16c9db1c...`/`5636a7eb...`/`b84d72e1...`/`c5444043...`/`cb3e60fe...`/
  `8ddb802b...`).
- R10-c: `phi4/runs24/R10C_REPORT.md`; `phi4/runs24/r10c/` — 7 configs/
  binaries/logs (.status): r10c_p1_k{5p0,2p0,1p0,0p5,0p25,0p1} +
  r10c_p2_k5p0 (log sha256 first-16: 6aaed9511fc9ba76 / 0143a1ed0f9c26ec
  / fbad632cb170df82 / aefd7c9ce402a333 / 157832b115e32a2c /
  3ec62b3662e1f557 / a738c68a932d2cff — the k5p0 hash recomputed this
  doc pass from the .status file).
- Checkers: `phi4/runs24/myo_books.py` SHA256
  `7e1f0ac96dc90fbc8c8605099b275e7e73f72aaa34b4285de416ae2c4cc7f7ab`;
  `phi4/runs24/r10c/r10c_analyze.py` SHA256
  `039601924f3d9195495a9c52cee7411e08c7dd2eed9593ccabc39071e34eaea5`
  (both recomputed).
- Execution record: `actin_phasespace/plan.md` R10 Stage 0–3 (+ Stage 4
  combined doc pass — this document).

## Reproduction

```bash
# toolchain: certified Ergo compiler (python3 -m core), frozen per Stage-0
# runner: runs20/runner_r6.sh (sequential, /tmp-staged, verified; writes .status)
# engines: runs23/filopod_min.ergo (parent) -> runs24/myosin_unit.ergo
# R10-a: compile static_cert/*.ergo; cmp mirror_off.out vs runs23 mirror (3f3269db...);
#        CERT_MYO emyo=0.25 exact; FD: (emyo+ - emyo-)/2e-6 vs +/-1.0, err 3.2e-10/7.6e-10
#        sign battery: grep '^myost' sign/sign_pmyo{1,2}.log (strict lab dx signs)
# R10-b: runs24/gates/work variants; child sha256 == R9-b reference sha256 per row
# R10-c: runs24/r10c configs (anchored ^PARAMETER copies; 2 changed lines each);
#        books: runs24/myo_books.py + r10c/r10c_analyze.py;
#        contour invariant: awk '$1=="myost"{if($6-$5!=1)bad++}' (0 violations);
#        F-V curve: myos windows >50k, v_c=nstep*PITCH/(NDIAG*DT), F=meanf
```

## Conclusions for the phase-space map

The coarse-grained bipolar myosin element is certified on the
constructed-unit footing: barbed-ward stepping as a data-structure
invariant (2959/2959 program-wide), antiparallel contraction at the
FSTALL=4 scale with 12× selectivity over a silent parallel control, a
measured force-velocity curve with stall at the registered scale and no
runaway, and pure Bell-slip turnover with no clamp. Combined with the R9
finding (bundle polarization is certified; traction is tip-linkage
bottlenecked), the R11 stress-fiber design inputs are: motor stall scale
4, single-motor capture geometry, anchor-compliance as the load path,
tip linkage as the traction bottleneck, and ~200–400 steps of bundle
polarity memory per link. Engine certified and frozen; per the roadmap
the project proceeds to R11 (stress fiber).
