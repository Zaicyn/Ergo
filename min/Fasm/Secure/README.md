# Secure — file integrity on torus geometry (ESF campaign)

Goal: (A) multi-bit correction using the torus layout, (B) measured
choice of hash for this use. Specs: `Spec/Ergo_Stream_Format.md` (ESF2
frames + single-byte syndrome repair), `Spec/ESF_Slot_Pool_Brief.md`
(v4 squaragon as frame pool), `Spec/Hash_Strengthening_Proposal.md`
(FNV-1a 64 vs xorshift paths).

## Key observation: the math already exists in-tree

ESF §3's `(S0, S1, S2) = (Σb, Σb·idx, Σb·idx²)` with single-byte repair
(`d = ΔS0`, `p = ΔS1/d` exact division, S2 gate, re-verify) is the same
object as SQ5's flux triple (`s0/s1/s2` per bin-shell) and SQ5's
`sq5_try_sec` (`d = ds0`, `p = ds1/d`, `expect2 == ds2` gate).
Multi-bit correction is therefore a composition problem, not a new
primitive: more equations from more geometry.

## A. Multi-bit correction capacity (torus layout)

One frame with 3 global syndromes repairs exactly 1 byte (ESF §3
proof: no wrap since `|d·p| < 2^32`, uniqueness exact). The torus
adds independent equation sets:

1. **Bin partition (8 bins):** per-bin triples (sq5 flux does this
   today) make each bin independently single-byte-repairable → up to
   8 correctable bytes per frame-group when spread ≤ 1 per bin.
2. **Duplex shells (2 views):** 6 equations per bin solve same-bin
   2-byte errors (4 unknowns `d1,p1,d2,p2` + 2 gates); shell
   disagreement alone is a free detector (`duplex_mismatch` pattern
   from Sq2B/SQW).
3. **Journal reference (sq5 `jr`):** stored per-bin moments turn
   detection into O(1) residual checks per bin (rescan only to repair).
4. **Product layer (optional):** column moments across bins locate
   errors at row×column intersections when bin-local solve is
   ambiguous (clustered multi-byte).

Capacity summary: 1-byte anywhere (proven); up to 8-byte spread
(1/bin); 2-byte same-bin via duplex; beyond that detection-only.
Every repair stays gated + re-verified, so the miscorrection floor
≈ 2^−32 per attempt is preserved (same argument as ESF §3).

Geometry note (exact, no padding): one SQ5 bin = 32 gens × 2 shells
× 64 B = 4096 B = one ESF frame. So frame `k` ↔ bin `k mod 8`,
slots within the bin = 64 chunks of 64 B, shells = dual views.
Index bases differ today (ESF 1-based over 4080 region vs flux
`g*64+i+1`) — align on one convention in the prototype. ESF stores
S-words in-frame; the torus keeps journals separately — keep both,
compare cost.

## B. Hash choice for this use

Contenders: FNV-1a 64 (proposal Path A, canonical, GPU-side uses it),
splitmix64-block-stream (HashKit extension, Stafford finalizer =
designed avalanche), ad-hoc XOR-shift (control, expected to lose).
xoshiro256** is a PRNG, not a hash — excluded except as control.

Metrics (all measured, none promised): (1) avalanche — flip sampled
input bits, mean output Hamming distance (want ≈ 32) + distribution;
(2) speed — ns/byte on 4 KB frames; (3) detection — N random
multi-byte corruptions all detected (expect 100% everywhere; the
differentiator is (1)+(2)). Prediction: splitmix wins avalanche,
FNV-1a wins simplicity/canonicity — report both margins, recommend
by measurement.

## Allocator roles for this test

| Role | Allocator | Reason |
|---|---|---|
| Syndrome/repair engine | SQ5 | bin×shell triples + journals + SEC/tier2/resync tiers already exist; flux just vectorized 5.9× |
| Frame pool | SQ4 | slot-pool brief names v4 squaragon literally; SCATLT claim order = ESF schedule geometry; zone watermarks |
| Duplex redundancy pattern | Sq2B / SQW | two-shell views, transcribe/pay_ok verify shapes (reference only) |
| Hash candidates | HashKit + new FNV-1a 64 | shootout (B) |
| Audit/log | trit / RLE / int_codec + emit | poison records, repair logs |

Out of scope: V8 (fold checksums don't fit frame semantics), V22
(superseded), SQM/SQFH (moment/float machinery not needed here).

## Prototype plan

1. `hashshoot` (B, ~1 session, self-contained): FNV-1a 64 (new impl)
   vs splitmix-stream vs ad-hoc on 4 KB frames — avalanche histogram
   + GB/s + detection trial. Uses `hash_rng.inc`.
2. `torusecc` (A, bigger): 8-bin frame model with per-bin S0/S1/S2 +
   dual shells; inject k = 1,2,3,4,6,8 byte errors, spread vs
   clustered, N trials each; repair via bin-local SEC + duplex
   2-byte solve; report correction rate vs k/pattern + miscorrections
   (expect 0).

## hashshoot results (DONE 2026-09-13)

`hashshoot.asm` (+ `hashshoot.c` mirror): 4 KB frames, full 32768-bit
avalanche, best-of-5 ns/frame over 5000 iters, 2000-trial 2–8 byte
detection. C mirror-clean (digests + avalanche + detection match),
deterministic across runs.

| hash | digest | ns/4 KB | aval mean | min–max | miss/2000 |
|---|---|---|---|---|---|
| FNV-1a 64 | ef98fd1c3b78d3d9 | 4162 | 30.71 | 7–48 | 0 |
| splitmix-stream | 25c6260cb17903ef | 1680 | 32.02 | 16–49 | 0 |
| ad-hoc | 76ca09756b57a177 | 399 | 1.68 | 0–4 | 0 |

Verdict: splitmix-stream wins on both axes — avalanche 32.02 with a
tight binomial-like spread vs FNV-1a's 30.71 (real bias, ~60σ) and
weak-bit tail (min 7); 2.5× faster (0.41 vs 1.02 ns/B). Ad-hoc is
disqualified (mean 1.68: single-bit flips nearly invisible). All
three detect 2000/2000 multi-byte corruptions — detection is not the
differentiator at this size. Recommendation: splitmix-stream for the
integrity hash; keep FNV-1a as the canonical cross-context fallback
(proposal Trigger 3: CPU/GPU agreement).
