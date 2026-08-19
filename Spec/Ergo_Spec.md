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

✅ **Arena-backed allocation:** ALLOCATABLE arrays are bump-allocated from a file-scope STATIC arena in the generated C. No libc, no syscalls — the arena lives in BSS, is zero-filled by the loader, and is 64-byte aligned.

✅ **DEALLOCATE is a no-op:** The arena is bump-only (LIFO would require a freelist; not in scope). A user writing `ALLOCATE; DEALLOCATE; ALLOCATE` in a loop will not recycle memory. Matches the "allocate once at startup, never free" pattern that ALLOCATABLE is for.

✅ **Arena size:** Default is 1 GiB. Override with `--arena-size <N>` (accepts K/M/G suffix). On exhaustion, the program aborts with a stderr message naming the requested and available bytes.

**Model name:** F77+Allocatable (strict, no hidden allocation)

**Implementation reference:** [Spec/Arena_Lowering_Brief.md](Arena_Lowering_Brief.md).

### Array Layout (Locked)

Multi-dimensional arrays are **column-major** (Fortran order): the first
subscript varies fastest in memory.

```
REAL :: A(m, n)     ! A(1,1) and A(2,1) are adjacent in memory
```

- **One convention on both sides of every boundary.** The C backend declares
  arrays with reversed dimensions and emits reversed subscripts
  (`A(i,j,k)` → `A[k-1][j-1][i-1]`); the SPIRV backend linearizes with the
  matching column-major formula. Host buffers are flat copies — both sides
  must agree on what `A(i,j)` means.
- **DATA initializers fill in Fortran order** (first subscript fastest):
  `DATA A / 1, 2, 3, 4 /` on `A(2,2)` gives `A(1,1)=1, A(2,1)=2, A(1,2)=3,
  A(2,2)=4`.
- **Why column-major:** Ergo sources write first-index-innermost loop nests
  (galaxy `DO K / DO J / DO I`, sq2core). Measured on RTX 2060
  (`work/gpu_audit/coalesce_bench`): an I-fastest walk over column-major
  storage coalesces identically to a K-fastest walk over row-major
  (~550 vs ~520 GB/s); either walk/storage mismatch costs ~20×. The
  convention is free — matching the walk to the storage is everything, and
  the compiler cannot reorder the programmer's loop nests.
- **JIT:** `JitLibrary.array_np` reshapes views with `order='F'`; flat
  buffers from `array()` are column-major.

---

### Part 3: Type System

✅ **Base types:** INTEGER, REAL, COMPLEX, LOGICAL, CHARACTER (fixed-length)

✅ **Integer kinds (Inc-2A):** INTEGER (32-bit, C `int`) and INTEGER*8
(64-bit, C `long long`). Only `*8` is accepted — `INTEGER*4` etc. are
parse errors. Kind rules follow Fortran:
- Mixed INTEGER/INTEGER*8 arithmetic → INTEGER*8 (widening wins among
  integer operands; REAL still wins overall)
- Implicit narrowing `INTEGER := <INTEGER*8 expr>` → **compile-time
  error** (use `INT(x)` explicitly)
- Implicit widening `INTEGER*8 := <INTEGER expr>` is allowed
- DO loop variables and bounds may be INTEGER*8 (required for 3^N ED
  state spaces at N ≥ 20, which overflow int32)
- 1-D arrays of INTEGER*8 are supported
- INTEGER*8 is **CPU-only**: GPU extraction of any loop touching int64
  values is rejected with a named diagnostic (the alternative would be
  silent i32 truncation in push constants / element types)

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

✅ **Case policy (ratified 2026-08-12):** *identifiers are
case-sensitive; keywords are case-insensitive; intrinsic dispatch is
case-insensitive.* `alpha` and `ALPHA` are different variables;
`DO`/`do` and `CALL ZERO`/`call zero` are the same construct.

✅ **Subroutine argument passing (A6, ratified 2026-08-12):**
Fortran-style by-reference. A SUBROUTINE dummy that is a scalar
lowers to a pointer — assignments to it copy out to the caller's
variable. Consequently, at the call site a written scalar dummy
requires a plain scalar variable: passing a literal, expression, or
array element to a dummy the subroutine writes is a compile-time
error (the checker names the argument). Read-only scalar dummies
accept any expression (the compiler copies it to a temporary).
Array dummies are by-reference as before; STATIC arrays as arguments
remain forbidden (Part 7). FUNCTION arguments are by-value and do
not copy out.

✅ **Backends (ratified 2026-08-12):** the IR codegen
(`core/ir_codegen.py`) is the supported backend. The legacy AST
codegen (`core/codegen.py`, reachable only via the Python API with
`use_ir=False`) is **deprecated**: it remains for dual-path golden
testing and prints a deprecation warning when selected.

✅ **Large local arrays (A1, 2026-08-13):** a local (non-STATIC) array
whose compile-time-known size exceeds 1 MB is **hoisted to
function-local C static storage** by the IR backend (an ERGO NOTE is
printed). Statics are zero-initialized and persist across calls —
this can only mask, never create, read-before-write bugs.
**Reentrancy constraint:** recursion into a function owning such an
array would share it, so the checker rejects recursion cycles
involving functions with hoisted locals (named error; recursion with
only small/ALLOCATABLE locals is unaffected). Unresolvable sizes keep
the batch-1 stack warning. The legacy backend keeps the warning only.

✅ **WRITE format audit (A4, ratified 2026-08-13):** the WRITE format
string lowers verbatim to C `fprintf`, so the supported set is
validated at compile time (checker; both backends share it) and
anything else is a **named compile-time error**, never a runtime
dice-roll. Supported: conversions `%d %i %x %X` (INTEGER/LOGICAL),
`%lld %lli` (INTEGER*8), `%f %F %e %E %g %G` (REAL), `%s`
(CHARACTER), `%%` literal; flags `- + 0 space #`; field width digits;
`.precision` digits. Rejected with named errors: `%n` (always),
dynamic `*`/`.*` width-precision, other length modifiers, unknown
conversions, conversion/argument count mismatch, and type mismatch
(`%d` vs REAL, `%f` vs INTEGER, `%d` vs INTEGER*8 — use `%lld`).

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


## Design Decision Summary (For Reference)

### The 16-Operator Constraint
**Why?** Discipline. Most "useful" languages sneak in 50+ operators. Ergo's 16 are minimal, orthogonal, and non-ambiguous.

### F77+Allocatable Memory Model
**Why?** Flexibility for runtime-sized systems (like particle counts from input files) while maintaining strict "no hidden allocation" rule. GPU-friendly because allocation is explicit and happens outside kernels.

### Comparison Chaining
**Why?** Mathematical readability (`1 < x ≤ 10` reads like math) without sacrificing determinism (desugars to AND at parse time, not runtime magic).

### Assignment is Statement-Only
**Why?** No side-effect expressions. Separates pure computation from state mutation. Makes SSA/IR generation trivial.

### Unary Minus Binds Looser Than `**`
**Why?** Matches Fortran/Python convention. Deterministic, no ambiguity. If user wants `(-5) ** 2 = 25`, they write parentheses.

### No String Concatenation Operator
**Why?** Ergo is "mathematical by default." Strings are secondary. Explicit CONCAT function makes memory behavior clear.

### No Intrinsic Allocates
**Why?** Caller controls memory. No surprise allocations in hot loops. GPU-friendly (kernels don't allocate).

---

## Specification Files

1. **Ergo_Spec.md** — Full language specification (this document: types, memory, AST, examples)
2. Grammar (EBNF) — now Part 5 of this document
3. Memory model — now Part 2 of this document; lowering detail in [Spec/Arena_Lowering_Brief.md](Arena_Lowering_Brief.md)
4. **Ergo_Intrinsic_Signatures_Complete.md** — Complete, authoritative intrinsic signatures (supersedes the first-draft intrinsics specification)
5. **MCL_Bootstrap_Strategy.md** — Phase-by-phase implementation plan (MCL-era document; Ergo rewrite pending)

---


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

## Ergo Language Design is COMPLETE and LOCKED ✅

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
- ✅ Bootstrap strategy (Python first, then self-hosting in Ergo)

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
- The generated code for any Ergo statement must contain exactly the stores the programmer wrote, plus loop variables

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

Array-level expressions (`A := B + C * D` where A, B, C, D are arrays) are **illegal** in Ergo.

The programmer must write explicit loops:
```
DO I = 1, N
  A(I) := B(I) + C(I) * D(I)
ENDDO
```

**Why (R6 — the rationale, for the numpy/MATLAB/Fortran-90 reader):**
an array expression forces the compiler to choose between fusing
(which changes semantics when arrays alias) and materializing a
temporary — and a temporary is a hidden allocation, which this
language does not do, ever. Every allocation in Ergo is visible:
STATIC arrays, the ALLOCATABLE arena, or nothing. The explicit loop
is not a workaround for a missing feature; it is the feature. It
makes exactly the stores you wrote, in the order you wrote them —
auditable, vectorizable by the C backend, and bit-reproducible by
construction. Physics stencils want explicit loops anyway; the only
thing the array expression bought was brevity, and brevity is not
worth a compiler that can accidentally become slow or silently
change your numerics.

Ergo supports two loop forms: counted (`DO I = A, B`) and conditional
(`DO WHILE condition`). Both support `CYCLE` (continue) and `EXIT` (break).
DO WHILE conditions must be boolean — no truthy integers.
Use `ELSEIF` (one word), not `ELSE IF`.

This rule exists because array expressions create an impossible choice:
1. **Fuse** the operations (no temporary) — changes semantics if arrays alias
2. **Create temporaries** — violates the no-hidden-allocation rule
3. **Restrict aliasing** — adds complexity with no benefit over explicit loops

Ergo chooses none of these. The explicit loop is auditable, vectorizable by the C backend, and creates exactly the stores the programmer wrote. The compiler's job is to lower what you wrote, not to decide what you meant.

### Expression Evaluation Order (Locked)

Expressions are evaluated with **standard mathematical precedence, strictly deterministic**.

Rules:
1. Operands are evaluated left-to-right within each precedence level
2. The compiler may not reorder floating-point operations in ways that change results (e.g., `(A + B) + C` must not become `A + (B + C)`)
3. Parentheses override precedence and are always respected
4. No speculative or parallel evaluation of subexpressions

This guarantees **bitwise reproducible results** across compilations and platforms (given the same libm). The same Ergo source with the same inputs produces the same floating-point output every time.

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

### Determinism Contract (x86)

Ergo guarantees bit-identical output across:
- Repeated runs of the same binary on the same hardware.
- Clean rebuilds of the same source on the same target triple with the
  same compiler version and feature flags.

This guarantee holds under the default build flags:
`-O3 -march=x86-64-v3 -ffp-contract=fast -fno-math-errno -std=c11`.
FMA is enabled by feature-level requirement (FMA3 is part of the
`x86-64-v3` baseline), not by an explicit `-mfma`. The same source
compiled twice with the same compiler version produces bit-identical
program output even though the binaries themselves may differ in
build-ID, timestamp, and similar non-semantic metadata.

The guarantee does **not** extend to:
- Cross-target builds (x86 vs ARM vs RISC-V). Each target has its own
  determinism contract per its own audit.
- Builds with `--cpu-fast-math`. This flag explicitly permits
  reassociation and non-NaN-preserving min/max; bit-identity is
  sacrificed for speed.
- Builds with `--gpu-fast-math`. On supported GPU backends this weakens
  FP guarantees (NVVM math intrinsic swap; SPIRV currently does not
  consume the flag — see Part 9.9 implementation status).
- Builds with different compiler versions (GCC 13 → GCC 14 may alter
  bit patterns even under strict flags). Pin the compiler version for
  long-term reproducibility.
- Builds on CPUs without FMA support (`-ffp-contract=fast` becomes a
  no-op). The `x86-64-v3` march requirement guarantees FMA; relaxing
  it requires its own audit.

Empirical basis: the recipe is validated by the V22 Squaragon work
documented in `Testing/V22/COMPILER_DETERMINISM.md`. V22 is a
hand-vectorized geometry primitive whose algebraic-zero residual
provides a sensitive determinism oracle — small drift becomes
detectable as a non-zero result. Under the recipe flags, the residual
is bit-exactly `0.0`. Under `-ffast-math`, it drifts to ~0.053 over
1M calls.

**Validation tooling:** the `ERGO_HASH_FINAL=1` environment variable
enables a runtime state-hash for regression validation. When set, the
compiled binary hashes a canonical sequence of GPU particle arrays
(POS_X, POS_Y, POS_Z, VEL_X, VEL_Y, VEL_Z, OMEGA_NAT) at exit and
prints `ERGO_FINAL_HASH=<16-hex-digits>` to stdout. See
`core/ir_codegen.py:_emit_final_hash_hook` for details. The hook fires
only when the program has GPU-resident state; CPU-only programs use
inline source-level hashes (see `tests/sq2core.ergo` for the
established pattern).

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

### 8.5 Tiled Dispatch (`--gpu-tile-size`)

With `--gpu-tile-size N` (N>0), an extracted kernel is dispatched in
tiles over its single device buffer; per-tile push constants
`_tile_base`/`_tile_hi` shift and bound the iteration space
(`i = gid + 1 + _tile_base; if (i <= _tile_hi)`).

**Quantization guarantee (locked):** the tile step is quantized to a
workgroup multiple (`QTILE = max(256, floor(N/256)*256)`), so tile `t`
group `g` covers exactly the elements of untiled group
`t·(QTILE/256) + g`. Reduction partials land in `[tile][acc][group]`
slots and the host ordered combine iterates in the same fixed order as
the untiled dispatch — **tiled results are bitwise identical to
untiled results**, for any requested tile size, including remainder
tiles. Tiling changes dispatch granularity, never numerics.

Segmented reductions and the coalesced multi-reduction readback refuse
tiling (whole-range dispatch) with a named diagnostic.

### 8.6 TILE_CLIP (Program-Maintained Clipmap)

A `STATIC INTEGER :: TILE_CLIP(NT)` array declared in the program gates
the tiled host dispatch loop: flag 0 = skip the tile's dispatch (stale
device values persist), nonzero = dispatch normally. One clip array is
shared by all tiled kernels (QTILE is uniform); tiles beyond the
declared size always dispatch. Skipped tiles in a tiled **reduction**
kernel are unsound (the ordered combine expects every tile's partials),
so clipping is refused there with a named warning.

Skip semantics are the program's contract: the program must guarantee
a skipped tile's outputs would not have changed above its own
tolerance. The framework for sound clip bounds (per solver class) is
`Spec/Ergo_Activity_Bounds.md`. Oracles: `tests/gpu_clipmap.ergo`
(bitwise, cone bound), `tests/gpu_clipmap_amp.ergo` (error-bounded,
amplitude envelope).

### 8.7 Ping-Pong Eligibility

An array is double-buffered (2× device buffer, `_pp_rd_offset` /
`_pp_wr_offset` push constants injected into index math) only when ALL
of the following hold (`compute_pingpong_arrays` in `core/ir_gpu.py` —
single source of truth for backend and host):

- exactly one kernel reads it and that kernel also writes it
- that kernel is dispatched inside a batched frame loop
- every other kernel touching it is write-only and runs before that
  frame loop (init-time)
- all qualifying arrays share one shape (one global element-offset pair)

Otherwise the array stays single-buffered. Rationale: cross-kernel
dataflow within a frame under double-buffering reads stale halves —
the eligibility rule exists precisely to make that failure
unrepresentable.

### 8.8 Streaming Intrinsics and Transfer Semantics

`CALL VK_STAGE` / `CALL VK_FETCH` (signatures in
`Spec/Ergo_Intrinsic_Signatures_Complete.md` Category 6) express
out-of-core streaming in Ergo: explicit host↔device slice transfers
with zero host-side array copies. Both are frame-draining
synchronization points (VK_STAGE drains only when the recording frame
has unsubmitted kernel writes that overlap). CPU builds lower them to
memmove, so streamed programs remain runnable CPU-only.

**Transfer granularity:** host-side writes to GPU-resident arrays are
tracked as runtime dirty intervals; uploads transfer only the dirty
range (`upload_at`). Unanalyzable cases fall back to whole-array
uploads — never under-approximated. Transfers never change values;
results are bitwise-identical regardless of transfer granularity.

**Device limits:** `maxStorageBufferRange` is queried at init and
asserted at buffer creation. Buffers larger than the limit are a
compile/startup error, not silent UB.

**INTEGER*8 on GPU:** extraction of any loop touching int64 values is
rejected with a named diagnostic. Index widths: global indices beyond
i32 are expressed as i32 tile-relative + i64 tile base.

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

**Implementation status (resolved 2026-07-21):** the gate above is now
wired. Extraction rejects SCATTER-classified loops to the CPU by default
(`extract_kernels(..., gpu_fast_math=False)`), and the SPIRV backend
raises if a SCATTER kernel ever arrives without the flag. Sort-by-GEN is
deterministic by default (CPU counting sort, stable by class); the GPU
histogram/scan/scatter path is retained under `--gpu-fast-math` with
documented nondeterminism. See `core/archive/changes.md` F66/F70/F73.

### 9.10 GPU Numeric Precision Policy

In f64 mode (the default), the SPIRV backend evaluates `SQRT` natively
in f64 (verified against `spirv-val`). All other GLSL.std.450
transcendentals — SIN, COS, TAN, ASIN, ACOS, ATAN, SINH, COSH, TANH,
EXP, LOG, LOG10, **and POW** (16/32-bit only in GLSL.std.450) — are
evaluated f64→f32→f64. Each affected kernel emits exactly one
compile-time warning naming the functions; expected deviation is ~1e-7
relative to the CPU path for those calls. Programs that need full f64
transcendentals on the GPU must use the CPU path (or restructure); the
CPU backend always computes in the declared precision.

---

## APPENDIX: Design Rationale (TL;DR)

Ergo is a **mathematical compute language** designed for physics simulation, GPU kernels, and HPC. It is not:
- A general-purpose language (no strings as first-class, no file I/O)
- A modern convenience language (no auto-reallocation, no garbage collection)
- A research language (no novel type systems, no advanced features)

Instead, Ergo is:
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

This is not Fortran. It's not Python. It's **Ergo:** the language for getting shit done in simulation.

---