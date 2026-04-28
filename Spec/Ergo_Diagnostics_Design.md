# Ergo Diagnostics Design

## Philosophy

Warnings are allowed to be heuristic. Errors must remain provable.
The compiler should feel like an experienced numerical engineer looking
over your shoulder, not a mystical optimizer oracle.

> "What you wrote is what executes."

WARNING/PERF diagnostics must not alter generated code.
Diagnostic passes cannot influence optimization legality.

ERROR diagnostics are part of the language contract.
WARNING and PERF diagnostics may evolve between compiler versions.

## Diagnostic Classes

| Class     | Meaning                        | Blocks compile |
|-----------|--------------------------------|----------------|
| **ERROR** | Proven incorrect               | Yes            |
| **WARNING** | Semantically dangerous       | No             |
| **PERF**  | Legal but performance-hostile  | No             |

Separation matters — ERROR is provable, WARNING is heuristic, PERF is
advisory. Users can suppress WARNING and PERF independently.

## Suppression Syntax

```
!$SUPPRESS WARNING FP_EQUALITY
IF X = 0.0 THEN

!$SUPPRESS PERF BRANCH_DIVERGENCE
DO I = 1, NPART
```

Scoped suppression:
```
!$PUSH_SUPPRESS FP_EQUALITY
  ... code where exact FP comparison is intentional ...
!$POP_SUPPRESS
```

Without suppression syntax, users fight the compiler once projects scale.

## Surface: Compiler vs Extension

Some diagnostics are compiler-side (parser, checker, codegen). Others are
better as IDE hints (VSCodium extension) because they need visual context
or are too noisy for build output.

| Diagnostic                    | Surface     | Class     |
|-------------------------------|-------------|-----------|
| FP equality comparison        | Compiler    | WARNING   |
| DO WHILE without EXIT         | Compiler    | WARNING   |
| Division by near-zero         | Compiler    | WARNING   |
| Unmodified loop variable      | Compiler    | WARNING   |
| Large array implicit copy     | Compiler    | WARNING   |
| ALLOCATE inside loop          | Compiler    | WARNING   |
| GPU aliasing in parallel loop | Compiler    | ERROR     |
| PARAMETER integer overflow    | Compiler    | ERROR     |
| Branch divergence in GPU loop | Extension   | PERF      |
| SoA vs AoS layout hint        | Extension   | PERF      |
| Scatter contention estimate   | Extension   | PERF      |
| Warp occupancy estimate       | Extension   | PERF      |
| GPU extraction failure reason | Extension   | PERF      |
| Array memory footprint        | Extension   | PERF      |
| Sort order preservation       | Extension   | CORRECTNESS |
| Integration stability pattern | Extension   | WARNING   |
| Cancellation risk             | Extension   | WARNING   |
| Mixed continuous/discrete     | Extension   | WARNING   |
| Ring coherence monitor        | Extension   | DEBUG     |
| Determinism / FP reassociation| Extension   | WARNING   |

---

## Compiler Diagnostics (Immediate)

### 1. Floating-Point Equality

```
IF X = 0.1 THEN    ← WARNING
```

```
ERGO WARNING line 42:
  Direct REAL equality comparison may be unstable
  Consider tolerance comparison: ABS(X - 0.1) < TOL
```

Implementation: checker.py, flag `==` and `≠` between REAL operands.
No exception for 0.0 — `SIN(PI) = 0.0` is a common trap. Suppress
with `!$SUPPRESS WARNING FP_EQUALITY` when exact comparison is intentional.

### 2. DO WHILE Without EXIT

```
DO WHILE (.TRUE.)
  ! no EXIT anywhere in body
ENDDO
```

```
ERGO WARNING line 10:
  DO WHILE with invariant condition and no EXIT
  Loop may never terminate
```

Implementation: parser or checker, scan body for EXIT statement.
Heuristic only — presence of EXIT suppresses the warning even if
termination cannot be proven. Not an error — infinite loops are valid
for servers/simulations terminated externally.

### 3. Unmodified Loop Variable

```
DO WHILE (ITER < MAX_ITER)
  ! body never modifies ITER or MAX_ITER
ENDDO
```

```
ERGO WARNING line 45:
  Loop exit condition depends on 'ITER', 'MAX_ITER'
  Neither is modified in the loop body
```

Implementation: checker.py, scan loop body for assignments to variables
appearing in the condition. Catches a class of "logically bounded but
actually infinite" loops.

### 4. Division Safety

```
X := A / B
```

where B has no prior guard (no `IF B ≠ 0` or `MAX(B, epsilon)` in scope).

```
ERGO WARNING line 55:
  Division by potentially zero value 'B'
  No prior guard detected in scope
```

Implementation: simple dataflow — track whether divisor has been guarded.
Conservative: only warn when no guard is visible. False positives
acceptable for warnings. Users can suppress or add `ASSERT(B > 0)` to
prove safety to the compiler.

### 5. Large Array Implicit Copy

```
CALL F(PARTICLES)    ← PARTICLES is REAL(30000000)
```

```
ERGO WARNING line 88:
  Large array 'PARTICLES' potentially copied (120 MB estimated)
  Consider INOUT parameter or explicit view
```

Implementation: checker.py, estimate array size from declaration,
warn above threshold (e.g., 1 MB).

Note: Ergo arrays should always pass by reference/view unless explicitly
copied. The warning catches cases where the ABI might introduce a copy.

### 6. Allocation in Hot Loop

When ALLOCATE exists in the language:

```
DO I = 1, N
  ALLOCATE(TMP(1000))
ENDDO
```

```
ERGO WARNING line 52:
  ALLOCATE inside loop body
  Potential catastrophic allocator overhead
```

Implementation: checker.py, flag ALLOCATE inside any DO/DO WHILE body.

### 7. GPU Aliasing in Parallel Loops (ERROR)

```
SUBROUTINE UPDATE(INOUT A, INOUT B)
  DO I = 1, N
    A(I) := A(I) + B(I)
  ENDDO
END
```

If A and B could be the same array, the GPU extraction is invalid
(read/write races between threads).

```
ERGO ERROR line 33:
  GPU-extracted loop: INOUT arrays 'A' and 'B' may alias
  Parallel execution requires provably non-aliased arrays
```

Implementation: checker.py, verify that all INOUT arrays in a
GPU-extractable loop are distinct declarations. If the compiler cannot
prove non-aliasing, extraction is blocked with an ERROR.

### 8. PARAMETER Integer Overflow (ERROR)

```
PARAMETER INTEGER :: X = 2147483647 + 1
```

```
ERGO ERROR line 5:
  Compile-time integer overflow in PARAMETER expression
```

Compile-time overflow is always provable and always an error.
Runtime overflow follows the --checked-int flag.

---

## Extension Diagnostics (VSCodium)

These run as IDE analysis, not during compilation. They provide inline
hints, hover information, and gutter markers.

### 9. Branch Divergence

Detect loops with per-element conditionals that break warp uniformity:

```
DO I = 1, NPART
  IF IAND(FLAGS(I), PFLAG_CRYSTAL) ≠ 0 THEN    ← PERF hint
    CYCLE
  ENDIF
```

Inline hint:
```
PERF: 31% of particles may take early exit (COAST mode)
      Warp utilization ~69% — consider sorting by mode
```

Implementation: extension analyzes FLAG checks in GPU-extracted loops,
cross-references with LUT statistics (FLOW_MODE distribution).

### 10. SoA vs AoS Layout

When the extension detects struct-like access patterns:

```
POS_X(I) := ...
POS_Y(I) := ...
POS_Z(I) := ...
```

Hint (positive reinforcement):
```
PERF: SoA layout detected — optimal for GPU coalesced access
```

Or if interleaved access is detected:
```
PERF: Mixed access pattern on arrays A, B, C
      GPU threads may generate 3 separate cache line loads
```

### 11. Array Memory Footprint

Hover over array declaration:
```
STATIC REAL :: POS_X(MAXPART)    ← hover: "120 MB at MAXPART=30000000"
```

Gutter marker for total VRAM usage estimate per module.

### 12. GPU Extraction Failure

When a loop can't be GPU-extracted, show why inline:

```
DO I = 1, N
  CALL SOME_FUNC()    ← PERF: GPU extraction blocked — function call
ENDDO
```

Or:
```
DO I = 1, N
  TOTAL := TOTAL + X(I)    ← PERF: GPU extraction blocked — cross-iteration
ENDDO                              dependency on 'TOTAL'
                                   Hint: use REDUCE_SUM(TOTAL)
```

The compiler already reports these. The extension surfaces them inline
with the source, plus suggested transformations where possible.

### 13. Scatter Contention Estimate

For grid scatter patterns:

```
GRID_DENSITY(CI, CJ, CK) := GRID_DENSITY(CI, CJ, CK) + 1
```

Hint:
```
PERF: Atomic scatter to 32^3 grid — ~900 particles per cell average
      Expected atomic contention: moderate
```

### 14. Sort Order Preservation (CORRECTNESS)

When SORT_BY_GEN is used, verify that downstream operations preserve
the sort order required for warp shuffle correctness:

```
SORT_BY_GEN at line 210 establishes ring order for shuffle coupling.
Loop at line 245 scatters particles by density — ring order may be lost.
Warp shuffle at line 280 assumes ring-adjacent threads share a warp.
```

This is a CORRECTNESS issue, not just PERF — broken sort order means
ring coupling produces wrong physics (shuffling with random neighbors).

### 15. Integration Stability

Detect explicit Euler patterns:

```
X := X + DT * F(X)
```

```
WARNING: Explicit Euler integration detected
         Stability requires DT < 2/|eigenvalue_max|
```

Also detect mixed continuous/discrete updates on the same variable:

```
OMEGA := OMEGA + K * DT      ← continuous term
OMEGA := OMEGA * 0.5          ← discrete factor in same timestep
```

```
WARNING: Mixed continuous/discrete update on 'OMEGA'
         Discrete factor 0.5 may violate explicit Euler stability
         Consider substepping or implicit correction
```

### 16. Ring Coherence Monitor (DEBUG)

When hopfion ring coupling is active, hover over SORT_BY_GEN or
RING_NEXT calls to see ring health:

- Winding number Q (should be 1 for stable rings)
- Mean OMEGA across the ring
- Spillover threshold proximity

Debug visualization, not a diagnostic — lives in the extension's
debug overlay.

### 17. Determinism Diagnostics

Detect patterns that may produce nondeterministic results:

- Unordered reductions (parallel sum with FP reassociation)
- Race-prone scatter (multiple threads writing same index)
- Non-associative reductions under --fast-math

```
WARNING: Parallel reduction may produce nondeterministic FP results
         due to reassociation order
```

Core to Ergo's identity as a deterministic simulation language.

---

## Integer Overflow Strategy

Default: wraparound (matches F77 behavior, fast).
PARAMETER expressions: always checked (compile-time overflow is an ERROR).
Debug flag: `--checked-int` emits overflow traps for runtime arithmetic.

```bash
python -m mcl --checked-int --target spirv ...
```

In checked mode, every integer arithmetic op gets a post-check:

```c
int result = a + b;
if ((b > 0 && result < a) || (b < 0 && result > a))
    ergo_trap_overflow(__LINE__);
```

GPU kernels: checked mode not available (no trap mechanism in SPIRV compute).
CPU-only feature for debugging. Extension can show PERF hints for GPU index
calculations involving large constants without bounds checks.

---

## Aliasing Rules

Ergo should stay restrictive:

- Arrays are never copied implicitly — pass by reference/view
- Function parameters: IN (read-only), OUT (write-only), INOUT (read-write)
- No arbitrary writable aliasing through pointers
- Immutable views (when views are added) — read-only window into existing array
- GPU-extracted loops: all INOUT arrays must be provably non-aliased (ERROR if not)

This is what makes Fortran fast. Preserve it.

---

## Graph / Code Semantic Parity

Golden rule: **Graph compiles to canonical Ergo text first.**

Never directly lower graph → C/SPIRV independently. The text representation
is the single source of truth. The graph is a view, not an alternative IR.

If the graph representation ever diverges from what the text would produce,
that's a critical bug — not a feature.

---

## Implementation Priority

### Phase 1 (next few sessions)
1. FP equality warning (checker.py, ~20 lines)
2. DO WHILE without EXIT warning (parser.py, ~10 lines)
3. Division safety warning (checker.py, ~40 lines)
4. Unmodified loop variable warning (checker.py, ~30 lines)
5. PARAMETER integer overflow error (checker.py, ~15 lines)
6. GPU extraction failure formatting (already exists, improve messages)

### Phase 2 (extension MVP)
7. Array memory footprint hover
8. GPU extraction failure inline hints with transformation suggestions
9. Branch divergence markers
10. Sort order preservation correctness checks
11. Mixed continuous/discrete update warnings

### Phase 3 (extension full)
12. Scatter contention estimates
13. SoA/AoS layout hints
14. Integration stability detection
15. Ring coherence debug overlay
16. Determinism diagnostics

### Phase 4 (compiler maturity)
17. GPU aliasing ERROR (needs alias analysis)
18. Allocation lifetime analysis
19. --checked-int debug mode
20. Range analysis for division guards
21. Diagnostic suppression syntax (!$SUPPRESS / !$PUSH / !$POP)
