# RAIL_MAP.md — what the staged dock-gate rail encodes (uL18, 293 aa)

2026-08-29. Question: does the dock-gate "rail" (staged cross-seam
contact activation in `ul18_stag5.ergo`) encode physical assembly order,
and does the structure *ratchet* through it — discrete rotation steps at
gate release — or drift smoothly?  Measured with read-only telemetry on
the certified staged program; no physics touched (proof below).

## The rail as actually shipped

The certified `ul18_stag5.ergo` gates 91 cross-seam native contacts via
per-contact frames in `CONTACT_INTER` (measured from the source, not the
docs):

| gate frame | contacts | seam(s) |
|---|---:|---|
| 24000 | 25 | D1(1–63)↔D2(64–126) |
| 48000 | 14 + 29 | D1↔D3(127–189), D2↔D3 |
| 72000 | 16 + 7 | D2↔D4(190–252), D3↔D4 |
| — | 0 | D5(253–293) has **zero** cross-seam contacts to gate |

Discrepancy, recorded honestly: `CODON_FINDINGS.md` describes the arm as
"T_k = 24000·k (24k/48k/72k/96k)" — the file contains no 96000 gate.
The 96k fourth gate exists only in that text.

## Instrument (new files; ul18_stag5.ergo untouched)

- `min/ribosome/mk_rail_variants.py` — patch generator (anchored inserts).
- `min/ribosome/ul18_stag5_rail.ergo` — staged arm + telemetry:
  per-10-frames per-gated-contact distances inside gate windows
  (T_k ± 4000) plus a control window (100000–108000); per-bead
  coordinates in the same windows; per-contact first-formation table
  (first frame D < NATIVE_CUTOFF = 2.6).
- `min/ribosome/ul18_stag5_rail_nogate.ergo` — same telemetry; the 91
  contacts live from frame 0 (CONTACT_INTER zeroed before the slot bake).
- `min/ribosome/rail_analysis.py` — timing + Kabsch/SVD rotation
  analysis (the certified SVD recipe; the hand-rolled alignment is
  retired per RIBOSOME_FINDINGS ERRATA).  Per-seam series land in
  `min/ribosome/rail_series/*.csv`.

**Determinism:** each arm run twice, byte-identical stdout both times
(staged 48,322,505 B; no-gate 47,893,541 B).  **Physics identity:**
every CSV frame row of the rail arm is byte-identical to the pristine
program built the same day (14,693/14,693) — telemetry is read-only.

## Q1 — gate vs formation timing: the structure waits for the gate

First-formation lag = first frame below cutoff minus gate frame
(staged arm, per contact):

| gate | n | never | lag min | p25 | median | p75 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| 24000 | 25 | 0 | −23370 | +100 | +110 | +420 | +15260 |
| 48000 | 43 | 0 | +30 | +40 | +50 | +420 | +23970 |
| 72000 | 23 | 2 | −71700 | −25010 | +120 | +3150 | +62570 |

Fraction-formed curves: flat and low before the gate (0.08 / 0.00 /
0.13–0.26), then a step at activation — t50 = 24120 / 48130 / 72510
(120–510 frames after the gate).  The 72k seam's pre-gate fraction
*decays* to 0.00 by 50k (the two domains diffuse apart while ungated)
and recovers to 0.61 within ~1000 frames of activation; 2 of its 23
contacts never form at all.

**Answer:** gate-limited, not physics-limited — at the seam level the
contacts form 50–500 frames after activation, one to two orders faster
than the 24000-frame gate spacing.  The exceptions are real: a handful
of contacts are geometrically closed long before their gate (min lags
−23370, −71700) — pre-closed geometry carrying no force until release.

## Q2 — rotation during docking: discrete ratchet steps at gate release

Relative inter-domain rotation (SVD/Kabsch frames per domain vs its own
pre-gate reference at T_k − 3000; seam relative rotation = R_up·R_downᵀ;
control floor from the no-gate 100–108k window: 0.69° mean, 1.23° max):

| seam | pre-gate mean | post-gate mean | max | step @ gate±500 | Kabsch resid U/D |
|---|---:|---:|---:|---:|---:|
| D1\|D2 @24k | 0.53° | 7.45° | 8.66° | +2.82° | 1.21 / 0.83 |
| D1\|D3 @48k | 0.33° | 62.9° | 71.4° | +33.8° | 2.10 / 2.90 |
| D2\|D3 @48k | 0.36° | 53.6° | 61.4° | +27.8° | 1.75 / 2.90 |
| D2\|D4 @72k | 0.78° | 12.9° | 17.4° | +5.57° | 1.85 / 2.24 |
| D3\|D4 @72k | 1.03° | 25.3° | 36.7° | +8.70° | 0.92 / 2.24 |

Step shape (rail_series CSVs): the D1|D2 event is 1.27° at the gate →
1.47° at +80 → 2.55° at +100 → 3.97° at +180 — a snap within ~100
frames.  The D3 event: 0.87° → 7.85° → 20.3° → 30.5° across the 300
frames after 48000, settling near 62–70°.  These are discrete,
gate-triggered reorientations, not smooth drift.

Confound check: Kabsch residuals (internal deformation absorbed by the
frame) are 0.8–2.9 model units on the large-rotation seams — real but an
order below the rotation; the rotation number is the event.

**The no-gate arm kills the ratchet.** With the same contacts live from
frame 0: every seam's rotation stays ≤ 4.0° max with steps ≤ 0.3° — no
events at all — and all 91 contacts form almost immediately (first-formed
frames ~40–780; two never form at 24k's seam).  The ratchet steps exist
*because* the rail held the domains apart while they accumulated
orientational offset; the step is the stored offset released at once.

## Q3 — what the rail encodes: order, not destination

Evidence stacked:

1. **Without the rail, physics docks immediately and smoothly** —
   contacts close within 40–2000 frames of the start, rotations stay
   ≤4°, no events (no-gate arm).  The native geometry alone is sufficient
   and early.
2. **With the rail, formation is gate-limited** (Q1) and docking happens
   as discrete rotation snaps at each release (Q2).
3. **The destination doesn't care** (CODON_FINDINGS phase-0, pre-existing):
   staged 11.77 ≈ dom5-simultaneous 11.88 ≈ mono 11.43 whole-chain RMSD;
   the tail is unplaced either way (D5 has no contacts to gate).

**Verdict:** the rail encodes a real *assembly order and pathway* —
when each seam closes and how much stored rotation each seam releases —
but it is **a convenience with respect to the final structure**: the same
end state is reached with all contacts simultaneous (dom5) or absent
(mono class).  The physical system does not ratchet on its own; the
ratchet events are rail-release artifacts.  Nothing here supports reading
biological assembly timing into the final fold.

**Magnitude vs the biological ratchet class (~10° intersubunit):** the
D1|D2 event (7.4° sustained, 8.7° max) is in that class; the D3 event
(62–71°) is not — it is 24000 frames of free diffusion discharged at
once.  If a biologically-scaled ratchet is wanted, the gates would have
to release before the offset accumulates — from Q1's formation numbers,
a few hundred frames of separation at most.

## Backend note (re-certification-relevant)

Today's backend (post `ba3783d` segred/dock-gate extraction fix and
`a905d80` NoContraction contraction policy) produces **zero** identical
frame rows vs the certified `ul18_stag5.csv` (recorded at `cb4635f`)
for the *pristine* program.  The rail arm is byte-identical to the
pristine program built today, so the rail measurements are consistent
with current reality; the certified CSV awaits the regeneration decision
that was already pending.

## Reproduce

```
python3 min/ribosome/mk_rail_variants.py
python -m core min/ribosome/ul18_stag5_rail.ergo --target spirv \
    --precision f32 -o /tmp/rail && /tmp/rail > rail_run.txt
python -m core min/ribosome/ul18_stag5_rail_nogate.ergo --target spirv \
    --precision f32 -o /tmp/railng && /tmp/railng > railng_run.txt
python3 min/ribosome/rail_analysis.py rail_run.txt
```
