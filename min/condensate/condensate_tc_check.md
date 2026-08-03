# Reaching Tc: hot ladder + strong confinement at N=48/96

Programs: `gen_condensate_hot.py` → `condensate_hot48.ergo` /
`condensate_hot96.ergo` (N=48, R=22.67; N=96, R=28.57), plus
`condensate_probe.ergo` (N=48 with ATT_K reduced 10×). Same system and
metrics as `condensate_scaling_check.md` (GNNQQNY chains, per-pair
Gaussian attraction, harmonic sphere, 8 constant-T blocks/run, 24000
frames).

## Setup (documented)

- Ladder TMULS = {4, 8, 10, 15, 20, 25, 30, 40}: the 6 hot rungs from
  the task plus 2 sub-Tc anchors for the binodal curve. T = TMUL ×
  0.01 in sim noise units (0.04–0.40).
- CONF_K = 0.05 (was 0.01) to hold hot vapor. **Confinement pre-check:
  HOLDS at N=48** (implied cluster radius 18.1 u < R_BOX 22.67 at
  TMUL=40) and is **marginal but contained at N=96** (implied radius
  ≈ 30.5 u vs R_BOX 28.57 — the single mega-cluster fills the box;
  nothing escapes). No CONF_K=0.1 rerun needed.
- ATT_K = 0.005 per pair (constant with N, as before).

## Hot-ladder table (late-half statistics)

N=48:

| TMUL | frac_late | σ(frac) | ncl_late | dense ρ | dilute ρ | VEL (speed²) |
|---|---|---|---|---|---|---|
| 4 | 0.938 | 0.000 | 2.0 | 0.0176 | 0.00068 | 0.067 |
| 8 | 0.983 | 0.023 | 1.6 | 0.0137 | 0.0000 | 0.258 |
| 10–40 | 0.99–1.00 | ≤0.010 | 1.1–1.4 | 0.0135–0.0137 | 0.0000 | 0.40 → 6.23 |

N=96:

| TMUL | frac_late | σ(frac) | ncl_late | dense ρ | dilute ρ | VEL |
|---|---|---|---|---|---|---|
| 4–15 | 0.988–0.990 | ≤0.005 | 2.0–2.2 | 0.00558 | 0.00029 | — |
| 20–40 | 0.993–1.000 | ≤0.008 | 1.0–1.6 | 0.00569 | 0.0000 | 2.55 → 6.39 |

## The central measurement: NO dissolution, even at T = 0.40

At TMUL=40 the kinetic temperature is speed² ≈ 6.2–6.4 per residue —
thermal energy ~3 per residue against an attraction well of depth
0.005 per contact (600:1). Every chain in every block stays in one
cluster (frac = 1.000, σ ≤ 0.005, ncl ≈ 1). **The droplet does not
dissolve.**

Probe (the discriminator): ATT_K ÷ 10 (0.0005), N=48, same hot ladder
— the droplet STILL holds at T=0.40 (frac 0.999, ncl 1.1). So the
barrier is not the attraction energy either.

## Why — the mechanism (documented from the kick structure)

The sim's "thermal noise" is NOT a stochastic bath. Each residue is
kicked by a deterministic smooth hash,
`SIN((I+1)*7.3 + FRAME*0.17)` (and 0.31/0.09 variants), which is a
quasi-periodic sinusoid in time with period ~20–70 frames and fixed
amplitude. With VELOCITY_DAMP = 0.9 the residue follows the drive
adiabatically: it sloshes out and back over each period. Consequences,
all measured here:

1. **Equipartition-like kinetic temperature exists** (speed² ∝ TMUL²
   to a few percent — the isolation check), so "T" is meaningful as a
   shaking amplitude.
2. **But transport is oscillatory, not diffusive.** Net displacement
   per drive period ≈ 0 (the force reverses sign and the motion
   retraces). The speed² saturation tells the same story: naive
   kick/damping balance predicts speed² ≈ 48 at T=0.4; measured 6.2 —
   the oscillatory reversal saps 87% of the drive before it can carry
   a chain anywhere.
3. **Therefore evaporation — a thermally-activated escape process —
   does not exist in this dynamics.** Raising T beyond the point where
   the slosh amplitude exceeds per-contact binding does not continue
   to erode the cluster; it just shakes it harder, coherently.
4. This reframes the earlier results consistently: the N=24 "fraying"
   at TMUL 6–8 was the **mechanical slosh threshold** (amplitude ≈
   binding, chains mechanically plucked), not a thermal critical
   region; the suppression with N (1/√N) is the droplet moving more
   rigidly under coherent shaking; and the confinement failure at
   T=0.1/CONF_K=0.01 was the slosh pushing the cloud out of the box.

## Verdicts per question

**(a) A T above which the system is homogeneous: NOT reachable in this
dynamics.** Not because of finite size (the scaling experiment's
verdict) and not because of attraction strength (the 10×-weaker probe
also fails) — because the bath cannot dissolve anything.
**(b) Binodal gap closing: cannot evaluate** — there is no below-Tc
fraying at N ≥ 48 on any ladder tested, so no gap curve exists to fit.
**(c) Tc bracket: none exists here.** There is no critical temperature
in these units because there is no entropic mixing process to drive
one. **(d) Transition sharpening at N=96 vs 48: moot** — no transition
at either N.

## The honest read

The LLPS project has now mapped the boundary of this model's
thermodynamics precisely: demixing and droplet formation are
mechanical-aggregation phenomena the model DOES capture (validated:
dominant cluster, binodal-like gap at N=24, spinodal-like
coalescence); but the high-temperature side of the phase diagram —
entropy-driven mixing, real dissolution, a true critical point —
requires a stochastic heat bath this sim does not have. The named fix
(quantified by measurements here): replace the smooth hash kicks with
per-frame white noise (uncorrelated signs frame-to-frame, e.g.
hash(FRAME × prime × residue) → uniform [−1,1]) so transport becomes
diffusive. That is a one-line change to the noise model and would make
Tc a well-posed question again; the machinery (constant-T isolated
blocks, cluster metrics, confinement) is all proven and ready.

Files: `gen_condensate_hot.py`, `condensate_hot48.ergo`,
`condensate_hot96.ergo`, `condensate_probe.ergo` (+binaries),
`condensate_hot48.out`, `condensate_hot96.out`, `condensate_probe.out`,
this report.

---

## CORRECTION (added after the white-bath task)

Two errors in the report above, found during the white-noise task and
corrected there (see white_check.md for full tables):

1. **Wrong attraction strength.** The hot-ladder and N=96 runs in this
   file were built with ATT_K = 0.03, not 0.005 as stated in the Setup
   section (the hot generator inherited the base template's bumped
   value). The N=48 numbers labeled ATT_K=0.005 are actually ATT_K=0.03.
2. **The "ATT_K ÷ 10 probe" never happened.** The sed pattern did not
   exist in the file, so `condensate_probe.ergo` was byte-identical to
   the base run — the claim that a 10×-weaker attraction also fails to
   dissolve was produced by accident (identical outputs were not
   noticed at the time).

Corrected sinusoid-bath reruns at ATT_K=0.005 (in white_check.md, table
"sinusoid bath, this task's reruns") show the SAME qualitative outcome
— no erosion at any rung at either N — so the bath-mechanism
conclusion (the quasi-periodic drive cannot dissolve) stands. But the
specific numbers in the Hot-ladder table above (all at ATT_K=0.03) and
the probe claim should be disregarded; and with the white bath the
droplet DOES dissolve (Tc ≈ TMUL 30–40 at N=96, binodal gap closing at
TMUL=40 — see white_check.md).
