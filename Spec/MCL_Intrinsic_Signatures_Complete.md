> **SUPERSEDED (2026-08-23):** kept for history. Current reference: Spec/Ergo_Intrinsic_Signatures_Complete.md.

# MCL Intrinsic Function Signatures (Complete Reference)

## Overview

This is the authoritative list of every built-in function in MCL. Each entry specifies:
- **Signature:** Function name, argument types, return type
- **Shape propagation:** How input shapes determine output shape
- **Memory:** Caller allocates, stack return, or error
- **Semantics:** What it does

This is used by the compiler's type checker to:
1. Validate argument types
2. Infer output shape
3. Check assignment shape compatibility: `C := FUNC(args)` → compiler verifies `shape(C) == shape(FUNC(...))`

---

## Category 1: Scalar → Scalar (Pure Math, No Allocation)

All of these take one or more numeric scalars and return a scalar. No allocation. Stack return.

### Trigonometric Functions

| Function | Signature | Return Type | Semantics |
|----------|-----------|------------|-----------|
| SIN | `SIN(x: REAL) → REAL` | REAL | Sine in radians |
| COS | `COS(x: REAL) → REAL` | REAL | Cosine in radians |
| TAN | `TAN(x: REAL) → REAL` | REAL | Tangent in radians |
| ASIN | `ASIN(x: REAL) → REAL` | REAL | Arcsine, result in [-π/2, π/2] |
| ACOS | `ACOS(x: REAL) → REAL` | REAL | Arccosine, result in [0, π] |
| ATAN | `ATAN(x: REAL) → REAL` | REAL | Arctangent, result in [-π/2, π/2] |
| ATAN2 | `ATAN2(y: REAL, x: REAL) → REAL` | REAL | Two-argument arctangent. Result in [-π, π]. Handles quadrants correctly. |

### Exponential & Logarithmic

| Function | Signature | Return Type | Semantics |
|----------|-----------|------------|-----------|
| EXP | `EXP(x: REAL) → REAL` | REAL | e^x |
| LOG | `LOG(x: REAL) → REAL` | REAL | Natural logarithm (ln) |
| LOG10 | `LOG10(x: REAL) → REAL` | REAL | Base-10 logarithm |
| SQRT | `SQRT(x: REAL) → REAL` | REAL | Square root. x must be ≥ 0. |
| SQRT | `SQRT(z: COMPLEX) → COMPLEX` | COMPLEX | Complex square root |

### Hyperbolic Functions

| Function | Signature | Return Type | Semantics |
|----------|-----------|------------|-----------|
| SINH | `SINH(x: REAL) → REAL` | REAL | Hyperbolic sine |
| COSH | `COSH(x: REAL) → REAL` | REAL | Hyperbolic cosine |
| TANH | `TANH(x: REAL) → REAL` | REAL | Hyperbolic tangent |

### Absolute Value & Sign

| Function | Signature | Return Type | Semantics |
|----------|-----------|------------|-----------|
| ABS | `ABS(x: REAL) → REAL` | REAL | Absolute value of real |
| ABS | `ABS(x: INTEGER) → INTEGER` | INTEGER | Absolute value of integer |
| ABS | `ABS(z: COMPLEX) → REAL` | REAL | Magnitude of complex number: sqrt(real²+imag²) |
| SIGN | `SIGN(x: REAL, y: REAL) → REAL` | REAL | Return \|x\| with sign of y |
| SIGN | `SIGN(x: INTEGER, y: INTEGER) → INTEGER` | INTEGER | Return \|x\| with sign of y |

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

| Function | Signature | Return Type | Semantics |
|----------|-----------|------------|-----------|
| MOD | `MOD(a: INTEGER, b: INTEGER) → INTEGER` | INTEGER | Remainder: sign of dividend (a). a MOD b = a - INT(a/b) * b |
| MOD | `MOD(a: REAL, b: REAL) → REAL` | REAL | Remainder: sign of dividend (a) |
| MAX | `MAX(a: REAL, b: REAL, ...) → REAL` | REAL | Maximum of arguments (variadic, 2+ args) |
| MAX | `MAX(a: INTEGER, b: INTEGER, ...) → INTEGER` | INTEGER | Maximum of arguments (variadic, 2+ args) |
| MIN | `MIN(a: REAL, b: REAL, ...) → REAL` | REAL | Minimum of arguments (variadic, 2+ args) |
| MIN | `MIN(a: INTEGER, b: INTEGER, ...) → INTEGER` | INTEGER | Minimum of arguments (variadic, 2+ args) |

### Complex Number Operations

| Function | Signature | Return Type | Semantics |
|----------|-----------|------------|-----------|
| CMPLX | `CMPLX(real: REAL, imag: REAL) → COMPLEX` | COMPLEX | Construct complex from real and imaginary parts |
| REAL | `REAL(z: COMPLEX) → REAL` | REAL | Extract real component of complex |
| AIMAG | `AIMAG(z: COMPLEX) → REAL` | REAL | Extract imaginary component of complex |
| CONJG | `CONJG(z: COMPLEX) → COMPLEX` | COMPLEX | Complex conjugate: real - imag\*i |

---

## Category 2: Array → Scalar (Reduction, No Allocation)

These consume arrays and return scalar results. Input arrays must be pre-allocated by caller. Output is stack (scalar).

### Vector Reduction Functions

| Function | Signature | Memory | Shape Constraint | Semantics |
|----------|-----------|--------|-----------------|-----------|
| SUM | `SUM(a: REAL(:)) → REAL` | Stack | a is 1D | Sum all elements: Σ a[i] |
| SUM | `SUM(a: INTEGER(:)) → INTEGER` | Stack | a is 1D | Sum all elements |
| PRODUCT | `PRODUCT(a: REAL(:)) → REAL` | Stack | a is 1D | Product all elements: Π a[i] |
| PRODUCT | `PRODUCT(a: INTEGER(:)) → INTEGER` | Stack | a is 1D | Product all elements |
| DOT_PRODUCT | `DOT_PRODUCT(a: REAL(:), b: REAL(:)) → REAL` | Stack | a.shape == b.shape, both 1D | Dot product: Σ a[i] * b[i] |
| NORM2 | `NORM2(a: REAL(:)) → REAL` | Stack | a is 1D | Euclidean norm: sqrt(Σ a[i]²) |
| MAXVAL | `MAXVAL(a: REAL(:)) → REAL` | Stack | a is 1D | Maximum element |
| MAXVAL | `MAXVAL(a: INTEGER(:)) → INTEGER` | Stack | a is 1D | Maximum element |
| MINVAL | `MINVAL(a: REAL(:)) → REAL` | Stack | a is 1D | Minimum element |
| MINVAL | `MINVAL(a: INTEGER(:)) → INTEGER` | Stack | a is 1D | Minimum element |

---

## Category 3: Array → Array (Requires Pre-Allocated Output)

These consume array(s) and produce array results. **Caller must pre-allocate output with correct shape.**

### Matrix Operations

| Function | Signature | Input Shapes | Output Shape | Compile-Time Check? | Semantics |
|----------|-----------|--------------|--------------|-------------------|-----------|
| MATMUL | `MATMUL(A: REAL(:,:), B: REAL(:,:)) → REAL(:,:)` | A(m,n), B(n,p) | (m, p) | Yes, if m,n,p known | Matrix multiply. Requires A.shape[1] == B.shape[0] |
| TRANSPOSE | `TRANSPOSE(A: REAL(:,:)) → REAL(:,:)` | A(m, n) | (n, m) | Yes, if m,n known | Matrix transpose |
| RESHAPE | `RESHAPE(A: REAL(:), shape: INTEGER(:)) → REAL(:)` | A(any), shape=[d1,d2,...] | Product of shape args | Yes, if shape is constant | Reshape A into new layout. Total elements must match. |

### Element-Wise Operations (Caller-Allocated Output)

| Function | Signature | Input Shapes | Output Shape | Semantics |
|----------|-----------|--------------|--------------|-----------|
| SQRT | `SQRT(A: REAL(:)) → REAL(:)` | A(n) | (n) | Element-wise square root |
| EXP | `EXP(A: REAL(:)) → REAL(:)` | A(n) | (n) | Element-wise exponential |
| LOG | `LOG(A: REAL(:)) → REAL(:)` | A(n) | (n) | Element-wise natural logarithm |
| SIN | `SIN(A: REAL(:)) → REAL(:)` | A(n) | (n) | Element-wise sine |
| COS | `COS(A: REAL(:)) → REAL(:)` | A(n) | (n) | Element-wise cosine |
| ABS | `ABS(A: REAL(:)) → REAL(:)` | A(n) | (n) | Element-wise absolute value |

**Note:** When applied to arrays, these functions are element-wise. Output shape matches input shape.

### Multi-Dimensional Reductions (Advanced, Optional for Phase 1)

| Function | Signature | Semantics |
|----------|-----------|-----------|
| SUM | `SUM(A: REAL(:,:), dim: INTEGER) → REAL(:)` | Sum along dimension (advanced) |
| MAXVAL | `MAXVAL(A: REAL(:,:), dim: INTEGER) → REAL(:)` | Max along dimension (advanced) |

**Note:** These are omitted from Phase 1 to keep the spec simple. Implement later if needed.

---

## Category 4: String Functions

All string operations are on fixed-length CHARACTER types. No dynamic allocation.

### String Query

| Function | Signature | Return Type | Semantics |
|----------|-----------|------------|-----------|
| LEN | `LEN(s: CHARACTER(*)) → INTEGER` | INTEGER | Length of string (fixed-length, so deterministic) |
| INDEX | `INDEX(s: CHARACTER(*), substr: CHARACTER(*)) → INTEGER` | INTEGER | Position of first occurrence of substr in s, or 0 if not found |

### Type Conversion

| Function | Signature | Return Type | Semantics |
|----------|-----------|------------|-----------|
| CHAR | `CHAR(i: INTEGER) → CHARACTER(LEN=1)` | CHARACTER(LEN=1) | ASCII code to character |
| ICHAR | `ICHAR(c: CHARACTER(LEN=1)) → INTEGER` | INTEGER | Character to ASCII code |

### String Concatenation (Limited, Explicit)

| Function | Signature | Return Type | Semantics |
|----------|-----------|------------|-----------|
| CONCAT | `CONCAT(s1: CHARACTER(*), s2: CHARACTER(*)) → CHARACTER(*)` | CHARACTER(*) | Concatenate two strings. **Caller must declare result with adequate length.** |

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

**Design rationale:** MCL strings are fixed-length. No dynamic allocation. Caller is responsible for declaring adequate space.

---

## Category 5: Array Construction & Inspection (Special)

These are less common but useful for advanced array operations.

### Array Inspection

| Function | Signature | Return Type | Memory | Semantics |
|----------|-----------|------------|--------|-----------|
| SIZE | `SIZE(A: REAL(:)) → INTEGER` | INTEGER | Stack | Total number of elements |
| SIZE | `SIZE(A: REAL(:,:), dim: INTEGER) → INTEGER` | INTEGER | Stack | Size along dimension dim |
| RANK | `RANK(A: REAL(:,:)) → INTEGER` | INTEGER | Stack | Number of dimensions (rank). E.g., RANK of 3D array is 3. |
| SHAPE | `SHAPE(A: REAL(:,:)) → INTEGER(:)` | INTEGER(:) | Caller-allocated | Return array of dimensions. **Caller must pre-allocate with size = RANK(A).** |

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

But these are backend concerns. From MCL's perspective, they're simple function calls with pre-allocated outputs.

---

## Intrinsic Summary Table (Cheat Sheet)

| Category | Examples | Memory Behavior |
|----------|----------|-----------------|
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

| Function | Signature | Memory | Semantics |
|----------|-----------|--------|-----------|
| ZERO | `CALL ZERO(A)` — A is any declared array | In-place | Zero all elements of A |

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

