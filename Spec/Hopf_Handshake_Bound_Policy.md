# Hopf Handshake Bound — Prototype Compiler Policy

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

A handshake block without an oracle clause should compile with a warning in prototype mode and reject in certified mode.

### 7. GPU lowering rule

On GPU, handshake = unrolled schedule only.

Reject for GPU if:

- depth cannot be proven at compile time
- activation depends on runtime data beyond a fixed sector index
- payload contains pointers/allocatables
- mediator update requires dynamic stack
- INTEGER*8 or COMPLEX appears in the handshake frame

The mediator should lower to registers/shared state. The endpoints lower to normal STATIC field arrays.

## Future syntax sketch

Not current ergo — a planning sketch:

```ergo
HANDSHAKE PAIR DEPTH=2 FRAME_BYTES=256 MAXIT=240 &
          CONSERVE PARITY SPIN NORM
  ENDPOINT A = ATOM_LEFT
  ENDPOINT B = ATOM_RIGHT
  MEDIATOR M = PINNED_OSC MIDPOINT

  PAYLOAD M = (AMP, PHASE, SIGN, SECTOR)

  STAGE 1: PROPAGATE A COUNT=NTAU ORACLE NORM TOL=1.0E-12
  SIGNAL A -> M -> B WHEN OVERLAP(BOND) > 0.0
  STAGE 2: PROPAGATE B COUNT=NTAU ORACLE NORM TOL=1.0E-12

  ORACLE UNITED_LIMIT    R=0.2  TOL=6.0E-2
  ORACLE SEPARATED_LIMIT R=12.0 TOL=1.0E-3
  ORACLE TRIPLET_NULL
  ORACLE VARIATIONAL
ENDHANDSHAKE
```

The compiler does not emit recursive calls for this. It emits a checked schedule:

```text
check depth <= 2
check frame bytes <= 512
check no ALLOCATE in region
emit stage 1 counted loop
emit mediator fixed-record update
emit activation-token move
emit stage 2 counted loop
emit oracle checks
```

If any check fails: compile-time rejection.

## Compiler prerequisites already surfaced by the campaign

Before HHB becomes real syntax, these are the right prerequisites:

1. **A6 scalar dummy-arg copy-out** must be fixed or permanently worked around with 1-element arrays.
2. **Undefined identifier in array bound** must be a hard error — the df_radial colon-bounds failure should never become a silent “whatever ran.”
3. **Case policy** needs a spec decision; until then generated handshake code should be UPPERCASE-only.
4. **No silent fallback semantics** anywhere in the runtime: SCANFAIL must print.
5. Dual-codegen drift needs a golden-output handshake test so legacy and IR paths cannot diverge quietly.

## Suggested integration phases

**Phase 0 — pattern only:** write handshakes with existing counted DO loops, STATIC payload arrays, visited flags, and explicit oracle prints. No compiler change.

**Phase 1 — linter/static analysis:** mcl recognizes the pattern and warns on depth > 2, `ALLOCATE` in region, missing MAXIT, missing oracle, mediator writing activation flags.

**Phase 2 — directive form:** something like `VERIFY HANDSHAKE ...` or an attribute block before structured syntax exists.

**Phase 3 — real AST/IR node:** parser gains `HANDSHAKE ... ENDHANDSHAKE`; ir_builder proves the schedule finite; codegen lowers to straight-line/countable code; GPU path accepts only fully unrolled instances.

**Phase 4 — certification suite:** tests must include both positive and negative oracles.

## First certification ladder

Reuse the existing physics as the compiler test ladder:

1. **H₂⁺ parity handshake:** σg/σu stay separated; split exponent ≈ −1; midpoint coherence behaves.
2. **H₂ two-electron handshake:** singlet binds, triplet repulsive, ionic content dissolves with R, dissociation limit −1.0.
3. **HeH⁺ heteronuclear handshake:** no-parity case; triplet midpoint non-erasure; charge localization toward He.
4. **df_radial2 SCF handshake:** SCANFAIL loud-and-recover; norm-root solver rejects source-amplitude-dependent fake roots.
5. **Negative controls:** LCAO mirror v1 must fail where the engine catches it; norm-inflated stored orbitals must trip OVLMAT; wrong exchange-like integrals must trip the triplet-null/variational oracle.

## One-sentence policy

Handshake recursion is legal only as a bounded, oracle-instrumented token pass between two centers through a pinned amplitude carrier — depth ≤ 2, payload ≤ 512 bytes, no allocation, no re-entry, no silent failure.
