# Stage B v2: cyclic-parallel Jacobi entanglement — validation report

Program: `stageB_jacobi.ergo` (generator `gen_ergo_stageB_jacobi.py`).
Techniques per Fawzi & Goulbourne (NeurIPS 2021): cyclic elimination
(round-robin tournament schedule, every off-diagonal once per sweep),
parallel rounds (⌊n/2⌋ disjoint pairs per round, n−1 rounds per sweep),
termination on off(A) = √(Σ_off-diag²) < 1e-10·√n, eigenvalue-only mode
(no V accumulation). Schedule computed inline via MOD arithmetic (no
DATA tables). Rotation: stable tan form (τ, t = sgn(τ)/(|τ|+√(1+τ²)),
c = 1/√(1+t²), s = t·c).

## Standalone eigensolver validation

- **5×5 known spectrum** (diag {1..5} + orthogonal similarity):
  recovered exactly ({1, 2, 3, 4, 5} unsorted), 4 sweeps.
- **81×81 random Gram** (from random 81×200 A): eigenvalues match numpy
  `eigvalsh` to **1.9e-11 relative** (gate 1e-8), 7 sweeps. ✓
- Sweep counts in production: 0 sweeps for l ≤ 4 (Gram nearly
  diagonal-dominant at these sizes after build), 12 (cap) for l = 5, 6.

## Production validation

**(B=0.25, J=1.0) — line point, PERFECT.** Ground E0 = −4.2367838390
(converged). S(l) matches Python `entropy_cc` to all printed digits:

| l | Ergo S | Python S |
|---|---|---|
| 1 | 0.880772 | 0.880772 |
| 2 | 1.112147 | 1.112147 |
| 3 | 1.226433 | 1.226433 |
| 4 | 1.292696 | 1.292696 |
| 5 | 1.328267 | 1.328267 |
| 6 | 1.339547 | 1.339547 |

**CC-fit c = 1.0161** vs Python all-cuts 1.0161 — exact, well inside the
±0.05 band around the 1.017 target.

**(B=0.1, J=2.0) — formula caveat (important, honest).** The task's Gram
G = A_r A_r^T + A_i A_i^T equals **Re(A A^H)** = Re(ρ) where ρ is the
true reduced density matrix. These coincide only for states that are
real up to a global phase (the line point — hence exact there). For a
genuinely complex ground state (off-line), Re(ρ) is NOT ρ, and the
spectrum differs: Ergo computed exactly the specified formula (verified
to 5e-5 against a Python replica of the same Gram), giving S(l) =
[0.730050, 1.051919, 1.275998, 1.404233, 1.477338, 1.530055] and
c = 1.5659, whereas the true entanglement spectrum (eig of the complex
Hermitian A A^H, i.e. SVD of A) gives S(l) = [0.730026, 0.944375,
1.052292, 1.115815, 1.149616, 1.160217] and true c = 0.9537 (matches
the island work's 0.954). The correct Ergo upgrade if wanted: eig of
the 2n×2n real-symmetric block [[G, −K], [K, G]] (G, K = real/imag
parts of A A^H), whose spectrum is each ρ eigenvalue doubled.

## Cost model and timings

- Gram build: RL²/2 × CL ≈ RL·531k/2 MACs — l=6 (729): ~2×10⁸, ~1 s.
- Cyclic Jacobi: ~M³ ops/sweep; ~0–12 sweeps needed. l=6 (729):
  ~3–5 s; l=5 (243): <0.5 s; smaller: negligible.
- Per-point totals (including ~60–90 s ground solve at N=12):
  full production run (2 points, 12 cuts): **2 min 58 s** wall.
  The previous naive largest-element-search Jacobi took >96 min on the
  same workload (>50× slower, mostly the search + redundant rotations).
- Per-sweep parallelism: within a round the ⌊n/2⌋ pair updates are
  disjoint and independent → MAP-extractable (good GPU prospects);
  rounds are sequential with a barrier per round (n−1 barriers/sweep).

## GPU extraction prospects

The pair-rotation inner loops (`DO C0 = 1, M` row/col updates) are
affine-index array updates — INJECTIVE, extractable as-is. The round
loop is a host loop; each round's pair loop is a MAP over disjoint
index pairs (extractable once the MOD-based participant computation is
tableized or computed per-thread). off(A) is a REDUCTION per sweep.
No structural blockers for a SPIR-V version; the win would be the 729
cut where sweeps cost seconds.

## Files

`gen_ergo_stageB_jacobi.py`, `stageB_jacobi.ergo`, `stageB_jacobi` (binary),
`stageB_jacobi.out`, this file. Stage A (recap): `stageA_complex.ergo`,
validated 5/5 points (E0 to 5e-9, gap to 1e-6, B↔0.5−B symmetry exact).
