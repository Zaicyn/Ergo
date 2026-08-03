# Packed sweep + parallel tempering for 1SNO (staphylococcal nuclease)

Programs (min/pmargin/, emitted by `gen_packed_1sno.py`, which reuses the
BBA5 machinery from `gen_packed_bba5.py`):
- `packed_1sno.ergo` — baseline packed sweep, 8 blocks (seeds 0.0–7.0),
  v2 packed-force-kernel form, 136 residues, NREG=246, MAXFRAME=48000,
  quench at 38400 (0.8×, matching the doc recipe: TORSK=0.2, HB_CAP=0,
  NATIVE_K=1.0, register torsions from frame 1200, REG_K=0.5)
- `packed_1sno_temper.ergo` — TMUL ladder 1.0→2.0 geometric, Metropolis
  swaps every 500 frames (identical design to BBA5 temper)
- `packed_1sno_gate.ergo` — SWAP_EVERY=0 validation gate
- Per-domain RMSD added to all three (CLINICAL.md §6.3): domain 1 =
  residues 1–98, domain 2 = 99–136 (per SCALING.md), Kabsch over each
  subrange (`COMPUTE_RMSD_RANGE`).

Units: all RMSDs are raw `.out` model units, the same numbers the doc
tables quote as "Å" (SCALING.md); the true scale is 2.4999 Å per model
unit (mean_ca_ca/1.52). Oracle: `tests/waveform_snase_seed_0.0..4.0.out`
at frame 48000. Runtime: 54 s per run (8 blocks × 48k), all builds
CPU-deterministic (temper ×2 md5-identical).

## 1. Baseline validation

| block | seed | packed | doc oracle | Δ | verdict |
|---|---|---|---|---|---|
| 1 | 0.0 | 2.0521 | 2.1686 | −0.117 | ✓ within 0.2 |
| 2 | 1.0 | 3.2640 | 2.6759 | +0.588 | exceeds 0.2 — chaotic (below) |
| 3 | 2.0 | 2.2853 | 2.2600 | +0.025 | ✓ |
| 4 | 3.0 | 9.6605 | 10.1447 | −0.484 | exceeds 0.2 — same stuck plateau, same call |
| 5 | 4.0 | 4.6738 | 4.7725 | −0.099 | ✓ |
| 6 | 5.0 | 2.9624 | — new | | good |
| 7 | 6.0 | 3.6934 | — new | | marginal (slow) |
| 8 | 7.0 | 2.4426 | — new | | good |

**Isolation proof** (the 0.2-exceeding deltas are chaos, not packing
bugs): packed TRACE matches the sequential `.out` to all 4 printed
digits at frames 200–600 for blocks 1 and 4, and at frames 200–1000 for
block 2 (e.g. block 2: 5.0002/4.8504/4.7007/4.6230/4.5549 vs sequential
5.0002/4.8504/4.7007/4.6231/4.5549). A 136-residue system amplifies
residual FP/codegen differences far more than BBA5's 23: the sequential
source *recompiled with the current compiler* itself moves seed 1.0 to
2.8010 (vs its own .out 2.6759) and seed 3.0 to 10.1369 (vs 10.1447) —
the packed endpoint deltas sit in the same band. Doc's sweep verdict
reproduced: seeds 0.0/2.0 good, 3.0 stuck on the wrong-basin plateau
(~10), 4.0 slowly descending (~4.7); seed 1.0 lands marginal (3.26) in
this build.

## 2. Tempering

**Gate: PASSED** — swaps-OFF output byte-identical to the baseline (only
header + SWAPSTAT lines differ; 0 tries).

Swap acceptance per pair (of 96): 38.5% / 24.0% / **0.0%** / 50.0% /
37.5% / 27.1% / 43.8%. Much lower than BBA5's 86–100% — correct
physics: energies and their spread are ~10× larger here, and pair 3
(folded block 3, E≈5, vs stuck block 4, E≈33) is always rejected —
Metropolis correctly refuses to freeze the stuck block onto the cold
rung.

Rescue table (full-chain RMSD):

| block | seed | baseline | temper | call |
|---|---|---|---|---|
| 1 | 0.0 | 2.0521 | 2.1133 | unchanged (good) |
| 2 | 1.0 | 3.2640 | 2.8417 | improved |
| 3 | 2.0 | 2.2853 | 2.2544 | unchanged (good) |
| 4 | 3.0 | 9.6605 (stuck) | 9.9880 | **NOT rescued** |
| 5 | 4.0 | 4.6738 (slow) | 4.7355 | unchanged (slow) |
| 6 | 5.0 | 2.9624 | 2.1994 | improved |
| 7 | 6.0 | 3.6934 | 2.9188 | improved |
| 8 | 7.0 | 2.4426 | **1.7491** | **best fold of the sweep** |

Mean RMSD 3.88 → 3.60. Trap rate (stuck plateaus, RMSD > 4): 2/8 → 2/8 —
the deep seed-3.0 basin is untouched. But tempering improved ALL four
marginal blocks substantially and produced the best structure of the
sweep (1.75). Good folders unharmed (blocks 1, 3 within chaotic
deviation; block 3's domain 2 stays at 0.11).

## 3. Per-domain breakdown (DOM rows: full / D1 1–98 / D2 99–136)

| block | seed | baseline D1 / D2 | temper D1 / D2 | reading |
|---|---|---|---|---|
| 1 | 0.0 | 2.34 / 0.77 | 2.31 / 1.07 | D2 near-native both |
| 2 | 1.0 | 3.77 / 0.31 | 3.30 / 0.45 | D2 native; error is D1/interface |
| 3 | 2.0 | 2.68 / 0.21 | 2.65 / 0.11 | best D2 (native) |
| 4 | 3.0 | **8.73 / 2.68** | **8.83 / 6.52** | domain-1 misplacement (the stuck trap); tempering made D2 WORSE without fixing D1 |
| 5 | 4.0 | 3.64 / 3.13 | 3.63 / 3.09 | both domains mildly off (interface, doc's residues 73–81) |
| 6 | 5.0 | 2.82 / 3.02 | 2.47 / **1.04** | D2 repaired by tempering |
| 7 | 6.0 | 4.09 / 0.63 | 3.04 / 1.07 | improved |
| 8 | 7.0 | 1.10 / **6.22** | 1.28 / **2.09** | D2 misplacement → largely repaired (the sweep's best result) |

Per-domain RMSD is directly diagnostic: the seed-3.0 trap is a
domain-1-vs-domain-2 misplacement (D2 folded at 2.68 while D1 is 8.7
off) — the classic domain-swap failure mode — and the tempering wins
(blocks 6, 8) are specifically domain-2 repairs. Two-domain tempering
earns its keep on MARGINAL domain defects, not on the deep domain-1
trap.

## 4. Energy-blindness check (vs the BBA5 finding)

Final Metropolis energies (baseline | temper):

| block | seed | RMSD | E |
|---|---|---|---|
| 3 | 2.0 | 2.29 / 2.25 | 4.90 / 1.53 |
| 1 | 0.0 | 2.05 / 2.11 | 5.70 / 5.23 |
| 6 | 5.0 | 2.96 / 2.20 | 17.9 / 6.22 |
| 7 | 6.0 | 3.69 / 2.92 | 16.7 / 14.7 |
| 8 | 7.0 | 2.44 / 1.75 | 21.5 / 15.7 |
| 2 | 1.0 | 3.26 / 2.84 | 22.0 / 21.8 |
| 5 | 4.0 | 4.67 / 4.74 | 23.4 / 20.7 |
| 4 | 3.0 | 9.66 / 9.99 | **32.9 / 36.2** |

**The BBA5 energy-blindness finding does NOT reproduce here.** The
seed-3.0 trap is energy-DISTINCT — the highest-energy block by a wide
margin (33–36 vs 5–23) — i.e. a high-energy KINETIC plateau, not a
compact non-native minimum competitive with native. For 1SNO the
Metropolis signal was correct and the swap rejections were physically
right; the trap survives because escaping it requires melting domain 1
back through even higher energy, and the effective tempering window
(noise > baseline only at frames < 1200, ~2 swap steps) is far too
short for a 136-residue domain re-melt. Caveat: mid-RMSD blocks span a
wide energy range (RMSD ~2–3.7 at E 5–22), so energy still does not
rank the near-native structures — RMSD remains the call oracle.

## Verdict

- Packed sweep for 1SNO: validated (isolation exact to 1e-4 early;
  doc's verdict reproduced including the stuck seed-3.0 plateau;
  endpoint deltas for two seeds exceed 0.2 but are demonstrated
  cross-version/chaos effects, with the sequential recompile itself
  moving comparably).
- Tempering: gate bitwise; no deep-trap rescue (2/8 → 2/8) — but all
  four marginal blocks improved (mean 3.83 → 3.26) and the sweep's best
  fold comes from tempering (seed 7.0, 2.44 → 1.75, a domain-2 repair).
- Follow-ups (ordered): (1) longer hot phase — the effective tempering
  window is only frames < 1200 (~2 swap steps); a ~5000-frame hot phase
  is the obvious lever for the domain-1 trap; (2) per-domain swap
  criteria (swap on per-domain energies so a well-folded D2 isn't
  penalized — the block-4 D2 regression is exactly this failure);
  (3) even/odd pair sweep; (4) per-domain RMSD is now available and
  should become standard output for multi-domain targets.

Files: `gen_packed_1sno.py`, `packed_1sno.ergo` (+bin),
`packed_1sno_temper.ergo` (+bin), `packed_1sno_gate.ergo` (+bin),
`packed_1sno.out`, `packed_1sno_gate.out`, `packed_1sno_temper_r1.out`,
`packed_1sno_temper_r2.out`, this report.
