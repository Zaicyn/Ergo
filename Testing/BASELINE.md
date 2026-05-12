# Bump-allocator floor measurements

Establishes "do-nothing" baselines for CPU and GPU allocation cost so that
the Ergo/V8/V22 comparison numbers in
[V8_VS_V22_HEAD_TO_HEAD.md](V8_VS_V22_HEAD_TO_HEAD.md) and the eventual
unified comparison table can be reported as multiples of a physical floor.
Hardware is the same as the head-to-head doc: Ryzen 5 3600 (Zen 2,
6c/12t, AVX2+FMA) + RTX 2060 (sm_75, 30 SMs).

Toolchain at measurement time:
- gcc 15.2.1
- nvcc 13.1.115 (release 13.1)
- driver/runtime versions inherited from `/opt/cuda`

Build commands (also documented in `baseline_bump.{c,cu}` headers):

```bash
gcc  -O3 -march=native -fopenmp -std=c11 baseline_bump.c  -o baseline_bump_cpu
nvcc -arch=sm_75       -O3                baseline_bump.cu -o baseline_bump_gpu
```

## CPU bump-allocator floors

50,000,000 × 64B allocations, 16B alignment. Three regimes measured:

### Single-thread

Single increment of a thread-local offset. No contention possible.

```
single-thread: 50000000 allocs in 0.0257 s = 1944.8 M/s, 0.51 ns/alloc
```

**Floor: ~0.51 ns/alloc, ~1.94 G/s.** This is the absolute lower bound on
CPU allocation cost — three integer ops (load, add, store) per call.

### Multi-thread, per-thread arena

Each thread bumps its own offset in a private 256 MB slice of the arena.
No shared writes; expected to scale linearly with core count.

```
 1t per-thread arena:        1947.9 M/s,  0.51 ns/alloc
 2t per-thread arena:        3001.5 M/s,  0.33 ns/alloc
 4t per-thread arena:        7723.0 M/s,  0.13 ns/alloc
 6t per-thread arena:       11590.2 M/s,  0.09 ns/alloc
12t per-thread arena:       10802.7 M/s,  0.09 ns/alloc  (SMT, no gain)
```

**6-core floor: ~0.09 ns/64B-eq, ~11.6 G/s aggregate** — 5.96× linear
speedup vs single-thread. SMT to 12 threads adds nothing (no shared work
to overlap).

### Multi-thread, shared atomic counter

All threads contend on a single `atomic_fetch_add_explicit` counter. This
is the "naive shared bump" anti-pattern; the cost is dominated by L1↔L2
cacheline ping-pong, not by the increment.

```
 1t shared atomic counter:    232.2 M/s,  4.31 ns/alloc
 2t shared atomic counter:    117.7 M/s,  8.50 ns/alloc
 4t shared atomic counter:    127.5 M/s,  7.84 ns/alloc
 6t shared atomic counter:    158.0 M/s,  6.33 ns/alloc
12t shared atomic counter:    134.4 M/s,  7.44 ns/alloc
```

**Single-thread atomic: ~4.3 ns** — 8.4× slower than single-thread
per-arena bump. The cost is the locked-RMW operation; even with zero
contention, the L1 invalidation overhead dominates.

**1t→2t doubles latency** (4.3→8.5 ns) — the cacheline starts bouncing
between cores. Throughput stays roughly flat at 120-160 M/s through 12
threads.

V22 at 11.2 ns/call single-thread (hand-SSE residual computation, *not*
allocation) is doing ~22× more work than the shared-atomic floor — its
geometric residual is comparable in cost to a contended atomic increment.

## GPU bump-allocator floors

Both kernels match V8's micro-bench geometry exactly: 256 blocks × 256
threads × 1000 iters/lane, `__launch_bounds__(256, 3)`, 5 reps with
counter reset between. Two floors are reported because nvcc applies
warp aggregation automatically when all lanes request a uniform size —
and that produces a fundamentally different cost regime than per-lane
atomic contention.

### Floor A: warp-aggregated (compiler folds per-warp)

All lanes call `atomicAdd(&d_offset, 64)` with a uniform size. nvcc
detects this and rewrites the per-lane atomics into one per-warp atomic
of `popcount(activemask) * 64`, then broadcasts the base back to all
lanes.

SASS pattern in the loop body (4× unrolled):
```
S2R       R10, SR_LANEID
VOTEU.ANY UR10, UPT, PT
FLO.U32   R5,   UR10
UPOPC     UR6,  UR10
UIMAD.WIDE.U32  UR6, UR6, 0x40, URZ     ; popcount × 64
@P0 ATOMG.E.ADD.64.STRONG.GPU PT, R6, [UR8], R6
```

The `@P0` predicate means only one lane per warp issues the atomic.

Measurement:
```
rep 0: 34847.1 M 64B-eq/s, 0.03 ns/64B-eq
rep 1: 35082.9 M 64B-eq/s, 0.03 ns/64B-eq
rep 2: 35203.5 M 64B-eq/s, 0.03 ns/64B-eq
rep 3: 35281.1 M 64B-eq/s, 0.03 ns/64B-eq
rep 4: 35078.1 M 64B-eq/s, 0.03 ns/64B-eq
```

**Floor A: ~35 G/s, ~0.03 ns/lane-alloc** — but this is one atomic per
warp, not per lane. Per-warp atomic cost is ~32×0.03 ≈ 1 ns, dominated
by serialized atomic issue at L2.

### Floor B: non-aggregated (per-lane sz=64+(lane&7)*8 defeats fold)

Per-lane size varies as `64 + (lane_id & 7) * 8` ∈ {64, 72, ..., 120},
producing 8 distinct sizes across the warp. The compiler cannot fold
the per-lane atomicAdds into one because the warp's sum depends on
which lanes are active *and* their per-lane sizes.

SASS pattern in the loop body (4× unrolled):
```
ATOMG.E.ADD.64.STRONG.GPU PT, R4, [UR6], R6     ; unguarded — all lanes
```

No `VOTEU.ANY` / `UPOPC` aggregation primitives. Every active lane
issues its own atomic.

Throughput is reported as 64B-equivalents: total bytes allocated / 64.
The conversion is conservative: real average size is
(64+72+...+120)/8 = 92 bytes, so the 64B-eq rate slightly overstates
the equivalent-64B-allocs-per-second figure.

Measurement:
```
rep 0:  1856.3 M 64B-eq/s, 0.54 ns/64B-eq
rep 1:  1857.0 M 64B-eq/s, 0.54 ns/64B-eq
rep 2:  2180.7 M 64B-eq/s, 0.46 ns/64B-eq
rep 3:  2621.8 M 64B-eq/s, 0.38 ns/64B-eq
rep 4:  2630.7 M 64B-eq/s, 0.38 ns/64B-eq
```

**Floor B: ~2.6 G/s 64B-eq, ~0.38 ns/64B-eq** at steady state. Real
per-lane-alloc cost (not 64B-eq) is ~0.55 ns; the 64B-eq metric is
inflated by ~1.4× because the average lane size is 92B not 64B.

### What V8 sits against

V8's measured steady-state from
[V8_VS_V22_HEAD_TO_HEAD.md](V8_VS_V22_HEAD_TO_HEAD.md): **0.58 ns/alloc,
1.73 G/s** (current toolchain re-measurement).

- V8 vs Floor A (warp-aggregated): V8 is **~19× slower per lane**.
  Floor A is one atomic per warp; V8 is one atomic per lane (the slab
  bitmap claim). These are different operations.
- V8 vs Floor B (non-aggregated): V8 is **~1.05× the floor**.
  Both do per-lane atomics. V8 is within noise of the bare-atomic floor.

**This is a non-obvious result.** V8's geometric design (Viviani
scatter, per-warp slab ranges, warp-cooperative coordination) does *not*
beat a naive per-lane atomicAdd in terms of wall-clock throughput on
RTX 2060. The atomics dominate the cost regardless of which address
they hit; the L2 atomic unit's throughput is the bottleneck, not
contention on a single cacheline.

What V8 *does* provide beyond Floor B:
- **Structured slab classes** (64B/128B/256B) with per-class size
  metadata — Floor B is just bytes.
- **Free-slot recycling** via warp-cursor wrap — Floor B is bump-only.
- **Deterministic bitmap layout** so the same source compiles to
  bit-identical SASS — Floor B has no such guarantee.

These are real features, but they're orthogonal to per-lane allocation
throughput. V8's ~538×–874× speedup vs `cudaMalloc` is real and shipping;
the comparison to bump floors clarifies *why* it's fast (avoiding the
syscall, not beating the hardware atomic throughput) and *what* it
provides on top of fast (the slab structure).

## Summary table

| Regime | Throughput | ns/64B-eq | Atomic ops |
|---|---:|---:|---|
| CPU 1t per-arena | 1.95 G/s | 0.51 | none |
| CPU 6t per-arena | 11.6 G/s | 0.09 | none |
| CPU 1t shared atomic | 232 M/s | 4.31 | 1 per call |
| CPU 6t shared atomic | 158 M/s | 6.33 | 1 per call (contended) |
| GPU Floor A (aggregated) | 35.0 G/s | 0.03 | 1 per warp |
| GPU Floor B (non-aggregated) | 2.6 G/s | 0.38 (0.55/lane) | 1 per lane |
| V8 (RTX 2060, nvcc 13.1) | 1.73 G/s | — (0.58/lane) | 1 per lane |
| V22 hand-SSE 6t | 549 M/s | — (residual, not alloc) | none |

The CPU and GPU columns are not directly comparable (different hardware,
different throughput regimes), but the bump-floor rows in each let
allocator measurements be reported as "X× over the floor" — a
hardware-normalized claim.

## Reproducing

```bash
cd Testing
gcc  -O3 -march=native -fopenmp -std=c11 baseline_bump.c  -o /tmp/baseline_bump_cpu
nvcc -arch=sm_75       -O3                baseline_bump.cu -o /tmp/baseline_bump_gpu
/tmp/baseline_bump_cpu
/tmp/baseline_bump_gpu
```

SASS verification of the two GPU floors:
```bash
nvcc -arch=sm_75 -O3 -cubin baseline_bump.cu -o /tmp/baseline_bump.cubin
cuobjdump --dump-sass /tmp/baseline_bump.cubin | grep -E "VOTEU\.ANY|UPOPC|ATOMG\.E\.ADD"
```

Floor A's kernel should show repeated `VOTEU.ANY` + `UPOPC` blocks
before each `@P0 ATOMG.E.ADD`. Floor B's kernel should show only bare
`ATOMG.E.ADD` instructions with no warp-aggregation preamble.
