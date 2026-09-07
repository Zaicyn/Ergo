# Integration brief — full actin scaffold (M4b+M4c+M4d merged)

You are merging four independently-certified mechanism builds into ONE engine
+ ONE mirror: the full actin scaffold (dendritic branched network, two-ended
kinetics with treadmilling, ATP hydrolysis aging, transient crosslink gel).

FIRST read, in this order:
1. `/mnt/agents/output/actin_swarm/BRIEFING.md` — dialect, oracle ladder, pitfalls.
2. This file — composition decisions are ALREADY MADE below; don't redesign them.
3. The four source builds + their RESULTS.md (skim for the "gotchas" sections):
   - `/mnt/agents/output/actin_swarm/m4c_branching/` — branching.ergo + branching_mirror.py (**STRUCTURAL BASE**)
   - `/mnt/agents/output/actin_swarm/m4b_pointed/` — treadmilling.ergo + treadmilling_mirror.py
   - `/mnt/agents/output/actin_swarm/m4h_hydrolysis/` — hydrolysis.ergo + hydrolysis_mirror.py
   - `/mnt/agents/output/actin_swarm/m4d_crosslink/` — crosslink.ergo + crosslink_mirror.py

## Composition design (fixed — implement this)

**Base**: M4C's branching build (multi-chain arrays, symmetric BP1..BP6
bonded-partner slots, FILBONDS FX/FY fix). Everything else grafts onto it.

**Topology**: NFMAX=8 chains, N=90 monomers, box 12³ (M4C's geometry).
Chain 1 = the anchored seed chain with a LIVE pointed end (M4B machinery:
pointed bind/unbind, anchor transfer/NPF re-grip). Chains 2..8 = Arp2/3
branches, pointed-capped. All chains have live barbed ends.

**Feature flags** (PARAMETER INTEGER): DOPOINTED=1, DOHYD=1, DOBRANCH=1,
DOLINK=1. Each mechanism must be individually switchable so isolated rate
re-calibration can run in the merged binary.

**Kinetics per end, state-dependent (M4B × M4H merged)**:
- Barbed unbind, every chain: NUC-dependent — KOFFB_T=0.045 (ATP terminal),
  KOFFB_A=0.18 (ADP terminal) [M4H values].
- Pointed unbind, seed chain only: KOFFP_T=0.05 (ATP), KOFFP_A=0.10 (ADP)
  [M4B's effective 0.10 kept as the ADP rate, 2× contrast mirroring M4H].
- Binds: barbed KON=500 saturated (all chains); pointed KONP=1.0
  (seed chain only) [M4B].
- Release distances: barbed 1.65 (RCAP+0.25), pointed 2.5 (RCAP+1.1) —
  the asymmetry is load-bearing (anchored stationary window self-recapture).
- Hydrolysis: NUC per monomer, P=KHYD·DT=0.03·DT per bound ATP monomer per
  step; free pool ATP; binds set NUC=1; unbinds recharge to 1 [M4H].
- Branching: M4C's exact machinery — KBR=0.02 (eff ×1.11 documented),
  62.5° build angle, 8-spring junction, daughters spawn as ATP trimers.
- Crosslinks: M4D's exact machinery — KLINK=20, L0=0.7 fixed, RLINK=1.0,
  KLINKF=0.3, KLINKB=3.0, MAXL=64, LOOPMIN=6, **including the 98-offset
  far-cell candidate pass**. Inter-chain links are the whole point (gel).

**RNG draw slots (collision-free, already reserved)**:
500/501 barbed bind/unbind (per chain K: 500+2K, 501+2K if the M4C build
already per-chain-slots them — follow M4C's existing convention and extend
it), 502/503 pointed, 600+M hydrolysis, 700+K branch, 800+L link.
EVERY step consumes the same slots regardless of what fires. Document the
final slot map in a comment block at the top of the engine.

**Pool arithmetic check (do this BEFORE running)**: steady state needs
Σ(off-rates) < kon·c0·NF_eff. With N=90, c0=87/1728≈0.050, kon≈2.1e-2,
koff_b_eff≈4.1e-4 (M4H measured), expect M* ≈ 90 − c**·1728 with
c** = (NF·koff_b + koff_p)/(NF·kon). Compute it, print the prediction in
RESULTS.md, and flag if the regime is degenerate (M* < 20 or > 85).

## Cert contract (same ladder, integration-grade)

1. **FD** ≤1e-8 on a config loading ladder + branch springs + ≥2 links +
   anchor + walls, all uncapped, out of WCA cores.
2. **Static byte cert** ≤1e-11: formula-generated config with mother hexamer
   + one branch trimer + ≥2 known-strain links + NUC pattern + spiral gas.
   CFG/FRC/CERT rows + NUC rows byte-compared engine vs mirror.
3. **Isolated rate re-calibration IN THE MERGED BINARY** via flags:
   - DOLINK=0,DOBRANCH=0,DOPOINTED=0,DOHYD=1 → reproduce M4H:
     koff_ATP/koff_ADP/khyd within 10% of nominal.
   - DOPOINTED=1,DOHYD=0,branch/link off → reproduce M4B: koff_b/koff_p
     within 10%.
   - DOBRANCH=1 only → reproduce M4C: KBR_eff ≈ 1.11× nominal ±20%.
   - DOLINK=1 only → reproduce M4D: birth/death within 10%.
   (These prove the merge didn't cross-contaminate rate paths.)
4. **Full phenomenon runs** — all flags on, 300k steps, ≥2 seeds, engine AND
   mirror (M4H's τ≈100k equilibration lesson; mirror is slow, use nohup and
   checkpoint logs to /mnt every ~10 min — /tmp CAN BE WIPED MID-RUN).
   Report: total bound M(t) vs multi-chain ODE with hydrolysis-weighted
   koff_b_eff; branch count; link count vs its mean-field; ATP cap profile
   on the seed chain; pointed ratchet count vs |net_p|·steps identity;
   kT pinned at 0.4; fmax; engine/mirror agreement within 2σ on second-half
   means of M, links, natp.
5. **Health gates**: no runaway coiling (efil strain bounded), no anchor
   strain blowup (eanch < ~5 sustained), nout=0, no crash.

## Deliverables — /mnt/agents/output/actin_swarm/integration/

scaffold_full.ergo, scaffold_full_cert.ergo (MIRROR=1),
scaffold_full_mirror.py (--fd/--cert/--cal/--run/--full), cert dumps,
all run logs, INTEGRATION_RESULTS.md (parameter table, slot map, all cert
numbers, isolated-recalibration table, phenomenon results per seed,
engine/mirror comparison, deviations-with-mechanisms).
Work in /tmp/m4i/ (toolchain: cp -r
/mnt/agents/output/actin_swarm/toolchain/ergo_mcl /tmp/m4i/). CHECKPOINT to
the persistent dir after every milestone.

Final message to lead: 10-line summary — FD, cert diff, the four isolated
recalibration ratios, full-run engine/mirror agreement numbers, kT/efil/eanch
health, and any composition surprises (mechanisms interacting unexpectedly).
