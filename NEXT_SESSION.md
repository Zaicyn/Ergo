# Next Session: Hopfion Spillover + DO WHILE

## What's Done

Full ring coupling pipeline operational at 30M@60-74fps:

- **RING_PREV / RING_NEXT** — warp shuffle intrinsics, wrapping modular index
- **RING_SHIFT(val, delta)** — parameterized shuffle for butterfly reductions
- **SORT_BY_GEN** — compiler-generated counting sort, pointer swap, census intervals
- **Phase lock (15.5)** — PH_ERR with signed wrap, restoring toward SEAM_STEP_PH spacing
- **Zero-sum metabolic exchange (15.6)** — directional OMEGA diffusion gated by FLOW_W, RING_PREV(TRANSFER) for conservation, poles reflect
- **Topological charge stabilization (15.7)** — butterfly reduction of PH_DIFF across warp, winding error correction toward Q=1, gated on MET_GATE > 1.49 (complete rings only)
- **Crystal field** — GRID_CRYSTAL permanent density, PFLAG_BANKED

## Task 1: Hopfion Spillover (Section 15.8)

When a complete ring (Q=1) can't maintain coherence due to low OMEGA,
the ring spills — particles are released with an energy penalty and
natural physics dissolves the structure over subsequent frames.

### The Physics

Spillover is a **collective** collapse — the ring breaks as a unit when
the mean OMEGA drops below viability. This is distinct from crystallization
(individual particles freezing when their personal OMEGA < 0.008).
Spillover fires BEFORE crystallization catches individual particles.

OMEGA_CRITICAL = 0.04 (50% of OMEGA_BASE). The ring spills when its
mean metabolic rate drops to half the background level.

### Implementation

Section 15.8, after the winding correction, gated on MET_GATE > 1.49:

```
! ── 15.8. HOPFION SPILLOVER ──────────────────────────────
! Ring cannot maintain Q=1 when mean OMEGA is too low.
! Spilled particles get an energy penalty; natural physics
! (COAST → crystallize) handles dissolution over time.
! Gate: complete rings only (MET_GATE > 1.49).

! Warp mean OMEGA via butterfly reduction (same pattern as 15.7)
OMEGA_SUM := OMEGA
OMEGA_SUM := OMEGA_SUM + RING_SHIFT(OMEGA_SUM, 16)
OMEGA_SUM := OMEGA_SUM + RING_SHIFT(OMEGA_SUM, 8)
OMEGA_SUM := OMEGA_SUM + RING_SHIFT(OMEGA_SUM, 4)
OMEGA_SUM := OMEGA_SUM + RING_SHIFT(OMEGA_SUM, 2)
OMEGA_SUM := OMEGA_SUM + RING_SHIFT(OMEGA_SUM, 1)
OMEGA_MEAN := OMEGA_SUM / 32.0

IF OMEGA_MEAN < OMEGA_CRITICAL THEN
  OMEGA := OMEGA * SPILL_DECAY
ENDIF
```

No flag changes, no mode changes. Just hammer OMEGA down by SPILL_DECAY
(0.5). Low OMEGA → COUPLING=0 (COAST segments) → natural decoupling from
field → drift toward crystallization over ~100-500 frames. The ring dissolves
naturally. The winding correction in 15.7 stops firing because MET_GATE drops
below 1.49 as particles scatter out of the cell.

### New Constants

```
PARAMETER REAL :: OMEGA_CRITICAL = 0.04
PARAMETER REAL :: SPILL_DECAY = 0.5
```

### New Variables

```
REAL :: OMEGA_SUM, OMEGA_MEAN
```

Add to declarations at top of SIM_PHYSICS_STEP (~line 179).

### Verification

1. Run at 30M — rings that lose energy should visibly dissolve (color fades
   from green/yellow to blue, then particles crystallize)
2. High-energy rings should remain stable (Q=1 maintained)
3. Census: monitor crystal count growth rate — should see bursts when rings
   spill, not steady trickle

## Task 2: DO WHILE Language Feature

### Syntax

```
DO WHILE condition
  body
ENDDO
```

Condition must be a scalar boolean expression (comparison result).
No truthy integers, no implicit conversions. Reevaluated every iteration.

### Parser Changes

In `parser.py`, extend `_parse_do` to recognize `DO WHILE`:
- If token after DO is KW_WHILE (new keyword), parse condition expression,
  expect THEN or newline, parse body until ENDDO
- Return new AST node: `DoWhileStmt(condition, body)`

New token: `KW_WHILE` in tokens.py (or reuse DO + peek for WHILE identifier).

### IR Changes

New IR node: `IRWhileLoop(condition, body)` — no loop variable, no bounds.
Lower in ir_builder.py: condition → IRBranch at top, body, unconditional
branch back to condition.

### Codegen

C: `while (condition) { body }`
SPIRV: same as current unextractable loops — the GPU extractor skips them
(frame loop is already unextracted). DO WHILE is for CPU-side control flow
(main loop, convergence loops).

### Why

`DEFAULT_FRAMES = 2147483647` is a hack. The main loop should be:

```
DO WHILE (.TRUE.)
  CALL CLEAR_GRID()
  ...
ENDDO
```

Also enables convergence loops, retry loops, and other CPU-side patterns
that currently require artificial counted bounds.

### Loop Family After This

| Construct       | Meaning                         |
|-----------------|----------------------------------|
| DO I = A, B     | counted deterministic iteration  |
| DO WHILE cond   | condition-controlled iteration   |
| CYCLE           | continue (both loop types)       |
| EXIT            | break (both loop types)          |

Complete structured loop algebra. No iterators, no generators, no closures.

## Build

```bash
./structured/build.sh
sed '/VERIFY/,/4250/d' galaxy_structured.ergo > /tmp/nonet.ergo
python -m mcl --target spirv --precision f32 --no-split --render -N 29000000 -M 30000000 -o galaxy_render /tmp/nonet.ergo
```

## Key Files

```
structured/
  constants.ergo       — OMEGA_CRITICAL, SPILL_DECAY (new)
  fluid_subs.ergo      — Section 15.8 (spillover), declarations

mcl/
  tokens.py           — KW_WHILE (new, for DO WHILE)
  ast_nodes.py        — DoWhileStmt (new)
  parser.py           — _parse_do extended for WHILE variant
  ir.py               — IRWhileLoop (new)
  ir_builder.py       — Lower DoWhileStmt to IRWhileLoop
  ir_codegen.py       — Emit while() in C
  backends/spirv.py   — Skip extraction (same as frame loop)

structured/
  main.ergo            — Replace DO FRAME = 1, DEFAULT_FRAMES with DO WHILE (.TRUE.)
```
