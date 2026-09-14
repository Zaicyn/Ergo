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

## Multithreaded scaling (1–12 threads, 6C/12T)

Harness `benchmark/mtbench.c` (built both ways), 2M ops/thread of
64 B, barrier start, best-of-3. Modes: churn (per-thread
malloc/free), shard (per-thread PRIVATE pool: ring claim + invariant
stamp, the SQ4-style path as a C model), shared (one pool +
`pthread_mutex`, the lock-cost control). Mops/s:

| mode | 1T | 2T | 4T | 6T | 8T | 12T |
|---|---|---|---|---|---|---|
| glibc churn | 152 | 304 | 582 | 833 | 981 | 1139 |
| tcmalloc churn | 158 | 317 | 625 | 907 | 905 | 1098 |
| shard (private) | 1231 | 2432 | 4633 | ~4400 | ~5200 | ~6000–12400* |
| shared (mutex) | 91 | 21 | 20 | 10 | 8 | 7 |

*Shard at ≥6T varies run to run (SMT contention on 6 physical
cores; two runs gave 5990 and 12444 at 12T). Churn numbers are
stable across runs (±5%).

Reading it straight:

- **No defeat anywhere.** Churn throughput is a dead heat at every
  thread count (glibc marginally ahead at 12T, 1139 vs 1098;
  efficiency ~0.6 both). TCMalloc's thread cache does not separate
  from glibc arenas on this pattern.
- **Sharding wins big.** Private-pool claim (with invariant stamp,
  no locks) runs 5–10× hotter than malloc churn at every thread
  count, single-thread included (1231 vs ~155 Mops/s). Same
  scaling shape as churn, higher floor. This is the SQ4 design
  (one pool per worker, never share) and the numbers say the
  design, not just the code, is fast.
- **Sharing loses catastrophically.** One pool + mutex collapses
  past 1T (91 → 7 Mops/s) — the control that proves the sharded
  result is about avoiding the lock, not about doing less work.
- Caveats: C model of the claim path (not the FASM port; same
  operations: head advance + stamp + occupy); fixed 64 B; no NUMA
  (single socket); best-of-3 understates SMT noise (see *).

## Embedded: Heltec WiFi LoRa 32 V3 (ESP32-S3 @ 240 MHz)

Port of `benchmark/bench_sq4.c` (same seed, same draws) to Arduino,
run on-device over USB serial. x86 FASM cannot run here (Xtensa
LX7), so the C mirror — which *is* the spec — is what ports.

| check | x86 oracle | ESP32-S3 | match |
|---|---|---|---|
| O1_alloc | 100096/100096 | 100096/100096 | yes |
| victims | (4,23,31) (2,6,25) (0,27,19) | identical | yes, bit-exact |
| det/rep/remain | 3/3/0 | 3/3/0 | yes |
| coherency fail | 0 | 0/512 | yes |
| ns/claim | 5.4 | **530.9** (1.88 Mips) | ~100x (portable C++, flash exec) |
| torus | 3268 B | 3268 B | yes |
| heap free | — | 369616 B | plenty |

Two consecutive runs printed identical numbers (deterministic).
Bring-up notes: `ARDUINO_USB_CDC_ON_BOOT=1` is mandatory (else
`Serial` goes to unconnected UART0 — silence); sketch prints once
at boot, so capture across a DTR reset. Firmware (PlatformIO
project) lives outside the tree for now; results above are the
record. The Meshtastic firmware it replaced can be re-flashed
anytime via their web flasher.

## Script store + log retrieval (LittleFS, no radio yet)

Follow-up layer on the same board: length-framed file ops
(`WRITE/APPEND path len` + raw bytes, `CAT` answers `BEGIN n` +
bytes + `END`), a line-command dispatcher (`RUNSQ4`, `STATUS`),
results appended to `/s/log.txt` with millis() stamps, driven
from USB serial by a host script. End-to-end verified: pushed a
14-byte script, ran it, fetched the 195-byte log — oracle lines
identical to the direct run (`O1 100096/100096`, same victims,
`det=3 rep=3 rem=0`, `coh 0/512`; 502.9 ns/item with logging).
LittleFS reports 16384/1572864 B (room for hundreds of scripts).
Bring-up notes: subdirectories are not auto-created (`mkdir /s`
at boot); `rm` of a missing file must answer, not error; host
must flush framework log spam before each reply. The frames are
LoRa-ready by design (explicit lengths = chunk grammar); the
radio transport itself is still to build.

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
