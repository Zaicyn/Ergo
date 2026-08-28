"""Ergo Intermediate Representation.

Typed SSA-like IR between the checked AST and backend code generation.
Each function/program is represented as a list of basic blocks forming a
control flow graph. Instructions are typed and carry source line info.

Design goals:
- Every instruction has an explicit result type (or VOID for side effects).
- Control flow is explicit: conditional branches, loop structures.
- Array indexing is 0-based at this level (1-based -> 0-based lowered here).
- Loop nests are preserved as structured constructs for fusion analysis.
- Source lines propagate for #line directives in any backend.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


# ── Precision control ────────────────────────────────────────

# Global precision for REAL type.  Set via --precision f32|f64.
# Affects C codegen (float vs double), SPIRV (OpTypeFloat 32 vs 64),
# buffer sizes, push constant layout.
_real_precision: int = 64  # bits: 32 or 64

def set_real_precision(bits: int) -> None:
    global _real_precision
    assert bits in (32, 64), f"precision must be 32 or 64, got {bits}"
    _real_precision = bits

def get_real_precision() -> int:
    return _real_precision


# ── Types ────────────────────────────────────────────────────

class IRType(Enum):
    REAL = "REAL"
    INTEGER = "INTEGER"
    INT64 = "INT64"        # INTEGER*8 — 64-bit integer (CPU only; no GPU)
    LOGICAL = "LOGICAL"
    CHARACTER = "CHARACTER"
    STRING = "STRING"          # string literal (for format strings)
    VOID = "VOID"              # no return value (subroutine, side-effect ops)

    @property
    def c_type(self) -> str:
        return {
            IRType.REAL: "float" if _real_precision == 32 else "double",
            IRType.INTEGER: "int",
            IRType.INT64: "long long",
            IRType.LOGICAL: "int",
            IRType.CHARACTER: "char",
            IRType.STRING: "const char*",
            IRType.VOID: "void",
        }[self]


# ── Storage Classes ──────────────────────────────────────────

class StorageClass(Enum):
    LOCAL = auto()        # stack variable (inside function or main)
    STATIC = auto()       # file-scope static (direct addressing)
    PARAMETER = auto()    # compile-time constant (static const)
    ALLOCATABLE = auto()  # heap-allocated (malloc/free)


# ── Variable Declaration ─────────────────────────────────────

@dataclass
class IRVar:
    """A declared variable in the IR."""
    name: str
    type: IRType
    storage: StorageClass = StorageClass.LOCAL
    shape: tuple | None = None      # None = scalar, (10, 20) = array dims
    init_value: Any = None          # initial value (for PARAMETER, inline init)
    data_init: list | None = None   # DATA statement values
    line: int = 0

    @property
    def is_array(self) -> bool:
        return self.shape is not None

    @property
    def is_scalar(self) -> bool:
        return self.shape is None

    @property
    def rank(self) -> int:
        return len(self.shape) if self.shape else 0


# ── Operands ─────────────────────────────────────────────────
# IR instructions operate on operands, not AST nodes.

@dataclass
class IRConst:
    """A literal constant value."""
    type: IRType
    value: Any  # int, float, str, bool

    def __repr__(self):
        return f"IRConst({self.type.value}, {self.value!r})"


@dataclass
class IRRef:
    """A reference to a named variable or temporary."""
    name: str
    type: IRType = IRType.VOID  # filled during IR building

    def __repr__(self):
        return f"IRRef({self.name}:{self.type.value})"


# An operand is either IRConst or IRRef
Operand = IRConst | IRRef


# ── Operations ───────────────────────────────────────────────

class Op(Enum):
    """All IR operations."""

    # Arithmetic (binary, result = same type as operands or promoted)
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    POW = "pow"
    MOD = "mod"

    # Unary
    NEG = "neg"

    # Relational (result = LOGICAL)
    LT = "lt"
    GT = "gt"
    EQ = "eq"
    NE = "ne"
    LE = "le"
    GE = "ge"

    # Logical (result = LOGICAL)
    AND = "and"
    OR = "or"
    NOT = "not"

    # Bitwise (result = INTEGER)
    ISHFT = "ishft"
    IEOR = "ieor"
    IAND = "iand"
    IOR = "ior"
    BITNOT = "bitnot"

    # Type conversion
    TO_REAL = "to_real"     # INTEGER -> REAL
    TO_INT = "to_int"       # REAL -> INTEGER
    TO_INT64 = "to_int64"   # numeric -> INTEGER*8 (explicit INT8())
    TO_CHAR = "to_char"     # INTEGER -> CHARACTER

    # Math intrinsics (result = REAL unless noted)
    SIN = "sin"
    COS = "cos"
    TAN = "tan"
    ASIN = "asin"
    ACOS = "acos"
    ATAN = "atan"
    ATAN2 = "atan2"
    EXP = "exp"
    LOG = "log"
    LOG10 = "log10"
    SQRT = "sqrt"
    ABS = "abs"
    SINH = "sinh"
    COSH = "cosh"
    TANH = "tanh"
    MAX = "max"
    MIN = "min"
    CLAMP = "clamp"
    SIGN = "sign"

    # PRNG intrinsics (splitmix64 finalize at 64-bit width; see
    # ir_codegen._emit_hash_helper for constants and statistics notes)
    HASH = "hash"           # INTEGER -> INTEGER (non-negative int32)
    RAND = "rand"           # INTEGER -> REAL (uniform [0, 1), top 53 bits)

    # Whole-array reductions (result = REAL; array names in meta["arrays"],
    # element count from the compile-time shape — no allocation)
    DOT_PRODUCT = "dot_product"
    NORM2 = "norm2"

    # Warp ring shuffle (subgroup operations)
    RING_PREV = "ring_prev"   # value from lane-1 neighbor (wraps)
    RING_NEXT = "ring_next"   # value from lane+1 neighbor (wraps)
    RING_SHIFT = "ring_shift"       # value from lane+delta neighbor (wraps)
    RING_BROADCAST = "ring_broadcast"  # broadcast one lane's value to all

    # Warp ballot / prefix-sum (nullable pattern — branchless compaction)
    WARP_BALLOT = "warp_ballot"               # ballot(pred) -> uvec4 mask
    WARP_BALLOT_COUNT = "warp_ballot_count"   # popcount(ballot) -> u32
    WARP_BALLOT_PREFIX = "warp_ballot_prefix" # exclusive prefix popcount -> u32
    WARP_BROADCAST_FIRST = "warp_broadcast_first"  # broadcast first active lane's value

    # Array operations
    LOAD = "load"           # load from array: result = array[indices]
    STORE = "store"         # store to array: array[indices] = value

    # Memory
    ALLOC = "alloc"         # allocate: ptr = malloc(shape)
    FREE = "free"           # deallocate: free(ptr)
    ZERO = "zero"           # zero entire array: memset(array, 0, sizeof)

    # Function/subroutine
    CALL = "call"           # function call with return value
    CALL_VOID = "call_void" # subroutine call (no return)

    # I/O
    PRINT = "print"         # print single value
    WRITE = "write"         # formatted write (or raw record: meta fmt=None)
    FLUSH = "flush"
    OPEN = "open"           # OPEN(unit, path, mode) — file unit (Part 10)
    CLOSE = "close"         # CLOSE(unit)
    ESF_NEXT = "esf_next"   # .esf stream: scheduled channel of next frame

    # Control flow (these are pseudo-ops — actual control flow is structural)
    RETURN = "return"
    RETURN_VOID = "return_void"
    STOP = "stop"
    HHB_FAIL = "hhb_fail"   # HHB boundary-check failure: print + exit(1)
    VERIFY = "verify"       # CPU oracle checkpoint
    SORT_BY_GEN = "sort_by_gen"  # compiler-generated sort kernels

    # Copy / move
    COPY = "copy"           # simple assignment: dst = src


# ── Instructions ─────────────────────────────────────────────

@dataclass
class IRInst:
    """A single IR instruction.

    result: name of the result variable (None for void ops like STORE, CALL_VOID)
    op:     the operation
    args:   list of operands (IRConst or IRRef)
    type:   result type
    line:   source line number for #line directives
    meta:   extra metadata (format strings, array name for LOAD/STORE, etc.)
    """
    op: Op
    args: list[Operand] = field(default_factory=list)
    result: str | None = None
    type: IRType = IRType.VOID
    line: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        r = f"{self.result} = " if self.result else ""
        a = ", ".join(str(a) for a in self.args)
        return f"  {r}{self.op.value}({a})"


# ── Structured Control Flow ──────────────────────────────────
# We keep control flow as structured blocks (not a flat CFG with gotos).
# This preserves loop nests for fusion analysis and makes C emission trivial.

@dataclass
class IRBlock:
    """A basic block: a sequence of instructions with no internal branches."""
    label: str
    insts: list[IRInst] = field(default_factory=list)
    line: int = 0


@dataclass
class IRIf:
    """Structured if/elseif/else."""
    condition: Operand
    then_body: list  # list of IRBlock | IRIf | IRLoop | IRSelect
    else_body: list | None = None
    line: int = 0


@dataclass
class IRLoop:
    """Structured DO loop — preserved for fusion analysis.

    var:   loop variable name
    start, end, step: loop bounds (Operand)
    body:  list of structured IR items
    """
    var: str
    start: Operand
    end: Operand
    step: Operand
    body: list  # list of IRBlock | IRIf | IRLoop | IRSelect
    line: int = 0
    # True when produced by nested-loop linearization (ir_gpu): write
    # injectivity over the collapsed space was proven at acceptance time
    # (writes exactly at (I,J)), so extraction must skip the affine
    # store-index classification — the flattened store index is a
    # computed column-major linear form (MOD/DIV from the I/J recovery)
    # that the affine extractor cannot read.
    linearized: bool = False


@dataclass
class IRSelect:
    """Structured SELECT CASE."""
    expr: Operand
    cases: list  # list of (Operand | None, body_list) — None = DEFAULT
    line: int = 0


@dataclass
class IRWhileLoop:
    """Structured DO WHILE loop — condition-controlled iteration."""
    condition: Operand
    cond_block: 'IRBlock'  # block that computes the condition
    body: list  # list of IRBlock | IRIf | IRLoop | IRSelect | IRWhileLoop
    line: int = 0


# A structured IR item is one of these:
IRItem = IRBlock | IRIf | IRLoop | IRSelect | IRWhileLoop


# ── Function ────────────────────────────────────────────────

@dataclass
class IRFunc:
    """A function or subroutine in IR form."""
    name: str
    params: list[IRVar]         # parameter declarations
    locals: list[IRVar]         # local variable declarations
    body: list[IRItem]          # structured body
    return_type: IRType = IRType.VOID  # VOID for subroutines
    is_subroutine: bool = False
    line: int = 0


# ── Module (top-level program) ───────────────────────────────

@dataclass
class IRModule:
    """Complete IR for one compilation unit.

    globals:   file-scope variables (STATIC, PARAMETER)
    functions: function/subroutine definitions
    main_body: main program body (structured IR items)
    data_inits: DATA statement initializers
    source_file: original source path for #line
    """
    globals: list[IRVar] = field(default_factory=list)
    functions: list[IRFunc] = field(default_factory=list)
    main_body: list[IRItem] = field(default_factory=list)
    main_locals: list[IRVar] = field(default_factory=list)
    data_inits: dict[str, list] = field(default_factory=dict)
    source_file: str | None = None


# ── Debug / dump ─────────────────────────────────────────────

def dump_module(mod: IRModule) -> str:
    """Dump IR module as human-readable text."""
    lines = []
    lines.append(f"# IR Module (source: {mod.source_file})")
    lines.append("")

    if mod.globals:
        lines.append("# Globals")
        for g in mod.globals:
            shape_str = f"({','.join(str(d) for d in g.shape)})" if g.shape else ""
            init_str = f" = {g.init_value}" if g.init_value is not None else ""
            lines.append(f"  {g.storage.name} {g.type.value} {g.name}{shape_str}{init_str}")
        lines.append("")

    for fn in mod.functions:
        params = ", ".join(f"{p.type.value} {p.name}" for p in fn.params)
        ret = fn.return_type.value
        kind = "SUBROUTINE" if fn.is_subroutine else f"{ret} FUNCTION"
        lines.append(f"# {kind} {fn.name}({params})")
        for v in fn.locals:
            shape_str = f"({','.join(str(d) for d in v.shape)})" if v.shape else ""
            lines.append(f"  LOCAL {v.type.value} {v.name}{shape_str}")
        _dump_body(fn.body, lines, indent=1)
        lines.append("")

    if mod.main_body:
        lines.append("# MAIN")
        for v in mod.main_locals:
            shape_str = f"({','.join(str(d) for d in v.shape)})" if v.shape else ""
            init_str = f" = {v.init_value}" if v.init_value is not None else ""
            lines.append(f"  LOCAL {v.type.value} {v.name}{shape_str}{init_str}")
        _dump_body(mod.main_body, lines, indent=1)

    return "\n".join(lines) + "\n"


def _dump_body(items: list, lines: list[str], indent: int):
    pad = "  " * indent
    for item in items:
        if isinstance(item, IRBlock):
            if item.insts:
                lines.append(f"{pad}# block {item.label}:")
                for inst in item.insts:
                    lines.append(f"{pad}  {inst}")
        elif isinstance(item, IRIf):
            lines.append(f"{pad}IF {item.condition}:")
            _dump_body(item.then_body, lines, indent + 1)
            if item.else_body:
                lines.append(f"{pad}ELSE:")
                _dump_body(item.else_body, lines, indent + 1)
        elif isinstance(item, IRLoop):
            lines.append(
                f"{pad}DO {item.var} = {item.start}, {item.end}, {item.step}:")
            _dump_body(item.body, lines, indent + 1)
        elif isinstance(item, IRWhileLoop):
            lines.append(f"{pad}DO WHILE {item.condition}:")
            _dump_body(item.body, lines, indent + 1)
        elif isinstance(item, IRSelect):
            lines.append(f"{pad}SELECT {item.expr}:")
            for val, body in item.cases:
                label = "DEFAULT" if val is None else str(val)
                lines.append(f"{pad}  CASE {label}:")
                _dump_body(body, lines, indent + 2)
