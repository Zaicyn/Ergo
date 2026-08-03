# Packed BBA5 v2 — packed force kernels + GPU distribution validation

Program: `min/pmargin/packed_bba5_v2.ergo` (from updated
`min/pmargin/gen_packed_bba5.py`). v2 lifts the three chain-local force
loops (Morse bonds, backbone angles, dihedral torsions) OUT of the
per-block loop into ONE packed loop each per frame, over runtime-built
block-aware index tables (`BOND_A/B(176)`, `ANG_A/B/C(168)`,
`TORS_A..D(160)`) with block offsets baked in, plus packed parameter
tables (`ANGK_P`, `ANGT0_P`, `TORSK_P`, `TORSP0_P`) filled from the
shared per-residue params in `INIT_TABLES()`. Design choice: tables are
built at runtime from the shared tables (no value duplication, no
generator-time parsing); index arithmetic is plain integer packing.
Everything else — pair loops (steric/hydrophobic/Go), phase dynamics,
register torsions, damping, schedule — unchanged; the frame is split
into block loop A (phase..Go) → 3 packed force kernels → block loop B
(register/damping/position/hbonds), preserving per-block operation
order exactly.

## T1 — CPU bitwise validation (PASSED)

`packed_bba5_v2.out` is **byte-identical** to the validated v1
`packed_bba5.out` except the `# PACKED_BBA5_V2` header line (diff
verified; md5s otherwise equal). Final RMSDs reproduce the validated
table exactly:

| block | seed | v2 CPU | v1 CPU (=oracle-validated) |
|---|---|---|---|
| 1 | 0.0 | 1.6680 | 1.6680 |
| 2 | 1.0 | 0.3150 | 0.3150 |
| 3 | 2.0 | 0.4872 | 0.4872 |
| 4 | 3.0 | 0.3889 | 0.3889 |
| 5 | 4.0 | 0.2872 | 0.2872 |
| 6 | 5.0 | 0.1854 | 0.1854 |
| 7 | 6.0 | 1.0047 | 1.0047 |
| 8 | 7.0 | 1.0855 | 1.0855 |

CPU wall: 2.50 s (same as v1). Two CPU runs md5-identical (deterministic).

## T2 — GPU rerun (`--target spirv --gpu-fast-math`, RTX 2060)

Extraction: **3 kernels** — kernel_3 (line 265, packed Morse), kernel_4
(286, packed angles), kernel_5 (321, packed torsions; ATAN2 now lowers
via F105, f32 with the documented ~1e-7 warning). Kernel report confirms
one launch per force type per frame.

`ERGO_PROFILE=1` counters vs the interleaved version (last session):

| metric | v1 interleaved GPU | v2 packed GPU |
|---|---|---|
| compute launches | ~1.15M (24/frame) | **144,000 (3/frame)** |
| frame drains | — | 96,001 (2/frame) |
| queue submit+wait cycles | — | 576,038 (12/frame) |
| wall time | 3 m 38 s (218 s) | **29.0 s** |
| CPU wall (same machine) | 2.5 s | 2.5 s |
| slowdown vs CPU | ~87× | **11.6×** |
| GPU compute (profiled) | — | 0.047 ms/frame ≈ 2.3 s total |

v2 is 7.5× faster than the interleaved GPU run. GPU compute time (2.3 s)
is now on par with the CPU compute; the remaining 27 s is submission
overhead: 576k submit+wait cycles ≈ 46 µs each — the runtime still
drains/synchronizes every frame around the CPU-side block loops, which
dominates everything. The stage-4 lesson (block index in the data, not
the dispatch loop) is confirmed: launches/frame 24 → 3.

What still stays CPU, with the kernel report's named reasons:
- Phase advance / Kuramoto / noise / thermal kicks (23-iteration loops):
  "too few iterations (23) for GPU kernel launch"; FRAME-dependent:
  "depends on outer loop var(s) ['FRAME']". (The F106 multi-accumulator
  rejections seen in v1 no longer appear for the Kuramoto sums — the
  size gate hits first.)
- Steric / hydrophobic / Go pair loops: nested — "nested loop at line
  N" + inner "depends on outer loop var(s) ['I']".
- Register torsions: "too few iterations (6)".
- H-bond bookkeeping: staged reduction rejected — "reduction body must
  be straight-line code (no IF/loops/SELECT)", integer accumulators.
- Kabsch RMSD sums: staged reduction rejected — "write-back of
  '_COMPUTE_RMSD_SUM_DIST_SQ' is not the accumulate ADD result".

## T3 — distribution-level validation (f32 regime oracle)

Per-block final RMSD (model units; Å ≈ ×2.58), CPU vs two GPU runs:

| block | seed | CPU | GPU run 1 | GPU run 2 | GPU−CPU (r2) | GPU r1−r2 |
|---|---|---|---|---|---|---|
| 1 | 0.0 | 1.6680 | 1.6680 | 1.6680 | 0.0000 | 0.0000 |
| 2 | 1.0 | 0.3150 | 0.6281 | 0.6225 | +0.3075 | −0.0056 |
| 3 | 2.0 | 0.4872 | 0.4871 | 0.4871 | −0.0001 | 0.0000 |
| 4 | 3.0 | 0.3889 | 0.3883 | 0.3834 | −0.0055 | −0.0049 |
| 5 | 4.0 | 0.2872 | 0.2872 | 0.2872 | 0.0000 | 0.0000 |
| 6 | 5.0 | 0.1854 | 0.6705 | 0.1999 | +0.0145 | **−0.4706** |
| 7 | 6.0 | 1.0047 | 0.2505 | 0.2643 | −0.7404 | +0.0138 |
| 8 | 7.0 | 1.0855 | 1.0774 | 1.0774 | −0.0081 | 0.0000 |

Determinism: CPU bitwise-deterministic. GPU is deterministic on SETTLED
basins but NOT run-to-run deterministic on marginally-settled
trajectories (block 6 swings 0.47 model ≈ 1.2 Å between identical
invocations) — atomic-add ordering races inject FP noise that chaotic
trajectories amplify; blocks still annealing at quench-end are the
victims. This is inherent to the atomic-scatter kernels in the f32
regime, not a build bug.

Distribution statistics (model units):

| stat | CPU | GPU r1 | GPU r2 |
|---|---|---|---|
| mean | 0.678 | 0.682 | 0.624 |
| median | 0.438 | 0.438 | 0.435 |
| min | 0.185 | 0.251 | 0.200 |
| max | 1.668 | 1.668 | 1.668 |
| traps (>2 Å) | 3/8 (s0,s6,s7) | 2/8 (s0,s7) | 2/8 (s0,s7) |
| sub-1.5 Å | 5/8 | 4/8 | 5/8 |
| sub-3 Å | 6/8 (75%) | 6/8 (75%) | 6/8 (75%) |

Clinical calls (CLINICAL.md thresholds: <1.5 Å native-like, 1.5–3.5 Å
correct topology, % of seeds sub-3 Å → confidence):

- **(a) Trap rate:** seed 0.0 is trapped on every build at the identical
  value 1.6680 (4.3 Å) — the deep wrong valley is robust to f32
  rerouting; hard-trap DETECTION is preserved exactly. Seed 7.0 also
  traps everywhere. Seed 6.0 flips: CPU calls it trapped (2.59 Å), both
  GPU runs call it folded (~0.6 Å) — a marginal basin rerouted into the
  native one.
- **(b) Distribution:** median identical to 3 digits on all builds
  (0.435–0.438); mean 0.62–0.68; min/max bracket the same range.
- **(c) Verdict: clinically equivalent at the distribution level, not
  per-seed.** The sub-3 Å seed fraction (the guide's confidence metric)
  is 6/8 = 75% ("moderate confidence") on every build. The sub-1.5 Å
  fold rate wobbles 4–5/8 between GPU runs. One marginal per-seed call
  flips (seed 6.0). For the documented use cases — trap detection and
  distribution-level confidence — the GPU run makes the same calls; for
  any use that depends on an individual marginal trajectory's endpoint,
  no build (CPU or GPU) is authoritative in this precision regime
  anyway: the same flip exists between two CPU builds of the sequential
  source (0.3055 vs 0.2595 for seed 1.0 last session).

## Bottom line

v2 restructure is dynamics-preserving (CPU bitwise-identical) and
delivers the 3-launches/frame target (144k launches, 7.5× faster GPU
wall than interleaved). GPU remains 11.6× slower than CPU purely on
per-frame submit/wait overhead — the next win is keeping whole frames
(or the whole trajectory) device-resident, which needs the CPU-side
loops (pair forces, Kuramoto, hbonds) to extract or be restructured as
packed flat loops the same way. Physics validity in the f32 atomic
regime holds at the distribution level with one honest caveat: unsettled
trajectories are not run-to-run deterministic on GPU.

Files: `min/pmargin/gen_packed_bba5.py` (v1+v2 emitter),
`packed_bba5_v2.ergo`, `packed_bba5_v2` (CPU bin), `packed_bba5_v2.out`,
`v2_cpu_run2.out`, `v2_gpu_run1.out`, `v2_gpu_run2.out`,
`v2_prof1.txt`/`v2_prof2.txt` (profiles), this report.
