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
               Spec Part 8.2/9.9 gate (wired): serialized on CPU
               by default. extract_kernels(gpu_fast_math=False)
               rejects SCATTER loops — full-loop and split-prefix
               classifications alike — so the host loop runs
               sequentially with bitwise-reproducible results.
               With gpu_fast_math=True the kernel is extracted
               with atomic_arrays populated; backends emit atomic
               operations and accumulation order is undefined
               (not bitwise identical to sequential execution).

Execution mapping:
  INJECTIVE  → GPU kernel (1 thread per iteration)
  FLOW       → GPU kernel (gather/scatter)
  SHIFT(k)   → CPU loop (wavefront future)
  REDUCTION  → GPU kernel (staged parallel reduction: per-thread
               values → workgroup tree combine in shared memory →
               per-group partials; host does the final ordered sum)
  SCATTER    → CPU loop (default); GPU kernel with atomics under
               --gpu-fast-math

When a loop body contains both extractable and non-extractable sections,
the pass splits the body at the boundary. The extractable prefix becomes
a GPU kernel; the suffix remains a CPU loop.

Extraction rules:
  1. Array writes have INJECTIVE or FLOW index (no SHIFT; SCATTER
     only when gpu_fast_math is on).
  2. No I/O (PRINT, WRITE, FLUSH).
  3. No ALLOCATE/DEALLOCATE.
  4. No cross-iteration read-write aliasing.
  5. All referenced arrays have known shape.
  6. Scalar accumulators only as a validatable sum-reduction pattern
     (acc := acc + expr; see _validate_reduction).
  7. No nested loops.

Per-iteration working scalars (written then read within one iteration)
are allowed — they become per-thread registers on GPU.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .ir import (
    IRModule, IRVar, IRBlock, IRIf, IRLoop, IRSelect, IRWhileLoop,
    IRInst, IRConst, IRRef, IRType, StorageClass, Op, Operand,
)
from .ir_affine import (
    AffineExpr, LoopDependence, extract_affine, detect_shift,
    check_bounds, _operand_to_affine, affine_add, affine_mul_const,
    SymbolKind,
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
    # REDUCTION kernels: name of the scalar accumulator (sum pattern
    # validated by _validate_reduction). None for non-reduction kernels.
    reduction_var: str | None = None
    # Segmented REDUCTION kernels: name of the REAL accumulator ARRAY
    # (ACC(TAB(I)) := ACC(TAB(I)) + expr, validated by
    # _validate_seg_reduction). Segments are padded so each workgroup
    # lies within one segment; the host combines partials per segment.
    reduction_array: str | None = None
    # Multi-accumulator REDUCTION kernels: ALL accumulators (the staged
    # reduce combines each per workgroup; partials buffer is laid out
    # [acc][workgroup]). Empty for non-reduction kernels; when set,
    # reduction_var holds the first entry for legacy consumers.
    reduction_vars: list = field(default_factory=list)
    # Parent body list holding this kernel's loop (object identity —
    # used by fusion's adjacency rule and by _do_fuse to remove the
    # absorbed loop). None for split kernels, whose synthetic flow loop
    # is not an item of any parent body (they never fuse).
    parent_body: list | None = field(default=None, repr=False, compare=False)


@dataclass
class SortByGenPlan:
    """Compiler-generated sort-by-GEN kernels."""
    arrays: list[str]              # arrays to permute together
    source_line: int               # source line of SORT_BY_GEN directive
    histogram_kernel_id: int = -1  # assigned during SPIRV generation
    scan_kernel_id: int = -1
    scatter_kernel_id: int = -1


@dataclass
class GPUPlan:
    """Result of kernel extraction analysis on a module."""
    kernels: list[KernelPlan] = field(default_factory=list)
    rejections: list[tuple[int, str]] = field(default_factory=list)  # (line, reason)
    warnings: list[tuple[int, str]] = field(default_factory=list)    # (line, message)
    fusions: list[tuple[int, int, int]] = field(default_factory=list)  # (k1_id, k2_id, fused_id)
    sort_plans: list[SortByGenPlan] = field(default_factory=list)


def _frame_kernel_info(module: IRModule, plan: GPUPlan) -> tuple[set[int], dict[int, int]]:
    """Kernel IDs dispatched inside batched frame loops, plus a map
    kernel_id -> source line of the frame loop that contains it.

    Mirrors IRCodeGen._frame_kernel_ids: a frame loop is an outermost
    loop in main_body that is not itself extracted but contains
    extracted kernels (also: while loops containing kernels)."""
    kernel_by_line = {k.source_line: k for k in plan.kernels}

    def contains_dispatch(items: list) -> bool:
        for item in items:
            if isinstance(item, IRLoop):
                if item.line in kernel_by_line:
                    return True
                if contains_dispatch(item.body):
                    return True
            elif isinstance(item, IRWhileLoop):
                if contains_dispatch(item.body):
                    return True
            elif isinstance(item, IRIf):
                if contains_dispatch(item.then_body):
                    return True
                if item.else_body and contains_dispatch(item.else_body):
                    return True
        return False

    def collect(items: list, ids: set[int], loop_line: int,
                kline: dict[int, int]):
        for item in items:
            if isinstance(item, IRLoop):
                k = kernel_by_line.get(item.line)
                if k:
                    ids.add(k.kernel_id)
                    kline[k.kernel_id] = loop_line
                collect(item.body, ids, loop_line, kline)
            elif isinstance(item, IRWhileLoop):
                collect(item.body, ids, loop_line, kline)
            elif isinstance(item, IRIf):
                collect(item.then_body, ids, loop_line, kline)
                if item.else_body:
                    collect(item.else_body, ids, loop_line, kline)

    frame_ids: set[int] = set()
    kernel_frame_line: dict[int, int] = {}
    for item in module.main_body:
        if isinstance(item, IRLoop):
            if item.line not in kernel_by_line and contains_dispatch(item.body):
                collect(item.body, frame_ids, item.line, kernel_frame_line)
        elif isinstance(item, IRWhileLoop):
            if contains_dispatch(item.body):
                collect(item.body, frame_ids, item.line, kernel_frame_line)
    return frame_ids, kernel_frame_line


def compute_pingpong_arrays(module: IRModule, plan: GPUPlan) -> set[str]:
    """Arrays that get 2x ping-pong device buffers (single source of
    truth — used identically by the SPIRV backend and the host codegen).

    Ping-pong swaps read/write halves at frame_begin, so a read inside a
    frame sees the END-OF-PREVIOUS-FRAME state. That is only equivalent
    to sequential CPU semantics when no data flows BETWEEN kernels
    through the array within a frame. The rule is therefore:

      - exactly one kernel READS the array, and that kernel also WRITES
        it (all reads take the rd offset, all its writes the wr offset);
      - the read-write kernel is dispatched inside the frame loop (the
        offset swap lives at frame_begin; a kernel dispatched outside it
        would read the uninitialized half);
      - any OTHER kernel touching the array may only WRITE it, and only
        before the frame loop (a write-only access takes no offset and
        lands at element 0 — the half frame 1 reads);
      - all candidate arrays share one element count: the host swap
        state is a single global element offset pair, so arrays of
        differing sizes cannot participate (kept at 1x rather than
        silently wrong).
    """
    access: dict[str, list[KernelPlan]] = {}
    for k in plan.kernels:
        for a in k.arrays_read | k.arrays_written:
            access.setdefault(a, []).append(k)

    frame_ids, kernel_frame_line = _frame_kernel_info(module, plan)
    shapes: dict[str, tuple] = {}
    for g in module.globals:
        if g.shape:
            shapes[g.name] = g.shape
    for v in module.main_locals:
        if v.shape:
            shapes[v.name] = v.shape

    result: set[str] = set()
    for a, ks in access.items():
        readers = [k for k in ks if a in k.arrays_read]
        rw = [k for k in readers if a in k.arrays_written]
        if len(rw) != 1 or len(readers) != 1:
            continue
        k = rw[0]
        if k.kernel_id not in frame_ids:
            continue
        others = [x for x in ks if x is not k]
        if any(a in x.arrays_read for x in others):
            continue
        # Other writers must run before the frame loop holding the rw
        # kernel (init-time), so their offset-less writes land in the
        # half that frame's first iteration reads.
        fl = kernel_frame_line.get(k.kernel_id, 0)
        if any(x.source_line > fl for x in others):
            continue
        result.add(a)

    # One global offset pair => one element count for all pp arrays.
    size_classes = {shapes.get(a) for a in result}
    if len(size_classes) != 1 or None in size_classes:
        return set()
    return result


# I/O and memory ops that disqualify a body item.
# ZERO (memset) is bulk — it zeros an entire array, not one element
# per thread, so it cannot be a per-element kernel item.
_DISQUALIFYING_OPS = {Op.PRINT, Op.WRITE, Op.FLUSH, Op.ALLOC, Op.FREE,
                      Op.CALL, Op.CALL_VOID, Op.STOP, Op.ZERO,
                      Op.SORT_BY_GEN}


# Spec 8.2/9.9: SCATTER loops serialize on the CPU unless the user opts
# into GPU atomics. Shared by the full-loop and split-prefix gates.
_SCATTER_GATE_REASON = (
    "SCATTER loop: serialized on CPU by default "
    "(use --gpu-fast-math for GPU atomics)")


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

# Loop-invariant names (PARAMETERs), set by extract_kernels
# and promote_locals via _compute_module_invariants before any reader runs.
_module_invariants: set[str] = set()


def _compute_module_invariants(module: IRModule) -> set[str]:
    """Compute the loop-invariant names for affine index classification.

    Rule (identical everywhere it is used): global PARAMETERs only.
    STATIC scalars are NOT invariants — they are mutable file-scope
    state; treating them as constant made `A(S+I) := ...` with S
    updated per iteration falsely classify INJECTIVE. Computed fresh
    from the module on every entry point that (transitively) reads
    _module_invariants, so back-to-back compiles of different modules
    in one process never see stale or missing names.
    """
    invariants: set[str] = set()
    for g in module.globals:
        if g.storage == StorageClass.PARAMETER:
            invariants.add(g.name)
    return invariants


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

    # promote_locals runs before extract_kernels, so the invariant set
    # must be computed fresh here — otherwise the first compile in a
    # process sees an empty set and later compiles see the previous
    # module's names.
    global _module_invariants
    _module_invariants = _compute_module_invariants(module)

    _temp_counter = [90000]  # high base to avoid collisions
    _promo_seq = [1]  # monotonic buffer-name sequence (collision-proof)

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

    # PARAMETER values for resolving loop start/step
    param_values: dict[str, int] = {}
    for g in module.globals:
        if (g.storage == StorageClass.PARAMETER
                and isinstance(g.init_value, int)):
            param_values[g.name] = g.init_value

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
        ok, reason, _, _, _, _, _, _, _, _, _, _ = _check_loop(loop, array_shapes, var_types)
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

        # Buffer sizing (loop.end entries) and indexing (var - 1) are
        # only sound for a 1-based, unit-stride loop — anything else
        # stores out of bounds or miscounts the rows. (Checked here,
        # once promotion is known to apply, so loops that never needed
        # promotion don't get noisy rejections.)
        if (_resolve_bound(loop.start, param_values) != 1
                or _resolve_bound(loop.step, param_values) != 1):
            diags.append(
                f"  line {loop.line}: PROMOTE rejected: loop start/step "
                f"not resolvable to 1 — buffer sizing/indexing would be "
                f"wrong")
            return None

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

        # Reordering hazard (same rule as _try_split): the promoted
        # flow loop dispatches all its iterations before the suffix
        # loop runs on the CPU, so it must not read arrays the suffix
        # writes — those reads would observe pre-loop values where the
        # sequential program sees suffix-written ones.
        prefix_arr_reads, _ = _loop_array_accesses(flow_items)
        _, suffix_arr_writes = _loop_array_accesses(suffix_items)
        hazard = prefix_arr_reads & suffix_arr_writes
        if hazard:
            diags.append(
                f"  line {loop.line}: PROMOTE rejected: flow prefix "
                f"reads array(s) {sorted(hazard)} written by the suffix "
                f"(GPU prefix would run before the CPU suffix computes "
                f"them)")
            return None

        # Promotion rewrites only plain block-level READS of a leaked
        # local. A suffix WRITE of one (a read-modify-write carry would
        # keep landing on the CPU scalar while reads come from the
        # buffer), or a structural read the rewrite cannot reach (IF
        # condition, nested-loop bound, SELECT expression), makes the
        # promotion unsound — reject loudly.
        suffix_writes: set[str] = set()
        _collect_result_names(suffix_items, suffix_writes)
        written_leaks = leaked & suffix_writes
        if written_leaks:
            diags.append(
                f"  line {loop.line}: PROMOTE rejected: suffix writes "
                f"leaked local(s) {sorted(written_leaks)} — buffer "
                f"promotion cannot carry read-modify-write scalars")
            return None
        structural = _find_structural_scalar_refs(suffix_items, leaked)
        if structural:
            diags.append(
                f"  line {loop.line}: PROMOTE rejected: suffix reads "
                f"leaked local(s) {sorted(structural)} in an IF "
                f"condition, loop bound, or SELECT expression")
            return None

        # Check suffix for further complexity that would need multi-split
        suffix_has_further_leaks = False
        suffix_reads_from_leaked: set[str] = set()
        _collect_scalar_reads(suffix_items, suffix_reads_from_leaked)
        # All leaked locals will become buffer arrays, so those are resolved.
        # But check if the suffix itself has issues beyond the leaked locals.
        suffix_has_nested = False
        for sitem in suffix_items:
            if isinstance(sitem, IRLoop):
                suffix_has_nested = True
            if isinstance(sitem, IRBlock):
                for inst in sitem.insts:
                    if inst.op in _DISQUALIFYING_OPS:
                        suffix_has_further_leaks = True

        if suffix_has_nested or suffix_has_further_leaks:
            diags.append(
                f"  line {loop.line}: PROMOTE: suffix has additional "
                f"extraction blockers (nested loop or I/O) "
                f"— further manual splitting may improve GPU coverage")

        # 1. Create buffer array declarations. Names are counter-
        #    generated and always fresh: a user-declared X_BUF, or a
        #    buffer from an earlier promotion of the same local name
        #    (possibly sized for a different loop), must never be
        #    aliased — the mapping only ever points at storage this
        #    pass created.
        existing_names = ({v.name for v in module.main_locals}
                          | {g.name for g in module.globals})
        buf_names: dict[str, str] = {}  # original -> buffer name
        for name in sorted(leaked):
            buf_name = f"_promo_{name}_BUF_{_promo_seq[0]}"
            while buf_name in existing_names:
                _promo_seq[0] += 1
                buf_name = f"_promo_{name}_BUF_{_promo_seq[0]}"
            _promo_seq[0] += 1
            buf_names[name] = buf_name
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

        # 2. Build a FRESH index temp for the buffer stores: strictly
        #    loop_var - 1 — the same derivation _rewrite_suffix uses
        #    for the loads. Reusing an arbitrary _idx* temp from the
        #    prefix is unsound: those are <subscript> - 1 for whatever
        #    subscript came first (e.g. I+1-1 = I in a stencil), which
        #    stores the buffer rows shifted from where the suffix
        #    loads them.
        store_block = IRBlock(label=_fresh("promote_store"), line=loop.line)

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

        # 5. Build the suffix loop. It gets the first suffix item's
        #    line, NOT the original loop's line: host codegen keys
        #    extracted kernels by source line, so a suffix loop sharing
        #    the flow kernel's line would be misidentified as that
        #    kernel — dispatched on the GPU a second time instead of
        #    being emitted as the CPU remainder.
        suffix_line = (getattr(suffix_items[0], 'line', loop.line)
                       if suffix_items else loop.line)
        suffix_loop = IRLoop(
            var=loop.var,
            start=loop.start,
            end=loop.end,
            step=loop.step,
            body=suffix_items_new,
            line=suffix_line,
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

    Into (1-based, matching the kernel backends' i = gid + 1 convention):
        DO _K = 1, NX*NY
          _K0 = _K - 1
          I = _K0 MOD NX + 1
          J = _K0 / NX + 1
          BODY using I, J
        ENDDO

    _K0 is the column-major linear index (the locked Ergo convention,
    Spec Part 3): first dimension fastest, _K0 = (J-1)*NX + (I-1).

    Eligibility (all required; violations are reported, not folded):
    - Exactly one inner loop; any non-empty item AFTER the inner loop
      blocks linearization (such items run once per outer iteration and
      would otherwise be silently dropped)
    - Both loops have resolvable integer bounds and resolvable unit steps
    - Inner loop body has no nested loops
    - Nested-stencil acceptance (see _check_stencil_nest): every write is
      exactly at (I, J) — provably injective over the collapsed space;
      every read index is affine in (I, J); a written array may only be
      read at the same (I, J) (no cross-iteration reads of written
      arrays — SHIFT/flow patterns are rejected); 1D stores must not
      index by either loop variable; preamble blocks must not store to
      arrays
    - Multi-dimensional accesses are flattened to their column-major
      linear index (computed from the body's own index temps); the
      resulting loop is tagged `linearized` so extraction trusts the
      acceptance-time injectivity proof instead of re-classifying the
      (MOD/DIV-shaped) store index.

    Returns diagnostic messages.
    """
    diags: list[str] = []

    # Collect PARAMETER values for resolving bounds
    param_values: dict[str, int] = {}
    for g in module.globals:
        if g.storage == StorageClass.PARAMETER and g.init_value is not None:
            if isinstance(g.init_value, int):
                param_values[g.name] = g.init_value

    # Array shapes (globals + main locals) for the acceptance check and
    # the flat-index rewrite
    array_shapes: dict[str, tuple] = {}
    for g in module.globals:
        if g.shape:
            array_shapes[g.name] = g.shape
    for v in module.main_locals:
        if v.shape:
            array_shapes[v.name] = v.shape

    # Loop-invariant names for the affine index checks (same rule as
    # everywhere: global PARAMETERs only)
    invariants = _compute_module_invariants(module)

    _temp_counter = [0]

    def _fresh_temp(prefix: str = "_K") -> str:
        _temp_counter[0] += 1
        return f"{prefix}_{_temp_counter[0]}"

    # Const-evaluable INTEGER temp definitions (hoisted loop bounds like
    # NY-1, which the IR builder lowers to a temp before the loop).
    # Names defined more than once are ambiguous and resolve to None.
    _bound_defs: dict[str, IRInst] = {}
    _bound_ambig: set[str] = set()

    def _collect_bound_defs(items: list):
        for _item in items:
            if isinstance(_item, (IRLoop, IRWhileLoop)):
                _collect_bound_defs(_item.body)
                continue
            for _blk in _iter_blocks([_item]):
                for _inst in _blk.insts:
                    if not _inst.result or _inst.type != IRType.INTEGER:
                        continue
                    if _inst.result in _bound_defs:
                        _bound_ambig.add(_inst.result)
                    _bound_defs.setdefault(_inst.result, _inst)
    _collect_bound_defs(module.main_body)

    def _resolve(op: Operand, depth: int = 0) -> int | None:
        if depth > 10:
            return None
        if isinstance(op, IRConst) and isinstance(op.value, int):
            return op.value
        if isinstance(op, IRRef):
            if op.name in param_values:
                return param_values[op.name]
            if op.name in _bound_ambig:
                return None
            inst = _bound_defs.get(op.name)
            if inst is None or len(inst.args) != 2:
                return None
            a = _resolve(inst.args[0], depth + 1)
            b = _resolve(inst.args[1], depth + 1)
            if a is None or b is None:
                return None
            if inst.op == Op.ADD:
                return a + b
            if inst.op == Op.SUB:
                return a - b
            if inst.op == Op.MUL:
                return a * b
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

            # Items AFTER the inner loop run once per outer iteration,
            # after the inner loop completes — they cannot fold into the
            # collapsed body (previously they were silently deleted).
            inner_pos = next(i for i, b in enumerate(outer.body)
                             if b is inner)
            suffix_items = [b for b in outer.body[inner_pos + 1:]
                            if not (isinstance(b, IRBlock) and not b.insts)]
            if suffix_items:
                diags.append(
                    f"line {outer.line}: not linearized: "
                    f"{len(suffix_items)} item(s) follow the inner loop")
                outer.body = _try_linearize(outer.body)
                new_items.append(outer)
                continue

            # Check: both loops have resolvable bounds. Any integer start
            # works — the collapsed-loop preamble recovers I and J from
            # the linear index by adding the starts back.
            outer_start = _resolve(outer.start)
            inner_start = _resolve(inner.start)
            if outer_start is None or inner_start is None:
                outer.body = _try_linearize(outer.body)
                new_items.append(outer)
                continue

            # Steps must resolve to 1 — a strided or dynamic step does
            # not map onto the dense collapsed space.
            if _resolve(outer.step) != 1 or _resolve(inner.step) != 1:
                diags.append(
                    f"line {outer.line}: not linearized: "
                    f"non-unit or unresolvable loop step")
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

            # ── Nested-stencil acceptance ──
            # Conservative: every rule in _check_stencil_nest must pass;
            # anything else keeps the CPU loop with a named diagnostic.
            bad = _check_stencil_nest(
                inner.body, preamble_items, inner.var, outer.var,
                inner_start, outer_start, inner_end, outer_end,
                array_shapes, invariants, param_values)
            if bad is not None:
                diags.append(
                    f"line {outer.line}: not linearized: {bad}")
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

            # Build the linearized loop. The kernel backends derive the
            # loop variable as gid + 1 (1-based), so the collapsed loop
            # runs _K = 1..total; the 0-based linear index is _K0 = _K-1.
            k_var = _fresh_temp("_linK")
            k0_temp = _fresh_temp("_linK0")

            # Preamble block: compute I and J from _K
            #   _K0 = _K - 1
            #   I = _K0 MOD NX + inner_start
            #   J = _K0 / NX + outer_start
            mod_temp = _fresh_temp("_mod")
            div_temp = _fresh_temp("_div")
            i_temp = _fresh_temp("_li")
            j_temp = _fresh_temp("_lj")

            preamble_insts = [
                IRInst(op=Op.SUB,
                       args=[IRRef(k_var, IRType.INTEGER),
                             IRConst(IRType.INTEGER, 1)],
                       result=k0_temp, type=IRType.INTEGER,
                       line=inner.line),
                IRInst(op=Op.MOD,
                       args=[IRRef(k0_temp, IRType.INTEGER), nx_op],
                       result=mod_temp, type=IRType.INTEGER,
                       line=inner.line),
                IRInst(op=Op.ADD,
                       args=[IRRef(mod_temp, IRType.INTEGER),
                             IRConst(IRType.INTEGER, inner_start)],
                       result=i_temp, type=IRType.INTEGER,
                       line=inner.line),
                IRInst(op=Op.DIV,
                       args=[IRRef(k0_temp, IRType.INTEGER), nx_op],
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

            # Flatten every multi-dimensional STORE/LOAD to its
            # column-major linear index, computed from the body's own
            # index temps (sound for any accepted access form — the
            # acceptance check is what makes it safe).
            flat_body = [preamble] + preamble_items + inner.body
            _flatten_access_indices(flat_body, array_shapes, param_values,
                                    _fresh_temp)

            # Create the linearized 1D loop (1-based: _K = 1..total),
            # tagged so extraction trusts the acceptance-time injectivity
            # proof instead of re-classifying the flattened store index.
            lin_loop = IRLoop(
                var=k_var,
                start=IRConst(IRType.INTEGER, 1),
                end=IRConst(IRType.INTEGER, total),
                step=IRConst(IRType.INTEGER, 1),
                body=flat_body,
                line=outer.line,
                linearized=True,
            )

            diags.append(
                f"LINEARIZED: 2D loop at line {outer.line} "
                f"({outer_var}={outer_start}..{outer_end}, "
                f"{inner_var}={inner_start}..{inner_end}) "
                f"→ 1D loop _K=1..{total}")

            new_items.append(lin_loop)

        return new_items

    module.main_body = _try_linearize(module.main_body)
    return diags


def _cell_offset(index_args: list, iv: str, ov: str, istart: int,
                 ostart: int, defs: dict, invariants: set,
                 param_values: dict) -> tuple | None:
    """Affine (di, dj) offset of a 2D index vs the exact cell (iv, ov).

    Index args are 0-based temps (sub(expr, 1) form), so the affine
    constant of an exact (iv, ov) access is -1. Returns (di, dj,
    ci, cj) — subscript offsets and loop-var coefficients — or None
    when either dim is not affine with a single loop-variable symbol.
    """
    if len(index_args) != 2:
        return None
    e0 = extract_affine(index_args[0].name, iv, defs, invariants,
                        param_values=param_values) \
        if isinstance(index_args[0], IRRef) else None
    e1 = extract_affine(index_args[1].name, ov, defs, invariants,
                        param_values=param_values) \
        if isinstance(index_args[1], IRRef) else None
    if e0 is None or e1 is None:
        return None
    syms0 = {s.name for s in e0.coeffs}
    syms1 = {s.name for s in e1.coeffs}
    if syms0 - {iv} or syms1 - {ov}:
        return None
    ci = e0.loop_var_coeff(iv)
    cj = e1.loop_var_coeff(ov)
    return (e0.constant + 1, e1.constant + 1, ci, cj)


def _check_stencil_nest(body: list, preamble_items: list,
                        inner_var: str, outer_var: str,
                        inner_start: int, outer_start: int,
                        inner_end: int, outer_end: int,
                        array_shapes: dict, invariants: set,
                        param_values: dict) -> str | None:
    """Nested-stencil acceptance check. Returns a rejection reason
    (named rule) or None when the nest may be flattened to one kernel.

    Rules (all conservative — violations keep the CPU loop):
      1. Preamble: no array stores, no side-effecting ops (it would run
         inner_count times more often).
      2. Every WRITE is exactly at (inner_var, outer_var) — provably
         injective over the collapsed space (one cell per iteration).
      3. A WRITTEN array may only be READ at the same (inner, outer) —
         no cross-iteration reads of written arrays (SHIFT/flow forms
         are rejected; they need dependence handling).
      4. Every read index is affine in (inner, outer) with coefficient
         0 or 1 per dimension, and stays inside the declared extents
         for the whole loop range (verified statically).
      5. 1D stores must not index by either collapsed variable
         (duplicate writes across the nest); preamble rule 1 applies.
    """
    # Rule 1: preamble
    for block in _iter_blocks(preamble_items):
        for inst in block.insts:
            if inst.op == Op.STORE:
                return (f"preamble store to "
                        f"'{inst.meta.get('array', '')}'")
            if inst.op in _DISQUALIFYING_OPS:
                return f"preamble op '{inst.op.value}'"

    defs: dict[str, IRInst] = {}
    for block in _iter_blocks(body):
        for inst in block.insts:
            if inst.result:
                defs[inst.result] = inst

    written: dict[str, list] = {}
    read_idxs: dict[str, list] = {}
    for block in _iter_blocks(body):
        for inst in block.insts:
            if inst.op == Op.STORE:
                arr = inst.meta.get("array", "")
                idx_args = inst.args[1:]
                if len(idx_args) == 1:
                    # Rule 5 (stores): 1D store must not index by a
                    # collapsed variable (duplicate writes).
                    if _index_refs_loop_vars(idx_args[0], defs,
                                             inner_var, outer_var):
                        return (f"1D store to '{arr}' indexes by a "
                                f"collapsed loop variable (duplicate "
                                f"writes across the nest)")
                    continue
                written.setdefault(arr, []).append(idx_args)
            elif inst.op == Op.LOAD:
                arr = inst.meta.get("array", "")
                read_idxs.setdefault(arr, []).append(inst.args)
            elif inst.op in _DISQUALIFYING_OPS:
                return f"op '{inst.op.value}' in stencil body"
            elif inst.op == Op.ZERO:
                return (f"ZERO of '{inst.meta.get('array', '')}' in a "
                        f"nested loop (bulk op, not per-cell)")

    # Rule 2 + 3: writes exactly at (I, J); written arrays read only
    # at the same (I, J).
    for arr, idx_lists in written.items():
        shape = array_shapes.get(arr)
        if not shape or len(shape) != 2:
            return (f"written array '{arr}' is not 2D — flattened "
                    f"write injectivity unprovable")
        for idx in idx_lists:
            off = _cell_offset(idx, inner_var, outer_var,
                               inner_start, outer_start, defs,
                               invariants, param_values)
            if off is None:
                return (f"write to '{arr}' has a non-affine index — "
                        f"flattened write injectivity unprovable")
            di, dj, ci, cj = off
            if ci != 1 or cj != 1 or di != 0 or dj != 0:
                return (f"write to '{arr}' is not exactly at "
                        f"({inner_var}, {outer_var}) — cross-cell "
                        f"writes need SHIFT handling (rejected)")
        for ridx in read_idxs.get(arr, []):
            if len(ridx) == 1:
                return (f"1D read of written array '{arr}' inside the "
                        f"nest (untrackable access)")
            off = _cell_offset(ridx, inner_var, outer_var,
                               inner_start, outer_start, defs,
                               invariants, param_values)
            if off is None:
                return (f"read of written array '{arr}' has a "
                        f"non-affine index")
            di, dj, ci, cj = off
            if ci != 1 or cj != 1 or di != 0 or dj != 0:
                return (f"cross-iteration read of written array "
                        f"'{arr}' (offset {di:+d},{dj:+d}) — "
                        f"SHIFT/flow patterns rejected")

    # Rule 4: every read index affine, coeff 0/1, statically in-bounds.
    for arr, idx_lists in read_idxs.items():
        shape = array_shapes.get(arr)
        for ridx in idx_lists:
            if len(ridx) == 1:
                continue  # 1D load — safe (read-only)
            off = _cell_offset(ridx, inner_var, outer_var,
                               inner_start, outer_start, defs,
                               invariants, param_values)
            if off is None:
                return (f"read of '{arr}' has a non-affine index")
            di, dj, ci, cj = off
            if ci not in (0, 1) or cj not in (0, 1):
                return (f"read of '{arr}' has unsupported affine "
                        f"coefficients ({ci}, {cj})")
            if shape and len(shape) >= 2 and ci == 1 and cj == 1:
                d0 = shape[0] if isinstance(shape[0], int) else \
                    param_values.get(shape[0]) if isinstance(shape[0], str) else None
                d1 = shape[1] if isinstance(shape[1], int) else \
                    param_values.get(shape[1]) if isinstance(shape[1], str) else None
                if d0 is not None:
                    if inner_start + di < 1 or inner_end + di > d0:
                        return (f"read of '{arr}' leaves dimension 1 "
                                f"bounds [1, {d0}] over the loop range")
                if d1 is not None:
                    if outer_start + dj < 1 or outer_end + dj > d1:
                        return (f"read of '{arr}' leaves dimension 2 "
                                f"bounds [1, {d1}] over the loop range")
    return None


def _flatten_access_indices(body: list, array_shapes: dict,
                            param_values: dict, fresh_temp):
    """Rewrite every multi-dimensional LOAD/STORE in a linearized body
    to a single flat column-major linear index computed from the body's
    own index temps:
        2-D (i, j):    i + dim0 * j
        3-D (i, j, k): i + dim0 * (j + dim1 * k)
    (indices are already 0-based). Sound for any index form because it
    reuses the temps the body already computes; the acceptance check
    (_check_stencil_nest) is what makes flattening safe. Buffers are
    flat — this is exactly the layout both sides already use.
    """
    def dim_op(d):
        if isinstance(d, int):
            return IRConst(IRType.INTEGER, d)
        if isinstance(d, str) and d in param_values:
            return IRConst(IRType.INTEGER, param_values[d])
        if isinstance(d, str):
            return IRRef(d, IRType.INTEGER)
        return None

    for block in _iter_blocks(body):
        new_insts = []
        for inst in block.insts:
            if inst.op in (Op.LOAD, Op.STORE):
                arr = inst.meta.get("array", "")
                idx_args = (inst.args if inst.op == Op.LOAD
                            else inst.args[1:])
                shape = array_shapes.get(arr)
                if shape and len(shape) > 1 and len(idx_args) == len(shape):
                    dims = [dim_op(d) for d in shape]
                    if all(d is not None for d in dims):
                        # linear = idx0 + dim0*(idx1 [+ dim1*idx2])
                        acc = idx_args[-1]
                        for d_i in range(len(idx_args) - 1, 0, -1):
                            m = fresh_temp("_lmul")
                            new_insts.append(IRInst(
                                op=Op.MUL, result=m,
                                args=[acc, dims[d_i - 1]],
                                type=IRType.INTEGER, line=inst.line))
                            a = fresh_temp("_ladd")
                            new_insts.append(IRInst(
                                op=Op.ADD, result=a,
                                args=[idx_args[d_i - 1], IRRef(m, IRType.INTEGER)],
                                type=IRType.INTEGER, line=inst.line))
                            acc = IRRef(a, IRType.INTEGER)
                        if inst.op == Op.LOAD:
                            inst.args = [acc]
                        else:
                            inst.args = [inst.args[0], acc]
            new_insts.append(inst)
        block.insts = new_insts


def _loop_array_accesses(body: list) -> tuple[set[str], set[str]]:
    """Collect array names read and written by a list of IR items.

    Descends into IF/SELECT bodies (like the classifier) but not into
    nested loops. Returns (arrays_read, arrays_written).
    """
    reads: set[str] = set()
    writes: set[str] = set()
    for block in _iter_blocks(body):
        for inst in block.insts:
            if inst.op == Op.LOAD:
                reads.add(inst.meta.get("array", ""))
            elif inst.op == Op.STORE:
                writes.add(inst.meta.get("array", ""))
            elif inst.op == Op.ZERO:
                arr = inst.meta.get("array", "")
                if arr:
                    writes.add(arr)
    return reads, writes


def _index_refs_loop_vars(op: Operand, defs: dict[str, IRInst],
                          var1: str, var2: str, depth: int = 0) -> bool:
    """Check if an index operand's definition tree references either
    collapsed loop variable (directly or through temps, including the
    index arguments of a LOAD in the chain). Unresolvable chains count
    as referencing — the safe direction for linearization."""
    if depth > 20:
        return True
    if isinstance(op, IRConst):
        return False
    if not isinstance(op, IRRef):
        return True
    name = op.name
    if name == var1 or name == var2:
        return True
    inst = defs.get(name)
    if inst is None:
        # Not defined in the checked region (PARAMETER, outer-outer
        # loop var, scalar input) — invariant w.r.t. the collapsed pair.
        return False
    return any(_index_refs_loop_vars(arg, defs, var1, var2, depth + 1)
               for arg in inst.args)


def _affine_of_operand(op: Operand, loop_var: str, defs: dict[str, IRInst],
                       invariants: set[str]) -> AffineExpr | None:
    """Affine expression for a single index operand (const or ref)."""
    if isinstance(op, IRConst) and isinstance(op.value, int):
        return AffineExpr({}, op.value)
    if isinstance(op, IRRef):
        return extract_affine(op.name, loop_var, defs, invariants)
    return None


def _linearize_index_check(body: list, preamble: list,
                           inner_var: str, outer_var: str,
                           inner_start: int, outer_start: int,
                           invariants: set[str]) -> str | None:
    """Verify every array access in a linearization candidate collapses
    soundly onto the linear index. Returns a rejection reason or None.

    Rules (see linearize_nested_loops docstring):
    - preamble items must not store to arrays or run side-effecting
      ops (they would execute inner_count times more often)
    - 2D/3D accesses must index the first two dims as exactly
      (inner_var, outer_var) in order — same coefficient 1, constant
      -start, no other symbols
    - a 3rd index must not involve either collapsed variable
    - 1D stores must not index by either collapsed variable (the cell
      would be written once per row/column — a duplicate-write race);
      1D loads are safe (they observe the same values)
    """
    for block in _iter_blocks(preamble):
        for inst in block.insts:
            if inst.op == Op.STORE:
                return (f"preamble store to "
                        f"'{inst.meta.get('array', '')}'")
            if inst.op in _DISQUALIFYING_OPS:
                return f"preamble op '{inst.op.value}'"

    defs: dict[str, IRInst] = {}
    for block in _iter_blocks(body):
        for inst in block.insts:
            if inst.result:
                defs[inst.result] = inst
        for inst in block.insts:
            if inst.op == Op.STORE:
                arr = inst.meta.get("array", "")
                reason = _check_collapse_indices(
                    inst.args[1:], True, arr, inner_var, outer_var,
                    inner_start, outer_start, defs, invariants)
                if reason:
                    return reason
            elif inst.op == Op.LOAD:
                arr = inst.meta.get("array", "")
                reason = _check_collapse_indices(
                    inst.args, False, arr, inner_var, outer_var,
                    inner_start, outer_start, defs, invariants)
                if reason:
                    return reason
    return None


def _check_collapse_indices(index_args: list[Operand], is_store: bool,
                            arr: str, inner_var: str, outer_var: str,
                            inner_start: int, outer_start: int,
                            defs: dict[str, IRInst],
                            invariants: set[str]) -> str | None:
    """Check one STORE/LOAD's index list against the collapse pattern."""
    if len(index_args) == 1:
        if is_store and _index_refs_loop_vars(
                index_args[0], defs, inner_var, outer_var):
            return (f"1D store to '{arr}' indexes by a collapsed loop "
                    f"variable (duplicate writes across the nest)")
        return None

    if len(index_args) in (2, 3):
        e0 = _affine_of_operand(index_args[0], inner_var, defs, invariants)
        if (e0 is None or len(e0.coeffs) != 1
                or e0.loop_var_coeff(inner_var) != 1
                or e0.constant != -inner_start):
            return (f"access of '{arr}' is not exactly "
                    f"({inner_var}, {outer_var}) in order")
        e1 = _affine_of_operand(index_args[1], outer_var, defs, invariants)
        if (e1 is None or len(e1.coeffs) != 1
                or e1.loop_var_coeff(outer_var) != 1
                or e1.constant != -outer_start):
            return (f"access of '{arr}' is not exactly "
                    f"({inner_var}, {outer_var}) in order")
        if (len(index_args) == 3
                and _index_refs_loop_vars(index_args[2], defs,
                                          inner_var, outer_var)):
            return (f"third index of '{arr}' involves a collapsed "
                    f"loop variable")
        return None

    return f"access of '{arr}' has unsupported rank {len(index_args) + 1}"


def _rewrite_2d_indices(body: list, inner_var: str, outer_var: str,
                        k0_var: str) -> list:
    """Rewrite 2D STORE/LOAD indices to the 0-based linearized index.

    For stores like GRID(_idx_I, _idx_J) where _idx_I derives from the
    inner var and _idx_J from the outer var, replace both index args
    with a single _K0 reference. This makes the store look like a 1D
    linear write, which the affine extractor can classify as INJECTIVE.
    Only call this after _linearize_index_check has verified that every
    access really is (inner, outer) in order — the substitution is
    unconditional.
    """
    new_body = []
    for item in body:
        if isinstance(item, IRBlock):
            new_insts = []
            for inst in item.insts:
                if inst.op == Op.STORE and len(inst.args) == 3:
                    # 2D store: args = [value, idx_dim0, idx_dim1]
                    # Replace with: args = [value, _K0]
                    new_inst = IRInst(
                        op=Op.STORE,
                        args=[inst.args[0], IRRef(k0_var, IRType.INTEGER)],
                        result=inst.result,
                        type=inst.type,
                        line=inst.line,
                        meta=dict(inst.meta),
                    )
                    new_insts.append(new_inst)
                elif inst.op == Op.STORE and len(inst.args) == 4:
                    # 3D store: args = [value, idx_dim0, idx_dim1, idx_dim2]
                    # Collapse inner 2 dims to _K0, keep outer dim
                    new_inst = IRInst(
                        op=Op.STORE,
                        args=[inst.args[0], IRRef(k0_var, IRType.INTEGER),
                              inst.args[3]],
                        result=inst.result,
                        type=inst.type,
                        line=inst.line,
                        meta=dict(inst.meta),
                    )
                    new_insts.append(new_inst)
                elif inst.op == Op.LOAD and len(inst.args) == 2:
                    # 2D load: args = [idx_dim0, idx_dim1]
                    # Replace with: args = [_K0]
                    new_inst = IRInst(
                        op=Op.LOAD,
                        args=[IRRef(k0_var, IRType.INTEGER)],
                        result=inst.result,
                        type=inst.type,
                        line=inst.line,
                        meta=dict(inst.meta),
                    )
                    new_insts.append(new_inst)
                elif inst.op == Op.LOAD and len(inst.args) == 3:
                    # 3D load: args = [idx_dim0, idx_dim1, idx_dim2]
                    # Collapse inner 2 dims to _K0, keep outer dim
                    new_inst = IRInst(
                        op=Op.LOAD,
                        args=[IRRef(k0_var, IRType.INTEGER), inst.args[2]],
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
                item.then_body, inner_var, outer_var, k0_var)
            new_else = None
            if item.else_body:
                new_else = _rewrite_2d_indices(
                    item.else_body, inner_var, outer_var, k0_var)
            new_body.append(IRIf(
                condition=item.condition,
                then_body=new_then,
                else_body=new_else,
                line=item.line))
        else:
            new_body.append(item)
    return new_body


def extract_kernels(module: IRModule, allow_split: bool = True,
                    gpu_fast_math: bool = False) -> GPUPlan:
    """Analyze module and identify extractable GPU kernels.

    Scans main_body, recursing into non-extractable loops to find
    extractable inner loops. When a loop body has a parallelizable
    prefix followed by a sequential suffix, splits the body and
    extracts the prefix as a kernel.

    gpu_fast_math (spec 8.2/9.9): when False, any loop classifying
    SCATTER — as a full loop or as a split prefix — is rejected so it
    executes sequentially on the CPU. When True, SCATTER loops are
    extracted with atomic_arrays populated for atomic emission.
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

    # Collect loop-invariant names (PARAMETERs), fresh from this module.
    # Stored module-level for access by _index_is_loop_var and
    # _classify_store_index.
    global _module_invariants
    _module_invariants = _compute_module_invariants(module)

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
                # Check for SORT_BY_GEN directives in blocks
                if isinstance(item, IRBlock):
                    for inst in item.insts:
                        if inst.op == Op.SORT_BY_GEN:
                            plan.sort_plans.append(SortByGenPlan(
                                arrays=inst.meta["arrays"],
                                source_line=inst.line,
                            ))
                if isinstance(item, IRIf):
                    _scan(item.then_body, outer_loop_vars)
                    if item.else_body:
                        _scan(item.else_body, outer_loop_vars)
                continue

            # Try full loop extraction first
            ok, reason, arrays_r, arrays_w, scalars_r, scalars_l, \
                loop_dep, shift_k, atomic_arrs, red_var, red_arr, red_vars = \
                _check_loop(item, array_shapes, var_types,
                            param_values, plan.warnings)

            if ok:
                outer_deps = scalars_r & outer_loop_vars
                if outer_deps:
                    reason = (f"depends on outer loop var(s) "
                              f"{sorted(outer_deps)}")
                    ok = False

            if ok:
                # Resolve bounds through PARAMETERs too — a small
                # constant-bound loop (e.g. per-block zeroing, NB=21)
                # must not launch a kernel any more than a literal one.
                lo = _resolve_bound(item.start, param_values)
                hi = _resolve_bound(item.end, param_values)
                if lo is not None and hi is not None:
                    iters = hi - lo + 1
                    if iters < MIN_KERNEL_ITERS:
                        reason = (f"too few iterations ({iters}) for GPU "
                                  f"kernel launch")
                        ok = False

            if ok and loop_dep == LoopDependence.SCATTER and not gpu_fast_math:
                # Spec 8.2/9.9: SCATTER serializes on CPU by default.
                # The split path below may still salvage a non-SCATTER
                # prefix; the SCATTER items themselves stay on the CPU.
                reason = _SCATTER_GATE_REASON
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
                    reduction_var=red_var,
                    reduction_array=red_arr,
                    reduction_vars=red_vars or [],
                    parent_body=items,
                ))
                kernel_id[0] += 1
                continue

            # Full extraction failed — try splitting the body into
            # a flow prefix (GPU) and structural suffix (CPU).
            rej_before = len(plan.rejections)
            split_ok = allow_split and _try_split(
                item, idx, array_shapes, var_types, outer_loop_vars,
                plan, kernel_id, MIN_KERNEL_ITERS, param_values,
                gpu_fast_math=gpu_fast_math)

            if not split_ok:
                # _try_split reports a gated SCATTER prefix itself;
                # don't double-report the same loop.
                gated = any(
                    rl == item.line and rr == _SCATTER_GATE_REASON
                    for rl, rr in plan.rejections[rej_before:])
                if not gated:
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

    Two adjacent kernels can be fused if (ALL required, spec 8.3):
    1. Same iteration space (identical bounds and step)
    2. Both INJECTIVE or both FLOW (no SHIFT/SCATTER — no loop-carried
       dependencies in either loop)
    3. No aliasing: written arrays are distinct between the two kernels
    4. Local producer-consumer: every array written by kernel 1 and read
       by kernel 2 is read at the SAME affine index it was written
       (A(I) → A(I), never A(I-1) or A(I+1))
    5. No side effects between the two loops in their parent body
       (I/O, ALLOCATE/DEALLOCATE, calls with unknown effects)

    Plus the anti-dependence and scalar-carrier rules that keep the
    fused kernel identical to sequential execution:
    - kernel 1 reads ∩ kernel 2 writes must be empty
    - kernel 1 per-iteration locals ∩ kernel 2 scalar inputs must be
      empty (sequentially kernel 2 would read the LAST iteration's
      value; fused it would read the same-iteration value)
    - both loops must be items of the SAME parent body (kernels from
      different nests never fuse)

    Fusion merges the second kernel's loop body into the first, keeps
    the intermediate array write (conservative — elimination is a
    future optimization), removes the second kernel from the plan, and
    removes the second loop from the module so host codegen does not
    re-execute it on the CPU.

    Returns diagnostic messages.
    """
    if len(plan.kernels) < 2:
        return []

    # Analysis context for the affine producer-consumer check
    invariants = _compute_module_invariants(module)
    array_shapes: dict[str, tuple] = {}
    param_values: dict[str, int] = {}
    for g in module.globals:
        if g.shape:
            array_shapes[g.name] = g.shape
        if (g.storage == StorageClass.PARAMETER
                and isinstance(g.init_value, int)):
            param_values[g.name] = g.init_value
    for v in module.main_locals:
        if v.shape:
            array_shapes[v.name] = v.shape

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
        reason = _can_fuse(k1, k2, invariants, array_shapes, param_values)
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
    s1, s2 = k1.loop.start, k2.loop.start
    e1, e2 = k1.loop.end, k2.loop.end
    st1, st2 = k1.loop.step, k2.loop.step

    def _eq(a: Operand, b: Operand) -> bool:
        if isinstance(a, IRConst) and isinstance(b, IRConst):
            return a.value == b.value and a.type == b.type
        if isinstance(a, IRRef) and isinstance(b, IRRef):
            return a.name == b.name
        return False

    return _eq(s1, s2) and _eq(e1, e2) and _eq(st1, st2)


def _access_exprs(kernel: KernelPlan, invariants: set[str],
                  array_shapes: dict, param_values: dict | None
                  ) -> tuple[dict[str, list], dict[str, list]]:
    """Collect per-array write/read AffineExprs for a kernel's loop body.

    Returns (store_exprs, load_exprs): array name → list of affine
    expressions, one per STORE/LOAD, with None where the index is not
    affine (data-dependent). Same def-visibility walk as
    _classify_body_dependence: indices trace against the instructions
    seen up to the block holding the access.
    """
    store_exprs: dict[str, list] = {}
    load_exprs: dict[str, list] = {}
    seen_insts: list = []

    for block in _iter_blocks(kernel.loop.body):
        seen_insts.extend(block.insts)
        for inst in block.insts:
            if inst.op == Op.STORE:
                arr = inst.meta.get("array", "")
                _, expr = _classify_store_index(
                    inst.args[1:], kernel.loop_var, insts=seen_insts,
                    invariants=invariants,
                    shape=array_shapes.get(arr), param_values=param_values)
                store_exprs.setdefault(arr, []).append(expr)
            elif inst.op == Op.LOAD:
                arr = inst.meta.get("array", "")
                rexpr = _extract_load_index(
                    inst.args, kernel.loop_var, seen_insts, invariants,
                    shape=array_shapes.get(arr), param_values=param_values)
                load_exprs.setdefault(arr, []).append(rexpr)
    return store_exprs, load_exprs


def _same_affine_index(wexpr: AffineExpr, write_var: str,
                       rexpr: AffineExpr, read_var: str) -> bool:
    """True when a write and a read index are the same affine function
    of their respective loop variables (A(I) written, A(I) read)."""
    if wexpr.constant != rexpr.constant:
        return False
    if wexpr.loop_var_coeff(write_var) != rexpr.loop_var_coeff(read_var):
        return False
    w_params = {s.name: c for s, c in wexpr.coeffs.items()
                if s.kind == SymbolKind.PARAMETER}
    r_params = {s.name: c for s, c in rexpr.coeffs.items()
                if s.kind == SymbolKind.PARAMETER}
    return w_params == r_params


def _can_fuse(k1: KernelPlan, k2: KernelPlan,
              invariants: set[str], array_shapes: dict,
              param_values: dict | None) -> str | None:
    """Check if two adjacent kernels can be fused (spec 8.3).

    Returns None if fusible, or a reason string if not.
    """
    # 1. Same iteration space
    if not _bounds_match(k1, k2):
        return "different iteration bounds"

    # 2. Both must be INJECTIVE or FLOW (no loop-carried dependencies)
    fusible_deps = {LoopDependence.INJECTIVE, LoopDependence.FLOW}
    if k1.dependence not in fusible_deps:
        return f"kernel 1 is {k1.dependence.value}"
    if k2.dependence not in fusible_deps:
        return f"kernel 2 is {k2.dependence.value}"

    # 3. Written arrays must be distinct (no write-write conflict)
    write_overlap = k1.arrays_written & k2.arrays_written
    if write_overlap:
        return f"both write to {sorted(write_overlap)}"

    # Anti-dependence: k1 must not read anything k2 writes. Sequentially
    # k1's reads all happen before k2's first write; fused they interleave.
    anti = k1.arrays_read & k2.arrays_written
    if anti:
        return (f"anti-dependence: kernel 1 reads {sorted(anti)} "
                f"written by kernel 2")

    # Scalar producer-consumer: a per-iteration local of k1 read by k2
    # carries the LAST iteration's value sequentially, but would carry
    # the same-iteration value when fused — a different program.
    scalar_dep = k1.scalars_local & k2.scalars_read
    if scalar_dep:
        return (f"kernel 2 reads per-iteration local(s) "
                f"{sorted(scalar_dep)} of kernel 1")

    # Adjacency: both loops must be items of the SAME parent body.
    # Kernels from different nests (or split kernels, whose synthetic
    # loops have no parent) never fuse.
    p1, p2 = k1.parent_body, k2.parent_body
    if p1 is None or p2 is None or p1 is not p2:
        return "loops are not items of the same parent body"
    idx1 = next((i for i, x in enumerate(p1) if x is k1.loop), None)
    idx2 = next((i for i, x in enumerate(p2) if x is k2.loop), None)
    if idx1 is None or idx2 is None:
        return "kernel loop not found in its parent body"
    if idx2 < idx1:
        idx1, idx2 = idx2, idx1

    # 5. No side effects between the loops in the parent body
    for item in p1[idx1 + 1:idx2]:
        if _has_side_effects(item):
            return "side effects between loops"

    # 4. Local producer-consumer: every array k1 writes that k2 reads
    # must be read at the SAME affine index as written (A(I) → A(I)).
    # A stencil read (A(I-1), A(I+1)) or a data-dependent read makes
    # the fused kernel observe same-iteration values the sequential
    # program never has — reject.
    shared = k1.arrays_written & k2.arrays_read
    if shared:
        k1_stores, _ = _access_exprs(k1, invariants, array_shapes,
                                     param_values)
        _, k2_loads = _access_exprs(k2, invariants, array_shapes,
                                    param_values)
        for arr in sorted(shared):
            wexprs = k1_stores.get(arr, [])
            rexprs = k2_loads.get(arr, [])
            if not wexprs or not rexprs:
                return (f"producer-consumer index of '{arr}' not "
                        f"provably affine")
            for wexpr in wexprs:
                if wexpr is None:
                    return (f"producer-consumer write index of '{arr}' "
                            f"not affine")
            for rexpr in rexprs:
                if rexpr is None:
                    return (f"producer-consumer read index of '{arr}' "
                            f"not affine")
                if not any(_same_affine_index(wexpr, k1.loop_var,
                                              rexpr, k2.loop_var)
                           for wexpr in wexprs):
                    return (f"'{arr}' read at a different affine index "
                            f"than written (stencil)")

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

    After fusion, k1's loop contains both bodies. k2 is removed from
    the plan by the caller, and k2's loop is removed from its parent
    body here — otherwise host codegen would re-emit it as a CPU loop,
    re-executing k2's work with stale state and uploading over the
    GPU's fused results.
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

    # Remove k2's loop from its parent body (identity match — the IR
    # dataclasses are value-comparable, and a distinct but equal loop
    # must not be deleted).
    if k2.parent_body is not None:
        for i, x in enumerate(k2.parent_body):
            if x is k2.loop:
                del k2.parent_body[i]
                break


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
               min_iters: int,
               param_values: dict[str, int] | None = None,
               gpu_fast_math: bool = False) -> bool:
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

    # Check minimum iteration count (resolved through PARAMETERs —
    # same rule as the full-extraction gate in extract_kernels).
    lo = _resolve_bound(loop.start, param_values or {})
    hi = _resolve_bound(loop.end, param_values or {})
    if lo is not None and hi is not None:
        if hi - lo + 1 < min_iters:
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
            scalars_written, scalars_read_before_write, param_values)

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

    # Check that no locals computed in the flow prefix are read by the
    # structural suffix. Every prefix-defined name (named locals AND
    # _-prefixed inlined locals/temps — anything an instruction result
    # introduces) is a per-iteration device register the CPU suffix
    # will not have. The suffix is everything NOT in the flow prefix:
    # items at/after the split point plus any I/O-only items skipped
    # during the walk — all of it stays on the CPU.
    flow_ids = {id(it) for it in flow_items}
    suffix_items = [it for it in body if id(it) not in flow_ids]
    if suffix_items:
        prefix_defs: set[str] = set()
        for block in _iter_blocks(flow_items):
            for inst in block.insts:
                if inst.result:
                    prefix_defs.add(inst.result)
        prefix_defs.discard(loop.var)
        suffix_reads: set[str] = set()
        _collect_scalar_reads(suffix_items, suffix_reads)
        leaked_locals = prefix_defs & suffix_reads
        if leaked_locals:
            plan.rejections.append((
                loop.line,
                f"SPLIT rejected: flow-prefix locals {sorted(leaked_locals)} "
                f"are read by structural suffix (GPU->CPU boundary crossing)"
            ))
            return False

        # Reordering hazard: the GPU prefix dispatches all its
        # iterations before the CPU suffix runs. A prefix read of an
        # array the suffix writes observes pre-loop values where the
        # sequential program sees suffix-written ones.
        _, suffix_arr_writes = _loop_array_accesses(suffix_items)
        reordered = arrays_read & suffix_arr_writes
        if reordered:
            plan.rejections.append((
                loop.line,
                f"SPLIT rejected: flow prefix reads array(s) "
                f"{sorted(reordered)} written by the structural suffix "
                f"(GPU prefix would run before the CPU suffix computes "
                f"them)"
            ))
            return False

    # Classify the flow prefix for real (Spec 9.5) — the split kernel
    # must not silently default to INJECTIVE. A prefix containing a
    # SHIFT pattern (e.g. A(I) := A(I-1)) has a cross-iteration
    # dependency and cannot be dispatched as a parallel kernel; a
    # SCATTER prefix ships with its atomic arrays identified.
    safe = globals().get('_module_invariants', set())
    flow_dep, flow_shift_k, flow_atomics, _ = _classify_body_dependence(
        flow_items, loop.var, safe, array_shapes, param_values)
    if flow_dep == LoopDependence.SHIFT:
        plan.rejections.append((
            loop.line,
            f"SPLIT rejected: flow prefix classified as SHIFT"
            + (f" (k={flow_shift_k})" if flow_shift_k is not None else "")
            + " — cross-iteration dependency cannot run as a parallel kernel"
        ))
        return False

    # Spec 8.2/9.9: a SCATTER prefix (e.g. read-modify-write through a
    # data-dependent index) serializes on the CPU unless the user opted
    # into GPU atomics.
    if flow_dep == LoopDependence.SCATTER and not gpu_fast_math:
        plan.rejections.append((loop.line, _SCATTER_GATE_REASON))
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
        dependence=flow_dep,
        shift_k=flow_shift_k,
        split_from=loop.line,
        is_partial=True,
        atomic_arrays=flow_atomics,
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
                scalars_read_before_write: set[str],
                param_values: dict[str, int] | None = None
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
                                         insts=item.insts,
                                         shape=array_shapes.get(arr),
                                         param_values=param_values):
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
            scalars_written, scalars_read_before_write, param_values)
        if not ok:
            return False, reason
        if item.else_body:
            ok, reason = _check_item_recursive(
                item.else_body, loop_var, array_shapes, var_types,
                arrays_read, arrays_written, scalars_read,
                scalars_written, scalars_read_before_write, param_values)
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
                           scalars_read_before_write: set[str],
                           param_values: dict[str, int] | None = None
                           ) -> tuple[bool, str]:
    """Check a list of items for flow-compatibility."""
    for item in items:
        ok, reason = _check_item(
            item, loop_var, array_shapes, var_types,
            arrays_read, arrays_written, scalars_read,
            scalars_written, scalars_read_before_write, param_values)
        if not ok:
            return False, reason
    return True, ""


# ── Full-loop extraction ───────────────────────────────────


def _check_loop(loop: IRLoop, array_shapes: dict, var_types: dict,
                param_values: dict[str, int] | None = None,
                bounds_warnings: list | None = None
                ) -> tuple[bool, str, set[str], set[str], set[str], set[str],
                           LoopDependence, int | None, set[str], str | None,
                           str | None, list | None]:
    """Check whether a complete loop is GPU-extractable.

    Returns (ok, reason, arrays_read, arrays_written, scalars_read,
             scalars_local, dependence, shift_k, atomic_arrays,
             reduction_var, reduction_array, reduction_vars).
    """
    _empty = False, "", set(), set(), set(), set(), LoopDependence.SCATTER, None, set(), None, None, None

    # Inc-2A: 64-bit integers are CPU-only. The backend would silently
    # treat an INT64 scalar/array as i32 (push constants, element type) —
    # reject loudly instead (shaders' i64 is reserved for HASH/RAND).
    def _has_int64(items) -> bool:
        for it in items:
            if isinstance(it, IRBlock):
                for inst in it.insts:
                    if inst.type == IRType.INT64:
                        return True
                    arr = inst.meta.get("array", "") if inst.meta else ""
                    if arr and var_types.get(arr) == IRType.INT64:
                        return True
                    for a in inst.args:
                        if isinstance(a, IRRef) and a.type == IRType.INT64:
                            return True
            elif isinstance(it, (IRLoop, IRWhileLoop)):
                if _has_int64(it.body):
                    return True
            elif isinstance(it, IRIf):
                if _has_int64(it.then_body):
                    return True
                if it.else_body and _has_int64(it.else_body):
                    return True
        return False
    if _has_int64(loop.body):
        return (False, "INTEGER*8 (int64) is CPU-only — not supported on "
                "GPU (Inc-2A)", set(), set(), set(), set(),
                LoopDependence.SCATTER, None, set(), None, None, None)

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
                             scalars_written, scalars_read_before_write,
                             param_values=param_values)

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
                                 allow_scatter=True,
                                 param_values=param_values)

    if not ok:
        return False, reason, set(), set(), set(), set(), LoopDependence.SCATTER, None, set(), None, None, None

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
        # REDUCTION: accept validatable sum-reduction patterns (one or
        # more accumulators) for staged GPU lowering; anything else
        # stays on the CPU.
        red_vars, red_reason = _validate_reductions(
            loop, accumulators, arrays_written, var_types)
        if red_vars is None:
            return (False,
                    f"scalar accumulator(s) {sorted(accumulators)} "
                    f"(cross-iteration dependency){red_reason}",
                    set(), set(), set(), set(), LoopDependence.REDUCTION,
                    None, set(), None, None, None)
        for acc in red_vars:
            scalars_read.discard(acc)
        scalars_read.discard(loop_var)
        for name in arrays_read:
            if name not in array_shapes:
                return (False, f"array '{name}' has unknown shape",
                        set(), set(), set(), set(), LoopDependence.SCATTER,
                        None, set(), None, None, None)
        return (True, "", arrays_read, set(), scalars_read, set(),
                LoopDependence.REDUCTION, None, set(), red_vars[0], None,
                red_vars)

    # Segmented REDUCTION: ACC(TAB(I)) := ACC(TAB(I)) + expr — one kernel
    # computes all segment sums at once. Each workgroup lies within one
    # (padded) segment and tree-combines as in the scalar staged reduce;
    # the host combines per segment in group order.
    seg_acc, seg_reason = _validate_seg_reduction(
        loop, arrays_read, arrays_written, array_shapes, var_types,
        param_values)
    if seg_acc is not None:
        scalars_read.discard(loop_var)
        for name in arrays_read:
            if name not in array_shapes:
                return (False, f"array '{name}' has unknown shape",
                        set(), set(), set(), set(), LoopDependence.SCATTER,
                        None, set(), None, None, None)
        arrays_read.discard(seg_acc)
        arrays_written.discard(seg_acc)
        return (True, "", arrays_read, set(), scalars_read, set(),
                LoopDependence.REDUCTION, None, set(), None, seg_acc, None)
    if seg_reason and bounds_warnings is not None:
        # Candidate that failed a V1 constraint — note why it fell back
        # to the normal (SCATTER/CPU) path.
        bounds_warnings.append((loop.line, seg_reason))

    scalars_local = set()
    for s in scalars_written:
        if not s.startswith("_") and s not in accumulators:
            scalars_local.add(s)

    all_arrays = arrays_read | arrays_written
    for name in all_arrays:
        if name not in array_shapes:
            return (False, f"array '{name}' has unknown shape",
                    set(), set(), set(), set(), LoopDependence.SCATTER,
                    None, set(), None, None, None)

    scalars_read.discard(loop_var)
    scalars_read -= scalars_local

    # ── Dependence classification ──────────────────────────
    # Classify each STORE index; most restrictive wins. Shared with
    # _try_split so split kernels get a real classification too.
    if getattr(loop, "linearized", False):
        # Nested-stencil linearization already proved write injectivity
        # over the collapsed space at acceptance time (writes exactly at
        # (I,J), reads of written arrays only at the same (I,J)); the
        # flattened store index is a computed linear form the affine
        # classifier cannot read. Everything else (legality, shapes,
        # accumulators) was checked above.
        return (True, "", arrays_read, arrays_written, scalars_read,
                scalars_local, LoopDependence.INJECTIVE, None, set(),
                None, None, None)
    safe = globals().get('_module_invariants', set())
    loop_dep, shift_k, atomic_arrays, store_exprs = \
        _classify_body_dependence(loop.body, loop_var, safe,
                                  array_shapes, param_values)

    # SHIFT loops are not GPU-extractable
    if loop_dep == LoopDependence.SHIFT:
        reason = (f"loop classified as {loop_dep.value}"
                  + (f" (k={shift_k})" if shift_k is not None else ""))
        return (False, reason, set(), set(), set(), set(), loop_dep,
                shift_k, set(), None, None, None)

    # ── Bounds validation ──────────────────────────────────
    # When loop bounds and array sizes are compile-time constants
    # (or resolvable PARAMETERs), verify index expressions stay
    # within [1, SIZE(array)].
    if store_exprs and param_values is not None:
        loop_lower = _resolve_bound(loop.start, param_values)
        loop_upper = _resolve_bound(loop.end, param_values)

        if loop_lower is not None and loop_upper is not None:
            for arr, wexprs in store_exprs.items():
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
                        for wexpr in wexprs:
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
            loop_dep, shift_k, atomic_arrays, None, None, None)


def _def_of(insts: list, name: str) -> IRInst | None:
    """Return the instruction whose result is `name` (SSA temps are
    single-definition within a body)."""
    for inst in insts:
        if inst.result == name:
            return inst
    return None


def _seg_index_table(insts: list, index_args: list,
                     loop_var: str) -> str | None:
    """Check that an array index list is exactly TAB(<loop var>) — a
    single table LOAD indexed by the loop variable — and return the
    table array name, or None if the form doesn't match.

    Expected lowering chain: idx = SUB(t_blk, 1); t_blk = LOAD TAB at
    (SUB(loop_var, 1)).
    """
    if len(index_args) != 1 or not isinstance(index_args[0], IRRef):
        return None
    sub1 = _def_of(insts, index_args[0].name)
    if (sub1 is None or sub1.op != Op.SUB or len(sub1.args) != 2
            or not isinstance(sub1.args[0], IRRef)
            or not (isinstance(sub1.args[1], IRConst)
                    and sub1.args[1].value == 1)):
        return None
    ld = _def_of(insts, sub1.args[0].name)
    if ld is None or ld.op != Op.LOAD:
        return None
    tab = ld.meta.get("array", "")
    if not tab or len(ld.args) != 1 or not isinstance(ld.args[0], IRRef):
        return None
    sub2 = _def_of(insts, ld.args[0].name)
    if (sub2 is None or sub2.op != Op.SUB or len(sub2.args) != 2
            or not isinstance(sub2.args[0], IRRef)
            or sub2.args[0].name != loop_var
            or not (isinstance(sub2.args[1], IRConst)
                    and sub2.args[1].value == 1)):
        return None
    return tab


def _validate_seg_reduction(loop: IRLoop,
                            arrays_read: set[str], arrays_written: set[str],
                            array_shapes: dict, var_types: dict,
                            param_values: dict[str, int]
                            ) -> tuple[str | None, str]:
    """Detect and validate a segmented sum reduction:
        ACC(TAB(I)) := ACC(TAB(I)) + <expr>

    One GPU kernel computes all segment sums at once: segments are
    padded to a multiple of the workgroup size (256), so each workgroup
    lies entirely within one segment and tree-combines exactly like the
    scalar staged reduce; group partial g belongs to segment
    g / Gseg. The host downloads the nseg x Gseg partials and combines
    per segment in group order — no atomics, deterministic.

    Returns (acc_name, "") on success; (None, "") when the loop is not
    a segmented-accumulate candidate (caller falls through to normal
    classification); (None, reason) when it is a candidate but violates
    a V1 constraint.
    """
    not_candidate = (None, "")

    # Candidate shape: exactly one array read AND written (the RMW
    # accumulator), and it is the only array written.
    rw = arrays_read & arrays_written
    if len(rw) != 1 or arrays_written != rw:
        return not_candidate
    acc = next(iter(rw))
    if var_types.get(acc) != IRType.REAL:
        # INTEGER RMW arrays are histograms/scatters, not segmented sums
        return not_candidate

    # Dispatch mapping is i = gid + 1: only 1..N step-1 loops map.
    if not (isinstance(loop.start, IRConst) and loop.start.value == 1):
        return not_candidate
    if not (isinstance(loop.step, IRConst) and loop.step.value == 1):
        return not_candidate

    insts = []
    for item in loop.body:
        if not isinstance(item, IRBlock):
            return not_candidate
        insts.extend(item.insts)

    loads = [i for i in insts
             if i.op == Op.LOAD and i.meta.get("array") == acc]
    stores = [i for i in insts
              if i.op == Op.STORE and i.meta.get("array") == acc]
    if len(loads) != 1 or len(stores) != 1:
        return not_candidate
    ld, st = loads[0], stores[0]
    if ld.result is None:
        return not_candidate

    # The load result feeds exactly one use: the accumulate ADD, whose
    # result is the stored value.
    uses = sum(1 for i in insts
               for a in i.args if isinstance(a, IRRef) and a.name == ld.result)
    if uses != 1:
        return not_candidate
    if not st.args or not isinstance(st.args[0], IRRef):
        return not_candidate
    add = _def_of(insts, st.args[0].name)
    if (add is None or add.op != Op.ADD or add.result is None
            or not any(isinstance(a, IRRef) and a.name == ld.result
                       for a in add.args)):
        return not_candidate
    if not (insts.index(ld) < insts.index(add) < insts.index(st)):
        return not_candidate

    # Read and write indices must be the same table lookup at the loop
    # variable (same TAB): each iteration touches exactly one segment.
    tab_ld = _seg_index_table(insts, ld.args, loop.var)
    tab_st = _seg_index_table(insts, st.args[1:], loop.var)
    if tab_ld is None or tab_ld != tab_st:
        return not_candidate
    if var_types.get(tab_ld) != IRType.INTEGER:
        return not_candidate

    # ── V1 segment geometry: compile-time provable ─────────────
    # nseg segments of equal length, each padded to a multiple of the
    # workgroup size, so one workgroup never straddles a boundary.
    shape = array_shapes.get(acc)
    nseg = None
    if shape and len(shape) == 1:
        dim = shape[0]
        if isinstance(dim, int):
            nseg = dim
        elif isinstance(dim, str):
            nseg = param_values.get(dim)
    bound = _resolve_bound(loop.end, param_values)
    if nseg is None or bound is None:
        return (None,
                f"segmented reduction '{acc}': loop bound and segment "
                f"count must be compile-time constants (CPU fallback)")
    if bound % nseg != 0:
        return (None,
                f"segmented reduction '{acc}': loop bound {bound} is not "
                f"a multiple of the segment count {nseg} (CPU fallback)")
    seg_len = bound // nseg
    if seg_len % 256 != 0:
        return (None,
                f"segmented reduction '{acc}': segment length {seg_len} "
                f"is not a multiple of the workgroup size 256 — pad "
                f"segments (CPU fallback)")

    return acc, ""


def _validate_reductions(loop: IRLoop, accumulators: set[str],
                         arrays_written: set[str],
                         var_types: dict) -> tuple[list | None, str]:
    """Validate REDUCTION-classified loops for staged GPU lowering.

    Accepted pattern (sum reduction, N accumulators):
        acc_k := acc_k + <expr_k>     for each accumulator k
    — each accumulator read by exactly one ADD and written by exactly one
    COPY of that ADD's result, in that order; no array stores;
    straight-line body (no branches, CYCLE/EXIT, or I/O); constant
    start=1, step=1 (the dispatch mapping is i = gid + 1). Accumulators
    may be REAL or INTEGER (integer sums are combined in f64 on device —
    exact below 2^53).

    Returns ([accumulator_names], "") on success, (None, reason)
    otherwise. The reason string is appended to the CPU-fallback
    diagnostic.
    """
    def reject(why: str):
        return None, f"; staged reduction rejected — {why}"

    # Shared structural constraints.
    if not (isinstance(loop.start, IRConst) and loop.start.value == 1):
        return reject("loop start must be the constant 1")
    if not (isinstance(loop.step, IRConst) and loop.step.value == 1):
        return reject("loop step must be the constant 1")

    if arrays_written:
        return reject("reduction loop must not write arrays")

    insts = []
    for item in loop.body:
        if not isinstance(item, IRBlock):
            return reject("reduction body must be straight-line code "
                          "(no IF/loops/SELECT)")
        insts.extend(item.insts)

    for inst in insts:
        if inst.op == Op.STORE:
            return reject("reduction loop must not write arrays")
        if inst.op == Op.COPY and inst.meta.get("kind") in ("cycle", "exit"):
            return reject("CYCLE/EXIT in reduction loop")

    accs = []
    for acc in sorted(accumulators):
        acc_type = var_types.get(acc)
        if acc_type not in (IRType.REAL, IRType.INTEGER):
            return reject(f"accumulator '{acc}' must be REAL or INTEGER")

        add_pos = -1
        add_result = None
        copy_pos = -1
        for pos, inst in enumerate(insts):
            reads_acc = any(isinstance(a, IRRef) and a.name == acc
                            for a in inst.args)
            if inst.op == Op.COPY and inst.result == acc:
                if copy_pos >= 0:
                    return reject(f"accumulator '{acc}' written more than once")
                copy_pos = pos
            elif reads_acc:
                # A read of acc that is not the write-back COPY's source:
                # only the single accumulate ADD may read it.
                if inst.op == Op.ADD and add_pos < 0 and inst.result:
                    add_pos = pos
                    add_result = inst.result
                else:
                    return reject(f"accumulator '{acc}' read by "
                                  f"non-accumulate op '{inst.op.value}'")

        if add_pos < 0:
            return reject(f"accumulator '{acc}' has no accumulate ADD")
        if copy_pos < 0:
            return reject(f"accumulator '{acc}' is never written back")
        if copy_pos < add_pos:
            return reject(f"accumulate ADD for '{acc}' must precede the "
                          f"write-back COPY")
        src = insts[copy_pos].args[0] if insts[copy_pos].args else None
        if not (isinstance(src, IRRef) and src.name == add_result):
            return reject(f"write-back of '{acc}' is not the accumulate ADD "
                          f"result")
        accs.append(acc)

    return accs, ""


def _check_body(items: list, loop_var: str, array_shapes: dict,
                var_types: dict,
                arrays_read: set[str], arrays_written: set[str],
                scalars_read: set[str],
                scalars_written: set[str],
                scalars_read_before_write: set[str],
                allow_scatter: bool = False,
                param_values: dict[str, int] | None = None) -> tuple[bool, str]:
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
                                             insts=item.insts,
                                             shape=array_shapes.get(arr),
                                             param_values=param_values):
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
                                     allow_scatter, param_values)
            if not ok:
                return False, reason
            if item.else_body:
                ok, reason = _check_body(item.else_body, loop_var,
                                         array_shapes, var_types,
                                         arrays_read, arrays_written,
                                         scalars_read, scalars_written,
                                         scalars_read_before_write,
                                         allow_scatter, param_values)
                if not ok:
                    return False, reason

        elif isinstance(item, IRLoop):
            return False, f"nested loop at line {item.line}"

        elif isinstance(item, IRSelect):
            return False, f"SELECT CASE inside loop at line {item.line}"

    return True, ""


def _combine_affine_indices(exprs: list[AffineExpr],
                            shape: tuple | None,
                            param_values: dict[str, int] | None
                            ) -> AffineExpr | None:
    """Fold per-dimension affine indices into one linear affine expr.

    Column-major linearization (the locked Ergo convention, Spec Part 3):
    lin = i0 + d0*(i1 + d1*(i2)), so the stride of dimension d is the
    product of extents d0..d_{d-1}. Extents come from the array shape;
    PARAMETER-named dims are resolved via param_values. Returns None if
    any needed extent cannot be resolved to a concrete int.

    A constant per-dimension index contributes a zero loop-var
    coefficient scaled by its stride — it cannot make an otherwise
    injective combined index non-injective.
    """
    if shape is None or len(shape) < len(exprs):
        return None
    pvals = param_values or {}
    stride = 1
    combined = exprs[0]
    for d in range(1, len(exprs)):
        dim = shape[d - 1]
        if isinstance(dim, bool):
            return None
        if isinstance(dim, int):
            extent = dim
        elif isinstance(dim, str):
            extent = pvals.get(dim)
        else:
            extent = None
        if not isinstance(extent, int) or isinstance(extent, bool):
            return None
        stride *= extent
        combined = affine_add(combined, affine_mul_const(exprs[d], stride))
    return combined


def _classify_store_index(index_args: list[Operand], loop_var: str,
                          insts: list | None = None,
                          invariants: set[str] | None = None,
                          shape: tuple | None = None,
                          param_values: dict[str, int] | None = None
                          ) -> tuple[LoopDependence, AffineExpr | None]:
    """Classify a STORE index and extract its affine structure if possible.

    Returns (dependence_class, affine_expr_or_None).

    - INJECTIVE + AffineExpr: affine index with non-zero loop-var coefficient
    - FLOW + None: data-dependent index (array LOAD), no read-modify-write
    - SCATTER + None: non-affine, division, or constant index

    Multi-dimensional stores are classified by their combined linear
    index (column-major): every per-dimension index must extract affine
    and every needed extent must resolve to an int, otherwise the same
    load-vs-scatter fallback as the 1-D case applies.
    """
    if not index_args:
        return LoopDependence.SCATTER, None

    if insts is None:
        return LoopDependence.SCATTER, None

    # Build def map for this block
    defs: dict[str, IRInst] = {}
    for inst in insts:
        if inst.result:
            defs[inst.result] = inst

    safe = invariants if invariants is not None else globals().get('_module_invariants', set())

    if len(index_args) > 1:
        return _classify_multidim_index(index_args, loop_var, defs, safe,
                                        shape, param_values)

    arg = index_args[0]
    if not isinstance(arg, IRRef):
        return LoopDependence.SCATTER, None

    # Try affine extraction (PARAMETERs resolve to their values — makes
    # affine-by-PARAMETER strides like (J-1)*NX provable)
    expr = extract_affine(arg.name, loop_var, defs, safe,
                          param_values=param_values)

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


def _classify_multidim_index(index_args: list[Operand], loop_var: str,
                             defs: dict[str, IRInst],
                             invariants: set[str],
                             shape: tuple | None,
                             param_values: dict[str, int] | None
                             ) -> tuple[LoopDependence, AffineExpr | None]:
    """Classify a multi-dimensional STORE index via its linear index."""
    exprs = [_operand_to_affine(arg, loop_var, defs, invariants, 0,
                                param_values)
             for arg in index_args]

    if any(e is None for e in exprs):
        # Some dimension is non-affine: data-dependent (FLOW) if any
        # index traces through an array LOAD, else SCATTER.
        for arg in index_args:
            if isinstance(arg, IRRef) and _index_has_load(arg.name, defs):
                return LoopDependence.FLOW, None
        return LoopDependence.SCATTER, None

    combined = _combine_affine_indices(exprs, shape, param_values)
    if combined is None:
        # Extents not resolvable to ints — cannot prove injectivity.
        return LoopDependence.SCATTER, None

    if combined.is_injective(loop_var):
        return LoopDependence.INJECTIVE, combined
    # Constant combined index = SCATTER
    return LoopDependence.SCATTER, combined


def _extract_load_index(index_args: list[Operand], loop_var: str,
                        insts: list, invariants: set[str],
                        shape: tuple | None = None,
                        param_values: dict[str, int] | None = None
                        ) -> AffineExpr | None:
    """Extract AffineExpr for a LOAD index (for shift detection).

    Multi-dimensional loads are folded to their combined linear index
    the same way stores are; returns None when extraction fails.
    """
    defs: dict[str, IRInst] = {}
    for inst in insts:
        if inst.result:
            defs[inst.result] = inst

    if len(index_args) == 1:
        arg = index_args[0]
        if not isinstance(arg, IRRef):
            return None
        return extract_affine(arg.name, loop_var, defs, invariants,
                              param_values=param_values)

    exprs = [_operand_to_affine(arg, loop_var, defs, invariants, 0,
                                param_values)
             for arg in index_args]
    if any(e is None for e in exprs):
        return None
    return _combine_affine_indices(exprs, shape, param_values)


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
        if isinstance(arg, IRRef):
            if _index_has_load(arg.name, defs, depth + 1):
                return True
    return False


def _index_is_loop_var(index_args: list[Operand], loop_var: str,
                       insts: list | None = None,
                       invariants: set[str] | None = None,
                       shape: tuple | None = None,
                       param_values: dict[str, int] | None = None) -> bool:
    """Legacy compatibility wrapper — returns True for INJECTIVE or FLOW indices.

    Used by _check_body and _try_split which need a boolean check.
    INJECTIVE and FLOW are both extractable to GPU; SCATTER is not.
    """
    dep, _ = _classify_store_index(index_args, loop_var, insts, invariants,
                                   shape, param_values)
    return dep in (LoopDependence.INJECTIVE, LoopDependence.FLOW)


def _iter_blocks(items: list):
    """Yield every IRBlock in a body item list.

    Recurses into IRIf then/else bodies and IRSelect case bodies — the
    classifier must see physics hidden inside conditionals — but NOT
    into nested IRLoop bodies (those are separate loops, classified on
    their own).
    """
    for item in items:
        if isinstance(item, IRBlock):
            yield item
        elif isinstance(item, IRIf):
            yield from _iter_blocks(item.then_body)
            if item.else_body:
                yield from _iter_blocks(item.else_body)
        elif isinstance(item, IRSelect):
            for _, case_body in item.cases:
                yield from _iter_blocks(case_body)


def _classify_body_dependence(body_items: list, loop_var: str,
                              invariants: set[str],
                              array_shapes: dict | None = None,
                              param_values: dict[str, int] | None = None
                              ) -> tuple[LoopDependence, int | None, set[str], dict]:
    """Classify the dependence structure of a loop body (Spec 9.5).

    Walks every STORE/LOAD in the body (descending into IF/SELECT
    bodies, not into nested loops) and combines the per-store
    classifications:
      - every store of an array is kept; the worst rank across ALL
        stores wins (a FLOW store followed by an INJECTIVE store to the
        same array must not hide the FLOW),
      - any FLOW store to an array that is also loaded upgrades the
        loop to SCATTER (read-modify-write at a data-dependent index),
      - any same-array affine write/read pair at a constant non-zero
        offset is SHIFT(k).

    Index expressions are traced against the defs of every block up to
    and including the one holding the STORE/LOAD: per-iteration values
    flow across blocks within one iteration (e.g. `J := IDX(I)` in one
    statement, `A(J) := ...` in the next), and later blocks must not
    pollute earlier stores (a scalar re-assigned mid-body traces to
    its def as of the store, not its final def).

    Returns (dependence, shift_k, atomic_arrays, store_exprs) where
    store_exprs maps array name → list of write AffineExprs (for
    bounds validation).
    """
    loop_dep = LoopDependence.INJECTIVE  # best case
    shift_k: int | None = None

    store_deps: dict[str, list[LoopDependence]] = {}  # arr → per-store classes
    store_exprs: dict[str, list[AffineExpr]] = {}     # arr → write AffineExprs
    load_exprs: dict[str, list[AffineExpr]] = {}      # arr → read AffineExprs
    arrays_loaded: set[str] = set()  # all arrays that appear in LOADs

    shapes = array_shapes or {}
    seen_insts: list = []  # defs visible so far (per-iteration, in order)

    for block in _iter_blocks(body_items):
        seen_insts.extend(block.insts)
        for inst in block.insts:
            if inst.op == Op.STORE:
                arr = inst.meta.get("array", "")
                dep, expr = _classify_store_index(
                    inst.args[1:], loop_var, insts=seen_insts,
                    invariants=invariants,
                    shape=shapes.get(arr), param_values=param_values)
                store_deps.setdefault(arr, []).append(dep)
                # Track worst classification across every store
                if _dep_rank(dep) > _dep_rank(loop_dep):
                    loop_dep = dep
                if expr is not None:
                    store_exprs.setdefault(arr, []).append(expr)
            elif inst.op == Op.LOAD:
                arr = inst.meta.get("array", "")
                arrays_loaded.add(arr)
                rexpr = _extract_load_index(
                    inst.args, loop_var, seen_insts, invariants,
                    shape=shapes.get(arr), param_values=param_values)
                if rexpr is not None:
                    load_exprs.setdefault(arr, []).append(rexpr)

    # FLOW + read-modify-write of same array = SCATTER.
    # If the index is data-dependent and we both read and write the array,
    # we can't assume the reads and writes don't collide.
    for arr, deps in store_deps.items():
        if arr in arrays_loaded and any(d == LoopDependence.FLOW for d in deps):
            loop_dep = LoopDependence.SCATTER
            break

    # Check for shift dependencies: same array written and read at
    # different offsets. Every (write expr × read expr) pair is checked —
    # with multiple stores to one array, any of them may carry the shift.
    # Runs whenever the loop is not already SCATTER: SHIFT (cross-
    # iteration, serialized) outranks FLOW, so a FLOW store on one array
    # must not hide an affine shift pair on another (spec 9.5 — the most
    # restrictive classification applies).
    if loop_dep in (LoopDependence.INJECTIVE, LoopDependence.FLOW):
        for arr, wexprs in store_exprs.items():
            if arr not in load_exprs:
                continue
            for wexpr in wexprs:
                for rexpr in load_exprs[arr]:
                    k = detect_shift(wexpr, rexpr, loop_var)
                    if k is not None and k != 0:
                        loop_dep = LoopDependence.SHIFT
                        shift_k = k
                        break
                if loop_dep == LoopDependence.SHIFT:
                    break
            if loop_dep == LoopDependence.SHIFT:
                break

    # SCATTER loops are extractable with atomic operations.
    # Identify which arrays need atomics: those with non-injective
    # write indices (FLOW or SCATTER) that also appear in LOADs
    # (read-modify-write pattern).
    atomic_arrays: set[str] = set()
    if loop_dep == LoopDependence.SCATTER:
        for arr, deps in store_deps.items():
            if arr in arrays_loaded and any(
                    d in (LoopDependence.FLOW, LoopDependence.SCATTER)
                    for d in deps):
                atomic_arrays.add(arr)

    return loop_dep, shift_k, atomic_arrays, store_exprs


def _collect_scalar_reads(items: list, reads: set[str]):
    """Recursively collect ALL variable names read in a list of IR items.

    Complete for GPU->CPU boundary analysis: every Operand reference in
    every instruction (including STORE value and index args — a store
    index computed on the device is just as unavailable to the CPU
    suffix as a loaded value), IF conditions, SELECT expressions, and
    loop bounds. Underscore-prefixed names (inlined subroutine locals,
    compiler temps) are included: they are per-iteration values like
    any named local.
    """
    for item in items:
        if isinstance(item, IRBlock):
            for inst in item.insts:
                for arg in inst.args:
                    if isinstance(arg, IRRef):
                        reads.add(arg.name)
        elif isinstance(item, IRIf):
            if isinstance(item.condition, IRRef):
                reads.add(item.condition.name)
            _collect_scalar_reads(item.then_body, reads)
            if item.else_body:
                _collect_scalar_reads(item.else_body, reads)
        elif isinstance(item, IRLoop):
            for bound in (item.start, item.end, item.step):
                if isinstance(bound, IRRef):
                    reads.add(bound.name)
            _collect_scalar_reads(item.body, reads)
        elif isinstance(item, IRSelect):
            if isinstance(item.expr, IRRef):
                reads.add(item.expr.name)
            for _, case_body in item.cases:
                _collect_scalar_reads(case_body, reads)


def _collect_scalar_refs(op: Operand, scalars: set[str]):
    """Collect scalar variable references from an operand."""
    if isinstance(op, IRRef):
        if not op.name.startswith("_"):
            scalars.add(op.name)


def _collect_result_names(items: list, out: set[str]):
    """Collect every instruction result name defined in a list of IR
    items, descending into IF/SELECT bodies and nested loop bodies.
    Loop variables count as defined by their loop."""
    for item in items:
        if isinstance(item, IRBlock):
            for inst in item.insts:
                if inst.result:
                    out.add(inst.result)
        elif isinstance(item, IRIf):
            _collect_result_names(item.then_body, out)
            if item.else_body:
                _collect_result_names(item.else_body, out)
        elif isinstance(item, IRLoop):
            out.add(item.var)
            _collect_result_names(item.body, out)
        elif isinstance(item, IRSelect):
            for _, case_body in item.cases:
                _collect_result_names(case_body, out)


def _find_structural_scalar_refs(items: list, names: set[str]) -> set[str]:
    """Find which of `names` are read from structural positions the
    promote_locals suffix rewrite cannot reach: IF conditions, loop
    bounds (start/end/step), and SELECT expressions. Plain block-level
    reads are not reported (the rewrite handles those)."""
    found: set[str] = set()
    for item in items:
        if isinstance(item, IRBlock):
            continue  # block-level reads are rewritten
        if isinstance(item, IRIf):
            if (isinstance(item.condition, IRRef)
                    and item.condition.name in names):
                found.add(item.condition.name)
            found |= _find_structural_scalar_refs(item.then_body, names)
            if item.else_body:
                found |= _find_structural_scalar_refs(
                    item.else_body, names)
        elif isinstance(item, IRLoop):
            for bound in (item.start, item.end, item.step):
                if isinstance(bound, IRRef) and bound.name in names:
                    found.add(bound.name)
            found |= _find_structural_scalar_refs(item.body, names)
        elif isinstance(item, IRSelect):
            if isinstance(item.expr, IRRef) and item.expr.name in names:
                found.add(item.expr.name)
            for _, case_body in item.cases:
                found |= _find_structural_scalar_refs(case_body, names)
    return found
