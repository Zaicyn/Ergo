# HashKit — deterministic hashing tools (shared)

Two tools live here. Both are debug/analysis kit, not allocator
hot paths (no allocator hashes at runtime; see below).

## det_harness (counter-mode RNG)

`det_harness.asm` (+ `.c` mirror): splitmix64-Stafford pure functions
with Ergo HASH/RAND top-31/top-53 semantics. Counter-mode event
streams for failure analysis: event `k` recomputable from `(seed, k)`
with no replay. Digests match the C mirror; deterministic.

## House integrity hash: splitmix-stream

Measured decision (Secure campaign, `../Secure/hashshoot.asm`,
2026-09-13 — FNV-1a 64 vs splitmix-stream vs ad-hoc control on
4 KB frames, C mirror-clean):

| hash | ns/4 KB | avalanche mean | spread |
|---|---|---|---|
| splitmix-stream | 1680 (0.41 ns/B) | 32.02 | 16–49 |
| FNV-1a 64 | 4162 (1.02 ns/B) | 30.71 (real bias) | 7–48 |
| ad-hoc shift-xor | 399 | 1.68 (blind) | 0–4 |

Construction: `h = mix(h XOR block)` per u64 block, Stafford
finalizer as the compression function, IV 0. Use this for all new
integrity hashing (frame fingerprints, audit digests, torusecc).
Keep FNV-1a 64 as the canonical cross-context fallback
(CPU/GPU agreement — Hash Strengthening proposal Trigger 3).

## Why no allocator changes

Checked 2026-09-13: the fleet's only hash is SQW's `sqw_hash`,
called once per alloc (cold). Everything else uses xoshiro256**
(RNG — different job, keep) or moment syndromes (keep). The
splitmix win applies to new code only: no oracle churn, no C
mirrors to update.
