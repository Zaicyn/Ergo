# SQW baseline + FASM port

Source: `benchmark/{sqw_cert.c,sqw_core.h,bench_sqw.c,SQW_DESIGN.md}` (+ shared
`common.h`). Cell comes from `../sqb_cell.inc` — this port added only the
recognition layer (FNV-1a word hash + finalizer, 4096-entry cache,
complement-paired refcounts, audit) and the cert driver.

## Baselines

- GCC `-O2` (`out.gcc.txt`): all 12 lines pass in ~92 ms — 256/256
  recognition, 214/214 refpair, 644/644 payload, 428/428 poison-failsafe,
  4942/5111 poisson repair, amplification 1.88.
- musl-static (`out.musl.txt`): byte-identical.

## FASM port (`sqw.asm` -> `sqw`, 8156 bytes, no libc)

129 ms best-of-5 (1.4× C — closest ratio yet, the shared AVX2 cell ops
fire throughout). Verified byte-identical at default 1500 and at 30.

Notable confirmations: 50%-duplication stream build (Fisher-Yates +
random half) reproduces memoization pressure exactly (skips fire,
O1 256/256); occupied-only event targeting via per-round occ_list;
REF/SYN/PAY/IDX rand01 thresholds 0.70/0.50/0.67; tomb_refs amplification
accounting; `%.2f` line via the shared fdec pattern.

Bugs caught: Phase-A cat chain read stale flags (`je` after `mov` can
never take — consume flags immediately), which zeroed REF rounds and
inflated IDX 428→642 (counts must sum-check: PAY+SYN+REF+IDX = rounds);
one wrong threshold constant (sq2b's 0.60 pasted where SQW needs 0.50);
two literal spacings (O5/O6) fixed by extracting exact strings from C.
