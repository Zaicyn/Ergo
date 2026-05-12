# Coast Lane + Census mRNA — Implementation Brief

## What this is

Move CPU census ([structured/census.ergo](../structured/census.ergo)) onto the
GPU, inside the dead time of coast-state particle lanes. Transport results back
to CPU via a double-buffered ring (mRNA pattern). Net: eliminate the 25ms
periodic CPU pass and the implicit particle-array download.

This is the second instance of the Nullable Warp Pattern
([Spec/Nullable_Warp_Pattern.md](Nullable_Warp_Pattern.md)). Crystal lane was
the first (+3.2% k2, confirmed free). Coast tests whether the pattern
generalizes.

## Three-step path, each step has a measurable outcome

### Step 1: Split coast off into its own branch — MEASURE FIRST

**The load-bearing experiment.** A split branch is only profitable if whole
warps land in the coast branch. A mixed warp pays both paths plus divergence
overhead, which is strictly worse than the current uniform-with-zeros code.

**Why we think it works:** FMODE comes from `FLOW_MODE(GEN)`. Per
[structured/constants.ergo:96](../structured/constants.ergo#L96) the GEN→mode
mapping is "10 COAST (31%), 14 ACTIVE (44%), 8 FLOW (25%)". After `SORT_BY_GEN`
(operational per `project_ring_sort_done` memory), particles sharing a GEN are
buffer-adjacent, so a 32-lane warp contains particles from typically 1–2
adjacent GEN bins. Most warps should be FMODE-uniform.

**What to do:**

1. In [structured/fluid_subs.ergo](../structured/fluid_subs.ergo), after the
   crystal/ejected skip block at line ~243 but before the existing physics
   path, add a coast branch:

   ```
   IF FMODE = 0 THEN
     ! Coast: gravity + decay + phase lock only.
     ! Skip waveguide read, envelope, density forcing, GTX/GTY/GTZ field.
     ! Those evaluate to zero anyway when COUPLING=0 / RHO=0.
     ... gravity (steps 1, currently at lines ~260-274) ...
     ... omega decay (step 2, currently at line ~277-279) ...
     ... velocity accumulation (step 14, currently at line ~386-388) ...
     ... omega clamp ...
     ! Store back
     POS_X(I) := PX + VX * DT
     ... etc
     CYCLE
   ENDIF

   ! Original ACTIVE/FLOW path continues below
   ```

   The exact subset of steps to keep in the coast branch is: anything that
   doesn't multiply RHO, ENV, MET_GATE, or the waveguide gradient. The
   COUPLING=0 path through the original code is the spec for what coast
   currently computes — match it exactly to preserve semantics.

2. Build and run with `ERGO_PROFILE=1` per [NEXT_SESSION.md:117](../NEXT_SESSION.md#L117).
   Compare k2 time against current baseline.

3. **Decision point:**
   - If active-lane k2 unchanged or faster → branch coherence holds, proceed
     to step 2.
   - If active-lane k2 gets worse → warps are mixing, the split costs more
     than it saves. Stop. Don't proceed; the rest of this brief assumes step
     1 passed.

**Bonus diagnostic before doing this:** add a tiny shader that for each warp
records `unique(GEN)` count (using RING_SHIFT to compare lanes), histogrammed
across the 30M particle population. Expected: mostly 1, some 2, near-zero ≥3.
This is a 30-minute experiment that de-risks the whole step. Worth doing
first.

### Step 2: Naive atomic census in the coast branch

Goal: get the histogram and state counts produced on GPU, before optimizing
contention.

**State buffers** (likely already declared in
[structured/fluid_state.ergo:37-39](../structured/fluid_state.ergo#L37-L39)):

```
STATIC INTEGER :: CENSUS_OMEGA_HIST(20)
STATIC INTEGER :: CENSUS_STATE_COUNT(4)
```

These already exist. Don't redeclare. Just write into them from GPU.

**In the coast branch (after the integration math, before CYCLE):**

```
BIN := CLAMP(INT(OMEGA * 10.0), 0, 19) + 1
CENSUS_OMEGA_HIST(BIN) := CENSUS_OMEGA_HIST(BIN) + 1   ! atomicAdd
CENSUS_STATE_COUNT(3) := CENSUS_STATE_COUNT(3) + 1     ! atomicAdd (coast = state 3)
```

Per `project_compiler_progress` memory and the SCATTER classification in Part 9
of [MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md), this should emit atomics
automatically if `--fast-math` is set, or serialize otherwise. **Confirm which
mode the existing build uses** — grep `ergo_oracle` and the build.sh for the
flag. If atomics aren't being emitted, this won't work until they are.

Also: the same atomicAdd pattern needs to happen for crystal lane state count,
ejected/nova state count, active state count — each in their respective
branches. Currently those counts are computed only in the CPU census pass; they
need to migrate to GPU concurrently.

**Measure:** kernel time should jump noticeably from step 1's baseline due to
9M atomicAdds per frame contending on 24 counters. Record the jump — it
quantifies what step 3 is solving.

### Step 3: Warp-ballot reduction

Replace the per-particle atomicAdd with one atomicAdd per warp per bucket.

The four ops are already in the SPIRV backend per
`project_compiler_progress` and confirmed at
[mcl/ir.py:189-192](../mcl/ir.py#L189-L192):
- `WARP_BALLOT(predicate) → uvec4 mask`
- `WARP_BALLOT_COUNT(ballot) → u32` (popcount)
- `WARP_BALLOT_PREFIX(ballot) → u32` (exclusive scan)
- `WARP_BROADCAST_FIRST(value) → value` (first active lane broadcasts)

**Surface syntax** — check by reading
[mcl/backends/spirv.py:861, 2052-2094](../mcl/backends/spirv.py#L861) to see
how the codegen consumes these and what the .ergo source needs to look like.
If they're not currently callable from .ergo (only via IR), add the parser
wiring first. The crystal lane in
[structured/fluid_subs.ergo:218-241](../structured/fluid_subs.ergo#L218-L241)
does NOT currently use them — Level 1 atomic from
[Nullable_Warp_Pattern.md:55-62](Nullable_Warp_Pattern.md#L55-L62) — so this
might be the first .ergo-level use.

**Pattern for state count** (one bucket, simple case):

```
IS_COAST := 0
IF FMODE = 0 THEN
  IS_COAST := 1
ENDIF
BALLOT := WARP_BALLOT(IS_COAST)
WARP_N := WARP_BALLOT_COUNT(BALLOT)
! Only lane 0 in the warp does the atomic. WARP_BROADCAST_FIRST returns the
! lane index of the first active lane; compare against an intrinsic that
! returns "my lane index" — check whether that exists in the IR, or use
! WARP_BALLOT_PREFIX (which is 0 only for the first active lane).
IF WARP_BALLOT_PREFIX(BALLOT) = 0 .AND. IS_COAST = 1 THEN
  CENSUS_STATE_COUNT(3) := CENSUS_STATE_COUNT(3) + WARP_N
ENDIF
```

Caveat: that "first active lane elects" trick needs verification against the
SPIRV codegen. The natural primitive is `subgroupElect()`. If the IR doesn't
expose that, the prefix-popcount-equals-zero check is the equivalent.

**Pattern for OMEGA histogram** (20 buckets, loop):

```
BIN := CLAMP(INT(OMEGA * 10.0), 0, 19) + 1
DO B = 1, 20
  IS_BIN := 0
  IF FMODE = 0 .AND. BIN = B THEN
    IS_BIN := 1
  ENDIF
  BALLOT := WARP_BALLOT(IS_BIN)
  WARP_N := WARP_BALLOT_COUNT(BALLOT)
  IF WARP_BALLOT_PREFIX(BALLOT) = 0 .AND. IS_BIN = 1 .AND. WARP_N > 0 THEN
    CENSUS_OMEGA_HIST(B) := CENSUS_OMEGA_HIST(B) + WARP_N
  ENDIF
ENDDO
```

20-iteration loop per particle. Looks heavy but most iterations exit fast
because `IS_BIN` is computed locally and the ballot/popcount are fast warp ops.

**Measure:** kernel time should drop back toward step 1's baseline. If it
doesn't, atomic contention wasn't the bottleneck and something else is going
on — investigate before proceeding.

### Step 4: mRNA transport (double-buffered ring)

Goal: deliver census results to CPU without zeroing, without sync, without
blocking the writer.

**Design** (full discussion in `project_census_mrna` memory):

- Two 512B buffers. GPU writes one, CPU reads the other.
- `FULL_BUF` flag indicates which buffer is currently the "mRNA" (ready for
  CPU translation).
- GPU writes a slot per frame. When the slot index wraps, swap buffers and
  set the flag.
- No zeroing — validity is encoded by which buffer the flag points to.
- If CPU falls behind, oldest history is lost (correct semantics — newest
  reading wins).

**Buffer layout:**

```
PARAMETER INTEGER :: CENSUS_SLOTS = 5       ! tune later
PARAMETER INTEGER :: CENSUS_SLOT_INTS = 24  ! 20 hist + 4 state
STATIC INTEGER :: CENSUS_RING_A(CENSUS_SLOT_INTS, CENSUS_SLOTS)
STATIC INTEGER :: CENSUS_RING_B(CENSUS_SLOT_INTS, CENSUS_SLOTS)
STATIC INTEGER :: CENSUS_HEAD(1)            ! 0..CENSUS_SLOTS-1
STATIC INTEGER :: CENSUS_BUF(1)             ! 0=writing A, 1=writing B
STATIC INTEGER :: CENSUS_FULL_BUF(1)        ! which buf CPU should read (-1 = none)
```

**End-of-frame single-thread kernel** (run once per frame, one workgroup, one
thread — avoids race on `HEAD`/`BUF`):

```
! Snapshot current accumulators into CENSUS_RING[BUF][HEAD]
IF CENSUS_BUF(1) = 0 THEN
  DO B = 1, 20
    CENSUS_RING_A(B, CENSUS_HEAD(1) + 1) := CENSUS_OMEGA_HIST(B)
  ENDDO
  ... state counts ...
ELSE
  ... CENSUS_RING_B ...
ENDIF

! Reset accumulators for next frame (atomically — these are per-frame snapshots)
DO B = 1, 20
  CENSUS_OMEGA_HIST(B) := 0
ENDDO
CENSUS_STATE_COUNT(1) := 0
... etc ...

! Advance ring
CENSUS_HEAD(1) := CENSUS_HEAD(1) + 1
IF CENSUS_HEAD(1) ≥ CENSUS_SLOTS THEN
  CENSUS_HEAD(1) := 0
  CENSUS_FULL_BUF(1) := CENSUS_BUF(1)        ! release current buf to CPU
  CENSUS_BUF(1) := 1 - CENSUS_BUF(1)         ! flip writing buf
ENDIF
```

Note: the per-frame snapshot accumulators DO need zeroing here, since they're
"counts this frame" not "monotonic totals." This is different from the
ring buffer itself, which never gets zeroed.

**CPU side** (opportunistic — runs in main loop when convenient):

```c
int full = atomic_load(census_full_buf);   // -1 if nothing ready
if (full == 0) {
    // Read ring A (one 512B transfer)
    memcpy(local_census, gpu_ring_a, sizeof(local_census));
    atomic_store(census_full_buf, -1);     // signal consumed
    process_census(local_census);
} else if (full == 1) {
    // ... ring B ...
}
```

**Vulkan ordering note:** the GPU mail copy → flag set sequence needs release
semantics on the flag write so the CPU sees the mail before the raised flag.
On Vulkan this is a `vkCmdPipelineBarrier` between the copy dispatch and any
subsequent commands. The CPU read is naturally ordered because the host read
happens after `vkQueueWaitIdle` or fence wait on the dispatch — confirm
whichever pattern the existing readback in `project_render_perf` uses.

**Measure:** total CPU pipeline time. The 25ms periodic stall in CPU census
should disappear. The 96B-per-512B-buffer download should be invisible.

### Step 5: Delete CPU census pass

[structured/census.ergo](../structured/census.ergo) becomes a 10-line function
that reads the mRNA buffer and prints. The loop over particles
(line 28-41) goes away.

## What to verify before merging

1. **Determinism preserved.** Same seed, same frames, same final state. Run
   pre- and post-coast-lane builds, hash final POS_X. Must match exactly.
   (The warp-ballot reductions sum in warp-order, which is deterministic per
   [Spec/Nullable_Warp_Pattern.md:162-170](Nullable_Warp_Pattern.md#L162-L170).)

2. **Census numbers match CPU reference.** Keep CPU census alive for 100
   frames, run both, diff the histograms. Should be bitwise identical
   (integer atomics, deterministic warp accumulation).

3. **k2 cost.** Total physics kernel time. Targets:
   - Step 1 alone: same or better than baseline.
   - Step 2: noticeably worse (atomic contention).
   - Step 3: back to step 1 territory (within 1-2%).
   - Step 4: no change from step 3 (CPU work happens off the critical path).

## Open questions for the implementing session

1. Does the .ergo parser accept `WARP_BALLOT` / `WARP_BALLOT_COUNT` /
   `WARP_BALLOT_PREFIX` / `WARP_BROADCAST_FIRST` as callable functions, or
   are they IR-only? If IR-only, add parser wiring as a sub-task.

2. Does the SPIRV backend handle these ops correctly when nested inside an
   `IF` block? The `feedback_spirv_scatter` memory documents one edge case
   in IF/loop interaction at
   [mcl/backends/spirv.py:1354](../mcl/backends/spirv.py#L1354) — worth
   checking whether ballot ops have similar issues.

3. Is `--fast-math` the default in the build? Without it, atomic emission
   may be suppressed per Part 8.2 of
   [MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md).

4. What's the existing pattern for "single-thread post-physics kernel"? Is
   there already a small dispatch in
   [mcl/runtime/vk_host.c](../mcl/runtime/vk_host.c) for the spawn counter
   or oracle that can be extended, or does the end-of-frame mailbox kernel
   need a fresh dispatch?

5. Where in the frame loop does the ballot/mail kernel sequence go? After
   physics, before render? Confirm with the existing `feedback_render_sync`
   ordering rule.

## Files likely to change

- [structured/fluid_subs.ergo](../structured/fluid_subs.ergo) — add coast
  branch, warp-ballot census in coast branch
- [structured/fluid_state.ergo](../structured/fluid_state.ergo) — add
  CENSUS_RING_A/B/HEAD/BUF/FULL_BUF
- [structured/main.ergo](../structured/main.ergo) — add post-physics
  mail-kernel call
- [structured/census.ergo](../structured/census.ergo) — replace particle loop
  with mRNA read
- [mcl/parser.py](../mcl/parser.py) — possibly: expose WARP_BALLOT ops as
  parseable function calls (if not already)
- [mcl/runtime/vk_host.c](../mcl/runtime/vk_host.c) — possibly: small
  end-of-frame dispatch + CPU-side mailbox poll

## What not to do

- Don't try to do all three lanes (coast + ejected + nova) at once.
  Coast first, validate the pattern, then add others.
- Don't make the ring depth tunable from the start. Pick CENSUS_SLOTS=5,
  ship it, tune empirically once the rest works.
- Don't optimize the mail-kernel dispatch overhead until you've measured it.
  A single-threaded dispatch is microseconds; not worth folding into the
  physics kernel unless profiling says otherwise.
- Don't add monotonic-counter / delta-on-CPU logic. The snapshot-and-zero
  pattern matches the existing CPU census semantics; "monotonic with CPU
  deltas" is a different feature and a different conversation.
