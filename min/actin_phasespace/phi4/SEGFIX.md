# SEGFIX — F-clobber ghost-filament bug: root cause, fix, contamination audit (2026-09-02)

## 1. Root cause (fully diagnosed via deterministic heartbeat bisection)

`F` is a single global integer. `REBUILD_BONDS()` contains `DO F = 1, MAXF`
and returns with **F = MAXF+1** (21 at MAXF=20, 17 at MAXF=16).

In `KINETICS`, `REBUILD_BONDS()` is called mid-iteration inside the
`DO F = 1, MAXF` loop (barbed promotion, pointed bind, unbind tails, and —
in the R5 branch engine — the branch commit). All code after such a call
within the same iteration then ran with **F = MAXF+1**, indexing filament
arrays one past their end:

- reads: `FILLEN(21)`, `FILPNT(21)`, `CAPST(21)` → adjacent static memory
  (layout-dependent garbage, often plausible floats/ints);
- ghost binds: the barbed/pointed candidate loops ran with
  `HB/TP` derived from `FILBARB(21)/FILPNT(21)` garbage coordinates; when a
  free monomer happened to satisfy `D < RCAP, QQ > QMIN` against that
  garbage, a **ghost bind** fired: a real free monomer was teleported and
  chained into "filament 21" (`FILLEN(21)` incremented in-bounds after the
  array bump test — confirming the mechanism);
- crash: once ghost `FILLEN(21) > 2`, the pointed-unbind path walked the
  corrupt ghost chain → `PREVM(Q) := 0` with wild Q → SIGSEGV (error 6,
  write to unmapped). Crash step varied per build (109k/171k/501k/610k)
  because it depended on static layout garbage — explaining all earlier
  "mysterious" behavior.

Diagnosis method: hash-RNG (`RAND(SN+slot)`) makes trajectories
WRITE-invariant → heartbeat + FLUSH bisection localized the crash to
KINETICS, filament F=14, between pointed-bind loop end and pointed-unbind;
marker `kpp` printed F=21, exposing the clobber.

## 2. Fix (quirk-preserving, gate-clean)

Engines patched: `brush_br2.ergo` (R5), `brush_c200g.ergo` (budget-200
parent), `brush_cg_f1ref.ergo` (reference for L1 patch form).

- Filament arrays bumped `MAXF` → `MAXF+2` (index MAXF+1 reads valid zeros).
- Guard `IF F <= MAXF THEN` wraps every KINETICS F-loop region that can
  execute after a mid-iteration REBUILD_BONDS/DISSOLVE call:
  W1 = whole post-branch-block body (brush_br2 only), W2 = barbed-unbind
  onward, W3 = pointed section onward, W4 = pointed-unbind.
- The historical quirk is *preserved*, not "fixed": after any bind/unbind/
  branch, higher-index filaments still lose their kinetics turn that step
  (loop exits at F=MAXF+1). Changing that would alter the certified
  effective kinetics; guards only make the F=MAXF+1 tail provably inert.

Verification:
- Continuity intent: guard ≡ old behavior wherever old behavior was
  non-corrupt. (Old binaries contained live ghost events, so bitwise
  continuity with old binaries is impossible *and undesirable* — see §3.)
- Gate O-R1 (patched pair): `brush_br2(PBR=0)` ≡ `brush_c200g`,
  **0 diffs** over 300k steps (seed 77031). Ghost scan of patched engines:
  0 mismatches in 2000+2000 census rows.

## 3. Contamination audit of prior certified runs

Ghost detector: census `nfree` (computed as NM − NIN − 2·NDIM) vs actual
`STATE=0` count from the `gm` dump at the same step. A ghost-bound monomer
is `STATE=1` but invisible to `NIN` → `nfree` overcounts → mismatch.

| run | engine | ghost rows | worst sequestration | onset |
|---|---|---|---|---|
| brush_c200 F=1 (old binary, 300k) | unguarded | 411/600 (69%) | 1 monomer | ~74k |
| runs15 bc_f1.0_s100788 (rerun, 1M) | unguarded | 1251/2000 (63%) | **19 monomers** | ~374k |
| runs15 bc_f4.0_s100788 (rerun, 1M) | unguarded | 1238/2000 (62%) | 1 monomer | ~297k |
| guarded reruns (all) | patched | **0** | 0 | — |

Observable shift (2nd-half means), stored runs15 vs guarded rerun:
- F=1: N_f 11.10 → 11.58 (+4%), n̄ 9.49 → 9.71 (+2%)
- F=4: N_f 9.45 → 10.30 (+9%), n̄ 12.03 → 11.11 (−8%)

**Assessment:** L1 qualitative laws stand (binary insertion gate, stall
scale, engagement order-of-magnitude, lifecycle/capping law — all derived
from ensemble patterns far above a 2-9% shift). Exact certified values
carry ghost contamination at the few-percent level (worst case: one f1 run
lost 19/150 monomers late in the run). BRUSH_LAW.md numbers should be
regarded as contaminated at this level; a full guarded re-ensemble of
runs15 is available if wanted (each 1M run ≈ 70 s → 40 runs ≈ 50 min).

The bug predates φ4.5 (present since the REBUILD_BONDS refactor) — all
brush/piston lineage results share it; cap150/pop150 (CAP_LAW) use the
same KINETICS skeleton and should be assumed equally contaminated at
similar magnitude.

## 4. R5 smoke status (patched engine, F=1, 1M steps, seed 77031)

Run completes clean. Log: `br2_smoke_f1.log`.
- O-R1 gates: **PASS** (0 diffs, patched pair)
- O-R2 branch dominance: **PASS** — nbr 670 / total births ≈ 852 = 78.6%
- O-R3 engagement: **FAIL** — n_eng = 1.26 (goal ≥ 3), P(bare) = 9.2%
  (goal < 5%)
- O-R4 stability: conservation 0/2000 ✓; stationarity ✓ (18.66→18.71);
  **ceiling saturation FAIL** — N_f=MAXF=20 for 48% of the 2nd half;
  len 42 transient (slot 7, steps 135k-208k)
- O-R6 angle instrument: |b_x| mean 0.46, flat-ish (mother-orientation
  confound — fbr line needs mother a_x logged next engine rev)

Structural diagnosis: with N_tot=200 the brush equilibrates at N_f≈18.7,
n̄≈8.5 — most tips never reach the membrane plane (xp≈10.9, base≈2,
need len ≳ 14). Branching raised filament NUMBER, not membrane-proximal
pusher density; slot ceiling then choked 8k branch attempts (novbr 8062).
