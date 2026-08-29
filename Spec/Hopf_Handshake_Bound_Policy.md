# Hopf Handshake Bound — Compiler Policy (ratified 2026-08-28)

Drafted as a prototype policy from the H₂⁺ / H₂ / df_radial2 campaigns;
ratified after Phase 0–4 implementation and the certification ladder
(scoreboard: HHB_IMPLEMENTATION_PLAN.md). Language-rule summary:
Ergo_Spec.md Part 11.

Source inspiration: H₂⁺ handshake findings, H₂ two-electron handshake findings, and the df_radial2 / Wigner-stage certification findings.

## Core rule

Recursive handshake syntax is allowed only when the compiler can lower it to a **static finite schedule**. No runtime call stack. No data-dependent recursion. The recursion expresses topology: center → mediator → center. It must never express search.

Physical picture: the bonding signal activates the next parity group; the middle ion cloud carries amplitude/phase only. The mediator has **no control authority**.

## HHB policy clauses

### 1. Fixed shape — tri-ionic single connection

A handshake unit has exactly:

- endpoint A
- one mediator / pinned oscillator
- endpoint B

No fan-out. No mediator spawning new mediators. A paired hopfion is the maximum composite: two handshake units, explicitly declared.

Compiler rule: if the activation graph is not a chain of length ≤ 2 per declared hopfion unit, reject.

### 2. Activation is monotonic

Each stage has a visited bit. Once a parity group fires, it stays fired for that step. The bonding token moves forward only.

Allowed:

```text
FIRED(1) = false → true → signal to mediator → FIRED(2) = true
```

Forbidden unless separately budgeted:

```text
FIRED(2) → reactivates FIRED(1)
```

If rewind/recoil is wanted later, make it a separate construct with its own counter, e.g. `MAX_REWIND = 1`, not part of the base handshake.

### 3. Payload is tiny and fixed

The mediator may carry only a fixed record:

```text
AMP      REAL
PHASE    REAL
SIGN     INTEGER   ! singlet/triplet, bonding/antibonding phase bit
SECTOR   INTEGER   ! parity / κ / symmetry channel
TARGET   INTEGER
STATUS   INTEGER
```

Use REAL pairs instead of COMPLEX. Keep INTEGER*8 off GPU.

The 512-byte idea works as a **control-block budget**, not as storage for fields/orbitals/Wigner maps. Formal form:

```text
HS_FRAME_BYTES = 256
HS_MAX_DEPTH   = 2
HS_TOTAL_BYTES = 512
```

Paired maximum uses ping-pong frames inside one static 512-byte block. Bigger physical state — orbitals, densities, maps, SCF potentials — stays in normal `STATIC` arrays outside the handshake control block.

### 4. All loops are counted

No naked convergence loop inside a handshake. Every iterative propagation has:

```text
MAXIT       compile-time or PARAMETER bound
STATUS      loud result code
ORACLE      required invariant check
```

Policy rule from df_radial2: never silently keep the old value after a failed scan. Either recover loudly within a bounded attempt ladder, or abort.

Two failure classes:

- **Recoverable numerical miss:** print `HS_SCANFAIL`-style diagnostics — cycle, stage, kept epsilon, pole count — then widen at most three bounded attempts.
- **Structural violation:** depth overflow, re-entry, payload overflow, allocation inside handshake, broken invariant → hard error.

**Bounded attempt loops (added 2026-08-28, implemented):** a `DO WHILE`
inside a handshake region counts as a counted loop when the compiler proves
ALL of: condition is `counter < bound` (strict, counter a single INTEGER,
bound a compile-time constant or PARAMETER); the counter's last write before
the loop in the same scope is a constant; exactly one unconditional top-level
increment `counter := counter + 1` per iteration; every other counter write
is a forced exit inside an IF assigning a constant >= bound. The proof is
emitted as the loop's implicit MAXIT in the lint diagnostics; anything not
matching keeps the hard `hhb_uncounted` error. On the GPU path the proven
loop is unrolled at its bound into predicated straight-line copies inside
the kernel body (a forced exit makes later copies no-ops — exact while
semantics), so an enclosing counted loop stays extractable (policy §7's
"unrolled schedule only" now covers the attempt ladder).

### 5. Sector invariants are part of the type

The handshake declares what it preserves:

```text
CONSERVE PARITY
CONSERVE SPIN
CONSERVE NODE_COUNT
CONSERVE NORM
```

For H₂⁺ this is parity: σg/σu do not mix under imaginary time. For H₂ this is antisymmetry: the sign of the bond is carried by singlet/triplet sector, not by extra looping. For df_radial2 this is Sturm ordering plus norm-root selection.

Baked-in numerical rule: sign/pole detection must use logical signbit tests, never products. The df_radial2 W0 ~ 1e180 case is the reason product-based sign tests are disallowed in handshake oracles.

### 6. Oracles are mandatory, not decorative

Every handshake stage must expose at least one null/limit oracle. Reusable oracle set:

- norm/Parseval: `WNORM = 1` or particle-count norm to ~1e-12/1e-14
- united-atom limit
- separated-atom limit
- variational direction: CI/grid energy must not overbind
- triplet-null test: no bound triplet where physics forbids it
- dissociation limit: correct separated-atom energy
- screened-vs-hydrogenic distinction: hydrogenic values are baselines, not targets, once screening exists
- byte-determinism: same input → same output hash

Measured caveat (2026-08-28, HHB Phase-4 NC3): a fixed-window oracle
(e.g. a singlet-triplet gap asserted inside (0, 20) Ha at every R)
catches sign flips and norm drift but NOT structure-preserving wrong
integrals — an exchange read at a slipped index produced plausible gaps
inside the window at every R. The discriminator is the dissociation
limit (the corrupted split persisted at 0.196 Ha vs the correct 0.0006
at R=6): the dissociation-limit oracle must be wired per-program (e.g.
as a post-loop boundary check), not assumed to fall out of a window.

A handshake block without an oracle clause should compile with a warning in prototype mode and reject in certified mode.

### 7. GPU lowering rule

On GPU, handshake = unrolled schedule only.

A bounded loop inside a verified handshake unrolls into predicated
straight-line kernel copies when its proven bound ≤ 64; larger bounds
keep the runtime loop, which blocks extraction of any enclosing loop
(structural cliff: identical output, but the kernel runs on CPU).
This applies to counted loops and to proven bounded-attempt loops
(§4) alike.

Reject for GPU if:

- depth cannot be proven at compile time
- activation depends on runtime data beyond a fixed sector index
- payload contains pointers/allocatables
- mediator update requires dynamic stack
- INTEGER*8 or COMPLEX appears in the handshake frame

The mediator should lower to registers/shared state. The endpoints lower to normal STATIC field arrays.

## Syntax (implemented 2026-08-28, Phase 0–4 complete)

Current ergo — two forms, same lowering:

```ergo
VERIFY HANDSHAKE h2_scf DEPTH=2 FRAME_BYTES=256 MAXIT=240 &
       CONSERVE NORM PAYLOAD=(NRM) ORACLE NCHK VALUE=1.0 LIMIT=1.0E-9
  <statement>

HANDSHAKE h2_scf DEPTH=2 FRAME_BYTES=256 MAXIT=240 &
          CONSERVE NORM PAYLOAD=(NRM) ORACLE NCHK VALUE=1.0 LIMIT=1.0E-9
  <statements>
ENDHANDSHAKE
```

The compiler does not emit recursive calls. It emits a checked schedule:

```text
check depth <= 2
check frame bytes <= 512
check no ALLOCATE in region
emit counted stages (bounded-attempt loops unrolled at their proven bound)
emit mediator fixed-record update
emit oracle checks (entry capture + boundary checks)
```

If any check fails: compile-time rejection. A failed oracle at runtime
aborts with `HHB_SCANFAIL` (actual/expected/tol), exit 1.

Still future work: the richer ENDPOINT/MEDIATOR/STAGE/SIGNAL declarative
form (explicit topology naming, `SIGNAL A -> M -> B WHEN ...`). The
implemented forms annotate existing counted-loop structure rather than
declaring the topology; the policy limits above are enforced identically
under either form.

## Compiler prerequisites surfaced by the campaign (all landed)

These were prerequisites for real syntax; all are in now:

1. ~~A6 scalar dummy-arg copy-out~~ — fixed (language batch 1).
2. ~~Undefined identifier in array bound~~ — hard error (batch 2).
3. Case policy — settled; spec is the authority.
4. ~~Silent fallback semantics~~ — SCANFAIL prints and aborts (exit 1).
5. ~~Dual-codegen drift~~ — golden handshake test pins legacy and IR paths.

## Integration phases (all complete)

- **Phase 0–2** — pattern, linter (`core/hhb_lint.py`), `VERIFY HANDSHAKE` directive: done.
- **Phase 3** — `HANDSHAKE ... ENDHANDSHAKE` AST/IR node, schedule-finiteness proof, GPU unrolled lowering: done.
- **Phase 4** — certification suite with positive and negative oracles: done (scoreboard in HHB_IMPLEMENTATION_PLAN.md).

## Certification ladder (complete)

All five rungs pass; all three negative controls trip. Full scoreboard
with oracle values: HHB_IMPLEMENTATION_PLAN.md, Phase-4 section.

1. **H₂⁺ parity** — σg/σu separated, WNORM = 1 to 1e-13.
2. **H₂ two-electron** — singlet binds, triplet repulsive, dissociation −1.0.
3. **HeH⁺ heteronuclear** — no-parity case, charge localizes toward He.
4. **df_radial2 SCF** — SCANFAIL loud-and-recover.
5. **Negative controls** — norm inflation, wrong mirror value, and (after
   the NC3 hole was found and closed) wrong exchange integrals all abort
   with HHB_SCANFAIL.

## One-sentence policy

Handshake recursion is legal only as a bounded, oracle-instrumented token pass between two centers through a pinned amplitude carrier — depth ≤ 2, payload ≤ 512 bytes, no allocation, no re-entry, no silent failure.
