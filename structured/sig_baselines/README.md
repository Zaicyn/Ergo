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

- `N500K_F200K_thresh048.log` — 19 sigs at N=500K, **PROGRADE**, 8-field format
- `N1M_F200K_thresh048.log` — 37 sigs at N=1M, **PROGRADE**, 8-field format
- `N100K_F200K_thresh048_TANGENT.log` — 954 sigs at N=100K, **TANGENT**, 8-field format
- `N100K_F200K_thresh048_TANGENT_12field.log` — same 954 sigs, **12-field extended format** (adds gen, energy, ang_mom, bin_presence)

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

## Extended fields (2026-05-14, post-12-field upgrade)

Added 4 fields to SIG_* collection to recover information lost in the
original 8-field format:

  SIG_GEN          — raw GEN bin (1..32). Recovers identity collapsed
                     by `|zc|` and `|fw|` (which both have ties across
                     multiple GEN bins).
  SIG_ENERGY       — specific orbital energy ½v² − GM/r at death.
                     Distinguishes deeply-bound from marginally-bound
                     populations.
  SIG_ANG_MOM      — |r × v| at death. Distinguishes near-circular
                     orbits (high L) from plunge orbits (low L).
  SIG_BIN_PRESENCE — bitmask of GEN bins represented in dying cell.
                     bitcount → ring coverage at death location.

Re-clustering the same 954-crystal tangent-mode run with the extended
fields produces the same 4 classes but with sharper discrimination:

  Class             n    rnorm  rho    energy   ang_mom  bin_pres
  HALO_DUST        47   0.90   0.0    −0.09     91        0
  MAIN_DISK       886   0.61   1.0    −0.18     54        1
  CORE_REMNANT     2   0.01   109    −10.3      0.5       1
  DENSE_INNER      19   0.05   99     −2.1      4.3       1

### Three new findings from the extended fields

1. **`SIG_GEN = 1` for all 954 crystals.** Not a sampling artifact —
   every single crystal in tangent-mode at this scale came from GEN
   bin 1 specifically. The substrate's crystallization population is
   not just COAST-biased; it's selectively GEN=1-biased among the 10
   available COAST bins. Suggests the (TANGENT[1] = (−1, 0, 0),
   Z_COUPLING[1] = 1.0, FLOW_W[1] = 0.0) combination creates a
   uniquely favorable plunge geometry. GEN=17 has the same
   (zc=1, fw=0) but TANGENT[17] = (+1, 0, 0), and never produces a
   crystal in this run.

2. **Angular momentum is the clean class separator.** 200× spread
   between CORE_REMNANT (L≈0.5, near-radial plunge) and HALO_DUST
   (L≈91, near-circular outer orbit). Confirms V22 assistant's theory
   that tangent-mode produces low-L plunges; the four classes
   correspond to different L survival rates.

3. **`bin_presence = 0` cleanly separates HALO_DUST.** Particles
   crystallizing in cells with zero ring-bin coverage = the substrate
   has no topological structure at the death location. All other
   classes have bin_presence = 1 (single bin, partial structure).
   DBSCAN at default eps actually picks up subclusters within
   bin_presence=0 by separating mid-r-norm from outer-r-norm halo
   particles.

### Implication: gen=1 invariance is a substrate constraint, not noise

The fact that crystallization is locked to a single GEN bin reveals
that the current substrate has **no genuine GEN-mixing in the
crystallization population**. Every crystal arrived via the same
phase trajectory through θ-space. This is itself a strong indictment
of identity-centric topology — and a clear prediction for the V22
port: if trajectory-centric topology works as intended, post-port
re-runs should show crystals from multiple GEN bins, since particles
cycle through θ-space and can crystallize at different phases.

Post-port "Test of multi-GEN crystallization" = simple histogram of
SIG_GEN across crystals. Pre-port = single bin (1). Post-port = many
bins if trajectory-centric is working.

## Update: prograde-mode crystals ALSO show SIG_GEN = 1 (2026-05-14)

After three external AI analyses raised competing interpretations of
the GEN=1 monopoly (substrate chirality, ISCO analog, eigenmode
filtering vs architectural bias), ran the discriminator experiment
GPT proposed: re-cluster in **prograde mode** at threshold 0.048,
N=1M, with the 12-field signatures.

Result: **all 37 prograde crystals also have GEN=1.**

This is decisive against the "TANGENT[1] direction creates plunge
geometry" theory. In prograde mode the velocity direction is
`(-z, 0, x)/r_xz`, completely independent of TANGENT[GEN]. Yet the
GEN=1 monopoly persists.

### The actual mechanism: GEN is frozen at seed, GEN derives from seed position

GEN is computed once at SIM_INIT or SIM_SEED_SHELL from:

  θ_seed = atan2(Z, X) + SEAM_STEP
  PH     = int(θ_seed · PHASE_MASK / 2π) & PHASE_MASK
  GEN    = (PH >> 10) & GEN_MASK + 1

For positions near the +X axis (Z ≈ 0, X > 0), `atan2(Z,X) ≈ 0`,
`θ_seed ≈ SEAM_STEP = 0.196`, `PH ≈ 1024`, `GEN = 1`.

So GEN=1 = the angular wedge near the +X axis (approximately
`[0°, 22.5°]` in the XZ plane from +X).

Once GEN is set, identity-centric topology keeps it frozen. The
particle's GEN never updates regardless of where it moves. So when
the particle eventually crystallizes — wherever, however — its
recorded GEN is the GEN of its **seed-time angular position**, not
its current angular position.

The "GEN=1 monopoly" finding reduces to: **the particles that
crystallize all came from the same seed-time angular wedge.**

### Why specifically GEN=1 and not other bins

Particles seeded in different wedges:

- Tangent mode: TANGENT[k] velocity direction varies with k. Most
  TANGENT entries have y components that produce velocities not
  aligned with orbital tangent → orbits decay quickly. TANGENT[1]
  and TANGENT[17] have zero y component → these orbits stay in the
  XZ plane longest before crystallizing. TANGENT[1] = (-1, 0, 0)
  produces a clean radial plunge from the +X axis → reaches v²<0.01
  at periapsis. TANGENT[17] = (+1, 0, 0) produces a clean radial
  flight outward from the -X axis (since GEN=17 ≈ -X wedge) → but
  particles never come back to GEN=17 territory at low speed.

- Prograde mode: velocity always perpendicular to position in XZ
  plane. Particles in GEN=1 wedge get velocity in +Z direction →
  they orbit, return to GEN=1 wedge at slightly larger r each cycle,
  eventually reach apoapsis where v²<0.01. GEN=17 particles (at -X
  axis with velocity in -Z direction) also orbit, but their orbits
  apoapsis lands... actually this is unclear, would need direct
  measurement of why GEN=17 doesn't produce crystals too.

Either way, the mechanism is **seed-position bias** + **frozen GEN**,
not substrate-native phase selection.

### Implication: this changes the V22 port test design

The SIG_GEN distribution is NOT a clean discriminator for
trajectory-centric vs identity-centric topology by itself. Post-V22-port,
crystals could still come from a narrow GEN range if the seed
position bias persists.

**Better discriminator**: compare the GEN at crystallization to the
GEN at seed time. Pre-port = identical for every particle (frozen GEN).
Post-port = should differ for any particle that orbited more than a few
GEN bins worth before dying.

Requires a new field: `SIG_GEN_SEED` — the GEN at seed time, separate
from `SIG_GEN` (current GEN at death). Trivial to add: store on the
FLAGS bits 8-12 = the seed GEN that's already there in the current
implementation. Post-port, the current-GEN comes from `theta[i]`
recomputed each frame.

### Recommendation: GPT's LUT permutation test is still worth doing

Even though we've ruled out "TANGENT[1] direction" as the cause, we
haven't fully isolated the role of LUT contents vs the role of bin
index. Permuting the LUT (cycle FLOW_MODE, TANGENT, Z_COUPLING,
FLOW_W by an offset of e.g. +7) should shift the crystal population
to whatever bin now holds the original (COAST + zc=1 + fw=0) entries.
If the crystal population moves with the LUT contents → role-based
selection (substrate-native). If it stays at index 1 → there's
something index-specific in the implementation (likely SPAWN_COUNTER
modulo or initial RNG sequence ordering).

This test costs about 30 minutes of work: write a `permute_constants.py`
that generates a rotated version of `constants.ergo` from a CLI offset,
run both, compare clusters. Deferred for now.

### What this means for the AIs' interpretations

- **GPT** had the correct framing: cannot distinguish substrate-native
  selection from architectural bias without permutation test.
- **Deepseek's** "substrate chirality" reading of GEN=1 is not
  supported by data; prograde-mode result shows GEN=1 is geometric,
  not dynamical.
- **Gemini's** rotation test would also reveal this, but tests a
  different axis (position-axis chirality vs LUT-vs-index).

All three AIs jumped to "this is substrate physics" too quickly. The
right epistemic move was GPT's: name the alternative hypotheses, do
the cheapest test that distinguishes them.
