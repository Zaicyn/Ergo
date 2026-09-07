"""Hopf Handshake Bound (HHB) static linter.

Phase-1 implementation: recognizes handshake-shaped blocks marked by
`VERIFY HANDSHAKE <name> [options]` and validates the bounded-recursion
policy from Spec/Hopf_Handshake_Bound_Policy.md.

This module does NOT lower handshakes to special IR. It only emits
named diagnostics. In prototype mode violations are warnings; in
certified mode they are errors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import ast_nodes as ast
from .ir import get_real_precision


@dataclass
class HHBViolation:
    """Single HHB policy violation."""
    kind: str       # e.g. "hhb_depth", "hhb_allocate", "hhb_uncounted"
    message: str
    line: int
    certified: bool = False  # True -> should be a hard error


class HHBLinter:
    """Walk the AST and validate handshake blocks.

    Usage:
        linter = HHBLinter()
        violations = linter.lint(program)
    """

    def __init__(self, certified: bool = False):
        self.certified = certified
        self.violations: list[HHBViolation] = []
        self.definitions: dict[str, ast.SubroutineDef | ast.FunctionDef] = {}
        self.params: set[str] = set()
        self.var_info: dict[str, dict] = {}

    def lint(self, program: ast.Program) -> list[HHBViolation]:
        self.violations = []
        # Index subroutine/function definitions for call analysis.
        self.definitions = {}
        for unit in program.units:
            if isinstance(unit, (ast.FunctionDef, ast.SubroutineDef)):
                self.definitions[unit.name] = unit
        # Index PARAMETERs and variable type/shape info from declarations.
        self.params = set()
        self.var_info = {}
        self._index_declarations(program.units)
        # Program.units is a flat list of top-level statements/declarations.
        self._visit_body(program.units)
        # Also check function/subroutine bodies for nested handshakes.
        for unit in program.units:
            if isinstance(unit, (ast.FunctionDef, ast.SubroutineDef)):
                self._visit_body(unit.body)
        return self.violations

    def _index_declarations(self, units: list):
        """Build PARAMETER set and variable type/shape table."""
        for unit in units:
            if isinstance(unit, ast.Declaration):
                for vd in unit.variables:
                    info = {
                        "type": unit.type_name.upper(),
                        "shape": vd.shape,
                        "parameter": unit.parameter,
                        "allocatable": unit.allocatable,
                        "static": unit.static,
                        "init_value": vd.init_value,
                    }
                    self.var_info[vd.name] = info
                    if unit.parameter:
                        self.params.add(vd.name)
            elif isinstance(unit, (ast.FunctionDef, ast.SubroutineDef)):
                self._index_declarations(unit.declarations)

    # ── AST traversal ─────────────────────────────────────────

    def _visit_body(self, body: list):
        i = 0
        while i < len(body):
            stmt = body[i]
            if isinstance(stmt, ast.VerifyHandshakeStmt):
                # The directive applies to the next statement/block.
                if i + 1 >= len(body):
                    self._add(
                        "hhb_empty",
                        f"VERIFY HANDSHAKE '{stmt.name}' has no following block",
                        stmt.line, certified=True)
                else:
                    target = body[i + 1]
                    self._lint_handshake(stmt, target)
                    i += 1
            else:
                self._visit_stmt(stmt)
            i += 1

    def _visit_stmt(self, stmt: Any):
        if isinstance(stmt, ast.VerifyHandshakeStmt):
            # Top-level directive without a following block is an error;
            # otherwise we rely on _visit_body to pair it with the next stmt.
            pass
        elif isinstance(stmt, ast.HandshakeStmt):
            # Find first counted DO/IF target in the handshake body.
            target = None
            for s in stmt.body:
                if isinstance(s, (ast.DoLoop, ast.IfStmt)):
                    target = s
                    break
            if target is None:
                self._add(
                    "hhb_shape",
                    f"Handshake '{stmt.name}' body must contain a counted "
                    f"DO loop or IF block",
                    stmt.line, certified=True)
            else:
                self._lint_handshake(
                    ast.VerifyHandshakeStmt(stmt.name, stmt.options,
                                            line=stmt.line),
                    target)
            for s in stmt.body:
                self._visit_stmt(s)
        elif isinstance(stmt, ast.IfStmt):
            self._visit_body(stmt.then_body)
            if stmt.else_body:
                self._visit_body(stmt.else_body)
        elif isinstance(stmt, ast.DoLoop):
            self._visit_body(stmt.body)
        elif isinstance(stmt, ast.DoWhileStmt):
            self._visit_body(stmt.body)
        elif isinstance(stmt, ast.SelectCaseStmt):
            for _, case_body in stmt.cases:
                self._visit_body(case_body)

    # ── handshake validation ──────────────────────────────────

    def _lint_handshake(self, directive: ast.VerifyHandshakeStmt,
                        target: Any):
        """Validate a marked block against HHB policy."""
        opts = directive.options
        name = directive.name

        # Basic option checks
        depth = opts.get("DEPTH", 2)
        if depth > 2:
            self._add(
                "hhb_depth",
                f"Handshake '{name}' DEPTH={depth} exceeds maximum 2",
                directive.line, certified=True)

        frame_bytes = opts.get("FRAME_BYTES", 256)
        if frame_bytes > 256:
            self._add(
                "hhb_frame",
                f"Handshake '{name}' FRAME_BYTES={frame_bytes} exceeds 256",
                directive.line, certified=True)

        maxit = opts.get("MAXIT")
        if maxit is None:
            self._add(
                "hhb_maxit",
                f"Handshake '{name}' has no MAXIT bound",
                directive.line, certified=True)
        elif not self._is_static_maxit(maxit):
            self._add(
                "hhb_maxit",
                f"Handshake '{name}' MAXIT={maxit} is not a compile-time "
                f"constant or PARAMETER",
                directive.line, certified=True)

        conserve = opts.get("CONSERVE", [])
        allowed_conserve = {"PARITY", "SPIN", "NODE_COUNT", "NORM"}
        conserve_names = set()
        for item in conserve:
            if isinstance(item, (list, tuple)) and len(item) == 3:
                inv_name, value_expr, tol = item
            else:
                self._add(
                    "hhb_conserve",
                    f"Handshake '{name}' CONSERVE '{item}' malformed",
                    directive.line, certified=True)
                continue
            inv_name = inv_name.upper()
            if inv_name not in allowed_conserve:
                self._add(
                    "hhb_conserve",
                    f"Handshake '{name}' unknown CONSERVE flag '{inv_name}'",
                    directive.line, certified=True)
                continue
            if value_expr is None:
                self._add(
                    "hhb_conserve",
                    f"Handshake '{name}' CONSERVE '{inv_name}' missing VALUE",
                    directive.line, certified=True)
                continue
            if tol is None:
                self._add(
                    "hhb_conserve",
                    f"Handshake '{name}' CONSERVE '{inv_name}' missing TOL",
                    directive.line, certified=True)
                continue
            if tol <= 0.0:
                self._add(
                    "hhb_conserve",
                    f"Handshake '{name}' CONSERVE '{inv_name}' TOL={tol} "
                    f"must be positive",
                    directive.line, certified=True)
                continue
            # Precision floor: f32 cannot meaningfully check tighter than ~1e-6.
            if get_real_precision() == 32 and tol < 1.0E-6:
                self._add(
                    "hhb_conserve",
                    f"Handshake '{name}' CONSERVE '{inv_name}' TOL={tol} "
                    f"is below f32 precision floor (1.0E-6)",
                    directive.line, certified=True)
                continue
            conserve_names.add(inv_name)

        # Target must be a counted DO loop or an IF wrapping counted loops.
        if not isinstance(target, (ast.DoLoop, ast.IfStmt)):
            self._add(
                "hhb_shape",
                f"Handshake '{name}' target must be a counted DO loop or IF",
                directive.line, certified=True)
            return

        # Gather handshake statistics
        ctx = _HandshakeContext(name, depth, maxit)
        self._analyze_block(target, ctx)

        # Report findings
        if ctx.allocates:
            self._add(
                "hhb_allocate",
                f"Handshake '{name}' contains ALLOCATE/DEALLOCATE "
                f"(allocation inside handshake is forbidden)",
                ctx.alloc_line, certified=True)

        if ctx.do_whiles:
            self._add(
                "hhb_uncounted",
                f"Handshake '{name}' contains {ctx.do_whiles} DO WHILE loop(s); "
                f"all loops must be counted DO loops",
                ctx.dw_line, certified=True)

        # Bounded attempt loops accepted this block (proven counted):
        # report each with its implicit MAXIT.
        for ln, bound in ctx.bounded_whiles:
            self._add(
                "hhb_bounded",
                f"Handshake '{name}': bounded attempt loop (DO WHILE, "
                f"line {ln}) is provably counted — implicit MAXIT={bound}",
                ln, certified=False)

        if ctx.uncounted_loops:
            self._add(
                "hhb_uncounted",
                f"Handshake '{name}' contains DO loop(s) without "
                f"compile-time-constant/PARAMETER bounds",
                ctx.uc_line, certified=True)

        # Depth estimate: count top-level counted stages in the target.
        # A single counted DO loop is one stage; an IF with counted loops in
        # each branch counts each branch as a stage. Inner loops are part of
        # a stage, not additional stages.
        stages = self._count_top_stages(target)
        if stages > depth:
            self._add(
                "hhb_depth",
                f"Handshake '{name}' appears to have {stages} activation "
                f"stage(s) but DEPTH={depth}",
                directive.line, certified=True)

        # Payload size check: declared payload + captured CONSERVE invariants
        payload_vars = opts.get("PAYLOAD", [])
        payload_bytes, payload_errors = self._payload_size(payload_vars)
        for msg, line in payload_errors:
            self._add("hhb_payload", msg, line, certified=True)
        # Each CONSERVE invariant captures its VALUE at handshake entry;
        # count one scalar slot (8 bytes for REAL) per invariant.
        conserve_capture_bytes = len(conserve_names) * 8
        payload_bytes += conserve_capture_bytes
        total_budget = 2 * frame_bytes  # ping-pong pair
        if payload_bytes > total_budget:
            self._add(
                "hhb_payload",
                f"Handshake '{name}' total payload {payload_bytes} bytes "
                f"(declared + {conserve_capture_bytes} bytes for CONSERVE capture) "
                f"exceeds budget {total_budget} bytes (FRAME_BYTES={frame_bytes})",
                directive.line, certified=True)
        elif payload_vars and payload_bytes == 0:
            self._add(
                "hhb_payload",
                f"Handshake '{name}' PAYLOAD is empty or all variables unknown",
                directive.line, certified=True)

        # Re-entry / rewind
        if ctx.rewinds > 0 and "MAX_REWIND" not in opts:
            self._add(
                "hhb_rewind",
                f"Handshake '{name}' re-arms a visited stage without "
                f"MAX_REWIND (monotonic activation required)",
                ctx.rewind_line, certified=True)

        # Oracles
        oracles = opts.get("ORACLE", [])
        if not oracles and not ctx.oracles:
            self._add(
                "hhb_oracle",
                f"Handshake '{name}' has no ORACLE/WRITE diagnostic "
                f"(at least one null/limit oracle is required)",
                directive.line, certified=self.certified)
        for spec in oracles:
            oracle_name = spec.get("name", "<unnamed>")
            if "VALUE" not in spec:
                self._add(
                    "hhb_oracle",
                    f"Handshake '{name}' ORACLE '{oracle_name}' missing VALUE",
                    directive.line, certified=True)
            if "LIMIT" not in spec:
                self._add(
                    "hhb_oracle",
                    f"Handshake '{name}' ORACLE '{oracle_name}' missing LIMIT",
                    directive.line, certified=True)
            else:
                limit = spec["LIMIT"]
                if limit <= 0.0:
                    self._add(
                        "hhb_oracle",
                        f"Handshake '{name}' ORACLE '{oracle_name}' "
                        f"LIMIT={limit} must be positive",
                        directive.line, certified=True)
                elif get_real_precision() == 32 and limit < 1.0E-6:
                    self._add(
                        "hhb_oracle",
                        f"Handshake '{name}' ORACLE '{oracle_name}' "
                        f"LIMIT={limit} is below f32 precision floor (1.0E-6)",
                        directive.line, certified=True)

        # Bad payload types
        if ctx.payload_int8:
            self._add(
                "hhb_payload_type",
                f"Handshake '{name}' payload uses INTEGER*8 / COMPLEX "
                f"(forbidden in handshake frame)",
                ctx.payload_int8_line, certified=True)

    def _analyze_block(self, node: Any, ctx: "_HandshakeContext",
                        call_stack: tuple[str, ...] = (),
                        siblings: list | None = None, idx: int | None = None):
        """Recursively analyze a handshake block, collecting statistics."""
        if isinstance(node, ast.DoLoop):
            ctx.note_do_loop(node)
            for i, stmt in enumerate(node.body):
                self._analyze_block(stmt, ctx, call_stack, node.body, i)
        elif isinstance(node, ast.DoWhileStmt):
            bound = self._bounded_attempt_bound(node, siblings, idx)
            if bound is not None:
                ctx.bounded_whiles.append((node.line, bound))
                node.hhb_bound = bound   # for the IR builder (GPU unroll)
            else:
                ctx.note_do_while(node)
            for i, stmt in enumerate(node.body):
                self._analyze_block(stmt, ctx, call_stack, node.body, i)
        elif isinstance(node, ast.IfStmt):
            for i, stmt in enumerate(node.then_body):
                self._analyze_block(stmt, ctx, call_stack, node.then_body, i)
            if node.else_body:
                for i, stmt in enumerate(node.else_body):
                    self._analyze_block(stmt, ctx, call_stack,
                                        node.else_body, i)
        elif isinstance(node, ast.AllocateStmt):
            ctx.note_allocate(node)
        elif isinstance(node, ast.DeallocateStmt):
            ctx.note_allocate(node)
        elif isinstance(node, ast.AssignStmt):
            ctx.note_assign(node)
            self._scan_expr_for_calls(node.value, node.line, ctx, call_stack)
        elif isinstance(node, ast.WriteStmt):
            ctx.note_oracle(node)
        elif isinstance(node, ast.CallStmt):
            self._check_call(node.name, node.line, ctx, call_stack)
        elif isinstance(node, ast.VerifyStmt):
            # A nested regular VERIFY counts as an oracle checkpoint.
            ctx.note_oracle(node)

    def _scan_expr_for_calls(self, expr: Any, line: int,
                             ctx: "_HandshakeContext",
                             call_stack: tuple[str, ...]):
        """Find function calls inside expressions and validate them."""
        if expr is None:
            return
        if isinstance(expr, ast.CallOrSubscript):
            # Ambiguous: could be array subscript or function call. Treat as a
            # function call only if there is a definition with that name.
            if expr.name in self.definitions:
                self._check_call(expr.name, line, ctx, call_stack)
            for arg in expr.args:
                self._scan_expr_for_calls(arg, line, ctx, call_stack)
            return
        if isinstance(expr, ast.BinaryOp):
            self._scan_expr_for_calls(expr.left, line, ctx, call_stack)
            self._scan_expr_for_calls(expr.right, line, ctx, call_stack)
            return
        if isinstance(expr, ast.UnaryOp):
            self._scan_expr_for_calls(expr.operand, line, ctx, call_stack)
            return

    def _check_call(self, name: str, line: int, ctx: "_HandshakeContext",
                    call_stack: tuple[str, ...]):
        """Validate a subroutine/function call inside a handshake.

        Calls to HHB-clean leaf routines are allowed; unknown or
        non-HHB-clean calls are reported.
        """
        if name in call_stack:
            self._add(
                "hhb_call",
                f"Handshake '{ctx.name}' call to '{name}' would recurse",
                line, certified=True)
            return
        definition = self.definitions.get(name)
        if definition is None:
            self._add(
                "hhb_call",
                f"Handshake '{ctx.name}' calls unknown subroutine/function "
                f"'{name}'; handshakes must be self-contained",
                line, certified=True)
            return
        sub_ctx = _HandshakeContext(ctx.name, ctx.depth, ctx.maxit)
        new_stack = call_stack + (name,)
        for i, stmt in enumerate(definition.body):
            self._analyze_block(stmt, sub_ctx, new_stack,
                                definition.body, i)
        # proven-bounded attempt loops in the callee count (and report)
        # at the handshake level
        ctx.bounded_whiles.extend(sub_ctx.bounded_whiles)
        if (sub_ctx.do_whiles or sub_ctx.allocates or
                sub_ctx.uncounted_loops or sub_ctx.rewinds or
                sub_ctx.payload_int8):
            self._add(
                "hhb_call",
                f"Handshake '{ctx.name}' calls '{name}' which contains "
                f"forbidden HHB constructs (uncounted loops, allocation, "
                f"rewind, or bad payload types)",
                line, certified=True)

    def _is_static_maxit(self, maxit: Any) -> bool:
        """MAXIT must be an integer literal or a PARAMETER reference whose
        value is statically known."""
        if isinstance(maxit, int):
            return True
        if isinstance(maxit, str):
            return self._static_int_value(maxit) is not None
        return False

    @staticmethod
    def _target_name(expr: Any) -> str | None:
        """Name of an assignment target (plain scalar only)."""
        if isinstance(expr, ast.Variable):
            return expr.name
        return None

    def _bounded_attempt_bound(self, node: ast.DoWhileStmt,
                               siblings: list | None, idx: int | None
                               ) -> int | None:
        """Prove the bounded-attempt pattern on a DO WHILE; return the
        implicit MAXIT (the bound) or None.

        A `DO WHILE counter < bound` counts as a counted loop when ALL
        hold (any doubt -> None, keep the hard error):
          - condition is `counter < bound` (strict <), counter a single
            INTEGER variable, bound a compile-time constant/PARAMETER;
          - the counter's last top-level write before the loop in the
            same scope assigns a compile-time constant;
          - the body contains exactly one unconditional top-level
            increment `counter := counter + 1`;
          - every other write to the counter is inside an IF branch and
            assigns a constant >= bound (the forced-exit idiom);
          - no nested loop writes the counter.
        """
        cond = node.condition
        if not isinstance(cond, ast.BinaryOp):
            return None
        if cond.op not in ("<", ".LT."):
            return None
        if not isinstance(cond.left, ast.Variable):
            return None
        var = cond.left.name
        info = self.var_info.get(var)
        if info is None or info["type"] != "INTEGER":
            return None
        bound = self._eval_static_dim(cond.right)
        if bound is None or bound <= 0:
            return None

        # Pre-loop: the counter's last top-level write in this scope
        # must assign a compile-time constant.
        if siblings is None or idx is None:
            return None
        last_write = None
        for s in siblings[:idx]:
            if isinstance(s, ast.AssignStmt) and \
                    self._target_name(s.target) == var:
                last_write = s
        if last_write is None:
            return None
        if self._eval_static_dim(last_write.value) is None:
            return None

        # Body: exactly one unconditional top-level increment;
        # any other counter write must be a forced exit inside an IF.
        top_increments = 0
        for s in node.body:
            if isinstance(s, ast.AssignStmt):
                if self._target_name(s.target) != var:
                    continue
                if not self._is_unit_increment(s.value, var):
                    return None
                top_increments += 1
            elif isinstance(s, ast.IfStmt):
                for branch in (s.then_body, s.else_body or []):
                    for ss in branch:
                        if isinstance(ss, ast.AssignStmt) and \
                                self._target_name(ss.target) == var:
                            val = self._eval_static_dim(ss.value)
                            if val is None or val < bound:
                                return None
                        elif self._writes_var_deep(ss, var):
                            return None
            else:
                if self._writes_var_deep(s, var):
                    return None
        if top_increments != 1:
            return None
        return bound

    def _is_unit_increment(self, expr: Any, var: str) -> bool:
        """True for `var := var + 1` / `var := 1 + var`."""
        if not isinstance(expr, ast.BinaryOp) or expr.op != "+":
            return False
        for a, b in ((expr.left, expr.right), (expr.right, expr.left)):
            if isinstance(a, ast.Variable) and a.name == var and \
                    isinstance(b, ast.Literal) and b.value == 1:
                return True
        return False

    def _writes_var_deep(self, stmt: Any, var: str) -> bool:
        """True if `stmt` writes `var` anywhere (including nested)."""
        if isinstance(stmt, ast.AssignStmt):
            return self._target_name(stmt.target) == var
        for body_attr in ("body", "then_body", "else_body"):
            body = getattr(stmt, body_attr, None)
            if body:
                for ss in body:
                    if self._writes_var_deep(ss, var):
                        return True
        return False

    def _static_int_value(self, name: str) -> int | None:
        """Return integer value of a PARAMETER or literal reference."""
        if name in self.params:
            info = self.var_info.get(name)
            if info:
                return self._eval_static_dim(info.get("init_value"))
        return None

    def _payload_size(self, names: list[str]) -> tuple[int, list[tuple[str, int]]]:
        """Compute declared payload size in bytes and collect errors.

        Returns (size, [(error_message, line), ...]).
        """
        total = 0
        errors: list[tuple[str, int]] = []
        for n in names:
            info = self.var_info.get(n)
            if not info:
                errors.append((
                    f"PAYLOAD variable '{n}' is not declared", 0))
                continue
            type_name = info["type"]
            elem_size = self._sizeof_type(type_name)
            if type_name == "COMPLEX":
                errors.append((
                    f"PAYLOAD variable '{n}' has forbidden COMPLEX type", 0))
            shape = info.get("shape")
            if shape:
                dim_size = 1
                for dim in shape:
                    d = self._eval_static_dim(dim)
                    if d is None:
                        errors.append((
                            f"PAYLOAD array '{n}' has non-static dimension "
                            f"'{dim}'", 0))
                        dim_size = None
                        break
                    dim_size *= d
                if dim_size is None:
                    continue
                total += elem_size * dim_size
            else:
                total += elem_size
        return total, errors

    def _sizeof_type(self, type_name: str) -> int:
        return {
            "REAL": 8,
            "INTEGER": 4,
            "LOGICAL": 1,
            "COMPLEX": 16,
            "CHARACTER": 1,
        }.get(type_name.upper(), 8)

    def _eval_static_dim(self, dim: Any) -> int | None:
        """Evaluate a static array dimension (Literal, PARAMETER var, or
        arithmetic combination thereof). Returns None if not static."""
        if isinstance(dim, ast.Literal):
            return int(dim.value)
        if isinstance(dim, ast.Variable):
            return self._static_int_value(dim.name)
        if isinstance(dim, ast.BinaryOp):
            left = self._eval_static_dim(dim.left)
            right = self._eval_static_dim(dim.right)
            if left is None or right is None:
                return None
            if dim.op == "+":
                return left + right
            if dim.op == "-":
                return left - right
            if dim.op == "*":
                return left * right
            if dim.op == "/":
                return left // right
            if dim.op == "**":
                return left ** right
            return None
        if isinstance(dim, ast.UnaryOp):
            val = self._eval_static_dim(dim.operand)
            if val is None:
                return None
            if dim.op == "-":
                return -val
            if dim.op == "+":
                return val
            return None
        if isinstance(dim, int):
            return dim
        return None

    def _count_top_stages(self, node: Any) -> int:
        """Count top-level counted DO-loop stages in target block."""
        if isinstance(node, ast.DoLoop):
            return 1
        if isinstance(node, ast.IfStmt):
            count = 0
            for stmt in node.then_body:
                if isinstance(stmt, ast.DoLoop):
                    count += 1
            for stmt in node.else_body or []:
                if isinstance(stmt, ast.DoLoop):
                    count += 1
            return max(count, 1)
        return 0

    def _add(self, kind: str, message: str, line: int,
             certified: bool = False):
        is_error = certified or self.certified
        self.violations.append(HHBViolation(
            kind, message, line, certified=is_error))


@dataclass
class _HandshakeContext:
    """Mutable analysis state for one handshake block."""
    name: str
    depth: int
    maxit: int | None

    do_loops: int = 0
    do_whiles: int = 0
    allocates: int = 0
    uncounted_loops: int = 0
    stages: int = 0
    rewinds: int = 0
    oracles: int = 0
    payload_int8: bool = False

    # First occurrence lines for diagnostics
    dw_line: int = 0
    uc_line: int = 0
    alloc_line: int = 0
    rewind_line: int = 0
    payload_int8_line: int = 0

    # Variables written in activation-flag style
    activation_vars: set[str] = field(default_factory=set)
    # Variables that look like visited flags
    visited_vars: set[str] = field(default_factory=set)
    # Potential payload variables (scalars written in the block)
    payload_vars: set[str] = field(default_factory=set)
    # Provably-bounded attempt loops accepted as counted: (line, bound)
    bounded_whiles: list = field(default_factory=list)

    def note_do_loop(self, node: ast.DoLoop):
        self.do_loops += 1
        if not self._is_counted(node):
            self.uncounted_loops += 1
            if self.uc_line == 0:
                self.uc_line = node.line
        # Each counted DO loop with a reduction/assignment to a distinct
        # scalar is treated as a propagation stage.
        stage_marker = self._stage_marker(node)
        if stage_marker:
            self.stages += 1

    def note_do_while(self, node: ast.DoWhileStmt):
        self.do_whiles += 1
        if self.dw_line == 0:
            self.dw_line = node.line

    def note_allocate(self, node):
        self.allocates += 1
        if self.alloc_line == 0:
            self.alloc_line = node.line

    def note_assign(self, node: ast.AssignStmt):
        target = self._name_of(node.target)
        if target:
            # Detect visited-flag pattern: FIRED(1)=.TRUE., VISITED(I)=1, etc.
            if (target.upper().startswith("FIRED") or
                    target.upper().startswith("VISITED") or
                    target.upper().startswith("DONE")):
                self.visited_vars.add(target)
            # Detect activation re-entry: assigning false/true to same flag
            if target in self.visited_vars:
                self.rewinds += 1
                if self.rewind_line == 0:
                    self.rewind_line = node.line
            else:
                self.payload_vars.add(target)

    def note_oracle(self, node):
        self.oracles += 1

    def _is_counted(self, node: ast.DoLoop) -> bool:
        """A DO loop is counted if start/end/step are constants or
        PARAMETER refs. We approximate by accepting Literal values and
        Variable refs; a full implementation would use the symbol table."""
        return (self._is_static(node.start) and
                self._is_static(node.end) and
                self._is_static(node.step))

    def _is_static(self, expr: Any) -> bool:
        if expr is None:
            return True
        if isinstance(expr, ast.Literal):
            return True
        if isinstance(expr, ast.Variable):
            # PARAMETERs and loop vars are common; accept variable refs here
            # and let the checker/constant-folder refine later.
            return True
        if isinstance(expr, ast.BinaryOp):
            return (self._is_static(expr.left) and
                    self._is_static(expr.right))
        if isinstance(expr, ast.UnaryOp):
            return self._is_static(expr.operand)
        return False

    def _stage_marker(self, node: ast.DoLoop) -> str | None:
        """Heuristic: a propagation stage is a counted DO loop whose body
        contains an assignment to a scalar that is not a visited flag."""
        for stmt in node.body:
            marker = self._find_scalar_write(stmt)
            if marker and marker not in self.visited_vars:
                return marker
        return None

    def _find_scalar_write(self, node: Any) -> str | None:
        if isinstance(node, ast.AssignStmt):
            return self._name_of(node.target)
        if isinstance(node, ast.IfStmt):
            for stmt in node.then_body:
                m = self._find_scalar_write(stmt)
                if m:
                    return m
            if node.else_body:
                for stmt in node.else_body:
                    m = self._find_scalar_write(stmt)
                    if m:
                        return m
        if isinstance(node, (ast.DoLoop, ast.DoWhileStmt)):
            for stmt in node.body:
                m = self._find_scalar_write(stmt)
                if m:
                    return m
        return None

    def _name_of(self, expr: Any) -> str | None:
        if isinstance(expr, ast.Variable):
            return expr.name
        # Array subscripts are CallOrSubscript nodes in this AST; skip them
        # for payload/visited-flag naming.
        return None

    def estimate_payload_bytes(self) -> int:
        """Rough payload estimate: 8 bytes per REAL scalar, 4 per INTEGER."""
        # Without type info we assume mixed; use 8 bytes per scalar.
        return len(self.payload_vars) * 8


# ast_nodes uses CallOrSubscript for both calls and subscripts; we only
# need Variable targets here.
