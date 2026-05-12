# Performance Opportunities

Open performance work in Ergo, with explicit dependencies (or absence
thereof) and triggers for when each becomes worth pursuing.

Written after the determinism-arc landing (spirv-peephole + arena-lowering +
x86-determinism stages 1-3 + allocator comparison). The current state of
Ergo on a Ryzen 5 3600 + RTX 2060 is "hardware-budget-consistent throughput"
on galaxy_structured-class workloads — the SPIRV physics kernel hits 60-74
FPS at 30M particles, the CPU arena emit sits at 1.5× of the bump floor
(entirely accounted for by the bounds-check), and there is no obvious
slack at the op-count level.

This document is for opportunities *beyond* that current state. None of
them are blocking; all of them have triggers. Most are deferred until a
concrete workload makes them load-bearing.

## Framing

What follows is *not* a roadmap and not a brief. It is a catalogue of
known available wins with their dependencies named honestly. The
methodology pattern from prior briefs (predict → measure → falsify or
confirm) applies to each; before pursuing any, the trigger condition
should be checked empirically.

CPU parallelism via OpenMP, pthreads, or any thread library is **not**
on this list. Ergo's parallelism model is GPU-resident — loops extract
to SPIRV kernels via the FLOW/INJECTIVE/REDUCTION/SCATTER classifier
([mcl/ir_gpu.py](../mcl/ir_gpu.py)) and run on hardware that's already
massively parallel. The right way to make Ergo "use more CPU cores" is
to extract more loops to GPU, not to add a thread runtime to the CPU
side. Items 2 and 3 below are exactly that path.

## 1. Coast lane work

**Status:** brief written, methodology proven on crystal lane (the first
instance of the Nullable Warp Pattern).
Reference: [Coast_Lane_Brief.md](Coast_Lane_Brief.md).

**Dependencies:** zero new external. Compiler work in
[mcl/backends/spirv.py](../mcl/backends/spirv.py) and source-level
changes in [structured/fluid_subs.ergo](../structured/fluid_subs.ergo).

**Structural prerequisite (blocking):** `SORT_BY_GEN` directive plumbed
through compiler but not invoked by any shipping `.ergo` program. The
brief's load-bearing premise is "warps after sort are FMODE-coherent,
so the coast branch executes on whole warps not mixed warps." This needs
empirical confirmation before the brief's full plan is dispatched.

**Pre-flight check (30 minutes, before the brief is dispatched):**

1. Add `SORT_BY_GEN POS_X, POS_Y, POS_Z, VEL_X, VEL_Y, VEL_Z, OMEGA_NAT, FLAGS`
   to [structured/main.ergo](../structured/main.ergo).
2. Build galaxy_structured at current scale, confirm it still runs and
   produces deterministic output (hash stable across runs).
3. Measure warp GEN-uniformity: for each warp, count `unique(GEN)` via
   `RING_BROADCAST(GEN, 0)` comparisons. Histogram the count across all
   ~940K warps (at 30M particles).

**Decision point:** if histogram peaks at 1, with a small tail at 2 and
near-zero ≥3, the premise holds and the brief's full plan is viable. If
the histogram is flatter than that, the split-branch approach in the brief
fails and the cost-benefit changes substantially.

**Payoff if prerequisite passes:**
- Continuous census on GPU (eliminates the latent 25 ms CPU pass if it
  ever gets re-enabled).
- Real-time signal for the verify oracle (currently throttled to every
  100 frames by census interval).
- Second instance of the Nullable Warp Pattern — validates the pattern
  generalizes beyond crystal lane.
- Sets up later lanes (ejected, nova) with confirmed methodology.

**Estimated effort:** 30 min prerequisite + 3-4 days brief execution if
prerequisite passes. Implementer pattern from prior briefs applies.

**Priority:** highest payoff-to-dependency ratio of the four items here.
The brief is written. The methodology is proven. The only barrier is the
prerequisite check.

## 2. Reduction loops as GPU kernels (staged reduce with warp shuffle)

**Status:** spec describes the path, code doesn't implement it yet.
Reference: [MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md) Part 9.6
("Staged reduce — warp shuffle" for REDUCTION dependence class).

**Dependencies:** zero new external.

**Current state:** [mcl/ir_gpu.py:13](../mcl/ir_gpu.py#L13) and
[mcl/ir_gpu.py:31](../mcl/ir_gpu.py#L31) explicitly mark REDUCTION as
"CPU loop (staged reduce future)". The classifier identifies REDUCTION
loops correctly but the extractor doesn't emit them as GPU kernels —
they stay on CPU as serial reductions.

The SPIRV backend already supports the relevant warp-shuffle primitives:
`RING_PREV`, `RING_NEXT`, `RING_SHIFT`, `RING_BROADCAST`,
`WARP_BALLOT`/`COUNT`/`PREFIX`/`BROADCAST_FIRST` (the latter four added
during the crystal lane work). What's missing is the *extractor logic*
that recognizes a REDUCTION pattern, emits a staged-reduce kernel using
those primitives, and handles the cross-warp combination (one atomic per
workgroup, broadcast back to all lanes).

**What needs doing:**

1. Recognize REDUCTION loop in the IR pass (already done — classifier
   tags them).
2. Emit a GPU kernel that:
   - Each lane accumulates a partial sum over its iteration chunk.
   - Warp-level reduction via 5 rounds of `RING_SHIFT` butterfly
     (same pattern as the topological winding check in
     [structured/fluid_subs.ergo:472-490](../structured/fluid_subs.ergo#L472)).
   - One lane per warp does an atomicAdd to a global accumulator.
   - Final result broadcast/read by the host.
3. Wire the extractor to emit this kernel for REDUCTION dependence class.

**Payoff:** workload-dependent. Useful only when a Ergo program actually
has reduction loops as a CPU bottleneck. Galaxy_structured currently
does not — its CPU side is coordination and init, not numerical reduction.
But the verify oracle, future census aggregation, and any future
analytics-style workload would benefit.

**Estimated effort:** 5-7 days. Larger than the SPIRV peephole work
because the extractor changes are more invasive (new kernel template,
new dispatch shape, atomic-add into accumulator buffer, host readback).

**Trigger:** a profile of a specific workload showing CPU reduction loops
dominate. Without that trigger, the work is speculative — designing for
hypothetical workloads tends to produce designs that need rework when the
actual workload arrives.

**Priority:** medium. Real value but workload-dependent.

## 3. Scatter loops as GPU kernels with atomics

**Status:** plumbing exists, gate is wired but never consulted, spec/code
divergence documented.
Reference: [MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md) Part 8.2
(scatter atomic insertion rules) and Part 9.9 (implementation status
paragraph added in x86-determinism stage 3).

**Dependencies:** zero new external.

**Current state:** [mcl/ir_gpu.py:1807-1816](../mcl/ir_gpu.py#L1807-L1816)
populates `atomic_arrays` unconditionally for any SCATTER kernel with
read-modify-write at a runtime index. The `gpu_fast_math` flag is plumbed
through the SPIRV backend (per x86-determinism stage 2) but never read
for atomic-emission decisions. The classifier currently routes SCATTER
loops to CPU per [mcl/ir_gpu.py:32](../mcl/ir_gpu.py#L32) ("SCATTER → CPU
loop (atomic future)").

The spec (Part 8.2) describes a `--gpu-fast-math`-gated choice between
"serialize on CPU" (strict bitwise-deterministic) and "emit atomics on
GPU" (locally non-deterministic in sum order but vastly faster). The
code currently does neither for SCATTER — it routes to CPU regardless.

**What needs doing:**

1. Decide the resolution of the spec/code gap. Two options:
   - Wire the gate: SCATTER kernels emit atomics on GPU when
     `--gpu-fast-math` is set, serialize on CPU otherwise.
   - Update the spec: drop the gate, document that SCATTER always
     extracts to GPU with atomics (or always stays on CPU).

   The first option preserves the spec's framing and adds the runtime
   capability. The second simplifies but loses the user-controllable
   determinism/speed tradeoff.

2. If wiring the gate: extractor changes to emit SCATTER as a GPU kernel
   when the flag is set. The atomic emission itself is already done
   (the `atomic_arrays` set drives SPIRV `OpAtomicIAdd`/`OpAtomicFAdd`
   selection). What's missing is the dispatch shape and the gate check
   in the extractor.

**Payoff:** workload-dependent. Galaxy_structured does have scatter
patterns (grid density accumulation, ring exchange) but they're already
on GPU via direct kernel emission, not via the SCATTER→CPU classifier
path. The Coast Lane Brief's network oracle work (scatter-sum-broadcast
for consensus field) is the natural triggering workload — it's a
SCATTER pattern that currently has to be handled manually.

**Estimated effort:** 3-5 days, depending on which resolution path is
chosen. The wire-the-gate option is larger; the spec-update option is
~1 day.

**Trigger:** any workload that introduces a SCATTER pattern not already
handled by the manually-emitted GPU kernels. The network oracle is the
closest current candidate.

**Priority:** medium. The spec/code divergence should be resolved
eventually regardless of workload — it's a known inconsistency between
documentation and behavior. Doing it under a real workload trigger
ensures the implementation choice matches actual needs.

## 4. Small SPIRV peephole follow-ups

**Status:** known opportunities, each 1-2 days, each 1-2% wins.

**Dependencies:** zero new external.

### 4a. Finding 3 case-3: PARAMETER-resolved literal divisors

Reference: [SPIRV_Peephole_Brief.md](SPIRV_Peephole_Brief.md) Finding 3,
deferred cases.

**Current state:** stage-3 of the SPIRV peephole work folds
`MOD(loop_var, K)` to `OpBitwiseAnd` when `K` is a literal power of two
and `loop_var` is provably non-negative. The fold currently does NOT fire
when `K` is a PARAMETER reference resolved to a constant — e.g.,
`MOD(I, GRID_SIZE)` where `GRID_SIZE = 32` is a PARAMETER passed via
push constants.

**What needs doing:** PARAMETER value folding at the SPIRV emit boundary.
When the divisor in a `MOD` is an IRRef to a PARAMETER, look up the
PARAMETER's declared value; if it resolves to a power-of-two literal,
fold as if it were a literal divisor.

**Payoff:** 6 additional `OpSRem` → `OpBitwiseAnd` folds in galaxy
physics. `OpSRem` is 10-30 cycles on GPU; `OpBitwiseAnd` is 1 cycle.
Real but small per-fold savings; aggregate impact probably <1% on
wall-clock.

**Estimated effort:** 1 day. Mostly mechanical — find the PARAMETER
resolution path in the SPIRV emitter, hook a constant-resolution check
into the existing MOD-fold logic.

### 4b. 3D-access OpIMul fold

Reference: Pass 3 instruction-count audit from allocator comparison work.

**Current state:** 3D array access `A(CI, CJ, CK)` lowers to a
linearization sequence in [mcl/backends/spirv.py](../mcl/backends/spirv.py)
that computes `(CK-1) * GRID_SIZE * GRID_SIZE + (CJ-1) * GRID_SIZE + (CI-1)`.
The two `GRID_SIZE` multiplications are separate `OpIMul` ops; for any
fixed array shape they could be a single multiply against a precomputed
stride constant.

**What needs doing:** in `_linearize_index`, when the multi-dim shape is
known at compile time (which is always for STATIC arrays), precompute
the strides as compile-time constants and emit one `OpIMul` per dimension
against the precomputed stride instead of two `OpIMul`s for the higher
dimensions.

**Payoff:** 1 fewer `OpIMul` per 3D access site. galaxy_structured has
a handful of such sites; most grid access uses precomputed flat 1D
indices and dodges the 3D path entirely. Aggregate impact: minimal,
probably <0.5%.

**Estimated effort:** 1-2 days. The change is localized to
`_linearize_index` but needs careful handling of dynamic shape cases
(when the array shape involves a runtime value, the fold can't apply).

**Trigger for 4a and 4b:** neither has a hard trigger; they're
incremental cleanup. Worth doing when there's bandwidth for compiler
work and no higher-priority item.

**Priority:** low. Each is correct and worth doing; neither is
load-bearing.

## What's deliberately not on this list

For the same "trigger-driven, not speculative" reason:

- **Stage 4 of x86 determinism (configurable flag surface).** Deferred
  until ARM/RISC-V port begins. The current hardcoded defaults are
  correct for x86; making them configurable speculatively risks designing
  for the wrong constraints.

- **Stage 5 of x86 determinism (OpenMP reductions).** Removed entirely.
  The premise was wrong — Ergo's parallelism is GPU-resident, not CPU,
  and adding CPU threads is the wrong mechanism. The actual path for
  "make reductions faster" is item 2 above (REDUCTION as GPU kernel).

- **Per-frame scratch as an Ergo language feature.** Speculative — no
  current Ergo program needs it. The arena lowering provides the
  primitive; if a future workload needs reset-at-frame-boundary
  semantics, design it then against the actual use case.

- **NVVM backend completion.** SPIRV is the GPU production path; NVVM
  is partial. No current trigger to complete it.

- **Multi-GPU.** Out of scope. Determinism story would have to grow
  significantly.

## Methodology reminder

Each item above has an implicit "predict → measure → falsify or confirm"
shape. Before dispatching any of them as implementer work:

1. State the prediction explicitly. What number or behavior would
   indicate success? What would falsify the premise?
2. Run the cheapest possible diagnostic that tests the prediction.
3. Only after the diagnostic confirms the premise, dispatch the full
   implementation work.

The Coast Lane prerequisite (30-min warp coherence check) is the model.
Skipping this step has historically produced wasted implementer days
on premises that turned out to be wrong (the HOST_VISIBLE hypothesis in
Pass 3 of the allocator comparison; the SPIRV atomic gate assumption in
the original x86-determinism brief; the methodology bug in the GPU bump
floor measurement). The diagnostic step costs hours; skipping it costs
days.

## Summary table

| Item | Effort | Dependencies | Trigger | Payoff |
|---|---|---|---|---|
| 1. Coast lane | 30min preflight + 3-4 days | None | Preflight passes | High (capability + methodology validation) |
| 2. REDUCTION → GPU | 5-7 days | None | Workload bottlenecks on CPU reduction | Medium (workload-dependent) |
| 3. SCATTER → GPU | 3-5 days | None | Spec/code resolution + scatter workload | Medium (correctness + future capability) |
| 4a. PARAMETER MOD fold | 1 day | None | Bandwidth available | Low (<1% perf) |
| 4b. 3D-access IMul fold | 1-2 days | None | Bandwidth available | Low (<0.5% perf) |

Total if all pursued: ~12-19 days of implementer work, zero new
external dependencies, net effect is "Ergo can handle CPU-pressure
workloads via the GPU path" + small SPIRV cleanup.

The single recommendation: **do the Coast Lane preflight check first.**
Item 1 is the highest payoff per dependency, and the preflight is a
30-minute experiment that determines whether the full brief is worth
dispatching. Everything else can wait for its trigger.
