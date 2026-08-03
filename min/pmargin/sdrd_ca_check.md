# Calcium site stabilization for SdrD — retest with white bath

Programs (min/pmargin/): `gen_sdrd_ca.py` →
`sdrd_ca_{A2,A3,B1,B2}.ergo` (+ `sdrd_ca_B1_k{05,10,20}.ergo` for the
strength bracket). Model per the amide-bead pattern: one dynamic
pseudo-atom per crystal Ca²⁺ site (integrated with the same white-hash
kicks and damping as residues, initialized at the centroid of its
coordinators' Cα per block), each coordinating residue's Cα tethered
to its Ca bead by a harmonic bond `FM = −2·K_CA·(D − R0)` at the
crystal Cα→Ca distance (×0.399853 to model units).

## Coordination table (from pdb/10PS.pdb, protein atoms ≤ 3.0 Å)

| site | host | coordinators (residue, key atom, Å) | Cα→Ca (Å) |
|---|---|---|---|
| Ca801 | B1 | E652(O,2.24), D655(OD1,2.45), N657(OD1,2.23), S672(O,2.41) | 4.0–5.0 |
| Ca802 | B1 | N574(OD1,2.27), L671(O,2.26), D674(OD1/OD2,2.55/2.39) | 4.5–5.2 |
| Ca803 | B1 | D579, N581, N583, V585(O), E587(OE1), E590 (6 coord.) | 4.3–6.8 |
| Ca804 | B2 | I762(O), D765, N767, T782(O) | 4.0–5.1 |
| Ca805 | B2 | D686, M781(O), D784 | 4.6–5.2 |
| Ca806 | B2 | D691, N693, N695, I697(O), D699, E702 (6 coord.) | 4.4–6.6 |
| Ca807 | A2 | D363 only (single contact — weak site, documented) | 5.5 |
| Ca808 | A2+A3 | D363, D365 (A2), D481 (A3) — CROSS-DOMAIN: excluded from per-domain runs | 5.0–5.7 |
| Ca809 | A2 | D261, D263, S265, T267, D273 | 4.4–5.1 |

B domains host 6 of 9 sites (3 each); A2 hosts 2 (one weak); A3 hosts
none alone (the cross-domain site 8 is excluded from per-domain files,
documented). Consistent with MSCRAMM B-domain Ca²⁺ stabilization.

## Before/after (8 seeds each, final RMSD, model units)

| domain | white bath (best / median) | + Ca staples K=1.0 (best / median) | K=0.5 | K=2.0 | K=10 |
|---|---|---|---|---|---|
| A2 | 3.40 / 5.35 | 3.66 / 5.32 | — | — | — |
| B1 | 0.90 / 4.35 | 0.91 / 4.64 | 0.91 / 4.38 | 0.91 / 4.38 | 0.91 / ~4.8 |
| B2 | 1.80 / 4.85 | 1.82 / 4.85 | — | — | — |

Per-seed trajectories are near-identical to the no-calcium runs at
every strength tested (matching to 1–2 digits on most seeds).

## Verdict — the informative negative

**Calcium staples change nothing at any strength from K=0.5 to K=10.**
Not the best fold, not the median, not even the per-seed trajectory
shape. The reason is structural, not parametric: the model's Go
contact map is already derived from the same crystal, so the
coordination geometry the calcium locks is already encoded in the
native-contact network — the staples are redundant information at Cα
resolution. In good folds the staples are satisfied and contribute ~0
net force; in trapped folds they are ~2–20% of the field — never
enough to redirect a landscape whose other ~200 contacts per domain
disagree. The energy-function ceiling mapped in `sdrd_check.md` and
`sdrd_white_check.md` stands unchanged, and it now stands with the
explicit-cofactor hypothesis eliminated: **the ceiling is not missing
chemistry at the Cα/Cβ level either — it is the contact/energy
function itself.** If calcium's role is ever to matter in this model
it would need explicit carboxylate beads (charged side chains) with
the Ca as a coordination hub — a different representation, not a term
on this one.

Files: `gen_sdrd_ca.py`, `sdrd_ca_{A2,A3,B1,B2}.ergo`,
`sdrd_ca_B1_k{05,10,20}.ergo` (+binaries), `sdrd_ca_{A2,B1,B2}.out`,
`sdrd_ca_B1_k{05,10,20}.out`, this report.
