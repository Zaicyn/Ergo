# Ergo Material Properties Design

## The Problem

GRID_CRYSTAL treats all frozen structure identically. A crystallized sun
and a dead bacterium produce the same +1 in the same grid. But they have
vastly different physical properties — mass, coherence, energy content,
reactivity. The simulation needs to distinguish materials without
exploding the grid into hundreds of channels.

## Core Concept: Archetype + Delta

Inspired by the sq2core allocator pattern (seed vertices + imprint
perturbation) and condensed matter physics (immutable lattice + local
excitations).

### Two layers:

**ELEMENT_ID** (8 bits) — archetype. Indexes into a static LUT of
baseline properties. Immutable. Set once when structure crystallizes.
A granite cliff is a million cells all with ELEMENT_ID = GRANITE.

**STATE** (24 bits) — local delta from baseline. Packed nibbles encoding
deviations from the archetype. A pristine cell has STATE = 0 (zero delta,
pure archetype). Only damaged/heated/weathered cells have nonzero STATE.

**One integer per grid cell:**

```
STATIC INTEGER :: GRID_MATERIAL(GRID_SIZE, GRID_SIZE, GRID_SIZE)
```

128 KB. Replaces the 512 KB four-grid approach. Lazy calculation:
95%+ of frozen cells are pristine → single LUT lookup, no unpacking.

## Encoding

```
Bits 31-24: ELEMENT_ID (8 bits, 256 archetypes)
Bits 23-20: COHERENCE delta  (4 bits, signed -8..+7 from baseline)
Bits 19-16: ENERGY delta     (4 bits, signed -8..+7 from baseline)
Bits 15-12: MOBILITY delta   (4 bits, signed -8..+7 from baseline)
Bits 11-8:  REACTIVITY delta (4 bits, signed -8..+7 from baseline)
Bits  7-4:  PERSISTENCE delta(4 bits, signed -8..+7 from baseline)
Bits  3-0:  FLAGS            (4 bits: decaying, visited, boundary, reserved)
```

Unpacking:
```
ELEM := IAND(ISHFT(GRID_MATERIAL(I,J,K), -24), 255)
COH_DELTA := IAND(ISHFT(GRID_MATERIAL(I,J,K), -20), 15)
! Sign extend: if > 7, subtract 16
IF COH_DELTA > 7 THEN
  COH_DELTA := COH_DELTA - 16
ENDIF
COHERENCE := MAT_COHERENCE(ELEM) + COH_DELTA
```

Fast path (pristine, STATE = 0):
```
IF IAND(GRID_MATERIAL(I,J,K), 16777215) = 0 THEN
  ! Pure archetype — single LUT lookup, no delta unpacking
  ELEM := ISHFT(GRID_MATERIAL(I,J,K), -24)
  COHERENCE := MAT_COHERENCE(ELEM)
  ENERGY := MAT_ENERGY(ELEM)
  ...
ENDIF
```

The branch predictor loves this — vast majority of frozen cells are
pristine, one code path, zero delta arithmetic.

## Property Set

Six properties per material. No PHASE stored — phase is derived from
COHERENCE × ENERGY × MOBILITY (continuous phase transitions emerge
from field dynamics, not categorical labels).

| Property | Nibble range | Meaning |
|---|---|---|
| COHERENCE | 0-15 | Structural integrity (15 = diamond, 0 = dust) |
| ENERGY | 0-15 | Stored free energy (15 = fuel, 0 = inert) |
| MOBILITY | 0-15 | How freely matter can rearrange (15 = gas, 0 = frozen) |
| REACTIVITY | 0-15 | How readily it couples to agents (15 = explosive, 0 = noble) |
| PERSISTENCE | 0-15 | Self-decay resistance (15 = eternal, 0 = unstable) |
| MASS | (in archetype LUT) | Gravitational contribution per unit |

MASS is in the archetype LUT only — it doesn't change locally.
A weathered rock is still rock-mass. Only the surface properties change.

## Emergent Phase

Phase is not stored. It emerges from three fields:

| Coherence | Energy | Mobility | Emergent behavior |
|---|---|---|---|
| High | Low | Low | Crystal / rock |
| Medium | Medium | Medium | Liquid |
| Low | High | High | Gas |
| Very low | Extreme | Extreme | Plasma |
| High | High | Low | Stressed solid |
| Medium | Low | Very low | Glass |
| Low | Low | Low | Powder / dust |
| Medium | High | Low | Foam / bubbling |

Continuous transitions between these states happen naturally as the
fields evolve through decay channels. No discrete phase boundaries —
a melting solid passes through stressed → softened → viscous → flowing
as COHERENCE drops and MOBILITY rises.

## Archetype LUT

Static lookup table. Set once at simulation init. ~256 entries max.

```
! Archetype baseline properties (nibble scale 0-15)
STATIC INTEGER :: MAT_COHERENCE(256)
STATIC INTEGER :: MAT_ENERGY(256)
STATIC INTEGER :: MAT_MOBILITY(256)
STATIC INTEGER :: MAT_REACTIVITY(256)
STATIC INTEGER :: MAT_PERSISTENCE(256)
STATIC REAL :: MAT_MASS(256)

! Example archetypes
! ID  Name        COH  ENR  MOB  REA  PER  MASS
!  0  VOID          0    0   15    0   15   0.0
!  1  STELLAR_DEAD 15    0    0    0   15  100.0
!  2  ROCK         14    0    1    1   14   2.5
!  3  ICE           9    0    3    2    6   0.9
!  4  WOOD         10   11    1    8    4   0.6
!  5  DEAD_CELL     7   12    3   12    2   1.0
!  6  SOIL          3    5    4    6    8   1.3
!  7  WATER         1    1   12    3   10   1.0
!  8  ORGANIC_MIX   5    8    5   10    3   0.8
!  9  MINERAL      13    0    0    2   13   3.0
! 10  METAL        15    0    0    4   15   7.8
```

Domain-specific: galaxy sim uses only ID 0 (void) and 1 (stellar_dead).
Colony sim uses IDs 0, 5, 6, 7, 8. Ecosystem uses the full range.
Users can define their own archetypes via DATA statements.

## How Materials Get Set

When a particle crystallizes, scatter deposits the archetype based on
simulation domain + particle state at death:

```
! In SCATTER_GRID, crystal banking section:
IF IAND(FLAGS(I), PFLAG_CRYSTAL) ≠ 0 THEN
  IF IAND(FLAGS(I), PFLAG_BANKED) = 0 THEN
    CI := CLAMP(INT(POS_X(I) / CELL_SIZE) + GRID_HALF, 1, GRID_SIZE)
    CJ := CLAMP(INT(POS_Y(I) / CELL_SIZE) + GRID_HALF, 1, GRID_SIZE)
    CK := CLAMP(INT(POS_Z(I) / CELL_SIZE) + GRID_HALF, 1, GRID_SIZE)
    GRID_CRYSTAL(CI, CJ, CK) := GRID_CRYSTAL(CI, CJ, CK) + 1

    ! Set material: archetype from domain, state = 0 (pristine)
    ! ENERGY delta from particle OMEGA at death
    ENERGY_DELTA := CLAMP(INT(OMEGA * 15.0 / OMEGA_MAX), 0, 15)
    GRID_MATERIAL(CI, CJ, CK) := IOR( &
      ISHFT(CRYSTAL_ARCHETYPE, 24), &
      ISHFT(ENERGY_DELTA, 16))

    FLAGS(I) := IOR(FLAGS(I), PFLAG_BANKED)
  ENDIF
  CYCLE
ENDIF
```

CRYSTAL_ARCHETYPE is a simulation-level PARAMETER:
- Galaxy: CRYSTAL_ARCHETYPE = 1 (STELLAR_DEAD)
- Colony: CRYSTAL_ARCHETYPE = 5 (DEAD_CELL)

## Interaction with Decay System

The decay channels (see Ergo_Decay_Systems_Design.md) read from the
archetype + delta to get effective properties:

```
ELEM := IAND(ISHFT(GRID_MATERIAL(I,J,K), -24), 255)
COHERENCE := MAT_COHERENCE(ELEM) + COH_DELTA
ENERGY := MAT_ENERGY(ELEM) + ENR_DELTA
MOBILITY := MAT_MOBILITY(ELEM) + MOB_DELTA
```

As decay proceeds, deltas get written back:
- Agent consumption → ENERGY delta decreases
- Structural damage → COHERENCE delta decreases
- Weathering → MOBILITY delta increases (structure loosens)

When effective COHERENCE reaches 0: crystal entry removed (structure gone).
The deltas encode the decay history — how far this cell has drifted from
its pristine archetype.

## Interaction with Physics

Live particles respond to material properties through the waveguide:

- High ENERGY cells attract consumers (density siphon toward food)
- High COHERENCE cells resist deformation (stable gradient)
- High MOBILITY cells allow flow (reduced field resistance)
- Low REACTIVITY cells are inert (no coupling to agents)

These couple through existing mechanisms — GRID_DENSITY for attraction,
GRID_GRAD for forces. Material properties modulate coupling strength.

## Memory Footprint

| Component | Size | Notes |
|---|---|---|
| GRID_MATERIAL | 128 KB | 32^3 × 4 bytes, one integer per cell |
| Archetype LUTs | ~6 KB | 6 arrays × 256 × 4 bytes |
| Total | ~134 KB | vs 512 KB for four separate grids |

Plus GRID_CRYSTAL stays as-is (128 KB integer count).
Total material system: 262 KB. Negligible.

## Domain Profiles

Each simulation domain sets CRYSTAL_ARCHETYPE and populates the
archetype LUT:

```
! Galaxy profile
PARAMETER INTEGER :: CRYSTAL_ARCHETYPE = 1
DATA MAT_COHERENCE(1) / 15 /   ! stellar dead: maximum coherence
DATA MAT_ENERGY(1) / 0 /       ! no free energy
DATA MAT_MOBILITY(1) / 0 /     ! completely frozen
DATA MAT_REACTIVITY(1) / 0 /   ! nothing interacts
DATA MAT_PERSISTENCE(1) / 15 / ! eternal
DATA MAT_MASS(1) / 100.0 /     ! stellar mass

! Colony profile
PARAMETER INTEGER :: CRYSTAL_ARCHETYPE = 5
DATA MAT_COHERENCE(5) / 7 /    ! dead cell: moderate structure
DATA MAT_ENERGY(5) / 12 /      ! high free energy (nutrients)
DATA MAT_MOBILITY(5) / 3 /     ! slightly mobile (lysis)
DATA MAT_REACTIVITY(5) / 12 /  ! highly reactive (biodegradable)
DATA MAT_PERSISTENCE(5) / 2 /  ! decays quickly
DATA MAT_MASS(5) / 1.0 /       ! unit mass
```

## Implementation Priority

1. Define archetype LUT structure (constants.ergo, ~30 lines)
2. Add GRID_MATERIAL to waveguide_state.ergo (1 line, 128 KB)
3. Set GRID_MATERIAL at crystal banking time in scatter (5 lines)
4. Unpack in STENCIL_GRID for decay channel input (10 lines)
5. Write delta back after decay modifies properties (5 lines)
6. Wire material properties into physics coupling (5 lines)
7. Domain-specific archetype profiles
8. Visualize: material archetype → color in renderer
