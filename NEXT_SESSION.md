# Next Session: Zero-Sum Metabolic Exchange on the Ring

## What's Done

Everything up to phase-lock ring coupling is working:

- **RING_PREV / RING_NEXT** — warp shuffle intrinsics, wrapping modular index
- **SORT_BY_GEN** — compiler-generated counting sort (histogram → prefix sum → scatter → pointer swap), runs at census intervals
- **Phase lock** — `OMEGA -= PH_ERR * K_PHASE_LOCK * DT` with signed wrap, normalized to [-1,1]. Running at 30M@60-74fps.
- **Crystal field** — GRID_CRYSTAL permanent density, PFLAG_BANKED, frozen suns contribute to field without per-particle compute.

## The Problem

The original metabolic exchange (commented out) inflated OMEGA because:

```
TRANSFER := MIN(ABS(DEFICIT), ABS(Z_C) * DT)
IF OMEGA_NEXT > OMEGA THEN
  OMEGA := OMEGA + TRANSFER   ← receiver gains
ELSE
  OMEGA := OMEGA - TRANSFER   ← but donor doesn't lose (different thread!)
ENDIF
```

Each thread independently decides to gain or lose based on its neighbor's value,
but the neighbor is a separate thread making its own independent decision. There's
no coordination — both threads can simultaneously decide to gain from each other.
With the [0, OMEGA_MAX] clamp, losses are bounded but gains accumulate. Net result:
global OMEGA inflation → everything turns yellow.

## The Fix: Zero-Sum Warp Exchange

Metabolic energy must be **conserved** within the ring. If thread A gains X from
thread B, thread B must lose exactly X. This requires coordination between threads.

### Approach: Shuffle-Based Half-Exchange

Each thread computes a **signed transfer** with its RING_NEXT neighbor. The transfer
is positive if energy flows forward (GEN → GEN+1) and negative if backward.
Both threads see the same transfer value (one via direct compute, one via shuffle),
so the exchange is automatically zero-sum.

```
! Each thread computes: how much should flow from ME to my NEXT neighbor?
OMEGA_NEXT := RING_NEXT(OMEGA)

! Diffusion: energy flows from high to low, gated by FLOW_W direction
DIFF := (OMEGA - OMEGA_NEXT) * 0.5    ! signed: positive = I have more
FLOW_DIR := FLOW_WG                    ! FLOW_W sign determines allowed direction

! Gate: only allow flow in the FLOW_W direction
IF FLOW_DIR > 0.0 THEN
  ! Forward flow allowed: clamp to non-negative (I can only send forward)
  TRANSFER := MAX(DIFF, 0.0) * ABS(Z_C) * DT
ELSE
  ! Backward flow allowed: clamp to non-positive (I can only send backward)
  TRANSFER := MIN(DIFF, 0.0) * ABS(Z_C) * DT
ENDIF

! Cap transfer to prevent over-drain
TRANSFER := MAX(TRANSFER, -OMEGA * 0.5)
TRANSFER := MIN(TRANSFER, OMEGA * 0.5)

! I lose TRANSFER (positive = I'm sending forward)
OMEGA := OMEGA - TRANSFER

! My PREV neighbor's TRANSFER is what flows TO me
! (their "forward send" is my "receive from behind")
TRANSFER_FROM_PREV := RING_PREV(TRANSFER)
OMEGA := OMEGA + TRANSFER_FROM_PREV
```

Why this is zero-sum:
- Thread I sends TRANSFER to thread I+1
- Thread I+1 receives that same TRANSFER via RING_PREV
- Thread I loses exactly what thread I+1 gains
- No independent decisions — the transfer value is computed once and shuffled

### Data Flow

```
Thread:    [0]  [1]  [2]  ... [31]
           ↓    ↓    ↓        ↓
Compute:   T₀   T₁   T₂       T₃₁    (each computes its forward transfer)
           ↓    ↓    ↓        ↓
Send:      -T₀  -T₁  -T₂      -T₃₁   (lose what you send)
Receive:   +T₃₁ +T₀  +T₁      +T₃₀   (gain what PREV sent, via shuffle)
           ↓    ↓    ↓        ↓
Net:       T₃₁-T₀  T₀-T₁  T₁-T₂  T₃₀-T₃₁   (sum = 0, conservation holds)
```

### Shuffle Count

3 shuffles per frame per particle:
- RING_NEXT(OMEGA) — read neighbor's omega for diffusion
- RING_PREV(TRANSFER) — receive incoming transfer from behind
- RING_NEXT(PH) — phase lock (already working)

All register-to-register. Zero memory traffic.

## Implementation

### fluid_subs.mcl changes

Replace the commented-out metabolic exchange in section 15.5 with the
zero-sum formulation above. Keep the existing phase lock. New variables:

```
REAL :: DIFF, FLOW_DIR, TRANSFER, TRANSFER_FROM_PREV
```

Add to the declarations at the top of SIM_PHYSICS_STEP (line ~179).

### Constants

May want a new constant for exchange rate damping:

```
PARAMETER REAL :: OMEGA_EXCHANGE_RATE = 0.5   ! fraction of diffusion applied per DT
```

Start at 0.5, tune empirically. The Z_COUPLING already gates per-segment
strength, this is a global damping on top.

### Verification

1. **Conservation test**: Sum OMEGA across all particles before and after
   a frame. Should be equal (minus OMEGA_DECAY losses, which are separate).
   Can do this in census.

2. **Visual test**: Should NOT turn yellow. Energy flows along the ring
   directionally (FLOW_W gated), not uniformly.

3. **Ring structure**: With sort active, energy should visibly flow along
   Viviani ring segments — particles in FLOW mode push energy forward,
   COAST particles receive but don't transmit.

### What to watch for

- **Numerical drift**: Floating point means the exchange isn't perfectly
  zero-sum. The clamp at [0, OMEGA_MAX] catches drift, but if the per-frame
  error is systematic, it could still accumulate. Monitor via census.

- **Over-damping**: If OMEGA_EXCHANGE_RATE × Z_C × DT > 0.5, the exchange
  overshoots and oscillates. Keep the product well under 1.

- **Dead threads**: Crystallized particles (PFLAG_CRYSTAL) CYCLE before
  section 15.5. Their lanes in the warp have stale OMEGA values from before
  crystallization. The shuffle reads stale data — but since the crystal
  particle itself doesn't write back, this only affects its live neighbors.
  The live neighbor receives stale OMEGA from the crystal slot, which is
  bounded and finite. Acceptable — the crystal's field influence is in
  GRID_CRYSTAL, not in the ring exchange.

## Current Performance

- Headless: 141 fps at 29M (7.1ms/frame)
- Render with sort + phase lock: 60-74 fps at 30M
- RTX 2060, f32, DEVICE_LOCAL buffers

Expected impact: 1 additional shuffle (RING_PREV on TRANSFER) + ~10 ALU ops.
Negligible — shuffles are register-to-register, ALU is hidden by memory latency.

## Build

```bash
./structured/build.sh
# Strip VERIFY for no-oracle, remove SORT_BY_GEN if sort still broken:
sed '/VERIFY/,/4250/d' galaxy_structured.mcl > /tmp/nonet.mcl
python -m mcl --target spirv --precision f32 --no-split --render -N 29000000 -M 30000000 -o galaxy_render /tmp/nonet.mcl

# Headless benchmark:
sed '/VERIFY/,/4250/d' galaxy_structured.mcl | sed 's/DEFAULT_FRAMES = 2147483647/DEFAULT_FRAMES = 5000/' > /tmp/bench.mcl
python -m mcl --target spirv --precision f32 --no-split -N 29000000 -M 30000000 -o galaxy_gpu /tmp/bench.mcl
ERGO_PROFILE=1 timeout 120 ./galaxy_gpu
```

## Key Files

```
structured/
  constants.mcl       — K_PHASE_LOCK, OMEGA_EXCHANGE_RATE (new)
  fluid_subs.mcl      — Section 15.5: phase lock + metabolic exchange (modify)
  main.mcl            — SORT_BY_GEN at census intervals

mcl/
  backends/spirv.py   — Sort kernel atomics (fixed), shuffle emission
  ir_codegen.py       — Sort dispatch with barriers, MAXPART-sized buffers
```
