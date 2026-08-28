# Ribosome Project Plan — Ergo/min/ribosome

**Opened:** 2026-08-23
**Goal:** construct a eukaryotic 80S ribosome (60S + 40S subunits) in the ergo
waveform engine, as far toward function as the field supports.
**Lineage:** builds on the proinsulin MIDY campaign (see MULTIDOMAIN_FINDINGS.md
§22–§44) — multi-chain breaks, breakable restraints, substepping, per-chain
telemetry, thermal-floor stress assays all transfer directly.

## Target composition (human 80S)

- **60S large subunit:** 28S rRNA (~5,070 nt), 5.8S rRNA (~156 nt),
  5S rRNA (~121 nt), ~47 ribosomal proteins
- **40S small subunit:** 18S rRNA (~1,870 nt), ~33 ribosomal proteins
- Total order: ~7,000 nt + ~80 protein chains ≈ 12,000+ beads at one-bead-
  per-residue granularity. Full assembly is a GPU-scale target; the ladder
  below is ordered so every rung is CPU-feasible until rung 6.

## Design decisions (pre-registered)

1. **Nucleotide bead:** one bead per nucleotide, positioned at C1′ (protein
   beads stay at Cα). Rationale: C1′–C1′ spacing (~5.9 Å in A-form) maps
   cleanly onto our existing contact-map machinery; P is noisier in density.
2. **Backbone geometry:** RNA-specific Morse/angle/torsion targets taken from
   the reference structure (same native-derived Go philosophy as proteins —
   targets from geometry, never hand-tuned).
3. **Base pairing:** WC pairs as breakable harmonic restraints — literally the
   cystine block with RNA pair tables (BP_I/BP_J/BP_R0/BP_ON, K_BP param).
   Wobble/noncanonical pairs get their own K if needed (cf. MIS_KK per-pair).
4. **Stacking:** implicit in the Go contact map for rungs 0–2 (stacked
   neighbors are native contacts). A dedicated anisotropic stacking term is
   deferred until evidence says the map is insufficient.
5. **Electrostatics/Mg²⁺:** deliberately absent in v1. No phosphate repulsion,
   no ion atmosphere. We measure how far the map carries us; if tertiary
   assembly fails specifically at long-range RNA–RNA contacts, that failure
   is the justification for a charge term — added only with evidence, per the
   standing no-arbitrary-terms discipline.
6. **Verification discipline (inherited):** every new force term FD-validated
   before any long run; telemetry-only changes must bitwise-reproduce prior
   physics; runs as .csv; pre-registered reads before looking at results.

## The rung ladder

| Rung | System | Size | Certifies |
|---|---|---|---|
| 0 | Generator: nt parsing, bead extraction, BP table from DSSR/annotation | — | tooling |
| 1 | Hairpin (~22 nt stem-loop) | ~22 beads | bead type + A-form stem holds |
| 2 | tRNA (PDB 1EHZ, 76 nt) | 76 beads | tertiary L-shape from cloverleaf |
| 3 | 5S rRNA + L5/L18/L31 | ~120 nt + ~700 res | mixed RNA–protein assembly |
| 4 | 28S Domain V (PTC core) | ~500 nt | large RNA domain self-folds |
| 5 | 40S from pre-folded domains (fold-then-dock) | ~5,500 beads | subunit-scale assembly; GPU eval |
| 6 | 60S likewise | ~9,000 beads | GPU mandatory |

**Certification criteria per rung (pre-registered):**
- Rung 1: stem WC pairs hold R0 ± 20% under thermal floor f25; helical twist
  emergent (rise/twist within 15% of A-form).
- Rung 2: final RMSD < 5.0 model units (bead space) on ≥ 2/3 seeds; elbow
  (D/TΨC arm contact) forms without restraint — the tertiary emergence test.
- Rung 3: RNA–protein interface contacts from the reference recovered at
  ≥ 70%; proteins fold to their usual 3.5–5.0 range.
- Rung 4: domain RMSD < 6.0; PTC A/P-site geometry held under f25 floor
  (the MIDY stress assay reused as a functional-core stability read).
- Rungs 5–6: criteria set when we get there; requires the GPU handoff.

## Functional reads (deferred, in order of cost)

1. PTC A/P-site spacing stability under thermal floor (cheapest — rung 4 byproduct)
2. mRNA channel threading through assembled 40S
3. Intersubunit ratcheting (40S/60S relative rotation, frame dynamics)
4. Anything resembling translation requires tRNA charging + factors — out of
   scope until rungs 5–6 are solid

## Roadblocks register (updated as we hit them)

- (anticipated) N² pair scan cost beyond ~1,000 beads → GPU handoff timing
- (anticipated) no electrostatics → tertiary contact failure mode at rung 2/4
- (open) reference structure choice for human 80S components
- (open) noncanonical pair K calibration

## File layout (user side)

```
Ergo/min/ribosome/
  RIBOSOME_PLAN.md        (this file)
  RIBOSOME_FINDINGS.md    (created at rung 1; same audit format as MULTIDOMAIN)
  pdb/                    (reference structures)
  json/                   (parsed bead structures)
  runs/                   (.ergo variants + .csv outputs)
```
