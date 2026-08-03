# Directionality tax — register-offset-priced amide wells

Programs (min/amyloid/, from `gen_tax.py`): bracket TAX ∈ {0 (gate),
0.1, 0.25, 0.5, 1.0, 2.0} × D (=0.2) at off-by-one and correct starts,
plus wrong-diagonal scramble (DIAG=10). Everything else identical to
the bead model (narrow Morse at 1.341 u, valence 1, greedy formation,
12000 frames, quench 9600, < 1 s per run).

## Tax formula (documented)

For an amide bond between residue i (sheet 1) and residue j (sheet 2),
the register offset from the crystal anti-parallel diagonal
(i + j = 8 — the (2,6),(4,4),(6,2) pattern) is

  OFF = |i + j − DIAG|,  DIAG = 8 (10 for the scramble control)

and the effective well depth is `D_eff = D·(1 − TAX·OFF)`. At the well
bottom this is exactly E = −D + TAX·D·OFF (the prescribed penalty:
wrong pairings possible but expensive). D_eff enters BOTH the greedy
bond choice (each O bonds the in-range inter-sheet free N with the
highest score DEFF·EXP(−HB_A·(D−HB_R0)), only if score > 0) AND the
Morse force. No register masking, no forcing — any pair may form if it
pays. Bond energy for the gap: E = DEFF·(g² − 2g) per bond.

**Init bug found and fixed (documented):** sheet-2 amide beads were
initialized with unflipped side-chain offsets — the 2₁ screw flips x,z
so sheet-2 beads sat on the wrong side of their Cα. This corrupted the
earlier bead experiment's initial geometry (its bonds formed only after
leash relaxation); all results below use the flipped init, and the
TAX=0 gate re-establishes the bead phenomenology on the corrected
geometry.

## Gate (TAX=0)

Off-by-one persists (sheet-2 COMy ≈ 4.68 vs correct ≈ 2.4–2.5), 4
bonds (2 diagonal + shifted), EBOND −0.70 — the isoenergetic
re-bonding of the bead experiment, on corrected geometry. ✓

## Bracket table

Correct start:

| TAX | NHB | diagonal bonds (sum 8) | EBOND | sheet-2 COMy |
|---|---|---|---|---|
| 0 | 7 | 2 | −1.396 | 3.08 |
| 0.1 | 7 | 3 | −1.229 | 3.06 |
| 0.25 | 7 | 2 | −0.889 | 2.88 |
| 0.5 | 3 | **3 (only s8)** | −0.599 | 2.42 |
| 1.0 | 3 | 3 (only s8) | −0.599 | 2.37 |
| 2.0 | 3 | 3 (only s8) | −0.599 | 2.37 |

Off-by-one start (correct register ≈ 2.4; start 4.82):

| TAX | NHB | EBOND | COMy(final) | COMy trajectory |
|---|---|---|---|---|
| 0 | 4 | −0.705 | 4.68 | flat (no drift) |
| 0.1 | 4 | −0.649 | 4.68 | flat |
| 0.25 | 4 | −0.616 | 4.65 | 4.82→4.65, slow |
| 0.5 | 1 | −0.198 | 4.35 | 4.82→4.29 (f=10000) → rebound 4.35 |
| 1.0 | 1 | −0.198 | 4.34 | same profile as 0.5 |
| 2.0 | 1 | −0.198 | 4.34 | same |

Scramble (DIAG=10, TAX=0.5): **0 bonds at both starts** — correct
pairs (sum 8) pay |8−10|·0.5·D = D → DEFF = 0 → nothing binds. The tax
carries the information, not generic stiffness. ✓

## Findings

1. **The tax works as a selector.** At TAX ≥ 0.5 the correct start
   retains ONLY true crystal H-bonds (the (2,6)/(6,2) diagonal; the
   central (4,4) never bonds because its crystal distance 5.65 Å is
   outside the 4.5 Å range — physically consistent, it is not an
   H-bond in the crystal either). Off-diagonal bonds are priced out
   exactly as designed. At TAX = 1.0 vs 2.0 nothing changes (Δ=1
   pairs are already DEFF ≤ 0 at 1.0).
2. **The degeneracy is broken energetically** — a gap exists at every
   level (correct vs sheared EBOND: −1.40/−0.70 at TAX=0 →
   −0.60/−0.20 at TAX ≥ 0.5). Note the gap does NOT open cleanly with
   tax (pruning shrinks both states; measured gap 0.69 → 0.40) — the
   pre-registered prediction holds only qualitatively.
3. **Correction begins but does not complete.** The off-register
   offset shrinks monotonically with tax (final COMy 4.68 → 4.68 →
   4.65 → 4.35 → 4.34) and the TAX ≥ 0.5 trajectories show a real
   slide (4.82 → 4.29 by frame 10000) — then a rebound to ~4.35 and a
   stall. Net correction ≈ 20–25% of the 1.95 u offset. Sheets stay
   intact throughout (kk 1.96–1.99; no buckling from the tax).

## Verdict — outcome class (iii), leaning (i)

The hypothesis is partially confirmed and precisely falsified where it
fails: the tax DOES break the isoenergetic degeneracy (energetic gap
plus clean diagonal selection at TAX ≥ 0.5), and a downhill channel
opens — the offset decays monotonically for thousands of frames. But
correction stalls at ~25% with a rebound, at every tax level. The
remaining barrier is kinetic, not energetic: completing the slide
requires breaking the last diagonal bond while shearing a full strand
spacing against tethers/sterics, and the quench-floor thermal budget
(0.001 × 12000 frames) does not cross it. The tax window where the
physics is clean is TAX ≈ 0.5 (full diagonal selection, drift
strongest); more tax (≥ 1.0) changes nothing. Named next levers:
longer anneal (the drift was still moving at f=10000), or a pulsed
rocking to cross the slide barrier — the validated pulse is the
obvious candidate.

Files: `gen_tax.py`, `tax_{0p0,0p1,0p25,0p5,1p0,2p0}_{face,off1}.ergo`,
`tax_0p5_scrdiag_{face,off1}.ergo` (+binaries and `.out` files),
this report.
