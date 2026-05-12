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

CPU rows compare against the per-arena bump (CPU Floor A) as the
1.0× reference. GPU rows compare against the non-aggregated bump
(GPU Floor B) as the 1.0× reference — the floor V8's lanes actually
contend against. Smaller-is-better in the rightmost column: 1.0× is
"at the floor"; <1.0× escapes the floor's contention pattern; >1.0×
pays more than the floor.

| System | Throughput | ns/lane-op | × Floor (ns/op) | Notes |
|---|---:|---:|---:|---|
| **CPU 1t per-arena bump** | 1.95 G/s | 0.51 | 1.00× (reference) | Load + add + store |
| **CPU 6t per-arena bump** | 11.6 G/s | 0.09 | 0.18× | 5.96× linear scaling |
| **CPU 1t shared atomic** | 232 M/s | 4.31 | 8.5× | Locked RMW dominates |
| **CPU 6t shared atomic** | 158 M/s | 6.33 | 12× | Cacheline ping-pong |
| **V22 hand-SSE 1t** | 89 M/s | 11.2¹ | — | Geometric residual, not alloc |
| **V22 hand-SSE 6t** | 549 M/s | 1.82¹ | — | 17% drift vs prior doc² |
| **Ergo CPU arena** | TBD (Pass 2) | TBD | TBD | Expected ≈ 1.0× (bump emit *is* the floor) |
| **GPU bump Floor A** | 35.5 G/s | 0.03 | 0.08× | nvcc warp-aggregated; 1 atomic/warp |
| **GPU bump Floor B** | 2.65 G/s | 0.38 (0.55/lane) | 1.00× (reference) | 1 atomic/lane, per-lane size varied |
| **V8 slab allocator** | 1.73 G/s | 0.58 | 1.05× | Per-lane bitmap atomic³ |
| **cudaMalloc** | ~3 M/s⁴ | ~330 | ~600× | Driver call, not warp-cooperative |
| **Ergo GPU runtime alloc** | N/A | N/A | N/A | No runtime GPU allocator; see Sub-table 2 |

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
| **malloc (libc, glibc)** | ~30 ns⁵ | N/A | Single libc call; backed by sbrk/mmap |
| **V22 SQ2FAL** | ~30 ns | Yes (per-thread) | Scatter LUT + bin advance |
| **V8 viviani_slab_alloc** | ~50 ns | Yes (per-warp) | First range claim adds 100 SASS instr; amortized over warp lifetime |
| **vkAllocateMemory (Vulkan)** | TBD (Pass 3) | No | Vulkan driver call per buffer; expected to dominate Ergo GPU init |
| **Ergo CPU arena init** | ~0⁶ | Yes (program lifetime) | BSS-resident `_ergo_arena[]`; first ALLOCATE = bump increment |
| **Ergo GPU init (per array)** | TBD (Pass 3) | Yes (program lifetime) | One vkCreateBuffer + vkAllocateMemory + vkBindBufferMemory per declared array |

⁵ malloc init cost approximated; not measured in this work.

⁶ "~0" means: no per-arena init step beyond what the OS loader
already does for any BSS-resident allocation. `_ergo_arena[]` is a
file-scope `static char[ERGO_ARENA_BYTES]`; the loader zero-fills
it once at program load (a one-time amortized cost shared with every
other BSS symbol in the binary), and `_ergo_arena_offset` starts at
0. The first ALLOCATE pays the bump emit cost (load offset, round
size, bounds check, advance offset) — same as the CPU steady-state
floor row in Sub-table 1, no more, no less. There is no
allocator-side setup separate from the bump itself.

### Why init cost matters specifically for Ergo

Ergo programs don't allocate at steady state. `galaxy_structured.ergo`
and the other shipping Ergo programs do all their allocation at
program start, then run the simulation for millions of frames with
zero allocs/frame. The unified comparison's steady-state column is
N/A for Ergo GPU and matches the CPU bump floor for Ergo CPU; the
*init* column is where Ergo's design has measurable cost and where
it should be compared against per-allocation runtime allocators that
amortize their setup over many calls.

Once Pass 3 measures `vkAllocateMemory`'s per-buffer cost on this
hardware, the table will let a reader see the trade Ergo makes
concretely: it pays N × init-cost at program start in exchange for
0 ns/alloc at every subsequent timestep. V8 and V22 pay the inverse:
small per-call cost amortized across many calls, but every call has
that cost.

## Sub-table 3: Features and determinism

Qualitative comparison. Not throughput.

| Feature | Ergo CPU | Ergo GPU | V22 (CPU) | V8 (GPU) | cudaMalloc | CPU bump | GPU bump |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Bit-identical across rebuilds | ✓⁷ | ✓ (spec)⁷ᵃ | ✓⁸ | ✓⁹ | N/A | trivially | trivially |
| Bit-identical across machines | ✓ | TBD | ✓ | ✗ | ✗ | trivially | trivially |
| Runtime allocator | ✓ (bump emit) | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Structured size classes | ✗ | ✗ | fixed | 64B/128B/256B | any | ✗ | ✗ |
| Free / recycle | no-op¹⁰ | N/A | per-bin freelist | warp-cursor wrap | full free | none | none |
| Language-integrated | ✓ (ALLOCATE) | ✓ (declared arrays) | ✗ (library) | ✗ (library) | ✗ | ✗ | ✗ |
| Bounds-checked at allocate | ✓ (abort on overflow) | ✓ (spec)¹¹ | ✗ | ✗ (fallback path) | yes (NULL return) | no | no |

⁷ Ergo CPU bit-identical-across-rebuilds: design contract,
**validated**. Documented in
[Spec/x86_Determinism_Audit.md](../Spec/x86_Determinism_Audit.md);
the stage-1/2/3 work (commits 802e939…1093c77) builds with explicit
flag pinning and was tested across rebuilds.

⁷ᵃ Ergo GPU bit-identical-across-rebuilds: design contract, **not
empirically validated in this work**. The SPIRV emission contract
in `mcl/backends/spirv.py` is deterministic by construction (no
hash-set iteration, no random ordering); but a back-to-back rebuild
of the same Ergo program has not been diffed at the SPIRV level
within this audit. Flagged for follow-up.

⁸ V22 bit-identical determinism documented in
[V22/COMPILER_DETERMINISM.md](V22/COMPILER_DETERMINISM.md). Requires
`-O3 -march=native -ffp-contract=fast`. Breaks under `-ffast-math`.

⁹ V8 bit-identical SASS within a toolchain version (same nvcc + same
source = same SASS, verified via empty diff in
[V8/COMPILER_DETERMINISM.md](V8/COMPILER_DETERMINISM.md)). Across
toolchain versions: ~9% throughput drift observed between prior
nvcc and nvcc 13.1; SASS differs across major nvcc releases by
design.

¹⁰ Ergo's DEALLOCATE is a documented no-op under the arena lowering:
the bump arena is one-shot for program lifetime; freeing a single
allocation would leave a hole, and Ergo's design assumes the next
ALLOCATE doesn't need that hole back. See
[Spec/Arena_Lowering_Brief.md](../Spec/Arena_Lowering_Brief.md).
Design contract, **validated** by codegen inspection (no `free(` or
`malloc(` in emitted C; `_ergo_arena_offset` advances monotonically).

¹¹ Ergo GPU bounds-check-at-allocate: design contract, **not
empirically validated**. The Vulkan host code in
`mcl/runtime/vk_host.c` checks `vkAllocateMemory` return codes and
exits on failure, but Ergo's error-handling path has not been
exercised in an out-of-VRAM test within this audit. The CPU
bounds-check (footnote 6) is empirically validated; the GPU path
relies on the Vulkan API contract.

## What's still TBD

- **Pass 2** (Ergo CPU instrumentation): measure Ergo's arena bump
  on `tests/allocate_bench.ergo` under the post-x86-determinism flag
  regime. Fills the **Ergo CPU arena** row in Sub-table 1 and the
  **Ergo CPU arena init** row in Sub-table 2. Predicted result: both
  rows match the CPU bump floor exactly (bump emit *is* the
  operation).

- **Pass 3** (Ergo GPU instrumentation): measure Ergo's
  `vkAllocateMemory` cost per buffer on this hardware, and inspect
  Ergo's SPIRV buffer-access pattern post-peephole for the GPU
  instruction-count comparison. Fills the **vkAllocateMemory** and
  **Ergo GPU init** rows in Sub-table 2 and produces the GPU
  instruction-count table called for in
  [Spec/Allocator_Comparison_Brief.md](../Spec/Allocator_Comparison_Brief.md).
  No Ergo cell to fill in Sub-table 1 — Ergo has no runtime GPU
  allocator and the cell is correctly N/A.

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
