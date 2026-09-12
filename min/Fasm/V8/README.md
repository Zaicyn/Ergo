# V8 three-way assembly comparison

Slice: `compute_invariant` + `viviani_normal`, extracted verbatim from
`Testing/V8/aizawa.cuh` into `v8_slice.c` (CUDA decoration stubbed only).
Flags: `-O3 -march=x86-64-v3 -ffp-contract=fast -fno-math-errno -std=c11`.

## Runtime outputs (oracle: `v8_driver.c`, fixed inputs)

- `v8_driver.gcc` (glibc, dynamic) vs `v8_driver.musl` (musl, static):
  **byte-identical** (`out.gcc.txt` == `out.musl.txt`).
- `v8_invariant` (FASM, no libc): invariant line **matches** exactly.

## Assembly findings

- GCC vs musl `.s`: kernel instructions **identical** (modulo assembler
  label numbering). The 145-line vs 682-line gap is all musl `math.h`
  static-inline FP-classify helpers (`__islessf`, `__isgreater`, ...),
  not kernel codegen. musl dragged them in; glibc didn't.
- `viviani_normal` (both): fused `sincosf@PLT` call, FMA (`vfnmadd`/
  `vfmsub`/`vfmadd`), `vsqrtss` + branchless divide guard. Takeaway:
  the float kernel is **libm-bound** — bare FASM can't take it until it
  has an owned sin/cos (same lesson as `ergo_math_kernels.h`).
- `compute_invariant` (both): GCC auto-vectorized to AVX2 (`vpxor ymm`)
  with scalar head/tail. The FASM port (`v8_invariant.asm`) is scalar —
  matching SIMD by hand is the open next step (the V22 hand-SSE story
  all over again).

## Sizes

- FASM static, no-libc binary: **621 bytes**.
- gcc/glibc driver: 16024 bytes. musl static driver: 39696 bytes.

## Files

- `v8_slice.c` / `v8_driver.c` — C slice + oracle driver
- `v8_slice.gcc.s` / `v8_slice.musl.s` — emitted assembly
  (`-fkeep-inline-functions` so bodies are visible)
- `v8_invariant.asm` / `v8_invariant` — FASM source + assembled binary
- `out.{gcc,musl,fasm}.txt` — captured outputs
