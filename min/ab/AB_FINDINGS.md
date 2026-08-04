# AB_FINDINGS.md — Aharonov-Bohm lensing campaign (papers/2301.09980v2)

**Question:** does the Ergo wave engine (real/imag staggered-leapfrog
Schroedinger + Peierls link phases, all CPU, deterministic) predict
the paper's AB lensing effects on its own, or does it need tweaking?

**Verdict (short):** it emerges on its own. With the link-phase sign
convention fixed once (a genuine implementation bug caught by the
uniform-beta velocity test — the sin terms must act on the same field),
every headline effect appears with no per-effect tuning: linear fringe
shift with flux, gauge-clean nulls, flux periodicity to a few percent,
parabolic phase profile in the torus hole, polarity flip on current
reversal, and a quartic term of opposite sign to the quadratic one
(Cs/f opposite polarity) in both current directions. Quantitative
accuracy is fan-averaging/discretization limited (~10-20% at the
fringes, ~9-35% on the lens curvature — see per-stage numbers).

## Stage table

| stage | file | oracle | result | verdict |
|---|---|---|---|---|
| 0 null | `stage0_null.ergo` | centroid at center | 256.0000/256.0000 (env/fringe) | PASS |
| 0 phase screen | (same) | fringe shift = TH0/2pi periods = 8.65 cells, envelope unmoved | fringe 8.35, env 0.25 | PASS |
| 0 classical V | (same) | envelope AND fringes move (contrast) | env -5.45, fringe -22.6 | PASS |
| 1 spreading | `schrod_2d.ergo` | sigma(t)=s0 sqrt(1+(2at/2s0^2)^2) | 12.792 vs 12.806; 40.722 vs 40.792 | PASS (0.1-0.2%) |
| 1 dispersion | (same) | v_group = 2 a k0 = 0.16 | 0.1547 (3.3%, lattice dispersion) | PASS |
| 1 stability | (same) | a <= 0.25 (=2/Lmax, Lmax=8) | a=0.24 stable, a=0.26 NaN | PASS (sharp) |
| 2 flux sweep | `ab_fluxline.ergo` | fringe phasor phase steps pi/4 per case | see table below | PASS w/ fan-averaging caveat |
| 2 gauge oracle | (same) | A=grad chi single-valued -> zero | 0.028-0.042 rad | PASS (lie detector) |
| 2 periodicity | (same) | FL=2pi == FL=0 pattern | residual 0.24-0.33 rad (4-5%) | QUALITATIVE (see S2 note) |
| 2 channel probe | (same) | per-channel phase difference = pi at FL=pi | 3.39-3.41 rad | PASS (~8%) |
| 3 self-consistency | `ab_lens.ergo` | emergent c2 vs (q/hbar)sum A_z | 5.80e-4 vs 6.35e-4 (9%) | PASS |
| 3 parabolic profile | (same) | quadratic+quartic fit R^2 | 0.90 / 0.97 (two polarities) | PASS |
| 3 polarity flip | (same) | c2 sign flips with J | +5.80e-4 / -8.56e-4 (inner: +9.89/-9.72 e-4) | PASS |
| 3 Cs vs f | (same) | sign(c4) opposite sign(c2), both polarities, both windows | holds (meas and pred) | PASS |
| 3 nulls | (same) | J=0 flat; conservative A step-but-flat | case3 exact 0; case4 |c2|=1.3e-4 of lens; case5 1.5e-3 | PASS |
| 3 solve | (same) | Poisson residual | 3.9e-6 (~1e-4 rel) | PASS |

Determinism: all four programs run twice -> byte-identical output.

## Stage 2 phasor series (fringe phase vs flux, unwrapped)

| FL | meas (rad) | exact (rad) |
|---|---|---|
| 0 | -0.000 | 0.000 |
| pi/4 | 0.53-0.56 | 0.785 |
| pi/2 | 1.10-1.14 | 1.571 |
| 3pi/4 | 1.74-1.80 | 2.356 |
| pi | 2.57-2.64 | 3.142 |
| 3pi/2 (unwrap) | 4.64-4.74 | 4.712 |
| 7pi/4 (unwrap) | 5.46 | 5.498 |
| 2pi (unwrap) | 5.95-6.02 | 6.283 |

Monotone, linear, high-flux values within 1-4%; low-flux lags up to
~30%. This is the finite-packet fan average: each channel is a
diffracting fan of paths, and the path-integral phase varies across
the fan, so the pattern-averaged phase is not the ray value. It is NOT
an implementation error — the loop integral of the link phases is
exact (verified in-sim to 1e-4) and the gauge oracle is clean.
Residual periodicity error (4-5%) is likewise fan-averaging + the
absorbing disk breaking exact gauge equivalence at one flux quantum
(disk-radius insensitive: 0.245 vs 0.263 rad at r=4 vs r=8).

## The one real bug found (and fixed) en route

The staggered leapfrog for the Peierls Hamiltonian must read
  dI = a (Lc R - Ls I),   dR = -a (Ls R + Lc I)
(sin-link terms act on the same field). The first version had them
crossed, which diluted the AB coupling ~40x (fringe shifts ~0.03
cells instead of ~7). Caught by the uniform-beta test (constant link
phase beta must shift the group velocity by exactly 2*a*beta). This is
why the gauge oracle alone is not enough — the gauge bump passes under
both the right and the crossed scheme; the velocity test is the real
lie detector for the curl part.

## Stage 3 mechanics (what "emerges on its own" means here)

- J_z from two discretized poloidal loops (minor radius 24, major 90,
  mirror circulation so the inner walls share a J_z direction, as in a
  toroidal solenoid); A_z from masked in-place GS-SOR
  (lap A_z = -J_z, zero frame); z-link Peierls phases; A_x omitted
  (second-order for the paraxial beam — documented in the source).
- The emergent wavefront curvature matches the same-grid line integral
  of A_z to 9% near the lens exit (z=300). Downstream (z=340+) the
  wavefront curvature is propagation-dominated — the eikonal comparison
  must be made near the lens; documented as window sensitivity.
- Cs/f sign relation (c4 opposite c2) holds in the measured wavefront
  AND in the raw A_z-integral profile, in both current directions.
- The lens strength used J0 = 0.005: at J0 = 1 the link phases alias
  past the lattice Nyquist (A_z ~ 6 rad/link) — the only parameter
  that HAD to be scaled, and it is a lattice-resolution bound, not
  physics tuning.

## Cross-links

- `min/fdtd/FDTD_FINDINGS.md` — the masked two-buffer stencil idiom
  this campaign's wave sections inherit.
- Paper claims (2301.09980v2): Tonomura step (periodicity — §Stage 2),
  parabolic in-hole phase profile, convex/concave flip on current
  reversal, Cs of opposite polarity to f (Scherzer evasion), no image
  rotation (no toroidal phase shifts — our link phases are z-only, so
  rotation is absent by construction).
