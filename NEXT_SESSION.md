# Next Session: Material System Implementation

## What's Done

Full ring coupling + crystal field operational at 30M@60-74fps:

- **RING_PREV / RING_NEXT / RING_SHIFT** — warp shuffle intrinsics
- **SORT_BY_GEN** — compiler-generated counting sort, pointer swap
- **Phase lock (15.5)** + **Metabolic exchange (15.6)** + **Winding correction (15.7)**
- **Hopfion spillover (15.8)** — butterfly OMEGA reduction, threshold decay
- **Crystal field** — GRID_CRYSTAL permanent density, PFLAG_BANKED
- **DO WHILE** — complete loop algebra
- **VSCodium extension** — syntax highlighting, LSP diagnostics, hover, GPU PERF hints
- **File extension** — .ergo (not .mcl)

## The Task: Archetype + Delta Material System

Design doc: Spec/Ergo_Material_Properties_Design.md

One integer per grid cell. 8-bit archetype ID (LUT lookup) + 24-bit
packed signed nibble deltas. Pristine cells (STATE=0) are a single
LUT lookup — zero delta arithmetic.

### Step 1: Archetype LUT (constants.ergo)

Add after the existing LUTs (FLOW_MODE, TANGENT, etc.):

```
! ── Material archetype LUT ────────────────────────────────
! Each archetype defines baseline properties (nibble scale 0-15).
! ELEMENT_ID indexes into these tables.
PARAMETER INTEGER :: MAT_COUNT = 16

STATIC INTEGER :: MAT_COHERENCE(MAT_COUNT)
STATIC INTEGER :: MAT_ENERGY(MAT_COUNT)
STATIC INTEGER :: MAT_MOBILITY(MAT_COUNT)
STATIC INTEGER :: MAT_REACTIVITY(MAT_COUNT)
STATIC INTEGER :: MAT_PERSISTENCE(MAT_COUNT)
STATIC REAL :: MAT_MASS(MAT_COUNT)

! ID 0: VOID (empty space)
DATA MAT_COHERENCE(1)  /  0 /
DATA MAT_ENERGY(1)     /  0 /
DATA MAT_MOBILITY(1)   / 15 /
DATA MAT_REACTIVITY(1) /  0 /
DATA MAT_PERSISTENCE(1)/ 15 /
DATA MAT_MASS(1)       / 0.0 /

! ID 1: STELLAR_DEAD (white dwarf, neutron star)
DATA MAT_COHERENCE(2)  / 15 /
DATA MAT_ENERGY(2)     /  0 /
DATA MAT_MOBILITY(2)   /  0 /
DATA MAT_REACTIVITY(2) /  0 /
DATA MAT_PERSISTENCE(2)/ 15 /
DATA MAT_MASS(2)       / 100.0 /

! ID 2: ROCK
DATA MAT_COHERENCE(3)  / 14 /
DATA MAT_ENERGY(3)     /  0 /
DATA MAT_MOBILITY(3)   /  1 /
DATA MAT_REACTIVITY(3) /  1 /
DATA MAT_PERSISTENCE(3)/ 14 /
DATA MAT_MASS(3)       / 2.5 /

! ... more archetypes as needed per domain
```

Note: DATA uses 1-based indexing. ELEMENT_ID 0 maps to index 1.

Domain parameter:
```
PARAMETER INTEGER :: CRYSTAL_ARCHETYPE = 1   ! galaxy: STELLAR_DEAD
```

### Step 2: GRID_MATERIAL grid (waveguide_state.ergo)

Add after GRID_CRYSTAL:

```
! ── Material state (archetype + delta, never cleared) ─────
! Bits 31-24: ELEMENT_ID (archetype index)
! Bits 23-20: COHERENCE delta (signed nibble)
! Bits 19-16: ENERGY delta (signed nibble)
! Bits 15-12: MOBILITY delta (signed nibble)
! Bits 11-8:  REACTIVITY delta (signed nibble)
! Bits 7-4:   PERSISTENCE delta (signed nibble)
! Bits 3-0:   FLAGS (decaying, visited, boundary, reserved)
STATIC INTEGER :: GRID_MATERIAL(GRID_SIZE, GRID_SIZE, GRID_SIZE)
```

### Step 3: Set material at crystal banking (waveguide_subs.ergo)

In SCATTER_GRID, inside the crystal banking block (after GRID_CRYSTAL
deposit, before FLAGS set to PFLAG_BANKED):

```
! Set material: archetype + energy delta from OMEGA at death
ENERGY_DELTA := CLAMP(INT(OMEGA_NAT(I) * 15.0 / OMEGA_MAX), 0, 15)
GRID_MATERIAL(CI, CJ, CK) := IOR( &
  ISHFT(CRYSTAL_ARCHETYPE, 24), &
  ISHFT(ENERGY_DELTA, 16))
```

This sets the archetype from the domain parameter and packs the
particle's OMEGA at death into the ENERGY delta. All other deltas
start at 0 (pristine).

### Step 4: Unpack in STENCIL_GRID (waveguide_subs.ergo)

After the crystal field blend (`GRID_DENSITY += GRID_CRYSTAL`) and
before gradient computation, unpack material properties for cells
that have crystal content:

```
! Material properties (only for cells with crystal content)
IF GRID_CRYSTAL(I, J, K) > 0 THEN
  MAT_RAW := GRID_MATERIAL(I, J, K)
  ELEM := IAND(ISHFT(MAT_RAW, -24), 255) + 1  ! 1-based LUT index

  ! Fast path: pristine (no deltas)
  IF IAND(MAT_RAW, 16777215) = 0 THEN
    M_COHER := MAT_COHERENCE(ELEM)
    M_ENERG := MAT_ENERGY(ELEM)
    M_MOBIL := MAT_MOBILITY(ELEM)
    M_REACT := MAT_REACTIVITY(ELEM)
    M_PERST := MAT_PERSISTENCE(ELEM)
  ELSE
    ! Unpack signed nibble deltas
    M_COHER := MAT_COHERENCE(ELEM) + NIBBLE_SIGNED(ISHFT(MAT_RAW, -20))
    M_ENERG := MAT_ENERGY(ELEM) + NIBBLE_SIGNED(ISHFT(MAT_RAW, -16))
    M_MOBIL := MAT_MOBILITY(ELEM) + NIBBLE_SIGNED(ISHFT(MAT_RAW, -12))
    M_REACT := MAT_REACTIVITY(ELEM) + NIBBLE_SIGNED(ISHFT(MAT_RAW, -8))
    M_PERST := MAT_PERSISTENCE(ELEM) + NIBBLE_SIGNED(ISHFT(MAT_RAW, -4))
  ENDIF

  ! Clamp to valid range
  M_COHER := CLAMP(M_COHER, 0, 15)
  M_ENERG := CLAMP(M_ENERG, 0, 15)
  M_MOBIL := CLAMP(M_MOBIL, 0, 15)
  M_REACT := CLAMP(M_REACT, 0, 15)
  M_PERST := CLAMP(M_PERST, 0, 15)
ENDIF
```

NIBBLE_SIGNED helper (add to fluid_subs.ergo or inline):
```
INTEGER FUNCTION NIBBLE_SIGNED(V)
  INTEGER :: V, N
  N := IAND(V, 15)
  IF N > 7 THEN
    N := N - 16
  ENDIF
  NIBBLE_SIGNED := N
  RETURN NIBBLE_SIGNED
END
```

### Step 5: Decay channels in STENCIL_GRID (waveguide_subs.ergo)

After material unpacking, apply the three decay channels:

```
IF GRID_CRYSTAL(I, J, K) > 0 THEN
  ! Channel 1: Radiative (self-decay)
  SELF_LOSS := (15 - M_PERST) * RADIATIVE_RATE

  ! Channel 2: Agent-driven (live density consumes crystal)
  AGENTS := REAL(GRID_DENSITY(I, J, K))
  AGENT_LOSS := AGENTS * REAL(M_REACT) * REAL(M_ENERG) * AGENT_DECAY_RATE

  ! Channel 3: Stress (gradient tears structure)
  GRAD_MAG := SQRT(GRID_GRAD_X(I,J,K)**2 + GRID_GRAD_Y(I,J,K)**2 + GRID_GRAD_Z(I,J,K)**2)
  STRESS_LOSS := MAX(GRAD_MAG - REAL(M_COHER), 0.0) * STRESS_RATE

  ! Total coherence loss
  TOTAL_LOSS := SELF_LOSS + AGENT_LOSS + STRESS_LOSS

  ! Update deltas (write back to GRID_MATERIAL)
  IF TOTAL_LOSS > 0.1 THEN
    NEW_COH := MAX(M_COHER - INT(TOTAL_LOSS), 0)
    NEW_ENR := MAX(M_ENERG - INT(AGENT_LOSS), 0)
    NEW_MOB := MIN(M_MOBIL + INT(TOTAL_LOSS * 0.5), 15)
    ! Pack deltas back
    COH_D := CLAMP(NEW_COH - MAT_COHERENCE(ELEM), -8, 7)
    ENR_D := CLAMP(NEW_ENR - MAT_ENERGY(ELEM), -8, 7)
    MOB_D := CLAMP(NEW_MOB - MAT_MOBILITY(ELEM), -8, 7)
    ! Encode signed nibbles (negative → add 16)
    IF COH_D < 0 THEN
      COH_D := COH_D + 16
    ENDIF
    IF ENR_D < 0 THEN
      ENR_D := ENR_D + 16
    ENDIF
    IF MOB_D < 0 THEN
      MOB_D := MOB_D + 16
    ENDIF
    GRID_MATERIAL(I,J,K) := IOR(IOR(IOR( &
      ISHFT(IAND(ISHFT(MAT_RAW, -24), 255), 24), &
      ISHFT(IAND(COH_D, 15), 20)), &
      ISHFT(IAND(ENR_D, 15), 16)), &
      ISHFT(IAND(MOB_D, 15), 12))
  ENDIF

  ! Crystal removal: coherence gone = structure dissolved
  IF NEW_COH ≤ 0 THEN
    GRID_CRYSTAL(I, J, K) := MAX(GRID_CRYSTAL(I, J, K) - 1, 0)
    GRID_MATERIAL(I, J, K) := 0
  ENDIF
ENDIF
```

### Step 6: New constants (constants.ergo)

```
! ── Decay channel rates ───────────────────────────────────
PARAMETER REAL :: RADIATIVE_RATE = 0.0001
PARAMETER REAL :: AGENT_DECAY_RATE = 0.01
PARAMETER REAL :: STRESS_RATE = 0.001

! ── Domain: galaxy (dead stars don't decay) ───────────────
! Override for galaxy: all rates effectively zero because
! STELLAR_DEAD archetype has REACT=0, ENERGY=0, PERSIST=15.
! No need to set rates to zero — the material properties
! naturally produce zero decay.
```

### Step 7: New variable declarations

In STENCIL_GRID, add local variables:
```
INTEGER :: MAT_RAW, ELEM
INTEGER :: M_COHER, M_ENERG, M_MOBIL, M_REACT, M_PERST
REAL :: SELF_LOSS, AGENT_LOSS, STRESS_LOSS, TOTAL_LOSS, GRAD_MAG
INTEGER :: NEW_COH, NEW_ENR, NEW_MOB
INTEGER :: COH_D, ENR_D, MOB_D
```

### Verification

1. Galaxy sim: GRID_MATERIAL should be all STELLAR_DEAD with ENERGY
   delta = 0 (OMEGA was near 0 at crystallization). Decay channels
   should produce zero loss. GRID_CRYSTAL unchanged from current behavior.

2. Test material decay: temporarily set CRYSTAL_ARCHETYPE to DEAD_CELL
   (ID 5) and AGENT_DECAY_RATE to 0.1. Crystals should visibly erode
   where live density is high.

3. Performance: stencil processes 32^3 = 32768 cells. The material
   unpacking + decay adds ~20 ops per cell with crystal content.
   At typical crystal fractions (<10% of cells), this is <3000 extra
   ops per frame. Negligible.

## Build

```bash
./structured/build.sh
sed '/VERIFY/,/4250/d' galaxy_structured.ergo > /tmp/nonet.ergo
python -m mcl --target spirv --precision f32 --no-split --render -N 29000000 -M 30000000 -o galaxy_render /tmp/nonet.ergo
```

## Key Files to Modify

```
structured/
  constants.ergo       — MAT_* LUTs, CRYSTAL_ARCHETYPE, decay rates
  waveguide_state.ergo — GRID_MATERIAL declaration
  waveguide_subs.ergo  — scatter (set material), stencil (unpack + decay)
  fluid_subs.ergo      — NIBBLE_SIGNED helper function
```
