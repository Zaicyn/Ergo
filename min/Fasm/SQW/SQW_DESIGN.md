# SQW — write-skip / memoized duplex cell (molecular recognition)

2026-08-27. User prompt: "one with write skip? Basically memoization.
If the data exists, don't touch it." SQW is SQ2B plus a recognition
layer that decides — before any synthesis — whether the incoming item
is already physically present, and if so touches nothing but a
refcount.
Files: `sqw_core.h` (the cell), `bench_sqw.c` (duplication sweep),
`sqw_cert.c` (certification driver).

## 1. The design question

SQ2B's duplex proofread commit costs ~336 ns/item whether the data is
new or not. Biological systems face the same economics and solve it
with *recognition*: an enzyme doesn't rebuild a substrate it already
holds. SQW asks: can a content-recognition layer skip the entire
write, what does the skip cost when it misses, and what does
physically sharing one copy do to the integrity story?

The answer is workload-conditional — which is exactly why the doc
exists: memoization is a trade, not a free win.

## 2. Mechanism

```
alloc(id, item, data):
    h  = word-wise hash(data)                # ~19 dependent ops
    e  = idx[h % 4096]                       # direct-mapped cache
    if e.used && e.h == h
       && !tombstoned(e.slot)
       && memcmp(strand0(e.slot), data) == 0:   # EXACT byte verify
        ref_inc(e.slot)                      # paired refcount ++
        skips++ ; return                     # nothing else touched
    slot = sqb_alloc_slot(...)               # full SQ2B proofread commit
    idx[h % 4096] = {h, slot, used}          # insert (may evict)
```

Three load-bearing decisions:

1. **Verify is byte-exact, always.** The hash is only a hint; the
   skip is gated on a full 152-byte memcmp against strand 0 plus a
   tombstone check. Consequence: the cache is *fail-safe by
   construction*. A poisoned/evicted/collided cache entry can only
   cause a missed skip (we re-allocate and re-store correct data),
   never wrong content. Certified: O7, 428/428 under deliberate
   cache-poisoning injection, zero wrong-skip events.

2. **Refcounts are complement-paired** (`lo | ~lo<<16`). Any
   single-event hit to a refcount word breaks the pair and is
   detected per-slot at audit. But: without a logical→physical map,
   a broken refcount is *detected, not repairable* — we know it's
   wrong, not what it should be. This is documented as an
   unrepairable-detected class, the same honesty category as SQ5's
   anomaly class.

3. **The hash is on the hot path — treat it that way.** First
   version used byte-serial FNV over 152 bytes: 152 dependent
   multiply links ≈ 250 ns, which made SQW *slower than SQ2B at 77%
   skip rate* — the whole point of the design eaten by one serial
   chain. This is the CRC32C lesson from the ESF campaign recurring
   in a new place. Replaced with a word-wise mix (8 bytes per step,
   19 links + finalizer). Rule written down: if you memoize, your
   recognition hash is part of your critical path; latency, not
   throughput, is the metric.

## 3. Measured duplication sweep

vs SQ2B's flat ~335 ns/item on identical content:

| duplication | skip rate | ns/item | vs SQ2B |
|---|---|---|---|
| 0% | 0% | ~410–470 | **slower** — recognition tax, no benefit |
| 50% | 49% | ~270 | 0.80× |
| 90% | 86% | ~158 | 0.47× |
| 99% | 99% | ~122 | 0.36× |

Skip path alone ≈ 75 ns (hash + verify). **Crossover ≈ 30–40%
duplication.** Below that, recognition is a pure tax and the layer
should be compiled out. Sweep cost also collapses with occupancy
(1.7 µs at 99% dedup vs ~70 µs full) — fewer physical codons to
patrol.

## 4. The integrity cost: concentration, not weakness

Dedup means N logical items share M < N physical codons. Nothing
about detection or repair per-codon degrades — but the *same event
rate* now lands on fewer targets, and each hit carries a bigger
blast radius. Measured under the identical 12-events/round poisson
protocol:

- repair 96.7% vs SQ2B's 98.3%
- tombstones 83 vs 48
- **~1.9 logical items lost per tombstone** (tomb_refs / tombs) —
  one physical apoptosis kills every logical item that recognized
  itself into that slot.

This is the honest price sheet: memoization trades physical
redundancy for write avoidance, and redundancy *was* part of the
integrity budget. Documented, quantified, not hidden.

## 5. Certification (pre-registered oracles, byte-deterministic)

```
SQWOR O1_recognition_exact   exact-U stream, 0 false skip, 0 false alloc
SQWOR O2_refpair_det         refcount corruption detected per-slot
SQWOR O3_payload_det/rep     1.000000 / 1.000000  isolated [A]
SQWOR O4_syndrome_det/rep    1.000000 / 1.000000  isolated [A]
SQWOR O5_closure             0 unresolved
SQWOR O6_apoptosis           0 in isolated phase
SQWOR O7_cache_failsafe      428/428 poisoned-cache → missed skip only [A]
SQWOR auxB_amplification     1.9 logical items lost per tombstone
```

Two harness-class artifacts were caught during certification and are
recorded so the canary protocol stays trustworthy:

- **Events on unoccupied slots.** Early runs targeted random
  (bin, gen) pairs; dedup leaves ~half the physical space
  unallocated, and corrupting unallocated space is not an integrity
  event — it inflated misses to ~50% det. Events now target the
  occupied list only.
- **Mixed-round contamination.** O7's fail-safe oracle was polluted
  by co-occurring payload events in poisson rounds (verify failures
  for legitimate reasons). O7 is scored in the isolated phase only.

## 6. When to use it

- Workload has ≥ ~40% duplication → SQW, large win, integrity cost
  is the concentration factor above.
- Unique-dominated stream → SQ2B (or SQM); the recognition layer is
  a tax with nothing to pay for.
- Never present the skip as free integrity: the refcount is
  detected-unrepairable, and the tombstone blast radius grows with
  the dedup ratio. Both numbers are measured, per workload, before
  deployment claims.
