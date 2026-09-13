# PHASE MAP — where each architecture is necessary (data sense)

Not a biological map: a decision map over workload × requirement,
measured on the reflex testbed (`reflex.asm` + `.c`, N=200/cell,
mirror-clean). Columns per cell below are corr / apop / det / misc.

## Tiers and what they cost

| Tier | Structures | Syndrome words/frame | Repair compute |
|---|---|---|---|
| sense (9+0) | 9 doublets × S0 | 18 | none (never touches) |
| reflex (9+0 + dynein) | + S1, one SEC attempt, tombstone | 36 | 1 idiv-class op max per tubule |
| full (9+2 + central pair) | + S2/S3, gates, search, refuse | 80 | bounded search (131k pairs worst) |

18 = bare sensor states (9 channels × present/absent-ish readings).
80 = committable frame: same signal space + arbitration (duplex
1+1, uniqueness) + check words (S2/S3 gates). The 4.4× expansion
is nearly all redundancy/checks, not new signals — the central
pair is an arbitration line, not a data line.

## Measured matrix (source of the map)

k=1: all tiers corr=200 (sense: det=200), misc=0 everywhere.
k=2 spread: reflex 190/10/0/0, full 200/0/0/0.
k=2 clust: reflex 99/99/0/2, full 200/0/0/0.
k=3 spread: reflex 168/31/0/1, full 200/0/0/0.
k=3 clust: reflex 1/197/0/2, full 151/0/49/0.
k=4 spread: reflex 143/57/0/0, full 198/0/2/0.
k=4 clust: reflex 0/198/0/2, full 3/0/197/0.
k=6 spread: reflex 79/119/0/2, full 187/0/13/0.
k=6 clust: reflex 0/200/0/0, full 115/0/85/0.
k=8 spread: reflex 37/158/0/5, full 175/0/25/0.
k=8 clust: reflex 0/200/0/0, full 0/0/200/0.
sense: det=200, misc=0 in all 24 cells. Full misc=0 in all 24 cells.
Reflex misc total = 14 (cells k=2c,3s,3c,4c,6s,8s).

## The map: cheapest sufficient tier by requirement

1. **Detect only** (any k, either pattern): **sense**.
   Evidence: 4800/4800 detected, 0 missed, 18 words. Nothing
   cheaper exists; nothing more is needed.
2. **Repair, k=1** (any pattern): **reflex**.
   200/200 corr, 0 misc. Full ties on outcome at 2.2× the words.
3. **Repair with apoptosis tolerated, misc must be 0**:
   **reflex** where it stays clean (k=1 all; k=2 spread 190+10apop;
   k=4 spread 143+57apop), else full.
4. **Repair, zero misc, k ≥ 2 clustered or k ≥ 3**:
   **full**. Reflex miscorrects (2,1,2,2,2,5 across those cells)
   and collapses to apoptosis (k=3c: 1 corr; k≥4c: 0 corr).
5. **Repair maximally (most bytes back, silence required)**:
   **full** everywhere k ≥ 2 (full corr ≥ reflex corr in every row;
   e.g. k=6clust 115 vs 0, k=8s 175 vs 37).
6. **Containment only (never silently wrong, data loss OK)**:
   **reflex** suffices everywhere (worst case: tombstone all —
   k=6/8clust show 0/200/0/0 with 0 misc). Cheapest safe harbor.

## Necessity boundaries (where cheaper tiers provably fail)

- Reflex over sense: anywhere repair is required (sense repairs 0
  by construction). Boundary: k ≥ 1 + repair requirement.
- Full over reflex: (a) zero-misc requirement wherever reflex
  miscs (measured: k=2c,3s,3c,4c,6s,8s); (b) any-repair-at-all on
  clustered k ≥ 3 (reflex corr ∈ {1,0,0,0}); (c) full-repair on
  spread k ≥ 2 where apoptosis is intolerable (reflex apops
  10–158 per cell).
- Sense over nothing: never insufficient for detection (measured).
  The day sense misses (S0 collision), the floor moves — 0 such
  trials in 4800.

## Reading for the biology question

- Sensing is cheap and total: 18 words see everything. Antennae
  don't need motors — matches 9+0 primary cilia.
- Reflex (dynein, no central pair) buys speed + containment, not
  safety: 13 of 14 reflex miscs are accepted SECs the gates would
  have caught. A motor acting on antenna-grade information makes
  mistakes at ~0.3% on hard cells — affordable if apoptosis backs
  it (dead doublet > wrong doublet), fatal otherwise.
- The central pair buys safety + the hard tail: 14 → 0 misc,
  k=6clust 0 → 115 corr. Its words are checks, its compute is
  arbitration (uniqueness counting). Keep it wherever silent
  miscorrection is unacceptable; skip it where apoptosis is an
  acceptable answer (then reflex at half the words contains
  everything).
- Open edges (N=200 leaves these unmeasured): reflex misc=0 cells
  may misc at higher N (rate bounds, not zeros); exact k=2..3
  spread boundary for apop-intolerance; W-sizing measured
  (alignchk DONE 2026-09-14: re-align iff s <= W-4 at 200/200;
  shco fullok tracks s/W; s=500/W=512 unresolvable — 12 B TRUE
  window outscored by wrong offset).

## Reproduce

`reflex.asm` + `reflex.c` in this directory (mirror-clean,
deterministic). Matrix: k ∈ {1,2,3,4,6,8} × {spread, clust},
N=200, same draws through all three policies per trial
(snapshot/restore). TSV: `R <pol> k=<k> <pat> <corr> <apop>
<det> <misc>`, pol 0/1/2 = sense/reflex/full.
