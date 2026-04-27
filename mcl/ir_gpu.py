"""GPU kernel extraction pass.

Walks an IRModule and identifies DO loops (or portions of loops) that
can be lowered to GPU kernels.

Dependence classification (refinements of FLOW):
  INJECTIVE  — compiler proves writes are injective (affine index, no division).
               Fully parallel, no synchronization.
  FLOW       — data-dependent index (array LOAD), asserted non-colliding.
               Parallel by contract (gather/scatter kernel).
  SHIFT(k)   — same-array read/write at known constant offset k.
               Cross-iteration dependency; sequential or wavefront.
  REDUCTION  — scalar accumulator (sum, product, min/max).
               Staged parallel reduction.
  SCATTER    — known or possible write collisions.
               Sequential (default) or atomic (--fast-math).

Execution mapping:
  INJECTIVE  → GPU kernel (1 thread per iteration)
  FLOW       → GPU kernel (gather/scatter)
  SHIFT(k)   → CPU loop (wavefront future)
  REDUCTION  → CPU loop (staged reduce future)
  SCATTER    → CPU loop (atomic future)

When a loop body contains both extractable and non-extractable sections,
the pass splits the body at the boundary. The extractable prefix becomes
a GPU kernel; the suffix remains a CPU loop.

Extraction rules:
  1. Array writes have INJECTIVE or FLOW index (no SCATTER/SHIFT).
  2. No I/O (PRINT, WRITE, FLUSH).
  3. No ALLOCATE/DEALLOCATE.
  4. No cross-iteration read-write aliasing.
  5. All referenced arrays have known shape.
  6. No scalar accumulators.
  7. No nested loops.

Per-iteration working scalars (written then read within one iteration)
are allowed — they become per-thread registers on GPU.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .ir import (
    IRModule, IRVar, IRBlock, IRIf, IRLoop, IRSelect,
    IRInst, IRConst, IRRef, IRType, StorageClass, Op, Operand,
)
from .ir_affine import (
    AffineExpr, LoopDependence, extract_affine, detect_shift,
    check_bounds, _operand_to_affine,
)


@dataclass
class KernelPlan:
    """Description of a single extracted GPU kernel."""
    kernel_id: int                     # sequential kernel index
    loop: IRLoop                       # the original IR loop (or synthetic)
    loop_index: int                    # position in parent body list
    arrays_read: set[str]              # arrays loaded inside the kernel
    arrays_written: set[str]           # arrays stored inside the kernel
    scalars_read: set[str]             # scalar variables/parameters read
    scalars_local: set[str]            # per-iteration working scalars (-> registers)
    loop_var: str                      # loop induction variable name
    loop_bound: Operand                # upper bound (N)
    source_line: int                   # source line for diagnostics
    dependence: LoopDependence = LoopDependence.INJECTIVE  # classification
    shift_k: int | None = None         # shift distance (only for SHIFT)
    split_from: int | None = None      # if split, source line of original loop
    is_partial: bool = False           # True if this is a flow prefix of a split
    atomic_arrays: set[str] = field(default_factory=set)  # arrays needing atomic ops


@dataclass
class GPUPlan:
    """Result of kernel extraction analysis on a module."""
    kernels: list[KernelPlan] = field(default_factory=list)
    rejections: list[tuple[int, str]] = field(default_factory=list)  # (line, reason)
    warnings: list[tuple[int, str]] = field(default_factory=list)    # (line, message)
    fusions: list[tuple[int, int, int]] = field(default_factory=list)  # (k1_id, k2_id, fused_id)


# I/O and memory ops that disqualify a body item.
# ZERO (memset) is bulk — it zeros an entire array, not one element
# per thread, so it cannot be a per-element kernel item.
_DISQUALIFYING_OPS = {Op.PRINT, Op.WRITE, Op.FLUSH, Op.ALLOC, Op.FREE,
                      Op.CALL, Op.CALL_VOID, Op.STOP, Op.ZERO}


def _resolve_bound(op: Operand, param_values: dict[str, int]) -> int | None:
    """Resolve a loop bound operand to a concrete integer.

    Returns the integer value if the bound is a literal constant or a
    PARAMETER with a known value. Returns None otherwise.
    """
    if isinstance(op, IRConst) and isinstance(op.value, int):
        return op.value
    if isinstance(op, IRRef) and op.name in param_values:
        return param_values[op.name]
    return None


def _dep_rank(dep: LoopDependence) -> int:
    """Ordering for dependence classes: higher = more restrictive."""
    return {
        LoopDependence.INJECTIVE: 0,
        LoopDependence.FLOW: 1,
        LoopDependence.SHIFT: 3,
        LoopDependence.REDUCTION: 4,
        LoopDependence.SCATTER: 5,
    }[dep]

# Loop-invariant names (PARAMETERs, STATIC scalars), set by extract_kernels
_module_invariants: set[str] = set()


def promote_locals(module: IRModule) -> list[str]:
    """Pre-pass: promote leaked locals to buffer arrays.

    When a loop body has a parallelizable flow prefix and a structural
    suffix, but locals computed in the prefix are read by the suffix
    (blocking extraction), this pass:

      1. Adds buffer arrays (SCALAR_BUF) to module.main_locals
      2. Appends STORE instructions at the end of the flow prefix
         to write each local into its buffer at the loop index
      3. Replaces scalar reads in the structural suffix with LOAD
         instructions from the buffer arrays
      4. Splits the loop into two separate loops in the parent body

    Returns a list of diagnostic messages.
    """
    diags: list[str] = []
    _temp_counter = [90000]  # high base to avoid collisions

    def _fresh(prefix: str = "t") -> str:
        _temp_counter[0] += 1
        return f"_{prefix}_{_temp_counter[0]}"

    # Build lookup tables
    array_shapes: dict[str, tuple] = {}
    var_types: dict[str, IRType] = {}
    for g in module.globals:
        var_types[g.name] = g.type
        if g.shape:
            array_shapes[g.name] = g.shape
    for v in module.main_locals:
        var_types[v.name] = v.type
        if v.shape:
            array_shapes[v.name] = v.shape

    def _try_promote(items: list, outer_loop_vars: set[str] = frozenset()):
        """Walk items, find loops that need promotion, transform in place."""
        # We may insert new loops, so iterate by index and adjust
        i = 0
        while i < len(items):
            item = items[i]
            if isinstance(item, IRIf):
                _try_promote(item.then_body, outer_loop_vars)
                if item.else_body:
                    _try_promote(item.else_body, outer_loop_vars)
                i += 1
                continue
            if isinstance(item, IRLoop):
                # Check if this loop needs and can benefit from promotion
                result = _analyze_for_promotion(
                    item, array_shapes, var_types, outer_loop_vars)
                if result is not None:
                    leaked, flow_items, split_idx, scalars_local = result
                    new_items = _do_promote(
                        item, leaked, flow_items, split_idx,
                        scalars_local, var_types)
                    if new_items:
                        # Replace original loop with promoted loops
                        items[i:i+1] = new_items
                        i += len(new_items)
                        continue
                # Recurse into unmodified loop body
                inner_vars = outer_loop_vars | {item.var}
                _try_promote(item.body, inner_vars)
                i += 1
                continue
            i += 1

    def _analyze_for_promotion(
        loop: IRLoop, array_shapes: dict, var_types: dict,
        outer_loop_vars: set[str]
    ) -> tuple[set[str], list, int, set[str]] | None:
        """Check if a loop would benefit from local promotion.

        Returns (leaked_locals, flow_items, split_idx, scalars_local)
        or None if promotion isn't applicable.
        """
        body = loop.body
        if len(body) < 2:
            return None

        # Need enough iterations for a kernel
        if isinstance(loop.end, IRConst) and isinstance(loop.start, IRConst):
            iters = loop.end.value - loop.start.value + 1
            if iters < 64:
                return None

        # First check if the full loop is already extractable
        ok, reason, _, _, _, _, _, _, _ = _check_loop(loop, array_shapes, var_types)
        if ok:
            return None  # already extractable, no promotion needed

        # Walk body to find split point (same logic as _try_split)
        flow_items: list = []
        split_idx = -1
        arrays_read: set[str] = set()
        arrays_written: set[str] = set()
        scalars_read: set[str] = set()
        scalars_written: set[str] = set()
        scalars_read_before_write: set[str] = set()

        for idx, item in enumerate(body):
            ar_before = set(arrays_read)
            aw_before = set(arrays_written)
            sr_before = set(scalars_read)
            sw_before = set(scalars_written)
            srbw_before = set(scalars_read_before_write)

            item_ok, item_reason = _check_item(
                item, loop.var, array_shapes, var_types,
                arrays_read, arrays_written, scalars_read,
                scalars_written, scalars_read_before_write)

            def _restore():
                arrays_read.clear(); arrays_read.update(ar_before)
                arrays_written.clear(); arrays_written.update(aw_before)
                scalars_read.clear(); scalars_read.update(sr_before)
                scalars_written.clear(); scalars_written.update(sw_before)
                scalars_read_before_write.clear()
                scalars_read_before_write.update(srbw_before)

            if not item_ok:
                split_idx = idx
                _restore()
                break

            new_written = scalars_written - sw_before
            new_accum = set()
            for s in new_written:
                if s.startswith("_t_") or s.startswith("_idx") or s == loop.var:
                    continue
                if s in scalars_read_before_write:
                    new_accum.add(s)
            if new_accum:
                split_idx = idx
                _restore()
                break

            flow_items.append(item)

        if split_idx < 0:
            return None

        # Need meaningful prefix
        real_items = sum(1 for it in flow_items
                         if isinstance(it, IRBlock) and it.insts
                         or isinstance(it, IRIf))
        if real_items < 3:
            return None

        # Check for outer loop var deps
        scalars_written.discard(loop.var)
        non_temp = {s for s in scalars_read if not s.startswith("_")}
        scalars_local = {s for s in scalars_written if not s.startswith("_")}
        input_scalars = non_temp - scalars_local
        input_scalars.discard(loop.var)
        _collect_scalar_refs(loop.start, input_scalars)
        _collect_scalar_refs(loop.end, input_scalars)
        _collect_scalar_refs(loop.step, input_scalars)
        if input_scalars & outer_loop_vars:
            return None

        # Check arrays have known shape
        for name in arrays_read | arrays_written:
            if name not in array_shapes:
                return None

        # Find leaked locals
        suffix_items = body[split_idx:]
        suffix_reads: set[str] = set()
        _collect_scalar_reads(suffix_items, suffix_reads)
        leaked = scalars_local & suffix_reads

        if not leaked:
            return None  # no leaked locals — _try_split can handle this

        return leaked, flow_items, split_idx, scalars_local

    def _do_promote(
        loop: IRLoop, leaked: set[str], flow_items: list,
        split_idx: int, scalars_local: set[str],
        var_types: dict
    ) -> list | None:
        """Perform the actual promotion: create buffer arrays, rewrite IR.

        Returns a list of new IR items to replace the original loop,
        or None if promotion can't proceed.
        """
        body = loop.body
        suffix_items = body[split_idx:]

        # Determine loop bound for array size
        if isinstance(loop.end, IRConst):
            buf_size = loop.end.value
        else:
            diags.append(
                f"  line {loop.line}: PROMOTE skipped: dynamic loop bound")
            return None

        # Check suffix for further complexity that would need multi-split
        suffix_has_further_leaks = False
        suffix_reads_from_leaked: set[str] = set()
        _collect_scalar_reads(suffix_items, suffix_reads_from_leaked)
        # All leaked locals will become buffer arrays, so those are resolved.
        # But check if the suffix itself has issues beyond the leaked locals.
        suffix_has_accum = False
        suffix_has_nested = False
        for sitem in suffix_items:
            if isinstance(sitem, IRLoop):
                suffix_has_nested = True
            if isinstance(sitem, IRBlock):
                for inst in sitem.insts:
                    if inst.op in _DISQUALIFYING_OPS:
                        suffix_has_further_leaks = True

        if suffix_has_nested or suffix_has_further_leaks or suffix_has_accum:
            diags.append(
                f"  line {loop.line}: PROMOTE: suffix has additional "
                f"extraction blockers (nested loop, I/O, or accumulator) "
                f"— further manual splitting may improve GPU coverage")

        # 1. Create buffer array declarations (skip if already exists)
        existing_names = {v.name for v in module.main_locals} | {g.name for g in module.globals}
        buf_names: dict[str, str] = {}  # original -> buffer name
        for name in sorted(leaked):
            buf_name = f"{name}_BUF"
            buf_names[name] = buf_name
            if buf_name not in existing_names:
                scalar_type = var_types.get(name, IRType.REAL)
                buf_var = IRVar(
                    name=buf_name,
                    type=scalar_type,
                    storage=StorageClass.LOCAL,
                    shape=(buf_size,),
                    line=loop.line,
                )
                module.main_locals.append(buf_var)
                array_shapes[buf_name] = (buf_size,)
                var_types[buf_name] = scalar_type
                existing_names.add(buf_name)
            diags.append(
                f"  line {loop.line}: PROMOTE {name} -> {buf_name}({buf_size})")

        # 2. Build the index temp for the flow prefix stores.
        #    We need _idx = loop_var - 1 for 0-based array access.
        #    Find an existing _idx temp in the flow prefix, or create one.
        idx_temp = None
        for fitem in flow_items:
            if isinstance(fitem, IRBlock):
                for inst in fitem.insts:
                    if (inst.op == Op.SUB and inst.result
                            and inst.result.startswith("_idx")):
                        idx_temp = inst.result
                        break
            if idx_temp:
                break

        store_block = IRBlock(label=_fresh("promote_store"), line=loop.line)

        if idx_temp is None:
            # Create our own index temp
            idx_temp = _fresh("idx")
            store_block.insts.append(IRInst(
                op=Op.SUB,
                result=idx_temp,
                args=[IRRef(loop.var, IRType.INTEGER),
                      IRConst(IRType.INTEGER, 1)],
                type=IRType.INTEGER,
                line=loop.line,
            ))

        # Add STORE for each leaked local
        for name in sorted(leaked):
            buf_name = buf_names[name]
            scalar_type = var_types.get(name, IRType.REAL)
            store_block.insts.append(IRInst(
                op=Op.STORE,
                args=[IRRef(name, scalar_type),
                      IRRef(idx_temp, IRType.INTEGER)],
                type=IRType.VOID,
                line=loop.line,
                meta={"array": buf_name},
            ))

        # 3. Build the flow prefix loop (with stores appended)
        flow_loop = IRLoop(
            var=loop.var,
            start=loop.start,
            end=loop.end,
            step=loop.step,
            body=flow_items + [store_block],
            line=loop.line,
        )

        # 4. Rewrite suffix: replace scalar reads of leaked locals
        #    with LOAD instructions from buffer arrays.
        suffix_items_new = _rewrite_suffix(
            suffix_items, buf_names, loop.var, var_types)

        # 5. Build the suffix loop
        suffix_loop = IRLoop(
            var=loop.var,
            start=loop.start,
            end=loop.end,
            step=loop.step,
            body=suffix_items_new,
            line=loop.line,
        )

        diags.append(
            f"  line {loop.line}: split into flow loop "
            f"({len(flow_items)} items + stores) + "
            f"suffix loop ({len(suffix_items)} items)")

        return [flow_loop, suffix_loop]

    def _rewrite_suffix(
        items: list, buf_names: dict[str, str],
        loop_var: str, var_types: dict
    ) -> list:
        """Deep-copy suffix items, replacing scalar reads of promoted
        locals with LOAD instructions from buffer arrays.

        For each reference to a promoted scalar, we insert a LOAD from
        the buffer array at the loop index and replace the reference
        with the loaded temp.
        """
        import copy
        new_items = []
        for item in items:
            if isinstance(item, IRBlock):
                new_block = IRBlock(label=item.label + "_promo",
                                    insts=[], line=item.line)
                # We need an index temp for LOADs. Create one per block.
                idx_temp = None
                for inst in item.insts:
                    new_inst = copy.copy(inst)
                    new_inst.args = list(inst.args)
                    new_inst.meta = dict(inst.meta)

                    # Check args for references to promoted scalars
                    for ai, arg in enumerate(new_inst.args):
                        if (isinstance(arg, IRRef)
                                and arg.name in buf_names):
                            buf_name = buf_names[arg.name]
                            scalar_type = var_types.get(
                                arg.name, IRType.REAL)

                            # Ensure we have an idx temp
                            if idx_temp is None:
                                idx_temp = _fresh("idx")
                                new_block.insts.append(IRInst(
                                    op=Op.SUB,
                                    result=idx_temp,
                                    args=[IRRef(loop_var, IRType.INTEGER),
                                          IRConst(IRType.INTEGER, 1)],
                                    type=IRType.INTEGER,
                                    line=inst.line,
                                ))

                            # Emit LOAD from buffer
                            load_temp = _fresh("ld")
                            new_block.insts.append(IRInst(
                                op=Op.LOAD,
                                result=load_temp,
                                args=[IRRef(idx_temp, IRType.INTEGER)],
                                type=scalar_type,
                                line=inst.line,
                                meta={"array": buf_name},
                            ))
                            # Replace the arg
                            new_inst.args[ai] = IRRef(
                                load_temp, scalar_type)

                    new_block.insts.append(new_inst)
                new_items.append(new_block)

            elif isinstance(item, IRIf):
                new_then = _rewrite_suffix(
                    item.then_body, buf_names, loop_var, var_types)
                new_else = None
                if item.else_body:
                    new_else = _rewrite_suffix(
                        item.else_body, buf_names, loop_var, var_types)
                # Check if the condition references a promoted scalar
                new_cond = item.condition
                if (isinstance(new_cond, IRRef)
                        and new_cond.name in buf_names):
                    # Need to load it — wrap in a block before the IF
                    # Actually, the condition is just a ref, we handle
                    # this at the block level above. Conditions that are
                    # promoted scalars are rare; skip for now.
                    pass
                new_items.append(IRIf(
                    condition=new_cond,
                    then_body=new_then,
                    else_body=new_else,
                    line=item.line,
                ))

            elif isinstance(item, IRLoop):
                import copy
                new_body = _rewrite_suffix(
                    item.body, buf_names, loop_var, var_types)
                new_items.append(IRLoop(
                    var=item.var,
                    start=item.start,
                    end=item.end,
                    step=item.step,
                    body=new_body,
                    line=item.line,
                ))

            elif isinstance(item, IRSelect):
                import copy
                new_cases = []
                for case_val, case_body in item.cases:
                    new_body = _rewrite_suffix(
                        case_body, buf_names, loop_var, var_types)
                    new_cases.append((case_val, new_body))
                new_items.append(IRSelect(
                    expr=item.expr,
                    cases=new_cases,
                    line=item.line,
                ))
            else:
                new_items.append(item)

        return new_items

    _try_promote(module.main_body)
    return diags


# ── Nested loop linearization ──────────────────────────────

def linearize_nested_loops(module: IRModule) -> list[str]:
    """Linearize eligible 2D nested loops into 1D loops for GPU extraction.

    Transforms:
        DO J = 1, NY
          DO I = 1, NX
            BODY using I, J
          ENDDO
        ENDDO

    Into:
        DO _K = 0, NX*NY - 1
          I = _K MOD NX + 1
          J = _K / NX + 1
          BODY using I, J
        ENDDO

    The linearized index _K is injective over the 2D domain, so the
    result is a single MAP kernel.

    Eligibility:
    - Exactly one inner loop (no other items in outer body)
    - Both loops have constant or PARAMETER bounds starting at 1
    - Inner loop body has no nested loops
    - No cross-iteration dependencies between outer iterations
      (inner body doesn't read/write based on outer var in a way
      that creates conflicts — checked by the normal classification)

    Returns diagnostic messages.
    """
    diags: list[str] = []

    # Collect PARAMETER values for resolving bounds
    param_values: dict[str, int] = {}
    for g in module.globals:
        if g.storage == StorageClass.PARAMETER and g.init_value is not None:
            if isinstance(g.init_value, int):
                param_values[g.name] = g.init_value

    _temp_counter = [0]

    def _fresh_temp(prefix: str = "_K") -> str:
        _temp_counter[0] += 1
        return f"{prefix}_{_temp_counter[0]}"

    def _resolve(op: Operand) -> int | None:
        if isinstance(op, IRConst) and isinstance(op.value, int):
            return op.value
        if isinstance(op, IRRef) and op.name in param_values:
            return param_values[op.name]
        return None

    def _try_linearize(items: list) -> list:
        new_items = []
        for item in items:
            if not isinstance(item, IRLoop):
                # Recurse into IFs
                if isinstance(item, IRIf):
                    item.then_body = _try_linearize(item.then_body)
                    if item.else_body:
                        item.else_body = _try_linearize(item.else_body)
                new_items.append(item)
                continue

            outer = item

            # Check: outer body is exactly one inner loop
            inner_loops = [b for b in outer.body if isinstance(b, IRLoop)]
            non_loops = [b for b in outer.body if not isinstance(b, IRLoop)]

            # Allow IRBlocks with no instructions (empty blocks from IR builder)
            real_non_loops = []
            for nl in non_loops:
                if isinstance(nl, IRBlock) and not nl.insts:
                    continue
                real_non_loops.append(nl)

            if len(inner_loops) != 1:
                # Multiple inner loops — can't linearize
                outer.body = _try_linearize(outer.body)
                new_items.append(outer)
                continue

            # Separate preamble (blocks before the inner loop) from the
            # inner loop. Preamble blocks compute things from the outer
            # loop var (e.g. KM, KP for stencil). These get included in
            # the linearized body after deriving the outer var from _K.
            preamble_items = []
            for idx_b, bl in enumerate(outer.body):
                if isinstance(bl, IRLoop):
                    break
                preamble_items.append(bl)

            if real_non_loops and not all(isinstance(r, IRBlock) for r in real_non_loops):
                # Non-block, non-loop items (IFs etc.) — can't linearize
                outer.body = _try_linearize(outer.body)
                new_items.append(outer)
                continue

            inner = inner_loops[0]

            # Check: no further nesting in inner body.
            # If inner has nested loops, recursively linearize inner
            # first, then retry the outer pair.
            if any(isinstance(bi, IRLoop) for bi in inner.body):
                outer.body = _try_linearize(outer.body)
                # After linearizing inner, retry: the inner loop
                # may now be a simple 1D loop (linearized 2D→1D).
                # Re-scan for preamble + inner loop structure.
                inner_loops2 = [b for b in outer.body if isinstance(b, IRLoop)]
                if len(inner_loops2) == 1:
                    inner = inner_loops2[0]
                    if not any(isinstance(bi, IRLoop) for bi in inner.body):
                        # Inner was linearized — rebuild preamble and
                        # fall through to linearize outer+inner
                        preamble_items = []
                        for bl in outer.body:
                            if isinstance(bl, IRLoop):
                                break
                            preamble_items.append(bl)
                    else:
                        new_items.append(outer)
                        continue
                else:
                    new_items.append(outer)
                    continue

            # Check: both loops have resolvable bounds
            outer_start = _resolve(outer.start)
            inner_start = _resolve(inner.start)
            # Accept either 1-based (original) or 0-based (linearized)
            if outer_start is None or inner_start is None:
                outer.body = _try_linearize(outer.body)
                new_items.append(outer)
                continue
            if outer_start not in (0, 1) or inner_start not in (0, 1):
                outer.body = _try_linearize(outer.body)
                new_items.append(outer)
                continue

            # Resolve extents
            outer_end = _resolve(outer.end)
            inner_end = _resolve(inner.end)

            if outer_end is None or inner_end is None:
                outer.body = _try_linearize(outer.body)
                new_items.append(outer)
                continue

            # Compute iteration counts
            outer_count = outer_end - outer_start + 1
            inner_count = inner_end - inner_start + 1
            total = inner_count * outer_count
            nx_op = IRConst(IRType.INTEGER, inner_count)
            ny_op = IRConst(IRType.INTEGER, outer_count)
            outer_var = outer.var   # J
            inner_var = inner.var   # I

            # Build the linearized loop
            k_var = _fresh_temp("_linK")

            # Preamble block: compute I and J from _K
            #   I = _K MOD NX + 1
            #   J = _K / NX + 1
            mod_temp = _fresh_temp("_mod")
            div_temp = _fresh_temp("_div")
            i_temp = _fresh_temp("_li")
            j_temp = _fresh_temp("_lj")

            preamble_insts = [
                IRInst(op=Op.MOD,
                       args=[IRRef(k_var, IRType.INTEGER), nx_op],
                       result=mod_temp, type=IRType.INTEGER,
                       line=inner.line),
                IRInst(op=Op.ADD,
                       args=[IRRef(mod_temp, IRType.INTEGER),
                             IRConst(IRType.INTEGER, inner_start)],
                       result=i_temp, type=IRType.INTEGER,
                       line=inner.line),
                IRInst(op=Op.DIV,
                       args=[IRRef(k_var, IRType.INTEGER), nx_op],
                       result=div_temp, type=IRType.INTEGER,
                       line=inner.line),
                IRInst(op=Op.ADD,
                       args=[IRRef(div_temp, IRType.INTEGER),
                             IRConst(IRType.INTEGER, outer_start)],
                       result=j_temp, type=IRType.INTEGER,
                       line=inner.line),
                # Copy to original variable names so body references work
                IRInst(op=Op.COPY,
                       args=[IRRef(i_temp, IRType.INTEGER)],
                       result=inner_var, type=IRType.INTEGER,
                       line=inner.line),
                IRInst(op=Op.COPY,
                       args=[IRRef(j_temp, IRType.INTEGER)],
                       result=outer_var, type=IRType.INTEGER,
                       line=inner.line),
            ]

            preamble = IRBlock(
                label=f"lin_preamble_{k_var}",
                insts=preamble_insts,
                line=inner.line)

            # Rewrite multi-dimensional STOREs/LOADs that use both I and J
            # to use the linear _K index directly.
            # GRID(I, J) with 2 index args → GRID(_K) with 1 index arg
            # This works because _K = (J-1)*NX + (I-1), which is exactly
            # the row-major linearization the C backend uses.
            rewritten_body = _rewrite_2d_indices(
                inner.body, inner_var, outer_var, k_var)

            # Build new loop body: preamble + outer preamble blocks + rewritten inner body.
            # Outer preamble blocks (e.g. KM/KP for stencil) compute values
            # from the outer loop var, which is now derived from _K.
            new_body = [preamble] + preamble_items + rewritten_body

            # Create the linearized 1D loop
            lin_loop = IRLoop(
                var=k_var,
                start=IRConst(IRType.INTEGER, 0),
                end=IRConst(IRType.INTEGER, total - 1),
                step=IRConst(IRType.INTEGER, 1),
                body=new_body,
                line=outer.line,
            )

            diags.append(
                f"LINEARIZED: 2D loop at line {outer.line} "
                f"({outer_var}=1..{outer_end}, {inner_var}=1..{inner_end}) "
                f"→ 1D loop _K=0..{total - 1}")

            new_items.append(lin_loop)

        return new_items

    module.main_body = _try_linearize(module.main_body)
    return diags


def _rewrite_2d_indices(body: list, inner_var: str, outer_var: str,
                        k_var: str) -> list:
    """Rewrite 2D STORE/LOAD indices to use linearized _K index.

    For stores like GRID(_idx_I, _idx_J) where _idx_I derives from the
    inner var and _idx_J from the outer var, replace both index args
    with a single _K reference. This makes the store look like a 1D
    linear write, which the affine extractor can classify as INJECTIVE.
    """
    new_body = []
    for item in body:
        if isinstance(item, IRBlock):
            new_insts = []
            for inst in item.insts:
                if inst.op == Op.STORE and len(inst.args) == 3:
                    # 2D store: args = [value, idx_dim0, idx_dim1]
                    # Replace with: args = [value, _K]
                    new_inst = IRInst(
                        op=Op.STORE,
                        args=[inst.args[0], IRRef(k_var, IRType.INTEGER)],
                        result=inst.result,
                        type=inst.type,
                        line=inst.line,
                        meta=dict(inst.meta),
                    )
                    new_insts.append(new_inst)
                elif inst.op == Op.STORE and len(inst.args) == 4:
                    # 3D store: args = [value, idx_dim0, idx_dim1, idx_dim2]
                    # Collapse inner 2 dims to _K, keep outer dim
                    new_inst = IRInst(
                        op=Op.STORE,
                        args=[inst.args[0], IRRef(k_var, IRType.INTEGER),
                              inst.args[3]],
                        result=inst.result,
                        type=inst.type,
                        line=inst.line,
                        meta=dict(inst.meta),
                    )
                    new_insts.append(new_inst)
                elif inst.op == Op.LOAD and len(inst.args) == 2:
                    # 2D load: args = [idx_dim0, idx_dim1]
                    # Replace with: args = [_K]
                    new_inst = IRInst(
                        op=Op.LOAD,
                        args=[IRRef(k_var, IRType.INTEGER)],
                        result=inst.result,
                        type=inst.type,
                        line=inst.line,
                        meta=dict(inst.meta),
                    )
                    new_insts.append(new_inst)
                elif inst.op == Op.LOAD and len(inst.args) == 3:
                    # 3D load: args = [idx_dim0, idx_dim1, idx_dim2]
                    # Collapse inner 2 dims to _K, keep outer dim
                    new_inst = IRInst(
                        op=Op.LOAD,
                        args=[IRRef(k_var, IRType.INTEGER), inst.args[2]],
                        result=inst.result,
                        type=inst.type,
                        line=inst.line,
                        meta=dict(inst.meta),
                    )
                    new_insts.append(new_inst)
                else:
                    new_insts.append(inst)
            new_body.append(IRBlock(
                label=item.label, insts=new_insts, line=item.line))
        elif isinstance(item, IRIf):
            new_then = _rewrite_2d_indices(
                item.then_body, inner_var, outer_var, k_var)
            new_else = None
            if item.else_body:
                new_else = _rewrite_2d_indices(
                    item.else_body, inner_var, outer_var, k_var)
            new_body.append(IRIf(
                condition=item.condition,
                then_body=new_then,
                else_body=new_else,
                line=item.line))
        else:
            new_body.append(item)
    return new_body


def extract_kernels(module: IRModule, allow_split: bool = True) -> GPUPlan:
    """Analyze module and identify extractable GPU kernels.

    Scans main_body, recursing into non-extractable loops to find
    extractable inner loops. When a loop body has a parallelizable
    prefix followed by a sequential suffix, splits the body and
    extracts the prefix as a kernel.
    """
    plan = GPUPlan()

    # Build lookup tables
    array_shapes: dict[str, tuple] = {}
    var_storage: dict[str, StorageClass] = {}
    var_types: dict[str, IRType] = {}

    for g in module.globals:
        var_types[g.name] = g.type
        var_storage[g.name] = g.storage
        if g.shape:
            array_shapes[g.name] = g.shape

    for v in module.main_locals:
        var_types[v.name] = v.type
        var_storage[v.name] = v.storage
        if v.shape:
            array_shapes[v.name] = v.shape

    kernel_id = [0]

    # Collect loop-invariant names (PARAMETERs and STATIC scalars without shape)
    # Stored module-level for access by _index_is_loop_var
    global _module_invariants
    _module_invariants = set()
    for g in module.globals:
        if g.storage == StorageClass.PARAMETER:
            _module_invariants.add(g.name)
        elif g.storage == StorageClass.STATIC and not g.shape:
            _module_invariants.add(g.name)

    # Build PARAMETER value map for bounds validation
    param_values: dict[str, int] = {}
    for g in module.globals:
        if g.storage == StorageClass.PARAMETER and g.init_value is not None:
            if isinstance(g.init_value, int):
                param_values[g.name] = g.init_value

    # Minimum iteration count to justify a GPU kernel launch.
    MIN_KERNEL_ITERS = 64

    def _scan(items: list, outer_loop_vars: set[str] = frozenset()):
        for idx, item in enumerate(items):
            if not isinstance(item, IRLoop):
                if isinstance(item, IRIf):
                    _scan(item.then_body, outer_loop_vars)
                    if item.else_body:
                        _scan(item.else_body, outer_loop_vars)
                continue

            # Try full loop extraction first
            ok, reason, arrays_r, arrays_w, scalars_r, scalars_l, \
                loop_dep, shift_k, atomic_arrs = \
                _check_loop(item, array_shapes, var_types,
                            param_values, plan.warnings)

            if ok:
                outer_deps = scalars_r & outer_loop_vars
                if outer_deps:
                    reason = (f"depends on outer loop var(s) "
                              f"{sorted(outer_deps)}")
                    ok = False

            if ok:
                if (isinstance(item.end, IRConst)
                        and isinstance(item.start, IRConst)):
                    iters = item.end.value - item.start.value + 1
                    if iters < MIN_KERNEL_ITERS:
                        reason = (f"too few iterations ({iters}) for GPU "
                                  f"kernel launch")
                        ok = False

            if ok:
                plan.kernels.append(KernelPlan(
                    kernel_id=kernel_id[0],
                    loop=item,
                    loop_index=idx,
                    arrays_read=arrays_r,
                    arrays_written=arrays_w,
                    scalars_read=scalars_r,
                    scalars_local=scalars_l,
                    loop_var=item.var,
                    loop_bound=item.end,
                    source_line=item.line,
                    dependence=loop_dep,
                    shift_k=shift_k,
                    atomic_arrays=atomic_arrs,
                ))
                kernel_id[0] += 1
                continue

            # Full extraction failed — try splitting the body into
            # a flow prefix (GPU) and structural suffix (CPU).
            split_ok = allow_split and _try_split(
                item, idx, array_shapes, var_types, outer_loop_vars,
                plan, kernel_id, MIN_KERNEL_ITERS)

            if not split_ok:
                plan.rejections.append((item.line, reason))

            # Recurse into this loop's body to find inner extractable
            # loops (e.g. inlined subroutine loops inside a frame loop)
            inner_vars = outer_loop_vars | {item.var}
            _scan(item.body, inner_vars)

    _scan(module.main_body)

    # Post-extraction: find _-prefixed refs used in kernel bodies but not
    # defined within them. These are inlined subroutine locals computed
    # in init blocks before the loop — they need to become push constants.
    for kernel in plan.kernels:
        _fixup_inlined_inputs(kernel, var_types, array_shapes)

    # Post-fixup: reject kernels that depend on outer loop variables.
    # The fixup may have added _-prefixed refs (like _STENCIL_GRID_J)
    # that are actually outer loop iteration variables, not constants.
    all_loop_vars = _collect_loop_vars(module.main_body)
    to_remove = []
    for kernel in plan.kernels:
        outer_deps = kernel.scalars_read & (all_loop_vars - {kernel.loop_var})
        if outer_deps:
            plan.rejections.append((
                kernel.source_line,
                f"depends on outer loop var(s) {sorted(outer_deps)} "
                f"(detected after _-prefix fixup)"))
            to_remove.append(kernel)
    for k in to_remove:
        plan.kernels.remove(k)

    return plan


def _collect_loop_vars(items: list) -> set[str]:
    """Collect all loop iteration variable names from an IR body."""
    vars_: set[str] = set()
    for item in items:
        if isinstance(item, IRLoop):
            vars_.add(item.var)
            vars_ |= _collect_loop_vars(item.body)
        elif isinstance(item, IRIf):
            vars_ |= _collect_loop_vars(item.then_body)
            if item.else_body:
                vars_ |= _collect_loop_vars(item.else_body)
    return vars_


def _fixup_inlined_inputs(kernel: KernelPlan, var_types: dict,
                          array_shapes: dict):
    """Add _-prefixed external refs to scalars_read.

    After inlining, subroutine parameters and locals computed before
    the kernel loop (e.g. _SIM_PHYSICS_STEP_DT) start with '_' and
    are skipped by _collect_scalar_refs. This pass finds them and adds
    them to scalars_read so the SPIRV backend creates push constants.
    """
    refs_used: set[str] = set()
    defs_in_body: set[str] = set()
    _collect_all_refs(kernel.loop.body, refs_used, defs_in_body)

    # Also count the loop variable as defined
    defs_in_body.add(kernel.loop_var)

    # External _-prefixed refs: used but not defined in body, not arrays
    external = set()
    for name in refs_used:
        if not name.startswith("_"):
            continue
        if name in defs_in_body:
            continue
        if name in array_shapes:
            continue
        external.add(name)

    if external:
        kernel.scalars_read |= external


def _collect_all_refs(items: list, refs: set[str], defs: set[str]):
    """Collect ALL variable refs and defs in a body (including _-prefixed)."""
    for item in items:
        if isinstance(item, IRBlock):
            for inst in item.insts:
                for arg in inst.args:
                    if isinstance(arg, IRRef):
                        refs.add(arg.name)
                if inst.result:
                    defs.add(inst.result)
        elif isinstance(item, IRIf):
            if isinstance(item.condition, IRRef):
                refs.add(item.condition.name)
            _collect_all_refs(item.then_body, refs, defs)
            if item.else_body:
                _collect_all_refs(item.else_body, refs, defs)
        elif isinstance(item, IRLoop):
            defs.add(item.var)
            if isinstance(item.start, IRRef):
                refs.add(item.start.name)
            if isinstance(item.end, IRRef):
                refs.add(item.end.name)
            _collect_all_refs(item.body, refs, defs)
        elif isinstance(item, IRSelect):
            if isinstance(item.expr, IRRef):
                refs.add(item.expr.name)
            for _, case_body in item.cases:
                _collect_all_refs(case_body, refs, defs)


# ── Loop fusion ────────────────────────────────────────────

def fuse_kernels(plan: GPUPlan, module: IRModule) -> list[str]:
    """Fuse adjacent compatible GPU kernels per Part 8.3 rules.

    Two adjacent kernels can be fused if:
    1. Same iteration space (identical bounds)
    2. Both INJECTIVE or both FLOW (no SHIFT/SCATTER)
    3. No aliasing: written arrays are distinct between the two kernels
    4. Producer-consumer: arrays written by kernel 1 and read by kernel 2
       use the same index (same loop variable)
    5. No side effects between the two loops in the original body

    Fusion merges the second kernel's loop body into the first, eliminates
    the intermediate array write (it becomes a register), and removes the
    second kernel from the plan.

    Returns diagnostic messages.
    """
    if len(plan.kernels) < 2:
        return []

    diags: list[str] = []
    fused_away: set[int] = set()  # kernel_ids that got absorbed
    i = 0

    while i < len(plan.kernels) - 1:
        k1 = plan.kernels[i]
        k2 = plan.kernels[i + 1]

        if k1.kernel_id in fused_away or k2.kernel_id in fused_away:
            i += 1
            continue

        # Check fusibility
        reason = _can_fuse(k1, k2, module)
        if reason is not None:
            i += 1
            continue

        # Fuse: merge k2 body into k1
        _do_fuse(k1, k2)
        fused_away.add(k2.kernel_id)
        plan.fusions.append((k1.kernel_id, k2.kernel_id, k1.kernel_id))
        diags.append(
            f"FUSED: kernel_{k1.kernel_id} (line {k1.source_line}) + "
            f"kernel_{k2.kernel_id} (line {k2.source_line}) → "
            f"kernel_{k1.kernel_id}")

        # Don't advance — try fusing k1 with the next kernel too
        plan.kernels.pop(i + 1)

        # But do continue checking
        continue

    return diags


def _bounds_match(k1: KernelPlan, k2: KernelPlan) -> bool:
    """Check if two kernels have the same iteration space."""
    # Same start
    s1, s2 = k1.loop.start, k2.loop.start
    e1, e2 = k1.loop.end, k2.loop.end

    def _eq(a: Operand, b: Operand) -> bool:
        if isinstance(a, IRConst) and isinstance(b, IRConst):
            return a.value == b.value and a.type == b.type
        if isinstance(a, IRRef) and isinstance(b, IRRef):
            return a.name == b.name
        return False

    return _eq(s1, s2) and _eq(e1, e2)


def _can_fuse(k1: KernelPlan, k2: KernelPlan,
              module: IRModule) -> str | None:
    """Check if two adjacent kernels can be fused.

    Returns None if fusible, or a reason string if not.
    """
    # 1. Same iteration space
    if not _bounds_match(k1, k2):
        return "different iteration bounds"

    # 2. Both must be INJECTIVE or FLOW (parallelizable)
    fusible_deps = {LoopDependence.INJECTIVE, LoopDependence.FLOW}
    if k1.dependence not in fusible_deps:
        return f"kernel 1 is {k1.dependence.value}"
    if k2.dependence not in fusible_deps:
        return f"kernel 2 is {k2.dependence.value}"

    # 3. Written arrays must be distinct (no write-write conflict)
    write_overlap = k1.arrays_written & k2.arrays_written
    if write_overlap:
        return f"both write to {sorted(write_overlap)}"

    # 4. Check producer-consumer: k1 writes, k2 reads same arrays
    # (This is the desired pattern — intermediate becomes register)
    # The check is: any array written by k1 that k2 reads must not
    # also be read by something else after k2 (we skip this for now —
    # conservative: allow fusion, keep the intermediate array write)

    # 5. No side effects between the loops in original body
    # Adjacent kernels in the plan came from adjacent loops in the body.
    # Check there's nothing between them (I/O, allocations, etc.)
    idx1 = k1.loop_index
    idx2 = k2.loop_index
    if idx2 != idx1 + 1:
        # Not strictly adjacent in the body — check items between them
        for idx in range(idx1 + 1, idx2):
            if idx < len(module.main_body):
                item = module.main_body[idx]
                if _has_side_effects(item):
                    return "side effects between loops"

    return None


def _has_side_effects(item) -> bool:
    """Check if an IR item has side effects (I/O, alloc, calls)."""
    if isinstance(item, IRBlock):
        for inst in item.insts:
            if inst.op in _DISQUALIFYING_OPS:
                return True
        return False
    if isinstance(item, IRIf):
        for sub in item.then_body:
            if _has_side_effects(sub):
                return True
        if item.else_body:
            for sub in item.else_body:
                if _has_side_effects(sub):
                    return True
        return False
    if isinstance(item, IRLoop):
        return True  # Conservative: any loop between kernels blocks fusion
    return False


def _do_fuse(k1: KernelPlan, k2: KernelPlan):
    """Merge k2's loop body into k1's loop body.

    After fusion, k1's loop contains both bodies. k2 should be removed
    from the plan.
    """
    # Merge tracking sets
    k1.arrays_read |= k2.arrays_read
    k1.arrays_written |= k2.arrays_written
    k1.scalars_read |= k2.scalars_read
    k1.scalars_local |= k2.scalars_local

    # Rename k2's loop variable to match k1's if different
    if k2.loop_var != k1.loop_var:
        _rename_var_in_body(k2.loop.body, k2.loop_var, k1.loop_var)

    # Append k2's body items to k1's loop body
    k1.loop.body.extend(k2.loop.body)


def _rename_var_in_body(body: list, old_name: str, new_name: str):
    """Rename a variable in all IR items recursively."""
    for item in body:
        if isinstance(item, IRBlock):
            for inst in item.insts:
                for i, arg in enumerate(inst.args):
                    if isinstance(arg, IRRef) and arg.name == old_name:
                        inst.args[i] = IRRef(new_name, arg.type)
                if inst.result == old_name:
                    inst.result = new_name
        elif isinstance(item, IRIf):
            if isinstance(item.condition, IRRef) and item.condition.name == old_name:
                item.condition = IRRef(new_name, item.condition.type)
            _rename_var_in_body(item.then_body, old_name, new_name)
            if item.else_body:
                _rename_var_in_body(item.else_body, old_name, new_name)
        elif isinstance(item, IRLoop):
            _rename_var_in_body(item.body, old_name, new_name)


_IO_OPS = {Op.PRINT, Op.WRITE, Op.FLUSH}


def _is_io_only(item) -> bool:
    """Check if an item fails flow-check solely because of I/O ops.

    Returns True if the item contains I/O but no other side effects
    (no STORE, no scalar writes that produce values, no nested loops,
    no ALLOC/FREE/CALL). These items can be safely skipped during
    extraction — they only read data and print it.
    """
    if isinstance(item, IRBlock):
        has_io = False
        for inst in item.insts:
            if inst.op in _IO_OPS:
                has_io = True
            elif inst.op in (Op.STORE, Op.ALLOC, Op.FREE,
                             Op.CALL, Op.CALL_VOID, Op.STOP):
                return False
        return has_io

    if isinstance(item, IRIf):
        # An IF that wraps I/O (e.g. IF MOD(IT,10)=0 THEN WRITE ENDIF)
        then_io = all(_is_io_only(it) or _is_pure_read(it)
                      for it in item.then_body)
        else_io = True
        if item.else_body:
            else_io = all(_is_io_only(it) or _is_pure_read(it)
                          for it in item.else_body)
        # At least one branch must actually contain I/O
        then_has = any(_is_io_only(it) for it in item.then_body)
        else_has = (item.else_body and
                    any(_is_io_only(it) for it in item.else_body))
        return (then_io and else_io and (then_has or else_has))

    return False


def _is_pure_read(item) -> bool:
    """Check if an item only reads (no writes, no side effects).

    Used to allow condition-check blocks before I/O (e.g. the MOD
    comparison block that gates a conditional WRITE).
    """
    if isinstance(item, IRBlock):
        for inst in item.insts:
            if inst.op in (_IO_OPS | {Op.STORE, Op.ALLOC, Op.FREE,
                                       Op.CALL, Op.CALL_VOID, Op.STOP}):
                return False
            # COPY that writes a named (non-temp) scalar is a data producer
            if inst.op == Op.COPY and inst.result:
                if not inst.result.startswith("_"):
                    return False
        return True
    return False


def _try_split(loop: IRLoop, loop_idx: int,
               array_shapes: dict, var_types: dict,
               outer_loop_vars: set[str],
               plan: GPUPlan, kernel_id: list[int],
               min_iters: int) -> bool:
    """Try to split a loop body into flow (GPU) + structural (CPU).

    Walks the body item-by-item. Each item is checked independently
    for flow-compatibility. The first item that fails marks the split
    point. The flow prefix must be non-trivial (>= 3 items) to be
    worth extracting.

    I/O-only items (WRITE/PRINT wrapped in conditionals) are skipped
    during the walk — they don't produce values, so flow items after
    them can still be extracted. The I/O items are reported as
    "stripped for GPU" so the user knows their debug output won't
    appear in the GPU kernel.

    Returns True if a split was made.
    """
    body = loop.body
    if len(body) < 2:
        return False

    # Check minimum iteration count
    if isinstance(loop.end, IRConst) and isinstance(loop.start, IRConst):
        iters = loop.end.value - loop.start.value + 1
        if iters < min_iters:
            return False

    # Walk items and find the split point.
    # An item fails flow-compatibility for two reasons:
    #   (a) It contains a disqualifying op (I/O, nested loop, etc.)
    #   (b) It introduces a cross-iteration accumulator
    # In both cases, this item and everything after it is structural.
    #
    # Exception: I/O-only items are skipped — they don't produce
    # values and can be left in a CPU loop alongside the kernel.
    flow_items: list = []
    io_skipped: list[int] = []  # source lines of skipped I/O items
    split_idx = -1
    split_reason = ""

    # Track state as we walk — these are cumulative across items
    arrays_read: set[str] = set()
    arrays_written: set[str] = set()
    scalars_read: set[str] = set()
    scalars_written: set[str] = set()
    scalars_read_before_write: set[str] = set()

    for i, item in enumerate(body):
        # Snapshot ALL mutable state before checking this item.
        ar_before = set(arrays_read)
        aw_before = set(arrays_written)
        sr_before = set(scalars_read)
        sw_before = set(scalars_written)
        srbw_before = set(scalars_read_before_write)

        item_ok, item_reason = _check_item(
            item, loop.var, array_shapes, var_types,
            arrays_read, arrays_written, scalars_read,
            scalars_written, scalars_read_before_write)

        def _restore():
            arrays_read.clear(); arrays_read.update(ar_before)
            arrays_written.clear(); arrays_written.update(aw_before)
            scalars_read.clear(); scalars_read.update(sr_before)
            scalars_written.clear(); scalars_written.update(sw_before)
            scalars_read_before_write.clear()
            scalars_read_before_write.update(srbw_before)

        if not item_ok:
            # Before giving up, check if this is an I/O-only item
            # that we can skip over.
            if _is_io_only(item):
                _restore()
                io_line = getattr(item, 'line', loop.line)
                io_skipped.append(io_line)
                continue

            split_idx = i
            split_reason = item_reason
            _restore()
            break

        # Check if this item introduced a new accumulator
        new_written = scalars_written - sw_before
        new_accum = set()
        for s in new_written:
            if s.startswith("_t_") or s.startswith("_idx") or s == loop.var:
                continue
            if s in scalars_read_before_write:
                new_accum.add(s)

        if new_accum:
            split_idx = i
            split_reason = (f"scalar accumulator(s) {sorted(new_accum)}")
            _restore()
            break

        flow_items.append(item)

    if split_idx < 0 and not flow_items:
        return False

    # Need a meaningful flow prefix — at least a few items of real work.
    real_items = sum(1 for it in flow_items
                     if isinstance(it, IRBlock) and it.insts
                     or isinstance(it, IRIf))
    if real_items < 3:
        return False

    # The flow prefix has no accumulators — we split before any appeared.
    scalars_written.discard(loop.var)

    # Check outer loop var dependencies
    non_temp_scalars = {s for s in scalars_read if not s.startswith("_")}
    scalars_local = {s for s in scalars_written
                     if not s.startswith("_")}
    input_scalars = non_temp_scalars - scalars_local
    input_scalars.discard(loop.var)

    _collect_scalar_refs(loop.start, input_scalars)
    _collect_scalar_refs(loop.end, input_scalars)
    _collect_scalar_refs(loop.step, input_scalars)

    outer_deps = input_scalars & outer_loop_vars
    if outer_deps:
        return False

    # Check arrays have known shape
    all_arrays = arrays_read | arrays_written
    for name in all_arrays:
        if name not in array_shapes:
            return False

    # Check that no locals computed in the flow prefix are read by
    # the structural suffix. These are per-thread GPU registers that
    # won't be available to the CPU loop.
    if split_idx >= 0:
        suffix_items = body[split_idx:]
        suffix_reads: set[str] = set()
        _collect_scalar_reads(suffix_items, suffix_reads)
        leaked_locals = scalars_local & suffix_reads
        if leaked_locals:
            plan.rejections.append((
                loop.line,
                f"SPLIT rejected: flow-prefix locals {sorted(leaked_locals)} "
                f"are read by structural suffix (GPU->CPU boundary crossing)"
            ))
            return False

    # Build the flow kernel — a synthetic loop containing only the
    # flow prefix items.
    flow_loop = IRLoop(
        var=loop.var,
        start=loop.start,
        end=loop.end,
        step=loop.step,
        body=flow_items,
        line=loop.line,
    )

    # Get the structural suffix line for reporting
    if split_idx >= 0:
        suffix_item = body[split_idx]
        suffix_line = getattr(suffix_item, 'line', loop.line)
    else:
        suffix_line = loop.line

    plan.kernels.append(KernelPlan(
        kernel_id=kernel_id[0],
        loop=flow_loop,
        loop_index=loop_idx,
        arrays_read=arrays_read,
        arrays_written=arrays_written,
        scalars_read=input_scalars,
        scalars_local=scalars_local,
        loop_var=loop.var,
        loop_bound=loop.end,
        source_line=loop.line,
        split_from=loop.line,
        is_partial=True,
    ))
    kernel_id[0] += 1

    # Report the split
    n_flow = len(flow_items)
    if split_idx >= 0:
        n_struct = len(body) - split_idx
        plan.rejections.append((
            loop.line,
            f"SPLIT at item {split_idx}/{len(body)}: "
            f"{n_flow} flow items -> kernel, "
            f"{n_struct} structural items remain on CPU "
            f"(first structural: {split_reason} at line {suffix_line})"
        ))
    elif io_skipped:
        # Entire loop extracted (minus I/O items)
        plan.rejections.append((
            loop.line,
            f"SPLIT: {n_flow} flow items -> kernel "
            f"(full loop extracted, I/O items remain on CPU)"
        ))

    # Report skipped I/O
    if io_skipped:
        lines_str = ", ".join(str(l) for l in io_skipped)
        plan.rejections.append((
            loop.line,
            f"I/O stripped for GPU at line(s) {lines_str} "
            f"— debug output runs in CPU loop only"
        ))

    return True


def _check_item(item, loop_var: str, array_shapes: dict,
                var_types: dict,
                arrays_read: set[str], arrays_written: set[str],
                scalars_read: set[str],
                scalars_written: set[str],
                scalars_read_before_write: set[str]
                ) -> tuple[bool, str]:
    """Check a single body item for flow-compatibility.

    Updates tracking sets in place. Returns (ok, reason).
    """
    if isinstance(item, IRBlock):
        for inst in item.insts:
            if inst.op in _DISQUALIFYING_OPS:
                return False, f"I/O or side-effect op '{inst.op.value}'"

            # Track read-before-write for accumulator detection
            for arg in inst.args:
                if isinstance(arg, IRRef):
                    if not (arg.name.startswith("_t_") or
                            arg.name.startswith("_idx")):
                        if arg.name not in scalars_written:
                            scalars_read_before_write.add(arg.name)

            if inst.op == Op.STORE:
                arr = inst.meta.get("array", "")
                arrays_written.add(arr)
                if not _index_is_loop_var(inst.args[1:], loop_var,
                                         insts=item.insts):
                    return False, f"array '{arr}' written at non-loop-var index"

            if inst.op == Op.LOAD:
                arr = inst.meta.get("array", "")
                arrays_read.add(arr)

            if inst.op == Op.ZERO:
                arr = inst.meta.get("array", "")
                if arr:
                    arrays_written.add(arr)

            if inst.op == Op.COPY and inst.result:
                scalars_written.add(inst.result)

            for arg in inst.args:
                _collect_scalar_refs(arg, scalars_read)

        return True, ""

    if isinstance(item, IRIf):
        ok, reason = _check_item_recursive(
            item.then_body, loop_var, array_shapes, var_types,
            arrays_read, arrays_written, scalars_read,
            scalars_written, scalars_read_before_write)
        if not ok:
            return False, reason
        if item.else_body:
            ok, reason = _check_item_recursive(
                item.else_body, loop_var, array_shapes, var_types,
                arrays_read, arrays_written, scalars_read,
                scalars_written, scalars_read_before_write)
            if not ok:
                return False, reason
        return True, ""

    if isinstance(item, IRLoop):
        return False, f"nested loop"

    if isinstance(item, IRSelect):
        return False, f"SELECT CASE"

    return True, ""


def _check_item_recursive(items: list, loop_var: str,
                           array_shapes: dict, var_types: dict,
                           arrays_read: set[str],
                           arrays_written: set[str],
                           scalars_read: set[str],
                           scalars_written: set[str],
                           scalars_read_before_write: set[str]
                           ) -> tuple[bool, str]:
    """Check a list of items for flow-compatibility."""
    for item in items:
        ok, reason = _check_item(
            item, loop_var, array_shapes, var_types,
            arrays_read, arrays_written, scalars_read,
            scalars_written, scalars_read_before_write)
        if not ok:
            return False, reason
    return True, ""


# ── Full-loop extraction ───────────────────────────────────


def _check_loop(loop: IRLoop, array_shapes: dict, var_types: dict,
                param_values: dict[str, int] | None = None,
                bounds_warnings: list | None = None
                ) -> tuple[bool, str, set[str], set[str], set[str], set[str],
                           LoopDependence, int | None, set[str]]:
    """Check whether a complete loop is GPU-extractable.

    Returns (ok, reason, arrays_read, arrays_written, scalars_read,
             scalars_local, dependence, shift_k).
    """
    _empty = False, "", set(), set(), set(), set(), LoopDependence.SCATTER, None, set()

    arrays_read: set[str] = set()
    arrays_written: set[str] = set()
    scalars_read: set[str] = set()
    loop_var = loop.var

    _collect_scalar_refs(loop.start, scalars_read)
    _collect_scalar_refs(loop.end, scalars_read)
    _collect_scalar_refs(loop.step, scalars_read)

    scalars_written: set[str] = set()
    scalars_read_before_write: set[str] = set()

    ok, reason = _check_body(loop.body, loop_var, array_shapes, var_types,
                             arrays_read, arrays_written, scalars_read,
                             scalars_written, scalars_read_before_write)

    # If rejected due to non-loop-var index, retry with scatter allowed.
    # This enables full extraction of scatter kernels with atomics.
    if not ok and "non-loop-var index" in reason:
        arrays_read.clear(); arrays_written.clear()
        scalars_read.clear(); scalars_written.clear()
        scalars_read_before_write.clear()
        _collect_scalar_refs(loop.start, scalars_read)
        _collect_scalar_refs(loop.end, scalars_read)
        _collect_scalar_refs(loop.step, scalars_read)
        ok, reason = _check_body(loop.body, loop_var, array_shapes, var_types,
                                 arrays_read, arrays_written, scalars_read,
                                 scalars_written, scalars_read_before_write,
                                 allow_scatter=True)

    if not ok:
        return False, reason, set(), set(), set(), set(), LoopDependence.SCATTER, None, set()

    scalars_written.discard(loop_var)

    accumulators = set()
    for s in scalars_written:
        # Skip pure SSA temps (_t_NNN, _idx_NNN) — these are single-use
        # within one iteration and never accumulate.
        if s.startswith("_t_") or s.startswith("_idx"):
            continue
        if s in scalars_read_before_write:
            accumulators.add(s)

    if accumulators:
        return (False,
                f"scalar accumulator(s) {sorted(accumulators)} "
                f"(cross-iteration dependency)",
                set(), set(), set(), set(), LoopDependence.REDUCTION, None, set())

    scalars_local = set()
    for s in scalars_written:
        if not s.startswith("_") and s not in accumulators:
            scalars_local.add(s)

    all_arrays = arrays_read | arrays_written
    for name in all_arrays:
        if name not in array_shapes:
            return (False, f"array '{name}' has unknown shape",
                    set(), set(), set(), set(), LoopDependence.SCATTER, None, set())

    scalars_read.discard(loop_var)
    scalars_read -= scalars_local

    # ── Dependence classification ──────────────────────────
    # Classify each STORE index; most restrictive wins.
    safe = globals().get('_module_invariants', set())
    loop_dep = LoopDependence.INJECTIVE  # best case
    shift_k: int | None = None

    store_exprs: dict[str, AffineExpr] = {}   # array_name → write AffineExpr
    store_deps: dict[str, LoopDependence] = {}  # array_name → store classification
    load_exprs: dict[str, list[AffineExpr]] = {}  # array_name → [read AffineExprs]
    arrays_loaded: set[str] = set()  # all arrays that appear in LOADs

    for item in loop.body:
        if not isinstance(item, IRBlock):
            continue
        for inst in item.insts:
            if inst.op == Op.STORE:
                arr = inst.meta.get("array", "")
                dep, expr = _classify_store_index(
                    inst.args[1:], loop_var, insts=item.insts, invariants=safe)
                store_deps[arr] = dep
                # Track worst classification
                if _dep_rank(dep) > _dep_rank(loop_dep):
                    loop_dep = dep
                if expr is not None:
                    store_exprs[arr] = expr
            elif inst.op == Op.LOAD:
                arr = inst.meta.get("array", "")
                arrays_loaded.add(arr)
                rexpr = _extract_load_index(
                    inst.args, loop_var, item.insts, safe)
                if rexpr is not None:
                    load_exprs.setdefault(arr, []).append(rexpr)

    # FLOW + read-modify-write of same array = SCATTER.
    # If the index is data-dependent and we both read and write the array,
    # we can't assume the reads and writes don't collide.
    for arr, dep in store_deps.items():
        if dep == LoopDependence.FLOW and arr in arrays_loaded:
            loop_dep = LoopDependence.SCATTER
            break

    # Check for shift dependencies: same array written and read at different offsets
    if loop_dep == LoopDependence.INJECTIVE:
        for arr, wexpr in store_exprs.items():
            if arr in load_exprs:
                for rexpr in load_exprs[arr]:
                    k = detect_shift(wexpr, rexpr, loop_var)
                    if k is not None and k != 0:
                        loop_dep = LoopDependence.SHIFT
                        shift_k = k
                        break
                if loop_dep == LoopDependence.SHIFT:
                    break

    # SHIFT loops are not GPU-extractable
    if loop_dep == LoopDependence.SHIFT:
        reason = (f"loop classified as {loop_dep.value}"
                  + (f" (k={shift_k})" if shift_k is not None else ""))
        return (False, reason, set(), set(), set(), set(), loop_dep, shift_k, set())

    # SCATTER loops are extractable with atomic operations.
    # Identify which arrays need atomics: those with non-injective
    # write indices (FLOW or SCATTER) that also appear in LOADs
    # (read-modify-write pattern).
    atomic_arrays: set[str] = set()
    if loop_dep == LoopDependence.SCATTER:
        for arr, dep in store_deps.items():
            if dep in (LoopDependence.FLOW, LoopDependence.SCATTER):
                if arr in arrays_loaded:
                    atomic_arrays.add(arr)

    # ── Bounds validation ──────────────────────────────────
    # When loop bounds and array sizes are compile-time constants
    # (or resolvable PARAMETERs), verify index expressions stay
    # within [1, SIZE(array)].
    if store_exprs and param_values is not None:
        loop_lower = _resolve_bound(loop.start, param_values)
        loop_upper = _resolve_bound(loop.end, param_values)

        if loop_lower is not None and loop_upper is not None:
            for arr, wexpr in store_exprs.items():
                if arr not in array_shapes:
                    continue
                shape = array_shapes[arr]
                # For 1D arrays, check against first (only) dimension
                if len(shape) == 1:
                    dim = shape[0]
                    # Resolve PARAMETER-named dimensions
                    if isinstance(dim, str):
                        arr_size = param_values.get(dim)
                    elif isinstance(dim, int):
                        arr_size = dim
                    else:
                        arr_size = None

                    if arr_size is not None:
                        ok_b, min_i, max_i = check_bounds(
                            wexpr, loop_var, loop_lower, loop_upper,
                            arr_size, param_values)
                        if not ok_b and bounds_warnings is not None:
                            bounds_warnings.append((
                                loop.line,
                                f"array '{arr}' index out of bounds: "
                                f"index range [{min_i}, {max_i}] vs "
                                f"array size {arr_size} "
                                f"(line {loop.line})"
                            ))

    return (True, "", arrays_read, arrays_written, scalars_read, scalars_local,
            loop_dep, shift_k, atomic_arrays)


def _check_body(items: list, loop_var: str, array_shapes: dict,
                var_types: dict,
                arrays_read: set[str], arrays_written: set[str],
                scalars_read: set[str],
                scalars_written: set[str],
                scalars_read_before_write: set[str],
                allow_scatter: bool = False) -> tuple[bool, str]:
    """Recursively check a loop body for extractability."""
    for item in items:
        if isinstance(item, IRBlock):
            for inst in item.insts:
                if inst.op in _DISQUALIFYING_OPS:
                    return False, f"disqualifying op '{inst.op.value}' at line {inst.line}"

                for arg in inst.args:
                    if isinstance(arg, IRRef):
                        # Track read-before-write for all refs (including
                        # _-prefixed inlined locals) to detect accumulators.
                        # Skip pure SSA temps (_t_, _idx_) as they're
                        # single-use per iteration.
                        if not (arg.name.startswith("_t_") or
                                arg.name.startswith("_idx")):
                            if arg.name not in scalars_written:
                                scalars_read_before_write.add(arg.name)

                if inst.op == Op.STORE:
                    arr = inst.meta.get("array", "")
                    arrays_written.add(arr)
                    if not _index_is_loop_var(inst.args[1:], loop_var,
                                             insts=item.insts):
                        if not allow_scatter:
                            return (False,
                                    f"array '{arr}' written at non-loop-var index (line {inst.line})")

                if inst.op == Op.LOAD:
                    arr = inst.meta.get("array", "")
                    arrays_read.add(arr)

                if inst.op == Op.ZERO:
                    arr = inst.meta.get("array", "")
                    if arr:
                        arrays_written.add(arr)

                if inst.op == Op.COPY and inst.result:
                    scalars_written.add(inst.result)

                for arg in inst.args:
                    _collect_scalar_refs(arg, scalars_read)

        elif isinstance(item, IRIf):
            ok, reason = _check_body(item.then_body, loop_var, array_shapes,
                                     var_types, arrays_read, arrays_written,
                                     scalars_read, scalars_written,
                                     scalars_read_before_write,
                                     allow_scatter)
            if not ok:
                return False, reason
            if item.else_body:
                ok, reason = _check_body(item.else_body, loop_var,
                                         array_shapes, var_types,
                                         arrays_read, arrays_written,
                                         scalars_read, scalars_written,
                                         scalars_read_before_write,
                                         allow_scatter)
                if not ok:
                    return False, reason

        elif isinstance(item, IRLoop):
            return False, f"nested loop at line {item.line}"

        elif isinstance(item, IRSelect):
            return False, f"SELECT CASE inside loop at line {item.line}"

    return True, ""


def _classify_store_index(index_args: list[Operand], loop_var: str,
                          insts: list | None = None,
                          invariants: set[str] | None = None
                          ) -> tuple[LoopDependence, AffineExpr | None]:
    """Classify a STORE index and extract its affine structure if possible.

    Returns (dependence_class, affine_expr_or_None).

    - INJECTIVE + AffineExpr: affine index with non-zero loop-var coefficient
    - FLOW + None: data-dependent index (array LOAD), no read-modify-write
    - SCATTER + None: non-affine, division, or constant index
    """
    if len(index_args) != 1:
        return LoopDependence.SCATTER, None
    arg = index_args[0]
    if not isinstance(arg, IRRef):
        return LoopDependence.SCATTER, None

    if insts is None:
        return LoopDependence.SCATTER, None

    # Build def map for this block
    defs: dict[str, IRInst] = {}
    for inst in insts:
        if inst.result:
            defs[inst.result] = inst

    safe = invariants if invariants is not None else globals().get('_module_invariants', set())

    # Try affine extraction
    expr = extract_affine(arg.name, loop_var, defs, safe)

    if expr is not None:
        if expr.is_injective(loop_var):
            return LoopDependence.INJECTIVE, expr
        else:
            # Zero loop-var coefficient = constant index = SCATTER
            return LoopDependence.SCATTER, expr

    # Affine extraction failed — check why.
    # If the index traces through an array LOAD, it's FLOW (data-dependent
    # remapping, asserted non-colliding). Otherwise it's SCATTER.
    if _index_has_load(arg.name, defs):
        return LoopDependence.FLOW, None
    return LoopDependence.SCATTER, None


def _extract_load_index(index_args: list[Operand], loop_var: str,
                        insts: list, invariants: set[str]
                        ) -> AffineExpr | None:
    """Extract AffineExpr for a LOAD index (for shift detection)."""
    if len(index_args) != 1:
        return None
    arg = index_args[0]
    if not isinstance(arg, IRRef):
        return None

    defs: dict[str, IRInst] = {}
    for inst in insts:
        if inst.result:
            defs[inst.result] = inst

    return extract_affine(arg.name, loop_var, defs, invariants)


def _index_has_load(name: str, defs: dict[str, IRInst],
                    depth: int = 0) -> bool:
    """Check if an index traces through an array LOAD (data-dependent)."""
    if depth > 20:
        return False
    if name not in defs:
        return False
    inst = defs[name]
    if inst.op == Op.LOAD:
        return True
    for arg in inst.args:
        if isinstance(arg, IRRef) and arg.name.startswith("_"):
            if _index_has_load(arg.name, defs, depth + 1):
                return True
    return False


def _index_is_loop_var(index_args: list[Operand], loop_var: str,
                       insts: list | None = None,
                       invariants: set[str] | None = None) -> bool:
    """Legacy compatibility wrapper — returns True for INJECTIVE or FLOW indices.

    Used by _check_body and _try_split which need a boolean check.
    INJECTIVE and FLOW are both extractable to GPU; SCATTER is not.
    """
    dep, _ = _classify_store_index(index_args, loop_var, insts, invariants)
    return dep in (LoopDependence.INJECTIVE, LoopDependence.FLOW)


def _collect_scalar_reads(items: list, reads: set[str]):
    """Recursively collect all scalar variables read in a list of IR items."""
    for item in items:
        if isinstance(item, IRBlock):
            for inst in item.insts:
                for arg in inst.args:
                    if isinstance(arg, IRRef) and not arg.name.startswith("_"):
                        reads.add(arg.name)
        elif isinstance(item, IRIf):
            if item.condition and isinstance(item.condition, IRRef):
                if not item.condition.name.startswith("_"):
                    reads.add(item.condition.name)
            _collect_scalar_reads(item.then_body, reads)
            if item.else_body:
                _collect_scalar_reads(item.else_body, reads)
        elif isinstance(item, IRLoop):
            _collect_scalar_reads(item.body, reads)
        elif isinstance(item, IRSelect):
            for _, case_body in item.cases:
                _collect_scalar_reads(case_body, reads)


def _collect_scalar_refs(op: Operand, scalars: set[str]):
    """Collect scalar variable references from an operand."""
    if isinstance(op, IRRef):
        if not op.name.startswith("_"):
            scalars.add(op.name)
