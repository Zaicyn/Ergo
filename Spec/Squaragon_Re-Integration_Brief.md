# Squaragon Re-Integration — Intent Brief

## What this is

A statement of intent, not a plan. Squaragon was originally designed as
the structural core of the Ergo project — the geometric primitive that
allocation, scheduling, and physics all derive from. At some point early
in the project's history that role was replaced with parallel mechanisms
(flat atomic counters for spawning, raw thread-ID scheduling, force-field
modulation that uses the Viviani LUT but doesn't structurally depend on
it). The methodology drifted away from "geometry is the map" and toward
"geometry is a force you apply."

This brief exists to mark that the drift is recognized and the
re-integration is desired. The implementer session that picks this up
will need to do the actual planning — this document only names the
intent and the constraints.

## What changed

The Squaragon design is described in the documentation that survives
([Testing/PROJECT_THESIS.md](../Testing/PROJECT_THESIS.md),
[allocator/sq2core.f](../allocator/sq2core.f),
[tests/sq3core.ergo](../tests/sq3core.ergo)) and in the original C
library at [Testing/V22/](../Testing/V22/). The methodology is intact;
the wiring in Ergo's physics workloads is not.

Three specific roles Squaragon was meant to fill in Ergo:

1. **Allocator.** Particle slots, grid cells, and any dynamic state
   should be claimed via Squaragon's geometric scatter (Viviani LUT
   into 2×8×32 torus slots), not via flat atomic counters or
   pre-allocated STATIC tables. Current state: `SPAWN_COUNTER` in
   [structured/fluid_state.ergo:30](../structured/fluid_state.ergo#L30)
   is a flat atomic; ALLOCATABLE goes through the arena bump landed
   in the determinism arc. Both work; neither is geometric.

2. **Scheduler.** Warp/lane assignments and the order in which
   particles are processed should derive from geometric position
   (which bin, which ring slot, which shell) rather than from raw
   thread ID. Current state: thread ID and `GlobalInvocationId.x` are
   the scheduling primitive everywhere. The SORT_BY_GEN directive
   exists as compiler infrastructure but isn't invoked by any shipping
   workload.

3. **Physics organization.** The Viviani LUT (`CURVE_PT`, `TANGENT`)
   currently appears as a force-field reference particles align toward
   (step 9 of the physics integrator in
   [structured/fluid_subs.ergo:319](../structured/fluid_subs.ergo#L319),
   phase-lock at line 413). That use survives. What's missing is the
   *structural* use — the geometry deciding how particles are
   distributed across slots, not just where the force pulls them.

Roles 1 and 2 are what got removed. Role 3's force-field use survives
but is decoupled from the allocator/scheduler that should have produced
the spatial structure it operates on.

## When and where the breakage actually happened

**The flattening predates git.** A history audit (May 2026) confirmed
that the first commit on master (`a8944c5`, April 27) is a 22K-line
initial commit that already contains the flattened form. The April 26
archive snapshot in [archive/2026-04-26/](../archive/2026-04-26/) and
[archive/2026-04-26-net/](../archive/2026-04-26-net/) shows the same
post-flattening state with a slightly different organization.

The flattening happened at the **C → Ergo port** before any of this
landed in version control. At port time, Squaragon's role as a runtime
allocator and scheduler was translated into:

- `FLOW_MODE(32)` — a 32-int constant LUT (`DATA FLOW_MODE / 0, 1, 1,
  1, 2, ... /`), consulted per particle every frame.
- `TANGENT(3, 32)` — a 96-float Viviani curve LUT, used as a force
  field in the physics integrator.

What was lost: the *runtime structure* — Squaragon's slot claim
(`SQ2FAL`), its scatter-based placement, its torus geometry as the
organizing principle for memory layout and execution order. What was
kept: the *geometric constants derived from Squaragon* baked in as
LUT data the physics reads.

**Implication for the implementer session:** there is no git diff to
revert. The reference for what Squaragon-cored Ergo *should* look like
has to come from outside the git history. The candidates are:

- The original C server source (`server_main.c`, `sim_*.h`) if
  recoverable — the design that was ported from, with Squaragon still
  structural.
- The Fortran reference at [allocator/sq2core.f](../allocator/sq2core.f)
  — the same algorithm in F77, useful for the allocator math but not
  for the wiring decisions.
- The C library at [Testing/V22/](../Testing/V22/) — the geometric
  primitives, residual computation, and `SQ2_*` family in their
  current canonical form.
- [tests/sq3core.ergo](../tests/sq3core.ergo) — the Ergo expression of
  the allocator pattern, just landed today (May 2026). Correct
  bit-pack, verified by SQ3VAL, but isolated from physics code.

The implementer's first move is therefore **research, not code
archaeology**. Reconstruct what the Squaragon-cored design *should*
look like from the surviving reference material, then design the
wiring back into the live physics code. Skipping this step and
attempting "find the commit that broke it" will waste time on a search
with no answer.

**Scope-of-target note:** the live physics code in [structured/](../structured/)
plus [galaxy_structured.ergo](../galaxy_structured.ergo) is compact —
most of the project's line count is in the Vulkan runtime
([mcl/runtime/vk_host.c](../mcl/runtime/vk_host.c) ~3900 lines) and the
compiler ([mcl/](../mcl/) ~12K lines), neither of which the
re-integration needs to touch. The actual physics surface that needs
re-wiring is on the order of a few hundred lines across
fluid_state.ergo, fluid_subs.ergo, and constants.ergo. Don't be
intimidated by the project's total line count; the load-bearing
surface for this work is small.

## What the re-integration aims for

The intent is to make Squaragon (specifically the v3 refinement in
[tests/sq3core.ergo](../tests/sq3core.ergo)) the canonical source of
spatial structure for Ergo physics workloads. Not a new layer on top
of the existing mechanisms; a *replacement* for them in roles 1 and 2,
and a *connection point* to role 3 so that the field a particle
experiences is consistent with the slot it occupies.

Operationally that means:

- Particle spawn paths claim slots via SQ3FAL (or its multi-thread/GPU
  analog), not via atomic spawn counters.
- The slot a particle occupies determines its GEN bin, its ring
  position, and therefore which Viviani tangent it experiences — all
  from the geometry, not from separate bookkeeping.
- Scheduling traversal order is geometric (across bins, across ring,
  across shells) rather than thread-ID order. SORT_BY_GEN or its
  equivalent becomes load-bearing rather than dormant.
- The arena lowering that was added during the determinism arc
  ([Spec/Arena_Lowering_Brief.md](Arena_Lowering_Brief.md)) becomes
  a fallback for non-Squaragon allocations; the primary path for
  physics state is through Squaragon.

## Constraints worth preserving

The work that's landed since the original removal is real and should
not be undone. Specifically:

- **Determinism contract.** The x86 determinism arc and SPIRV peephole
  work produce a build pipeline that delivers bit-identical output
  across rebuilds. Whatever Squaragon re-integration does, it must
  preserve this. Hash validation (`ERGO_HASH_FINAL`) is the existing
  oracle for catching regressions.
- **sq3core's verified bit-pack.** v3 introduced the integer-only
  fast path, the SQ3VAL verifier, and the bit-twiddle seam encoding.
  Whatever wiring gets done should consume v3 as-is, not require
  Squaragon changes underneath.
- **The arena lowering.** ALLOCATABLE → arena bump is correct and
  shipping. Squaragon doesn't replace the arena; Squaragon provides
  a *different* allocation surface (geometric, fixed-size, for
  physics state) that coexists with the arena (bump, variable-size,
  for explicit ALLOCATE statements).
- **The Performance_Opportunities and Invariant_Language_Feature
  catalogues.** Coast lane work, REDUCTION→GPU extraction, INVARIANT
  V1 — these remain valid follow-ups. Squaragon re-integration may
  intersect with them (especially coast lane, which depends on
  SORT_BY_GEN being active) but doesn't replace them.

## What this brief does not specify

Deliberately:

- Concrete code changes. The implementer session has to figure out
  what to wire and where.
- Order of operations. There's a real sequencing question (does the
  allocator get replaced first, or the scheduler, or do they need to
  land together) and the right answer depends on what the implementer
  finds when they audit the current state.
- Determinism baseline migration. The current canonical hash
  `-1975039029` for sq2core/sq3core and `c92852dba55f3b34` for
  galaxy_structured are pre-re-integration. Post-re-integration
  hashes will differ. The implementer needs to decide how to handle
  the baseline transition (tag the pre-state, document the new state,
  preserve the validation methodology across the change).
- GPU vs CPU split. Squaragon was originally a CPU allocator. The
  current galaxy_structured physics is mostly GPU. Whether
  Squaragon-on-GPU is a port of sq3core or a new design informed by
  V8's slab work is a real question the implementer needs to address.
- Whether to restore SORT_BY_GEN as part of this work, or whether
  scheduling re-integration is a separate follow-up. Coast Lane Brief
  has a relevant prerequisite (warp coherence after sort) that
  intersects with the scheduling part of this work.

## Methodology reminder

The pattern from prior briefs applies:

1. **Pre-flight grep before any code changes.** Audit what's currently
   wired where. The previous session's investigation found Viviani
   used as a force field but not as structure; the implementer should
   verify that's still the state and find every site that would need
   to change.
2. **Predict before measure.** State what the post-re-integration
   behavior should look like (hash values, throughput, frame rate)
   before running anything. Stop and diagnose if reality diverges from
   the prediction.
3. **Stage the work.** This is too large for one PR. Probably 3-5
   stages, each independently validatable. The arena lowering and x86
   determinism arcs are the precedent for staging shape.
4. **Document corrections back into the brief.** When the audit
   reveals something this document gets wrong, update this document
   rather than working around it. Future readers should see the
   corrected picture, not the original guess.

## What the implementer session should produce

At minimum, before any code changes:

- A current-state audit. Where exactly is the spawn path? What does
  the scheduler look like today? What invariants does the existing
  physics rely on that the re-integration must preserve?
- A staged plan. Probably looks like (a) pre-flight diagnostics,
  (b) restore sq3core wiring for one specific allocation site
  end-to-end, (c) extend to additional sites, (d) restore scheduling,
  (e) cross-validation against the original C library's behavior if
  applicable.
- An explicit decision about the determinism baseline. Either
  preserve the existing hashes by careful migration, or migrate the
  baseline with a clear tag and documentation.

The implementer doesn't need to ship the re-integration in one
session. The first session's deliverable is a plan that the next
session can dispatch from.

## Why this matters

The methodology you've validated across multiple projects (Schism,
Sanity, the C engines, V8, V22) is *derive geometry first, encode
invariants, let the runtime collapse to the discrete consequences of
continuous proofs*. Ergo as currently shipping is a partial expression
of that methodology — the language has the discipline, the compiler
has the determinism, the physics has the force fields, but the
*structural connection* between geometric derivation and operational
behavior is broken. Particles experience the Viviani field but aren't
placed by it. They align to it but don't live on it.

Re-integration restores the connection. After the work is done, a
particle's slot, its scheduling, and the field it experiences all
derive from the same geometric primitive. The methodology becomes
visible in the source rather than asserted in commentary. That is
what the project was meant to be.

The work is recoverable. The math is intact. The reference
implementation (sq3core) is correct and verified. What remains is the
wiring.
