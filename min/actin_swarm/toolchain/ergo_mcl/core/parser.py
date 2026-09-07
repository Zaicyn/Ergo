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
        ret_type = self._maybe_kind_suffix(ret_type, ret_tok.line)
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

    def _maybe_kind_suffix(self, type_name: str, line: int) -> str:
        """INTEGER*8 kind suffix (64-bit integers, Inc-2A). Only *8 is
        valid; anything else is a parse error (never silently ignored)."""
        if type_name == "INTEGER" and self._at(TT.STAR):
            self._eat(TT.STAR)
            tok = self._eat(TT.INTEGER_LIT)
            if tok.value != 8:
                raise ParseError(
                    f"Only INTEGER*8 is supported, got INTEGER*{tok.value}",
                    line, tok.col)
            return "INTEGER*8"
        return type_name

    def _parse_static_declaration(self) -> ast.Declaration:
        """Parse: STATIC INTEGER :: name(shape), ... or STATIC REAL :: ..."""
        line = self._cur().line
        self._eat(TT.KW_STATIC)
        type_tok = self._eat(self._cur().type)
        type_name = type_tok.value.upper()
        type_name = self._maybe_kind_suffix(type_name, line)

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
        type_name = self._maybe_kind_suffix(type_name, line)

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

        if not self._at(TT.COLONCOLON):
            raise ParseError(
                f"declarations need '::' — write "
                f"'{type_name} :: name' (got "
                f"'{self._cur().value}')",
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
        if self._at(TT.KW_OPEN):
            return self._parse_open()
        if self._at(TT.KW_CLOSE):
            return self._parse_close()
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
        if self._at(TT.KW_EXIT):
            self._eat(TT.KW_EXIT)
            self._eat_newline()
            return ast.ExitStmt()
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
        if self._at(TT.KW_HANDSHAKE):
            return self._parse_handshake()
        if self._at(TT.KW_SORT_BY_GEN):
            return self._parse_sort_by_gen()
        # Declaration (inside function body)
        if self._at(*TYPE_KEYWORDS):
            return self._parse_declaration()
        # Friendly errors for the two END-shaped beginner mistakes
        if self._at(TT.KW_END):
            nxt = self._peek()
            if nxt.type in (TT.KW_DO, TT.KW_IF) or \
                    (nxt.type == TT.IDENT and
                     nxt.value.upper() in ("DO", "IF")):
                raise ParseError(
                    "ENDDO / ENDIF are one word in Ergo — "
                    "'END DO' / 'END IF' do not parse",
                    self._cur().line, self._cur().col,
                )
            raise ParseError(
                "Ergo has no PROGRAM/END wrapper — a bare END is not a "
                "program terminator; just end the file",
                self._cur().line, self._cur().col,
            )
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
        if not self._at(TT.KW_THEN):
            raise ParseError(
                "single-line IF is not supported in Ergo — write "
                "IF (cond) THEN / ENDIF with statements on their own "
                "lines (THEN is required)",
                self._cur().line, self._cur().col,
            )
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

    def _parse_do(self):
        line = self._cur().line
        self._eat(TT.KW_DO)

        # DO WHILE condition
        if self._at(TT.KW_WHILE):
            self._eat(TT.KW_WHILE)
            condition = self._parse_expression()
            self._eat_newline()
            self._skip_newlines()
            body = []
            while not self._at(TT.KW_ENDDO, TT.EOF):
                body.append(self._parse_statement())
                self._skip_newlines()
            self._eat(TT.KW_ENDDO)
            self._eat_newline()
            return ast.DoWhileStmt(condition, body, line=line)

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

    def _parse_hhb_options(self, context: str,
                           multiline: bool = False) -> tuple[dict, list]:
        """Parse Hopf Handshake Bound options shared by VERIFY HANDSHAKE and
        HANDSHAKE ... ENDHANDSHAKE. Returns (options, conserve_list).

        If multiline is True, newlines are treated as whitespace between
        options (used by HANDSHAKE ... ENDHANDSHAKE). Otherwise options are
        expected on a single line and the first NEWLINE terminates parsing
        (used by VERIFY HANDSHAKE).
        """
        options: dict = {}
        conserve: list[tuple[str, Any, float | None]] = []
        while True:
            if multiline:
                self._skip_newlines()
            if not self._at(TT.IDENT):
                break
            opt_tok = self._eat(TT.IDENT)
            opt_key = opt_tok.value.upper()
            if opt_key == "CONSERVE":
                # Parse CONSERVE <name> VALUE=<expr> TOL=<value> triples
                while self._at(TT.IDENT):
                    inv_name = self._eat(TT.IDENT).value.upper()
                    value_expr = None
                    tol = None
                    while self._at(TT.IDENT):
                        sub_key = self._eat(TT.IDENT).value.upper()
                        self._eat(TT.EQ)
                        if sub_key == "VALUE":
                            value_expr = self._parse_expression()
                        elif sub_key == "TOL":
                            tol_tok = self._cur()
                            if tol_tok.type == TT.REAL_LIT:
                                self._eat(TT.REAL_LIT)
                                tol = tol_tok.value
                            elif tol_tok.type == TT.INTEGER_LIT:
                                self._eat(TT.INTEGER_LIT)
                                tol = float(tol_tok.value)
                            else:
                                raise self._parse_error(
                                    "Expected REAL_LIT or INTEGER_LIT after TOL=",
                                    tol_tok)
                        else:
                            raise self._parse_error(
                                f"Unknown CONSERVE sub-option '{sub_key}'",
                                self._cur())
                        # Stop if next token is an option keyword
                        if (self._at(TT.IDENT) and
                                self._cur().value.upper() in
                                ("DEPTH", "FRAME_BYTES", "MAXIT", "MAX_REWIND",
                                 "PAYLOAD", "ORACLE", "CONSERVE", "EVERY", "NET")):
                            break
                        # Stop if next token is the start of a new CONSERVE triple
                        if (self._at(TT.IDENT) and
                                self._peek().type == TT.IDENT and
                                self._peek().value.upper() == "VALUE"):
                            break
                    conserve.append((inv_name, value_expr, tol))
                    # Stop if next token is another option keyword
                    if (self._at(TT.IDENT) and
                            self._cur().value.upper() in
                            ("DEPTH", "FRAME_BYTES", "MAXIT", "MAX_REWIND",
                             "PAYLOAD", "ORACLE", "EVERY", "NET")):
                        break
                continue
            if opt_key == "PAYLOAD":
                self._eat(TT.EQ)
                self._eat(TT.LPAREN)
                payload_vars = [self._eat(TT.IDENT).value]
                while self._match(TT.COMMA):
                    payload_vars.append(self._eat(TT.IDENT).value)
                self._eat(TT.RPAREN)
                options["PAYLOAD"] = payload_vars
                continue
            if opt_key == "ORACLE":
                # ORACLE <name> VALUE=... [P=...] LIMIT=...
                oracle_name = self._eat(TT.IDENT).value
                oracle_spec: dict = {"name": oracle_name}
                while self._at(TT.IDENT):
                    spec_key = self._eat(TT.IDENT).value.upper()
                    self._eat(TT.EQ)
                    if spec_key == "VALUE":
                        # VALUE is an expression evaluated at the boundary.
                        oracle_spec["VALUE"] = self._parse_expression()
                    elif spec_key in ("LIMIT", "P"):
                        # LIMIT/P are compile-time numeric tolerances.
                        tol_tok = self._cur()
                        if tol_tok.type == TT.REAL_LIT:
                            self._eat(TT.REAL_LIT)
                            oracle_spec[spec_key] = tol_tok.value
                        elif tol_tok.type == TT.INTEGER_LIT:
                            self._eat(TT.INTEGER_LIT)
                            oracle_spec[spec_key] = float(tol_tok.value)
                        else:
                            raise self._parse_error(
                                f"Expected numeric literal after {spec_key}=",
                                tol_tok)
                    else:
                        raise self._parse_error(
                            f"Unknown ORACLE sub-option '{spec_key}'",
                            self._cur())
                    # Stop if next token is an option keyword
                    if (self._at(TT.IDENT) and
                            self._cur().value.upper() in
                            ("DEPTH", "FRAME_BYTES", "MAXIT", "MAX_REWIND",
                             "PAYLOAD", "ORACLE", "CONSERVE", "EVERY", "NET")):
                        break
                options.setdefault("ORACLE", []).append(oracle_spec)
                continue
            if opt_key in ("DEPTH", "FRAME_BYTES", "MAXIT", "MAX_REWIND"):
                self._eat(TT.EQ)
                val_tok = self._cur()
                if val_tok.type == TT.INTEGER_LIT:
                    self._eat(TT.INTEGER_LIT)
                    options[opt_key] = val_tok.value
                elif val_tok.type == TT.IDENT:
                    self._eat(TT.IDENT)
                    options[opt_key] = val_tok.value  # PARAMETER reference
                else:
                    raise self._parse_error(
                        f"Expected INTEGER_LIT or IDENT after {opt_key}=",
                        val_tok)
                continue
            if opt_key in ("ORACLE", "EVERY", "TOL", "NET"):
                # These belong to the regular VERIFY form; backtrack
                # is not trivial, so treat as error here.
                raise ParseError(
                    f"Unexpected '{opt_key}' in {context} "
                    f"(use VERIFY ... ORACLE ... for oracle checkpoints)",
                    opt_tok.line, opt_tok.col)
            if opt_key == "PAYLOAD":
                # Should have been handled above; defensive error.
                raise ParseError(
                    f"Malformed PAYLOAD option in {context}",
                    opt_tok.line, opt_tok.col)
            raise ParseError(
                f"Unknown {context} option '{opt_key}'",
                opt_tok.line, opt_tok.col)
        if conserve:
            options["CONSERVE"] = conserve
        return options, conserve

    def _parse_verify(self) -> ast.VerifyStmt | ast.VerifyHandshakeStmt:
        """Parse: VERIFY arr1, arr2, ... ORACLE n EVERY m TOL t
                 OR VERIFY HANDSHAKE name [DEPTH=d] [FRAME_BYTES=b] ...
        """
        line = self._cur().line
        self._eat(TT.KW_VERIFY)
        # HHB directive form: VERIFY HANDSHAKE name [options]
        if ((self._at(TT.IDENT) or self._at(TT.KW_HANDSHAKE)) and
                self._cur().value.upper() == "HANDSHAKE"):
            self._eat(self._cur().type)
            name_tok = self._eat(TT.IDENT)
            name = name_tok.value
            options, _ = self._parse_hhb_options("VERIFY HANDSHAKE",
                                                  multiline=False)
            self._eat_newline()
            return ast.VerifyHandshakeStmt(name, options, line=line)
        # Standard VERIFY form
        arrays = [self._eat(TT.IDENT).value]
        while self._match(TT.COMMA):
            arrays.append(self._eat(TT.IDENT).value)
        # ORACLE n — required
        oracle_tok = self._eat(TT.IDENT)
        if oracle_tok.value.upper() != "ORACLE":
            raise ParseError(
                f"Expected ORACLE, got '{oracle_tok.value}'",
                oracle_tok.line, oracle_tok.col,
            )
        oracle_size = self._eat(TT.INTEGER_LIT).value
        # EVERY m — optional
        every = 1
        if self._at(TT.IDENT) and self._cur().value.upper() == "EVERY":
            self._eat(TT.IDENT)
            every = self._eat(TT.INTEGER_LIT).value
        # TOL t — optional; must be a numeric literal. The value is spliced
        # into generated C, so a general expression would stringify there
        # as Python AST repr garbage.
        tolerance = 1e-6
        if self._at(TT.IDENT) and self._cur().value.upper() == "TOL":
            self._eat(TT.IDENT)
            tol_line, tol_col = self._cur().line, self._cur().col
            tol_expr = self._parse_expression()
            if not (isinstance(tol_expr, ast.Literal)
                    and tol_expr.type in ("INTEGER", "REAL")):
                raise ParseError(
                    "TOL must be a numeric literal",
                    tol_line, tol_col,
                )
            tolerance = tol_expr.value
        # NET "host:port" — optional, enables UDP transport to oracle
        net_host = None
        net_gpu_id = 0
        if self._at(TT.IDENT) and self._cur().value.upper() == "NET":
            self._eat(TT.IDENT)
            tok = self._eat(TT.STRING_LIT)
            net_host = tok.value
            # GPU n — optional client identity
            if self._at(TT.IDENT) and self._cur().value.upper() == "GPU":
                self._eat(TT.IDENT)
                net_gpu_id = self._eat(TT.INTEGER_LIT).value
        self._eat_newline()
        return ast.VerifyStmt(arrays, oracle_size, every, tolerance,
                              net_host=net_host, net_gpu_id=net_gpu_id,
                              line=line)

    def _parse_handshake(self) -> ast.HandshakeStmt:
        """Parse: HANDSHAKE name [options] ... ENDHANDSHAKE

        Minimal Phase-3 form: options followed by a body terminated by
        ENDHANDSHAKE. The first counted DO/IF block inside the body is the
        handshake target; the rest is setup/teardown.
        """
        line = self._cur().line
        self._eat(TT.KW_HANDSHAKE)
        name_tok = self._eat(TT.IDENT)
        name = name_tok.value
        options, _ = self._parse_hhb_options("HANDSHAKE", multiline=True)
        self._skip_newlines()

        body = []
        while not self._at(TT.KW_ENDHANDSHAKE, TT.EOF):
            body.append(self._parse_statement())
            self._skip_newlines()
        self._eat(TT.KW_ENDHANDSHAKE)
        self._eat_newline()
        return ast.HandshakeStmt(name, options, body, line=line)

    def _parse_sort_by_gen(self) -> ast.SortByGenStmt:
        """Parse: SORT_BY_GEN arr1, arr2, ..."""
        line = self._cur().line
        self._eat(TT.KW_SORT_BY_GEN)
        arrays = [self._eat(TT.IDENT).value]
        while self._match(TT.COMMA):
            arrays.append(self._eat(TT.IDENT).value)
        self._eat_newline()
        return ast.SortByGenStmt(arrays, line=line)

    def _parse_print(self) -> ast.PrintStmt:
        line = self._cur().line
        self._eat(TT.KW_PRINT)
        val = self._parse_expression()
        if self._at(TT.COMMA):
            raise ParseError(
                "PRINT takes ONE expression — use WRITE(*, \"fmt\") "
                "with a format string for multiple values",
                self._cur().line, self._cur().col,
            )
        self._eat_newline()
        return ast.PrintStmt(val, line=line)

    def _parse_write(self) -> ast.WriteStmt:
        """Parse: WRITE(unit, "fmt") arg1, arg2, ...
        Or:    WRITE(unit, "fmt", "NO") arg1, arg2, ...  (no-advance)
        Or:    WRITE(unit) A(lo:hi), B(lo:hi), ...       (raw record)
        unit: * for stdout, 0 for stderr, or an INTEGER expression
        naming an OPEN'd file unit (Spec Part 10).
        """
        line = self._cur().line
        self._eat(TT.KW_WRITE)
        self._eat(TT.LPAREN)
        # Unit: * or integer literal or integer expression
        if self._match(TT.STAR):
            unit = "*"
        elif self._at(TT.INTEGER_LIT) and \
                self._peek().type in (TT.COMMA, TT.RPAREN):
            tok = self._eat(TT.INTEGER_LIT)
            unit = str(tok.value)
        else:
            unit = self._parse_expression()
        if self._match(TT.RPAREN):
            # Raw-record form: WRITE(unit) A(lo:hi), ...
            sections = []
            if not self._at(TT.NEWLINE, TT.EOF):
                sections.append(self._parse_section())
                while self._match(TT.COMMA):
                    sections.append(self._parse_section())
            if not sections:
                raise ParseError(
                    "WRITE(unit) with no format needs at least one "
                    "array section: WRITE(unit) A(lo:hi)",
                    self._cur().line, self._cur().col,
                )
            self._eat_newline()
            return ast.WriteStmt(unit, None, sections, True, line=line)
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

    def _parse_section(self) -> ast.ArraySection:
        """Parse A(lo:hi) — a 1-D array section (raw-record WRITE)."""
        line = self._cur().line
        name_tok = self._eat(TT.IDENT)
        self._eat(TT.LPAREN)
        lo = self._parse_expression()
        self._eat(TT.COLON)
        hi = self._parse_expression()
        self._eat(TT.RPAREN)
        return ast.ArraySection(name_tok.value, lo, hi, line=line)

    def _parse_open(self) -> ast.OpenStmt:
        """Parse: OPEN(unit, "path", MODE) — MODE "WRITE" | "APPEND"."""
        line = self._cur().line
        self._eat(TT.KW_OPEN)
        self._eat(TT.LPAREN)
        unit = self._parse_expression()
        self._eat(TT.COMMA)
        path_tok = self._eat(TT.STRING_LIT)
        self._eat(TT.COMMA)
        mode_tok = self._eat(TT.STRING_LIT)
        mode = mode_tok.value.upper()
        if mode not in ("WRITE", "APPEND"):
            raise ParseError(
                f"OPEN: MODE must be \"WRITE\" or \"APPEND\", got "
                f"\"{mode_tok.value}\"", mode_tok.line, mode_tok.col,
            )
        self._eat(TT.RPAREN)
        self._eat_newline()
        return ast.OpenStmt(unit, path_tok.value, mode, line=line)

    def _parse_close(self) -> ast.CloseStmt:
        """Parse: CLOSE(unit)."""
        line = self._cur().line
        self._eat(TT.KW_CLOSE)
        self._eat(TT.LPAREN)
        unit = self._parse_expression()
        self._eat(TT.RPAREN)
        self._eat_newline()
        return ast.CloseStmt(unit, line=line)

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
            if isinstance(target, ast.BinaryOp) and \
                    target.op in ("=", "=="):
                raise ParseError(
                    "assignment is ':=' in Ergo — bare '=' is a "
                    "comparison, and a comparison is not assignable",
                    line, self._cur().col,
                )
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
