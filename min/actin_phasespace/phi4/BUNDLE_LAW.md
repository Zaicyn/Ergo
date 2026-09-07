# BUNDLE_LAW.md — φ4.10 bundle polarity: parallel and antiparallel architectures (R8) certification

Certified: 2026-09-03 (all stages, R8-a through R8-f; R8-f executed under
the force-first doctrine as a diagnostic — books PASS, signs PASS,
distributions reported as ranges). Engine lineage:
pop_fpt.ergo (φ4) → brush_c400g → brush_br400 → brush_bra (S4 anchored
branching) → brush_bra_x → brush_bra_r (hold-release piston) → brush_bfm
(per-filament formin channel) → brush_adh (PADH substrate adhesion channel)
→ brush_xlk (PXL filamin-like crosslink channel) → **bundle_pol** (PBUND
bundle-polarity gate on crosslink attach). Final source
`phi4/runs22/bundle_pol.ergo` (2974 lines, +245 vs parent, 0 parent lines
touched, 8 additive hunks), SHA256
`fb1c8d281b72816304a8bf13e9b66e815ec75200c20803c31879011b46507935`, merge
commit `d84f3c6` in the live repo. Parent: certified `brush_xlk.ergo`
(SHA256 `a3ed43347392aa97f7ad2bde5ad0d7c1ce0e09e244220cedba59edc7ea46944a`,
merge `7ff0566`). Oracle: `plan_bundle.md` (O-B1..O-B5 plus registered
Amendment B-1), registered 2026-09-03 before engine build and ensembles.
All certification arms run PADH=0 and XLNF=0 — the R7-certified slip law
(O-X6, β_X = 0.995310 ± 0.002709) **carries over by registration**: the
force and rupture code paths are untouched, so R8 runs no XLNF=1 law grid
(~56 MB logs instead of ~800 MB). Method: swarm delegation authorized by
the 2026-09-02 workflow amendment; stage order remained lock-step — gates
before smokes, smokes before ensembles, the O-B4 investigation and
ground-truth verification before any amendment. All durable artifacts
under `/mnt/agents/output/actin_phasespace/`. Runs: `runs22/` (R8-a
static_cert + 50k smokes, 2 O-B1 gate logs, 2 constructed-pair logs, 1
brush smoke, 3 selectivity-ensemble logs reusing the R8-d arm, 3
ground-truth verification logs, 2 branched-mesh diagnostic logs + 2 lpol
cross-check logs). Analysis is reproduced by
`runs22/stage_i_analysis.py` (brush/pair analyzer, 1379 lines, SHA256
`4d2b399c...`), `runs22/r8c/r8c_constructed_analysis.py` (constructed
census, 354 lines, SHA256 `529ca904...`),
`runs22/ob4_investigation/ob4_age_analysis.py` (age-stratified
persistence, 610 lines, SHA256 `53799a77...`),
`runs22/ob4_verification/lpol_analysis.py` (engine-native ground truth,
393 lines, SHA256 `70158f94...`), and the R8-f branched-mesh tooling
`runs22/r8f/stage_i_branched.py` (475 lines, SHA256 `5e9ed1c9...`),
`runs22/r8f/r8f_age_analysis.py` (232 lines, SHA256 `43e959a5...`), and
`runs22/r8f/r8f_pinning_analysis.py` (138 lines, SHA256 `af127851...`);
analyzer self-tests in `runs22/SELFTEST_I.md` and
`runs22/ANALYZER_I_VALIDATION.md`.

## The question

R7 certified transient filamin-like crosslinks and a contractile cohesion
law. But every R7 link is accepted regardless of the relative orientation
of the two filaments it connects: the mesh has no polarity organization.
Stress fibers need **antiparallel** organization; filopodia need
**parallel** bundles. A contraction (R10 myosin) or protrusion (R12)
result is uninterpretable if the underlying bundle polarity is unknown or
an artifact of sign conventions.

**R8 asks whether the engine can distinguish, stabilize, and measure
parallel versus antiparallel actin bundles — with zero polarity sign
errors — so that R10 myosin contraction and R12 filopodium protrusion can
each be certified against the architecture they require.**

Polarity is certified both as an instrument (the cosθ record and its
replay) and as a selection channel (the deterministic attach gate), before
any motor is introduced.

| stage | arm | purpose |
|-------|-----|---------|
| R8-a | build + static/FD cert + review/verify + merge | PBUND channel on the certified brush_xlk parent; O-B2 statics |
| R8-b | O-B1 gates | PBUND=0 bit-identity to certified parent, both arms |
| R8-c | constructed-pair smoke (PCERT seeded geometry, PBUND=1/2) | O-B2 runtime zero sign errors, O-B3 lifetimes, O-B5 |
| R8-d | brush smoke (PBUND=1, PBR=0, FORMIN=0, PADH=0, F=1, seed 77031, 1M) | occupancy/turnover sanity; first selectivity read |
| R8-e | selectivity ensemble PBUND∈{1,2} × seeds {77031,84950}, F=1, 1M, XLNF=0 | decides O-B4 (as amended by B-1) against the archived R7 control; O-B5 on all logs |
| R8-f | PBUND=2 in the branched mesh (PBR=1, FORMIN=0, PADH=1, F=1, seeds {77031,84950}) | integration diagnostic (not a gate): books PASS, signs PASS; distributions measured as ranges |

## Mechanism as certified

The bundle-polarity channel is a deterministic acceptance gate on the
certified R7 crosslink attach path. The crosslink element itself —
spring, Bell slip rupture, RNG discipline, pool and inventory machinery —
is unchanged from R7.

- For a candidate crosslink between monomer I of filament F1 and monomer J
  of filament F2, the **local tangent** of each filament at the linked
  monomer is

  `t(B) = unit( P(B+1) − P(B−1) )`   (directed pointed → barbed along the
  contour, via the engine's PREVM/NEXTM links; head bead of monomer M is
  `2*M−1`).

  The link polarity is `cosθ = t(I)·t(J) ∈ [−1,+1]`: parallel → +1,
  antiparallel → −1, orthogonal ≈ 0.
- **Eligibility:** both monomers must be interior (PREVM > 0 and NEXTM >
  0, contour distance ≥ 1 from each end) and both filaments must have
  contour length ≥ 4 monomers (FILLEN ≥ 4); otherwise the gate reports
  ineligible (POLOK=0, cos=0) and the candidate is rejected. The
  end-to-end filament axis is a secondary instrument quantity (offline,
  from gm records), not part of the acceptance rule.
- **Polarity-selective acceptance** (POLGATE subroutine, called after the
  R7 attach Bernoulli and pool checks, before commit):
  - PBUND = 0: unselective — the cosθ code path is not reached; no
    records; no draws; byte-identical to the certified R7 parent.
  - PBUND = 1: parallel-preferring — a candidate that passes the R7
    attach Bernoulli is accepted iff `cosθ ≥ +COSB`.
  - PBUND = 2: antiparallel-preferring — accepted iff `cosθ ≤ −COSB`.
- Acceptance is **deterministic given cosθ: ZERO new RNG draws**, no
  changes to existing slot usage (the R7 span 4700–6873 and all legacy
  spans untouched; RNG scan 25 = 25 sites). On rejection no link forms;
  the candidate set is re-evaluated next step under the parent's normal
  attach draw. Rejected candidates are not sticky and do not modify the
  eligibility of other pairs.
- The gate adds **no new engine state**: links carry no polarity tag
  (polarity is a function of geometry, recomputed from positions).
  Attach/rupture/inventory semantics are exactly R7's; the R7 inventory
  oracle (xlka/xlkr/xlks reconstruction) applies unchanged.

Registered parameters:

| parameter | value | role |
|---|---:|---|
| `PBUND` | 0/1/2 | channel toggle: 0 = off/unselective (≡ R7 parent), 1 = parallel, 2 = antiparallel |
| `COSB` | 0.5 | polarity acceptance threshold on \|cosθ\| |

All R7 crosslink parameters (RXLK, KXLK, KONX, KOFFX, FBX, DX0, SMAXX,
XLMAXF, MAXXL), R6 adhesion parameters, and parent parameters are
unchanged.

Instrumentation (WRITE-only):

```text
bpol STEP I J cos      one record per ACCEPTED attach, PBUND>0 only; cos %.6f
```

PBUND=0 emits nothing. All R7 records (xlka/xlkr/xlks, xlkf under XLNF)
and parent records (census, gm, fil, pstn, xpt, geo, rel) unchanged.
Offline, `stage_i_analysis.py` computes live cosθ from gm dumps (link
replay from xlka/xlkr + gm positions, the O-X3a-certified pattern, with an
exact-cover solver for unrecorded pointed-end prepends constrained by
fil-record lengths), polarity-class populations, per-class lifetimes,
inter-filament spacing, and sliding displacement.

**Diagnostic variants (runs22 only, NOT in the certified engine):** two
purely additive, inert-by-construction instruments were certified and used
inside `runs22/` but live nowhere in `bundle_pol.ergo`:
`PCERT=0/1` (`runs22/r8c/r8c_pairs.variant.ergo`, SHA256 `311a05d4...`)
seeds the constructed-pair geometry under MIRROR=0 dynamics for R8-c, and
`PLPOL=0/1` (`runs22/ob4_verification/*.variant.ergo`) emits the
engine-native ground-truth record `lpol STEP M1 M2 AGE OK COS` at gm-dump
cadence for the O-B4 verification. Both are proven dynamics-neutral by
byte-identity (below); the certified engine is untouched.

## Amendment registered during the rung

One amendment was registered in `plan_bundle.md` and is part of the
certified configuration:

**B-1 — O-B4 re-instrumented (2026-09-03, user-registered).** Trigger:
R8-e returned live-fraction enrichment 1.58/1.59 (PBUND=1) and 1.62/1.64
(PBUND=2) vs the registered ≥ 2.0 — O-B4 FAIL as originally written, with
every secondary window satisfied, 100% attach-class purity, and zero sign
errors on all arms. STOP registered per protocol; root cause investigated
(age-stratified analysis) and then verified against engine ground truth
(the lpol instrument, user-directed) before registration. The unstratified
live-fraction criterion conflated selection with persistence: the gate is
perfectly selective at attach, but crosslinked filament pairs
rotationally diffuse at ~54–56° RMS per 500-step dump interval, so
polarity class memory decays 2–3× faster than links turn over and the
observed ~1.6 is the physical steady-state ceiling for ANY working gate.
O-B4 as amended has three tiers, all measured on the R8-e ensemble plus
the ground-truth runs:

1. **Primary (selection):** intended-class fraction among live links with
   age < 250 steps ≥ 2.0× the R7 control's overall class fraction.
2. **Secondary (persistence):** class-persistence half-life ≥ 150 steps
   AND ≥ 0.3× the arm's lifetime median.
3. **Tertiary (consistency):** steady-state enrichment within 5% of the
   one-compartment persistence×turnover mixture prediction — reported as a
   diagnostic; flagged as self-referential and never to be used as the
   sole gate.

Also registered with B-1: (a) the analyzer replay prepend-ambiguity
caveat is verdict-insensitive (fraction shifts ≤ 0.005; ~1% flagged
samples); replay tightening deferred as an R9+ candidate amendment;
(b) the lpol instrument lives only in `runs22/ob4_verification/`
variants; (c) the age cutoff must be ≤ 250 — pooling to < 500 dilutes
PBUND=1 below 2.0 on physics, not on gate defects.

## Certification chain

1. **Static/FD certification passed (R8-a)** (`runs22/SELFTEST_I.md`,
   `runs22/static_cert/`, `runs22/smokes/`). Fresh Ergo compile PASS.
   MIRROR constructed-pair sign battery with **zero sign errors**
   (`static_cert/bpol{1,2}_mirror_pxl1.out`): PBUND=1 — parallel pair
   accepted cos +1.000000, antiparallel pair rejected cos −1.000000;
   PBUND=2 — exact reverse; eligibility negatives (single-monomer
   filament, 3-mer, end monomer) all `ok 0 acc 0` under both channels.
   Spring re-certification on the constructed pairs: CERT_XL `exl` =
   0.25 = KXLK·(d−DX0)² exact at pure-x stretch d=2.0; differential force
   ±1.0 x̂ bitwise; central FD error **7.62e-10 < 1e-8**. RNG scan: 25 =
   25 RAND sites, span 4700–6873 untouched, zero draws added. MIRROR
   PBUND=0 dumps byte-identical to the parent lineage dumps (SHA256
   `3f3269db...` PXL=0 and `d3da0428...` PXL=1 — both equal to the parent
   outs). 50k equivalence smoke: PBUND=0 ≡ parent **byte-identical**
   (SHA256 `007e6b2b...` for both `smokes/bpol0_50k.log` and
   `smokes/parent_50k.log`; crosslink channel active, zero bpol records).
   Runtime gate conformance in the 50k channel smokes: 369/369 (PBUND=1)
   and 416/416 (PBUND=2) xlka=bpol records, cos windows clean, inventory
   exact, max\|netf\| = 0.
2. **Independent review GO** (all 8 checklist items PASS; sign convention
   traced through the parent source — NEXTM points pointed→barbed;
   runtime cross-check gate cos 0.770929 vs gm-axis dot 0.770689). One
   spec-ambiguity flag (a dead "end-bead tangents" phrase in §4.1 of the
   oracle): strictest reading accepted, one-line clarifying note, non-
   blocking. **Independent verification 6/7 reproduced** including
   re-execution of all cert binaries; the single non-reproduced item
   (binary byte-hash recompile) is unattainable *by toolchain design* —
   `driver.py:239` embeds a random tempfile name as an STT_FILE symbol,
   so exactly 8 of 74,216 bytes differ between any two compiles, all
   other bytes bit-identical. **Registered process note:** the certified
   artifact is the engine source hash; binary hashes are recorded
   as-shipped (the same property held for all R6/R7 binaries; compiler
   frozen per the user's Stage-0 verification: 30/31 toolchain files
   byte-identical to the user's upload, the single delta being the user's
   own FMA-SUB codegen fix). Merged as commit `d84f3c6`.
3. **O-B1 gates passed (R8-b)** on the merged source: both arms
   byte-identical to the archived R7 parent over 300k steps — gate 1
   (PBR=0, FORMIN=0) log SHA256 `a67e3bbf...` and gate 2 (PBR=1,
   FORMIN=1) log SHA256 `db4b42fb...`, **exactly the R7 (= R6) gate
   hashes** (lineage continuity confirmed); attempt=1, FINAL×2, NUL=0,
   zero bpol records; variant diffs = exactly one anchored line each.
4. **Analyzer adaptation certified (parallel with R8-b).**
   `stage_i_analysis.py` (SHA256 `4d2b399c...`) preserves the certified
   stage_h streaming architecture and adds bpol parse, live-cosθ replay
   at gm dumps, polarity-class populations, per-class lifetimes/spacing/
   sliding, and bpol-vs-replay consistency. Replay topology EXACT
   (exact-cover solver for unrecorded pointed-end prepends, constrained
   by fil-record lengths; certified 0 errors at 300/300 gm dumps on real
   logs). Synthetic validation 8/8 exact (parallel/antiparallel
   Δcos=0.0000, orthogonal drift, rupture lifetime exact, no-bpol parent
   mode byte-identical to stage_h, prepend/branch/nucleation-recycle
   reconciliation exact); real 50k smokes: 369/369 parallel and 416/416
   antiparallel attach classes (100%); end-to-end exactness proof
   Δcos = −1.2e-07 at dump-step attach; shared metrics byte-identical to
   stage_h on identical logs (`runs22/ANALYZER_I_VALIDATION.md`).
5. **Constructed-pair smoke passed (R8-c)** (`runs22/r8c/`, analyzer
   `r8c_constructed_analysis.py`, SHA256 `529ca904...`). PCERT variant
   inertness proven first: PCERT=0 50k smoke byte-identical to the parent
   (`007e6b2b...`), MIRROR sign battery + FD re-run byte-identical to
   static_cert. Constructed-pair smokes (PCERT=1, F_EXT=0, 300k steps):
   PBUND=1 — **133 attaches, cos ∈ [+0.502465, +0.998995], 100%
   parallel, zero sign errors**; PBUND=2 — 87 attaches, cos ∈
   [−0.993064, −0.500579], 100% antiparallel; eligibility negatives: zero
   attaches in both arms (structural proof; min \|cos\| > 0.5 observed).
   **O-B3 PASS both arms, both readings:** lifetime medians 895.0
   (n=133, max 7050) and 831.0 (n=87, max 6353); survival at 10× median
   = 0; longest-lived < 20× median; ratios vs the R7 brush-smoke median
   542.5: 1.6498/1.5318 (registered factor window [0.5, 2.0]: IN); ratios
   vs the slip-law prediction at the measured stored force
   (⟨\|F\|⟩ = 0.7799/0.7019 ⇒ predicted medians 1271.2/1374.3):
   0.7041/0.6047 (IN). Ruptures slip-dominated (107/74 slip of 133/87).
   **O-B5 PASS both arms:** constructed census (39 monomers) conservation
   exact over 600+600 censuses, ghost scan clean, crosslink inventory
   exact including the predicted single t=0 orphan xlkr (INIT_CERT cert
   link; ruptured at step 4623 cause 2 / step 5320 cause 1), max\|netf\|
   = 0 over 600+600 windows, FINAL present, NUL=0, nfil continuity exact.
   Registered non-gating caveat: eligibility flux is thin in the
   constructed geometry (attach rate 4.7e-4/3.1e-4 per 500-step window;
   windows with any attach 112/540 and 76/540; short constructed
   filaments fluctuate around the FILLEN ≥ 4 floor) — measurable, no
   STOP; a geometry amendment is available if richer constructed
   statistics are ever needed.
6. **Brush smoke passed (R8-d)** (`runs22/r8d/`, log SHA256
   `bbcc44da...`, 56.7 MB, attempt=1). PBUND=1, unbranched brush, F=1,
   seed 77031, 1M steps. O-B5 clean; instrument conformance perfect
   (xlka = bpol = 8876, every attach parallel, zero sign errors, cos
   windows hold exactly); occupancy 0.3088 (≫ the registered 0.05 floor),
   turnover continuous (4523/4520 post-burn-in attach/rupture events),
   balance 0.0007, drift 0.0524 — all O-X2 windows IN. Lifetime median
   594 vs control 544 (1.09×); rupture-cause shift: monomer-unbind
   ruptures 71 vs 1514 in the control — bundling protects endpoints.
   First selectivity read: live parallel fraction 0.3787 vs the R7
   control 0.2396 → **1.58×** (below the then-registered 2.0 — early
   warning noted); antiparallel depleted 0.61×. The parallel-bundled
   brush stands taller at force balance (geo stationary mean 49.366 vs
   41.882 control).
7. **Selectivity ensemble completed; O-B4 FAIL as registered; STOP
   (R8-e)** (`runs22/r8e/`, decision record `OB4_DECISION.txt`, SHA256
   `532c40aa...`). Three new runs (PBUND=1 seed 84950; PBUND=2 seeds
   77031/84950) plus the R8-d reuse arm; archived R7 control recomputed
   from `runs21/smokes/xlk_on_f1_s77031.log` with the identical replay
   (no new R7 runs; control fractions parallel 0.2396 / antiparallel
   0.2778 / orthogonal 0.4825 over 7011 link-dump samples, exact match to
   the R8-d registered control). All four arms clean (O-B5, instrument
   conformance, zero sign errors, attach-class purity 100%, cos windows
   [+0.500005, +0.999971] and [−0.999968, −0.500036]) and every secondary
   window satisfied (occupancy 0.2758–0.3170 ≫ 0.05; balance ≤ 0.0022;
   drift ≤ 0.1569; events ≥ 4116/4117; lifetime medians 594/595/501/493
   = 1.09/1.09/0.92/0.91× control) — but live-fraction enrichment
   **1.5806/1.5881 (PBUND=1) and 1.6206/1.6433 (PBUND=2), all below the
   registered ≥ 2.0: formal verdict O-B4 FAIL.** The criterion was not
   relaxed; the numbers were reported cleanly for the amendment decision,
   and the persistence-instrument investigation launched before any
   amendment per the standing snag protocol.
8. **O-B4 instrument investigation completed**
   (`runs22/ob4_investigation/ob4_report.txt`, SHA256 `c0f4b262...`;
   analyzer `ob4_age_analysis.py`, SHA256 `53799a77...`; replay machinery
   imported unmodified; reproduces the registered numbers exactly).
   Age-stratification shows the gate is perfectly selective where it acts:
   intended-class fraction in the age < 250 bin 0.6113/0.6088 (PBUND=1)
   and 0.6873/0.7082 (PBUND=2) → enrichment 2.551/2.541 and 2.474/2.549,
   all ≥ 2.0; by age ≥ 500 the live population is statistically
   indistinguishable from control. Class-persistence half-lives
   210/213/283/288 steps = 0.35/0.36/0.56/0.58× the arms' lifetime
   medians. A one-compartment mixture of the measured persistence curve
   and lifetime distribution predicts steady-state enrichment
   1.564/1.590/1.611/1.618 vs observed 1.580/1.588/1.620/1.643 (obs/pred
   1.011/0.998/1.006/1.016) — the registered unstratified 2.0 was
   physically unreachable; ~1.6 is the ceiling. Control age structure
   mildly non-flat (max bin deviation 0.052); conclusions hold under both
   denominators; sensitivity max per-bin shift 0.0038. External review
   (user-relayed) concurred: adopt the age-stratified criterion.
   **User directive: verify the 1.6 independently first** — "if it is we
   know the timing. Rotation is basically inevitable here, we just need
   to measure how much it rotates over time."
9. **Ground-truth verification completed (user-directed)**
   (`runs22/ob4_verification/`, `OB4_VERIFICATION.md` SHA256
   `9bd7b792...`, `ob4_lpol_verification.txt` SHA256 `b107229f...`,
   analyzer `lpol_analysis.py` SHA256 `70158f94...`). An engine-native
   records-only instrument `lpol STEP M1 M2 AGE OK COS` (emitted at
   NDIAG=500 gm-dump cadence for every live crosslink; tangent definition
   identical to the analyzer replay; zero new RNG draws) was added as
   additive-only variants of the R8 engine (+45 lines) and the R7 parent
   (+47 lines), guarded by a new inert parameter PLPOL (default 0).
   **Dynamics-neutrality proven by construction: for all three
   verification runs (PBUND=1 s77031, PBUND=2 s77031, R7 control), the
   logs stripped of lpol lines are BYTE-IDENTICAL to the certified logs**
   (13,035 / 12,386 / 30,891 lpol records removed, respectively; also
   prefix-verified on a 60 s pilot). Ground truth vs replay: steady-state
   intended fraction 0.3795 vs 0.3787 (PBUND=1) and 0.4515 vs 0.4502
   (PBUND=2); enrichment **1.5740 vs 1.5803** (PBUND=1) and **1.6242 vs
   1.6202** (PBUND=2); control fractions within 0.0016; age-bin fractions
   within 0.0051; class-persistence half-lives **212.0/284.1 steps vs
   replay 210/283**. The replay analyzer is **validated as an instrument**
   on these logs, and its numbers for the seed-84950 arms carry full
   instrument weight. Rotation timing certified (engine ground truth):
   per-link RMS rotation **55.85° (PBUND=1) / 53.86° (PBUND=2) /
   53.6° (control) per 500-step dump** — roughly age-independent
   (~50–62° in every 250-step age bin from 500 to 2000), i.e. universal
   thermal diffusion, not a gate effect; mean-cos decorrelation
   τ_cos ≈ 130 (PBUND=1) / 295 (PBUND=2) steps; per-link first-class-exit
   Kaplan–Meier medians 405/428 steps vs link-lifetime medians 594/501.
10. **Amendment B-1 user-registered; O-B4 PASS; R8-e CERTIFIED.** Scored
    on the R8-e ensemble plus the ground-truth runs: **primary**
    young-link (age < 250) enrichment 2.55/2.54 (PBUND=1, seeds
    77031/84950) and 2.47/2.55 (PBUND=2) — PASS both channels, both
    seeds; **secondary** half-lives 212 = 0.36× (PBUND=1) and 284 = 0.57×
    (PBUND=2) the lifetime medians against the ≥ 150-step and ≥ 0.3× bars
    — PASS; **tertiary** steady-state obs/pred 0.998–1.016 against the 5%
    bar — PASS (diagnostic-only, self-referential, never the sole gate).
    The registered rotation-timing numbers (~54–56° RMS/dump, τ_cos ≈
    130/295 steps, half-lives 212/284 steps) are certified instrument
    outputs feeding R9/R10 design (bundle polarity memory vs myosin duty
    cycle). Age cutoff ≤ 250 locked; lpol kept out of the certified
    engine; replay tightening deferred to R9+ candidates.
11. **Branched-mesh diagnostic completed (R8-f)** (`runs22/r8f/`,
    `R8F_REPORT.md`, SHA256 `f7965feb...`), executed under the
    force-first doctrine: HARD checks are forces/books/signs only;
    distributions are measured and reported as ranges. PBUND=2,
    PBR=1, FORMIN=0, PADH=1, F_EXT=1, seeds {77031, 84950}, 1M steps,
    XLNF=0, anchored variant edits only (diff-verified against the
    certified engine; recompiles differ only in the 8-byte tempfile
    symbol). **Books PASS both seeds** (monomer conservation exact at
    every census incl. an independent awk recount; ghost scan 0;
    crosslink inventory exact — xlka 12166/12270, open-at-final 9/7
    matching the final NXL; adhesion inventory exact — adha−adhr = 3/2 =
    final nadh; max\|netf\| = 0 over all 2000 xlks windows per seed;
    nfil continuity event-exact, 0/1999 mismatched windows, max window
    \|Δnfil\| 14/6 vs 15 in the R7-f parent — normal branching dynamics).
    **Signs PASS both seeds**: 24,436 bpol records, every attach cos ≤
    −0.5 (windows [−0.999981, −0.500050] / [−0.999991, −0.500032]),
    100% antiparallel attach purity. The R7-f MAXXL=24 watch item
    **resolves**: 0/1000 pinned windows in both seeds. Measured findings
    (antiparallel enrichment 1.705–1.706× in the branched architecture,
    tension, rupture mix, persistence timing) are reported as ranges in
    the R8-f section below.

## The O-B4 selectivity saga

The scientific centerpiece of R8 is that the registered selectivity
criterion failed, was stopped per protocol, and was re-registered only
after the failure was explained and independently verified against engine
ground truth. The certified statement is sharper than the original
registration: **selection and persistence are separate physical
quantities**, and the gate is perfect at exactly one of them.

### Act 1 — the premise fails cleanly (registered stop)

The registered O-B4 asked the *live-link population* to carry the gate's
signature: intended-class live fraction ≥ 2.0× the unselective control.
All four R8-e arms enriched their intended class — 1.58/1.59 (parallel),
1.62/1.64 (antiparallel) — reproducibly, with 100% attach-class purity
and every secondary window green, and reproducibly short of 2.0
(`runs22/r8e/OB4_DECISION.txt`). Opposite-class depletion ran 0.56–0.61×
on all arms. Per the registered stop protocol the criterion was not
relaxed; R8-f and docs were blocked pending investigation.

### Act 2 — the investigation: rotation erases the memory, not the selection

`runs22/ob4_investigation/ob4_report.txt` stratified the live population
by link age (age = dump step − xlka attach step):

| arm | age<250 intended frac | enrichment | age ≥ 500 | half-life | lifetime median | mixture pred | observed |
|---|---:|---:|---|---:|---:|---:|---:|
| PBUND=1 s77031 (R8-d) | 0.6113 | 2.551 | ≈ control | 210 st (0.35×) | 594 | 1.564 | 1.580 |
| PBUND=1 s84950 (R8-e) | 0.6088 | 2.541 | ≈ control | 213 st (0.36×) | 595 | 1.590 | 1.588 |
| PBUND=2 s77031 (R8-e) | 0.6873 | 2.474 | ≈ control | 283 st (0.56×) | 501 | 1.611 | 1.620 |
| PBUND=2 s84950 (R8-e) | 0.7082 | 2.549 | ≈ control | 288 st (0.58×) | 493 | 1.618 | 1.643 |

Fresh links are 61–71% in-class (vs the control's 24–28%); within one
lifetime the class memory is gone. Polarity decorrelates 2–3× faster than
links turn over, so the steady-state live population is a mixture
dominated by old, decorrelated links — a one-compartment
persistence×turnover model predicts the observed ~1.6 to within 1.6%.
The 2.0 unstratified bar was unreachable *by construction* for any gate
that is perfect at attach: selection happens at birth; persistence is
eroded by universal thermal rotation.

### Act 3 — ground truth confirms the instrument before the amendment

Before registering anything, the user directed an independent check of
the 1.6 and of the rotation timing. The lpol engine-native record (same
tangent math as the replay, zero new draws, additive-only variants) made
the check decisive twice over: (i) stripped-log byte-identity on all
three verification runs proves the instrument is dynamics-neutral by
construction; (ii) ground truth reproduces the replay to ≤ 0.006 in
enrichment, ≤ 0.005 in age bins, and 2 steps in half-lives — the replay
analyzer is validated as an instrument, and the rotation timing is
engine-measured: ~54–56° RMS per 500-step dump in both gated arms and
53.6° in the ungated control, age-independent; τ_cos ≈ 130/295 steps;
first-class-exit KM medians 405/428 steps. A crosslinked filament pair
randomizes its relative orientation in roughly one to two dump intervals
(~250–500 steps); the gate's enrichment survives in steady state only
because fresh links are continuously attached in-class.

### Act 4 — Amendment B-1: three tiers, all PASS

B-1 re-instrumented O-B4 to match the physics: primary young-link
selection (≥ 2.0× at age < 250: measured 2.55/2.54 and 2.47/2.55),
secondary persistence (half-life ≥ 150 steps and ≥ 0.3× lifetime median:
measured 212 = 0.36× and 284 = 0.57×), tertiary mixture consistency
(obs/pred 0.998–1.016, diagnostic-only). **O-B4 PASS under B-1; R8-e
certified.** Registered alongside: the ≤ 250-step age cutoff is locked
(widening to < 500 dilutes PBUND=1 below 2.0 on physics, not gate
defects); the tertiary tier is self-referential and never a sole gate.

## R8 laws

### L-B1 The polarity gate is perfectly selective at attach (O-B2)

Every accepted attach is in the intended class, in every geometry and at
every stage: MIRROR sign battery exact (parallel accepted cos +1.0,
antiparallel rejected cos −1.0 under PBUND=1; exact reverse under
PBUND=2; eligibility negatives never attach); 133/133 parallel and 87/87
antiparallel in the constructed pairs; 369/369 and 416/416 in the 50k
channel smokes; 8876/8876 (R8-d) and 8770/9641/8209 (R8-e arms) in the
brush — **100% attach-class purity, zero sign errors, zero window
violations** across all 36k+ accepted attaches of the certification
program. Eligibility (interior tangent, contour ≥ 4) is enforced
structurally: ineligible candidates produce no attach and no record.

### L-B2 Polarity memory is erased by universal thermal rotation (O-B4 investigation + ground truth)

Crosslinked filament pairs rotationally diffuse at **~54–56° RMS per
500-step dump interval** (engine ground truth: 55.85° PBUND=1, 53.86°
PBUND=2, 53.6° unselective control) — age-independent (~50–62° in every
250-step age bin from 500 to 2000) and control-identical: rotation is
universal thermal diffusion, not a gate effect. Mean cos(age) decays
exponentially with **τ_cos ≈ 130 steps (PBUND=1) / 295 steps
(PBUND=2)**, starting from +0.507/−0.579 at age 125 and gone (< \|0.07\|)
by age ~500–750; class-persistence half-lives are **212/284 steps**
(anchored-curve crossing; replay 210/283), and per-link first-class-exit
KM medians are 405/428 steps against link-lifetime medians of 594/501.

### L-B3 Selection and persistence are separate physical quantities (O-B4 as B-1-amended)

The gate enriches the young (age < 250) live population **2.47–2.55×**
over control in both channels and both seeds, while the class-persistence
half-life is only 0.36–0.57× the link lifetime median. A one-compartment
mixture of the measured persistence curve and lifetime distribution
predicts the steady-state live-fraction enrichment to obs/pred
**0.998–1.016** — the observed ~1.6 unstratified enrichment is the
physical ceiling for ANY attach-perfect gate at this rotation rate, which
is why the original unstratified 2.0 criterion failed on physics, not on
gate defects. Opposite-class live fractions are depleted 0.56–0.61× on
all arms.

### L-B4 Gated bundles inherit the certified slip-law stability (O-B3)

Constructed-pair lifetimes (medians 895.0/831.0, n=133/87) sit inside
the registered factor window [0.5, 2.0] against both reference readings:
1.65/1.53× the R7 brush-smoke median at matched load, and 0.70/0.60× the
R7-certified slip-law prediction evaluated at the measured stored force
(⟨\|F\|⟩ ≈ 0.70–0.78). No instant collapse (survival at 10× median = 0
links alive), no immortality (longest-lived 7050/6353 < 20× median);
ruptures slip-dominated (80%/85% slip) as in R7. In the brush, lifetime
medians 594/595 (parallel) and 501/493 (antiparallel) vs control 544
(1.09/1.09/0.92/0.91×), with the rupture-cause shift expected of
bundling (monomer-unbind ruptures 71 vs 1514 in the paired R8-d/control
comparison — endpoints protected).

### L-B5 The gate preserves every conservation, inventory, and bookkeeping oracle (O-B1, O-B5)

PBUND=0 is byte-identical to the certified R7 parent at every level
tested: MIRROR dumps (SHA256 `3f3269db...`/`d3da0428...`), the 50k
dynamic smoke (`007e6b2b...`), and both 300k O-B1 gate arms
(`a67e3bbf...`/`db4b42fb...` — exactly the R7/R6 gate hashes). Across all
runs22 certification logs: monomer conservation exact (400 brush / 39
constructed) at every census, ghost scan clean, crosslink inventory exact
at every window (including the predicted t=0 orphan xlkr in the
constructed arms), zero-bookkeeping max\|netf\| = 0 in every xlks window
(bound `5e-7·(1+nrec/500)`), nfil continuity exact, FINAL present,
NUL-free, full 1M-step completion, attempt=1 on every ensemble log. No
artificial fusion: filament-count dynamics continuous everywhere.

### L-B6 The slip law carries over by registration (design carry-over)

The force and rupture code paths are bit-identical to R7's (8 additive
hunks, 0 parent lines touched; gate call spliced between the R7 Bernoulli
and link commit), so the O-X6-certified Bell slip law β_X = 0.995310 ±
0.002709 carries over by registration and R8 ran no XLNF=1 law grid.
Every observed lifetime statistic is consistent with that law (L-B4);
the failure-mode trigger that would void the carry-over (any discovered
force/rupture-path alteration) never fired. The strongest a-posteriori
confirmation is the O-B4 ground-truth program itself: three independent
re-executions with an additive records-only instrument reproduced the
certified logs byte-for-byte (stripped of the instrument records).

## Oracle scorecard

| oracle | registered criterion | measured result | verdict |
|---|---|---|---|
| O-B1 gates | PBUND=0 ≡ certified R7 parent, both arms, byte-identical over 300k; zero bpol; conservation exact | byte-identical; log hashes a67e3bbf.../db4b42fb... equal the R7 (= R6) gate hashes; FINAL×2, NUL=0, 0 bpol | **PASS** |
| O-B2 instrument zero sign errors | constructed MIRROR pairs: zero classification errors both channels; every bpol cos in window; spring statics exact; FD < 1e-8 | sign battery zero errors (par acc cos +1.0 / anti rej cos −1.0, exact reverse PBUND=2; eligibility negatives all rejected); CERT_XL = 0.25 exact; differential force ±1.0 x̂ bitwise; FD 7.62e-10; runtime 133/133 + 87/87 purity | **PASS** |
| O-B3 stability | lifetimes within factor [0.5,2.0] of R7 median at matched load and of the slip-law prediction; S(10×med)=0; longest < 20× med | medians 895.0/831.0; ratios 1.65/1.53 vs R7 median and 0.70/0.60 vs slip-law prediction (both readings IN); S(10×)=0; max 7050/6353 | **PASS** |
| O-B4 selectivity | as registered: live-fraction enrichment ≥ 2.0× control | 1.58/1.59 (PB1), 1.62/1.64 (PB2) — all < 2.0; all secondary windows satisfied | **FAIL as registered** → **PASS under Amendment B-1**: primary 2.55/2.54, 2.47/2.55 (≥2.0×); secondary 212 st = 0.36×, 284 st = 0.57× (≥150 st, ≥0.3×); tertiary obs/pred 0.998–1.016 (≤5%) |
| O-B5 no collapse/fusion/leak | conservation exact; ghosts 0; inventory exact; max\|netf\| = 0; FINAL; NUL-free; no SIGSEGV/hang; nfil continuous | exact on every runs22 certification log (brush 400, constructed 39; 600+600 constructed windows; 2000-window brush logs; orphan t=0 xlkr predicted and found) | **PASS** |

**R8 exit criterion (plan_bundle.md §10): MET for the certified scope.**
Parallel and antiparallel bundles are separately measurable with zero
sign errors (O-B2), stable for their registered lifetimes (O-B3),
selectively enriched by the channel relative to the unselective control
(O-B4 as B-1-amended), and free of collapse, fusion, and inventory leaks
(O-B1, O-B5). The R8-f branched-mesh integration diagnostic — registered
as a diagnostic, not a gate — is complete (books PASS, signs PASS;
measured findings below): the antiparallel channel works in the
architecture stress fibers will use, and the R7-f pool-pinning watch item
resolves under the gate. **R8 is fully closed.** Per the roadmap the
project proceeds to R9 (minimal parallel bundle, oracle
`plan_filopod.md` registered 2026-09-03) and R10 (myosin).

## The 2026-09-03 force-first doctrine

Registered 2026-09-03 with the R9 oracle (`plan_filopod.md`) and binding
on subsequent stages, after the user critique that threshold oracles on
position/timing/length distributions chase ghosts in a constantly
rebuilding system. User directives: **"the only oracles we can rely on
here are forces"** and **"fibers are going to move, rotate differently,
be differing lengths — we can guess at ranges but that's about it."**

- **Hard gates (binary; failure = bug = STOP with evidence):** force
  closure (max\|netf\| = 0 zero-bookkeeping), FD vs analytic forces <
  1e-8 on any new or recombined force path, energy accounting, monomer
  conservation, exact inventories, ghost scan, no nfil discontinuities,
  and instrument neutrality (byte-identity under inert amendments),
  including channel-OFF byte-identity to the certified parent.
- **Emergent distributions are measurements, reported as ranges — never
  gates:** bundle geometry, orientation, length, and lifetime statistics
  are diagnostics with per-seed spread, exactly as the fibers move,
  rotate, and differ in length.

R8 anticipated this doctrine in fact if not in name: every hard gate of
the rung is a force/conservation/inventory/byte-identity oracle (O-B1,
O-B2 statics, O-B5, the stripped-log neutrality proofs), and the single
distributional gate (the original unstratified O-B4) is precisely the one
that failed on physics and had to be re-registered against measured
timing. The B-1 tiers are the bridge form: selection and persistence are
certified as *instrument* properties (measured against the control with
locked methods), while the doctrine governs R9+.

## Failure-mode register (plan_bundle.md §8) with dispositions

| # | anticipated failure | registered response | disposition |
|---|---|---|---|
| 1 | Zero or near-zero acceptance (brush geometry rarely passes the polarity window) | measure eligibility flux first; then narrow-COSB amendment; never silently widen | **Not triggered.** Brush occupancy 0.28–0.32 ≫ 0.05 floor; acceptance plentiful (8.2k–9.6k accepted attaches per 1M-step arm, 4.1k–4.5k post burn-in). Eligibility flux measured in R8-c (thin in the *constructed* geometry only — registered caveat) |
| 2 | Pool exhaustion from rejection churn (candidates repeatedly drawn/rejected while the pool fills with orthogonal links) | rejected-class pool exclusion only via amendment with inventory proof; default COSB/eligibility amendment | **Not triggered.** nxl means 5.1–6.7 in the gated brush arms vs MAXXL=24; cap-pinning longest run 0 windows in every certification arm — confirmed in the dense branched mesh at R8-f (0/1000 pinned windows both seeds, pool ~50% occupied; the R7-f watch item closes) |
| 3 | Tangent instability on short/curved filaments (sign flicker under thermal motion) | contour ≥ 4 eligibility (registered); tangent-smoothing amendment with static re-cert if flicker dominates | **Mitigated by construction.** Contour ≥ 4 + interior eligibility enforced; zero sign errors in all batteries. The large bpol-vs-replay \|dcos\| between dumps was investigated and certified as real physics — 54–56° RMS/dump thermal rotation (L-B2), not instrument flicker; no smoothing amendment needed |
| 4 | PBUND=0 divergence from parent | any byte difference is a bug; fix before any smoke | **Not triggered.** Byte-identity at every level (MIRROR, 50k smoke, both 300k gates) |
| 5 | Sign convention error | caught by O-B2 with zero tolerance; fix convention, rerun full static suite, quarantine affected logs | **None found.** O-B2 zero-tolerance batteries clean at every stage (36k+ attaches, 100% class purity) |
| 6 | Force/rupture path alteration discovered in build | voids slip-law carry-over; XLNF=1 amendment and β re-certification before any ensemble | **Not triggered.** 0 parent lines touched; carry-over intact (L-B6); confirmed a posteriori by the three stripped-log byte-identity proofs |
| 7* | *(emergent, not anticipated)* unstratified O-B4 criterion physically unreachable | — | **Triggered and resolved.** Registered STOP → age-stratified investigation → user-directed ground-truth verification → Amendment B-1 (three-tier O-B4) → PASS. Documented in the O-B4 saga above |

## Known limitations / R8-f and R9+ handoff

1. **MAXXL=24 pool saturation in dense meshes — watch item CLOSED at
   R8-f, not handed forward.** R7-f registered 7–14 consecutive
   cap-pinned windows in branched meshes (nfil≈31): the link population
   there was pool-limited, not kinetics-limited. R8-f re-measured pool
   behavior under PBUND=2 in exactly that architecture: the antiparallel
   gate keeps the pool ~50% occupied (nxl mean 12.1–13.2 of 24, max
   21/19) and **pinning is 0/1000 post-burn-in windows in both seeds** —
   the R7-f pinning behavior does not appear in the gated branched mesh.
   Residual guidance only: dense-mesh rungs with wider acceptance
   windows (or unselective channels) should still re-register pool size.
2. **Analyzer replay prepend ambiguity (verdict-insensitive; R9+
   tightening candidate).** On dense logs the exact-cover replay can swap
   two pointed-tip extras when tips lie within PREP_DMAX, producing
   chimeric chains (worst case: r8e_pbund1_s84950, topology cert fails
   from dump 63500, 13/6538 post-burn-in samples flagged). Sensitivity
   readouts excluding flagged samples change no fraction at the 4th
   decimal (clean 0.3805/0.1643/0.4552 vs reported 0.3805/0.1643/0.4553);
   latent flagged samples in the passing logs (18/24/0) shift fractions
   ≤ 0.0003. The engine record stream is complete and certified-clean
   throughout — this is an analyzer-topology caveat only. Registered with
   B-1 as verdict-insensitive; replay tightening deferred as an R9+
   candidate amendment. Note the ground-truth lpol validation bounds the
   practical impact: engine-native vs replay fractions agree ≤ 0.005. In
   the dense branched mesh the same replay substrate fails harder (the
   R8-f topology-reconstruction caveat below: ~60k invisible
   within-window bind/unbind pairs, all dumps taint-flagged); the R8-f
   numbers are carried by the exact-subset bound (~1e-6) and the lpol
   cross-check, and the R9+ tightening amendment should cover the
   branched case.
3. **Eligibility-flux thinness in constructed geometry.** R8-c attach
   rates are 3–5e-4 per 500-step window (112/540 and 76/540 windows with
   any attach) because short constructed filaments fluctuate around the
   FILLEN ≥ 4 floor. Sufficient for the O-B2/O-B3 readings (133/87
   attaches); a geometry amendment is registered as available if richer
   constructed statistics are ever needed.
4. **lpol instrument confinement.** The engine-native ground-truth
   record lives only in `runs22/ob4_verification/` variants (+45/+47
   additive lines, PLPOL default 0, stripped-log byte-identical); the
   certified `bundle_pol.ergo` is untouched. If R9+ wants engine-native
   polarity timing, it must re-register the instrument.
5. **Age cutoff locked at ≤ 250 steps.** Pooling young links to < 500
   dilutes PBUND=1 below 2.0 (1.968/1.965 measured) on physics, not gate
   defects — future stages must not widen the bin. The certified rotation
   timing (τ_cos ≈ 130/295 steps; first-exit KM medians 405/428 steps) is
   the design input for R9/R10: any mechanism that must *use* bundle
   polarity (myosin duty cycle, protrusion persistence) has ~200–400
   steps of class memory per link to work with unless it re-reads
   geometry continuously.

## R8-f branched-mesh diagnostic (antiparallel, PBR=1) — COMPLETE

Source of truth: `runs22/r8f/R8F_REPORT.md` (SHA256 `f7965feb...`), with
`r8f_age_analysis.txt` (`2f8d96d3...`), `r8f_pinning_results.txt`
(`98b237fd...`), and the certified-analyzer reports
`r8f_pbund2_s{77031,84950}.analysis.txt` (`a72376e5...` / `478e0098...`).
R8-f is registered as a **diagnostic, not a gate**, and was executed
under the 2026-09-03 force-first doctrine: HARD checks are
forces/books/signs only; every emergent distribution below is a measured
finding reported as a range, with no pass/fail threshold.

**Config.** Certified `runs22/bundle_pol.ergo`; anchored `^PARAMETER`
variant edits only (diff-verified: `F_EXT 0.1→1.0`, `PADH 0→1`,
`PXL 0→1`, `PBUND 0→2`, `NSTEPS→1M`, per-arm SEED; unedited base carries
the R7-f geometry PBR=1, KBR=2.0, DBR=1.5, PANCH=1, FORMIN=0, MAXF=32,
NMAX=400, MAXXL=24, XLMAXF=2, XLNF=0, COSB=0.5, XSEED=6.0). Seeds
{77031, 84950}, 1M steps. Logs `f8a093fd...` / `f4015fbc...` (both OK
attempt=1; 2000 xlks windows, FINAL + FINAL_E present, NUL-free).
Provenance re-verified: each variant recompiled; binaries differ from the
archived `.bin` only in the registered 8-byte tempfile symbol. The
architecture-matched control is the archived R7-f branched unselective
log (`runs21/integration/integ_pbr1_formin0_adh_xlk_s77031.log`),
replayed with the identical method — no new R7 runs.

### HARD checks — books PASS, signs PASS (both seeds)

- **Books:** monomer conservation exact at every census (independent awk
  recount, 0 violations); ghost scan 0; crosslink inventory exact
  (xlka 12166/12270, xlkr 12157/12263, open-at-final 9/7 = final NXL);
  adhesion inventory exact (adha−adhr = 3/2 = final nadh);
  zero-bookkeeping max\|netf\| = 0 over all 2000 xlks windows per seed;
  nfil continuity **event-exact** — every census-window Δnfil equals
  recorded births minus deaths (0/1999 mismatched windows; max window
  \|Δnfil\| 14/6 vs 15 in the R7-f branched parent — normal branching
  dynamics between 500-step censuses, not fusion/leak).
- **Signs (correctness property, not a distribution):** independent
  recount over all **24,436 bpol records** — every accepted attach cos ≤
  −COSB = −0.5 (windows [−0.999981, −0.500050] / [−0.999991, −0.500032],
  0 violations); attach classes 100% antiparallel, zero parallel, zero
  orthogonal. The gate works unchanged in the dense branched mesh.

### Measured findings (post burn-in > 500k; ranges across the two seeds; no verdict)

**Occupancy and turnover.** nfil mean 30.465/30.868 (R7-f 30.945); nxl
mean 13.185/12.109 (R7-f 22.586); **occupancy nxl/nfil 0.4328/0.3923
(R7-f 0.7299)** — the gate roughly halves accepted attaches (attach rate
0.012264/0.012392 vs 0.024546 per step, the expected ~50% solid-angle
window); balance 0.0013/0.0003, drift 0.0035/0.0239. The antiparallel-
bundled branched brush stands taller: geo 12.042/12.507 (R7-f 10.125),
piston xp at 1M 11.247/11.276 (R7-f 10.439).

**MAXXL=24 pool behavior — the R7-f watch item RESOLVES.** Pinned
windows (nxl ≥ effective cap min(24, XLMAXF·nfil/2)): **0/1000
post-burn-in windows in BOTH seeds** (nxl max 21/19 < 24; pool mean
12–13 of 24 ≈ 50% occupied). The R7-f reference showed a 7-window
pinned run; under the antiparallel gate the pinning behavior does not
appear in either seed. Known-limitation entry 1 is closed accordingly.

**Tension through the mesh.** Crosslink live-link mean \|F\|
0.8681/0.9169 (window ranges [0.5253, 1.2657]/[0.5259, 1.4161]; R7-f
mean 0.8947); mean stretch 1.6896/1.7546 against rest DX0=1.5 — the
network lives in tension in the branched architecture too. Rupture \|F\|
median **1.517/1.683**, p90 ≈ 2.99 both seeds, max = 3.000 both (the
SMAXX hard-release boundary; R7-f post-burn-in median 1.497). Adhesion
carries the larger forces: window mean \|F\| **2.069/2.518** (R7-f
2.456), rupture median 3.508/3.622, max 7.081/7.535 (R7-f median 3.572).
Adhesion occupancy 0.0358/0.0770 (R7-f FORMIN=0: 0.0767); traction-on
window fraction 0.842/0.986 (R7-f 0.965) — seed 77031 shows a
suppressed-adhesion episode (nadh mean 1.094 vs 2.376), reported as a
range with no verdict.

**Rupture-cause mix and lifetimes.** Slip-dominated in both seeds —
slip **81.45%/79.95%**, hard-stretch 15.16%/17.36%, monomer-unbind
2.95%/2.37%, filament-death 0.44%/0.32% (R7-f: 72.16/15.44/10.39/2.01%)
— endpoint-geometry causes (unbind/death) are **~3× rarer than in
R7-f**, the bundling endpoint-protection signature already seen in the
unbranched brush (L-B4). Link lifetimes: median **718/657 steps**, mean
1068.5/981.7, max 14176/12161 (R7-f median 636).

**Bundle polarity persistence in the branched geometry.** Live
antiparallel fraction **0.3882/0.3884 vs the R7-f branched control
0.2277 → enrichment 1.705/1.706×**; young links (age < 250) 0.6857/0.6889
(control same-bin 0.2578, ~2.7×); class-persistence half-lives **295/275
steps = 0.41/0.42× the arms' lifetime medians** — the same
selection-vs-persistence separation certified in the brush (L-B2/L-B3),
in the architecture stress fibers will use. The one-compartment
age-mixture of the measured persistence curve and lifetime survival
predicts live antiparallel **0.393/0.408 vs observed 0.388/0.388**: the
steady-state live fraction is again fully explained by attach purity +
post-attach rotational drift. The independent engine-native lpol
cross-check (PLPOL=1 records-only variant runs
`r8f_lpol_s{77031,84950}`, used read-only) gives live antiparallel
0.3832/0.3770 and reproduces every age bin within a few percent.

### Registered R8-f caveats (both verdict-free by doctrine)

1. **Analyzer topology-reconstruction FAIL on dense branched logs —
   reported limitation, bounded.** The certified analyzer's TOPOLOGY
   RECONSTRUCTION section (a replay-substrate quality gate for contour
   analysis, not a force/books check) flags the dense branched mesh:
   ~60k invisible within-dump-window bind/unbind pairs (engine wbp
   pointed binds 7948/8371 vs 0 replay-assigned prepends), so the
   analyzer's OVERALL line prints FAIL. Under the force-first doctrine
   this is a reported limitation, not a verdict. Two facts bound its
   impact on every measured polarity number above: (a) the exact subset
   (attaches landing on a dump step) shows max\|dcos\| 1.13e-06/5.11e-07
   — the replay tangent is engine-exact; (b) the engine-native lpol
   cross-check reproduces every replay-based number within a few
   percent. All 2000 dumps per log are taint-flagged in the arm **and**
   identically in the R7-f control replay (apples-to-apples comparison);
   the flagged-exclusion sensitivity column is unavailable (nan) — the
   lpol cross-check covers the gap. Feeds known limitation 2 (R9+
   replay-tightening candidate, branched case included).
2. **s84950 FINAL lenfil 0 — seed-filament record artifact.** The
   legacy FINAL record is filament-1-centric (nfree := NM − FILLEN(1));
   in s84950 the original seed filament 1 had dissolved by step 1M
   (FINAL lenfil 0 / nfree 400). The mesh itself is healthy (final
   census nfil=31, nbound conserved). No bookkeeping implication.

### R7-f vs R8-f (same quantities, branched FORMIN=0 architecture)

| quantity | R7-f (unselective) | R8-f (PBUND=2, 2 seeds) |
|---|---|---|
| nfil mean | 30.945 | 30.465 – 30.868 |
| nxl mean | 22.586 | 12.109 – 13.185 |
| occupancy nxl/nfil | 0.7299 | 0.3923 – 0.4328 |
| attach rate /step | 0.024546 | 0.012264 – 0.012392 |
| pool pinning | longest run 7 windows (flagged) | none (0/1000 windows, both seeds) |
| rupture median \|F\| | 1.497 (post burn-in) | 1.517 – 1.683 |
| rupture mix slip/hard/unbind/death | 72.2/15.4/10.4/2.0% | ~80–81/15–17/2.4–3.0/0.3–0.4% |
| adhesion occupancy | 0.0767 | 0.0358 – 0.0770 |
| adhesion rupture median \|F\| | 3.572 | 3.508 – 3.622 |
| brush height (geo) | 10.125 | 12.042 – 12.507 |
| live antiparallel fraction | 0.2277 | 0.3882 – 0.3884 (1.71×) |

**R8-f verdict (limited by doctrine): Books PASS. Signs PASS.** All other
entries are measured findings reported as ranges. The antiparallel
channel is certified as an instrument in the branched architecture:
perfect attach selectivity, exact books, resolved pool behavior, and a
quantified polarity-memory budget (275–295-step half-lives) for the R11
stress-fiber design.

## Space-conscious design note

Three registered economy decisions govern R8's disk footprint, all still
binding: (i) **slip-law carry-over** — because the force/rupture paths
are untouched, R8 runs no XLNF=1 per-step-force law grid; all ensemble
logs are XLNF=0 at ~56 MB instead of ~800 MB each (the 47.1M-exposure
β_X identification from R7 stands as the certified rupture law); (ii)
**no checkpoint archive** is created until the user gives explicit
go-ahead ("don't zip anything up till I give a go-ahead... The files are
massive") — all artifacts live as plain files under
`/mnt/agents/output/actin_phasespace/`; (iii) diagnostic variants
(PCERT, PLPOL) are confined to `runs22/` subdirectories so the certified
engine tree carries zero instrumentation weight.

## Artifacts

Engine: `phi4/runs22/bundle_pol.ergo`, SHA256
`fb1c8d281b72816304a8bf13e9b66e815ec75200c20803c31879011b46507935` (merge
commit `d84f3c6`, 2974 lines, +245 vs parent, 0 parent lines touched).
Run variants: `runs22/variant_pbund1.ergo` `8a933cb5...`,
`runs22/variant_pbund2.ergo` `7473981c...` (one anchored line each).

Analyzers and certification scripts:

| file | SHA256 |
|---|---|
| runs22/stage_i_analysis.py (1379 lines, streaming) | 4d2b399cc63f5ac4c18b0473e0b6da541820b348bc16fb2d79dbaffd483277ea |
| runs22/r8c/r8c_constructed_analysis.py (354 lines) | 529ca9047837850a201f70b44e081ebf23ecad159cb8032ecadae5083e41e5f2 |
| runs22/ob4_investigation/ob4_age_analysis.py (610 lines) | 53799a775f96734f9318cce07c76a1ed1071dd2c0c682e692dbb7d47403e4110 |
| runs22/ob4_verification/lpol_analysis.py (393 lines) | 70158f94bd2a0607afb85cd49c396e300e05eb3e04ea87de4d86cd15bad26f8e |
| runs22/r8f/stage_i_branched.py (475 lines, branched-mesh analyzer wrapper) | 5e9ed1c917669e7bb2a9e82260e2c8ae36623a06ec13e0c3e453f9f4dd4cd9cc |
| runs22/r8f/r8f_age_analysis.py (232 lines, ob4 method + BranchedTopology) | 43e959a59d0f05047e9fe3bacf8f3adc3551f8f34a9a73afdc874961cb0f767d |
| runs22/r8f/r8f_pinning_analysis.py (138 lines, pool/adhesion/nfil continuity) | af12785188b0a60d0595df570d8b9e1eaa0111e0cb882dd4fafa7bbf624991a9 |

Analysis outputs and certification documents:

| file | SHA256 |
|---|---|
| runs22/SELFTEST_I.md (R8-a build + static/FD evidence) | e3c13020dbb3201dd993d1a7e76f07e6de2ae3456ad77357a1f5d1c11ae59214 |
| runs22/ANALYZER_I_VALIDATION.md (stage_i synthetic + real validation) | c12f7e24007fab331a84778df76e86bfbc8c4dc449e2b60ed4fdcba597e1d1ee |
| runs22/r8e/OB4_DECISION.txt (O-B4 FAIL as registered) | 532c40aa628c30a1da1246ca331db345f99babbd2522e0bf44a73529ed1f15dc |
| runs22/ob4_investigation/ob4_report.txt (age-stratified + persistence + ceiling model) | c0f4b2622ade1b5419f1a19fc31279ae3c8eb72538bc53b593f5796ab745cde3 |
| runs22/ob4_verification/OB4_VERIFICATION.md (ground truth, neutrality proofs, rotation timing) | 9bd7b792b9f37f253601179aa852de7e9b4609dff151b9355979b73292e76817 |
| runs22/ob4_verification/ob4_lpol_verification.txt (full numeric report) | b107229f097ceeee73bc3cf6c5cb83a0fb5f19c5dd089e8aebf33ffa9a57b090 |
| runs22/r8c/r8c_pairs.variant.ergo (PCERT diagnostic variant, runs22 only) | 311a05d4f8f6c315afb9394bbb9cfc006d72703c6199c6a8429a72afb163ccc0 |
| runs22/r8f/R8F_REPORT.md (R8-f stage report: books, signs, measured ranges) | f7965feb9bd8d6186144dfb5b0859d263ae02e2c75fc6851d7b4a0921574303f |
| runs22/r8f/r8f_age_analysis.txt (branched polarity persistence, ob4 method) | 2f8d96d3b2aa8e6dd065ad068a0338113e58770b0a83e2c2ed2207639695a6d8 |
| runs22/r8f/r8f_pinning_results.txt (pool pinning + adhesion coexistence + nfil) | 98b237fd2dcaf124361bc0efca52245908529f5f5b42233809ada2a9e7158084 |
| runs22/r8f/r8f_pbund2_s77031.analysis.txt (certified-analyzer report, branched wrapper) | a72376e5cdf5b2b073bea84048f3bed85a924afde57a11b735b35b2bab6ab4d6 |
| runs22/r8f/r8f_pbund2_s84950.analysis.txt (certified-analyzer report, branched wrapper) | 478e0098a4af7c24a75089197f77654543b600c428db21a6f1b8bfd5c2e4f79f |

Static certification (`runs22/static_cert/`): MIRROR outs
`3f3269dbc8f2...` (bpol0/parent, PXL=0, byte-identical pair),
`d3da0428f96f...` (bpol0/parent, PXL=1, byte-identical pair),
`dbc0a80990bf...` (bpol1 PXL=1), `44caf9e4ff6f...` (bpol2 PXL=1); FD
outs `c0b86dc288de...`/`86f8f05dec7e...`. Full artifact hashes in
`runs22/SHA256SUMS`.

Gates (`runs22/gates/ob1_gate{1,2}_child.log`, runner-verified, child ≡
archived R7 parent within each arm):

| gate arm | SHA256 |
|---|---|
| gate 1 (PBR=0, FORMIN=0) | a67e3bbfd5a9ca7e89ee2087916eec3844aec88f562bbd3414b871792f6545e5 |
| gate 2 (PBR=1, FORMIN=1) | db4b42fb5a21335f47a55781e99397bc383e738bb644c114ffb50abf5ca84ed6 |

Run logs (SHA256 from `*.status`, runner-verified post-copy; all OK
attempt=1):

| run | SHA256 |
|---|---|
| smokes/parent_50k.log and smokes/bpol0_50k.log (byte-identical pair) | 007e6b2b20f1992a4248362ea92528dfa5ba5b39614a8d922ebf89336810faa0 |
| smokes/bpol1_50k.log | bf4b704064a2743e4b60d959d097b1a947d8aa97fbfad309798e8f931018d2ec |
| smokes/bpol2_50k.log | b2eb6baebabce43e36573a83a235053273d1e8264b03b72a5731eee9a52011ca |
| r8c/r8c_pbund1.log | 4f47a88872babd0e6b3d842a1d1e14dfa41b27b906a46782e0db9bc3a8560ec7 |
| r8c/r8c_pbund2.log | 680d582923e4f282d3dd0ffc8bcdcce907b8a2bf2af542ef2fcf14a7d955eafb |
| r8d/r8d_pbund1_s77031.log | bbcc44da3492e7a82666264b6046ab86a63c0234580a791d49b26c115b9b0123 |
| r8e/r8e_pbund1_s84950.log | 8cc49f7d89e2cb56e64f209c83341c3880416f411fd72060d6990a5b3d172040 |
| r8e/r8e_pbund2_s77031.log | bd5c4c0f0886281303e870382f5b2a9cbc802181151f5f5db76f264830fcb2bb |
| r8e/r8e_pbund2_s84950.log | ffd1b6cfc609a723695f6762fa9bcaecbb5d8a1174567977ac7c5f30c09fdbf8 |
| ob4_verification/ob4v_pbund1_s77031.log (13,035 lpol; stripped ≡ r8d log) | 7a606672d586762df7818be703e545f8d16e403a1cfc712199b7928fed9f1ed1 |
| ob4_verification/ob4v_pbund2_s77031.log (12,386 lpol; stripped ≡ r8e log) | 3a6655fb81006a18cc1917c51d2a0d5ffbbffee570cacca8fe472fd3f76bf31a |
| ob4_verification/ob4v_xlk_on_f1_s77031.log (30,891 lpol; stripped ≡ runs21 control) | db903fb36ac74e4c596cb05c60d9e9b110c0a9962b351b228481cb15f909be0f |
| r8f/r8f_pbund2_s77031.log | f8a093fd524cf1c7cb09bb1c227bffecea87c33dd37fa733a6bbc7bf8d6d0a12 |
| r8f/r8f_pbund2_s84950.log | f4015fbc6b729c56db7a60ec6c202b8658dec63074e1966b8824acd0bc85d165 |
| r8f/r8f_lpol_s77031.log (25,949 lpol; cross-check variant, read-only) | 7679670e20ca5cc38e23bab335298b23abff4acf5e2faa2d5774b1cd87d09659 |
| r8f/r8f_lpol_s84950.log (24,060 lpol; cross-check variant, read-only) | 5892f80cac15066e8d34e4dca9c913a9ef9e1966f0f569ffb2aac1eca04e33c0 |

Control evidence (archived, no new R7 runs):
`runs21/smokes/xlk_on_f1_s77031.log` (SHA256 `0128a50f...`, certified in
CROSSLINK_LAW.md), reanalyzed by stage_i replay as
`runs22/r8d/r7c_control_xlk_on_f1_s77031.analysis.txt` and
`runs22/r8e/r7c_control_xlk_on_f1_s77031.analysis.txt` with sensitivity
readouts `runs22/r8e/*.sensitivity.txt`. Per-log `.variant.ergo` inputs
and `.status` files sit beside every log.

## Reproduction

```sh
# toolchain (certified Ergo compiler, frozen per Stage-0 user verification)
cd /mnt/agents/output/actin_swarm/toolchain/ergo_mcl
python3 -m core /mnt/agents/output/actin_phasespace/phi4/runs22/bundle_pol.ergo -o <bin>

# runner (wipe-immune pattern: /tmp stream, verify, cp, re-verify; writes .status)
cd /mnt/agents/output/actin_phasespace/phi4
sh runs20/runner_r6.sh <bin> runs22/<dest>.log

# brush / smoke / ensemble analysis (per-log; R7 capabilities + polarity replay)
python3 runs22/stage_i_analysis.py <logs...> \
    --expected-steps 1000000 --burn-in 500000 --out <out>.txt

# constructed-pair analysis (R8-c census geometry)
python3 runs22/r8c/r8c_constructed_analysis.py runs22/r8c/r8c_pbund1.log \
    --pbund 1 --burn-in 30000 --out runs22/r8c/r8c_pbund1.r8c_analysis.txt

# O-B4 age-stratified investigation (4 R8 arms + archived R7 control)
python3 runs22/ob4_investigation/ob4_age_analysis.py \
    --out runs22/ob4_investigation/ob4_report.txt

# O-B4 engine-native ground-truth verification (lpol logs)
python3 runs22/ob4_verification/lpol_analysis.py \
    --control runs22/ob4_verification/ob4v_xlk_on_f1_s77031.log \
    --pb1 runs22/ob4_verification/ob4v_pbund1_s77031.log \
    --pb2 runs22/ob4_verification/ob4v_pbund2_s77031.log \
    --out runs22/ob4_verification/ob4_lpol_verification.txt
```

## Conclusions for the phase-space map

1. **A deterministic polarity gate on crosslink attach is exact.** One
   local-tangent dot product with interior/contour-≥4 eligibility gives
   100% attach-class purity with zero sign errors, zero new RNG draws,
   zero new engine state, and byte-identical OFF behavior — parallel and
   antiparallel bundles are now separately constructible and measurable
   in the certified engine.
2. **Selection and persistence are separate physical quantities.** The
   gate is perfect at attach, but universal thermal rotation (~54–56° RMS
   per 500-step dump, control-identical, age-independent) erases class
   memory with half-lives 212/284 steps — 0.36/0.57× the link lifetimes —
   so steady-state live-fraction enrichment ceilings at ~1.6, exactly as
   the persistence×turnover mixture predicts (0.998–1.016). Young-link
   enrichment (age < 250) is the true selection measure: 2.47–2.55×.
3. **The rotation timing is a certified design number for R9/R10.**
   τ_cos ≈ 130 (parallel) / 295 (antiparallel) steps; first-class-exit
   KM medians 405/428 steps vs lifetime medians 594/501. Motors and
   protrusion machinery that must exploit bundle polarity have a
   quantified memory budget per link, measured against engine ground
   truth (lpol), not analyzer assumption.
4. **Instrument claims earn instrument weight only through ground
   truth.** The replay analyzer's numbers carried the FAIL, the
   investigation, and the amended PASS — but the amendment was registered
   only after an engine-native record, proven dynamics-neutral by
   stripped-log byte-identity, reproduced every load-bearing number
   (enrichment ≤ 0.006, age bins ≤ 0.005, half-lives ≤ 2 steps). This is
   the force-first doctrine in action: hard gates on forces,
   conservation, inventory, and byte-identity; distributions reported as
   measured ranges.
5. **The antiparallel channel transfers to the branched architecture
   (R8-f).** In the dense branched mesh stress fibers will use: books
   and signs PASS on both seeds (24,436 attaches, 100% antiparallel),
   live antiparallel enrichment 1.71× over the branched control with
   275–295-step persistence half-lives, tension and slip-law
   phenomenology intact (endpoint ruptures ~3× rarer than R7-f), and the
   R7-f MAXXL=24 pool-pinning watch item resolves (0/1000 pinned
   windows) — the gate itself relieves pool pressure by halving
   acceptance. The dense-mesh replay substrate is the one instrument
   that does not transfer (topology-reconstruction FAIL, bounded by
   exact-subset ~1e-6 and the lpol cross-check) — queued for the R9+
   tightening amendment.
