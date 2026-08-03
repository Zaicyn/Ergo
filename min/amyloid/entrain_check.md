# Longer anneal + entrainment sweep on the off-register tax run

Base: `tax_0p5_off1.ergo` (TAX=0.5, off-by-one start — the run that
began correcting and stalled at ~25%). MAXFRAME 12000 → 50000, quench
9600 → 40000 (0.8×, standard recipe; documented: without moving the
quench, frames past 9600 carry zero noise and "longer anneal" would be
vacuous). Pulse: mode-1 standing wave across the packed 28-residue
vector, A=0.05, on Cα velocities (beads follow via tethers).
Register readout: sheet-2 COM y (correct ≈ 2.4; off-register start ≈ 4.8).

## Task 1 — longer anneal (no pulse)

Offset vs frame: 4.82 (start) → 4.69 (f6000) → **4.36 (f9000) → 4.35
(f12000, the original stall point) → 4.56 → 4.60 → 4.62 (f15000 on,
flat to f50000)**. Final bonds: 0.

**Anneal alone does NOT complete and does not even hold its best
progress:** the slide reaches ~25–30% (min 4.29 at f~10000), then
REVERSES to 4.62 and freezes permanently (still 4.62 at f50000 with
zero bonds). The ~25% stall reported from the 12000-frame window is
not a stable state; it is the turning point of a partial excursion.

## Task 2 — entrainment sweep (pulse A=0.05 on the off1/TAX=0.5 start)

| ω (rad/frame) | period (frames) | final COMy | NHB | EBOND | outcome |
|---|---|---|---|---|---|
| anneal (no pulse) | — | 4.62 | 0 | 0.000 | stall after rebound |
| 0.0005 | ~12600 | 3.04 | 10 | **−1.490** | violent rocking (COMy swings 0.6–5.9 with the pulse period); ends mid-cycle, most-bound state; endpoint phase-dependent |
| 0.002 (validated 1SNO rescue) | ~3140 | 5.22 | 0 | 0.000 | **FAILS** — anti-resonant: pumped swings 3.4–5.7, ends unbound and MORE separated than the start |
| 0.005 | ~1260 | **2.44** | 7 | −1.017 | **correction completes** (2.44 ≈ correct 2.4); bonds include diagonal pairs |
| 0.02 | ~314 | **2.52** | 9 | **−1.495** | completes (2.52); strongly bound end state |
| 7.83 ("schumann", documented below) | 0.80 (sub-Nyquist) | 4.63 | 0 | 0.000 | **indistinguishable from anneal** (curve matches to the digit until f40000; 0.01 late deviation) |

Control, pulse without tax (ω=0.005): final 2.58, **10 bonds**,
EBOND **−1.908** — the pulse alone also drives the slide to completion
(and binds harder, because without the tax every pair pays full depth).

**Schumann mapping + caveat (documented plainly):** the sim has no
physical time unit; the labeled point takes 7.83 literally as rad/frame.
At DT=0.01 the period is 0.80 frames < 1 frame — sub-Nyquist, so the
drive aliases into a deterministic noise hash that averages out. There
is no established physical coupling of Schumann resonances to molecular
dynamics; this is one labeled point in the sweep, and it behaves exactly
as that framing predicts: nothing distinct from the no-pulse anneal.

## Specificity verdict

- **The pulse is the slide motor; the tax is the bond selector.** The
  no-tax pulse control reaches essentially the same corrected position
  (2.58) with MORE bonds — so the sliding itself does not need the tax.
  What the tax contributes is pattern selectivity (diagonal-only
  bonding at TAX ≥ 0.5) at the cost of total adhesion (EBOND −1.02 vs
  −1.91). The two mechanisms are complementary, not synergistic:
  tax started the correction (earlier finding), pulse completes it,
  tax cleans the bond pattern.
- **Frequency specificity is a broad window with a hole, not a
  basin-matched peak.** ω = 0.005–0.02 (periods ~300–1300 frames)
  completes the correction; slower (0.0005) works but violently and
  phase-dependently; and the previously validated 0.002 — the frequency
  that rescued 1SNO (136 residues) — FAILS here, sitting in a hole
  between two working points. Interpretation (documented as such): the
  working frequency is system-specific (mass/length of the object being
  rocked), not a universal constant; a 28-residue two-sheet system
  wants faster rocking than a 136-residue protein. No sharp
  resonance peak is visible; the sweep shows an effective band with
  nonlinear anti-resonance at 0.002.
- **Nothing happens at the Schumann-labeled point** beyond the anneal.

## Bottom line

Anneal alone: partial excursion, rebound, permanent stall (not a
solution). Pulse at the right window: completes the register
correction the tax started (2.44–2.52 ≈ correct 2.4, sheets intact,
bonds formed). The correction mechanism decomposes cleanly: pulse =
motor, tax = selector. The "validated rescue frequency" is not
portable across system sizes — it must be re-swept per system, and
this sweep is the measured example.

Files: `gen_entrain.py`, `entrain_anneal.ergo`,
`entrain_w{0005,002,005,02}.ergo`, `entrain_schumann.ergo`,
`entrain_notax_w005.ergo` (+binaries and `.out` files), this report.
