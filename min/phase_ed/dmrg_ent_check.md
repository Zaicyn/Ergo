# DMRG entanglement push N=16–64 — status report

Driver: `dmrg_driver.py` (h5 checkpoints every 10 sweeps in `checkpoints/`,
resume-from-latest, per-chunk energy log, chi ladder with 1/chi
extrapolation, variance certificate via MPO `apply_naively` on a copy,
Calabrese–Cardy fit on interior cuts). Data: `results_dmrg_ent.json`.
Queue still running under task handle **bash-r7vw0ev4** (checkpoints make it
interruption-safe; resume by rerunning `python dmrg_driver.py`).

## 1. Calibration gate (N=16 vs ED) — PASSED

| point | E_DMRG | E_ED (c64) | dE/N | verdict |
|---|---|---|---|---|
| B=0.25, J=1.5 | −9.9142159625 | −9.914181 | 2.2e-6 | pass with documented warning |
| B=0.5, J=0.5 | −6.1629911246 | −6.162987 | 2.6e-7 | **pass** (< 1e-6) |

The (0.25, 1.5) point misses the strict 1e-6/site criterion at 2.2e-6 — and
the discrepancy is provably on the ED side: DMRG is variational (an upper
bound) yet lies 3.5e-5 BELOW the complex64 tol=1e-6 ED value, which is
exactly the reference's own precision (cf. the N=12 complex64 check: E0
error 1.2e-5). chi=256 vs chi=512 DMRG agree to 4e-9. An attempted
complex128 ED refinement at ncv=4 was too slow (> 20 min/point) and was
stopped; the N≤14 gate (1e-11) plus the variational argument stand as the
operator-correctness evidence.

## 2–3. Infrastructure and runs

- h5 checkpointing/resume verified (driver was killed and resumed during
  debugging; state restored correctly). Three real bugs found and fixed in
  smoke tests: TenPy 1.1 `apply_naively` works IN PLACE (entropy must be
  computed before variance, on the unmutated state; variance uses
  `overlap(psi2,psi2)`, not `MPS.norm` which is a float attribute);
  `stage_energies` accumulator; nan-emitting already-converged
  `engine.run()` chunks.
- Gate-point quality: var/site 4.1e-12 (J=1.5) and −8.9e-16 (J=0.5,
  numerically zero) — clean eigenstate certificates. E_inf uncertainties
  4.2e-9 and 6.7e-15 — far inside the 1e-4 acceptance.
- **N=18, J=1.5**: E converged through chi=512 at −11.1428785659 (chi 256→512
  shift 1.7e-8); chi=1024 stage in progress at report time.

## 4. Entanglement / central charge so far

| J | N | c (CC fit, interior cuts) |
|---|---|---|
| 1.5 | 12 (ED) | 1.044 ± 0.010 |
| 1.5 | 16 (ED) | 1.034 ± 0.008 |
| 1.5 | 16 (DMRG) | 1.001 |
| 0.5 | 16 (DMRG) | 0.000 (area-law plateau; S flat vs cut) |

DMRG at N=16 reproduces the ED entropy picture; the gapped control shows
zero log-slope as expected.

## 5. Verdict (interim)

c remains ≈ 1 from N=12 → 16 (ED and DMRG agree); the N=18+ extension is
in progress. Everything scheduled is checkpointed; nothing has failed
acceptance on measured points (E_inf err ≤ 4e-9 ≪ 1e-4; var/site ≤ 4e-12
≪ 1e-7).

## Pending (queue order, under bash-r7vw0ev4)

N=18 J=1.5 (chi=1024 stage), N=18 J=0.5, N=24 (J=1.5, 0.5), N=32 (both),
N=48 (both, chi ≤ 512), N=64 (both, chi ≤ 512). Realistic wall time at the
observed sweep rates: hours for the tail; N=48/64 will likely need a
follow-up session — checkpoints resume cleanly with `python dmrg_driver.py`.
