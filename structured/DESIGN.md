# Structured Pipeline — Three-Layer Architecture

## The Principle

Everything is a signed accumulator. Positive = source, negative = drain, zero = skip.
Zero is not "nothing happened." Zero is "nothing TO do." The null is the skip signal.

The system has three layers, each with different update rates and ownership:

```
Layer 1: CONSTANTS (reference lattice)
    Computed once. Never changes during simulation.
    CPU owns. GPU reads.
    
Layer 2: WAVEGUIDES (field structure)
    Updated at census intervals (every 50-2000 frames).
    CPU computes from sampled conditions.
    GPU reads as correction overlay.
    
Layer 3: FLUID (particle dynamics)
    Updated every frame.
    GPU owns exclusively.
    CPU never sees individual particles — only summaries.
```


## Layer 1 — Constants (the reference)

Things that never change. Set once at init.

```
FLOW_MODE[32]       — lifecycle mode per ring segment
TANGENT[3][32]      — tangent vectors per ring segment
CURVE_PT[3][32]     — curve control points per ring segment
Z_COUPLING[32]      — z-coupling per ring segment
FLOW_W[32]          — flow weights per ring segment
CUBOCT[3][12]       — cuboctahedral seed shell vertices
BH_MASS             — central mass
CELL_SIZE           — grid cell dimension
GRID_HALF           — grid center offset
All OMEGA_* params  — thresholds, decay rates, gain
All PFLAG_* masks   — status bit definitions
GEN_SHIFT, GEN_MASK — phase bit layout
PHASE_INC_SCALE     — phase advance rate
SEAM_STEP_PH        — spawn phase offset
```

These are push constants or small GPU buffers. Read-only. Never uploaded after init.
The GPU kernel reads them but never writes them.


## Layer 2 — Waveguides (field structure)

The density field and its derivatives. Updated by the CPU sampling the
GPU's particle state at census intervals.

```
GRID_DENSITY[32][32][32]     — particle count per cell (INTEGER)
GRID_GRAD_X/Y/Z[32][32][32] — density gradients (REAL)
GRID_MET_GATE[32][32][32]    — metabolic gate per cell (REAL)
BIN_PRESENCE[32][32][32]     — generation bin mask per cell (INTEGER)
GRID_DENSITY_GLOBAL[32][32][32] — oracle consensus field (REAL)
FIELD_BLEND                  — blend alpha (0=autonomous, 1=full consensus)
```

The waveguide layer is the structure that guides the fluid. It changes slowly.
The GPU rebuilds it every frame via scatter+stencil, but the STRUCTURE of it
(which cells matter, where the gradients point) is low-frequency.

The oracle provides GRID_DENSITY_GLOBAL as an external correction.
The blend mixes it into the local field before computing gradients.

Key insight: the CPU oracle never sees individual particles. It sees the
field — the 128KB density grid. That's the summary. The waveguide IS the
interface between GPU fluid and CPU supervision.


## Layer 3 — Fluid (particle dynamics)

The particles. GPU-exclusive. Each particle is a signed accumulator.

```
Per particle (8 arrays):
    POS_X, POS_Y, POS_Z    — position (REAL, accumulated by velocity)
    VEL_X, VEL_Y, VEL_Z    — velocity (REAL, accumulated by forces)
    OMEGA_NAT               — metabolic energy (REAL, accumulated by drive-decay)
    FLAGS                   — status + phase + generation (INTEGER, bitfield)

Per particle, the accumulator logic:
    velocity += force * dt        (positive force = accelerate, negative = decelerate)
    position += velocity * dt     (positive velocity = move, zero = stationary = skip)
    omega += (target - omega) * response * dt   (positive drive = heat, negative = cool)
    
    If velocity ≈ 0 and omega ≈ 0: particle is crystallized. Skip it.
    If omega > threshold: nova. Change mode.
    If omega < threshold: crystallize. Freeze.
    
    Zero omega = off. Zero velocity = frozen. Zero density = empty cell = skip.
```


## The Pipeline (per frame)

```
CLEAR (zero waveguide accumulators)
    ↓
SCATTER (fluid → waveguide)
    Each particle deposits +1 into its density cell
    Each particle advances its phase (integer accumulator in FLAGS)
    Each particle writes its generation bin
    Zero-flagged (ejected/crystal) particles: SKIP
    ↓
STENCIL (waveguide → waveguide)
    Compute gradients from density (central differences)
    Compute MET_GATE from bin presence (popcount → coverage)
    Blend with oracle global field (low-frequency correction)
    Cells with zero density: gradients are zero. Natural skip.
    ↓
PHYSICS (waveguide + constants → fluid)
    Each particle reads the waveguide at its position
    Computes forces from gravity (constant) + field (waveguide)
    Accumulates velocity, position, omega
    Zero-force cells: no density siphon contribution. Natural skip.
    COAST mode: only gravity (no waveguide read). Minimal accumulation.
    Crystal: frozen. Skip entirely.
```


## The Accumulator Model

Every value in the system is one of three states:
- **Positive**: gaining, sourcing, heating, moving outward
- **Negative**: losing, draining, cooling, moving inward  
- **Zero**: off, skip, no contribution, inert

The frame loop doesn't "compute physics for every particle."
It "accumulates signed deltas for every non-zero particle."

This means:
- Crystal particles (omega=0, vel=0) cost zero. They exist but don't compute.
- Empty cells (density=0) produce zero gradients. Stencil skips naturally.
- COAST particles with zero omega decay contribute nothing to the field.
  They still orbit (gravity accumulates velocity) but the waveguide ignores them.

The GPU doesn't decide "should I skip this?" — the ZERO does. The multiply
by zero IS the skip. No branch needed. The hardware's FMA unit produces
zero output when any input is zero. That's free.


## What Changes From Current Architecture

### Constants layer (mostly done)
- LUT arrays are already push constants or small buffers
- Physics parameters are already push constants
- Nothing changes here

### Waveguide layer (needs cleanup)
- GRID_DENSITY changes from per-frame GPU rebuild to census-interval sampling
  when running multi-rate (scatter every N frames at steady state)
- Oracle field becomes a proper correction term, not a replacement
- MET_GATE stays in stencil (already done)
- The waveguide is the ONLY thing the CPU oracle ever sees or modifies

### Fluid layer (needs restructuring)
- Ping-pong: physics reads from one half, writes to the other
  (the wave propagates, the residual is what scatter measures next frame)
- The render reads from the write half (latest output)
- Downloads for CPU code (spawn, census) read from the write half
- The fluid layer is NEVER downloaded in bulk — only sampled:
  * 12 probe particles for VERIFY (672 bytes)
  * Population count + omega stats for census (96 bytes)
  * Density grid for oracle (128KB — but that's waveguide, not fluid)

### The render
- Render reads directly from the GPU fluid buffers at the correct offset
- No CPU involvement in render — no download, no upload, no min/max scan
  (move the color range to a GPU reduction or use fixed range)
- Render happens AFTER frame_end, reading from write-half of ping-pong
- The render IS a consumer of the fluid layer, like physics but read-only


## File Structure

```
structured/
    DESIGN.md           — this file
    constants.ergo       — Layer 1: LUTs, parameters, seed geometry
    waveguide.ergo       — Layer 2: grid subroutines (clear, scatter, stencil, blend)
    fluid.ergo           — Layer 3: physics step, spawn
    census.ergo          — CPU sampling: population stats, oracle communication
    main.ergo            — pipeline orchestration: init → frame loop
```

When Ergo gets USE/INCLUDE, these become separate modules.
Until then, they concatenate into galaxy_structured.ergo in dependency order.


## The Key Insight

The CPU doesn't simulate. The CPU OBSERVES.

The GPU runs the fluid autonomously. The CPU samples the waveguide
at census intervals. The oracle aggregates waveguides from multiple GPUs.
The correction flows back as a field overlay, not as particle commands.

```
GPU (fluid):     scatter → stencil → physics → scatter → ...
                     ↓                                ↑
CPU (observer):   sample density    →    blend correction
                     ↓                        ↑
Oracle (consensus): sum grids → trust weight → broadcast
```

The CPU never touches particles. The oracle never touches waveguides directly.
Each layer communicates through the interface below it:
- Constants are read by waveguides and fluid
- Waveguides are read by fluid, sampled by CPU
- Fluid is owned by GPU, invisible to CPU except through waveguide summaries
