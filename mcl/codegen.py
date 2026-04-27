"""C code generator for MCL AST.

Guarantees:
- STATIC declarations emit file-scope `static` variables (direct addressing, no indirection).
- Arrays use direct C indexing with 1-based → 0-based offset.
- Bitwise intrinsics (ISHFT, IEOR, IAND, IOR, NOT) lower to C operators.
"""

from . import ast_nodes as ast


C_TYPE = {
    "REAL": "double",
    "INTEGER": "int",
    "LOGICAL": "int",
    "COMPLEX": "double _Complex",
}

RELOP_MAP = {
    "<": "<", ">": ">", "=": "==",
    "≠": "!=", "≤": "<=", "≥": ">=",
}

# Math intrinsics → C function name
C_MATH = {
    "SIN": "sin", "COS": "cos", "TAN": "tan",
    "ASIN": "asin", "ACOS": "acos", "ATAN": "atan", "ATAN2": "atan2",
    "EXP": "exp", "LOG": "log", "LOG10": "log10",
    "SQRT": "sqrt",
    "SINH": "sinh", "COSH": "cosh", "TANH": "tanh",
}


class CodeGen:
    def __init__(self, tree: ast.Program, source_file: str = None):
        self.tree = tree
        self.lines: list[str] = []
        self.indent = 0
        # Source file path for #line directives
        self.source_file = source_file
        self._last_line_directive = 0
        # Track variable types for PRINT format and array detection
        self.var_types: dict[str, str] = {}
        # Track which names are arrays (have shape) for subscript codegen
        self.array_shapes: dict[str, tuple] = {}
        # Track which names are STATIC or PARAMETER
        self.static_vars: set[str] = set()
        self.parameter_vars: set[str] = set()
        # Track function return types
        self.func_return_types: dict[str, str] = {}
        # Pending DATA initializers: name → list of values
        self.data_inits: dict[str, list] = {}
        # Current function's return variable name (for Fortran-style returns)
        self._func_ret_var: str | None = None

    def generate(self) -> str:
        self.lines.append("#include <stdio.h>")
        self.lines.append("#include <math.h>")
        self.lines.append("#include <stdlib.h>")
        self.lines.append("#include <string.h>")
        self.lines.append("")

        # First pass: collect STATIC declarations, DATA statements,
        # function signatures, to inform codegen
        self._collect_metadata()

        # Emit STATIC and PARAMETER declarations at file scope
        statics = []
        parameters = []
        data_stmts = []
        functions = []
        main_stmts = []
        for unit in self.tree.units:
            if isinstance(unit, ast.Declaration) and unit.parameter:
                parameters.append(unit)
            elif isinstance(unit, ast.Declaration) and unit.static:
                statics.append(unit)
            elif isinstance(unit, ast.DataStmt):
                data_stmts.append(unit)
            elif isinstance(unit, (ast.FunctionDef, ast.SubroutineDef)):
                functions.append(unit)
            else:
                main_stmts.append(unit)

        # Collect DATA initializers
        for ds in data_stmts:
            self.data_inits[ds.name] = ds.values

        # Emit PARAMETER constants at file scope
        for decl in parameters:
            self._emit_parameter_decl(decl)
        if parameters:
            self._put("")

        # Forward declarations for functions
        for fn in functions:
            self._emit_forward_decl(fn)
        if functions:
            self._put("")

        # Emit STATIC vars at file scope
        for decl in statics:
            self._emit_static_decl(decl)
        if statics:
            self._put("")

        # Emit functions
        for fn in functions:
            self._emit_function(fn)
            self._put("")

        # Emit main
        self._put("int main(void) {")
        self.indent += 1
        for stmt in main_stmts:
            self._emit_stmt(stmt)
        self._put("return 0;")
        self.indent -= 1
        self._put("}")
        return "\n".join(self.lines) + "\n"

    # ── metadata collection ──────────────────────────────────

    def _collect_metadata(self):
        for unit in self.tree.units:
            if isinstance(unit, ast.Declaration):
                for v in unit.variables:
                    self.var_types[v.name] = unit.type_name
                    if v.shape:
                        self.array_shapes[v.name] = v.shape
                    if unit.static:
                        self.static_vars.add(v.name)
                    if unit.parameter:
                        self.parameter_vars.add(v.name)
            elif isinstance(unit, ast.FunctionDef):
                ret = unit.return_type or "REAL"
                self.func_return_types[unit.name] = ret
                # Also collect param/local types
                for decl in unit.declarations:
                    for v in decl.variables:
                        self.var_types[v.name] = decl.type_name
                        if v.shape:
                            self.array_shapes[v.name] = v.shape

    # ── helpers ──────────────────────────────────────────────

    def _put(self, line: str):
        self.lines.append("    " * self.indent + line)

    def _emit_line_directive(self, node):
        """Emit #line directive if the node has source line info."""
        if self.source_file and hasattr(node, 'line') and node.line > 0:
            if node.line != self._last_line_directive:
                self.lines.append(f'#line {node.line} "{self.source_file}"')
                self._last_line_directive = node.line

    def _c_type(self, type_name: str) -> str:
        return C_TYPE.get(type_name, "double")

    # ── PARAMETER declarations (file scope, const) ────────────

    def _emit_parameter_decl(self, decl: ast.Declaration):
        self._emit_line_directive(decl)
        c_type = self._c_type(decl.type_name)
        for v in decl.variables:
            init = self._expr(v.init_value)
            # Integer PARAMETERs must be #define so they work as C array dims
            if decl.type_name == "INTEGER":
                self._put(f"#define {v.name} {init}")
            else:
                self._put(f"static const {c_type} {v.name} = {init};")

    # ── STATIC declarations (file scope) ─────────────────────

    def _emit_static_decl(self, decl: ast.Declaration):
        c_type = self._c_type(decl.type_name)
        for v in decl.variables:
            if v.shape:
                dims = "".join(f"[{self._expr(d)}]" for d in v.shape)
                init = self._static_array_init(v.name, v.shape, c_type)
                self._put(f"static {c_type} {v.name}{dims}{init};")
            else:
                init = ""
                # Inline initializer: STATIC INTEGER :: X = 5
                if v.init_value is not None:
                    init = f" = {self._expr(v.init_value)}"
                elif v.name in self.data_inits:
                    vals = self.data_inits[v.name]
                    if vals:
                        init = f" = {self._expr(vals[0])}"
                self._put(f"static {c_type} {v.name}{init};")

    def _static_array_init(self, name: str, shape: tuple, c_type: str) -> str:
        """Generate initializer for static array from DATA statement."""
        if name not in self.data_inits:
            return ""
        vals = self.data_inits[name]
        if not vals:
            return ""
        val_strs = [self._expr(v) for v in vals]
        return " = {" + ", ".join(val_strs) + "}"

    # ── forward declarations ─────────────────────────────────

    def _emit_forward_decl(self, fn):
        if isinstance(fn, ast.FunctionDef):
            ret = self._c_type(fn.return_type or "REAL")
            params = self._func_params(fn)
            self._put(f"{ret} {fn.name}({params});")
        elif isinstance(fn, ast.SubroutineDef):
            params = self._sub_params(fn)
            self._put(f"void {fn.name}({params});")

    # ── functions ────────────────────────────────────────────

    def _emit_function(self, fn):
        if isinstance(fn, ast.FunctionDef):
            self._emit_func_def(fn)
        elif isinstance(fn, ast.SubroutineDef):
            self._emit_sub_def(fn)

    def _func_params(self, fn: ast.FunctionDef) -> str:
        param_types = {}
        for decl in fn.declarations:
            for v in decl.variables:
                param_types[v.name] = decl.type_name
                if v.shape:
                    self.array_shapes[v.name] = v.shape
        parts = []
        for p in fn.params:
            ct = self._c_type(param_types.get(p, "REAL"))
            # Check if param is an array
            if p in self.array_shapes:
                shape = self.array_shapes[p]
                # First dim as pointer, rest as fixed
                if len(shape) == 1:
                    parts.append(f"{ct} {p}[]")
                else:
                    dims = "".join(f"[{self._expr(d)}]" for d in shape[1:])
                    parts.append(f"{ct} {p}[][{dims[1:-1]}]" if len(shape) > 1 else f"{ct} *{p}")
            else:
                parts.append(f"{ct} {p}")
        if not parts:
            return "void"
        return ", ".join(parts)

    def _sub_params(self, fn: ast.SubroutineDef) -> str:
        param_types = {}
        for decl in fn.declarations:
            for v in decl.variables:
                param_types[v.name] = decl.type_name
                if v.shape:
                    self.array_shapes[v.name] = v.shape
        parts = []
        for p in fn.params:
            ct = self._c_type(param_types.get(p, "INTEGER"))
            if p in self.array_shapes:
                parts.append(f"{ct} *{p}")
            else:
                # Value parameters — MCL has no hidden pointers
                parts.append(f"{ct} {p}")
        if not parts:
            return "void"
        return ", ".join(parts)

    def _emit_func_def(self, fn: ast.FunctionDef):
        ret = self._c_type(fn.return_type or "REAL")
        params = self._func_params(fn)
        self._put(f"{ret} {fn.name}({params}) {{")
        self.indent += 1

        # Declare return variable (Fortran idiom: function name is a variable)
        self._put(f"{ret} {fn.name}_;")
        self._func_ret_var = fn.name

        # Declare locals (skip params)
        param_set = set(fn.params)
        for decl in fn.declarations:
            c_type = self._c_type(decl.type_name)
            for v in decl.variables:
                if v.name not in param_set:
                    self.var_types[v.name] = decl.type_name
                    if v.shape:
                        self.array_shapes[v.name] = v.shape
                        dims = "".join(f"[{self._expr(d)}]" for d in v.shape)
                        self._put(f"{c_type} {v.name}{dims};")
                    else:
                        self._put(f"{c_type} {v.name};")
                else:
                    self.var_types[v.name] = decl.type_name

        for stmt in fn.body:
            self._emit_stmt(stmt)

        self._func_ret_var = None
        self.indent -= 1
        self._put("}")

    def _emit_sub_def(self, fn: ast.SubroutineDef):
        params = self._sub_params(fn)
        self._put(f"void {fn.name}({params}) {{")
        self.indent += 1

        param_set = set(fn.params)
        for decl in fn.declarations:
            c_type = self._c_type(decl.type_name)
            for v in decl.variables:
                if v.name not in param_set:
                    self.var_types[v.name] = decl.type_name
                    if v.shape:
                        self.array_shapes[v.name] = v.shape
                        dims = "".join(f"[{self._expr(d)}]" for d in v.shape)
                        self._put(f"{c_type} {v.name}{dims};")
                    else:
                        self._put(f"{c_type} {v.name};")
                else:
                    self.var_types[v.name] = decl.type_name

        for stmt in fn.body:
            self._emit_stmt(stmt)

        self.indent -= 1
        self._put("}")

    # ── statements ───────────────────────────────────────────

    def _emit_stmt(self, node):
        self._emit_line_directive(node)
        if isinstance(node, ast.Declaration):
            self._emit_decl(node)
        elif isinstance(node, ast.AssignStmt):
            self._emit_assign(node)
        elif isinstance(node, ast.IfStmt):
            self._emit_if(node)
        elif isinstance(node, ast.DoLoop):
            self._emit_do(node)
        elif isinstance(node, ast.PrintStmt):
            self._emit_print(node)
        elif isinstance(node, ast.ReturnStmt):
            self._emit_return(node)
        elif isinstance(node, ast.CallStmt):
            if node.name.upper() == "ZERO" and len(node.args) == 1:
                arg = node.args[0]
                if isinstance(arg, ast.Variable) and arg.name in self.array_shapes:
                    self._put(f"memset({arg.name}, 0, sizeof({arg.name}));")
                else:
                    args = ", ".join(self._call_arg(a) for a in node.args)
                    self._put(f"{node.name}({args});")
            else:
                args = ", ".join(self._call_arg(a) for a in node.args)
                self._put(f"{node.name}({args});")
        elif isinstance(node, ast.AllocateStmt):
            self._emit_allocate(node)
        elif isinstance(node, ast.DeallocateStmt):
            self._put(f"free({node.name}); {node.name} = NULL;")
        elif isinstance(node, ast.SelectCaseStmt):
            self._emit_select_case(node)
        elif isinstance(node, ast.WriteStmt):
            self._emit_write(node)
        elif isinstance(node, ast.CycleStmt):
            self._put("continue;")
        elif isinstance(node, ast.StopStmt):
            self._put("return 0;")
        elif isinstance(node, ast.FlushStmt):
            self._put("fflush(stdout);")
        elif isinstance(node, ast.ImplicitNone):
            pass
        elif isinstance(node, ast.DataStmt):
            pass  # handled at file scope

    def _emit_decl(self, node: ast.Declaration):
        c_type = self._c_type(node.type_name)
        if node.parameter:
            for v in node.variables:
                self.var_types[v.name] = node.type_name
                init = self._expr(v.init_value)
                self._put(f"const {c_type} {v.name} = {init};")
            return
        for v in node.variables:
            self.var_types[v.name] = node.type_name
            if node.allocatable:
                self._put(f"{c_type} *{v.name} = NULL;")
            elif v.shape:
                self.array_shapes[v.name] = v.shape
                dims = "".join(f"[{self._expr(d)}]" for d in v.shape)
                # Check for DATA initializer
                init = self._static_array_init(v.name, v.shape, c_type)
                self._put(f"{c_type} {v.name}{dims}{init};")
            else:
                init = ""
                if v.init_value is not None:
                    init = f" = {self._expr(v.init_value)}"
                self._put(f"{c_type} {v.name}{init};")

    def _emit_assign(self, node: ast.AssignStmt):
        target = self._lvalue(node.target)
        value = self._expr(node.value)
        self._put(f"{target} = {value};")

    def _emit_if(self, node: ast.IfStmt):
        cond = self._expr(node.condition)
        self._put(f"if ({cond}) {{")
        self.indent += 1
        for s in node.then_body:
            self._emit_stmt(s)
        self.indent -= 1
        if node.else_body:
            # Check if else_body is a single IfStmt (ELSEIF chain)
            if (len(node.else_body) == 1
                    and isinstance(node.else_body[0], ast.IfStmt)):
                inner = node.else_body[0]
                cond2 = self._expr(inner.condition)
                self._put(f"}} else if ({cond2}) {{")
                self.indent += 1
                for s in inner.then_body:
                    self._emit_stmt(s)
                self.indent -= 1
                if inner.else_body:
                    self._emit_else_chain(inner.else_body)
                else:
                    self._put("}")
            else:
                self._put("} else {")
                self.indent += 1
                for s in node.else_body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._put("}")
        else:
            self._put("}")

    def _emit_else_chain(self, else_body):
        """Continue emitting else-if chain."""
        if (len(else_body) == 1 and isinstance(else_body[0], ast.IfStmt)):
            inner = else_body[0]
            cond = self._expr(inner.condition)
            self._put(f"}} else if ({cond}) {{")
            self.indent += 1
            for s in inner.then_body:
                self._emit_stmt(s)
            self.indent -= 1
            if inner.else_body:
                self._emit_else_chain(inner.else_body)
            else:
                self._put("}")
        else:
            self._put("} else {")
            self.indent += 1
            for s in else_body:
                self._emit_stmt(s)
            self.indent -= 1
            self._put("}")

    def _emit_select_case(self, node: ast.SelectCaseStmt):
        expr = self._expr(node.expr)
        self._put(f"switch ({expr}) {{")
        self.indent += 1
        for case_val, body in node.cases:
            if case_val is None:
                self._put("default: {")
            else:
                self._put(f"case {self._expr(case_val)}: {{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self._put("break;")
            self.indent -= 1
            self._put("}")
        self.indent -= 1
        self._put("}")

    def _emit_do(self, node: ast.DoLoop):
        var = node.var
        start = self._expr(node.start)
        end = self._expr(node.end)
        step = self._expr(node.step)
        self._put(f"for (int {var} = {start}; {var} <= {end}; {var} += {step}) {{")
        self.indent += 1
        for s in node.body:
            self._emit_stmt(s)
        self.indent -= 1
        self._put("}")

    def _emit_print(self, node: ast.PrintStmt):
        val = self._expr(node.value)
        fmt = self._format_for(node.value)
        self._put(f'printf("{fmt}\\n", {val});')

    def _emit_write(self, node: ast.WriteStmt):
        """Emit WRITE as fprintf/printf with format string."""
        stream = "stderr" if node.unit == "0" else "stdout"
        fmt = node.fmt
        # Add newline unless ADVANCE=NO
        if node.advance:
            fmt = fmt + "\\n"
        if node.args:
            args = ", ".join(self._expr(a) for a in node.args)
            self._put(f'fprintf({stream}, "{fmt}", {args});')
        else:
            self._put(f'fprintf({stream}, "{fmt}");')

    def _emit_return(self, node: ast.ReturnStmt):
        if node.value is not None:
            val = node.value
            # RETURN funcname → return funcname_
            if (isinstance(val, ast.Variable)
                    and hasattr(self, '_func_ret_var')
                    and self._func_ret_var
                    and val.name == self._func_ret_var):
                self._put(f"return {val.name}_;")
            else:
                self._put(f"return {self._expr(val)};")
        else:
            self._put("return;")

    def _emit_allocate(self, node: ast.AllocateStmt):
        size = " * ".join(self._expr(d) for d in node.shape)
        c_type = self._c_type(self.var_types.get(node.name, "REAL"))
        self._put(f"{node.name} = ({c_type} *)malloc(({size}) * sizeof({c_type}));")

    # ── call argument handling ───────────────────────────────

    def _call_arg(self, arg) -> str:
        """For subroutine CALL, pass by value (MCL: no hidden pointers)."""
        return self._expr(arg)

    # ── lvalue (assignment target) ───────────────────────────

    def _lvalue(self, node) -> str:
        if isinstance(node, ast.Variable):
            # Function return variable: SQ2SCT := val
            if hasattr(self, '_func_ret_var') and self._func_ret_var and node.name == self._func_ret_var:
                return f"{node.name}_"
            return node.name
        if isinstance(node, ast.CallOrSubscript):
            # Array subscript on left side
            if node.name in self.array_shapes:
                indices = "][".join(f"({self._expr(a)}) - 1" for a in node.args)
                return f"{node.name}[{indices}]"
            return f"{node.name}({', '.join(self._expr(a) for a in node.args)})"
        return self._expr(node)

    # ── expressions ──────────────────────────────────────────

    def _expr(self, node) -> str:
        if isinstance(node, ast.Literal):
            if node.type == "REAL":
                s = repr(node.value)
                if "." not in s and "e" not in s.lower():
                    s += ".0"
                return s
            if node.type == "INTEGER":
                return str(node.value)
            if node.type == "STRING":
                return f'"{node.value}"'
            if node.type == "LOGICAL":
                return "1" if node.value else "0"

        if isinstance(node, ast.Variable):
            return node.name

        if isinstance(node, ast.BinaryOp):
            left = self._expr(node.left)
            right = self._expr(node.right)

            if node.op == "**":
                return f"pow({left}, {right})"
            if node.op == ".AND.":
                return f"({left} && {right})"
            if node.op == ".OR.":
                return f"({left} || {right})"
            if node.op in RELOP_MAP:
                return f"({left} {RELOP_MAP[node.op]} {right})"

            return f"({left} {node.op} {right})"

        if isinstance(node, ast.UnaryOp):
            operand = self._expr(node.operand)
            if node.op == ".NOT.":
                return f"(!{operand})"
            return f"({node.op}{operand})"

        if isinstance(node, ast.CallOrSubscript):
            upper = node.name.upper()

            # Array subscript (known array)
            if node.name in self.array_shapes:
                indices = "][".join(f"({self._expr(a)}) - 1" for a in node.args)
                return f"{node.name}[{indices}]"

            # Bitwise intrinsics → direct C operators
            if upper == "ISHFT":
                val = self._expr(node.args[0])
                shift_node = node.args[1]
                # Optimize: compile-time constant shift
                if isinstance(shift_node, ast.Literal) and shift_node.type == "INTEGER":
                    sv = shift_node.value
                    if sv >= 0:
                        return f"(({val}) << {sv})"
                    else:
                        return f"((unsigned)({val}) >> {-sv})"
                if isinstance(shift_node, ast.UnaryOp) and shift_node.op == "-" and isinstance(shift_node.operand, ast.Literal):
                    sv = shift_node.operand.value
                    return f"((unsigned)({val}) >> {sv})"
                shift = self._expr(shift_node)
                return f"(({shift}) >= 0 ? ({val}) << ({shift}) : (unsigned)({val}) >> -({shift}))"
            if upper == "IEOR":
                return f"({self._expr(node.args[0])} ^ {self._expr(node.args[1])})"
            if upper == "IAND":
                return f"({self._expr(node.args[0])} & {self._expr(node.args[1])})"
            if upper == "IOR":
                return f"({self._expr(node.args[0])} | {self._expr(node.args[1])})"
            if upper == "NOT":
                return f"(~{self._expr(node.args[0])})"
            if upper == "MOD":
                a0, a1 = self._expr(node.args[0]), self._expr(node.args[1])
                # Use fmod for real operands, % for integer
                if self._infer_int(node.args[0]) and self._infer_int(node.args[1]):
                    return f"({a0} % {a1})"
                return f"fmod({a0}, {a1})"
            if upper == "REAL":
                return f"(double)({self._expr(node.args[0])})"
            if upper == "INT":
                return f"(int)({self._expr(node.args[0])})"
            if upper == "CHAR":
                return f"(char)({self._expr(node.args[0])})"

            # Math intrinsics
            if upper in C_MATH:
                args = ", ".join(self._expr(a) for a in node.args)
                return f"{C_MATH[upper]}({args})"

            # ABS — type-aware
            if upper == "ABS":
                arg = self._expr(node.args[0])
                is_int = self._infer_int(node.args[0])
                return f"abs({arg})" if is_int else f"fabs({arg})"

            # MAX / MIN (variadic)
            if upper == "MAX" and len(node.args) == 2:
                a, b = self._expr(node.args[0]), self._expr(node.args[1])
                if self._infer_int(node.args[0]):
                    return f"(({a}) > ({b}) ? ({a}) : ({b}))"
                return f"fmax({a}, {b})"
            if upper == "MIN" and len(node.args) == 2:
                a, b = self._expr(node.args[0]), self._expr(node.args[1])
                if self._infer_int(node.args[0]):
                    return f"(({a}) < ({b}) ? ({a}) : ({b}))"
                return f"fmin({a}, {b})"

            # CLAMP — branchless: fmin(fmax(x, lo), hi)
            if upper == "CLAMP" and len(node.args) == 3:
                x = self._expr(node.args[0])
                lo = self._expr(node.args[1])
                hi = self._expr(node.args[2])
                if self._infer_int(node.args[0]):
                    return f"(({x}) < ({lo}) ? ({lo}) : (({x}) > ({hi}) ? ({hi}) : ({x})))"
                return f"fmin(fmax({x}, {lo}), {hi})"

            # Generic function call
            args = ", ".join(self._expr(a) for a in node.args)
            return f"{node.name}({args})"

        return f"/* unknown: {type(node).__name__} */"

    def _infer_int(self, node) -> bool:
        """Rough check: is this expression integer-typed?"""
        if isinstance(node, ast.Literal):
            return node.type == "INTEGER"
        if isinstance(node, ast.Variable):
            return self.var_types.get(node.name) == "INTEGER"
        if isinstance(node, ast.BinaryOp):
            # Integer if both operands are integer (for +, -, *, /, %)
            return self._infer_int(node.left) and self._infer_int(node.right)
        if isinstance(node, ast.UnaryOp):
            return self._infer_int(node.operand)
        if isinstance(node, ast.CallOrSubscript):
            upper = node.name.upper()
            if upper == "MOD":
                return self._infer_int(node.args[0]) and self._infer_int(node.args[1])
            if upper in ("INT", "IAND", "IOR", "IEOR", "ISHFT", "NOT", "ABS"):
                return self._infer_int(node.args[0])
            if node.name in self.array_shapes:
                return self.var_types.get(node.name) == "INTEGER"
        return False

    def _format_for(self, node) -> str:
        if isinstance(node, ast.Literal):
            return {
                "INTEGER": "%d", "REAL": "%f", "STRING": "%s", "LOGICAL": "%d"
            }.get(node.type, "%f")
        if isinstance(node, ast.Variable):
            vtype = self.var_types.get(node.name, "REAL")
            return {"INTEGER": "%d", "REAL": "%f", "LOGICAL": "%d"}.get(vtype, "%f")
        return "%f"
