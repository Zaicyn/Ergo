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

## 5. Parabolic (diffusion / Schrödinger) — specified, future

Solver: explicit diffusion, or unitary Schrödinger evolution.

- **Gaussian tail:** no sharp cone; the fundamental solution is a
  Gaussian. Clip outside `r > √(4αt·ln(A0/tol))` (diffusivity α).
  Wider reach than hyperbolic — expect smaller savings.
- **Quantum vortices: never-clip.** Phase winds around a vortex
  regardless of local amplitude; clipping a low-amplitude tile between
  vortices corrupts the global phase field.

## 6. Contract summary

| piece | owner | where |
|---|---|---|
| Tile dispatch + skip | compiler | `core/ir_codegen.py` (`--gpu-tile-size`, `TILE_CLIP`) |
| Bound computation | Ergo program | per-solver `TILE_CLIP` fill |
| Soundness of skipping | Ergo program | documented in program header |
| Validation cadence | Ergo program | forced all-tiles-on step every K |
| Error vs bound audit | findings docs | measured at validation sweeps |

## 7. Reproducibility

| artifact | path |
|---|---|
| Cone clipmap oracle (bitwise) | `tests/gpu_clipmap.ergo` |
| Amplitude-envelope oracle | `tests/gpu_clipmap_amp.ergo` |
| Clip mechanism | `core/ir_codegen.py` (commit `141f4f8`) |
| Tiling mechanism | Inc-1 (commit `a3a1017` content) |
| Anisotropy measurement | `min/dendrite/DENDRITE_FINDINGS.md` §2 |
