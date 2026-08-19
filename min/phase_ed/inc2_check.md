# Inc-2: int64 (2A) + matrix-free ED matvec with gather-window streaming (2B)

## 2A — INTEGER*8

Syntax `INTEGER*8` (only *8 accepted; `INTEGER*4` etc. are parse errors).
End-to-end: parser kind suffix -> checker type `"INTEGER*8"` (NUMERIC,
INT_TYPES) -> `IRType.INT64` -> C `long long`, `%lld`, `xLL` literals.

- Promotion (Fortran kind rules): INTEGER*8 wins over INTEGER among
  integer operands; REAL still wins overall. Implicit narrowing
  `INTEGER := <int64 expr>` is a **compile error** (use INT()
  explicitly); implicit widening int64 := INTEGER is fine. INT8(x) is
  the explicit widening intrinsic; INT(x) stays the explicit narrowing
  one (int64 -> int32).
- DO loop variables/bounds may be INTEGER*8 (needed for 3^N state
  spaces at N >= 20).
- Arrays of INTEGER*8 work (1-D tested).
- GPU: extraction of any loop touching int64 values is rejected with
  the named diagnostic `INTEGER*8 (int64) is CPU-only — not supported
  on GPU (Inc-2A)` (the alternative was silent i32 truncation in push
  constants / element types).
- Oracle: `tests/int64.ergo` — 3^20 = 3486784401, sums/products past
  2^31, MOD/DIV, comparisons, INT8/INT/REAL round-trips, int64 array
  prefix sums — all exact. Regression: emit-c byte-identical to HEAD
  for gpu_tile, dbm_radial_gpu, gpu_clipmap, gpu_pingpong.

## 2B — matrix-free ED matvec

Physics: ternary rotor chain, basis = ternary strings, dim = 3^N,
original gauge at B=0.25 (V = K_PHASE − B·K_BIAS = 0 → real H):

  out[x] = (diag(x) − SHIFT)·v[x] − (J/2) Σ_i [m1·v[x−3^i+3^j] + m2·v[x+3^i−3^j]]
  diag(x) = Σ_i ((d_i−1)²)/2, d_i = (x // 3^i) % 3, j = i+1 mod N

Digit extraction is unrolled in the generated kernel (no nested loops —
extraction rule), masks are branch-free MIN products, bond reads use a
MOD-wrapped index so mask=0 reads stay in-bounds (mask=1 ⇒ wrapped ==
raw, provably). No SRC/COEF tables anywhere (the stage0 table approach
is dead at N≈17-18 as predicted).

**SHIFT fix (physics, not machinery):** the stage0 shift-3 dominance
(|E0−3| > |Emax−3|) is N=8-specific. Measured failure: N=14 with
SHIFT=3 converges to the spectrum TOP (+11.68 instead of −4.93). Now
SHIFT = 2N: Emax ≤ 1.5N < 2N makes H̃ negative definite at any N.

**Power iteration:** H̃ = H − 2N·I, v ← H̃v, ρ = v·w (v normalized),
E0 = ρ + 2N, convergence |Δρ| < 1e-12, 3000-iter cap. Explicit
multi-accumulator reduction loops (Inc-1 ordered combine —
deterministic), not DOT_PRODUCT/NORM2 intrinsics (those lower to CPU
loops and would force full-vector downloads every iteration).

### Variants (gen_ed_matvec.py)

- **resident** (N ≤ 17): V/W fully on GPU (N=17: 2 × 1.03 GB).
- **streamed** (N = 18): V resident (3.1 GB < maxStorageBufferRange
  4.29 GB — now asserted in vk_host create_buffer), W produced through
  a QT = 3^16 window per tile and downloaded to the host array HW;
  Rayleigh ρ and ||W||² accumulate via per-tile multi-reductions (host
  ordered combine in tile order — deterministic). HW/V host copies are
  kept off the GPU with never-true WRITE disqualifiers (host arrays
  must not become GPU-resident — VRAM).

### Results (RTX 2060, f64)

| N | path | E0 (Ergo GPU) | E0 (ref) | note |
|---|---|---|---|---|
| 8 | resident | −2.8591343125 | −2.859134312545 (stage0) | exact to print precision, CPU build identical |
| 14 | resident | −4.9302231299 | −4.930223376092 (eigsh) | 2.5e-7 (drho 1.1e-9 at 3000-iter cap); CPU f64 build identical to GPU |
| 16 | resident | −5.6251812974 | −5.625185465982 (eigsh) | 4.2e-6 (drho 1.4e-8 at cap) |
| 17 | resident | (see run) | (see run) | |
| 18 | streamed | (see run) | — | streaming machinery demo |

Matvec checksums vs the numba bridge (`ed_ref.py`, same gauge, same
seed): N=8 c1/c2 EXACT; N=14 within f64 reduction-order noise
(c1: −141136851.8323995 vs −141136851.83240008). Probes w0/wmid/wlast
match to ~1e-14.

Determinism: two GPU runs at N=8 and N=14 → byte-identical full output.

Perf: N=14 3000 iters: GPU 35 s vs CPU f64 20 min (34×). N=16: 5m16s
GPU (105 ms/iter: 43M×~200-flop f64 matvec + 2 multi-reductions/iter).
CPU N=18 was not attempted (~26 h estimated).

### Deferred: N=19/20 remote-slice gather streaming

At N=19 (9.3 GB f64) V itself is not resident. Design (validated in
pieces, not yet one program): split the matvec into a low-bond kernel
(gather halo ≤ 2·3^(N−2) — a QT + 2-halo window buffer ≈ 1.4 GB at
QT = 3^16) and a high-bond kernel for the top bonds (offsets ~3^(N−1):
a separate QT remote slice uploaded per tile via the Inc-4 ranged
upload path from the host vector). i64 tile base needed only at N=20
(indices fit i32 through N=19; 2A delivered the host side). Host
streams slices via ergo_vk_upload_at between per-tile dispatches —
never per-tile buffer binds (bindings stay per-frame-per-pipeline).

## N=19: landed (variant `streamed19` in gen_ed_matvec.py)

Two new statement intrinsics make streaming expressible in Ergo with
zero host array copies (`core/ir_builder.py`/`ir_codegen.py`,
checker-registered): `CALL VK_STAGE(gpu_arr, host_arr, src0, dst0,
len)` (host→device slice) and `CALL VK_FETCH(host_arr, gpu_arr, src0,
dst0, len)` (device→host). Both are frame-draining sync points
(VK_STAGE only when the recording frame has unsubmitted kernel writes);
CPU builds lower them to memmove so streamed programs still run
CPU-only. Diagnostics: non-GPU-resident device arg or GPU-resident
host arg are compile errors.

Design (generic N; validated at N=8 against the stage0 oracle):
- QT = 3^(N−3), NT = 27 tiles. Kernel A (diag + bonds i ≤ N−3) reads a
  5·QT ring window VA (halo 2·QT); the ring slot of global g is simply
  MOD(g−1, WINA)+1 — no base tracking; each tile stages only the
  advancing QT slice (one prime of 3·QT per iteration).
- Kernel B (bonds i = N−2, N−1; offsets 6·QT and 9·QT−1) reads four
  remote QT slices staged per tile (the 9·QT−1 offset is absorbed by
  staging the slice shifted by 1 — no straddle).
- Per-tile multi-reduction accumulates RHO/NRM2T in tile order (Inc-1
  combine), then VK_FETCH streams the WWIN tile into host HW.
- Device total at N=19: 1.72 + 1.38 + 0.34 GB ≈ 3.45 GB — fits with
  headroom (maxStorageBufferRange 4.29 GB per buffer asserted).

Two runtime fixes fell out of profiling:
1. **HOST_CACHED staging** (vk_host.c): the staging buffer was
   HOST_VISIBLE|HOST_COHERENT = write-combined on this driver —
   measured 0.57 GB/s; memcpy-bound. HOST_CACHED staging measures
   6.7 GB/s (12×). Every GPU binary prints the choice at startup.
2. **Reduction readback chunk** 1024 → 65536 floats: the N=19 per-tile
   reduction issued ~9k submit/waits per iteration (8 KiB chunks);
   now ~300/iter. Combine order unchanged (bitwise-identical results).

Measured at N=19 (300-iter probe NITER=2): ~11.5 s/iteration —
57 GB/iter of transfers (B-slices 37 GB dominate) vs ~290 GFLOP/iter:
arithmetic intensity ~5 flop/byte, deeply transfer-bound on PCIe
(roofline: f64 compute would need ~30 flop/byte to balance at this
card's ~200 GFLOP/s FP64). Slice-caching / tile-order scheduling could
cut the B-slice traffic ~2-4× but needs per-tile slot-index push
constants (the arena-slots-without-rebinds scheme) — deferred; v1
documents the wall.

## Inc-5: tile scheduling / slice cache (variant `streamed19s`)

The deferral was wrong about needing a compiler feature: slot indices
are ordinary Ergo INTEGER scalars (per-dispatch push constants since
Inc-1) and `RA(SLOT*QT + K)` is an affine index the extractor already
handles. Zero compiler changes for the cache itself.

Schedule construction (offline, baked into DATA tables — runtime is
table reads): the offline simulator evaluates cache policies with an
exact Belady model. Findings:
- Slice identity is the 1-based host start, NOT the tile index — the
  ±(27·QT−1) wrap-bond slices are shifted one element off tile
  alignment (bug caught by numpy simulation before any GPU run).
- A step's remotes are simultaneously resident — victim selection must
  exclude the current step's needed set (second sim-caught bug).
- The A/B stride conflict is real: kernel A's sliding window wants
  canonical tile order; kernel B's reuse spans ±(6..27) tiles want
  class-blocked (mod 3/9/27) orders. Every schedule that helps B by
  30%+ wrecks A by 5-9×. Resolution: **variant Y** — move all bonds
  except the wrap bond (i=N−1) into the A ring (halo 18 slices, ring
  37·QT), and give B (wrap bond only, refs {d±27}) a tiny Belady arena
  (C_B=4 slots; 108 misses = the distinct-slice floor — cache hits are
  impossible at 54-step reuse distance, the arena is a staging area).
  Canonical order ⇒ reduction combine bitwise-identical to streamed19.
- Numbers (QT=3^15, NT=81): A-ring 100 slices + B 108 + W fetch 81 =
  289 slices = 33.2 GB/iter vs 57 GB uncached — **1.72× fewer bytes**
  (target was 1.5×). VRAM: ring 4.25 + arena 0.46 + WWIN 0.11 +
  staging 0.13 ≈ 4.95 GB (fits; the 37-slot ring was chosen against
  maxStorageBufferRange 4.29 GB — 4.25 GB per buffer).
- Measured wall: 8.0 s/iter vs 9.85 s/iter uncached (1.23×) — the
  residual is fixed overhead: ~430 transfers + ~160 frame drains per
  iteration (per-tile fetch/reduction drains serialize host/device),
  the host normalize pass, and f64 GPU compute. Bytes were cut 1.7×;
  latency-bound components didn't move. Also landed en route: single-
  download multi-acc reduction readback (one submit/wait per tile
  instead of two).

Oracles: N=8 streamed19s full convergence E0 = −2.8591343125 exact
(CPU and GPU); N=19 mv1 checksums bitwise identical to streamed19 AND
to the lean CPU reference (c1 = −46554303960.39218, c2 =
−186217215708.692, probes exact); determinism two runs byte-identical.
Energy trajectory (streamed19s, 100 iters, ~8 s/iter): E0(50) =
−6.2803309579, E0(100) = −6.5267461409 (drho 2.0e-3, still converging;
full convergence at N=19 is multi-hour and out of oracle scope — the
matvec checksum is the hard oracle). Cross-check: capped CPU power
iteration (temp-free numba, 2-vector footprint) at iter 1 gives
E0 = −2.0778282186 vs the GPU's −2.0778282188 — 2e-10 agreement at
matched iteration (the GPU labels the unnormalized first pass as
iter 1, so its "iter k" is CPU "iter k-1" for k >= 2).

Ops note addendum: stdout redirected to files is block-buffered — use
`stdbuf -oL` when a run's progress must be visible mid-flight, and
always launch with the background-task wrapper (a bare `&` child dies
with the session turn).

### Ops note: reference-generation memory

scipy eigsh with default `ncv=20` allocates a 20 × dim Krylov
workspace — 20 GB at N=17 — which OOMed the host IDE when run
concurrently with the GPU jobs. Reference energies above N=16 use
`ed_ref.py power N` (plain power iteration, two vectors, ~2 GB) or
explicit small `ncv`. One heavyweight job at a time.

## Files

- `tests/int64.ergo`
- `min/phase_ed/gen_ed_matvec.py` — generator (resident/streamed)
- `min/phase_ed/ed_ref.py` + `ed_ref_report.json` — bridge/reference
- compiler: `core/ir.py` (IRType.INT64, Op.TO_INT64), `core/parser.py`
  (kind suffix), `core/checker.py` (type rules), `core/ir_builder.py`,
  `core/ir_codegen.py`, `core/ir_gpu.py` (int64 GPU rejection),
  `core/driver.py` (scoped -mcmodel=large), `core/runtime/vk_host.c`
  (maxStorageBufferRange query + assert)

## Inc-2 follow-up (2026-08-10): frame-batch stale-scalar bugs, found by the tower variant

The `tower` generator variant (deflated power iteration, N=16 GPU ED
for the LL↔string campaign) exposed two GPU-path correctness bugs.
Both were 100% reproducible: deflated states collapsed to the ground
energy; the last state's SECT overlaps read as exact zeros. CPU builds
were correct throughout, which is what fingered the GPU codegen path.

### Bug 1 (the campaign blocker): pending reduction scalar consumed by a GPU kernel's push constants

`core/ir_codegen.py::_emit_body` deferred coalesced reduction
readbacks (`_pending_reductions`, Inc-5) until "the next item is NOT a
GPU kernel". A GPU kernel whose push constants pack a pending
accumulator is also a consumer — the PC block is memcpy'd at record
time — but the flush test never fired for it, so the consumer recorded
a one-iteration-stale (or zero) value. In the tower: the Gram–Schmidt
overlap reduction OV was immediately followed by the W-update kernel
whose PC packs OV; the update ran with stale OV every iteration, the
deflation never bit, and every later state converged to the ground
state (E1 = E0 = −5.0250389412 instead of −4.8774898361 at N=8).

The earlier "workaround print" (an in-loop WRITE of OV) only worked
because a host read of OV made the next item non-GPU, forcing the
flush — position mattered, not the print. Fix: the flush condition now
also fires when the next GPU kernel's PC scalar set
(`scalars_read` + loop-bound ref) intersects the pending accumulators
(`reduction_var`/`reduction_vars`). Emitted C now orders: OV reduction
→ drain → readback → W-update dispatch with the fresh OV.

### Bug 2 (diagnostics): host-fallback kernel loops read stale host arrays

`_gpu_arrays()` gives device buffers only to arrays used by frame-loop
kernels, so the tower's last-state array (ST3: written after the final
frame loop, read only by the post-loop SECT kernels) stays host-only.
Its store loop then host-falls-back — `_emit_loop` set `kernel = None`
and emitted the CPU loop with NO download of its GPU-resident reads,
so `ST3 := V` copied a stale host V (mid-body download logic skips
kernel-planned loops, assuming they run on device), and the SECT
overlaps involving ST3 printed exact zeros on GPU. Fix: on host
fallback of a kernel-planned loop, drain the frame and download the
intersection `kernel.arrays_read ∩ _gpu_arrays()` before the CPU loop
(body-download bookkeeping + ping-pong offset handling included).
SECT now resolves the winding pair to M = ±1 exactly (2×2 block
eigenvalues ±1.0000) on GPU.

### Proof

- Workaround removed from `gen_ed_matvec.py` (tower variant emits no
  sync print). N=8 GPU tower NSTATE=3: −5.0250389412, −4.8774898361,
  −4.8774898361 — scipy to print precision; two runs byte-identical.
- N=16 tower regression: two runs byte-identical (T16_FIX_DET_OK),
  E0 = −9.9142125030, winding gap 0.07426 (campaign values unchanged).
- CPU `--emit-c` byte-identical to pre-fix HEAD for programs not using
  either changed path (gpu_stencil2d, gpu_dot_product, prng,
  xfer_range sampled).
- Oracle suite: see below / campaign report.

### Pre-existing limitation (deferral, unrelated)

`ERGO_VK_MAX_BUFFERS` = 64 counts every per-kernel reduction partials
buffer; the 7-state tower exceeds it (9 arrays + ~70 `d__reduce_*`
slots). NSTATE ≤ 3 fits. A shared partials pool needs liveness
analysis across deferred readbacks — not attempted here.
