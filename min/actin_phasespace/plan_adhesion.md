# plan_adhesion.md — R6 substrate adhesion and traction rung

Registered: 2026-09-02, before any R6 engine build or run. Methodology:
sequential lock-step; oracle and experiment designed together; gates before
smokes; smokes before ensembles; checkpoint to `/mnt`. Single thread, no
swarm.

## 1. Question

Can an actin brush form **dynamic substrate adhesions** that transmit a
measurable traction force while continuing to turn over?

This is the first rung on the stress-fiber path in `NEXT_STAGES_PLAN.md`:
adhesion must be certified before crosslinking, myosin, stress fibers, or
full filopodia can be interpreted mechanically.

## 2. Certified starting point

Parent engine: `brush_bfm.ergo`.

Certified properties inherited from R2/R5:

- exact monomer conservation and clean ghost scans;
- unbranched brush, branched brush, formin brush, and hybrid arms;
- hold-release piston protocol;
- force-margin stall instrumentation;
- deterministic hash RNG with collision-mapped slots;
- WRITE-only instrumentation does not perturb trajectories.

R6 begins with the **unbranched, no-formin arm** (`PBR=0`, `FORMIN=0`) to
isolate adhesion. Branched and hybrid integration are diagnostic follow-on
arms, not part of the first pass/fail gate.

## 3. Scope decision

The first adhesion is deliberately minimal:

- one substrate interface;
- one dynamic adhesion bond per filament;
- slip-bond rupture only;
- no catch bonds;
- no integrin clustering;
- no crosslinking;
- no myosin;
- no membrane tube or full filopodium geometry.

This isolates the new bookkeeping and force path before adding bundle
machinery.

## 4. Geometry and mechanism

Engine candidate: **`brush_adh.ergo = brush_bfm + PADH channel`**.

### 4.1 Substrate interface

Add a fixed lab-frame substrate interface at:

```text
XADH = 2.0
```

This is inside the existing 12σ box, above the hard/soft wall at
`XWALL=0.5`, and coincides with the lower edge of the certified free-gas
seeding slab. It is a substrate adhesion plane, not a new steric wall.

At attachment, the substrate target is:

```text
A = (XADH, y_bead(attach), z_bead(attach))
```

Thus the substrate is spatially fixed in x but permits lateral yz placement
without introducing a discrete adhesion-site lattice in the first
implementation.

### 4.2 Eligible actin element

Each active filament may carry at most one adhesion. The eligible element is
the **pointed-end tail bead** at the moment of attachment:

```text
B = 2*FILPNT(F)
eligible if PX(B) ≤ XADH + RADH
```

After attachment, the adhesion remains bound to that **monomer**, not merely
to the filament slot. If pointed polymerization makes the monomer internal,
the adhesion becomes a side/shaft attachment. This is intentional: it models
an adhesion gripping the filament rather than a tip-only clutch.

The bond is removed if the attached monomer leaves the filament or the
filament dies.

### 4.3 Spring and slip rupture

While attached:

```text
d = |R_bead - A|
F_A = 2*KADH*d        (3D harmonic spring, existing engine convention)
```

The force on the bead points toward A. The equal-and-opposite substrate
traction is accumulated separately as `-F_A`.

Rupture is a force-dependent slip bond:

```text
P_rupture = KOFFA * DT * EXP(|F_A| / FBA)
```

A hard geometric release also fires when:

```text
|R_bead - A| > SMAXA
```

No catch bond, force reinforcement, or adhesion maturation is included in
R6.

### 4.4 Registered parameters

Initial smoke parameters:

| parameter | value | role |
|---|---:|---|
| `PADH` | 0/1 | channel toggle; OFF must be bit-identical |
| `XADH` | 2.0 | fixed substrate interface |
| `RADH` | 0.75 | capture slab around interface |
| `KADH` | 2.0 | adhesion spring stiffness |
| `KONA` | 2.0 | attachment rate while eligible |
| `KOFFA` | 0.02 | zero-force rupture rate |
| `FBA` | 1.0 | slip-bond force scale |
| `SMAXA` | 2.5 | hard geometric release |

Rationale: KONA=2.0 gives P≈0.01/step while eligible; KOFFA=0.02 gives a
zero-force lifetime of order 10k steps; FBA=1.0 makes force sensitivity
measurable at the brush's certified per-tip force scale.

### 4.5 RNG slots

Current certified slots end with branching at `4500+2(F-1)` and
`4501+2(F-1)`. R6 reserves:

```text
attachment: 4600 + 2*(F-1)
rupture:    4601 + 2*(F-1)
```

For MAXF=32 the range ends at 4662 and is disjoint from all existing slots.
No draw is made when `PADH=0`.

### 4.6 State and inventory

New per-filament state:

- `ADHM(F)` — adhered monomer ID, 0 if unattached;
- `ADHB(F)` — adhered bead ID at attachment;
- `ADHX/Y/Z(F)` — fixed substrate target;
- `ADHBORN(F)` — attachment step.

Clearing rules:

- filament birth/branch birth: state starts unattached;
- attached monomer unbinds: adhesion ruptures;
- filament death/dissolution: adhesion ruptures;
- hard stretch or stochastic slip: adhesion ruptures.

The adhesion inventory is `sum(ADHM>0)` and must equal the number of
occupied adhesion records at every census.

## 5. Instrumentation

All instrumentation is WRITE-only and added to the gate filter.

### Event records

```text
adha STEP F M bead x y z
adhr STEP F M lifetime force_x force_y force_z cause
```

`cause`: 1=slip, 2=hard stretch, 3=monomer unbind, 4=filament death.

### Windowed records

One line per NDIAG window:

```text
adhs STEP nadh trx try trz fabs attach_rate rupture_rate
```

where `trx/try/trz` are the mean substrate reactions and `fabs` is the mean
adhesion force magnitude over attached bonds.

### Static certification

`MIRROR=1` must expose adhesion spring energy/force in a constructed loaded
configuration for FD validation. The adhesion energy is:

```text
E_A = KADH * d*d
```

for the uncapped harmonic spring.

## 6. Registered oracles

### O-A1 — engine gates

With `PADH=0`, the new engine must be bit-identical to the certified parent
under the strict gate filter:

1. `PBR=0, FORMIN=0` ≡ `brush_bfm(PBR=0,FORMIN=0)`;
2. `PBR=1, FORMIN=1` ≡ `brush_bfm(PBR=1,FORMIN=1)`.

Each gate: 300k steps, seed 77031, 0 diffs. Ghost scan must remain zero.

**Fail response:** do not smoke. Fix bookkeeping/RNG/instrumentation and
rerun gates.

### O-A2 — adhesion dynamics

In the unbranched F=1 smoke, stationary adhesion occupancy must satisfy:

```text
0.05 ≤ ⟨N_adh⟩/⟨N_f⟩ ≤ 0.60
```

and the stationary window must contain at least 20 attachment and 20 rupture
events.

Interpretation:

- below 0.05: substrate geometry or eligibility is ineffective;
- above 0.60: adhesion is over-pinning the brush;
- too few events: bonds are effectively irreversible.

### O-A3 — slip-bond law

Event-resolved rupture hazard must increase with adhesion force. Pooling the
law-grid arms, the fitted hazard sensitivity β_A in

```text
hazard(F_A) = KOFFA * EXP(β_A * F_A)
```

must lie in the registered window:

```text
0.5 ≤ β_A ≤ 2.0
```

with nominal FBA=1.0. This is deliberately broad: it tests direction and
scale, not a precision fit.

**Fail response:** if β_A≤0 or the hazard is force-flat, the force used for
rupture is wrong or the event log is misattributed; stop and diagnose before
integration arms.

### O-A4 — traction and force accounting

Two separate criteria:

1. **Bookkeeping exactness:** reported substrate traction equals the
   independently recomputed negative adhesion spring force to numerical
   tolerance on every `adhs` record.
2. **Load response:** mean x-directed traction magnitude at F=4 must exceed
   the F=0 arm, and the F=1 smoke must show nonzero sustained traction
   rather than isolated numerical spikes.

The purpose is to prove that adhesion is a real force path, not merely a
state flag. The full multi-force closure equation will be recorded in the
R6 law document after the sign audit, but no phantom force source is allowed.

### O-A5 — stability and inventory

Across all R6 runs:

- monomer conservation exact: `nbound+nfree+2*ndim=400`;
- filament-length sum equals `nbound` at every census;
- gm state counts match census exactly;
- ghost scan = 0;
- `N_f≤MAXF`;
- adhesion inventory equals event/state reconstruction exactly;
- no SIGSEGV, hang, NUL corruption, or missing FINAL over 1M steps.

## 7. Stage plan

### Stage R6-a — build and gates

1. Copy `brush_bfm.ergo` → `brush_adh.ergo`.
2. Add the PADH channel, state arrays, RNG slots, force accumulator,
   instrumentation, and clearing rules.
3. Extend MIRROR/FD certification to the adhesion spring.
4. Run O-A1 gates.
5. Verify compilation with the certified Ergo toolchain.

No ensemble before both gates pass.

### Stage R6-b — unit smoke

Purpose: prove the adhesion spring and rupture machinery in the simplest
load path.

Configuration:

```text
PADH=1, PBR=0, FORMIN=0, DIMERS=0, PSTN=1
F_EXT=1, seed=77031, 1M steps
```

If required to place the initial pointed end inside the adhesion slab, add a
default-inert initial-condition parameter such as `XSEED`, with default
exactly equal to the parent value. Any nondefault value must be documented
and must not affect the O-A1 gate.

Pass criteria:

- adhesion forms;
- spring force matches FD certification;
- ruptures occur;
- traction record is nonzero;
- no inventory or ghost failure.

### Stage R6-c — brush smoke

Configuration:

```text
PADH=1, PBR=0, FORMIN=0, DIMERS=1, PSTN=1
F_EXT=1, seed=77031, 1M steps, clamped piston
```

Checks O-A2 occupancy/turnover, first traction read, conservation, and
survival. If O-A2 fails for geometry reasons, register an adhesion-geometry
amendment before any ensemble.

### Stage R6-d — law grid

Clamped piston, unbranched arm:

```text
F_EXT ∈ {0,1,4} × seeds {77031,84950}
```

Measurements:

- occupancy and turnover;
- attachment waiting time;
- rupture hazard vs force;
- traction vs load;
- filament population, engagement, and force changes relative to PADH=0.

This grid decides O-A2, O-A3, O-A4, and O-A5.

### Stage R6-e — release/traction grid

Only after the clamped grid passes:

```text
hold-release PREL=300k
F_EXT ∈ {1,4,8} × seeds {77031,84950}
```

Purpose: test whether the adhered brush remains force-balanced when the
piston is free. This is not a v(F) assay; the ratified B-2 force-margin
instrument remains the valid 12σ-box criterion.

### Stage R6-f — integration diagnostics

One-seed smokes only, after the base mechanism passes:

1. `PBR=1, FORMIN=0` — branched mesh + substrate adhesion;
2. `PBR=1, FORMIN=1` — hybrid + substrate adhesion.

These diagnose interference with S4 branch anchors and formin tethers. They
are not oracle arms unless promoted by a later amendment.

## 8. Anticipated failure modes and registered responses

1. **Zero or near-zero adhesion occupancy**
   - Cause: pointed ends rarely enter the x≈2 slab.
   - Response: measure eligibility flux first; then register a narrow
     amendment to XADH/RADH or allow side-bead attachment. Do not silently
     widen the geometry.

2. **Adhesion deadlock**
   - Cause: KOFFA too low, FBA too large, or attachments transferred into
     long-lived shaft positions.
   - Response: register a rupture-rate amendment or make shaft attachment
     ineligible after pointed growth.

3. **Over-constraint / structural freezing**
   - Cause: too many filaments simultaneously substrate-bound.
   - Response: reduce occupancy through KONA or one-bond eligibility; do not
     proceed to crosslinking on a frozen brush.

4. **Double-anchor interference**
   - Cause: S4 membrane anchors or the initial seed anchor coexist with a
     substrate adhesion on the same filament.
   - Response: keep base certification unbranched; for integration, register
     an explicit precedence rule rather than ad hoc clearing.

5. **Force-sign confusion**
   - Cause: traction reported on bead rather than substrate, or piston
     reaction sign mixed with actin force.
   - Response: static FD case plus analytic sign check before smoke.

6. **Inventory leak on death/unbind**
   - Cause: ADHM not cleared at dissolution, pointed unbind, or slot reuse.
   - Response: fix and rerun O-A1/O-A5; any affected ensemble logs are
     quarantined.

7. **RNG-slot collision**
   - Cause: new slots overlap future or legacy channels.
   - Response: rebase before smoke; OFF-gate must remain exact.

## 9. Deliverables

- `brush_adh.ergo`
- gate logs and 0-diff certificates
- `runs20/` ensemble using the verified runner pattern
- `stage_g_analysis.py` and analysis output
- `ADHESION_LAW.md`
- `ANALYTICS.md` update
- verified R6 checkpoint archive

## 10. Exit criterion for R6

R6 passes when a dynamic substrate adhesion channel is gate-clean, forms and
ruptures continuously, shows the registered slip-bond force response,
reports exact traction bookkeeping, and preserves all conservation and ghost
oracles in the unbranched brush. Only then does the project proceed to R7
crosslinking.
