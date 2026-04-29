# Ergo Threshold Tuning Guide

## Principle

Observe first, then adjust one constant at a time. Never tune two
simultaneously — you can't tell which one caused the change.

## Current Constants (starting values)

| Constant | Value | Location | Purpose |
|---|---|---|---|
| K_PHASE_LOCK | 0.001 | constants.ergo:70 | Phase restoring strength between ring neighbors |
| OMEGA_EXCHANGE_RATE | 0.5 | constants.ergo:71 | Fraction of metabolic diffusion applied per DT |
| OMEGA_CRITICAL | 0.04 | constants.ergo:72 | Mean warp OMEGA below which ring spills |
| SPILL_DECAY | 0.5 | constants.ergo:73 | OMEGA multiplier on spillover (0.5 = halve) |
| K_WINDING | 0.0001 | constants.ergo:74 | Winding number Q correction strength |
| OMEGA_CRYSTAL_THRESH | 0.008 | constants.ergo:40 | Individual particle crystallization threshold |
| OMEGA_BASE | 0.08 | constants.ergo:34 | Background metabolic rate (always present) |
| OMEGA_DECAY | 0.15 | constants.ergo:37 | Per-frame omega decay rate |
| OMEGA_NOVA_THRESH | 0.65 | constants.ergo:39 | Supernova trigger threshold |

## Tuning Order

Tune in this order. Each step depends on the previous being stable.

### Phase 0: Instrument Census

Before touching any constant, add warp-level statistics to census.
Currently census only prints NPART and FRAME.

**Add to census.ergo or a new census_ring.ergo:**

```
! Per-frame counters (updated in physics kernel, read at census)
STATIC INTEGER :: CRYSTAL_COUNT = 0
STATIC INTEGER :: SPILLOVER_COUNT = 0
STATIC REAL :: OMEGA_WARP_MIN = 999.0
STATIC REAL :: OMEGA_WARP_MAX = 0.0
STATIC REAL :: WINDING_ERR_MAX = 0.0
```

At census intervals, print:
```
PRINT CRYSTAL_COUNT
PRINT SPILLOVER_COUNT
PRINT OMEGA_WARP_MIN       ! lowest warp mean OMEGA in system
PRINT OMEGA_WARP_MAX       ! highest warp mean OMEGA
PRINT WINDING_ERR_MAX      ! largest |Q - 1| error across warps
```

Reset counters after printing.

**What to look for:**
- OMEGA_WARP_MIN tells you the natural floor of healthy rings
- OMEGA_WARP_MAX tells you the ceiling (should be near OMEGA_MAX=2.0 for active rings)
- WINDING_ERR_MAX tells you how well phase lock is holding Q near 1
- CRYSTAL_COUNT growth rate tells you how fast particles are dying
- SPILLOVER_COUNT tells you how often rings break (should be rare events, not constant)

---

### Phase 1: Baseline (no ring coupling)

**Config:** Disable sections 15.5-15.8 entirely. Run pure spatial physics.

**Run:** 10,000+ frames at 29M particles.

**Record:**
- [ ] OMEGA distribution: what range do particles naturally occupy?
- [ ] Crystal rate: how many crystallize per 1000 frames?
- [ ] Visual: does the galaxy form recognizable structure?

**Expected:** OMEGA settles between OMEGA_BASE (0.08) and ~0.4 for most
particles. COAST particles decay toward crystallization. Active particles
maintain higher OMEGA from density coupling.

**This is the reference.** All tuning compares against this baseline.

---

### Phase 2: Phase Lock Only (K_PHASE_LOCK)

**Config:** Enable section 15.5 only. Sort active. No metabolic exchange,
no winding correction, no spillover.

**Tuning target:** Q should drift toward 1 for complete rings but not
be artificially clamped. WINDING_ERR_MAX should be small but nonzero.

| Symptom | Meaning | Action |
|---|---|---|
| Q stays exactly 1.000 | Over-clamped | Reduce K_PHASE_LOCK |
| Q wanders (0.5-1.5) | Under-clamped | Increase K_PHASE_LOCK |
| OMEGA distribution narrows | Phase lock is draining energy | Reduce K_PHASE_LOCK |
| OMEGA distribution unchanged from baseline | Phase lock has no effect | Increase K_PHASE_LOCK |
| Everything turns yellow | OMEGA inflating | K_PHASE_LOCK too high, PH_ERR is biased |

**Search range:** 0.0001 → 0.01, multiply by 3 each step.

**Record:**
- [ ] K_PHASE_LOCK value that gives Q ∈ [0.95, 1.05] for healthy rings
- [ ] OMEGA distribution with phase lock vs baseline — should be similar
- [ ] Visual: any color shift? Should look like baseline.

---

### Phase 3: Metabolic Exchange (OMEGA_EXCHANGE_RATE)

**Config:** Enable sections 15.5 + 15.6. Sort active.

**Tuning target:** OMEGA should flow directionally along the ring (FLOW_W
gated), not inflate uniformly. Total OMEGA should be approximately
conserved (minus OMEGA_DECAY losses).

| Symptom | Meaning | Action |
|---|---|---|
| Everything turns yellow/green | OMEGA inflating | Reduce OMEGA_EXCHANGE_RATE |
| No visible change from Phase 2 | Exchange too weak | Increase OMEGA_EXCHANGE_RATE |
| OMEGA_WARP_MIN drops fast | Exchange is draining weak rings | Reduce OMEGA_EXCHANGE_RATE |
| Ring structure visible in color | Working correctly | Lock this value |
| COAST particles gain OMEGA | Exchange leaking to non-coupled | Check FLOW_W gating at poles |

**Search range:** 0.1 → 1.0, step by 0.2.

**Conservation check:** Sum OMEGA before and after 1000 frames.
Difference should be explainable entirely by OMEGA_DECAY. If the
sum grows, the zero-sum exchange has a leak.

**Record:**
- [ ] OMEGA_EXCHANGE_RATE value where exchange is visible but not inflationary
- [ ] Total OMEGA conservation error per 1000 frames
- [ ] Visual: directional energy flow along ring segments

---

### Phase 4: Winding Correction (K_WINDING)

**Config:** Enable sections 15.5 + 15.6 + 15.7. Sort active.

**Tuning target:** Q stays very close to 1 for complete rings (MET_GATE=8).
The correction should be barely perceptible — local phase lock does the
heavy lifting, winding correction just prevents drift.

| Symptom | Meaning | Action |
|---|---|---|
| WINDING_ERR_MAX stays near 0 | Correction working | Good |
| WINDING_ERR_MAX grows over time | Correction too weak | Increase K_WINDING |
| OMEGA oscillates per frame | Correction too strong | Reduce K_WINDING |
| Only some rings maintain Q=1 | Expected — incomplete rings don't get correction | Correct behavior |

**Search range:** 0.00001 → 0.001, multiply by 3 each step.

**Record:**
- [ ] K_WINDING value where WINDING_ERR_MAX < 100 after 10,000 frames
- [ ] No visible oscillation or jitter in particle motion

---

### Phase 5: Spillover (OMEGA_CRITICAL + SPILL_DECAY)

**Config:** Enable all sections 15.5-15.8. Sort active. Full system.

**Pre-step:** From Phase 3 data, note OMEGA_WARP_MIN for healthy rings.
Call this OMEGA_FLOOR.

**Set initial OMEGA_CRITICAL:**
- Start at OMEGA_FLOOR × 0.5 (generous — only truly dying rings spill)

**Tuning target:** Dying rings spill and dissolve. Healthy rings never
trigger spillover. Spillover events should be rare (few per 1000 frames),
not constant.

| Symptom | Meaning | Action |
|---|---|---|
| No spillover events ever | Threshold too low | Raise OMEGA_CRITICAL |
| Healthy rings spilling | Threshold too high | Lower OMEGA_CRITICAL |
| Rings dissolve in ~100 frames after spill | SPILL_DECAY correct | Good |
| Rings dissolve instantly | SPILL_DECAY too aggressive | Raise toward 0.8 |
| Spilled particles linger for 1000+ frames | SPILL_DECAY too gentle | Lower toward 0.3 |
| Burst of crystals after spillover | Expected — ring dissolution | Correct behavior |

**OMEGA_CRITICAL search:** Binary search between OMEGA_FLOOR × 0.3 and
OMEGA_FLOOR × 0.9.

**SPILL_DECAY search:** 0.3 → 0.9, step by 0.1. This is mostly visual —
how fast do you want dying rings to fade?

**Record:**
- [ ] OMEGA_CRITICAL value where spillover is rare but real
- [ ] SPILL_DECAY value that gives visible dissolution over ~200-500 frames
- [ ] Crystal count growth: should show bursts (ring deaths) not steady trickle
- [ ] Visual: rings fade from green/yellow → blue → crystallize after spill

---

## Final Validation

After all phases complete, run the full system for 50,000+ frames and check:

- [ ] OMEGA distribution is stable (not drifting up or down over time)
- [ ] Q ≈ 1 for complete rings, undefined for partial rings
- [ ] Crystal count grows in bursts (ring spillovers), not linearly
- [ ] GRID_CRYSTAL accumulates — frozen suns visibly affect live particles
- [ ] No yellow sponge (OMEGA inflation)
- [ ] No immediate mass crystallization (OMEGA deflation)
- [ ] Galaxy structure is recognizable and dynamic
- [ ] FPS stable at 60-74 rendered, 130+ headless

## Pitfall: Register Pressure

GPU performance can drop suddenly and seemingly at random when kernel
register usage crosses a hardware threshold. The SM has a fixed register
file (65,536 on Turing). More registers per thread = fewer resident
warps = less latency hiding = slower execution.

**Why it looks random:** Adding one local variable to the physics kernel
can push register count from 32 to 33, dropping max occupancy from 100%
to 67%. The code change is trivial but the performance impact is 1.5x.
This looks like "the GPU just got slower" with no obvious cause.

**How to detect:**

```bash
# Profile with nsys — look for "stall: not selected" or low occupancy
nsys profile --trace=vulkan ./galaxy_render

# Or use ERGO_PROFILE=1 and compare k2 (physics) time before/after
# any code change. If k2 jumps by >20% without algorithmic change,
# register pressure is the likely cause.
```

**Symptoms:**
- Physics kernel time (k2) increases >20% after adding a variable
- No change in particle count or algorithm
- Reverting the variable addition restores performance
- Performance is fine at small N but degrades at large N (more warps
  competing for the same register file)

**The fix:** Split the kernel into two passes with fewer live variables
each. The natural split point is between spatial physics (gravity,
envelope, steering) and ring topology (coupling, winding, spillover).
Each half uses ~24-28 registers instead of ~48-62 combined.

**Cost of splitting:** One extra compute barrier between passes (~0.01ms)
plus any variables that are live across the split become intermediate
buffer arrays. The --promote-locals compiler flag handles this.

**Rule of thumb:**
- ≤32 regs/thread: full speed, don't worry
- 33-48 regs/thread: acceptable, monitor occupancy
- 49-64 regs/thread: consider splitting
- >64 regs/thread: split immediately, spills are killing you

**Current physics kernel:** ~102 inlined locals, estimated 48-62
registers after SSA optimization. In the warning zone. If fps drops
unexpectedly after adding ring coupling features, register pressure
is the first thing to check.

## Measured Register Pressure (2026-04-29, RTX 2060)

Profiled with `ERGO_PROFILE=1`, headless, `--precision f32 --no-split`.

### Baseline — monolithic kernel (102 locals, k2 = physics)

| N | k0 (scatter) | k1 (stencil) | k2 (physics) | Total | FPS |
|---|---|---|---|---|---|
| 1M | 0.046 ms | 0.008 ms | 0.208 ms | 0.262 ms | 3,819 |
| 10M | 0.409 ms | 0.007 ms | 2.047 ms | 2.464 ms | 406 |
| 29M | 1.178 ms | 0.007 ms | 5.900 ms | 7.086 ms | 141 |

Scaling is linear (10x particles → 9.8x k2 time). No super-linear
blowup = no register spilling at current local count. 29M headless
is above the 130 fps target.

### With census scratch arrays (+3 per-particle array writes in kernel)

Added CENSUS_FLAGS, CENSUS_OMEGA_MEAN, CENSUS_WINDING_ERR writes
inside the physics kernel. Extends live ranges for OMEGA_MEAN and
WINDING_ERR. Still 102 declared locals but more simultaneous liveness.

| N | k2 baseline | k2 + census | Delta | % increase |
|---|---|---|---|---|
| 1M | 0.208 ms | 0.278 ms | +0.070 ms | +33.7% |
| 10M | 2.047 ms | 2.550 ms | +0.503 ms | +24.6% |
| 29M | 5.900 ms | 7.404 ms | +1.504 ms | +25.5% |

**Lesson:** 3 extra array writes = 25% regression. Every additional
live variable in the hot kernel costs ~5-8% throughput. Census
observation belongs in a COLD path (separate kernel at census
intervals), not inside the HOT physics kernel.

### Kernel split — Pass 1 (spatial+omega, 78 locals) + Pass 2 (ring, 41 locals)

Split at section 15/15.5 boundary. Pass 1 writes VEL+OMEGA, Pass 2
reads them back. Pass 2 re-reads GRID_DENSITY + GRID_MET_GATE (2
grid reads) for nova/spillover gating. No ENV recomputation.

| N | Baseline (monolithic) | Split (k2+k3) | Delta |
|---|---|---|---|
| 1M | 0.208 ms | 0.387 ms | +86% |
| 10M | 2.047 ms | 3.763 ms | +84% |
| 29M | 5.900 ms | 10.514 ms | +78% |

**Lesson:** Split is SLOWER at current register count. The second
memory pass over 29M particles (re-reading POS/VEL/FLAGS/OMEGA =
~812MB bandwidth) costs more than any occupancy gain from fewer
registers per pass. The monolithic kernel is bandwidth-limited, not
register-limited.

### When to split

The split becomes profitable when register pressure causes occupancy
to drop enough that the bandwidth cost of two passes is less than the
latency-hiding loss from low occupancy. Based on these measurements:

- **At 102 locals (current):** monolithic wins. Don't split.
- **At ~120 locals (+18):** expect ~50% regression from register
  pressure. Split break-even point. Profile before deciding.
- **At ~140+ locals:** split will likely win. The monolithic kernel
  will be spilling to local memory (LMEM), which is slower than
  a second clean pass.

**The split architecture is validated and ready.** Two subroutines
exist: `SIM_PHYSICS_SPATIAL` (sections 1-15, 78 locals) and
`SIM_PHYSICS_RING` (sections 15.5-18, 41 locals). Revert to
monolithic for now; switch when locals exceed ~120.

**Profiling command:**
```bash
bash structured/build.sh
python -m mcl --target spirv --precision f32 --no-split -o galaxy_gpu galaxy_structured.ergo
ERGO_PROFILE=1 ./galaxy_gpu -N 29000000 --frames 500 2>&1 | grep -A10 "GPU profile"
```

## Locked Values

Once tuned, record final values here:

| Constant | Tuned value | Phase | Notes |
|---|---|---|---|
| K_PHASE_LOCK | TBD | 2 | |
| OMEGA_EXCHANGE_RATE | TBD | 3 | |
| K_WINDING | TBD | 4 | |
| OMEGA_CRITICAL | TBD | 5 | |
| SPILL_DECAY | TBD | 5 | |
