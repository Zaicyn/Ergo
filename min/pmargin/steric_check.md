# Steric-size term for W6F + pulse-response comparison

Base: `tests/waveform_trpcage_cb4.ergo` (identical to the ar0.05 variant;
WT folds to 0.5879, MAXFRAME 4000, quench 3200, native-D0 aromatic
loop). W6F built on the SAME base for apples-to-apples (the older
`Protein_Margin/trpcage_w6f_cb.ergo` uses a different fixed-distance
aromatic loop; its Phe value AROMATIC_MULT(6)=0.30 was adopted; the
older file's W6F reference fold is 0.5885). Variants from
`gen_steric.py`, all runs < 1 s.

## Volume table and term design

Residue volumes (Zamyatnin 1972, Å³): Trp 227.8, Phe 189.9, Tyr 193.6.
`STERIC_DV(i) = max(0, V_native(i) − V_placed(i))`; WT: all zero (term
identically off). W6F: `STERIC_DV(6) = 227.8 − 189.9 = 37.9`.

Force form (per Cβ-Cβ packing partner, D < 8.0, pocket tightness enters
through the number of formed partners — no separate table):
- **Anti-collapse (default):** for over-collapsed pairs (D < D0),
  repulsion `FS = K·(DV_i+DV_j)·(D0−D)/D0` — an underpacked residue
  cannot hold its native packing partners as tightly.
- **Void-filling (opposite sign, tested as control):** for
  under-collapsed pairs (D > D0), attraction of the same magnitude —
  the void gets filled (physical: real pockets collapse onto the
  smaller side chain).
- Diagnostic energy `E_STERIC = K·(DV_i+DV_j)·(D0∓D)²/(2·D0)`
  (accounting only, no force feedback).

## WT gate — PASSED

`steric_wt.ergo` (K=0.001, DV≡0): final RMSD **0.5879**, identical to
the unmodified variant (≤ 0.7 required). The term is zero by
construction for WT (×0.0 is IEEE-exact). Caveat, documented: the
output is bitwise-identical to the reference only through frame ~1790;
after that the extra code in the force loop perturbs codegen FP
association and the chaotic trajectory diverges (final RMSD still
matches to 4 digits because the fold is settled). Same signature as the
earlier cross-build deviations — not a dynamics difference.

## W6F signature — NONE; the term does not destabilize at any strength

Dose-response (final RMSD; WT = 0.5879, untreated W6F ≈ 0.588):

| STERIC_K | anti-collapse W6F | void-filling W6F |
|---|---|---|
| 0.0003 | 0.5852 | — |
| 0.001 | 0.5669 | 0.5701 |
| 0.005 | 0.5373 | — |
| 0.01 | 0.5173 | 0.5205 |
| 0.05 | 0.4930 | — |
| 0.1 | 0.4963 | — |

**No trap, no deviation, at either sign, over a 330× K range — W6F
folds as well as or BETTER than WT.** The anti-collapse variant
monotonically IMPROVES W6F's RMSD (0.585 → 0.493): holding the pocket
open at Trp size makes the mutant geometrically more WT-like (and
Kabsch-to-WT rewards exactly that). The term is self-limiting —
E_STERIC falls at high K (0.0094 at K=0.005 → 0.0023 at K=0.1) because
the pocket stops over-collapsing. The void-filling variant likewise
improves slightly (0.520 at K=0.01). The Go restraints + native
torsions pin the 20-residue topology orders of magnitude more strongly
than any of these terms (residual Go energy at the fold ≈ 0.003–0.006;
E_STERIC 0.002–0.03).

**Margin measurement (fallback per the task):** the term's energy
contribution is real but tiny — E_STERIC(W6F) = 0.0078 (K=0.001,
void) to 0.029 (K=0.01) vs E_STERIC(WT) = 0.0 and residual native-
contact energy ≈ 0.003–0.006. The margin shrink is measurable but
nowhere near destabilizing; at K=0.01 the steric penalty is ~5× the
residual Go energy and the fold still holds at 0.52.

## Pulse response (validated 1SNO pulse: ω=0.002, A=0.05, backbone standing wave)

| run | final RMSD |
|---|---|
| WT + steric (K=0.001) | 0.5879 |
| W6F + steric (K=0.001) | 0.5669 |
| WT + steric + pulse | 1.0944 |
| W6F + steric + pulse | 1.0836 |

The pulse knocks BOTH variants from ~0.59 to ~1.09 — a strong shared
perturbation (for a 20-residue protein, A=0.05 rocking is violent) but
with **no differential signature** (Δ = 0.01, inside chaotic
deviation). Since the steric term produces no W6F trap, there is no
mutation-induced trap for the pulse to rescue; the pulse-response
question is moot here, and the near-identical response is consistent
with the two structures being physically indistinguishable in this
model.

## Verdict (honest, and it agrees with CLINICAL.md §8)

The steric-size term as specified (penalize Phe in a Trp-sized pocket)
was implemented faithfully, gated, and swept over 330× in strength in
both physically reasonable sign conventions. **It does not produce a
W6F destabilization signature, and no plausible sign/strength of a
Cβ-distance-based term will**: the Trp-cage Go basin is too robust at
Cα/Cβ resolution, and a term that penalizes pocket deformation
perversely makes the mutant MORE WT-like geometrically. This is the
representation limitation CLINICAL.md §8 names, now demonstrated rather
than asserted: capturing W6F destabilization needs side-chain physics
the model doesn't have (explicit pocket strain, solvent/void
thermodynamics, the indole NH interaction) — not a bigger K. The
pulse-response comparison is consistent: identical within chaos.

Files: `gen_steric.py`, `steric_wt.ergo`, `steric_w6f_k{3e4,1e3,5e3}.ergo`,
`steric_w6f_k{0.01,0.05,0.1}.ergo`, `steric_w6f_void_k{1e3,1e2}.ergo`,
`pulse_steric_{wt,w6f}.ergo` (+binaries and `.out` files), this report.
