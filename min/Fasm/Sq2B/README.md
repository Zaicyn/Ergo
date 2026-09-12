# Sq2B (fixed V22) baseline + OG comparison

Source: `benchmark/{bench_sq2b.c,sq2b_cert.c,squaragon_v2_bio.h,
SQ2B_DESIGN.md}` (copied here) + shared `common.h`/`cache_perf.h`.
Driver: `sq2b_cert` at default 1500 rounds (Phase A isolated +
Phase B poisson tail + blind-class mapping). Flags: `-O2`; musl
build is `-static`.

## Outputs (`out.gcc.txt` vs `out.musl.txt`)

**Byte-identical.** Full table:

```
O1_payload_det   900/900  | O2_payload_rep   900/900
O3_syndrome_det  300/300  | O4_syndrome_rep  300/300
O5_closure       0 unresolved | O6_apoptosis 0 (isolated)
O7_blind_random  2000/2000 detected+tombstoned (never silent)
O8_blind_crafted 2000/2000 blind (documented exclusion)
auxB_det  5647/5647 | auxB_rep 5551/5647 = 0.983
auxB_tombs 48, coh_fail 48, slippage 0, unresolved 0, retries 0
```

Runtime ~0.2 s both toolchains.

## Assembly (`sq2b_cert.gcc.s` vs `.musl.s`)

Same story as V22: kernel codegen identical modulo label numbering;
only the `atoi`→`strtol` (glibc) vs `atoi@PLT` (musl) CLI-parsing
difference.

## OG vs fixed

| | V22 (OG, `../V22/`) | Sq2B (fixed, here) |
|---|---|---|
| Cell | twin identical shells, compare wholesale | duplex base-complement (`^0x55`), per-strand self-syndrome |
| Write path | write and hope | kinetic proofreading: write, re-read, verify, 1 retry, else refuse |
| Damage confined to 1 strand | unrepairable | resynthesized from intact strand (900/900 repair) |
| Both strands hit | silent propagation risk | `0xDEAD5EED` tombstone, loudly counted (48/48, coh_fail == tomb count) |
| Oracle shape | ns/call + zero-residual | detection/repair rates + tomb accounting |
| Cross-libc | bit-zero holds | byte-identical tables |

Honest caveat: the two drivers measure different things (residual
latency vs detection rates), so there is no single "Xs faster"
row — the fix summary is integrity, not latency: failures that were
silent-or-fatal in V22 are detected-and-counted in Sq2B at a measured
98.3% poisson-tail repair rate.

## FASM port (`sq2b.asm` → `sq2b`, 6162 bytes, no libc)

Full port of `sq2b_cert.c` + cell + xoshiro RNG: static BSS arena
(~260 KB: three cells, tables, accumulators), `write`/`exit` syscalls
only, own `%lld`/`%.6f` formatting (exact-double digit extraction,
round-half-even).

Build: `fasm sq2b.asm sq2b` (FASM 1.73.x). No install needed — the
assembler runs from a tarball.

Verification: stdout **byte-identical** to `sq2b_cert` at default 1500
rounds and at rounds 30 and 7 (`out.fasm.txt` == `out.gcc.txt`).
Runtime ~0.9 s vs ~0.2 s gcc (scalar hand-loops vs `-O2`).

Bugs caught by the oracle diff during porting (all found because
output differed, all worth knowing for the next ports):

1. Loop counter in a call-clobbered register: `seed_rng` counted its
   10 warmups in `ecx`, which `xoshiro` clobbers — it warmed up
   ~2 billion times (21 s runs) and landed mid-stream. Fixed with a
   callee-saved counter. Audit rule: no counter in rax/rcx/rdx/r8-r11
   across a `call`.
2. Byte load into the address register: scoring decoded strand 1 with
   `mov al, [rax+rcx]` — writing `al` corrupts the low byte of the
   `rax` pointer itself. Failed exactly the strand-1 events (452/900).
   `strand_ok` survived only because it uses `rbx`. Fixed with `dl`.
3. FASM 1.x vs UTF-8: a comment containing `─` poisoned parsing of the
   *next* line (bogus "operand sizes" error). File is ASCII-only now.
4. FASM types labels by defining directive: `rb`-defined labels read
   as bytes, so `mov rax, [accA+24]` fails — accumulators are `rq`.
