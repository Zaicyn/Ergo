# Two-sheet steric-zipper packing test — GNNQQNY / 1YJP

Programs (min/amyloid/, from `gen_zipper.py`):
`zipper_guided.ergo` (2 sheets × 2 chains, in-register + zipper
contacts, all chains from coils), `zipper_emergent.ergo` (in-register
only, zipper contacts compiled out, measurement kept). Same force field
and schedule as the amyloid runs (12000 frames, quench 9600; runs < 1 s).
Layout: chains 1–2 = sheet 1 (crystal A, A+b), chains 3–4 = sheet 2
(2₁ screw mate, screw+b).

## Oracle contact list (extracted from pdb/1YJP.pdb crystal symmetry)

The 2₁ screw flips x,z, so facing chains run ANTI-parallel in
projection; the zipper interface is the (2,6),(4,4),(6,2) diagonal
around central residue 4. Pairs with Cα–Cα < 8 Å (target distances in
model units, ×0.400074):

| zipper contact | pair (1,3) & (2,4), m=0 | pair (2,3), m=−1 |
|---|---|---|
| A2–S6 | 7.650 Å = 3.0605 u | 7.475 Å = 2.9905 u |
| A4–S4 (central, closest) | 6.888 Å = 2.7557 u | 6.888 Å = 2.7557 u |
| A6–S2 | 7.475 Å = 2.9905 u | 7.650 Å = 3.0605 u |

Pair (1,4) (m=+1) has no Cα–Cα < 8 Å (closest 9.737 Å) → no contacts.
Total: 9 zipper contacts (3 per facing pair), ZIP_K = 1.0.

## Guided run — the model HOLDS the sheet-to-sheet geometry

Both sheets self-assemble from four independent coils (in-register mean
distance locked by frame ~600–3200 per pair) and the zipper closes.
Final zipper geometry vs target:

| contact | actual (u) | target (u) | dev |
|---|---|---|---|
| A2–S6 (pair 1,3) | 3.095 | 3.061 | +0.034 |
| A4–S4 (pair 1,3) | 2.777 | 2.756 | +0.021 |
| A6–S2 (pair 1,3) | 2.999 | 2.990 | +0.008 |
| A2–S6 (pair 2,4) | 3.054 | 3.061 | −0.006 |
| A4–S4 (pair 2,4) | 2.757 | 2.756 | +0.002 |
| A6–S2 (pair 2,4) | 2.995 | 2.990 | +0.004 |
| A2–S6 (pair 2,3) | 2.986 | 2.990 | −0.004 |
| A4–S4 (pair 2,3) | 2.736 | 2.756 | −0.020 |
| A6–S2 (pair 2,3) | 3.069 | 3.061 | +0.008 |

**All nine contacts within ±0.034 units (±0.09 Å) of the crystal
targets.** No systematic offset (deviations are centered ~0) → no
sheet slide; no alternating stretch/compress pattern → no buckle.
In-register retention in BOTH sheets: pair 1–2 k–k = 1.92–2.00 u,
pair 3–4 k–k = 1.96–1.98 u (oracle 1.9468) ✓. Closest inter-sheet
approach overall (ZMIN) = 1.918 u ≈ 4.8 Å (some off-list pair packs
slightly tighter than the central zipper contact — above the steric
floor, no clash). Stability: TRACE is flat from frame ~3200 through
quench (1.970/1.966 at 12000) — the packed double sheet holds; no
drift or rotation apart. Sheet COMs show the expected ~2-residue axial
offset between facing chains (the anti-parallel diagonal pattern) —
that is the crystal geometry, not a defect.

## Emergent run — the sheets do NOT find the zipper face

With only in-register contacts (zipper list compiled out, hydrophobic
on): both sheets assemble internally and hold register perfectly
(k–k = 1.96–1.97 in both sheets — identical to guided). But the two
sheets stay ~20 units apart all run: facing-pair distances 19.1–22.4 u
(vs targets 2.76–3.06, deviations +16 to +19 u), closest inter-sheet
approach 16.3 u ≈ 41 Å. They assembled in place and never met. The
only hydrophobic residue is Tyr7, which is NOT part of the zipper
interface (the interface is residues 2/4/6 — polar Asn/Gln) — so the
model has no attractive term that could bring the sheets together, and
none emerged.

## Verdict

- **Sheet-to-sheet geometry: the model holds it essentially exactly**
  (±0.09 Å on all 9 real crystal contacts) once the contacts exist —
  including the anti-parallel diagonal zipper pattern, planarity, and
  quench stability.
- **Emergence: zero.** The zipper is 100% contact-driven at these
  settings. Two perfectly good sheets can coexist 40 Å apart and never
  pack, because the polar Asn/Gln zipper face has no attraction in this
  force field. This mirrors the stage-1 hydrophobic negative: retention
  is proven, spontaneous zipper nucleation is not addressed by the
  model.
- Follow-ups if nucleation is ever in scope: a directional polar
  attraction between Asn/Gln amide pairs (the physical steric-zipper
  H-bond ladder), or explicit sheet-face alignment terms; longer sheets
  to test register torsion competition across the interface.

Files: `gen_zipper.py`, `zipper_guided.ergo`, `zipper_emergent.ergo`
(+binaries), `zipper_guided.out`, `zipper_emergent.out`, this report.
