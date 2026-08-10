# H₂ handshake — findings

The two-electron sequel to the H₂⁺ campaign (`HANDSHAKE_FINDINGS.md`).
Same 3D imaginary-time Schrödinger solver in Ergo, now driving a grid
full-CI in six two-center orbitals per internuclear distance R
(`min/handshake/h2_orb.ergo` — engine; `min/handshake/h2_ci.py` —
spin-adapted CI/analysis driver), preceded by an analytic
Heitler–London ladder (`min/handshake/h2_hl.py`) that calibrates every
rung against sourced literature values before the grid campaign trusts
its own integrals. Reuses the H₂⁺ production grid (NX=128, BOX=16
bohr, exact Coulomb, cell centers — no nucleus on a grid point), so
the H₂⁺ grid-convergence budget carries over: +7.4e-3 Ha per electron
at dx=0.25, extrapolation-recoverable; the one-electron oracle below
lands inside it. Determinism: no RNG anywhere (fixed sweep/step/SOR
counts); engine proven byte-identical on a reduced single-R (1.401)
variant run twice, analyzers run twice byte-identical. The production
R-scan is the reduced oracle-critical set {0.5, 1.0, 1.401, 2, 3, 4,
6} bohr (each R ≈ 9–10 min of engine time; documented per the
campaign's bounded-run rule — R=8/12 dropped, R=0.5/1.401 added).

## Stage 1 — analytic Heitler–London ladder

Closed-form two-center integrals over 1s Slater orbitals (overlap S,
one-electron A/B, Coulomb J, exchange K — K via the Euler-γ/expi form,
all verified numerically by prolate-spheroidal quadrature to ~0.5% and
by Poisson convolution to ~1–2%; the Weinbaum mixed integral M by
Poisson only). One correctness find worth recording: for ζ ≠ 1 the
cross one-electron element ⟨a|h_a|b⟩ ≠ E_1s·S; the correct form
⟨a|−½∇²|b⟩ = −ζ²S/2 + ζB gives H_ab = −ζ²S² + 2(ζ−1)SB − 2SB + K +
S²/R, which reduces to the naive form only at ζ = 1.

| rung | ansatz | result | target |
|---|---|---|---|
| 1 | HL, ζ = 1 | D_e = 3.1557 eV at R_e = 1.643 bohr | 3.13–3.16 eV @ 1.64 |
| 2 | Wang (ζ variational) | ζ* = 1.1680, D_e = 3.7843 eV at R = 1.4058; R_e = 1.413 | ζ* = 1.166, 3.78 eV, R_e = 1.406 |
| 3 | Weinbaum cov+ion CI, ζ = 1 | D_e = 3.3933 eV, cov/ion = −0.8465/−0.5323 | HL+ionic ~3.21 eV (IUPAC) |
| 3 | Weinbaum, ζ = 1.168 | D_e = 4.0545 eV, cov/ion = −0.8937/−0.4486 | Wang+ionic 4.00 eV (IUPAC) |

Missing correlation vs the exact D_e = 4.7475 eV: 1.5918 eV (rung 1),
0.9632 eV (rung 2), 0.6947 eV (rung 3, ζ = 1.168). Ionic fraction at
the minimum ≈ c_ion²/(c_cov² + c_ion²) ≈ 0.28 (ζ = 1) / 0.20
(ζ = 1.168) — the bond is mostly covalent, but the ionic structures
carry ~0.24 eV of binding at fixed ζ, and radial contraction (ζ) is
worth ~0.63 eV more.

## Stage 2 — grid full-CI (six orbitals)

Per R, the engine produces six orbitals by imaginary-time propagation
with Gram–Schmidt deflation (1σg, 1σu, and x/z-multiplied hybrids —
mixed σ/π_x symmetry), then all 21×21 = 441 two-electron integrals
(ij|kl) per R by SOR Poisson solves (NSOR=400, ω=1.8) on the product
densities with monopole+dipole boundary values, plus the ionic
integrals Θ_ij = ⟨σ_i|Θ(z<0)|σ_j⟩. The CI driver builds the
spin-adapted basis (21 singlet CSFs: 6 doubly-occupied + 15 sym
open-shell; 15 triplet CSFs) with Slater–Condon elements
(⟨ii|jj⟩ = (ij|ij), ⟨ii|jk_S⟩ = √2 (ij|ik), ⟨ij_S|kl_S⟩ = (ik|jl) +
(il|jk); triplet with the minus sign), toy-validated against
hand-computed 2-orbital matrices.

Oracles (all pass):

- **Burrau:** h(1σg) at R = 1.401 = −1.27185 Ha vs exact −1.2848
  (interpolated), dev +1.3e-2 — inside the documented dx=0.25 grid
  budget (+7.4e-3…+2.0e-2 across R).
- **Self-Coulomb:** (1σg 1σg|1σg 1σg) = 1.0402 at R = 0.5, trending to
  the He⁺ 1s united-atom limit 5Z/8 = 1.25 as R → 0.
- **Dissociation:** E_singlet(R=6) = −0.999965 Ha vs −1.0 (two H
  atoms); E_triplet(R=6) = −0.999324, both correct to ~1e-3.
- **Triplet null:** the triplet curve is repulsive at every R in both
  the 2- and 6-orbital CI (min −0.9993 Ha at R=6, approaching −1.0
  from above). No bound triplet minimum.
- **Variational:** every CI energy above the exact curve (no
  overbinding — see the bug history below).

CI ladder (D_e at the R=1.401 grid point, target R_e = 1.4011 bohr):

| orbitals | D_e | recovery vs 4.7475 |
|---|---|---|
| 2 | 2.2255 eV | 46.9% |
| 4 | 2.2642 eV | 47.7% |
| 6 | 3.2019 eV | 67.4% |

For scale: RHF H₂ D_e = 3.64 eV, Coolidge–James 4.72 eV, exact
4.7475 eV. The grid CI sits below RHF because its basis is the
*frozen* H₂⁺ orbital set (unscreened, no ζ freedom): the 1σg²
configuration alone gives only 1.90 eV here, and the added orbitals
recover another 1.3 eV by configuration mixing. Stage 1 quantifies
what the grid basis lacks: radial contraction (Wang ζ) is worth 0.63
eV and the Weinbaum result (4.05 eV with ζ + ionic in a minimal
basis) beats the 6-orbital frozen-basis CI (3.20 eV) — radial
flexibility is worth more than four extra σ/π orbitals.

Two bugs were caught by the STOP conditions during the campaign and
fixed before these numbers were produced (documented because the
oracles were what caught them):

1. `h2_orb.ergo` stored each orbital right after its last
   imaginary-time step — which comes *after* the per-sweep
   orthogonalize+normalize — so stored orbitals had norms up to 1.022
   and all h_i/(ij|kl) were inflated by norm/norm² factors. Fixed with
   a final deflation+normalization pass before storage (OVLMAT now
   reports diagonals = 1.0 and off-diagonals ~1e-15).
2. `h2_ci.py` used Coulomb integrals where Slater–Condon requires
   exchange-like ones (⟨ii|jj⟩ was (ii|jj), should be (ij|ij); same
   for ⟨ii|jk_S⟩). The unphysical 246% D_e recovery and a bound
   triplet exposed it; toy-matrix validation now guards the formulas.

## Stage 3 — two-electron handshake map

Six-orbital CI, per R (energies Ha, split in eV, ionic = P(both
electrons on the same side of the midplane) from the Θ integrals):

| R | E_singlet | E_triplet | S–T split | ionic |
|---|---|---|---|---|
| 0.5 | −0.422767 | +0.160213 | +15.864 | 0.4525 |
| 1.0 | −1.046424 | −0.604854 | +12.016 | 0.4269 |
| 1.401 | −1.117669 | −0.774287 | +9.344 | 0.3926 |
| 2.0 | −1.104895 | −0.886749 | +5.936 | 0.3429 |
| 3.0 | −1.032158 | −0.960916 | +1.939 | 0.2383 |
| 4.0 | −1.002596 | −0.987272 | +0.417 | 0.0995 |
| 6.0 | −0.999965 | −0.999324 | +0.017 | 0.0125 |

- **Ionic content dissolves with R:** 0.45 at R=0.5 (near the
  independent-electron value 0.5 of the united-atom/1σg² limit),
  0.39 at R_e, → 0.013 at R=6 (pure Heitler–London covalent: one
  electron per atom). The bond strengthens its covalent character as
  it stretches; the ionic structures are a small-R phenomenon. (The
  Weinbaum c_ion² fraction ≈ 0.20 at R_e measures a different
  projection — CSF coefficient weight in a minimal basis — the Θ map
  here is the direct spatial observable.)
- **Singlet–triplet split** falls monotonically 15.9 → 0.02 eV; no
  crossing anywhere — the singlet is the ground state at every R, and
  the exchange splitting vanishes with the 1s-tail overlap, the same
  R·e^{−R} physics as the H₂⁺ σ_g/σ_u split but now carried by a true
  two-electron (Heitler–London) mechanism.

## Stage 4 — mechanism statement and boundary

What the second electron changes: in H₂⁺ the bond was the handshake
midpoint of one electron between two Fock centers; in H₂ the same
midpoint picture holds, but the *sign* of the bond is now set by
antisymmetry — the singlet (symmetric space / antisymmetric spin)
binds, the triplet is repulsive everywhere, and the binding energy is
the exchange discount the singlet earns from the tail overlap. The
covalent structure is the whole story at dissociation (ionic → 0);
near R_e the ionic structures add ~¼ eV (Stage 1) and show up as a
0.39 same-side probability (Stage 3). What the frozen grid basis
cannot say: radial contraction (ζ optimization, 0.63 eV) and full
angular correlation are outside a six-orbital H₂⁺-frozen CI, which is
why the grid ladder stops at 67% where Weinbaum's two-parameter
ansatz reaches 85%.

Boundary: H₂ is the last exact two-center oracle. Everything from
here up (H₂⁺ → H₂ done) has closed-form or sourced-table references
at every rung; the next systems (HeH⁺, He, LiH…) have no analytic
two-center integrals — the grid engine and its oracle discipline
(overlap norms, Burrau-style tables where they exist, united-atom and
separated-atom limits, triplet-null tests, variational monotonicity)
are the calibration that has to carry over.

## Files

- `min/handshake/h2_hl.py` — analytic HL ladder (Stage 1; run twice,
  byte-identical).
- `min/handshake/h2_orb.ergo` — grid engine: 6 orbitals per R,
  Poisson/SOR two-electron integrals, THETA ionic integrals
  (production scan R = {0.5, 1, 1.401, 2, 3, 4, 6}).
- `min/handshake/h2_ci.py` — spin-adapted full-CI, oracles, ionic map
  (run twice, byte-identical; engine determinism re-checked on a
  reduced single-R variant, byte-identical).
- `min/handshake/H2_FINDINGS.md` — this file.
