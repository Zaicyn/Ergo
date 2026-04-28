# Ergo Decay Systems Design

## The Principle

Decay is not destruction. It is energy redistribution mediated by
structure-exploiting processes. Nothing decays on its own — something
has to do the decaying. The rate depends on what agents are present
and whether they can access the structure.

> Decay rate = gradient × coupling × agents

No gradient → nothing wants it.
No coupling → nothing can reach it.
No agents → nothing acts on it.

## Three Decay Channels

### Channel 1: Radiative Decay (self-driven, no agents)

A hot body loses energy by existing. No interaction partner needed.
Rate depends only on the body's own state.

**Already implemented:** OMEGA_DECAY in the physics kernel.

```
DECAY := 1.0 - OMEGA_DECAY * DT
OMEGA := OMEGA * DECAY^4
```

Every particle loses OMEGA every frame regardless of neighbors.
This is the white dwarf cooling, the isotope decaying, the signal
fading. Pure self-dissipation.

**For crystal field:** PERSISTENCE property controls this channel.

```
! In STENCIL_GRID:
! Self-decay: crystal energy dissipates based on persistence
SELF_LOSS := (1.0 - GRID_PERSIST(I,J,K)) * RADIATIVE_RATE * DT
GRID_ENERGY(I,J,K) := MAX(GRID_ENERGY(I,J,K) - SELF_LOSS, 0.0)
```

High PERSISTENCE (dead star, rock) → almost no self-decay.
Low PERSISTENCE (dead cell, organic matter) → energy bleeds off even
without consumers. Thermal dissipation, chemical degradation.

### Channel 2: Agent-Driven Decay (requires live density)

The log rotting. Fungi consume lignin, bacteria consume cellulose.
Rate depends on: how much life is present × how accessible the
structure is × how much energy is available to extract.

**Not yet implemented.** This is the new channel.

```
! In STENCIL_GRID, after crystal field blend:
! Agent-driven erosion: live density consumes crystal energy
AGENTS := REAL(GRID_DENSITY(I,J,K))          ! how much life is here
ACCESS := GRID_ACCESS(I,J,K)                  ! can agents reach it
ENERGY := GRID_ENERGY(I,J,K)                  ! is there energy to extract
GRADIENT := MIN(ENERGY, AGENTS * ACCESS)      ! interaction strength

EROSION := GRADIENT * AGENT_DECAY_RATE * DT
GRID_ENERGY(I,J,K) := MAX(GRID_ENERGY(I,J,K) - EROSION, 0.0)
GRID_COHERENCE(I,J,K) := MAX(GRID_COHERENCE(I,J,K) - EROSION * COHERENCE_LOSS_RATE, 0.0)
```

The feedback loop: agents consume energy, which reduces the gradient,
which slows further consumption. Self-limiting — the log doesn't
vanish instantly, it decays in stages as each layer becomes accessible.

When GRID_COHERENCE reaches 0: the crystal entry is removed from the
grid. The structure has fully decomposed. The remaining energy (if any)
becomes available as ambient field density.

### Channel 3: Stress Decay (gradient-driven, structural)

A cliff erodes because gravity × weather exceeds cohesion. Ice cracks
under thermal cycling. A building crumbles from vibration. No biological
agent — the structure's own field gradients tear it apart.

```
! In STENCIL_GRID, after gradient computation:
! Stress decay: steep gradients erode coherence
GRAD_MAG := SQRT(GRID_GRAD_X(I,J,K)**2 + GRID_GRAD_Y(I,J,K)**2 + GRID_GRAD_Z(I,J,K)**2)
STRESS := MAX(GRAD_MAG - COHERENCE_THRESHOLD, 0.0)

IF GRID_CRYSTAL(I,J,K) > 0 THEN
  GRID_COHERENCE(I,J,K) := MAX(GRID_COHERENCE(I,J,K) - STRESS * STRESS_RATE * DT, 0.0)
ENDIF
```

High COHERENCE threshold (rock, metal) → resists stress unless extreme.
Low COHERENCE threshold (sand, loose soil) → erodes easily under any gradient.

This channel creates realistic erosion patterns: steep edges crumble,
flat regions persist. The gradient is the "weathering" force.

## Channel Interaction

The three channels are **additive and independent.** Each operates on
the same material properties but through different mechanisms:

```
Total coherence loss per frame =
    (1 - PERSIST) × RADIATIVE_RATE × DT           ! Channel 1: self-decay
  + AGENTS × ACCESS × ENERGY × AGENT_RATE × DT    ! Channel 2: consumption
  + max(GRAD_MAG - THRESHOLD, 0) × STRESS_RATE × DT ! Channel 3: stress
```

A dead star: Channel 1 ≈ 0 (high persist), Channel 2 = 0 (no agents),
Channel 3 ≈ 0 (gradients are smooth). Total decay ≈ 0. Permanent.

A rotting log: Channel 1 moderate (some chemical decay), Channel 2
dominant (fungi, bacteria), Channel 3 minor (gravity, rain). Fast decay.

A cliff face: Channel 1 ≈ 0 (rock is persistent), Channel 2 ≈ 0
(minimal biology), Channel 3 dominant (gravity + weathering). Slow erosion.

## The Cascade

Real decay isn't uniform — it's a cascade of phase transitions:

1. Agents attack accessible surface → ENERGY drops
2. Energy loss reduces coherence → ACCESS increases (structure opens up)
3. Higher access exposes more to agents → decay accelerates
4. Coherence drops below threshold → structure fragments
5. Fragments have even higher ACCESS → rapid final decomposition

This emerges naturally from the interaction terms:
- ENERGY loss → COHERENCE loss (structure weakens as energy extracted)
- COHERENCE loss → ACCESS increase (broken structure is more porous)
- ACCESS increase → faster agent erosion (positive feedback)

The cascade doesn't need to be coded explicitly. It's an emergent
property of the three coupled fields.

## New Constants

```
! Decay channel rates
PARAMETER REAL :: RADIATIVE_RATE = 0.0001    ! self-decay per frame
PARAMETER REAL :: AGENT_DECAY_RATE = 0.01    ! consumption per unit agent-access
PARAMETER REAL :: COHERENCE_LOSS_RATE = 0.5  ! coherence lost per unit energy consumed
PARAMETER REAL :: STRESS_RATE = 0.001        ! coherence lost per unit excess gradient
PARAMETER REAL :: COHERENCE_THRESHOLD = 0.1  ! gradient magnitude below which no stress decay

! Domain overrides (galaxy sim)
! AGENT_DECAY_RATE = 0.0   — nothing eats dead stars
! STRESS_RATE = 0.0        — stellar remnants don't erode
! RADIATIVE_RATE = 0.0     — already cold (OMEGA was 0 at crystallization)
```

## Domain Application

### Galaxy Simulation

All three decay channels are effectively zero:
- Dead stars have no accessible energy (OMEGA was near 0 at crystal time)
- No agents operate at stellar scale
- Gravitational gradients don't erode stellar mass

GRID_CRYSTAL stays permanent. Correct physics. No changes needed.

### Colony / Biome Simulation

Agent-driven decay is dominant:
- Dead cells lyse → high ACCESS, high ENERGY
- Live neighbors consume released nutrients
- Coherence drops as membrane disintegrates
- Final decomposition releases energy to ambient field

The cascade produces visible "rot" — a dead cell fades over hundreds
of frames as neighbors eat it, not in a single step.

### Geophysics / Material Science

Stress decay is dominant:
- Rock under gradient stress cracks
- Water (phase cycling) increases ACCESS
- Slow biological weathering (lichen, roots) adds Channel 2
- Erosion concentrates at high-gradient features (cliffs, ridges)

### Mixed Ecosystems

All three channels active simultaneously:
- Dead tree: Channel 1 (chemical degradation) + Channel 2 (fungi,
  bacteria, insects) + Channel 3 (gravity, wind)
- The relative rates determine the character of decay
- Tropical forest: Channel 2 dominates (fast biological turnover)
- Desert: Channel 1 dominates (slow chemical + UV degradation)
- Mountain: Channel 3 dominates (frost weathering + gravity)

## Implementation Priority

1. Add material property grids (see Ergo_Material_Properties_Design.md)
2. Implement Channel 1 (radiative) in STENCIL_GRID — single line
3. Implement Channel 2 (agent-driven) in STENCIL_GRID — 5 lines
4. Implement COHERENCE → ACCESS feedback (cascade) — 2 lines
5. Implement Channel 3 (stress) in STENCIL_GRID — 3 lines
6. Implement crystal removal when COHERENCE = 0 — 1 line
7. Domain-specific constant profiles (galaxy vs colony vs geo)
8. Tune rates empirically per domain (same approach as threshold tuning guide)

## Visualization

Decay state maps to render channels:
- COHERENCE → brightness (fading as structure breaks down)
- ENERGY_CONTENT → heat color (hot = has energy, cold = depleted)
- ACCESS → transparency or outline (sealed = opaque, porous = translucent)

In the point cloud renderer, crystallized particles could be colored
by their grid cell's COHERENCE instead of OMEGA — showing the decay
state of the structure they're part of.
