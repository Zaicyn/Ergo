# Atom-as-hopfion verification chain — findings

Task: verify the chain Fock(S³) → hydrogen → periodic table, with the
validated double-cover machinery (min/quaternion/, commit 1e5942c) as
the spin side. Reproduce: `python min/atomhopf/atom_map.py` (twice —
byte-identical). All five items in one file; NIST literals verified
against sources before use.

## Quantum-number ↔ geometric-object mapping

| quantum object | geometric object (this chain) | status |
|---|---|---|
| shell n | S³ Laplacian level l = n−1 | exact (items 1, 2) |
| energy ∝ −1/n² | S³ eigenvalue l(l+2) = (l+1)²−1 | exact (item 2, 5 ppm) |
| shell degeneracy n² | level multiplicity (l+1)² | exact (item 1) |
| subshell l_sub = 0..n−1 | diagonal-O(3) CG tower of j×j (Hopf: left ⊕ right charge) | exact (item 4) |
| magnetic number m | M = m1 − m2 (adjoint action) | exact (item 4) |
| spin ±½ | SU(2) double cover of SO(3) | exact (2e-15, prior task) |
| period lengths 2,8,8,18,18,32 | 2n² with Madelung (n+l) reordering | exact core + interaction boundary (item 5) |

## Oracle numbers

**Item 1 — degeneracy.** (l+1)² = n² and Σ(2 l_sub+1) = n² hold as
integer identities (l = 0..6); ×2 double cover gives
{2, 8, 18, 32, 50, 72, 98}; the period lengths {2, 8, 8, 18, 18, 32, 32}
are 2n² with each value repeated — the repetition is the item-5
boundary.

**Item 2 — Balmer (real NIST data, vacuum):** five independent
wavelength ratios vs exact rationals of (1/n₁²−1/n₂²):

| ratio | measured | exact | rel dev |
|---|---|---|---|
| Hα/Lyα | 5.399993 | 27/5 | 1.2e-06 |
| Hβ/Lyα | 4.000008 | 4 | 2.1e-06 |
| Paα/Lyα | 15.428694 | 108/7 | 7.9e-06 |
| Hα/Lyβ | 6.400002 | 32/5 | 3.1e-07 |
| Hβ/Hα | 0.740743 | 20/27 | 3.3e-06 |

Worst 7.9e-06 — 5+ digit agreement. Unmodeled corrections: fine
structure (the Hα multiplet spans 0.014 Å in air), Lamb shift, reduced
mass — ppm level, as advertised.

**Item 3 — Z² (real data):**

| line | naive /Z² | +reduced mass | NIST | rel dev |
|---|---|---|---|---|
| He II Lyα | 30.39175 | 30.37937 | 30.378 | 4.5e-05 |
| He II Balmer-α | 164.11525 | 164.04841 | 164.04 | 5.1e-05 |
| Li III Lyα | 13.50744 | 13.50115 | 13.50 | 8.5e-05 |
| Li III Lyβ | 11.39689 | 11.39158 | 11.39 | 1.4e-04 |
| Li III Balmer-α | 72.94007 | 72.90610 | ~72.91 (level-derived Ritz) | 5.3e-05 |

Same S³ spectrum, E ∝ Z², residuals 4e-5–1.4e-4 (better than the
expected ~0.05%); residual sources: reduced mass (modeled), (Zα)²
relativistic/fine structure (unmodeled, ~2e-5 at Z=2). The Li III
Balmer-α reference is level-derived, not a direct line measurement —
labeled as such.

**Item 4 — subshell decomposition (the Hopf part).** S³ harmonics built
as explicit Wigner D^j_{m1,m2} matrices (little-d closed form, Euler
phases). Findings:

- *Naive right-U(1) fiber reduction fails, as the plan anticipated:* at
  integer j the invariant (m2=0) section is a single S² multiplet
  l_sub = j (dim 2j+1) — not the tower; at half-integer j the section
  is EMPTY (m2=0 ∉ lattice) — no base functions at all.
- *Correct combination (Biedenharn–Louck):* the physical O(3) is the
  diagonal of SU(2)_L × SU(2)_R — the adjoint action g → hgh⁻¹, with
  magnetic number M = m1 − m2. Measured by decomposing the adjoint
  character (built from the explicit D matrices) onto integer-spin
  characters: every level j comes out exactly j×j = 0⊕1⊕…⊕2j, CG
  coefficients = 1.0 to ≤1.1e-12. Multiplet towers: l=0: {1}; l=1:
  {1,3}; l=2: {1,3,5}; l=3: {1,3,5,7}; l=4: {1,3,5,7,9} — i.e.
  {1,3,5,…,2l+1}, summing to (l+1)² exactly. The s/p/d/f subshells are
  the diagonal-CG content of the S³ level — the two Hopf charges (left
  m1, right m2) combine into the physical (l_sub, m).

**Item 5 — ion map.** Hydrogenic order (n, then l_sub):
`1s 2s 2p 3s 3p 3d 4s …` vs Madelung (n+l_sub): `1s 2s 2p 3s 3p 4s 3d
4p 5s 4d …`. First divergence: 3d vs 4s (K, Ca fill 4s first); then 4d
after 5s (Rb/Sr), 4f after 6s (Cs/Ba). Real-atom anomalies beyond even
Madelung: Cr [Ar]3d⁵4s¹, Cu [Ar]3d¹⁰4s¹. The paragraph: the Fock/S³
structure is exact for one electron; the (n+l) reordering is where
electron-electron interaction becomes load-bearing (shielding breaks
the Coulomb O(4)); that interaction — not the hopfion core — is the
boundary of the map.

**Cross-check:** the min/quaternion spectral kernel's level/degeneracy
pairs (l(l+2), (l+1)²) match the Fock map exactly (character limits
l+1 verified numerically).

## What is exact vs what is analogy

Exact (measured here): the single-electron structure — shell and
subshell degeneracies, the Balmer/Lyman spectrum and its Z² scaling for
hydrogenic ions (ppm–100 ppm), the double-cover factor of 2, the
subshell tower as diagonal-CG content. Analogy/ boundary: multi-electron
atoms (Madelung reordering and its anomalies are interaction physics);
the Li III Balmer-α reference is level-derived.

## Sources for the real-data literals

- H I: [NIST Handbook of Basic Atomic Spectroscopic Data, hydrogen
  table 2](https://physics.nist.gov/PhysRefData/Handbook/Tables/hydrogentable2.htm)
  (air wavelengths; converted to vacuum ×1.000276); Lyα/Lyβ vacuum
  values per standard tabulations
  ([Tatum, Stellar Atmospheres 7.3](https://www.astro.uvic.ca/~tatum/stellatm/atm7.pdf)).
- He II Lyα 30.378 nm and Balmer-α 164.04 nm: standard (Tennyson,
  *Astronomical Spectroscopy*, notes the 1640 Å He II Balmer-α).
- Li III Lyα 13.50 / Lyβ 11.39 nm: NIST ASD as tabulated in
  [this compilation](https://www.preprints.org/manuscript/202407.0575/v2/download)
  (experimental column matches NIST ASD; theory 13.4953).

## Files

- `min/atomhopf/atom_map.py` — all five items + cross-check.
- `min/atomhopf/ATOM_FINDINGS.md` — this file.
