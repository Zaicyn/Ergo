# STAGE C CHECKPOINT + FORWARD PLAN (2026-09-02, ~23:05)

## What is certified/fixed at this checkpoint

### 1. The segfault fix (SEGFIX.md — full document in this folder)
- Root cause: global loop variable F clobbered to MAXF+1 by REBUILD_BONDS'
  internal `DO F = 1, MAXF`; all KINETICS code after a mid-iteration bond
  rebuild ran as a "ghost filament MAXF+1", reading layout-dependent garbage
  and eventually wild-writing (SIGSEGV, crash step layout-dependent).
- Fix: quirk-preserving `IF F <= MAXF THEN` guards + filament arrays bumped
  to MAXF+2. The historical loop-truncation quirk (higher-index filaments
  lose their kinetics turn after any bind/unbind/branch in the same step)
  is deliberately PRESERVED — it is de facto physics of the certified L1
  ensemble.
- Verified: patched-pair gate O-R1 = 0 diffs; ghost scan clean (0/2000 rows).
- Contamination audit: the bug was LIVE in old certified runs (worst: 19/150
  monomers invisibly sequestered in one runs15 f1 run). L1 qualitative laws
  stand; exact numbers carry 2-9% contamination (documented, re-ensemble
  deferred by user decision "No preference" → my call: defer, spend compute
  on R5).

### 2. Engine generation 400 (budget bump, user-approved)
- N_tot 200→400, NB 400→800, NBMAX 650→1300, NSLOT→51200, MAXF 20→32,
  NFILH(33).
- RNG slot-map rebase (collisions documented and removed):
  Langevin 1..2400 | kinetics 3000+4(F-1)..+3 | hydrolysis 3200+M |
  dimers 3700/3702/3710+M | piston 4200 | cap 4300+F | uncap 4400+F |
  branch 4500+2(F-1)/4501+2(F-1). All disjoint at N=400, MAXF=32.
- Gate: brush_br400(PBR=0) ≡ brush_c400g, 0 diffs over 300k.

### 3. Assembly-method decision (ASSEMBLY_OPTIONS.md — the options survey)
- Surveyed actin_swarm lineage for assembly methods (M4C side-branch
  8-spring junction, M4B anchor transfer, M4D crosslinks, plane NPF).
- Empirical tournament (F=0.1 arm, 1M steps each):
  - S1 free daughters, budget 400: n_eng 2.36 — FAILS O-R3 (goal ≥3).
  - **S4 membrane-anchored daughters (brush_bra.ergo): n_eng 3.58, P(bare)
    0.005 — PASSES O-R3.** Winner. Gate: brush_bra(PBR=0) ≡ brush_c400g,
    0 diffs.
- S2 (full M4C junction port) deferred to the gel rung; S3/S5 documented.
- O-R6 instrument fixed (fbr now logs the actual construction basis ABX/ABY/ABZ):
  cos(daughter, tip axis) = 0.3420 ± 0.0000 — exact by construction, verified.

### 4. Laplace analytic screening (LAPLACE_CHECK.md — full document)
- The certified transport oracle applies to the brush ONLY as a hybrid:
  Laplace supply field × certified dynamical suppression factor 0.574.
  Validation: per-tip barbed capture predicted 8.4e-5/step vs engine
  1.14e-4/step → ratio 0.74, no fitted parameters.
- Solver bug fixed: sealed fluid pockets in dense brush → singular Neumann
  system → CG garbage. Fix: connected-component pocket removal + hard assert.
- βP renormalization proven insufficient (transport saturation);
  D/kT rescale proven unnecessary.
- Robust structural findings: engaged-tip supply favoritism 1.4×; supply
  flat over n=3-22; engaged tips are SHORT (n̄=9.3, membrane-born daughters).
- Scripts in laplace/.

## Known open items (explicitly deferred, with rationale)

1. **O-R4 ceiling criterion** — RESOLVED by ratified Amendment B-1
   (2026-09-02): slot-limited branching IS the density regulation; ceiling
   occupancy is an instrumented observable, not a failure criterion.
2. **Smoke load mislabel** — the Stage B smokes ran at F_EXT=0.1 (engine
   default), not F=1.0 as labeled. Impact: none on decisions (S1 vs S4
   ranking is load-robust); the registered F=1.0 oracle is measured properly
   by the Stage C clamped grid (f1.0 × 4 seeds).
3. **runs15 decontamination** — deferred (2-9% contamination documented in
   SEGFIX.md §3; qualitative laws unaffected).
4. **Pointed-axis logging** — add to ftd dump if pointed flux accuracy
   below 1.5× is ever needed (Laplace pointed gap ~65% of engine).
5. **kT plateau 0.6** — inherited brush physics (runs15 ran 0.8-1.3);
   documented, not a blocker.

## Stage C ensemble (runs17/) — status at checkpoint

26 runs on brush_bra (PBR=1, PANCH=1), 1M steps each:
- clamped (XPLO=5.5/XPHI=11.3): F ∈ {0, 0.5, 1, 2, 4} × seeds
  {77031, 84950, 92869, 100788} — 20 runs DONE.
- released (XPLO=1.5/XPHI=11.4): F ∈ {0.5, 1, 2} × seeds {77031, 84950} —
  6 done (relx_*, verified intact) — SUPERSEDED for v(F): free-from-t=0
  protocol hits the initial-transient artifact (see RELEASE_PROTOCOL.md).
- runs18 hold-release grid (brush_bra_r, PREL=300000): F ∈ {0.5, 1, 2, 3,
  4, 6} × seeds {77031, 84950} — 12/12 DONE, verified. v-by-drift found
  geometrically unavailable (12σ box); O-R5 certified in FORCE FORM:
  stall > 6 measured (~8.5 extrapolated, 11.4 thin-brush anchor) vs
  unbranched 2.5–3; margin(F) and clamp occupancy monotone; ⟨FRCT⟩=5.7 at
  F=2 with no XPLO support. See RELEASE_PROTOCOL.md "Outcome".

## Forward plan (next actions in order)

**Stage C analysis — DONE:** items 1, 2, 4 complete (law table load-flat,
O-R3 PASS at F=1.0: n_eng 3.48, P(bare)=0; Laplace hybrid 0.83 across
loads). Item 3 complete in force form (above); velocity form needs a
tall-box engine — USER DECISION PENDING (build now vs defer).

**Stage D (write-up) — DONE (2026-09-02):**
5. BRANCH_LAW.md written and amended: L-R5.1..L-R5.6 laws, O-R1..O-R6
   scorecard (O-R1 PASS, O-R2 BORDERLINE 0.64 vs 0.70, O-R3 PASS, O-R4 PASS
   under ratified B-1, O-R5 PASS force-form ≈4× stall amplification under
   ratified B-2, O-R6 PASS 70.00° exact under ratified B-3), branched-vs-
   unbranched reference table (runs18 nov grid), corrections (blk:bind
   artifact 157-182 → 2-4; brshare 75-80% → 57-72%). Amendments B-1/B-2/B-3
   RATIFIED 2026-09-02 and registered in plan_branch.md.
6. ANALYTICS.md maps 2/3 updated (R5 engagement result; load-sharing law
   validated per-tip, amplification via recruitment). SEGFIX contamination
   headers added to BRUSH_LAW.md and CAP_LAW.md.
7. Checkpoint zip: phi4_stageCD_checkpoint.zip (logs excluded, in place).

**R2 (formin-brush) — DONE (2026-09-02):**
plan_formin.md registered (O-F1..O-F7). brush_bfm.ergo built (brush_bra_r +
per-filament F2-certified formin tether, no RNG draws). O-F1 gates PASS
(0-diff both PBR; ghost scan 0/600×2). Smoke: direct F2 port collapsed
(grip 0.09, spacer pathology) → Amendment F-1 (S0F=0.75, RGRIP=2.5) fixed
(grip 0.24, plane held). Ensemble: 26/26 runs complete and verified
(law grid arms B/C clamped + stall grid hold-release). INCIDENTS: mid-
ensemble /tmp wipe destroyed in-flight raws; direct concurrent streaming to
/mnt reproduced 48MB NUL-sparse heads. Definitive runner21.sh streams to
/tmp, verifies exit/FINAL/NUL=0, copies to /mnt, re-verifies, and retries;
all final logs are clean. Lesson: on this box, only /mnt is durable, and
/mnt must not receive concurrent streaming writes.

Stage F-e write-up DONE: FORMIN_LAW.md certifies O-F1 PASS, O-F2 PASS,
O-F3 FAIL measured (arm B n_eng 1.56-1.70 at F=1), O-F4 FAIL measured
(per-grip blk:bind 0.29-0.71), O-F5 PASS (F_s(B)≈14-16, recruitment-limited),
O-F6 FAIL as composite (isotropic 0.50; length n̄ 15.6-19.0 passes), O-F7
PASS (26/26 exact conservation, zero ghosts). ANALYTICS.md updated.

**Remaining rungs:** now sequenced in `NEXT_STAGES_PLAN.md`:
- R6 adhesion/traction — pre-registered draft `plan_adhesion.md` complete;
- R7 filamin-like crosslinking;
- R8 bundle polarity;
- R9 minimal filopodium-like parallel bundle;
- R10 myosin contractile unit;
- R11 stress fiber;
- R12 full filopodia and motility integration.
- φ5 1D closure and tall-box v(F) remain deferred unless a stage gate makes
  them blocking.
