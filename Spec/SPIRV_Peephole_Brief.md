# SPIRV Peephole Cleanup — Implementation Brief

## What this is

The Ergo→SPIRV codegen produces functionally correct but unnecessarily verbose
SPIRV. The CPU path (Ergo→C→GCC) is clean because GCC does aggressive
optimization. The GPU path (Ergo→SPIRV→driver) is *not* clean because driver
compilers vary in aggressiveness and a clean SPIRV is essential for:

1. **Determinism across drivers/vendors.** Part 6 of
   [MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md) promises bitwise
   reproducibility. If different drivers re-derive optimizations differently
   (e.g., one predicates an IF, another branches), the guarantee weakens.
   Emitting clean SPIRV with explicit hints makes determinism contractual,
   not best-effort.
2. **Auditability.** Right now reading a kernel's SPIRV to verify the STATIC
   constitution or check kernel structure requires mentally filtering noise.
   With these peepholes, the SPIRV becomes a faithful reflection of the source.
3. **Future profiling.** Upcoming work (coast lane + warp-ballot census) needs
   clean measurements. Comparing "naive + bloat" vs "ballot + bloat" has
   worse signal-to-noise than comparing clean against clean.

This is a **non-functional** change. After this work, identical inputs must
produce identical outputs. The only difference is the SPIRV is smaller and
more explicit about intent.

## Concrete findings

Audit of [galaxy_render.spvasm](../galaxy_render.spvasm) (5 compute kernels,
3044 lines total) shows four patterns worth fixing:

### Finding 1 — Dead `_ISub` instructions (~78 per physics kernel)

The Ergo compiler emits `_idx_N = sub(var, 1)` for every 1-based-to-0-based
array index conversion. In many cases the resulting `OpAccessChain` uses a
*different* index expression (e.g., the original 1-based index passed
through to a primitive that handles offset internally), and the `OpISub`
result is never consumed.

Example from [galaxy_render.spvasm:1023-1030](../galaxy_render.spvasm#L1023):
```
%130 = OpISub %5 %99 %74     ; never used
%131 = OpISub %5 %101 %74    ; never used
%132 = OpISub %5 %86 %74     ; never used
%133 = OpAccessChain %16 %22 %117 %75   ; uses %75 directly
%134 = OpLoad %5 %133
```

**Counted: 78 instances** of `%X - 1` followed by an `OpAccessChain` that
doesn't use the result, in the physics kernel function alone.

**Diagnostic:**
```bash
awk '/^     %69 = OpFunction/,/OpFunctionEnd/' galaxy_render.spvasm \
  | grep -c "OpISub.*%99 %74\|OpISub.*%101 %74\|OpISub.*%86 %74"
```

**Root cause:** likely in IR-to-SPIRV lowering in
[mcl/backends/spirv.py](../mcl/backends/spirv.py). The IR carries explicit
1-based subtraction (visible in `--emit-ir` output, e.g.
`_idx_8 = sub(IRRef(BIN:INTEGER), IRConst(INTEGER, 1))`), and the SPIRV
emitter both emits the `OpISub` AND handles offset adjustment in the
`OpAccessChain` path.

**Fix:** the SPIRV emitter should track which `_idx_N` values are consumed
by `OpAccessChain` only, and either (a) skip emitting the `OpISub` when the
access chain will compute the offset itself, or (b) emit the `OpISub` and
use it consistently. Pick one path through, not both.

### Finding 2 — `BITCOUNT` doesn't lower to `OpBitCount`

The function in [structured/fluid_subs.ergo:29-39](../structured/fluid_subs.ergo#L29):
```ergo
INTEGER FUNCTION BITCOUNT(N)
  CNT := 0
  DO B = 0, 7
    IF IAND(N, ISHFT(1, B)) ≠ 0 THEN
      CNT := CNT + 1
    ENDIF
  ENDDO
END
```

Currently compiles to **40+ SPIR-V instructions**: 8 unrolled iterations of
`OpBitwiseAnd / OpINotEqual / OpSelectionMerge None / OpBranchConditional /
OpPhi`. Visible in [galaxy_render.spvasm:1109-1180+](../galaxy_render.spvasm#L1109).

SPIR-V has `OpBitCount %result %operand` which most drivers map to a single
hardware instruction (`POPC` on NVIDIA, `S_BCNT1_I32_B32` on AMD).

**Fix — two options:**

**Option A: pattern recognition.** Add an IR pass that recognizes
`COUNT := COUNT + (IAND(N, mask) ≠ 0 ? 1 : 0)` accumulated over consecutive
bit positions and replaces it with a `popcount` IR op. Fragile (relies on
matching the exact source pattern) but transparent to user code.

**Option B: dedicated intrinsic.** Add `POPCOUNT(n)` to the Ergo intrinsic
list ([Spec/MCL_Intrinsic_Signatures_Complete.md](MCL_Intrinsic_Signatures_Complete.md)),
matching the precedent set by `ZERO`. User opts in explicitly, no fragile
pattern matching. The CPU lowering is `__builtin_popcount`; the SPIRV
lowering is `OpBitCount`. Documented, deterministic, single instruction.

**Recommended: Option B.** Aligns with the spec's "explicit intent over
optimizer luck" philosophy (see ZERO rationale in Part 6 of
[MCL_Design_COMPLETE.md](MCL_Design_COMPLETE.md)). Then update
`BITCOUNT(N)` callsites to use `POPCOUNT(N)`.

### Finding 3 — `MOD(x, power_of_two)` doesn't fold to `OpBitwiseAnd`

Source line in [tests/sq2core.ergo:46](../tests/sq2core.ergo#L46):
```ergo
SQ2SCT := SCATLT(MOD(ID - 1, 32) + 1) + 1
```

GCC turns `MOD(x, 32)` into `AND x, 31` (with a 3-instruction signed-fixup
dance, total ~5 ops including the modulo).

The Ergo IR shows `mod(_t_1, 32)` is emitted as `OpSRem %_t_1 %const_32` in
SPIRV. `OpSRem` is **integer division on most GPUs** — 10-30 cycles, vs
1 cycle for `OpBitwiseAnd`. Significantly worse than the CPU equivalent.

**Fix:** IR-level constant folding pass: when the second operand of `MOD` is
a compile-time constant power-of-two, emit `OpBitwiseAnd` with mask
(constant - 1). Pure SPIRV-side optimization, no surface change.

**Caveat:** must preserve Ergo semantics. Ergo `MOD` follows "sign of
dividend" per [MCL_Intrinsic_Signatures_Complete.md:85](MCL_Intrinsic_Signatures_Complete.md#L85).
For negative dividend, `AND` and `SRem` differ. If the IR carries
non-negative range information for the dividend, fold safely; otherwise
emit the safe sign-fixup pattern (still cheaper than `OpSRem`).

For arrays indexed by `MOD(I-1, N)+1` where `I` is a loop variable with
known non-negative range, the dividend is provably non-negative and the
simple `AND` is safe.

### Finding 4 — `OpSelectionMerge` always emits `None`, never `Flatten`

`grep "OpSelectionMerge" galaxy_render.spvasm | awk '{print $NF}' | sort -u`
returns only `None`. Every IF in every kernel.

For small IF bodies (one-arm clamps, single-store predicated writes), the
hint `OpSelectionMerge %merge Flatten` tells the driver "predicate this,
don't actually branch." Without the hint, the driver applies its own
heuristic — which varies across vendors and even driver versions.

This is the load-bearing concern for determinism: an `IF` that gets
predicated on driver V1 but branched on V2 can produce different warp-level
divergence behavior, which can affect:
- The order of atomic operations from different lanes (if `--fast-math`)
- Timing-sensitive memory accesses
- Future warp-ballot operations (which inspect lane masks)

**Fix:** in the SPIRV emitter, classify each `IRIf` block:
- IF body has ≤ N IR instructions (suggest N=8) AND
- No global memory writes inside the IF AND
- No function calls inside the IF
→ emit `OpSelectionMerge %merge Flatten`
- Otherwise → emit `OpSelectionMerge %merge None` (current behavior)

The N=8 threshold is conservative — drivers can predicate larger blocks but
returns diminish. Start conservative; tune empirically.

**Validation:** the OMEGA-clamp pattern (appears many times in
[structured/fluid_subs.ergo](../structured/fluid_subs.ergo): `IF OMEGA > OMEGA_MAX
THEN OMEGA := OMEGA_MAX ENDIF`) is the canonical case. After this fix, it
should emit with `Flatten`.

## Order of operations

1. **Finding 1 first (dead `_ISub`).** Highest instruction-count impact,
   simplest fix, no semantic risk. Likely just deleting an unconditional
   emit in the SPIRV codegen.

2. **Finding 4 (Flatten hints).** Pure additive — emit one more hint per
   IF. No correctness risk. Highest determinism payoff.

3. **Finding 3 (`MOD` power-of-two).** Constant folding pass. Confirm
   non-negative dividend before unconditional AND; fall back to safe
   sign-fixup otherwise.

4. **Finding 2 (`POPCOUNT` intrinsic).** New surface area (parser,
   checker, codegen for two backends). Largest scope, lowest immediate
   payoff (BITCOUNT is only called from spawn-rare paths). Could defer to
   a separate PR if scope grows.

## How to validate non-regression

The whole point of this work is "same outputs, smaller SPIRV." Regression
testing must confirm:

### Test 1: bitwise output equality

Build `galaxy_render` before and after, run with the same seed for the same
number of frames, hash final particle state (POS_X, POS_Y, POS_Z, VEL_*,
OMEGA_NAT, FLAGS). Hashes must match exactly.

Suggested invocation:
```bash
# Before
git stash
python -m mcl --target spirv --precision f32 --no-split --render \
  -N 1000000 -M 1000000 -o galaxy_before galaxy_structured.ergo
./galaxy_before --frames 1000 --hash-final > before.hash

# After
git stash pop
python -m mcl --target spirv --precision f32 --no-split --render \
  -N 1000000 -M 1000000 -o galaxy_after galaxy_structured.ergo
./galaxy_after --frames 1000 --hash-final > after.hash

diff before.hash after.hash   # must be empty
```

Note: `--hash-final` may not exist; if not, add a CPU-side hash of the
particle arrays after the last frame as a one-line driver addition.

### Test 2: SPIRV instruction count drop

```bash
wc -l galaxy_render.spvasm   # before vs after
grep -c "OpISub" galaxy_render.spvasm   # should drop substantially
grep -c "OpSRem" galaxy_render.spvasm   # should drop where folded
grep "OpSelectionMerge" galaxy_render.spvasm | grep -c Flatten   # should be > 0
```

Expected: 10-15% fewer total ops, dozens of fewer `OpISub`s, several
`Flatten` hints.

### Test 3: framerate unchanged or better

`ERGO_PROFILE=1 ./galaxy_render --frames 500` before and after.
k1, k2, k3 timings should be unchanged or slightly better. A regression
indicates either a correctness bug or that the driver was already DCE'ing
the dead ops and the wins are masked.

### Test 4: kernel report shows fewer scratch IRs

```bash
python -m mcl --target spirv --kernel-report galaxy_structured.ergo
```

Output should show reduced per-kernel IR count.

## Files likely to change

- [mcl/backends/spirv.py](../mcl/backends/spirv.py) — primary target. The
  emit functions for `OpAccessChain`, `OpSRem`, `OpSelectionMerge` are the
  candidates.
- [mcl/ir.py](../mcl/ir.py) — add `POPCOUNT` op if Finding 2 is taken.
- [mcl/ir_builder.py](../mcl/ir_builder.py) — wire `POPCOUNT` to parser
  output.
- [mcl/parser.py](../mcl/parser.py) — recognize `POPCOUNT` as intrinsic.
- [mcl/checker.py](../mcl/checker.py) — type-check `POPCOUNT(INTEGER) → INTEGER`.
- [mcl/codegen.py](../mcl/codegen.py) — C-side lowering of `POPCOUNT` to
  `__builtin_popcount`.
- [Spec/MCL_Intrinsic_Signatures_Complete.md](MCL_Intrinsic_Signatures_Complete.md) —
  document `POPCOUNT` in Category 6 (or wherever bitwise intrinsics live).

## What not to do

- **Don't try to "fix" the IR to be SSA / drop temporaries / generally
  modernize the IR.** That's a different project. This work is narrow:
  emit cleaner SPIRV from the existing IR. The IR's verbosity is fine
  because GCC handles it on the CPU side.
- **Don't add `Flatten` hints unconditionally.** A large IF body with
  `Flatten` forces the driver to fully predicate both arms, executing all
  instructions even when the mask is zero. For large IFs this is strictly
  worse than branching. The body-size heuristic matters.
- **Don't rewrite `BITCOUNT` to use `POPCOUNT` in the same PR as adding
  `POPCOUNT`.** Land the intrinsic first, migrate callsites separately,
  measure separately.
- **Don't measure performance impact in isolation.** The downstream
  driver compiler may already be doing some of this work. The point of
  the cleanup is *determinism and auditability*, not necessarily speed.
  If the wall-clock numbers don't change, that's *fine* — the win is that
  they now can't change across driver versions either.

## Open questions for the implementer

1. Does `OpAccessChain` in the current SPIRV emit always handle 1-to-0
   conversion, or does it sometimes rely on the caller having done it?
   The answer determines whether the dead `_ISub` fix is "delete the emit"
   or "delete the emit AND fix the access chain to not double-subtract."

2. Is there an existing IR pass infrastructure to plug constant folding
   into, or does it need to be a new pass in
   [mcl/ir_affine.py](../mcl/ir_affine.py) (which already handles affine
   index analysis)?

3. What's the deterministic baseline? Is there an existing CI check or
   regression suite that captures bitwise equality across simulation
   runs? If not, the implementer needs to establish one before changing
   any emission.

4. Are there existing `--emit-spirv`-style flags that dump SPIRV without
   running the simulation? Useful for the SPIRV instruction-count
   comparison without recompiling/launching every iteration.
