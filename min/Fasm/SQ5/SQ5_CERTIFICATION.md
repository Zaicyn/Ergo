# SQ5 Certification — Wigner-pattern verification of the v5 counterflow allocator

2026-08-27. Companion to ALLOCATOR_COMPARISON.md. This document records
the four certification fixes applied to the SQ5 prototype, the real bug
they caught, the pre-registered oracle table with results, the measured
blindness boundary, and the overhead each fix introduces.

Files: `sq5_core.h` (shared core), `bench_sq5.c` (comparison row),
`sq5_cert.c` (certification driver), `sq5_mirror.py` (independent mirror).

---

## 1. The four fixes

### Fix 1 — independent mirror (engine-vs-mirror, df_radial2 pattern)
`sq5_mirror.py` regenerates the clean allocator state **from the
specification alone** (scatter LUT, stamp formula, payload fill, scalar
mod-2^32 moment journals — no C code shared), applies the dumped event
list, and recomputes flux / triangulation / SEC / stamp checks
independently. The engine (`sq5_cert.c`) dumps clean / corrupted /
repaired snapshots plus its per-bin decision log (`sq5_audit.txt`).
Four stage verdicts, all required diff = 0:

| stage | what it certifies | result |
|---|---|---|
| S1 clean | alloc simulation + **incremental SSE4.1 journal path vs Python scalar recompute** | diff 0 PASS |
| S2 corrupt | event-application semantics identical on both sides | diff 0 PASS |
| S3 decide | flux flags, classification, SEC positions, tiers, stamp flags — 8/8 bins | diff 0 PASS |
| S4 repair | final payload / stamps / journals | diff 0 PASS |

S1 is the money check: the SIMD journal (cvtepu8/mullo lane arithmetic)
is byte-exact against an independent scalar implementation.

### Fix 2 — full-range injection (the V22 [144,152) lesson)
Injection previously touched payload bytes only; journals (192 B) and
stamps (2 KB) were never corrupted. Now:
- comparison row: target byte drawn uniformly from the whole
  (pay | stamp | journal) space — natural footprint proportions;
- certification driver: stratified 70/15/15 to give the small check
  fields statistics.

Coverage forced two design completions (both were latent, untested
paths, exactly the canary class):
- **Stamp corruption** was a *true blind spot* — nothing checked
  stamps. Stamps are pure position metadata, exactly recomputable from
  coordinates (SQ4 semantics), so validation is recompute-and-compare:
  detection exact, repair free. Now checked every sweep.
- **Journal corruption** was previously handled only *by accident*
  (tier-2's journal rebuild). The third residual now does its real job:
  streams agree but stream-vs-journal residual nonzero ⇒ the **journal**
  is the broken element ⇒ resync (3 stores) instead of a bin-shell copy.
  Classification table (r0/r1 = stream-vs-journal per shell, rx =
  cross-shell):

  | flags | meaning | action |
  |---|---|---|
  | r0 only / r1 only | journal corrupt | resync journal |
  | r0+rx / r1+rx | payload corrupt | SEC → tier-2 |
  | r0+r1, no rx, ds equal | identical hit both shells | SEC each |
  | r0+r1, no rx, ds differ | both journals suspect | resync both |
  | r0+r1+rx | payload both shells | SEC each; tier-2 from the repaired shell |
  | rx only | anomaly (impossible via injection) | counted, 0 observed |

### Fix 3 — pre-registered oracle table
Counting oracles (exact by construction) are separated from measurement
oracles (must earn their numbers), and the tautological detection column
is gone: detection is now credited from actual per-bin flags and the
stamp badmap, per event. Results (1500 isolated rounds + 500 poisson
rounds, byte-identical across repeat runs):

```
SQ5OR O1_payload_det  900/900 = 1.000000  expect=1.000000 counting [A]   PASS
SQ5OR O2_stamp_det    300/300 = 1.000000  expect=1.000000 counting [A]   PASS
SQ5OR O3_journal_det  300/300 = 1.000000  expect=1.000000 counting [A]   PASS
SQ5OR O4_payload_rep  900/900 = 1.000000  expect>=0.990   measurement [A] PASS
SQ5OR O5_arbitration  300/300 = 1.000000  expect=1.000000 measurement [A] PASS
SQ5OR O6_coh_fail     0 slots [A]         expect=0                        PASS
SQ5OR O7_collision    2000/2000 blind; 31698 quads mapped  documented-exclusion
SQ5OR O8_mirror_diff  0                   expect=0 construction           PASS
SQ5OR auxB_det        6000/6000 = 1.000000  poisson tail (12 ev/round)
SQ5OR auxB_rep        5370/6000 = 0.895000  poisson tail (multi-hit DED limit)
SQ5OR auxB_coh_fail   473 slots  auxB_unresolved 588  auxB_anomalies 0
```

Phase A is the SEC/DED design point (1 event/round): all oracles exact.
Phase B (12 events/round ≈ 1.5 per 4 KB bin) deliberately stresses the
multi-hit tail: detection still 100% (every event opens a residual),
repair 89.5% — the failures are exactly the DED-limit configurations
(double-byte + same-bin cross-hits where no clean sibling exists), which
a three-moment scheme cannot fix *by design*. Reported, not hidden.
Byte-determinism: two full runs identical modulo the timing line (O9).

### Fix 4 — collision mapping (the negativity-budget exclusion, mapped)
The algebraic blindness class is now measured, not just named. A
3rd-difference quad at consecutive linear byte positions with deltas
(d, −3d, 3d, −d) preserves s0, s1 AND s2 exactly (the 4th finite
difference of a quadratic vanishes). Because **all three residuals —
both counterflow streams and the cross-shell flux — are built from the
same three moments**, such a collision is invisible to the *entire*
instrument, arbitration included. Empirical: 31,698 realizable quads in
one cell fill (~62 per bin-shell, deltas d ≤ 8); 2,000 applied, 2,000
blind (flags == 0 every time), 100.0% as predicted.

**Honest consequence:** the counterflow adds *arbitration* (which
element is broken), not *wider detection*. Widening detection past the
moment-collision class requires a nonlinear check (CRC/hash) per bin —
the exact serial-chain cost the design exists to avoid. This is the
documented exclusion boundary, same status as "negativity budget is not
a stable grid observable" in the Wigner spec.

## 2. The real bug the ladder caught

The prototype's SEC repaired content correctly but then **added ds to
the journal** ("journal += ds closes the flux"). Since ds =
corrupt_stream − journal and the restored content already equals the
original journal, this left the journal desynced by exactly ds — every
SEC repair silently poisoned the journal for the *next* sweep. The old
harness scored payload patterns only and never re-checked flux closure,
so det/rep showed 100/100 while the journal drifted. The closure oracle
(O6/unresolved) caught it on the first certification run (unresolved =
3 per flagged bin). Fixed in `sq5_core.h:sq5_try_sec` — the journal is
now untouched by SEC. In your canary framing: this one was not planted;
it was mine, and the mirror-first ladder is what caught it.

## 3. Overhead of the four fixes

Measured on the same injected state, full validation vs legacy
(old semantics, no rx, no stamp check, no closure verify):

| fix | where the cost lands | measured |
|---|---|---|
| 1. Mirror | offline only | audit dump ~200 KB text (~1 ms); mirror 0.09 s; **hot path 0** |
| 2. Coverage + triangulation | validate sweep only | full 16.6 µs vs legacy 14.4 µs per full-cell sweep (isolated), 26.8 vs 24.5 µs (poisson): **+2.1–2.3 µs/sweep (+9–15%)** for rx residual + stamp check + closure verify + journal resync path |
| 3. Oracle table | stdout only | zero |
| 4. Collision mapping | offline analysis | one scan of 2×8×2045 quad positions per fill; **hot path 0** |

Allocator hot path (alloc + incremental journal + stamp) is **untouched
by all four fixes** — comparison-row ns/item moved 31.6 → 46.1 between
sessions, but every ESF row moved proportionally (batch_repair 29.4 →
51.0), i.e. host drift, not the fixes. Drift-controlled: SQ5 runs at
**0.90× the ESF_v2_batch_repair row** this session (was 1.07×), with
bin-granularity repair instead of 256 KB frame amortization. The
validate sweep itself is 13.3 µs detect + 4.3 µs repair per full-cell
sweep (SQ5T line) — a periodic cost the application schedules, not a
per-alloc cost.

## 4. What is NOT yet certified

- **Multi-hit repair beyond DED** is a design limit (O auxB), not a bug.
- **Collision blindness** is mapped (O7) but unmitigated — accepted
  exclusion; a nonlinear per-bin check would be a v6 decision.
- The mirror certifies *construction*, not workload realism: corruption
  here is random-byte XOR; bursty or adversarial (collision-seeking)
  corruption belongs in a follow-on campaign.
- Cert runs at NB=8/NR=32/PAY=64 only; the mirror is parameterized and
  the alternate-geometry rows should be re-certified if those configs
  matter.
