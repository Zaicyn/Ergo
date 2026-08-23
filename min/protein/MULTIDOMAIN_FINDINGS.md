# Multi-Domain Folding — Findings and Open Issues

**Date:** 2026-08-22
**Scope:** Resumption of the protein campaign after the 2026-07-20 scaling
study. Goal: push past the 120–180 residue ceiling toward genuine
multi-domain targets. First experiment: fold-then-dock contact staging on
T4 lysozyme (2LZM, 164 res). Result: **negative** — and informative.

---

## 1. Where the campaign stood

From `SCALING.md` / `TRANSFERABILITY.md` (2026-07-20):

- Recipe: native angle/torsion targets + Go contacts (6.5 Å, NATIVE_K=1.0)
  + hydrophobic collapse (0.002) + late register torsions (frame 1200,
  REG_K=0.5) + quench tail at 0.8·MAXFRAME, **HB_CAP=0** (dynamic H-bonds
  disabled — they over-stabilize wrong collapse in β proteins).
- Scaling: chignolin 10 → 0.012 Å, Trp-cage 20 → 0.79 Å, BBA5 23 → 0.74 Å,
  WW 34 → 2.10 Å, GB1 56 → 0.24–1.25 Å, SNase 136 → 2.36 Å (3/5 seeds).
- SNase failure geometry: N-terminus (res 1, ~18 Å) and domain interface
  (res 73–81); 2/5 seeds trapped in wrong basins. Domain cores <1 Å.

Standing traps (do not re-step):

1. Never activate a new restraint from frame 0 (register-torsion lesson).
2. Do not re-enable dynamic H-bonds naively.
3. Native dihedral targets are necessary; generic SS targets hurt.
4. One seed proves nothing — 5-seed sweeps are the methodology.
5. Distinguish convergence-rate limits from representation limits before
   changing the model (BBA5 was pure runtime).

**Correction recorded 2026-08-22:** with HB_CAP=0 the Kuramoto phase field
touches no force term (it only gated H-bond formation). Proposals based on
"per-domain phase fields" are inert in the flagship recipe. The phase field
is currently decorative.

---

## 2. What was built (2026-08-22)

### 2.1 Fold-then-dock staging (`--domains`, `--dock-from`)

- `generate_protein_ergo.py`: `--domains "1-98,99-136"` (or JSON from
  `detect_domains.py`) classifies every Go contact as intra/inter-domain;
  `--dock-from N` sets the activation frame (default 0.5·MAXFRAME when
  domains given; hard error without `--domains`).
- `waveform_template.ergo`: new `CONTACT_INTER(N,N)` matrix + `DOCK_FROM`
  parameter (default 2e9 = off). Inter-domain contacts exert no force and
  contribute no `e_native` until `FRAME > DOCK_FROM`. Gate is inert when
  domains are omitted → single-domain behavior unchanged.
- `analyze_margin.py`: `--domains` adds per-domain Kabsch RMSD (each domain
  aligned independently) + interface-region deviation summary.
- **Pairing rule:** new generator requires the new template (it always
  initializes `CONTACT_INTER`).

Certification at build time:

- Generator regression vs old generator+template: identical except the one
  `CONTACT_INTER` zero line (hence the pairing rule).
- Gate verified live: `e_native` flat until frame 48000, spike to ~551 at
  activation (6 interface contacts far from native distance), relaxed by
  96k. Engages exactly on schedule.
- Analyzer verified on a synthetic wrong-docking case (D2 rotated 90° +
  translated): global 2.59 Å, per-domain 0.000/0.000 — cleanly separates
  misfolding from mis-docking.
- Dialect balance on generated variant: 51/51 DO, 43/43 block IF, no
  single-line IF.

### 2.2 Target selection (detector survey, 2026-08-22)

`detect_domains.py` run on candidates pulled from RCSB:

| Target | Res | Domains @ default | Go contacts crossing boundary | Role |
|---|---|---|---|---|
| 1SNO | 136 | 1 (won't split) | 25/197 (13%) | Lobed, not cleanly two-domain; use known 98/99 boundary manually |
| 2LZM | 164 | 2 (cut at 70/71) | 6/173 (3%) | **Cleanest two-domain test** |
| 4I1H | 306 | 4 (87/179/246) | 45/364 (12%) | The >180 multi-domain prize |
| 5N2W | 382 | 5 | — | Too big for now |
| 3IFW | 223 | 1 (never splits) | — | Negative control (monolith) |

SNase detector note: no contradiction with SCALING.md — SNase's lobes are
contact-dense across 98/99, so the min-cut correctly refuses at threshold
0.12. It is a weak two-domain case; 2LZM is the strong one.

---

## 3. The T4L experiment (2LZM, 164 res, boundary 70/71)

Design: 5 seeds × {staged (`--dock-from 48000` of 96000) vs baseline},
otherwise the GB1/SNase recipe verbatim (`--hb-cap 0 --tors-k 0.2
--maxframe 96000 --quench-frame 76800`).

### Results (SVD-Kabsch on FINAL_STRUCTURE, Å)

| seed | base global | dock global | base D1 / D2 | dock D1 / D2 |
|---|---|---|---|---|
| 0.0 | 4.27 | 5.46 | 2.25 / 2.36 | 2.38 / 2.63 |
| 1.0 | 5.59 | 5.49 | 2.73 / 3.36 | 3.08 / 3.94 |
| 2.0 | 4.40 | 4.42 | 1.95 / 2.95 | 2.23 / 2.84 |
| 3.0 | 5.46 | 6.37 | 2.43 / 4.28 | 2.79 / 4.62 |
| 4.0 | 4.25 | 4.77 | 1.53 / 3.70 | 1.72 / 3.63 |

Mean global: baseline 4.79, staged 5.30. Staging never helped; the gate
provably engaged (§2.1). **Negative result.**

### Interpretation

The SNase assumption — "domains fold fine, docking fails" — is **false for
T4L**. Per-domain RMSDs are 1.5–4.6 Å: the domains themselves are only
roughly folded. Interface staging cannot help a protein whose domains
haven't folded; with a 3% interface, gating six weak contacts mostly
removed a small guiding signal during collapse — hence the slight harm.

The ceiling at 164 is therefore **single-domain folding quality degrading
with size/helix content**, not domain docking. D2 (94 res) is consistently
worse than D1 (70 res).

Prime suspect: **TORSK = 0.2 is the β-protein setting** (WW/BBA5/GB1/SNase
are all sheet-containing). T4L is strongly α-rich; the only prior helical
target (Trp-cage) used **TORSK = 0.6**.

---

## 4. Open issues

1. **Engine-internal `rmsd_native` is unreliable on staged runs.** For dock
   runs it disagrees with the final-structure Kabsch (dock_0.0: 11.62 vs
   5.46 Å); baseline runs match exactly. The in-engine quaternion Kabsch
   can land in a wrong-rotation local minimum. `analyze_margin.py`'s SVD
   Kabsch on FINAL_STRUCTURE is authoritative; treat the CSV column as
   suspect until the solver is fixed. — *engine bug list*
2. **N-terminus / termini flexibility** (carried from SCALING.md; SNase
   res 1 ~18 Å).
3. **Per-domain RMSD reporting now exists** — use it on every multi-domain
   run, baseline included.
4. **2LZM boundary is detector-native (70/71)**; do not confuse with CATH's
   non-contiguous T4L assignment — our gate needs contiguous segments.
5. DeepSeek-style "phase transition at 120–180 residues" explanations are
   **not supported** by any of our data: SNase domain cores fold to <1 Å,
   and T4L fails by under-folding, not by decoherence. The ceiling is
   mechanical (force mix, schedule, size), not a change in the physics.

## 5. Next experiments (in order)

1. **T4L TORSK sweep**: baseline (no `--domains`), 5 seeds,
   `--tors-k 0.6`. If per-domain RMSDs collapse toward <1.5 Å, T4L was a
   force-mix problem. If not, try TORSK 0.4 and/or longer MAXFRAME.
2. **Re-test `--dock-from` only on top of the corrected recipe**, when
   domains actually fold — staging can only dock what exists.
3. **3IFW negative control** (223-res monolith, `--domains` omitted):
   probes the size ceiling without the domain confound and guards against
   template regressions.
4. **4I1H (4 domains, 306 res)** only after 1–2 are understood.
5. Fix the in-engine RMSD solver (issue 1) before any long-trajectory
   diagnostics work.

## 6. Reproduce

```bash
export PYTHONPATH=$HOME/Ergo          # makes `python3 -m core` work anywhere
cd ~/Ergo/min/protein

python3 extract_pdb_ca.py ../../pdb/2LZM.pdb -o 2lzm.json
python3 detect_domains.py --json 2lzm.json     # expect D1: 1-70, D2: 71-164

# staged
python3 generate_protein_ergo.py --name t4l_dock --json 2lzm.json \
  --pdb ../../pdb/2LZM.pdb --chain A --output waveform_t4l_dock_0.0.ergo \
  --hb-cap 0 --tors-k 0.2 --maxframe 96000 --quench-frame 76800 \
  --domains "1-70,71-164" --dock-from 48000 --seed 0.0
python3 -m core waveform_t4l_dock_0.0.ergo -o waveform_t4l_dock_0.0
./waveform_t4l_dock_0.0 > waveform_t4l_dock_0.0.out 2>&1
python3 analyze_margin.py waveform_t4l_dock_0.0.out --domains "1-70,71-164"

# baseline: same without --domains/--dock-from (keep --domains on the
# analyze_margin call so per-domain RMSD is reported for both)
```

Files (updated copies, this session): `generate_protein_ergo.py`,
`waveform_template.ergo.txt` (rename to `waveform_template.ergo`),
`analyze_margin.py`. Runs: `waveform_t4l_{dock,base}_{0.0..4.0}.out`.

---

## 7. TORSK sweep result (2026-08-22, second T4L experiment)

Same 2LZM setup, baseline (no staging), `--tors-k 0.6` (the α-protein
setting), 5 seeds, 96k frames:

| seed | tk02 global | tk06 global | tk06 D1 | tk06 D2 |
|---|---|---|---|---|
| 0.0 | 4.27 | 3.98 | 1.73 | 2.09 |
| 1.0 | 5.59 | 5.58 | 3.02 | 4.29 |
| 2.0 | 4.40 | 4.55 | 2.88 | 2.80 |
| 3.0 | 5.46 | 6.01 | 3.84 | 4.81 |
| 4.0 | 4.25 | 5.03 | 4.39 | 3.75 |

Mean global: tk02 4.79 → tk06 5.03. **TORSK force-mix hypothesis rejected**;
domains remain under-folded (1.7–4.8 Å).

Trajectory analysis (internal `rmsd_native` column, shape only — see issue
below): descending seeds are still descending at 96k (tk06_0.0: 4.34 → 3.98
over the last 24k frames) → **convergence-rate limited**, BBA5-style.
Trapped seeds plateau hard (tk06_3.0: ~9.4–9.8 flat from 48k on).

**Instrument issue update (supersedes §4.1 framing):** the in-engine
`rmsd_native` divergence is NOT specific to staged runs. tk06_3.0 reports
9.78 internally while the FINAL_STRUCTURE SVD-Kabsch gives 6.01; runs near
the native basin (tk06_0.0, all tk02 baselines) match exactly. Pattern:
the quaternion RMSD solver fails when the structure is far from native —
i.e., it over-reports RMSD precisely for trapped seeds. Absolute values
off-basin are untrustworthy; FINAL_STRUCTURE Kabsch remains authoritative.

**Revised diagnosis for the 164-residue ceiling:** part convergence-rate
(fixable with frames), part seed trapping (fixable with sweeps), with the
thermal schedule as the prime structural suspect — the five heat/cool
cycles are hard-coded into frames 0–1200 regardless of MAXFRAME, so a 96k
run spends ~1% of its time annealing and 99% in cold descent. What worked
at 4k–24k frames may simply not scale.

**Next:** (a) MAXFRAME 192k on seeds 0.0/4.0 to confirm convergence-rate;
(b) scale the thermal schedule with MAXFRAME (cycles proportional to
runtime, not fixed at 1200); (c) engine RMSD solver fix.

---

## 8. Scaled-schedule result (2026-08-22, third T4L experiment)

New template parameter `SCHEDULE_SCALED` (default 0 = legacy): thermal
cycles span the first half of MAXFRAME instead of frames 0–1200
(`--scaled-schedule`). At 96k: peaks at 12000/36000, cold from 48000,
quench 76800. Schedule shape certified in-sandbox and confirmed live in
the runs' thermal column. (First cut had an off-by-2 — QTR=HALF/2 gives
one cycle, not two; fixed to QTR=HALF/4 before delivery.)

T4L, tk06, seeds 0.0/3.0/4.0, scaled schedule vs unscaled:

| seed | tk06 global | tk06s global | tk06s D1 / D2 |
|---|---|---|---|
| 0.0 | 3.98 | 4.36 | 1.93 / 1.08 |
| 3.0 | 6.01 | 6.28 | 2.87 / 4.37 |
| 4.0 | 5.03 | 4.52 | 1.76 / 3.59 |

**Schedule hypothesis rejected.** The trapped seed stays trapped (3.0:
6.28); no seed improved meaningfully. Annealing time is not the binding
constraint; trapping is initial-condition/landscape, not schedule.

**T4L at 164, three levers down:** interface staging (worse), TORSK 0.2→0.6
(wash), scaled annealing (wash). Remaining levers: raw MAXFRAME (descending
seeds are still descending at 96k — the convergence-rate component is
real), seed sweeps, or accept a representation limit for α-rich proteins
at this size. Per-domain note: tk06s_0.0 folded D2 to **1.08 Å** — the
best T4L domain fold yet, from the hot-phase-extended run.

Instrument issue reconfirmed: tk06s_3.0 internal rmsd_native 13.6 vs SVD
6.28 — internal solver over-reports on trapped seeds, as diagnosed in §7.

**Next:** MAXFRAME 192k on seeds 0.0/4.0 (scaled schedule) — the last
cheap lever before calling a representation limit.

---

## 9. The 192k pair — closing the T4L line (2026-08-22)

tk06 + scaled schedule, MAXFRAME=192000, quench 153600, seeds 0.0/4.0:

| seed | tk06 @96k | tk06s @96k | 192k global | 192k D1 / D2 | internal traj 96k→144k→192k |
|---|---|---|---|---|---|
| 0.0 | 3.98 | 4.36 | **3.19** | 1.47 / 2.26 | 4.61 → 3.81 → 3.19 (still falling) |
| 4.0 | 5.03 | 4.52 | 4.96 | 2.13 / 3.57 | 5.18 → 6.15 → 8.20 (wandering off) |

**Split outcome.** Seed 0.0: convergence-rate component is real (192k
bought 1.2 Å, not yet flattened). Seed 4.0: drifted backwards after 96k —
runtime cannot fix basin selection. Instrument bug seen again (4.0:
8.20 internal vs 4.96 SVD).

**Campaign synthesis (T4L, 164 res):** four levers tested — interface
staging (worse), TORSK 0.2→0.6 (wash), scaled annealing (wash), doubled
runtime (helps only seeds already in the right catchment). The binding
constraint at this size is **basin selection**, i.e. initial-condition
luck. Practical ceiling for single-trajectory folding of α-rich proteins:
~140–160 residues (SNase and T4L both on the boundary).

**Recommended pivots (in order):**
1. Seed-selection driver: K short runs (16 × 24k), rank by e_native,
   continue the best — attacks the documented failure mode directly.
2. Fix the in-engine quaternion RMSD solver (4 run families of evidence).
3. Keep --domains/--dock-from + per-domain RMSD in the toolbox for targets
   where docking genuinely is the failure mode (SNase interface, res 73–81).
4. Optional: one 384k run on seed 0.0 to measure the asymptote.

**Status: T4L experiment line closed** unless otherwise directed.

---

## 10. RMSD solver fixed — power iteration was the bug (2026-08-22)

**Root cause confirmed.** `COMPUTE_RMSD` used power iteration for the top
eigenpair of the 4×4 quaternion matrix, from the fixed start vector
(1,0,0,0), 40 iterations. Off-basin structures have top eigenvectors
near-orthogonal to that start (or near-degenerate top eigenvalues), so
power iteration converged to the wrong rotation — over-reporting RMSD
exactly on trapped/relaxed-off-basin runs. Replicating the old algorithm
in the sandbox reproduces every historical internal `rmsd_native` value
to 3 decimals (e.g. dock_0.0: 11.622 = engine's 11.62).

**Fix:** the campaign-certified cyclic Jacobi eigensolver
(viviani_4d_ed / h2_wig / h4_wig CI block) now replaces power iteration
in `waveform_template.ergo`'s `COMPUTE_RMSD`. Certified against all 18
T4L FINAL_STRUCTURE blocks: **Jacobi = SVD-Kabsch to 3 decimals on every
run**, including all eight known divergence cases. Dynamics untouched
(diagnostics only); dialect balanced (63/63 DO, 48/48 IF). One robustness
guard added beyond the h2_wig original: `OFF := SQRT(MAX(OFF, 0.0))` —
the sum-of-squares minus diagonal-squares form can round negative at
convergence (observed as a sqrt warning in the Python mirror). NOTE: the
same unguarded pattern exists in the h2_wig/h4_wig CI Jacobi — worth
adding the MAX guard there too.

**Retroactive implication (important):** every historical verdict based
on the internal `rmsd_native` column is suspect off-basin. That includes
the SNase seed sweep in SCALING.md (seed 3.0 "10.14 stuck", seed 4.0
"4.77") and BBA5 seed 0.0 "4.30" — those were power-iteration numbers
and are upper bounds inflated by an unknown amount. Their FINAL_STRUCTURE
blocks should be re-measured with SVD (`analyze_margin.py`) before the
"seed trapping" narrative is trusted quantitatively. The qualitative
picture (some seeds worse than others) certainly survives, but the
numbers — and possibly the basin classifications — need re-measurement.

**Methodology going forward:** the internal rmsd column is now trustworthy
in newly generated variants; for all archived runs, FINAL_STRUCTURE + SVD
is the only authoritative RMSD.


---

## 11. 3IFW negative control (2026-08-22, fourth T4L-era experiment)

Purpose: isolate domain architecture from raw chain length. 3IFW = 223-res
single-domain monolith (detector: 1 domain at all thresholds). If our ceiling
is basin selection on one big domain, 3IFW must fail; if it folded well, the
size-ceiling narrative would be wrong and 4I1H (306 res, 4 domains) would be
uninterpretable.

Setup: identical to the T4L tk06 96k baseline — hb-cap 0, tors-k 0.6,
maxframe 96000, quench 76800, legacy thermal schedule, Jacobi RMSD solver,
seeds 0.0-4.0.

Results (final frame, internal = SVD-verified on all seeds):

| seed | 3IFW RMSD | T4L tk06 RMSD |
|---|---|---|
| 0.0 | 8.16 | 3.98 |
| 1.0 | 8.31 | 5.58 |
| 2.0 | 8.28 | 4.55 |
| 3.0 | 10.67 | 6.01 |
| 4.0 | 6.51 | 5.03 |
| mean | **8.38** | **5.03** |

- Every 3IFW seed is worse than every T4L seed. Best 3IFW (6.51) > worst T4L (6.01).
- Chains collapse fine: final rgyr 7.2-7.7 vs native 6.53 (except seed 3.0,
  bloated at 10.74). Failure is basin selection, not collapse.
- Trajectories nearly flat after 24k (e.g. 0.0: 8.56 → 8.16) — settled into
  wrong basins early and never left; quench rescued nothing.

**Control passes: the ceiling is real and architecture-independent at this
recipe.** A 223-res monolith fails exactly as the basin-selection model
predicts. A 4I1H success at 306 res would therefore be meaningful evidence
for fold-then-dock; a 3IFW-style failure for 4I1H would refute it cleanly.


---

## 12. 4I1H fold-then-dock test (2026-08-22, fifth experiment)

306 res, 4 domains (D1 1-87, D2 88-179, D3 180-246, D4 247-306; detector
boundaries). Recipe: hb-cap 0, tors-k 0.6, 96k, quench 76800, legacy schedule,
Jacobi solver. Staged (dock-from 48000) vs baseline, 5 seeds each.
3IFW (223-res monolith, §11) is the size control.

Final global RMSD (internal = SVD on all ten):

| seed | dock | base |
|---|---|---|
| 0.0 | **5.86** | 5.64 |
| 1.0 | 9.83 | **878.4 (exploded)** |
| 2.0 | 8.93 | 9.02 |
| 3.0 | 8.89 | 9.19 |
| 4.0 | 7.89 | **39.7 (exploded)** |
| mean | 8.28 | 188 (survivors: 7.95) |

Findings:

1. **Baseline explodes at 306 res — staging prevents it.** 2/5 base seeds
   blew up within the first 1000 frames (e_native ~1.2e5, rgyr frozen at
   ~880 = shredded chain). Mechanism: long-range inter-domain Go contacts
   active during the violent early collapse produce huge cross-chain forces;
   at 164 res this was survivable, at 306 it is not. Dock variants (interface
   off until 48k) never exploded. NEW TRAP: at >300 res, always-on native
   contacts are a stability hazard; staging is the fix.
2. **The gate does real work at 48k.** Every dock seed improved sharply at
   gate-on: 0.0: 8.4→5.9; 1.0: 17.8→9.8; 4.0: 12.0→7.9. e_native spikes
   (6e3-3e4) then relaxes within ~20k frames. Interface activation actively
   re-docks partially folded domains — opposite of T4L, where it was mildly
   harmful.
3. **Architecture beats length.** Same seed, same recipe: 4I1H dock 0.0 =
   5.86 A at 306 res vs 3IFW 0.0 = 8.16 A at 223 res. The larger multi-domain
   protein folds *better* than the smaller monolith. With the 3IFW control in
   place, this is positive evidence for the fold-then-dock thesis.
4. **Domain-internal folding still partial.** Best-seed per-domain RMSDs
   (dock 0.0): D1 4.98, D2 2.46, D3 4.93, D4 3.11 — domains are recognizable
   but not at isolated-domain quality (60-92 res alone folds to ~1.5-3 A).
   Domain basin selection inside a long chain remains a binding constraint.
5. Among non-exploded seeds base (7.95) edges dock (8.28) — staging's mild
   drag on good catchments persists (T4L signature), but 0/5 vs 2/5
   explosions dominates any mean-based comparison.


---

## 12a. UNITS ERRATUM (2026-08-22)

All RMSD values reported in this document (and quoted verbally this
session) are **engine model units**, not Angstroms. The generator rescales
native coordinates to mean Ca-Ca = 1.52; verified scale: **1 model unit =
2.5 A** (4I1H engine-native Ca-Ca = 1.52 vs 3.80 A raw). Corrected
headline numbers: T4L 192k seed 0.0 = 3.19 u = 8.0 A; 4I1H dock 0.0 =
5.86 u = 14.7 A; 3IFW mean = 8.38 u = 21 A. All comparisons, ratios, and
conclusions are unit-invariant and stand unchanged.

## 13. Ultrasonic pulse port (2026-08-22)

Historical results (heatpulse_check.md, sdrd_check.md): mode-1 backbone
standing-wave velocity kick `V += A*sin(w*FRAME)*sin(pi*I/(N+1))`, axes
phase-shifted 2pi/3, applied every frame after thermal impulses, before
sterics. 1SNO: w=0.002/A=0.05 rescued the seed-3.0 domain trap (9.66 ->
3.40 full) where sustained heat at 20x floor did nothing; frequency
dependence at fixed amplitude proves mechanical (not thermal) mechanism.
SdrD/10PS (556 res, 4 domains): pulse disassembled a catastrophic
inter-domain blob (117 -> 14 full).

Port: `PULSE_AMP` / `PULSE_OMEGA` params + kick block added to
waveform_template.ergo, verbatim formula and placement (OFF offsets
dropped for the sequential template; kick gated by PULSE_AMP > 0).
Generator: `--pulse-amp` / `--pulse-omega`. Certification: regression
regen of 4I1H dock 0.0 with no pulse flags differs from the delivered
variant ONLY in the inert pulse lines (AMP = 0.0 default) -> existing
results bitwise unaffected.

First pulse runs (w=0.002, A=0.05): 4I1H dock seeds 1.0/3.0 (live traps),
4I1H base 1.0 + pulse (does the pulse also prevent the early-collapse
explosion?), 3IFW seeds 0.0/4.0. Baselines all in hand (sec 11-12).


### Pulse result (2026-08-22): NEGATIVE on this campaign's traps

w=0.002, A=0.05 (the 1SNO/SdrD-certified setting), internal = SVD on all:

| case | baseline | + pulse | delta |
|---|---|---|---|
| 4I1H dock 1.0 | 9.83 | 10.23 | +0.40 worse |
| 4I1H dock 3.0 | 8.89 | 10.15 | +1.26 worse |
| 4I1H base 1.0 (explosion) | 878.4 | 766.8 | still exploded |
| 3IFW 0.0 | 8.16 | 8.55 | +0.39 worse |
| 3IFW 4.0 | 6.51 | 7.05 | +0.54 worse |

Min-over-trajectory never beats the baseline final either (no transient
rescue followed by re-trap). Per pre-registered criteria this is null to
mildly harmful across the board.

Diagnosis (why 1SNO worked and this didn't): (a) the 1SNO pulse was
mode-TARGETED — lobe peak placed over the trapped domain-1/register
error; a generic mode-1 lobe across 223-306 residues does not match
these traps; (b) SdrD's rescue disassembled a LOOSE inter-domain blob,
while 4I1H/3IFW traps are compact wrong basins (rgyr near-native) —
rocking a compact object does no internal work; (c) the 4I1H base
explosion is a first-1000-frame runaway; the slow pulse reaches full
amplitude only near frame ~800 and cannot prevent it.

Conclusion: coherent global agitation is not a general trap-escape
mechanism in this engine — it works when the drive is matched to the
specific trapped mode. Per-trap mode tuning costs more than it saves.
Seed-scan driver (cheap basin lottery) is now the unequivocal next move.


---

## 14. Seed-scan driver result (2026-08-22)

16 seeds scanned to 24k (4I1H dock recipe, quench off, gate at 48k).
Determinism verified bitwise: scan seeds 0-4 at frame 24000 == the 96k
runs at frame 24000, all five. Continuation-by-rerun is exact.

Scan ranking (24k): 0 (8.31) < 15 (9.18) < 7 (9.59) < 6 (10.02) < ...
Extremes predict finals (seed 0 best, seeds 1/3 worst at both ends);
mid-table is noisy (seed 4: 10th at 24k, 2nd at 96k).

Continuations (production 96k, internal = SVD):

| seed | 24k | 96k final | per-domain (D1/D2/D3/D4) |
|---|---|---|---|
| 15.0 | 9.18 | **8.22** | 2.17 / 2.83 / 5.54 / 3.12 |
| 7.0 | 9.59 | **8.72** | 3.07 / 4.09 / 6.38 / 3.02 |

**Verdict: outcome #2 — the golden-seed effect is real and rare.** Neither
scan winner beats seed 0's 5.86; both land in the 8-9 cluster with every
other non-zero seed. Best-of-16 at 24k does not reliably find another
5.86-class catchment. Full dock table (7 seeds): 5.86, 7.89, 8.22, 8.72,
8.89, 8.93, 9.83 (mean 8.49, median 8.72).

**Sharpened diagnosis — docking, not domain folding, now binds.** Seed
15 folds three of four domains to 2.2-3.1 units (5.4-7.8 A) — near
isolated-domain quality — yet finishes at 8.22 globally, worse than seed
0 whose domains are worse (4.98/2.46/4.93/3.11) but whose domains are
ARRANGED better. At 4 domains the residual error is inter-domain
placement, i.e. the docking phase (48k frames post-gate) is too short or
too weak to fix arrangement. D3 (67 res) is the weakest domain across
seeds (5.5-6.4) — small, late, and presumably dragged by its neighbors.

Next levers, ranked: (a) earlier gate (dock-from 24000, doubling docked
time) on seed 15 — cheap, directly targets the binding constraint;
(b) 192k on dock 0.0 (asymptote of the golden catchment);
(c) accept the ceiling and write up.


---

## 15. Domain rigid-body quaternion MC (2026-08-22)

Motivation (user proposal): per-residue jitter has no fast collective
rotational channel, so domains cannot reorient as units post-gate — the
seed-15 result (domains 2.2-3.1, global 8.22) showed arrangement, not
domain folding, is the binding constraint. Quaternions: no gimbal lock,
cheaper than Euler — and the template already owns the certified Jacobi
quaternion eigensolver + quaternion->rotation code.

Mechanism (option A, move set not steering): every MC_EVERY frames
post-gate, each domain gets a hash-deterministic small rigid rotation
(angle in [-MC_ANGLE, MC_ANGLE], quaternion-sampled axis) about its COM,
applied to positions AND velocities; accepted iff inter-domain Go +
steric energy does not increase (greedy). Internal structure preserved
exactly by construction. Tests whether the bottleneck is kinetic (no
channel) or thermodynamic (wrong arrangements preferred).

Build: MC_EVERY (default 0 = off), MC_ANGLE (default 0.08), NDOM,
DOM_BEG/DOM_END table; generator flags --mc-every/--mc-angle (hard error
without --domains). Nested IF gates (no MOD-by-zero).

Certification: (1) regression regen of 4I1H dock 0.0: 176 diff lines,
ALL additions inside the gated pulse/MC blocks, zero lines removed or
changed -> dynamics bitwise-unaffected at defaults. (2) Energy mirror:
Python replication of the Go energy on dock-15.0's final structure
matches the engine's CSV e_native to 4 decimals (7.8044); inter-domain
share = 1.69 units — the MC move's target energy.

First runs: 4I1H dock + MC (every 100 frames, 480 moves/domain
post-gate) on seed 15.0 (well-folded domains, bad arrangement — the
target case) and seed 0.0 (does MC improve the golden catchment too?).
Baselines: 8.22 and 5.86.


### MC rotation-only result: NULL (and diagnostic)

mc-every 100, angle 0.08, greedy, post-gate. Internal = SVD on both.

- seed 15.0: 8.22 -> 8.12 (null by the pre-registered >=1.5 criterion)
- seed 0.0: 5.86 -> 6.21 (null/slightly worse, within the +/-0.5 band)

Error decomposition after global alignment (seed 15): per-domain COM
offsets are D1 3.0, D2 4.7, D3 4.0, D4 **11.2** model units — D4 is
FOLDED (internal 3.34) but parked ~28 A from its native position. A
rotation about a domain's own COM cannot move the COM: the residual
error is substantially TRANSLATIONAL and the rotation-only move set is
blind to it by construction. Fix: rigid translation moves with the same
greedy acceptance (MC_TRANS, default 0.3) — full 6-DOF rigid-body MC.
Template + generator updated, regression re-certified (additions-only).
Next runs: 4i1h_dock_mct seeds 15.0 / 0.0, same baselines (8.22 / 5.86).


### Metropolis MC iteration (2026-08-22)

Greedy 6-DOF MC result: null-to-harmful (15.0: 8.22 -> 8.74; 0.0: 5.86
-> 6.14; D4 COM offset 11.2 -> 12.1; baseline relaxes to LOWER inter
energy than the MC run). Diagnosis: the energy function is innocent
(native arrangement has inter-Go energy exactly 0 vs trap's 1.69) but
every small rigid move from the trap goes uphill -> greedy paralyzed.
Barriers exceed step size: this is the pulse/heat lesson one level down
— small-step downhill-only machinery cannot escape, on ANY coordinate.

Fix: Metropolis acceptance (MC_TEMP param, EXP(-dE/T) uphill acceptance,
hash-deterministic uniform), annealed linearly to 0 over the first 60%
of the post-gate window (= quench frame at gate 0.5M / quench 0.8M).
Greedy path behavior identical at MC_TEMP=0 (regression: 3 replaced
condition lines, behavior-preserving at T=0). First guess T=0.1 (~order
of per-move dE). Runs: 4i1h_dock_mcm seeds 15.0/0.0, baselines 8.22/5.86.
If Metropolis also fails: no post-hoc move policy substitutes for drawing
the right catchment during collapse -> fix must act during collapse
(earlier gate / sequential domain staging), not after.


### Metropolis MC result: NULL — post-collapse rescue branch CLOSED

MC_TEMP 0.1, annealed to greedy by quench; internal = SVD on both.

- seed 15.0: 8.22 -> 8.55 (worse; D4 COM offset still 10.4 — the mover
  cannot unpark a folded domain even with heated uphill acceptance)
- seed 0.0: 5.86 -> 5.72 (marginal, within noise)

Campaign-level conclusion: heat, coherent pulses, and heated collective
rigid-body moves ALL fail post-collapse. No post-hoc move policy
substitutes for drawing the right catchment during collapse. The fix
must act DURING collapse.

## 16. Next experiment: early gate (dock-from 24000)

User decision over sequential/co-translational staging (sequential needs
axial positioning solved first — deferred). Rationale: docking forces
act while the chain is still molten and rearrangeable, rather than on
rigid collapsed domains. Risk (pre-registered): gate-on at 24k hits
less-folded structures -> bigger e_native spike -> possible instability
(cf. the always-on baseline explosions). Watch the 24k spike. Seeds
15.0 (target case) and 0.0 (golden catchment), MC off — one variable
changed vs the 48k-gate baselines (8.22 / 5.86).


---

## 17. Axial pre-positioned init (2026-08-22)

Early-gate (dock-from 24000) result: NULL on both seeds (15.0: 8.22 ->
8.19; 0.0: 5.86 -> 5.71; 24k gate-on spikes 2398/5969, no explosion).
Docking-time budget is not the constraint. Campaign-wide: arrangement is
decided in the first ~24k frames of collapse; nothing applied afterward
(heat, pulse, heated 6-DOF rigid MC, earlier interface forces) revises
it. The remaining place to act is the INITIAL CONDITION.

Built: --axial-init (requires --domains). Each domain's start residue is
anchored at that domain's native COM (model units); the self-avoiding
random walk grows each domain's denatured coil from its anchor
(ATT := 20 pre-expires the walk for anchored residues; subsequent
residues walk from the anchor). Domains begin as extended coils in
native-like axial arrangement — the ribosome-exit-tunnel geometry, per
the co-translational argument. Explicitly a native-biased INIT: this
tests "what does the dynamics need", not ab-initio prediction.

First runs: 4I1H, gate 48k, MC off, seeds 15.0 (target: 8.22, D4 parked
~11 units out) and 0.0 (golden: 5.86). If axial init folds 4I1H cleanly,
collapse geometry — not any post-collapse machinery — is the whole game.


---

## 18. Oriented-residue (Cosserat ribbon) dynamics (2026-08-22)

User correction, accepted: the quaternion solver was being used as a
GAUGE (RMSD, MC moves) while orientation was never part of the dynamical
state. Per-residue state was position + velocity + scalar Kuramoto phase
(inert at HB_CAP=0). Rotational registration had no dynamical channel
DURING collapse — every post-collapse fix (pulse, MC, early gate) was
palliative by construction.

Built: each residue carries orientation quaternion q_i + angular velocity
w_i, integrated per frame (q_dot = 0.5 w (x) q, renormalized, damped).
Two couplings, active from frame 0:
  1. Neighbor alignment torque (FRAME_K): relative rotation q_i^-1 (x)
     q_i+1 vs native relative frame (generator-emitted Frenet-frame
     quaternions); error vector drives pair torques.
  2. Orientation->position coupling (FRAME_POS_K): p_i+1 pulled toward
     p_i + R(q_i) . v*_i (native bond in local frame). Rotations
     translate: misregistered orientation pushes backbone atoms during
     collapse.
Both default 0 (regression: 2542 diff lines, ALL additions, 0 removed —
emitted native-frame data dominates the line count).

Certification (mirror-first): (1) native fixed point: coupling force =
0 at native structure (max 1.2e-5, literal rounding); (2) FD check:
coupling force = -dE/dp to 1e-5; (3) torque sign: a twisted pair
torques BACK toward the native relative frame (error angle decreases).
First settings are guesses: FRAME_K 0.5, FRAME_POS_K 0.5 — sweep if
promising. Runs: 4I1H dock, seeds 15.0 / 0.0, baselines 8.22 / 5.86.


### Frame dynamics, first run (K=0.5/0.5): direction CONFIRMED, calibration wrong

- Collapse phase improves with orientation integration (the user's core
  claim): seed 0.0 at 24k = 7.18 vs baseline 8.31; per-domain folds
  2.12/2.68/5.89/3.21 vs baseline 4.98/2.46/4.93/3.11 (D1 4.98 -> 2.12).
  Global RMSD wash on 0.0 (5.86 -> 5.96): arrangement unchanged.
- Seed 15.0: late instability — 7.72 @76800 -> 12.71 @96000, e_native
  14 -> 95, rgyr 19.6. Torque wind-up: persistent alignment torque +
  0.98 angular damping + zero thermal masking at quench -> coherent
  limit cycle. K=0.5 too stiff.
- Next: K=0.1/0.1 pair; if post-quench climb persists, taper frame
  forces to zero by quench (same anneal shape as MC_TEMP).


### Frame K=0.1/0.1: BREAKTHROUGH — both seeds improve, no wind-up

| seed | baseline | frame K=0.1 | notes |
|---|---|---|---|
| 15.0 | 8.22 | **7.09** | D1 = 0.66 (best domain fold ever, in-chain); D4 COM 10.8 -> 6.9 (unparking via torque); monotone descent through quench; e_native 3.3 lowest ever for this seed |
| 0.0 | 5.86 | **5.18** | new campaign best; all 4 domains < 5.5; COM offsets small |

Internal = SVD on both. K=0.5's instability was stiffness (torque
wind-up in the cold phase), cured by K=0.1. Orientation integrated
DURING collapse is the first lever in the campaign to beat both seeds
simultaneously — heat, pulse, heated rigid-body MC, and early gating
all failed post-collapse; this acts while the fold forms.

Next: K sweep {0.05, 0.2} x seeds {15, 0} to bracket; 192k frame run
on seed 0.0 for the asymptote.


### K sweep result: optimum K = 0.1; D3 is now the weakest link

| K | 15.0 | 0.0 | stability |
|---|---|---|---|
| 0 | 8.22 | 5.86 | — |
| 0.05 | 7.79 | 5.30 | flat |
| 0.1 | 7.09 | 5.18 | flat |
| 0.2 | 7.00 | 6.09 | 0.0 creeping (5.80->6.09) |
| 0.5 | 12.72 | 5.96 | wind-up |

Per-domain at K=0.2 (seed 15): 1.84/2.03/3.93/2.89 — four good domains
in a 306-res chain. Residual error concentrated in D3 (4-6 internal,
COM 4-6 off) and D2-D3-D4 relative geometry. Standard setting: K=0.1.
Next: 192k asymptote at K=0.1 (gate proportional at 96k, quench 153.6k),
seeds 0.0/15.0 — both 96k trajectories still descending at the end.


### 192k asymptote at K=0.1: golden seed still descending, trapped seed flat

| seed | 96k | 192k | post-quench |
|---|---|---|---|
| 0.0 | 5.18 | **4.38** (best ever; per-domain 2.36/2.78/4.41/0.89) | descending 4.54->4.38 |
| 15.0 | 7.09 | 7.00 (0.65/3.64/5.18/3.40) | flat 6.95->7.00 |

- D4 (formerly parked ~11 units out) now folds to 0.89 in-chain.
- Runtime rescues good catchments, NOT traps — same law as T4L at 164.
- D3 (67 res) is the persistent laggard across ALL experiments: weakest
  internal fold and 4-6 unit COM offset every time. Late, small, and
  dragged by neighbors; possibly genuinely harder landscape (its
  register/torsion content per residue) — worth a standalone fold test
  (D3 alone, 67 res, well inside validated range) to separate
  landscape-hardness from chain-context drag.

## 19. Campaign state (2026-08-22)

Recipe: fold-then-dock staging + oriented-ribbon dynamics (K=0.1) +
native targets + Go contacts, 5-16 seed pool. 4I1H (306 res, 4 domains):
best 4.38 units = 11 A global, domains 0.9-4.4 units. Instruments: Jacobi
RMSD certified, per-domain Kabsch, all SVD-verified.
Open: D3 standalone test; K=0.1 seed rescan (the seed landscape changed
with the orientation field on); 384k on seed 0.0; axial-init variants
remain on the shelf (superseded by frame dynamics but not refuted).

## 20. HB_CAP=0 confound discovered (2026-08-22) — entire campaign ran with H-bonds OFF
Trigger: D3-solo outs showed nhb == 0 every frame, all seeds.
Root cause: all 4I1H/3IFW variants were generated with --hb-cap 0
(intended "uncapped"); but the formation gate is `DEG_I < HB_CAP`,
so HB_CAP=0 disables de novo hbond formation entirely. Template
default is HB_CAP=2. Verified nhb==0 in dock_0.0, base_0.0,
frame192k_0.0, 3ifw_0.0 outs. EVERY campaign number to date —
baseline 5.86, K=0.1 breakthrough (7.09/5.18), 192k asymptote 4.38 —
was obtained with zero hydrogen bonds. K-response curve and all
comparisons remain internally valid (same confound everywhere), but
absolute values and possibly the K optimum may shift with HB_CAP=2.
D3-solo hb0 result (recorded but confounded): 4.13/4.06/4.43 units
across seeds 0/1/2 — solo ~= in-chain (3.93-4.41), i.e. NO context
drag; D3 is intrinsically hard *without* hbonds.
Fix: one-line patch HB_CAP 0->2 (diffs verified, nothing else touched).
Re-runs queued: d3_solo_hb2 seeds 0/1/2 (primary read: does D3 fold
alone with hbonds?), framek01_hb2 seeds 0.0/15.0 (direct before/after
vs 7.09/5.18). If hb2 changes the picture, the seed-rescan plan moves
to hb2 conditions and key campaign landmarks get recertified.

## 21. HB_CAP=2 recheck result (2026-08-22) — stabilizer, not rescuer
Formation path works (nhb ~50 by frame 100 on 67-res D3; ~260 on
306-res 4I1H). Results: framek01 seed 0: 5.18 -> 5.03 (small gain);
seed 15 (trapped): 7.09 -> 8.40 (WORSE — bonds cement the trap, form
in first ~100 frames before arrangement is decided). D3 solo hb2:
4.16/3.91/3.52 (best min 3.17) — still outside folded band; second
pre-registered branch CONFIRMED: D3 landscape is intrinsically hard
for this force field (not hbond starvation, not context drag).
Campaign default is now HB_CAP=2; hb0 numbers are historical. Open:
K mini-sweep at hb2 before any seed rescan (optimum may shift).

## 22. Proinsulin (T1D/MIDY) campaign opened (2026-08-22)
Target: 2KQP full-length human proinsulin NMR (86 res, model 1;
analog substitutions AspB10/LysB28/ProB29 present in deposit).
Disulfide map verified vs sequence: A6-A11 = resnum 71-76,
A7-B7 = 72-7, A20-B19 = 85-19. Akita MIDY mutation C96Y
(preproinsulin) = CysA7 = resnum 72 (partner of B7).
No misfolded proinsulin PDB exists (misfolds are ensembles) —
misfold is the simulation OUTPUT, WT vs mutant under identical
conditions. Phase 1: bare WT, no disulfide term, K=0.1, HB_CAP=2,
96k/quench 76800, seeds 0/1/2 (built + verified: seq exact, 6 Cys,
scale 0.397185, 57 contacts). Phase 2: cystine restraint term
(harmonic to native Cys-Cys distance, pairs above) + FD validation,
then Akita C72Y mutant runs both ways. Note: in vitro proinsulin
oxidative folding is hard even WT — bare run is expected to
underfold; the ss/bare gap is itself the measurement.

## 23. Breakable cystine restraint term (2026-08-22)
Motivation: bare-field 2KQP folds (3.47/4.71/4.08; all three cystine
pairs emergent at native distance: 2.03/1.90/2.02 vs 2.05/1.79/2.02)
prove restraints are redundant for WT — user called double-dipping,
confirmed. But the Akita MIDY mechanism IS a deleted disulfide
(CysA7-B7); without bonds present in WT the mutant has nothing to
lose and the contrast collapses to a hydrophobicity tweak.
Design: harmonic Calpha-Calpha restraint, E = CSS_K*(D-R0)^2,
FM = -2*CSS_K*(D-R0), same +/- impulse convention as Go contacts.
R0 from scaled native geometry (2.047/1.786/2.016). Breakable per
pair via CYS_ON. Defaults CSS_K=0/NCYSPAIR=0 = inert; template diff
is additions-only (regression-verified vs bare 2KQP file).
FD validation: max |analytic - central FD| = 2.4e-08 (200 random
configs). Generator flags: --cystine / --cystine-off / --css-k /
--mutate "pos:AA" (sequence-dependent terms only; Go map is
native-derived so geometry is unchanged).
Caveat on record: Akita C72Y also RAISES hydrophobicity at position
72 (C=0.0 -> Y=1.0 in HYDRO table) — the deleted bond is the intended
lever, but the added sticky Tyr is a known co-varying artifact.
Runs queued: 2kqp_ss seeds 0/1/2 (all bonds on) vs 2kqp_akita seeds
0/1/2 (72-7 deleted + C72Y), identical everything else.

## 24. Akita deletion read: NEGATIVE (2026-08-22)
WT+ss (all 3 bonds): 3.68/4.72/4.05 vs bare 3.47/4.71/4.08 — ss
inert as predicted (double-dipping confirmed quantitatively).
Akita C72Y + A7-B7 deleted: 2.90/4.44/4.06 — NOT worse; better on
seed 0. The deleted 72-7 seam stays at native distance anyway
(1.64-1.87 vs 1.79): the Go contact map holds the seam closed;
A7-B7 is topologically redundant in this landscape. Seed-0
improvement attributed to the sticky-Tyr artifact (HYDRO 0.0->1.0).
Conclusion: absence of the bond is not the MIDY lever in silico —
real Akita is driven by the freed CysB7 forming WRONG disulfides.
## 25. Mispairing variant built (2026-08-22)
Same harmonic form (FD validation carries over from §23).
akmis = akita + NMISPAIR=2: freed Cys7 (B7) competing restraints to
Cys76 (A11) and Cys85 (A20), R0=2.0 (generic disulfide Ca-Ca),
MIS_K=0.25 = half of CSS_K so wrong bonds compete, not dominate.
WT mispair list empty (inert). Diff vs akita: mispair-only (37
lines, verified). Reads: akmis significantly worse than akita/ss on
matched seeds = kinetic-competition model captures MIDY; watch
whether 7-76/7-85 approach 2.0 in final structures (wrong bond
actually formed) vs merely strained native (7-72 stays ~native).

## 26. Mispairing result + pulse rescue test (2026-08-22)
akmis: 4.14/4.34/4.17 vs akita 2.90/4.44/4.06. Wrong bond 7-76
CLOSES on seeds 0/2 (1.85/1.75); 7-85 never engages (3.0-3.4).
Cost ~1 unit where wrong bond forms: strained fold, not catastrophe.
Biology gap identified: real MIDY catastrophe is INTERmolecular
(dominant-negative disulfide-linked oligomers of mutant onto WT),
plus co-translational vectorial folding and PDI/chaperone machinery
— none expressible single-chain. Next real MIDY model: two-chain
Akita+WT box with inter-chain mispair restraints.
Pulse rescue pre-registered: harmonic restraints cannot break, only
re-route; akmis+pulse (0.05/0.002) on seeds 0/1/2 built. Recovery
to <=3.5 on seed 0 = re-routing works; unchanged = harmonic traps
need a breaking mechanism, not agitation.

## 27. Pulse rescue on mispair trap: POSITIVE on soft traps (2026-08-22)
akmis+pulse: 3.16/4.61/3.81 vs akmis 4.14/4.34/4.17. Seed 0: wrong
bond 7-76 OPENED (1.85 -> 3.39), native seam 72-7 re-closed (1.62),
RMSD 4.14 -> 3.16 (min 2.94) — chain climbed out of the restraint
geometry entirely (harmonic not broken, escaped: cost at 3.39 is
small and flat). Seed 1 unchanged (nothing to rescue). Law updated:
coherent agitation rescues SOFT traps (still plastic), not compact
settled basins — consistent across 4I1H (fail) and 2KQP (success).

## 28. Two-chain dominant-negative MIDY model built (2026-08-22)
NRES=172: mutant chain (1-86: C72Y, A7-B7 deleted, intra mispairs
7-76/7-85) + WT chain (87-172: all 3 disulfides). CHAIN_BREAK=86:
Morse/angle/torsion/frame-torque/frame-position loops all guarded
(IF I /= CHAIN_BREAK...), inter-chain Go contacts excluded (114 =
2x57 exactly, verified), chain 2 anchored at (22,10,10) start.
Weapon: inter-chain mispair restraints mutant Cys7 -> WT Cys
158/162/171 (MIS_K=0.25, R0=2.0). dimwt control: WT+WT, all bonds
on, no mispairs. Regression: single-chain files unchanged except
inert additions. Analysis: PER-CHAIN Kabsch from FINAL_STRUCTURE
(global RMSD confounded by quaternary arrangement). Reads: (1)
dimwt both chains fold ~ bare singles = two-chain baseline sane;
(2) dimak: WT chain significantly worse than dimwt WT chain =
dominant-negative capture; (3) inter-chain distances 7-158/162/171
-> ~2.0 = aggregate bond formed.

## 29. Two-chain result (2026-08-22): capture YES, toxicity INCONCLUSIVE
dimwt: chains fold independently (2.76-4.79), drift apart
(COM sep 17.7-24.8). dimak: chains end 2-5x closer (4.3-10.1) —
mutant Cys7 closes toward WT Cys to 2.37-2.52 (target 2.0) =
inter-chain capture, the aggregation step of MIDY. But WT fold
damage marginal (dimak WT 3.98 mean vs dimwt 3.79): wrong bonds
strain but don't fully close at MIS_K=0.25. Two-chain assay cannot
yet rule dominant-negative toxicity in or out.

## 30. Escalation build (2026-08-22): full-strength inter-chain, closer start
Per-pair mispair K (MIS_KK array; syntax i-j:k). dimak2: intra
mispairs 0.25, inter-chain (7->158/162/171) at 0.5 = full disulfide
strength once formed. Chain separation 12 -> 8 units (--chain-sep;
anchor 18,10,10). Matched control dimwt8 rebuilt at sep 8.
Reads: (1) inter-chain bonds fully close (~2.0); (2) WT chain in
dimak2 significantly worse than dimwt8 = dominant-negative toxicity,
the core MIDY claim; (3) if still no damage with closed wrong bonds,
the model says WT proinsulin fold is robust to attachment and the
toxicity must come from larger oligomers (3+ chains) or ER context.

## 31. Steric explosion analysis (2026-08-22)
dimwt8 seed 2.0 exploded at frame ~870 (rgyr 8 -> 3545, e_native
8.6e9 = corpse not cause). Root cause analysis: physical SEED
(thermal jitter walks inter-chain pair below D~0.5 in dense pack),
numerical DETONATION (steric impulse overshoots the whole gap below
D=0.52: solve D^7 = DT^2*FORCE_SCALE*eps*sig^6; fixed linear damping
cannot stabilize unbounded D^-6 gain; Morse short-range softness then
enables bond pass-through and the angle term's 1/UN^2 diverges as
amplifier). Placement was NOT the cause (walk self-avoidance is
chain-agnostic, DD<1.55 rejected). Diagnosis: the event is
resolution-limited — the fixed step DT cannot track the potential
where it is steep. Resolution: temporal, see §32.

## 32. Adaptive substepping implemented (2026-08-22)
Standing design constraint (user): NO artificial clamping/damping —
nothing restricted unless physical; numerical instabilities are
resolved by resolution, never by caps. Implementation: temporal
resolution. Per frame, a priori closest-approach
scan (steric pairs + backbone bonds) -> NSUB = min(64,
floor(0.8/DMIN)+1); the full force+integrate block runs NSUB times at
DTW = DT/NSUB with forces recomputed per substep. Dampers rooted, not
repeated (DAMP_SUB/FDAMP_SUB = X^(1/NSUB), exact pass-through at
NSUB=1 for the bitwise oracle). Spec: Ergo_Activity_Bounds §5
(activity_bounds_section5.md, rewritten). Template DO/ENDDO and
IF/ENDIF balanced (89/89, 100/100 in generated dimer); region verified
free of bare DT. Verification protocol unchanged: five healthy runs
must be bitwise identical; dimwt8_2.0 must survive frame 870.

## §33 Adaptive substepping — verification + first results (2026-08-23)

**Oracle diagnosis.** The pre-registered bitwise oracle (substepped == unsubstepped
on healthy runs) FAILED on all five healthy dimer runs — first divergence at the
first logged frame (frame 10). Root cause located and it is NOT a wrap bug:
the seeded dimer start at --chain-sep 8 has a closest steric approach of
DMIN = 0.679 (residues 22–88, inter-chain) < SUBSTEP_D = 0.8 from frame 0.
Every dimer run at sep 8 is substepping (NSUB>=2) from its first frame, so
bitwise identity with the old unsubstepped runs was impossible by construction.
The oracle was mis-specified for the dimer family, not the implementation.
The strict NSUB=1 bitwise test remains unverified — it needs a run whose
DMIN never crosses 0.8 (single-chain variants qualify). PENDING USER APPROVAL
before treating that as settled.

**dimwt8_2.0 SURVIVED.** Old run detonated at frame ~870 (rgyr max 14092,
e_native 5.5e10, corpse). Substepped run: rgyr max 8.1, e_native max 5.1e3,
final rgyr 6.73, folded. The §31 explosion was resolution-limited, exactly as
the absolutism philosophy predicts — fixed by time resolution, no caps.
dimwt8_0.0 old run also had a hidden transient (rgyr max 1445) that the
substepped run never develops (max 18.5). dimak2_2.0 shows one transient
excursion (rgyr 71, e_native 2.7e6) but recovers fully and folds.

**Per-chain Kabsch RMSD (new, substepped finals) vs native:**
- dimwt8: 4.70/4.07, 4.21/4.89, 4.30/5.24 ; COM sep 19.25/14.06/8.52
- dimak2: 4.56/3.72, 4.40/4.22, 3.73/4.16 ; COM sep 9.22/7.91/5.35

**Toxicity read (MIDY question): INCONCLUSIVE at two-chain scale.** WT partner
chains in dimak2 (3.72/4.22/4.16) fold as well or better than WT chains in
dimwt8 (4.07/4.89/5.24) — no toxicity observed even at full-strength
inter-chain bonds and sep-8 start. Capture/aggregation persists: dimak2 COM
separations (5.4-9.2) stay well below dimwt8 (8.5-19.3) — the Akita chain
sticks. But a two-chain assay cannot settle the dominant-negative question:
real MIDY toxicity may require oligomer-scale clusters (3+ chains, one mutant
seeding many WT) or ER context (crowding, chaperones, membrane) that this
model does not contain. Next: oligomer variants if we pursue it.

## 34. Trimer dose series build (2026-08-23): mutant-dose toxicity sweep
Second-opinion convergence: oligomer scale is the ranked next step (our §33
and Deepseek agree). Design: hold chain count at 3, vary mutant dose —
triwt (0M/3), trim1 (1M/3, low seeding), trim2 (2M/3, high seeding), 3 seeds
each. Read: WT-chain fold quality vs mutant dose = the toxicity curve; a
dose-dependent WT degradation is the dominant-negative signature a 2-chain
assay cannot resolve.

Implementation: generator extended to multi-chain (--chain-break "86,172";
template gains CHAIN_BREAK2 with all junction guards duplicated; CYS/MIS
arrays 8 -> 16; chain-3 anchor at (14, 16.93, 10) completing a side-8
triangle with (10,10,10)/(18,10,10)). Trimer json 2kqp_trimer.json (258 res).
Cystine: 9 native pairs (3/chain), mutant A7-B7 OFF per mutant chain
(trim1: pair 72-7; trim2: + 158-93). Mispair: intra-mutant 7->76/85 @0.25
(mirroring chain 2: 93->162/171); inter full-strength @0.5 from each mutant
Cys7 to every other chain's Cys 72/76/85 equivalents (trim1: 8 pairs;
trim2: 16 incl. mutant<->mutant cross-links). Substepping active from frame 0
(triangle start has inter-chain DMIN < 0.8) — expected, and dimwt8_2.0 showed
the resolver holds. All nine files verified: NRES=258, breaks 86/172,
NCYSPAIR=9, NMISPAIR=0/8/16, CYS_ON flags correct, IF/ENDIF 101/101,
ENDDO 89, no VMAX.

## 35. Trimer dose series result (2026-08-23): strong capture, WT degradation absent-to-weak
All eight uploaded runs healthy — no explosions anywhere (rgyr max 8.6-12.7;
substepping held across the whole family; triwt seed 0 not yet uploaded).

Wrong-bond closure is STRONG at trimer scale: mutant Cys7 sits at 2.2-3.0
model units from essentially every targeted Cys on partner chains (R0=2.0),
several fully closed at 1.7-2.3 in trim2. Capture network denser than any
dimer run (dimers: best 2.16 on one pair). COM separations contract with
dose: trim2 seeds 1/2 show chain1-chain2 at 8.8/4.1 vs triwt 14.2/8.7.

Per-chain Kabsch RMSD (chains 1/2/3):
- triwt (0M): 5.11/2.75/4.05 ; 4.62/4.83/2.98        -> WT pool mean 4.06
- trim1 (1M): 3.20/4.05/4.97 ; 5.60/4.55/4.17 ; 3.68/4.47/3.16
  -> WT chains mean 4.22, mutant chain mean 4.16
- trim2 (2M): 4.21/4.40/5.40 ; 4.84/3.93/5.25 ; 4.63/4.02/4.12
  -> WT chain (ch3) mean 4.92, mutant chains mean 4.34

Dose response: WT mean 4.06 (0M) -> 4.22 (1M) -> 4.92 (2M). Weak monotonic
uptrend at high dose but inside seed-to-seed spread (~1 unit), n=2-3 per
tier — NOT a resolved dominant-negative signal. The Akita chains themselves
fold as well as WT (4.16/4.34) — mispairing restraints at these strengths
strain but do not misfold the mutant either.

Campaign-level statement now: across 2-chain (§29-33) and 3-chain (this
section) assays, at up to full-strength wrong-bond networks and 2/3 mutant
dose, contact-mediated fold corruption of WT proinsulin is NOT observed in
this field. If MIDY dominant-negative toxicity is real, it requires
ingredients the model lacks (ERAD/proteostasis, chaperones, membrane,
crowding) — the simulation negative is consistent with the literature gap
(no paper directly measures structural corruption of WT by mutant; band-
intensity co-expression assays only). Open: triwt seed 0 for the full
control tier; optionally a steric-hindrance read (does captured WT get
proteasomally-stuck = remains extended longer during folding, i.e. folding
TIME not final RMSD).

### §35 addendum (2026-08-23): triwt_0.0 received
Healthy (rgyr max 12.7, en max 9.2e3); chains 3.30/3.66/4.74, COM
19.3/15.4/19.8 (drift apart, WT-WT baseline). Control tier complete:
WT 0M mean 4.00 (n=9 chains, 3 seeds). Updated dose curve:
4.00 (0M) -> 4.23 (1M) -> 4.92 (2M). The uptrend at high dose persists
but remains within seed noise; verdict unchanged — no resolved
dominant-negative signal.

## 36. Per-chain RMSD telemetry (2026-08-23) — instrumentation only
Global rmsd_native is confounded in multi-chain systems (inter-chain drift
dominates fold signal; settle-time extraction degenerate, §35 follow-up).
Fix: COMPUTE_RMSD_CHAINS(), a segment-bounded clone of the verified Jacobi
Kabsch block (pure read-only instrumentation, zero physics contact).
Segments from CHAIN_BREAK/CHAIN_BREAK2 (1-4 chains supported; single-chain
RMSD_CHAIN(1) == RMSD_NATIVE). CSV row gains rmsd_c1..rmsd_c4 columns
(0.0 for absent chains). Enables folding-time read: frames until each
chain's own RMSD drops below threshold and stays = kinetic toxicity
channel (ERAD-relevant delay) invisible in final structures.
All nine trimer variants regenerated with telemetry; same physics,
bitwise-equivalent force path (telemetry runs after integration, reads
only). Delivered as .ergo directly per user preference.

## 37. Folding-time / kinetic-toxicity read (2026-08-23): NEGATIVE
Telemetry verified first: old 18 columns bitwise-identical to the pre-
telemetry runs (max abs diff 0.0 on all nine) and engine per-chain Kabsch
matches offline Kabsch on FINAL_STRUCTURE to printed digits. Telemetry is
read-only confirmed empirically, not just by construction.

Sustained fold time = first frame per-chain RMSD < 5.0, staying below
(+1.0 excursion tolerance). Per-chain fold frames:

- triwt (0M): c1 270/1980/79710, c2 270/30/510, c3 48860/17520/80
- trim1 (1M): c1(M) 600/never/1500, c2 170/30/620, c3 90620/2020/80
- trim2 (2M): c1(M) 3330/81000/1590, c2(M) 460/350/1060, c3 never/1150/80

Median WT fold time by dose: 0M 510, 1M 395, 2M 615 frames.
NO dose-ordered delay — spread within a tier (30 -> 90620 frames) dwarfs
any between-tier difference; folding time is seed/landscape-noise
dominated. The doubly-flanked WT chain in trim2 (c3) folds no slower than
the same chain in triwt (median 1150 vs 17520). One WT chain never
sustained <5.0 (trim2_0.0 c3, final 5.40) and one mutant neither
(trim1_1.0 c1, 5.60) — both borderline, both captured, not degraded.

Kinetic channel closed: capture does not delay WT folding in this field.
Combined with §35 (no final-RMSD degradation at any dose), the MIDY
dominant-negative hypothesis finds no support in structure OR kinetics
across 2-chain and 3-chain assays. If real, it needs ER-environment
ingredients outside the model (proteostasis load, chaperones, membrane,
redox). Campaign recommendation: document as a clean negative; further
escalation inside this force field is not informative.

## 38. Thermal-floor stressor build (2026-08-23): dose x stress factorial
Hypothesis (user + Hua-paper motivation): MIDY toxicity = kinetics x
stress. Kinetics alone negative (§37); now add sustained ER-stress analog.
Design: --thermal-floor F replaces quench-to-zero tail with sustained
thermal noise F after frame 76800 (folding schedule untouched; floor only
in what was the quench tail). Factorial: dose {0M=triwt, 2M=trim2} x
floor {f10=0.1, f25=0.25} x seeds {0,1,2} = 12 runs, with the floor=0
runs (§35/§37) as the in-hand baseline tier. Pre-registered read: WT
chain fold time + final RMSD under stress, by dose. Interaction term
(stress hurts WT preferentially at high mutant dose) = the kinetics x
stress signature. Main-effect-only (stress hurts all chains equally) =
generic noise sensitivity, NOT MIDY-specific.

## 39. Thermal-floor result (2026-08-23): qualified POSITIVE — stress strips marginal captured folds
Mechanics: pre-floor segments (frames <=76800) bitwise-identical to floor=0
runs in all 12 stress runs. Schedule splice provably inert during folding.

Controls (triwt f10/f25): settled WT folds unconditionally stable — finals
within 0.1-0.2 of floor=0, 0% post-floor time >5.0 except chains already
>5 at quench. Stress alone does nothing to WT.

trim2 (WT = chain 3, flanked by two captured mutants):
- f10: c3 = 5.35 / 5.24 / 4.01 (vs floor=0: 5.40 / 5.25 / 4.12) — no effect
- f25 seed 0: 5.37 (baseline 5.40) — no effect (already marginal)
- f25 seed 2: 4.03 (baseline 4.12) — no effect (solidly folded)
- f25 seed 1: 8.93 (baseline 5.25) — INTERACTION HIT. Within 400 frames of
  floor onset c3 jumps 5.18 -> 11.49, never returns (settles ~8.9, still
  slowly recovering at run end). Mutant chains in the same run sit still
  (4.6->4.7, 3.9) and all triwt chains at f25 sit still.

Read: the kinetics x stress hypothesis gets QUALIFIED support. Stress does
not unfold captured WT chains in general — it strips exactly the
MARGINALLY folded one (baseline 5.25, the tier's borderline case) at the
higher floor. 1/3 seeds, threshold-dependent (f25 yes, f10 no). The
signature is real but narrow: capture + sustained noise + marginal fold =
destabilization. Solid folds survive capture+stress; unfolded ones were
already unfolded. Biological echo: MIDY toxicity is stress-dependent in
vivo (ER stress precipitates beta-cell failure), and the vulnerable
population is exactly the marginally-folded captured fraction.
Caveats: single seed, no dose-response within f25 tier, n=3. A
confirmatory run set would be trim1 f25 (does a single mutant suffice
under stress?) and additional seeds of trim2 f25.

## 40. Interaction confirmation set built (2026-08-23): three tiers
Following the §39 qualified positive (trim2 f25 seed 1: marginal captured
WT stripped 5.2 -> 8.9):
- Tier 1 (dose-dependence): trim1 f25, seeds 0-2 — does ONE mutant suffice
  under stress?
- Tier 2 (reproducibility): trim2 f25, NEW seeds 3/4/5 — does the hit
  repeat, and does it track marginal baseline folds?
- Tier 3 (ceiling): f40 floor (0.4), triwt + trim2 seeds 0-2 — does higher
  stress strip the SOLID fold (seed 2, 4.12)? If even that survives,
  capture protects as much as it endangers.
Pre-registered reads: (a) trim1 f25 hit rate < trim2 f25 hit rate =
dose-ordered interaction; (b) trim2 f25 seeds 3-5 hits correlate with
marginal (>5) baseline folds; (c) f40 damage in triwt = generic threshold,
f40 damage preferentially in trim2 = mechanism scales.

## 41. Interaction confirmation results (2026-08-23): dose-ordered, marginality-targeted
Read key: state at frame 76800 (floor onset; schedule provably identical
before it) = the fold the stress inherited; final - at-quench = strip event.

Tier 1 (trim1 f25, one mutant): NO strips. at-quench == final everywhere
(marginal chains 5.72, 5.23 survive). One mutant does not suffice.

Tier 2 (trim2 f25, seeds 3-5): no NEW strip events. All chains >5 at the
end were already >5 at quench (seed 4 c3: 13.03 at quench; seed 5 c2:
7.45). Seed 3's marginal c3 (6.11) was NOT stripped (5.89). Marginality
alone does not determine stripping.

Tier 3 (f40): triwt untouched again (0.4 floor, 0% time >5 beyond pre-
existing marginal). trim2_f40_1.0: chain 1 (MUTANT) stripped 5.05 ->
16.94; same run's WT c3 marginal (5.18) survives at 5.57. Seed 1 again.

Campaign tally of strip events (chain jumps >3 units post-floor):
2 events, both in 2-mutant systems (trim2_f25_1.0 c3 WT 5.2->8.9;
trim2_f40_1.0 c1 mutant 5.1->16.9), both marginal-at-onset folds.
Zero strips in 12 control runs (triwt all floors, trim1 f25).

Conclusions: (1) dose-dependence CONFIRMED — stripping requires the
2-mutant cluster; one mutant never suffices, WT-only never strips even
at f40. (2) The vulnerable population is the marginal-folded fraction
(any chain, WT or mutant) inside a dense mutant cluster — not WT
specifically. (3) Marginality is necessary-looking but not sufficient
(seed-3 c3 6.11 survived f25) — cluster geometry decides which marginal
chain goes. MIDY model as supported: mutant clusters + sustained stress
selectively destabilize the weakest folder in the cluster; in vivo that
weakest folder includes captured WT, and ERAD disposes of the rest.

## 42. Factorial completion (2026-08-23): DOSE EFFECT CONFIRMED at baseline
trim2 floor=0 seeds 3-5 received; pre-floor segments bitwise identical to
the f25 runs (oracle holds on the new seeds too). Seed 4 chain 3 was a
landscape failure independent of stress (13.06 baseline = 13.03 at f25
quench); seed 5 c2 mutant likewise (7.31).

FULL FACTORIAL, WT chain outcomes:
- triwt (0M), all floors, n=9 chains: mean 4.00, median ~4.0, frac>5 = 11%
  (1/9), INSENSITIVE to floor level (4.00/4.01/4.03/3.99 at 0/f10/f25/f40)
- trim1 (1M) WT chains, n=6: frac>5 = 0%
- trim2 (2M) WT chain 3, floor=0, n=6 seeds: mean 6.28, median 5.33,
  frac>5 = 67% (4/6) — SIX-FOLD elevation of marginal-failure fraction,
  no stress needed. The n=3 read in §35 (4.92) undersampled this.
- Under stress: median 5.33 -> 5.63 (f25) with 2 outright strip events
  (§41). Stress amplifies but does not create the dose effect.

CORRECTED CAMPAIGN CONCLUSION (supersedes the "no structural effect"
framing of §35/§37): at 2/3 mutant dose, the captured WT chain fails to
reach a clean fold in two-thirds of seeds at baseline — the dominant-
negative signal was real but needed n=6 and the 2M dose to resolve.
Stress (sustained thermal floor) then selectively strips the marginal
members of the cluster (any genotype). MIDY sketch: mutant clusters
(i) increase the fraction of WT that folds marginally, (ii) under ER
stress, the marginal members are destroyed. Both halves now have
direct in-silico support.

## 43. Four-chain baseline build (2026-08-23): minimum viable universality test
Purpose (user framing): NOT establishing universality — a baseline for
proposed universality, a minimum viable starting point for other labs to
test. Two tiers x 3 seeds = 6 runs:
- quad3m (3 mutants / 4 chains, WT = chain 4): escalation tier; ~3/3 WT
  failure = threshold signature.
- quad2m (2 mutants / 4 chains, WT = chains 3,4): the discriminator —
  dose-FRACTION model (2/4=50% should drop toward trim1's 0%) vs
  critical-COUNT model (2 mutants already over threshold -> ~67% like
  trim2). Six WT observations resolve the fraction to 1/6 steps.
Engineering: template gains CHAIN_BREAK3 (guards cloned, same pattern);
MIS arrays widened 16 -> 40 (quad3m needs 33: 6 intra + 27 inter);
chain-4 anchor at (14, 12.31, 16.53) = tetrahedral apex over the side-8
triangle. Same seeds 0-2 as the trimer series for landscape comparability.
Verified: NMIS 22/33, NCYS 12, mutant A7-B7 bonds OFF (pairs 2,5 in
quad2m; 2,5,8 in quad3m), balanced blocks, BREAK3=258.
Pre-registered reads: (a) quad3m WT frac>5 vs trim2's 67%; (b) quad2m
WT frac>5 near 0-17% = fraction model, near 67% = count model;
(c) strip/marginality pattern per chain as in §41-42.
