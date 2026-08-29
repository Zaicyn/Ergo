# Owned transcendental kernels — verification results

2026-08-29. Kernels: `core/runtime/ergo_math_kernels.h` (SIN, COS, EXP,
LOG, POW, ATAN2; f64 + f32). Standard: Spec/Ergo_Hardware_Op_Map.md §2.

## Tooling (all in tests/math_kernels/)

- `gen_coeffs.py` — generates the polynomial coefficient sets:
  Chebyshev-node fits solved as power-basis Vandermonde systems at
  800-bit mpmath precision, dense-validated. The fdlibm/msun exp/log
  f64 formulations are validated the same way (3.4e-19 / 1.2e-18 sup
  error in exact arithmetic).
- `dump.c` — bit-plumbing harness: raw-bits in, raw-bits out, no text
  float parsing anywhere.
- `ulp_check.py` — sweeps + domain-edge cases vs an 800-bit mpmath
  reference (correctly-rounded via `float(mpf)`), per-kernel max-ulp
  report, and gcc-vs-clang bit identity over the identical sweep.
  Run: `python3 tests/math_kernels/ulp_check.py` (requires
  `.venv` mpmath; builds `dump_gcc`/`dump_clang` with the recipe flags).

## Measured (2026-08-29, this machine; gcc 16.1.1, clang 22.1.8)

| kernel | cases | max ulp | gcc==clang |
|---|---|---:|---|
| sin   | 80220 | 2 | yes |
| cos   | 80220 | 2 | yes |
| exp   | 90009 | 1 | yes |
| log   | 84009 | 1 | yes |
| atan2 | 30076 | 1 | yes |
| pow   | 34485 | 1 | yes |
| sinf   | 70030 | 1 | yes |
| cosf   | 70030 | 1 | yes |
| expf   | 60009 | 1 | yes |
| logf   | 62008 | 1 | yes |
| atan2f | 20049 | 2 | yes |
| powf   | 20385 | 1 | yes |

pow extended stress (post-restructure, 2026-08-29 evening): 200,000
additional cases (positive base × ±1000 exponent, near-1 bases,
negative base × integer exponent, overflow/underflow boundary fuzz) —
max 1 ulp, gcc==clang bit-identical. Speed: 534 → 107 ns/call f64
(log2_dd 195 → 68 ns, exp2_dd 207 → 23 ns), 83 ns f32 (libm: 22.8 /
9.3).

Edge coverage: denormal inputs/outputs, ±0, ±Inf, NaN; trig near
multiples of π/2 at several magnitudes and huge arguments through the
Payne-Hanek path (1e6..1e300, plus 6381956970095103-class stress
arguments); log near 1.0 (±2000 ulps) and denormal inputs; exp across
the denormal-output band; pow overflow/underflow boundary fuzz and the
C99 Annex F special lattice (hand-written oracle, not host libm).

Sweeps where the reference itself needs care: mpmath range reduction
for |x| ≥ 2^400-scale trig arguments needs working precision above the
exponent; the harness runs 800 bits and the PH path was additionally
verified against an exact-integer mirror of the reduction window.

## Bugs the harness caught during development (recorded)

- Hand-typed fdlibm exp coefficients from memory had wrong exponents
  (P2–P5) — the exact-arithmetic formulation check passed but the hex
  literals were wrong. All constants now machine-verified.
- log f64: m-window upper edge missing (m in [sqrt(2), 2) never
  halved) — pushed the series far outside its fit interval near x=1.
- atan f64 core: sign convention of the fitted polynomial
  (atan t − t vs t − atan t) mismatched the fdlibm assembly line;
  plus a wrong reduction constant (`1+1.5z` vs `1.5+1.5z`).
- Payne-Hanek: with an 8-limb window the fraction's low bits fell
  below the extraction windows for F < 192 (corrupting the round-up
  complement) — fixed with a 9-limb window (F ≥ 215 always).
- atan2 ratio guard: exponent-difference-by-bit-subtraction is
  contaminated by mantissa borrow — restructured to divide first and
  guard only the +Inf ratio.
- pow f64: `2+f` in the log argument reduction is not exact — a plain
  f64 divide there capped the dd chain at 2^-54 (51-ulp pow cases).
  Fixed with dd division.
- f32 small-argument cutoff was written as the 2^-10 bit pattern,
  not 2^-12 — sinf/cosf returned the identity where a 2.5-ulp
  correction was needed.
- gcc/clang bit divergence came from contractible `a - b*c` tail
  expressions (kcos qx path, exp/log tails) — all now explicit fma.
