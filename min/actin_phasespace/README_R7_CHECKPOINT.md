# R7 Checkpoint Archive — Actin Phase-Space Project (Filamin-like Crosslinking)

## What R7 certified

R7 certified a transient slip-bond (filamin-like) crosslink channel in the
phi4 brush engine (`brush_xlk.ergo`, derived from the certified R6 parent
`brush_adh.ergo`). All six R7 objectives passed (O-X1..O-X6 PASS): PXL=0 is
byte-identical to the certified parent in both O-X1 gate arms; the channel
shows continuous formation/rupture with exact inventory and zero net-force
bookkeeping (O-X2/O-X5); the pooled Bell slip law is certified at
beta = 0.995310 +/- 0.002709 (nominal 1/FBX = 1.0, 47.1M exposures,
load-invariant across arms) (O-X6); and cohesion without freezing is
certified as a contractile internal-tension mechanism — links are born
compressed, live stretched, rupture overstretched, pull the top layer down
(73-76%), and causally inhibit growth (O-X3a mechanism gate PASS) — with
measurable brush shortening at force balance: O-X3b 10-seed pooled
mean dx95 = -0.3823, one-sided p = 0.0043 (Wilcoxon p = 0.0098), plus the
registered finding that cohesion attenuates as external load dominates at
F_EXT = 4 (F4 attenuation finding). The R7-f integration diagnostics showed
inter-channel interactions are architecture-dependent: crosslinks recover
branched-mesh adhesion occupancy (+30%) in the branched-only mesh but
suppress it (-40%) in the formin hybrid, and the diagnostic flag that the
link pool pins at the MAXXL=24 cap for 7-14 consecutive windows in dense
branched meshes (pool-limited, not kinetics-limited) is registered as a
non-gating note for R8+ pool re-registration. The final engine SHA256 is
a3ed43347392aa97f7ad2bde5ad0d7c1ce0e09e244220cedba59edc7ea46944a (verified
before archiving, and re-verifiable from inside the zip).

## Directory layout of the archive

- `README_R7_CHECKPOINT.md` — this file.
- `SHA256SUMS_R7.txt` — sha256 of every payload file (see "Manifest" below).
- `plan.md` — top-level session plan (stored at the zip root).
- `phi4/brush_xlk.ergo` — final R7 crosslink engine (hash verified, above).
- `phi4/brush_adh.ergo` — R6 parent engine (O-X1 reference).
- `phi4/brush_bfm.ergo` — R5 grandparent engine (lineage anchor).
- `phi4/plan_crosslink.md` — R7 crosslink plan/oracle (O-X1..O-X6 +
  registered amendments X-1..X-6).
- `phi4/CROSSLINK_LAW.md` — certified crosslink/cohesion law document.
- `phi4/ANALYTICS.md` — analytics writeup.
- `phi4/ADHESION_LAW.md` — certified R6 adhesion slip-law document
  (referenced by the R7-f diagnostics).
- `phi4/runs21/` — complete R7 run tree (44 runs, 1M steps each: 2 smokes +
  6-run XLNF=1 law grid + 34 cohesion/release/ensemble runs + 2 integration
  diagnostics), with `__pycache__` excluded by design:
  - `gates/` — O-X1 gate artifacts (parent/child pairs, .status, variants).
  - `smokes/` — R7-c paired ON/OFF brush smoke logs + analysis.
  - `law_grid/` — R7-d XLNF=1 per-step-force grid (~4.6 GB logs) +
    `law_grid_analysis.txt` (pooled slip-law ML fit).
  - `cohesion/` — R7-e arms: F2/F4 paired seeds, release pair, O-X3b seed
    ensemble, OX3_INVESTIGATION.md, OX3A_CERTIFICATION.txt,
    OX3B_RESCORE.txt / OX3B_RESCORE_10SEED.txt, OX4_RESCORE.txt, arm
    analyses; 30+ logs with .status/.variant.ergo sidecars.
  - `integration/` — R7-f architecture-dependent adhesion diagnostics.
  - `static_cert_candidate/` — R7-a static/FD certification run.
  - `verify_r7a/` — independent R7-a verification artifacts.
  - `superseded/` — superseded artifacts kept for provenance (incl. the
    stale NaN law-grid analysis).
  - `stage_h_analysis.py` — smoke/pair/integration per-log analyzer.
  - `stage_h_law_analysis.py` — R7-d law-grid analyzer (O-X2..O-X6).
  - `ox3a_certification.py` — O-X3a contractile-mechanism gate script.
  - `SELFTEST_H.md` — analyzer self-test certification.

## Git bundle (absent by fact)

No `r7_repo.bundle` is included: `/mnt/agents/output/actin_phasespace/
r6_workspace/repo` currently exists only as a working tree (no `.git`
directory), so there is no repository to bundle. The R6+R7 commit history
referenced by the docs (merges `615c8ae`, `7ff0566`, ...) is preserved in
the R6 checkpoint archive (`actin_phasespace_r6_adhesion_checkpoint.zip` ->
`r6_repo.bundle`, verifiable with `git bundle verify`).

## Manifest

`SHA256SUMS_R7.txt` lists the sha256 of every file in the archive payload,
computed before zipping, with paths relative to the zip root. By design it
excludes itself and any git bundle (a bundle is self-verifying via
`git bundle verify`); no bundle is present in this archive (see above).
All other entries, including this README, are covered.

## Restoration / reproduction notes

1. Unpack: `unzip actin_phasespace_r7_crosslink_checkpoint.zip`
2. Verify payload integrity: `sha256sum -c SHA256SUMS_R7.txt` (run from the
   unpacked root; the manifest itself is not listed).
3. Verify the engine source hash: `sha256sum phi4/brush_xlk.ergo` must equal
   `a3ed43347392aa97f7ad2bde5ad0d7c1ce0e09e244220cedba59edc7ea46944a`.
   Without unpacking, `unzip -p <zip> phi4/brush_xlk.ergo | sha256sum`
   gives the same value.
4. Toolchain: the certified Ergo compiler lives at
   `/mnt/agents/output/actin_swarm/toolchain/ergo_mcl`.
   Compile an engine from that directory with:
   `python3 -m core <path>/brush_xlk.ergo -o <bin>`
5. Reproduction entry points (see also the "Reproduction" section of
   `phi4/CROSSLINK_LAW.md`):
   - Runner: `sh runs20/runner_r6.sh <bin> runs21/<dest>.log` (the
     wipe-immune batch runner — /tmp stream, verify, cp, re-verify, writes
     `.status`; it is preserved in the R6 checkpoint archive at
     `phi4/runs20/runner_r6.sh`, as `runs20/` is not part of this R7
     archive).
   - Smoke / cohesion-pair / integration per-log analysis:
     `python3 phi4/runs21/stage_h_analysis.py <logs...>
       --expected-steps 1000000 --burn-in 500000 --out <out>.txt`
   - Law-grid analysis (O-X2/O-X4/O-X5 + pooled O-X6 slip-law ML fit):
     `python3 phi4/runs21/stage_h_law_analysis.py
       NAME=FEXT=SEED=PATH [...] --burn-in 500000 --expected-steps 1000000
       --out <out>.txt` (exact certified invocation in CROSSLINK_LAW.md).
   - O-X3a contractile-mechanism gate (existing logs):
     `python3 phi4/runs21/ox3a_certification.py --out <out>.txt`
6. Registered R8+ note: the link pool pins at MAXXL=24 in dense branched
   meshes (pool-limited); bundle-polarity (R8) design must re-register pool
   size and account for the architecture-dependent substrate-interface
   interaction found in R7-f.
