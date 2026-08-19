from .tokens import Token, TT, KEYWORDS
from .errors import LexError


class Lexer:
    def __init__(self, source: str):
        # NOTE: line continuation is handled in the tokenize loop
        # (_consume_continuation), not by pre-joining lines. Joining with a
        # regex here shifts the line number of every token after the first
        # continuation — and tokens, #line directives, and kernel reports
        # all trust these numbers.
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []

    def _peek(self, offset=0) -> str:
        i = self.pos + offset
        if i < len(self.source):
            return self.source[i]
        return "\0"

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self.pos < len(self.source) and self.source[self.pos] == expected:
            self._advance()
            return True
        return False

    def _emit(self, tt: TT, value=None):
        self.tokens.append(Token(tt, value, self.line, self.col))

    def _error(self, msg):
        raise LexError(msg, self.line, self.col)

    def tokenize(self) -> list[Token]:
        while self.pos < len(self.source):
            self._skip_whitespace()
            if self.pos >= len(self.source):
                break

            ch = self._peek()

            # Newline
            if ch == "\n":
                line, col = self.line, self.col
                self._advance()
                # Only emit NEWLINE if the last token isn't already a NEWLINE or start of file
                if self.tokens and self.tokens[-1].type != TT.NEWLINE:
                    self.tokens.append(Token(TT.NEWLINE, None, line, col))
                continue

            # Comment — but '!=' is a C habit, not Ergo not-equals.
            # Lexing it as '!'-comment would silently delete the comparison
            # from an otherwise-valid program, so reject it outright.
            if ch == "!":
                if self._peek(1) == "=":
                    self._error("'!=' is not the Ergo not-equals operator — use '/=', '≠', or '.NE.'")
                self._skip_comment()
                continue

            # Line continuation: & <ws> newline — line numbers preserved
            if ch == "&":
                self._consume_continuation()
                continue

            # Unicode operators
            if ch == "\u2260":  # ≠
                line, col = self.line, self.col
                self._advance()
                self.tokens.append(Token(TT.NEQ, "≠", line, col))
                continue
            if ch == "\u2264":  # ≤
                line, col = self.line, self.col
                self._advance()
                self.tokens.append(Token(TT.LEQ, "≤", line, col))
                continue
            if ch == "\u2265":  # ≥
                line, col = self.line, self.col
                self._advance()
                self.tokens.append(Token(TT.GEQ, "≥", line, col))
                continue

            # Dotted keywords: .AND. .OR. .NOT. .TRUE. .FALSE.
            if ch == "." and self._peek(1).isalpha():
                tok = self._try_dotted_keyword()
                if tok:
                    continue
                # Fall through — could be start of a real literal like .5

            # Number literal (including those starting with .)
            if ch.isdigit() or (ch == "." and self._peek(1).isdigit()):
                self._read_number()
                continue

            # String literal
            if ch in ('"', "'"):
                self._read_string()
                continue

            # Identifier or keyword
            if ch.isalpha() or ch == "_":
                self._read_identifier()
                continue

            # Two-char operators
            if ch == "*" and self._peek(1) == "*":
                line, col = self.line, self.col
                self._advance()
                self._advance()
                self.tokens.append(Token(TT.STARSTAR, "**", line, col))
                continue
            if ch == ":" and self._peek(1) == "=":
                line, col = self.line, self.col
                self._advance()
                self._advance()
                self.tokens.append(Token(TT.ASSIGN, ":=", line, col))
                continue
            if ch == ":" and self._peek(1) == ":":
                line, col = self.line, self.col
                self._advance()
                self._advance()
                self.tokens.append(Token(TT.COLONCOLON, "::", line, col))
                continue
            if ch == "<" and self._peek(1) == "=":
                line, col = self.line, self.col
                self._advance()
                self._advance()
                self.tokens.append(Token(TT.LEQ, "<=", line, col))
                continue
            if ch == ">" and self._peek(1) == "=":
                line, col = self.line, self.col
                self._advance()
                self._advance()
                self.tokens.append(Token(TT.GEQ, ">=", line, col))
                continue
            if ch == "/" and self._peek(1) == "=":
                line, col = self.line, self.col
                self._advance()
                self._advance()
                self.tokens.append(Token(TT.NEQ, "/=", line, col))
                continue
            if ch == "=" and self._peek(1) == "=":
                # Friendly alias for = (equality). A bare '=' never legally
                # follows another '=', so this is unambiguous.
                line, col = self.line, self.col
                self._advance()
                self._advance()
                self.tokens.append(Token(TT.EQ, "==", line, col))
                continue

            # Single-char operators and delimiters
            line, col = self.line, self.col
            single = {
                "+": TT.PLUS, "-": TT.MINUS, "*": TT.STAR, "/": TT.SLASH,
                "<": TT.LT, ">": TT.GT, "=": TT.EQ,
                "(": TT.LPAREN, ")": TT.RPAREN, ",": TT.COMMA, ":": TT.COLON,
            }
            if ch in single:
                self._advance()
                self.tokens.append(Token(single[ch], ch, line, col))
                continue

            self._error(f"Unexpected character: {ch!r}")

        # Ensure final NEWLINE
        if self.tokens and self.tokens[-1].type != TT.NEWLINE:
            self.tokens.append(Token(TT.NEWLINE, None, self.line, self.col))
        self.tokens.append(Token(TT.EOF, None, self.line, self.col))
        return self.tokens

    def _skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in (" ", "\t", "\r"):
            self._advance()

    def _skip_comment(self):
        # ! to end of line
        while self.pos < len(self.source) and self.source[self.pos] != "\n":
            self._advance()

    def _consume_continuation(self):
        """Consume '&' <optional ws> newline — Fortran line continuation.

        Done during lexing (not via regex pre-pass) so every token keeps
        the line number of its physical source line. A stray '&' that is
        not followed by a newline is an error, same as before.
        """
        i = self.pos + 1
        while i < len(self.source) and self.source[i] in (" ", "\t", "\r"):
            i += 1
        if i < len(self.source) and self.source[i] == "\n":
            while self.pos <= i:
                self._advance()  # consumes '&', whitespace, and the '\n'
        else:
            self._error("Unexpected character: '&'")

    def _try_dotted_keyword(self) -> bool:
        """Try to match .AND. .OR. .NOT. .TRUE. .FALSE. and the Fortran
        dotted relational operators .EQ. .NE. .LT. .LE. .GT. .GE."""
        dotted = {
            ".AND.": TT.AND, ".OR.": TT.OR, ".NOT.": TT.NOT,
            ".TRUE.": TT.TRUE, ".FALSE.": TT.FALSE,
            ".EQ.": TT.EQ, ".NE.": TT.NEQ, ".LT.": TT.LT,
            ".LE.": TT.LEQ, ".GT.": TT.GT, ".GE.": TT.GEQ,
        }
        for kw, tt in dotted.items():
            end = self.pos + len(kw)
            if end <= len(self.source) and self.source[self.pos:end].upper() == kw:
                line, col = self.line, self.col
                for _ in range(len(kw)):
                    self._advance()
                self.tokens.append(Token(tt, kw, line, col))
                return True
        return False

    def _read_number(self):
        line, col = self.line, self.col
        start = self.pos
        is_real = False

        # Integer part
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self._advance()

        # Decimal part
        if self.pos < len(self.source) and self.source[self.pos] == ".":
            # Make sure the dot isn't the start of .AND. etc.
            next_ch = self._peek(1)
            if next_ch.isdigit() or next_ch in ("e", "E", "\0", " ", "\n", "\t", ")", ",", "+", "-", "*", "/", "<", ">", "=", "!"):
                is_real = True
                self._advance()  # consume .
                while self.pos < len(self.source) and self.source[self.pos].isdigit():
                    self._advance()
            # If next char is alpha (like .AND.), don't consume the dot

        # Exponent part
        if self.pos < len(self.source) and self.source[self.pos] in ("e", "E"):
            is_real = True
            self._advance()
            if self.pos < len(self.source) and self.source[self.pos] in ("+", "-"):
                self._advance()
            if self.pos >= len(self.source) or not self.source[self.pos].isdigit():
                self._error("Expected digit in exponent")
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                self._advance()

        text = self.source[start:self.pos]
        if is_real:
            self.tokens.append(Token(TT.REAL_LIT, float(text), line, col))
        else:
            self.tokens.append(Token(TT.INTEGER_LIT, int(text), line, col))

    def _read_string(self):
        line, col = self.line, self.col
        quote = self._advance()
        chars = []
        while self.pos < len(self.source) and self.source[self.pos] != quote:
            if self.source[self.pos] == "\n":
                self._error("Unterminated string literal")
            c = self._advance()
            if c == "\\":
                # Escape sequences (2026-08-13, A2 golden divergence fix):
                # \n \t \r \\ \' \" and octal \NNN (1-3 digits, e.g.
                # \033 = ESC for ANSI codes). Previously the backslash
                # passed through raw and the two codegen paths disagreed
                # (legacy let C's octal interpretation fire, IR escaped
                # the backslash into literal text). Unknown escapes are
                # a named error, never a silent drop.
                if self.pos >= len(self.source):
                    self._error("Unterminated string literal")
                e = self._advance()
                simple = {"n": "\n", "t": "\t", "r": "\r",
                          "\\": "\\", "'": "'", '"': '"', "0": None}
                if e in "01234567":
                    digits = e
                    while (len(digits) < 3 and
                           self.pos < len(self.source) and
                           self.source[self.pos] in "01234567"):
                        digits += self._advance()
                    chars.append(chr(int(digits, 8)))
                elif e in simple and simple[e] is not None:
                    chars.append(simple[e])
                else:
                    self._error(f"Unknown escape sequence '\\{e}' in "
                                f"string literal (supported: \\n \\t \\r "
                                f"\\\\ \\' \\\" \\NNN octal)")
            else:
                chars.append(c)
        if self.pos >= len(self.source):
            self._error("Unterminated string literal")
        self._advance()  # closing quote
        self.tokens.append(Token(TT.STRING_LIT, "".join(chars), line, col))

    def _read_identifier(self):
        line, col = self.line, self.col
        start = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == "_"):
            self._advance()
        text = self.source[start:self.pos]
        upper = text.upper()
        if upper in KEYWORDS:
            self.tokens.append(Token(KEYWORDS[upper], text, line, col))
        else:
            self.tokens.append(Token(TT.IDENT, text, line, col))
