# Helium campaign — findings

The two-electron atom, done radially: the handshake machinery
(3D imaginary-time + Poisson two-electron integrals + spin-adapted CI
from `min/handshake/`) specialized to one center, where everything is
1D and the accuracy jumps accordingly. Engine `min/helium/he_orb.ergo`
(radial orbitals + all Slater integrals), analysis
`min/helium/he_ci.py`. Determinism: engine and analyzer each run
twice, byte-identical (Z=2 and Z=3).

## Stage 1 — radial orbital engine

Uniform radial grid in u(r) = r·R(r), node exactly at r = 0
(u(0) = 0 is exact — the first version clamped u at the first cell,
a fake boundary layer that cost 5% on the s orbitals; moving the node
to r = 0 fixed it). Imaginary-time Euler, 5-point Laplacian,
Gram–Schmidt deflation within each l block, step count scaled with n
(the near-degenerate n=3 shell converges slowly).

He⁺ ladder vs exact −Z²/2n² (Z = 2):

| orbital | computed | exact | dev |
|---|---|---|---|
| 1s | −1.99998144 | −2.0 | +1.9e-5 |
| 2s | −0.49993932 | −0.5 | +6.1e-5 |
| 2p | −0.49999999(95) | −0.5 | +5e-11 |
| 3s | −0.22203183 | −0.22222222 | +1.9e-4 |
| 3p | −0.22206719 | −0.22222222 | +1.6e-4 |
| 3d | −0.22222222(22) | −0.22222222 | +1e-12 |

Grid budget: ≤ 2e-4 Ha everywhere (s orbitals carry it — the cusp at
Z=2 wants more points per bohr; p/d are centrifugally kept off the
origin and are exact to 1e-10+).

Poisson/integral oracles (cumulative Y^k form, trapezoid):
F⁰(1s,1s) = 1.250135 vs closed-form 5Z/8 = 1.25 (dev 1.3e-4).
Cross-checks vs analytic hydrogenic quadrature: R¹[1s2p] dev 7.6e-6,
R⁰/R²[2p2p] dev 9e-6 / 5.7e-6, 3d block dev ≤ 6e-7. Same code at Z=3
(sed the PARAMETER, nothing else): ladder ≤ 1.4e-4, F⁰ = 1.875455 vs
1.875 (5Z/8, dev 4.5e-4) — the isoelectronic construction needs no
refitting.

## Stage 2 — CI ground state

Spin-orbital determinants; two-electron matrix elements from the exact
2-particle expansion (⟨ab|H|cd⟩ with parity-tracked canonical
ordering); spatial integrals (pr|qs) = Σ_k M^k·R^k[pr,qs] with the
angular factors M^k from the spherical-harmonic addition theorem and
1-sphere Gaunt quadrature. Angular machine certified end-to-end:
M⁰(ssss) = 1 exactly; the doubly-occupied ¹S pair energies match the
textbook coefficients to all printed digits — 2p² ¹S = F⁰ + (2/5)F²,
3d² ¹S = F⁰ + (2/7)(F² + F⁴) (both ratios 1.00000000; the signs are
the correct Hund ordering, verified by an independent direct 4D
angular quadrature of the L=0-coupled pair functions). Coupling
oracles: ⟨1s²|H|2p²⟩ = −5.9e-2, ⟨1s²|H|3d²⟩ = 1.1e-3 (nonzero, small).

Ground-state CI (¹S CSFs 1s², 1s2s, 2s², 1s3s, 2s3s, 3s², 2p², 3p²,
3d²), fixed bare-hydrogenic orbitals:

| basis | E₀ (Ha) | recovery from 1s² |
|---|---|---|
| 1s² alone | −2.749828 | — |
| s block | −2.840499 | 58.9% |
| s+p | −2.843070 | 60.6% |
| s+p+d | −2.843070 | 60.6% |
| HF limit | −2.8617 | (unreachable here) |
| exact (Pekeris) | −2.903724 | 100% |

Variational monotonicity holds (every value above exact; no
overshoot). Two distinct gaps, quantified: (a) **fixed-basis radial
gap** — the bare Z=2 orbitals cannot relax, so the HF limit −2.8617
is out of reach by construction; our CI stops 0.019 Ha above it; (b)
**cusp/partial-wave gap** — p and d partial waves add only 0.0026 Ha
at this basis size; the remaining 0.061 Ha to exact is the
correlation-cusp slow convergence (the documented ~l⁻⁴ tail), which
this small basis samples but does not chase. The s-block radial CI
carries 59% of the 1s²→exact gap; angular correlation is a small
correction on top at fixed radial flexibility.

## Stage 3 — singlet/triplet and isoelectronic

**He 2¹S/2³S (1s2s):** E(2¹S) = −2.031569, E(2³S) = −2.121156 Ha;
splitting = 0.089587 Ha = 2.438 eV vs NIST 0.796 eV (0.02925 Ha).
First-order analytic check (our quadrature): J(1s,2s) = 0.419753,
K(1s,2s) = 0.0438957 → 2K = 0.0878 Ha — the engine matches its own
first-order value; the 3× overshoot vs NIST is the known
bare-basis artifact: the true 2s electron sees a screened core
(Z_eff ≈ 1), shrinking the 1s–2s exchange. Documented, not chased
(screening = refitting).

**Li⁺ (Z=3), same code, no refitting:** 1s² = −7.124267;
s-block CI −7.198520; s+p = −7.200492 vs HF limit −7.23642, exact
−7.279913 (49% recovery from 1s²). Same structure as He — the
construction transfers.

## Stage 4 — boundary

Two electrons is where this stays cheap: the CSF count at fixed
angular cutoff is combinatorial in the electron number, and the
next element up (Be, 4 electrons) is where interactions rule — per
the census, that is where the handshakes stop being analytic and the
campaign machinery (GPU ED, DMRG) has to take over. The radial engine
itself extends trivially (same orbitals, more CSFs); the factorial
wall is the CI assembly, not the integrals.

## Files

- `min/helium/he_orb.ergo` — radial engine (orbitals + R^k integrals;
  Z is a build-time PARAMETER; Z=2 and Z=3 builds run twice,
  byte-identical).
- `min/helium/he_ci.py` — angular machinery + CI + Stage 3 (run twice,
  byte-identical).
- `min/helium/HELIUM_FINDINGS.md` — this file.
