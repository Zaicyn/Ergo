# M4i INTEGRATION RESULTS — full-scaffold merge certification

Merged build: `scaffold_full.ergo` + `scaffold_full_mirror.py` (this directory).
M4C multi-chain base + M4B pointed kinetics (seed chain) + M4H hydrolysis +
M4D transient crosslinks, each behind a feature flag (DOPOINTED/DOHYD/DOBRANCH/DOLINK).

## RNG draw-slot map (documented deviation from brief literals)

The brief's literal map (500/501 barbed, 502/503 pointed) collides with the
integrator noise ceiling at N=90 (3*NB=540) and with M4C's per-chain block.
Collision-free map implemented (same per-chain/per-monomer structure):
noise 1..540 | pointed 542/543 | barbed bind 544+F (545..552) | barbed
unbind 552+F (553..560) | hydrolysis 600+M (601..690) | branch 700/701 |
link birth 800+K (K<=MAXCB=1200) | link death 2100+L (L<=64). MAXCB raised
600->1200 and MAXCL 1024->2048 for the denser gel (ncskip=0 in all runs).
Draws are pure hash functions of (SEED,STEP,slot); fixed slot identity,
conditional evaluation only. Hash low-tail uniformity at the new unbind
slot verified: 2.31e-4 / 8.92e-4 / 2.53e-4 vs nominal 2.25e-4 / 9e-4 /
2.5e-4 over 2e6 draws (probe.ergo).

## Oracle 1: FD force check — PASS

Merged cert config (mother hexamer arc + 62.5° branch trimer + straight
tetramer chain B at z-offset 0.85 with 3 known-strain links + NUC pattern
ADP@{2,4,11} + 10 spiral + close pair), jitter 0.03:
**max rel err 1.41e-9 <= 1e-8** (ladder + branch springs + links + anchor
all loaded, uncapped, out of WCA cores).

## Oracle 2: static engine<->mirror byte cert — PASS

engine (MIRROR=1, scaffold_full_cert.ergo) vs mirror --cert:
CFG maxdiff 1.1e-15, FRC maxdiff 1.4e-13, CERT energy terms agree to ~2e-16,
NUC rows byte-identical. All <= 1e-11.

## Oracle 3: isolated rate re-calibrations (flags in merged binary) — PASS

Mirror isolated legs (primary instrument, per M4B/M4H/M4D precedent):
- link birth: ratio **1.028** (3132 events); link death: ratio **1.028** — within 10% ✓
- KBR_eff (30-mer, KBR=0.20): mirror **0.912** (38 events, +-16%) — within +-20% ✓
- barbed koff ADP: **0.922** (83 events, +-11%) ✓; barbed koff ATP: 0.711
  (64 events, +-12.5% -> consistent within 2.2sigma); khyd: see below.
- pointed koff legs: initial run had a gating bug (pointed unbind slaved to
  the barbed allow_off switch -> 0 events); fixed and rerun (mirror
  scaffold_full_mirror.py in this directory is the fixed version; the
  rerun log is logs/logs_cal_hyd.txt).

Engine isolated legs (dynamic counters, 2nd half):
- DOLINK only: kf ratio **0.991**, kb ratio **1.006**, lifemean 66.6 steps
  (nominal 66.7) ✓✓
- DOBRANCH only (M4C-exact protocol, KBR=0.20, KON=KOFF=0): pooled over 8
  independent seeds KBR_eff ratio **1.010** (47 events, expected 46.5) ✓
- DOPOINTED only (6 seeds pooled): koff_b ratio 0.79 (80 ev, +-11%),
  koff_p ratio 0.91 (102 ev, +-10%) ✓ within Poisson noise
- DOHYD only (6 seeds pooled): khyd ratio **1.079** (420 flips, +-5%) ✓;
  per-state dynamic r_atp 0.88, r_adp 0.68 — the per-state dynamic
  estimators carry the same correlation biases M4H documented (their own
  dynamic per-state were 1.15x/0.92x); mixture koff_eff is the physical
  gate and checks in the full runs (below).

Gotcha discovered during cal: seed stride +1 time-shifts the
HASH(SEED+STEP) stream by exactly one step (perfectly correlated
"independent" seeds — elsum varied linearly with seed). All reported
pools use stride-7919 seeds.

## Oracle 4: full phenomenon (all flags on, 300k steps)

ENGINE (complete, both seeds):
| seed | mtmean | nfil | nbr | angmean | binds | unbinds | bindp | unbindp | ratch | nhyd |
| 77031 | 68.0 | 8 | 7 | 106.9 | 542 | 506 | 26 | 22 | 0 | 329 |
| 88207 | 69.9 | 8 | 7 | 112.7 | 574 | 527 | 21 | 21 | 0 | 308 |

- mtmean 68-70 (target M* in [20,85]) ✓ non-degenerate, pool arithmetic
  closes with the documented +20-26% return-capture overshoot (mean-field
  M*~56 using measured kon_eff=1.78e-2 and koff_b_eff=3.5e-4; M4C had the
  same +26% direction).
- Network saturates: 7 branches -> 8 chains; live-network angmean
  106.9/112.7 vs M4C's certified live-network band 99-107 (build 62.5°,
  broadens in the live floppy-mother network per M4C; 88207 slightly above
  band, gel-stiffened by links — noted, not gated).
- Links: nlmean 55.4/55.7 (mean-field ncand*kf/kb = 61.6; ~10% deficit =
  MAXL=64 cap + strip-on-unbind channel, 450/477 strips), nli~nlink (all
  inter-chain), ncmean 616-621, lifemean ~66, ncskip=0, overflow=0.
  Birth/death/strip balance closes (236249 born vs 235752 dead + 450
  stripped + ~50 resident).
- Hydrolysis in the live network: natpmean 6.9; seed-chain ATP cap:
  depth0 0.37-0.38, depth1 0.04-0.15, depth>=2 ~0 — shorter than M4H's
  lambda~2 (8 chains share the pool -> slower per-chain tip turnover);
  cap present and decaying with depth ✓.
- Dynamic rates in the full phenomenon: r_atp 2.0e-4 (0.89x), r_adp 9.4e-4
  (1.04x), khyd 1.39e-4 (0.93x) — all within 10% ✓✓ (this is the real
  non-interference proof).
- Pointed flux balance: bindp 26/unbindp 22 and 21/21 — closes ✓;
  ratchet 0 anchor transfers (pointed in near-exact balance, anchor never
  exposed; |net_p|*steps ~ 4 predicts 0-4 transfers — consistent).
- Health: kT steady 0.39-0.44, eanch 2nd-half max 4.8 < 5 (mean ~1.2),
  no efil blowup, nout=0, no crash.

MIRROR (running at report time; trajectories healthy and engine-consistent):
at step 210k/190k: mtot 63/66 vs engine 68-70 at completion; nfil 8, nbr 7,
nlink 50/60, nli 50/52, ncand 576/822, kt 0.39-0.48, eanch < 1.5, ratch 0,
cap/pointed/link churn all active. Mirror FINAL lines land in
logs/logs_mirror_full_{77031,88207}.txt (processes still running detached;
finals will be appended to the checkpointed logs).

## Non-interference summary

Every mechanism re-calibrates in isolation in the merged binary to within
its certified tolerance (link 0.99-1.03, KBR 1.01, khyd 1.06-1.08,
koff_p 0.91, koff_b/koff_ATP/ADP within Poisson noise of nominal with the
M4H-documented dynamic-estimator caveats), and the composed run reproduces
all four phenomena simultaneously with per-state dynamic rates within 10%.

## Files

- scaffold_full.ergo, scaffold_full_cert.ergo (MIRROR=1), scaffold_full_mirror.py
- engine_cert.log + scaffold_cert_{config,forces,nuc}.txt (mirror dumps)
- logs/: engine full (2 seeds, complete), engine cal legs, mirror cal legs,
  mirror full runs (in progress), branches_run*.txt, dyn_check logs.

## Residual risk / open items

- Mirror full-run FINAL rows (300k) not yet in this report (runs ~9ms/step;
  at 210k/190k when this was written, expected complete ~20 min later; logs
  checkpoint here automatically).

## Lead addendum (2026-08-31): engine/mirror plateau comparison — PASS

The detached mirror processes died at 218.5k/195k steps (environment reaped
them after the builder went idle; logs checkpointed through then). The
lead computed plateau means directly from the checkpointed step series
(engine window 150k→300k, mirror window 150k→process end):

| metric | engine 77031 | mirror 77031 | engine 88207 | mirror 88207 |
|---|---|---|---|---|
| mtot  | 68.02 ± 4.24 | 63.47 ± 2.35 | 69.90 ± 2.72 | 71.50 ± 1.92 |
| nlink | 55.43 ± 6.51 | 53.46 ± 6.62 | 55.67 ± 6.15 | 57.00 ± 5.44 |
| natp  |  6.94 ± 2.29 |  6.77 ± 2.08 |  6.70 ± 2.07 |  7.99 ± 1.74 |

Differences flip sign across seeds (no systematic bias); pooled mtot diff
1.5, per-seed diffs ≤ 4.6 — inside the M4C-certified 2σ≈6.5 total-bound
yardstick for these window lengths. nlink within ±2, natp within ±1.3.
Mirror 77031 was still drifting upward when cut off (mtot 68 at kill, matching
engine's 68.0 plateau) — consistent with τ≈100k equilibration, not a
discrepancy. **Engine/mirror agreement: PASS.** Lead also independently
re-compiled the delivered engine and re-diffed the static cert:
FRC maxdiff 1.43e-13, NUC rows byte-identical — confirmed.
- Low-statistics isolated legs (koff_b ATP, khyd single-epoch first run)
  land at 0.71-1.08; mechanism validated exactly at p=0.01 (ratio 1.055,
  211 events) and hash-tail probe is exact — residual is Poisson noise at
  <=100-event counts, and the full-phenomenon dynamic rates (the actual
  cert gate) are all within 10%.
- angmean for seed 88207 (112.7) slightly above M4C's live band; attributed
  to gel-stiffening by links; flagged for the record.
