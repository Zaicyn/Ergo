# Stage 3b: batch sweep end-to-end on GPU — validation

Program: `stage3_gpu.ergo` (generator v2, `gen_ergo_stage3.py`).
Binaries: `stage3_cpu` (default target), `stage3_gpu` (`--target spirv`,
Vulkan on RTX 2060, VK_EXT_shader_atomic_float supported).

## Restructuring that made extraction work (compiler facts, ir_gpu.py)

1. `extract_kernels` "scans main_body" — SUBROUTINE loops are never
   extracted, so the matvec is inlined at both call sites.
2. WHILE loops are not traversed — convergence loops became fixed-count
   `DO K = 1, KMAX` with an **idempotent fixed point** (once converged,
   extra iterations leave the vector unchanged) plus a CONV flag
   recording first-convergence iteration. KMAX1 = 2500, KMAX2 = 3000.
3. Warm starts dropped; every point cold-seeded deterministically
   (independent points for the INJECTIVE batch map).
4. Dot/norm written as explicit accumulator loops (REDUCTION → SPIR-V);
   DOT_PRODUCT/NORM2 intrinsics deliberately unused.

## Kernel report (`--kernel-report`)

- **16 kernels extracted**: seed, initial norms/normalizes, ground-phase
  matvec + Rayleigh reduction + norm reduction + normalize, GS copy,
  deflated-phase matvec + deflate reduction + Rayleigh reduction + norm
  reduction + normalize.
- **3 rejected (organizational, expected)**: the DO P batch loop and the
  two DO K convergence loops ("nested loop" — the pass recursed into
  their bodies as designed).

## Validation (all 21 rows)

| comparison | worst |ΔE0| | worst |Δgap| | tolerance | verdict |
|---|---|---|---|
| stage3-CPU vs stage2 (warm-start oracle) | 0.00e+00 | 0.00e+00 | 1e-6 | PASS (bitwise at print precision) |
| stage3-GPU vs stage3-CPU | 0.00e+00 | 0.00e+00 | 1e-5 | PASS (bitwise at print precision — no f64 rounding-order divergence observed at N=6561) |

Named points: J=0.0 → E0 = 0, gap = 0.5 exactly; J=1.0 → E0 =
−2.8591343125, gap = 0.120548 — both paths, exact. All CONV flags = 1
(every point converged before its KMAX; actual first-convergence
iterations are columns 4–5 of the output, e.g. 673/230 at J=2.0).

## Wall times (21-point sweep) and honest cost breakdown

| path | wall | note |
|---|---|---|
| stage2 CPU (warm starts + early exit) | 0.235 s | reference |
| stage3 CPU (cold + fixed KMAX) | 12.9 s | 55× stage2 — the price of extraction-legal structure: cold seeds (~670 vs ~50 iters) AND no early exit |
| stage3 GPU (SPIR-V) | 28.7 s | 2.2× slower than stage3-CPU |

GPU slower, as predicted at this size — measured, not guessed: the sweep
executes ~115 000 iterations × 4–5 kernel launches each ≈ 0.5 M launches
on 6561-element vectors; wall 28.7 s vs user 6.0 s + sys 3.9 s shows the
bulk is launch/fence overhead, not device compute. Per-iteration fenced
syncs at 6561 elements are the culprit. The GPU path's value at this
stage is the *validated end-to-end extraction* (16 kernels, bitwise
agreement), not speed; it should turn profitable when vectors are large
enough to amortize launches (N ≥ 12, 531 k elements, est. ~80× more work
per launch) or with multi-point batching on device.

## Files

`gen_ergo_stage3.py`, `stage3_gpu.ergo`, `stage3_cpu`, `stage3_gpu`,
`stage3_cpu.out`, `stage3_gpu.out`, `stage3_gpu.spvasm`, this file.
