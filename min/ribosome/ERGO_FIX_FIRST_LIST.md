# Ergo — Bug Tally & Golden-Pass Fix List

Everything hit during the ribosome campaign, with status. Ordered roughly by
severity for a pre-release golden pass. Dates 2026-08. Full narrative in
RIBOSOME_FINDINGS.md.

---

## A. Compiler / engine (mcl + SPIRV backend)

- [ ] **A1 — f64 GPU path never compiled (missing import).**
  `spirv.py` `_collect_f32_only_ops` (~line 189) references `IRWhileLoop`,
  which is not in the `from ..ir import (...)` list (~line 21) → NameError.
  Only fires when `get_real_precision() == 64`, so f64 SPIRV had literally
  never compiled. One-line import fix. **OPEN** (found by us, fix handed over).

- [x] **A2 — Extractor hole: DO-WHILE bodies fell through un-rejected.**
  `ir_gpu.py` `_check_item/_check_body` didn't reject IRWhileLoop body items;
  the INIT_CHAIN self-avoiding-walk DO WHILE got extracted to device and
  wrote BSS-zero CANDX over real positions. **FIXED by user/Kimi Code**
  (named rejection + CPU→GPU split guard: flow prefix must not read scalars
  the suffix writes). Regression: `tests/gpu_fallback_coil.ergo`.

- [x] **A3 — Backwards sync at host-fallback boundaries.**
  `ir_codegen.py` (~line 1383) fired stale-host-copy downloads
  unconditionally, clobbering host-fresh arrays. **FIXED by user/Kimi Code**
  (download only `_gpu_current - _cpu_dirty`).

- [x] **A4 — f32 DD-floor underflow (the all-NaN bug).**
  Pad slots have D=0 → DD=1e-30 → `PHOS_LAM*DD*DD` = 8e-60 underflows to 0
  in f32 → 0/0 = NaN; ~183 pad slots per segment NaN'd all velocities on the
  first force pass. Floor raised to 1e-16 (f64-bitwise-neutral, f32-safe).
  **FIXED in delivered variants + repo template — VERIFY your repo template
  actually has 1.0E-16 in all 6 force loops** (the copy uploaded to me still
  had 1.0E-30; my sandbox kept getting wiped and re-pulling the old file).

- [ ] **A5 — Legacy `_host_launch_code` in spirv.py (~line 682) hardcodes
  "double".** Not the live path (live dispatch is `_emit_gpu_dispatch` in
  ir_codegen.py, which is precision-aware), but it's a trap for anyone who
  wires it up later. Delete or fix. **OPEN** (cosmetic-hazard class).

## B. Generator (generate_protein_ergo.py)

- [ ] **B1 — Silent hydrophobic-flag zeroing on renumbered slices.**
  Sequence comes from the PDB matched by residue number against the json's
  `pdb_res`. If the slice json keeps original structure numbering but the PDB
  renumbers from 1, every lookup misses → all residues UNK → all
  RES_HYDRO = 0, silently. Caught by partition audit (43+0 ≠ 72).
  Fix: hard-fail when >N% of residues resolve to UNK. **OPEN**.

- [ ] **B2 — RNA adenines map to ALANINE when PDB uses CA atom names.**
  `parse_pdb_sequence` requires atom name `CA`; fed a mixed-chain PDB with
  CA-named RNA beads, resname `A` maps through the amino-acid table →
  hydrophobicity 0.5 on every adenine, silently. (Certified RNA builds
  avoided it by accident: C1' atom names → UNK → 0.) Fix: nucleotide
  resnames (A/U/G/C + modified) must never enter the AA hydro table;
  warn on AA/nucleotide namespace collision. **OPEN**.

- [ ] **B3 — Register torsions ON by default.**
  `--no-register` exists but default emits NREG register torsions; the
  certified protein recipes (ul18_solo_f02 era) had none. Builds without an
  explicit flag are NOT the certified recipe. Fix: default off, or at least
  print NREG loudly in the generation banner. **OPEN** (policy decision).

- [ ] **B4 — Chain-break handler strips inter-chain contacts by default**
  (MIDY-era assumption). Caused TWO stacked silent failures in the first
  5S RNP attempt (zero inter-chain force for 96k frames; then dock gate
  opened onto an empty contact list). `--keep-inter-contacts` was added and
  works; but "strip silently" remains the default. Fix: require explicit
  choice, or print inter-chain contact count in the banner (it does now:
  `inter_contacts=N` — keep that, and warn when 0 with multiple chains).
  **PARTIAL** (feature exists; default still hazardous).

## C. Analysis-side (my tooling — fixed, recorded for honesty)

- [x] **C1 — Hand-rolled quaternion Kabsch converged to wrong eigenvector on
  subset alignments.** Whole-chain values were correct (matched engine RMSD
  exactly), subset values garbage (e.g. mono CTD "8.09" when ≤4.98 was
  provable). Caused one wrong post-hoc claim ("assembly degrades per-domain
  folds") — **errata issued, all subset numbers recomputed with SVD Kabsch**
  and RIBOSOME_FINDINGS.md corrected. Lesson: validate alignment code
  against the engine's own whole-chain RMSD before trusting subsets.

## E. Proposed upgrades (design-stage, not bugs)

- [ ] **E1 — Hopf Handshake Bound (HHB): bounded "recursion" as a static
  schedule.** Prototype compiler policy, cleaned up from
  Hopf_Handshake_Bound_Policy.md (2026-08-25). Core rule: recursive
  handshake syntax is legal **only when the compiler can lower it to a
  static finite schedule** — no runtime call stack, no data-dependent
  recursion, no allocation in region. The recursion expresses topology
  (center → mediator → center), never search. Clauses:
  1. **Fixed shape:** endpoint A → one pinned mediator → endpoint B;
     chain length ≤ 2 per declared unit; a paired hopfion (two explicitly
     declared units) is the maximum composite. No fan-out, no mediator
     spawning mediators.
  2. **Monotonic activation:** visited bits, forward-only token; re-arming
     only at an explicit **EPOCH** boundary (new — resolves reset
     ambiguity for handshakes spanning frames). Rewind/recoil, if wanted,
     is a separate construct with its own counter (e.g. MAX_REWIND = 1).
  3. **Fixed tiny payload:** AMP/PHASE/SIGN/SECTOR/TARGET/STATUS;
     HS_FRAME_BYTES = 256, HS_MAX_DEPTH = 2, HS_TOTAL_BYTES = 512
     (control-block budget; fields/orbitals/maps stay in normal STATIC
     arrays). REAL pairs, no COMPLEX, no INTEGER*8 on GPU.
  4. **All loops counted:** every propagation has MAXIT + loud STATUS +
     ORACLE. SCANFAIL prints (cycle, stage, kept epsilon, pole count) and
     the recovery ladder is itself **static** (three unrolled widened
     attempts, fixed bounds — no retry loop). Structural violations
     (depth overflow, re-entry, payload overflow, ALLOCATE, broken
     invariant) are hard errors.
  5. **Sector invariants in the type:** CONSERVE PARITY / SPIN /
     NODE_COUNT / NORM declared per handshake. Sign/pole tests must use
     logical signbit tests, never products (df_radial2 W0 ~ 1e180 lesson).
  6. **Mandatory oracles:** norm/Parseval, united-atom, separated-atom,
     variational direction, triplet-null, dissociation limit, screened-vs-
     hydrogenic baseline, determinism. Prototype mode warns; certified
     mode rejects handshake blocks with no oracle clause.
  7. **GPU lowering:** unrolled schedule only. Reject when depth is not
     compile-time provable, payload has pointers/allocatables, or the
     mediator needs a dynamic stack. **Data-dependent activation is
     allowed only as a branchless mask** (DOCKM pattern: exact 0/1
     arithmetic, token moves every step weighted by the mask) — the
     schedule's control-flow shape must be data-independent even when the
     activation weight is not. (Amends the original clause 7, which
     banned the data-dependent WHEN its own syntax sketch used.)
  8. **Determinism oracle is per-target:** byte-determinism holds within
     (target, precision, build-hash) only. GPU-f32 vs CPU-f64 are
     independent seeds by design (coil RNG is precision-sensitive);
     cross-target agreement is statistical (basin distributions), never
     bitwise. (Amends the original "same input → same output hash".)
  Integration phases: (0) pattern-only with counted DO loops — NOTE:
  `ul18_stag5.ergo` (per-seam dock stagger, ribosome campaign) is already
  a living instance: static activation order, mediator carrying amplitude
  only, no control authority; (1) linter warnings; (2) VERIFY directive;
  (3) HANDSHAKE...ENDHANDSHAKE AST/IR node with schedule finiteness proof;
  (4) certification suite with positive AND negative oracles, reusing
  H₂⁺ parity / H₂ singlet-triplet / HeH⁺ / df_radial2 SCANFAIL as the
  ladder. One-sentence policy: handshake recursion is legal only as a
  bounded, oracle-instrumented token pass between two centers through a
  pinned amplitude carrier — depth ≤ 2, payload ≤ 512 bytes, no
  allocation, no re-entry, no silent failure.

- [ ] **E2 — HHB compiler prerequisites (surfaced by the campaign).**
  (a) A6 scalar dummy-arg copy-out must be fixed or permanently worked
  around with 1-element arrays; (b) undefined identifier in an array
  bound must be a HARD ERROR (the df_radial colon-bounds failure must
  never silently "run something"); (c) case policy needs a spec decision —
  until then generated handshake code is UPPERCASE-only; (d) no silent
  fallback semantics anywhere in the runtime (SCANFAIL must print);
  (e) dual-codegen drift needs a golden-output handshake test so legacy
  and IR paths cannot diverge quietly.

## D. Process hazards (not code bugs, but they bit us repeatedly)

- **D1 — /tmp wipe roulette.** Scripts and run dirs lived in /tmp on both
  our sides; repeated "file not found" / stale-file confusions, including a
  whole re-upload of attempt-1 CSVs as if new. Rule adopted: deliverables
  and runner inputs live in the project dir, /tmp is scratch only.
- **D2 — Stale-binary/cert hazard.** First cert gate "failed" only because a
  stale broken-pipeline CSV was in the folder. The cert analysis now checks
  row counts / NaN fractions before the verdict.
- **D3 — bestofn_run.py cd's to repo root internally**, breaking relative
  variant paths. Drive batch runs with explicit per-variant commands from
  `min/ribosome` instead (documented convention).

---

## Golden-pass checklist (suggested order)

1. A1 (one-line import) — then run the f64 GPU determinism pair as proof.
2. A4 verification — grep the repo template for `1.0E-30`; must be zero hits.
3. B1+B2 — make UNK-sequence resolution a hard error or loud warning;
   namespace-separate nucleotide vs amino-acid lookups.
4. B4/B3 — generator banner must print: NRES, chains/breaks, inter-chain
   contact count, NREG, NCYSPAIR, DD floor value. If any is 0/unexpected,
   refuse or warn loudly.
5. A5 — delete the dead `double`-hardcoded launcher.
6. Re-run the full certification suite clean: `gpu_fallback_coil` (bitwise
   f64+f32), tRNA 3-seed gate, one d5t solo, uL11 mono/dock — all should
   reproduce the documented numbers within basin tolerance.
7. E2 prerequisites (hard-error array bounds, loud SCANFAIL, case policy,
   dummy-arg copy-out) — these gate any future HHB work; cheap to land with
   the A-series. E1 itself is post-golden-pass design work.
