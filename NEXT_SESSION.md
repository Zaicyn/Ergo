# Next Session: Crystal Lane Signature Collection

## The Insight

The physics kernel CYCLEs past crystallized particles at the top of the
loop (line ~186). Those threads sit idle waiting for warp sync — wasted
execution slots. But the thread already loaded FLAGS and knows its
particle index. Use that dead time to collect resonance signatures.

This is free compute. The warp is in flight, the active threads are
doing 5.9ms of physics. Crystal threads would otherwise idle for all
of it. Every crystal in the warp = one signature collection slot.
No branching at the end — if there are zero crystals in the warp,
the signature code simply doesn't exist (the IF block is never entered).

## Current Physics Kernel Flow

```
DO I = 1, NPART
  ! Skip crystal/ejected (line ~186)
  IF IAND(FLAGS(I), IOR(PFLAG_CRYSTAL, PFLAG_EJECTED)) ≠ 0 THEN
    CYCLE    ← dead time starts here, thread idles until warp sync
  ENDIF

  ! ... 5.9ms of physics for active threads ...
ENDDO
```

## New Flow

```
DO I = 1, NPART
  IF IAND(FLAGS(I), IOR(PFLAG_CRYSTAL, PFLAG_EJECTED)) ≠ 0 THEN

    ! ── Crystal lane: collect signature while warp works ──
    ! Only collect if not already signed (PFLAG_BANKED handles this)
    ! and buffer has room
    IF IAND(FLAGS(I), PFLAG_CRYSTAL) ≠ 0 THEN
      IF IAND(FLAGS(I), PFLAG_SIGNED) = 0 THEN
        SIG_SLOT := SIG_COUNT(1) + 1
        IF SIG_SLOT ≤ SIG_MAX THEN
          SIG_COUNT(1) := SIG_SLOT

          ! Compute signature from already-loaded particle state
          GEN := IAND(ISHFT(FLAGS(I), -GEN_SHIFT), GEN_MASK) + 1
          CI := CLAMP(INT(POS_X(I) / CELL_SIZE) + GRID_HALF, 1, GRID_SIZE)
          CJ := CLAMP(INT(POS_Y(I) / CELL_SIZE) + GRID_HALF, 1, GRID_SIZE)
          CK := CLAMP(INT(POS_Z(I) / CELL_SIZE) + GRID_HALF, 1, GRID_SIZE)

          SIG_OMEGA(SIG_SLOT) := OMEGA_NAT(I)
          SIG_RHO(SIG_SLOT) := REAL(GRID_DENSITY(CI, CJ, CK)) / 32.0
          SIG_FMODE(SIG_SLOT) := REAL(FLOW_MODE(GEN))
          SIG_VMAG(SIG_SLOT) := SQRT(VEL_X(I)*VEL_X(I) + VEL_Y(I)*VEL_Y(I) + VEL_Z(I)*VEL_Z(I))
          SIG_RNORM(SIG_SLOT) := SQRT(POS_X(I)*POS_X(I) + POS_Y(I)*POS_Y(I) + POS_Z(I)*POS_Z(I)) / DISK_OUTER_R
          SIG_MGATE(SIG_SLOT) := GRID_MET_GATE(CI, CJ, CK)
          SIG_ZC(SIG_SLOT) := ABS(Z_COUPLING(GEN))
          SIG_FW(SIG_SLOT) := ABS(FLOW_W(GEN))

          FLAGS(I) := IOR(FLAGS(I), PFLAG_SIGNED)
        ENDIF
      ENDIF
    ENDIF

    CYCLE
  ENDIF

  ! ... physics for active threads (unchanged) ...
ENDDO
```

## Why This Is Free

1. The warp is already in flight — active threads do 5.9ms of physics
2. Crystal threads idle during that entire time (just CYCLE + wait)
3. The signature work (~15 ops: 3 grid lookups, 1 sqrt, 8 stores)
   is a fraction of the physics work (~300 ops per active thread)
4. Crystal threads finish their signature work long before active
   threads finish physics — then idle as before
5. No new warp launches, no new register pressure on active threads
6. The IF block doesn't exist for warps with zero crystals — the
   branch is never taken, zero cost

## What Changes

### constants.ergo
Add a new flag bit:
```
PARAMETER INTEGER :: PFLAG_SIGNED = 64   ! bit 6: signature collected
```

### fluid_subs.ergo
Move signature collection from scatter into the physics kernel's
crystal CYCLE block. The code goes BETWEEN the crystal/ejected check
and the CYCLE statement. No changes to the active physics path.

### waveguide_subs.ergo (scatter)
REMOVE the signature collection from scatter. It no longer happens
there. The crystal banking (GRID_CRYSTAL + GRID_MATERIAL) stays in
scatter — only the SIG_* writes move to physics.

### fluid_state.ergo
SIG_* arrays stay as-is. SIG_COUNT(1) is still the atomic counter.

### census.ergo
No changes. Census reads SIG_* arrays the same way.

## What Stays The Same

- Active thread physics — zero changes, zero register pressure added
- Scatter kernel — loses the SIG_* writes (fewer bindings, potentially faster)
- Stencil kernel — unchanged
- Census — unchanged
- SIG_* buffer layout — unchanged
- Clustering tool — unchanged

## Register Pressure Analysis

The crystal lane code adds ~10 locals (GEN, CI, CJ, CK, SIG_SLOT,
plus the computed values). But these only exist in the crystal branch
which CYCLEs before reaching the physics code. The SPIRV compiler
sees that the crystal locals and physics locals are never live
simultaneously — their registers don't compete.

In practice, the crystal branch may share registers with the early
physics setup (lines 190-208: PX, PY, PZ, VX, VY, VZ load) since
those are also needed for the signature. But the crystal branch
exits before the heavy physics starts (envelope, steering, channels),
so peak register usage shouldn't increase.

Verify with: compare k2 (physics) time before and after. If it
increases >5%, the register allocator is not separating the branches
properly and we need to reconsider.

## Deterministic Behavior

Each crystal particle gets signed exactly once:
- PFLAG_CRYSTAL is set in physics section 17 (threshold observation)
- Next frame, physics kernel checks crystal flag → enters crystal lane
- Signature is collected, PFLAG_SIGNED is set
- Subsequent frames: PFLAG_SIGNED is set → skip signature → CYCLE
- No race conditions: each particle is processed by exactly one thread

The SIG_COUNT atomic increment is the only contention point, same as
before. At typical crystal rates (<0.01% of particles per frame),
contention is negligible.

## Build & Test

```bash
bash structured/build.sh
python -m mcl --target spirv --precision f32 --no-split -N 5000000 -M 5000000 -o galaxy_gpu galaxy_structured.ergo
ERGO_PROFILE=1 timeout 30 ./galaxy_gpu  # compare k2 time to baseline

# Signature collection (need raised threshold to see crystals):
sed 's/DEFAULT_FRAMES = 2147483647/DEFAULT_FRAMES = 500000/; s/OMEGA_CRYSTAL_THRESH = 0.008/OMEGA_CRYSTAL_THRESH = 0.048/' galaxy_structured.ergo > /tmp/sig_run.ergo
python -m mcl --target spirv --precision f32 --no-split -N 5000000 -M 5000000 -o /tmp/sig_gpu /tmp/sig_run.ergo
/tmp/sig_gpu > /tmp/sig_output.txt 2>&1
python tools/cluster_signatures.py /tmp/sig_output.txt --clusters 6
```

## Key Files

```
structured/
  constants.ergo       — PFLAG_SIGNED (new, bit 6)
  fluid_subs.ergo      — Crystal lane signature collection (new)
  waveguide_subs.ergo  — Remove SIG_* from scatter (cleanup)
```
