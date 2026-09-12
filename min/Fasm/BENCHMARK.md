# Cross-allocator benchmark (2026-09-11 session)

Method: `benchmark/main_cpu.c` + `bench_*.c` built
`gcc -O3 -march=native -std=c11`, run `/tmp/opencode/allocator_cmp_cpu
100000 0.01 0` (100k items, 1% error rate, no churn) on Zen 2.
Cache counters via `cache_perf.h` (perf_event_open). Raw outputs:
`cmp_cpu.txt` (stdout) + `cmp_cpu.stderr.txt` (per-system detail).
Timings are single-shot at 100k items (stable at this volume;
host drift acknowledged — see SQ5_CERTIFICATION.md §3).

## Allocators (the ported bunch)

| system | ns/item | det_% | rep_% | coh | L1_hit% | instr/item | notes |
|---|---|---|---|---|---|---|---|
| V22 | 79.57 | 100.00 | 100.00 | 0/220 | 93.35 | 473.6 | **14076 silent alloc rejects live** (the deferred bug, on stage) |
| SQ4 | 2.66 | 100.00 | 100.00 | 0/512 | 99.99 | 36.6 | metadata-only; overflow probe added 2026-09-11 — **0 rejects** (was 15640), full 512-slot coherency |
| SQ5 | 30.29 | 100.00 | 100.00 | 0/256 | 98.31 | 258.4 | sweep 18.6µs, stamp_flagged=1 |
| SQ2B | 61.30 | 100.00 | 100.00 | 0/256 | 93.30 | 558.7 | sweep 18.6µs, 0 tombs at 1% |
| SQW | 59.63 | 100.00 | 100.00 | 0/256 | 91.04 | 509.1 | **49.2% skipped** (dup=500); sweep 10.2µs |
| SQM | 47.54 | N/A | N/A | 0/256 | 96.45 | 349.0 | write-amp bench, not inject/detect: **1.00 rd / 1.16 wr bytes per write** |

Notes:
- SQM's 0.00% det/rep in the raw table means "not measured"
  (`bench_sqm.c` zeroes those fields; it measures amplification).
  Presented as N/A, same convention as the GPU row.
- V22 `alloc_M/s` includes fast-fail no-ops (harness WARNING);
  its ns/item flatters the rejects. Coherency for V22 is measured
  on the repaired shell per the comparison doc.
- SQ4's silence was fixed, not inherent: SCATLT imbalance is a
  routing problem (8×32 geometry holds all 256), and a cold-path
  linear probe recovers every overflowed item. Price: 2.25 → 2.66
  ns/item (+7 instr, perfectly predicted) — same regime, still 10×
  clear of the next allocator. V22's identical disease was left
  alone deliberately (Sq2B supersedes; plan.md).
- ESF frame rows (context, not the bunch): ESF/v2 ~2.2µs/item at
  99.9–100% rep; batch variants trade rep for speed; CRC detects
  only (rep 0 by design).

## Sidecars (different workloads, not rankable above)

- **V8** (the favorite): no CPU alloc bench (GPU slab story; no CUDA
  here). CPU-side: `compute_invariant` = 32-XOR fold, whole
  no-libc driver ~1.24 ms startup-dominated; the kernel itself is
  tens of ns. Cheapest integrity per byte in the family — no
  replicas, journals, or refcounts, which is exactly why it's hard
  to beat and exactly why it protects the least.
- **SQFH**: stream validator, 427 ns/tile handoff (FASM) vs 217 C;
  lanes lin=4069 slip=2 shear=12 spike=1; slips 2/2 recovered,
  episode 1500/1512, spike 3000/17, overflow 12/12 + 0.6053 excess.

## Read

- Speed: SQ4 metadata (2.3ns) » moments (SQ5 30, SQM 48) »
  cells (SQW 60, SQ2B 61, V22 80) » frames (~2200). Two orders
  of magnitude end to end, and the ordering matches the design
  docs' price sheets.
- Cache: small structures win (SQ4 99.99% L1, SQ5 98.31%,
  SQM 96.45%); full cells sit ~91–93% with 10–15 L1 miss/item.
  LLC is ~99.9% everywhere at this volume — nothing here is
  memory-bound on Zen 2; all gaps are instruction work
  (instr/item spans 30 → 559 across the allocators, 5000+ frames).
- Integrity at 1%: 100/100 across every detection-capable
  allocator; the differentiators are elsewhere (poisson tails in
  the cert oracles, blind-class maps, amplification, blast radius).
