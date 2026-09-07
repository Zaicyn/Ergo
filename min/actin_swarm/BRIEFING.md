# Actin scaffold swarm — shared briefing (READ FULLY BEFORE CODING)

You are one of four agents building an actin-scaffolding mechanism on top of a
certified M4a baseline. You own ONE mechanism. Your job: implement it in BOTH
the Ergo engine and the Python mirror, optimize its parameters, and certify it
through the full oracle ladder. The lead agent compares all four results at
the end on **optimality AND accuracy** — an uncertified result scores zero no
matter how pretty the phenomenon looks.

## File layout

- `/mnt/agents/output/actin_swarm/base/m4a/` — certified M4a baseline:
  `actin_filament.ergo` (engine), `actin_mirror.py` (oracle),
  `actin_cert_config.txt` / `actin_cert_forces.txt` (static-cert dumps),
  `ACTIN_SPEC.md` (full model spec + parameter table + known pitfalls).
- `/mnt/agents/output/actin_swarm/base/m4b_wip/` — work-in-progress M4b
  engine (`actin_scaffold.ergo`) + mirror (`actin_mirror_m4b.py`) with
  pointed-end kinetics and ATP hydrolysis already implemented (feature flags
  DOPOINTED/DOHYD). It RUNS but the parameter regime overgrows (len ~49,
  should plateau ~15-25). Agents M4B/M4H start here; M4C/M4D start from m4a.
- `/mnt/agents/output/actin_swarm/toolchain/ergo_mcl/` — the mcl compiler.
  Copy it to your own /tmp workdir: `cp -r .../ergo_mcl /tmp/<yourname>/`.
- Your deliverable dir: `/mnt/agents/output/actin_swarm/<yourname>/`
  (persistent). Work in `/tmp/<yourname>/` for speed but CHECKPOINT
  deliverables to the persistent dir after every milestone — /tmp may be
  wiped without warning.

## Build & run

```
cd /tmp/<yourname>/ergo_mcl && python3 -m core <file>.ergo -o /tmp/<yourname>/bin
/tmp/<yourname>/bin            # engine run (fast: 150k steps ~ 1 min)
python3 <mirror>.py --fd       # FD force check
python3 <mirror>.py --cert     # write static-cert oracle dumps
python3 <mirror>.py --cal      # rate calibration (SLOW: ~20 min — run with nohup, log to file)
python3 <mirror>.py --run N    # dynamic run (SLOW ~6 ms/step — chunk it or nohup)
```

Compiler gotcha: `__main__.py` misreports missing runtime headers as
"Error: File not found: <source>" — if a build fails that way, check that
`ergo_mcl/runtime/` (ergo_math_kernels.h, ergo_io.h, ergo_stream.h,
ergo_net.h, common.h, cache_perf.h, ergo_vk.h) survived the copy.

## Ergo dialect (hard constraints — the compiler rejects anything else)

- `IMPLICIT NONE`; no PROGRAM wrapper; code starts at top level, subroutines
  after.
- `PARAMETER INTEGER :: N = 60` / `PARAMETER REAL :: X = 0.5` declarations.
- `STATIC INTEGER ::` / `STATIC REAL ::` arrays and scalars.
- Assignment is `:=` (NOT `=`). Comparison ops `≥ ≤ ≠` or `>= <= /=` — match
  the baseline file's style (it uses `<`, `>`, `.AND.`, `.OR.`).
- Block IF/ENDIF, DO/ENDDO. No `^` or `**` — write repeated multiplication.
- Subroutines take NO arguments (globals/STATICs only). `CALL FOO()`.
- WRITE format: `WRITE(*, "step %d kt %.4f ...") args...`
- Deterministic RNG idiom: `SN := HASH(SEED + STEP)` then
  `RAND(SN + k)` ∈ [0,1). Every step must consume the SAME set of draw slots
  (e.g. k=500 bind, 501 unbind, 502/503 pointed, 600+M hydrolysis) whether or
  not the event fires — never make draw counts conditional on physics.
- DATA stencil continuations with trailing comma before `&` (see baseline
  cert config code for the pattern).
- Indexing: engine monomers are 1-based; monomer M's beads are head=2M−1,
  tail=2M. Mirror is 0-based: head=2m, tail=2m+1. **The M4a jitter off-by-one
  (`REAL(I-1)` vs `REAL(I)`) cost us a full cert cycle — check index bases
  every time you port a formula.**

## Oracle ladder (your certification contract — ALL stages must pass)

1. **FD** — analytic forces vs central differences (mirror `--fd`), max rel
   error ≤1e-8 on a config exercising EVERY force term you added. Kinetics-only
   changes inherit the M4a FD (1.6e-9) but you must re-run it to prove no
   regression. New force terms (branch springs, crosslinks) need FD configs
   that load them with nonzero, uncapped force — capped/FCAP-saturated forces
   are FD-invalid BY CONSTRUCTION; keep test geometries out of the WCA core.
2. **Static byte cert** — engine MIRROR=1 variant dumps CFG/FRC/CERT rows from
   a formula-generated config (no RNG); mirror `--cert` writes oracle dumps;
   compare ≤1e-11 (M4a got 4.4e-14). Your cert config must include your new
   structure (a branch, some crosslinks, ...) at zero or known strain.
3. **Rate calibration** — measure every kinetic rate you introduced in
   isolation (mirror), compare to nominal. Divid by ELIGIBLE steps, not total
   steps (e.g. unbind blocked at the MLEN floor → eligible = steps with
   MLEN>floor). Mean-field ODE prediction from measured rates.
4. **Phenomenon cert** — engine AND mirror dynamic runs (≥150k steps,
   ≥2-3 seeds each). Trajectories diverge chaotically: compare STATISTICS
   (second-half means ± sem), not trajectories. Must show: plateau/steady
   state near prediction (or documented deviation with mechanism), kT pinned
   at nominal (0.4), modest fmax, engine/mirror agreement within ~1-2σ.

## Known pitfalls (hard-won, do not rediscover)

- **Park-limited transport**: window visits are long correlated parks;
  on-rate scales with RCAP² and ballistic transit, NOT Smoluchowski flux.
  Current params (DT=0.005, kT=0.4, RCAP=1.4, box 12) are already tuned for
  this — don't regress them.
- **Unbind catapult**: a freed monomer left inside a former partner's WCA
  core (exclusion removed on unbind) gets FCAP-launched → heating feedback
  → runaway coiled growth. The baseline releases at RCAP+0.25=1.65 along the
  end axis (force-free, outside the capture window).
- **Instant-rebind trap**: releasing INSIDE RCAP with alignment makes unbind
  a no-op (rebind next step at P=1). 1.65 is outside; keep it outside.
- **Return capture**: released monomers parked at 1.65 still re-enter
  diffusively, so effective koff in dynamics ≈ 0.8× nominal and plateaus sit
  ~40% above naive ODE predictions. This is a documented model property —
  quantify it, don't fight it.
- **Ladder geometry**: σ=0.5 because at σ=1 the second-neighbor pair
  head_i–tail_{i+2} (distance 0.7) sits in the WCA core. Do not raise σ.
- **Finite-pool arithmetic**: steady state needs sum(koff) < kon·c0. With
  c0=57/1728=0.033 and kon_b slope ≈1.73e-2/step/conc, total off-rates must
  stay below ~5.7e-4/step or the filament collapses; but above koff_b alone
  or there's no treadmilling window. Check your parameter regime against
  this BEFORE running.
- **Anchor transfer** (M4b WIP): pointed unbind of the anchored monomer
  re-grips the new pointed monomer in place. Keep anchor targets = bead
  positions AT TRANSFER TIME (zero initial strain).

## Deliverables (in /mnt/agents/output/actin_swarm/<yourname>/)

1. `<mechanism>.ergo` — engine, compiles rc=0, MIRROR=1 cert variant included
   (separate file OK).
2. `<mechanism>_mirror.py` — mirror with --fd/--cert/--cal/--run.
3. Cert oracle dumps.
4. `RESULTS.md` — the money document: parameter table (final values +
   what you tried and rejected), oracle ladder numbers (FD, cert diff,
   measured vs nominal rates, ODE prediction), phenomenon results (engine
   vs mirror, per-seed table, statistics), failure modes found and fixed,
   and a blunt "what I'd do differently" section.
5. Logs from the final engine and mirror runs.

## Scoring (how the lead compares you)

Accuracy gate (must pass): FD ≤1e-8, static cert ≤1e-11, measured rates
within 10% of nominal, engine/mirror agreement within 2σ.
Optimality ranking (among passing builds): quality of the target phenomenon
(clearest demonstration at lowest parameter fiddling), stability margins
(kT flatness, fmax, no runaway), runtime cost, code clarity/extensibility
for the final integration.
