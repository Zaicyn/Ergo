# NEXT_STAGES_PLAN.md — route to adhesion, bundling, myosin, and stress fibers

Drafted: 2026-09-02. Status: **roadmap only — no engine build or ensemble is
authorized by this document**. Each rung below still requires its own
pre-registered `plan_<rung>.md`, with oracle and experiment designed together
before implementation.

## 1. Starting point certified by the current project

The current engine lineage has certified:

- single-filament treadmill chemistry and force assays (`FORCE_LAW.md`);
- population turnover, nucleation, and capping (`POPULATION_LAW.md`,
  `NUCLEATION_LAW.md`, `CAP_LAW.md`);
- an unbranched membrane brush with stall 2.5-3 (`BRUSH_LAW.md`);
- an S4 branched dendritic mesh with engagement n_eng≈3.5 and stall≈12
  (`BRANCH_LAW.md`);
- a formin-tethered processive brush with stall≈14-16 and a hybrid that
  remains force-balanced at F=20 (`FORMIN_LAW.md`).

The hybrid is mechanically strong but still **not a stress fiber and not a
filopodium**:

- no substrate adhesion;
- no crosslinkers;
- no persistent parallel or antiparallel bundles;
- no myosin filaments;
- no contractile force generation;
- orientation remains isotropic at the brush scale.

## 2. Strategic ordering

The direct route to contractile stress fibers is:

```text
adhesion → crosslinking → bundle polarity → minimal parallel-bundle testbed
→ myosin contractile unit → stress fiber → full filopodia / crawling
```

**Filopodium placement:** full filopodia belong near the end. A deliberately
minimal filopodium-like parallel bundle is placed before myosin because it is
a useful non-contractile test of bundling, alignment, formin organization,
and tip adhesion. It is not the full biological organelle.

## 3. Roadmap summary

| rung | target | primary new mechanism | depends on | deliverable |
|---|---|---|---|---|
| R6 | adhesion/traction | dynamic substrate adhesions | current brush engines | `ADHESION_LAW.md` |
| R7 | crosslinking | filamin-like dynamic crosslinks | R6 | `CROSSLINK_LAW.md` |
| R8 | bundle polarity | parallel/antiparallel bundle recognition and stabilization | R7 | `BUNDLE_LAW.md` |
| R9 | minimal filopodium-like bundle | aligned parallel bundle + formin tip + adhesion | R6-R8 | `PARALLEL_BUNDLE_LAW.md` |
| R10 | myosin contractile unit | bipolar myosin filament on antiparallel actin | R7-R8 | `MYOSIN_LAW.md` |
| R11 | stress fiber | actin-myosin bundle anchored between adhesions | R6-R10 | `STRESS_FIBER_LAW.md` |
| R12 | full filopodia and motility integration | membrane tube, guidance, richer adhesions | R6-R11 | `FILOPODIUM_LAW.md` / crawl integration |

No stage begins until the previous stage has: (i) OFF-gate bit identity,
(ii) smoke certification, (iii) ensemble analysis, (iv) a law document,
(v) checkpoint archive, and (vi) any amendments ratified.

---

# R6 — adhesion and traction

## Question

Can the brush exchange force with a substrate through dynamic adhesions
without phantom forces, adhesion deadlock, or inventory leaks?

## Why first

Adhesion is shared by stress fibers, filopodia, and crawling. It must be
certified before any contractile structure can be interpreted as pulling on
a substrate rather than on an engine boundary.

## Mechanism sketch

Engine candidate: `brush_adh.ergo`.

- Add a small number of substrate adhesion sites or adhesion-competent
  monomers.
- Adhesion bond forms when an eligible actin bead enters an adhesion zone.
- Bond is a finite-stiffness spring with finite lifetime.
- First implementation should use a **slip bond**: rupture rate increases
  with tension. Catch-bond behavior, if desired, is a later amendment.
- Bond rupture and reformation use dedicated RNG slots, active only when
  the adhesion channel is ON.
- Instrument per-bond force, lifetime, attachment state, and total traction.

## Registered oracle classes

- **O-A1 gates:** adhesion OFF ≡ certified parent bit-identical.
- **O-A2 adhesion dynamics:** nonzero attachment occupancy with continuing
  turnover; neither zero adhesion nor irreversible total arrest.
- **O-A3 force response:** rupture/lifetime responds monotonically to
  applied tension under the registered slip-bond law.
- **O-A4 traction closure:** substrate reaction balances measured brush
  force over stationary windows; no unaccounted momentum sink.
- **O-A5 stability:** exact monomer conservation, ghost scan zero,
  adhesion inventory conserved, no runaway bond count.

## Smoke and ensemble

- Smoke: one adhesion geometry, moderate load, 1M steps.
- Ensemble: adhesion strength/density grid only after smoke.
- Discriminator arms: adhesion OFF, weak slip bond, strong slip bond.

## Exit criterion

A stationary brush generates measurable, balanced traction with dynamic
adhesions and no conservation or ghost pathology.

---

# R7 — filamin-like crosslinking and mechanical cohesion

## Question

Do dynamic crosslinks stabilize the mesh without freezing it into an
irreversible aggregate?

## Mechanism sketch

Engine candidate: `brush_xlk.ergo`.

- Add transient actin-actin crosslinks between eligible nearby monomer
  beads on different filaments, or between distant monomers on the same
  filament if explicitly registered.
- First abstraction: filamin-like flexible stabilizer, not a bundle-specific
  crosslinker.
- Crosslinks have finite rest length, stiffness, lifetime, and rupture
  force.
- Crosslink inventory must be explicit and conserved.
- Instrument crosslink number, lifetime, force spectrum, cluster size, and
  mesh displacement under a registered perturbation.

## Registered oracle classes

- **O-X1 gates:** crosslinker OFF ≡ certified adhesion parent.
- **O-X2 dynamic equilibrium:** crosslinks form and break continuously;
  stationary occupancy is neither zero nor saturated indefinitely.
- **O-X3 cohesion:** crosslinked mesh shows increased resistance to a
  registered pull/perturbation relative to the OFF arm.
- **O-X4 no collapse:** crosslinking must not produce a single irreversible
  compact aggregate or destroy brush turnover.
- **O-X5 stability:** monomer, filament, adhesion, and crosslink inventories
  all conserved; ghost scan zero.

## Exit criterion

The mesh is mechanically tougher but remains dynamic and turnover-competent.

---

# R8 — bundle polarity: parallel and antiparallel architectures

## Question

Can the engine distinguish, stabilize, and measure parallel versus
antiparallel actin bundles?

## Why this is separate

Stress fibers need antiparallel actin organization for myosin contraction.
Filopodia need parallel bundles. Polarity must be certified before myosin;
otherwise a contraction result could be an artifact of sign conventions.

## Mechanism sketch

Engine candidate: `bundle_pol.ergo`.

- Reuse crosslink machinery from R7.
- Add a polarity-dependent crosslink channel or bundle-recognition
  instrument.
- Bundle state is determined from filament axes, bead separation, and
  persistence of contact.
- Start with constructed geometries: one parallel pair and one
  antiparallel pair, then allow self-assembly only after the instrument is
  certified.
- Instrument polarity correlation, bundle lifetime, inter-filament spacing,
  and sliding displacement.

## Registered oracle classes

- **O-B1 gates:** bundle channel OFF ≡ certified crosslink parent.
- **O-B2 instrument:** constructed parallel and antiparallel pairs are
  classified correctly with zero sign errors.
- **O-B3 stability:** both bundle classes persist for their registered
  lifetimes under no-motor conditions.
- **O-B4 selectivity:** the crosslink rule enriches the intended polarity
  relative to the unselective R7 control.
- **O-B5 stability:** no filament collapse, artificial fusion, or inventory
  leak.

## Exit criterion

Parallel and antiparallel bundles are separately measurable, stable, and
mechanically distinguishable.

---

# R9 — minimal filopodium-like parallel bundle

## Question

Can formins, bundle crosslinkers, and tip adhesion organize a persistent
parallel actin bundle?

## Scope control

This is **not** the full filopodium. It lacks a membrane tube, guidance
field, and detailed tip complex. It is the simplest non-contractile bundle
assay that validates the shared machinery before myosin is introduced.

## Mechanism sketch

Engine candidate: `filopod_min.ergo`.

- Seed or recruit a small cluster of parallel filaments.
- Use the R2 formin tether/channel at the distal end where appropriate.
- Use R8 parallel-bundle crosslinking.
- Use R6 adhesion at the distal tip or along the shaft, as pre-registered.
- Measure bundle polarization, length distribution, tip force, stall,
  adhesion traction, and survival.

## Registered oracle classes

- **O-P1 gates:** all new channels OFF ≡ certified R8 parent.
- **O-P2 polarization:** bundle axis correlation exceeds a registered
  threshold; isotropic brush behavior is a failure.
- **O-P3 persistence:** bundle survives longer than the ordinary filament
  lifetime without becoming immortal.
- **O-P4 force:** tip traction/stall exceeds the unbundled control by a
  registered factor.
- **O-P5 dynamic turnover:** monomer and filament turnover continue inside
  the bundle.
- **O-P6 stability:** exact inventories and ghost scan zero.

## Exit criterion

A stable, polarized, force-bearing parallel bundle exists without myosin.

---

# R10 — myosin contractile unit

## Question

Can a coarse-grained bipolar myosin filament generate directional sliding
and contractile force between antiparallel actin filaments?

## Why this is its own rung

Myosin introduces a new force source and a new sign convention. It must be
certified in a minimal unit before being embedded in a stress fiber.

## Mechanism sketch

Engine candidate: `myosin_unit.ergo`.

- Construct two antiparallel actin filaments or bundles with known
  polarity.
- Add one bipolar myosin element with heads coupled to each actin track.
- Heads move toward actin barbed ends; on antiparallel tracks this produces
  contraction.
- Include force-dependent stall and unbinding.
- Start with fixed endpoints, then dynamic endpoints only after the sign
  and force laws pass.
- Instrument myosin position, step direction, force, actin sliding,
  contraction velocity, and rupture events.

## Registered oracle classes

- **O-M1 gates:** myosin OFF ≡ certified bundle parent.
- **O-M2 directionality:** sliding direction is correct on both constructed
  parallel and antiparallel controls.
- **O-M3 contraction:** antiparallel unit develops registered contractile
  force or endpoint displacement; parallel control does not.
- **O-M4 force-velocity:** contraction slows under resisting load and
  stalls within a registered window.
- **O-M5 turnover:** myosin binding/unbinding remains dynamic; no permanent
  clamp.
- **O-M6 stability:** actin, crosslinker, adhesion, and myosin inventories
  conserved; no ghost forces.

## Exit criterion

A single antiparallel actin-myosin unit contracts with the correct sign,
finite stall, and dynamic turnover.

---

# R11 — stress fiber

## Question

Can actin bundles, crosslinkers, adhesions, and myosin assemble into a
stable contractile stress fiber anchored to the substrate?

## Mechanism sketch

Engine candidate: `stress_fiber.ergo`.

- Arrange alternating actin polarity along a bundle or fiber segment.
- Attach ends to R6-certified substrate adhesions.
- Use R8 bundle stabilization and R10 myosin units.
- Permit turnover so the structure is a steady-state material, not a frozen
  object.
- Measure tension, endpoint traction, length homeostasis, myosin
  distribution, actin flow, and repair after a registered perturbation.

## Registered oracle classes

- **O-S1 gates:** each new channel OFF ≡ the appropriate R10 parent.
- **O-S2 assembly:** a persistent fiber forms within the registered time
  window from the registered initial condition.
- **O-S3 contractility:** endpoint adhesions bear inward traction; fiber
  tension is positive and stationary.
- **O-S4 polarity organization:** antiparallel regions are enriched around
  myosin; parallel regions are separately identified.
- **O-S5 homeostasis:** fiber length and tension remain bounded despite
  turnover.
- **O-S6 perturbation recovery:** after a registered stretch or severing
  perturbation, the fiber either repairs or fails in a measurable,
  classified way.
- **O-S7 stability:** all inventories conserved, ghost scan zero, no force
  discontinuity from bookkeeping.

## Exit criterion

A dynamic adhesion-anchored actin-myosin bundle maintains contractile
tension and transmits traction to both substrate attachments.

---

# R12 — full filopodia and motility integration

## Question

Can the certified parallel bundle become a protrusive, adhesive, guidance-
competent filopodium, and can it coexist with the lamellipodium-like mesh
and stress-fiber machinery?

## Full-filopodium additions

- membrane tube or effective membrane confinement;
- formin-rich tip complex;
- fascin-like parallel crosslinking;
- distal adhesion and traction;
- guidance/chemotactic response if required;
- coupling to the dendritic mesh at the base.

## Registered oracle classes

- **O-FP1 gates:** membrane/guidance channels OFF ≡ certified R9/R11 parent.
- **O-FP2 structure:** thin protrusion, parallel bundle, polarized tip.
- **O-FP3 protrusion:** positive extension under registered membrane load.
- **O-FP4 guidance:** protrusion direction responds to a registered guidance
  cue without phantom forces.
- **O-FP5 adhesion:** tip adhesion alters persistence or traction in the
  registered direction.
- **O-FP6 integration:** filopodium, branched mesh, and stress-fiber
  machinery can coexist without RNG-slot, inventory, or force-accounting
  interference.

## Exit criterion

The full filopodium is a biologically interpretable application of the
certified bundle/adhesion machinery, not a prerequisite for stress fibers.

---

# Cross-stage engineering requirements

These requirements apply to every rung.

1. **Oracle-first:** every new channel gets its own `plan_<rung>.md` before
   implementation.
2. **Mirror-first gates:** every OFF state must be bit-identical to its
   certified parent under the strict gate filter.
3. **No hidden RNG changes:** new RNG draws require explicitly mapped,
   collision-free slots and are forbidden in OFF arms.
4. **Ghost and inventory scans:** monomer, filament, adhesion, crosslink,
   bundle, and myosin inventories must be exact at every census.
5. **Runner discipline:** use the runs19 runner pattern — stream to /tmp,
   verify exit/FINAL/NUL=0, copy to /mnt, re-verify, and retry on failure.
6. **Checkpoint discipline:** each rung ends with a law document, analyzer
   scripts, manifests, and a verified zip under `/mnt/agents/output/`.
7. **Amendment discipline:** measured violations of a registered premise
   produce explicit amendments; criteria are not silently rewritten.
8. **Sequential execution:** no parallel mechanism development. Parallelism
   is allowed only within a single certified ensemble runner, not across
   design stages.

# Deferred items

These remain useful but should not interrupt the stress-fiber path unless a
stage gate exposes them as blockers:

- tall-box true v(F) engine;
- φ5 1D closure and boundary-table refinement;
- guarded re-ensemble of older contaminated runs;
- detailed membrane biophysics;
- full guidance/chemotaxis;
- complete crawling-cell integration.

# Immediate next action

R6 is now pre-registered in `plan_adhesion.md`. The next action is to build
`brush_adh.ergo`, extend FD/static certification to the adhesion spring, and
run the O-A1 OFF-gates before any smoke or ensemble.
