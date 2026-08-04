# Squaragon allocator tuning audit — findings

Scope: `allocator/sq2core.f` (F77 reference), `tests/sq3core.ergo` (Ergo port),
`Testing/V22/` (production cross-reference, read-only). Audit only — no
allocator constants were changed. Reproduce from repo root:

```
python allocator/gen_tuning_relax.py   # emits allocator/tuning_relax.ergo
python allocator/tuning_check.py       # L1 + L2 + L3, all drivers
```

Determinism: every driver (C, F77, Ergo, L2 relax) run twice per audit,
byte-identical; the audit script itself run twice, byte-identical report.
Cross-port runtime: F77 / Ergo / independent Python model agree exactly on
TTOTAL=192, ZONE=1, state HASH=-1975039029 (400 fast allocs), and the F77
SQ2SCT sequence equals the design LUT repeated.

## Level 1 — static LUT self-consistency

Every baked table regenerates from the analytic definition in
`Testing/V22/squaragon_v2.h` and matches the compiled production C driver
output. Nothing is orphaned.

| table | generator | verdict |
|---|---|---|
| SCATLT (32) | `sq2_viviani_scatter_full(id, 32)`, HOPFQ=1.97, f32 | exact-match (both ports + production) |
| FLOWW (32) | `w(θ)=sin3θ/3+sin9θ/9+sin27θ/27`, θ=2πi/32 | exact-match (baked = production f32 `sinf` to all 6 decimals; naive f64 recompute differs by ≤4.9e-7) |
| FLOWM (32) | `\|w\|>0.30→2, >0.22→1, else 0` | exact-match — **but the header comment says ACTIVE is 0.15–0.30 while the code branches on 0.22**; the LUT follows the code |
| SOLTON (32) | `\|w\|>0.30` | exact-match (identical to FLOWM==2 mask) |
| BINGEO (8) | `trunc(\|viviani_z(2πb/8)\|·255)` → 228/104/0/104 repeating | exact-match |
| SEED (12×3) | exact unit cuboctahedron (±1/√2) | exact-match, 0.0 error |

Notes:
- SCATLT's period-16×2 structure is a symmetry of the generator
  (`|x|`, `z` invariant under θ→θ+π), not a copy-paste artifact.
- Two bake sites sit exactly on truncation boundaries (id=0: xc4=0.0;
  id=8: proj8=0.0, xc4=6.0) — held by exact float symmetry of sinf/cosf
  at multiples of π/2. Stable in practice, fragile by construction.
- FLOWW's asymmetric pair (idx 5: 0.163085 vs idx 11: 0.163086) is
  faithful f32 `sinf` rounding, present identically in the V22 header.

## Level 2 — geodesy (action deficit)

Metric (documented, sensitivity-checked): 8-bin × 32-ring torus graph;
ring step `WR(r)=1+(|FLOWW[r]|+|FLOWW[r+1]|)/2`, bin step `WB=SCLRAT=27/16`;
all-pairs geodesic distances by Dijkstra in `tuning_relax.ergo`
(cross-checked against a Python replica, max abs diff 1.2e-6 over the
65536-entry matrix); walk action = collision energy `E=Σ 1/(1+d)`.

Measured (Ergo binary, deterministic):

- design walk: **E = 5.103851** (DSUM = 169.82)
- swap-descent from design: **E = 3.308874** (converged sweep 4) —
  improving single swaps exist *from the design itself*
- best of 16 random-init descents: E = 3.279905
- **deficit ≈ 35%**, robust across all 16 metric variants
  (γ ∈ {0,0.5,1,2} × WB ∈ {1, 27/16, φ, 2}: deficit 33.5–39.8%)
- 100 random single-swap perturbations: **50 rose, 35 fell**, 15 unchanged
  (ΔE mean +0.166, range −0.387..+1.142)

The plan's tuning claim (deficit ≈ 0, perturbations rise) is **refuted**
for this metric family. Retune candidate (relaxed sequence, same bin
multiset): `2 6 2 6 2 6 2 6 3 6 4 2 4 2 7 4 0 4 0 4 7 4 7 4 3 7 3 6 0 4 0 3`.
Caveat: see L3a — the design wins on *worst-case* separation while losing
on energy; the two objectives diverge, and the design reads as max-min
tuned, not energy tuned.

## Level 3 — runtime properties

**L3a — adjacent-ID separation (512-ID stream, torus distance):**
design min=2.819, p5=5.063, mean=11.728.
- vs 100 random same-multiset LUTs: **all 100 worse on min**
  (range 1.132–1.252); 92 worse on mean, 8 better.
- vs 100 single-swap perturbations: 64 worse on min, **1 marginally
  better (2.917)** — design is near-dominant, not strictly optimal.
The Hopf-ergodicity collision claim **holds** at worst-case level.

**L3b — bin loads:** per 32-ID period the design histogram is
`{0:4, 2:6, 3:4, 4:8, 6:6, 7:4}` — **bins 1 and 5 are never used**,
loads ratio 4:6:8. Rolling-window max-min spread (32/128/512 IDs):
8/32/128, worse than uniform-random-8-bin LUTs (means 5.5/23/77).
Temporal variation is zero (periodic). The scatter is equidistributed
over *6 of 8* bins only.

**Capacity consequence (measured, F77 driver):** 6 active bins × 32 ring
= 192 max occupancy shell-1; after SQ2REP TTOTAL=384 = THRESHOLD_BIAS
*exactly*; THRESHOLD_WORKING=432 and THRESHOLD_MAX=496 are **unreachable**
— zones OVERDRIVE/DIVIDE are dead states. The thresholds are calibrated
for 8×32×2=512, i.e. they assume an 8-bin scatter the baked LUT does not
deliver.

**L3c — constant usage map (traced through SQ2INI/SQ2FLD/gate ops +
sweeps):**

| constant | bites the alloc path? | measured verdict |
|---|---|---|
| SCLRAT=27/16 | no — only in SQ2SCL, which SQ2ALC/SQ2FAL never call (alloc hardcodes SCALE=1.0); V22 shell-1 strands are copy-only | **inert** |
| BIAS=0.75 | no — only in `sq2_inefficiency = residual*bias` with residual ≡ 0; declared-but-unreferenced (BIASV) in F77 | **inert** |
| HOPFQ=1.97 | only via SCATLT *generation*; LUT fast paths never see it | **load-bearing & at optimum**: ±20% sweep — 1.97 has the best worst-case separation (min 2.82 vs ≤1.69 at 8 other swept values); not mean-optimal (11.73 vs best 13.39 @1.77); unused-bin count (2) not optimal (1 @1.87/2.27/2.36) |
| SEMSTR=0.03 | via round(64·s)=2 seam-shift bits in SQ3FAL | **inert in band**: constant 2 across ±20%; flips only at −22%/+30% |

**L3d — triple-XOR residual (production V22 header, C driver):**
unperturbed: shortcut and full both exactly 0.
Per-vertex ε=1e-3 response: along z: 3.000e-3 (all 12 vertices);
along x or y: ≤5.96e-8 (float noise floor). The residual is exactly
`3·|z-centroid|/scale` — **blind to any in-plane perturbation** and to
any perturbation set with zero z-sum. 100 random-direction perturbations:
all detected (min residual 2.17e-5). The V22 data imprint perturbs .x and
.y of two vertices (invisible) and .z of one (visible): **2/3 of the
imprint channel is undetectable by this metric**. The thesis's
"implementation collapses to a constant" claim is true but the
corruption-detection claim holds only for z-directed corruption.
The F77 port has no residual routine at all.

## Verdict summary

| item | verdict |
|---|---|
| SCATLT | load-bearing; worst-case near-optimal (L3a), energy-suboptimal (L2, retune candidate above); uses 6/8 bins |
| FLOWW / FLOWM / SOLTON | exact-match; **inert at runtime** (SQ2FLW/SQ2FLM/SQ2SOL have no callers in the alloc path); FLOWM header comment wrong (0.15 vs 0.22) |
| BINGEO | exact-match; load-bearing (invariant geo byte) |
| SEED | exact-match; load-bearing |
| SCLRAT | inert in alloc path |
| BIAS | inert |
| HOPFQ=1.97 | load-bearing via LUT generation; measured at the worst-case optimum — the suspect constant is actually tuned |
| SEMSTR=0.03 | inert in ±20% band |
| THBIAS/THWORK/THMAX=384/432/496 | load-bearing but miscalibrated for the 6-bin LUT: 432/496 unreachable, DIVIDE a dead state |
| triple-XOR residual | detection claim partially false (in-plane blind); F77 port lacks it |

## Surprises

1. **Bins 1 and 5 are never scattered to** — a property of baking
   `sq2_viviani_scatter_full(id, total=32)`; the generator emits 1/5 for
   other totals. Capacity drops 512→384 and two of four zone thresholds
   become dead states.
2. **The design LUT is 35% off the collision-energy optimum** yet
   dominates 100/100 random LUTs on worst-case separation — it is max-min
   tuned, not energy tuned.
3. **HOPFQ=1.97 is not folklore**: it sits at the measured worst-case
   optimum of the sweep.
4. The triple-XOR residual — the thesis's flagship "algebraically zero"
   metric — cannot see 2/3 of the perturbation channels the allocator
   actually writes.
