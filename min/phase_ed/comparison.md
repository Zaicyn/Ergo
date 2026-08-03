# Quantum counterpart of the classical bias sweep — comparison

Classical reference: `min/redirect_bias_sweep.log` (w_peak column), 12-node ring,
dφ/dt = 1.0 + 0.5·sin(ref−φ) + B·2.0·sin(ref+π−φ) + 0.1·sin(3φ).

Quantum model: single rotor H = p²/2I − K_PHASE·cos(φ−ref) − B·K_BIAS·cos(φ−ref−π)
+ (K_DRIFT/3)·cos(3φ), I=1, exact diagonalization in |m⟩, m=−20..20
(observables averaged over the 12 node refs; spread from the cos3φ term ≤ 9e-4).
Chain: 12 sites, m_i ∈ {−1,0,1}, matrix-free LinearOperator + eigsh k=4.

Files: `rotor_single.py`, `results_single.json`, `rotor_chain.py`,
`results_chain.json`, `chain_run.log`.

## Validation status — PASSED

- Projector cross-checked against real-space integration of |ψ(φ)|² (agrees to grid error).
- Lmax=20 is fully converged: |w(Lmax=30)−w(Lmax=20)| ≤ 3e-16 at B = 0, 0.25, 0.5, 1.
- Chain at J=0 factorizes exactly: max |E0_chain − 12·E0_single(Lmax=1)| = 3.2e-14,
  max |w_chain − w_single| = 8.3e-15 over all 11 B points (eigsh tol 1e-12).

## Headline curves

| B | classical w_peak | quantum w (Lmax=20) | quantum w (Lmax=1) | chain J=0 | chain J=0.5 |
|------|------|------|------|------|------|
| 0.00 | 0.338 | 0.116 | 0.132 | 0.132 | 0.083 |
| 0.20 | 0.474 | 0.377 | 0.378 | 0.378 | 0.238 |
| 0.25 | 0.506 | 0.5000 | 0.5000 | (0.500) | — |
| 0.30 | 0.536 | 0.623 | 0.623 | 0.623 | 0.762 |
| 0.50 | 0.663 | 0.884 | 0.868 | 0.868 | 0.917 |
| 1.00 | 0.910 | 0.977 | 0.938 | 0.938 | 0.942 |

## 1. Does quantum w(B) accumulate like the classical curve?

Yes — a smooth, monotonic sigmoid, steeper than the classical one. Both curves
cross w = 0.5 at the same place: quantum w(0.25) = 0.500000000000000 (exact, by
the symmetry below), classical w_peak(0.25) = 0.506. The midpoints coincide.
The ranges differ: quantum spans 0.116 → 0.977 (Δ = 0.86), classical
0.338 → 0.910 (Δ = 0.57). Slope at the midpoint: quantum ≈ 2.5 per unit B,
classical ≈ 0.62 — the quantum transition is ~4× sharper. The classical curve
starts high (0.34 at B=0) because it is a driven dynamical steady state
(OMEGA_BASE rotation + relaxation), not a ground state.

## 2. Structure at B = 0.25

Exact and exact-looking, respectively:

- The first harmonic −(K_PHASE − B·K_BIAS)·cos(φ−ref) vanishes at B = 0.25
  (0.5 − 2·0.25 = 0). The code uses the unsimplified two-term form; the
  cancellation appears in the spectrum, not by construction.
- Gap minimum: fine scan (ΔB = 0.01) gives min gap = 0.4999 at B = 0.25
  (Lmax=20). At that point only the kinetic term and the weak (K_DRIFT/3)cos3φ
  remain; the gap is the free-rotor m=0→±1 spacing 1/2I = 0.5, slightly
  reduced by drift hybridization.
- Order parameter r(B) = |<e^{i(φ−ref)}>| hits exactly 0 at B = 0.25 (the
  surviving cos3φ potential is 3-fold symmetric, so <e^{iφ}> = 0 by symmetry).
  r falls 0.61 → 0 → 0.61 symmetrically about the crossing.
- |ψ(φ)|²: single peak at φ = ref for B < 0.25; at B = 0.25 it is nearly flat
  with a slight 3-fold modulation (max/min = 0.162/0.157 — the three drift
  minima); single peak at φ = ref+π (the *center of the forbidden window*)
  for B > 0.25. The state tunnels/delocalizes through the competition point
  rather than sliding.
- Classical sim: coherence_peak crashes to 0.0118 at bias 0.25 (dip over
  0.20–0.30). The quantum model reproduces the competition point at exactly
  the same bias, B = 0.25, with r = 0 as the sharp version of the classical
  coherence crash.

## 3. What quantum mechanics changes

- **Zero-point floor.** w(B=0) = 0.116 even though the potential minimum sits
  at the center of the *allowed* window: the ground state has irreducible
  zero-point width (harmonic estimate σ ≈ 0.84 rad). A noiseless classical
  particle would give w = 0.
- **Exact symmetry.** With the drift term, w(B) = 1 − w(0.5 − B) holds to
  ~4e-4 (Lmax=20, ref-averaged); without drift (and exactly in the spin-1
  chain, where cos3φ has no matrix elements) it is exact, as is w(0.25) = 1/2.
  The classical curve only roughly shows this (0.338 vs 1−0.910 = 0.090 —
  it does not have the symmetry; dynamics breaks it).
- **Sharper but smooth transition.** The single-rotor crossover is analytic
  (no true transition at finite size), ~4× steeper than the classical curve.
  Inertia controls the sharpness: I = 2 gives w = 0.044 → 0.994 (nearly
  classical), I = 0.5 gives 0.235 → 0.932 (very quantum). I = 1 is between.
- **Truncation error (spin-1).** |w(Lmax=20) − w(Lmax=1)| is 0.016 at B = 0,
  0.000 at B = 0.25, and max 0.039 at B = 1. So the chain numbers carry a
  few-percent systematic, worst deep in the biased regime.
- **Drift term vanishes in the chain basis**: <m±3|cos3φ|m> needs |m±3| ≤ 1,
  impossible for m ∈ {−1,0,1}. The chain therefore sees a strictly 2-fold
  problem; quoted above where this matters.

## 4. Does J = 0.5 change w(B)?

Materially, yes — it sharpens the transition:

| B | w (J=0) | w (J=0.5) | gap (J=0) | gap (J=0.5) |
|-----|------|------|------|------|
| 0.0 | 0.132 | 0.083 | 0.683 | 0.720 |
| 0.2 | 0.378 | 0.238 | 0.510 | 0.251 |
| 0.3 | 0.623 | 0.762 | 0.510 | 0.251 |
| 0.5 | 0.868 | 0.917 | 0.683 | 0.720 |
| 1.0 | 0.938 | 0.942 | 1.340 | 1.489 |

Neighbor coupling aligns the rotors: below the competition point w is pushed
*down* (0.132 → 0.083 at B=0), above it *up* (0.868 → 0.917 at B=0.5). r
increases everywhere (0.577 → 0.655 at B=0). Most notably the gap at the
competition point collapses from 0.510 to 0.251 (B = 0.2/0.3 bracketing 0.25)
— collective softening, the finite-N precursor of a genuine quantum phase
transition at B = 0.25 that the independent-particle classical sim cannot have.
E0(B) and gap(B) remain exactly symmetric about B = 0.25 at J = 0.5 (the
φ_i → φ_i + π symmetry survives the cos(φ_i − φ_{i+1}) coupling).

## 5. Verdict

w-accumulation survives quantization cleanly. With w defined identically on
both sides (weight/fraction with |φ−ref| > π/2), the quantum ground state
reproduces the classical phenomenology: monotonic accumulation from ~0.1 to
~0.98, midpoint and coherence collapse at the same bias B = 0.25, and a
competition point that is if anything sharper than the classical one.

What is genuinely new in the quantum version:

1. An irreducible zero-point floor under w (0.116 at B = 0) — fluctuation
   weight with no classical source.
2. Exact symmetry w(B) = 1 − w(0.5−B) and r(0.25) = 0; the classical
   "coherence crash" becomes a symmetry-enforced zero of the order parameter,
   and at that point the state is a coherent 3-fold-delocalized wavefunction
   rather than a mixture of confused particles.
3. Collective gap softening under coupling (0.51 → 0.25 at J = 0.5), i.e. the
   quantum model is on the road to a true phase transition; the classical
   independent-particle sim has no analog.

Caveat: the quantum w is a ground-state (equilibrium, T=0) property while the
classical w is a driven dynamical steady state (OMEGA_BASE = 1 rotation plus
relaxation). Same observable definition, different ensembles — absolute values
should not be expected to match, and they don't (worst at B = 0: 0.116 vs
0.338). The robust shared content is the location and nature of the
competition point, not the curve normalization.
