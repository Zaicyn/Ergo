# PLAN — torusecc: multi-bit correction on torus layout (Secure stage 2)

Status: planned, not started. Predecessor stage DONE: hashshoot
(`Secure/hashshoot.asm` + `.c`, commit `226018d`; splitmix-stream
wins: 1680 ns/4 KB, avalanche 32.02; house-hash decision in
`HashKit/README.md`). Specs: `Spec/Ergo_Stream_Format.md` (§3 repair),
`Spec/ESF_Slot_Pool_Brief.md`, `Secure/README.md` (capacity argument).

## Goal

Demonstrate multi-byte correction (not just detection) for 4096-byte
frames using torus geometry: partitioned per-sub-bin moment triples
plus duplex shells. Report correction rate vs error count/pattern,
with miscorrections expected at exactly 0 (every repair gated +
re-verified, 2^−32 floor argument as in ESF §3).

## Geometry (fixed for the prototype)

- Frame = 4096 B payload, modeled as **8 sub-bins × 512 B**.
- Each sub-bin has **2 shells**: shell0 = data bytes, shell1 =
  bytewise complement (sqb duplex convention `c1 = c0 ^ 0x55`).
- Per sub-bin per shell: triple `(S0, S1, S2)` =
  `(Σb, Σb·idx, Σb·idx²)` mod 2^32, **idx 1-based within the sub-bin**
  (1..512; partition keeps `|d·p| ≤ 255·511`, no wrap ever).
- Plus one global frame triple (ESF-style, idx 1-based over 4096)
  for the detection floor + cross-check.
- Stored reference triples ("journal") computed at frame-write time;
  residuals = recomputed − stored. (Mirrors sq5 `jr` + flux split.)

## Repair ladder (per sub-bin, in order)

1. **Clean**: all residuals zero → nothing to do.
2. **Single-byte SEC** (mirrors `sq5_try_sec` / ESF §3):
   `d = ΔS0` signed, valid iff `d ∈ [1,255]` or `d ∈ [−255,−1]`
   (mod-2^32 edges); `p = ΔS1/d` with exact divisibility check,
   `1 ≤ p ≤ 512`; gate `d·p² ≡ ΔS2`; apply, re-verify all three.
3. **Duplex 2-byte solve** (same sub-bin, both shells = 6 equations):
   unknowns `d1,p1,d2,p2`. Solve from shell0 pair + shell1 pair
   jointly (4 equations), gate on remaining 2 + global triple +
   re-verify. Refuse on any failure.
4. **Refuse** (detected, reported, never miscorrected).

Expected capacity: k=1 → 100%; spread k≤8 (~≤1/sub-bin) → ~100%;
same-sub-bin k=2 → fixed via (3); same-sub-bin k≥3 → refused,
detected, miscorrections 0.

## Trial matrix

k ∈ {1,2,3,4,6,8} bytes × {spread (uniform random positions),
clustered (all in 1–2 sub-bins)} × N=500 trials each. Per trial:
record corrected / refused-detected / miscorrected. Inject with
xoshiro/xorshift, fixed seed (deterministic). Error bytes uniform
nonzero deltas.

## Build order

1. `Secure/torusecc.asm`: BSS (frame, backup, stored triples
   8×2×3 dwords + global 3, recomputed ditto), deterministic fill,
   triple builders (scalar first — 512 B × 16 triples is trivial
   cost; vectorize only if profiling demands it), SEC solver,
   duplex 2-byte solver, trial driver, TSV print
   (`T k=<k> <spread|clust> corrected=<n> refused=<n> misc=<n>`).
2. `Secure/torusecc.c` mirror: same fill/inject/solve, same TSV.
   Digests + TSV must match the asm exactly (house rule).
3. Run matrix, paste table into this file under `## Results`,
   commit. Misc > 0 is a STOP event (do not tune around it —
   find the unsound gate).

## Reuse (do not reinvent)

- Moment math shape: `sq5_flux_bin` / `syn_avx2` patterns
  (vpmovzxbd + vpmulld chains) if the scalar triple builders show
  up in profiling (unlikely at 4 KB).
- Frame hashing of repaired frames: splitmix-stream
  (`HashKit/README.md` decision).
- Print/emit shapes: `hashshoot.asm` `ph16`/`pdec`/linebuf pattern.
- Deterministic RNG for injection: xorshift64 seed `0x123456789`
  (same as hashshoot detection).

## Pitfalls (paid for this session — do not repay)

- `vzeroupper` AFTER 256-bit loads wipes them (pitfall 18): loads
  must dominate their uses; no hoisted ymm constants across calls.
- Legacy SSE inside AVX loops = ~70 cy transitions (pitfall 17):
  VEX-only in any 256-bit region.
- BSS label typing: `rb`-defined labels need explicit
  `dword`/`qword`/`yword`/`dqword` size on symbol access.
- Timing-loop counters must live in regs the callee preserves
  (r14d/r15d owned by `vfy_B`-style callees caused an infinite
  123↔124 oscillation once).
- Probe/trial code after `jmp <loop>` is dead: route loop-exit
  edges through trampolines.
- `mov [sym], imm64` never assembles: `mov rax, imm` + store.
- Verify-before-commit: oracle/audit diff + C mirror + best-of-5,
  same as every prior stage.

## Results (DONE 2026-09-13, hardened 2026-09-14)

`torusecc.asm` (+ `.c` mirror): 8 sub-bins × 512 B × duplex shells,
per-sub-bin triples + global, SEC + duplex-2-byte (1+1 algebraic,
2-in-one bounded search) + refuse ladder, N=500 per cell, verdicts
via pristine-backup memcmp. Asm/C mirror-clean on all 12 cells,
deterministic across runs.

| k | spread (corr/ref/misc) | clust (corr/ref/misc) |
|---|---|---|
| 1 | 500 / 0 / 0 | 500 / 0 / 0 |
| 2 | 500 / 0 / 0 | 500 / 0 / 0 |
| 3 | 499 / 1 / 0 | 370 / 130 / 0 |
| 4 | 490 / 10 / 0 | 4 / 496 / 0 |
| 6 | 467 / 33 / 0 | 285 / 215 / 0 |
| 8 | 411 / 89 / 0 | 0 / 500 / 0 |

misc = 0 over 6000 trials × 2 implementations.

### Soundness hole found by the mirror rule, closed with S3

The first matrix showed 2 miscorrections (k=3 clustered). Autopsy
(python replica of the draw stream + candidate enumeration) proved
the cause: **post-fix re-verification is vacuous by linearity** —
a search solution satisfying all three equations zeroes the
residuals by construction, so reverify (sub-bin AND global) passes
provably, and memcmp is the only thing that ever catches it.
Fix: **4th moment S3 = Σb·idx³** as an independent gate (SEC and
search both). A spurious pair satisfying S0/S1/S2 fails S3 except
by fresh 2^−32 coincidence. Syndrome cost rises 204 B → 272 B per
4 KB frame (5.0% → 6.6%). Bonus: S3 *disambiguates* (cases with two
S0–S2 solutions where only one passes S3 now fix instead of
refusing — k=2 went 499/487 → 500/500, k=6 clust 264 → 285).

Bugs caught along the way (all fixed, all in PLAN pitfalls):
- `movsx rbx, r9b` in `sec_fix` broke the S2 gate for |d| > 127.
- Clustered-split register reuse (`r10d` = split point clobbered
  by per-iteration shell assignment → 1+5 instead of 3+3);
  C mirror was right.
- resbin shell1 stores landed at +12/+16/+20 (clobbering shell0's
  S3 slot) instead of +16/+20/+24 — found by disassembling the
  built binary after a debug print showed impossible e3=0.

## Resume checklist (for a fresh context)

- Repo: `/home/zaiken/Ergo`, branch state per `git log --oneline -3`
  (expect `226018d` tip). Toolchain: `/tmp/opencode/fasm/fasm.x64`
  v1.73.35 (not on PATH). FASM include resolves relative to the
  source file's dir; `yword`/`dqword` size tags required on
  symbolic AVX mem operands.
- Key files: `min/Fasm/Secure/README.md` (analysis + hashshoot
  results), `min/Fasm/Secure/hashshoot.{asm,c}` (reference for
  print/AVX/determinism patterns), `Spec/Ergo_Stream_Format.md` §3
  (repair math), `min/Fasm/SQ5/sq5.asm` `sq5_try_sec` shape.
- Benchmark table: `min/Fasm/BENCHMARK.md` (all systems parity+).
- Start at Build order step 1. First acceptance gate: k=1 spread
  corrects 500/500 with misc=0 and C mirror-clean.
