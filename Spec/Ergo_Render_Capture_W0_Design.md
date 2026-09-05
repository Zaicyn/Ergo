# W0 Phase-1 design — render-buffer capture (PNG dump)

2026-09-05. Phase 1 of work/wave3d_engine/INTEGRATION_PLAN.md §W0:
design + proven encoder prototype only — NO core/ edits (awaits
check-in approval). Encoder prototype: /tmp/png_proto.c (verified
pixel-exact round-trip through PIL AND a stdlib-zlib manual chunk walk,
odd-size 257×131 pattern; `file` identifies it as a valid PNG).

## Current state (evidence from the live path)

- Live render host: `core/runtime/vk_host.c` (vk_render.c is dead
  reference code). Render entry points: `ergo_vk_render_frame` (grid),
  `ergo_vk_render_points`, `ergo_vk_render_gaussians`,
  `ergo_vk_render_grid_gaussians`, `ergo_vk_render_meshlets` — all
  `if (g.headless) return;` up front.
- Windowed frame flow (render_points, vk_host.c:3094–3232): wait
  `g.render_fence` (previous render) → `vkAcquireNextImageKHR`
  (UINT64_MAX) → record render pass into `g.render_cmd_buf` (dedicated
  render command buffer, distinct from the compute frame cmd_bufs and
  the xfer channel) → submit on `g.compute_queue` with
  sem_available/sem_finished → `vkQueuePresentKHR`.
- Swapchain: B8G8R8A8_SRGB, `imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT`
  only (vk_host.c:1919) — readback needs `| TRANSFER_SRC` added there.
  Extent follows the window (ERGO_WIN, default 800×800 square since
  725fc68).
- Headless today: `ergo_vk_init(1)` skips GLFW/swapchain/render-pass
  creation entirely; render functions early-return.
  `ERGO_VK_HEADLESS_ONLY` builds (driver adds it when --render is
  absent) compile all render code OUT — capture can never live there.
- No step concept in the render host. (Generated code can publish
  `ergo_stats_frame` as a weak symbol, but only NET programs do.)

## Design

### Capture trigger and filename

- `ERGO_SHOT_EVERY=N` — capture every Nth render call (frame cadence;
  the render host counts frames, it has no step number). Default 0 = off.
- `ERGO_SHOT_INTERVAL=T` — wall-clock seconds between captures
  (whichever fires; both may be set).
- Filenames: `shot_<frame>.png` (`%06d`), in the CWD. Optional phase-2
  upgrade: `ergo_vk_set_step(int)` called from generated code so names
  carry the sim step — needs a one-line emission in
  core/ir_codegen.py's render block; flagged as a decision point, not
  required for W0's oracles.

### Windowed capture (window stays, dumps alongside)

- Swapchain creation gains `| VK_IMAGE_USAGE_TRANSFER_SRC_BIT`.
- When a capture is due, the copy is recorded INTO `g.render_cmd_buf`
  right after `vkCmdEndRenderPass`: layout transition
  PRESENT_SRC_KHR → TRANSFER_SRC_OPTIMAL → `vkCmdCopyImageToBuffer`
  into a persistently-mapped host staging buffer → transition back to
  PRESENT_SRC_KHR. Present then proceeds normally — the window image is
  unchanged (the copy is a read).
- After the submit, capture frames host-block once on
  `g.render_fence` (already the frame's completion fence), then map →
  BGRA→RGB byte swap (swapchain is B8G8R8A8) → `png_write_rgb8`.
  Non-capture frames pay zero.

### Headless capture (offscreen target; the early-return replacement)

- New env `ERGO_OFFSCREEN=1` (checked inside `ergo_vk_init` — no
  codegen change): a `--render` build then skips GLFW window/surface/
  swapchain creation and instead creates: offscreen color VkImage
  (B8G8R8A8_SRGB, COLOR_ATTACHMENT|TRANSFER_SRC) + view, a depth image
  (same format/usage as the windowed depth), and a framebuffer bound to
  the SAME render pass (created with the fixed format — no surface caps
  needed). `g.offscreen = 1`; `g.headless` stays 0 so the render
  functions do NOT early-return.
- In the render functions, the offscreen branch replaces
  acquire/semaphores/present with: render into the offscreen
  framebuffer, submit with `g.render_fence`, wait it (no display pacing
  headless — host-blocking is free), copy → PNG when due.
  `ergo_vk_should_close` returns 0 when offscreen (no window).
- Extent: `ERGO_WIN` (default 800×800) — same as windowed, so windowed
  and offscreen captures are pixel-comparable.
- `ERGO_VK_HEADLESS_ONLY` builds stay capture-less (render code is
  compiled out there by design).

### Coverage: which builds get capture

- `--render` windowed: capture (windowed path above).
- `--render` + `ERGO_OFFSCREEN=1`: capture (headless; the CI/remote
  route). This covers BOTH the GPU+render build and the render-only
  (CPU physics) build — they share the render host.
- Plain `--target spirv` (headless-only compile): no capture (nothing
  to capture — no render code). Documented limitation.

### PNG encoder (proven)

`/tmp/png_proto.c`, ~100 lines, no deps: zlib stream of STORED deflate
blocks (max 65535 each), filter byte 0 per row, CRC32/Adler32 tables
computed at init. Uncompressed, so PNG bytes are a pure function of the
pixels — byte determinism comes free. (Decision recorded per the plan:
PNG over PPM — proven trivial and self-contained; PPM would be ~30
lines but 3x bigger files and no viewer metadata; PNG costs little.)

### Oracles (per the plan)

1. Pixel-exact double-run: two offscreen runs with the same
   ERGO_SHOT_EVERY → `cmp` the PNGs byte-identical.
2. Window-vs-dump same-frame match: a windowed run with capture at
   frame F vs an X11 `import` of the same frame — pixel-equal after
   cropping to the client area (the presented bytes ARE the swapchain
   bytes; sRGB passes through unchanged).
3. Gate green: change is render-host only, no physics bits — render
   builds compile, corpus/golden/stream/nodegraph unchanged.

### Risk list (frame choreography — the stall-fix lesson)

- The capture copy rides `g.render_cmd_buf`/`g.render_fence` —
  render-owned resources, submitted in the SAME submission as the render
  pass. It never touches the compute frame cmd_bufs/fences or the xfer
  channel (the 2026-09-05 end-of-run stall was exactly an out-of-channel
  cmd_buf reset; this design has no such cross-channel use).
- Layout transitions: the swapchain image must be back in
  PRESENT_SRC_KHR before `vkQueuePresentKHR` — the transition pair is
  recorded inline, so a capture can't strand the layout.
- The host wait on `g.render_fence` happens on capture frames only,
  before present — same fence the next frame would wait on anyway; no
  new synchronization object enters the choreography.
- Capture does not touch `pts_ds`/descriptor bindings, the f32 shadow
  conversion, or `render_offset` (ping-pong) — the copy reads the
  PRESENTED image, so whatever the pipelines drew is what lands in the
  PNG (f32 shadows, orbit camera, point sizes all included by
  construction).
- Depth buffer is not captured (color only).
- Offscreen mode skips `glfwPollEvents` pressure entirely (no window);
  `ergo_vk_should_close` returns 0.
- ERGO_ORBIT interaction: the camera advances per render call as today;
  capture frames sample whatever the camera is at that frame. For
  reproducible captures pair with `ERGO_ORBIT=0`/`ERGO_CAM=...`.
- ERGO_WIN: sets both the window and the offscreen extent — one knob,
  comparable captures.
- PNG writes are small (800×800×3 stored ≈ 1.9 MB) and happen on the
  host after the fence wait — no GPU-side cost beyond the copy.

## Files that WOULD change in phase 2 (awaiting approval)

1. `core/runtime/vk_host.c`: encoder; `g.offscreen` mode in
   `ergo_vk_init` + offscreen target creation; `TRANSFER_SRC` swapchain
   usage; capture staging buffer; the due-check + copy + write in the
   five render entry points (shared helper); `should_close` offscreen.
2. `core/runtime/ergo_vk.h`: no change needed (all internal state).
3. `tests/` (not core/): a capture regression — small render program,
   offscreen double-run, PNG byte-compare + nonblack check; wired like
   the existing RENDER COMPILE CHECK in tests/golden/run_golden.py.
4. Usage note: appended to the design doc / render docs when landed.

## Landed usage note (phase 2, 2026-09-05)

Landed exactly as designed (vk_host.c only; no ir_codegen change, no
video, no compressed PNG, no depth capture):

```
ERGO_SHOT_EVERY=1000  ./my_render_build     # shot every 1000 frames
ERGO_SHOT_INTERVAL=30 ./my_render_build     # or every 30 s wall clock
ERGO_OFFSCREEN=1 ERGO_SHOT_EVERY=10 ./my_render_build   # headless
```

- Filenames `shot_<frame>.png` (`%06d` render-call count), written to
  the CWD; each shot logged on stderr. 800×800 (or ERGO_WIN=WxH),
  8-bit RGB, uncompressed zlib (deterministic bytes).
- Offscreen mode skips the window entirely (no display needed); the
  camera envs (ERGO_CAM, ERGO_ORBIT) apply identically — for
  reproducible captures use ERGO_ORBIT=0 / ERGO_CAM=az,el,dist.
- Windowed runs dump alongside the live window; the dump is
  pixel-identical to the X11 window content of the same frame
  (verified: `import -window` vs shot PNG, sumdiff 0).
- `ERGO_VK_HEADLESS_ONLY` builds (no --render) have no capture.

Verified: gate green (golden 16/16, corpus 200/200, stream 8/8,
nodegraph 11/11, render compile check PASS) + new CAPTURE REGRESSION
in tests/golden/run_golden.py (offscreen double-run byte-identical +
nonblack, 30 shots).  End-to-end: GPU printer run with
ERGO_OFFSCREEN=1 ERGO_SHOT_EVERY=1000 produced shot_001000..014000
(mid-print ring arcs → closed shell), rc=0.

## Explicitly not in W0 (unchanged at landing)

- No `core/ir_codegen.py` change (step-stamped filenames deferred;
  frame-numbered names suffice for the oracles).
- No video/streaming, no compressed PNG, no depth capture.
