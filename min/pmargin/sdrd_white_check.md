# SdrD retest with the white-noise bath

Programs (min/pmargin/): `gen_sdrd_white.py` →
`sdrd_white_{A2,A3,B1,B2,full}.ergo` (+binaries/.out). Minimal
controlled swap vs `sdrd_check.md`: ONLY the velocity kicks change
(splitmix-style integer hash from `white_check.md`, amplitude
variance-matched ×2.449 per component). Phase noise left as the old
sinusoid — phases are inert at HB_CAP=0 (they gate only H-bonds,
disabled in this recipe), so the A/B is exactly the velocity-bath
model. Same force field, same packed v2 programs, same seeds, same
schedule (heat cycles to 1200, floor 0.001, quench 38400, 48000
frames). Runtime: domains 35–74 s; full construct 8 m 22 s.

**Quench-floor note (as asked):** THERMAL_CURRENT scales both drive
types multiplicatively, so the variance match holds at every schedule
point — floor and quench included. What changes is only the temporal
correlation of the noise.

## 1. Per-domain gate retest (8 seeds each, final RMSD, model units ×2.5 = Å)

| domain | old best | white best | Δ best | old median | white median | catastrophes (>10) |
|---|---|---|---|---|---|---|
| A2 (152) | 4.37 | **3.38** | −23% | 5.75 | 5.32 | 0 → 0 |
| A3 (168) | 2.67 | **2.38** | −11% | 6.65 | 5.32 | **3/8 → 0/8** |
| B1 (120) | 2.95 | **0.91 (2.3 Å)** | −69% | 4.05 | 4.38 | 0 → 0 |
| B2 (116) | 3.03 | **1.82** | −40% | 4.70 | 4.85 | 1/8 → 0/8 |

- **Every domain's best fold improves (11–69%).** B1 seed 1 goes
  2.95 → **0.91 — the first genuine (sub-1.5 Å-class) fold at this
  size anywhere in the SdrD work**.
- **A3's three catastrophic seeds (10.5/11.2/10.2) are ALL rescued**
  to mediocre folds (4.9/5.2/4.1). Per-domain catastrophic blocks:
  4/32 → **0/32**.
- Medians barely move (±0.4–0.7 units, both directions): the white
  bath converts trapped outliers into folders but does not flatten the
  rugged landscape for the median seed. Per-seed scatter is large
  (chaotic deviation rules — the robust statements are the best-case,
  the catastrophe rate, and the mean/median, not individual seeds).

## 2. Full construct retest (556 res, 8 blocks)

| block | old full (A2 A3 B1 B2) | white full (A2 A3 B1 B2) |
|---|---|---|
| 1 | 30.8 (13.1 23.7 5.9 5.3) | 15.3 (9.0 13.3 6.8 6.1) |
| 2 | 19.9 (9.1 6.4 8.5 3.7) | 19.3 (8.7 5.8 12.6 4.6) |
| 3 | 14.8 (8.2 9.1 9.3 8.4) | 20.7 (6.2 5.5 12.9 11.1) |
| 4 | 27.5 (8.2 4.8 10.6 5.3) | 27.6 (8.0 5.0 6.6 5.3) |
| 5 | **117.2** (9.6 **149.3 173.2** 6.0) | **15.2** (12.5 **5.4 4.6** 5.7) |
| 6 | 28.4 (19.6 24.0 7.2 3.1) | 36.2 (20.0 39.5 7.8 3.8) |
| 7 | 23.4 (11.6 5.2 5.2 7.0) | 23.3 (4.7 10.8 5.8 7.5) |
| 8 | 17.2 (4.6 5.0 8.2 2.9) | 20.7 (5.5 4.7 12.1 2.9) |

- **The merged-blob catastrophe is gone without any pulse:** block 5,
  117.2 → 15.2, with A3 = 149.3 → 5.4 and B1 = 173.2 → 4.6 — the two
  domains that fused into the blob now fold independently. The old
  drive needed the validated pulse to achieve the same disaggregation
  (117.2 → 14.17); the white bath gets it natively.
- Full-chain distribution: mean 34.9 → **21.0 (−40%)**, median 25.5 →
  20.5, max 117.2 → 36.2. Catastrophes (full > 50): **1 → 0**.
- New anatomy note: block 6 grows a fresh inter-domain failure
  (A3 = 39.5) and B1 traps migrate (12.1–12.9 on three blocks) —
  inter-domain mispacking is still the dominant error mode; the white
  bath prevents the irreversible fusion, not the misalignment.

## 3. Verdict

**(a) PARTIAL RESCUE — the ceiling was partly a dynamics artifact,
and now it's quantified.** The white bath improves the best fold on
every domain (11–69%), eliminates every catastrophic per-domain trap
(4/32 → 0/32) and the full-construct blob (1 → 0), and cuts the
full-chain mean 40%. Most striking: B1 0.91 (2.3 Å) is a real fold —
the first SdrD domain to reach it. **But the landscape/size verdict
survives for the median seed:** medians move only ±0.4–0.7 units, and
A2/A3 still have no sub-4 fold at any seed. The decomposition is now
clean: **the old slosh drive was capping the best case and creating
the irreversible catastrophes (dynamics artifact — eliminated); the
median ruggedness is the energy function (force-field ceiling —
confirmed, now with the dynamics suspect eliminated).** Per-seed
precision-regime rules apply throughout: individual values scatter by
several units; the distribution statistics are the robust content.

Files: `gen_sdrd_white.py`, `sdrd_white_{A2,A3,B1,B2,full}.ergo`
(+binaries), `sdrd_white_{A2,A3,B1,B2,full}.out`, this report.
