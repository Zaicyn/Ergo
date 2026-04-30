# Render Pipeline Overhaul — Handoff Document

## What We're Doing

Replacing the per-frame-recorded render pipeline with persistent
command buffers. The render is a pure forward pass (additive particle
splatting). Command buffers don't snapshot data — the SSBOs update
from compute and the pre-recorded draw naturally reads the latest.

### Current Architecture (broken by 6ms fence stall)
```
Every frame:
  vkWaitForFences(render_fence)       ← 6ms stall HERE
  vkResetCommandBuffer(render_cmd_buf)
  vkBeginCommandBuffer(...)
    barrier, beginRenderPass, bindPipeline, bindDescriptors
    pushConstants(viewProj, cam, cull, val_min/max)
    vkCmdDraw(n_points)
  vkEndCommandBuffer(...)
  vkQueueSubmit(render_fence)
  vkQueuePresentKHR(...)
```

### Target Architecture (zero fence stall in steady state)
```
At init (once):
  For each swapchain image i:
    Record cmd_buf[i]: barrier → renderPass[i] → bind → drawIndirect
  
Every frame:
  fi = current_frame % sc_count
  vkWaitForFences(render_fence[fi])     ← already signaled (N frames old)
  memcpy(render_ubo[fi], params, 96)    ← camera, cull, colors
  memcpy(indirect_buf, {NPART,1,0,0})   ← draw count
  vkAcquireNextImageKHR → img_idx
  vkQueueSubmit(cmd_buf[img_idx], fence[fi])
  vkQueuePresentKHR(...)
```

## What's Done

### 1. Shaders Updated (push_constant → UBO)
- `mcl/runtime/render_points.vert` — uses `layout(set=0, binding=5) uniform RenderParams`
- `mcl/runtime/render_gauss.vert` — same UBO layout
- Fragment shaders unchanged
- **SPIRV compiled and embedded in render_shaders.h** (build_shaders.sh already run)
- Shaders are ready to go

### 2. vk_render.c Written (new render logic)
- `mcl/runtime/vk_render.c` — standalone file with:
  - `RenderParams` struct (96 bytes, matches shader UBO)
  - `camera_key_cb()` — C key toggles culling
  - `create_host_buffer()` — helper for UBO + indirect buf
  - `render_persistent_init()` — allocates per-image resources
  - `render_record_persistent()` — pre-records cmd bufs (called once)
  - `ergo_vk_render_points()` — trivial per-frame submit
  - `ergo_vk_render_gaussians()` — routes to render_points
  - `render_persistent_cleanup()` — destroys per-image resources

### 3. vk_host.c Reverted to Clean State
- `git checkout mcl/runtime/vk_host.c` — back to last commit
- No partial edits remain

### 4. Compiler Changes (from earlier in session)
- `mcl/backends/spirv.py` line 1351-1357 — scatter index fix (committed)
- `mcl/ir_codegen.py` — VMAX default changed to 3.0 (may not be committed)
- `mcl/ir_codegen.py` — `ERGO_RENDER=gauss` env var switch for render mode

## What Needs to Be Done

### Step 1: Update vk_host.c Struct (lines 149-175)

Replace:
```c
VkCommandBuffer  render_cmd_buf;
VkSemaphore      sem_available;
VkSemaphore      sem_finished;
VkFence          render_fence;
```

With:
```c
VkCommandBuffer  render_cmd_buf[ERGO_VK_MAX_SWAPCHAIN];
VkSemaphore      sem_available[ERGO_VK_MAX_SWAPCHAIN];
VkSemaphore      sem_finished[ERGO_VK_MAX_SWAPCHAIN];
VkFence          render_fence[ERGO_VK_MAX_SWAPCHAIN];
uint32_t         current_frame;

VkBuffer         render_ubo[ERGO_VK_MAX_SWAPCHAIN];
VkDeviceMemory   render_ubo_mem[ERGO_VK_MAX_SWAPCHAIN];
void            *render_ubo_mapped[ERGO_VK_MAX_SWAPCHAIN];

VkBuffer         indirect_buf;
VkDeviceMemory   indirect_mem;
void            *indirect_mapped;

int              render_recorded;
int              render_mode;  /* 0=points, 1=gaussians */
```

### Step 2: Update Points Pipeline Descriptor Layout (line ~1898)

Current: 4 SSBOs (binding 0-3), push constants (96 bytes)

New: 5 bindings — 4 SSBOs (binding 0-3) + 1 UBO (binding 5), no push constants

```c
VkDescriptorSetLayoutBinding bindings[5];
// bindings[0-3]: STORAGE_BUFFER, vertex stage (unchanged)
// bindings[4]: binding=5, UNIFORM_BUFFER, vertex stage (NEW)

// Pipeline layout: NO push constants
pl_ci.pushConstantRangeCount = 0;
```

Descriptor pool needs both STORAGE_BUFFER (4) and UNIFORM_BUFFER (1).

### Step 3: Update Gaussian Pipeline Descriptor Layout (similar)

Current: 5 bindings (4 SSBOs + 1 combined image sampler at binding 4), push constants

New: 6 bindings (4 SSBOs + sampler at binding 4 + UBO at binding 5), no push constants

### Step 4: Update Init (line ~651)

Replace single cmd buf + fence + semaphore allocation with call to
`render_persistent_init()` from vk_render.c. Need to `#include "vk_render.c"`
at the right point in vk_host.c (after struct + helpers, before render functions).

Also register key callback:
```c
glfwSetKeyCallback(g.window, camera_key_cb);
```

Add forward declaration:
```c
static void camera_key_cb(GLFWwindow *w, int key, int scancode, int action, int mods);
```

### Step 5: Remove Old Render Functions

Delete or replace:
- `ergo_vk_render_points()` (line ~2315-2448) — replaced by vk_render.c version
- `ergo_vk_render_gaussians()` (line ~2452-2537) — replaced by vk_render.c version

Keep `ergo_vk_render_frame()` (grid render, line ~2170-2310) for now — it uses
its own pipeline and isn't the bottleneck.

### Step 6: Update Cleanup (line ~700)

Replace:
```c
vkDestroySemaphore(g.device, g.sem_available, NULL);
vkDestroySemaphore(g.device, g.sem_finished, NULL);
vkDestroyFence(g.device, g.render_fence, NULL);
```

With call to `render_persistent_cleanup()` from vk_render.c.

### Step 7: Fix UBO Per-Frame Issue

**KNOWN ISSUE:** The pre-record function binds ONE descriptor set to
ALL command buffers. But the UBO needs to be per-frame (each frame
writes different camera params to its own UBO).

**Solution options:**
1. **Per-frame descriptor sets** — allocate sc_count descriptor sets,
   each bound to its own UBO. Pre-record cmd_buf[i] binds ds[i].
   Most correct but requires sc_count descriptor sets.

2. **Dynamic UBO** — use VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC
   with dynamic offset. Single descriptor set, per-frame offset.
   The pre-record uses offset=0, the submit overrides with
   vkCmdBindDescriptorSets dynamic offset. But this requires the
   cmd buf to be re-recorded (defeats the purpose).

3. **Single UBO, update before submit** — use one UBO, update it
   between fence-wait and submit. The fence guarantees the GPU is
   done reading the old data. Simple but requires all frames to
   read from the same UBO (no true in-flight overlap for UBO reads).

**Recommendation:** Option 3 is simplest and works because:
- The fence wait guarantees previous frame finished reading the UBO
- Camera params are tiny (96 bytes) — no bandwidth concern
- We still get frames-in-flight benefit for the cmd buf + swapchain
  image (the main sources of stall)

With option 3, simplify to single UBO:
```c
VkBuffer         render_ubo;
VkDeviceMemory   render_ubo_mem;
void            *render_ubo_mapped;
// No per-frame array needed
```

### Step 8: Update Headless Stubs (line ~2543)

The headless stubs for render_points and render_gaussians stay as
empty functions (they already exist at bottom of file).

### Step 9: Update codegen (ir_codegen.py)

The codegen emits `ergo_vk_render_points()` or `ergo_vk_render_gaussians()`
with the same function signature. The API doesn't change — the render
functions still accept the same arguments. But push constants are no
longer used, so the `point_size` argument becomes unused (splat size
is hardcoded in the shader or derived from UBO params).

The `ERGO_RENDER=gauss` env var switch in codegen (line ~950) can be
simplified since both modes now route through the same render function.

### Step 10: Rebuild and Test

```bash
cd mcl/runtime && bash build_shaders.sh && cd ../..
bash structured/build.sh  
python -m mcl --target spirv --precision f32 --no-split --render -o galaxy_render galaxy_structured.ergo

# Basic test
./galaxy_render -N 100000 --frames 100

# Scale test
ERGO_NOVSYNC=1 ./galaxy_render -N 5000000

# Gaussian test
ERGO_RENDER=gauss ./galaxy_render -N 1000000

# Culling test (press C)
# Camera test (mouse drag + scroll)
# Clean shutdown test (close window)
```

## Key Files

| File | Status | Notes |
|---|---|---|
| mcl/runtime/render_points.vert | DONE | UBO at binding 5 |
| mcl/runtime/render_gauss.vert | DONE | UBO at binding 5 |
| mcl/runtime/render_points.frag | unchanged | |
| mcl/runtime/render_gauss.frag | unchanged | |
| mcl/runtime/render_shaders.h | DONE | rebuilt with new shaders |
| mcl/runtime/build_shaders.sh | DONE | includes gauss shaders |
| mcl/runtime/vk_render.c | WRITTEN | new render logic, needs integration |
| mcl/runtime/vk_host.c | CLEAN | needs struct + init + pipeline + cleanup edits |
| mcl/runtime/ergo_vk.h | unchanged | API stays same |
| mcl/ir_codegen.py | needs VMAX=3.0 | minor |

## Architectural Notes

- The grid render (ergo_vk_render_frame) is separate and uses its own
  pipeline with push constants. Leave it alone for now — it's only used
  for heightfield visualization, not particle rendering.

- The `pts_ds_bound` global flag (line 238) was used to avoid rebinding
  descriptor sets after sort pointer swaps. With persistent cmd bufs,
  descriptor sets are bound at pre-record time. If sort swaps buffer
  pointers, the descriptor set bindings become stale. Need to either:
  re-record on sort swap (rare, every 5000 frames) or ensure sort
  doesn't change the VkBuffer handles (it doesn't — sort reorders
  contents within the same buffers).

- The `render_offset` for ping-pong buffers needs attention. The
  pre-recorded cmd buf binds descriptors with a fixed offset. If
  ping-pong flips the read offset, descriptors become stale.
  Solution: `ergo_vk_set_render_offset()` should trigger a re-record.
  This is called at most once per frame (before render) so re-recording
  on offset change is acceptable.

## The Bigger Picture

This render pipeline fix is Step 1 of the trajectory:

1. **Persistent render architecture** (this work) — zero CPU stall
2. **Stable gaussian splat renderer** — validate splat shading
3. **Grid-derived gaussian extraction** — covariance tensors from grid moments
4. **Hierarchical representation** — merge coherent regions
5. **Meshlet conversion / shell traversal** — the final renderer

The 32^3 grid already computes density, momentum, and metabolic gate
per cell. Those ARE gaussian parameters. Step 3 just reads them out
as splat descriptors instead of drawing individual particles. The
render goes from O(particles) to O(cells).
