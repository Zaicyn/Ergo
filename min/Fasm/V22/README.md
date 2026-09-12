# V22 (OG) baseline

Source: `Testing/V22/v22_compare.c` + `squaragon_v2.h` (copied here).
Driver compares scalar residual vs hand-SSE residual, 1M iters.
Flags: `-O3 -march=x86-64-v3 -ffp-contract=fast -fno-math-errno
-std=c11 -fwrapv`. musl build is `-static`.

## Outputs (`out.gcc.txt` vs `out.musl.txt`)

```
scalar:   r=0  ~26-28 ns/call  (sink=0)
hand-sse: r=0  ~11-13 ns/call  (sink=0)
speedup: hand-sse ~2.2x faster than scalar
```

Residual values bit-zero on both libcs — the algebraic-zero invariant
holds cross-libc. (ns/call varies run to run; the r=/sink= lines are
the deterministic oracle.)

## Assembly (`v22_compare.gcc.s` vs `.musl.s`)

Kernel codegen identical modulo label numbering. One real (trivial)
difference, in CLI parsing only: glibc inlines `atoi(argv[1])` as
`strtol`, musl emits `atoi@PLT`. Hot loops unaffected.

## Notes

- Known V22 bug is **deferred**, not investigated here.
- For the fixed-variant comparison, see `../Sq2B/README.md`.
