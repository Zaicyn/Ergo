# Compiler determinism for GEO

Empirical findings from compiling the GEO prototype allocators
(`geo_32D_1024_streams.cu` and `geo_min.cu`) under `nvcc 13.1` for
`sm_75`. These are early-prototype benchmarks of `cudaMallocAsync`
with host-side memoization/binning, not standalone allocators — and
that fundamentally changes what determinism means for them.

See `../asm/geo_min.{ptx,sass,host.s}` and
`../asm/geo_32D_1024_streams.{ptx,sass,host.s}`.

## TL;DR

GEO compiles cleanly and the compiler made all the right calls. The
problems are **in the source**, not the codegen:

| Aspect | Status | Notes |
|---|---|---|
| GPU code (`touch_kernel`) | **Solid** | 11 SASS instructions; PTX byte-identical between the two files |
| Host code compilation | **Solid** | Same nvcc → host-asm pipeline as V8, no surprises |
| Determinism of `cudaMallocAsync` itself | **Outside your control** | The allocator under benchmark is the CUDA runtime, not GEO |
| Dead code in `geo_min.cu` | **Source bug** | 8192 trig-table entries computed at startup, never read |
| Stack frames | **Source-imposed** | 86 KB / 152 KB per `run_32D` call from compile-time-sized arrays |
| CHECK macro shadowing | **Source bug** | `cudaError_t err = err;` shadows outer scope; nvcc warned and we ignored |
| Identity of the two files | **Confused** | They're two iterations of the same allocator, not two designs |

The bottom line: **GEO doesn't have compiler-determinism problems
worth solving because the host-side `cudaMallocAsync` interplay is
the real workload, and nothing the compiler does to the C++ wrapper
materially affects it.** Real fixes are source cleanups, not flag
changes.

## What GEO actually is

Reading `run_32D` in either file reveals the design: it's a
*benchmark harness* that runs 1024 concurrent CUDA streams, each
asking for one of 4 fixed buffer sizes per cycle, and times how
long `cudaMallocAsync`/`cudaFreeAsync` takes when the host-side
code does or doesn't intervene with:

- **Memoization**: keep a per-stream LRU of "held" pointers and
  reuse them when a size matches.
- **Binning**: `cycle % 4` selects the size from `{64, 4096,
  256KB, 64MB}`.
- **Motif protection**: hold the pointer (don't free) when the
  allocation rate or counter pattern hits a threshold.

The CUDA kernel is `touch_kernel`, which writes one byte per
thread to dirty the page. The PTX/SASS for this kernel is
**byte-identical between the two files** — the diff is one line
(the embedded source filename).

What differs between the two files is the **host-side benchmark
parameters and the dead trig-table code in `geo_min.cu`**.

## The GPU side is trivial and consistent

`touch_kernel` is 11 SASS instructions on sm_75:

```
IMAD.MOV.U32         R1, RZ, RZ, c[0x0][0x28]         ; stack pointer
S2R                  R2, SR_CTAID.X
S2R                  R5, SR_TID.X
IMAD                 R2, R2, c[0x0][0x0], R5          ; idx = blockIdx*blockDim + tid
ISETP.GE.U32.AND     P0, PT, R2, c[0x0][0x168], PT    ; cmp low half
SHF.R.S32.HI         R3, RZ, 0x1f, R2                 ; sign-extend
ISETP.GE.U32.AND.EX  P0, PT, R3, c[0x0][0x16c], PT, P0 ; cmp high half (Turing has no 64-bit cmp)
@P0 EXIT
ULDC.64              UR4, c[0x0][0x160]               ; base ptr
STG.E.U8.SYS         [R2.64+UR4], R5                  ; write byte
EXIT
```

8 registers, no stack frame, no atomics, no spills. The fact that
PTX is byte-identical between the two files means **whatever you
change in `run_32D`'s host logic, the kernel emission is
unaffected** — which is correct, since `touch_kernel` doesn't
depend on `CYCLES` or `PER_STREAM_MAX_HOLD`.

This is the cleanest determinism story in the entire codebase:
trivial kernel, deterministic compilation, no compiler choices to
worry about.

## The host code is where the prototypes live

`run_32D` is **445 instructions in geo_min, 494 in geo_32D**, all
host x86. Most of those instructions are the memoization-loop
walking the `holds[s][h]` and `hold_sizes[s][h]` arrays — 8KB of
pointer-chasing per cycle iteration.

The compiler honored the source faithfully. The compile-time
constants (`CYCLES=256` vs `200`, `PER_STREAM_MAX_HOLD=4` vs `8`)
got inlined as immediate operands; loops were unrolled where
profitable; `cudaMallocAsync` etc. lowered to PLT calls as
expected. **There are no surprises in the codegen.**

The interesting question for GEO is whether the *source choices*
are good — and several of them aren't.

## Problem 1: 8 KB of dead trig-table work at startup

`geo_min.cu` adds a 4096-entry sin/cos lookup table:

```c
static float sin_table[TRIG_TABLE_SIZE];
static float cos_table[TRIG_TABLE_SIZE];

void init_trig_tables() {
    if (trig_tables_initialized) return;
    for (int i = 0; i < TRIG_TABLE_SIZE; ++i) {
        float theta = (float)i * TRIG_TABLE_STEP;
        sin_table[i] = sinf(theta);   // 4096 sinf calls
        cos_table[i] = cosf(theta);   // 4096 cosf calls
    }
    ...
}

inline float fast_sinf(float x) { ... return sin_table[idx]; }
inline float fast_cosf(float x) { ... return cos_table[idx]; }

int main() {
    ...
    init_trig_tables();   // called from main
    ...
}
```

The tables are populated at startup. `init_trig_tables` runs 8192
trig function calls. **`fast_sinf` and `fast_cosf` are never
called from anywhere else in the file.** The tables are written
and never read.

The compiler emitted `_Z16init_trig_tablesv` because it can't
prove the writes are dead (the static tables have external-visible
addresses through their symbol). 8192 trig calls run on every
invocation.

This is harmless to the benchmark numbers (the timer doesn't start
until after `init_trig_tables` returns), but it's a clear sign
that the file is a work-in-progress: someone added the LUT
infrastructure but never wired it into the allocator path. Either
delete the dead code or wire it up.

`geo_32D_1024_streams.cu` doesn't have this — it's the **earlier**
version, before the trig table was bolted on.

## Problem 2: Huge stack frames from C arrays sized by macros

The host-side bookkeeping for 1024 streams × 4 (or 8) holds is
allocated **on the stack** as plain C arrays:

```c
void*    holds[NUM_STREAMS][PER_STREAM_MAX_HOLD]    = {};   // 32 or 64 KB
size_t   hold_sizes[NUM_STREAMS][PER_STREAM_MAX_HOLD] = {}; // 32 or 64 KB
int      hold_counts[NUM_STREAMS]    = {};                  // 4 KB
float    alloc_rates[NUM_STREAMS]    = {};                  // 4 KB
int      alloc_counters[NUM_STREAMS] = {};                  // 4 KB
cudaStream_t streams[NUM_STREAMS];                          // 8 KB
```

The compiler reserves the whole frame on entry with one `sub rsp`:

- `geo_min` (MAX_HOLD=4): `sub rsp, 86336` → **84 KB**
- `geo_32D` (MAX_HOLD=8): `sub rsp, 151904` → **148 KB**

This is deterministic — every call to `run_32D` allocates exactly
the same frame — but it's:

1. **Close to typical container stack guards** (some default to
   512 KB or 1 MB per thread; running this on the main thread is
   fine, but a worker pool with small stacks would crash).
2. **Forces zero-init via `memset`** because of the `= {}`
   initializers. The compiler emits 5 `memset` calls at function
   entry to clear the arrays. That's 144 KB of memory traffic
   before the timer even starts.
3. **Cache-cold on every entry**. The stack pages aren't
   in the data cache when the function is called; you pay the
   miss latency on first access.

The cleaner pattern is to allocate these on the heap:

```c
auto* holds       = new void*[NUM_STREAMS * PER_STREAM_MAX_HOLD]();
auto* hold_sizes  = new size_t[NUM_STREAMS * PER_STREAM_MAX_HOLD]();
// ... pass to runner, delete at end
```

…or to make them `static` so they live in BSS and are zero-init
once at program startup, not on every `run_32D` invocation. For a
benchmark where `run_32D` is called twice (with and without
protection), BSS is simplest and fastest.

The compiler can't make this decision for you — these are
explicitly-sized arrays at the source level, so the frame is
what the source asks for.

## Problem 3: The CHECK macro has a real bug

```c
#define CHECK(call) { \
    cudaError_t err = call; \
    if (err != cudaSuccess) { \
        fprintf(stderr, "CUDA error %s:%d: %s\n", __FILE__, __LINE__, cudaGetErrorString(err)); \
    } \
}
```

Now look at how it's called in the OOM cleanup path:

```c
cudaError_t err = cudaMallocAsync(&ptr, size, streams[s]);
if (err == cudaErrorMemoryAllocation) {
    had_oom = true;
    continue;
}
CHECK(err);   // ← line 118: expanded to `cudaError_t err = err;` which shadows
```

The outer scope has `err` from the `cudaMallocAsync` call. When
`CHECK(err)` is expanded, the macro creates a *new* `cudaError_t
err` initialized from… itself. C semantics say this initializes
from the outer-scope `err` (the name in the initializer is the
outer one because the new `err` isn't visible until after the
declarator), so it actually works — but it's the textbook
`int x = x;` warning case, and nvcc flagged it:

```
warning #549-D: variable "err" is used before its value is set
```

Both `geo_min.cu` (line 118) and `geo_32D_1024_streams.cu`
(line 87) have this. Fix:

```c
#define CHECK_ERR(e) do { cudaError_t _err = (e); \
    if (_err != cudaSuccess) fprintf(stderr, ...); } while(0)
```

…using a name that can't collide with caller locals.

## Problem 4: The two files are two iterations, not two designs

The `Makefile` treats `geo_32D_1024_streams.cu` and `geo_min.cu`
as separate targets, and the GPU PTX confirms they share
`touch_kernel` byte-for-byte. The diff between them shows:

- `geo_32D_1024_streams.cu`: `CYCLES=200`, `MAX_HOLD=8`, three
  separate booleans (`use_motif`, `use_binning`, `use_memo`) all
  driven by `use_protection`.
- `geo_min.cu`: `CYCLES=256`, `MAX_HOLD=4`, all protections always
  on (the booleans are collapsed), plus the dead trig table.

These look like two checkpoints of the same allocator's
evolution, not two distinct designs being benchmarked. The
`Testing/` setup compiles both for asm inspection, which is fine,
but for actual benchmarking you probably want to pick one,
delete the other, and keep refactoring forward.

## What's *not* a problem in GEO

Several things you might worry about are actually fine:

- **`-O3` host optimization**: nvcc passes this through to g++,
  which inlined `fast_sinf`/`fast_cosf` (would be valuable if
  anything called them), inlined the size-class table lookups,
  and unrolled the memoization scan loop. All consistent.
- **CUDA stream creation**: 1024 `cudaStreamCreate` calls. This is
  expensive (~50 µs each on most systems) but the timer doesn't
  start until after.
- **`cudaMallocAsync` semantics**: The allocator under test is
  the CUDA driver's memory pool. Whatever determinism guarantees
  the driver provides is what GEO measures; no compiler flag
  changes that.
- **`global_held_bytes` as `__device__ __managed__`**: this is
  Unified Memory state used from the host. nvcc lowered it
  correctly (managed variable registration in
  `_ZL24__sti____cudaRegisterAllv`); no surprises.

## Comparison to V8 and V22

| | V22 | V8 | GEO |
|---|---|---|---|
| What the allocator does | Float invariant math | GPU slab claim/release | Host-side cache around `cudaMallocAsync` |
| Real work happens in | C SIMD intrinsics | CUDA atomics + warp ops | CUDA runtime calls |
| Determinism threat | `-ffast-math` reassociation | Register count, branch folding | None from compiler; **source choices** are the threat |
| Compiler choices that matter | Auto-vectorization, FMA fusion | Inlining, register cap, unroll | Inlining (works), stack layout (forced by source) |
| Hot path size | 67 SSE instructions | 1500+ SASS per kernel | 1 host call to `cudaMallocAsync@PLT` |

GEO is the simplest case for compiler determinism precisely
because the compiler isn't doing much interesting work. Everything
expensive happens inside `cudaMallocAsync`, which is a closed-source
PLT-linked library call. The compiler can't optimize it, can't
inline it, and can't reorder it relative to other CUDA calls (it
might have observable side effects).

What GEO loses in compiler-determinism interest, it gains in
**runtime-determinism uncertainty**: `cudaMallocAsync`'s timing
varies with the driver's internal memory pool state, fragmentation,
prior allocations, and concurrent activity on the GPU. None of
that is captured in the SASS dump.

## Recommendations summary

GEO is a prototype, so most of these are "if you keep working on
this, do these things":

### Source fixes
1. **Delete the dead trig table code in `geo_min.cu`** (or wire it
   into the scatter computation if that was the intent).
2. **Move the per-stream arrays to BSS or the heap.** Either
   declare them `static` (one zero-init at program load) or `new[]`
   them (one heap alloc per call, but no stack pressure).
3. **Fix the `CHECK` macro** to use a `_err` local that can't
   collide with caller variables.
4. **Decide what to do about the two files.** If they're two
   stages of the same evolution, archive one. If they're meant to
   compare two strategies, give them distinct kernel names so the
   PTX isn't redundant.

### Compiler / build
- The current Makefile flags (`-O3 -arch=sm_75 -lineinfo
  --ptxas-options=-v`) are correct. No flag tuning to do.
- Don't add `--use_fast_math`: the trig-table code, if ever
  wired up, exists *because* the author wanted to avoid `sinf`'s
  rounding semantics from glibc. Letting nvcc swap to an
  approximation defeats that.
- Don't bother with PGO / FDO: the benchmark loop is dominated
  by `cudaMallocAsync@PLT` time, not by branch-prediction in the
  host wrapper.

### Don't expect compiler magic
The fundamental thing GEO is measuring — host-side cache
effectiveness against `cudaMallocAsync` — is unchanged by any
compiler flag. The compiler emits a faithful C++ wrapper around
runtime calls; the runtime calls are the cost; the cache logic
is small enough that its asm is exactly what the source says.

## Reproducing these measurements

```bash
cd Testing
make asm/geo_min.{ptx,sass,host.s}
make asm/geo_32D_1024_streams.{ptx,sass,host.s}

# Verify the PTX is byte-identical except for filenames:
diff asm/geo_min.ptx asm/geo_32D_1024_streams.ptx
# (one line: the .file directive)
```

To see the stack frame size for `run_32D`:

```bash
grep -E "sub\s+rsp" asm/geo_min.host.s | head -3
grep -E "sub\s+rsp" asm/geo_32D_1024_streams.host.s | head -3
```

---

## Summary

GEO has the cleanest compiler-determinism story in this codebase —
because there's almost no real work for the compiler to do. The
GPU kernel is trivial, the host code is a wrapper around CUDA
runtime calls, and the constants get inlined as you'd expect.

But the **prototype-quality source** has real issues: dead code,
oversized stack frames, a macro that triggers a compiler warning,
and two files that probably should be one. None of those are
compiler problems — they're places where the source asks the
compiler to do something deterministically, and the compiler
does it, and the result is just not what you wanted.

If V22 is "carefully written code that compilers respect," and
V8 is "carefully written code with compiler-knobs left untuned,"
then GEO is "code where the compiler is the least of your
worries." Fix the source, then come back to it.
