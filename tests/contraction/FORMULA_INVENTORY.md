# FORMULA_INVENTORY.md — the contraction lint's rules vs gcc reality

2026-08-29. Question: does the rule set in `core/ir_contract.py` (the
fusible-site analysis behind the contraction boundary lint) predict what
gcc actually fuses under the recipe flags (`-O3 -fwrapv
-march=x86-64-v3 -ffp-contract=fast -fno-math-errno -std=c11`)?

Method (`tests/contraction/gcc_fusion_audit.py`): for each program, emit
C (`python -m core <prog> --emit-c`), extract every fp `a*b±c` site
(temp-chained and inline forms), classify per the documented rule, then
compile with the recipe and read the RTL-final dump (fusion shows as
`{*fma_fmadd_*}` patterns with source-line tags; plain ops as
`fop_[ds]f`/`adddf`/...). Verdicts per site: `fused`, `unfused`,
`mixed` (both forms in one binary — path/index-dependent), `absent`
(attribution gap). Audit calibrated on three known programs first
(owned_math_smoke: sin fused/cos+exp+pow not; fusible_stress: all seven
loop sites fused; coil: zero sites).

## Coverage (corpus: all 197 golden-corpus programs + ribosome ul18_stag5
+ wigner h2_wig_hhb + ab/schrod_2d_stream + min/dirac/* + min/dendrite/*
+ fusible_stress + core/runtime/ergo_math_kernels.h)

42,499 sites audited. **Zero dangerous-direction mismatches** (no site
where the rule says never-fuse but gcc fuses, and no rule-fusible site
that structurally cannot fuse).

| shape class | sites | rule==gcc (deterministic) | fragile (path/shape-dependent) | attribution gap |
|---|---:|---:|---:|---:|
| plain (`x±y`, one side a mul) | 25,686 | 4,877 | 17,436 | 3,373 |
| both-mul (`a*b ± c*d`) | 14,959 | 10 | 14,147 | 802 |
| call-factor (`call()*k ± c`) | 1,552 | 646 | 494 | 412 |
| all-constant mul | 302 | 302 | 0 | 0 |

Reads on this table:

- **The all-const rule is exact** (302/302 folded unfused, as the rule
  says). The earlier v1 audit flagged two of these as mixed; that was
  ±2-line attribution-window contamination from a neighboring fused
  accumulator — fixed by matching the fused insn's `[orig:...]` temp
  names against the site's operand names.
- **Plain sites**: where the rule and gcc agree deterministically, they
  agree 100%. The big "fragile" share is mostly *vectorized loop* sites:
  gcc's dump shows both fused (main vector loop) and unfused (scalar
  remainder/epilogue) forms of the same site in one binary — the fusion
  of a vectorized site is index-dependent by construction (last
  N mod vector-width elements compute unfused). For the lint's MAY
  semantics this is correctly "fusible"; for bit-prediction it means
  vectorized loop sites are not uniformly one or the other.
- **both-mul sites** in physics loops (the `dx*dx + dy*dy` distance
  forms) are nearly all in vectorized loops → same epilogue effect.
- **call-factor sites** (the sin/cos class from the smoke test): 646
  deterministically fused, 494 path-dependent, 412 unattributed. This
  is the genuinely unstable class: same source shape fuses or not
  depending on the callee's return-path structure after inlining
  (probe9: multi-return fused, single-return didn't, noinline fused;
  smoke: sin fused, cos/exp/pow didn't — in one loop).

## The one rule that needed sharpening

The lint's rule table should split call-factor sites out of "fusible"
into "**fusible-fragile**": a site whose mul factor is the result of a
call (intrinsic or user function, single- or multi-return) fuses
according to gcc's post-inlining PHI/sink behavior, not according to any
property visible at IR level. Predicting "fused" for these is wrong
often enough (494/1552 path-dependent) that the lint should say so.

**Status: APPLIED (2026-08-29, after the audit).** `ir_contract.py` now
marks such sites `fragile: True` and the SPIR-V boundary lint reports
them separately ("call-factor sites … where CPU fusion is callee-shape
luck"). Verified: no corpus test references the old lint text;
contraction suite + HHB suites rerun green.

## Programs whose CPU bits are least stable across compiler versions

207 of 213 audited programs contain at least one fragile site (they
dwarf the stable set). The fragile-set leaders by site count:

- min/ribosome/ul18_stag5.ergo — 298 sites
- tests/waveform_parkin_*, t4lyso_*, trpcage_*, uchl1_*, gb1_*,
  snase_*, ww_*, bba5_*, chain_fold_*, molecule_* (164 MD programs,
  ~233 sites each)
- min/dirac/dirac_radial.ergo — 122
- min/wigner/h2_wig_hhb.ergo — 75
- tests/buc_colony.ergo — 27
- min/ab/schrod_2d_stream.ergo — 16
- min/dendrite/* (dbm_radial family, laplace_annulus) — 7-13 each
- tests/sq4core.ergo — 8, tests/buc_membrane_unit.ergo — 11

Conversely, programs NOT in the fragile list (the majority of the
non-physics corpus: alloc_smoke, prng, int64, sq2core, write_formats,
etc.) have zero fragile sites — their CPU bits depend on the recipe
only through the guaranteed classes.

## Consequences stated plainly

1. For the lint (a MAY analysis reporting possible CPU≠GPU boundary
   sites): current rules are sound — zero false "never" predictions.
2. For exact CPU bit-prediction under the recipe: plain straight-line
   sites are 100% predictable; vectorized-loop sites are index-dependent
   by construction (main-loop/epilogue); call-factor sites are
   callee-shape luck. Only the first class can ever be promised.
3. The fragile program list above is the answer to "which programs
   move if the compiler version changes" — with the caveat that
   chaotic MD amplifiers flip on ANY single-site change, so their
   stability is structural, not fixable by pinning recipes.
4. The kernel header itself has 7 sites; all are intentional
   (explicit-fma design) or exact-mul neutral; the two `sl + u3 * pt`
   exp2 tails are call-factor-shaped and read fragile under the audit.
   **Status: APPLIED (2026-08-29).** Bit-check first: both lines under
   gcc AND clang with recipe flags produced byte-identical output over
   the full pow/powf sweep (30,156 + 30,000 cases per compiler) with
   the lines as-is vs explicit `fma(u3, pt, sl)`/`fmaf` — both compilers
   were already fusing them — so the explicit forms were applied
   (ergo_math_kernels.h), the full ulp suite reruns with all bounds
   holding (pow ≤1 ulp both precisions, gcc==clang), and the corpus
   gate's move set is unchanged program-for-program.

## Reproduce

```
python3 tests/contraction/gcc_fusion_audit.py --corpus    # full sweep
python3 tests/contraction/gcc_fusion_audit.py <prog.ergo> # one program
```

Probes used for the ground rules: tests/contraction/probe*.c (bakes the
measured gcc behavior: left-mul-wins, sub sign-flips, NEG folds,
multi-use fuses, cross-block fuses, (a+b)*c never, all-const folds,
f32 mirrors f64).
