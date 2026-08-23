# .esf slot pool — v4 squaragon as the frame/buffer pool manager (sketch)

Status: D4 sketch only — design, no runtime integration. The arena
stays bump-only (`Spec/Arena_Lowering_Brief.md` unchanged); this pool
is a *separate, fixed-size* service for stream frames, not a general
allocator.

## Claim

An `.esf` writer that buffers frames (e.g. a future batched or
multi-producer mode) needs a pool of 4096-byte frame slots with:
O(1) claim/release, bounded claim→use skew across producer channels,
and a cheap live-integrity check over the pool. The v4 squaragon
(`allocator/sq4core.f`, `tests/sq4core.ergo`; audit in
`allocator/TUNING_FINDINGS.md`) is exactly that shape:

- **slots** = the v4 8-bin × 32-ring torus (256 slots per pool
  instance; two instances = the 512-slot fill the v4 thresholds are
  calibrated for after Fix 1);
- **claim** = `SQ4ALC`: the next slot comes from the SCATLT scatter
  sequence — the *same* LUT the `.esf` channel schedule uses, so
  buffer reuse order and stream interleave share one geometry
  (bounded inter-arrival skew, measured in `tests/stream/` test 2:
  max gap ≤ 30 for 8 channels, bound 32);
- **release** = slot return to its bin's free ring;
- **pool integrity** = `SQ4RES`, the 3-axis residual with the
  provable floor `sqrt(3)*|d|/scale` for any corruption direction —
  the same pattern `.esf` frames carry per-frame in bytes
  (`Spec/Ergo_Stream_Format.md` §3);
- **pressure** = the v4 zone thresholds (ACTIVE / OVERDRIVE / DIVIDE,
  all reachable after Fix 1) map to pool watermark policy: ACTIVE =
  steady, OVERDRIVE = producer throttle / flush early, DIVIDE =
  split the stream (roll to a fresh `.esf` segment).

## Sketch API (runtime service, C, beside ergo_stream.h)

```
pool = esf_pool_open(nslots)          ! 256 or 512 (two tori)
s    = esf_pool_claim(pool)           ! O(1), SCATLT order
... fill frame s (esf layout) ...
esf_pool_commit(pool, s)              ! frame becomes drainable
esf_pool_release(pool, s)             ! after fwrite
zone = esf_pool_zone(pool)            ! ACTIVE/OVERDRIVE/DIVIDE
bad  = esf_pool_audit(pool)           ! SQ4RES-style residual, 0 = clean
```

Determinism: fixed slot counts, scatter-ordered claims, no
timestamps — the pool's state after N operations is a function of
the operation sequence only (the v4 cross-port audit already
demonstrates bit-exact F77/Ergo/Python agreement on exactly this
state machine, including the 512-slot TINVAR dump).

## What this is NOT / what is deferred

- Not integrated: the current `.esf` writer is eager (one fwrite per
  frame, no pool). The pool is the service for a future buffered
  mode; landing it wants a measured need, not anticipation.
- Not a replacement for the arena: ALLOCATABLE stays bump-only.
- The v4 audit's open caveats apply: the LUT's worst-case separation
  (1.6875) is the 8-bin family ceiling, and the design reads as
  max-min tuned, not energy tuned (L2/L3a). For a *schedule* (not a
  collision problem) max-min is the right objective — stated here so
  the choice is auditable.
- Zone thresholds need re-derivation for frame semantics (a "full"
  pool of 4096-byte slots is a memory budget question); the sketch
  keeps the v4 numbers as placeholders until the buffered mode
  exists to measure against.
