# Allocator comparison: SQ4 vs glibc malloc vs TCMalloc

Single-threaded fixed-size churn on Ryzen 5 3600, N=100096 ops
(SQ4's own count), best-of-5, `CLOCK_MONOTONIC`. TCMalloc via
`-ltcmalloc` (gperftools, verified linked). SQ4 number is its FASM
binary's `SQ4T` line re-run for this doc (544392 ns → **5.44
ns/claim**); the checked-in `out.fasm.txt` reads 563360 (5.63),
same ballpark.

## ns/op (alloc-only | batch alloc+free | churn pair)

| size | glibc a | glibc b | glibc c | tcmalloc a | tcmalloc b | tcmalloc c | SQ4 claim |
|---|---|---|---|---|---|---|---|
| 16 | 20.0 | 34.0 | 6.1 | 5.5 | 13.3 | 6.5 | — |
| 64 | 37.0 | 55.2 | 6.6 | 6.6 | 15.1 | 6.5 | **5.4** |
| 256 | 111.7 | 153.2 | 6.5 | 14.7 | 29.9 | 6.5 | — |
| 1024 | 410.5 | 544.5 | 6.3 | 34.1 | 55.3 | 6.5 | — |
| 4096 | 1593 | 1932 | 17.9 | 66.4 | 103.4 | 6.5 | — |

Touch-one-word variants measured identical (±1%) at every cell, so
memory touch is not the differentiator — mechanism is.

Overhead per object: glibc +8 B at all sizes (24/72/264/… usable);
TCMalloc +0 B (exact size classes); SQ4 ~6–8 B/slot (4 B invariant
+ occupancy/frozen bytes + shared heads, from the torus layout).

## Reading it honestly

- **SQ4's claim path (5.4 ns, invariants included) beats
  TCMalloc's alloc-only (6.6 ns at 64 B)** — ~1.2× faster while
  computing a position stamp per slot. That is the headline, with
  the caveats below.
- **TCMalloc dominates everywhere else**: batch (13–103 ns vs
  glibc's 34–1932 — size classes + caching absorb arena pressure
  that crushes glibc at 100K live blocks), arbitrary sizes, and
  zero rounding overhead. glibc only competes on the hot churn
  fast path (~6.5 ns all around, tcache doing its job).
- **Scope is the real difference, not speed.** SQ4 allocates
  fixed-size slots from a 256-slot pool and never frees (tombstone
  + recycle model); it has no threads, no size classes, no
  fragmentation story. TCMalloc is a general allocator with thread
  caches, profiling hooks, and twenty years of production. This
  bench is single-threaded, which flatters SQ4 and understates
  TCMalloc's best card — multithreaded scaling is untested here.
- **Why pick SQ4 then:** the features TCMalloc doesn't have —
  per-slot position invariants (detection 100% by construction),
  repair-by-rewrite, coherency walks, deterministic seeded audit
  oracles (O1–O4), slot/bin/ring/shell geometry with frozen and
  tombstone states. The comparison shows those features cost
  nothing measurable on the claim path.

## Reproduce

```
gcc -O2 -std=c11 -D_GNU_SOURCE -o /tmp/ab_glibc benchmark/allocbench.c
gcc -O2 -std=c11 -D_GNU_SOURCE -o /tmp/ab_tcm benchmark/allocbench.c -ltcmalloc
/tmp/ab_glibc; /tmp/ab_tcm
min/Fasm/SQ4/sq4 2>/dev/null | grep SQ4T   # claim ns / 100096
```

Harness: `benchmark/allocbench.c`. Follow-ups, not done:
multithreaded scaling (expected to favor TCMalloc), fragmentation
under adversarial patterns, SQ4 claim path under pool pressure.
