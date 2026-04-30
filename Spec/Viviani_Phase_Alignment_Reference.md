# Viviani Phase Alignment — Why Disks Form

## The Key Insight

The Viviani field does NOT attract particles to spatial positions on the curve.
It aligns velocity projections to a rotating basis vector. The disk emerges
from phase coherence, not spatial attraction.

Particles never "touch" the curve — they satisfy a velocity projection
constraint, and the flat disk appears as a consequence.

## The Mechanism

1. A basis vector `n(phi)` rotates through 3D space (the Viviani tangent)
2. Each particle's velocity is steered toward `v · n = target`
3. The target modulates with phase position (cos(phi) for strong channel)
4. Particles with aligned velocities naturally co-orbit
5. The Y-axis (perpendicular to disk plane) collapses as alignment improves

## Mapping to Ergo Simulation

| Concept | Demo (Deepseek) | Ergo simulation |
|---|---|---|
| Rotating basis | `n(phi)` = viviani_basis() | `TANGENT(*, GEN)` LUT |
| Velocity alignment | `v·n → target` | EM steering (section 10) |
| Alignment force | `gamma * error * n` | `STEER_R * (V - V_DOT_T * T)` |
| Phase modulation | `cos(phi)` target | `Z_COUPLING(GEN)` strong channel |
| Disk formation | Z-std drops over ~200 frames | Sphere flattens naturally |

## The NASA Cup Analogy

- `n(phi)` = the cup's orientation (rotating)
- `target = cos(phi)` = surface tension direction
- `v·n = cos(phi)` = liquid surface aligned to cup
- The disk = the liquid surface itself

## Why Disks Are Energy-Efficient

Starting from a sphere at 30M particles: 50fps (80fps headless).
Starting from a disk at 30M particles: 74fps (141fps headless).

The disk is computationally cheaper because:
- Fewer grid cells occupied (~30% vs ~52% of 32^3 volume)
- Better cache coherence (particles in thin Y band hit same cells)
- Less render overdraw (thin disk vs full depth sphere)

Nature prefers disks for the same reason — angular momentum conservation
minimizes the Y-axis extent, which minimizes interaction volume, which
minimizes energy dissipation. The simulation's performance profile
mirrors the physics: low-entropy configurations are cheap.

## Phases of Formation (from Deepseek's demo)

### Phase 1: Random cloud (0-100 frames)
- Random positions, random velocities
- No alignment, no structure

### Phase 2: Velocity alignment begins (100-200 frames)
- Steering force rotates velocities toward tangent
- Particles with similar phase start co-orbiting

### Phase 3: Disk forms (200-400 frames)
- All velocities converge to satisfy projection constraint
- Z-axis collapses as velocities align to XZ plane
- Flat disk emerges in position space

### Phase 4: Breathing and shells (400+ frames)
- Disk thickness oscillates with cos^2 modulation
- Shell structures appear in radial distribution
- System is stable — no explosion, no collapse

## Reference Implementation

Deepseek's 800-particle Python demo (matplotlib animation):

```python
def viviani_basis(phi):
    x = np.sin(phi) - 0.5 * np.sin(3 * phi)
    y = -np.cos(phi) + 0.5 * np.cos(3 * phi)
    z = np.cos(phi) * np.cos(3 * phi)
    norm = np.sqrt(x*x + y*y + z*z)
    return np.array([x, y, z]) / norm if norm > 1e-6 else np.array([1,0,0])

# Per particle per frame:
n = viviani_basis(omega * t)
target = np.cos(omega * t)
proj = np.dot(vel[i], n)
error = proj - target
vel[i] -= gamma * error * n * dt    # steering force
pos[i] += vel[i] * dt               # integration
```

This is the minimal reproduction of what the Ergo physics kernel does
at 30M particles on GPU — the same math, just sections 8-10 of
SIM_PHYSICS_STEP compressed to 6 lines.
