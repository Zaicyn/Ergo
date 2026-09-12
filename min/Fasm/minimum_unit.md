# Minimum unit — what width fits the math (SQM moment system, PAY=64)

Measured/computed 2026-09-11 (exact bounds, not estimates). Purpose: stop
re-litigating lane widths. The answer is a ladder — each layer has its own
minimum, and they are not interchangeable.

## The ladder

| Layer | Exact bound | Minimum unit |
|---|---|---|
| Pairing (complement `^0x55`, quaternary digits, period-4 bins) | 4 symbols | **2-bit** symbols |
| Payload bytes | full 0–255 range used by fill | **8-bit** |
| Delta magnitude | ±255 | 9-bit signed |
| Position (1-based 1..64) | 64 | 7-bit |
| Moment s0 | ≤ 16,320 | 14-bit |
| Moment s1 | ≤ 530,400 | 20-bit |
| Moment s2 | ≤ 22,807,200 | 25-bit |
| Moment s3 | ≤ 1,103,232,000 | **31-bit** |
| s3 per 16-position lane, worst (top) lane | ≤ 750,573,120 | 30-bit |
| Solve det / un / vn | ~2^39 / ~2^45 / ~2^50 | **64-bit** container |

## Conclusions (locked)

1. **32-bit lanes carrying 8-bit inputs is the minimum efficient unit for
   the moment math.** s3's 31 bits force it. u16 lanes overflow — even a
   16-position split lane needs 30 bits at the top end — so any sub-32-bit
   scheme pays hi/lo carry bookkeeping that costs more than it saves.
   This is exactly what GCC emits (`vpmovzxwd`/`vpmulld`) and what the
   SSE4.1 path in `sqm_core.h` already does. The scalar FASM port's shape
   (u8 in, u32 accumulate) is confirmed, not just its values.
2. **The solve stays scalar u64.** Its intermediates genuinely need ~50
   bits; it runs only on mismatch/sweep (rare paths). No SIMD case.
3. **The 2-bit structure is real but lives one layer down.** Complement
   pairing, quaternary digits, period-4 bins — all 2-bit phenomena. The
   moment sums operate on byte magnitudes and are blind to pair states.
   Do not try to push pair-width arithmetic up into the moments.

## The 1.58-bit note (read before chasing ghosts)

`log2(3) ≈ 1.585`. It appears nowhere as a compute width in this system.
What it IS: the information content of a uniform ternary decision, and
this system is full of natural ternaries — per-codon sweep outcome
(untouched / repaired / tombstoned), per-write path (skip / solve /
slice). So ~1.6 bits per codon is the entropy scale of the **control
layer**, and its only legitimate use case is **encoding the action
stream** (or reasoning about decision capacity) — never lane widths,
never accumulator sizes, never the solve. If a future discussion starts
with "1.58-bit units," point here: it is a measure of decisions, not a
thing to build an ALU lane out of.

## Consequences for the AVX2 `mom` (when we write it)

u8 load → `vpmovzxbw`/`vpmovzxwd` widen → u32 `vpmulld` chains →
horizontal sum at the end. Inputs stay bytes on the floor; accumulators
stay doublewords; the solve stays scalar. Anything narrower breaks s3;
anything wider wastes lanes.

## Float containment (locked: integer or f64, never f32)

s3's 31 bits sit exactly between the two float mantissas: f32 carries 24,
f64 carries 53. Consequences, all exact rather than approximate:

- Moments can never go f32. At s3's scale the f32 ulp is 2^7 = 128, so
  accumulations would be wrong by up to ±64 before the solve starts, and
  the exact Vandermonde check dies. One bit-width comparison rules it out
  permanently: 31 > 24.
- The *entire* pipeline fits f64 exactly: s3 (2^31), det (2^39),
  un (2^45), vn (2^50) — all below 2^53, so every value is exactly
  representable, including exact quotients on the divisible paths. f64 is
  a valid exact container; it just buys nothing over integer (`idiv`
  yields quotient and remainder together, which is what the divisibility
  checks want), so integer stays the implementation.
- The 53-bit boundary is already load-bearing elsewhere: `(x>>11) * 2^-53`
  carries maximal RNG entropy precisely there (hence the musl/glibc
  bit-identity), and the decimal digit-extraction printer works because
  doubles have room for its guard digits.
- Corollary for cadence: 16/32/64 *bytes* is the 128/256/512-*bit* SIMD
  register ladder, and 32 bytes is one AVX2 register is one moment struct
  (4xu64). The alignment table in the cadence discussion is really about
  registers, not caches.
