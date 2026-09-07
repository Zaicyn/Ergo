# φ4 Population Rung — Certification (POPULATION_LAW)

Date: 2026-09-01. Engine: pop_fpt.ergo (nuc_fpt + trimer promotion +
multi-filament table). Oracle: popsim_pop.py (pre-registered BEFORE any
engine run — see POP_ORACLE.md). Corner: KNUC=1.0, KDIM=2.0 (measured
ν = 4.86e-4/step/box at c=0.0212). Ensemble: 16 seeds, 300k steps,
stationary half ≥150k. Certified toolchain (actin_swarm/ergo_mcl).

## Mirror gates
- **G1: PASS, 0 diffs.** pop_fpt DIMERS=0 ≡ runs7 (ge_77031), all shared
  lines byte-identical ([ergo]/# /census/fil/POPSTAT/NFILH/dimstat filtered —
  additive instruments only). The per-filament restructure, slot arithmetic
  500+4(F−1), and floor switch are invisible to the certified trajectory.
- **G2: PASS, 0 diffs.** pop_fpt DIMERS=1,KNUC=0 ≡ nuc_fpt DIMERS=1,KNUC=0.
  No floor-hit occurred in 300k steps (0 fdeath) — the dissolution branch is
  exercised only in the population ensemble, where conservation certifies it.
- **G3: PASS.** Corner smoke: no explosion (FMAX ≤ 455 transient, kT stable,
  ewca ~ −1..−4.5), 94 births / 91 deaths, POPSTAT nover=0.
- **Pool conservation: EXACT.** census nbound+nfree+2·ndim = 60 at every
  NDIAG of all 16 runs. Ensemble mean: 28.6 + 31.3 = 59.9.

## The headline: the dwarf population is REAL
Oracle pre-registration (which the orchestrator's plan sketch got WRONG —
it guessed N_f oscillating 1↔2 around an incumbent; the oracle said 3.4
dwarfs and the engine confirms the oracle, not the sketch):

| Observable | Engine (16 seeds) | Oracle (pre-registered) | Verdict |
|---|---|---|---|
| N_f* | 3.57 ± 0.34 | 3.42 ± 0.26 | **CONFIRMED** |
| births = deaths | 44.1 vs 44.8 /1.5e5 steps | 451/1.5e5 (rate below) | **CONFIRMED** (stationary current) |
| inter-birth CV | 1.03 ± 0.17 | 1.0–1.1 | **CONFIRMED** (memoryless) |
| aB (barbed tip ATP) | 0.825 ± 0.018 | 0.810 | **CONFIRMED** |
| c* | 0.0166 ± 0.001 | 0.0220 ± 0.0007 | **GAP — explained (below)** |
| split | 0.763 ± 0.028 | 0.683 ± 0.010 | **GAP — explained** |
| n̄ | 8.77 ± 1.31 | 6.53 ± 0.90 | follows c* via conservation (not independent) |
| aP | 0.508 ± 0.052 | 0.643 | **GAP — explained** |

N_f distribution (engine census | oracle): 1: 0.018|0.065, 2: 0.153|0.178,
3: 0.313|0.292, 4: 0.310|0.266, 5: 0.171|0.144, 6: 0.034|0.045.

## The c* gap is the halo, and it transports ν correctly
The engine's population pins the GLOBAL pool at c* = 0.0166, below the
sandbox's 0.0220. The engine has space; the sandbox doesn't. Released
monomers re-enter near their parent filament (the recycling halo measured
in the sub-law rung), so TIPS feed from a locally enriched field while the
global pool settles lower. Two independent confirmations:
1. **ν(c) transports**: at the engine's own c*, the measured law predicts
   ν = 4.86e-4·(0.0166/0.0212)^2.6 = 2.56e-4/step; the engine measures
   2.94e-4/step — ratio 1.15, and the 15% excess is itself halo enrichment
   (births happen where local c > global c).
2. **Newborns survive better than the oracle said**: P(reach 8/12/16) =
   0.120/0.059/0.020 engine vs 0.084/0.022/0.009 oracle; lifetimes
   11.3k vs 5.9k steps. New filaments born inside a halo feed from it.

The split/aP gaps are the same lesson at the pointed end: the sandbox's
PSPLIT=0.47 fixed on-ratio (calibrated at n̄≈25) over-weights pointed
capture for dwarf filaments; in the engine pointed binding is
chemistry-limited (KONP=1.0) and relatively rarer at short lengths →
split shifts barbed-ward (0.763) and pointed combs age (aP 0.51 vs 0.64).
**Oracle refinement for φ5: on-rates must be per-end chemistry, not a
fixed ratio, and the effective c at a tip is halo-renormalized.**

## The population birth map (engine-exclusive; oracle is blind)
- Births are NOT tip-seeking: min distance birth→nearest barbed head
  4.90 vs permutation null 4.88 (n=704; deciles identical). No signal.
- Births ARE halo-seeking: min distance birth→nearest other BOUND monomer
  5.95 vs far-time null 6.66 and uniform-point null 6.53 (n=234; every
  decile shifted ~0.6–0.7). The recycling field around the filament BODY,
  not the tip, pre-draws the next filament's birthplace.
- This is the population-level reading of the sub-law rung's inward-shifted
  birth map: spatial autocatalysis without attraction, mediated by the
  dissipation field of existing filaments.

## Regime notes
- NDIM at the corner: 0.24 mean, max 3 — no dimer soup (KDIM=2.0 fast
  dissociation, as designed). The soup regime (KNUC=500, KDIM=0.12:
  NDIM*≈17-21) is absent here.
- NFILH (full-run, seed 77031): P(N_f≤1)=0.006 — the box is essentially
  never empty; P(N_f≥6)=0.02. The population is self-sustaining from the
  seed onward; homogeneous nucleation maintains it after the seed dies.

## Status of the three sandbox predictions
1. Stationary birth-death current: **CONFIRMED** (44.1 vs 44.8, and the
   rate is the measured ν(c) law evaluated at the engine's own c*).
2. c* pinned: **REVISED** — pinned yes (±0.001 across seeds), but at 0.0166,
   not 0.022; the spatial halo renormalizes what "c" a tip sees. The
   conservation closure c*V + N_f·n̄ = 60 is EXACT on both sides.
3. Hazard CV ≈ 1: **CONFIRMED** (1.03 ± 0.17).

## Assay design notes (for the archive)
- MAXF=10 slots, never overflowed (oracle: P(N_f>8)<0.002; engine max 7).
- Filament slots recycle by lowest-free-index; slot 1 doubles as the legacy
  instrument view (occ/geo/tips lines are slot-1; census is authoritative).
- Transient NOUT (1–3 beads past the wall at release/dissolution teleports)
  is bounded, soft-walled back, kT-stable; inherited convention.
- runs9/: 16 stripped logs (gm/geo dropped; deterministic engine + seeded
  source reproduce) + pop_77031.full.log + G1/G2 gate logs + driver script.
