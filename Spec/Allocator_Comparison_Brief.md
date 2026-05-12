# Ergo vs V8 vs V22 — Allocator Comparison Brief

## Corrections vs original brief

Three adjustments folded in pre-dispatch after implementer analysis:

1. **Framing is established by [Testing/V8_VS_V22_HEAD_TO_HEAD.md](../Testing/V8_VS_V22_HEAD_TO_HEAD.md), not invented by this brief.** That doc already
   landed on "Option 1 with native-workload framing" via the
   forklift-vs-bicycle metaphor. The Ergo row extends that approach, doesn't
   replace it. **Do not try to make Ergo look comparable to V8/V22 on
   throughput.** If three of four throughput cells in Ergo's column end up
   as "N/A — does not allocate at runtime," that is the correct result.
   The prose treatment matches the existing forklift-vs-bicycle pattern:
   honest about what each system pays vs. avoids.

2. **Pre-flight smoke test elevated from open question to blocking
   prerequisite.** "Does ALLOCATABLE actually work today?" — the original
   brief left this in Open Questions, which is too late. None of the
   shipping Ergo programs use ALLOCATABLE; the arena lowering work
   added the bump emit but didn't validate end-to-end runtime behavior
   on a real ALLOCATABLE program. **Run a 30-minute smoke test before
   any pass starts.** Write a trivial program that exercises ALLOCATE +
   array access + PRINT, compile, run, confirm it produces the expected
   output. If it doesn't work, stop and flag — the work doesn't proceed
   until ALLOCATABLE is functional or its breakage is explicitly accepted
   as out-of-scope for this brief.

3. **Pass ordering revised for early-signal and graceful-failure.**
   Original order: Pass 1 → 2 → 3 → 4. Revised order: **Pass 1 → Pass 4 →
   Pass 2 → Pass 3.** Reasoning: Pass 1 (calibration floors) is small and
   unblocks Pass 4 (unified table). Pass 4 with Ergo cells placeholdered
   as "see Pass 2/3" is shippable on its own. Pass 2 (Ergo CPU) and
   Pass 3 (Ergo GPU) fill in the placeholders. If Pass 2 hits the
   ALLOCATABLE blocker, or Pass 3 hits the cross-API GPU comparison
   limit, you still have Pass 1 + Pass 4 as a deliverable rather than a
   stalled work-in-progress.

   Pass 3 specifically: if NVIDIA driver-SASS dump for Vulkan is not
   working within an hour, **compare at SPIRV level only, document the
   API-stack mismatch as a structural limitation, and ship.** Don't
   spend days fighting Nsight Graphics for marginal returns.

## What this is

Extend the existing comparison work in [Testing/](../Testing/) to include
Ergo's allocation pattern as a third row. Two deliverables:

**(A) Assembly-level structural comparison.** Disassemble Ergo's lowered
allocation path (CPU and GPU) and compare instruction-by-instruction against
V8's SASS and V22's SSE/x86. The question is "what does each system *do*
at the hardware level when it allocates."

**(B) Performance comparison.** Measure Ergo against V8 and V22 on
matched workloads. Calibrate with a "do nothing" baseline so the numbers
are comparable across systems.

The existing benchmarks in [Testing/V8/](../Testing/V8/) and
[Testing/V22/](../Testing/V22/) are already done. This brief is about
*adding the third column to those tables* — not re-doing the V8/V22 work.

## Important framing before you start

**Ergo doesn't have a runtime allocator in the V8/V22 sense.** This is the
first thing the implementer needs to internalize, because it shapes what
"comparison" can honestly mean.

- **CPU side ([mcl/codegen.py:519](../mcl/codegen.py#L519), [mcl/ir_codegen.py:1421](../mcl/ir_codegen.py#L1421)):**
  `ALLOCATABLE` arrays currently lower to a single `malloc()` call at the
  `ALLOCATE` statement. **This is a known regression from the spec's
  no-hidden-allocation constitution and will be replaced with a STATIC-backed
  arena bump allocator after this comparison work completes.** See note below
  on two-stage measurement. `STATIC` arrays are file-scope and never call any
  allocator — they're BSS-resident, addressed RIP-relative.
- **GPU side ([mcl/runtime/vk_host.c:900,912](../mcl/runtime/vk_host.c#L900)):**
  each declared array gets one `vkCreateBuffer` + `vkAllocateMemory` at
  init. After init, the GPU does no allocation. The "allocator" is a
  fixed table of buffer pointers.

Compare this to V8 and V22:
- **V8** is a *runtime* GPU allocator. Lanes request slots concurrently;
  the allocator services 65M concurrent requests per second.
- **V22** is a CPU geometric primitive that includes an allocator
  (`SQ2FAL`); its 14-instruction fast path computes a slot from a
  scatter LUT, not just retrieves a pre-allocated pointer.

**The honest comparison is therefore three-way:**

| | Ergo (current) | V22 | V8 |
|---|---|---|---|
| Pattern | Allocate-once-at-startup, static lookup at runtime | Runtime CPU allocator, lattice-aligned slots | Runtime GPU allocator, warp-cooperative |
| Per-alloc cost | ~0 (no runtime allocation) | ~14 instructions (SQ2FAL fast path) | ~10-30 SASS ops/lane amortized |
| Throughput | N/A (no allocations after startup) | 469 M/s on 6-core CPU | 1.9 G/s on 30K GPU lanes |

This is not a flaw in Ergo. It's a different design point. The interesting
result is *quantifying the difference* so future decisions about whether
Ergo should grow runtime allocation are grounded.

## Two-stage measurement plan

**Stage 1 (this brief): measure Ergo as-is, including the malloc-backed
ALLOCATE path.**

The malloc in [mcl/codegen.py:519](../mcl/codegen.py#L519) and
[mcl/ir_codegen.py:1421](../mcl/ir_codegen.py#L1421) is a known regression
from the spec's "no intrinsic ever allocates" rule (Part 2 of
[Spec/MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md)). It exists because
an earlier session needed ALLOCATABLE to work and reached for the obvious
primitive. No shipping Ergo program currently uses ALLOCATABLE — the
malloc path is dead code on every real workload — but the comparison
work has to measure it because the implementer's `tests/allocate_bench.ergo`
will exercise it.

Treat the malloc measurement as the **worst-case baseline**, not as
Ergo's true allocation performance. Frame it that way in the report:
"this is what Ergo costs *when ALLOCATABLE is used*, given the current
lowering. The lowering is going to be replaced; this number bounds how
much improvement the replacement should deliver."

**Stage 2 (separate brief, after stage 1 lands): re-measure with the
arena-backed lowering.**

After stage 1 produces the table, the malloc is removed and ALLOCATABLE
lowers to a STATIC-backed arena bump. The exact same `tests/allocate_bench.ergo`
gets re-measured. The delta between stage 1 and stage 2 ALLOCATE numbers
is the interesting result — it quantifies how much of the original
measurement was libc cost vs intrinsic cost.

The two-stage plan means:

1. Stage 1's "Ergo ALLOCATE" column should be labelled
   **"Ergo ALLOCATE (malloc-backed, worst case)"** in the output table.
2. The report should note that stage 2 will re-run with a different
   lowering and reference the (future) Stage 2 brief.
3. The bump-allocator floor measurement in B.1 becomes especially
   important — it predicts what Ergo's stage-2 ALLOCATE *should* hit,
   since the arena lowering is essentially a bump allocator.

A separate brief covers the lowering fix itself
([Spec/Arena_Lowering_Brief.md](Arena_Lowering_Brief.md)). It's
sequenced *after* this comparison work so the before/after numbers are
measured against the same toolchain and machine.

## Part A — Assembly-level structural comparison

### A.1 CPU side: Ergo `ALLOCATE` and STATIC access vs V22's `SQ2FAL`

**Goal:** produce a side-by-side table of x86 instructions for three
patterns:

1. **Ergo STATIC access** — what the binary does when an Ergo program
   reads/writes a STATIC array element. Reference: [Testing/](../Testing/)
   conversation already did this for `sq2core.ergo`; reuse the methodology.
2. **Ergo ALLOCATABLE allocation** — what the binary does for
   `ALLOCATE(A(N))` in Ergo source. This is currently `malloc()` (the
   known regression flagged above). Measure both the call sequence and
   the typical libc path. The measurement is the worst-case baseline; the
   stage-2 brief replaces the lowering.
3. **V22 `SQ2FAL`** — already in [Testing/asm/](../Testing/asm/) per the
   COMPILER_DETERMINISM.md doc. Reuse.

**Methodology:**

```bash
# Ergo CPU - emit C, compile to assembly, inspect
python -m mcl --emit-c tests/sq2core.ergo > /tmp/ergo_sq2.c
gcc -O3 -march=x86-64-v3 -ffp-contract=fast -fno-math-errno \
    -S -masm=intel -fno-asynchronous-unwind-tables \
    /tmp/ergo_sq2.c -o /tmp/ergo_sq2.s

# Also generate an Ergo program that uses ALLOCATE explicitly:
# write tests/allocate_bench.ergo (see A.4 below for what it should do)
python -m mcl --emit-c tests/allocate_bench.ergo > /tmp/ergo_alloc.c
gcc -O3 ... -S /tmp/ergo_alloc.c -o /tmp/ergo_alloc.s

# V22 reference (already exists)
ls Testing/asm/v22_compare.fma.s  # confirm presence
```

Build with the stage-1 `DETERMINISTIC_FLAGS` so the comparison is against
a representative shipping configuration, not against `-O0`.

**Output:** a comparison table for one canonical operation per system:

| Operation | Ergo STATIC load | Ergo ALLOCATE | V22 SQ2FAL fast-path | Notes |
|---|---|---|---|---|
| Instruction count | TBD | TBD (mostly libc) | 14 | Already known for V22 |
| Memory ops | TBD | TBD | 2 loads, 3 RMW | |
| Branches | TBD | TBD | 1 (overflow check) | |
| Indirection | TBD (expected: 0) | TBD (call+ret) | 0 (file-scope STATIC) | |
| Cycles (estimated) | TBD | TBD | ~30 | |

Then a narrative section: "what's structurally similar, what's
structurally different." The Testing/ docs already did this analysis for
V8 and V22 — match that prose style. Focus on what the *geometry* of
each instruction stream tells you about the design.

### A.2 GPU side: Ergo `STATIC` GPU access vs V8's `viviani_slab_alloc`

**Goal:** same table, but SPIRV/SASS instead of x86.

1. **Ergo GPU buffer access** — for a STATIC array used in a SPIRV
   kernel, what does the OpAccessChain+OpLoad/OpStore pattern look
   like? This is documented in the SPIRV peephole PR
   ([Spec/SPIRV_Peephole_Brief.md](SPIRV_Peephole_Brief.md))'s
   findings. Reuse `galaxy_render.spvasm` post-peephole-cleanup as
   the reference.
2. **V8 `viviani_slab_alloc` fast path** — already in
   [Testing/asm/aizawa_slab_test.sass](../Testing/asm/) per
   [Testing/V8/COMPILER_DETERMINISM.md](../Testing/V8/COMPILER_DETERMINISM.md).

**Methodology:**

```bash
# Ergo GPU — rebuild post-SPIRV-peephole
python -m mcl --target spirv --precision f32 --no-split --render \
  -N 1000000 -M 1000000 -o /tmp/galaxy_test galaxy_structured.ergo
# galaxy_test.spvasm is the canonical artifact

# V8 reference (already exists)
ls Testing/asm/aizawa_slab_test.sass
```

The comparison is at *two levels* on GPU: SPIRV (Ergo emits) and SASS
(NVIDIA driver produces). V8 only has SASS because it's CUDA. Compare
Ergo SPIRV → driver SASS against V8 source → ptxas SASS, with the
understanding that the SPIRV→SASS step is opaque (driver decides).

**Output:** comparison table for one canonical GPU operation:

| Operation | Ergo SPIRV access (post-peephole) | Ergo driver-SASS (if obtainable) | V8 SASS fast path | Notes |
|---|---|---|---|---|
| Ops to address a buffer slot | TBD | TBD | ~10-30 amortized | |
| Atomic ops in path | TBD | TBD | ATOM.E.AND.STRONG.GPU + ballot | |
| Warp-cooperative primitives | RING_PREV/NEXT, BALLOT (Ergo) | TBD | __ballot_sync, __shfl_sync | |
| Register count | TBD | TBD | 40-56 (per launch_bounds) | |
| Determinism guarantees | Bitwise (per [x86_Determinism_Audit](x86_Determinism_Audit.md)) | Driver-dependent | Bit-identical SASS across rebuilds | |

**Driver-SASS caveat:** getting SASS out of a SPIRV→Vulkan pipeline is
harder than CUDA. NVIDIA's Nsight Graphics can dump it; alternatives
include `RGA` (Radeon GPU Analyzer, despite the name it supports
Vulkan) or `vulkan_radeon`'s shader dump env vars. Pick whichever the
implementer can get working in under an hour. If neither works,
**compare at SPIRV level only and document the limitation** — the
SPIRV is what Ergo produces, the SASS is the driver's choice, and
forcing parity on the latter isn't load-bearing for the comparison.

### A.3 Narrative findings

For each side (CPU and GPU), write 2-3 paragraphs answering:

1. **What's structurally similar?** E.g., Ergo STATIC and V22's
   `BINGEO[]` are both file-scope arrays addressed RIP-relative.
2. **What's structurally different?** E.g., Ergo's allocation happens
   at startup once; V22's `SQ2FAL` happens per-request.
3. **What's the determinism story?** Ergo's stage-3 contract vs V22's
   `-ffp-contract=fast` recipe vs V8's bit-identical SASS.

Don't moralize — just describe. The reader gets to draw conclusions.

### A.4 New artifact needed: `tests/allocate_bench.ergo`

To measure Ergo's `ALLOCATE` path, you need an Ergo program that
exercises it. The current test suite mostly uses STATIC. Write a small
one (~50 lines):

```ergo
! Benchmark Ergo's ALLOCATABLE path: many small ALLOCATE+DEALLOCATE
! cycles, measure how malloc-bound it is.

IMPLICIT NONE
INTEGER :: I, N
REAL, ALLOCATABLE :: A(:)

N := 1000
DO I = 1, N
  ALLOCATE(A(64))
  A(1) := REAL(I)
  DEALLOCATE(A)
ENDDO

PRINT N
```

Adjust to match Ergo's actual ALLOCATABLE syntax — verify against
[Spec/MCL_Quick_Reference.txt](MCL_Quick_Reference.txt). If
DEALLOCATE doesn't exist as a statement, drop it and just leak; the
measurement is about the allocation path, not the free path.

## Part B — Performance comparison

### B.1 Calibrate the zero point

**This is the most important step. Do it first.**

The existing V8 and V22 numbers (1.9 G/s, 469 M/s) are measured against
different baselines (`cudaMalloc` for V8, scalar fallback for V22).
Cross-allocator comparison requires a shared zero point.

**Build a "do nothing" baseline for both CPU and GPU:**

**CPU bump allocator** (~30 lines):
```c
// Testing/baseline_bump.c
#include <stdint.h>
static char _arena[1 << 30];  // 1 GB static arena
static uintptr_t _offset = 0;

void* bump_alloc(size_t sz) {
    uintptr_t p = (_offset + 15) & ~15;  // 16B align
    _offset = p + sz;
    return (void*)(_arena + p);
}
```

Measure: how many `bump_alloc(64)` calls per second, single-threaded
and 6-thread. This is the floor — any real allocator costs more.

**GPU bump allocator** (~50 lines, CUDA):
```cuda
__device__ unsigned long long _gpu_offset = 0;
__device__ char _gpu_arena[1ULL << 30];

__device__ void* gpu_bump_alloc(size_t sz) {
    unsigned long long p = atomicAdd(&_gpu_offset, sz);
    return _gpu_arena + p;
}
```

Measure: 65M concurrent `gpu_bump_alloc(64)` calls. Same shape as V8's
stress test. This is the GPU floor.

**Expected results:** CPU bump should be ~1-2 ns/call (pure increment).
GPU bump should be ~3-5 ns/call (atomic increment, dominated by atomic
contention on a single counter). The floor numbers are interesting in
their own right — they bound how much V8's geometry buys you over the
naive "one counter, atomicAdd" design.

### B.2 Ergo's place in the comparison

Three workloads, each with the same calibration:

**Workload 1: startup allocation throughput** — how fast can each
system allocate N buffers of size S at init?

| System | Setup time for N=1000, S=64KB |
|---|---|
| Ergo (vkAllocateMemory loop) | TBD (measured) |
| Ergo CPU malloc loop | TBD (measured) |
| V22 SQ2FAL × 1000 | TBD (measured) |
| V8 viviani_slab_alloc × 1000 | TBD (measured) |
| CPU bump × 1000 | TBD (measured, expected near-zero) |
| GPU bump × 1000 | TBD (measured) |

Ergo's `vkAllocateMemory` is *slow* — it's a Vulkan driver call per
allocation. Expect it to be the slowest column by orders of magnitude.
That's not Ergo being bad; it's Ergo not having an allocator. The
table makes it visible.

**Workload 2: steady-state physics performance** — how fast does the
existing `galaxy_structured.ergo` run? Already measured at 30M@60-74fps
per the `project_render_perf` memory. Re-measure with current
post-x86-determinism flags. This is the workload where Ergo's
allocate-once design pays off.

| System | Allocs/frame | Frame time | Hash-stable |
|---|---|---|---|
| Ergo current | 0 (post-startup) | TBD | Yes (per stage 1) |
| Ergo + V22-backed startup | 0 (post-startup) | TBD (should match) | Should hold |
| Ergo + V22 per-frame scratch (synthetic) | N (varies) | TBD | Should hold |

Workload 2 is the most informative comparison for the "should Ergo grow
runtime allocation as a feature" question. If per-frame V22 scratch
doesn't measurably slow the simulation, Ergo can grow the feature
cheaply. If it does, the current design is justified.

**Workload 3: V8/V22 microbench (existing)** — reproduce the existing
Testing/ measurements with current flags. No Ergo changes, just
re-validation that the V8/V22 numbers haven't drifted.

### B.3 Hardware and methodology

Same hardware as the existing Testing/ docs: Ryzen 5 3600 + RTX 2060.
Run all measurements on the same machine in one sitting to control for
thermal/scheduler variance.

For each measurement:
- 5 runs, take median
- Discard first run (cold cache)
- Record wall-clock and per-op (ns/alloc) where applicable
- Note any variance >10% across the 5 runs (suggests measurement noise
  needs more iterations)

Document GCC version, nvcc version, kernel version, GPU driver version
in the output. The V22 doc already establishes this practice.

### B.4 Output: extended comparison table

The end product is one table that subsumes the V8 and V22 ones:

| Metric | Ergo (current) | V22 (CPU lattice) | V8 (GPU slab) | CPU bump (floor) | GPU bump (floor) |
|---|---:|---:|---:|---:|---:|
| Steady-state throughput | N/A | 469 M/s | 1.9 G/s | TBD | TBD |
| Latency per op | N/A | 2.1 ns | 0.52 ns | TBD | TBD |
| Startup cost / buffer | TBD | ~30 ns | ~50 ns | ~0 | ~0 |
| Determinism | Bit-identical (x86 contract) | Bit-identical (`-ffp-contract=fast`) | Bit-identical SASS | Trivially | Trivially |
| Concurrent throughput | N/A | 6-core scaled | 30K-lane scaled | N/A | TBD |
| Memory model | STATIC + libc malloc | Lattice slots | Slab + bitmap | Bump arena | Atomic bump |

Plus a side-by-side instruction-count table from Part A.

## Sequencing

**Prerequisite (before Pass 1):** 30-minute ALLOCATABLE smoke test per
Correction 2. Confirm `ALLOCATE(A(N))` + array access + PRINT works
end-to-end with the arena lowering. If it doesn't, stop and report.

The work then decomposes into four passes, **executed in this revised
order (Pass 1 → 4 → 2 → 3) per Correction 3:**

1. **Pass 1: Calibrate.** Build CPU and GPU bump allocators, measure
   them. Updates [Testing/](../Testing/) with `baseline_bump.{c,cu}` and
   a `BASELINE.md` reporting the floors. ~1 day. *Unblocks Pass 4.*

2. **Pass 4: Unified table (initial).** Combine Pass 1's floors with
   existing V8/V22 numbers. Add an Ergo column with cells placeholdered
   as "see Pass 2/3." Ship as `Testing/COMPARISON_TABLE.md`. ~½ day.
   *This is shippable on its own; if Pass 2 or 3 blocks, Pass 4 has
   already produced a meaningful artifact.*

3. **Pass 2: Ergo CPU instrumentation.** Build `tests/allocate_bench.ergo`,
   compile with current `DETERMINISTIC_FLAGS`, capture x86 assembly.
   Side-by-side table with V22. Fills in the Ergo CPU cells in the
   unified table from Pass 4. ~1 day. *Requires the prerequisite
   smoke test to have passed.*

4. **Pass 3: Ergo GPU instrumentation.** Use existing post-peephole
   `galaxy_render.spvasm` plus a small "allocation-pattern microkernel"
   if needed (writing into a STATIC GPU array in a tight loop). Compare
   against V8 SASS at SPIRV level; SASS-level if driver dump works in
   under an hour. Fills in the Ergo GPU cells. ~1-2 days, with the
   SPIRV-only escape hatch.

Total: ~4-5 days of measurement and writeup, with two graceful failure
modes (ALLOCATABLE broken → stop after prerequisite; driver-SASS
intractable → SPIRV-only Pass 3) that still yield a shippable artifact.

## What not to do

- **Don't write a custom allocator for Ergo.** The point of this brief
  is to *measure what's there*, not to add anything. If the measurements
  suggest Ergo needs runtime allocation, that's a separate decision and
  a separate brief.

- **Don't run benchmarks across machines.** The existing V8/V22 numbers
  are Ryzen 5 3600 + RTX 2060. Stay on that hardware. Cross-machine
  comparison is its own audit and not in scope.

- **Don't try to make Ergo "win" any column.** The honest table is the
  goal. Ergo will lose the throughput columns (because it doesn't have
  runtime allocation) and win the steady-state columns (because static
  carveout has zero runtime cost). Both are correct results. Report them.

- **Don't bundle Part A and Part B into one PR.** Each part has its
  own deliverable (a table + narrative for A; a benchmark suite + table
  for B). Reviewers should be able to sign off on each independently.

- **Don't fight the GPU driver-SASS dump.** If it doesn't work in under
  an hour, document the limitation and compare at SPIRV level. The
  brief is about understanding, not about exhaustive coverage.

- **Don't add comparisons against other allocators** (mimalloc, jemalloc,
  TLSF, etc.) in this PR. They're interesting but out of scope. The
  three-way Ergo/V22/V8 comparison is the contribution.

## Validation

For Part A:
- Every assembly listing in the comparison table must be reproducible
  from a documented command line.
- The comparison narrative must be reviewable against the actual
  assembly — no claims that aren't supported by a specific listing.

For Part B:
- Every measurement must include the 5-run median + variance.
- Any measurement with >10% variance must be re-run with more iterations
  until it's stable, or annotated as "noisy" in the output.
- The bump baselines must be reproducible by anyone who clones the
  repo and runs `make` in Testing/.
- The Ergo measurements must use the post-x86-determinism build flags
  (stage 1 commit 1093c77 or later), not the pre-flag `-O0` build —
  otherwise the numbers describe a build no one ships.

## Open questions for the implementer

(The original "does ALLOCATABLE work?" question is now the prerequisite
smoke test per Correction 2. The remaining open questions are scope and
methodology, not blockers.)

1. **Should V8 be re-measured at all?** The Testing/ docs are dated.
   If the V8 binary still exists and ptxas hasn't changed (it has, GCC
   15.2.1 is in the toolchain now per the docs), the existing numbers
   might still hold. If you rebuild V8 from source and the numbers
   shift, that's a separate observation worth flagging.

2. **What's the right size class for the comparison?** V8 has 3 size
   classes (64B, 128B, 256B). V22's slots are fixed at the lattice
   structure. Ergo's allocations are whatever the source declared.
   Picking 64B as the canonical size for the comparison is the most
   defensible (smallest, most allocation-pressure-sensitive).

3. **Branching:** branch from the merge state of master after
   spirv-peephole + arena-lowering have landed. Both are prerequisites
   (spirv-peephole for `ERGO_HASH_FINAL`, arena-lowering for the actual
   ALLOCATE→bump emit being measured). If those haven't merged when
   this work starts, branch from arena-lowering directly (which is
   already off spirv-peephole).

4. **NVVM target?** The Ergo SPIRV backend is the GPU production path,
   but there's also an NVVM backend. Should that be in scope? Default
   answer: no — SPIRV is what ships, NVVM is partial. Add NVVM as a
   follow-up if results warrant.

## Reporting back

After each pass (in the revised execution order):
- Pass 1: file the bump-allocator code + BASELINE.md.
- Pass 4 (initial): file the unified table with Ergo cells placeholdered.
- Pass 2: fill in Ergo CPU cells; file the CPU comparison table + narrative.
- Pass 3: fill in Ergo GPU cells; file the GPU comparison table + narrative.

Hand back to me (or the user) when each pass is complete; don't
sequence them all autonomously. The earlier passes inform what to
measure in the later passes — for example, if the GPU bump floor is
much higher than expected, V8's geometric design looks even better
relative to the floor, and the narrative should adjust.

If a pass turns up something genuinely surprising (a number that breaks
the V22 or V8 doc's claims, an Ergo measurement that's nonsensical),
**stop and flag it.** Don't try to explain it away in the writeup. The
existing Testing/ docs are the trusted prior art; a measurement that
contradicts them probably means something is wrong with the new
measurement, not with the prior art.
