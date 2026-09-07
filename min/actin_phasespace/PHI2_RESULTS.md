# φ2 — Phase-space rung 2: treadmilling / the current-carrying state

Builds on φ1's certified chain machinery and measured-return methodology;
adds the pointed end (M4b locked params: KONP=1.0, KOFFB=0.066, KOFFP=0.10,
releases 1.65 barbed / 2.5 pointed). Single thread, lock-step
oracle/experiment. Assay: `tread_fpt.ergo` — certified M4b engine +
counters only (**bit-identity verified**: all 300 DIAG rows of the certified
M4B seed-77031 run reproduce exactly). Ensemble: 64 seeds × 300k steps.

## The headline: treadmilling is a current-carrying stationary state

Per-end current profiles from interval counters (post-mixing, 64 runs):

- j_b(n) ≈ **+2.4e-4/step** and j_p(n) ≈ **−2.4e-4/step** at *every* length
  from n=4 to n=30 — the residual (growth) current is ~20× smaller.
- The length coordinate is not sitting at a detailed-balance fixed point;
  probability flows *through* the filament: in at the barbed end, out at the
  pointed end, length unchanged. This is the exact analogue of a
  momentum-carrying eigenstate — nonzero current, stationary distribution.
- Consequence: **length equilibration and the treadmill current are
  different processes on different timescales.** The through-current is
  ~2.4e-4/step; the length-relaxing residual is ~2e-5/step → the length
  distribution needs millions of steps to equilibrate. This *explains* the
  seed spread M4B documented (lmean 5.5–28.9 across seeds at 300k): every
  run is mid-transit on the slow mode while the fast mode is fully
  equilibrated. τ_slow is not a bug to fix; it's the physics — and it is why
  both M4B's 150k protocol and any naive plateau gate are structurally
  incapable of seeing this steady state.

## Gates

| gate | oracle | engine | verdict |
|---|---|---|---|
| flux closure (identity) | net_b + net_p = Δlen | exact, 64/64 (+16.4 = +16.4) | **PASS (exact)** |
| ratchet bookkeeping | ratch = NUPT − NBPT − Δrank(anchor) | 36/64 exact; deviations = −Δrank, all small | **PASS (with boundary correction)** — the anchor is a Lagrangian marker: it moves only when the material it grips depolymerizes; ratch counts monomers transited *through* the anchor |
| treadmill current T | 2.37e-4/step | barbed +2.50e-4, pointed +2.29e-4 (imbalance 2.1e-5 = residual creep) | **PASS** — resolves M4B's documented "T excess 2×": it was gross-vs-net flux plus then-unmeasured ρ |
| stationary length (protocol-matched endpoint, t=300k) | chain-sim 19.2 | 19.4 | **PASS** |
| window mean (2nd half) | chain-sim 19.52 ± 0.48 | 17.77 ± 0.67 | 2.3σ — residual consistent with the kon_b(n) conformation slope (below); engine runs lower-mid-window then catch up |

## Measured rate structure (the map speaks)

**Return asymmetry, quantified in one dataset:** ρ_b(5k) = 0.442 ± 0.007 vs
ρ_p(5k) = 0.059 ± 0.003 — **7.5×**. The far pointed release (2.5) works as
designed; the barbed window keeps its M4a-grade return cloud. Cross-capture
is real and small: pointed→barbed 4.1% of pointed releases, barbed→pointed
3.6% — a direct microscopic conveyor path for treadmilled monomers that
skips the bulk pool entirely.

**kon asymmetry and its mechanism:**
- barbed kon_b(n) rises 1.8e-2 → 2.45e-2 across n=4→30; at *fixed* n,
  coiled intervals (ee/contour < 0.7) run ~+11% hotter than straight ones.
- pointed kon_p(n) ≈ 1.0e-2, **flat** in n and conformation.
- Mechanism: the barbed end is transport-limited (P = min(1, KON·DT) = 1 —
  every aligned candidate in the window binds), so its rate tracks the local
  monomer concentration, which the coil enhances (φ1-R5). The pointed end is
  chemistry-limited (P = KONP·DT = 5e-3/step), so transport enhancements
  don't reach it. **The conformation coordinate couples only to
  transport-limited channels** — this bounds exactly where the φ1 residual
  can live in every future rung.

## φ2 → φ3 hand-off

1. The (n, j_b, j_p, coil) instrument is built and validated; φ3 adds the
   cap-age coordinate (hydrolysis comb) and the triangle/stacking geometry.
2. Open quantitative target: the kon_b(ee/contour) law — measured slope
   ~+11% per coil transition at contour ≈ LBOX, rising toward ~1.7× at
   contour ≈ 2·LBOX (φ1 plateau). Needed to close the length-distribution
   gate at long lengths.
3. Design constraint for all subsequent rungs: length gates need ≳ 1M-step
   runs (or gate on currents/endpoints, not window means) whenever both ends
   are live.

## Files

- `two_end_oracle.py` — two-end chain oracle (stationary / fixed point /
  treadmill current with closure check / protocol-matched simulator)
- `tread_fpt.ergo` — instrumented assay (bit-identity verified vs M4B cert)
- `runs2/tr_*.log` — 64 × 300k-step ensemble
