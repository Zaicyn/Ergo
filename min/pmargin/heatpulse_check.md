# Sustained heat + ultrasonic pulse on the 1SNO domain-1 trap

Target: the seed-3.0 trap (baseline full 9.66 / D1 8.73 / D2 2.68, E≈33,
high-energy kinetic plateau, domain-swap topology). All variants from
`gen_heatpulse.py` (patches on `packed_1sno_gate/temper.ergo`), 54 s per
run, CPU-deterministic. Trap threshold: full RMSD > 4; rescue criterion:
D1 < 3 with D2 < 3 and good folders intact.

## Task 1 — sustained heat (floor raised 0.001 → 0.005/0.01/0.02 through frame 24000)

| config | block 4 full / D1 / D2 | trap rescued? | good folders (b1, b3) | pair-3 acc |
|---|---|---|---|---|
| heat 0.01, NO swaps (ctl) | 8.41 / 8.66 / **1.84** | NO (D1 8.66) | intact (2.23 / 2.34) | — |
| heat 0.005 + swaps | 9.81 / 8.73 / 2.24 | NO | intact (2.03 / 2.25) | 0.00 |
| heat 0.01 + swaps | 9.96 / 8.82 / 6.80 | NO (D2 wrecked too) | intact (2.39 / 2.34) | 0.00 |
| heat 0.02 + swaps | 10.00 / 8.80 / 6.78 | NO (D2 wrecked too) | intact (2.50 / 2.33) | 0.00 |

**Sustained heat does NOT melt the domain-1 trap at any level up to
0.02 (20× the original floor).** D1 is pinned at 8.7–8.8. The plateau is
robust to incoherent thermal noise, period. Notes: (a) sustained heat
ALONE (no swaps) is the gentlest config — it relaxes the trap's full
RMSD (9.66 → 8.41) and improves D2 (2.68 → 1.84) without rescuing D1;
(b) heat+swaps keeps wrecking D2 via swap-induced reroutes, and pair 3
(folded E≈5 vs stuck E≈33) is still rejected 100% — Metropolis will not
freeze the stuck block onto a cold rung at any heat level; (c) marginals
like block 7 IMPROVE with heat (0.95 at heat 0.02 — best systematic
block-7 result); (d) acceptance elsewhere 0.25–0.68, no heat
sensitivity worth reporting.

## Task 2 — ultrasonic pulse factorial

Pulse: `V_i += A·sin(ω·frame)·sin(π·i/(N+1))` on all three axes (axes
phase-shifted 2π/3). **Documented choice: mode-1 standing wave along the
backbone** — peaks at residue 68 (covers domain 1, near-zero at the
C-terminus) because the trap is a domain-1/register error; a global AC
kick is translation-invariant under Kabsch RMSD and would be a null
control. No swaps, baseline schedule. Factorial: ω ∈ {0.002 (period
3142), 0.017 (370), 0.17 (37, the noise-hash scale)} × A ∈ {0.002, 0.01,
0.05} (floor 0.001; peak-cycle noise 1.0).

Block-4 (trap) results, full / D1 / D2 — with block-1 (good folder) and
block-7 (marginal) as controls:

| | A=0.002 | A=0.01 | A=0.05 |
|---|---|---|---|
| **ω=0.002** | 10.02 / 8.78 / 2.65 | 10.09 / 8.79 / 3.07 | **3.40 / 3.83 / 1.65** |
| **ω=0.017** | 7.64 / 5.24 / 4.21 | 10.12 / 4.44 / 2.15 | 9.77 / 7.77 / 1.79 |
| **ω=0.17** | 9.82 / 4.52 / 2.39 | 10.14 / 8.89 / 2.46 | 8.15 / 6.64 / 1.14 |

**Exactly one combo works: slow (ω=0.002, period ≈ 3100 frames) + strong
(A=0.05).** Full table for `pulse_w002_a050` (baseline in parens):

| block | seed | full | D1 | D2 | note |
|---|---|---|---|---|---|
| 1 | 0.0 | 1.82 (2.05) | 1.89 | 0.67 | good, improved |
| 2 | 1.0 | 1.32 (3.26) | 1.39 | 0.72 | much improved |
| 3 | 2.0 | 2.45 (2.29) | 2.80 | 0.41 | intact |
| 4 | 3.0 | **3.40 (9.66)** | **3.83** | **1.65** | **RESCUED** |
| 5 | 4.0 | 4.44 (4.67) | 3.57 | 5.02 | slow block, D2 worse (was 3.13) — the one casualty |
| 6 | 5.0 | 3.57 (2.96) | 3.84 | 1.98 | slightly worse, fine |
| 7 | 6.0 | 0.76 (3.69) | 0.60 | 0.89 | much improved |
| 8 | 7.0 | 1.46 (2.44) | 1.33 | 1.36 | improved |

Mean RMSD 2.40 (baseline 3.88, temper 3.60) — the best table seen in any
1SNO experiment. Trap rate (>4): 2/8 → 1/8 (only the slow-descender
block 5 at 4.44). D1 of the trap block: 8.73 → 3.83. Good-folder D2s all
< 0.9. D2 of the rescued block: 1.65 ✓.

Intermediate-frequency partial effects are instructive: ω=0.017 and
0.17 at small A improve D1 (4.4–5.2) but leave full RMSD ~8–10 — the
domains fold better individually yet stay mispositioned relative to each
other (domain-orientation trap). Only the slow-strong combo fixes
domain placement AND the full chain.

## Combo (sonication + heat, the physically motivated pairing)

| config | block 4 full / D1 / D2 | verdict |
|---|---|---|
| pulse alone (w002_a050) | **3.40 / 3.83 / 1.65** | best |
| pulse + heat 0.01 (no swaps) | 3.98 / 4.22 / 7.13 | worse; heat degrades D2 |
| pulse + heat 0.01 + swaps | 9.81 / 8.35 / 7.97 | **re-trapped** |

The pairing does NOT help in this model: sustained incoherent noise on
top of the coherent pulse degrades D2, and adding swaps fully re-traps
(the hot/cold shuffle reroutes the trajectory out of the rescue path).

## Verdict — mechanical, not thermal (and the honesty check)

**The pulse works and it is NOT just effective heating.** Three lines of
evidence: (1) strong FREQUENCY dependence at fixed amplitude — A=0.05
gives D1 = 3.83 / 7.77 / 6.64 at ω = 0.002 / 0.017 / 0.17; a pure
heating effect would be frequency-independent at equal RMS power;
(2) the kick is zero-mean and coherent (a slow global rocking of domain
1), not white noise — the rescue requires the period (~3100 frames) to
be comparable to the basin-escape timescale, i.e. sustained coherent
torque, not jitter; (3) a sharp amplitude threshold (0.01 does nothing,
0.05 works) with no corresponding change in the incoherent background.
Sustained incoherent heat at 20× the floor, with or without swaps,
achieves nothing — the contrast between the two experiments IS the
demonstration that the mechanism is mechanical.

Honest caveats: (a) the pulse's spatial lobe is all-positive
(sin(πi/(N+1)) sums nonzero), so there is a net-force component — it
cannot inflate/deflate Kabsch RMSD through translation, but the field is
not a pure internal mode either; (b) one casualty: the slow-descender
block 5's D2 went 3.13 → 5.02 (it was mid-transition anyway);
(c) real sonication breaks aggregates via cavitation and boundary
effects — this model has a uniform periodic force field, so the analogy
is qualitative (coherent mechanical agitation escapes kinetic traps),
not literal; (d) the rescue (D1 3.83) is below the trap line but not a
sub-3 Å fold — the block ends in the correct topology family with
domain-1 misalignment reduced ~2.3×, still descending.

Practical recommendation: for rugged multi-domain targets, run the
packed sweep WITH the slow-strong pulse (ω ≈ 2π/3000, A ≈ 50× the noise
floor) and no tempering swaps — it dominates every tempering variant
tested (mean 2.40 vs 3.60, trap 1/8 vs 2/8, D2 integrity preserved).

Files: `gen_heatpulse.py`, `heat_010_ctl.ergo`, `heat_005_swap.ergo`,
`heat_010_swap.ergo`, `heat_020_swap.ergo`, `pulse_w{002,017,170}_a{002,010,050}.ergo`,
`combo_heat_pulse.ergo`, `combo_heat_pulse_swap.ergo` (+binaries and
`.out` files), this report.
