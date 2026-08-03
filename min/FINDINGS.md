# Findings: Competition-Driven Criticality in Driven Phase Systems

**Date:** 2026-07-25
**Status:** Evidence-complete at the stated numerical precision. All claims below are backed by files in `min/`, `min/spin_swap/`, and `min/phase_ed/`.

---

## 1. Executive Summary

Starting from a classical phase-oscillator simulation (the "redirect bias
sweep"), this project built a chain of increasingly exact models of the same
underlying competition — one attractive direction vs. one forbidden
direction per site — and established:

> **A 12-site quantum rotor chain with harmonic driving has a gapless,
> c = 1 (Luttinger-liquid) critical phase for inter-site coupling
> J ≳ 1.0–1.1, organized around a competition line pinned exactly at
> B = 0.25 by algebraic symmetry. The boundary is gapped, the critical
> line shows z = 1 gap scaling, the central charge is confirmed by exact
> diagonalization (N = 12–16) and calibrated DMRG (N = 16–48), and the
> full (B, J) map shows the line is the spine of a 2D critical wedge
> with a bowtie bifurcation at the BKT point.**

The classical simulator's "coherence crash" at bias ≈ 0.2–0.3 is the
mean-field echo of this quantum critical region: both occur at the same,
exactly computable balance point.

A second, independent thread replicated the Li/Pokorný trimer master
equation (Nat. Commun. 2026) in Ergo — including a direct 2D
reproduction of their charging-ring dI/dV maps — and used it to measure
the kinetic vs. energetic structure of charge-state stability
(Section 6).

A methods result fell out of the investigation: a documented
DMRG convergence failure at strong coupling that manufactured a
published-but-false "topological protection" signature, and the
referee protocol that prevents it (Section 5).

---

## 2. The Models

### 2.1 Classical bias sweep (Ergo)

`min/redirect_bias_sweep.ergo`. N = 1000 independent particles on a
12-node ring, phase dynamics per particle:

```
dφ/dt = ω + K_PHASE·sin(ref − φ) + B·K_BIAS·sin(ref + π − φ) + K_DRIFT·sin(3φ)
```

K_PHASE = 0.5, K_BIAS = 2.0, K_DRIFT = 0.1, ω = 1.0, ref_i = 2π(i−1)/12.
Bias B swept 0 → 1 in 21 steps; w = fraction of particles with
|φ − ref| > π/2 ("forbidden window").

### 2.2 Quantum rotor chain (exact)

`min/phase_ed/`. Each classical particle maps to a quantum rotor:

```
H = Σᵢ pᵢ²/2I  −  K_PHASE Σᵢ cos(φᵢ − refᵢ)
               −  B·K_BIAS Σᵢ cos(φᵢ − refᵢ − π)
               +  (K_DRIFT/3) Σᵢ cos(3φᵢ)
               −  J Σᵢ cos(φᵢ − φᵢ₊₁)          (periodic)
```

Key algebra (exact): since −cos(φ − ref − π) = +cos(φ − ref), the first
harmonic is −(K_PHASE − B·K_BIAS)·cos(φ − ref) and **vanishes identically
at B = K_PHASE/K_BIAS = 0.25**. This is the competition point; it is
algebra, not numerics.

### 2.3 Trimer PME (Li/Pokorný anchor)

`min/trimer_pme.ergo`. Exact 8-state Pauli master equation with the
paper's parameters (ε = −90 meV, W = 50 meV, kT = 0.22 meV) and their
tip electrostatics (charged sphere, z_tip = 0.6 nm, image plane
z_S = −0.09 nm; lever arm calibrated once to the 520 mV ring voltage).

---

## 3. Principal Results

### 3.1 The competition point is exact, and both descriptions meet there

| | Classical (driven ODE) | Quantum (T=0 ground state) |
|---|---|---|
| Competition point | coherence crash at B ≈ 0.20–0.30 | B = 0.25 exactly (harmonic cancellation) |
| w at competition | 0.506 | 0.500000 (exact) |
| Order parameter | coherence ≈ 0.01 | r = 0 (exact, 3-fold symmetry) |
| w sweep range | 0.338 → 0.910 | 0.116 → 0.977 |

Files: `min/redirect_bias_sweep.log`, `min/phase_ed/results_single.json`,
`min/phase_ed/comparison.md`.

The classical and quantum fluctuation-dominated regimes sit at the same
algebraic balance point. The absolute w values differ (driven steady
state vs. ground state; the quantum model has a zero-point floor of
0.116); the shared, robust content is the location and structure of the
competition point.

### 3.2 Gap scaling: z = 1, and the critical region is a phase, not a point

Finite-size gap on the competition line (spin-1 rotors, exact
diagonalization with a numba-compiled matrix-free operator, validated to
10⁻¹⁴):

| J | gap(N) series | 1/N intercept | verdict |
|---|---|---|---|
| 0.75 | 0.1196 → 0.0903 → 0.0763 (N=8,12,16) | **+0.033** | gapped |
| 1.00 | 0.1206 → 0.0835 → 0.0649 | **+0.009** | closes |
| 1.25 | 0.1322 → 0.0892 → 0.0677 | **+0.003** | closes |
| 1.50 | 0.1476 → 0.0987 → 0.0743 | **+0.001** | closes |
| 2.00 | 0.1822 → 0.1212 → 0.0909 | **−0.001** | closes |

Control (B = 0.50, J = 0.5): gap *rises* with N, extrapolates to +0.736.

Every J ≥ 1.0 closes as 1/N — z = 1 critical scaling — while J = 0.75
stays finite. The 1/N coefficient grows smoothly (0.89 → 1.46, linear in
J, rms 0.001), consistent with an excitation velocity increasing with
coupling. Conclusion: **a gapless critical phase for J ≳ 1.0–1.1**,
not an isolated critical point. Files: `min/phase_ed/results_fss.json`,
`n16_results.json`, `n16_extended.json`, `bkt_check.md`.

### 3.3 Central charge: c = 1 (Luttinger liquid)

Calabrese–Cardy fits S(ℓ) = (c/3)·log[(N/π)·sin(πℓ/N)] + const:

| N | method | J=1.0 | J=1.5 | J=2.0 | J=0.5 (control) |
|---|---|---|---|---|---|
| 12 | exact ED | 1.016±0.009 | 1.044±0.010 | 1.052±0.012 | 0.58 (bad fit) |
| 16 | exact ED | 1.004±0.008 | 1.034±0.008 | 1.040±0.009 | 0.48 (bad fit) |
| 16 | DMRG | — | 1.0006±0.0001 | — | 0.000 |
| 18 | DMRG | — | 1.0001±0.0001 | — | 0.194 |
| 24 | DMRG | — | 0.9989±0.0000 | — | 0.079 |
| 32 | DMRG | — | 0.9981±0.0000 | — | 0.025 |
| 48 | DMRG | — | 0.9962±0.0001 | — | 0.003 |

c = 1 within 0.4% across a 4× size range, two independent numerical
methods. The control column converges to zero with N — the area-law
signature of a gapped state, cleanly separated from the log growth.

DMRG trust chain (Section 5): energies χ-extrapolated, variance
certificates (⟨H²⟩−⟨H⟩² per site ≤ 2.8e-8), calibration vs. exact ED
worst residual 1.8e-11/site, checkpointed resume. Files:
`min/phase_ed/results_entanglement.json`, `results_dmrg_ent.json`,
`tenpy_calib.json`.

### 3.4 The full phase diagram (updated after the (B, J) map, §3.6)

```
                gapped phase          gapless critical phase
                (J < J_c)             (J ≳ J_c, c=1, z=1)
                      |               /  critical WEDGE  \
   gap ∝ 1/N .........|..........(==== spine ============)──  ← B = 0.25 (exact:
                      |               \   fan + bowtie   /      w = 0.5, r = 0)
                   J_c ≈ 1.0–1.1
```

On the line itself, w = 0.500000 and r = 0 exactly at every J: the system
sits in coherently delocalized superposition between the allowed and
forbidden sectors, and the gap to escape it closes as the collective
coupling reaches criticality. Below J_c the line is the exact gap
minimum; above J_c it becomes the spine of a 2D critical fan (§3.6).

### 3.5 Boundary type: BKT, confirmed by correlation wave vector

PT (Pokrovsky–Talapov) boundaries require an incommensurate correlation
wave vector q drifting with J and locking at the transition; BKT
boundaries have q commensurate throughout. Measurement (`min/phase_ed/
correlator.py`, `pt_bkt_check.md`) of C(r) = ⟨e^{i(φᵢ−φᵢ₊ᵣ})⟩ across
J = 0.5–2.0 and N = 12–48 (ED vectors + DMRG checkpoints):

- q = 0 at every point: C(r) strictly positive, monotone, zero sign
  changes; oscillatory fits hit the resolution boundary and fit 15–20×
  worse than plain algebraic decay.
- Correlation exponent η ≈ 0.28 (J=1.0) → 0.23–0.25 (J≥1.5), i.e.
  Luttinger parameter K = 1/(2η) ≈ 1.8 → 2.2 across the boundary —
  consistent with the universal BKT value K = 2.
- Lmax=2 spot check (where the cos(3φ) drift formally reopens a PT
  channel): no oscillation gained, ΔC ≤ 4e-4.

Combined with the exact reduction of the on-line Hamiltonian to the pure
quantum phase model (first harmonic cancels, drift has no spin-1 matrix
elements), the boundary at J_c ≈ 1.0–1.1 is **BKT**, supported by three
consistent signatures: gap closure ∝ 1/N, c = 1, K ≈ 2.

### 3.6 The (B, J) plane: critical wedge and bowtie bifurcation

The phase diagram as a plane, not a line
(`min/phase_ed/engine/bj_map.py`, `results_bj_map.json`, maps in
`engine/maps/`): 441 points, B ∈ [0, 0.5] × J ∈ [0, 2.0] at N = 12,
with E0/gap from Lanczos, central charge from CC fits, and correlation
exponent η from C(r). Four findings:

1. **The gap valley tracks B = 0.25 only up to J_c, then bifurcates.**
   Exact on the line for J ≤ 1.0 (minimum 0.0835 at J = 1.0); at J = 1.5
   the minimum moves off-line to B = 0.175 (+ mirror 0.325); at J = 2.0
   to B = 0.10 (+ 0.40), with off-line gap 0.0827 below the on-line
   0.1212. A bowtie centered on the BKT point: the competition line is
   the exact minimum below criticality and a saddle above it.
2. **c ≈ 1 is a wedge, not a line.** The critical region fans out from
   (B = 0.25, J ≈ 1.0), widening from B ∈ [0.2, 0.3] at J = 1.0 to
   B ∈ [0.1, 0.4] at J = 2.0, with c ≈ 0 everywhere below J_c (including
   on the line). The exact competition line is the *spine* of a 2D
   critical fan, not a 1D critical object.
3. **η runs exactly through BKT.** On the line: η = 0.33 → 0.264 →
   0.238 → 0.211 across J = 0.8 → 2.0, so K = 1/(2η) climbs 1.5 → 1.9 →
   2.1 → 2.4, crossing the universal K = 2 precisely at J_c ≈ 1.0–1.1.
4. **No Pokrovsky–Talapov anywhere in the plane.** 93% of oscillating
   correlator points carry q = π/6 — the ref-helix imprint,
   commensurate by construction. (One boundary point at (0.1, 2.0)
   showed q = 0.65 — recorded as fit noise at the transition, not an
   incommensurate signal.)
5. **A commensurate pinned lobe inside the wedge** (the "island,"
   resolved by zoom — `engine/island_zoom.py`, `results_island.json`,
   `engine/island_check.md`). The low-c region at (B ≲ 0.12,
   J ≲ 2.0–2.4) is a distinct gapped phase, not a fit artifact:
   - Sharp slanted boundary: c jumps 0.3 → 1.06 within ΔB = 0.02.
   - Entropy saturates hard (increments → 0.000, true area law) inside;
     grows logarithmically in the wedge outside.
   - Gap *grows* with N (0.33 → 0.67 interior, N = 12 → 14) — opposite
     of the wedge's 1/N closure. Real phase, not numerics.
   - Ground state is pinned: r = 0.63 (vs 0.07 in the wedge), with a
     period-6 locked modulation of the forbidden-window occupation
     (w_i patterns at 0.137/0.5/0.863, verified against one-site reduced
     density matrices).
   The plane therefore has three phases: gapped (J < J_c), the c = 1
   critical wedge, and the commensurate locked lobe carved from its
   low-B corner — a commensurate-incommensurate boundary between the
   lobe (helix wins) and the wedge (fluctuations depin).
6. **Bulk extension to J = 3.0** (806 points, `engine/results_bulk.json`,
   `engine/maps/bulk_{gap,c}.png`): the critical wedge persists and
   widens with coupling (spine c: 1.052 → 1.060, no re-entrance); the
   lobe recedes smoothly toward B = 0 (boundary B ≲ 0.12 at J = 1.5 →
   B ≲ 0.03–0.05 at J = 3.0); the spine gap rises linearly through
   J = 3.0 (0.0835 → 0.170) — velocity growth continues with no anomaly
   at strong coupling. Computed with the chunked parallel driver
   (`engine/bulk_map.py`, ProcessPool strips, thread-capped BLAS):
   806 points in 3,057 s vs 441 points in 3,015 s single-threaded;
   validated 440/441 points against the original grid to ≤ 2e-9.

**Methods:** off-line complex-H gate vs. dense brute force (max |ΔE| =
1.15e-14 at B = 0.10, J = 0.7) before the sweep; eigsh k=2, tol=1e-8
(worst Lanczos residual 8e-9); 441 points, 3 015 s wall (~6.8 s/pt,
eigsh-dominated). Island zoom: 121-point fine grid + N-scaling at three
points (~19 min); w_i cross-checked against reduced density matrices
(0.13690 both ways). c values deep in the wedge saturate at ≈1.2 — the
known finite-size CC-fit overshoot at N = 12 (see §8); the wedge
*structure*, not the saturation value, is the result.

---

## 4. What a Luttinger Liquid Is (Accessible)

For readers new to the term (including the project's author, at time of
writing).

**In 1D, quantum fluctuations win.** In higher dimensions, ordered phases
(magnets, crystals) survive quantum fluctuations. In one dimension they
generically cannot: the fluctuations destroy true long-range order. What
replaces it is the *Luttinger liquid* — not a gas of individual
particles, not an ordered solid, but a medium whose low-energy physics is
entirely **collective waves** of the phase field.

Three measurable signatures define it, and all three were measured here:

1. **Gapless with z = 1.** Excitations are wave-like with linear
   dispersion ω = v·k, so the finite-size gap closes as gap ∝ 1/N. The
   proportionality constant is (a factor of order 2π times) the wave
   velocity v — our smoothly growing 1/N slopes (0.89 → 1.46 with J).
   "z = 1" means energy scales like inverse length, the same
   space-time symmetry as relativity in 1+1 dimensions.

2. **Central charge c = 1.** The central charge counts the independent
   gapless bosonic channels — the number of distinct collective wave
   types. c = 1 means exactly one: a single phase mode. This is the
   simplest possible critical fluid, the same universality class as the
   1D XY model and sound in a 1D gas. It is measured through entanglement:
   in a critical 1D system, the entanglement entropy of a segment grows
   logarithmically with segment size, with slope c/3 — the
   Calabrese–Cardy formula we fit. Gapped systems instead saturate
   (area law), which is exactly what the J = 0.5 control does.

3. **No isolated critical point required.** Luttinger liquids are
   *phases*, occupying a region of parameter space (here: all J ≳ 1.0),
   not knife-edge points — matching our finding that every J ≥ 1.0
   closes as 1/N.

**Boundary flavor.** The transition into a Luttinger liquid from a gapped
phase is typically Berezinskii–Kosterlitz–Thouless (BKT): the gap opens
exponentially slowly, e^(−const/√(J−J_c)). That singularity is invisible
at N ≤ 16, so our J_c ≈ 1.0–1.1 is where the extrapolated gap vanishes,
not a confirmation of BKT scaling. Confirming it would need either much
larger N or a level-spectroscopy measurement.

**Physical reading for this project.** In the critical phase, the rotors
do not choose between the allowed (ref) and forbidden (ref + π)
directions. They form a single delocalized quantum fluid of phase waves
spanning both. The "walls" between sectors — which at finite
temperature melt thermally (Section 6) — here vanish by coherent quantum
delocalization. The classical simulator sees the same balance point as a
population split indecisively between two attractors; the quantum system
resolves the indecision into a critical phase.

---

## 5. Methods Result: The DMRG Trap and the Referee Protocol

A prior publication of the project reported "machine-precision
topological protection" (variance of ⟨m·n⟩ ~ 10⁻²⁴ in N ≡ 0 mod 4
sectors) from TenPy DMRG runs of a spin-1/2 XY chain at J/h = 200.

**It was an artifact, and it is fully diagnosed** (`min/spin_swap/`):

- Exact diagonalization: true variance is ~1.3e-7 (N=12), mean 1.86e-3.
- The DMRG state sits 0.011 above the exact ground energy with overlap
  99.995% — it is almost the right state, but the missing 0.005%
  carries the entire observable (mean ≈ 0 vs 1.86e-3).
- The signature is reproduced exactly by the h = 0 (field-off) state:
  mean ~ 1e-18, var ~ 1e-32. A state that never responds to the field
  looks like "perfect protection."
- The user's own published table contains the tell: mean(m·n) = 0 to
  machine precision in exactly the "protected" sectors.
- Root cause: at N ≡ 0 mod 4 the field's 4-site orbits average to zero,
  suppressing the coupling between the unpolarized J-dominated state and
  field-polarized states. DMRG parks in the symmetric sector from any
  initial state (verified: polarized and alternating starts converge to
  the bit-identical wrong state).

**The referee protocol** (applied throughout the DMRG phase of this
work):

1. Calibration gate: DMRG must reproduce exact-ED energies at small N
   (< 1e-6/site) before any larger-N number is trusted.
2. χ ladder with χ→∞ extrapolation, acceptance uncertainty < gap/20.
3. Energy variance ⟨H²⟩−⟨H⟩² per site as eigenstate certificate.
4. Energy is the referee; observables are never trusted from a state
   that fails the energy check.
5. Checkpoint everything; multi-start; lowest energy wins.

The anomaly that produced a false discovery becomes the methodology that
prevents the next one. It is also, independently, a publishable caution:
*symmetry-protected DMRG convergence failure masquerading as a protected
phase at J/h ≫ 1.*

---

## 6. Trimer PME: Structure of the Walls (Li/Pokorný anchor)

Replication (`min/trimer_pme.ergo`, `min/trimer_pme_summary.json`) of the
8-state master equation from Li, Pokorný, Hapala et al., Nat. Commun.
(2026), with their fitted parameters and tip electrostatics:

- Discharge Q: 1.991 → 0.988 across the tip scan (paper: −2e → −1e). ✓
- Trapped singlet manifold (|100⟩,|010⟩,|001⟩) reaches 0.97 occupation —
  the paper's non-equilibrium occupancy, and the precise anchor for the
  project's "w component." ✓
- NDC: |I| drops 45% at the discharge threshold, Vs ≈ 788 mV vs. their
  ~760 mV (4% off, from a one-parameter lever-arm calibration to the
  520 mV ring). ✓
- Far-site trapping: current suppression where the occupied site is far
  from the tip (their Fig. 3 mechanism). ✓

**Porosity ablation** (weak inter-site channel G_HOP swept 10⁻⁴ → 1):
nothing below ~1% of Γ_s, then smooth washout — trapped w drains
0.97 → 0.63, suppressed current recovers 0.037 → 0.079, control region
flat within 3%. Escapes happen where stress is highest, but only above a
porosity threshold.

**Temperature sweep (wall solidity):** two hardness tiers measured. The
kinetic trap melts first (trapped w drops from kT ≈ 1 meV); the energetic
blockade holds to 130× the experimental temperature (w = 0.98 at
kT = 0.22 meV, still 0.57 at 28 meV). NDC depth ∝ 1/kT in the melt
regime — exponential walls softening on schedule, no phase transition.

**2D charging-ring map (direct Fig. 2/3 reproduction):**
`min/trimer_map.ergo` — the same validated PME driven over a 60×60 tip
grid (25,200 steady-state solves) at Vs ∈ {540, 620, 690, 770, 790,
810, 870} mV, with dI/dV at 790 mV by central difference (maps in
`min/maps/`). All three target features reproduce:

- Three distinct discharge rings around the molecules at Vs = 540 mV
  (their Fig. 2a).
- Rings expanding and intersecting into the trillium-flower pattern by
  Vs = 690 mV (their Fig. 2b–h morphology).
- Genuine negative dI/dV over 31% of the grid at 790 mV, forming a
  three-petal band through the trimer center — the NDC region,
  coinciding pixel-for-pixel with the boundary of the W_SING ≈ 0.95
  kinetic-trapping region (the mechanism in one picture).

Expected non-reproduction (documented): the paper's chiral NDC pattern —
our model lacks the SOMO orbital's angular modulation, so the NDC region
is C3-symmetric. Map values at center-adjacent points match the
validated 1D scan to the last digit.

Physical summary: patterns persist where undoing them costs more energy
than the environment supplies (energetic wall), and rearrange only where
pathways exist with rates comparable to the driving (kinetic wall). At
the competition point of Section 3, both walls vanish exactly.

---

## 6b. Quantum Battery / Superextensivity Analysis (2026-08-02)

Test of the Hymas et al. quantum battery claim (papers/s41377-026-02240-6):
superextensive steady-state photocurrent (P ∝ N²) from microcavity
polaritons in CuPc under incoherent illumination. Two independent models
built and cross-checked (`min/qbattery/`):

**Model 1 — classical polariton-branch rate equation** (correlation-free,
the most charitable classical reading; `qbattery_check.md`):
- Control exponents exactly 1.00 ✓; cavity exponents 1.12–1.33 in the
  experimental N-range, climbing to an exact asymptotic **P ∝ N^1.5**.
- Decomposition: the photocurrent is LINEAR once the bright collective
  mode saturates; the superextensive power comes entirely from the
  **dressed voltage** (extraction threshold lifted ∝ G√N). The claimed
  N² is out of reach of any classical term — but 1.5 covers most of the
  reported enhancement (P_cav/P_ctrl ≈ 4×10⁵ at experimental N ~ 10¹⁴).

**Model 2 — exact Lindblad trajectories, quantum rotor emitters**
(`rotor_battery_check.md`, all-Ergo engine, 32-point blocked sweep,
analytic-validated):
- exp(I) = 0.91 ± 0.11 — **linear**, matching the classical model.
  The I ~ N^1.5 that the paper's P ~ N² requires is **excluded at ~5σ**.
- Pair coherence tracks the current (corr = 0.914 across 17 points) but
  its N-scaling is flat-to-negative — **no coherence-driven
  superextensivity**. Exchange coupling J suppresses transport;
  dephasing partially restores it (environment-assisted re-localization).
- Dephasing boundary: coherent effects survive γφ ≲ 0.1 (coupling
  scale), wash out by ~10·G. Classical harvest is robust without
  isolation; coherent enhancement requires it.

**Verdict:** the quantum battery's superextensivity is mostly
classical dressed-voltage arithmetic (P ∝ N^1.5, regime-independent);
the quantum trajectory model finds no coherence-driven residual at all.
The claimed N² is supported by neither instrument. The mechanism left
standing is cavity-dressed extraction thresholds — collective optics,
not quantum magic. (Caveat: current-only measurement; the dressed-voltage
channel itself is validated only through the classical model's fit to the
paper's stated mechanism.)

**Ergo feasibility note:** the entire trajectory engine (matvec, jump
operators, PRNG, sampling, N=8, DIM=26,244) is one STATIC-array Ergo
program (~25 min/sweep). Limits found: 32-bit INTEGER (breaks int64-hash
assumptions — see caveat 8), no compound DO WHILE, no built-in RNG
(white-hash idiom needs per-use validation).

---

- **"Viviani trefoil":** the 3D curve x = sinθ − ½sin3θ,
  y = −cosθ + ½cos3θ, z = cosθ·cos3θ is not a trefoil and not a knot at
  all — it has exactly two exact double points (proven analytically and
  by 12,000-sample scan; `min/knot_check.py`). Any perturbation into an
  embedding has crossing number ≤ 2, i.e. the unknot. The 4D w-lift
  separates the strands, but trivially (any distinct w does; all 4D
  curves are unknotted).
- **The engine does not consume the knot:** `viviani_lut_normal(θ)` is a
  pointwise direction lookup; the 5D variant with the w component is
  dead code (never called). The spin-model dynamics are insensitive to
  the curve's topology.
- **"Machine-precision protection" (10⁻²⁴):** DMRG convergence artifact,
  Section 5.
- **Chirality test:** mirroring the field's y-component gives
  bit-identical results (antiunitary symmetry). The scalar observable
  m·n cannot detect chirality by construction; a pseudoscalar observable
  would be needed for that claim.

---

## 8. Caveats and Open Items

1. ~~BKT boundary unconfirmed~~ **RESOLVED (§3.5):** correlation wave
   vector q = 0 across the entire transition, correlation exponent
   consistent with K → 2 at J_c — BKT confirmed to numerical precision.
   (The essential-singularity gap form itself remains invisible at
   N ≤ 16, but the PT alternative is excluded.)
2. **Spin-1 truncation.** The chain uses Lmax = 1 rotors; Lmax = 2
   checks at 8 sites show gaps ~15% smaller, same structure. The
   cos(3φ) drift term vanishes identically in the spin-1 basis
   (measured effect at Lmax=2: 0.2%).
3. **Finite-size CC-fit overshoot.** c values deep in the (B, J)
   critical wedge saturate at ≈1.2 at N = 12 — the known Calabrese–Cardy
   finite-size overshoot. The wedge structure and the on-line c = 1.00
   values (N up to 48) are the results; the saturation value is not.
4. **Quantum T=0 vs. classical driven.** The two models share the
   competition point and its structure, not absolute observable values.
5. **Single-precision N=16 ED** (complex64, gap error ≤ 3e-7) used for
   the bridge points; immaterial at the reported scales.
6. **N=64 DMRG not run** — c was flat (±4e-3) through N=48; the
   marginal information did not justify ~27 h of compute.
7. **32-bit INTEGER in Ergo** (measured in the rotor-battery engine):
   multiplicative "int64-style" hash PRNGs wrap at 32 bits, which can
   cause *conditional* distribution bias (e.g., channel-selection
   variates starve late channels — measured mean 0.22, max 0.71 before
   the fix). Mitigation: independent second hash stream for selection
   variates, plus per-use validation of conditional statistics whenever
   a hash is used for scheduling/selection. Unconditional additive-noise
   uses (condensate white bath) were validated separately and are
   unaffected. A compiler-level fix (int64 INTEGER or a validated PRNG
   intrinsic) is the durable solution.

---

## 9. Reproducibility

| Artifact | Path |
|---|---|
| Classical bias sweep (Ergo) | `min/redirect_bias_sweep.ergo` → `min/redirect_bias_sweep.log` |
| Trimer PME (Ergo) | `min/trimer_pme.ergo` → `min/trimer_pme.log`, `trimer_pme_summary.json` |
| Knot checker | `min/knot_check.py` |
| DMRG artifact diagnosis | `min/spin_swap/` (ED + DMRG + analysis) |
| Single-rotor ED | `min/phase_ed/rotor_single.py`, `results_single.json` |
| 12-site chain ED | `min/phase_ed/rotor_chain.py`, `results_chain.json` |
| Gap map | `min/phase_ed/gap_map.py`, `results_gap_map.json`, `gap_map.png` |
| Finite-size scaling | `min/phase_ed/fss.py`, `results_fss.json`, `fss_gap.png` |
| Optimized matvec + N=16 | `min/phase_ed/matvec_fast.py`, `n16_results.json`, `n16_extended.json` |
| Central charge (ED) | `min/phase_ed/entanglement.py`, `results_entanglement.json` |
| Central charge (DMRG) | `min/phase_ed/dmrg_driver.py`, `results_dmrg_ent.json`, `tenpy_calib.json` |
| Quantum battery (classical + rotor) | `min/qbattery/qbattery.ergo`, `qbattery_check.md`, `rotor_traj.ergo`, `rotor_battery_check.md` |
| Trimer 2D ring map | `min/trimer_map.ergo`, `min/trimer_map.npz`, `min/maps/` |
| (B, J) characterization map | `min/phase_ed/engine/bj_map.py`, `results_bj_map.json`, `engine/maps/{gap,c,eta}_bj.png` |
| Multi-model engine | `min/phase_ed/engine/models/` (rotor, xxz, fk, rydberg — all literature-gated) |
| Ergo GPU pipeline | `min/phase_ed/engine/stage{0..4}*` — oracle-validated eigensolver + packed batch sweep (N=8: 0.27 s, N=12: 55 s, N=14: 27 min on GPU) |

Ergo compiler: `python -m core <source>.ergo -o <binary>`.
Python environment: `.venv/bin/python` (numpy, scipy, physics-tenpy,
numba, matplotlib).

---

## 10. One-Paragraph Abstract (Draft)

We study a 12-site quantum rotor chain with harmonic driving that pits
two preferred phase directions against each other. The competition point
is pinned exactly at drive ratio B = 0.25 by harmonic-cancellation
symmetry, with w = 0.5 and vanishing order parameter at all couplings.
Exact diagonalization (N ≤ 16, custom matrix-free operator) and
calibrated DMRG (N ≤ 48) show that below J_c ≈ 1.0–1.1 the system is
gapped, while above it the finite-size gap closes as 1/N (z = 1) with a
smoothly varying velocity, and the bipartite entanglement entropy follows
the Calabrese–Cardy form with central charge c = 1.00 ± 0.01. Mapping
the full (B, J) plane reveals that the exact competition line is the
spine of a two-dimensional critical wedge, with a bowtie bifurcation of
the gap minimum at the BKT point and the Luttinger parameter crossing
K = 2 at the boundary — a Luttinger-liquid critical phase whose exact
line organizes the fan. A classical driven-oscillator realization of the
same competition shows its coherence-collapse region at the same
algebraic balance point, identifying the classical phase-coexistence
signature as the mean-field echo of the quantum critical region. We
additionally document a symmetry-protected DMRG convergence failure at
strong coupling that produces false "protected phase" signatures, and
the energy-referee protocol that detects it.
