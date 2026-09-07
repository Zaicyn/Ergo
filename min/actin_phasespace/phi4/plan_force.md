# Force/Membrane Rung (formin) — Plan (lock-step, single thread)

Green-lit: "force/membrane coupling it is then. Formin if I remember correctly."

Framing: the motility unit is a treadmilling filament doing work against a
load. Two-stage certification: bare Brownian-ratchet first (does the
exponential force-velocity law EMERGE from engine sterics with zero free
parameters?), then the formin gate (processive barbed-end coupling that
changes the force response).

## Stage F0 — geometry audit (BEFORE any design commitment)
The treadmill translates the filament toward the barbed side at
~j·PITCH ≈ 1.4e-4 σ/step ⇒ ~40 σ over a 300k run in a 12 σ box.
Question: do runs7-class runs end wall-stalled (uncertified force coupling
inside every certified steady state) or does the anchor geometry prevent it?
Audit: tips tracks (barbed head / pointed tail positions) from runs7 logs,
translation velocity vs j·PITCH, wall-approach distances, and where the
steady-state windows actually sat relative to the walls.

## Stage F0 — geometry audit: DONE (results)
- No ballistic treadmill drift: center MSD/lag falls 0.63→0.13 with lag;
  box-bounded diffusion. Certified steady states are bulk states.
- Filament-axis decorrelation ≈ 10-20k steps ⇒ measurement windows ≤ 10k
  steps; episode-based analysis.
- **The engine chain is FREELY HINGED**: ee = 4.4 vs contour 14.4 (n=25).
  Junction springs constrain distances, not angles. Actin-realistic bending
  stiffness is INCOMPATIBLE with the 12σ box at n̄=25 (a straight 25-mer is
  14.4σ). Defer bending physics; force assay is tip-local + clamped.
- Tips within 1.0σ of a wall 20% of the time (runs7) — box-size caveat,
  consistent across all certified rungs; piston contact force tagged per
  event to keep load accounting local.
- Barbed rates (runs7, 16 seeds): j_on = 5.58e-4, j_off = 3.59e-4 per step.

## Stage F1 — bare ratchet (force-clamp piston): REFINED
Oracle (PRE-REGISTERED, zero free parameters):
  v(F) = 0.6·(5.58e-4·exp(−0.6F/0.4) − 3.59e-4)   [PITCH·(j_on·e^(−Fδ/kT)−j_off)]
  F_s = (kT/δ)·ln(j_on/j_off) = 0.293 engine force units
  v0 = 1.19e-4 σ/step
The force CLAMP makes the load linear in insertion displacement
(work = F_ext·PITCH per insertion) even though contact is harmonic.
Experiment (piston_fpt.ergo, parent = pop_fpt, DIMERS=0 single filament):
  mobile plane ⊥ x at XP, one-sided harmonic contact (KPST=100, margin 0.5,
  same form as certified WALLS); overdamped deterministic motion
  XP += PMU·(F_react − F_ext)·DT, clamped [7.0, 11.3]; NO RNG draws.
  Instruments: pstn line per NDIAG (XP, window-mean reaction, contact
  steps); bbind event tags (step, monomer, filament, new-head gap, new-head
  contact force); TFHIST per-step histogram of tip contact force (dwell
  normalization ⇒ j_on(F) = events/dwell per bin, self-calibrated at F=0).
  Arms: F_ext ∈ {0.0, 0.1, 0.2, 0.293, 0.4, 0.6} × 16 seeds, 300k steps.
Gates: G-F1 PSTN=0 ≡ runs7 (0 diffs, shared lines); G-F2 parked piston
  (F_ext=0, XP0=11.3) rare-contact control; smoke test for force sanity.
Analysis: per-arm j_on(F_ext) and piston drift v(F_ext) vs oracle curve;
event-level j_on(force)/dwell from TFHIST as the within-arm cross-check;
F_ext=0.6 arm documents super-stall crush mode.

## Stage F2 — formin gate
Minimal formin: a processive barbed-tip element (one bit per filament,
tracks the tip on each bind) that (i) holds a standoff between tip and
obstacle (insertion allowed at contact), (ii) transmits load with a gated
spring: compression closes, tension opens (mDia1-class response).
Oracle: gated-ratchet prediction — shifted stall force, force-acceleration
window; processivity under load (no tip loss).
Falsification target: bare-tip v(F) exponential vs formin v(F) deviation.

## Deferred
Multi-filament load sharing (lamellipodium = population rung × force rung),
membrane surface physics (bending, surface tension), pointed-end anchors
under load.

## F1 execution log (this session)
- F1 ensemble v1 (300k steps, XPLO=7.0, NO insertion gate) — 96/96 FINAL,
  preserved stripped at runs10a/. **FINDING A (certified negative):**
  teleport-register insertion is FORCE-BLIND — j_on flat (~5.0-5.5e-4)
  across F_ext 0→0.6, no stall, F_stall=∞. Binds under contact rise
  0.3%→6.4% with load: the filament grows INTO the load zone and shoves
  the piston. A register that places mass without checking sterics does no
  work against the membrane. Insertion must EARN the gap (Mogilner-Oster).
- Fix installed: **SGATE** — barbed bind blocked when the new head lands
  inside the piston contact zone (PX(HP) > XP − XPMAR); NBLK counter;
  pstn line carries nblk; TFHIST stationary-half guard (dwell/event
  normalization consistency, P6). SGATE adds NO RNG draws.
- G-F1 re-run on SGATE build: **0 diffs** (PSTN=0 ≡ runs7). NOTE: sed
  parameter substitution must target the exact PARAMETER line text —
  a broad s/DIMERS = 1/DIMERS = 0/ corrupted the kinetic guards
  (DIMERS = 1 → 0 inside IF clauses) and produced a spurious gate fail;
  caught by head-of-log diff (dim/nuc lines at DIMERS=0).
- Smoke @ F_ext=0.293 (pre-registered stall): NBLK fires (180 blocks /
  ~186 commits over 300k), piston responsive — but <FRCT> still rising
  (0.015→0.15) and xp creeping (7.0→7.74) at 300k: NOT equilibrated.
  Piston parked on the XPLO=7.0 clamp early — clamp must never bear load.
- Ensemble v2 (RUNNING, /tmp/runs11): 1M steps (stationary half >500k),
  XPLO=5.5 (protective only), same 6 arms × 16 seeds. Measurements:
  v from piston drift AND PITCH·(j_on−j_off) cross-check; j_on(F) vs
  oracle exp(−1.5F); <FRCT> = F_ext force-balance audit; clamp occupancy.

## STATUS: force/membrane rung COMPLETE (certified)
F1 (bare ratchet): three architectures, three certified falsifications with
mechanisms (FORCE_LAW.md). F2 (formin): certified power-stroke class —
flat j_on to F=4, force balance when gripped, survival at all loads.
Engines: piston_fpt.ergo (SGATE), piston2 (+revert+thermal), piston3
(+ejection cooldown), formin_fpt.ergo (slip-grip ring + threading).
All gates 0 diffs (PSTN=0 ≡ runs7; FORMIN=0 ≡ piston3).
Data: runs10a (F1a), runs11 (F1b), runs13 (F1c), runs14 (F2).
Checkpoint: actin_phasespace_force_checkpoint.zip (132MB).
NEXT RUNG: lamellipodium = φ4 population × membrane (multi-filament load
sharing, brush engagement — the geometry where Brownian gating should
finally become measurable).
