# Ergo Adaptive Rendering Design

## The Premise

Two types of visible matter, two rendering strategies:

- **Live fluid** (particles) — dynamic, soft, volumetric → Gaussian splats
- **Crystal structure** (grid) — static, hard, persistent → Meshlets

The 32^3 density grid is the acceleration structure for both.
No separate octree or BVH needed.

## Architecture

```
Frame pipeline:
  GPU Compute: CLEAR → SCATTER → STENCIL → PHYSICS
       ↓
  Grid culling pre-pass (32^3 = 32K cells)
       ↓
  ┌─────────────────────────────────────────┐
  │ Gaussian pass: live particles           │
  │   - Each particle = oriented gaussian   │
  │   - Size from OMEGA (energy = influence)│
  │   - Orientation from velocity direction │
  │   - Opacity from density coupling       │
  │   - Depth sorted (front-to-back)        │
  └─────────────────────────────────────────┘
       +
  ┌─────────────────────────────────────────┐
  │ Meshlet pass: crystal field             │
  │   - Each non-zero GRID_CRYSTAL cell     │
  │   - Meshlet = small triangle cluster    │
  │   - Material properties → shading       │
  │   - Static — only updates on crystal    │
  │     banking events                      │
  └─────────────────────────────────────────┘
       ↓
  Composite → swapchain present
```

## Gaussian Splats for Live Particles

Each of the 25M+ particles becomes an oriented 3D gaussian:

| Gaussian property | Source | Notes |
|---|---|---|
| Position | POS_X, POS_Y, POS_Z | Already in SoA buffers |
| Scale/size | OMEGA_NAT | High energy = larger splat |
| Orientation | VEL_X, VEL_Y, VEL_Z | Velocity = elongation direction |
| Color | OMEGA_NAT or GEN | Heat palette or ring position |
| Opacity | GRID_DENSITY at cell | Dense regions = more opaque |

Advantages over current point cloud:
- Smooth volumetric appearance (no gaps between points)
- Natural LOD — distant particles become larger, fewer needed
- Depth-sorted rendering gives correct transparency
- Already have all the input data — no new arrays needed

Implementation: vertex shader computes gaussian quad per particle,
fragment shader evaluates gaussian falloff. Similar to 3D Gaussian
Splatting but without the neural training — properties are physical.

## Meshlets for Crystal Field

Each GRID_CRYSTAL cell with count > 0 becomes a meshlet:

| Meshlet property | Source | Notes |
|---|---|---|
| Position | Grid cell (I,J,K) × CELL_SIZE | Fixed spatial location |
| Geometry | Cube or iso-surface | Depends on neighbor occupancy |
| Color/shading | GRID_MATERIAL | Archetype → base color, deltas → weathering |
| Coherence | MAT_COHERENCE | High = smooth surface, low = rough/cracked |
| Density | GRID_CRYSTAL count | More crystals = more solid |

Advantages:
- Static between crystallization events — no per-frame recompute
- Small triangle clusters (64-128 triangles per meshlet)
- Meshlet culling is per-cell — 32^3 checks, trivial
- Material properties give free visual variation

Implementation: compute shader generates meshlets from non-zero
GRID_CRYSTAL cells. Only regenerates when crystal count changes
(at census intervals). Fragment shader reads material properties
for per-meshlet shading.

## Grid-Level Culling

The 32^3 grid provides O(32K) culling for both render passes:

### Frustum culling
- Test each grid cell's AABB against the view frustum
- Skip cells entirely outside the frustum
- At 32^3 = 32,768 cells, this is ~0.01ms

### Occlusion culling
- Walk grid cells front-to-back in view direction
- High-density crystal cells occlude what's behind them
- Particles behind solid crystal structure are skipped

### Density threshold culling
- Skip cells where GRID_DENSITY = 0 (no live particles)
- Skip cells where GRID_CRYSTAL = 0 (no structure)
- At equilibrium, many cells are empty — significant cull

### LOD from grid
- Near camera: render individual gaussians per particle
- Far from camera: render one gaussian per grid cell
  (position = cell center, size = cell extent, color = average OMEGA)
- Transition distance based on cell projected size

## Data Flow

```
Live particles (every frame):
  POS_X/Y/Z  ──→ gaussian position
  VEL_X/Y/Z  ──→ gaussian orientation
  OMEGA_NAT  ──→ gaussian size + color
  GRID_DENSITY ──→ gaussian opacity
  All in existing GPU buffers — zero extra memory

Crystal field (at census / banking events):
  GRID_CRYSTAL  ──→ meshlet occupancy
  GRID_MATERIAL ──→ meshlet shading
  Already downloaded to CPU at census
  Meshlet geometry regenerated only on change
```

## Compatibility with Current Pipeline

The current point cloud renderer (`render_points.vert/frag`) stays as
a fallback. The gaussian + meshlet pipeline is an upgrade path:

1. **Phase 1:** Replace point cloud with gaussian splats
   - Same vertex shader structure, different quad expansion
   - Fragment shader adds gaussian falloff
   - No new buffers, no new compute passes

2. **Phase 2:** Add meshlet pass for crystal field
   - New compute shader: grid → meshlet generation
   - New graphics pipeline for meshlet rendering
   - Only runs when GRID_CRYSTAL changes

3. **Phase 3:** Grid-level culling
   - CPU-side frustum test on 32^3 cells
   - Pass visible cell list to gaussian + meshlet passes
   - Skip invisible cells entirely

4. **Phase 4:** LOD transitions
   - Per-cell LOD based on projected size
   - Aggregate distant cells into single gaussians
   - Smooth transition to avoid popping

## Performance Estimates (RTX 2060)

| Component | Current (points) | Phase 1 (gaussians) | Phase 2+ (full) |
|---|---|---|---|
| Vertex shader | 30M invocations | 30M quad expansions | 30M + meshlets |
| Fragment shader | 30M × 1px | 30M × ~4px (gaussian) | + meshlet shading |
| Overdraw | Minimal (1px) | Moderate (gaussian overlap) | Managed (depth sort) |
| Memory | Zero extra | Zero extra | ~1MB meshlet buffer |
| Expected FPS at 30M | 74 | ~40-50 | ~50-60 with culling |

Gaussians are more expensive per-pixel than points but the visual
quality leap is enormous. Grid culling recovers some of the cost
by skipping empty regions entirely.

## Shell-Based Front-to-Back Rendering

The density grid isn't just a culling oracle — it IS the rendering
primitive. The 32^3 grid projected into view space gives a shell
structure. Render front-to-back, early-terminate on opacity.

### How it works

1. Sort grid layers by view direction (32 slices)
2. For each shell (front to back):
   - Project non-empty cells onto screen-space meshlets
   - Render gaussian splats for particles in those cells
   - Accumulate opacity per pixel
3. When a pixel's opacity exceeds threshold → stop traversing
4. Dense crystal cells are fully opaque → immediate termination

### Why it solves overdraw

- Each pixel is touched by at most one shell's particles
- Crystal meshlets are hard occlusion boundaries
- The back half of the galaxy never renders (occluded by front)
- Typically 8-12 shells before opacity saturates (out of 32 max)

### Numbers

```
32 shells (worst case, looking through full grid)
32×32 = 1024 cells per shell
8-12 shells before opacity saturates = ~8K-12K meshlets
Particles in visible front cells: ~2-5M out of 30M
Everything else culled before fragment shader
```

Instead of 30M gaussians competing for screen space, you get 2-5M
in the visible front-facing cells with zero overdraw. The shell
structure guarantees each pixel is written once.

### Implementation

This works in the existing Vulkan rasterization pipeline — no compute
ray marching needed:

- Compute pre-pass: sort grid cells by view depth (32K sorts, trivial)
- Vertex shader: expand meshlets for front-visible cells
- Fragment shader: gaussian evaluation with opacity accumulation
- Early-Z + depth test handles the shell ordering naturally

The crystal field makes this even better: crystal cells are fully
opaque, so any crystal meshlet immediately terminates that ray through
the grid. Dense crystal regions become free hard occlusion for the
live fluid behind them.

## Connection to Material System

The material archetype drives meshlet appearance:

| Archetype | Visual |
|---|---|
| STELLAR_DEAD | Bright white/blue, smooth, glowing |
| ROCK | Grey/brown, rough texture from low coherence |
| ICE | Translucent blue, smooth |
| DEAD_CELL | Amber/yellow, soft edges |
| METAL | Reflective, high coherence = mirror-like |

Material deltas modify the base appearance:
- Reduced COHERENCE → surface cracks, roughness
- Reduced ENERGY → dimming
- Increased MOBILITY → wavering edges, transparency

This is the hysteresis memory making decay visible — a weathered
crystal looks different from a pristine one because the delta
encodes its history.
