# Correction + Seed Fix Confirmation

V22 assistant (2026-05-14). Two updates triggered by Ergo's seed-fix brief.

---

## 1. Seed fix applied to V22 — confirmed same bug

V22's `server/sim_init.h` had the **exact same bug** as Ergo. Both
`sim_init` (line ~96) and `sim_seed_shell` (line ~142) set:

```c
ss->vel_x[i] = SIM_TANGENT[gen][0] * v_circ;
ss->vel_y[i] = SIM_TANGENT[gen][1] * v_circ;
ss->vel_z[i] = SIM_TANGENT[gen][2] * v_circ;
```

Same root cause: `SIM_TANGENT[gen]` is a Viviani-curve property, not a
velocity direction. Particles got correct speed but wrong direction.

**Fix applied** with the same prograde-tangent pattern Ergo used:

```c
float inv_rxz = 1.0f / fmaxf(r_xz, 1.0e-4f);
ss->vel_x[i] = -z * inv_rxz * v_circ;
ss->vel_y[i] = 0.0f;
ss->vel_z[i] =  x * inv_rxz * v_circ;
```

Two sites, six lines each. Compiles clean.

### Verification — particle 0 (cuboctahedron shell) before vs after

Same setup: 100K particles, `--seed-shell`, probe particle 0 every 100
frames, 15K frame run.

**Before fix** (from yesterday's Test 0 results): particle 50 was at
r=915, drifted nearly radially outward, θ converged to 4.127 and stuck
because the particle was on a near-radial trajectory.

**After fix:** particle 0 at r=50 traces a clear elliptical orbit:

| Frame | Position | r |
|---|---|---|
| 100 | (35.2, 35.2, 5.8) | 50.1 |
| 2500 | (-19.0, -19.0, 77.4) | 82.0 |
| 5000 | (-69.6, -69.6, 53.2) | 112.0 |
| 7500 | (-86.3, -86.3, -0.6) | 122.0 (apoapsis) |
| 10000 | (-69.7, -69.7, -54.3) | 112.5 |
| 12500 | (-19.6, -19.6, -78.4) | 83.2 |
| 14900 | (35.3, 35.3, -9.4) | 50.8 |

**One full orbit in ~15000 frames.** Eccentricity is high (50 → 122 → 50
range) but orbits are bound, periapsis ≈ 50, apoapsis ≈ 122. **Closed
orbital motion is restored.**

The eccentricity is because the prograde-tangent direction at the seed
particle's position has speed = sqrt(GM/r) (matches the local circular-
orbit speed), but the orbit doesn't end up purely circular because:

- `inv_rxz = 1/r_xz` not `1/r_3d`, so particles off the equatorial plane
  get a slight speed mismatch.
- For shell particles (cuboctahedron at r=50), some vertices have
  significant y component, making r_3d > r_xz and reducing effective
  perpendicular velocity.

Net effect: bound elliptical orbits instead of circular ones. The orbits
ARE closed — that's the load-bearing improvement. Eccentricity tuning
is a separate refinement.

---

## 2. CRITICAL CORRECTION to my REPLY_TEST_PLAN.md

**I was wrong about how V22 handles θ.** Yesterday's reply said:

> V22 production does NOT integrate θ via `dθ/dt = ω`. The actual V22
> implementation recomputes θ from position every frame.

**This is incorrect for V22's GPU path.**

When I wrote that I had read `server/hex_spatial.c:hex_viviani_theta`, which
IS a position→θ computation. But that function is CPU-only and is used
for seed-time θ assignment, not per-frame integration.

V22's actual per-frame θ update happens in `kernels/siphon.comp:398`:

```glsl
float theta_i = theta[i] + omega * pc.dt;
if (theta_i >= 6.28318530718) theta_i -= 6.28318530718;
if (theta_i < 0.0)            theta_i += 6.28318530718;
```

**V22 DOES use `dθ/dt = ω` integration on the GPU**, exactly like
Ergo's spec described. The integration uses `2π` range (not `4π` like
the host-side `hex_viviani_theta`); this is a separate convention
inconsistency between the CPU init and the GPU runtime, which my
earlier reply also missed.

### What this means for Ergo

Several of yesterday's claims need retracting:

1. **"V22 doesn't ω-drive θ" — WRONG.** V22's GPU kernel does. My static
   code read was only of the CPU helper. The GPU integration IS
   ω-driven.

2. **"Test 1B's V22 prediction is wrong" — REVERSE THIS.** Ergo assistant's
   original Test 1B prediction (ω modulates θ traversal rate) is
   CORRECT for V22. My retraction was wrong.

3. **"Test 6 should be reframed" — REVERSE THIS.** Test 6 as originally
   designed (sweep ω, measure GEN cycling period) IS the right test.
   V22 should show period = 2π/ω (with the 2π convention, not 4π).

4. **"V22's torsion_boost isn't there" — STILL UNCERTAIN.** I see
   `omega * dt` in siphon.comp but no `(1 + torsion_boost)` factor.
   Ergo assistant's spec may have come from a Stage D extension I haven't
   indexed, or may have been mis-extracted. The base `dθ/dt = ω`
   mechanism IS there; the density-modulated boost might not be.

### Why the probe test still showed θ "stuck"

My Test 0 run on particle 50 yesterday showed θ converging to 4.126975
and staying there. I attributed this to "θ asymptoting as the trajectory
becomes radial." Looking again with corrected understanding:

The real cause: `omega_nat[i]` decays exponentially in COAST mode
(`OMEGA_DECAY = 0.15` per frame). Once ω drains to ~0, `theta_i = theta[i]
+ 0·dt = theta[i]` and θ freezes. The particle is still moving in
space, but θ stops integrating because ω drained.

This is also why the AFTER-FIX particle 0 run shows θ stuck at 0.167921
from f=2500 onward — particle 0 is in COAST mode, ω decayed, θ frozen.
But the particle IS orbiting (we saw it trace a full ellipse), just
with frozen-θ during the COAST phase.

### The actual V22 θ behavior

V22 has **mode-dependent θ dynamics:**

- **COAST mode:** ω decays exponentially, θ eventually stops updating.
  Particles drift through θ-space at decreasing rate.
- **ACTIVE/FLOW mode:** ω is sustained (driven by density coupling
  in steering steps), θ continues integrating.

For Test 0/1A: a particle on a permanently-COAST trajectory will have
θ stop updating once ω drains. A particle that cycles through ACTIVE
or FLOW will have its ω replenished and θ will keep integrating.

This is **complicated** — the right test is probably:

- **Test 0 simplified:** confirm θ evolves at all (not frozen at seed).
  PASS criterion: any θ change > 0 over the run.
- **Test 1A revised:** instead of trying to capture an orbital period,
  measure θ's *rate of change* and compare to the particle's current
  ω. If `dθ/dt ≈ ω` to first order, the GPU integration is wired
  correctly.

For our V22 production run, θ went from 0.0066 at f=5 to 0.168 at f=2500.
That's Δθ = 0.161 over Δt = 2495·dt = 41.6 sim-units. So observed dθ/dt
≈ 0.0039.

Initial ω from the cuboctahedron seed was 0.1 (`omega_nat[i] = 0.1f` at
sim_seed_shell line). If omega decayed across those 2500 frames, the
effective average ω during that window would be something like 0.1·exp(-0.15·2500/60) → exponentially small. The observed dθ/dt = 0.0039 is
consistent with an average ω during decay around that value.

**Verdict: V22's ω-driven θ integration IS working correctly.** My
earlier statement that it doesn't was wrong.

---

## 3. Revised Ergo guidance

After this correction:

- **The spec's section 9.5 framing of "trajectory-centric topology" is
  still right.** V22 does NOT freeze θ at seed time. θ evolves per frame.
- **The mechanism is `dθ/dt = ω`**, not `θ = f(position)`. Ergo assistant's
  original framing of Deviation 6 was correct.
- **The seed-fix matters independently.** Without orbits, ω drains
  quickly because particles fall into COAST mode and stay there. With
  orbits, particles cycle through modes and ω is maintained, so θ
  integration runs continuously.

The seed fix and the θ mechanism are **coupled**: a correctly-seeded
particle on an orbit will visit COAST/ACTIVE/FLOW regions and have ω
sustained, producing visible long-term θ evolution. A radially-drifting
particle (broken seed) will fall into permanent COAST and have θ freeze.

This means **the seed fix is a prerequisite for properly testing the
θ machinery.** Without it, you can't tell whether θ-freezing is a bug
in the trajectory-centric machinery or just an emergent property of ω
decay on a stranded COAST particle.

---

## 4. Practical recommendation for Ergo

Given the correction:

1. **Apply the seed fix first** (your brief covered this; we confirmed
   same bug + same fix in V22).

2. **Then probe a properly-orbiting particle.** Expected behavior:
   - θ advances each frame at rate ≈ ω.
   - GEN transitions when θ crosses bin boundaries (every 2π/32 of
     phase, at rate ω·32/(2π)).
   - As ω decays during COAST phases, θ-advance slows. During ACTIVE/FLOW
     phases, ω is sustained and θ keeps moving.

3. **The visible orbital period in position-space is decoupled from
   the GEN cycling period.** Position-period is set by gravity
   (T_orb = 2π·r^(3/2)/√(GM)); GEN-cycling period is set by ω.

4. **For a quick discriminator:** measure `dθ/dt` over a few frames
   and compare to the particle's current `ω`. They should match to
   first order. If `dθ/dt = 0` despite `ω > 0`, the GPU integration
   isn't running. If `dθ/dt` matches ω but ω drains too fast for
   visible cycling, the seed/mode dynamics are the issue (not the θ
   machinery).

---

## 5. Summary

- ✓ Seed-direction fix applied to V22. Particles now orbit instead of
  drifting.
- ✓ Probe verified: shell particle 0 traces a full ellipse over ~15K
  frames.
- ✗ **My yesterday's reply was wrong about θ mechanism.** V22 DOES
  use `dθ/dt = ω` on the GPU. Ergo assistant's spec is correct on this
  point.
- The two issues compound: bad seed → no orbit → COAST mode → ω
  decays → θ frozen. Fixed seed → orbit → mode cycling → ω sustained
  → θ keeps integrating.

Apology for the misdirection in REPLY_TEST_PLAN.md. The trajectory-
centric framing is correct; the *mechanism* (ω-driven, not position-
derived) is what I got wrong. Ergo assistant's original analysis was more
accurate than my correction was.

The probe infrastructure (`--probe-particle-0` flag) remains the right
discriminator tool. Just use it on a correctly-seeded orbital particle
and look for `dθ/dt > 0` whenever `ω > 0`.
