# Ergo VSCodium Extension Design

## Overview

A Language Server Protocol (LSP) extension for Ergo (.ergo files).
Syntax highlighting, inline diagnostics, hover info, and GPU performance
hints — all powered by the existing Python compiler infrastructure.

## Architecture

```
VSCodium
  ├── package.json          (extension manifest)
  ├── syntaxes/
  │   └── ergo.tmLanguage.json  (TextMate grammar)
  └── starts LSP server ──→ mcl/lsp_server.py (Python, pygls)
                                ├── uses mcl/parser.py     (existing)
                                ├── uses mcl/checker.py    (existing)
                                ├── uses mcl/ir_builder.py (existing)
                                └── uses mcl/ir_gpu.py     (existing)
```

The extension is a thin shell. All intelligence lives in the Python LSP
server, which imports the existing compiler modules. No duplication.

## Components

### 1. TextMate Grammar (syntaxes/ergo.tmLanguage.json)

Syntax highlighting only — no semantic analysis. Regex-based tokenization.

**Scopes to highlight:**

| Pattern | Scope | Color intent |
|---------|-------|-------------|
| `SUBROUTINE`, `FUNCTION`, `END` | keyword.control | purple |
| `DO`, `ENDDO`, `DO WHILE`, `IF`, `THEN`, `ELSE`, `ELSEIF`, `ENDIF`, `CYCLE`, `EXIT` | keyword.control.flow | purple |
| `CALL`, `RETURN` | keyword.control | purple |
| `INTEGER`, `REAL`, `PARAMETER`, `STATIC` | storage.type | blue |
| `IMPLICIT NONE` | keyword.declaration | blue |
| `IAND`, `IOR`, `ISHFT`, `NOT`, `SQRT`, `ABS`, `MAX`, `MIN`, `CLAMP`, `REAL`, `INT`, `MOD`, `ATAN2` | support.function.builtin | yellow |
| `RING_PREV`, `RING_NEXT`, `RING_SHIFT` | support.function.intrinsic.ring | cyan |
| `SORT_BY_GEN`, `VERIFY` | keyword.directive | orange |
| `PRINT` | keyword.other | purple |
| `!` to end of line | comment.line | grey |
| Numbers (`123`, `0.5`, `1.0E-4`) | constant.numeric | green |
| String literals (`"..."`) | string.quoted.double | green |
| `.AND.`, `.OR.`, `.NOT.`, `≠`, `≥`, `≤` | keyword.operator.logical | red |
| `:=` | keyword.operator.assignment | white |
| `PFLAG_*`, `GRID_*`, `OMEGA_*` | variable.other.constant | bold |
| `DATA` | keyword.other.data | blue |

**File association:** `*.ergo` → language ID `ergo`

**Estimated size:** ~150 lines of JSON.

### 2. LSP Server (mcl/lsp_server.py)

Python LSP server using `pygls` (pip install pygls).

**Capabilities:**

| LSP Feature | What it does | Priority |
|-------------|-------------|----------|
| `textDocument/didOpen` | Parse file, report diagnostics | MVP |
| `textDocument/didChange` | Re-parse on edit, update diagnostics | MVP |
| `textDocument/hover` | Array footprint, constant values, FLOW class | MVP |
| `textDocument/publishDiagnostics` | ERROR/WARNING/PERF inline markers | MVP |
| `textDocument/completion` | Keyword + intrinsic completion | Phase 2 |
| `textDocument/definition` | Go-to-definition for SUBROUTINEs | Phase 2 |
| `textDocument/references` | Find all references to a variable | Phase 2 |
| `textDocument/codeAction` | "Replace with CLAMP" quick fix | Phase 3 |

**Core loop:**

```python
from pygls.server import LanguageServer
from mcl.parser import parse
from mcl.checker import check
from mcl.ir_builder import IRBuilder
from mcl.ir_gpu import extract_kernels

server = LanguageServer("ergo-lsp", "v0.1")

@server.feature("textDocument/didOpen")
@server.feature("textDocument/didChange")
def on_change(params):
    uri = params.text_document.uri
    text = server.workspace.get_text_document(uri).source

    diagnostics = []

    # Parse
    try:
        ast = parse(text)
    except ParseError as e:
        diagnostics.append(make_diagnostic(e.line, e.col, e.msg, ERROR))
        server.publish_diagnostics(uri, diagnostics)
        return

    # Check (type errors, warnings)
    errors, warnings = check(ast)
    for e in errors:
        diagnostics.append(make_diagnostic(e.line, e.col, e.msg, ERROR))
    for w in warnings:
        diagnostics.append(make_diagnostic(w.line, w.col, w.msg, WARNING))

    # GPU analysis (PERF hints)
    try:
        ir = IRBuilder(ast).build()
        plans = extract_kernels(ir)
        for plan in plans:
            diagnostics.append(make_perf_hint(
                plan.source_line,
                f"Loop classified as {plan.kind} — "
                f"{'GPU extracted' if plan.extracted else 'CPU only: ' + plan.reject_reason}"
            ))
    except Exception:
        pass  # GPU analysis failure is not user-facing

    server.publish_diagnostics(uri, diagnostics)
```

**Diagnostic severity mapping:**

| Ergo class | LSP severity |
|------------|-------------|
| ERROR | DiagnosticSeverity.Error |
| WARNING | DiagnosticSeverity.Warning |
| PERF | DiagnosticSeverity.Hint |
| CORRECTNESS | DiagnosticSeverity.Warning |

### 3. Hover Provider

```python
@server.feature("textDocument/hover")
def on_hover(params):
    line = params.position.line
    col = params.position.character
    # Find token at position in parsed AST

    # Array declarations: show memory footprint
    # "STATIC REAL :: POS_X(MAXPART)"
    # → "POS_X: REAL array, 30000000 elements, 120 MB"

    # Constants: show resolved value
    # "PARAMETER REAL :: K_PHASE_LOCK = 0.001"
    # → "K_PHASE_LOCK = 0.001 (phase restoring strength)"

    # LUT arrays: show values
    # "FLOW_MODE(GEN)"
    # → "FLOW_MODE: [0,1,1,1,2,0,0,2,...] — 10 COAST, 14 ACTIVE, 8 FLOW"

    # RING_PREV/RING_NEXT: show shuffle semantics
    # → "Warp shuffle: reads lane (id-1) & 31, wraps at ring boundary"

    # Extracted loops: show classification
    # → "INJECTIVE kernel — 29M threads, ~5.9ms estimated"
```

### 4. package.json (Extension Manifest)

```json
{
  "name": "ergo-lang",
  "displayName": "Ergo Language",
  "description": "Language support for Ergo (.ergo) — simulation language",
  "version": "0.1.0",
  "engines": { "vscode": "^1.75.0" },
  "categories": ["Programming Languages"],
  "contributes": {
    "languages": [{
      "id": "ergo",
      "aliases": ["Ergo", "MCL"],
      "extensions": [".ergo"],
      "configuration": "./language-configuration.json"
    }],
    "grammars": [{
      "language": "ergo",
      "scopeName": "source.ergo",
      "path": "./syntaxes/ergo.tmLanguage.json"
    }]
  },
  "main": "./extension.js",
  "activationEvents": ["onLanguage:ergo"]
}
```

**extension.js** — minimal JS that starts the Python LSP server:

```javascript
const { LanguageClient } = require('vscode-languageclient/node');

function activate(context) {
    const client = new LanguageClient(
        'ergo-lsp', 'Ergo Language Server',
        { command: 'python', args: ['-m', 'mcl.lsp_server'] },
        { documentSelector: [{ scheme: 'file', language: 'ergo' }] }
    );
    client.start();
    context.subscriptions.push(client);
}

module.exports = { activate };
```

~15 lines. The Python server does all the work.

### 5. language-configuration.json

Bracket matching, auto-close, comment toggling:

```json
{
  "comments": { "lineComment": "!" },
  "brackets": [],
  "autoClosingPairs": [
    { "open": "(", "close": ")" }
  ],
  "surroundingPairs": [
    ["(", ")"],
    ["\"", "\""]
  ],
  "folding": {
    "markers": {
      "start": "^\\s*(DO|IF|SUBROUTINE|FUNCTION)\\b",
      "end": "^\\s*(ENDDO|ENDIF|END)\\b"
    }
  }
}
```

## File Layout

```
ergo-extension/
  package.json
  extension.js                (~15 lines)
  language-configuration.json (~20 lines)
  syntaxes/
    ergo.tmLanguage.json      (~150 lines)

mcl/
  lsp_server.py               (~300 lines, new)
  lsp_diagnostics.py          (~200 lines, new — WARNING/PERF analysis)
```

Total new code: ~700 lines across 4 files.
Extension shell: ~200 lines (JSON + JS).
LSP server + analysis: ~500 lines (Python).

## Dependencies

- `pygls` — Python LSP library (pip install pygls)
- `vscode-languageclient` — npm package for the extension JS side
- Node.js — for packaging the extension (vsix)

No other dependencies. The LSP server imports from the existing `mcl/` package.

## Implementation Order

### Session 1: Syntax Highlighting
1. Write ergo.tmLanguage.json
2. Write package.json + language-configuration.json
3. Write minimal extension.js (no LSP yet, just syntax)
4. Test: open .ergo file in VSCodium, verify colors

### Session 2: LSP Diagnostics
5. pip install pygls
6. Write mcl/lsp_server.py — parse on open/change, publish ERROR diagnostics
7. Wire extension.js to start LSP server
8. Test: syntax errors show red squiggles inline

### Session 3: Hover + PERF Hints
9. Add hover provider (array footprint, constant values)
10. Add WARNING diagnostics (FP equality, division safety)
11. Add PERF hints (FLOW classification, extraction failure reasons)
12. Test: hover over array shows size, loops show classification

### Session 4: Polish
13. Code completion (keywords, intrinsics)
14. Go-to-definition for subroutines
15. Quick fix actions (suggest CLAMP, suggest tolerance comparison)
16. Package as .vsix for distribution

## Design Rules

- **The LSP server never modifies files.** Read-only analysis.
- **Parse errors don't block PERF analysis.** If the parser fails, show
  the parse error but still try to analyze what was successfully parsed.
- **Diagnostics update on every keystroke** (debounced). The Ergo parser
  is fast enough for this — 1000 lines parses in <10ms.
- **No network calls.** Everything runs locally. The LSP server is the
  compiler running in analysis mode.
- **GPU analysis is best-effort.** If IR building or kernel extraction
  fails, suppress those hints silently. Never crash the LSP server.
