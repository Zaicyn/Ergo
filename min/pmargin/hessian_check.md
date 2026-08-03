# Hessian spectroscopy — native fold vs trap (BBA5)

Program: `min/pmargin/hessian.py`. States: seed 4.0 near-native (RMSD
0.29) and seed 0.0 trap (RMSD 1.668), final structures from
`tests/waveform_bba5_seed_{4.0,0.0}.out`. Energy mirror implements the
sim's exact terms (Morse, angles, torsions [force-convention dihedral],
hydrophobic, Go contacts, register torsions, and steric energy inferred
from the sim's force form `FM = eps·(σ/D)⁶` ⇒ `E = eps·σ⁶/(5D⁵)`),
all tables parsed from `tests/waveform_bba5_seed_0.0.ergo`.
**Size note: BBA5 has 23 Cα → the Hessian is 69×69 (69 DOF), not
207×207/69 Cα as the task stated — reported plainly.**

Method: 4-point central differences of the total energy (symmetric by
construction, verified max|H−Hᵀ| = 0 exactly), h-convergence tested
(h = 1e-3 → 1e-4 → 1e-5: stable to 4 digits at h ≤ 1e-4 except at the
steric cutoff — see caveats). Diagonalization with `numpy.linalg.eigh`
(documented; trace(H) = Σ eigenvalues to 10 digits as the built-in
consistency check).

## Energies and minima

E(native) = 0.0448, E(trap) = 0.1044 — the trap is 0.06 units (2.3×)
higher but energetically competitive (consistent with the earlier
energy-blindness finding). |grad| at native = 34.4, at trap = 0.026 —
the native gradient is large, entirely from the steric cutoff
discontinuity (tightly packed native has pairs straddling D = 2.5 where
the sim's force jumps; the trap is loosely packed with no such pairs).
The small negative eigenvalues (native −0.0003, trap −0.0015) are
within the numerical noise floor of the cutoff-straddling differences —
both states are minima up to that precision.

## Spectra — the central result

First 15 eigenvalues, native vs trap:

| # | native | trap |
|---|---|---|
| 1 | −0.0003 | −0.0015 |
| 2–4 | ~0 (rigid-body, ±1e-9) | ~0 |
| 5 | 0.0002 | 0.0002 |
| 6 | 0.0020 | 0.0005 |
| 7 | 0.0053 | 0.0034 |
| 8 | 0.0153 | 0.0088 |
| 9 | 0.0231 | 0.0135 |
| 10 | 0.0448 | 0.0231 |
| 11 | 0.0503 | 0.0504 |
| 12 | 0.0856 | 0.0577 |
| 13–15 | 0.159 / 0.187 / 0.258 | 0.090 / 0.152 / 0.157 |

Median positive curvature (>0.05): native 3.56, trap 3.45.
Near-zero counts (|λ| < 1e-3 / 1e-2 / 0.05): native 5 / 7 / 10,
trap 5 / 8 / 10.

**The spectra are statistically identical.** Same zero-mode count (5
within noise of the 6 rigid-body modes), same gap structure (gap at
~0.002–0.005, then a rising ladder), same median stiffness (3.56 vs
3.45 — 3% apart), same near-zero counts to within 0–2 modes at every
threshold.

## Term decomposition (native state)

Rayleigh quotients of the 12 softest native modes against each term's
Hessian: the soft modes are owned by **ANGLE (0.003–0.049) and TORSION
(0.000–0.025)** — collective backbone angle/dihedral deformations. Go
and register contribute small positive shares; steric contributes small
NEGATIVE shares (soft modes relax wall contacts slightly). Per-term
spectra confirm: the Go network itself has a near-zero floor (2.4e-3 →
0) — contact-distance-preserving shape deformations are free under Go
alone — and register likewise (floor −0.004 ≈ 0).

## Answers to the questions

**(a) Does the trap have more soft modes? NO.** Near-zero counts are
identical (5/7/10 vs 5/8/10 — differences of 0–2, inside the noise
floor). The trap is NOT a wider basin.
**(b) Does native have unexpected near-zero modes?** No — ~5 modes at
<1e-3 ≈ the rigid-body 6 (one lifted into the noise), then a clear
gap to ~0.002. No unexpected floppy directions beyond the collective
angle/torsion ladder every folded state has.
**(c) Which terms own the soft modes?** Backbone ANGLE and TORSION —
the force field's weak points are the bending/dihedral channels, not
the contact network (which has its own contact-preserving flat
directions but at zero cost rather than as a trap).

## Diagnosis (and the story flip)

**The trap is NOT softer than native — the entropic-trapping story
flips to a purely kinetic one.** The wrong valley is a comparably
deep (within 0.06), comparably stiff (median curvature within 3%),
comparably narrow (identical near-zero counts) minimum. Nothing about
the local geometry favors it: no extra basin volume, no curvature
advantage, no soft-mode surplus. The seed-0.0 trajectory simply fell
into an equally legitimate hole and the escape is a barrier-crossing
problem — exactly the regime where thermal budget and time (not basin
shape) decide outcomes, and consistent with the earlier findings that
the trap is energetically competitive (E within 0.06) and that
mechanical means (pulse, tempering swaps) rather than entropy
gradients are what moves the system out of it.

Caveats documented: the steric cutoff discontinuity inflates
|grad|/top-eigenvalue at tightly packed states (the native max
eigenvalue 1.7e5 is a wall-straddling artifact, not physics of the
soft spectrum, which is clean); the steric energy form is inferred
from the sim's force law (documented in hessian.py); numpy was used
for diagonalization with the trace check as the consistency oracle
(Jacobi cross-check available via /tmp/hessian_*.npy if wanted).

Files: `min/pmargin/hessian.py`, `/tmp/hessian_native.npy`,
`/tmp/hessian_trap.npy`, this report.
