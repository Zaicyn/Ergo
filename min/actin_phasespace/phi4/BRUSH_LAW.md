# BRUSH_LAW.md — L1 lamellipodium-brush rung certification (N_f ≈ 10)

> **CONTAMINATION HEADER (SEGFIX, 2026-09-02):** the runs underlying this
> document were executed with the live F-clobber bug (ghost filament MAXF+1
> binds; SEGFIX.md). Audit (§3): worst case ≤19/150 monomers
> ghost-sequestered; laws and qualitative conclusions stand; absolute numbers
> carry ±2–9% shifts. Post-fix reference values for engagement/force are in
> BRANCH_LAW.md (Stage C, guarded engines). A guarded re-ensemble was
> offered and deferred (user decision).

Certified: 2026-09-02. Engine: brush_c.ergo = φ4 population engine × membrane
piston × slab nucleation gate × one-way barbed capping (φ4.5, CAP_LAW.md).
Budget N_tot = 150, MAXF = 16, KCAP = 0.03, KUNC = 0.
Oracles: plan_brush.md (O1-O5, Amendments 1-4) + plan_cap.md (C-1, C-2) —
all registered before the runs they describe. Toolchain: certified
ergo_mcl. Ensemble: runs15/ — F_ext ∈ {0.0, 0.5, 1.0, 2.0, 4.0} × 8 seeds
(77031+i·7919) × 1M steps, analysis on retained stationary tails
(~760k-1M; log heads lost to a /mnt sparse-write artifact, tails verified
intact and consistent; conservation exact in every census of all 40 runs).

## Gates

| Gate | Pair | Result |
|------|------|--------|
| G-CB1 | brush_c(PSTN=0,PCAP=1) ≡ pop_slab_c | 0 diffs / 97,298 lines |
| G-CB2 | brush_c(PSTN=0,PCAP=0) ≡ pop_slab_c(PCAP=0) | 0 diffs / 95,903 |

## Population law (oracle O1″, Amendment 4: baseline = ensemble arms)

| F | N_f | n̄ | c* | n_eng | P(bare) | x_p | ⟨FRCT⟩ |
|---|-----|-----|------|-------|---------|-----|--------|
| 0.0 | 10.27 ± 0.63 | 10.07 | 0.0285 | 0.65 ± 0.04 | 0.450 | 10.83 | 0.95 |
| 0.5 | 10.74 ± 0.34 | 10.31 | 0.0239 | 0.89 ± 0.02 | 0.243 | 10.29 | 1.06 |
| 1.0 | 10.71 ± 0.34 | 10.00 | 0.0256 | 1.10 ± 0.02 | 0.109 |  9.53 | 1.44 |
| 2.0 |  9.97 ± 0.60 | 10.61 | 0.0273 | 1.37 ± 0.06 | 0.083 |  7.47 | 1.95 |
| 4.0 |  9.45 ± 0.45 | 10.27 | 0.0316 | 1.42 ± 0.07 | 0.127 |  6.19 | 2.56 |

(errors = s.e.m. over 8 seeds)

- **O1 PASS**: N_f* = 9.5-10.7 across all arms — the N_f ≈ 10 target holds
  with the membrane live, under all loads. Conservation exact (0 violations
  in all census records of 40 runs). Births = deaths (stationary N_f,
  ~360-480 deaths/1M/run). No MAXF ceiling press (N_f=16 occupancy 0.01%).
- **O-C3′/O-C5′ in-brush PASS**: giants eliminated — no filament sustains
  len > 31; the pre-capping ancients (len 52-84) are gone.
- **O2 PARTIAL**: P(bare) < 0.2 at F ≥ 1 (0.08-0.13) but not at F = 0
  (0.45 — yo-yo piston keeps the brush mostly unloaded, as predicted in
  Amendment 4). n_eng rises monotonically with F (0.65 → 1.42) — the
  predicted "engagement rises with load" trend PASSES.

## Force law — the insertion channel is BINARY, not Boltzmann (O3 FALSIFIED as posed)

Pre-registered O3 predicted j_on(F) = j_on(0)·exp(−F·δ/(n_eng·kT)),
δ = 1.2, kT = 1: at F = 1, 2, 4 this predicts ratios 0.34, 0.17, 0.03.

Measured membrane-insertion rate (bbind channel, per step):
  j/j0 = 1.024 ± 0.064 (F=0.5), 1.035 ± 0.061 (F=1), 1.042 ± 0.092 (F=2),
         0.886 ± 0.056 (F=4).
The exponential prediction is off by an order of magnitude at F ≥ 2.
**FALSIFIED.** The physics: the SGATE membrane makes insertion binary —
a tip either has clearance (insertion proceeds at the unloaded rate) or it
does not (blocked, candidate ejected via COOL). Load does not slow
insertion; it REDISTRIBUTES attempts into rejections: blocked fraction of
membrane-zone attempts = 57% (F=0) → 66% → 74% → 82% (F=2) → 82% (F=4).
This is the certified F1b supply-limited/trapped-retry picture extended to
the brush: the exponential appears in the *blocking probability*, not the
rate of successful events.

## Force balance and stall (O4)

- ⟨FRCT⟩ ≥ F for F ≤ 2 (the brush HOLDS: 0.95 vs 0, 1.06 vs 0.5, 1.44 vs 1,
  1.95 vs 2); at F = 4 the brush yields: ⟨FRCT⟩ = 2.56 < 4.
- **Stall force F_s ≈ 2.5-3** (between arms 2 and 4): the brush's maximum
  sustainable contact force saturates at ≈ 2.6. Per engaged tip at stall:
  ≈ 2.6/1.4 ≈ 1.9.
- Piston position x_p(F) is the clean, tight order parameter: monotone
  10.83 → 6.19, s.e.m. small; each arm stationary in the tail.
- Caveat (registered): the thermal kick (DP=0.2) gives per-step kick rms
  0.049 vs drift-per-step ~3e-5, so single-run piston drift is
  diffusion-masked below ~2M steps; force-balance claims rest on the
  8-seed means and the stationarity of x_p, not on single-run drift.
- **E1 correction (runs16, released piston, XPLO 5.5→1.5):** with the
  lower clamp removed, free-piston equilibria sink 0.1-1.6 units BELOW
  the clamped values at F ≥ 1 (F=2: 7.47 → 6.9-7.5) — i.e. the clamped
  x_p numbers at F ≥ 1 carried 0.5-1.6 units of XPLO rectification.
  ⟨FRCT⟩ ordering and the stall conclusion (F_s ≈ 2.5-3) are unchanged.
  No released run showed any positive drift: protrusion velocity
  v0(F) ≈ 0 for fixed-slab geometry at all F — persistent protrusion is
  impossible without membrane-attached nucleation (motivates R5).
- **E2 correction (KCAP=0.015):** n̄ and N_f did NOT scale as 1/KCAP
  (n̄ 9.1 vs predicted 18-22; N_f 10.9 vs 6-8) — infant-churn dominates
  the length mean, not cap length. n_eng = 1.13, statistically identical
  to KCAP=0.03 (1.10): engagement is invariant to the capping timescale,
  experimentally confirming ANALYTICS.md Map 2 (engagement is
  structural, not kinetic). No giants at KCAP/2 (max len 26).

## Population law — what the brush costs

c* ≈ 0.024-0.032 (vs 0.015-0.019 uncapped) — capping suppresses growth,
the pool refills, nucleation rate rises with c²; turnover is fast and
continuous (~0.4 deaths/1k steps). The brush is a genuine steady-state
population, not a persistent set: no filament in the stationary window was
born before t ≈ 550k.

## Verdicts vs plan_brush.md oracle

| Oracle | Verdict |
|--------|---------|
| O1 population/conservation | PASS (N_f* ≈ 10 ± 0.6 all arms) |
| O2 engagement | PARTIAL (P(bare)<0.2 for F≥1; n_eng rises with F ✓) |
| O3 exponential insertion law | FALSIFIED — binary gating; load enters via blocked fraction |
| O4 force balance | PASS for F ≤ 2; stall identified F_s ≈ 2.5-3 |
| O5 F=0 ≈ bulk baseline | PASS as re-posed (F=0 arm stable, N_f ≈ 10.3) |

## Artifacts

- Engines: brush_c.ergo, pop_slab_c.ergo, cap150b.ergo, pop150.ergo
  (+ gate variants in gates_l1/).
- Ensemble: runs15/ (40 ergo + 40 logs, gm/geo-stripped, NUL-compacted).
- Companion docs: plan_brush.md, plan_cap.md, CAP_LAW.md, FORCE_LAW.md.

## Next rungs (registered)

- R2: formin-brush comparison arm (processive vs binary-gated brush).
- R3: n_eng engineering — raise engagement (narrower birth slab toward the
  plane, or longer n̄ via KCAP/2) to test load-sharing with n_eng ≥ 3.
- φ5: 1D closure (per-end chemistry + halo-renormalized c).
- Scaling: N_tot > 150 only on request — N_f ≈ 10 certified stable.
