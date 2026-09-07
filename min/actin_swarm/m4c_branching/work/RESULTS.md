# M4c — Dendritic Branching (Arp2/3-like side nucleation): RESULTS

Multi-filament refactor of the certified M4a dumbbell engine + Arp2/3-like
branch nucleation. Deliverables: `branching.ergo` (engine), `branching_cert.ergo`
(MIRROR=1 static-cert variant), `branching_mirror.py` (FD/cert/calibration/dynamics
mirror), oracles (`ode_oracle.py`, `angle_oracle.py`, `compare_runs.py`), cert dumps,
and all run/calibration logs.

## Model

- **Topology**: NFMAX=8 chains; per-chain pointed/barbed/mlen/live/host arrays;
  monomer→chain map; bond list rebuilt (dirty-flagged) after kinetics in fixed
  order (ladders by ascending chain, then branch springs). Seed trimer = chain 1.
- **Kinetics**: per-chain barbed-end bind/unbind EXACTLY as certified M4a
  (KON=500 saturated, KOFF=0.09, RCAP=1.4 window, register teleport, release at
  1.65, MLEN>3 floor), looped over all live chains, fixed RNG draw slots.
- **Branch event**: each step, NELIG = # eligible hosts (bound, non-barbed,
  unprotected, not a branch-base d1/d2, ≥3 barbed-side neighbors, neighbors
  unprotected). If a chain slot is free and ≥3 pool monomers remain:
  fire iff UBR1 < KBR·DT·NELIG; host = INT(UBR2·NELIG)-th eligible monomer.
  Daughter TRIMER spawned from the first 3 free monomers at build angle 62.5°
  to the host axis, offset BLAT=0.9 lateral / BAX=−0.2 axial; daughter pointed
  end capped, barbed end elongates normally; host..host+3 unbind-protected.
- **Attachment**: 8 branch springs (KFIL=100) pinning daughter d1/d2 beads to the
  4 consecutive host-segment beads (rests BRB1..BRB8 from ideal-straight geometry,
  tabulated in the engine). 70° is EMERGENT — no angle potential; the build angle
  (62.5°) is calibrated so the thermally relaxed mean is 70° (see below).
- **Pool raised N=60→90** (box 12³ unchanged; density 0.052 still dilute).
  On-rate re-verified post-raise (below).

## Oracle ladder results

1. **FD cert** (mirror, branch-loaded config, jittered): max_rel 1.41e-09 ≤ 1e-8. PASS
2. **Static byte cert** (mother hexamer on arc + branch trimer at build angle on
   monomer 3 + 10 spiral + close pair; formula-generated, no RNG):
   config max|Δ| 1.11e-15, forces 1.43e-13, energies ~1.5e-15 — all ≤ 1e-11. PASS
3. **Rate calibrations**:
   - KBR_eff (isolation: anchored 30-mer, KON=KOFF=0, KBR=0.20):
     engine 56 seeds/40k steps: 336 events, ELSUM=294,095 → KBR_eff = 1.142e-3
     (ratio 1.142±0.055 vs nominal 1.0e-3); mirror 6 seeds: 36 events → 0.875e-3
     (±0.167); combined 372 events → 1.110e-3 (ratio 1.110±0.052). The ~+11%
     effective-rate renormalization over bare KBR is the calibrated value used
     in the mean-field predictions below (RAND low-tail uniformity verified
     separately: 0.000985/0.009947 vs 0.001/0.01 over 2e6 draws).
   - kon, multiple live chains (mother hexamer + branch trimer, unbind off):
     with pool depletion integrated, slope ≈ 2.0–2.2e-2 /step/conc, consistent
     with M4a's 1.73e-2 (multi-window capture across chains slightly raises it;
     25 events, ±20%).
   - koff multi-chain (mother 8-mer + branch trimer, bind off): 5.6e-4 ±70%
     (2 events) vs nominal 4.5e-4 — consistent; M4a's 0.8×return-capture factor
     within noise. Protection floor verified: unbinding halts at MLEN=3 and at
     HPROT barbed ends.
4. **Dynamic runs** 150k steps ×2 seeds (77031, 88051), engine + mirror:
   - total bound M (2nd half): engine 67.53/67.17, mirror 67.19/64.71 →
     pooled diff 1.39 < 2σ=6.53. PASS
   - branch count: 7/7 engine, 7/7 mirror (NFMAX−1 slots all filled). identical.
   - per-chain lengths (all chains): engine 8.42±5.16, mirror 8.24±4.26,
     diff 0.17 < 2σ=9.47; histograms same shape. PASS — daughters elongate and
     share the mother's plateau statistics.
   - network kT pinned at 0.40±0.05 throughout; no crashes, no mass leaks
     (mtot+nfree=90 at every diag).

## Phenomena

1. **Branch count vs mean field**: dB/dt = KBR_eff·NELIG(t)·[slot free]·[pool≥3].
   Using engine/mirror-tracked per-step ELSUM=ΣNELIG (exact gate bookkeeping):
   predicted total births over 150k = 21.4 (4.97/5.19 engine, 8.94/3.35 mirror),
   observed 28 (7 per run) → ratio 1.31±0.19, consistent at ~1.6σ Poisson.
   B(t) trajectory tracked ∫KBR_eff·NELIG dt throughout (saturation at NFMAX−1=7).
2. **Branch angle 70°**: certified on the isolated junction (frozen straight
   mother, thermalized daughter, `angle_oracle.py`): relaxed mean **69.2±7.4°**,
   median 68.1°, q05/q95 = 59.7°/82.4° — peaks at 70°, mean within ±10°. PASS.
   The 62.5° build angle compensates a measured +7.5° entropic tilt bias of the
   flexible junction. In the live network the instantaneous angle vs the host
   axis broadens to ~99–107° mean (sd 24–33°): the mother filament is
   conformationally floppy (M4a ee/contour≈0.3) and local kinks across the
   4-monomer anchor span tilt the rigidly-held daughter. Birth angle vs host
   axis is exactly 62.50° in every engine BRANCH log line. This is physical —
   real 70° branches are likewise defined on straight mother segments.
3. **Daughter growth**: daughters elongate from trimers to the shared plateau
   (final per-chain lengths e.g. engine 77031: 10 20 9 6 6 8 8 4; mirror:
   12 8 3 7 11 15 3 4); daughter/mother length statistics agree within 2σ
   (above); per-chain mass balance exact.
4. **Mass balance vs multi-chain ODE**: dM/dt = (kon_eff·c − koff_eff)·NF +
   3·dB/dt, c=(N−M)/V, NF=1+B, with kon_eff/koff_eff calibrated from the run's
   own event counts. Predicted vs measured 2nd-half M: engine 66.9 vs 67.5
   (77031), 67.6 vs 67.2 (88051); mirror 68.1 vs 67.19, 65.3 vs 64.71.
   Agreement ≤1 monomer everywhere. PASS

## Bug fixes during build (for the record)

- FILBONDS FX/FY register typo (energy pump) — found by A/B vs M4a@N=90 + mechanical subroutine diff.
- M4a's bonded-partner arrays (BP1/BP2) were asymmetric for interior monomers
  (harmless at M4a geometry: ladder pairs at 0.6 > WCUT). Cert jitter pushed a
  branch-chain ladder pair inside WCUT and leaked a WCA force (byte-cert force
  mismatch 1.3 with matching energies). Rebuilt as fully symmetric 6-slot
  BP1..BP6 (3 ladder + 3 branch). Byte cert clean after fix.
- Two-spring/4-spring/6-spring branch attachments left the daughter base
  orientation underconstrained (flop to ~90–160°); the 8-spring design fixes
  (z,ρ) of every d1/d2 bead and locks azimuth via the daughter ladder.

## Recommended final parameter set

NMAX=90, NFMAX=8, LBOX=12, DT=0.005, kT=0.4, KON=500, KOFF=0.09, KBR=0.02
(KBR_eff≈1.1e-4/monomer/step; fills all 7 branch slots in ~3–30k steps),
build angle 62.5° (C70=0.46174861323503386, S70=0.88701083317822171),
BLAT=0.9, BAX=−0.2, BRB1..BRB8 as tabulated in branching.ergo, NSEEDP=3.

## Files

- `branching.ergo`, `branching_cert.ergo`, `branching_mirror.py`
- `branch_cert_config.txt`, `branch_cert_forces.txt` (+ engine cert log)
- `run_engine_{77031,88051}.log`, `run_mirror_{77031,88051}.log`,
  `ang_*.txt`, `branches_*.txt`
- `kbr_calib.log` (56 engine seeds + 6 mirror seeds), `cal23_mirror.log` (kon/koff legs),
  `cal_engine_*.log` (per-seed engine calib, in work/)
- `ode_oracle.py`, `angle_oracle.py`, `compare_runs.py`
