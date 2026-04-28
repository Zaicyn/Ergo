"""Ergo LSP server — parse, check, hover, GPU analysis.

Launch:  python -m mcl.lsp_server
Transport: stdio (extension.js spawns this as a child process)

Session 3: hover provider + PERF hints (FLOW classification, extraction failures).
"""

import sys
import os
import logging
from pathlib import Path

from pygls.lsp.server import LanguageServer
import lsprotocol.types as lsp

from .lexer import Lexer
from .parser import Parser
from .checker import Checker, Diagnostic, INTRINSIC_RETURNS
from .tokens import Token, TT
from .symbols import Symbol, FuncSymbol
from .errors import LexError, ParseError, MCLError

logging.basicConfig(filename="/tmp/ergo-lsp.log", level=logging.DEBUG)
log = logging.getLogger("ergo-lsp")

server = LanguageServer(
    "ergo-lsp", "v0.1",
    text_document_sync_kind=lsp.TextDocumentSyncKind.Full,
)


# ── per-document analysis cache ───────────────────────────────

class DocState:
    """Cached analysis state for a single document."""
    __slots__ = ("tokens", "tree", "checker", "source_lines")

    def __init__(self):
        self.tokens: list[Token] = []
        self.tree = None
        self.checker: Checker | None = None
        self.source_lines: list[str] = []


_doc_cache: dict[str, DocState] = {}


# ── project-wide symbol discovery ─────────────────────────────

def _discover_project_symbols(root: str) -> tuple[list[Symbol], list[FuncSymbol]]:
    """Scan all .ergo files for PARAMETER/STATIC declarations and subroutine signatures."""
    from . import ast_nodes as ast

    symbols = []
    func_symbols = []
    root_path = Path(root)
    if not root_path.is_dir():
        return symbols, func_symbols

    for ergo_file in root_path.rglob("*.ergo"):
        if "archive" in ergo_file.parts:
            continue
        try:
            source = ergo_file.read_text()
            tokens = Lexer(source).tokenize()
            tree = Parser(tokens).parse()
        except (MCLError, Exception):
            continue

        for unit in tree.units:
            _collect_declarations(unit, symbols)
            if hasattr(unit, 'declarations'):
                for decl in unit.declarations:
                    _collect_declarations(decl, symbols)
            if isinstance(unit, ast.SubroutineDef):
                param_types = {}
                param_shapes = {}
                for decl in unit.declarations:
                    for v in decl.variables:
                        param_types[v.name] = decl.type_name
                        if v.shape:
                            param_shapes[v.name] = v.shape
                func_symbols.append(FuncSymbol(
                    name=unit.name, return_type="VOID",
                    param_names=unit.params, param_types=param_types,
                    param_shapes=param_shapes, is_subroutine=True,
                ))
            elif isinstance(unit, ast.FunctionDef):
                param_types = {}
                param_shapes = {}
                for decl in unit.declarations:
                    for v in decl.variables:
                        param_types[v.name] = decl.type_name
                        if v.shape:
                            param_shapes[v.name] = v.shape
                func_symbols.append(FuncSymbol(
                    name=unit.name, return_type=unit.return_type or "REAL",
                    param_names=unit.params, param_types=param_types,
                    param_shapes=param_shapes,
                ))

    seen = set()
    unique = [s for s in symbols if not (s.name in seen or seen.add(s.name))]
    seen_f = set()
    unique_f = [f for f in func_symbols if not (f.name in seen_f or seen_f.add(f.name))]
    return unique, unique_f


def _collect_declarations(node, symbols: list):
    """Extract PARAMETER and STATIC symbols from a Declaration node."""
    from . import ast_nodes as ast
    if not isinstance(node, ast.Declaration):
        return
    if not (node.parameter or node.static):
        return
    for v in node.variables:
        symbols.append(Symbol(
            name=v.name, type_name=node.type_name, shape=v.shape,
            is_parameter=node.parameter, is_static=node.static,
            is_external=True,
        ))


_project_symbols: list[Symbol] | None = None
_project_funcs: list[FuncSymbol] | None = None


def _get_project_symbols() -> tuple[list[Symbol], list[FuncSymbol]]:
    global _project_symbols, _project_funcs
    if _project_symbols is not None:
        return _project_symbols, _project_funcs

    root = os.getcwd()
    try:
        folders = server.workspace.folders
        if folders:
            from urllib.parse import urlparse
            uri = list(folders.values())[0].uri if isinstance(folders, dict) else folders[0].uri
            root = urlparse(uri).path
    except Exception:
        pass

    log.info("Discovering project symbols from %s", root)
    _project_symbols, _project_funcs = _discover_project_symbols(root)
    log.info("Found %d symbols, %d functions",
             len(_project_symbols), len(_project_funcs))
    return _project_symbols, _project_funcs


# ── analysis pipeline ─────────────────────────────────────────

def analyze(source: str, uri: str = "") -> list[lsp.Diagnostic]:
    """Run lexer → parser → checker → GPU analysis. Cache state for hover."""
    diagnostics = []
    state = DocState()
    state.source_lines = source.splitlines()

    # Lex
    try:
        state.tokens = Lexer(source).tokenize()
    except LexError as e:
        diagnostics.append(_make_diagnostic(
            e.line or 1, e.col or 1, e.message, lsp.DiagnosticSeverity.Error))
        _doc_cache[uri] = state
        return diagnostics

    # Parse
    try:
        state.tree = Parser(state.tokens).parse()
    except ParseError as e:
        diagnostics.append(_make_diagnostic(
            e.line or 1, e.col or 1, e.message, lsp.DiagnosticSeverity.Error))
        _doc_cache[uri] = state
        return diagnostics

    # Check
    checker = Checker()
    proj_syms, proj_funcs = _get_project_symbols()
    for sym in proj_syms:
        checker.symtab.declare(sym)
    for fs in proj_funcs:
        checker.symtab.declare_func(fs)
    checker.check(state.tree)
    state.checker = checker
    _doc_cache[uri] = state

    for d in checker.diagnostics:
        severity = (lsp.DiagnosticSeverity.Error if d.level == "error"
                    else lsp.DiagnosticSeverity.Warning)
        diagnostics.append(_make_diagnostic(d.line, d.col, d.msg, severity))

    # GPU analysis (PERF hints) — best effort, never crash
    try:
        diagnostics.extend(_gpu_diagnostics(state))
    except Exception:
        log.exception("GPU analysis failed for %s", uri)

    return diagnostics


def _gpu_diagnostics(state: DocState) -> list[lsp.Diagnostic]:
    """Run IR build + GPU kernel extraction, return PERF hint diagnostics."""
    from .ir_builder import IRBuilder
    from .ir_gpu import extract_kernels
    from .ir_inline import inline_subroutines
    from .ir_affine import LoopDependence

    hints = []

    ir = IRBuilder().build(state.tree)
    inline_subroutines(ir)
    plan = extract_kernels(ir, allow_split=True)

    # Extracted kernels — show classification
    for k in plan.kernels:
        dep = k.dependence.value  # "INJECTIVE", "SCATTER", etc.
        tag = "SPLIT " if k.is_partial else ""
        n_arrays = len(k.arrays_read | k.arrays_written)
        msg = f"{tag}{dep} — GPU extracted ({n_arrays} arrays)"
        if k.dependence == LoopDependence.SCATTER:
            msg += f" ⚠ atomic contention on {sorted(k.atomic_arrays)}"
        hints.append(_make_diagnostic(
            k.source_line, 1, msg, lsp.DiagnosticSeverity.Hint))

    # Rejected loops — show reason
    for line, reason in plan.rejections:
        hints.append(_make_diagnostic(
            line, 1, f"CPU only: {reason}", lsp.DiagnosticSeverity.Hint))

    # Extraction warnings
    for line, msg in plan.warnings:
        hints.append(_make_diagnostic(
            line, 1, msg, lsp.DiagnosticSeverity.Hint))

    return hints


# ── hover provider ────────────────────────────────────────────

# Intrinsic documentation for hover
_INTRINSIC_DOCS = {
    "SIN": "SIN(x: REAL) → REAL — Sine in radians",
    "COS": "COS(x: REAL) → REAL — Cosine in radians",
    "TAN": "TAN(x: REAL) → REAL — Tangent in radians",
    "ASIN": "ASIN(x: REAL) → REAL — Arcsine, result in [-π/2, π/2]",
    "ACOS": "ACOS(x: REAL) → REAL — Arccosine, result in [0, π]",
    "ATAN": "ATAN(x: REAL) → REAL — Arctangent, result in [-π/2, π/2]",
    "ATAN2": "ATAN2(y: REAL, x: REAL) → REAL — Two-argument arctangent",
    "EXP": "EXP(x: REAL) → REAL — e^x",
    "LOG": "LOG(x: REAL) → REAL — Natural logarithm",
    "LOG10": "LOG10(x: REAL) → REAL — Base-10 logarithm",
    "SQRT": "SQRT(x: REAL) → REAL — Square root (x ≥ 0)",
    "ABS": "ABS(x) → same type — Absolute value (INTEGER, REAL, or COMPLEX)",
    "SIGN": "SIGN(x, y) → same type — |x| with sign of y",
    "MOD": "MOD(a, b) → same type — Remainder, sign of dividend",
    "MAX": "MAX(a, b, ...) → same type — Maximum of arguments (variadic)",
    "MIN": "MIN(a, b, ...) → same type — Minimum of arguments (variadic)",
    "CLAMP": "CLAMP(x, lo, hi) → same type — Branchless clamp to [lo, hi]",
    "SINH": "SINH(x: REAL) → REAL — Hyperbolic sine",
    "COSH": "COSH(x: REAL) → REAL — Hyperbolic cosine",
    "TANH": "TANH(x: REAL) → REAL — Hyperbolic tangent",
    "IAND": "IAND(a: INTEGER, b: INTEGER) → INTEGER — Bitwise AND",
    "IOR": "IOR(a: INTEGER, b: INTEGER) → INTEGER — Bitwise OR",
    "IEOR": "IEOR(a: INTEGER, b: INTEGER) → INTEGER — Bitwise XOR",
    "ISHFT": "ISHFT(i: INTEGER, shift: INTEGER) → INTEGER — Bit shift (left if positive)",
    "NOT": "NOT(i: INTEGER) → INTEGER — Bitwise complement",
    "SUM": "SUM(a(:)) → scalar — Sum all elements",
    "PRODUCT": "PRODUCT(a(:)) → scalar — Product of all elements",
    "DOT_PRODUCT": "DOT_PRODUCT(a(:), b(:)) → REAL — Dot product: Σ a[i]*b[i]",
    "NORM2": "NORM2(a(:)) → REAL — Euclidean norm: √(Σ a[i]²)",
    "MAXVAL": "MAXVAL(a(:)) → scalar — Maximum element",
    "MINVAL": "MINVAL(a(:)) → scalar — Minimum element",
    "MATMUL": "MATMUL(A(m,n), B(n,p)) → (m,p) — Matrix multiply (caller-allocated output)",
    "TRANSPOSE": "TRANSPOSE(A(m,n)) → (n,m) — Matrix transpose (caller-allocated output)",
    "RESHAPE": "RESHAPE(A, shape) → reshaped — Reshape array (total elements must match)",
    "SIZE": "SIZE(A) → INTEGER — Total number of elements",
    "RANK": "RANK(A) → INTEGER — Number of dimensions",
    "SHAPE": "SHAPE(A) → INTEGER(:) — Array of dimension sizes (caller-allocated)",
    "ZERO": "CALL ZERO(A) — Zero all elements (memset). Statement-only.",
    "REAL": "REAL(x) → REAL — Convert INTEGER to REAL, or extract real part of COMPLEX",
    "INT": "INT(x: REAL) → INTEGER — Truncate to integer",
    "CMPLX": "CMPLX(re: REAL, im: REAL) → COMPLEX — Construct complex number",
    "AIMAG": "AIMAG(z: COMPLEX) → REAL — Extract imaginary part",
    "CONJG": "CONJG(z: COMPLEX) → COMPLEX — Complex conjugate",
    "LEN": "LEN(s: CHARACTER) → INTEGER — String length",
    "INDEX": "INDEX(s, substr) → INTEGER — Position of first occurrence, or 0",
    "CONCAT": "CONCAT(s1, s2) → CHARACTER — Concatenate (caller declares result length)",
    "RING_PREV": "RING_PREV(x) — Warp shuffle: value from GEN-1 neighbor (lane & 31)",
    "RING_NEXT": "RING_NEXT(x) — Warp shuffle: value from GEN+1 neighbor (lane & 31)",
    "RING_SHIFT": "RING_SHIFT(x, d) — Warp shuffle: value from lane+d neighbor",
    "RING_BROADCAST": "RING_BROADCAST(x, lane) — Warp shuffle: broadcast from lane",
}

# Type sizes in bytes (for memory footprint calculation)
_TYPE_BYTES = {"REAL": 8, "INTEGER": 4, "LOGICAL": 4, "COMPLEX": 16, "CHARACTER": 1}


def _find_token_at(tokens: list[Token], line_1: int, col_1: int) -> Token | None:
    """Find the token at a 1-based (line, col) position.

    Returns the token whose span covers the position, preferring identifiers
    and keywords over operators and delimiters.
    """
    best = None
    for tok in tokens:
        if tok.type in (TT.NEWLINE, TT.EOF):
            continue
        if tok.line == line_1:
            # Estimate token end column from value
            tok_len = len(str(tok.value)) if tok.value is not None else 1
            if tok.col <= col_1 < tok.col + tok_len:
                return tok
            # Also accept if we're just past the token (cursor after last char)
            if tok.col <= col_1 <= tok.col + tok_len:
                best = tok
    return best


def _hover_for_token(tok: Token, state: DocState) -> str | None:
    """Generate hover markdown for a token, using cached analysis state."""
    if tok is None:
        return None

    name = (tok.value if isinstance(tok.value, str) else "").upper()

    # Intrinsic functions
    if name in _INTRINSIC_DOCS:
        return f"```\n{_INTRINSIC_DOCS[name]}\n```"

    # Identifier — look up in symbol table
    if tok.type == TT.IDENT and state.checker:
        sym = state.checker.symtab.lookup(tok.value)
        if sym:
            return _format_symbol_hover(sym, state)

        # Check function table
        fsym = state.checker.symtab.lookup_func(tok.value)
        if fsym:
            return _format_func_hover(fsym)

    # Keywords — show brief info
    if tok.type == TT.KW_SORT_BY_GEN:
        return ("```\nSORT_BY_GEN array_list\n```\n"
                "Sort particles by GEN field for ring-adjacent warp placement.\n"
                "Generates histogram + prefix-scan + scatter kernels.")
    if tok.type == TT.KW_VERIFY:
        return ("```\nVERIFY arrays ORACLE n EVERY m TOL t\n```\n"
                "CPU oracle checkpoint — downloads GPU arrays, compares against\n"
                "CPU reference computation for correctness verification.")

    return None


def _format_symbol_hover(sym: Symbol, state: DocState) -> str:
    """Format hover info for a variable/constant symbol."""
    parts = []

    # Type and storage class
    qualifiers = []
    if sym.is_static:
        qualifiers.append("STATIC")
    if sym.is_parameter:
        qualifiers.append("PARAMETER")
    if sym.is_allocatable:
        qualifiers.append("ALLOCATABLE")
    qual_str = " ".join(qualifiers)
    if qual_str:
        qual_str += " "

    if sym.shape:
        shape_str = ", ".join(str(d) for d in sym.shape)
        parts.append(f"```\n{qual_str}{sym.type_name} :: {sym.name}({shape_str})\n```")
    else:
        parts.append(f"```\n{qual_str}{sym.type_name} :: {sym.name}\n```")

    # PARAMETER — show resolved value
    if sym.is_parameter and sym.const_value is not None:
        parts.append(f"**Value:** `{sym.const_value}`")

    # Array — show memory footprint
    if sym.shape:
        resolved = sym.resolved_shape()
        if resolved:
            n_elements = 1
            for d in resolved:
                n_elements *= d
            elem_bytes = _TYPE_BYTES.get(sym.type_name, 8)
            total_bytes = n_elements * elem_bytes
            if total_bytes >= 1024 * 1024:
                size_str = f"{total_bytes / (1024*1024):.1f} MB"
            elif total_bytes >= 1024:
                size_str = f"{total_bytes / 1024:.1f} KB"
            else:
                size_str = f"{total_bytes} bytes"
            parts.append(f"**Memory:** {n_elements:,} elements, {size_str}")

    return "\n\n".join(parts)


def _format_func_hover(fsym: FuncSymbol) -> str:
    """Format hover info for a subroutine/function."""
    kind = "SUBROUTINE" if fsym.is_subroutine else f"{fsym.return_type} FUNCTION"
    params = []
    for p in fsym.param_names:
        ptype = fsym.param_types.get(p, "?")
        pshape = fsym.param_shapes.get(p)
        if pshape:
            shape_str = ", ".join(str(d) for d in pshape)
            params.append(f"{ptype} :: {p}({shape_str})")
        else:
            params.append(f"{ptype} :: {p}")
    param_str = ", ".join(params) if params else ""
    return f"```\n{kind} {fsym.name}({param_str})\n```"


# ── diagnostic helpers ────────────────────────────────────────

def _make_diagnostic(
    line: int, col: int, msg: str, severity: lsp.DiagnosticSeverity,
) -> lsp.Diagnostic:
    ln = max(0, (line or 1) - 1)
    co = max(0, (col or 1) - 1)
    return lsp.Diagnostic(
        range=lsp.Range(
            start=lsp.Position(line=ln, character=co),
            end=lsp.Position(line=ln, character=co + 80),
        ),
        message=msg,
        severity=severity,
        source="ergo",
    )


# ── LSP event handlers ────────────────────────────────────────

@server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
def did_open(params: lsp.DidOpenTextDocumentParams):
    _publish(params.text_document.uri, params.text_document.text)


@server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
def did_change(params: lsp.DidChangeTextDocumentParams):
    text = params.content_changes[0].text
    _publish(params.text_document.uri, text)


@server.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
def did_save(params: lsp.DidSaveTextDocumentParams):
    doc = server.workspace.get_text_document(params.text_document.uri)
    _publish(params.text_document.uri, doc.source)


@server.feature(lsp.TEXT_DOCUMENT_HOVER)
def hover(params: lsp.HoverParams) -> lsp.Hover | None:
    uri = params.text_document.uri
    state = _doc_cache.get(uri)
    if not state or not state.tokens:
        return None

    # LSP position is 0-based; tokens are 1-based
    line_1 = params.position.line + 1
    col_1 = params.position.character + 1

    tok = _find_token_at(state.tokens, line_1, col_1)
    if tok is None:
        return None

    content = _hover_for_token(tok, state)
    if content is None:
        return None

    return lsp.Hover(
        contents=lsp.MarkupContent(
            kind=lsp.MarkupKind.Markdown,
            value=content,
        ),
    )


def _publish(uri: str, source: str):
    try:
        diags = analyze(source, uri)
    except Exception:
        log.exception("Analysis failed for %s", uri)
        diags = []
    server.text_document_publish_diagnostics(
        lsp.PublishDiagnosticsParams(uri=uri, diagnostics=diags)
    )


# ── entry point ────────────────────────────────────────────────

def main():
    log.info("Ergo LSP server starting (stdio)")
    server.start_io()


if __name__ == "__main__":
    main()
