"""AST to IR lowering.

Walks the checked AST and produces an IRModule. Expressions are lowered to
sequences of IR instructions in SSA-like form — each subexpression gets a
temporary. Control flow remains structured (IRIf, IRLoop, IRSelect).
"""

from __future__ import annotations

from typing import Any

from . import ast_nodes as ast
from .errors import MCLError
from .ir import (
    IRModule, IRFunc, IRVar, IRBlock, IRIf, IRLoop, IRSelect,
    IRInst, IRConst, IRRef, IRType, StorageClass, Op, Operand,
)


# Map Ergo type names to IR types
TYPE_MAP = {
    "REAL": IRType.REAL,
    "INTEGER": IRType.INTEGER,
    "INTEGER*8": IRType.INT64,   # 64-bit integer (Inc-2A, CPU only)
    "LOGICAL": IRType.LOGICAL,
    "CHARACTER": IRType.CHARACTER,
    # STRING appears on string literals (e.g. PRINT "hello") — typing them
    # REAL emitted them as bare identifiers with a %f format.
    "STRING": IRType.STRING,
    # COMPLEX deliberately absent: see _ir_type — fail loudly, never
    # silently lower it to REAL again.
}

# Map binary operator strings to IR ops
BINOP_MAP = {
    "+": Op.ADD, "-": Op.SUB, "*": Op.MUL, "/": Op.DIV, "**": Op.POW,
    "<": Op.LT, ">": Op.GT, "=": Op.EQ, "≠": Op.NE, "≤": Op.LE, "≥": Op.GE,
    ".AND.": Op.AND, ".OR.": Op.OR,
}

# Intrinsic name -> (Op, result_type_override_or_None)
INTRINSIC_MAP = {
    "SIN": (Op.SIN, IRType.REAL), "COS": (Op.COS, IRType.REAL),
    "TAN": (Op.TAN, IRType.REAL), "ASIN": (Op.ASIN, IRType.REAL),
    "ACOS": (Op.ACOS, IRType.REAL), "ATAN": (Op.ATAN, IRType.REAL),
    "ATAN2": (Op.ATAN2, IRType.REAL), "EXP": (Op.EXP, IRType.REAL),
    "LOG": (Op.LOG, IRType.REAL), "LOG10": (Op.LOG10, IRType.REAL),
    "SQRT": (Op.SQRT, IRType.REAL), "SINH": (Op.SINH, IRType.REAL),
    "COSH": (Op.COSH, IRType.REAL), "TANH": (Op.TANH, IRType.REAL),
    "MAX": (Op.MAX, None), "MIN": (Op.MIN, None),
    "CLAMP": (Op.CLAMP, None),
    "ABS": (Op.ABS, None),
    "MOD": (Op.MOD, None),
    "SIGN": (Op.SIGN, None),
    "HASH": (Op.HASH, IRType.INTEGER), "RAND": (Op.RAND, IRType.REAL),
    "ESF_NEXT": (Op.ESF_NEXT, IRType.INTEGER),
}


class IRBuilder:
    def __init__(self):
        self._temp_counter = 0
        self._block_counter = 0
        # Variable type tracking (name -> IRType)
        self._var_types: dict[str, IRType] = {}
        # Array shapes (name -> tuple of dims)
        self._array_shapes: dict[str, tuple] = {}
        # PARAMETER constants (name -> folded value), for constant folding
        # of declaration initializers and array shapes
        self._param_values: dict[str, Any] = {}
        # Function return types
        self._func_return_types: dict[str, IRType] = {}
        # Current function name (for Fortran-style return variable)
        self._in_function: str | None = None
        # Current module and locals list, used for HHB capture variables
        self._current_module: IRModule | None = None
        self._current_locals: list[IRVar] | None = None

    def _fresh_temp(self, prefix: str = "t") -> str:
        self._temp_counter += 1
        return f"_{prefix}_{self._temp_counter}"

    def _fresh_block(self, prefix: str = "bb") -> str:
        self._block_counter += 1
        return f"{prefix}_{self._block_counter}"

    def _ir_type(self, type_name: str) -> IRType:
        if type_name == "COMPLEX":
            # Used to lower to REAL via TYPE_MAP, producing wrong numerics
            # with no warning. Refuse until COMPLEX is really implemented.
            raise MCLError(
                "COMPLEX is not supported by the IR backend yet "
                "(previously it was silently treated as REAL)."
            )
        return TYPE_MAP.get(type_name, IRType.REAL)

    def _type_of(self, name: str) -> IRType:
        return self._var_types.get(name, IRType.REAL)

    # ── top level ────────────────────────────────────────────

    def build(self, tree: ast.Program, source_file: str = None) -> IRModule:
        mod = IRModule(source_file=source_file)
        self._current_module = mod
        self._current_locals = mod.main_locals

        # Promote VERIFY HANDSHAKE <directive> + following statement into a
        # HandshakeStmt AST node so that _lower_handshake emits entry capture
        # and boundary checks.  This keeps the directive surface syntax while
        # reusing the Phase-3b lowering path.
        tree.units = self._promote_verify_handshakes(tree.units)

        # First pass: register functions and collect global state
        for unit in tree.units:
            if isinstance(unit, ast.FunctionDef):
                ret = self._ir_type(unit.return_type or "REAL")
                self._func_return_types[unit.name] = ret
            elif isinstance(unit, ast.SubroutineDef):
                self._func_return_types[unit.name] = IRType.VOID

        # Classify top-level units
        for unit in tree.units:
            if isinstance(unit, ast.Declaration) and (unit.static or unit.parameter):
                self._lower_global_decl(unit, mod)
            elif isinstance(unit, ast.DataStmt):
                mod.data_inits[unit.name] = unit.values
            elif isinstance(unit, ast.FunctionDef):
                mod.functions.append(self._lower_function(unit))
            elif isinstance(unit, ast.SubroutineDef):
                mod.functions.append(self._lower_subroutine(unit))
            elif isinstance(unit, ast.ImplicitNone):
                pass
            else:
                # Main body statement — could be a declaration or executable
                if isinstance(unit, ast.Declaration):
                    self._lower_local_decl(unit, mod.main_locals)
                    items = []
                else:
                    items = self._lower_stmt(unit)
                    mod.main_body.extend(items)

        return mod

    # ── VERIFY HANDSHAKE promotion ───────────────────────────

    def _promote_verify_handshakes(self, stmts: list) -> list:
        """Rewrite VERIFY HANDSHAKE directives into explicit HandshakeStmt nodes.

        A directive followed by a statement becomes a HandshakeStmt whose body
        is that single statement.  The directive is left untouched if it has no
        following statement (the linter will report this).  Nested statement
        lists inside IF/DO/WHILE/SELECT/HANDSHAKE/functions/subroutines are
        also transformed so VERIFY HANDSHAKE can be used inside any scope.
        """
        result = []
        i = 0
        while i < len(stmts):
            stmt = stmts[i]
            if isinstance(stmt, ast.VerifyHandshakeStmt):
                if i + 1 < len(stmts):
                    target = self._promote_stmt(stmts[i + 1])
                    result.append(ast.HandshakeStmt(
                        name=stmt.name,
                        options=stmt.options,
                        body=[target],
                        line=stmt.line,
                    ))
                    i += 2
                else:
                    result.append(stmt)
                    i += 1
            else:
                result.append(self._promote_stmt(stmt))
                i += 1
        return result

    def _promote_stmt(self, stmt: Any) -> Any:
        """Recursively promote VERIFY HANDSHAKE inside compound statements."""
        if isinstance(stmt, ast.IfStmt):
            stmt.then_body = self._promote_verify_handshakes(stmt.then_body)
            if stmt.else_body:
                stmt.else_body = self._promote_verify_handshakes(stmt.else_body)
        elif isinstance(stmt, ast.DoLoop):
            stmt.body = self._promote_verify_handshakes(stmt.body)
        elif isinstance(stmt, ast.DoWhileStmt):
            stmt.body = self._promote_verify_handshakes(stmt.body)
        elif isinstance(stmt, ast.SelectCaseStmt):
            stmt.cases = [
                (val, self._promote_verify_handshakes(body))
                for val, body in stmt.cases
            ]
        elif isinstance(stmt, ast.HandshakeStmt):
            stmt.body = self._promote_verify_handshakes(stmt.body)
        elif isinstance(stmt, (ast.FunctionDef, ast.SubroutineDef)):
            stmt.body = self._promote_verify_handshakes(stmt.body)
        return stmt

    # ── globals ──────────────────────────────────────────────

    def _lower_global_decl(self, decl: ast.Declaration, mod: IRModule):
        storage = StorageClass.PARAMETER if decl.parameter else StorageClass.STATIC
        ir_type = self._ir_type(decl.type_name)
        for v in decl.variables:
            shape = self._lower_shape(v.shape) if v.shape else None
            init = self._const_value(v.init_value) if v.init_value else None
            irv = IRVar(
                name=v.name, type=ir_type, storage=storage,
                shape=shape, init_value=init, line=decl.line,
            )
            mod.globals.append(irv)
            self._var_types[v.name] = ir_type
            if decl.parameter and init is not None:
                self._param_values[v.name] = init
            if shape:
                self._array_shapes[v.name] = shape

    def _lower_local_decl(self, decl: ast.Declaration, locals_list: list[IRVar]):
        ir_type = self._ir_type(decl.type_name)
        storage = StorageClass.ALLOCATABLE if decl.allocatable else StorageClass.LOCAL
        if decl.parameter:
            storage = StorageClass.PARAMETER
        for v in decl.variables:
            shape = self._lower_shape(v.shape) if v.shape else None
            init = self._const_value(v.init_value) if v.init_value else None
            irv = IRVar(
                name=v.name, type=ir_type, storage=storage,
                shape=shape, init_value=init, line=decl.line,
            )
            locals_list.append(irv)
            self._var_types[v.name] = ir_type
            if decl.parameter and init is not None:
                self._param_values[v.name] = init
            if shape:
                self._array_shapes[v.name] = shape

    def _lower_shape(self, shape: tuple) -> tuple:
        """Lower AST shape dims to plain ints or variable name strings.

        Non-literal dims are constant-folded (PARAMETER names resolve via
        _param_values). A bare non-constant name is kept as a string for
        dummy-argument shapes in functions; any other dim that does not
        fold to an integer is rejected — emitting the AST repr into a C
        declarator is never right.
        """
        result = []
        for d in shape:
            if isinstance(d, ast.Literal):
                result.append(d.value)
            elif isinstance(d, ast.Variable):
                if d.name in self._param_values:
                    v = self._param_values[d.name]
                    if not isinstance(v, int) or isinstance(v, bool):
                        raise MCLError(
                            "array shape must be a compile-time constant "
                            "(use ALLOCATABLE for runtime-sized arrays)")
                    result.append(v)
                else:
                    result.append(d.name)
            elif isinstance(d, int):
                result.append(d)
            elif isinstance(d, str):
                result.append(d)
            else:
                v = self._const_value(d)
                if not isinstance(v, int) or isinstance(v, bool):
                    raise MCLError(
                        "array shape must be a compile-time constant "
                        "(use ALLOCATABLE for runtime-sized arrays)")
                result.append(v)
        return tuple(result)

    # ── functions / subroutines ──────────────────────────────

    def _lower_function(self, fn: ast.FunctionDef) -> IRFunc:
        saved_types = dict(self._var_types)
        saved_shapes = dict(self._array_shapes)
        saved_params = dict(self._param_values)
        saved_func = self._in_function
        self._in_function = fn.name

        ret_type = self._ir_type(fn.return_type or "REAL")

        # Collect param types from declarations
        param_types = {}
        param_shapes = {}
        for decl in fn.declarations:
            for v in decl.variables:
                if decl.parameter:
                    # Register before any shapes are lowered — a PARAMETER
                    # may appear in a later declaration's array shape.
                    init = self._const_value(v.init_value) if v.init_value else None
                    if init is not None:
                        self._param_values[v.name] = init
                param_types[v.name] = self._ir_type(decl.type_name)
                if v.shape:
                    param_shapes[v.name] = self._lower_shape(v.shape)

        # Build param IRVars
        params = []
        for p in fn.params:
            pt = param_types.get(p, IRType.REAL)
            ps = param_shapes.get(p)
            params.append(IRVar(name=p, type=pt, shape=ps))
            self._var_types[p] = pt
            if ps:
                self._array_shapes[p] = ps

        # Return variable (Fortran idiom)
        self._var_types[fn.name] = ret_type

        # Local declarations (skip params)
        locals_ = []
        param_set = set(fn.params)
        for decl in fn.declarations:
            for v in decl.variables:
                if v.name not in param_set:
                    self._lower_local_decl_single(
                        v, decl.type_name, decl.allocatable, decl.parameter, locals_)

        # Add the return variable as a local
        locals_.append(IRVar(name=f"{fn.name}_", type=ret_type))
        self._var_types[f"{fn.name}_"] = ret_type

        # Lower body
        saved_locals = self._current_locals
        self._current_locals = locals_
        body = []
        for stmt in fn.body:
            if isinstance(stmt, ast.DataStmt):
                # Function-local DATA: attach values to the local IRVar so
                # codegen can emit an initializer.
                for v in locals_:
                    if v.name == stmt.name:
                        v.data_init = stmt.values
                        break
                continue
            body.extend(self._lower_stmt(stmt))
        self._current_locals = saved_locals

        self._in_function = saved_func
        self._var_types = saved_types
        self._array_shapes = saved_shapes
        self._param_values = saved_params

        return IRFunc(
            name=fn.name, params=params, locals=locals_, body=body,
            return_type=ret_type, is_subroutine=False,
        )

    def _lower_subroutine(self, fn: ast.SubroutineDef) -> IRFunc:
        saved_types = dict(self._var_types)
        saved_shapes = dict(self._array_shapes)
        saved_params = dict(self._param_values)
        saved_func = self._in_function
        self._in_function = None

        param_types = {}
        param_shapes = {}
        for decl in fn.declarations:
            for v in decl.variables:
                if decl.parameter:
                    # Register before any shapes are lowered — a PARAMETER
                    # may appear in a later declaration's array shape.
                    init = self._const_value(v.init_value) if v.init_value else None
                    if init is not None:
                        self._param_values[v.name] = init
                param_types[v.name] = self._ir_type(decl.type_name)
                if v.shape:
                    param_shapes[v.name] = self._lower_shape(v.shape)

        params = []
        for p in fn.params:
            pt = param_types.get(p, IRType.INTEGER)
            ps = param_shapes.get(p)
            params.append(IRVar(name=p, type=pt, shape=ps))
            self._var_types[p] = pt
            if ps:
                self._array_shapes[p] = ps

        locals_ = []
        param_set = set(fn.params)
        for decl in fn.declarations:
            for v in decl.variables:
                if v.name not in param_set:
                    self._lower_local_decl_single(
                        v, decl.type_name, decl.allocatable, decl.parameter, locals_)

        saved_locals = self._current_locals
        self._current_locals = locals_
        body = []
        for stmt in fn.body:
            if isinstance(stmt, ast.DataStmt):
                # Function-local DATA: attach values to the local IRVar so
                # codegen can emit an initializer.
                for v in locals_:
                    if v.name == stmt.name:
                        v.data_init = stmt.values
                        break
                continue
            body.extend(self._lower_stmt(stmt))
        self._current_locals = saved_locals

        self._in_function = saved_func
        self._var_types = saved_types
        self._array_shapes = saved_shapes
        self._param_values = saved_params

        return IRFunc(
            name=fn.name, params=params, locals=locals_, body=body,
            return_type=IRType.VOID, is_subroutine=True,
        )

    def _lower_local_decl_single(self, v: ast.VarDecl, type_name: str,
                                  allocatable: bool, parameter: bool,
                                  locals_: list[IRVar]):
        ir_type = self._ir_type(type_name)
        storage = StorageClass.ALLOCATABLE if allocatable else StorageClass.LOCAL
        if parameter:
            storage = StorageClass.PARAMETER
        shape = self._lower_shape(v.shape) if v.shape else None
        init = self._const_value(v.init_value) if v.init_value else None
        locals_.append(IRVar(
            name=v.name, type=ir_type, storage=storage,
            shape=shape, init_value=init,
        ))
        self._var_types[v.name] = ir_type
        if parameter and init is not None:
            self._param_values[v.name] = init
        if shape:
            self._array_shapes[v.name] = shape

    # ── assignment ───────────────────────────────────────────

    def _lower_assign(self, node: ast.AssignStmt) -> list:
        block = IRBlock(self._fresh_block("assign"), line=node.line)

        # Lower the value expression
        val_op = self._lower_expr(node.value, block)

        # Lower the target
        if isinstance(node.target, ast.Variable):
            target_name = node.target.name
            # Fortran return variable idiom
            if self._in_function and target_name == self._in_function:
                target_name = f"{target_name}_"
            block.insts.append(IRInst(
                op=Op.COPY, result=target_name, args=[val_op],
                type=self._type_of(target_name), line=node.line,
            ))
        elif isinstance(node.target, ast.CallOrSubscript):
            if node.target.name in self._array_shapes:
                # Array store: A(i, j) := val  ->  store A, [i-1, j-1], val
                indices = []
                for arg in node.target.args:
                    idx = self._lower_expr(arg, block)
                    # 1-based to 0-based
                    one = IRConst(IRType.INTEGER, 1)
                    t = self._fresh_temp("idx")
                    block.insts.append(IRInst(
                        op=Op.SUB, result=t, args=[idx, one],
                        type=IRType.INTEGER, line=node.line,
                    ))
                    indices.append(IRRef(t, IRType.INTEGER))
                block.insts.append(IRInst(
                    op=Op.STORE, args=[val_op] + indices,
                    type=IRType.VOID, line=node.line,
                    meta={"array": node.target.name},
                ))
            else:
                # Not a declared array — the store has nowhere to go.
                # Must not silently drop it.
                raise MCLError("invalid assignment target", node.line)
        else:
            # Literal / expression targets (e.g. `5 := x`) — reject loudly
            # instead of dropping the store.
            raise MCLError("invalid assignment target", node.line)
        return [block]

    # ── expressions ──────────────────────────────────────────

    def _lower_expr(self, node, block: IRBlock) -> Operand:
        """Lower an AST expression to IR instructions in the given block.
        Returns the operand holding the result."""

        if isinstance(node, ast.Literal):
            return IRConst(self._ir_type(node.type), node.value)

        if isinstance(node, ast.Variable):
            name = node.name
            if self._in_function and name == self._in_function:
                name = f"{name}_"
            return IRRef(name, self._type_of(name))

        if isinstance(node, ast.BinaryOp):
            return self._lower_binop(node, block)

        if isinstance(node, ast.UnaryOp):
            return self._lower_unop(node, block)

        if isinstance(node, ast.CallOrSubscript):
            return self._lower_call_or_subscript(node, block)

        # Fallback
        return IRConst(IRType.INTEGER, 0)

    def _lower_binop(self, node: ast.BinaryOp, block: IRBlock) -> Operand:
        left = self._lower_expr(node.left, block)
        right = self._lower_expr(node.right, block)

        op = BINOP_MAP.get(node.op)
        if op is None:
            # Unknown op — shouldn't happen
            return left

        # Determine result type
        if op in (Op.LT, Op.GT, Op.EQ, Op.NE, Op.LE, Op.GE, Op.AND, Op.OR):
            result_type = IRType.LOGICAL
        else:
            result_type = self._promote(self._operand_type(left),
                                        self._operand_type(right))

        t = self._fresh_temp()
        block.insts.append(IRInst(
            op=op, result=t, args=[left, right], type=result_type,
        ))
        return IRRef(t, result_type)

    def _lower_unop(self, node: ast.UnaryOp, block: IRBlock) -> Operand:
        operand = self._lower_expr(node.operand, block)

        if node.op == "-":
            t = self._fresh_temp()
            ot = self._operand_type(operand)
            block.insts.append(IRInst(
                op=Op.NEG, result=t, args=[operand], type=ot,
            ))
            return IRRef(t, ot)

        if node.op == "+":
            return operand  # unary plus is a no-op

        if node.op == ".NOT.":
            t = self._fresh_temp()
            block.insts.append(IRInst(
                op=Op.NOT, result=t, args=[operand], type=IRType.LOGICAL,
            ))
            return IRRef(t, IRType.LOGICAL)

        return operand

    def _lower_call_or_subscript(self, node: ast.CallOrSubscript,
                                  block: IRBlock) -> Operand:
        upper = node.name.upper()

        # Array subscript
        if node.name in self._array_shapes:
            indices = []
            for arg in node.args:
                idx = self._lower_expr(arg, block)
                one = IRConst(IRType.INTEGER, 1)
                t = self._fresh_temp("idx")
                block.insts.append(IRInst(
                    op=Op.SUB, result=t, args=[idx, one],
                    type=IRType.INTEGER,
                ))
                indices.append(IRRef(t, IRType.INTEGER))
            elem_type = self._type_of(node.name)
            t = self._fresh_temp("ld")
            block.insts.append(IRInst(
                op=Op.LOAD, result=t, args=indices,
                type=elem_type,
                meta={"array": node.name},
            ))
            return IRRef(t, elem_type)

        # Bitwise intrinsics
        if upper == "ISHFT":
            a = self._lower_expr(node.args[0], block)
            b = self._lower_expr(node.args[1], block)
            t = self._fresh_temp()
            block.insts.append(IRInst(
                op=Op.ISHFT, result=t, args=[a, b], type=IRType.INTEGER,
            ))
            return IRRef(t, IRType.INTEGER)

        if upper in ("IEOR", "IAND", "IOR"):
            op_map = {"IEOR": Op.IEOR, "IAND": Op.IAND, "IOR": Op.IOR}
            a = self._lower_expr(node.args[0], block)
            b = self._lower_expr(node.args[1], block)
            t = self._fresh_temp()
            block.insts.append(IRInst(
                op=op_map[upper], result=t, args=[a, b], type=IRType.INTEGER,
            ))
            return IRRef(t, IRType.INTEGER)

        if upper == "NOT":
            a = self._lower_expr(node.args[0], block)
            t = self._fresh_temp()
            block.insts.append(IRInst(
                op=Op.BITNOT, result=t, args=[a], type=IRType.INTEGER,
            ))
            return IRRef(t, IRType.INTEGER)

        # Warp ring shuffle intrinsics
        if upper in ("RING_PREV", "RING_NEXT"):
            a = self._lower_expr(node.args[0], block)
            ret_type = self._operand_type(a)
            t = self._fresh_temp()
            block.insts.append(IRInst(
                op=Op.RING_PREV if upper == "RING_PREV" else Op.RING_NEXT,
                result=t, args=[a], type=ret_type,
            ))
            return IRRef(t, ret_type)

        if upper == "RING_SHIFT":
            a = self._lower_expr(node.args[0], block)
            delta = self._lower_expr(node.args[1], block)
            ret_type = self._operand_type(a)
            t = self._fresh_temp()
            block.insts.append(IRInst(
                op=Op.RING_SHIFT, result=t, args=[a, delta], type=ret_type,
            ))
            return IRRef(t, ret_type)

        if upper == "RING_BROADCAST":
            a = self._lower_expr(node.args[0], block)
            lane = self._lower_expr(node.args[1], block)
            ret_type = self._operand_type(a)
            t = self._fresh_temp()
            block.insts.append(IRInst(
                op=Op.RING_BROADCAST, result=t, args=[a, lane], type=ret_type,
            ))
            return IRRef(t, ret_type)

        # Type conversions
        if upper == "REAL":
            a = self._lower_expr(node.args[0], block)
            t = self._fresh_temp()
            block.insts.append(IRInst(
                op=Op.TO_REAL, result=t, args=[a], type=IRType.REAL,
            ))
            return IRRef(t, IRType.REAL)

        if upper == "INT":
            a = self._lower_expr(node.args[0], block)
            t = self._fresh_temp()
            block.insts.append(IRInst(
                op=Op.TO_INT, result=t, args=[a], type=IRType.INTEGER,
            ))
            return IRRef(t, IRType.INTEGER)

        if upper == "INT8":
            a = self._lower_expr(node.args[0], block)
            t = self._fresh_temp()
            block.insts.append(IRInst(
                op=Op.TO_INT64, result=t, args=[a], type=IRType.INT64,
            ))
            return IRRef(t, IRType.INT64)

        if upper == "CHAR":
            a = self._lower_expr(node.args[0], block)
            t = self._fresh_temp()
            block.insts.append(IRInst(
                op=Op.TO_CHAR, result=t, args=[a], type=IRType.CHARACTER,
            ))
            return IRRef(t, IRType.CHARACTER)

        # Whole-array reductions: DOT_PRODUCT(A, B) → REAL, NORM2(A) → REAL.
        # Shape rules (1D REAL arrays, compile-time-known matching shapes)
        # are enforced by the checker; the array names ride in meta so
        # codegen can bind the compile-time element count.
        if upper in ("DOT_PRODUCT", "NORM2"):
            names = [a.name if isinstance(a, ast.Variable) else "?"
                     for a in node.args]
            t = self._fresh_temp()
            block.insts.append(IRInst(
                op=Op.DOT_PRODUCT if upper == "DOT_PRODUCT" else Op.NORM2,
                result=t, args=[], type=IRType.REAL,
                line=getattr(node, "line", 0),
                meta={"arrays": names},
            ))
            return IRRef(t, IRType.REAL)

        # Math / general intrinsics
        if upper in INTRINSIC_MAP:
            ir_op, ret_override = INTRINSIC_MAP[upper]
            lowered_args = [self._lower_expr(a, block) for a in node.args]
            if ret_override:
                ret_type = ret_override
            else:
                # Infer from first argument
                ret_type = self._operand_type(lowered_args[0]) if lowered_args else IRType.REAL
            t = self._fresh_temp()
            block.insts.append(IRInst(
                op=ir_op, result=t, args=lowered_args, type=ret_type,
            ))
            return IRRef(t, ret_type)

        # User function call
        lowered_args = [self._lower_expr(a, block) for a in node.args]
        ret_type = self._func_return_types.get(node.name, IRType.REAL)
        t = self._fresh_temp("call")
        block.insts.append(IRInst(
            op=Op.CALL, result=t, args=lowered_args, type=ret_type,
            meta={"func": node.name},
        ))
        return IRRef(t, ret_type)

    # ── control flow ─────────────────────────────────────────

    def _lower_if(self, node: ast.IfStmt) -> IRIf:
        # Lower condition into a block, get the condition operand
        cond_block = IRBlock(self._fresh_block("if_cond"), line=node.line)
        cond_op = self._lower_expr(node.condition, cond_block)

        # Lower then body
        then_items = []
        if cond_block.insts:
            then_items_prefix = [cond_block]
        else:
            then_items_prefix = []

        then_body = []
        for s in node.then_body:
            then_body.extend(self._lower_stmt(s))

        # Lower else body
        else_body = None
        if node.else_body:
            else_body = []
            for s in node.else_body:
                else_body.extend(self._lower_stmt(s))

        # The condition block instructions need to execute before the branch.
        # We prepend them to the parent scope and use cond_op for the branch.
        # But since IRIf takes a single operand, we need the cond block to
        # be evaluated first. Put it before the IRIf.
        result_items = then_items_prefix
        result_items.append(IRIf(
            condition=cond_op, then_body=then_body,
            else_body=else_body, line=node.line,
        ))
        # We return a single IRIf. If there's a cond_block, we need to
        # wrap both in the parent. Return as list handled by caller.
        # Actually, _lower_stmt returns a list, so this is fine —
        # but _lower_if returns a single item. Let me fix the protocol.
        # We'll return the list from here and adjust _lower_stmt.

        # Actually the cleanest thing: attach the cond block to the IRIf meta
        # and let the C backend emit it. Or just always use an IRBlock + IRIf pair.
        # Let's go with returning the cond_block separate and the IRIf.
        # The caller (_lower_stmt) already extends a list, so we're fine.
        if cond_block.insts:
            return [cond_block, IRIf(
                condition=cond_op, then_body=then_body,
                else_body=else_body, line=node.line,
            )]
        return [IRIf(
            condition=cond_op, then_body=then_body,
            else_body=else_body, line=node.line,
        )]

    def _lower_loop(self, node: ast.DoLoop) -> IRLoop:
        # Lower bounds
        start_block = IRBlock(self._fresh_block("loop_bounds"))
        start_op = self._lower_expr(node.start, start_block)
        end_op = self._lower_expr(node.end, start_block)
        step_op = self._lower_expr(node.step, start_block)

        # Register loop var
        self._var_types[node.var] = IRType.INTEGER

        # Lower body
        body_items = []
        for s in node.body:
            body_items.extend(self._lower_stmt(s))

        loop = IRLoop(
            var=node.var, start=start_op, end=end_op, step=step_op,
            body=body_items, line=node.line,
        )

        if start_block.insts:
            return [start_block, loop]
        return [loop]

    def _lower_while(self, node: ast.DoWhileStmt) -> list:
        from .ir import IRWhileLoop
        cond_block = IRBlock(self._fresh_block("while_cond"), line=node.line)
        cond_op = self._lower_expr(node.condition, cond_block)

        body_items = []
        for s in node.body:
            body_items.extend(self._lower_stmt(s))

        return [IRWhileLoop(
            condition=cond_op, cond_block=cond_block,
            body=body_items, line=node.line,
        )]

    def _lower_select(self, node: ast.SelectCaseStmt) -> list:
        expr_block = IRBlock(self._fresh_block("select_expr"), line=node.line)
        expr_op = self._lower_expr(node.expr, expr_block)

        cases = []
        for case_val, case_body in node.cases:
            if case_val is not None:
                val_op = self._lower_expr(case_val, expr_block)
            else:
                val_op = None
            body_items = []
            for s in case_body:
                body_items.extend(self._lower_stmt(s))
            cases.append((val_op, body_items))

        sel = IRSelect(expr=expr_op, cases=cases, line=node.line)
        if expr_block.insts:
            return [expr_block, sel]
        return [sel]

    # ── statements (continued) ───────────────────────────────

    def _lower_print(self, node: ast.PrintStmt) -> list:
        block = IRBlock(self._fresh_block("print"), line=node.line)
        val = self._lower_expr(node.value, block)
        block.insts.append(IRInst(
            op=Op.PRINT, args=[val], type=IRType.VOID, line=node.line,
        ))
        return [block]

    def _lower_write(self, node: ast.WriteStmt) -> list:
        block = IRBlock(self._fresh_block("write"), line=node.line)
        # Unit: preconnected string ("*", "0") or a lowered INTEGER expr
        if isinstance(node.unit, str):
            unit = node.unit
        else:
            unit = self._lower_expr(node.unit, block)
        # Raw-record form: WRITE(unit) A(lo:hi), ... — sections carry
        # the array name plus lowered bounds (Spec Part 10.4).
        if node.fmt is None:
            sections = []
            for sec in node.args:
                lo = self._lower_expr(sec.lo, block)
                hi = self._lower_expr(sec.hi, block)
                sections.append((sec.name, lo, hi))
            block.insts.append(IRInst(
                op=Op.WRITE, args=[], type=IRType.VOID,
                line=node.line,
                meta={"unit": unit, "fmt": None, "sections": sections},
            ))
            return [block]
        lowered_args = [self._lower_expr(a, block) for a in node.args]
        block.insts.append(IRInst(
            op=Op.WRITE, args=lowered_args, type=IRType.VOID,
            line=node.line,
            meta={
                "unit": unit,
                "fmt": node.fmt,
                "advance": node.advance,
            },
        ))
        return [block]

    def _lower_return(self, node: ast.ReturnStmt) -> list:
        block = IRBlock(self._fresh_block("return"), line=node.line)
        if node.value is not None:
            val = self._lower_expr(node.value, block)
            block.insts.append(IRInst(
                op=Op.RETURN, args=[val], type=IRType.VOID, line=node.line,
            ))
        else:
            block.insts.append(IRInst(
                op=Op.RETURN_VOID, type=IRType.VOID, line=node.line,
            ))
        return [block]

    def _lower_call_stmt(self, node: ast.CallStmt) -> list:
        block = IRBlock(self._fresh_block("call"), line=node.line)

        # ZERO intrinsic: CALL ZERO(array) → memset(array, 0, sizeof)
        if node.name.upper() == "ZERO" and len(node.args) == 1:
            arg = node.args[0]
            if isinstance(arg, ast.Variable) and arg.name in self._array_shapes:
                block.insts.append(IRInst(
                    op=Op.ZERO, result=None, args=[],
                    type=IRType.VOID, line=node.line,
                    meta={"array": arg.name},
                ))
                return [block]

        # Streaming intrinsics (Inc-2B N=19): direct host↔device slice
        # transfers with NO host-side array copy (the Inc-4 ranged path
        # only covers compiler-tracked dirty arrays; streaming needs
        # explicit sub-range moves from an arbitrary host array).
        #   CALL VK_STAGE(gpu_arr, host_arr, src0, dst0, len)
        #     device[dst0..dst0+len) := host[src0..src0+len)  (1-based)
        #   CALL VK_FETCH(host_arr, gpu_arr, src0, dst0, len)
        #     host[dst0..dst0+len) := device[src0..src0+len)
        uname = node.name.upper()
        if uname in ("VK_STAGE", "VK_FETCH") and len(node.args) == 5:
            a_arr, b_arr = node.args[0], node.args[1]
            if (isinstance(a_arr, ast.Variable) and
                    isinstance(b_arr, ast.Variable) and
                    a_arr.name in self._array_shapes and
                    b_arr.name in self._array_shapes):
                ops = [self._lower_expr(a, block) for a in node.args[2:]]
                block.insts.append(IRInst(
                    op=Op.CALL_VOID, args=ops, type=IRType.VOID,
                    line=node.line,
                    meta={"func": uname, "arr_a": a_arr.name,
                          "arr_b": b_arr.name},
                ))
                return [block]
            from .errors import MCLError
            raise MCLError(
                f"{uname}: first two arguments must be declared arrays")

        # .esf stream intrinsics (Spec/Ergo_Stream_Format.md):
        #   CALL ESF_OPEN(unit, "path", nch)
        #   CALL ESF_WRITE(unit, ch, array, n)   ! n = element count
        #   CALL ESF_CLOSE(unit)
        if uname == "ESF_OPEN" and len(node.args) == 3 and \
                isinstance(node.args[1], ast.Literal) and \
                node.args[1].type == "STRING":
            ops = [self._lower_expr(node.args[0], block),
                   self._lower_expr(node.args[2], block)]
            block.insts.append(IRInst(
                op=Op.CALL_VOID, args=ops, type=IRType.VOID,
                line=node.line,
                meta={"func": "ESF_OPEN", "path": node.args[1].value},
            ))
            return [block]
        if uname == "ESF_WRITE" and len(node.args) == 4 and \
                isinstance(node.args[2], ast.Variable) and \
                node.args[2].name in self._array_shapes:
            ops = [self._lower_expr(node.args[0], block),
                   self._lower_expr(node.args[1], block),
                   self._lower_expr(node.args[3], block)]
            block.insts.append(IRInst(
                op=Op.CALL_VOID, args=ops, type=IRType.VOID,
                line=node.line,
                meta={"func": "ESF_WRITE",
                      "array": node.args[2].name},
            ))
            return [block]
        if uname == "ESF_CLOSE" and len(node.args) == 1:
            ops = [self._lower_expr(node.args[0], block)]
            block.insts.append(IRInst(
                op=Op.CALL_VOID, args=ops, type=IRType.VOID,
                line=node.line, meta={"func": "ESF_CLOSE"},
            ))
            return [block]
        if uname in ("ESF_OPEN", "ESF_WRITE", "ESF_CLOSE"):
            from .errors import MCLError
            raise MCLError(
                f"{uname}: bad arguments — expected "
                + {"ESF_OPEN": 'ESF_OPEN(unit, "path", nch)',
                   "ESF_WRITE": "ESF_WRITE(unit, ch, array, n) "
                                "(array a declared 1-D array)",
                   "ESF_CLOSE": "ESF_CLOSE(unit)"}[uname])

        lowered_args = [self._lower_expr(a, block) for a in node.args]
        block.insts.append(IRInst(
            op=Op.CALL_VOID, args=lowered_args, type=IRType.VOID,
            line=node.line, meta={"func": node.name},
        ))
        return [block]

    def _lower_allocate(self, node: ast.AllocateStmt) -> list:
        block = IRBlock(self._fresh_block("alloc"), line=node.line)
        dims = [self._lower_expr(d, block) for d in node.shape]
        block.insts.append(IRInst(
            op=Op.ALLOC, result=node.name, args=dims,
            type=self._type_of(node.name), line=node.line,
        ))
        return [block]

    def _lower_deallocate(self, node: ast.DeallocateStmt) -> list:
        block = IRBlock(self._fresh_block("free"), line=node.line)
        block.insts.append(IRInst(
            op=Op.FREE, args=[IRRef(node.name, self._type_of(node.name))],
            type=IRType.VOID, line=node.line,
        ))
        return [block]

    # ── helpers ──────────────────────────────────────────────

    def _operand_type(self, op: Operand) -> IRType:
        if isinstance(op, IRConst):
            return op.type
        if isinstance(op, IRRef):
            return op.type
        return IRType.REAL

    def _promote(self, a: IRType, b: IRType) -> IRType:
        if a == b:
            return a
        if IRType.REAL in (a, b):
            return IRType.REAL
        # Fortran kind promotion: INTEGER*8 wins over default INTEGER
        if {a, b} <= {IRType.INT64, IRType.INTEGER} and IRType.INT64 in (a, b):
            return IRType.INT64
        return a

    def _const_value(self, node) -> Any:
        """Extract a compile-time constant from an AST node.

        Folds literals, PARAMETER references, unary +/-, and binary
        +,-,*,/,** over numeric constants. Returns None when the
        expression is not a compile-time constant (variables, calls);
        downstream paths handle that (STATIC: no initializer, PARAMETER:
        loud 'None' in the emitted C).
        """
        if isinstance(node, ast.Literal):
            return node.value
        if isinstance(node, ast.Variable):
            # PARAMETER names are compile-time constants
            return self._param_values.get(node.name)
        if isinstance(node, ast.UnaryOp) and node.op in ("+", "-"):
            v = self._const_value(node.operand)
            if self._is_numeric(v):
                return v if node.op == "+" else -v
            return None
        if isinstance(node, ast.BinaryOp) and node.op in ("+", "-", "*", "/", "**"):
            l = self._const_value(node.left)
            r = self._const_value(node.right)
            if self._is_numeric(l) and self._is_numeric(r):
                try:
                    return self._fold_binop(node.op, l, r)
                except ArithmeticError:
                    return None
            return None
        return None

    @staticmethod
    def _is_numeric(v) -> bool:
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    @staticmethod
    def _fold_binop(op: str, l, r):
        """Fold a binary op over two numeric constants.

        INTEGER/INTEGER stays INTEGER: division truncates toward zero
        like C (-7/2 = -3, not Python's floor -4), and ** keeps an int
        result for non-negative int exponents. Any REAL operand promotes
        to float math; INTEGER ** negative exponent folds to REAL.
        Division by zero returns None (left to downstream handling).
        """
        real_math = isinstance(l, float) or isinstance(r, float)
        if op == "+":
            return l + r
        if op == "-":
            return l - r
        if op == "*":
            return l * r
        if op == "/":
            if r == 0:
                return None
            if real_math:
                return l / r
            # C truncates toward zero; Python // floors
            q = abs(l) // abs(r)
            return q if (l < 0) == (r < 0) else -q
        if op == "**":
            if real_math:
                v = float(l) ** float(r)
                # float ** float can yield complex (e.g. (-1.0) ** 0.5)
                return v if isinstance(v, float) else None
            if r < 0:
                return float(l) ** r
            return l ** r
        return None

    # Fix: _lower_if and _lower_loop should return lists, update _lower_stmt

    def _lower_stmt(self, node) -> list:
        """Lower one AST statement to a list of IR items."""
        if isinstance(node, ast.Declaration):
            ir_type = self._ir_type(node.type_name)
            for v in node.variables:
                self._var_types[v.name] = ir_type
                if v.shape:
                    self._array_shapes[v.name] = self._lower_shape(v.shape)
            return []

        if isinstance(node, ast.AssignStmt):
            return self._lower_assign(node)

        if isinstance(node, ast.IfStmt):
            return self._lower_if(node)

        if isinstance(node, ast.DoLoop):
            return self._lower_loop(node)

        if isinstance(node, ast.DoWhileStmt):
            return self._lower_while(node)

        if isinstance(node, ast.SelectCaseStmt):
            return self._lower_select(node)

        if isinstance(node, ast.PrintStmt):
            return self._lower_print(node)

        if isinstance(node, ast.WriteStmt):
            return self._lower_write(node)

        if isinstance(node, ast.OpenStmt):
            block = IRBlock(self._fresh_block("open"), line=node.line)
            u = self._lower_expr(node.unit, block)
            block.insts.append(IRInst(
                op=Op.OPEN, args=[u], type=IRType.VOID, line=node.line,
                meta={"path": node.path, "mode": node.mode},
            ))
            return [block]

        if isinstance(node, ast.CloseStmt):
            block = IRBlock(self._fresh_block("close"), line=node.line)
            u = self._lower_expr(node.unit, block)
            block.insts.append(IRInst(
                op=Op.CLOSE, args=[u], type=IRType.VOID, line=node.line,
            ))
            return [block]

        if isinstance(node, ast.ReturnStmt):
            return self._lower_return(node)

        if isinstance(node, ast.CallStmt):
            return self._lower_call_stmt(node)

        if isinstance(node, ast.AllocateStmt):
            return self._lower_allocate(node)

        if isinstance(node, ast.DeallocateStmt):
            return self._lower_deallocate(node)

        if isinstance(node, ast.CycleStmt):
            block = IRBlock(self._fresh_block("cycle"))
            block.insts.append(IRInst(op=Op.COPY, type=IRType.VOID,
                                      meta={"kind": "cycle"}))
            return [block]

        if isinstance(node, ast.ExitStmt):
            block = IRBlock(self._fresh_block("exit"))
            block.insts.append(IRInst(op=Op.COPY, type=IRType.VOID,
                                      meta={"kind": "exit"}))
            return [block]

        if isinstance(node, ast.StopStmt):
            block = IRBlock(self._fresh_block("stop"))
            block.insts.append(IRInst(op=Op.STOP, type=IRType.VOID))
            return [block]

        if isinstance(node, ast.FlushStmt):
            block = IRBlock(self._fresh_block("flush"))
            block.insts.append(IRInst(op=Op.FLUSH, type=IRType.VOID))
            return [block]

        if isinstance(node, ast.VerifyStmt):
            block = IRBlock(self._fresh_block("verify"), line=node.line)
            block.insts.append(IRInst(
                op=Op.VERIFY, type=IRType.VOID, line=node.line,
                meta={
                    "arrays": node.arrays,
                    "oracle_size": node.oracle_size,
                    "every": node.every,
                    "tolerance": node.tolerance,
                    "net_host": node.net_host,
                    "net_gpu_id": node.net_gpu_id,
                }
            ))
            return [block]

        if isinstance(node, ast.SortByGenStmt):
            block = IRBlock(self._fresh_block("sort_by_gen"), line=node.line)
            block.insts.append(IRInst(
                op=Op.SORT_BY_GEN, type=IRType.VOID, line=node.line,
                meta={"arrays": node.arrays}
            ))
            return [block]

        if isinstance(node, ast.VerifyHandshakeStmt):
            # Phase-1 lint directive: no IR emission.
            return []

        if isinstance(node, ast.HandshakeStmt):
            return self._lower_handshake(node)

        if isinstance(node, (ast.ImplicitNone, ast.DataStmt)):
            return []

        return []

    def _lower_handshake(self, node: ast.HandshakeStmt) -> list:
        """Lower a HANDSHAKE ... ENDHANDSHAKE block.

        Emits:
          - entry capture for each CONSERVE invariant (captured at handshake
            entry, before any stage runs)
          - the body statements
          - CONSERVE + ORACLE checks after every top-level stage (counted
            DO loop or IF block) and at the end of the handshake
        """
        opts = node.options
        conserve = opts.get("CONSERVE", [])
        oracles = opts.get("ORACLE", [])
        handshake_name = node.name

        # Entry-capture locals for CONSERVE invariants.
        capture_vars: dict[str, tuple[str, IRType]] = {}
        capture_block = IRBlock(self._fresh_block("hhb_capture"), line=node.line)
        for inv_name, value_expr, tol in conserve:
            entry_name = f"_hhb_{handshake_name}_{inv_name}_entry"
            # Lower the expression once to determine its type and produce
            # instructions; declare the capture variable with that type.
            val_op = self._lower_expr(value_expr, capture_block)
            val_type = self._operand_type(val_op)
            capture_vars[inv_name] = (entry_name, val_type)
            self._var_types[entry_name] = val_type
            if self._current_locals is not None:
                self._current_locals.append(
                    IRVar(name=entry_name, type=val_type))
            capture_block.insts.append(IRInst(
                op=Op.COPY, result=entry_name, args=[val_op], type=val_type,
                line=node.line,
            ))

        result: list = []
        if capture_block.insts:
            result.append(capture_block)

        # Lower body and inject boundary checks after each stage.
        for stmt in node.body:
            result.extend(self._lower_stmt(stmt))
            if isinstance(stmt, (ast.DoLoop, ast.IfStmt)):
                # Stage boundary: emit checks.
                result.extend(self._build_hhb_boundary_checks(
                    node, conserve, oracles, capture_vars, stmt.line))

        return result

    def _build_hhb_boundary_checks(
        self, node: ast.HandshakeStmt, conserve: list, oracles: list,
        capture_vars: dict[str, tuple[str, IRType]], line: int
    ) -> list:
        """Build IR items for one boundary check point."""
        items: list = []
        handshake_name = node.name

        # CONSERVE checks: |current_value - entry_value| > TOL  => fail
        for inv_name, value_expr, tol in conserve:
            entry_name, entry_type = capture_vars[inv_name]
            check_block = IRBlock(self._fresh_block("hhb_check"), line=line)
            cur_op = self._lower_expr(value_expr, check_block)
            entry_op = IRRef(entry_name, entry_type)
            diff_t = self._fresh_temp()
            check_block.insts.append(IRInst(
                op=Op.SUB, result=diff_t, args=[cur_op, entry_op],
                type=entry_type, line=line,
            ))
            abs_t = self._fresh_temp()
            check_block.insts.append(IRInst(
                op=Op.ABS, result=abs_t, args=[IRRef(diff_t, entry_type)],
                type=entry_type, line=line,
            ))
            tol_op = IRConst(entry_type, tol)
            cond_t = self._fresh_temp()
            check_block.insts.append(IRInst(
                op=Op.GT, result=cond_t,
                args=[IRRef(abs_t, entry_type), tol_op],
                type=IRType.LOGICAL, line=line,
            ))
            fail_block = self._hhb_fail_block(
                handshake_name, "CONSERVE", inv_name, line,
                actual_op=cur_op, expected_op=entry_op, tol_op=tol_op)
            items.append(check_block)
            items.append(IRIf(
                condition=IRRef(cond_t, IRType.LOGICAL),
                then_body=[fail_block],
                line=line,
            ))

        # ORACLE checks: |actual - expected| > LIMIT  => fail
        for spec in oracles:
            oracle_name = spec.get("name", "<unnamed>")
            expected_expr = spec.get("VALUE")
            limit = spec.get("LIMIT")
            if expected_expr is None or limit is None:
                continue
            check_block = IRBlock(self._fresh_block("hhb_oracle"), line=line)
            actual_op = self._lower_expr(
                ast.Variable(oracle_name), check_block)
            actual_type = self._operand_type(actual_op)
            expected_op = self._lower_expr(expected_expr, check_block)
            diff_t = self._fresh_temp()
            check_block.insts.append(IRInst(
                op=Op.SUB, result=diff_t, args=[actual_op, expected_op],
                type=actual_type, line=line,
            ))
            abs_t = self._fresh_temp()
            check_block.insts.append(IRInst(
                op=Op.ABS, result=abs_t, args=[IRRef(diff_t, actual_type)],
                type=actual_type, line=line,
            ))
            limit_op = IRConst(actual_type, limit)
            cond_t = self._fresh_temp()
            check_block.insts.append(IRInst(
                op=Op.GT, result=cond_t,
                args=[IRRef(abs_t, actual_type), limit_op],
                type=IRType.LOGICAL, line=line,
            ))
            fail_block = self._hhb_fail_block(
                handshake_name, "ORACLE", oracle_name, line,
                actual_op=actual_op, expected_op=expected_op, tol_op=limit_op)
            items.append(check_block)
            items.append(IRIf(
                condition=IRRef(cond_t, IRType.LOGICAL),
                then_body=[fail_block],
                line=line,
            ))

        return items

    def _hhb_fail_block(self, handshake_name: str, kind: str, name: str,
                        line: int, *, actual_op: Operand, expected_op: Operand,
                        tol_op: Operand) -> IRBlock:
        """Build a block that prints a rich HHB failure message and exits(1)."""
        block = IRBlock(self._fresh_block("hhb_fail"), line=line)
        label = (f"HHB_SCANFAIL handshake={handshake_name} kind={kind} "
                 f"name={name} line={line}")
        fmt = label + " actual=%.17e expected=%.17e tol=%.17e"
        block.insts.append(IRInst(
            op=Op.WRITE, args=[actual_op, expected_op, tol_op],
            type=IRType.VOID, line=line,
            meta={"unit": "0", "fmt": fmt, "advance": True},
        ))
        block.insts.append(IRInst(
            op=Op.HHB_FAIL, type=IRType.VOID, line=line,
            meta={"message": label},
        ))
        return block
