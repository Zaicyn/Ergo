# Secure — AUDIT

Every substantive bug found by measurement in this campaign: symptom,
cause, fix, and the commit that carries it. Shared assembler pitfalls
(#1–#20) live in `min/Fasm/progress.md` and are referenced, not
repeated — except where Secure re-offended, which is noted honestly.

## Repair math

- **Vacuous reverify after repair (torusecc).** Post-repair residual
  check always passed by linearity, so miscorrections went undetected.
  Fixed with the S3 cubic gate on both stored and derived variants;
  misc 0/6000×2 after. (`5644e54`, `60505a3`)
- **Rebuild-before-repair transplants errors (packetbench).** Parity
  rebuild from dirty survivors copied their errors into the fresh
  packet (mixed cell 0/200). Order is SEC survivors → rebuild from
  clean data → reverify (now 176/200). (`fa8ea30`)
- **GF(256) generator 2 has order 51, not 255.** Log/exp tables built
  around 2 silently aliased; every 2-erasure solve produced garbage
  (LO d=2: 0/200). Switched to 3 (verified order 255) → 200/200.
  Finite-field code fails silently and exactly. (`e6d3fc4`)

## Integer arithmetic in ports

- **`div r/m32` uses only the low 32 bits (reflex).** C's full-64-bit
  `%` diverged from the port's `div r32`. Fixed with `div r64`.
  (Power-of-2 masks were always safe.) (`cd61736`)
- **Quotient vs remainder (pktcodec `dmg_burst`).** Burst start took
  `rax` (quotient) after `div` instead of `rdx` (remainder): starts
  landed terabytes out of range, SIGSEGV. Caught by watching the
  `div` execute live. This is progress.md #13 re-offending. (`dce9076`)
- **`modpow` square step clobbered the result (rgba_hs).** `mov eax,
  ebx` discarded the running product every multiply iteration (27
  instead of 191, zero complaint). Save/restore `rax` around the
  square. (`720bced`)
- **Single vs double indirection (pktcodec `sec_pkt`).** Saved ref
  pointer in `st_ref`, then subtracted `dword [st_ref]` — the low 32
  bits *of the pointer itself* — instead of dereferencing. Residuals
  in the billions where ±255 was the max. Fingerprint: bound the
  residuals first (S0 over 512 B can't exceed ~130K). (`dce9076`)

## Printing (the `pdec`/`div` family)

- **Pointer reused across `pdec` (reflex, alignchk).** `pdec` clobbers
  `rdx` via `div`; a buffer pointer held across two `pdec` calls
  prints glued numbers. Reload per counter. (`cd61736`, `514966e`)
- **Truncated labels.** 7–9 byte labels loaded short dropped their
  trailing `=` (`exact1`, `tamper1`, `tags1`, short `verify=`).
  Exact-size moves or nothing. (`720bced`)
- **Serve counter init after the branch (tcp_node).** `served` was
  zeroed past the listen-select, so the timeout path printed the
  stale socket fd as "served=3" — deterministic, bogus, while
  recovery stayed correct. Init counters before the branch.
  (`8abe547`)

## FASM encoding and reserved words

- **`vpbroadcastd ymm, r32` is EVEX-only** (progress.md #11):
  assembles, SIGILLs on AVX2-only. Broadcast from xmm.
- **Legacy SSE in AVX loops** (progress.md #17, ~70cy transitions):
  VEX-encode everything; `vzeroupper` at boundaries, never inside
  live ymm loops (progress.md #18).
- **Cross-lane ops cost everywhere** (progress.md #19, measured
  1.38×); **256-bit width is per-machine** (progress.md #20, 1.7×
  here on Zen 2, split on Zen 1).
- **Reserved words as symbols:** `dec`, `LDS` (`720bced`),
  `restore`, `used` (`dce9076`). Renamed on contact.
- **`db`-defined symbols need explicit size overrides** (`mov ax,
  word [...]`; stores as `mov word [...], ...`). (`720bced`)
- **ALU ops take imm32 only.** 64-bit constants must go through
  registers or memory (`add rax, [st_m1]`). `mov r64, imm64` is
  fine. (`720bced`)
- **Include-tail segment reset** (progress.md #16 re-offending):
  `pktcore.inc` ends in `readable` (st_m1), so node code after the
  include landed non-executable — entry in data, instant SIGSEGV.
  Re-issue the segment after every include. (`dc514c4`)

## Sockets and protocol

- **Fetch only on erasures (demandbench, sockbench).** Parity solves
  erasures, so a receiver that knows its missing-unit count fetches
  iff 1–2 units are gone; pure-error damage skips straight to
  resend accounting. Cut bytes and RTT at every damage rate.
  (`4e98245`)
- **NULL `lost` dereference (packetbench `run_ecc`).** Guarded;
  unrecoverable erasures skip SEC. (`fa8ea30`)
- **Stale length header on hand-rolled fetch replies (sockbench).**
  Replies carried the request's `len=1`: receiver copied 1 byte of
  good parity + 511 bytes of stack garbage, commitment failed
  (correctly). Set headers explicitly. (`4e98245`)
- **`SO_RCVTIMEO {0,0}` means BLOCK, not poll.** Drain loops must use
  `select()` with a zero timeout (true nonblocking poll). (`4e98245`)
- **Missing `SO_REUSEADDR`** hung setup on reruns (TIME_WAIT).
  (`4e98245`, `8abe547`)
- **Missing `TCP_NODELAY`** stalled the 11-byte fetch request to
  ~1.5 ms. Set on everything latency-sensitive. (`8abe547`)
- **Sender must ignore SIGPIPE** (died silently on send-into-closed).
  (`8abe547`)
- **Test probes must not TCP-connect.** A readiness probe consumes
  the one accept and desyncs the matrix; sleep ordering instead.
  (`8abe547`)
- **Uninitialized accept addrlen** (BSS zeros → 0). Always init to
  16 before accept. (`8abe547`)
- **Startup races (UDP).** Receiver must be bound before datagrams
  fly; orchestrate receiver-first with port ready-probing.
  (`dc514c4`)
- **Zero-oracle scoring (interop receivers).** Receiver compared
  against an unbuilt (all-zero) frame: full=1 on empty air. Receivers
  build the known-answer frame for scoring; the repair path never
  reads it. (`dc514c4`)
- **Unit index stamped 0 on all datagrams (asm sender).** `al` held
  low(u*512) = 0; receivers deduped 7 units (got=2). The C sender
  working isolated it to serialization in one step. (`dc514c4`)

## C-mirror bugs (the mirror disciplining the port, for once reversed)

- **`v_ovl_corr` short-circuit (alignchk).** C skipped SEC when the
  overlap agreed; asm `corr_core` always SECs. 5 M-row splits; fixed
  C to mirror asm (always-SEC + recheck). Pure-corrupt rows
  unchanged. (`514966e`)

## Open (not bugs: measured boundaries)

Bursts past interleave depth, whole-segment erasure, 3+ unit loss,
damage fractions where resend wins — all in `TCP_PROMISE.md` with
numbers. The grid verdict on loss-inertness (algebra exact,
second-order pool-concentration real) is recorded there too.
