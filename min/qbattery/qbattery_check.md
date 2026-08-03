# Quantum battery rate model — testing superextensive discharge (Hymas 2026)

Programs: `min/qbattery/qbattery.ergo` (open-system rate model,
graphene_transfer idiom: Euler to steady state), `analyze_qbattery.py`
(log-log exponents). Model paper: `papers/sapphire.txt` — claim:
steady-state discharge power scales super-linearly with N (P ~ N²,
cavity/control ratio linear in N); no-cavity control linear.

## Model (documented — the classical-channel alternative hypothesis)

Polariton-branch rate equations, no non-classical correlations anywhere:
- **B** = bright collective polariton occupancy (one mode; superradiant
  absorption `W·N·fB·(1−B)`, fB = 0.5 = LP oscillator fraction by the sum
  rule; two-level saturation `(1−B)`); decays at κ + k_ISC.
- **D** = dark-mode singlets (N−1 uncoupled modes, independent
  absorption W, decay γ + k_ISC).
- **T** = triplet reservoir (metastable, k_rec = 0.01 per the paper's
  10⁶× persistence), extraction k_ext = 1.
- I = k_ext·T (photocurrent); P = I·Vth;
  Vth(cavity) = E_T1 + G√N (dressed-state voltage — the paper's own
  stated mechanism: "open-circuit voltage grows as √N");
  Vth(control) = E_T1.
Parameters (documented, ns⁻¹): k_ISC = 1, γ = 0.1, κ swept, k_ext = 1,
G = 0.05 eV (Ω = G√N reaches ~0.5 eV at N=100, matching the UP/LP
separation in the reflectance spectra), E_T1 = 1.2 eV. Sweep:
N ∈ {1…200}, W ∈ {0.001, 0.1, 1.0} (pump crossover), κ ∈ {0.1, 0.5, 2.0}.
The model is exactly solvable at steady state; the Euler values match
the analytic fixed point to printed precision (verified at N ≤ 10⁵).

## Exponent table (log-log fits)

Control (sanity): exp(I) = exp(P) = 1.00 exactly, all regimes ✓.

Cavity, full N range (1–200):

| W | κ | exp(I) | exp(P) | P-ratio exp |
|---|---|---|---|---|
| 0.001 | 0.1 | 1.17 | 1.22 | 0.23 |
| 0.001 | 0.5 | 1.19 | 1.26 | 0.27 |
| 0.001 | 2.0 | 1.23 | 1.33 | 0.34 |
| 0.1 | 0.1 | 1.08 | 1.16 | 0.16 |
| 0.1 | 0.5 | 1.13 | 1.20 | 0.20 |
| 0.1 | 2.0 | 1.22 | 1.30 | 0.30 |
| 1.0 | 0.1 | 1.04 | 1.12 | 0.12 |
| 1.0 | 0.5 | 1.08 | 1.15 | 0.15 |
| 1.0 | 2.0 | 1.16 | 1.23 | 0.23 |

Excluding N ≤ 2 (small-N collective turn-on): exp(I) drops to
0.95–1.04 ≈ 1.0; exp(P) stays 1.05–1.14.

## Decomposition (the honest numbers)

1. **The photocurrent is LINEAR in N in the classical model** once the
   collective mode is established (excluding the small-N turn-on). The
   superextensive-current claim (I ~ N^1.5) is NOT reproduced: the
   bright channel saturates (B → 1 as W·N·fB ≫ κ + k_ISC), and the
   dark channel is extensive by construction.
2. **The power is mildly superextensive (exp ≈ 1.05–1.14 mid-range),
   ENTIRELY from the dressed voltage** Vth = E_T1 + G√N. Its log-slope
   is < 0.5 at small N (E_T1 dominates the sum) and rises toward 0.5
   as G√N ≫ E_T1. Measured directly: exp(P) climbs 1.17 → 1.26 → 1.41
   over N = 100 → 10⁵, heading to 1.5 asymptotically.
3. **Asymptotic (exact, from the steady-state formulas): exp(P) → 1.5,
   ratio exponent → 0.5** for every pump strength (saturated or not,
   since I ∝ N in both regimes). At experimental N ~ 10¹⁴ the model
   gives P_cav/P_ctrl = 1 + G√N/E_T1 ≈ 4×10⁵ and P ∝ N^1.5.
4. **The crossover exists**: the P-ratio exponent falls as pump W rises
   (0.34 → 0.12 at κ = 2) — strong pump saturates the bright channel
   and erases the collective advantage, consistent with the paper's
   linear/superlinear crossover narrative (their Fig. S19).

## Verdicts per question

**(a) Does the cavity case show exponent > 1?** YES — exp(P) =
1.05–1.33 depending on regime, plus an asymptotic approach to 1.5.
Superextensivity is real in the classical rate model.
**(b) Does classical rate arithmetic suffice?** MOSTLY, with a precise
deficit: the model reproduces superextensive power via exactly the
mechanism the paper itself states (dressed voltage ∝ √N) — but it
caps at **P ∝ N^1.5 (ratio ∝ N^0.5), not the paper's P ∝ N² (ratio ∝
N)**. The missing factor of N^0.5 is a superextensive CURRENT (I ~
N^1.5), which no term in this classical model produces: the bright
channel saturates. So the "quantum battery" effect is largely
collective-optics arithmetic — demystified — EXCEPT the extra
superextensive current, which is either the real quantum-correlation
content or an additional mechanism the rate model lacks (e.g.
absorption cross-section growing with polariton Q ∝ √N/κ).
**(c) Controlling parameters:** the exponent is set by the
pump-vs-saturation regime (weak pump → larger apparent exponent via
the collective turn-on and no saturation; strong pump → linear) and by
κ vs the dressed-voltage scale G√N/E_T1 (the asymptotic exponent is
regime-independent at 1.5). The honest reading: at experimental N the
regime that matters is the asymptotic one, where this model says 1.5,
not 2.

Files: `min/qbattery/qbattery.ergo`, `min/qbattery/qbattery.out`,
`min/qbattery/analyze_qbattery.py`, this report. Note: the large-N
Euler run overflows at N ≥ 10⁶ (DT=0.01 unstable for rates > 100);
the asymptotic values above are from the exact steady-state solution
of the same model, verified against the Euler output at N ≤ 10⁵.
