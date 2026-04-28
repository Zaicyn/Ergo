# Ergo Operator Expansion Reference

## Status: Reference only. Not planned for immediate implementation.

Ergo currently has 16 operators. The encoding supports up to 256.
This document captures a feasible expansion map for if/when specific
operators are needed. The principle: add operators only when they solve
a real problem you've actually hit. Don't fill slots speculatively.

## Current 16 (locked, the core)

| Category    | Operators                       | Count |
|-------------|----------------------------------|-------|
| Arithmetic  | `**` `*` `/` `+` `-`            | 5     |
| Relational  | `<` `>` `=` `≠` `≤` `≥`        | 6     |
| Logical     | `.AND.` `.OR.` `.NOT.`           | 3     |
| Assignment  | `:=`                             | 1     |
| Unary       | `+` `-` (prefix, shared symbols)| 1     |

These cover all math, comparison, logic, and assignment a physics kernel
needs. Everything else is an intrinsic function call.

## Why 16 → 256 (not 16 → 32 or 64)

No real architecture packs operator tokens into nibbles. The IR, parser,
and codegen all use full integers for op codes. 256 (one byte) is the
natural machine-friendly ceiling. It removes the artificial constraint
without encouraging bloat.

NAND is the hardware substrate — every AND, OR, NOT, XOR is NANDs at
the transistor level. The language doesn't need a NAND operator because
it operates above that abstraction.

## Potential Expansion Domains

### Domain 1: Bitwise operators (~6 ops)

Currently intrinsics: IAND, IOR, IEOR, ISHFT, NOT, POPCOUNT.
Could become operators if bitwise math becomes pervasive in user code.
For now, intrinsics work fine — the codegen emits the same instructions.

```
&    bitwise AND     (currently IAND)
|    bitwise OR      (currently IOR)
^    bitwise XOR     (currently IEOR)
<<   left shift      (currently ISHFT with positive)
>>   right shift     (currently ISHFT with negative)
~    bitwise NOT     (currently NOT)
```

**Case for:** cleaner physics kernels with heavy flag manipulation.
**Case against:** symbol collision risk, readability for non-CS audience.

### Domain 2: Compound assignment (~5 ops)

```
+= -= *= /= **=
```

Pure syntactic sugar: `X += DT * AX` desugars to `X := X + DT * AX`.
No semantic difference.

**Case for:** less repetition in physics kernels (every velocity update
repeats the variable name).
**Case against:** two ways to write the same thing. Ergo prefers one way.

### Domain 3: Range / membership (~2 ops)

```
IN     X IN [0.0, 1.0]     → (X ≥ 0.0) .AND. (X ≤ 1.0)
NOT IN X NOT IN [0.0, 1.0] → (X < 0.0) .OR. (X > 1.0)
```

**Case for:** readability for bounds checking, guard clauses.
**Case against:** desugars trivially, comparison chaining already exists.

### Domain 4: String (~1 op)

```
//   concatenation (Fortran standard)
```

**Case for:** string handling when Ergo gets I/O.
**Case against:** simulation language, strings are rare.

### Domain 5: Saturating arithmetic (~2 ops)

```
+| saturating add (clamps at MAX instead of wrapping)
-| saturating sub (clamps at 0/MIN instead of wrapping)
```

**Case for:** integer signal processing, color math, index safety.
**Case against:** CLAMP(X + Y, 0, MAX) is explicit and auditable.

## The 10 Semantic Clusters (GPT's ISA reference)

For hardware-level thinking, not language-level. Included for reference.

| Cluster              | Approx ops | Ergo relevance        |
|----------------------|------------|------------------------|
| Integer ALU          | ~40        | Core 16 covers this    |
| Memory/addressing    | ~35        | Compiler handles        |
| Control flow         | ~25        | DO/IF/CALL handles     |
| Bit manipulation     | ~25        | Intrinsics cover this  |
| Floating point       | ~35        | Intrinsics cover this  |
| Vector/SIMD          | ~45        | GPU kernels, not ops   |
| Concurrency/atomics  | ~20        | Runtime + directives   |
| System/privileged    | ~20        | Not applicable         |
| Type conversion      | ~15        | REAL(), INT() intrinsics |
| Acceleration hooks   | ~16        | RING_SHIFT etc.        |

Key insight: most of these map to intrinsics or compiler internals,
not to user-visible operators. The 16-operator surface is correct
for the abstraction level Ergo targets.

## Decision Framework

Add a new operator only when ALL of these are true:

1. There's a real use case that's been hit multiple times
2. The intrinsic version is significantly less readable
3. The operator meaning is unambiguous to domain experts
4. It composes cleanly with existing operators (no precedence surprises)
5. It doesn't create two ways to express the same thing without benefit

If any of these fail, keep it as an intrinsic.
