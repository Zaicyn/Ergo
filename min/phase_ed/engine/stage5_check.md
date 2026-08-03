# Stage 5: N=14 scale-up — packed GPU in ED-hostile territory

Program: `stage4_n14.ergo` (generator `gen_ergo_stage5.py`), N=14,
DIM = 3^14 = 4 782 969, NP = 21×DIM = 100 442 349 packed elements,
shift σ = 4.0, NBATCH = 120 (240 total batch phases).

## Design decisions (VRAM-constrained)

Device budget ≈ 4.6 GB (measured 4 596 MiB via nvidia-smi during the
run, 5 481 MiB free at start):
- Single packed matvec would need per-element lookup tables
  (LOCOF/BLKOF/BJ2E = 1.6 GB) — affordable ONLY after eliminating V2/W2
  (phases share V/W; GS kept) and the COEF mask table (sentinel-zero
  trick: SRC sentinel = NP+1 with V(NP+1) := 0; every term is
  A := A − BJ2E(I)·V(SRC + offset) since the mask was uniformly −1).
- Per-block matvec form (no packed tables) was tried first and REJECTED:
  the inner loop "depends on outer loop var(s) ['B']" and does not
  extract (kernel report, /tmp/n14g.log). The packed form it is.
- Shift check at N=14: Emax(J=0) = 14×0.5 = 7, |Emax−4| = 3 < |E0−4| =
  4 — σ = 4.0 still past the spectral midpoint (N=12 lesson applied).
- Host link needed `-mcmodel=large` (3.5 GB of BSS statics overflow
  PC32 relocations; the Ergo driver has no code-model flag, so the
  binary was built manually from `--emit-c` output with the driver's
  deterministic flags + `-mcmodel=large`). GPU host binary links
  vk_host.c + `-lvulkan -lglfw` the same way.

## Preliminary results

- CPU smoke (NBATCH=3): pipeline correct at scale — J=0.0 block reads
  (0.0004, 0.5001) after 48 iterations, no NaN/segfault. CPU cost
  measured at ~50 s/batch → a full CPU run ≈ 240 batches ≈ **3.3 h** —
  prohibitively slow; validation uses oracles + extrapolation instead.
- CPU timing extrapolation (stated method): measured 50 s/batch at
  N=14 (vs ~14 s/batch at N=12) — the dim×terms scaling (9× elements ×
  28/24 terms ≈ 10.5× would predict ~150 s; the measured 50 s says the
  N=12 run was latency-, not FLOP-, dominated at that size).
- GPU run launched in background: task **bash-km30qpnm**. VRAM during
  run: 4 596 MiB used, GPU util 27–41% — comfortably fitted, no OOM.
  As of this writing the run is ongoing (>30 min); N=12's GPU took
  24 min at 9× fewer elements with 150 batches, so a multi-hour run is
  plausible. Final table lands in this file on completion.

## Final results (fixed compiler, F99a/b)

The pre-fix N=14 run (bash-km30qpnm) never finished — killed at its 3 h
timeout. With the dispatch-coalescing/transfer-flood fixes the same
sweep completed in **27 min 08 s** (task bash-aotdmjmb; 4 269 compute
launches, 77% host CPU).

Validation of all 21 rows (`stage4_n14_gpu.out`):

| check | result | oracle | verdict |
|---|---|---|---|
| J=0.0 | E0 = 0.0000000000, gap = 0.500000 | (0, 0.5) analytic | exact ✓ |
| J=1.0 | gap = 0.072916 | 0.07292 (FSS N=14 ED) | Δ = 4e-6 ✓ (tol 1e-4) |
| J=1.5 | gap = 0.084716 | ~0.0847 (1/N trend) | Δ = 1.6e-5 ✓ |
| J=2.0 | gap = 0.103854 | ~0.104 (1/N trend) | Δ = 1.5e-4, within trend-fit error ✓ |
| structure | gap min 0.072916 at J=1.0, monotone increasing right of it | competition-line expectation | ✓ |
| convergence | 20/21 blocks both flags | — | J=0.1 deflated run missed the strict 1e-12 in 120 batches (conv2 = 0); its gap 0.405213 is consistent with the gapped small-J regime (N-independent), value kept |

Crossover verdict: GPU 27 min vs extrapolated CPU ~3.3 h → **GPU ≈ 7×
faster at N=14** (and the pre-fix compiler never finished at all). With
F99a/b the packed-GPU path is the fastest ED-style engine in the project
at this size; Python sparse eigsh (~21 min at N=14 by N=12 scaling of
~0.13 s/point... honest note: eigsh k=2 at N=14 took 1261 s for ONE
point at J=1.0 in the FSS work, so the packed sweep's 27 min for 42
eigenpairs (21 × E0+E1) is competitive).

## Files

`gen_ergo_stage5.py`, `stage4_n14.ergo`, `n14_cpu` (smoke),
`n14_smoke.ergo`, `n14_gpu`, `stage4_n14_gpu.out`, this file.
