# Compiler determinism for V8

Empirical findings from compiling the V8 slab allocator (Viviani-scatter
warp-permanent slab GPU allocator) under `nvcc 13.1` for `sm_75`
(RTX 2060). The question is the same as V22's: **which compiler choices
serve V8's determinism goals, where is the compiler making decisions
the source doesn't constrain, and where is there room for improvement?**

V8 is fundamentally different from V22 — it's a GPU allocator, not a
CPU geometry primitive — so determinism takes a different shape:

- **Bit-exact output** (V22's concern) doesn't apply: the allocator
  returns pointers, not floats.
- **Warp-uniform control flow** is the determinism that matters. Any
  divergence breaks the "all 32 lanes execute the same instruction at
  the same time" guarantee, which V8 relies on for correctness (the
  `__ballot_sync` / `__shfl_sync` primitives deadlock otherwise).
- **Register usage and occupancy** are deterministic-throughput concerns.
  A kernel that's register-bound on one GPU and not another runs at
  different speeds depending on what else is launched alongside it.
- **SASS reproducibility**: same source + same nvcc gives bit-identical
  SASS (verified — diff is empty). That part is solid.

See `../asm/aizawa_slab_test.{ptx,sass}` for the compiled outputs.

## TL;DR

| Aspect | Status | Notes |
|---|---|---|
| SASS reproducibility across rebuilds | **Solid** | Bit-identical |
| Zero register spills | **Solid** | ptxas reports 0 bytes spill stores/loads |
| Warp-uniform control flow on hot path | **Solid** | `__ballot_sync` correctly placed outside divergent branches |
| Register count vs occupancy | **Concern** | 50–56 regs/kernel caps SM_75 occupancy at ~50% |
| Runtime-`cls` branch chains | **Concern** | `slab_stress` keeps if-chain per allocation |
| `held[4]`/`hcls[4]` arrays in local memory | **Concern** | 80-byte stack frame, ~44 STL/LDL per kernel |
| Outer-loop unrolling decisions | **Mixed** | Compiler chose for you; might not be what you want |

Recommended near-term changes (in priority order):

1. **Pin block size with `__launch_bounds__`** to give ptxas a register
   budget. Currently no kernel has bounds hints; ptxas picks whatever
   keeps register pressure free. Forcing `__launch_bounds__(256, 2)`
   would cap registers and double minimum occupancy, possibly with a
   small spill cost.
2. **Specialize `cls` in `slab_stress_kernel`** with a templated kernel
   or a `switch` on a compile-time-known class set, so the
   `slab_slots`/`slab_init_bitmap` if-chain folds away per call.
3. **Try `#pragma unroll 1`** on `slab_correctness_kernel`'s outer
   class loop to see if the SASS halves with no measurable harm. The
   compiler currently emits three specialized copies; the workload's
   `iters`-bound inner loop probably amortizes setup either way.

## What's deterministic and works well

### Inlining is uniform and complete

The V8 source declares zero `__forceinline__`, zero `__noinline__`, and
zero `#pragma unroll` directives. Despite that:

- All device functions (`viviani_slab_alloc`, `viviani_slab_free`,
  `slab_slots`, `slab_stride`, `slab_init_bitmap`, scatter helpers)
  are inlined into the 5 entry kernels.
- PTX has **zero `.func` declarations** — only `.entry` kernels exist
  after lowering.

This is consistent and predictable. The compiler made the same call
every time: inline everything, let the kernel grow. There's no surprise
"this version got inlined, that one didn't" failure mode, which is
exactly what you want from a deterministic build.

The cost (5 fat kernels at 50–56 registers each) is real, but it's a
**predictable** cost. You know exactly what the trade-off is.

### Zero register spills

ptxas reports `0 bytes spill stores, 0 bytes spill loads` for every
kernel. The 50–56 registers/kernel is the *working set after inlining*,
not the result of running out of registers. This means:

- The compiler isn't silently moving data to local memory to fit.
- Behavior is predictable across launches.
- The register count maps directly to a known occupancy bound.

### Warp-uniform control flow is preserved

The hot path in `viviani_slab_alloc` is careful to call `__ballot_sync`
**outside** any divergent if-block:

```cuda
// __ballot_sync MUST be called by ALL lanes unconditionally —
// it is a warp-wide barrier. Calling it inside a divergent if-block
// deadlocks lanes that took different branches.
bool succeeded = (old_bmap & mask) != 0u;
uint32_t winners = __ballot_sync(warp_mask, succeeded);
if (succeeded) { ... }
```

The SASS confirms this: `VOTE.ANY` (the ballot lowering) sits at the
top of the post-claim block, ahead of the `@P0 BRA` for the success
branch. The source intent translated faithfully through nvcc.

### SLAB_ATOMIC_* portability macros lower predictably

`SLAB_ATOMIC_AND` → `ATOM.E.AND.STRONG.GPU`, `SLAB_ATOMIC_CAS` →
`ATOM.E.CAS.STRONG.GPU`, `SLAB_ATOMIC_ADD_ULL` →
`ATOM.E.ADD.64.STRONG.GPU` consistently. The `STRONG.GPU` scope is
sm_70+ release-consistency — the strongest device-scope ordering nvcc
emits without `__threadfence_system`. For a single-GPU allocator this
is correct and the strongest guarantee available.

## What's compiler-chosen and might need improvement

### Register count: 50–56 per kernel caps occupancy

| Kernel | Registers | Theoretical occupancy on SM_75 |
|---|---:|---|
| `slab_stress_kernel` | 56 | ~14 warps/SM = 43% |
| `slab_tput_kernel` | 56 | ~14 warps/SM = 43% |
| `slab_correctness_kernel` | 50 | ~16 warps/SM = 50% |
| `viviani_slab_bench_kernel` | 54 | ~14 warps/SM = 43% |

SM_75 has 64K registers/SM and 32 warps/SM max. At 56 regs/thread × 32
threads/warp = 1792 regs/warp, you fit `65536 / 1792 ≈ 36` warps worth
of register state, but SM_75 caps at 32 warps. To reach max occupancy
you need ≤32 regs/thread (64 regs/warp pair).

Currently nothing in the source asks ptxas to compress registers.
Adding `__launch_bounds__(blockSize, minBlocksPerSM)` would let ptxas
trade some spills for higher concurrency. For an allocator whose hot
path is **dominated by memory ops** (atomic CAS/AND/OR on superblock
bitmaps), running more warps per SM to hide those latencies often
wins even if each warp gets slightly slower from spills.

The current behavior is the right *default* (no spills, predictable
working set) but should probably be tested with:

```cuda
__global__ __launch_bounds__(256, 2)
void slab_stress_kernel(...)
```

…to force ptxas to fit into 32 regs (64K / (32*32*2 blocks)) and see
whether the throughput improves.

### Runtime-`cls` keeps the if-chain in slab_stress_kernel

In `slab_stress_kernel`:

```cuda
int c = (int)((global_warp_id + i) % (uint32_t)SLAB_CLASSES);
void* ptr = viviani_slab_alloc(pool, c, ...);
```

`c` is runtime-computed, so when `viviani_slab_alloc` inlines and
calls `slab_slots(cls)`, the source's `if (cls == 0) return 32u; ...`
chain stays in SASS as:

```
ISETP.EQ.U32.AND P0, PT, R10, 0x1, PT
ISETP.EQ.U32.AND.EX P0, PT, R11, RZ, PT, P0
```

The SASS shows **22 such ISETP.EQ comparisons** in `slab_stress_kernel`,
some per iteration of the outer alloc loop. Each comparison is cheap
individually, but they sit in the hot path and prevent ptxas from
folding the `slab_init_bitmap`, `slab_slots`, `slab_stride`,
`slab_sbs_per_warp_alloc` constants away.

By contrast, in `slab_correctness_kernel` where `c` is the loop index
of the outer `for(c=0;c<SLAB_CLASSES;c++)` loop, the compiler:

- Unrolled the outer loop (`SLAB_CLASSES = 3`, constant).
- Specialized each unrolled copy for that particular `cls`.
- Folded all the `slab_slots(0) = 32`, `slab_init_bitmap(0) = 0xffffffff`
  etc. into immediate constants.

You can see the specialization in SASS: the cls=0 region of
`slab_correctness_kernel` only references `0xffffffff` (init bitmap for
class 0), the cls=1 region only references `0x7fffffff`, the cls=2
region only references `0x7fff`. Branch chain: gone.

**Improvement opportunity**: if `slab_stress_kernel`'s round-robin
over classes is just a benchmark choice (not a fundamental property
of stress-testing), running 3 separate single-class instances would
let the compiler specialize each. The same goes for any production
caller that knows its class at compile time — pass it as a template
parameter:

```cuda
template <int CLS>
__global__ void my_kernel(SlabPool* pool, ...) {
    void* p = viviani_slab_alloc(pool, CLS, ...);  // cls folds
}
```

Worth a benchmark before doing it across the board, but the SASS
clearly shows the compiler can deliver a measurably smaller hot path
when `cls` is known.

### `held[4]`/`hcls[4]` live in local memory

`slab_stress_kernel` has an 80-byte stack frame holding:

```cuda
void* held[4] = {nullptr};   // 4 * 8 = 32 bytes
int   hcls[4] = {0};         // 4 * 4 = 16 bytes
```

SASS confirms: 16 `STL.128` (128-bit local stores) and 28 `LDL` (local
loads) in the kernel. The compiler emits vectorized 16-byte writes
when zero-initializing, but the array slots are accessed by
runtime-variable index `held[hcnt]`, which forces local memory because
GPU registers aren't addressable.

This is **not a compiler bug** — it's how indirect indexing has to
work on hardware without addressable register files. The fix has to
come from the source:

```cuda
// Instead of:
held[hcnt] = ptr;
// Use explicit unroll:
switch (hcnt) {
    case 0: held0 = ptr; break;
    case 1: held1 = ptr; break;
    case 2: held2 = ptr; break;
    case 3: held3 = ptr; break;
}
```

…which gives the compiler 4 scalar `void*` locals it can keep in
registers. Ugly, but if the 80-byte stack frame ever shows up as a
bottleneck (it's local memory traffic, which on SM_75 is global memory
with L1 caching — much slower than registers), this is the rewrite.

For now, the 80-byte frame is **deterministic** (same allocation
strategy every build) but **suboptimal**.

### Outer-loop unrolling: compiler chose, results vary

`slab_correctness_kernel` outer loop:

```cuda
for (int c = 0; c < SLAB_CLASSES; c++)
    for (uint32_t i = 0; i < iters; i++)
        // alloc + write + verify + free
```

The compiler **fully unrolled the outer 3-iteration loop** and emitted
three specialized inner-loop bodies. This doubled the kernel size
relative to `slab_stress_kernel` (2864 SASS instrs vs 1512).

Additionally, *inside each unrolled cls=k copy*, the inner `attempt < n_positions`
retry loop got further unrolling decisions made on top:

- For cls=1 (n_positions=9): **9 ATOM.AND** in a row — fully unrolled.
- For cls=2 (n_positions=6): **6 ATOM.AND** in a row — fully unrolled.
- For cls=0 (n_positions=18): **only 1 ATOM.AND**, kept as a loop —
  ptxas decided 18 iterations was too many to unroll.

That asymmetric decision is invisible from the source. It's the
heuristic working as designed — but it means **the cls=0 path performs
differently from cls=1/cls=2** in a way the source code doesn't
suggest. For a deterministic-workload allocator that should treat all
size classes uniformly, this is worth knowing.

To take control:

```cuda
#pragma unroll 1   // disable inner-loop unrolling, uniform behavior
for (uint32_t attempt = 0; attempt < n_positions; attempt++) { ... }
```

…or the opposite, force unroll:

```cuda
#pragma unroll
for (uint32_t attempt = 0; attempt < n_positions; attempt++) { ... }
```

(The latter only helps when `n_positions` is a compile-time constant
or the compiler can prove a bound — same situation as `cls`-specialization.)

### `lineinfo` keeps source correlation, no performance cost

The Makefile uses `-lineinfo`, which embeds source-line metadata
without inhibiting optimization. The SASS dumps include comments like

```
/*1fe0*/ ATOM.E.AND.STRONG.GPU PT, R18, [R18], R28 ;
```

…which `cuobjdump --dump-sass --dump-elf-symbols` can correlate back
to specific source lines via the DWARF metadata. This is the right
default for an allocator: debug info available, optimization unaffected.

## What V8 does *not* expose to compiler choice

Several things are nailed down by the source and won't be reinterpreted:

- **`SLAB_SBS_PER_WARP = 18`**: defined as `#define`, not a parameter.
  ptxas can't change it. The choice of 18 = LCM(1,2,3) × 3 is
  algebraically required for the lane/slot decomposition to work, so
  it shouldn't be a variable.
- **Bitmap layout** (`slab_init_bitmap`): the 32-bit, 31-bit, 15-bit
  bitmasks are constants returned by the helper. No way for the
  compiler to "optimize" them differently.
- **Atomic semantics** (`atomicAnd`, `atomicOr`, `atomicCAS`): nvcc
  always lowers these to `ATOM.E.<op>.STRONG.GPU`. No "relaxed"
  variants slip in unless the source uses `__nanosleep` or the new
  `cuda::atomic<...>` types with explicit memory_order.
- **`__syncwarp(mask)`**: lowered to `WARPSYNC`, can't be elided or
  reordered around.

These are V8's **load-bearing determinism guarantees** and the
compiler respects them all.

## Comparison to V22

The two allocators end up at opposite ends of the determinism spectrum:

| | V22 (Squaragon) | V8 (Slab) |
|---|---|---|
| Concern | Bit-exact float math | Warp-uniform control flow + atomic ordering |
| Threat model | `-ffast-math` reassociation | Divergent `__ballot_sync` / register spills |
| Hand-written SIMD | Yes; **needed** for 2.25× over scalar under strict IEEE | Yes (warp-cooperative ops) |
| What the compiler chose | Inlining, vertex packing into .LC pool | Inlining, register count, unroll decisions |
| Where source forced its hand | `static inline` headers, `__m128` types | `__syncwarp` placement, `__activemask` use |
| What's left to compiler heuristic | Auto-vectorization (correctly declined) | Register cap, unroll thresholds, branch folding |

Both allocators are determinism-conscious in their source; V22 has
made the explicit floating-point decisions, V8 has made the explicit
warp-cooperative decisions. The remaining surface where the compiler
gets to choose for V8 is **smaller** than for V22, but more impactful:
register allocation drives occupancy, which drives end-to-end
throughput at scale.

## Recommendations summary

For V8's deterministic-workload goals:

### Keep
- Current build flags: `-O3 -arch=sm_75 -lineinfo --ptxas-options=-v`.
  These give optimization + source correlation + visibility into
  ptxas's decisions without changing the semantics.
- Zero spills as a hard requirement. Watch `ptxas info` output during
  builds — if "spill stores" goes above 0, something regressed.
- All `__ballot_sync` / `__shfl_sync` / `__syncwarp` calls outside
  divergent regions. The current source is careful here; future
  changes should preserve this.

### Try
- `__launch_bounds__(blockSize, 2)` on each entry kernel. Bench
  before/after. Likely a throughput win on SM_75 even with small
  spill cost.
- Template-specialize callers of `viviani_slab_alloc` on `cls` where
  the size class is known at launch time. Folds away the
  `slab_slots`/`slab_init_bitmap` if-chains on the hot path.

### Investigate
- The asymmetric unroll behavior in `slab_correctness_kernel` (cls=0
  unrolls differently from cls=1 and cls=2). If this causes measurable
  variance in correctness-test runtime per class, force uniform
  behavior with `#pragma unroll 1`.
- Whether the `held[4]`/`hcls[4]` local-memory traffic in
  `slab_stress_kernel` shows up as a bottleneck. If so, manually
  scalarize the ring buffer.

### Don't
- Don't add `--use_fast_math` to nvcc — same family as V22's
  `-ffast-math`. The slab allocator doesn't do floating-point math
  on the hot path anyway, so the win would be marginal, but the
  Viviani scatter computation uses `sinf`/`cosf` and `__use_fast_math`
  would substitute approximate versions. The scatter is supposed to be
  reproducible; don't compromise it.
- Don't use `volatile` to "force re-reads" of `sb->bitmap` — the
  atomic ops already carry the memory ordering you need, and
  `volatile` would inhibit other optimizations without buying anything.
- Don't downgrade `STRONG.GPU` ordering. The current strength is
  exactly what a multi-warp single-GPU allocator needs.

## Reproducing these measurements

```bash
cd Testing
make asm/aizawa_slab_test.{ptx,sass,host.s}
# ptxas info appears in the build log; the SASS dump is the canonical
# artifact for inspecting compiler choices.
```

To verify reproducibility:

```bash
cp asm/aizawa_slab_test.sass /tmp/before.sass
rm asm/aizawa_slab_test.sass asm/aizawa_slab_test.elf
make asm/aizawa_slab_test.sass
diff /tmp/before.sass asm/aizawa_slab_test.sass    # should be empty
```

---

## Summary

V8 is in good shape for determinism. The compiler is making consistent
inlining decisions, zero spills, faithful lowering of warp-cooperative
primitives, and bit-identical SASS across rebuilds. The places where
the compiler is making choices the source doesn't constrain —
register count, branch folding on runtime `cls`, asymmetric retry-loop
unrolling — are all **predictable** in their inconsistency, in the
sense that you can read the SASS and see exactly what was chosen.

What V8 lacks compared to V22 is the explicit "I'm pinning this
decision" annotations. V22's `__m128` types pin SIMD width; V8 has no
equivalent of `__launch_bounds__` to pin register/occupancy targets.
Adding those annotations would give the slab allocator the same level
of compile-time determinism V22 has, without changing any semantics
that matter.

Unlike V22, **`--use_fast_math` is not the trap** for V8 — the slab
allocator's hot path is integer atomics, not floats. The trap for V8
is **letting the compiler choose register count and unroll factor for
you**, which it currently does, and which works fine on RTX 2060 but
may not on a different SM.
