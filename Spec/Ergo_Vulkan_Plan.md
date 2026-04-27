# Ergo Vulkan Plan — Rough Draft

*2026-04-23*

## Goal

Run Ergo simulations on GPU via Vulkan compute, with optional window
rendering. Same source file, two modes:

```
mcl sim.mcl --target spirv                  # headless compute
mcl sim.mcl --target spirv --render         # compute + live window
```

---

## Architecture

```
Ergo IR (existing, vendor-neutral)
  |
  +---> mcl/backends/spirv.py        SPIR-V compute shader emission
  |
  +---> mcl/runtime/vk_host.c        Vulkan host runtime (C99, linked in)
  |       |
  |       +---> Headless mode         compute dispatch, readback, done
  |       |
  |       +---> Render mode           compute dispatch + render pass + present
  |
  +---> mcl/runtime/render.frag      Fullscreen quad fragment shader
  +---> mcl/runtime/render.vert      Passthrough vertex shader (6 verts)
```

### What each piece does

**spirv.py** — new backend, same interface as nvvm.py. Consumes
KernelPlan + IRModule, emits SPIR-V assembly text. We use the
SPIR-V text format and assemble with `spirv-as` (from the Vulkan SDK),
or emit binary directly via a small Python SPIR-V builder. The kernel
structure is the same as NVVM — one workgroup invocation per array
element, global_id replaces threadIdx.

**vk_host.c** — a single C99 file that the Ergo driver links into the
final executable. It provides:
- `ergo_vk_init(headless)` — instance, device, queues. If not headless,
  also creates a GLFW window + surface + swapchain.
- `ergo_vk_create_buffer(size)` — allocate device storage buffer.
- `ergo_vk_upload(buf, data, size)` — host → device.
- `ergo_vk_download(buf, data, size)` — device → host.
- `ergo_vk_load_shader(spirv, size)` — create compute pipeline from SPIR-V.
- `ergo_vk_dispatch(pipeline, bufs, n_groups)` — bind + dispatch + wait.
- `ergo_vk_render_frame(bufs, width, height)` — run render pass, present.
- `ergo_vk_should_close()` — poll window events, return 1 if closed.
- `ergo_vk_shutdown()` — teardown.

This is ~800 lines of C. It wraps all the Vulkan boilerplate behind a
flat C API that the generated host code calls. The generated code never
touches Vulkan directly — it calls these functions.

**render.vert / render.frag** — baked-in shaders for visualization.
The vertex shader emits a fullscreen triangle. The fragment shader
reads from a storage buffer (the simulation state) and maps values
to colors. For the colony sim: buffer index = pixel position, value
= membrane potential, color = ANSI-equivalent palette. These get
compiled to SPIR-V at build time and embedded as byte arrays in
vk_host.c.

---

## SPIR-V Backend (spirv.py)

Same pattern as nvvm.py but targeting SPIR-V instead of NVVM IR.

Key differences from NVVM:

| Concept | NVVM | SPIR-V |
|---------|------|--------|
| Thread ID | `@llvm.nvvm.read.ptx.sreg.tid.x` | `gl_GlobalInvocationID.x` (builtin) |
| Array access | raw pointer + GEP | storage buffer + OpAccessChain |
| Scalar params | function args | push constants or uniform buffer |
| Math | `@llvm.nvvm.sin.d` | `OpExtInst GLSL.std.450 Sin` |
| Types | LLVM types (double, i32) | OpTypeFloat 64, OpTypeInt 32 |
| Entry point | `!nvvm.annotations` kernel | OpEntryPoint GLCompute |
| Work groups | grid/block via launch API | `local_size` decoration + vkCmdDispatch |

The IR-to-SPIR-V mapping is mechanical — same operations, different
encoding. The extraction pass and KernelPlan are shared.

### Emission approach

Option A: emit SPIR-V text assembly, assemble with `spirv-as`.
  - Pro: human-readable, debuggable.
  - Con: requires Vulkan SDK tool at build time.

Option B: emit SPIR-V binary directly from Python.
  - Pro: no external tool dependency.
  - Con: more code, harder to debug.

**Start with Option A.** Switch to B later if needed. The text format
is well-documented and maps 1:1 to binary.

Example — the particle update kernel in SPIR-V text:

```
; SPIR-V
; Version: 1.0
; Generator: Ergo
               OpCapability Shader
               OpCapability Float64
               OpMemoryModel Logical GLSL450
               OpEntryPoint GLCompute %main "main" %gl_GlobalInvocationID
               OpExecutionMode %main LocalSize 256 1 1

               ; Storage buffer bindings
               OpDecorate %px_var DescriptorSet 0
               OpDecorate %px_var Binding 0
               OpDecorate %vx_var DescriptorSet 0
               OpDecorate %vx_var Binding 1

               ; Types
       %void = OpTypeVoid
       %func = OpTypeFunction %void
        %f64 = OpTypeFloat 64
        %u32 = OpTypeInt 32 0
     %v3uint = OpTypeVector %u32 3

               ; Push constant for DT and N
    %pc_type = OpTypeStruct %f64 %u32
    ; ...

       %main = OpFunction %void None %func
      %entry = OpLabel
        %gid = OpLoad %v3uint %gl_GlobalInvocationID
       %tidx = OpCompositeExtract %u32 %gid 0

               ; bounds check: tidx < N
               ; load px[tidx], load vx[tidx]
               ; px[tidx] = px[tidx] + vx[tidx] * DT
               ; store

               OpReturn
               OpFunctionEnd
```

---

## Host Code Generation

The generated host C99 calls the vk_host API. For the colony sim
with 3 extracted kernels, the generated main() looks roughly like:

```c
#include "ergo_vk.h"

int main(void) {
    // CPU-side declarations (scalars, parameters)
    static const int N = 2048;
    static const double DT = 0.001;
    // ...

    // Init Vulkan (headless or windowed)
    ergo_vk_init(/*headless=*/0);

    // Allocate device buffers for arrays used by kernels
    VkBuf d_px = ergo_vk_create_buffer(N * sizeof(double));
    VkBuf d_vx = ergo_vk_create_buffer(N * sizeof(double));
    // ...

    // Load compute shaders (compiled SPIR-V, embedded or from file)
    VkPipe kern_0 = ergo_vk_load_shader(kernel_0_spv, sizeof(kernel_0_spv));
    VkPipe kern_1 = ergo_vk_load_shader(kernel_1_spv, sizeof(kernel_1_spv));

    // === CPU init code (non-extractable) ===
    // ... seeding, setup ...

    // Upload initial state
    ergo_vk_upload(d_px, px, N * sizeof(double));

    // === Main loop ===
    for (int FRAME = 1; FRAME <= 2000; FRAME++) {
        // GPU: physics kernel
        ergo_vk_dispatch(kern_1, bufs, (N + 255) / 256);

        // CPU: structural suffix (PRNG, division, diffusion boundary)
        ergo_vk_download(d_CATP, CATP, ...);  // only what CPU needs
        for (int I = 1; I <= 2048; I++) {
            // ... structural code ...
        }
        ergo_vk_upload(d_CATP, CATP, ...);    // push changes back

        // Render (if windowed)
        ergo_vk_render_frame(d_CPSI, 64, 32);
        if (ergo_vk_should_close()) break;
    }

    ergo_vk_shutdown();
}
```

The driver generates this by:
1. Walking the IR main_body.
2. For extracted kernels: emit dispatch call instead of the loop.
3. For structural suffixes: emit the C loop as normal.
4. Insert upload/download around GPU↔CPU transitions.
5. Insert render call at frame boundaries (if --render).

---

## Implementation Approach: Raw Vulkan C API

After evaluating the Vulkan ecosystem (Vulkan-Hpp, VMA, Vk-Bootstrap,
volk, Vookoo, magma), the decision is: **raw Vulkan C API, single file
runtime, no wrapper libraries.**

### Why raw Vulkan

Most Vulkan helper libraries target game engines making thousands of
draw calls per frame. Ergo is compute-first — we dispatch a handful of
compute kernels per simulation tick, then optionally draw a fullscreen
quad. The concerns don't overlap:

- **Loader dispatch overhead (volk):** irrelevant. We make ~5 Vulkan
  calls per frame, not 5000. Nanoseconds on a millisecond tick.
- **C++ wrappers (Vulkan-Hpp):** the entire Ergo toolchain is C99 host
  code + Python compiler. Adding C++ means requiring a C++ compiler,
  which contradicts "no nvcc, no C++" from the Performance Constitution.
- **VMA:** overkill. Ergo arrays have compile-time known shapes. We
  allocate N buffers at init, use them for the entire run, free at
  shutdown. No fragmentation, no pools, no dynamic allocation.
- **Vk-Bootstrap:** solves the init boilerplate nicely, but is C++.

### What we get

- `vk_host.c` is ~800 lines, written once, calling raw `vkCreate*` /
  `vkCmd*` functions. The generated Ergo code calls 8-10 functions
  from it. That's the entire Vulkan surface area.
- `gcc -std=c99 -lvulkan -lglfw` and done. No build system complexity.
- Full auditability — no hidden allocations, no abstraction layers,
  same philosophy as the language.

### Fallback: vkb (C port of vk-bootstrap)

If the init boilerplate (instance creation, physical device selection,
queue family discovery, swapchain setup) proves painful to maintain
across driver versions and platforms, we can pull in `vkb` — the C
port of vk-bootstrap. It handles only the setup ceremony and gets out
of the way for actual compute/render work. It's C99-compatible and
adds no runtime overhead.

Decision: **start without it, add only if we hit real maintenance pain
in the init path.**

## Build Dependencies

| Component | Purpose | When |
|-----------|---------|------|
| Vulkan SDK (`libvulkan`) | Runtime API | Always |
| `spirv-as` | Assemble SPIR-V text to binary | Build time |
| GLFW | Window + surface creation | Render mode only |
| gcc | Compile host C99 + link vk_host.c | Build time |
| vkb (optional) | Vulkan init boilerplate | Only if needed |

All are available on Linux, Windows, Mac (MoltenVK). No NVIDIA
dependency. Runs on any Vulkan-capable GPU.

---

## Work Breakdown

### Phase A: SPIR-V backend (spirv.py)
- Same interface as KernelBackend
- Emit SPIR-V text assembly for each extracted kernel
- Storage buffers for arrays, push constants for scalars
- gl_GlobalInvocationID for thread index
- GLSL.std.450 extended instructions for math
- Test: particle update kernel assembles with spirv-as

### Phase B: Vulkan host runtime (vk_host.c)
- ergo_vk_init (instance, device, queue — headless or windowed)
- Buffer management (create, upload, download)
- Compute pipeline (load SPIR-V, create pipeline, dispatch)
- Synchronization (fence wait after dispatch)
- Test: manually written host code + particle kernel runs

### Phase C: Host codegen integration
- ir_codegen.py aware of GPU plan
- Replace extracted loops with dispatch calls
- Insert buffer alloc/upload/download at transitions
- Structural suffixes emit as normal C loops
- Test: colony sim physics on GPU, structural on CPU

### Phase D: Render pass
- Fullscreen quad vertex shader
- Fragment shader: read storage buffer, map to color
- Swapchain present after compute
- GLFW window events (close, resize)
- Test: colony sim renders live in a window

### Phase E: Polish
- Embed SPIR-V binaries in generated C (no runtime file deps)
- Double-buffering for async compute + render
- Frame timing / vsync
- Graceful fallback if no Vulkan device found

---

## What we are NOT doing

- No optimization levels. The compiler lowers what you wrote.
- No implicit memory transfers. Transfers are visible in generated code.
- No hidden allocation. Every buffer is traceable to a source array.
- No shader compilation at runtime. SPIR-V is compiled at build time.
- No abstraction layers (no engine, no scene graph, no ECS). Just
  buffers and dispatches.

---

## Resolved decisions

**1. Push constants for scalar params.**
128 bytes is the Vulkan minimum guarantee. Colony sim kernel_1 has
14 doubles = 112 bytes — fits. Push constants are simpler codegen
(no extra buffer, no descriptor set entry) and faster than UBOs for
small payloads. If a future kernel exceeds 128 bytes, spill to a
uniform buffer for that kernel only.

**2. Require f64, fail fast.**
Ergo is a deterministic simulation language. Silently dropping to
f32 would produce wrong results and violate the Performance
Constitution. The runtime checks `shaderFloat64` at device selection
and errors with a clear message if unavailable. No f32 fallback path
— that's a second codegen path for minimal gain and maximum risk.
Most discrete GPUs (NVIDIA, AMD, Intel Arc) support f64. Integrated
GPUs that don't are not simulation targets.

**3. SPIR-V text emission first (Option A).**
Emit human-readable SPIR-V assembly, assemble with `spirv-as` from
the Vulkan SDK. Debuggability is worth the build-time dependency.
Binary emission (Option B) can be added later if we need to drop
the SDK requirement.

## Open questions for next session

1. The render fragment shader needs to know the simulation grid layout
   (64x32 for colony). Where does this come from — source annotation,
   compiler inference, or runtime parameter?

2. Frame pacing — should the render loop drive the simulation tick, or
   should simulation run as fast as possible with render sampling the
   latest state?
