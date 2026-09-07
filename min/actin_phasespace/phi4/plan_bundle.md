# plan_bundle.md — R8 bundle polarity: parallel and antiparallel architectures

DRAFT 2026-09-03 — presented for registration review. Methodology: sequential
lock-step; oracle and experiment designed together; gates before smokes;
smokes before ensembles; checkpoint to `/mnt`. Swarm delegation for
implementation, gates, and parallelizable runs remains authorized under the
R6 workflow amendment; stage ordering remains lock-step. **No checkpoint zip
is created until the user gives explicit go-ahead (space discipline).**

Parent: certified `brush_xlk.ergo` (R7, SHA256 a3ed4334...). Roadmap:
`NEXT_STAGES_PLAN.md` §R8 (oracle classes O-B1..O-B5 sketched there are
ratified here in full).

## 1. Question

Can the engine distinguish, stabilize, and measure parallel versus
antiparallel actin bundles — with zero polarity sign errors — so that R10
myosin contraction and R12 filopodium protrusion can each be certified
against the architecture they require?

## 2. Why this is separate

Stress fibers need antiparallel organization; filopodia need parallel
bundles. A contraction or protrusion result is uninterpretable if the
underlying bundle polarity is unknown or an artifact of sign conventions.
Polarity must be certified as an instrument and as a selection channel
before any motor is introduced.

## 3. Design carry-over from R7 (space and certification economy)

The crosslink spring, rupture path, RNG discipline, and inventory machinery
are unchanged from R7. The certified slip law (O-X6, β = 0.995310 ±
0.002709) is a property of the rupture path and **carries over by
registration**: R8 runs no XLNF=1 law grid. R8 ensembles run XLNF=0
(~56 MB logs instead of ~800 MB). The new certifiable content of R8 is
confined to the attachment-acceptance path (a deterministic polarity gate)
and the polarity instrument. Any change to the force or rupture code path
discovered during build voids this carry-over and triggers an XLNF=1
amendment.

## 4. Mechanism

Engine candidate: `bundle_pol.ergo` (parent `brush_xlk.ergo`).

### 4.1 Local polarity

For a candidate crosslink between monomer I of filament F1 and monomer J of
filament F2, the local tangent of each filament at the linked monomer is

  t(B) = unit( P(B+1) - P(B-1) )   (directed pointed → barbed along contour)

with end-bead tangents using the single interior neighbor. The link polarity
is cosθ = t(I)·t(J) ∈ [−1, +1]: parallel cosθ → +1, antiparallel → −1,
orthogonal ≈ 0. Eligibility requires both monomers to have contour distance
≥ 1 from their filament ends (interior tangent defined); short filaments
(contour < 4 monomers) are ineligible. The end-to-end filament axis is a
secondary instrument quantity (offline, from gm records), not part of the
acceptance rule.

### 4.2 Polarity-selective acceptance

New channel parameter PBUND ∈ {0, 1, 2}:

- PBUND = 0: unselective — byte-identical to the certified R7 parent
  (the cosθ code path is not reached; no records; no draws).
- PBUND = 1: parallel-preferring — a candidate link that passes the R7
  attach Bernoulli is accepted iff cosθ ≥ +COSB.
- PBUND = 2: antiparallel-preferring — accepted iff cosθ ≤ −COSB.

Acceptance is DETERMINISTIC given cosθ: no new RNG draws, no changes to
existing slot usage. On rejection no link forms; the candidate set is
re-evaluated next step under the parent's normal attach draw. Rejected
candidates are not sticky and do not modify eligibility of other pairs.

### 4.3 Parameters

| name | default | meaning |
|------|---------|---------|
| PBUND | 0 | 0 = off/unselective (≡ R7 parent), 1 = parallel, 2 = antiparallel |
| COSB | 0.5 | polarity acceptance threshold on \|cosθ\| |

All R7 crosslink parameters (RXLK, KXLK, KONX, KOFFX, FBX, DX0, SMAX...),
R6 adhesion parameters, and parent parameters are unchanged.

### 4.4 RNG discipline

No new RAND sites. The polarity gate consumes no draws. The R7 slot span
4700–6873 and all legacy spans are untouched. OFF-gate requirement:
PBUND=0 produces zero draws beyond the parent's, and output is
byte-identical to the R7 parent (see O-B1).

### 4.5 Inventory

The polarity gate adds no new state: links carry no polarity tag in engine
state (polarity is a function of geometry, recomputed from positions).
Attach/rupture/inventory semantics are exactly R7's; the R7 inventory
oracle (xlka/xlkr/xlks reconstruction) applies unchanged.

## 5. Instrumentation

- `bpol STEP I J cos` — one record per ACCEPTED attach, emitted only when
  PBUND > 0 (WRITE-only; PBUND=0 emits nothing). cos printed %.6f.
- All R7 records (xlka/xlkr/xlks, xlkf under XLNF) and parent records
  (census, gm, fil, pstn, xpt, geo, rel) unchanged.
- Offline analyzers compute live cosθ from gm dumps (link replay from
  xlka/xlkr + gm positions, the O-X3a-certified pattern), polarity-class
  populations, bundle lifetimes by class, inter-filament spacing, and
  sliding displacement. Analyzer: `stage_i_analysis.py`, adapted from
  certified `stage_h_analysis.py`, re-validated on synthetics before first
  use.

## 6. Oracles

### O-B1 — OFF gates

PBUND=0 (with PBUND-instrument inert) is byte-identical to the certified R7
parent over 300k steps, both gate arms (PBR=0/FORMIN=0 and PBR=1/FORMIN=1).
Zero bpol records; conservation exact; hashes recorded.

### O-B2 — instrument zero sign errors (constructed geometries)

Constructed straight-chain pairs in the MIRROR/static configuration:
one parallel pair and one antiparallel pair within RXLK, each exercised
under PBUND=1 and PBUND=2. The polarity gate must classify every attach
candidate with zero sign errors: parallel pair accepted under PBUND=1 and
rejected under PBUND=2; antiparallel pair the reverse; every emitted bpol
cos satisfies the registered window for its channel. Static/FD
re-certification of the spring on the constructed pairs (energy =
KXLK·(d−DX0)² exact; differential force exact; central FD error < 1e-8).

### O-B3 — stability (constructed geometries, no motor)

Both bundle classes persist for their registered lifetimes: bundle
lifetime distribution consistent with the R7-certified slip law (median
within a registered factor [0.5, 2.0] of the R7 median at matched load);
no instant collapse (survival > 0 at 10× median lifetime is a failure);
no immortality (longest-lived bundle < 20× median).

### O-B4 — selectivity (brush ensemble)

In the unbranched brush at F_EXT=1, the polarity channel enriches its
intended class relative to the R7 unselective control: the fraction of
live links with cosθ ≥ +COSB under PBUND=1, and with cosθ ≤ −COSB under
PBUND=2, each exceeds the archived R7 control fraction by a registered
factor ≥ 2.0, with occupancy and turnover inside the O-X2-registered
windows (occupancy may sit below the R7 range — registered floor 0.05 —
since the gate rejects candidates; balance and drift windows unchanged).
The R7 control distribution is computed from archived runs21 logs; no new
R7 runs.

### O-B5 — no collapse, fusion, or leak

Standard battery on every R8 run: monomer conservation exact (400),
ghost scan clean, crosslink inventory exact, zero-bookkeeping exact
(max|netf| = 0), FINAL present, NUL-free, no SIGSEGV/hang over 1M steps,
and no artificial fusion (filament count dynamics continuous; no step
discontinuities in nfil census).

## 7. Stages

### R8-a — build, static/FD certification, review, merge

Implement PBUND/COSB + bpol record. MIRROR constructed-pair certification
(O-B2 statics, FD). Independent review + verification, then merge.

### R8-b — O-B1 gates

Both arms, 300k, byte-identical vs R7 parent.

### R8-c — constructed-pair smoke

Unit box with seeded parallel and antiparallel pairs; PBUND=1 and PBUND=2;
instrument records, stability (O-B2 runtime, O-B3). If eligibility flux is
too low to measure, register a geometry amendment before any ensemble.

### R8-d — brush smoke

PBUND=1, unbranched brush (PBR=0, FORMIN=0, PADH=0), F_EXT=1, seed 77031,
1M steps. Occupancy/turnover/balance/drift sanity; first selectivity read.

### R8-e — selectivity ensemble

PBUND ∈ {1, 2} × seeds {77031, 84950}, F_EXT=1, 1M steps, XLNF=0.
Decides O-B4 against the archived R7 control. O-B5 battery on all logs.

### R8-f — integration diagnostic

PBUND=2 (antiparallel) in the branched mesh (PBR=1, FORMIN=0), one seed:
antiparallel enrichment in the architecture stress fibers will use, plus
the MAXXL=24 pool behavior registered at R7-f. Diagnostic, not a gate.

## 8. Anticipated failure modes and registered responses

1. **Zero or near-zero acceptance**
   - Cause: brush tangent geometry rarely passes the polarity window.
   - Response: measure eligibility flux (candidates vs accepted per window)
     first; then register a narrow COSB amendment. Do not silently widen
     the window.
2. **Pool exhaustion from rejection churn**
   - Cause: candidates repeatedly drawn and rejected while the MAXXL pool
     sits full of orthogonal links.
   - Response: registered option — rejected-class links may be excluded
     from pool accounting only via amendment with inventory proof; default
     response is a COSB or eligibility amendment.
3. **Tangent instability on short/curved filaments**
   - Cause: local tangent flips sign under thermal motion.
   - Response: contour-length eligibility (≥4 monomers) is registered;
     if sign flicker dominates bpol records, register a tangent-smoothing
     amendment (chord over k beads) with static re-certification.
4. **PBUND=0 divergence from parent**
   - Any byte difference is a bug: fix before any smoke; OFF-gate must
     remain exact.
5. **Sign convention error**
   - Caught by O-B2 with zero tolerance; fix the convention, rerun the
     full static suite, and quarantine any affected logs.
6. **Force/rupture path alteration discovered in build**
   - Voids the R7 slip-law carry-over (§3): register an XLNF=1 amendment
     and re-certify β before any selectivity ensemble.

## 9. Deliverables

- `bundle_pol.ergo`
- gate logs and 0-diff certificates
- `runs22/` ensemble using the verified runner pattern (XLNF=0)
- `stage_i_analysis.py` and analysis outputs
- `BUNDLE_LAW.md`
- `ANALYTICS.md` update
- checkpoint archive **only on explicit user go-ahead**

## 10. Exit criterion for R8

Parallel and antiparallel bundles are separately measurable with zero sign
errors (O-B2), stable for their registered lifetimes (O-B3), selectively
enriched by the channel relative to the unselective control (O-B4), and
free of collapse, fusion, and inventory leaks (O-B1, O-B5). Only then does
the project proceed to R9 (minimal parallel bundle) and R10 (myosin).

---

## Amendment B-1 — O-B4 re-instrumented (2026-09-03, user-registered)

**Trigger.** R8-e (four-arm selectivity ensemble, PBUND∈{1,2} × seeds
{77031, 84950}) returned live-fraction enrichment 1.58/1.59 (PBUND=1) and
1.62/1.64 (PBUND=2) vs the registered ≥2.0 — O-B4 FAIL as originally
written, with every secondary window satisfied, 100% attach-class purity,
and zero sign errors on all arms. STOP registered per protocol.

**Root cause (investigated, then verified against engine ground truth).**
The unstratified live-fraction criterion conflates selection with
persistence. The gate is perfectly selective at attach, but crosslinked
filament pairs rotationally diffuse at ~54–56° RMS per 500-step dump
interval (age-independent; the unselective control rotates identically at
~53.6°). Polarity class memory decays with half-life 212 steps (PBUND=1)
/ 284 steps (PBUND=2) vs lifetime medians 594/501 — polarity decorrelates
2–3× faster than links turn over. A one-compartment mixture of the
measured persistence curve and lifetime distribution predicts a
steady-state enrichment ceiling of 1.56–1.62 — the observed ~1.6 is the
physical ceiling for ANY working gate, so the original unstratified 2.0
criterion was unreachable by construction.

**Ground-truth verification (user-directed before registration).** An
engine-native records-only instrument (`lpol STEP M1 M2 AGE OK COS`,
emitted at gm-dump cadence; zero new RNG draws; tangent definition
identical to the analyzer replay) was added as additive-only variants of
both the R8 engine and the R7 parent. For all three verification runs
(PBUND=1 s77031, PBUND=2 s77031, R7 control), the logs stripped of `lpol`
lines are BYTE-IDENTICAL to the certified logs — dynamics-neutrality
proven by construction. Ground truth vs replay: enrichment 1.574 vs 1.580
(PB1), 1.624 vs 1.620 (PB2), control fractions within 0.002; age-bin
fractions within 0.005; half-lives 212/284 vs replay 210/283. The replay
analyzer is validated as an instrument on these logs, and its numbers for
the seed-84950 arms carry full instrument weight.

**O-B4 as amended (three tiers, all measured on the R8-e ensemble + the
ground-truth runs):**

1. **Primary (selection):** intended-class fraction among live links with
   age < 250 steps ≥ 2.0× the R7 control's overall class fraction.
   Measured: 2.55/2.54 (PBUND=1, seeds 77031/84950) and 2.47–2.49/2.55
   (PBUND=2) — **PASS both channels, both seeds.**
2. **Secondary (persistence):** class-persistence half-life ≥ 150 steps
   AND ≥ 0.3× the arm's lifetime median. Measured: 212 steps = 0.36×
   (PB1), 284 steps = 0.57× (PB2) — **PASS.**
3. **Tertiary (consistency):** steady-state enrichment within 5% of the
   one-compartment persistence×turnover mixture prediction. Measured
   obs/pred 0.998–1.016 — **PASS** (reported as a diagnostic; flagged as
   self-referential and never to be used as the sole gate).

**Verdict under B-1: O-B4 PASS; R8-e certified.** The registered rotation
timing numbers (~54–56° RMS/dump, τ_cos ≈ 130/295 steps, half-lives
212/284 steps) are certified instrument outputs feeding R9/R10 design
(bundle polarity memory vs myosin duty cycle).

**Also registered:** (a) analyzer replay prepend-ambiguity caveat —
verdict-insensitive here (fraction shifts ≤0.005; ~1% flagged samples);
replay tightening deferred as an R9+ candidate amendment. (b) The `lpol`
instrument lives only in `runs22/ob4_verification/` variants; the
certified `bundle_pol.ergo` is untouched. (c) Age cutoff must be ≤250:
pooling to <500 dilutes PBUND=1 below 2.0 on physics, not on gate
defects — do not widen the bin in future stages.
