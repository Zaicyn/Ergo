# Hopf Handshake Bound (E1) Implementation Plan

**Goal:** Add bounded "recursion" as a static schedule to Ergo, per `Spec/Hopf_Handshake_Bound_Policy.md` and `min/ribosome/ERGO_FIX_FIRST_LIST.md` item E1.

## Design principle

The handshake is **not** general recursion. It is a compile-time-provable static schedule: endpoint A → mediator → endpoint B, depth ≤ 2, no runtime stack, no allocation. The compiler rejects anything that cannot lower to counted loops + fixed payload + oracle checks.

## Integration phases (from policy)

| Phase | Deliverable | Compiler change | Status |
|-------|-------------|-----------------|--------|
| 0 | Pattern-only handshakes using existing counted DO loops | None | Already possible |
| 1 | Static linter / analysis pass that recognizes handshake patterns and warns on violations | Add analysis module | **Done** |
| 2 | `VERIFY HANDSHAKE ...` directive form | Parser + checker | **Done** |
| 3a | Verifier-first hard checks: payload budget, MAXIT staticness, recursive helper cleanness | Linter | **Done** |
| 3b | Auto-emission of CONSERVE + ORACLE checks + parser acceptance → IR lowering | Parser + AST + IR builder + codegen | **Done** |
| 3c | `HANDSHAKE ... ENDHANDSHAKE` first-class AST/IR node (sugar over 3b lowering) | Parser + AST + checker + IR builder + codegen | **Done** |
| 3d | `VERIFY HANDSHAKE` directive lowers to the same emission as `HANDSHAKE` | IR builder promotion pass | **Done** |
| 4 | Certification suite with positive/negative oracles | Tests | In progress |

## Completed Phase 1 + 2

- Created `core/hhb_lint.py` — AST walker that validates marked handshake blocks.
- Added `VerifyHandshakeStmt` to `core/ast_nodes.py`.
- Extended `core/parser.py` to parse:
  ```ergo
  VERIFY HANDSHAKE <name> [DEPTH=N] [FRAME_BYTES=B] [MAXIT=M|PARAM] [CONSERVE ...]
  ```
- Wired the linter into `core/driver.py` and `core/__main__.py` so all
  compilations run the pass.
- Added `core/test_hhb_lint.py` positive/negative unit tests.

Recognition triggers on the `VERIFY HANDSHAKE` directive followed by a
`DO` loop or `IF` block.

Validation rules (per policy clauses 1–4, 7):

- **Fixed shape:** block contains at most two counted propagation stages separated by a mediator update; no fan-out; no mediator spawning mediator.
- **Counted loops only:** every iterative construct is a `DO` loop with compile-time-constant or PARAMETER bound and `MAXIT` semantics; no `DO WHILE` inside handshake.
- **No allocation:** `ALLOCATE`/`DEALLOCATE` inside the region is a hard error.
- **MAXIT staticness:** `MAXIT` must be an integer literal or a `PARAMETER`
  whose value is known at compile time.
- **Payload size:** explicit `PAYLOAD=(...)` declaration is checked against
  `FRAME_BYTES`; the ping-pong budget is `2 * FRAME_BYTES`. Unknown variables,
  non-static array dimensions, and `COMPLEX` payload members are hard errors.
- **No INTEGER*8 / COMPLEX in payload.**
- **CONSERVE invariants require explicit TOL:** `CONSERVE NORM TOL=1.0E-10`.
  A `CONSERVE` without `TOL` is a lint error. On violation the program aborts
  with a `HS_SCANFAIL`-style diagnostic; it never continues, clamps, or
  warns-and-proceeds.
- **No re-entry / rewind unless explicitly budgeted:** visited-flag pattern; rewind requires `MAX_REWIND = N` annotation.
- **Calls must be statically bounded:** subroutine/function calls are allowed
  only if the callee is defined in the same module and its body satisfies all
  HHB rules (counted loops only, no allocation, no do-while, etc.). Unknown
  or non-clean calls are rejected.
- **GPU-rejection criteria:** if `--target spirv` and the handshake cannot be fully unrolled (data-dependent activation beyond a branchless 0/1 mask, allocatables, dynamic bound), reject.

Output: named diagnostics (warnings in prototype mode, errors in certified mode).

## Phase 3b design decisions (set before emission code)

### Oracle evaluation semantics

Oracle checks are **target-local** floating-point comparisons at stage
boundaries. Tolerances are **per-(target, precision)** and must be justifiable
at the current precision:

- Under `--precision f64`, tight tolerances (e.g. `LIMIT=1.0E-12`) are valid.
- Under `--precision f32`, the linter rejects `LIMIT < 1.0E-6` for `REAL`
  oracles (and `TOL < 1.0E-6` for `CONSERVE`) with a hard error. A tolerance
  below the f32 precision floor would fire on rounding noise rather than a
  physical violation, so the author must choose a meaningful tolerance for the
  precision they are compiling for.
- The same source compiled for CPU vs GPU at the same precision may produce
  different oracle outcomes; this is expected and acceptable because oracles
  observe target-local state.

Silent cross-target divergence in a *verification* feature is worse than no
check, so precision floors are enforced by the linter as hard errors.

### CONSERVE failure policy

A violated `CONSERVE` invariant is a **hard abort** with a `HS_SCANFAIL`-style
diagnostic. The program never continues, never clamps the value, and never
warns-and-proceeds. Each `CONSERVE` declaration must carry an explicit
`TOL=`; defaulted tolerances are forbidden because a "conserved" norm checked
at f64 epsilon is a false-alarm generator on GPU f32.

### Checks must not perturb numerics

Emitted oracle/CONSERVE checks read state but must not reorder floating-point
operations in the compute path. The IR ordering with checks must be identical
to the ordering without checks. Validation: a golden test where a handshake
program and its hand-lowered equivalent produce bitwise-identical CSV output
per target.

### Oracle checks are boundary-only

`ORACLE` and `CONSERVE` checks fire only at stage boundaries, not mid-stage.
This preserves loop structure and keeps the check schedule deterministic.

## Proposed Phase 3 syntax (trimmed)

```ergo
HANDSHAKE <name>
    DEPTH=2
    FRAME_BYTES=256
    MAXIT=NTAU
    CONSERVE PARITY TOL=0.0
    CONSERVE NORM   TOL=1.0E-10

  PAYLOAD BOND = (R, E_TOT, W00, WMIN, PMIN, WMAX)

  STAGE 1: PARITY=1
    PROPAGATE PSI COUNT=NTAU
    DIAGNOSTIC E_TOT
    BUILD_MEDIATOR WG FROM PSI

  STAGE 2: PARITY=2
    PROPAGATE PSI COUNT=NTAU
    DIAGNOSTIC E_TOT
    BUILD_MEDIATOR WG FROM PSI

  ORACLE W0     VALUE= 1.0/PI*(1-2*(PARITY-1))  LIMIT=2.0E-3
  ORACLE WNORM  VALUE= 1.0                       LIMIT=1.0E-12
  ORACLE FRINGE VALUE= WMIN  P=PMIN              LIMIT=5.0E-2
ENDHANDSHAKE
```

The IR builder lowers this to:
- Static payload array (≤ 2 × FRAME_BYTES).
- Counted `DO` loops for each stage.
- Boundary checks for `CONSERVE` and `ORACLE`.
- `HS_SCANFAIL`-style abort on violation.
- No subroutine calls, no runtime stack.

## Files to touch

- `core/tokens.py` — add handshake keywords.
- `core/ast_nodes.py` — add `HandshakeStmt` / `VerifyHandshakeStmt`.
- `core/parser.py` — parse new syntax/directive.
- `core/checker.py` — validate HHB rules.
- `core/hhb_lint.py` — new static analysis module.
- `core/ir_builder.py` — lower Phase 3 node.
- Tests under `tests/` or `min/wigner/`.

## First test ladder (reuse existing physics)

1. `h2p_wig.ergo` — parity handshake (σg/σu).
2. `h2_wig.ergo` / `h4_wig.ergo` — singlet/triplet.
3. `df_radial2.ergo` — SCF handshake with loud SCANFAIL.
4. Negative controls: LCAO v1 failure, wrong exchange integrals.

## Completed test results

- `h2p_wig_hhb.ergo`: propagation-only handshake passes with explicit
  `PAYLOAD=(NRM)`; only an oracle warning remains (no WRITE inside the
  annotated loop).
- `df_radial2_hhb.ergo`: SCF handshake now passes with explicit
  `PAYLOAD=(ESUM, EDIFF)` and `MAXIT=NCYC`. The linter recursively verifies
  that the called subroutines/functions (`YZ`, `YKP`, `VOPN`, `SHOOT`,
  `NODEX`, `NNODE`, `LEGS`) contain only counted loops and no
  allocation/rewind/do-while constructs.
- `core/test_hhb_lint.py`: all unit tests pass, including new payload-budget,
  MAXIT-staticness, CONSERVE-with-TOL, ORACLE, and HANDSHAKE-block-syntax
  tests.
- `core/test_hhb_golden.py`: HANDSHAKE block and hand-lowered equivalent
  produce bitwise-identical output under both `--precision f64` and
  `--precision f32`.
- `min/wigner/hhb_handshake_block.ergo`: passing ORACLE example.
- `min/wigner/hhb_handshake_fail.ergo`: example that aborts with
  `HHB_SCANFAIL` and `exit(1)`.

## Completed since last update

- Added richer `HHB_SCANFAIL` diagnostics with `actual=`, `expected=`, and
  `tol=` values.
- Extended `core/test_hhb_golden.py` with a multi-stage `HANDSHAKE` block
  covering sequential counted stages + CONSERVE entry capture.
- Implemented `VERIFY HANDSHAKE` lowering: the IR builder now promotes a
  directive + following statement into a `HandshakeStmt`, reusing the same
  entry-capture and boundary-check emission.
- Field test A: added `VERIFY HANDSHAKE` annotation to
  `min/ribosome/ul18_full_slot_hhb.ergo`; smoke (`MAXFRAME=4800`) and full
  96 k-frame GPU f32 runs produce byte-identical output to the certified
  `min/ribosome/ul18_full_slot.csv`.
- Field test B: promoted the annotation to a true `HANDSHAKE ... ENDHANDSHAKE`
  block around the first `DO K = 1, NSLOT` pass in
  `min/ribosome/ul18_full_slot_hhb.ergo`; smoke and full 96 k-frame GPU f32
  runs again produce byte-identical output to the certified CSV.
- Diagnosed the `ul18_stag5.ergo` f32 SPIR-V hang: it occurs between frame
  500 and frame 1000, requires multiple working-tree compiler changes to
  reproduce, and is not caused by the `ergo_stream.h` buffer.  The root
  change is still being narrowed.
- Added `core/test_stag5_hang_regression.py`: compiles `ul18_stag5.ergo` with
  `MAXFRAME=1000` at f32 SPIR-V and asserts completion within 30 s.  It
  currently fails, serving as the guard for the fix.
- Added build-version stamping: every generated executable now embeds
  `git describe --dirty` and prints it at startup.
- Added timing comparison example: `work/timing_comparison/{manual,handshake}_staging.ergo`
  and `work/timing_comparison/run_comparison.py`.  CPU f64 and SPIR-V f32
  variants produce identical values; runtimes are within noise.

## Next action

- Finish narrowing the `ul18_stag5.ergo` f32 SPIR-V hang to the specific
  compiler change, fix it, and verify `core/test_stag5_hang_regression.py`
  passes.
- Run the full 144 k-frame validation of `min/ribosome/ul18_stag5_hhb.ergo`
  against the certified `min/ribosome/ul18_stag5.csv` once the hang is fixed.
- Otherwise the HHB feature is field-proven on `ul18_full_slot`: unit tests,
  multi-stage golden tests, annotation and block-form non-interference all
  pass with byte-identical output.
