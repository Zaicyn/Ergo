# LL ↔ string bridge — findings

The rotor-chain Luttinger liquid (min/FINDINGS.md §3: c=1, z=1, BKT,
K ≈ 1.8–2.2) mapped onto the closed-string language of the glueball
flux tube (min/glueball/GLUEBALL_FINDINGS.md Stage 2). Question: does
the LL tower realize the string spectrum, and does the string picture
calibrated on the rotor say anything back about the glueball
estimates? Model: ternary rotor chain at the exact competition point
B = 0.25 (field term V = K_PHASE − B·K_BIAS = 0), J = 1.5 (clean
critical phase). ED referee throughout; every driver run twice,
byte-identical. Heavy ED is Ergo-engine-first: scipy eigsh only for
N ≤ 14 cross-validation, GPU Ergo engine (Inc-2 machinery,
`min/phase_ed/gen_ed_matvec.py`, new `tower` variant — deflated power
iteration with per-sweep Gram–Schmidt + SECT overlap matrices for
sector ID) for N = 16/17. GPU regression gate N=8 E0 = −2.8591343125
run first — passes (CPU and SPIR-V builds identical to print
precision); tower variant validated at N=8 against scipy to all 10
printed digits for all 7 states.

## Stage 1 — Casimir + tower (`rotor_tower.py`, GPU `tower` variant)

scipy ED (N = 8, 10, 12, 14, k=8, tol 1e-12, deterministic ARPACK
seed; sectors resolved by cluster-diagonalizing the exact symmetries
M = Σm_i and translation T):

**(a) Casimir / central charge.** E₀(N) = ε∞·N − b/N fit:
ε∞ = −0.6167978771, b = 0.7248614971, max|resid| = 6.8e-5. Velocity
from the M=0, p=±2π/N phonon pair: v = 1.3562 (drifts 1.340→1.367
from N=8→14). Casimir c = 6b/(πv) = **1.0208** — vs the entanglement
route at J=1.5 (1.044±0.010 N=12 ED, 1.034±0.008 N=16 ED, ~1.00
DMRG): **cross-method agreement, c=1 within ~2%**, two independent
physical routes (ground-state energy vs entanglement entropy).

**(b) Tower** (x = ΔE·N/2πv, all N): winding pair M=±1 at x =
0.139; M=±2 pair at x = 0.550 (= 4·x_wind = 0.555 within 1% — the
quadratic winding spectrum); phonon pair M=0, p=±2π/N at x =
0.988→1.008, converging to the LL integer 1 from below with N. LL
structure confirmed at the few-% level at these sizes.

**(c) K three-way.** Winding route: x_wind = 0.1388 → **K = 1.801**
(1.805→1.796 N=8→14, flat). η-route (FINDINGS §3.5): K = 1/(2η) ≈
1.8 (J=1.0) → 2.0–2.2 (J≥1.5). BKT universal: K = 2. The winding
route sits at the low edge of the η band at this J — consistent
within combined tolerances (η's own uncertainty maps to ±0.2 on K);
no headline disagreement, the residual ~10% spread between the
winding and η routes at J=1.5 is recorded, not averaged over.

**GPU large-N verification (Ergo engine, tower variant, J=1.5,
SPIR-V on the RTX 2060, both runs byte-identical):**

- N=16 tower (3 states): E₀ = −9.9142125030 vs the Casimir fit's
  prediction from N ≤ 14 (−9.914069): agreement 1.4e-4, and the GPU
  value is a power-iteration upper bound at the 3000-iter cap, so the
  true value sits even closer. First excited pair E₁ = E₂ =
  −9.839957/−9.839952 (degenerate within 5e-6, the power-iteration
  convergence level): gap 0.07426, exactly the N=16 J=1.5 gap 0.0743
  documented in FINDINGS §3.2 — now identified as the winding sector.
  x_wind(N=16) = 0.1394 → K = 1.793, continuing the N=8–14 trend
  (1.805→1.796→1.793). The large-N engine confirms the small-N LL
  analysis; no new physics appears at N=16.
- N=17 E₀ (resident variant): E₀ = −10.5283882130 vs the Casimir
  fit's prediction from N ≤ 14 (−10.528203): agreement 1.9e-4
  (1.8e-5 relative), again a power-iteration upper bound. The
  ε∞·N − πv/(6N) form, fitted on N = 8–14, predicts both GPU points
  within the iteration-cap accuracy — the Casimir law holds out to
  the largest N the engine reaches.
- Machinery note (deferral): the tower variant exposed a vk_host
  frame-batch bug — kernels of a new state replay with ST bindings
  recorded before the previous state's store landed, so deflation
  silently read stale state vectors (all states collapsed to the
  ground energy on GPU; CPU builds correct). Workaround baked into
  the generator: an in-loop readback print after the first GS
  reduction at ITER=2 forces the drain + re-record (position and
  iteration both matter — measured). The SECT overlap of the LAST
  state still reads stale zeros on GPU (same bug, one drain short);
  sector ID at N=16 therefore rests on the exact degeneracy + gap
  continuity with N ≤ 14, which is unambiguous. A proper runtime fix
  is the deferral.

## Stage 2 — LL → string map (`ll_string.py`)

Tower written in closed-string form E(L) = σ_eff·L + (2πv/L)(x −
(d−2)/12) with d−2 = 1 transverse mode. **Single-σ_eff test:** with
the LL-quantized x values (0; M²/4K winding; 1 phonon), every
identified level at every N solves for the same σ_eff: spread 0.0021,
rms 5.1e-4, worst deviation from ε∞ 1.8e-3 — the compact-boson
requirement (one σ_eff for all levels) **holds** at the tower's own
accuracy. No deviation finding.

**Casimir mode count (explicit):** rotor −πv/(6L) = −(2πv/L)(1/12) —
one transverse mode, c=1 compact boson, i.e. the D=2+1 string.
QCD Lüscher −πv(d−2)/(6L) = −πv/(3L) with d−2=2 transverse modes
(D=3+1). The factor of 2 is exactly the transverse-mode count; the
rotor chain realizes the one-mode member of the same family.

**σ_eff interpretation:** σ_eff = ε∞ = −0.6168 < 0 — a bulk vacuum
energy density, NOT a confining tension. The critical phase has
vanishing kink tension (kink condensation *is* the criticality);
winding gaps close as 1/L instead of growing as σL. The string FORM
carries over exactly; the tension's sign and meaning do not.

## Stage 3 — glueball connection

**Calibration.** The rotor's σ_eff = ε∞ = −0.6168 is a bulk vacuum
density (negative, non-confining — see Stage 2); the flux tube's
σ = 0.185 GeV² is a physical confining tension. There is no honest
numerical map between the two *tensions* — what transfers is the
structure: one shared closed-string formula
E(L) = σL + (2πv/L)(x − (d−2)/12), with the rotor supplying the
d−2 = 1 member measured to few-% accuracy end-to-end (Casimir,
quantized tower, winding sector), and QCD living at d−2 = 2. The
rotor chain is the calibrated testbed for the *formula*; σ = 0.185
GeV² remains the flux tube's own independent input.

**Does the LL analysis correct the glueball estimates?** It does not
move the numbers (flux-tube prescription (a) E² = 4πσn stands:
0⁺⁺/2⁺⁺ = 1.525 GeV, 0⁻⁺ = 2.156 GeV), but it settles *why* the
prescriptions sorted the way they did. Glueball Stage 2's prescription
(c) — E(L) = σL + (4πn − π/3)/L minimized over loop length L — came
out ~2× too heavy and was documented as a failure mode. The rotor
tower shows the mechanism: in the measured LL spectrum the Casimir
term rides on the bulk energy with the level content quantized in x
at spacing 2πv/L; the tower states are NOT σL-minimizers — the
physical tower is the large-loop limit where E ≈ σL sets the scale
and ΔE² = 4πσ per phonon, exactly prescription (a). Treating L as a
variational coordinate (c) double-counts the zero-point/Casimir piece
against the phonon tower and manufactures a spurious bound-state
condition. The LL side supplies this as a *parameter-free* statement:
the Lüscher coefficient and the tower spacing fall out of the rotor
measurement with no fit beyond v and K.

**Boundary.** Both sides are model-level. c = 1 here vs d−2 = 2
transverse modes for the QCD string — the factor-of-2 Casimir
mode-count is documented, not bridged. The rotor's critical phase has
no confining tension (that is why it is critical); the glueball flux
tube is nothing but tension. And the quantum numbers don't map: the
rotor tower is labeled by (M, p) of a 1D chain, the glueball tower by
J^PC of phonon angular momentum — the bridge is the spectral FORM,
not a state-by-state dictionary. The GPU engine's role was large-N
verification (N=16 tower, N=17 E0, both byte-identical across runs);
its generator now has a deflated-tower variant, and the vk_host
frame-batch staleness bug it exposed is recorded as the machinery
deferral.

## Files

- `min/llstring/rotor_tower.py` — Stage 1 scipy driver (N=8–14;
  run twice, byte-identical; writes `tower_results.json`).
- `min/phase_ed/gen_ed_matvec.py` — added the `tower` variant
  (deflated power iteration + SECT sector matrices; N=8 validated
  against scipy to print precision).
- `min/llstring/ll_string.py` — Stage 2 string-map driver (run
  twice, byte-identical).
- `min/llstring/LLSTRING_FINDINGS.md` — this file.
