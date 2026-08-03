# Interface orientation terms for fold-then-dock — a clean null, and its anatomy

Programs: `min/pmargin/gen_orient.py` (quartet selection + matrix
emission), `orient_*.ergo` (+binaries/.out), analysis `orient_analyze.py`,
`orient_errmode.py`. Base: `dock_oracle.ergo` / `dock_sim.ergo`
(dock_check.md protocol: damped domains, live linkers, K_LR=0.3 tether,
white bath, 48000 frames).

## The term (documented)

Cross-domain dihedral restraints using the sim's own register-torsion
machinery verbatim (2k(1−cos(φ−p0)), frame gate). Quartet selection:
for each of the 32 cross-domain native contacts (i,j) spanning a
boundary bnd ∈ {152, 320, 440}, two quartets — (i−1, i, j, j+1) and
(i, i+1, j−1, j), extras required to stay in the contacting domains —
**53 quartets**, p0 from the crystal (force convention). The β-sheet
chirality rationale: distance-only contacts can't pick a face; signed
dihedrals can.

## The matrix (best/mean full RMSD; internal / placement; IFACE satisfaction)

| cell | init | best | mean | internal | placement | IFACE sat |
|---|---|---|---|---|---|---|
| hot baseline | oracle | 9.06 | 13.07 | 2.56 | 12.80 | 93% |
| hot baseline | sim | 9.34 | 12.46 | 2.97 | 12.08 | 92% |
| hot + orient k=0.5 | oracle | 9.08 | 12.98 | 2.57 | 12.71 | 89% |
| hot + orient k=0.5 | sim | 9.30 | 12.45 | 2.97 | 12.07 | 87% |
| hot + orient k=1.0 | sim | 9.29 | 12.43 | 2.97 | 12.05 | 88% |
| cold baseline | oracle | 9.07 | 13.06 | 2.54 | 12.79 | 92% |
| cold baseline | sim | 9.35 | 12.45 | 2.99 | 12.06 | 92% |
| cold + orient k=0.5 | oracle | 9.06 | 12.96 | 2.57 | 12.69 | 88% |
| cold + orient k=0.5 | sim | 9.29 | 12.42 | 3.00 | 12.03 | 89% |
| hot + orient EARLY k=0.5 (frame-0) | oracle | 9.08 | 12.92 | 2.57 | 12.64 | 88% |
| hot + orient EARLY k=0.5 | sim | 9.29 | 12.08 | 2.99 | 11.69 | 85% |
| hot + orient EARLY k=1.0 | sim | 9.33 | 12.29 | 2.96 | 11.90 | 84% |

**Every cell ties within noise.** Gates: hot baselines reproduce
dock_oracle/dock_sim exactly (they ARE those runs); both patches
verified in place (NREG=1801, cold schedule in source).

## Why the null is real (three diagnostics, all in Ergo/numpy)

1. **The term is active and effective at the interface**: final-state
   quartet deviation (block 4, sim init) collapses from **51.7° mean
   (29/58 > 30°) baseline to 12.9° (7/58) with the early k=0.5 term** —
   the interface's local geometry is driven to near-native.
2. **Placement doesn't follow**: same final state — per-domain COM
   errors 3.5–11.8 and relative rotations 23–35° in BOTH baseline and
   early-k05 (e.g. A3: 11.8/33° vs 11.8/32°). Domains bend internally
   (they're compliant, internal RMSD 2.5–3.5) and satisfy the interface
   restraints LOCALLY while remaining globally misplaced.
3. **The term's signal is strong**: rigidly rotating a domain by 30°
   (placement RMSD ~1.2) deviates the interface quartets by 51–90° mean
   — so the failure is not restraint insensitivity.

## Verdicts

**(a) Does the orientation term fix placement? NO** — at k=0.5 or 1.0,
gated at frame 1200 or active from frame 0. The term provably works at
what it touches (interface dihedrals 51.7°→12.9°), but rigid-body
placement is untouched: **the degeneracy is not in the restraint TYPE
(distance vs dihedral) — it is structural. Any LOCAL interface
restraint is satisfiable by compliant domains in a globally wrong
arrangement; the domains' own softness absorbs the misplacement.** This
is the 1SNO contact-degeneracy lesson one level up.
**(b) Does cold docking preserve domains? NO — cold ≈ hot identically**
(per-domain means: cold oracle 3.03/1.83/3.50/0.92 vs hot
3.02/1.85/3.54/0.92). This corrects the dock_check reading: the oracle
domains' 0→2–3.5 deformation is **force-driven, not heat-driven** — the
field relaxes the crystal geometry to its own preferred minimum; the
1200-frame ramp is irrelevant at 48000 frames.
**(c) Winning cell: none — all tie (best 9.06–9.35, no cell's placement
< 3).** The null IS the finding, and it is well-controlled (term
verified active, sensitive, early, and strong).

**What would actually move placement** (follow-ups, ordered):
(1) LONG-LEVERAGE orientation restraints — quartets with atoms far into
each domain (i, i+s, j, j−s with s ~ 30–60), which local interface
bending cannot satisfy; the 53 short-leverage quartets are the
control showing leverage is the missing ingredient.
(2) Rigid-body domain docking moves (the placement error is a
rigid-body coordinate; the sim's per-bead moves explore it at 0.5
damping with ~zero hopping — a Monte-Carlo domain move set would
address it directly).
(3) The field-ceiling connection: domain compliance is the same
force-field ceiling documented for the median seed in
sdrd_white_check.md — stiffening domain internal geometry
(angle/torsion strengths) would reduce the absorption capacity, but
risks the loop-distortion failure mode from the 1SNO tether work.

Files: `gen_orient.py`, `orient_{hot,cold,early}_*.ergo` (+binaries,
`.out`s), `orient_analyze.py` (+`.out`), `orient_errmode.py` (+`.out`),
`dock_sim_struct.ergo`, `orient_early_sim_k05_struct.ergo` (+`.out`s),
this report.
