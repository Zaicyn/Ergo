# Ergo Material Properties Design

## The Problem

GRID_CRYSTAL treats all frozen structure identically. A crystallized sun
and a dead bacterium produce the same +1 in the same grid. But they have
vastly different physical properties — mass, density, conductivity,
persistence, accessibility to agents. The simulation needs to distinguish
materials without exploding the grid into hundreds of channels.

## Core Concept: Material Classes

A material class is a small set of properties that determine how frozen
structure behaves. Not a full material database — just enough to
differentiate the important behaviors.

### Minimal Property Set

| Property | Type | Meaning | Range |
|---|---|---|---|
| COHERENCE | REAL | Structural integrity (1.0 = perfect crystal, 0.0 = dust) | 0.0 - 1.0 |
| ACCESSIBILITY | REAL | How exposed to agents (1.0 = fully accessible, 0.0 = sealed) | 0.0 - 1.0 |
| ENERGY_CONTENT | REAL | Stored free energy available to consumers | 0.0 - OMEGA_MAX |
| PERSISTENCE | REAL | Resistance to self-decay (radiative cooling etc.) | 0.0 - 1.0 |

### Example Material Profiles

| Material | COHERENCE | ACCESS | ENERGY | PERSIST | Real-world |
|---|---|---|---|---|---|
| Dead star | 1.0 | 0.0 | 0.0 | 1.0 | White dwarf, neutron star |
| Dead cell | 0.5 | 1.0 | 0.8 | 0.1 | Lysed bacterium |
| Bone/shell | 0.9 | 0.2 | 0.1 | 0.8 | Mineralized structure |
| Wood | 0.7 | 0.6 | 0.7 | 0.3 | Dead tree, log |
| Soil | 0.2 | 1.0 | 0.3 | 0.5 | Decomposed organic matter |
| Rock | 0.95 | 0.1 | 0.0 | 0.95 | Granite, basite |
| Ice | 0.6 | 0.3 | 0.0 | 0.4 | Phase-dependent |

### Why These Four

- **COHERENCE** determines when structure physically fragments (falls apart)
- **ACCESSIBILITY** determines how fast agents can interact (surface area, porosity)
- **ENERGY_CONTENT** determines whether anything WANTS to consume it (gradient)
- **PERSISTENCE** determines self-decay rate without agents (radiative, chemical)

GPT's key insight: decay only happens where gradients exist AND coupling
pathways are open. ENERGY_CONTENT is the gradient. ACCESSIBILITY is the
coupling. No gradient or no access = no agent-driven decay.

## Grid Representation

### Option A: Separate grids per property (simple, expensive)

```
STATIC REAL :: GRID_COHERENCE(GRID_SIZE, GRID_SIZE, GRID_SIZE)
STATIC REAL :: GRID_ACCESS(GRID_SIZE, GRID_SIZE, GRID_SIZE)
STATIC REAL :: GRID_ENERGY(GRID_SIZE, GRID_SIZE, GRID_SIZE)
STATIC REAL :: GRID_PERSIST(GRID_SIZE, GRID_SIZE, GRID_SIZE)
```

4 grids × 32^3 × 4 bytes = 512 KB. Negligible compared to particle arrays.
Simple, readable, each grid updated independently.

### Option B: Packed material ID (compact, lookup-based)

```
STATIC INTEGER :: GRID_MATERIAL(GRID_SIZE, GRID_SIZE, GRID_SIZE)
```

Material ID indexes into a static LUT of properties. 1 grid instead of 4.
But limits you to predefined materials — can't blend or interpolate.

### Recommendation: Option A for now

512 KB is nothing. Separate grids compose cleanly with existing stencil
operations. Blending happens naturally (two materials in same cell =
weighted average of properties). Switch to packed IDs only if the grid
count becomes a problem.

## How Materials Get Set

When a particle crystallizes (PFLAG_CRYSTAL set in physics kernel),
the scatter pass deposits material properties based on the particle's
state at death:

```
! In SCATTER_GRID, crystal banking section:
IF IAND(FLAGS(I), PFLAG_CRYSTAL) ≠ 0 THEN
  IF IAND(FLAGS(I), PFLAG_BANKED) = 0 THEN
    CI := CLAMP(INT(POS_X(I) / CELL_SIZE) + GRID_HALF, 1, GRID_SIZE)
    CJ := CLAMP(INT(POS_Y(I) / CELL_SIZE) + GRID_HALF, 1, GRID_SIZE)
    CK := CLAMP(INT(POS_Z(I) / CELL_SIZE) + GRID_HALF, 1, GRID_SIZE)
    GRID_CRYSTAL(CI, CJ, CK) := GRID_CRYSTAL(CI, CJ, CK) + 1

    ! Material properties from particle state at death
    GRID_COHERENCE(CI, CJ, CK) := GRID_COHERENCE(CI, CJ, CK) + 1.0
    GRID_ENERGY(CI, CJ, CK) := GRID_ENERGY(CI, CJ, CK) + OMEGA
    GRID_ACCESS(CI, CJ, CK) := GRID_ACCESS(CI, CJ, CK) + ACCESS_FROM_MODE(FMODE)

    FLAGS(I) := IOR(FLAGS(I), PFLAG_BANKED)
  ENDIF
  CYCLE
ENDIF
```

ACCESS_FROM_MODE: COAST particles are more accessible (exposed, drifting),
ACTIVE particles less so (embedded in coupled structure).

## Interaction with Decay System

Material properties feed directly into the decay system
(see Ergo_Decay_Systems_Design.md):

- Decay rate = f(ENERGY_CONTENT, ACCESSIBILITY, live_density)
- COHERENCE decreases as decay proceeds
- When COHERENCE reaches 0, the crystal entry is removed (structure gone)
- PERSISTENCE governs self-decay (no agents needed)

## Interaction with Physics

Live particles respond to material properties through the waveguide:

- High ENERGY_CONTENT cells attract consumers (density siphon pulls toward food)
- High COHERENCE cells resist deformation (gradient is stable, not noisy)
- Low ACCESSIBILITY cells are effectively walls (density can't penetrate)

These couple through existing mechanisms — GRID_DENSITY for attraction,
GRID_GRAD for forces. The material grids modulate the coupling strength.

## Domain Specificity

The material property values are domain-specific:

- Galaxy sim: all crystals are dead stars (COHERENCE=1, ACCESS=0, ENERGY=0, PERSIST=1)
- Colony sim: dead cells have high ENERGY, high ACCESS, low PERSIST
- Ecosystem: mixed — rock substrate vs organic matter vs water

The grid structure is the same. The constants change per domain.
This could be a configuration file or PARAMETER block per simulation.

## Implementation Priority

1. Add the 4 material grids to waveguide_state.ergo (512 KB total)
2. Set material properties at crystal banking time in scatter
3. Wire into decay system (separate design doc)
4. Modulate physics coupling based on material properties
5. Visualize: render material type as color channel
