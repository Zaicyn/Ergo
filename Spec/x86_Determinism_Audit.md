# x86 Determinism Audit — Ergo build pipeline vs V22 recipe

The V22 work established an empirical recipe for bit-exact deterministic
float math on x86 under GCC. Ergo's design promises the same property
(Part 6 of [MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md): "bitwise
reproducible results across compilations and platforms"). This document
audits whether Ergo's current build pipeline inherits V22's determinism
guarantees in practice.

Reference: [Testing/V22/COMPILER_DETERMINISM.md](../Testing/V22/COMPILER_DETERMINISM.md).

## Recipe to match

V22 recommends:

```
CFLAGS = -O3 -march=native -ffp-contract=fast -std=c11 -fno-math-errno
```

Forbidden:

```
-ffast-math, -Ofast, -funsafe-math-optimizations, -fassociative-math,
-freciprocal-math, -ffinite-math-only
```

The recipe is justified by:
- `-O3` produces good code without altering FP semantics.
- `-march=native` enables ISA features (FMA, AVX2) but is bit-deterministic
  *within* that feature set.
- `-ffp-contract=fast` is the one optional flag that adds FMA fusion
  across statements; FMA itself is IEEE 754-2008 standard and
  deterministic.
- `-fno-math-errno` lets the compiler inline `sqrtf`/`sqrt` directly
  rather than calling libm; no semantic change.
- `-std=c11` is the modern strict-conformant target.
- `-ffast-math` is forbidden because it permits reassociation
  (`(a+b)+c` → `a+(b+c)`), which breaks bit-equality of accumulator
  chains and destroys V22's algebraic-zero invariants.

## Ergo's current GCC invocation

From [mcl/driver.py](../mcl/driver.py), three call sites compile generated
C to executables. They share the same flag set:

### Site 1: pure CPU build ([mcl/driver.py:90-98](../mcl/driver.py#L90-L98))

```python
gcc_flags = ["gcc", "-o", output, c_path, "-lm", "-std=c99",
             f"-I{runtime_dir}"]
if render:
    gcc_flags.insert(3, vk_host_c)
    gcc_flags.extend(["-lvulkan", "-lglfw"])
if fast_math:
    gcc_flags.append("-ffast-math")
```

### Site 2: SPIRV target fallback ([mcl/driver.py:175-181](../mcl/driver.py#L175-L181))

```python
gcc_flags = [
    "gcc", "-o", output, c_path, vk_host_c,
    "-lm", "-lvulkan", "-lglfw", "-std=c99",
    f"-I{runtime_dir}",
]
if fast_math:
    gcc_flags.append("-ffast-math")
```

### Site 3: SPIRV target with kernel extraction ([mcl/driver.py:234-245](../mcl/driver.py#L234-L245))

```python
gcc_flags = [
    "gcc", "-o", output, c_path,
    vk_host_c,
    "-lm", "-lvulkan", "-std=c99",
    f"-I{runtime_dir}",
]
if render:
    gcc_flags.append("-lglfw")
else:
    gcc_flags.append("-DERGO_VK_HEADLESS_ONLY")
if fast_math:
    gcc_flags.append("-ffast-math")
```

## Flag-by-flag comparison

| Flag | V22 recipe | Ergo current | Status |
|---|---|---|---|
| `-O3` | required | **missing** | **gap** |
| `-march=native` | required | **missing** | **gap** |
| `-ffp-contract=fast` | recommended | **missing** | **gap** |
| `-fno-math-errno` | recommended | **missing** | **gap** |
| `-std=c11` | recommended | `-std=c99` | minor |
| `-ffast-math` | **forbidden** | gated by `--fast-math` flag | **hazard** |
| `-Ofast` | forbidden | not used | ok |
| `-funsafe-math-optimizations` | forbidden | not used | ok |
| `-fassociative-math` | forbidden | not used | ok |
| `-freciprocal-math` | forbidden | not used | ok |
| `-ffinite-math-only` | forbidden | not used | ok |

## Findings

### Finding A: No optimization level set (CRITICAL)

Ergo does not pass `-O0`, `-O1`, `-O2`, `-O3`, or any optimization level
to GCC. The default for GCC is `-O0` (no optimization).

This means **every Ergo program currently compiles at `-O0`**. Implications:

- All scalar code runs without inlining, dead-code elimination, common
  subexpression elimination, or any of the work the
  [Testing/allocator analysis](../Testing/PROJECT_THESIS.md) documented as
  load-bearing for Ergo's "STATIC constitution" claims.
- The 14-instruction `SQ2FAL` fast path measured earlier in this project
  assumed `-O2`. At `-O0` it would be dozens of instructions with explicit
  loads and stores for every local.
- The MOD-to-AND fold, RIP-relative STATIC access, dead-code elimination
  of TINVAR — all of those are `-O2`+ optimizations. None are happening
  in the default build.

This is a much bigger gap than the FP recipe. Spec Part 6's IEEE strictness
is correct under `-O0` (no reassociation happens at all), but the
performance and the "constitution" promises rely on optimization.

**Fix:** add `-O3` to all three call sites.

### Finding B: `-ffast-math` is exposed and unsplit (HAZARD)

The Ergo `--fast-math` CLI flag ([mcl/__main__.py](../mcl/__main__.py))
maps directly to GCC `-ffast-math` *and* to the SPIRV atomic emission
rule in Part 8.2 of the spec. These are two separate decisions:

1. **SPIRV atomic emission:** allows scatter loops to emit `atomicAdd`
   instead of serializing. The IR change is local, the determinism
   weakening is well-scoped (sum order in one operation).
2. **GCC `-ffast-math`:** allows reassociation across the entire program,
   denormal flushing, reciprocal approximation, no-NaN assumptions.
   Per V22's measurements, this **drifts the algebraic-zero residual to
   ~0.053 over 1M calls** — exactly the kind of failure mode Ergo's
   Part 6 promises won't happen.

A user enabling `--fast-math` to get atomic scatter on GPU also gets
GCC's full reassociation on CPU silently. That's the trap V22 documents.

**Fix:** split the flag. Options:

- **(a)** Rename existing `--fast-math` to `--gpu-fast-math` (or `--scatter-atomics`),
  affecting only SPIRV. Add a separate `--cpu-fast-math` for the GCC flag.
  Default both off.
- **(b)** Keep `--fast-math` as a coarse "I accept non-determinism" master,
  document it as such, but don't apply it as `-ffast-math` to CPU code —
  apply only the safe parts (`-ffp-contract=fast`, `-fno-math-errno`,
  `-fno-trapping-math`). Treat full `-ffast-math` as requiring an explicit
  separate opt-in.

Recommendation: **(a)**. The principle is "the flag name should describe
what it permits, not what it enables." A user who reads `--gpu-fast-math`
knows they're loosening GPU semantics. A user who reads `--fast-math`
without context can't tell.

### Finding C: `-ffp-contract=fast` is not set (minor)

Without `-ffp-contract=fast`, GCC fuses `a*b + c` into FMA only within
a single expression, not across statements. V22's hand-SSE gains 2% from
this flag; scalar reductions in galaxy/structured may gain more (V22
measured 23 additional scalar FMAs across the whole library).

This is purely a performance leak, not a determinism leak — the absence of
the flag is the *safer* default. But the spec's IEEE 754-2008 framing
already permits FMA, so turning it on doesn't weaken the contract.

**Fix:** add `-ffp-contract=fast` to all three call sites.

### Finding D: `-fno-math-errno` is not set (minor)

Without this, GCC emits `call sqrtf` instead of inlining `vsqrtss`.
Measurable but small slowdown on any scalar code that uses SQRT —
which is most physics kernels. The galaxy build calls SQRT for distance,
norm, omega phase response, gravity. Every one of those is a libm call
right now.

**Fix:** add `-fno-math-errno` to all three call sites.

### Finding E: `-march=native` is not set (architectural)

Without `-march=native`, GCC targets the baseline x86-64 ABI (no AVX,
no FMA, no SSE4 beyond SSE2). This is the safest cross-machine default
but leaves substantial performance on the table on any modern CPU.

There's a real tradeoff here that V22's audit doesn't dwell on but is
important for Ergo:

- **`-march=native`:** binary is fast on the build machine but won't run
  on older CPUs (illegal instruction on launch). Determinism within
  a feature set still holds.
- **`-march=x86-64-v3`:** binary requires Haswell+ / Zen+ (FMA + AVX2 +
  BMI2). Portable across modern CPUs, deterministic, fast.
- **`-march=x86-64`:** baseline, runs everywhere, no FMA, slow.

For Ergo's "deterministic simulation" goals, **`-march=x86-64-v3` is the
right baseline.** It guarantees FMA availability (so `-ffp-contract=fast`
actually fires) and is supported by every CPU from ~2013 onward.

If portability to pre-2013 hardware matters, expose `-march` as a
user-controllable flag with `-march=x86-64-v3` as the default.

**Fix:** add `-march=x86-64-v3` (not `-march=native`) to all three call sites.

### Finding F: `-std=c99` vs `-std=c11` (cosmetic)

V22 uses `-std=c11`. Ergo uses `-std=c99`. The differences that matter
to Ergo: c11 adds `_Atomic`, `_Static_assert`, anonymous structs/unions,
threads.h. Ergo's generated C doesn't use any of those. No determinism
implication. Safe to leave at c99 or upgrade to c11; recommend c11 only
for consistency with the V22 baseline.

### Finding G: build flags are not user-controllable (architectural)

Currently the GCC flag set is hardcoded in [mcl/driver.py](../mcl/driver.py).
A user who wants `-O2` instead of `-O3`, or wants to disable
`-ffp-contract=fast`, has to edit the compiler source.

V22 documents flag combinations the user *should* care about
([Testing/V22/COMPILER_DETERMINISM.md:216-242](../Testing/V22/COMPILER_DETERMINISM.md#L216-L242)).
Ergo should expose at least:

- `--cpu-opt {0,1,2,3}` — optimization level. Default 3.
- `--cpu-march {x86-64,x86-64-v3,native}` — target ISA. Default `x86-64-v3`.
- `--cpu-fp-contract {off,on,fast}` — FMA contraction. Default `fast`.
- `--cpu-fast-math` — explicit, separate from GPU `--fast-math`. Default off.

This is also necessary infrastructure for the ARM/RISC-V targets:
the flag *values* differ per target, but the *flag categories* are the
same. Building this surface for x86 first makes the future port less work.

## Recommended changes, in priority order

### 1. Add `-O3 -march=x86-64-v3 -ffp-contract=fast -fno-math-errno` to all three GCC invocations.

Minimal source change. ~6 lines edited in [mcl/driver.py](../mcl/driver.py).
Massive performance improvement. No determinism regression
(all four flags are V22-verified safe).

Hash-validate before/after using the same `ERGO_HASH_FINAL` mechanism from
the SPIRV peephole work. The hash *will* change (because `-O3` changes
codegen and FMA fusion changes float bit patterns) — that's expected.
What matters is:

1. The hash is **stable across two back-to-back runs** of the new build.
2. The hash is **stable across two clean rebuilds** of the same source
   (bit-identical binary).

If both hold, the determinism contract is preserved.

### 2. Split `--fast-math` into `--gpu-fast-math` (existing behavior, renamed) and `--cpu-fast-math` (new, opt-in).

Larger change. Touches driver.py, __main__.py, possibly the spec.

Migration: any current user of `--fast-math` should be told to use
`--gpu-fast-math` instead. If anyone is depending on the GCC flag side
effect, they need to opt in explicitly.

### 3. Document the determinism contract in the spec.

Add a section to [Spec/MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md)
Part 6 (or a new appendix) stating:

- Ergo guarantees bit-identical output across rebuilds *of the same source*
  *on the same target triple* *with the same feature flags*.
- The default build flags (after fix 1) honor IEEE 754-2008 strictly,
  including FMA semantics.
- `--cpu-fast-math` is opt-in and weakens this guarantee.
- Cross-target bit-identity (x86 vs ARM, FMA vs no-FMA) is **not** promised
  by Ergo; it's deferred to user responsibility per target tuple.
- The V8/V22 work in [Testing/](../Testing/) is the empirical basis for
  these guarantees.

### 4. Add the configurable flag surface (`--cpu-opt`, `--cpu-march`, etc.)

Larger change, can be deferred until ARM or RISC-V work begins. The
hardcoded defaults from fix 1 are fine for the common case.

### 5. (Future) OpenMP reduction pragmas for SUM/DOT_PRODUCT/NORM2.

Per V22's analysis, strict IEEE prevents the compiler from auto-vectorizing
reduction loops. `#pragma omp simd reduction(+:acc)` grants explicit
reassociation permission for one accumulator. Generated C should emit
this pragma above reduction loops.

Cost: depends on OpenMP runtime, requires `-fopenmp` flag. Determinism
becomes "deterministic for a given thread count," which is what the spec
already promises for Part 9's REDUCTION class.

Not blocking; can come after the build-flag fixes.

## Validation plan

For each fix:

1. **Pre-change baseline:** build current `galaxy_structured.ergo` (or any
   non-trivial Ergo program), run with `ERGO_HASH_FINAL=1` twice, record
   both hashes and wall-clock.
2. **Apply change.**
3. **Post-change validation:**
   - Two back-to-back runs of the new build → hashes match each other.
   - Two clean rebuilds of the new build → binaries match (`cmp`) or
     run hashes match.
4. **Pre vs post:** hash *may* differ (expected for `-O3`, FMA). Wall-clock
   should improve substantially for fix 1.

If any "should match" comparison fails, stop and investigate before
shipping the change.

## Open questions for the implementer

1. Are there existing Ergo programs that rely on `-O0` behavior (e.g.,
   single-stepping in a debugger, or relying on locals not being optimized
   out)? Adding `-O3` will break those use cases. If yes, gate optimization
   behind a flag with `-O3` as default.

2. Is `-march=x86-64-v3` the right floor? Survey actual hardware in use
   by Ergo users. If anyone runs on pre-Haswell, drop to `x86-64-v2`
   (just SSE4.2 + popcnt) or stay at `x86-64` with `--cpu-march native`
   available for tuning.

3. Does the runtime ([mcl/runtime/vk_host.c](../mcl/runtime/vk_host.c))
   already get compiled with different flags than the generated C? If
   yes, the runtime's flags should match for consistency.

4. RISC-V/ARM follow-up: which toolchains are the target — GCC?
   LLVM? Both? The flag names differ slightly between them
   (`-ffp-contract=fast` is GCC; LLVM uses the same but interprets it
   somewhat differently for cross-statement fusion).

## Bottom line

Ergo currently inherits **none** of V22's determinism recipe by default.
Generated C compiles at `-O0` with no FP contract control, no FMA fusion,
no inlined `sqrtf`. The `-ffast-math` exposure via `--fast-math` is the
single biggest determinism hazard — a user-facing flag that, per V22's
direct measurement, drifts the algebraic-zero residual.

The fix is small (~6 lines for the flag changes) and validated by V22's
prior work. The hash mechanism from the SPIRV peephole PR can validate
each change. After this audit, x86 determinism becomes a *property the
compiler enforces*, not a property the spec aspires to.

ARM and RISC-V can then port the same methodology with target-specific
flag substitutions; the infrastructure built for x86 (split flags,
documented contract, hash validation) carries over directly.
