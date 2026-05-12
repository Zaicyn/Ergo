# x86 Determinism Fix — Implementation Brief

## Corrections vs original brief

Three gaps were caught during stage 1 implementation. Documented here so
stages 2+ pick them up:

1. **Fourth GCC call site at [mcl/jit.py:168](../mcl/jit.py#L168).** The
   original brief listed three call sites in [mcl/driver.py](../mcl/driver.py)
   (lines 90, 175, 234) but missed the JIT path. The JIT path was already
   at `-O2` (not `-O0` like the AOT path), uses `-shared -fPIC` for
   `.so` output, and reads from stdin (`-x c -`). `DETERMINISTIC_FLAGS`
   is **additive** to those existing flags — don't replace `-shared` /
   `-fPIC`. Stage 1 lands this; stage 2 needs to update the
   `jit(...)` function signature when `fast_math` is split.

2. **`-std=c11` belongs in `DETERMINISTIC_FLAGS`.** The original brief
   showed the constant without a `-std` flag, while all four call sites
   inlined `-std=c99`. The spec text in stage 3 already promises `c11`.
   Stage 1 standardizes via the constant, dropping the per-call-site
   `-std=c99`. (Generated C compiled cleanly under `c11`; if a future
   change breaks that, fall back to `c99` and revise the stage 3 spec
   text — don't fight an unrelated C compatibility issue.)

3. **Stage 1 validation target and hash mechanism were under-specified.**
   The brief said "build `galaxy_structured.ergo` (or whatever the
   brief's stage specifies)" but no stage actually specified one. The
   `ERGO_HASH_FINAL` hook is GPU-only (early-returns when `_gpu_arrays()`
   is empty), so a CPU-only program needs an inline source-level hash.
   Stage 1 uses [tests/sq2core.ergo](../tests/sq2core.ergo) with an
   inline xorshift-mix hash over the integer state arrays
   (`TOCC`, `TFROZ`, `TWHEAD`, `TLEN`, `TALLOC`, `TTOTAL`), plus
   `galaxy_structured.ergo` with the existing GPU hash hook for
   FP/GPU-pipeline coverage.

   The sq2core hash uses only `IEOR` and `ISHFT` (no addition, no
   multiplication) so the hash itself is bit-exact under any GCC
   optimization level. Skipping `TINVAR` (REAL) is intentional —
   FP determinism is validated separately via the GPU path.

   A future extension worth considering: generalize the
   `ERGO_HASH_FINAL` hook in [mcl/ir_codegen.py:2097](../mcl/ir_codegen.py#L2097)
   to also fire on CPU-only programs by hashing canonical STATIC arrays
   when `_gpu_arrays()` is empty. ~20 LOC. Removes the need for inline
   per-test hashes. Not in stage 1 scope.

## What this is

Ergo's C-backend build pipeline currently inherits none of the
determinism/performance recipe that the V22 work established for x86 under
GCC. Generated C compiles at `-O0` by default. This brief lands the recipe
in stages, each stage independently validatable via the `ERGO_HASH_FINAL`
mechanism added in the SPIRV peephole work.

Full analysis: [x86_Determinism_Audit.md](x86_Determinism_Audit.md).
V22 empirical basis: [../Testing/V22/COMPILER_DETERMINISM.md](../Testing/V22/COMPILER_DETERMINISM.md).

This is **not** a single-PR task. It is sequenced as five stages, each its
own PR, each with explicit validation gates. **Do not proceed to stage N+1
without passing stage N's validation.**

## Prerequisites

1. Branch off `main` (or current default). Name: `x86-determinism-stage-N` per stage.
2. `ERGO_HASH_FINAL=1` hash hook is operational (landed in commit ffa1d5e
   on the spirv-peephole branch — merge that first if not already in main).
3. Familiarity with [Testing/V22/COMPILER_DETERMINISM.md](../Testing/V22/COMPILER_DETERMINISM.md)
   — this is the empirical basis for every flag choice in the brief.

## Validation methodology (applies to every stage)

For each stage:

1. **Pre-change baseline:** check out the pre-stage commit. Build
   `galaxy_structured.ergo` (or whatever the brief's stage specifies).
   Run twice with `ERGO_HASH_FINAL=1`, record both hashes. They **must**
   match each other (proves the pre-change build is itself deterministic).
   Record wall-clock for both runs.
2. **Apply the stage's changes.** Single commit per change; multiple
   commits per stage allowed if logically separable.
3. **Post-change validation:**
   - Two back-to-back runs of the new build → hashes match each other.
   - Two clean rebuilds (`make clean && build`) → run hashes match across
     the two builds. (This validates that the *compilation itself* is
     deterministic, not just runtime.)
4. **Pre vs post:** hash *may* differ between baseline and post-change
   (expected for `-O3`, FMA). What you're validating is *stability of the
   post-change build*, not equivalence with the pre-change build.
5. **Wall-clock comparison:** record post-change median wall-clock over
   5 runs. Significant regressions (>10% slower) are a flag — investigate
   before committing.

A "validation passed" stage produces a commit + a one-line note in the
PR description: "Stage N: baseline hash X, post-change hash Y (stable
across 2 back-to-back runs and 2 clean rebuilds), wall-clock Z."

If any of those four conditions fail, **stop and report**, do not proceed.

## Files in scope

Every stage edits one or more of:

- [mcl/driver.py](../mcl/driver.py) — primary target. Three GCC call sites
  at lines 90, 175, 234. Defines `DETERMINISTIC_FLAGS` (added in stage 1).
- [mcl/jit.py](../mcl/jit.py) — fourth GCC call site at line 168. Imports
  `DETERMINISTIC_FLAGS` from `driver`. The JIT site keeps its own
  `-shared -fPIC -x c -` flags; `DETERMINISTIC_FLAGS` is additive.
- [mcl/__main__.py](../mcl/__main__.py) — argparse setup, CLI flag wiring.
- [Spec/MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md) — documentation of
  the determinism contract.
- [tests/sq2core.ergo](../tests/sq2core.ergo) — stage 1's CPU-path
  validation harness (inline integer state hash).

Nothing else should change. If a stage's change requires touching anything
in [mcl/ir.py](../mcl/ir.py), [mcl/backends/](../mcl/backends/),
[mcl/codegen.py](../mcl/codegen.py), or any other `.ergo` source, stop and
ask — you've drifted out of scope.

## Stage 1 — Add safe optimization + FP flags

**Goal:** every Ergo program compiles with `-O3 -march=x86-64-v3
-ffp-contract=fast -fno-math-errno` by default.

**Why:** these four flags are V22-validated as performance-positive and
determinism-neutral. Per the audit, they're the single biggest gap with
the V22 recipe. Net effect: substantial performance improvement, zero
determinism cost.

**Change:** at all four GCC call sites — three in
[mcl/driver.py](../mcl/driver.py) (lines 90, 175, 234) and one in
[mcl/jit.py](../mcl/jit.py) (line 168) — splice the flags into the
existing flag list. Pattern as landed in stage 1:

```python
# mcl/driver.py — module scope
DETERMINISTIC_FLAGS = [
    "-O3",
    "-march=x86-64-v3",
    "-ffp-contract=fast",
    "-fno-math-errno",
    "-std=c11",
]
gcc_flags = ["gcc", "-o", output, c_path] + DETERMINISTIC_FLAGS + ["-lm", ...]
```

Define `DETERMINISTIC_FLAGS` once at module scope in `driver.py`,
reference from all three driver sites and from `jit.py` (via
`from .driver import DETERMINISTIC_FLAGS`). Don't copy-paste the list.
Drop the per-call-site `-std=c99` (now covered by the constant).

**Validation:**

1. Pre-baseline: hash + wall-clock of two runs at pre-change commit.
2. Apply commit.
3. Two back-to-back runs of new build → hashes match each other.
4. Two clean rebuilds (`rm <output> && python -m mcl ...`) → hashes match
   across rebuilds, AND the binaries are bit-identical
   (`cmp build1 build2` should produce no output).
5. Wall-clock should improve, often substantially (V22's STATIC-constitution
   analysis suggests 2-10× on physics-heavy code, since the current build
   is `-O0`).

**Expected hash behavior pre vs post:** the hash *will* change. `-O3` and
FMA fusion alter the bit pattern of float results. That is expected and OK.
What matters is post-change stability.

**Failure modes to watch for:**

- Compile errors from `-march=x86-64-v3` on older CPUs. If the build
  machine is pre-Haswell or pre-Zen, downgrade to `x86-64-v2` and
  document it.
- `vk_host.c` or other runtime C files failing to compile under `-O3`
  due to strict aliasing or similar. Fix the runtime; do not relax the
  flag.
- Binary bit-identity failing across rebuilds. GCC build-IDs and timestamps
  embedded in binaries can cause this; the *hash of program output* must
  still match. If output hashes match but `cmp` shows differences, that's
  fine — note it in the PR.
- Wall-clock regression. Possible if the pre-change build was somehow
  benefiting from `-O0` (unlikely but conceivable for some pathological
  pattern). Investigate before committing.

**Out of scope for this stage:** anything in stages 2-5.

## Stage 2 — Split `--fast-math` into `--gpu-fast-math` and `--cpu-fast-math`

**Goal:** the `--fast-math` CLI flag no longer silently applies GCC
`-ffast-math` alongside SPIRV scatter atomics. Users opt into each
explicitly.

**Why:** per the audit, the current single flag is a hazard — anyone
enabling it for GPU scatter atomics also gets full reassociation on CPU
code, which V22 measured as drifting the algebraic-zero residual to ~0.053
over 1M calls. The two concerns are independent and should be controllable
independently.

**Change in [mcl/__main__.py](../mcl/__main__.py):**

Add two new flags:

```python
parser.add_argument(
    "--gpu-fast-math", action="store_true",
    help="Allow GPU scatter atomics (loosens determinism on SPIRV "
         "scatter reductions only; CPU codegen unaffected)",
)
parser.add_argument(
    "--cpu-fast-math", action="store_true",
    help="Pass -ffast-math to GCC (allows reassociation, breaks IEEE; "
         "use only when you've verified no algebraic invariants depend "
         "on bit-exact float math)",
)
```

Keep `--fast-math` for one release as a **deprecation alias** that sets
both new flags and prints a warning to stderr:

```
WARNING: --fast-math is deprecated and applies BOTH --gpu-fast-math and
--cpu-fast-math. Use the specific flags instead. See
Spec/x86_Determinism_Audit.md for the rationale.
```

This avoids breaking existing user invocations while signalling the
change. Remove the alias entirely in a future release.

**Change in [mcl/driver.py](../mcl/driver.py) and [mcl/jit.py](../mcl/jit.py):**

The current `fast_math: bool` parameter to `compile_source`,
`_compile_target`, and `jit(...)` becomes two parameters:
`gpu_fast_math: bool` and `cpu_fast_math: bool`. Update all four GCC
call sites:

```python
if cpu_fast_math:
    gcc_flags.append("-ffast-math")
```

The SPIRV backend's atomic-emission rule reads `gpu_fast_math` instead of
`fast_math`. Find the read site in [mcl/backends/spirv.py](../mcl/backends/spirv.py)
or wherever Part 8.2's "fast-math mode" check lives, and update it.

The JIT path currently has a `fast_math: bool = False` keyword argument
on `jit(...)` ([mcl/jit.py:122](../mcl/jit.py#L122)). Splitting it is
a backwards-incompatible signature change — grep for `jit(` callers
(including in [tests/](../tests/)) before changing the signature.
Consider the same one-release deprecation alias pattern as for the
CLI flag.

**Validation:**

1. Run with neither flag → must behave identically to stage-1 build
   (no GCC `-ffast-math`, no SPIRV scatter atomics). Hash should match
   stage-1's hash.
2. Run with `--gpu-fast-math` only → SPIRV atomics enabled, CPU codegen
   unchanged. Hash differs from default *only* on programs with scatter
   loops; otherwise identical.
3. Run with `--cpu-fast-math` only → GCC `-ffast-math`, SPIRV scatter
   serialized. Hash differs from default for any FP-heavy program.
4. Run with `--fast-math` (deprecated) → both above, plus a stderr warning.
   Behavior identical to pre-change `--fast-math`.

For each of (1)-(4), verify the now-standard back-to-back-stability and
rebuild-stability properties.

**Failure modes to watch for:**

- Any caller of `compile_source` or `_compile_target` that currently
  passes `fast_math=True` and expected both effects. Find them all
  (grep), update them to pass both new args.
- The SPIRV atomic check might be reading the flag through a different
  channel than the C driver (e.g., env var or AST attribute). Trace it
  end-to-end.
- Tests in [tests/](../tests/) that pass `--fast-math` — update or
  verify the deprecation alias works.

**Out of scope:** changing what `-ffast-math` actually does on CPU.
You're only splitting which user-facing flag controls it.

## Stage 3 — Document the determinism contract in the spec

**Goal:** [Spec/MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md) Part 6
states the determinism guarantees Ergo provides, with explicit reference
to the build flags and the V8/V22 empirical work.

**Why:** the audit found that the spec promises "bitwise reproducible
results across compilations and platforms" but the build pipeline
didn't deliver it. With stages 1-2 landed, the pipeline *does* deliver it
under specific conditions. Those conditions need to be in the spec, not
just in the implementer's head.

**Change in [Spec/MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md):**

Add a subsection to Part 6, after "Expression Evaluation Order (Locked)":

```markdown
### Determinism Contract (x86)

Ergo guarantees bit-identical output across:
- Repeated runs of the same binary on the same hardware.
- Clean rebuilds of the same source on the same target triple with the
  same compiler version and feature flags.

This guarantee holds under the default build flags:
`-O3 -march=x86-64-v3 -ffp-contract=fast -fno-math-errno -std=c11`.

The guarantee does NOT extend to:
- Cross-target builds (x86 vs ARM vs RISC-V). Each target has its own
  determinism contract per its own audit.
- Builds with `--cpu-fast-math`. This flag explicitly permits
  reassociation; bit-identity is sacrificed for speed.
- Builds with different compiler versions (GCC 13 → GCC 14 may alter
  bit patterns even under strict flags). Pin the compiler version for
  long-term reproducibility.
- Builds on CPUs without FMA support (`-ffp-contract=fast` becomes a
  no-op). The `x86-64-v3` march requirement guarantees FMA; relaxing
  it requires its own audit.

Empirical basis: the recipe is validated by the V22 Squaragon work
documented in `Testing/V22/COMPILER_DETERMINISM.md`. V22 is a
hand-vectorized geometry primitive whose algebraic-zero residual provides
a sensitive determinism oracle — small drift becomes detectable as a
non-zero result. Under the recipe flags, the residual is bit-exactly
`0.0`. Under `-ffast-math`, it drifts to ~0.053 over 1M calls.

The `--cpu-fast-math` flag is therefore documented as
"explicitly off the determinism contract." Users enabling it accept
that bit-identity no longer holds.
```

Adjust prose to match the rest of the spec's tone.

**Validation:** no runtime change. This is a documentation commit. The
validation is "does the documented contract match the actual behavior of
the build pipeline after stages 1-2."

Verify by:
1. Re-read the new spec section against the current behavior of
   [mcl/driver.py](../mcl/driver.py).
2. Confirm every claim in the section is true.
3. If any claim isn't true, either fix the build or fix the spec — but
   don't ship a contract you don't enforce.

**Out of scope:** any change to existing spec sections beyond adding the
new subsection. Don't reorganize Part 6 to accommodate it; just append.

## Stage 4 — Add configurable flag surface (deferred)

**Goal:** expose `--cpu-opt`, `--cpu-march`, `--cpu-fp-contract` as
user-facing flags, with the stage-1 values as defaults.

**Why:** infrastructure for the ARM/RISC-V port. The flag *names* differ
per target but the flag *categories* are the same. Building this surface
for x86 first makes the future port mechanical.

**Defer this stage** until ARM or RISC-V work is on the table. The
hardcoded defaults from stage 1 are sufficient for the x86-only case.

When this stage is needed, the brief is:

- Add three argparse flags: `--cpu-opt {0,1,2,3}` (default 3),
  `--cpu-march STR` (default `x86-64-v3`),
  `--cpu-fp-contract {off,on,fast}` (default `fast`).
- `DETERMINISTIC_FLAGS` in driver.py becomes a function of those args.
- The deprecation alias for `--fast-math` (from stage 2) is the precedent
  for how to handle CLI surface changes; follow the same pattern.

**Validation:** for each non-default value of each flag, verify the
build still produces stable hashes across back-to-back runs and rebuilds.
The hashes will differ between flag settings (that's the point) but must
be stable within a setting.

**Out of scope until activated.**

## Stage 5 — OpenMP reduction pragmas (deferred)

**Goal:** generated C emits `#pragma omp simd reduction(+:acc)` (or
analogous) above SUM/DOT_PRODUCT/NORM2 loops to grant explicit
reassociation permission for one accumulator.

**Why:** per V22's analysis, strict IEEE prevents GCC from
auto-vectorizing reduction loops. V22 went around this with hand-SIMD;
Ergo can use the OpenMP `reduction` clause as a portable equivalent that
preserves "deterministic for a given thread count" semantics.

**Defer this stage** until profiling shows reduction loops are a
bottleneck. Stage 1's `-O3 -march=x86-64-v3 -ffp-contract=fast` will
already deliver SIMD on non-reduction loops; reductions are the
specifically-blocked case.

**Validation when activated:** hashes must be stable for a given thread
count. Document this as a per-thread-count determinism guarantee, not a
universal one.

**Out of scope until activated.**

## Sequencing

Run stages in order. Stage 1 must land and be validated before stage 2 is
started. Each PR references its predecessor.

Stage 1 is the urgent one. Stage 2 is the hazard-mitigation one. Stage 3
formalizes the contract. Stages 4 and 5 are deferred infrastructure.

Estimated effort, assuming the implementer is familiar with the codebase
from prior briefs:

- Stage 1: 30 minutes implementation + 1 hour validation. One PR.
- Stage 2: 2-4 hours implementation + 1 hour validation. One PR.
- Stage 3: 30 minutes implementation. Validation is rereading. One PR.
- Stage 4: 4-6 hours when activated. One PR.
- Stage 5: 2-4 hours when activated. One PR.

Total active work: 4-6 hours across three PRs. Deferred work adds 6-10
hours when picked up.

## What not to do

- **Don't bundle multiple stages into one PR.** Each stage has its own
  validation gate. Bundling means a single failure rolls back the whole
  PR; sequencing means each piece ships independently.
- **Don't change FP semantics in the generated C.** This brief only
  touches build flags and CLI surface. The C codegen itself
  ([mcl/codegen.py](../mcl/codegen.py)) is not touched. If you find
  yourself wanting to modify generated C to "help" the compiler, stop
  — that's a separate project with a separate brief.
- **Don't optimize the spec wording in stage 3.** Add the new subsection.
  Don't reorganize Part 6 around it. Spec churn produces review burden
  out of proportion to the value.
- **Don't expand `-march=x86-64-v3` to `-march=native`.** Native means
  "fast on the build machine, undefined on others." For an Ergo program
  that may be redistributed or run on heterogeneous hardware, `v3` is
  the right floor. If a user wants `native`, that's stage 4's
  `--cpu-march` flag.
- **Don't enable `-flto` (link-time optimization).** Tempting because
  it would inline across translation units, but it complicates the
  determinism story (LTO can introduce nondeterminism in some GCC
  versions) and the audit didn't validate it. Separate audit, separate
  decision.
- **Don't touch the runtime C files** ([mcl/runtime/vk_host.c](../mcl/runtime/vk_host.c)
  etc.) beyond what's necessary to make them compile under the new flags.
  If a runtime file breaks under `-O3`, fix the runtime file minimally,
  don't relax the flags.

## Open questions for the implementer

1. Is there a CI or test harness that runs Ergo programs and checks
   output? If yes, stage 1 will perturb its expected hashes — those need
   updating. If no, the validation methodology in this brief is the
   harness.

2. Does the runtime ([mcl/runtime/](../mcl/runtime/)) compile under `-O3`
   today? It's not currently being optimized either (per the audit), so
   stage 1 will be the first time it's seen `-O3`. There may be latent
   strict-aliasing issues that surface. Plan for an hour of runtime
   debugging if so.

3. The SPIRV peephole hash hook (commit ffa1d5e) hashes POS/VEL/OMEGA at
   exit. If stage 1's `-O3` build produces a different hash (expected),
   the SPIRV peephole branch's validation needs re-anchoring against the
   new baseline. Coordinate the merge order: SPIRV peephole branch first,
   then start stage 1 with the new merge as the baseline.

4. Are there any consumers of [mcl/driver.py](../mcl/driver.py) outside
   the main CLI (e.g., tests that import `compile_source` directly)?
   They need updating in stage 2 when `fast_math` becomes
   `gpu_fast_math` + `cpu_fast_math`. Grep before changing the signature.

5. What's the project's policy on the deprecation alias in stage 2? Some
   projects keep deprecated flags for years; others remove them
   immediately. Default in this brief is "one release of warning, then
   remove." Adjust per project norms.

## Reporting back

After each stage:

- Branch name + commit hash(es)
- Baseline hash + post-change hash
- Wall-clock pre vs post (median of 5 runs)
- Confirmation that all four validation conditions held (back-to-back
  match, rebuild match, optional binary cmp, no significant regression)
- Anything surprising

If a stage failed validation, report what failed and stop. Do not
attempt the next stage.
