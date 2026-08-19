# Your First Ergo Program — "hello, stencil"

Ten minutes, three commands, one lesson per step. Everything here is
runnable from the repo root; the constitution is `Spec/Ergo_Spec.md`,
this is the citizenship test.

## 1. The program

Ergo has no `PROGRAM`/`END` wrapper — top-level statements are the main
body. `IMPLICIT NONE` and `::` declarations are the house dialect.
Save as `hello.ergo`:

```
IMPLICIT NONE
INTEGER, PARAMETER :: N = 64
STATIC REAL :: A(N), B(N)
INTEGER :: K, T

DO K = 1, N
  A(K) := 0.0
ENDDO
A(N / 2) := 1.0

DO T = 1, 200
  DO K = 2, N - 1
    B(K) := 0.5 * (A(K - 1) + A(K + 1))
  ENDDO
  DO K = 2, N - 1
    A(K) := B(K)
  ENDDO
ENDDO

WRITE(*, "('center after 200 steps: %.6f')") A(N / 2)
```

The traps this dodges (the parser teaches all of them with named
messages): assignment is `:=`, `ENDDO`/`ENDIF` are one word, IF is
always block form, declarations need `::`, and there are no array
expressions — stencils are explicit loops.

## 2. Compile and run

```bash
python -m core hello.ergo -o hello
./hello
```

```
('center after 200 steps: 0.056343')
```

(The pulse diffuses — the point is the loop, not the physics.)

## 3. Determinism, for free

```bash
./hello > run1.txt; ./hello > run2.txt; cmp run1.txt run2.txt && echo BITWISE
```

Same binary, same output, every time — the language's evaluation-order
rules (spec Part 7) make reassociation a compile-level impossibility
unless you opt into `--cpu-fast-math`. Programs with GPU state can go
further: `ERGO_HASH_FINAL=1 ./program` prints a state hash at exit for
cross-run comparison.

## 4. Why STATIC matters

Now edit the program: `N = 64` → `N = 300000`, and delete the word
`STATIC` from the declaration. Recompile:

```
ERGO NOTE: local array A(300000) is 2.4 MB — hoisted to static storage (A1)
ERGO NOTE: local array B(300000) is 2.4 MB — hoisted to static storage (A1)
```

A plain local array lives on the stack, and the default 8 MB stack
used to just segfault. Today the compiler hoists arrays larger than
1 MB to static storage itself (and tells you); sizes it can't resolve
at compile time get a warning telling you to declare `STATIC`. The
explicit habit — `STATIC` for anything big — is still the right one:
it documents intent and keeps frames small.

## 5. Where next

- `Spec/Ergo_Spec.md` — the language constitution (operators, memory
  model, STATIC rules, GPU execution model, determinism contract).
- `Spec/Ergo_Intrinsic_Signatures_Complete.md` — every intrinsic with
  its implementation status (CPU/GPU/planned).
- `tests/golden/run_golden.py` — the dual-path golden corpus;
  `tests/golden/check_errors.py` — the teaching-message goldens.
- `--target spirv` — the GPU backend (`tests/gpu_stencil2d.ergo` is a
  minimal GPU stencil; `NEXT_SESSION.md` §2 has the flag map).
