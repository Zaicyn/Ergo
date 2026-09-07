# M4a — Actin scaffold pilot: nucleation, elongation, steady state

Single-filament pilot. A seeded trimer nucleus elongates at the barbed end by
reversible binding from a finite G-actin pool; pool depletion drives the
system to a steady-state length. Mirror-first, oracle-first: forces
FD-certified, static state byte-certified against the Python mirror, kinetics
rate-calibrated before any phenomenon is claimed.

## Model

**Monomer = polar dumbbell**: head bead + tail bead, intra bond KBOND=100 at
rest R0=0.5; axis a (tail→head) is the polarity, head side = barbed (+),
tail side = pointed (−).

**Filament junction = triangulated ladder.** Consecutive monomers p→q are
linked by three harmonic springs (KFIL=100): head_p–head_q and tail_p–tail_q
at rest PITCH=0.6, plus the cross spring head_p–tail_q at rest
RCROSS=PITCH−R0=0.1. Bending stiffness is emergent from the ladder geometry;
bonded pairs are excluded from the pair potential (engine BP1/BP2 arrays,
mirror exclusion mask).

**Pair potential**: all non-bonded, non-same-monomer bead pairs are WCA with
σ=0.5, ε=1, cutoff 2^(1/6)·σ=0.5612. No bulk attraction — G-actin stays a
gas below criticality by construction; all cohesion flows through the kinetic
bonds. (σ=0.5, not 1: at σ=1 the second-neighbor pair head_i–tail_{i+2} sits
at 2·PITCH−R0=0.7 < 2^(1/6), inside the capped core — FD-invalid by
construction. At σ=0.5 the closest non-bonded pair is 0.7 > 0.5612, outside
the cutoff.)

**Nucleus**: trimer, pre-bonded, straight along x at box center; monomer 1's
two beads held by soft springs (KSEED=5) to their initial positions —
a nucleation-promoting factor. Pointed end capped by design (M4b+ hook);
only the barbed end is live. Length floor MLEN>3 for unbinding (seeded-assay
convention).

**Kinetics** (deterministic hash-seeded draws, one bind draw + one unbind
draw per step, both sides):

- **Bind**: a free monomer m is a candidate when |r_tail(m) − r_head(barbed)|
  < RCAP=1.4 and a_m·a_barbed > QMIN=0.0. First candidate accepts with
  P = min(1, KON·Δt) per step (KON=500 → saturated at 1, diffusion-limited).
  On accept the monomer **teleports to register**: tail at
  r_head(barbed) + RCROSS·a_barbed, head at tail + R0·a_barbed; the three
  junction springs are created.
- **Unbind**: the terminal barbed monomer leaves with P = KOFF·Δt per step
  (KOFF=0.09 → 4.5e-4/step), provided MLEN>3. On release the monomer is
  **teleported out of the capture window**: tail at
  r_head(new barbed) + (RCAP+0.25)·a, head at tail + R0·a. See "Negative
  results" for why this placement matters.
- At most one bind and one unbind per step.

**Integrator**: Langevin velocity-Verlet, Δt=0.005, kT=0.4, γ=2.0,
deterministic hash noise; FCAP=500; soft walls (XWALL=0.5, KWALL=100).
Box LBOX=12, N=60 monomers (120 beads): c0 = 57/1728 ≈ 0.033 after seeding.

## Final parameters

| param | value | | param | value |
|---|---|---|---|---|
| LBOX | 12.0 | | KFIL | 100 |
| DT | 0.005 | | PITCH | 0.6 |
| KT | 0.4 | | RCROSS | 0.1 |
| GAMMA | 2.0 | | σ (WCA) | 0.5 |
| FCAP | 500 | | RCAP | 1.4 |
| KBOND | 100 | | QMIN | 0.0 |
| R0 | 0.5 | | KON | 500 (saturated) |
| KSEED | 5.0 | | KOFF | 0.09 |
| N | 60 | | NSEED | 3 |

## Negative results (what the oracle ladder caught)

1. **Park-limited transport.** With ballistic Langevin dynamics at the
   original parameters (Δt=0.002, kT=0.2, RCAP=0.9, box 20), the on-rate was
   ~300× below the Smoluchowski estimate: window visits are long correlated
   *parks* (~1200 steps) and orientation randomizes on the same timescale, so
   each park yields a single effective orientation draw. Fix: Δt→0.005,
   kT→0.4, RCAP→1.4, QMIN→0.0, KON→saturated, box 12. On-rate responds to
   RCAP² and ballistic transit speed, not to the naive flux formula.

2. **Unbind catapult.** A freed monomer was left with its tail at RCROSS=0.1
   from the new barbed head; removing the bond exclusion put it inside the
   WCA core → FCAP-capped force ~5000 → catapult velocity ~25 → heating
   feedback (engine kT drifted 0.4→0.97, filament coiled against the walls,
   efil strain 26–72, overgrowth to len 45). Fix attempt 1 (teleport to
   0.65 along the axis, force-free) created a worse failure:

3. **Instant-rebind trap.** Parking the freed monomer at 0.65 — inside
   RCAP=1.4, perfectly aligned (q≈1) — made every unbind a no-op: rebind
   next step with P=1. The engine grew to len 49 with binds≈unbinds in the
   late phase. Final fix: release at RCAP+0.25=1.65 along the axis — outside
   the window, force-free, re-entry only by diffusion. This leaves a real,
   physical return-capture probability (see Results).

## Oracle ladder results

1. **FD** — analytic forces vs central differences (h=1e-6) on the cert
   config: max rel error **1.60e-9** (WCA + intra + ladder + anchor + walls).
2. **Static cert** — hexamer + 10 golden-spiral monomers + one close pair,
   positions by formula, no RNG: engine CFG/FRC rows vs mirror dump,
   max abs diff **4.35e-14**; CERT energies agree to ≤5.6e-16
   (ewca −1.85107530651567753, ebond 0.39646632068176374,
   efil 0.86365448163521352, eanch 0.00806176021410609, ewall 0).
3. **Rate calibration** (mirror):
   k_off_eff = **4.465e-4/step** (12 unbinds / 26876 eligible steps;
   nominal 4.5e-4 — eligible-step normalization matters, the filament sits
   at the MLEN=3 floor where unbind is blocked).
   k_on slope = **1.73e-2 /step/conc** (fixed-pool runs, unbind off:
   pools 20/40/60 → 1.75e-4 / 5.0e-4 / 5.75e-4 at c = 0.0116/0.0231/0.0347;
   noisy, ±30%).
   Mean-field prediction: c* = k_off/k_on_slope ≈ 0.0258,
   L* = N − c*·V ≈ **15.4** monomers, dL/dt = k_on·(N−L)/V − k_off.
4. **Phenomenon cert** — 150k-step dynamic runs, 3 seeds each side
   (seeds 77031 / 123457 / 888811), second-half mean length:

   | seed | engine lmean | mirror lmean |
   |---|---|---|
   | 77031 | 20.14 | 16.99 |
   | 123457 | 26.13 | 21.50 |
   | 888811 | 22.84 | 24.17 |
   | **mean** | **23.04 ± 1.43** | **20.89 ± 2.07** |

   Engine vs mirror agree within 1σ. Both plateau — no growth-to-exhaustion,
   no collapse-to-seed — with fluctuations of ±5 monomers, kT pinned at
   0.36–0.50 (nominal 0.4), modest fmax, no coiling (ee/contour ≈ 0.3 at
   plateau). An engine/mirror on-rate A/B with KOFF=0 (20–30k steps,
   3 seeds each) agreed within 1.3× (Poisson noise).

   The observed plateau (~21–23) sits above the naive ODE prediction (15.4)
   because the release-at-1.65 monomer retains a diffusive return-capture
   probability: the effective k_off in dynamic conditions is ~0.8× the
   nominal draw rate (engine plateau L≈23 → c≈0.021 → implied k_off_eff
   ≈ 3.5e-4/step). This is a model property, identical on both sides, not an
   implementation asymmetry; the ODE with nominal rates is a lower bound on
   L*.

## Files

- `actin_filament.ergo` — engine (dynamic run, MIRROR=0).
- `actin_cert.ergo` — static-cert variant (MIRROR=1): one force pass on the
  cert config, dumps CFG/FRC/CERT rows.
- `actin_mirror.py` — Python mirror/oracle (`--fd`, `--cert`, `--cal`,
  `--run [nsteps]`, `--full`).
- `actin_cert_config.txt`, `actin_cert_forces.txt` — mirror oracle dumps
  for the static cert.

Build & run: `python3 -m core actin_filament.ergo -o actin_bin && ./actin_bin`
(150k steps ≈ 1 min). Mirror: `python3 actin_mirror.py --full`
(Python mirror runs ~500× slower than the engine — calibrate/run in chunks).

## M4b+ hooks (not in M4a)

- Pointed-end kinetics (the NEXTM/PREVM lists already track both ends).
- ATP hydrolysis state per monomer (ADP/ATP cap → k_off depends on terminal
  nucleotide state) — the STATE array has room.
- Branching (Arp2/3): a third spring topology at a mother-filament side
  site; REBUILD_BONDS already handles arbitrary bond lists.
- Crosslinking: transient springs between nearby filament beads — reuse the
  cell list + candidacy idiom.
