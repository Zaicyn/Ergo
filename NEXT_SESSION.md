# Next Session: Particle Compaction + Warp-Level Skip

## Goal

Eliminate wasted GPU compute for dead/crystallized particles by compacting
the alive particles to the front of the array. This reduces dispatch size
and creates uniform crystal-only warps at the tail that skip entirely.

## The Problem

At 30M particles after many frames:
- Low indices: crystallized (frozen, FLAGS has PFLAG_CRYSTAL)
- Mid indices: mixed alive/dead, mixed COAST/ACTIVE/FLOW
- High indices: fresh spawns (ACTIVE)

The physics kernel dispatches `(NPART + 255) / 256` workgroups. NPART
includes dead particles. Dead particles hit the CYCLE at line 193 and
exit, but the warp still launched and the thread still occupied a slot.

With COAST particles (31%), the unified kernel computes field coupling
multiplied by zero — 4% wasted compute. With dead particles, the CYCLE
is free but the dispatch size is inflated.

## The Fix: Periodic Compaction

Every N frames (e.g., every 1000 or at census intervals):

1. **Count alive** — parallel reduction over FLAGS, count non-crystal/non-ejected
2. **Prefix scan** — compute destination index for each alive particle
3. **Scatter** — move alive particles to compact indices [0..alive_count)
4. **Update NPART** — set to alive_count

After compaction:
- Dispatch size = alive_count (no dead particle warps)
- First warps = oldest alive particles (likely COAST → will crystallize soon)
- Last warps = freshest spawns (ACTIVE)
- Crystal warps eliminated entirely

## Compaction Algorithm (GPU parallel)

```
// Step 1: Per-thread alive flag
alive[i] = (FLAGS[i] & (CRYSTAL | EJECTED)) == 0 ? 1 : 0

// Step 2: Exclusive prefix scan on alive[]
// dest[i] = sum(alive[0..i-1])
// This gives the destination index for each alive particle.

// Step 3: If alive, scatter to dest[i]
if (alive[i]) {
    POS_X[dest[i]] = POS_X[i]
    // ... all particle arrays
    FLAGS[dest[i]] = FLAGS[i]
}

// Step 4: NPART = total alive count (last element of scan + last alive flag)
```

The prefix scan is the hard part — it's a well-known GPU algorithm
(Blelloch scan, work-efficient). Ergo's SPIRV backend doesn't generate
scans yet, but the allocator in other versions of the codebase has one.

## Implementation Options

### Option A: Separate compaction kernel (cleanest)
- New subroutine `SIM_COMPACT()` with its own extracted GPU kernel
- Called from main loop at census intervals
- Needs: prefix scan array, temporary buffers for scatter
- The allocator (sq2core or similar) may already have this

### Option B: Compact during scatter (piggyback)
- Scatter already iterates all particles
- During scatter, also compute alive flag + write to compact indices
- Combines compaction with the density pass
- Harder to implement but zero extra dispatches

### Option C: Lazy compaction (simplest)
- Don't scatter — just swap dead particles to the end
- Each frame, if particle I is dead and I < NPART, swap with NPART-1
  and decrement NPART
- Sequential, but only processes a few particles per frame
- Works on CPU, not GPU-friendly

## What Exists

The user mentions a compaction implementation exists in another version
of the allocator. Check:
- `allocator/sq2core.f` — the Squaragon V2 allocator
- Other repos the user has access to
- The pattern is: prefix scan → scatter → update count

## Current Architecture (for context)

```
structured/
  constants.mcl       — Layer 1: LUTs, parameters
  fluid_state.mcl     — Layer 3: particle arrays, spawn control
  waveguide_state.mcl — Layer 2: grid arrays, census state
  fluid_subs.mcl      — Physics + spawn (unified kernel)
  waveguide_subs.mcl  — Clear, scatter, stencil
  census.mcl          — CPU observation (NPART only currently)
  main.mcl            — Pipeline: CLEAR → SCATTER → STENCIL → PHYSICS
  build.sh            — Assembles → galaxy_structured.mcl
```

Pipeline per frame (zero CPU↔GPU transfers):
```
GPU: CLEAR → SCATTER → STENCIL → PHYSICS+SPAWN
CPU: observes at census intervals only (768KB grid download)
```

Performance: 134 fps at 30M, 138 fps at 29M (RTX 2060, f32)
Known inefficiency: COAST (31%) computes field coupling × zero = 4% waste

## Build

```bash
./structured/build.sh
python -m mcl --target spirv --precision f32 --no-split -o galaxy_gpu galaxy_structured.mcl
python -m mcl --target spirv --precision f32 --no-split --render -o galaxy_render galaxy_structured.mcl
ERGO_PROFILE=1 ./galaxy_gpu
```

Render requires stripping VERIFY/NET line for no-oracle mode:
```bash
sed '/VERIFY/,/4250/d' galaxy_structured.mcl > /tmp/render.mcl
python -m mcl --target spirv --precision f32 --no-split --render -N 1000000 -M 1000000 -o galaxy_render /tmp/render.mcl
```

## Key Decisions from This Session

- Unified physics kernel: one path, COUPLING multiplier, no mode branching
- OMEGA_BASE always present (not gated by COUPLING) — prevents total collapse
- Spawn is continuous rate-based (SPAWN_RATE=0.01), not discrete ticks
- CPU never writes particle arrays after init — GPU is sole owner
- Render: f32 vertex shader, compute→vertex barrier, frame_end before render
- No per-frame uploads or downloads in frame loop
