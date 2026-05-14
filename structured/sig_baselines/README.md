# Crystal-lane signature baselines

Captured 2026-05-14, pre-V22-port Ergo at experimental crystallization
threshold = 0.048 (above the OMEGA equilibrium plateau of 0.0367).

## Why threshold 0.048 not 0.008

The shipping `OMEGA_CRYSTAL_THRESH = 0.008` is **below** the COAST-mode
equilibrium ω plateau. With current dynamics, no particle ever reaches
ω < 0.008, so crystals don't form and the SIG_* buffer stays empty.
Threshold 0.048 is *above* the plateau, so any COAST particle that also
satisfies `v² < 0.01` (drifts to large r where orbital speed is low)
crystallizes.

Restore to 0.008 in `constants.ergo` after these baselines are captured.

## Reproducibility

```
# Set OMEGA_CRYSTAL_THRESH = 0.048 in structured/constants.ergo
./structured/build_sig.sh
python -m mcl --target spirv --precision f32 --no-split -M 1000000 -N 500000 \
    -o galaxy_sig_500k galaxy_sig.ergo
./galaxy_sig_500k > N500K_F200K_thresh048.log

# Cluster:
cat N500K_F200K_thresh048.log | python3 structured/cluster_sigs.py --k 2
```

## Findings

### N=500K, 200K frames: 19 crystals

K-means k=2:
- Cluster A (4 particles, 21%): r≈676, ρ≈0.0625, mgate≈0.36 — **DENSE_INNER**
- Cluster B (15 particles, 79%): r≈830, ρ≈0.0, mgate≈0.20 — **HALO_DUST**

### N=1M, 200K frames: 37 crystals

K-means k=2:
- Cluster A (6 particles, 16%): r≈438, ρ≈0.31, mgate≈0.31 — **DENSE_INNER**
- Cluster B (31 particles, 84%): r≈842, ρ≈0.02, mgate≈0.28 — **HALO_DUST**

K-means elbow scan: smooth decrease in inertia from k=2 (96.4) to k=8
(11.1). No clear elbow, suggesting the data is fundamentally 2-class
with within-cluster variance contributed mostly by spatial scatter.

## Invariant signature fields (no variance across all 56 crystals)

These fields are **constant** at the moment of crystallization regardless
of where or how the particle dies:

| Field | Value | Interpretation |
|---|---|---|
| ω | 0.0367 | COAST-mode plateau, the only state that allows crystallization |
| fmode | 0 | All crystallizing particles are in COAST (FLOW_MODE[GEN]=0) |
| vmag | 0.1000 | Exact threshold value — particles cross v²=0.01 at this speed |
| zc | 1.0 | All in GEN bins with Z_COUPLING[GEN]=1.0 |
| fw | 0.0 | All in GEN bins with FLOW_W[GEN]=0.0 |

## Validation of GPT's framing

The data confirms three of GPT's predictions:

1. **"All particles that crystallize do so the same way"** — every signature
   has identical ω, fmode, vmag, zc, fw values. Only spatial location (r)
   and local density (ρ, mgate) vary. The substrate produces **one death
   pathway**, not a diversity of them.

2. **"The substrate is still flat"** — global decay constant produces
   single-mechanism crystallization. Two clusters emerge purely from
   spatial position relative to the disk, not from internal particle
   state.

3. **Reproduces the April 30 baseline** documented in
   [Spec/Material_Future_Directions.md](../../Spec/Material_Future_Directions.md):
   "All other signature fields identical at death (OMEGA≈0.037, V≈0.1,
   FMODE=0). Ring coupling has no effect on crystallization signatures
   at equilibrium." Same 2-class result. Class population fractions
   differ slightly (April 30: 33%/67%, ours: 16-21%/79-84%) due to
   smaller sample size.

## Implications for the V22 port

Post-port (trajectory-centric topology + sections 1, 9.5, 4 of the
spec), expect richer signatures because:

- Particles cycle through ACTIVE/FLOW bins → fmode varies at death.
- Density coupling drives ω in ACTIVE/FLOW → ω at death varies.
- Different gen bins → different zc, fw at death.
- Mode-gating correctness → different deceleration mechanisms → vmag
  at death varies.

If the post-port re-cluster still shows only 2 classes by spatial
position, the substrate genuinely doesn't produce material diversity
and Option A/B/C improvements from Material_Future_Directions.md become
priority work. If 4+ clusters emerge, trajectory-centric dynamics alone
is enough.

## Files

- `N500K_F200K_thresh048.log` — 19 signatures at N=500K, **PROGRADE** seed mode
- `N1M_F200K_thresh048.log` — 37 signatures at N=1M, **PROGRADE** seed mode
- `N100K_F200K_thresh048_TANGENT.log` — 954 signatures at N=100K, **TANGENT** seed mode

## Late finding: seed direction is the load-bearing knob

Per V22 assistant's session 2026-05-14 (after their seed-fix was applied in
V22, they noticed the same "crystals stopped forming" symptom in V22's
test results that we saw here). V22 added a runtime toggle between
prograde and tangent-direction seeding. We did the same as a PARAMETER
toggle in `constants.ergo`:

```
PARAMETER INTEGER :: SEED_DIR_PROGRADE = 0
PARAMETER INTEGER :: SEED_DIR_TANGENT  = 1
PARAMETER INTEGER :: SEED_DIR_MODE = 0   ! 0 = prograde, 1 = tangent
```

### Re-test in TANGENT mode

Setting `SEED_DIR_MODE = 1` (Viviani-curve tangent direction as velocity,
the pre-`06cbcc8` Ergo behavior), threshold 0.048, N=100K, 200K frames:

**954 crystallizations** — 25× the prograde rate at 1M / 10× the count
in 1/10 the particle count → **~250× more crystal-productive per
particle**. Matches V22 assistant's cb9a5ba observation of "exponentially
accelerating" crystal counts in tangent mode.

K-means k=4 reveals **4 distinct classes**:

| Class | n | r | ρ | mgate | Interpretation |
|---|---|---|---|---|---|
| MAIN_DISK   | 886 | 736 | 1.0 | 0.36 | bulk stellar death |
| DENSE_INNER | 19  | 57  | 99  | 0.36 | inner density spike |
| CORE_REMNANT | 2 | 11  | 109 | 0.36 | innermost remnant |
| HALO_DUST   | 47  | 1077 | 0.0 | 0.20 | outer halo |

K-means k=6 further resolves MAIN_DISK into MID_DISK (r≈546) and
OUTER_DISK (r≈1080). Inertia continues dropping smoothly, suggesting
the structure is genuinely multi-class, not just 2.

### Implication

The original April 30 measurement was implicitly done in tangent-mode
(pre-`06cbcc8`). The "2 material classes" finding there underrepresents
the substrate's actual class diversity — at N=100K (much smaller than
April 30's 5M) we already see 4 classes in tangent mode. April 30's
2-class result was probably limited by:
- The clustering tool used then may have been less sensitive to small
  high-density clusters (DBSCAN here also only finds 2).
- The threshold and density distributions were different.

The **prograde "loose decay = flat" finding from earlier in this
README is still correct for prograde mode**, but it's not a substrate
property — it's a consequence of the seeding choice. The substrate IS
capable of diverse material production; it just needs particles that
can reach the v² < 0.01 state, and prograde orbits never do.

### Open question for the V22 port

What happens to class diversity once trajectory-centric topology is
wired (V22 sections 1 + 9.5)? Two hypotheses:

1. **Prograde + trajectory-centric** produces 4+ classes because
   ω-driven mode cycling lets particles enter ACTIVE/FLOW regimes,
   accumulate ω, then drift back into COAST and decelerate — creating
   the same v²-low conditions tangent mode produces via eccentric
   plunges, but through phase dynamics instead of geometric ones.

2. **Prograde + trajectory-centric** still doesn't produce v²-low
   conditions because the prograde orbits are still energetically
   conserved — ω cycling alone doesn't decelerate particles. In this
   case, the death pathway genuinely needs the tangent-direction
   seeding OR one of the Option A/B/C death-criterion improvements
   from Material_Future_Directions.md.

The post-V22-port re-run (both seed modes × both trajectory regimes)
will discriminate.
