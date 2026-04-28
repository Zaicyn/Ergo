# Ergo Memory Tiers Design

## The Premise

Not all data needs the same speed. Physics arrays need GPU VRAM at
maximum bandwidth. Network buffers need CPU accessibility. File preload
caches need capacity, not speed. The language should let the programmer
express this, and the compiler should respect it.

## Current State

Everything is implicitly GPU-local. STATIC arrays go to DEVICE_LOCAL
VRAM. The CPU never touches particle arrays after init — the waveguide
grid is the only cross-boundary data, and it's transferred explicitly
at census intervals via DOWNLOAD_WAVEGUIDE.

This works for "GPU does everything" mode. It breaks when:

- CPU handles networking (oracle consensus, field exchange)
- CPU preloads files (colony genomes, initial conditions)
- CPU runs debug/verification alongside GPU physics
- Multiple GPUs share work with CPU coordination

## The Two-Tier Model

### HOT: GPU-resident, maximum bandwidth

Physics arrays, render buffers, grid accumulators. These are read and
written by GPU kernels every frame. They never leave VRAM unless
explicitly downloaded.

```
HOT REAL :: POS_X(MAXPART)          ! GPU VRAM, DEVICE_LOCAL
HOT REAL :: VEL_X(MAXPART)          ! GPU VRAM, DEVICE_LOCAL
HOT INTEGER :: GRID_DENSITY(32,32,32) ! GPU VRAM, DEVICE_LOCAL
```

Compiler behavior:
- Allocate with VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT
- Never auto-download to CPU
- Explicit DOWNLOAD required for CPU access
- GPU kernels can read/write freely

### COLD: CPU-resident, accessible without transfer

Network buffers, file preload caches, configuration, oracle state,
census history. These are read and written by CPU code. GPU access
is rare or nonexistent.

```
COLD REAL :: GRID_DENSITY_GLOBAL(32,32,32)  ! CPU memory, oracle consensus
COLD INTEGER :: CENSUS_PREV_CRYSTAL          ! CPU, census history
COLD REAL :: NET_FIELD_RECV(32,32,32)        ! CPU, network receive buffer
```

Compiler behavior:
- Allocate with VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | HOST_COHERENT_BIT
- CPU can read/write directly (no staging buffer needed)
- If GPU needs access: explicit UPLOAD, or map as host-visible SSBO
- Acceptable latency: not on the hot path

### Default (no annotation): follows current behavior

STATIC arrays in GPU-extracted loops → HOT (DEVICE_LOCAL)
STATIC arrays only accessed by CPU code → COLD (HOST_VISIBLE)
The compiler infers this from usage analysis. Annotation overrides.

## Why Not Three Tiers?

WARM (shared/pinned memory) is a trap. It's HOST_VISIBLE + DEVICE_LOCAL
on some GPUs (AMD APUs, integrated graphics) but not others (discrete
NVIDIA). Code that depends on WARM being fast is non-portable. Two tiers
(definitely-GPU, definitely-CPU) are always clear. If data needs to cross
the boundary, use explicit UPLOAD/DOWNLOAD.

## Hardware Mapping

| Tier | Vulkan memory flags | Access | Bandwidth |
|------|-------------------|--------|-----------|
| HOT | DEVICE_LOCAL | GPU fast, CPU needs download | 192+ GB/s (RTX 2060) |
| COLD | HOST_VISIBLE, HOST_COHERENT | CPU fast, GPU slow if mapped | ~15 GB/s (PCIe 3.0) |

## CPU/GPU Work Split

The tiers map to a clean work split that's already emerging:

### GPU (HOT data, every frame)
- CLEAR_GRID — zero accumulators
- SCATTER_GRID — particle → density field
- STENCIL_GRID — gradients + crystal blend
- SIM_PHYSICS_STEP — forces, integration, spawn
- SORT_BY_GEN — counting sort at census intervals
- Render — point cloud draw from SoA buffers

### CPU (COLD data, intermittent)
- Oracle consensus — receive GRID_DENSITY_GLOBAL from network
- Census observation — read NPART, compute adaptive interval
- Network send/recv — multicast density grid + spawn commands
- File I/O — load initial conditions, save checkpoints
- Verification — Lagrangian probe comparison, Lyapunov classification
- Window events — GLFW poll, camera input

### Boundary (explicit transfer, at census intervals)
- DOWNLOAD_WAVEGUIDE — GPU → CPU: density grid for oracle
- UPLOAD consensus — CPU → GPU: blended field from network
- UPLOAD spawn commands — CPU → GPU: oracle-directed spawn rate

The key insight: the boundary crossings are infrequent (every 50-2000
frames) and small (~768KB grid). The particle arrays (480MB+) never
cross. HOT stays hot, COLD stays cold.

## Interaction with SORT_BY_GEN

The sort creates implicit fast/slow lanes within the HOT tier:

- COAST particles (31% of ring positions) — minimal compute per thread,
  warps retire early, release registers for other warps
- ACTIVE particles (44%) — full physics, sustained compute
- FLOW particles (25%) — full physics + escape channel

After SORT_BY_GEN, these are clustered in the array. The GPU warp
scheduler naturally gives more resources to the ACTIVE/FLOW warps
because they run longer. COAST warps finish fast and free their slots.

This is hardware-managed lane separation. The language doesn't need
to express it — the sort + the GPU scheduler handle it. But the
HOT/COLD tier split IS something the language expresses because it's
about data placement, not execution scheduling.

## Implementation

### Phase 1: Implicit inference (no syntax change)

The compiler already knows which arrays are GPU-extracted and which
are CPU-only. Use this to automatically choose DEVICE_LOCAL vs
HOST_VISIBLE. No new keywords needed.

Changes:
- ir_gpu.py: track which arrays appear in extracted kernels
- ir_codegen.py: emit VK_MEMORY_PROPERTY_HOST_VISIBLE for CPU-only arrays
- vk_host.c: ergo_vk_create_buffer takes a tier flag

### Phase 2: Explicit annotation (new keywords)

Add HOT/COLD as optional qualifiers on STATIC declarations:

```
HOT STATIC REAL :: POS_X(MAXPART)
COLD STATIC REAL :: GRID_DENSITY_GLOBAL(32,32,32)
```

Parser: recognize HOT/COLD before STATIC/REAL/INTEGER.
Checker: warn if HOT array is only accessed by CPU, or COLD array
is in a GPU-extracted loop.
Codegen: respect the annotation, override inference.

### Phase 3: Multi-device

When multiple GPUs or CPU+GPU coexist:

```
HOT DEVICE(0) REAL :: POS_X(MAXPART)       ! GPU 0
HOT DEVICE(1) REAL :: POS_X_MIRROR(MAXPART) ! GPU 1
COLD REAL :: CONSENSUS_FIELD(32,32,32)       ! CPU, shared between devices
```

This is future work. The tier system supports it because the tiers
map to physical memory locations, and DEVICE(n) is just a location
qualifier.

## Diagnostic Integration

The extension can show tier information in hover:

```
POS_X: HOT REAL array, 30000000 elements, 114.4 MB (DEVICE_LOCAL)
GRID_DENSITY_GLOBAL: COLD REAL array, 32768 elements, 128 KB (HOST_VISIBLE)
```

PERF warning if a COLD array is accessed in a GPU hot path:

```
PERF: COLD array 'GRID_DENSITY_GLOBAL' accessed in GPU-extracted loop
      Consider HOT copy or explicit UPLOAD before kernel
```

WARNING if a HOT array is downloaded every frame:

```
WARNING: HOT array 'POS_X' downloaded every frame (480 MB/frame)
         CPU-GPU transfer bandwidth is 15 GB/s — this costs 32ms
```
