# Amide ladder term for emergent zipper nucleation — GNNQQNY / 1YJP

Programs (min/amyloid/, from `gen_amide.py`): strength bracket
(`amide_k{001,002,004,008}.ergo`), scramble controls
(`amide_scramble_{type,reg}.ergo`), close-start variants (`*_close.ergo`),
face-start register-discrimination variants (`amide_face_*.ergo`).
Base: in-register contacts ON within sheets, inter-sheet (zipper)
contacts OFF, all chains from coils except the face-start set.
Same schedule as the amyloid runs (12000 frames, quench 9600, < 1 s each).

## 1. Well geometry from the crystal (no invented distances)

Measured from `pdb/1YJP.pdb` (2₁ screw mate, the (2,6),(4,4),(6,2)
zipper diagonal):

| quantity | values (Å) | model units |
|---|---|---|
| amide N↔O across the zipper | 3.353 (A2.ND2–S6.OD1, true H-bond), 4.056/4.075 (A6–S2), 5.651–7.241 (A4–S4, A2.OD1–S6.ND2) | 1.34–2.90 |
| Cβ–Cβ of the 3 zipper pairs | 5.660 / 4.399 / 4.581, **mean 4.880, spread ±0.63** | **1.952 ± 0.25** |
| Cα–Cα of the 3 zipper pairs | 7.650 / 6.888 / 7.475 | 3.06 / 2.76 / 2.99 |

Term: Gaussian well `FM = −LADDER_K·w·EXP(−1.0·(D−1.952)²)` on the
Cβ proxy (aromatic-term pattern: Cβ = Cα + fixed native offset from
`1YJP_ca.json`). ALPHA=1.0 keeps ≥78% strength across the measured
crystal spread. Type filter: Asn/Gln only (positions 2–6). Register
weights for the anti-parallel face (2₁ screw): Δ = i+j−8; w = 1.0 at
Δ=0, 0.5 at |Δ|=1, 0 beyond (52 pairs over the 4 facing chain pairs).
Bracket: K ∈ {0.001, 0.002, 0.004, 0.008} = 0.5×–4× HYDRO_STRENGTH.

## 2. A/B emergence test — the term never engages from afar

All four strengths, from the standard coil starts (chains 10 units
apart): outputs are **bitwise-identical to the no-ladder emergent
baseline** (sheets hold internal register at kk = 1.966, facing pairs
stay 19–22 units, ZMIN 16.32). At K=0.008 as well. Reason, measured not
assumed: the Gaussian well is invisible beyond ~4 units
(EXP(−(D−1.95)²) < 0.002 at D > 4.5) and the sheets never approach
closer than ~16 units within the run. **A contact-strength well has no
capture radius** — and the earlier emergent negative is partly a
DIFFUSION limit at this timescale, now demonstrated directly.

Close-start control (chains 5 units apart): sheets relax, then sit
~10 units apart (closest approach 5.90 units ≈ 15 Å) — still beyond the
well. Identical outcomes across K=0.004/0.008 and both scrambles.
Diffusional encounter at this damping/timescale does not happen even at
half the initial spacing.

## 3. Face-start (contact distance): the ladder HOLDS but does not DISCRIMINATE

Sheets initialized at the crystal facing geometry (sheet 1 = A, A+b;
sheet 2 = screw(A), screw(A)+b; no zipper contacts anywhere):

| variant | sheet-2 offset | final ZMIN | zipper pairs (act vs tgt 2.76–3.06) | register |
|---|---|---|---|---|
| face K=0.004 | 0 (correct) | 2.69 | 2.95–4.13 | **held** (sheets stay packed through quench; ZMIN ≈ 6.7 Å ≈ crystal 6.89 Å) |
| face K=0.004 | +1 residue | 2.80 | 3.5–4.6 | **NOT restored** — offset persists (sheet-2 COM stays +1.95 u) |
| face K=0.008 | +1 residue | 2.70 | 3.5–4.4 | NOT restored (same) |
| face scr-type | +1 residue | 2.90 | 3.5–4.6 | NOT restored |
| face scr-reg | +1 residue | 2.89 | 3.5–4.6 | NOT restored |

- **Holding:** from the correct start, the ladder keeps the double sheet
  packed through quench (ZMIN 2.69 u ≈ 6.7 Å; zipper deviations
  +0.2…+1.4 u — looser than explicit contacts' ±0.034 but cohesive).
  Sheets do not buckle at any strength (in-register kk = 1.966–1.973
  everywhere).
- **Register restoration: fails at every strength.** The +1-residue
  offset remains at the end (sheet-2 COM stays shifted by exactly one
  strand spacing). The scrambles are indistinguishable from the normal
  term — the planned specificity controls are moot: there is no effect
  for them to be specific to (documented plainly).

Why the proxy cannot discriminate (the physical explanation, supported
by the numbers): a one-residue register offset moves a facing pair by
one strand spacing (1.95 u) along the fibril axis, changing the pair
distance from ~1.8–2.3 u to ~2.6–3.0 u — still inside or at the edge of
the ALPHA=1.0 well (63–94 % of peak attraction for the closest pairs).
Adjacent registers differ by only ~2× in total zipper binding, and the
slide path between them has no downhill channel at this width: the well
is simultaneously too short-ranged to capture and too wide to
discriminate. The register information in the real zipper lives in the
anti-parallel diagonal of SHORT contacts (3.3–4.1 Å amide N↔O); a
single Gaussian at the Cβ-Cβ mean (4.88 Å) smears that pattern beyond
use.

## Verdict

**Can a Cβ-level amide proxy discriminate zipper register? NO — not at
crystal-derived well width and these strengths.** It can weakly hold an
already-formed zipper against drifting apart (cohesion at contact,
stable through quench), but it captures nothing from afar and does not
correct even a one-residue register offset. Emergent zipper nucleation
therefore does NOT occur in this model with this term; the earlier
negative is refined, not reversed: what fails is not just diffusion
(diffusion fails too, demonstrated) but the term's information content
at Cβ resolution. A register-discriminating term would need to encode
the anti-parallel diagonal SHARPLY — much narrower wells at the
individual amide N↔O distances (3.3–4.1 Å) on explicit amide beads, or
directional (angle-dependent) H-bonds — both beyond the Cα/Cβ
representation.

Files: `gen_amide.py`, `amide_k{001,002,004,008}.ergo`,
`amide_scramble_{type,reg}.ergo`, `amide_{k004,k008,scramble_type,scramble_reg}_close.ergo`,
`amide_face_{k004,off1_k004,off1_k008,off1_scrtype,off1_scrreg}.ergo`
(+binaries and `.out` files), this report.
