# FORMIN_LAW.md — φ4.7 formin-brush vs branched-brush (R2) certification

Certified: 2026-09-02. Engine lineage: pop_fpt.ergo (φ4) → brush_c400g →
brush_br400 → brush_bra (S4 anchored branching) → brush_bra_x → brush_bra_r
(hold-release piston) → **brush_bfm** (per-filament formin channel). Oracle:
`plan_formin.md` (O-F1..O-F7), registered before engine build and ensemble.
Method: sequential lock-step, no swarm; gates before smokes, smokes before
ensembles; all durable artifacts under `/mnt/agents/output/actin_phasespace/`.
Runs: `runs19/` (26-run ensemble, 1M steps each). Analysis is reproduced by
`runs19/stage_f_analysis.py`; output: `runs19/stage_f_analysis.out`.

## The question

R5 certified the stochastic dendritic brush: S4 branching multiplies
membrane-proximal tips, gives n_eng = 3.38-3.83 at ordinary loads, recruits
n_eng → 5.9 under compression, and stalls at F* ≈ 12. F2 certified the
opposite elemental architecture: one processive slip-grip formin filament is
a power-stroke ratchet, has load-flat insertion to F=4, and is individually
unstallable by membrane pressure in the certified range.

**R2 asks what happens when those mechanisms are put in the same brush.**

| arm | branching PBR | formin FORMIN | interpretation |
|-----|---:|---:|---|
| A | 1 | 0 | stochastic branched brush; completed in runs17/runs18 |
| B | 0 | 1 | pure processive brush; this rung |
| C | 1 | 1 | hybrid processive + branched brush; this rung |

## Mechanism as certified

The formin element is a per-filament port of the F2-certified slip-grip
tether:

- `GRIPF(F)=0→1` when the barbed tip enters the grasp ring `PX > XP−RGRIP`.
- At grip, the yz anchor is latched; the yz force is a two-sided spring,
  capped at `FMAXT`.
- The x force is one-sided compression-only against `XP−S0F`, capped at
  `FMAXT`; its reaction is added to the piston force.
- A tether slips when its 3D stretch exceeds `SMAXF`.
- While gripped, the tip axis relaxes toward +x at rate `KORI`.
- The channel draws no random numbers, so FORMIN=0 is gate-inert.

The direct F2 geometry failed at brush density (Amendment F-1 in
`plan_formin.md`): S0F=1.25 parked tethered tips outside the contact window
and RGRIP=1.0 reached too few tips. The certified brush geometry is
**S0F=0.75, RGRIP=2.5**, with KF=2.0, FMAXT=5.0, SMAXF=2.0, KORI=1.0
unchanged.

## Certification chain

1. **O-F1 engine gates passed.** `brush_bfm(FORMIN=0,PBR=1)` ≡ `brush_bra`
   and `brush_bfm(FORMIN=0,PBR=0)` ≡ `brush_bra_b0`, both 0-diff over 300k
   steps. Ghost scans were clean.
2. **Amended smoke passed.** At F=1 the formin brush held the plane, had
   grip 5.4/23 = 0.24, exact monomer conservation, and no ghost filaments.
3. **Law grid completed.** Arms B and C at F∈{0,1,4} × two seeds = 12 runs,
   clamped piston, stationary window t>500k.
4. **Stall grid completed.** Hold-release PREL=300k. Arm B at
   F∈{4,8,12,16,20}; arm C at F∈{12,20}; two seeds each = 14 runs,
   stationary post-release window t>400k.
5. **Infrastructure verification passed.** `runner21.sh` streamed to /tmp,
   verified exit/FINAL/NUL=0, copied to /mnt, and re-verified. All 26 logs
   have FINAL, no NUL bytes, and 2000 census blocks.
6. **O-F7 verification passed.** 26/26 runs: exact census conservation,
   filament-length/census agreement, zero gm-state ghost mismatches,
   N_f ≤ MAXF, complete 1M-step trajectories.

## R2 laws

### L-F2.1 Processive grip scales in count, not in brush engagement

The slip-grip channel is active and in its registered processivity band.
For arm B:

| F | n_eng | gripped tips | grip fraction | mean force |
|---:|---:|---:|---:|---:|
| 0 | 1.46-1.49 | 5.09-5.40 | 0.24-0.27 | 2.09-2.13 |
| 1 | 1.56-1.70 | 5.41-5.44 | 0.25-0.28 | 2.08-2.23 |
| 4 | 2.51-2.51 | 7.46-7.94 | 0.35-0.36 | 4.02-4.04 |

But gripped does not mean membrane-engaged: the x tether is one-sided, so a
gripped tip may sit anywhere behind the plane until it is compressed. The
tether therefore does not multiply the number of contact-bearing tips. Arm B
engagement remains in the unbranched class, not the branched class.

### L-F2.2 The formin channel is law-neutral for ordinary brush contact

At clamped loads F≤4, arm B is quantitatively close to the unbranched
reference: n_eng ≈ 1.5-2.5, P(bare) ≤ 0.033, and force balance ≈ the
unbranched brush. Formin tethering does not replace branching as the
engagement mechanism.

The structural difference is length, not contact: arm B carries
n̄ = 15.6-19.0 monomers versus 11.7-12.2 in the hybrid/branched class. The
processive slip-grip keeps some tips growing and produces occasional long
tethered rods (FINAL lenfil 24-68 in the F=1 law runs), but most load still
comes from the short untethered brush population.

### L-F2.3 Arm B stalls at F* ≈ 14-16 by recruitment saturation, not slip or crush

Post-release force margins for arm B:

| load F | margins, two seeds | n_eng | grip | verdict |
|---:|---|---:|---:|---|
| 4 | +0.04, +0.06 | 2.50-2.59 | 7.48-8.25 | holds |
| 8 | +0.03, +0.03 | 3.58-3.75 | 10.79-11.83 | holds |
| 12 | +0.02, +0.03 | 4.68-4.82 | 13.20-14.83 | holds |
| 16 | −0.02, −0.07 | 5.72-5.94 | 14.02-15.56 | zero crossing |
| 20 | −0.15, −0.96 | 6.88-7.04 | 13.06-17.14 | above stall |

Thus **F_s(B) is bracketed at 14-16** (positive at 12, negative at 16),
inside the registered O-F5 window [6,30]. It is roughly 5× the certified
unbranched stall 2.5-3 and slightly above the branched stall ≈12.

The mechanism discriminator is unambiguous:

- **not slip stall:** grip does not go to zero; it rises from ≈7.5 at F=4
  to ≈14-17 at F=20;
- **not crush stall:** n̄ does not fall to the floor; it stays ≈15-20 and
  rises to 23 in the most compressed seed;
- **recruitment-limited stall:** n_eng rises 2.5 → 7.0 as compression pulls
  more tips into the contact zone, while the plane remains essentially off
  the protective clamps until the highest load. The stall occurs when this
  recruitment can no longer add load-bearing tips fast enough.

This is the branched brush's load-adaptive signature, now produced by
tether-mediated recruitment instead of branch-mediated tip multiplication.

### L-F2.4 Branching and formin are synergistic above either component's stall

Arm C remains force-balanced at F=20:

| load F | margins, two seeds | n_eng | grip | n̄ |
|---:|---|---:|---:|---:|
| 12 | +0.06, +0.11 | 5.40-5.57 | 17.64-17.66 | 11.4 |
| 20 | +0.01, +0.01 | 6.81-7.30 | 21.60-23.97 | 11.2-11.3 |

So **F_s(C)>20** on this grid. Branching supplies a dense, ceiling-pinned
short-filament mesh; the formin channel grips most of that mesh under
compression. The hybrid is not merely additive: at F=20 it holds a load
above both the branched-only stall (≈12) and the processive-only bracket
(≈14-16), with zero lower-clamp occupancy and no filament-length collapse.

### L-F2.5 Processivity alone does not polarize the brush

Arm B orientation is isotropic at every measured load: mean |a·x̂| =
0.491-0.502, statistically the same 60°-class mesh as the stochastic brush.
The KORI=1 threading torque acts only on the gripped subpopulation
(≈25-36% in the clamped law grid) and is too weak, or too intermittent, to
orient the standing brush.

The composite O-F6 structure prediction therefore splits:

- processive length component: **confirmed** (n̄ = 15.6-19.0 ≥ 15);
- polarization component: **falsified** (0.50 < 0.65).

### L-F2.6 The single-filament power-stroke signature is diluted in a brush

The F2 single-filament discriminator was near-zero blocked inserts per
gripped tip. In arm B, stationary event-window blk:bind ratios are
1.57-5.61 globally and **0.29-0.71 per gripped tip**, above the registered
O-F4 bar <0.2.

Interpretation: the processive spring still retracts gripped tips after
insertion, but only a minority of filaments is gripped at ordinary loads.
The ungripped majority continues to make ordinary stochastic blocked
attempts, so the brush-level register does not inherit the F2 power-stroke
signature. Arm C has lower per-grip ratios (0.19-0.27) because branching
raises the gripped denominator, but its global blk:bind remains 2.32-3.63,
not near zero.

## Stationary law-grid summary

Stationary window t>500k, two seeds per cell:

| arm | F | n_eng | grip | grip fraction | mean abs(a·x̂) | n̄ | lifetime | blk:bind | blk:bind/grip |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B | 0 | 1.46-1.49 | 5.09-5.40 | 0.24-0.27 | 0.499-0.500 | 16.1-19.0 | 39.1-39.7k | 1.57-2.41 | 0.29-0.47 |
| B | 1 | 1.56-1.70 | 5.41-5.44 | 0.25-0.28 | 0.501-0.502 | 16.5-18.7 | 43.0-53.8k | 2.37-3.16 | 0.44-0.58 |
| B | 4 | 2.51 | 7.46-7.94 | 0.35-0.36 | 0.491-0.496 | 15.6-17.2 | 41.2-50.1k | 4.83-5.61 | 0.65-0.71 |
| C | 0 | 3.42-3.47 | 12.34-12.55 | 0.40-0.41 | 0.500-0.503 | 11.7-11.9 | 37.7-37.9k | 2.32-2.94 | 0.19-0.23 |
| C | 1 | 2.99-3.76 | 11.52-13.06 | 0.37-0.43 | 0.501-0.504 | 11.8-12.2 | 35.8-40.6k | 2.56-2.75 | 0.20-0.24 |
| C | 4 | 3.82-3.95 | 13.31-13.32 | 0.43 | 0.503-0.506 | 11.7 | 35.3-43.0k | 3.02-3.63 | 0.23-0.27 |

## Oracle scorecard

| oracle | registered criterion | measured result | verdict |
|---|---|---|---|
| O-F1 gates | FORMIN=0 ≡ both certified parents, 0 diffs; ghost scan clean | both gates 0-diff over 300k; ghosts 0 | **PASS** |
| O-F2 processivity | grip fraction ∈ [0.2,0.6] at F=1 | 0.25-0.28 | **PASS** |
| O-F3 engagement | arm B n_eng ≥ 3.48 at F=1 | 1.56-1.70 | **FAIL — measured result** |
| O-F4 force class | per-gripped-tip blk:bind <0.2 at all loads | arm B 0.29-0.71 | **FAIL — measured result** |
| O-F5 stall | F_s(B) ∈ [6,30]; classify slip/crush/recruitment | F_s(B) ≈14-16; recruitment-limited | **PASS** |
| O-F6 structure | arm B mean abs(a·x̂) ≥0.65 and n̄ ≥15 | orientation 0.491-0.502; n̄ 15.6-19.0 | **FAIL as composite; length subcriterion passes** |
| O-F7 stability | exact conservation, ghost scan 0, N_f≤MAXF, full 1M completion | 26/26 clean | **PASS** |

## Verification note

The first O-F7 scanner version treated `ndim` as a monomer count rather than
a dimer count and falsely reported conservation failures. The corrected
identity, now encoded in `stage_f_analysis.py`, is:

```text
nbound + nfree + 2*ndim = 400
gm state counts = (nbound, nfree, 2*ndim)
```

With that correction, all 26 ensemble logs verify exactly at all 2000 census
blocks per run.

## Conclusions for the phase-space map

1. **Branching is the engagement mechanism; formin is not.** A processive
   tether holds a subset of tips but does not create membrane-proximal tips.
2. **Processivity buys stall, not orientation.** Arm B raises stall from
   2.5-3 to ≈14-16 while remaining orientationally isotropic.
3. **The high-load architecture is hybrid.** Branching supplies tip density;
   formin supplies processive load paths. Together they hold F=20, above
   either mechanism alone.
4. **Single-filament force class does not automatically scale.** The F2
   power-stroke signature is diluted by the untethered brush population;
   brush-level force class must be measured per gripped tip, not inferred
   from the isolated element.

## Open items

- Stage D amendments B-1/B-2/B-3 were ratified on 2026-09-02 and are now recorded in `plan_branch.md` and `BRANCH_LAW.md`.
- A finer stall bracket for arm B (F=13,14,15) would localize F_s(B), but
  is not needed for O-F5 because the measured 12/16 bracket already sits in
  the registered window and identifies the mechanism.
- If polarization is biologically load-bearing, test stronger KORI or a
  two-sided/formin-anchor geometry as a new pre-registered amendment; the
  certified KORI=1 channel does not polarize the brush.
- If brush-level power-stroke dominance is desired, increase the gripped
  fraction rather than changing the single-filament tether chemistry.
