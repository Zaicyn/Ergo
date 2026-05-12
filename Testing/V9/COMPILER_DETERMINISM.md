# Compiler determinism for V9

Empirical findings from compiling V9 — the "many-body physics" allocator
that extends V8 with gravitational repulsion, mean-field density tracking,
and a **Langevin dynamics stepper** — under `nvcc 13.1` for `sm_75`.

See `../asm/slab_comparison_test.{ptx,sass,host.s}` for outputs.

The compiler does the right things consistently. The determinism problem
is in the **design**: V9 is deliberately non-deterministic by construction.

## TL;DR

| Aspect | Status | Notes |
|---|---|---|
| SASS reproducibility across rebuilds | **Solid** | Bit-identical (verified) |
| Zero register spills | **Solid** | 0 bytes spill stores/loads on every kernel |
| Float math on the hot path | **Inherited from V8** | sinf/cosf/sqrtf in Viviani scatter, now plus more |
| Runtime allocator behavior reproducibility | **Broken by design** | Langevin thermostat is a random number generator |
| Code size growth vs V8 | **Modest** | +200 SASS instrs/kernel from extra warp-coop reads |
| Register usage | **Higher than V8** | 58 vs 56 regs per stress kernel |
| Stack frame | **Higher than V8** | 88 vs 80 bytes per stress kernel |
| Dead-code kernels in binary | **Yes** | Langevin step kernel ships but never called from canonical tests |

V9 changes the question. V22 cared about bit-exact math; V8 cared about
warp-uniform control flow; V9 **introduces an explicit random walk in the
allocator state**. The scatter direction in V9 depends on a global "phase"
that evolves under a stochastic differential equation. That's the goal,
not a bug — but it does mean that "the allocator behaves the same way
on every run" is no longer true.

The compiler-determinism story is unchanged from V8 (SASS is reproducible,
zero spills, kernels inline cleanly). The **runtime determinism story** is
the new failure mode.

## What's the same as V8

V9 reuses V8's slab structure: 3 size classes (64/128/256 B), `SBS_PER_WARP`
group claim, warp-uniform `__ballot_sync` placement, `ATOM.E.<op>.STRONG.GPU`
lowering. The compiler treats it the same way:

- All device helpers inlined (`v9_slab_alloc`, `v9_slab_free`, scatter math).
- PTX has zero `.func` declarations; only `.entry` kernels.
- ptxas info reports `0 bytes spill stores, 0 bytes spill loads` for all
  V9 kernels.
- SASS is bit-identical across rebuilds.

The 5 V9 kernels compiled into our test:

| Kernel | SASS instrs | Registers | Stack frame |
|---|---:|---:|---:|
| `v8_stress_kernel` (V8 baseline for comparison) | 1240 | 51 | 80 B |
| `viviani_slab_stress_kernel_v9` | 1448 | 58 | 88 B |
| `viviani_slab_bench_kernel_v9` | 1336 | 58 | 32 B |
| `viviani_slab_langevin_step_kernel_v9` | 560 | 30 | 32 B |
| `viviani_slab_density_decay_kernel_v9` | 24 | 10 | 0 B |

The V9 stress kernel is +208 SASS instructions over V8's matching kernel,
+7 registers, +8 bytes of stack frame. That's the cost of the "many-body
physics": density-field reads, phase reads, warp-cooperative bitmap scan,
mean-field gradient sampling.

It's not free, but it's a modest, *deterministic* cost. The compiler
emitted exactly what the source asked for — no surprises.

## Where V9 diverges from V8

### Stack frame growth from `__activemask` + extra warp-coop state

V8's `slab_stress_kernel` has 80 bytes of stack frame for `held[4]` /
`hcls[4]`. V9's matching kernel has 88. The extra 8 bytes hold the
warp-cooperative bitmap state that V9 introduces (the "leader reads
bitmap and broadcasts via shuffle" optimization).

That's exactly what the comment header claims V9 does:

> Warp-cooperative bitmap scan: Leader reads bitmap, broadcasts via shuffle,
> lanes only attempt atomics on actually-free slots. Reduces contention 2x.

The compiler honored it. The SASS shows `LDG` (load global, by leader),
`SHFL.SYNC` (broadcast), then conditional `ATOM.E.AND.STRONG.GPU`
guarded by the broadcast result. The atomicAnd count is roughly the
same as V8's, but each is preceded by a guard predicate — the compiler
correctly preserved the optimization.

### Register pressure climbed past the 32-reg occupancy threshold

V8 was already at 51–56 registers (SM_75 max occupancy needs ≤32).
V9 at 58 registers is *further* past the threshold, capping theoretical
occupancy at ~36% on SM_75 instead of V8's ~43%.

Same caveats as the V8 analysis apply: this is **predictable** (no spills,
known working set, no random ptxas variability) but pessimistic for
occupancy-bound workloads. The same `__launch_bounds__` knob recommended
for V8 applies here — and arguably matters more because the gap is bigger.

## The hidden float math in V8 was already a problem

A correction to the V8 doc: I claimed V8's hot path was "integer atomics,
not floats." That was wrong. V8 has this in `aizawa_slab.cuh` line 161:

```cuda
__host__ __device__ static inline void slab_viviani_normal(
        float theta, float* nx, float* ny, float* nz) {
    float s=sinf(theta), c=cosf(theta), s3=sinf(3.f*theta), c3=cosf(3.f*theta);
    float x=s-.5f*s3, y=-c+.5f*c3, z=c*c3;
    float n=sqrtf(x*x+y*y+z*z); if(n<1e-6f)n=1.f;
    *nx=x/n; *ny=y/n; *nz=z/n;
}
```

`slab_viviani_normal` is called from `slab_viviani_scatter`, which is
called from `viviani_slab_alloc` at the start of every allocation that
needs a new range. The SASS for V8's `slab_stress_kernel` actually
contains:

```
FFMA:      66 instructions
FMUL:      24
FADD:       4
MUFU.RCP:   9       (hardware reciprocal — division lowering)
MUFU.RSQ:   3       (hardware reciprocal sqrt)
FCHK:       3       (IEEE division check)
```

So the "allocator with no float math" claim from the prior doc was
wrong. **V8 does scatter math in float on every range claim.** It happens
to be amortized (one warp claims a 12-superblock range and then reuses
it for many allocations), so it's not catastrophic — but it's there.

What V9 adds on top:

- **Extra reciprocal sqrt** (`MUFU.RSQ` 3→3 in stress, but 4 in langevin):
  same Viviani math plus the Langevin thermostat's `sqrt(2*gamma*T)`.
- **Extra MUFU.RCP** (9→12 per stress kernel): more divisions from the
  density-field normalization (`gradient /= total_density` in the
  Langevin kernel, and similar reads from `effective_temp[cls]`).

If V8's float-on-the-hot-path bothers you, V9 makes it worse, not better.

## The actual determinism problem: Langevin noise

`viviani_slab_langevin_step_kernel_v9` runs on its own — not from inside
`v9_slab_alloc` — to **periodically update a global phase per size class**.
The phase is then read by allocators to bias their scatter choice.

The update step is a literal stochastic ODE:

```cuda
uint32_t seed = (uint32_t)(cls * 12345 + step_counter * 67890);
float noise = v9_slab_langevin_noise(seed);     // Box-Muller, uniform → normal
force += sqrtf(2.0f * V9_SLAB_LANGEVIN_GAMMA * temp) * noise;

float new_velocity = velocity + force * V9_SLAB_LANGEVIN_DT;
float new_phase = phase + new_velocity * V9_SLAB_LANGEVIN_DT;
// ... store back to field->global_phase[cls]
```

Two consequences:

1. **Two allocations of the same class from the same warp at the same
   "logical time" can scatter to different superblocks** depending on
   how many Langevin steps have run in between. The scatter is a
   function of `phase`, and `phase` is non-stationary.

2. **The seed itself is deterministic** (`cls * 12345 + step_counter * 67890`),
   so given an exact step count history, the noise is reproducible.
   But step count is not directly under the application's control — it
   depends on whatever cadence the host launches the langevin kernel at.

In other words: V9 is **reproducible if you control the schedule**, and
**non-deterministic relative to V8** otherwise. The slab math is the same;
the *direction* it scatters is now random-walking around the SB ring.

This is what the design literature calls the technique — "self-organize
to minimize energy" — and it's intentional. But it makes V9 a different
class of artifact than the other allocators in this codebase. V22 was
"floats must round to exactly the same bits." V8 was "every thread takes
the same path through the warp." V9 is "the warps deliberately wander."

For deterministic-workload goals, V9 is the opposite of what you want.
The mechanism that makes V9 interesting (Langevin self-organization) is
the same mechanism that breaks reproducibility.

## Dead code: langevin/decay kernels in the binary, not called

`slab_comparison_test.cu` (the canonical test we built) calls neither
`viviani_slab_langevin_step_kernel_v9` nor `viviani_slab_density_decay_kernel_v9`
from any kernel-launch site (`<<<>>>`). Yet they're in the SASS:

- `viviani_slab_langevin_step_kernel_v9`: 560 instructions
- `viviani_slab_density_decay_kernel_v9`: 24 instructions

These ship because they're declared `__global__` in the header that the
.cu file includes. CUDA's compilation model emits every `__global__`
function it sees during a TU compile.

This is a recurring pattern in the codebase — V8 has `viviani_slab_bench_kernel`
in its header that some tests don't use either. Probably not worth fixing
in V9 specifically (the Langevin kernel is small), but it's worth
knowing about for any production binary: the SASS dump shows you what
*could* be launched, not just what *is*. Stripping unused kernels would
need either separate TUs per test or explicit `static` device functions
called from one canonical wrapper.

## What V9 does well

Aside from the design choice to be non-deterministic, V9 the code is
fine:

- The atomic operations are correctly placed (no divergence inside ballot).
- Warp-cooperative bitmap scan is implemented as the comment claims.
- The Langevin RNG is a deterministic xorshift seeded from `(cls, step)`
  — if you control step count, you can replay. So V9 isn't *fundamentally*
  non-replayable; it requires careful scheduling discipline.
- No spills, clean register pressure, predictable SASS.

The compiler did not introduce any new sources of non-determinism. Every
source of run-to-run variability is in the source.

## Recommendations summary

For V9 specifically:

### If you want V9's allocator semantics but reproducible behavior
1. **Pin the Langevin step count.** Make the host code call the langevin
   kernel an exact number of times in an exact order, independent of any
   timing. Currently it's called from `viviani_slab_decay_density` which
   runs on a "periodic" schedule — non-reproducible.
2. **Use a fixed seed schedule.** The seed already depends on `step_counter`,
   so if step_counter is reproducible, the noise is too. Verify this is
   the case in your test harness.
3. **Document the determinism contract.** V9 is conditionally deterministic
   (requires schedule discipline). V8 and the others are unconditionally
   deterministic. That's a real API difference.

### If you don't need V9's many-body behavior
- **Use V8.** V9's measured costs (208 extra SASS instrs/kernel,
  +2 registers, +8 bytes stack, plus extra MUFU.RCP) buy you the
  random-walk behavior. If you want determinism, that's pure overhead.

### General (carry-over from V8)
- `__launch_bounds__(blockSize, minBlocks)` — even more useful here
  because the gap is bigger (58 regs vs SM_75's 32-reg threshold).
- Don't add `--use_fast_math` — V9's Langevin noise uses `sqrtf` and
  `logf` whose rounding matters for the SDE to remain a valid SDE.
- Don't fix the dead `langevin_step_kernel` shipping in binaries
  unless you actually find it in production paths.

## Comparison row in the codebase

| Allocator | Source of non-determinism | Compiler-level fix? |
|---|---|---|
| V22 | `-ffast-math` reassociation | Yes: don't use the flag |
| V8 | None at compile or runtime | N/A |
| GEO | None from compiler; depends on `cudaMallocAsync` driver state | N/A |
| **V9** | **Langevin stochastic ODE in scatter phase** | **No: it's the design** |

V9 is the first allocator in this codebase where the determinism problem
**is not a compiler choice you can flip off**. The code does exactly what
the source says — it's the source that introduces a random walk into the
allocator state. If you want deterministic V9, you need to either (a)
remove the Langevin path entirely, in which case it's V8 with extra
overhead, or (b) wrap the host-side launch schedule so the step count
becomes a reproducible function of the workload.
