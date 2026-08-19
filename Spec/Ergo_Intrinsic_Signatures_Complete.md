# Ergo Intrinsic Function Signatures (Complete Reference)

## Overview

This is the authoritative list of every built-in function in Ergo. Each entry specifies:
- **Signature:** Function name, argument types, return type
- **Shape propagation:** How input shapes determine output shape
- **Memory:** Caller allocates, stack return, or error
- **Semantics:** What it does
- **Status (A3, 2026-08-13):** implementation status — `CPU+GPU`
  (both backends; GPU transcendental note in Ergo_Spec.md §9.10),
  `CPU` (host only), `GPU` (device kernels; a CPU fallback is noted
  where one exists), `planned` (named compile-time error today),
  `removed`. This column is the answer to "wait, does X exist?" — a
  feature that exists but isn't ruled here is a bug in this document.

This is used by the compiler's type checker to:
1. Validate argument types
2. Infer output shape
3. Check assignment shape compatibility: `C := FUNC(args)` → compiler verifies `shape(C) == shape(FUNC(...))`

---

## Category 1: Scalar → Scalar (Pure Math, No Allocation)

All of these take one or more numeric scalars and return a scalar. No allocation. Stack return.

### Trigonometric Functions

| Function | Signature | Return Type | Semantics | Status |
|----------|-----------|------------|-----------|--------|
| SIN | `SIN(x: REAL) → REAL` | REAL | Sine in radians | CPU+GPU |
| COS | `COS(x: REAL) → REAL` | REAL | Cosine in radians | CPU+GPU |
| TAN | `TAN(x: REAL) → REAL` | REAL | Tangent in radians | CPU+GPU |
| ASIN | `ASIN(x: REAL) → REAL` | REAL | Arcsine, result in [-π/2, π/2] | CPU+GPU |
| ACOS | `ACOS(x: REAL) → REAL` | REAL | Arccosine, result in [0, π] | CPU+GPU |
| ATAN | `ATAN(x: REAL) → REAL` | REAL | Arctangent, result in [-π/2, π/2] | CPU+GPU |
| ATAN2 | `ATAN2(y: REAL, x: REAL) → REAL` | REAL | Two-argument arctangent. Result in [-π, π]. Handles quadrants correctly. | CPU+GPU |

### Exponential & Logarithmic

| Function | Signature | Return Type | Semantics | Status |
|----------|-----------|------------|-----------|--------|
| EXP | `EXP(x: REAL) → REAL` | REAL | e^x | CPU+GPU |
| LOG | `LOG(x: REAL) → REAL` | REAL | Natural logarithm (ln) | CPU+GPU |
| LOG10 | `LOG10(x: REAL) → REAL` | REAL | Base-10 logarithm | CPU+GPU |
| SQRT | `SQRT(x: REAL) → REAL` | REAL | Square root. x must be ≥ 0. | CPU+GPU |
| SQRT | `SQRT(z: COMPLEX) → COMPLEX` | COMPLEX | Complex square root | planned (both backends raise, A3) |

### Hyperbolic Functions

| Function | Signature | Return Type | Semantics | Status |
|----------|-----------|------------|-----------|--------|
| SINH | `SINH(x: REAL) → REAL` | REAL | Hyperbolic sine | CPU+GPU |
| COSH | `COSH(x: REAL) → REAL` | REAL | Hyperbolic cosine | CPU+GPU |
| TANH | `TANH(x: REAL) → REAL` | REAL | Hyperbolic tangent | CPU+GPU |

### Absolute Value & Sign

| Function | Signature | Return Type | Semantics | Status |
|----------|-----------|------------|-----------|--------|
| ABS | `ABS(x: REAL) → REAL` | REAL | Absolute value of real | CPU+GPU |
| ABS | `ABS(x: INTEGER) → INTEGER` | INTEGER | Absolute value of integer | CPU+GPU |
| ABS | `ABS(z: COMPLEX) → REAL` | REAL | Magnitude of complex number: sqrt(real²+imag²) | planned (both backends raise, A3) |
| SIGN | `SIGN(x: REAL, y: REAL) → REAL` | REAL | Return \|x\| with sign of y | CPU+GPU |
| SIGN | `SIGN(x: INTEGER, y: INTEGER) → INTEGER` | INTEGER | Return \|x\| with sign of y | CPU+GPU |

### Exponentiation Edge Cases

**INTEGER ** INTEGER (negative exponent):**
```
2 ** (-2)      ❌ ILLEGAL (Compile-time error)
2.0 ** (-2)    ✅ LEGAL (REAL ** INTEGER → REAL, result is 0.25)
```

**REAL ** REAL (negative exponent):**
```
3.5 ** (-1.5)  ✅ LEGAL (REAL ** REAL → REAL)
```

**COMPLEX ** COMPLEX (negative exponent):**
```
(1+2i) ** (-1) ✅ LEGAL (COMPLEX ** INTEGER → COMPLEX)
(1+2i) ** (0.5+0i) ✅ LEGAL (COMPLEX ** COMPLEX → COMPLEX)
```

**Rule:** The INTEGER**negative error applies only when both operands are INTEGER type. COMPLEX exponentiation with negative exponents is always allowed.

| Function | Signature | Return Type | Semantics | Status |
|----------|-----------|------------|-----------|--------|
| MOD | `MOD(a: INTEGER, b: INTEGER) → INTEGER` | INTEGER | Remainder: sign of dividend (a). a MOD b = a - INT(a/b) * b | CPU+GPU |
| MOD | `MOD(a: REAL, b: REAL) → REAL` | REAL | Remainder: sign of dividend (a) | CPU+GPU |
| MAX | `MAX(a: REAL, b: REAL, ...) → REAL` | REAL | Maximum of arguments (variadic, 2+ args) | CPU+GPU |
| MAX | `MAX(a: INTEGER, b: INTEGER, ...) → INTEGER` | INTEGER | Maximum of arguments (variadic, 2+ args) | CPU+GPU |
| MIN | `MIN(a: REAL, b: REAL, ...) → REAL` | REAL | Minimum of arguments (variadic, 2+ args) | CPU+GPU |
| MIN | `MIN(a: INTEGER, b: INTEGER, ...) → INTEGER` | INTEGER | Minimum of arguments (variadic, 2+ args) | CPU+GPU |

### Random Number Generation

splitmix64 finalizer (Stafford 2013) implemented at 64-bit width in the
runtime — Ergo INTEGER is 32-bit, so hand-rolled multiplicative hash
idioms in source wrap early and bias conditioned variates (the
rotor-battery channel-selection failure: conditional mean 0.22, max 0.71,
fixed by this intrinsic family). Constants: Weyl increment = golden-ratio
2^64/phi; both multipliers are Stafford's odd 64-bit constants. The full
64-bit output passes PractRand and BigCrush; only high bits are used.
Pure functions of their seed argument — no hidden state; chaining
`S := HASH(S)` applies the Weyl increment each call (canonical splitmix64
state advance), and counter-based use `RAND(SEED + I)` gives independent
per-index variates.

| Function | Signature | Return Type | Semantics | Status |
|----------|-----------|------------|-----------|--------|
| HASH | `HASH(seed: INTEGER) → INTEGER` | INTEGER | splitmix64(seed) top 31 bits → non-negative int32 in [0, 2^31-1] | CPU+GPU |
| RAND | `RAND(seed: INTEGER) → REAL` | REAL | splitmix64(seed) top 53 bits × 2^-53 → uniform on [0, 1), exact in f64 | CPU+GPU |

Measured on 100k samples (tests/prng.ergo): mean 0.4991, variance
0.0836, lag-1..8 autocorrelation |r| < 0.005, conditional mean 0.4987,
conditional max 0.99999.

### Complex Number Operations

| Function | Signature | Return Type | Semantics | Status |
|----------|-----------|------------|-----------|--------|
| CMPLX | `CMPLX(real: REAL, imag: REAL) → COMPLEX` | COMPLEX | Construct complex from real and imaginary parts | planned (both backends raise, A3) |
| REAL | `REAL(z: COMPLEX) → REAL` | REAL | Extract real component of complex | planned (both backends raise, A3) |
| AIMAG | `AIMAG(z: COMPLEX) → REAL` | REAL | Extract imaginary component of complex | planned (both backends raise, A3) |
| CONJG | `CONJG(z: COMPLEX) → COMPLEX` | COMPLEX | Complex conjugate: real - imag\*i | planned (both backends raise, A3) |

---

## Category 2: Array → Scalar (Reduction, No Allocation)

These consume arrays and return scalar results. Input arrays must be pre-allocated by caller. Output is stack (scalar).

### Vector Reduction Functions

| Function | Signature | Memory | Shape Constraint | Semantics | Status |
|----------|-----------|--------|-----------------|-----------|--------|
| SUM | `SUM(a: REAL(:)) → REAL` | Stack | a is 1D | Sum all elements: Σ a[i] | CPU+GPU |
| SUM | `SUM(a: INTEGER(:)) → INTEGER` | Stack | a is 1D | Sum all elements | CPU+GPU |
| PRODUCT | `PRODUCT(a: REAL(:)) → REAL` | Stack | a is 1D | Product all elements: Π a[i] | CPU+GPU |
| PRODUCT | `PRODUCT(a: INTEGER(:)) → INTEGER` | Stack | a is 1D | Product all elements | CPU+GPU |
| DOT_PRODUCT | `DOT_PRODUCT(a: REAL(:), b: REAL(:)) → REAL` | Stack | a.shape == b.shape, both 1D | Dot product: Σ a[i] * b[i] | CPU+GPU |
| NORM2 | `NORM2(a: REAL(:)) → REAL` | Stack | a is 1D | Euclidean norm: sqrt(Σ a[i]²) | CPU+GPU |
| MAXVAL | `MAXVAL(a: REAL(:)) → REAL` | Stack | a is 1D | Maximum element | CPU+GPU |
| MAXVAL | `MAXVAL(a: INTEGER(:)) → INTEGER` | Stack | a is 1D | Maximum element | CPU+GPU |
| MINVAL | `MINVAL(a: REAL(:)) → REAL` | Stack | a is 1D | Minimum element | CPU+GPU |
| MINVAL | `MINVAL(a: INTEGER(:)) → INTEGER` | Stack | a is 1D | Minimum element | CPU+GPU |

---

## Category 3: Array → Array (Requires Pre-Allocated Output)

These consume array(s) and produce array results. **Caller must pre-allocate output with correct shape.**

### Matrix Operations

| Function | Signature | Input Shapes | Output Shape | Compile-Time Check? | Semantics | Status |
|----------|-----------|--------------|--------------|-------------------|-----------|--------|
| MATMUL | `MATMUL(A: REAL(:,:), B: REAL(:,:)) → REAL(:,:)` | A(m,n), B(n,p) | (m, p) | Yes, if m,n,p known | Matrix multiply. Requires A.shape[1] == B.shape[0] | CPU |
| TRANSPOSE | `TRANSPOSE(A: REAL(:,:)) → REAL(:,:)` | A(m, n) | (n, m) | Yes, if m,n known | Matrix transpose | CPU |
| RESHAPE | `RESHAPE(A: REAL(:), shape: INTEGER(:)) → REAL(:)` | A(any), shape=[d1,d2,...] | Product of shape args | Yes, if shape is constant | Reshape A into new layout. Total elements must match. | CPU |

### Element-Wise Operations (Caller-Allocated Output)

| Function | Signature | Input Shapes | Output Shape | Semantics | Status |
|----------|-----------|--------------|--------------|-----------|--------|
| SQRT | `SQRT(A: REAL(:)) → REAL(:)` | A(n) | (n) | Element-wise square root | CPU+GPU |
| EXP | `EXP(A: REAL(:)) → REAL(:)` | A(n) | (n) | Element-wise exponential | CPU+GPU |
| LOG | `LOG(A: REAL(:)) → REAL(:)` | A(n) | (n) | Element-wise natural logarithm | CPU+GPU |
| SIN | `SIN(A: REAL(:)) → REAL(:)` | A(n) | (n) | Element-wise sine | CPU+GPU |
| COS | `COS(A: REAL(:)) → REAL(:)` | A(n) | (n) | Element-wise cosine | CPU+GPU |
| ABS | `ABS(A: REAL(:)) → REAL(:)` | A(n) | (n) | Element-wise absolute value | CPU+GPU |

**Note:** When applied to arrays, these functions are element-wise. Output shape matches input shape.

### Multi-Dimensional Reductions (Advanced, Optional for Phase 1)

| Function | Signature | Semantics | Status |
|----------|-----------|-----------|--------|
| SUM | `SUM(A: REAL(:,:), dim: INTEGER) → REAL(:)` | Sum along dimension (advanced) | CPU+GPU |
| MAXVAL | `MAXVAL(A: REAL(:,:), dim: INTEGER) → REAL(:)` | Max along dimension (advanced) | CPU+GPU |

**Note:** These are omitted from Phase 1 to keep the spec simple. Implement later if needed.

---

## Category 4: String Functions

All string operations are on fixed-length CHARACTER types. No dynamic allocation.

### String Query

| Function | Signature | Return Type | Semantics | Status |
|----------|-----------|------------|-----------|--------|
| LEN | `LEN(s: CHARACTER(*)) → INTEGER` | INTEGER | Length of string (fixed-length, so deterministic) | CPU+GPU |
| INDEX | `INDEX(s: CHARACTER(*), substr: CHARACTER(*)) → INTEGER` | INTEGER | Position of first occurrence of substr in s, or 0 if not found | CPU+GPU |

### Type Conversion

| Function | Signature | Return Type | Semantics | Status |
|----------|-----------|------------|-----------|--------|
| CHAR | `CHAR(i: INTEGER) → CHARACTER(LEN=1)` | CHARACTER(LEN=1) | ASCII code to character | CPU |
| ICHAR | `ICHAR(c: CHARACTER(LEN=1)) → INTEGER` | INTEGER | Character to ASCII code | CPU |

### Numeric Kind Conversion (INTEGER*8, Inc-2A)

| Function | Signature | Return Type | Semantics | Status |
|----------|-----------|------------|-----------|--------|
| INT8 | `INT8(x: numeric) → INTEGER*8` | INTEGER*8 | Explicit widening to 64-bit integer | CPU+GPU |
| INT | `INT(x: numeric) → INTEGER` | INTEGER | Truncation toward zero; also the explicit **narrowing** path INTEGER*8 → INTEGER (implicit narrowing is a compile-time error) | CPU+GPU |
| REAL | `REAL(x: numeric) → REAL` | REAL | Conversion to REAL (from either integer kind) | CPU+GPU |

Mixing rules and the CPU-only restriction of INTEGER*8 are specified in
`Spec/Ergo_Spec.md` Part 3.

### String Concatenation (Limited, Explicit)

| Function | Signature | Return Type | Semantics | Status |
|----------|-----------|------------|-----------|--------|
| CONCAT | `CONCAT(s1: CHARACTER(*), s2: CHARACTER(*)) → CHARACTER(*)` | CHARACTER(*) | Concatenate two strings. **Caller must declare result with adequate length.** | CPU |

**Usage Example:**
```
CHARACTER(LEN=10) :: s1
CHARACTER(LEN=15) :: s2
CHARACTER(LEN=25) :: result   ! Caller declares result size

result := CONCAT(s1, s2)
```

**Truncation & Error Rules:**
- If combined length of s1 and s2 exceeds result size and both are constant (known at compile time): **Compile-time error.** ("String concatenation result would exceed allocated space")
- If combined length is unknown at compile time (e.g., strings are procedure arguments): **Runtime bounds check** (optional, if enabled). If result is too small: truncation or runtime error depending on implementation choice.

**Design rationale:** Ergo strings are fixed-length. No dynamic allocation. Caller is responsible for declaring adequate space.

---

## Category 5: Array Construction & Inspection (Special)

These are less common but useful for advanced array operations.

### Array Inspection

| Function | Signature | Return Type | Memory | Semantics | Status |
|----------|-----------|------------|--------|-----------|--------|
| SIZE | `SIZE(A: REAL(:)) → INTEGER` | INTEGER | Stack | Total number of elements | CPU (compile-time) |
| SIZE | `SIZE(A: REAL(:,:), dim: INTEGER) → INTEGER` | INTEGER | Stack | Size along dimension dim | CPU (compile-time) |
| RANK | `RANK(A: REAL(:,:)) → INTEGER` | INTEGER | Stack | Number of dimensions (rank). E.g., RANK of 3D array is 3. | CPU (compile-time) |
| SHAPE | `SHAPE(A: REAL(:,:)) → INTEGER(:)` | INTEGER(:) | Caller-allocated | Return array of dimensions. **Caller must pre-allocate with size = RANK(A).** | CPU (compile-time) |

**Example (SIZE - stack return):**
```
REAL :: A(10, 20)
INTEGER :: s

s := SIZE(A)           ! s = 200 (total elements)
s := SIZE(A, 1)        ! s = 10 (first dimension)
s := RANK(A)           ! s = 2 (number of dimensions)
```

**Example (SHAPE - caller-allocated output, known rank):**
```
REAL :: A(10, 20)
INTEGER :: dims(2)     ! Caller allocates with size = RANK(A) = 2

dims := SHAPE(A)       ! dims becomes [10, 20]
```

**Example (SHAPE - caller-allocated output, unknown rank):**
```
SUBROUTINE process(A)
  REAL :: A(:,:)       ! Rank known at compile time (2D)
  INTEGER :: dims(2)   ! Caller allocates with size = 2
  
  dims := SHAPE(A)     ! OK: dims is pre-allocated with correct size
END SUBROUTINE

SUBROUTINE process_general(A)
  REAL :: A(:)         ! Rank unknown (could be 1D, 2D, etc.)
  INTEGER, ALLOCATABLE :: dims(:)
  
  ALLOCATE(dims(RANK(A)))  ! Allocate based on rank
  dims := SHAPE(A)       ! Now OK: dims is pre-allocated
END SUBROUTINE
```

**Memory contract for SHAPE:**
- **Caller must allocate output array with size = RANK(A)**
- If rank is known at compile time, caller allocates fixed-size array
- If rank is unknown, caller allocates with explicit ALLOCATE(dims(RANK(A)))
- SHAPE writes into the pre-allocated array; **never allocates**

---

## Intrinsic Polymorphism & Type Overloading

Many intrinsics are **polymorphic** (overloaded). Examples:

- **SIN(x):** Works on REAL or REAL array
- **ABS(x):** Works on INTEGER, REAL, or COMPLEX
- **MOD(a, b):** Works on INTEGER or REAL
- **MAX(a, b, ...):** Works on INTEGER or REAL

**Compiler rule:** Determine overload based on argument types. If ambiguous, reject with error.

---

## Shape Propagation Rules (For Compiler Type Checker)

When checking assignment `C := FUNC(args)`, the compiler must:

1. **Infer output shape** from input shapes and constant shape arguments
2. **Check dimension compatibility:** `shape(C) == shape(result)` at compile time if possible, else insert runtime check

### Examples

#### MATMUL
```
REAL :: A(10, 20), B(20, 15), C(10, 15)

C := MATMUL(A, B)

Compiler inference:
  Input A: (10, 20)
  Input B: (20, 15)
  Check: A.shape[1] == B.shape[0]? YES (20 == 20)
  Output shape: (A.shape[0], B.shape[1]) = (10, 15)
  Check: C.shape == (10, 15)? YES → OK
```

#### RESHAPE
```
REAL :: A(12), B(3, 4)

B := RESHAPE(A, [3, 4])

Compiler inference:
  Input A: (12)
  Shape arg: [3, 4] (constant)
  Check: product of A = 12, product of shape = 12? YES
  Output shape: (3, 4)
  Check: B.shape == (3, 4)? YES → OK
```

#### Shape mismatch error
```
REAL :: A(10, 20), B(20, 15)
REAL :: C(5, 5)  ! Wrong shape!

C := MATMUL(A, B)

Compiler inference:
  Output shape would be (10, 15)
  Check: C.shape (5, 5) == (10, 15)? NO
  Compile-time error: "Shape mismatch in assignment"
```

---

## Intrinsic Function Implementation Notes

### Stack vs Heap

- **Pure scalar returns (SIN, COS, ABS, etc.):** Return value in FP register or scalar memory. No allocation.
- **Array returns (MATMUL, TRANSPOSE, RESHAPE):** Caller provides output buffer. Intrinsic writes into it. No allocation.
- **String returns (CONCAT):** Return fixed-length string in caller's buffer (or stack if small). No allocation.

### Performance Assumptions

The compiler may inline simple intrinsics (SIN, COS, SQRT, ABS) as hardware instructions or library calls.

Complex intrinsics (MATMUL, TRANSPOSE) may use optimized implementations:
- MATMUL → BLAS (Basic Linear Algebra Subprograms) call
- TRANSPOSE → Parallel loop or cache-optimized kernel
- DOT_PRODUCT → Vectorized loop

But these are backend concerns. From Ergo's perspective, they're simple function calls with pre-allocated outputs.

---

## Intrinsic Summary Table (Cheat Sheet)

| Category | Examples | Memory Behavior |
|----------|----------|-----------------|--------|
| Scalar math | SIN, COS, EXP, SQRT, ABS, MOD, MAX | Stack return, no allocation |
| Vector reduction | SUM, PRODUCT, DOT_PRODUCT, NORM2 | Stack return (scalar), input pre-allocated |
| Array operations | MATMUL, TRANSPOSE, RESHAPE, SQRT (on array) | Output pre-allocated by caller |
| String operations | LEN, INDEX, CONCAT | Stack return or fixed-length caller-allocated |
| Array inspection | SIZE, SHAPE | Stack return or caller-allocated (minimal overhead) |
| Memory operations | ZERO | In-place modification, no allocation (memset) |

---

## Intrinsic Error Conditions

### Compile-Time Errors (Static Check)

- Shape mismatch on assignment: `C := MATMUL(A, B)` where C shape doesn't match output
- Dimension mismatch in MATMUL: `MATMUL(A, B)` where A.shape[1] ≠ B.shape[0]
- RESHAPE with incompatible sizes: `RESHAPE(A, [d1, d2])` where product of A ≠ product of shape
- Type mismatch: `SIN(int_var)` (SIN expects REAL)

### Runtime Errors (Dynamic Check)

- Array bounds on indexing: `A(i)` where i is out of bounds (if bounds checking enabled)
- Shape mismatch with allocatable arrays: `C := MATMUL(A, B)` where C was allocated with wrong shape
- Invalid logarithm: `LOG(negative_value)`
- Division by zero in MOD: `MOD(a, 0)`

---

## Testing Checklist for Intrinsics

- [ ] SIN, COS, TAN on known values (0, π/2, π)
- [ ] SQRT on 0, 1, 4 (should give 0, 1, 2)
- [ ] ABS on negative numbers
- [ ] MOD with positive and negative arguments
- [ ] MAX/MIN with multiple arguments
- [ ] DOT_PRODUCT of two vectors
- [ ] MATMUL of compatible matrices
- [ ] TRANSPOSE of rectangular matrix
- [ ] RESHAPE with correct and incorrect sizes
- [ ] Shape checks on assignment (error cases)
- [ ] ZERO on STATIC REAL, INTEGER, and multi-dimensional arrays

---

## Category 6: Memory Operations (Statement-Only)

These are statement-level intrinsics invoked via CALL. They modify memory in place.
No return value. No allocation. Deterministic, platform-portable behavior.

### Array Zeroing

| Function | Signature | Memory | Semantics | Status |
|----------|-----------|--------|-----------|--------|
| ZERO | `CALL ZERO(A)` — A is any declared array | In-place | Zero all elements of A | CPU+GPU |

**Codegen contract:** `CALL ZERO(A)` always emits `memset(A, 0, sizeof(A))`.

`memset` is C89/C99/C11 standard, implemented and hardware-optimized on every
conforming platform (x86, ARM, RISC-V, POWER, etc.). Each platform's libc
provides a tuned implementation using the widest available store instructions.

**Why a dedicated intrinsic instead of a loop?**

A triple-nested DO loop that zeros an array is semantically identical, but its
codegen depends on compiler optimization level:
- At `-O3`, GCC/Clang may recognize the loop pattern and emit memset.
- At `-O0` or `-O1`, they emit scalar stores with loop overhead.
- Across compilers and architectures, pattern recognition is not guaranteed.

This means the same Ergo source could produce different C code depending on
optimization flags — violating the principle that "the compiler lowers what
you wrote, not what you meant."

`CALL ZERO(A)` makes the intent explicit. One Ergo statement, one C library
call, identical behavior at every optimization level on every platform.

**Usage:**
```
STATIC REAL :: GRID(32, 32, 32)
STATIC INTEGER :: FLAGS(10000)

CALL ZERO(GRID)       ! memset(GRID, 0, sizeof(GRID))
CALL ZERO(FLAGS)      ! memset(FLAGS, 0, sizeof(FLAGS))
```

**Constraints:**
- Argument must be a declared array (STATIC or local with known shape).
- Cannot be used on scalars (use `:= 0` assignment).
- Cannot be used on ALLOCATABLE arrays that have not been allocated.
- ZERO is a statement, not an expression: `X := ZERO(A)` is illegal.

### Device Streaming (Inc-2C)

Explicit host↔device slice transfers for out-of-core GPU programs.
Statement-only, CALL-invoked, in-place, no allocation. Indices are
1-based element offsets into the respective arrays.

| Function | Signature | Memory | Semantics | Status |
|----------|-----------|--------|-----------|--------|
| VK_STAGE | `CALL VK_STAGE(gpu_arr, host_arr, src0, dst0, len)` | host→device | Upload `len` elements from `host_arr(src0..)` to `gpu_arr(dst0..)` | GPU (+CPU memmove) |
| VK_FETCH | `CALL VK_FETCH(host_arr, gpu_arr, src0, dst0, len)` | device→host | Download `len` elements from `gpu_arr(src0..)` to `host_arr(dst0..)` | GPU (+CPU memmove) |

**Synchronization contract:** both are frame-draining sync points.
VK_STAGE drains the recording frame first only when the frame has
unsubmitted kernel writes that overlap the destination (an upload
recorded ahead of pending dispatches would otherwise be clobbered).
VK_FETCH always drains (the data must exist before the copy).

**Residency contract (compile-time):** the device argument of
VK_STAGE must be GPU-resident and the host argument must NOT be
GPU-resident (and vice versa for VK_FETCH) — violations are compile
errors with named diagnostics. Zero host-side array copies: these are
the only sanctioned path for moving slices between the host arena and
device buffers in streamed programs.

**CPU lowering:** both lower to memmove, so streamed programs run
correctly CPU-only (the GPU execution model, `Spec/Ergo_Spec.md`
§8.8, is an implementation detail).

**Reference:** design + validation in `min/phase_ed/inc2_check.md`
(N=19 ED gather-window streaming).

---

## Future Extensions (Post-Phase 1)

The following intrinsics are useful but not required for the initial implementation:

- **Reductions with dimension:** `SUM(A, dim=1)`
- **Array slicing operators:** `A(1:5, 1:10)`
- **Logical array functions:** `ANY(mask)`, `ALL(mask)`, `COUNT(mask)`
- **Sorting:** `SORT(A)`
- **Eigen/SVD:** Advanced linear algebra (likely external library)

These can be added later without breaking the core language.

---

## LOCKED: Intrinsic Function Set

✅ All base intrinsics defined with explicit signatures, shape propagation rules, and memory semantics.

**The compiler now has everything needed to type-check intrinsic calls and verify shape compatibility on assignment.**

---

## Category 7: Warp Subgroup Intrinsics (GPU-only)

Subgroup shuffle/ballot operations for extracted GPU kernels. **Status:
GPU-only, and hard-coded to a 32-lane subgroup** — on GPUs with a
different wavefront width the semantics are wrong, and there is no CPU
lowering (the CPU front end does not know these names; a program using
them compiles for `--target spirv` only). Portability landmine by
construction; use only in kernels written for 32-lane NVIDIA subgroups.

| Function | Signature | Return Type | Semantics | Status |
|----------|-----------|------------|-----------|--------|
| RING_PREV | `RING_PREV(x: REAL) → REAL` | REAL | value from the lane−1 neighbor (wraps within the 32-lane subgroup) | GPU-only (32-lane) |
| RING_NEXT | `RING_NEXT(x: REAL) → REAL` | REAL | value from the lane+1 neighbor (wraps) | GPU-only (32-lane) |
| RING_SHIFT | `RING_SHIFT(x: REAL, delta: INTEGER) → REAL` | REAL | value from lane+delta (wraps) | GPU-only (32-lane) |
| RING_BROADCAST | `RING_BROADCAST(x: REAL, lane: INTEGER) → REAL` | REAL | broadcast one lane's value to the subgroup | GPU-only (32-lane) |
| WARP_BALLOT | `WARP_BALLOT(pred) → mask` | INTEGER | ballot across the subgroup | GPU-only (32-lane) |
| WARP_BALLOT_COUNT | `WARP_BALLOT_COUNT(pred) → INTEGER` | INTEGER | popcount of the ballot | GPU-only (32-lane) |
| WARP_BALLOT_PREFIX | `WARP_BALLOT_PREFIX(pred) → INTEGER` | INTEGER | exclusive prefix popcount | GPU-only (32-lane) |
| WARP_BROADCAST_FIRST | `WARP_BROADCAST_FIRST(...) → REAL` | REAL | first active lane's value | GPU-only (32-lane) |

Oracle: `tests/gpu_ring_shuffle.ergo`.

---

## The VERIFY Directive (statement, not an intrinsic)

Syntax (parser `_parse_verify`):

```
VERIFY arr1, arr2, ... ORACLE n [EVERY m] [TOL t] [NET "host:port" [GPU k]]
```

Semantics (IR backend, `_emit_verify`): a CPU **oracle shadow state**.
The first `n` elements of each listed array are mirrored into CPU
shadow arrays at first call and evolved independently by the CPU each
frame with the same physics; every `m` frames (default 1) the GPU
state is sampled and compared against the shadow within relative
tolerance `t` (default 1e-6), reporting divergence on stderr. `NET`
sends the checkpoint over UDP to an oracle host (`GPU k` selects the
client identity). `ERGO_NO_VERIFY=1` disables the oracle at runtime;
`--no-verify` omits it at compile time (required for programs whose
physics uses GPU-only intrinsics, since the CPU shadow copy cannot
contain them). Downloads/uploads around the checkpoint are guard-aware
(Inc-4): on non-oracle frames no transfer happens when `m > 1`.

**Status:** CPU oracle for GPU programs (that is its purpose);
documented 2026-08-13 (A3) — it was parsed and working but unruled.
| Construct | Kind | Semantics | Status |
|-----------|------|-----------|--------|
| VERIFY | statement directive | CPU shadow-state oracle for GPU programs | CPU+GPU (oracle is host-side) |
