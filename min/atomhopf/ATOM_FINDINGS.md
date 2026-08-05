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

---

# Census: how many of the 118 ground-state configurations does the map reproduce?

`python min/atomhopf/atom_census.py` (twice, byte-identical; literal
table baked with citations, no runtime fetching). Three orderings:
(a) hydrogenic pure geometry (n, then l_sub), (b) Madelung (n+l_sub,
then n), (c) the curated measured table (Madelung + 20 documented
anomaly overrides, electron-count asserted per element).

## Headline numbers

- **Geometry-pure (hydrogenic) matches: 27 / 118.** Z=1–18 (H–Ar,
  before any 3d/4s competition), then Cu(29), Zn(30), Ga–Kr(31–36), and
  Pd(46) — the Cu and Pd full-shell anomalies coincide with the
  hydrogenic order, so pure geometry accidentally recovers them.
- **Madelung (interaction patch) matches: 98 / 118.** Of which 83/102 in
  the measured range Z=1–102; Z=103–118 are Dirac–Fock predictions that
  mostly follow Madelung, so 15/16 there is partly circular.
- **Anomalies (Madelung resisters): 20.**

The 20 resisters (Madelung → actual):
Cr 3d⁴4s²→3d⁵4s¹; Cu →3d¹⁰4s¹; Nb 4d³5s²→4d⁴5s¹; Mo →4d⁵5s¹;
Ru →4d⁷5s¹; Rh →4d⁸5s¹; Pd →4d¹⁰5s⁰; Ag →4d¹⁰5s¹;
Pt 5d⁸6s²→5d⁹6s¹; Au →5d¹⁰6s¹;
La 4f¹→5d¹4f⁰; Ce 4f²→4f¹5d¹; Gd 4f⁸→4f⁷5d¹;
Ac 5f¹→6d¹5f⁰; Th 5f²→6d²5f⁰; Pa 5f³→5f²6d¹; U 5f⁴→5f³6d¹;
Np 5f⁵→5f⁴6d¹; Cm 5f⁸→5f⁷6d¹;
Lr 6d¹→7p¹ (relativistic-calculation consensus + 2015+ ionization
measurements; labeled as such).

## Layered verdict

- **Exact spectra:** 1 atom (hydrogen, 5-digit Balmer/Lyman ratios) plus
  all one-electron ions up to the relativistic ceiling — computed at
  **Z ≈ 13.7** ((Zα)² correction to Lyα passes 1% at Z=14, Si XIV;
  through Al XIII the map is exact to better than 1% with reduced mass
  alone).
- **Configurations:** 27/118 pure geometry; 98/118 with the Madelung
  interaction patch; 20 resisters by name (above) — all d/f-block
  near-degeneracy effects (half/full-shell stabilization and f/d
  reordering at the series boundaries), i.e. correlation physics the
  single-electron S³ structure cannot see.

---

# Ratchet test: how much of the anomaly census is the exchange ratchet?

Model (`min/atomhopf/exchange_ratchet.py`, twice byte-identical,
hashseed-invariant): frontier candidates (≤2-electron moves along the
measured anomaly channels ns↔(n−1)d and (n−2)f↔(n−1)d — the ns→(n−2)f
channel is excluded and disclosed, since opening it floods lanthanide
false positives with no measured counterpart), Hund-first spins,
E = Σnᵢεᵢ − K·[C(n↑,2)+C(n↓,2)] + P·(paired orbitals), argmin wins
(ties to Madelung). Curated measured table reused from atom_census.py.

## Oracles

**1. Emergence.** K=P=0 reproduces Madelung exactly (98/118 gate ✓).
With physical K the anomalies emerge — but a *uniform* gap (variant A,
1066-cell Δ×K×P×Δ_fd sweep) has **no precision-1 cell with recall > 0**:
the ratchet fires identically on Cr 3d⁴4s²→d⁵s¹ and W 5d⁴6s²→d⁵s¹
(same structure), so exactness is impossible without the series trend.
Allowing the physically known gap ordering **D₄(4d) < D₃(3d) < D₅(5d)**
(4d smallest; 5d largest via relativistic s-stabilization — variant B,
4048 cells): **precision 1.0, recall 6/20** {Cr, Cu, Mo, Nb, Ag, Pd}.
The P-channel probe adds **Gd, Cm** (f⁸→f⁷d¹ half-filled ratchet), but
always with **Tb, Bk** false positives: the same 2P that empties a pair
in f⁸ (Gd) empties one in f⁹ (Tb) via the double move — structural, so
P>Gd-threshold ⇒ P>Tb-threshold.

**2. Robustness (not a point fit).** The precision-1 region is
contiguous: K ∈ [0.25, 0.30]×Δ (≈19% relative width), P ∈ [0, 0.10],
D₄ = 0.8, D₅ ∈ {1.2, 1.5} — 16 cells, recall 6/20 throughout.

**3. Parameter sanity.** Slater-orbital exchange (Slater rules Z_eff,
exact radial F^k quadrature, Gaunt factors from direct (θ,φ) quadrature
— validated against p² ³P's canonical 3/25 and 6/25 coefficients and an
independent density-matrix sum rule): J̄(3d) = 0.93 eV,
J̄(4f) = 0.56 eV per same-spin pair. Working K = 0.275×Δ ≈ 0.28 eV at
Δ ≈ 1 eV → K_work/J̄(3d) = 0.30 — same order of magnitude (the model K
is an effective, screened exchange; a >10× discrepancy would have
rejected the fit).

**4. Verdict split.**

- **Internal (exchange ratchet): 8/20.** Clean at precision 1:
  Cr, Cu, Mo, Nb, Ag, Pd (note: Pd's extreme d¹⁰s⁰ *is* reproduced).
  Via the pairing channel with Tb/Bk companions: Gd, Cm.
- **External (needs relativity/correlation): 12/20.**
  - Ru, Rh — exchange gains below the clean window (1–2K), inseparable
    from Co-class false positives;
  - Pt, Au — same thresholds as W/Sg/Rg; what actually selects them is
    the relativistic 5d/6s structure, which the model only knows as a
    gap parameter;
  - La, Ce, Ac, Th, Pa, U, Np — f↔d orbital *ordering* at the series
    starts (the ratchet is exchange-neutral there; the f collapse is
    correlation physics);
  - Lr — relativistic 7p¹.

**5. Determinism.** Script twice byte-identical, PYTHONHASHSEED-invariant.

## Boundary statement

This is an effective two-body model (uniform K, P per subshell,
orbital-energy ladder patched by the measured Madelung order), not
first-principles: the exchange it counts is exact fermionic
antisymmetry — the double-cover structure validated on S³ — but screened
and orbitally averaged. Relativity enters only as a residual category
(Pt/Au, Lr) and as the empirically required D₅ > D₄ gap trend. That
**8 of 20 anomalies emerge from the ratchet alone over a contiguous
parameter region — including the full-shell extremes Cu and Pd — and
that the clean window cannot reach the rest without false positives**,
is the measured internal-vs-external split of the anomaly census.
