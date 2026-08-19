# Ergo — Fix-First List

Two buckets: **ASAP** (things actively producing wrong results, crashes, or
silent divergence today) and **Adoption roadblocks** (things that will stop
anyone but the author from using the language, even if the language itself
is sound). Compiled 2026-08-12 from the AB campaign debugging sessions,
the 2026-07-21 bugfix changelog, the locked spec (Parts 1–9), and the
Arena Lowering Brief.

Priority within each bucket is ranked by blast radius, not effort.

---

## ASAP — correctness and crash bugs

### A1. Local NPTS-scale arrays segfault at runtime
- **Symptom:** 8 × 262144-double local arrays = 16.8 MB stack frame > 8 MB
  default stack → SIGSEGV in the first setup loop (faulting store at
  rbp−0x1000378). No diagnostic, compiles clean.
- **Hit:** Stage 5 (`ab_recoil.ergo`), 2026-08. Cost a full debugging cycle
  (gdb, disassembly) to identify.
- **Fix (chosen):** hoist PARAMETER-sized local arrays to file-scope static
  storage in codegen — the same lowering `STATIC` already gets.
- **Interim (cheap, do even if hoisting lands):** compile-time warning when a
  local array's compile-time-known size exceeds ~1 MB: "local array R(NPTS)
  is 2.0 MB on the stack; declare STATIC or raise ulimit".
- **Spec angle:** STATIC already exists and is the correct explicit answer;
  the bug is that the *default* path is a trap.

### A2. Dual codegen paths can silently diverge
- **Symptom:** legacy AST codegen (`codegen.py`) and IR codegen
  (`ir_codegen.py`) implement the same language independently. F7/F8-class
  bugs (negative-step DO, implicit function return) were fixed in legacy but
  are **unverified in the IR path**. COMPLEX already diverges by design
  (loud error vs `double _Complex`).
- **Why this is existential:** the language's entire value proposition is
  "the compiler refuses to lie to you." Two backends that can disagree
  *silently* are a determinism violation waiting for a victim.
- **Fix:** golden-output test — a corpus of small programs compiled through
  both paths, run, stdout + `ERGO_HASH_FINAL` diffed. Wire into whatever
  passes for CI. Then treat any future divergence as a test failure, not a
  judgment call.
- **Follow-up:** decide whether legacy is deprecated (document it) or
  maintained (then every fix lands twice, enforced by the golden test).

### A3. Half-landed features with silent or surprising behavior
- **COMPLEX:** IR path raises (F6, correct); legacy path lowers to
  `double _Complex` (numerics neither path has validated). Until COMPLEX is
  real, both paths should raise the same error.
- **Ring intrinsics (RING_PREV/NEXT/SHIFT):** GPU-path only, hard-coded
  32-lane assumption, absent from the CPU front-end and from the locked
  intrinsics doc. Portability landmine on non-32-wavefront GPUs; silent
  absence on CPU.
- **VERIFY directive:** parsed (F1/F2 fixed) but absent from the intrinsics
  doc. Either spec it or remove it.
- **Fix:** one "implementation status" column in the intrinsics doc —
  CPU / GPU / planned / removed — per intrinsic. Half a day of doc work,
  prevents every "wait, does X exist?" ambiguity going forward.

### A4. WRITE/format marshaling fragility
- **Symptom:** `%+.4f` in a format string compiled fine; binary crashed at
  runtime (root cause that day was A1, but the flag path was suspicious
  enough to burn time on — the marshaling is clearly undertested).
- **Fix:** audit the WRITE lowering's format-flag handling; either support
  the full flag set or reject unsupported flags at compile time with a named
  error. A format string should never be a runtime-dice-roll.

### A5. IR-path verification debt from the 2026-07-21 batch
- F7 (negative-step DO bounds hoisting) and F8 (implicit `return <name>_;`)
  landed in legacy only. The changelog itself flags both as "same check
  needed for ir_codegen.py."
- **Fix:** port + test both. Small, mechanical, currently a known hole.

### A6. Scalar SUBROUTINE dummy args don't copy out (silent wrong answers)
- **Found:** 2026-08-12, octonion battery + 5 probes (oct_rand_probe*.ergo).
- **Symptom:** a SUBROUTINE that writes a scalar (non-array) dummy arg
  (`X := 42.0`) leaves the caller's variable unchanged; arrays pass back
  fine. Probe5 reproducer: `SET42 -> 0.0`, `ADD1 -> unchanged`,
  `DMAX2 -> 0.0`. Consistent with scalar dummies lowered by value in C
  (`double X_`) instead of by pointer (`double *X_`), i.e. Fortran's
  pass-by-reference semantics only implemented for arrays.
- **Blast radius:** any "return through arguments" scalar — accumulators,
  error codes, min/max helpers — silently returns garbage/stale values with
  no error. Worst possible failure mode for a determinism-first language:
  the octonion battery computed a correct 1.67 associator and reported 0.
- **Workaround (verified):** pass scalars home in 1-element arrays.
- **Fix:** pointer-lower scalar dummies in codegen (both paths — see A2);
  add a golden test: SET42 / ADD1 / DMAX2 from probe5.

---

## Adoption roadblocks — will stop new users cold

### R1. Error messages don't teach
- Real examples from this month: single-line `IF (c) stmt` →
  "Expected ':=' in assignment" (tells the user nothing); top-level `END` →
  "Unexpected token: KW_END"; ATAN2 with INTEGER args → at least that one
  names the problem.
- **Why it blocks adoption:** the dialect is deliberately minimal (block IF
  only, no PROGRAM/END wrapper), which is fine — but then the parser is the
  only teacher a new user has. Each error should name the construct expected
  and the likely cause: "single-line IF is not supported; use IF/THEN/ENDIF".
- **Fix:** one pass over ParseError sites for the top ~10 beginner mistakes;
  each gets a message + suggestion. High leverage per hour spent.

### R2. The spec and the implementation have drifted
- Locked spec (Parts 1–9) is the product's spine, but: ring intrinsics
  aren't in it, VERIFY isn't in the intrinsics doc, case policy has no
  decision, COMPLEX is unspecified while half-implemented. The spec says
  "a rule the compiler silently violates is worse than no rule" — the same
  applies to features that exist but aren't ruled.
- **Fix:** spec amendment pass — one section per drifted feature with a
  status tag (see A3). Includes the **case-policy decision** (identifiers
  case-sensitive + keywords case-insensitive + mixed intrinsic dispatch is
  currently the de-facto behavior; need to make this case insensitive by default if possible, user's choice).

### R3. No documented "first program" path
- A newcomer currently needs to learn by osmosis: house dialect (IMPLICIT
  NONE, no PROGRAM/END), STATIC-for-big-arrays rule, block-IF-only,
  build invocation, `--arena-size`, determinism flags. All of it exists —
  scattered across the spec, briefs, and tribal knowledge.
- **Fix:** one short "hello, stencil" walkthrough in the spec repo: minimal
  program → compile → run → ERGO_HASH_FINAL → "now make the array big and
  watch why STATIC matters". The spec stays the constitution; this is the
  citizenship test.

### R4. `tests/` is gitignored (whitelist mode)
- Flagged in the Arena brief as out-of-scope, but it means validation
  harnesses require force-add, collide at merge time, and are invisible to
  anyone cloning the repo. For a language whose pitch is *verifiability*,
  shipping without a visible test corpus undercuts the pitch.
- **Fix:** un-ignore `tests/`, add a `tests/.gitignore` for ephemera
  (binaries, .spvasm dumps). Pairs naturally with the A2 golden corpus.

### R5. Un-fortran loop-variable semantics (legacy path)
- `for (int I = ...)` shadows the outer declared `I`; the loop var doesn't
  retain its final value after the loop. Anyone coming from Fortran — the
  exact audience the syntax courts — will get this wrong on day one.
- **Fix:** emit the assignment to the user-visible variable at loop exit
  (or declare the loop var at function scope). Known issue since 2026-07-21,
  deliberately deferred; it belongs on the ASAP-adjacent list because it's
  a *semantics* surprise, not an ergonomics one.

### R6. No array-level expressions (accepted trade-off — document the why)
- `A := B + C*D` on arrays is illegal by design (no temporaries). Correct
  call for the determinism/no-hidden-allocation philosophy, and physics
  stencils want explicit loops anyway — but it's the first thing a
  numpy/MATLAB/Fortran-90 user will try.
- **Fix:** not a code change — one paragraph in the spec/rationale doc
  explaining *why* (no implicit temporaries, ever) with the idiomatic
  loop pattern shown. Turns a frustration into a philosophy lesson.

---

## Explicitly NOT on this list

- **JIT (jit_x86) instability** — experimental path, documented as unstable;
  not on the critical path for correctness or adoption.
- **GPU/Vulkan evolution (Inc-3 elliptic rewrites, clipmap extensions)** —
  active development, not debt.
- **Allocator sophistication (freelist, thread-safety, NUMA)** — the Arena
  brief correctly rules these out of scope; bump-only is the spec.
- **`_func_params` string-sliced declarators, `_lower_if` dead code** —
  fragile/cosmetic internals; fix opportunistically when touched, no
  user-visible impact today.

---

## Suggested sequencing

1. **This week:** A1 interim warning + A3 status column + A5 ports (all
   small, all close known holes).
2. **Next batch-fix session:** A2 golden test + A4 WRITE audit + case-policy
   decision (R2) + R5 loop-var semantics.
3. **Before showing anyone outside:** R1 error-message pass + R3 walkthrough
   + R4 tests/ un-ignored. That's the "another human can use this" gate.
4. **A1 hoisting** whenever codegen is open anyway — the warning makes it
   non-urgent, the hoist makes it gone.
