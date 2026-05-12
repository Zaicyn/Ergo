# Vulkan allocation cost model — Pass 3 diagnostic

Detailed cost characterization for `vkAllocateMemory` on the
Pass 3 test hardware (NVIDIA RTX 2060, Linux, NVIDIA driver via Vulkan
1.x). Established during Pass 3 of the allocator comparison after the
single-number "vkAllocateMemory cost" framing turned out to hide two
distinct phenomena that scale differently.

The instrumentation lives in `mcl/runtime/vk_host.c` under
`#ifdef ERGO_BENCH_VK_ALLOC`; the microbench driver is
`/tmp/vk_alloc_microbench.c` (not tracked — methodology lives here
and in the Pass 3 commit message).

## Cost model

For `vkAllocateMemory` of an `n`-byte buffer with
`VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT`:

```
cost(n) ≈ max(162 µs, 162 µs + 19 ns/byte × n)
```

Two regimes:

- **Floor-dominated** (n ≲ 8 MB): cost is ~162 µs, size-independent.
  This is the per-call driver overhead — IOCTLs into the kernel
  driver, memory-type-table lookups, internal allocator bookkeeping.
  Holds flat from 4 KB through 1 MB.
- **Size-dominated** (n ≳ 16 MB): cost is dominated by the
  19 ns/byte slope. This is the per-byte cost of committing VRAM
  pages: page-table setup, internal driver bookkeeping that scales
  with allocation size. *Not* GPU bandwidth-limited (the slope
  corresponds to ~50 MB/s effective allocation throughput, far below
  the 2060's ~300 GB/s VRAM bandwidth).

Crossover at ~8 MB (where the 19 ns/byte slope contribution equals
the 162 µs floor).

## Measured data

All values are warm steady-state (mean of 49 calls following a
single cold call). DEVICE_LOCAL memory type unless noted.

| Allocation size | vkAllocateMemory (µs) | Per-byte rate (ns/B) | Notes |
|---|---:|---:|---|
| 4 KB | 163 | — | floor-dominated |
| 16 KB | 164 | — | floor-dominated |
| 64 KB | 162 | — | floor-dominated |
| 1 MB | 195 | 31 | transition region |
| 16 MB | 507 | 21 | size-dominated; asymptotic slope visible |
| 64 MB | 1426 | 21 | asymptotic |
| 256 MB | 5076 | 19 | asymptotic |

Cold-call overhead is +10–15 µs on the first call only; not a
load-bearing concern for typical Ergo programs that allocate 30-40
buffers at startup (the cold cost amortizes across the warm cohort).

## HOST_VISIBLE vs DEVICE_LOCAL (falsified hypothesis)

The Pass 3 diagnostic plan hypothesized that the per-byte cost was
specific to DEVICE_LOCAL VRAM commit-and-zero — i.e., HOST_VISIBLE
allocations should escape the slope.

**The hypothesis was falsified.** HOST_VISIBLE allocations are not
faster; they are dramatically *slower* at large sizes:

| Size | DEVICE_LOCAL warm (µs) | HOST_VISIBLE warm (µs) | Ratio |
|---|---:|---:|---:|
| 64 KB | 165 | 233 | 1.4× |
| 16 MB | 515 | 4970 | **9.6×** |

The HOST_VISIBLE slope is ~290 ns/byte vs DEVICE_LOCAL's 19 ns/byte
— **15× higher**. Most likely explanation: HOST_VISIBLE allocations
go through PCIe-bus-bound zeroing of pinned system memory, while
DEVICE_LOCAL allocations get a faster driver-internal path that
doesn't require host-side zero-fill traffic. The PCIe Gen 3 ×16 bus
on this hardware caps at ~16 GB/s practical, and 290 ns/byte
corresponds to ~3.4 GB/s — consistent with the bus being partially
saturated by other Vulkan traffic during the alloc.

Memory-type verification: `memoryTypeBits=0x3b` on both runs (both
DEVICE_LOCAL and HOST_VISIBLE are permissible for the buffer's
usage flags), and the selected `memoryTypeIndex` differed (1 for
DEVICE_LOCAL, 3 for HOST_VISIBLE). The test was measuring genuinely
different memory types, not a silent fallback.

**Methodological lesson**: pre-committing to a falsification
threshold ("hypothesis confirmed if HOST_VISIBLE 16 MB <250 µs;
falsified if >400 µs") kept the result honest. Measured 4970 µs
— well into the falsified range. The two memory types are not
"zeroed vs not zeroed"; they're different driver paths with
genuinely different cost structures.

## VRAM ceiling

Cumulative DEVICE_LOCAL allocations on RTX 2060 (6 GB total) hit
`VK_ERROR_OUT_OF_DEVICE_MEMORY` (-2) at **~4 GB committed**. The
remaining ~2 GB is reserved by the driver/swapchain/other GPU
state. Practical hard ceiling for Ergo programs is ~4 GB of array
storage on this hardware.

## Applying the model to galaxy_structured

Galaxy_structured at N=18M particles creates 37 buffers; the two
largest are 149 MB each.

Model prediction per 149 MB buffer:
```
162 µs + 19 ns/byte × 149 × 1024 × 1024 = 3134 µs
```

Measured: **2867 µs**. Within 9% of the model — the cost model
predicts galaxy_structured's startup overhead at the per-buffer
granularity.

Total startup overhead for galaxy_structured's 37 allocations on
this hardware: **~27.6 ms wall-clock**. That's the one-time
allocation cost that doesn't recur per frame; for a simulation that
runs millions of frames at 60-74 FPS, this overhead is invisible.

## Calibration anchors for future predictions

- **NVIDIA Linux Vulkan DEVICE_LOCAL allocation floor**: ~162 µs
  per call, independent of size below ~1 MB.
- **DEVICE_LOCAL per-byte slope**: ~19 ns/byte for allocations
  ≥16 MB.
- **HOST_VISIBLE per-byte slope**: ~290 ns/byte. Significantly
  slower; avoid HOST_VISIBLE for large buffers unless host-mapping
  is required.
- **Crossover size**: ~8 MB; below this floor dominates, above this
  size cost dominates.
- **VRAM ceiling on 6 GB cards**: ~4 GB committable; rest is
  driver/swapchain overhead.

These anchors are NVIDIA-Linux-specific. ARM Mali, AMD RADV, Intel
ANV, Apple MoltenVK, and Windows NVIDIA all have different cost
structures and would need separate characterization.

## Pre-measurement predictions (recorded for calibration)

For the methodology trail (Pass 2's "anchor at 0.25 ns/op" pattern):

| Prediction | Measured | Miss factor |
|---|---|---|
| Warm `vkAllocateMemory`: 5-20 µs | 162-498 µs (size dep.) | 10-30× low |
| HOST_VISIBLE faster than DEVICE_LOCAL | 9.6× slower at 16 MB | reversed |
| 256 MB total cost ~510 ms | 5076 µs | 100× low |

The 100× miss on the 256 MB prediction came from extrapolating
naively from the 64 KB → 16 MB slope of 1.3 ns/byte, which
includes the floor-decay confound. The asymptotic slope is
~0.020 ns/byte (19 ns/KB), which gives the right answer.
**Future predictions on Vulkan allocation cost should anchor at
"162 µs floor + 19 ns/byte" rather than estimating from a single
size.**
