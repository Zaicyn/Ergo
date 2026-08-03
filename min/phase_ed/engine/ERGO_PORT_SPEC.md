# Ergo Port Specification — phase-engine hot layers

Grounding: `core/ir_gpu.py` (`extract_kernels`, `linearize_nested_loops`,
`_classify_store_index`), `Spec/Ergo_Spec.md` Parts 8–9,
`Spec/Ergo_Intrinsic_Signatures_Complete.md`. Oracle numbers come from the
Python engine (`results_fss.json`, `results_sweep1.json`, `bench_alloc.json`).

## 1. Layer inventory and extraction status TODAY

### (a) Index-arena matvec — NEEDS RESTRUCTURING (workaround exists)

Natural Fortran form:
```
DO X = 1, DIM
  ACC := 0.0
  DO T = 1, TT                 ! TT = 6N, fixed per (model, N)
    ACC := ACC + LUT(CID(X,T)) * V(SRC(X,T))
  ENDDO
  OUT(X) := ACC
ENDDO
```
Extraction status: **REJECTED today**, for two independent reasons found
in `ir_gpu.py`:
1. The store `OUT(X) := ACC` sits AFTER the inner loop — `linearize_nested_loops`
   (ir_gpu.py:683) explicitly blocks: "any non-empty item AFTER the inner
   loop blocks linearization".
2. Moving the store inside the inner loop does not help: the linearizer
   requires "1D stores must not index by either loop variable"
   (ir_gpu.py:712-ish), and OUT(X) is indexed by the outer loop var.
   The collapsed store cannot be proven INJECTIVE (index via division
   → SCATTER per `_classify_store_index`, ir_gpu.py:2466: non-affine or
   division ⇒ SCATTER ⇒ CPU-serialized by default, Spec 8.2).

**Workaround that compiles today:** generated UNROLLED single loop —
TT is a compile-time constant per (model, N) (48 at N=8, 72 at N=12,
84 at N=14), so the code generator emits:
```
DO X = 1, DIM
  OUT(X) := DIAG(X)*V(X) + LUT(CID(X,1))*V(SRC(X,1)) &
                        + LUT(CID(X,2))*V(SRC(X,2)) + ...   ! TT terms
ENDDO
```
Classification: store OUT(X) affine injective ⇒ INJECTIVE ⇒ GPU kernel;
reads V(SRC(X,k)) are array-indexed LOADs (gather) — allowed;
single expression, no loop-carried accumulator (rule 6 targets
cross-iteration accumulators; per-iteration temporaries are registers).
All seven extraction rules (ir_gpu.py:34–47) pass. Numerics: the term
order is fixed and identical to sequential evaluation, so results are
bitwise reproducible (Spec Part 7) — matches the Python arena to the
last bit if the same term order is emitted.

### (b) Dot products / norms (Lanczos orthogonalization) — COMPILER WORK

`extract_kernels` maps REDUCTION → "CPU loop (staged reduce future)"
(ir_gpu.py:30). The DOT_PRODUCT intrinsic is declared in the checker
(checker.py:35) and documented (lsp_server.py:270,
Ergo_Intrinsic_Signatures_Complete.md:115), and Part 9's table promises
"staged reduce (warp shuffle)" — but there is **no lowering**: DOT_PRODUCT
appears in no codegen backend (checked codegen.py, ir_codegen.py,
backends/), and the intrinsics doc checklist leaves it unticked
("– [ ] DOT_PRODUCT of two vectors"). Until a deterministic staged
reduction lands, Lanczos reductions run on the CPU backend.

### (c) Batch sweep over parameter points — HOST PATTERN (no kernel needed)

The sweep is orchestration: per point, build coefficients (scalar
arithmetic on host) and launch the matvec/eigensolver. Nothing to
extract; the parameter grid lives in a STATIC table initialized by DATA
statements. Not a compiler blocker.

### (d) COO dense build (memset + scatter) — EXTRACTS TODAY

- memset: `CALL ZERO(A)` → GPU fill per the buffer state machine
  (Spec 8.1: ZEROED via vkCmdFillBuffer / cudaMemsetAsync).
- scatter: `OUT(ROWS(K)) := VALS(K)` — data-dependent index via array
  LOAD, asserted non-colliding (COO entries are unique by construction)
  ⇒ FLOW ⇒ "GPU kernel (gather/scatter), parallel by contract"
  (ir_gpu.py:28, Spec 9.4 FLOW). No read-modify-write of OUT ⇒ not
  SCATTER. This is the canonical Ergo idiom per Part 9.2.

### (e) GPU dense eigh — OUT OF SCOPE for Ergo v1

cusolver syevd binding is a library call, not an extractable kernel.
Keep via host FFI to cupy/cusolver (current Python path: 2.3 s per
6561²-c64 full diagonalization, `gpu_dense.py`).

## 2. Data layout

- All arrays STATIC (Spec: STATIC arrays are alias-free by design and
  arena-backed in BSS, 64-byte aligned, zero-filled by the loader).
- Index arena `SRC(DIM, TT)` int32, coefficient IDs `CID(DIM, TT)` uint8,
  `LUT(4)` complex, `DIAG(DIM)` real — initialized once at startup
  (computed, not DATA; DATA statements for the small fixed tables:
  LUT recipes, trig-free phases since coefficients carry them).
- Arena sizing (from alloc work): DIM×TT×5 B — 1.3 MB at N=8, 153 MB at
  N=12, 1.6 GB at N=14 → `--arena-size 256M` covers N ≤ 12 plus vectors;
  N=14 needs `--arena-size 3G` (Spec line 31: flag accepts K/M/G
  suffixes; exhaustion aborts with a named-bytes message).
- The arena is build-once-per-(model,N) — the "allocate once at
  startup, never free" pattern Spec line 29 endorses.

## 3. Missing compiler features (needed, in priority order)

1. **DOT_PRODUCT / NORM2 lowering** (CPU staged deterministic reduction
   now, GPU warp-shuffle staged reduce next) — blocks on-GPU Lanczos.
2. **Nested-loop linearization for accumulator-then-store nests** —
   the canonical `ACC` + post-loop store form (blocked at two places,
   see 1a). Unrolling is the interim path and is acceptable at TT ≤ 84;
   beyond that (larger N, second-neighbor models) code size will matter.
3. **FLOW write with multiple contributions** (`OUT(P(K)) := OUT(P(K)) + V`
   read-modify-write): currently SCATTER ⇒ CPU-serialized by default,
   GPU atomics only under `--gpu-fast-math` (Spec 8.2). The dense-build
   scatter avoids this by construction (unique entries); any future
   additive assembly does not.

## 4. Staged port order (each stage gated on the Python oracle)

| Stage | Deliverable | Oracle (must match) |
|---|---|---|
| 0 | CPU Ergo matvec, unrolled form, N=8 | E0 = −2.8591343125, gap = 0.120548 (B=0.25, J=1.0) to 1e-12; bitwise vs Python arena if term order preserved |
| 1 | Same as GPU INJECTIVE kernel | identical eigenvalues; throughput ≥ 10⁴ mv/s at N=8 (Python arena: 11 074) |
| 2 | Host Lanczos (CPU reductions) + gap-only driver | rotor B=0.25 row of results_sweep1.json, gaps to 1e-9 (c128 path) |
| 3 | GPU COO dense build (ZERO + FLOW scatter) | dense eigenvalues vs `fastchain_to_dense`, max Δ ≤ 1e-6 (c64) |
| 4 | DOT_PRODUCT/NORM2 lowering (compiler work) | dot products bitwise-identical to sequential CPU evaluation |
| 5 | Full-GPU Lanczos | Stage 2 oracle on device |

## 5. Ergonomics

```
python -m core compile engine/ergo/rotor_mv.ergo --arena-size 256M --gpu -o rotor_mv
./rotor_mv --grid B=0.25 J=0.5:0.1:2.0 --out gaps.csv
```
The sweep driver is an Ergo main: STATIC parameter table (DATA),
one kernel launch per matvec, host loop over grid points. The engine's
JSON oracles regenerate per stage via the existing Python drivers.
