# 1SNO domain-swap trap — Hessian/dihedral anatomy + targeted torsion correction

Programs: `min/pmargin/hessian_1sno.py` (408×408 Hessian spectroscopy,
mirror of the sim's exact 7 energy terms), `min/pmargin/dihedral_1sno.py`
(per-residue dihedral/contact/Kabsch anatomy),
`min/pmargin/packed_1sno_struct.ergo` (validated `packed_1sno.ergo` +
per-block FINAL_STRUCTURE_B dump — rerun produced FINAL/DOM rows
byte-identical to the validated baseline, so all structures below ARE
the validated states), probes `tors_1sno_probe.ergo` (top-4 dihedrals),
`tors_1sno_probe8.ergo` (top-8), `tors_1sno_wrong.ergo` (wrong-position
control), all TORSK 0.2→1.0 at the stated positions, same recipe as the
BBA5 probes.

States: trap = block 4 (seed 3.0: sim 9.66 / D1 8.73 / D2 2.68;
exact SVD Kabsch 4.28 — the sim-metric inflation noted in
dihedral_check.md applies). Good = block 1 (seed 0.0, 2.05/2.34/0.77),
aux good = block 3 (seed 2.0, 2.29/2.68/0.21).

## 1. Hessian spectroscopy (408×408, good vs trap)

Method: same as hessian.py (BBA5) — energy mirror verified term-by-term
against tests/waveform_snase_seed_0.0.ergo (Morse bonds, angles,
native torsions k=0.2, hydro, Go contacts, 246 register torsions,
steric; constants identical to BBA5 except tables). 136 Cα → 408
coordinates; mixed central differences h=1e-4 (diagonals converged to
4 digits at h=1e-3..1e-5), symmetrized, numpy eigh, trace check exact.

**Cutoff artifact (methodological finding, also relevant to BBA5):**
the sim's hard steric (D=2.5) and hydro (D=8.0) cutoffs make any
finite-difference Hessian pick up spurious ΔE/h² curvature for pairs
sitting within h of a cutoff. The trap has pair 41-55 at D=2.50011 —
the untapered run produced a ±1.7×10⁵ eigenvalue pair localized at
residue 55. Fixed by tapering both cutoffs with a C¹ cosine switch over
the last 0.1 model units (energy shift ≤ 0.01); the spectra below use
the tapered mirror. The extreme TOP modes that remain (good 6360,
trap 4398) are NOT cutoffs: they localize at single residues with
near-singular local geometry — verified: good's top two modes
(6360, 1492) sit at residue 109, whose backbone angle is 179.3°
(essentially straight — the dihedral coordinate is singular there, so
the torsion potential's Cartesian curvature diverges). These are
dihedral-singularity artifacts of the coordinate, far above the
physical band (median ≈ 5), and they do not touch the soft end.

**Energies and gradients:** E(good) = 7.75, E(trap) = 40.44,
E(native reference) = 0.67. |grad| = 0.67 (good) vs 1.33 (trap).
The trap is a HIGH-ENERGY, still-relaxing kinetic plateau — consistent
with the temper report's energy-distinct finding (E≈33–36 vs 5–23),
not a compact alternative minimum.

**Spectrum — the trap is NOT a twin of the good fold:**
- Soft end: trap has 6 modes with |λ| < 0.05 (good: 3), plus ONE
  GENUINELY NEGATIVE mode (λ = −0.47) localized at residues 51/56/45
  (the fragmented segment) — a saddle direction; the trap is not even
  a local minimum along it.
- Near-zero modes at residue 91 (three modes, ~100% localized) and at
  residue 1 (the dangling N-terminus, both states).
- Mid-band: trap is STIFFER (quantile ratio good/trap 0.76–0.91 over
  q0.2–q0.8) — more constraints engaged against the contact network.
- Soft-mode localization: both states share the intrinsic hinges
  23-24 (3 soft modes each) and 79-80; the trap ADDS residue 91 (the
  untethered bead — bonds 90/91 broken, worst Kabsch residue 17.02)
  and 62 (0.77 mode).
- Term ownership (good state, Rayleigh quotients): the 12 softest
  modes are owned by torsion + angle + morse (0.1–0.7 each);
  go/hydro/register contribute ≈ 0 — the soft coordinates are backbone
  dihedral coordinates, exactly the coordinates the correction acts on,
  but they live at the hinges/breaks, not at the big dihedral
  deviations.

## 2. Dihedral anatomy — a different beast from BBA5

- **86 of 133 dihedrals deviate ≥5° from native (66 ≥10°)** — BBA5 had
  exactly TWO. Mean |Δ|: domain 1 = 23.7°, domain 2 = 10.7°, boundary
  band 93–104 = 19.6° — deviations are DISTRIBUTED across D1, NOT
  clustered at the domain boundary (top-15 has only two boundary-band
  residues: 95, 98). Good-fold noise floor: seed 2.0 mean 3.7° (17
  dihedrals ≥5°), seed 0.0 mean 8.4°.
- **Contacts: 196/197 native contacts satisfied in the trap** (mean
  |D−R0| 0.106, max 0.53), including ALL 25 cross-domain contacts
  (mean 0.101, max 0.32). The Go contact map is degenerate at 136
  residues: near-complete contact satisfaction does not imply native.
- **The decisive finding — the trap's backbone is BROKEN.** The Morse
  bond plateaus (zero restoring force beyond D≈4, cost capped at
  1.4/bond), so the field allows disconnected segments at small energy
  cost. Broken bonds (D>3) per block: block 4 (trap): **8 breaks —
  bonds 1, 8, 22, 24, 32, 72, 90, 91**, with 22/24 at D≈9 and 90/91 at
  D≈11.5 fully untethered; block 5 (seed 4.0, slow): 11 breaks; best
  folders (blocks 2, 8): only stretched (3–4) bonds plus the N-terminal
  dangle. Bond 1 (N-terminus) is broken in 6 of 8 blocks — residue 1
  sits ~20 units out and contributes ~1.7 to every full-chain RMSD (a
  measurement caveat for all 1SNO RMSD tables).
- The structure is therefore a CONTACT-SATISFIED FRAGMENTED fold:
  segments [2..~24], [~25..~90], the loose bead 91, [92..136] held
  together by the (degenerate) contact network, not by the backbone.
  The giant dihedral deviations (30: +118°, 83: +115°, 90/92: +95°...)
  are downstream symptoms of the segment rearrangement, not causes.

Anatomy comparison:

| | BBA5 trap | 1SNO trap |
|---|---|---|
| deviating dihedrals | exactly 2 | 86 (≥5°) |
| backbone | intact | 8 broken tethers (4 fully) |
| contacts | all satisfied | 196/197 satisfied |
| energy vs good fold | degenerate (energy-blind) | 40.4 vs 7.7 (distinct) |
| Hessian soft end | twin of native | softer (6 vs 3) + saddle mode |
| anatomy | global warp, native local structure | fragmented plateau, D1 segments |

## 3. Targeted torsion correction — does NOT transfer

DOM rows (full / D1 1–98 / D2 99–136), sim metric:

| block (seed) | baseline | probe top-4 (30,83,90,92) | probe8 (+58,89,9,8) | wrong (10,27,42,44) |
|---|---|---|---|---|
| 1 (0.0, gate) | 2.05/2.34/0.77 | 2.58/2.89/1.37 | **3.81/3.84/2.87 damaged** | 2.15/2.33/1.30 |
| 2 (1.0) | 3.26/3.77/0.31 | 1.62/1.68/1.30 | 1.76/1.95/0.14 | 1.96/2.26/0.16 |
| 3 (2.0, gate) | 2.29/2.68/0.21 | 2.36/2.76/0.14 | 2.21/2.59/0.10 | 2.27/2.65/0.37 |
| 4 (3.0, TRAP) | 9.66/8.73/2.68 | **10.12/8.99/2.76 — no effect** | **9.95/9.01/2.59 — no effect** | **5.99/4.33/3.00 — partial** |
| 5 (4.0) | 4.67/3.64/3.13 | 4.78/3.77/2.53 | 4.58/3.55/2.78 | 4.36/3.12/3.93 |
| 6 (5.0) | 2.96/2.82/3.02 | 2.78/2.57/2.90 | 2.41/2.25/2.68 | 3.23/3.20/3.11 |
| 7 (6.0) | 3.69/4.09/0.63 | 2.66/2.92/0.35 | 1.13/1.12/0.38 | 2.88/3.30/0.25 |
| 8 (7.0) | 2.44/1.10/6.22 | 1.76/1.26/2.21 | 3.30/2.72/3.42 | 2.42/1.98/2.63 |

- **Targeted stiffening fails to rescue**: top-4 and top-8 both leave
  the trap inside its basin (D1 8.99/9.01 vs baseline 8.73; the basin's
  cross-build band is 9.7–10.1). Native gate: probe marginal (block 1
  2.05→2.58), probe8 damages the best folder (→3.81).
- **The wrong-position control PARTIALLY helps** (D1 8.73→4.33, full
  9.66→5.99, still far from the D1<3 rescue bar) while passing the
  gate. Honest reading: two of its four positions (42, 44) sit inside
  the Kabsch-worst fragmented segment (43:10.7, 42:10.4, 44:8.6
  displacement), so the "wrong" control is accidentally a
  segment-stiffening probe. It shows (a) generic stiffening inside the
  warped segments regularizes the fold somewhat, but (b) no 4–8-point
  torsion correction closes this basin, and (c) the BBA5 targeting rule
  (rank by dihedral deviation) picks the WRONG positions in this
  anatomy — those deviations are symptoms of the backbone breaks.
- Side observation: all three variants improve several marginal blocks
  (1.0, 6.0, sometimes 7.0) — mild generic benefit of torsion
  regularization, uncorrelated with trap rescue.

## 4. Verdict

**The BBA5 targeted-torsion fix does NOT transfer to the 1SNO
domain-swap trap.** The trap is a different beast: not a smoothly
warped native-like minimum with two deviating dihedrals, but a
high-energy, contact-satisfied FRAGMENTED plateau — 8 broken backbone
tethers, 86 deviating dihedrals across D1 segments, extra soft modes
and a saddle direction at the break junctions (res 91, 51–56), stiffer
mid-spectrum against the contact network. Escape requires re-zipping
the backbone through stretched-bond states (the Morse plateau gives no
restoring force to do it), which tempering, hot windows, sustained heat
(packed_1sno_check.md), and now targeted torsions all fail to provide.
The correction anatomy that would match this trap is the TETHER, not
the torsion: (1) give the backbone bond a long-range restoring force
(the Morse plateau makes breaks irreversible at ~1.4/bond), or (2)
probe targeted bond-tether reinforcement at the observed junctions
(22-24-25, 90-91-92). Also recommended: report RMSD over residues
2..136 (the dangling N-terminal bead inflates every full-chain 1SNO
RMSD by ~1.7).

Files: `hessian_1sno.py`, `dihedral_1sno.py`, `packed_1sno_struct.ergo`
(+bin, `.out`), `tors_1sno_probe.ergo`, `tors_1sno_probe8.ergo`,
`tors_1sno_wrong.ergo` (+bins, `.out`s), `hessian_1sno.out`,
`dihedral_1sno.out`, this report.
