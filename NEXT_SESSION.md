# Next Session: Warp-Level Ring Shuffle

## Goal

Direct ring-neighbor coupling via GPU warp shuffle. Particles sorted by GEN
(32 Viviani ring positions = 32 warp lanes) exchange OMEGA and PHASE in
registers. Zero memory traffic for topological coupling.

## Why

The Viviani ring is a 5D topology (3 spatial + phase + omega). Ring-adjacent
particles (GEN and GEN±1) share a functional pathway regardless of 3D distance.
Currently this coupling is implicit — goes through the density grid indirectly.
Making it explicit via shuffle means:

- Metabolic energy (OMEGA) flows along the ring at wire speed
- Phase coherence is enforced directly between ring neighbors
- The 3D spatial coupling (gravity, density siphon) stays in the grid — orthogonal, additive

This is the "2 and 2 linking through space" — positive and negative units
connected in 5D, with the warp as the ring.

## Architecture

### 1. Language: RING_PREV / RING_NEXT intrinsics

New MCL intrinsics for cross-lane register exchange:

```
OMEGA_PREV := RING_PREV(OMEGA)    ! value from GEN-1 neighbor
OMEGA_NEXT := RING_NEXT(OMEGA)    ! value from GEN+1 neighbor
PHASE_PREV := RING_PREV(PHASE)
PHASE_NEXT := RING_NEXT(PHASE)
```

Semantics: "get this scalar from my ring neighbor." Requires particles sorted
by GEN so ring adjacency = warp adjacency. The ring wraps: lane 0's PREV is
lane 31, lane 31's NEXT is lane 0.

Parser: recognize RING_PREV(expr) and RING_NEXT(expr) as intrinsic function calls.
IR: new IRIntrinsic nodes (RING_PREV, RING_NEXT) carrying the source expression.

### 2. SPIRV: SubgroupShuffle emission

RING_PREV(x) → OpGroupNonUniformShuffleUp with delta=1
RING_NEXT(x) → OpGroupNonUniformShuffleDown with delta=1

Wrapping: SPIRV shuffle with delta wraps at subgroup size (32 on NVIDIA).
If subgroup size != 32, use OpGroupNonUniformShuffle with explicit index:
  RING_PREV: OpGroupNonUniformShuffle(x, (lane - 1 + 32) % 32)
  RING_NEXT: OpGroupNonUniformShuffle(x, (lane + 1) % 32)

Requires:
- Capability: GroupNonUniform, GroupNonUniformShuffle
- Execution model: GLCompute with SubgroupSize = 32
- gl_SubgroupInvocationID for lane index

The codegen needs to:
1. Declare SubgroupSize execution mode
2. Import gl_SubgroupInvocationID as a builtin
3. Emit shuffle ops in the kernel body

### 3. Sort by GEN: Counting sort (3 kernels)

32 buckets, one per GEN value. 32 = 2^5 = warp size. Perfect.

```
Kernel A: COUNT_GEN
  For each particle: atomicAdd(histogram[GEN], 1)
  32 shared-memory atomics. Fits in one cache line.

Kernel B: SCAN_GEN (single warp, 32 elements)
  Exclusive prefix sum over histogram → offsets[0..31]
  Unrolled, 5 steps. Trivial.

Kernel C: SCATTER_GEN
  For each particle: idx = atomicAdd(offsets[GEN], 1); sorted[idx] = particle
  Writes are coalesced within each GEN bucket.
```

After sort: particles with same GEN are contiguous. Groups of 32 consecutive
particles span all 32 ring positions. Each warp = one complete ring traversal.

Sort frequency: every N frames (like census). Not every frame — GEN changes
slowly (phase advance wraps the ring over ~1000 frames).

### 4. MCL integration: SORT_BY_GEN directive

New MCL directive that tells the compiler to insert the 3-kernel sort:

```
SORT_BY_GEN FLAGS, POS_X, POS_Y, POS_Z, VEL_X, VEL_Y, VEL_Z, OMEGA_NAT
```

Lists all particle arrays that must be permuted together. The compiler generates
the histogram, scan, and scatter kernels, plus temporary buffers.

Called in the main loop at census intervals (like compaction would have been).

### 5. Ring coupling kernel (new physics section)

After the existing spatial physics (gravity, density siphon, envelope, steering),
add ring coupling as section 17.5 (before threshold observations):

```
! ── 17.5. RING COUPLING (topological, not spatial) ───────
! Metabolic exchange: OMEGA flows along ring via FLOW_W direction
OMEGA_PREV := RING_PREV(OMEGA)
OMEGA_NEXT := RING_NEXT(OMEGA)

DEFICIT := TARGET - OMEGA
TRANSFER := MIN(ABS(DEFICIT), ABS(Z_C) * DT)
IF FLOW_WG > 0.0 THEN
  OMEGA := OMEGA + TRANSFER * SIGN(1.0, OMEGA_NEXT - OMEGA)
ELSE
  OMEGA := OMEGA + TRANSFER * SIGN(1.0, OMEGA_PREV - OMEGA)
ENDIF

! Phase lock: restoring toward reference Viviani spacing
PH_NEXT := RING_NEXT(PH)
PH_DIFF := IAND(PH_NEXT - PH + PHASE_MASK + 1, PHASE_MASK)
PH_ERR := PH_DIFF - SEAM_STEP_PH
OMEGA := OMEGA - REAL(PH_ERR) * K_PHASE_LOCK * DT
```

New constants needed:
- K_PHASE_LOCK: coupling strength for phase restoring (start ~0.001, tune empirically)

### 6. Data shuffled per neighbor

Per shuffle operation (2 per coupling step: PREV and NEXT):
- OMEGA (float, 4 bytes) — metabolic state
- PH (integer, 4 bytes) — phase on ring

That's 16 bytes of shuffle per particle per frame. At 30M particles, the shuffle
itself is zero-cost (register to register within warp). The sort is the only
memory cost, and it runs at census intervals.

### 7. Implementation order

1. SPIRV: Add SubgroupShuffle capability + emission (ir_codegen.py)
2. Parser: Recognize RING_PREV / RING_NEXT as intrinsic calls
3. IR: Add IRIntrinsic nodes for ring shuffle
4. Codegen: Emit OpGroupNonUniformShuffleUp/Down for ring intrinsics
5. Test: Simple MCL program that shuffles a value and prints it
6. Sort: Implement COUNT_GEN / SCAN_GEN / SCATTER_GEN kernel extraction
7. Directive: SORT_BY_GEN parser + codegen support
8. Physics: Add ring coupling section to fluid_subs.mcl
9. Tune: K_PHASE_LOCK empirically, verify conservation

## What exists

- Physics kernel: fluid_subs.mcl (424 lines), fully GPU-extracted
- GEN encoding: 5 bits in FLAGS (bits 8-12), 32 ring positions
- LUTs: FLOW_MODE, TANGENT, Z_COUPLING, FLOW_W, CURVE_PT — all indexed by GEN
- SPIRV backend: ir_codegen.py emits compute shaders, handles push constants,
  barriers, atomics. Does NOT yet emit subgroup operations.
- Warp size: 256 threads per workgroup (NVIDIA maps to 8 warps of 32)

## Build

```bash
./structured/build.sh
python -m mcl --target spirv --precision f32 --no-split -o galaxy_gpu galaxy_structured.mcl

# Render (strip VERIFY for no-oracle mode):
sed '/VERIFY/,/4250/d' galaxy_structured.mcl > /tmp/nonet.mcl
python -m mcl --target spirv --precision f32 --no-split --render -N 29000000 -M 30000000 -o galaxy_render /tmp/nonet.mcl
```

## Current performance

- Headless: 141 fps at 29M (7.1ms/frame: scatter 1.2ms, stencil 0.007ms, physics 5.9ms)
- Render: 74 fps at 30M (13.5ms/frame: compute 7ms + vertex 6.5ms)
- RTX 2060, f32, DEVICE_LOCAL buffers

## Key files

```
structured/
  constants.mcl       — LUTs, parameters, PFLAG_*, phase encoding
  fluid_state.mcl     — Particle arrays (SoA), spawn control
  waveguide_state.mcl — Grid arrays, GRID_CRYSTAL, census state
  fluid_subs.mcl      — Physics + spawn kernel
  waveguide_subs.mcl  — Clear, scatter (crystal banking), stencil
  census.mcl          — CPU observation
  main.mcl            — Pipeline orchestration

mcl/
  ir_codegen.py       — SPIRV codegen (2311 lines)
  ir.py               — IR nodes (380 lines)
  parser.py           — MCL parser (739 lines)
  driver.py           — Build driver (294 lines)

mcl/runtime/
  vk_host.c           — Vulkan runtime (2135 lines)
  render_points.vert  — Point cloud vertex shader
  render_points.frag  — Point cloud fragment shader
  render_shaders.h    — Embedded SPIRV (auto-generated)

allocator/
  sq2core.f           — Torus allocator (688 lines, F77)
```
