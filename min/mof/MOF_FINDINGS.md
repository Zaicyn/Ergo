# MOF campaign — findings

Porting the trimer PME setup onto MOF secondary building units.
Reproduce: `python min/mof/fe3o_compare.py` (Stage 1 oracles),
`python min/mof/mof235_framework.py` (Stage 2), `python
min/mof/mof5_geometry.py` (Stage 3). All drivers run twice,
byte-identical; analyzers deterministic.

## Stage 1 — Fe3O SBU

**ED oracle (`fe3o_ed.py`, 216 states, dense).** H = −2J Σ S_i·S_j
(molecular convention; J<0 = AF). Sign note: the plan's ladder
E(S) = J/2·[S(S+1)−const] with J<0 would put the AF ground state last;
the physical AF requirement (S_T=1/2 ground) fixes the convention —
H = −2J with J<0 gives E(S) = −J[S(S+1)−3s(s+1)]. All 8 multiplets
match the ladder to machine precision with CG-enumerated
multiplicities m(S_T) = {2,4,6,5,4,3,2,1}: ground = S_T=1/2, two
doublets (degeneracy 4); E(3/2)−E(1/2) = 75.000000 = −3J exactly
(ratio 1.000000000). The Wigner flip-flop builder was validated
against the spin-1/2 trimer first (caught two real bugs).

**Ergo PME (`fe3o_sbu.ergo`).** Ladder + canonical Boltzmann sums +
Pauli master equation over the 8 multiplets (adjacent-S_T bath
transitions, detailed balance with degeneracy factors).
`fe3o_compare.py` verdicts (PASS):
- LADDER vs ED: max |ΔE| = 0.00, multiplicities all equal.
- CANON vs ED canonical χ: max rel dev 2.6e-7 (μ_eff 1.3e-7).
- PME steady state vs canonical: χ identical, populations to 5e-11.

**Susceptibility.** Low-T limit: μ_eff/Fe → 1.00 μB (S_T=1/2 doublet
ground; per-trimer 1.73). High-T: μ_eff/Fe = 5.875 at 30 000 K vs
exact g√(s(s+1)) = 5.9161 — ratio 0.993, monotonically converging
(5.793 @10⁴ K, 5.875 @3×10⁴ K). The asymptote is only reached at
T ≫ |J|/k_B — documented as convergence, not claimed at 300 K.

**J from literature/measurement.** MOF-235's measured μ_eff per Fe:
3.23 μB at 300 K, 1.95 μB at 5 K
([Sudik et al., Yaghi lab](https://yaghi.berkeley.edu/pdfPublications/MOFtrigonal.pdf)).
Fitting the isolated-SBU 300 K point gives **J = −30.968 cm⁻¹**
(H=−2J convention; comparable Fe₃O-trimer fits give ~−12 cm⁻¹ under
−2J-style conventions for different compounds — convention mapping
documented in the file). Isolated-SBU prediction at 5 K: 1.00 vs
measured 1.95 (see Stage 2 for the counterion interpretation).

**Mixed-valence port (the trimer PME port proper).** 8 charge states
(bit i = Fe²⁺ on site i), EPS0 = +30 meV (intervalence on-site, ABOVE
the bath so the substrate only removes — the trimer_pme structure:
in via gate, out via substrate), W = 50 meV, kT = 26 meV (300 K),
substrate on all sites at GS = 1.0 / μ_S = 0, gate at site 3 with
GT = 0.5 / μ_T = +150 meV, LAM = 5 meV stabilizing site 1. All
ASSUMED and flagged; BDC linkers are coupling channels only.

**Intervalence-channel ablation (Robin–Day):** sweeping G_IT from
1e-6 to 10 (≫ GS): the gate-fed electron is kinetically trapped at
the gate vertex (P1C = 0.653, DELOC = 0.513) at 1e-6 and delocalizes
to ~1/3 (P1C = 0.331, DELOC = 0.665) by G_IT = 10; the gate current
rises 0.263 → 0.344 (delocalization opens conduction). G_IT ≥ 1e-3
reproduces the canonical Boltzmann sector exactly
(P1A/B/C = 0.377/0.311/0.311 = e^{LAM/kT} tilted). Class III ↔ I/II
transition measured as a smooth crossover between G_IT/GS ~ 0.01–1.

**Upstream flag:** the porosity channel in `min/trimer_pme.ergo`
uses rate f(−ΔE) for inter-site hops with the comment
"detailed-balance preserving" — that form favors UPHILL moves
(anti-Boltzmann; verified numerically: Boltzmann is not stationary
under it). The MV port uses the DB-correct f(ΔE). If the trimer_pme
ablation numbers are load-bearing elsewhere, revisit them.

## Stage 2 — MOF-235 framework (2 SBUs)

`mof235_framework.py`: 6 × S=5/2, 46 656 states, sector-wise dense ED
by total M. One effective Fe–Fe inter-SBU bond with J′ (3 BDC linkers
folded into one swept channel — documented simplification). J′ swept
{0.05, 0.1, 0.2}·|J| with J = −30.968.

- **J′=0 control:** framework == isolated to 4 digits at every T
  (validates the sector ED).
- **Oracle — high-T Curie constant:** framework/(2×isolated) ratio
  1.0024 at 3000 K, 1.0003 at 30 000 K — untouched by J′ as required.
- **Low-T modification (measured):** μ_eff/Fe ratio vs isolated at
  1 K: 0.099 (J′=0.05), 0.021 (J′=0.1), 0.006 (J′=0.2) — the AF
  inter-SBU coupling suppresses the low-T moment as required.
- **MOF-235 measured comparison (J′=0.1):** 300 K: 3.2437 vs measured
  3.23 (0.4%); 5 K: 0.608 vs measured 1.95. The 5 K residual is NOT
  fixable by J′ (more AF coupling only suppresses further) — the
  natural explanation is the [FeCl₄]⁻ counterion (one free S=5/2 Fe
  per trimer in the reported formula): a simple mixture estimate,
  μ² = (3·μ_tr² + μ_free²)/4, gives 3.0 — over-predicting (partial
  guest occupancy/ordering would lower it). Both directions documented;
  not tuned.

3 SBUs (10M states) were not built — stopped at 2 per the plan's
fallback (sector-wise dense ED at 46656 states; the 10M-state problem
would want the sparse/ED-engine route).

## Stage 3 — MOF-5 geometry

`mof5_geometry.py`: Zn₄O(BDC)₃, pcu, from bond lengths/angles
(documented per line):

- **Lattice parameter:** the Zn–O–C arm length is 4.713 Å; the arm
  angle vs the pcu edge is the one structural input. Bracket: naive
  collinear 30.37 Å (+17.7%), arm-along-(111) 22.40 Å (−13.2%), and
  with the arm angle (43.8°) from the measured centroid→C = 3.4 Å:
  **a = 25.12 Å (−2.6% vs 25.669–25.92)**.
- **Density:** at model a: 0.645 g/cm³ (+9.4% vs 0.59);
  at literature a: **0.605 g/cm³ (+2.5% vs 0.59)**.
- **Pore aperture:** square-window estimate (4 BDC rods spanning the
  node–node gap): **6.76 Å (−16% vs ~8 Å)**.
- **Surface area:** flat-slab geometric model **2448 m²/g vs 2900
  Langmuir (−16%)** — geometric estimates run low because the Langmuir
  monolayer follows the corrugated vdW surface; documented, not tuned.
- Cavities: large ~15.0 Å (lit ~15), small ~9.6 (lit ~11).

## Parameters & sources

| parameter | value | source |
|---|---|---|
| S per Fe | 5/2 (Fe³⁺ high-spin d⁵) | standard |
| g | 2.0 | standard |
| J (intra-SBU) | −30.968 cm⁻¹ (H=−2J) | fitted to MOF-235 300 K μ_eff (Sudik 2005) |
| MOF-235 μ_eff | 3.23 (300 K), 1.95 (5 K) per Fe | Sudik et al. (Yaghi lab), 5 kG, 5–300 K |
| J′ | 0.05–0.2·\|J\| swept | plan |
| MV model (EPS0, W, LAM, GT, MU_T) | +30, 50, 5, 0.5·GS, +150 meV | ASSUMED — flagged |
| MOF-5 a / ρ / area | 25.669–25.92 Å / 0.59 / 2900 m²/g | Yaghi group lit |

## Files

- `min/mof/fe3o_sbu.ergo` — spin ladder + canonical χ + multiplet PME
  + mixed-valence PME port (two-bath gate model).
- `min/mof/fe3o_ed.py` — ED oracle (216 states), J fit, reference dump
  (`fe3o_ref.txt`).
- `min/mof/fe3o_compare.py` — Stage-1 oracle runner.
- `min/mof/mof235_framework.py` — Stage-2 2-SBU ED + oracles.
- `min/mof/mof5_geometry.py` — Stage-3 geometric model.
- `min/mof/MOF_FINDINGS.md` — this file.

## Postscript — trimer_pme.ergo rate inversion FIXED

The flagged anti-Boltzmann porosity channel (`FERMI(0.0 - DE)` favoring
uphill hops) is fixed in `min/trimer_pme.ergo` (`FERMI(DE)`); the
original is preserved as `min/trimer_pme_orig.ergo`. Rate-level oracle:
with the tip over site 1 (E2 = −29.25, E3 = −59.65 meV), the fixed
RH(2,3) = 1.0 / RH(3,2) = 0 (downhill favored) vs the original's exact
inverse. Behavioral effect at G_HOP = 1.0: trapped w_singlet drains to
~0.006–0.009 (was ~0.019–0.028 with the inverted channel). Conclusions
drawn from the original POROSITY ablation should be re-evaluated.
