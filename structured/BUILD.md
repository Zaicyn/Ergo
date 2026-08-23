# Structured Build Order

Until Ergo gets USE/INCLUDE, the modules concatenate in dependency order.
All state declarations must come before any subroutine definitions.

## Assembly order:

```bash
cat constants.ergo    \  # Layer 1: parameters, LUTs (no state, no subs)
    fluid_state.ergo  \  # Layer 3: particle arrays, population vars
    waveguide_state.ergo \  # Layer 2: grid arrays, census state
    fluid_subs.ergo   \  # Layer 3: RNGF, BITCOUNT, SIM_INIT, SIM_SEED_SHELL, SIM_PHYSICS_STEP, SIM_SPAWN
    waveguide_subs.ergo \ # Layer 2: CLEAR_GRID, SCATTER_GRID, STENCIL_GRID
    census.ergo       \  # Readback: SIM_CENSUS_ADAPTIVE
    main.ergo         \  # Pipeline orchestration
    > galaxy_structured.ergo
```

## Build:

```bash
# Assemble
./structured/build.sh

# CPU
python -m core -o galaxy_cpu galaxy_structured.ergo

# GPU headless
python -m core --target spirv --precision f32 --no-split -o galaxy_gpu galaxy_structured.ergo

# GPU with render
python -m core --target spirv --precision f32 --no-split --render -o galaxy_gpu galaxy_structured.ergo
```

## Why this order:

1. Constants first — everything reads them
2. Fluid state (POS, VEL, FLAGS, OMEGA) — waveguide subs read these in scatter
3. Waveguide state (GRID_*) — physics reads these
4. Fluid subs — can reference all state
5. Waveguide subs — can reference fluid state + waveguide state
6. Census — reads both fluid and waveguide state
7. Main — calls everything
