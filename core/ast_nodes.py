from dataclasses import dataclass, field
from typing import Any


@dataclass
class Program:
    units: list  # top-level statements, function defs, subroutine defs


@dataclass
class FunctionDef:
    name: str
    params: list[str]
    declarations: list
    body: list
    return_type: str = None


@dataclass
class SubroutineDef:
    name: str
    params: list[str]
    declarations: list
    body: list


@dataclass
class Declaration:
    type_name: str  # "REAL", "INTEGER", "LOGICAL", etc.
    variables: list  # list of VarDecl
    allocatable: bool = False
    static: bool = False  # STATIC keyword — file-scope, direct addressing
    parameter: bool = False  # PARAMETER keyword — compile-time constant
    line: int = 0


@dataclass
class VarDecl:
    name: str
    shape: tuple = None  # None=scalar, (10,20)=static array, (':',':')=allocatable
    init_value: Any = None  # initial value for DATA-style init


@dataclass
class DataStmt:
    """DATA name / values / — static initialization."""
    name: str
    values: list  # list of Literal values


@dataclass
class AssignStmt:
    target: Any  # Variable or ArraySubscript
    value: Any   # expression
    line: int = 0


@dataclass
class IfStmt:
    condition: Any
    then_body: list
    else_body: list = None
    line: int = 0


@dataclass
class DoLoop:
    var: str
    start: Any
    end: Any
    step: Any
    body: list
    line: int = 0


@dataclass
class DoWhileStmt:
    condition: Any
    body: list
    line: int = 0


@dataclass
class PrintStmt:
    value: Any
    line: int = 0


@dataclass
class ReturnStmt:
    value: Any = None
    line: int = 0


@dataclass
class AllocateStmt:
    name: str
    shape: list  # list of expressions
    line: int = 0


@dataclass
class DeallocateStmt:
    name: str
    line: int = 0


@dataclass
class CallStmt:
    name: str
    args: list
    line: int = 0


@dataclass
class ImplicitNone:
    pass


@dataclass
class CycleStmt:
    """CYCLE — skip to next DO loop iteration (like C 'continue')."""
    pass


@dataclass
class ExitStmt:
    """EXIT — leave the enclosing DO loop entirely (like C 'break')."""
    pass


@dataclass
class StopStmt:
    """STOP — terminate program."""
    pass


@dataclass
class VerifyStmt:
    """VERIFY arrays ORACLE n EVERY m TOL t — CPU oracle checkpoint.
    arrays: list of array names to verify
    oracle_size: number of elements to check (first N)
    every: check every N frames (default 1)
    tolerance: relative error threshold (default 1e-6)
    """
    arrays: list
    oracle_size: int
    every: int = 1
    tolerance: float = 1e-6
    net_host: str = None  # NET "host:port" — send verify/census over UDP
    net_gpu_id: int = 0  # GPU n — client identity for multi-GPU oracle
    line: int = 0


@dataclass
class SortByGenStmt:
    """SORT_BY_GEN arr1, arr2, ... — sort particles by GEN field.
    arrays: list of array names permuted together.
    Compiler generates histogram, scan, and scatter kernels.
    """
    arrays: list
    line: int = 0


@dataclass
class WriteStmt:
    """WRITE(unit, fmt) args — formatted output.
    unit: 0=stderr, *=stdout
    fmt: format string
    args: list of expressions
    advance: True=with newline, False=no newline
    """
    unit: str    # "*" or "0" or "6"
    fmt: str     # format string (C printf-style after translation)
    args: list
    advance: bool = True
    line: int = 0


@dataclass
class FlushStmt:
    """FLUSH — flush stdout."""
    pass


@dataclass
class SelectCaseStmt:
    """SELECT CASE (expr) / CASE val / ... / CASE DEFAULT / ... / ENDSELECT"""
    expr: Any
    cases: list      # list of (value_or_None, body) — None = DEFAULT
    # Each case: (Literal or list of Literals for ranges, list of stmts)
    line: int = 0


# Expressions

@dataclass
class BinaryOp:
    op: str
    left: Any
    right: Any


@dataclass
class UnaryOp:
    op: str
    operand: Any


@dataclass
class Variable:
    name: str


@dataclass
class Literal:
    type: str   # "INTEGER", "REAL", "STRING", "LOGICAL"
    value: Any


@dataclass
class CallOrSubscript:
    """Function call or array subscript — ambiguous at parse time."""
    name: str
    args: list
