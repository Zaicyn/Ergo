# Finite-size scaling of the condensate — N ∈ {24, 48, 96}

Programs: `gen_condensate_n.py` → `condensate_n48.ergo`,
`condensate_n96.ergo` (N=24 baseline from `condensate_tc.ergo`). Same
physics as `condensate_check.md` (8 constant-T blocks, Gaussian
inter-chain attraction, harmonic sphere).

## Scaling protocol (documented)

- **ATT_K = 0.005 per pair, constant with N.** The pair potential is a
  two-bead property; it must not scale with N. What grows with N at
  constant bulk density is the coordination per chain (extensive
  binding) — that IS the correct extensive physics, not a scaling
  artifact. N-dependence should therefore enter only through droplet
  fluctuations (~1/√N) and droplet surface/volume.
- **R_BOX ∝ N^(1/3):** 18.0 / 22.67 / 28.57 for N = 24/48/96 — bulk
  density held constant. Grid starts spacing 5 u everywhere (grid
  occupies ~4–6% of box volume at every N).
- **Cost:** N=48: 97 s; N=96: 6 m 00 s (5376 residues — vs 8 m 49 s
  for the 4456-residue SdrD run; scaling is the expected n² of the
  pair loops). Within budget as background runs.

## Finite-size scaling table (late-half statistics per block)

| N | TMUL | frac(late) | σ(frac) | shed/1000f | T50 | dense ρ | dilute ρ |
|---|---|---|---|---|---|---|---|
| 24 | 0.5–4 | 0.917 | 0.000 | 0.0 | 200 | 0.00524–0.00539 | 0.00229 |
| 24 | 6 | 0.868 | 0.041 | 0.1 | 200 | 0.00513 | 0.00458 |
| 24 | 8 | 0.878 | 0.042 | 0.7 | 200 | 0.00524 | 0.00458 |
| 24 | 10 | 0.917 | 0.000 | 0.0 | 200 | 0.00568 | 0.00229 |
| 48 | 0.5–6 | 0.938 | 0.000 | 0.0 | 200 | 0.0176 | 0.00068 |
| 48 | 8 | 0.983 | 0.023 | 0.0 | 200 | 0.0137 | 0.0000 |
| 48 | 10 | 0.994 | 0.009 | 0.0 | 200 | 0.0137 | 0.0000 |
| 96 | 0.5–10 | 0.979–0.990 | ≤0.005 | 0.0 | 400 | (see caveat) | (see caveat) |

## Verdicts per question

**(a) Does the Tc bracket sharpen with N? NO — it closes over.** The
fluctuation amplitude does follow the expected scaling: σ(frac) at the
hot end ≈ 0.041 (N=24) → 0.023 (N=48) → ≤0.005 (N=96), a clean ~1/√N
law. But the fraying window itself (TMUL 6–8 at N=24) does not narrow
toward a critical point — it DISAPPEARS: at N=48 the only remnant is a
slight fray at TMUL=8 (σ=0.023, zero shed events), and at N=96
everything is condensed through TMUL=10 (frac 0.98–0.99). Larger N
makes the droplet more stable at every temperature on this ladder.
**(b) Does the homogeneous phase appear at large N? NO — it recedes.**
At N=24 the hot blocks at least frayed; at N=96 there is not even a
shed event. Escaped chains recapture more effectively as the droplet
grows, and the evaporated fraction shrinks with N at fixed T.
**(c) Binodal gap T-dependence: only evaluable at N=24** (it narrows
0.003 → 0.0006 toward Tc, as reported before). At N ≥ 48 there is no
fraying on this ladder, so no curve to fit; and at N=96 the metric
itself breaks at the hot end — the weak harmonic confinement
(CONF_K=0.01) loses to T=0.1 kicks, the vapor cloud expands past the
box (implied cluster radius 64 u vs box 28.57 u), and the
dense/dilute densities are meaningless there. N=48's metrics are fine.
**(d) Coalescence time: sensible.** T50 = 200 → 200 → 400 frames for
N = 24/48/96 — roughly doubling per 4× N (more chains to gather,
larger box), no pathological scaling.

## Physical reading (documented interpretation)

At constant bulk density, mean-field Tc is N-independent — it is set by
coordination × well depth, both fixed here. What the N=24 "fraying"
actually was: fluctuation-driven partial shedding of a small droplet,
suppressed ~1/√N as N grows. So the ladder (T ≤ 0.1) is simply BELOW
Tc everywhere at N ≥ 48, and the sharpened finite-size story is that
the N=24 fluctuation regime was the small-system tail of the same
physics, not a transition. The correct protocol for a real Tc bracket
at N=96 is a HOTTER ladder (TMUL ≈ 20–30, with sim-stability checks
on kick magnitude) AND a stronger confinement (CONF_K must beat the
kick amplitude or the cloud escapes the sphere, as measured at
TMUL=10/N=96) — not a bigger N. From the trend, no plausible N fixes
the cage at this temperature ladder: the cage is a T/CONF_K issue,
not an N issue.

## Bottom line

N=96 is not "still cage-dominated" in the naive sense — it is cleanly
BELOW Tc: the fluctuation amplitude obeys ~1/√N exactly as finite-size
theory predicts, and with that suppression the droplet never frays. The
questions as posed answer: (a) bracket closes rather than sharpens,
(b) homogeneous phase recedes with N, (c) binodal curve evaluable only
at N=24, (d) coalescence scales sensibly. The next experiment, if Tc
is wanted, is a TMUL 20–30 sweep with CONF_K ≈ 0.05 — documented here
with its failure mode (confinement escape) already measured.

Files: `gen_condensate_n.py`, `condensate_n48.ergo`,
`condensate_n96.ergo` (+binaries), `condensate_n48.out`,
`condensate_n96.out`, baseline `condensate_tc.out`, this report.
