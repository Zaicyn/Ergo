# Next Session: Tune Ring Coupling + Run at Scale

## What's Done (all complete)

### RING_PREV / RING_NEXT intrinsics (steps 1-5)
- ir.py, ir_builder.py, spirv.py — full compiler pipeline
- OpGroupNonUniformShuffle with wrapping modular index `(lane ± 1) & 31`
- Validated on RTX 2060: lane 0 RING_PREV returns lane 31's value

### SORT_BY_GEN directive (steps 6-7)
- New directive: `SORT_BY_GEN FLAGS, POS_X, POS_Y, POS_Z, VEL_X, VEL_Y, VEL_Z, OMEGA_NAT`
- 7 compiler files: tokens, AST, parser, checker, IR, IR builder, GPU extraction
- 3 compiler-generated SPIRV kernels:
  - kernel_5 (COUNT_GEN): atomicAdd histogram[GEN], 256 threads/wg
  - kernel_6 (SCAN_GEN): Hillis-Steele exclusive prefix sum, 32 threads, 5 steps
  - kernel_7 (SCATTER_GEN): scatter all 8 arrays, 18 bindings, 256 threads/wg
- Pointer swap after scatter (d_X ↔ d_sort_X) — zero copy
- Called at census intervals in main.mcl

### Ring coupling physics (step 8)
- Section 15.5 in fluid_subs.mcl (after OMEGA accumulation, before position writeback)
- Metabolic exchange: RING_PREV/RING_NEXT on OMEGA, direction-gated by FLOW_W
- Phase lock: RING_NEXT on PH, restoring toward SEAM_STEP_PH spacing
- Re-clamp OMEGA to [0, OMEGA_MAX] after exchange
- K_PHASE_LOCK = 0.001 in constants.mcl

## What's Next

### Step 9: Tune and validate

1. **Run at 29M** — verify sort + ring coupling don't crash or degrade fps
2. **Profile** — check sort kernel times (should be ~1ms total at census intervals)
3. **Observe ring behavior** — does OMEGA flow along the Viviani curve as expected?
4. **Tune K_PHASE_LOCK** — too high = kills natural dynamics, too low = no coherence
5. **Verify conservation** — total OMEGA should be conserved minus decay losses
6. **Check crystal behavior** — do crystallized suns interact correctly with ring coupling?
   (They should be skipped — CYCLE fires before section 15.5)

### Potential issues to watch for

- **Sort at census intervals may be too infrequent** — if GEN changes faster than
  census period, warps de-align between sorts. Monitor ring coupling quality
  degradation over time.
- **First sort** — the initial unsorted state means ring coupling runs against random
  neighbors until the first census. Should be harmless (bounded by clamp) but
  may cause a visible transient.
- **NPART vs sorted count** — sort scatters NPART particles. If spawn adds particles
  between sorts, new particles land at array end unsorted. They participate in
  shuffle with whatever warp they land in. Acceptable — sort catches up at next census.

## Current Performance (before ring coupling + sort)

- Headless: 141 fps at 29M (7.1ms/frame)
- Render: 74 fps at 30M (13.5ms/frame)
- RTX 2060, f32, DEVICE_LOCAL buffers

Expected impact: ring coupling adds 3 shuffle ops per particle (register-only,
near-zero cost). Sort adds ~1ms every census interval (every 50-2000 frames).
Per-frame cost increase should be negligible.

## Build

```bash
./structured/build.sh
python -m mcl --target spirv --precision f32 --no-split -o galaxy_gpu galaxy_structured.mcl

# Render (strip VERIFY for no-oracle mode):
sed '/VERIFY/,/4250/d' galaxy_structured.mcl > /tmp/nonet.mcl
python -m mcl --target spirv --precision f32 --no-split --render -N 29000000 -M 30000000 -o galaxy_render /tmp/nonet.mcl

# Headless benchmark (5000 frames):
sed '/VERIFY/,/4250/d' galaxy_structured.mcl | sed 's/DEFAULT_FRAMES = 2147483647/DEFAULT_FRAMES = 5000/' > /tmp/bench.mcl
python -m mcl --target spirv --precision f32 --no-split -N 29000000 -M 30000000 -o galaxy_gpu /tmp/bench.mcl
ERGO_PROFILE=1 timeout 120 ./galaxy_gpu
```

## Key Files

```
structured/
  constants.mcl       — K_PHASE_LOCK, PFLAG_BANKED, phase encoding
  fluid_subs.mcl      — Physics kernel with ring coupling (section 15.5)
  waveguide_subs.mcl  — Crystal banking in scatter, crystal field in stencil
  main.mcl            — SORT_BY_GEN at census intervals

mcl/
  tokens.py           — KW_SORT_BY_GEN token
  ast_nodes.py        — SortByGenStmt AST node
  parser.py           — _parse_sort_by_gen()
  checker.py          — Array name validation
  ir.py               — Op.RING_PREV, Op.RING_NEXT, Op.SORT_BY_GEN
  ir_builder.py       — Intrinsic recognition + sort lowering
  ir_gpu.py           — SortByGenPlan, kernel extraction
  backends/spirv.py   — SubgroupShuffle + 3 sort kernels
  ir_codegen.py       — Sort dispatch + pointer swap

tests/
  gpu_ring_shuffle.mcl — Validates ring intrinsics on GPU
```
