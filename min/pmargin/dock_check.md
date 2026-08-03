# Fold-then-dock for SdrD — oracle-dock and sim-dock vs all-at-once

Programs: `min/pmargin/gen_dock.py` → `dock_oracle.ergo` (domains at
native PDB internal geometry) and `dock_sim.ergo` (domains at best
per-domain sim folds: A2 blk8 3.38, A3 blk7 2.38, B1 blk1 0.91, B2 blk7
1.82, Kabsch-aligned offline; per-domain native slices verified identical
to the full-chain native). Base: `sdrd_white_full.ergo` (validated
packed white-bath full construct, 556 res, 8 blocks, same schedule:
heat cycles to 1200, floor, quench 38400, 48000 frames). Domain folds
extracted by rerunning the per-domain white programs with structure
dumps (`sdrd_white_{A2,A3,B1,B2}_struct.ergo/.out` — FINAL rows
byte-identical to the validated runs).

## Protocol (documented in gen_dock.py)

- **Assembly init**: each domain rigid (native or sim-fold internal
  geometry), domain COMs spread by 10·(D−2.5) units along a per-block
  white-hash direction → inter-domain backbone bonds start stretched
  ~10 units; docking must close them.
- **Docking dynamics** (what the sim supports): per-residue velocity
  damping (amyloid damped-template pattern) — 0.5 strong on all domain
  beads, 0.9 normal on interface windows ±3 around each boundary
  (150-156, 318-324, 438-444) = the live linkers. The sim has no
  rigid-body domain DOF; per-bead damping is the approximation.
- **Field**: adopted tether continuation (K_LR = 0.3 past D=4.0) in the
  Morse kernel — required since the assembly start puts the
  inter-domain bonds deep in the old plateau.
- **Diagnostics**: IFACE rows (cross-domain native-contact geometry per
  block), DTRACE rows (block-1 full + per-domain RMSD trajectory).

## Results

Final per-block full RMSD (best / mean / median):

| variant | best | mean | median | vs all-at-once (best 13.2 / mean 21.0) |
|---|---|---|---|---|
| oracle-dock | **9.06** (blk 4) | 13.07 | 10.86 | best −31%, mean −38% |
| sim-dock | **9.34** (blk 4) | 12.46 | 11.01 | best −29%, mean −41% |

Block 3 (seed 2.0) is a shared outlier (24.75 / 23.62) — the same
separation direction in both variants docks a domain onto the wrong
face; excluded or included, the means move by ≤1.5.

**Interface geometry (IFACE, 32 cross-domain native contacts):**
28–31/32 satisfied (<0.5 units) in EVERY block of BOTH variants, mean
|D−R0| 0.19–0.27, max ~1.1. The interface contacts form readily and
hold.

**Internal vs placement decomposition** (internal-only RMSD = what the
full-chain RMSD would be if the domains were perfectly placed):

| | internal-only | placement contribution |
|---|---|---|
| oracle blocks | 2.09–2.95 | **8.8–24.6** |
| sim blocks | 2.52–3.38 | **9.0–23.4** |

Placement is ≥90% of the error everywhere. The domains are folded and
the contacts are satisfied; the domains are in the wrong mutual
arrangement.

**Domain integrity during docking (DTRACE, oracle block 1):** the
perfect oracle domains do NOT survive the heat ramp — A2 0→2.71,
A3 0→1.79, B1 0→2.82 by frame 1000 (the 0.5 damping cannot hold them
against the heat cycles); afterwards they are nearly stable (drift
≤0.7 to frame 48000). B2 holds best (0→0.25→0.65). Sim folds hold
their starting errors almost exactly (A2 4.01→4.00; B1 2.82→3.51
degrades; B2 1.74→1.52 improves). Full-chain RMSD drops from ~11.2 to
~10.4 within the first ~6000 frames and plateaus — the placement is
locked in early and never anneals.

## Verdict (per the decision tree)

- **Fold-then-dock BEATS all-at-once**: best 9.06 vs 13.2 (−31%), mean
  ~12.5–13.1 vs 21.0 (−38 to −41%), and it also beats sequential
  staging (which did not improve the all-at-once best case). Both
  variants win; sim-dock ≈ oracle-dock to within noise.
- **Oracle-dock does NOT assemble native placement** — so per the
  decision tree the insufficiency is in the FIELD, with a sharp
  refinement: the interface CONTACTS are not the failure (they form
  and hold, 28–31/32 satisfied); the failure is that the 32-contact
  interface is DEGENERATE AGAINST RIGID-BODY PLACEMENT. Domains sit at
  correct interface distances in a wrong mutual orientation — the same
  degeneracy found in the 1SNO trap, now at construct scale. The field
  lacks placement-pinning restraints (interface
  angle/dihedral/register terms, or more cross-domain contacts).
- **Per-domain errors do NOT propagate**: sim-dock matches oracle-dock
  everywhere (best 9.34 vs 9.06, mean 12.5 vs 13.1) — the protocol is
  not the bottleneck; realistic 0.9–3.4-unit per-domain folds are good
  enough. The deployable protocol works as well as the oracle.
- **Domain integrity caveat (honest)**: the current schedule reshapes
  even perfect domains during the initial heat ramp (0 → 2–3.5 in 1000
  frames despite 0.5 damping). A colder docking schedule (quench-only,
  or heat peak capped) is the obvious follow-up and would let the
  oracle domains arrive at the interface intact — but the placement
  degeneracy, not domain melting, is what caps the final RMSD.

**Follow-ups (ordered):** (1) interface placement restraints —
register/dihedral terms across domain boundaries or a larger
cross-domain contact set (the field fix the anatomy dictates);
(2) cold docking schedule (no heat cycles; the domains then stay at
their input quality, isolating placement cleanly);
(3) rigid-body domain moves (true Monte-Carlo domain docking) if the
sim's move set is ever extended.

Files: `gen_dock.py`, `dock_oracle.ergo`, `dock_sim.ergo` (+binaries,
`.out`s), `sdrd_white_{A2,A3,B1,B2}_struct.ergo` (+binaries, `.out`s),
this report.
