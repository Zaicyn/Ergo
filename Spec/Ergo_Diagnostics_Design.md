# Ergo Diagnostics Design

## Philosophy

Warnings are allowed to be heuristic. Errors must remain provable.
The compiler should feel like an experienced numerical engineer looking
over your shoulder, not a mystical optimizer oracle.

> "What you wrote is what executes."

## Diagnostic Classes

| Class     | Meaning                        | Blocks compile |
|-----------|--------------------------------|----------------|
| **ERROR** | Proven incorrect               | Yes            |
| **WARNING** | Semantically dangerous       | No             |
| **PERF**  | Legal but performance-hostile  | No             |

Separation matters — ERROR is provable, WARNING is heuristic, PERF is
advisory. Users can suppress WARNING and PERF independently.

## Surface: Compiler vs Extension

Some diagnostics are compiler-side (parser, checker, codegen). Others are
better as IDE hints (VSCodium extension) because they need visual context
or are too noisy for build output.

| Diagnostic                    | Surface     | Class   |
|-------------------------------|-------------|---------|
| FP equality comparison        | Compiler    | WARNING |
| DO WHILE without EXIT         | Compiler    | WARNING |
| Division by near-zero         | Compiler    | WARNING |
| Large array passed by value   | Compiler    | WARNING |
| ALLOCATE inside loop          | Compiler    | WARNING |
| Unbounded loop invariant cond | Compiler    | WARNING |
| Branch divergence in GPU loop | Extension   | PERF    |
| SoA vs AoS layout hint        | Extension   | PERF    |
| Scatter contention estimate   | Extension   | PERF    |
| Warp occupancy estimate       | Extension   | PERF    |
| GPU extraction failure reason | Extension   | PERF    |
| Array memory footprint        | Extension   | PERF    |
| Integration stability pattern | Extension   | WARNING |
| Cancellation risk             | Extension   | WARNING |

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
Exception: comparison to 0.0 is acceptable (exact zero is representable).

### 2. DO WHILE Without EXIT

```
DO WHILE (.TRUE.)
  ! no EXIT anywhere in body
ENDDO
```

```
ERGO WARNING line 10:
  DO WHILE with invariant condition and no EXIT
  Loop will never terminate
```

Implementation: parser or checker, scan body for EXIT statement.
Not an error — infinite loops are valid for servers/simulations
when terminated externally (Ctrl-C, window close).

### 3. Division Safety

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
Conservative: only warn when no guard is visible, not when guard exists
on any path. False positives acceptable for warnings.

### 4. Large Array Pass-by-Value

```
CALL F(PARTICLES)    ← PARTICLES is REAL(30000000)
```

```
ERGO WARNING line 88:
  Large array 'PARTICLES' passed by value (120 MB estimated)
  Consider INOUT parameter or explicit view
```

Implementation: checker.py, estimate array size from declaration,
warn above threshold (e.g., 1 MB).

### 5. Allocation in Hot Loop

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

---

## Extension Diagnostics (VSCodium)

These run as IDE analysis, not during compilation. They provide inline
hints, hover information, and gutter markers.

### 6. Branch Divergence

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

### 7. SoA vs AoS Layout

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

### 8. Array Memory Footprint

Hover over array declaration:
```
STATIC REAL :: POS_X(MAXPART)    ← hover: "120 MB at MAXPART=30000000"
```

Gutter marker for total VRAM usage estimate per module.

### 9. GPU Extraction Failure

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
```

The compiler already reports these (`[spirv] Loop at line X not extracted:
disqualifying op`). The extension surfaces them inline with the source.

### 10. Scatter Contention Estimate

For grid scatter patterns:

```
GRID_DENSITY(CI, CJ, CK) := GRID_DENSITY(CI, CJ, CK) + 1
```

Hint:
```
PERF: Atomic scatter to 32^3 grid — ~900 particles per cell average
      Expected atomic contention: moderate
```

### 11. Integration Stability

Detect explicit Euler patterns:

```
X := X + DT * F(X)
```

```
WARNING: Explicit Euler integration detected
         Stability requires DT < 2/|eigenvalue_max|
         Consider monitoring for divergence
```

Advanced — needs pattern matching on the update structure.
Not for initial version.

---

## Integer Overflow Strategy

Default: wraparound (matches F77 behavior, fast).
Debug flag: `--checked-int` emits overflow traps.

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
CPU-only feature for debugging.

---

## Aliasing Rules

Ergo should stay restrictive:

- Arrays are never aliased unless explicitly declared
- Function parameters: IN (read-only), OUT (write-only), INOUT (read-write)
- No arbitrary writable aliasing through pointers
- Immutable views (when views are added) — read-only window into existing array

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
3. GPU extraction failure reasons in compiler output (already exists, just format better)

### Phase 2 (extension MVP)
4. Array memory footprint hover
5. GPU extraction failure inline hints
6. Branch divergence markers

### Phase 3 (extension full)
7. Scatter contention estimates
8. SoA/AoS layout hints
9. Division safety warnings
10. Integration stability detection

### Phase 4 (compiler maturity)
11. Allocation lifetime analysis
12. --checked-int debug mode
13. Range analysis for division guards
