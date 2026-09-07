# STRESS_FIBER_LAW.md — φ4.13 stress fiber (stress_fiber, R11) certification and the anchor-competition finding

Certified: 2026-09-04 (R11-a build/statics/FD/sign battery + micro-smokes
+ combined review/verify + merge; R11-b O-S1 gates; R11-c 1M fiber
measurements). Doc pass 2026-09-04. **All hard gates PASS (O-S1 7/7
byte-identical, O-S7 books 4/4, FD 2.8e-10/1.5e-9, sign battery 80/80
frozen-kinetics); the R11 exit criterion is MET with one registered
measured qualification** — the fiber maintains stationary contractile
tension and transmits inward traction to both substrate attachments, and
the unperturbed steady state is rupture-dominated **anchor competition**:
one dominant anchor carries the load while the subordinate anchor's duty
is sporadic-to-~zero (a physics finding, not a bug; reported as-is per
the registered failure response — no adhesion tuning).

Engine lineage: pop_fpt.ergo (φ4) → brush_adh (R6 adhesion) → brush_xlk
(R7 crosslinks) → bundle_pol (R8 polarity gate) → filopod_min (R9,
closed with the O-P4 tip-linkage finding) → myosin_unit (R10, certified;
L-M1..L-M5) → **stress_fiber** (R11: PSF constructed-fiber + SF
slip-bond anchor channel, PSEV sever machinery) — the **7th certified
engine** in one additive lineage, each channel-OFF byte-identical to its
parent. Final source `phi4/runs25/stress_fiber.ergo` (5058 lines,
**+811/−0** vs parent — verified by direct diff this doc pass: 811
added, 0 removed/changed, 21 hunks), SHA256
`3a6cc866b869de69f09683f3cd61a0c93dba89b8136ea5a05ffef39ef6faed68`
(recomputed this doc pass), merge commit `049ff28` in the live repo
(durable code bundle `actin_phasespace/r11_repo.bundle`). Parent:
certified `phi4/runs24/myosin_unit.ergo` SHA256
`2806ed054ecebf0fe9eb6db93af39d433991dfd97d36b534afdb22c4d923110f`,
re-verified untouched after build and after every stage. Oracle:
`phi4/plan_stress.md` (O-S1..O-S7 + doctrine; builder registrations
1–12, builder errata 1–4, verifier errata 5–8, R11-c registrations +
run record — all appended BEFORE the corresponding builds/runs). The R9
PCLU/PTIPA/PTIP channels stay OFF in all R11 configs (registered user
priority). Runs under `phi4/runs25/` (static_cert/, sign/, smokes/,
gates/, r11c/). No zips; no certified file modified after certification.
New RNG slot block **7010–7073** (SF adhesion attach `7010+2(F−1)`,
rupture `7011+2(F−1)`), disjoint from the registered max 7001 (R10
myosin block 6970–7001).

## The question

Can actin bundles, crosslinkers, adhesions, and myosin assemble into a
stable contractile stress fiber anchored to the substrate at both ends?

**R11 answer: yes, with a measured qualification — a live-kinetics
alternating-polarity fiber, anchored at both barbed ends by certified
R6-law slip bonds, maintains stationary positive midplane tension in all
4 arms (means 17.26/10.31/10.43/13.25 over ~1M steps; 93.6–98.3% of
post-assembly windows positive) and bears inward traction at both
substrate planes (both-ends simultaneous inward traction demonstrated on
main_s77031: end0 +0.490 at 75.5% bonded duty, end1 −0.254 at 16.1%,
bond force scale fmag ≈ 2.0 both ends). The qualification: in the
unperturbed steady state, rupture-dominated slip-bond competition
concentrates the load on ONE anchor (seed selects the side: 77031→left,
84950→right); severed fibers re-anchor BOTH ends at 84–94% duty and
repair.**

| stage | arm | purpose | outcome |
|-------|-----|---------|---------|
| R11-a | build + MIRROR static/FD cert + constructed sign battery + O-S1 50k + micro-smokes (incl. sever arm) + combined review/verify + merge | PSF/PSEV channels on certified R10 parent | PASS all; CERTIFICATION VALID, GO; 4 verifier errata registered |
| R11-b | O-S1 gates PSF=0/PSEV=0 × PBUND∈{0,1,2} × seeds {77031,84950}, 300k, + PMYO=1 50k extension row | new channels OFF ≡ R10 parent, byte-identical | PASS 7/7 |
| R11-c | 4×1M fiber runs: mains (PSEV=0) + sever arms (PSEV=1, SEVSTEP=500), seeds {77031,84950}, live kinetics | O-S2..O-S7 measurements | hard gates PASS; exit criterion MET with anchor-competition qualification |

## Doctrine (binding, quoted from plan_stress.md)

- **Hard gates (failure = bug = STOP with evidence):** O-S1 byte-identity
  (each new channel OFF ≡ R10 parent); FD < 1e-8 on any new force path;
  sign correctness of motor stepping (contour invariant) and of
  antiparallel gating (zero tolerance); O-S7 books (all inventories incl.
  myosin conserved, ghost scan zero, max|netf|=0, no bookkeeping force
  discontinuity).
- **O-S3 contractility is the headline FORCE measurement:** both endpoint
  adhesion groups bear inward traction; fiber tension positive and
  stationary. Method pre-registered by the builder (traction =
  adhs-convention windowed substrate force per end; tension =
  cross-section force sum through the fiber midplane); numbers reported
  per seed.
- **Ranges (never gates):** O-S2 assembly time from the registered
  initial condition; O-S4 polarity organization (antiparallel enrichment
  around myosin; parallel regions identified); O-S5 homeostasis
  (length/tension boundedness under turnover — reported as distributions;
  no runaway is the force-domain check); O-S6 perturbation outcome
  (registered sever/stretch; outcome classified: repaired /
  failed-measurable, with the numbers).
- Registered failure responses carried in full: hard-gate failure ⇒
  STOP, evidence, no tuning; rupture-dominated anchors ⇒ report
  distributions as-is (the R9 lesson — do not strengthen adhesion to hit
  a number); no zips; deletions only on user word.

## Mechanism as certified

- **Live-kinetics anchor footing (reg. 1).** The fiber-end anchors ARE
  adhesion slip bonds — the R10 constructed-barbed-end KSEED anchors
  (and their frozen-kinetics unbind-transfer gap, R10 known limitation 2)
  are replaced wholesale: INIT_SF sets NO HASA anchors on fiber monomers.
  Anchoring = new SF adhesion channel implementing the certified R6
  slip-bond law **verbatim** (spring F=2·KADH·(A−R) to a fixed on-plane
  target, E=KADH·d², slip P=KOFFA·DT·EXP(AFD/FBA) on the CURRENT
  distance (ADHKIN convention), hard release d>SMAXA, one bond per
  filament tracking the MONOMER (shaft grip), cause 3 wired at both
  monomer-unbind sites, cause 4 in DISSOLVE), with the same R6 parameter
  set (KADH/KONA/KOFFA/FBA/SMAXA/RADH — no new physics parameters).
  Load-dependent unbind and re-attachment are the certified R6 behavior.
- **End geometry (reg. 2 — registered deviation: barbed-end grips, NOT
  pointed ends).** Certified R10 mechanics: the bipolar motor walks
  barbed-ward on both tracks; between antiparallel filaments this slides
  each filament pointed-end-first toward the fiber center, i.e.
  contraction = barbed ends converge. Anchors at the barbed ends
  therefore bear INWARD traction; pointed-end grips would bear OUTWARD
  (extensile) traction and cannot produce the O-S3 headline. Registered
  sarcomere-like geometry: barbed ends OUTWARD at the two substrate
  planes (XADH left, XSF2=9.0 right), pointed ends inward; the SF bond
  grips the barbed-end head bead B=2·FILBARB(F)−1, zone-scoped
  (attach-eligible when unattached and PX(B) ≤ XADH+RADH, end group 0,
  or PX(B) ≥ XSF2−RADH, end group 1). Inward-traction sign criterion
  (adhs convention, traction = −F on substrate): left healthy contraction
  ⇒ trx > 0; right ⇒ trx < 0.
- **Constructed fiber (reg. 3; deterministic INIT_SF, ZERO new RNG
  draws — gas monomers from the SAME INIT_DYN hash stream, RCNT=1000).**
  NHF=3 filaments per half, 6 total (slots 1..6), LSF=9 monomers each
  (contour 5.4). Ring cross-section radius RSF=1.5 about (6,6), halves
  alternating: every adjacent ring pair is an antiparallel L–R pair at
  distance exactly 1.5 = DX0 = DMY0; same-half (parallel) pairs at
  1.5·√3 ≈ 2.598 > RMYO/RXLK = 2.0 (geometrically excluded from
  motor/link candidacy). Left half axis −x (barbed toward the left
  plane), right half +x. Overlap region x ∈ [3.45, 7.55] ≈ 4.1 about
  the midplane XSFM=5.5.
- **Myosin ensemble (reg. 4 + errata 1/5).** PMYO=1; attach candidacy =
  the certified R10 MYOKIN all-pairs scan UNCHANGED; on the constructed
  fiber the only eligible pairs are the 6 antiparallel L–R ring
  neighbors. Pool MAXMYO=8 (6 ≤ 8, no raise — registered bound check).
  3 motors pre-bound on pairs (1,4),(2,5),(3,6) with step-0 myoa records
  (inventory exact from t=0); the other 3 eligible pairs attach
  dynamically. **Erratum 5 (binding correction to erratum 1):** the
  as-built left-half grips are monomers (6,15,24) at head-x = 4.30, NOT
  5.5; constructed grip distances 1.9206–1.9216 (gm-derived), so the 3
  pre-bound motors start stretched **0.42 (≈0.84 units contractile
  preload each, ~2.5 total, SAME sign as contraction)** — no gate break,
  but "exact rest" is false and ALL tension numbers below carry this
  preload note. **Record-accuracy defect (registered):** the step-0 myoa
  records print the hardcoded RSF constant 1.500000, not the true 1.92 —
  all R11-c analysis uses gm-derived distances for constructed motors,
  never the myoa field.
- **Crosslinks (reg. 5).** PXL=1 with the R8 gate in mode PBUND=2
  (antiparallel-selective): the load-bearing overlap is antiparallel and
  contractility needs it crosslinked. Same-half parallel pairs are both
  gate-rejected and geometrically out of capture range, so crosslinks
  form ONLY between halves (with the registered buckled-local-axis
  exception — see O-S4). XLMAXF=2 per filament, saturated by
  construction; MAXXL=24 ≥ 6.
- **SF adhesion channel mechanics (reg. 6).** Per-filament bond arrays
  (R6 ADH* pattern); SFAKIN draws UAT (slot 7010+2(F−1)) and URP
  (7011+2(F−1)) unconditionally per active filament per step, ascending
  F, after MYOKIN. Attach Bernoulli P=MIN(1,KONA·DT) in the reg. 2
  zones; rupture hard-release d>SMAXA (cause 2) else slip (cause 1).
  End grouping SFAE∈{0,1} assigned at attach; per-end accumulators.
  Constructed bonds emitted as step-0 sfa events (inventory exact from
  t=0). Records: `sfa` (attach), `sfr` (rupture, adhr convention),
  `sfas STEP E nb trx try trz fmag arate rrate` (windowed per-end census,
  TWO lines per NDIAG window, adhs convention: trx.. = Σ(−F)/NDIAG
  substrate traction, fmag = mean |F| per bond-step).
- **Instrumentation (reg. 7; records-only, zero RNG, no force, no
  feedback).** Windowed `fib STEP nfil npoly tipxL tipxR flen ten nmyo
  nxl` at NDIAG. **Registered tension definition:** midplane
  cross-section force sum at XSFM=5.5 — every backbone junction spring,
  crosslink, or motor spring straddling the midplane contributes the
  signed x-force it exerts on the right-side bead, negated (tension > 0
  = contractile); pure accumulation under PSF=1 AND MIRROR=0 guards,
  windowed mean /NDIAG. WCA contacts excluded; adhesion bonds never
  straddle the midplane by construction.
- **Perturbation (reg. 8).** PSEV=0 inert default. PSEV=1: at
  STEP=SEVSTEP, deterministic midplane sever of every filament whose
  contour straddles XSFM; the barbed-side remnant keeps its slot (and
  its SF/R6 bonds), the pointed-side remnant becomes a new filament in
  the first free slot (ascending, deterministic). Crosslinks/motors
  touching pointed-remnant monomers release with **cause 5 =
  sever-induced release** (new registered cause code, PSEV=1 runs only);
  an R6 ADH bond whose gripped monomer moves to the remnant TRANSFERS to
  the new slot (monomer-grip convention, no event); SF bonds always stay
  on the kept barbed side. `sev` record per cut. Zero RNG.
  REBUILD_BONDS after.
- **Configs (regs. 9–12).** MIRROR static cert cert_sf1 (R10 cert stack
  + PSF=1: filaments 14/15 at exact rest geometry, constructed SF bonds
  d=0.5 pure-x, F = ∓2.0 x̂ on beads 125/133, esfa=1.0; channel-isolated
  FD on esfa, tolerance 1e-8, ulp-justified per the R10 convention).
  Sign battery (reg. 10): PSF=1, VMYO=120, KOFFM=0, SMAXM=100, KOFFA=0,
  SMAXA=100, frozen kinetics, PXL=0, PADH=0, 2000 steps — hard criteria
  = contour invariant MNEW=MOLD+1 on 100% of myost + strict lab signs on
  the deterministic constructed battery. Micro-smoke (reg. 11): PSF=1,
  PXL=1, PBUND=2, PMYO=1, PADH=1, PBR=0, PSTN=0, DIMERS=0, PCAP=1, live
  certified kinetics, 50k + PSEV=1 sever arm. O-S1 at build time
  (reg. 12): the R10 O-P1 config on the new engine ⇒ byte-identical to
  `runs23/smokes/op1_50k.log` (sha256 007e6b2b…faa0).
- **Builder errata 2–4 (registered post-build, additive):** myor cause 6
  = construction overwrite (INIT_MYO's unit motor released via the
  certified MYO_REL path before INIT_SF overwrites state — motor
  inventory record-exact; verified cum(myoa)−cum(myor)=nmyo at every
  myos window in all R11 runs); the INIT_CERT R11 cert block is fully
  unrolled with literal constants (see the UB landmine caution below);
  INIT_SF gas loop = verbatim bounded INIT_MYO pattern.

## PERMANENT CAUTION — the UB landmine (verifier erratum 8, standing rule for all future rungs)

All parent init routines carry a **pre-existing latent out-of-bounds
write**: STATE(I) is written over I=1..NB=800 while STATE has NMAX=400
entries. It is present in ALL certified parents, is empirically harmless
to date (every byte-identity chain holds, including the R11 mirror_off
3f3269db…), and is verifier-confirmed **structurally confined to the
MIRROR=1 static-cert path** (single OOB site; cannot reach dynamics). But
gcc -O3 -march=x86-64-v3 EXPLOITED the UB to miscompile the first
(loop+derived-arithmetic) version of the R11 INIT_CERT block (PX(134)
computed from a stale zero; correct at -O0). Resolution under additive
discipline: the cert block is unrolled with literal constants (immune);
INIT_SF uses bounded loops only. **STANDING RULE: NO non-literal code
may be added to INIT_CERT in any future rung until the parent UB is
fixed; fixing the parent requires a new parent rung (out of R11 scope).
Register this rule in every rung doc.**

## Certification chain

1. **Static/FD certification passed (R11-a)** (`runs25/static_cert/`,
   `runs25/sign/`, `runs25/smokes/`). Additive-only proof: diff
   parent↔engine = 811 added, 0 removed/changed (recomputed this doc
   pass). **MIRROR static cert:** mirror_off byte-identical to the R10/R9
   mirror (both SHA256 `3f3269db...`, recomputed); cert_sf1 parent
   CFG(118)/FRC(118)/CERT/CERT_ADH/CERT_XL/CERT_TIP/CERT_MYO lines
   byte-identical to `runs24/static_cert/cert_myo1.out` (recomputed by
   line extraction and comparison — pure zero additions); new lines
   SFAC×2 + `CERT_SFA esfa` = 1.00000000000000000e+00 **exact**;
   constructed-bond forces on beads 125/133 = −2.0/+2.0 x̂ exact.
   **FD (central, h=1e-6) on the channel-isolated esfa:** bead 125
   |FD−(+2.0)| = **2.8e-10**, bead 133 |FD−(−2.0)| = **1.5e-9** — both
   < 1e-8 (recomputed from the four fd_sf*.out CERT_SFA lines this doc
   pass: slopes +2.0000000003 / −1.99999999999). **Sign battery
   (reg. 10, hard): 80/80** — recomputed this doc pass from
   `sign/sign_sf1.log`: 80/80 myost events satisfy the contour invariant
   MNEW=MOLD+1 AND carry the strict constructed-geometry lab sign
   (left-half heads dx<0: 38/38; right-half heads dx>0: 42/42 — heads
   walk APART, contractile loading). **O-S1 50k (reg. 12):**
   `smokes/op1_50k.log` byte-identical to the certified R7–R10 reference
   SHA256 `007e6b2b...faa0` (recomputed — one hash now covers R7 through
   R11 channel-OFF 50k equivalence). **Micro-smokes (50k, reg. 11
   config, live kinetics):** books PASS both arms (`sf_books.py`):
   conservation 400 every census, ghost scan, motor inventory exact from
   t=0 (incl. cause-6 construction overwrite), XL/R6-ADH/SF per-end
   inventories, max|netf|=0.000e+00, FINAL, NUL=0; sever arm (SEVSTEP=
   25000) cut exactly 1 filament (sev 25000 F6→G7, remnant lengths 58/4
   exact — recomputed) with ZERO cause-5 releases (the erratum-7 coverage
   gap, carried to R11-c). **O-S3 signature present in the smoke**
   (ranges, recomputed this doc pass): step-1 traction end0 +6.003 /
   end1 −6.001 (3 constructed bonds × 2.0 exact); window-1 sfas
   +2.88/−1.07; tension positive in 94/100 windows, second-half mean
   9.60, max 58.59; fiber contracts flen 8.61→≈0 by ~4k; anchors
   rupture-dominated as registered (sfr 241: 239 slip + 2 cause-3,
   median lifetime 385 steps; erratum-6 wording correction carried: 31
   post-t=0 right-end attaches, last at step 9940, right end bare for
   the final 40,060 steps ≈ 80% of the 50k run — recomputed; the
   erratum's "~39.9k" is rounding).
2. **Combined review + verify: CERTIFICATION VALID, GO for merge**;
   7/7 byte-identical fresh recompiles. Verifier errata 5–8 registered
   (carried in full above: the 0.42/motor preload + myoa record-accuracy
   defect; the right-end-reattach wording correction; the cause-5
   coverage gap; the UB standing rule). Merge commit `049ff28` (.git
   restored from r10_repo.bundle after the 4th container wipe; durable
   `actin_phasespace/r11_repo.bundle` refreshed).
3. **O-S1 gates passed (R11-b)** (`runs25/gates/`). **7/7
   byte-identical:** 6-row matrix (PSF=0/PSEV=0 × PBUND∈{0,1,2} × seeds
   {77031,84950}, 300k) vs the runs24/gates om1 references (hashes
   re-verified pre-use, not rerun): child sha256s equal the references
   exactly — `16c9db1c...`/`5636a7eb...`/`b84d72e1...`/`c5444043...`/
   `cb3e60fe...`/`8ddb802b...` (all recomputed this doc pass: each
   runs25 os1 log is byte-for-byte its runs24 om1 reference). Plus the
   PMYO=1 extension row `os1x_pmyo1_50k.log` SHA256 `0a4ba14c...`
   byte-identical to the R10-a smoke reference
   `runs24/smokes/unit_pmyo1_50k.log` (recomputed; no 300k PMYO=1
   reference exists — registered). All OK attempt=1, FINAL×2, NUL=0.
   Engine 3a6cc866… untouched before/after.
4. **R11-c fiber measurements** (`runs25/r11c/`; registrations appended
   to plan_stress.md BEFORE any 1M run; engine hash re-verified before
   and after; **budget 4/6 used, both registered reserve slots NOT
   spent** — reserve decision registered). Run matrix: main_s77031 /
   main_s84950 (PSEV=0) and sev_s77031 / sev_s84950 (PSEV=1, SEVSTEP=500
   — registered justification: step 500 is simultaneously post-assembly
   by the O-S2(a) criterion, maximally loaded (windowed tension 37.7 =
   smoke-run maximum, incl. the erratum-5 preload), and the ONLY epoch
   where the sever cuts through live link/motor density: 6/6 filaments
   straddle at 500 vs 0/6 by 1500). All runs: reg. 11 config, anchored
   `^PARAMETER`-only copies (verified this doc pass: mains differ from
   the certified engine in exactly 9 parameter lines; sever arms add
   PSEV=1/SEVSTEP=500 and the seed line; the certified file untouched),
   1M steps, NDIAG=500, XLNF=0, live certified kinetics. All OK
   attempt=1, NUL=0, FINAL present. Log SHA256 (recomputed this doc
   pass, match the registered run record exactly):
   `main_s77031 e72842a9...e729e8` (57,934,755 B),
   `main_s84950 e5b2b226...1abce` (57,689,747 B),
   `sev_s77031 f0a6e71e...83afa` (59,149,092 B),
   `sev_s84950 8cfd9240...66e38` (58,791,632 B).
   **Determinism chains (recomputed this doc pass):** main_s77031.log is
   byte-identical to `smokes/sf_50k.log` through step 50000 (common
   prefix 2,962,005 B; the smoke's only extra content is its 48-line
   terminal FINAL/POPSTAT/NFILH block); each sev arm is byte-identical
   to its main arm through step 499 (PSEV=1 inert until SEVSTEP, sev
   records at exactly 500).
   - **O-S7 books (HARD): PASS on all 4 logs.** 2000 censuses each;
     conservation 400 exact (independently spot-recomputed this doc
     pass: 2000/2000 censuses nbound+nfree+ndim=400 on main_s77031);
     ghost scan zero; motor inventory incl. causes 1–6 exact at every
     myos window; XL inventory causes 1–5; R6-ADH inventory; SF per-end
     inventories; fib↔fil census cross-check exact; **max|netf| =
     0.000e+00 every window** (independently re-derived this doc pass
     over all 4000 myos+xlks census records per log × 4 logs); nfil
     continuity (no big jumps); FINAL, NUL=0; sever checks (sev only at
     SEVSTEP, remnant slots previously inactive, post-sev lengths).
     Analyzer `r11c/r11c_analyze.py` (SEVSTEP-parameterized re-derivation
     of `sf_books.py` + reg-8 R6-transfer re-key) cross-validated against
     sf_books.py on the smoke (identical counts, PASS) and against
     independent awk re-derivations on all 4 logs. bpol gate spot-check:
     0 violations on 9000+ PBUND=2 accepts (cos ≤ −0.5, printed 6 dp).
   - **O-S3 (headline force; post-assembly ≥4000; erratum-5 preload
     noted; gm-derived distances):**

     | arm | end0 bonded% | end0 trx (bonded) | end1 bonded% | end1 trx (bonded) | fmag both ends |
     |-----|-------------:|------------------:|-------------:|------------------:|---------------|
     | main_s77031 | 75.5% (1504/1993) | **+0.490** inward | 16.1% (321/1993) | **−0.254** inward | 2.028 / 2.060 |
     | main_s84950 | 11.7% (234/1993) | −0.056 (~0 mixed) | 98.9% (1972/1993) | **−0.271** inward | 2.019 / 2.060 |
     | sev_s77031 | 90.2% (1798/1993) | +0.364 inward | 93.7% (1868/1993) | +0.011 (~0) | 2.033 / 2.045 |
     | sev_s84950 | 84.8% (1690/1993) | +0.163 inward | 86.2% (1718/1993) | +0.046 (~0) | 2.038 / 2.035 |

     (main_s77031 column independently recomputed this doc pass from the
     sfas records — exact match: 1504/1993=75.5%, trx +0.490/med +0.555;
     321/1993=16.1%, trx −0.254/med −0.498; fmag 2.028/2.060.) Signs per
     reg. 2: left healthy trx>0, right healthy trx<0 — main_s77031 shows
     BOTH simultaneously; main_s84950's dominant end is the RIGHT (trx
     −0.271 < 0, correct sign); sever-arm subordinate ends carry ~zero
     mixed traction at high duty (re-anchored but load-shared).
     **Fiber tension (fib ten) positive and stationary in ALL 4 arms**
     (main_s77031 column recomputed exactly): means
     17.261/10.307/10.427/13.249, medians 14.620/8.890/8.506/10.626,
     windows>0 fractions 1960/1993 (98.3%), 1880/1993 (94.3%),
     1865/1993 (93.6%), 1909/1993 (95.8%); minima −2.345/−2.121/
     −3.413/−3.502 (transient excursions); first-half vs second-half
     means within spread (17.31/17.22; 11.05/9.57; 9.39/11.46;
     15.37/11.13) — stationary.
   - **O-S2 (ranges):** (a) bond-assembly latency = **500** (window 1)
     on all 4 arms — the honest constructed-fiber result (window-1 sfas
     on main_s77031 recomputed: end0 nb=3 trx +2.88; end1 event-duty
     attach/rupture 0.006/0.012, fmag 2.88; fib ten 37.66 > 0). (b)
     contractile equilibration (flen<1.0 for ≥3 consecutive windows):
     **3500 / 8500** (mains), **85500 / 39500** (post-sever).
   - **O-S4 (ranges):** antiparallel link density enriched INSIDE the
     myosin region in all 4 logs (links/unit-x, in vs out:
     0.799/0.696, 0.892/0.747, 0.781/0.423, 0.883/0.590); parallel
     regions = same-half pairs, geometrically link-free by construction
     EXCEPT the buckled-local-axis accepts: 1236/1599/659/890 same-half
     links accepted program-wide (cumulative xlka fractions
     38.8%/39.7%/9.5%/16.0% — recomputed this doc pass; see the
     provenance note on plan.md's "20–40%" wording). Every accept is
     gate-proven by its bpol record (cos ≤ −0.5; 0 violations) — a
     measured finding (local-axis buckling makes same-half pairs
     antiparallel by the certified gate), not a gate violation.
   - **O-S5 (ranges):** homeostasis holds. flen bounded (mains:
     [−3.088,2.272] mean −0.129; [−3.151,3.324] mean −0.002; post-sever
     wider, [−6.058,7.576]/[−4.319,6.283], remnant growth included);
     tension bounded, no monotone drift (above); turnover per 1k steps
     (post-assembly): myosin 1.14–1.18, crosslinks 3.18–6.96, SF
     adhesion 4.36–9.87; nbound 328.9–343.1 bounded (no runaway
     polymerization); force-domain no-runaway check: max|netf|=0 and
     tension within the observed envelope (global max 94.406 transient,
     main_s77031).
   - **O-S6 (registered classification): both sever arms REPAIRED.**
     sev_s77031: 6/6 filaments cut at step 500 (sev records recomputed
     this doc pass), **cause-5 coverage = 3 (myor×1 via MYO_MONDIE +
     xlkr×2 via XL_MONDIE, all lifetime/endpoint-exact in books —
     recomputed from the event records) — erratum-7 program-level
     requirement MET**; 1 reg-8 R6 bond transfer (no event, re-keyed to
     remnant slot 10, lifetime-exact). Tension: 37.686 pre-sever → 70.55
     spike (fib window 1000) → ~13 sustained; sustained >0 (≥10 windows)
     resumes at step 1000; both ends re-bond from step 1000 at 90.2%/93.7%
     duty — **the severed ensemble anchors BOTH ends better than its
     main arm**; all 6 remnants persist and grow (e.g. G10: 5→57
     monomers by step 1M). sev_s84950: 4/6 filaments cut (F2/F5 did not
     straddle), **cause-5 = 0 — per-arm registered target (≥2) MISSED
     with the registered geometry reason** (reconstruction from
     main_s84950.log: this seed's motor heads had already walked off the
     midplane by step 500 — left-half heads x≤3.5, right-half x≥6.2 —
     and only 2 crosslinks were live, both grips on the kept barbed
     sides, nearest grip x=5.57 vs cut ~5.5); tension 54.26 pre-sever →
     dip to 2.34 → ~13 sustained, sustained >0 resumes at step 1000;
     ends re-bond at 84.8%/86.2% duty; remnants persist (G10: 5→92
     monomers). Classification REPAIRED on the registered criteria. The
     reserve slots were NOT spent: a non-census-aligned SEVSTEP would
     evade the census-anchored sever books checks, weakening O-S7 —
     registered trade decision.

## R11 laws

### L-S1 A live-kinetics anchored fiber holds stationary contractile tension under full turnover (O-S3/O-S5)

With track kinetics, motor kinetics, crosslink kinetics, and anchor
slip-bonds ALL live, the fiber's midplane tension is positive and
stationary over 1M steps in 4/4 arms (means 10.31–17.26; 93.6–98.3% of
post-assembly windows positive; first/second-half means within spread),
while every component turns over (per 1k steps: myosin ~1.2, crosslinks
3.2–7.0, SF anchors 4.4–9.9) and inventories stay bounded (nbound
329–343; max|netf|=0). Contractile tension here is a homeostatic
steady-state property of the turning-over ensemble, not of any static
construction. (All tension numbers carry the registered erratum-5
constructed preload: 0.42/motor stretch, ~2.5 units total at 3 motors,
same sign as contraction.)

### L-S2 Both-ends slip-bond traction is inward at the fmag≈2.0 bond-force scale (O-S3)

The certified R6 slip-bond law, instanced at the two fiber barbed ends
(reg. 2 registered deviation — pointed-end grips provably extensile),
transmits INWARD traction to both substrate planes with the correct
signs (left trx>0, right trx<0): demonstrated simultaneously on
main_s77031 (end0 +0.490 at 75.5% duty; end1 −0.254 at 16.1% duty) and
per-end on every arm. The per-bond force scale while bonded is fmag ≈
2.0 at all ends of all arms (2.019–2.060) — traction magnitude is set by
bond COUNT (duty × nb), not by per-bond force; windowed traction is
duty-limited (see L-S3).

### L-S3 Rupture-dominated anchor competition: the steady state concentrates load on ONE anchor (measured qualification)

In the unperturbed steady state the two ends do not share the load
symmetrically: one anchor dominates and the subordinate anchor's bonded
duty/traction is sporadic-to-~zero. The seed picks the side: 77031 →
left dominant (75.5% vs 16.1%), 84950 → right dominant (98.9% vs 11.7%,
subordinate mean −0.056 ≈ 0 mixed-sign). Anchors are rupture-dominated
as registered (smoke: 239/241 slip ruptures, median lifetime 385 steps;
slip P=KOFFA·DT·EXP(AFD/FBA) under stall-scale loads — the R9
tip-bottleneck lesson: traction is linkage-limited). This is a measured
physics finding reported as-is under the registered failure response
(no adhesion tuning to hit a number); it does not contradict L-S2 —
both-ends inward traction is real and demonstrated, but asymmetric.

### L-S4 Severed fibers re-anchor BOTH ends and repair (O-S6)

A midplane sever at the loaded transient (SEVSTEP=500) is followed by:
(i) deterministic fission of straddling filaments with cause-5
link/motor releases and slot-exact bookkeeping (exercised program-wide
in sev_s77031: myor×1 + xlkr×2, lifetime/endpoint-exact); (ii) a
tension transient — spike to 70.6 (s77031, post-sever window 1) or dip
to 2.3 (s84950) — then sustained tension ≈ 13 (≥10 consecutive windows
>0 from step 1000, never broken); (iii) re-anchoring of BOTH ends at
84–94% bonded duty (higher than the unperturbed mains' subordinate
ends — the post-sever ensemble escapes single-anchor dominance); (iv)
remnant persistence and re-growth (all remnants alive at 1M; up to 5→92
monomers). Both arms classify REPAIRED on the registered criteria.

### L-S5 Antiparallel organization is enriched around myosin; the gate is record-proven (O-S4)

Crosslink density inside the myosin-bearing region exceeds outside in
all 4 logs (0.78–0.89 vs 0.42–0.75 links/unit-x), and every accepted
link — including the same-half buckled-local-axis accepts (9.5–39.7% of
cumulative attaches, arm-dependent) — carries a bpol record proving the
certified PBUND=2 gate accepted it at cos ≤ −0.5 (0 violations on 9000+
accepts). Parallel regions (same-half pairs at 2.598 > RXLK) stay
link-free by construction except under buckling; polarity organization
is a range finding, never a gate.

### L-S6 Motor directionality is certified on the frozen-kinetics battery; live-kinetics lab signs are a range (sign doctrine)

The hard motor-sign gate for R11 is the R11-a constructed-geometry
frozen-kinetics battery: 80/80 contour-invariant AND strict lab signs
(recomputed). In the live-kinetics 1M logs the per-head lab-x sign is
~50/50 (e.g. main_s77031 L_ok 7371/L_bad 7098, R_ok 14044/R_bad 14487)
— registered range physics: filament buckling plus monomer-slot
recycling under live turnover make the lab-frame sign geometry-dependent
(the R10 L-M1 doctrine: contour correctness is the invariant; lab signs
are ranges). The contour data-structure invariant is not the
live-kinetics check (slots recycle); the hard live-log content is zero
stale-grip/null-step events (all 4 logs clean) with the per-head sign
reported as a range.

## Oracle scorecard (O-S1..O-S7)

| oracle | registered criterion | measured result | verdict |
|---|---|---|---|
| O-S1 channel-OFF byte-identity | PSF=0/PSEV=0 ≡ certified R10 parent, all levels | MIRROR `3f3269db...`; 50k `007e6b2b...`; 300k gates 6/6 + PMYO=1 50k row `0a4ba14c...` = 7/7 byte-identical (all hashes recomputed) | **PASS** |
| O-S2 assembly time (range) | report from the registered initial condition | (a) bond-assembly latency 500 all arms (constructed, honest); (b) contractile equilibration 3500/8500 mains, 85500/39500 post-sever | **REPORTED (range)** |
| O-S3 contractility (headline force) | both endpoint adhesion groups bear inward traction; tension positive + stationary | both-ends simultaneous inward traction on main_s77031 (+0.490/−0.254, fmag≈2.0); per-end inward traction all arms; tension positive 93.6–98.3% windows, stationary, means 10.31–17.26, all 4 arms; qualification: anchor competition (L-S3) | **PASS with registered measured qualification** |
| O-S4 polarity organization (range) | antiparallel enrichment around myosin; parallel regions identified | density in>out all 4 logs (0.799/0.696, 0.892/0.747, 0.781/0.423, 0.883/0.590); same-half buckled accepts 9.5–39.7%, bpol-proven, 0 gate violations | **REPORTED (range)** |
| O-S5 homeostasis (range; no-runaway force check) | length/tension bounded under turnover; distributions | flen/tension bounded, stationary; turnover balanced; nbound 329–343; max|netf|=0 | **REPORTED (range), no runaway** |
| O-S6 perturbation outcome (range) | sever at registered step; classify repaired/failed-measurable | both arms REPAIRED: re-anchored both ends 84–94%, tension transient then ~13 sustained, remnants persist/grow; cause-5 program target MET (sev_s77031: 3); sev_s84950 per-arm target MISSED with registered geometry reason | **REPORTED (range); both REPAIRED** |
| O-S7 books (HARD) | all inventories conserved, ghost scan 0, max|netf|=0, no bookkeeping force discontinuity | PASS all 4 logs: 2000 censuses each; conservation/ghost/motor(causes 1–6)/XL(1–5)/R6-ADH/SF per-end exact; fib↔fil cross-check exact; netf 0.000e+00 every window (independently re-derived); FINAL, NUL=0 | **PASS** |

**R11 exit criterion (plan_stress.md): MET.** A dynamic
adhesion-anchored actin-myosin fiber (i) maintains contractile tension —
YES, positive+stationary all 4 arms (L-S1); (ii) transmits inward
traction to BOTH substrate attachments — DEMONSTRATED (L-S2; severed
arms re-anchor both ends at 84–94% duty, L-S4); (iii) with the force
numbers recorded for the cell-scale stage — tension scale 10–17 mean
(peak 94 transient), per-bond fmag ≈ 2.0, traction duty-limited per
L-S3. The anchor-competition qualification is registered as a physics
finding, not a bug; all hard gates PASS.

## Failure-mode register (plan_stress.md §"Registered failure responses") with dispositions

| anticipated failure | registered response | disposition |
|---|---|---|
| Hard-gate failure (O-S1/FD/signs/O-S7) | STOP, evidence, no tuning | **Not triggered.** All hard gates passed at every stage (7/7 O-S1, FD 2.8e-10/1.5e-9, 80/80 sign battery, 4/4 O-S7) |
| Near-zero assembly (O-S2) | measure nucleation/attach flux first; geometry amendments only, never physics | **Not triggered.** Constructed fiber assembles in window 1 (latency 500) on all arms |
| Traction rupture-dominated at anchors | report distributions as-is (R9 lesson — do not strengthen adhesion) | **TRIGGERED as physics.** Anchors are rupture-dominated slip bonds; the steady state concentrates load on one anchor (L-S3). Distributions reported as-is; no parameter touched |
| Disk pressure / no zips | 1M logs ~56MB discipline; deletions only on user word | Honored; nothing zipped or deleted (4 × 57–59MB logs retained) |
| UB landmine (erratum 8) | no non-literal code in INIT_CERT; bounded loops; register every rung | **Standing rule, permanent** (see the caution section); parent fix deferred to a future parent rung |

## Caveats and provenance

1. **Erratum-5 preload on all tension numbers.** The 3 constructed
   motors start stretched 0.42 each (~0.84 units contractile preload per
   motor, ~2.5 total, same sign as contraction). All O-S3 tension
   numbers include it; it does not change any verdict (steady-state
   tension is turnover-maintained, not preload-maintained), but it is
   registered and must be quoted with the numbers.
2. **myoa record-accuracy defect (erratum 5b).** Step-0 myoa records
   print the hardcoded constant 1.500000 where the true constructed grip
   distance is 1.92. R11-c analysis uses gm-derived distances for
   constructed motors; the myoa distance field on constructed attaches is
   not to be trusted (follows the parent SMYO convention, where the
   constant matched reality). Engine forces are unaffected (computed
   from positions); this is a records-only defect, registered.
3. **Analyzer finding: reg-8 R6 transfer re-key (records-only).** An R6
   ADH bond whose gripped monomer moves to a sever remnant TRANSFERS to
   the new slot with NO event record (registered monomer-grip
   convention). The R11-c analyzer re-keys such bonds by remnant slot
   (adhr lifetime-exact); the engine's own books remain exact
   (sev_s77031: 1 such transfer, filament 4 → slot 10, lifetime 385).
   `sf_books.py` hardcodes SEVSTEP=25000 and is applied unmodified only
   to PSEV=0 arms as a cross-check; the R11-c analyzer
   (`r11c_analyze.py`) is the SEVSTEP-parameterized checker of record.
4. **Live-kinetics sign caveat (L-S6).** The hard motor-sign gate is
   the frozen-kinetics 80/80 battery; live-log per-head lab signs are
   ~50/50 range physics (buckling + slot recycling). Do not quote
   live-log lab-sign fractions as directionality evidence.
5. **Doc-pass discrepancy notes (recomputation culture — recorded, not
   silently fixed).** (a) plan.md's O-S4 summary says "20–40% of dynamic
   links are same-half buckled local-axis accepts"; the artifacts (raw
   counts in r11c/*.analysis.txt, independently recomputed from xlka
   records this doc pass) give cumulative-attach fractions
   **38.8%/39.7%/9.5%/16.0%** (mains ~39%, sever arms 9.5–16.0%) — the
   "20–40%" band matches neither the per-arm values nor their range;
   this law doc carries the recomputed numbers. (b) Verifier erratum 6's
   "bare for the final ~39.9k steps" computes to 40,060 steps from the
   last right-end attach at step 9940 (80.1% of 50k) — tilde-level
   rounding only, noted for completeness. Neither affects any gate,
   law, or verdict. plan files were NOT modified (discrepancies reported
   here per the doc-pass rule).
6. **Reserves unspent; budget 4/6.** Both registered reserve slots were
   held against ambiguous measurements and deliberately NOT spent
   (registered reserve decision: sev_s84950's cause-5 miss has a
   geometry reason, and a non-census-aligned SEVSTEP would weaken O-S7).
   No further R11 runs.
7. **Determinism chains (recomputed).** main_s77031 ≡ sf_50k.log
   through step 50000 (only the 48-line terminal FINAL block differs);
   sev_s77031 ≡ main_s77031 and sev_s84950 ≡ main_s84950 through step
   499 (PSEV=1 inert until SEVSTEP; sev records at exactly 500).
8. **Runner/checker provenance.** Runs via `runner_r6.sh` (sequential,
   /tmp-staged, .status-written; all attempt=1). Checkers:
   `runs25/sf_books.py` SHA256
   `01077b09817bbd017a307d57ee6f30b650260d39c9fd7d86af42fc8dde80541d`;
   `runs25/r11c/r11c_analyze.py` SHA256
   `36e7c5a27e28eb3529851b70c6cc161398a99f72a6fed31c68f380dfef54b290`
   (both recomputed this doc pass); analysis outputs
   `r11c/*.analysis.txt` (BOOKS PASS ×4, recomputed spot-level on
   main_s77031 and independently on netf/conservation/sever records for
   all 4 logs); driver record `r11c/driver.log` SHA256 `f388c990...`.
9. **R10 frozen-kinetics limitation resolved by construction (reg. 1).**
   The R10 anchor unbind-transfer gap does not exist in R11: INIT_SF
   sets no HASA anchors on fiber monomers, so there is no constructed
   KSEED anchor whose transfer could be needed; anchoring is entirely
   the live R6 slip-bond law.
10. **Single-construction scope.** Numbers are for the reg. 3
    six-filament ring construction at registered defaults, seeds
    {77031, 84950} (the seed axis spans the anchor-competition sides);
    other fiber geometries/myosin densities are future registration
    items. The R9 PCLU/PTIPA/PTIP channels remain OFF (available but
    unused) per the registered user priority.

## Artifacts (all under `/mnt/agents/output/actin_phasespace/`)

- Engine: `phi4/runs25/stress_fiber.ergo` SHA256
  `3a6cc866b869de69f09683f3cd61a0c93dba89b8136ea5a05ffef39ef6faed68`
  (5058 lines, +811/−0; recomputed) + `stress_fiber.bin`. Code bundle
  `actin_phasespace/r11_repo.bundle` (refreshed at this doc pass; sha256
  reported in the plan.md R11-doc entry).
- Oracle: `phi4/plan_stress.md` (regs. 1–12, builder errata 1–4,
  verifier errata 5–8, R11-c registrations + run record, all pre-run).
- R11-a: `runs25/static_cert/` (mirror_off.out `3f3269db...`,
  cert_sf1.out `301cc45d...` — SFAC×2 + CERT_SFA esfa=1.0 exact,
  parent lines byte-identical, FD outs fd_sf{125,133}_{plus,minus});
  `runs25/sign/sign_sf1.log` `cb1e4e96...` (80/80);
  `runs25/smokes/` (op1_50k.log `007e6b2b...` = R7–R10 reference;
  sf_50k.log `e7576aaf...`; sf_sev_50k.log `48d3d8a3...`; construction
  probes probe0/probe0psf0/probe1).
- R11-b: `runs25/gates/` — 6 os1 300k logs byte-identical to the
  runs24 om1 references (hashes `16c9db1c...`/`5636a7eb...`/
  `b84d72e1...`/`c5444043...`/`cb3e60fe...`/`8ddb802b...`) +
  os1x_pmyo1_50k.log `0a4ba14c...`; .status files; work/ variants.
- R11-c: `runs25/r11c/` — 4 anchored-copy configs + binaries + 1M logs
  (`e72842a9...`/`e5b2b226...`/`f0a6e71e...`/`8cfd9240...`, recomputed)
  + .status + .compile.log + `*.analysis.txt` + `r11c_analyze.py` +
  `driver.log`.
- Checkers: `runs25/sf_books.py` `01077b09...`;
  `runs25/r11c/r11c_analyze.py` `36e7c5a2...` (both recomputed).
- Execution record: `actin_phasespace/plan.md` R11 Stage 0–3 (+ this
  R11-doc pass). Analytics index: `phi4/ANALYTICS.md` MAP 10.

## Reproduction

```bash
# toolchain: certified Ergo compiler (python3 -m core), frozen per Stage-0
# runner: runner_r6.sh (sequential, /tmp-staged, verified; writes .status)
# engines: runs24/myosin_unit.ergo (parent) -> runs25/stress_fiber.ergo
# R11-a: compile static_cert/*.ergo; cmp mirror_off.out vs R10 mirror (3f3269db...);
#        CERT_SFA esfa=1.0 exact; FD: (esfa+ - esfa-)/2e-6 vs +/-2.0, err 2.8e-10/1.5e-9
#        sign battery: myost events — contour $6==$5+1 AND lab sign by gripped half (80/80)
# R11-b: runs25/gates/work variants; child sha256 == runs24 om1 reference sha256 per row
# R11-c: runs25/r11c configs (anchored ^PARAMETER copies; 9-11 changed lines each);
#        books+measurements: r11c/r11c_analyze.py (SEVSTEP-parameterized);
#        cross-check mains with sf_books.py; independent awk: conservation,
#        netf over myos/xlks census fields, contour/cause-5 event counts
```

## Conclusions for the phase-space map

The 7th certified engine closes the stress-fiber question: a
live-kinetics alternating-polarity actin-myosin fiber, anchored at both
barbed ends by certified R6 slip bonds, holds stationary contractile
tension under full component turnover (L-S1), transmits inward traction
to both substrate attachments at the fmag≈2.0 bond scale (L-S2), and
repairs a midplane sever by re-anchoring both ends (L-S4). The measured
qualification — rupture-dominated anchor competition concentrating load
on one seed-selected anchor in the unperturbed steady state (L-S3) — is
the design-relevant finding for the cell-scale stage: traction magnitude
is duty-limited by linkage kinetics, not by the contractile machinery
(the R9 tip-bottleneck lesson, now expressed at the fiber scale).
Polarity organization is antiparallel-enriched around myosin with
record-proven gating (L-S5); motor directionality rests on the
frozen-kinetics battery, with live-log signs a registered range (L-S6).
Engine certified and frozen; R11 CLOSED.
