# ALLOCATABLE Arena Lowering — Implementation Brief

## Corrections vs original brief

Three corrections caught pre-implementation. Documented here so future
readers don't repeat the mistakes:

1. **Path A is the right scope, not "land after the comparison brief."**
   The original brief said "Sequence it *after* Spec/Allocator_Comparison_Brief.md
   has measured the current malloc-based lowering. The before/after
   comparison is the validation that the fix did what it should." That
   framing made the fix wait on prerequisite benchmark infrastructure
   that doesn't exist yet (no `tests/allocate_bench.ergo`). Correction:
   the fix doesn't need the comparison to be valid. Tests 1 and 4 are
   sufficient on their own — Test 1 (sq2core / galaxy hash unchanged)
   proves STATIC programs aren't regressed; Test 4 (no `malloc(` in the
   binary) proves the regression is gone. Tests 2, 3, 5 are deferred
   until `tests/allocate_bench.ergo` exists (see comparison brief);
   they're required for end-to-end performance validation, not for
   regression-fix validation.

2. **Branch off `spirv-peephole`, not `master`.** An earlier instruction
   said to branch off master to keep arena-lowering independent of the
   x86 determinism chain. That was wrong: master doesn't have the
   `ERGO_HASH_FINAL` hash hook (added in spirv-peephole, commit
   `ffa1d5e`), which is required for Test 1 validation. Branch off
   spirv-peephole — same dependency pattern as the x86 determinism
   stages — and re-baseline against spirv-peephole's hashes, not
   master's. spirv-peephole is the validation-tooling line; the
   determinism flags are downstream of it but independent of this
   work. The merge order:
   `spirv-peephole → master`, then `arena-lowering → master` as an
   independent line alongside the x86 determinism chain.

3. **Test 1 reference hashes (spirv-peephole tip):**
   - `galaxy_structured.ergo` (default -N 100000 --frames 100):
     `799a92c55b6b3805` (uses existing GPU hash hook)
   - `tests/sq2core.ergo` (imported from stage-1 since `tests/` is
     gitignored): `-1975039029` (uses inline integer xorshift hash;
     -O0-invariant by design)

   Both baselines stable across 2 back-to-back runs at spirv-peephole
   tip pre-arena. Post-arena: both must still produce these hashes.

## What this is

Replace the `malloc()`-based lowering of Ergo's `ALLOCATE` statement
with a STATIC-backed arena bump allocator. Removes libc dependence from
the language's allocation primitive and aligns the implementation with
the spec's "no intrinsic ever allocates" rule.

Coordinates with [Spec/Allocator_Comparison_Brief.md](Allocator_Comparison_Brief.md)
— the comparison work's `tests/allocate_bench.ergo` will exercise the
arena lowering when it lands. The regression fix itself doesn't wait
on the comparison; see Correction 1 above.

## The regression being fixed

[mcl/codegen.py:519](../mcl/codegen.py#L519):
```python
self._put(f"{node.name} = ({c_type} *)malloc(({size}) * sizeof({c_type}));")
```

[mcl/ir_codegen.py:1421](../mcl/ir_codegen.py#L1421):
```python
self._put(f"{result} = ({ct} *)malloc(({size}) * sizeof({ct}));")
```

Both emit a libc `malloc` call for `ALLOCATE(A(N))`. This contradicts
[Spec/MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md) Part 2:
"No intrinsic ever allocates. Output arrays are caller-allocated."
The presence of `malloc` in generated C means every Ergo program that
uses ALLOCATABLE has a hidden libc dependence the spec disallows.

No shipping Ergo program currently uses ALLOCATABLE (all of
[structured/](../structured/) and [galaxy/](../galaxy/) use STATIC),
so the regression is dead code on every real workload. The fix
matters because:

1. **The spec contract should be enforced, not aspirational.** A spec
   rule that the compiler silently violates is worse than no rule.
2. **Future workloads may need ALLOCATABLE.** When they do, the
   underlying mechanism should already be constitution-compliant.
3. **The allocator comparison work** wants a meaningful "Ergo
   ALLOCATE" measurement, not a libc measurement.

## The fix in shape

Replace `malloc(size)` with bump-from-arena. The arena is a STATIC
backing buffer declared at module scope in the generated C. ALLOCATE
advances an offset pointer; DEALLOCATE is a no-op (or, optionally, a
sanity check; see "DEALLOCATE semantics" below).

**Generated C sketch:**

```c
// Module-scope STATIC arena, sized by compile-time analysis
// (or a configurable cap, default e.g. 1 GiB).
#define ERGO_ARENA_BYTES (1ULL << 30)
static char _ergo_arena[ERGO_ARENA_BYTES] __attribute__((aligned(64)));
static size_t _ergo_arena_offset = 0;

// ALLOCATE(A(N)) lowers to:
{
    size_t _sz = (N) * sizeof(double);
    size_t _aligned = (_sz + 63) & ~(size_t)63;  // 64B align
    if (_ergo_arena_offset + _aligned > ERGO_ARENA_BYTES) {
        fprintf(stderr, "ergo: arena exhausted (need %zu, have %zu)\n",
                _aligned, ERGO_ARENA_BYTES - _ergo_arena_offset);
        abort();
    }
    A = (double *)(_ergo_arena + _ergo_arena_offset);
    _ergo_arena_offset += _aligned;
}
```

This is the V22 "fixed pool, lattice-aligned slots" design at its
simplest: pool from BSS, slots sized by request, alignment fixed at
64B (one cache line, also the AVX-512 alignment). Per-ALLOCATE cost
is one bounded compare + one add + one assignment. RIP-relative
addressing throughout. No libc, no syscalls, no allocator state
outside the arena.

## Design decisions worth being explicit about

### Arena size

Three options, in order of complexity:

**(a) Fixed default + override.** Default 1 GiB arena. User can
override with `--arena-size <N>` CLI flag. Simplest. Wastes BSS
on programs that don't use ALLOCATABLE (1 GB of zeroed BSS is
basically free on modern OSes — pages aren't backed until touched —
but the binary's reported size grows visibly).

**(b) Compile-time analysis.** Inspect the AST for every ALLOCATE
statement, sum their maximum possible sizes (using the largest
constant in any size expression), use that as the arena size. Most
elegant. Hardest to get right because sizes can be runtime values.
Fallback to (a) when size analysis fails.

**(c) Configurable PARAMETER.** Add a `STATIC INTEGER :: ERGO_ARENA_BYTES`
PARAMETER that the user declares at source level. The compiler reads
it during codegen. Simplest from a compiler perspective but pushes
the sizing burden onto the user.

**Recommended: (a).** Default 1 GiB is large enough that no current
workload would hit it, and the CLI override is one argparse line.
(b) and (c) are interesting follow-ups when a real workload hits
the default cap.

If the implementer prefers (c) — the user-controlled approach is
more honest about who's responsible — that's also defensible. Pick
one and document why in the commit message.

### DEALLOCATE semantics

ALLOCATE adds; DEALLOCATE doesn't subtract. Two reasons:

1. **Arena allocators are LIFO-only.** A user could
   `ALLOCATE(A); ALLOCATE(B); DEALLOCATE(A)` and expect A's bytes back.
   A simple bump can't do that — it'd have to be a freelist.
2. **Ergo's existing ALLOCATABLE usage pattern (if any) is "allocate
   once at startup, never free."** That's the STATIC pattern with a
   runtime size. Bump matches it.

So DEALLOCATE becomes a no-op (or, in debug builds, a sanity check
that the pointer is within the arena range — useful for catching
bugs but not required).

Document this clearly in the commit and in the spec. A user who
writes `ALLOCATE; DEALLOCATE; ALLOCATE` in a loop expecting
the arena to recycle will be surprised when it doesn't. The
docstring on the lowering should say "DEALLOCATE is a no-op; the
arena is bump-only."

If a future workload needs true free-and-reuse semantics, that's a
*different* allocator (V22-style lattice slots, or freelist over
the arena) and a different brief.

### Alignment

64-byte alignment for every ALLOCATE. Reasons:

- Matches one cache line on every current x86 CPU.
- Matches AVX-512 vector alignment (still relevant on AMD Zen 4+
  and Intel Sapphire Rapids+).
- Matches the natural alignment of a double-precision SIMD vector.
- Costs ≤ 63 bytes of slack per allocation, negligible at typical
  allocation sizes.

The mask form `(_sz + 63) & ~(size_t)63` is the standard idiom.
Don't bikeshed alignment up or down — 64B is the right default.

### Thread safety

Not in scope. Ergo's current execution model is single-threaded on
CPU (parallelism is GPU-only via SPIRV kernels). The arena bump is
sequential; no atomic needed.

If Ergo ever grows multi-threaded CPU execution (OpenMP, threads),
the arena bump becomes `atomic_fetch_add(&_ergo_arena_offset, _aligned)`.
One-line change. Not in scope now.

### Arena reset / multiple arenas

Not in scope. The current spec doesn't define them. If a future
workload needs "phase-scoped" allocation (allocate a batch, use it,
reset arena, allocate next batch), that's a feature addition, not
part of fixing the malloc regression.

## The change

Three edits, all in [mcl/](../mcl/):

### Edit 1: arena declaration in generated C

Both [mcl/codegen.py](../mcl/codegen.py) and
[mcl/ir_codegen.py](../mcl/ir_codegen.py) emit a `main()` function or
equivalent module-scope C. Find the place where module-scope C is
emitted (top of the file, after `#include`s, before any function
definitions). Add:

```c
/* Ergo arena: STATIC-backed bump allocator for ALLOCATABLE arrays.
   No libc, no syscalls — file-scope BSS only. DEALLOCATE is a no-op. */
#define ERGO_ARENA_BYTES ((size_t)1 << 30)
static char _ergo_arena[ERGO_ARENA_BYTES] __attribute__((aligned(64)));
static size_t _ergo_arena_offset = 0;
```

Emit this **only if** the program contains at least one ALLOCATE
statement. Programs that don't use ALLOCATABLE shouldn't carry the
arena BSS. Detect by walking the IR for ALLOCATE ops once during
codegen setup; gate the emit on that flag.

### Edit 2: ALLOCATE lowering at [mcl/codegen.py:519](../mcl/codegen.py#L519)

Replace:
```python
self._put(f"{node.name} = ({c_type} *)malloc(({size}) * sizeof({c_type}));")
```

With:
```python
self._put(f"{{")
self._put(f"    size_t _sz = ({size}) * sizeof({c_type});")
self._put(f"    size_t _aligned = (_sz + 63) & ~(size_t)63;")
self._put(f"    if (_ergo_arena_offset + _aligned > ERGO_ARENA_BYTES) {{")
self._put(f'        fprintf(stderr, "ergo: arena exhausted (need %zu, have %zu)\\n",')
self._put(f"                _aligned, ERGO_ARENA_BYTES - _ergo_arena_offset);")
self._put(f"        abort();")
self._put(f"    }}")
self._put(f"    {node.name} = ({c_type} *)(_ergo_arena + _ergo_arena_offset);")
self._put(f"    _ergo_arena_offset += _aligned;")
self._put(f"}}")
```

Or factor it into a helper. The exact indentation pattern in the
generated C should match what's already there — look at the existing
emit functions in codegen.py for the style.

### Edit 3: same change at [mcl/ir_codegen.py:1421](../mcl/ir_codegen.py#L1421)

Same shape. The two codegen paths exist because there's an older
AST-direct path and a newer IR-based path; both need fixing.

### Edit 4: DEALLOCATE lowering (if it exists)

Grep for DEALLOCATE in both codegen files. If it currently lowers to
`free(...)`, change it to a comment or remove the emit entirely. A
DEALLOCATE statement in Ergo source becomes nothing in C (or
optionally, a debug-only bounds check).

### Edit 5: spec update

In [Spec/MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md) Part 2,
update the ALLOCATABLE description to mention:

- ALLOCATABLE arrays are backed by a STATIC arena (BSS-resident, no
  libc).
- DEALLOCATE is a no-op; the arena is bump-only.
- Arena size is `--arena-size` (default 1 GiB).

This is a small addition, not a rewrite. Same shape as the stage-3
determinism contract addition.

### Edit 6: CLI flag in [mcl/__main__.py](../mcl/__main__.py)

Add `--arena-size <bytes>` argparse flag. Plumb it through
`compile_source` and `_compile_target` to the codegen layer.
Codegen substitutes the value into the `#define` instead of the
literal `(size_t)1 << 30`.

Accept human-friendly suffixes if you want (1G, 512M, etc.) — or
keep it simple and require bytes. Whichever is less code. The
flag exists, that's the load-bearing thing.

## Validation

Reuse the methodology from the SPIRV peephole and x86 determinism
work. Tests 1 and 4 are the load-bearing checks for the
regression-fix scope (Path A); tests 2, 3, 5 are deferred until
`tests/allocate_bench.ergo` exists in the comparison work.

### Test 1: bitwise equality on STATIC-only programs (REQUIRED)

`tests/sq2core.ergo` and `galaxy_structured.ergo` use no ALLOCATABLE.
Their hashes must be **unchanged** by this work — the arena lowering
only affects ALLOCATABLE programs.

```bash
# Baselines (spirv-peephole tip, pre-arena):
#   sq2core inline hash:  -1975039029
#   galaxy GPU hash:      799a92c55b6b3805

# Post-change:
python -m mcl tests/sq2core.ergo -o /tmp/sq2core_post
/tmp/sq2core_post                       # must still print -1975039029

python -m mcl --target spirv --precision f32 --no-split \
    -N 100000 -M 100000 -o /tmp/galaxy_post galaxy_structured.ergo
ERGO_HASH_FINAL=1 /tmp/galaxy_post --frames 100 -N 100000 -M 100000
# must print ERGO_FINAL_HASH=799a92c55b6b3805
```

If either hash changes, the arena emit gate (Edit 1) is wrong — it's
emitting arena code for programs that don't use ALLOCATABLE, which
shouldn't change behavior but might be affecting the binary somehow
(BSS layout, ASLR, debug symbols). Investigate.

### Test 4: no libc malloc in generated binary (REQUIRED)

Build an ALLOCATE-using program. Check both the generated C and the
final binary for malloc/free calls.

```bash
# Emit C and grep for libc allocator calls:
python -m mcl tests/alloc_smoke.ergo --emit-c | grep -E "malloc\(|free\("
# expected: 0 matches

# Build and check the binary:
python -m mcl tests/alloc_smoke.ergo -o /tmp/alloc_smoke
objdump -d /tmp/alloc_smoke | grep -c "call.*malloc"
# expected: 0
```

This is the load-bearing test for the regression fix. If this number
is anything but zero, the malloc lowering is still firing somewhere.

Pre-arena reference: this program currently emits one `malloc(` and
one `free(` in C, and the binary has one `call.*malloc` instruction.

### Test 2: ALLOCATABLE programs produce correct results (DEFERRED)

**Deferred** until `tests/allocate_bench.ergo` exists in the
comparison work. The arena_smoke.ergo program above provides a
minimum sanity check (the SUM_A = 2525.0 output must be unchanged
pre/post), but a real benchmark target is needed for end-to-end
performance validation.

### Test 3: arena exhaustion (DEFERRED)

**Deferred** until `tests/allocate_bench.ergo` or a dedicated
exhaustion test exists. Confirms the bounds check + abort path
in the arena lowering fires correctly.

### Test 5: re-run the allocator comparison benchmark (DEFERRED)

**Deferred** until the comparison brief lands its benchmark
infrastructure. This is the payoff measurement (libc cost vs.
intrinsic cost), but it requires the comparison work to provide
the baseline numbers.

## What not to do

- **Don't grow the arena into a real allocator** (freelist, slab,
  etc.) in this PR. Bump is the spec. If a future workload needs
  free-and-reuse, that's a different brief and probably a different
  allocator (V22-style).

- **Don't make the arena thread-safe** unless you also need it.
  Ergo is single-threaded on CPU; the atomic isn't load-bearing
  yet. Add it when it's needed, not preemptively.

- **Don't add `realloc` semantics.** ALLOCATE in Ergo doesn't resize
  — Part 2 of the spec says "Assignment never resizes arrays."
  The arena doesn't need to handle reallocation because Ergo doesn't
  expose it.

- **Don't touch the GPU allocation path.** vk_host.c's
  `vkAllocateMemory` is the GPU-side pattern. It happens at startup
  only, not in the hot path. It's not in the same regression class
  as the CPU malloc. Different brief, if ever.

- **Don't optimize the arena layout for cache behavior** (e.g., per-
  thread arenas, NUMA-aware placement). 64-byte alignment is enough
  for now. Optimization is a follow-up if profiling shows arena
  contention is real.

- **Don't keep the malloc lowering behind a flag** ("--use-malloc"
  or similar). The malloc is a regression; the fix is to remove it.
  A flag preserves the regression and creates two paths to maintain.
  Hard remove.

## Open questions for the implementer

1. **Is there an existing DEALLOCATE lowering?** Grep both codegen
   files. If yes, change it to no-op. If no, this work doesn't add
   one — DEALLOCATE in source becomes nothing in generated C.

2. **Are there callers of `compile_source` that test ALLOCATE
   behavior?** Grep `tests/` for ALLOCATABLE. Any existing test that
   exercises ALLOCATE will be validating the new lowering — that's
   good. If no tests exist, the comparison work's
   `tests/allocate_bench.ergo` is the first one.

3. **Is the arena's `__attribute__((aligned(64)))` portable?**
   GCC and Clang accept it; MSVC doesn't, but Ergo doesn't target
   MSVC. If RISC-V or ARM GCC toolchains have issues, fall back to
   `alignas(64)` from `<stdalign.h>` (C11, already required by
   stage 1 of x86 determinism).

4. **Should the arena be zero-initialized?** BSS is automatically
   zeroed by the loader. So yes, for free. ALLOCATE returning zeroed
   memory may or may not match malloc's behavior (malloc doesn't
   guarantee zero, but BSS does), but Ergo source shouldn't be
   relying on either. Document the guarantee: arena ALLOCATE returns
   zeroed memory.

5. **What's the right default arena size?** 1 GiB is generous and
   defensible (modern systems have it, BSS is lazy). If targeting
   embedded RISC-V where 1 GiB doesn't exist, the `--arena-size`
   flag handles it. Default should be the common-case size, not the
   minimum.

## Sequencing

Single PR, four commits suggested:

1. `codegen: add arena declaration when ALLOCATABLE is used` (Edit 1).
2. `codegen: replace malloc with arena bump in ALLOCATE lowering`
   (Edits 2-4).
3. `cli: add --arena-size flag` (Edit 6).
4. `spec: document arena-backed ALLOCATABLE semantics` (Edit 5).

Each commit independently testable. Commit 1 alone is a no-op (arena
declared but unused). Commits 1+2 deliver the fix. Commits 3 and 4
are polish.

## Reporting back

After implementation:

- Hash of `tests/sq2core.ergo` (must match -1975039029).
- Hash of `tests/allocate_bench.ergo` pre vs post (must match).
- Output of `objdump -d ... | grep -c "call.*malloc"` (must be 0).
- Re-run of B.1 / B.2 from the comparison brief. Report the
  delta between pre-fix and post-fix ALLOCATE measurements.

The expected story: Ergo's ALLOCATE column in the comparison table
moves from "libc malloc" (slow, syscalls under contention) to
"bump-from-arena" (a few instructions, no syscalls). If the post-fix
number isn't within 2-3× of the CPU bump baseline, something in the
lowering is wrong — the arena bump *is* a bump allocator, so it
should hit the same floor.
