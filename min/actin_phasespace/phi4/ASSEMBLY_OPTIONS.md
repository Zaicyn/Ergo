# ASSEMBLY OPTIONS — how to fix brush engagement (O-R3), informed by actin_swarm lineage (2026-09-02)

Trigger: R5 smoke (brush_br2, N_tot=200, MAXF=20) failed O-R3 (n_eng=1.26,
goal ≥3) and O-R4 (slot ceiling 48%). Structural diagnosis: filaments
nucleate at the base gate (x≈2), capped-equilibrium length n̄≈8.5; tips
reach the membrane (margin x≈10.4) only at len ≳15 — branching raised
filament NUMBER (N_f≈18.7), not membrane-proximal pusher density.

The actin_swarm docs (BRIEFING/COMPARE/INTEGRATION_BRIEF + m4c RESULTS)
contain several *certified* assembly mechanisms. Candidate levers:

## S1 — Budget bump (N_tot 200→400, MAXF 20→32)  [approved; running]
- Lever: more filaments at the same capped-equilibrium length → more
  chance reachers. Nothing structural changes.
- Prediction: N_f≈35, n_eng ≈ N_f·P(len≥15) ≈ 2–3 — *marginal* vs goal.
- Cost: parameter-only; ~2× step cost. Risk: low. Reuses: nothing needed.

## S2 — M4C side-branching with certified 8-spring junction (port from actin_swarm/m4c_branching)
- Mechanism: branch fires on SIDE host monomers (bound, non-barbed,
  unprotected, ≥3 barbed-side neighbors; eligibility further restricted to
  hosts within DBR of the membrane margin in brush context). Daughter
  trimer placed at certified build angle 62.5° (relaxes to 69.2±7.4° —
  angle_oracle.py certified), offset BLAT=0.9/BAX=−0.2, pinned by 8 springs
  (KFIL=100, rests BRB1..8) to 4 host-segment beads; host..host+3
  unbind-protected (HPROT); daughter pointed-capped.
- Effect: ONE mother that reaches the membrane converts into a CLUSTER of
  daughters born inside the engagement zone, mechanically held at the
  mother tip ≈ membrane. Dendritic tree topology — the real Arp2/3
  geometry, and the topology later rungs (gel/crawl) need anyway.
- Cost: moderate port (junction springs into REBUILD_BONDS, HPROT array,
  eligibility scan; RNG slots). Certified assets reused: build angle,
  BRB rests, KBR_eff ×1.11 renormalization, angle oracle.
- Risk: port bugs → mitigated by the standard ladder (FD on loaded
  junction, static byte cert, isolated KBR recalibration).

## S3 — Plane NPF de-novo nucleation (membrane-attached, no mother)
- Nucleate trimers directly AT the plane with a pointed-end anchor spring
  (reuse NUC/KSEED machinery, anchor target tracks xp). Engagement by
  construction. But abandons the dendritic question — a different rung
  (registered in plan_branch.md as the O-R5 falsification lever).

## S4 — Hybrid membrane-branching
- Branch from zone-eligible mother tips (current chemistry) but anchor the
  daughter pointed end AT the plane. Keeps branching, guarantees daughter
  engagement. Semi-ad hoc biologically (Arp2/3 doesn't anchor to the
  membrane; NPFs do).

## S5 — M4D crosslinking
- Cohesion/bundling, not reach. Does not move n_eng. Defer to gel rung.

## Decision procedure (empirical, sequential, lock-step)
1. **S1 smoke first** (cheap, approved): if O-R3 passes (n_eng≥3,
   P(bare)<0.05) and O-R4 ceiling clean → cheapest path wins, proceed to
   Stage C ensemble.
2. If S1 marginal/fails → **S2** is the structurally correct fix (certified
   dendritic junction, zone-restricted eligibility) with S4 as shortcut
   fallback. S3 only if the dendritic hypothesis itself falsifies.

## 400-generation hygiene folded into the S1 build
- Slot-map rebase (collisions crept in as N grew: Langevin 1..3NB reached
  1200 at NB=400, colliding with capping 1001..1020, uncap 1101..1120;
  hydrolysis 600+M collided with Langevin since N=150, and with dimers
  710+M for M≥111 — documented inheritance, physically negligible at
  P~1.5e-4 but statistically impure):
  Langevin 1..2400 | kinetics 3000+4(F-1)..+3 (F≤32) | hydrolysis 3200+M |
  dimers 3700/3702/3710+M | piston 4200 | cap 4300+F | uncap 4400+F |
  branch 4500+2(F-1)/4501+2(F-1). All disjoint for N≤400, NB=800, MAXF=32.
- O-R6 instrument fix: fbr line extended with mother axis components
  (gate-safe: fbr exists only when PBR=1; no draw changes).
- Guards (SEGFIX) carried over unchanged; NFILH(33).
