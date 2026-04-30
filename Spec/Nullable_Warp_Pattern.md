# Nullable Warp Pattern

## Principle

Every warp slot always computes something useful. Role determines
what "useful" means and where the result goes. No idle threads,
no branches, just data-dependent routing.

> Nullable computation: the result exists for every thread. The mask
> determines which results are non-null. The GPU's predicated execution
> handles the null path at zero cost.

## The Four Roles

| State | Primary work | Secondary work (filler) |
|---|---|---|
| **Active** | Physics integration | Density field update |
| **Crystal** | Signature computation | Grid cell statistics |
| **Coast** | Reduced physics (COUPLING=0) | Census aggregation |
| **Ejected** | Nothing (true null) | Subgrid turbulence stats |

Every state does something. The warp is never partially idle.

## Why Branches Don't Branch

Traditional GPU divergence:
```
if (alive) {
    physics();     // half warp stalls
} else {
    signature();   // other half stalls
}
// Both paths serialize → 2× time
```

Nullable pattern:
```
// Both paths exist in instruction stream
// GPU predicated execution: masked-off lanes retire immediately
// Warp executes at speed of LONGER path (physics)
// Shorter path (signature) finishes early, idles harmlessly
// Total time = max(physics, signature) = physics
// Signature collection is FREE
```

No serialization. The warp always runs at physics speed.
Crystal threads finish their 15-op signature while active threads
are still on op 15 of 300. Then they idle. Same total time.

## Branchless Output Compaction

### Level 1: Atomic (simple, some contention)

```
! Current approach: atomicAdd on SIG_COUNT
SIG_SLOT := SIG_COUNT(1) + 1    ! atomic increment
SIG_OMEGA(SIG_SLOT) := OMEGA_NAT(I)
```

Contention: O(crystals_per_frame) atomic ops on one counter.
At <0.01% crystal rate, contention is negligible.

### Level 2: Warp-level prefix sum (zero contention)

Using SPIRV subgroup ballot + exclusive scan:

```glsl
// Each thread knows its role
uint is_crystal = (role == CRYSTAL) ? 1u : 0u;

// Ballot: bitmask of which lanes are crystals
uvec4 ballot = subgroupBallot(is_crystal);

// Count crystals in this warp
uint warp_crystal_count = subgroupBallotBitCount(ballot);

// One atomic per WARP (not per thread)
uint warp_offset;
if (subgroupElect()) {
    warp_offset = atomicAdd(counter, warp_crystal_count);
}
warp_offset = subgroupBroadcastFirst(warp_offset);

// Each crystal thread gets a unique dense slot
uint my_slot = warp_offset + subgroupBallotExclusiveBitCount(ballot);

if (is_crystal) {
    output[my_slot] = signature;
}
```

Contention: O(warps) atomic ops instead of O(crystals).
At 30M particles / 32 threads per warp = 937K warps. But only
warps with crystals do the atomic. At 0.01% crystal rate, that's
~94 atomics total. Negligible.

### Level 3: Fully branchless (predicated write)

```glsl
// Compute signature unconditionally
vec4 sig = compute_signature(particle_data);

// Write with predication — hardware masks the store
// The store instruction exists but the write mask is zero for non-crystals
crystal_buffer[my_slot] = is_crystal ? sig : crystal_buffer[my_slot];
```

The ternary compiles to a predicated move — no branch, no divergence.
The masked-off store is a no-op at the hardware level.

## SPIRV Requirements

For Level 2 (warp-level prefix sum):

```
OpCapability GroupNonUniform
OpCapability GroupNonUniformBallot
OpCapability GroupNonUniformArithmetic

; Ballot
%ballot = OpGroupNonUniformBallotKHR %v4u32 %subgroup %is_crystal

; Count
%count = OpGroupNonUniformBallotBitCount %u32 %subgroup Reduce %ballot

; Exclusive count (prefix sum)
%prefix = OpGroupNonUniformBallotBitCount %u32 %subgroup ExclusiveScan %ballot

; Broadcast
%offset = OpGroupNonUniformBroadcastFirst %u32 %subgroup %warp_offset
```

These are extensions of the RING_PREV/RING_NEXT subgroup ops already
in the compiler. The capability declarations are already present
(GroupNonUniform + GroupNonUniformShuffle). Adding Ballot + Arithmetic
is straightforward.

## Application to Ergo Particle States

### Crystal lane (implemented)
- Signature collection during physics kernel dead time
- PFLAG_SIGNED prevents double-collection
- ~15 ops, hidden behind ~300 ops of active physics
- Zero register pressure (crystal locals dead before physics locals born)

### Coast lane (future)
- Census statistics: count per GEN bin, aggregate OMEGA
- Warp-level reduction on census counters
- Hidden behind active thread physics

### Ejected lane (future)
- Subgrid density estimation (dead particle's last-known position
  contributes to a low-res density map for background rendering)
- Or true null — ejected particles are gone, their warp time
  is the only genuinely wasted compute

### Nova lane (future)
- Blast radius computation: how many neighbors affected
- Warp-level gather of nearby particle indices
- Hidden behind the blast velocity application

## Determinism Guarantee

The nullable pattern is deterministic because:

1. Each particle's role is determined by FLAGS (set in previous frame)
2. The role determines which computation runs (no random choice)
3. Output slots are determined by prefix sum (not by execution order)
4. Each particle produces at most one output per role transition
5. The PFLAG_SIGNED / PFLAG_BANKED flags prevent repeat computation

Same input → same FLAGS → same roles → same prefix sums → same
output slots → same results. Bitwise reproducible.

## Scaling

At 50M particles with 1% crystal rate:
- 500K crystals × 15 ops = 7.5M ops (signature)
- 49.5M active × 300 ops = 14.85B ops (physics)
- Ratio: 0.05% overhead from signatures
- The physics dominates completely

Even at 10% crystal rate (5M crystals):
- 5M × 15 = 75M ops
- 45M × 300 = 13.5B ops
- Ratio: 0.6% overhead
- Still invisible

The nullable pattern scales linearly with particle count and is
independent of crystal fraction. More crystals = more signatures
collected FOR FREE, not more compute time spent.

## Connection to BLAS / BEPUphysics2

This is the same principle as BEPU's staggered scalar loads:

> "While waiting for lane 3's memory load, process lane 1's math"

In BEPU: the CPU hides memory latency by interleaving work.
In Ergo: the GPU hides divergence by filling dead lanes with work.

Both avoid idle hardware. Both are deterministic. Both scale linearly.
The difference: BEPU does it manually in C# with careful scheduling.
Ergo does it structurally — the particle state determines the work,
the GPU mask determines the routing.
