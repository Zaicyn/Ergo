# SQFH baseline + FASM port

Source: `sqfh_cert.c` (synthetic-stream cert driver, 161 lines),
`sqfh_core.h` (lock-in handoff core, 566 — legacy path only),
`bench_sqfh_ab.c` (model-M + real-engine harness — context only, not
ported), `SQFH_DESIGN.md`.

The fast pass: tiles of 64 f32 samples validated against an analytic
prior (4 trig + atan2 per tile via Chebyshev recurrence — no
per-sample transcendentals). Cert uses the legacy bare-sinusoid path
only (`sqfh_init`, never `init_m`); model-M/exp paths not ported.

## Baselines

- GCC `-O2` (`out.gcc.txt`): 9 oracle lines — purity 4069/4069,
  2 slips + recovery, episode 1500/1512, 12/12 raw, spike 3000/17,
  12/12 overflow + 0.6053 excess. **Zero FMA** in the emitted code.
- musl-static (`out.musl.txt`): identical modulo O6 timing.

## FASM port (`sqfh.asm` -> `sqfh`, 8221 bytes, no libc)

First port with **owned f64 transcendentals** (V8's float kernel
stayed libm-bound): Cody-Waite sincos (x87-derived 2pi split +
quadrant fold), half-angle atan2, asin-via-atan2, `sqrtsd` for
sqrt/hypot (correctly rounded = bit-identical to libm). All decimal
consts as single-rounding int ratios (no hex tables, no parser
trust); TRUE_K etc. computed at runtime in C op order. Verified
3.9e-12 worst-case vs libm (margins need 5e-5).

Verified: stdout oracle byte-identical (O6 timing excluded),
repeat runs identical, 8 ms best-of-5 vs 8 ms gcc (parity — see
below). O6 lanes match (4069/2/12/1).

Speed work (post-port investigation): whole-program perf showed
47.9M cycles at IPC 1.16, 72% in stream gen. Microbenchmarks:
owned `my_sin` 16.0 ns/op vs libm 11.1 ns (1.45×) and ~7ns per
`frnd` draw with call overhead. Fix, both bit-safe by construction:
per-tile reseeded Chebyshev rotation for the main sine (drift
~1e-14 over 64 steps, same shape the core itself uses) + inline
xorshift draws (identical draw stream, zero calls) on clean tiles;
exact full-sin path kept for overflow/shear tiles. 16 → 8 ms,
oracle still byte-identical (recurrence perturbs ~1e-14, lanes
need 1e-3, %.4f needs 5e-5).

Bugs caught: `rep stosq` advancing `rdi` past the struct init
(fields landed in the next BSS object); `wallns` killing the tile
pointer in `rsi` (every tile read garbage → all-SHEAR); tns held
in a register the scoring loop reuses (O6 0.0); `C_4096` hex wrong
(0x412… = 524288, not 4096); `vpbroadcastd ymm,r32` is EVEX-only
(SIGILL — use movd + xmm broadcast; see progress.md pitfalls).
