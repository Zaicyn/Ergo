# ν(c) — the nucleation rate law, MEASURED (φ4 sub-law rung)

**Status: CERTIFIED (sub-law closure).** Assay `nuc_fpt.ergo` (dimer channel
+ instruments), 80-run ensemble (KNUC × KDIM surface, 8–16 seeds/point,
300k steps, certified toolchain `actin_swarm/toolchain`). Mirror gates:
DIMERS=0 bit-identical to runs7 seed 77031 (0 diffs / 39k lines); patch
identity DIMERS=0 vs unmodified source 0 diffs. Toolchain note: the upload
compiler copy differs from the checkpointed certified one (post-FMA-fix
divergence) — all φ4 work uses the checkpointed toolchain.

> **ERRATUM to the first draft of this doc:** the oracle-side arithmetic
> dropped a factor of 10³ (½·k2·c²·V at c=0.019 is 1.1e-2/step/box, not
> 1.1e-5) and — the deeper error — assumed Smoluchowski flux-limited
> encounter kinetics. The engine measures the actual regime: **occupancy
> gating**. Corrected law below. The "self-consistency echo" paragraph of
> the draft was therefore wrong and is replaced.

## The measured law: both legs are occupancy-gated

Engine bind kinetics are P = min(1, K·DT) per step while the candidate is
in the capture window. In a 12³ box with a dense pool, a qualifying pair
sits in-window for many steps — the formation rate is set by the
*equilibrium occupancy of the capture zone*, not by the diffusion flux to
it (Smoluchowski). Measured:

**Leg 1 — dimer formation:** ν2 = Ω₂·(KNUC·DT)/step, with the qualifying-
pair occupancy Ω₂ = 0.74–0.85 at the operating pool (c ≈ 0.017, ~29 free
monomers), independent of KDIM over 100× (0.12–12) and linear in KNUC over
10³ (0.1–500 arm ratios 9.0 and 9.6 vs KNUC ratios 10). Geometry check:
Ω₂ ≈ (N_free²/2)·V_shell/V·f_align with V_shell = (4π/3)(RCAP³−1.0³) ≈ 7.3,
f_align ≈ 0.5·f_orient² ≈ 0.2–0.4 — closes within a factor ~2.

**Leg 2 — third-monomer branch:** f3(KDIM) = 0.504 / 0.129 / 0.090 at
k_-2 = 6e-4 / 1e-2 / 6e-2 per step (KNUC=1.0 arm). Two additive channels:
- an arrival race (third monomer diffuses in during the dimer lifetime),
  dominant at long τ;
- an **occupancy floor ≈ 0.09**: P(a third monomer is already in the window
  at the moment of dimer birth) — dominant when τ ≪ transit time.
f3 floor ∝ c, arrival part ∝ c·(k3/k_-2) → **ν ∝ c²·f3(c): cubic-ish in c
at all KDIM** (effective exponent 2.3–2.9 across the sweep).

## The ν surface (per step per box, c ≈ 0.017)

| KNUC \ KDIM | 0.12 (τ=1667) | 2.0 (τ=100) | 12.0 (τ=17) |
|---|---|---|---|
| 500 (saturated) | 7.6e-3 (dimer-locked regime) | 5.7e-3 | 6.7e-3 |
| 1.0 (pointed-like) | 1.9e-3 | 4.9e-4 | 3.5e-4 |
| 0.1 | 2.4e-4 | 7.1e-5 | 4.4e-5 |

Regime boundaries discovered by the sweep:
- **KNUC saturated (500) + long-lived dimers → dimer-locked state**: NDIM*
  ≈ 17–21 dimers hold 2/3 of the pool, the filament starves to n ≈ 5.
  A legitimate phase of the model — the "dimer soup" — but not biology.
- **KNUC ≤ 1 → healthy filament (n* ≈ 20–25), dimers rare (NDIM* ≈ 0–2).**
  This is the biological corner: dimer formation is chemistry-limited
  (acceptance ~ pointed-end class), dimer unstable (τ ≲ 100 steps).

## Assay corner for the φ4 population rung

**KNUC = 1.0, KDIM = 2.0**: ν = 4.9e-4/step/box (one seed per ~2000 steps
per 60-pool box), k_nuc,eq = ν/c ≈ 0.029 — which lands exactly on the
sandbox's k_nuc = 3e-2 row (N_f* = 13, n̄ = 43, c* = 0.019 per 600-pool
box). The sandbox map and the measured law now join: the population assay
can be built with nucleation at its measured rate, and its steady state is
already predicted.

## Engineering errata folded into the assay (both certified by failure)

1. Inert trimers drain the pool 3 monomers/event and collapse the filament
   (lenfil → 3 by 300k steps). Sub-law assay recycles seeds to the pool
   after logging; filament promotion is the population rung.
2. The RCROSS=0.1 junction cross-pair sits inside WCUT; without BP
   neighbor-list exclusion the capped WCA turns every dimer into a
   stochastic blender (formation churn 30×). Dimer junctions carry full BP
   exclusion; trimer second junction uses 2 PITCH springs (all pairs
   outside WCUT, no cross spring).

## The transient precursor (measured)

The reaction is three-state, not two-state: m + m ⇌ **(m+m)\*** → d →
(+m) → trimer, where (m+m)\* is the encounter complex (in-window,
axis-aligned). Evidence:

1. **Memoryless conversion**: formation waiting-time CV = 0.95–0.96 at
   KNUC = 1.0 and 0.1 (pure Poisson); mean interval 266 steps vs
   1/(Ω₂·KNUC·DT) = 263 — exact closure. The precursor population is
   quasi-steady; conversion is a memoryless draw. Its internal clock is
   the ~125-step axis memory certified at the transport rung — the
   quaternion compression feeds directly into nucleation.
2. **The map**: trimer births are inward-shifted (mean r = 4.54 from the
   anchor vs ~5.5 uniform, all deciles shifted ~1 unit). Central gas
   depletion should suppress central nucleation; instead the recycling
   *flux* (release teleports at 1.65–2.5 units from the tips) enriches
   precursor encounters there — "the halo is a flux, not a pile-up"
   applied to birth. **Nucleation is spatially autocatalytic without
   attraction: the filament's shadow pre-draws the next filament's
   birthplace.**

Artifacts: phi4/nuc_fpt.ergo (assay), phi4/runs8/ (stripped logs:
dim/nuc/dimstat/step/occ kept, gm/geo dropped — deterministic engine +
seeded sources reproduce the rest), this doc.
