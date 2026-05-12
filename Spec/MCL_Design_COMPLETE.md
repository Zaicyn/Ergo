# MCL Language Design — COMPLETE & LOCKED

## Status: Ready for Implementation ✅

This document confirms that **all language design decisions are locked**. The compiler can now be built.

---

## What Is Locked

### Part 1: Operators (16 Total)

✅ **Arithmetic:** `**`, `*`, `/`, `+`, `-`  
✅ **Relational:** `<`, `>`, `=`, `≠`, `≤`, `≥`  
✅ **Logical:** `.AND.`, `.OR.`, `.NOT.`  
✅ **Assignment:** `:=`  
✅ **Unary:** `+`, `-` (prefix, right-associative)

**Precedence:** Fixed. No ambiguity.  
**Special behavior:** Comparison chaining (`1 < x ≤ 10` → desugars to AND tree at parse time).  
**Exclusions:** No `//` (concatenation), no `++`/`--`, no bitwise.

---

### Part 2: Memory Model

✅ **Two kinds of arrays:**
- Static: `REAL :: A(10, 20)` (compile-time constant shape)
- Allocatable: `REAL, ALLOCATABLE :: A(:,:)` + `ALLOCATE(A(m, n))` (runtime shape)

✅ **Core rule:** No intrinsic ever allocates. Output arrays are caller-allocated.

✅ **No automatic reallocation:** Assignment never changes shape. Shape mismatch is error.

✅ **ALLOCATE/DEALLOCATE are statements:** `ALLOCATE(C(m, p))` is a statement, not an expression.

**Model name:** F77+Allocatable (strict, no hidden allocation)

---

### Part 3: Type System

✅ **Base types:** INTEGER, REAL, COMPLEX, LOGICAL, CHARACTER (fixed-length)

✅ **Type coercion:**
- INTEGER + REAL → REAL (promotion)
- COMPLEX + anything → COMPLEX
- INTEGER ** INTEGER (negative exponent) → **Compile-time error** (must use REAL)

✅ **No implicit allocation on type mismatch.** Shape errors are errors.

---

### Part 4: Intrinsic Functions

✅ **Complete signature list** with shape propagation rules:
- Scalar math: SIN, COS, EXP, SQRT, ABS, MOD, MAX, MIN
- Vector reduction: SUM, PRODUCT, DOT_PRODUCT, NORM2
- Array operations: MATMUL, TRANSPOSE, RESHAPE (all caller-allocated output)
- String functions: LEN, INDEX, CONCAT (fixed-length)
- Array inspection: SIZE, SHAPE

✅ **Memory contract:** Every intrinsic explicitly states whether output is:
- Stack (scalar return)
- Caller-allocated (array return)
- Error (if size cannot be determined)

---

### Part 5: Grammar (EBNF)

✅ **Precedence climbing algorithm** — formally specified  
✅ **Comparison chain desugaring** — happens at parse time  
✅ **Assignment protection** — rejects `y := x := 5`  
✅ **All statement types:** IF, DO, FUNCTION, SUBROUTINE, DECLARE, ASSIGN

---

### Part 5b: Line Continuation

✅ **`&` at end of line joins with next line.** Pre-processed before tokenization.  
Trailing `&`, optional whitespace, newline, and leading whitespace on the next line are replaced with a single space.

```
DATA A / 1, 2, &
         3, 4 /

PARAMETER REAL :: LONG_NAME = &
  3.14159265358979
```

---

### Part 6: Semantics

✅ **Unary minus binds looser than `**`:** `-5 ** 2 = -25` (not `25`)  
✅ **Assignment is statement-only:** No side-effect expressions  
✅ **Comparison chaining is real:** `1 < x ≤ 10` is sugar for `(1 < x) .AND. (x ≤ 10)`  
✅ **No magic shape inference:** If shapes don't match, compiler rejects  

---

## What Is NOT in This Language

❌ **String concatenation operator** (`//` is not an operator; use CONCAT function)  
❌ **Implicit allocation** (no "helpful" compiler allocation of arrays)  
❌ **Garbage collection** (deterministic memory, explicit DEALLOCATE)  
❌ **Operator overloading** (operators are fixed, no user-defined operators)  
❌ **Method syntax** (no `.` for methods; use function calls)  
❌ **Increment/decrement** (no `++` or `--`)  
❌ **Ternary operator** (no `? :`)  
❌ **Dynamic typing** (types are static and checked at compile time)  
❌ **Exception handling** (no try/catch; errors are compile-time or assertion failures)  

---

## Compiler Phases (Implementation Roadmap)

### Phase 1: Lexer & Parser (Week 1)
- [ ] Tokenize all 16 operators, keywords, identifiers, literals
- [ ] Implement precedence-climbing parser
- [ ] Desugar comparison chains at parse time
- [ ] Build AST
- [ ] Reject assignment chaining and other illegal patterns

**Deliverable:** Parser that takes MCL source → AST (no errors = valid syntax)

### Phase 2: Type Checker & Semantic Analysis (Week 2)
- [ ] Type inference and checking
- [ ] Symbol table (variable and function declarations)
- [ ] Shape propagation for array operations
- [ ] Intrinsic function resolution
- [ ] Memory model validation (no unallocated arrays used)

**Deliverable:** Validated AST with type information and shape constraints

### Phase 3: Intermediate Representation (Week 2-3)
- [ ] Convert AST to IR (simple imperative form or LLVM-like)
- [ ] Flatten control flow into explicit labels and jumps
- [ ] Track allocation and deallocation points

**Deliverable:** IR suitable for code generation

### Phase 4: Backend Code Generation (Week 3-4)
- [ ] Emit C code (readable, auditable)
  - OR: Emit x86-64 assembly (advanced)
  - OR: Emit SPIRV for GPU kernels
- [ ] Link against system malloc/free for ALLOCATE/DEALLOCATE
- [ ] Test that generated code compiles and runs

**Deliverable:** Executable binary or object files

### Phase 5: Testing & Validation (Week 4-5)
- [ ] Unit tests (lexer, parser, type checker)
- [ ] Integration tests (real physics kernels)
- [ ] Performance validation (compare to F77)
- [ ] Memory audit (no memory leaks, no hidden allocations)

**Deliverable:** Passing test suite, real kernel working correctly

---

## Success Criteria

You will know MCL is ready when:

1. ✅ **Parser is deterministic:** Same input → Same AST every time
2. ✅ **Type checker is strict:** Rejects shape mismatches, type errors, and unallocated arrays
3. ✅ **No hidden allocations:** Every ALLOCATE/DEALLOCATE is visible in generated code
4. ✅ **Real kernel works:** Sanity hopfion update step compiles and runs faster than F77
5. ✅ **Code is auditable:** Generated C or assembly is readable and matches MCL semantics exactly

---

## Design Decision Summary (For Reference)

### The 16-Operator Constraint
**Why?** Discipline. Most "useful" languages sneak in 50+ operators. MCL's 16 are minimal, orthogonal, and non-ambiguous.

### F77+Allocatable Memory Model
**Why?** Flexibility for runtime-sized systems (like particle counts from input files) while maintaining strict "no hidden allocation" rule. GPU-friendly because allocation is explicit and happens outside kernels.

### Comparison Chaining
**Why?** Mathematical readability (`1 < x ≤ 10` reads like math) without sacrificing determinism (desugars to AND at parse time, not runtime magic).

### Assignment is Statement-Only
**Why?** No side-effect expressions. Separates pure computation from state mutation. Makes SSA/IR generation trivial.

### Unary Minus Binds Looser Than `**`
**Why?** Matches Fortran/Python convention. Deterministic, no ambiguity. If user wants `(-5) ** 2 = 25`, they write parentheses.

### No String Concatenation Operator
**Why?** MCL is "mathematical by default." Strings are secondary. Explicit CONCAT function makes memory behavior clear.

### No Intrinsic Allocates
**Why?** Caller controls memory. No surprise allocations in hot loops. GPU-friendly (kernels don't allocate).

---

## Files You Now Have

1. **Language_Design_Spec_v1_UPDATED.md** — Full language specification (types, memory, AST, examples)
2. **MCL_EBNF_Grammar.md** — Formal grammar (parser-ready)
3. **MCL_Memory_Model_Decision.md** — Memory model rationale and rules
4. **MCL_Intrinsics_Specification.md** — First draft of intrinsic functions (old version)
5. **MCL_Intrinsic_Signatures_Complete.md** — Complete, authoritative intrinsic signatures (NEW)
6. **MCL_Implementation_Roadmap.md** — Phase-by-phase implementation plan

---

## Next Step: Code the Lexer

You have everything you need to start implementation. Here's the minimal path:

### Week 1 Goal: Lexer + Parser (Python Bootstrap)

**Write the MCL compiler in Python first.** Why?
- Fast iteration
- Easy debugging
- Validates language design
- After it works, rewrite in MCL itself (self-hosting)

```
Day 1-2: Lexer (tokenize MCL source)
Day 2-3: Parser (build AST with precedence climbing)
Day 3-4: Error checking (reject illegal patterns)
Day 4-5: C codegen (emit readable C code)
```

See **MCL_Bootstrap_Strategy.md** for detailed week-by-week plan and code stubs.

**Pick a language for the bootstrap compiler:**
- **Python** ✅ (Recommended: fast to write, easy to debug)
- **C** (Faster runtime, but slower to develop)
- **Rust** (Memory-safe, but overkill for bootstrap)

**Recommendation:** Start in Python. Once bootstrap works, rewrite compiler in MCL itself. This validates the entire language design in the most rigorous way possible.

---

## Final Locked Decisions (DeepSeek Review) ✅

DeepSeek pointed out one missing piece: **SHAPE function memory semantics.**

**SHAPE now locked to caller-allocated output:**
```
REAL :: A(10, 20)
INTEGER :: dims(2)       ! Caller allocates with size = RANK(A)

dims := SHAPE(A)         ! SHAPE writes into pre-allocated dims
```

**Added RANK intrinsic:**
```
RANK(A)  → INTEGER       ! Number of dimensions
SHAPE(A) → INTEGER(:)    ! Array of dimension sizes (caller-allocated)
SIZE(A)  → INTEGER       ! Total number of elements
```

**Also clarified:**
- CONCAT truncation: Compile-time error if result length exceeds declared length (constant case)
- COMPLEX exponentiation: Negative exponents are allowed for COMPLEX type (exception to INTEGER**negative error)

---

## MCL Language Design is COMPLETE and LOCKED ✅

**No more design decisions.** Everything is specified:

- ✅ 16 operators (all precedences locked)
- ✅ F77+Allocatable memory model (explicit ALLOCATE, no hidden allocation)
- ✅ Type system (static types, shape checking, coercion rules)
- ✅ Intrinsic functions (complete signature table with shape propagation, including ZERO)
- ✅ Grammar (EBNF, parser-ready)
- ✅ Semantics (unary minus, comparison chaining, assignment-as-statement)
- ✅ STATIC storage and performance constitution (Part 7)
- ✅ GPU execution model (Part 8: buffer state, atomics, loop fusion)
- ✅ IR loop classification (Part 9: FLOW-rooted taxonomy — INJECTIVE/FLOW/SHIFT/REDUCTION/SCATTER)
- ✅ Bootstrap strategy (Python first, then self-hosting in MCL)

**You are ready to build.**

---

---

## Part 7: STATIC Storage and Performance Constitution

### STATIC Declarations

STATIC variables are file-scope, program-lifetime storage with direct addressing.

```
STATIC INTEGER :: TWHEAD(8, 2)
STATIC INTEGER :: SCATLT(32)
DATA SCATLT / 6, 4, 6, 2, ... /
```

**Semantics (locked):**
1. Global storage duration — allocated once at program load
2. Single canonical instance — no copies, no shadowing
3. Address is a link-time constant — resolved by the linker, not computed at runtime
4. No implicit pointer wrapping — the compiler may not introduce indirection layers
5. Direct access in generated code — no base pointer, no struct-of-arrays wrapper

**Codegen guarantee:** `STATIC` declarations lower to C file-scope `static` variables. Access compiles to `%rip`-relative or absolute addressing. No `->`, no `*ptr`, no indirection.

### STATIC Aliasing Rule

STATIC arrays are **non-aliasing**. Specifically:
- STATIC storage must never be passed as a function/subroutine parameter
- Subroutines access STATIC state directly by name, not through arguments
- This eliminates the aliasing escape that would force conservative optimization

If a subroutine needs to operate on STATIC data, it references it directly. The data's address is known; passing it through a pointer adds nothing but aliasing risk.

### No Implicit Temporaries

No expression, intrinsic, or assignment may introduce heap allocation or implicit array temporaries.

- Array expressions (`A := B + C * D`) are not supported for arrays — use explicit loops or caller-allocated intrinsics
- Intrinsics that return arrays (MATMUL, TRANSPOSE) write into caller-allocated output
- The generated code for any MCL statement must contain exactly the stores the programmer wrote, plus loop variables

This is the performance constitution: **the language cannot accidentally become slow.**

### Numeric Conversion Rules

Type conversions are primitive hardware operations, not function calls.

| Conversion | Syntax | C Lowering | Hardware |
|------------|--------|------------|----------|
| `REAL(x)` | `INTEGER -> REAL` | `(double)(x)` | `cvtsi2sd` (1 cycle) |
| `INT(x)` | `REAL -> INTEGER` | `(int)(x)` | `cvttsd2si` (1 cycle) |

**Locked guarantees:**
- No runtime dispatch, no precision ambiguity, no promotion chains
- Single-step, side-effect-free conversion with no allocation and no call boundary
- The compiler may not route these through runtime helpers

### Bitwise Intrinsics

| Intrinsic | Signature | C Lowering |
|-----------|-----------|------------|
| `ISHFT(i, shift)` | `INTEGER, INTEGER -> INTEGER` | `i << shift` or `(unsigned)i >> -shift` |
| `IEOR(a, b)` | `INTEGER, INTEGER -> INTEGER` | `a ^ b` |
| `IAND(a, b)` | `INTEGER, INTEGER -> INTEGER` | `a & b` |
| `IOR(a, b)` | `INTEGER, INTEGER -> INTEGER` | `a \| b` |
| `NOT(i)` | `INTEGER -> INTEGER` | `~i` |

These are zero-overhead: they compile to single CPU instructions.

### CLAMP Intrinsic

```
X := CLAMP(X, lo, hi)
```

| Intrinsic | Signature | C Lowering |
|-----------|-----------|------------|
| `CLAMP(x, lo, hi)` | `REAL, REAL, REAL -> REAL` | `fmin(fmax(x, lo), hi)` |
| `CLAMP(x, lo, hi)` | `INTEGER, INTEGER, INTEGER -> INTEGER` | `x < lo ? lo : (x > hi ? hi : x)` |

**Guaranteed branchless lowering when possible.** This is a primitive intrinsic, not syntactic sugar for if/then. The compiler must not emit branch-based clamping when the target supports `fmin`/`fmax` instructions.

Rationale: Clamping appears 14+ times in the colony physics (ion concentrations, membrane potential, mesh integrity). Each instance is 2 branches × N cells × 50 ticks × 2000 frames = 400M unnecessary branches eliminated.

### Array Expression Rule (Locked)

Array-level expressions (`A := B + C * D` where A, B, C, D are arrays) are **illegal** in MCL.

The programmer must write explicit loops:
```
DO I = 1, N
  A(I) := B(I) + C(I) * D(I)
ENDDO
```

MCL supports two loop forms: counted (`DO I = A, B`) and conditional
(`DO WHILE condition`). Both support `CYCLE` (continue) and `EXIT` (break).
DO WHILE conditions must be boolean — no truthy integers.
Use `ELSEIF` (one word), not `ELSE IF`.

This rule exists because array expressions create an impossible choice:
1. **Fuse** the operations (no temporary) — changes semantics if arrays alias
2. **Create temporaries** — violates the no-hidden-allocation rule
3. **Restrict aliasing** — adds complexity with no benefit over explicit loops

MCL chooses none of these. The explicit loop is auditable, vectorizable by the C backend, and creates exactly the stores the programmer wrote. The compiler's job is to lower what you wrote, not to decide what you meant.

### Expression Evaluation Order (Locked)

Expressions are evaluated with **standard mathematical precedence, strictly deterministic**.

Rules:
1. Operands are evaluated left-to-right within each precedence level
2. The compiler may not reorder floating-point operations in ways that change results (e.g., `(A + B) + C` must not become `A + (B + C)`)
3. Parentheses override precedence and are always respected
4. No speculative or parallel evaluation of subexpressions

This guarantees **bitwise reproducible results** across compilations and platforms (given the same libm). The same MCL source with the same inputs produces the same floating-point output every time.

Rationale: Simulation science requires reproducibility. A cell colony that produces different population dynamics on different compiler versions is useless for validation. The slight performance cost of strict evaluation order (preventing reassociation optimizations) is acceptable — the C backend at `-O2` still vectorizes loop bodies, which is where the real performance lives.

Note: The `--cpu-fast-math` flag may relax this rule for workloads where reproducibility is less important than speed. When enabled, the compiler may reassociate, fuse multiply-adds, and use non-NaN-preserving min/max. This must be opt-in, never default.

### IEEE Semantics for Math Intrinsics

By default, all math intrinsics follow IEEE 754 semantics:
- `CLAMP`, `MIN`, `MAX` use `fmin`/`fmax` which propagate NaN correctly
- `SQRT` of negative values is a runtime error, not silent NaN
- Division by zero behavior follows C99 rules

Under `--cpu-fast-math`, these constraints are relaxed:
- `CLAMP` may lower to `maxsd`/`minsd` (2 instructions, NaN not preserved)
- `MIN`/`MAX` may use non-NaN-preserving comparisons
- The compiler may fuse multiply-add operations

---

## Part 8: GPU Execution Model

### 8.1 Buffer State Machine

All arrays mapped to GPU memory participate in a compiler-managed state machine.

**States:**

| State | Meaning |
|-------|---------|
| UNINITIALIZED | Memory allocated, contents undefined |
| ZEROED | Fully initialized to zero |
| WRITTEN | Fully written by a kernel or host operation |
| READABLE | Safe for read access (barrier completed) |

**Transitions:**

- `ALLOCATE(A)` → UNINITIALIZED
- `CALL ZERO(A)` → ZEROED (CPU: `memset`, GPU: `vkCmdFillBuffer` / `cudaMemsetAsync`)
- `A(I) := ...` inside parallel loop → WRITTEN
- Completion of write + barrier → READABLE

**Barrier insertion rule:** The compiler inserts a synchronization barrier when a buffer transitions from WRITTEN/ZEROED to being read by a subsequent operation, and no ordering guarantee exists.

- Vulkan: `vkCmdPipelineBarrier`
- CUDA: stream synchronization or event dependency

No barrier is required when operations are recorded in the same command buffer with inherent execution ordering, or when writes are followed by writes (no read dependency).

**Correctness guarantee:** No read of a buffer observes partially completed writes from a prior operation. This preserves the deterministic semantics defined in Part 7.

### 8.2 Atomic Insertion Rules (Scatter Semantics)

A parallel loop may contain writes where multiple iterations target the same index:

```
GRID(CI, CJ, CK) := GRID(CI, CJ, CK) + 1.0
```

This creates a write conflict under parallel execution.

**Lowering rules:**

If a loop is classified as SCATTER (see Part 9) and contains accumulation `A(idx) := A(idx) ⊕ value`, the compiler must:

1. **Default mode (strict):** Serialize the loop. Results are identical to sequential execution. Bitwise reproducibility preserved.
2. **`--gpu-fast-math` mode:** Emit atomic operations (`atomicAdd`, `atomicMin`, etc.). Accumulation order is undefined but numerically stable. Results are not bitwise identical to sequential execution.

**CPU backend:** Always sequential execution (matches existing semantics).

**GPU backend (default):** Serialize scatter loops unless `--gpu-fast-math` is enabled.

**GPU backend (`--gpu-fast-math`):** Emit `atomicAdd` for `+`, `atomicMin`/`atomicMax` for `MIN`/`MAX`. CAS loop for unsupported operations.

**Formal rule:** If a parallel loop contains non-unique writes, the compiler must either serialize execution or emit atomic operations with explicitly defined numerical semantics. Silent data races are never permitted.

### 8.3 Loop Fusion Rules

**Goal:** Minimize kernel launches and global memory traffic.

**Fusion candidate pattern:**

```
DO I = 1, N
  A(I) := f(B(I), C(I))
ENDDO

DO I = 1, N
  D(I) := g(A(I), E(I))
ENDDO
```

**Fusion conditions (ALL required):**

1. **Same iteration space:** Both loops have identical bounds.
2. **No cross-iteration dependencies:** No loop-carried dependencies in either loop.
3. **No aliasing:** All written arrays are distinct. (Guaranteed for STATIC by design.)
4. **Local producer-consumer:** `A(I)` written in loop 1, read as `A(I)` (same index) in loop 2. NOT `A(I-1)` or `A(I+1)`.
5. **No side effects between loops:** No I/O, ALLOCATE/DEALLOCATE, or calls with unknown effects.

**Fused result:**

```
DO I = 1, N
  temp := f(B(I), C(I))
  D(I) := g(temp, E(I))
ENDDO
```

Intermediate array `A` may be eliminated. On GPU: single kernel, intermediate lives in registers, no global memory roundtrip. The barrier between the original WRITE(A) and READ(A) is eliminated because the operation becomes intra-thread.

**Non-fusable cases:** Aliased arrays, different loop bounds, scatter operations, intermediate result used elsewhere.

**Correctness guarantee:** Fusion must not change evaluation order within an iteration or violate floating-point determinism (Part 7).

### 8.4 Integration with Existing Guarantees

These rules preserve all constraints from Parts 1-7:

- No hidden allocation (buffer management is compiler-managed, not language-visible)
- Deterministic evaluation (sequential semantics are the default)
- No implicit temporaries (register-level intermediates from fusion are not visible at the language level)

**New guarantee:** Parallel execution is an implementation detail. Program semantics are identical to sequential execution unless `--gpu-fast-math` is enabled.

---

## Part 9: IR Loop Classification — FLOW as Root Primitive

### 9.1 Purpose

The compiler classifies every `DO` loop to drive parallelization, atomic insertion,
barrier placement, and fusion eligibility.

### 9.2 Core Principle: FLOW

Every element in a simulation has somewhere to go. Particles move to grid cells.
Ions cross membranes. Mass redistributes across meshes. The index mapping that
determines where each element lands is **FLOW** — the fundamental operation of
the language.

FLOW is a data-dependent remapping: each iteration writes to a location determined
by the physics. The compiler's job is to determine how much it can prove about
that remapping, and choose an execution strategy accordingly.

### 9.3 Definitions

For a loop `DO I = L, U` with body `BODY(I)`:

- `W(I)` = set of memory locations written in iteration `I`
- `R(I)` = set of memory locations read in iteration `I`
- `g(I)` = the index function for each write `A(g(I))`

### 9.4 Dependence Classification

The compiler analyzes each write index `g(I)` and classifies the loop's
**dependence structure**. These are refinements of FLOW — they describe how
much the compiler can prove about where the data goes.

#### INJECTIVE

The compiler proves that `g(I)` is an injective (one-to-one) function of the
loop variable. Every iteration writes to a unique location.

```
∀ I ≠ J: W(I) ∩ W(J) = ∅  (proven by compiler)
```

Detection: `g(I)` is an affine expression `a*I + b` where `a ≠ 0` and no
integer division is involved. Affine analysis extracts coefficients; non-zero
loop-variable coefficient proves injectivity.

```
DO I = 1, N
  A(I) := B(I) + C(I)      ! g(I) = I — trivially injective
ENDDO

DO I = 1, N
  A(2*I) := B(I)            ! g(I) = 2*I — injective (stride 2)
ENDDO

DO I = 1, N
  A(N - I + 1) := B(I)      ! g(I) = -I + N + 1 — injective (stride -1)
ENDDO
```

#### FLOW (unresolved)

The index is data-dependent — derived from a runtime array load — but the
pattern is structurally a permutation. Each element flows to its destination.
The compiler cannot prove injectivity, but the programmer asserts non-collision
by the structure of the computation.

```
∀ I ≠ J: W(I) ∩ W(J) = ∅  (asserted, not proven)
```

Detection: `g(I)` depends on an array LOAD (e.g., `A(P(I))` where `P` is a
permutation/index array). No read-modify-write of the target array.

```
DO I = 1, N
  A(P(I)) := B(I)           ! P maps particles to grid cells
ENDDO
```

This is the canonical simulation operation: transport, remapping, scatter-free
redistribution. FLOW is not a fallback — it is the default regime of physics
kernels. INJECTIVE is the special case where the compiler can see the
streamlines.

#### SHIFT(k)

The loop reads and writes the same array at a known constant offset. Iteration
`I` depends on the result of iteration `I - k`.

Detection: For a write `A(f(I))` and read `A(h(I))` of the same array, both
`f` and `h` are affine with the same loop-variable coefficient, and their
constant terms differ by `k`.

```
DO I = 2, N
  A(I) := A(I - 1) + B(I)   ! shift k=1: write at I, read at I-1
ENDDO
```

This is a cross-iteration dependency. Not parallelizable as MAP, but the
dependency distance is known and constant. Future optimization: wavefront
scheduling or pipeline execution.

#### REDUCTION

A scalar accumulator is read and written across iterations. The loop computes
an aggregate (sum, product, min, max) over the iteration space.

Detection: A non-temporary scalar is read before written in the loop body
(accumulator pattern).

```
DO I = 1, N
  total := total + A(I)     ! scalar accumulator
ENDDO
```

#### SCATTER

The flow has broken — multiple iterations may write to the same location, or
the compiler cannot rule it out and the pattern includes read-modify-write.

```
∃ I ≠ J: W(I) ∩ W(J) ≠ ∅  (possible or proven)
```

Detection: Write index is data-dependent AND the target array is both read and
written at that index (accumulation at runtime index). Or: write index is
constant. Or: integer division in the index expression (non-injective).

```
DO I = 1, N
  GRID(IDX(I)) := GRID(IDX(I)) + 1.0    ! read-modify-write at runtime index
ENDDO

DO I = 1, N
  A(I / 2) := B(I)          ! floor division — collisions at I=1,2
ENDDO
```

### 9.5 Decision Procedure

For each write `A(g(I))` in a loop body:

1. Extract affine expression from `g(I)`:
   - If affine with non-zero loop-var coefficient and no division → **INJECTIVE**
   - If affine with zero loop-var coefficient (constant index) → **SCATTER**
   - If affine extraction fails (non-affine, array LOAD in index):
     - If no read-modify-write of target array → **FLOW**
     - If read-modify-write of target array → **SCATTER**
2. For INJECTIVE writes, check same-array reads:
   - If same array read at different affine offset → **SHIFT(k)** where `k` is the offset difference
3. For scalar accumulators (read-before-write) → **REDUCTION**
4. Multiple writes checked independently. Most restrictive classification applies.

### 9.6 Execution Mapping

Dependence classification maps to execution strategy:

| Dependence | Execution | Parallel | Atomics | Fusion | Deterministic |
|------------|-----------|----------|---------|--------|---------------|
| INJECTIVE | MAP — 1 thread per iteration | Yes | No | Yes | Yes |
| FLOW | MAP — gather/scatter kernel | Yes (asserted) | No | Yes | Yes |
| SHIFT(k) | Sequential (wavefront future) | No (default) | No | No | Yes |
| REDUCTION | Staged reduce (warp shuffle) | Staged | No | No | Yes |
| SCATTER | Sequential or atomic | No (default) | Yes (`--gpu-fast-math`) | No | Yes (if serialized) |

### 9.7 Affine Analysis

The compiler uses `AffineExpr` to extract index structure:

```
AffineExpr:
    coeffs: dict[Symbol, int]   # Symbol = (name, kind) where kind is LOOP_VAR or PARAMETER
    constant: int
```

Operations: add, subtract, multiply by constant. Division is outside the affine
language — any division in the index expression causes affine extraction to fail,
which falls through to FLOW or SCATTER classification.

Examples:
- `I` → `AffineExpr({I: 1}, 0)`
- `2*I + 5` → `AffineExpr({I: 2}, 5)`
- `N - I + 1` → `AffineExpr({I: -1, N: 1}, 1)`
- `P(I)` → extraction fails (array LOAD) → FLOW or SCATTER

### 9.8 Alias Interaction

STATIC arrays are non-aliasing by design (Part 7). Two distinct STATIC arrays never alias.

ALLOCATABLE arrays may alias if passed through subroutine parameters. If aliasing
cannot be ruled out, conservatively classify as SCATTER.

### 9.9 Determinism Guarantee

**Default mode:** All loops produce results identical to sequential execution.
INJECTIVE and FLOW are parallel-safe. SHIFT and SCATTER are serialized.
REDUCTION uses deterministic staged reduction.

**`--gpu-fast-math` mode:** SCATTER may use atomic operations with non-deterministic
accumulation order. Only allowed if the operation is associative or the user
accepts numerical variation.

**Implementation status:** as of this writing, the SPIRV backend emits atomics
unconditionally for any SCATTER kernel with read-modify-write at a runtime
index. The `--gpu-fast-math` gate described above is plumbed through the
backend constructor but not consulted at the atomic-emission site. Resolution
(wire the gate to match this spec, vs. update this section to match the
unconditional code) is open.

---

## APPENDIX: Design Rationale (TL;DR)

MCL is a **mathematical compute language** designed for physics simulation, GPU kernels, and HPC. It is not:
- A general-purpose language (no strings as first-class, no file I/O)
- A modern convenience language (no auto-reallocation, no garbage collection)
- A research language (no novel type systems, no advanced features)

Instead, MCL is:
- **F77-inspired:** Simple, deterministic, auditable
- **GPU-ready:** No hidden allocations, explicit memory
- **Math-first:** Operators are mathematical, syntax reads like specs
- **Strict:** Types are static, memory is explicit, shapes are checked

**Philosophy:** Get the core so tight that micro-optimizations aren't needed. Discipline over convenience.

**Result:** A language where:
- Every allocation is visible
- Every shape check is deterministic
- Every operation is auditable
- Performance is predictable

This is not Fortran. It's not Python. It's **MCL:** the language for getting shit done in simulation.

---

## The Real Achievement

You didn't just design a language. You **closed the design loop.**

No "we'll figure it out later." No ambiguous corners. Every decision documented, justified, and locked.

That's rare. Most language designs have a 20% "TODO: decide later" section that balloons to 80% of the implementation effort.

Not this one.

You have a specification that a competent developer could hand to a team and say: "Build this compiler. Every decision is already made."

That's the mark of good design: not cleverness, but **completeness with discipline**.

---

## Next Action

**Start the lexer.** Spend the next 5 days tokenizing MCL. After that, the parser writes itself.

You've got this.

