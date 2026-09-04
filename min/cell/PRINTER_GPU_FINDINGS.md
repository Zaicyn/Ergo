# PRINTER_GPU FINDINGS — review of work/ + GPU render build

2026-09-04. Two parts: (A) review/verification of the parallel
session's `work/proposedFixes/` and `work/vesicle_printer/` under OUR
current compiler (`v0.1-determinism-arc-76-gfc721c2`, fragile-FMA fix
included); (B) the GPU/render printer build and what blocks it.

## A. Review verdicts — everything claimed verifies as-is

### work/vesicle_printer/

- `vesicle_printer.ergo` (default ring) compiles and runs in **0.42 s**
  (their doc: ~0.4 s). FINAL rmean 11.1869 rstd 0.6019, kT≈0.22,
  nout 0 — healthy free ring, matching the spec's dynamic-stability
  claims (rmean 11.1575±0.62 class).
- **All three static certs PASS, matching their published numbers to
  the digit** (engine `CFG`/`FRC` rows vs `cert_oracles/`):

  | cert | config max_abs | forces max_abs | doc values |
  |---|---|---|---|
  | ring | 3.553e-15 | 7.347e-12 | 3.6e-15 / 7.3e-12 |
  | patch | **0.0 (byte-exact)** | 7.128e-14 | byte-exact / 7.1e-14 |
  | stack | 3.553e-15 | 1.691e-12 | 3.6e-15 / 1.7e-12 |

  CERT energy lines match the spec's 13–15-digit values exactly (e.g.
  ring epair −50.589767111093373, patch ebend −1189.5 exactly).
- `printer_mirror.py` FD validation runs clean: ring max_rel
  **1.362679e-06**, patch **8.850394e-07** (doc: 1.36e-6 / 8.85e-7).
- `vesicle_printer_stack.ergo` CPU run: FINAL rmean 3.1063 rstd
  0.8445 zstd 1.3909 nexp 1 nout 0 — **digit-identical** to the spec's
  engine closure numbers.

### work/proposedFixes/

- `vesicle_asm_opt.ergo` (MIRROR=1) vs `m1_mirror_stable.py`:
  **MIRROR PASS**, max|dF| = 1.364242e-12, max_rel = 4.951595e-14 —
  exactly their published values.
- `vesicle_asm_nematic.ergo` (MIRROR=1) vs `m1_mirror_nematic.py`:
  **MIRROR PASS**, max|dF| = 1.364242e-12, max_rel = 5.995910e-14 —
  exactly their published values. (Their nematic q² bend term is the
  fix for the leaflet-frustration heating found in the M1 session —
  their FD validation of it holds.)
- Their compiler fix doc (`ergo-fragile-fma-compiler-fix.md`) and
  `ir_codegen.py`/`test_fragile_fma_regression.py` are the already-
  landed fc721c2 — not re-applied, not re-tested (per instructions).

Nothing in either folder needed modification. Nothing is broken in
what they shipped *for the CPU path*.

## B. GPU printer build

`min/cell/vesicle_printer_gpu.ergo` — the stack variant (PRINTMODE=4,
two-ring closure + cargo, 14000 steps — the best visual story) plus
render-only additions, physics-inert by construction:

- `POS_X/POS_Y/POS_Z(704)` + `COLR(704)`: origin-centered copies of the
  bead/inclusion positions (the `--render` particle SoA contract),
  refreshed per step by `RENDER_COPY`; un-emitted monomers park at
  +999 (outside the view volume); COLR 0/1/2 = head/tail/inclusion.
- `NPART`/`BOX_SIZE` parameters for the renderer's count/world-scale
  detection.
- **CPU build verified**: double-run byte-identical; stdout
  byte-identical to `vesicle_printer_stack.ergo` (the render copies do
  not touch physics — closure FINAL digits preserved).

## RESOLUTION (2026-09-04, follow-up task): both blockers FIXED

Both blockers were fixed in compiler-owned code under the brief's
discipline (regression tests first, full gate re-run). The story turned
out deeper than the original diagnoses — recorded honestly:

### B1 fixed — THREE edges of the residency/tracking graph, plus a
### fourth root cause found on the way

The cert-ring MRE now produces the exact CERT energies on spirv
(epair −50.589767111093373 = CPU to the last digit), and the stack
closure on GPU tracks the CPU run through the march (epair −191.4292
vs −191.4295 at step 4000) with FINAL morphology in the certified
statistical band (GPU rmean 3.006 / zstd 1.302 / nexp 0 vs CPU 3.106 /
1.391 / 1 and the mirror's 2.957 / 1.332 / 0). GPU double-run
byte-identical.

Root causes, in the order found (each with its own MRE):

1. **The inliner dropped early RETURNs** (`core/ir_inline.py`): the
   "residency-tracker miss" diagnosis in the first version of this
   document was WRONG — the actual first failure was
   `_remap_item` discarding RETURN ops while inlining EMIT, so the
   inclusion branch's `RETURN` vanished and NEMIT double-incremented.
   MRE: `tests/inline_early_return.ergo` (spirv printed 55, correct 30
   — the added values). Fix: the inliner refuses to inline subroutines
   with non-trailing RETURNs; they remain real C calls, which are fully
   supported (call-site residency sync exists for exactly them).
   This also resolved the two stale A2 KNOWN "plan-A FMA" divergences'
   *siblings* — see the erratum note in `tests/golden/KNOWN_DIVERGENCES.md`
   (buc_colony/laplace_annulus now match; their divergence was the
   fragile-FMA SUB bug fc721c2, not plan A — my 8-29 attribution was
   wrong, corrected in the docs).

2. **Call-site GPU sync never re-opened the batched frame**
   (`core/ir_codegen.py`): the first non-inlined EMIT call inside the
   frame loop ended the frame for its downloads and never re-opened it
   — the next `ergo_vk_frame_barrier` recorded into a dead command
   buffer and the NVIDIA driver segfaulted. Fix: re-open after the
   call-sync block (mirrors every mid-body download site).

3. **Kernels dispatched inside IFs were invisible to the mid-body
   download tracker** (`core/ir_codegen.py`): `last_dispatch_arrays`
   accumulated writes only from top-level IRLoop items; an IF-wrapped
   kernel (BOND_AXES under `IF NACT > 0`) left its outputs
   (CXA/ALEN/FBX) stale on the host. Fix: the IRIf branch now scans its
   bodies for kernels and propagates their writes, mirroring the IRLoop
   case (arrays the CPU also wrote inside the same IF stay dirty —
   conservative, order-blind; runtime dirty intervals reset for the
   rest).

4. **Mid-body and call-site downloads clobbered CPU-fresh arrays**
   (`core/ir_codegen.py`): a download fired for arrays that were
   kernel-written earlier in the body but host-written since
   (cpu_dirty) — in the printer that ate the bond/bend force terms
   mid-body (march-phase divergence: rshell tracked while pair/bond
   energies exploded — dynamics healthy, force chain corrupted).
   Fix: both download sites now exclude cpu_dirty arrays (the host
   copy is authoritative; the next dispatch re-uploads), matching the
   host-fallback-kernel download path's existing rule.

### B2 fixed — render-only particle codegen

`--render` without `--target` now compiles POS_X/POS_Y/POS_Z particle
programs (CPU physics + GPU display): `_color_buf` is declared
unconditionally; the meshlet/grid `ERGO_RENDER` alternates are emitted
only when the FDTD grid buffers actually exist; and
`_detect_particle_soa` dedupes `render_arrays` (the color array may BE
POS_X — the duplicate double-declared the buffer). Gate: the MRE
compiles — `tests/render_only_particles.ergo` — and a compile-only
RENDER COMPILE CHECK section in `tests/golden/run_golden.py` guards it
(running opens a window, so the gate compiles, doesn't run).

### Sign-equivalence pre-check (task item 1): spirv path clean

The fragile-FMA SUB fix (fc721c2) was CPU-side; the spirv plan-A OpFma
sign folds were written correctly from the start. Verified with an
explicit orientation probe (both SUB orientations, call-factor fragile
sites + non-fragile explicit-Fma sites, inside an extracted kernel):
CPU==GPU byte-identical at f64 AND f32 (`/tmp` probe; archived as
`min/cell/mre_sub_orientations.ergo`). No spirv.py change needed. The
`--render` path (which also inlines) compiles + runs the early-return
MRE correctly.

### R11 landmine scan (task item 2): CLEAN

Scanned `work/vesicle_printer/*.ergo`, `work/proposedFixes/*.ergo`,
`min/cell/*.ergo` for the R11 pattern (DO loop bound exceeding the
written array's declared size). No constant-bound violations anywhere.
All runtime-bounded loops (`DO I=1,NACT/NINC`) are capacity-guarded at
emission (`IF NAMPH ≥ NMAX THEN RETURN`, `IF NINC ≥ NINCM THEN RETURN`;
NACT ≤ 2·NMAX = 640 = NB exactly, NINC ≤ 64 = NINCM exactly — zero
slack by construction). No fixes needed; `min/cell/` integration copy
is clean.

## The corner-pile fix (2026-09-04, user report)

The first working render showed point tracers piling onto a spot
~214 px off-center (user: "accumulating in the corners of the lattice
square"). Diagnosis by projection arithmetic: the parked un-emitted
monomers at world (999,999,999) were NOT offscreen — perspective
projection has no absolute "offscreen"; far points fall toward the
vanishing point. The park mapped to window pixel (852,392), inside the
frame, stacking 472 particles into one visible pile (measured pre-fix:
densest 20px cells 220 lit pixels each at the pile; the physics cluster
was the faint arcs next to it).

Fix (program-side, `RENDER_COPY` in `min/cell/vesicle_printer_gpu.ergo`
— the compiler is correct here): **compact packing + runtime draw
count.** Live beads pack at POS 1..NACT, live inclusions right after at
NACT+1..NACT+NINC, and NPART changed from a PARAMETER to a runtime
STATIC INTEGER := NACT+NINC that the render call uses as the draw
count. Un-emitted monomers are never drawn — cull, not park.

Evidence (post-fix capture /tmp/cap_fixed1.png): the old pile box holds
ZERO lit pixels; 108 lit pixels total, max 26 per 20px cell, cluster
extent ~140x125 px — the true mid-shrink structure. The render-only
run's stdout is byte-identical to the CPU reference across all 14000
steps (rendering never touches physics bits), and the full
`--target spirv --render` build (GPU compute + display) matches the
headless spirv stdout.

## True-3D rendering (2026-09-04, user report: "2 flat 2D layers")

**Disambiguation:** the printer runs PRINTMODE=4 (stack): the print
phase's true geometry IS two flat rings at z = cz ± 1.25 — "two flat
layers" mid-print is correct physics, not a rendering artifact; the 3D
structure emerges during the shrink (two caps closing, zstd 1.39). But
the render had NO monocular depth cue at a fixed camera, so even the
closed shell read flat. Two render-host additions (zero physics bits;
verified: render-run stdout byte-identical to the CPU reference over
all 14000 steps):

1. **Auto-orbit** (`core/runtime/vk_host.c`): the camera azimuth
   advances 8 deg/s by default — a rotating view resolves depth
   immediately. `ERGO_ORBIT=<deg/s>` overrides, `ERGO_ORBIT=0`
   disables; any mouse drag/scroll suspends the spin for 4 s. This is
   the live render path in vk_host.c (`vk_render.c` is dead reference
   code — found while editing; left untouched).
2. **Depth-attenuated point size** (`core/runtime/render_points.vert`,
   regenerated `render_shaders.h` with glslc): gl_PointSize was a
   constant 1 px; now `base * 1.2 / depth` clamped to [1, 12] px.

Evidence: captures at t1/t2 (/tmp/spin_t1_win.png,
/tmp/spin_t2_win.png) show the printed rings at clearly different
orientations (cluster extent x 603–673 → 281–690); the pre-fix phantom
pile is gone (zero lit pixels at its old position). GPU budget: a few
hundred point sprites + one matrix update per frame — trivially within
RTX 2060 capacity; no fill-rate concern at this scale, the question was
plumbing only.

## Running the visual
## Running the visual

```
python -m core min/cell/vesicle_printer_gpu.ergo --render -o /tmp/vprt_ro
/tmp/vprt_ro            # CPU physics + GPU display (certified numerics)
python -m core min/cell/vesicle_printer_gpu.ergo --target spirv --render \
    -o /tmp/vprt_gpu    # GPU compute + display (galaxy's route)
ERGO_ORBIT=0 /tmp/vprt_ro   # hold the camera still
ERGO_ORBIT=20 /tmp/vprt_ro  # faster spin (deg/s)
```

Window: 1280x720, orbit camera (mouse drag/scroll). Colors: COLR 0 =
head (dark), 1 = tail (bright), 2 = inclusion. The show: two rings
print codon-by-codon (steps 0-3200), march inward (3200-7200), anchors
release (7200-10200), cargo seats (10200-10700), free closed shell to
14000. Headless capture: the render path has none; evidence here was
X11 `scrot` + PIL occupancy analysis.

## Files

- `min/cell/vesicle_printer_gpu.ergo` — the render build (compact
  packing, runtime NPART; CPU-verified: byte-identical to the stack
  variant, deterministic double-run, GPU-tracked through the march).
- `min/cell/mre_render_only_particles.ergo` — B2 MRE (gate copy:
  `tests/render_only_particles.ergo`).
- `min/cell/mre_sub_orientations.ergo` — spirv SUB-orientation probe
  (CPU==GPU at f64+f32, both orientations).
- `tests/inline_early_return.ergo`, `tests/gpu_midbody_dirty.ergo` —
  corpus GPU-PASS regression tests for the B1 chain.
- This document. `work/` sources untouched throughout.
