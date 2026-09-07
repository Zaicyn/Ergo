# CROSSLINK_LAW.md — φ4.9 filamin-like crosslinking and mechanical cohesion (R7) certification

Certified: 2026-09-02. Engine lineage: pop_fpt.ergo (φ4) → brush_c400g →
brush_br400 → brush_bra (S4 anchored branching) → brush_bra_x → brush_bra_r
(hold-release piston) → brush_bfm (per-filament formin channel) → brush_adh
(PADH substrate adhesion channel) → **brush_xlk** (PXL filamin-like crosslink
channel). Final source `phi4/brush_xlk.ergo` (2729 lines, +412 vs parent),
SHA256 `a3ed43347392aa97f7ad2bde5ad0d7c1ce0e09e244220cedba59edc7ea46944a`,
merge commit `7ff0566`. Parent: certified `brush_adh.ergo` (SHA256
`f709fb4453a1c6c6405ca33f9600844253ee7e35296acdb208f8d79bbf7075b8`, merge
`615c8ae`). Oracle: `plan_crosslink.md` (O-X1..O-X6 plus registered
amendments X-1..X-6), registered before engine build and ensemble. All
certification arms run PADH=0; adhesion appears only in the R7-f integration
diagnostics. Method: swarm delegation authorized by the 2026-09-02 workflow
amendment; stage order remained lock-step — gates before smokes, smokes
before ensembles, O-X3a+O-X3b before R7-f and docs. All durable artifacts
under `/mnt/agents/output/actin_phasespace/`. Runs: `runs21/` (44 runs, 1M
steps each: 2 smokes + 6-run XLNF=1 law grid + 34 cohesion/release/ensemble
runs + 2 integration diagnostics). Analysis is reproduced by
`runs21/stage_h_analysis.py` (smoke/pair, SHA256 `a6ede934...`),
`runs21/stage_h_law_analysis.py` (law grid, SHA256 `fdcd3bcb...`), and
`runs21/ox3a_certification.py` (O-X3a mechanism gate, SHA256 `1b2f0f9b...`);
analyzer self-tests in `runs21/SELFTEST_H.md`.

## The question

R6 certified dynamic substrate adhesion in the unbranched brush and recorded
a known limitation: in the branched mesh, adhesion occupancy collapses 3.2×
(pointed tails are consumed at branch junctions). No attractive
inter-filament force exists anywhere in the certified lineage — every brush
certified so far is a collection of independent filaments whose only
coupling is through the piston.

**R7 asks whether transient filamin-like crosslinks make the brush
mechanically cohesive — tougher under load — without freezing it into an
irreversible aggregate.**

This is the second rung on the stress-fiber path in `NEXT_STAGES_PLAN.md`:
crosslinking must be certified before bundle polarity (R8), myosin (R10),
and stress fibers (R11) can be interpreted mechanically.

| stage | arm | purpose |
|-------|-----|---------|
| R7-a | build + static/FD cert + review/verify | PXL channel on the certified brush_adh parent |
| R7-b | O-X1 gates | PXL=0 bit-identity to certified parent, both arms |
| R7-c | brush smoke (PBR=0, FORMIN=0, PADH=0, F=1, paired ON/OFF) | O-X2 occupancy/turnover, O-X4 no-collapse, first cohesion read |
| R7-d | law grid F∈{0,1,4} × 2 seeds, XLNF=1 | decides O-X2, O-X5, O-X6 |
| R7-e | cohesion arms F∈{2,4} paired ×2 seeds + release pair + O-X3b seed ensemble (24 runs) | decides O-X3 (as amended to O-X3a + O-X3b), O-X4 |
| R7-f | PBR=1 FORMIN=0 / PBR=1 FORMIN=1, PADH=1, PXL=1, one seed each | integration diagnostics (not oracle arms) |

## Mechanism as certified

The crosslink element is a minimal transient slip bond between filaments of
the certified brush_adh brush:

- A crosslink connects the **head beads** `B1=2*M1-1`, `B2=2*M2-1` of two
  bound monomers on two **different** active filaments `F1 < F2`
  (inter-filament only by registration; intra-filament links are out of R7
  scope).
- Eligibility requires, in addition: the adhesion-carrying monomer of a
  filament is **ineligible** (registered double-anchor precedence,
  plan_adhesion.md §8 mode 4 — the adhesion bond keeps its monomer); no
  existing crosslink on the pair; both filaments below the per-filament cap
  `XLMAXF`; head-bead distance `d < RXLK`.
- Candidate selection is an all-pairs bound-monomer scan (O(NIN²/2), the
  same order as the certified DIMKIN scan), keeping the **minimum-distance**
  candidate per open filament pair — deterministic, no extra RNG.
- The spring has finite rest length: `E = KXLK·(d − DX0)²`,
  `F on B1 = 2·KXLK·(d − DX0)·û`, equal and opposite on B2 (an internal
  force, net zero on the system). `d > DX0` attractive, `d < DX0` repulsive.
  `DX0 = 1.5 > WCUT = 0.5612`, so the rest geometry never fights WCA
  sterics.
- Rupture is a force-dependent Bell slip bond,
  `P_rupture = KOFFX·DT·EXP(|F_stored|/FBX)` (stored previous-step force,
  the ADHKIN convention), plus a hard geometric release at `d > SMAXX`,
  plus removal when an endpoint monomer unbinds (cause 3) or an endpoint
  filament dies (cause 4). Cause codes: 1=slip, 2=hard stretch,
  3=monomer unbind, 4=filament death.
- One draw per eligible open pair per step: attachment
  `RAND(SN + 4700 + 2*(F1*(MAXF+2)+F2))`, rupture
  `RAND(SN + 4701 + 2*(F1*(MAXF+2)+F2))`. With `F1 < F2` the pair index is
  ≤ 1086, so the claimed span **4700–6873** is disjoint from every parent
  slot (max parent slot 4663). **No draws are made when PXL=0.**
- Pool discipline: one link per filament pair, per-filament cap XLMAXF=2,
  global pool MAXXL=24, first-free-slot allocation — bounded occupancy so
  freezing is detectable as saturation.

Registered parameters:

| parameter | value | role |
|---|---:|---|
| `PXL` | 0/1 | channel toggle; OFF bit-identical to parent |
| `RXLK` | 2.0 | head-bead capture radius |
| `KONX` | 1.0 | attachment rate per eligible open pair |
| `KOFFX` | 0.05 | basal slip rupture rate |
| `KXLK` | 1.0 | crosslink spring stiffness (softer than KADH=2.0; filamin is flexible) |
| `DX0` | 1.5 | crosslink rest length (> WCUT; never fights sterics) |
| `FBX` | 1.0 | Bell slip force scale |
| `SMAXX` | 3.0 | hard-release stretch |
| `XLMAXF` | 2 | per-filament link cap |
| `MAXXL` | 24 | global link pool size |
| `XLNF` | 0/1 | WRITE-only per-step crosslink-force record; default 0 inert |

XLNF was registered **at build time** — the R6 PADHF lesson (per-step force
records must exist before the law grid, not retrofitted after a cancelled
ensemble).

Instrumentation (all WRITE-only):

```text
xlka STEP L F1 M1 F2 M2 d                             attachment
xlkr STEP L F1 M1 F2 M2 lifetime fx fy fz cause       rupture
xlks STEP nxl meanf meand netfx netfy netfz attach_rate rupture_rate   per NDIAG=500 window
xlkf STEP L F1 F2 fx fy fz                            per step per link (XLNF=1, MIRROR=0 only)
```

The `xlks` `netf*` columns are a **zero-bookkeeping** instrument: crosslink
forces are internal, so every window's net force must vanish to the %.6f
rounding bound `5e-7·(1+nrec/500)`.

**Accepted deviation (registered):** the parent's per-monomer bond-force
arrays `FBX/FBY/FBZ` were renamed `BFX/BFY/BFZ` to resolve a collision with
the registered R7 parameter name `FBX` (the Bell force scale). The rename is
behavior-neutral, proven by the byte-identical MIRROR and O-X1 gate outputs.

## Amendments registered during the rung

Six amendments were registered in `plan_crosslink.md` and are part of the
certified configuration:

1. **X-1 — O-X3 instrument clarification.** The `geo` record is
   `geo STEP FILLEN(1)` — filament 1's monomer count, not brush height. The
   engine-native brush-height instrument is the piston position `XP` (free
   piston, PREL=0: stationary mean XP is the brush height at force balance).
   Clarification only.
2. **X-2 — language correction.** Smoke and law-grid arms run with the free
   equilibrating piston (PREL=0), as actually executed in R6-d/R7-c; only
   the release grid uses the clamped-then-free protocol. No R6 result
   changes.
3. **X-3 — O-X3 degeneracy guard.** After the R7-d F_EXT=4 seed-84950 arm
   pinned the piston at the XPLO=5.5 clamp, O-X3 was moved to
   F_EXT ∈ {2,4} with any both-clamped comparison excluded as degenerate.
4. **X-4 — O-X3 re-registration (contractile cohesion, user-approved).**
   After the geometry/sign investigation: censor-free **x95 reach**
   instrument (95th percentile of monomer x per gm dump, steps > 500k),
   sign expectation flipped (crosslinked brush SHORTER), effect ≥ 0.3 and
   ≥ 3σ per comparison. Piston XP retired as the cohesion instrument; the
   R7-c F=1 XP comparison retracted as gate evidence.
5. **X-5 — O-X3 split (user-approved).** After the X-4 re-score failed on
   power and a null cell: **O-X3a** = contractile-mechanism certification on
   existing logs (three criteria in every ON arm), **O-X3b** = powered
   6-seed × 2-load x95 ensemble (≥5/6 seeds Δ<0 plus one-sample t p<0.05 per
   load; x95 over bound monomers). 16 new runs.
6. **X-6 — O-X3b re-scope (user-approved).** After the 6-seed re-score
   showed a real but seed-heterogeneous F2 effect and F4 attenuation: the
   per-seed sign-count criterion retired; **registered statistic = pooled
   one-sample one-sided t over 10 F_EXT=2 seed-Δx95 values** (6 existing + 4
   new seeds, 8 new runs); **F_EXT=4 load attenuation registered as a
   finding, not a gate cell.**

## Certification chain

1. **Static/FD certification passed** (pre-merge, branch `r7-xlk-impl`;
   `runs21/static_cert_candidate/RESULT.md`). Fresh Ergo compile PASS;
   MIRROR=1 PXL=0 dump byte-identical to the parent MIRROR dump (SHA256
   `3f3269db...` both); MIRROR=1 PXL=1 static link at pure-x stretch d=2.0:
   `CERT_XL = 0.25` equals `KXLK·(d−DX0)²` exactly (binary-exact);
   differential FRC is `+1.0 x̂` on bead 37 and `−1.0 x̂` on bead 39
   (= ±2·KXLK·(d−DX0)·û) bitwise, all other lines pure additions; PADH=1
   arm reproduces the R6 CERT_ADH value exactly (adhesion + crosslink
   coexist); central FD error **7.62e-10 < 1e-8**. RNG slot scan: the two
   new RAND sites appear once each inside XLINKKIN, span 4700–6873
   collision-free, zero crosslink draws at PXL=0; XLNF=1/PXL=0 ≡
   XLNF=0/PXL=0 byte-identical. 20k dynamic smoke: 291 xlka / 275 xlkr /
   40 xlks, all four rupture causes exercised, inventory exact,
   netf=0.000000 every window.
2. **Independent reviewer PASS** (3 informational notes: a comment
   inaccuracy vs the registered text, a meand-precision nit, and a note
   that the adhesion/crosslink exclusion is one-directional — all
   spec-conformant) and **independent verifier PASS** (all 6 claims
   reproduced from scratch with matching hashes).
3. **O-X1 gates passed** on the final merged source: arm 1
   (`PBR=0,FORMIN=0`) and arm 2 (`PBR=1,FORMIN=1`) both byte-identical to
   the certified parent over 300k steps, log SHA256 `a67e3bbf...` and
   `db4b42fb...` — **exactly the R6 gate hashes** (lineage continuity
   confirmed); 600/600 clean censuses, NUL=0, FINAL present, 0 xlk records.
4. **Brush smoke passed (R7-c).** Paired ON/OFF, F=1, seed 77031, 1M
   steps, free piston. ON: occupancy 0.6920 (O-X2 window [0.1,1.5]),
   balance 0.0007, 11,124/11,116 stationary attach/rupture events, drift
   0.0376, ruptures slip-dominated (14,239 slip / 5,143 hard / 1,514 unbind
   / 271 death), median lifetime 544; O-X4: rel-rate ratio 1.097 ≥ 0.5,
   displacement ratio 0.982 ≥ 0.25, cap-pinning longest run 1 window.
   Analyzers certified against synthetics beforehand (`SELFTEST_H.md`:
   β recovery 0.966±0.049 at β_true=1.0, flat-hazard rejection,
   tampered-window detection at the exact window, real-data PASS).
5. **Law grid passed (R7-d, XLNF=1).** F∈{0,1,4} × seeds {77031,84950},
   1M steps, free piston: all 6 runs structurally clean, crosslink
   inventory exact, zero-bookkeeping max\|netf\|=0, pooled O-X6 slip-law
   fit in the registered window. OVERALL: PASS.
   Analyzer incident resolved in-stage: a gm-displacement NaN had two root
   causes (OOM whole-file parse in stage_h_analysis.py → converted to
   streaming; missing gm-position tracking in stage_h_law_analysis.py →
   added verbatim). Fixed analyzers (SHA256 `a6ede934...`/`fdcd3bcb...`)
   were validated by bit-identical XLNF=0-vs-XLNF=1 cross-checks;
   `law_grid_analysis.txt` was regenerated (SHA256 `94b6585b...`), diff vs
   the stale version = exactly the 9 displacement lines, β unchanged;
   the stale NaN version is preserved at
   `runs21/superseded/law_grid_analysis_nan_stale.txt`.
6. **Cohesion stage passed (R7-e) after the O-X3 saga** — original gate
   failure, registered investigation, and two re-registrations; told in
   full below. Outcome: O-X3a mechanism certification PASS (all 3 criteria,
   all 5 ON arms); O-X3b 10-seed pooled test PASS, decisive (p=0.0043);
   O-X4 no-collapse PASS on every paired arm (rel-rate ratios
   1.086/0.936/1.097, displacement ratios 0.983/1.002/0.982, cap-pin ≤ 2
   consecutive windows in every certification arm).
7. **Integration diagnostics completed (R7-f).** Two one-seed smokes, all
   gates green (stage_h + stage_g OVERALL PASS, both inventories exact,
   zero-bookkeeping exact); the architecture-dependent adhesion finding is
   recorded under R7 laws below.

## The O-X3 cohesion saga

The scientific centerpiece of R7 is that the registered cohesion premise
failed, was investigated under a registered stop, and was re-registered
twice before the true law emerged. The final certified statement is the
opposite sign of the original registration.

### Act 1 — the original premise fails (registered stop)

The registered O-X3 premise was "cohesion ⇒ taller brush": paired same-seed
arms, gate `XP_ON > XP_OFF` at F_EXT ∈ {2,4}. Measured stationary XP means
(steps > 500k):

| pair | XP_ON | XP_OFF | verdict |
|---|---:|---:|---|
| F=1 s77031 (R7-c, final draws) | 10.97 | 9.77 | apparent pass (later retracted) |
| F=2 s77031 | 9.452 | 10.057 | **fail** |
| F=2 s84950 | 9.335 | 10.181 | **fail** |
| F=4 s77031 | 7.956 | 7.774 | pass, ratio 1.023 |
| F=4 s84950 | 6.911 | 7.682 | **fail**, ratio 0.900 |

The sign was load/seed-dependent, not a clean stiffening. Per the
registered O-X3 escape ("if the sign is wrong, stop and register a
geometry/sign investigation before any amendment"), the O-X3 track stopped;
R7-f and docs were blocked pending the investigation.

### Act 2 — the investigation: a contractile internal-tension network

`runs21/cohesion/OX3_INVESTIGATION.md` (independent read-only re-parse of
all 12 cohesion/smoke/release logs; every overlapping analyzer number
reproduced exactly) established:

- **Strain cycle.** Links are born **compressed** (⟨d_birth⟩ = 1.233–1.296
  < DX0=1.5 — min-distance candidate selection picks the closest pair),
  live **stretched** (⟨d_live⟩ = 1.845–1.867 > DX0), and rupture
  **overstretched** (median rupture \|F\| ≈ 1.9 ⇒ d ≈ 2.45; 85% of ruptures
  attractive). Attachment selects a local minimum of pair separation,
  diffusion separates the pair, and Bell slip culls the tightest links —
  mean internal tension at zero mean external strain.
- **Tension only.** The engine's filaments are freely-jointed chains
  (FILBONDS = distance springs only, no bending rigidity), so
  inter-filament tension cannot act as struts — it can only contract the
  tangle. The upper endpoint of a live link is pulled downward in 73–76% of
  cases (mean F_x = −0.32..−0.37 per link).
- **Causal growth inhibition.** A filament's net Δlen flips from
  +0.02..+0.06 per 5k steps before attach to −0.05..−0.10 after attach
  (paired, n ≈ 17k–22k attach-endpoints per arm, p ≤ 1.7e-7 in all five ON
  arms); length-matched controls show linked young filaments grow at half
  rate, and linked filaments are *less* piston-blocked (not a
  piston-proximity confound).
- **Refuted alternatives.** Lateral compaction: per-dump RMS yz radius
  changes ≤ 0.16. Tilt/leaning: mean \|a·x̂\| = 0.499–0.503 in all 12 logs
  (Δ ≤ 0.003). Tip-proximal capping: link endpoints are uniform along the
  contour, slightly tip-depleted (4.6–7.3% top-decile).
- **Sick gate statistics.** XP is clamp-censored at both ends (upper clamp
  XPHI=11.3 active in OFF arms at F≤2: 9.3%/2.0%/3.3% of samples; lower
  clamp 3.9% in on_f4_s84950), per-arm Neff is only 17–67, and the R7-c
  F=1 "pass" was built from two single final draws — it **reverses under
  stationary means** (10.753 ON vs 10.866 OFF). The F4 s77031 "+0.18 pass"
  is 0.7σ noise. Rare giant clamped-FRCT spikes in ON arms (max 1037 vs
  39–61 OFF) are a genuine collective-force-transmission signature but
  appear only inside censored clamp episodes.
- The F4 s84950 geo=68.06 "anomaly" is the Amendment-X-1 instrument
  artifact (geo = FILLEN(1); filament 1 held 18–21% of the bound pool)
  plus brief marginal clamp touches — engine state certified-clean
  throughout; registered as an instrument artifact, no engine action.

### Act 3 — Amendment X-4 fails on power and a null cell

X-4 re-registered O-X3 on the censor-free x95 instrument with the sign
flipped (shorter ON), requiring effect ≥ 0.3 and ≥ 3σ in both seeds at both
loads. The independent re-score (`OX4_RESCORE.txt`) returned **FAIL**:
per-arm Neff 23–50 (vs the ≥200 target for ±0.2-resolution claims) leaves
z = −2.7..−3.2 marginal and estimator-fragile where the sign is right, and
**F4 s77031 has the wrong sign** (Δ = +0.03..+0.07, null) under both
instrument readings. The FRCT spike-incidence diagnostic was retracted
(incidence is symmetric; only magnitude differs in 3/4 cells, during
censored clamp episodes).

### Act 4 — Amendment X-5: mechanism PASS, 6-seed ensemble FAIL

X-5 split O-X3. **O-X3a** (mechanism certification on existing logs,
`ox3a_certification.py`, SHA256 `1b2f0f9b...`) **PASSED** all three
criteria in every one of the five ON arms:

| arm | ⟨d_birth⟩ | ⟨d_live⟩ | median d_rup | frac_down | growth-inhibition p |
|---|---:|---:|---:|---:|---:|
| F1 s77031 | 1.2960 | 1.8575 | 2.3639 | 0.7544 | 1.93e-07 |
| F2 s77031 | 1.2857 | 1.8666 | 2.3883 | 0.7548 | 1.42e-06 |
| F2 s84950 | 1.2836 | 1.8517 | 2.3608 | 0.7509 | 2.49e-14 |
| F4 s77031 | 1.2776 | 1.8517 | 2.3785 | 0.7464 | 2.68e-09 |
| F4 s84950 | 1.2431 | 1.8459 | 2.3752 | 0.7401 | 1.66e-07 |

(gates: all three strain-cycle inequalities vs DX0=1.5; frac_down > 0.65;
paired Δlen < 0 at p ≤ 0.01; worst-case p = 2.49e-14). All cross-checks
against the analyzer txts match exactly.

**O-X3b** (6-seed ensemble, seeds {77031, 84950, 6203, 34567, 92869,
55631} × F_EXT ∈ {2,4}, x95 over bound monomers) **FAILED** the X-5 gate
(`OX3B_RESCORE.txt`, independent verifier): F2 — 4/6 seeds negative
(needed ≥5/6), pooled t = −2.099, p = 0.0449 (marginal); F4 — 2/6 seeds
negative, t = −1.233, p = 0.136 (attenuated to null).

### Act 5 — Amendment X-6: decisive PASS, load attenuation registered

X-6 retired the per-seed sign count (the wrong statistic for a
real-on-average but seed-heterogeneous effect), registered the **pooled
one-sample one-sided t over per-seed Δx95** as the statistic, added 4 F2
seeds {44729, 73553, 91229, 28387}, and registered the F4 attenuation as a
finding. The 10-seed re-score (`OX3B_RESCORE_10SEED.txt`, SHA256
`fd55a987...`, independent verifier with own parser; all 6 prior seed
deltas reproduced exactly):

- **mean Δx95 = −0.3823, sd 0.3612, t = −3.347 (df=9), one-sided
  p = 0.0043** — PASS, decisive (p < 0.01, not marginal);
- 95% CI on the mean: **[−0.6406, −0.1239]**, excludes 0;
- Wilcoxon signed-rank p = 0.0098; 8/10 seeds negative (s6203 +0.1048,
  s55631 +0.1983, seed heterogeneity as registered); per-arm Neff
  17.3–40.0 reported as-is;
- percentile-method sensitivity ≤ 0.002 per seed, no sign flips.

**Registered finding (X-6):** the contractile shortening attenuates with
load — F_EXT=2 10-seed mean −0.3823 vs F_EXT=4 6-seed mean −0.127
(p=0.136) — because the measured tether-load budget on the engaged zone is
only ≈10–20% of F_EXT, so external compression dominates at high load.

## R7 laws

### L-X1 The crosslink population is a steady-state turnover pool (O-X2)

Stationary (t>500k) pooled arms of the XLNF=1 law grid:

| F_EXT | nfil | nxl | occupancy | attach/rupture events | balance | drift |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 23.244 | 15.888 | 0.6835 | 21532 / 21520 | 0.0006 | 0.0538 |
| 1 | 21.745 | 14.825 | 0.6818 | 20140 / 20128 | 0.0006 | 0.2317 |
| 4 | 22.159 | 16.396 | 0.7399 | 21722 / 21731 | 0.0004 | 0.1894 |

Per-run occupancies span 0.6693–0.7403 — all inside the registered window
[0.1, 1.5], bounded away from both extinction and the XLMAXF=2 cap;
balance ≤ 0.0011 and drift ≤ 0.24 at every arm against the 0.05/0.50 bars;
≈10k events per run against ≥20/20. Ruptures are slip-dominated
(≈67% slip / 25% hard-stretch / 7% unbind / 1.3% death across arms).

### L-X2 The rupture hazard is the registered Bell slip law, β_X ≈ 1/FBX to 0.5% (O-X6)

Per-step exposure maximum-likelihood fit of
`μ = KOFFX·DT·exp(β_X·|F|)`, pooling all six XLNF=1 law-grid runs
(post-burn-in; cause-1 ruptures terminal, causes 2/3/4 and final-open links
right-censored; fixed offset log(KOFFX·DT) = −8.294050):

- exposures = **47,100,489**; slip events = **42,984**;
- **β_X = 0.995310 ± 0.002709 (SE); 95% CI [0.990001, 1.000619]** —
  registered window [0.5, 2.0] IN, statistically indistinguishable from the
  nominal 1/FBX = 1.0;
- expected/observed events = 43045.2/42984 = 1.0014;
- force-decile calibration tracks across the full decade of event rates
  (e.g. decile 1: 0.000273 vs 0.000273; decile 10: 0.002911 vs 0.002899);
- per-arm homogeneity: β ∈ [0.985842, 1.005299] (spread 0.019457) across
  F_EXT ∈ {0,1,4} — load-invariant, as registered for a bond-level kinetic
  parameter.

β_X is identified from 47.1M per-step force exposures (the build-time XLNF
record), not from 43k rupture-step proxies.

### L-X3 Cohesion is contractile: the crosslinked brush is shorter at force balance (O-X3a + O-X3b)

Transient slip-bond crosslinks on freely-jointed chains form a contractile
internal-tension network (Act 2 strain cycle, certified by O-X3a on all
five ON arms), and its macroscopic signature is certified by the
X-6-registered pooled test: at F_EXT=2 the crosslinked brush's x95 reach is
shorter — **mean Δx95 = −0.3823, 95% CI [−0.6406, −0.1239], p =
0.0043** across 10 seeds, at equal polymer mass (nbound equal within 2.3
monomers across arms), equal orientation, and equal lateral radius.
Collective force transmission is real (clamped-FRCT spike magnitudes
1037 vs 39 in censored clamp episodes) but the free-piston equilibrium
signature is contraction, not stiffening: with no bending rigidity,
inter-filament tension has no strut direction. The effect attenuates with
load (F4 mean −0.13) as external compression dominates the ≈10–20%-of-
F_EXT tether budget — registered as a finding.

### L-X4 Crosslinking does not freeze the mesh (O-X4)

On every paired certification arm (smoke F=1; cohesion F∈{2,4}; release):
stationary monomer-release-rate ratios ON/OFF = 1.086 / 0.936 / 1.097 (bar
≥ 0.5); gm median-displacement ratios 0.983 / 1.002 / 0.982 (bar ≥ 0.25);
nxl pinned at the effective cap for at most 2 consecutive windows
everywhere (bar > 5). Census conservation exact throughout.

### L-X5 Internal forces book-keep to zero exactly (O-X5)

Across all 44 runs21 logs: exact monomer conservation
`nbound+nfree+2*ndim=400` at every census, filament-length sum = nbound,
ghost scan 0, nfil ≤ MAXF, FINAL present, NUL-free, complete 1M-step
trajectories. Crosslink inventory (event reconstruction by slot L,
endpoint identity, per-filament cap, inter-filament only, F1<F2) exact at
every window of every ON run (open-at-final 12–24, always matched by the
final xlks census). Zero-bookkeeping: **max\|netf\| = 0** over every xlks
window of every run (tol `5e-7·(1+nrec/500)`); law-grid meanf closure
max\|err\| ≤ 5.06e-07.

### L-X6 Crosslink–adhesion interaction is architecture-dependent (R7-f diagnostic)

One-seed integration smokes (PBR=1, PADH=1, PXL=1, F=1, seed 77031; all
gates green, both inventories exact, zero-bookkeeping exact):

| arm | adh occupancy (R6-f → R7-f) | traction windows \|tr\|>0 | adh median \|F\| | xlk median \|F\| | xlk occupancy | cap-pinning |
|---|---|---|---|---|---|---|
| PBR=1, FORMIN=0 (branched) | 0.0590 → **0.0767 (+30%)** | 92.7% → **96.5%** | 3.5585 | 1.3871 | 0.7299 | 7 consecutive windows |
| PBR=1, FORMIN=1 (hybrid) | 0.0627 → **0.0373 (−40%)** | 96.1% → **81.2%** | 3.5690 | 1.3177 | 0.7413 | 14 consecutive windows |

In the branched-only mesh, crosslinks **help** adhesion (load transmission
through the mesh; adhesion bonds carry ≈2.6× the crosslink force). In the
hybrid, crosslinks **suppress** adhesion (substrate-interface
competition/shielding). The R6-f handoff question is answered: recovery is
architecture-dependent, not generic. Both arms pin nxl at the MAXXL=24
pool cap for 7–14 consecutive windows in branched meshes (nfil≈31) —
pool-limited, not kinetics-limited; registered for R8+ (non-gating).

## Oracle scorecard

| oracle | registered criterion | measured result | verdict |
|---|---|---|---|
| O-X1 gates | PXL=0 ≡ certified brush_adh parent, both arms, 0 diffs over 300k; ghosts 0 | byte-identical; log hashes a67e3bbf.../db4b42fb... equal the R6 gate hashes; 600/600 clean censuses; 0 xlk records | **PASS** |
| O-X2 dynamics | occupancy ∈ [0.1,1.5]; balance < 5%; ≥20/20 events; drift ≤ 50% | occupancy 0.6693–0.7403 all arms; balance ≤ 0.0011; ≈10k events/run; drift ≤ 0.24 | **PASS** |
| O-X3 cohesion | as amended: O-X3a mechanism (3 criteria, every ON arm) + O-X3b X-6 pooled t, mean Δx95 < 0 at p < 0.05 | O-X3a PASS all 5 arms (worst-case p 2.49e-14); O-X3b 10-seed mean −0.3823, CI [−0.6406,−0.1239], t=−3.347, p=0.0043; Wilcoxon 0.0098 | **PASS (as X-6-registered O-X3a + O-X3b)** |
| O-X4 no collapse | rel rate ≥ 50% of OFF; displacement ≥ 0.25× OFF; no >5-window cap pinning; conservation exact | ratios 1.086/0.936/1.097 and 0.983/1.002/0.982; cap-pin ≤ 2 windows all certification arms | **PASS** |
| O-X5 stability/inventory | conservation exact; ghosts 0; inventory exact every window; zero-bookkeeping \|netf\| ≤ 5e-7·(1+nrec/500); full 1M completion | exact on all 44 runs; max\|netf\| = 0 every window; meanf closure ≤ 5.06e-07 | **PASS** |
| O-X6 slip law | β_X ∈ [0.5,2.0] from per-step exposure fit; decile calibration; arm homogeneity | β_X = 0.995310 ± 0.002709, CI [0.990001,1.000619]; exp/obs 1.0014; calibration tracks; arm β ∈ [0.985842,1.005299] | **PASS** |

**R7 exit criterion (plan_crosslink.md §10): MET.** The dynamic
filamin-like crosslink channel is gate-clean (O-X1, lineage hashes
unchanged), forms and ruptures continuously with a certified slip law
(O-X2/O-X6), produces measurable cohesion without freezing the mesh
(O-X3a/O-X3b/O-X4), and preserves every monomer, filament, and crosslink
inventory oracle in the unbranched brush (O-X5). The project is cleared for
R8 bundle polarity.

## Known limitations / R8+ handoff

1. **F4 load attenuation (registered X-6 finding).** Contractile shortening
   is certified at F_EXT=2 (mean −0.38) and attenuates toward null at
   F_EXT=4 (mean −0.13, p=0.136), because the tether-load budget on the
   engaged zone is ≈10–20% of F_EXT. Cohesion under strong external
   compression is a different (untested) observable — the collective FRCT
   spike signature suggests toughness under confinement that R8+ could
   register directly.
2. **MAXXL=24 pool saturation in dense meshes.** In branched meshes
   (nfil≈31) nxl pins at the 24-slot pool cap for 7–14 consecutive windows
   — the link population is pool-limited, not kinetics-limited. Registered
   for R8+ (non-gating in R7); any bundle-polarity rung with denser meshes
   must re-register the pool size.
3. **Hybrid adhesion suppression.** Crosslinks recover branched-mesh
   adhesion only in the branched-only architecture (+30% occupancy); in the
   hybrid they suppress it (−40% occupancy, traction 81.2% of windows) via
   substrate-interface competition. Input to R8 architecture design.
4. **Neff < 200 per-arm caveat.** Existing-log effective sample sizes are
   17–67 per arm; the X-6 gate passes on seed-pooling instead. Any future
   ±0.2-resolution per-arm claim needs Neff ≥ 200 (≈4× longer runs or 4
   seeds per arm); never gate on single final draws (the R7-c F=1 "pass"
   reversed under stationary means).
5. **Contractile tension is the R10/R11 foundation.** The certified
   network supplies mean internal tension at zero external strain — the
   substrate on which myosin (R10) and stress-fiber (R11) mechanics will
   build. A crosslink-stiffened *tall* brush requires bending rigidity
   first (a KBEND/angular term); in a freely-jointed model inter-filament
   tension is purely contractile by construction. Registered as R8+
   bundle-polarity territory, out of R7 scope.

## Artifacts

Engine: `phi4/brush_xlk.ergo`, SHA256
`a3ed43347392aa97f7ad2bde5ad0d7c1ce0e09e244220cedba59edc7ea46944a` (merge
commit `7ff0566`, branch `r7-xlk-impl`, 2729 lines, +412 vs parent).

Analyzers and certification scripts:

| file | SHA256 |
|---|---|
| runs21/stage_h_analysis.py (550 lines, streaming) | a6ede934e2c1d8afea972e1a3ee90724e8c52d181aa724675dd53f3d75805460 |
| runs21/stage_h_law_analysis.py (731 lines) | fdcd3bcbf4972630df9bf96248e5a3c4b377da5f5c1ed525cca2f4a70aacc616 |
| runs21/ox3a_certification.py (326 lines) | 1b2f0f9b90033b89fb7c637c6aaf91bba56fe902d2664da0e860e06801f8d160 |

Analysis outputs:

| file | SHA256 |
|---|---|
| runs21/law_grid/law_grid_analysis.txt (regenerated, current) | 94b6585b59115871c9955047b29f7c91ab93b70c3d55aaead2075bad1ec0d3fb |
| runs21/superseded/law_grid_analysis_nan_stale.txt (pre-fix, preserved) | 81cea90641178b03dfca7ccff0627321ed768d614a52d360b8a53b80112b21d9 |
| runs21/smokes/r7c_smoke_analysis.txt | 710443e19423a01c6cd545759ac594b9f46a65d4e2badb741a08f31b7727794f |
| runs21/cohesion/arm_f2.0_analysis.txt | 061945da7cedd643c999bbdfa9b899efede6f2352baf54e4592742e62f110beb |
| runs21/cohesion/arm_f4.0_analysis.txt | d5906ce7d5d30686de8679787e18deccb2955f2f44f4741ec5bcea03f6c1d7cc |
| runs21/cohesion/release_f4.0_analysis.txt | 650c69b812e8cfe61c997745e80dfed1ff5c935dbcd94c03f309fef7eebc03cc |
| runs21/cohesion/OX3_INVESTIGATION.md | a5de22f72d96b7811ede5152c0104d607200ba9ce2ccf07ef49a4906f8ecb08f |
| runs21/cohesion/OX4_RESCORE.txt | 589546f1e168cdd20a5cd6df1e4656d2153dbfa74da89a80f8da5a2277bee1c8 |
| runs21/cohesion/OX3A_CERTIFICATION.txt | 01f83cf28c2c3f04f8c0e958f28bb3e7c77809602844a2c54b17259740337003 |
| runs21/cohesion/OX3B_RESCORE.txt (6-seed, FAIL) | 761c494c99e407240b97662477bdf429c24ee85e83465ed9347af89d14522930 |
| runs21/cohesion/OX3B_RESCORE_10SEED.txt (X-6, PASS) | fd55a987782839ccf1a3407e39b2e88f9a8165a0124e9f105c9ac6b40e5a1c07 |
| runs21/integration/integ_pbr1_formin0_{g,h}.txt | 9c55a6a601e6416af7cfc2946210d83a2b2dffadd899693d67795cb985f6597c / f6bc0520a79c4e82f7aef63c76ac0508b9a5255c02e3948259a4566371b4dd72 |
| runs21/integration/integ_pbr1_formin1_{g,h}.txt | 7933094262ec13d371c5f7d230a17f859d48f40b662bcaa0ba6d7aa85dfe04f6 / ff4ace4c9baf2d3b29b0fc0cd5e11409cb46790c99277be9aab0dea56241e39e |
| runs21/static_cert_candidate/RESULT.md | d86a72c1cbabaf082cc9d2bf994f8857eb2bf32f102b6f36a493af8d4e1beef9 |
| runs21/SELFTEST_H.md | d5ddd24d0c055709fc73df3b0d0e8dc545e9d9ccd97f230db90a22bdddbecab5 |
| plan_crosslink.md (oracle + amendments X-1..X-6) | adca13a08bc12608cda548e82d190c61faff608aacfbd951ebce75be8a61be98 |

Gates (`runs21/gates/ox1_gate{1,2}_{parent,child}.log`, runner-verified,
parent ≡ child within each arm):

| gate arm | SHA256 (both logs) |
|---|---|
| gate 1 (PBR=0, FORMIN=0) | a67e3bbfd5a9ca7e89ee2087916eec3844aec88f562bbd3414b871792f6545e5 |
| gate 2 (PBR=1, FORMIN=1) | db4b42fb5a21335f47a55781e99397bc383e738bb644c114ffb50abf5ca84ed6 |

Run logs (SHA256 from `*.status`, runner-verified post-copy; all OK
attempt=1). Smokes and law grid:

| run | SHA256 |
|---|---|
| smokes/xlk_on_f1_s77031.log | 0128a50ffb9fde846fe19d5857da724d7733ce05bb652210d210abb50cb55939 |
| smokes/xlk_off_f1_s77031.log | 4975a96086fda12380054c225ed32bf245182278b1bc4e0914c5e0ee94c15435 |
| law_grid/xlk_f0.0_s77031.log | f686ff2a678a53440ad8441a20560b0de17ee5183a2600dca11ee2f31e0a5fff |
| law_grid/xlk_f0.0_s84950.log | 1d2d8717d2584996512f468e07a3f156b990d69921cd28c330c3c2624eaa5819 |
| law_grid/xlk_f1.0_s77031.log | 0fde6c07d937c88aae907378718eb7ae33738ad20bb5169803e5ed0550b1118a |
| law_grid/xlk_f1.0_s84950.log | 8a6f7253aa38e1291bcc5324478dd11195ab5f1d4f12ad4413a3fcf5de86902b |
| law_grid/xlk_f4.0_s77031.log | 7c11ea911bb4d529d689882dc89278020b3b321fc7e19d3c0a5a30e9d18b0ec4 |
| law_grid/xlk_f4.0_s84950.log | e650d687c26496428ad509b9825613405decd8cefc515bb3be35b520407cce9a |

Cohesion arms, F_EXT=2 (10 paired seeds):

| run | SHA256 |
|---|---|
| cohesion/xlk_on_f2.0_s77031.log | f924e8548f1d3635f92bb9cb99c61c68f5c4578e3354b5bfa42795c0ba15ac63 |
| cohesion/xlk_off_f2.0_s77031.log | 67745e2a0c3d8822f6642c046ac84b493212f13603667c39ccbba6d28341bd1e |
| cohesion/xlk_on_f2.0_s84950.log | 03b47235cff77bc9168cc32a2d235ccd1b011c022c3145db4e87abf720c00a9b |
| cohesion/xlk_off_f2.0_s84950.log | 67772ae93fc063534c9dd49031649a2bd340dc0cdff9f12bc77c4c450a34042d |
| cohesion/xlk_on_f2.0_s6203.log | 1327d0d77823b97171ffbcae571909121019409962782382e87dd018493f1702 |
| cohesion/xlk_off_f2.0_s6203.log | 6bf17c0a4dff37778f6094629a25d1c0179ad9fec144639ce53220414796b722 |
| cohesion/xlk_on_f2.0_s34567.log | 62f69f60eb6e6c3b43c89e624ddecf620c9277688aedf3cd1e409848c8aa094f |
| cohesion/xlk_off_f2.0_s34567.log | 90a8aa5fba4ef85489a73472d64e01ea8d03f87a56690cb4e571d15866e802ad |
| cohesion/xlk_on_f2.0_s92869.log | 09dcb461420e376062d94995b428c6b36866f93313e0123bf279593c23055427 |
| cohesion/xlk_off_f2.0_s92869.log | 589b6d0b49ec511fb154dfdc6fabe2a823081590b6a7c7783531337d81e67f09 |
| cohesion/xlk_on_f2.0_s55631.log | 06ac84423328e6546b7c721a9ea9a30f27f0c0e808f1ae36be30d70351f153b3 |
| cohesion/xlk_off_f2.0_s55631.log | 2a4c65c0be2cd0374789ad4550700feeeccfc9ce0c5097c8b600b995e961b95f |
| cohesion/xlk_on_f2.0_s44729.log | 374124ac682ef4ae8753a904b99e6ebd825d05a48c52a8a4adc873195e4f33f8 |
| cohesion/xlk_off_f2.0_s44729.log | 47af6e6023e0cd79bf87031904b623343a6e6261cfe52799261a192436b18dc6 |
| cohesion/xlk_on_f2.0_s73553.log | 760d826c430d64774869cbc9bb7c0fbe9d0dec668082e0326fbe4259844d54f4 |
| cohesion/xlk_off_f2.0_s73553.log | 4d4df45dc13de4436c50096c3efd2a304b18c9172d6a4b5295e9d371b8567994 |
| cohesion/xlk_on_f2.0_s91229.log | ed6e94ce73e3bbee8698c2d51ce807c85f5de7b9fcdc05efa0c9547e99abe523 |
| cohesion/xlk_off_f2.0_s91229.log | 4b9185d461b16e779ac2d70e36237fd4ac3a60fb83ca533079e81d47bb180c1a |
| cohesion/xlk_on_f2.0_s28387.log | 900e536214f78ea649958bfd7df2fbfe0328a9731b853e55e99762f4fef4ce23 |
| cohesion/xlk_off_f2.0_s28387.log | 86b7d27003d48f9c5b43c2c9af4e1bc5f361f5a69e4ddaea3a1f84415752d0c8 |

Cohesion arms, F_EXT=4 (6 paired seeds), release pair, integration:

| run | SHA256 |
|---|---|
| cohesion/xlk_on_f4.0_s77031.log | 482fce10928846303c2e5afa8ab0202fafd2bff54b9ba3d13fd996ae0a8894bd |
| cohesion/xlk_off_f4.0_s77031.log | 1227a7654112bac9fe5c5f7de9bf8cb99ea204c1bf41f9a4b2de8d655ebc7f5f |
| cohesion/xlk_on_f4.0_s84950.log | 2ac577904a73a83647f8d4e338e2dd3ffc066cd224e51072314f49c48f996cf1 |
| cohesion/xlk_off_f4.0_s84950.log | 2092f740e768383a625b235f3366b467fae2955f4bfcd592be312aab04f0dd3e |
| cohesion/xlk_on_f4.0_s6203.log | 8e972c9b2aa89ba3a0b53c0591c3b418ac7be988f6099d25d53ca01045186bba |
| cohesion/xlk_off_f4.0_s6203.log | 1c8e35a645c52a66231ca366449fa30656007ed262c7fdf1edfedd1a53f2d1e1 |
| cohesion/xlk_on_f4.0_s34567.log | 535d2eff93815b7a84633cb22249aa512743fa5780b8e14ca2beb506375b1b7b |
| cohesion/xlk_off_f4.0_s34567.log | d8cae04ebf85795ec4479634289cf7e027d310bb1332bf516abe7b90b977408b |
| cohesion/xlk_on_f4.0_s92869.log | 51cbf9bcb8acaefdf0d99c67bb8cee1845fc94e87db5305645879eadfcbd9f30 |
| cohesion/xlk_off_f4.0_s92869.log | f7dae47a76d15f647d6ab7706320015a81854c5413aa9e7e6f8b95ef5eacfac5 |
| cohesion/xlk_on_f4.0_s55631.log | 6addf212a56def10b07fdc6662def5fd592a3c3a1ec20f02294be04bc64d98f8 |
| cohesion/xlk_off_f4.0_s55631.log | 035a760825c498f91202b904d00a7e9bcdeb898bf3fc13a0df6458f4ac834026 |
| cohesion/xlk_rel_on_f4.0_s77031.log | ab4f8537c67f16701a30be700c04a558f0a8151335a038fb1efa96d9337efcf7 |
| cohesion/xlk_rel_off_f4.0_s77031.log | cc4295a47342216f27fd39c3202adecd3778704f9fe252f21bd9472adc26c8da |
| integration/integ_pbr1_formin0_adh_xlk_s77031.log | 66876801ff5b8afd4ef2a025a8353cea0109e3546293ce607c23a094e069a0d7 |
| integration/integ_pbr1_formin1_adh_xlk_s77031.log | a6c3241883f6f6469e08c6ef4b1e39fab7c106484f81a1192bbd3468a214cac5 |

Static certification: `runs21/static_cert_candidate/` (RESULT.md,
SHA256SUMS, MIRROR/FD/20k-smoke outputs). Per-log `.variant.ergo` inputs
and `.status` files sit beside every log. The R6-f baseline numbers are
certified in `ADHESION_LAW.md` (runs20).

## Reproduction

```sh
# toolchain (certified Ergo compiler)
cd /mnt/agents/output/actin_swarm/toolchain/ergo_mcl
python3 -m core /mnt/agents/output/actin_phasespace/phi4/brush_xlk.ergo -o <bin>

# runner (wipe-immune pattern: /tmp stream, verify, cp, re-verify; writes .status)
cd /mnt/agents/output/actin_phasespace/phi4
sh runs20/runner_r6.sh <bin> runs21/<dest>.log

# smoke / cohesion-pair / integration analysis (per-log)
python3 runs21/stage_h_analysis.py <logs...> \
    --expected-steps 1000000 --burn-in 500000 --out <out>.txt

# law-grid analysis (O-X2/O-X4/O-X5 + pooled O-X6 slip-law ML fit)
python3 runs21/stage_h_law_analysis.py \
    f0_s77031=0.0=77031=runs21/law_grid/xlk_f0.0_s77031.log \
    f0_s84950=0.0=84950=runs21/law_grid/xlk_f0.0_s84950.log \
    f1_s77031=1.0=77031=runs21/law_grid/xlk_f1.0_s77031.log \
    f1_s84950=1.0=84950=runs21/law_grid/xlk_f1.0_s84950.log \
    f4_s77031=4.0=77031=runs21/law_grid/xlk_f4.0_s77031.log \
    f4_s84950=4.0=84950=runs21/law_grid/xlk_f4.0_s84950.log \
    --burn-in 500000 --expected-steps 1000000 \
    --out runs21/law_grid/law_grid_analysis.txt

# O-X3a contractile-mechanism certification (Amendment X-5 gate, existing logs)
python3 runs21/ox3a_certification.py --out runs21/cohesion/OX3A_CERTIFICATION.txt
```

## Conclusions for the phase-space map

1. **A minimal slip-bond crosslinker is sufficient for a living,
   load-bearing mesh.** One spring class at KXLK=1.0, DX0=1.5, KOFFX=0.05,
   FBX=1.0 with bounded caps (XLMAXF=2, MAXXL=24) gives 0.67–0.74
   occupancy, exact attach/rupture balance, zero net-force bookkeeping, and
   no freeze — on 44 runs without a single inventory or conservation
   violation.
2. **The rupture kinetics are the registered Bell law**, measured
   β_X = 0.9953 ± 0.0027 against nominal 1/FBX = 1.0 over 47.1M exposures,
   load-invariant across arms — the crosslink channel's force sensitivity
   is certified, not assumed.
3. **Cohesion in a freely-jointed brush is contractile, not stiffening.**
   Min-distance birth selects compressed links; diffusion stretches them;
   Bell slip culls the tightest — the network lives in tension, pulls the
   top layer down (73–76% of links), inhibits growth causally
   (p ≤ 2.5e-14), and shortens the brush measurably at force balance
   (Δx95 = −0.38, p = 0.0043, 10 seeds), attenuating as external load
   dominates. A taller crosslinked brush requires bending rigidity first.
4. **Inter-channel interactions are architecture-dependent.** Crosslinks
   recover branched-mesh adhesion (+30% occupancy) but suppress it in the
   hybrid (−40%); MAXXL=24 saturates in dense meshes. Bundle-polarity (R8)
   design must re-register pool size and account for substrate-interface
   competition.
