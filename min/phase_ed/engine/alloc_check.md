# Allocator-inspired performance work — benchmark report

Patterns applied: GEO (exact-size memoization, zero steady-state alloc),
V22 (everything precomputed into LUTs, direct addressing). Files:
`index_arena.py`, `gpu_dense.py`, `bench_alloc.py`; data:
`bench_alloc.json`, logs `bench_alloc.log`, `gpu_dense_bench.log`.

## Milestone A — cache-optimized matvec (CPU, numba)

**A1 index-map arena** (V22/GEO): gather formulation
`out[x] = diag[x]·v[x] + Σ_t lut[cid[x,t]]·v[src[x,t]]` — one contiguous
int32 source arena (dim × 6N, −1 sentinel) + uint8 coefficient IDs into a
4-entry LUT + explicit offset table. One build allocation per (model, N),
zero per-term/per-call allocations.

**A2 Z-order layout**: Morton-style trit-significance interleave
(lo/hi-end alternating), arena built directly in the permuted labeling so
a fully-permuted eigsh workflow costs nothing extra per matvec.

**Correctness gate (N=8, 4 lowest eigenvalues vs existing path):**
arena max|ΔE| = 1.1e-14, arena+Z = 1.2e-14 — PASS (≪ 1e-9).

**Throughput (matvecs/sec, best sustained over 2 s):**

| N (dim) | roll-decode | arena | arena+Z | arena size |
|---|---|---|---|---|
| 8 (6 561) | 6 196 | **11 074 (+79%)** | 10 554 (+70%) | 1.3 MB |
| 12 (531 441) | 80 | **119 (+49%)** | 122 (+52%) | 153 MB |
| 14 (4.78 M) | 8.6 | **10.8 (+25%)** | 10.9 (+26%) | 1 607 MB |

- **Arena wins everywhere**, most where it stays cache-resident (N=8:
  +79%). At N=14 the arena is 1.6 GB/pass (bandwidth-bound) yet still
  +25% because it eliminates all digit divmod work.
- **Z-order verdict: NEUTRAL-TO-HARMFUL.** −5% vs plain arena at N=8,
  +2% and +1% (noise) at N=12/14. Physical reason: the chain is 1D —
  there is no 2D locality for a space-filling curve to exploit, the
  natural trit order already makes bond strides adjacent (3^i, 3^{i+1}),
  and the interleave only lengthens mid-ring strides (3→9). Recommended:
  do NOT adopt; keep natural order. (Honest negative result, as
  requested.)

## Milestone B — GPU dense pipeline

**B.1/B.2** COO template (rows/cols/kind arenas + 4-value coefficient
recipe + kinetic diagonal) uploaded once; dense build = memset + fancy
-index scatter on device: **2.91 ms per 6561² complex64 matrix** — beats
the sub-10 ms target by 3.4×. Correctness gate vs CPU complex128:
max|ΔE| = **6.0e-7** over the 4 lowest eigenvalues — PASS (< 1e-5).

**B.3 streamed syevd (gap-only, 12 points, 6561-c64):**

| streams | wall | pts/s |
|---|---|---|
| 1 | 27.6 s | 0.43 |
| 2 | 27.7 s | 0.43 |
| 4 | 27.9 s | 0.43 |

Zero scaling: one 6561-c64 `syevd` (~2.3 s) already saturates the RTX
2060 — additional streams just queue. Steady-state allocation is zero
via the cupy memory pool (blocks recycled; the GEO pattern delegated to
the pool rather than hand-rolled).

## Honest verdict — GPU dense vs CPU baseline

- **Gap-only sweeps at this size: GPU dense LOSES decisively.** 0.43
  pts/s vs ~10 pts/s (sparse Lanczos on the roll-decode matvec) and
  ~50+ pts/s with the new arena matvec (11 074 mv/s at N=8). When only
  2 eigenvalues are needed, O(dim·N) matvecs beat any O(dim³) path by
  orders of magnitude.
- **GPU dense WINS where the full spectrum or eigenvectors are the
  product**: 2.3 s per complete 6561-c64 diagonalization vs 13.4 s for
  CPU `eigvalsh` at f32 (5.8×) — and the build side is now 2.9 ms, so
  the pipeline is eigh-bound, not construction-bound. Best-fit roles:
  full-spectrum studies, level statistics, eigenvector observables at
  4000–8000-dim, and as the batch engine if a problem genuinely needs
  dense algebra.
- **Tie/irrelevant**: streaming — with a compute-saturating kernel, 1
  stream is optimal; stream pools only help small matrices (≲1000-dim,
  untested here) or kernels with idle phases.
