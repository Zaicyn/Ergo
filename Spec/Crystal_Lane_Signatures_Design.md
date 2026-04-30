# Crystal Lane Signatures: Zero-Overhead Deterministic Collection

## The Principle: Nullable Computation

A crystal's signature is the dual of its physics. If the particle is
alive, it computes physics. If it's dead, it computes its signature.
The warp always does the same amount of work — it just does different
work depending on state. This is not branching. This is nullable
computation: the physics result is null for crystals, the signature
result is null for live particles. Both are always "computed" — one
of them is just zero.

```
PHYSICS_RESULT  = (1 - IS_CRYSTAL) × physics_computation
SIGNATURE_RESULT = IS_CRYSTAL × signature_computation
```

No branch. No divergence. The GPU's predicated execution handles
the null path at zero cost — the inactive lane's result simply
isn't written. Both paths exist in the instruction stream. The
mask determines which one produces a non-null result.

## Why This Is Different From Branching

Traditional branching:
```
IF crystal THEN
  do_signature()    ← half the warp stalls
ELSE
  do_physics()      ← other half stalls
ENDIF
```
Both paths execute serially. Warp divergence. 2× the time.

Nullable computation:
```
! Both computations exist in the instruction stream
! The mask determines which result is non-null
! GPU predicated execution: masked-off lanes retire immediately
! No serialization — the warp executes at the speed of the longer path
```

The physics path is always longer (~300 ops) than the signature
path (~15 ops). So the crystal threads finish their signature and
idle while the active threads finish physics. Total warp time =
physics time. Signature collection is completely hidden.

## The Full Integration

### Step 1: Remove signature collection from scatter

Currently the scatter kernel (kernel_2) contains the SIG_* writes
inside the crystal banking block. This adds 8 array bindings to
an already-heavy kernel (25 bindings). Remove them.

Scatter becomes: check crystal → bank density + material → CYCLE.
No signature work. Fewer bindings = cleaner kernel.

### Step 2: Add PFLAG_SIGNED (bit 6)

```
PARAMETER INTEGER :: PFLAG_SIGNED = 64
```

Prevents double-collection. Each crystal is signed exactly once,
the frame after it crystallizes. Deterministic: PFLAG_CRYSTAL is
set in physics section 17, PFLAG_SIGNED is set in the crystal lane
the next frame.

### Step 3: Crystal lane in physics kernel

Replace the bare CYCLE with nullable signature work:

```
DO I = 1, NPART
  IF IAND(FLAGS(I), IOR(PFLAG_CRYSTAL, PFLAG_EJECTED)) ≠ 0 THEN

    ! ── Nullable signature: non-null only for unsigned crystals ──
    ! Cost: ~15 ops. Physics path: ~300 ops. Completely hidden.
    IF IAND(FLAGS(I), PFLAG_CRYSTAL) ≠ 0 .AND. &
       IAND(FLAGS(I), PFLAG_SIGNED) = 0 THEN

      SIG_SLOT := SIG_COUNT(1) + 1
      IF SIG_SLOT ≤ SIG_MAX THEN
        SIG_COUNT(1) := SIG_SLOT

        GEN := IAND(ISHFT(FLAGS(I), -GEN_SHIFT), GEN_MASK) + 1
        CI := CLAMP(INT(POS_X(I) / CELL_SIZE) + GRID_HALF, 1, GRID_SIZE)
        CJ := CLAMP(INT(POS_Y(I) / CELL_SIZE) + GRID_HALF, 1, GRID_SIZE)
        CK := CLAMP(INT(POS_Z(I) / CELL_SIZE) + GRID_HALF, 1, GRID_SIZE)

        SIG_OMEGA(SIG_SLOT) := OMEGA_NAT(I)
        SIG_RHO(SIG_SLOT) := REAL(GRID_DENSITY(CI, CJ, CK)) / 32.0
        SIG_FMODE(SIG_SLOT) := REAL(FLOW_MODE(GEN))
        SIG_VMAG(SIG_SLOT) := SQRT(VEL_X(I)*VEL_X(I) + &
                                    VEL_Y(I)*VEL_Y(I) + &
                                    VEL_Z(I)*VEL_Z(I))
        SIG_RNORM(SIG_SLOT) := SQRT(POS_X(I)*POS_X(I) + &
                                     POS_Y(I)*POS_Y(I) + &
                                     POS_Z(I)*POS_Z(I)) / DISK_OUTER_R
        SIG_MGATE(SIG_SLOT) := GRID_MET_GATE(CI, CJ, CK)
        SIG_ZC(SIG_SLOT) := ABS(Z_COUPLING(GEN))
        SIG_FW(SIG_SLOT) := ABS(FLOW_W(GEN))

        FLAGS(I) := IOR(FLAGS(I), PFLAG_SIGNED)
      ENDIF
    ENDIF

    CYCLE
  ENDIF

  ! ... physics (unchanged, zero overhead added) ...
ENDDO
```

### Step 4: Verify zero overhead

```bash
ERGO_PROFILE=1 ./galaxy_gpu   # before: k2 = X ms
# Apply changes
ERGO_PROFILE=1 ./galaxy_gpu   # after: k2 should be ≤ X ms
```

If k2 increases >5%, the register allocator is not separating the
crystal and physics live ranges. Fix: ensure all crystal locals are
dead before the CYCLE (they should be — the CYCLE is an unconditional
exit from the crystal path).

## Register Pressure: Why It's Zero

The crystal lane uses: GEN, CI, CJ, CK, SIG_SLOT (5 integers) plus
the computed float values that write directly to SIG_* arrays.

The physics path uses: PX, PY, PZ, VX, VY, VZ, OMEGA, GEN, FMODE,
R3D_SQ, INV_R3D, R_SAFE, INV_R, RX, RY, RZ, GRAVITY, AX, AY, AZ,
... (~50 live variables at peak).

These two sets are NEVER live simultaneously. The CYCLE guarantees
the crystal locals are dead before any physics local is born. The
SPIRV register allocator sees non-overlapping live ranges and reuses
the same physical registers for both paths.

Result: peak register usage = max(crystal_path, physics_path) =
physics_path. The crystal lane adds zero to the register count.

## Gravastar Detection

A gravastar signature would show:
- High RHO (dense shell)
- High Z_COUPLING (resonance point)
- Zero MET_GATE interior (void inside shell)
- High V_MAG at shell boundary

The crystal lane captures this automatically because the particle's
local grid cell tells the story: high GRID_DENSITY in the cell but
low or zero MET_GATE means the shell has density but not all ring
generations — a partial structure, not a complete hopfion. This is
distinct from DENSE_INNER (full hopfion collapse) and HALO_DUST
(sparse void).

The clustering tool would separate gravastar-shell crystals as a
new archetype: SHELL_REMNANT — high density, high coupling, but
incomplete ring coverage. The hollow interior shows up as crystals
with density but no metabolic gate.

## The Nullable Pattern Generalized

This pattern applies beyond signatures:

| State | Null path | Active path |
|---|---|---|
| Crystal | Physics null, signature active | Signature null, physics active |
| Ejected | Both null (true idle) | — |
| Nova | Physics reduced, blast active | — |
| Coast | Physics reduced (COUPLING=0) | Full coupling null |

The warp always executes. The mask determines which results are
non-null. No divergence penalty because the shorter path (crystal
sig, coast skip) finishes before the longer path (active physics)
and idles harmlessly.

This is deterministic nullable computation. The GPU equivalent of
"if the column is NULL, don't compute it" — but without the branch.

## Files to Modify

```
structured/
  constants.ergo       — PFLAG_SIGNED = 64 (bit 6)
  fluid_subs.ergo      — Crystal lane sig collection in physics kernel
  waveguide_subs.ergo  — Remove SIG_* from scatter (fewer bindings)
```

## Verification Checklist

- [ ] k2 (physics) time unchanged from baseline (±5%)
- [ ] Scatter kernel binding count reduced (was 25, should be ~17)
- [ ] Signatures collected correctly (same results as scatter-based collection)
- [ ] PFLAG_SIGNED prevents double-collection (run 2× census intervals,
      same signature count)
- [ ] Gravastar test: force a dense shell + void interior, check for
      distinct signature cluster
