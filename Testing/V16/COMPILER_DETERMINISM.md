# Compiler determinism for V16

Empirical findings from compiling V16 — the "half-step alternating shell"
allocator — under `nvcc 13.1` for `sm_75`.

See `../asm/test_halfstep.{ptx,sass,host.s}` for outputs.

V16 has the cleanest *intent* of any allocator we've examined: deterministic
period-2 shell alternation, no floating-point math, no random number
generators. But the implementation tripped over two compiler-visible
problems that the source structure doesn't make obvious. Worth knowing
before any of these design ideas go further.

## TL;DR

| Aspect | Status | Notes |
|---|---|---|
| SASS reproducibility across rebuilds | **Solid** | Bit-identical |
| Zero register spills | **Solid** | 0 bytes |
| Floating-point math on the hot path | **Solid** | Source has no sinf/cosf/sqrtf — V16 *did* remove the Viviani math |
| **Hidden floating-point on hot path** | **Concern** | 12 `MUFU.RCP` per kernel from integer division by runtime values |
| **Duplicate kernel shipped in binary** | **Concern** | `test_kernel` is a copy-paste of `v16_stress_kernel`; both ship at 976 SASS instrs each |
| Register usage | **Better than V8/V9** | 48 regs vs V8's 56, V9's 58 |
| Stack frame | **Better than V8/V9** | 48 B vs V8's 80, V9's 88 |
| Missing dependency: V15 directory | **Build issue** | `showdown.cu` won't compile — file copied into `Testing/` doesn't fix the path |

V16 made real progress on V8's hot-path cost — no float scatter math, no
Langevin physics, lower register count. But its replacement (integer
division/modulo for capped exclusive range calculation) **introduced its
own hidden float-equivalent operations** via the GPU's no-integer-divide
hardware limit. And the test harness copies the canonical kernel into a
second file under a new name, doubling the shipped GPU code.

## What V16 fixed (compared to V8 and V9)

The Viviani sin/cos/sqrt scatter is gone. V16 source has **zero**
references to `sinf`, `cosf`, `sqrtf`, or `logf`. The scatter mechanism
is integer-only:

```c
uint32_t scattered_wid = (global_wid * 37u) % grid_warps;
uint32_t shell = v16_halfstep_shell(global_wid, phase);
uint32_t scatter = shell_base + (scattered_wid % half_sbs);
```

A prime multiplier (`* 37`) plus modulo, plus shell selection from a
bit pattern — all integer ops. **The intent is sound.** No transcendental
math, no IEEE-rounding concerns, no scatter dependent on a random
process.

V16 also reduced resource pressure:

| | V8 stress | V9 stress | V16 stress |
|---|---:|---:|---:|
| Registers | 56 | 58 | **48** |
| Stack frame | 80 B | 88 B | **48 B** |
| SASS instrs | 1512 | 1448 | **976** |
| FFMA (float fused-multiply-add) | 66 | 73 | **0** |
| MUFU.SIN/COS | 0 / 0 | 0 / 0 | **0 / 0** |
| MUFU.RCP (reciprocal) | 9 | 12 | **12** |
| MUFU.RSQ (recip sqrt) | 3 | 3 | **0** |

V16 is **smaller and lighter than either V8 or V9** by every register/stack
measure. That's a real win. But look at `MUFU.RCP`: V16 has the same
count as V9 even though V16 has no float math.

## The hidden float: integer division becomes MUFU.RCP

Turing (sm_75) has **no integer division hardware**. Every `/` or `%`
where the divisor is runtime-variable lowers to a single-precision
reciprocal-multiply sequence:

```
I2F           Rd, divisor        ; int → float
MUFU.RCP      Rt, Rd             ; hardware reciprocal (single precision)
FMUL/FFMA     ...                ; multiply by dividend, correct
F2I           Rresult, ...       ; float → int
```

V16's `v16_slab_alloc` has many runtime divisions:

```c
uint32_t ideal = pool->pool_depth / total_warps;      // runtime / runtime
uint32_t warp_slot = global_wid % total_warps;        // runtime % runtime
uint32_t scattered_wid = (global_wid * 37u) % grid_warps;
uint32_t shell_base = shell * half_sbs;
uint32_t scatter = shell_base + (scattered_wid % half_sbs);
uint32_t n_pos = sbs_per_warp / sbs_needed;
uint32_t half_sbs = sbs_per_warp / 2;                 // div by 2 — optimized to shift
```

Most of these have *runtime* divisors (`total_warps`, `grid_warps`,
`half_sbs`, `sbs_needed`, etc.). Only `sbs_per_warp / 2` becomes a shift.
The rest each produce a MUFU.RCP-based sequence.

Counted in the SASS: **12 `MUFU.RCP` per kernel**, exactly matching V9's
count. V16's "no float math" claim was true at the **source level** but
false at the **emitted-SASS level**.

Whether this matters for determinism:

- **The result is deterministic** — same inputs give same outputs every
  time. MUFU.RCP is a specified hardware operation with bit-exact behavior.
- **Throughput is comparable to V8's float scatter** — both pay 5-10
  SASS instructions per integer division. V16 didn't escape the cost,
  it just changed where it lives.
- **Cross-GPU portability** is roughly equivalent — MUFU.RCP behaves the
  same on every sm_70+ part the same way `sinf` does.

So V16 traded one kind of float-equivalent work for another. Not a loss,
not the win the design notes claim.

To actually escape MUFU.RCP, the source would need to either:

1. **Replace runtime divisions with constants.** If `pool_depth` and
   `total_warps` were both compile-time constants, ptxas would fold the
   division away. They're not — `total_warps` is derived from grid
   dimensions, `pool_depth` is a struct field — so this would need
   templated kernels with per-launch instantiation.

2. **Replace divisions with bit ops where the divisor is a power of two.**
   The `half_sbs / 2` already does this (folded to shift). Restructuring
   the algorithm so all divisions hit powers-of-two would be the path
   to truly division-free SASS.

3. **Use the `__umulhi` reciprocal-multiply trick by hand**, baking in
   a magic-number reciprocal for known-bounded divisors. Ugly, but
   produces exactly the assembly you want.

None of those are urgent, but if "no float math" is a real V16 goal,
the SASS shows it wasn't achieved.

## Duplicate kernel: 1952 instructions of code where 976 would do

The canonical V16 test we compile (`test_halfstep.cu`) defines a
`__global__ void test_kernel(...)` that is, line by line, a **literal
copy of `v16_stress_kernel`** declared in `viviani_v16_gpu.cuh`.

Verified empirically:

- Both have 976 SASS instructions.
- Their opcode histograms are **identical** (same count of every mnemonic).
- Both ship in the SASS dump.

The only difference is the symbol name. The test calls `test_kernel`;
`v16_stress_kernel` is never called from this binary.

What happened: the V16 header defines `v16_stress_kernel` because the
author wanted a reusable stress test bundled with the allocator. The
`test_halfstep.cu` author then **copy-pasted that kernel into the test
file** instead of calling it, presumably to add minor variations during
development that ended up not happening. Both versions remain.

This is the same dead-`__global__`-in-header pattern V9 has with
`viviani_slab_langevin_step_kernel_v9`. Worse in V16 because the dead
code is the *same size* as the live code.

Two fixes worth considering:

1. **Delete `test_kernel` from `test_halfstep.cu`**, call `v16_stress_kernel`
   directly. Cuts the SASS in half.
2. **Move `__global__` kernels out of headers** into companion `.cu`
   files. The header should declare allocator device functions; tests
   should provide their own kernels. This is the same advice as V8's
   `viviani_slab_bench_kernel` in the slab header.

## The empty V15 dependency

`V16/showdown.cu` opens with:

```c
#include "../V14/viviani_v14_gpu.cuh"
#include "../V15/viviani_v15_gpu.cuh"
#include "viviani_v16_gpu.cuh"
```

`Testing/V15/` doesn't exist. The original repo's `V15/` directory does,
so the showdown harness compiles in the original location — but the
Testing setup deliberately copied only what was needed for the
canonical test (which is `test_halfstep.cu`, not `showdown.cu`).

For documenting V16's determinism this is fine. For future expansion,
either copy `V15/` into Testing/ or drop showdown.cu from the test
matrix entirely.

## What V16 does well at the compiler level

The structural determinism story is solid:

- **No spills.** ptxas reports 0 spill stores/loads on both kernels.
- **Lowest register pressure of any slab allocator** in this codebase
  (48 regs). On SM_75 that yields ~16 concurrent warps/SM occupancy
  vs V8/V9's ~14. Modest improvement, but real.
- **Smallest SASS body.** 976 instrs per stress kernel is 35% smaller
  than V8's 1512. The "half-step" design is genuinely less code than
  Viviani scatter, once you don't count the duplicated copy.
- **Same atomic semantics as V8.** `ATOM.E.<op>.STRONG.GPU` everywhere,
  warp-uniform `__ballot_sync`/`__shfl_sync` placement.
- **SASS reproducibility.** Bit-identical on rebuild.

If V16 had moved the `__global__` kernels out of the header *and*
replaced the runtime integer divisions with constants or shifts, it
would be the clear winner among the slab-style allocators. As it stands,
it's smaller than V8 but pays a similar hidden cost.

## Comparison across the slab family

| | V8 | V9 | V16 |
|---|---|---|---|
| Design intent | Viviani scatter | V8 + Langevin many-body | Half-step shell alternation |
| Float in source | sinf/cosf/sqrtf in scatter | V8's + Langevin (sqrtf/logf/cosf) | None |
| Float in SASS | 66 FFMA, 9 MUFU.RCP, 3 MUFU.RSQ | 73 FFMA, 12 MUFU.RCP, 3 MUFU.RSQ | 0 FFMA, **12 MUFU.RCP**, 0 MUFU.RSQ |
| Runtime determinism | Reproducible | **Stochastic (Langevin)** | Reproducible |
| Registers / stack | 56 / 80 B | 58 / 88 B | **48 / 48 B** |
| SASS per stress kernel | 1512 | 1448 | **976** (×2 with dup = 1952) |
| Dead `__global__` in binary | 1 (`viviani_slab_bench_kernel`) | 2 (Langevin, density_decay) | 1 (duplicate `test_kernel`) |

V16 is the smallest of the three, with the most disciplined design
intent (no stochasticity, no transcendentals). The implementation has
two compiler-visible issues — hidden integer division costs and the
test-file kernel duplication — that the source doesn't make obvious.
Both are fixable in the source; neither is a compiler flag.

## Recommendations summary

### Immediate source fixes
1. **Delete `test_kernel` from `test_halfstep.cu`**, call
   `v16_stress_kernel` directly. Cuts binary GPU code size in half.
2. **Move `__global__` kernels out of `viviani_v16_gpu.cuh`** into a
   companion `.cu` file. Same advice as V8/V9.
3. **If the showdown harness matters, restore the V15 dependency** or
   drop `showdown.cu`.

### Performance investigations worth doing
1. **Run with `__launch_bounds__(256, 4)`.** V16 has more headroom for
   higher minBlocks per SM than V8/V9 because its register count is
   lower. May yield a real occupancy win.
2. **Audit the runtime division sites.** Replace `pool->pool_depth /
   total_warps` and similar with shifts where possible, or template the
   kernel on `total_warps` if launch configurations are known.
3. **Profile the prime-multiplier scatter** (`global_wid * 37 % grid_warps`).
   If `grid_warps` is reliably a power of 2 in production, mask instead
   of mod.

### Don't bother
- Adding `--use_fast_math` — V16 has no source-level float math, so
  the flag has nothing to apply to. The MUFU.RCP usage is for integer
  division and isn't affected by `__use_fast_math`.
- "Cleaning up" the duplicate kernel by renaming — the fix is to
  delete one copy, not rename the other.

## Reproducing these measurements

```bash
cd Testing
make asm/test_halfstep.{ptx,sass,host.s}

# Count kernels:
grep -E "Function : " asm/test_halfstep.sass

# Confirm the duplicate:
python3 - << 'EOF'
import re
with open('asm/test_halfstep.sass') as f:
    text = f.read()
def hist(name):
    body = re.search(rf'Function : {re.escape(name)}.*?(?=Function :|\Z)', text, re.S).group(0)
    return tuple(sorted(set(re.findall(r'^\s+/\*[0-9a-fx]+\*/\s+(?:@!?P\w\s+)?([A-Z][A-Z0-9._]*)\b', body, re.M))))
print('Same opcode set:', hist('_Z11test_kernelP12V16_SlabPooljPj') == hist('_Z17v16_stress_kernelP12V16_SlabPooljPj'))
EOF
```

---

## Summary

V16's determinism intent is the best in the codebase: no floats, no
RNG, period-2 shell alternation. The implementation almost delivers
on that — but the runtime integer divisions in `v16_slab_alloc`
compile to `MUFU.RCP` sequences that put V16 at parity with V8's
float scatter for "hidden compiler-introduced complexity in the hot
path." And the test file duplicates the stress kernel, shipping
2× the GPU code that's actually used.

Neither problem is the compiler's fault — both are source-shape
decisions the compiler faithfully reproduced. V16 with the duplicate
deleted and the division sites cleaned up would be the cleanest slab
allocator in this codebase by both register pressure and emitted-SASS
metrics.
