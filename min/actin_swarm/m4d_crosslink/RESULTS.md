# M4d — transient crosslinking (fascin/α-actinin-like): results

Dynamic crosslink bonds on the M4a certified baseline: harmonic springs
(KLINK=20, FIXED rest L0=0.7) between beads of BOUND monomers, born
stochastically for candidate pairs within RLINK=1.0 (P = KLINKF·DT per
candidate-pair-step), dying at P = KLINKB·DT per link-step. Two anchored
trimer seeds grow parallel filaments (gap 1.5); inter-filament links
bundle them. Fixed-size slot arrays (MAXL=64), no compaction (slot =
fixed death-draw slot).

## Model / parameter decisions (final set)

| param | value | justification |
|---|---|---|
| KLINK | 20.0 | soft vs ladder KFIL=100: register pull without force spikes |
| L0 | 0.7 FIXED | birth-distance rests are zero-strain and store NO mechanical preference; fixed L0 actively pulls filaments into register (fascin enforces tight spacing). 0.7 sits just outside the WCA core (0.5612) and within candidate reach |
| RLINK | 1.0 | birth radius. CRITICAL: 27-cell stencil only covers cell-diff≤1 (|dx|≤0.75 guaranteed); candidates with d≤1.0 need the diff=2 shell → engine NBR_BUILD runs a second 98-offset candidate-only pass (125-stencil total). Mirror full-matrix = complete set. Parity verified by per-run birth identity (below) |
| KLINKF | 0.3 | birth P = 1.5e-3 /candidate-pair/step |
| KLINKB | 3.0 | death P = 1.5e-2 /link/step → nominal lifetime 66.7 |
| MAXL | 64 | steady L̄ ≤ 48 → headroom; never saturated in final runs |
| LOOPMIN | 6 | same-filament pairs need contour separation ≥6 (loop closure allowed, local crumple links forbidden; without it crumple links dominate candidates ~10:1 and drown the inter-filament signal) |
| NMAX | 96 | two barbed ends need kon·c0 > 2·koff_eff; N=60 collapses (5.4e-4 < 9e-4 nominal). Steady bound ≈ 65-70 (see overgrowth note) |
| seeds | 2 trimers, gap 1.5, parallel +x, both anchored | bundling needs ≥2 filaments; gap > RLINK so no links at t=0 — bundle self-assembles |
| WCA on linked pairs | KEPT (not excluded) | L0 > WCUT and spring/WCA agree in sign everywhere → no force switching at death → death-while-compressed catapult channel removed by construction (M4a unbind lesson). Static exclusion set = intra + junction only |
| M4a untouched | DT, kT=0.4, RCAP, σ, KON, KOFF, ladder geometry | per contract |

Draw slots (hash RNG, pure f(SEED,STEP)): noise 3I-2..3I ≤ 576;
bind/unbind 800-803 (per filament); births 810+k (k≤MAXCB=600,
NCSKIP=0 in all final runs); deaths 1500+L. Birth/death draws are
per-candidate/per-link every step; slot identity fixed.

## Oracle ladder results

**FD**: max rel err **1.20e-9** (≤1e-8). Cert config (hexamer arc +
parallel tetramer at 0.85 + 3 static links + spiral + close pair) +
σ=0.03 jitter; links loaded at strain 0.166–0.248 (forces 6.6–9.9,
uncapped, outside core).

**Static byte cert**: max |dFRC| = **4.35e-14** (≤1e-11), max |dCFG|
1.1e-15, energies agree ≤7e-16 (ewca −1.81167520617388766,
elink 1.60433617747278845). Ladder catch: mirror initially applied
anchors to beads 0-3 instead of [0,1,12,13]; FD PASSED (self-consistent)
— only the static cert caught it (eanch 10.81 vs 0.0123).

**Rate calibration** (mirror, two 8-mers at gap 0.8, steady state, no
polymerization, 40k steps, 2k burn, eligibility-normalized):
- birth: **1.477e-3** /candidate-pair-step (3484 events) vs nominal
  1.500e-3 → ratio **0.985** (Poisson ±1.7%)
- death: **1.460e-2** /link-step (3480 events) vs nominal 1.500e-2 →
  ratio **0.974**
- lifetime 67.34 vs nominal 66.67
- Mean-field: L* = k_b·C̄/k_d = 0.1012·C̄, C̄ = second-half candidate mean.

**Dynamic runs** (150k steps, engine seeds 77031/123457/888811 linked +
all 3 control KLINKF=0; mirror seeds 77031/123457 linked + 77031 ctl):

| run | lmean | nlmean | nlimean | C̄ (2nd half) | L* pred | sepmean | lifemean |
|---|---|---|---|---|---|---|---|
| eng77031 link | 67.90 | 14.42 | 14.42 | 150.9 | 15.27 | 2.65 | 66.44 |
| eng123457 link | 70.16 | 10.07 | 10.07 | 98.3 | 9.94 | 2.61 | 65.32 |
| eng888811 link | 64.99 | 6.45 | 6.45 | 67.9 | 6.87 | 3.04 | 65.82 |
| mir77031 link | 50.75 | 47.79 | 30.50 | 496.6* | 50.2 | 0.716 | 65.30 |
| mir123457 link | 49.61 | 41.83 | 27.14 | 431.3* | 43.6 | 0.783 | 64.94 |
| eng ctl ×3 | 68.1/68.2/68.2 | 0 | 0 | 26.4/18.1/8.0 | — | 2.96/3.55/3.11 | — |
| mir ctl 77031 | 52.64 | 0 | 0 | 8.6 (whole-run) | — | 3.49 | — |

*mirror candmean printout was the whole-run mean (a reporting patch was
lost mid-session); second-half C̄ recovered exactly from the birth
identity C̄ = births_sh/(k_b·75000) — which is itself the mean-field
relation, so the recovery is self-checking.

### Target 1 — link-count steady state ✓
L̄ vs mean-field prediction per run: engine 14.42/10.07/6.45 vs
15.27/9.94/6.87 (within 6%); mirror 47.79/41.83 vs 50.2/43.6 (within
5%). Engine second-half birth identity: births = p_b·ΣC̄ within 0.4–0.7%
(three seeds). ALL links are inter-filament in linked runs (nli=nlink);
controls have zero.

### Target 2 — mechanical effect ✓
Inter-filament attachment: frac(2nd half with ≥1 inter link) =
0.67/0.88/0.63 (engine; 0 in controls); bundle episodes (nli≥10) reach
nlink 15–46 with sep → 0.71–1.85 and transient al → 0.94–1.00
(registered bundle). Candidate supply C̄ = 68–151 linked vs 8–26
control (4–7×): links hold filaments in each other's birth zone
(positive feedback). sepmean linked 2.61–3.04 vs control 2.96–3.55.
Bundle is BISTABLE: eng77031 locked ~118–143k (nlink 34–46, sep 0.71)
then dissolved (nlink → 1); both mirror runs locked for the entire
second half. Locked-state stats: engine nlink 34.4/sep 1.0/C̄ 359
(seed 77031) vs mirror 30.5/sep 0.72/C̄ 370-500 — same state; the
mixing fraction differs (finite-run sampling of a bistable switch).
Note: the locked bundle is a tight CONTACT aggregate of two intrinsically
coiled filaments (ee/contour ≈ 0.2), not a globally aligned rod bundle —
the ladder bending stiffness sets that, and it is off-limits.

### Target 3 — turnover ✓
births ≈ deaths at steady state (engine: 20494/20475, 14529/14505,
11035/11006; mirror: 82414/82259, 66784/66645; strips 1–93 counted
separately). Mean lifetime 64.9–66.4 vs nominal 66.7 (within 2.1%).
Engine/mirror lifetime agreement: 66.44/65.32/65.82 vs 65.30/64.94 —
within 1%.

### Engine/mirror agreement
- Rates, lifetimes, mean-field relation L̄ = r·C̄: within a few %, both
  sides, all seeds → the link kinetics are the same process.
- lmean: engine 67.7±1.5 vs mirror 50.2±0.6: differs (M4a also had
  engine > mirror; here amplified by the coiled two-seed growth
  dynamics — chaotic trajectory divergence, documented in M4a as the
  expected mode).
- Raw nlmean differs by bistable state selection (above): engine mixes
  locked/dissolved within 150k, mirror locked early. Locked-state
  conditioned statistics agree to ~30% (nlink 34 vs 30, C̄ 359 vs
  370-500). Deviation documented, mechanism identified.

### The big catch (oracle ladder working as intended)
First campaign (27-stencil, RLINK=1.0): mirror locked into persistent
bundles (nlmean ~45), engine never locked (nlmean ~9) — >3σ
disagreement. Root cause: pairs with cell-diff 2 (|dx| ∈ (0.75,1.0])
are invisible to the 27-cell stencil but present in the mirror's full
matrix → engine candidate starvation (~30% fewer candidate-pair-steps
in bundled states). Fixed with the 98-offset far-cell candidate pass
(engine) — the complete-set rule both sides. Post-fix engine locks and
dissolves exactly like the mirror. (An RLINK≤0.75-only fix was also
tested and rejected: gap-1.5 filaments then never touch — no bundle.)

## Overgrowth / kT note
Both linked and control runs overgrow the nominal ODE plateau
(bound ≈ 65-70 vs naive 24): two nearby barbed windows recapture each
other's released monomers (release-park at 1.65 is inside the partner's
capture window when close/coiled) — implied k_off_eff ≈ 0.3×nominal per
filament. Same in no-link controls → not a crosslink effect. kT mean
0.42–0.54 (mirror 0.40–0.43), spikes ~1.0, identical with and without
links — inherited from the M4a growth dynamics at this density
(M4a single-filament range 0.36–0.50).

## Calibration failure modes fixed (for the record)
1. Preload-then-measure reset the step counter → negative link
   "lifetimes" (−311 steps!). Fixed: single continuous steady-state run.
2. Deaths-off birth calibration saturates MAXL → births stop while
   candidates keep counting → 50× low rate. Fixed: eligibility
   normalization (candidates counted only when a slot is free).
3. First draw cap MAXCB=280 < ncand~309 in dense bundles → silent birth
   throttling. Fixed: MAXCB=600 + NCSKIP counter (=0 in final runs).
4. A mirror anchor-index bug passed FD (self-consistent) — caught only
   by the static byte cert.

## What I'd do differently
- Check cell-stencil coverage against RLINK analytically BEFORE running
  dynamics (the diff-2 gap is a one-line argument); the dynamic
  engine/mirror comparison caught it, but a campaign was invalidated.
- The mean-axis alignment `al` is a poor order parameter for coiled
  filaments; a local pairwise a_i·a_j over contacting monomers would be
  sharper. Keep for v2.
- Verify every edit_file application with grep in this environment —
  three parallel-applied edits were silently dropped and each cost a
  debugging cycle (one caused a full memory-corruption blowup via
  NMAX/NB mismatch).
