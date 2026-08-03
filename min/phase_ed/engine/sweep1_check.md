# Sweep round 1 — gap maps for all four plugins

Data: `results_sweep1.json` (1254 points). Maps: `maps/{rotor,xxz,fk,rydberg}_gap.png`.
Driver: `sweep1.py`. Wall times: rotor 56 s, xxz 13 s, fk 55 s, rydberg 2 s
(total ~2 min for 1254 points).

## Execution notes (honest)

- **GPU tier measured and rejected for this round**: cupy's batched eigh
  uses cusolver *syevj* (Jacobi): timed at **47.6 s/matrix** at 6561-dim
  complex64 — vs ~0.1 s/point for CPU sparse Lanczos on the numba matvec.
  All sweeps ran on CPU sparse Lanczos (k=2, k=3 for rydberg). The GPU
  tier remains useful for single large dense eigh (5.6× at 6561-f32) but
  not for batched many-point sweeps at this size.
- **Construction caching**: `engine/cache/` with npz keyed by
  model+N+params hash and an 8 GB budget (disk had only 22 GB free —
  441 × 344 MB dense matrices were never storable). The real fix was a
  **fast dense emitter** (`matvec_fast.fastchain_to_dense`, one
  O(dim·N) numba pass, 0.05–0.9 s vs ~10 s column-wise; validated to
  4e-15 vs the matvec). With rebuilds that cheap, the cache is only
  exercised for small-dim models; roundtrip verified.
- **ARPACK pathology found and patched**: on exactly-diagonal
  Hamiltonians (rotor B=0.25,J=0 and fk V=0,J=0 — pure kinetic term),
  `eigsh` (every which/k/ncv variant, LinearOperator or `sparse.diags`)
  silently returns the *second* eigenvalue (0.5) instead of the true
  minimum 0. Both points patched analytically (E0=0, gap=0.5) in the
  JSON and guarded in `sweep1.py` (`_diagonal_only`). Every other J=0
  rotor point was validated against the known single-rotor values (all
  match to the spin-1 truncation error).

## Verdicts

**Rotor** (`maps/rotor_gap.png`): the map shows exactly the expected
structure — a deep gap valley pinned to the competition line B=0.25
across all J, with gap minimum 0.118 at J=0.9 and a sub-0.15 valley
floor from J=0.6 to J=1.5 (the finite-N signature of the critical
phase above J_c ≈ 1.0–1.1, marked). Off the line the gap reopens
symmetrically (0.163 at B=0 and B=0.5, J=2 — the B↔0.5−B symmetry
holds map-wide). No anomalies beyond the patched diagonal point.

**XXZ** (`maps/xxz_gap.png`): h=0 gap peaks at 0.356 exactly at Δ=1
(canonical BKT point, marked) with the ridge extending to h≈0.5; gap
falls monotonically for |Δ|<1 as expected of a LL with field. The
Δ=−1 column has gap 0 at h=0 (ferromagnetic Heisenberg point:
degenerate multiplet) and brightens ∝ h (Zeeman splitting) — correct,
not an anomaly. For Δ>1, the E1−E0 decay is the Néel SSB doublet
(cat splitting), per the established protocol note.

**FK** (`maps/fk_gap.png`): clean pinning picture — gap ≈ 0.1–0.18
along V=0 (free-rotor LL), monotone growth with V everywhere
(2.386 at V=3,J=0; 3.175 at V=3,J=2), no structure in J at fixed
V>0.5. Matches the sine-Gordon mass-generation expectation: any V
gaps the free boson at these sizes; no sign of a separate
commensurate-incommensurate line at N=8 (would need vector
observables and larger N to resolve).

**Rydberg** (`maps/rydberg_gap.png`): textbook Ising. E1−E0 (cat
doublet) collapses exponentially past δ≈0.75 — a perfect straight
line on the log axis down to 4e-9 at δ=3 — while E2−E0 has a clean
minimum (0.359 at δ=0.6–0.75) and rises linearly after. The
doublet-protocol (k≥3) works exactly as designed. Transition region
δ_c ≈ 0.6–0.8 at N=16, consistent with the c≈0.5 peak found earlier.

## Follow-ups flagged

- Vector observables (c, q) on the rotor valley edges (J≈0.6–0.8,
  B=0.25) to sharpen the gapped/critical boundary at N=8–12.
- XXZ h>0 LL exponent run along Δ=0.5 (K(h) from η via CPU vectors).
- FK at larger N (12–16) near V≈0.1–0.3 to look for the KT
  unpinned/pinned boundary that N=8 cannot resolve.
- ARPACK diagonal pathology: reported upstream-worthy; guard exists
  in `sweep1.py` but other drivers (analysis.py) should inherit it.
