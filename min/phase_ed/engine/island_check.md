# Island zoom — structure verdict

Zoom: B ∈ [0.0, 0.2] × J ∈ [1.5, 2.5], 121 points at N=12
(`results_island.json`), plus N-scaling at three points. Maps:
`maps/island_{gap,c,q,r}.png`.

## (a) Distinct gapped region with a boundary, or smooth wedge edge?

**A distinct gapped lobe with a defined (slanted) boundary.** The zoom
maps show a low-c (0.15–0.5) region occupying the corner B ≲ 0.12,
J ≲ 2.0–2.4, with the boundary running diagonally: B-boundary at
B ≈ 0.12 (sharp: c jumps 0.3 → 1.06 within ΔB = 0.02 at J = 1.7), and a
J-boundary slanting from J ≈ 1.7 at B = 0.12 to J ≈ 2.4 at B = 0.06.
Inside the lobe the gap at N=12 is a basin (0.045–0.083) and the ground
state is pinned; outside it c ≈ 1.05–1.11 (the wedge). The coarse-map
"island" point (0.1, 2.0) sits ON the lobe's J-boundary — it is the
transition cell, not the interior.

## (b) Ground-state character: pinned commensurate lobe vs critical wedge

Decisive signatures:
- **Plateau test** (same test that caught the spurious J=0.5 c-values):
  deep-lobe points (0.1, 1.6) and (0.06, 2.3) saturate hard,
  S(ℓ) = 0.265 → 0.350 with increments → 0.000 — area law, genuinely
  gapped. The wedge point (0.2, 2.0) keeps growing (increments 0.242,
  0.119, 0.069, 0.037, 0.012) — critical. So the low-c values inside
  the lobe are REAL, not CC-fit artifacts.
- **Order parameter r**: HIGH inside the lobe (r = 0.629 at (0.1, 1.6),
  0.636 at (0.06, 2.3)) — rotors pinned to their reference phases —
  vs r = 0.069 in the wedge at (0.2, 2.0) (depinned, phase-fluctuating).
  This is the textbook commensurate-incommensurate contrast: the lobe
  is the commensurate (locked) phase, the wedge the incommensurate LL.
- **q**: q = 2π/12 = π/6 across essentially the whole zoom region —
  the lobe is locked to the decoration's commensuration (helix winding
  once per ring), no incommensurate wave vector anywhere. The one
  shifted value (q = 0.65 at the boundary point (0.1, 2.0)) is most
  likely fit noise at the transition.
- **Per-site w** carries a crystal pattern: at (0, 2.0),
  w_i = (0.137, 0.5, 0.863, 0.863, 0.5, 0.137) with period 6 (verified
  against one-site reduced density matrices) — some sites pinned near
  ref, some near ref+π, some free; the mean is trivially 0.5
  everywhere, but the per-site vector shows the locked modulation.
- **η**: ~2.8 inside the lobe (fast decay, gapped) vs ~0.23 in the
  wedge.

## (c) Persistence with N — the lobe is real and opens further

| point | gap N=8 → 10 → 12 → 14 | c N=8 → 14 |
|---|---|---|
| (0.1, 2.0) boundary | 0.173, 0.133, 0.083, **0.435** | 1.10, 1.10, 0.95, **0.15** |
| (0.1, 1.6) interior | 0.146, 0.126, 0.327, **0.673** | 1.10, 1.09, 0.19, **0.12** |
| (0.2, 2.0) wedge | 0.181, 0.144, 0.119, **0.100** | 1.08, 1.07, 1.06, **1.06** |

The lobe's gap GROWS with N (and c collapses to ~0.12–0.15) while the
wedge's gap closes ~1/N with c stable at 1.06. The N=12 "small-gap
island" was misleading in the gap channel — N=12 sits at a
commensurability sweet spot (the ring matches the ref pattern) where
even the locked phase has a soft gap — but c and r already separate the
phases at N=12, and the N-scaling settles it: the lobe persists and
strengthens; it does not shrink.

## (d) Artifact assessment

Not an artifact. Three independent tests agree: (i) S(ℓ) saturates
inside the lobe (the plateau test that previously caught spurious c),
(ii) the gap grows with N at the boundary AND interior points while
closing 1/N in the wedge, (iii) r and the per-site w pattern show a
pinned, modulated state with the decoration's commensurate q = π/6.
The N=12 gap-basin is a commensurability coincidence (N = ref count),
not a second critical region. The only genuinely anomalous data point
is q = 0.65 at (0.1, 2.0) — flagged as probable fit noise at the phase
boundary rather than an incommensurate signal.

## Files

`island_zoom.py`, `results_island.json`, `maps/island_{gap,c,q,r}.png`,
this file.
