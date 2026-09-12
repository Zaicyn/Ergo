# SQ5 baseline + FASM port

Source: `sq5_cert.c` (cert driver, 326 lines), `sq5_core.h`
(counterflow journal core, 367), `bench_sq5.c` (comparison row —
context only, not ported), `SQ5_CERTIFICATION.md` (pre-registered
oracle table + the four Wigner fixes), `sq5_mirror.py` (independent
oracle, stays python-side).

## Baselines

- GCC `-O2 -mavx2 -msse4.1` (`out.gcc.txt`): matches the
  pre-registered table exactly (900/900, 300/300s, 2000/2000 +
  31698 quads, 6000/6000 + 5370/6000 — see `SQ5_CERTIFICATION.md` §1
  Fix 3). `SQ5T` timing varies run to run (excluded from diffs).
- musl-static (`out.musl.txt`): identical modulo SQ5T.
- `audit.gcc.txt` / `audit.musl.txt` (211647 B): byte-identical —
  the audit dump is fully deterministic (seed `0xCE27`).

## FASM port (`sq5.asm` -> `sq5`, 11379 bytes, no libc)

Scalar + SSE4.1 `journal_add` (dispatched via CPUID.1 ECX[19], scalar
fallback). Verified: stdout oracle byte-identical at default/30/7,
audit byte-identical, repeat runs identical modulo SQ5T, and
`sq5_mirror.py` S1–S4 PASS against the FASM audit.

Notes: RNG is xoshiro256** (not ++); SEC uses signed `idiv`;
journal/stamp XOR acts on LE bytes in place; `SQ5T` via `cvttsd2si`
(timing only). 344 ms best-of-5 vs 61 ms gcc-avx2 vs 154 ms
scalar-C — flux-sweep scheduling is the known lever (see progress.md
SQ5 section); an AVX2 flux attempt was measured 2.5× worse and
reverted rather than shipped slow.

Bugs caught: alloc-scatter quotient/remainder swap (self-consistent,
audit-only symptom); `cdq`-kills-divisor SIGFPE; reversed torus copy
wiping `clean` (one swap → Phase B + O7 + audit diverge); hex-staging
half-size; inverted chunk-min `cmov`. All in `progress.md` pitfalls.
