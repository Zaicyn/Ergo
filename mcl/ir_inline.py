"""Subroutine inlining pass for the Ergo IR.

Inlines subroutine bodies at call sites so that per-element loops
inside subroutines become visible to the kernel extractor.

This is the key pass that enables GPU extraction from the galaxy sim
and other structured-programming simulations where the physics loop
lives inside a SUBROUTINE, not in the main body.

Architecture:
  - The CPU is the oracle (seed domain). It keeps ground truth.
  - The GPU is the worker. Inlining exposes the parallel loops so
    the extractor can ship them to compute shaders.
  - Verification: CPU spot-checks GPU results against oracle state.
"""

from __future__ import annotations

from .ir import (
    IRModule, IRFunc, IRVar, IRBlock, IRIf, IRLoop, IRSelect,
    IRInst, IRConst, IRRef, IRType, Op, StorageClass, Operand,
    IRItem,
)


def inline_subroutines(module: IRModule) -> list[str]:
    """Inline subroutine calls in main_body.

    Replaces CALL_VOID instructions with the called subroutine's body,
    substituting parameters and renaming locals to avoid collisions.

    Mutates module in place. Returns diagnostic messages.
    """
    diags: list[str] = []

    # Build subroutine lookup
    sub_map: dict[str, IRFunc] = {}
    for fn in module.functions:
        if fn.is_subroutine:
            sub_map[fn.name] = fn

    if not sub_map:
        return diags

    # Track which locals we've added
    existing_locals = {v.name for v in module.main_locals}
    existing_globals = {g.name for g in module.globals}

    # Counter for unique prefixes
    inline_count: dict[str, int] = {}

    def _unique_prefix(sub_name: str) -> str:
        n = inline_count.get(sub_name, 0)
        inline_count[sub_name] = n + 1
        if n == 0:
            return f"_{sub_name}_"
        return f"_{sub_name}_{n}_"

    def _is_sub_local(name: str, local_names: set[str]) -> bool:
        """Check if a name is local to the subroutine (local or param)."""
        return name in local_names

    def _remap_operand(op: Operand, prefix: str,
                       local_names: set[str]) -> Operand:
        if isinstance(op, IRConst):
            return op
        if isinstance(op, IRRef):
            if _is_sub_local(op.name, local_names):
                return IRRef(prefix + op.name, op.type)
            # Global — keep as-is
            return op
        return op

    def _remap_inst(inst: IRInst, prefix: str,
                    local_names: set[str]) -> IRInst:
        new_args = [_remap_operand(a, prefix, local_names) for a in inst.args]
        new_result = inst.result
        if new_result is not None and _is_sub_local(new_result, local_names):
            new_result = prefix + new_result

        new_meta = dict(inst.meta)
        if "array" in new_meta:
            arr = new_meta["array"]
            if _is_sub_local(arr, local_names):
                new_meta["array"] = prefix + arr

        return IRInst(
            op=inst.op, args=new_args, result=new_result,
            type=inst.type, line=inst.line, meta=new_meta,
        )

    def _remap_body(body: list[IRItem], prefix: str,
                    local_names: set[str]) -> list[IRItem]:
        return [_remap_item(item, prefix, local_names) for item in body]

    def _remap_item(item: IRItem, prefix: str,
                    local_names: set[str]) -> IRItem:
        if isinstance(item, IRBlock):
            new_insts = []
            for inst in item.insts:
                if inst.op in (Op.RETURN_VOID, Op.RETURN):
                    continue
                new_insts.append(_remap_inst(inst, prefix, local_names))
            return IRBlock(label=prefix + item.label, insts=new_insts, line=item.line)

        elif isinstance(item, IRLoop):
            new_var = (prefix + item.var) if _is_sub_local(item.var, local_names) else item.var
            new_start = _remap_operand(item.start, prefix, local_names)
            new_end = _remap_operand(item.end, prefix, local_names)
            new_step = _remap_operand(item.step, prefix, local_names)
            new_body = _remap_body(item.body, prefix, local_names)
            return IRLoop(var=new_var, start=new_start, end=new_end, step=new_step,
                         body=new_body, line=item.line)

        elif isinstance(item, IRIf):
            new_cond = _remap_operand(item.condition, prefix, local_names)
            new_then = _remap_body(item.then_body, prefix, local_names)
            new_else = _remap_body(item.else_body, prefix, local_names) if item.else_body else None
            return IRIf(condition=new_cond, then_body=new_then, else_body=new_else, line=item.line)

        elif isinstance(item, IRSelect):
            new_expr = _remap_operand(item.expr, prefix, local_names)
            new_cases = []
            for case_val, case_body in item.cases:
                cv = _remap_operand(case_val, prefix, local_names) if case_val else None
                cb = _remap_body(case_body, prefix, local_names)
                new_cases.append((cv, cb))
            return IRSelect(expr=new_expr, cases=new_cases, line=item.line)

        return item

    def _inline_block(block: IRBlock) -> list[IRItem]:
        """Process a single block. If it contains a CALL_VOID to a known
        subroutine, inline it."""
        call_inst = None
        other_insts = []
        for inst in block.insts:
            if inst.op == Op.CALL_VOID and inst.meta.get("func") in sub_map:
                call_inst = inst
            else:
                other_insts.append(inst)

        if call_inst is None:
            return [block]

        sub_name = call_inst.meta["func"]
        sub = sub_map[sub_name]
        prefix = _unique_prefix(sub_name)

        # All subroutine locals + params are "local names" that get prefixed.
        # This handles shadowing correctly: if a sub has a local OMEGA_MAX
        # that shadows the global PARAMETER OMEGA_MAX, the local gets
        # renamed and the global remains untouched elsewhere.
        local_names = {v.name for v in sub.locals} | {p.name for p in sub.params}

        # Add prefixed locals to module.main_locals
        for v in sub.locals:
            prefixed = prefix + v.name
            if prefixed not in existing_locals:
                module.main_locals.append(IRVar(
                    name=prefixed, type=v.type, storage=StorageClass.LOCAL,
                    shape=v.shape, line=v.line,
                ))
                existing_locals.add(prefixed)

        # Parameters become prefixed locals, initialized from call args
        for p in sub.params:
            prefixed = prefix + p.name
            if prefixed not in existing_locals:
                module.main_locals.append(IRVar(
                    name=prefixed, type=p.type, storage=StorageClass.LOCAL,
                    shape=p.shape, line=p.line,
                ))
                existing_locals.add(prefixed)

        # Build initialization block: copy call args into prefixed param locals
        init_insts = list(other_insts)  # carry forward any pre-call insts
        for i, p in enumerate(sub.params):
            if i < len(call_inst.args):
                init_insts.append(IRInst(
                    op=Op.COPY,
                    result=prefix + p.name,
                    args=[call_inst.args[i]],
                    type=p.type,
                    line=call_inst.line,
                ))

        # Clone and remap the subroutine body
        inlined = _remap_body(sub.body, prefix, local_names)

        diags.append(f"Inlined {sub_name}() ({len(sub.body)} items, "
                     f"{len(sub.locals)} locals)")

        result = []
        if init_insts:
            init_block = IRBlock(label=prefix + "init", insts=init_insts,
                                 line=call_inst.line)
            init_block.inlined_from = sub_name  # marker for codegen hooks
            result.append(init_block)
        result.extend(inlined)
        # Tag the last item so codegen knows where the inlined body ends
        if result:
            result[-1].inlined_end = sub_name
        return result

    def _process_body(body: list[IRItem]) -> list[IRItem]:
        """Recursively process a body, inlining CALL_VOID where possible."""
        result = []
        for item in body:
            if isinstance(item, IRBlock):
                result.extend(_inline_block(item))
            elif isinstance(item, IRLoop):
                new_body = _process_body(item.body)
                result.append(IRLoop(var=item.var, start=item.start, end=item.end,
                                    step=item.step, body=new_body, line=item.line))
            elif isinstance(item, IRIf):
                new_then = _process_body(item.then_body)
                new_else = _process_body(item.else_body) if item.else_body else None
                result.append(IRIf(condition=item.condition, then_body=new_then,
                                  else_body=new_else, line=item.line))
            elif isinstance(item, IRSelect):
                new_cases = []
                for cv, cb in item.cases:
                    new_cases.append((cv, _process_body(cb)))
                result.append(IRSelect(expr=item.expr, cases=new_cases, line=item.line))
            else:
                result.append(item)
        return result

    module.main_body = _process_body(module.main_body)
    return diags
