# FASM experiment — progress

Goal: prove small Ergo-adjacent kernels can go GCC -> musl -> bare FASM
(no libc) with byte-identical oracle output. See `plan.md` for the
original concept.

## Status

| Variant | Dir | GCC | musl | FASM | Notes |
|---|---|---|---|---|---|
| V8 slice (`viviani_normal` + `compute_invariant`) | `V8/` | identical | identical | matches (`v8_invariant`, 769 B, AVX2 fold + scalar fallback) | First blood. Integer kernel fully portable; float kernel is libm-bound (`sincosf@PLT`), stays in C until owned trig exists. Hand-AVX2 fold closes the open item (no gain at 32 XORs, recorded honestly). |
| V22 (OG residual) | `V22/` | `r=0 sink=0` | same | — | Baseline only. Algebraic-zero invariant holds cross-libc. V22 alloc bug characterized 2026-09-11 (220/256, 14.1% silent rejects, unbalanced Viviani scatter, no fallback) — fix deliberately open, Sq2B supersedes. |
| Sq2B (fixed V22) | `Sq2B/` | cert passes | byte-identical | matches (`sq2b`, 6795 B, AVX2 mismatch + syn, cell via shared `sqb_cell.inc`) | Full port + driver; cell logic extracted shared (oracle-identical after). Verified at 7/30/1500 rounds. |
| SQM (moment-Merkle) | `SQM/` | all 9 pass | byte-identical | matches (`sqm`, 8505 B, AVX2 mom integrated) | Full port: dispatched `mom` (AVX2 u32 lanes w/ scalar fallback), `idiv` Vandermonde solve, own `%.6f`/`%.2f`. Verified at 7/30/1000/2000 rounds. |
| SQ5 | `SQ5/` | O1-O7 + auxB match pre-registered table; audit byte-identical; mirror S1-S4 PASS on FASM audit | GCC+musl filed, cross-identical modulo SQ5T; audits byte-identical (211647 B) | matches (`sq5`, 11379 B, scalar + SSE4.1 journal) | RNG is xoshiro256** here; libm vestigial; newest/least-tested → repeat-determinism + 30/7 gates added. |
| SQW (memoized duplex) | `SQW/` | all 12 pass incl. 428/428 poison-failsafe | byte-identical | matches (`sqw`, 8156 B, shared `sqb_cell.inc` + recognition layer) | Recognition/cache/refcounts/audit new; cell rides free. Verified at 30/1500 rounds. |
| SQFH (+SQF) | `SQFH/` | O1-O5 + O7/O8 match; O6 lanes match (timing varies) | GCC+musl filed, identical modulo O6; **zero FMA** | matches (`sqfh`, 8221 B, owned f64 trig) | Fast pass done; cert is legacy-only (no exp/model-M); repeat-deterministic. |
| SQ4 (metadata torus) | `SQ4/` | O1-O4 counts match fixed C bench; victims byte-identical | C bench is the spec (no cert.c) | matches (`sq4`, 3248 B) | Completes the set. Ports the overflow-probe fix; fixed protocol (256/391/0.01). |
| Trit codec (Phase 1) | `trit/` (`trit.asm` + `trit_ref.c`) | mirror passes, digest matches | n/a (no libc to compare) | self-test 0/261, digest matches C | Full toolset below. |

Reference data: `V22/` and `Sq2B/` READMEs hold the OG-vs-fixed comparison
(detection/repair rates, not latency — the drivers measure different things).

## Trit codec Phase 1 (DONE 2026-09-11)

`trit.asm`: pack/unpack (bulk + scalar), assembler-generated 243-entry
decode table (self-validated arithmetically, so a table typo cannot hide),
loud refusal of 243–255 and of trit values > 2, exhaustive self-test
(243 round-trips + 13 byte refusals + 5 trit refusals = 261 checks),
FNV digest, rdtsc + clock_gettime bench. `trit_ref.c`: independent C
mirror — same 0/261, same digest `6e72a3b7acdc05e9` over 1M shared-seed
trits (validates RNG replication + pack equivalence end to end).

Speed (best-of-5, 1M trits):

| | FASM | C (`-O2`) |
|---|---|---|
| pack | 638 MB/s out (1.24 cy/trit) | 363 MB/s |
| unpack | 1067 MB/s in (0.74 cy/trit) | 186 MB/s |

The 5.7× unpack gap is table lookup vs per-trit divmod — the exact reason
the spec mandates tables. Pack gap (1.8×) is Horner+lea vs portable C.

## Trit Phase 2 (DONE 2026-09-11)

`trit/phase2.asm` (+ shared `trit_codec.inc`): 2000 real sweep-action
rounds (256 ternary outcomes each, captured from sq2b cert runs:
98.7% zeros) encoded four ways, sizes + best-of-3 encode/decode speeds,
round-trip verified. `out.phase2.txt` holds a reference run.

Sizes (bytes): raw 512000 (100%) | 2-bit 128000 (25%) | trit 104000
(20.3%, incl. zero pad) | RLE 30578 (6.0%). Trit beats 2-bit by the
predicted ~19% (1.585 vs 2.0 bits/unit). RLE crushes both — run structure
beats density on sparse damage, as predicted; the extent-RLE idea in
`trit_meta.md` is validated in miniature.

Speeds (MB/s, best-of-3): enc raw 7931 / 2-bit 3362 / trit 3083 /
rle 1463; dec raw 8433 / 2-bit 3262 / trit 5445 / rle 1651.
Round-trip fails: 0 everywhere. Note trit-decode beats 2-bit-decode
(table loads vs shift/mask chains); RLE is slowest both ways (branchy)
and 5× smaller — the classic density/speed trade, now measured.

## Log v1 — live action logs from sq2b (DONE 2026-09-11)

Per `compression_plan.md`: `trit/rle_pack.inc` extracted from
`trit/phase2.asm` (pack2/unpack2/rle_enc/rle_dec, dependency-free;
phase2 rerun prints identical sizes/fails), then `Sq2B/sq2b_log.asm`
(instrumented copy — `sq2b.asm` untouched) encodes action[256] RLE +
trit (52 B frame) after every cert-round sweep, verifies by
decode-compare in-tool, and appends [u16le len][payload] frames to
`/tmp/opencode/sq2b_log_{rle,trit}.bin`. Summary to stderr so the
12-line stdout oracle stays byte-identical to GCC.

Results at default 2000 rounds: RLE payload 30578, trit payload 104000
— byte-exact vs Phase 2 — fails 0; files 34578 / 108000 (4 KB framing).
Inline single-pass speeds (encode+verify, not best-of-3): enc ~410,
dec ~400 MB/s — slower than phase2's 1461/1651 best-of-3 encode-only,
as expected (byte-at-a-time verify loop + cold cache every round).
File-level check: RLE frames decode to histogram {0:505255, 1:6697,
2:48} — the logged stream IS the cert stream.

Bug caught: `mov rbx, rdi` before `push rbx` in the log-function
prolog — the push saved the clobbered value and the pop restored it,
silently losing the caller's cell pointer (segfault two layers later,
zero output). See pitfalls.

## Compression Phase A — zigzag + varints (DONE 2026-09-11)

`trit/int_codec.inc` (shared, single source) + `trit/zztest.asm` driver +
`trit/int_ref.c` mirror. Per `compression_plan.md`: `zz_enc`/`zz_dec`
branchless, `put_i64`/`get_i64` minimal-byte LE with sign extension,
`i64width` minimal signed width. Gate results: exhaustive int8 (256) +
32-entry boundary table incl. INT64_MIN/MAX (64 checks) = 0/576 fails on
both sides; digests match (`d16b669d9e621c20` over 65536 shared-LCG
values — validates edge semantics end to end). Speeds at parity, as
expected for scalar code: zz ~9 cy/op-pair both, put/get ~19 cy vs
6.2 ns C (~19 cy @3 GHz). No magic, just verified equivalence — which is
the point of a toolset. Bug caught en route: `get_i64` first draft
carried garbage upper `rdx` bits into its shift count (BSS-temp
discipline for values live across `cpuid`-style clobbers).

## AVX2 mom → sqm.asm integration (DONE 2026-09-11)

Standalone proved 80 vs 207 cycles/iter (2.7×), bit-identical over 108
combos. Integrated per plan: scalar `mom` → `mom_scalar`, shared
`mom_avx2` + `check_avx2` pasted verbatim, cached BSS dispatch flag set
once in `_start`, 32 B-aligned index consts, `hstmp`. Oracle matches at
default + 2000 rounds; wall 23 → 8.9 ms best-of-5 (2.6× whole-program),
now faster than gcc `-O3` (9.8 ms). Cost: +567 bytes.

## SQ5 port (DONE 2026-09-11)

`SQ5/sq5.asm` (scalar + SSE4.1 journal, 11379 B): the moment-journal
allocator, newest and least-tested of the bunch, so gated harder than
usual. GCC (`-O2 -mavx2 -msse4.1`) + musl baselines filed, cross-identical
modulo SQ5T; 12-line stdout oracle byte-identical at default/30/7;
211647 B `sq5_audit.txt` byte-identical (second artifact, feeds the
mirror); repeat runs identical modulo SQ5T; `sq5_mirror.py` S1–S4 PASS
against the FASM audit (O8 verdict 0) — the independent Python spec
agrees with the port end to end.

Notable: RNG here is xoshiro256** (`sq2b.asm`'s "++" label is wrong, its
code is ** — reused verbatim, correctly labeled this time). `-lm` is
vestigial (no transcendental calls). SEC needs signed `idiv` (C
semantics). Journal corruption XORs bytes of LE u32s — same-memory,
no endian work. SQ5T uses `cvttsd2si` + `emit_u64` (timing only,
excluded from diff).

Speeds (best-of-5, this box): FASM 344 ms vs gcc-avx2 61 ms vs
scalar-C 154 ms — 2.2× off equivalent C, 5.6× off vectorized C, our
worst ratio. Cause: flux_bin moment sweeps dominate and gcc `-mavx2`
auto-vectorizes them; the C build's explicit SSE4.1 journal path is in
(+5%: 362 → 344 ms). An AVX2 flux was attempted and REVERTED: 865 ms
(2.5× worse than scalar). Post-mortem: 16 B-chunk vector moments are
latency-bound on Zen 2 (long mulld chains, only 4-way chunk parallelism)
while scalar exposes 64 independent byte-chains the OOO engine eats for
breakfast; a competitive version needs full-unroll + multi-accumulator
scheduling, which is blind tuning without counters — queued, not forced.
Flux unrolling (scalar or vector) is the known lever; everything else
(alloc/rep/SEC/classify/stamp/audit) is noise beside it.

Bugs caught: quotient-saved-instead-of-remainder in alloc scatter
(`b0` always 0 — self-consistent sequential fill, oracles all green,
only the audit dump told the truth); `cdq` overwriting the `idiv`
divisor; reversed `cpy_torus` args wiping `clean` (pitfall #7 strikes
again — Phase B + O7 + audit all diverged from one swap); 1024 B hex
staging for 1024 B chunks (needs 2048); inverted `cmova`/`cmovb` in
chunk-min. See pitfalls for the durable three.

## SQFH port (DONE 2026-09-11)

`SQFH/sqfh.asm` -> `sqfh` (8221 B): the GPU→CPU handoff fast pass
(4096 tiles × 64 f32, lock-in demodulation against an analytic prior).
Cert uses the legacy bare-sinusoid path only — model-M/exp never
touched, not ported. GCC + musl baselines filed, identical modulo O6;
**zero FMA** in the build (all FP ops replicate bit-exactly).

First port with **owned f64 transcendentals** (V8's float kernel
stayed libm-bound): Cody-Waite sincos (x87-derived 2pi split, then a
quadrant fold — the first attempt wrongly used mod-2pi turns as
octants and blew up at multiples of pi/2), half-angle atan2,
asin-via-atan2, `sqrtsd` for sqrt/hypot (correctly rounded =
bit-identical to libm). All decimal consts as single-rounding int
ratios at init (no hex tables, no parser trust); TRUE_K etc. computed
at runtime in C op order. Unit-gated 3.9e-12 worst-case vs libm
(margins need 5e-5). New `emit_f4` (%.4f); O6 timing via scaled
`cvttsd2si` (excluded from diff, counts included).

Verified: stdout oracle byte-identical (O6 timing excluded), repeat
runs identical, 8 ms best-of-5 vs 8 ms gcc (**parity** — see speed
work below). O6 lanes match (4069/2/12/1).

Speed work (post-port investigation, measured not guessed):
whole-program `perf` showed 47.9M cycles at IPC 1.16 with 72% in
stream gen. Microbenchmarks: owned `my_sin` 16.0 ns/op vs libm
11.1 ns (1.45×); ~7 ns per `frnd` draw, dominated by call overhead
(2 nested calls × 1M draws). Fix: per-tile reseeded Chebyshev
rotation for the main sine (drift ~1e-14, same shape the core
uses) + inline xorshift draws (identical draw stream, zero calls)
on clean tiles; exact full-sin path kept for overflow/shear tiles.
16 → 8 ms with the oracle still byte-identical (1e-14 perturbations
vs 1e-3 lane margins and 5e-5 print bands). New `emit_f4` (%.4f);
O6 timing via scaled `cvttsd2si` (excluded from diff, counts
included).

Bugs caught: `rep stosq` advancing `rdi` past the struct being
initialized (fields landed in the next BSS object); `wallns`
clobbering the tile pointer in `rsi` (every tile read garbage →
all-SHEAR, the classic pitfall #1 wearing a syscall disguise);
timing accumulator held in a register the scoring loop reuses
(O6 0.0 — same class); hand-memorized `C_4096` hex wrong by 128×
(see new pitfall #14); octant-vs-turns confusion in the reducer
(caught by the trig unit gate before it could touch the oracle).

## Wall-clock speeds, all working FASM variants (best-of-5)

| Binary | Time | Size |
|---|---|---|
| `V8/v8_invariant` (FASM, AVX2 fold + scalar fallback) | ~1240 us (noise; startup-dominated, was 1260/1161 scalar) | 769 B |
| `V8/v8_driver.gcc` (C) | 1616 us | 16024 B |
| `Sq2B/sq2b` (FASM) | 903 ms scalar → 601 ms (+mismatch) → 351 ms (+syn) → 194 ms (+decode) → **152 ms (+pay_ok, 2.27× total)** | 6162 → 6401 → 6593 → 6891 → 7446 → 7766 B |
| `sq2b.gcc` (C `-O2`) | 212 ms | 28784 B |
| `SQM/sqm` (FASM) | 23 ms scalar → **8.9 ms AVX2 (2.6×)** | 7938 → 8505 → 9041 B (shared incs) |
| `SQW/sqw` (FASM) | 129 ms → 99 ms (+decode) → **44.6 ms (+pay_ok via shared cell)** | 8156 → 8252 → 8786 → 9106 B |
| `SQ5/sq5` (FASM, scalar + SSE4.1 journal) | 344 ms | 11379 → 11926 B (shared incs) |
| `sq5.gcc` (C `-O2 -mavx2 -msse4.1`) | 61 ms | 29632 B |
| `sq5` scalar-C (`-O2`, no SIMD flags) | 154 ms | — |
| `SQFH/sqfh` (FASM, owned f64 trig + rotation recurrence) | 8 ms | 8700 → 9158 B (shared incs) |
| `sqfh.gcc` (C `-O2`) | 8 ms | — |
| `SQ4/sq4` (FASM, fixed-probe port) | 1.8 ms | 3248 → 3821 B (shared incs) |
| `sqm` CREL (C full flags) | 9.8 ms | 32928 B |

Read honestly: the V8 pair is startup-dominated (µs of real work; the gap
is the dynamic loader). Sq2B was 4.3× slower than optimized C; the AVX2
`duplex_mismatch` integration (6.7× on the kernel) brought the whole
program to 2.8× (601 vs 212 ms), and `sqb_syn` stacked on top (7.4× on
its kernel) to 351 ms / 1.65× — remaining scalar excise-memcpy work
bounds it further, as predicted.
SQM *was* 2.3× slower until the AVX2 `mom` integration flipped it: the
FASM binary is now ~10% faster than gcc `-O3` (8.9 vs 9.8 ms) at a quarter
of the size. Lesson recorded, not exception claimed: hand-vectorizing the
single hottest kernel beat the compiler there; everywhere else the
vectorizer still wins. Sizes run 4–26× smaller across the board.

## Shared playbook (reuse for each port)

- Static BSS arena (`rb`/`rd`/`rq`), `write(2)`/`exit(2)` only, own entry.
- Shared includes (single source, all consumers byte-verified):
  `sqb_cell.inc` (cell/sweep/syndrome, sq2b+sqw),
  `rng.inc` (xoshiro256** + seed/rand helpers),
  `emit.inc` (emit_str/u64/f6/fdec, ratio, atoi, wallns, cycles,
  mem_eq — BSS contract: outbuf/outcur/numbuf/fdigits/tsbuf),
  `trit_codec.inc`, `rle_pack.inc`, `int_codec.inc`.
  ~1350 duplicated lines consolidated to ~410 (binaries gain
  ~0.5–0.9 KB of dead shared functions — documented tax, not a bug).
- C appels: args rdi,rsi,rdx,rcx,r8,r9; only rbx,rbp,r12-r15 survive calls.
- `emit_str` / `emit_u64` / `emit_fdec(N)` (exact-double digit extraction,
  guard digit + sticky, round-half-even) -> `emit_f6`, `emit_f2`.
- Signed C division/modulo = `idiv` (truncation) — never `div`.
  `%2==0` parity via TEST-bit works for negatives.
- `(uint64_t)(negative int)` wraps — plain 64-bit `add`/`imul` match C.
- `(uint8_t)(a + b)` full-int add truncated = low-byte add.
- `argv[1]` parsed with atoi semantics; defaults match each driver.
- Verify at 2-3 round counts, not just default (plus 2000 once).

## Pitfalls — assembler quirks (FASM 1.73.x, ELF64)

1. **Counter in a call-clobbered register.** Only rbx,rbp,r12-r15 survive
   a `call`. `seed_rng` counted warmups in `ecx` — `xoshiro` clobbers it,
   so it warmed up ~2 billion times (21 s runs, mid-stream RNG). Same
   class: O2's `okc` bit in `r11d` across a `mom` call that uses `r11`
   as s2 (442/1000 garbage). Audit every value live across a `call`.
2. **Byte load into the address register.** `mov al, [rax+rcx]` writes
   `al` — the low byte of the pointer itself. Killed exactly the
   strand-1 repairs. Use `dl` (or any non-address byte reg).
3. **Label typing by defining directive.** `rb`-defined labels read as
   bytes: `mov rax, [accA+24]` fails if `accA` is `rb`. Use `rq`/`rd`
   for qword/dword data, or explicit size prefixes. (Reg-indirect
   `[rbx+...]` always infers fine.)
4. **UTF-8 in comments poisons parsing.** A `─` in a comment broke the
   *next* line with a bogus error. Keep port sources ASCII-only.
5. **`rd` reserves, `dd` initializes.** `SCATLT rd 6,5,...` fails;
   `SCATLT dd ...` works. (`EQ` is also a reserved word.)
6. **Structure triage for new ports:** duplicate/overlapping local labels
   across scopes, unbalanced push/pop counts (odd pushes = aligned),
   `rep movsb` advances `rdi`/`rsi` (recompute addresses after), 32-bit
   `%` via `div r32` (zero `edx` first), `cmp`-then-`setcc` polarity —
   `setz` after `test eax,eax` means "eax==0"; check every one against
   its helper's 1-on-equal vs 1-on-different convention.
7. **`rep movsb` copies `[rsi]` into `[rdi]` — verify every copy's
   direction.** Phase 2 had all three raw copies backwards
   (`rdi=filebuf, rsi=e_raw`), silently overwriting the input with zeros
   round by round: totals exact, validations trivially passing, memcmps
   vacuous, RLE at exactly 4 bytes/round. Fingerprint of this bug class:
   aggregates look structurally perfect while content-sensitive checks
   (or downstream consumers) starve. Read every `rep movsb` as
   "source-rsi to dest-rdi" out loud once per file.
8. **Local-label typos jump somewhere valid.** `jnz .bdrl` instead of
   `jnz .bdl` assembled clean (both labels existed in scope) and
   ping-ponged bench sections forever — 100% CPU, zero output, no error.
   The assembler cannot catch this; after writing any loop nest, grep all
   local labels and confirm every jump target resolves to the intended
   one (Phase 2 cost hours on this single character).
9. **NEVER run edit and build in parallel.** Three times this session the
   assembler read the file before the edit landed, producing stale
   binaries whose behavior was then "analyzed" at length (including one
   phantom "still hangs" and one phantom "fixed"). Edit tool first,
   confirm, *then* build — sequentially, always. A same-size rebuild
   proves nothing; a behavior change proves the new binary ran.
7. **C numerical traps to replicate, not "fix":** `printf` args evaluate
   right-to-left (affects harness field assignment, not the real drivers
   which use statements); confirm-read counters increment even on failed
   checks; division-by-zero guards (`cnt ? a/b : 0.0`).
10. **Save before clobber, in that order.** `mov rbx, rdi` before
    `push rbx` saves the *new* value — the pop restores it and the
    caller's register is gone (Log v1 segfaulted two layers later with
    zero output; the direct-call probe passed because it never touched
    `rbx`). Pushes first, then move args into the saved registers.
11. **`vpbroadcastd ymm, r32` is EVEX-only.** FASM assembles it (to an
    EVEX prefix) without complaint; it SIGILLs on AVX2-only CPUs.
    Broadcast from an xmm instead (`movd xmm, r32` +
    `vpbroadcastd ymm, xmm` — VEX, genuinely AVX2). Any GPR-sourced
    256-bit broadcast deserves a second look at the encoding.
12. **`cdq` eats the `idiv` divisor.** `mov eax, ds1; cdq; idiv edx`
    divides by the *sign extension*, not `d` (here: divide-by-zero
    SIGFPE). Hold the divisor in another register across `cdq`.
13. **Quotient is not remainder.** `div` leaves both; saving `eax`
    when you meant `edx` silently rebuilds the data structure in a
    different-but-self-consistent order (SQ5 alloc scattered 0..31
    sequentially — every behavioral oracle green, only the dump
    differed). After any `div`, say out loud which half you keep.
14. **Never hand-memorize inexact decimal hex.** `0x4120…` is 524288,
    not 4096 (SQFH's `C_4096` was wrong by 128× and only timing
    noticed). Derive every non-exact decimal const at init via a
    single correctly-rounded int-ratio division (`num/den` with exact
    ints = identical to the C literal, provably). Powers of two and
    small ints as hex are fine; everything else goes through
    `mkconst`.
15. **Loop heads are entries AND back-edges.** One-shot setup placed
    AT the loop label (`xor r11d` at `.sloop:`) re-runs every
    iteration once anything else jumps there — infinite loop that
    assembles clean and passes a glance review (SQFH fast-path
    retrofit). Keep setup above the label in an entry stub; the
    label itself must be pure loop.
16. **Code assembled into a non-executable segment faults on fetch,
    and the RIP points at data.** Appending a function after the
    rodata directive (SQ4's `rep` landed past `segment readable`)
    builds clean and dies calling into literals. After any append
    or move, grep `^segment` and confirm every global label sits
    in the segment you think it does.
17. **Legacy SSE inside hot AVX-256 loops pays transition
    penalties.** `movhlps` has no VEX encoding; executing it with
    dirty upper ymm state costs ~70 cycles per transition —
    measured 30× on a fold kernel (76 ns → ~1.5 ns switching to
    `vpunpckhqdq`). In any 256-bit loop, every instruction must
    be VEX; audit with the microbench, not the eye.

## Pitfalls — methodology (learned the hard way)

1. **Unique binary names, always.** C and asm debug builds once shared
   `/tmp/opencode/sqm_dbg`, so the asm build overwrote the C build and
   "comparisons" matched the program against itself — including a
   "perfect" oracle that was just the C binary. Prefix everything
   (`CREL`, `CDBG`, `ADBG`) and embed a marker line in debug output.
2. **Verify the oracle, not just the dumps.** Per-round debug dumps can
   agree while the accumulated oracle differs (they read different
   storage — BSS temps vs registers). Always diff the final oracle too.
3. **Distrust "impossible" results; check the harness first.** A
   "diverging RNG" turned out to be argument-evaluation order in a
   throwaway test harness, not the port. Bisect with minimal standalone
   reproductions before touching port code.
4. **Counts are RNG-pure; values are logic.** Diverging event *counts*
   mean stream/seed/call-count bugs. Matching counts with wrong *values*
   mean logic bugs. The RNGSTATE-dump trick (post-phase state from both
   sides) separates them in one run.
5. **File the failing output.** Every `out.{gcc,musl,fasm}.txt` plus the
   `.s` assembly stays in-tree per variant, so regressions are diffable.
