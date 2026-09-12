# SQM baselines + FASM port

Source: `benchmark/{sqm_cert.c,sqm_core.h,bench_sqm.c,SQM_DESIGN.md}`
+ shared `common.h`/`cache_perf.h`. `esf_syndrome.h` copied for reference:
the port implements the exact *scalar* moment path, not the SSE4.1 one
(both provably identical — all sums < 2^32 at PAY=64).

## Baselines

- GCC (`-O3 -march=x86-64-v3 -ffp-contract=fast -fno-math-errno`,
  `out.gcc.txt` + `sqm_cert.gcc.s`): all 9 lines pass, 9 ms.
- musl-static (`out.musl.txt` + `sqm_cert.musl.s`): byte-identical.
  Only asm diff: glibc inlines `atoi` as `strtol`, musl calls `atoi@PLT`.
- Driver uses `rand_u32` only (no `rand01`). One `%.2f` line (O3).

## FASM port (`sqm.asm` -> `sqm`, 7938 bytes, no libc)

Full `sqm_write` (skip/delta/slice paths, lazy halves, pointwise
journal updates), Vandermonde solve (`idiv` — C truncation semantics;
TEST-bit for `%2==0`), sweep, all six oracles, own `%lld`/`%.6f`/`%.2f`
(int-part + guard digit + sticky, round-half-even).

Verify: `fasm sqm.asm sqm && ./sqm`, stdout byte-identical to `sqm_cert`
at default 1000 rounds and at 7/30/2000 (`out.fasm.txt`).

Bugs the oracle diff caught:

1. `okc` in scratch across a call: the O2 driver held its content-ok
   bit in `r11d` across the `mom` call for the journal check — but
   `mom` uses `r11` as its s2 accumulator. Result: `o2_ok` accumulated
   garbage (`442/1000`). Symptom fingerprint: per-round BSS dumps were
   *correct* while the accumulated oracle was wrong. Fixed with
   callee-saved `ebp`. Same bug class as Sq2B's seed-`ecx` clobber:
   audit every value live across a `call` — only rbx,rbp,r12-r15
   survive.
2. Confirm-read counter order: C counts the read even when the check
   fails — `inc` before the branch, not after (latent O3 inexactness).
3. Set-direction on flag tests: `caught += (D != 0)` needs `setz`
   after `test eax,eax` when the helper returns 1-on-equal (O5 quad).
   Check every `setcc` against its helper's polarity.
