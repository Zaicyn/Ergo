# CODON PHASE 1 SPEC — codon→bead torsional coupling (DRAFT v1, for sign-off)

Status: PROPOSED. No code built. No physics changed. Requires explicit approval
per doctrine (no force-field/parameter change without sign-off; mirror-first;
FD validation). Context: CODON_FINDINGS.md §1–6.

## 0. Design constraints inherited from Phase 0

Phase 0 (staged emergence, 2026-08-25) proved translation ORDER carries no
placement information for uL18's tail (staged 11.77 vs simultaneous 11.88,
tail COM offset ~35 in both). Therefore the codon shadow, if it talks to
folding at all, must couple to GEOMETRY at the bead level — not to emergence
timing, schedules, or gates.

## 1. Hypothesis under test

Synonymous codon choice biases local backbone conformational preference during
folding. Operational form: the siphon escape weight of the codon at position i,
w_c(i) = (±1)·⅓·sin(5·2π·ring/32) (CODON_FINDINGS §1.3), perturbs the
backbone torsion target of residue i.

## 2. The mapping (the entire change)

In INIT_CHAIN of the variant file, for each residue i:

```
RES_TORSP0(i) := RES_TORSP0_native(i) + CODON_ALPHA * w_c(i)
```

with one new scalar:

```
PARAMETER REAL :: CODON_ALPHA = 0.0    ! rad per unit w; 0 = certified baseline
```

That is all. RES_TORSP0 is an EXISTING per-residue array of the certified
torsion term (RES_TORSK stiffness 0.6, unchanged). No new force term, no new
code path, no new array class. The change is data (per-residue constants) plus
one parameter.

### Why this knob and not another
- **Existing, FD-certified term.** The torsion potential's functional form is
  untouched — only per-residue target constants shift. FD re-validation is a
  spot check, not a new certification.
- **Bitwise-null at α=0.** With CODON_ALPHA = 0.0 the file is the certified
  baseline byte-for-byte in every force-relevant line. The knob has a true
  OFF position — our standard mirror test is exact, not statistical.
- **Orthogonal to everything certified.** Does not touch NATIVE_R0,
  NATIVE_CONTACT/CONTACT_INTER, RES_HYDRO, hbond, frame terms, phos, gates,
  or the slot tables. The Go-native contact geometry is identical in all arms;
  only the torsional bias field differs.
- **Physically the right channel.** A torsion-target offset strains the native
  state slightly (native is no longer exactly zero-force) — which IS the
  hypothesis: the shadow writes a local conformational bias into the chain
  that the fold must resolve. Rejected alternatives: modulating RES_TORSK
  (stiffness — confounds with fold stability globally), RES_HYDRO (changes
  chemistry), initial-coil seeding only (washes out; and GPU/CPU RNG already
  decorrelates ICs).

## 3. Experiment arms (Phase 2 preview, built on the SAME 143-aa uL11 chain)

Codon strings are synonymous recodings of the 1SM1 uL11 amino-acid sequence
(NOT Buchnera's own rplK sequence — the folding target is the 1SM1 structure;
Buchnera supplies the codon-usage language). Arms:

- **nat** — codons sampled from Buchnera's per-family frequencies
  (⟨w⟩ ≈ 0 by construction; the "organism-style" shadow)
- **max** — per-residue synonymous choice maximizing w_c (⟨w⟩ ≈ +0.23 class;
  exact value recomputed on the 1SM1 sequence at build time)
- **rev** — minimizing w_c (⟨w⟩ ≈ −0.21 class)

All three arms: identical protein, identical certified recipe (hb-cap 2,
hydro 0.002, NATIVE_K 1.00, frame-k/frame-pos-k 0.2, no register, maxframe
96000, seed per replicate), identical contact lists — they differ ONLY in the
RES_TORSP0 offset pattern.

α dose ladder: 0.0 (mirror), 0.10, 0.30, 0.60 rad/unit-w. Max |w| = 1/3, so
max per-residue offset = α/3 ≤ 0.20 rad — perturbative against the 2π torsion
period and small vs the native P0 spread (reported at build time).
Seeds: 4 per (arm × α>0) for basin statistics; seed 0 first.

## 4. Validation ladder (before any physics run)

1. **Mirror-null:** α=0 file vs certified ul11 mono — bitwise diff of all
   force-relevant lines must be empty.
2. **FD spot check:** torsion force on the modified P0 array vs analytical
   (functional form unchanged; verifying no write went out of bounds, no
   index shifted).
3. **Partition audit:** count of modified RES_TORSP0 lines = 142 (stop codon
   ignored); no other INIT_CHAIN/INIT_NATIVE writes differ from baseline.
4. **Offset audit:** max |offset| = α/3 exactly; Σ offsets per arm ≈
   N·α·⟨w⟩_arm within rounding — proves the arm labels are what they claim.
5. **GPU/CPU seed caveat stands:** f32 and f64 runs are independent
   trajectories; comparisons are basin statistics within one target.

## 5. Pre-registered reads (written before results)

1. **Primary:** final-RMSD distributions per (arm, α) vs the certified uL11
   mono basin (3.41 class). Separation beyond seed noise between max and rev
   at a given α = the shadow couples to folding through torsion.
2. **Dose-response:** monotone separation with α = genuine coupling;
   flat = channel dead at tested strengths → honest negative, stop.
3. **Sign asymmetry:** max-helping vs rev-hurting (or vice versa) would say
   the pump direction matters, not just shadow magnitude — connects to the
   organism-level viability pattern (CODON_FINDINGS §2).
4. **Localization:** per-domain/subset SVD-Kabsch reads — does the effect
   concentrate anywhere (e.g. the RNA-binding surface)?
5. **Strain bookkeeping:** E_TORSION at native for each arm (how far the
   shadow pushed native off zero-force) — sanity that effects aren't a
   trivial "more strain = worse fold" artifact; max and rev carry the same
   |offset| distribution, so strain magnitude alone cannot separate them.

## 6. Explicitly NOT in this spec

No emergence scheduling (dead, Phase 0). No new force terms. No hydro/contact/
native-geometry changes. No MC. No organism mixing beyond codon-usage language.
No claims about in-vivo translation kinetics (ergo has none — arms differ only
through this mapping, which is what makes the instrument clean).

## 7. If approved, build order

1. Recode 1SM1 uL11 → three codon strings (script prints ⟨w⟩, eff, offset
   audits per arm).
2. Generate 3 arms × α=0.30 × seed 0 first (smoke test), then the dose ladder
   + seeds 1–3.
3. Mirror-null + FD + audits on every file before delivery.
4. You run; pre-registered reads above.
