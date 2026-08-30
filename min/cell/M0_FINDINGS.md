# M0 FINDINGS — dynamic neighbor list (cell list / spatial hash)

2026-08-30. Milestone M0 of Project CELL (`min/cell/README.md`).
Backend: post-plan-A compiler-owned FMA (re-certification window closed
2026-08-29); build `v0.1-determinism-arc-73-g599d689`.

## Deliverables

- `min/cell/nlist_probe.ergo` — the probe: jittered-lattice bead cloud
  (N=2000, spacing 1.15 < RC=1.2, jitter ±0.03, random velocities
  ±0.3), LJ-ish short-range force computed BOTH ways per step (brute
  N² reference and cell list), 25 Euler drift steps with a full list
  rebuild every step. The cell-list machinery is three subroutines —
  `CELL_BUILD` (bucket + counting sort), `NBR_BUILD` (27-cell stencil,
  padded fixed-stride slot segments), `FORCE_CELL` (flat masked slot
  passes) — written engine-style so M1 can lift them verbatim.
- `min/cell/nlist_probe_control_corrupt.ergo` — negative control
  (generated from the probe by `CORRUPT = 0 → 1`; regenerate with the
  sed line in its header if the probe changes).
- `min/cell/nlist_bench.ergo` + `min/cell/run_m0_bench.py` — O3 perf
  harness (parameter sweep via `@`-tagged PARAMETER lines).
- `min/cell/mre_loop_carried_sync.ergo` — minimal repro of the
  compiler sync bug found during M0 (see "Compiler issue found").

## Oracle table

| Oracle | Result | Numbers |
|---|---|---|
| O1 force equivalence, f64 | **PASS** | max \||ΔF\|| over 25 steps = **1.78e-15** (CPU build) and 1.78e-15 (GPU build), vs the pre-registered 1e-12 class. Every step ≤ 1.78e-15; most steps 8.9e-16 (0-1 ulp of the O(1) forces). |
| O2 byte-determinism | **PASS** | CPU binary double-run byte-identical (`cmp` clean); GPU binary double-run byte-identical. |
| O3 perf, N=10k | **PASS** | whole-binary wall, 3 force evaluations, median of 3 runs: brute N² **0.6866 s** vs cell-list **0.2592 s** (CPU, 2.65×) and **0.2335 s** (GPU). Crossover shape below. |
| Negative control | **PASS** | corrupt build (every 10th bead's bucket misassigned, +1 wrapping): maxdf = **2.33** at step 1 (clean: 8.9e-16 — 12 orders up), epot off by 176 (1.7%), checksum moved. Corruption presence verified in the build: header prints `CORRUPT=1`, trailer prints `[CONTROL] CORRUPT=1 active: 200 bead buckets misassigned`, and the slot count shifts (43908 → 43766). O1 catches it decisively. |

Supporting probe facts (clean build, both targets agree): ordered
pairs 10830 → 10762 across the 25 steps (pairs genuinely form and
break; the rebuilt list tracks the N² reference every step), slots
43908 (≈22 candidates/bead), max bucket-stencil population 26 of 256
capacity, overflow trap never fires.

### O1 reduction-order disclosure (pre-registered intent)

Brute force sums each bead's neighbors in index order j = 1..N; the
cell list sums them in 27-cell-stencil bucket order (bead-index order
inside each bucket, guaranteed by counting-sort placement in index
order). Same pair SET, different summation order — the measured
1e-15 class is exactly float-summation-order noise on O(1) forces,
as pre-registered. GPU adds staged-vs-sequential reduction order on
top (Spec §9.9 class) and still lands at 1.78e-15.

## O3 perf curve (whole-binary wall, seconds, median of 3)

| N | brute CPU | cell CPU | cell GPU |
|---|---|---|---|
| 500 | 0.0026 | 0.0146 | 0.1909 |
| 1000 | 0.0086 | 0.0276 | 0.1904 |
| 2000 | 0.0293 | 0.0544 | 0.2013 |
| 5000 | 0.1737 | 0.1325 | 0.2054 |
| 10000 | 0.6866 | 0.2592 | 0.2335 |
| 20000 | 2.7546 | 0.5196 | 0.2892 |

Shape: brute scales N² (4.2× per doubling past 5k, as expected); cell
CPU scales ~linearly (2.0× per doubling past 5k). CPU crossover between
N=2000 and N=5000 — late for two documented reasons: (1) the slot
segments are padded to the fixed 256 stride the GPU segred geometry
requires, so the force passes evaluate N×256 slots regardless of the
~22 real candidates per bead (~10× padding waste, paid to keep ONE
program byte-consistent across both targets); (2) each component pass
recomputes the distance chain (engine idiom: one RMW accumulator array
per loop), so a slot costs ~3× a brute pair-eval. A CPU-only dense
variant would cross over far earlier; noted as an M1 knob, deliberately
not split now. GPU is flat ≈0.19 s — Vulkan device init floor; the
kernels themselves are sub-10ms at these sizes. GPU beats CPU cell at
N=10k+ and is 9.5× under brute at N=20k (0.289 vs 2.755 s).

Checksums agree across paths at every N to the summation-order class
(e.g. N=10000: brute …4.73273877547022328e+06 vs cell CPU
…4.73273877547022235e+06; GPU cell matches brute exactly there).

## GPU extraction — what did and didn't

Extracted (spirv build, 10 kernels): lattice init, bucket zeroing,
offset/cursor init, force zeroing, **the three FORCE_CELL component
passes as segmented reductions** (the M0 payload), the energy pass as
a staged scalar reduction, and the integrate pass. Stays on CPU by
design: counting-sort placement (histogram SCATTER — serialized), the
prefix sum (SHIFT k=1), and NBR_BUILD (nested, data-dependent bucket
walk). Build-side CPU cost is included in the O3 cell numbers.

### The extraction contract discovered (the reusable idiom)

The naive dense-packed neighbor list does NOT extract — a
scatter-accumulate `FX(NBR_I(K)) := FX(NBR_I(K)) + …` classifies
SCATTER unless the segred V1 proof fires, which requires ALL of:
1. **fixed segment geometry**: loop bound and segment count
   compile-time constants, bound = nseg × seg_len, **seg_len a
   multiple of 256** (one workgroup never straddles a segment) — hence
   the 256-stride padded segments with self-slot padding (masked to
   exact 0 by the r > 1e-12 guard);
2. **one RMW accumulator array per loop** (hence three component
   passes, like the engine);
3. **the owner table lookup INLINE in the accumulator index**
   (`FX(NBR_I(K))`, not via a named temp `KI := NBR_I(K)` — the
   candidate analysis does not follow the COPY through a named
   variable);
4. straight-line masked body (0/1 masks, no IF), constant bounds
   1..NSLOT step 1.

This is precisely the ul18_stag5 PAIR_BLK idiom; M0 confirms it
generalizes to a REBUILT (dynamic) slot list, not just init-time
static pairs.

## Compiler issue found (FIXED 2026-08-30, same window)

`min/cell/mre_loop_carried_sync.ergo`: a GPU kernel at the BOTTOM of
a loop body whose result is read by CPU code at the TOP of the next
iteration read silently STALE host data — the host-download tracker
(`core/ir_codegen.py`) only downloaded when a kernel write preceded
the CPU read in one linear body pass; the loop back-edge carried no
device→host dirty mark. Pre-fix GPU printed step sums `0, 0, 0` where
CPU correctly gave `0, 1000, 2000`. The probe's first draft (integrate
at loop bottom) hit this: GPU step-2+ forces disagreed with the
reference by O(1) because the CPU brute/cell build read stale
positions.

**Fix (this window, verifier-approved task):** the frame-loop path now
scopes the download tracker to the frame body and emits an
end-of-iteration back-edge refresh — download arrays that are
kernel-written anywhere in the body AND CPU-read anywhere in the body,
minus arrays the mid-body logic already downloaded this iteration and
minus CPU-written arrays (host copy fresh). Mirrors the existing
nested-loop refresh. Regression test: `tests/gpu_backedge_sync.ergo`
(corpus GPU-PASS). Verified: MRE prints 0/1000/2000 on GPU; this
probe's output byte-identical pre/post fix on both targets;
ul18_stag5 1000-frame GPU time unchanged (zero refreshes emitted for
it — its CPU reads were already mid-body-covered); full gate green
with zero output moves. Rule now written into Spec Part 8.1
("Host-copy coherence"). The probe keeps its integrate-at-top
ordering — it is the natural leapfrog form and its output is
unchanged either way.

## Honest notes / known limits

- The bucket grid is non-periodic (clamped indices). M1's vesicle
  doesn't need PBC; if it ever does, the stencil walk grows wrap
  arithmetic — mask form unchanged.
- Rebuild-every-step, no skin. Skin/rebuild-every-k is a perf knob
  (build is ~15% of the cell-path CPU cost at N=10k) deferred to M1.
- MAXNBR=256 overflow is trapped in the probe (reported per step,
  never fired: max 26); the bench template omits the trap (fixed
  lattice density) — noted in its header.
- CPU↔GPU outputs differ in the last ulp on epot/checksum lines
  (staged vs sequential reductions, Spec §9.9 pre-registered class);
  maxdf stays 1e-15 class on both.
- The probe is NOT wired into `tests/golden/run_corpus.py` (corpus
  covers tracked `tests/*.ergo` only). It's fast (~0.1 s CPU) and
  gate-suitable; adding it is a verifier decision.

## Reproduce

```
python -m core min/cell/nlist_probe.ergo -o /tmp/m0_cpu && /tmp/m0_cpu
python -m core min/cell/nlist_probe.ergo --target spirv -o /tmp/m0_gpu && /tmp/m0_gpu
python -m core min/cell/nlist_probe_control_corrupt.ergo -o /tmp/m0c && /tmp/m0c
python3 min/cell/run_m0_bench.py     # O3 sweep (compiles+times, ~15 min)
```
