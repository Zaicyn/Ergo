# AB_REWIND_FINDINGS.md

**Campaign:** Aharonov–Bohm Stage 4–7 — Π-ledger, time-reversal census, recoil physics, and the clean flux line
**Engine:** ergo/mcl staggered-leapfrog Schrödinger grid (512×512, AA=0.2, Peierls links, NSP=48 sponge, r=8 WALL=0 shield disk at (256,256))
**Verification standard:** every headline number reproduced by an independent C mirror to displayed precision before interpretation; all ergo runs cited here match the mirror byte-for-byte at printed digits (cx values +1.00 site from 1-based indexing throughout).

> **REVISION NOTICE (Stage 7):** Stages 2–6 used *linearized* Peierls links (−TH·dy/r²), whose discrete curl is only approximately zero — a flux line **plus a spurious B-field concentrated at the core**. Since F5 showed the recoil physics is core-localized, the artifact sat on the signal. F1–F3 are engine mechanics and stand. **F4–F7 are linearized-link measurements** — retained as the "fringing-field solenoid" column; the ideal-AB column begins at F8 (exact links, zero plaquette flux outside the core by construction).

---

## F1. Two ledgers balance (Stage 4a)

The Kang/Vaidman/Pearle–Rizzi equivalence was checked entry-by-entry, not asserted. A continuous Π-ledger (Π_sim = FL·(EY,−EX)/2π, mass-normalized per channel, PH += FLV·(VX·EY − VY·EX)/(2π·W)) was integrated alongside the screen phasor for FL = 0, π/2, π, 2π.

- Ledger/flux ratio: **0.6442 / 0.6455 / 0.6500** — constant to 0.9% across flux values.
- Screen phasors byte-exact vs the original stage-2 engine (2.63562@π, −0.33050@2π).
- The **2π discriminator fired**: the screen is blind at 2π (single-valued wavefunction) while the ledger books the full winding (4.084). Loop-closed phases are the only observables; the accumulated local phase probe was found contaminated by dynamical drift and removed.
- The ledger is **shield-tolerant**: transient energy-core dips at transit (to 1.9) do not corrupt the balance.

**Verdict:** the electromagnetic-field momentum ledger and the wavefunction phase are the same book kept two ways, to instrument precision.

## F2. Handedness and polarity budget (Stage 4b)

Seven-case flip (0, ±π/2, ±π, ±2π). Handedness reversal is exact under FL → −FL; polarity budget |ledger(−FL)|/|ledger(+FL)| = **1.0000 / 1.0002 / 1.0007**.

Side discovery — the seed of Stage 5: an **FL-odd centroid displacement**, negative-FL packets traveling ~2.4 sites per π farther at T=2200, non-monotonic in FL.

## F3. Time-reversal census (Stage 4c–d)

True engine reversal (backward leapfrog sweeps from the actual final state — not a phase-conjugate mirror launch, which was shown analytically to *reproduce* rather than unwind, since A·dl is invariant under full T).

- **Leapfrog is exactly reversible**: return deficit 2.887e-15 (FL=0), 2.873e-15 (FL=π) after 1200+1200 steps. Flux changes nothing.
- **The sponge is the only entropy source**: backward amplification ×1.5/step (= 1/0.664, the forward absorber), 0.18 dex/step, rewind death at t=203 (mirror predicted 202).
- **The disk is a mirror, not a sink**: WALL=0 Dirichlet pinning is a reversible boundary. Aimed-packet rewind deficit **4.131e-12, byte-identical to the C mirror**; the transit mass dip (0.99923477) retraced exactly to 8 digits, ending 1.00000000.

**Verdict:** nothing on the grid destroys information in exact arithmetic. The arrow of time lives in the absorber's finite-precision arithmetic, not in the dynamics, and not in the flux.

## F4. The recoil is the canonical/kinetic split (Stage 5)

Nine-case sweep with a dedicated instrument: per-channel centroids (CX, CY) plus **kinetic momentum from the gauge-covariant derivative** built with the Peierls links.

Small-FL regime (±π/4, ±π/2) is exact:

- FL-odd to **0.03 sites**; channel-mirror antisymmetric to **0.06 sites**.
- Linear: Δcx1 = −1.0 (π/4), −1.6 (π/2); Δkx1 = **−0.00237 per π/4** (bottom channel opposed, top aided).
- Measured slope Δkx1/ΔFL = −0.00302 vs A at closest approach FL/(2π·52) = 0.00306 — agreement to 1.3%.

Large-FL regime is band curvature, not force:

- Displacement **rolls over past π/2** (−1.0 at π, +0.3 at 2π — explaining the 4b non-monotonicity): group velocity ∝ sin(k−A), not linear impulse.
- The 2π odd-asymmetry (+2.4 sites) and FL-even channel-sum growth are second-order lattice dispersion, reproduced exactly by the mirror — engine physics, not boundary artifact.

**Verdict:** no force acts on the packet. Canonical momentum is conserved; the displacement is the kinetic velocity k−A imprinted per channel. The "recoil" measured from the wavefunction side *is* the hidden-momentum transfer the coil must absorb — magnitude ~1% of carrier momentum per π of flux at r=52.

## F5. Standoff sweep: the 1/r law fails instructively (Stage 5b)

Three standoffs (r = 24, 52, 100), 7-case FL sweep each, all 21 cases byte-exact vs mirror.

| slope Δkx1/FL @ π/4 | naive 1/r prediction | measured |
|---|---|---|
| r = 24 | −0.00663 | **−0.00293** |
| r = 52 | −0.00306 | −0.00302 |
| r = 100 | −0.00159 | **−0.00019** |

- **Saturation** r=24 ≈ r=52 (ratio 0.969): the path integral of A_x over the full line is r-independent (∫dy/(x²+dy²)dx = π), so no integral mechanism can grow as 1/r.
- **Collapse and sign flip at r=100** (Δcx1 = +0.143 at +π/4, still FL-odd but reversed; null cx = 358 vs 340 — the packets miss the disk diffraction fan entirely).

**Verdict:** the recoil is dominated by the **near-field transit region at the shield edge**, not the distributed 1/r tail of A.

## F6. The missing cell: no shield, no recoil (Stage 5c)

Flux without the disk (WALL=1 everywhere, links unchanged), same r=52 geometry. Byte-exact vs mirror.

- Channel-1 slope collapses −0.00302 → **+0.00066** (noise level, sign flipped).
- Odd symmetry destroyed: ±π/4 pairs +0.346 / −0.550 are no longer mirror images; channel 2 absorbs the core-crossing momentum asymmetrically.
- Null heals: kx1 = 0.29533 ≈ K₀, cx1 = 358.91 (= the r=100 no-grazing null).

**The closed 2×2:**

| | flux | no flux |
|---|---|---|
| **disk** | recoil (F4) | nothing (FL=0 null) |
| **no disk** | **nothing (F6)** | trivial |

**Verdict:** the recoil requires the **flux-threaded hole**. The mechanism is shield-edge circulation — partial waves winding the disk on both sides, recombining with FL-dependent phase (a ring-interferometer geometry pinned to the shield). This is a measurement, from the wavefunction side, of the Kang position: the shield is not a passive detail, it is where the momentum transfer happens.

## F7. The recoiling coil: momentum closure measured, not assumed (Stage 6)

The flux source was given a dynamical degree of freedom: coil = disk+flux composite (the shield *is* the solenoid core), free mass MC = 5·M₀, constrained to x, coupled by impulse form F = −ΔPKX per step, with WALL and links rebuilt around the moving center. The coil is the momentum sink for everything that hits the shield — FL=0 diffraction recoil (control) and the FL-dependent AB kick (signal). Five cases (0, ±π/2, ±π); **byte-exact vs the C mirror on all 55 trajectory prints and all final states.**

- **The coupling is stable and physical**: V ≈ 0 until t≈1000, ramps through the transit window (t = 1000–1600), plateaus after. No ringing, no runaway. The kick is transit-localized *on the source side* — the F5 locality result confirmed from the other end of the momentum pipe.
- **Control (FL=0)**: the coil absorbs ~67 momentum units (~17% of the packet's forward momentum) as diffraction recoil, drifting Q = 9.081 sites to V = 0.010216.
- **Signal**: flux *reduces* the recoil — final V = 0.010193 (+π/2), 0.010171 (−π/2), 0.010101 (+π), 0.010055 (−π). Coil ΔP(+π) ≈ **−0.76 units**; FL-odd component ≈ +0.30.
- **Closure**: the live coil loses **0.76 units** at +π (MCFAC=5) — and the heavy-coil control (MCFAC=50, byte-exact vs mirror: V = 0.0010656 / 0.0010631 / 0.0010599 / 0.0010524 / 0.0010458, Q = 0.948 → 0.931) gives **0.87 units**. The transferred impulse is mass-independent within 15%, so the closure value is **0.8 ± 0.1 units at π, measured by the coil**. The static Stage-5 wavefunction estimate (+0.62) is the underestimate — its per-channel Δkx·W bookkeeping assumed a 50/50 channel-mass split and ignored late-time dispersion mixing; the coil integrates everything with no bookkeeping choices. Momentum conservation across the AB coupling is a measurement, not an assumption.
- The modulation is mostly FL-even — the band-curvature component (F4) appearing on the coil, as it must.
- The static-link engine of Stages 2–5 is the MC→∞ limit of this file.

**Verdict:** with a dynamical coil, the recoil has somewhere to go, and it goes there in the transit window, in the amount the wavefunction side predicted. The full chain — phase accumulation (F1), reversibility (F3), canonical/kinetic split (F4), shield-edge locality (F5), topology requirement (F6), source-side momentum closure (F7) — is now measured end to end.

---

## F8. The clean flux line: the true recoil is an interference gate (Stage 7)

Exact-gradient Peierls links (atan2 angle differences; plaquette flux *identically* zero outside the core) in the Stage-5 instrument, all 9 cases **byte-exact vs mirror**:

- **The true AB recoil is ~17× the linearized measurement and opposite in sign at small FL.** At +π, channel 1 keeps 97% of launch momentum (kx1 = 0.290 ≈ K₀ = 0.3) and advances **+17.37 sites** (linearized: −1.0). At +π/4: +5.35 (linearized: −1.0).
- **The gate function is (1−cos FL).** Channel-sum displacement: 4.04 / 14.05 / 30.10 / 30.73 at π/4 / π/2 / +π / −π, collapsing to 1.92 / 3.14 at ±2π — matching the two-path interference term (0.29 : 1 : 2 : 2 : 0) to a few percent. **The recoil is AB scattering, not a −A velocity shift**: momentum dump into the shield is extinguished when the circulation paths around it interfere destructively in the backward channel (half-integer flux) and restored at integer flux. Flux-periodic with period 2π, as physics demands.
- **The exact symmetry**: dcx1(−FL) = dcx2(+FL) to ~0.1 site — reflection composed with flux reversal.
- **Integer flux is null in both link schemes** (+2π: Δcx1 = +0.33 both) — gauge invariance verified at the instrument's precision.
- **The −2π winding-direction asymmetry (+2.09) is identical to 8 digits in both schemes** — discretization-independent, promoted from suspected artifact to open physics: the engine distinguishes winding *direction* at full flux.
- **Live-coil, exact links, engine-verified (7 cases, byte-consistent with mirror):** final V = 0.0102164 (0) / 0.0067193 (+π/2) / 0.0067936 (−π/2) / **0.0022339 (+π) / 0.0022346 (−π)** / 0.0097185 (+2π) / 0.0096238 (−2π). The gate holds on the source side: coil impulse ΔP = 23.1 / 22.6 at ±π/2, **52.7 / 52.7 at ±π**, 3.29 / 3.91 at ±2π — the (1−cos FL) law at two independent flux points, ±π symmetric to 0.02 units. At π the transit-window V-ramp is suppressed 3× at t=1000: the momentum genuinely never leaves the packet (closure holds trivially at the gate null — there is nothing to close).
- **The ±2π winding asymmetry is now seen three ways**: static (both link schemes, +2.09 identical to 8 digits) and live source-side (3.29 vs 3.91). The coil distinguishes winding direction at full flux. Headline open physics.
- The live-2π residual vs FL=0 (ΔP ≈ 3.3–3.9) is attributable to the moving flux line's EMF (time-dependent gauge — real live-coil physics, separate thread) plus the winding asymmetry.

**Verdict:** with a clean flux line, the shielded AB system is an interference-gated scatterer. The linearized-link fringing field was large enough (~0.2 rad of spurious phase on circulation paths at TH=0.5) to close the gate; F4–F7 measured that fringing-field regime. Re-measurement of the standoff, no-shield, and live-J campaigns with exact links is now queued.

---

## F9. The winding asymmetry is core-boundary physics (T1/T2, engine-verified)

Two mirror-verified probes of the ±2π winding-direction split, which between them self-corrected:

- **T1 (resolution doubling, 1024², everything ×2, K0 fixed):** split 1.75 → 2.11 sites; transverse kick ~±3 sites at both resolutions. Read in isolation this leaned "lattice-pinned artifact." All 5 cases byte-exact vs mirror (cx −1.00 indexing offset, as always).
- **T2 (radius sweep at fixed 512², r = 8/12/16):** the split **grows steeply with core radius — 1.76 / 5.39 / 8.03 sites (~r^1.8)**. A staircase artifact would *shrink* as the disk smooths with r; the opposite happened. The lattice-artifact reading is dead.
- **T1's near-constancy explained:** the hi-res run also doubled the standoff (2.48λ → 4.95λ), and the split decays with standoff — the two scalings cancelled. Independent confirmation: the π gate amplitude at 512² is 30.1 / 27.6 / 18.4 across r = 8/12/16 (still strong at r=16) but collapsed to 4.3/4.8 at the hi-res standoff. **The "transparency collapse" reported after T1 was standoff dilution, not a core-size resonance.**
- The transverse (y) kick at ±2π is winding-odd, ~2–3 sites at all radii (dcy1-odd −4.37 / −5.91 / −5.04 at r = 8/12/16).
- Gate remains gated at all radii: sum2pi = 1.9/3.1, 2.0/2.9, 1.3/2.0 (vs ~19–31 at π).
- dkx at ±2π ≈ 0 at r=8 (−0.00153) — no net momentum transfer at the null, consistent with the centroid shift being a near-field redistribution.

**Verdict:** the engine's handedness knowledge at full flux is a **near-field circulation effect around the finite cored hole** — dynamical phase residue that the topological phase cannot cancel at 2π, growing with core radius and dying with standoff. Not a discretization artifact, not continuum point-flux AB (which must be null at 2π): it is the genuine physics of a flux-threaded *finite* hole with a wall — the system the engine actually models. The ±2π winding asymmetry stays on the books as physics, mechanism attached.

---

## F10. The gate's standoff law, and the split's oscillation (Stage 8, engine-verified)

Exact-link standoff sweep (core r=8 fixed; standoffs 24 / 52 / 100 sites = 1.14 / 2.48 / 4.76λ), 15 cases byte-exact vs mirror:

- **Gate amplitude decays steeply with standoff:** sumpi = **92.04/92.62** (s24) → **30.10/30.73** (s52) → **0.78/1.11** (s100). At one wavelength from the core the transparency is 3× the Stage-7 value; past ~5λ the gate is shut at any flux. F5's core-locality confirmed in the fringing-free regime: **the gate is a near-field object.**
- **The winding split is not monotonic — it changes sign:** +5.15 (s24) → −1.76 (s52) → +3.82 (s100), with dcy1-odd 0.12 / −4.37 / −0.76 following its own pattern. Hypothesis (marked as such): oscillatory radial dependence — winding ±1 couples to different radial scattering orders, and the standoff sweep is sampling across a node. Consistent with the F9 near-field mechanism, but the s=100 uptick means a **longer-ranged component** exists beyond the near-field term.
- **At s24 the 2π null is not clean:** dkx1 = +0.0075 / −0.0039 — real momentum transfer at integer flux at close range (strong near-field residue), unlike s52 (dkx ≈ 0).
- **Stage 5b's linearized-link sign flip at s=100 does NOT reproduce with exact links** (dcx1 at +π stays positive, +1.89) — retired as fringing-field behavior.
- Null-case diffraction drag quantified: kx_null = 0.168 / 0.243 / 0.292 at s = 24/52/100 (launch 0.3).

**Verdict:** the gate law is mapped and steep; the winding asymmetry has (at least) two components — a near-field residue (F9) plus a sign-changing longer-ranged term. Next isolator: aimed single-packet instrument (one packet, one winding, no second channel) to separate far-tail instrument residue from genuine long-range winding physics.

---

## F11. The two effects, separated (Stage 9, engine-verified)

Aimed single-packet instrument (one packet below the core, standoffs 52/100, no second channel), 10 cases byte-exact vs mirror:

- **The gate vanishes single-packet.** FL-even sums ≈ 0 (sumpi = −0.016, sum2pi = −0.064 at s52) — a one-sided passage shows no (1−cos FL) structure at all. Retroactive proof of the F8 mechanism: the gate *is* two-path interference; it needs both circulation paths sampled coherently.
- **The winding handedness is a one-sided local deflection.** Single-packet displacement is purely winding-odd and ~linear in FL: dcx ∓1.6 at ∓π growing to ∓3.3 at ∓2π (s52), with a comparable TRANSVERSE component (dcy ∓2.3 → ∓4.7). It does not return to zero at integer flux — topology cancels closed-loop phases only, and a one-sided passage never closes a loop.
- **Magnitude ≈ ⅓ of the naive local-A push:** dkx = −0.0060 vs FL/(2π·s) = −0.019 at 2π, s52 — sensible for a packet sampling a spread of closest-approach distances.
- **Nearly standoff-independent:** split 6.55 (s52) / 6.00 (s100).
- **F10's U-shaped, sign-changing split demoted:** not two physical components. The two-packet instrument reads this same ~constant one-sided push through the two-channel interference mask; the mask's phase varies with standoff, so the push reads out amplified (s24), cancelled/reversed (s52), or partially restored (s100). No long-range second component required.
- **Direction structure at 2π:** +2π repels and drags (cx −3.3, cy away-from-core −4.7, kx −0.006), −2π attracts and boosts — direction-dependent phase shift from scattering off the wall+circulation system is the mechanism sketch (theory, unverified).

**Verdict:** the campaign's two AB effects are now cleanly separated. (a) One-sided local deflection: winding-odd, ~linear in FL, ungated, persists at integer flux, ~⅓ of local-A magnitude — this is the "handedness at full flux" signal, isolated and explained in shape. (b) Two-path interference gate: flux-periodic (1−cos FL), requires both paths, near-field (F10 standoff law). The winding-asymmetry thread (F8→F9→F10→F11) is CLOSED: the engine distinguishes winding direction at 2π because a one-sided wave is not a closed loop, and integer flux is only topological for closed loops.

## Synthesis

Across Stages 4–5 the campaign established, each at mirror-verified precision:

1. Wavefunction phase and field-momentum ledger are the same book (F1, F2).
2. The dynamics are exactly reversible; irreversibility is bookkeeping precision in the absorber only (F3).
3. The AB "recoil" is the canonical/kinetic momentum split, measured directly with the covariant derivative (F4).
4. That split is not distributed along the path — it is generated at the shield edge (F5).
5. Remove the hole and the effect vanishes: the flux-threaded ring geometry is necessary (F6).
6. With a live coil, momentum closes: source-side loss balances wavefunction-side gain, transit-localized, at measured magnitude (F7).

The doors this opens (per the campaign's long-range interest in recoil physics): any device that extracts AB momentum transfer must give the wave a loop to wind — the shield geometry, not the flux tail, is the actuator.

**Stage-7 addendum:** the clean-flux-line measurement (F8) strengthens and sharpens this: the actuator is the *interference gate* around the flux-threaded hole, and it is flux-tunable — momentum transfer switches from full to (nearly) zero across half a flux quantum. A recoiling-flux-line device is a flux-controlled momentum valve. Links 3–6 of the chain above were measured in the fringing-field regime and are queued for re-measurement with exact links; links 1–2 stand as measured.

## Open items

- **EXACT-LINK RE-MEASUREMENT**: live-J done (F8), standoff sweep done (F10), single-packet isolation done (F11). Remaining: no-shield 2×2 with exact links (at the gate null the wave should pass the core almost freely), plus a heavy-coil (MCFAC=50) exact-link control.
- **The ±2π winding-direction asymmetry — CLOSED (F11)**: one-sided local deflection, winding-odd, ~linear in FL, ungated; topology can't cancel what never closes a loop. F10's sign changes were the interference mask, not a second component. Remaining theory item: the direction-dependent phase-shift mechanism (repel+drag vs attract+boost) deserves an analytic partial-wave treatment.
- **Moving-flux EMF residual** (3.29 units at live 2π): time-dependent gauge physics of the recoiling coil; isolate by comparing live-2π at two coil masses. Note post-F11: part of this residual is presumably the one-sided deflection acting on the coil-side ledger — the EMF isolation should subtract the F11 static value first.
- **Gate-law mapping**: the (1−cos FL) channel-sum fit is empirical; measure at FL = π/8, 3π/8, 5π/8, 7π/8 to nail the functional form and its standoff dependence.
- **Live-coil ±2π at two standoffs**: does the source-side impulse carry the F11 standoff-insensitive one-sided push, or the masked two-packet value?
- **Compiler**: hoist PARAMETER-sized arrays to static storage (T1/T2/Stage-8/9 files use STATIC declarations — the workaround is now the house style). Full fix-list in `ERGO_FIX_FIRST_LIST.md`.

## Files

| file | stage |
|---|---|
| `ab_pi_ledger.ergo` | 4a |
| `ab_pi_ledger_flip.ergo` | 4b |
| `ab_time_rewind.ergo` | 4c |
| `ab_disk_rewind.ergo` | 4d |
| `ab_recoil.ergo` | 5 (linearized links) |
| `ab_recoil_standoff.ergo` | 5b (linearized) |
| `ab_recoil_noshield.ergo` | 5c (linearized) |
| `ab_livej.ergo` | 6 (linearized) |
| `ab_livej_m50.ergo` | 6b (linearized, heavy coil) |
| `ab_recoil_exact.ergo` | 7 (exact links — clean flux line) |
| `ab_livej_exact.ergo` | 7b (exact links, live coil, ±2π) |
| `ab_recoil_exact_hr.ergo` | T1 (resolution doubling, 1024²) |
| `ab_recoil_radius.ergo` | T2 (radius sweep r=8/12/16) |
| `ab_recoil_soff_exact.ergo` | 8 (exact-link standoff sweep) |
| `ab_single_2pi.ergo` | 9 (aimed single-packet isolation) |

All verified against C mirrors (`gcc -O2`, no dependencies); mirror sources available on request.
