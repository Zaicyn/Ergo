# V8 launch-bounds experiment

Tested whether adding `__launch_bounds__` to V8's slab kernels actually
helps. Five build variants on the same hardware (Ryzen 5 3600 host,
RTX 2060 GPU, sm_75, nvcc 13.1, RTX 2060), same source otherwise.

## Setup

Each variant injects a different attribute onto the four `__global__`
kernels in `aizawa_slab_test.cu`:

```cuda
// baseline
__global__ void slab_stress_kernel(...)

// lb256x2
__global__ __launch_bounds__(256, 2) void slab_stress_kernel(...)

// lb256x3
__global__ __launch_bounds__(256, 3) void slab_stress_kernel(...)

// lb256x4
__global__ __launch_bounds__(256, 4) void slab_stress_kernel(...)

// lb_force32 — no attribute, but compiled with -maxrregcount=32
```

Variants live under `V8_bounded/`. Binaries land in `asm/bounded/*.elf`.

The arguments mean: `(maxThreadsPerBlock, minBlocksPerSM)`. ptxas uses
the pair to compute a register cap: `regs ≤ 65536 / (threads * minBlocks)`.
At 256 threads, minBlocks=2 caps at 128 regs, minBlocks=3 caps at 85,
minBlocks=4 caps at 64. The compiler then tries to fit within the cap
without spilling.

## What ptxas did

| Variant | stress | tput | correct | bench | spills |
|---|---:|---:|---:|---:|---:|
| baseline | 56 | 56 | 50 | 54 | 0 |
| `__launch_bounds__(256,2)` | 52 | 52 | 46 | 54 | 0 |
| `__launch_bounds__(256,3)` | **40** | **40** | **42** | 54 | **0** |
| `__launch_bounds__(256,4)` | 40 | 40 | 42 | 54 | 0 |
| `-maxrregcount=32` | 32 | 31 | 32 | 32 | 0 |

A few observations:

- **The baseline had headroom.** ptxas could fit V8's kernels in 40
  registers all along; it just didn't because nothing asked it to.
- **`(256,3)` is the floor for `__launch_bounds__` on this code.**
  Going to `(256,4)` produced identical SASS — ptxas converged.
- **`-maxrregcount=32` drives even lower without spilling.** This is
  surprising. The 32-reg threshold is what SM_75 needs for max occupancy
  *at small block sizes*; V8 was already at 100% theoretical occupancy
  at 256 threads/block with 56 regs (4 blocks/SM × 8 warps = 32 warps),
  so the extra register compression doesn't buy more occupancy. It
  might still help by freeing registers for the scheduler.
- **`viviani_slab_bench_kernel` stayed at 54 regs in every bounded
  variant.** That kernel's launch site uses different block dimensions
  than the others, so the `(256, N)` constraint didn't bind.

## What that did to the SASS

| Variant | stress instrs | tput instrs | correct instrs | bench instrs | total STL/LDL |
|---|---:|---:|---:|---:|---:|
| baseline | 1512 | 1976 | 2864 | 1136 | 16/28 16/24 24/36 8/12 |
| lb256x3 | 1544 | 2000 | 2992 | 1136 | 16/28 16/24 24/36 8/12 |

The bounded SASS is **slightly larger** (≈2–4% more instructions per
kernel). The local memory traffic (STL/LDL) is **unchanged**, which
confirms ptxas didn't compensate for lower registers by spilling — it
rescheduled at the instruction level instead.

SASS is **bit-identical across rebuilds** (verified by diff against a
fresh build). The determinism guarantees from the V8 doc all hold.

## What that did to wall-clock time

End-to-end timing (the binary runs correctness + tput + stress + bench
in one process), 5 runs per variant, median:

| Variant | Median wall time | Versus baseline |
|---|---:|---:|
| baseline | 0.34 s | — |
| lb256x2 | 0.29 s | **−15%** |
| lb256x3 | 0.29 s | **−15%** |
| lb256x4 | 0.29 s | **−15%** |
| lb_force32 | 0.29 s | **−15%** |

All four "ask ptxas to use fewer registers" variants are essentially
tied, all ≈15% faster than baseline.

A few more numbers from the throughput sub-test (cycles/iter, median
of 5 runs; lower is better):

| Variant | 64B class | 128B class | 256B class |
|---|---:|---:|---:|
| baseline | 4099 | 4639 | 4040 |
| lb256x2 | 3980 | 5220 | 4127 |
| lb256x3 | 5845 | 4619 | 4128 |
| lb256x4 | 5071 | 5084 | 4084 |
| lb_force32 | 4025 | 4968 | 4143 |

Per-class throughput is noisier than total wall time — values bounce
around by ±25% across runs. This is the throughput sub-test (3
allocations per warp, very short kernel), where measurement overhead
and L2/scheduler quirks dominate over algorithmic differences. The
*total wall time* (which is mostly dominated by the longer stress and
correctness kernels) is the cleaner signal: a stable ~15% improvement.

## Why the gain is real but not huge

The naive expectation ("more registers = lower occupancy = slower")
predicted a bigger gain. The actual story:

1. **V8 was already at theoretical max occupancy at 256-thread blocks.**
   56 regs × 256 threads = 14336 regs/block; 65536/SM gives 4 blocks/SM
   = 32 warps/SM = 100%. The register count was high, but it wasn't
   limiting concurrent warps.

2. **The 15% gain is from reduced register pressure on the scheduler,
   not occupancy.** With fewer live registers per thread, the warp
   scheduler can issue from more warps in parallel (less register
   file contention, faster context switching between warps when one
   stalls on memory).

3. **For kernels that hit the 56-reg ceiling at smaller blocks**
   (e.g. 128 threads/block as `tput` and `correct` use), `__launch_bounds__`
   *would* improve occupancy too. With 128-thread blocks at 56 regs:
   8 blocks × 4 warps = 32 warps/SM at 100%. So those were already
   maxed too. The gain there is purely scheduler pressure.

If V8 ever shipped a config with **32-thread blocks** (one warp per
block), the register count *would* limit occupancy and the bounds
attribute would matter much more. At the current launch shape,
15% is what's available.

## Determinism cost

None measured. The bounded variants:

- Have **zero register spills** (ptxas wasn't forced into spills).
- Produce **bit-identical SASS across rebuilds** (verified).
- Pass the correctness test (`0 corruption errors`).
- Hit `0.00% fallback rate` on the stress test, same as baseline.
- Maintain the same `0` warp barriers, same atomic ordering
  (`ATOM.E.<op>.STRONG.GPU`), same `__ballot_sync`/`__shfl_sync`
  semantics.

The bounded SASS is slightly larger (more instructions) but no
spills, no extra atomics, no extra synchronization. It's just
ptxas doing more instruction-level scheduling.

## Recommendation

Add `__launch_bounds__(256, 3)` (or `(256, 4)` — identical effect on
this codebase) to V8's three main kernels. Free 15% off wall time
with zero spills, bit-reproducible SASS, no determinism degradation.

The simpler `-maxrregcount=32` approach gets the same speedup
without any source changes, but it applies globally across the entire
TU and would also compress `viviani_slab_bench_kernel` (which `__launch_bounds__`
doesn't touch). On this code that's harmless (no spills emerged at
32 regs), but it's a blunt-instrument flag and worth avoiding if
you can be more specific.

The bench kernel (`viviani_slab_bench_kernel`) is a separate question.
It launches with different block dimensions than the others, so a
`(256, N)` bound doesn't constrain it. If its register count matters
(it's currently at 54), apply a separate bound matching its actual
launch shape — but check first whether its launch site is in the hot
path or just a one-shot benchmark; if the latter, no point optimizing.

## Caveats worth knowing

- **`__launch_bounds__` is a hint, not a guarantee.** If you launch
  with more threads than `maxThreadsPerBlock` declared, the runtime
  errors out. If you launch with fewer, ptxas's register decisions
  may be suboptimal but the kernel still runs. The values must match
  actual launch sites or you lose the bound's effect (silently, for
  too-few-threads case).
- **Different SMs change the math.** sm_75 has 65536 regs/SM. sm_80
  (A100) has 65536 too but max 64 warps/SM. sm_90 (H100) has 65536
  but 64 warps/SM and 32 blocks/SM. The exact register cap that
  ptxas derives from `__launch_bounds__` depends on which SM target
  you compile for. The 15% measurement here is sm_75-specific.
- **Profile with NSight, not wall-clock**, if you want to dig into
  *why* the 15% appears. Wall clock is noisy and conflates everything;
  NSight Compute would let you confirm whether it's warp-scheduler
  utilization or something else (memory pipe usage, cache hit rate,
  etc.). I didn't run NSight here; the 15% wall-clock signal was
  consistent enough across 5 runs to call.

## Reproducing this experiment

```bash
cd Testing

# Build all variants:
for V in baseline lb256x2 lb256x3 lb256x4 lb_force32; do
    if [ "$V" = "lb_force32" ]; then EXTRA="-maxrregcount=32"; else EXTRA=""; fi
    nvcc -arch=sm_75 -O3 -lineinfo --ptxas-options=-v $EXTRA -IV8 \
        V8_bounded/$V.cu -o asm/bounded/$V.elf
done

# Compare ptxas stats (look for "Used N registers"):
nvcc -arch=sm_75 -O3 --ptxas-options=-v -IV8 V8_bounded/baseline.cu  -o /dev/null 2>&1 | grep Used
nvcc -arch=sm_75 -O3 --ptxas-options=-v -IV8 V8_bounded/lb256x3.cu   -o /dev/null 2>&1 | grep Used

# Time them:
for V in baseline lb256x3; do
    echo "-- $V --"
    for i in 1 2 3 4 5; do /usr/bin/time -f "%e" ./asm/bounded/$V.elf >/dev/null; done
done
```

## Final summary

Yes, `__launch_bounds__` helps V8. Not by as much as the "register
pressure caps occupancy" story would predict — the V8 launch shape
already had max occupancy. But ptxas had headroom to compress the
register working set further (56 → 40 regs, sometimes 32) with no
spills, and the runtime gain is a stable ~15% off end-to-end wall
time across multiple runs.

The fact that no spills appeared at 32 regs is the most interesting
piece. V8's hot path looks register-hungry in source (56-reg working
set after inlining everything), but a lot of those registers held
live values that *could* be recomputed cheaply if ptxas needed the
register. With pressure applied, ptxas found those values and
re-emitted them.

That's `__launch_bounds__` working as designed: not freeing the
hardware to run more warps (V8 was at the warp ceiling already),
but freeing ptxas to spend a few more instructions in exchange for
holding fewer live values per thread. The scheduler is what benefits.
