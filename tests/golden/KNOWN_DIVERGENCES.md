# KNOWN_DIVERGENCES — IR vs legacy codegen burn-down list

Companion to `tests/golden/run_golden.py` (A2). The harness compares
stdout byte-exact between the IR (supported) and legacy (deprecated)
codegen paths. Entries here are the *accepted* divergences; anything
the harness flags as NEW-DIVERGENCE is a bug to burn down.

## Standing divergences (by design or documented debt)

1. **COMPLEX.** IR path raises a clean error (F6); legacy lowers to
   `double _Complex` with unvalidated numerics. A corpus program using
   COMPLEX reports BUILD-DIVERGE (IR raises) — expected until COMPLEX
   is specified and implemented properly. No corpus program uses
   COMPLEX today.
2. **Ring intrinsics (RING_PREV/NEXT/SHIFT).** GPU-only, hard-coded
   32-lane assumption, absent from the CPU front end. A CPU-corpus
   program using them fails to build on both paths — excluded from the
   corpus by construction.
3. **GPU-only intrinsics (VK_STAGE/VK_FETCH).** CPU builds lower them
   to memmove (by design, deterministic); corpus programs are
   CPU-only, so this never triggers here.

## Fixed in this batch (2026-08-13) — previously diverging, now MATCH

- **Backslash escapes in string literals.** The lexer passed `\`
  through raw; legacy then let C's octal interpretation produce ESC
  bytes while the IR path escaped the backslash into literal text.
  buc_colony.ergo diverged at byte 0 (and its ANSI UI was silently
  broken on the IR path). Fixed at the lexer: `\n \t \r \\ \' \"
  \NNN` (octal) are processed at read time; unknown escapes are a
  named lexer error. Legacy learned `_c_str_escape` (WRITE formats and
  STRING literals), matching IR. Both paths now emit real ESC bytes
  and agree byte-exact.
- **INTEGER*8 in legacy codegen.** Was lowered to `double` with no
  `INT8` intrinsic (int64 programs couldn't build or printed garbage).
  Legacy now maps `INTEGER*8` → `long long` and `INT8(x)` →
  `(long long)(x)`; tests/int64.ergo agrees bitwise across paths.
- **Legacy loop-variable semantics (R5).** `for (int I = ...)`
  shadowed the user's variable, losing the post-loop value; and
  `ExitStmt` had no emitter case at all (EXIT silently dropped —
  found while goldening `tests/loopvar_after.ergo`). Legacy now
  iterates the user's variable (IR-matching Fortran semantics) and
  emits `break;` for EXIT.
- **Scalar subroutine dummies (A6, batch 1).** By-reference in both
  paths; tests/sub_scalar_ref.ergo is the golden.

## Latent source bugs caught by the A4 WRITE audit (fixed in source)

- `tests/waveform_cluster.ergo`: WRITE format had 43 conversions for
  42 arguments (trailing unmatched `%d` removed — would have read one
  garbage fprintf argument at runtime).
- `min/dbm/ab_pi_ledger_flip.ergo`: literal trailing `%` in a format
  (C-UB) → `%%` (output identical).
