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
