# SQF-H — the lazy GPU→CPU handoff (analytic-prior waveform validation)

2026-08-27. Files: `sqfh_core.h` (the handoff cell), `sqfh_cert.c`
(certification driver + synthetic stream).
2026-08-29: model M extension (chirp + envelope) and the real-engine
test — `bench_sqfh_ab.c`, `min/ab/schrod_2d_stream.ergo`; see §10.

Build & run:

```sh
gcc -O2 -o sqfh_cert sqfh_cert.c -lm
./sqfh_cert
```

## 1. What problem this solves

The forward pass — live simulation data on the GPU, or initial setup —
is raw from the source. It needs no correction; there is nothing more
true to correct it against. The integrity problem lives at the
**handoff**: the lazy transfer where the CPU receives the stream,
checks it against what the physics *should* be doing, and organizes it
into proper batched storage.

The CPU has a fixed-size grid; the GPU scales to the task. All the CPU
needs to know is the **scaling factor, amplitude, and frequency** of
the waveform(s) the GPU was supposed to be tracking. It is bound
continuous physics, with phase/time dilation as needed to keep
everything synced.

This is the key structural fact: the CPU's expectation is not learned,
not tracked, not statistical. It is **analytic** — derived from the
wave parameters. The reference cannot be slowly fooled by a smooth
wrong trajectory, because the reference is the bound physics itself.

## 2. The journal is four wave parameters

Every prior cell in the family (SQ5/SQM/SQW/SQ2B) stores check words
next to the data. SQF-H stores none. The journal is the tuple

```
(scale, A, k, phi)     scaling, amplitude, wavenumber, phase ledger
```

and the expected content of any tile is derived from it in closed
form. If the GPU's task scaling changes mid-stream, the new tuple
simply rides with the next tile's metadata — the handshake is
per-tile, so rescaling costs nothing and cannot desync the archive.

**Model M (§10):** the real-engine test showed a localized packet is
never a bare sinusoid per tile. The journal gains two closed-form
terms — quadratic phase (chirp `c`) and a Gaussian envelope
(`σ`, center `x_c`, carried per tile as `x0`):

```
(scale, A, k, c, sigma, x_c, phi)
```

With `c = 0` and `sigma = 0` the cell is bit-identical to the
four-parameter cell; `sqfh_cert.c` is the regression net.

## 3. The check: lock-in demodulation (one pass)

Per tile (64 f32 samples), the CPU mixes the incoming samples against
the reference at (k, phi):

- **I** = Σ w·cos(θ), **Q** = Σ w·sin(θ), θ = k·x·scale + phi
- fitted amplitude = 2·√(I²+Q²)/N
- **δφ = atan2(I, Q)** — the rotation that best explains the tile
  (sin-reference convention; see §7 for the swapped-quadrature bug
  this comment exists to prevent)
- **residual** = Σw² − 2(I²+Q²)/N — energy *no* sinusoid at (k, any
  phase) can explain

This is the quaternion structure made load-bearing: amplitude is the
scalar part, I/Q is the rotation plane, the phase ledger is the
accumulated rotation. (The ribosome does the same thing in three
levels: initial selection = the I-match, proofreading = the
Q-rotation check, accommodation = the three-lane route.)

**Hot-path cost note:** the first version called cos/sin per sample —
64 transcendental pairs per tile, 1460 ns/tile. The per-sample phase
step is constant, so a Chebyshev rotation recurrence (c′ = c·cosΔ −
s·sinΔ) replaces all of them: two trig calls per *tile*, f64 drift
over 64 steps ~1e-14, cost drops to **278 ns/tile (4.35 ns/sample)**.
Same lesson as the CRC32C and serial-hash traps: transcendentals and
serial chains on the hot path are the tax that eats the design.

## 4. Four lanes

Constructive flow is predictable. Shear is the only place things get
chaotic — and shear is *self-announcing* on the imaginary axis. No
GPU flags, no feedback to the forward path.

```
residual/E > SHEAR_THRESH (0.02)?
 ├─ yes → >5% of samples pinned at the envelope rail?
 │   ├─ yes → candidate OVERFLOW.  Confirm: does a clipped sinusoid
 │   │   at the recovered true amplitude explain the tile?
 │   │   ├─ yes → OVERFLOW: the wave is FINE; the cone of spacetime
 │   │   │   was too small.  Calculate the excess (below), archive
 │   │   │   raw + tag.  The excess is DATA: it goes back as the
 │   │   │   resubmission parameter or carries to neighboring tiles.
 │   │   │   Conservation: nothing vanishes at the rail.
 │   │   └─ no  → fall through (shear can pile samples on the rail)
 │   ├─ one sample holds >50% of residual energy?
 │   │   ├─ yes → SPIKE: transport garbage, localized.  Quarantine
 │   │   │   the sample, tile stays tracked, no episode.
 │   │   └─ no  → SHEAR: distributed quadrature growth.  Curl — a
 │   │       bifurcation, a new degree of freedom, not damage.
 │   │       OFF-RAMP: archive RAW AND COMPLETE, episode-open tag,
 │   │       analytic prior suspended.
 └─ no  → |δφ| > SLIP_TOL (0.01 rad)?
     ├─ yes → SLIP: the tile is the same waveform at a dilated phase.
     │        A rotation, not damage.  Adopt phi += δφ (phase/time
     │        dilation to stay synced), archive, count loudly.
     └─ no  → LINEAR: constructive superposition on the bound
              trajectory.  Archive raw, advance the ledger.
```

**Slips are rotations** — the imaginary axis doing its proper job.
**Shear is the rotation failing to close** — the off-ramp.
**Overflow is the cone hitting its own boundary** — envelope physics,
not wave physics.

### The overflow lane and the excess calculation

The GPU simulates waveforms inside an envelope the way a game renders
a player's clipmap: a cone of sight — here, a cone of spacetime.  When
the amplitude unexpectedly reaches the envelope edge, the tile rails:
samples pin at ±A_env exactly where |sin θ| ≈ 1.  Two discriminators
separate this from shear, both free in the same pass:

- overflow excess is **peak-aligned** (in-phase, I axis): the phase
  and zero-crossings stay true, only the peaks flatten;
- shear growth is **quadrature** (Q axis): a new degree of freedom.

And the excess is **analytically invertible**.  A clipper's surviving
fundamental follows the describing function

    M(A) = A · (2/π) · [asin(r) + r·√(1−r²)],   r = A_env / A

The lock-in pass measures M = 2√(I²+Q²)/N directly; bisection on the
formula recovers A_true, and **excess = A_true − A_env**.  (Watch the
range: a fully squared-off wave's fundamental is 4/π × rail, so M can
legitimately reach 1.27·A_env — an early "M ≥ A_env means deeply
railed" shortcut was wrong and is recorded as a fixed bug.)

Confirmation matters: shear can also push samples onto the rail.  So
the lane only fires when a clipped sinusoid at the *recovered*
amplitude re-explains the tile (residual of the clipped fit below the
shear threshold).  Otherwise it falls through to spike/shear.

Certified: 12/12 railed tiles (true A = 1.6, envelope 1.0) routed
OVERFLOW with excess recovered at 0.6053 vs true 0.6000, raw
byte-identical, zero false episodes.

## 5. The episode protocol (off-ramp / on-ramp)

Shear data is precious — it is where the interesting physics is — so
the design's prime directive is **never clamp, never correct**:

- **Episode open:** tile archived byte-identical, tagged. The moment
  journal for the span records *measured* complex moments as-is
  rather than the analytic reference.
- **During the episode:** tiles are checked for continuation, not
  against the suspended prior. An episode ends when residual/E
  collapses back below threshold.
- **On-ramp / close:** tagged, and the phase ledger resyncs with the
  phase the episode *actually consumed* — measured from the data via
  the closing tile's δφ, never assumed.
- Episode boundaries are first-class archive objects: open/close
  tags with the measured phase across the episode.

Nothing is restricted unless there is a physical reason for it — and
a bifurcation *is* a physical event, so it is routed and recorded,
not suppressed.

## 6. Certified behavior (sqfh_cert.c, deterministic)

Synthetic GPU stream: 4096 tiles × 64 f32 samples, A = 1, three
cycles/tile, σ = 0.005·A noise. Injections with generator-side truth:
a +0.40 rad slip at tile 1000, a 12-tile distributed shear episode at
tiles 1500–1511 (chirp + amplitude breathing), a −0.25 rad slip at
tile 2500, and a ×50 transport spike at tile 3000 sample 17.

```
SQFHOR O1_linear_purity   4081/4081 = 1.000000  expect>=0.990
SQFHOR O2_slip_count      2 detected (expect 2)  false_slips=0
SQFHOR O2_slip_recovery   0.3991 / -0.2491 rad (true +0.40 / -0.25)
SQFHOR O3_episode         open@tile 1500  close@tile 1512  pairs=1/1
SQFHOR O4_raw_fidelity    12/12 episode tiles byte-identical
SQFHOR O5_spike           tile 3000 sample 17 routed=SPIKE (not shear)
SQFHOR O7_overflow_lane   12/12 routed OVERFLOW, 0 episodes, raw 12/12
SQFHOR O8_excess_recovery 0.6053 (true 0.6000, |err|<=0.05)
SQFHOR O6_handoff_cost    ~300-326 ns/tile (~5 ns/sample)
```

The stream also injects 12 envelope-overflow tiles at 2000–2011
(true amplitude 1.6 railed at the 1.0 envelope).

## 7. The bug the ladder caught (recorded)

First certified run: **1284 phantom slips.** The demodulation was
written `δφ = atan2(Q, I)` — which under the sin-reference convention
measures π/2 − slip. The ledger adopted π/2, the next tile read as
−π/2 off, the ledger adopted π, and the phase accumulator oscillated
forever without settling. Everything *looked* like enthusiastic slip
detection. Fixed to `atan2(I, Q)`; the ledger went silent except at
the two real injections. The comment in `sqfh_lockin` now carries the
derivation so the convention can't drift again.

## 8. Boundaries, stated once

- The prior is the bound physics: if the tracked model itself is
  wrong (wrong k, wrong A), every tile reads as slip or shear. That
  is detection working, not failing — but it means parameter truth
  lives upstream of the handoff.
- A wrong signal in the *exact shape* of the tracked waveform is
  invisible (the pent-class exclusion, one level up): structured,
  documented, not statistical.
- Thresholds (0.02 residual, 0.01 rad slip, 0.50 spike share) route
  traffic; they never alter data. Tuning them trades false episodes
  against missed on-ramps and is a physical, per-stream decision.
- Episode continuation uses a local tracking check; a shear episode
  that *never* closes is archived raw forever — loud by construction
  (the episode-open tag never gets its pair).
- Overflow recovery is exact for moderate excess; as the wave
  approaches fully squared-off, the describing function flattens and
  the inversion loses resolution (returned excess becomes a lower
  bound — loud, never a silent guess).

## 9. Where it sits in the family

SQF owns the birth of data (forward batch, deferred integrity);
**SQF-H owns its transport** (lazy handoff, analytic prior); SQM owns
its edits; SQW owns redundancy; SQ2B owns the archive. Two different
integrity problems — transport plausibility vs storage bit-fidelity —
each with its own machinery, no overlap tax.

Natural next step: point the handoff at a real ergo stream — **done**,
see §10 (the Schrödinger engine from the AB campaign, not the dbm
lead; the real stream forced the model-M extension).

## 10. Model M and the real-engine test (2026-08-29)

Stream: `min/ab/schrod_2d_stream.ergo` (physics identical to the AB
campaign's stage-1 `schrod_2d.ergo`; oracles reproduced: v_group
0.1547, σ_y 12.798/40.730) emits row y=Y0 of Re ψ as raw f32, 512
samples × 1600 steps → `/tmp/schrod_stream.bin`. Harness:
`benchmark/bench_sqfh_ab.c` — each row is handed over as one 8-tile
batch (SQFH_BATCH) with the journal in closed form from the program's
own PARAMETERs (K0=0.4, SIG0=16, AA=0.20, X0=140).

### The bare prior fails on real packet data

First run (four-parameter journal): residual share 0.73–0.97
*everywhere*, including packet center; zero SLIPs ever fired; every
LINEAR tile was numerical silence (E≈0). Two measured mechanisms, both
intrinsic to a localized packet vs a fixed 64-sample tile:

- **envelope taper**: packet σ=16 cells ≪ 64-sample tile — no
  constant-amplitude sinusoid fits a tile spanning 4σ of envelope;
- **spreading chirp** (wavefront curvature): local k inside the packet
  measured by zero crossings spans 0.349–0.449 at T=100 and
  0.209–0.628 at T=800. No single tone explains such a tile.

### The extension

Reference: `θ_i = phi + k·scale·i + c·(x0+i)²`, `env_i =
exp(−(x0+i)²/σ²)`, least-squares fit `w = env·(α·sinθ + β·cosθ)` via
the exact env²-weighted 2×2 normal system (the double-angle moments
come from squaring the θ rotator — c²−s², 2sc — no extra trig).
Journal elements, all closed-form in T:

- chirp `c(T) = 2t_s/(σ0⁴+4t_s²)`, `t_s = 2·AA·T` — the exact
  Gaussian-packet solution under ψ_t = ia∇²ψ. (The first derivation
  carried a factor-2 error, c = t_s/(σ0⁴+4t_s²); a Hilbert phase fit
  against the stream fixed it: c_meas/c = 0.95–1.08 over
  T=100..1600.)
- envelope `σ(T) = σ0·√(1+(T/320)²)`, `A(T) = 1/√(1+(T/320)²)`
  (the program's own spreading oracle), `x_c(T) = X0 + 0.1547·T`
  (measured lattice v_group, AB_FINDINGS stage 1).
- phase `phi(T) = K0·(1−X0) − ωT + π/2`, ω = AA·K0² continuum —
  lattice dispersion deliberately NOT in the journal.

Cost discipline: both terms are exact under second-order recurrences
(the rotation step itself rotates by 2c per sample; the Gaussian ratio
by exp(−2/σ²)). One per-tile context (2 sincos + 2 exp; the
row-constant seeds cached at init) is shared by the lock-in, the rail
scan, the spike localizer, and the overflow re-fit; per sample ~30
flops, zero transcendentals. The overflow rail under an envelope is
`env_i·A` and the re-fit reuses the fitted (α,β) scaled by A_true/Afit
— the describing-function inversion stays the flat-amplitude one
(approximate under envelope; never triggered on this stream).

Silence gate (model M only): E < 1e-12 routes LINEAR and closes any
open episode without phase adoption. The floor is a property of the
f32 wire format (roundoff ~2e-13·A² per tile), not physics tuning:
every spike false positive on the real stream had E < 4e-14 (median
1.4e-53 — f32 underflow tails) while real packet tails are ≥ 1e-7.
Side benefit: it also removes a denormal-f64 microcoded slow path
(5–10×) the underflow tails were triggering.

Backward compatibility: `c = 0 && σ = 0` dispatches to the legacy cell
verbatim. `sqfh_cert.c` unchanged, all oracles pass bit-identical
(O1 1.000000; slips 0.3991/−0.2491; episode 1500/1512; spike tile
3000 sample 17; 12/12 overflow, excess 0.6053; ~241 ns/tile).

### Re-test numbers (12800 tiles, ergo f32 stream)

Lanes: LINEAR 4381, SLIP 4249, SHEAR 4170, SPIKE 0, OVERFLOW 0.

- **Center packet tiles** (|x_mid − x_c| < 1.5σ, E > 1e-4, n=3360):
  92.4% tracked (LINEAR+SLIP), share median 0.0054, p90 0.0186 —
  under the 0.02 shear gate. Share at packet center runs 0.0002
  (early T) to 0.003–0.015 (late T).
- **SLIP fires legitimately**: 4249 slips, median |δφ| 0.24 rad. This
  is the continuum-ω journal's phase error against the lattice engine
  being adopted per tile — the design absorbing known-model error as
  rotation, exactly as intended.
- **Remaining SHEAR (4170)** is concentrated at: (a) packet far tails
  — the lattice packet's dispersive (Airy) tail is genuinely not the
  analytic Gaussian (tile 1 at T=150 carries real 5×10⁻³ oscillations
  where the Gaussian tail predicts 10⁻¹³); (b) the absorbing-sponge
  boundary tiles (correct routing: the sponge is a real deviation from
  the bound physics); (c) late-time center tiles where the
  continuum-vs-lattice chirp error (c_meas/c ≈ 1.06–1.08 at T≥1200,
  plus a measured cubic phase term c3 ≈ 1.5e-7) pushes share just over
  the gate (center SHEAR 16.5% at T≥1100, share p90 0.0243).
- **Cost**: mean 336, median 350, p99 610 ns/tile (synthetic baseline
  278; pre-extension real-stream run 208–295). Per lane: LINEAR 183,
  SLIP 365, SHEAR 461 ns. Cache profile intact (in-process per-tile
  perf counters): L1d 530–850 loads/tile by lane, misses 6.5–7.5/tile
  (0.8–1.4%), LLC misses 2.6–12.5/tile, 2818–6540 instr/tile.
  Whole-process `perf stat` cross-check: L1d miss 1.7% (dominated by
  the file load; LLC generic events unsupported on this PMU, so the
  in-process LLC numbers are the evidence).

### What the prior still does not know

- lattice dispersion ω(k) (the phase-ledger error it causes is
  absorbed loudly via SLIP — that lane working, not failing);
- the lattice chirp correction (~5–8% at late T) and cubic/quartic
  phase (the Airy tails) — the current wall for the remaining SHEAR;
- the absorbing sponge at the grid boundary;
- overflow excess recovery under an envelope (flat describing
  function, approximate, untriggered here).

Whether to teach the journal the lattice dispersion (ω and the chirp
correction are both closed-form in λ(k) = 4sin²(k/2)) is a design
decision deferred upstream: it would move the late-time center tiles
from borderline SHEAR to tracked, at the cost of coupling the journal
to the discretization instead of the continuum physics.
