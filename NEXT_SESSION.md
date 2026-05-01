# Next Session: Grid Render Projection + Visual Tuning

## What's Done

### Crystal Lane Signatures (Step 3) — COMPLETE
- `PFLAG_SIGNED = 64` in constants.ergo
- 8 SIG_* arrays + SIG_COUNT atomic counter in fluid_state.ergo
- Crystal lane code in physics kernel: ~15 ops hidden behind ~300 ops
- **k2 delta: +3.2% (confirmed free)**
- Deterministic: PFLAG_SIGNED prevents double-collection

### Ballot/Arithmetic SPIRV Ops (Step 2) — COMPLETE
- `WARP_BALLOT`, `WARP_BALLOT_COUNT`, `WARP_BALLOT_PREFIX`, `WARP_BROADCAST_FIRST`
- `GroupNonUniformBallot` + `GroupNonUniformArithmetic` capabilities
- Plumbing for Level 2 warp compaction (not yet used by crystal lane)

### Grid Cell Render (Step 4) — PARTIALLY WORKING
- 32K cell centers precomputed, uploaded once, rendered via particle points pipeline
- `ERGO_RENDER=grid` env var activates it
- Grid lattice visible, positions correct
- **Color is wrong** — all blue, met_gate range doesn't map well to heat palette
- **No projection** — raw grid lattice, not a lightfield cubemap

### Persistent Render (Step 1) — REVERTED
- Pre-recorded cmd bufs with per-swapchain fences crashed GPU
- Root cause: `render_fence[fi]` vs `render_cmd_buf[img_idx]` mismatch
- Also: shader UBO vs push constant mismatch caused black screen
- Restored original single-fence render. Can revisit with proper
  per-image fence tracking (acquire first, then wait on that image's fence).

## What Needs to Be Done

### 1. Fix Grid Render Color
The met_gate range (0.2–1.5) is being mapped against particle OMEGA range
(0–3) which squashes everything to blue. Fix: pass met_gate-specific
val_min/val_max (0.2, 1.5) through the push constants. The call in
vk_host.c already hardcodes these but the particle vertex shader
normalizes against push constant val_min/val_max which come from the
particle color scan.

### 2. Grid Render as Lightfield Projection
Current: 32K points at grid cell centers = raw lattice.
Target: project grid data as a lightfield.

The grid IS the lightfield. Each cell has density, gradients, met_gate.
The render should show this as a continuous field, not discrete points.
Options:
- **Splat-per-cell**: each cell = one screen-aligned quad with gaussian
  falloff, sized to fill one cell width. Needs a working custom pipeline
  (the grid_gauss_pipeline was black — debug why).
- **Cubemap texture**: render grid slices to 6 cube faces, display as
  environment. More complex but proper projection.
- **Volume ray march**: compute shader traces rays through the grid.
  Most correct but most work.

The splat-per-cell approach is closest to what's implemented. The pipeline
was black because of shader/pipeline layout mismatch. The grid_gauss_pipeline
had a sampler+UBO in its descriptor layout but the fragment shader (pts_frag)
doesn't use them. Fix: strip the descriptor layout to 4 SSBOs only AND
verify the SPIRV shader actually produces visible output (the debug test
with hardcoded screen-space quad + forced red was still black — investigate).

### 3. Custom Grid Pipeline Debug
The grid_gauss_pipeline with its own vertex shader produces no visible
output even with a hardcoded screen-space quad. The pipeline creates
successfully, the draw call executes, present succeeds, but nothing
appears. Possible causes:
- Shader module SPIRV has incompatible interface (check spirv-dis output)
- Pipeline layout mismatch despite matching descriptor layout
- Missing Vulkan feature or capability for the shader
- Test: create a truly minimal pipeline (no SSBOs, hardcoded triangle)
  to isolate whether it's a pipeline creation issue or shader issue

### 4. Persistent Render (Future)
When revisiting, the fix is:
```
// Acquire FIRST, then wait on that image's fence
vkAcquireNextImageKHR → img_idx
vkWaitForFences(render_fence[img_idx])  // not render_fence[fi]
// Submit cmd_buf[img_idx] with fence[img_idx]
```
And ensure shader interface (push constant vs UBO) matches pipeline layout.
Integer SSBOs in vertex shaders crash NVIDIA without
vertexPipelineStoresAndAtomics — use float buffers only.

## Current File State

| File | Status |
|---|---|
| structured/constants.ergo | PFLAG_SIGNED = 64 added |
| structured/fluid_state.ergo | SIG_* arrays declared |
| structured/fluid_subs.ergo | Crystal lane in physics kernel |
| mcl/ir.py | 4 ballot IR ops |
| mcl/backends/spirv.py | Ballot/arithmetic SPIRV emission |
| mcl/ir_codegen.py | ERGO_RENDER=grid codegen, render_invalidate |
| mcl/runtime/vk_host.c | Original render + grid cell render via pts pipeline |
| mcl/runtime/render_grid_gauss.vert | Grid vertex shader (not used — pipeline broken) |
| mcl/runtime/render_shaders.h | Includes grid gauss SPIRV |
| mcl/runtime/render_points.vert | Original push constant version (restored) |
| mcl/runtime/render_gauss.vert | Original push constant version (restored) |
| mcl/runtime/ergo_vk.h | render_grid_gaussians + render_invalidate API |

## Build & Test

```bash
# Assemble + compile
bash structured/build.sh
python -m mcl --target spirv --precision f32 --no-split --render \
  -N 1000000 -M 1000000 -o galaxy_render galaxy_structured.ergo

# Particle points (working)
./galaxy_render --frames 200

# Grid cells (working but all-blue)
ERGO_RENDER=grid ./galaxy_render --frames 500

# Profile crystal lane overhead
ERGO_PROFILE=1 ./galaxy_render --frames 200
# k2 should be ~1.67ms (baseline 1.61ms, +3.2%)
```
