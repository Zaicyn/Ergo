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
integrity residual generalizes the v4 3-axis residual (Fix 2) from
3-vectors to bytes.

## 1. Frame layout

All integer header fields are **little-endian**, fixed width.

| offset | size | field |
|---|---|---|
| 0 | 4 | magic: ASCII `ESF1` (0x31 0x46 0x53 0x45 little-endian) |
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

## 3. Integrity residual

The v4 3-axis residual (`(I+R120+R240)` symmetrization, max over
axes, floor `sqrt(3)*|d|/scale`) generalizes to bytes as three
**rotated projections** of the summed region: byte at file offset
`o` belongs to projection class `a = (o - 4) mod 3`, and

```
S_a = sum of bytes at offsets o in [4,16) ∪ [28, 28+L)
      with (o-4) mod 3 == a                                  (mod 2^32)
```

The **summed region** covers the mutable header fields (frame index,
channel, length, sequence — offsets 4..15) *and* the used payload —
not the magic (checked by equality), not the integrity words
themselves (offsets 16..27), and not the zero-fill.

**Detection floor:** any single-byte change `d` (`d` in ±[1,255])
inside the summed region moves exactly one projection by `d`, so the
residual `max_a |S_a' - S_a|` is exactly `|d| >= 1` — every
single-byte corruption is caught, no blind directions (contrast the
v2 triple-XOR, blind to 2/3 of perturbation channels). A multi-byte
region flip escapes only if the signed changes in *each* of the three
classes independently cancel mod 2^32; the measured detection rate
over injected random regions is reported by the corruption test
(mirroring the v4 1000-direction audit).

The residual is an *integrity* check, not a cryptographic hash: it
detects corruption, it does not authenticate.

## 4. Reader algorithm (reference)

For each 4096-byte frame at file offset `k*4096`:

1. Magic must be `ESF1` (equality).
2. `k` field must equal the frame ordinal; `c` must equal
   `SCATLT[k mod 32] mod C`; `L <= 4068`; the channel sequence must
   be the count of earlier frames on channel `c`.
3. Recompute `S0,S1,S2` over offsets `[4,16) ∪ [28, 28+L)`; compare
   to the stored words.
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

`.esf` costs one 4096-byte `fwrite` per frame plus the integrity
summation pass over the payload. Write throughput vs plain `fwrite`
of the same byte count is measured in `tests/stream/` (overhead
test) and reported, not guaranteed.
