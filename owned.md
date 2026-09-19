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
- [x] `_ergo_atan`: Implement via `_ergo_atan2(x, 1.0)`.
- [x] `_ergo_acos`: Implement via `_ergo_atan2(sqrt(1-x*x), x)`.
- [x] `_ergo_asin`: Implement via `_ergo_atan2(x, sqrt(1-x*x))`.
- [x] `_ergo_tan`: Implement via `_ergo_sin(x) / _ergo_cos(x)`.
- [x] `_ergo_log10`: Implement via `_ergo_log(x) * (1.0 / ln(10))`.
- [x] `_ergo_fmod`: exact shift-and-subtract on integer mantissas (bit-exact
  vs `fmod` over 3M+ random patterns incl. denormals; NaN/Inf/zero per C
  semantics). Real-valued `MOD` in codegen now emits `_ergo_fmod`/`_ergo_fmodf`
  by default, libm `fmod` under `--libm-fallback`.
- [x] Hyperbolics (`_ergo_sinh`, `_ergo_cosh`, `_ergo_tanh` + `f` variants):
  Taylor poly for |x| < 0.25 (no cancellation at 0), direct `_ergo_exp`
  composition mid-range, half-scaled `exp(x/2)` path above 700 (f64) / 80
  (f32) so e.g. `sinh(710) = 1.117e308` instead of overflowing to Inf;
  `tanh` clamps to +-1 beyond 20. Measured <= 5.1 ulp (f64) / <= 4 ulp (f32)
  vs libm over [-800, 800]; all NaN/Inf/zero/denormal edges match.
- [x] Wire these new functions into `C_MATH` and `OWNED_MATH` in `ir_codegen.py`.
- [x] Verified: f64+f32+fallback compile+run; core pytest 23 passed;
  golden IR-vs-legacy 16/16 MATCH; corpus 200/200 vs baseline.

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
