# Sequential amyloid assembly test — GNNQQNY / 1YJP

Programs (min/amyloid/, from `gen_amyloid.py`): `amyloid_dimer_guided.ergo`
(2 chains from coils + inter-chain in-register Go contacts),
`amyloid_dimer_hydro.ergo` (2 chains, contacts OFF — hydrophobic only),
`amyloid_trimer.ergo` (dimer template VDAMP 0.5 + chain 3 from coil),
`amyloid_tetramer.ergo` (trimer template + chain 4). Force field: the
standard recipe (Morse backbone, angles K=0.3 / torsions K=0.2 with
targets from the REAL 1YJP chain-A geometry, steric, hydrophobic,
harmonic inter-chain contacts INTER_K=1.0). Phase/Kuramoto machinery
omitted (the HB_CAP=0 recipe disables it in the protein sims too).
Thermal: heat cycles to frame 1200, floor 0.001, quench 9600/12000.
Runs are < 0.1 s each.

## Oracle (real, not synthetic)

`pdb/1YJP.pdb` (fetched from RCSB). The asymmetric unit is ONE chain;
the cross-β neighbor is the crystal b-translation (b = 4.866 Å, P2₁,
exactly the literature ~4.8 Å). Scaled to model units (×0.400074, mean
Cα–Cα bond = 1.52):
- **in-register inter-strand Cα–Cα: 1.9468 units (4.866 Å), all 7 residues exactly**;
- register discrimination in the crystal: k vs k+1 = 4.12–6.54 Å (note:
  one pair is CLOSER than the in-register 4.866 — nearest-neighbor
  register assignment is unreliable even in the real crystal; the
  register there comes from symmetry, not distance);
- sheet zipper (2₁ screw mate): closest Cα–Cα approach 6.888 Å
  (2.756 units); the literature "~10 Å sheet-to-sheet" is a mean plane
  distance — the measured closest approach in this crystal is 6.9 Å.
- intra-chain Go contacts: NONE (extended strand; |i-j|≥4 pairs are all
  beyond the 6.5 Å cutoff — strands are held by Morse/angles/torsions,
  the assembly by inter-chain contacts — physically correct for cross-β).

## Stage 1 — dimer

**Guided (in-register contacts, both chains from hash-walk coils):**
the dimer ASSEMBLES from denatured coils in under 1000 frames (mean
in-register distance 2.09 at frame 200 → locked 1.97 by ~800) and HOLDS
the cross-β geometry through quench. Final per-residue table (oracle
1.9468):

| k | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| k–k (units) | 1.966 | 1.968 | 1.964 | 1.968 | 1.964 | 1.969 | 1.959 |
| k–k (Å) | 4.92 | 4.92 | 4.91 | 4.92 | 4.91 | 4.92 | 4.90 |
| k–(k+1) | 2.77 | 2.50 | 2.10 | 2.50 | 2.06 | 2.83 | — |

All in-register distances within +1.2% of the oracle; every off-register
k–(k+1) distance is larger than its k–k — **register selected and held**.
No cross-chain register torsions needed (see notes).

**Unguided (hydrophobic only):** NO assembly. Mean in-register distance
is flat ~8.9 units (≈22 Å) for the entire run; final k–k distances
7.4–11.5 units with no register pattern; the chains sit ~8.8 units apart
(center of mass) — at best a loose end-tether via the two Tyr7 residues,
certainly not a sheet. Physically the right answer: the GNNQQNY steric
zipper is polar/H-bond driven (only Tyr carries hydrophobic weight in
the model), so pure hydrophobic attraction has nothing to build with.
This is also the needed control: the contacts in the guided runs are
doing the work — the model does not spontaneously discover cross-β
geometry from generic attraction at these settings.

## Stages 2–3 — monomer addition

Template chains start AT the oracle geometry with strong damping
(VDAMP 0.5; note: not frozen — the template expands ~7% under the
heat ramp, pair-1 mean k–k peaks at 3.28 around frame 200–600, then
re-anneals to ~1.97 by frame 2400).

- **Chain 3 (trimer):** docks in-register onto the damped dimer.
  Pair 2 (chain 3 vs template): mean k–k 4.39 at frame 200 → final
  1.954–1.972 per residue, all off-register k–(k+1) larger. Template
  pair 1 also re-settles at 1.96–1.99.
- **Chain 4 (tetramer):** same story — pair 3 goes 5.22 → 1.951–1.972;
  all three adjacent pairs end at 1.95–1.99 units.

Sheet integrity: chain centers of mass step uniformly by ≈1.95 units
per added chain (trimer COM offsets ≈ (1.2, 1.5, 0.35); tetramer
similar and regular) — the sheet grows along one axis, chains stay
parallel, no twist or slide detected within the run window.

## Geometry table vs oracle (final, model units; oracle 1.9468)

| pair | run | mean k–k | range k–k | register (k–k < k–(k+1))? |
|---|---|---|---|---|
| 1–2 | dimer guided | 1.966 | 1.959–1.969 | ✓ all 6 pairs |
| 1–2 | dimer hydro | 8.93 | 7.44–11.46 | ✗ none |
| 1–2 | trimer | 1.971 | 1.955–1.988 | ✓ |
| 2–3 | trimer | 1.965 | 1.954–1.972 | ✓ |
| 1–2 | tetramer | 1.967 | 1.951–1.978 | ✓ |
| 2–3 | tetramer | 1.973 | 1.953–1.992 | ✓ |
| 3–4 | tetramer | 1.965 | 1.953–1.970 | ✓ |

## Verdict and caveats (honest)

- The model CAN hold inter-chain cross-β geometry: guided dimer
  self-assembles from coils and retains the oracle spacing to +1.2%,
  and sequential monomer addition works through chain 4 — the
  template-and-grow mechanism the user designed for is validated.
- Assembly is CONTACT-DRIVEN, not emergent: with the contact list
  removed, nothing assembles (polar peptide, no hydrophobic core).
  The model proves retention/docking, not spontaneous cross-β
  nucleation.
- Register selection did NOT need cross-chain register torsions here:
  with 7 equal-spacing in-register contacts, the in-register
  arrangement is the unique global minimum (any shifted register
  leaves end contacts unsatisfied). The BBA5 wrong-register lesson
  will bite for LONGER peptides (where shifted/anti-parallel registers
  satisfy comparable contact counts) — that is when cross-chain
  register torsions become the documented fix.
- Not tested / follow-ups: (a) sheet-to-sheet packing (the 6.9–10 Å
  zipper spacing) — needs a two-sheet variant initialized on the 2₁
  screw-mate geometry; (b) longer peptides / anti-parallel competition
  (register-torsion fix); (c) a nucleation experiment with realistic
  H-bond-like directional inter-chain terms instead of prescribed
  contact lists; (d) template relaxation under the heat ramp suggests
  VDAMP 0.3–0.4 or a template-only gentle schedule for cleaner staging.

Files: `gen_amyloid.py`, `amyloid_dimer_guided.ergo`,
`amyloid_dimer_hydro.ergo`, `amyloid_trimer.ergo`,
`amyloid_tetramer.ergo` (+binaries), `dimer_guided.out`,
`dimer_hydro.out`, `trimer.out`, `tetramer.out`, `pdb/1YJP.pdb`,
`pdb/1YJP_ca.json`, this report.
