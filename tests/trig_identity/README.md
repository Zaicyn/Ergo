# tests/trig_identity — three-path f32 sin/cos bit-identity harness

The audit trail for the shared f32 trig core (the "N64-modder contract":
one quarter-symmetry + minimax core, fixed coefficients, explicit fma,
running bit-identically on all three paths):

| path | implementation |
|---|---|
| CPU runtime | `core/runtime/ergo_math_kernels.h` (`_ergo_sinf`/`_ergo_cosf`) |
| SPIR-V compute | `core/backends/spirv.py` (`_emit_trig32_helper`, branchless OpFunction) |
| GLSL render shaders | `core/runtime/ergo_trig32.glsl` (`ergo_sincosf32`) |

## Run

```
python3 tests/trig_identity/run_identity.py
```

Exit 0 = PASS: the sin and cos result sections are **byte-identical**
across all three paths — raw f32 bits, no ulp tolerance, no NaN-payload
normalization (NaN/Inf input returns the explicit qNaN `0xffc00000` on
all three).

## How it works

1. `dump_trig.ergo` procedurally generates the domain (exact constructs
   only: RNE-consistent decimal literals, powers of two by doubling,
   NaN/Inf by C99 division) — M = 1,400,093 values: special cases,
   tier boundaries (6400, 0x1.8p+20), a dense ±7000 sweep, Payne-Hanek
   magnitudes (1.5·2^k, k = 21..127), denormals. It evaluates SIN/COS
   and raw-writes three f32 sections to `/tmp/trig32_domain.bin`:
   `[M domain][M sin bits][M cos bits]`.
2. The orchestrator builds that program twice (CPU, `--target spirv`)
   and compiles `glsl_dump.comp` (which `#include`s the render-shader
   core) with glslc, running it on the same domain via `run_glsl.c`
   (a minimal headless Vulkan dispatch; the device must offer
   `shaderFloat64` + `shaderInt64`, which every ergo target does).
3. Byte-compare of all three result files.

## Traps this harness caught (2026-09-04, recorded)

- **Contract-sensitive quadrant index.** The tier-1/tier-2
  `k = rint(ax·2/π)` was written `mul` then magic-number rint; the
  driver's `-O3 -ffp-contract=fast` fused it into
  `fma(ax, 2/π, m) - m`, flipping k by 1 on double-rounding boundaries
  (~66 cases in 1.4M). The core now writes the fused form explicitly in
  all three languages, so the result no longer depends on the compiler's
  contract mode.
- **GLSL fast-math license.** glslc emits no NoContraction decorations;
  the NVIDIA compiler used that license to perturb the f32 minimax
  kernel tail by 1 ulp and even folded `x - x` to `+0.0` on the NaN
  path. Fix: every fp temporary in the GLSL core is `precise`, and the
  NaN result is an explicit bit constant.
- **glslc rejects hex float literals** (GLSL profile): all constants in
  `ergo_trig32.glsl` are bit-constructed (`uintBitsToFloat` /
  `packDouble2x32`), hex value in a comment.
