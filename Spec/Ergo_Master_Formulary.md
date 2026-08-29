# The Ergo Master Formulary

*What the project is, what its formulas are, what failed, and what the
failures taught. Compiled 2026-08-29 from thirteen domain surveys, the
finding documents they cite, and the engine-side session record. Every
claim cites its source; a number without a citation is a bug in this
document.*

## 1. Prologue

Ergo is a deterministic mathematical compute language — 16 operators,
F77+Allocatable memory, no hidden allocation, bit-reproducible by
construction (`Spec/Ergo_Spec.md` Part 1–3) — and the compiler/runtime
around it: an IR backend targeting C (gcc recipe) and SPIR-V (Vulkan
compute), a GPU loop-extraction taxonomy, and a growing set of owned
numeric kernels. On top of that substrate the project has run two
hundred-plus experiments: protein and RNA folding engines, quantum
chemistry solvers, lattice-growth models, glueball effective models,
allocators, and an integrity-verification family.

This document is organized by *pattern*, not by domain — the same
three or four ideas keep reappearing under different physics, and the
patterns are the transferable content. The domain chronology is in the
index (§8). The failure catalog (§5) is the most valuable section: it
is the only place the project's negative results are collected, and it
is deliberately longer than the victory lists.

How to read it: each section's formulas are the ones that survived
certification. "Certified" has a specific meaning here — pre-registered
oracles, an independent mirror, and byte-exact reruns (§6). When a
number is cited from a findings document, that document contains the
oracle log behind it.

## 2. The numerical core

Everything numerical in the project reduces to a handful of rules,
each bought with at least one failure.

**The determinism recipe.** The x86 determinism audit measured the flag
space and landed on `-O3 -fwrapv -march=x86-64-v3 -ffp-contract=fast
-fno-math-errno -std=c11` (`core/driver.py:29-36`,
`Spec/x86_Determinism_Audit.md:21-46`). FMA fusion is IEEE-754
arithmetic and deterministic per build; reassociation is neither — the
V22 hand-vectorized geometry kernel's algebraic-zero residual drifts to
~0.053 over 1M calls under `-ffast-math`, and stays bit-exactly 0.0
under the recipe (`Spec/Ergo_Spec.md` Part 7;
`Testing/V22/COMPILER_DETERMINISM.md`). The forbidden list —
`-ffast-math -Ofast -fassociative-math -freciprocal-math
-ffinite-math-only` — is written into the same audit. Single vs double
rounding is the whole game: `a*b+c` computed as mul-then-add rounds
twice, `fma(a,b,c)` rounds once, and a simulator that cares about its
last ulp must know which it's getting.

**The libm hole and the owned kernels.** glibc and musl disagree
bitwise on sin/cos/exp/pow (measured by hashing 200k results per
function; they agree on log/atan2/sqrt, which is luck, not contract —
`Spec/Ergo_Hardware_Op_Map.md` §2). So the six hot transcendentals are
now owned: fixed-coefficient Chebyshev/fdlibm kernels with explicit
`fma` at every contraction point, documented argument reduction
(Payne-Hanek with a 1440-bit 2/π table for huge trig arguments),
measured ≤2 ulp f64 and ≤2 ulp f32 against an 800-bit mpmath reference,
bit-identical between gcc 16.1.1 and clang 22.1.8
(`core/runtime/ergo_math_kernels.h` header comment;
`tests/math_kernels/RESULTS.md`). pow runs its series with
double-double heads and plain-f64 tails — the poly-with-dd-head split
took it from 534 to 107 ns/call at the same measured 1-ulp bound
(commit `bf6963b`). A loud `--libm-fallback` (driver flag, env var, or
macro) maps back to host libm when the kernels can't build.

**Contraction is compiler-owned.** Which `a*b±c` sites become FMA was,
by measurement, not predictable from the IR: in one loop gcc fused
`S += sin(X)*0.37` and not `S += cos(X)*0.73`, because the callee's
return-path structure after inlining decides whether the multiply lands
in a PHI (`Spec/Ergo_Hardware_Op_Map.md` §4, "Contraction policy";
probes in `tests/contraction/probe*.c`). A naive IR rule emitting fma
everywhere moved 145/197 corpus programs' CPU outputs (chaotic
amplifiers flip on one site). So the GPU side pins `NoContraction` on
every fp arithmetic result — the RTX 2060 driver does contract
undecorated pairs, measured — and the compiler reports fusible sites
per kernel at build time (the boundary lint), with call-factor sites
marked fusible-fragile
(`core/backends/spirv.py`; `core/ir_contract.py`). The corpus-scale
audit behind this: 42,499 sites, zero dangerous-direction mismatches
between the lint's rules and gcc's behavior
(`tests/contraction/FORMULA_INVENTORY.md`). A kernel with no reported
sites, no transcendentals, and no reductions is CPU==GPU-bitwise by
construction; `tests/gpu_fallback_coil.ergo` is the standing witness
(f64 and f32).

**Alignment is worth 2×.** glibc malloc returns huge blocks at
mod-64 = 16, splitting every ymm access across a cache line; generated
code must 64-byte-align large buffers, and the ALLOCATABLE arena
already is (`Spec/Ergo_Hardware_Op_Map.md` §4;
`Spec/Arena_Lowering_Brief.md:137-157`). The arena itself is a 1 GiB
BSS bump with one compare-and-add per alloc and a no-op DEALLOCATE —
"no intrinsic ever allocates" is enforced structurally, not by
discipline.

**Walk-order is bandwidth.** The coalescing law, measured at 512³:
matching the walk to the storage order is a 20× bandwidth gap (520 GB/s
matched vs 26.5 GB/s mismatched; 16.5 ms vs 324 ms)
(`work/gpu_audit/coalesce_bench/results.txt`;
`Spec/Ergo_Spec.md` Part 2's column-major rationale cites the same
measurement). Register pressure has its own measured table: ≤32 regs =
100% occupancy, >64 = split the kernel
(`Spec/Ergo_Diagnostics_Design.md:518-527`), and integrator stability
is DT < 2/|λmax| (same doc:454). The VK allocation cost model —
cost(n) ≈ max(162 µs, 162 µs + 19 ns/B·n), crossover ~8 MB — predicts
galaxy_structured's 149 MB buffer within 9%
(`Testing/VK_ALLOC_COST_MODEL.md`).

**Minimalism as an integrity feature.** Sixteen operators, no array
expressions, strict left-to-right evaluation with no reassociation —
"the compiler lowers what you wrote, not what you meant"
(`Spec/Ergo_Spec.md` Part 7, Expression Evaluation Order). Every
allocation is visible; every op is auditable; the performance
constitution is that the language cannot accidentally become slow.

**RCT-style geometry.** The allocator family's layout constants are
derived from packing geometry, not tuned: the cuboctahedral 12-vertex
kissing number gives `SLAB_SBS_PER_WARP = 18 = LCM(1,2,3)×3`
(`Testing/PROJECT_THESIS.md:39`; `Testing/V8/aizawa_slab.cuh:93`), and
the Viviani/Hopf scatter curve `x = sinθ − ½sin3θ, z = cosθ·cos3θ`
(with `q = trunc(|z|·HOPFQ·31) mod 31`, HOPFQ = 1.97 measured
worst-case-optimal at `allocator/TUNING_FINDINGS.md` L3c) is the same
curve that runs the galaxy engine's 32-point LUTs
(`galaxy/galaxy_full.ergo.txt:82-101`). Power-of-two and
geometrically-derived constants dominate because tuned constants are
unauditable.

## 3. The integrity family

Seven allocator/verification cells plus the stream formats, all
certified under one seeded corruption harness. The math spine:

**Moment syndromes.** `S0 = Σb, S1 = Σb·i, S2 = Σb·i²` over frame
bytes; a single corrupted byte gives d = ΔS0, position p = ΔS1/d,
confirmed by ΔS2 = d·p² — locate AND restore, no replica
(`benchmark/ALLOCATOR_COMPARISON.md:346-349`). SQM inverts the same
machinery into write addressing: delta-moments of incoming-vs-journal
solve an exact integer Vandermonde for 1–2 changed bytes (Newton
identities; `benchmark/SQM_DESIGN.md:75-102`), with the u32-lane safety
proof 16×255·64³ ≈ 1.07e9 < 2³² (`SQM_DESIGN.md:55-71`). Binomial
half-moments come without a third pass: s1′ = g1 − H·s0, s2′ = g2 −
2H·g1 + H²·s0 (`SQM_DESIGN.md:95-98`).

**The blindness ladder is honest.** Four-point third-difference quads
(d, −3d, 3d, −d) are invisible to every 3-moment scheme (2000/2000);
s3 catches them 2000/2000; five-point pents (1, −4, 6, −4, 1) stay
blind. Each added moment pushes blindness one point out — the ladder is
mapped, not hidden (`benchmark/SQ5_CERTIFICATION.md:93-109`;
`SQM_DESIGN.md:61-67`). V22's fold misses bytes [144,152) entirely
(~5.3% invisible) and its unbalanced Viviani LUT silently rejects
14–16% of allocs at full fill (`ALLOCATOR_COMPARISON.md:323-335`).

**Counterflow journals.** SQ5's forward/backward accumulation per shell
plus the journal gives three residuals, and the classification table
routes journal-vs-payload corruption
(`benchmark/SQ5_CERTIFICATION.md:52-62`). Duplex mechanisms — complement
pairing b⊕0x55, per-strand self-syndromes, wholesale resynthesis,
apoptosis tombstones 0xDEAD5EED — are SQ2B's (`benchmark/SQ2B_DESIGN.md:11-20`).

**The SQF-H lane structure.** The GPU→CPU lazy handoff validates tiles
against an analytic journal by lock-in demodulation: I = Σw·cosθ,
Q = Σw·sinθ, δφ = atan2(I, Q) (sin-reference convention — atan2(Q, I)
was the 1284-phantom-slip bug, §5), residual = Σw² − 2(I²+Q²)/N, and
the five lanes LINEAR/SLIP/SHEAR/SPIKE/OVERFLOW route by what no
rotation can absorb (`benchmark/SQFH_DESIGN.md`). Overflow excess is
invertible through the clipper describing function M(A) = A·(2/π)·[asin
r + r√(1−r²)], r = A_env/A, bisected. Tested against a real
ergo-produced Schrödinger stream (`min/ab/schrod_2d_stream.ergo` →
`benchmark/bench_sqfh_ab.c`): the bare (scale, A, k, φ) journal fails
outright on a real packet (residual share 0.73–0.97 — envelope taper
and spreading chirp are not single-tone), and the model-M journal
(chirp c(T) = 2t_s/(σ0⁴+4t_s²), t_s = 2·AA·T; envelope σ(T) = σ0√(1 +
(T/320)²) — both closed-form from the sim's own PARAMETERs) restores
92.4% of center-packet tiles to tracked at ~336 ns/tile
(`benchmark/SQFH_DESIGN.md` §10 — the model-M derivation, the
per-tile-position residual table, and the measured cache/cost profile
are all there).

**Batching vs per-item.** ESF's 63-payload frames amortize the sweep:
43 ns/item vs 3 µs unbatched, 76× (`ALLOCATOR_COMPARISON.md:404-409`).
SQM's 1-byte update costs 1.00 rd/1.16 wr B vs 64 B full-copy, ~55×
traffic cut (`SQM_DESIGN.md:127-137`). SQW's memoized write-skip runs
0.36× SQ2B cost at 99% duplication with crossover at ~30–40%
(`SQW_DESIGN.md:69-81`) — and its dedup concentrates threat: 96.7%
repair vs 98.3%, ~1.9 logical items lost per tombstone, blast radius
growing with duplication (`SQW_DESIGN.md:83-99,133`; this is the
strand-overflow/tombstone failure mode).

**Latency over throughput, always.** Serial chains lose to parallel
math with ILP: CRC32C's ~1,017 chained instructions ≈ 3 µs/frame; a
byte-serial FNV recognition hash (152 dependent links ≈ 250 ns) made
SQW slower than the thing it was accelerating; per-sample cos/sin put
SQF-H at 1460 ns/tile until a Chebyshev rotation recurrence (two trig
calls per tile) brought 278
(`ALLOCATOR_COMPARISON.md:387-392`; `benchmark/SQW_DESIGN.md:56-64`;
`benchmark/SQFH_DESIGN.md` §3). The same rule fired again in the owned
kernels: transcendentals and serial chains on the hot path are the tax
that eats the design.

**Floors.** V8's warp-permanent slab allocator: 1.9 G allocs/s, 0.52
ns/alloc GPU-wide, 538–863× over cudaMalloc — and 1.05× the bare
per-lane atomic floor, i.e. the hardware atomic ceiling, not luck
(`Testing/V8_VS_V22_HEAD_TO_HEAD.md`; `COMPARISON_TABLE.md`). The
bump-floor normalization ("X× over the floor") is the standing
measurement discipline.

## 4. The physics solvers

**Imaginary-time propagation.** The staggered real/imag leapfrog
(I += a·lap(R), R -= a·lap(I)) with stability bound a ≤ 0.25 = 2/Lmax
for the 5-point Laplacian — a=0.24 stable, a=0.26 NaN, a sharp wall
(`min/ab/AB_FINDINGS.md:27`; `min/ab/schrod_2d.ergo`). Imaginary-time
grids converge as dx² (slope 0.116 Ha/bohr²), and a cell-center even-N
grid needs no soft-core — soft-core Coulomb was measured (+4.3e-2
shift) and rejected (`min/handshake/HANDSHAKE_FINDINGS.md` §1).
Imaginary-time also drives the Faddeev–Niemi Hopf-soliton relaxation
(`min/glueball/GLUEBALL_FINDINGS.md:69-97`).

**The quantum-chemistry ladder.** H₂⁺ parity handshake (D_e 0.10244 vs
0.10263 target, 0.2%) → grid full-CI with the Slater–Condon CSF
elements (⟨ii|jj⟩ = (ij|ij), ⟨ii|jk_S⟩ = √2(ij|ik), ⟨ij_S|kl_S⟩ =
(ik|jl)+(il|jk)) and the analytic Heitler–London ladder (D_e
46.9/47.7/67.4% of exact over 2/4/6 orbitals) → the Wigner-map
instrument (transverse-averaged W(z,p) = (1/π)∫dy′ e^{2ipy′}ρ(z−y′,
z+y′); midpoint oracle W(0,0) = ±1/π; full-Nyquist DFT makes ∫∫W = 1
exact) → the Dirac-Fock frozen-source eigensolver: ε is the root of
‖X(ε)‖ = 1 (normalization as Lagrange multiplier), variation of
parameters over a homogeneous pair with constant Wronskian, Sturm
ordering anchoring branch selection, and logical signbit tests only
because W0 ~ 1e180 overflows products (`min/wigner/DF_RADIAL2_FINDINGS.md:69-96`;
`min/handshake/H2_FINDINGS.md:29,56`;
`wigner_handshake_spec.md:11-22,128`). Certified against
Clementi–Roetti: He ×100 −2.861680242 (dev ~2e-7), Ne ×100
−128.5471256 (dev ~2.6e-5), with the relativistic deepening and the
correctly-ordered 2p fine split. The Dirac–Coulomb shooter underneath
matches the all-orders Sommerfeld formula to 3.8e-13…2.3e-11 Ha from H
to U⁹¹⁺, with the analytic small-r series start (F = r^s, G = q₀r^s,
s = √(κ²−(Zα)²)) handling the origin singularity exactly — never
clamped (`min/dirac/dirac_radial.ergo:15`; `min/dirac/ceiling.py:21-25`;
`DIRAC_FINDINGS.md`).

**DBM / Laplacian growth.** φ harmonic with cluster φ=0, outer φ=1,
growth p_i ∝ φ_i^η, SOR with ω = 2/(1+sin(π/N)) warm-started per
deposit, and the φ≥0 maximum-principle clamp that kills the NaN cascade
(§5). The η sweep is monotone: D = 2.001 (η=0, exact Eden) → 1.856
(0.5) → ~1.71 mean across η=1 seeds (literature window 1.60–1.75) →
1.462 (η=2). Tip-screening: strip roughness 59.2 rows vs 3.4 Eden
(17×), Gibbs–Thomson in the boundary condition (not the attachment
rule — the measured wrong-signed lesson), depletion self-limiting with
freeze exactly at mass=CAP. GPU Jacobi port (ω=1; the GS ω≈1.976 is
unstable under Jacobi) runs ~24× over CPU SOR, bitwise-deterministic
per seed+backend (`min/dendrite/DENDRITE_FINDINGS.md`;
`dbm_pack/dbm_mirror_*.json`).

**The ribosome MD engine.** Cα/C1′-bead Go-like dynamics with the
PHOS screened Coulomb E(D) = PHOS_EPS·exp(−D/PHOS_LAM)/D, breakable
cystine restraints, branchless dock gates as exact 0/1 masks (DOCKM =
(1 − SIGN(1, DOCK_FROM−FRAME))/2), the DD floor 1e-16 (f32-safe,
f64-bitwise-neutral), and adaptive substepping NSUB = min(64,
floor(SUBSTEP_D/DMIN)+1) with dampers rooted DAMP^(1/NSUB)
(`min/ribosome/RIBOSOME_FINDINGS.md:74-75,608-614,756-781`;
`min/protein/activity_bounds_section5.md:14-49`). The GPU restructure
(unified pair-slot engine, segmented reduction) was mirror-verified to
max force deviation 2.7e-20 and certified with a 3-seed GPU-vs-CPU
gate. Docking: 100% contact recovery on every gated set ever installed.
The rung-4 wall is the honest boundary: continuous RNA ≳180 nt does
not fold, measured and not chased
(`min/ribosome/RIBOSOME_FINAL.md`, `RIBOSOME_FINDINGS.md:873-898`).

**SQF-H wave handoff** is in §3 — it is solver-adjacent machinery:
the AB campaign's own oracles (v_group 0.1547, the spreading law)
became the handoff journal's model-M closed forms.

**The glueball/Hopf campaign.** MIT-bag levels E(R) = Ω/R + (4π/3)BR³
with cavity zeros x(TE₁) = 2.743707, x(TM₁) = 4.493409; flux-tube
prescriptions E² = 4πσn (Isgur–Paton) and the Arvis Casimir form; the
FN soliton at Q ≈ 0.97 held, E 236.5 vs ~241 published (−2%), virial
within ±3.4% — and the lattice topology barrier honestly documented:
grid flow doesn't conserve Hopf charge, Q slips, production stops
under-converged (`min/glueball/GLUEBALL_FINDINGS.md:22-120`). The atom
campaign: Fock(S³) → hydrogen → Balmer/NIST ratios to 7.9 ppm
(`min/atomhopf/ATOM_FINDINGS.md`).

**The galaxy engine and the straggler campaigns.** The 29M-particle
metabolic N-body sim on the Viviani spine runs the CLEAR→SCATTER→
STENCIL→PHYSICS pipeline at 6.948 ms/frame, 144 fps, ~259 GB/s = 77% of
the RTX 2060's 336 GB/s peak — bandwidth-bound, after the THETA
elimination (scatter 1.927→1.160 ms) and the merged phase-advance
(`galaxy/ARCHITECTURE.md:86-130`). Its spawn budget curve, its
speed-preserving steering (rotate toward the LUT tangent, rescale to
preserve |v|), and its signed-accumulator model ("zero is the skip
signal; the multiply by zero IS the skip", `structured/DESIGN.md:129-148`)
are the transferable pieces. The rotor-chain campaign measured c = 1
within 0.4% across N=12–48 by two methods with the Calabrese–Cardy
cross-check (`min/FINDINGS.md:124-247`); the trimer PME ring maps are
pixel-coincident with the trapping boundary (`min/trimer_map_check.md`);
the quaternion S³ winding identity holds to the f64 floor (~5e-13)
with the Berry-π flip exact (`min/quaternion/QUATERNION_FINDINGS.md:30-39`);
and the octonion battery's oracles (NORM 6.6e-16, Moufang 4.9e-15)
all matched (`min/octonion/oct_cd_battery.ergo:22-32`). The LLPS work's
white-bath pattern (SplitMix noise, variance-matched ×2.449=√6,
isolated constant-T blocks per run) is measured at
`min/condensate/white_check.md:9-96`.

## 5. The failure catalog

The rule of this section: each entry is what happened, why, and the
rule it produced. These are the project's real assets — the findings
docs are mostly failure autopsies.

- **The φ<0 NaN cascade** (dendrite). SOR ω→2 undershoots φ below 0 at
  the steep surface; φ^η is NaN for non-integer η; NaN then poisoned
  the MAXD convergence test, producing instant false "convergence" —
  growth dead while logs printed fake mass. Double failure: silent
  stall plus a lying flag. Rule: NaN in a convergence test is a
  first-class hazard for every iterative solver with a MAXD exit; and
  the φ≥0 clamp (maximum-principle projection) is now standard for any
  solver feeding non-integer powers
  (`min/dendrite/DENDRITE_FINDINGS.md` §4).
- **The silent SCANFAIL freeze** (df_radial). An ±8% rescan kept the
  cycle-1 energy on failure — the SCF looked converged. Fixed with loud
  SCANFAIL + a bounded widening ladder; the loud-failure semantics are
  now ratified compiler policy (`Spec/Hopf_Handshake_Bound_Policy.md`;
  `min/wigner/DF_RADIAL2_FINDINGS.md` §3).
- **Wronskian fake roots** (df_radial v1). A Wronskian of two
  particular solutions has source-amplitude-dependent artifact zeros;
  the Ne oscillation (−41.5 → −42.3) was artifact churn, and He passed
  only because source-free 1s is the one exact case. Rule: the detector
  must be normalization-as-root (‖X(ε)‖ = 1), and "passed for the wrong
  reason" is a failure mode with its own name now
  (`DF_RADIAL2_FINDINGS.md:56-67,132-137`).
- **df_radial never compiled.** The colon-bounds array `F(NR:NT,4)`
  was a parse error; its published Ne numbers were never physical.
  Rule: colon-bounds arrays must be a hard compile error
  (`DF_RADIAL2_FINDINGS.md:24-28,377-378`) — a language rule born from
  a non-physical publication.
- **The 1284 phantom slips** (SQF-H). δφ = atan2(Q, I) under a
  sin-reference lock-in measures π/2 − slip; the phase ledger adopted
  π/2, oscillated forever, and everything looked like enthusiastic slip
  detection. Fixed to atan2(I, Q); the derivation comment now lives in
  the code so the convention can't drift (`benchmark/SQFH_DESIGN.md`;
  `benchmark/sqfh_core.h` lock-in comment).
- **The V22 fold blind spot** [144,152): ~5.3% of bytes invisible; the
  shell-0-golden repair propagates corruption; 14–16% silent alloc
  rejection from an unbalanced LUT. Rule: blind classes are mapped in
  the certification, quantified, and printed
  (`benchmark/ALLOCATOR_COMPARISON.md:323-335`).
- **Serial-chain latency traps**, three times: CRC32C (1,017 chained
  instructions ≈ 3 µs/frame, loses to three independent AVX2
  accumulators), the FNV recognition hash (152 dependent multiplies ≈
  250 ns — SQW was slower than SQ2B at 77% skip), per-sample trig in
  SQF-H (1460 → 278 ns/tile via the recurrence). One rule
  (`benchmark/ALLOCATOR_COMPARISON.md:387-392`; `benchmark/SQW_DESIGN.md:56-64`).
- **The uncorrupted negative control** (work/ audits). A silent
  string-replace failure produced a fake PASS; the rule is
  cmp-the-control — diff the control against the pass arm, never trust
  a green control you didn't corrupt on purpose
  (`Spec/x86_Determinism_Audit.md` lineage; also the HHB NC3 fix: a
  too-narrow EGAP window let the corrupted control escape, fixed by a
  dissociation-limit recompute oracle, 345× divergence vs 0.01
  tolerance — `Spec/HHB_IMPLEMENTATION_PLAN.md:225-231`).
- **The dock-gate hoist** (ribosome GPU restructure). Four compiler
  bugs root-caused by verification, not by staring: stale-upload
  hoisting, an extractor hole that wrote BSS zeros over position arrays
  (`IRWhileLoop` extraction), f32 pad-slot NaN (8e-60 underflow → 0/0),
  and an f64 GPU path that had never compiled. The regression test is
  `tests/gpu_fallback_coil.ergo`
  (`min/ribosome/RIBOSOME_PRECISION_SWEEP.md:108-118`;
  `min/ribosome/ERGO_FIX_FIRST_LIST.md` A1–B2).
- **The f32 driver Sqrt.** The RTX 2060's GLSL.std.450 Sqrt is 1 ulp
  off at f32 (measured, `Spec/Ergo_Spec.md` Part 9.10 driver notes) —
  a driver-precision class that lives in the never-bitwise list.
- **DMRG false topological protection.** "10⁻²⁴ variance" was an
  under-converged state 0.011 above ground at 99.995% overlap — the
  missing 0.005% carried the entire observable, and the h=0 control
  reproduced it (symmetry-sector attractor at N≡0 mod 4). Rule: the
  energy referee protocol and the ED calibration gate govern all DMRG
  (`min/FINDINGS.md:307-344`).
- **The crossed sin-link terms** (AB campaign). The one real
  implementation bug diluted the AB coupling ~40×; the gauge oracle
  passes under both schemes — only the uniform-β velocity test caught
  it. Rule: a gauge-null test alone is insufficient; pair it with a
  velocity test sensitive to the curl part (`min/ab/AB_FINDINGS.md:64-74`).
- **The 32-bit PRNG conditional bias.** Hand-rolled integer hashes wrap
  early and bias conditioned variates (rotor channel selection: mean
  0.22 vs 0.5). Rule: splitmix64 finalizer at 64-bit width, owned, both
  backends (`Spec/Ergo_Intrinsic_Signatures_Complete.md`, RNG section;
  `min/FINDINGS.md:491-500`; the condensate Knuth-xor autocorrelation
  failure at `min/condensate/white_check.md:21-45`).
- **The HB_CAP=0 confound.** A gate `DEG_I < HB_CAP` silently disabled
  H-bonds for an entire campaign. Rule: gates get reachability audits
  (is your event criterion reachable?) — the same audit class as the
  galaxy dead threshold below the COAST plateau
  (`min/protein/MULTIDOMAIN_FINDINGS.md` §20–§21;
  `structured/sig_baselines/README.md:6-15`).
- **The Kabsch erratum.** A hand-rolled Kabsch returned the wrong
  eigenvector on subsets and inverted the uL18-tail conclusion.
  Replaced by the cyclic Jacobi quaternion eigensolver, certified
  (`min/ribosome/RIBOSOME_FINDINGS.md:1185-1202`).
- **NVVM was a dead end; malloc-backed ALLOCATE was dead code; `-O0`
  was the default until the audit.** The largest single performance
  finding was a default (`Spec/Ergo_GPU_Roadmap.md`;
  `Spec/x86_Determinism_Audit.md` Finding A).
- **Fabricated-report errors caught by measurement.** The condensate
  tc report had ATT_K mislabeled and a sed probe that never matched;
  the white-bath task named them by measuring (MSD exponent 0.00 →
  1.21) (`min/condensate/condensate_tc_check.md:115-139`). Rule:
  reports are regenerated from runs, never edited.

## 6. Process patterns

The discipline that makes the rest possible:

**Oracle-first design.** Oracles are written before the engine: the
annulus Laplace solver was certified before any DBM growth ran
(`min/dendrite/DENDRITE_FINDINGS.md` §2); the quantum-chemistry ladder
certified each stage before building the next. Interior-fit oracles
(2-parameter log fits, not boundary-referenced analytics) handle
staircase-boundary PDE validation generally.

**Engine-vs-mirror certification.** Independent mirrors (numpy) certify
engines to byte-exact or measured-agreement: df_radial2's
mirror↔engine↔Clementi–Roetti three-way agreement closed its
certification at 8.5e-9 (`min/wigner/DF_RADIAL2_FINDINGS.md`); SQ5's
mirror diff is 0 (`benchmark/SQ5_CERTIFICATION.md:71-83`); the Wigner
mirror caught the mirror's own failure (2×1s LCAO fails 2σ below R≈2 —
the engine caught the mirror, not vice versa). The mirror is not the
reference; it's the second suspect.

**Negative controls with corruption-presence gates.** A control that
wasn't corrupted on purpose isn't a control (§5). The HHB ladder runs 5
positive rungs PASS + 3 negative controls TRIP
(`Spec/HHB_IMPLEMENTATION_PLAN.md:205-236`).

**Ranked-suspect debugging.** The stag5 "hang" was triaged by one
discriminating CPU observation (88% CPU, state R → host-busy, not
fence-idle) eliminating device theories, then root-caused to three
codegen bugs (`work/compiler_regression_ul18_stag5_hang.md`).

**Certification ladders and the loud-failure rule.** Pre-registered
oracles, staged rungs, documented exclusions, and failure that aborts
loudly (HHB_SCANFAIL with actual/expected/tol, exit 1) rather than
keeping the old value (`Spec/Ergo_Spec.md` Part 11.5).

**Fixed-point discipline with a measured floor.** The galaxy engine's
15-bit phase quantization was binary-search certified; <14 bits
destabilizes the mode-switching feedback (`galaxy/ARCHITECTURE.md:76-80`).
Quantization is a measured decision, not an aesthetic one.

**Epistemic audits.** Two cheap checks recur: the threshold-vs-plateau
audit (is your event criterion reachable? — the galaxy crystal
threshold 0.008 sat below the COAST plateau 0.0367, so no particle
could ever crystallize and the SIG buffers stayed empty,
`structured/sig_baselines/README.md:6-15`), and the frozen-derived-quantity
audit (GEN at death ≠ GEN at seed — the "GEN=1 monopoly" that three
external AIs theorized about was an architectural bias, not substrate
physics, `structured/sig_baselines/README.md:263-309`). And the seed-direction
regression: a seeding commit silently collapsed crystal diversity, so
the "flat substrate" finding was an artifact (README:144-159). Rule:
audit the instrument before theorizing the signal. A documentation one
too: docs cited `mcl/driver.py` while the code moved to
`core/driver.py` — cite-then-verify applies to paths, not just numbers.

## 7. The reuse map

What transferred across domains, per the surveys and the tree:

- **The splitmix64 PRNG** (owned 64-bit finalizer): rotor batteries →
  condensate white bath → qbattery → DBM roulette → ribosome thermal
  kicks. One generator, both backends, conditional validation per use.
- **The Pauli-master-equation idiom**: trimer (Li/Pokorný) → MOF
  mixed-valence → graphene transfer rates (`min/` surveys).
- **The masked two-buffer stencil + cosine sponge**: FDTD → the AB
  Schrödinger engines → DBM SOR (`min/fdtd/FDTD_FINDINGS.md`;
  `min/ab/AB_FINDINGS.md:96-97`).
- **Byte-identical gates**: from the x86 determinism audit through
  every campaign's rerun checks; `ERGO_HASH_FINAL` state hashing is the
  standard regression mechanism (`Spec/Ergo_Spec.md` Part 7).
- **Stage-4 packed sweeps and isolated constant-T blocks**: pmargin →
  condensate → ribosome campaign arms.
- **The cyclic Jacobi eigensolver**: m0's 4D Viviani ED → protein RMSD
  (`min/protein/MULTIDOMAIN_FINDINGS.md` §10).
- **Cumulative-Poisson Y^k SCF structure**: the helium engine →
  hf_radial → the Wigner/heteronuclear handshakes.
- **The kernel-side extraction conservatism**: "if not affine, it's
  SCATTER, no heroics" (`galaxy/DRAFT_index_analysis.md:48-96`), with
  the backward data-flow walk (`_traces_to_loop_var`) that fixed the
  `_idx*` prefix-match data-race near-miss.
- **SQF-H's analytic-prior + lock-in + episode protocol** is
  transport-integrity machinery applicable to any GPU→CPU sim stream;
  its journal closed forms came from the AB campaign's certified
  oracles.
- **HHB handshake verification** (bounded schedules, signbit-only sign
  detection, loud SCANFAIL) went from the Wigner campaign's failures
  into the language (Spec Part 11) and back out to the ribosome field
  tests.

## 8. Index of artifacts

By domain; each entry is experiments → finding doc.

- **AB / wave engines**: `min/ab/` (stage0_null, schrod_2d,
  ab_fluxline, ab_lens, schrod_2d_stream) → `min/ab/AB_FINDINGS.md`;
  SQF-H handoff → `benchmark/SQFH_DESIGN.md`.
- **Allocators, early generations**: `Testing/V8,V9,V16,V22,GEO`,
  `baseline_*`, `allocator/sq2core.f/sq4core.f` →
  `Testing/PROJECT_THESIS.md`, `allocator/TUNING_FINDINGS.md`.
- **Allocators, benchmark family**: `benchmark/` (SQ4/SQ5/SQ2B/SQW/SQM/
  SQF-H/ESF) → `benchmark/ALLOCATOR_COMPARISON.md` + per-design MDs +
  certification docs.
- **DBM/dendrite**: `min/dendrite/`, `dbm_pack/` →
  `min/dendrite/DENDRITE_FINDINGS.md`, mirror JSONs.
- **Dirac/Dirac-Fock**: `min/dirac/`, `min/diracfock/`,
  `min/wigner/df_radial2.ergo` → `DIRAC_FINDINGS.md`,
  `min/wigner/DF_RADIAL2_FINDINGS.md`.
- **FDTD**: `min/fdtd/` → `min/fdtd/FDTD_FINDINGS.md`, `weber_check.md`.
- **Galaxy/structured**: `galaxy/galaxy_full.ergo`, `structured/` →
  `galaxy/ARCHITECTURE.md`, `structured/DESIGN.md`,
  `structured/sig_baselines/README.md`.
- **Glueball/atoms**: `min/glueball/`, `min/atomhopf/` →
  `GLUEBALL_FINDINGS.md`, `ATOM_FINDINGS.md`.
- **Handshake/Wigner chemistry**: `min/handshake/`, `min/wigner/` →
  `HANDSHAKE_FINDINGS.md`, `H2_FINDINGS.md`, `wigner_handshake_spec.md`.
- **LLPS/condensate**: `min/condensate/` → `condensate_check.md`,
  `white_check.md`.
- **Octonion/Viviani geometry**: `min/octonion/`, `96/`,
  `spectral tool/`, `min/m0/` → `min/FINDINGS.md`,
  `VIVIANI_DEBUG_NOTES.md`.
- **Proteins**: `Protein_Margin/`, `min/protein/`, `min/pmargin/` →
  ALGORITHM/SCALING/TRANSFERABILITY/CLINICAL docs,
  `MULTIDOMAIN_FINDINGS.md`, `PROINSULIN_MIDY_REPORT.md`.
- **Ribosome**: `min/ribosome/` → `RIBOSOME_PLAN/FINDINGS/FINAL.md`,
  `CODON_FINDINGS.md`, `RIBOSOME_PRECISION_SWEEP.md`.
- **Rotor-chain and stragglers**: `min/` rest → `min/FINDINGS.md`,
  per-folder checks.
- **Compiler/engine**: `Spec/x86_Determinism_Audit.md`,
  `Spec/Arena_Lowering_Brief.md`, `Spec/Ergo_Hardware_Op_Map.md`,
  `tests/math_kernels/`, `tests/contraction/`, `Spec/HHB_*.md`.

## 9. What this adds up to

The honest claim: Ergo is a deterministic simulation substrate whose
guarantees are measured, not asserted. The compiler's numerics are
owned down to the last ulp (fixed-coefficient kernels, compiler-owned
contraction, pinned recipes); the physics engines are certified by
oracle ladders and independent mirrors; and the failure catalog is the
proof the certification works — every documented blind spot was found
by an instrument, not by inspection, and each one is now a rule. The
system's credibility rests on the fact that its negative results are
recorded with the same precision as its positive ones.

The known boundaries are written down where they live: the rung-4 RNA
wall, the lattice topology barrier for Hopf charge, the CPU≠GPU
transcendental and staged-reduction classes, the blindness ladder's
next rung, and the corpus baselines awaiting their re-certification
decision. Nothing in this document should be believed beyond what its
citations support.
