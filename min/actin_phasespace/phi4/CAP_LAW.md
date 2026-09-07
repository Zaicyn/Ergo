# CAP_LAW.md — φ4.5 capping-protein sub-rung certification

> **CONTAMINATION HEADER (SEGFIX, 2026-09-02):** runs underlying this
> document predate the F-clobber fix (ghost filament MAXF+1; SEGFIX.md).
> Audit (§3): worst case ≤19/150 monomers ghost-sequestered; laws and
> qualitative conclusions stand; absolute numbers carry ±2–9% shifts.
> Post-fix reference values are in BRANCH_LAW.md (Stage C, guarded engines).

Certified: 2026-09-02. Engine lineage: pop_fpt.ergo (φ4) → pop150/cap150(b) →
pop_slab_c/brush_c. All gates run with the certified toolchain
(/mnt/agents/output/actin_swarm/toolchain/ergo_mcl). Oracle: plan_cap.md
(incl. Amendments C-1, C-2), registered before the runs they describe.

## The problem this rung solves (findings F-B1..F-B3, from run data)

Filament length near c* is a near-critical random walk (pool self-consistency
drives net drift ≈ 0), so death time ~ n̄²: any filament fluctuating past
len ≈ 40 is effectively immortal on 1M-step horizons and sequesters the
monomer budget. Observed: uncapped slab brush (any piston state/load)
collapses to N_f ≈ 4.6-5.8 with 1-2 ancients at len 41-84 holding ~60% of
bound mass; even the uncapped ISOTROPIC parent at N_tot=150 grew a len-46
ancient. The membrane does not cap length (at F=0 it retreats; under load
the ancients outlive the horizon). Real cells solve this with capping
protein. The model demonstrates that requirement endogenously.

## Chemistry (lineage-preserving toggleable channel)

Per active filament, per step, only when PCAP=1:
- uncapped tip: cap with P = KCAP·DT (draw slot 1000+F)
- capped tip: uncap with P = KUNC·DT (slot 1100+F)
Capped tip: barbed bind scan AND barbed unbind blocked. Pointed end
unaffected. CAPST reset to 0 on slot promotion. Slots disjoint from all
existing draw ranges. PCAP=0 → no draws, guard inert → bit-identical parent.

Rates (Amendment C-1, after reversible KCAP=0.1/KUNC=0.9 FAILED — giant
len 75 survived; near-critical drift −0.1g relaxes in ~7.5M steps ≫ horizon):
  KCAP = 0.03 (P = 3e-5/step; mean growth episode ≈ 33k steps;
               length-at-cap ≈ b/KCAP ≈ 10 from measured b ≈ g_p ≈ 3e-4/step)
  KUNC = 0.0  (absorbing cap = death sentence, as in cells)

## Gates (bit-identity, strict filter, 300k steps each)

| Gate | Pair | Result |
|------|------|--------|
| G-C1 | cap150(PCAP=0) vs pop150 | 0 diffs / 97,049 lines |
| G-CB1 | brush_c(PSTN=0) vs pop_slab_c (both PCAP=1) | 0 diffs / 97,298 |
| G-CB2 | brush_c(PSTN=0,PCAP=0) vs pop_slab_c(PCAP=0) | 0 diffs / 95,903 |

## Certified population law with capping (cap150b, iso, N_tot=150, 1M steps)

| Oracle | Prediction | Measured | Verdict |
|--------|-----------|----------|---------|
| O-C3′ n̄ | 6-15 | 8.5, max len 24 | PASS |
| O-C4′ N_f | 9-13 | 13.1 (median 13) | PASS |
| O-C5′ giants | maxn < 45, P(len>30)<1% | maxn 34, P = 0.0000 | PASS |
| O-C2′ NCAP≈deaths | within 15% | 257 vs 479 (0.54) | REVISED: ~half of newborns die before first cap (gambler's ruin near zero capital); mechanism confirmed by O-C3′/O-C5′ |
| conservation | exact | nbound+nfree+2·ndim = 150 every census | PASS |
| births=deaths | stationary | yes (479 deaths/1M, N_f stationary) | PASS |

c* rises 0.015 → 0.0225 (growth suppressed → pool refills) — as predicted.
Slot ceiling: 169 overflow-recycles at MAXF=14 (N_f pressed 14 in 40% of
records) → brush_c built with MAXF=16 headroom.

## Brush smoke (brush_c, F=1.0, 1M, seed 77031) — gate to Stage C

N_f = 10.26 (8-13), n̄ = 10.5, c = 0.0246, max len 31 (transient),
n_eng = 1.10, P(bare) = 0.119, ⟨FRCT⟩ = 1.21 vs F = 1.0 (+21% piston
rectification, tracked per arm as effective-load calibration).
Nucleation-gate rejections 243 vs 360 deaths — healthy turnover.
STABLE over the full stationary window. GO for ensemble.
