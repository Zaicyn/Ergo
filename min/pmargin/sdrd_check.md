# SdrD A2-A3-B1-B2 (10PS) — staged 4-domain folding test

**Size caveat (throughout):** 556 residues is 4× past the model's
validated 10–140 residue range. Null results are informative and are
reported plainly.

## Stage 1 — parse + domain boundaries

`pdb/10PS.pdb`: single chain A, 4298 ATOM records, residues 243–798
(DBREF: UniProt Q99W47 SDRD_STAAM 244–798) + a C-terminal expression
tag (residues 801–809, excluded; one numbering gap 798→801).
Cα extraction with `tools/extract_pdb_ca.py` → `pdb/10PS_ca.json`;
per-domain JSONs split from it. `mean_ca_ca` corrected to 3.8014 Å
(consecutive Cα within the construct; the file-level value 4.229 was
inflated by the tag gap — would have uniformly scaled all structures
10% small; scale = 0.399853 → 2.501 Å per model unit).

**Boundary method (documented):** no header annotation exists, so
boundaries were detected structurally — for each candidate cut, count
Cα–Cα pairs < 10 Å crossing the cut; tandem-domain linkers are deep
minima. Three minima, clean and well-separated:

| domain | residues | size | cut minimum (contacts) |
|---|---|---|---|
| A2 | 243–394 | 152 | 168 at res 395 |
| A3 | 395–562 | 168 | 81 at res 563 |
| B1 | 563–682 | 120 | 60 at res 683 |
| B2 | 683–798 | 116 | (C-term) |

These are consistent with MSCRAMM A-domain (~130–170) and B-domain
(~110–120) sizes. Sequential indices in the construct: A2 = 1–152,
A3 = 153–320, B1 = 321–440, B2 = 441–556.

## Recipe

Per domain and full construct: the proven 1SNO recipe (HB_CAP=0,
TORSK=0.2, register torsions from frame 1200 REG_K=0.5, quench at 0.8×,
MAXFRAME=48000, packed 8-seed sweep, v2 packed force kernels).
Sequential variants from `tests/generate_protein_ergo.py`
(`sdrd_*_seq.ergo`); packed variants from `gen_10ps.py`
(`sdrd_{A2,A3,B1,B2,full}.ergo`). Full construct adds per-domain RMSD
(COMPUTE_RMSD_RANGE over the four ranges above, DOM rows).

## Stage 2 — per-domain baseline (the gate): **FAIL**

Final RMSD per domain, 8 seeds (model units; ×2.501 = Å):

| domain (res) | best | median | worst | catastrophic (>10) | verdict |
|---|---|---|---|---|---|
| A2 (152) | 4.37 (s7) = 10.9 Å | ~5.8 | 9.31 (s4) | 0/8 | FAIL — all blocks ≥ 11 Å |
| A3 (168) | 2.67 (s6) = 6.7 Å | ~6.7 | 11.20 (s1) | 3/8 (s1,s5,s7) | FAIL — one mediocre fold, rest poor/catastrophic |
| B1 (120) | 2.95 (s1) = 7.4 Å | ~4.3 | 6.43 (s4) | 0/8 | borderline at best |
| B2 (116) | 3.03 (s6) = 7.6 Å | ~4.5 | 10.96 (s5) | 1/8 | borderline at best |

Reference points at validated sizes: 1SNO (136 res) good basins
2.05–2.68; GB1 (56) 0.24–2.45; BBA5 (23) ≤ 1.67. Even B1/B2 —
inside the validated size range — fold ~40% worse than 1SNO's good
basins; A2/A3 (past the 140 ceiling) are at 11–16 Å for nearly all
seeds. **The gate fails: individual SdrD domains do not reach
validated-range fold quality.** Traps are already frequent at domain
level (A3: 3/8 catastrophic).

Candidate diagnoses (ablated below): (a) recipe issue — these
β-sandwiches carry 300–576 register torsions per domain (vs 6 for
BBA5, 246 for the 136-res 1SNO), so the register term may dominate and
lock wrong registers after frame 1200; (b) landscape/size issue —
bigger, more rugged β-sandwich energy surface.

## Stage 3 — full construct (556 res): comprehensive misfold

| block | seed | full | A2 | A3 | B1 | B2 |
|---|---|---|---|---|---|---|
| 1 | 0.0 | 30.76 | 13.05 | 23.68 | 5.94 | 5.33 |
| 2 | 1.0 | 19.90 | 9.06 | 6.36 | 8.48 | 3.68 |
| 3 | 2.0 | 14.84 | 8.15 | 9.14 | 9.30 | 8.42 |
| 4 | 3.0 | 27.52 | 8.22 | 4.84 | 10.61 | 5.35 |
| 5 | 4.0 | **117.20** | 9.56 | **149.34** | **173.24** | 5.95 |
| 6 | 5.0 | 28.41 | 19.60 | 24.02 | 7.17 | 3.10 |
| 7 | 6.0 | 23.42 | 11.58 | 5.17 | 5.16 | 6.96 |
| 8 | 7.0 | 17.17 | 4.57 | 5.04 | 8.18 | 2.94 |

Full-chain RMSD 14.8–30.8 model units (37–77 Å) — misfolded on every
block, plus one catastrophic inter-domain collapse (block 5: A3 and B1
at 149/173 model units — those domains merged into a blob; B2 in the
same block is 5.95, i.e. folded independently while the middle of the
chain fused).

**In-domain vs inter-domain verdict:** BOTH fail, but differently.
Block 8 shows in-domain folds CAN survive the full construct (B2 = 2.94
≈ its standalone best 3.03; A2 = 4.57 ≈ standalone best 4.37), so the
chain does not inherently destroy domain folds. However: (i) full-chain
RMSD is 3–10× any per-domain RMSD on every block → the dominant error
is inter-domain arrangement (compact-but-wrong packings, the 1SNO
domain-swap signature at 4× scale); (ii) the single catastrophic
failure (block 5) is purely inter-domain; (iii) typical in-domain
RMSDs are somewhat worse than standalone bests (B1 8.18 vs 2.95) — the
bigger system also degrades in-domain quality through more trap
opportunities.

## Cost accounting

- Full construct: 8 blocks × 556 res × 48000 frames = **8 m 49 s**
  (biggest run in this project; the n² pair loops dominate —
  ~(556/136)² ≈ 17× the 54 s 1SNO run).
- Domains: A2 65 s, A3 78 s, B1 44 s, B2 38 s (sizes 152/168/120/116).
- Packed file sizes: full 18251 lines (840 Go contacts, 1748 register
  torsions, 4440/4432/4424 packed kernel entries/block-set);
  compile ~40 s.

## Register-torsion ablation (diagnosis test)

Domains re-run with register torsions disabled (loop gate set to frame
999999; everything else identical):

| domain | best (with reg) | best (no reg) | median (with reg) | median (no reg) |
|---|---|---|---|---|
| A2 | 4.367 | 4.997 | ~5.8 | ~6.1 |
| B1 | 2.954 | 3.621 | ~4.3 | ~5.2 |

**Diagnosis (a) REJECTED:** register torsions are not the problem —
removing them makes both domains slightly WORSE (they help here, as
they did for BBA5/WW/1SNO). The failure is diagnosis (b): the
β-sandwich landscape is genuinely too rugged for this force field at
120–170 residues — consistent with the model's documented size ceiling,
not a recipe defect.

## Stage 4 — pulse on the full construct (ω=0.002, A=0.05, backbone standing wave)

| block | seed | baseline full | pulse full | pulse A2 | pulse A3 | pulse B1 | pulse B2 |
|---|---|---|---|---|---|---|---|
| 1 | 0.0 | 30.76 | **13.22** | 12.40 | 8.09 | 6.00 | 5.83 |
| 2 | 1.0 | 19.90 | 20.62 | 8.59 | 6.68 | 7.98 | 3.89 |
| 3 | 2.0 | 14.84 | 19.98 | 5.59 | 4.97 | 13.93 | 5.86 |
| 4 | 3.0 | 27.52 | 28.16 | 8.36 | 4.89 | 6.44 | 5.52 |
| 5 | 4.0 | **117.20** | **14.17** | 11.75 | **4.27** | **5.13** | 5.66 |
| 6 | 5.0 | 28.41 | 28.96 | 19.81 | 24.57 | 7.00 | 3.38 |
| 7 | 6.0 | 23.42 | 23.17 | 6.83 | 6.43 | 6.31 | 7.67 |
| 8 | 7.0 | 17.17 | 18.88 | 4.92 | 5.19 | 7.68 | 2.83 |

**Mechanical rescue works at 556-res scale — spectacularly for the
worst block.** Block 5's catastrophic inter-domain blob (A3 = 149,
B1 = 173 model units) is completely disassembled: full 117.2 → 14.17,
with A3 and B1 ending at 4.27 / 5.13 — individually folded. Mean
full-chain RMSD improves 34.9 → 21.0; the best block improves to
13.22; nothing is made dramatically worse (worst case +4.5 on block 3).
As at 1SNO scale, the pulse does not create good folds — it prevents
catastrophic wrong-packings and lets marginal blocks settle better.

## Overall verdict

- **Per-domain gate: FAIL** — SdrD β-sandwich domains do not reach
  validated-range fold quality (best 6.7–7.4 Å on the two in-range
  domains; A2/A3 ≥ 11 Å nearly everywhere). This is a landscape/size
  limitation, demonstrated (not asserted): the register-torsion
  machinery that handles BBA5/WW/1SNO helps here too, just not enough.
- **Full construct:** misfolds on all blocks (37–77 Å), with
  inter-domain arrangement the dominant error (full RMSD 3–10× the
  per-domain RMSDs; block-8 shows in-domain folds CAN survive — B2
  2.94 ≈ standalone 3.03) and one pure inter-domain catastrophe.
- **Pulse:** eliminates the catastrophe and improves the mean 34.9 →
  21.0 — mechanical rocking remains the best rescue tool at 4× the
  validated size.
- **Null result is the finding:** at 556 residues / 4 domains the model
  is past its reach for production-quality folds; it remains useful at
  this scale for trap MECHANICS (domain-swap detection, pulse-response
  studies), not for structure prediction.

Files: `gen_10ps.py`, `sdrd_{A2,A3,B1,B2,full}_seq.ergo` (sequential
variants), `sdrd_{A2,A3,B1,B2,full}.ergo` (+binaries),
`sdrd_{A2,B1}_noreg.ergo` (+binaries), `sdrd_full_pulse.ergo` (+binary),
`pdb/10PS_{A2,A3,B1,B2,full}_ca.json`, `sdrd_*.out`, this report.
