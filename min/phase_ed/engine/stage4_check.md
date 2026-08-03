# Stage 4: packed on-device batching + N=12 scale-up

Programs: `stage4_batch.ergo` (N=8, 21×6561 = 137 781 packed elements),
`stage4_n12.ergo` (N=12, 21×531 441 = 11 160 261). Generator:
`gen_ergo_stage4.py`.

## Design as built

- Packed block-diagonal H; per-element lookup tables LOCOF/BLKOF/BJ2E
  built at RUNTIME (identical content to DATA tables; runtime build
  chosen because N=12 DATA would be ~200 MB of source). The division-in
  -read-index question is thereby moot — no division in any kernel index
  (block offset = I − LOCOF(I), arithmetic). The lookup-table form won
  by elimination, not by a shootout.
- Iterations batched by 16 (8 ping-pong matvec pairs, 1 eval matvec, per
  -block REDUCTION kernels for rho/norm/overlap sums, packed normalize).
  Per-block convergence |Δρ| < 1e-12 at batch granularity; batches skip
  once all blocks converge.

## N=8 validation (CPU path) — PASS

All 21 (J, E0, gap) rows vs stage-2 oracle: worst |ΔE0| = 0, |Δgap| = 0
(bitwise at print precision). Named points: J=0.0 → (0, 0.5); J=1.0 →
(−2.8591343125, 0.120548). Wall time **3.34 s** vs stage3-CPU 12.9 s
(3.9×) and stage3-GPU 28.7 s (8.6×). Launch count ≈ 60 batches × ~20
kernels ≈ 1 200 (vs stage 3's ~500 000). Convergence batches: 42–44
(ground), 14–16 (deflated) — matches stage-3 cold counts (672/240).

## N=8 GPU path — BLOCKED by a runtime bug (documented, not worked
around)

The packed GPU run produced NaN (multi-store prod kernel wrote zeros),
then — after restructuring sums into per-block REDUCTION kernels —
deterministically wrong values with frozen sums. Diagnosis ladder:

| repro | result |
|---|---|
| device array → host readback (xfer_test) | works |
| SCATTER-classified host accumulate (xfer3) | works |
| IF+DO-nested kernel sequence (xfer2) | works |
| offset-index REDUCTION kernels (xfer4) | works |
| full packed batch (stage4_gpu) | **kernel outputs FREEZE after ~5 batch iterations** (S1/S2/S3 bitwise-identical from batch 5 onward; device matvecs demonstrably ran — W correct — yet sums stop updating; deterministic across runs) |

Root cause is in the Vulkan executor's buffer-state/kernel-dispatch
handling inside the repeated batch structure — a compiler-runtime bug,
not an Ergo-source issue (the same source compiles and runs correctly on
the CPU backend, 0 deltas vs oracle). No FLUSH/BARRIER intrinsic exists
to force sync from source. The `stage4_dbg.ergo` probes are preserved
for upstream debugging.

## N=12 scale-up (CPU path) — PASS with one physics fix

- First attempt segfaulted: TT was hardcoded 16 (=2×8) but the spin-1
  bond fill emits up to 2 terms per bond — 24 at N=12 — so the term
  table overflowed (silent out-of-bounds; the checker's bounds check
  only covers constant indices). Fixed: TT = 2N parameterized.
- First physics run then exposed a **shift degeneracy**: with σ = 3.0
  and N=12, Emax = +6 gives |Emax − σ| = 3 = |E0 − σ| exactly at J=0 —
  power iteration cannot separate the ground state from the spectral top
  (blocks at J = 0.0–0.3 reported E0 ≈ +6, gap ≈ 6). Fixed: σ = 4.0
  (|E0−4| = 4 > |Emax−4| = 2), NBATCH raised to 150 for the slower
  ratio at large J.
- Final run (background task bash-0lt9uowj, ~35 min): all 21 rows in
  `stage4_n12.out`, all CONV flags nonzero (8–89 ground batches, 7–137
  deflated). Validation vs the FSS N=12 series:

| J | gap (Ergo) | FSS ref | delta |
|---|---|---|---|
| 0.00 | 0.500000 (E0 = 0 exactly) | (kinetic) | exact |
| 1.00 | 0.083523 | 0.08352 | 3e-6 |
| 1.25 | 0.0876/0.0909 (J=1.2/1.3 bracket) | 0.08920 | between ✓ |
| 1.50 | 0.098654 | 0.09865 | 4e-6 |
| 2.00 | 0.121200 | 0.12120 | 0 |
| 0.75 | 0.0953/0.0869 (J=0.7/0.8 bracket) | 0.09027 | between ✓ |

All inside the 1e-4 tolerance; E0 matches too (e.g. J=2.0: −10.7606885
vs −10.760689). Small-J rows match the N=12 gap map (J=0.1 → 0.405213,
J=0.2 → 0.321439, J=0.5 → 0.142946). Note: 0.75/1.25 are not on the
0.1-step grid (same flag as stage 2/3).

## Timing summary (final, post runtime-bug fix; updated with the
dispatch-coalescing/transfer-flood compiler fixes F99a/b)

The frame-batch deferral bug (stage4 GPU freeze) was fixed upstream
(ir_codegen deferral now checks intervening CPU reads). A later compiler
round (dispatch coalescing + transfer-flood fixes, F99a/b in
core/archive/changes.md) transformed throughput again — see the last two
rows.

| configuration | wall | note |
|---|---|---|
| stage2 CPU (warm starts + early exit) | 0.235 s | reference floor |
| stage3 CPU (cold + fixed KMAX) | 12.9 s | extraction-legal structure |
| stage3 GPU | 28.7 s | ~0.5 M launches |
| stage4-CPU packed N=8 | 3.34 s | ~1 200 launches |
| stage4-GPU packed N=8 (pre-F99) | 7.62 s | validated: 0 deltas |
| stage4-GPU packed N=8 (F99a/b) | **0.27 s** (per changes.md) | 21/21 rows bitwise |
| stage4-CPU packed N=12 | ~35 min | 150 batches, σ = 4.0 |
| stage4-GPU packed N=12 (pre-F99) | 24.1 min | validated vs FSS |
| stage4-GPU packed N=12 (F99a/b) | **55.0 s** | validated: gaps ≤ 4e-6 from FSS, J=0.0 → (0, 0.5) exact, 21/21 blocks converged; profile: 4 883 compute launches, 528 frame drains, 452 frames |

Validation after the fix: N=8 GPU — all 21 rows match the stage-2
oracle with zero deltas at print precision. N=12 GPU (pre-F99) —
J=1.0: 0.083523, J=1.5: 0.098654, J=2.0: 0.121200 (all ≤ 4e-6 from
FSS), J=0.75/1.25 bracketed by off-grid neighbors, J=0.0 → (0, 0.5)
exact. N=12 GPU (F99a/b, 55 s) — same validated numbers, 21/21 blocks
with both convergence flags set.

The F99a/b fixes give 26× on the packed N=12 sweep (24.1 min → 55 s),
making the GPU path 38× faster than the packed CPU at N=12 (55 s vs
~35 min) — the packed-GPU design now wins decisively at scale, and the
bottleneck has shifted back to device compute itself (matvec FLOPs),
no longer launch/transfer overhead.

| configuration | wall | note |
|---|---|---|
| stage2 CPU (warm starts + early exit) | 0.235 s | reference floor |
| stage3 CPU (cold + fixed KMAX) | 12.9 s | extraction-legal structure |
| stage3 GPU | 28.7 s | ~0.5 M launches |
| stage4-CPU packed N=8 | 3.34 s | ~1 200 launches |
| stage4-GPU packed N=8 | **7.62 s** (user 6.1, sys 0.3) | validated: worst deltas 0 vs oracle |
| stage4-CPU packed N=12 | ~35 min | 150 batches, σ = 4.0 |
| stage4-GPU packed N=12 | **24.1 min** | validated vs FSS (deltas ≤ 4e-6; J=0.0 → (0, 0.5) exact) |

Validation after the fix: N=8 GPU — all 21 rows match the stage-2
oracle with zero deltas at print precision. N=12 GPU — J=1.0: 0.083523,
J=1.5: 0.098654, J=2.0: 0.121200 (all ≤ 4e-6 from FSS), J=0.75/1.25
bracketed by off-grid neighbors, J=0.0 → (0, 0.5) exact.

## Verdict on the packed-GPU path

- It does NOT beat everything: at N=8 the GPU is 2.3× SLOWER than the
  packed CPU (7.62 s vs 3.34 s) — ~1 200 launches on 137 k-element
  vectors is still launch/sync-dominated. It beats stage3-GPU (28.7 s)
  3.8× and stage3-CPU-cold (12.9 s) 1.7×.
- At N=12 the GPU finally wins, but only 1.45× (24.1 vs ~35 min) — the
  80× arithmetic-per-launch is real but mostly eaten by the per-block
  reduction pattern, not by launch count.
- Next bottleneck (measured structure, not guessed): the per-block
  REDUCTION kernels — 63–84 launches per batch (21 blocks × 3–4 sums),
  each reading a 0.5–6.5 M-element slice and returning one scalar with
  an accumulator readback sync. At N=12 that is ~3 700 of the ~4 900
  launches. The matvec itself (~17 launches/batch × 24 terms × 11.2 M
  elements ≈ 4.6 GFLOP/batch) is the other ~half. What would help, in
  order: (1) segmented/multi-output reduction (one kernel, 21 block sums
  — needs compiler support; currently SCATTER-accumulate stays on CPU);
  (2) fusing the rho/norm/overlap reductions into fewer passes; (3)
  dropping the eval matvec by computing rho from the last ping-pong
  output. Transfers are small (scalars + 21-entry tables) and NOT the
  bottleneck at this scale.

## Files

`gen_ergo_stage4.py`, `stage4_batch.ergo`, `stage4_n12.ergo`,
`stage4_cpu`, `stage4_n12_cpu`, `stage4_cpu.out`, `stage4_n12.out`,
`stage4_dbg.ergo` (GPU bug probes), `xfer{,_test,_2,_3,_4}.ergo` (repro
ladder), this file.
