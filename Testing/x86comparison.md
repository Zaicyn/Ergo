# Hot-path assembly snippets — Ergo / V22 / V8

Side-by-side listings of the load-bearing inner loops for each of the
three systems in the allocator comparison. These are the actual
compiler outputs from the measurements documented in
[COMPARISON_TABLE.md](COMPARISON_TABLE.md) and
[BASELINE.md](BASELINE.md). Each section lists the gcc/nvcc invocation
needed to regenerate the asm — the listings themselves are build
products and not tracked, but the source files and build commands are.

Hardware/toolchain context (matches the measurement runs):

- gcc 15.2.1 on Linux x86-64 (Zen 2, Ryzen 5 3600)
- nvcc 13.1.115, sm_75 (RTX 2060)
- Intel syntax (`-masm=intel`) for x86 listings
- SASS extracted via `cuobjdump --dump-sass`

## 1. Ergo CPU arena emit (the bump + bounds check)

The hot path is the inner loop of `tests/allocate_bench.ergo` after
`mcl --emit-c` → `gcc -O3 -march=x86-64-v3 -ffp-contract=fast -fno-math-errno
-std=c11 -S -masm=intel`.

The arena offset is promoted to a register (`rdx`) across the entire
loop body; loaded once on entry, stored once on exit. Per-iteration
cost is six ops, three of which are the arena emit itself.

### Source (the Ergo emit, from `core/codegen.py`)

```c
{
    size_t _sz = (64) * sizeof(double);            /* 512 */
    size_t _aligned = (_sz + 63) & ~(size_t)63;    /* 512, already aligned */
    if (_ergo_arena_offset + _aligned > ERGO_ARENA_BYTES) {
        fprintf(stderr, "ergo: arena exhausted ...");
        abort();
    }
    A = (double *)(_ergo_arena + _ergo_arena_offset);
    _ergo_arena_offset += _aligned;
}
A[0] = (double)I;
total = total + A[0];
```

### x86 inner loop (gcc 15.2.1, `-O3 -march=x86-64-v3 -ffp-contract=fast`)

```asm
.L3:
    mov     rcx, rdx                              # save current base for the access
    lea     rdx, 512[rdx]                         # bump offset by 512
    cmp     rdx, 1073741824                       # bounds check vs ERGO_ARENA_BYTES (1<<30)
    ja      .L34                                  # → abort path if exceeded
    vcvtsi2sd  xmm0, xmm2, eax                    # convert I to double
    add     eax, 1                                # I++
    vaddsd  xmm1, xmm1, xmm0                      # total += xmm0
    mov     esi, 1                                # live-out sentinel (abort-path bookkeeping)
    vmovsd  QWORD PTR 512[rdi+rcx], xmm0          # A[0] = REAL(I)  (the store)
    cmp     eax, 1001                             # loop counter
    jne     .L3
```

Prologue (loads offset once before loop entry):

```asm
.L12:
    vxorps  xmm2, xmm2, xmm2
    vxorpd  xmm1, xmm1, xmm1
    mov     eax, 1
    mov     rdx, QWORD PTR _ergo_arena_offset[rip]   # LOAD offset, once
    lea     rdi, _ergo_arena[rip-512]
    ...
```

Epilogue (stores offset once after loop exit):

```asm
    mov     QWORD PTR _ergo_arena_offset[rip], rdx   # STORE offset, once
```

**Per-iteration breakdown:**

| Instruction | Purpose | Allocator cost? |
|---|---|---|
| `mov rcx, rdx` | save base for access | ✓ |
| `lea rdx, 512[rdx]` | bump offset | ✓ |
| `cmp rdx, 1073741824` | bounds check | ✓ |
| `ja .L34` | branch on overflow (predicted not taken) | ✓ |
| `vcvtsi2sd xmm0, xmm2, eax` | int → double | (bench work) |
| `add eax, 1` | I++ | (loop control) |
| `vaddsd xmm1, xmm1, xmm0` | accumulator | (bench work) |
| `mov esi, 1` | sentinel for abort path | (bookkeeping) |
| `vmovsd [rsi+r8], xmm0` | A[0] = REAL(I) | (the actual write to allocated memory) |
| `cmp/jne` | loop branch | (loop control) |

The four arena-emit instructions (`mov` + `lea` + `cmp` + `ja`)
overlap with the floating-point work because they're on independent
registers. Pass 2 measured this as 0.77 ns/iter in isolation (the
`nostore` variant of `Testing/baseline_arena.c`), vs the CPU pure-bump
floor of 0.51 ns/iter — 0.25 ns delta is the bounds check.

### Regenerate

```bash
# From the repo root, on master with arena lowering merged:
python -m core --emit-c tests/allocate_bench.ergo > /tmp/allocate_bench.c
gcc -O3 -march=x86-64-v3 -ffp-contract=fast -fno-math-errno -std=c11 \
    -S -masm=intel -fno-asynchronous-unwind-tables \
    /tmp/allocate_bench.c -o /tmp/allocate_bench.s
```

The `.L3:` label may be renumbered by different gcc versions; look for
the inner loop that contains `vmovsd ... xmm0` and a `cmp ... 1073741824`.

## 2. V22 hand-SSE residual

The hot function is `bench_handsse` from `Testing/V22/v22_compare.c`,
which wraps `sq2_simd_triple_xor_residual_sse` (the canonical V22
operation). 67 packed-SSE instructions per call. The key thing the
table shows is FMA fusion under `-ffp-contract=fast`: instructions
like `vfmadd132ps` and `vfnmadd132ps` appear, fusing separate `vmulps`
+ `vaddps` pairs into single FMA ops. Under plain `-O3 -march=native`
without `-ffp-contract=fast`, these stay as separate ops; the FMA
fusion is what buys the ~2% throughput win documented in
[V22/COMPILER_DETERMINISM.md](V22/COMPILER_DETERMINISM.md).

### Source (one of the 12 vertex transforms, plus the final reduction)

```c
/* From squaragon_v2.h — sq2_simd_triple_xor_residual_sse hot body */
__m128 v_x = _mm_mul_ps(scale_vec, _mm_load_ps(seed_x));
__m128 v_y = _mm_mul_ps(scale_vec, _mm_load_ps(seed_y));
__m128 t0 = _mm_add_ps(v_x, bias);
__m128 t1 = _mm_mul_ps(v_x, phi);
/* ... 9 vmulps, 30 vaddps, 4 vsubps, 6 vhaddps, 1 vsqrtps, 1 vdivps ... */
```

### x86 (gcc 15.2.1, `-O3 -march=native -ffp-contract=fast` — FMA enabled)

```asm
bench_handsse:
    vbroadcastss xmm1, xmm0                         # scale → all 4 lanes
    vmulps    xmm4, xmm1, XMMWORD PTR .LC5[rip]     # _86 = scale * seed_x
    vmulps    xmm7, xmm1, XMMWORD PTR .LC4[rip]     # _85 = scale * seed_y
    vxorps    xmm3, xmm3, xmm3                      # zero
    vbroadcastss xmm14, DWORD PTR .LC0[rip]
    vmovaps   xmm2, xmm0                            # save scale
    vxorps    xmm0, xmm0, xmm0
    vmulss    xmm2, xmm2, xmm0
    vmulss    xmm15, xmm2, DWORD PTR .LC0[rip]
    vaddss    xmm0, xmm2, xmm0
    vbroadcastss xmm10, xmm2
    vaddss    xmm0, xmm2, xmm0
    vaddps    xmm6, xmm4, xmm3
    vaddps    xmm5, xmm7, xmm3
    vbroadcastss xmm3, DWORD PTR .LC1[rip]
    vmulps    xmm11, xmm7, xmm14                    # _95 = _85 * phi
    vmovaps   xmm12, xmm4
    vmovaps   xmm8, xmm4
    vaddss    xmm0, xmm2, xmm0
    vbroadcastss xmm15, xmm15
    vbroadcastss xmm0, xmm0
    vaddps    xmm0, xmm0, xmm4
    vmulps    xmm9, xmm7, xmm3                      # _92 = _85 * tmp
    vfmadd132ps  xmm12, xmm11, xmm3                 # FMA: tmp172 = xmm12*xmm3 + _95
    vfmsub132ps  xmm3, xmm11, xmm4                  # FMA: tmp167 = xmm3*_95 - _86
    vaddps    xmm0, xmm0, xmm4
    vfnmadd132ps xmm8, xmm9, xmm14                  # FMA: _93 = -(xmm8*_92) + tmp169
    vfmadd132ps  xmm14, xmm9, xmm4                  # FMA: _100 = xmm14*_92 + _86
    vaddps    xmm0, xmm0, xmm4
    vaddps    xmm12, xmm12, xmm6
    ; ... ~30 more vaddps doing the magnitude-squared accumulation ...
    vhaddps   xmm0, xmm0, xmm0                      # horizontal-add for reduction
    vhaddps   xmm0, xmm0, xmm0
    vhaddps   xmm5, xmm5, xmm5
    vhaddps   xmm2, xmm2, xmm2
    vhaddps   xmm5, xmm5, xmm5
    vhaddps   xmm2, xmm2, xmm2
    vmulps    xmm5, xmm5, xmm5                      # _58 = sum²
    vfmadd132ps xmm2, xmm5, xmm2                    # FMA: tmp210 = magnitude
    vfmadd132ps xmm0, xmm2, xmm0
    vsqrtps   xmm0, xmm0                            # final magnitude
    vdivps    xmm0, xmm0, xmm1                      # residual = mag / scale
    ret
```

**Op-mix (full function, both regimes):**

| Op | -O3 -march=native | + -ffp-contract=fast | + -ffast-math |
|---|---:|---:|---:|
| `vmulps` / `vmulss` | 9+ | 5 (4 fused into FMAs) | varies (heavy reassoc) |
| `vfmadd*ps` | 0 | 5 | varies |
| `vaddps` / `vaddss` | 30 | 28 | reordered/merged |
| `vsubps` | 4 | 4 | 4 |
| `vhaddps` | 6 | 6 | 0 (fully reassociated) |
| `vsqrtps` + `vdivps` | 1 + 1 | 1 + 1 | replaced with vrsqrtps approximation |
| **Algebraic invariant preserved** | ✓ | ✓ | **✗** |

The single most important V22 finding: **`-ffp-contract=fast`
preserves the algebraic-zero property of the residual** while still
emitting FMAs. `-ffast-math` does not — it reassociates the additions
and the residual drifts from bit-zero on unperturbed inputs.
[V22/COMPILER_DETERMINISM.md](V22/COMPILER_DETERMINISM.md) covers this
in detail.

### Regenerate

```bash
cd Testing && make compare
# produces asm/v22_compare.{base,fma,fast}.s alongside the corresponding .elf binaries
# bench_handsse hot loop is around line 377 in v22_compare.fma.s
```

## 3. V8 viviani_slab_alloc bitmap claim (SASS, not x86)

V8 is GPU-side: CUDA → PTX → SASS via nvcc. There is no x86 hot path
to compare; the relevant ISA is SASS (NVIDIA's hardware instruction
set). Including it here for completeness because the COMPARISON_TABLE
references the V8 hot-path op count alongside the CPU systems.

The canonical operation is **the bitmap-bit claim** — when a warp
attempts to acquire a slot from a slab's bitmap. This is the
ATOM.E.AND.STRONG.GPU op surrounded by ballot-coordination
instructions.

### Source (from `Testing/V8/aizawa_slab.cuh`, `viviani_slab_alloc`)

```cpp
/* Hot path: claim a slot via atomicAnd on the bitmap.
 * Each lane attempts a distinct bit; STRONG.GPU ordering guarantees
 * visibility across the whole device. */
uint32_t old = atomicAnd(&sb->bitmap, ~(1u << slot));
if (old & (1u << slot)) {
    /* We claimed it. */
    return sb->data + slot * stride;
}
/* Otherwise advance cursor and retry. */
```

### SASS (nvcc 13.1, sm_75, `-O3`)

From `Testing/asm/aizawa_slab_test.sass`, the slab_stress_kernel
hot path:

```asm
        /*2640*/   ATOM.E.AND.STRONG.GPU PT, R20, [R20], R51 ;     ; the bitmap atomic
        /*2650*/   LOP3.LUT P2, RZ, R20, R49, RZ, 0xc0, !PT ;      ; (old & ~target_bit) test
        /*2660*/   BRA.DIV 0x5390 ;                                ; divergent branch handler
        /*2670*/   VOTE.ANY R15, PT, P2 ;                          ; consensus across lanes
        /*2680*/   LOP3.LUT R2, R15, R12, RZ, 0xc0, !PT ;          ; mask combine
        /*2690*/  @P2 BREAK B1 ;                                   ; exit if claimed
        /*26a0*/  @P2 BRA 0x29b0 ;
        /*26b0*/   ISETP.NE.AND P0, PT, R0, R13, PT ;              ; cursor advance test
        /*26c0*/   IMAD.MOV.U32 R47, RZ, RZ, RZ ;
        /*26d0*/  @!P0 LDS.U R5, [R10] ;                           ; load shared-mem cursor
        /*26e0*/  @!P0 IMAD.IADD R2, R6, 0x1, R5 ;                 ; cursor += 1
        /*26f0*/  @!P0 IMAD.WIDE.U32 R4, R2, 0x38e38e39, RZ ;      ; reciprocal-multiply for /18
        /*2700*/  @!P0 SHF.R.U32.HI R5, RZ, 0x2, R5 ;              ; (/18 via reciprocal)
        /*2710*/  @!P0 IMAD R47, R5, -0x12, R2 ;                   ; (mod 18)
        /*2720*/  @!P0 STS [R10], R47 ;                            ; store back to shared-mem
        /*2730*/   BRA.DIV 0x53d0 ;
        /*2740*/   SHFL.IDX PT, R47, R47, R13, 0x1f ;              ; broadcast cursor to all lanes
        /*2750*/   STS [R10], R47 ;
        /*2760*/   IADD3 R50, R50, 0x1, RZ ;                       ; outer counter++
        /*2770*/   ISETP.GE.U32.AND P0, PT, R50, R48, PT ;
        /*2780*/  @P0 BRA 0x27f0 ;
        /*2790*/   VOTE.ANY R2, PT, PT ;                           ; warp-wide active mask
        /*27a0*/   YIELD ;                                         ; hint scheduler to switch warps
        /*27b0*/   VOTEU.ANY UR5, UPT, PT ;
        /*27c0*/   LOP3.LUT P0, RZ, R2, UR5, RZ, 0xc, !PT ;
        /*27d0*/  @!P0 BRA.U 0x24c0 ;                              ; retry loop edge
        /*27e0*/   BRA 0x2790 ;
```

**Breakdown:**

- **The atomic itself**: `ATOM.E.AND.STRONG.GPU` at `/*2640*/` — one instruction, fully serialized through L2's atomic unit.
- **The claim test**: `LOP3.LUT P2, RZ, R20, R49, RZ, 0xc0, !PT` at `/*2650*/` — single 3-input LUT instruction tests whether the bit was set in the old value.
- **Warp consensus**: `VOTE.ANY R15, PT, P2` at `/*2670*/` — broadcast the claim result across the warp.
- **Predicated cursor advance**: `/*26b0/*` through `/*2720*/` — ~7 instructions, all `@P0` or `@!P0` predicated, so only the lanes that *failed* to claim execute them.
- **Cursor recirculation**: `IMAD.WIDE.U32` + `SHF.R.U32.HI` + `IMAD` at `/*26f0/-/*2710*/` — compute `cursor % SBS_PER_WARP` via reciprocal multiply (the magic constant `0x38e38e39` is `2^32 / 18` for SBS_PER_WARP=18).

**Per-claim cost on the fast path** (claim succeeds, no retry): 
~10 SASS ops including the atomic. With retries, the cursor-advance 
path adds ~7 more predicated ops. Matches the V8 head-to-head doc's 
"10-30 SASS ops/lane amortized" framing.

### Regenerate

```bash
cd Testing && make sass
# produces asm/aizawa_slab_test.sass via cuobjdump --dump-sass
# slab_stress_kernel starts at line 25:
#   Function : _Z18slab_stress_kernelP8SlabPooljPj
# The atomic claim region is around offset /*2640*/ (line ~1251 in the dump).
```

## Side-by-side summary

| System | Hot-path op count | Where the cost lives |
|---|---:|---|
| **Ergo arena emit** | 4 x86 ops (mov+lea+cmp+ja) | Bump + bounds check, register-resident offset |
| **V22 residual** | 67 SSE ops (full function) | Packed 4-lane FP math, 6 horizontal reductions, sqrt+div finale |
| **V8 slot claim** | ~10 SASS ops fast path | One atomicAnd, ballot consensus, cursor recirculation |

Each is doing structurally different work. The op counts aren't 
directly comparable across systems; they characterize where each 
design spends its hot-path budget. See 
[COMPARISON_TABLE.md](COMPARISON_TABLE.md) Sub-table 2b for the full 
abstraction-level disclaimer.

## Notes on what's NOT shown here

- **V22 scalar version** (`bench_scalar`): 209 scalar fp ops, 12-deep
  accumulator chain. Available in `v22_compare.base.s` for comparison
  against the hand-SSE version. Showcases what the SSE rewrite buys
  (2.25× speedup under strict IEEE).
- **Ergo SPIRV** (the GPU side): documented in
  [COMPARISON_TABLE.md](COMPARISON_TABLE.md) Sub-table 2b. The
  Ergo→SPIRV→driver-SASS pipeline produces different hot-path SASS
  depending on the driver version; the SPIRV is what Ergo guarantees,
  not the SASS.
- **The Ergo physics kernel** (1,112 SPIRV ops): too large to
  reproduce inline; the op-mix histogram is in COMPARISON_TABLE.md.
  Regenerate the SPIRV via the build command in that doc.
