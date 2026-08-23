# LEGACY_CATALOG — pre-1.0 tech-debt survey

Read-only survey of `/home/zaiken/Ergo`, compiled 2026-08-23 (HEAD `cde1879`).
Goal: zero legacy tech debt before 1.0. Each entry: what it is, evidence of
obsolescence (last commit, live references), blast radius, disposition.

Disposition codes: **DELETE** / **DEPRECATE-then-delete** / **KEEP-as-reference**
(move to archive/) / **NEEDS-PORT** / **DECIDE** (question for the user stated).

**Repo-wide fact that shapes everything below:** `.gitignore` is whitelist-mode
(`*` ignored, specific trees re-enabled). Tracked trees: `core/`, `Spec/`,
`tests/` (sources only), `Testing/` (sources only), `structured/`, `allocator/`,
`tools/`, `min/` (`.ergo`/`.py`/`.md` only), plus `README.md`,
`NEXT_SESSION.md`, `galaxy_structured.ergo`. **Every other top-level tree is
untracked** — invisible to a fresh clone. Verified: no ELF binaries, `.o`,
`.so`, `.spv`, or `.spvasm` files are tracked; `core/runtime/render_shaders.h`
(generated) IS tracked, so `--render` builds without rerunning
`build_shaders.sh`.

---

## 1. Legacy AST codegen — `core/codegen.py`

Deprecated 2026-08-12 per `core/driver.py:177-184` (prints deprecation warning
when `use_ir=False`); last real change `d5d353a` 2026-08-19 (batch-2 golden
fixes — note: it is still receiving parity fixes, it is not frozen).

- **Live references (complete list):** `core/driver.py:13` (import) and the
  `use_ir=False` branch; `tests/golden/run_golden.py:63-70` (sole caller — no
  CLI route exists, the harness calls `compile_file(..., use_ir=False)`
  in-process); a comment in `tests/sub_scalar_ref.ergo:4`; documentation in
  `Spec/Ergo_Spec.md:158-162` and `tests/golden/KNOWN_DIVERGENCES.md`.
- **Features existing ONLY in legacy: NONE.** It is a strict subset — legacy
  *raises* "IR-path only" for ESF stream I/O (`codegen.py:419-424`), OPEN/CLOSE
  file units (`:447-451`), and WRITE to file units / raw-record WRITE
  (`:603-609`). COMPLEX refuses on both paths (`:33-43`).
- **Blast radius of removal:** the A2 golden harness loses its second path —
  that harness exists *only* to cross-check legacy vs IR, so removing legacy
  makes `run_golden.py` + `KNOWN_DIVERGENCES.md` pointless (delete or rewrite
  as IR-only regression goldens). Also touch: `driver.py` (`use_ir` param),
  `Ergo_Spec.md` backend paragraph, `tests/sub_scalar_ref.ergo` comment,
  driver comment pointer to `ERGO_FIX_FIRST_LIST.md A2` (which lives at
  `min/octonion/ERGO_FIX_FIRST_LIST.md`, not repo root — minor doc rot).
- **Disposition: DECIDE.** Question: keep the dual-path golden check through
  1.0 (it caught real bugs — see KNOWN_DIVERGENCES "Fixed in this batch"), or
  delete legacy now and convert the harness to IR-only output goldens? If
  deleted: codegen.py, run_golden.py's legacy half, and the `use_ir` parameter
  all go together.

## 2. `core/archive/` — old compiler snapshots + `changes.md`

Snapshots of `codegen/ir_builder/lexer/parser` plus `changes.md` (feature
history F66–F107). Untouched since the `mcl/ → core/` rename (`a3a1017`,
2026-08-03, rename-only). No code imports it (grep for `core.archive` /
`from .archive`: zero code hits).

- **Live references:** `changes.md` is cited as history by `NEXT_SESSION.md:54`,
  `Spec/Ergo_Spec.md:876`, `min/phase_ed/engine/stage4_check.md:87`,
  `min/pmargin/PROTEIN_MARGIN_FINDINGS.md:526`. The four `.py` snapshots have
  no references at all.
- **Blast radius:** deleting the `.py` snapshots breaks nothing. Deleting
  `changes.md` orphans four doc citations.
- **Disposition: KEEP-as-reference for `changes.md`; DELETE the four `.py`
  snapshots** (their content is in git history anyway). Low risk.

## 3. JIT — `core/jit.py` (supported) and `core/jit_x86.py` (experimental)

`core/jit.py` is the documented supported JIT (ctypes dlopen of gcc-built
`.so`); `core/archive/changes.md:1177` names it the supported path and
`jit_x86.py`'s own docstring defers to it. Only user found: untracked
`jit-examples/conway_colony.py`. **No tracked file imports `core.jit`.**

`core/jit_x86.py` — direct x86-64 machine-code emitter, self-described
unstable ("for a working JIT today use core.jit"), flagged experimental in
`min/octonion/ERGO_FIX_FIRST_LIST.md:157`. Zero importers anywhere.

- **Blast radius:** removing `jit_x86.py` breaks nothing tracked. Removing
  `jit.py` breaks `jit-examples/` (untracked) and a public API.
- **Disposition:** `jit_x86.py` — **DECIDE** (is native-machine-code JIT a
  1.0 aspiration? if not, DELETE). `jit.py` — **KEEP** (working, small,
  documented) but consider tracking `jit-examples/` or deleting it.

## 4. Tooling — `core/lsp_server.py`, `core/nodegraph.py`

- `core/lsp_server.py`: no tracked importers. Its only launcher,
  `ergo-extension/extension.js:18`, spawns `python -m mcl.lsp_server` —
  **broken since the Aug-3 rename** (`mcl` package no longer exists). Its own
  docstring says `python -m mcl.lsp_server`. venv has pygls 2.1.1; the
  `pygls.lsp.server` import matches pygls v2 API, but the server has not been
  run/verified since the rename. Untouched since `a3a1017`.
- `core/nodegraph.py`: self-contained (imports only `json`/`dataclasses`),
  **zero importers in the entire repo**. Mentioned only in stale `README.md:259`
  and designed in `Spec/Ergo_NodeGraph_Design.md` (2026-04-28). Orphan.
- **Disposition: DECIDE** (same question for both): is the editor/LSP and
  node-graph tooling in scope for 1.0? If yes, both need a fix-and-verify pass
  (extension.js module path at minimum). If no: DELETE `nodegraph.py`,
  DEPRECATE-then-delete the LSP + `ergo-extension/`.
- **RESOLVED 2026-08 (nodegraph only):** user ruled it an essential
  production feature — completed and gated; see "Decisions recorded"
  below. The LSP half of the question stays open.

## 5. NVVM backend — `core/backends/nvvm.py`

Known-broken by its own docstring banner ("EXPERIMENTAL — KNOWN BROKEN"),
constructor raises `MCLError` unconditionally (`nvvm.py:98-101`) since F87
(2026-07-21, per `changes.md`). Last content change `dccc79e` 2026-05-11. All
GPU work since is SPIRV. No script or test uses `--target nvvm` (grep clean).
`driver.py:325` notes "nvvm raises on construction anyway".

- **Blast radius of removal:** `driver.py:404-405` target validation list;
  `core/__main__.py` help texts that still cite nvvm as the example target
  (`:31`) and as the `--gpu-fast-math` consumer (`:81-83`) — those strings are
  stale either way. Historical docs (`Spec/Ergo_GPU_Roadmap.md`, the
  `Spec/Ergo_Vulkan_Plan.md` comparison table) describe it.
- **Disposition: DECIDE.** It is already a loud-stub; options: keep the stub
  (costs nothing, documents the dead end), or DELETE the file and drop "nvvm"
  from the driver target list. Either way fix the `__main__.py` help text.
- **RESOLVED 2026-08:** keep-stub now, delete at 1.0 unless a CUDA-only
  deployment requirement appears — full reasoning + the musl analysis in
  "Decisions recorded" below.

## 6. Render runtime — `core/runtime/vk_render.c` orphan; `--render` path

- **`vk_render.c` is dead code.** Nothing `#include`s it or links it (grep for
  `vk_render.c` hits only `Spec/Render_Pipeline_Handoff.md` and its own
  header). It redefines `ergo_vk_render_points` (`vk_render.c:235`) which
  `vk_host.c:2958` also defines — compiling both would be a duplicate-symbol
  error. It is the residue of the incomplete integration described in
  `Spec/Render_Pipeline_Handoff.md` (2026-04-30: "WRITTEN | needs
  integration"). `vk_host.c` clearly won (it has full render functions at
  lines 2775-3810 plus headless stubs at 4157+).
  **Disposition: DELETE** — zero blast radius; or DECIDE if the handoff was
  meant to be finished instead.
- **`--render` path itself** (`vk_host.c` + shaders + `render_shaders.h`):
  wired into `driver.py:202-206` and `ir_codegen.py` render calls; runtime
  files touched by today's commit `cde1879`. Not verifiable without a Vulkan
  display from this survey. The three C harnesses (`tests/test_vk_render.c`,
  `test_vk_particle.c`, `test_galaxy_render.c`) carry stale build comments
  referencing `mcl/runtime/`. **Disposition: KEEP, manually verify once; fix
  the stale build comments.**

## 7. `core/runtime/ergo_net.h` — UDP oracle/consensus transport

Live. Consumed by `core/ir_codegen.py` (`#include "ergo_net.h"` at `:270`;
verify/census/field/spawn/consensus calls at `:2594-3161`). Enabled at runtime
via `ERGO_CONSENSUS=1`; used by `galaxy_structured.ergo:1435` and
`structured/main.ergo:32`. **Disposition: KEEP.**

## 8. Doc/script drift

- **`python -m mcl` (renamed to `core` on Aug-3):** still in user-facing
  places — `README.md:20` (quick start!), `core/__main__.py:1` docstring and
  `prog="mcl"` (`:12`), `core/lsp_server.py:3`,
  `core/runtime/build_shaders.sh:4`, `ergo-extension/extension.js:18`
  (functional break), `android/build_android.sh:6,63,103-104` (functional
  break, untracked tree), comments in `tests/gpu_index_patterns.ergo:10`,
  `tests/test_vk_particle.c:16`, `tests/test_galaxy_render.c:10`,
  `tests/test_vk_render.c:9`, `Testing/x86comparison.md:105`,
  `structured/BUILD.md:26-32`, `structured/sig_baselines/README.md:22`, and
  many dated `Spec/` briefs (Arena/Allocator/SPIRV_Peephole/Render_Handoff/
  Threshold_Tuning/VSCodium/Ergo_Diagnostics/x86_Determinism_Audit — the last
  also has a broken `[mcl/__main__.py](../mcl/__main__.py)` link at :139).
  **Disposition:** fix the live surfaces (README, `__main__`, extension.js,
  build_android.sh, test build comments); leave or batch-annotate dated Spec
  briefs. Zero risk.
- **`--fast-math` deprecated alias:** still accepted with a warning
  (`__main__.py:86-90,230-236`), documented as "one-release deprecation alias"
  — kept since `dccc79e` (2026-05-11), ~3.5 months. Only live use found:
  README quick start (itself stale). **Disposition: DELETE the alias** when
  README is fixed; tiny blast radius.
- **"passing STATIC as argument is forbidden" — wrong.** Reality:
  `core/checker.py:760-776` emits a *warning* ("TEACHES rather than breaks the
  build"), goldened in `tests/golden/check_errors.py:47-51` ("warning, not
  error"). Stale claims at `NEXT_SESSION.md:74` ("is forbidden"),
  `Spec/Ergo_Spec.md:154` ("remain forbidden"), `Spec/MCL_Design_COMPLETE.md:320`.
  **Disposition: doc fix** — say "warned against, still compiles".
- **Other deprecated flags:** `--no-verify` (used by `structured/main_sq4.ergo`;
  legitimate feature), `--promote-locals` (used in
  `Spec/Threshold_Tuning_Guide.md`), `--no-split` (used in many build
  commands) — all live, not debt.
- **`Spec/` docs describing superseded things:** `MCL_Design_COMPLETE.md`
  ("Ready for Implementation" — pre-implementation lock doc, superseded by
  `Ergo_Spec.md`); `MCL_Intrinsic_Signatures_Complete.md` (2026-04-27,
  superseded by `Ergo_Intrinsic_Signatures_Complete.md`, 2026-08-19);
  `Ergo_GPU_Roadmap.md` (the NVVM plan — a dead end);
  `Render_Pipeline_Handoff.md` (describes the vk_render.c integration that
  never happened). **Disposition: KEEP-as-reference** with a one-line
  "SUPERSEDED by X" header, or move to `Spec/archive/`. DECIDE on taste.

## 9. Top-level untracked trees (whitelist `.gitignore`)

None of these are in git; all survive only on this machine. Each needs
**track / archive / delete** — that is inherently a user decision.

- `V22` — **symlink to `/home/zaiken/sanity/Sanity/V22`**, an external
  directory with its own `.git`. Not deletable from here without touching
  another project; the symlink itself is the only repo-resident artifact.
  DECIDE: remove symlink.
- `galaxy/` — old galaxy sim (`galaxy_full.ergo`, generated `_gen.c`, `.txt`
  dumps). Superseded in spirit by root `galaxy_structured.ergo` (tracked,
  currently dirty) and `structured/`. Likely DELETE. DECIDE.
- `structured/` — **tracked**, 31 files, "WIP snapshot: SQ4 fluid spawner
  integration (parked mid-Phase-A)" `445c748` 2026-08-04. Its BUILD.md uses
  stale `python -m mcl`. DECIDE: is it still parked-but-alive, or superseded
  by root `galaxy_structured.ergo`?
- `android/` + `android-app/` — untracked; `build_android.sh` broken by the
  rename (see §8). Note: `core/runtime/vk_host.c:127-135,332` still carries
  Android `#ifdef` branches — load-bearing only for this target. DECIDE:
  revive (fix script, track tree) or drop (delete trees + strip Android
  branches from vk_host.c).
- `ergo-extension/` — VS Code extension, untracked, LSP launch broken (§4).
  DECIDE with the LSP question.
- `jit-examples/` — untracked, only user of `core/jit.py`; its README
  references a stale `examples/` path. DECIDE: track it (it's the JIT's only
  demo) or delete.
- `archive/`, `96/`, `spectral tool/`, `Cellular demos/` — old Python/Fortran
  experiment scripts (incl. `.f` F77 sources), untracked, no references.
  DELETE or KEEP-as-reference locally. DECIDE.
- `schismatomic/`, `schismdynamics/` — standalone C/CUDA dynamics library
  (CMake, barnes-hut, hex spatial), untracked, no references from tracked
  code. DECIDE.
- `papers/`, `reference/`, `pdb/`, `work/`, `.assistant/`, `KimiSkills/`,
  `Protein_Margin/`, `minbrain/`, `min/m0/` (new untracked viviani work) —
  data/tooling trees. `pdb/` matters: `tests/generate_protein_ergo.py` reads
  PDB files from it, so the protein test-generation workflow is not
  reproducible from a fresh clone. DECIDE per tree.
- `Testing/` — **tracked** (40 source files): V8/V9/V16/V22/GEO CUDA allocator
  prototypes + asm Makefile, last commit `bdd6cc7` 2026-05-12. Historical, but
  cited as read-only cross-reference by `allocator/TUNING_FINDINGS.md` and the
  allocator Spec briefs. `Testing/asm/` is untracked-regenerable by design.
  **KEEP-as-reference** (optionally move under `archive/`).

## 10. Build artifacts in git

Clean. Verified: `git ls-files` contains no ELF/`.o`/`.so`/`.spv`/`.spvasm`;
`tests/` binaries, `.out` and `.txt` dumps (hundreds on disk) are untracked by
the whitelist; `core/runtime/*.spv` untracked but `render_shaders.h` (their
compiled-in form) is tracked. One note: `allocator/sq2core.f` was suspected
superseded by `sq4core.f` — **false**: `allocator/TUNING_FINDINGS.md` uses
sq2core.f as the F77 cross-validation reference, and `tests/sq2core.ergo` is
in the golden corpus. KEEP both.

## 11. `tests/` corpus vs golden harness

203 tracked `.ergo` files; the golden corpus covers 16
(`tests/golden/run_golden.py:25-42`). There is **no CI** (no `.github/`), so
"obsolete test" can't be established by a passing signal. Known
caveats: `gpu_*` tests need Vulkan; `waveform_*` protein programs are
generated by `tests/generate_protein_ergo.py` from untracked `pdb/` assets;
`tests/stream/` and `tests/golden/check_errors.py` are current (today's
commits). **Disposition: DECIDE** — needs an audit run (compile-and-run each,
classify failures) before anything is deleted; do not bulk-delete on age
alone, several "old" tests are the only coverage of their feature.

## 12. `README.md` and `NEXT_SESSION.md`

- `README.md`: titled "Ergo (MCL)", quick start broken (`python3 -m mcl`,
  `--fast-math`), repo map lists `nodegraph.py` and "--fast-math support".
  First thing a 1.0 reader sees. **Fix (NEEDS-PORT of content, not code).**
- `NEXT_SESSION.md`: dated 2026-08-03 session handoff; contains the stale
  STATIC-forbidden claim (:74). **DECIDE:** keep as a rolling handoff
  (then fix), or delete for 1.0.

---

## Summary table — suggested cleanup order (risk-free first)

| # | Item | Action | Blast radius |
|---|------|--------|--------------|
| 1 | `python -m mcl` in README/`__main__`/test comments | Doc fix | none |
| 2 | STATIC-as-argument "forbidden" claims (Spec, NEXT_SESSION) | Doc fix | none |
| 3 | `ergo-extension/extension.js`, `android/build_android.sh` mcl→core | Fix (currently broken) | none |
| 4 | `core/runtime/vk_render.c` | DELETE | none — orphan, nothing includes it |
| 5 | `core/archive/*.py` snapshots (keep changes.md) | DELETE | none — git history has them |
| 6 | `--fast-math` alias | DELETE after #1 | README line only |
| 7 | Superseded Spec docs (MCL_Design_COMPLETE, MCL_Intrinsic_Signatures, Ergo_GPU_Roadmap, Render_Pipeline_Handoff) | Mark SUPERSEDED / move to Spec/archive | none |
| 8 | Untracked experiment trees (`96/`, `spectral tool/`, `Cellular demos/`, `archive/`, `galaxy/`, `schism*`) | DECIDE: track/archive/delete | none in git either way |
| 9 | `V22` symlink to external project | DECIDE (remove symlink) | none |
| 10 | `core/jit_x86.py` | DECIDE → likely DELETE | none (zero importers) |
| 11 | `core/nodegraph.py` | DECIDE → likely DELETE or archive | README line only |
| 12 | `core/lsp_server.py` + `ergo-extension/` | DECIDE: fix-and-verify or drop | extension only |
| 13 | `android/` + `android-app/` + vk_host.c Android branches | DECIDE: revive or strip | vk_host.c #ifdefs |
| 14 | `structured/` (parked WIP) | DECIDE: resume, archive, or delete | its own BUILD.md refs |
| 15 | `core/backends/nvvm.py` | DECIDE: keep loud-stub or DELETE + driver/`__main__` touch-up | driver target list, help text |
| 16 | `tests/` corpus audit (203 files, no CI) | DECIDE after audit run | unknown until audited |
| 17 | `core/codegen.py` legacy backend + `use_ir` + golden harness | DECIDE (keep through 1.0?) — highest coupling | run_golden.py, driver API, spec |

**Load-bearing but ancient (do not delete casually):** `core/archive/changes.md`
(cited history), `Testing/V22` sources (allocator audit cross-reference),
`allocator/sq2core.f` (F77 validation reference), `core/runtime/ergo_net.h`
(consensus transport), `core/runtime/render_shaders.h` (checked-in generated
file the `--render` build depends on).

**Undecidable from the repo (user input needed):** whether dual-path golden
testing survives to 1.0 (#17); whether LSP/node-graph/android/JIT-native are
1.0 scope (#9/#11/#12/#13); whether `structured/` is alive (#14).

---

## Decisions recorded (2026-08)

### Nodegraph (catalog #11 / §4) — KEPT, completed to Phase A

User ruling: the node graph is an essential production feature, not a
deletion candidate. Completed to a working, gated state:

- `core/nodegraph.py` now round-trips the design-doc JSON schema
  (top-level `inputs`/`outputs`, `input:`/`output:`/`param:` edge refs,
  input `"value"` defaults), handles `param:` pseudo-node refs in
  validation/topo/codegen, and initializes standalone-target inputs.
- CLI route: `python -m core <graph>.json [-o bin]` (plus `--emit-ergo`
  for the readable-source target) — the zero-importer orphan now has a
  production entry point.
- Golden suite: `tests/nodegraph/run_nodegraph.py` (11/11) — two
  end-to-end graphs verified against analytic values (Nernst potential,
  switch pipeline), six validation negatives, determinism +
  round-trip checks; wired into `run_golden.py`.
- Remaining roadmap (subgraph nodes, array pins, Select, tick mode,
  Nuklear phases B–D, source→graph) is documented in
  `Spec/Ergo_NodeGraph_Design.md` "Implementation Status".

### NVVM (catalog #15 / §5) — keep-stub now, delete at 1.0

**Is it needed for anything? No.** Every GPU feature since 2026-05 is
SPIRV-only: staged/segmented reductions, ATAN2, HASH/RAND (int64 ALU),
tiled dispatch, ping-pong buffers, clipmaps, the F104 2D stencils. The
SPIRV path runs on NVIDIA hardware via Vulkan (verified on the RTX 2060
here), so NVVM's only distinct value would be a CUDA-only deployment
(no Vulkan loader) — no such requirement exists. Making NVVM viable
means re-doing the SPIRV backend's correctness work against its
docstring's own broken catalog (.approx intrinsics without correction,
SCATTER without atomics, invalid IR for integer arrays/mixed
arithmetic, missing phi nodes) — a 634-line stub vs spirv.py's 3,547
audited lines. Not worth it.

**Does musl change the calculus? No — it reinforces the verdict.** musl
builds concern the host side (static/small libc for the generated C +
gcc link; the Ergo C runtime is already near-libc-free — stdio/math/
stdlib only, so a musl static build of CPU-only programs is close to
trivial). The GPU constraint under musl is the *Vulkan loader and
proprietary driver stack*, which is libc-sensitive — not the choice of
kernel IR. NVVM would make musl strictly worse: libNVVM and the CUDA
driver are glibc-centric binary dependencies. If small static builds
become a goal, the path is CPU-only-musl today and possibly
SPIRV-via-fossilize/lavapipe later — never NVVM.

**Verdict:** keep the loud stub through 1.0 (zero cost, documents the
dead end); DELETE at 1.0 unless a CUDA-only deployment requirement
materializes, and then drop "nvvm" from `driver.py`'s target list and
the `__main__.py` help texts in the same commit.

### Android (catalog #13) — revival sketch (glance only)

Current state: `android/build_android.sh` was un-broken in the cleanup
batch (now invokes `python -m core --target spirv --precision f32`);
`vk_host.c` still carries its `ERGO_VK_ANDROID` guards (26 sites:
includes, `ANativeWindow`, log redirection, render deferred). Neither
is verified — that needs the NDK, which this box may not even have
installed. Revival cost estimate: (1) confirm the NDK and run
`build_android.sh` once — the likely rot points are the vk_host.c
ifdef sites (they've been carried through months of vk_host.c edits
without a compile check) and the Gradle config in `android-app/`;
(2) runtime verification needs an emulator image with Vulkan
(SwiftShader) or a physical device — the sim is headless-capable, so a
plain instrumentation run (`SimActivity` → logcat) suffices for a
smoke test; (3) expect half a day of guard fixes, not a redesign.
Recommendation: leave parked until an actual Android deployment need
exists; the pieces are coherent enough that revival is a verification
job, not archaeology.
