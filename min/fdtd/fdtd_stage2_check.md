# FDTD stage-1/2/3 report — GPU double-buffer rerun, time slit, sparse recovery

Programs (all in `min/fdtd/`):
- `fdtd_slit_db.ergo` — double-buffered double slit (rotate copies eliminated)
- `fdtd_slit_1d.ergo` — flattened 1D GPU version, on-device screen accumulation
- `fdtd_timeslit.ergo` — time-domain double slit (Tirole et al., Nature 2023 analog)
- `sparse_recovery.py` — sparse Fourier recovery of the screen profile
- analysis: `analyze_timeslit.py`, `analyze_fdtd.py`

Physics setup unchanged from `fdtd_check.md` (C2=0.25, 640×512, sponge 40,
pulse T0=200/TW=60, barrier ix=300 slits [219,230]/[283,294] d=64, screen
ix=560, PROF over T=900..1800).

## Stage 1 — double buffering, on-device accumulation, GPU rerun

**CPU double buffering works.** `fdtd_slit_db.ergo` replaces the rotate
copies with an U/UN ping-pong (two stencil passes per `DO T = 1, NSTEPS, 2`
iteration): CPU wall 1.667 s → **0.948 s (1.76×)**, output **bitwise
identical** to the rotate version (0.00e+00 per-cell delta), oracle
verdicts unchanged (λ=16 → 65.50 vs 65.00, 0.8% PASS; λ=20 → 85.00 vs
81.25, 4.6% PASS; λ=12 → 53.88 vs 48.75, 10.5% real Fresnel near-field,
d²/λL = 1.31; standing-wave nodes 7.91 vs 8.0 PASS).

**GPU zero-field bug: root cause found and fixed at source level.** The
flattened GPU version compiled and ran but produced all-zero fields.
Investigation (pingpong_test.ergo, init_dump.ergo, SPIR-V + generated-C
inspection) showed:

1. The ping-pong stencil itself is bit-exact on GPU — the earlier
   "codegen bug" suspicion was a bad probe cell (beyond the wavefront:
   200 steps × Courant 0.5 = 100 cells of propagation).
2. The real bug is in the compiler's upload scheduling: "Sync CPU state
   to GPU" is emitted only before the *outermost* frame loop. Host init
   loops sitting between the first GPU kernel and the time loop modify
   ABSORB/PASS/BOUND **on the host copy only** — they are never
   re-uploaded. The device keeps the init kernel's BOUND=0 everywhere,
   so the masked stencil degenerates to an identity copy and the field
   never propagates (screen PROF = 0 exactly).
3. Fix (source level): the whole init is computed **arithmetically
   inside the init kernel** — cell coordinates via `MOD`/`INT`,
   interior mask, cosine sponge, and barrier-with-slits as clamped
   integer expressions (`MIN`/`MAX`). Verified value-identical to the
   host-loop init (init_dump.ergo) and the resulting CPU profiles are
   **bitwise identical** to the validated double-buffered run.
4. GPU intrinsics caveat found en route: `ABS` on INTEGER lowers to
   something the NVVM pipeline rejects (vkCreateComputePipelines -13);
   `MAX(x, -x)` works. `MOD`, `INT`, `MIN`, `MAX`, `REAL` are fine.

**GPU rerun (fixed):** per-scene max |CPU−GPU| = 2.4e-5 / 1.9e-4 /
2.7e-4 absolute = **1.8e-7 / 7.0e-7 / 2.6e-7 relative** (reduction-order
FP noise in the on-device PROF accumulation). Profiles are
extraction-identical to the validated CPU results, so the oracle table
of `fdtd_check.md` stands for both backends.

**Timing: GPU still loses ~59× — transfer flood, not compute.** GPU wall
69.5 s vs CPU 1.18 s. The runtime unconditionally downloads every
kernel-written array after every dispatch (`core/ir_codegen.py:721`
region) and re-uploads host-touched arrays: per step-pair that is ~2 ×
2.6 MB stencil downloads + the 512-column source add round-trip. The
kernels themselves are sub-millisecond; the ~70 s is PCIe traffic and
submit/wait latency. This is a **runtime issue for the compiler agent**
— it cannot be fixed from Ergo source (double buffering, flattened
arrays, and on-device accumulation were all tried; the drain pattern is
unchanged). The Ergo-side work (no rotate copies, on-device PROF) is
still correct and necessary: once the runtime stops draining per
dispatch, this program needs no further changes.

`ERGO_PROFILE=1` counters for the fixed GPU run (69.5 s wall):
- 8709 compute launches, 12033 queue submit+wait cycles, 6010 frame drains (~1 drain per half-step: 3 scenes × 2000 steps)
- GPU compute itself: 1.094 ms per frame avg (k0 stencil 0.521 ms + k1 stencil 0.573 ms) ≈ **6.6 s total** — the remaining ~63 s (90%) is transfer + submit/wait overhead, i.e. the unconditional per-dispatch download flood.

## Stage 2 — time-domain double slit (Tirole et al. 2023)

`fdtd_timeslit.ergo`: no barrier. The line source (ix=40) emits **two
Gaussian-envelope pulses** at T1=200 and T2=200+Δt, in phase at carrier
λ=16 (both Δt are whole carrier periods). Probe at ix=400, row 256
records U(t) for 2000 steps; 12 scenarios: Δt ∈ {64, 96, 128} × rise
time TW ∈ {80, 40, 20, 10} (σ_t = TW/√2). CPU wall 4.8 s.

Theory: two identical delayed pulses give |S(ω)| = 2|S₀(ω)|·|cos(ωΔt/2)|
— fringes in the **spectrum** with period 2π/Δt (slits in time →
fringes in frequency).

Extraction (`analyze_timeslit.py`):
- **Period** via the Wiener-Khinchin dual: the comb with period 2π/Δt in
  |S|² ⟺ side peak of the autocorrelation at lag Δt. Autocorrelation of
  the **Hilbert envelope** (removes carrier wiggles), `find_peaks` in
  lag [30,200], parabolic refinement → Δt_rec.
- **Visibility**: parametric envelope E(ω) — Gaussian with the exact
  source width σ_ω = √2/TW, amplitude/center fitted to |S| at the
  theoretical comb maxima (where |cos|=1); V = (p95−p5)/(p95+p5) of
  |S|/E inside E's FWHM. V→1 when the pulse band resolves comb zeros,
  V→small when the band is narrower than one fringe period.

Results:

| SC | Δt | TW | Δt_rec | delta | V | verdict |
|----|----|----|--------|-------|---|---------|
| 1 | 64 | 80 | — (no side peak) | — | 0.462 | FAIL (unresolved) |
| 2 | 96 | 80 | — | — | 0.496 | FAIL (unresolved) |
| 3 | 128 | 80 | — | — | 0.625 | FAIL (unresolved) |
| 4 | 64 | 40 | — | — | 0.773 | FAIL (unresolved) |
| 5 | 96 | 40 | — | — | 0.865 | FAIL (unresolved) |
| 6 | 128 | 40 | 126.28 | 1.3% | 0.938 | PASS |
| 7 | 64 | 20 | 63.86 | 0.2% | 0.829 | PASS |
| 8 | 96 | 20 | 95.76 | 0.2% | 0.918 | PASS |
| 9 | 128 | 20 | 127.85 | 0.1% | 0.917 | PASS |
| 10 | 64 | 10 | 62.13 | 2.9% | 0.876 | PASS |
| 11 | 96 | 10 | 95.38 | 0.6% | 0.931 | PASS |
| 12 | 128 | 10 | 127.78 | 0.2% | 0.912 | PASS |

Verdicts:
- **Fringe-period oracle (5%): PASS wherever the time slits are
  physically resolved.** Resolution follows a Rayleigh-style criterion
  Δt ≳ 2σ_t: TW=80 (σ_t=57) resolves nothing, TW=40 (σ_t=28) resolves
  only Δt=128, TW=20/10 resolve everything. The FAILs are the physics
  (merged pulses = one slit, no comb), not extraction errors.
- **Visibility trend (sharper → more visible): CONFIRMED.** V rises
  monotonically as TW shrinks at Δt=64 (0.46 → 0.77 → 0.83 → 0.88) and
  Δt=96 (0.50 → 0.87 → 0.92 → 0.93), saturating at V ≈ 0.92 once the
  comb zeros fall well inside the pulse band; at Δt=128 the top three
  are saturated within noise (0.94/0.92/0.91).

## Stage 3 — sparse Fourier recovery (`sparse_recovery.py`)

Signal: the validated λ=16 screen profile (scene 2 of `slit_1d.out`),
preprocessed exactly as in the validated extraction (smooth σ=3, central
crop rows 101–412, baseline σ=25 subtracted) → oscillation on N=312
cells. The pattern is Fresnel-chirped (65-cell spacing at center
widening outward), so the recovery target is the **full-data dominant
Fourier period 75.01 cells**; the far-field oracle 65.0 applies to the
central fringes (65.5 validated in fdtd_check.md).

Method: OMP over 4096 complex exponentials, k=3 atoms, LS refit per
pick, strongest atom in the physical band [1/120, 1/30], parabolic
frequency refinement. Uniform-stride and seeded random subsampling.

| K | uniform | ok | random (median of 8) | ok/8 |
|---|---------|----|----------------------|------|
| 312 | 75.01 | Y | 75.01 | 8/8 |
| 256 | 74.67 | Y | 75.08 | 8/8 |
| 128 | 76.20 | Y | 75.70 | 8/8 |
| 64  | 75.59 | Y | 75.70 | 8/8 |
| 48  | 75.16 | Y | 75.50 | 8/8 |
| 32  | 76.37 | Y | 76.36 | 8/8 |
| 24  | 74.65 | Y | 74.11 | 8/8 |
| 16  | nan   | n | 75.49 | 6/8 |

- **Min K recovering the spacing to 5%: K = 24 uniform, K = 16 random
  (6/8 draws).** This sits right at the compressed-sensing ballpark
  K ~ k·log₂N = 3·log₂312 ≈ 25.
- Uniform K=16 collapses (OMP picks no in-band atom — 16 points /
  3 complex atoms is underdetermined and stride-20 sampling is
  coherence-prone), while random K=16 still recovers in 6/8 draws: the
  classic incoherence advantage of random sampling.

## Compiler-agent handoff (runtime issues, not fixable from Ergo source)

1. **Unconditional per-dispatch download** (ir_codegen.py ~line 721):
   every kernel dispatch is followed by `ergo_vk_download` of every
   written array, plus upload of host-touched arrays — the ~60× GPU
   slowdown on FDTD. Needed: device-resident arrays across the time loop
   (download only when the host actually reads, e.g. final WRITE).
2. **Missing re-upload after host loops between kernels**: host writes
   to STATIC arrays after a GPU kernel but before the next frame loop
   are silently never uploaded (the all-zero-fields bug above). Either
   emit "Sync CPU state" before *every* frame loop or track host-side
   dirtiness per array.
3. **`ABS` on INTEGER breaks the NVVM pipeline**
   (vkCreateComputePipelines error -13); `MIN/MAX/MOD/INT/REAL` lower
   fine.
4. Arithmetic DO-loop upper bounds (`DO K = a, N - 1`) emit invalid
   SPIR-V (`OpSLessThanEqual` Int32 vs Float64) — precomputing
   `NEND := N - 1` as INTEGER works around it.
