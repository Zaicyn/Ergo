# Colony Sim GPU Plan

*2026-04-23*

## Current State

The colony sim renders live in a Vulkan window but the physics and
diffusion loops run on CPU. Only the init kernel (kernel_0) runs on GPU.

The physics loop (line 120) can't split because per-iteration locals
like `WILEAK`, `IPUMP`, `WIK`, `WIH` are computed in the extractable
prefix but read by the structural suffix (PRNG, mesh damage, membrane
potential update, death check, division). The compiler correctly
rejects this split.

The diffusion loop (line 300) can't split because `DFLUX`, `NI`, `NX`
cross the same boundary, and the suffix has a nested neighbor loop.

## Strategy: Separate Passes

The physics loop mixes three concerns in one DO loop:

1. **Electrochemistry** (items 0-39): Nernst potentials, leak currents,
   pump, synthase, ATP decay, mesh decay — pure data-parallel, no
   cross-iteration deps. This is the flow prefix.

2. **Environmental noise** (items 40-50): PRNG (ISEED accumulator),
   mesh damage, mesh repair — sequential because of ISEED.

3. **Membrane update + structural** (items 50-70): CPSI/ion update
   (depends on WILEAK/IPUMP from #1), death check, division with
   neighbor search.

The fix: split the source into separate passes so each loop is
independently extractable.

### Pass 1: Electrochemistry kernel (GPU)
```
DO I = 1, NCELLS
  IF CALIVE(I) ≠ 1 THEN CYCLE
  ! Nernst, leak, pump, synthase, ATP decay, mesh decay
  ! Write results to temporary arrays: WILEAK_BUF(I), WIK_BUF(I), etc.
  ! Also write updated CATP, CHIN, CMSH in place
ENDDO
```
Add buffer arrays `WILEAK_BUF(2048)`, `WIK_BUF(2048)`, `WIH_BUF(2048)`,
`IPUMP_BUF(2048)` to store per-cell intermediate results. This makes
the locals into arrays — extractable, no boundary crossing.

### Pass 2: Environmental noise (CPU)
```
DO I = 1, NCELLS
  ! ISEED PRNG, mesh damage, mesh repair
ENDDO
```
Stays on CPU. ISEED is a sequential accumulator.

### Pass 3: Membrane update (GPU)
```
DO I = 1, NCELLS
  IF CALIVE(I) ≠ 1 THEN CYCLE
  ITOTAL = WILEAK_BUF(I) + IPUMP_BUF(I)
  DPSIDT = -ITOTAL / CM
  CPSI(I) = CPSI(I) + DPSIDT
  ! clamp, ion update using WIK_BUF(I), WIH_BUF(I)
ENDDO
```
Reads from the buffer arrays. No cross-iteration deps. Extractable.

### Pass 4: Death + division (CPU)
```
DO I = 1, NCELLS
  ! death check, division with neighbor search
ENDDO
```
Stays on CPU. Division has NEMPTY accumulator and neighbor loop.

### Pass 5: Diffusion (partially GPU)
The right/down neighbor diffusion is extractable if the boundary
leak loop is a separate pass. Split into:
- Pass 5a: right+down neighbor diffusion (GPU, no cross-iteration if
  we accept the slight ordering dependency)
- Pass 5b: boundary leak to environment (CPU, nested neighbor loop)

## What to Change

1. **buc_colony_gpu.ergo**: Restructure the physics DO loop into
   separate passes. Add `WILEAK_BUF`, `WIK_BUF`, `WIH_BUF`,
   `IPUMP_BUF` arrays. Move membrane update to its own loop.

2. **No compiler changes needed.** The extraction pass will
   naturally see the separated loops as extractable.

3. Verify with `--kernel-report` that passes 1 and 3 extract.

4. Test numerical correctness by comparing CPU vs GPU output
   for a few frames.

## Expected Result

3-4 GPU kernels (init, electrochemistry, membrane update, maybe
diffusion) + 2-3 CPU loops (noise, death/division, boundary leak).
The heavy physics math runs on GPU, the sequential/structural
work stays on CPU.
