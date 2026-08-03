# Dendritic Stage 2 — dynamic alignment: do segments seek the low-field wedge?

Program: `min/fdtd/dendrite_stage2.ergo` (+binary/.out). TE Yee solver
(ribbon geometry), 256×256, sponge 20, s=0.5, NSTEPS=3000.

## Setup and the inertia model (documented)

- NSEG=5 ribbon segments, L=40 cells, pinned at junction (128,128),
  diverging ramped DC (junction = common source). Initial angles
  (documented seed — fixed list): **20°, 80°, 150°, 210°, 320°**.
- **Torque**: per segment about the junction,
  τ_s = Σ_cells r×(J×B) = −Hz·(r_x·j_x + r_y·j_y). The ribbon's own
  field vanishes on its axis (weber_check.md), so the Hz at a segment's
  cells IS the other segments' field — the torque is a clean
  cross-segment quantity by construction.
- **Rotational dynamics** (the sim has no segment inertia, so we define
  it — simplest documented model): OVERDAMPED first-order relaxation,
  ω_s = τ_s / GAMMAR with GAMMAR = 2000, capped at |ω| ≤ OMAX = 5e-4
  rad/frame to keep rotation quasi-static against the field solve. No
  inertia term; rate is model-chosen, DIRECTION is physical.
- E-field/accumulated-charge torque NOT included in the dynamics
  (documented): the charge-buildup comparison is drawn from the
  trajectory timing vs the known charge ramp Q = I·t.
- Segments cross each other freely (superposition, no sterics).

## Angle trajectories (degrees; torque τ in parentheses at t=2750)

| t | seg1 (20°) | seg2 (80°) | seg3 (150°) | seg4 (210°) | seg5 (320°) |
|---|---|---|---|---|---|
| 350 | 17.5 | 83.7 | 153.2 | 210.3 | 318.2 |
| 950 | 2.1 | 100.7 | 169.1 | 210.8 | 308.3 |
| 1550 | −15.1 | 117.9 | 186.3 | 210.7 | 293.7 |
| 2150 | −32.3 | 135.1 | 203.5 | 209.5 | 276.5 |
| 2450 | −40.9 | 143.7 | 212.1 | 212.3 | 267.9 |
| 2750 | −49.5 | 152.3 | 220.2 (0.97) | 220.2 (0.97) | 259.4 |
| 3000 | −56.7 | 159.5 | 225.3 (0.68) | 225.3 (0.68) | 252.2 |

## Verdict — the void is PASSIVE; segments bunch onto each other

**(a) No reorientation toward the 90–120° low-field wedge.** No
segment moves toward the cancellation region identified in Stage 1.
Instead the dynamics is **pairwise magnetic attraction**: segments 3
and 4 (opening 60°) collapse onto each other — their mutual angle
closes to 0° by t≈2750 and they lock together at ~225° with identical
torques — the exact OPPOSITE of settling into a wedge between them.
Segments 2 (80→152°) and 5 (320→259°) converge on the bunch; segment
1 rotates away clockwise (20→−57°, taking the long way toward the
cluster through −140°).
**(b) Diagnosis of the wedge's passivity:** the cancellation wedge is
a superposition null of the CURRENT PATTERN, not a force minimum. The
torque on a segment is set by the other segments' fields at its
position — and same-direction ribbon currents attract, so a segment in
a low-field region feels an imbalance pulling it toward the NEARER
neighbor, not into the null. Torque nulls exist (segment 4 hovered at
τ≈0 around 210° for ~1000 frames) but they are pass-through
equilibria, not attractors. So: **the low-field wedge is a passive
cancellation region; the attractor is bunching (collapse onto
neighbors), not the wedge.**
**(c) Alignment rate vs charge buildup:** reorientation is driven by
the STEADY J×B torque (τ ~ 0.7–2.3 throughout) and progresses
uniformly from t≈250 onward, well before the tip-charge budget
(Q = I·t, reaching ~140 by t=3000) could dominate — consistent with
Stage 1's finding that charge accumulation modulates field strength,
not structure. Rate caveat (honest): much of the run sat at the
|ω| = OMAX cap, so the trajectory DIRECTIONS are physics but the
speeds are set by the documented damping model.

Files: `dendrite_stage2.ergo` (+binary, `.out`), this report.
