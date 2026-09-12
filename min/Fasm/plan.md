# Fasm experiment — rough draft

Goal: find out whether a small, static, no-libc path (Fasm) can carry
Ergo-style kernels that currently go through GCC/glibc/musl.

This is a large experiment. This file is the placeholder for the
concept only — no emitter design, no ABI specifics yet.

## Why these kernels

- `Testing/V8_bounded/` — bounded slab/pool allocator tests. Mostly a
  GPU story (CUDA kernels + host harness). Fasm-relevant slice is
  small: the host-side harness logic only, not the device kernels.
- `Testing/V22/` — CPU geometry residual, hand-SSE, strict-IEEE flags
  (`-O3 -march=native -ffp-contract=fast`, no `-ffast-math`). This is
  the natural first Fasm candidate: fixed-size math, no allocation in
  the hot path, determinism-sensitive.
- V22 has a known bug. Deferred — get clean baselines first, debug the
  port against the buggy reference rather than fixing it here.

The ~30 allocator variants across `Testing/` (V8/V9/V16/GEO/...) stay
out of scope until one small kernel survives the full path below.

## Step 1 — musl baselines (reference outputs)

Build and run the small V8-bounded host pieces and the V22 drivers
under `musl-gcc`, capture outputs/hashes:

- V22: `v22_compare.c` / `v22_parallel.c` against `squaragon_v2*.h`
- V8_bounded: host-side only (no CUDA device code in this step)

Record: stdout, exit code, any output hash, compiler flags used.
These become the oracle the Fasm builds are diffed against.

Note: `fasm` is not installed on this machine yet; musl-gcc is
(`musl-gcc` present, `fasm: command not found` at time of writing).

## Step 2 — Fasm rework sketch (concept only)

- CPU-only, static, no-libc: own startup, BSS arena, Linux syscalls
  for `write`/`exit`. No `printf`, no `malloc`, no libm in the hot
  path (owned math kernels, same rule as the current
  `--libm-fallback=off` path).
- Structured control flow only (`IF/DO/SELECT/CYCLE/EXIT` level) —
  maps 1:1 to labels/jumps, same as the existing `jit_x86` approach
  but as readable Fasm text.
- `vk_host.c`, SPIR-V/NVVM, and all GPU paths stay on GCC/nvcc.
  Fasm never touches them in this experiment.

## Non-goals (for now)

- No full-sim port, no Vulkan in Fasm, no float-format rework.
- No V22 bugfix here — just characterize it.
- No emitter implementation until musl baselines are captured.

## Next steps when ready

1. Pick the single smallest V22 residual entry point.
2. Capture its musl output + hash.
3. Hand-write (or later generate) the equivalent Fasm kernel.
4. Diff. Decide whether a second kernel is worth it.
