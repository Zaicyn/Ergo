from .tokens import Token, TT
from .errors import ParseError
from . import ast_nodes as ast


TYPE_KEYWORDS = (TT.KW_REAL, TT.KW_INTEGER, TT.KW_LOGICAL,
                 TT.KW_COMPLEX, TT.KW_CHARACTER)


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # ── helpers ──────────────────────────────────────────────

    def _cur(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self, offset=1) -> Token:
        i = self.pos + offset
        if i < len(self.tokens):
            return self.tokens[i]
        return self.tokens[-1]  # EOF

    def _at(self, *types: TT) -> bool:
        return self._cur().type in types

    def _eat(self, tt: TT, msg: str = None) -> Token:
        tok = self._cur()
        if tok.type != tt:
            msg = msg or f"Expected {tt.name}, got {tok.type.name}"
            raise ParseError(msg, tok.line, tok.col)
        self.pos += 1
        return tok

    def _match(self, *types: TT) -> Token | None:
        if self._cur().type in types:
            tok = self._cur()
            self.pos += 1
            return tok
        return None

    def _skip_newlines(self):
        while self._cur().type == TT.NEWLINE:
            self.pos += 1

    def _eat_newline(self):
        if self._cur().type == TT.NEWLINE:
            self.pos += 1
        elif self._cur().type == TT.EOF:
            pass
        else:
            raise ParseError(
                f"Expected newline, got {self._cur().type.name}",
                self._cur().line, self._cur().col,
            )

    # ── top-level ────────────────────────────────────────────

    def parse(self) -> ast.Program:
        self._skip_newlines()
        units = []
        while not self._at(TT.EOF):
            # Typed function: INTEGER FUNCTION name(...)
            if self._at(*TYPE_KEYWORDS) and self._peek().type == TT.KW_FUNCTION:
                units.append(self._parse_typed_function())
            elif self._at(TT.KW_FUNCTION):
                units.append(self._parse_function())
            elif self._at(TT.KW_SUBROUTINE):
                units.append(self._parse_subroutine())
            elif self._at(TT.KW_STATIC):
                units.append(self._parse_static_declaration())
            elif self._at(TT.KW_PARAMETER):
                units.append(self._parse_parameter_declaration())
            elif self._at(TT.KW_DATA):
                units.append(self._parse_data_stmt())
            else:
                units.append(self._parse_statement())
            self._skip_newlines()
        return ast.Program(units)

    # ── functions / subroutines ──────────────────────────────

    def _parse_typed_function(self) -> ast.FunctionDef:
        """Parse: INTEGER FUNCTION name(...) or REAL FUNCTION name(...)"""
        ret_tok = self._eat(self._cur().type)
        ret_type = ret_tok.value.upper()
        self._eat(TT.KW_FUNCTION)
        name = self._eat(TT.IDENT).value
        self._eat(TT.LPAREN)
        params = self._parse_ident_list()
        self._eat(TT.RPAREN)
        self._eat_newline()
        self._skip_newlines()

        decls, body = self._parse_body_until(TT.KW_END)
        self._eat(TT.KW_END)
        self._eat_newline()
        return ast.FunctionDef(name, params, decls, body, return_type=ret_type)

    def _parse_function(self) -> ast.FunctionDef:
        self._eat(TT.KW_FUNCTION)
        name = self._eat(TT.IDENT).value
        self._eat(TT.LPAREN)
        params = self._parse_ident_list()
        self._eat(TT.RPAREN)
        self._eat_newline()
        self._skip_newlines()

        decls, body = self._parse_body_until(TT.KW_END)
        self._eat(TT.KW_END)
        self._eat_newline()
        return ast.FunctionDef(name, params, decls, body)

    def _parse_subroutine(self) -> ast.SubroutineDef:
        self._eat(TT.KW_SUBROUTINE)
        name = self._eat(TT.IDENT).value
        params = []
        if self._match(TT.LPAREN):
            params = self._parse_ident_list()
            self._eat(TT.RPAREN)
        self._eat_newline()
        self._skip_newlines()

        decls, body = self._parse_body_until(TT.KW_END)
        self._eat(TT.KW_END)
        self._eat_newline()
        return ast.SubroutineDef(name, params, decls, body)

    def _parse_ident_list(self) -> list[str]:
        names = []
        if not self._at(TT.RPAREN):
            names.append(self._eat(TT.IDENT).value)
            while self._match(TT.COMMA):
                names.append(self._eat(TT.IDENT).value)
        return names

    def _parse_body_until(self, *stop: TT) -> tuple[list, list]:
        decls = []
        body = []
        while not self._at(*stop, TT.EOF):
            if self._at(*TYPE_KEYWORDS):
                # Could be typed function inside body? No — just a declaration
                decls.append(self._parse_declaration())
            elif self._at(TT.KW_IMPLICIT):
                body.append(self._parse_implicit_none())
            else:
                body.append(self._parse_statement())
            self._skip_newlines()
        return decls, body

    # ── declarations ─────────────────────────────────────────

    def _parse_static_declaration(self) -> ast.Declaration:
        """Parse: STATIC INTEGER :: name(shape), ... or STATIC REAL :: ..."""
        line = self._cur().line
        self._eat(TT.KW_STATIC)
        type_tok = self._eat(self._cur().type)
        type_name = type_tok.value.upper()

        self._eat(TT.COLONCOLON)

        variables = []
        variables.append(self._parse_var_decl(allocatable=False))
        while self._match(TT.COMMA):
            variables.append(self._parse_var_decl(allocatable=False))

        self._eat_newline()
        return ast.Declaration(type_name, variables, allocatable=False, static=True, line=line)

    def _parse_declaration(self) -> ast.Declaration:
        line = self._cur().line
        type_tok = self._eat(self._cur().type)
        type_name = type_tok.value.upper()

        allocatable = False
        parameter = False
        if self._match(TT.COMMA):
            if self._at(TT.KW_ALLOCATABLE):
                self._eat(TT.KW_ALLOCATABLE)
                allocatable = True
            elif self._at(TT.KW_PARAMETER):
                self._eat(TT.KW_PARAMETER)
                parameter = True
            else:
                raise ParseError(
                    f"Expected ALLOCATABLE or PARAMETER after comma, "
                    f"got {self._cur().type.name}",
                    self._cur().line, self._cur().col,
                )

        self._eat(TT.COLONCOLON)

        variables = []
        variables.append(self._parse_var_decl(allocatable))
        while self._match(TT.COMMA):
            variables.append(self._parse_var_decl(allocatable))

        # PARAMETER requires initializer
        if parameter:
            for v in variables:
                if v.init_value is None:
                    raise ParseError(
                        f"PARAMETER '{v.name}' must have an initializer",
                        line, 0,
                    )

        self._eat_newline()
        return ast.Declaration(type_name, variables, allocatable, parameter=parameter, line=line)

    def _parse_parameter_declaration(self) -> ast.Declaration:
        """Parse: PARAMETER REAL :: GRAVITY = 9.80665"""
        line = self._cur().line
        self._eat(TT.KW_PARAMETER)
        type_tok = self._eat(self._cur().type)
        type_name = type_tok.value.upper()

        self._eat(TT.COLONCOLON)

        variables = []
        variables.append(self._parse_var_decl(allocatable=False))
        while self._match(TT.COMMA):
            variables.append(self._parse_var_decl(allocatable=False))

        for v in variables:
            if v.init_value is None:
                raise ParseError(
                    f"PARAMETER '{v.name}' must have an initializer",
                    line, 0,
                )

        self._eat_newline()
        return ast.Declaration(type_name, variables, allocatable=False, parameter=True, line=line)

    def _parse_var_decl(self, allocatable: bool) -> ast.VarDecl:
        name = self._eat(TT.IDENT).value
        shape = None
        init_value = None
        if self._match(TT.LPAREN):
            dims = []
            dims.append(self._parse_dim_spec(allocatable))
            while self._match(TT.COMMA):
                dims.append(self._parse_dim_spec(allocatable))
            self._eat(TT.RPAREN)
            shape = tuple(dims)
        # Optional initializer: = expr
        if self._match(TT.EQ):
            init_value = self._parse_expression()
        return ast.VarDecl(name, shape, init_value=init_value)

    def _parse_dim_spec(self, allocatable: bool):
        if allocatable and self._at(TT.COLON):
            self._eat(TT.COLON)
            return ":"
        return self._parse_expression()

    # ── DATA statement ───────────────────────────────────────

    def _parse_data_stmt(self) -> ast.DataStmt:
        """Parse: DATA name / val1, val2, ... /"""
        self._eat(TT.KW_DATA)
        name = self._eat(TT.IDENT).value
        self._eat(TT.SLASH, "Expected '/' before DATA values")
        values = []
        values.append(self._parse_data_value())
        while self._match(TT.COMMA):
            values.append(self._parse_data_value())
        self._eat(TT.SLASH, "Expected '/' after DATA values")
        self._eat_newline()
        return ast.DataStmt(name, values)

    def _parse_data_value(self):
        """Parse a literal value, possibly with unary minus."""
        if self._at(TT.MINUS):
            self.pos += 1
            tok = self._match(TT.INTEGER_LIT, TT.REAL_LIT)
            if tok:
                if tok.type == TT.INTEGER_LIT:
                    return ast.Literal("INTEGER", -tok.value)
                return ast.Literal("REAL", -tok.value)
            raise ParseError("Expected number after '-' in DATA", self._cur().line, self._cur().col)
        tok = self._match(TT.INTEGER_LIT)
        if tok:
            return ast.Literal("INTEGER", tok.value)
        tok = self._match(TT.REAL_LIT)
        if tok:
            return ast.Literal("REAL", tok.value)
        tok = self._match(TT.STRING_LIT)
        if tok:
            return ast.Literal("STRING", tok.value)
        raise ParseError(f"Expected literal in DATA statement, got {self._cur().type.name}",
                         self._cur().line, self._cur().col)

    # ── statements ───────────────────────────────────────────

    def _parse_statement(self):
        if self._at(TT.KW_IF):
            return self._parse_if()
        if self._at(TT.KW_SELECT):
            return self._parse_select_case()
        if self._at(TT.KW_DO):
            return self._parse_do()
        if self._at(TT.KW_PRINT):
            return self._parse_print()
        if self._at(TT.KW_WRITE):
            return self._parse_write()
        if self._at(TT.KW_RETURN):
            return self._parse_return()
        if self._at(TT.KW_CALL):
            return self._parse_call()
        if self._at(TT.KW_ALLOCATE):
            return self._parse_allocate()
        if self._at(TT.KW_DEALLOCATE):
            return self._parse_deallocate()
        if self._at(TT.KW_IMPLICIT):
            return self._parse_implicit_none()
        if self._at(TT.KW_DATA):
            return self._parse_data_stmt()
        if self._at(TT.KW_STATIC):
            return self._parse_static_declaration()
        if self._at(TT.KW_PARAMETER):
            return self._parse_parameter_declaration()
        if self._at(TT.KW_CYCLE):
            self._eat(TT.KW_CYCLE)
            self._eat_newline()
            return ast.CycleStmt()
        if self._at(TT.KW_STOP):
            self._eat(TT.KW_STOP)
            self._eat_newline()
            return ast.StopStmt()
        if self._at(TT.KW_FLUSH):
            self._eat(TT.KW_FLUSH)
            self._eat_newline()
            return ast.FlushStmt()
        if self._at(TT.KW_VERIFY):
            return self._parse_verify()
        # Declaration (inside function body)
        if self._at(*TYPE_KEYWORDS):
            return self._parse_declaration()
        # Assignment: ident := expr  OR  ident(args) := expr
        return self._parse_assignment()

    def _parse_implicit_none(self) -> ast.ImplicitNone:
        self._eat(TT.KW_IMPLICIT)
        self._eat(TT.KW_NONE)
        self._eat_newline()
        return ast.ImplicitNone()

    def _parse_if(self) -> ast.IfStmt:
        line = self._cur().line
        self._eat(TT.KW_IF)
        cond = self._parse_expression()
        self._eat(TT.KW_THEN)
        self._eat_newline()
        self._skip_newlines()

        then_body = []
        while not self._at(TT.KW_ELSE, TT.KW_ELSEIF, TT.KW_ENDIF, TT.EOF):
            then_body.append(self._parse_statement())
            self._skip_newlines()

        else_body = None
        if self._at(TT.KW_ELSEIF):
            # ELSEIF becomes nested IfStmt in the else branch
            else_body = [self._parse_elseif()]
        elif self._match(TT.KW_ELSE):
            self._eat_newline()
            self._skip_newlines()
            else_body = []
            while not self._at(TT.KW_ENDIF, TT.EOF):
                else_body.append(self._parse_statement())
                self._skip_newlines()

        self._eat(TT.KW_ENDIF)
        self._eat_newline()
        return ast.IfStmt(cond, then_body, else_body, line=line)

    def _parse_elseif(self) -> ast.IfStmt:
        """Parse ELSEIF chain — returns nested IfStmt without consuming ENDIF."""
        line = self._cur().line
        self._eat(TT.KW_ELSEIF)
        cond = self._parse_expression()
        self._eat(TT.KW_THEN)
        self._eat_newline()
        self._skip_newlines()

        then_body = []
        while not self._at(TT.KW_ELSE, TT.KW_ELSEIF, TT.KW_ENDIF, TT.EOF):
            then_body.append(self._parse_statement())
            self._skip_newlines()

        else_body = None
        if self._at(TT.KW_ELSEIF):
            else_body = [self._parse_elseif()]
        elif self._match(TT.KW_ELSE):
            self._eat_newline()
            self._skip_newlines()
            else_body = []
            while not self._at(TT.KW_ENDIF, TT.EOF):
                else_body.append(self._parse_statement())
                self._skip_newlines()

        # Don't consume ENDIF — the outermost _parse_if does that
        return ast.IfStmt(cond, then_body, else_body, line=line)

    def _parse_select_case(self) -> ast.SelectCaseStmt:
        """Parse: SELECT CASE (expr) / CASE val / ... / CASE DEFAULT / ... / ENDSELECT"""
        line = self._cur().line
        self._eat(TT.KW_SELECT)
        self._eat(TT.KW_CASE)
        self._eat(TT.LPAREN)
        expr = self._parse_expression()
        self._eat(TT.RPAREN)
        self._eat_newline()
        self._skip_newlines()

        cases = []
        while not self._at(TT.KW_ENDSELECT, TT.EOF):
            self._eat(TT.KW_CASE)
            # CASE DEFAULT or CASE value
            if self._match(TT.KW_DEFAULT):
                case_val = None
            else:
                case_val = self._parse_expression()
            self._eat_newline()
            self._skip_newlines()

            body = []
            while not self._at(TT.KW_CASE, TT.KW_ENDSELECT, TT.EOF):
                body.append(self._parse_statement())
                self._skip_newlines()

            cases.append((case_val, body))

        self._eat(TT.KW_ENDSELECT)
        self._eat_newline()
        return ast.SelectCaseStmt(expr, cases, line=line)

    def _parse_do(self) -> ast.DoLoop:
        line = self._cur().line
        self._eat(TT.KW_DO)
        var = self._eat(TT.IDENT).value
        self._eat(TT.EQ)
        start = self._parse_expression()
        self._eat(TT.COMMA)
        end = self._parse_expression()
        step = ast.Literal("INTEGER", 1)
        if self._match(TT.COMMA):
            step = self._parse_expression()
        self._eat_newline()
        self._skip_newlines()

        body = []
        while not self._at(TT.KW_ENDDO, TT.EOF):
            body.append(self._parse_statement())
            self._skip_newlines()

        self._eat(TT.KW_ENDDO)
        self._eat_newline()
        return ast.DoLoop(var, start, end, step, body, line=line)

    def _parse_verify(self) -> ast.VerifyStmt:
        """Parse: VERIFY arr1, arr2, ... ORACLE n EVERY m TOL t"""
        line = self._cur().line
        self._eat(TT.KW_VERIFY)
        # Parse comma-separated array names
        arrays = [self._eat(TT.IDENT).value]
        while self._match(TT.COMMA):
            arrays.append(self._eat(TT.IDENT).value)
        # ORACLE n — required
        oracle_tok = self._eat(TT.IDENT)
        if oracle_tok.value != "ORACLE":
            raise self._error(f"Expected ORACLE, got '{oracle_tok.value}'")
        oracle_size = self._eat(TT.INTEGER_LIT).value
        # EVERY m — optional
        every = 1
        if self._at(TT.IDENT) and self._cur().value == "EVERY":
            self._eat(TT.IDENT)
            every = self._eat(TT.INTEGER_LIT).value
        # TOL t — optional
        tolerance = 1e-6
        if self._at(TT.IDENT) and self._cur().value == "TOL":
            self._eat(TT.IDENT)
            tolerance = self._parse_expression()  # allow numeric expression
            if hasattr(tolerance, 'value'):
                tolerance = tolerance.value
        # NET "host:port" — optional, enables UDP transport to oracle
        net_host = None
        net_gpu_id = 0
        if self._at(TT.IDENT) and self._cur().value == "NET":
            self._eat(TT.IDENT)
            tok = self._eat(TT.STRING_LIT)
            net_host = tok.value
            # GPU n — optional client identity
            if self._at(TT.IDENT) and self._cur().value == "GPU":
                self._eat(TT.IDENT)
                net_gpu_id = self._eat(TT.INTEGER_LIT).value
        self._eat_newline()
        return ast.VerifyStmt(arrays, oracle_size, every, tolerance,
                              net_host=net_host, net_gpu_id=net_gpu_id,
                              line=line)

    def _parse_print(self) -> ast.PrintStmt:
        line = self._cur().line
        self._eat(TT.KW_PRINT)
        val = self._parse_expression()
        self._eat_newline()
        return ast.PrintStmt(val, line=line)

    def _parse_write(self) -> ast.WriteStmt:
        """Parse: WRITE(unit, "fmt") arg1, arg2, ...
        Or:    WRITE(unit, "fmt", "NO") arg1, arg2, ...  (no-advance)
        unit: * for stdout, 0 for stderr
        """
        line = self._cur().line
        self._eat(TT.KW_WRITE)
        self._eat(TT.LPAREN)
        # Unit: * or 0 or integer
        if self._match(TT.STAR):
            unit = "*"
        else:
            tok = self._eat(TT.INTEGER_LIT)
            unit = str(tok.value)
        self._eat(TT.COMMA)
        # Format string
        fmt_tok = self._eat(TT.STRING_LIT)
        fmt = fmt_tok.value
        # Optional ADVANCE control
        advance = True
        if self._match(TT.COMMA):
            adv_tok = self._eat(TT.STRING_LIT)
            if adv_tok.value.upper() == "NO":
                advance = False
        self._eat(TT.RPAREN)
        # Arguments
        args = []
        if not self._at(TT.NEWLINE, TT.EOF):
            args.append(self._parse_expression())
            while self._match(TT.COMMA):
                args.append(self._parse_expression())
        self._eat_newline()
        return ast.WriteStmt(unit, fmt, args, advance, line=line)

    def _parse_return(self) -> ast.ReturnStmt:
        line = self._cur().line
        self._eat(TT.KW_RETURN)
        val = None
        if not self._at(TT.NEWLINE, TT.EOF):
            val = self._parse_expression()
        self._eat_newline()
        return ast.ReturnStmt(val, line=line)

    def _parse_call(self) -> ast.CallStmt:
        line = self._cur().line
        self._eat(TT.KW_CALL)
        name = self._eat(TT.IDENT).value
        args = []
        if self._match(TT.LPAREN):
            if not self._at(TT.RPAREN):
                args.append(self._parse_expression())
                while self._match(TT.COMMA):
                    args.append(self._parse_expression())
            self._eat(TT.RPAREN)
        self._eat_newline()
        return ast.CallStmt(name, args, line=line)

    def _parse_allocate(self) -> ast.AllocateStmt:
        line = self._cur().line
        self._eat(TT.KW_ALLOCATE)
        self._eat(TT.LPAREN)
        name = self._eat(TT.IDENT).value
        self._eat(TT.LPAREN)
        dims = [self._parse_expression()]
        while self._match(TT.COMMA):
            dims.append(self._parse_expression())
        self._eat(TT.RPAREN)
        self._eat(TT.RPAREN)
        self._eat_newline()
        return ast.AllocateStmt(name, dims, line=line)

    def _parse_deallocate(self) -> ast.DeallocateStmt:
        line = self._cur().line
        self._eat(TT.KW_DEALLOCATE)
        self._eat(TT.LPAREN)
        name = self._eat(TT.IDENT).value
        self._eat(TT.RPAREN)
        self._eat_newline()
        return ast.DeallocateStmt(name, line=line)

    def _parse_assignment(self):
        line = self._cur().line
        target = self._parse_expression()
        if not self._match(TT.ASSIGN):
            raise ParseError(
                f"Expected ':=' in assignment, got {self._cur().type.name}",
                self._cur().line, self._cur().col,
            )
        value = self._parse_expression()
        self._eat_newline()
        return ast.AssignStmt(target, value, line=line)

    # ── expressions (precedence climbing) ────────────────────

    def _parse_expression(self):
        return self._parse_or()

    def _parse_or(self):
        left = self._parse_and()
        while self._match(TT.OR):
            right = self._parse_and()
            left = ast.BinaryOp(".OR.", left, right)
        return left

    def _parse_and(self):
        left = self._parse_not()
        while self._match(TT.AND):
            right = self._parse_not()
            left = ast.BinaryOp(".AND.", left, right)
        return left

    def _parse_not(self):
        if self._match(TT.NOT):
            operand = self._parse_not()
            return ast.UnaryOp(".NOT.", operand)
        return self._parse_relational()

    def _parse_relational(self):
        """Parse relational with comparison chain desugaring."""
        left = self._parse_additive()

        rel_ops = {TT.LT: "<", TT.GT: ">", TT.EQ: "=", TT.NEQ: "≠",
                   TT.LEQ: "≤", TT.GEQ: "≥"}

        comparisons = []
        while self._cur().type in rel_ops:
            op_str = rel_ops[self._cur().type]
            self.pos += 1
            right = self._parse_additive()
            comparisons.append((left, op_str, right))
            left = right

        if len(comparisons) == 0:
            return left
        if len(comparisons) == 1:
            c = comparisons[0]
            return ast.BinaryOp(c[1], c[0], c[2])

        # Chain: desugar to AND tree
        result = ast.BinaryOp(comparisons[0][1], comparisons[0][0], comparisons[0][2])
        for c in comparisons[1:]:
            cmp = ast.BinaryOp(c[1], c[0], c[2])
            result = ast.BinaryOp(".AND.", result, cmp)
        return result

    def _parse_additive(self):
        left = self._parse_multiplicative()
        while self._at(TT.PLUS, TT.MINUS):
            op = "+" if self._cur().type == TT.PLUS else "-"
            self.pos += 1
            right = self._parse_multiplicative()
            left = ast.BinaryOp(op, left, right)
        return left

    def _parse_multiplicative(self):
        left = self._parse_unary()
        while self._at(TT.STAR, TT.SLASH):
            op = "*" if self._cur().type == TT.STAR else "/"
            self.pos += 1
            right = self._parse_unary()
            left = ast.BinaryOp(op, left, right)
        return left

    def _parse_unary(self):
        if self._at(TT.PLUS, TT.MINUS):
            op = "+" if self._cur().type == TT.PLUS else "-"
            self.pos += 1
            operand = self._parse_unary()
            return ast.UnaryOp(op, operand)
        return self._parse_exponent()

    def _parse_exponent(self):
        base = self._parse_postfix()
        if self._match(TT.STARSTAR):
            exp = self._parse_unary()
            return ast.BinaryOp("**", base, exp)
        return base

    def _parse_postfix(self):
        expr = self._parse_primary()
        while self._at(TT.LPAREN):
            if not isinstance(expr, ast.Variable):
                break
            self._eat(TT.LPAREN)
            args = []
            if not self._at(TT.RPAREN):
                args.append(self._parse_expression())
                while self._match(TT.COMMA):
                    args.append(self._parse_expression())
            self._eat(TT.RPAREN)
            expr = ast.CallOrSubscript(expr.name, args)
        return expr

    def _parse_primary(self):
        tok = self._match(TT.INTEGER_LIT)
        if tok:
            return ast.Literal("INTEGER", tok.value)
        tok = self._match(TT.REAL_LIT)
        if tok:
            return ast.Literal("REAL", tok.value)
        tok = self._match(TT.STRING_LIT)
        if tok:
            return ast.Literal("STRING", tok.value)
        if self._match(TT.TRUE):
            return ast.Literal("LOGICAL", True)
        if self._match(TT.FALSE):
            return ast.Literal("LOGICAL", False)

        tok = self._match(TT.IDENT)
        if tok:
            return ast.Variable(tok.value)

        # Type keywords used as conversion functions: REAL(...), INT(...)
        if self._at(*TYPE_KEYWORDS):
            tok = self._cur()
            # Only treat as function call if followed by (
            if self._peek().type == TT.LPAREN:
                self.pos += 1
                return ast.Variable(tok.value.upper())

        if self._match(TT.LPAREN):
            expr = self._parse_expression()
            self._eat(TT.RPAREN)
            return expr

        raise ParseError(
            f"Unexpected token: {self._cur().type.name} ({self._cur().value!r})",
            self._cur().line, self._cur().col,
        )
