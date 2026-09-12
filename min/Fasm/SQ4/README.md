# SQ4 FASM port (completes the set)

Source: `benchmark/bench_sq4.c` (there is no sq4_cert.c — the bench
IS the spec). Fixed protocol: n=256, 391 rounds, error_rate=0.01
(inj=3), churn=0, seed `0x5C4A11`. RNG is xoshiro256** (same code as
sq5.asm, correctly labeled).

## What it covers

`sq4.asm` ports the bench flow with the **fixed** `sq4_fal`
(overflow probe): tin, 391×256 allocs, rep, occupied-slot scan,
Fisher-Yates victim pick (in-place, no malloc), single-bit flips,
val/score/repair/re-validate, coherency walk, SQ4OR oracle lines +
SQ4T timing (excluded from diff). Victims go to stderr as
`SQ4V ev` lines (bench convention).

## Verification

- O1 100096/100096 (0 fails), O2 3/3, O3 3/3, O4 0 slots.
- Victim stream **byte-identical to C** (order included):
  (4,23,31), (2,6,25), (0,27,19) — same seed, draws, conversions.
- 1.8 ms best-of-5, 3248 bytes.

## Bugs caught (all in the port, none in C)

- `sq4_rep` assembled into a non-executable segment (chunk landed
  past the rodata directive) — call faulted into literals. Fix:
  keep all code above `segment readable`. New rule of thumb: after
  any append, grep `^segment` and confirm every global label sits
  in the right one.
- Torus layout: twhead/tlen/talloc are int[8][2] = 64 B each, not
  32 — overlapping offsets corrupted everything downstream while
  O1 stayed green (twhead still advanced monotonically-ish).
- Slot stride cargo-culted from sq5 (`shl 5`): SQ4's is (gen*8+bin),
  not (bin*32+gen) — rep/val/scan/coh all read garbage (val 135
  bad vs coh 0 was the fingerprint: same-state disagreement means
  addressing, not content).
- Twhead reads at `rax*4` instead of `rax*8` (half offset) —
  occupancy went sparse (n_occ ~100, inj=1) while allocs still
  "succeeded". Sparse occupancy with zero fails is the fingerprint.
