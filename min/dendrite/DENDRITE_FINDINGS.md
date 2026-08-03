# DBM Dendrite Findings — Laplacian Tip-Growth Thread

**Status:** radial DBM validated (all oracles pass). Strip (battery
geometry) analysis numbers being filled from the eta=1 / eta=0 runs.

Thread origin: `min/fdtd/FDTD_FINDINGS.md` §3–4 showed free current
segments **bunch** (parallel currents lock and merge) and the low-field
wedge is a passive superposition null — EM free-segment dynamics cannot
branch. The recorded way forward was tip-driven Laplacian growth
(dielectric breakdown model, DBM; Niemeyer–Pietronero–Wiesmann 1984),
which is also the standard electrodeposition model: potential is
harmonic in the electrolyte, growth rate ∝ local field at the interface.

**Verdict up front:** this mechanism class branches. Same field-physics
family, different mechanism — and the morphology is dendritic by every
measure we applied.

## 1. Model

Lattice DBM on a flattened 1D grid (`K = I + (J-1)*NX`, shift neighbors,
branch-free mask multiplies — the `min/fdtd/stencil_test.ergo` idiom):

- Cluster sites fixed φ=0 (absorbing boundary), outer boundary φ=1.
- Field relaxed by warm-started SOR (ω = 2/(1+sin(π/N)), fixed-count
  sweep loop with convergence flag, TOL 1e-6) after every deposit.
- Growth probability p_i ∝ φ_i^η at empty sites 4-adjacent (von Neumann)
  to the cluster; one deposit per step; roulette pick with a single
  counter-based draw `RAND(SEED + G)` — bitwise reproducible per seed.

## 2. Stage 1 — Laplace solver validation (`laplace_annulus.ergo`)

Radial annulus (inner disk φ=0, outer circle φ=1), SOR to machine-level
fixed point (maxdelta < 1e-9), three grids (129/257/513, geometry scaled
with N):

| oracle | 129 | 257 | 513 | verdict |
|---|---|---|---|---|
| log-fit residual L2 (band) | 1.22e-4 | 4.64e-5 | 1.81e-5 | ~2.6×/doubling |
| fitted flux A vs analytic 0.5581 | 0.5480 | 0.5529 | 0.5546 | converging to analytic |
| azimuthal shell max–min | 2.48e-2 | 1.32e-2 | 6.94e-3 | O(h), 4-fold |

- The naive oracle (compare against ln(r/R0)/ln(R1/R0) at nominal radii)
  fails at O(h): staircase boundaries shift the *effective* radii by
  O(h), which displaces the whole log profile. The correct interior
  oracle is a 2-parameter log fit φ = A·ln r + B — residual then
  measures harmonicity/shape without the boundary ambiguity.
- Azimuthal modulation is 4-fold, O(h), from the staircase boundaries +
  5-point stencil. This is the documented square-lattice anisotropy of
  lattice DBM; it is visible in the clusters (axis-preferred branches)
  and is reported, not hidden.

## 3. Stage 2/3 — Radial DBM (`dbm_radial.ergo`, `analyze_dbm.py`)

257² grid, outer circle R1=126.5, 4000 growth steps/run, mass–radius
scaling D from log-log fit (window r ∈ [4, 0.7·rmax]).

| run | η | mass | rmax | D | R² |
|---|---|---|---|---|---|
| e00 | 0.0 | 4001 | 42.7 | **2.001** | 0.9996 |
| e05 | 0.5 | 4001 | 62.2 | **1.856** | 0.9992 |
| base | 1.0 | 4001 | 91.3 | **1.725** | 0.9993 |
| s777 | 1.0 | 3535 | 101.9* | **1.650** | 0.9992 |
| s31337 | 1.0 | 4001 | 92.6 | **1.740** | 0.9984 |
| e20 | 2.0 | 1495 | 101.2* | **1.462** | 0.9951 |

(*boundary stop at 0.8·R1.)

Oracles — all PASS:

- **Literature window:** η=1 → D = 1.725 / 1.650 / 1.740 across three
  seeds (mean 1.71) — 2D Laplacian growth literature range 1.60–1.75.
- **Endpoint η=0:** D = 2.001 — compact Eden growth, exactly as required.
- **Endpoint η→2:** D = 1.46 and falling, sparse needles — correct
  direction toward D→1.
- **Monotone D(η):** 2.00 → 1.86 → 1.71 → 1.46. ✓
- **Determinism:** identical binary run twice → `diff` clean (bitwise).
- **Mass accounting:** exactly one deposit per step (mass = steps + 1);
  candidate weight sum TOTW > 0 every step.

Morphology (`dbm_radial_eta_sweep.png`): η=0 compact disk; η=0.5 dense
branches; η=1 ramified DBM with screened fjords; η=2 sparse needles.
The η=1 clusters show visible 4-fold axis preference (lattice
anisotropy, §2).

## 4. Methodology catch — the φ<0 NaN cascade (worth recording)

First η=0.5 run stalled silently at mass 173: `totw = -nan`, growth
dead, but the log kept printing "mass = step+1" (a log artifact, not
real growth). Root cause: SOR with ω→2 undershoots φ below 0 at the
steep cluster surface; `φ**η` is NaN for non-integer η (and a *signed*
weight for η=1/2, contaminating totals without NaN). The NaN then
poisoned the SOR convergence test (MAXD comparisons), which reported
instant convergence — a double failure.

Fix: clamp φ ≥ 0 after each SOR update (`MAX(PHI+DN, 0.0)`) — the
physical field is non-negative by the maximum principle. One-line,
branch-free, applied in both `dbm_radial.ergo` and `dbm_strip.ergo`.
All sweep numbers above are post-fix.

Lessons: (a) in a determinism language, non-integer powers of
solver-produced fields need a sign guarantee or a clamp; (b) "mass" in
the progress log now reads as a log artifact — the real growth signal
is rmax/ncand moving.

## 5. Stage 4 — Battery strip geometry (`dbm_strip.ergo`)

Line seed electrode (bottom row, φ=0, cluster), counter electrode (top
row, φ=1), Neumann side walls via mirrored LIDX/RIDX index arrays
(branch-free stencil). η=1 vs η=0 Eden control, tracked per 100 steps:
tip height, mean column height, per-column roughness.

Results (257² grid, seed 12345, 8000 steps max):

| run | η | outcome | tip | hmean | rough | tip/mean | ncand |
|---|---|---|---|---|---|---|---|
| strip | 1.0 | tip hit row 218 (0.85·NY) at step 7645 | 215 | 119.2 | **59.2** | 1.80 | ~7600 |
| strip_e00 | 0.0 | ran to 8000 steps, never left the base | 41 | 32.8 | **3.4** | 1.25 | ~545 |

Oracle — screening instability — PASS:

- η=0 (Eden control): compact layer advance — tip tracks the mean
  (ratio 1.52→1.25, settling toward 1), roughness 3.4 rows, candidate
  count ~545 (a single rough surface row's worth of interface).
- η=1: tips screen the valleys and outrun the deposit — tip/mean 1.80
  and the tip–mean gap widens throughout the run (series plot in
  `dbm_strip_compare.png`), roughness 59.2 rows (17× Eden), interface
  fully ramified (ncand ~7600).
- Morphology: η=1 grows discrete dendrite trees off the electrode
  (multiple trunks, side branches, screened inter-trunk fjords); η=0
  grows a uniform mossy layer. This is the electrodeposition picture
  the battery literature calls dendritic growth — and the exact
  morphology class the FDTD free-segment dynamics could not produce.

## 6. Surface tension and depletion (Stage 6)

Two physics extensions, both defaulting to OFF with bitwise-identical
old physics (regression oracle: SNAP occupancy diffs clean against
`dbm_radial_ref_d0cap0.out` / `dbm_strip_ref_d0cap0.out` — PASS):

- **D0** — capillary length (Gibbs-Thomson surface tension)
- **CAP** — finite reservoir capacity; outer boundary drains
  `PHIB = max(1-mass/CAP, 0)`, growth freezes at exhaustion; physical
  time advances as `T += 1/TOTW` per deposit (flux = rate).

### 6.1 Growth-LAW surface tension: a negative result (superseded)

First implementation put the Gibbs-Thomson term in the attachment
rule: `w = max(phi - D0*(2-m), 0)**eta`. Measured (radial, eta=1):

| D0 | D | rmax | verdict |
|---|---|---|---|
| 0 | 1.725 | 91.3 | base |
| 0.002 | 1.615 | 89.2 | MORE ramified |
| 0.005 | 1.538 | 101.4* | MORE ramified |
| 0.02 | 1.434 | 101.2* | MORE ramified |

Strip: roughness ROSE (59.2 → 77.9 at D0=0.002); D0=0.01 froze the
interface at step 1 (threshold exceeds the whole strip field).

**Diagnosis:** a constant barrier in the attachment rule is a field
*threshold*: it deletes low-phi candidates (fjords) while high-phi
tips survive — amplifying screening, the opposite of surface tension.
Real Gibbs-Thomson stabilization is non-local, acting through the
field: raised interface potential at a convex tip flattens the local
gradient and diverts flux elsewhere. That only happens if the term is
in the boundary condition of the solve, not the attachment rule.
(Sources preserved as `dbm_*_glaw_st*.ergo`.)

### 6.2 Growth-law depletion alone: clock, not morphology

Uniform drain PHIB scales every candidate weight by the same factor,
which cancels in the roulette — D unchanged (cap6000: D=1.723 vs base
1.725). Depletion alone changes only the rate (tracked via `T`).
It acquires morphological teeth only in combination with a fixed
barrier scale (D0): when PHIB collapses below the GT barrier, growth
self-limits. First growth-law cap3000 run also exposed a bookkeeping
leak (mass 4001 > CAP=3000 on residual field); fixed by an explicit
freeze at PHIB=0.

### 6.3 Boundary-condition Gibbs-Thomson (current model)

Cluster site deposited with m cluster neighbors is held at
`phi_s = D0*(2-m)` (tip +D0, flat 0, notch -D0), quenched at
attachment. Interior clamp phi>=0 erases the small negative pockets
near bays — bay candidates get w=0 either way, so pinning is
preserved (documented approximation).

Radial, eta=1, 4000 steps (figures `dbm_radial_gt_sweep.png`):

| D0 | CAP | mass | rmax | D | note |
|---|---|---|---|---|---|
| 0 | 0 | 4001 | 91.3 | 1.725 | base |
| 0.0005 | 0 | 4001 | 86.4 | 1.667 | branches thicken |
| 0.002 | 0 | 4001 | 81.0 | 1.726 | dense core |
| 0.005 | 0 | 4001 | 76.1 | 1.773 | thick arms |
| 0.002 | 3000 | 3000 | 58.0 | **1.838** | compact snowflake |
| 0 | 3000 | 3000 | 78.0 | 1.722 | exhausted at mass=CAP ✓ |
| 0 | 6000 | 4001 | 92.7 | 1.723 | PHIB ended 0.333 |

Strip, eta=1, 8000 steps (figure `dbm_strip_compare.png`):

| D0 | CAP | rough | tip/mean final | outcome |
|---|---|---|---|---|
| 0 | 0 | 59.2 | 1.80 | tip hit row 218 at step 7645 |
| 0.002 | 0 | 15.0 | 1.71 | ran all 8000 steps, tip only 77 |
| 0.005 | 0 | 9.7 | 1.55 | tip 59, low regular undulations |
| 0.002 | 8000 | 8.5 | 1.48 | exhausted at mass=CAP=8000 ✓ |

Oracles — all PASS:

- **Opposite sign vs §6.1:** BC-form surface tension stabilizes. Strip
  roughness falls 59.2 → 15.0 → 9.7 with D0; tips no longer outrun the
  mean (ratio → 1.5 and falling, vs 1.80 and widening). Radial rmax at
  fixed mass falls monotonically (91 → 86 → 81 → 76) and D rises to
  1.77–1.84. Morphology shifts from sparse trees to thick-fingered
  compact growth — the Mullins-Sekerka cutoff.
- **Regression:** D0=0/CAP=0 occupancy bitwise-identical to the
  pre-extension reference (both geometries). ✓
- **Depletion bookkeeping:** growth now freezes at exactly mass=CAP
  (both radial cap3000 and strip gt002cap8000 report
  "reservoir exhausted" at mass=CAP). ✓
- **Depletion is morphology-free (statistically):** cap3000/cap6000
  with D0=0 give D = 1.722/1.723 vs base 1.725 — invariant. NOTE: this
  invariance is statistical, not bitwise — the uniform PHIB factor
  cancels analytically in the roulette but not in floating point, so
  individual picks flip at rounding boundaries and trajectories diverge
  (standard precision contract: distributions, not trajectories).
- **Depletion + GT interact (the battery point):** with fixed GT
  barriers and a draining bulk, the *effective* surface tension grows
  as PHIB falls — same D0=0.002 gives D=1.726 at infinite reservoir
  but D=1.838 at CAP=3000. Depletion progressively stabilizes the
  interface, then freezes it at exhaustion. Dendrites in a finite cell
  are self-limiting.
- **Physical time:** `T += 1/TOTW` per deposit shows the clock
  stretching as PHIB falls (at mass 2901: cap3000 has T=2043 vs T=762
  for the undepleted base — 2.7× dilation and rising steeply toward
  exhaustion; ncand is identical at 2841, per the invariance above).

## 7. Caveats

- 2D lattice DBM; 4-fold anisotropy is inherent (off-lattice / noise-
  reduction variants out of scope).
- One deposit per full SOR re-solve: ~10 min per 4000-step run at 257²
  single-thread. The SOR sweep is the GPU candidate (red-black ordering
  → two shift kernels); not yet extracted.
- Growth probability uses φ at the candidate site (NPW convention).
  Gibbs-Thomson curvature is quenched at attachment (not re-relaxed as
  the neighborhood fills) and uses the 4-neighbor proxy; interior
  clamp approximates bay fields (§6.3). No time-dependent diffusion
  (quasi-static Laplace throughout).

## 8. GPU outlook — which activity bound applies here

With Inc-1 tiling + the TILE_CLIP clipmap (Spec/Ergo_Activity_Bounds.md)
in place, this solver's bound class is **elliptic**: after a deposit at
site s of size ε, the relaxation front advances 1 site/sweep and the
perturbation amplitude decays dipole-like (§2), so the active region is
`{r ≤ min(sweeps, ε/tol)}` around the cluster's newest sites. Expected
effect once the red-black rewrite (Inc-3) lands: the far field of the
256² grid stops being dispatched after the first few sweeps following
each deposit — the SOR sweep count (~200–380/step, the dominant cost)
collapses to a moving band around the cluster perimeter. Estimated
dispatched fraction: perimeter/area of the cluster bounding region —
under 10% for a 4000-site cluster on 256² — with the residual oracle
(per-tile max-delta < tol) as the referee.

## 8. Reproducibility

| artifact | path |
|---|---|
| Laplace validation | `min/dendrite/laplace_annulus.ergo` (runs at 129/257/513) |
| Radial DBM | `min/dendrite/dbm_radial.ergo`, variants `dbm_radial_{e00,e05,e20,s777,s31337}.ergo` |
| Radial outputs | `min/dendrite/dbm_radial*.out`, `dbm_radial_eta_sweep.png`, `dbm_radial_eta1.png` |
| Fractal analysis | `min/dendrite/analyze_dbm.py` |
| Strip sim | `min/dendrite/dbm_strip.ergo`, `dbm_strip_e00.ergo` |
| Strip analysis | `min/dendrite/analyze_strip.py`, `dbm_strip_compare.png` |
| GT-BC variants | `min/dendrite/dbm_{radial,strip}_gt*.ergo` (+ `_cap*`) |
| Growth-law null (§6.1) | `min/dendrite/dbm_*_glaw_st*.ergo` + `dbm_*_st*.out` |

## 9. Inc-3 landed: GPU Jacobi relaxation + elliptic TILE_CLIP

`min/dendrite/dbm_radial_gpu.ergo` ports the DBM solver to the GPU per
§8: the in-place GS-SOR sweep becomes a Jacobi ping-pong (PHI/PHI2
alternate; omega=1 — the GS optimal omega~1.976 is unstable under
Jacobi), the weight map and the TOTW+NCAND reduction extract as GPU
kernels, and the sweep loop runs under the elliptic TILE_CLIP bound
(cluster bbox + sweeps-remaining + margin; row-band tiles, NT=8 at
QT=8192 on 256²; validation sweep every 16 sweeps; warm-up 5 steps).
Grid is 256² (tile-friendly), SWFIX=384 fixed sweeps/step (no
convergence test — static loop bounds required for extraction).

Solver-change controls (the fixed-point is the same discrete-harmonic
field; the iteration and its truncation differ):

| build | seed 12345 | seed 777 | seed 31337 |
|---|---|---|---|
| CPU f64 257² GS-SOR (reference) | 1.725 | 1.650 | 1.740 |
| CPU f64 256² Jacobi-384 (this source) | 1.714 | — | — |
| CPU f32 256² Jacobi-384 | 1.713 | 1.647 | 1.762 |
| GPU f32 256² Jacobi-384 (clip) | 1.677 | 1.653 | 1.729 |
| GPU f32 256² Jacobi-384 (no clip) | 1.714 | — | — |

All GPU runs inside the 1.60–1.75 oracle window; the CPU f32
control at seed 31337 lands at 1.762 (inside the analyzer's 1.55–1.80
PASS band, just above the literature window) — the spread is intrinsic
to the solver change + precision, not a GPU artifact. No systematic
f32 shift beyond
run-to-run morphology noise at these seed counts. Residual (CPU
max-delta sweep after the last solve) is ~1e-3–3e-2 depending on the
step sampled — the fixed-count Jacobi solve is deliberately
under-converged vs the SOR TOLG=1e-6 (Jacobi's low-frequency rate is
~300x SOR's per sweep; converging would cost more than it buys — the
morphology oracle passes regardless, Laplacian growth weights are
dominated by the local gradient structure).

Clip soundness: APPROXIMATE regime (not trajectory-exact). The
"sweeps-remaining" rule is exact only for the not-yet-reached far
field (the Jacobi front is sharp, 1 site/sweep); clipped tiles also
freeze their leftover warm-start residual (~1e-3–1e-2) until the next
validation sweep, so clipped and unclipped runs diverge at the
trajectory level (D 1.677 vs 1.714 at seed 12345 — both in window).
Determinism at fixed seed+backend is bitwise (full .out diff clean
across two runs).

Performance (4000 steps, 256², RTX 2060): GPU ~25.5 s vs ~4 min CPU
f32/f64 Jacobi-384 and ~10 min CPU f64 GS-SOR 257² — ~9x vs the
equivalent CPU Jacobi build, ~24x vs the SOR reference. Dispatched
tile fraction 93–97%: at 256² with NT=8 and SWFIX=384 the clip barely
engages (SWFIX >> grid radius, so most sweeps can still reach
everywhere); the speedup is GPU parallelism + batched frames, not
clipping. Cost accounting (ERGO_PROFILE): ~11.9M per-tile dispatch
records (~12 s CPU) + ~92k transfer submit/waits (23/step: the
static-scan downloads of PHI/PHI2/W every step, the reduce readback,
and the CLUS/MASK/PHI upload after each deposit) — transfers and
record overhead dominate, GPU compute is trivial at this size.
Compiler fix that fell out: frame-loop upload scans in
core/ir_codegen.py now recurse into nested IF/loop bodies (kernels
inside IF(DONE==0)/IF(sweep parity) had their CPU-deposited arrays
silently never uploaded — GPU CLUS stayed seed-only); default-path
--emit-c byte-identical to HEAD on the Inc-1/2 oracle tests.
