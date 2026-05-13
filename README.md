# Ergo (MCL)

A mathematical compute language for physics simulation, GPU kernels, and HPC.

Ergo compiles to C via gcc. No runtime, no garbage collector, no hidden allocation.
Every memory operation is visible in the source. Every shape check is deterministic.
Performance is predictable because the language forbids the patterns that make it unpredictable.

## Quick Start

```bash
# Compile and run
python3 -m mcl tests/test_first.ergo -o test_first
./test_first

# Emit generated C (inspect what the compiler produces)
python3 -m mcl tests/test_first.ergo --emit-c

# Compile with fast-math (FP reassociation, aggressive vectorization)
python3 -m mcl tests/buc_colony.ergo -o buc_colony --fast-math
./buc_colony
```

Requirements: Python 3.10+, gcc, libm.

## What It Looks Like

```
IMPLICIT NONE
REAL :: x, y, z
INTEGER :: i

x := 5.0
y := 3.0
z := x + y * 2.0
PRINT z

DO i = 1, 10, 1
  x := x + 1.0
ENDDO

IF 0.0 < z ≤ 20.0 THEN
  PRINT z
ENDIF
```

Key differences from Fortran: `:=` for assignment, `=` for comparison, `ENDIF`/`ENDDO` (no labels), comparison chaining (`0.0 < z ≤ 20.0` desugars to AND at parse time), Unicode operators.

## Architecture

```
MCL source
  │
  ▼
Lexer (tokens.py)          Tokenize: Unicode operators, dotted keywords, literals
  │
  ▼
Parser (parser.py)         AST: precedence climbing, comparison chain desugaring
  │
  ▼
Checker (checker.py)       Type check, shape propagation, bounds, allocation tracking
  │
  ▼
CodeGen (codegen.py)       Emit C99: STATIC → static, ISHFT → <<, 1-based → 0-based
  │
  ▼
gcc -O2 -lm -std=c99      Optimize: constant folding, vectorization, jump tables
  │
  ▼
Executable
```

### Compiler Modules (2,602 lines total)

| Module | Lines | Purpose |
|--------|-------|---------|
| `tokens.py` | 136 | Token types, keywords enum |
| `lexer.py` | 227 | Single-pass tokenizer (Unicode, dotted keywords, reals) |
| `parser.py` | 635 | Recursive descent with precedence climbing |
| `ast_nodes.py` | 173 | Dataclass AST nodes |
| `symbols.py` | 102 | Symbol table with nested scopes, allocation state |
| `checker.py` | 541 | Type checker, shape propagation, bounds, alloc tracking |
| `codegen.py` | 644 | C99 code emitter |
| `driver.py` | 75 | Pipeline orchestration (lex → parse → check → codegen → gcc) |
| `errors.py` | 30 | Error classes with source location |
| `__main__.py` | 39 | CLI entry point |

## Language Features

### Operators (16)

```
Arithmetic:    **  *  /  +  -
Relational:    <  >  =  ≠  ≤  ≥
Logical:       .AND.  .OR.  .NOT.
Assignment:    :=
```

### Types

`INTEGER`, `REAL`, `LOGICAL`, `CHARACTER`. `REAL` maps to C `double`. Implicit promotion: INTEGER + REAL → REAL.

### Control Flow

```
IF condition THEN ... ELSEIF ... ELSE ... ENDIF
DO var = start, end, step ... ENDDO          (CYCLE to skip iteration)
SELECT CASE (expr) ... CASE val ... CASE DEFAULT ... ENDSELECT
RETURN, STOP
```

### STATIC Storage

File-scope variables with guaranteed direct addressing. No pointer wrapping, no indirection.

```
STATIC INTEGER :: TWHEAD(8, 2)
STATIC INTEGER :: SCATLT(32)
DATA SCATLT / 6, 4, 6, 2, 7, 4, 3, 0, ... /
```

Compiles to `static int SCATLT[32] = {6, 4, ...};` — resolved to `%rip`-relative addressing in assembly.

### PARAMETER Constants

Compile-time immutable values. The checker rejects reassignment and propagates the constant value into bounds checking.

```
PARAMETER REAL :: GRAVITY = 9.80665
PARAMETER INTEGER :: NMAX = 20000000
INTEGER, PARAMETER :: NCELLS = 1024
```

Compiles to `static const`. PARAMETER values feed the bounds checker — `A(NMAX + 1)` is caught at compile time.

### Intrinsics

| Category | Functions |
|----------|-----------|
| Scalar math | SIN, COS, TAN, EXP, LOG, LOG10, SQRT, ABS, MOD |
| Trig inverse | ASIN, ACOS, ATAN, ATAN2 |
| Hyperbolic | SINH, COSH, TANH |
| Comparison | MAX, MIN, CLAMP (branchless: fmin/fmax) |
| Bitwise | ISHFT, IEOR, IAND, IOR, NOT |
| Conversion | REAL(), INT(), CHAR(), ICHAR() (hardware cast, 1 cycle) |

### I/O

```
PRINT expr                                          ! stdout, auto-format
WRITE(*, "fmt") arg1, arg2                          ! stdout, printf-style
WRITE(0, "fmt") arg1                                ! stderr
WRITE(*, "text", "NO") arg1                         ! no newline (ADVANCE=NO)
FLUSH                                               ! fflush(stdout)
```

## Semantic Guarantees

### Performance Constitution

1. **No hidden allocation.** Every ALLOCATE/DEALLOCATE is visible in source.
2. **No implicit temporaries.** Array expressions (`A := B + C`) are illegal. Use explicit loops.
3. **No hidden indirection.** STATIC storage compiles to direct address computation.
4. **No evaluation reordering.** Strict left-to-right, no FP reassociation (bitwise reproducible).
5. **Numeric casts are hardware instructions.** `REAL()` → `cvtsi2sd`, `INT()` → `cvttsd2si`.
6. **CLAMP is branchless.** `fmin(fmax(x, lo), hi)` — 2 instructions under fast-math.
7. **IEEE semantics by default.** NaN-safe math. `--fast-math` is opt-in, never default.

### Static Analysis (Compile-Time Rejection)

The checker catches these errors before any C is generated:

| Category | What it catches |
|----------|----------------|
| Types | Undeclared variables, type mismatches, non-integer loop vars |
| Shapes | MATMUL inner dimension mismatch, result shape mismatch |
| Bounds | Constant index exceeds declared dimension, index < 1 |
| Allocation | Use before ALLOCATE, double DEALLOCATE, ALLOCATE on non-allocatable |
| Control flow | CYCLE outside DO loop, wrong argument counts |
| Constants | Reassignment of PARAMETER variables |

### Source-Mapped Diagnostics

The codegen emits `#line` directives in the generated C. When gcc catches something the checker missed, errors point to your Ergo source file and line number — not generated C.

```
gcc error → #line 42 "membrane.ergo" → you fix line 42 in your source
```

## Node Graph

Ergo's determinism makes it uniquely suited for visual node-graph programming. Every node is a pure function of its inputs, every edge is a typed value, execution order is determined by the DAG topology. No ambiguity.

The graph compiles to flat Ergo source via topological sort. This is not an interpreter — the graph IS the program.

```
  [CONST 5.0] ──► [a] Div ──► [x] Log10 ──► [out] Mul ──► [E]
  [CONST 200] ──► [b]          [CONST 61.5] ──► [b]
```

Compiles to typed SSA:
```
_div0 := 5.0 / 200.0
_log0 := LOG10(_div0)
_mul0 := _log0 * 61.5
```

The graph compiler emits **typed SSA form** — each node gets one assignment, each value flows through exactly one named edge. This is not a design goal imposed on the system; it's what falls out naturally when you topologically sort a DAG of pure deterministic functions.

### Features

- **45 built-in node types**: arithmetic, math intrinsics, comparison, logic, bitwise, conversion, control flow
- **Type-checked edges**: REAL (blue), INTEGER (green), LOGICAL (orange), CHARACTER (pink). Mismatches rejected at graph validation time.
- **Implicit promotion**: INTEGER → REAL edges are allowed. All other conversions require explicit nodes (ToInt, ToReal, ToChar, ToIChar).
- **Cycle detection**: Kahn's algorithm — cycles are structurally impossible in a valid graph.
- **JSON serialization**: human-readable, diffable, full round-trip fidelity.
- **Compilation**: Graph → Ergo source → C → executable. Same graph, same output, every time.

### Compilation Targets

| Target | Output | Use case |
|--------|--------|----------|
| Ergo source | `.ergo` file | Human-readable, editable |
| C executable | Binary via gcc | Standalone simulation |
| Tick function | Loop body | Simulation per-timestep |

See `Spec/Ergo_NodeGraph_Design.md` for the full specification including Nuklear integration, subgraphs, and tick-based simulation.

## Test Programs

| Program | Lines | What it tests |
|---------|-------|---------------|
| `test_first.ergo` | 19 | Arithmetic, loops, comparison chaining |
| `sq2core.ergo` | 160 | Squaragon V2 allocator (1.8ns/alloc, biology-inspired torus) |
| `sq3core.ergo` | 290 | Squaragon V3 refinement: integer-only fast path, bit-twiddle seam, SQ3VAL verifier |
| `buc_membrane_unit.ergo` | 203 | Nernst-Planck membrane physics, 5 experiments, CSV output |
| `buc_colony.ergo` | 443 | 64x32 cell grid: diffusion, division, death, ANSI visualization |

### Validation Results

- **sq2core**: 192 allocations, zone 1. Assembly verified: all `%rip`-relative, zero `->`, zero `malloc`.
- **sq3core**: same allocation result (192/zone 1), 0 SQ3VAL mismatches across all TINVAR entries. No FP ops in fast path; bit-pack exactly recoverable.
- **membrane unit**: Run 1 steady state PSI = -246.44 mV, ATP = 0.8777. Matches F77 to 4 decimal places.
- **colony**: Frame 10: 343 cells (WT:97, KO_msh:86, KO_mem:85, KO_tra:75). Exact match with F77 output.

## Repository Structure

```
Ergo/
  mcl/                    Python compiler package
    tokens.py               Token types and keywords
    lexer.py                Tokenizer
    parser.py               Recursive descent parser
    ast_nodes.py            AST node definitions (with source line tracking)
    symbols.py              Symbol table + allocation state + PARAMETER tracking
    checker.py              Type checker + shape propagation + constant propagation
    codegen.py              C99 code emitter (with #line directives)
    driver.py               Pipeline orchestration (--fast-math support)
    nodegraph.py            Node graph data model, validation, and compilation
    errors.py               Error/diagnostic classes
    __main__.py             CLI entry point
  tests/                  Ergo test programs
    test_first.ergo          Basic arithmetic and control flow
    sq2core.ergo             Squaragon V2 torus allocator
    sq3core.ergo             Squaragon V3 — integer-only fast path + SQ3VAL verifier
    buc_membrane_unit.ergo   Single-cell membrane physics
    buc_colony.ergo          Colony simulator with ANSI display
  Spec/                   Language specification (locked)
    MCL_Design_COMPLETE.md                Full language design + performance constitution
    MCL_Intrinsic_Signatures_Complete.md  Intrinsic function reference
    MCL_Bootstrap_Strategy.md             Implementation roadmap
    MCL_Quick_Reference.txt               One-page cheat sheet
    Ergo_NodeGraph_Design.md              Node graph specification
  allocator/              F77 reference implementation
    sq2core.f               Original Squaragon V2 allocator
  Cellular demos/         F77 reference implementations
    buc_membrane_unit.f     Original membrane unit test
    buc_colony.f            Original colony simulator
    MCLtranslation.md       Translation guide (physics + structure)
```

## Design Philosophy

Ergo is not a general-purpose language. It is a tool for expressing deterministic physical simulations where:

- Every allocation is visible
- Every shape check is deterministic
- Every operation is auditable
- Performance is predictable

The compiler's job is to lower what you wrote, not to decide what you meant.
