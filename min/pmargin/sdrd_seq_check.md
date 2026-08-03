# Sequential co-translational SdrD assembly (white bath)

Program: `min/pmargin/sdrd_seq_full.ergo` (from `gen_sdrd_seq.py`,
base `sdrd_white_full.ergo`), 8 blocks × 556 residues, 8 m 33 s.
Biological premise (the user's): SdrD is secreted unfolded and folds
extracellularly, C-terminally tethered — N-to-C sequential, not
all-at-once refolding. The all-at-once protocol tests a process
biology doesn't use.

## Protocol (the amyloid template-addition pattern in one run)

Domain-staged activation: stage 1 (frames 1–12000) A2 folds alone;
stage 2 (12001–24000) A3 denatured added, A2 = damped template
(VDAMP 0.5); stage 3 (+B1 at 24001); stage 4 (+B2 at 36001). Inactive
domains are frozen in their coil state (VDAMP 0, no kicks). Thermal
schedule unchanged (heat cycles frames 1–1200, floor 0.001, quench
38400 — documented: stage 1 gets the hot cycles, later stages fold at
the floor, matching the domain-sweep regime; each domain also gets
only 12000 frames vs the sweep's 48000 — confound, addressed below).

**Curated boundaries** (UniProt/Pfam curation per the task; the
contact-minimum detection from `sdrd_check.md` was within 2–7
residues): A2 = construct 1–152 (res 243–394), A3 = 153–325 (res
395–568, A region ends 568), B1 = 326–437 (res 569–680, CNA-B1
curated), B2 = 438–555 (res 681–791, CNA-B2 curated; res 792–798 =
tail, folds with B2, unscored). Per-domain RMSD ranges updated
accordingly (A3 173, B1 112, B2 118).

## Per-stage tables (8 blocks; best / median per domain per stage)

| stage end | A2 | A3 | B1 | B2 | full-chain |
|---|---|---|---|---|---|
| 12000 (+A2) | 5.94 / 10.81 | — | — | — | — |
| 24000 (+A3) | 5.95 / 11.65 | 5.67 / 8.34 | — | — | — |
| 36000 (+B1) | 5.90 / 11.53 | 5.58 / 7.17 | 4.00 / 5.47 | — | — |
| 48000 (+B2) | 5.58 / 11.49 | 5.52 / 7.07 | 3.91 / 5.45 | 4.56 / 5.76 | 16.47 / 21.20 |

References: white-bath domain sweeps (48000 frames each): A2 best
3.38 / med 5.32; A3 2.38 / 5.32; B1 0.91 / 4.38; B2 1.82 / 4.85.
All-at-once white full construct: best 15.2 / med 20.5 / mean 21.0 /
max 36.2.

Same-time control (sweep at frame 12000, blocks 1/2/5): A2 = 6.21 /
7.00 / 11.14 — sequential stage-1 A2 = 6.83 / 16.41 / 12.86 for the
same blocks. **The tethered A2 folds SLOWER** (b2 16.41 vs 7.00,
b5 12.86 vs 11.14): dragging the frozen A3–B2 tail hinders the leading
domain — co-translational folding is harder for the N-terminal
domain, and it shows.

## Sequential vs simultaneous (final state)

| metric | sequential | all-at-once (white) |
|---|---|---|
| full-chain best / median / mean / max | 16.47 / 21.20 / 22.0 / **26.8** | 15.2 / 20.5 / 21.0 / **36.2** |
| worst per-domain value anywhere | A2 15.7 | A3 39.5 |
| merged-blob catastrophes | 0 | 0 (white bath already eliminated them) |
| A3 worst block | 11.2 | 39.5 |
| B1 worst block | 9.8 | 12.9 |
| best per-domain folds (A2/A3/B1/B2) | 5.58 / 5.52 / 3.91 / 4.56 | 4.57 / 4.84 / 4.84 / 2.83 in-construct; 3.38 / 2.38 / 0.91 / 1.82 in sweeps |

**The bad tail is tamed; the good tail is not improved.** Sequential
assembly compresses the failure side of the distribution: no domain
anywhere ends worse than 15.7 (vs 39.5 all-at-once), full-chain max
26.8 vs 36.2 — the staged template prevents runaway inter-domain
fusion by construction (the template is already structured and damped
when the next domain arrives). But best-case folds are all worse than
the isolated sweeps (tether + only 12000 frames per domain vs 48000 —
the confound is documented; a 4×-frame staging variant is the named
follow-up, est. ~35 min, out of this budget).

## Verdict

The user's biological insight is informative **in reverse**: the
all-at-once protocol was never the bottleneck. Sequential assembly
(i) does NOT improve any headline metric (full best 16.5 vs 15.2,
median 21.2 vs 20.5 — inside chaotic deviation), (ii) tames the
failure tail (no domain > 15.7 anywhere; max full 26.8 vs 36.2) — a
real structural benefit of staged tethering, and (iii) makes the
LEADING domain fold slower (A2 same-time control: 16.41 vs 7.00 on
the outlier block) because it drags a frozen tail. Merged-blob
catastrophes occur in neither protocol once the white bath is in use.
The remaining ceiling is the energy landscape, not the protocol:
co-translational assembly changes the trap distribution (fewer deep
traps, more tether drag) without lowering it. Follow-ups named:
192k-frame staging (48k per domain, removing the time confound), and
per-stage heat cycles (each domain gets its own anneal instead of the
floor — the current schedule gives only stage 1 the hot cycles).

Files: `gen_sdrd_seq.py`, `sdrd_seq_full.ergo` (+binary),
`sdrd_seq_full.out`, this report.
