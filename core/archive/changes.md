# Ergo Compiler — Change Log

Quick index of what changed, where, and why. Bugs are numbered (`F1`–`F107`)
so fixes can be cross-referenced if regressions appear later.

---

## 2026-07-27 — HASH/RAND intrinsics (compiler-level 32-bit hash fix)

**Summary.** Ergo INTEGER is 32-bit, so hand-rolled multiplicative hash
PRNGs in source wrap early and bias conditioned variates — the
rotor-battery engine measured its channel-selection variate at mean 0.22 /
max 0.71 (late channels starved; fabricated a spurious ×10-30 dephasing
boost). Fix chosen: **(a) a validated PRNG intrinsic family** over (b)
int64 INTEGER support — the intrinsic kills the bug class for every
program without touching semantics or the type system.

- **Design:** `HASH(seed: INTEGER) → INTEGER` (non-negative int32
  [0, 2^31-1]) and `RAND(seed: INTEGER) → REAL` (uniform [0, 1), top 53
  bits × 2^-53, exact in f64), both implemented as the splitmix64
  finalizer (Stafford 2013) at 64-bit width — Weyl increment = golden
  ratio 2^64/phi, Stafford's two odd multipliers. Pure functions of the
  seed — no hidden state. Chaining `S := HASH(S)` applies the Weyl
  increment per call (canonical splitmix64 advance); counter-based
  `RAND(SEED + I)` gives independent per-index variates; independent
  streams are just independent seed offsets.
- **Sites:** `core/checker.py` (return types + `(1, 1, "int")` arg
  rules), `core/codegen.py` (legacy: once-per-TU `_ergo_splitmix64 /
  _ergo_hash32 / _ergo_rand01` helpers + `_expr` lowering), `core/ir.py`
  (`Op.HASH`, `Op.RAND`), `core/ir_builder.py` (INTRINSIC_MAP),
  `core/ir_codegen.py` (helper emission + `_emit_inst` cases),
  `core/backends/spirv.py` (64-bit lowering: OpSConvert/OpBitcast widen,
  u64 IAdd/IMul/ShiftRightLogical/BitwiseXor, HASH = >>33 → OpUConvert
  i32, RAND = >>11 → OpConvertUToF × 2^-53; Int64 capability emitted
  whenever a kernel uses HASH/RAND, independent of float precision),
  `Spec/Ergo_Intrinsic_Signatures_Complete.md` (Category 1 section with
  constants and measured statistics).
- **Statistics (tests/prng.ergo, 100k samples, identical on all three
  paths — legacy C, IR-CPU, SPIR-V GPU):** mean 0.499119, variance
  0.083626 (uniform 1/12), lag-1..8 autocorrelation all |r| < 0.005,
  conditional-on-threshold mean 0.498746 and max 0.999988 — the rotor
  failure mode (0.22 / 0.71) does NOT reproduce; determinism: chained
  `S := HASH(S)` checksum 497286391 identical across runs and across
  all three codegen paths. The test file documents the idiom migration
  (32-bit IEOR/multiply chain → `S := HASH(S); X := RAND(S)`).

---

## 2026-07-27 — ATAN2 lowering + multi-accumulator staged reduction

**Summary.** Two blockers from the packed-protein-MD report
(min/pmargin/packed_check.md): the SPIR-V backend had no ATAN2 lowering
(build died on the torsion kernel), and the staged reduction accepted
only a single REAL accumulator (Kabsch/RMSD/Kuramoto sums).

- **F105 — ATAN2 in the SPIR-V backend** (`core/backends/spirv.py`).
  GLSL.std.450 `Atan2(y, x)`, two-operand form: f64 mode evaluates
  f64→f32→f64 (spec 9.10), f32 mode calls directly; registered in
  GLSL_EXT (excluded from the single-arg generic path), GLSL_F32_ONLY,
  and the warning-name table, so the per-kernel compile-time warning
  ("ATAN2 evaluated at f32 … ~1e-7 relative deviation") prints exactly
  like SIN/COS/EXP. `tests/gpu_atan2.ergo`: GPU vs exact f64 ≤ 6e-7
  relative; warning verified. NVVM has no atan2 either — noted, not
  fixed (backend documented as broken).
- **F106 — multi-accumulator staged reduction.** `_validate_reduction`
  → `_validate_reductions` (`core/ir_gpu.py`): N accumulators per loop,
  each required to satisfy the same conservative pattern (one accumulate
  ADD, one write-back COPY of that ADD's result, nothing else reads it,
  straight-line body, start=1/step=1, no array stores), REAL or INTEGER
  (integer sums combined in f64 on device — exact below 2^53); anything
  else keeps the CPU path with a named reason. Device: every accumulator
  seeds identity, per-acc workgroup tree combine (shared array reused
  with a barrier between passes), partials buffer layout [acc][workgroup]
  (slot `acc_i*n_groups + wgid`; single-acc layout unchanged). Host:
  per-acc ordered combine from `acc_i*G` offsets, `(int)` cast for
  INTEGER accumulators (`core/ir_codegen.py`; `KernelPlan.reduction_vars`,
  `_check_loop` returns a 12-tuple).
  `tests/gpu_multired.ergo` (two REAL sums + INTEGER count + a second
  accumulation round onto nonzero accumulators): GPU == CPU bitwise.
- **Integration (min/pmargin/packed_bba5.ergo, --target spirv
  --gpu-fast-math):** the build now SUCCEEDS — Morse bonds (line 242),
  angles (260), torsions (291, uses ATAN2) extract as SCATTER atomic
  kernels. Everything else stays on CPU with named reasons (nested
  loops, too-few-iterations, outer-var dependencies, non-straight-line
  reductions, non-ADD-write-back RMSD). GPU result is deterministic
  (two runs identical) but deviates from the f64 oracle beyond the 0.1 Å
  tolerance on all 8 seeds; the deviation is precision-regime, not a
  bug — an f32-precision CPU build reroutes every trajectory the same
  way (all GLSL transcendentals are f32-only; the system is chaotic —
  the engine's own check doc shows 18% RMSD moves from plain f64
  FP-order changes). Atomic accumulation-order is a smaller additional
  term. Wall: GPU 3 m 38 s vs CPU 2.5 s (~87× slower; 1.15 M launches,
  5.76 M submit+wait cycles — launch/sync-bound per frame per block).
  Verdict: machinery unblocked and validated; this program gains nothing
  from the GPU today.

---

## 2026-07-27 — Nested 2D stencil extraction (flattened single-kernel lowering)

**Summary.** `extract_kernels` only handled single 1D loops; nested DO
pairs (FDTD stencils) always fell to CPU. `linearize_nested_loops` now
accepts a nested pair (outer J, inner I) under a conservative acceptance
check and flattens it to one kernel: the collapsed loop runs `_K = 1..total`
with I/J recovered in a preamble, and every multi-dim access is rewritten
to its column-major linear index computed from the body's own index temps
(`i + dim0*j` — the flat-buffer layout both sides already use).
fdtd_slit_db: **64 s → 2.7 s**, fdtd_sw: **43 s → 0.69 s**, both bitwise
identical to their CPU runs.

- **Acceptance rules** (`core/ir_gpu.py` `_check_stencil_nest`, all
  required, named diagnostic per failed rule — CPU behavior unchanged on
  any rejection): (1) preamble has no array stores / side-effecting ops;
  (2) every WRITE is exactly at `(I, J)` — provably injective over the
  collapsed space; (3) a written array may only be READ at the same
  `(I, J)` — cross-iteration reads (SHIFT/flow) rejected by name;
  (4) every read index is affine in `(I, J)` with coefficient 0 or 1 per
  dimension (PARAMETER bounds resolve via the affine×PARAMETER fix) and
  statically in-bounds over the loop range; (5) 1D stores must not index
  by either collapsed variable (duplicate-write race).
- **Mechanism:** `IRLoop.linearized` flag (`core/ir.py`) — acceptance
  proves write injectivity, so `_check_loop` (`core/ir_gpu.py`) skips the
  affine store-index classification for tagged loops (the flattened store
  index is a computed linear form with MOD/DIV from the I/J recovery that
  the affine extractor cannot read); legality/shape/accumulator checks
  still run. Loop-bound resolution in the linearizer now const-evals
  hoisted bound temps (`NY-1` etc., INTEGER-typed, ambiguity-safe). Host
  fallback for non-extracted linearized loops uses the Issue-4
  `_subscripts` decomposition (already in place).
- **Replacements:** the old pure-write/exact-(I,J) acceptance
  (`_linearize_index_check`) and `_K0` rewrite (`_rewrite_2d_indices`)
  are superseded by `_check_stencil_nest` + `_flatten_access_indices`
  (init nests linearize through the same new path — validated). The old
  helpers remain as dead code.
- **Validation:** `tests/gpu_stencil2d.ergo` (16x12 diffusion blur,
  stencil + copy nests extract, GPU == CPU bitwise); SHIFT-pattern
  rejection probe (`cross-iteration read of written array 'U'
  (offset -1,+0) — SHIFT/flow patterns rejected`, CPU result correct);
  fdtd_slit_db / fdtd_sw bitwise == CPU; standing-wave node spacing
  8.15 cells (oracle 7.91±1 PASS). **Fringe-oracle caveat:** the 65.50
  (λ=16) / 85.00 (λ=20) table values from fdtd_check.md are NOT
  reproducible from any current source — fdtd_slit / fdtd_slit_db /
  fdtd_slit_1d all yield center-side fringe spacings ~75 / ~88 (all
  bitwise-identical profiles), consistent with Fresnel broadening
  (d²/λL ≈ 0.98/0.79) and with the engine's own sparse-recovery
  measurement (75.01 cells). λ=20 is within 5% of 85.00; λ=16 is not,
  and that is a physics/documentation discrepancy, not a compiler
  divergence (GPU == CPU bitwise everywhere).

---

## 2026-07-27 — FDTD batch: upload scheduling, download flood, int ABS, linearized init

**Summary.** Four FDTD-reported issues, three of which turned out different
from their diagnoses. fdtd_slit_1d GPU: 69.5 s → **0.64 s**, 12 033 → **12**
submit+wait cycles, matching CPU to 7.9e-6 (f32 COS in the on-device init —
documented f32-transcendental deviation). fdtd_slit_db / fdtd_sw: bitwise
correct at ~64 s / ~43 s (their 2D stencils stay on CPU — full-array
ping-pong floor, not a sync bug).

- **F100 — integer ABS invalid SPIR-V** (`core/backends/spirv.py`,
  `_emit_inst` GLSL path): `ABS` on an INTEGER operand emitted
  `OpExtInst %f64 FAbs %i32` — a type mismatch spirv-as accepts but the
  driver rejects (`vkCreateComputePipelines -13`). Now emits `SAbs` with an
  i32 signature for integer operands. Also fixed the **push-constant type of
  hoisted loop-bound temps** (`N-1` etc.): the backend defaulted unknown
  temps to REAL (f64, 8 bytes) while the host typed them int (4 bytes) —
  garbage bounds, empty kernels. The bound member now uses the IR operand's
  type; `_load_bound` converts real-typed bounds to i32 as a safety net.
- **F101 — linearized init on multi-dim arrays** (`core/ir_codegen.py`
  LOAD/STORE): the loop-linearization pass rewrites `U(I,J)` to a 1-D
  `U(_K0)`, which is flat-buffer-correct on GPU but invalid C on the host's
  `double U[NY][NX]` declaration when the loop isn't extracted. New
  `_subscripts` helper decomposes a single linear index back into
  column-major C subscripts (`U[lin/NX][lin%NX]`).
- **F102 — upload scheduling across body nesting** (`core/ir_codegen.py`):
  `cpu_dirty_arrays` was a per-`_emit_body` local, so host init writes in
  an outer body never reached the upload-before-dispatch logic of kernels
  nested in inner loops (FDTD masks/ICs ran stale on device). The dirty set
  is now instance-level (`self._cpu_dirty`), visible at every nesting
  level, cleared on upload and on GPU-kernel rewrite. Related: the
  pre-frame-loop "Sync CPU state" upload now uploads **only CPU-dirty
  arrays** — the old upload-everything clobbered device data computed by
  pre-loop init kernels with stale BSS host copies (gpu_segred round-1
  sums read as zero).
- **F103 — the "unconditional download" flood is phantom CPU reads + a
  SCATTER misclassification.** Diagnosis said downloads fired with no CPU
  readers; in fact (a) the mid-body scans used kernel-agnostic
  `_collect_array_reads/writes`, so array accesses inside *extracted
  kernels* (e.g. PROF accumulate loops nested in IFs) counted as CPU reads,
  forcing a full-array download every iteration — now kernel-aware
  (`_collect_cpu_array_reads`), and (b) the line-source loops
  (`UN(IX_SRC+(J-1)*NX) := … + SV`) classified SCATTER and ran on CPU
  because `affine_mul` can't express affine×PARAMETER strides. `extract_affine`
  now substitutes PARAMETER *values* (classification-only; codegen still
  uses the push constant), so those loops extract as INJECTIVE kernels and
  the host round-trips vanish entirely. Also fixed the end-of-iteration
  refresh F99a forgot: a CPU loop inside a batched frame whose body reads
  GPU-written arrays (CPU stencil interleaved with source kernels) now
  gets a per-iteration download of exactly `kernel-written ∩ cpu-read`
  arrays, minus anything already downloaded mid-body.

---

## 2026-07-26 — Dispatch coalescing: one drain per reduction group + transfer flood fix

**Summary.** Reduction kernels in a batched frame no longer drain → sync
dispatch → download → re-open per kernel. Consecutive reduction dispatches
record into the SAME frame; the host read-back is deferred to one drain +
ONE combined partials download (new `ergo_vk_download_multi`, N buffers in
a single transfer submission) when the CPU first needs accumulator results.
The stale-read intersection check is untouched: any CPU read of a
just-dispatched array still forces an immediate drain/download.
stage4_batch (N=8): **7.05 s → 0.27 s (~26×)**, rows 21/21 bitwise vs the
stage-2 oracle.

- **Files:** `core/ir_codegen.py` (`_pending_reductions` queue;
  `_emit_gpu_dispatch` defers batched reduction read-backs;
  `_emit_reduction_readback` + `_flush_pending_reductions` — flush before
  the first non-dispatch item and at end of body),
  `core/runtime/vk_host.c` (`ergo_vk_download_multi`; ERGO_PROFILE-gated
  launch/submit+wait/drain counters), `core/runtime/ergo_vk.h`.
- **Bigger find — the transfer flood.** Profiling the coalesced build
  showed the per-batch cost was never the reduction syncs but ~20 MB of
  full-array transfers per batch iteration, from two tracking bugs:
  - **F99a — nested dispatch loops drained per iteration.** The
    end-of-body "download for subsequent CPU code" fired at the end of
    EVERY CPU loop body wrapping GPU dispatches (the ping-pong matvec
    loop: 8 frame drains + 16 full-array downloads per batch). Inside a
    batched frame, end-of-body downloads are now skipped; transfers
    happen only at drain points driven by actual CPU reads (the mid-body
    intersection check).
  - **F99b — kernel writes misattributed as CPU writes.** A CPU loop
    wrapping GPU dispatches (and any IF wrapping loops) marked the
    kernels' output arrays CPU-dirty, forcing re-uploads of stale host
    data. New `_collect_cpu_array_writes` skips extracted sub-loops.
    Once downloads stopped refreshing host copies (F99a), this became a
    correctness bug too: the stale seed-time host copy of V was uploaded
    over the GPU-converged V before `GS := V`, silently breaking the
    deflated phase. Additionally, GPU kernel writes inside a CPU loop now
    CLEAR stale CPU-dirty flags for the arrays they rewrote (unless the
    CPU also wrote them in that loop).
- **Measured:** launches 2069 → 2069 (unchanged — coalescing is about
  syncs, not launch count); queue submit+wait cycles ≈2 500–3 000 (est.,
  counter didn't exist in the before build) → **285**; frame drains
  ≈1 100–1 300 (est.) → **218**; per-batch full-array transfers
  ~20 MB → ~0.
- **Semantics:** frame-batch model unchanged — record into one command
  buffer, drain only when the host needs data. The reduction read-back
  timing moves from "immediately after each reduction kernel" to "before
  the first subsequent non-dispatch item"; accumulator contents are
  identical (same ordered host combine).

---

## 2026-07-26 — Segmented reduction (one kernel, many block sums) + runtime capacity

**Summary.** REDUCTION loops whose accumulator is a REAL *array* indexed by a
table lookup (`ACC(BLKOF(I)) := ACC(BLKOF(I)) + expr`) now extract to the GPU
as segmented reductions: one kernel computes all segment sums at once. The
mechanism reuses the staged scalar reduce unchanged — each workgroup lies
entirely within one segment (segments must be equal-length and padded to a
multiple of 256, checked at extraction), tree-combines in shared memory, and
writes its partial to `OUT[wgid]`; group `g` belongs to segment `g / Gseg`.
The host downloads the partials and combines per segment in group order,
adding onto the pre-existing accumulator values. No atomics; deterministic
for a fixed dispatch shape. Chosen over per-lane segment tagging because it
reuses the proven scalar path verbatim and keeps the determinism
constitution.

- **Files:** `core/ir_gpu.py` (`KernelPlan.reduction_array`,
  `_validate_seg_reduction` — validates the single-table-RMW pattern and the
  padding geometry, else silent CPU fallback; `_check_loop` now returns an
  11-tuple), `core/backends/spirv.py` (`_is_reduction()`; LOAD of the
  accumulator array emits identity 0, STORE is suppressed and captured as
  the per-thread value), `core/ir_codegen.py` (segmented read-back in
  `_emit_gpu_dispatch`), `tests/gpu_segred.ergo` (2 rounds, nonzero ACC).
- **F98 — segmented accumulator clobbered by device sync.** When the
  accumulator array was ALSO written by another kernel (e.g. an extracted
  zeroing loop), it became GPU-resident: the host combine added partials
  onto a stale host copy and a later download of the zeroed device buffer
  clobbered the sums (stage4: S2=0 → NRT=inf → NaN everywhere). Fix in
  `_emit_gpu_dispatch`: if the accumulator is GPU-resident, download it
  before combining and upload the combined values after.
- **MIN_KERNEL_ITERS now resolves PARAMETER bounds** (`extract_kernels`
  and `_try_split`): a 21-iteration per-block zeroing loop previously
  launched a kernel because the check only fired for literal bounds. Small
  loops like that now stay on CPU as intended.
- **Runtime:** `ERGO_VK_MAX_PIPELINES` 16 → 64 (segmented stage4 needs 17+);
  env-gated total-launch counter printed by `ergo_vk_profile_report`.
- **stage4_batch.ergo regenerated** (gen_ergo_stage4.py): blocks padded
  DIM=6561 → DIMP=6656, sums rewritten as segmented loops. GPU vs CPU:
  21/21 rows bitwise identical (matches the stage-2 oracle). Wall time
  7.7 s → 7.1 s; launches 1730 → 2069 (reductions are kernels now — the
  per-block-kernel variant the 75%-of-launches figure referred to would
  have been ~7 700).

---

## 2026-07-22 — Atomic fetch-add fusion (spawn slot allocator) + galaxy_structured source fix

**Summary.** galaxy_structured's spawn system was broken in two layers:
the source had lost `NPART := SPAWN_COUNTER(1)` (removed in the user's own
commit `6f89b3d`, Apr 2026 — population pinned at 12 forever), and the
slot allocator's load-then-atomicAdd pattern raced on GPU (parallel
spawns claimed the same slot; skipped slots stayed zero and rendered at
the origin). Fixed the source line and taught the compiler the
fetch-add fusion the source comment always intended.

### F97 — Atomic fetch-add fusion in the SPIRV backend

- **Files:** `core/backends/spirv.py` (new `_analyze_fetch_adds`,
  `_iter_blocks`, LOAD fusion site, STORE skip site)
- **Pattern:** `SLOT := counter + 1; counter := counter + 1` (and any
  same-shape claim: a LOAD feeding an ADD with a constant-int delta,
  with a later RMW store to the same array/index/delta). Before: plain
  load + separate `OpAtomicIAdd` — every thread read the same counter
  value → slot collisions, skipped (zero) slots, NPART overcounting
  initialized children.
- **Fix:** the claim LOAD emits ONE `OpAtomicIAdd` that returns the old
  value (unique slot per thread, increments once); the partner STORE is
  skipped. Gated to non-partial kernels with `gpu_fast_math` and the
  array in `atomic_arrays` — sequential/CPU paths untouched.
- **Subtleties handled:** statements are one-per-IRBlock (load and add
  live in different blocks); index temps with distinct names but equal
  constant values (`_idx_N = 1-1`) are folded to match; the store's own
  internal load is excluded from claims (no double increment).
- **Verification:** `work/gpu_audit/probe_spawn_fused.ergo` — before
  fusion: NPART=36 with only ~2 slots written; after: **NPART=48 with
  `VAL(13..16) = 10.5/20.5/30.5/40.5`** (every spawn unique slot,
  correct child values). Determinism harness green; colony 0 validation
  errors; galaxy builds/runs.

### galaxy_structured.ergo (source, not compiler)

- **`NPART := SPAWN_COUNTER(1)` restored** at line 1387 (was removed in
  user commit `6f89b3d`; the comment at line 567 kept promising the
  behavior). Verified live: NPART grows 12 → 24 → 37 → 51 → 66 → 83 →
  102 under forced rate. Note: the spawn hash is deterministic per
  (particle, GEN window) and GEN changes every ~128 frames, so growth
  at `SPAWN_RATE=0.01` is bursty (each favorable window spawns ~128 per
  particle), not the "smooth growth" the comment claims.

---

---

## 2026-07-22 — Render bring-up: RING/dead-code, NET/upload guards, oracle lifecycle

**Summary.** Getting `galaxy_full.ergo --render` running exposed a chain of
issues from the GPU-cleanup changes: dead inlined subroutines with GPU-only
ops broke CPU emission, render/NET paths referenced nonexistent device
buffers, kernel-read uploads were starved by the oracle gate (stale-grid
physics), and the verify drain unbalanced the frame lifecycle (intermittent
freeze after frame 1). Also added a runtime oracle kill switch.

### F89 — Dead function definitions emitted after inlining

- **Symptom:** `galaxy_structured.ergo` failed with "RING/WARP subgroup
  intrinsics are only available in GPU kernels" — the CPU codegen emitted
  the fully-inlined `SIM_PHYSICS_STEP` definition (dead code) containing
  GPU-only RING ops.
- **Fix:** `ir_codegen._collect_referenced_funcs` — skip function
  definitions with no remaining CALL/CALL_VOID sites (main + all bodies).
  The VERIFY oracle's hardcoded `SIM_PHYSICS_STEP` call counts as a
  reference (the oracle needs it).
- **Fallout caught the same day:** the oracle's direct `SIM_PHYSICS_STEP(...)`
  emission was invisible to the first version of the collector → link
  error. Fixed by treating `Op.VERIFY` as a reference to it.
- **Note:** galaxy_structured still can't build — its oracle calls a
  RING-containing subroutine on CPU (real semantics gap, needs a spec
  decision on CPU warp-ring emulation vs `--no-verify`).

### F90 — NET field upload referenced a non-device array

- **Symptom:** `d_GRID_DENSITY_GLOBAL undeclared` — the consensus field
  upload emitted `ergo_vk_upload(d_GRID_DENSITY_GLOBAL, …)` even when the
  stencil (and thus the array) was CPU-resident (no device buffer exists).
- **Fix:** upload only when `GRID_DENSITY_GLOBAL` is actually in the GPU
  array set.

### F91 — ERGO_COLOR candidates referenced non-device arrays

- **Symptom:** `d_PUMP_RESID/d_PUMP_HIST undeclared` — the runtime color
  channel selector emitted `d_{arr}` for every REAL array shaped like
  POS_X, including CPU-only ones.
- **Fix:** candidates filtered to GPU-resident arrays.

### F92 — Kernel-read uploads starved by the oracle gate (stale-grid physics)

- **Symptom:** rendered physics was wonky — corner clustering, cardinal
  jets. The density deposit ran on CPU every frame (Stage 2 atomics
  gate), but uploads of CPU-modified arrays were gated to oracle frames
  (`every 100`): GPU kernels read 99-frame-stale grids.
- **Fix:** kernel-read arrays upload **every frame**; only oracle-only
  arrays keep the gated schedule (`ir_codegen` upload-set split).

### F93 — Verify drain unbalanced the frame lifecycle (intermittent freeze)

- **Symptom:** render froze after ~frame 1 — main thread blocked in
  `vkWaitForFences` inside `ergo_vk_frame_begin` on an unsubmitted fence.
- **Root cause:** `_emit_verify`'s end+wait sits inside the
  `every`-gated C block but set `_frame_ended_early` unconditionally at
  codegen, so the finalizer skipped the close on the 99% of frames where
  the gate is closed; the re-begun frame's fence was never submitted.
- **Fix:** verify drain now re-begins the frame immediately after its
  wait (same D21 pattern as the other drains). Headless runs never froze
  (compute lifecycle sound); the intermittent render freeze under window
  pressure is still being tracked separately.

### F94 — Sort temp buffers sized by shape, not MAXPART

- Duplicate of F76 note (same fix, logged here for the GPU batch series):
  `d_sort_{arr}` creation no longer hardcodes `MAXPART`.

### F95 — Runtime oracle kill switch: ERGO_NO_VERIFY

- `if (!getenv("ERGO_NO_VERIFY")) { ... }` wraps the entire oracle block
  (init, downloads, shadow evolution, uploads). No recompile needed; also
  removes the periodic full-array download bandwidth.

### F96 — `--no-verify` compile flag (unblocks RING sources incl. galaxy_structured)

- **Files:** `core/__main__.py`, `core/driver.py`, `core/ir_codegen.py`
- **Symptom:** `galaxy_structured.ergo` could not compile at all — its
  VERIFY oracle calls `SIM_PHYSICS_STEP` on the CPU, but that subroutine
  contains GPU-only RING_* intrinsics (F39 made RING-on-CPU a hard error;
  in May it was silently garbage).
- **Fix:** `--no-verify` omits the oracle block at compile time
  (`IRCodeGen(no_verify=True)` → `_emit_verify` returns early). With no
  oracle call, the RING-containing subroutine has no remaining call sites
  and is dropped as dead code (F89) — no CPU copy, no error. The
  `_collect_referenced_funcs` VERIFY-reference is suppressed under the
  flag. `--gpu-fast-math` remains required for its SCATTER loops (the
  crystal-lane RING loops must stay on device).
- **Verified:** `galaxy_structured.ergo --target spirv --render
  --gpu-fast-math --no-verify` builds and runs.

**Verification:** galaxy_full render builds and runs past frame 1200+
(repeated runs, no freeze); `ERGO_NO_VERIFY=1` produces zero oracle
output; headless galaxy_full runs clean; colony/galaxy determinism
hashes unchanged; galaxy_structured builds + runs.

---

---

## 2026-07-21 — GPU batch 5 (Stage 4): precision policy, NVVM shelve, spec lock

**Summary.** SPIRV `SQRT`/`POW` are now true f64 (GLSL.std.450 defines
them for f64) — the Stage-0 oracle deviation of ~1e-6 absolute drops to
bit-identical for the Sqrt part; remaining transcendentals stay f32 with
one loud warning per kernel. NVVM is shelved as experimental with a loud
error. The spec now records the resolved atomics gate (9.9) and the
precision policy (9.10).

### F86 — SPIRV f64 Sqrt + transcendental warnings (B10)

- **Files:** `core/backends/spirv.py`, `core/backends/__init__.py`
- `GLSL_F32_ONLY` no longer contains SQRT — it now emits native f64
  (`OpExtInst … Sqrt` on `OpTypeFloat 64`). POW was *also* tried
  f64-native and reverted: `spirv-val` rejects f64 Pow (GLSL.std.450
  Pow is 16/32-bit only — verified empirically, not from docs).
- The remaining f32-only transcendentals (SIN/COS/TAN/ASIN/ACOS/ATAN/
  SINH/COSH/TANH/EXP/LOG/POW) keep the f64→f32→f64 path but now emit
  **exactly one warning per kernel** naming the ops and the expected
  deviation (deduped per backend instance — the driver calls
  `generate()` twice).
- Oracle evidence (`work/gpu_audit/probe_oracle.ergo`, SIN+SQRT):
  before — 3/3 points deviated ~1e-6; after — Sqrt-carrying points are
  **bit-identical** to CPU; only the SIN-carrying point deviates (f32,
  warned).

### F87 — NVVM backend shelved as experimental

- **File:** `core/backends/nvvm.py`
- The audit catalog stands unfixed by decision (SPIRV/Vulkan is the
  shipping path): unconditional `.approx` TAN/SINH/COSH/TANH; fast-math
  EXP/LOG→ex2/lg2 **without the required scale correction** (EXP returns
  2^x); no SCATTER atomics (data race); invalid LLVM IR for integer
  arrays, mixed int/real arithmetic, POW/MAX/MIN declarations, CYCLE/IF.
- Constructor now raises `MCLError("--target nvvm is experimental and
  currently broken …; use --target spirv")`; docstring carries the full
  catalog. Code kept for reference until the CUDA path is revived.

### F88 — Spec: atomics gate resolved + precision policy locked

- `Spec/Ergo_Spec.md` Part 9.9: the open "Implementation status"
  paragraph is replaced with the resolved behavior (gate wired at
  extraction + backend guard; sort deterministic by default).
- New Part 9.10 "GPU Numeric Precision Policy": Sqrt/Pow native f64,
  transcendentals f32 with one warning per kernel, CPU always exact.

**Stage 4 verification:** oracle above; `--target nvvm` fails loudly;
determinism harness green; colony + galaxy run clean; CPU corpus
178/184 unchanged.

---



---

## 2026-07-21 — GPU batch 4 (Stage 3): promote_locals correctness

**Summary.** The flag-gated `--promote-locals` pass no longer produces
silently wrong code. Rule applied throughout: promote only what is
provably safe; everything else is a loud rejection with a diagnostic.
Also closed the split prefix-reads/suffix-writes reordering hazard and a
same-line kernel collision that could dispatch the wrong kernel.

**Files changed:** `core/ir_gpu.py` only.

**Verification:** probes `work/gpu_audit/probes_stage3/`; buc with
`--promote-locals` shows safe promotions (`_promo_DIST_BUF_1`,
`_promo_MRMOD_BUF_2`) AND correct rejections; 0 validation errors;
determinism hashes unchanged (flag-gated, no default-path change);
CPU corpus 178/184.

### F79 — Buffer store index off-by-N

- The buffer STORE reused the first `_idx*` SUB temp assuming it was
  `loop_var − 1`; in stencils it's `I+1−1` or `I−2` — stores landed in
  the wrong cells while suffix loads used fresh `loop_var − 1` temps.
  Now always a fresh `loop_var − 1` temp. GPU output byte-identical to
  the CPU run on the probe.

### F80 — `{name}_BUF` collisions with user arrays

- If the user declared `X_BUF`, promotion kept the mapping but skipped
  the decl — silently storing into the user's array; two promotions of
  one name shared one buffer sized for the first loop. Now counter-based
  `_promo_{name}_BUF_{n}` names, bumped until free of every declared
  name.

### F81 — Suffix writes to promoted scalars

- `_rewrite_suffix` rewrote only reads; `X := X + 1` in the suffix kept
  writing the CPU scalar while reads came from the buffer — carry
  silently broken. Now rejected loudly: `PROMOTE rejected: suffix
  writes leaked local(s) [...] — buffer promotion cannot carry
  read-modify-write scalars`. The dead accumulator guard is subsumed.

### F82 — Suffix IF conditions / loop bounds / SELECT expressions

- These read the stale CPU scalar ("skip for now"). Now rejected loudly
  when a leaked local is read in any of them.

### F83 — Missing start/step validation

- Buffers were sized `loop.end` and indexed `var − 1` regardless:
  `DO I = 0, N-1` stored at index −1; step ≠ 1 miscounted. Now rejected
  unless start and step both resolve to 1 (literal or PARAMETER).

### F84 — Split prefix-reads/suffix-writes reordering hazard

- `_try_split` (and `_do_promote`) never checked whether the GPU prefix
  reads arrays the CPU suffix writes — the prefix would run before the
  suffix computes them. Now rejected loudly on both paths. Probe: split
  that printed 0.0 now runs sequentially and prints the correct value.

### F85 — Same-line kernel collision dispatched the wrong kernel

- Promoted flow/suffix loops shared `line`, so `ir_codegen`'s
  `_kernel_by_line` map identified the CPU suffix loop as the GPU kernel
  — one kernel dispatched twice, the other never (probe's GPU run
  printed nothing). The suffix loop now gets the first suffix item's
  line. (`_kernel_by_line` remains line-keyed — any future pass
  creating two same-line loops trips it; noted for the codegen owner.)

---



---

## 2026-07-21 — GPU batch 3 (Stage 2): execution semantics

**Summary.** The spec's SCATTER policy is now real: scatter loops fall
back to CPU by default and only dispatch with atomics under
`--gpu-fast-math` (spec 8.2/9.9). Fusion enforces all five legality
conditions instead of fusing stencil chains into wrong answers. The
linearizer can no longer flatten temporal×spatial nests into racy
kernels. Split kernels can't leak prefix locals into CPU suffixes (was a
live segfault in galaxy). Sort-by-GEN is deterministic. And RING no
longer assumes a 32-lane warp.

**Files changed:** `core/ir_gpu.py` (F66–F69, F72),
`core/backends/spirv.py` (F70–F71), `core/ir_codegen.py` (F73–F77),
`core/driver.py`, `core/__main__.py` (F66 plumbing).

**Verification:** probes `work/gpu_audit/probes_stage2/` (13+4);
scatter probe both modes (CPU default, GPU atomics with
`--gpu-fast-math`); sort probe ordered+stable+reproducible on CPU,
default-GPU, and fast-math-GPU paths; colony AND galaxy 0 Vulkan
validation errors on full runs; `gpu_determinism.sh` green; CPU corpus
178/184 unchanged.

### F66 — SCATTER gate at extraction (spec 8.2/9.9 wired)

- `extract_kernels(module, allow_split, gpu_fast_math=False)`: SCATTER
  full-loops and SCATTER split-prefixes are rejected to CPU by default
  ("serialized on CPU by default (use --gpu-fast-math for GPU atomics)");
  with the flag they extract with `atomic_arrays` populated. Plumb:
  `driver.py` + `--kernel-report`. Verified: scatter probe computes
  `1.0` on both modes.

### F67 — Fusion legality (spec 8.3, all five conditions)

- `_can_fuse` now enforces: matching bounds AND step; anti-dependence
  (k1 reads ∩ k2 writes); scalar producer-consumer
  (k1.scalars_local ∩ k2.scalars_read); condition 4 (k2 reads k1's
  arrays only at the SAME affine index); adjacency by parent-body
  identity (no cross-nest fusion). `_do_fuse` removes k2's loop from
  `module.main_body` — the CPU no longer re-executes the fused loop
  with stale state and uploads over the GPU's fused results.

### F68 — Linearize soundness

- `linearize_nested_loops` can no longer: flatten nests with any array
  read AND written in the body (was: temporal `DO F` × spatial `DO I`
  RMW recurrences became racy flat kernels — demonstrated live);
  silently delete blocks after the inner loop; ignore non-unit steps;
  collapse non-exact index patterns (`A(I,5)`, `A(J,I)`, `A(I±1,J)`
  rejected loudly). Collapsed loops are now 1-based `_K=1..total` (was
  0..total-1 — an off-by-one that made every flat kernel wrong).
  Probes: RMW nest → not linearized (per-frame inner kernel instead);
  pure-write 2-D init → still collapses, correct bound.

### F69 — SHIFT outranks FLOW (spec 9.5 "most restrictive applies")

- Shift detection now runs for INJECTIVE **and** FLOW worst-store
  classes; a FLOW loop with an affine shift pair on another array is
  SHIFT (serialized), not extracted FLOW.

### F70 — SPIRV atomics emission guard

- `_require_atomic_gate()` raises `MCLError` if a kernel with
  `atomic_arrays` reaches the backend without `--gpu-fast-math`
  (defense-in-depth behind the F66 extraction gate). Sort-kernel
  atomics exempt (compiler-generated).

### F71 — RING_* real subgroup size

- The `& 31` hardcode is gone: RING_PREV/NEXT/SHIFT load
  `gl_SubgroupSize` (GL_KHR_shader_subgroup) and mask with size−1 at
  each use site. Output on the RTX 2060 (subgroup 32) byte-identical to
  the pre-change binary; now correct on wave64/16-lane hardware.

### F72 — Split kernels leaked prefix locals into CPU suffixes (segfault)

- Galaxy crashed after F66–F68: the line-293 loop split into a GPU
  prefix (computing `_SCATTER_GRID_CI/CJ/CK/GEN`) and a CPU suffix
  consuming them as STORE index args — never assigned on CPU → index
  ~2.67e9 into a 32³ static → SIGSEGV. `_try_split`'s leak detection
  dropped `_`-prefixed names from both sides and missed STORE index
  args, IF/SELECT conditions, and loop bounds. Now: complete read set
  (all operand refs), complete prefix-def set, and any prefix→suffix
  local intersection rejects the split loudly (galaxy's 293 loop runs
  sequentially on CPU; galaxy runs crash-free again).

### F73 — Sort-by-GEN deterministic CPU counting sort

- The GPU scatter assigned slots in atomic-arrival order
  (irreproducible). Default path is now: drain frame, download
  GPU-resident arrays, stable counting sort by
  `(FLAGS[i] >> GEN_SHIFT) & GEN_MASK` on CPU, copy back, re-upload —
  bitwise reproducible. `--gpu-fast-math` keeps the GPU
  histogram/scan/scatter path (documented nondeterminism). Probe:
  ordered + stable + identical across runs; also fixes the
  GPU-plan-less case (pure CPU sort, no dangling `d_` handles).

### F74 — GPU→CPU sync for non-inlined subroutine calls (D18)

- `need_sync` for CALL_VOID was gated on `_in_frame_loop`; a
  non-inlined sub outside the frame loop read stale CPU copies. Now
  syncs anywhere, with downloads filtered to actually-GPU-resident
  arrays (init-region calls aren't clobbered with GPU garbage), and
  uploads mark arrays GPU-current.

### F75 — Barrier before frame_fill on dispatch-written buffers (D19)

- `ZERO`→`ergo_vk_frame_fill` recorded a TRANSFER-stage fill after
  COMPUTE writes with no ordering (WAW hazard). Per-frame dirty
  tracking (`_frame_gpu_dirty`) now drains and re-opens the frame
  before filling a buffer a dispatch wrote earlier in the same frame.

### F76 — Sort temp buffers sized by shape, not MAXPART

- `d_sort_{arr}` buffers were created with `MAXPART * sizeof` —
  programs without MAXPART (i.e., anything not galaxy) failed C
  compilation. Now sized from the array's real shape (with the same
  MAXPART→CAPACITY substitution as the regular buffers they swap with).

### F77 — Push-constant member lists unified (D20)

- All three host/backend sites now derive the push-constant scalar list
  from one helper (`_kernel_pc_scalars`), so the size arithmetic and
  the C struct can't drift apart.

### F78 — Host descriptor sets updated while pending (D23)

- **File:** `core/runtime/vk_host.c`
- **Symptom:** `VUID-vkUpdateDescriptorSets-None-03047` — host-side
  `ergo_vk_bind_buffer` rewrote a pipeline's single descriptor set while
  a previous frame's still-pending command buffer referenced it (WAR
  hazard; benign on NVIDIA, a real hazard elsewhere).
- **Fix:** per-frame-slot descriptor sets (`PipeSlot.ds[2]`, matching
  the two cmd_buf/fence slots); `bind_buffer` writes only the current
  slot's set; one-time binds write both slots at init.
- **Verification:** direct repro (frame loop wrapping two INJECTIVE
  kernels) went 20 → 0 validation errors; galaxy/buc colony runs clean;
  `ERGO_FINAL_HASH` identical across before-fix, after-fix, and the
  pre-change reference binary (three-way match, physics untouched).

## Known issues deliberately NOT fixed in this batch

- **Host runtime shutdown leaks:** buffers/fence/query pool not
  destroyed at `ergo_vk_shutdown` (cosmetic — 8 warnings at exit).
- **Split prefix→suffix array hazard:** `_try_split` does not check
  whether a flow prefix READS arrays the suffix WRITES (GPU-before-CPU
  reordering). Flagged by the Stage-2 worker for the next audit.
- **promote_locals cluster** (Stage 3), **SPIRV f64 transcendentals +
  NVVM shelve** (Stage 4).
- Spec text: Part 9.9 "Implementation status" still describes the gate
  as unwired — spec-owner update queued with the Stage 4 docs.

---



---

## 2026-07-21 — GPU batch 2 (Stage 1): classification correctness

**Summary.** The kernel classifier (`ir_gpu.py`) now sees what it
classifies: stores inside IFs count, all stores per array count, STATIC
scalars are not constants, multi-dim subscripts classify by their combined
linear index, and split kernels carry the real dependence class instead of
a default-INJECTIVE lie. On the backend side, three silent fallbacks are
now loud errors, and a runtime-valued loop bound can no longer become a
silent empty kernel.

**Files changed:** `core/ir_gpu.py` (F59–F64), `core/backends/spirv.py`
(F65), `core/ir_codegen.py` (F65).

**Verification:** probe suite `work/gpu_audit/probes_stage1/` (11
classification probes with before/after); extraction reports on all three
GPU sources unchanged (fixes are neutral where code was already correct);
colony 0 validation errors; `gpu_determinism.sh` green; CPU corpus
178/184 unchanged.

### F59 — IF-body stores invisible to the classifier (A2)

- `_check_loop`'s STORE/LOAD collection skipped non-IRBlock items
  (`ir_gpu.py` ~1781): physics inside an IF was classified INJECTIVE
  regardless of SHIFT/SCATTER content. New `_iter_blocks` helper descends
  into `IRIf.then_body/else_body` and `IRSelect` case bodies (not nested
  IRLoops). Probe: `IF cond THEN A(I) := A(I-1)+1.0` now rejects as
  SHIFT(k=1) instead of dispatching racy-parallel.

### F60 — Per-array classification was last-store-wins (A3)

- `store_deps[arr] = dep` / `store_exprs[arr] = expr` overwrote per
  array; a FLOW store followed by an INJECTIVE store to one array
  suppressed the SCATTER upgrade, and shift detection saw only the last
  store. All stores now accumulate: worst rank wins, the
  FLOW+loaded→SCATTER upgrade checks every store, shift detection checks
  every (store × load) pair. Shared helper `_classify_body_dependence`.

### F61 — STATIC scalars treated as loop invariants (A4)

- `_compute_module_invariants` added every shape-less STATIC global.
  STATIC is mutable file-scope state — `A(S+I)` with S updated per
  iteration classified INJECTIVE → parallel write collisions. Invariants
  are now PARAMETERs only.

### F62 — `_index_has_load` only followed `_`-prefixed refs (A8)

- Index expressions flowing through user-named variables weren't traced,
  so `J := IDX(I)` + `A(J) := B(I)` classified SCATTER instead of FLOW.
  The trace now follows all refs. (Also: defs accumulate across blocks in
  body order, so cross-block index chains resolve.)

### F63 — Multi-dim subscripts classified by construction as SCATTER

- `_classify_store_index`/`_extract_load_index` required exactly one
  index arg — every multi-dim store (`A(I, 2)`, `GRID(I, J, K)`) was
  SCATTER by construction. New `_combine_affine_indices` folds the
  per-dimension affine exprs into one combined expr with the column-major
  linearization `i0 + d0*(i1 + d1*(i2))`, dims from `array_shapes`
  (PARAMETER dims resolved); classify the combined expr as usual.
  `A(I, 2)` now INJECTIVE (was SCATTER); unresolvable dims stay
  conservative (SCATTER/FLOW).

### F64 — Split kernels defaulted to INJECTIVE (A1)

- `_try_split`'s `KernelPlan` never passed `dependence=` — a split prefix
  containing SHIFT/SCATTER patterns dispatched parallel, no atomics, no
  CPU suffix. The prefix now goes through `_classify_body_dependence`;
  SHIFT rejects the split with a reason; `dependence=`/`shift_k=`/
  `atomic_arrays=` populated on the plan.

### F65 — SPIRV silent fallbacks → loud errors; loop bounds in push constants

- Unhandled IR op (e.g. IEOR) emitted a comment and computed with `0.0`;
  unresolvable loop bound became constant 0 (every thread disabled —
  silently empty kernel); missing array shape in multi-dim linearization
  invented a magic dim 32. All three now raise `MCLError`.
- The B13 raise exposed a live bug in galaxy: `_SIM_SEED_SHELL_N_SHELL`
  (runtime-valued loop bound) was a silently-empty kernel because
  extraction never put bounds in `scalars_read`. Loop-bound refs are now
  unioned into the push-constant scalar list on both sides
  (`ir_codegen._kernel_pc_scalars`, spirv `_declare_push_constants`) —
  the kernel actually runs now.

**Follow-up noted for Stage 2:** shift detection still only runs when
the loop's worst store class is INJECTIVE — a loop made FLOW by one
array won't shift-check another array's affine pair (spec 9.5's
"most restrictive applies" would rank SHIFT above FLOW).

---



---

## 2026-07-21 — GPU batch 1: frame lifecycle, driver fallback, array-layout unification

**Summary.** First stage of the GPU cleanup (plan in
`work/gpu_audit/`): GPU binaries segfaulted on first dispatch; `--target`
with no extractable kernels printed "Compiled successfully" but produced
no binary; and the multi-dim array layout story was settled by measurement
and unified to **column-major on both sides** — which also fixed silent
misalignment of every multi-dim DATA table in the galaxy family.

**Verification:** `work/gpu_audit/gpu_determinism.sh` (byte-identical
emissions across PYTHONHASHSEED 0/42); colony program 0 Vulkan validation
errors (was: segfault); layout probe CPU==GPU on `A(I,J)` reads;
`work/gpu_audit/coalesce_bench` (nvcc, results.txt); sq2core stdout
byte-identical to reference; CPU corpus 178/184 unchanged.

### F55 — GPU frame lifecycle: dispatches recorded into dead command buffers

- **Files:** `core/ir_codegen.py` (download sites, nested-loop path)
- **Symptom:** freshly compiled GPU binaries segfaulted in the NVIDIA
  driver at the first `ergo_vk_frame_dispatch`; Vulkan validation showed
  every command recorded into a command buffer that was not recording.
- **Root cause (two halves):** (a) mid-frame `frame_end/wait` drains
  (emitted before host↔device downloads) never re-opened the frame, so
  the next dispatch in the same iteration recorded into an ended buffer;
  (b) the nested-loop `frame_end`/flush sites closed the *outer* frame
  from *inside* a nested loop's braces — once per inner iteration.
- **Fix:** re-`ergo_vk_frame_begin()` after every early drain (the runtime
  is designed for it — `vk_host.c:1354`); deleted the nested-loop close
  sites (the outer frame loop owns the lifecycle). Verified with gdb
  event traces and two minimal probes; colony now runs with **zero**
  validation-layer errors.

### F56 — `--target` with no extractable kernels produced no binary

- **File/function:** `core/driver.py` → `_compile_target`
- **Symptom:** "No extractable kernels found. Falling back to CPU path."
  + "Compiled successfully: ./x" — but no `./x` existed (the C was
  returned, never passed to gcc).
- **Fix:** the fallback returns `None` and `compile_source` continues
  down the normal CPU path (codegen + gcc).

### F57 — Multi-dim arrays: layout divergence + silent DATA corruption

- **Files:** `core/ir_codegen.py`, `core/codegen.py` (C array dims and
  subscripts now reversed), `core/backends/spirv.py` (column-major
  retained), `core/jit.py` (`array_np` → `order='F'`), `Spec/Ergo_Spec.md`
  (layout locked, Part 2).
- **History:** the SPIRV backend linearized column-major (documented
  intent, `galaxy/DRAFT_index_analysis.md:91`) while the C backend
  emitted row-major — a program writing `A(I,J)` on GPU read back
  transposed values on CPU (probe: `A(2,1)` printed 81 vs 21,
  **reproduced on the May-14 reference compiler**).
- **Measurement:** a 2×2 (storage × walk) stencil benchmark on the RTX
  2060 (`work/gpu_audit/coalesce_bench/results.txt`): matched pairs
  ~520–549 GB/s (CM×I-fast ≈ RM×K-fast), mismatched pairs ~27 GB/s
  (~20× penalty). The convention is free; walk-matches-storage is
  everything. Ergo sources write first-index-innermost loops and the
  compiler cannot reorder them — so column-major both sides.
- **Implementation:** Ergo `A(d0,d1,d2)` → C `A[d2][d1][d0]`;
  `A(i,j,k)` → `A[k-1][j-1][i-1]`; DATA fills first-index-fastest
  (Fortran order). 1-D arrays unaffected.
- **Silent corruption found along the way:** the galaxy family's
  geometry tables (`TANGENT(3,32)`, `CUBOCT(3,12)`, `CURVE_PT(3,32)` —
  27 DATA users) are authored as (x,y,z) triples and read as
  `TANGENT(1..3, GEN)`. Under row-major fill, `TANGENT(c,GEN)` for
  c>1 or GEN>1 read the wrong flat slots (verified: May build prints
  0.0/garbage where the fixed build prints the authored values).
  Column-major fill matches the authoring — a long-standing data bug
  fixed as a side effect of the unification.
- **Verification:** layout probe CPU==GPU; sq2core (3-D arrays + inline
  hash) stdout byte-identical to its reference binary; corpus unchanged.

### F58 — JIT `array_np` uses Fortran order

- **File:** `core/jit.py` — numpy views of STATIC arrays now reshape
  with `order='F'` and document the column-major flat layout; JIT array
  test suite updated and green (36 checks).

## Known issues deliberately NOT fixed in this batch (GPU Stages 1–4)

- **Classification correctness** (ir_gpu): IF-body stores invisible to the
  classifier, last-store-wins per-array classification, STATIC scalars as
  invariants, split-path re-extraction as default-INJECTIVE, SPIRV
  silent-0.0 fallbacks (IEOR et al.), empty-kernel on unresolved bounds.
- **Execution semantics:** unconditional SPIRV atomics (spec 9.9 — gate
  exists, unwired), sort-by-GEN atomic-arrival-order scatter, fusion
  conditions 3/4 unenforced + stale-CPU re-execution, linearize_nested
  unsoundness (demonstrated: flattens temporal×spatial nests into racy
  kernels; bound off-by-one), promote_locals cluster, RING 32-lane
  assumption, push-constant size computed twice.
- **Host runtime:** descriptor set updated while referenced by a pending
  command buffer (galaxy; benign on NVIDIA, hazard elsewhere); shutdown
  resource leaks (buffers/fence/query pool not destroyed — cosmetic);
  SPIRV f64 math at f32 for transcendentals (Sqrt/Pow fix pending);
  NVVM backend catalog (will be shelved as experimental).

---



---

## 2026-07-21 — Bugfix batch 2 (determinism audit: checker, frontend, IR path, driver)

**Summary.** Forty fixes driven by a full determinism audit (ranked findings
in `work/determinism_audit/`). Headline items: the F7/F8 IR-path analogs are
now fixed (negative-step loops, missing RETURN — the two open items from
batch 1), `CALL ZERO` on ALLOCATABLE zeroed only the pointer, `STOP` inside a
function silently returned 0 to the caller, `!=` was eaten as a comment, and
every `--target` compile crashed on a stale `import mcl.*`. Also added the
spec'd-but-missing `EXIT` statement and `SIGN` intrinsic, made the checker
enforce a dozen spec-mandated rejections, and made `--precision f32` emit
real f32 arithmetic on the CPU path.

**Files changed:**

| File | Fixes |
|---|---|
| `checker.py` | F9–F25 |
| `symbols.py` | F17 |
| `lexer.py` | F26 |
| `parser.py` | F27, F45 |
| `ir_builder.py` | F28–F33, F45 |
| `ir_codegen.py` | F33–F45 |
| `driver.py` | F46, F47 |
| `ir_gpu.py` | F48 |
| `ir.py`, `tokens.py`, `ast_nodes.py` | F33, F45 (plumbing) |

**Verification:** ~60 probes under `work/determinism_audit/probes_*/`
(broken behavior captured before each fix, verified after; every semantic
fix compiled with gcc *and run*). Corpus: `work/determinism_audit/corpus_run.sh`
over all 184 `tests/*.ergo` — baseline 179 PASS / 5 FAIL; final 178 PASS /
6 FAIL. The 5 `waveform_molecule_*` FAILs are pre-existing (they rely on
`&`-inside-string continuation, deliberately LexError since F3). The one new
FAIL, `tests/gpu_ring_shuffle.ergo`, is *correct* behavior: it uses
`RING_*` intrinsics and the corpus compiles without `--target`, so F39's
mandated error fires; it compiles fine with `--target spirv`.
End-to-end: `tests/sq2core.ergo` stdout **byte-identical** to the pre-built
reference binary; `tests/buc_colony.ergo` physics **byte-identical** after
normalizing the F44 escape change (see F44 note); `tests/alloc_smoke.ergo`
unchanged (2525.0). GPU emission smoke (`--target spirv` and `--target nvvm`
`--emit-c`) passes on `tests/buc_colony_gpu.ergo`, `galaxy/galaxy_bench.ergo`,
and `tests/gpu_ring_shuffle.ergo`.

---

### Checker (F9–F25)

- **F9 — INTEGER \*\* negative-INTEGER → compile-time error** (`checker.py:_infer_type`).
  Spec Part 3 mandates this; previously compiled to `pow()` truncated into an
  int. Fires on literal/unary-minus/PARAMETER negative exponents; non-constant
  INTEGER exponent still allowed (sign unknowable at compile time).
- **F10 — DO WHILE requires LOGICAL** (`checker.py:_check_do_while`).
  `DO WHILE i` on an INTEGER compiled and ran to 0. Spec line 290.
- **F11 — Intrinsic argument types + arity validated** (new
  `INTRINSIC_ARG_RULES`, `_check_intrinsic`). `SIN(2)` silently promoted;
  `MOD(5.5, 2)` typed from first arg only; `ISHFT(3)` crashed ir_builder with
  a raw `IndexError`. Full matrix per the signatures doc (REAL-only math fns,
  ATAN2/ABS/SIGN/MOD/MAX/MIN/CLAMP homogeneous rules, bitwise INTEGER rules,
  arities). Array-typed args skip validation (element-wise forms unimplemented).
- **F12 — Undeclared parameters are errors** (`_check_function`/`_check_subroutine`).
  Previously defaulted to REAL (functions) or INTEGER (subroutines) — the
  latter silently truncated REAL actuals at the C call.
- **F13 — DO bounds/step must be INTEGER.** REAL bounds truncated via C
  conversion (`DO i = 1, 3.7` ran).
- **F14 — DATA statements validated** (`_check_data`). Undeclared target's
  data silently vanished; overflow counts truncated at gcc; duplicates were
  last-wins. Now: declared target, not ALLOCATABLE, count ≤ elements, literal
  type compatibility, duplicate → error. (DATA errors carry no line number —
  parser doesn't set `DataStmt.line`.)
- **F15 — Scalar initializer on array declaration rejected.**
  `REAL :: A(3) = 1.5` compiled and silently produced zeros.
- **F16 — PARAMETER protections.** Assigning to a subscripted PARAMETER
  element bypassed the const check; a PARAMETER could be a DO variable.
- **F17 — Duplicate function definitions error** (`symbols.py:declare_func`,
  with `is_external` escape for LSP pre-seeded symbols).
- **F18 — Unknown function/subroutine calls error.** Previously passed the
  checker and died at gcc with implicit-declaration.
- **F19 — Subscripting a scalar errors** ("'x' is not an array").
- **F20 — Array↔scalar assignments error.** scalar := array always;
  array := scalar (broadcast) rejected per the array-expression rule after a
  corpus scan found zero uses (explicit loop / `CALL ZERO` instead).
- **F21 — Logical/relational operand types.** `.AND.` on INTEGERs compiled;
  `x < "str"` yielded LOGICAL. Both error now.
- **F22 — SELECT CASE validated:** INTEGER selector, constant INTEGER case
  literals, single DEFAULT, no duplicate values.
- **F23 — ALLOCATE validated:** rank must match declaration; dim expressions
  must be INTEGER.
- **F24 — Diagnostics hygiene:** dedup of identical diagnostics (double
  arg-inference removed), `_stmt_line` set in declarations (errors inside
  initializers now correctly located), collected warnings actually printed to
  stderr (errors still the only abort).
- **F25 — `_const_eval` correctness:** integer division truncates toward
  zero like C (was Python floor: -7/2 gave -4 at check time vs -3 at
  runtime); constant division-by-zero is an error, not silent None; `**`
  folds for non-negative INTEGER exponents.

### Frontend (F26–F27)

- **F26 — `!=` is a LexError** (`lexer.py`). `x := a != b` lexed as
  `x := a` + comment — a silent deletion of the comparison. Message points
  to `/=`, `≠`, `.NE.`. Only exactly-adjacent `!=` is rejected.
- **F27 — VERIFY TOL must be a numeric literal** (`parser.py:_parse_verify`).
  Non-literals survived as AST nodes and were f-stringified into C as Python
  repr garbage.

### IR builder (F28–F33)

- **F28 — Invalid assignment targets raise MCLError** (`_lower_assign`).
  `5 := x`, `a+b := 5`, `g(x) := 5` previously produced no store and no
  diagnostic. (Checker rejects first; this is defense-in-depth.)
- **F29 — `_const_value` folds constant BinaryOps.** `STATIC REAL :: X =
  1.0+2.0` silently emitted with no initializer; `PARAMETER REAL :: X =
  1.5*2.0` emitted literal `None` into C. Folds `+ - * / **` with C-truncating
  integer division; PARAMETER names resolve via `_param_values`.
- **F30 — Array shape expressions folded** (`_lower_shape`). `REAL :: A(N+1)`
  with PARAMETER N emitted Python AST repr into the C declarator. Non-foldable
  expression dims now raise MCLError (bare variable dims kept for
  assumed-shape dummies).
- **F31 — STRING literals typed STRING** (`TYPE_MAP`). Was IRType.REAL →
  `printf("%f\n", hello)`. (Emission half is F44.)
- **F32 — Function-local DATA recorded.** `ir_builder` dropped `DataStmt`
  inside function bodies; values now attach to the local `IRVar.data_init`
  and codegen (F41) emits the initializer.
- **F33 — SIGN intrinsic implemented** (`ir.py` Op.SIGN, `INTRINSIC_MAP`,
  `ir_codegen` emission). Checker accepted SIGN but no backend lowering
  existed. REAL → `copysign`/`copysignf`; INTEGER → `abs(a) * (b >= 0 ? 1 : -1)`.

### IR codegen (F34–F44)

- **F34 — DO loops: negative step, bound hoisting, shadowing (IR-path F7
  analog).** All three emission sites (plain, split-kernel suffix, frame
  loop) now hoist end/step into `_ergo_end{n}`/`_ergo_step{n}` evaluated
  once, comparator follows step sign, and the loop assigns to the declared
  variable (no `int` — post-loop reads see the Fortran-mandated final value,
  not an uninitialized shadow).
- **F35 — Functions end with `return <name>_;` (IR-path F8 analog).**
  Falling off a non-void C function was UB that "worked" at -O3 by register
  luck.
- **F36 — CYCLE inside DO WHILE re-evaluates the condition.** While loops
  now emit `for (;;) { cond; if (!cond) break; body }` — previously
  `continue` skipped the trailing re-evaluation → infinite loop.
- **F37 — ZERO on ALLOCATABLE zeroes the array, not the pointer.**
  `memset(A, 0, sizeof(A))` on a `double *` zeroed 8 bytes. ALLOCATE now
  records byte size in `_ergo_sz_{name}`; ZERO uses it. ALLOC size
  computation also casts each dim to `size_t` (int×int overflow hole).
- **F38 — STOP emits `exit(0)`** — previously `return 0;`, which inside a
  function silently returned 0 to the caller instead of stopping.
- **F39 — RING/WARP subgroup ops error loudly on the CPU path** (MCLError).
  Previously hit the unhandled-op fallthrough and read an uninitialized temp.
- **F40 — Function-local scalar initializers emitted.** `INTEGER :: L = 5`
  inside a function was `int L;` (uninitialized).
- **F41 — DATA applies to non-STATIC scalars and function-local arrays**
  (new `_data_values`/`_data_scalar_init`/`_data_array_init`; reads
  `mod.data_inits` and `IRVar.data_init`).
- **F42 — f32 mode emits f32 arithmetic.** `--precision f32` previously
  computed in double (unsuffixed literals, double libm). Now `f`-suffixed
  literals and `sinf/sqrtf/powf/fmodf/fminf/...`. Also: non-finite literals
  emit `__builtin_inf[f]()`/`__builtin_nan[f]("")` (was `X = inf.0;`).
- **F43 — Final-hash hook precision + self-guarding.** Hardcoded
  `NPART * sizeof(float)` hashed half of each f64 array and broke
  compilation of GPU programs lacking NPART (even with the env var unset).
  Now uses the real element size and skips emission when NPART is absent.
- **F44 — String emission quoted + escaped; STRING formats to `%s`.**
  Strings splice raw into C, so source `\033` was reinterpreted by the C
  compiler as the ESC byte. **Behavior change:** strings now print
  literally what the source contains — `tests/buc_colony.ergo`'s ANSI color
  codes print as literal `\033` text. Physics output byte-identical; if
  ANSI escapes are wanted, that needs a lexer escape-sequence decision
  (spec-level), not a codegen passthrough.

### Cross-file feature (F45) and driver (F46–F48)

- **F45 — EXIT statement implemented** (spec line 289 promised it; it was a
  parse error before). Full plumbing: `KW_EXIT` token/keyword, `ExitStmt`
  AST, parser, checker (`EXIT used outside of DO loop`), IR lowering
  (`meta.kind="exit"`), codegen (`break;`). Known limitation: EXIT inside a
  SELECT CASE inside a loop breaks the C switch, not the loop — same caveat
  class as any `break` in a switch; documented, not handled.
- **F46 — `_load_backend` package-relative** (`driver.py`). Absolute
  `import mcl.backends.*` crashed every `--target` compile after the
  `mcl/`→`core/` rename (and risked silently loading a stray installed
  `mcl` package). Now `importlib.import_module(f".backends.{target}",
  package=__package__)`.
- **F47 — `-N`/`-M` overrides applied before the checker** (`driver.py`
  `_apply_param_overrides` rewrites AST PARAMETER literals right after
  parsing). Bounds/shape checks previously used pre-override values —
  wrongly rejecting valid overridden programs and wrongly accepting
  out-of-bounds ones. IR-level mutation kept (message now prints
  `old → new` with both equal).
- **F48 — `_module_invariants` no longer a stale process-global**
  (`ir_gpu.py` `_compute_module_invariants`). `promote_locals` ran before
  `extract_kernels` populated the global: first compile in a process saw an
  empty set; later compiles saw the *previous module's* parameters —
  compile A-then-B differed from compiling B alone. Both entry points now
  compute the set fresh from the module (identical rule, just not stale).

---

## Known issues deliberately NOT fixed in this batch

- **GPU classification/fusion/promote/linearize semantics** (audit Tier 2):
  split-path re-extraction of SHIFT/SCATTER as INJECTIVE, IF-body stores
  invisible to the classifier, last-store-wins per-array classification,
  STATIC scalars as invariants, fusion conditions 3/4 unenforced +
  stale-CPU re-execution of fused loops, promote_locals `_idx` reuse and
  unrewritten suffix uses, linearize dropping post-inner blocks and the
  row/column-major mismatch, unconditional SPIRV atomics (spec 9.9 open
  item), SPIRV f64-math-at-f32, NVVM backend catalog, RING 32-lane
  assumption, SPIRV IEOR→0.0 fallback. Deferred as the dedicated GPU batch.
- **Legacy `codegen.py` path:** not touched except where batch 1 already
  did. The drift items from batch 1's list still apply.
- **Case policy:** identifiers case-sensitive, keywords case-insensitive,
  intrinsic dispatch uppercases but array lookup is case-sensitive
  (`ir_builder._lower_call_or_subscript`). Mechanism documented in the
  audit; needs a spec decision.
- **`EXIT` inside SELECT CASE inside a loop** breaks the C switch, not the
  loop (F45 limitation).
- **Checker gaps remaining:** array-result intrinsics (MATMUL/TRANSPOSE/
  RESHAPE/SUM/...) validate but have no backend lowering (loud gcc
  failure); LSP-only PARAMETER-with-shape path works around F15 via
  pre-seeded symbols.
- **Escape sequences in strings:** none. Source text is literal; `\033`
  prints as four characters (F44 consequence, spec decision pending).

## Notes for future regression hunts

- Probe suites live in `work/determinism_audit/probes_{checker,front,
  builder,codegen,driver,integration}/`; the corpus runner is
  `work/determinism_audit/corpus_run.sh` (compare against `baseline.txt`).
- If loop codegen regresses, the three emission sites are
  `ir_codegen.py` split-kernel suffix (~956), frame loop (~1001), plain CPU
  loop (~1226) — all share `_emit_do_header`/`_emit_do_footer`.
- If a new intrinsic is added, four places must agree: checker
  `INTRINSIC_RETURNS` + `INTRINSIC_ARG_RULES`, builder `INTRINSIC_MAP`,
  codegen emission, and (for GPU) the SPIRV/NVVM backends.
- Behavior changes vs batch-1 compiler that are *intended*: negative-step
  loops now execute; functions without RETURN now return their result
  variable; DO WHILE+CYCLE now terminates; WRITE/PRINT strings print
  literally (F44); programs violating F9–F23 spec rules now fail to
  compile.

---

---

## 2026-07-21 — JIT hardening (jit.py proof of concept)

**Summary.** Four fixes to the gcc-based JIT (`core/jit.py`), which is now
the supported JIT path. The x86-64 machine-code JIT (`core/jit_x86.py`) is a
long-term cross-platform project and is marked **experimental/known-broken**
in its docstring (constants in expressions can segfault the host process;
no comparisons, no INTEGER datapath, no arrays, no checker) — do not use it.

**Verification:** `work/determinism_audit/test_jit.py` — 15 checks covering
f64/f32 REAL functions, INTEGER functions, subroutines, loop+IF+EXIT,
cache correctness, precision isolation, error paths. All pass.

### F49 — JIT signatures guessed from Python values; INTEGER functions returned garbage

- **File/function:** `jit.py` → `JitLibrary.call`
- **Symptom:** `DOUBLEIT(21)` (an INTEGER function) returned `0.0` — every
  return type was auto-defaulted to REAL, and argument types were guessed
  from Python value types.
- **Fix:** new `register_ir(ir_module)` derives every function's signature
  from the IR declarations (INTEGER/LOGICAL → `c_int`, REAL →
  `c_float`/`c_double`, subroutine → void). `call()` uses the registered
  signature, validates arity, and raises `MCLError` for unknown names
  (listing available functions) and for functions with array or non-scalar
  parameters (marked unsupported with the reason).

### F50 — JIT cache ignored precision and flags

- **File/function:** `jit.py` → `jit` cache key
- **Symptom:** `jit(src, precision=32)` and `jit(src, precision=64)`
  returned the *same* cached library — the key was the source hash only.
- **Fix:** cache key is now `source:precision:cpu_fast_math`.

### F51 — JIT leaked its precision into the process global

- **File/function:** `jit.py` → `jit`
- **Symptom:** `jit(precision=32)` left `get_real_precision() == 32`, so a
  later `compile_source` call in the same process silently compiled in f32.
- **Fix:** precision is saved before the build and restored in a `finally`.

### F52 — JIT `.so` written to a predictable temp path

- **File/function:** `jit.py` → `jit` output path
- **Symptom:** `tempdir/ergo_jit_<hash>.so` — predictable, clobberable,
  pre-creatable by another process.
- **Fix:** each library gets a private `tempfile.mkdtemp(prefix="ergo_jit_")`
  directory, removed on GC; failed gcc runs clean up too.

### F53 — JIT libraries could not expose STATIC storage

- **File/function:** `ir_codegen.py` → `_emit_static_var`; `jit.py`
- **Symptom:** STATIC arrays/scalars were emitted with the C `static`
  keyword, hiding them from the shared-library symbol table — Python had
  no way to reach the storage that Ergo subroutines operate on directly
  (the Spec Part 7 idiom: STATIC state is accessed by name, never passed
  as a parameter).
- **Fix:** jit mode omits `static` on STATIC declarations, exporting them.
  New `JitLibrary` accessors: `array(name)` → (flat ctypes array, shape),
  `array_np(name)` → zero-copy numpy view, `value(name)` /
  `set_value(name, v)` for STATIC scalars. Multi-dim arrays flatten in C
  row-major order (first Ergo index = outermost).

### F54 — JIT rejected all array parameters

- **File/function:** `jit.py` → `register_ir`, `call`
- **Symptom:** functions with assumed-shape array parameters
  (`REAL :: A(N)`) were marked unsupported — the JIT was scalar-only,
  useless for matrix code.
- **Fix:** array parameters register as `POINTER` types and `call()`
  marshals them zero-copy from numpy arrays (dtype-checked: float64 for
  f64 REAL, float32 for f32, int32 for INTEGER; must be C-contiguous),
  ctypes arrays, `array.array`/memoryview (format-checked), or
  lists/tuples (copied — callee mutations lost). Element counts are
  validated against the declared shape, resolving parameter-name dims
  (`A(N)`) from the call arguments; mismatch raises `MCLError`.

**Verification:** `work/determinism_audit/test_jit_arrays.py` — 21 checks
(all four marshal paths, shape/dtype/contiguity validation, f32, STATIC
array round-trip through a callee, STATIC scalar read/write both
directions, accessor misuse errors). `test_jit.py` — 15 checks. All pass.

---

## 2026-07-21 — Bugfix batch 1 (lexer, parser, IR builder, legacy codegen)

**Summary.** Eight fixes across four files. The headline item is F3: the
line-continuation regex was silently shifting every token line number after
the first `&`, corrupting error messages, `#line` directives, and kernel
reports. Also fixed: a crash in VERIFY's error path, silently wrong COMPLEX
lowering, broken negative-step DO loops (legacy path), and undefined behavior
when a function ends without RETURN. Added ASCII (`<=` `>=` `/=` `==`) and
dotted (`.LE.` `.GE.` …) operator spellings alongside the Unicode ones.

**Files changed:**

| File | Fixes |
|---|---|
| `lexer.py` | F3, F4 |
| `parser.py` | F1, F2 |
| `ir_builder.py` | F5, F6 |
| `codegen.py` (legacy AST path) | F7, F8 |

**Verification:** 30 automated checks, all passing — 20 lexer unit tests,
5 parser tests, and one end-to-end program (source → lexer → parser →
codegen → `gcc -O3 -fwrapv -ffp-contract=fast -std=c11` → run, output
verified). Test harness preserved at `work/ergo_compiler_fixes/`.

---

### F1 — VERIFY error path crashed with AttributeError

- **File/function:** `parser.py` → `_parse_verify`
- **Symptom:** a malformed VERIFY (e.g. `VERIFY X FOO 3`) raised
  `AttributeError: 'Parser' object has no attribute '_error'` instead of a
  proper parse error.
- **Root cause:** `_error` is a `Lexer` method; `Parser` never had one. The
  call site was `raise self._error(...)`.
- **Fix:** raise `ParseError(f"Expected ORACLE, ...", line, col)` directly.
- **Test:** malformed VERIFY now raises `ParseError` containing "Expected
  ORACLE".

### F2 — VERIFY pseudo-keywords were case-sensitive

- **File/function:** `parser.py` → `_parse_verify`
- **Symptom:** `VERIFY A oracle 8` failed; only uppercase
  `ORACLE`/`EVERY`/`TOL`/`NET`/`GPU` were accepted, inconsistent with the
  language's case-insensitive keywords.
- **Fix:** compare with `.upper()` at all five sites.
- **Note:** these are *pseudo*-keywords (lexed as `IDENT`, matched by value),
  which is why the case-insensitive keyword table didn't cover them.

### F3 — Line continuation broke all downstream line numbers

- **File/function:** `lexer.py` → `__init__` (removed), new
  `_consume_continuation` in the tokenize loop
- **Symptom:** after the first `&`-continuation, every token's line number
  was too low by the number of joined lines — corrupting error messages,
  `#line` directives in generated C, and kernel-report source lines.
  Bonus corruption: an `&` at end-of-line *inside a string literal* was
  silently rewritten before lexing.
- **Root cause:** continuation was done by regex pre-pass
  (`re.sub(r'&\s*\n\s*', ' ', source)`) before position tracking began.
- **Fix:** continuation is now handled during lexing via
  `_consume_continuation`, which consumes `&` <whitespace> `\n` using the
  same `_advance` that tracks line/column. A stray `&` not followed by a
  newline is a `LexError` (same as before).
- **Lesson:** never pre-process source text in a way position tracking
  can't see.
- **Tests:** tokens after a continuation keep physical line numbers;
  multiline string containing `&` → clean `LexError`, no silent mutation.

### F4 — ASCII and dotted operator spellings added

- **File/function:** `lexer.py` → two-char operator section and
  `_try_dotted_keyword`
- **Symptom:** `a <= b` died with "Unexpected token: EQ" — the *only*
  spellings for `≤ ≥ ≠` were the Unicode glyphs, and the Fortran dotted
  relational set was absent.
- **Fix:** new two-char tokens: `<=` → `LEQ`, `>=` → `GEQ`, `/=` → `NEQ`,
  plus `==` as an alias for `=` (unambiguous — two bare `=` never legally
  adjacent). Dotted keywords extended: `.EQ. .NE. .LT. .LE. .GT. .GE.`
  (case-insensitive, matching `.AND.` etc.). Unicode `≤ ≥ ≠` unchanged.
- **Edge cases preserved:** `1.LE.2` lexes as `1`, `.LE.`, `2` (the number
  reader already refuses a dot before a letter); `.5` still a real literal;
  plain `/` and DATA-statement slashes unaffected.
- **Tests:** 13 lexer tests cover the new spellings and edge cases.

### F5 — Missing `Any` import in IR builder

- **File/function:** `ir_builder.py` → module header, `_const_value`
- **Symptom:** latent — `_const_value(self, node) -> Any` referenced `Any`
  without importing it. Saved at runtime only because
  `from __future__ import annotations` makes annotations lazy strings;
  `typing.get_type_hints` or any static checker would fail.
- **Fix:** added `from typing import Any`.

### F6 — COMPLEX silently lowered to REAL

- **File/function:** `ir_builder.py` → `TYPE_MAP`, `_ir_type`
- **Symptom:** declaring `COMPLEX` produced a REAL with no warning —
  silently wrong numerics, the one failure mode a determinism language
  can't afford.
- **Fix:** removed the `COMPLEX → REAL` placeholder from `TYPE_MAP`;
  `_ir_type` now raises `MCLError` ("not supported yet") on COMPLEX.
- **Note:** legacy `codegen.py` still maps COMPLEX to `double _Complex`;
  if COMPLEX is ever implemented for real, both paths must agree.

### F7 — Negative-step DO loops silently empty (legacy path)

- **File/function:** `codegen.py` → `_emit_do`
- **Symptom:** `DO I = 10, 1, -1` generated `for (i = 10; i <= 1; i += -1)`
  — zero iterations, no warning.
- **Fix:** loop bounds/step are hoisted into per-loop temporaries
  (`_ergo_endN`, `_ergo_stepN`, counter in `__init__`) and the comparator
  follows the step sign: `step > 0 ? i <= end : i >= end`.
- **Side effect (intentional):** bounds are now evaluated once at loop
  entry, matching Fortran semantics (previously re-evaluated per iteration).
- **Open:** the IR path (`ir_codegen.py`, not in this batch) must be checked
  for the same bug.

### F8 — Function without RETURN → C undefined behavior (legacy path)

- **File/function:** `codegen.py` → `_emit_func_def`
- **Symptom:** a function that sets its return variable but never executes
  `RETURN` fell off the end of a non-void C function — UB. Appeared to work
  at `-O3` because the value often lingered in the return register; the
  worst kind of bug (invisible until a compiler/flag change).
- **Fix:** every function body now ends with an explicit
  `return <name>_;` (Fortran semantics: falling off the end returns the
  function-name variable). An explicit user `RETURN` simply makes the added
  line unreachable — harmless.
- **Open:** same check needed for `ir_codegen.py`.

---

## Known issues deliberately NOT fixed in this batch

- **Case policy:** identifiers case-sensitive, keywords case-insensitive,
  intrinsic dispatch uppercases but array lookup is case-sensitive
  (`ir_builder._lower_call_or_subscript`). Needs a spec decision, not a patch.
- **Loop-variable shadowing (legacy path):** `for (int I = ...)` shadows an
  outer declared `I`, so the loop var doesn't retain its final value after
  the loop — un-Fortran-like.
- **`_func_params` multi-dim array emission** builds C declarators via
  string slicing (`dims[1:-1]`); works by accident for 2D/3D, fragile.
- **`_lower_if` dead code** (`ir_builder.py` ~line 559–568): leftover
  deliberation comments and an unused `result_items`; harmless, cosmetic.
- **Dual codegen drift:** legacy AST codegen and `IRCodeGen` can diverge
  silently; F7/F8-style bugs must be fixed in both. Consider deprecating
  the legacy path or adding a golden-output test that runs both.

## Notes for future regression hunts

- All fixes are additive or behavior-correcting; no grammar was removed.
  Existing valid programs compile identically, except: programs that relied
  on wrong line numbers after `&`, used COMPLEX (now an error), or depended
  on negative-step loops being empty (they now run).
- If a new lexer bug appears around `.` or numbers, check the interaction
  order in `tokenize()`: dotted keywords → numbers → identifiers, and the
  number reader's refusal to eat a dot before a letter.
- If line numbers drift again, suspect any future pre-processing of
  `self.source` before `Lexer.__init__` stores it (see F3 lesson).
