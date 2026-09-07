# Actin phase-space R6 build execution plan

## Stage 0 — Workflow update
- User has authorized delegation for implementation, gates, and smoke tests where parallelizable.
- Preserve lock-step certification: build → static/FD certification → O-A1 gates → unit smoke → brush smoke.
- Do not start any smoke unless the corresponding build and gates pass.

## Stage 1 — Coding orchestration
- Load `vibecoding-general-swarm` for this non-web coding task.
- Set up an isolated workspace/worktree or copy-based workspace as appropriate.
- Delegate the `brush_adh.ergo` implementation to a coder subagent with the registered `plan_adhesion.md` and exact Ergo dialect constraints.

## Stage 2 — Static and FD certification — PASS
- Certified Ergo compile passed from candidate and merged sources.
- MIRROR PADH=0 is byte-identical to parent; MIRROR PADH=1 adhesion energy matches `KADH*d*d` exactly.
- Differential bead force matches `2*KADH*(A-R)` exactly; central FD error is `5.826e-10`.
- RNG slot scan confirms 4600/4601 adhesion slots are collision-free; PADH=0 has no adhesion draws.
- Candidate branch `24e993d` passed independent review and verification, then merged as `1b8b0c1`.

## Stage 3 — O-A1 gates — PASS on final XSEED-amended engine
- Gate 1 (PADH=0, PBR=0, FORMIN=0, XSEED=6.0): parent/child byte-identical over 300k steps; 600/600 clean censuses; NUL=0; FINAL present.
- Gate 2 (PADH=0, PBR=1, FORMIN=1, XSEED=6.0): parent/child byte-identical over 300k steps; 600/600 clean censuses; NUL=0; FINAL present.
- Final source SHA256 is `168b473ec206d566d01558c8377d1b1b1a4ae1ecb429fb84fb44ecde43390c49` and is promoted to `phi4/brush_adh.ergo`.
- Superseded pre-XSEED engine is quarantined at `phi4/runs20/superseded/brush_adh_prexseed.ergo`.

## Stage 4 — R6 smokes — PASS
- Unit smoke: 1M steps, 843/843 attach/rupture, exact inventory, conservation/ghost scan clean, recurring nonzero traction. Intermittency is expected for the single-filament DIMERS=0 geometry.
- Brush smoke: 1M steps, stationary occupancy `4.344/22.520=0.1929` (O-A2 PASS), 5767 stationary attachments and 5768 ruptures, sustained traction in 100% of post-burn windows, exact inventory, conservation/ghost scan clean.
- R6 is cleared for the registered law grid.

## Stage 5 — PADHF instrumentation amendment — GATE-CLEAN
- Statistical audit found the old schema could not rigorously certify O-A3 or O-A4(1): `adhr` records only rupture-step force, while `adhs` traction is a 500-step time integral.
- Registered and merged the default-inert WRITE-only per-step record `adhf STEP F M fx fy fz` under `PADHF=1`; final source is commit `615c8ae`, SHA256 `f709fb4453a1c6c6405ca33f9600844253ee7e35296acdb208f8d79bbf7075b8`.
- Both official O-A1 PADH=0 gates rerun on the PADHF-amended source and passed with byte-identical 300k outputs and 600/600 clean censuses.
- Final engine promoted to `phi4/brush_adh.ergo` and recompiled cleanly.
- The preliminary old-schema law grid is preserved under `runs20/law_grid/superseded_*` and is not a certification input.
- Instrumented law-grid analyzer passed synthetic validation and selective rejection of superseded old-schema logs.
- Instrumented R6-d grid is running: F_EXT ∈ {0,1,4} × seeds {77031,84950}, PADH=1, PADHF=1, PBR=0, FORMIN=0, DIMERS=1, PSTN=1, XSEED=6.0.

## Stage 5b — R6-d instrumented law grid — PASS (pooled)
- All 6 runs (F_EXT ∈ {0,1,4} × seeds {77031,84950}, 1M steps, PADHF=1): structural O-A5 clean (2000 censuses, conservation exact, ghosts 0, FINAL present, NUL-free), adhesion inventory exact, O-A4 traction closure max err ≈ 5.8e-07 at %.6f rounding bound.
- Pooled O-A3 per-step exposure ML fit: exposures=13,861,254, slip events=32,167, β = 0.995474 ± 0.001413 (95% CI [0.992705, 0.998243]), converged; registered window [0.5,2.0] IN; expected/observed = 0.9984; decile calibration tracks.
- Arm homogeneity: β range [0.994730, 0.996086] (spread 0.0014) across F_EXT arms.
- O-A2 occupancy per arm: 0.1824 / 0.1928 / 0.2863 — all in [0.05, 0.60]; events ≥ 10k per arm; sustained traction ≥ 99.9% of post-burn windows.
- O-A4(2) load response: |mean trx| monotone nondecreasing (0.664 → 0.673 → 0.974).
- Report: `phi4/runs20/law_grid/law_grid_analysis.txt` — OVERALL: PASS.
- R6-d decides O-A2/O-A3/O-A4/O-A5: all PASS. Cleared for R6-e.

## Stage 6 — R6-e release/traction grid — PASS
- Registered config: hold-release PREL=300000, F_EXT ∈ {1,4,8} × seeds {77031,84950}, 1M steps, PADH=1, PBR=0, FORMIN=0, DIMERS=1, PSTN=1, XSEED=6.0, PADHF=0 (per-step forces not required; O-A3/O-A4 already certified).
- All 6 runs: runner OK attempt=1, structural VERIFY PASS (2000 censuses, conservation exact, ghosts 0, FINAL, NUL-free), adhesion inventory PASS (open-at-final 2–14, exact).
- Occupancy: F=1 → 0.1977/0.1743; F=4 → 0.2781/0.2450; F=8 → 0.3506/0.3508 — all in [0.05, 0.60], rising with load. Traction sustained 100% of post-burn windows everywhere.
- Force-balance diagnostic (piston, release at 300k from xp≈9.0):
  - F_EXT=1: piston runs +x to XPHI=11.3 clamp — brush overpowers load (below stall).
  - F_EXT=4: piston overshoots inward then relaxes to a fluctuating balance around x≈7–8.5 (near stall).
  - F_EXT=8: piston compresses brush to XPLO=5.5 clamp (load dominates, above stall).
  - Stall load for the adhered brush is bracketed between 4 and 8 in the release geometry; mean |tr| rises 3.8 → 4.6 → 5.2.
- Artifacts: `phi4/runs20/release_grid/` (logs + .status + .variant.ergo + arm_*_analysis.txt).
- R6-e PASS. Cleared for R6-f integration diagnostics.

## Stage 7 — R6-f integration diagnostics — COMPLETE (diagnostic finding recorded)
- Two one-seed smokes (seed 77031, 1M steps, F_EXT=1, DIMERS=1, PSTN=1, XSEED=6.0, PADH=1, PADHF=0): both structurally clean (VERIFY PASS, inventory exact, conservation/ghost clean, NUL-free).
- PBR=1, FORMIN=0: occupancy 0.0590 (vs 0.19 unbranched baseline, ~3.2× collapse), traction sustained 92.7% of windows (< 95% ad-hoc gate), nadh mean 1.8 over nfil 30.8; slip-dominated ruptures (87%), 13% monomer-unbind.
- PBR=1, FORMIN=1: occupancy 0.0627, traction sustained 96.1%, nadh mean 1.91 over nfil 30.4; thin margin above the 0.05 occupancy floor.
- Interpretation: genuine adhesion/branch-anchor interference — in the branched mesh most pointed tails are consumed at branch junctions, so few filaments present a capturable tail near the substrate plane; nfil also inflates the occupancy denominator. Not structural corruption.
- Decision (user: no preference → recommended option): record as a known limitation in ADHESION_LAW.md; R6 exit criterion is defined on the unbranched brush and is fully met; interference resolution deferred to R7+ where crosslinking changes mesh architecture.
- Artifacts: `phi4/runs20/integration/` (logs + .status + .variant.ergo + analysis txt).

## Stage 7b — R6 status vs registered exit criterion — MET
- R6 exit criterion (plan_adhesion.md §10): dynamic adhesion channel gate-clean (O-A1 ×3 generations), forms/ruptures continuously (R6-b/c/d), registered slip-bond force response (O-A3 β=0.9955±0.0014), exact traction bookkeeping (O-A4 closure ≤5.8e-07), conservation/ghost oracles preserved in the unbranched brush (O-A5 all runs). **R6 PASSES.** Cleared for R7 crosslinking after docs + checkpoint.

## Stage 8 — Report and checkpoint — COMPLETE (R6 CLOSED, PASS)
- `phi4/ADHESION_LAW.md` written (372 lines): mechanism as certified, three registered amendments, full certification chain, laws L-R6.1–L-R6.5, O-A1..O-A5 scorecard all PASS, known-limitation/R7-handoff section, 16 runner-verified log SHA256s, reproduction block.
- `phi4/ANALYTICS.md` updated (MAP 5 R6 section appended; existing content preserved).
- Verified checkpoint archive: `actin_phasespace_r6_adhesion_checkpoint.zip` (1.03 GiB, 199 entries, `unzip -t` PASS, zip SHA256 `cb26f6bcc4ce6a192e8078dbe0c32b59353cd5d8077619d5f22c3923469e1782`, engine hash inside re-verified = f709fb44..., includes runs20 payload, git bundle, README, SHA256SUMS_R6.txt).
- One snag checked in (R6-f branched-mesh interference); resolved per user as documented limitation deferred to R7+.
- **R6 substrate adhesion: CERTIFIED. Next: R7 filamin crosslinking (roadmap: R7 → R8 bundle polarity → R9 minimal parallel bundle → R10 myosin → R11 stress fiber → R12 filopodia/motility).**

# ───────────────────────── R7 — filamin-like crosslinking ─────────────────────────

## R7 Stage 0 — Oracle registration — COMPLETE
- `phi4/plan_crosslink.md` registered 2026-09-02 before any R7 build: mechanism (§4), parameters (§4.4), RNG slots 4700–6873 (§4.5), inventory (§4.6), instrumentation incl. build-time XLNF per-step force record (§5), oracles O-X1..O-X6 (§6), stages R7-a..f (§7), failure modes (§8), exit criterion (§10).
- Parent: certified `brush_adh.ergo` (f709fb44...). Certification arms run PADH=0; adhesion appears only in R7-f integration diagnostics (the R6-f handoff question).
- Engine candidate: `brush_xlk.ergo`. Run directory: `phi4/runs21/`. Analyzers: `stage_h_analysis.py`, `stage_h_law_analysis.py` (adapted from certified stage_g_*, re-validated on synthetics before first use).

## R7 Stage 1 — Build, static/FD certification, review, merge (R7-a) — PASS
- `brush_xlk.ergo` (2729 lines, +412 vs parent) on branch `r7-xlk-impl`, commit `7ff0566`, merged fast-forward into master; promoted to `phi4/brush_xlk.ergo`, SHA256 `a3ed43347392aa97f7ad2bde5ad0d7c1ce0e09e244220cedba59edc7ea46944a`.
- Static cert: MIRROR PXL=0 byte-identical to parent; CERT_XL = 0.25 exact (=KXLK·(d−DX0)², d=2.0); differential FRC ±1.0 x̂ on beads 37/39 bitwise; central FD error 7.62e-10 < 1e-8.
- Slot scan: only two new RAND sites (4700/4701+2·pair, inside XLINKKIN); span 4700–6873 disjoint; PXL=0 zero crosslink draws; XLNF=1/PXL=0 ≡ XLNF=0/PXL=0 byte-identical.
- 20k smoke: 291 xlka / 275 xlkr / 40 xlks; all four rupture causes exercised; inventory exact; netf=0.000000 all windows; nxl mean 10.0 max 17; PXL=0 20k byte-identical to parent.
- Independent reviewer: PASS (3 informational notes: N1 comment inaccuracy re ADHKIN convention — registered text governs; N2 meand ≤1e-16 nit; N3 one-directional adhesion/crosslink exclusion is spec-conformant, note for R7-f). Independent verifier: PASS, all 6 claims reproduced from scratch with matching hashes.
- Accepted deviation: parent per-monomer bond-force arrays FBX/FBY/FBZ renamed BFX/BFY/BFZ (collision with registered parameter FBX); behavior-neutral, proven by byte-identities.

## R7 Stage 2 — O-X1 gates (R7-b) — PASS
- Arm 1 (PBR=0, FORMIN=0): parent/child byte-identical 300k, sha256 a67e3bbf... (= R6 gate-1 hash, continuity confirmed); 600/600 clean censuses; conservation exact; 0 xlk records.
- Arm 2 (PBR=1, FORMIN=1): parent/child byte-identical 300k, sha256 db4b42fb... (= R6 gate-2 hash); 600/600 clean censuses; conservation exact; 0 xlk records.
- Artifacts: `phi4/runs21/gates/ox1_gate{1,2}_*`. Cleared for R7-c smoke.

## R7 Stage 3 — Brush smoke (R7-c) — PASS
- Paired ON (PXL=1) / OFF (PXL=0) arms, PBR=0, FORMIN=0, PADH=0, F_EXT=1, seed 77031, 1M, free piston (PREL=0 as registered-executed).
- ON: sha256 0128a50f...; OFF: 4975a960...; both attempt=1; analyzer OVERALL PASS ×2 (`runs21/smokes/r7c_smoke_analysis.txt`).
- O-X2: occupancy 0.6920 ∈ [0.1,1.5]; balance 0.0007; 11124/11116 stationary events; drift 0.0376 ≤ 0.50. Causes: slip 14239, hard 5143, unbind 1514, death 271; median lifetime 544.
- O-X4: rel-rate ratio 1.097 ≥ 0.5; displacement ratio 0.982 ≥ 0.25; cap pinning longest run 1 window.
- Diagnostics: XP_ON 10.97 > XP_OFF 9.77 (stiffening sign confirmed at F=1); FILLEN(1) 41.9 vs 61.4 (filament-1 length, NOT brush height).
- Amendments registered: X-1 (O-X3 instrument = xpt XP, not geo FILLEN(1)); X-2 ("clamped piston" language correction — smoke/law-grid arms run free equilibrating piston; R6 results unaffected).
- Analyzers certified: `stage_h_analysis.py` (543 lines) + `stage_h_law_analysis.py` (715 lines), self-tests in `runs21/SELFTEST_H.md` (synthetic β recovery 0.966±0.049; flat-hazard rejection; tampered-window detection; real-data PASS).
- Cleared for R7-d law grid.

## R7 Stage 4 — Law grid (R7-d) — PASS (pooled)
- 6 runs (F_EXT ∈ {0,1,4} × seeds {77031,84950}, 1M, PXL=1, XLNF=1, PBR=0, FORMIN=0, PADH=0, free piston): all structural O-X5 PASS (2000 censuses, conservation exact, ghosts 0, FINAL, NUL-free), crosslink inventory exact, zero-bookkeeping max|netf|=0, meanf closure ≤5.06e-07.
- Pooled O-X6: exposures 47,100,489, slip events 42,984, **β = 0.995310 ± 0.002709**, 95% CI [0.990001, 1.000619], converged, IN [0.5, 2.0]; expected/observed 1.0014; decile calibration tracks across all deciles; arm homogeneity β ∈ [0.985842, 1.005299] (spread 0.019).
- O-X2 per arm: occupancy 0.6835/0.6818/0.7399 (all IN), balance ≤0.0011, drift ≤0.24, events ≈10k per run.
- Noted: F4 s84950 ON pinned piston at XPLO=5.5 (clamp) → registered amendment X-3 (O-X3 degeneracy guard, gate now runs F_EXT ∈ {2,4}).
- Analyzer bug RESOLVED: gm-displacement NaN had two causes — stage_h_analysis.py OOM on 800MB XLNF=1 logs (converted to streaming parser) and stage_h_law_analysis.py never storing gm positions (added verbatim). Fixed analyzers sha256 a6ede934.../fdcd3bcb...; validated bit-identical cross-checks (XLNF=0 vs XLNF=1 same seed), smoke artifact regenerated byte-identical, f1.0-arm diff = exactly the 3 displacement lines.
- `law_grid_analysis.txt` REGENERATED with fixed analyzer (sha256 94b6585b...): diff vs stale = exactly the 9 displacement lines, β unchanged 0.995310±0.002709, OVERALL PASS. Stale NaN version preserved at `runs21/superseded/law_grid_analysis_nan_stale.txt`.
- Report: `runs21/law_grid/law_grid_analysis.txt` — OVERALL PASS. Cleared for R7-e.

## R7 Stage 5 — Cohesion arms (R7-e) — IN PROGRESS (recovered from container restart)
- Paired PXL=0/1 same-seed F_EXT=4 clamped (O-X3 gate: H_ON > H_OFF both seeds, ratio ≤ 1.5) + PREL=300k release diagnostic. Decides O-X3/O-X4.
- DONE: F_EXT=2 arm 4/4 logs OVERALL PASS (`cohesion/arm_f2.0_analysis.txt`); release pair (F4, PREL=300k) both PASS (`cohesion/release_f4.0_analysis.txt`); F4 gate ON s77031 PASS (sha256 482fce10...).
- INCIDENT 2026-09-02 ~16:44 UTC: container restarted mid-stage (PID 1 epoch 16:44, /tmp wiped). F4-gate subagent lost with its shell context (zombie); deleted and re-dispatched. All /mnt artifacts intact; remaining F4 logs (on_s84950, off_s77031, off_s84950) + pooled O-X3 analysis assigned to fresh subagent using existing verified variants/binaries.
- gm-displacement NaN-on-XLNF=1 analyzer fix: RESOLVED (dual root cause: OOM whole-file parse in stage_h_analysis.py → streaming; missing gm-position tracking in stage_h_law_analysis.py → added verbatim). Fixed analyzers a6ede934.../fdcd3bcb...; law_grid_analysis.txt regenerated (94b6585b..., diff = exactly 9 lines, β unchanged); stale copy at runs21/superseded/law_grid_analysis_nan_stale.txt.
- F4 clamped gate completed post-restart: all 4 logs OVERALL PASS (structural/inventory/zero-bookkeeping), O-X4 PASS (rel-rate 1.086/0.936, disp 0.983/1.002, cap-pin ≤2).
- **O-X3 GATE FAILURE (registered stop):** stationary mean XP (xpt, steps>500k, n=1000/arm):
  F=1 (R7-c): ON 10.97 > OFF 9.77 ✓ | F=2: ON 9.452 < OFF 10.057 ✗ (s77031); ON 9.335 < OFF 10.181 ✗ (s84950) | F=4: ON 7.956 > OFF 7.774 ✓ (s77031, ratio 1.023); ON 6.911 < OFF 7.682 ✗ (s84950, ratio 0.900). No comparison degenerate per X-3 (max clamp occupancy 3.8%).
  → Sign is load/seed-dependent, not a clean stiffening. Anomaly: on84950 F4 geo brush height 68.06 vs ~23–50 elsewhere, final XP at XPLO clamp.
  → Per plan_crosslink.md O-X3 ("if the sign is wrong, stop and register a geometry/sign investigation before any amendment"): O-X3 track STOPPED; R7-f and docs/archive blocked pending investigation. Checked in with user.
- Investigation (`cohesion/OX3_INVESTIGATION.md`): contractile internal-tension network — links born compressed (⟨d_birth⟩≈1.26<DX0), live stretched (≈1.86>DX0), rupture overstretched; top layer pulled down 73–76%; causal growth inhibition p≤1.7e-7; lateral-compaction and tilt hypotheses refuted. X-4 (x95 instrument, flipped sign) re-scored by independent verifier: FAIL — underpowered (Neff 23–50) and load-dependent (null at F4 s77031); FRCT incidence diagnostic retracted.
- Amendment X-5 (user-approved): O-X3 split — O-X3a microscopic mechanism gate (existing logs) + O-X3b 6-seed ensemble gate (16 new runs, seeds {6203,34567,92869,55631} added, x95 over bound monomers, ≥5/6 seeds Δ<0 + one-sample t p<0.05 per load; load-dependence registered as possible finding).
- **O-X3a PASS** (`cohesion/OX3A_CERTIFICATION.txt`, script `ox3a_certification.py` sha256 1b2f0f9b...): all 3 criteria in all 5 ON arms — strain cycle 1.24–1.30 / 1.85–1.87 / 2.36–2.39 vs DX0=1.5; top-layer tension 0.740–0.755 > 0.65; growth inhibition p ≤ 2.5e-14 worst-case... (all p ≤ 1.4e-06 except noted). Cross-checks match analyzer txts exactly.
- O-X3b ensemble running: 4 seed-arm subagents (16 runs).
- O-X3b 6-seed re-score FAIL (F2 4/6 + pooled p=0.045; F4 2/6 + p=0.136, load attenuation) → Amendment X-6 (user-approved): pooled over-seeds t as THE statistic, +4 F2 seeds {44729,73553,91229,28387}, F4 attenuation registered as finding.
- **O-X3b PASS, decisive** (`cohesion/OX3B_RESCORE_10SEED.txt` sha256 fd55a987...): 10-seed mean Δx95 = −0.3823, 95% CI [−0.6406,−0.1239], t=−3.347, one-sided p=0.0043; Wilcoxon p=0.0098; 8/10 seeds negative; all 6 prior values reproduced exactly; census cross-checks exact.
- **O-X3 COMPLETE (a+b). R7-e CLOSED.** Cohesion certified: contractile slip-bond network, measurable shortening at low/moderate load, attenuation at high load registered.

## R7 Stage 6 — Integration diagnostics (R7-f) — COMPLETE (architecture-dependent finding)
- Both runs all-gates-green (stage_h + stage_g OVERALL PASS; both inventories exact; zero-bookkeeping exact; xlk occupancy 0.7299/0.7413 IN).
- FORMIN=0 (branched): adhesion occupancy 0.0590 → 0.0767 (+30%), traction 92.7% → 96.5% — crosslinks HELP adhesion (load transmission; adh |F| 3.56 vs xlk 1.39).
- FORMIN=1 (hybrid): adhesion occupancy 0.0627 → 0.0373 (−40%), traction 96.1% → 81.2% — crosslinks SUPPRESS adhesion (substrate-interface competition/shielding).
- Diagnostic flag both arms: nxl pins at MAXXL=24 cap for 7–14 consecutive windows in branched meshes (nfil≈31) — pool-limited, not kinetics-limited; registered for R8+ (non-gating).
- Artifacts: `phi4/runs21/integration/`.
- R6-f handoff answered: crosslinking recovers branched-mesh adhesion only in the branched-only mesh; in the hybrid it worsens it. Input to R8 bundle-polarity design.
- R7 vs exit criterion (plan_crosslink.md §10): gate-clean (O-X1), continuous formation/rupture with certified slip law (O-X2/O-X6 β=0.995310±0.002709), measurable cohesion without freezing (O-X3a mechanism + O-X3b 10-seed p=0.0043 + O-X4), all inventory/conservation oracles exact (O-X5). **R7 PASSES.** Proceeding to docs + checkpoint.

## R7 Stage 7 — Report and checkpoint — COMPLETE (R7 CLOSED, PASS)
- `phi4/CROSSLINK_LAW.md` written (651 lines): mechanism as certified, all six amendments, full certification chain, O-X3 contractile-cohesion saga in five acts, R7-f architecture-dependent integration finding, O-X1..O-X6 scorecard all PASS, artifacts with sha256s (44 run logs), reproduction block.
- `phi4/ANALYTICS.md` updated (MAP 6 R7 section appended; existing content byte-preserved).
- Verified checkpoint archive: `actin_phasespace_r7_crosslink_checkpoint.zip` (2.76 GB, 297 entries, `unzip -t` PASS, zip sha256 2bf40028..., engine hash inside re-verified = a3ed4334...). Built on local disk after two FUSE mount drops, then copied to /mnt.
- Provenance incident: `r6_workspace/repo/.git` vanished (container/FUSE incident); original R7 merge commit 7ff0566 lost. REPAIRED: R6 bundle cloned from R6 checkpoint zip, R7 state recommitted (526194a) with incident note, new complete-history bundle at `actin_phasespace/r7_repo.bundle` (sha256 a86227f3...), live repo restored in the workspace.
- Check-ins this rung: O-X3 gate failure → investigation → amendments X-4/X-5/X-6 (all user-approved); container restart zombie-agent recovery; .git provenance loss/repair.
- **R7 filamin-like crosslinking: CERTIFIED. Next: R8 bundle polarity (roadmap: R8 → R9 minimal parallel bundle → R10 myosin → R11 stress fiber → R12 filopodia/motility).**

## R8 Stage 0 — Oracle registration — COMPLETE (user-approved)
- Compiler integrity verified against the user's original upload BEFORE any R8 build: 30/31 files byte-identical; the single delta is the user's own FMA-SUB codegen fix in `ir_codegen.py` (`c_op = "+"`, one line + 3-line comment), matching the user's uploaded `ergo-fragile-fma-compiler-fix.md`. User confirmed: "is this the only change? that's all I need to know."
- R8 oracle drafted and registered as `phi4/plan_bundle.md` (2026-09-03): PBUND∈{0,1,2} polarity gate on crosslink attach; cosθ = t(I)·t(J), tangent `t(B)=unit(P(B+1)−P(B−1))`, interior-tangent eligibility (contour ≥4 monomers); COSB=0.5; PBUND=1 parallel (cosθ ≥ +COSB), PBUND=2 antiparallel (cosθ ≤ −COSB); **deterministic acceptance, zero new RNG draws**; PBUND=0 must be byte-identical to the R7 parent; **slip-law carryover** from R7 (no XLNF=1 law grid — any change to the force/rupture code path voids the carryover); `bpol STEP I J cos` record (PBUND>0 only); oracle ladder O-B1..O-B5; stages R8-a..f; failure-mode responses pre-registered (eligibility-flux-first, sign-error zero tolerance, PBUND=0 divergence = bug).
- User registration: **"Looks good for now. We can revise if and when we run into roadblocks."**
- **Binding space constraint:** no checkpoint zip until explicit user go-ahead ("don't zip anything up till I give a go-ahead... The files are massive"). R8 runs slip-law only (XLNF=0), ~56 MB/log.
- Parent engine: `phi4/brush_xlk.ergo` sha256 a3ed43347392aa97f7ad2bde5ad0d7c1ce0e09e244220cedba59edc7ea46944a (DO NOT MODIFY).

## R8 Stage 1 — Build, static/FD certification, review, merge (R8-a) — PASS
- `bundle_pol.ergo` built (builder subagent): 8 hunks, **245 added lines, 0 parent lines touched**; engine sha256 `fb1c8d281b72816304a8bf13e9b66e815ec75200c20803c31879011b46507935`. POLGATE subroutine (tangent pointed→barbed via NEXTM/PREVM; eligibility interior AND FILLEN≥4; PBUND=1 cos≥+COSB, PBUND=2 cos≤−COSB; deterministic, zero RNG); gate call after R7 Bernoulli + pool checks, before commit; `bpol STEP I J cos` (%.6f) after xlka.
- **Certification (O-B2 statics):** sign battery zero errors (PBUND=1: par acc cos+1.0 / anti rej cos−1.0; PBUND=2 exact reverse; eligibility negatives all rejected); energy CERT_XL=0.25=KXLK(d−DX0)² exact; differential force ±1.0 x̂ bitwise; central FD error 7.62e-10 < 1e-8; RNG scan 25=25 sites, span 4700–6873 untouched; MIRROR PXL=0/PXL=1 dumps byte-identical to parent lineage hashes; 50k equivalence smoke PBUND=0 ≡ parent byte-identical (`007e6b2b…`, crosslink channel active, zero bpol); runtime gate conformance 369/369 + 416/416 xlka=bpol, cos windows clean, inventory exact, max|netf|=0.
- **Independent review: GO** (all 8 checklist items PASS; sign convention traced through parent source — NEXTM points pointed→barbed; runtime cross-check gate cos 0.770929 vs gm-axis dot 0.770689). Spec-ambiguity flag (§4.1 dead "end-bead tangents" phrase): strictest reading accepted; one-line clarifying amendment noted for R8-b, non-blocking.
- **Independent verification: 6/7 reproduced** incl. re-execution of all cert binaries. Item 2 (binary byte-hash recompile) not reproducible *by toolchain design*: `driver.py:239` embeds a random tempfile name (`mcl_XXXXXXXX.c`) as an STT_FILE symbol — exactly 8 bytes differ between any two compiles; all other 74,208 bytes bit-identical ⇒ provenance holds. **Registered process note:** certified artifact = engine source hash; binary hashes recorded as-shipped (same property held for all R6/R7 binaries; compiler frozen per user verification, not patched).
- Merged: repo commit `d84f3c6`. Artifacts: `phi4/runs22/` (SELFTEST_I.md, SHA256SUMS, static_cert/, smokes/; 14 MB, no archives per space constraint).

## R8 Stage 2 — O-B1 gates (R8-b) — PASS
- Both arms byte-identical to archived R7 parent 300k logs: gate1 (PBR=0) child=parent=`a67e3bbfd5a9ca7e89ee2087916eec3844aec88f562bbd3414b871792f6545e5`; gate2 (FORMIN=1) child=parent=`db4b42fb5a21335f47a55781e99397bc383e738bb644c114ffb50abf5ca84ed6`. attempt=1, FINAL×2, NUL=0, zero bpol. Variant diffs = exactly one anchored line each (PBR=0 / FORMIN=1), matching the R7 edit sets. Artifacts `phi4/runs22/gates/`.

## R8 Stage 2b — Analyzer adaptation (parallel with R8-b) — GO
- `phi4/runs22/stage_i_analysis.py` (sha256 4d2b399c…): stage_h streaming architecture preserved; adds bpol parse, live-cosθ replay at gm dumps, polarity-class populations, per-class lifetimes/spacing/sliding, bpol-vs-replay consistency. Replay topology EXACT (exact-cover solver for unrecorded pointed-end prepends, constrained by fil-record lengths; certified 0 errors at 300/300 gm dumps on real logs). Monomer axes rejected as unreliable (flip in disordered junctions).
- Synthetic validation 8/8 exact (par/anti Δcos=0.0000, orthogonal drift, rupture lifetime exact, no-bpol parent mode byte-identical to stage_h, prepend/branch/nuc-recycle reconciliation exact). Real smokes: bpol1 369/369 parallel (100%), bpol2 416/416 antiparallel (100%); end-to-end exactness proof Δcos=−1.2e-07 at dump-step attach; shared metrics byte-identical to stage_h on identical logs. Doc: `runs22/ANALYZER_I_VALIDATION.md`.

## R8 Stage 3 — Constructed-pair smoke (R8-c) — PASS
- Variant `runs22/r8c/r8c_pairs.variant.ergo` (sha256 311a05d4…): purely additive PCERT=0/1 amendment (INIT_CERT seeded geometry under MIRROR=0 dynamics; guard touches only R8-added lines; zero new RAND sites). Inertness proven: PCERT=0 50k smoke byte-identical to parent (`007e6b2b…`); MIRROR sign battery + FD re-run byte-identical to static_cert.
- Constructed-pair smokes (PCERT=1, F_EXT=0, 300k after 100k pilot <100 attaches): PBUND=1 — 133 attaches, cos ∈ [+0.5025, +0.9990], 100% parallel, **zero sign errors**; PBUND=2 — 87 attaches, cos ∈ [−0.9931, −0.5006], 100% antiparallel. Eligibility negatives: zero attaches both arms (structural proof + min|cos|>0.5 observed).
- **O-B3 PASS both arms, both readings:** lifetimes median 895.0 (n=133, max 7050) / 831.0 (n=87, max 6353); S(10×med)=0, max<20×med. Ratios vs R7 brush-smoke median 542.5: 1.65/1.53 (IN [0.5,2.0]); vs slip-law prediction at measured stored force (⟨|F|⟩≈0.70–0.78): 0.70/0.60 (IN). Slip-dominated rupture causes (R7-like).
- **O-B5 PASS both arms:** constructed census conservation exact (39), ghost scan clean, inventory exact incl. the predicted single t=0 orphan xlkr (XLBORN=0 cert link), max|netf|=0 over 600+600 windows, FINAL, NUL=0, nfil continuity exact.
- Caveats registered (non-gating): stage_i analyzer certified for R7-parent census only — constructed-census logs analyzed by dedicated `r8c_constructed_analysis.py` (event-record sections agreed exactly where comparable); eligibility flux thin in constructed geometry (attach rate 3–5e-4/window; 4-mers fluctuate around FILLEN≥4 floor) — measurable, no STOP; geometry amendment available if richer constructed stats ever needed.

## R8 Stage 4 — Brush smoke (R8-d) — PASS
- PBUND=1 brush (PBR=0/FORMIN=0/PADH=0, F_EXT=1, seed 77031, 1M): log 56.7MB sha256 bbcc44da…, attempt=1. O-B5 clean; instrument conformance perfect (xlka=bpol=8876, min cos 0.500005, zero sign errors); occupancy 0.3088 (≫0.05 floor), turnover continuous, balance 0.0007, drift 0.052 — all windows IN. Lifetime median 594 vs control 544 (1.09×); rupture-cause shift (unbind 71 vs 1514 — endpoints protected by bundling). First selectivity read: live parallel fraction 0.3787 vs R7 control 0.2396 → **1.58×** (below the registered 2.0 — early warning noted); antiparallel depleted 0.61×. Brush taller under parallel bundling (49.4 vs 41.9).

## R8 Stage 5 — Selectivity ensemble (R8-e) — RUNS COMPLETE; **O-B4 FAIL as registered — STOP registered**
- 3 new runs (PBUND=1×84950, PBUND=2×{77031,84950}) + R8-d reuse arm: all clean (O-B5, instrument conformance, zero sign errors, cos windows [±0.5000.., ±0.9999..]). Control cross-check exact (0.2396/0.2778/0.4825).
- **O-B4 formal verdict: FAIL overall** — live-fraction enrichment all four arms 1.58/1.59 (PBUND=1), 1.62/1.64 (PBUND=2) vs registered ≥2.0. Every secondary window satisfied on every arm (occupancy 0.28–0.32 ≫ 0.05; balance ≤0.002; drift ≤0.16; turnover continuous; lifetimes 0.91–1.09× control).
- Root cause visible in the data: attach-class purity is 100% (deterministic gate) — the live-fraction dilution is post-attach ROTATIONAL DRIFT of links between gm dumps; the ≥2.0 live-fraction factor conflates selection (perfect) with persistence (finite). Opposite-class depletion 0.56–0.61× all arms.
- Analyzer caveat registered (verdict-insensitive): stage_i pointed-tip prepend ambiguity on dense logs (13/6538 samples flagged on pbund1_s84950; sensitivity shows no 4th-decimal change; latent ≤0.0003 elsewhere). Registered analyzer-replay tightening as a candidate amendment independent of O-B4.
- Decision record `runs22/r8e/OB4_DECISION.txt`. Per the standing snag protocol: investigation of the correct persistence instrument launched BEFORE any amendment; user check-in follows.

## R8 Stage 5b — O-B4 instrument investigation — COMPLETE
- `runs22/ob4_investigation/ob4_age_analysis.py` (sha256 53799a77…) + `ob4_report.txt`. Reproduces registered numbers exactly. Age-stratified enrichment: age<250 bin 0.611/0.609 (PB1), 0.687/0.708 (PB2) → 2.47–2.56× control, all arms ≥2.0; by age ≥500 the live population is statistically indistinguishable from control. Persistence half-lives 210/213/283/288 steps = 0.35/0.36/0.56/0.58× lifetime median. One-compartment mixture from measured persistence × lifetime predicts steady-state enrichment 1.564–1.618 vs observed 1.580–1.643 (ratio 0.998–1.016) — the registered unstratified 2.0 was physically unreachable; ~1.6 is the ceiling. Control age structure mildly non-flat (±0.052); conclusions hold under both denominators. Sensitivity: max per-bin shift 0.0038. Candidates 1–4 with measured yields; recommendation: age<250 ≥2.0× primary + persistence half-life secondary.
- External review (user-relayed, Deepseek): adopt age-stratified criterion; register primary <250 ≥2.0×, secondary half-life ≥0.3× median, tertiary steady-state within 5%; "physics has spoken". USER DIRECTIVE: **verify the 1.6 independently first — "if it is we know the timing. Rotation is basically inevitable here, we just need to measure how much it rotates over time."**

## R8 Stage 5c — Ground-truth verification of the 1.6 + rotation timing — COMPLETE; **O-B4-AMENDED (B-1) USER-REGISTERED; R8-e CERTIFIED**
- lpol engine-native instrument (`runs22/ob4_verification/`): additive-only variants of R8 engine + R7 parent; stripped logs BYTE-IDENTICAL to certified logs on all 3 verification runs (dynamics-neutrality by construction). Ground truth vs replay: enrichment 1.574 vs 1.580 (PB1), 1.624 vs 1.620 (PB2); control fractions ≤0.002; age bins ≤0.005; half-lives 212/284 vs replay 210/283. Replay analyzer VALIDATED as an instrument.
- Rotation timing certified: ~54–56° RMS per 500-step dump, age-independent, control-identical (53.6°) — rotation is universal thermal diffusion, not a gate effect; τ_cos ≈ 130 (PB1) / 295 (PB2) steps; per-link first-exit KM median 405/428 steps vs lifetime 594/501.
- **Amendment B-1 registered in plan_bundle.md (user-approved):** primary young-link (<250) enrichment ≥2.0× (2.55/2.54 PB1, 2.47–2.49/2.55 PB2 — PASS); secondary half-life ≥150 steps and ≥0.3× lifetime median (0.36/0.57 — PASS); tertiary steady-state within 5% of mixture prediction (0.998–1.016 — PASS, diagnostic-only). **O-B4 PASS under B-1; R8-e CERTIFIED.** Age cutoff ≤250 locked; lpol kept out of the certified engine; replay-tightening deferred to R9+ candidates.

## R8 Stage 6 — Antiparallel branched-mesh diagnostic (R8-f) — PASS (books/signs); findings as ranges
- Doctrine change (2026-09-03, user-registered via plan_filopod.md): force-first certification — hard gates = force closure/FD/energy/conservation/inventory/instrument-neutrality + zero sign errors (correctness); emergent distributions = measured ranges, never thresholds. Autonomous execution; halts only on hard-gate failures; multiple-choice prompting suspended (UI freezes).
- R8-f (PBUND=2 branched mesh, PBR=1/FORMIN=0/PADH=1, F_EXT=1, seeds {77031,84950}, 1M; runs found pre-existing in runs22/r8f, provenance fully re-verified): **books PASS** (conservation exact 400, ghost 0, xlk+adh inventory exact, max|netf|=0 ×2000 windows/seed, event-exact nfil continuity); **signs PASS** (24,436 bpol all cos ≤ −0.5, zero errors).
- Measured ranges: occupancy nxl/nfil 0.392–0.433 (R7-f: 0.730; gate halves attach rate); **MAXXL=24 pinning: 0/1000 post-burn-in windows both seeds — the R7-f watch item RESOLVES under PBUND=2** (R7-f had a 7-window pinned run); xlk |F| live 0.868–0.917, rupture median 1.52–1.68; adhesion |F| mean 2.07–2.52; polarity persistence in mesh: live antiparallel 1.705–1.706× control, half-life 275–295 steps ≈0.41–0.42× lifetime median, mixture model predicts 0.393/0.408 vs observed 0.388 (steady state = attach purity + drift, engine-native lpol cross-check agrees); rupture mix slip 80–82% (endpoint causes ~3× rarer than R7-f); lifetimes 657–718.
- Caveat registered: analyzer topology-reconstruction gate FAILs on dense branched logs (~60k invisible within-window bind/unbind pairs) — doctrine: reported limitation, bounded by exact-subset replay (max|dcos|~1e-6) + lpol cross-check. s84950 FINAL lenfil 0 = dissolved seed filament record artifact (mesh healthy, nfil=31).

## R8 Stage 7 — Report and documentation — COMPLETE (**R8 CLOSED**)
- `phi4/BUNDLE_LAW.md` (777 lines): engine identity, mechanism, B-1, 10-step certification chain with numbers, L-B1..L-B6, failure-mode register, limitations, space discipline. `phi4/ANALYTICS.md` MAP 7 added (+91 lines). All quoted figures traced to artifacts; artifact hashes recomputed. R8-f section integrated from runs22/r8f/R8F_REPORT.md.
- No checkpoint zip (user space constraint stands; go-ahead required). R8 engine `runs22/bundle_pol.ergo` fb1c8d28… is the R9 parent.

## R9 Stage 0 — Oracle registration — COMPLETE
- `phi4/plan_filopod.md` registered 2026-09-03 under force-first doctrine: minimal parallel bundle (filopod_min.ergo) = R6 adhesion + R7 crosslinks + R8 PBUND=1 + FORMIN channel + deterministic seeded parallel cluster + tip instrumentation. Hard gates: O-P1 inertness byte-identity, FD/books battery, O-P4 tip traction/stall vs unbundled control (method pre-registered, threshold-free). Ranges: O-P2 polarization, O-P3 persistence, O-P5 turnover, lengths. Log budget <1GB. Stages R9-a build/FD/review/merge → R9-b gates → R9-c smoke+force → R9-d ensemble → R9-doc.

- R8-f integration landed (BUNDLE_LAW.md 958 lines, 25/25 markers verified; ANALYTICS.md 329). Tooling hazard registered: parallel-batched edit_file calls can report success without persisting — doc edits must be applied singly and re-verified by grep (detected and corrected by the doc agent).

## R9 Stage 1 — Build, static/FD certification, review, merge (R9-a) — PASS
- Engine `runs23/filopod_min.ergo` sha256 **6a343fde…f498d8f**; additive +525/0 on certified R8 parent (parent fb1c8d28… re-verified untouched). Registrations appended to plan_filopod.md BEFORE build: PCLU seeded cluster (5×8, slots 1–5, monomers 1–40, cross spacing 1.5=DX0, pointed anchors x=2.0, barbed heads 6.70, gas from same INIT_DYN stream — zero new RNG draws); FORMIN scoped by certified grasp-ring (no code change); PTIPA verbatim R6 slip-bond instance at tip zone (barbed head, PX≥XTIP−RADH, target XTIP=9.0=XP0, RNG block 6900–6963 — corrected from 6962 per review); PTIP records-only `tip/tipa/tipr`.
- Certification: FD vs analytic all composed paths < 1e-8 (exl 1.398e-10, etip 6.756e-10, eadh 6.810e-9); sign battery zero errors both arms (parent CERT_BPOL + cluster CERT_FPOL); MIRROR-off dump byte-identical to parent; **O-P1 50k byte-identity PASS (007e6b2b…, cmp clean)**; cluster smoke 50k books PASS (conservation 400 ×100 censuses, ghost clean, xlk 397/389 + tip 422/412/10-open inventories exact, max|netf|=0, bpol all cos∈[0.500069,0.999560]).
- Independent review: **GO with concerns** (no blockers) — concern 1 RNG block off-by-one → FIXED in oracle (6900–6963); concern 2 cert header overclaim → close at R9-b via amended wording; notes: ntip=active-filament count semantic (documented), O-P1 coverage to be extended at R9-b (PBUND-active arms + 300k), INIT_CLU bounds notes. Independent verification: **CERTIFICATION VALID** all 8 claims; one doc flag → FIXED in oracle (FD bead 96 / PCLU=1 amendment line).
- Merge: repo .git lost again in container restart → restored from r7_repo.bundle (a86227f3…), R8 tree recommitted (1b9b579, hash-verified), R9-a committed **df789f3**; durable `actin_phasespace/r9_repo.bundle` sha256 ab2ad7d8… created (code-only, tiny — not a data zip).
- Process note: builder hit the batched-edit_file silent-drop hazard (3 calls), self-detected via inconsistent cert evidence, full line-by-line re-audit, all certs from final audited engine.

## R9 Stage 2 — O-P1 gates (R9-b) — PASS
- 6/6 rows byte-identical (PBUND∈{0,1,2} × seeds {77031,84950}, 300k, all new channels OFF): child sha256s 16c9db1c…/5636a7eb…/b84d72e1…/c5444043…/cb3e60fe…/8ddb802b…; all statuses OK attempt=1, NUL=0, FINAL ×2.
- Provenance correction registered: briefing premise wrong — runs22/gates/ holds only OB1-era off-matrix logs (PXL=0/F_EXT=0.1); no 300k brush-config parent refs ever existed. All 6 parent refs run fresh under R9-b from the certified parent (fb1c8d28… verified untouched before/after). s77031 parent refs have R9-b provenance (not R8-b) — flagged for the record.
- Known-issue registered (deferred to doc amendment, no hash-changing edit): parent-carried INIT_CERT header wording "pure additions" overclaims vs a PADH=1 baseline (aggregate totals only; explainable, no physics defect).
- O-P1 review note closed: coverage now includes POLGATE-active arms (PBUND=1/2) and 300k steps, both seeds.

## R9 Stage 3 — Bundle smoke + O-P4 force (R9-c) — COMPLETE (books PASS; preliminary O-P4 NEGATIVE at s77031)
- Runs: bundled 58.5MB sha256 2144637e…, control 59.0MB e5a818e4… (both OK attempt=1, 1M, seed 77031). Engine 6a343fde… verified unchanged.
- Books battery BOTH ARMS PASS: conservation exact ×2000 censuses, ghost clean, xlk inventory (10477/10468 bundled; 20495/20476 control), tip inventory (10205/10195/10; 10064/10055/9), max|netf|=0, nfil event-exact, bpol zero sign errors (min cos 0.500026).
- **O-P4 preliminary (seed 77031, n=1000 matched windows): bundled trx mean +0.5113 vs control −0.0081 (Neff≈415, Welch t=1.97, p=0.024 — significant but small vs sd≈3.7–3.9). NEITHER pre-registered limb met: distributions fully overlap (not disjoint); no ≥1.5× factor (magnitudes 0.936×, favor control slightly). No differential stall (xp static ~10.5 both arms; fluctuating steady state).** ≥1.5× limb degenerate on signed trx (control mean≈0) — method note for R9-d.
- Mechanism: tip adhesion bonds are the load bottleneck both arms (tipr rupture |F| median 2.66/2.70, 97% above FBA=1.0, cause-1 dominated) — shaft alignment doesn't amplify tip traction. Bundling halves xlk occupancy (8.28 vs 16.93) and lowers npoly (91.2 vs 122.3).
- Measured ranges: bpol purity 1.0000 (mean cos +0.763); persistence — bundled incumbents slots 1,2 survive all 1M, cluster occupants ~100× ordinary filament lifetime (median 5088/3530); cluster lengths mean 19.0/24.7; grips 10.9/12.1; tip occupancy 9.8/10.7.
- Full polarization gm-replay deferred to R9-d (stage_i certified vs runs22 schema; R9 records additive — adaptation + engine-native cross-check required per the dense-branched lesson).

## R9 Stage 4 — Measurement ensemble + pooled O-P4 verdict (R9-d) — COMPLETE; **O-P4 FORMAL VERDICT: FAIL (physics finding, not a bug)**
- s84950 arms (bundled 58.1MB 342c9f16…, control 58.8MB c59f9684…) + lpol verification run: all hard checks PASS both seeds (books exact ×2000 censuses, inventories exact, max|netf|=0, bpol cos∈[0.500161,0.999973] zero sign errors). lpol variant stripped log BYTE-IDENTICAL to certified r9c bundled s77031 log → instrument valid; replay vs lpol ≤0.0013 on every class/age bin → replay stands for all 4 arms (pre-burn-in flagged dumps excluded; measurement window reconciles exactly).
- **Pooled O-P4 (4 arms): disjoint limb NO both seeds; magnitude limb |tr| 0.9506 (p=0.978), |trx| 0.9436 — <1.5, wrong direction; signed-trx difference +0.3406 (0.7011 vs 0.3606), t=1.86, p=0.0317 — significant but satisfies neither limb. O-P4 FAIL.**
- Root cause (registered finding): **tip-linkage bottleneck** — bundling polarizes the interior (live par 0.374/0.376 vs control 0.241/0.238 ≈1.56×, carried by age<250 at 0.617–0.621 vs 0.242–0.247 — R8 rotation physics transfers exactly) but tip-bond occupancy (9.8/10.7), rupture |F| (2.66/2.70, ~97% > FBA), and formin grip are unchanged; traction is set by the tip interface, not bundle polarization. Bundling halves xlink occupancy (8.3/7.8 vs 16.9/15.7) and turnover; npoly effect seed-dependent (91 vs 122 @77031; 142 vs 112 @84950).
- **R9 exit criterion ("force-bearing") NOT met.** Awaiting user direction: close R9 with the finding registered and proceed to R10 design (tip bottleneck on the table), or iterate tip architecture first. R9-doc (PARALLEL_BUNDLE_LAW.md + MAP 8) pending that decision.
- Artifacts: runs23/r9d/R9D_REPORT.md + full analysis suite. Tooling hazard reconfirmed: duplicate edit_file calls to same file in one message can silently clobber — one edit per message per file.

## R9 disposition — CLOSED WITH FINDING (user directive 2026-09-03)
- User: over token budget, proceed directly to R10 ("its a vital part"); project organization deferred to manual user review. R9 closed as: certified engine (R9-a/b), polarized bundle, O-P4 FAIL = tip-linkage bottleneck (registered design target for R10/R11 force transmission). R9-doc deferred — to be folded into a combined doc pass when budget allows.

## R10 Stage 0 — Oracle registration — COMPLETE
- `phi4/plan_myosin.md` registered under force-first doctrine: myosin_unit.ergo on certified filopod_min parent (R9 channels OFF in R10 configs); constructed antiparallel pair, fixed endpoints first; bipolar motor walks barbed-ward; force-dependent stall + Bell unbinding; records-only instrumentation. Hard gates: O-M1 byte-identity, FD<1e-8 motor path, O-M2 directionality as sign-correctness (zero tolerance), books+myosin inventory. Force measurements: O-M3 contraction vs parallel control (parallel MUST NOT contract — hard sign limb), O-M4 force-velocity/stall. RNG block must start above 6963.

## R10 Stage 1 — Build, static/FD certification, review, merge (R10-a) — PASS
- Engine `runs24/myosin_unit.ergo` sha256 **2806ed05…110f**; additive +748/0 on certified R9 parent (6a343fde… re-verified untouched). Registrations 1–6 + addenda appended to plan_myosin.md before build: PMYO∈{0,1,2}, RNG block 6970–7001 (above registered max 6963), motor law (KMYO spring superposition, stall clip at FSTALL=4, Bell slip, SMAXM hard release), constructed antiparallel + parallel units (both-ends-anchored amendment), step-0 constructed myoa, 50k sign-criterion interpretation.
- Certification: channels-off mirror byte-identical to R9; cert_myo1 parent CFG(102)/FRC(102)/CERT lines byte-identical to R9 cert base; CERT_MYO emyo=0.25 exact; motor force analytic ±1.0 ŷ exact, differential machine-exact; FD channel-isolated emyo (total-energy FD impossible — ewca ulp 7.6e-6 > signal, numerically justified): beads 105/113 err 3.2e-10/7.6e-10 < 1e-8. **O-M2 sign battery 15/15 clean** (PMYO=1 heads apart barbed-ward; PMYO=2 both heads same direction, no contraction). **O-M1 50k byte-identical (007e6b2b…)**.
- Micro-smokes (fixed-endpoint, frozen track kinetics): books PASS both arms (conservation, motor inventory cum(myoa)−cum(myor)=nmyo exact ×100 windows, max|netf|=0); PMYO=1 tension saturates at stall scale (meanf 4.27 vs FSTALL=4, max 5.06, no runaway, meand 1.5→3.2–4.0); PMYO=2 control non-contractile (meanf ≤0.71); turnover dynamic (14/13, 6/5 — no clamp).
- Documented exception (registered reg. 6 addendum, verified independently): 1/107 myost negative lab-x = transient tip buckling under stall; stepping rule is contour-based (NEXTM), invariant MNEW=MOLD+1 holds 150/150 — geometry, not a sign error.
- Combined review+verify (budget measure): **CERTIFICATION VALID, GO for merge**; 3 notes (machine-exact phrasing; two imprecise quoted ranges — quote computed bounds at R10-c; anchor unbind-transfer inert under frozen kinetics, resolve before live-kinetics arms; R10-c hard sign check = contour invariant, lab-x as range metric).
- Merge: .git wiped by container restart (3rd time) → restored from r9_repo.bundle (ab2ad7d8…), committed **8beb34d**; durable `actin_phasespace/r10_repo.bundle` sha256 3d941a04…

## R10 Stage 2 — O-M1 gates (R10-b) — PASS
- 6/6 byte-identical (PMYO=0 × PBUND∈{0,1,2} × seeds {77031,84950}, 300k) vs R9-b references (hashes verified pre-use, not rerun): child sha256s equal reference sha256s exactly (16c9db1c…/5636a7eb…/b84d72e1…/c5444043…/cb3e60fe…/8ddb802b…). All OK attempt=1, FINAL, NUL=0. Variant diffs anchored-only. Engine 2806ed05… untouched before/after.

## R10 Stage 3 — Constructed-unit measurements (R10-c) — PASS all oracle classes (**R10 exit criterion MET**)
- R10-c registrations appended to plan_myosin.md first: matrix (PMYO=1 antiparallel + PMYO=2 parallel at KSEED=5.0; PMYO=1 sweep KSEED∈{2,1,0.5,0.25,0.1}; 300k, s77031, frozen track kinetics). Resisting-load mechanism: **KSEED anchor-compliance sweep** (F_EXT lives only in the PSTN piston channel, off for constructed units; KSEED is the sole force path on the constructed tracks — registered with rationale, zero RNG-stream change).
- **O-M2 (hard): 2809/2809 myost contour-correct, zero violations** (lab-sign degrades only in soft-anchor arms = registered buckling geometry, not error). **O-M6 (hard): PASS all 7 logs** (conservation ×600 censuses, motor inventory exact every window, max|netf|=0 awk re-derived, NUL=0, FINAL).
- **O-M3: antiparallel meanf=4.30 vs parallel 0.36 (12×; parallel control silent, meand≈rest) — hard parallel-silence limb PASS.**
- **O-M4: force saturates 4.30 (max 5.17, no runaway); velocity collapses 0.50→0.023 as force crosses ≈4.5 — stall at the registered FSTALL=4.0 scale. PASS.**
- **O-M5: turnover balanced at all loads (arate=rrate), 100% Bell-slip, max lifetime 31154≪300k — no clamp.** Contractile arm turns over ~2.7× faster than control (Bell law).
- Report `runs24/R10C_REPORT.md`; 7/10 budget runs used; engine hash untouched. Finding registered: barbed-end parking at low tension (track-length effect, no tuning).

## R10 Stage 4 — Combined documentation pass (R9+R10) — COMPLETE (**R10 CLOSED; R6–R10 ALL CLOSED**)
- `phi4/PARALLEL_BUNDLE_LAW.md` (530 lines) — R9 law doc incl. O-P4 FAIL headline + tip-linkage-bottleneck finding, L-P1..L-P5, scorecard. `phi4/MYOSIN_LAW.md` (503 lines) — R10 law doc, L-M1..L-M5, O-M1..O-M6 all PASS, exit criterion MET, R11 numbers table (stall 4, velocity 0.50→0.023, turnover). `phi4/ANALYTICS.md` 329→465 lines (MAP 8 R9/runs23 + MAP 9 R10/runs24).
- Doc-pass verification: all engine hashes, bundles, additive diffs, byte-identities, FD errors, gate hashes, book counts, O-M2 2809/2809, O-M3/O-M4/O-M5 independently recomputed from artifacts. **Doc-pass correction registered**: R9D_REPORT's "npoly variance lower at both seeds" is inconsistent with its own §5 at s84950 (349.07 vs 195.31) — law doc carries the correction (variance seed-dependent; only flux suppression robust). Caveats registered: runs23/SHA256SUMS references absent build/ dir (reproducible compile artifacts); no O-P6 in plan_filopod (scorecard says so).
- Project state: six certified engines in one additive lineage (brush_bfm → R6 adhesion → R7 crosslink → R8 polarity → R9 bundle → R10 myosin), each channel-OFF byte-identical to its parent; durable code provenance in actin_phasespace/r{7,9,10}_repo.bundle; no data zips (user space constraint); plan.md is the chronological index of every stage, hash, and artifact.

## R11 Stage 0 — Oracle registration — COMPLETE (user go 2026-09-04)
- User priorities (binding): stress fibers + myosin FIRST; adhesion + stress testing FIRST; filopodia/tip LOW PRIORITY (PCLU/PTIPA/PTIP stay OFF in R11).
- `phi4/plan_stress.md` registered: stress_fiber.ergo on certified R10 parent; alternating-polarity segment, both ends R6-adhesion anchored; dynamic myosin ensemble on antiparallel regions; live-kinetics footing (resolves R10 anchor unbind-transfer limitation); O-S3 contractility = headline force measurement (both-ends inward traction + stationary positive tension); O-S2/O-S4/O-S5/O-S6 as ranges; O-S1/O-S7/FD/signs hard. RNG blocks above 7001.

## R11 Stage 1 — Build, static/FD certification, review, merge (R11-a) — PASS
- Engine `runs25/stress_fiber.ergo` sha256 **3a6cc866…ed68** (5058 lines); additive +811/−0 (21 hunks) on certified R10 parent (2806ed05… untouched). PSF fiber channel (alternating-polarity segment, barbed-end SF slip-bond grips at both planes — registered deviation reg. 2: pointed grips provably extensile), dynamic myosin ensemble, sever machinery (PSEV), records sfa/sfr/sfas/fib/sev; RNG 7010–7073 (above registered max).
- Gates: O-S1 50k byte-identical (007e6b2b…); mirror_off byte-identical to R10 (3f3269db…); cert_sf1 parent lines byte-identical; CERT_SFA esfa=1.0 exact, FRC ±2.0 x̂ exact; FD bead125 2.8e-10 / bead133 1.5e-9; sign battery 80/80 contour+sign correct both halves; O-S7 books both arms incl. sever (sev 25000 F6→G7, lengths 58/4 exact).
- O-S3 signature present: step-1 traction ±6.0 (3 bonds × 2.0), window-1 +2.88/−1.07, tension positive 94% windows (mean 9.6 2nd half, max 58.6); fiber contracts 8.6→≈0 by ~4k; anchor rupture-dominated as registered (slip 239/241, median lifetime 385; right end bare final 80% of run — corrected wording per C2).
- Combined review+verify: **CERTIFICATION VALID, GO for merge**; 7/7 byte-identical fresh recompiles. UB landmine independently confirmed: single OOB site (STATE over I=1..NB=800, size 400), pre-existing in all parents, STRUCTURALLY CONFINED to MIRROR=1 cert path (cannot reach dynamics); standing rule registered — no non-literal code in INIT_CERT until a parent-fix rung.
- Verifier errata registered in plan_stress.md: (5/C1) as-built left grips (6,15,24) at head-x 4.30, constructed grip d=1.92 not 1.5 → 0.42 contractile preload (same sign, no gate break); step-0 myoa prints RSF constant not true d (record-accuracy defect; R11-c uses gm-derived distances); (6/C2) right-end reattach wording corrected; (7/N4) cause-5 sever-release untested — R11-c sever must cut through link/motor density.
- Merge: .git wiped (4th container restart) → restored from r10_repo.bundle, committed **049ff28**; durable `actin_phasespace/r11_repo.bundle` sha256 bff8bcbd…

## R11 Stage 2 — O-S1 gates (R11-b) — PASS
- 7/7 byte-identical: 6-row matrix (PSF=0/PSEV=0 × PBUND∈{0,1,2} × seeds {77031,84950}, 300k) vs runs24/gates om1 references (hashes re-verified pre-use); child sha256s equal references exactly. PMYO=1 extension row at 50k vs R10-a smoke reference (0a4ba14c…; no 300k PMYO=1 reference exists — registered). All OK attempt=1, FINAL×2, NUL=0. Engine 3a6cc866… untouched before/after.

## R11 Stage 3 — Fiber measurements (R11-c: O-S2..O-S7) — COMPLETE (hard gates PASS; outcome below)
- Progress + LANDMINE registered (2026-09-04): pre-existing parent UB — all INIT_* routines write STATE(I) in a DO I=1,NB loop while STATE is size NMAX=400 (out-of-bounds when NB<NMAX leaves... when loop bound exceeds array size). Latent in ALL certified binaries; empirically harmless (every byte-identity chain holds, incl. R11 mirror_off 3f3269db…), but gcc -O3 exploited the UB to MISCOMPILE newly added INIT_CERT-adjacent code (stale-zero derived arithmetic). Additive-discipline resolution: cert block unrolled with literal constants; INIT_SF uses bounded DO M=1,NMAX; dynamics-path mitigation = O-S1 byte-identity + 1-step construction probe (54/54 fiber monomers position-verified, max err 7.7e-4). RULE for all future rungs: no derived arithmetic in INIT_CERT-adjacent regions; bounded loops only; register in every rung doc. Parent lines cannot be fixed under additive discipline — flag permanently.
- R11-a static cert PASS so far: mirror_off byte-identical to R10; cert_sf1 parent lines byte-identical; SFAC×2 + CERT_SFA esfa=1.0 exact; FD bead125 err 2.8e-10 / bead133 err 1.5e-9 (<1e-8). Errata being registered: motor grip wording (B0+4 both halves, head x=5.5); myor cause 6 "construction overwrite" (INIT_MYO unit motor released at t=0 under INIT_SF, else inventory leak — verified cum(myoa)−cum(myor)=3=NMYO). First traction signs correct at step 1 (end0 +6.003 / end1 −6.001 inward, 3 bonds × 2.0 exact).

## R11 Stage 3 result — R11-c measurement record (2026-09-04)
- Registration-first: "R11-c registrations" appended to plan_stress.md BEFORE runs (matrix; SEVSTEP=500 justified from 50k baseline — the ONLY epoch where the sever cuts through live link/motor density: 6/6 filaments + nmyo=8 + nxl=5 straddling at step 500 vs 0/6 by 1500; O-S3 format; O-S2 two-part; O-S4/O-S5/O-S6 methods). Post-run addendum: run record + reserve decision.
- Runs (runner_r6.sh, sequential, all OK attempt=1, NUL=0, FINAL×2): main_s77031 e72842a9… / main_s84950 e5b2b226… / sev_s77031 f0a6e71e… / sev_s84950 8cfd9240… (all 1M, PSF=1/PXL=1/PMYO=1/PBUND=2, live kinetics). Determinism: main_s77031 byte-identical to smokes/sf_50k.log through 50000; sev arms byte-identical to mains through 499. Engine 3a6cc866… verified untouched before/after. Budget 4/6 used; reserves registered unspent.
- **O-S7 (hard) PASS all 4 logs:** 2000 censuses each; conservation/ghost/motor/XL/R6-ADH/SF per-end inventories exact; fib↔fil census cross-check exact; max|netf|=0.000e+00 every window; nfil continuity; bpol gate spot-check 0 violations (9000+ PBUND=2 accepts at cos≤−0.5). Analyzer r11c_analyze.py cross-validated vs sf_books.py on smoke + independent awk re-derivations. New analyzer-level finding: reg-8 R6 bond transfer at sever emits no event (adhr lifetime-exact re-key by remnant slot); engine books exact.
- **O-S3 (headline force, post-assembly ≥4000; erratum-5 0.42/motor preload noted; gm-derived distances):** main_s77031 end0 75.5% bonded trx **+0.490 inward** / end1 16.1% bonded trx **−0.254 inward**; main_s84950 end0 11.7% −0.056 (~0 mixed) / end1 98.9% **−0.271 inward**; sev_77031 90.2% +0.364 / 93.7% +0.011(~0); sev_84950 84.8% +0.163 / 86.2% +0.046(~0). **Tension positive and stationary in ALL 4 arms** (means 17.26/10.31/10.43/13.25; 93.6–98.3% windows >0; first/second-half means within spread). **Measured finding (anchor competition):** rupture-dominated steady state concentrates load on ONE dominant anchor (seed picks left vs right: 77031→left 75.5%, 84950→right 98.9%); subordinate anchor bonds sporadically with inward (77031) or ~zero mixed (84950) traction. Both-ends simultaneous inward traction demonstrated on main_s77031. Reported as-is per registered failure response (no adhesion tuning).
- **Ranges:** O-S2 (a) bond-assembly latency 500 (constructed fiber, honest); (b) contractile equilibration flen<1.0: 3500/8500 mains; 85500/39500 post-sever. O-S4: antiparallel link density inside myosin region > outside in all 4 logs (0.80/0.70, 0.89/0.75, 0.78/0.42, 0.88/0.59); 20–40% of dynamic links are same-half buckled local-axis antiparallel accepts (bpol records prove gate; finding, not violation). O-S5: flen bounded mains [−3.2,3.3] mean ≈0; tension bounded, netf=0 no runaway; turnover/1k myosin ≈1.2, XL 3.2–7.0, SF-adh 4.4–9.9; nbound ≈329–343 bounded. Homeostasis holds.
- **O-S6: both sever arms REPAIRED.** sev_77031: 6/6 cut, **cause-5 = 3** (myor×1 + xlkr×2 — erratum-7 program-level target MET, lifetime/endpoint-exact), 1 reg-8 R6 transfer; tension 37.7→70.6 spike→~13 sustained, never ≤0 for 10 windows; both ends re-bond from step 1000 at 90%/94% (severed ensemble anchors BOTH ends better than main); all 6 remnants persist and grow (G10: 5→57 monomers). sev_84950: 4/6 cut, **cause-5 = 0 — per-arm target MISSED with geometry reason** (this seed's motor heads had walked off the midplane by 500: left ≤3.5, right ≥6.2; only 2 XLs live, both kept-side at cut; verified by reconstruction); tension 54.3→2.3 dip→~13 sustained; remnants persist (G10: 5→92). Classification REPAIRED on registered criteria.
- Residual notes: live-kinetics per-head dx sign ~50/50 (registered range — buckling + slot recycling; the motor-sign hard gate rests on the R11-a frozen-kinetics 80/80 battery, not live logs). Orchestrator spot-check: main_s77031.analysis.txt numbers independently re-read and match report (75.5%/16.1%, +0.490/−0.254, tension 17.26/14.62, 1960/1993=98.3%, BOOKS PASS).
- **Disposition: R11 CLOSED.** Exit criterion adjudicated: (i) fiber maintains contractile tension — YES, positive+stationary all 4 arms; (ii) transmits inward traction to BOTH substrate attachments — DEMONSTRATED (main_s77031 both ends inward, correct signs, fmag≈2.0 both ends; severed arms re-anchor both ends at 84–94% occupancy); (iii) measured qualification registered: rupture-dominated anchor competition — in the unperturbed steady state one anchor typically dominates and the subordinate anchor's duty/traction is sporadic-to-~zero (seed 84950 left end 11.7%, mixed ~0). Physics finding, not a bug: all hard gates (O-S1 7/7, O-S7 4/4, FD, signs) PASS. No further R11 runs; reserves unspent.

## R11 Stage 4 — Documentation pass (R11-doc) — COMPLETE (**R11 CLOSED; R6–R11 ALL CLOSED**)
- `phi4/STRESS_FIBER_LAW.md` (641 lines) — R11 law doc: doctrine, engine registration (3a6cc866…, 5058 lines, +811/−0, RNG 7010–7073, 7th certified engine), O-S1..O-S7 gate record with verdicts, laws L-S1..L-S6 (tension homeostasis; both-ends traction fmag≈2.0; anchor competition; sever-repair; antiparallel enrichment; live-kinetics sign caveat), scorecard, failure-register dispositions, caveats/provenance (UB-landmine permanent caution prominent; erratum-5 preload; myoa record defect; analyzer reg-8 re-key; reserves unspent 4/6; determinism chains). `phi4/ANALYTICS.md` 465→537 lines (MAP 10, runs25/ index with sha256s).
- Doc-pass recomputation (all from artifacts): engine hash + additive diff; 4 r11c log hashes/sizes; O-S1 7/7 byte-identity (6 gate logs hash-equal to runs24 om1 refs + os1x = 0a4ba14c…); mirror_off 3f3269db…; cert parent-line identity + esfa=1.0; FD 2.8e-10/1.5e-9 re-derived from fd outs; sign battery 80/80 contour+sign re-counted; BOOKS PASS ×4 + netf=0 independently re-derived (4000 census records/log); conservation 400 at 2000/2000 censuses; O-S3 main_s77031 fully recomputed from sfas/fib (75.5%/16.1%, +0.490/−0.254, 17.261/14.620, 1960/1993) — exact; sever records + cause-5 counts re-counted; smoke numbers (94/100, 9.60, 58.59, 239/241, 385, 9940, 58/4) re-verified. **Discrepancies recorded in the law doc (plan files NOT modified):** (a) O-S4 same-half link fraction — plan.md said "20–40%", artifacts give 38.8/39.7/9.5/16.0% cumulative-attach (law doc carries recomputed numbers); (b) erratum-6 "~39.9k bare" computes to 40,060 steps (rounding). Neither affects any gate/law/verdict.
- Git: commit **792bd57** "R11-doc: STRESS_FIBER_LAW.md + MAP 10 (R11 CLOSED)" (17 files: law doc, ANALYTICS.md, plan_stress.md synced to post-R11-c state, r11c_analyze.py + small text artifacts; 56MB logs not committed per practice). Fresh durable bundle `actin_phasespace/r11_repo.bundle` sha256 **948bda1ece14466d2143c0d0a6b289d5495772dbf1c36092d7bf84564d082812**.
- Doc-pass correction (registered): plan.md's Stage-3 "20–40% of dynamic links are same-half buckled local-axis accepts" does not match artifacts — recomputed cumulative-attach fractions are 38.8% / 39.7% / 9.5% / 16.0% (main77031/main84950/sev77031/sev84950). STRESS_FIBER_LAW.md carries the recomputed numbers. Tilde-level erratum-6 note: bare span computes to 40,060 steps (80.1%). No gate/law/verdict affected.
- R11 Stage 4 (R11-doc) verification: all hashes, O-S1 7/7, FD, 80/80 signs, O-S7 ×4, O-S3 numbers independently recomputed from artifacts — exact. Repo commit 792bd57; bundle actin_phasespace/r11_repo.bundle sha256 948bda1e…2812 (git bundle verify OK). **R11 CLOSED — R6–R11 ALL CLOSED.**
