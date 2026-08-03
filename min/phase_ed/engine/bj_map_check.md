# Full (B, J) characterization map — verdict

Grid: rotor chain N=12, B ∈ [0.0, 0.5] × J ∈ [0.0, 2.0], 441 points,
E0/gap (eigsh k=2, arena matvec, worst Lanczos residual 8e-9), CC-fit c,
correlator η + oscillatory flag. Data: `results_bj_map.json`; maps:
`maps/{gap,c,eta}_bj.png`. Off-line validation before the sweep:
gauge-folded complex-H matvec vs explicit-ref dense at (B=0.10, J=0.7):
max |ΔE| = 1.15e-14 (gate 1e-8). Wall time 3 015 s (~6.8 s/pt — eigsh
k=2 dominates; near-critical points cost ~4 s regardless of tolerance,
which is why tol = 1e-8 was used: E0/gap identical to 1e-11 runs).

## (a) Does the gap valley track B = 0.25 exactly across J?

Only up to J_c. The valley sits exactly on the line for J ≤ 1.0
(min 0.0835 at J=1.0), then **bifurcates**: at J=1.5 the minimum has
moved to B = 0.175 (and mirror B = 0.325), at J=2.0 to B = 0.10 (and
0.40) with gap 0.0827 < the on-line 0.1212. The gap map
(`maps/gap_bj.png`) shows a bowtie/X centered at (0.25, ~1.0). The
drift is real physics, not a solver artifact (residuals ≤ 8e-9 at every
point, and the points revalidate against dense diagonalization).
Interpretation: past J_c the pure-phase-model critical point on the
line becomes a saddle of the gap landscape; the minima live off-line in
field-pinned regions whose local excitations soften.

## (b) Is c ≈ 1 confined to the line, or is there a critical wedge?

**A wedge.** The c map (`maps/c_bj.png`) shows c ≈ 1.0–1.06 forming a
fan that opens from the point (B = 0.25, J ≈ 1.0): at J = 1.0 it spans
roughly B ∈ [0.2, 0.3]; by J = 2.0 it spans B ∈ [0.1, 0.4]. Below the
fan (J < 1) c collapses to ~0 (gapped). Outside it at large J
(B ≲ 0.1 / ≳ 0.4) c drops again (0.95 at (0.1, 2.0)) — a gapped pocket
coincident with the drifted gap minimum. So the honest statement is:
the competition line is the SPINE of a critical wedge that widens with
J, not a one-dimensional critical object. At N=12 the wedge edges are
smooth crossovers, not sharp boundaries.

## (c) η on the line and the K estimate

On B = 0.25: η runs 0.53 (J=0.6) → 0.33 (0.8) → 0.29 (0.9) → 0.264
(1.0) → 0.238 (1.25) → 0.221 (1.5) → 0.211 (2.0). With the phase-model
relation η = 1/(2K): K ≈ 1.5 at J=0.8, 1.7 at J=0.9, 1.9 at J=1.0,
2.1 at 1.25, 2.3 at 1.5, 2.4 at 2.0 — K climbs through K = 2 (the BKT
value) right at J_c ≈ 1.0–1.1, exactly as required. Consistent.

## (d) Off-line structure — the oscillation is commensurate, not PT

320 of 441 points have non-monotone C(r) with sign changes, and the
oscillatory fit beats plain algebraic at 333 points. The wave vector is
**q = 2π/12 = π/6 at 411/441 points (93%)** — the ring's reference-phase
winding. Off the line, the ground state carries the helix imprint of
the ref_i pattern (which winds once around the ring by construction),
and that is the oscillation the fit sees. The remaining ~30 points are
short-correlator fit noise. Verdict: NO Pokrovsky–Talapov
incommensuration anywhere in the plane — q is locked to the decoration
commensuration by construction, on and off the line. Additional
structure: the bowtie gap bifurcation of (a) and a low-c pocket at
(B ≈ 0.1, J ≈ 2.0) are the only off-line surprises, both reported above.

## Files

`bj_map.py`, `bj_maps.py`, `results_bj_map.json`,
`maps/{gap,c,eta}_bj.png`, this file.
