# NEXT SESSION — Project Handoff (Ergo)

**Written:** 2026-08-03, end of session approaching compaction.
Read this first. It covers the engine, the compiler, the language vs Fortran,
and where everything lives.

---

## 1. What this project is

**Ergo** — a compiled, deterministic simulation language (F77-inspired,
static types, no hidden allocation) with a Python compiler in `core/` that
emits C, plus SPIR-V GPU backends. It is NOT the old `mcl` toolchain —
compile with `python -m core`.

Everything in this repo is built on top of it: a phase-diagram engine
(quantum rotor chains, DMRG, ED), protein folding (Protein Margin),
FDTD electrodynamics, master-equation models (trimer PME, graphene,
quantum battery), and LLPS/condensate simulation.

## 2. The compiler — location and usage

**Location:** `core/` (Python package). Entry point: `core/__main__.py`.

**Compile & run:**
```bash
python -m core <source>.ergo -o <binary>     # compile
./<binary>                                    # run
python -m core <graph>.json -o <binary>      # node graph → binary (Phase A)
python -m core <graph>.json --emit-ergo      # graph → readable Ergo source
```

**Key flags:**
- `--target spirv` — GPU (Vulkan; works on the RTX 2060 here)
- `--precision f32|f64` (default f64)
- `--arena-size <N>` — ALLOCATABLE arena (1 GiB default; accepts K/M/G)
- `--emit-c` — print generated C instead of compiling
- `--emit-ir` — dump IR
- `--kernel-report` — show which loops extract to GPU and why others don't
- `--cpu-fast-math`, `--gpu-fast-math` — precision-relaxing (opt-in only)
- `-N`, `-M` — override DEFAULT_N / MAXPART parameters

**Compiler internals** (if you need to change it):
- `core/lexer.py`, `parser.py` — front end
- `core/checker.py` — types, intrinsic table (INTRINSIC_RETURNS/ARG_RULES)
- `core/codegen.py` — legacy C backend
- `core/ir.py`, `ir_builder.py`, `ir_codegen.py` — the DEFAULT pipeline
  (the legacy path exists but the default is IR — both were patched for
  DOT_PRODUCT and HASH/RAND)
- `core/ir_gpu.py` — kernel extraction (loop classification:
  INJECTIVE/FLOW/SHIFT/REDUCTION/SCATTER; conservative CPU fallback with
  named diagnostics)
- `core/backends/spirv.py` — SPIR-V emission (staged reduction, segmented
  reduction, ATAN2, HASH/RAND all lowered here)
- `core/runtime/vk_host.c` — Vulkan host runtime (frame-batch dispatch)
- `core/archive/changes.md` — full feature history (F96–F107)

## 3. Ergo vs Fortran — the differences that bite

Ergo looks like Fortran but is NOT. The gotchas that cost time if you
assume Fortran semantics:

- **No PROGRAM/END PROGRAM wrapper.** Top-level statements are the main
  body; subroutines are top-level units. Flat structure.
- **`ENDDO` and `ENDIF` are one word.** `END DO` / `END IF` fail to parse.
- **No single-line IF.** `IF (cond) CYCLE` is illegal — use block IF/ENDIF.
- **Assignment is `:=`** (not `=`). `=` / `==` are comparison.
- **`WRITE(*, "fmt") args`** — printf-style to stdout; unit `0` = stderr.
  File units exist (Part 10, IR-only): `OPEN(unit, "path", "WRITE"|"APPEND")`
  / `CLOSE(unit)`, formatted `WRITE(unit, "fmt")`, raw-record
  `WRITE(unit) A(lo:hi)`, and the `.esf` framed stream intrinsics
  (`CALL ESF_OPEN/ESF_WRITE/ESF_CLOSE`, `CH := ESF_NEXT(unit)` — see
  `Spec/Ergo_Stream_Format.md`). READ is deferred.
  `PRINT x` takes ONE expression only.
- **STATIC for shared state** — file-scope arrays; subroutines access
  STATIC directly by name (passing STATIC as an argument compiles with
  a teaching warning — see Spec Part 7).
- **DATA statements** fill column-major (first subscript fastest).
- **Column-major arrays** — `A(i,j)` → `A[j-1][i-1]` in C. First index
  varies fastest in memory.
- **No array expressions** (`A := B + C*D` on arrays is illegal — write
  explicit loops).
- **`ALLOCATABLE` arrays bump-allocate from a static arena** (no libc
  malloc). DEALLOCATE is a no-op. `--arena-size` controls it.
- **No string concatenation operator** (`//` doesn't exist).
- **No `RAND` builtin historically** — use the new intrinsics below.
- **Relational operators:** `==`, `=`, `/=`, `≠`, `≤`, `≥`, `.GT.`, `.LT.`,
  `.GE.`, `.LE.`, `.EQ.`, `.NE.` all work.
- **32-bit INTEGER** — multiplicative hash PRNG idioms wrap early and
  cause conditional bias (measured). Use the compiler intrinsics instead:

**PRNG intrinsics (F107, validated):**
```
S := HASH(S)          ! splitmix64, chaining
X := RAND(S)          ! uniform REAL in [0,1)
X := RAND(SEED + I)   ! counter-based independent variates
```

**GPU extraction rules that matter:**
- Subroutines never extract — inline into main body or top level.
- `DO WHILE` loops aren't traversed — use fixed-count `DO K` with an
  idempotent fixed point + convergence flag.
- Reduction loops extract if single REAL accumulator (or N accumulators,
  F106), straight-line body, start=1 step=1.
- 2D stencils extract (F104) if writes are exactly at (I,J), no
  cross-iteration reads of written arrays, affine indices.
- Anything failing checks → CPU fallback with a NAMED reason in
  `--kernel-report`. Never silently wrong.

## 4. Spec files (authoritative language reference)

- **`Spec/Ergo_Spec.md`** — the full language spec (operators, memory
  model, column-major layout, STATIC semantics, GPU execution model,
  IR loop classification, determinism contract)
- **`Spec/Ergo_Intrinsic_Signatures_Complete.md`** — every intrinsic with
  types/shapes/memory semantics (now includes HASH/RAND and DOT_PRODUCT)
- **`Spec/Arena_Lowering_Brief.md`** — the ALLOCATABLE arena model
- `Spec/` also has design docs for specific systems (GPU roadmap,
  diagnostics, decay systems, etc.) — check filenames as needed.

## 5. Findings docs (what we learned, where it's written down)

- **`min/FINDINGS.md`** — the physics campaign: Luttinger-liquid critical
  phase (c=1, z=1, BKT, exact competition line B=0.25), trimer PME
  replication (Li/Pokorný), DMRG trap + referee protocol, quantum battery
  analysis (P ∝ N^1.5 classical, linear quantum, N² excluded at 5σ)
- **`min/pmargin/PROTEIN_MARGIN_FINDINGS.md`** — the protein campaign:
  packed sweeps, tempering, ultrasonic pulse rescue, white-bath
  discovery, SdrD ceiling map, fold-then-dock, MC placement solved
- **`min/pmargin/FORCE_FIELD_REFERENCE.md`** — every force-field term and
  knob (for reweighting work)
- **`min/fdtd/FDTD_FINDINGS.md`** — electrodynamics: wave optics, Weber vs
  Maxwell (Maxwell handles longitudinal force via E-field), dendrite test
  (voids are passive; bunching is the attractor)
- **`min/LITERATURE_SCOPING.md`** — novelty positioning vs published
  literature for the critical-phase paper

## 6. Key directories

- `core/` — the Ergo compiler (Python)
- `min/` — the redirect/rotor/condensate/graphene/qbattery work + all
  findings docs
- `min/phase_ed/` — phase-diagram engine (ED, DMRG, plugins:
  rotor/xxz/fk/rydberg, bulk mapping)
- `min/pmargin/` — protein margin (packed sweeps, tempering, pulse,
  SdrD, docking, MC)
- `min/fdtd/` — FDTD electrodynamics (wave optics, Weber, dendrite)
- `min/amyloid/` — amyloid cross-chain geometry + register problem
- `min/condensate/` — LLPS + white-bath discovery
- `min/qbattery/` — quantum battery analysis
- `tests/` — hundreds of .ergo programs (waveform_* folding sims,
  gpu_* GPU tests, sq2core, dot_product, prng, etc.)
- `papers/` — PDFs read this campaign (Li/Pokorný trimer, LLPS review,
  quantum battery, Maxwell conjecture, Jacobi NeurIPS, etc.) + extracted
  .txt versions
- `Testing/` — allocator benchmarks (V8 slab, V22 squaragon, GEO)

## 7. Hard-won operational lessons

- **Oracle discipline:** every result has a validation oracle or a
  documented reason it can't. Keep it that way.
- **The sim's old "thermal noise" was a quasi-periodic slosh drive, NOT a
  stochastic bath** — evaporation didn't exist in it. The white-hash bath
  (splitmix hash → now the HASH/RAND intrinsics) fixes this. Prior
  evaporation/dissolution claims are superseded; folding/pulse results
  stand (mechanical phenomena, variance-matched).
- **Precision contract:** distributions yes, trajectories no. f32 GPU
  transcendentals reroute chaotic trajectories; distribution statistics
  are preserved. Never compare per-seed RMSD across backends; compare
  distributions.
- **32-bit INTEGER** — don't hand-roll hash PRNGs; use HASH/RAND (F107).
- **GPU batching pattern:** pack independent work into one big vector
  (block index in the data), one kernel per operation type per frame —
  not per block per op. This is how stage-4 got 0.27 s sweeps.
- **The referee protocol for DMRG/ED:** energy is the referee, observables
  are not. Any state that fails the energy check is wrong no matter how
  converged it looks.
- **Background tasks:** long runs go to background with checkpointing
  (h5 per 10 sweeps in dmrg_driver.py pattern). The IDE has crashed on
  dense numpy eigh before — prefer Ergo binaries for heavy solves.

## 8. Where things stand (open threads)

- Multi-domain placement: SOLVED by rigid-body MC (placement < 3,
  −76%). Deployable version needs field-consistent proxy scoring.
- Deterministic restraint class for docking: exhausted (all nulls
  documented in PROTEIN_MARGIN_FINDINGS.md §9.6–9.8).
- Force-field ceiling: the field's minimum ≠ crystal (triple-eliminated:
  dynamics, protocol, cofactors). Reweighting candidates in
  FORCE_FIELD_REFERENCE.md.
- Paper-ready: critical phase (FINDINGS.md), DMRG referee protocol,
  Protein Margin characterization.
- Dendrite tip-growth (DBM-style Laplacian growth) is the open sim if
  the dendrite thread resumes — free-segment bunching is NOT dendritic.

## 9. Roadmap item (flagged by user): 32-bit ceiling + GPU tiling

**The ceiling:** Ergo INTEGER is 32-bit (C `int`). Signed range ~2.1 B —
overflows at N=20 for ED state spaces (N=18 → 387M, N=20 → 3.5B).
GPU buffer *addressing* is also 32-bit (`maxStorageBufferRange` ~2–4 GB)
even though Int64 ALU exists (used for HASH/RAND; `shaderInt64` enabled
in `vk_host.c`). So large states can't live in one GPU buffer regardless
of ALU support.

**The design (user's, correct):** int64 on the CPU (holds full state),
GPU processes 32-bit tiles with halo exchange — standard out-of-core
pattern, fits the existing packed-batch machinery:
- Eigensolvers: matvec tiles per 32-bit slice (global index maps on CPU),
  norms reduce across tiles. Power iteration = N tile dispatches + 1
  global reduction per iteration.
- Stencils/MD: thin halos (short-range stencils), CPU orchestrates.
- Already exists: packed-batch pattern, frame-batch transfers, arena,
  white-hash PRNG, reduction machinery. New work: int64 CPU type, tile/halo
  runtime, cross-tile reduction path.

**Bridge (already working):** CPU-side 64-bit ED via numba runs today
(N=16 bridge done this way) — physics isn't blocked while GPU tiling is
built. GPU path stays capped at N=16–17 for eigensolvers until then.

**Sequencing:** substantial piece of work (type system + tiling runtime +
halo management) — deserves a dedicated session, not a side quest.

---
