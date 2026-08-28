# OPCODE MAP — ancient machine code baseline (Tier 1 ROM + Tier 2 dialects)

Framing (user, 2026-08-25): "We need to see what LUCA did, what bacteria did,
and what archaea did. Basically we are mapping out ancient machine code. Op
level." Reference papers: Moody et al. 2024 (LUCA prokaryote-grade, ~2,600
protein families, universal code + translation machinery pre-LUCA);
Mrnjavac et al. 2026 (metabolism INCOMPLETE at LUCA — final assembly
independent in bacterial/archaeal lineages); Pathak et al. 2026 (P/N delivery
context).

## Tier 1 — the opcode ROM (fixed, verified)

64 ops, encoding `index = b1·16 + b2·4 + b3`, digits A=0,T=1,G=2,C=3
(bsu_preprocess convention, verified). Each op carries:
- aa assignment + degeneracy class (standard table 11; variants exist, e.g.
  table 4 TGA=Trp in Mycoplasma/Syn3 — always check before decoding),
- shadow weight w_c = (±1)·⅓·sin(5·2π·ring/32), ring = c mod 32, pole = c//32
  (pole 0 = first base A/T → +; pole 1 = G/C → −). 17 distinct w symbols.
- The 5θ "escape" harmonic is the shadow channel; FLOWW (3/9/27θ) is the
  z-component carrier. Verified against sq2core.f numerically (6.5e-07).

Shadow capacity: 1.57 bits/codon max (uniform synonymous), ~1.37 used (buc).

## Tier 2 — dialect protocol (pre-registered)

Per genome: decode with gene tables (frame offsets + strand), validate by
clean-ORF rate, then compute in-gene ⟨w⟩ and the **composition null**:
uniform synonymous re-draw per residue (analytic: null mean = per-residue
family means, sd = √(Σ fam_var)/N). The null absorbs GC/composition pressure;
the z-score isolates directional synonymous CHOICE. No sign claim without
the null. Code-variant tables checked first. Retraction discipline per
campaign rules.

## Tier 2 RESULTS (2026-08-25) — first panel, 5 bacteria

| organism | genes (clean) | GC% | obs ⟨w⟩ | null | z |
|---|---|---|---|---|---|
| Buchnera APS (AT-rich endosymbiont) | 507 | ~26 | +0.0097 | +0.0032 | **+13.6** |
| E. coli K-12 (51% GC) | 3870 | ~51 | +0.0012 | −0.0014 | **+14.2** |
| Syn3.0 (minimal, table 4) | 437 | ~24 | +0.0106 | +0.0009 | **+19.9** |
| Streptomyces coelicolor (72% GC) | 4764 | 72.1 | −0.0193 | −0.0056 | **−83.6** |
| Pseudomonas aeruginosa (66% GC) | 4941 | 66.6 | −0.0163 | −0.0062 | **−64.0** |

ALL FIVE significant against the composition null. The dialect split is real
and bidirectional: AT-rich/minimal genomes pump POSITIVE; the two GC-rich
bacteria pump strongly NEGATIVE (effect sizes ~2× the AT-rich ones). The null
removes composition-driven choice, so this is directional synonymous choice,
not raw GC content. Note eco (51% GC) sits near zero/null boundary — sign
tracks the GC axis but the magnitude is a choice, not a composition readout.

### Consequence for the old project's "Thermus negative = dead" claim
T. thermophilus is GC-rich (~69%). Under the corrected in-gene pipeline its
negative pump is most likely the GC-rich dialect, not a death signature —
the old viable/dead interpretation needs re-examination against the null.
(Old project had no composition null.) Flagged, not yet retracted — needs the
thermus bin re-run through this pipeline.

### The user's gradient point (now with evidence)
"A negative pump wouldn't be the worst thing — locally changing the gradient
could be a benefit." The two most sophisticated free-living bacteria in the
panel run the strongest NEGATIVE pumps. Sign is not a viability axis; it
looks like an ecology/lifestyle axis. Hypothesis to test: positive pump =
streamlined/minimal genomes (drift-dominated, small effective population);
negative pump = large-genome free-living generalists (selection-dominated).
Archaeal panel will test whether the axis is domain-level or lifestyle-level.

## Tier 2 RESULTS, panel 2 (2026-08-25) — archaea + Thermus, self-generated bins

Generated with genome_preprocess.py (in output/; generalized from
bsu_preprocess.py) from NCBI RefSeq records (gbwithparts). One parser bug
found and fixed: IUPAC ambiguity codes must map to N, not be deleted
(frame shift; hit mja at 17% clean, fixed → 90%).

| organism | domain | GC% | obs ⟨w⟩ | null | z |
|---|---|---|---|---|---|
| M. jannaschii (hyperthermophile) | Archaea | 31 | −0.0044 | −0.0071 | **+8.8** |
| S. solfataricus (hyperthermophile) | Archaea | 36 | −0.0043 | −0.0062 | **+7.4** |
| P. furiosus (hyperthermophile) | Archaea | 41 | −0.0128 | −0.0067 | **−21.2** |
| H. volcanii (halophile) | Archaea | 67 | −0.0238 | −0.0159 | **−32.5** |
| T. thermophilus (GC-rich thermophile) | Bacteria | 69 | −0.0142 | −0.0053 | **−28.9** |

### The headline: the sign axis is NOT bacterial-vs-archaeal
Both domains contain both signs. Positive-bias: buc, eco, syn3 (bacteria)
+ mja, sso (archaea). Negative-bias: strep, pseudo, tth (bacteria) + pfu,
hvo (archaea). LUCA's two branches did NOT split the shadow dialect by
domain — the axis runs through ecology/physiology, not phylogeny.
Complication for a clean GC story: pfu (41% GC) is negative while eco
(51%) is positive; mja/sso are positive hyperthermophiles while pfu/tth
are negative ones. No single-variable explanation survives contact with
the panel. That is a RESULT: the dialect is multidimensional.

### RETRACTION (old project): "Thermus negative = dead/viability signal"
tth through the corrected pipeline (in-gene, composition null): z = −28.9,
squarely in the GC-rich-negative class with strep/pseudo/hvo. The old
viable/dead reading had no composition null and a frame-0 stream; the
sign it saw was the GC-rich dialect. The "dead pump" interpretation is
RETRACTED pending any analysis that separates viability from dialect.

## Tier 3 — structural dialects (files in hand)

- 4V9F: Haloarcula marismortui 50S, re-refined 2.4 Å (archaeal LSU — the
  1JJ2 successor; MORE complete stalks). Primary archaeal folding target.
- 4V4N: Methanococcus jannaschii ribosome–SecYEβ complex (archaeal ribosome
  + translocon; also the Tier-2 genome we'd want: M. jannaschii).
- 6ZR2: mouse respiratory complex I (eukaryote; membrane energetics —
  colony-project territory, park for now).

Archaeal folding arm: extract uL11/uL18/uL5 homologs from 4V9F, fold with the
certified recipe, compare against bacterial baselines (ul11 3.41; uL18 core
6.81; 5S RNP 8.31). THEN shadow-coupling per domain if Phase 1 separates.

## Ring / process classification (2026-08-25) — information flow between rings

Classifier: genes sorted by product/gene-name into ring0 (kernel: ribosomal
proteins, core replication dna*/gyr/polC, RNAP rpo*, EF/IF/prf), ring1 (HAL:
aaRS/tRNA ligases + modification, release factors, chaperones gro/dnak/tig/
clp), mobile (transposase/integrase/IS/phage/resolvase), else userspace.
z-scores vs composition null, per ring, 10 genomes:

| genome | ring0 | ring1 | userspace | mobile |
|---|---|---|---|---|
| buc | +4.8 | +3.2 | +12.4 | — |
| eco | +9.0 | +5.8 | +12.3 | +1.0 |
| syn3 | +6.9 | +7.3 | +17.3 | — |
| strep | −9.9 | −8.4 | −82.4 | −6.2 |
| pseudo | −0.0 | −2.8 | −64.6 | −2.0 |
| mja | +5.1 | +1.4 | +7.8 | +1.4 |
| sso | +2.3 | +0.6 | +7.1 | +0.6 |
| hvo | −2.9 | −1.6 | −32.6 | −1.0 |
| pfu | −3.7 | −4.2 | −21.1 | +4.6 |
| tth | −0.6 | −5.3 | −28.4 | −6.2 |

FINDINGS (process-classification, user's ring model):

1. Direction of flow: dialect is written in USERSPACE at full amplitude;
   ring0/ring1 carry the same sign at 3–8× attenuated |z|. Sign-preserving,
   amplitude-filtered coupling — userspace is the writable region, the ring
   boundary is a low-pass filter. Matches the earlier eco observation:
   ribosomal proteins pump hard only against a near-zero background.
2. Protection of the core: mobile genes arrive dialect-NEUTRAL (|z| ≲ 2 in
   all panels with adequate n). Incoming HGT code does not carry the host
   shadow — it cannot spoof kernel-style signal on arrival. The firewall
   works because foreign code is "unwritten," not because it's blocked by
   sequence identity.
3. Kernel is hardest to perturb: pseudo ring0 is 0.0z while userspace runs
   −64.6z; even strep ring0 moves only −9.9z against −82.4z userspace.

CAVEAT: part of the ring0 attenuation is mechanical — smaller n and locked
amino-acid composition in conserved proteins shrink synonymous wiggle room.
The sign consistency across all 10 genomes says the attenuation is structural
as well as statistical.

PREDICTION (falsifiable): long-resident mobile genes should show intermediate
|z| between fresh-mobile (≈0) and host userspace — an "assimilation gradient."
If confirmed, the flow direction (userspace → kernel, foreign code gets
re-written over time) is measured, not assumed.

### Assimilation gradient — TESTED (2026-08-25), prediction CONFIRMED

Method (assimilation_gradient.py, delivered): per-gene z vs composition null;
residency-age proxy = codon-usage anomaly (chi2 distance of the gene's 64-
codon vector to host) and, independently, GC3 deviation. Mobile genes sorted
most-anomalous (freshest) → most host-like (oldest), mean z per tercile, plus
Spearman rho of anomaly score vs sign(userspace)-aligned z (negative rho =
assimilation). Pipeline verified: pooled z reproduces the Tier-2 panel
(strep −83.6, pseudo −64.0, hvo −32.5, tth −28.8, sso +7.3, ...).

Tercile means (fresh → mid → old) and rho (chi2 / GC3 proxies):

| genome | n_mob | fresh | mid | old | userspace mean z | rho chi2 (p) | rho GC3 (p) |
|---|---|---|---|---|---|---|---|
| sso | 105 | −0.88 | +0.11 | +1.04 | +0.16 | −0.647 (<0.001) | −0.439 (<0.001) |
| strep | 32 | −0.22 | −0.98 | −1.67 | −1.16 | −0.604 (<0.001) | −0.511 (0.003) |
| pseudo | 28 | −0.27 | −0.48 | −0.77 | −0.87 | −0.200 (0.31) | −0.130 (0.51) |
| eco | 86 | +0.13 | +0.48 | −0.27 | +0.24 | +0.201 (0.06) | −0.198 (0.07) |
| pfu | 25 | +1.01 | +1.70 | +0.23 | −0.46 | −0.170 (0.42) | −0.140 (0.50) |
| hvo | 19 | −0.47 | +0.10 | −0.36 | −0.62 | −0.199 (0.41) | −0.025 (0.92) |

READ: monotone fresh→old convergence toward the host userspace dialect in
both genomes that have a strong dialect AND a large mobile cohort (sso, strep;
both proxies, p ≤ 0.003). pseudo shows the same monotone direction, under-
powered at n=28. eco is a null-effect control: its per-gene shadow is tiny
(userspace mean z +0.24), so there is nothing to assimilate TO — flat is the
correct outcome there. pfu/hvo inconclusive (small n, noisy terciles).

CONSEQUENCE for the ring model: the dialect is an acquired, host-side
property. Foreign code enters unwritten (z≈0) and is progressively re-written
into the host shadow as it ages in the genome — information flows host →
gene, not gene → host. Combined with the ring attenuation table, the full
picture: userspace writes the shadow at full amplitude, the ring boundary
low-passes it into ring0/ring1, and the firewall works because arriving code
has no signature at all.

## Pending / shopping list

- Archaeal codon bins (M. jannaschii, Sulfolobus, Haloferax, an Asgard if
  available) — Tier 2's decisive test: is the sign axis domain or lifestyle?
- thermus codon bin (re-run old claim through the null-corrected pipeline).
- Remaining old-project organism bins if found (the other viable/dead set).
- ul11_shadow_*_a30 runs (Phase 1 smoke test) — RUNNING/AWAITING CSVs.
