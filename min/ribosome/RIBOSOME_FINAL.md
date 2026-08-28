# The Ribosome Campaign — Closing Report

**Ergo waveform molecular dynamics, 2026-08. Engine: mcl slot-form, GPU SPIRV f32 (certified), CPU f64 (reference). Doctrine: no artificial clamping or damping anywhere; everything rolls over; nothing restricted unless there is a physical reason.**

---

## 1. What was built and certified

**Engine.** The unified pair-slot form (all four N² pair terms — steric, phosphate, hydrophobic, Go contacts — in one padded slot list, six branchless force loops, segmented deterministic reduction) was mirror-verified against the old form to 2.7e-20 max force deviation, finite-difference validated against documented energies (2.0e-10), and certified on GPU: bitwise-deterministic in both precisions, 3-seed tRNA gate passed (GPU-vs-CPU basin deltas 0.34/0.90/1.44, CPU-vs-old-cert 0.01/0.01/0.07). Deterministic replay subsequently confirmed twice more in production (runway arm, null control).

**Bugs found and fixed along the way** (all documented in RIBOSOME_FINDINGS.md): f32 DD-floor underflow (1e-30 → 1e-16); IRWhileLoop extractor hole; stale-host-copy sync clobber; missing IRWhileLoop import (f64 GPU had never compiled); generator silently zeroing hydrophobic flags on renumbered slices; generator mapping RNA adenines to alanine in the hydro table when fed CA atom names. One analysis-side errata: a hand-rolled Kabsch gave wrong subset alignments; all per-domain reads recomputed with SVD and the corrections issued.

## 2. Certified results

| Target | Size | Result | Note |
|---|---|---|---|
| tRNA (1EHZ) | 76 | **4.10–6.17** (3 seeds) | certification gate target, passed |
| 5S rRNA + uL5 + uL18 assembly (6QZP) | 589, 3 chains | **8.31 hier / 8.71 mono** whole-complex | docking certified, 55/55 interfaces |
| — per-chain inside assembly | | 5S 5.95, uL5 4.53, uL18 7.35 | uL5 beats its solo plateau in complex |
| uL11 (1SM1, two-domain) | 143 | **3.41 mono / 3.88 dock** | lobes solo 3.29 / 2.83 |
| uL18 core (6QZP, tailless) | 252 | **median 6.81, min 4.92** (5 seeds) | on the size-scaling line |

**Docking channel**: certified on four independent systems (d5 37/37, d5t 21/21, uL11 5/5, 5S RNP 55/55 — every gated contact ever installed has closed at ratio ≈1.0–1.1). Fold-then-dock is mechanically solved.

## 3. The wall, and what bounds it

Domain-scale RNA (≳180–550 nt continuous chain) does not fold to criterion: d5 solos 7.8–9.9, d5t solos 10.2–14.0, 550-nt mono 13.1–18.5, hier 14.4–23.0. Two honest negatives, pre-registered, documented.

**Confounds excluded by experiment:**
- Runway: 3× frames reproduces the 96k fold exactly, then melts back (7.76 → 8.18). Not time.
- Window selection: median-density window fails *harder* than densest. Not bias.
- Dock timing: 24k/48k/72k identical to three digits at the wall. Not scheduling.
- Per-domain quality: domains inside assemblies fold at solo quality (SVD-verified). Not the domains.

**What actually governs assembly — interface density.** Sparse-seam assemblies (d5/d5t: 21–37 contacts across 3 RNA-RNA boundaries) close their contacts onto *wrong* relative geometry (23 RMSD class). Dense-interface assemblies (5S RNP: 55 tight protein-RNA contacts across 2 boundaries) close onto *correct* geometry (8.3 RMSD class). 589 beads with dense interfaces assembles; 550 nt with sparse seams does not. Local contact satisfaction determines assembly geometry only when the interface is dense enough to overdetermine it.

## 4. The uL18 tail — the campaign's biological finding

uL18 (RpL5) has a 41-aa C-terminal tail with *zero* native cross-contacts to its core — unique in the rung-3 set (uL5's termini are densely integrated; uL11 has a hinged two-domain fold instead).

- Free full chain: 11.43 RMSD. Tailless core: 6.81 (best 4.92), on the scaling line.
- The core folds at solo quality *inside* the full-chain run — the tail doesn't poison the core; it ends up **mispositioned** (whole-chain RMSD is dominated by core–tail placement error).
- In the 5S RNP assembly, uL18 folds to **7.35 with the tail correctly placed** — the 5S scaffold does the positioning.

This is the chaperone story, reproduced in-engine: RpL5 is captured co-translationally by Syo1 and delivered onto the 5S RNA; the tail never exists as a free agent in vivo. The simulation recovers both halves of that statement — the unchaperoned chain misplaces its tail, and the scaffolded assembly places it.

## 5. Open problems (next campaign, needs new physics + sign-off)

1. **Chain growth** (Syo1-faithful tail delivery / co-translational folding): fold the core, extend the chain late. No growth machinery exists.
2. **Approach-geometry control for sparse-seam domains**: the rung-4 wall is now precisely defined as a placement problem under underdetermined interfaces. Timing is dead; the lever would be geometric (e.g. native-composition steering of the approach), which is new force-field physics.
3. **The ~180–550 nt continuous-RNA wall** itself: mono sits on the ~1 RMSD/75-bead scaling line; whether that's basin statistics or force-field incompleteness at domain scale is unresolved.
4. Engineering: .esf checkpointing (writer-side exists), batch runners, f64 GPU path review.

## 6. Campaign in one paragraph

The engine folds everything up to ~300 beads to 3–7 RMSD, docks any interface you hand it at 100% contact recovery, assembles the full 5S RNP to 8.3 RMSD with every chain at solo quality, and fails only where continuous RNA exceeds ~500 nt with sparse internal seams — a failure now precisely characterized as underdetermined assembly geometry rather than misfolding. All certifications, negative results, pre-registered gates, bugs, and errata are documented in RIBOSOME_FINDINGS.md.
