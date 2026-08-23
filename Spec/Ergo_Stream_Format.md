# Ergo Stream Format (.esf) — framed, multiplexed, self-checking

Status: approved design (data-flow campaign, deliverable D2).
Implementation: `core/runtime/ergo_stream.h`. Language surface:
Spec/Ergo_Spec.md Part 10. Tests: `tests/stream/`.

An `.esf` file is a sequence of **fixed-size 4096-byte frames**. One
file carries up to 8 logical **channels**; the channel each frame
belongs to is assigned by a scatter schedule (below), not by the
writer's whim. Every frame carries an integrity residual. The reader
side (a Python reference reader lives in `tests/stream/`) can verify
a frame standalone: header fields, schedule position, and residual
are all computed, never searched.

Design lineage: the channel interleave is the Viviani scatter
permutation from the v4 squaragon allocator
(`allocator/TUNING_FINDINGS.md` Fix 1, baked from
`sq2_viviani_scatter_full(id, total=52)` at HOPFQ=1.97, float32); the
integrity words carry the v4 Fix-2 lesson (a residual with a provable
detection floor and no blind directions) into a weighted-syndrome
scheme that additionally *locates* single-byte damage (§3).

## 1. Frame layout

All integer header fields are **little-endian**, fixed width.

| offset | size | field |
|---|---|---|
| 0 | 4 | magic: ASCII `ESF2` (0x32 0x46 0x53 0x45 little-endian) |
| 4 | 4 | frame index `k` (uint32, 0-based, strictly +1 per frame) |
| 8 | 2 | channel `c` (uint16, 0..C-1) |
| 10 | 2 | payload length `L` in bytes (uint16, 0..4068) |
| 12 | 4 | per-channel sequence number (uint32, 0-based per channel) |
| 16 | 4 | integrity `S0` (uint32) |
| 20 | 4 | integrity `S1` (uint32) |
| 24 | 4 | integrity `S2` (uint32) |
| 28 | 4068 | payload region (`L` bytes used, rest zero-filled) |

`28 + 4068 = 4096` exactly.

## 2. Scatter-scheduled interleave

The number of channels `C` is fixed at `ESF_OPEN` (1..8 — the
geometry is the Viviani 5D modulus-8 scatter; more channels are a
named error). The channel carried by frame `k` is:

```
ch(k) = SCATLT[k mod 32] mod C
SCATLT = (6 5 4 0 2 3 4 7 4 6 3 0 1 2 1 0
          3 6 4 7 4 3 2 0 4 5 6 5 4 0 2 3)    ! the v4 bake
```

For `C = 8` this is the v4 allocator scatter sequence verbatim (the
`mod C` is the identity). The generator behind the LUT — derived, not
tuned — is `sq2_viviani_scatter_full(id, 52)` at HOPFQ=1.97
(`Testing/V22/squaragon_v2.h`), certified by cross-port audit
(F77/Ergo/C/Python agree exactly, `allocator/TUNING_FINDINGS.md` L1).

**Direct addressing:** `ch(k)` is computed from the frame index, so
the reader knows the expected channel of every frame position without
scanning; a frame whose channel field disagrees with `ch(k)` is
corrupt by construction.

**Skew bound:** the schedule has period 32 and every bin `0..7`
appears in SCATLT (that was the v4 Fix-1 property — the old 6-bin
LUT left bins dead). Therefore for `C = 8` every channel arrives at
least twice per 32-frame period and the per-channel inter-arrival
gap is strictly bounded by the period; per-channel max gaps are
*measured* in `tests/stream/` (for all `C` in 1..8) and reported
against this bound — the test asserts gap < 32 and reports the
measured value. For `C < 8` the `mod C` fold only shortens gaps
(every channel of `0..C-1` still appears, since bins `0..7` all
appear).

**Writer discipline:** the program serves channels in schedule
order. `ESF_NEXT(unit)` returns `ch(k)` for the next frame; the
program posts that channel's next payload with `ESF_WRITE`. Posting
a channel other than the scheduled one is a named runtime error
(`ERGO-ESF: channel out of schedule`). This keeps the stream
program-ordered and deterministic with no hidden buffering: one
`ESF_WRITE` = one frame = one `fwrite` of 4096 bytes; the flush
points are exactly `ESF_CLOSE` and program end.

## 3. Integrity residual (ESF2: weighted syndromes → repair)

ESF2 replaces the ESF1 mod-3 class sums with three **weighted
syndromes** over a fixed summed region — offsets `[4,16) ∪
[28,4096)` — that does NOT depend on the (corruptible) length field:
the payload region is summed to its full 4068 bytes regardless of `L`
(zero-fill bytes are 0 and contribute nothing, so the writer's sums
equal the reader's whether computed to `L` or to 4068; summing to
4068 also closes the ESF1 zero-fill blind spot — every byte in
`[4,4096)` is now covered).

Each covered byte carries a contiguous **index** (1-based by design —
see the ambiguity note):

```
idx(o) = o - 3          for o in [4,16)      -> idx 1..12   (header)
idx(o) = o - 15         for o in [28,4096)   -> idx 13..4080 (payload)
S0 = Σ b·idx^0,  S1 = Σ b·idx,  S2 = Σ b·idx²     (all mod 2^32)
```

**Detection floor (preserved):** any single-byte change `d`
(`d ∈ ±[1,255]`) at index `p` moves S0 by exactly `d ≠ 0` — the ESF1
floor `|d| ≥ 1` is preserved, now with zero-fill included.

**Repair (single-byte):** with Δ = computed − stored (mod 2^32):

1. `d = ΔS0`, interpreted signed: valid only if `ΔS0 ∈ [1,255]`
   (`d = ΔS0`) or `ΔS0 ∈ [2^32−255, 2^32−1]` (`d = ΔS0 − 2^32`);
   anything else cannot be a single byte → refuse.
2. Position: the unique `p ∈ [1,4080]` with `d·p ≡ ΔS1 (mod 2^32)`.
   **Uniqueness is exact, not probabilistic:** `d·p₁ ≡ d·p₂` implies
   `d·(p₁−p₂) ≡ 0`, but `|d·(p₁−p₂)| ≤ 255·4079 = 1,040,145 < 2^32`
   and nonzero, so `p₁ = p₂`. Since `|d·p| ≤ 255·4080 < 2^32` there is
   no wrap, so `p` is recovered by plain integer division
   (`ΔS1 / d`, divisibility checked) — no modular inverse, no search.
3. **Consistency gate:** accept the repair only if `d·p² ≡ ΔS2
   (mod 2^32)`; then subtract `d` from the byte at `p` (mod 256) and
   re-verify that all three recomputed syndromes equal the stored
   words exactly. Any failure → refuse (the corruption is still
   *detected* and reported; only repair is refused).

**Why idx starts at 1 (the ambiguity that is designed out):** the
stored integrity words (offsets 16..27) are outside the summed
region. A flip of S0's low byte produces `Δ = (−δ, 0, 0)`; with an
idx-0 position that would be indistinguishable from a data flip at
idx 0 — a silent-miscorrection channel. With idx ≥ 1 the equation
`d·p ≡ 0` has no solution (`|d·p| ∈ [1, 1,040,145]`, nonzero and
`< 2^32`), so integrity-word corruption is detected and refused,
never miscorrected. Flips of the S1/S2 words give `ΔS0 = 0`, i.e.
`d = 0`, likewise refused.

**Miscorrection bound (multi-byte):** a k-byte corruption is
miscorrected only if its syndrome vector satisfies all three
single-byte equations. The S0/S1 pair fixes `(d, p)` with no modular
freedom (no wrap in range), leaving one 32-bit modular equation (S2)
to hold by chance: probability ≈ 2^−32 per random corruption
(a 2-byte corruption needs `d₁d₂(p₁−p₂)² ≡ 0 (mod 2^32)`-type
alignment). Measured over 1000 random region flips in
`tests/stream/` — observed 0; the suite asserts it.

The residual is an *integrity* check, not a cryptographic hash: it
detects (and now repairs single-byte) corruption; it does not
authenticate.

## 4. Reader algorithm (reference)

For each 4096-byte frame at file offset `k*4096`:

1. Magic must be `ESF2` (equality; the magic is outside the summed
   region — detected, not repairable).
2. Recompute `S0,S1,S2` over the fixed region `[4,16) ∪ [28,4096)`
   and compare to the stored words. On mismatch, attempt the §3
   single-byte repair (signed-`d` range check, exact position solve,
   S2 consistency gate, re-verify after the fix). Refusal = corrupt
   frame, reported; the frame is never silently miscorrected.
3. On the (repaired) frame: `k` field must equal the frame ordinal;
   `c` must equal `SCATLT[k mod 32] mod C`; `L <= 4068`; the channel
   sequence must be the count of earlier frames on channel `c`.
4. Payload = bytes `[28, 28+L)`, appended to channel `c`'s stream.

A file whose length is not a multiple of 4096 is truncated/corrupt.
`C` is recoverable from the first frame's context by the reader
contract: the writer states `C` out of band (the test harness passes
it), since `ch(k) mod C` is ambiguous from one frame. (Self-describing
`C` in a superblock is a deferred extension, not needed by the
write-path-first deliverable.)

## 5. Determinism

Same program, same inputs → byte-identical `.esf` file: frame order
is program order, the schedule is a fixed LUT, integrity sums are
integer arithmetic, zero-fill is explicit. Verified by the
determinism test (same program twice, byte-identical file).

## 6. Cost (measured, not promised)

`.esf` costs one 4096-byte `fwrite` per frame plus the syndrome
summation pass over the fixed 4080-byte covered region (three
multiply-accumulates per byte). Write throughput vs plain `fwrite`
of the same byte count is measured in `tests/stream/` (overhead
test) and reported, not guaranteed.
