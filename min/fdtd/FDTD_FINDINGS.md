# FDTD Electrodynamics Campaign — Findings

**Date:** 2026-08-03
**Scope:** 2D FDTD wave-optics and full Maxwell Yee solver validation,
Weber-vs-Maxwell force comparison, and the dendritic-pattern test
(Stages 1–2). All results oracle-validated; nulls documented with
engagement controls.

---

## 1. Wave-Optics Validation (scalar FDTD)

`min/fdtd/fdtd_slit.ergo`, `fdtd_sw.ergo` — scalar 2D wave equation,
leapfrog, sponge boundaries.

- Double-slit fringes: λ=16 → 65.50 cells vs 65.00 oracle (**0.8%**);
  λ=20 → 85.00 vs 81.25 (**4.6%**). λ=12 deviates +10.5% — correctly
  identified as Fresnel-regime broadening (d²/λL = 1.31), not an error.
- Standing-wave nodes: 7.91 vs 8.0 cells (**1.1%**).
- GPU (SPIR-V): extraction-correct (identical fringe numbers; standing
  wave bitwise identical) but launch/transfer-bound at this grid size —
  the transfer-flood weakness documented in the stage-4 GPU work.
- Field description of light (fringes, diffraction, standing waves)
  validated as far as classical optics goes; photons enter only at
  detection, which is out of scope for the solver.

## 2. Weber vs Maxwell Force Comparison

`min/fdtd/fdtd_tm.ergo`, `fdtd_te.ergo`, `fdtd_te1.ergo`,
`fdtd_loop.ergo` — full 2D Maxwell Yee solvers (TM: E_z,H_x,H_y;
TE: H_z,E_x,E_y), ramped DC sources, cosine sponge.

**The question:** does Maxwell's `F = qE + qv×B` handle longitudinal
(line-joining) forces between current elements, or is a Weber-style
velocity-dependent potential needed?

- **Oracle (parallel wires):** H matches 1/r scaling; J×B force along
  the joining line validated to ~6%.
- **Collinear (discriminating case):** B on-axis = 2% of off-axis
  (qv×B ≈ 0 confirmed), but the longitudinal force on the partner is
  **attractive and nonzero — supplied entirely by the E field** of
  continuity-mandated charge accumulation at the open elements' ends
  (measured: E grows linearly in time, 0.003→0.61). Weber's formula
  gives a constant attraction of the same sign; Maxwell's E-field force
  is time-dependent (∝ t²) because open elements have no DC steady state.
  Signs agree, mechanisms agree, functional forms differ by design —
  reconcilable only in the closed-circuit limit.
- **Closed loop:** static interior B = 0.0500 = μ₀K **exactly**,
  exterior ≈ 0 — **Maxwell ≡ Ampère ≡ Weber for closed circuits.**

**Verdict:** Maxwell handles longitudinal forces electrically (the qE
term from continuity-mandated accumulation), with no velocity-dependent
potential. Weber's law is an alternate mechanism for the same physics —
viable in quasi-statics, unable to reach the radiation regime the FDTD
solver lives in natively.

**Methodology catch (worth recording):** an initial Biot-Savart
comparison failed by 88× because line-current analytics were applied to
2D ribbon currents (infinite sheets). The sim was right; the textbook
geometry assumption was wrong. Analytics for 2D TE currents must be done
in the sheet geometry.

## 3. Dendritic Pattern Test (Stages 1–2)

Testing whether electromagnetic field topology can drive dendritic
(branching) pattern formation.

### Stage 1 — geometry creates voids (`dendrite_stage1_check.md`)

Two ribbon segments at angles 0°–180°, shared junction, ramped DC.

- **B-field voids are systematic with angle:** inner-region void-block
  count 5 → 9 → 11 → 14 → 18 → **21 (120°)** → 14, with positions
  tracking the geometry — on-axis at 0°, spreading at 30–60°, filling
  the **inter-segment cancellation wedge at 90–120°**, vertical null
  columns at 180°.
- **Mechanism (measured):** the two ribbons' sheet fields point
  oppositely inside the wedge — superposition cancellation that widens
  with opening angle. A steady-current effect.
- **E-field voids: none** at any angle — charge accumulation produces no
  cancellation structure (junction deficit tracks |1+cos θ|; tips ~I·t
  regardless of angle).

**Verdict:** geometry alone predicts void structure; charge accumulation
does not create it.

### Stage 2 — the void is passive (`dendrite_stage2_check.md`)

Five ribbon segments pinned at a junction, free to rotate, overdamped
rotational dynamics from J×B torque.

- **No alignment toward the 90–120° low-field wedge.** Instead,
  **parallel-wire bunching:** segments 3+4 (60° apart) collapse onto
  each other (mutual angle → 0° by t≈2750, locking ~225°); the rest
  converge on the bunch.
- **Diagnosis:** the wedge is a superposition null of the current
  pattern, not a force minimum. A segment in the low-field region feels
  the imbalance pulling it toward its *nearer neighbor* (same-direction
  ribbons attract), not into the null. Torque nulls exist but are
  pass-through equilibria, not attractors.
- **Rate check:** reorientation is steady-J×B-torque driven from t≈250
  onward, well before tip-charge buildup could dominate — charge
  modulates strength, not structure.

**Verdict:** the wedge exists but is **passive** — a cancellation
artifact, not a potential well. The electromagnetic attractor for free
current segments is **bunching** (parallel currents lock and merge), not
branching. Dendritic patterns require a different mechanism class
(tip-driven Laplacian growth / dielectric breakdown), not free-segment
dynamics.

**Thread resolved:** the DBM follow-up is built and validated in
`min/dendrite/` (`DENDRITE_FINDINGS.md`) — tip-driven Laplacian growth
branches (D≈1.71 at η=1, screening instability in strip geometry),
confirming the mechanism-class diagnosis above.

## 4. Three Hypotheses, Measured

| hypothesis | verdict |
|---|---|
| Low-field void is an attractor (dendrite driver) | ✗ dead — passive superposition null |
| Charge accumulation drives morphology | ✗ dead — modulates strength, not structure; torque precedes charging |
| J×B bunching is the attractor | ✓ measured — parallel currents collapse, lock, merge early-onset |

## 5. Caveats

- 2D TE currents are infinite ribbons per unit z; 3D finite-element
  corrections are out of scope.
- Stage 2 speeds are model-chosen (ω cap saturated much of the run);
  directions are physics, rates are not.
- The bunching result is electrodynamics of free current segments — it
  does not extend to biological current organization (action potentials
  are transient and ~10⁶× below thermal force scales; fasciculation is
  molecularly driven, not electromagnetic).
- GPU extraction works for these solvers but is launch/transfer-bound
  at FDTD grid sizes; CPU path used for all results here.

## 6. Reproducibility

| artifact | path |
|---|---|
| Wave optics (slit, standing wave) | `min/fdtd/fdtd_slit.ergo`, `fdtd_sw.ergo`, `fdtd_check.md` |
| Stage-2 GPU/debug records | `min/fdtd/fdtd_stage2_check.md` |
| Weber vs Maxwell | `min/fdtd/fdtd_tm.ergo`, `fdtd_te.ergo`, `fdtd_te1.ergo`, `fdtd_loop.ergo`, `weber_check.md` |
| Dendrite Stage 1 (angle sweep) | `min/fdtd/dendrite_a*.ergo`, `dendrite_stage1_check.md` |
| Dendrite Stage 2 (dynamics) | `min/fdtd/dendrite_stage2.ergo`, `dendrite_stage2_check.md` |
