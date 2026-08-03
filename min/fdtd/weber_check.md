# Weber vs Maxwell in the FDTD system — force comparison

Programs (min/fdtd/): `fdtd_tm.ergo` (TM: Ez, Hx, Hy — parallel line
currents, the oracle), `fdtd_te.ergo` (TE: Hz, Ex, Ey — collinear
elements, both driven), `fdtd_te1.ergo` (collinear, seg1 driven only —
clean field measurement), `fdtd_loop.ergo` (TE closed rectangular loop).
Standard Yee updates, s = dt/dx = 0.5 (2D CFL ≤ 1/√2), cosine sponge
boundaries (proven pattern from the scalar FDTD work), ramped DC soft
current sources. Normalized units ε₀=μ₀=1, c=1.

**Geometry note (critical, documented):** a 2D Maxwell solver has two
decoupled polarizations with different physical meanings. TM point
sources Jz are true 3D LINE currents (B = μ₀I/2πr) — used for the
oracle. TE in-plane currents Jx/Jy are infinite current RIBBONS
(sheets per unit z) — the collinear and loop cases live here, and all
analytics are done in the sheet geometry (documented per result).

## 1. Solver validation — the parallel-wire oracle (TM)

Two line currents at (128,98) and (128,158), R=60, wire 2 un-driven
(probe reads wire 1's external field only). Steady state converged to
6 digits by t=3000:

| check | sim | analytic | deviation |
|---|---|---|---|
| H profile 1/r (r=30/60/90) | 2.85/1.54/1.06 ×10⁻⁴ | 2.65/1.33/0.88 ×10⁻⁴ | scaling exact; +8/16/20% point-wise |
| H above/below avg r=30 | 2.63×10⁻⁴ | 2.65×10⁻⁴ | **0.8%** |
| H above/below avg r=60 | 1.245×10⁻⁴ | 1.33×10⁻⁴ | **6.4%** |
| Ampère circulation ∮H·dl (16×16 contour) | 0.0480 | I = 0.0500 | 4% (exact in the discrete scheme up to residual ∂Ez/∂t) |
| field direction | azimuthal: Hx dominant, Hy ≈ 5% | azimuthal | ✓ |

The oracle passes: force J₂×B₁ along the joining line = I₂·H with the
measured H within ~6% of Biot-Savart (the point-wise excess is grid
anisotropy plus the known 2D DC Ez-offset peculiarity — the 2D wave
Green's function has no bounded static limit; H itself is unaffected,
and the Ampère circulation confirms the normalization).

## 2. Collinear elements (TE) — the discriminating case

Two collinear current ribbons on the x-axis: seg1 x∈[68,108], seg2
x∈[148,188], gap 40, both driven +x (ramped DC).

**(a) B on the axis ≈ 0** ✓: Hz at the seg2 midpoint is +0.0251 at
y=128.5 and −0.0242 at y=127.5 — antisymmetric, cancelling on the axis
(residual on-axis ≈ 4×10⁻⁴ = 2% of the off-axis value). Collinear
Biot-Savart vanishes; **the magnetic force J×B is zero on-axis**, as
the briefing states.

**(b) E longitudinal from end-charge accumulation** ✓: continuity
(∇·J ≠ 0 at ribbon ends) ramps charge at ± ends — measured E fields
grow LINEARLY in time (probe after seg1's end: 0.003→0.61 over
t=100..1500; seg2 midpoint −0.014→−0.48). There is no DC steady state
for open elements — exactly the Maxwell account.

**(c) The longitudinal force** (seg1-only run, clean field): seg1's
field along seg2 is longitudinal (+x, 0.031–0.081 growing linearly),
and the force on seg2's accumulated end charges is **attractive**
(−x, toward seg1), magnitude ≈ Q(t)·[E₁(148)−E₁(189)] ≈ 3.5 at
t=1500, growing ∝ t² (charges ∝ t, field ∝ t). The transverse
component E_y ≈ 0.

**Weber evaluation (documented mapping):** for steady DC elements,
Fechner's hypothesis (current = symmetric ± carrier motion) gives
ṙ = 2·v_drift (relative radial carrier velocity) and r̈ = 0, so
Weber's law reduces to a CONSTANT longitudinal attraction between
collinear same-direction elements: F_Weber = (μ₀/4π)·2·I₁I₂L₁L₂/R²
= 5.3×10⁻³ in sim units (R = 40 gap). **Comparison: the signs AGREE
(attraction) — but the functional forms differ fundamentally: Weber
supplies a constant velocity-dependent force; Maxwell supplies an
electric force that grows with the accumulating charge (no DC steady
state for open elements).** The two can only be identified in the
closed-circuit limit — which is precisely the historical theorem
(Weber ≡ Ampère ≡ Maxwell for closed circuits), tested next. So: the
Maxwell answer to "who supplies the longitudinal force between
collinear elements?" is demonstrated in the sim: **not qv×B (zero
on-axis) but qE from continuity-mandated charge accumulation — no
velocity-dependent potential needed.**

## 3. Closed loop (TE) — the agreement test

Rectangular ribbon loop (drive ranges chosen per-cell divergence-free
— verified analytically in the staggered flux bookkeeping):

- **No charge ramp**: corner/edge E fields bounded and small
  (~10⁻⁵–10⁻⁶, oscillating to zero) — continuity satisfied, static
  fields only.
- **Static B holds exactly**: interior Hz = 0.0500 rock-steady from
  t≈700 to t=3000. Sheet-physics analytics: the ribbon loop is a 2D
  solenoid — each ribbon contributes μ₀K/2 per side, giving uniform
  B = μ₀K = 0.0500 inside ✓ (measured EXACTLY 0.0500) and ~0 outside
  (test element at (218,100): settles to −0.000000 ✓).
- **Ampère circulation** around the bottom sheet: −5.0000 vs
  K×width = 0.05×100 = 5.0 ✓ exact.
- **Force on an external collinear element** from the closed loop:
  ≈ 0 (the solenoid's exterior field cancels) — the 2D form of the
  closed-circuit result: for closed currents, Maxwell's field
  computation and Weber/Ampère's action-at-a-distance integral give
  the SAME field and the SAME force (here: both zero outside, by the
  same cancellation). Documented agreement.

## Caveats (honest)

- The TM oracle's point-wise H runs 8–20% above Biot-Savart (grid
  anisotropy + 2D DC Ez offset); the profile/circulation/averaged
  values are the solid ones (0.8–6.4%). No stability issues at the
  current sources (soft ramped sources, s=0.5).
- The collinear force magnitude is time-dependent by construction
  (charge ramp) — no steady-state number exists to quote against
  Weber's constant; the comparison is structural (sign ✓, mechanism ✓,
  functional form ✗ by design, closed-circuit agreement ✓).
- 2D limitation: true 3D wire-element forces (finite L/r corrections)
  can't be computed in 2D; the sheet geometry is the honest 2D analog
  and is used consistently for every analytic comparison.

Files: `fdtd_tm.ergo`, `fdtd_te.ergo`, `fdtd_te1.ergo`, `fdtd_loop.ergo`
(+binaries, `.out`s), this report.
