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

- Known V22 bug is **characterized** (second pass, 2026-09-11), not
  fixed here per plan.md ("debug the port against the buggy reference
  rather than fixing it here"): `sq2_cell_alloc`
  (`Testing/V22/squaragon_v2_dna.h:270`) maps id→bin via the
  unbalanced `sq2_viviani_scatter_full` and silently drops the item
  when that strand is full — no fallback scan, no error return.
  Measured: scatter histogram at total=256 is
  [20,44,18,28,56,32,30,28] against ring 32 → bins 1 and 4 overflow
  by 12+24 → **220/256 allocated, 36 silent rejects (14.1%)**,
  matching the comparison doc's "~14%" and its "0 (220)" V22 row.
  Root cause per the doc: the dynamic Viviani loads don't balance;
  suggested fix (unimplemented): baked SCATLT or overflow fallback.
  Sq2B supersedes with proofread-and-refuse semantics, so the OG fix
  is a deliberate open decision, not an oversight.
- For the fixed-variant comparison, see `../Sq2B/README.md`.
