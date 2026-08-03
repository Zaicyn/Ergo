# Protein Margin — Force-Field Reference (for reweighting work)

Extracted verbatim from `tests/waveform_bba5_96k.ergo` and the validated
packed variants. All parameters with their current values. This is the
complete term inventory; the reweighting knobs are marked ★.

---

## Term 1 — Backbone Morse bonds (chain integrity)

```
E_bond(i) = BACKBONE_D · (1 − exp(−MORSE_A·(D_i − BACKBONE_R0)))²
FM      = −2·BACKBONE_D·MORSE_A·(1−E)·E · FORCE_SCALE,   E = exp(−MORSE_A·(D−R0))
```
- `BACKBONE_R0 = 1.52` (equilibrium Cα–Cα distance, model units)
- `BACKBONE_D  = 1.4`  ★ (well depth — chain stiffness)
- `MORSE_A     = 1.0`  ★ (well width)
- **Plateau:** no restoring force past D ≈ 4 (the fragmentation artifact —
  §9.4/9.5). Adopted fix: harmonic continuation `+K_LR·(D−4.0)²` for
  D > 4.0, with **K_LR ≈ 0.3 ± 0.2** (§9.5; K_LR = 1.0 spawns new traps).

## Term 2 — Backbone angle bending (local geometry)

```
E_angle(i) = RES_ANGK(i) · (cos θ_i − cos(RES_ANGT0(i)))²
θ_i = angle(Cα_{i−1}, Cα_i, Cα_{i+1}),  targets = native crystal angles
```
- `RES_ANGK = 0.3` ★ (uniform; per-residue targets from crystal)

## Term 3 — Backbone torsion/dihedral (local chirality)

```
E_torsion(i) = 2·RES_TORSK(i) · (1 − cos(φ_i − RES_TORSP0(i)))
F          = −2·RES_TORSK(i) · sin(φ_i − φ0)
φ_i = dihedral(Cα_{i−1}, Cα_i, Cα_{i+1}, Cα_{i+2}),  targets = native
```
- `RES_TORSK = 0.2` ★ (uniform; per-residue targets from crystal)
- Note: BBA5's rescue used position-selective TORSK 0.2→1.0 at res 10, 15
  (§9.3) — per-residue reweighting is proven to work for bending traps.

## Term 4 — Hydrophobic attraction (core packing, implicit solvent)

```
FM(i,j) = −HYDRO_STRENGTH · H_i · H_j · exp(−HYDRO_ALPHA·(D_ij − HYDRO_R0))
   for D_ij < HYDRO_CUTOFF, both residues hydrophobic (H > 0)
```
- `HYDRO_STRENGTH = 0.0020` ★
- `HYDRO_R0 = 4.0`, `HYDRO_CUTOFF = 8.0`, `HYDRO_ALPHA = 1.0`
- `H_i = RES_HYDRO(i)` — per-residue hydrophobicity weights ★
  (this is the implicit-solvent free-energy term; its balance against the
  local geometry terms is a prime reweighting suspect for the
  field-vs-crystal minimum mismatch, §9.8)

## Term 5 — Go native contacts (the pre-encoded map)

```
E_go(i,j) = NATIVE_K · (D_ij − NATIVE_R0(i,j))²   (harmonic)
FM        = −2·NATIVE_K · (D_ij − R0)
   for native pairs: Cα–Cα < 6.5 Å in the crystal
```
- `NATIVE_K` ★ (contact depth; balance vs BACKBONE_D stiffness and vs
  hydrophobic drive)
- `NATIVE_R0(i,j)` — per-pair crystal distances (not a knob — the oracle)
- Known degeneracies: fragmentation blind spot (§9.4), interface
  orientation blindness (§9.6–9.8)

## Term 6 — Steric repulsion (excluded volume)

```
FM(i,j) = STERIC_EPS · (STERIC_SIG / D_ij)^6   for |i−j| ≥ 4, D < STERIC_CUT
```
- `STERIC_EPS`, `STERIC_SIG`, `STERIC_CUT` ★ (hard cutoff — the source of
  the finite-difference Hessian cutoff artifacts, §9.4; a C¹ taper is the
  documented fix for analysis work)

## Term 7 — Register torsions (β-sheet chirality signal)

```
E_reg(q) = REG_K · (φ_q − φ_q^native)²   over cross-strand quartets
```
- `REG_K = 0.5` ★, activated from `EXTRA_TORSIONS_FROM = 1200` (late
  activation is essential — early activation rigidifies wrong register)
- The chirality/orientation mechanism that fixed wrong-face β packing
  (TRANSFERABILITY.md); its cross-domain analog FAILED for interfaces
  (§9.6–9.8 — orientation degeneracy is deeper than restraint type)

## Term 8 — Phase dynamics (Kuramoto layer, orthogonal to positions)

```
θ_i ← θ_i + ω_i·DT + COUPLING_K·sin(θ_mean − θ_i)·DT + phase_noise
```
- `COUPLING_K = 5.0` ★ — collective phase locking drive
- Phase-noise hash (legacy) / white-hash bath (validated replacement, §8.2)

## Term 9 — Thermal drive + integrator

```
RES_V(I) += THERMAL_CURRENT · noise(I, FRAME) · DT
velocity *= VELOCITY_DAMP each frame
```
- `VELOCITY_DAMP = 0.9` ★ (effective friction — sets basin-escape timescale)
- `FORCE_SCALE = 6.0` ★ (global force multiplier — integrator timescale,
  not physics per se, but interacts with the schedule)
- Noise: white-hash (validated; the old quasi-periodic slosh drive is
  superseded, §8.2)

---

## The reweighting-relevant balance structure

The field's minimum ≠ crystal (§9.8). The competing drives:

- **Local stiffness** (Terms 1–3: Morse, angles, torsions) — holds native
  local geometry.
- **Contact drive** (Term 5: Go map) — pulls toward native long-range
  contact pattern. Pre-encoded, degenerate (§9.4, §9.6).
- **Packing drive** (Term 4: hydrophobic) — pulls toward compact cores,
  geometry-agnostic. The leading suspect for pulling the minimum off
  crystal when it outvotes local terms.
- **Excluded volume** (Term 6) — sets the repulsive wall.

Frustration lives where these disagree: thousands of native-targeted terms
(2, 3, 5) vs the geometry-agnostic packing term (4) vs excluded volume
(6). Any reweighting that shifts the field minimum toward crystal must
either weaken the packing drive, strengthen local stiffness, or break the
contact-map degeneracies — and the §9.3 result (position-selective torsion
reweighting rescues without side effects) is the proof that *selective*,
not global, reweighting is the viable path.
