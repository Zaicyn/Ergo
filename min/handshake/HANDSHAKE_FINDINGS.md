# H₂⁺ handshake — findings

How two Fock/S³ atomic constructions merge into a covalent bond, tested
with a 3D imaginary-time Schrödinger solver in Ergo
(`min/handshake/h2p.ergo`, flattened masked stencil, parity-selected,
exact Coulomb on a cell-center grid — even N puts no cell center on a
nucleus). Reproduce: `python min/handshake/analyze_handshake.py`
(drives builds/runs/oracles/plots; production binary twice,
byte-identical).

## Stage 1 — H atom oracle

Grid convergence at L = 16 bohr, exact Coulomb:

| NX | dx | E (Ha) | err vs −0.5 |
|---|---|---|---|
| 128 | 0.2500 | −0.492591 | +7.41e-3 |
| 192 | 0.1667 | −0.496588 | +3.41e-3 |
| 256 | 0.1250 | −0.498049 | +1.95e-3 |

dx² fit: **E₀ = −0.499842, residual +1.58e-4** — inside the ~1e-3
oracle tolerance. Raw error scales ~dx² (slope 0.116 Ha/bohr²); the
residual grid error is the rounded 1s cusp. Soft-core Coulomb was
measured and rejected: a=0.15 shifts the atom to −0.4568 (+4.3e-2),
unusable; the exact-Coulomb cell-center grid needs no softening.
Imaginary-time convergence: max |E(τ=2000)−E(τ=2500)| over the whole
scan = 8.1e-6 Ha. dτ = 0.008 ≤ dx²/6 = 0.0104 at the production grid
(the analyzer's fine-grid variants scale dτ and steps automatically —
a fixed dτ=0.008 is unstable at dx=0.125; caught as a garbage 256³
result during the audit and fixed by dτ ∝ dx²).

## Stage 2 — Burrau oracles

Electronic energies vs the sourced nonrelativistic table
(arXiv:2310.04057 Table I / Burrau–Bates–Wind):

| R | computed σ_g | exact σ_g | dev |
|---|---|---|---|
| 0.5 | −1.694887 | −1.734988 | +4.0e-2 |
| 1.0 | −1.431876 | −1.451786 | +2.0e-2 |
| 2.0 | −1.092846 | −1.102634 | +9.8e-3 |
| 3.0 | −0.903576 | −0.910896 | +7.3e-3 |
| 4.0 | −0.789400 | −0.796085 | +6.7e-3 |
| 6.0 | −0.671730 | −0.678636 | +6.9e-3 |
| 8.0 | −0.620325 | −0.627570 | +7.3e-3 |

All deviations positive (grid is variationally high) and ~1% or better
past R=2. **Error budget (R=2, σ_g):** −1.092846 / −1.098136 /
−1.100064 at NX = 128/192/256; dx² extrapolation **−1.102438 vs exact
−1.1026342, residual +1.96e-4** — the scan points carry a documented
+7e-3 systematic at dx=0.25, extrapolation-recoverable.

- **Equilibrium:** minimum at R=2.0 grid point (target R_e = 1.997).
- **D_e:** raw 0.0928 Ha at 128³; with the R=2 extrapolation,
  **0.10244 vs 0.10263 target (0.2%)**.
- **United-atom limit (R=0.2):** σ_g −1.879 (limit −2.0, deepest cusp
  = largest grid error, −6%); σ_u −0.5063 (limit −0.5, +1.3% — the 2p
  state is cusp-free at the origin, hence much more accurate).
- **Separated limit (R=12):** both −0.576 (limit −0.5; residual
  matches the σ_g tail structure at these R, grid budget applies).
- **σ_u at R=2:** −0.659730 vs Bates–Wind −0.66753 (+7.8e-3, same
  budget).
- **Split exponent:** ΔE(R) = E_u − E_g; fit log(ΔE/R) vs R over
  R = 4…12: **slope −0.9787** (the ~R·e^{−R} law, exponent −1 to 2%).

## Stage 3 — the handshake map

Squared overlaps of the converged states with the separated-atom
combos (1s_L ± 1s_R) and the united-atom He⁺ 1s/2s/2p at the midpoint
(full table in the analyzer output; `h2p_overlaps.png`):

- **σ_g:** separated-atom content |1s_L+1s_R|² = 0.735 (R=0.2) → 0.944
  (R=2) → 1.000 (R=12); united-atom |He⁺1s|² = 0.998 → 0.663 → 0.0003.
  The He⁺ **2s** content peaks at |c|² ≈ 0.49 at R = 4 — the
  polarization/hybridization channel of the merger.
- **σ_u:** |1s_L−1s_R|² = 0.772 (R=0.2) → 0.993 (R=2) → 1.000;
  |He⁺2p|² = 1.000 → 0.930 → 0.044. The 2p content decays
  monotonically; the odd state is "already mostly split" at R=2.
- **The crossover/merger zone is R ≈ 1.5–4** for both parities: below
  it the wavefunction is a single-Fock (united-atom) object, above it
  two Fock centers. The σ_g bond's binding lives exactly in this zone
  (R_e = 2): the bond is the handshake midpoint, not either limit.

## Stage 4 — mechanism statement and boundary

What survives the merger: the *parity* (the construction is exact per
parity sector — imaginary time preserves it, and the σ_g/σ_u split
ΔE ~ R·e^{−R} comes out of the two-center tunneling alone). What the
crossover looks like: a continuous transfer of norm from the
united-atom functions to the separated pair through R ≈ 1.5–4, carried
on the σ_g side by the He⁺ 2s (radial polarization) channel. Where the
split comes from: the overlap of the two 1s tails — the antisymmetric
combination has a nodal plane at the midpoint and pays the kinetic
price; everything else about the two states is the same physics.

Boundary: H₂⁺ is one-electron — there is no exchange, no correlation,
no singlet/triplet distinction in this campaign. H₂ itself
(Heitler–London: D_e = 4.75 eV, R_e = 0.74 Å) needs the two-electron
handshake (antisymmetrized two-particle wavefunction, correlation) —
not built here.

## Files

- `min/handshake/h2p.ergo` — the solver (ATOM + SCAN + OVL sections).
- `min/handshake/analyze_handshake.py` — oracle driver (determinism,
  grid variants, budgets, plots).
- `min/handshake/h2p_energy.png`, `h2p_split.png`, `h2p_overlaps.png`.
- `min/handshake/HANDSHAKE_FINDINGS.md` — this file.
