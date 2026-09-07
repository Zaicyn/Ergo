# BRUSH RUNG (L1) — φ4 population × membrane = lamellipodium assay

Lock-step: oracle below is registered BEFORE the engine is built/run.
Parent engines: pop_fpt.ergo (φ4 certified population) + piston3_fpt.ergo
channels (SGATE gap-limited insertion, revert-on-block, ejection cooldown,
thermal piston DP=kT·PMU slot 800). No formin — the bare brush is the
Brownian-gating test; formin-brush is a later comparison arm.

## User decision
N_f target = 10 first (validate values before scaling higher).
Budget: N_tot = 125 (dwarf n̄≈9 + pool c≈0.02 → N_f* ≈ 10.7 predicted).
Static bumps: NMAX 60→125, NB→250, NBMAX→400, NSLOT→16000, MAXF 10→12,
literal (60)/(10) dims → (NMAX)/(MAXF). No chemistry changes.

## Engine surgery (brush_fpt.ergo)
1. Piston contact generalized: loop ALL active filaments, one-sided
   harmonic contact (KPST=100, margin XPMAR=0.5) on each barbed tip
   monomer's 2 beads; reactions sum to FRCT (load sharing by
   construction). Thermal piston unchanged (slot 800, PSTN=1 only).
2. SGATE/ejection/revert transplanted verbatim — already per-filament
   (inside the F loop). COOL semantics multi-filament: a cooled monomer
   clears when far from the tip currently being scanned (documented
   approximation; single-cool-flag per monomer).
3. New instrument: NENG — per-step count of active tips with head bead
   PX > XP − 1.0 (within 1σ of the plane); window mean on pstn line.
4. TFHIST (filament-1-only dwell histogram) dropped — superseded by
   per-event bbind/bblk (carry filament index F and register gap RGAP).

## Gates
- G-L1a: brush_fpt PSTN=0 NMAX=125 DIMERS=1 ≡ pop_fpt sed-bumped to
  NMAX=125 DIMERS=1 (bit-identical) — validates the transplant at the
  operating budget.
- G-L1b: brush_fpt PSTN=0 NMAX=60 DIMERS=1 SEED=77031 ≡ φ4 runs9
  pop_77031.full.log (bit-identical) — validates lineage at the
  certified budget.

## Pre-registered oracle (zero free params beyond certified inputs)
Certified inputs: φ4 dwarf state (n̄=8.77, c*=0.0166, conservation exact,
corner ν law); F1c bare-worm engagement ~10%; F0 tip statistics;
kT=0.4, δ=PITCH=0.6; runs7 j_on=5.58e-4, j_off=3.59e-4.

O1. Population: N_f* = (125 − c*·1728)/8.77 ≈ 10.7 ± 2; n̄ ≈ 9 ± 1;
    conservation c*V + N_f·n̄ = 125 exact; births = deaths stationary.
O2. Engagement: ⟨n_eng⟩ ≈ 2–4; P(bare brush) < 0.2; n_eng rises with
    F_ext (membrane seats onto the brush).
O3. Force–velocity (the rung's target): brush insertion rate suppressed
    as j_on(F) = j_on(0)·exp(−F·δ/(n_eng·kT)) — load shared over the
    engaged tips. With n_eng≈3: brush stall F_s ≈ n_eng·0.294·(ln ratio
    correction) ≈ 1–3 (arms cover 0–4). Block fraction rises with F and
    with 1/n_eng.
O4. Force balance ⟨FRCT⟩ = F_ext in stationary half (clamp occupancy
    small — XPLO=5.5 protective only).
O5. F=0 arm: free-membrane baseline — n_eng small, j_on ≈ bulk.
Falsification: j_on flat in F at full engagement (Brownian gating still
absent → something deeper wrong); or N_f* far outside 10.7±2 (φ4 law
fails to transport at 2× budget — would itself be a finding).
Arms: F_ext ∈ {0.0, 0.5, 1.0, 2.0, 4.0} × 8 seeds × 1M steps,
stationary half >500k. XP0=9.0, XPLO=5.5, XPHI=11.3, PMU=0.5.

## Analysis
Population (N_f*, n̄, c*, births/deaths); n_eng distribution per arm;
j_on(F) and brush v (piston drift + PITCH·Σnet barbed); per-event gap
spectra (bbind/bblk RGAP by filament); force balance audit; clamp
occupancy; F=4 crush documentation. Then BRUSH_LAW.md certification.


---

## AMENDMENT 1 (post-smoke falsification, registered before rebuild)

Smoke (brush_fpt v1, F=0.1, 300k, gates G-L1a/b PASSED 0-diff) falsified two
oracle items, and the failures are independent and instructive:

1. **O1 fails: the φ4 dwarf-state n̄ does NOT transport across budget.**
   Parent pop125 (PSTN=0, certified gate artifact): N_f* = 6.43 (median 6),
   n̄ = 15.4, c* = 0.0176 (stationary half). The pool concentration c* ≈ 0.017
   DID transport (predicted 0.0166), but n̄ rose 8.77 → 15.4: filament length
   is budget-dependent, so N_f* = (125 − c*V)/n̄ ≈ 6.4, not 10.7. This is the
   pre-registered "transport failure is itself a finding" clause: the φ4
   population law is sublinear in budget. O1's n̄=9±1 prediction is withdrawn;
   N_f targeting must be done by measured n̄ at the operating geometry.
2. **O2 fails on geometry, not on statistics.** Engine nucleation is emergent
   from the bulk monomer gas (dimer→trimer promotion, positions homogeneous,
   axes isotropic): only ~37% of monomers have a_x>0.5 and tips are diluted
   box-wide. Measured ⟨n_eng⟩ ≈ 0.5–1.4, P(bare) ≫ 0.2, piston escapes to
   the XPHI clamp at low load. The oracle assumed brush geometry (p≈0.2–0.3
   per filament); the engine implemented isotropic geometry. Oracle stands;
   the engine geometry is what must change.

### Geometry fix (biologically grounded)
Lamellipodial nucleation promotion factors (WASP/Arp2/3) are membrane-bound:
filaments are born AT the load surface with barbed ends toward it. Implement
as a **promotion gate** on the dimer→trimer promotion (the only birth
channel): promote only if the newborn barbed tip x > XNU_LO = 6.0 AND the
dimer axis a_x > ANUMIN = 0.0; otherwise recycle the cluster exactly like
the pre-certified slot-overflow path (no RNG draws in gate or recycle →
bit-structure preserved). Chemistry rates untouched (KNUC/KDIM/KTRI as φ4).
Dimer formation stays homogeneous (precursor, ndim ≪ 1). XPLO=5.5 < XNU_LO
so the clamp cannot sit on the birth slab.

### Amended oracle (registered before pop_slab measurement)
- O1′: at the brush geometry, N_f* and n̄ are MEASURED from pop_slab
  (PSTN=0) at N_tot=125, then the budget is retuned so N_f* = 10 ± 1.
  Conservation c*V + N_f·n̄ = N_tot exact; births = deaths stationary;
  c* ≥ 0.0166 (gating raises the pool — fewer births per attempt).
- O2 (unchanged numbers, now geometry-matched): ⟨n_eng⟩ ≈ 2–4,
  P(bare) < 0.2, n_eng rises with F_ext.
- O3, O4, O5 unchanged.
- Gates: G-L1a′: brush_slab PSTN=0 ≡ pop_slab at identical statics
  (bit-identical). G-L1b (runs9 lineage) was PASSED pre-amendment and is
  retired post-amendment by construction (nucleation geometry intentionally
  differs); the bit-chain is preserved through the new parent pop_slab.


## AMENDMENT 2 (budget-dial falsified; gate width is the N_f dial)

Budget probes (pop_slab, PSTN=0, 300k, seed 77031, stationary half):
  N_tot=125: N_f*=4-5,  n̄=19.5, c*=0.0174, ngate/(ngate+births)=116/149 (22% accept)
  N_tot=200: N_f*=7,    n̄=28.8, c*=0.0156
  N_tot=275: N_f*=7.5,  n̄=32.8, c*=0.0173
FINDING: c* is invariant (≈0.016-0.017) at every budget → dimer formation
rate is budget-invariant → birth rate is budget-invariant → N_f* SATURATES
(~8 asymptote); extra monomers inflate n̄ linearly (n̄ ≈ 0.13·N_tot). Worse,
n̄·PITCH reaches the box x-extent at N_tot≥200 (contour ≈17-20 vs LBOX=12):
filaments span wall-to-wall — a finite-size artifact, not a free brush.
The budget dial therefore CANNOT deliver N_f=10. It only sets n̄.

Dials that remain: promotion-gate width (activator-density analog — the
biologically legitimate knob) or KNUC (φ4 corner, frozen). Choose gate width.

Amended operating point (registered before probe):
  XNU_LO 6.0 → 2.0 (slab = 76% of box x-extent), ANUMIN = 0.0 unchanged
  (hemisphere orientation is the non-negotiable membrane abstraction).
  N_tot 275 → 150 → predicted n̄ ≈ 11-12 (brush fits the box) and
  acceptance ≈ 35% → N_f* ≈ 8-11. If N_f* < 9: iterate ANUMIN → −0.3.
  Falsification: N_f* still ≪ 9 at acceptance ≈ 35% → birth-limitation
  model wrong; diagnose dimer pool dynamics directly.


## AMENDMENT 3 (N_f ≈ births × lifetime; lifetime is the second dial)

Gate-width probes at N_tot=150 (300k, seed 77031, stationary half):
  XNU_LO=2.0, ANUMIN= 0.0: accept 43%, births 2.2e-4/step, N_f*=7.8, n̄=15.8
  XNU_LO=2.0, ANUMIN=-0.3: accept 56%, births 2.5e-4/step, N_f*=7.5, n̄=16.5
FINDING: births respond to gate width as predicted, but N_f does NOT —
lifetime anti-responds (35k→30k steps): newborn competition shortens lives.
Cross-condition lifetimes: 41k @N_tot=125 (n̄=19.5), 70k @200 (n̄=29),
35k @150 (n̄=16). Lifetime scales with n̄ (death = pointed-end grind-down
from length n̄ → longer filaments live longer). So N_f* ≈ births × f(n̄),
and n̄ = (N_tot − c*V)/N_f — the two dials act through ONE equation.

Solved forward (registered before probe): N_tot=175, XNU_LO=2.0,
ANUMIN=-0.3 → births ≈ 2.4e-4/step, n̄ ≈ 14 (fits box: contour 8.4 < 12),
lifetime ≈ 45k → N_f* ≈ 10-11. Accept window N_f* ∈ [9, 11] (user target
10, floor 8). If overshoot > 11: N_tot → 165. If undershoot < 9:
N_tot → 190 (n̄ ≈ 16 still fits).


## AMENDMENT 4 (the PSTN=0 parent is not the assay; baseline moves to the F=0 piston arm)

1M-step stationarity runs (both log tails intact; heads lost to a sparse-write
artifact under nohup on /mnt — tail census blocks complete and consistent):
  pop125 (isotropic parent):   N_f ≈ 6-7, n̄ ≈ 14, c ≈ 0.019 — STABLE at 1M.
  pop_slab175 (gated parent):  N_f 8.6@300k → 4.6@1M — COLLAPSES.
Mechanism (fil/fdeath forensics): a filament born at t≈94 (initial gas,
pre-gate) grew to len 107 (contour 64 ≫ LBOX=12 — a folded wall-wadded
tangle), sequestering 61% of the monomer budget; newborns churn with
lifetimes 52-6000 steps, maxn 3-9. In the gated geometry every filament is
born pointing +x toward the +x wall; with no membrane (PSTN=0) nothing caps
elongation at the wall, so the first filament to reach the wall grows
without bound (gambler's-ruin capital makes it immortal). The isotropic
parent escapes because only ~1/6 of filaments head +x and rotational
wander kills them before wall capture.

Diagnosis: the runaway is an artifact of running the SLAB GEOMETRY WITHOUT
THE PISTON. The actual assay always has the membrane: SGATE arrests tips at
XP−XPMAR, pointed-end grind then shortens and kills filaments normally —
the brush self-limits its length to the birth-slab→plane depth. The
PSTN=0 "baseline" I set out to measure is the one configuration that is
physically meaningless in this geometry.

Amended measurement plan (registered before brush_slab probe):
- O1″ baseline = the F_ext=0 arm of brush_slab itself (membrane present,
  no load). Predict: n̄ self-limits to ≈ brush depth / PITCH ≈ 8-12;
  N_f* ≈ (175 − c*V)/n̄ ≈ 10-14; NFILH overflow watch (MAXF=14);
  stationary at 1M (no len>40 filaments, no ancient births dominating).
- pop_slab175 retains ONE duty only: G-L1a′ bit-gate partner (300k,
  code-identity check — stationarity irrelevant for gates).
- If F=0 arm gives N_f* > 12: budget → 150. If N_f* < 9: budget → 200.
