# LAPLACE QUICK-CHECK on the branched brush (pre-Stage-C screening, 2026-09-02)

Question: does the certified transport oracle (screened-Poisson/Laplace solver,
FFT-preconditioned, TRANSPORT_ORACLE_RESULTS.md) transfer to the R5 branched
brush, and what needs tweaking before quantitative use?

Method: geometry-dump variant brush_bra_geo (ftd lines = per-filament tip dump;
WRITE-only instrumentation, trajectory-invariant). 8 stationary snapshots
(step>200k, F=0.1 clamped arm, seed 77031), N=48 grid, per-filament barbed
Dirichlet sinks + pointed radiation sinks + teleport-blob sources (barbed
head+1.65a, pointed tail−2.5a — brush engine's exact rules), wall layer,
connected-component pocket removal (new — the dense brush seals fluid pockets
that make the Neumann system singular; the single-filament geo lineage never
hit this).

## Applicability verdict

| aspect | status |
|---|---|
| n≥16 certified domain | brush n̄≈9-12 — OUT of certified domain (documented 2× overshoot regime for n=8-15) — but see "structural findings": the engaged subpopulation is what matters |
| kT/D tweak | NOT needed — results insensitive to D×1.5 (kT_eff 0.6 vs 0.4) |
| βP (pointed reactivity) renormalization | INSUFFICIENT — no value reproduces the engine's barbed/pointed capture split (solver floor 0.49-0.56 vs engine 0.307 even at βP=2.5 = 1000× geo nominal). Both sinks transport-saturate; the gap is not a rate, it's dynamics |
| pointed hemisphere sink mask | implemented (rear cone); does not close the gap alone |
| correct reduced model | **hybrid**: Laplace supply field × certified dynamical suppression (fresh-monomer blocking delay + treadmill escape, §3.4/§3.5 of the transport cert) |

## Hybrid validation (the one number that matters)

solver per-tip barbed supply 1.47e-4/step × 0.574 suppression
(engine/oracle fast-return ratio 0.442/0.77, certified geo rung)
= 8.4e-5/step vs engine measured per-tip barbed capture 1.14e-4/step
→ **ratio 0.74** (26% low, order-unity, no fitted parameters; the short-n
regime accounts for the residual, consistent with the documented 2× bound).

## Structural findings (robust — geometry statements, βP-independent)

1. **Engaged tips enjoy 1.4× supply favoritism** over behind tips (they sit
   at the shadow boundary facing the open reservoir). Transport does not
   starve the membrane — the supply side of protrusion is favorable.
2. **Supply is length-flat** across n=3-22 (1.4-1.6e-4/step), dipping only
   for n=22-40 (deepest-shadow long filaments).
3. **Engaged tips are SHORT (n̄_eng=9.3)** — with anchored branching, the
   membrane-engaged subpopulation is membrane-BORN daughters, not long
   reachers. The old "need len≥15 to reach" bottleneck applied to
   slab-born filaments only; S4 bypasses it structurally.
4. The brush is **pointed-dominated** (release ratio 11.5:1, capture ratio
   2.3:1) — the pool is set by pointed-sink throughput; when pointed sinks
   are made strong, the solver pool lands at 0.0125 vs engine 0.0174.

## Tweaks adopted / deferred before quantitative brush use

- ADOPTED: fluid-pocket connected-component removal (else singular; CG
  silently returns garbage without the info==0 assert — found the hard way).
- ADOPTED: rear-hemisphere pointed sink mask; βP ≥ 0.25 (transport-limited).
- ADOPTED: hybrid suppression factor 0.574 on barbed capture.
- DEFERRED (needs engine instrument): pointed release blobs currently reuse
  the barbed axis (pointed axis not logged); add pointed axis to ftd dump if
  the pointed throughput gap (solver captures ~65% of engine's pointed flux)
  needs to close below 1.5×.
- NOT NEEDED: D rescale for the 0.6 kT plateau.

Artifacts: /tmp/r17/laplace_check.py, laplace_calib.py, laplace_calib2.py
(drivers); bra_geo.log geometry source (brush_bra_geo.ergo variant).
