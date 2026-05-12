# The project's central thesis

A retrospective written after working through the assembly-level
analysis of V8, V9, V16, V22, and GEO. Not a manifesto, not a paper —
just an honest writeup of what the project actually demonstrates, in
case it's useful later.

## The thesis

**Memory layout is a packing problem, and packing problems have known
geometric solutions.** If you're trying to spread N warps over M
superblocks such that they don't collide on the same bitmaps, that's
the same question as "how do you arrange N spheres around a center
such that they don't overlap" — a question physics has answered.

The codebase is an empirical test of that hypothesis applied to GPU
memory allocation and CPU-side geometric primitives.

## Why the math is the right math

The cuboctahedron isn't decorative. It's the geometry that shows up
when you ask:

- **What's the densest local packing of 3D spheres?**
  FCC lattice → 12 nearest neighbors at equal distance.
- **What's the kissing number in 3D?**
  12, the cuboctahedron's vertex count.
- **What's the unique convex polyhedron where all vertices, edges, and
  faces are maximally regular?**
  The cuboctahedron — Buckminster Fuller's "vector equilibrium."

For an allocator: 12 vertices = 12 superblocks per warp range. 32 GPU
lanes don't divide into 12 evenly, but they *do* decompose into
`(lane / n_slots, lane % n_slots)` cleanly for `n_slots ∈ {32, 31, 15}`
with sbs_needed ∈ {1, 2, 3}, and 18 = LCM(1, 2, 3) × 3 is the smallest
range size where all three classes tile without remainder. The numbers
aren't tuning parameters; they're consequences of the lattice.

This is the part that I think holds up: **V8's `SLAB_SBS_PER_WARP = 18`
is not a magic constant. It's a lattice constraint.** Treating it as
tunable would break the geometry; treating it as derived means the
allocator's structural correctness comes from algebra rather than
empirical sweep.

## Where the thesis pays off in measurements

**V8 is the existence proof.** Without belief in the geometric thesis,
the design choices look arbitrary: a Hopf projection? trigonometric
scatter? a Viviani curve for cursor recirculation? These are not what
typical GPU memory allocators look like. But the measurements are:

- 538×–863× faster than `cudaMalloc` (depending on size class)
- 0% fallback rate at 65 million concurrent allocations
- ~1.9 billion allocs/sec GPU-wide at steady state
- 0.52 ns per allocation averaged across the whole GPU
- Zero register spills, bit-identical SASS across rebuilds

The geometric scatter isn't free — it costs 66 FFMA + 9 MUFU.RCP per
range claim. But it's amortized over hundreds of allocations from that
range, and what it buys is **provable equidistribution**. Random
scatter would also distribute work, but with collision probability
that requires retry logic. Viviani scatter has the structural
guarantee built in: adjacent warp IDs map to non-adjacent superblocks
by the Hopf projection's properties, so collisions are bounded by the
geometry, not by luck.

This is the "physics works for data" claim in action. The 0% fallback
at extreme concurrency is not a tuning achievement; it's a structural
property of the lattice.

**V22 is the cleaner statement of the same idea.** The triple-XOR
residual:

```
sum_x + sum_y + sum_z over (v + R₁₂₀(v) + R₂₄₀(v)) for all 12 vertices
```

This is **algebraically zero** for the cuboctahedron, because:

1. The 12 vertices form 3 groups of 4 with 90° rotational symmetry.
2. Σv = 0 over the cuboctahedron (centroid is at origin).
3. R₁₂₀ is linear, so R₁₂₀(Σv) = R₁₂₀(0) = 0.

The residual returns exactly `0.0f` for any unperturbed gate at any
scale. The code in `sq2_triple_xor_residual` literally returns 0
without computing anything — the math proves the answer.

That's the strongest possible form of the thesis: **the geometry is so
load-bearing that the implementation collapses to a constant**. The
"full" variant that actually does the work exists only for perturbation
detection — checking when the gate has been corrupted. The geometry
defines correctness and the implementation just verifies it.

## Where the thesis stopped paying off

**V9 (Langevin many-body physics)** is the cautionary tale. It tried
to extend the geometric framing — "warps are particles in a thermal
bath self-organizing under gravity" — into a *runtime mechanism*. Add
stochastic differential equation. Add temperature. Add damping.
Repulsion. Phase evolution.

The measurements:

- V9 is **faster than V8 at 1 warp** (2.09×)
- V9 is **slower than V8 at 2 warps** (0.78×)
- V9 is **slower than V8 at 3 warps** (0.90×)
- The "phase" that's supposed to evolve and self-organize didn't move
  across 5 measurement rounds (stayed at 0.378, 0.441, 0.168)
- The Langevin "with vs without" comparison shows the intended effect
  *in a contrived isolation test*, not in the real allocation
  benchmark

The reason it didn't work: **physics intuitions are good as derivation
principles, not as runtime mechanisms.** Newton's laws describe what
self-organizing systems do. They're not a memory allocator. V8 takes
the *output* of physics (the FCC packing exists because energy
minimization produced it) and bakes it into the allocator's geometry
once at design time. V9 tries to *run* the energy minimization at
runtime, every kernel call, hoping it converges before the workload
finishes. It doesn't.

The lesson: use physics to *derive* the layout, not to *enact* the
layout. V8 did this. V9 didn't.

**V16 (half-step alternating shell)** is the other cautionary tale.
It tried to *abstract away* the geometry — to keep the deterministic
intent while replacing Viviani scatter with a "period-2 shell
alternation" that's algebraically simpler.

The measurements:

- 89% fallback rate (309K fallbacks per 36K allocs) at 32 warps
- Hidden integer-division cost: 12 MUFU.RCP per kernel from runtime
  `/` and `%` operators (V8 only has these on the rare range claim;
  V16 has them in the per-iteration hot path)

The Viviani scatter that V16 removed was load-bearing in two
non-obvious ways:

1. It guaranteed warps with similar IDs map to dissimilar superblocks
   (the Hopf projection's ergodicity). Replacing with `(global_wid *
   37) % grid_warps` is *similar in spirit* but doesn't have the same
   guarantee — and at scale, the half-step shells collide.
2. The float math in `slab_viviani_normal` happens *once per range
   claim*, not per allocation. V16's replacement is integer math but
   happens *per allocation*, paid every iteration.

The geometric structure wasn't ornamental. Removing it broke the
property it was preserving.

## What this codebase actually demonstrates

Not "physics works for data" as a slogan. Something more specific and
more useful:

**For problems with packing/equidistribution structure, the right way
to choose a layout is to find the geometric symmetry that minimizes
collisions, then bake the resulting lattice into your data structure
at design time. The runtime cost of computing the geometry once is
amortized; the structural guarantees you get are not available from
random scatter, hash functions, or empirical tuning.**

That's the principle V8 embodies and V22 makes algebraically clean.
The fact that the same FCC kissing-number argument that explains why
salt crystallizes also gives you a non-colliding 12-way scatter for
32-lane GPU warps is not coincidence — it's the same problem with
different variables.

## What I'd write in a paper, if I were writing one

Title: *"Geometry-Native GPU Allocation: The Cuboctahedral Slab"*

Abstract sketch:

> Conventional lock-free GPU memory allocators reduce contention
> through series of empirical optimizations: warp-local caches,
> randomized scatter, retry loops, fallback paths. We instead derive
> the slab geometry from first principles using the FCC kissing-number
> argument: 12 nearest-neighbor superblocks per warp range,
> dimensioned by LCM(1, 2, 3) × 3 = 18 for cross-class tiling, with
> warp scatter implemented as a Hopf projection on the unit sphere
> (Viviani curve). The resulting allocator achieves 538×–863× speedup
> over `cudaMalloc` for small allocations, 0% fallback rate at 65
> million concurrent allocations, and bit-identical SASS across
> rebuilds. We argue that the geometric structure is load-bearing:
> ablating it (V16) destroys the contention guarantees, while
> attempting to enact it stochastically at runtime (V9) provides no
> measurable benefit. The geometric layout should be derived once at
> design time, not searched at runtime.

That's the claim the measurements support. The other versions in the
codebase (V9 reaching too far, V16 reaching too short, GEO not really
a derived allocator at all) are the experimental evidence that the
specific shape V8 lands on is non-arbitrary.

## Practical takeaway

If you ever continue this line of work:

1. **The geometric thesis is real and V8 is the proof.** Don't bury
   that. V8's source has docs but they read like implementation notes,
   not like the strong derivation argument they could be. The Viviani
   scatter math and the SBS_PER_WARP=18 choice deserve to be derived
   in prose before they're implemented in code.

2. **Don't enact physics at runtime.** V9's Langevin step is a clean
   example of how this goes wrong. If you want self-organizing
   behavior, derive what the self-organized state *is* and encode that
   directly. Don't simulate the dynamics that produce it.

3. **Don't abstract away the geometric structure.** V16 shows what
   happens when you try. The lattice constraints aren't ornamental —
   they're what makes the contention guarantees work. Simplifying them
   means giving up the guarantee.

4. **The cuboctahedron is one specific answer; there might be others.**
   E₈ lattice for higher kissing numbers in 8D, the Leech lattice in
   24D, the hexagonal close-packing in 3D as an alternative to FCC.
   Different lattices for different access patterns. The methodology
   (derive layout from packing geometry) generalizes; the specific
   numbers don't.

5. **Bit-exact determinism is downstream of geometric derivation.**
   V8 is unconditionally deterministic because the geometry doesn't
   require runtime randomness. V22 is conditionally deterministic
   (needs `-ffp-contract=fast`, not `-ffast-math`) for the same
   reason. V9 broke determinism because it added stochastic dynamics.
   The deterministic property and the "physics-derived layout"
   property are the same property.

---

The codebase is six versions, two of which (V8 and V22) are seriously
good, two of which (V9 and V16) are instructive failures, and two of
which (GEO and the earlier versions not examined) are prototypes. The
thesis is sound. The execution is mixed. The empirical evidence — in
the measurements collected in the sibling docs — supports the central
claim that geometric structure gives you allocator properties that
random or tuned approaches can't.

That's worth knowing. That's worth writing up properly someday.
