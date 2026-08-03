# Ergo Activity Bounds — Per-Solver Clipmap Framework

**Status:** framework + hyperbolic envelope implemented; elliptic/parabolic
bounds specified for their solver rewrites.
**Depends on:** `--gpu-tile-size` (Inc-1) and the `TILE_CLIP` mechanism
(commit `141f4f8`). No compiler changes are needed to use this framework:
the compiler owns the *skip*, the Ergo program owns the *bound*.

---

## 1. The idea

A solver's "cone of activity" is its frustum. Tiles that provably cannot
change above tolerance this step are flagged 0 in `TILE_CLIP` and skipped
by the tiled host dispatch loop. "Provably" is the operative word: the
bound must be *a priori* (derived from source history and the solver's
propagation law), never measured from the field — a per-step global field
reduction to compute the bound would reintroduce the cost the clip exists
to avoid.

Skip semantics: a skipped tile's output elements keep their stale device
values. Soundness is the **program's** contract with the compiler.

## 2. The rules (apply to every bound below)

1. **Conservative summing.** Envelopes from multiple sources add by the
   triangle inequality, `|ΣAᵢ| ≤ Σ|Aᵢ|` — worst-case coherent addition.
   Never budget for cancellation.
2. **Never-clip classes.** Rotational/curl content, topological defects
   (phase vortices), and guided/surface modes do **not** decay by
   geometric spreading. Any tile hosting them — or that can come to host
   them — stays dispatched.
3. **Scattering budget.** Source-centric envelopes assume free space.
   Boundaries and inhomogeneities re-scatter; carry a scatter term or a
   margin multiplier that covers it.
4. **A priori tracking only.** The amplitude/activity budget is computed
   from source history (analytic, cheap). Field-measured feedback is
   allowed only at validation sweeps (rule 5).
5. **Validation sweeps.** Every K steps, force all tiles on for one full
   step and (where practical) compare the true error against the bound.
   This is the referee; a bound that fails validation gets its margin
   raised, never its error check loosened.
6. **Anisotropy margin.** Square-lattice envelopes are direction-
   dependent (4-fold anisotropy measured in the Laplace solver,
   `min/dendrite/DENDRITE_FINDINGS.md` §2). Bounds carry a margin
   factor for it.

## 3. Hyperbolic (FDTD wave) — IMPLEMENTED

Solver: 2D leapfrog wave equation (`min/fdtd/stencil_test.ergo` idiom).

- **Cone bound (sharp, bitwise):** the discrete domain of influence
  grows one cell (L1) per half-step; after T steps all nonzero field is
  inside radius 2T (+margin). With zero initial field, skipped tiles
  compute exact 0.0 — the clipped run is *bitwise* identical to full.
  Oracle: `tests/gpu_clipmap.ergo` (32.6% dispatched at 60 steps).
- **Amplitude envelope (tighter, error-bounded):** point-source waves
  in 2D decay as `1/√r` — but in 2D there is **no Huygens principle**:
  the wave leaves a ringing wake behind the front, so a retarded-*value*
  envelope `|A(t − r/c)|` is UNSOUND (it falls to ≈0 behind the front
  while the wake still rings at O(0.1); measured 5×10⁵× oracle
  violation in `tests/gpu_clipmap_amp.ergo`'s first implementation).
  The honest 2D bound is the retarded **cumulative** sum
  `PSUM(t − r/c) = Σ_{s≤t−r/c} A(s)` — exactly zero before the front
  arrives (sharp causality, tighter than the cone) and covering the
  wake afterwards. Per tile: `E = MARGIN · PSUM(t − r/c)/√max(r,r0)`;
  clip when `E < TOL_ENV`. Oracle: `tests/gpu_clipmap_amp.ergo` —
  max error 1.4e-7 ≤ TOL_ENV·MARGIN = 4e-7 vs full run, dispatched
  30.6% (beats the cone's 32.6% via the sharper front edge; the wake
  itself is NOT clippable at these tolerances — on large grids the
  advantage stays at the front edge, that is 2D physics not a
  mechanism limit). NOT bitwise — documented in the test header.
- With inhomogeneities or reflective boundaries: add a scatter budget
  (incident × worst-case reflection coefficient). Guided modes along
  interfaces: never-clip (rule 2).

## 4. Elliptic (Laplace relaxation / DBM) — specified, lands with Inc-3

Solver: Jacobi/red-black relaxation of ∇²φ = 0 with warm starts
(`min/dendrite/dbm_radial.ergo` after the red-black rewrite).

- **Sharp front:** one Jacobi/red-black sweep propagates change exactly
  one lattice site. After S sweeps, nothing beyond S sites from the
  last change has moved at all.
- **Amplitude decay:** a local perturbation of size ε decays
  multipole-like with distance (dipole-like decay measured against the
  analytic annulus solution, DENDRITE_FINDINGS §2). Amplitude reach:
  `R(ε) ~ ε/tol` sites for dipole decay in 2D.
- **Clip rule:** after a deposit at site s, active region =
  `{r ≤ min(S, R(ε))}` around s, where ε = field change at s.
- **Validation:** the SOR/Jacobi residual (max-delta) is already
  computed every sweep — a per-tile residual below tol for K
  consecutive sweeps is the measured backstop, but the a priori bound
  above is the primary clip.
- **Precision caveat (see §6):** fjord weights φ~1e-8 underflow f32 —
  a systematic tip bias, not noise. The far-field tail's handoff is a
  moment-matched multipole proxy in f64, not CPU relaxation.

## 5. Parabolic (diffusion / Schrödinger) — specified, future

Solver: explicit diffusion, or unitary Schrödinger evolution.

- **Gaussian tail:** no sharp cone; the fundamental solution is a
  Gaussian. Clip outside `r > √(4αt·ln(A0/tol))` (diffusivity α).
  Wider reach than hyperbolic — expect smaller savings.
- **Quantum vortices: never-clip.** Phase winds around a vortex
  regardless of local amplitude; clipping a low-amplitude tile between
  vortices corrupts the global phase field.

## 6. The frozen state (precision handoff pattern)

Two thresholds must not be conflated:

- **TOL_ENV** — physics tolerance: below this the contribution is
  negligible; clip (state 0).
- **NOISE_FLOOR** — representational limit: `K_NF · eps_f32 · A_ref`.
  Below this the GPU isn't computing decay, it's computing rounding
  noise.

Regime check (do this per solver before reaching for this pattern):
if NOISE_FLOOR < TOL_ENV everywhere, tiles clip on physics before
precision binds and the two-state framework suffices. Hyperbolic on
our grids: floor reached at r ~ 10¹² cells — **edge case**. Elliptic
(DBM): the far-field tail IS the computation (fjord weights φ~1e-8 vs
exact 0 change morphology; f32 underflow is a systematic tip bias, not
noise) — the noise floor is the **normal operating condition** and
Inc-3's f32 scope is distribution-level morphology only.

**States (program-maintained; no compiler changes — frozen is 0 on the
GPU side plus a program-side ownership transfer via download_at /
upload_at):**

- 0 — provably unchanged; GPU-stale-but-correct (skip).
- 1 — dispatched; GPU-authoritative.
- 2 — frozen: envelope crossed NOISE_FLOOR above TOL_ENV; GPU stops
  touching it, CPU owns the state.

**Eager frontier, lazy interior.** A frozen tile adjacent to a live
tile supplies stencil halo values; stale halo injects error into the
live region. Therefore freeze only stencil-closed interiors — the
frontier band stays dispatched (eager by construction). Interior
frozen tiles are read-only and can be fully lazy: their value is
computed only when queried.

**Resume modes:**

- *Analytic* (hyperbolic, homogeneous media): snapshot = pulse
  parameters; evaluate the closed-form Green's function in f64 at any
  (t, r) directly — jumps to arbitrary t, no accumulated integration
  error. Superposition does NOT break this (linear equation — any
  pulse count is closed-form); inhomogeneity/scatterers and
  nonlinearity DO.
- *Moment-matched multipole proxy* (elliptic): the cluster's far field
  is fixed by its boundary values; snapshot = cluster moments,
  evaluate the multipole series in f64. Cheaper and more accurate than
  CPU-relaxing the frozen region.
- *Numerical f64 continuation* (parabolic, or inhomogeneous
  hyperbolic): snapshot = full tile state + boundary trace; lazy
  queries cost O(t − t_freeze) catch-up (fine if rare), else eager
  stepping with a documented budget.
- *Affine range remap* (any LINEAR PDE — Laplace, wave, diffusion,
  Schrödinger): the PDE is invariant under
  `phi_local = (phi − floor)/(ceiling − floor)` with floor/ceiling from
  the boundary trace — the same solve runs at full f32 precision in
  the local window instead of f64. VALIDATED
  (`min/dendrite/dbm_zoom.ergo`): remapped f32 vs f64 reference in a
  DBM bay window, max relative error 3.1e-7 vs unremapped 1.5e-3
  (~4700× better; the unremapped error is tolerance truncation at the
  global scale — exactly the noise-floor conflation of this section).
  Boundary-trace error bounds the zoom; remap-back onto the global
  grid is lossy (analysis-only mode, or low-pass reinsertion).

**Re-entry (thaw).** A frozen tile's envelope can rise again (new
pulse, cluster growth). The program re-evaluates the same a priori
bound over the frozen set each step (cheap, analytic) and thaws 2→1
with an f64→f32 upload — an honest, documented precision event.

**Oracle:** full f64 CPU reference vs frozen-clipmap run; error at
query points ≤ tol; frontier never stale by construction.

## 7. Contract summary

| piece | owner | where |
|---|---|---|
| Tile dispatch + skip | compiler | `core/ir_codegen.py` (`--gpu-tile-size`, `TILE_CLIP`) |
| Bound computation | Ergo program | per-solver `TILE_CLIP` fill |
| Soundness of skipping | Ergo program | documented in program header |
| Validation cadence | Ergo program | forced all-tiles-on step every K |
| Error vs bound audit | findings docs | measured at validation sweeps |

## 8. Reproducibility

| artifact | path |
|---|---|
| Cone clipmap oracle (bitwise) | `tests/gpu_clipmap.ergo` |
| Amplitude-envelope oracle | `tests/gpu_clipmap_amp.ergo` |
| Clip mechanism | `core/ir_codegen.py` (commit `141f4f8`) |
| Tiling mechanism | Inc-1 (commit `a3a1017` content) |
| Anisotropy measurement | `min/dendrite/DENDRITE_FINDINGS.md` §2 |
