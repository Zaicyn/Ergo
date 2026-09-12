# Trit metadata layer — ROUGH DRAFT (theory, not yet tested)

Status: proposal only. Nothing below is implemented or measured. The codec
math (3^5 = 243) is arithmetic fact; everything about payoffs, placements,
and performance is conjecture until Phase 1 runs.

## Idea

Use base-3 (~1.585 bits/unit) as a *metadata/control* layer — an index
system akin to extents — over structures that already have natural ternary
states. Never as compute widths (see `minimum_unit.md`: the 1.58-bit ghost
warning). Rule of thumb for the whole design: **2-bit packing for hot
state, trit packing for cold metadata.**

## Codec (defined, not yet built)

- Little-trit-first: `v = t0 + 3*t1 + 9*t2 + 27*t3 + 81*t4`.
- Five trits per byte (3^5 = 243 <= 255).
- Codes 243–255 are RESERVED (framing/run markers, stream sync). A decoder
  that accepts them as data is a bug; refusal must be loud.
- Encode: multiply-add chain. Decode: 256-entry table (no divmod anywhere
  near a hot path).
- Density: ~1.585 bits/unit vs 2.0 for 2-bit packing (~20% saving) at
  significant decode cost. That tradeoff is why hot state stays 2-bit/byte.

## Candidate states (observed, already ternary in practice)

- Sweep outcome per codon: untouched / repaired / tombstoned
  (today: 1 action byte each).
- Slot lifecycle: empty / live / tomb (today: `occ` byte + tomb dword —
  ~5 bytes holding ~1.58 bits of information).
- SQW recognition cache entry: empty / valid / tombstoned.
- O6-style audit outcomes per sweep/frame.

## Extent form (theory)

Damage is sparse, so per-unit density is the wrong optimization — run
structure is. Proposed: `extent = (base:u32, len:u32, state:trit)` over
sweep outcomes, trit-packed on write, decoded on audit only. Long
untouched runs + rare repair/tomb events; the 12 spare codes serve as run
markers. Filesystem-extent shape, three states instead of allocated/free.

## Phases (gated, like everything else)

1. **Codec alone** (C + FASM mirror): round-trip property tests including
   the 243 boundary, throughput measurement, loud refusal of 243–255.
   No integration until this passes.
2. **One cold path**: trit-packed sweep-action log per round, sized
   against raw bytes and 2-bit packing. If it does not win net of table
   cost, stop here.
3. **Never the hot loop.** Sweep keeps reading byte flags; decode runs on
   audit/snapshot only, with the byte array as oracle (same discipline
   as `sq5_mirror.py`).

## Explicit non-goals (theory, held until evidence says otherwise)

- No trit-packed slot states in allocator hot paths.
- No GPU-lane ternary metadata before the binary ballot pattern saturates.
- No claims about throughput until Phase 1 measures it.
