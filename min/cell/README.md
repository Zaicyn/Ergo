# Project CELL — ribosome → membrane → the shape of a cell

Approved 2026-08-30. Plan of record:
`Spec/` plan of record is the approved plan (session plan file);
this README carries the working ladder and the pre-registered oracles.

**Goal:** a coarse-grained cell — self-assembled closed vesicle,
buc-model electrochemistry on the boundary, and a ribosome-synthesized
membrane protein inserted into it. Minimum viable: the *shape* of a
cell with a protein in the membrane.

## Assets

- `tests/buc_membrane_unit.ergo` — single-cell Nernst-Planck model
  (fixed point PSI≈−246, ATP≈0.88).
- `tests/buc_colony.ergo` / `buc_colony_gpu.ergo` — colony port.
- `Cellular demos/MCLtranslation.md` — the physics derivation.
- `tests/waveform_membrane.ergo` — proven 2D amphiphilic sheet.
- `min/ribosome/ul18_stag5.ergo` — the MD engine (hydrophobic table,
  multi-chain, staged dock rail, GPU-certified).

## Milestone ladder and pre-registered oracles

### M0 — dynamic neighbor list (engine feature)
Spatial-hash/cell-list short-range force path, GPU-extractable.
**Status: DONE 2026-08-30 — all oracles pass, see
`min/cell/M0_FINDINGS.md`. The loop-carried GPU→CPU sync compiler bug
it surfaced is FIXED (frame-level back-edge refresh,
core/ir_codegen.py; regression test tests/gpu_backedge_sync.ergo;
Spec Part 8.1).**
Oracles:
- O1 force equivalence vs brute-force N² mirror on a random cloud
  (max |ΔF| ~0 at f64, order 1e-12 class)
- O2 byte-determinism double-run
- O3 perf: measured N² vs cell-list crossover at N=10k
- Negative control: misaligned bucket assignment must be caught by O1.

### M1 — 3D vesicle self-assembly
Amphiphile beads (polar HEAD / hydrophobic TAIL + orientation axis),
bending rigidity on local normals, dispersed-gas start.
Oracles:
- O1 closure: genus-0 inside/outside ray-cast test passes
- O2 bilayer thickness in pre-registered band
- O3 surface ∝ N^(2/3) scaling across two sizes
- O4 edge energy → 0 (no persistent free edge)
- Negative control: pure-TAIL beads must NOT form a bilayer
- Known failure mode to log: micelle vs vesicle competition (headgroup
  bias knob).

### M2 — electrochemistry on the vesicle
buc_membrane_unit op chain on the closed boundary; inside/outside ion
pools from the closure test; leak gated by local packing-defect density.
Oracles:
- O1 fixed point matches buc_membrane_unit (PSI≈−246, ATP≈0.88 within
  the coarse-grain band)
- O2 collapse when leak exceeds repair (extinction + hysteresis,
  qualitative)

### M3 — secretion: ribosome → membrane protein
Chain synthesized under the staged rail (translation clock) with a
hydrophobic anchor (single TM-helix class), released at the vesicle.
Oracles:
- O1 insertion orientation: anchor spans the bilayer, termini on
  opposite sides
- O2 insertion changes local leak per the M2 rules (channel behavior)
- O3 determinism double-run
- Negative control: anchorless chain must NOT insert.

### M4 (stretch) — colony coupling
Division condition on PSI/ATP/mesh from buc_colony. Optional; M3 is the
project's definition of done.

## Working rules

- Certification per project standard: pre-registered oracles, mirror
  verification, byte-determinism, negative controls, findings doc per
  milestone (`M1_FINDINGS.md` etc.), failures recorded.
- GPU jobs serialize; check `nvidia-smi` first.
- Commits by the user-facing verifier after independent verification.
