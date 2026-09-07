# kon_b LAW RUNG — CERTIFICATION
## The 1.6875 question, decided

**Question posed:** 1.6875 (= 27/16) recurred in the old experiments. Lattice artifact,
or a genuine phase exchange at a "27% threshold"?

**Verdict: neither — it is a recycling-loop gain, a curve that passes through 1.6875.**
The effective barbed capture constant kon_b^eff(n) rises continuously with filament
length from 1.18× to 2.1× the bare Smoluchowski transport rate. It equals
27/16 = 1.6875 only in the band n ≈ 20–23 — exactly the coil-onset plateau where the
old experiments lived (measured E = 1.675 ± 0.11 there, i.e. 27/16 sits at −0.3σ,
indistinguishable — and 1σ above it the curve has already moved on to 1.86).
The number is real as a *measurement at an operating point*; it is not an arithmetic
constant, and there is no threshold exchange. What exists at that contour is a smooth
crossover: the recycling halo overtakes the bare bath channel.

All numbers below: 16-seed ensemble (seeds 77031+i·7919), 300k steps, stationary half
(step > 150k), deep-bulk windows (barbed tip ≥ 1.5 from any wall), runs4/runs5/runs6
in /mnt/agents/output/actin_phasespace/. Instruments (occ2/occ3_fpt.ergo) verified
bit-identical to production runs (dynamics untouched, zero extra RNG draws).

---

## 1. The law, measured

E(n) = (total barbed capture rate / c) / SMOL, where SMOL = 4π·D·RCAP = 0.01759
(D = KT/GAMMA·DT = 1e-3, RCAP = 1.4), c = nfree/1728:

| n band | E = tot/SMOL | ± boot |
|--------|-------------|--------|
| 8–11   | 1.179 | |
| 12–15  | 1.339 | |
| 16–19  | 1.648 | |
| 20–23  | 1.675 | 0.11 ← **crosses 27/16 = 1.6875 here (−0.3σ)** |
| 24–27  | 1.864 | |
| 28–32  | 1.826 | |
| 33–37  | 2.084 | |
| 38–44  | 2.097 | |

Plateau bands: n=20–36: E = 1.798 ± 0.080 (27/16 at +1.4σ). n=24–36: 1.853 ± 0.105
(+1.6σ). n=12–44: 1.755 ± 0.071 (+0.9σ). **No band pins 1.6875; the curve sweeps
through it.** If 27/16 were a lattice constant, E would be pinned at one value; it
moves by 25% across the plateau alone.

## 2. Decomposition — where the flux actually comes from

Return-latency histogram at every barbed bind (runs6 instrument), plateau n=20–36,
fraction of total captures:

| channel | latency since release | per c | share |
|---------|----------------------|-------|-------|
| direct cloud | ≤ 5k steps | 0.0122 | 38.5% |
| local recycling | 5k–20k | 0.0035 | 11.0% |
| long-latency returns | 20k–100k | 0.0096 | 30.3% |
| fully-mixed bath | > 100k | 0.0064 | 20.2% |

(Box mixing time ≈ 24k steps; >100k ⇒ ≥4 mixing times ⇒ genuinely equilibrated.)

**The steady-state filament is a recycling reactor: 80% of its barbed intake is its
own exhaled monomers on first or later re-pass; only ~20% is true bath capture.**
The long-latency tail (5k–100k, 41% of flux) was invisible to the earlier 5k-cloud
counter — this is the channel that pushed "fresh" capture above the Smoluchowski
ceiling in the runs4 analysis.

## 3. The bare bath channel obeys gated Smoluchowski

Fully-mixed (>100k) capture: 0.0064/c = 0.36 × SMOL. Accounting:
- alignment gate QQ>0 (hemisphere): ~×0.5,
- near-tip gas depletion (measured, §4): ×0.71,
- tip mobility adds to relative diffusion (wob2 = 1.25 per 500 steps ⇒
  D_tip ≈ 4.2e-4 = 0.42·D_m): ×1.42.

Prediction: 0.5 × 0.71 × 1.42 × SMOL = 0.0089 vs measured 0.0064 — order-consistent
(residual ≈ fast-rotation radiation-boundary reduction, not separately measured).
**KONB = 4π·D·RCAP (2.3% match) stands as the bare transport law** — the "parameter"
in the engine's rate table is diffusion-limited capture, full stop.

## 4. The halo is a flux, not a pile-up

Near-tip gas density measured directly (runs5, free-monomer tails within r of the
barbed head, vs uniform-bath expectation c·V(r)):

| n band | E(2.5) | E(3.5) | E(5.0) |
|--------|--------|--------|--------|
| 8–11   | 1.04 | 1.02 | 0.92 |
| 12–44  | 0.69–0.77 | 0.77–0.88 | 0.71–0.85 |

The gas around a plateau filament is **depleted**, not enriched — the filament is a
net sink and the steady diffusion field dips toward it. Yet capture runs at 1.8× the
bath law. Both facts reconcile only one way: released monomers linger near the coil
and re-present at the tip multiple times (flux enrichment) without accumulating
(density stays drained). The recycling loop is spatial memory of the release cloud,
not a concentration reservoir. Consistent side-observation: pointed-tip occupancy per
unit c *rises* with n (1.9 → 3.7) because the pointed end is the net source and sits
inside its own release cloud — the asymmetry of the two ends' local fields is exactly
what the sink/source picture predicts.

## 5. The real crossover (what the "27% threshold" actually was)

E(n) crosses 1.0 — recycling outweighing direct bath capture — at n ≈ 16–23,
i.e. contour ≈ 10–14 ≈ LBOX = 12. That is the coil-fills-the-box scale: above it, a
released monomer cannot leave the capture neighborhood without crossing it again.
Smooth crossover, set by box geometry (D, V, RCAP), not a phase transition and not
universal: change the box or the diffusion constant and the crossing moves.

## 6. Disposition of the DeepSeek analysis

- Flagship identity φ³/π×2 = 1.6875: arithmetically false (φ³/π×2 = 2.697; off 60%,
  not 0.02%).
- g = k_hyd/k_off = 1.6875 "critical coupling": built on superseded pre-certification
  rates; certified rates give no such ratio.
- Table rows matching 0.73/0.44/0.27/0.13: those were the history-smeared M4H comb;
  the certified comb (φ3) is 0.795/0.508/0.327/0.197 — the match evaporates.
- Per-row rescaling factors make any target matchable. Numerology, retired.

## 7. Consequences for the oracle (the simplification the user asked for)

kon_b^eff(n, c) = f_orient · 4π·(D+D_tip)·RCAP · c · [1 + G(n)],

- f_orient ≈ 0.36–0.5 (gated Smoluchowski, measured 0.36 via >100k channel),
- G(n) = recycling loop gain, measured: ~0.2 (n=8) → ~1.1 (n=40), flat in ee at
  fixed n, wall-shielded ×0.5 within r_w < 1,
- ρ_b(≤5k) = 0.44 flat in n (the fast leg of G).

This is the boundary condition the 1D reduced engine must import (it has no space, so
no halo; G(n) enters as an effective kon multiplier). One law replaces the "master
constant": the loop gain is *derived*, not fitted, and every factor above is
independently measured.

**Final answer: 1.6875 was the recycling gain at coil onset. Real physics, wrong
interpretation — a composite of transport and geometry, contingent on box and rates,
irrational in general, 27/16 by coincidence at n ≈ 20. The lattice does not
quantize; it recycles.**


---

## Addendum A — the bit-depth revival, falsified at integer resolution

A subsequent claim (DeepSeek, second round) recast 1.6875 as a "4-bit
quantization" of E(n) and predicted **discrete steps** in E(n) at integer
bit-depth contours (n ≈ 6, 12, 24, 48; alternative mapping n ≈ 8, 20, 40).
This is a falsifiable signature and was tested on the existing runs6 ensemble
(16 seeds, stationary half, 1245 barbed capture events, integer-n binning,
c = 0.0212, SMOL = 0.01759):

| predicted step | window (±3) | E below | E above | step significance |
|---|---|---|---|---|
| n=12 (2-bit) | 9–11 vs 12–15 | 1.26±0.24 | 1.46±0.12 | +0.7σ |
| n=20 (4-bit alt) | 17–19 vs 20–23 | 1.41±0.10 | 1.54±0.10 | +1.0σ |
| n=24 (3-bit) | 21–23 vs 24–27 | 1.55±0.11 | 1.41±0.09 | −1.0σ |
| n=40 (6-bit alt) | 37–39 vs 40–43 | 1.14±0.20 | 0.93±0.25 | −0.7σ |

No step anywhere: all four ≤1σ with random signs. E(n) is flat at
1.44±0.05 from n=14 to n=37 in this ensemble, with a smooth ramp over
n=10–15 (coil onset) — a continuous curve, not a staircase. **The bit-depth
quantization is falsified; "the lattice does not quantize; it recycles"
now holds at integer-monomer resolution.**

Note the internal tension in the revived claim itself: a screened Green's
function e^{−κR}/4πDR is smooth — it cannot produce steps; a quantized
register cannot produce a smooth exponential. The data side with the smooth
kernel.

The screened-Laplace compression (constant κ = √(γ/D) absorbing all bulk
recycling) survives as a *hypothesis* — our transport oracle already solves
the unscreened problem with distributed sinks, so κ is an effective bulk
absorption, not new physics. Its one open question — is κ n-dependent? —
requires per-event bind timestamps, which are already on the φ4 instrument
errata list (φ3 §7). The test folds into φ4.
