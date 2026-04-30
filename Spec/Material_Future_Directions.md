# Material System — Future Directions

Captured from Grok's review of the archetype + delta design (2026-04-29).
These are architectural notes for when the resonance database and multi-domain simulations mature.

## 1. Resonance-Driven Archetype Selection at Quench

**Current limitation:** Crystallization uses a flat `CRYSTAL_ARCHETYPE` parameter per domain. Every crystal cell becomes the same material regardless of local conditions.

**Future state:** When a hopfion/soliton cluster reaches crystallization threshold (via phason flip + energy loss), compute the local harmonic stack and match it against the resonance library to dynamically select `ELEMENT_ID`.

```
! In scatter / crystal banking section:
local_harmonics = compute_harmonic_signature(pos, vel, theta, psi, envelope)
ELEM_ID         = RESONANCE_MATCH(local_harmonics, particle_state)
MATCH_QUALITY   = resonance_score(...)          ! 0.0 to 1.0

ENERGY_DELTA    = CLAMP(INT(OMEGA * 15.0 / OMEGA_MAX), 0, 15)
COHERENCE_DELTA = CLAMP(INT(MATCH_QUALITY * 7.0), -8, 7)

GRID_MATERIAL(CI,CJ,CK) = IOR(ISHFT(ELEM_ID, 24), &
                        ISHFT(ENERGY_DELTA, 16), &
                        ISHFT(COHERENCE_DELTA, 20), ...)
```

Higher match quality → higher initial COHERENCE → more stable, longer-lived
crystal. Noisy or poorly phase-locked quenches produce fragile material that
decays faster. Natural quality metric.

## 2. Delta Precision Trade-offs

Current 4-bit signed deltas (±7) are acceptable for galaxy-scale (stellar_dead
has almost no decay). Biological and chemical simulations will likely need
finer control.

Options (in order of preference):
- Keep current 24-bit STATE for now (fast, cache-friendly)
- Expand to two 32-bit integers per cell (256 KB total) → 8-bit deltas (±127)
- Hybrid: Use FLAGS nibble to index into a sparse high-precision overlay grid
  when needed

No immediate change required. Monitor biological runs for quantization artifacts.

## 3. Resonance Library Format

Needs to be compact and GPU-friendly for fast per-quench lookups.

Recommended starting design:
- Fixed signature per archetype: 8-12 floats (dominant harmonic coefficients
  + spin/orbital weights)
- Total size: 256 archetypes × 12 × 4 bytes = 12 KB → easily fits in push
  constants or constant buffer
- Optional: Add a 32-bit spectral hash for ultra-fast rejection before full
  comparison

The `RESONANCE_MATCH()` function should return both the best ELEMENT_ID and a
normalized match quality score.

## 4. Multi-Material Interfaces & Reactions

When adjacent cells have different archetypes:
- Sharp interfaces for solid-solid boundaries
- Gradient blending for fluid-like materials
- Optional reaction zones where differing archetypes trigger new archetype
  creation or delta shifts (alloys, chemical reactions, biological decomposition)

This becomes relevant once resonance-based selection is active and multiple
materials can appear in the same simulation.

## 5. Material-Modulated Particle Coupling

Material properties should influence live particle behavior through the waveguide:
- High COHERENCE: Stable, predictable gradients → clean orbital steering
- High MOBILITY: Noisy field → increased particle jitter
- High ENERGY: Stronger attraction to consumers
- High REACTIVITY: Amplified OMEGA/phase exchange rate

Example modulation:
```
coupling = 1.0 + (REAL(M_REACTIVITY) / 15.0) * REACTIVITY_FACTOR
rho      = REAL(GRID_DENSITY(...)) * coupling
```

These multipliers plug into existing force terms without major refactoring.

## 6. Current State Summary (April 2026)

- Still using static CRYSTAL_ARCHETYPE per domain
- 11 archetypes defined (VOID through METAL)
- 4-bit signed nibbles for deltas, 24-bit STATE
- Strong pristine fast path (95%+ cells)
- Galaxy domain uses STELLAR_DEAD (zero decay)
- Material system is architecturally ready for resonance injection

The archetype + delta design provides an excellent foundation. Once the
resonance database and harmonic signature computation are complete,
switching from fixed archetype to dynamic `RESONANCE_MATCH()` at quench
time should be relatively straightforward.

## 7. Crystallization Criterion Evolution

**Current limitation:** Crystallization is `OMEGA < 0.008 AND V < 0.01` — a
scalar low-energy condition. But OMEGA equilibrates at ~0.05 due to
OMEGA_BASE (0.08) providing a constant floor. The threshold is unreachable
under normal dynamics. All particles that crystallize do so the same way
(COAST decay to floor), producing only 2 material classes (DENSE_INNER vs
HALO_DUST) differentiated solely by density × radius.

**The deeper finding:** The physics conserves too much mobility. The field
has a nonzero mobility attractor. Damping alone does not produce inert
matter. Equilibrium is active, not frozen.

### Option A: Variance-based crystallization (detect frozen dynamics)

Instead of low absolute energy, detect that energy *stopped changing*:

```
IF ABS(OMEGA - OMEGA_PREV) < EPSILON .AND. SPD_SQ < 0.01 THEN
  PFLAG_CRYSTAL := set
ENDIF
```

Requires storing OMEGA_PREV per particle (1 extra array, 4 bytes × MAXPART).
Detects truly frozen particles regardless of their absolute OMEGA level.
A particle at OMEGA=0.05 that hasn't changed in 1000 frames is more
"crystal" than one at OMEGA=0.01 that's oscillating.

### Option B: Local sink mechanism (irreversible energy extraction)

Add a mechanism that drains OMEGA below the floor in specific conditions:

```
! Dense regions: binding lock — neighbors absorb mobility
IF RHO > DENSE_LIMIT THEN
  OMEGA := OMEGA * 0.95
ENDIF

! Or: hysteresis — reactivation harder than activation
IF IAND(FLAGS, PFLAG_DORMANT) ≠ 0 THEN
  OMEGA_DECAY := OMEGA_DECAY * 4.0
ENDIF
```

Creates a path to low OMEGA that OMEGA_BASE alone can't maintain.
Different sink mechanisms produce different death paths = richer signatures.

### Option C: Two-stage phase state (strongest long-term)

Replace binary ACTIVE/CRYSTAL with three states:

| State   | Meaning                                    |
|---------|---------------------------------------------|
| ACTIVE  | High mobility, full field coupling           |
| DORMANT | Low mobility, reduced coupling, reversible   |
| CRYSTAL | Structurally locked, irreversible, field only |

Crystallization becomes topology-dependent:

```
IF OMEGA < DORMANT_LIMIT
  .AND. NEIGHBOR_ALIGNMENT > ALIGN_LIMIT
  .AND. AGE > MIN_AGE
THEN
  PFLAG_CRYSTAL := set
ENDIF
```

This matches the hopfion architecture — a ring that loses coherence
becomes DORMANT (can recover), but a ring that loses coherence AND
has high neighbor alignment becomes CRYSTAL (locked structure).
Different paths to crystal = different signatures = richer materials.

### Measured baseline (2026-04-30)

At threshold 0.048 (above equilibrium floor), 500K frames, 5M particles:
- 4096 crystallization events captured
- 2 material classes: DENSE_INNER (33%, core) and HALO_DUST (67%, edge)
- Differentiation on density × radius only
- All other signature fields identical at death (OMEGA≈0.037, V≈0.1, FMODE=0)
- Ring coupling has no effect on crystallization signatures at equilibrium

## Priority Order

1. **Crystallization criterion evolution** (Option A or C above)
2. Resonance signature computation + matching kernel
3. Dynamic ELEMENT_ID selection at crystallization
4. Match-quality → initial COHERENCE mapping
5. Material-property modulation of particle physics
6. Multi-material boundary handling
