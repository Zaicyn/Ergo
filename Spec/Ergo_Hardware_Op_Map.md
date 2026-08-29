# Ergo Hardware Op Map — assembly-core project, Phase 1

2026-08-29. This document maps every Ergo operator and intrinsic to its
hardware counterpart or runtime routine, with the determinism standard
each mapping must meet. It is the ground plan for the assembly core:
the column "planned owner" is the work list, ordered by what the
measurements say is broken.

Grounding: `Spec/Ergo_Spec.md` Parts 1, 7, 9.9–9.10, 11;
`Spec/Ergo_Intrinsic_Signatures_Complete.md` (the catalog this maps);
the 2026-08-29 benchmark session (`benchmark/bench_cplx.c`,
`benchmark/bench_cplx2.c`, and the glibc-vs-musl libm runs) — every
performance or bitwise claim below is from that session unless noted.

**Determinism standards used in the tables:**

- **IEEE-exact** — the operation is exactly rounded by definition
  (add/sub/mul/div/sqrt, fmod, conversions). Bit-reproducible on any
  conforming target, no libm involvement. Free.
- **recipe-locked** — bit-identical across runs and clean rebuilds
  under the Part 7 recipe (`-O3 -march=x86-64-v3 -ffp-contract=fast
  -fno-math-errno -std=c11`), same compiler version, same target.
- **owned-kernel required** — libm breaks cross-libc bit-identity here
  (measured) or must be assumed to (unmeasured). The function must be
  re-implemented as a fixed-coefficient Ergo runtime kernel with a
  documented ulp bound against an mpfr reference.
- **out of contract** — explicitly excluded from the determinism
  contract (GPU-only intrinsics, `--cpu-fast-math` builds).

---

## 1. The map

### 1.1 Arithmetic operators (Part 1)

| Construct | Lowering today | Hardware counterpart | Determinism standard | Notes |
|---|---|---|---|---|
| `+` `-` (REAL, f64) | C `+`/`-` | `addsd`/`subsd`; `vaddpd`/`vsubpd` vectorized | IEEE-exact | FMA contraction under `-ffp-contract=fast` fuses `a*b+c` — pinned by the recipe (§4) |
| `+` `-` (REAL, f32) | C `+`/`-` | `addss`/`subss`; `vaddps`/`vsubps` | IEEE-exact | |
| `*` (REAL) | C `*` | `mulsd`/`mulss`; `vmulpd`/`vmulps` | IEEE-exact | |
| `/` (REAL) | C `/` | `divsd`/`divss`; `vdivpd`/`vdivps` | IEEE-exact | div is the slowest basic op; vectorize, never approximate (no `rcpps` — not exact) |
| `+` `-` `*` (INTEGER, INTEGER*8) | C `int`/`long long` | `add`/`sub`/`imul`, 32/64-bit | exact | wrapping two's-complement |
| `/` `MOD` (INTEGER) | C `/` `%` | `idiv` (quotient + remainder in one op) | exact | C99 truncation-toward-zero = Fortran MOD sign-of-dividend. Semantics match; no fixup needed |
| unary `-` | C unary | `xorpd` sign flip | IEEE-exact | binds looser than `**` (Part 6) |
| `**` REAL**INTEGER | C loop / `pow` | repeated `mulsd`, unrolled by exponent | IEEE-exact | never route integer exponents through `pow` — `pow(x,2)` ≠ `x*x` bitwise in general |
| `**` REAL**REAL | libm `pow`/`powf` | none — runtime kernel | owned-kernel required | glibc/musl disagree bitwise (measured); see §2 |
| `**` INTEGER**INTEGER | C loop | `imul` chain | exact | negative exponent is a compile-time error (Part 3) |
| `**` COMPLEX**INTEGER | planned | repeated complex mul (SoA pairs) | recipe-locked | |
| `**` COMPLEX**COMPLEX | planned | none — composite: `exp(w·log(z))` | owned-kernel required | built on the owned exp/log kernels; flagged — no instruction or libm call corresponds |
| relational `< > = ≠ ≤ ≥` (REAL) | C comparisons | `ucomisd` + `setcc`/`cmov` | IEEE-exact | NaN unordered semantics fall out of `ucomisd`; `=` on REAL is exact-bit equality per IEEE |
| relational (INTEGER) | C comparisons | `cmp` + `setcc` | exact | |
| `.AND.` `.OR.` `.NOT.` (LOGICAL) | C `&&`/`\|\|`/`!` on `int` | `test`/`setcc`, short-circuit | exact | LOGICAL lowers to C `int` (ir_codegen `_c_type`) |
| `:=` | C `=` | `movsd`/`vmovpd` store | — | assignment is statement-only (Part 6) |
| comparison chaining `1 < x ≤ 10` | parse-time desugar to AND tree | — | exact | no runtime construct exists (Part 1) |

### 1.2 Scalar intrinsics (signatures doc, Category 1)

| Construct | Lowering today | Hardware counterpart | Determinism standard | Notes |
|---|---|---|---|---|
| ABS (REAL) | `fabs`/`fabsf` | `vandpd`/`vandps` with sign mask — 1:1, inlined | IEEE-exact | not a libm call; any libc |
| ABS (INTEGER) | C `abs` | `cdq`+`xor`+`sub` or `cmov` | exact | |
| SIGN (REAL) | C idiom | copysign bit trick: `and`/`andn`/`or` on sign bits | IEEE-exact | Fortran SIGN(x,y) = \|x\| with sign of y; y=±0 gives ±\|x\| — keep that |
| SIGN (INTEGER) | C idiom | negate/select | exact | |
| MOD (REAL) | libm `fmod` | none on SSE/AVX — `fmod` is exact by definition | IEEE-exact | exact remainder ⇒ cross-libc safe; one of the few libm calls that may stay. (x87 `fprem` exists but is the legacy path modern libm avoids) |
| MAX/MIN (REAL, variadic) | `fmax`/`fmin` | `maxsd`/`minsd` + NaN fixup, branchless | IEEE-exact (default) | Part 7: default uses NaN-propagating `fmin`/`fmax` semantics; `--cpu-fast-math` may lower to bare `maxsd`/`minsd` (NaN not preserved). Both documented, both branchless; never an `if` |
| MAX/MIN (INTEGER) | C idiom | `cmp`+`cmov` | exact | |
| CLAMP(x,lo,hi) REAL | `fmin(fmax(x,lo),hi)` | two of the MAX/MIN lowerings | IEEE-exact (default) | Part 7 locked: guaranteed branchless; 400M-branch rationale stands |
| CLAMP INTEGER | C ternary | `cmp`+`cmov` ×2 | exact | |
| SQRT (REAL) | C `sqrt`/`sqrtf` | `sqrtsd`/`sqrtsd`; `vsqrtpd`/`vsqrtps` | IEEE-exact | hardware, exactly rounded; glibc/musl agree bitwise (measured). **Not an asm-core target (§5)** |
| INT / REAL / INT8 conversions | C casts | `cvttsd2si`, `cvtsi2sd` (32/64-bit forms) | IEEE-exact | Part 7 numeric-conversion rule: single hardware step, never a runtime helper. INT is the explicit narrowing path INTEGER*8→INTEGER (C truncation semantics); implicit narrowing is a compile error |
| HASH (INTEGER) | runtime C | splitmix64 finalizer, 64-bit: 2 `imul` + 2 shifts + 2 `xor` | exact (owned already) | 64-bit internal state; top 31 bits → int32 (signatures doc) |
| RAND (INTEGER seed) | runtime C | same splitmix64 core; top 53 bits × 2⁻⁵³ → f64 | exact (owned already) | **never libc `rand`** — its algorithm is implementation-defined. Ours is already the owned generator; the asm core inherits it verbatim |

### 1.3 Transcendentals

All lower today through libm via the `C_MATH` table in
`core/ir_codegen.py` (`sin` → `sinf` under `--precision f32`). This is
the determinism hole; §2 is the full table and the fix plan.

### 1.4 Complex operations (Category 1; all `planned` at A3)

The measured verdict (bench_cplx, bench_cplx2): **C99 `_Complex` is a
trap on hot paths.** mul/div lower to per-element runtime calls
(`__muldc3`/`__divdc3`) carrying an Annex-G NaN-guard branch; they
never vectorize; div runs 4–10× slower than manual pairs (7–9 ns/elem
vs ~2). `-fcx-limited-range` restores parity only by *removing* the
robustness. Both gcc and clang fumble this identically.

| Construct | Planned lowering | Hardware counterpart | Determinism standard | Notes |
|---|---|---|---|---|
| layout | **SoA REAL pairs** (re[], im[]) — Ergo's existing convention | ymm lanes of plain f64/f32 | — | SoA wins or ties everywhere compute-bound; AoS marginally better only when DRAM-bound (measured). Convention stays SoA |
| CMPLX(re, im) | **pack**: two lane writes | `vmovpd` to separate arrays | recipe-locked | never `re + im*_Complex_I`: an Inf imaginary part NaN-poisons the real part through the multiply (measured) |
| REAL(z), AIMAG(z) | lane read from the respective array | `vmovpd` load | recipe-locked | free — that is the point of SoA |
| CONJG(z) | negate imaginary lane | `vxorpd` sign mask | recipe-locked | |
| complex `+` `-` | pairwise REAL add/sub | `vaddpd`/`vsubpd` | IEEE-exact | |
| complex `*` | naive pairs: `ar*br − ai*bi`, `ar*bi + ai*br` | `vmulpd` + `vfmsub`/`vfmadd` (FMA3) | recipe-locked | FMA contraction is bitwise-visible here — pin `-ffp-contract` (clang's default-fast and gcc's fast produce different bits between `_Complex` lowering and manual pairs; measured) |
| complex `/` | naive pairs: `d = br²+bi²`, then two divides | `vmulpd`/`vfmadd` + `vdivpd` | recipe-locked | Annex-G robustness (overflow-safe scaling) is a **separate explicit routine, emitted only when requested** — the default hot path is the fast naive form |
| SQRT(COMPLEX) | planned | none — runtime kernel on pairs | owned-kernel required | flagged: needs a real algorithm (branch on sign of re, two sqrt/hypot forms), no instruction corresponds |
| ABS(COMPLEX) → REAL | planned | `sqrt(re²+im²)` naive on pairs | recipe-locked | overflow-robust `hypot` form only as the explicit separate routine, same rule as complex div |

### 1.5 Reductions and array intrinsics (Categories 2–3)

| Construct | Lowering today | Hardware counterpart | Determinism standard | Notes |
|---|---|---|---|---|
| SUM / PRODUCT (1-D) | C loop, vectorized | sequential `vaddsd` chain, or staged vector reduction under the Part 9.9 rules | recipe-locked | reassociation changes bits: the recipe keeps source order; `--cpu-fast-math` relaxes |
| DOT_PRODUCT | C loop | `vmulpd`+`vaddpd` staged | recipe-locked | |
| NORM2 | C loop + `sqrt` | DOT_PRODUCT + `sqrtsd` | recipe-locked | naive sum-of-squares; overflow-robust scaled form only as an explicit separate routine (same rule as complex div) |
| MAXVAL / MINVAL | C loop | MAX/MIN lowering per §1.2 | IEEE-exact (default) | |
| element-wise SQRT/EXP/LOG/SIN/COS/ABS on arrays | per-element calls in a C loop | vector SQRT/ABS 1:1; transcendentals = owned kernels in a vectorized loop | per scalar op | the vectorizable loop itself is already near-optimal (§5) |
| MATMUL | C triple loop | none — blocked C kernel to be written | recipe-locked | flagged: no instruction corresponds; blocked+FMA kernel, 64-byte-aligned tiles |
| TRANSPOSE | C loop | tiled copy kernel | exact | DRAM-bound; AoS-friendly (the one place layout is neutral) |
| RESHAPE | metadata / `memcpy` | `rep movsb` or `memcpy` | exact | column-major layout locked (Part 2); reshape of contiguous storage is a copy |
| SUM/MAXVAL along dim | C loop | as 1-D reductions | recipe-locked | |

### 1.6 String, memory, and inspection (Categories 4–6)

| Construct | Lowering today | Hardware counterpart | Determinism standard | Notes |
|---|---|---|---|---|
| LEN | compile-time constant | — | exact | fixed-length CHARACTER: no runtime op |
| INDEX | C byte loop | byte-compare loop | exact | |
| CHAR / ICHAR | C cast | `mov` | exact | ASCII |
| CONCAT | C byte copy ×2 | `memcpy` ×2 | exact | caller-allocated; constant-size overflow is a compile error |
| ZERO(A) | `memset` (locked in the signatures doc) | `rep stosb` / `vmovpd` stores via libc memset | exact | one statement, one call, every platform |
| SIZE / RANK / SHAPE | compile-time constants / small store | — | exact | no runtime op worth an instruction |
| VK_STAGE / VK_FETCH | CPU: `memmove`; GPU: device transfer | `memcpy` | exact (CPU side) | GPU residency contract is compile-time (signatures doc) |

### 1.7 Out of scope for the CPU map

- **Warp subgroup intrinsics** (RING_*, WARP_*): GPU-only, hard-coded
  32-lane, no CPU lowering exists or is planned (signatures doc,
  Category 7). Out of contract here.
- **VERIFY**: a statement directive (CPU shadow-state oracle), not an
  op. HHB payload frames (Part 11) explicitly exclude INTEGER*8 and
  COMPLEX — the frame is bytes; nothing to map.
- **LOGICAL arrays / ANY / ALL / COUNT / SORT**: listed as future
  extensions in the signatures doc; nothing to map yet.

---

## 2. The transcendental table

**Status 2026-08-29: the six core kernels are LANDED and are the
default lowering** — `core/runtime/ergo_math_kernels.h` (inlined into
generated C by `core/ir_codegen.py` when any of SIN/COS/EXP/LOG/ATAN2/
POW is used), measured ≤ 2 ulp f64 / ≤ 2 ulp f32 against an 800-bit
mpmath reference, bit-identical between gcc and clang
(tests/math_kernels/RESULTS.md). The remaining rows (TAN, ASIN, …)
still lower to libm.

**Fallback (loud):** `--libm-fallback` (driver flag), or
`ERGO_LIBM_FALLBACK=1` (environment), or `-DERGO_MATH_LIBM` (macro on a
standalone rebuild of emitted C). Each route maps the six back to host
libm; the driver prints a build-log note naming the broken guarantee
(cross-libc bit-identity). The fallback exists for build environments
where the kernels cannot compile and for generating gate baselines —
it is not a silent default anywhere.

Measured 2026-08-29, this machine, glibc vs musl: bitwise agreement
checked by hashing 200k results per function; speed in ns/call.

| Function | Lowering today | glibc vs musl bits | Speed (glibc / musl, ns) | Planned owner | Determinism-critical core? |
|---|---|---|---|---|---|
| SIN | libm `sin`/`sinf` | **disagree** | 10.9 / 9.6 | owned kernel, shared sincos core | **yes** |
| COS | libm `cos`/`cosf` | **disagree** | 11.0 / 9.6 | shared sincos core (phase-shifted) | **yes** |
| EXP | libm `exp`/`expf` | **disagree** | 5.6 / 3.4 | owned kernel (2^k · polynomial) | **yes** |
| LOG | libm `log`/`logf` | agree (measured) | 4.7 / 6.0 | owned kernel anyway — agreement between two libcs is luck, not a contract | **yes** |
| POW | libm `pow`/`powf` | **disagree** | 16.1 / 14.7 | owned kernel (exp/log composite with exact special cases) | **yes** |

| ATAN2 | libm `atan2`/`atan2f` | agree (measured) | 15.8 / 12.3 | owned kernel (same reasoning as LOG) | **yes** |
| TAN | libm | unmeasured today | — | owned kernel (sincos ratio or own reduction) | no — assume divergent until measured |
| ASIN / ACOS | libm | unmeasured today | — | owned kernel (atan2-based identities) | no |
| ATAN | libm | unmeasured today | — | owned kernel (shares the atan2 polynomial) | no |
| SINH / COSH | libm | unmeasured today | — | owned kernel (exp-based) | no |
| TANH | libm | unmeasured today | — | owned kernel (exp-based, rational form) | no |
| LOG10 | libm | unmeasured today | — | owned kernel (log · 1/ln10 — the constant must be double-double or correctly rounded) | no |
| SQRT | hardware | agree (measured) | parity (hardware) | none — stays hardware | n/a (§5) |

**The kernel standard** (the "owned kernel" column, one recipe for all):
Cephes/SLEEF-style minimax polynomials, coefficients fixed in the
source as hex-float literals, FMA3 evaluation (the x86-64-v3 baseline
guarantees it), argument reduction documented per function, ulp bound
measured against an mpfr-class reference (mpmath at 800 bits here) and
recorded in the kernel header, f64 and f32 variants. The six marked
**core** are the ones physics programs actually hot-loop on and the
ones the cross-libc evidence convicts; the rest follow the same
standard as they land. Landed cost profile (this machine): owned
sin/cos/exp/atan2 beat glibc scalar libm; log is ~2× slower; pow is
~4.7× slower (107 ns vs 22.8 — double-double heads over the leading
series terms with plain-f64 tails; the full-dd first cut was ~534 ns.
Residual gap is the documented follow-up if pow profiles hot).

Why own even the agreeing ones (LOG, ATAN2): two libcs agreeing today
says nothing about musl-next-year or a third libc. Bit-identity that
depends on the host libc is not a property of the program.

---

## 3. GPU note

Every op here has a SPIR-V GLSL.std.450 counterpart on the GPU side,
and the SPIRV backend already lowers to it — with the Part 9.10
precision policy: SQRT native f64, all other transcendentals evaluated
f64→f32→f64 (~1e-7 expected deviation, one compile-time warning per
affected kernel; POW exists only at 16/32-bit in GLSL.std.450). GPU
determinism is a separate story per Part 9.9 (SCATTER/atomics under
`--gpu-fast-math`). The assembly core is a **CPU-side** project; nothing
in this document changes the SPIRV path. If the CPU owned kernels land,
the GPU f64-transcendental gap becomes the wider of the two — that is a
known, separate follow-up.

---

## 4. Build-flag standards

1. **The determinism contract recipe (Part 7, unchanged):**
   `-O3 -march=x86-64-v3 -ffp-contract=fast -fno-math-errno -std=c11`.
   FMA3 comes from the feature level, not `-mfma`. Validated by the V22
   bit-exactness oracle (algebraic-zero residual bit-exactly 0.0 under
   the recipe; drifts to ~0.053 over 1M calls under `-ffast-math`).
2. **`-ffp-contract` is pinned, always, explicitly** — it is a
   bitwise-relevant knob, not a performance nicety. clang defaults to
   `fast` and produces different bits between its `_Complex` lowering
   and manual pairs (measured). Generated builds must pass the flag on
   every compile line regardless of compiler.
3. **64-byte alignment for large buffers (new, from today's session).**
   glibc malloc returns huge blocks at mod-64 = 16 — every ymm access
   then splits a cache line, ~2× on affected kernels. Generated code
   must 64-byte-align large allocations. The ALLOCATABLE arena already
   is 64-byte aligned (Part 2); the rule binds any buffer that leaves
   the arena path (JIT interop, runtime scratch, MATMUL tiles).
4. **Compiler parity after controls:** gcc and clang land within ~10%
   on vectorizable kernels once alignment is fixed; clang slightly
   ahead on some; both fumble `_Complex` identically (runtime calls).
   Either compiler meets the contract under the recipe.
5. **`--cpu-fast-math` boundary (Part 7, unchanged):** opt-in only,
   never default; permits reassociation, FMA fusion beyond the pinned
   rule, and non-NaN-preserving min/max; bit-identity is explicitly
   sacrificed. Nothing in the asm core may depend on it.

### Contraction policy (2026-08-29, measured)

**Who may contract a `a*b ± c` into an FMA is now decided per side:**

- **CPU (generated C):** the recipe pins `-ffp-contract=fast`
  (unchanged). Which sites actually fuse is gcc's SSA-level discretion —
  measured below — and is *stable under the recipe* (same compiler
  version, same flags, same source → same bits, which is all the Part 7
  contract claims).
- **GPU (SPIR-V):** every floating-point arithmetic result the backend
  emits carries a `NoContraction` decoration. The Vulkan driver may
  never fuse what we did not choose — GPU output is deterministic per
  binary across driver versions.  This was NOT free: the RTX 2060
  driver does contract undecorated `OpFMul`/`OpFAdd` pairs (measured
  on tests/fusible_stress.ergo: R1(4096) = …97 fused vs …88 unfused).
- **The lint:** when compiling `--target spirv`, the compiler reports
  each kernel's fusible `a*b±c` sites (analysis:
  `core/ir_contract.py:compute_fma_sites`). At those sites the CPU
  recipe *may* contract while the GPU never will — a documented
  last-ulp CPU≠GPU boundary. A kernel with no reported sites is
  CPU==GPU-bitwise by construction (given no transcendentals, §9.10,
  and no reductions, §9.9).

**Why not IR-level `fma` emission matching gcc's fusion set (plan A)?**
Measured: gcc's fused set is not computable from the IR. It depends on
post-inlining PHI/sink behavior — in one and the same loop, the
`S += sin(X)*0.37` site fused while `S += cos(X)*0.73` did not (the
cos callee's four-return shape makes the multiply land in a PHI; the
sin callee's single return doesn't). A minimal synthetic pair flips the
other way (tests/contraction/probe9). A naive IR rule emitting fma at
every `a*b±c` site moved 145/197 corpus programs' CPU outputs vs HEAD
(chaotic amplifiers flip on one site). Any rule that mismatches gcc at
one site flips every chaotic program containing it — so "match gcc" is
out, and "uniform rule" moves CPU bits, which this phase forbids.

**What full by-construction CPU==GPU equality takes** (deferred to the
re-certification window, since it moves corpus CPU bits): emit explicit
`fma()` at marked sites AND a fusion barrier (`asm volatile("" :
"+x"(v))`, zero instructions) on every unmarked mul-feeding-add, on
both CPU and GPU — then both sides execute exactly the compiler's rule.
Pair with baseline re-record; the move set will be the fusible sites
where gcc's PHI luck disagreed with the rule.

**Classes that can never be CPU==GPU bitwise:** staged-vs-sequential
reductions (Part 9.9), GPU f64 transcendentals (f64→f32→f64, Part
9.10), and driver-precision deviations — measured on the RTX 2060:
GLSL.std.450 `Sqrt` at f32 is 1 ulp off (f64 is exact). Integer/
bitwise/geometry kernels without those classes and without
lint-reported sites are equivalent by construction today.

---

## 5. What is explicitly NOT mapped to asm

- **SQRT.** `sqrtsd`/`vsqrtpd` is exactly rounded hardware; the libcs
  already agree bitwise (measured). There is nothing to win and a
  determinism oracle to lose.
- **The compiler-vectorized loops** (element-wise arithmetic,
  reductions, stencils): measured near-optimal under the recipe once
  alignment is fixed. The C codegen already reaches hardware parity on
  these; hand asm would buy nothing measurable.
- **A direct-asm backend.** Deferred until profiling shows the C
  codegen itself as the bottleneck. The owned transcendentals land as
  C-kernel routines with fixed coefficients first — they are portable,
  auditable against the mpfr reference, and the compiler's own FMA
  contraction of a fixed polynomial is recipe-locked. Pure asm variants
  of individual kernels are a later, per-kernel decision driven by
  profile data, not a backend rewrite.
- **`fmod`** stays libm: exact by definition, cross-libc safe.
  (Revisit only if a third libc ever disagrees.)

---

## Flagged: no obvious hardware/routine counterpart

These are the entries where the map is not "instruction" or "keep the
C loop" — each needs a designed routine or a decision:

- **SQRT(COMPLEX)** — needs a real algorithm (branch on sign of re;
  naive form overflows at large |re|); status `planned`.
- **COMPLEX ** COMPLEX** — polar composite over the owned exp/log
  kernels; its bitwise fate is inherited from theirs.
- **ABS(COMPLEX) / complex div robustness** — naive vs overflow-robust
  is a language-level decision (fast default + explicit robust routine
  is the proposal above; no intrinsic spelling for "robust" exists yet).
- **MATMUL** — blocked kernel to be written; the only array intrinsic
  with real arithmetic content.
- **TAN..TANH, LOG10, ASIN/ACOS/ATAN** — unmeasured under the
  cross-libc hash today; assumed divergent until the 200k-hash check
  runs on them.
