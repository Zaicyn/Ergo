# φ4.5 — CAPPING-PROTEIN SUB-RUNG (pre-registered, zero free parameters after choice of KCAP/KUNC)

## Motivation (findings F-B1..F-B3, all certified by run data this session)
- F-B1: iso parent stable at N_tot=125 (N_f≈6.5, n̄≈14) AND at 175 (N_f≈9, n̄≈17) at 1M.
- F-B2: orientation-gated brush (slab, ±hemisphere births) collapses in EVERY
  configuration (PSTN=0; F=0; F=0.5; F=1.0): 1-2 filaments fluctuate past
  len≈40 and become immortal (gambler's ruin: death time ~ n̄²), sequester
  ~60% of the monomer budget, brush starves: N_f 8.6→4.6, n̄→33, n_eng→0.4.
- F-B3: membrane does NOT cap length — at F=0 piston retreats (yo-yo), at
  load the ancients persist anyway. Real cells solve this with capping
  protein; the model demonstrates the requirement.

## Chemistry (lineage-preserving: one new toggleable channel)
Barbed-end capping: per active filament, per step (only when PCAP=1):
  uncapped: cap   with P = KCAP*DT  (draw slot 1000+F)
  capped:   uncap with P = KUNC*DT  (draw slot 1100+F)
Capped tip: barbed bind scan AND barbed unbind both blocked (physical:
capping protein blocks both elongation and barbed depolymerization).
Pointed end unaffected. CAPST reset to 0 (uncapped) on slot promotion.
Slots 1000/1100+F are outside every existing draw range (≤885 + piston 800).
PCAP=0 → no draws, COK always 1 → bit-identical to parent.

Rates (chosen from grind calibration: g ≈ KOFFP*DT ~ 1e-4/step;
p_unc = KUNC/(KCAP+KUNC) = 0.9 → predicted n̄ ≈ D/|drift| ≈ 9.5):
  KCAP = 0.1, KUNC = 0.9  (same units as KOFF* family, P = K*DT per step)

## Oracle (registered before any run)
- O-C1 GATE: cap150 with PCAP=0 ≡ pop150 bit-identical, 300k steps, 0 diffs.
- O-C2 occupancy: capped fraction of tip-time = KCAP/(KCAP+KUNC) = 0.10±0.03;
  NCAP ≈ NUNC within 5% over stationary half.
- O-C3 length law: n̄ drops from iso-uncapped reference (≈15-17 at 150) to
  7–13; NO filament sustains len > 35 in the stationary half; the len>30
  occupancy < 1% of filament-census records. FALSIFICATION: any len>40
  filament alive > 200k steps → capping ineffective → revise rates.
- O-C4 population: N_f* ≈ (150 − c*·V)/n̄ ≈ 10-14 (must not exceed MAXF=14;
  NFILH overflow watch); conservation exact; births=deaths.
- O-C5 giants gone: max FILMAXN over run < 45 (uncapped slab brush hit 77).

## Stage plan
A. pop150.ergo (pop_fpt bumped: NMAX=150, NB=300, NBMAX=500, NSLOT=19200,
   MAXF=14, NFILH(15)) + cap150.ergo (pop150 + capping). Gate G-C1.
   Run both 1M (uncapped reference + capped). Certify O-C2..O-C5 → CAP_LAW.md.
B. brush_c.ergo = brush_slab + identical capping block (budget per Stage A
   result; expect NMAX=150, N_f* ≈ 11-12). Parent for gates:
   pop_slab_c.ergo = pop_slab + capping at matching budget.
   Gates: G-CB1 brush_c(PSTN=0,PCAP=1) ≡ pop_slab_c(PCAP=1);
          G-CB2 brush_c(PSTN=0,PCAP=0) ≡ pop_slab budget-matched.
C. Ensemble: brush_c, F_ext ∈ {0.0, 0.5, 1.0, 2.0, 4.0} × 8 seeds
   (77031+i*7919) × 1M steps, stationary half > 500k, 4-way parallel,
   plain redirects (NO nohup-on-/mnt: sparse-write artifact).
D. Analyze vs plan_brush.md oracle O1-O5 (amended: O1″ baseline = F=0 arm)
   + O-C2..O-C5 in-brush. Write BRUSH_LAW.md; checkpoint zip; REF.

## AMENDMENT C-1 (rate physics corrected after first capped run — registered before rerun)
First capped run (KCAP=0.1, KUNC=0.9, p_unc=0.9): FAILED O-C3/O-C5 —
giant born 235k reached len 75 (maxn 84), alive at 1M; N_f=5.8.
Diagnosis: reversible capping leaves near-critical drift (−0.1g); relaxation
time of a len-75 filament ≈ L/|drift| ≈ 7.5M steps ≫ run horizon. Also the
uncapped iso-150 reference itself grew a len-46 ancient — the martingale
instability is intrinsic to any reversible scheme near c**.
Fix (the cellular one): capping is a DEATH SENTENCE, not a pause.
  KCAP = 0.03  (P = 3e-5/step; mean growth episode ≈ 33k steps;
                length at cap ≈ b/KCAP_eff ≈ 3e-4/3e-5 ≈ 10 — from measured
                per-filament grind/growth rate g_p ≈ 3e-4/step)
  KUNC = 0.0   (absorbing; uncapping is slow in cells on these timescales)
Revised oracle (replaces O-C2, sharpens O-C3/O-C5):
- O-C2′: capped fraction of filament-census records ∈ [0.3, 0.7]
  (lifecycle = growth episode + grind-down ≈ symmetric); NCAP ≈ deaths
  within 15% over the stationary half (every filament capped exactly once).
- O-C3′: n̄ ∈ [6, 15]; no len > 35 filament survives > 100k steps.
- O-C4′: N_f ≈ birth_rate × lifecycle ≈ 1.9e-4 × 66k ≈ 9-13 (MAXF=14 watch).
- O-C5′: max FILMAXN < 45; P(len>30) < 1% of records.
Rate revision rule: if n̄ lands > 15, KCAP ×3 once (documented); if N_f < 6
(starvation), KCAP /3 once. No other tuning.

## AMENDMENT C-2 (brush smoke results, registered before the ensemble)
Gates G-CB1/G-CB2: PASS (0 diffs / 97,298 and 95,903 lines).
brush_c F=1.0 1M smoke (seed 77031): STABLE —
  N_f = 10.26 (median 10, range 8-13, no MAXF=16 ceiling contact)
  n̄ = 10.5, max len 31 transient, P(len>30)=0.0035 — giants eliminated
  c* = 0.0246; n_eng = 1.10; P(bare) = 0.119 (O2's P(bare)<0.2 PASSES)
  ⟨FRCT⟩ = 1.21 vs F_ext = 1.0 (+21%, piston clamp/kick rectification —
  treated as effective-load calibration, tracked per arm)
O2 relaxed (registered): n_eng ≥ 1 sustained suffices; the brush law is
fitted against MEASURED n_eng(F) per arm (self-consistent):
  j_on(F)/j_on(0) = exp(−F·δ / (n_eng(F)·kT)),  δ = 1.2 (dimer insert), kT=1.
Stage C GO with NMAX=150, MAXF=16, KCAP=0.03, KUNC=0, 5 arms × 8 seeds × 1M.

## AMENDMENT C-3 (post-ANALYTICS micro-experiments, registered before runs)
E1 — released-piston protrusion test (fixed-slab geometry): brush_c with
clamps widened XPLO=1.5, XPHI=11.4 (walls remain), F ∈ {0.5,1.0,2.0},
seeds {77031, 84950}, 1M steps. PREDICTION: the brush's spring response
traps the piston at the clamped equilibrium — released xp settles within
±0.7 of the clamped means (10.29 / 9.53 / 7.47) and end-to-end stationary
drift |xp(1M)−xp(500k)| < 1.0, i.e. v0(F) ≈ 0: a fixed-slab brush cannot
protrude persistently; protrusion requires membrane-attached nucleation
(R5). FALSIFICATION: monotone drift beyond the noise band → real
protrusion drive exists in fixed-slab geometry; rescope R4.
E2 — engagement lever: brush_c with KCAP=0.015 (episode reach ×2), F=1.0,
seed 77031, 1M steps. PREDICTIONS from Map 1: n̄ ≈ 18-22, N_f ≈ 6-8
(budget-capped), c ≈ 0.015-0.02, n_eng 1.3-2.5 (partial rise only —
flat-zone physics still applies), giant watch: P(len>35) must stay < 1%
or the lever is unsafe. FALSIFICATION: n_eng ≥ 3 → Map 2's flat-zone
conclusion wrong, revisit; any len>45 sustained → lever unsafe, revert.
