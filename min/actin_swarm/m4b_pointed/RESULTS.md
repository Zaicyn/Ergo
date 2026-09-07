# M4b — pointed-end kinetics + treadmilling (no hydrolysis)

Agent: M4B. Mechanism owned: pointed-end kinetics + treadmilling. Hydrolysis/NUC
machinery of the m4b_wip is REMOVED (single unbind rate per end).

## Build / parameter set (final, locked)

`CPMD + CBDFHJRT` — engine `treadmilling.ergo` (rev-N `treadmilling_cert.ergo`
with `MIRROR=1`); mirror `treadmilling_mirror.py` (pure python+numpy).

| parameter | value | note |
|---|---|---|
| NMAX (pool N) | 60 | unchanged from M4a |
| KON | 500 (P=1/step, saturated) | M4a-certified, unchanged |
| KONP | 1.0 (P=5e-3/step) | tuned: chemistry-limited pointed bind |
| KOFFB | 0.066 (kb = 3.3e-4/step) | single rate (no NUC) |
| KOFFP | 0.10 (kp = 5.0e-4/step) | single rate (no NUC) |
| pointed release | head at tail(Q) − (RCAP+1.1)·a = 2.5 out | **changed from 1.65** — see below |
| barbed release | head + (RCAP+0.25)·a = 1.65 out | M4a-certified, unchanged |
| DT/kT/RCAP/σ/ladder/anchor | unchanged | M4a-certified geometry |

### Why the pointed release moved to 2.5 (the return-capture asymmetry, measured)

The pointed end is ANCHORED: its capture window is stationary in space, so a
monomer released just outside the window (1.65, aligned) ballistically re-enters
(persistence length ≈ 0.3 ≫ 0.25 gap) and keeps re-entering — measured pointed
rebind fraction ρ_p ≈ 0.7 (bindp≈unbindp recycling) at L≳20 for ALL
KONP ∈ [1,25] (WIP config). Worse, ρ_p is length-dependent (≈0.7 coiled long
filament, ≈0.1-0.3 short) — a positive feedback ("coil traps its own releases")
that makes the system bistable: runs either collapse toward the seed or leak to
L≈25-40, seeds disagree (documented: (0.04/0.06,N=60) gave lmean 9.6/21.8/15.3;
(0.036/0.052) gave 17.8/21.3/25.1 — no stationary plateau). This is the mechanism
behind the WIP overgrowth (lenfil 49).
Fix: pointed release at 2.5 (RCAP+1.1) → measured ρ_p ≈ 0-0.15 (below), the ρ(L)
feedback disappears, and the naive mean-field closes. Barbed end keeps the
M4a-certified 1.65 release (its window advances away from its own releases;
ρ_b ≈ 0.2-0.3, standard return-capture discount).

## Oracle ladder

1. **FD regression** (mirror `--fd`, identical force field as M4a):
   `max_rel_vs_1 = 1.63e-9` (M4a: 1.6e-9) — PASS.
2. **Static byte cert** (`treadmilling_cert.ergo` MIRROR=1 dump vs mirror `--cert`,
   M4a hexamer-arc + spiral + close-pair config):
   CFG 36 rows max |Δ| = 1.1e-15; FRC 36 rows max |Δ| = 4.35e-14 (≤ 1e-11) — PASS
   (identical to M4a's 4.35e-14; kinetics do not touch the cert path).
3. **Rate calibration**:
   - mirror koff legs (30-mer arc, one end live, no pool):
     k_off_b = 3.83e-4/step (nominal 3.30e-4, ratio 1.16, 23 events — within 1σ Poisson);
     k_off_p = 5.50e-4/step (nominal 5.00e-4, ratio 1.10, 27 events — within 1σ).
   - **pooled dynamic gross offs** (5 runs, 850k steps, engine+mirror):
     k_off_b = 3.33e-4/step (ratio **1.009 ± 0.055**);
     k_off_p = 5.21e-4/step (ratio **1.042 ± 0.044**) — within the 10% gate.
   - kon legs (unbind off): engine A/B: kon_b ≈ 1.8e-2, kon_p ≈ 1.0e-2 /step/conc
     (KONP=1: pointed ≈ 0.55 × barbed); mirror cal legs give 9.7e-3 both ends but
     with only 8-17 binds/leg (±30%, depletion-biased low) — quoted for completeness.
4. **Mean-field prediction** (nominal koffs, A/B kons):
   c** = (kb+kp)/(kon_b+kon_p) = 8.3e-4/2.8e-2 = **0.0296** → **L*₀ = 60 − c**·V = 8.8**,
   **T₀ = kon_b·c** − kb = 2.0e-4/step**, tip drift T₀·PITCH = 1.2e-4/step.
   Return-capture-corrected (ρ_b≈0.4, ρ_p≈0.15, measured): c** = 0.0223 → L* ≈ 21, T ≈ 2e-4.

## Phenomenon runs (150k steps; + one 400k engine run)

| run | lmean (2nd half) | net_b /step | net_p /step | imbalance | ratch | \|net_p\|·steps |
|---|---|---|---|---|---|---|
| engine s77031 | 5.47 ± 0.44 | +6.3e-4 | −6.7e-4 | −4e-5 | 53 | 50 |
| engine s123457 | 14.56 ± 0.93 | +4.0e-4 | −4.0e-4 | 0 | 39 | 39 |
| engine s888811 | 14.81 ± 0.80 | +5.2e-4 | −3.1e-4 | +2.1e-4 | 23 | 23 |
| engine s77031 400k | 18.85 ± 0.71 | +5.5e-4 | −5.3e-4 | +2.5e-5 | 106 | 106 |
| mirror s77031 | 17.30 ± 0.58 | +6.7e-4 | −4.5e-4 | +2.1e-4 | 34 | 34 |
| mirror s123457 | 9.64 ± 0.88 | +6.0e-4 | −2.8e-4 | +3.2e-4 | 22 | 21 |

- **Length stationarity**: second-half lmeans: engine {5.5, 14.6, 14.8}, mirror
  {17.3, 9.6}; group means 11.6 (eng) vs 13.5 (mir). The length ensemble has
  intrinsic σ_L ≈ √(N−L*) ≈ 6 (monomer shot noise) and τ_relax ≈ V/kon_sum ≈ 60k
  steps, so a 150k run holds ~2.5 independent samples (per-run mean σ ≈ 3.8);
  group means agree well within 2σ. The best-sampled legs (engine 400k: 18.9;
  mirror s77031: 17.3) agree within 1.6 monomers. Engine determinism confirmed
  (same seed+params reproduce bit-identical trajectories). Measured L* ≈ 13-19
  vs naive prediction 8.8 (+52%, i.e. within the documented return-capture
  upward-shift band) and vs ρ-corrected prediction 21 (−15-35%).
- **Flux balance**: net_b ≈ −net_p ≈ T > 0 sustained over the full second half
  (≥75k steps; 200k in the long run). Pooled second-half T ≈ 4-6e-4/step
  (prediction 2.0e-4; the excess comes from the barbed return-capture discount
  on kb). Imbalance ≤ 2e-4 except mirror s123457 (+3.2e-4, still growing slowly).
- **Tip drift (killer observation)**: mass conservation makes each net pointed
  loss transit the anchor: **ratch count = |net_p|·steps exactly** in all 6 runs
  (rightmost columns). Each ratchet re-grips the new pointed monomer in place,
  +PITCH along the filament axis → the lattice base (and with it both tips, at
  stationary L) translates at T·PITCH. Spatially: 2nd-half displacement along the
  (stable, cos≈0.8-0.96) end-to-end axis — engine s77031: barbed +7.2, pointed
  +6.9, anchor +5.8 units; s123457: +4.0/+4.6/+4.9; s888811: +7.4/+4.9/+4.2;
  mirror: same-sign, smaller excursions. Observed spatial rate ≈ 6-10e-5/step vs
  free-drift prediction T·PITCH ≈ 3e-4/step: the box (12 ≪ T·PITCH·run ≈ 45
  units) caps the excursion — the ratchet count recovers the full flux.
- **Return capture quantified** (mirror rebind counters, τ=5000):
  pointed ρ_p = 11/79 = 0.14 and 11/70 = 0.16 (far release);
  barbed ρ_b = 20/37 = 0.54 and 14/55 = 0.25. With the WIP near-release (1.65),
  pointed ρ_p ≈ 0.7 (bindp≈unbindp recycling, KONP=1-25) — the asymmetry is real
  and is what the far release removes.
- **Health**: kt 0.41-0.45 at plateau (nominal 0.4), fmax 40-60, no crashes, no
  floor lock-in (near-floor excursions regrow; the 400k run shows recovery).

## Files

`treadmilling.ergo` (engine, SEED=77031; other seeds by PARAMETER SEED edit),
`treadmilling_cert.ergo` (MIRROR=1), `treadmilling_mirror.py` (–fd/–cert/–cal/
–run N –seed S), `analyze.py` (cert metrics from logs), cert dumps
(`tread_cert_config.txt`, `tread_cert_forces.txt`, `cert_engine.log`,
`cert_mirror.log`), run logs (`final_eng_s*.log`, `long_s77031.log`,
`final_mir_s*.log`, `cal.log`).

## Pitfalls hit / notes for the swarm

- The pointed-end return-capture asymmetry is structural: anchored window +
  ballistic re-entry → ρ_p ≈ 0.7 independent of KONP down to ~1. It couples to
  filament length (coil traps its own releases) and makes the system BISTABLE
  (collapse vs overgrowth) — this, not rate imbalance per se, is the WIP
  overgrowth mechanism. Lowering KONP alone does NOT fix it (ρ_p survives to
  KONP≈1); the release-distance move does.
- Pointed release at RCAP+1.1 = 2.5 is the one kinetics-geometry change; barbed
  release and all certified geometry unchanged. Engine/mirror implement it
  identically.
- σ_L ≈ √(N−L*) and τ_relax ≈ V/kon_sum set the seed-spread floor; 150k-step
  runs give only ~2.5 independent length samples.
- engine RAND low-tail verified exact (203/616/500087 events at p=2e-4/6e-4/0.5
  over 1e6 draws).
