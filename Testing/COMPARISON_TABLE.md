# Allocator comparison — unified table

Three sub-tables comparing four allocation systems on the hardware
documented in [BASELINE.md](BASELINE.md) and
[V8_VS_V22_HEAD_TO_HEAD.md](V8_VS_V22_HEAD_TO_HEAD.md): Ryzen 5 3600
+ RTX 2060.

**Forklift vs bicycle.** V8, V22, and Ergo are not the same kind of
thing. V8 is a runtime GPU allocator; V22 is a CPU geometric primitive
that includes a CPU allocator; Ergo is a deterministic simulation
language whose `ALLOCATABLE` arrays lower to a single CPU bump-arena
emit and whose GPU side has *no runtime allocator at all* — every GPU
array gets one `vkCreateBuffer + vkAllocateMemory` at program init,
and there's no per-frame allocation. Asking "which is fastest" gives
different answers depending on what's being timed. The three
sub-tables below partition the question:

- **Sub-table 1 (steady-state)**: per-op cost in the allocator's hot
  path. Apples-to-apples *within* a hardware class; not comparable
  across CPU/GPU.
- **Sub-table 2 (startup / init)**: one-shot cost per allocation made
  at program init. Where Ergo's design actually lives.
- **Sub-table 3 (features and determinism)**: qualitative comparison
  of what each system provides. Not throughput.

## Sub-table 1: Steady-state allocation throughput

Smaller-is-better in the rightmost column: 1.0× is "at the floor";
<1.0× escapes the floor's contention pattern; >1.0× pays more than
the floor. Each row is referenced against its hardware-class floor
per footnote ⁰: CPU rows against the CPU per-arena bump (0.51
ns/op); GPU rows against GPU Floor B (0.55 ns/lane-alloc).

| System | Throughput | ns/lane-op | × respective floor (ns/op)⁰ | Notes |
|---|---:|---:|---:|---|
| **CPU 1t per-arena bump** | 1.95 G/s | 0.51 | 1.00× (CPU reference) | Load + add + store |
| **CPU 6t per-arena bump** | 11.6 G/s | 0.09 | 0.18× | 5.96× linear scaling |
| **CPU 1t shared atomic** | 232 M/s | 4.31 | 8.5× | Locked RMW dominates |
| **CPU 6t shared atomic** | 158 M/s | 6.33 | 12× | Cacheline ping-pong |
| **V22 hand-SSE 1t** | 89 M/s | 11.2¹ | — | Geometric residual, not alloc |
| **V22 hand-SSE 6t** | 549 M/s | 1.82¹ | — | 17% drift vs prior doc² |
| **Ergo CPU arena** | 1.30 G/s | 0.77 | 1.5×⁵ | Bump + bounds-check + integer-dep chain |
| **GPU bump Floor A** | 35.5 G/s | 0.03 | 0.08× | nvcc warp-aggregated; 1 atomic/warp |
| **GPU bump Floor B** | 2.65 G/s | 0.38 (0.55/lane) | 1.00× (GPU reference) | 1 atomic/lane, per-lane size varied |
| **V8 slab allocator** | 1.73 G/s | 0.58 | 1.05× | Per-lane bitmap atomic³ |
| **cudaMalloc** | ~3 M/s⁴ | ~330 | ~600× | Driver call, not warp-cooperative |
| **Ergo GPU runtime alloc** | N/A | N/A | N/A | No runtime GPU allocator; see Sub-table 2 |

⁰ The "× respective floor" column references two different floors
because CPU and GPU allocation are not directly comparable. CPU rows
use the single-thread per-arena bump from
[BASELINE.md](BASELINE.md) §"CPU bump-allocator floors", measured
at 0.51 ns/op. GPU rows use Floor B from the same doc, measured at
0.55 ns/lane-alloc (after correcting the 64B-equivalent normalization
to actual lane cost). The bare numbers in this column tell a
hardware-normalized story per row; cross-row CPU/GPU comparisons
should reference Sub-table 3 for feature-level differences instead.

¹ V22 measures a 67-instruction geometric residual computation, not
allocation. Included for cross-reference with the V22 head-to-head
doc; the ns/op number is not comparable to allocator rows.

² V22 6t throughput in the head-to-head doc was 469 M/s; current
measurement is 549 M/s. Attributed to OpenMP scheduling improvements
in GCC 15.2.1; single-thread inner loop unchanged within noise.

³ See "The V8 vs Floor B finding" prose section below.

⁴ cudaMalloc baseline is hardcoded in the V8 throughput test from
empirical prior measurement; not re-run in the bump-floor work
because device-malloc from 8192 simultaneous threads runs the GPU
at 100% load for minutes and adds nothing new per the V8 test source.

⁵ Ergo CPU arena at 0.77 ns/alloc vs 0.51 ns/alloc CPU bump floor:
the entire 0.26 ns delta is the per-iter bounds check (`cmp rdx,
1073741824 / ja .L34` in the SASS, fired on every ALLOCATE).
Measured via the `nostore` variant of [baseline_arena.c](baseline_arena.c)
to isolate the allocator pattern from per-iter memory traffic — a
naive bench that wrote to A[0] each iter timed at 12.9 ns/alloc,
25× higher, dominated by DRAM write-for-ownership cost on fresh
cachelines (see Sub-table 2). The honest framing of the 1.5× ratio:
Ergo arena is "a bump plus a bounds check, with the bounds check
costing exactly what a bounds check should cost." The pure-bump
floor would happily run off the end of its arena and into segfault
territory; Ergo's emit catches that and aborts cleanly. The 49%
overhead is the price of not segfaulting. Future predictions about
"cheap" integer dependency-chain ops on Zen 2 should anchor at
~0.25 ns/op, not "negligible" — a calibration point recorded during
Pass 2.

### The V8 vs Floor B finding

V8's per-lane allocation cost (0.58 ns) sits within 5% of Floor B's
per-lane cost (0.55 ns, derived from the 64B-eq normalization). V8
does **not** match Floor A — Floor A is one atomic per warp via
nvcc's automatic warp aggregation, which is a different operation
than V8 performs.

This means: at RTX 2060's hardware atomic throughput ceiling, both
V8 and naive non-aggregated bump saturate the L2 atomic unit. V8's
geometric design (Viviani scatter, per-warp slab ranges,
ballot-coordinated bitmap claims) does not measurably reduce
per-lane atomic cost below the bare-atomic floor on this hardware.

**This is not "V8's geometric design is useless."** It says:

- V8's headline win against cudaMalloc (538×–874×) is achieved by
  being a *per-warp atomic allocator at all*, of which V8 is one
  instance and Floor B is another. Both reach the hardware floor.
  cudaMalloc is wherever a driver-API allocator can sit — orders of
  magnitude away from any per-warp design.
- The geometric design might be load-bearing on hardware where L2
  atomic throughput is lower (older or integrated GPUs), at higher
  concurrency (where contention scales past L2 saturation), or for
  properties other than throughput (the features in Sub-table 3).
- The implementation cost is small relative to what V8 *also*
  provides: slab structure, free-recycle, deterministic SASS. See
  Sub-table 3.

The original V8 head-to-head doc's "538×–874× faster than
cudaMalloc" framing is accurate but underspecified about *why*.
The win is escaping cudaMalloc, not beating bump. A reader choosing
V8 over a hand-rolled bump should expect equivalent per-lane
throughput plus the structural features, not better per-lane
throughput.

## Sub-table 2: Startup / per-allocation init cost

Where Ergo's allocate-once-at-startup design actually lives. Each row
measures cost per allocation made during program initialization, not
in steady state.

| System | Init cost per buffer | Setup cost amortizable? | Notes |
|---|---:|---|---|
| **malloc (libc, glibc)** | ~30 ns⁶ | N/A | Single libc call; backed by sbrk/mmap |
| **V22 SQ2FAL** | ~30 ns | Yes (per-thread) | Scatter LUT + bin advance |
| **V8 viviani_slab_alloc** | ~50 ns | Yes (per-warp) | First range claim adds 100 SASS instr; amortized over warp lifetime |
| **vkAllocateMemory (DEVICE_LOCAL, fixed floor)** | ~162 µs¹⁵ | No | NVIDIA Linux Vulkan per-call overhead, size-independent below ~1 MB |
| **vkAllocateMemory (DEVICE_LOCAL, per-byte slope)** | +19 ns/byte¹⁶ | No | Asymptotic at ≥16 MB; crossover with floor at ~8 MB |
| **vkAllocateMemory (HOST_VISIBLE, per-byte slope)** | +290 ns/byte¹⁷ | No | 15× the DEVICE_LOCAL slope; falsified hypothesis, see footnote |
| **Ergo arena emit (cold, no memory store)** | ~0 ns⁷ | Yes (program lifetime) | Bump + bounds check; overlaps with surrounding work in the loop |
| **+ first-touch (cold cacheline)** | +7.0 ns⁸ | One-time per cacheline | DRAM read-for-ownership when writing fresh memory |
| **+ wrap-revisit (evicted cacheline)** | +5.1 ns⁹ | Avoidable via free/recycle | Revisiting cachelines evicted from L3 after wrap |
| **Ergo GPU init (galaxy_structured @ N=18M)** | ~27.6 ms total¹⁸ | Yes (program lifetime) | 37 buffers, ~300 MB total VRAM committed |

⁶ malloc init cost approximated; not measured in this work.

⁷ "~0" means: no per-arena init step beyond what the OS loader
already does for any BSS-resident allocation. `_ergo_arena[]` is a
file-scope `static char[ERGO_ARENA_BYTES]`; the loader zero-fills
it once at program load (a one-time amortized cost shared with every
other BSS symbol in the binary), and `_ergo_arena_offset` starts at
0. The arena emit's per-iter cost is 0.77 ns when measured against a
register sink (the `nostore` variant of
[baseline_arena.c](baseline_arena.c)) — indistinguishable from the
per-iter accumulator work because the integer ops issue in parallel
with the floating-point work on Zen 2. The 0.77 ns × 1.5× factor
from Sub-table 1 is the bump+bounds-check cost; the "~0" framing
here means there is no separate allocator setup cost on top of that.

⁸ First-touch cost per 64B cacheline (cold): measured at 7.85
ns/iter via the `walk` variant of
[baseline_arena.c](baseline_arena.c) (bump emit + per-iter store to
`A[0]`, no wrap). This is the DRAM read-for-ownership cost when
writing to a fresh cacheline that wasn't in any cache level — a
property of the memory subsystem, not of any allocator. Any
allocator handing out fresh memory pays this; the only way to avoid
it is to reuse already-touched memory (which a free-and-reuse
allocator like V8 can do, and which a bump-only design fundamentally
cannot). This row exists in the table specifically to make that
trade-off visible.

⁹ Wrap-revisit cost (evicted cacheline): measured at 12.95
ns/iter via the `full` variant (bump emit + store + wrap when arena
exhausted), minus the `walk` first-touch baseline of 7.85
ns/iter = ~5.1 ns of additional cost per revisited cacheline. This
fires once the cumulative allocation exceeds Zen 2's L3 cache size
(~8 MB on the 3600), at which point wrap-handed-out cachelines have
been evicted from L3 and must be re-fetched from DRAM with their
old contents (which then get overwritten). For Ergo programs that
allocate once at startup and never wrap, this cost is zero. For
programs that exceed the arena and wrap, the cost is real and
unavoidable in a bump-only design — V8's warp-cursor recycling
specifically targets this regime.

¹⁵ `vkAllocateMemory` fixed floor: 162 µs/call on NVIDIA RTX 2060
under Linux Vulkan, measured warm-cohort mean across 49 successive
allocations following one cold call. Holds size-independent from
4 KB through ~1 MB, where the per-byte slope (footnote 16) begins
to dominate. The 162 µs is per-call driver overhead — IOCTLs into
the kernel driver, memory-type lookups, internal allocator
bookkeeping — not memory-bandwidth-related. See
[VK_ALLOC_COST_MODEL.md](VK_ALLOC_COST_MODEL.md) for the full
characterization.

¹⁶ DEVICE_LOCAL per-byte slope: ~19 ns/byte (~20 µs/MB) for
allocations ≥ 16 MB. The slope corresponds to ~50 MB/s effective
allocation throughput — far below the 2060's ~300 GB/s VRAM
bandwidth, so this isn't bandwidth-limited; it's per-byte driver
work (page-table setup, internal bookkeeping). Sample model
validation: galaxy_structured's 149 MB buffers predicted at
3134 µs (162 + 19×149e6 ns), measured at 2867 µs — within 9%.

¹⁷ HOST_VISIBLE per-byte slope: ~290 ns/byte, 15× higher than
DEVICE_LOCAL. This row exists because the Pass 3 diagnostic plan
predicted HOST_VISIBLE would be *faster* than DEVICE_LOCAL (the
hypothesis was "DEVICE_LOCAL pays a VRAM zero-fill cost that
HOST_VISIBLE escapes"). The hypothesis was **falsified**:
HOST_VISIBLE is dramatically slower at large sizes (4970 µs vs
515 µs at 16 MB). The cost is likely PCIe-bus-bound zeroing of
pinned system memory. Implication: for Ergo's STATIC array storage,
DEVICE_LOCAL is unambiguously the right memory type — HOST_VISIBLE
saves nothing on allocation time and adds host-mapping overhead
on every access.

¹⁸ Ergo GPU init wall-clock total for galaxy_structured at
N=18M particles: 27.6 ms across 37 buffer creations. Two largest
buffers are 149 MB each (the position and velocity arrays at
double precision) and contribute ~5.7 ms total. The remaining
~22 ms is spread across the other 35 smaller buffers, dominated
by the 162 µs fixed floor since most are well under 8 MB. For a
program running at 60-74 FPS over millions of frames, the 27.6 ms
one-time startup cost is invisible. See
[VK_ALLOC_COST_MODEL.md](VK_ALLOC_COST_MODEL.md) for the per-call
breakdown and the cold/warm analysis.

### Why init cost matters specifically for Ergo

Ergo programs don't allocate at steady state. `galaxy_structured.ergo`
and the other shipping Ergo programs do all their allocation at
program start, then run the simulation for millions of frames with
zero allocs/frame. The unified comparison's steady-state column is
N/A for Ergo GPU and matches the CPU bump floor for Ergo CPU; the
*init* column is where Ergo's design has measurable cost and where
it should be compared against per-allocation runtime allocators that
amortize their setup over many calls.

Pass 3's `vkAllocateMemory` characterization makes the Ergo trade
concrete: galaxy_structured at N=18M particles pays 27.6 ms of
one-time startup cost in exchange for 0 ns/alloc at every
subsequent timestep. V8 and V22 pay the inverse: small per-call
cost amortized across many calls, but every call has that cost.
For a simulation running millions of frames at 60-74 FPS, Ergo's
trade is unambiguously the right one — the 27.6 ms startup
overhead is invisible against the total simulation runtime, and
the savings of 0 ns/alloc per frame compound across hundreds of
thousands of frames.

The per-byte slope (~19 ns/byte for DEVICE_LOCAL VRAM commit) is
the part that scales with Ergo's total array footprint. A program
with 4 GB of arrays (near the RTX 2060 ceiling) would pay
~76 ms of one-time allocation cost. Still amortizable; still
invisible against a multi-minute simulation runtime.

## Sub-table 2b: GPU instruction-count characterization

This is a *characterization*, not a comparison. The two systems
emit code at different abstraction levels and counting their ops
side-by-side requires a structural disclaimer up front.

**The abstraction-level mismatch:**

Ergo emits SPIRV, which is an intermediate representation that the
NVIDIA Vulkan driver re-compiles into SASS at pipeline-creation
time. V8 emits CUDA C++ that nvcc compiles to PTX that ptxas
compiles to SASS — the same hardware ISA Ergo's SPIRV eventually
reaches via a different compilation path. **A SPIRV op count and a
SASS op count are not the same kind of number**, in either
direction:

- *SPIRV "expensive" → SASS "cheap"*: `OpAccessChain` is a
  non-trivial address-computation op at the SPIRV level, but on
  NVIDIA Vulkan it typically folds into the addressing mode of the
  following load — contributing zero standalone SASS instructions.
- *SPIRV "cheap" → SASS "expensive"*: `OpLoad` from a
  StorageBuffer is a single SPIRV op, but on cache-cold paths it
  lowers to LDG + dependency stalls totaling many cycles of
  effective cost.

There is no monotonic relationship between SPIRV op count and
SASS op count, and no honest way to normalize them into a single
comparable number. The table below characterizes *what each system
does in its hot path* and leaves the reader to draw conclusions
about where the work lives.

### Ergo hot-path SPIRV ops (galaxy_structured, kernel_4 = SIM_PHYSICS_STEP)

| Operation | SPIRV op count | What it is |
|---|---:|---|
| **Per-particle physics kernel (full body)** | 1,112 | All work for one particle-step: force computation, integration, branching for state transitions, multiple buffer reads/writes. No inner loops; straight-line code with 28 selection-merge regions (predicated IFs). |
| **1D buffer access (e.g., POS_X(I))** | 3 | `OpISub` (1-based→0-based) + `OpAccessChain` + `OpLoad`. Two if the index is already 0-based. |
| **3D buffer access (GRID_DENSITY(CI, CJ, CK))** | 10 | 3× `OpISub` (per-dim 1→0) + 3× `OpIMul` (strides; one redundant `× GRID_SIZE` for the K-stride) + 2× `OpIAdd` (combine) + `OpAccessChain` + `OpLoad`. |

Op-mix breakdown of the 1,112-op physics kernel: 156 FMul, 144
AccessChain, 126 Load, 91 ISub, 71 IAdd, 67 FAdd, 42 IMul, 32
Store, 28 SelectionMerge, 28 BranchConditional, 22 Phi, plus
smaller counts of FDiv, ExtInst (math built-ins), GroupNonUniform-
Shuffle, etc.

### V8 hot-path SASS ops (aizawa_slab_test, slab_stress_kernel)

Numbers from [V8/COMPILER_DETERMINISM.md](V8/COMPILER_DETERMINISM.md)
and [V8_VS_V22_HEAD_TO_HEAD.md](V8_VS_V22_HEAD_TO_HEAD.md). Not
re-derived here.

| Operation | SASS op count | What it is |
|---|---:|---|
| **viviani_slab_alloc fast path** | 10-30 amortized | Bitmap-bit claim via atomicAnd + warp-cooperative ballot + slot-to-pointer arithmetic. The range varies by class and warp-lifetime amortization of the first-range-claim setup (~100 SASS instr amortized over hundreds of allocs). |
| **Bitmap claim inner atomic** | 4-8 | `ATOMG.E.AND.STRONG.GPU` + `__ballot_sync` + `__popc` + a conditional check on the old-value bit. |
| **Slot-to-pointer arithmetic** | 2-3 | `MAD` or `MUL + ADD` to compute `sb->data + slot * stride`. |

### What this characterization shows

Each system spends its hot-path ops on what's structurally
load-bearing for its design:

- **V8 spends its ops on warp-cooperative slot allocation** — the
  bitmap atomic, ballot consensus, and slot-to-pointer arithmetic
  are all about coordinating 32 lanes claiming distinct slots from
  a shared structure. The per-lane SASS budget (10-30 ops) is
  small because the operation is simple at the algorithmic level
  even if it requires careful warp coordination.

- **Ergo spends its ops on multi-dim index linearization and
  physics work** — most of the 1,112 SPIRV ops in the physics
  kernel are arithmetic (FMul, FAdd, FMA-able pairs) doing actual
  physics, not addressing. The 3D-access overhead (10 ops vs the
  3 ops of a 1D access) is the cost of Ergo's multi-dim array
  abstraction — every multi-dim buffer access pays it. Whether
  it survives to SASS depends on the driver's ability to fold
  strides into addressing modes, which it can do for some patterns
  and can't for others.

Both are legitimate work. Neither maps cleanly onto the other.
The "1,112 SPIRV ops" headline for Ergo and the "10-30 SASS ops"
headline for V8 are answering different questions: Ergo's number
is "what does one particle-step of physics look like?", V8's is
"what does one slot claim look like?" The reader who wants to
know "is Ergo's kernel as efficient as V8's hot path" needs to ask
a different question — see calibration below.

### Calibration: physics kernel ops vs hardware budget

For what it's worth: galaxy_structured at 30M particles × 60 FPS
× 1,112 SPIRV ops per particle-step = **2.0 T SPIRV-ops/sec** sustained
demand. The RTX 2060's peak FP32 throughput is ~6.5 TFLOPS; the
sustained SASS-op rate across all SMs is a fraction of that.

For 2.0 T SPIRV-ops/sec to fit on a 2060, the SPIRV→SASS expansion
ratio has to average well under 1 — many SPIRV ops must fold into
addressing modes, fuse into FMAs, or vectorize. The measured 60-74
FPS sustained for galaxy_structured at this scale means it does fit;
the driver is achieving the necessary folding. **No follow-up SPIRV
peephole work is suggested by this calibration**; the kernel is
running within hardware budget at the measured throughput.

(If the kernel ran at, say, 5 FPS instead of 60, the same 1,112
SPIRV ops would imply a SPIRV→SASS expansion ratio that exceeds
hardware capacity by 12×, suggesting a real performance problem.
The math goes the other way too.)

## Sub-table 3: Features and determinism

Qualitative comparison. Not throughput.

| Feature | Ergo CPU | Ergo GPU | V22 (CPU) | V8 (GPU) | cudaMalloc | CPU bump | GPU bump |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Bit-identical across rebuilds | ✓¹⁰ | ✓ (spec)¹⁰ᵃ | ✓¹¹ | ✓¹² | N/A | trivially | trivially |
| Bit-identical across machines | ✓ | TBD | ✓ | ✗ | ✗ | trivially | trivially |
| Runtime allocator | ✓ (bump emit) | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Structured size classes | ✗ | ✗ | fixed | 64B/128B/256B | any | ✗ | ✗ |
| Free / recycle | no-op¹³ | N/A | per-bin freelist | warp-cursor wrap | full free | none | none |
| Language-integrated | ✓ (ALLOCATE) | ✓ (declared arrays) | ✗ (library) | ✗ (library) | ✗ | ✗ | ✗ |
| Bounds-checked at allocate | ✓ (abort on overflow) | ✓ (spec)¹⁴ | ✗ | ✗ (fallback path) | yes (NULL return) | no | no |

¹⁰ Ergo CPU bit-identical-across-rebuilds: design contract,
**validated**. Documented in
[Spec/x86_Determinism_Audit.md](../Spec/x86_Determinism_Audit.md);
the stage-1/2/3 work (commits 802e939…1093c77) builds with explicit
flag pinning and was tested across rebuilds.

¹⁰ᵃ Ergo GPU bit-identical-across-rebuilds: design contract, **not
empirically validated in this work**. The SPIRV emission contract
in `core/backends/spirv.py` is deterministic by construction (no
hash-set iteration, no random ordering); but a back-to-back rebuild
of the same Ergo program has not been diffed at the SPIRV level
within this audit. Flagged for follow-up.

¹¹ V22 bit-identical determinism documented in
[V22/COMPILER_DETERMINISM.md](V22/COMPILER_DETERMINISM.md). Requires
`-O3 -march=native -ffp-contract=fast`. Breaks under `-ffast-math`.

¹² V8 bit-identical SASS within a toolchain version (same nvcc + same
source = same SASS, verified via empty diff in
[V8/COMPILER_DETERMINISM.md](V8/COMPILER_DETERMINISM.md)). Across
toolchain versions: ~9% throughput drift observed between prior
nvcc and nvcc 13.1; SASS differs across major nvcc releases by
design.

¹³ Ergo's DEALLOCATE is a documented no-op under the arena lowering:
the bump arena is one-shot for program lifetime; freeing a single
allocation would leave a hole, and Ergo's design assumes the next
ALLOCATE doesn't need that hole back. See
[Spec/Arena_Lowering_Brief.md](../Spec/Arena_Lowering_Brief.md).
Design contract, **validated** by codegen inspection (no `free(` or
`malloc(` in emitted C; `_ergo_arena_offset` advances monotonically).

¹⁴ Ergo GPU bounds-check-at-allocate: design contract, **not
empirically validated**. The Vulkan host code in
`core/runtime/vk_host.c` checks `vkAllocateMemory` return codes and
exits on failure, but Ergo's error-handling path has not been
exercised in an out-of-VRAM test within this audit. The CPU
bounds-check (footnote 5) is empirically validated; the GPU path
relies on the Vulkan API contract.

## What's still TBD

- **Pass 2** (Ergo CPU instrumentation): ✅ **Complete.** Ergo CPU
  arena measured at 0.77 ns/alloc (1.5× of CPU bump floor) via the
  `nostore` variant of [baseline_arena.c](baseline_arena.c). Sub-table
  1's Ergo CPU arena row and Sub-table 2's three-row cost
  decomposition (sub-floor / first-touch / wrap-revisit) are filled in.
  Methodology surprise documented: a naive end-to-end bench timed at
  12.9 ns/alloc — 25× higher — and required the four-variant
  diagnostic to separate allocator cost from DRAM write-for-ownership
  cost.

- **Pass 3 (Ergo GPU instrumentation, allocation cost)**: ✅
  **Complete.** `vkAllocateMemory` characterized on NVIDIA Linux
  Vulkan as a two-component cost: 162 µs floor + 19 ns/byte slope
  (DEVICE_LOCAL). Sub-table 2 rows filled in.
  [VK_ALLOC_COST_MODEL.md](VK_ALLOC_COST_MODEL.md) documents the
  full characterization with falsified-hypothesis trail and four
  per-size diagnostic measurements.

- **Pass 3 (GPU instruction-count comparison)**: ✅ **Complete.**
  Characterization in Sub-table 2b above. The Ergo physics kernel
  is 1,112 SPIRV ops/particle-step (galaxy_structured kernel_4);
  V8's slab fast path is 10-30 SASS ops/lane. The numbers answer
  different questions (full-physics-step vs. one slot-claim) and
  the abstraction-level mismatch is explicit in the section
  preamble. Calibration: galaxy_structured at 30M @ 60 FPS implies
  SPIRV→SASS expansion ratio averaging well under 1, which the
  driver achieves via addressing-mode folding and FMA fusion. No
  follow-up peephole work suggested by the op count.

- **Cross-machine determinism for Ergo GPU**: Sub-table 3 has TBD
  for Ergo GPU bit-identical-across-machines. Determined by whether
  the SPIRV → driver SASS step preserves source bit-identity across
  GPU vendors. Not in scope for this brief; flagged for the SPIRV
  determinism audit if one happens.

## Reproducing

All measurements in Sub-tables 1 and 2 are reproducible from
in-tree sources per the build commands in [BASELINE.md](BASELINE.md)
and [V8_VS_V22_HEAD_TO_HEAD.md](V8_VS_V22_HEAD_TO_HEAD.md). Hardware
must match: Ryzen 5 3600 + RTX 2060, sm_75. Cross-machine numbers
will differ; the comparison is hardware-specific by design.
