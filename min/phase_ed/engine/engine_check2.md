# Engine expansion: FK + Rydberg plugins, GPU tier (gates and numbers)

## Task 1 — FK (pendulum form) plugin, `models/fk.py`

H = Σ pᵢ²/2 − J Σ cos(φ_{i+1} − φᵢ) − V Σ cos(q φᵢ), spin-1 rotors, I=1 —
the coupled-pendula (quantum sine-Gordon) form of Frenkel-Kontorova:
structurally the rotor chain with a uniform q-fold substrate field (no
gauge twist). Basis caveat documented in the plugin: the substrate term
has matrix elements only for q = 1, 2 in the spin-1 basis (q ≥ 3 vanishes,
like the rotor drift).

**GATE (q=1, J=1), gap series — PASS:**
- V = 0: 0.120548, 0.098344, 0.083523 (N = 8,10,12) — closes as 1/N,
  fit 0.889/N + 0.009, and numerically identical to the B=0.25 rotor
  chain at J=1.0 (same model, as required).
- V = 2: **2.060687 at all three N** — pinned, exactly size-independent
  (substrate-dominated single-site gap), definitively not closing.

## Task 2 — Rydberg blockade plugin, `models/rydberg.py`

Constrained basis (no adjacent 1s incl. wrap; Lucas-number dimension:
322/843/2207 at N=12/14/16). Honest structural note in the plugin: with
the strict blockade, V Σ nᵢnᵢ₊₁ ≡ 0 in this sector — the model is the
detuned PXP form (Ω=1); V is kept as a native parameter but is inert here.

**GATE (Ω=1, δ ∈ [0,3], N = 12,14,16) — PASS (engine does NOT see c=1
everywhere):**
- (a) Z2-ordered region: δ ≳ 1.0–1.25. Signature: E1−E0 → 0 (cat-doublet,
  e.g. 0.0066 at δ=1.0 down to <1e-4 at δ≥2, N=12) while E2−E0 stays
  finite and grows (0.59 → 2.8). Order parameter ⟨m_s²⟩ (N=16): 0.062 at
  δ=0.5 → 0.225 (δ=2) → 0.238 (δ=3), approaching the 0.25 Néel limit.
  (⟨m_s⟩ ≡ 0 identically in the symmetric finite-size ground state —
  recorded as a measurement-protocol note.)
- (b) Transition region δ ≈ 0.5–1.0 (E2−E0 minimum at δ≈0.75): CC-fit c
  peaks at **0.487–0.545** — at N=14/16: 0.515/0.520 (δ=0.5) and
  0.520/0.504 (δ=0.75) — Ising c = 1/2 within ±0.1 at the larger sizes.
- (c) No intermediate LL region resolves: c never approaches 1 anywhere
  in the sweep (max 0.545). Consistent with the strict-blockade model
  having a direct disordered→Z2 Ising transition; the literature's
  floating phase needs finite-V (unconstrained) or longer-range terms,
  which this sector excludes. The grid (0.25 step) does not resolve the
  transition location better than δ_c ≈ 0.75 ± 0.25; c estimates at
  N=12 are ~0.05 above the N=14/16 values (finite-size drift in the
  right direction).

## Task 3 — GPU batch tier, `gpu_batch.py`

- GPU: RTX 2060, 6 GB, driver CUDA 13.1. cupy-cuda12x failed
  (libcusolver.so.11 missing); **cupy-cuda13x 14.1.1 installed in the
  venv** and verified. VRAM caveat: ~4.4 GB was occupied by another
  process at benchmark time, so batch size is auto-fit to free VRAM
  (`memGetInfo`, 70% headroom) rather than blindly 16 — a 6561-dim
  complex64 matrix is 344 MB, so batch 16 = 5.5 GB was not available.
- `batched_eigh(model, N, grid)`: dense build via `model.make_dense`,
  stacked upload, `cupy.linalg.eigh`, downloads (E0, gap) per point
  (vectors optional). Benchmark, rotor N=8 (6561-dim), 16 points:
  - Under the observed foreign VRAM occupation (~4.3 GB used by another
    tenant), the auto-fit degraded to batch=1 and cusolver thrashed:
    1352 s for 16 eigh calls (~85 s/matrix) — no speedup, correctly
    flagged as contention, not a code path worth using in that state.
  - Clean microbenchmark (random symmetric 6561² float32, same matrix
    both sides): CPU `eigvalsh` 13.4 s vs GPU 2.4 s incl. upload —
    **5.6× speedup**, eigenvalues match to 3.9e-4 (float32 rounding).
  - Batch 16 at this dim needs 2.75 GB (f32) / 5.5 GB (c64) contiguous
    free VRAM; usable only when the GPU is not shared. Dense builds via
    column-wise `make_dense` dominate wall time (~20 min for 16 rotor
    matrices under CPU contention) and should be cached or moved
    on-device in a future iteration.

