# R6 Checkpoint Archive — Actin Phase-Space Project (Substrate Adhesion)

## What R6 certified

R6 certified the substrate-adhesion channel of the phi4 brush engine
(`brush_adh.ergo`, derived from the R5 parent `brush_bfm.ergo`). All five R6
objectives passed (O-A1..O-A5 PASS): the calibrated adhesion slip law is
beta = 0.995474 +/- 0.001413; the adhesion traction-closure residual is
<= 5.8e-07 across the certification grid; the release-grid stall bracket was
measured at 4 < F* < 8; and the R6-f branched-mesh interference was recorded
as a known limitation (documented in `phi4/ADHESION_LAW.md` and the repo's
`R6_NOTES.md`). The final engine SHA256 is
f709fb4453a1c6c6405ca33f9600844253ee7e35296acdb208f8d79bbf7075b8 (verified
before archiving).

## Directory layout of the archive

- `README_R6_CHECKPOINT.md` — this file.
- `SHA256SUMS_R6.txt` — sha256 of every payload file (see "Manifest" below).
- `plan.md` — top-level session plan (stored at the zip root).
- `r6_repo.bundle` — git bundle of the full `r6_workspace/repo` history
  (`git bundle create --all`). Restore with
  `git clone r6_repo.bundle repo`.
- `R6_NOTES.md` — repo-root R6 notes (copy from `r6_workspace/repo` HEAD).
- `phi4/brush_adh.ergo` — final R6 adhesion engine (hash verified, see above).
- `phi4/brush_bfm.ergo` — R5 parent engine (O-A1 reference).
- `phi4/plan_adhesion.md` — R6 adhesion plan.
- `phi4/ADHESION_LAW.md` — certified adhesion slip-law document.
- `phi4/ANALYTICS.md` — R6 analytics writeup.
- `phi4/runs20/` — complete R6 run tree (172 payload files, ~2.4 GB), with
  `__pycache__` directories excluded:
  - `gates/` — objective gate results (O-A1..O-A5).
  - `smokes/` — smoke-test runs and logs.
  - `law_grid/` — slip-law calibration grid, including `superseded_*` dirs.
  - `release_grid/` — release-force grid (stall bracket runs).
  - `integration/` — integration / traction-closure runs.
  - `static_cert_candidate/` — static-certification candidate run.
  - `selftest_padhf/` — PADHF per-step adhesion-force self-test.
  - `superseded/` — superseded runs kept for provenance.
  - `runner_r6.sh` — R6 batch runner.
  - `stage_g_analysis.py`, `stage_g_law_analysis.py` — analyzer scripts.
  - assorted `.status` / `.txt` / `.variant.ergo` files and run logs.

## Manifest

`SHA256SUMS_R6.txt` lists the sha256 of every file in the archive payload,
computed before zipping. By design it excludes `r6_repo.bundle` (the git
bundle is itself a content-addressed, self-verifying object — check it with
`git bundle verify`) and the manifest itself. All other entries, including
this README, are covered.

## Restoration / reproduction notes

1. Unpack: `unzip actin_phasespace_r6_adhesion_checkpoint.zip`
2. Verify payload integrity: `sha256sum -c SHA256SUMS_R6.txt` (run from the
   unpacked root; the bundle and the manifest will not be listed).
3. Restore the engine repo: `git clone r6_repo.bundle repo`
   (then `git bundle verify r6_repo.bundle` to confirm completeness).
4. Verify the engine binary-source hash:
   `sha256sum phi4/brush_adh.ergo` must equal
   `f709fb4453a1c6c6405ca33f9600844253ee7e35296acdb208f8d79bbf7075b8`.
5. Toolchain: the ergo_mcl toolchain lives at
   `/mnt/agents/output/actin_swarm/toolchain/ergo_mcl`.
   Compile an engine from that directory with:
   `python3 -m core brush_adh.ergo -o <bin>`
6. Reproduction entry points:
   - Runner: `phi4/runs20/runner_r6.sh` (batch driver used for the R6 grids;
     edit output paths before re-running).
   - Analyzers: `python3 phi4/runs20/stage_g_analysis.py` and
     `python3 phi4/runs20/stage_g_law_analysis.py` (see `--help` in each
     script and `phi4/ANALYTICS.md` for the invocation patterns used to
     produce the certified numbers).
7. Known limitation: R6-f branched-mesh interference — see
   `phi4/ADHESION_LAW.md` and `R6_NOTES.md` before extending the model to
   branched geometries.
