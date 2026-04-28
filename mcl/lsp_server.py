"""Ergo LSP server — parse on open/change, report diagnostics inline.

Launch:  python -m mcl.lsp_server
Transport: stdio (extension.js spawns this as a child process)

Session 2: parse errors + checker errors/warnings as diagnostics.
GPU analysis (PERF hints) added in Session 3.
"""

import sys
import os
import logging
from pathlib import Path

from pygls.lsp.server import LanguageServer
import lsprotocol.types as lsp

from .lexer import Lexer
from .parser import Parser
from .checker import Checker, Diagnostic
from .symbols import Symbol, FuncSymbol
from .errors import LexError, ParseError, MCLError

logging.basicConfig(filename="/tmp/ergo-lsp.log", level=logging.DEBUG)
log = logging.getLogger("ergo-lsp")

server = LanguageServer(
    "ergo-lsp", "v0.1",
    text_document_sync_kind=lsp.TextDocumentSyncKind.Full,
)


# ── project-wide symbol discovery ─────────────────────────────

def _discover_project_symbols(root: str) -> tuple[list[Symbol], list[FuncSymbol]]:
    """Scan all .ergo files for PARAMETER/STATIC declarations and subroutine signatures.

    Returns (symbols, func_symbols) to pre-seed into the checker so cross-file
    references don't produce undeclared-variable errors in single-file analysis.
    """
    from . import ast_nodes as ast

    symbols = []
    func_symbols = []
    root_path = Path(root)
    if not root_path.is_dir():
        return symbols, func_symbols

    for mcl_file in root_path.rglob("*.ergo"):
        if "archive" in mcl_file.parts:
            continue
        try:
            source = mcl_file.read_text()
            tokens = Lexer(source).tokenize()
            tree = Parser(tokens).parse()
        except (MCLError, Exception):
            continue

        for unit in tree.units:
            _collect_declarations(unit, symbols)
            if hasattr(unit, 'declarations'):
                for decl in unit.declarations:
                    _collect_declarations(decl, symbols)
            # Collect subroutine/function signatures
            if isinstance(unit, ast.SubroutineDef):
                param_types = {}
                param_shapes = {}
                for decl in unit.declarations:
                    for v in decl.variables:
                        param_types[v.name] = decl.type_name
                        if v.shape:
                            param_shapes[v.name] = v.shape
                func_symbols.append(FuncSymbol(
                    name=unit.name,
                    return_type="VOID",
                    param_names=unit.params,
                    param_types=param_types,
                    param_shapes=param_shapes,
                    is_subroutine=True,
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
                    name=unit.name,
                    return_type=unit.return_type or "REAL",
                    param_names=unit.params,
                    param_types=param_types,
                    param_shapes=param_shapes,
                ))

    # Deduplicate by name (first definition wins)
    seen = set()
    unique = []
    for sym in symbols:
        if sym.name not in seen:
            seen.add(sym.name)
            unique.append(sym)

    seen_funcs = set()
    unique_funcs = []
    for fs in func_symbols:
        if fs.name not in seen_funcs:
            seen_funcs.add(fs.name)
            unique_funcs.append(fs)

    return unique, unique_funcs


def _collect_declarations(node, symbols: list):
    """Extract PARAMETER and STATIC symbols from a Declaration node."""
    from . import ast_nodes as ast
    if not isinstance(node, ast.Declaration):
        return
    if not (node.parameter or node.static):
        return
    for v in node.variables:
        symbols.append(Symbol(
            name=v.name,
            type_name=node.type_name,
            shape=v.shape,
            is_parameter=node.parameter,
            is_static=node.static,
            is_external=True,
        ))


# Cache project symbols (computed once on first analysis)
_project_symbols: list[Symbol] | None = None
_project_funcs: list[FuncSymbol] | None = None


def _get_project_symbols() -> tuple[list[Symbol], list[FuncSymbol]]:
    """Get cached project-wide symbols, discovering on first call."""
    global _project_symbols, _project_funcs
    if _project_symbols is not None:
        return _project_symbols, _project_funcs

    # Determine project root from server workspace or cwd
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


# ── diagnostics ────────────────────────────────────────────────

def analyze(source: str, uri: str = "") -> list[lsp.Diagnostic]:
    """Run lexer → parser → checker on source text, return LSP diagnostics."""
    diagnostics = []

    # Lex
    try:
        tokens = Lexer(source).tokenize()
    except LexError as e:
        diagnostics.append(_make_diagnostic(
            e.line or 1, e.col or 1, e.message,
            lsp.DiagnosticSeverity.Error,
        ))
        return diagnostics

    # Parse
    try:
        tree = Parser(tokens).parse()
    except ParseError as e:
        diagnostics.append(_make_diagnostic(
            e.line or 1, e.col or 1, e.message,
            lsp.DiagnosticSeverity.Error,
        ))
        return diagnostics

    # Check (type errors + warnings)
    checker = Checker()

    # Pre-seed project-wide symbols so cross-file references are known
    proj_syms, proj_funcs = _get_project_symbols()
    for sym in proj_syms:
        checker.symtab.declare(sym)
    for fs in proj_funcs:
        checker.symtab.declare_func(fs)

    checker.check(tree)
    for d in checker.diagnostics:
        severity = (lsp.DiagnosticSeverity.Error if d.level == "error"
                    else lsp.DiagnosticSeverity.Warning)
        diagnostics.append(_make_diagnostic(d.line, d.col, d.msg, severity))

    return diagnostics


def _make_diagnostic(
    line: int, col: int, msg: str, severity: lsp.DiagnosticSeverity,
) -> lsp.Diagnostic:
    """Build an LSP Diagnostic at the given 1-based source location."""
    # LSP uses 0-based lines/columns
    ln = max(0, (line or 1) - 1)
    co = max(0, (col or 1) - 1)
    return lsp.Diagnostic(
        range=lsp.Range(
            start=lsp.Position(line=ln, character=co),
            # Highlight to end of line (we don't track token length yet)
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
    # Full sync — the entire document is in content_changes[0].text
    text = params.content_changes[0].text
    _publish(params.text_document.uri, text)


@server.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
def did_save(params: lsp.DidSaveTextDocumentParams):
    # Re-analyze on save (in case incremental changes were missed)
    doc = server.workspace.get_text_document(params.text_document.uri)
    _publish(params.text_document.uri, doc.source)


def _publish(uri: str, source: str):
    """Run analysis and publish diagnostics to the client."""
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
