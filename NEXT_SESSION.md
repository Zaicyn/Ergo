# Next Session: Sort-by-GEN + Ring Coupling Physics

## What's Done

Steps 1-5 complete — RING_PREV / RING_NEXT intrinsics work end-to-end:

- **ir.py** — Op.RING_PREV, Op.RING_NEXT enum values
- **ir_builder.py** — Intrinsic recognition, type-preserving (REAL→REAL, INTEGER→INTEGER)
- **spirv.py** — OpGroupNonUniformShuffle with wrapping modular index `(lane ± 1) & 31`
  - Capabilities: GroupNonUniform + GroupNonUniformShuffle
  - Builtin: SubgroupLocalInvocationId
  - Note: uses explicit index shuffle (NOT ShuffleUp/Down — those don't wrap per spec)
- **spirv.py** — Bonus: f64 type no longer emitted in f32 mode (passes spirv-val)
- **ir_codegen.py** — Bonus: VRAM capacity code only emitted when MAXPART exists
- **tests/gpu_ring_shuffle.mcl** — Validated on RTX 2060: lane 0 RING_PREV returns lane 31's value (wraps correctly)

## What's Next

### Step 6: Sort by GEN — Counting sort (3 kernels)

32 buckets, one per GEN value. 32 = 2^5 = warp size.

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

Sort frequency: every N frames (at census intervals). GEN changes slowly
(phase advance wraps the ring over ~1000 frames).

### Step 7: SORT_BY_GEN directive

New MCL directive — compiler-generated kernels, NOT runtime C:

```
SORT_BY_GEN FLAGS, POS_X, POS_Y, POS_Z, VEL_X, VEL_Y, VEL_Z, OMEGA_NAT
```

Lists all particle arrays permuted together. Compiler generates histogram,
scan, and scatter kernels + temporary buffers.

Called in main loop at census intervals.

### Step 8: Ring coupling physics

Add to fluid_subs.mcl as section 17.5 (after density siphon, before thresholds):

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

New constant: K_PHASE_LOCK (start ~0.001, tune empirically)

Data shuffled per neighbor: OMEGA (float) + PH (integer) = 8 bytes.
Zero memory traffic — register to register within warp.

### Step 9: Tune

- K_PHASE_LOCK empirically against simulation behavior
- Verify metabolic conservation (total OMEGA in ring minus decay)
- Check that phase-locking doesn't suppress natural ring dynamics

## Design Principles

- Ring coupling is **topological, not spatial** — two ring-adjacent particles
  can be far apart in 3D. The coupling is a functional pathway, not a force.
- 3D spatial coupling (gravity, density siphon) stays in the grid — **orthogonal and additive**
- BLAS insight: don't pack data, change the access pattern. SoA with coalesced
  warp access is already optimal for GPU. The sort reorders particles so the
  warp topology matches the ring topology.
- Allocator insight: tolerate gaps, don't compact. Dead crystal slots cost
  near-zero compute (CYCLE branch).

## Current Performance

- Headless: 141 fps at 29M (7.1ms/frame: scatter 1.2ms, stencil 0.007ms, physics 5.9ms)
- Render: 74 fps at 30M (13.5ms/frame: compute 7ms + vertex 6.5ms)
- RTX 2060, f32, DEVICE_LOCAL buffers

## Build

```bash
./structured/build.sh
python -m mcl --target spirv --precision f32 --no-split -o galaxy_gpu galaxy_structured.mcl

# Render (strip VERIFY for no-oracle mode):
sed '/VERIFY/,/4250/d' galaxy_structured.mcl > /tmp/nonet.mcl
python -m mcl --target spirv --precision f32 --no-split --render -N 29000000 -M 30000000 -o galaxy_render /tmp/nonet.mcl
```

## Key Files

```
structured/
  constants.mcl       — LUTs, parameters, PFLAG_*, PFLAG_BANKED, phase encoding
  fluid_state.mcl     — Particle arrays (SoA), spawn control
  waveguide_state.mcl — Grid arrays, GRID_CRYSTAL, census state
  fluid_subs.mcl      — Physics + spawn kernel (ring coupling goes here)
  waveguide_subs.mcl  — Clear, scatter (crystal banking), stencil
  census.mcl          — CPU observation
  main.mcl            — Pipeline orchestration (SORT_BY_GEN goes here)

mcl/
  ir.py               — IR nodes + Op enum (RING_PREV, RING_NEXT added)
  ir_builder.py       — Intrinsic recognition (RING_PREV, RING_NEXT added)
  spirv.py            — SPIRV codegen (SubgroupShuffle added)
  ir_codegen.py       — C/SPIRV driver codegen
  parser.py           — MCL parser
  driver.py           — Build driver

mcl/runtime/
  vk_host.c           — Vulkan runtime
  render_points.vert  — Point cloud vertex shader (direct SoA read)
  render_points.frag  — Point cloud fragment shader (branchless heat palette)
  render_shaders.h    — Embedded SPIRV (auto-generated by build_shaders.sh)

allocator/
  sq2core.f           — Torus allocator (F77) — design reference for gap tolerance

tests/
  gpu_ring_shuffle.mcl — Validates RING_PREV/RING_NEXT wrapping on GPU
```
