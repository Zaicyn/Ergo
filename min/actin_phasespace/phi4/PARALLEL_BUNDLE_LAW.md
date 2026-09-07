# PARALLEL_BUNDLE_LAW.md — φ4.11 minimal parallel bundle (filopod_min, R9) certification and the O-P4 force finding

Certified: 2026-09-03 (R9-a build/statics/gates; R9-b O-P1 gates; R9-c
single-seed smoke; R9-d ensemble). R9 is **closed with a registered
finding**: the headline force oracle **O-P4 FAILED on physics** (not a
bug) — the parallel bundle polarizes but is not certified force-bearing;
the bottleneck is the tip linkage. This document is the combined R9 doc
pass (deferred at R9 disposition, executed 2026-09-04 under the combined
R9+R10 documentation stage).

Engine lineage: pop_fpt.ergo (φ4) → brush_c400g → brush_br400 →
brush_bra (S4 anchored branching) → brush_bra_x → brush_bra_r →
brush_bfm (per-filament formin channel) → brush_adh (R6 PADH adhesion)
→ brush_xlk (R7 PXL crosslinks) → bundle_pol (R8 PBUND polarity gate)
→ **filopod_min** (R9: seeded parallel cluster + tip adhesion + tip
instrumentation, FORMIN at the distal end). Final source
`phi4/runs23/filopod_min.ergo` (3499 lines, **+525/0** vs parent —
verified by direct diff: 525 added, 0 removed/changed), SHA256
`6a343fdef82c16a74a8e862b33d44cd88bb4101b9079bc684d3f38b70f498d8f`
(recomputed this doc pass), merge commit `df789f3` in the live repo
(durable code-only bundle `actin_phasespace/r9_repo.bundle` SHA256
`ab2ad7d8ebaf06f5198b6861ab2fa0d40013f65e89218693a7aac395fe984a0a`,
recomputed). Parent: certified `phi4/runs22/bundle_pol.ergo` SHA256
`fb1c8d281b72816304a8bf13e9b66e815ec75200c20803c31879011b46507935`
(merge `d84f3c6`), re-verified untouched after build. Oracle:
`phi4/plan_filopod.md` (O-P1..O-P5 plus the doctrine hard-gate battery;
no O-P6 was ever registered), registered 2026-09-03 **before** engine
build and ensembles, under the 2026-09-03 force-first doctrine
(BUNDLE_LAW.md §doctrine; binding on R9). All durable artifacts under
`/mnt/agents/output/actin_phasespace/`; runs under `phi4/runs23/`
(static_cert/, smokes/, gates/, r9c/, r9d/). No zips; no certified file
modified after certification. Slip-law carryover from R7/R8 by
registration (no law grids; all arms XLNF=0).

## The question

Can formins, parallel-bundle crosslinking, and tip adhesion organize a
persistent, force-bearing parallel bundle — without myosin? This is not
the full filopodium (no membrane tube, no guidance field, no detailed
tip complex); it is the simplest non-contractile bundle assay validating
the shared machinery before R10 myosin.

**R9 answer: the machinery assembles, polarizes, and closes its books —
but the bundle is NOT certified force-bearing. O-P4 FAIL: traction is
set by the tip linkage, which bundling leaves unchanged.**

| stage | arm | purpose | outcome |
|-------|-----|---------|---------|
| R9-a | build + static/FD cert + review + verify + merge | PCLU/PTIPA/PTIP channels on certified R8 parent | PASS (GO with concerns, all closed/registered; CERTIFICATION VALID 8/8 claims) |
| R9-b | O-P1 gates PBUND∈{0,1,2} × seeds {77031,84950}, 300k | all new channels OFF ≡ R8 parent, byte-identical | PASS 6/6 |
| R9-c | bundle smoke + O-P4 single-seed (s77031, 1M, bundled vs PBUND=0 control) | books battery; preliminary O-P4 | books PASS both arms; O-P4 preliminary NEGATIVE |
| R9-d | ensemble (adds s84950 arms) + lpol instrument validation | pooled formal O-P4 verdict; polarization replay | **O-P4 FORMAL FAIL**; replay validated ≤0.0013 vs engine-native lpol |

## Mechanism as certified

Composition, not new physics: R6 adhesion channel (second instance at
the tip zone) + R7 transient crosslinks + R8 PBUND=1 parallel gate +
the certified R2 FORMIN channel at the distal end. All parent code
untouched (0 removed/changed lines). Registered builder scope
(plan_filopod.md, registrations 1–7, all before build):

- **PCLU seeded parallel cluster (registration 1; deterministic, ZERO
  new RNG draws).** `PCLU=0` (default): parent trimer `INIT_DYN` path,
  bit-identical to the R8 parent. `PCLU=1`: `INIT_CLU()` re-seeds after
  `INIT_DYN` (R8-c PCERT overwrite pattern; the hash RNG is stateless so
  the pre-draws consume nothing). Cluster: `NFCLU=5` filaments ×
  `LCLU=8` monomers, filament slots 1–5, monomer slots 1–40, axes along
  +x pointed→barbed. Pointed-monomer centers at x=2.25 so pointed tail
  beads sit on the substrate plane x=XADH=2.0 (brush anchoring
  geometry); barbed-end head beads distal at x=6.70, pointing at the
  piston. Lateral cross pattern (y,z) = (6,6), (4.5,6), (7.5,6),
  (6,4.5), (6,7.5): nearest-neighbor spacing 1.5 = DX0 (crosslinks form
  at zero initial stretch; spacing > WCUT, < RXLK=2.0 capture).
  Pointed-end anchoring as in the brush (FILANCH/HASA, ANCHORS
  KSEED-spring targets = seeded positions, machinery unchanged).
  Monomers 41..400: free gas rejection-sampled by the SAME INIT_DYN hash
  stream (existing slots only). Rationale (registered): 5×8 gives a
  PBUND-eligible (FILLEN≥4) parallel core with interior monomers from
  t=0, 360 free monomers, and an exact-bookkeeping census.
- **FORMIN scoping (registration 2; no code change).** The certified R2
  per-filament processive tether (grasp ring PX(barbed head) > XP−RGRIP,
  standoff XP−S0F) applies unchanged; scoping is SPATIAL: cluster tips
  seed at x=6.70 > XP0−RGRIP=6.5, so all five cluster tips are gripped
  from t=0 under FORMIN=1. FORMIN=0 path untouched → FORMIN-off
  byte-identity holds by construction.
- **PTIPA tip adhesion (registration 3; verbatim R6 slip-bond
  instance).** 3D harmonic spring F=2·KADH·(A−R), E=KADH·d², slip
  rupture P=KOFFA·DT·EXP(|F|/FBA), hard release d>SMAXA, one bond per
  filament, bond tracks the monomer. Placement: DISTAL TIP ZONE —
  eligible element = barbed-end head bead B=2·FILBARB(F)−1 with
  PX(B) ≥ XTIP−RADH; fixed lab-frame target A=(XTIP, y, z) (R6
  fixed-target convention). `XTIP=9.0` = XP0, the initial piston rest
  plane (tip complex gripping the membrane plane the bundle pushes
  against). Along-shaft adhesion via the parent PADH channel unchanged.
  Cause wiring mirrors R6 (cause 3 at both unbind sites, cause 4 in
  DISSOLVE). Registered composition note: the tip-adhered monomer
  REMAINS crosslink-eligible (parent inline exclusion not editable under
  the additive rule); both are certified force paths and superpose
  exactly — force closure verified per-path by FD and globally by the
  books battery.
- **RNG discipline (registration 3, as corrected in review).** New
  registered slot block **6900–6963**: attach 6900+2·(F−1), rupture
  6901+2·(F−1), F=1..MAXF=32 (64 slots; the review corrected an
  off-by-one — originally registered "6900–6962", the tail slot 6963 is
  the F=32 rupture slot). Disjoint from every certified slot (previous
  max 6873, R7 crosslink block). Zero draws when PTIPA=0 (routine never
  called). No other new draws anywhere in R9.
- **PTIP tip instrumentation (registration 4; records-only, zero RNG).**
  Windowed record at NDIAG cadence (after `xlks`, before `gm`):
  `tip STEP ntip xtip npoly trx try trz fmag` — ntip = active
  seeded-cluster filaments (slots 1..NFCLU; slot-membership definition,
  registered), xtip = mean x of their barbed head beads, npoly = ΣFILLEN
  over cluster slots, trx/try/trz = mean substrate traction at tip bonds
  over the window (exact adhs-convention bookkeeping), fmag = mean |F|
  per attached bond-step. Computed from existing state; no force, no
  feedback. PTIP=0 (default) emits nothing.
- **Event records (registration 5; strict WRITE arity, R6 mirror).**
  `tipa STEP F M B ax ay az` (attach, arity 7); `tipr STEP F M lifetime
  fx fy fz cause` (rupture, arity 8; cause 1=slip, 2=hard stretch,
  3=monomer unbind, 4=filament death).
- **MIRROR static-cert construction (registration 6).** INIT_CERT gains
  an additive constructed cluster (guard PCLU=1 AND PXL=1 AND PBUND>0 so
  parent R7/R8 constructed chains are always present): filaments 9
  (monomers 40–43, y=6), 10 (44–47, y=8) along +x, 11 (48–51, y=10)
  along −x, all z=2.5; constructed crosslink slot 2 between monomers 41
  and 45 (d=2.0 pure-y); constructed tip bond on filament 9 barbed
  monomer 43 (bead 85 at x=10.05, target XTIP=9.0, pure-x d=−1.05).
  New cert lines `TIPC`, `CERT_TIP etip`, and `CERT_FPOL <case> M1 M2 ok
  acc cos` sign battery (par (41,45) cos=+1; anti (45,49) cos=−1;
  endmon (40,45) ineligible). FD per the R6/R7/R8 fdplus/fdminus
  pattern: tip bead 85 x (etip), crosslink bead 81 y (exl), R6 adhesion
  bond bead 96 x (eadh, PCLU=1 composed config — amended per the R9-a
  verifier flag from the originally registered bead-2/PCLU=0 wording;
  the executed check exercises the identical adhesion law path in the
  composed configuration, and the bead-2 bond is present and exact in
  the same dump). Gate: |analytic − FD| < 1e-8 per path.
- **Registered run configs (registration 7).** O-P1: PCLU=0 PTIPA=0
  PTIP=0 PBUND=0, PXL=1 PBR=0 FORMIN=0 PADH=0 DIMERS=1 PSTN=1 F_EXT=1.0
  SEED=77031 NSTEPS=50000 XLNF=0 → byte-identity vs
  `runs22/smokes/parent_50k.log`. Cluster smoke: PCLU=1 PBUND=1 PTIPA=1
  PTIP=1 FORMIN=1 PXL=1 PADH=0 PBR=0 DIMERS=1 PSTN=1 F_EXT=1.0
  SEED=77031 NSTEPS=50000 XLNF=0 PCAP=1 (constructed census t=0:
  nfil=5, nbound=40, nfree=360, NM=400; PBR=0 — branching out of the
  minimal-bundle scope).

## Certification chain

1. **Static/FD certification passed (R9-a)** (`runs23/static_cert/`,
   `runs23/smokes/`, `runs23/SHA256SUMS`). Fresh compile PASS.
   FD vs analytic on all composed paths < 1e-8 (recomputed this doc pass
   from the cert outs: **exl 1.398e-10, etip 6.756e-10, eadh
   6.810e-9**). CERT_TIP `etip` = 2.205 = KADH·d² exact (KADH=2.0,
   d=1.05); constructed crosslink `exl` = 0.5 exact. Sign battery zero
   errors both arms (parent CERT_BPOL + cluster CERT_FPOL: par acc
   cos +1.000000 / anti rej cos −1.000000 / endmon `ok 0 acc 0` —
   verified in `static_cert/cert_base_bpol{1,2}.out`). MIRROR-off dump
   byte-identical to the parent lineage dump (SHA256 `3f3269db...`,
   recomputed — the same hash as the certified R7/R8 mirrors).
   **O-P1 50k byte-identity PASS:** `runs23/smokes/op1_50k.log` SHA256
   `007e6b2b20f1992a4248362ea92528dfa5ba5b39614a8d922ebf89336810faa0` =
   the certified R7/R8 50k reference (recomputed). Cluster smoke 50k
   books PASS: conservation 400 at all 100 censuses, ghost scan clean,
   xlink inventory exact (xlka=397 xlkr=389), tip inventory exact
   (tipa=422 tipr=412, 10 open — counts recomputed from
   `smokes/clu_50k.log`), max|netf|=0, bpol all cos∈[0.500069,0.999560]
   (plan.md Stage-1 record). Process note: the builder hit the
   batched-edit_file silent-drop hazard (3 calls), self-detected via
   inconsistent cert evidence, and re-audited line-by-line; all certs
   are from the final audited engine.
2. **Independent review: GO with concerns (no blockers).** Concern 1 —
   RNG block off-by-one → FIXED in the oracle (6900–6963). Concern 2 —
   cert header overclaim → registered as a known issue, closed at R9-b
   (deferred wording amendment; no hash-changing edit; parent-carried
   INIT_CERT header "pure additions" overclaims vs a PADH=1 baseline —
   aggregate totals only, explainable, no physics defect). Notes:
   ntip=active-filament-count semantic (documented); O-P1 coverage to be
   extended at R9-b (PBUND-active arms + 300k) — done; INIT_CLU bounds
   notes. **Independent verification: CERTIFICATION VALID, all 8
   claims**; one doc flag → FIXED in the oracle (FD bead 96 / PCLU=1
   amendment line).
3. **Merge.** Repo .git lost in a container restart → restored from
   `r7_repo.bundle`, R8 tree recommitted (`1b9b579`, hash-verified),
   R9-a committed **`df789f3`**; durable `r9_repo.bundle` SHA256
   `ab2ad7d8...` (recomputed this doc pass).
4. **O-P1 gates passed (R9-b)** (`runs23/gates/`). 6/6 rows
   byte-identical (PBUND∈{0,1,2} × seeds {77031,84950}, 300k, all new
   channels OFF): child == parent for every row, recomputed this doc
   pass — `16c9db1c...` / `5636a7eb...` / `b84d72e1...` / `c5444043...`
   / `cb3e60fe...` / `8ddb802b...`; all statuses OK
   attempt=1, NUL=0, FINAL ×2. **Provenance caveat (registered):** the
   briefing premise was wrong — `runs22/gates/` holds only OB1-era
   off-matrix logs (PXL=0/F_EXT=0.1); no 300k brush-config parent
   references ever existed. All 6 parent refs were run fresh under R9-b
   from the certified parent (fb1c8d28... verified untouched
   before/after); the s77031 parent refs therefore have **R9-b
   provenance, not R8-b** — flagged for the record.
5. **R9-c single-seed smoke + preliminary O-P4** (`runs23/r9c/`).
   Bundled 1M s77031 log SHA256 `2144637e...` (58,483,712 B), control
   (PBUND=0) `e5a818e4...`, both OK attempt=1 (recomputed). Books
   battery BOTH ARMS PASS: conservation exact ×2000 censuses, ghost
   clean, xlink inventory exact (xlka/xlkr = 10477/10468 bundled;
   20495/20476 control — recomputed), tip inventory exact (10205/10195,
   10 open; 10064/10055, 9 open — recomputed), max|netf|=0, nfil
   event-exact, bpol zero sign errors (min cos 0.500026, plan.md
   record). O-P4 preliminary (n=1000 matched post-burn-in tip windows,
   `r9c/r9c_op4_report.txt`): bundled trx mean +0.5113 vs control
   −0.0081 (Neff 413.2/419.4, Welch t=1.97, one-sided p=0.0243);
   NEITHER pre-registered limb met — distributions fully overlap
   ([−11.14,10.61] vs [−12.64,12.51]), magnitude ratios < 1 (|tr|
   0.9361), no differential stall (xp ≈ 10.5 both arms, fluctuating
   steady state). Method note registered for R9-d: the ≥1.5× limb is
   degenerate on signed trx (control mean ≈ 0 → ratio −62.9,
   meaningless); the limb applies to traction MAGNITUDES.
6. **R9-d ensemble + pooled verdict + replay validation**
   (`runs23/r9d/`). s84950 arms added (bundled `342c9f16...`, control
   `c59f9684...` — recomputed, match `r9d/SHA256SUMS`); R9-c s77031
   pair reused, not rerun. Hard checks PASS both seeds (conservation
   exact ×2000 censuses, ghost 2000/2000, xlink inventory exact
   (9667/9659 bundled, 19934/19913 control; bpol=xlka=9667 bundled),
   tip inventory exact (9344/9337; 9519/9507), max|netf|=0, bpol cos ∈
   [0.500161, 0.999973] zero sign errors — counts recomputed). lpol
   instrument validation: `filopod_min_lpol.variant.ergo` (r9c bundled
   config + 45 additive lines, PLPOL default 0 inert) run at PLPOL=1
   (`r9d_lpol_verify_s77031.log` `90b95d84...`, 16642 lpol records);
   stripped by `grep -v '^lpol '` the log is BYTE-IDENTICAL to the
   certified r9c bundled log (cmp clean — re-run this doc pass; 16642
   lpol records) → instrument dynamics-neutral and valid. Engine-native lpol vs replay (bundled
   s77031, post burn-in, tangent-eligible): agreement ≤ 0.0013 on every
   class fraction, mean cos, and age bin (≪ ±0.01 gate) → the replay
   numbers stand for all four arms; all reconciliation-flagged dumps are
   pre-burn-in on all four arms (post-burn-in measurement window
   reconciles exactly). **Pooled formal O-P4 verdict: FAIL** — see the
   headline section below.

## The headline: O-P4 FORMAL FAIL (physics finding, not a bug)

Method (pre-registered, threshold-free): matched post-burn-in
(>500k) tip windows, n=1000 per arm per seed; Neff = n/(1+2·Σρ_k),
Geyer IPS pair cutoff, lag ≤ 50 (the R7 O-X3 instrument); one-sided
tests in direction bundled > control; pooled mean = average of seed
means, Var = ¼Σsd²/Neff per arm. Per the R9-c method note the ≥1.5×
limb is applied to traction magnitudes (|tr|, |trx|); the signed-trx
difference is reported separately. Source: `runs23/r9d/r9d_op4_pooled.txt`
(SHA256 in `r9d/SHA256SUMS`), numbers cross-read against
`r9c/r9c_op4_report.txt` and `r9d/r9d_op4_analysis_s84950.txt`.

Per-seed reads (bundled vs control):

| seed | trx means | Welch t / p (signed) | \|trx\| ratio | \|tr\| ratio | disjoint (min_b trx > max_c trx) |
|------|-----------|----------------------|---------------|--------------|-----------------------------------|
| 77031 | +0.5113±3.6515 vs −0.0081±3.9482 | t=1.97, p=0.0243 | 0.9455 (p=0.926) | 0.9361 (p=0.995) | NO ([−11.14,10.61] vs [−12.64,12.51]) |
| 84950 | +0.8909±3.5768 vs +0.7292±3.8935 | t=0.63, p=0.2632 | 0.9416 (p=0.866) | 0.9653 (p=0.794) | NO ([−9.33,14.65] vs [−12.99,14.64]) |

Pooled limbs:

- **(a) Disjoint limb: NO in both seeds → limb fails.**
- **(b) Magnitude limb: pooled |tr| ratio 0.9506** (Neff-corrected
  one-sided p=0.978); **pooled |trx| ratio 0.9436** (p=0.960). Both
  < 1.5 — indeed < 1.0, the WRONG DIRECTION → limb fails.
- **(c) Signed-trx difference (separate, per the method note): pooled
  +0.3406** (bundled 0.7011 vs control 0.3606), se=0.1834, Welch t=1.86
  (df≈788), one-sided **p=0.0317** — statistically significant, but it
  satisfies **neither** pre-registered limb.

**FORMAL VERDICT: O-P4 FAIL.** The R9 exit criterion ("a stable,
polarized, force-bearing parallel bundle exists without myosin") is NOT
met; R9 closed with the finding registered (user directive 2026-09-03:
proceed directly to R10; doc pass deferred to the combined R9+R10 stage
— this document).

### Root cause: the tip-linkage bottleneck

The parallel-bundling gate does not make the seeded cluster certified
force-bearing. The signed traction response is real but small (pooled
+0.34 on a noise floor of σ≈3.8; significant only at p≈0.03 with
Neff-correction, and in only 1 of 2 seeds individually), while traction
MAGNITUDES are if anything slightly REDUCED by bundling (pooled |tr|
0.95, |trx| 0.94). The bottleneck is tip linkage, not filament
alignment: tip-bond occupancy is essentially unchanged by bundling
(9.76/9.86 bundled vs 10.68/10.02 control bonds, post burn-in), rupture
|F| ≈ 2.80–2.86 mean with ~96.5–97% above the slip scale FBA=1.0 in all
arms (deep slip-bond regime), and formin grip ≈ 10.9–11.1 bundled vs
11.3–12.1 control — so the cluster cannot convert its polarized
interior into sustained x-traction. Force-bearing filopodium traction
under this engine would require strengthening the tip-linkage pathway
(more/harder tip bonds or slower rupture), not more bundle polarity.
**Registered as the R9 finding and as the design target for R10/R11
force transmission.**

### Measured side effects of bundling (ranges, 4 arms, seed order 77031 bundled/control then 84950 bundled/control)

- **Crosslink loading halved:** xlink occupancy nxl 8.28 [3,16] and
  7.80 [1,15] bundled vs 16.93 [7,23] and 15.72 [9,23] control;
  attach+rupture rates ~9.8–10.6 vs ~20.9–21.4 per 1k steps.
- **Turnover suppressed; npoly variance seed-dependent:** cluster npoly
  mean/var (77031 bundled/control, then 84950 bundled/control):
  91.18/79.20, 122.32/551.16, 142.39/349.07, 111.92/195.31 — bundled
  variance lower at s77031 (79.20 vs 551.16) but HIGHER at s84950
  (349.07 vs 195.31). DOC-PASS CORRECTION: R9D_REPORT §3/§5's
  parenthetical "bundled variance lower at both seeds" is inconsistent
  with its own §5 numbers at s84950; the accurate statement is
  seed-dependent variance (this doc quotes the numbers, not the
  parenthetical).
- **Polymer content seed-dependent:** npoly 91.2 vs 122.3 at s77031 but
  142.4 vs 111.9 at s84950 — bundling stalls the cluster it manages to
  keep rather than growing it.
- **Bundled filaments shorter and longer-lived:** cluster filament
  length means 19.02/29.50 bundled vs 24.71/23.47 control (max 57/64 vs
  58/66); dead-incumbent lifetimes 232k–814k steps ≈ 50–200× the
  ordinary filament median (5088/3678 bundled, 3530/4556 control).
- **Persistence not protected:** seeded-incumbent 1M-step survival 5/10
  bundled vs 4/10 control — no significant protection.
- **Piston static:** xp 10.49–10.51 all arms (no drift; fluctuating
  steady state, no differential stall).

## R9 laws

### L-P1 The R8 polarity-selection instrument transfers exactly to the filopod geometry (O-P2, ranges)

Live-link parallel fraction (cos ≥ +0.5) 0.3739/0.3762 bundled vs
0.2407/0.2378 control (enrichment ≈ **1.56×**, both seeds), carried
ENTIRELY by fresh links (age < 250: 0.6172/0.6213 vs 0.2469/0.2422) and
decaying to the control baseline within ~500 steps of link age — the R8
rotation-timing result (L-B2/L-B3) reproduced in the filopod geometry on
two seeds. Both controls reproduce the certified OB4 unselective-control
class fractions (0.2411/0.2780/0.4809) to ≤ 0.014. The replay is
engine-ground-truth-validated on this engine (lpol agreement ≤ 0.0013
everywhere; post-burn-in reconciliation exact on all four arms). bpol
attach purity 1.0000 with zero sign errors across every R9 arm.

### L-P2 Bundle polarization does not certify force-bearing — traction is set by the tip interface (O-P4 FAIL)

Bundling polarizes the interior (L-P1) but leaves the tip linkage
unchanged (occupancy, rupture-force distribution, grip), and the pooled
traction verdict FAILS both pre-registered limbs (magnitude ratios
0.9506/0.9436, wrong direction; distributions never disjoint). The
signed-trx offset (+0.3406, p=0.0317) shows the polarized bundle does
bias traction in the protrusive direction — but far below any
certifiable force-bearing factor on this tip architecture. Design
consequence (registered): R10/R11 force-transmission work must
strengthen the tip-linkage pathway, not the bundle polarity.

### L-P3 Parallel bundling suppresses crosslink loading and cluster turnover (O-P5, ranges)

Halved xlink occupancy (≈8 vs ≈16) and halved attach/rupture flux: the
PBUND=1 gate rejects the orthogonal links the unselective control uses,
and the sparser link population remodels the bundle less. Cluster npoly
variance and mean are both seed-dependent (variance 79.20 vs 551.16 at
s77031 but 349.07 vs 195.31 at s84950; mean 91.2 vs 122.3 at s77031 but
142.4 vs 111.9 at s84950), so no monotonic "stabilization" or "growth"
law is claimed — only the flux suppression is robust across seeds.

### L-P4 Bundling does not protect the incumbent filaments (O-P3, ranges)

Seeded-incumbent survival 5/10 bundled vs 4/10 control; dead incumbents
live 232k–814k steps (50–200× ordinary medians) in both arms; cluster
slots reincarnate with the same bimodal mix (trimer recycles ~10²–10³
steps; recaptured filaments ~10⁴–4.5×10⁵, max 452098). "No immortality"
holds everywhere (books closed on all deaths; all rupture causes
accounted).

### L-P5 The composed instrument chain is exact (hard gates: books, inventories, neutrality)

Every R9 log closes its books: monomer conservation exact (400) at
every census, ghost scan clean, xlink/tip inventories exact
(event-exact attach−rupture=open), max|netf|=0, nfil event-continuous,
zero bpol sign errors, NUL=0, FINAL, attempt=1. Channel-OFF neutrality
is byte-exact at every level (MIRROR `3f3269db...`; O-P1 50k
`007e6b2b...`; O-P1 300k gates 6/6). The one added analyzer complexity
— chained pointed prepends in the R9 controls (demand 7 > static
PREP_DMAX reach) — is handled by a registered fallback (greedy
chain-aware assignment + cost-ordered DFS, 60k-node cap) with every
invocation counted and every flagged dump excluded conservatively; all
flagged dumps are pre-burn-in.

## Oracle scorecard (O-P1..O-P5; no O-P6 was registered — the doctrine hard-gate battery is listed as its own row)

| oracle | registered criterion | measured result | verdict |
|---|---|---|---|
| O-P1 channel-OFF inertness | all new channels OFF ≡ certified R8 parent, byte-identical | MIRROR `3f3269db...` = parent lineage; 50k `007e6b2b...` = R7/R8 reference; 300k gates 6/6 byte-identical (both seeds, PBUND∈{0,1,2}) | **PASS** |
| O-P2 polarization (ranges, never a gate) | bundle axis correlation / polarity measured with per-seed spread | live parallel 0.374–0.376 vs control 0.238–0.241 (≈1.56×); young-link 0.617–0.621 vs 0.242–0.247; decay to baseline within ~500 steps; lpol-validated ≤0.0013 | **MEASURED (ranges)** |
| O-P3 persistence (ranges; no-immortality via books) | bundle survival vs ordinary filament lifetime | incumbent survival 5/10 vs 4/10; incumbent lifetimes 232k–814k ≈ 50–200× ordinary medians; no immortality, books exact | **MEASURED (ranges)** |
| O-P4 force (HEADLINE GATE) | bundled tip traction/stall vs unbundled control: disjoint per-seed distributions, OR pooled magnitude factor ≥ 1.5 with Neff-corrected significance | disjoint: NO both seeds; magnitude: pooled \|tr\| 0.9506 (p=0.978), \|trx\| 0.9436 (p=0.960) — wrong direction; signed-trx +0.3406 p=0.0317 satisfies neither limb | **FAIL (registered physics finding)** |
| O-P5 turnover (ranges) | monomer/filament turnover inside the bundle | xlink occupancy ~8 vs ~16; rates ~10 vs ~21 per 1k (robust, both seeds); npoly mean/variance seed-dependent (91.18/79.20 & 142.39/349.07 bundled vs 122.32/551.16 & 111.92/195.31 control) | **MEASURED (ranges)** |
| Doctrine hard-gate battery | force closure, conservation, inventories, ghost scan, nfil continuity, sign zero-tolerance, neutrality | PASS on every R9 log (all counts above recomputed from the logs) | **PASS** |

**R9 exit criterion (plan_filopod.md): NOT MET** — "force-bearing" fails
at O-P4. R9 is closed by user directive (2026-09-03) as: certified
engine (R9-a/b), polarized bundle (L-P1), O-P4 FAIL = tip-linkage
bottleneck registered as the R10/R11 design target.

## Force-first doctrine (cross-reference)

The 2026-09-03 force-first doctrine is stated in full in BUNDLE_LAW.md
§"The 2026-09-03 force-first doctrine" and is binding on R9 (it was
registered with the R9 oracle). R9 is the first rung executed entirely
under it: every hard gate is a force/conservation/inventory/byte-identity
oracle (books battery, O-P1, FD, sign zero-tolerance, instrument
neutrality by byte-identity including the stripped-lpol proof); the
single headline force gate (O-P4) was registered threshold-free with a
pre-registered METHOD (disjointness or Neff-corrected magnitude factor),
and it returned a clean physics FAIL — the doctrine working as intended:
the method, not the number, was fixed in advance, and the negative
result is a certified finding, not a gate moved after the fact. All
distributional content (O-P2/O-P3/O-P5, lengths, occupancies, grips) is
reported as ranges with per-seed spread and was never used as a gate.

## Failure-mode register (plan_filopod.md §"Registered failure responses") with dispositions

| anticipated failure | registered response | disposition |
|---|---|---|
| Hard-gate failure (bug) | STOP, surface evidence, no parameter tuning | **Not triggered.** Every hard gate passed at every stage (books, FD, O-P1, signs, neutrality) |
| Near-zero bundle assembly in R9-c | measure nucleation/eligibility flux first; register finding; adjust GEOMETRY only by amendment | **Not triggered.** The seeded cluster assembles and sustains a polarized bundle (bpol attach purity 1.0000; ~9.7k accepted attaches per bundled 1M arm) |
| Tip adhesion rupture-dominated traction | report the traction distribution as-is (ranges); do not strengthen adhesion to hit a number | **TRIGGERED — executed exactly as registered.** Tip ruptures run ~97% above the slip scale (|F| mean ≈2.8 vs FBA=1.0) in ALL arms; the distributions were reported as-is, no adhesion parameter was touched, and the O-P4 FAIL was registered as the R9 finding |
| Disk pressure | compress completed-stage logs before any deletion; deletions only on explicit user word | Honored. No zips, no deletions. Space note: `runs23/SHA256SUMS` lists `build/filopod_min.bin` (`f5814ebf...`) and `build/op1_dyn.ergo` (`45902252...`) under a `build/` directory that is absent from the current tree (compile artifacts, reproducible from the certified engine; flagged this doc pass) |

## Known limitations / R10–R11 handoff

1. **Anchor/tip machinery is minimal by design.** Tip adhesion is a
   fixed-target R6 slip bond at the XTIP=9.0 plane with one bond per
   filament; ~97% of ruptures occur above the slip scale — the
   registered O-P4 root cause. There is no membrane tube, no tip
   complex, no load-sharing across tip bonds. Strengthening the
   tip-linkage pathway (more/harder tip bonds, slower rupture, or
   load-sharing) is the registered R10/R11 design target; any such
   change is a new channel requiring its own oracle, not a tuning of
   PTIPA.
2. **Anchor unbind-transfer caveat (carried from the brush/anchor
   machinery).** Anchored-monomer unbind handling is as registered in
   the parent chain; R9 configs run the brush ratchet footprint, where
   the certified machinery applies. The R10 constructed-unit configs
   additionally freeze track kinetics (see MYOSIN_LAW.md known
   limitations) — no R9 arm exercises anchored-barbed-unbind transfer.
3. **Analyzer replay ambiguity — status.** The R8-registered
   verdict-insensitive prepend-ambiguity caveat carries over; in R9 it
   is BOUNDED TWO WAYS: (a) conservative flagged-dump exclusion with all
   flagged dumps pre-burn-in on all four arms (post-burn-in measurement
   window reconciles exactly), and (b) engine-native lpol ground truth
   agreeing with the replay ≤ 0.0013 on every reported quantity. The
   chained-prepend fallback (demand 7 > static PREP_DMAX=3.0 reach in
   the dense control cluster-growth phase) is registered in
   `replay_r9.py` with invocation counting; exact per-dump certification
   is retained. Replay tightening remains an R10+ candidate amendment
   (branched-mesh case still open from R8-f).
4. **Cert-header known issue (registered at R9-b, deferred).** The
   parent-carried INIT_CERT header wording "pure additions" overclaims
   vs a PADH=1 baseline (aggregate totals only; explainable, no physics
   defect). Deferred to a doc amendment; no hash-changing edit was made.
5. **Provenance caveat.** The R9-b s77031 parent reference logs were
   produced under R9-b (not archived from R8-b — none existed on the
   brush config). Registered for the record; all six child==parent
   comparisons are internal to R9-b and hash-verified.
6. **edit_file batching hazard (process).** Confirmed again in R9-a
   (builder self-detected and re-audited) and noted at R9-d: batched or
   duplicate edit_file calls to the same file in one message can
   silently fail or clobber. One edit per message per file, then
   re-grep — the rule under which this doc pass was written.
7. **Single-geometry certification.** All R9 conclusions are for the
   5×8 seeded cluster, F_EXT=1.0 piston, NM=400 census, seeds
   {77031, 84950}. The O-P4 FAIL is a statement about THIS tip
   architecture; the registered response is architectural (R10/R11),
   not parametric.

## Artifacts (all under `/mnt/agents/output/actin_phasespace/`)

- Engine: `phi4/runs23/filopod_min.ergo` SHA256
  `6a343fdef82c16a74a8e862b33d44cd88bb4101b9079bc684d3f38b70f498d8f`
  (3499 lines, +525/0; recomputed). Parent `phi4/runs22/bundle_pol.ergo`
  SHA256 `fb1c8d281b72816304a8bf13e9b66e815ec75200c20803c31879011b46507935`.
  Code bundle `actin_phasespace/r9_repo.bundle` SHA256
  `ab2ad7d8ebaf06f5198b6861ab2fa0d40013f65e89218693a7aac395fe984a0a`.
- Oracle: `phi4/plan_filopod.md` (registered before build; RNG block
  corrected 6900–6963; FD bead-96 amendment line).
- R9-a: `phi4/runs23/static_cert/` (mirror_off/cert_base_bpol{1,2}/
  fd_{tip,xl,adh}_{plus,minus} .ergo/.bin/.out), `phi4/runs23/smokes/`
  (op1_50k `007e6b2b...`, clu_50k `79f5220b...`), top-level
  `runs23/SHA256SUMS`.
- R9-b: `phi4/runs23/gates/` (6 child + 6 parent 300k logs + .status +
  work/ variants; child hashes `16c9db1c...`/`5636a7eb...`/`b84d72e1...`/
  `c5444043...`/`cb3e60fe...`/`8ddb802b...`, each equal to its parent).
- R9-c: `phi4/runs23/r9c/` — bundled/control .ergo/.bin/logs (.status)
  `2144637e...`/`e5a818e4...`; `clu_books.py` SHA256
  `c4ad58d4142a9bd497900d8b1dcdf59b0842b27a6d740f95537c9ef6c74c9309`;
  `r9c_op4_analysis.py` SHA256
  `f588476b67921ab385b76287d73d3298524338c051819a836719e6439bed0ecc`;
  `r9c_op4_report.txt` (single-seed O-P4 + ranges).
- R9-d: `phi4/runs23/r9d/` — s84950 logs `342c9f16...`/`c59f9684...`;
  lpol verification `90b95d84...` + `filopod_min_lpol.variant.ergo`
  (`eebedc93...`) + PLPOL=0 compile proof; `R9D_REPORT.md`;
  `r9d_op4_pooled.py`/`.txt` (formal verdict);
  `r9d_op4_analysis_s84950.txt`; `replay_r9.py` SHA256
  `5b5fa8fb6b2804517dd0e1b0cb6bb5b2c1ddbbcb0f4bab3828f6d8f6cf3f0b8e`;
  `r9d_pol.py` SHA256
  `40edf225d4973a547c782d265bc2f6d51bfa4dff07c08e8d93523e18935c2747`;
  `r9d_op4_pooled.py` SHA256
  `6d9b9178ef277b904ad8f36a311b7f33065585ac9d211c3b996137774ed2da98`;
  per-arm replay outputs `replay_{b7,c7,b8,c8}.txt`; `SHA256SUMS`.
- Top-level analyzer: `phi4/runs23/clu_smoke_analysis.py` SHA256
  `980ddd41af96cbec5b7e145771b50a7a52542b06a09cffb699bd3e7d249fcfb9`.
- Execution record: `actin_phasespace/plan.md` R9 Stage 0–4 + R9
  disposition (CLOSED WITH FINDING, user directive 2026-09-03).

## Reproduction

```bash
# toolchain: certified Ergo compiler (python3 -m core), frozen per Stage-0
# runner: runs20/runner_r6.sh (wipe-immune /tmp-stream pattern; writes .status)
# engines: runs22/bundle_pol.ergo (parent) -> runs23/filopod_min.ergo
# R9-a: compile static_cert/*.ergo, diff mirror_off.out vs R8 mirror (3f3269db...);
#       FD from fd_{tip,xl,adh}_plus/minus outs: |analytic - (E+ - E-)/2e-6| < 1e-8
# R9-b: gates/work/driver.sh; child==parent byte-identity per row (sha256sum)
# R9-c: runs23/r9c configs; books: r9c/clu_books.py; O-P4: r9c/r9c_op4_analysis.py
# R9-d: runs23/r9d configs; pooled verdict: r9d/r9d_op4_pooled.py;
#       polarization replay: r9d/replay_r9.py + r9d/r9d_pol.py;
#       lpol validation: filopod_min_lpol.variant.ergo PLPOL=1, then
#       grep -v '^lpol ' r9d_lpol_verify_s77031.log | cmp - r9c/r9c_bundled_s77031.log
```

## Conclusions for the phase-space map

The minimal parallel bundle assembles, polarizes (1.56× live
enrichment, young-link carried, R8 rotation timing reproduced), closes
every book, and is instrument-exact — and it is NOT force-bearing:
traction is bottlenecked at the tip slip-bond interface, which bundling
does not change (O-P4 FAIL, pooled magnitude ratios 0.9506/0.9436,
signed offset +0.3406 p=0.0317 satisfying neither registered limb).
Bundling halves crosslink loading and turnover and shortens the bundled
filaments it keeps; it does not protect incumbents. The registered
design target for R10/R11 is the tip-linkage pathway. Engine certified
and frozen; parent of record for R10 (myosin_unit.ergo, MYOSIN_LAW.md).
