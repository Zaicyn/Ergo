# Graphene → GaAs → SSL → QD transfer: rate-model consistency check

Model: `min/graphene/graphene_transfer.ergo` — 5-state Pauli master
equation (G=graphene, A=GaAs, S=SSL, Q=InAs QD, LOST=sinks). Forward
layer steps barrier-limited `k_fwd = K0·exp(−ΔE/kT)`; backward steps
`k_back = k_fwd·exp(−ΔG/kT)` (detailed balance with driving force);
radiative sink KR=1.0/ns in Q (PL channel); non-radiative KNR per layer.
Steady state from an exact 4×4 direct solve (rates span ~10 decades —
explicit Euler cannot reach steady state); the trimer-style Euler
integrator is cross-validated on a mild config: max|ΔP| = 6.6e-14 vs
the direct solve (`# EULER_CHECK`).

Reference: Wang et al., npj 2D Mater. 4:27 (2020) (`papers/graphene.txt`).

## Parameter documentation (consistency testing, NOT fitting)

| parameter | value | source |
|---|---|---|
| kT | 0.026 eV | measured (room temp) |
| ΔE_C | 0.61 → 0.51 eV (non-irr → FLI) | measured (thermionic I–V fits) |
| graphene gap | 0 → 0.31 eV | measured (DFT/Raman) |
| KR | 1.0 /ns | measured ~1 ns QD radiative lifetime |
| K0 (attempt rate) | 1e3 /ns ref, swept 1e1–1e6 | FREE (ps-scale phonon-mediated) |
| ΔE_AS, ΔE_SQ | 0.05 eV | FREE (SSL miniband + phonon capture) |
| ΔG1,2,3 | 0.2/0.1/0.15 eV | FREE (cascade driving forces) |
| KNR(G,A,S,Q) | swept / 0.1 / 0.1 / 0.01 /ns | FREE |
| AMULT (absorption ×) | 2.0 | FREE — below-gap states harvest after gap opening |
| KLEAK (barrier-insensitive G→A) | 0 ref, swept | FREE — defect/pinhole channel hypothesis |
| DSQ_BOT (QD-only bottleneck) | 0.3 eV, swept 0.15–0.35 | FREE — phonon bottleneck (paper: TestQD capture is bottleneck-limited) |

## Experiment 1 — bandgap/ΔE sweep: is 20× consistent?

Reference configs (`# EXP1_REF`): J_GA (net junction flux = photocurrent
analog) non-irr 6.47e-8, irr 6.06e-6 (incl. AMULT=2) → **R_TOT = 93.6×**.
Naive thermionic: exp(0.10/0.026) = 47.0 efficiency ratio; ×AMULT=2 → 94×.

Regime map (`# EXP1_SCAN`, R_ETA over K0 × KNRG, 30 points):

| | KNRG=1e-2 | 1e-1 | 1 | 1e1 | 1e2 |
|---|---|---|---|---|---|
| K0=1e1 | 46.8 | 46.8 | 46.8 | 46.8 | 46.8 |
| K0=1e3 | 46.8 | 46.8 | 46.8 | 46.8 | 46.8 |
| K0=1e5 | 45.5 | 46.7 | 46.8 | 46.8 | 46.8 |
| K0=1e6 | 36.2 | 45.5 | 46.7 | 46.8 | 46.8 |

**The ratio is locked at ≈47 over the entire physical regime.** It only
starts to compress when ETA_irr approaches saturation (ETA_irr = 0.23 at
K0=1e6, KNRG=1e-2 → R_ETA = 36). Reaching R_TOT ≈ 20 via regime alone
needs ETA_irr ~ 0.7 with ETA_non small — i.e. K0 ~ 1e6 /ns (fs attempt
rate) AND graphene non-radiative lifetime ~μs. Both are implausible by
~3 orders of magnitude (attempt rates are ps-scale; graphene carrier
lifetimes are ps–ns). **Regime-tuning cannot produce 20×.**

What CAN cap the ratio below 47× (`# EXP1_LEAK`): a barrier-insensitive
leak channel KLEAK (defect/pinhole-assisted transfer, same in both
devices — physically expected in any wet-transferred interface). The
leak raises the non-irradiated baseline more than the irradiated one:

| KLEAK (/ns) | R_ETA | R_TOT (AMULT=2) |
|---|---|---|
| 0 | 46.8 | 93.6 |
| 1e-7 | 19.0 | 38.0 |
| **2.65e-7** | **10.0** | **20.0** (interpolated, exact additive law) |
| 1e-6 | 3.78 | 7.57 |
| 1e-4 | 1.03 | 2.06 |

Consistency curve for R_TOT = 20 (exact: KLEAK solves
(KLEAK+3.028e-6)/(KLEAK+6.468e-8) = 20/AMULT):

| AMULT | required R_ETA | required KLEAK (/ns) |
|---|---|---|
| 2 | 10.0 | 2.65e-7 |
| 4 | 5.0 | 6.76e-7 |
| 10 | 2.0 | 2.90e-6 |
| 20 | 1.0 | any KLEAK ≫ barrier rate |

**Verdict EXP1:** 20× is consistent with the rate model only if
(i) a small barrier-insensitive channel (~2.6e-7 /ns branch rate at
AMULT=2) exists in both devices — plausible for transferred interfaces,
and it correctly leaves the *dark-current* I–V thermionic fit intact
since it is barrier-insensitive; or (ii) the absorption multiplier is
~20 (the opened 0.31 eV gap harvesting a broad IR band) with comparable
transfer efficiency in both devices. What is NOT consistent: pure
thermionic transfer over the measured ΔE_C with AMULT=2 — that rigidly
predicts ~94×. Note also the absolute efficiencies: with measured
barriers and ps-scale K0, ETA ~ 1e-7–1e-6, far below a working
photodetector — independent evidence that the real photocurrent channel
is not simple over-barrier thermionic emission.

## Experiment 2 — layer sweep: non-monotonic PL

Algebraic PL(L) = A(L)·g^(L−1), A(L) = 1−0.977^L (`# EXP2_ALG`,
`# EXP2_PEAK`):

| g | peak L |
|---|---|
| 0.95, 0.90 | 8 (still rising) |
| 0.85 | 6 |
| 0.80 | 4 |
| **0.70** | **3** ✓ |
| 0.60 | 2 |
| 0.50 | 1 |

**g = 0.7 (70% per-interface transfer survival) reproduces the peak at
L=3**; the analytic window is g ∈ (0.672, 0.758) — of the scanned set
only 0.7 lands inside. PME check (`# EXP2_PME`): feeding A(L)·T(L) as
source multipliers into the full PME (g=0.7, non-irr config) gives
J_PL(L) matching the algebraic shape to 6 digits — expected: the model
is linear in the source, so no density-dependent distortion exists; the
non-monotonicity is purely the absorption-vs-interface-survival
competition, and 30% per-interface loss is quantitatively consistent
with the paper's "severe interface effect" from wet-chemical transfer.

## Experiment 3 — SA saturation

I_sat ∝ KR/η, so I_sat ratio = η_QDonly/η_GRcoupled. η from the PME
(`# EXP3`): QD-only case = source into GaAs with phonon-bottleneck
capture barrier DSQ_BOT; graphene-coupled = AMULT×source into G +
baseline into A, SSL-assisted capture (0.05 eV), irradiated offset.

| DSQ_BOT (eV) | η_QDonly | η_GRcoupled | I_sat ratio |
|---|---|---|---|
| 0.15 | 0.967 | 0.333 | 2.91 |
| 0.20 | 0.816 | 0.333 | 2.45 |
| 0.25 | 0.395 | 0.333 | 1.19 |
| **0.30** | **0.087** | **0.333** | **0.262** ✓ |
| 0.35 | 0.014 | 0.333 | 0.041 |

**Verdict EXP3:** the measured <1/3 saturation intensity is consistent
for phonon-bottleneck barriers ≳ 0.28 eV in the QD-only reference —
right at the documented choice 0.3 eV (phonon bottleneck is precisely
the mechanism the paper cites for weak TestQD emission, and the SSL is
what relieves it). Saturation curves (`# EXP3_CURVE`, ratio 0.262) show
the graphene device absorbing >2× more than the QD-only device already
at I = 0.1·I_sat,A and saturating ~4× harder at I = I_sat,A.

## Overall verdict

- **20× photocurrent:** NOT reproducible by regime-tuning within
  physical rate ranges — the thermionic efficiency ratio is locked at
  ≈47× (×AMULT). Consistent WITH a small barrier-insensitive leak
  (~2.6e-7 /ns at AMULT=2) in both devices, or with AMULT ~ 20. This is
  a real constraint on the paper's narrative: the measured ΔE_C
  reduction over-predicts the enhancement unless a barrier-insensitive
  channel dominates the baseline.
- **PL(L) peak at 3:** consistent; selects per-interface survival
  g ≈ 0.7 (window 0.672–0.758).
- **I_sat < 1/3:** consistent for QD-only phonon bottleneck ≳ 0.28 eV.
- Model limitations: single-carrier linear PME (no exciton/excited-state
  structure, no space charge, no density-dependent rates); all free
  parameters documented above; absolute efficiency is underdetermined
  by the paper (no EQE reported), which is why only ratios are tested.

Files: `graphene_transfer.ergo` (+binary), `graphene_transfer.out`
(full section output). No separate analysis script needed — the Ergo
output is self-tabulating; the consistency-curve interpolation is exact
(additive leak law) and verified numerically.
