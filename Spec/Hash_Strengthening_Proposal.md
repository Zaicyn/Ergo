# Hash Strengthening — Proposal

A small catalogue entry stashing the future-work direction for upgrading
Ergo's state-fingerprint hash when stronger guarantees become load-bearing.
Not a brief; not dispatched work. Same "thing to try when triggered"
shape as [Performance_Opportunities.md](Performance_Opportunities.md) and
[Invariant_Language_Feature.md](Invariant_Language_Feature.md).

## Current state

Two hashes exist in the repo, with different algorithms and different
domains of use:

**1. `ERGO_HASH_FINAL` (the GPU-side hash):**
[mcl/ir_codegen.py:160-170](../mcl/ir_codegen.py#L160-L170) — emits
textbook FNV-1a 64-bit into generated C. Seed `0xCBF29CE484222325`,
prime `0x100000001B3`, byte-wise `h ^= byte; h *= prime`. This is the
canonical algorithm and is correctly attributed. Used for galaxy-scale
particle state hashing in the determinism validation arc.

**2. The sq2core/sq3core inline hash (the CPU-side hash):**
[tests/sq2core.ergo:170-188](../tests/sq2core.ergo#L170), [tests/sq3core.ergo:253-271](../tests/sq3core.ergo#L253) —
ad-hoc XOR-of-shifts. Per-step mix is
`HASH := IEOR(ISHFT(HASH, 13), ISHFT(HASH, -19))`, seeded with
`166136261` (a constant adjacent to FNV-1a 32-bit offset basis but
not it). Adequate for regression detection on small allocator state;
not cryptographic, not proven full-period, not the canonical Marsaglia
xorshift32 family.

The CPU-side hash works for what it does. Its 32-bit state hashes ~1000
integer fields and produces a deterministic fingerprint across rebuilds
within a toolchain. Established baseline: `-1975039029` for the canonical
sq2core/sq3core test run.

## When this becomes worth changing

Four triggers, each independent. Any one of them would justify the
upgrade:

**Trigger 1: Collision-resistance becomes load-bearing.** The current
hash has ~32 bits of effective entropy and uses an unproven mixing
schedule. For small integer state (sq2core's 512 slots × a few fields)
collisions are very rare in practice, but the probability isn't
quantifiable without more analysis. If a future workload uses the hash
to detect *specific* state differences (e.g., "did slot 47 change in
this exact way"), the current hash's distributional weakness becomes
the bottleneck.

**Trigger 2: Cryptographic properties matter.** If the hash ever
becomes part of a security boundary — content addressing, commitment
schemes, signature material — the current ad-hoc mix is not acceptable.
Cryptographic hashes (BLAKE3, SHA-256) are the right tool there.

**Trigger 3: Cross-architecture hash agreement matters.** The current
hash is bit-exact within an architecture (both rebuilds on x86 produce
`-1975039029`). It would also be bit-exact on ARM and RISC-V because
the operations involved (IEOR, ISHFT) are well-defined across ISAs.
But if the hash ever gets compared *between* a CPU-side computation
and a GPU-side computation, the algorithmic difference (sq2core hash
on CPU vs FNV-1a 64-bit on GPU) means they can't agree by construction.
Unifying on FNV-1a 64-bit across both contexts would fix this.

**Trigger 4: Period properties become load-bearing.** If the hash is
ever fed back into itself as a PRNG (e.g., generating a sequence of
pseudo-random allocations for stress testing), the single-step XOR-of-
shifts has shorter period than Marsaglia xorshift32 and may produce
visible artifacts. A real Marsaglia xorshift32 would handle this with
its full-period 2^32-1 guarantee.

## Upgrade paths

Two candidates, picked based on which trigger fires:

**Path A: Unify on FNV-1a 64-bit.** Replace the sq2core/sq3core inline
hash with calls into the same `_ergo_fnv1a_update` helper that
ERGO_HASH_FINAL uses. Pros: one canonical hash across CPU and GPU
contexts, well-studied, larger state space (64-bit), correct attribution.
Cons: requires the helper to be available in the test harness's
generated C; baseline `-1975039029` becomes stale and the new baseline
needs to be re-recorded.

This is the right path for triggers 1, 3. Probably also the right
path for 2 if a quasi-cryptographic level of mixing is enough; if
true cryptographic strength is needed, BLAKE3 or SHA-256 instead.

**Path B: Canonical Marsaglia xorshift32.** Replace the single-step
mix with the three-step form:

```
HASH := IEOR(HASH, ISHFT(HASH, 13))
HASH := IEOR(HASH, ISHFT(HASH, -17))
HASH := IEOR(HASH, ISHFT(HASH, 5))
```

Pros: well-studied, proven full-period 2^32-1, invertible, still pure
integer ops. Cons: 32-bit state (smaller than FNV-1a 64-bit), still
not cryptographic, baseline changes.

This is the right path for trigger 4 (when PRNG-style usage matters)
and also a defensible alternative to Path A for triggers 1 and 3 if
you want to keep CPU-side state at 32 bits to match register width.

## What's also worth fixing alongside

Whichever path is chosen, two cleanup items should land at the same
time:

1. **The seed.** Replace `166136261` with the canonical seed for the
   chosen algorithm. For FNV-1a 64-bit, this is automatic (the helper
   already uses `14695981039346656037ULL`). For Marsaglia xorshift32,
   a defensible seed is the canonical non-zero starting state `2463534242`
   (which fits signed int32 as `-1831433054`) or any other documented
   xorshift seed from the literature.

2. **The comments.** Both sq2core and sq3core currently have warning
   comments pointing at this proposal. When the upgrade lands, those
   comments should be updated to reflect the new algorithm and remove
   the "ad-hoc, not Marsaglia, not FNV-1a" caveats.

## Migration impact

The baseline hash value `-1975039029` is referenced in several places:

- [tests/sq2core.ergo](../tests/sq2core.ergo) and
  [tests/sq3core.ergo](../tests/sq3core.ergo) themselves (as test
  expected output)
- Commit messages in the determinism arc (`9f42f62`, `5daa257`,
  `352e2a5`, several stage-1/2/3 commits)
- [Spec/Arena_Lowering_Brief.md](Arena_Lowering_Brief.md) (Test 1
  baseline reference)
- [Spec/x86_Determinism_Brief.md](x86_Determinism_Brief.md) (post-stage
  baselines)
- Various other briefs and analysis docs

An upgrade that changes the hash value means all of these references
become historical-rather-than-current. The migration shouldn't try to
hide this — the right move is to commit the algorithm change with the
new baseline clearly labeled, and treat the old `-1975039029` as the
canonical pre-upgrade value (the way `pre-determinism-arc` is the
canonical pre-merge tag).

If you ever do migrate, generate the new baseline as part of the
upgrade commit, update the test expectations, and add a one-line note
in the relevant briefs that the canonical hash changed at commit X.
Don't try to make the new hash equal the old hash via constant
manipulation — that would defeat the purpose.

## Recommendation

Until a concrete trigger fires, do nothing. The current hash is
adequate for its current use (regression detection across rebuilds).
The cleanup comments in sq2core/sq3core make the algorithm's actual
properties visible, so future readers won't be misled about what the
hash provides.

When a trigger fires, the choice between Path A (FNV-1a 64-bit) and
Path B (Marsaglia xorshift32) depends on which trigger. The decision
is straightforward enough that it doesn't need a brief — just pick
the algorithm matching the trigger and execute the migration.

This proposal exists mainly so the analysis isn't lost. If a future
implementer (or future-you) hits one of the triggers and starts asking
"what's the right hash here," this doc points at the answer without
requiring the analysis to be redone.
