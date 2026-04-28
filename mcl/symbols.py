"""Symbol table for MCL type checker.

Tracks variable declarations, types, shapes, allocation state, and scope.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class AllocState(Enum):
    """Allocation lifecycle state for ALLOCATABLE variables."""
    ALWAYS = auto()       # STATIC or stack — always allocated
    UNALLOCATED = auto()  # declared but not yet ALLOCATE'd
    ALLOCATED = auto()    # ALLOCATE'd
    DEALLOCATED = auto()  # DEALLOCATE'd
    UNKNOWN = auto()      # conditional paths diverge


@dataclass
class Symbol:
    name: str
    type_name: str          # "REAL", "INTEGER", "LOGICAL", etc.
    shape: tuple | None     # None=scalar, (10,20)=static array, (":",":")=allocatable
    is_static: bool = False
    is_allocatable: bool = False
    is_parameter: bool = False
    const_value: int | float | None = None  # compile-time value for PARAMETERs
    alloc_state: AllocState = AllocState.ALWAYS
    is_external: bool = False  # True if pre-seeded from another file (LSP cross-file)
    line: int = 0
    col: int = 0

    @property
    def rank(self) -> int:
        """Number of dimensions. 0 = scalar."""
        return len(self.shape) if self.shape else 0

    def resolved_shape(self) -> tuple[int, ...] | None:
        """Return shape as tuple of ints if all dimensions are compile-time constants.
        Returns None if any dimension is runtime-dependent.
        """
        if self.shape is None:
            return None
        result = []
        for d in self.shape:
            if isinstance(d, int):
                result.append(d)
            elif isinstance(d, str) and d == ":":
                return None  # allocatable, unknown at compile time
            else:
                return None  # expression, unknown at compile time
        return tuple(result)


@dataclass
class FuncSymbol:
    name: str
    return_type: str
    param_names: list[str]
    param_types: dict[str, str]
    param_shapes: dict[str, tuple | None] = field(default_factory=dict)
    is_subroutine: bool = False
    line: int = 0


class SymbolTable:
    """Scoped symbol table with nested scope support."""

    def __init__(self):
        self.scopes: list[dict[str, Symbol]] = [{}]
        self.functions: dict[str, FuncSymbol] = {}

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare(self, sym: Symbol):
        """Declare a symbol in the current scope. Returns error string if duplicate."""
        scope = self.scopes[-1]
        if sym.name in scope:
            existing = scope[sym.name]
            # Allow re-declaration if it shadows a pre-seeded cross-file symbol
            if existing.is_external:
                scope[sym.name] = sym
                return None
            return f"Variable '{sym.name}' already declared in this scope"
        scope[sym.name] = sym
        return None

    def lookup(self, name: str) -> Symbol | None:
        """Look up a symbol, searching from innermost to outermost scope."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def declare_func(self, fsym: FuncSymbol):
        self.functions[fsym.name] = fsym

    def lookup_func(self, name: str) -> FuncSymbol | None:
        return self.functions.get(name)

    @property
    def current_scope(self) -> dict[str, Symbol]:
        return self.scopes[-1]
