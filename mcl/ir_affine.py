"""Affine index analysis for GPU loop classification.

Extracts structured AffineExpr from IR index computations, replacing the
boolean _traces_to_loop_var check with actual coefficient extraction.

This turns "does this index derive from I?" into "this index equals 2*I + 5",
which enables:
  - Injectivity proof (non-zero loop-var coefficient, no division)
  - Shift dependency detection (same-array read/write offset comparison)
  - Bounds validation (when loop bounds and array sizes are PARAMETERs)

Division is outside the affine language. Any division in the index causes
extraction to fail — the caller falls through to FLOW or SCATTER.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from .ir import IRInst, IRConst, IRRef, Op, Operand


# ── Symbol kinds ─────────────────��──────────────────────────

class SymbolKind(Enum):
    LOOP_VAR = auto()     # loop induction variable
    PARAMETER = auto()    # compile-time constant or loop-invariant scalar


@dataclass(frozen=True)
class Symbol:
    """A named symbol in an affine expression."""
    name: str
    kind: SymbolKind

    def __repr__(self):
        return f"{self.name}:{self.kind.name}"


# ��─ AffineExpr ──��─────────────���─────────────────────────────

@dataclass
class AffineExpr:
    """An affine expression: sum of (symbol * coefficient) + constant.

    Example: 3*I + N + 5 → coeffs={Symbol(I,LOOP_VAR):3, Symbol(N,PARAMETER):1}, constant=5
    Example: I - 1       → coeffs={Symbol(I,LOOP_VAR):1}, constant=-1
    Example: 42          → coeffs={}, constant=42
    """
    coeffs: dict[Symbol, int] = field(default_factory=dict)
    constant: int = 0

    def loop_var_coeff(self, var_name: str) -> int:
        """Get the coefficient of a loop variable by name."""
        for sym, coeff in self.coeffs.items():
            if sym.name == var_name and sym.kind == SymbolKind.LOOP_VAR:
                return coeff
        return 0

    def is_injective(self, loop_var: str) -> bool:
        """True if this expression is injective over the loop variable.

        Non-zero coefficient means each iteration maps to a distinct index.
        """
        return self.loop_var_coeff(loop_var) != 0

    def stride(self, loop_var: str) -> int:
        """The stride per iteration (coefficient of the loop variable)."""
        return self.loop_var_coeff(loop_var)

    def constant_offset(self, loop_var: str) -> int:
        """The constant part of the expression (everything except the loop var term).

        For shift detection: if write is at aI+c1 and read is at aI+c2,
        the shift distance is c1-c2.

        Note: this includes PARAMETER terms in the 'constant' part since
        PARAMETERs are loop-invariant. For exact offset computation when
        PARAMETERs are present, both expressions must have identical
        PARAMETER coefficients.
        """
        return self.constant

    def __repr__(self):
        parts = []
        for sym, coeff in sorted(self.coeffs.items(), key=lambda x: x[0].name):
            if coeff == 1:
                parts.append(str(sym.name))
            elif coeff == -1:
                parts.append(f"-{sym.name}")
            else:
                parts.append(f"{coeff}*{sym.name}")
        if self.constant != 0 or not parts:
            parts.append(str(self.constant))
        return " + ".join(parts).replace(" + -", " - ")


# ── AffineExpr operations ──���───────────────────────────────

def affine_add(a: AffineExpr, b: AffineExpr) -> AffineExpr:
    coeffs = dict(a.coeffs)
    for sym, coeff in b.coeffs.items():
        coeffs[sym] = coeffs.get(sym, 0) + coeff
        if coeffs[sym] == 0:
            del coeffs[sym]
    return AffineExpr(coeffs, a.constant + b.constant)


def affine_sub(a: AffineExpr, b: AffineExpr) -> AffineExpr:
    coeffs = dict(a.coeffs)
    for sym, coeff in b.coeffs.items():
        coeffs[sym] = coeffs.get(sym, 0) - coeff
        if coeffs[sym] == 0:
            del coeffs[sym]
    return AffineExpr(coeffs, a.constant - b.constant)


def affine_neg(a: AffineExpr) -> AffineExpr:
    return AffineExpr({s: -c for s, c in a.coeffs.items()}, -a.constant)


def affine_mul_const(a: AffineExpr, k: int) -> AffineExpr:
    """Multiply an affine expression by an integer constant."""
    if k == 0:
        return AffineExpr({}, 0)
    return AffineExpr({s: c * k for s, c in a.coeffs.items()}, a.constant * k)


def affine_mul(a: AffineExpr, b: AffineExpr) -> AffineExpr | None:
    """Multiply two affine expressions. Returns None if result is non-affine.

    Only valid when at least one operand is a pure constant (no variables).
    """
    if not a.coeffs:
        return affine_mul_const(b, a.constant)
    if not b.coeffs:
        return affine_mul_const(a, b.constant)
    # Both have variables → non-affine (e.g. I*J)
    return None


# ── Affine extraction from IR ───────���──────────────────────

def extract_affine(name: str, loop_var: str,
                   defs: dict[str, IRInst],
                   invariants: set[str],
                   depth: int = 0) -> AffineExpr | None:
    """Extract an AffineExpr for an IR temp by walking its defining instructions.

    Returns None if the expression is non-affine (array LOAD, division,
    nonlinear product, unknown origin).

    Args:
        name: the IR variable/temp name to trace
        loop_var: the loop induction variable name
        defs: map of temp name → defining IRInst
        invariants: set of loop-invariant names (PARAMETERs, STATIC scalars)
        depth: recursion depth (safety cutoff at 20)
    """
    if depth > 20:
        return None

    # Loop variable itself
    if name == loop_var:
        return AffineExpr({Symbol(loop_var, SymbolKind.LOOP_VAR): 1}, 0)

    # PARAMETER or loop-invariant scalar
    if name in invariants:
        return AffineExpr({Symbol(name, SymbolKind.PARAMETER): 1}, 0)

    # Not a temp and not known → unknown origin
    if name not in defs:
        return None

    inst = defs[name]

    # LOAD from array = data-dependent → non-affine
    if inst.op == Op.LOAD:
        return None

    # Division = outside affine language
    if inst.op in (Op.DIV, Op.MOD):
        return None

    # Arithmetic: ADD, SUB, MUL
    if inst.op in (Op.ADD, Op.SUB, Op.MUL):
        left = _operand_to_affine(inst.args[0], loop_var, defs, invariants, depth)
        right = _operand_to_affine(inst.args[1], loop_var, defs, invariants, depth)
        if left is None or right is None:
            return None
        if inst.op == Op.ADD:
            return affine_add(left, right)
        if inst.op == Op.SUB:
            return affine_sub(left, right)
        if inst.op == Op.MUL:
            return affine_mul(left, right)

    # Unary negation
    if inst.op == Op.NEG:
        inner = _operand_to_affine(inst.args[0], loop_var, defs, invariants, depth)
        if inner is None:
            return None
        return affine_neg(inner)

    # COPY: trace through
    if inst.op == Op.COPY:
        if len(inst.args) == 1:
            return _operand_to_affine(inst.args[0], loop_var, defs, invariants, depth)
        return None

    # Anything else (CALL, STORE, POW, etc.) — non-affine
    return None


def _operand_to_affine(op: Operand, loop_var: str,
                       defs: dict[str, IRInst],
                       invariants: set[str],
                       depth: int) -> AffineExpr | None:
    """Convert an IR operand to AffineExpr."""
    if isinstance(op, IRConst):
        if op.value is not None and isinstance(op.value, (int, float)):
            return AffineExpr({}, int(op.value))
        return None
    if isinstance(op, IRRef):
        return extract_affine(op.name, loop_var, defs, invariants, depth + 1)
    return None


# ── Shift detection ───��─────────────────────────────────────

def detect_shift(write_expr: AffineExpr, read_expr: AffineExpr,
                 loop_var: str) -> int | None:
    """Detect shift dependency between a write and read of the same array.

    Returns the shift distance k if the write is at f(I) and read is at f(I)-k,
    meaning iteration I depends on iteration I-k. Returns None if the expressions
    have different loop-var coefficients or different PARAMETER terms (not a
    simple shift).

    Example:
        write A(I), read A(I-1) → shift k=1 (each iteration reads previous)
        write A(I), read A(I)   → shift k=0 (no cross-iteration dependency)
    """
    w_stride = write_expr.stride(loop_var)
    r_stride = read_expr.stride(loop_var)

    # Different strides → not a simple shift
    if w_stride != r_stride:
        return None

    # Check that PARAMETER coefficients match
    w_params = {s: c for s, c in write_expr.coeffs.items()
                if s.kind == SymbolKind.PARAMETER}
    r_params = {s: c for s, c in read_expr.coeffs.items()
                if s.kind == SymbolKind.PARAMETER}
    if w_params != r_params:
        return None

    # Shift is the difference in constant terms
    return write_expr.constant - read_expr.constant


# ── Bounds validation ────────────────────────────────────────

def check_bounds(expr: AffineExpr, loop_var: str,
                 lower: int, upper: int, array_size: int,
                 param_values: dict[str, int] | None = None
                 ) -> tuple[bool, int, int]:
    """Check if index expression stays within 1-based array bounds.

    Evaluates the affine expression at the loop bounds to find the min/max
    index values. PARAMETERs must be resolved to concrete values for the
    check to succeed.

    Args:
        expr: the affine index expression
        loop_var: loop induction variable name
        lower: loop lower bound (inclusive)
        upper: loop upper bound (inclusive)
        array_size: declared size of the array dimension being indexed
        param_values: map of PARAMETER name → concrete int value

    Returns:
        (ok, min_idx_1based, max_idx_1based)
        ok is True if all indices are within [1, array_size].
        The returned indices are 1-based (Ergo source level).
        Note: the IR uses 0-based indices internally, but the AffineExpr
        is extracted from the 0-based IR. The IR builder subtracts 1 from
        the source index, so the AffineExpr constant will be offset by -1
        from the source-level expression. We add 1 back to report in
        source terms.
    """
    pvals = param_values or {}

    # Resolve PARAMETER coefficients to constants
    resolved_const = expr.constant
    coeff = expr.loop_var_coeff(loop_var)

    for sym, c in expr.coeffs.items():
        if sym.kind == SymbolKind.PARAMETER:
            if sym.name not in pvals:
                # Can't resolve — skip bounds check
                return True, 0, 0
            resolved_const += c * pvals[sym.name]

    # Evaluate at loop bounds (0-based IR indices)
    val_at_lower = coeff * lower + resolved_const
    val_at_upper = coeff * upper + resolved_const

    if coeff >= 0:
        min_idx_0 = val_at_lower
        max_idx_0 = val_at_upper
    else:
        min_idx_0 = val_at_upper
        max_idx_0 = val_at_lower

    # Convert to 1-based for reporting (IR is 0-based, source is 1-based)
    min_idx_1 = min_idx_0 + 1
    max_idx_1 = max_idx_0 + 1

    ok = (min_idx_1 >= 1 and max_idx_1 <= array_size)
    return ok, min_idx_1, max_idx_1


# ── Classification enum ─────────────────────────────────────

class LoopDependence(Enum):
    """Dependence classification for a DO loop — refinements of FLOW."""
    INJECTIVE = "INJECTIVE"   # compiler proves unique writes (affine, no division)
    FLOW = "FLOW"             # data-dependent index, asserted non-colliding
    SHIFT = "SHIFT"           # same-array read/write at known constant offset
    REDUCTION = "REDUCTION"   # scalar accumulator
    SCATTER = "SCATTER"       # known or possible write collisions
