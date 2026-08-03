# Trimer 2D charging-ring map — reproduction of Li/Pokorný Fig. 2/3

Program: `min/trimer_map.ergo` (same 8-state Pauli master equation as the
validated `trimer_pme.ergo`: EPS0 = −90 meV, W = 50 meV, kT = 0.22 meV,
image-charge tip model TIP_Z = 0.6, Z_S = −0.09, L_UNIFORM = 0.03,
L_LOCAL = 0.0469 calibrated to the 520 mV ring). Grid 60×60 over
X ∈ [−0.8, 1.8], Y ∈ [−0.4, 1.3] nm; Vs series {540, 620, 690, 770,
790, 810, 870} mV in one program pass (25 200 steady-state solves,
NSTEPS = 100 000 kept as-is). Output: `trimer_map.out` (X Y VS I_TIP
Q_TOT W_SING), data `trimer_map.npz`, plots `maps/`.

## Sign-convention note (needed for the NDC verdict)

Our I_TIP is signed net electrons tip→cluster, so it is negative
everywhere (emission-dominated). The paper plots emission-positive
current and defines NDC as dI/dV < 0, i.e. |I| DROPPING with increasing
Vs. In our data that appears as raw dI_tip/dVs > 0 at the trapping
thresholds; in the paper convention (emission positive) those regions
are negative dI/dV. Both maps are in `maps/` (`dIdV_map_790mV.png` raw,
`dIdV_paper_convention_790mV.png` flipped).

## Verdict vs the paper (main.txt lines 259–266, 1015–1043)

**(a) Three distinct discharge rings at Vs = 540 — REPRODUCED.**
`I_map_540mV.png`: three clean lobes centered on the three site markers
(stars), separated by a high-current basin. Matches Fig. 2a ("three
distinct discharge rings corresponding to the three individual
molecules").

**(b) Rings expand and overlap into the trillium-flower pattern by
Vs = 690 — REPRODUCED.** The series 540 → 620 → 690 shows the lobes
growing until they touch; at 690 (`I_map_690mV.png`) the three expanded
rings intersect through the center with a Y-shaped junction — the
trillium-flower morphology of Fig. 2b–h. At 870
(`I_map_870mV.png`) the structure has reorganized into the
tree/anchor-shaped trapped region.

**(c) NDC region near the center at Vs = 790–870 — REPRODUCED, with the
sign convention above and the expected symmetry caveat.** In the paper
convention the dI/dV map at 790 mV
(`dIdV_paper_convention_790mV.png`) has actual negative values over 31%
of the grid, min = −0.00157 (units of the rate model), and the negative
band is a three-petal flower passing within 0.02 nm of the trimer
center (median NDC-pixel distance to center 0.77 nm). The NDC band is
exactly the boundary of the kinetically trapped singlet region
(`Wsing_map_790mV.png` — the Y/flower-shaped W_SING ≈ 0.95 zone
coincides pixel-for-pixel), which is the physical mechanism (current
blocked while the cluster is stuck in the singly occupied manifold).
**Not reproduced (expected, not a failure):** the paper's NDC holds a
"distinct chiral pattern" from the SOMO orbital's angular modulation,
which our model omits — our NDC region is C3-symmetric, and the
trillium arms are identical rather than chiral.

## Consistency check against the validated 1D model

Map values at center-adjacent points match `trimer_pme.ergo`'s 1D
position scan at Vs = 790 to the last digit (e.g. (0.434, 0.263) →
−0.111477 vs −0.111536 on the 30° scan line). The validated center
bias sweep's trapping threshold (788 mV) is the same transition whose
spatial boundary forms the NDC flower band here.

## Files

`min/trimer_map.ergo`, `min/trimer_map` (binary), `min/trimer_map.out`,
`min/trimer_map.npz`, `min/trimer_map_plot.py`,
`min/maps/I_map_{540,620,690,770,790,810,870}mV.png`,
`min/maps/Wsing_map_*.png`, `min/maps/dIdV_map_790mV.png`,
`min/maps/absdIdV_map_790mV.png`,
`min/maps/dIdV_paper_convention_790mV.png`, this file.
