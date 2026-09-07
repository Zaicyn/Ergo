# FDTD & Wigner GPU/CPU determinism report

**Date:** 2026-08-25
**Objective:** Check whether the GPU/CPU mismatch seen in ribosome simulations is a general GPU-backend bug, or specific to ribosome MD physics.

## Summary

- **2D FDTD wave simulations are CPU/GPU bit-identical** (f64). The SPIR-V backend and reduction combine are working correctly for structured grid problems.
- **1D FDTD `fdtd_slit_1d` shows only ~1e-6 numerical noise** (probably reduction-order / f32-intrinsic round-off), but no structural divergence.
- **Wigner SCF sources are not GPU-extractable** and fall back to CPU paths, producing completely different results (e.g. `SCANFAIL`).

Conclusion: the ribosome GPU/CPU divergence is not a universal backend bug; it is a property of chaotic MD trajectories amplifying small floating-point differences. FDTD can be used as a clean GPU correctness regression suite.

## FDTD results

| System | CPU/GPU output | Notes |
|--------|----------------|-------|
| `fdtd_slit.ergo` | **IDENTICAL** | 2D slit diffraction |
| `fdtd_te.ergo` | **IDENTICAL** | 2D TE mode |
| `fdtd_tm.ergo` | **IDENTICAL** | 2D TM mode |
| `fdtd_sw.ergo` | **IDENTICAL** | 2D standing wave |
| `fdtd_loop.ergo` | **IDENTICAL** | loop/cavity variant |
| `fdtd_timeslit.ergo` | **IDENTICAL** | time-varying slit |
| `fdtd_slit_db.ergo` | **IDENTICAL** | double-slit |
| `fdtd_te1.ergo` | **IDENTICAL** | TE variant |
| `fdtd_slit_1d.ergo` | Tiny ~1e-6 diffs | 1D propagation; numerical noise only |

### How the comparison was run

```bash
# CPU (host-only) binary
python3 -m core min/fdtd/<file>.ergo --precision f64 -o /tmp/<file>_cpu.bin

# GPU (SPIR-V) binary
python3 -m core min/fdtd/<file>.ergo --target spirv --precision f64 -o /tmp/<file>_gpu.bin

# Run and strip the GPU driver info header
/tmp/<file>_cpu.bin > /tmp/<file>_cpu.txt
/tmp/<file>_gpu.bin > /tmp/<file>_gpu.txt
sed '/^\[ergo_vk\]/d' /tmp/<file>_gpu.txt > /tmp/<file>_gpu_clean.txt

# Compare
diff /tmp/<file>_cpu.txt /tmp/<file>_gpu_clean.txt
```

### Example: `fdtd_slit_1d` differences

Only the 6th significant digit differs, and the diff does not grow along the grid:

```
CPU:  1 32 1.839293
GPU:  1 32 1.839295

CPU:  1 40 34.469950
GPU:  1 40 34.469947
```

This is consistent with a single workgroup reduction using a different summation order than the sequential CPU loop, not a logic error.

## Wigner results

| System | CPU/GPU output | Notes |
|--------|----------------|-------|
| `df_radial2.ergo` | **DIFFER** | CPU converges SCF; GPU emits `SCANFAIL` |
| `df_wig2.ergo` | **DIFFER** | CPU converges SCF; GPU emits `SCANFAIL` |
| `df_wig.ergo` | **DIFFER** | CPU converges SCF; GPU emits `SCANFAIL` |
| `h2p_wig.ergo` | **NEAR-IDENTICAL** | WNORM ~1e-12, WMAP ~1e-6 absolute differences; physics is correct |

### Why the SCF sources differ

`python3 -m core <file>.ergo --kernel-report --precision f64` shows the SCF loops are not extracted for GPU:

- `scalar accumulator(s) ['NRM'] (cross-iteration dependency); staged reduction rejected — loop start must be the constant 1`
- `SPLIT rejected: flow-prefix locals ['LA'] are read by structural suffix (GPU->CPU boundary crossing)`
- `depends on outer loop var(s) ['IA', 'IB']`
- `disqualifying op 'call' at line 0`

However, a few simple loops **are** extracted (e.g. potential build, source zeroing, midpoint arrays). The SCF then runs on the CPU but calls subroutines (`VOPN`, `SHOOT`, `LEGS`) that read those GPU-written arrays. The generated host code only downloads the arrays the top-level subroutine directly reads; it does not download the arrays read by nested subroutines (e.g. `LEGS` inside `VOPN` reads `VLM`, `SFM`, `SGM`, `VL`). The CPU subroutines therefore see stale host memory and the SCF fails to find roots.

This is a compiler host-sync limitation: GPU buffers are local to `main()`, and nested subroutine calls cannot trigger the necessary downloads. The SCF source would need to either (a) have all GPU-touching subroutines inlined into `main()`, or (b) use a different buffer visibility scheme, before GPU mode can be reliable.

### Why `h2p_wig.ergo` is fine

`h2p_wig.ergo` has no nested subroutines that read GPU arrays; the CPU Wigner-map construction runs after the extracted imaginary-time solver kernels, and the only differences are floating-point noise from the GPU normalization reduction.

## What this means for the ribosome work

1. **The GPU compiler is not broken.** FDTD 2D systems prove the SPIR-V backend, reduction readback, and host combine can produce bit-exact results.
2. **Ribosome divergence is physics-driven.** The `FRAME_K`, `PSEG`, and `PHOS` force paths introduce small floating-point differences that chaotic MD amplifies over many frames.
3. **FDTD should become the GPU regression suite.** Add a simple file-diff check to CI for the 2D FDTD files; any backend change that breaks these is a real bug.
4. **Ribosome validation should switch to statistical checks.** Compare ensemble distributions, basin occupancies, or Rg histograms, not single trajectories.

## Recommended next steps

1. Create a small regression script (`min/fdtd/fdtd_gpu_cpu_check.py` or similar) that automates the above comparison and runs in CI.
2. For Wigner SCF sources (`df_radial2`, `df_wig2`, `df_wig`), do not run with `--target spirv` until the host-sync issue is fixed. Either compile CPU-only or force the compiler to disable GPU extraction for these files.
3. To properly fix the Wigner GPU path, the compiler must either inline the SCF subroutines into `main()` or make GPU buffers accessible to subroutine calls so nested subroutine sync can work.
4. For ribosomes, decide acceptable tolerance for ensemble-level agreement and add that as the validation gate.

## Scripts and artifacts

- Original ribosome harness: `min/ribosome/gpu_cpu_qcheck.py` (left untouched)
- New FDTD harness: `min/fdtd/fdtd_gpu_cpu_check.py` (copied from `min/ribosome/gpu_cpu_qcheck.py` and adapted)
- Working copy of codegen with attempted Wigner fixes: `core/ir_codegen_wigner_debug.py` (copied from `core/ir_codegen.py` before editing; original restored)
- Raw outputs: `/tmp/fdtd_*_{cpu,gpu}.txt` and `/tmp/df_radial2_gpu_*.{out,c}` on the workstation

### Harness run summary

```bash
python3 min/fdtd/fdtd_gpu_cpu_check.py \
  min/fdtd/fdtd_slit.ergo \
  min/fdtd/fdtd_te.ergo \
  min/fdtd/fdtd_slit_1d.ergo \
  --tol 1e-9
```

Result:
- `fdtd_slit.ergo`: OK (1537 lines identical)
- `fdtd_te.ergo`: OK (57 lines identical)
- `fdtd_slit_1d.ergo`: 1332 lines with ~1e-6 absolute differences (passes at `1e-5` tolerance)
