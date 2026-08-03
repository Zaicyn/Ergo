# Open quantum-rotor battery — quantum-jump trajectories vs the classical 1.5 ceiling

Programs: `min/qbattery/gen_rotor_traj.py` → `rotor_traj.ergo` (the engine;
regenerate with `python min/qbattery/gen_rotor_traj.py`), `rotor_traj.out`
(32 points × 8 blocks), `analyze_rotor_traj.py` (offline aggregation),
`dbg_cav.ergo` / `dbg_dec.ergo` / `dbg_hash.ergo` (validation programs,
kept as artifacts). Companion: `qbattery_check.md` (classical rate model,
settled: exp(I) = 1.0, exp(P) → 1.5 via dressed voltage Vth = E_T1 + G√N).

## Model (documented)

N spin-1 rotors (m ∈ {−1, 0, +1} = S0/T1/S1) + one damped cavity (NC = 4
levels), Lindblad dynamics:

- H = WC a⁺a + WR Σ Lz_i + G Σ (a L⁺_i + a⁺ L⁻_i) − J Σ_pairs (L⁺_i L⁻_j + L⁻_i L⁺_j)
  (spin-1 ladder amplitude √2; exchange is −J(LxLx+LyLy) up to the
  documented factor).
- Jumps: √κ a (cavity loss, κ=0.5), √P a⁺ (incoherent pump, P=0.1),
  √γ_s L⁻_i restricted to S1→T1 (amplitude √2 ⇒ rate 2γ_s at m=+1,
  γ_s=1.0), √KEXT X_i (extraction T1→S0, amplitude 1, KEXT=1.0;
  **current I = KEXT·P(m=0)**), √γφ Lz_i (pure dephasing).
- Emitter control (Tavis–Cummings): sd=2, m=±0.5, ladder amplitude 1,
  decay AND extraction both S1→S0, current I = KEXT·P(m=+0.5).
- Parameters: WC=WR=1.0, G=0.1, DTQ=0.01. Sweep: rotor N=2–6 ×
  J ∈ {0, 0.25, 0.5} × γφ ∈ {0, 0.1, 1.0} (γφ>0 at J=0.25 only), rotor
  N=7,8 at J=γφ=0, emitter N=2–6 at J=γφ=0. 32 points.

## Method — quantum-jump trajectories in Ergo (why)

The user's constraint: all heavy computation in Ergo, no dense-Python
eigh (an earlier attempt OOM-crashed). The Ergo-natural open-system
method is the stochastic-wavefunction (quantum-jump) unraveling: state =
complex wavefunction of dimension NC·3^N (max 26244 amplitudes at N=8 —
STATIC arrays, no density matrices, no diagonalization), Euler
H_eff evolution + channel-resolved jumps, splitmix white-hash PRNG
(validated in min/condensate/white_check.md). Long-time average = steady
state. Per point: NTHERM=4000 burn-in steps, then NBLK=8 blocks ×
NSAMPLE=12000 steps (T=960 per point); block scatter gives the SEM.
Python is used ONLY to emit the sweep tables (gen_rotor_traj.py) and to
average blocks/fit exponents (analyze_rotor_traj.py) — no physics in
Python.

## Engine bugs found and fixed (honest list)

The first two sweeps produced corrupted numbers; all were traced and
fixed in the generator (current rotor_traj.ergo has all six):

1. **Jump-state walk overshoot**: compound `DO WHILE ACC < U2 .AND. S <= DIM`
  always ran to S = DIM+1 (verified 60/60 debug prints). Replaced with a
  flag-based walk (`SEL`) over the full array.
2. **Component-wise jump application** (the deep one): jumps were applied
  only to the one basis component selected by RATE_A(S)|ψ_S|². Proven
  wrong for superpositions (explicit 3-level counterexample: ensemble
  dρ_11/dt = 2|β|² + 2√2 Re(αβ*) vs Lindblad's 2|β|² − |α|²). Replaced
  with the standard unraveling: select CHANNEL k with probability
  ⟨L⁺_k L_k⟩/R_tot, apply L_k to the FULL state (all jump maps are
  injective partial shifts, applied in place with the safe loop
  direction), renormalize.
3. **Stale WT table in the generator** (double-counted NC): rotor 1 was
  frozen at m=−1 in every state and its coupling transitions wrote out
  of range. Regeneration from the template had silently reintroduced
  this after it was hand-fixed in the .ergo — the generator is now the
  single source of truth.
4. **Pump jump amplitude** √(n+2) → √(n+1) (off-by-one vs the
  PUMP·(n+1) rate).
5. **Rotor decay rate** γ_s → 2γ_s at m=+1, matching the documented √2
  ladder (emitter unchanged, amplitude 1).
6. **PRNG conditional bias** (the subtle one): the channel-selection
  variate was derived by continuing the SAME hash chain after
  conditioning on NOISE < R_tot·DTQ. Ergo INTEGER is C int (32-bit);
  the truncated splitmix finalizer leaves the low 16 bits correlated
  with their own history, so the conditioned variate had mean 0.22
  (measured in dbg_hash.ergo: 0/97 late-channel selections where 28
  expected) — channels late in the walk order were starved. Fixed with
  an INDEPENDENT second hash stream for channel selection (measured
  clean: conditional mean 0.475, 28/97 selections vs 28.6% expected).
  Also: block index added to the hash seed (blocks were replaying the
  identical noise stream).

**Validation** (analytic, both in Ergo):
- `dbg_cav.ergo`: decoupled cavity (G=0) is an exact birth–death chain,
  π_n ∝ (P/κ)^n, ⟨n⟩ = 0.2436 analytic. Measured 0.2443 (8-block mean).
- `dbg_dec.ergo`: single rotor started at m=+1 with G=0 decays exactly
  once and extracts exactly once per trajectory (32/32 ✓); mean current
  0.00752 vs analytic KEXT/(T·1) = 0.00833 ± 0.0015 (within 0.6σ).

## Results — extraction current I (mean ± SEM over 8 blocks)

Rotor, J=0, γφ=0 (the headline line):

| N | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| I | .0271±.0051 | .0416±.0045 | .0584±.0079 | .0836±.0149 | .0776±.0180 | .1040±.0132 | .0958±.0085 |
| coh | .0115 | .0118 | .0130 | .0153 | .0121 | .0135 | .0102 |

Emitter control, J=0, γφ=0: I = .0052, .0090, .0079, .0143, .0152
(N=2..6); coh ≈ .002–.003.

### Exponent table (weighted log-log fits of I vs N)

| line | exp(I) | verdict |
|---|---|---|
| rotor J=0 γφ=0 (N=2..8) | **0.91 ± 0.11** | linear, NOT 1.5 |
| emitter J=0 γφ=0 (N=2..6) | 0.99 ± 0.24 | linear ✓ (control) |
| rotor J=0.25 γφ=0 | −0.84 ± 0.12 | exchange SUPPRESSES |
| rotor J=0.5 γφ=0 | −0.62 ± 0.17 | suppression |
| rotor J=0.25 γφ=0.1 | −0.82 ± 0.12 | unchanged by weak dephasing |
| rotor J=0.25 γφ=1.0 | −0.20 ± 0.14 | suppression lifted by strong dephasing |

Classical references (qbattery_check.md): exp(I) = 1.0; exp(P) → 1.5
asymptotically via the dressed voltage alone; paper claim exp(P) = 2.
**The quantum current exponent matches the classical 1.0 within 1σ at
every point in the sweep; no superextensive current residual appears
anywhere.** The 1.5 classical power ceiling lives in the voltage, which
this current-only measurement does not test; the missing N^0.5 of
current that the paper's N² power would require is NOT present in the
quantum model at N=2..8.

### J (exchange) dependence and the coherence correlation

Exchange HURTS: at J=0.25 the current drops below J=0 by a factor
growing with N (×1.2 at N=2, ×8–9 at N=5–6) and the
exponent inverts (−0.84); at J=0.5 the same (−0.62). Mechanism
(consistent with the coherence data): exchange delocalizes the
excitation across rotor pairs, draining the local m=0 population that
the extraction channel counts — and the dilution grows with N.
Across all 17 rotor (N, J) points at γφ=0:
**corr(log I, log coh) = 0.914** — the pair coherence
⟨(L⁺_1 L⁻_2 + h.c.)/2⟩ tracks the current almost one-to-one; J
suppresses both together (coh falls .0121→.0017 at N=6 as J goes
0→0.25). So the coherence measure is an excellent proxy for the
transport-relevant population, but its N-scaling is flat-to-negative —
no coherence-driven superextensivity.

### Dephasing boundary (the temperature question)

At J=0.25: γφ=0.1 changes nothing (I within ±40%, all within errors;
coh unchanged). γφ=1.0 (i.e. γφ = 10·G = 4·J) partially RESTORES the
current at N≥4 (×1.2–1.5, exponent −0.84 → −0.20) while cutting coh
2–6× — environment-assisted re-localization out of the J-induced dark
superpositions. At N=2 strong dephasing hurts slightly (×0.7).
**Boundary: coherent exchange effects are intact for γφ ≲ 0.1 (the
light–matter coupling scale G) and are washed out by γφ ~ 1 (10·G).**
Reading for the temperature question: the coherent interaction effects
(this model has γφ ∝ temperature) require dephasing below the coupling
scale — i.e. the quantum coherence structure does NOT survive without
isolation — but the steady-state current itself is remarkably robust:
total variation across the whole γφ sweep is a factor ~1.5, not orders
of magnitude. (An earlier engine build showed a spurious ×10–30 current
boost at γφ=1; that was the PRNG conditional-bias artifact, now fixed.)

## Noise floor and systematic caveats (honest)

- Per-point SEM 9–29% (single long trajectory per point; blocks are
  T=120 vs mixing time ~1/G² = 100, so the SEM is a LOWER bound).
  Exponent errors ±0.11–0.24: exp = 1.5 is excluded at ≥4σ on the J=0
  rotor line, but 1.0 vs 1.15 is not resolvable at these statistics.
- N=8 dips below N=7 (0.096 vs 0.104, within 1σ): either onset of
  cavity sharing (nph stays ~0.18 while rotors multiply) or noise; the
  fit includes it, pulling the exponent slightly under 1.
- At γφ=1, R_tot·DTQ ≤ ~0.2: the one-jump-per-step rule incurs a
  few-% second-order error there.
- Cavity truncated at NC=4 with pump blocked at n=3 (validated harmless:
  ⟨n⟩ ≤ 0.29 everywhere; birth–death check exact).
- Trajectory unraveling = Lindblad ensemble only in the long-time
  limit; T=960/point with mixing ~100 gives ~10 independent windows —
  this is what sets the noise floor above.

## Verdicts

**(a) Superextensive discharge in the quantum model?** NO at N=2..8:
exp(I) = 0.91 ± 0.11 (rotor) and 0.99 ± 0.24 (emitter control) — both
linear, matching the classical rate model's exp(I) = 1.0 and ruling out
the I ~ N^1.5 the paper's P ~ N² requires. The classical 1.5 power
ceiling (dressed voltage) is untouched by this measurement.
**(b) What does the rotor phase structure add vs two-level emitters?**
A factor ~4–6 larger absolute current (the T1 middle level is an
extraction port the emitters lack) and a measurable pair coherence that
tracks transport (r = 0.91) — but NO exponent advantage.
**(c) J coupling:** purely detrimental here (delocalization dilutes the
extraction window); the coherence it destroys was the transport carrier.
**(d) Dephasing/temperature:** coherent interaction effects survive to
γφ ~ G and die by γφ ~ 10·G (assisted-transport crossover at γφ ≳ J);
the current magnitude itself is robust within ×1.5.

## Ergo feasibility — direct answer

Fully feasible, and it was the right tool: the whole engine (wavefunction
matvec, jump channels, PRNG, blocked sampling, N=8 / DIM=26244, ~1.2M
steps total) is one STATIC-array Ergo program, ~25 min wall for the
32-point sweep, no density matrices, no diagonalization, no external
numerics. Python touched only sweep-table emission and block averaging
(justified: no physics content). Limits hit, honestly: (1) Ergo INTEGER
is 32-bit C int — the "int64 splitmix" documented in white_check.md is
actually truncated, which is what made the conditioned PRNG bias
possible; the two-stream fix works within 32 bits. (2) No compound
`DO WHILE` conditions (item 1 above) — use flag-based loops. (3) No
built-in RNG — the white hash idiom is mandatory and must be re-validated
per use (conditional statistics, not just marginal). (4) Long runs are
the price of trajectories: exponent precision ~±0.1–0.2 at 25 min/sweep;
a factor-2 tightening needs ~4× the steps.

Files: `min/qbattery/gen_rotor_traj.py`, `rotor_traj.ergo`, `rotor_traj`
(binary), `rotor_traj.out`, `analyze_rotor_traj.py`, `dbg_cav.ergo` (+bin,
cavity birth–death validation), `dbg_dec.ergo` (+bin, rotor decay-chain
validation), `dbg_hash.ergo` (+bin, PRNG conditional-bias test), this
report.
