# Ergo Owned Standard Library Replacement Plan

This document tracks the progress of decoupling the Ergo compiler's generated C code from the standard C library (`<math.h>`, `<stdio.h>`, `<stdlib.h>`, `<string.h>`). The ultimate goal is to route all dependencies through a single custom include (`ergo_rt.h`) which relies on compiler built-ins and raw Linux syscalls.

## Phase 1: Compiler Built-ins (Freebies) - [COMPLETED]
- [x] Replace `fma` / `fmaf` with `__builtin_fma`
- [x] Replace `sqrt` / `sqrtf` with `__builtin_sqrt`
- [x] Replace `fabs` / `fabsf` with `__builtin_fabs`
- [x] Replace `fmax` / `fmaxf` with `__builtin_fmax`
- [x] Replace `fmin` / `fminf` with `__builtin_fmin`
- [x] Replace `copysign` with `__builtin_copysign`
- [x] Replace integer `abs` with `__builtin_abs`

## Phase 2: Extend `ergo_math_kernels.h`
Implement the remaining transcendental and math operations using existing owned components.
- [ ] `_ergo_atan`: Implement via `_ergo_atan2(x, 1.0)`.
- [ ] `_ergo_acos`: Implement via `_ergo_atan2(sqrt(1-x*x), x)`.
- [ ] `_ergo_asin`: Implement via `_ergo_atan2(x, sqrt(1-x*x))`.
- [ ] `_ergo_tan`: Implement via `_ergo_sin(x) / _ergo_cos(x)`.
- [ ] `_ergo_fmod`: Implement fully owned `x - trunc(x/y)*y` using bit manipulation.
- [ ] `_ergo_log10`: Implement via `_ergo_log(x) * (1.0 / ln(10))`.
- [ ] Hyperbolics (`_ergo_sinh`, `_ergo_cosh`, `_ergo_tanh`): Implement via `_ergo_exp` formulations.
- [ ] Wire these new functions into `C_MATH` and `OWNED_MATH` in `ir_codegen.py`.

## Phase 3: I/O & `stdio.h` Eradication
Replace the slow `printf`/`fprintf` paths and `FILE*` streams.
- [ ] **`ergo_syscall.h`**: Create minimal raw Linux syscall wrappers for `read(2)`, `write(2)`, `open(2)`, `close(2)`.
- [ ] **`ergo_print.h`**: Create a typed-dispatch formatter family (`ergo_print_f64`, `ergo_print_i32`, `ergo_print_str`) formatting to a stack buffer and using raw `write`.
- [ ] **`ir_codegen.py` Updates**: Change codegen to emit typed `ergo_print_*` calls instead of `printf`/`fprintf` based on compile-time types.
- [ ] **`ergo_io.h` Rewrite**: Remove `<stdio.h>`. Switch `fopen`/`fclose`/`fread`/`fwrite` to use `open(2)`/`close(2)`/`read(2)`/`write(2)`.
- [ ] **Error Handling**: Create a minimal string table for the specific errnos Ergo IO hits (`ENOENT`, `EACCES`, `ENOSPC`, `EBADF`) to replace `strerror`.

## Phase 4: `stdlib.h` & `string.h` Eradication
- [ ] `exit`: Replace with raw `syscall(SYS_exit_group, code)`.
- [ ] `abort`: Replace with `__builtin_trap()`.
- [ ] `atoi`: Implement a tiny 10-line loop in `ergo_rt.h`.
- [ ] `getenv`: Add a minimal syscall parser for `/proc/self/environ` (needed for GPU/render mode) or a lightweight wrapper.
- [ ] `memcpy` / `memset`: Replace with `__builtin_memcpy` and `__builtin_memset`.
- [ ] `strcmp`: Replace with `__builtin_strcmp` or a small custom loop (only used in CLI arg parsing).

## Phase 5: The Grand Unification (`ergo_rt.h`)
- [ ] Create `ergo_rt.h` encompassing all the above sub-headers.
- [ ] Remove `#include <math.h>`, `#include <stdio.h>`, `#include <stdlib.h>`, `#include <string.h>` entirely from `ir_codegen.py`.
- [ ] Run Golden Corpus baseline to ensure exact determinism and that everything continues passing.
