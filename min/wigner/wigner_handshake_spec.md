# Wigner handshake instrument — spec (Stage W)

Purpose: emit the Wigner quasi-probability map W(z, p) along the bond axis
for the handshake campaign's two-center states, so the radial interference
patterns in and around the binding region can be *seen*, not inferred.
H₂⁺ σg/σu first (analytic oracles exist); H₂ 1-RDM and the DF radial
(F, G) densities are follow-ons on the same block.

## Definition (locked)

Reduced coherence along the bond axis z (nuclei at z = ±R/2):

    rho(z, z') = ∫∫ dx dy  ψ*(x, y, z') ψ(x, y, z)        (trace = 1)
    W(z, p)    = (1/π) ∫ dy'  e^{2 i p y'} rho(z − y', z + y')

- This is the transverse-averaged 1D Wigner: it keeps the two-center
  coherence (the handshake) while averaging transverse structure.
- ∫∫ W dz dp = 1 exactly (normalization oracle).
- Pure-state midpoint identity (exact oracle, both parities, any R):
      W(0, 0) = (1/π) ∫ rho(−y, y) dy = ±1/π
  (+ for σg, − for σu — the antisymmetry node is exactly −1/π).

## What the mirror shows (analytic 1s combos, zeta = 1)

- σg: positive blob at small R; negative fringe pockets flank p = 0 at
  the midpoint from R ≈ 2 outward; fringe trough at p ≈ ±π/(R + 0.4),
  depth growing 0.003 (R=1) → 0.19 (R=6); cat limit as R → ∞.
- σu: the node pocket — deep negative eye centered exactly at (0, 0),
  W(0, 0) = −1/π, present at every R; the fringing moves out into the
  lobes as R grows.
- Negativity budget ν is dominated by cusp/tail structure and is NOT a
  stable grid observable at dx = 0.25 — excluded from the oracle set.

## Oracle table (mirror: 64×64×256 grid, z ∈ [−8, 8], transverse ±6)

Tolerances vs the ergo grid engine: W00 to 2e-3 (grid budget), fringe
position p_f to 5%, fringe depth to 15%, visibility to 20% (grid dx=0.25
smears p-structure at p·dx ≳ 1 — fringe pocket at R ≤ 2 sits at p ≈ 1.3,
near the grid's p-resolution edge; treat R ≤ 1.401 fringes as qualitative).

| R | par | W(0,0) | p_fringe | W_fringe | visibility |
|---|---|---|---|---|---|
| 0.5 | g | +0.318123 | ±2.983 | +0.000765 | 0.0024 |
| 1.0 | g | +0.318156 | ±2.420 | −0.002905 | 0.0091 |
| 1.401 | g | +0.318178 | ±1.785 | −0.008278 | 0.0260 |
| 2.0 | g | +0.318196 | ±1.296 | −0.022833 | 0.0718 |
| 3.0 | g | +0.318194 | ±0.905 | −0.062236 | 0.1956 |
| 4.0 | g | +0.318170 | ±0.685 | −0.110358 | 0.3469 |
| 6.0 | g | +0.318123 | ±0.489 | −0.192120 | 0.6039 |
| 0.5–6 | u | −0.317047 … −0.318073 | 0 (node) | = W(0,0) | 4.68 → 1.48 |

(1/π = 0.3183098861837907; W00 deviations from ±1/π are mirror truncation,
not physics.)

## Ergo block (to bolt onto h2p.ergo after each converged orbital)

1. Accumulate RZ(z, z') on cell-center z layers (NZ = 128, z index = KC):
   for each interior (IC, JC), for each (KC, KC2):
   RZ(KC, KC2) += PSI(i,j,k)·PSI(i,j,k2)·DX²  — 1.3e8 mults, seconds in C.
   STORAGE: RZ(128,128) STATIC = 131 KB. Symmetric: fill KC2 ≥ KC, mirror.
2. DFT (no FFT intrinsic — direct sum): for each z row KC,
   W(KC, IP) = (DZ/π) Σ_m RZ(KC−m, KC+m)·COS(2·P(IP)·m·DZ),
   m bounded by edge distance; NP = 256 cell-centered p-values spanning
   the FULL Nyquist range [−π/(2·DZ), +π/(2·DZ)] — required so the
   WNORM = ∫∫W = 1 oracle is exact by the discrete DFT sum identity.
   W(z,−p) ≠ W(z,p) away from the midpoint — emit both signs.
   Cost: 128 z × 256 p × ≤128 m ≈ 4e6 mults. Trivial.
   Note: structure beyond p·dx ≈ 1 is grid-aliased; the physical fringe
   zone is |p| ≲ 2. WMAP rows are emitted every 2nd z × 2nd p.
3. Outputs per (R, parity):
   - W0  line: W(0,0) (oracle ±1/π)
   - WFR line: midpoint-row fringe min (value, p location)
   - WVIS line: |min|/max of midpoint row
   - WNORM line: ∫∫W dz dp (oracle 1.0)
   - WMAP rows: coarse map, every 2nd z × every 2nd p
     (64×64 = 4096 rows/R/parity; format "WMAP R par z p W %.17e")
4. Determinism: no new RNG, no new solver physics; fixed loop counts.
   A6-safe: RZ/W arrays STATIC, any helper subroutines take arrays only.

## Verification ladder

1. ATOM control: single-center 1s on the same grid → W map must be the
   known single-hump form; W(0,0) = +1/π (even state), no fringes.
2. Analytic oracles above (σg/σu at 7 R).
3. United-atom limit: R = 0.5 σg map ≈ ATOM map with ζ → 2.
4. Byte-determinism: run twice, identical WMAP.

## Follow-ons (same block, later)

- H₂ two-electron: 1-RDM from CI eigenvectors (needs h2_ci coefficient
  import or baked HL/Weinbaum coefficients); singlet vs triplet maps.
- DF radial: radial Wigner of the (F, G) densities — the "along the bond
  structure" extension into the atomic chain (He, Ne).
- Fringe-position law p_f·(R + 0.4) ≈ π as a quick two-center-coherence
  readout for systems without analytic references (HeH⁺, LiH).

Mirror: wigner_mirror.py (emits the oracle table; compares engine WMAP).

## Stage W2 — two-electron 1-RDM maps (mirror oracles, 2026-08-13)

2-orbital CI ({|gg>, |uu>} singlet block; |gu_S> decouples by parity —
the Weinbaum cov/ion mix IS the gg/uu mixing), FD Laplacian + open-
boundary zero-padded Poisson, zeta=1 scan. Structural oracles (the
6-orbital engine will shift depths, not signs):

| R | c_uu² | W00_S (per e⁻) | W00_T (per e⁻) |
|---|---|---|---|
| 0.5 | 0.0025 | +0.316 | +2.2e-3 |
| 1.0 | 0.0061 | +0.314 | +1.5e-3 |
| 1.401 | 0.0121 | +0.310 | +1.2e-3 |
| 2.0 | 0.0316 | +0.298 | +0.9e-3 |
| 3.0 | 0.1180 | +0.243 | +0.6e-3 |
| 4.0 | 0.2625 | +0.151 | +0.3e-3 |
| 6.0 | 0.4389 | +0.039 | +0.1e-3 |

Headline: **triplet midpoint coherence W00_T = 0 at every R** (γ_gg =
γ_uu = 1 forced by antisymmetry → the handshake is erased at the center,
a permanent white slit in the map). Singlet W00_S ≈ (1/π)(1 − 2c_uu²):
the covalent-coherence order parameter, tracking ionic content → dies at
dissociation as the 1-RDM goes 50/50 (entanglement, not antisymmetry).
Singlet-vs-triplet midpoint contrast peaks in the binding region — the
phase-space statement of "the sign of the bond is set by antisymmetry."

## Engine results (h2p_wig, 2026-08-13 — CERTIFIED)

WNORM = 1 to 3e-12 on all 14 blocks; σu node pinned at p ≈ 0, depth = W0,
every R. W0 within 0.5% of the same-state coarse-grid baseline (0.3142 vs
0.3157 at R_e). Fringe law p_f·(R+0.4) ≈ π confirmed on engine values.

Grid-vs-physics decomposition of fringe depth (fine 1s → coarse 1s →
engine): dx=0.25 costs only ~2–10%; the residual is orbital relaxation
and CHANGES SIGN — deeper than baseline at R_e (+38% at 1.401), equal at
R = 2, shallower beyond (−9…−18% at R = 3…6). Reading: inside the binding
region the true σg piles amplitude into the handshake (stronger midpoint
coherence than frozen 1s combos); outside R ≈ 2 the true bond localizes
onto the centers faster than 1s combos (real σg → Heitler–London). The
handshake-coherence crossover at R ≈ 2, just outside R_e, is the
phase-space signature of the binding region — the Stage-W headline.

---

## Stage W3 — Dirac-Fock radial Wigner (df_wig.ergo)

**Purpose.** Extend the Wigner handshake to atoms: map the radial
interference structure of closed-shell Dirac-Fock orbitals (He 1s2;
Ne 1s2 2s2 2p1/2^2 2p3/2^4), isolating the relativistic signature via
the collapse pair (c x100 vs physical c). Anchors the heavy-atom end
of the chain before W4 (heteronuclear).

**Locked definition.** Half-line Wigner of the occupation-weighted
radial 1-RDM, in two coordinates:

  rho(x,x') = sum_a occ_a [F_a(x) F_a(x') + G_a(x) G_a(x')]
  W(x,p)    = (1/pi) int_{window} dy e^{2ipy} rho(x-y, x+y)

  coord 0 (r-map): x = r uniform, cell-centered,
                   r in [1e-6, 12], NR = 2048, window |y| <= min(r, RMAX-r)
  coord 1 (t-map): x = t = log r uniform, endpoints included,
                   t in [log 1e-6, log 12], NT = 1024, window to grid edge

Both maps use NP = 4096 momentum samples, p_j = pi j / (NP dx),
j = 0..NP-1 (full Nyquist: NP >= NR, so WNORM is an EXACT discrete
sum).  WNORM = dx dp sum W with dp = pi/(NP dx):
  WNORM_r -> sum_a occ_a          (He 2, Ne 10)
  WNORM_t -> sum_a occ_a int (F_a^2+G_a^2) dt   (mirror-defined number)

**Engine.** df_radial.ergo VERBATIM (shooting SCF, all oracles intact:
collapse test vs Stage-1 HF, Ne ~ -128.69 Ha, He ~ -2.86181), plus a
post-SCF block per (atom, c-scale): linear-interp resample of F,G from
the native log grid onto both map grids, symmetrized coherence
SK(k) = 2 sum_a occ_a (F_{i-k} F_{i+k} + G_{i-k} G_{i+k}), direct DFT
via a precomputed cosine table (no FFT intrinsic), W row = (dx/pi)
[SK(0) + sum_k CTB(j,k) SK(k)]. Map rows strided 8 in x, 16 in p.

**Mirror (wigner_mirror_w3.py).** Hydrogenic Dirac: closed-form
eigenvalue E = c^2 [1 + (Z/c)^2/(n_r+gam)^2]^-1/2, ONE inward IVP
(decaying branch; outward integration is unstable, contamination
e^{2 lambda r}) with series-consistent start. IMPORTANT: radial
equations in E (total energy) are
  F' = -kF/r + (E - V + c^2) G/c,  G' = kG/r - (E - c^2 - V) F/c
— E - c^2 in the G equation; double-counting rest mass injects an
oscillatory mode of wavelength ~ 1/c.

**Oracle table (mirror, 2026-08-21 run).** Engine prints W3NORM /
W3W0R0 / W3W0RH / W3W0T0 / W3W0TH per (atom, c-scale); compare against:

| atom | c    | eps_1s          | WNORM_r      | WNORM_t      | Wt(tc,p=0)   | Wt(tc,q*)    |
|------|------|-----------------|--------------|--------------|--------------|--------------|
| He   | x100 | -2.0000000298   | 2.0          | 3.99998504   | +2.1779e-03  | +5.7830e-09  |
| He   | x1   | -2.0001065141   | 2.0          | 4.00041102   | +2.1803e-03  | +5.7890e-09  |
| Ne   | x100 | -50.0000006676  | 10.0         | 40.00113804  | +1.9197e-01  | +6.4037e-07  |
| Ne   | x1   | -50.0667420172  | 10.0         | 40.09340880  | +1.9567e-01  | +6.4873e-07  |

(q* = j NP/2.  Wr first-cell oracles are p-independent — window is one
point — and are printed but carry no information.)

**Interpretation contract (same as W2).** The mirror is HYDROGENIC; the
engine is DF-SCF. Scalar-oracle agreement certifies the instrument;
map differences vs the mirror baseline are the screening/correlation
physics, not errors. The c x100 -> x1 deltas are the relativistic
signal: Ne eps_1s deepens 0.0667 Ha; the t-map norm moves at 4th
decimal (He) / 2nd decimal (Ne) — the log-r Wigner resolves the cusp.

**Verification ladder.**
1. DFSCF/DORB/INT lines byte-match df_radial oracles (transplant check).
2. W3NORM_r = 2.0 / 10.0 to ~1e-6; W3NORM_t vs table above.
3. W3W0T0 / W3W0TH vs table (t-center values carry the signal).
4. python wigner_mirror_w3.py compare out.txt <Z> <cscale> <coord> —
   nearest-match max abs diff; expect O(screening), not 1e-12.

**Output grammar.** W3MAP Z cscale coord x p W (coord 0=r, 1=t),
strided; W3NORM Z cscale coord value; W3W0* Z cscale value.
