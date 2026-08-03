# Parallel tempering (replica swap) on packed BBA5 — seed-rescue experiment

Programs: `min/pmargin/packed_temper.ergo` (SWAP_EVERY=500),
`min/pmargin/packed_temper_gate.ergo` (SWAP_EVERY=0, validation gate),
both emitted by the extended `min/pmargin/gen_packed_bba5.py` from the
v2 packed form. CPU only. Runs: `temper_gate.out`, `temper_run1.out`,
`temper_run2.out` (md5-identical — CPU deterministic).

## Design choices (documented)

- **Ladder:** per-block temperature multiplier `TMUL(B)`, geometric
  1.0 (block 1) → 2.0 (block 8), `TMUL(B) = 2**((B-1)/7)`.
- **Injection point:** TMUL multiplies the noise AMPLITUDE inside the
  existing schedule — both noise sites (`TEMP_X := THERMAL_CURRENT *
  TMUL(B) * PHASE_NOISE_SCALE` and the velocity kicks `THERMAL_CURRENT *
  TMUL(B) * SIN/COS(...)`). "Temperature" = noise-amplitude multiplier
  (the sim has no explicit thermostat; β ≡ 1/TMUL is the documented
  approximation). With TMUL = 1.0 the extra multiply is IEEE-exact, so
  the gate build is bitwise-identical to v2 — which is what makes the
  gate airtight.
- **Swap step:** every 500 frames, sequential adjacent-pair sweep
  B = 1..7 (documented: sequential, not even/odd). Metropolis
  `Δ = (β_i − β_{i+1})(E_i − E_{i+1})`, accept if `Δ > 0` or
  `hash < exp(Δ)`; hash =
  `MOD(ABS(SIN(frame*12.9898 + pair*78.233 + 3.7)*43758.5453), 1)` —
  same deterministic MOD family as the sim's noise. **Temperatures
  swap, states stay in blocks.**
- **Metropolis energy:** E = E_MORSE + E_ANGLE + E_TORSION + E_HYDRO +
  E_NATIVE (+ E_REGISTER only when FRAME > 1200, matching when that
  force is active). Computed per block at swap frames by
  `COMPUTE_ENERGY(OFFB, FRAME)`. Note: E_TORSION uses the FORCE's
  dihedral convention `ATAN2(B2MAG·(B1·N2), N1·N2)` — the source's
  diagnostic subroutine uses a different atan2 form; the force
  convention is the physically consistent choice for Metropolis.
- Post-quench swaps (frame > 12000) are dynamically inert (noise = 0 ×
  TMUL) but harmless; kept for simplicity.

## Validation gate (PASSED)

Swaps-OFF build (`SWAP_EVERY = 0` → TMUL ≡ 1.0): output is
**byte-identical** to the validated v2 table (diff vs
`packed_bba5_v2.out` shows only the header and the seven SWAPSTAT lines,
which report 0 tries). Dynamics untouched. Swaps-ON build is also
CPU-deterministic (two runs md5-identical).

## Swap acceptance

96 swap steps × 7 pairs; acceptance per pair: 93.8% / 86.5% / 96.9% /
100% / 95.8% / 97.9% / 97.9%. High by construction: ladder rungs are
close (ratio 2^(1/7) = 1.104 per rung) and all blocks fold the same
protein, so energy differences are small against Δβ ≈ 0.09 — |Δ| is
almost always tiny. (642 accepted swaps logged as SWACC rows.)

## Rescue table (final RMSD, model units; Å ≈ ×2.58)

| block | seed | v2 baseline | temper | trap (>2 Å = 0.775)? | call |
|---|---|---|---|---|---|
| 1 | 0.0 | 1.6680 (4.30 Å) | 1.8832 (4.86 Å) | trapped → trapped | NOT rescued (same wrong-valley class) |
| 2 | 1.0 | 0.3150 | 0.2674 | — | fine |
| 3 | 2.0 | 0.4872 | 0.4966 | — | fine |
| 4 | 3.0 | 0.3889 | 0.3890 | — | fine (identical) |
| 5 | 4.0 | 0.2872 | 0.3228 | — | fine |
| 6 | 5.0 | 0.1854 | 0.3202 | — | fine (largest good-folder shift) |
| 7 | 6.0 | 1.0047 (2.59 Å) | 5.0297 (13.0 Å) | trapped → trapped | NOT rescued (much worse endpoint) |
| 8 | 7.0 | 1.0855 (2.80 Å) | **0.5678 (1.47 Å)** | trapped → **folded** | **RESCUED** |

**Trap count: 3/8 → 2/8.** Headline: tempering rescued seed 7.0 (2.80 Å
→ 1.47 Å, from trap to native-like) and did NOT rescue seeds 0.0/6.0.

**Good folders undisturbed:** blocks 2–6 were all sub-0.5 model units in
v2; in the temper run they are 0.267–0.497 — every one still sub-1.5 Å
("native-like" call). Largest shift: seed 5.0, 0.185 → 0.320 (still
0.83 Å). No good folder was harmed beyond chaotic deviation.

## What actually happened to the two non-rescues (trace diagnosis)

- **Block 8 (seed 7.0), the rescue:** spent the hot phase at the hot end
  (TMUL 2.0), explored at RMSD ~6.9 through frame ~3200, walked down the
  ladder via swaps, annealed 6.9 → 1.53 by quench (12000), then folded
  cleanly post-quench to 0.5678. Textbook tempering rescue.
- **Block 7 (seed 6.0), the blowup — read carefully before calling it
  tempering damage:** it was NOT melted-and-frozen. It annealed to 1.19
  by quench (better than its v2 trap at 1.00), then, with noise = 0,
  **drifted deterministically deeper into a compact non-native basin**
  (RMSD 1.19 → 5.42 by frame 25300, still moving at 48000). Its final
  Metropolis energy is −0.057 — comparable to the folded blocks
  (−0.036…−0.065), i.e. this force field has compact non-native minima
  that are energetically competitive with native (worth knowing for
  future Metropolis work: E alone does not separate native from traps;
  RMSD remains the oracle). Clinically the call is unchanged (trap →
  trap); the RMSD endpoint is much worse, but the block was already in
  the "wrong valley" class in v2 — this is trap EXCHANGE during
  chaotic post-quench settling, not a fresh failure created by the hot
  phase.
- Seed 0.0's block: 1.67 → 1.88, same deep-valley signature; tempering
  shifted the endpoint within the trap class.

## Verdict and follow-ups

Parallel tempering on the packed form WORKS mechanically (gate bitwise,
deterministic, high sensible acceptance, one genuine rescue, good
folders unharmed) and delivers a net trap reduction 3 → 2 with zero
cost in run time (2.5 s, same as v2 — swaps are 96 × 8 energy
evaluations). It is not a universal seed rescue: the deep seed-0.0
valley survives, and one trapped seed exchanged into a worse non-native
basin. Follow-ups, in order of expected value:
1. Restrict swaps to the pre-quench window (frame ≤ 12000) — post-quench
   swaps are inert anyway; purely cosmetic.
2. More heat cycles / longer hot phase: only frames < 1200 have
   substantial noise, so all effective tempering happens in ~2 swap
   steps (500, 1000). A hot phase of ~5000 frames would give the ladder
   ~10 effective swap steps.
3. Even/odd pair sweep to avoid same-block double swaps in one step.
4. Cold-side-biased ladder (1.0–1.5) if good-folder disturbance ever
   matters (here it did not).

Files: `min/pmargin/gen_packed_bba5.py` (temper emitter),
`packed_temper.ergo`, `packed_temper` (binary), `packed_temper_gate.ergo`,
`packed_temper_gate` (binary), `temper_gate.out`, `temper_run1.out`,
`temper_run2.out`, this report.
