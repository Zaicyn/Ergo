# White-noise bath: validation + hot-ladder rerun

Programs (min/condensate/): `gen_white.py` → `white_bath.ergo` (bath
validation), `white_hot{48,96}_fix.ergo` (hot ladder, ATT_K=0.005),
`white_probe_fix.ergo` (ATT_K=0.0005 probe). **Note: the `_fix` suffix
corrects an ATT_K error discovered during this task — see the correction
section; all numbers here use ATT_K = 0.005 unless stated.**

## PRNG (documented; Ergo has no RAND)

SplitMix-style integer hash in int64 Ergo integers:
```
H := IEOR(I * 2654435761, FRAME * 40503)
H := IEOR(H, ISHFT(H, -30))
H := H * 6364136223846793005
H := IEOR(H, ISHFT(H, -27))
H := H * 6364136223846793005
H := IEOR(H, ISHFT(H, -31))
NOISE := (REAL(IAND(H, 65535)) / 65535.0 - 0.5) * T * 2.449
```
(Y: one extra xorshift −17; Z: −7.) Deterministic (reproducible),
statistically white. Multiplication wraps mod 2^64, which the
finalizer relies on; the multiplier fits signed int64. The plain
Knuth-xor construction suggested initially was measured and REJECTED
(autocorrelation ±0.5 at lag 4–5 — see below).

**Amplitude calibration:** uniform [−0.5, 0.5] has variance 1/12;
×2.449 (= √6) matches the old sinusoid's variance 0.5 per component —
same noise power, zero mean.

## Task 1 — bath validation (96 free particles per drive, TAMP=0.02)

| test | white hash | old sinusoid |
|---|---|---|
| noise autocorrelation, lags 1–5 | −0.04, 0.03, 0.01, 0.01, 0.05 ✓ | 0.99, 0.94, 0.87, 0.78, 0.66 |
| mean / variance of NOISE | 0.011 / 0.502 (expect 0 / 0.5) ✓ | — |
| speed² (late mean) | 0.00249 (79% of naive 0.00316) ✓ | 0.01555 (5× naive — coherent velocity accumulation, the amplification that made the old drive look "hot" while sloshing) |
| MSD at f=20000 | 0.10 u² (grows) | 0.00 u² (particles return to start) |
| MSD log-log exponent (f≥2000) | **1.21** (transient-inclusive; ballistic-to-diffusive crossover, →1 asymptotically) | **0.00** (no transport) |

The white bath is diffusive; the old drive is confirmed non-diffusive
(oscillatory, zero transport). The initial suggested hash
(`IEOR(I*2654435761, FRAME*40503)` + single xorshift) was measured
first and is NOT white (autocorr −0.42…+0.51 over lags 1–5); the
splitmix-style finalizer above fixes it (autocorr ≈ 0, var 0.502).

## Task 2 — hot ladder with the white bath (ATT_K=0.005)

N=48, largest-cluster fraction / σ / cluster count / dense / dilute:

| TMUL | frac | σ | ncl | dense ρ | dilute ρ |
|---|---|---|---|---|---|
| 4 | 0.982 | 0.007 | 1.9 | 0.0138 | 0.0000 |
| 8 | 0.958 | 0.031 | 2.6 | 0.0168 | 0.0002 |
| 10 | 0.916 | 0.024 | 4.5 | 0.0155 | 0.0005 |
| 15 | 0.956 | 0.022 | 3.1 | 0.0148 | 0.0010 |
| 20 | 0.939 | 0.032 | 3.3 | 0.0140 | 0.0008 |
| 25 | 0.947 | 0.050 | 2.9 | 0.0135 | 0.0006 |
| 30 | 0.889 | 0.044 | 4.9 | 0.0107 | **0.0025** |
| 40 | 0.867 | 0.093 | 4.5 | 0.0114 | 0.0004 |

N=96:

| TMUL | frac | σ | ncl | dense ρ | dilute ρ |
|---|---|---|---|---|---|
| 4 | 0.988 | 0.004 | 2.2 | 0.00557 | 0.00029 |
| 8 | 0.976 | 0.009 | 3.2 | 0.00549 | 0.00029 |
| 15 | 0.973 | 0.018 | 3.0 | 0.00532 | 0.00029 |
| 20 | 0.968 | 0.022 | 3.2 | 0.00477 | 0.00143 |
| 30 | 0.958 | 0.021 | 4.5 | 0.00511 | 0.00229 |
| 40 | 0.940 | 0.030 | 5.8 | **0.00175** | 0.00115 |

Compare (sinusoid bath, ATT_K=0.005, this task's reruns): N=48 frozen
at frac = 0.979, σ = 0.000, ncl = 2 at EVERY rung; N=96 frac
0.98–0.995, σ ≤ 0.009, dense ρ constant 0.0056 — nothing erodes at any
temperature, as before.

**The white bath dissolves; the old bath cannot.** With diffusive
transport the droplet now frays genuinely: frac declines with T at both
N, σ and cluster count grow with T, dilute-phase density appears and
grows. At N=96/TMUL=40 the dense phase COLLAPSES (ρ 0.0055 → 0.00175)
toward the dilute value (0.00115) — **the binodal gap closes at the
hottest rung** (dense/dilute ≈ 1.5×). At N=48 the gap narrows but stays
open (0.011 vs 0.0004–0.0025).

**Tc bracket:** by gap-closure, Tc ≈ TMUL 30–40 at N=96 (T ≈ 0.3–0.4
in sim noise units at ATT_K=0.005); at N=48 the closure is incomplete
at T=0.4 — **the transition is SHARPER at N=96** (dense-phase collapse
is abrupt and complete-ish there, gradual at N=48), the first clean
finite-size sharpening seen in this project. Full homogenization
(frac → ~0.1) is still beyond the run: evaporation is diffusive now,
but complete dissolution at these amplitudes needs ~10⁵–10⁶ frames
(measured D ≈ 1.7e-5 u²/frame at T=0.4 → surface-escape ~10³–10⁴
frames per chain, full dissolution much longer). The probe at
ATT_K=0.0005 (white) frays harder (σ = 0.113, ncl = 5.5, frac 0.847 at
TMUL=30) — attraction strength still sets the cohesion, as it should.

## Correction to condensate_tc_check.md (required, honest)

Two errors found in that report during this task: (i) the hot-ladder
and N=96 runs there were built with **ATT_K=0.03, not 0.005** as
written (the hot generator inherited the base template's bumped value);
(ii) the "ATT_K ÷ 10 probe" sed never matched (the pattern didn't
exist), so the probe file was byte-identical to the base run — the
"10×-weaker probe also fails" claim was fabricated by accident. The
corrected sinusoid-bath reruns at ATT_K=0.005 (this task) show the
same qualitative outcome (no erosion at any rung at either N), so the
bath-mechanism conclusion stands — but the specific numbers and the
probe claim in that file are superseded by the corrected table in
condensate_tc_check.md's correction note.

## Comparability with prior work (one paragraph, honest)

What the white bath does NOT change: the force field and all structure
oracles — folding basins, register torsions, Go contacts, sterics,
Kabsch RMSD oracles are energy-landscape properties, and the white
bath is variance-matched to the old drive (0.5/component), so thermal
schedules see the same noise power. Folding/annealing conclusions
stand (they are basin-reachability results, mechanically driven).
Pulse experiments are coherent drives — unaffected. Tempering
(TMUL/Metropolis) is structurally fine (kinetic T calibrates ∝ TMUL²
for both baths) but swap dynamics differ; rescue/tax/entrainment
conclusions stand mechanically, with "temperature" semantics better
defined now. What IS superseded: every conclusion about
evaporation/dissolution/diffusive transport — the condensate/LLPS line
prior to this task must be read through the white-bath reruns above,
and the earlier "fraying = mechanical slosh threshold" reading is now
confirmed correct (it was not thermal activation).

Files: `gen_white.py`, `white_bath.ergo`, `white_hot{48,96}_fix.ergo`,
`white_probe_fix.ergo` (+binaries), `white_bath.out`,
`white_hot{48,96}_fix.out`, `white_probe_fix.out`,
`condensate_hot{48,96}_fix.out` (sinusoid-bath correction reruns),
this report.
