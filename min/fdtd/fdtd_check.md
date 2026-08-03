# FDTD 2D wave-optics in Ergo — validation report

Programs: `min/fdtd/fdtd_slit.ergo` (double slit, 3 lambdas, Gaussian
pulse source T0=200/TW=60, barrier ix=300 with slits [219,230] and
[283,294] (sep d=64, width a=12, centered y=256), screen ix=560,
intensity accumulated during packet transit T=900..1800) and
`min/fdtd/fdtd_sw.ergo` (standing wave, continuous line source ix=40,
hard mirror PASS=0 at ix=580, RMS of |U| at row 256 averaged over the
last 500 steps). Both: C2 = 0.25 (Courant 0.5 < 1/√2 ✓ stable), grid
640×512, sponge = 40 cells per edge with cosine ramp to 0.5 (edge
reflections killed; barrier and mirror kept out of the sponge per the
gotcha).

## Oracle table

| experiment | measured | oracle | delta | verdict |
|---|---|---|---|---|
| double slit, λ=12 | 53.88 cells | 48.75 | 10.5% | FAIL with explanation (below) |
| double slit, λ=16 | 65.50 cells | 65.00 | 0.8% | PASS |
| double slit, λ=20 | 85.00 cells | 81.25 | 4.6% | PASS |
| multi-λ ratio | 12 : 14.6 : 18.9 | 12 : 16 : 20 | — | fails via λ=12 (same cause) |
| standing wave | 7.91 cells | 8.0 (λ/2) | 1.1% (tol 1 cell) | PASS |

**The λ=12 deviation is real physics, not a sim/extraction error.** The
far-field formula Δy = λL/d applies when d²/λL ≪ 1; at λ=12, d²/λL =
4096/(12×260) = 1.31 — squarely in the Fresnel regime. The profile's
spatial spectrum is a single clean peak at 1/53.9 (no contamination),
i.e. the fringes are regular, just ~11% wider than the far-field
asymptote — the expected Fresnel broadening. Extraction was done three
ways (peak positions, FFT of detrended oscillation, autocorrelation);
the peak-position method is the most robust and is what the table uses.

Physics debugging journey (worth recording): the first continuous-source
runs produced a reverb chamber of grid-scale noise that poisoned naive
extraction. Fixes that mattered: (1) Gaussian pulse source instead of
continuous drive (kills continuous noise injection; the packet transits
the screen before reflections return), (2) stronger wider sponge
(20→40 cells, 0.7→0.5 edge), (3) time-averaging the SW field over the
last 500 steps instead of an instantaneous snapshot (nodes hold still,
the envelope noise averages out), (4) moving the SW mirror out of the
sponge (600→580) per the barrier-in-sponge gotcha.

## CPU vs GPU (RTX 2060, SPIR-V, f64)

| program | CPU wall | GPU wall | result agreement |
|---|---|---|---|
| fdtd_slit | 1.667 s | 65.0 s | extraction-identical (53.88/65.50/85.00 both); per-cell deltas 2e-4–8e-4 relative (GPU reduction-order FP noise in the PROF accumulation) |
| fdtd_sw | 1.072 s | 42.6 s | **bitwise identical (delta 0.0)** |

The GPU LOSES 39–40× on this workload: per step it launches ~5 kernels
(stencil, source, screen accumulation, two rotate copies) over
640×512×8 B = 2.6 MB fields, and the rotate copies force full-array
upload/download transfers every step (~10–20 GB moved per run) — the
transfer-flood problem documented in the stage-4 GPU work. The kernels
extract correctly (INJECTIVE stencil, see below); the loss is launches +
transfers, not compute.

**GPU codegen bug found and worked around:** the SPIR-V host codegen
emits `UN[_linK0_2] = 0.0` (1D syntax on the 2D array `double
UN[512][640]` — pointer, not double) for host-linearized nested loops,
failing to compile. The slit dodged it because its init (inside the
scene loop) extracted as a device kernel; the sw init (top-level) hit
the host path. Workaround: wrap the init in a dummy outer loop
(`DO DMY = 1, 1`), matching the slit's structure — compiles and runs
correctly.

## Kernel report summary

- slit: 5 extractable kernels, 13 rejected (2 with "too few iterations
  (12)" — the slit-window open loops, correctly CPU).
- sw: 6 extractable kernels, 15 rejected (nested-loop dependencies as
  expected in init/sponge/source sections).

## Files

`fdtd_slit.ergo`, `fdtd_sw.ergo`, CPU + GPU binaries, `slit.out`,
`slit_gpu.out`, `sw.out`, `sw_gpu.out`, `analyze_fdtd.py`,
`fdtd_dump.ergo`/`dump.out` (field dump used in debugging), this file.
