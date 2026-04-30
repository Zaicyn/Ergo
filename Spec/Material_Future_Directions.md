# Material System — Future Directions

Captured from Grok's review of the archetype + delta design (2026-04-29).
These are not immediate tasks — they're architectural notes for when the
resonance database and multi-domain simulations are ready.

## 1. Resonance → Archetype Selection at Quench

Currently: crystallization uses a flat `CRYSTAL_ARCHETYPE` parameter.
Every crystal in a domain is the same material.

Future: when a hopfion/soliton cluster reaches crystallization threshold,
compute the local harmonic signature and match against a resonance library
to select the appropriate ELEMENT_ID dynamically.

```
! At crystallization time (in scatter, crystal banking):
ELEM_ID := RESONANCE_MATCH(local_harmonics, particle_state)
ENERGY_DELTA := CLAMP(INT(OMEGA * 15.0 / OMEGA_MAX), 0, 15)
COHERENCE_DELTA := CLAMP(INT(MATCH_QUALITY * 7.0), -8, 7)
GRID_MATERIAL(CI,CJ,CK) := IOR(ISHFT(ELEM_ID, 24), ...)
```

The match quality score sets initial COHERENCE — clean phase lock at
quench → high coherence crystal. Noisy quench → lower starting
coherence → decays faster. Natural "quality of crystallization."

## 2. Delta Precision

Current: 4 bits per property (±7 range). Fine for galaxy sim where
dead stars don't decay. May be too coarse for biological/chemical
contexts where energy gradients need finer resolution.

Options:
- **Keep 24-bit STATE** — acceptable for current scale
- **Split to two 32-bit ints** (256 KB total) — 8 bits per delta,
  ±127 range. Only if biological sim needs it.
- **Floating-point overlay** — for cells that need full precision,
  store a secondary float grid indexed by the FLAGS nibble

No action needed until a concrete simulation hits the resolution limit.

## 3. Resonance LUT Format

The material resonance library needs a compact GPU-queryable format.
Each archetype has a harmonic signature that the quench code matches
against. Options:

- **Fixed-size signature** — 8 floats per archetype (harmonic
  coefficients). 256 archetypes × 8 × 4 bytes = 8 KB. Trivially
  fits in push constants or small SSBO.
- **Spectral hash** — compress the signature to a 32-bit integer
  for fast comparison. Collisions acceptable since there are only
  16-256 archetypes.

## 4. Multi-Material Interfaces

When adjacent grid cells have different archetypes, the boundary
behavior matters:

- **Gradient blending** — interpolate properties across the boundary.
  Natural for liquids/gases, wrong for solid/solid interfaces.
- **Sharp interfaces** — maintain distinct properties. Correct for
  crystal boundaries. Needs boundary detection in stencil.
- **Reaction zones** — cells where two materials interact may produce
  a third (chemical reactions, alloys, biological processes).

This is a Phase 3+ concern. Current single-archetype-per-domain
avoids the problem entirely.

## 5. Particle-Field Coupling Modulation

How material properties affect live particles (not yet implemented):

- **High COHERENCE cells** — stable gradients, steering is predictable.
  Particles near high-coherence structure orbit cleanly.
- **High MOBILITY cells** — field is noisy, gradient fluctuates.
  Particles near high-mobility structure jitter.
- **High ENERGY cells** — attract consumers (density siphon enhanced).
  Particles are pulled toward energy-rich crystal.
- **High REACTIVITY cells** — coupling strength amplified. Particles
  near reactive material exchange OMEGA faster.

These would be multipliers on existing physics terms:
```
! In physics kernel, waveguide read:
RHO := REAL(GRID_DENSITY(CI,CJ,CK)) * COUPLING
! Future: modulate by material reactivity
! RHO := RHO * (1.0 + REAL(M_REACT) / 15.0)
```

## 6. Current State (for reference)

- CRYSTAL_ARCHETYPE = 1 (STELLAR_DEAD) for galaxy domain
- 11 archetypes defined in LUT (VOID through METAL)
- 4-bit signed nibble deltas, 24-bit STATE
- Three decay channels operational (radiative, agent, stress)
- Pristine fast path: 95%+ cells skip delta unpacking
- Galaxy sim: zero decay (STELLAR_DEAD properties produce zero loss)
