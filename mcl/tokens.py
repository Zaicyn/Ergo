from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TT(Enum):
    # Arithmetic
    STARSTAR = auto()
    STAR = auto()
    SLASH = auto()
    PLUS = auto()
    MINUS = auto()

    # Relational
    LT = auto()
    GT = auto()
    EQ = auto()
    NEQ = auto()
    LEQ = auto()
    GEQ = auto()

    # Logical
    AND = auto()
    OR = auto()
    NOT = auto()

    # Assignment
    ASSIGN = auto()  # :=

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    COLONCOLON = auto()  # ::
    COLON = auto()

    # Literals
    INTEGER_LIT = auto()
    REAL_LIT = auto()
    STRING_LIT = auto()
    TRUE = auto()
    FALSE = auto()

    # Identifier
    IDENT = auto()

    # Keywords
    KW_IF = auto()
    KW_THEN = auto()
    KW_ELSE = auto()
    KW_ENDIF = auto()
    KW_DO = auto()
    KW_ENDDO = auto()
    KW_FUNCTION = auto()
    KW_SUBROUTINE = auto()
    KW_END = auto()
    KW_RETURN = auto()
    KW_CALL = auto()
    KW_ALLOCATE = auto()
    KW_DEALLOCATE = auto()
    KW_PRINT = auto()
    KW_IMPLICIT = auto()
    KW_NONE = auto()

    # Type keywords
    KW_REAL = auto()
    KW_INTEGER = auto()
    KW_COMPLEX = auto()
    KW_LOGICAL = auto()
    KW_CHARACTER = auto()
    KW_ALLOCATABLE = auto()
    KW_STATIC = auto()
    KW_DATA = auto()
    KW_ELSEIF = auto()
    KW_CYCLE = auto()
    KW_STOP = auto()
    KW_WRITE = auto()
    KW_FLUSH = auto()
    KW_PARAMETER = auto()
    KW_SELECT = auto()
    KW_CASE = auto()
    KW_DEFAULT = auto()
    KW_ENDSELECT = auto()
    KW_VERIFY = auto()

    # Structure
    NEWLINE = auto()
    EOF = auto()


KEYWORDS = {
    "IF": TT.KW_IF,
    "THEN": TT.KW_THEN,
    "ELSE": TT.KW_ELSE,
    "ENDIF": TT.KW_ENDIF,
    "DO": TT.KW_DO,
    "ENDDO": TT.KW_ENDDO,
    "FUNCTION": TT.KW_FUNCTION,
    "SUBROUTINE": TT.KW_SUBROUTINE,
    "END": TT.KW_END,
    "RETURN": TT.KW_RETURN,
    "CALL": TT.KW_CALL,
    "ALLOCATE": TT.KW_ALLOCATE,
    "DEALLOCATE": TT.KW_DEALLOCATE,
    "PRINT": TT.KW_PRINT,
    "IMPLICIT": TT.KW_IMPLICIT,
    "NONE": TT.KW_NONE,
    "REAL": TT.KW_REAL,
    "INTEGER": TT.KW_INTEGER,
    "COMPLEX": TT.KW_COMPLEX,
    "LOGICAL": TT.KW_LOGICAL,
    "CHARACTER": TT.KW_CHARACTER,
    "ALLOCATABLE": TT.KW_ALLOCATABLE,
    "STATIC": TT.KW_STATIC,
    "DATA": TT.KW_DATA,
    "ELSEIF": TT.KW_ELSEIF,
    "CYCLE": TT.KW_CYCLE,
    "STOP": TT.KW_STOP,
    "WRITE": TT.KW_WRITE,
    "FLUSH": TT.KW_FLUSH,
    "PARAMETER": TT.KW_PARAMETER,
    "SELECT": TT.KW_SELECT,
    "CASE": TT.KW_CASE,
    "DEFAULT": TT.KW_DEFAULT,
    "ENDSELECT": TT.KW_ENDSELECT,
    "VERIFY": TT.KW_VERIFY,
}


@dataclass
class Token:
    type: TT
    value: Any
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.col})"
