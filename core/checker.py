"""MCL type checker and semantic validator.

Three-pass analysis:
1. Type checking — type mismatches, undeclared variables, promotion rules
2. Shape propagation — MATMUL/TRANSPOSE output shape vs declared shape
3. Bounds checking — constant array indices against declared dimensions
4. Allocation tracking — ALLOCATABLE used before ALLOCATE, double DEALLOCATE

All errors report MCL source line numbers.
"""

import sys

from . import ast_nodes as ast
from .symbols import SymbolTable, Symbol, FuncSymbol, AllocState
from .errors import MCLError


NUMERIC_TYPES = {"INTEGER", "REAL", "COMPLEX"}

# Character-family types (string literals have type "STRING")
CHAR_TYPES = {"CHARACTER", "STRING"}

# Intrinsic return types (None = depends on argument type)
INTRINSIC_RETURNS = {
    "SIN": "REAL", "COS": "REAL", "TAN": "REAL",
    "ASIN": "REAL", "ACOS": "REAL", "ATAN": "REAL", "ATAN2": "REAL",
    "EXP": "REAL", "LOG": "REAL", "LOG10": "REAL", "SQRT": "REAL",
    "SINH": "REAL", "COSH": "REAL", "TANH": "REAL",
    "REAL": "REAL", "INT": "INTEGER", "CHAR": "CHARACTER",
    "ISHFT": "INTEGER", "IEOR": "INTEGER", "IAND": "INTEGER",
    "IOR": "INTEGER", "NOT": "INTEGER",
    "HASH": "INTEGER", "RAND": "REAL",
    "ABS": None, "MOD": None, "MAX": None, "MIN": None, "CLAMP": None,
    "SIGN": None,
    "SUM": None, "PRODUCT": None, "DOT_PRODUCT": "REAL",
    "NORM2": "REAL", "MAXVAL": None, "MINVAL": None,
    "SIZE": "INTEGER", "RANK": "INTEGER",
    # Array-valued: shape checked by _infer_shape, type is the element type
    "MATMUL": None, "TRANSPOSE": None,
    # Warp ring shuffle intrinsics (GPU backend): type follows first argument
    "RING_PREV": None, "RING_NEXT": None,
    "RING_SHIFT": None, "RING_BROADCAST": None,
    "ZERO": None,  # statement-only: CALL ZERO(array) → memset
}

# Intrinsic argument rules: name -> (min_args, max_args or None, kind)
#   kind "real"        — every argument must be REAL
#   kind "int"         — every argument must be INTEGER
#   kind "numeric"     — every argument must be numeric
#   kind "int_or_real" — every argument must be INTEGER or REAL
#   kind "homo"        — arguments must be all INTEGER or all REAL
INTRINSIC_ARG_RULES = {
    "SIN": (1, 1, "real"), "COS": (1, 1, "real"), "TAN": (1, 1, "real"),
    "ASIN": (1, 1, "real"), "ACOS": (1, 1, "real"), "ATAN": (1, 1, "real"),
    "EXP": (1, 1, "real"), "LOG": (1, 1, "real"), "LOG10": (1, 1, "real"),
    "SQRT": (1, 1, "real"),
    "SINH": (1, 1, "real"), "COSH": (1, 1, "real"), "TANH": (1, 1, "real"),
    "ATAN2": (2, 2, "real"),
    "ABS": (1, 1, "int_or_real"),
    "SIGN": (2, 2, "homo"), "MOD": (2, 2, "homo"),
    "MAX": (2, None, "homo"), "MIN": (2, None, "homo"),
    "CLAMP": (3, 3, "homo"),
    "ISHFT": (2, 2, "int"), "IEOR": (2, 2, "int"),
    "IAND": (2, 2, "int"), "IOR": (2, 2, "int"),
    "NOT": (1, 1, "int"),
    "HASH": (1, 1, "int"), "RAND": (1, 1, "int"),
    "REAL": (1, 1, "numeric"), "INT": (1, 1, "numeric"),
    "CHAR": (1, 1, "int"),
    # Whole-array reductions also get shape validation in
    # _check_reduction_args (the rules below cover the scalar path).
    "DOT_PRODUCT": (2, 2, "real"), "NORM2": (1, 1, "real"),
}

# Intrinsics that are legal as CALL statements
STATEMENT_INTRINSICS = {"ZERO"}


def promote(t1: str, t2: str) -> str:
    if t1 == t2:
        return t1
    if t1 in NUMERIC_TYPES and t2 in NUMERIC_TYPES:
        if "COMPLEX" in (t1, t2):
            return "COMPLEX"
        if "REAL" in (t1, t2):
            return "REAL"
    return t1


def _type_family(t: str) -> str:
    if t in NUMERIC_TYPES:
        return "numeric"
    if t in CHAR_TYPES:
        return "char"
    return t


def comparable(t1: str, t2: str) -> bool:
    """Relational operands are compatible: both numeric, both character,
    or both the same other type (e.g. LOGICAL = LOGICAL)."""
    return _type_family(t1) == _type_family(t2)


class Diagnostic:
    """A single diagnostic message with source location."""

    def __init__(self, level: str, msg: str, line: int = 0, col: int = 0):
        self.level = level  # "error", "warning"
        self.msg = msg
        self.line = line
        self.col = col

    def __str__(self):
        loc = f" [line {self.line}]" if self.line else ""
        return f"ERGO {self.level.upper()}{loc}: {self.msg}"


class Checker:
    """Type checker and semantic validator for MCL AST."""

    def __init__(self):
        self.symtab = SymbolTable()
        self.diagnostics: list[Diagnostic] = []
        self._in_function: str | None = None
        self._in_loop: int = 0  # nesting depth for CYCLE validation
        self._stmt_line: int = 0  # line of enclosing statement (for expr errors)
        self._data_seen: set[str] = set()  # targets of DATA statements (per scope)

    def check(self, tree: ast.Program) -> list[str]:
        """Check the program. Returns list of error strings (empty = success)."""
        # Anything registered before check() runs is a cross-file pre-seed
        # (e.g. the LSP project index); this file's own definitions shadow it.
        for fsym in self.symtab.functions.values():
            fsym.is_external = True

        # Pass 1: register all functions/subroutines
        for unit in tree.units:
            if isinstance(unit, ast.FunctionDef):
                self._register_function(unit)
            elif isinstance(unit, ast.SubroutineDef):
                self._register_subroutine(unit)

        # Pass 2: check all code
        for unit in tree.units:
            self._check_unit(unit)

        # Warnings are printed to stderr; only errors abort compilation.
        # Identical diagnostics (same level, message, line) are reported once.
        errors: list[str] = []
        seen: set = set()
        for d in self.diagnostics:
            key = (d.level, d.msg, d.line)
            if key in seen:
                continue
            seen.add(key)
            if d.level == "warning":
                print(str(d), file=sys.stderr)
            else:
                errors.append(str(d))
        return errors

    def _error(self, msg: str, line: int = 0, col: int = 0):
        self.diagnostics.append(Diagnostic("error", msg, line, col))

    def _warn(self, msg: str, line: int = 0, col: int = 0):
        self.diagnostics.append(Diagnostic("warning", msg, line, col))

    # ── registration ────────────────────────────────────────

    def _register_function(self, fn: ast.FunctionDef):
        param_types = {}
        param_shapes = {}
        for decl in fn.declarations:
            for v in decl.variables:
                param_types[v.name] = decl.type_name
                if v.shape:
                    param_shapes[v.name] = v.shape
        err = self.symtab.declare_func(FuncSymbol(
            name=fn.name,
            return_type=fn.return_type or "REAL",
            param_names=fn.params,
            param_types=param_types,
            param_shapes=param_shapes,
        ))
        if err:
            self._error(err)

    def _register_subroutine(self, fn: ast.SubroutineDef):
        param_types = {}
        param_shapes = {}
        for decl in fn.declarations:
            for v in decl.variables:
                param_types[v.name] = decl.type_name
                if v.shape:
                    param_shapes[v.name] = v.shape
        err = self.symtab.declare_func(FuncSymbol(
            name=fn.name,
            return_type="VOID",
            param_names=fn.params,
            param_types=param_types,
            param_shapes=param_shapes,
            is_subroutine=True,
        ))
        if err:
            self._error(err)

    # ── unit checking ───────────────────────────────────────

    def _check_unit(self, unit):
        if isinstance(unit, ast.FunctionDef):
            self._check_function(unit)
        elif isinstance(unit, ast.SubroutineDef):
            self._check_subroutine(unit)
        elif isinstance(unit, ast.Declaration):
            self._check_declaration(unit)
        elif isinstance(unit, ast.DataStmt):
            self._check_data(unit)
        elif isinstance(unit, ast.ImplicitNone):
            pass
        else:
            self._check_stmt(unit)

    def _check_function(self, fn: ast.FunctionDef):
        self.symtab.enter_scope()
        self._in_function = fn.name
        prev_data_seen = self._data_seen
        self._data_seen = set()

        ret_type = fn.return_type or "REAL"
        self.symtab.declare(Symbol(fn.name, ret_type, None))

        fsym = self.symtab.lookup_func(fn.name)
        for p in fn.params:
            if fsym and p not in fsym.param_types:
                self._error(
                    f"Parameter '{p}' of FUNCTION '{fn.name}' has no "
                    f"type declaration"
                )
            ptype = fsym.param_types.get(p, "REAL") if fsym else "REAL"
            pshape = fsym.param_shapes.get(p) if fsym else None
            self.symtab.declare(Symbol(p, ptype, pshape))

        for decl in fn.declarations:
            self._check_declaration(decl, skip_params=set(fn.params))
        for stmt in fn.body:
            self._check_stmt(stmt)

        self._data_seen = prev_data_seen
        self._in_function = None
        self.symtab.exit_scope()

    def _check_subroutine(self, fn: ast.SubroutineDef):
        self.symtab.enter_scope()
        self._in_function = None
        prev_data_seen = self._data_seen
        self._data_seen = set()

        fsym = self.symtab.lookup_func(fn.name)
        for p in fn.params:
            if fsym and p not in fsym.param_types:
                self._error(
                    f"Parameter '{p}' of SUBROUTINE '{fn.name}' has no "
                    f"type declaration"
                )
            ptype = fsym.param_types.get(p, "INTEGER") if fsym else "INTEGER"
            pshape = fsym.param_shapes.get(p) if fsym else None
            self.symtab.declare(Symbol(p, ptype, pshape))

        for decl in fn.declarations:
            self._check_declaration(decl, skip_params=set(fn.params))
        for stmt in fn.body:
            self._check_stmt(stmt)

        self._data_seen = prev_data_seen
        self.symtab.exit_scope()

    # ── declarations ────────────────────────────────────────

    def _check_declaration(self, decl: ast.Declaration, skip_params: set = None):
        # Declaration initializers are expressions too — point errors at the
        # declaration's own line, not at whatever statement came before.
        decl_line = getattr(decl, "line", 0)
        if decl_line:
            self._stmt_line = decl_line
        skip = skip_params or set()
        for v in decl.variables:
            if v.name in skip:
                continue

            # Resolve shape to ints where possible
            resolved_shape = None
            if v.shape:
                resolved_shape = self._resolve_shape(v.shape)

            alloc_state = AllocState.ALWAYS
            if decl.allocatable:
                alloc_state = AllocState.UNALLOCATED

            # Evaluate PARAMETER const_value
            const_value = None
            if decl.parameter and v.init_value is not None:
                const_value = self._const_eval(v.init_value)
                if const_value is None:
                    # Try float eval for REAL parameters
                    const_value = self._const_eval_real(v.init_value)

            sym = Symbol(
                name=v.name,
                type_name=decl.type_name,
                shape=resolved_shape if resolved_shape else v.shape,
                is_static=decl.static,
                is_allocatable=decl.allocatable,
                is_parameter=decl.parameter,
                const_value=const_value,
                alloc_state=alloc_state,
            )
            err = self.symtab.declare(sym)
            if err:
                self._error(err)

            if v.init_value is not None:
                if v.shape is not None:
                    self._error(
                        f"Initializer on array declaration '{v.name}' is not "
                        f"supported; use DATA or an explicit loop",
                        decl_line,
                    )
                    continue
                init_type = self._infer_type(v.init_value)
                if init_type and init_type != decl.type_name:
                    if (init_type in NUMERIC_TYPES and decl.type_name in NUMERIC_TYPES):
                        pass  # numeric widening is allowed
                    elif not (init_type in CHAR_TYPES and decl.type_name in CHAR_TYPES):
                        self._error(
                            f"Initializer type {init_type} does not match "
                            f"declared type {decl.type_name} for '{v.name}'"
                        )

    def _resolve_shape(self, shape: tuple) -> tuple | None:
        """Try to resolve shape dimensions to integer constants."""
        result = []
        for d in shape:
            if d == ":":
                result.append(":")
            else:
                val = self._const_eval(d)
                result.append(val if val is not None else d)
        return tuple(result)

    def _const_eval(self, node) -> int | None:
        """Try to evaluate an expression as a compile-time integer constant."""
        if isinstance(node, ast.Literal) and node.type == "INTEGER":
            return node.value
        if isinstance(node, ast.Variable):
            sym = self.symtab.lookup(node.name)
            if sym and sym.is_parameter and sym.const_value is not None:
                if isinstance(sym.const_value, int):
                    return sym.const_value
            return None
        if isinstance(node, ast.BinaryOp):
            left = self._const_eval(node.left)
            right = self._const_eval(node.right)
            if left is not None and right is not None:
                if node.op == "+": return left + right
                if node.op == "-": return left - right
                if node.op == "*": return left * right
                if node.op == "/":
                    if right == 0:
                        self._error("Division by zero in constant expression",
                                    self._stmt_line)
                        return None
                    # C truncates integer division toward zero; Python // floors
                    q = abs(left) // abs(right)
                    return q if (left < 0) == (right < 0) else -q
                if node.op == "**":
                    if right < 0:
                        return None  # INTEGER ** negative is rejected in _infer_type
                    return left ** right
        if isinstance(node, ast.UnaryOp) and node.op == "-":
            val = self._const_eval(node.operand)
            if val is not None:
                return -val
        return None

    def _const_eval_real(self, node) -> float | None:
        """Try to evaluate an expression as a compile-time real constant."""
        if isinstance(node, ast.Literal):
            if node.type == "REAL":
                return node.value
            if node.type == "INTEGER":
                return float(node.value)
        if isinstance(node, ast.Variable):
            sym = self.symtab.lookup(node.name)
            if sym and sym.is_parameter and sym.const_value is not None:
                return float(sym.const_value)
            return None
        if isinstance(node, ast.BinaryOp):
            left = self._const_eval_real(node.left)
            right = self._const_eval_real(node.right)
            if left is not None and right is not None:
                if node.op == "+": return left + right
                if node.op == "-": return left - right
                if node.op == "*": return left * right
                if node.op == "/":
                    if right == 0:
                        self._error("Division by zero in constant expression",
                                    self._stmt_line)
                        return None
                    return left / right
                if node.op == "**": return left ** right
        if isinstance(node, ast.UnaryOp) and node.op == "-":
            val = self._const_eval_real(node.operand)
            if val is not None:
                return -val
        return None

    # ── statements ──────────────────────────────────────────

    def _check_stmt(self, node):
        # Track enclosing statement line for expression-level errors
        stmt_line = getattr(node, 'line', 0)
        if stmt_line:
            self._stmt_line = stmt_line
        if isinstance(node, ast.AssignStmt):
            self._check_assign(node)
        elif isinstance(node, ast.IfStmt):
            self._check_if(node)
        elif isinstance(node, ast.DoLoop):
            self._check_do(node)
        elif isinstance(node, ast.DoWhileStmt):
            cond_type = self._infer_type(node.condition)
            if cond_type is not None and cond_type != "LOGICAL":
                self._error(
                    f"DO WHILE condition must be LOGICAL, got {cond_type}",
                    node.line,
                )
            self._in_loop += 1
            for s in node.body:
                self._check_stmt(s)
            self._in_loop -= 1
        elif isinstance(node, ast.SelectCaseStmt):
            self._check_select(node)
        elif isinstance(node, ast.PrintStmt):
            self._infer_type(node.value)
        elif isinstance(node, ast.WriteStmt):
            for arg in node.args:
                self._infer_type(arg)
        elif isinstance(node, ast.ReturnStmt):
            if node.value is not None:
                self._infer_type(node.value)
        elif isinstance(node, ast.CallStmt):
            self._check_call(node)
        elif isinstance(node, ast.AllocateStmt):
            self._check_allocate(node)
        elif isinstance(node, ast.DeallocateStmt):
            self._check_deallocate(node)
        elif isinstance(node, ast.Declaration):
            self._check_declaration(node)
        elif isinstance(node, ast.CycleStmt):
            if self._in_loop == 0:
                self._error("CYCLE used outside of DO loop")
        elif isinstance(node, ast.ExitStmt):
            if self._in_loop == 0:
                self._error("EXIT used outside of DO loop")
        elif isinstance(node, (ast.StopStmt, ast.FlushStmt,
                               ast.ImplicitNone)):
            pass
        elif isinstance(node, ast.DataStmt):
            self._check_data(node)
        elif isinstance(node, ast.VerifyStmt):
            for arr_name in node.arrays:
                sym = self.symtab.lookup(arr_name)
                if not sym:
                    self._error(f"Undefined array '{arr_name}' in VERIFY",
                                node.line)
        elif isinstance(node, ast.SortByGenStmt):
            for arr_name in node.arrays:
                sym = self.symtab.lookup(arr_name)
                if not sym:
                    self._error(f"Undefined array '{arr_name}' in SORT_BY_GEN",
                                node.line)

    def _check_assign(self, node: ast.AssignStmt):
        # Reject assignment to PARAMETER (whole or a subscripted element)
        if isinstance(node.target, (ast.Variable, ast.CallOrSubscript)):
            sym = self.symtab.lookup(node.target.name)
            if sym and sym.is_parameter:
                self._error(
                    f"Cannot assign to PARAMETER '{node.target.name}' — "
                    f"it is a compile-time constant",
                    getattr(node, 'line', 0),
                )

        target_type = self._infer_type(node.target)
        value_type = self._infer_type(node.value)

        if target_type and value_type:
            if target_type != value_type:
                if not (target_type in NUMERIC_TYPES and value_type in NUMERIC_TYPES):
                    if not (target_type in CHAR_TYPES and value_type in CHAR_TYPES):
                        self._error(f"Cannot assign {value_type} to {target_type}")

        # ── Whole-array ↔ scalar assignment ──
        if isinstance(node.target, ast.Variable):
            tsym = self.symtab.lookup(node.target.name)
            if (tsym and tsym.shape is not None and value_type is not None
                    and not self._is_array_valued(node.value)):
                self._error(
                    f"Cannot assign scalar value to array '{node.target.name}' "
                    f"— use an explicit loop or CALL ZERO",
                    getattr(node, 'line', 0),
                )
            elif tsym and tsym.shape is None and self._is_array_valued(node.value):
                self._error(
                    f"Cannot assign array value to scalar '{node.target.name}'",
                    getattr(node, 'line', 0),
                )

        # ── Shape check on assignment ──
        target_shape = self._infer_shape(node.target)
        value_shape = self._infer_shape(node.value)
        if target_shape is not None and value_shape is not None:
            if target_shape != value_shape:
                self._error(
                    f"Shape mismatch in assignment: target has shape {target_shape}, "
                    f"expression has shape {value_shape}"
                )

        # ── Allocation state check on target ──
        if isinstance(node.target, ast.CallOrSubscript):
            sym = self.symtab.lookup(node.target.name)
            if sym and sym.is_allocatable and sym.alloc_state == AllocState.UNALLOCATED:
                self._error(
                    f"Array '{sym.name}' used before ALLOCATE"
                )
        elif isinstance(node.target, ast.Variable):
            sym = self.symtab.lookup(node.target.name)
            if sym and sym.is_allocatable and sym.alloc_state == AllocState.UNALLOCATED:
                self._error(f"Array '{sym.name}' used before ALLOCATE")

    def _is_array_valued(self, e) -> bool:
        """True if the expression denotes a whole array (not a scalar element)."""
        if isinstance(e, ast.Variable):
            sym = self.symtab.lookup(e.name)
            return sym is not None and sym.shape is not None
        if isinstance(e, ast.CallOrSubscript):
            # MATMUL/TRANSPOSE produce arrays; A(i) is a scalar element
            return self._infer_shape(e) is not None
        return False

    def _check_if(self, node: ast.IfStmt):
        self._infer_type(node.condition)
        for s in node.then_body:
            self._check_stmt(s)
        if node.else_body:
            for s in node.else_body:
                self._check_stmt(s)

    def _check_do(self, node: ast.DoLoop):
        sym = self.symtab.lookup(node.var)
        if sym and sym.is_parameter:
            self._error(
                f"PARAMETER '{node.var}' cannot be used as a DO loop "
                f"variable — it is a compile-time constant",
                node.line,
            )
        if sym and sym.type_name != "INTEGER":
            self._error(
                f"DO loop variable '{node.var}' must be INTEGER, "
                f"got {sym.type_name}",
                node.line,
            )

        for expr, label in ((node.start, "start"),
                            (node.end, "end"),
                            (node.step, "step")):
            t = self._infer_type(expr)
            if t is not None and t != "INTEGER":
                self._error(
                    f"DO loop {label} must be INTEGER, got {t}",
                    node.line,
                )
        self._in_loop += 1
        for s in node.body:
            self._check_stmt(s)
        self._in_loop -= 1

    def _check_call(self, node: ast.CallStmt):
        fsym = self.symtab.lookup_func(node.name)
        if fsym:
            if len(node.args) != len(fsym.param_names):
                self._error(
                    f"CALL {node.name}: expected {len(fsym.param_names)} "
                    f"arguments, got {len(node.args)}"
                )
        elif node.name.upper() not in STATEMENT_INTRINSICS:
            self._error(f"Undefined subroutine '{node.name}'", node.line)
        for arg in node.args:
            self._infer_type(arg)

    def _check_select(self, node: ast.SelectCaseStmt):
        expr_type = self._infer_type(node.expr)
        if expr_type is not None and expr_type != "INTEGER":
            self._error(
                f"SELECT CASE selector must be INTEGER, got {expr_type}",
                node.line,
            )
        seen_values: set[int] = set()
        seen_default = False
        for case_val, body in node.cases:
            if case_val is None:
                if seen_default:
                    self._error(
                        "SELECT CASE has more than one CASE DEFAULT",
                        node.line,
                    )
                seen_default = True
            elif isinstance(case_val, ast.Literal) and case_val.type != "INTEGER":
                self._error(
                    f"CASE value must be INTEGER, got {case_val.type}",
                    node.line,
                )
            else:
                v = self._case_literal_value(case_val)
                if v is None:
                    self._error(
                        "CASE value must be a constant INTEGER literal",
                        node.line,
                    )
                elif v in seen_values:
                    self._error(f"Duplicate CASE value {v}", node.line)
                else:
                    seen_values.add(v)
            for s in body:
                self._check_stmt(s)

    @staticmethod
    def _case_literal_value(e) -> int | None:
        """Integer value of a CASE label, or None if not an INTEGER literal."""
        if isinstance(e, ast.Literal) and e.type == "INTEGER":
            return e.value
        if (isinstance(e, ast.UnaryOp) and e.op == "-"
                and isinstance(e.operand, ast.Literal)
                and e.operand.type == "INTEGER"):
            return -e.operand.value
        return None

    # ── DATA statements ───────────────────────────────────────

    def _check_data(self, node: ast.DataStmt):
        line = getattr(node, "line", 0)
        sym = self.symtab.lookup(node.name)
        if sym is None:
            self._error(f"DATA: undeclared variable '{node.name}'", line)
            return
        if sym.name in self._data_seen:
            self._error(
                f"DATA: '{node.name}' is already initialized by a "
                f"previous DATA statement",
                line,
            )
        self._data_seen.add(sym.name)
        if sym.is_allocatable:
            self._error(
                f"DATA: '{node.name}' is ALLOCATABLE; DATA requires "
                f"static storage",
                line,
            )
            return

        # Value count must not exceed the element count
        resolved = sym.resolved_shape()
        if resolved is None:
            if sym.shape is None and len(node.values) != 1:
                self._error(
                    f"DATA: scalar '{node.name}' takes exactly 1 value, "
                    f"got {len(node.values)}",
                    line,
                )
            # runtime-shaped arrays cannot be count-checked at compile time
        else:
            total = 1
            for d in resolved:
                total *= d
            if len(node.values) > total:
                self._error(
                    f"DATA: {len(node.values)} values for '{node.name}', "
                    f"which has only {total} element(s)",
                    line,
                )

        # Values must be literals of a compatible type
        for v in node.values:
            if not isinstance(v, ast.Literal):
                self._error(
                    f"DATA: value for '{node.name}' must be a literal", line)
                continue
            if v.type in NUMERIC_TYPES:
                if sym.type_name not in NUMERIC_TYPES:
                    self._error(
                        f"DATA: {v.type} literal is not compatible with "
                        f"{sym.type_name} '{node.name}'",
                        line,
                    )
            elif v.type == "STRING":
                if sym.type_name != "CHARACTER":
                    self._error(
                        f"DATA: string literal can only initialize a "
                        f"CHARACTER variable, not {sym.type_name} "
                        f"'{node.name}'",
                        line,
                    )
            else:
                self._error(
                    f"DATA: {v.type} literal is not compatible with "
                    f"{sym.type_name} '{node.name}'",
                    line,
                )

    # ── allocation tracking ─────────────────────────────────

    def _check_allocate(self, node: ast.AllocateStmt):
        sym = self.symtab.lookup(node.name)
        if sym is None:
            self._error(f"ALLOCATE: undeclared variable '{node.name}'", node.line)
            return
        if not sym.is_allocatable:
            self._error(f"ALLOCATE: '{node.name}' is not ALLOCATABLE", node.line)
            return
        # Rank must match the declaration
        declared_rank = len(sym.shape) if sym.shape else 0
        if len(node.shape) != declared_rank:
            self._error(
                f"ALLOCATE: '{node.name}' was declared with rank "
                f"{declared_rank}, but is allocated with "
                f"{len(node.shape)} dimension(s)",
                node.line,
            )
        for d in node.shape:
            dt = self._infer_type(d)
            if dt is not None and dt != "INTEGER":
                self._error(
                    f"ALLOCATE: dimension of '{node.name}' must be "
                    f"INTEGER, got {dt}",
                    node.line,
                )
        if sym.alloc_state == AllocState.ALLOCATED:
            self._warn(f"ALLOCATE: '{node.name}' may already be allocated (potential leak)",
                       node.line)
        sym.alloc_state = AllocState.ALLOCATED

    def _check_deallocate(self, node: ast.DeallocateStmt):
        sym = self.symtab.lookup(node.name)
        if sym is None:
            self._error(f"DEALLOCATE: undeclared variable '{node.name}'")
            return
        if not sym.is_allocatable:
            self._error(f"DEALLOCATE: '{node.name}' is not ALLOCATABLE")
            return
        if sym.alloc_state == AllocState.UNALLOCATED:
            self._error(f"DEALLOCATE: '{node.name}' has not been allocated")
        elif sym.alloc_state == AllocState.DEALLOCATED:
            self._error(f"DEALLOCATE: '{node.name}' has already been deallocated (double free)")
        sym.alloc_state = AllocState.DEALLOCATED

    # ── type inference ──────────────────────────────────────

    def _infer_type(self, node) -> str | None:
        if node is None:
            return None

        if isinstance(node, ast.Literal):
            return node.type

        if isinstance(node, ast.Variable):
            if self._in_function and node.name == self._in_function:
                fsym = self.symtab.lookup_func(node.name)
                return fsym.return_type if fsym else "REAL"
            sym = self.symtab.lookup(node.name)
            if sym is None:
                self._error(f"Undeclared variable '{node.name}'",
                            self._stmt_line)
                return None
            # Allocation state check
            if sym.is_allocatable and sym.alloc_state == AllocState.UNALLOCATED:
                self._error(f"Array '{sym.name}' used before ALLOCATE")
            return sym.type_name

        if isinstance(node, ast.BinaryOp):
            left_t = self._infer_type(node.left)
            right_t = self._infer_type(node.right)
            if node.op in (".AND.", ".OR."):
                for t in (left_t, right_t):
                    if t is not None and t != "LOGICAL":
                        self._error(
                            f"{node.op} operand must be LOGICAL, got {t}",
                            self._stmt_line,
                        )
                return "LOGICAL"
            if node.op in ("<", ">", "=", "≠", "≤", "≥"):
                if left_t and right_t and not comparable(left_t, right_t):
                    self._error(
                        f"Cannot compare {left_t} with {right_t}",
                        self._stmt_line,
                    )
                return "LOGICAL"
            if node.op == "**" and left_t == "INTEGER" and right_t == "INTEGER":
                exp = self._const_eval(node.right)
                if exp is not None and exp < 0:
                    self._error(
                        "INTEGER ** INTEGER with negative exponent is a "
                        "compile-time error; use REAL",
                        self._stmt_line,
                    )
            if left_t and right_t:
                return promote(left_t, right_t)
            return left_t or right_t

        if isinstance(node, ast.UnaryOp):
            operand_t = self._infer_type(node.operand)
            if node.op == ".NOT.":
                if operand_t is not None and operand_t != "LOGICAL":
                    self._error(
                        f".NOT. operand must be LOGICAL, got {operand_t}",
                        self._stmt_line,
                    )
                return "LOGICAL"
            return operand_t

        if isinstance(node, ast.CallOrSubscript):
            return self._infer_call_type(node)

        return None

    def _infer_call_type(self, node: ast.CallOrSubscript) -> str | None:
        upper = node.name.upper()

        # Infer every argument type exactly once; the results are reused
        # by the intrinsic validation below (no double inference, no
        # duplicate diagnostics).
        arg_types = [self._infer_type(arg) for arg in node.args]

        # ── Array subscript ──
        sym = self.symtab.lookup(node.name)
        if sym and sym.shape is not None:
            # Bounds checking for constant indices
            self._check_bounds(node, sym)
            # Allocation state
            if sym.is_allocatable and sym.alloc_state == AllocState.UNALLOCATED:
                self._error(f"Array '{sym.name}' used before ALLOCATE",
                            self._stmt_line)
            # Rank check
            if len(node.args) != sym.rank:
                self._error(
                    f"Array '{node.name}' has rank {sym.rank}, "
                    f"indexed with {len(node.args)} dimensions",
                    self._stmt_line,
                )
            return sym.type_name

        # ── Known intrinsic ──
        if upper in INTRINSIC_RETURNS:
            return self._check_intrinsic(upper, node, arg_types)

        # ── User function ──
        fsym = self.symtab.lookup_func(node.name)
        if fsym:
            if len(node.args) != len(fsym.param_names):
                self._error(
                    f"Function {node.name}: expected {len(fsym.param_names)} "
                    f"arguments, got {len(node.args)}"
                )
            return fsym.return_type

        # ── Subscript of a declared scalar ──
        if sym is not None:
            self._error(f"'{node.name}' is not an array", self._stmt_line)
            return sym.type_name

        self._error(f"Undefined function '{node.name}'", self._stmt_line)
        return None

    def _check_intrinsic(self, name: str, node: ast.CallOrSubscript,
                         arg_types: list) -> str | None:
        """Validate intrinsic arity/argument types; return its result type."""
        # DOT_PRODUCT / NORM2 take whole arrays, so they would fall into the
        # element-wise escape below — handle their shape rules explicitly.
        if name in ("DOT_PRODUCT", "NORM2"):
            self._check_reduction_args(name, node, arg_types)
            return self._intrinsic_return(name, arg_types)

        # Element-wise intrinsics on arrays (e.g. SQRT(A)) are in the spec
        # but unimplemented downstream — leave existing behavior alone.
        for a in node.args:
            if self._is_array_valued(a):
                return self._intrinsic_return(name, arg_types)

        rule = INTRINSIC_ARG_RULES.get(name)
        if rule is not None:
            lo, hi, kind = rule
            n = len(node.args)
            if n < lo or (hi is not None and n > hi):
                if lo == hi:
                    want = f"{lo} argument" + ("" if lo == 1 else "s")
                else:
                    want = f"at least {lo} arguments"
                self._error(f"{name} expects {want}, got {n}",
                            self._stmt_line)
                return self._intrinsic_return(name, arg_types)

            known = [t for t in arg_types if t is not None]
            if kind == "real":
                bad = next((t for t in known if t != "REAL"), None)
                if bad:
                    self._error(f"{name} expects REAL, got {bad}",
                                self._stmt_line)
            elif kind == "int":
                bad = next((t for t in known if t != "INTEGER"), None)
                if bad:
                    self._error(f"{name} expects INTEGER, got {bad}",
                                self._stmt_line)
            elif kind == "numeric":
                bad = next((t for t in known if t not in NUMERIC_TYPES), None)
                if bad:
                    self._error(f"{name} expects a numeric argument, "
                                f"got {bad}", self._stmt_line)
            elif kind == "int_or_real":
                bad = next((t for t in known
                            if t not in ("INTEGER", "REAL")), None)
                if bad:
                    self._error(f"{name} expects INTEGER or REAL, got {bad}",
                                self._stmt_line)
            elif kind == "homo":
                distinct = set(known)
                if len(distinct) > 1 or (
                        distinct and not distinct <= {"INTEGER", "REAL"}):
                    got = ", ".join(sorted(distinct))
                    self._error(
                        f"{name} arguments must be all INTEGER or all "
                        f"REAL, got {got}",
                        self._stmt_line,
                    )
        return self._intrinsic_return(name, arg_types)

    def _check_reduction_args(self, name: str, node: ast.CallOrSubscript,
                              arg_types: list):
        """Shape validation for DOT_PRODUCT(a, b) / NORM2(a).

        V1 scope: arguments must be declared 1D REAL arrays whose shape is
        known at compile time (STATIC or local constant-shape). ALLOCATABLE,
        runtime-shaped, and assumed-shape arguments are rejected — the
        lowering needs a compile-time element count and never allocates.
        """
        want = 2 if name == "DOT_PRODUCT" else 1
        n = len(node.args)
        if n != want:
            want_s = f"{want} argument" + ("" if want == 1 else "s")
            self._error(f"{name} expects {want_s}, got {n}",
                        self._stmt_line)
            return

        sizes = []
        for arg, atype in zip(node.args, arg_types):
            if atype is not None and atype != "REAL":
                self._error(f"{name} expects REAL array arguments, "
                            f"got {atype}", self._stmt_line)
                continue
            if not isinstance(arg, ast.Variable):
                self._error(
                    f"{name} argument must be a whole 1D array, "
                    f"not an expression or subscript", self._stmt_line)
                continue
            sym = self.symtab.lookup(arg.name)
            if sym is None or sym.shape is None:
                self._error(
                    f"{name} argument '{arg.name}' must be a declared "
                    f"array", self._stmt_line)
                continue
            if sym.is_allocatable:
                self._error(
                    f"{name}: ALLOCATABLE array '{arg.name}' is not "
                    f"supported — use a STATIC or local constant-shape "
                    f"array", self._stmt_line)
                continue
            resolved = sym.resolved_shape()
            if resolved is None:
                self._error(
                    f"{name}: array '{arg.name}' must have a "
                    f"compile-time-known shape — runtime-shaped and "
                    f"assumed-shape arguments are not supported",
                    self._stmt_line)
                continue
            if len(resolved) != 1:
                self._error(
                    f"{name}: array '{arg.name}' must be 1D, "
                    f"got rank {len(resolved)}", self._stmt_line)
                continue
            sizes.append((arg.name, resolved[0]))

        if (name == "DOT_PRODUCT" and len(sizes) == 2
                and sizes[0][1] != sizes[1][1]):
            self._error(
                f"DOT_PRODUCT: shape mismatch — '{sizes[0][0]}' has "
                f"{sizes[0][1]} elements, '{sizes[1][0]}' has "
                f"{sizes[1][1]}", self._stmt_line)

    @staticmethod
    def _intrinsic_return(name: str, arg_types: list) -> str | None:
        ret = INTRINSIC_RETURNS[name]
        if ret is not None:
            return ret
        if arg_types and arg_types[0]:
            return arg_types[0]
        return "REAL"

    # ── bounds checking ─────────────────────────────────────

    def _check_bounds(self, node: ast.CallOrSubscript, sym: Symbol):
        """Check constant array indices against declared dimensions."""
        resolved = sym.resolved_shape()
        if resolved is None:
            return  # can't check runtime-sized arrays

        for i, arg in enumerate(node.args):
            if i >= len(resolved):
                break
            dim_size = resolved[i]
            idx = self._const_eval(arg)
            if idx is not None:
                if idx < 1:
                    self._error(
                        f"Array '{sym.name}' index {idx} in dimension {i+1} "
                        f"is below lower bound 1",
                        self._stmt_line,
                    )
                elif idx > dim_size:
                    self._error(
                        f"Array '{sym.name}' index {idx} in dimension {i+1} "
                        f"exceeds upper bound {dim_size}",
                        self._stmt_line,
                    )

    # ── shape inference ─────────────────────────────────────

    def _infer_shape(self, node) -> tuple[int, ...] | None:
        """Infer the shape of an expression. Returns None for scalars or unknowns."""
        if isinstance(node, ast.Variable):
            # Whole-array reference (e.g., C in `C := MATMUL(A, B)`)
            return self._get_var_shape(node)

        if isinstance(node, ast.CallOrSubscript):
            upper = node.name.upper()

            # MATMUL(A, B) → (rows(A), cols(B))
            if upper == "MATMUL" and len(node.args) == 2:
                shape_a = self._get_var_shape(node.args[0])
                shape_b = self._get_var_shape(node.args[1])
                if shape_a and shape_b and len(shape_a) == 2 and len(shape_b) == 2:
                    if shape_a[1] != shape_b[0]:
                        self._error(
                            f"MATMUL: inner dimension mismatch — "
                            f"A has {shape_a[1]} columns, B has {shape_b[0]} rows",
                            self._stmt_line,
                        )
                    return (shape_a[0], shape_b[1])

            # TRANSPOSE(A) → (cols(A), rows(A))
            if upper == "TRANSPOSE" and len(node.args) == 1:
                shape_a = self._get_var_shape(node.args[0])
                if shape_a and len(shape_a) == 2:
                    return (shape_a[1], shape_a[0])

            # Array subscript → scalar (no shape)
            sym = self.symtab.lookup(node.name)
            if sym and sym.shape is not None:
                return None  # subscripted = scalar element

        # Scalar expressions have no shape
        return None

    def _get_var_shape(self, node) -> tuple[int, ...] | None:
        """Get the compile-time shape of a variable reference."""
        if isinstance(node, ast.Variable):
            sym = self.symtab.lookup(node.name)
            if sym:
                return sym.resolved_shape()
        return None
