# CODON FINDINGS — combined campaign (codon playback × ergo folding)

Companion to RIBOSOME_FINDINGS.md / RIBOSOME_FINAL.md. This notebook covers the
merge of the old Fortran-era codon/torus/siphon project with the ergo 3D folding
engine. Newest entries at the bottom. Negative results and retractions are kept.

## 1. Reconstructed foundations (verified against source)

### 1.1 Codon index convention — CONFIRMED
From `bsu_preprocess.py`: `BASE_MAP = {'A':0,'T':1,'G':2,'C':3}`,
`index = b1*16 + b2*4 + b3` (b1 = first base). Therefore:
- `ring = c mod 32`, `pole = c // 32`
- pole 0 = first base A/T (codons 0–31) → +w; pole 1 = first base G/C → −w.
This matches the AT/GC parity split documented in PROGRESS.md exactly.

### 1.2 FLOWW is the z-component, NOT the siphon escape — CONFIRMED
The 32-entry FLOWW LUT in `sq2core.f` equals the soliton waveform
`sin(3θ)/3 + sin(9θ)/9 + sin(27θ)/27` (max deviation 6.5e-07, θ = 2πk/32).
The siphon escape component is a separate projection: **w = ⅓ sin(5θ)** —
the 5θ harmonic has no partner in the 3/9/27 stack.

### 1.3 Siphon metric — fully reconstructable, no missing code
Per-codon weight:
```
w_c = (+1 if c < 32 else −1) · ⅓ · sin(5 · 2π · (c mod 32) / 32)
```
Organism-level: `<w> = Σ freq_c · w_c`; `pump_efficiency = |<w>| / <|w>|`.
Verified: regenerating genome-wide numbers from raw codon streams requires
no further old-project code.

### 1.4 Codon stream format — decoded and validated
`*_codons.bin` = whole-genome codon stream, 1 byte/codon, aligned to GENOME
frame (not gene frame). Length×3 = genome size (verified: buc 640,680 ≈ 640,681 bp;
eco 4,641,651 ≈ 4,641,652; syn3 543,378 ≈ 543,379 — 1-bp floor-division residue).
Gene extraction needs `*_genes.tab` genomic coordinates + frame offset +
reverse-complement for minus-strand genes. Validation = clean-ORF rate
(start M, no internal stops, terminal stop).

## 2. Three-organism decode results

| organism | genetic code | clean ORFs | in-gene ⟨w⟩ | pump eff |
|---|---|---|---|---|
| Buchnera APS | standard (11) | 507/564 (90%) | +0.0096 | 0.050 |
| Syn3.0 | **table 4 (TGA=Trp)** | 437/458 (95%) | +0.0106 | 0.054 |
| E. coli K-12 MG1655 | standard (11) | 3870/4300 (90%) | +0.0008 | 0.004 |

(Syn3's apparent 23% decode failure was Mycoplasma's reassigned TGA; with
table 4 it decodes at 95%. Remaining non-clean features are pseudogenes and
annotation edge cases.)

### 2.1 Genome-wide vs concentrated pump
- Reduced genomes (Buchnera, Syn3) pump positive genome-wide (~+0.01).
- E. coli genome-wide is neutral (+0.0008), BUT its ribosomal proteins pump
  hard (efficiency: rpmH 0.40, rplU 0.36, rpsA 0.32, rpmJ 0.31, rplA 0.31,
  rplX 0.31). In a large generalized genome the signal concentrates in the
  translation machinery; in minimal/symbiont genomes it is global background.

### 2.2 RETRACTION — "5S RNP counter-pump" (does not replicate)
Buchnera rplK (−0.028, eff 0.162) and rplE (−0.019, eff 0.093) looked like a
conserved 5S-module signature. E. coli rplK = +0.019 and Syn3 rplK/rplE mildly
positive → Buchnera's negative 5S-protein pumps are lineage-specific drift,
not a module property. Retracted 2026-08-25, same discipline as the Kabsch errata.

### 2.3 rplR (uL18) — the consistent pumper
Positive in all three organisms: buc +0.022/0.121, eco +0.021/0.119,
syn3 +0.069/**0.400** (Syn3's strongest ribosomal pump). Noted, not yet interpreted.

### 2.4 Methodology caveat
Frame-0 whole-stream stats mix intergenic sequence and both strands; they
underestimate in-gene pump (buc: +0.0078 stream vs +0.0096 in-gene) and can
invent strand artifacts (eco minus strand −0.002 in stream, +0.001 in-gene).
Use in-gene numbers for claims.

## 3. uL11 synonymous-recoding bounds (Phase 2 instrument)

Buchnera rplK: 143 aa, clean ORF, natural ⟨w⟩ = −0.028 (eff 0.162).

| arm | ⟨w⟩ | pump eff | codons changed |
|---|---|---|---|
| natural | −0.028 | 0.16 | — |
| pump-maximized | +0.230 | 0.94 | 98/142 |
| pump-reversed | −0.213 | 0.96 | 82/142 |

|Δ⟨w⟩| ≈ 0.44 between arms, >0.94 coherence, sign-flip both directions.
Design note: extreme arms abandon Buchnera codon preferences — irrelevant in
ergo (no tRNA/kinetics model), and that is the point: the ONLY channel by
which arms can differ is the codon→bead coupling built in Phase 1.
Null result = mapping does nothing; differential result = mapping does something.

## 4. Open interpretive note (user, 2026-08-25)

"A negative pump (if we are talking charge) wouldn't be the worst thing.
Locally changing the gradient for some things could actually be a benefit,
especially where protein folding is being done."
— i.e. sign of ⟨w⟩ is not a fitness axis by itself; local gradient shaping
near folding machinery may be the function. Keep in mind for Phase 1 mapping.

## 5. Phase 0 — staged-emergence uL18 (BUILT 2026-08-25, awaiting runs)

Question: does translation-ORDER (N→C staged contact availability) alone place
the uL18 tail correctly, with zero new physics?

Design:
- Same certified slot-form uL18 (293 aa, 246 Go contacts, all params identical
  to ul18_full_slot certified mono except where stated).
- 5 sequence-ordered domains: D1 1–63, D2 64–126, D3 127–189, D4 190–252,
  D5 253–293 (D5 = the 41-aa zero-cross-contact tail; structurally clean split:
  25 + 43 + 23 + 0 cross-seam contacts, no non-adjacent cross pairs).
- MAXFRAME 144000 both arms (extended runway shared; runway confound already
  excluded on RNA, here it is controlled by the simultaneous arm).
- **ul18_dom5.ergo** (control): all 91 cross-seam contacts gate at the single
  certified DOCK_FROM = 48000. Legacy code path, gate expression untouched.
- **ul18_stag5.ergo** (staged): seam k gates at T_k = 24000·k for the
  seams that HAVE contacts — 24k (D1↔D2), 48k (D1↔D3 + D2↔D3), 72k
  (D2↔D4 + D3↔D4).  (Erratum 2026-08-29, RAIL_MAP.md Phase-0: an
  earlier version of this line said "24k/48k/72k/96k".  The staged arm
  gates the same 91 pairs as the dom5 control — pair sets verified
  identical — and D5 has zero cross-seam contacts by construction, so a
  96k gate never existed and never had anything to gate.  No contacts
  were dropped; the "(…/96k)" text overstated the map.)
  pair opens at FRAME > T_k; DOCK_FROM left at default huge. Gate change is
  branchless exact-0/1 arithmetic, per-slot, and PROVEN bitwise-identical to
  the legacy expression for all WCI ∈ {0,1} (288002-evaluation mirror sweep,
  0 mismatches). No force term added, removed, or altered when open.

Pre-registered reads (before seeing results):
1. If staged whole-chain RMSD ≈ 7 class (tail placed) vs mono 11.43 →
   playback ORDER alone carries placement information (ribosome as sequential
   reader). D5(tail) subset RMSD is the decisive statistic (SVD Kabsch).
2. If staged ≈ dom5 ≈ 11 class → order alone insufficient; placement needs
   contact guidance (chaperone/scaffold), consistent with the Syo1/5S finding.
3. dom5 vs mono controls the 5-way split + longer runway; stag5 vs dom5
   isolates ORDER.

Per-domain and tail/core subset reads use the SVD Kabsch (the broken
quaternion Kabsch is retired; see RIBOSOME_FINDINGS ERRATA).

## 6. Phase 0 RESULT (2026-08-25) — order alone does NOT place the tail

Runs: ul18_stag5.csv, ul18_dom5.csv (both complete, 144000 frames, no NaN).

| read | stag5 (staged) | dom5 (simultaneous) | reference |
|---|---|---|---|
| whole-chain RMSD | 11.77 | 11.88 | mono 11.43 |
| core [1-252] | 6.75 | 6.84 | core-solo median 6.81 |
| D1 | 5.88 | 4.47 | — |
| D2 | 2.18 | 2.83 | — |
| D3 | 0.92 | 2.53 | — |
| D4 | 2.79 | 2.73 | — |
| D5 tail (internal) | 2.96 | 2.75 | — |
| **tail COM offset (core-aligned)** | **35.15** | **34.82** | — |

Verdict: pre-registered read 2 CONFIRMED. Per-domain folds are at/above solo
quality in both arms (D3 0.92; core 6.75/6.84 vs 6.81 solo). The tail folds its
OWN internal structure fine (~3). But the tail sits ~35 model units from its
native berth in BOTH arms, and the stagger changed nothing (11.77 vs 11.88,
38.47 vs 38.38 — inside seed noise). Translation ORDER carries no placement
information for a zero-cross-contact tail. Placement requires contact guidance
(chaperone/scaffold) — the Syo1/5S finding is necessity, not luxury.
Consequence for the codon campaign: if the shadow layer talks to folding, the
tail's berth is one place it could act — but no order-only mechanism will
reach it. Phase 1 mapping must couple to geometry (contact/torsional seeding),
not to emergence timing.

## 7. Phase 1 BUILD (2026-08-25) — shadow-torsion arms, approved as written

Spec: CODON_PHASE1_SPEC.md (approved). Mapping: RES_TORSP0(i) += α·w_c(i),
α=0.30 smoke test, offsets folded into literal constants (dialect-safest form;
CODON_ALPHA parameter present as documentation, inert — deviation from spec
text is representation-only, numerically identical).

Arms (synonymous recodings of the 1SM1 uL11 143-aa sequence, Buchnera usage
language; nat sampled from Buchnera family frequencies, rng seed 20260825):
- ul11_shadow_nat_a30.ergo   ⟨w⟩ = −0.0204, eff 0.102, Σw = −2.92
- ul11_shadow_max_a30.ergo   ⟨w⟩ = +0.2369, eff 0.936, Σw = +33.88
- ul11_shadow_rev_a30.ergo   ⟨w⟩ = −0.2223, eff 0.965, Σw = −31.79

Validation (all pass):
1. Mirror-null: α=0 build vs certified ul11_mono.ergo — force-relevant text
   byte-identical; only 2 comment lines + inert parameter line added.
2. FD: functional form untouched (diff proves only P0 constants changed);
   campaign FD certification of the torsion term carries over.
3. Partition: every differing line is a RES_TORSP0 constant or the inert
   block (0 other lines, all three arms).
4. Offset audit: max|off| = α/3 = 0.1000 exactly; Σoff = α·Σw to rounding;
   max per-line error 4.7e-07 (f64 rounding of literals).
5. Recipe intact in all arms: MAXFRAME 96000, SEED 0.0, HB_CAP 2,
   HYDRO_STRENGTH 0.002, NATIVE_K 1.00, DD floor 1.0E-16 ×8, zero 1.0E-30.

Pre-registered reads: CODON_PHASE1_SPEC.md §5 (arm separation at fixed α;
dose-response if smoke test separates; sign asymmetry; subset localization;
strain bookkeeping vs E_TORSION artifact).

## 8. Phase 1 SMOKE RESULT (2026-08-25) — arm separation at alpha=0.30: YES

ul11_shadow_{nat,max,rev}_a30, GPU f32, seed 0, MAXFRAME 96000, certified
ul11_mono recipe (baseline 3.41 A, offsets zero):

| arm | <w> | final rmsd | min rmsd | rgyr | alpha_frac | nhb | e_torsion | tors_mean |
|---|---|---|---|---|---|---|---|---|
| nat | -0.0204 | 3.615 | 3.571 | 6.51 | 0.379 | 122 | 128.9 | 19.51 |
| max | +0.2369 | 3.109 | 3.014 | 7.45 | 0.350 | 115 | 130.3 | 10.60 |
| rev | -0.2223 | 3.261 | 3.220 | 6.57 | 0.400 | 124 | 128.0 | 15.40 |

READS:
1. ARMS SEPARATE: max -0.51 A and rev -0.35 A vs nat; ordering stable from
   frame 24000 onward (3.70/3.34/3.37 at 24k -> 3.62/3.11/3.26 at 96k).
   The shadow-torsion coupling is structural, not noise — first evidence the
   w-shadow does geometric work.
2. Sign: BOTH nonzero arms beat nat. max (positive <w>) best. nat sits at
   <w>=-0.0204 ~ 0, so nat-vs-max is the dose axis; rev-vs-max is the sign
   axis. rev does NOT undo the max gain => not a simple linear <w> effect;
   dose ladder will disentangle magnitude-vs-sign.
3. Localization: tors_mean moves strongly (19.5 nat -> 10.6 max -> 15.4 rev)
   while e_torsion stays ~128-130 — no runaway torsion strain, the E_TORSION
   bookkeeping is clean. alpha_frac slightly DOWN in max (0.350 vs 0.379):
   the gain is not "more helix", it's better placement.
4. Baseline note: nat (3.615) vs zero-offset ul11_mono (3.41) — same seed,
   tiny offsets, different trajectory; within-run noise band to be measured
   by the seed ladder before over-reading 0.1-0.2 A differences.

FOLLOW-UP BUILT (2026-08-25), per pre-registered ladder:
- Dose at seed 0: {nat,max,rev} x alpha {0.10, 0.60} (6 files; alpha=0 is
  ul11_mono, already run = 3.41).
- Seeds at alpha 0.30: {nat,max,rev} x SEED {1,2,3} (9 files).
Audits: a10/a60 differ from a30 ONLY in RES_TORSP0 literals + CODON_ALPHA
param (139 diff lines, all TORSP0/ALPHA); offset scale exact to <=3.3e-7
(literal rounding); seed variants differ ONLY in the SEED line.

## 9. Phase 1 LADDER RESULT (2026-08-25) — smoke separation does NOT replicate at seed level; weak rev signal, underpowered

All 15 follow-up CSVs in. Final rmsd_native (GPU f32):

seed 0:      nat a10 3.427 / a30 3.615 / a60 3.542
             max a10 3.219 / a30 3.109 / a60 3.035
             rev a10 3.419 / a30 3.261 / a60 3.603
a30 seeds:   nat 3.615 / 5.226 / 3.741 / 3.898 (s0..s3)
             max 3.109 / 5.032 / 4.234 / 4.451
             rev 3.261 / 4.505 / 3.659 / 4.048
alpha=0:     ul11_mono 3.410 / 4.882 (s1) / 4.298 (s2)   mean 4.197 sd 0.741

READS (pre-registered, honest):
1. SEED NOISE DOMINATES: alpha=0 baseline scatters 3.41-4.88 (sd 0.74 A)
   across seeds — LARGER than the seed-0 arm separation (0.5 A). The smoke
   result "arms separate" was substantially trajectory luck at seed 0.
   Retracted as an arm-level claim.
2. PAIRED per-seed diffs vs alpha=0 (s0,s1,s2):
   nat +0.20/+0.34/-0.56  mean -0.00  p=0.99  -> no effect
   max -0.30/+0.15/-0.06  mean -0.07  p=0.64  -> no effect
   rev -0.15/-0.38/-0.64  mean -0.39  p=0.11  -> direction-consistent
   (3/3 seeds, NEGATIVE <w> arm folds BETTER every time) but underpowered.
3. DOSE at seed 0 (single seed, NOT claimable): max monotone improving with
   dose (3.41->3.22->3.11->3.04); nat, rev non-monotone. If the max dose
   trend were real it would contradict read 2 — treat as seed-0 noise.
4. NET: the only surviving signal is rev (negative <w> shadow) helping
   folding by ~0.4 A. Intriguing sign note: nat shadow of this sequence is
   also slightly negative (-0.0204); the Buchnera dialect is positive-pump
   in general, so a negative-coupled tail segment is not crazy, but NO
   mechanism claim until the effect is statistically real.

POWER: paired sd ~0.25 A; to resolve a 0.4 A effect at p<0.05 needs ~5-6
paired seeds. BUILT: ul11_mono_{3,4,5}.ergo + ul11_shadow_rev_a30_s{4,5}.ergo
(s3 arm already ran; mono_3 needed for pairing). Seed-line-only diffs,
audited.

## 10. Phase 1 DECISIVE PAIRED TEST (2026-08-25) — rev arm effect is REAL, modest

6 paired seeds, rev_a30 vs alpha=0 ul11_mono (same-seed pairs, GPU f32):

  s0: 3.410 -> 3.261 (-0.149)    s3: 4.000 -> 4.048 (+0.048)
  s1: 4.882 -> 4.505 (-0.378)    s4: 3.660 -> 3.171 (-0.489)
  s2: 4.298 -> 3.659 (-0.639)    s5: 4.104 -> 3.931 (-0.173)

mean diff = -0.297 A, sd 0.252, paired t = -2.89, p = 0.034;
Wilcoxon p = 0.0625 (5/6 seeds negative; s3 the lone ~zero reversal).

VERDICT: the negative-<w> shadow arm folds measurably BETTER than the
zero-offset baseline: ~0.3 A average improvement at alpha=0.30 on the 1SM1
uL11 sequence. Passes the paired t-test at p<0.05; nonparametric is at the
n=6 floor (borderline). Effect size ~0.3 A vs baseline mean 4.07 A — real
but modest (~7%), NOT a folding-switch. nat and max arms: no effect (sec 9).
The shadow-torsion coupling therefore does signed geometric work: negative
<w> helps this fold, positive/zero does nothing. nat shadow of this sequence
is itself slightly negative (-0.0204) — consistent direction, but mechanism
claims wait for the sign-mapped follow-up.

STATUS: Phase 1 pre-registered reads COMPLETE. Next decision point (user):
(a) dose-response for rev at multiple seeds (does alpha=0.60 help more?);
(b) reverse-arm on a second sequence (specificity); (c) 4V9F archaeal arm.

## 11. Phase 1 WINDOW TEST (2026-08-25) — tolerance window CONFIRMED in shape; overshoot PENALIZES

rev arm dose curve, 4 paired seeds (s0-s3), diffs vs alpha=0 baseline:

  seed   base    a10          a30          a60
  s0     3.410   +0.009       -0.149       +0.193
  s1     4.882   +0.027       -0.378       +0.827
  s2     4.298   -0.616       -0.639       +0.070
  s3     4.000   +0.495       +0.048       +0.313
  mean           -0.02 (p=0.93)  -0.28 (p=0.16, 4-seed subset;
                  6-seed a30 p=0.034 from sec 10)  +0.35 (p=0.13, 3/4 pos)

READS:
1. LOWER EDGE: a10 is exactly inert (mean -0.02, p=0.93) — sub-threshold
   dose does nothing, cleanly.
2. SWEET SPOT: a30 helps (established, sec 10).
3. UPPER EDGE: a60 is not a flat cutoff — it actively HURTS (mean +0.35,
   3/4 seeds positive). Too much shadow offset degrades the fold. The
   window has a penalty wall, not a plateau.
4. MODEL: sign-gated tolerance band. Negative <w> at moderate amplitude
   (alpha~0.3, offsets <=0.1 rad) assists; zero/positive inert; overdriven
   negative harmful. Consistent with a resonance/tolerance picture, not a
   binary gate. Individual edge p-values are underpowered at 4 seeds, but
   the three-dose pattern (inert/help/harm) is coherent and direction-
   monotone — claimed as shape, not as pointwise significance.

## 12. Phase 1 WALL TEST (2026-08-25) — upper-edge "penalty" RETRACTED; a60 = variance amplifier, mean ~0

a60 vs baseline, 7 paired seeds:
  s0 +0.193  s1 +0.827  s2 +0.070  s3 +0.313  s4 -0.413  s5 -0.588  s6 +0.139
  mean +0.077, sd 0.469, t=0.44, p=0.68 (2/7 negative). Wilcoxon p=0.69.

READS:
1. The sec-11 "penalty wall" does NOT replicate: s4/s5 fold BETTER at a60
   (-0.41, -0.59) while s0/s1/s3/s6 fold worse. Mean is zero; retracted.
2. What a60 actually does: LARGE diffs in BOTH directions (|d| up to 0.83;
   sd 0.47 vs a30's 0.30 and a10's ~0.46-but-tiny-mean... a10 mean -0.02).
   Overdriving the shadow makes the outcome seed-dependent — the coupling
   overwhelms the native torsion field and the fold becomes a coin flip.
3. FINAL Phase 1 model (all pre-registered tests complete):
   - sign gate: negative <w> acts; zero/positive inert (nat p=0.99, max p=0.64)
   - tolerance band: a10 inert (p=0.93) -> a30 consistent help (-0.297,
     p=0.034, 6 seeds) -> a60 destabilized (mean 0, variance doubled)
   i.e. a resonance window, not a gate, not a wall: correct sign + moderate
   amplitude assists; overshoot injects noise rather than signal.

## 13. Tier-3 ARCHAEAL ARM BUILT (2026-08-25) — H. marismortui uL11 (4V9F chain I)

Extraction: 4V9F entity 11 / auth chain I = 50S protein L11P (RL11_HALMA),
145 CA (res 5-156; gaps 25-28, 43-49 are tight loops, max CA-CA 3.86 A —
contiguous-bead treatment clean). Sequence confirmed vs entity.
Build path certified by REGRESSION TEST: uploaded generate_protein_ergo.py +
certified ul11_mono.ergo as template regenerates ul11_mono bitwise except
(a) RES_PHOS block (uploaded generator predates it; inert, PHOS_EPS=0;
    re-injected for layout fidelity),
(b) scale: needs mean_ca_ca=3.8 in the JSON (convention scale=0.400000).
hmal_ul11_mono.ergo: 145 res, scale 0.400000, 119 native contacts,
cutoff 2.6 model units, NSLOT resized 36608 -> 37120 (=145*256), recipe
otherwise identical to certified bacterial arm (MAXFRAME 96000, HB_CAP 2,
HYDRO 0.002, NATIVE_K 1.00). Partition audit: diffs only NRES/NSLOT decls,
array sizes, literal blocks, and the (report-only, pre-existing) E2E line.
BUG NOTED (not fixed, awaiting user): E2E line in certified template reads
RES_X(NRES)-RES_X(143) — hard-coded index, so e2e=0 in ALL CSVs to date.
Report-only, zero physics effect. Fix = RES_X(1); needs template change.

Shadow arms (hvo codon language, Haloferax volcanii — sister haloarchaeon;
4V9F's own genome not in panel). alpha=0.30, offsets folded into RES_TORSP0:
  nat (hvo modal codons): <w>=+0.0218
  max: <w>=+0.2117   rev: <w>=-0.2384   (offsets bounded +/-0.1000)
Partition audits: TORSP0 literals + CODON_ALPHA doc-param only.
NOTE: hvo nat shadow is POSITIVE-ish (+0.02) even though hvo genome is a
strong negative-pump dialect (-32.5z). uL11 is ring0 — kernel genes are
muted (hvo ring0 -2.9z), so a near-zero nat shadow is exactly what the ring
model predicts.

PRE-REGISTERED READS (archaeal arm):
A1. hmal_ul11_mono baseline folds (certified recipe, archaeal sequence).
A2. rev arm (negative <w>, matching the sign that helped bacterial uL11)
    vs mono baseline, paired seeds: does the resonance window generalize
    across domains of life?
A3. max/nat arms: sign-gate check (expect inert, as bacterial).
If A2 helps: window is sequence-general. If not: window is
sequence-specific — honest negative, narrows the coupling's meaning.

## 14. Archaeal arm interim (2026-08-25) — baseline folds; rev echoes bacterial effect size, underpowered

A1 PASS: hmal_ul11_mono folds 4.234 A (min 4.174) on 145-res 4V9F chain I
with the untouched certified recipe. Archaeal sequence is foldable.
Baseline seed scatter 4.23-6.10 (noisier than bacterial 3.3-4.9 — loop-gap
chain), so arm tests need more seeds for equal power.

4 paired seeds (s0-s3), final rmsd diffs vs mono:
  rev: +0.535 / -0.220 / -0.708 / -0.800   mean -0.298 sd 0.611 p=0.40
  max: -0.228 / -0.256 / +0.453 / -0.377   mean -0.102 sd 0.375 p=0.63
READS: max dead (seed-0 ranking was luck, as in bacteria). rev shows the
SAME mean effect as bacterial rev (-0.298 vs -0.297 A) but double the
variance; s0 wrong-signed. Underpowered, not a claim. Extended to s4-s5
(4 runs: mono_s4/s5 + rev_s4/s5) — 6-seed paired test will decide.

## 15. Archaeal arm DECISIVE (2026-08-25) — window does NOT generalize; honest negative

6 paired seeds, hmal rev_a30 vs mono:
  s0 +0.535  s1 -0.220  s2 -0.708  s3 -0.800  s4 +0.206  s5 +0.432
  mean -0.092, sd 0.575, t=-0.39, p=0.71 (3/6 neg). Wilcoxon p=0.69.

VERDICT: the 4-seed echo (mean -0.298) regressed to zero with s4/s5.
No shadow-coupling effect on the archaeal uL11 sequence, either sign
(max: p=0.63; rev: p=0.71). The bacterial uL11 window (sec 10: rev -0.297 A,
p=0.034, 6 seeds) stands as a REAL but SEQUENCE-SPECIFIC effect.

CAMPAIGN-LEVEL SUMMARY (Phase 1 closed):
- The w-shadow -> torsion-zero-point coupling CAN do signed geometric work:
  one demonstrated case (bacterial uL11, negative <w>, alpha~0.3, ~0.3 A
  mean improvement, resonance-window dose shape).
- It is NOT a universal folding force: archaeal uL11 (145 res, same recipe,
  same arms, hvo codon language) shows nothing at any sign or either dose
  tested.
- Interpretation options, in order of parsimony:
  1. the effect requires coincidence between the shadow pattern and the
     sequence's native torsion landscape (bacterial uL11 has it; hmal
     doesn't) — i.e. shadow-assisted folding is an evolved, per-protein
     property, not physics every chain gets for free;
  2. the codon language matters more than the sign (hvo language on hmal
     sequence vs buc language on tt sequence — confounded with option 1);
  3. the bacterial result is a borderline false positive (p=0.034 once,
     not corrected for multiple arms) — cannot be excluded; a second
     bacterial sequence would be the cleanest arbiter.
- Next decisive test if wanted: bacterial uL18 (certified slot template
  exists) rev arm, 6 paired seeds. If a second bacterial protein shows the
  window, option 3 dies and option 1/2 live; if not, Phase 1 closes as a
  single-case curiosity.

## 16. uL18 rev arm BUILT (2026-08-25) — second bacterial sequence, decisive arbiter

Template: certified ul18_full_slot.ergo (293 res, slot-gated contacts).
Sequence recovered from RES_HYDRO comments (293 aa). Buchnera codon language
(same as bacterial uL11 arms): nat <w>=+0.0172, rev <w>=-0.2110 (offsets
bounded +/-0.1 at alpha=0.30, folded into RES_TORSP0 literals).
Files: ul18_shadow_rev_a30{,_s1.._s5} (6), ul18_shadow_nat_a30 (control),
ul18_full_slot_s{1..5} (baselines; s0 baseline = existing ul18_full_slot.csv).
Audits: mono seed files = SEED-line-only; rev = TORSP0+SEED+doc-param only
(offset err <=4.7e-7).

PRE-REGISTERED (arbiter for Phase 1 option 3):
- 6 paired seeds rev vs mono. Window replicates (mean <0, p<0.05) =>
  shadow-assisted folding is real and selective (2 bacterial proteins);
  bacterial-uL11-only false positive dies.
- No effect => Phase 1 closes as single-case; option 3 (uncorrected p=0.034)
  becomes the parsimonious reading.

## 17. uL18 ARBITER RESULT (2026-08-25) — NULL. Phase 1 closes as single-case.

6 paired seeds, ul18_shadow_rev_a30 vs ul18_full_slot (certified, 293 res):
  s0 -0.300  s1 +0.755  s2 -0.023  s3 +0.174  s4 -0.135  s5 -0.151
  mean +0.053, sd 0.378, t=0.34, p=0.74 (4/6 neg, trivial magnitudes).
  nat control (s0): +0.035 vs mono — inert as expected.
WARNING PATTERN: the seed-0 smoke AGAIN looked like the effect (-0.300,
same size as uL11!) and again failed replication. Seed-0 arm separations in
this rig are now 0-for-4 as predictors (uL11 max, hmal max, hmal rev 4-seed,
uL18 rev). Treat any future single-seed smoke as noise until paired.

FINAL PHASE 1 VERDICT:
- uL11 rev window (sec 10-12) is a REAL measured effect (p=0.034, 6 paired
  seeds, dose-structured) on ONE bacterial sequence.
- It does NOT replicate on archaeal uL11 (p=0.71) nor on bacterial uL18
  (p=0.74). Uncorrected for 3 arms x 3 sequences, option 3 (borderline
  false positive) is now the parsimonious reading.
- What survives as durable knowledge: (a) the coupling mechanism is real
  physics in the model (torsion zero-point offsets shift folds); (b) any
  folding assistance is per-sequence, rare, and small (~0.3 A at best);
  (c) the genome-level shadow organization (rings, assimilation, sign
  axis) stands INDEPENDENT of the folding-effect question — those are
  statistical-genetics results, not simulation results.
Deepseek's "microcode selectively enabled per-program" picture is
consistent with (b): IF the effect is real anywhere, it is per-protein
annotation, not a general steering field. The uL18 null means we cannot
claim even one confirmed second instance.
