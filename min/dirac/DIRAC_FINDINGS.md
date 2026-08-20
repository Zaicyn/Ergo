# Dirac campaign — findings

The atom map past the Schrödinger ceiling: a radial Dirac–Coulomb
solver in Ergo (`min/dirac/dirac_radial.ergo`), exact oracles from the
Sommerfeld fine-structure formula (closed form, all orders in Zα,
point nucleus). Ceiling re-measure for the census in
`min/dirac/ceiling.py`.

## Solver design (what's built and why)

Coupled first-order radial system for large F / small G (a.u., m=1,
c = 137.035999084 CODATA; ε = E − c² < 0 for bound states):

  dF/dr = −(κ/r)F + [2c + (ε−V)/c]G,  dG/dr = −[(ε−V)/c]F + (κ/r)G,
  V = −Z/r.

- **Origin singularity handled analytically, never clamped** (the
  helium boundary-layer lesson): outward integrations start from the
  exact small-r series F = r^s, G = q₀r^s with s = √(κ²−(Zα)²),
  q₀ = c(s+κ)/Z — this is exact as r→0, so the integrable 1/r^γ
  singularity at high Z never touches a grid clamp.
- **No variational collapse into the negative-energy sea by
  construction:** shooting (not a variational ansatz) — outward from
  the series, inward from the decaying asymptotics
  (F ~ e^{−λr}, G/F → −λc/(2c²+ε)), eigenvalue = Wronskian zero at the
  match point, found by a fixed 3000-point log scan + 60 fixed
  bisection steps. RK4 on a fixed log-t grid (NT = 20000).
- **States identified by radial node count** (never by tuning to the
  answer): n_r = n − l − 1 with l = κ (κ>0) / −κ−1 (κ<0) — the
  initial n−|κ| guess was wrong for κ>0 (it counted F's nodes; the
  large component carries l, so 2p₁/₂ has 0 nodes, not 1 — caught by
  the debug bracket table, fixed by counting over the full range
  including the inward leg). Node counts are a pure topology oracle.
- Two bugs fixed en route, both caught by the oracles: a sign drop in
  the log-midpoint bisection (geometric mean of two negative energies
  came out positive → NaN cascade) and the outward-only node counter.

## Oracle table (solver vs exact Sommerfeld, same run)

| state | solver binding (Ha) | exact (Ha) | dev |
|---|---|---|---|
| H 1s (Z=1) | 0.5000066566 | 0.5000066566 | +3.8e-13 |
| H 2s | 0.1250020802 | 0.1250020802 | −1.5e-12 |
| H 2p₁/₂ | 0.1250020802 | 0.1250020802 | −1.5e-12 |
| H 2p₃/₂ | 0.1250004160 | 0.1250004160 | +5.2e-13 |
| Pb⁸¹⁺ 1s (Z=82) | 3733.0455653 | 3733.0455653 | −2.3e-12 |
| U⁹¹⁺ 1s (Z=92) | 4861.1979044 | 4861.1979044 | −2.3e-11 |
| Si XIV 1s (Z=14) | 98.257056 | 98.257056 | +3.6e-13 |
| Si XIV 2p₁/₂ | 24.580351 | 24.580351 | −1.6e-11 |

Named oracles:
1. **Nonrelativistic limit + first-order fine structure (Z=1, 1s):**
   computed shift 6.6566e-6 Ha vs E⁽¹⁾ = (Zα)²E_n/n·[1/(j+½)−3/(4n)]
   = 6.6564e-6 Ha — agreement to 0.003% (residual is the higher-order
   part the formula drops).
2. **Fine-structure splitting:** 2p₁/₂−2p₃/₂ = 1.664160e-6 Ha =
   **4.528e-5 eV** vs the Dirac value 4.53e-5 eV (Lamb excluded,
   documented).
3. **Degeneracy:** 2s₁/₂ = 2p₁/₂ to 1.9e-16 Ha (κ=±1 — exact in
   Dirac–Coulomb; the solver reproduces it at the f64 floor).
4. **High-Z K shell (the ceiling extension):** Pb⁸¹⁺ 1s = 3733.05 Ha
   vs nonrelativistic 3362 (11% relativistic correction); U⁹¹⁺ 1s =
   4861.20 vs 4232 (15%) — measured at machine precision against the
   all-orders formula; the (Zα)² truncation visibly fails here (that
   was the point).
5. **Determinism:** two runs byte-identical (DIRAC_DET_OK).

## Census ceiling re-measured (`ceiling.py`)

Old census statement: "(Zα)² correction to Lyα passes 1% at Z = 13.7"
— a pure (Zα)² = 1% rule, no transition-level computation. With the
exact all-orders Dirac corrections:

| Z | Lyα Schrödinger error | 1s Schrödinger error |
|---|---|---|
| 13 | 0.207% | 0.226% |
| 14 | 0.240% | 0.262% |
| 26 (Fe) | 0.833% | 0.908% |
| 29 (Cu) | **1.00%** | — |
| 54 (Xe) | 3.71% | 4.05% |
| 82 (Pb) | 9.15% | 9.94% |
| 92 (U) | 11.93% | 12.94% |

**The 1% Lyα crossing sits at Z = 29 (Cu XXIX); the 1% K-shell
crossing at Z = 28 (Ni XXVIII)** — the transition correction carries a
~1/4 prefactor vs the naive (Zα)² rule, so the usable exact-map range
is twice as wide as the old estimate. `ATOM_FINDINGS.md`'s ceiling
section updated (the old line kept as the Schrödinger-limit estimate).
Engine anchors: the solver's Z=14 values match the formula at 1e-11.

## Boundary

Point nucleus throughout — at high Z the finite nuclear size matters
(Pb/U 1s shift ~1%) and is documented, not built (no nuclear charge
distribution). No QED: the Lamb shift is excluded by construction
(H 2s–2p₁/₂ Lamb splitting 1.06 GHz is absent from the model; the
2s=2p₁/₂ degeneracy we measure to 1e-16 Ha is exactly the physics QED
breaks). No many-electron Dirac–Fock — the He-campaign CI machinery
would carry it, but the screening/relaxation discipline there says
document, don't chase.
