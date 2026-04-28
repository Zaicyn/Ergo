# Ergo GPU Roadmap — Design Specification

*Draft v0.1 — 2026-04-23*

## Overview

Ergo compiles to C99 via gcc for CPU execution. This document defines the path to
GPU execution via NVVM IR and libNVVM, producing PTX that runs on NVIDIA hardware.

The core principle is unchanged: **the compiler lowers what you wrote.** The GPU
backend does not introduce hidden allocation, implicit synchronization, or
evaluation reordering. What changes is the *target*, not the *contract*.

---

## Why NVVM IR

Three options exist for GPU compilation:

| Path | Control | Effort | Performance |
|------|---------|--------|-------------|
| CUDA C emission (like current C99 path) | Medium | Low | Medium — nvcc makes its own decisions |
| NVVM IR + libNVVM | Full | Medium | Full — same backend as nvcc, but we control the IR |
| Raw PTX assembly | Total | Very high | Marginal gains over NVVM |

**NVVM IR is the right target.** It is LLVM IR constrained to the NVVM dialect.
libNVVM compiles it to PTX, which the CUDA driver loads. We get NVIDIA's register
allocator, instruction scheduler, and TMA support without writing an assembler.

NVVM IR is also what nvcc uses internally. We're just cutting out the C++ parser
and feeding the optimizer directly.

---

## Architecture

```
Ergo source
  |
  v
Lexer -> Parser -> Checker        (unchanged — all validation happens here)
  |
  v
Ergo IR                           (NEW — typed SSA, shape/alloc as node fields)
  |
  +---> C99 codegen -> gcc        (existing CPU path)
  |
  +---> NVVM IR codegen           (new GPU path)
  |       |
  |       v
  |     libNVVM -> PTX -> cubin
  |       |
  |       v
  |     CUDA Driver API           (load module, launch kernel, manage memory)
  |
  +---> Node graph compilation    (already emitting typed SSA)
```

The Ergo IR is the pivot point. It serves all three backends. The checker
guarantees that any program reaching the IR is type-safe, shape-consistent,
bounds-valid, and allocation-correct. Backends do not need to re-verify safety.

---

## Mapping Ergo to GPU Concepts

### Kernel Extraction

Not all Ergo code runs on the GPU. The compiler must identify **kernel regions** —
sections of code that are data-parallel and free of host-side effects.

The primary kernel candidate is the DO loop over independent iterations:

```
! This loop is kernel-extractable:
!   - no cross-iteration dependency
!   - no I/O inside the loop body
!   - all arrays are pre-allocated with known shape

DO i = 1, NPARTICLES
  fx(i) := mass(i) * ax(i)
  vy(i) := vy(i) + fx(i) * DT
  py(i) := py(i) + vy(i) * DT
ENDDO
```

**Extraction rules:**
1. Loop body contains only assignments to arrays indexed by the loop variable.
2. No WRITE, PRINT, FLUSH, STOP inside the loop.
3. No ALLOCATE/DEALLOCATE inside the loop.
4. No cross-iteration read-write aliasing (array writes at index `i` only,
   reads from any index are fine — the checker already tracks this).
5. All arrays have compile-time known shape or PARAMETER-derived shape.

Loops that pass these checks can be lowered to GPU kernels. Loops that fail
remain on the CPU path. No silent fallback — the compiler reports why a loop
was not extracted.

### Future: Explicit Kernel Annotation

For cases where the compiler cannot prove independence, or where the programmer
wants explicit control:

```
!$ERGO KERNEL
DO i = 1, NPARTICLES
  ...
ENDDO
```

The `!$ERGO KERNEL` directive asserts that the programmer guarantees independence.
The compiler trusts this but still validates type/shape/bounds. This mirrors
OpenMP's `!$OMP PARALLEL DO` — the programmer owns the correctness of the
parallelism claim, the compiler owns everything else.

---

## Memory Model

### Host-Device Mapping

| Ergo concept | GPU mapping | Notes |
|-------------|-------------|-------|
| PARAMETER | `__constant__` memory | Read-only, cached, broadcast to all threads |
| STATIC array | Device global memory | Persistent across kernel launches |
| Local scalar | Register | Per-thread, fastest |
| Local array (small, fixed) | Register or local memory | Compiler decides based on size |
| ALLOCATABLE array | Device global memory | Explicit cudaMalloc/cudaFree |

**Key rule:** Ergo's "no hidden allocation" extends to the GPU. Every device
memory allocation is visible in the source as an ALLOCATE statement. The compiler
never silently allocates device memory.

### Transfer Semantics

Data transfer between host and device must be explicit. The compiler does not
auto-migrate arrays.

```
!$ERGO DEVICE(px, py, pz, vx, vy, vz, mass)   ! allocate + copy to device
!$ERGO KERNEL
DO i = 1, N
  vx(i) := vx(i) + fx(i) * DT
ENDDO
!$ERGO HOST(px, py, pz)                         ! copy back to host
```

This is verbose by design. Hidden transfers are the #1 source of GPU performance
bugs. Making them visible is consistent with the Performance Constitution.

---

## NVVM IR Emission

### Ergo IR to NVVM IR Mapping

| Ergo IR node | NVVM IR |
|-------------|---------|
| REAL scalar | `double` |
| INTEGER scalar | `i32` |
| LOGICAL scalar | `i1` |
| Assignment | `store` |
| Variable read | `load` |
| Binary op (+, -, *, /) | `fadd`, `fsub`, `fmul`, `fdiv` (double) |
| Integer op | `add`, `sub`, `mul`, `sdiv` |
| Comparison | `fcmp`, `icmp` |
| SIN, COS, EXP, ... | `@llvm.nvvm.sin.d`, `@llvm.nvvm.cos.d`, ... |
| SQRT | `@llvm.nvvm.sqrt.rn.d` |
| ABS | `@llvm.fabs.f64` |
| CLAMP | `@llvm.minnum.f64` + `@llvm.maxnum.f64` (branchless) |
| Array subscript A(i) | `getelementptr` + `load`/`store` |
| PARAMETER | `@constant` global with `addrspace(4)` |
| STATIC array | `@global` with `addrspace(1)` |
| DO loop (kernel) | Thread grid: `tid = threadIdx.x + blockIdx.x * blockDim.x` |
| IF/ELSE | `br` + basic blocks (divergent, but NVVM handles reconvergence) |

### Kernel Function Signature

A kernel extracted from:
```
DO i = 1, N
  px(i) := px(i) + vx(i) * DT
ENDDO
```

Becomes:
```llvm
define void @_ergo_kernel_0(
    double* %px,        ; addrspace(1) device global
    double* %vx,        ; addrspace(1) device global
    double %DT,         ; passed by value (PARAMETER -> constant)
    i32 %N              ; array bound
) #0 {
entry:
    ; thread index
    %tid.x = call i32 @llvm.nvvm.read.ptx.sreg.tid.x()
    %bid.x = call i32 @llvm.nvvm.read.ptx.sreg.ctaid.x()
    %bsz.x = call i32 @llvm.nvvm.read.ptx.sreg.ntid.x()
    %gid = add i32 %tid.x, mul(i32 %bid.x, i32 %bsz.x)

    ; bounds check (Ergo 1-based -> 0-based)
    %i = add i32 %gid, 1
    %in_bounds = icmp sle i32 %i, %N
    br i1 %in_bounds, label %body, label %exit

body:
    %idx = sub i32 %i, 1                    ; 0-based index
    %px_ptr = getelementptr double, double* %px, i32 %idx
    %vx_ptr = getelementptr double, double* %vx, i32 %idx
    %px_val = load double, double* %px_ptr
    %vx_val = load double, double* %vx_ptr
    %delta = fmul double %vx_val, %DT
    %new_px = fadd double %px_val, %delta
    store double %new_px, double* %px_ptr
    br label %exit

exit:
    ret void
}

!nvvm.annotations = !{!0}
!0 = !{void (double*, double*, double, i32)* @_ergo_kernel_0, !"kernel", i32 1}
```

### NVVM Intrinsics for Ergo Intrinsics

| Ergo | NVVM intrinsic | Notes |
|------|----------------|-------|
| SIN(x) | `@llvm.nvvm.sin.d` | Device-optimized, ~2 ULP |
| COS(x) | `@llvm.nvvm.cos.d` | |
| EXP(x) | `@llvm.nvvm.ex2.approx.d` | Fast path, or `@llvm.exp.f64` for IEEE |
| LOG(x) | `@llvm.nvvm.lg2.approx.d` | Fast path |
| LOG10(x) | `@llvm.log10.f64` | |
| SQRT(x) | `@llvm.nvvm.sqrt.rn.d` | Round-to-nearest |
| ABS(x) | `@llvm.fabs.f64` | |
| MAX(a,b) | `@llvm.maxnum.f64` | NaN-safe |
| MIN(a,b) | `@llvm.minnum.f64` | NaN-safe |
| MOD(a,b) | `frem double` | |
| ISHFT | `shl` / `lshr` | Already lowered in Ergo |
| IEOR | `xor` | |
| IAND | `and` | |

**IEEE vs fast-math:** When `--fast-math` is active, use the `.approx` variants.
When not, use the IEEE-correct versions. The flag propagates from CLI to IR to
NVVM metadata.

---

## Data Layout: Structure of Arrays

GPU memory coalescing requires contiguous access per field. Ergo's existing
array model naturally supports this:

```
! Already SoA in current Ergo — each array is contiguous
REAL :: px(N), py(N), pz(N)
REAL :: vx(N), vy(N), vz(N)
REAL :: mass(N)
```

This is correct and performant. Each `px`, `py`, `pz` is a contiguous `double*`
in device memory. Threads accessing `px(i)` with consecutive `i` values get
coalesced reads.

### Future: LAYOUT Declaration

For large particle systems, a semantic grouping is useful for readability and
for the compiler to reason about related arrays:

```
LAYOUT SOA :: particles(NMAX)
  REAL :: x, y, z
  REAL :: vx, vy, vz
  REAL :: mass
  INTEGER :: type
ENDLAYOUT
```

This would lower to separate contiguous arrays (SoA) but carry the semantic
grouping. The compiler could then:
- Auto-generate transfer directives for the whole layout.
- Verify that kernel reads/writes within a layout are coalesced.
- Enable layout-aware kernel fusion (all fields of a layout travel together).

This is syntactic sugar over what's already expressible. It does not change
the memory model. Deferred to Phase 3.

---

## Kernel Fusion

The single biggest GPU performance win for physics engines. Without fusion:

```
! Kernel 1: compute forces
DO i = 1, N
  fx(i) := mass(i) * ax(i)
ENDDO

! Kernel 2: integrate velocity
DO i = 1, N
  vx(i) := vx(i) + fx(i) * DT
ENDDO

! Kernel 3: integrate position
DO i = 1, N
  px(i) := px(i) + vx(i) * DT
ENDDO
```

Three separate kernel launches. Each one writes to global memory, the next one
reads it back. ~20ms overhead per launch boundary.

**With fusion** (compiler detects the pattern):

```
! Single fused kernel: force + velocity + position
DO i = 1, N
  fx_local := mass(i) * ax(i)        ! stays in register
  vx(i) := vx(i) + fx_local * DT     ! one global read + write
  px(i) := px(i) + vx(i) * DT        ! one global read + write
ENDDO
```

One kernel launch. Intermediate values stay in registers. ~11ms instead of ~20ms.

### Fusion Rules

The IR must support loop fusion as a transformation pass:

1. **Adjacent loops** over the same range with the same index variable are fusion candidates.
2. Fusion is legal if the second loop's reads at index `i` only depend on the first
   loop's writes at index `i` (no cross-lane dependency).
3. Intermediate arrays that are written in loop 1 and read in loop 2 at the same
   index are **promoted to registers** in the fused kernel (eliminated from global memory).
4. The compiler reports fusion decisions: "Fused loops at lines 42-56 into kernel_0".

This is the primary motivation for the Ergo IR layer. You cannot do fusion by
manipulating C strings. You need structured loop nests with explicit data flow.

---

## Runtime: CUDA Driver API

The GPU runtime is minimal. Ergo does not link against the CUDA Runtime API
(`cudart`). Instead, it uses the **CUDA Driver API** directly:

```c
// Generated host code (C99, links against libcuda + libnvvm)

#include <cuda.h>
#include <nvvm.h>

// 1. Initialize
cuInit(0);
CUdevice dev; cuDeviceGet(&dev, 0);
CUcontext ctx; cuCtxCreate(&ctx, 0, dev);

// 2. Compile NVVM IR -> PTX (at build time or JIT)
nvvmProgram prog;
nvvmCreateProgram(&prog);
nvvmAddModuleToProgram(prog, nvvm_ir, nvvm_ir_size, "kernel.ll");
nvvmCompileProgram(prog, 0, NULL);
// extract PTX...

// 3. Load and launch
CUmodule mod; cuModuleLoadData(&mod, ptx);
CUfunction kern; cuModuleGetFunction(&kern, mod, "_ergo_kernel_0");

void *args[] = { &d_px, &d_vx, &DT, &N };
cuLaunchKernel(kern,
    (N + 255) / 256, 1, 1,   // grid
    256, 1, 1,                 // block
    0, NULL,                   // shared mem, stream
    args, NULL);

cuCtxSynchronize();
```

The host-side code is generated by the Ergo C99 codegen, extended with CUDA
Driver API calls. This is just C with library calls — no CUDA syntax, no nvcc
dependency at runtime.

### Build Dependencies

| Component | Purpose | When |
|-----------|---------|------|
| libNVVM | Compile NVVM IR to PTX | Build time (or JIT) |
| CUDA Driver (libcuda) | Load PTX, manage device memory, launch kernels | Runtime |
| gcc | Compile host-side C99 | Build time |

No nvcc. No CUDA Runtime API. No C++ anywhere. Pure C99 host code + NVVM IR
for device code.

---

## --fast-math on GPU

The `--fast-math` flag already exists in the CLI. On GPU:

| Mode | IEEE behavior | NVVM metadata | Intrinsics |
|------|---------------|---------------|------------|
| Default (IEEE) | Exact, NaN-safe | `nsz` not set | `@llvm.nvvm.sqrt.rn.d` |
| `--fast-math` | Approximate, reassociable | `fast` flag on FP ops | `@llvm.nvvm.sqrt.approx.d` |

The same flag, the same semantics, different backend. The Performance
Constitution applies identically: IEEE by default, fast-math opt-in.

---

## Synchronization

Ergo's "no hidden state" rule means synchronization is explicit:

```
!$ERGO BARRIER          ! maps to __syncthreads() / nvvm.barrier0
```

Within a kernel, threads execute independently. Cross-thread communication
requires explicit barriers or atomics.

### Atomics

For operations like collision response or reduction:

```
!$ERGO ATOMIC ADD total_energy, local_e
```

Maps to `atomicrmw fadd` in NVVM IR. The compiler verifies that atomic targets
are in device global memory (not registers or PARAMETER).

Atomics are the only place where determinism may be relaxed (FP atomic add is
not associative). The compiler warns when `--fast-math` is not active and
atomic FP operations are used.

---

## Implementation Phases

### Phase 1: Ergo IR -- COMPLETE (2026-04-23)

The IR layer is built and is now the default compilation path. All four test
programs (test_first, sq2core, buc_membrane_unit, buc_colony) produce identical
output through the IR path. The old AST-to-C codegen is preserved as fallback.

**What exists (`mcl/ir.py`, `mcl/ir_builder.py`, `mcl/ir_codegen.py`):**
- `IRModule` with globals, functions, main body, source file tracking.
- `IRVar` with type, storage class (LOCAL/STATIC/PARAMETER/ALLOCATABLE), shape.
- `IRInst` — typed SSA instruction with 37 operations: arithmetic, relational,
  logical, bitwise, math intrinsics, conversion, array load/store, alloc/free,
  call, I/O, control flow.
- `IRBlock` — basic block (sequence of instructions, no internal branches).
- `IRIf`, `IRLoop`, `IRSelect` — **structured** control flow, not a flat CFG.
  Loop nests are preserved as first-class constructs for fusion analysis.
- `IRBuilder` — AST-to-IR lowering. Expressions decompose to SSA temporaries.
  1-based array indexing lowered to 0-based here. Fortran return-variable idiom handled.
- `IRCodeGen` — C99 backend consuming IRModule. Auto-declares SSA temporaries.
  Emits `#line` directives from IR source lines.
- `dump_module()` — human-readable IR text dump for debugging.

**Pipeline is now:** `Source -> Lexer -> Parser -> Checker -> IRBuilder -> IRCodeGen -> gcc`

**What this means for GPU work:**
- The NVVM IR codegen (Phase 2) consumes the same `IRModule`.
- `IRLoop` nodes are the kernel extraction candidates — they carry var, bounds,
  and a structured body. No need to reverse-engineer loop structure from a flat CFG.
- `IRVar.storage` already distinguishes PARAMETER (-> `__constant__`),
  STATIC (-> device global), ALLOCATABLE (-> `cuMemAlloc`).
- `IRInst.line` propagates to NVVM debug info for cuda-gdb.

**Do NOT rebuild any of this. Start from Phase 2.**

### Phase 2: Kernel Extraction

- Identify extractable DO loops in the IR.
- Annotate extracted loops with thread grid dimensions.
- Generate host-side launch code (CUDA Driver API calls in C99).
- Generate device-side NVVM IR for extracted kernels.
- Compile NVVM IR via libNVVM at build time.
- Test: single-kernel extraction for a simple particle update.

### Phase 3: Memory Management

- ALLOCATE on device → `cuMemAlloc`.
- DEALLOCATE on device → `cuMemFree`.
- Explicit transfer directives (`!$ERGO DEVICE`, `!$ERGO HOST`).
- PARAMETER → constant memory.
- STATIC → device global.
- Test: membrane unit test running on GPU.

### Phase 4: Kernel Fusion

- IR pass to identify adjacent fusable loops.
- Register promotion for intermediate arrays.
- Fused kernel generation.
- Fusion report (which loops were fused, why others were not).
- Test: three-loop physics step fused to single kernel.

### Phase 5: Advanced

- LAYOUT SOA declarations.
- Shared memory tiling for stencil operations.
- Multi-GPU support (device selection, peer-to-peer).
- Warp-level primitives (shuffle, vote) via intrinsics.
- Profiling integration (nvprof annotations from Ergo source lines).

---

## What Ergo Already Has That Maps to GPU

| Feature | GPU benefit |
|---------|------------|
| No hidden allocation | Device memory is always explicit |
| No implicit temporaries | No surprise global memory traffic |
| No evaluation reordering (default) | Bitwise reproducible across CPU and GPU |
| `--fast-math` opt-in | Controlled use of GPU approximate intrinsics |
| PARAMETER constants | Natural `__constant__` memory candidates |
| STATIC arrays | Natural device global memory candidates |
| Bounds checking (compile-time) | No runtime bounds checks needed in kernels |
| 1-based indexing | Thread ID + 1, bounds check against N — simple |
| Node graph (typed SSA) | Prototype for the IR that feeds NVVM emission |
| `#line` directives | Source-mapped GPU debugging (cuda-gdb) |
| CLAMP branchless | Already maps to `minnum`/`maxnum` — no warp divergence |

---

## Design Principles

1. **Same contract, different target.** The Performance Constitution applies on GPU.
   No hidden allocation. No implicit transfer. No silent fallback to CPU.

2. **Explicit parallelism.** The compiler identifies kernel candidates, but the
   programmer can override or annotate. No "auto-parallel magic."

3. **Fusion is a compiler responsibility.** The programmer writes clear, separated
   loops. The compiler fuses them when it can prove safety. The programmer is
   told what happened.

4. **One source, two targets.** The same `.ergo` file compiles to CPU (gcc) or
   GPU (NVVM + CUDA Driver). The `--gpu` flag selects the target. Non-extractable
   code stays on the host automatically.

5. **No nvcc, no C++, no runtime API.** Pure C99 host code. NVVM IR device code.
   libNVVM at build time. CUDA Driver API at runtime. The dependency chain is
   minimal and auditable.
