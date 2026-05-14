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

- `N500K_F200K_thresh048.log` — 19 signatures at N=500K
- `N1M_F200K_thresh048.log` — 37 signatures at N=1M
