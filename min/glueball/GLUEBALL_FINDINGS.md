# Glueball campaign — findings

Can the engine compute pure-glue states at model level, checked against
BESIII/LQCD oracles. Three models, one per stage, each with independent
literature parameters (nothing tuned to BESIII; residuals reported, not
fitted). Python for Stages 1–2 (arithmetic, deterministic by
construction — each driver run twice, byte-identical); the Ergo
imaginary-time engine for Stage 3.

## Oracles (sourced)

- **BESIII** (PRL 132, 181901 (2024), `papers/PhysRevLett.132.181901.pdf`):
  X(2370), M = 2395 ± 11(stat) +26/−94(syst) MeV/c²,
  Γ = 188 +18/−17(stat) +124/−33(syst) MeV, J^PC = 0⁻⁺ (first
  determination, > 11.7σ). Consistent with the lightest pseudoscalar
  glueball; the paper quotes LQCD 2.395 ± 0.014 GeV (their ref [8]).
- **LQCD ordering:** 0⁺⁺ ~ 1.6–1.7 GeV < 2⁺⁺ ~ 2.2–2.4 <
  0⁻⁺ ~ 2.3–2.6 GeV. (f₀(1710) is the *scalar* candidate; X(2370) the
  *pseudoscalar* — the two are not conflated anywhere below.)

## Stage 1 — MIT bag (`bag_modes.py`)

Cavity zeros verified from the analytic mode conditions:
TE_1: d(x j₁)/dx = 0 → x = 2.743707 (lit. 2.7437); TM_1: j₁(x) = 0 →
x = 4.493409 (lit. 4.4934). Two-gluon minima of
E(R) = Ω/R + (4π/3)BR³, Ω = x₁+x₂−z₀, with DeGrand–Jaffe hadron-fit
inputs B^{1/4} = 146 MeV, z₀ = 1.84 (α_s = 0.55 enters only the
literature's magnetic splitting, not our numbers):

| config | states | E_min (pre-split) | R* |
|---|---|---|---|
| TE+TE | 0⁺⁺/2⁺⁺ | 0.9673 GeV | 0.99 fm |
| TE+TM | 0⁻⁺/2⁻⁺ | 1.2978 GeV | 1.09 fm |

Cross-check vs DeGrand et al. PRD 12 (1975) 2060 final (split) masses:
their 0⁺⁺ 0.96 and 0⁻⁺ 1.30 GeV match our degenerate minima; the
color-magnetic term pushes 2⁺⁺ → 1.29 and 2⁻⁺ → 1.66 (the right
direction for the LQCD ordering).

**Ordering verdict:** preserved (0⁺⁺ ≈ 2⁺⁺ < 0⁻⁺, splitting separates
0⁺⁺/2⁺⁺ correctly). **Levels:** everything ~40% light — scalar 0.97 vs
LQCD 1.6–1.7, and the pseudoscalar lands at 1.30 GeV vs LQCD 2.3–2.6:
a factor ~1.9 too light. This is the bag model's *known pseudoscalar
problem*, measured here rather than assumed: with B and z₀ fixed by
hadrons, the bag has no mechanism that pushes 0⁻⁺ up toward 2.4 GeV.

## Stage 2 — closed flux tube (`flux_loop.py`)

σ = 0.185 GeV² (√σ = 430 MeV, Sommer-scale string tension; input,
swept ±10% — masses scale √σ so the sweep moves levels ±5%). Three
documented prescriptions; quantum numbers per Isgur–Paton (n=1 phonon
→ 0⁺⁺, 2⁺⁺ degenerate; n=2 → 0⁻⁺, 2⁻⁺, 1⁻⁺):

| prescription | n=1 (0⁺⁺/2⁺⁺) | n=2 (0⁻⁺…) |
|---|---|---|
| (a) E² = 4πσn (Isgur–Paton standard) | 1.525 GeV | 2.156 GeV |
| (b) E² = 4πσ(n − 1/12) (Arvis) | 1.460 | 2.111 |
| (c) min_L [σL + (4πn − π/3)/L] | 2.920 | 4.222 |

**Ordering verdict:** preserved in all three (0⁺⁺ ≈ 2⁺⁺ < 0⁻⁺; the
pure string leaves 0⁺⁺/2⁺⁺ degenerate — spin splitting is beyond the
model). **Levels:** the standard form (a) puts 0⁺⁺ 7.6% below the LQCD
window mid and 0⁻⁺ 6.2% below the window — the best of the three
models here, and the only one with the pseudoscalar anywhere near
2.3 GeV. Form (c) is documented as the failure mode of the naive
Casimir closure: at the L where −π/(3L) binds, the loop
self-intersects — exactly why Isgur–Paton use (a).

## Stage 3 — Faddeev–Niemi Hopf soliton (`fn_soliton.ergo`)

The engine's part: a Q=1 Hopf texture relaxed by imaginary time on
the same flattened-stencil 3D machinery as the handshake campaigns.
Field n(x) ∈ S², energy E = E₂ + E₄ with E₂ = ½∫(∂n)²,
F_ij = n·(∂_i n × ∂_j n), E₄ = ¼∫Σ_{i<j}F_ij². Initial texture:
stereographic Hopf map (λ = 1.0, Q=1 by construction), Dirichlet
n = (0,0,−1) walls. Gradient flow with the analytically derived
quartic force (strain form, documented in the engine header),
projected ⊥ n, renormalized per point. Hopf charge on the grid:
B = ½εF, three SOR Poisson solves for ∇²C = −B, A = ∇×C,
Q = (1/16π²)∫A·B. Two production grids (driver `fn_analyze.py`,
each run twice): 128³ BOX=4 and 160³ BOX=5, same dx = 0.0625,
τ = 0.5 (1250 × dτ = 4e-4). **Determinism: both byte-identical ×2.**
The Ergo engine was cross-validated against an independent numpy
replica (τ=0 state and 300-step trajectories agree to all printed
digits).

Oracle verdicts:

| oracle | fn128 | fn160 | verdict |
|---|---|---|---|
| finite-size minimum (Derrick) | E 506→225, rms 4.0→2.3, no collapse/blowup in window | E 520→236, rms 5.0→2.8 | **holds** |
| Hopf Q start/mid/end | 0.958 / 0.969 / 0.971 | 0.974 / 0.979 / 0.970 | **stays ~0.97** (grid deficit ~3%, documented) |
| (2E₂+E₄)/32π² vs 1.232 (hep-th/0107187) | 1.1907 (−3.4%) | 1.2657 (+2.7%) | **within a few %**, both still descending at the cap |
| raw E vs published FN Q=1 (~241, Battye–Sutcliffe convention; 232–260 across normalizations) | 225.1 (−7%) | 236.5 (−2%) | **approaching from below**, under-converged |
| virial E₂/E₄ → 1 | 2.04 | 2.23 | **NOT met — honest fail, see below** |
| convergence at cap | ΔE/E = 3.0% over last 20% of steps | same order | **under-converged, stated plainly** |
| determinism | byte-identical | byte-identical | **holds** |

**The stage's real physics finding — the lattice topology barrier.**
Extended runs (beyond the production cap, run as diagnostics) show
the relaxation eventually drives the soliton core through the lattice
and the texture unwinds: Q slips to 0 at τ ≈ 0.2 (dx=0.125),
0.35–0.4 (0.083), 0.55 (0.071), 0.6 (0.0625 BOX=4), 0.65 (0.0625
BOX=5), after which E₄ collapses and the energy drains below the
continuum Q=1 bound (and smaller-λ variants go numerically unstable).
The slip τ grows with resolution but at every affordable spacing the
*continuum virial minimum lies below the lattice topology barrier*:
the grid flow does not conserve Hopf charge exactly, so the engine
cannot sit at the true minimum on these grids. Production therefore
stops at τ = 0.5, pre-slip, with Q ≈ 0.97 and the energy within a
few % of the published value and descending — the convergence level
reached, documented per the campaign's bounded-run rule rather than
hidden. Grid-convergence note: the two production grids share
dx = 0.0625 and differ in box size; their 4.8% energy difference
measures *boundary* sensitivity (the BOX=4 walls squeeze the texture:
rms 2.27 vs 2.84), not dx convergence — a genuinely finer-dx
production pair was not affordable within the bounded-run budget and
is the campaign's explicit deferral, together with a topology-aware
flow (e.g. arrested Newton + charge-fixing) as the cure for the
barrier slip.

Mass calibration (model-unit physics, nothing tuned): with
M_cl = (κ/e)·ε, ε = 236.5 (fn160 engine units), matching the Q=1
state to the LQCD scalar window (1.65 GeV) gives κ/e = 6.98 MeV —
order-consistent with Amari et al. (PLB 869 (2025) 139805), κ/e =
3.40 MeV (f₀(1500) input) / 6.31 MeV (f₀(1710) input), given the
different energy normalizations. At that anchor M/√σ = 3.84 with
Stage 2's √σ = 430 MeV: the FN glueball is an object of a few √σ,
the same scale the flux tube delivers directly. The FN model's
classical Q=1 soliton is a scalar-type object; rigid-body
quantization yields only positive parity (Amari et al. §2), so the
pseudoscalar 0⁻⁺ is *outside* the classical FN state's reach — an
honesty point, not a defect we patch over.

## Stage 4 — cross-model summary and boundary

| model | 0⁺⁺ | 2⁺⁺ | 0⁻⁺ | ordering |
|---|---|---|---|---|
| MIT bag (B, z₀ hadron-fit) | 0.97 (pre-split) | 0.97 → 1.29 (magnetic) | 1.30 | preserved |
| flux tube (σ = 0.185 GeV², swept) | 1.525 (degenerate) | 1.525 | 2.156 | preserved |
| FN hopfion (Q=1, model units) | ε = 236.5 (κ/e ≈ 7 MeV at LQCD anchor) | (rigid-body spin excitations; not computed) | **out of scope** (parity) | n/a |
| LQCD | 1.6–1.7 | 2.2–2.4 | 2.3–2.6 | — |
| BESIII candidate | f₀(1710) region | — | **X(2370) 2.395 +26/−94** | — |

Parameter honesty: every model ran with independent literature
inputs (DeGrand–Jaffe B, z₀; Sommer-scale σ; FN normalization-free
energy benchmark); residuals are reported, nothing was fitted to
BESIII or LQCD. Verdicts: all three models that can address the
ordering **preserve** 0⁺⁺ ≤ 2⁺⁺ < 0⁻⁺ — the ordering is robust
effective-model physics. Absolute levels are not: the bag is ~40%
light everywhere with its factor-~1.9 pseudoscalar problem exposed;
the flux tube is the best match (0⁺⁺ −7.6% vs window mid, 0⁻⁺ −6.2%
below the window — the only model putting the pseudoscalar near
X(2370)); the FN soliton is the only *topological* mechanism and
lands within a few % of its own continuum benchmark, but is a
scalar-sector, model-unit statement and cannot see the pseudoscalar
at all. The BESIII X(2370) pseudoscalar is best accommodated by the
flux-tube picture; the FN model speaks only to the scalar sector.

**Boundary:** these are effective models of pure glue, not LQCD. Each
fails differently and instructively — bag: confinement scale too
soft; flux tube: σ phenomenological, no spin splittings; FN: lattice
topology barrier caps the relaxation and parity blindness caps the
spectrum. What survives every model is the *ordering* and the
few-√σ mass scale; what none delivers is a controlled absolute mass.
That is where effective models end and lattice QCD begins.

## Files

- `min/glueball/bag_modes.py` — Stage 1 (run twice, byte-identical).
- `min/glueball/flux_loop.py` — Stage 2 (run twice, byte-identical).
- `min/glueball/fn_soliton.ergo` — Stage 3 engine (gradient-flow FN
  relaxation + Poisson Hopf charge; header documents the lattice
  topology-barrier study).
- `min/glueball/fn_analyze.py` — Stage 3 driver (two grids × two
  runs, byte-identical both; oracle summary).
- `min/glueball/GLUEBALL_FINDINGS.md` — this file.
