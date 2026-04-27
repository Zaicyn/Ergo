# Ergo Galaxy Simulation — Session Context

## What This Is

A metabolic galaxy simulation written in Ergo (Fortran-like DSL), compiled to
SPIRV compute shaders via a Python compiler, running on GPU (RTX 2060).
29 million particles at 141-144 fps with full Viviani force model.

The simulation models a galaxy as a metabolic system where particles traverse
a 32-segment lifecycle ring. The ring determines mode (COAST/ACTIVE/FLOW),
coupling to the density field, and spawn behavior. Two rotations (4pi) to
return to origin — spinor topology.

## Architecture: Forward Pipeline with Causal Ordering

```
CLEAR → SCATTER → STENCIL (+ blend) → PHYSICS
         ↓           ↓                    ↓
    write field   blend global +       read field
    + phase       transform to         update
    + generation  gradients            particles
                  + met_gate
```

**Ping-pong buffers**: Read-write particle arrays are doubled. Physics reads
from offset `PP_RD`, writes to offset `PP_WR`. Offsets swap each frame.

**Field blending**: STENCIL blends local density with oracle's global consensus
before computing gradients: `density + FIELD_BLEND * (global - density)`.
FIELD_BLEND = 0.15 default. One fma per cell, runs in SPIRV.

**3 dispatches per frame** in a single command buffer (batched frame dispatch).

### Network Oracle (implemented, tested)

```
                    ┌──────────────┐
                    │   Oracle     │  (Pi / any CPU)
                    │  trust mgr  │
                    │  field sum   │
                    │  regime cls  │
                    └──────┬───────┘
                      UDP │ 128KB field + 96B census
                   mcast  │ 128KB global field back
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
    │  GPU 0  │     │  GPU 1  │     │  GPU 2  │
    │ scatter │     │ scatter │     │ scatter │
    │ blend   │     │ blend   │     │ blend   │
    │ stencil │     │ stencil │     │ stencil │
    │ physics │     │ physics │     │ physics │
    └─────────┘     └─────────┘     └─────────┘

    Autonomous between census intervals.
    Oracle provides consensus field + spawn control.
    Trust-weighted: bad clients dampened in consensus.
```

Scatter-sum-broadcast: each GPU sends 128KB density grid, oracle sums
(trust-weighted), broadcasts global field via multicast. Each GPU blends
global into local before stencil. Particle count invisible to oracle.

### Performance at 29M (RTX 2060, f32)
```
SCATTER:  1.16 ms  (17%)
STENCIL:  0.005 ms (0.1%) — includes blend, still negligible
PHYSICS:  5.8 ms   (83%)    ← bandwidth-bound at 77% of 336 GB/s peak
TOTAL:    ~7.0 ms  (141-144 fps)
NET:      ~0 ms    (one census every 50-2000 frames, off critical path)
```

## Key Files

### Simulation
- `galaxy/galaxy_full.mcl` — the simulation (forward pipeline, packed phase, blend)
- `galaxy/galaxy_bench.mcl` — stripped benchmark version (no spawn/census/oracle)

### Compiler
- `mcl/ir_codegen.py` — C codegen: NET, field send/recv, PP-aware sync, blend
- `mcl/backends/spirv.py` — SPIRV: f32 types, right-shift, PP offset injection
- `mcl/parser.py` — NET "host:port" GPU n syntax
- `mcl/ast_nodes.py` — net_gpu_id field
- `mcl/ir_builder.py` — net_gpu_id propagation

### Runtime
- `mcl/runtime/vk_host.c` — Vulkan: xfer_cmd_buf, download_at/upload_at
- `mcl/runtime/ergo_vk.h` — API declarations
- `mcl/runtime/ergo_net.h` — UDP transport + field chunks + multicast

### Oracle
- `tools/ergo_oracle.c` — multi-client, trust-weighted consensus, field exchange

### Archive
- `archive/2026-04-26/` — pre-network snapshot
- `archive/2026-04-26-net/` — network oracle + field exchange milestone

### Build
```bash
# Oracle
cc -O2 -o ergo_oracle tools/ergo_oracle.c -lm

# GPU simulation
python -m mcl --target spirv --precision f32 --no-split -o galaxy_gpu galaxy/galaxy_full.mcl
ERGO_PROFILE=1 ./galaxy_gpu

# CPU test (loopback)
python -m mcl -o galaxy_cpu galaxy/galaxy_full.mcl
./ergo_oracle 4250 &
./galaxy_cpu
```


## Where To Go Next

### Phase 2: Tune for Cascade (Regime II)

Current omega ≈ 0.09 (PLATEAU). Need to reach ω > 0.4 for nova events.
Now with field blending, coherent structures couple across GPUs.

Parameters to tune:
- `OMEGA_GAIN = 2.0` → try 4.0 (density coupling strength)
- `OMEGA_RESPONSE = 0.5` → try 0.8 (tracking speed)
- `DENSITY_FORCE_SCALE = 0.01` → try 0.03 (pressure gradient strength)
- `FIELD_BLEND = 0.15` → regime-adaptive (high in COLD, low in WARMING)

### GPU hardware validation
- Run with ERGO_PROFILE=1, confirm pipeline timings hold with NET active
- Field recv/blend happens between frames, should not affect dispatch timing
- Test ping-pong correctness with structured initial conditions

### Multi-rate operator splitting
Field (scatter+stencil) doesn't need to update every frame at steady state.
Run scatter every N frames, physics every frame. FIELD_BLEND provides
inter-frame correction from oracle consensus.
