# tests/ Corpus Audit — findings and repairs

Scope: every tracked `tests/*.ergo` (206 files; includes the 3
`tests/stream/` programs, which the stream suite also covers).
Audit: `tests/golden/corpus_audit.py` (re-runnable; writes
`corpus_audit.json`). Regression gate: `tests/golden/run_corpus.py`.

Verdict rule: PASS = compiles (IR path) + runs exit 0 within 60 s +
two runs byte-identical stdout. GPU classes compiled+run with
`--target spirv` (serial, one Vulkan job at a time, RTX 2060).

## Classification (post-repair)

| class | count | meaning |
|---|---|---|
| PASS | 184 | compile + run + deterministic, CPU path |
| GPU-PASS | 13 | spirv compile + run + deterministic |
| SLOW | 8 | healthy long sims, > 60 s (excluded from default gate) |
| GPU-SLOW | 1 | 62 s GPU sim, no stdout by design (exit-0 is the signal) |
| FAIL-COMPILE | 0 | — |
| FAIL-RUNTIME | 0 | — |
| nondeterministic | 0 | — |

Pre-repair the audit found 5 FAIL-COMPILE (all repaired, below) and 0
runtime failures; nothing needed deletion, nothing was superseded.

## Repairs (Phase 2) — 5 files, one root cause

- `tests/waveform_molecule_dynamics.ergo`
- `tests/waveform_molecule_dynamics_geometric.ergo`
- `tests/waveform_molecule_dynamics_geometric_strain.ergo`
- `tests/waveform_molecule_dynamics_geometric_tall.ergo`
- `tests/waveform_molecule_repel.ergo`

**Fault (identical in all five):** `LexError: Unterminated string
literal` — the CSV-header `WRITE` format string was split across
lines with Fortran-style `&` continuation *inside the string
literal*. Ergo's `&` continuation (F3) applies between tokens during
lexing; a string literal must close on its own line. These are the
only multi-line strings in the corpus (the same files use `&`
between tokens extensively and lex fine).

**Repair:** joined each split format string into a single-line
literal — output bytes unchanged by construction (the continuation
text was string content). No other edits. Each file now: compiles,
runs to completion (100–150 CSV rows, physically sane — energies
relax, bonds form), two runs byte-identical.

**Language-decision flag (for the user, not a test bug):** Fortran
allows `&`-continuation inside string literals; Ergo currently
rejects it with a lexer error. Judged acceptable as-is (single-line
literals are the documented norm, and the corpus needed exactly five
one-line joins) — but if string continuation is ever wanted, it is a
lexer gap to close in `core/lexer.py::_consume_continuation`, not
more test churn. No compiler bug found in this audit.

## SLOW class (permanent, excluded from the default gate)

Genuine long protein-folding sims (192k–384k frames): all compile,
stream valid CSV immediately (3.5k–6k frames in the first 20 s,
values physically sensible), and are deterministic by construction
(fixed seeds, fixed step counts — same code family as the 184 PASS
waveform sims, which all double-run byte-identical). They run in the
gate with `--slow` (300 s timeout each).

- `waveform_parkin_s223p_s0_192k`, `waveform_parkin_wt_s0_192k`
- `waveform_uchl1_i93m_s4_192k`, `waveform_uchl1_i93m_s4_384k`,
  `waveform_uchl1_i93m_s4_t06_192k`
- `waveform_uchl1_wt_s4_192k`, `waveform_uchl1_wt_s4_384k`,
  `waveform_uchl1_wt_s4_t06_192k`

**GPU-SLOW:** `buc_colony_gpu.ergo` — 62 s on the RTX 2060 (just over
the default 60 s), and prints nothing by design (no WRITE/PRINT in
source; the regression signal is exit-0 completion). Runs with
`--slow`.

## The regression runner (Phase 3)

`tests/golden/run_corpus.py`, driven by the reviewed classes in
`corpus_audit.json`:

- default: 184 PASS (CPU, parallel 8 compile / 4 run) + 13 GPU-PASS
  (serial) — compile, run, diff stdout vs baseline;
- `--slow`: adds the 8 SLOW + 1 GPU-SLOW (300 s timeouts);
- `--no-gpu`, `--only=<glob>` for subset work;
- `--record`: (re)record baselines — **only after reviewing outputs**.

Baselines: `corpus_baseline.json` (tracked, 44 KB — sha256 + byte
count + first/last line per program) is the gate oracle. Full stdout
dumps live in `corpus_baseline/*.out` (**local-only**, ~50 MB,
regenerable with `--record`; repo convention keeps dumps out of
git). On DIFF the runner saves the actual output to
`/tmp/corpus_diff_<name>.out` for inspection. Sanity review at
record time: waveform sims show CSV header + per-frame rows +
`END_FINAL_STRUCTURE`; unit tests show their self-check lines
(`prng` chain-checksum, `write_formats` format rows, allocator TINVAR
dumps); `buc_colony` is an 8 MB ANSI frame animation (deterministic).

The runner is wired into the golden gate: `run_golden.py` tails it
after the stream suite (golden corpus 16/16 + stream 8/8 + corpus
197/197 all green at wiring time).

## Files

- `tests/golden/corpus_audit.py` — Phase-1 auditor (re-runnable)
- `tests/golden/corpus_audit.json` — machine-readable verdicts
- `tests/golden/run_corpus.py` — Phase-3 regression runner
- `tests/golden/corpus_baseline.json` — tracked hash oracle
- `tests/golden/run_golden.py` — gate wiring (stream + corpus tails)
- 5 repaired `tests/waveform_molecule*.ergo` (above)
