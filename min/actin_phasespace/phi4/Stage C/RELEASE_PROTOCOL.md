# Released-Piston Protocol Fix — Initial-Transient Artifact (Stage C, runs18)

## The snag

The runs17 `relx_*` released-piston arms (XPLO=1.5, XPHI=11.4, XP0=9.0, free
from t=0) cannot measure v(F). Every log shows, at the **first** logged step:

```
xpt 500 11.400000 97.994935      <- already at XPHI clamp, FRCT ~ 98
xpt 1500 11.400000 0.000000
```

and thereafter xp ∈ [10.7, 11.4], riding the clamp region for the whole 1M
steps. No drift phase exists to fit.

## Root cause

1. The plane starts at XP0=9.0 **inside** the initial monomer field
   (free gas seeded uniformly in x∈[2,10]; seed trimer at box center x=6.0).
2. At t=0 the brush does not exist yet → FRCT=0 → the load drags the plane
   toward −x at PMU·F_EXT·DT per step plus DP=0.2 diffusion.
3. The plane plows into the gas/brush interior; the first real contact is a
   deep-overlap spike (FRCT≈60–98 within 500 steps).
4. The spike flings the plane ballistically to the XPHI=11.4 clamp
   (ΔXP = PMU·FRCT·DT with FRCT~98 ⇒ ~2.4σ in a few hundred steps).
5. Once near the clamp it never leaves: brush contact force (~5.5) exceeds
   every load in the grid (≤4), so the plane re-pins at XPHI after each
   excursion. The clamp — not force balance — sets the position.

Consequence: any E1-style v(F) measurement on this protocol reads clamp
artifacts, not drift. The 6 relx runs remain valid as *held-brush* statistics
(pstn/occ tails), but not as velocity measurements.

## The fix: hold-then-release (engine `brush_bra_r.ergo`)

New parameter:

```
PARAMETER INTEGER :: PREL = 0    ! piston release step (0 = free from t=0)
```

The piston update + clamps are wrapped:

```
IF STEP >= PREL THEN
  XP := XP + PMU*(FRCT - F_EXT)*DT + SQRT(12*DP*DT)*(RAND(SN+4200) - 0.5)
  ...clamps...
ENDIF
```

Protocol for runs18: **PREL=300000** (brush equilibrates against the pinned
plane at XP0=9.0 for 6–7 filament lifetimes — clamped-arm lifetimes are
40–51k steps), then released with 2.4σ of drift room to the XPHI=11.4 clamp.
Hold-phase contact is physical (PISTON() force active throughout); only the
plane *motion* is gated.

## Certification

- Gate: `brush_bra_r` (PREL=0, PBR=0, NSTEPS=100000, SEED=77031) vs
  `brush_bra_b0` (identical config). Gate-filtered diff (xpt excluded):
  **0 lines** — the release gate is semantically inert at PREL=0 and xpt
  instrumentation does not perturb trajectories (deterministic hash RNG,
  WRITE-only).
- Gate artifacts: /tmp/r18/gate_b0.ergo, gate_r.ergo, gate_b0.gate,
  gate_r.gate, gate.diff (empty).

## Measurement plan (runs18)

Grid: F ∈ {0.5, 1.0, 2.0, 3.0, 4.0, 6.0} × seeds {77031, 84950} (12 runs,
1M steps). F≥3 arms added to bracket the stall (clamped arms imply stall > 4,
≈2× the certified unbranched 2.5–3).

Estimator (/tmp/r18/analyze_vf.py): discard [PREL, PREL+100k] (release leap +
re-equilibration), truncate at first xp ≥ 11.35 (clamp riding), binned OLS
slope of xp(t) (20k-step bins) + Theil–Sen cross-check; pstn-windowed ⟨fmean⟩
and ⟨neng⟩ post-release; clamp occupancy and xp min (XPLO-support check).

O-R5 scorecard: v>0 at F∈{0.5,1,2}; monotone v(0.5)>v(1)>v(2); v(3)/v(4)/v(6)
bracket the stall; ⟨FRCT⟩≈F_EXT sustained without XPLO support (xp min > 1.5).

## Outcome (runs18 complete, 12/12 verified nul=0)

**v-by-drift is geometrically unavailable in the 12σ box.** Post-release the
plane crosses the entire 2.4σ room in 2–10k steps (decompression +
brush-limited push of a brush that was *already stalled against the pinned
plane* — pstn ncon>0 from t≈20k: free gas is seeded across x∈[2,10], so the
brush fills space by nucleation+branching, not just tip advance from the
root). After the crossing, all runs sit clamp-adjacent (xp 10.7–11.35) with
no drift phase. Crossing-slope fits (5–10 points at 500-step cadence) are
noise-dominated and not F-ordered → not a measurement. Maturation and drift
timescales do not separate in this geometry.

**Force-form certification succeeds.** Stationary post-release balance
(Stage C/analysis/stage_c_force_analysis.py):

| F | ⟨fmean⟩ | margin (⟨f⟩−F) | clamp occ | ⟨neng⟩ |
|---|--------|----------------|-----------|--------|
| 0.5 | 5.23 | +4.73 | 0.57 | 3.34 |
| 1.0 | 5.36 | +4.36 | 0.54 | 3.43 |
| 2.0 | 5.71 | +3.71 | 0.42 | 3.59 |
| 3.0 | 5.99 | +2.99 | 0.33 | 3.73 |
| 4.0 | 6.57 | +2.57 | 0.27 | 4.07 |
| 6.0 | 7.57 | +1.57 | 0.15 | 4.54 |
| 8.0 | 8.53 | +0.53 | 0.04 | 4.83 |
| 10.0 | 10.27 | +0.27 | 0.02 | 5.38 |
| 12.0 | 12.05 | +0.05 | 0.00 | 5.87 |

(bracket arms F=8/10/12 added as runs18b, same protocol, 6/6 verified)

- ⟨fmean⟩ > F at every grid point up to F=10, margin ≈ 0 at F=12 →
  **stall F\* ≈ 12 measured directly** (no extrapolation) — ≈4× the
  certified unbranched 2.5–3. Consistent with the thin-brush pinned stall
  (hold phase) 11.4 ± 0.4: the system stall is set by the compressed-brush
  limit. Margin is monotone decreasing and concave (compression recruits
  engaged tips, ⟨neng⟩ 3.3 → 5.9, flattening the approach to stall).
- Margin and clamp occupancy decline **monotonically** with F (velocity
  ordering expressed in force form); stall force itself *rises* under
  compression (5.2 free → 12.1 at F=12): compression-dependent stall with
  load-adaptive tip recruitment, key input for the φ5 closure.
- F=2 arm: ⟨FRCT⟩=5.7 ≥ 2 with xp min 9.6–10.1, never touching XPLO=1.5 ✓.
- Hold-phase load-independence check: hold-end fmean/neng identical across F
  for fixed seed (F enters only via the gated piston update) ✓ engine
  consistent.

**True v(F) drift requires a tall-box engine** (LBOX≈24, root near wall, gas
confined below the plane at seeding, NMAX≈2000 → RNG slot-map rebase + new
generation gates). Estimated ~1–2 h build/certify + 10–15 min/run. Deferred
pending user decision.
