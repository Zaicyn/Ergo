# Hybrid Cα + amide-bead model — register discrimination test

Programs (min/amyloid/, from `gen_amide_beads.py`):
`bead_face_k{01,02,04}.ergo` (correct-register face start, D bracket),
`bead_face_off1_k02.ergo` (off-by-one), `bead_far_k02.ergo` (coils),
`bead_face_scramble_k02.ergo` (pseudo-beads on G1/Y7). Base: the proven
amyloid force field (in-register contacts within sheets, no zipper
contacts anywhere), 12000 frames, quench 9600, < 1 s per run.

## 1. Extracted bond machinery (from waveform_molecule_dynamics_geometric_strain.ergo)

| element | radius | homonuclear depth | valence | angle K | angle target |
|---|---|---|---|---|---|
| C | 0.76 | 1.00 | 4 | 0.35 | 109.47° (cos −1/3) |
| H | 0.31 | 1.25 | 1 | 0 | — |
| O | 0.66 | 0.42 | 2 | 0.25 | 104.45° (cos −0.2499) |
| N | 0.71 | 0.46 | 3 | 0.30 | 107.3° (cos −0.2987) |

- Combining rules: `r0(A,B,BO) = (rA+rB)(1 − 0.12(BO−1))`,
  `D(A,B,BO) = sqrt(D_AA·D_BB)(1 + 0.8(BO−1))` (bond order deepens and shortens).
- Morse: `E = D(g² − 2g)`, `g = exp(−a(r−r0))`, a = 1.0 (min −D at r0).
- Formation: distance < 2.5 AND phase alignment > 0.80 (order 1) / > 0.95 (order 1.5) AND valence free.
- Breaking: stress (1−align) > 0.05, order 0, angle strain > 0.5 (strain feeds back into topology), or out of range.
- Angle: `E = k(cosθ − cosθ0)²` with full analytic gradient; accumulated per-atom and per-bond.
- Steric: non-bonded pairs only, σ = 0.9(rA+rB), ε·(σ/r)⁶, cutoff 2.5.

**Hybrid simplification (documented):** the protein sims have no phase
machinery, so H-bond formation is DISTANCE-gated with a greedy
valence-1 rule (each amide O bonds its closest free N within 1.8 u,
inter-sheet only) instead of phase-gated; typed Morse + valence limits
+ angle terms are kept from the molecule framework. Geometric-mean
depth adapted: covalent-mean sqrt(0.46·0.42) = 0.44 is the top of the
D bracket {0.1, 0.2, 0.4} (H-bonds weaker than covalent).

## 2. Hybrid design

4 chains × 7 Cα + 40 amide beads (N and O per polar residue 2–6).
Each amide group = stiff-Morse triangle at PER-RESIDUE crystal values
(measured from 1YJP): Asn Cα–N 1.37–1.41, Cα–O 1.19–1.23, N–O
0.90–0.91; Gln Cα–N 1.92–1.98, Cα–O 1.73–1.74, N–O 0.91 (model units).
H-bond: N↔O across sheets, Morse D = HB_D, **r0 = 1.341 u = 3.353 Å
(the measured A2.ND2–S6.OD1 H-bond), a = 3.0 (narrow)**; valence 1 per
bead (greedy closest-in-range, inter-sheet only); directionality angle
terms at donor (Cα–N···O) and acceptor (Cα–O···N) with 90° target
(crystal mean 92.7°/94.5° of the two true H-bonds). Bead positions
initialized from crystal side-chain offsets (face starts) or parent
coil + offset (far start).

## 3. Results

**(a) Correct-register face start — HOLDS and engages the true zipper
pairs.** Final H-bonds (D=0.2): 5 bonds — O(c2,r3)–N(c3,r5) [3+5=8],
O(c2,r4)–N(c3,r4) [4+4=8], O(c3,r4)–N(c2,r4) [4+4=8] exactly on the
crystal anti-parallel diagonal, plus 2 near-diagonal (Δ=1) bonds. All
bond distances 1.30–1.34 u (3.3–3.4 Å, H-bond range). Sheets stable
through quench (kk 1.96–2.00; no buckling from the bead layer).
Bracket: 4 bonds (D=0.1) → 5 (D=0.2) → 6 (D=0.4).

**(b) Off-by-one face start — NOT corrected.** The +1.95 u register
offset persists to the end (sheet-2 COMs stay shifted ≈ +1.9 u). The
off-register state is NOT bond-poor: it forms 5 bonds at SHIFTED
pairings (residue sums 5–7, none at 8) with the same bond distances —
bond COUNT and energy are degenerate between registers; the contrast
lives only in pair identity and the angle term, which at K=0.3 drives
no walk back in 12000 frames.

**(c) Far start (coils) — zero bonds.** No capture (the narrow well +
the same diffusion limit documented in amide_check.md).

**(d) Scramble (pseudo-beads on G1/Y7, correct face start) — zero
bonds.** No amide partners exist within range at the wrong positions:
the effect is specific to the true Asn/Gln amide layer. The control
also passes trivially because the true zipper needs those positions.

Bug found and fixed during the work (documented): the first greedy
formation bonded every O to its own intramolecular N (0.91 u apart),
stretching each amide group toward the 1.34 u well; fixed by
restricting formation to inter-sheet pairs.

## 4. Verdict — does the atomistic amide layer discriminate register?

**Progress, with a precise residual limitation.** Against the Cβ
proxy's failure (never engaged, ~2%–37% register contrast, no
specificity), the bead layer:
- ENGAGES the crystal's actual zipper pairs at the correct register
  (3/5 bonds exactly on the anti-parallel diagonal at 3.3 Å — the
  Cβ proxy never formed anything);
- is specifically type-gated (G/Y scramble → exactly zero bonds);
- holds sheets without buckling at all three depths;
- but does NOT correct an off-by-one register and cannot capture from
  afar.

The remaining degeneracy is structural, not parametric: with valence-1
wells, a sheared sheet re-bonds shifted partners at equal count and
equal energy — the register information is present in bond IDENTITY
(the off-register bond pattern is visibly wrong, sums 5–7 vs 8), but
the energy landscape is flat between registers. Register CORRECTION
would need an energy term that prices the wrong pairings — e.g., the
register-weighted pairing list as a sparse contact mask on top of the
beads (guided, as before) or a directionality term strong enough to
tax off-diagonal bonds (the current 90° K=0.3 term does not).
So: the atomistic layer discriminates register where the Cβ proxy
could not — in the readout sense — but the hybrid model still does not
self-correct register, and the honest summary is that register selection
at this representation remains input information (contact lists or
oracle starts), not emergent physics.

Files: `gen_amide_beads.py`, `bead_face_k{01,02,04}.ergo`,
`bead_face_off1_k02.ergo`, `bead_far_k02.ergo`,
`bead_face_scramble_k02.ergo` (+binaries and `.out` files), this report.
