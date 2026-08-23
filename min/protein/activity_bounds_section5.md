## 5. Molecular Dynamics (chain_fold / waveform MD) — Adaptive Substepping

**Status:** implemented in the waveform template (`SUBSTEP_D`, `SUBSTEP_MAX`).
No compiler changes.

### Design constraint (standing)

No artificial clamping or damping. Nothing is restricted unless there is a
physical reason for it. Numerical instabilities are resolved by *resolution*
— finer time steps where the potential is steep — never by caps.

### The failure mode

Fixed-timestep impulse integration against the steric wall
(FM = ε(σ/D)^6): per-frame displacement equals the gap itself at
D ≈ 0.52 (solve D^7 = DT^2 · FORCE_SCALE · ε · σ^6). Below that D the kick
overshoots the interaction region; the pair swaps sides, the next kick
lands at smaller D, and the cycle diverges. No fixed linear damper can
stabilize an unbounded D^-6 gain. The wall is physical; the clock is too
coarse to watch the bounce.

### Rule

Each frame, BEFORE the force block, compute the closest approach DMIN over
all steric pairs (|i-j| >= 4) and all backbone bonds. Then:

```
NSUB = 1                                    if DMIN >= SUBSTEP_D
NSUB = min(SUBSTEP_MAX, floor(SUBSTEP_D/DMIN) + 1)   otherwise
```

The frame's full force+integrate block (steric, hydro, Go, cystine,
mispair, Morse, angle, torsion, register, frame dynamics, damping,
position update) runs NSUB times with DTW = DT/NSUB, forces recomputed
from current positions each substep. Dampers are compounding factors and
are rooted, not repeated: DAMP_SUB = VELOCITY_DAMP^(1/NSUB),
FDAMP_SUB = FRAME_DAMP^(1/NSUB) (with exact pass-through at NSUB = 1).

- **A priori (rule 4):** NSUB is a deterministic function of the state
  (closest approach), never of any field amplitude measurement.
- **Bitwise oracle (rule 5 analog):** at NSUB = 1 the substepped frame is
  operation-for-operation identical to the unwrapped frame (DT/1 = DT
  exactly, dampers pass through exactly). Any previously stable run must
  reproduce BITWISE with substepping compiled in. If it does not, the
  wrapping changed evaluation order — fix the wrapping, not the check.
- **Defaults:** SUBSTEP_D = 0.8 (above the 0.52 overshoot threshold with
  margin), SUBSTEP_MAX = 64 (DT/64 = 1.6e-4 resolves D down to ~0.08;
  below that the physics is a true fusion event the model does not claim
  to represent).
- **Cost:** only frames with close approaches pay. Healthy collapse
  trajectories sit at DMIN > 1 and never substep. Hot frames are the
  GPU tile-clip map's natural targets if the handoff is needed.

### Physics contract

Nothing is capped. Every value is earned by the dynamics; substepping only
refines the time resolution with which steep potentials are integrated.
A clash produces a hard, bounded, honestly-computed bounce.
