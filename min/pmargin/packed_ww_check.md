# Packed sweep + parallel tempering for PIN1 WW domain

Programs (min/pmargin/, from `gen_packed_ww.py`, same machinery as
BBA5/1SNO): `packed_ww.ergo` (baseline 8-block sweep, 34 residues,
NREG=78, MAXFRAME=24000, quench 19200 — the TRANSFERABILITY.md recipe:
HB_CAP=0, TORSK=0.2, register torsions from 1200),
`packed_ww_temper.ergo` (TMUL 1.0→2.0, swaps/500),
`packed_ww_gate.ergo` (swaps off). Single domain — no per-domain RMSD.
Units: raw model units; Å = ×2.506 (mean_ca_ca 3.809/1.52).
Runtime: ~3 s per run; temper build deterministic (×2 md5-identical).

## Gate

PASSED — swaps-OFF output byte-identical to baseline (only header +
SWAPSTAT lines differ; 0 tries).

## Baseline table and the doc's open question

| block | seed | RMSD (raw) | RMSD (Å) | class |
|---|---|---|---|---|
| 1 | 0.0 | 0.8363 | 2.10 | folder — **bitwise-exact match to the doc's `waveform_ww_v2.out` (0.8363)** |
| 2 | 1.0 | 2.1998 | 5.51 | OUTLIER (wrong basin) |
| 3 | 2.0 | 0.4724 | 1.18 | folder |
| 4 | 3.0 | 0.2432 | 0.61 | folder |
| 5 | 4.0 | 0.0946 | 0.24 | **best fold** |
| 6 | 5.0 | 2.1047 | 5.27 | OUTLIER |
| 7 | 6.0 | 0.1552 | 0.39 | folder |
| 8 | 7.0 | 2.5578 | 6.41 | OUTLIER |

**Answer to the doc's open question ("does WW have a bad default
seed?"): NO — the default seed 0.0 is fine (2.10 Å, exact doc
reproduction). But WW DOES have bad seeds: 3/8 (1.0, 5.0, 7.0) land in a
wrong basin at 5.3–6.4 Å, while the other 5 fold to 0.24–2.10 Å.** The
split is binary (no intermediate values): two well-separated basins.
Trap rate: 3/8. For production WW work use seed 4.0 (0.24 Å) or 6.0
(0.39 Å); a 3-seed sweep has a ~33% chance of hitting only outliers, so
seed sweeps remain essential.

## Tempering (48 swap steps)

Acceptance per pair: 89.6 / 62.5 / 79.2 / 87.5 / 79.2 / 83.3 / 52.1 %
(high, like BBA5 — small system, clustered energies).

| block | seed | baseline (Å) | temper (Å) | note |
|---|---|---|---|---|
| 1 | 0.0 | 2.10 | 2.15 | unchanged |
| 2 | 1.0 | 5.51 | 5.53 | NOT rescued |
| 3 | 2.0 | 1.18 | **5.22** | **good folder HARMED** |
| 4 | 3.0 | 0.61 | 0.28 | improved |
| 5 | 4.0 | 0.24 | 0.33 | unchanged |
| 6 | 5.0 | 5.27 | 5.36 | NOT rescued |
| 7 | 6.0 | 0.39 | 0.37 | unchanged |
| 8 | 7.0 | 6.41 | 6.20 | NOT rescued |

Verdict: tempering does nothing for WW — zero outlier rescues (the
outlier basin is separated by more than a 2×-amplitude noise ladder can
cross in the short hot window), and one good folder (seed 2.0) was
chaotically knocked into the outlier basin (1.18 → 5.22 Å). The basin
structure is binary and the ladder doesn't bridge it. Recommendation:
for WW, plain seed sweeps (cheap, 3 s) beat tempering; skip tempering
for small single-domain targets with this basin geometry.

Files: `gen_packed_ww.py`, `packed_ww.ergo` (+bin),
`packed_ww_temper.ergo` (+bin), `packed_ww_gate.ergo` (+bin),
`packed_ww.out`, `packed_ww_gate.out`, `packed_ww_temper_r1.out`,
`packed_ww_temper_r2.out`, this report.
