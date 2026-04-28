"""MCL type checker and semantic validator.

Three-pass analysis:
1. Type checking — type mismatches, undeclared variables, promotion rules
2. Shape propagation — MATMUL/TRANSPOSE output shape vs declared shape
3. Bounds checking — constant array indices against declared dimensions
4. Allocation tracking — ALLOCATABLE used before ALLOCATE, double DEALLOCATE

All errors report MCL source line numbers.
"""

from . import ast_nodes as ast
from .symbols import SymbolTable, Symbol, FuncSymbol, AllocState
from .errors import MCLError


NUMERIC_TYPES = {"INTEGER", "REAL", "COMPLEX"}

# Intrinsic return types (None = depends on argument type)
INTRINSIC_RETURNS = {
    "SIN": "REAL", "COS": "REAL", "TAN": "REAL",
    "ASIN": "REAL", "ACOS": "REAL", "ATAN": "REAL", "ATAN2": "REAL",
    "EXP": "REAL", "LOG": "REAL", "LOG10": "REAL", "SQRT": "REAL",
    "SINH": "REAL", "COSH": "REAL", "TANH": "REAL",
    "REAL": "REAL", "INT": "INTEGER", "CHAR": "CHARACTER",
    "ISHFT": "INTEGER", "IEOR": "INTEGER", "IAND": "INTEGER",
    "IOR": "INTEGER", "NOT": "INTEGER",
    "ABS": None, "MOD": None, "MAX": None, "MIN": None, "CLAMP": None,
    "SUM": None, "PRODUCT": None, "DOT_PRODUCT": "REAL",
    "NORM2": "REAL", "MAXVAL": None, "MINVAL": None,
    "SIZE": "INTEGER", "RANK": "INTEGER",
    "ZERO": None,  # statement-only: CALL ZERO(array) → memset
}


def promote(t1: str, t2: str) -> str:
    if t1 == t2:
        return t1
    if t1 in NUMERIC_TYPES and t2 in NUMERIC_TYPES:
        if "COMPLEX" in (t1, t2):
            return "COMPLEX"
        if "REAL" in (t1, t2):
            return "REAL"
    return t1


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

    def check(self, tree: ast.Program) -> list[str]:
        """Check the program. Returns list of error strings (empty = success)."""
        # Pass 1: register all functions/subroutines
        for unit in tree.units:
            if isinstance(unit, ast.FunctionDef):
                self._register_function(unit)
            elif isinstance(unit, ast.SubroutineDef):
                self._register_subroutine(unit)

        # Pass 2: check all code
        for unit in tree.units:
            self._check_unit(unit)

        return [str(d) for d in self.diagnostics if d.level == "error"]

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
        self.symtab.declare_func(FuncSymbol(
            name=fn.name,
            return_type=fn.return_type or "REAL",
            param_names=fn.params,
            param_types=param_types,
            param_shapes=param_shapes,
        ))

    def _register_subroutine(self, fn: ast.SubroutineDef):
        param_types = {}
        param_shapes = {}
        for decl in fn.declarations:
            for v in decl.variables:
                param_types[v.name] = decl.type_name
                if v.shape:
                    param_shapes[v.name] = v.shape
        self.symtab.declare_func(FuncSymbol(
            name=fn.name,
            return_type="VOID",
            param_names=fn.params,
            param_types=param_types,
            param_shapes=param_shapes,
            is_subroutine=True,
        ))

    # ── unit checking ───────────────────────────────────────

    def _check_unit(self, unit):
        if isinstance(unit, ast.FunctionDef):
            self._check_function(unit)
        elif isinstance(unit, ast.SubroutineDef):
            self._check_subroutine(unit)
        elif isinstance(unit, ast.Declaration):
            self._check_declaration(unit)
        elif isinstance(unit, (ast.DataStmt, ast.ImplicitNone)):
            pass
        else:
            self._check_stmt(unit)

    def _check_function(self, fn: ast.FunctionDef):
        self.symtab.enter_scope()
        self._in_function = fn.name

        ret_type = fn.return_type or "REAL"
        self.symtab.declare(Symbol(fn.name, ret_type, None))

        fsym = self.symtab.lookup_func(fn.name)
        for p in fn.params:
            ptype = fsym.param_types.get(p, "REAL") if fsym else "REAL"
            pshape = fsym.param_shapes.get(p) if fsym else None
            self.symtab.declare(Symbol(p, ptype, pshape))

        for decl in fn.declarations:
            self._check_declaration(decl, skip_params=set(fn.params))
        for stmt in fn.body:
            self._check_stmt(stmt)

        self._in_function = None
        self.symtab.exit_scope()

    def _check_subroutine(self, fn: ast.SubroutineDef):
        self.symtab.enter_scope()
        self._in_function = None

        fsym = self.symtab.lookup_func(fn.name)
        for p in fn.params:
            ptype = fsym.param_types.get(p, "INTEGER") if fsym else "INTEGER"
            pshape = fsym.param_shapes.get(p) if fsym else None
            self.symtab.declare(Symbol(p, ptype, pshape))

        for decl in fn.declarations:
            self._check_declaration(decl, skip_params=set(fn.params))
        for stmt in fn.body:
            self._check_stmt(stmt)

        self.symtab.exit_scope()

    # ── declarations ────────────────────────────────────────

    def _check_declaration(self, decl: ast.Declaration, skip_params: set = None):
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
                init_type = self._infer_type(v.init_value)
                if init_type and init_type != decl.type_name:
                    if not (init_type in NUMERIC_TYPES and decl.type_name in NUMERIC_TYPES):
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
                if node.op == "/" and right != 0: return left // right
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
                if node.op == "/" and right != 0: return left / right
                if node.op == "**": return left ** right
        if isinstance(node, ast.UnaryOp) and node.op == "-":
            val = self._const_eval_real(node.operand)
            if val is not None:
                return -val
        return None

    # ── statements ──────────────────────────────────────────

    def _check_stmt(self, node):
        if isinstance(node, ast.AssignStmt):
            self._check_assign(node)
        elif isinstance(node, ast.IfStmt):
            self._check_if(node)
        elif isinstance(node, ast.DoLoop):
            self._check_do(node)
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
        elif isinstance(node, (ast.StopStmt, ast.FlushStmt,
                               ast.ImplicitNone, ast.DataStmt)):
            pass
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
        # Reject assignment to PARAMETER
        if isinstance(node.target, ast.Variable):
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
                    self._error(f"Cannot assign {value_type} to {target_type}")

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

    def _check_if(self, node: ast.IfStmt):
        self._infer_type(node.condition)
        for s in node.then_body:
            self._check_stmt(s)
        if node.else_body:
            for s in node.else_body:
                self._check_stmt(s)

    def _check_do(self, node: ast.DoLoop):
        sym = self.symtab.lookup(node.var)
        if sym and sym.type_name != "INTEGER":
            self._error(f"DO loop variable '{node.var}' must be INTEGER, got {sym.type_name}")

        self._infer_type(node.start)
        self._infer_type(node.end)
        self._infer_type(node.step)
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
        for arg in node.args:
            self._infer_type(arg)

    def _check_select(self, node: ast.SelectCaseStmt):
        expr_type = self._infer_type(node.expr)
        for case_val, body in node.cases:
            if case_val is not None:
                val_type = self._infer_type(case_val)
                if expr_type and val_type and expr_type != val_type:
                    if not (expr_type in NUMERIC_TYPES and val_type in NUMERIC_TYPES):
                        self._error(
                            f"SELECT CASE type mismatch: expression is {expr_type}, "
                            f"case value is {val_type}"
                        )
            for s in body:
                self._check_stmt(s)

    # ── allocation tracking ─────────────────────────────────

    def _check_allocate(self, node: ast.AllocateStmt):
        sym = self.symtab.lookup(node.name)
        if sym is None:
            self._error(f"ALLOCATE: undeclared variable '{node.name}'")
            return
        if not sym.is_allocatable:
            self._error(f"ALLOCATE: '{node.name}' is not ALLOCATABLE")
            return
        if sym.alloc_state == AllocState.ALLOCATED:
            self._warn(f"ALLOCATE: '{node.name}' may already be allocated (potential leak)")
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
                self._error(f"Undeclared variable '{node.name}'")
                return None
            # Allocation state check
            if sym.is_allocatable and sym.alloc_state == AllocState.UNALLOCATED:
                self._error(f"Array '{sym.name}' used before ALLOCATE")
            return sym.type_name

        if isinstance(node, ast.BinaryOp):
            left_t = self._infer_type(node.left)
            right_t = self._infer_type(node.right)
            if node.op in ("<", ">", "=", "≠", "≤", "≥", ".AND.", ".OR."):
                return "LOGICAL"
            if left_t and right_t:
                return promote(left_t, right_t)
            return left_t or right_t

        if isinstance(node, ast.UnaryOp):
            operand_t = self._infer_type(node.operand)
            if node.op == ".NOT.":
                return "LOGICAL"
            return operand_t

        if isinstance(node, ast.CallOrSubscript):
            return self._infer_call_type(node)

        return None

    def _infer_call_type(self, node: ast.CallOrSubscript) -> str | None:
        upper = node.name.upper()

        # Check all arguments
        for arg in node.args:
            self._infer_type(arg)

        # ── Array subscript ──
        sym = self.symtab.lookup(node.name)
        if sym and sym.shape is not None:
            # Bounds checking for constant indices
            self._check_bounds(node, sym)
            # Allocation state
            if sym.is_allocatable and sym.alloc_state == AllocState.UNALLOCATED:
                self._error(f"Array '{sym.name}' used before ALLOCATE")
            # Rank check
            if len(node.args) != sym.rank:
                self._error(
                    f"Array '{node.name}' has rank {sym.rank}, "
                    f"indexed with {len(node.args)} dimensions"
                )
            return sym.type_name

        # ── Known intrinsic ──
        if upper in INTRINSIC_RETURNS:
            ret = INTRINSIC_RETURNS[upper]
            if ret is not None:
                return ret
            arg_type = self._infer_type(node.args[0]) if node.args else "REAL"
            return arg_type

        # ── User function ──
        fsym = self.symtab.lookup_func(node.name)
        if fsym:
            if len(node.args) != len(fsym.param_names):
                self._error(
                    f"Function {node.name}: expected {len(fsym.param_names)} "
                    f"arguments, got {len(node.args)}"
                )
            return fsym.return_type

        return None

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
                        f"is below lower bound 1"
                    )
                elif idx > dim_size:
                    self._error(
                        f"Array '{sym.name}' index {idx} in dimension {i+1} "
                        f"exceeds upper bound {dim_size}"
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
                            f"A has {shape_a[1]} columns, B has {shape_b[0]} rows"
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
