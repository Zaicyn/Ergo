# Compression plan (Phase A now, Phase 3 gated)

Context: `progress.md` (FASM ports), `trit_meta.md` (trit layer),
`minimum_unit.md` (width ladder), `../work/lossless_frame/ALLOCATOR_FIT.md`
and `LFC6_PLAN.md` (source designs). This file plans the compression work
so it can start the moment size pressure — log volume, binary size, or
arena high-water mark ("compaction") — demands it, instead of being
designed under pressure.

## Triggers (measure first, act on numbers)

- **Audit-log volume.** Measure sustained bytes/s of outcome/moment logs
  at target frame rate. Act when it exceeds the transmit/store budget for
  the deployment. First measurement owed: trit-packed sweep log at
  sim rate (Phase 2 measured 52 B/round on cert data, not sim rate).
- **Binary text size.** No-libc/static targets with size caps. Act when a
  capped target is named and `text` exceeds it (current ports: 0.6–8 KB;
  plenty of headroom today).
- **Arena/BSS pressure.** Long-horizon sims: watch arena high-water mark
  vs budget. Compression of resident structures (journals, caches) is a
  last resort behind eviction policy — say so explicitly if proposed.

No trigger fires today. Phase A proceeds because it is cheap tooling with
independent value (signed storage, log fields); Phase 3 waits on a trigger
or an explicit call.

## Phase A — zigzag + variable-width ints (DONE 2026-09-11)

Transplants from `lfc_dyadic.c`: `zz_enc/zz_dec`, `put_i64/get_i64`.

- `zz_enc`: `(e<<1)^(e>>31)` branchless (4 instrs). `zz_dec`:
  `(s>>1)^-(s&1)`. Maps small-magnitude signed values (solve deltas
  d1/d2, moment diffs) to small unsigned — precondition for all compact
  integer storage.
- `put_i64` / `get_i64`: minimal-byte LE store + sign-extending load,
  widths 1..8, caller chooses (same contract as `sparse_encode`'s fixed
  1/2/3/5/7-byte moment classes). Plus `i64width`: minimal signed width
  via `t = v^(v>>63)`, `bytes = (bsr(t)+9)>>3` capped at 8.
- Files: `trit/int_codec.inc` (shared, single source), `trit/zztest.asm`
  (driver). Graduates to shared if SQW/SQ5 ports use it.
- Tests (must all pass): exhaustive int8 round-trip (-128..127) with
  width==1 check; int16/32/64 boundary values (±2^(8n-1)-1, ±2^(8n-1),
  INT64_MIN/MAX); put/get round-trip per width 1..8; cross-check vs C
  mirror + digest. Speed: note cycles/op alongside.
- Integration points waiting: extent base/len fields, moment journal
  storage classes, RLE-adjacent delta coding, Phase-2 log v2.
- Gate to done: self-test green + C digest match + recorded speeds.
  No behavior change to existing ports (additive only).

## Phase 3 — range coder endgame (PLANNED, gated, do not start early)

Target: audit/log streams at near-entropy instead of fixed 1.585
bits/unit (our trit streams at ~98.7% zeros carry ~0.1 bits/unit — a
further 10–15× over trit packing). Range coding, not rANS (simpler to
port correctly, deterministic), after `lfc_dyadic.c` `rc_encode/rc_decode`.

- **3a Model format.** Static sparse model: transmitted symbol list +
  dyadic frequencies rescaled to exact RC_TOTAL (no Fenwick). Spec the
  header, stream, and trailer bytes first; no code.
- **3b Encoder.** Range subdivision, renormalization, carry-cache
  (`rc_shift_low` pattern). This stage holds all the subtlety — budget
  accordingly.
- **3c Decoder.** Table-driven bisection (`cum[mid] <= v`), exact-length
  dispatch (wrong length refuses loudly, per house doctrine).
- **3d Certification.** Round-trip corpus incl. adversarial inputs in the
  LFC6 §4 lineage (multi-hit, syndrome+stream hits, blind-class
  patterns); encode-twice byte-identity; FASM+C mirrors with matching
  digests; loud refusal on corrupt streams. The gate is the sweep, not
  a compile.
- **3e Integration.** First target only: trit audit logs (coldest path).
  Codec cores, hot sweeps, and GPU paths are explicitly out.
- Entry gate (any one): a compaction trigger fires, or explicit call.
  Exit criteria per stage above; stages do not overlap.

## Log v1 (DONE 2026-09-11 — served as the tutorial level)

Self-contained starter: emit real RLE + trit action logs from a live
`sq2b` cert run. Picks up with zero conversation history required; every
input below is either in-tree or reproducible from it.

### Background to absorb first (30 min)

- `progress.md`: Status table, both Pitfalls sections (assembler quirks +
  methodology — they were paid for in debugging hours, read them first).
- `trit_meta.md` (why ternary logs), `minimum_unit.md` (width ladder +
  ghost warning), `SQW/README.md` (most recent full port, shows the
  working pattern: survey → baseline → port → byte-match → record).
- Reference numbers (reproduce before trusting anything new): 2000 cert
  rounds × 256 ternary outcomes, value histogram {0:505255, 1:6697,
  2:48}, nonzero/round mean 3.37. Expected encoded totals: raw 512000
  (100%), 2-bit 128000 (25%), trit 104000 (20.3%, 51 groups + zero pad),
  RLE 30578 (6.0%). Speeds (MB/s best-of-3): enc 7931/3362/3083/1463,
  dec 8433/3262/5445/1651 (raw/2bit/trit/rle). All round-trips 0 fails.
- Toolchain: `/tmp/opencode/fasm/fasm.x64` (tarball; `fasm` is NOT on
  PATH). Build from the directory containing the sources (includes
  resolve by working directory). `musl-gcc` exists; `fasm` does not need
  installing.

### Steps (in order, each verified before the next)

1. **Extract `rle_pack.inc`** from `trit/phase2.asm`: `pack2`/`unpack2`,
   `rle_enc`/`rle_dec` (+ nothing else; driver stays). Same pattern as
   the `trit_codec.inc` extraction (which kept byte-identical output —
   do the same check: `phase2` rerun must print identical numbers).
   RLE format (locked): `[count:u8][value:u8]` pairs, count 1..255.
2. **Instrument a `sq2b` copy** (never the original; name it distinctly,
   e.g. `sq2b_log.asm` — never reuse a live binary name): after each
   cert-round sweep in Phase A/B, encode `action[256]` via `rle_enc`
   and the trit bulk path, `write(2)` both to per-method log files
   (`openat`/`write`/`close` pattern — see git history if needed, but
   re-derive from syscalls(2), don't copy blindly). Deterministic seed
   means the stream matches the reference histogram above — verify
   early (first divergence = stop and diagnose, don't accumulate).
3. **Self-verify in-tool**: decode each logged round back and compare
   against the live array before writing (the phase2 `fails` pattern).
   Done = log sizes match the table above byte-exactly, fails 0,
   speeds recorded alongside.
4. **Record**: sizes + speeds into `progress.md` (extend the Phase 2
   section, don't invent new tables), note anything surprising.

### Definition of done

- Two log files + a run transcript matching the reference numbers above.
- Round-trip fails 0, verified in-tool (not by eyeball).
- No changes to `sq2b.asm`, `phase2.asm`, or any include (additive
  copies only — the oracles stay green untouched).
- Progress entry written while the numbers are warm.

### Deliberately out of scope (queued behind this)

- Sparse-moment log (solve-on-decode) compares against THESE logs on
  identical data — needs this task's outputs as its baseline.
- Varint extent fields extend this log format — needs this format first.
- Range coder (Phase 3) takes these logs as its first integration
  target — needs measured densities to beat (6.0% RLE is the number).

### Pitfalls pre-loaded (from `progress.md`, most relevant here)

- `rep movsb` copies `[rsi]`→`[rdi]` — verify every copy's direction;
  reversed copies zero inputs while aggregates look perfect.
- Local-label typos jump somewhere valid — grep every jump target.
- BSS label typing (`rb` vs `rd`/`rq`) must match access width.
- Edit first, confirm, *then* build — never parallel.
- Distinct binary names always; ASCII-only sources; callee-saved
  discipline across every `call` (`cpuid` clobbers `rbx`!).

### Result (2026-09-11)

Done as specified: `trit/rle_pack.inc` shared, `Sq2B/sq2b_log.asm`
(10.4 KB) emits both logs live with in-tool decode-verify (fails 0),
stdout oracle byte-identical to GCC. Payloads byte-exact vs Phase 2
(RLE 30578, trit 104000); framing adds 4 KB/file. Full numbers in
`progress.md` (Log v1 section). Queued follow-ups (sparse-moment
comparison, varint fields, range-coder entry) now have measured
baselines to beat: 6.0% RLE at ~400 MB/s inline.
