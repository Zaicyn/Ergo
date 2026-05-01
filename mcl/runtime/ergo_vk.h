/*
 * ergo_vk.h — Vulkan compute runtime for Ergo
 *
 * Flat C99 API wrapping all Vulkan boilerplate. Generated Ergo host
 * code calls these functions; it never touches Vulkan directly.
 *
 * Lifecycle:
 *   ergo_vk_init        -> create instance, device, queues
 *   ergo_vk_create_buffer -> allocate device storage buffers
 *   ergo_vk_load_shader -> create compute pipeline from SPIR-V
 *   ergo_vk_upload / ergo_vk_download -> host <-> device transfers
 *   ergo_vk_bind_buffer -> bind a buffer to a pipeline descriptor
 *   ergo_vk_push_constants -> set push constant data
 *   ergo_vk_dispatch    -> dispatch compute and wait
 *   ergo_vk_shutdown    -> teardown everything
 *
 * Render pass functions (Phase D, stubbed for now):
 *   ergo_vk_render_frame, ergo_vk_should_close
 */

#ifndef ERGO_VK_H
#define ERGO_VK_H

#include <stddef.h>
#include <stdint.h>

/* Opaque handles — generated code stores these but never inspects them. */
typedef uint32_t ErgoVkBuf;
typedef uint32_t ErgoVkPipe;

/* ── Lifecycle ───────────────────────────────────────────── */

/*
 * Initialize Vulkan. Creates instance, selects a physical device with
 * compute queues and shaderFloat64 support, creates logical device.
 *
 * headless: 1 = compute only (no window).
 *           0 = compute + window (GLFW, Phase D).
 *
 * Returns 0 on success, non-zero on failure.
 */
int ergo_vk_init(int headless);

#ifdef ERGO_VK_ANDROID
/*
 * Android init: takes a native window for rendering.
 * Pass NULL for headless compute.
 */
int ergo_vk_init_android(void *native_window);
#endif

/*
 * Shut down Vulkan. Frees all buffers, pipelines, and device resources.
 */
void ergo_vk_shutdown(void);

/*
 * Query DEVICE_LOCAL heap size in bytes.
 * Returns total VRAM available to the device (not free — Vulkan 1.0
 * doesn't expose usage). Caller should apply a safety factor.
 */
size_t ergo_vk_device_local_bytes(void);

/* ── Buffer management ───────────────────────────────────── */

/*
 * Allocate a device-local storage buffer of `size` bytes.
 * Returns a buffer handle.
 */
ErgoVkBuf ergo_vk_create_buffer(size_t size);

/*
 * Upload `size` bytes from host `data` into device buffer `buf`.
 */
void ergo_vk_upload(ErgoVkBuf buf, const void *data, size_t size);

/*
 * Download `size` bytes from device buffer `buf` into host `data`.
 */
void ergo_vk_download(ErgoVkBuf buf, void *data, size_t size);

/*
 * Download `size` bytes from device buffer `buf` at byte `offset` into host `data`.
 * Used for ping-pong buffers where current state isn't at offset 0.
 */
void ergo_vk_download_at(ErgoVkBuf buf, void *data, size_t offset, size_t size);

/*
 * Upload `size` bytes from host `data` into device buffer `buf` at byte `offset`.
 */
void ergo_vk_upload_at(ErgoVkBuf buf, const void *data, size_t offset, size_t size);

/* ── Compute pipeline ────────────────────────────────────── */

/*
 * Create a compute pipeline from SPIR-V binary.
 *
 * spirv:      pointer to SPIR-V binary data.
 * spirv_size: size in bytes.
 * n_buffers:  number of storage buffer bindings (descriptor set 0).
 * pc_size:    push constant block size in bytes (0 if none).
 *
 * Returns a pipeline handle.
 */
ErgoVkPipe ergo_vk_load_shader(const void *spirv, size_t spirv_size,
                                int n_buffers, size_t pc_size);

/*
 * Bind a storage buffer to a pipeline's descriptor set.
 *
 * pipe:    pipeline handle.
 * binding: binding index (0, 1, 2, ...).
 * buf:     buffer handle.
 */
void ergo_vk_bind_buffer(ErgoVkPipe pipe, int binding, ErgoVkBuf buf);

/*
 * Set push constant data for a pipeline.
 *
 * pipe: pipeline handle.
 * data: pointer to push constant struct.
 * size: size in bytes.
 */
void ergo_vk_push_constants(ErgoVkPipe pipe, const void *data, size_t size);

/*
 * Dispatch compute work and wait for completion.
 *
 * pipe:     pipeline handle (must have buffers bound).
 * n_groups: number of workgroups in X dimension.
 */
void ergo_vk_dispatch(ErgoVkPipe pipe, int n_groups);

/*
 * Create a double-buffered storage buffer pair.
 * Returns handle to buffer A. Buffer B is created internally.
 * Use ergo_vk_read_buf/ergo_vk_write_buf to get current read/write buffer.
 */
ErgoVkBuf ergo_vk_create_buffer_pair(size_t size);

/*
 * Get the current read buffer (based on frame parity).
 * For single buffers, returns the buffer itself.
 */
ErgoVkBuf ergo_vk_read_buf(ErgoVkBuf buf);

/*
 * Get the current write buffer (based on frame parity).
 * For single buffers, returns the buffer itself.
 */
ErgoVkBuf ergo_vk_write_buf(ErgoVkBuf buf);

/* ── Batched frame dispatch ──────────────────────────────── */

/* Begin recording a new frame. Waits for previous frame's fence. */
void ergo_vk_frame_begin(void);

/* Record a buffer fill (zero) into the current command buffer. */
void ergo_vk_frame_fill(ErgoVkBuf buf, size_t size);

/* Insert a compute→compute memory barrier. */
void ergo_vk_frame_barrier(void);

/* Record a compute dispatch (no submit). */
void ergo_vk_frame_dispatch(ErgoVkPipe pipe, int n_groups);

/* End recording and submit. Does NOT wait — next frame_begin waits. */
void ergo_vk_frame_end(void);

/* Wait for the current frame's fence (GPU idle). Call after frame_end
 * and before any host↔device transfers so the queue is quiescent.
 * Safe to call multiple times — returns immediately if already waited. */
void ergo_vk_frame_wait(void);

/* Submit current command buffer, wait for ALL GPU work to finish, then
 * re-open a fresh command buffer. Used before pointer swaps that change
 * which VkBuffer is bound to a descriptor set. */
void ergo_vk_frame_drain(void);

/* Print GPU timestamp profile report (if ERGO_PROFILE env var is set). */
void ergo_vk_profile_report(void);

/* Set byte offset for ping-pong render (call before render_points). */
void ergo_vk_set_render_offset(size_t byte_offset);

/* Invalidate persistent render cmd bufs (call after sort pointer swaps). */
void ergo_vk_render_invalidate(void);

/* ── Render (Phase E — 3D) ───────────────────────────────── */

/*
 * Render a 3D frame: heightfield surface from simulation buffer.
 *
 * buf:          storage buffer of f64 values to visualize.
 * width, height: simulation grid dimensions.
 * val_min, val_max: value range for color mapping.
 * height_scale: vertical exaggeration of the heightfield (0.0 = flat).
 *
 * Camera is controlled interactively via mouse drag (orbit) and scroll
 * (zoom). No external camera API needed.
 */
void ergo_vk_render_frame(ErgoVkBuf buf, int width, int height,
                           float val_min, float val_max,
                           float height_scale);

/*
 * Render a 3D point cloud from particle SoA buffers.
 *
 * buf_x, buf_y, buf_z: position buffers (f64 arrays, SoA layout).
 * buf_color: color value buffer (f64 array, e.g. OMEGA_NAT).
 * n_points: number of particles to draw.
 * point_size: gl_PointSize in pixels.
 * val_min, val_max: value range for heat palette mapping.
 * world_scale: 1/world_radius, maps world coords to ~[-1,1] for the camera.
 */
void ergo_vk_render_points(ErgoVkBuf buf_x, ErgoVkBuf buf_y, ErgoVkBuf buf_z,
                            ErgoVkBuf buf_color, int n_points,
                            float point_size, float val_min, float val_max,
                            float world_scale);

/*
 * Render particles as gaussian splats (instanced quads with LUT falloff).
 * Same interface as render_points. Uses additive blending.
 * Activate with ERGO_RENDER=gauss environment variable.
 */
void ergo_vk_render_gaussians(ErgoVkBuf buf_x, ErgoVkBuf buf_y, ErgoVkBuf buf_z,
                               ErgoVkBuf buf_color, int n_points,
                               float point_size, float val_min, float val_max,
                               float world_scale);

/*
 * Render grid cells as gaussian splats (O(cells) instead of O(particles)).
 * Reads grid density, gradients, and metabolic gate directly.
 *
 * buf_grad_x:   GRID_GRAD_X buffer (float, flattened 3D)
 * buf_grad_y:   GRID_GRAD_Y buffer (float)
 * buf_grad_z:   GRID_GRAD_Z buffer (float)
 * buf_met_gate: GRID_MET_GATE buffer (float)
 * grid_size:    Grid dimension (32)
 * val_min, val_max: value range for color mapping
 * world_scale:  1/world_radius
 */
void ergo_vk_render_grid_gaussians(ErgoVkBuf buf_grad_x, ErgoVkBuf buf_grad_y,
                                    ErgoVkBuf buf_grad_z, ErgoVkBuf buf_met_gate,
                                    int grid_size, float val_min, float val_max,
                                    float world_scale);

/*
 * Poll window events. Returns 1 if the window should close.
 */
int ergo_vk_should_close(void);

#endif /* ERGO_VK_H */
