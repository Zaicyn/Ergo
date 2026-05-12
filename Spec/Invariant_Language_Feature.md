# INVARIANT as Language Feature — Catalogue Entry

A direction worth exploring: making geometric invariants first-class
declarations in Ergo source, with the compiler enforcing them.

This is **not a brief.** It's a catalogue of three increasingly
ambitious versions of the idea, with explicit triggers for when each
becomes worth pursuing. The same shape as
[Performance_Opportunities.md](Performance_Opportunities.md) — concrete
versions, dependencies, triggers, deliberately not a dispatchable plan.

## What this would extend

Ergo already enforces several classes of correctness at the language
level:

- **Memory:** STATIC constitution, no-hidden-allocation rule, arena
  lowering for ALLOCATABLE. The compiler refuses to introduce indirection
  the spec disallows.
- **Numerical:** Part 6 IEEE strictness, `-ffp-contract=fast` recipe,
  the determinism contract section added in x86-determinism stage 3.
  The compiler refuses to reassociate float operations.
- **Loop structure:** Part 9 FLOW/INJECTIVE/REDUCTION/SCATTER
  classifier. The compiler categorizes loops by their dependence
  pattern and routes them to appropriate parallelization.

What it does *not* currently enforce: **geometric invariants** — the
class of correctness that comes from continuous mathematical structure
underlying discrete computation. Ring conservation, topological charge
preservation, lattice-aligned tiling, phase-locked relationships.

These invariants exist in current Ergo source ([structured/fluid_subs.ergo](../structured/fluid_subs.ergo)
has 3-5 of them) but they're hand-coded. The programmer maintains the
derivation in their head; the compiler can't see the structure.

Making invariants part of Ergo's language is the same axis as the
existing enforcement work, extended to a new category: structural rather
than memory/numerical/computational.

## Prerequisite (load-bearing): Catalogue recurring invariant families first

**Before any version of this is dispatched, write the recurring-families
table.**

The idea's value depends on whether geometric invariants are a *frequently
recurring pattern* across simulation projects or a *one-off pattern* in
the current Ergo work. Different answer → different scope.

The table should cover the projects where the methodology has been
applied: Schism (molecules), Sanity (galaxies), the Ergo port (this
repo's structured/), the colony sims, the security primitives, the
communication stacks. For each, enumerate:

| Family | Concrete example | Detection mechanism | Enforcement mechanism |
|---|---|---|---|
| Ring conservation | OMEGA exchange in fluid_subs.ergo:436 | Paired add/subtract on cyclic index | Per-iteration symmetry |
| Winding preservation | Topological charge Q=1 in fluid_subs.ergo:472 | Butterfly reduction over warp | Proportional restoring force on OMEGA |
| Neighbor parity | (example from another project) | ... | ... |
| Symmetry preservation | (V8's cuboctahedral kissing-number) | Occupancy histogram | Lattice-aligned slot bookkeeping |
| Phase continuity | (example from waveguide work) | Gradient bound | Diffusion correction |

**Decision criteria after the table is written:**

- **5+ families across 3+ projects:** strong case for Version 1, clear
  set of primitives for what Version 2's library would need to support.
- **2-3 families recurring across multiple projects:** Version 1 case
  is moderate, Version 2 is premature, focus on debug-mode checks for
  the recurring ones.
- **Most families are project-specific one-offs:** the methodology lives
  in documentation and testing patterns, not in the compiler. Skip all
  three versions.

This catalogue exercise is the cheapest possible test of whether the
language feature earns its keep. Probably 2-4 hours of cross-project
review to produce. Without it, anything else here is speculation.

## Version 1: INVARIANT as named runtime check

**Pattern:** name the invariant, declare its property, compiler emits a
runtime check in debug builds, no-op in release builds.

```ergo
INVARIANT TOPOLOGICAL_CHARGE: SUM(PH_DIFF) OVER WARP = PHASE_MASK + 1
  WHEN MET_GATE > 1.49
  TOLERANCE 0
```

Note: this syntax is illustrative only. The actual syntax should be
designed *after* the recurring-families table identifies what the
common shapes are. Designing syntax up front based on one example is
the syntax trap.

**What it does:**

1. Names the invariant so it can be grepped, documented, referenced.
2. Emits a runtime check at the appropriate scope (per-iteration for
   loop-scoped invariants, per-frame for frame-scoped, etc.).
3. In debug builds, the check runs and aborts/logs on violation. In
   release builds, the declaration is documentation only.

**What it does NOT do:** prove anything. Generate enforcement code. Be
clever. It's `assert` lifted to talk about reductions and array
properties instead of scalar conditions.

**Why this version is safe:** the check evaluates a property of the
*current state*. If the check passes, the state satisfies the invariant
*right now*. If the check fails, the violation is caught immediately
and explicitly. There's no risk of the compiler silently generating
wrong code because the compiler isn't generating enforcement code — only
verification code.

**Value beyond debug:**

- **Observability.** Named invariants become trackable: graph them over
  time, attach tolerances, classify failure modes. Debugging shifts from
  "the sim feels wrong" to "Invariant TOPOLOGICAL_CHARGE diverged at
  frame 1824 after coastline exchange update."
- **Semantic anchors.** Future-you, collaborators, or implementers
  picking up the code see the invariants as first-class objects rather
  than scattered comments. The methodology pattern gets *preserved by
  the source* rather than living in the original author's memory.
- **Regression testing.** Named invariants can be checked across runs;
  drift between versions becomes visible.

**Dependencies:** zero new external. Compiler work in
[mcl/parser.py](../mcl/parser.py),
[mcl/checker.py](../mcl/checker.py),
[mcl/ir_codegen.py](../mcl/ir_codegen.py) for emit, possibly
[mcl/backends/spirv.py](../mcl/backends/spirv.py) for GPU-side reductions
the invariant needs (already partially available via WARP_BALLOT etc.).

**Estimated effort:** 2-3 weeks of compiler work after the catalogue is
done. The bulk is the syntax design (driven by catalogue), the parser,
the scope-tracking for "where does this invariant apply", and the
codegen for the check itself.

**Trigger:** the recurring-families catalogue shows ≥3 recurring families,
OR the next time a debugging session involves manually tracking an
invariant violation across frames. Either is sufficient.

**Priority:** highest of the three. The risk is low, the value is real,
the trigger is easy to fire.

## Version 2: INVARIANT as code generator

**Pattern:** the programmer declares the invariant; the compiler emits
both the check *and* the enforcement code (the restoring force, the
paired symmetric exchange, the lattice-aligned bookkeeping).

```ergo
INVARIANT TOPOLOGICAL_CHARGE: SUM(PH_DIFF) OVER WARP = PHASE_MASK + 1
  WHEN MET_GATE > 1.49
  RESTORING OMEGA WITH K_WINDING
```

The compiler reads this and emits the 6-line butterfly-reduction-and-
correction sequence currently hand-written at
[structured/fluid_subs.ergo:472-498](../structured/fluid_subs.ergo#L472).

**Why this is dangerous:**

Version 2 creates the illusion of correctness without the derivation.
If the compiler's emitted enforcement is subtly wrong (the
V16-failure-mode: replace Viviani scatter with "algebraically simpler"
hashing, look correct at the type-checker level, break the
equidistribution property the geometry was preserving), the simulation
runs, produces visibly weird results after some frames, and the
programmer trusts the declaration *because the compiler accepted it*.

The danger is the inversion of authority: in current Ergo, the
programmer is the authority on what enforcement code is correct (because
they wrote it from the derivation). In Version 2, the compiler is the
authority. The compiler is wrong by exactly as much as its library of
primitives doesn't capture the geometric structure correctly.

**What needs to exist before Version 2 is dispatched:**

1. **A formal specification of each primitive in the library.** "Ring
   conservation" needs a definition that's machine-checkable, not just
   "the compiler does the obvious thing for this pattern." The
   specification is what allows the compiler's emitted code to be
   *trusted*.
2. **Validation that the primitive's emitted code matches a known-good
   hand-written reference.** Each primitive in the library gets a
   golden test: a hand-coded example (from existing Ergo source, V8,
   V22, etc.), the compiler-emitted version, byte-or-behavior diff. If
   they don't match, the primitive needs work before it ships.
3. **A clear list of what the library does *not* cover.** Programmers
   need to know when to fall back to hand-coded enforcement because
   their pattern isn't in the library. Otherwise they'll declare an
   `INVARIANT` for a pattern the compiler half-handles and silently get
   wrong code.

The primitive library is its own design exercise, larger than the
compiler integration. Likely months of work, with the actual difficulty
being the *specification* not the *implementation*.

**Dependencies:** zero new external. Compiler work, but substantial.

**Estimated effort:** 2-4 months including the primitive library
design and validation.

**Trigger:** all of the following:
- Version 1 has been deployed and the recurring-families catalogue has
  grown to ≥5 families.
- The compiler team (or implementer) has a formal specification of at
  least the top 3 primitives, with golden tests.
- A real project has been blocked by "writing the same enforcement
  pattern for the Nth time" and wants the compiler to handle it.

Without all three, Version 2 is speculative and dangerous. With them,
it's a meaningful capability extension.

**Priority:** medium-low. The conditions to dispatch it safely are
substantial, and Version 1 captures most of the immediate value
without the risk.

## Version 3: INVARIANT as proof obligation

**Pattern:** the compiler doesn't generate enforcement; it *verifies
that the surrounding code already maintains the invariant*. Build fails
(strict mode) or warns (permissive mode) if the proof can't be
constructed.

```ergo
INVARIANT RING_CONSERVATION: SUM(OMEGA) OVER RING = CONSTANT
  UNDER METABOLIC_EXCHANGE
  PROVE
```

The compiler analyzes the metabolic-exchange code, recognizes that each
`OMEGA(I) -= TRANSFER; OMEGA(I+1) += TRANSFER` is a paired add/subtract
on a ring, and verifies conservation. If a programmer breaks the pairing
(`OMEGA(I) -= TRANSFER * 0.99`), the build fails.

This is V22's algebraic-zero pattern lifted into the compiler. V22's
residual returns `0.0f` because the algebra proves it; Version 3
returns "build successful" because the algebra of the surrounding code
proves the declared invariant.

**Why this is the hardest version:**

Theorem provers metastasize. A constrained prover for "ring sums" sounds
manageable. Users immediately want nested domains, conditional
invariants, stochastic tolerances, temporal invariants, multi-scale
coupling, emergent-region assertions. The compiler architecture becomes
about proof management. That can swallow years.

**Why it might still be worth doing eventually:**

For production deployment, security-relevant code, or anything where
the cost of a silent invariant violation is high, build-time proof is
qualitatively different from runtime check. Version 1's check fires
*after* the violation happens; Version 3's proof prevents the violation
from ever existing in shipped code.

This matches the "discipline over convenience" axis Ergo already
optimizes for. Other languages have refinement types (Liquid Haskell),
separation logic (Iris), dependent types (Idris); none of them target
*physical* invariants on GPU compute kernels. That niche is what Ergo
would occupy.

**What needs to exist before Version 3 is dispatched:**

- Version 2 has been deployed and used in production.
- A real project has had a silent invariant violation cost something
  meaningful (debugging time, wrong scientific result, production
  incident).
- The compiler team has bandwidth for a substantial theorem-prover
  subproject without it derailing the rest of Ergo's development.

**Dependencies:** zero new external for the prover itself, but
*ecosystem* dependencies are real — a proper proof obligation system
needs documentation, examples, error messages, IDE integration, and
ongoing maintenance. None of those are free.

**Estimated effort:** 6-12 months for a constrained first version,
plus indefinite ongoing maintenance.

**Trigger:** Version 2 deployed + a concrete incident where Version 1's
runtime check fired too late to prevent damage + bandwidth for a
substantial compiler subproject.

**Priority:** lowest. The conditions to dispatch it responsibly are
extensive. It's the dream, not the plan.

## What's deliberately not specified here

Following the catalogue-not-brief pattern:

- **Syntax.** Designed after the recurring-families table identifies
  shapes. Starting with syntax is the trap.
- **Implementation order.** Even within Version 1, the right order of
  invariant families to support depends on which appear most in the
  catalogue. Don't pre-commit.
- **Integration with existing classifiers.** Whether INVARIANT becomes a
  new IR node, a decoration on existing nodes, or something else is a
  design choice that comes after Version 1's scope is concrete.

## Summary

| Version | What it does | Risk | Value | Trigger |
|---|---|---|---|---|
| Catalogue | Document recurring invariant families across projects | Near-zero | Determines whether any of V1-V3 are worth doing | Now, before any version is dispatched |
| Version 1 | Named runtime checks in debug builds | Low | Observability, semantic anchors, regression testing | Catalogue shows ≥3 families, or next manual invariant debugging session |
| Version 2 | Compiler emits enforcement code from declarations | High (V16-failure-mode risk) | Eliminates repeated hand-coding of common patterns | V1 deployed + formal primitive specs exist + concrete need |
| Version 3 | Compiler proves invariants hold given surrounding code | Very high (theorem-prover scope creep) | Build-time correctness for production/security code | V2 deployed + concrete incident + sustained bandwidth |

**The one concrete next step:** if this direction is worth pursuing at
all, write the recurring-families catalogue. 2-4 hours of cross-project
review. The catalogue's content determines whether Version 1 is the
obvious next move, whether the whole direction is justified, or
whether the methodology lives better in documentation than in the
compiler.

The honest framing the methodology pattern keeps reinforcing: don't
build the language feature speculatively. Measure the recurrence first.
The catalogue is the measurement.
