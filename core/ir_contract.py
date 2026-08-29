"""IR-level FMA contraction analysis — the compiler-owned site report.

Policy (Spec/Ergo_Hardware_Op_Map.md §4, 2026-08-29): contraction is
compiler-owned.  On the GPU side that ownership is enforced by
NoContraction decorations on every fp arithmetic result (the Vulkan
driver may never fuse what we did not choose).  This module computes
the fusible-site set — every `a*b ± c` whose factors are REAL mul
results — which the SPIR-V backend reports at compile time as the
documented CPU≠GPU last-ulp boundary (the CPU recipe's
`-ffp-contract=fast` may contract those sites; the GPU never does).

A kernel with no reported sites (and no transcendentals — Part 9.10 —
and no reductions — Part 9.9) is CPU==GPU-bitwise by construction.

NOTE: emitting explicit fma() at these sites on the CPU side was
evaluated and REJECTED (2026-08-29, evidence in the op map §4 and
tests/contraction/): gcc's fused set is not computable from the IR —
it depends on post-inlining PHI/sink behavior that flips arbitrarily
between callee shapes (probe9, and the smoke-test sin-vs-cos
asymmetry).  Any IR rule that mismatches gcc at one site flips every
chaotic corpus program containing it (measured: 145/197 moved with the
naive rule).  So the marker is a REPORT, not an emission transform.

The site rule encoded here matches the measured gcc -ffp-contract=fast
behavior on straight-line code (tests/contraction/probe*.c):
  x + y, x = a*b        -> fusible as fma(a, b, y)
  x - y, x = a*b        -> fusible as fma(a, b, -y)
  x + y, y = a*b        -> fusible as fma(a, b, x)
  x - y, y = a*b        -> fusible as fma(-a, b, x)   (exact sign flip)
  both operands muls    -> the LEFT mul fuses (probe5, discriminating)
  NEG-wrapped mul       -> the sign folds into a factor, still fusible
  never fusible         -> add feeding a mul, any division form,
                           all-constant subtrees (folded unfused)
Multi-use and cross-block products are fusible; f32 mirrors f64.
"""

from .ir import (IRModule, IRBlock, IRIf, IRLoop, IRWhileLoop, IRSelect,
                 IRInst, Op, IRType, IRConst, IRRef)

# site record: id(add/sub inst) -> dict with:
#   mul:   the IRInst of the MUL whose operands become fma's a,b
#   side:  'L' (mul is the left operand) or 'R'
#   neg_mul:    negate the mul's first factor (NEG-wrapped right SUB /
#               NEG-wrapped left forms)
#   neg_addend: negate the non-mul operand (SUB with left mul)


def _const(op) -> bool:
    return isinstance(op, IRConst)


def compute_fma_sites(mod: IRModule) -> dict[int, dict]:
    """Walk the module in program order and mark fusible ADD/SUB sites.

    Returns {id(add/sub inst): site dict}.  Deterministic: called
    independently by the CPU and SPIR-V backends on the same final IR.
    """
    sites: dict[int, dict] = {}

    def mul_def(name, defs):
        """Current def of `name` if it is a fusible MUL (possibly behind
        one NEG).  Returns (mul_inst, negated) or None."""
        d = defs.get(name)
        if d is None or not isinstance(d, IRInst):
            return None
        neg = False
        if d.op == Op.NEG and isinstance(d.args[0], IRRef):
            dd = defs.get(d.args[0].name)
            if dd is None or not isinstance(dd, IRInst) or \
                    dd.op != Op.MUL:
                return None
            d, neg = dd, True
        if d.op != Op.MUL or d.type != IRType.REAL:
            return None
        # all-constant muls are folded unfused by the C compiler — skip
        if _const(d.args[0]) and _const(d.args[1]):
            return None
        return d, neg

    def consider(inst, defs):
        if inst.op not in (Op.ADD, Op.SUB) or inst.type != IRType.REAL:
            return
        if not inst.args or not isinstance(inst.args[0], IRRef):
            xname = None
        else:
            xname = inst.args[0].name
        yname = inst.args[1].name if isinstance(inst.args[1], IRRef) else None
        sub = inst.op == Op.SUB
        lm = mul_def(xname, defs) if xname else None
        rm = mul_def(yname, defs) if yname else None
        if lm is not None:
            mul, neg = lm
            sites[id(inst)] = {"mul": mul, "side": "L",
                               "neg_mul": neg, "neg_addend": sub}
        elif rm is not None:
            mul, neg = rm
            # SUB with right mul: negate a factor (exact)
            sites[id(inst)] = {"mul": mul, "side": "R",
                               "neg_mul": (not neg) if sub else neg,
                               "neg_addend": False}

    def walk(items, defs):
        for item in items:
            if isinstance(item, IRBlock):
                for inst in item.insts:
                    consider(inst, defs)
                    if inst.result:
                        defs[inst.result] = inst
            elif isinstance(item, IRIf):
                outer = dict(defs)
                walk(item.then_body, dict(defs))
                if item.else_body:
                    walk(item.else_body, dict(defs))
                # conservative merge: any var written in a branch whose
                # def now differs from the outer def becomes unknown
                # (a phi in the C backend's SSA — gcc does not fuse
                # through phis, so unmarked is the matching choice)
                changed = set()
                for scope in (item.then_body, item.else_body or []):
                    collect_writes(scope, changed)
                for v in changed:
                    defs[v] = None
                for v, d in outer.items():
                    if v not in changed:
                        defs[v] = d
            elif isinstance(item, (IRLoop, IRWhileLoop)):
                body_writes = set()
                collect_writes(item.body, body_writes)
                if isinstance(item, IRWhileLoop):
                    collect_writes([item.cond_block], body_writes)
                # loop-carried values become phis for outside users;
                # inside, program order is exact for the temp chains
                walk(item.body, dict(defs))
                for v in body_writes:
                    defs[v] = None
            elif isinstance(item, IRSelect):
                for _, body in item.cases:
                    walk(body, dict(defs))
                changed = set()
                for _, body in item.cases:
                    collect_writes(body, changed)
                for v in changed:
                    defs[v] = None

    def collect_writes(items, out):
        for item in items:
            if isinstance(item, IRBlock):
                for inst in item.insts:
                    if inst.result:
                        out.add(inst.result)
            elif isinstance(item, IRIf):
                collect_writes(item.then_body, out)
                if item.else_body:
                    collect_writes(item.else_body, out)
            elif isinstance(item, (IRLoop, IRWhileLoop)):
                collect_writes(item.body, out)
                if isinstance(item, IRWhileLoop):
                    collect_writes([item.cond_block], out)
            elif isinstance(item, IRSelect):
                for _, body in item.cases:
                    collect_writes(body, out)

    walk(mod.main_body, {})
    for fn in mod.functions:
        walk(fn.body, {})
    return sites
