# Compiler determinism for V22

Empirical findings from compiling the Squaragon V2 primitive under different
flag regimes on Zen 2 (Ryzen 5 3600, AVX2 + FMA, GCC 15.2.1). The question:
**which compiler settings give the best speed without letting the compiler
reinterpret the math?**

All measurements run against the `static inline` API in `squaragon_v2.h`
through the driver in `v22_compare.c`. See `../asm/v22_compare.{base,fma,fast}.s`
for the emitted assembly.

## TL;DR

| Regime | scalar (ns/call) | hand-SSE (ns/call) | Algebraic invariant | Bit-exact across runs |
|---|---:|---:|---|---|
| `-O3 -march=native` (baseline) | 25.7 | 11.4 | **preserved** | **yes** |
| `+ -ffp-contract=fast` | 25.9 | 11.2 | **preserved** | **yes** |
| `+ -ffast-math` | 6.7 | 6.7 | **broken** (residual drifts from 0) | no |

**Recommended for V22: `-O3 -march=native -ffp-contract=fast`.**

It buys the hand-rolled SIMD a small FMA boost (~2%) without compromising
the algebraic-zero property the residual relies on, and without enabling
any of the reassociation/denormal/NaN-handling shortcuts that destroy
determinism.

Do **not** use `-ffast-math` on the residual or invariant code paths.
The 3.8× scalar speedup looks attractive in a microbenchmark, but it comes
from the compiler rewriting `Σv = 0` math into a pairwise tree whose rounding
no longer cancels to bit-zero. The whole point of `sq2_triple_xor_residual`
is to detect perturbation by checking against a known-zero baseline — a
spurious residual on an unperturbed gate is a **false-positive integrity
failure** of the allocator. We measured a drift of ~0.053 accumulated over
a million calls under `-ffast-math`. Across runs the drift is consistent,
but it is not zero, and that is what matters.

## What's happening under each flag

### `-O3 -march=native` — strict IEEE, baseline

The compiler honors every floating-point operation written in the source.
Hand-rolled `__m128` intrinsics emit exactly the packed ops written:

```
9 × vmulps, 30 × vaddps, 4 × vsubps, 6 × vhaddps
```

The 12-vertex scalar version emits 209 scalar fp ops (51 mulss, 134 addss,
24 subss) along a 12-deep accumulator chain. The auto-vectorizer does
**not** fire on this loop — reassociating the additions would change
rounding, and strict IEEE forbids that.

The scalar `bench_scalar` runs at 25.7 ns/call; the hand-SSE version at
11.4 ns/call. **2.25× speedup**, and it's all earned by the SSE rewrite.

The named constants from the header (`SQ2_PHI`, `SQ2_INV_SQRT2`,
`SQ2_SCALE_RATIO`, `SQ2_BIAS`) appear in the binary only as raw IEEE 754
bit patterns in `.LC` data — the macros are fully inlined. The 12-vertex
`SQ2_SEED` table is repacked at compile time into a set of `.LC30/.LC31/...`
quads, one per axis per batch, so the hand-SSE version's `_mm_set_ps(...)`
shuffles disappear at compile time.

### `+ -ffp-contract=fast` — allow FMA fusion across statements

This is the **only** non-default flag I would recommend for V22.

`-ffp-contract=fast` permits GCC to fuse separate `a*b` and `+c` into a
single `vfmadd*` instruction across statement boundaries. (Default `on`
only fuses within a single expression, and SSE intrinsics suppress
fusion entirely, so without `fast` no FMAs appear in the hand-SSE body.)

Effect on the residual:

| | baseline | + fma-fast |
|---|---:|---:|
| `vmulps` (in bench_handsse) | 9 | 5 |
| `vaddps` (in bench_handsse) | 30 | 26 |
| `vsubps` (in bench_handsse) | 4 | 2 |
| `vfm*ps` (packed FMA) | 0 | **4** |

The 4 packed FMAs replace the 120° rotation pairs (`c120*vx - s120*vy`
becomes one `vfnmadd132ps`) and the final magnitude-squared dot product
(`x² + y² + z²` collapses into two FMAs in a chain).

**Determinism guarantees that hold under `-ffp-contract=fast`:**

- The algebraic-zero property of `sq2_triple_xor_residual` is preserved.
  Verified empirically: residual of an unperturbed gate is `0.0`
  (bit pattern `0x00000000`), identical to baseline.
- No reassociation across statements. `(a + b) + c` is still computed
  left-to-right; the compiler will not rewrite it to `a + (b + c)`.
- No denormal flushing, no NaN/Inf assumptions, no `1.0/sqrt()` shortcuts.
- Output is bit-exact across runs on the same hardware.
- Cross-CPU reproducibility holds as long as both CPUs have FMA support
  (any x86-64-v3 or later — Haswell+, Zen+). FMA's "round only once at the
  end" is well-defined by IEEE 754-2008.

The FMA gain on this specific function is small (~2% on hand-SSE; the
scalar version sees no measurable speedup because the bottleneck isn't
multiply-add throughput). But it's free correctness-preserving speed,
and on other functions in the codebase (the topology force kernels,
the Viviani z computation, the scale chains) `-ffp-contract=fast`
generated 23 *additional* scalar FMAs. Across the whole library it's
worth more than just on the residual.

### `+ -ffast-math` — reassociation, no NaN, flush denormals

**Do not enable this for V22.** What it does:

- Permits associative rewriting: `((a+b)+c)+d` may become `(a+b)+(c+d)`.
  This exposes ILP on long accumulator chains — the scalar version drops
  from 25.7 ns to 6.7 ns (3.8×) on this account alone.
- Permits replacing `x/y` with `x * (1/y)`, `sqrt(x)` with the rsqrt
  approximation, etc.
- Assumes no NaN, no Inf, denormals flush to zero.
- Allows reciprocal approximations.

This destroys the residual's algebraic property:

```
sq2_triple_xor_residual_full(unperturbed gate, accumulated 1M calls):
  baseline:    sink = 0.0          (bit-exact 0x00000000 every call)
  fma-fast:    sink = 0.0          (bit-exact 0x00000000 every call)
  fast-math:   sink = 0.0527571    (drifts; reproducible across runs but not zero)
```

The drift is small (~5e-8 per call) and run-to-run reproducible on the
same binary, but it is **not bit-zero**, and the V22 invariant logic
treats any non-zero residual as evidence of perturbation. Under
`-ffast-math` you get continuous false positives on unperturbed gates.

Note also: the speed parity (`scalar ≈ hand-SSE` at ~6.7 ns) shows that
under `-ffast-math` the SIMD code provides essentially no benefit. The
compiler's pairwise-tree restructuring of the scalar code runs as fast
as the manually-vectorized hand-SSE — they converge at the same final
bottleneck (`vsqrtss` + `vdivss` on the magnitude). So `-ffast-math`
both breaks determinism *and* eliminates the value of writing SIMD by
hand. There is no scenario in which it's the right choice for this
codebase.

## Why hand-rolled SIMD wins (under strict IEEE)

The 2.25× speedup of `sq2_simd_triple_xor_residual_sse` over the scalar
version is not from packed-multiply parallelism in the obvious way. It's
from **bypassing the dependency chain** the scalar source creates.

The manually-unrolled scalar version:

```c
SQ2_TRIPLE_ADD(0); SQ2_TRIPLE_ADD(1); ... SQ2_TRIPLE_ADD(11);
```

Each `SQ2_TRIPLE_ADD` writes to `sum_x`, `sum_y`, `sum_z`. Under strict
IEEE the compiler cannot reorder these — `sum_x` after vertex 11 depends
on `sum_x` after vertex 10, which depends on vertex 9, and so on. That's
a 12-deep serial chain per accumulator. The CPU's superscalar issue is
wasted on a chain it can't break.

The hand-SSE version sidesteps this by processing 4 vertices in parallel
per batch (3 batches × 4 lanes = 12 vertices), accumulating in three
`__m128` registers, then collapsing each with `vhaddps` at the end. The
intra-batch parallelism breaks the dependency chain — exactly the
restructuring the compiler refused to do.

So the hand-SSE code is not winning by "doing 4 things at once" in
the SIMD-throughput sense. It's winning by **encoding a reordering of
the math** that the strict-IEEE compiler is not allowed to discover.
`-ffast-math` lets the compiler discover it; the hand-SSE code stops
being special; both versions hit the same `sqrt/div` floor.

## Code-shape rules for determinism

If a function must produce bit-exact identical output under repeated
calls and across machines with the same ISA level, follow these:

1. **No `-ffast-math`, no `-Ofast`.** They imply each other and they imply
   `-funsafe-math-optimizations`, which permits reassociation. The
   reassociation is what breaks determinism.

2. **`-ffp-contract=fast` is fine.** FMA is IEEE 754-2008 standard; the
   "round only once" rule is well-defined, and any CPU with FMA produces
   the same result. The flag changes output bits relative to non-FMA
   builds, but the output is deterministic within FMA-enabled builds.
   If you need cross-architecture bit-identity with non-FMA CPUs, use
   `-ffp-contract=off` and accept the ~2% slowdown.

3. **Write hand-vectorized hot paths.** The compiler will not auto-vectorize
   reduction loops under strict IEEE. If you want SIMD throughput, you
   must write SIMD intrinsics or use `#pragma omp simd reduction(...)`
   (the OpenMP `reduction` clause explicitly grants reassociation
   permission for one specific accumulator, with predictable semantics).

4. **Express algebraic-zero invariants in code that proves them.**
   `sq2_triple_xor_residual` correctly returns `0.0` directly without
   computing anything — the math proves the result. The "full" variant
   is for perturbation detection and should be reached only when you
   *expect* a non-zero result. Don't rely on rounding-cancels-out from
   12 separate float adds; rely on a proof, encode the proof.

5. **Avoid header-only `static inline` for SIMD code paths.** They're
   easy to accidentally not call from any TU, at which point the
   compiler drops them. Our first build emitted zero packed-float
   instructions because nothing in the driver actually called
   `sq2_simd_triple_xor_residual_sse`. If a SIMD function must ship,
   give it external linkage and one canonical TU.

6. **Don't trust auto-vectorization for AVX2 reachability.** The hand-SSE
   functions stayed at 128-bit `xmm` under every flag combination
   tried, because `__m128` types fix the width. Auto-vectorization
   went 256-bit (`ymm`) on the XOR-fold in `sq2_shadow_invariant` and
   on the scale-multiply chain — but only because those were *scalar
   loops*, not hand-SSE. If you want AVX2 throughput in the residual,
   you must rewrite it with `__m256` types. The compiler will not
   widen `__m128` for you.

## Specific recommendation for V22 build flags

For the V22 library and any consumer of it:

```
CFLAGS = -O3 -march=native -ffp-contract=fast -std=c11
```

Optional additions:

- `-DSQ2_DEBUG_ASSERTIONS` during development per the README.
- `-fno-trapping-math` is safe if you've verified no division-by-zero
  or sqrt-of-negative is reachable; gives the compiler slightly more
  scheduling freedom without breaking IEEE rounding.
- `-fno-math-errno` is safe and gives the compiler permission to inline
  `sqrtf` directly rather than going through libm. **This one matters**:
  default GCC behavior with `-O3` still emits a `call sqrtf` for the
  scalar version, and `-fno-math-errno` lets it use `vsqrtss` inline.

Do **not** add:

- `-ffast-math`, `-Ofast`, `-funsafe-math-optimizations`,
  `-fassociative-math`, `-freciprocal-math`, `-ffinite-math-only`.
  All of these either reassociate (breaking determinism) or make
  unsafe assumptions about NaN/Inf/denormal handling that the
  topology/invariant logic depends on.

## What `-ffast-math` *would* be appropriate for

For completeness: if V22 ever grows a path that is genuinely a numerical
approximation (a graphics rendering pass, an error metric whose exact
value doesn't matter to within ε), that path can be compiled in its own
TU with `-ffast-math`. The way to do it cleanly is per-file in the
Makefile, not globally — never let `-ffast-math` near the residual,
invariant, or DNA-strand code.

## Reproducing these measurements

```
cd Testing
make compare         # builds asm/v22_compare.{base,fma,fast}.{s,elf}
./asm/v22_compare.base.elf 20000000
./asm/v22_compare.fma.elf  20000000
./asm/v22_compare.fast.elf 20000000
```

The `.s` files contain the per-regime assembly for both `bench_scalar`
and `bench_handsse`, with `-fverbose-asm` source-line annotations.

---

## Summary

For V22's deterministic-workload goals, the right answer is **not** to
let the compiler auto-tune. The 3.8× scalar speedup from `-ffast-math`
is real, but it comes from precisely the reassociation that V22's
algebraic-zero invariant cannot survive. The hand-rolled SSE intrinsics
exist exactly to encode a determinism-preserving restructuring of the
math that the compiler isn't allowed to discover on its own — and they
deliver 2.25× over scalar under strict IEEE, which is the regime V22
actually needs.

`-ffp-contract=fast` is the one optional knob worth turning. Everything
else in the `-ffast-math` family is off-limits.
