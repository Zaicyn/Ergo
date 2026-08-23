# DF_RADIAL2_FINDINGS.md — Dirac-Fock radial SCF engine, repaired and certified

2026-08-22. Companion to DIRAC_FINDINGS.md (single-electron shooter) and
wigner_handshake_spec.md (Stage W3). This document is the authoritative record
of the df_radial prototype autopsy, the four repairs, the certification
oracles, and the engine↔mirror agreement.

---

## 1. Where this sits

- **dirac_radial.ergo** — certified single-electron Dirac shooter (unchanged,
  still the numerical core: log-grid RK4, outward series start, inward
  decaying start, mid-match Wronskian).
- **df_radial.ergo** — the prototype Dirac-Fock SCF. **Never compiled**
  (colon-bounds array `F(NR:NT,4)`, "Expected RPAREN, got COLON"). Its He
  results were therefore never produced by this source; its Ne results
  (from whatever did run) are now known to be non-physical (§3, FIX 4).
- **df_mirror.py** — the repair mirror (Python, NT=4000), where all four
  fixes were developed and certified against Clementi–Roetti.
- **df_radial2.ergo** — the repaired engine (NT=20000), transcription of the
  certified mirror. Ran 2026-08-22, all oracles pass (§5).

## 2. Bug zero: it never compiled

`F(NR:NT,4)` — colon-bounds array declaration, unsupported by the dialect.
The prototype as uploaded is a parse error. Everything below was diagnosed
against the *intended* algorithm, rebuilt in the mirror.

## 3. The four repairs

### FIX 1 — initial packets: normalized, physical small component
The prototype seeded orbitals with the series-start form `G = q₀·F`,
`q₀ = c(s+κ)/Z`. For κ>0 that ratio puts essentially the entire norm
(~(2c/Z)²) in an unphysical branch of the small component — Ne x100 cycle 1
then built potentials from garbage and found no root at all. Fix:
`F = r^s·e^(−Zr/n)`, `G = (F′ + κF/r)/(2c)` with `F′ = (s/r − Z/n)F`,
then normalize on the log grid before the first potential build.

### FIX 2 — adaptive rescan, no silent freeze
Prototype: ±8% scan window around EPREV; on failure it silently kept the
cycle-1 energy — the SCF looked "converged" while frozen. Fix: three
attempts (±8%/31 pts → ×8 widen → full range −1.5Z²…−1e-6Z²/240 pts),
and SCANFAIL is **printed** (`cyc`, `orb`, `eps kept`, `poles`). In the
certified runs SCANFAIL fires at cycles 2–3 (transient under-relaxed
potentials), the engine recovers by cycle 4 and converges monotonically to
1e-13. Loud-and-recover is the designed behavior.

### FIX 3 — E_total printed
The prototype never assembled E = Σocc·ε − E₂, so no Clementi–Roetti oracle
was computable. df_radial2 prints `ETOT ... E=... sumeps=... E2=...` with
E₂ built from the same occupation-scaled exchange coefficients as the
potential (CXK/CXC tables, c_eff = CXC·occ_b/occ_std_b, occ_std = 2(s)/6(p)),
plus the full INT Slater–Condon table for external analysis.

### FIX 4 — variation-of-parameters orbital solver (the deep one)
The prototype's detector was the Wronskian of **two particular
solutions** (both legs carrying the frozen exchange sources). This is
numerically broken once sources are present:

- its zeros are **source-amplitude-dependent artifacts**, not eigenvalues.
  Demonstrated in the mirror: with normalized packets there is no deep root
  at all; scaling the source by ×1 creates roots at −37.7; normalized again,
  a spurious root at −0.54. The historical Ne x1 oscillation
  (−41.5 → −42.3 → −41.6) was this artifact churning.
- He passed only because a single 1s orbital has no off-diagonal sources
  (self-exchange is multiplicative, absorbed in VL).

Replacement (the certified algorithm): the frozen-source problem
(T−ε)X = S is linear and has a normalizable solution for every ε; ε is the
**normalization Lagrange multiplier** — the orbital energy is the root of

  ‖X(ε)‖ = 1.

Construction: homogeneous regular/decaying pair (U, W) of the same
potential; W0 = U_F·W_G − U_G·W_F (constant in t, trace-free system);
X = a(t)U + b(t)W with

  a′ = (SFv·W_G − SGv·W_F)/W0,  a(∞) = 0
  b′ = (U_F·SGv − U_G·SFv)/W0,  b(0) = 0
  SFv = −r·SG/c,  SGv = −r·SF/c   (source vector in the t-equations)

Properties that make it work:

- **Poles** of N(ε) = ‖X(ε)‖ sit at the homogeneous eigenvalues (W0 → 0);
  unit-norm roots bracket each pole. Branch selection is anchored by
  **Sturm ordering**: the k-th pole ascending in energy has k radial nodes —
  no node counting needed during targeting (node count is verified only at
  the accepted root).
- **Sign detection must be LOGICAL signbit tests, never products** —
  W0 reaches ~1e180 and any product-based test overflows or hides poles
  behind inf.
- **Pole-aware dense refine**: across a pole, log10 N jumps +inf → −inf and
  looks like a sign change; among adjacent sign-change pairs pick the one
  minimizing |f₀|+|f₁| (a true root, not a pole crossing).
- Per-orbital inward start NIN = index of min(RMAX, 62·n²/Z) (from
  dirac_radial's per-orbital RMAX) keeps the inward leg's amplification
  resolvable.
- The legacy both-leg Wronskian path (SHOOT) is retained **only** for
  source-free orbitals (He), where it is exact.

## 4. Certification protocol

Mirror (NT=4000) first, engine (NT=20000) second; oracles are
Clementi–Roetti total energies at c×100 (nonrelativistic limit) and the
Dirac-Fock deepening + 2p fine-structure split at physical c.

## 5. Results — df_radial2 engine run (2026-08-22), df_radial2.csv

Both SCFs converged to dE = 0.0 in print format (≤ 1e-13). SCANFAILs only
at cycles 2–3, recovered, monotone thereafter.

| Quantity | df_radial2 (NT=20000) | mirror (NT=4000) | oracle |
|---|---|---|---|
| He x100 eps₁s | −0.9179556486 | −0.91795762 | — |
| He x100 **E** | **−2.861680242** | −2.861686 | CR −2.861680 |
| Ne x100 eps | −32.7724507 / −1.9303917 / −0.85041011 / −0.85040972 | −32.77253 / −1.93040 / −0.85042 / −0.85042 | — |
| Ne x100 **E** | **−128.5471256** | −128.547444 | CR −128.5471 |
| He x1 eps₁s | −0.9179907705 | −0.91799274 | — |
| He x1 **E** | **−2.861813575** (deepening −1.33e-4) | −2.861819 | — |
| Ne x1 eps | −32.8175168 / −1.9354009 / −0.85209007 / −0.84865792 | −32.81760 / −1.93541 / −0.85210 / −0.84866 | — |
| Ne x1 **E** | **−128.6901474** (deepening −0.143) | −128.690466 | — |
| Ne x1 2p split | 3.4321e-3 (2p₁/₂ below 2p₃/₂ ✓) | 3.43e-3 ✓ | — |

Deviations from CR: He x100 ~−2e-7; Ne x100 ~−2.6e-5 — both at/below the
grid level, and both tighter than the mirror, as expected from NT 4000→20000.
The x100 2p pair correctly degenerates to 4e-6; the x1 pair splits with the
correct Dirac ordering (κ=+1 deeper).

## 6. Verdicts

1. **The df_radial prototype's Ne numbers were never physical.** Not "wrong
   grid", not "wrong mixing" — the detector's roots moved with source
   amplitude. Discard them entirely; df_radial2's are the first physical
   Ne numbers from this codebase.
2. **He was right for the wrong reason.** Source-free orbitals are the one
   case where the broken detector is exact.
3. **The repair semantics are certified end-to-end**: mirror CR-certified
   → engine transcription matches mirror to grid level → engine matches CR
   to 2e-7 (He) / 2.6e-5 (Ne).
4. SCANFAIL-as-designed: loud, transient, self-healing under SCF mixing.

## 7. Stage W3 certified — df_wig2 (2026-08-22, df_wig2.csv)

df_wig2 = df_radial2 SCF verbatim + the df_wig Wigner block (grids and
construction unchanged: NRW=2048 uniform-r, NTM=1024 uniform-t, NPW=4096,
cosine-table direct DFT). Run result:

- **SCF byte-identical to the df_radial2 certification run** in all four
  blocks (eps, ETOT, even the SCANFAIL pattern) — the graft is
  non-invasive.
- **WNORM_r matches the hydrogenic mirror oracles**:
  He x100 2.0000000145 (oracle 1.999999783110);
  Ne x100 10.000000118 (oracle 9.999999771372).
  Parseval: WNORM_r = Σ_a occ_a ∫ρ dr = Σ occ — a pure counting
  observable, screen-independent, so the hydrogenic target is exact.
- **WNORM_t is NOT a counting observable — it is a screening
  measurement.** Parseval: WNORM_t = Σ_a occ_a ∫ρ dt
  = Σ_a occ_a ⟨1/r⟩_a. The mirror oracles (3.99998 / 40.00114) were
  built from hydrogenic Dirac–Coulomb orbitals, where ⟨1/r⟩ = Z exactly.
  The certified SCF orbitals are screened, so the true values are lower:
  | WNORM_t | hydrogenic baseline | df_wig2 (SCF) |
  |---|---|---|
  | He x100 | 3.999985040231 | **3.374564887** |
  | He x1   | 3.99998…       | **3.374863112** |
  | Ne x100 | 40.00113803702 | **31.113324314** |
  | Ne x1   | 40.001…        | **31.175084758** |
  Cross-checked against the independent certified mirror: its SCF He
  orbital on the engine's t-grid gives 3.374565855 (engine 3.374564887,
  agreement 8.5e-9) and the direct integral 2⟨1/r⟩ = 3.37457. The
  "miss" vs the hydrogenic oracle **is** the physics: He 1s
  ⟨1/r⟩ = 1.687 (not Z = 2); Ne carries the whole-shell screening
  budget (−22% vs hydrogenic).
- **Relativistic contraction visible in WNORM_t** (x100 → x1): He
  +2.98e-4, Ne +6.18e-2 (+0.2%) — shells contract, ⟨1/r⟩ rises, correct
  sign and size.
- W3W0TH ≈ −4e-10 (clean zero); W3W0R0 = W3W0RH to printed digits.
- **The hydrogenic WNORM_t oracles are retired as baselines, not
  targets.** The screened values above are the certified W3 numbers.

### 7b. W3MAP point-by-point analysis (2026-08-22, df_wig2.csv rows)

Three comparisons, each isolating one layer:

**(i) Construction certification — engine vs SAME-orbitals mirror.**
The certified df_mirror SCF orbitals resampled to both map grids and run
through the same half-line Wigner construction, diffed against the
engine's W3MAP rows:

| Block | r-map max\|diff\| | t-map max\|diff\| |
|---|---|---|
| He x100 | 1.13e-6 | 8.44e-7 |
| He x1   | 1.13e-6 | 8.44e-7 |
| Ne x100 | 3.44e-6 | 1.04e-5 |
| Ne x1   | 3.42e-6 | 1.04e-5 |

(Ne x1 via `w3_certify_nex1.py`, run 2026-08-22: engine W3MAP rows vs
certified-mirror SCF orbitals through the same construction; rms 1.09e-7
r-map / 2.84e-7 t-map.)

The engine's resample + cosine-DFT map construction is exact to
interpolation/roundoff level. Everything larger in (ii) is physics.

**(ii) Screening — engine vs hydrogenic mirror maps.** Pointwise diffs
are O(1) relative and localize on the **p = 0 ridge in the valence
region** (screening pushes density outward, fattening W there):
He x100 max +0.163 at r=1.55 p=0 (rms 3.3e-3); Ne x100 max +1.77 at
r=1.17 p=0 (rms 3.3e-2); t-maps similar at t ≈ −1.1…−1.3. The x100 vs
x1 rows are nearly identical — screening beats relativity by three
orders of magnitude at map level.

**(iii) Fine structure — engine self-diff W(x1) − W(x100)** (same code,
same SCF algorithm, only c changes — all screening cancels):

| Atom | r-map max ΔW | t-map max ΔW | location |
|---|---|---|---|
| He | 3.3e-5 at r=0.42, p=0 | 1.6e-4 at t=−1.58, p=0 | core ridge |
| Ne | 1.8e-3 at r=0.57, p=0 | **2.7e-2** at t=−3.24, p=0 | r ≈ 0.039, deep core |

The relativistic signal scales ≈ (Zα)²·Z² (×25–80 from He to Ne), lives
on the p=0 ridge, and in Ne is dominated by the **1s contraction in the
deep core** — the t-map at r ≈ 0.04 is where the Dirac correction to the
inner shell shows up. The 2p κ-splitting rides on top at valence radii,
an order smaller.

**The map in one sentence:** screening owns the valence ridge at O(1),
relativistic contraction owns the deep-core ridge at
O(1e-2·(Z/10)²), and the instrument resolves both with construction
noise at 1e-5 — four decades below the weakest physics signal.

## 8. Stage W4a certified — heteronuclear handshake, HeH2+ (2026-08-22)

Engine **h4p_wig.ergo** (fork of h2p_wig): two-Z potential (He Z=2 at
z=−R/2, H Z=1 at z=+R/2), **no parity** — 1σ by plain imaginary time
from a He-weighted start, 2σ from an H-weighted antibonding start with
**per-step deflation against the converged 1σ** (the df_radial2 same-κ
pattern). Wigner block byte-identical to h2p_wig; IP now means state.
R list (mirror-scouted, spans the charge-localization transition;
HeH2+ has no bound equilibrium — literature-confirmed repulsive ground
curve): 0.75, 1.0, 1.5, 2.0, 3.0, 4.0.

Run (h4p_wig.csv): **WNORM = 1 to ≤1.8e-12 on all 12 maps** — the
no-parity pipeline is exact.

**Mirror v1 (wigner_mirror_w4.py, 2×1s LCAO) failed for 2σ below
R≈2 — the engine caught it.** LCAO: W(0,0)=+0.056 at R=0.75; engine:
**−0.2675** with the WFR minimum AT p≈0 (WVIS>1): the exact 2σ is
united-atom-2p-like with a node plane through the bond — the
heteronuclear descendant of W1's σu node pocket. Two 1s functions
cannot represent it.

**Mirror v2 (wigner_mirror_w4b.py)** adds a midpoint 2p_z STO
(ζ=3/2, exact Li2+ 2p as R→0); kinetic stays multiplicative, matrix
elements in the same deterministic prolate quadrature. Result:

- 2σ energies now respect the variational bound (mirror above engine
  everywhere) AND reproduce the engine's non-monotone curve (minimum
  at R≈1.5): mirror −1.238/−1.282/−1.309/−1.271/−1.126/−0.993 vs
  engine −1.278/−1.324/−1.368/−1.328/−1.169/−1.024.
- 2σ W(0,0): mirror −0.2425/−0.1934/−0.0945/−0.0250/+0.0260/+0.0268
  vs engine −0.2675/−0.2445/−0.1655/−0.0775/+0.0394/+0.0820 — correct
  sign structure everywhere; pocket depth ~25% shallow at mid R
  (fixed-exponent basis crudity).
- Map-level max|diff| vs engine: 1σ 2.4–4.6e-2; 2σ 6.2e-2 at R=0.75
  (was 0.376 pre-patch), ~0.10–0.13 mid/large R.
- Deterministic (oracles hash-identical across runs).

**Heteronuclear observables (the W4a physics):**
- W(0,0) is no longer ±1/π — it is the midpoint coherence of an
  asymmetric bond: 1σ runs +0.280 → +0.0076 as charge localizes onto
  He (mirror Mulliken popA(He): 0.96 at R=1 → 0.9997 at R=4).
- Fringes asymmetric in ±p; the 2σ node pocket sits AT the origin at
  small R and drifts off toward the H side by R=3–4 (fringe at
  p≈−1.84/−1.35).
- Engine ECONV sits below LCAO everywhere (exact grid solver);
  monotone repulsive 1σ curve → −2.0 (He+ + p), 2σ → −0.5 (H + He2+).

**Verdict: W4a PASS.** Heteronuclear machinery (two-Z potential,
deflation-selected excited state, no-parity Wigner) certified; mirror
v2 is quantitative for both states at small R and qualitative-to-
quantitative at mid R. Next: W4b — bound two-electron HeH+ (h2_wig
fork, R_e = 1.46 a0), where the heteronuclear handshake lives.

## 9. Stage W4b certified — bound two-electron HeH+ (2026-08-22, h4w.out)

**Engine: h4_wig.ergo** — fork of h2_wig.ergo (six-orbital full-CI +
1-RDM Wigner, singlet+triplet). Deltas: two-Z potential
V = −2/RR − 1/RL (He at z=−R/2, H at z=+R/2); asymmetric start packets
(He-weighted bonding 1σ, H-weighted 2σ, X/Y/Z-polarised, diffuse σ);
R = 0.75/1.0/1.46/2.0/3.0/4.0 centred on R_e = 1.46; new DIPOLE line
(electronic ⟨Σz⟩ from each 1-RDM + total dipole about midpoint,
μ_nuc = −R/2). CI/Jacobi/1-RDM/Wigner blocks byte-identical to h2_wig.

**Mirror: wigner_mirror_w2b.py** — 2-orbital CI over the w4b
one-electron orbitals (midpoint-2p LCAO) on a 128³ grid, 3-CSF singlet
block (no parity: |aa⟩, |ab_S⟩, |bb⟩ all mix). Deterministic
(hash-identical map runs). Same electronic-only energy convention as
the engine.

**Run (h4w.out, NX=128 BOX=16, 6 R × 2 spins, 98304 W2MAP rows):**

Norms (construction): GTRS/GTRT = 2 to 1e-14; W2NORM = 2.0 to 2.4e-12
every R, both spins. Construction certified exactly as in W2/W4a.

Energies (Ha, electronic; mirror in parentheses):

| R | ES engine | ES mirror | ET engine | ET mirror |
|---|---|---|---|---|
| 0.75 | −5.18485 | (−5.09930) | −3.88539 | (−3.82756) |
| 1.00 | −4.69575 | (−4.69326) | −3.65002 | (−3.66767) |
| 1.46 | −4.17797 | (−4.18991) | −3.44010 | (−3.47736) |
| 2.00 | −3.78822 | (−3.81360) | −3.26382 | (−3.31749) |
| 3.00 | −3.39979 | (−3.42093) | −3.03931 | (−3.10747) |
| 4.00 | −3.21410 | (−3.21806) | −2.90424 | (−2.96335) |

Singlet below triplet at every R; singlet curve bound with its minimum
near R ≈ 1.5–2 (R_e physics reproduced). Engine ES is below the mirror
at R ≤ 1 (full CI wins) and up to 0.03 Ha above at R ≥ 1.46 — the
2-orbital-mirror inequality is indicative only (mirror orbitals are
STO-LCAO, engine orbitals are grid h-eigenstates; neither contains the
other). Same caveat held for the triplet, mirror lower by 0.01–0.06 Ha.

W(0,0) (engine units; mirror × 2 in parentheses):

| R | singlet eng | (mirror) | triplet eng | (mirror) |
|---|---|---|---|---|
| 0.75 | +0.590 | (0.519) | +0.080 | (0.001) |
| 1.00 | +0.573 | (0.495) | +0.042 | (0.021) |
| 1.46 | +0.517 | (0.449) | +0.041 | (0.051) |
| 2.00 | +0.443 | (0.391) | +0.052 | (0.062) |
| 3.00 | +0.299 | (0.279) | +0.054 | (0.052) |
| 4.00 | +0.137 | (0.152) | +0.035 | (0.035) |

Singlet midpoint lobe positive, decaying with R; engine sits above the
mirror exactly as correlation should (mirror is uncorrelated-dominated).
**W00_T is no longer ≈ 0** (0.03–0.08): the W2 "antisymmetry erases the
midpoint" argument was parity-based and dies in the heteronuclear
case — predicted by the mirror, confirmed by the engine.

Dipole ⟨Σz⟩ (electronic; negative = toward He):

| R | singlet eng | (mirror) | triplet eng | (mirror) |
|---|---|---|---|---|
| 0.75 | −0.279 | (−0.344) | +0.521 | (+0.364) |
| 1.00 | −0.435 | (−0.476) | +0.245 | (+0.385) |
| 1.46 | −0.799 | (−0.836) | +0.047 | (+0.295) |
| 2.00 | −1.314 | (−1.359) | −0.153 | (+0.149) |
| 3.00 | −2.470 | (−2.506) | −0.321 | (+0.036) |
| 4.00 | −3.719 | (−3.809) | −0.183 | (+0.010) |

Singlet quantitative (≤0.07 everywhere) and → −R at large R: both
electrons migrate to He — the charge-localization transition, now in a
two-electron observable. Total dipole about the midpoint nearly
vanishes at R_e (DMUS = +0.069 at R=1.46) and grows to +1.72 at R=4.
Triplet dipole agrees at small R but flips sign earlier in the engine
(negative from R=2); the triplet is |12_T⟩-dominated (90–97%) in both,
so this is a genuine orbital-level difference between the engine's
second grid eigenstate and the mirror's LCAO 2σ at large R — flagged
honestly, dipole is not variationally protected.

Maps: 8192 rows compared per (R, SP), max |diff| 0.056–0.112 on maps
whose peaks are O(0.5) — the correlation gap between a 2-orbital STO
mirror and a 6-orbital grid full-CI, not construction noise (1e-5
scale). CSF dumps: singlet |11⟩ 88–96%, triplet |12_T⟩ 90–97% at all
R — the mirror's assumed configuration structure is the engine's.

**Verdict: W4b PASS.** Heteronuclear two-electron handshake certified:
norms exact, energy ordering correct, bound ground state, singlet
dipole and W00 trends quantitative, triplet midpoint non-erasure
confirmed. Known limits: mirror energies indicative only beyond R=1;
triplet dipole sign at large R is orbital-basis-sensitive.

## 10. State of the campaign / what's next

- W3 done, maps included; W4a done; **W4b done (this document, §9).**
- Compiler-side items this campaign surfaced (user's list): A6 scalar
  dummy-arg copy-out; undefined identifier in array bound must be a hard
  error; case-policy decision.

## 11. Reproduce

```bash
cp df_radial2.ergo.txt min/diracfock/df_radial2.ergo
cp df_wig2.ergo.txt   min/diracfock/df_wig2.ergo
cp h4p_wig.ergo.txt   min/handshake/h4p_wig.ergo
cp h4_wig.ergo.txt    min/handshake/h4_wig.ergo
source .venv/bin/activate
python -m core min/diracfock/df_radial2.ergo -o /tmp/df_radial2
/tmp/df_radial2 > df_radial2.csv
python -m core min/diracfock/df_wig2.ergo -o /tmp/df_wig2
/tmp/df_wig2 > df_wig2.csv
python -m core min/handshake/h4p_wig.ergo -o /tmp/h4w
/tmp/h4w > h4p_wig.csv
python wigner_mirror_w4b.py compare h4p_wig.csv <R> <state>
python -m core min/handshake/h4_wig.ergo -o /tmp/h4w2
/tmp/h4w2 > h4_wig.csv
python wigner_mirror_w2b.py compare h4_wig.csv <R> <SP>
```

Files: `df_radial2.ergo.txt`, `df_wig2.ergo.txt`, `h4p_wig.ergo.txt`,
`h4_wig.ergo.txt` (engines, rename to `.ergo`); `df_mirror.py`
(certified repair mirror); `df_radial2.csv`, `df_wig2.csv`,
`h4p_wig.csv`, `h4_wig.csv` (certification runs); `wigner_mirror_w3.py`
(hydrogenic W3 mirror — baselines only, see §7); `wigner_mirror_w4.py`
(W4a LCAO mirror v1 — superseded for 2σ), `wigner_mirror_w4b.py` (W4a
mirror v2, midpoint 2p STO — current), `wigner_mirror_w2b.py` (W4b
2-orbital-CI mirror — current).

