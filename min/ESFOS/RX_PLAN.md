# Next session: RX path mapping (plan)

Objective: map the BLE receive half the way TX was mapped — RX descriptor
ring format, recycle mechanism, RX-done signaling to host, where received
bytes land, RX enable/disable. Unblocks everything bidirectional
(minimal connection attempt after).

Rig state at close-out: app healthy, ADV gated off (TOG0), next REKICK
rescues normally. OpenOCD daemon with `espusbjtag caps_descriptor 0x2000`
+ `vid_pid 0x303a 0x1001`, telnet :4444, GDB :3333. Branch ahead of
origin/master (unpushed); see `git log --oneline`.

## 1. Files and how to use them

Repo (`/home/zaiken/Ergo/min/ESFOS/`, committed):
- `BEACON.md` — all TX findings (CS map, trigger PCs, OR-gate resume
  matrix, T1, scan-rsp, timing, ops). Read first.
- `BLOBS.md` — blob inventory (controller + PHY/BB closed).
- `SPEC.md`, `esfs.c` — project spec / misc source.
- `esfnode/src/esfnode.c` — probe firmware (4-phase auto-cycle:
  TOG set/clear, RESUME init replay, REKICK adv restart; serial prints
  are the phase clock: `TOG bit8=`, `RES done`, `REKICK`, `ADV start rc=`).
- `esfnode/src/radio_if.{c,h}`, `esfnode/{platformio.ini,sdkconfig.defaults}`
  — bearer + build config (sdkconfig.defaults authoritative;
  generated `sdkconfig.heltec_wifi_lora_32_V3` is build-local, never commit).
- `tools/mmio_miner.py` — static MMIO-site miner over blob `.o` files.
- `tools/le_poke_decode.py` — poke-table (init sequence) decoder.
- `tools/out/` — miner outputs + baselines: `mmio_sites.txt`,
  `poke_tables.txt`, `reg_baseline_{biton,bitoff,postresume}.txt`,
  `summary_by_{block,fn,region}.txt`, `undocumented.txt`, `regions.txt`.

Scratch (`~/opencode/`, NOT committed, rebuildable):
- `esfnode/.pio/build/heltec_wifi_lora_32_V3/firmware.elf` — linked ELF
  (symbols for GDB ROM disasm + nm). Rebuild via PIO from repo if stale.
- `btdm/obj/*.o`, `mmine/obj/*.o`, `btdm/dis/`, `mmine/dis/` — extracted
  blob objects + disassembly (lld_adv.o, lld.o, llm_adv.o, rwble.o,
  emi.o, ip_funcs.o, ...). `readelf -r ip_funcs.o` gives the RAM
  function-pointer table slot order; live base `0x3FCEA184`
  (from `[0x3FCEFF68]`).
- `*_dis.txt` (`setcs`, `advdataset`, `frmcbk`, `frmisr`, `endind`,
  `scanrsp`) — saved GDB ROM disassemblies with resolved literals.
- `em8k_fresh.bin` (EM base +8K @`0x3FCAE518`), `em_mid.bin` (EM-4K +12K),
  `cs0_live.bin`, `pool_live.bin`, `cs1.bin`, `pool1.bin` — key dumps.
- `dram*.bin`, `scan*.bin`, `sy*/sz*/bw*/bk*/bq*/bv*/bm*/lk*/v*` — DRAM
  sweep chunks (bases in filename order: 0x3FC88000/0x3FC97000/
  0x3FCA6000/0x3FCB5000[/upper halves]); most superseded, keep the
  newest per range.
- `trap{ A,B,C,D,E,F,G }.log`, `park.log` — GDB trap transcripts.
- `beacon_raw.log`, `v4_raw.log`, `verify_*.log`, `scanrsp_*.log` —
  btmon captures; `corr*.log`, `btmon*.pcap` — prior session evidence.
- `emregs.txt`, `ipf.txt`, `emscan.py`, `coc.py`, `snoop.py` — JTAG
  helpers (socket-telnet patterns; note telnet replies lag one command).

Key live addresses (re-verify post-reboot; heap is deterministic):
- EM base `0x3FCAE518` (from `0x60031204`); CS0 `0x3FCAE664`;
  adv pool `0x3FCAEDE8`; env `0x3FCEFCB0`; ip_funcs `0x3FCEA184`.
- Read side-effect rule: NEVER dump ISR/ack/FIFO/command regs
  (`0x6003100c,10,18,24,48,50`, `0x60011084,8c,90`, `0x60011868`,
  `0x60031304,360,364`). Safe whitelist = the 23 addrs in firmware.

## 2. Proven (TX side, see BEACON.md for evidence)

- Kill = clear bit8 @`0x60031000`; resume = gate + E0.bit0
  (`0x600310E0 |= 0x01`) OR gate + 11050-live (`0x60011050 0x711e02d0`).
  90-group pure don't-care. Reset-controlled matrix, audited.
- CS0 layout (CNTL/BDADDR/AA `8E89BED6`/CRCINIT/`0x8027`/TXCNT), 90 B
  stride, `+0x5C` = instance index; trigger PCs in ROM.
- Modem DMAs ADV body live from host mbuf (T1; 10 poke markers on air).
- Scan-rsp dormant + mbuf-gated; per-event slicing infeasible
  (5-150 ms events vs ~300 ms JTAG); DF parked (S3 is BT5.0, no CTE).

## 3. Unknowns (RX first, then the rest)

- RX ring @EM+0x000: 16x16B, w0 const `0x281a`-class, w1 ~0xCC-stride
  churning, w2 `0x3a->0x4d` over minutes. CONFIRM descriptor fields
  (bufptr/len/status) + recycle trigger + RX-done signal to host.
- RX ISR path: `r_lld_update_rxbuf_isr` / handler, regs `0x60011084/90`,
  `0x60031010/18` (excluded killers — read via JTAG mdw, never firmware
  dump; or disassemble handlers first).
- Where received bytes land (descriptor-linked buffer? which pool?).
- RX enable/disable (same gate bit? another bit? separate reg?).
- Later: CS necessity (zeroing trial, destructive-design), E0 high bits,
  11050 bit semantics, efuse own-addr shadow, TXDESC-from-scratch,
  per-event DMA latch (unbounded — parked unless RX work exposes it).

## 4. Testing process (method rules — earned, keep)

- Kill-readback-verified every trial; a dropped readback voids it.
- Reset-controlled: force ALL candidates idle + verify before subset.
- Frozen trials (halt CPU for writes; modem runs on) + post-hoc audit
  (mbuf addr/content + reg readbacks detect RES/REKICK intrusion).
- BlueZ verdicts need neighbor sightings as scanner control + fresh
  session per trial (no cache); btmon needs direct `sudo btmon`
  (NOPASSWD covers the binary, NOT `timeout`-wrapped calls).
- Background processes: use `nohup ... & disown` or keep foreground;
  bare `&` does not survive call end. Serial readers die on USB wedges;
  foreground reads only.
- Save/restore (dump before) around any write outside proven-safe regs.
- JTAG `reset` recovers wedges/slow-loop cleanly (boots from flash).

## 5. RX runbook (concrete steps)

1. Health check: serial HBs (2 s cadence), ADV on air (scan), gate/E0.
2. Baseline: dump EM+0x000 ring (16x16B) + region regs; record w1/w2.
3. Elicit RX traffic: active scans from laptop/phone (SCAN_REQ to us) +
   ambient advertisers; re-dump ring, diff per entry (which words move
   on reception?).
4. Disassemble `r_lld_update_rxbuf_isr` + handler (GDB + ELF, as before);
   find buffer-pointer computation + RX-done signal write.
5. One-shot trap at the recycle/descriptor store across a SCAN_REQ;
   capture regs (a5/a10 pattern as in TX traps).
6. Locate a received payload in DRAM (search for a known advertiser's
   bytes, e.g. a phone's name) -> confirms landing zone.
7. Doc + commit. Go/no-go on minimal connection attempt.

## 6. Session log 2026-09-18 (RX mapping, TX stable baseline kept)

Rig: OpenOCD espusbjtag (caps 0x2000, 303a:1001) telnet :4444; GDB :3333
unused (PIO GDB needs libpython2.7, absent). JTAG helper
`~/opencode/jtag.py` (scratch, NOT committed): passive banner drain
(the "lag" is only the connect banner + a `\x00` prefix on reply lines;
single-xchg is synchronous after that), address-echo-matched mdw with
continuation lines, bulk reads need cpu halted. BT helper
`~/opencode/btctl.py`: interactive bluetoothctl held open (per-process
`--timeout`/bare-`&` sessions drop discovery/link on exit -- this voided
early trials). `bluetoothctl --timeout N scan on` HOLDS discovery for Ns.

- RX ring @EM+0x000 = 16x16B confirmed. e0 = unprogrammed header
  (`a5a5a5a5` fill, w3 `0x148`); e1-15 live: w0 = bufptr (full 32b word,
  marches; low half was `0x281a`-class at some boots), w1 = `0x0270:RRRR`
  (RRRR monotonic +1/15-30 s while alive, frozen-static, survives REKICK
  re-init), w2 `0x0af70200` const, w3 `0f000c00` const. Entry stride in
  w0hi ~0xC0-0xE0 (avg ~0xD0 = 208 B-ish).
- March needs cpu1 (controller core) running: frozen (cpu1 halted) =
  static; alive = +25-31 KB/30 s ambient. NOT accelerated by held active
  scan + confirmed SCAN_REQ elicitation (stimulus == quiet) and NOT a
  per-packet counter (w1-lo +1/30 s metronomic in both). Relocates on
  REKICK re-init (two-group ~0xD00-split deltas).
- No `0x281a` literal in any blob .o -> tag is ROM-written. CPU
  watchpoint (OpenOCD `wp`, verified listed) on marching word never
  fires over 30-60 s: writer is NOT cpu1 (modem DMA) or wp silently
  broken (rwp removal errors; support immature -- treat as medium
  confidence). e0 never programs under ADV-RX (reserved for data-RX?).
- ISR/handler static decode (btdm/obj/lld.o + saved dis/lld.o.txt):
  ISR logs `[0x60031024]&0x7fff` + `[0x600312d0]&0x7fff`, clears bit7
  @0x600312d0, then calls `[[modules]+228]` = `r_ke_msg_send_basic`
  (0x40003abc, resolved via ELF ROM symbols) = RX-done signal.
  `r_lld_update_rxbuf(SZ,NB)` asserts SZ<=0x110, NB<=9 (so the 16-entry
  ring is NOT its table); handler loop is mod-10/20 B-stride with
  `r_emi_get_mem_addr_by_offset` (0x40003648 veneer) conversions,
  s16i status stores with bit15 = ready flag, and SETS bit15
  @0x600312d4 = recycle/update trigger (live: 312d0=0, 312d4=0xff when
  ADV off). `nm firmware.elf` carries the full BT ROM symbol table
  (all `r_*` addrs above from it).
- Landing zone: EM 8 K holds no payloads (only own BDADDR @0x152);
  480 KB DRAM sweep for live ambient names/MACs = zero hits (host never
  scans; buffers recycle too fast or never leave modem). Verdict:
  modem-private buffers, host-visible only via HCI (host scan) / L2CAP.
- CS base is PER-BOOT (0x3FCAE664 old build -> 0x3FCAE674 this build;
  magic-aligned: CNTL 0404/BDADDR/AA/CRCINIT/8027/txcount). mbuf likewise
  (0x3FCB0A00, `02 01 06 06 09 ESFOC` intact). RE-VERIFY EVERY BOOT.
  (One mis-poked mbuf-adjacent byte this session; healed by reset.)
- esfnode: added `CYCLE 0/1` serial gate for the 4-phase auto-cycle
  (default on; `cycle_en` + cmd parser; src synced to
  `~/opencode/esfnode`, rebuilt (PIO 6.2.0, 33 s), flashed post-OpenOCD
  stop). Serial input verified working (`STAT`/`CYCLE`). New heap
  2341760 (fresh boot 2402500, fragments with uptime).
- DUAL-CORE METHOD FIX: bare telnet halt/resume hits the current target
  (cpu1) only. A dual halt/resume dance WEDGES both cores (resume-order
  failure, only JTAG `reset` recovers). Discipline: cpu1-only
  halt/resume (freezes LL schedule; app on cpu0 keeps running, so
  phase-audits stay mandatory). `targets` state display lies (shows
  halted while app prints); serial HBs + memory are ground truth.
- REGRESSION: full v3 resume set, then row-K (gate+E0.bit0,
  readback-verified, gate PROVEN SET across a 20 s held scan with
  neighbor control) both DEAD where trial-E row-K was ALIVE. txcount
  static 000b, mbuf intact, CS magic-aligned. Soft reset revived ADV
  once (RSSI -42), then decayed again. Next: PHYSICAL power cycle
  (JTAG reset no longer suffices); then re-verify + re-run.
- CoC BLOCKED (independent of the above): GAP connects (ServicesResolved)
  but raw L2CAP CoC (coc.py, PSM 129) always EHOSTUNREACH at connect(),
  zero air egress, while ESP GATT answers (link + host alive) and ESP app
  prints no `EVT connected` for some establishments (stale-link
  re-resolution suspected in later tries). Historical rx.log proves the
  recipe (GAP-then-CoC) worked on this laptop stack. Laptop dmesg clean.
  Open: bind-type variant, l2test cross-check, MGMT-level trace of the
  failing connect.

## 7. Session log 2026-09-18 p2 (connection path + CoC data-RX)

- `coc.py` BUG (scratch): `BDADDR_LE_PUBLIC = 0` == BREDR. Kernel paged
  BREDR (Page Timeout in btmon) to the LE-only ESP -> EHOSTUNREACH.
  Fixed to 1. Lesson: EHOSTUNREACH + stray BREDR Create Connection in
  btmon = wrong addr type, not a dead peer.
- ESP `EVT connected` silence EXPLAINED: `ble_gap_adv_start(..., NULL,
  NULL)` never registered gap_ev. Fixed (prototype + pass gap_ev):
  first `EVT connected h=1`, `EVT phy tx=2 rx=2`, `EVT params` prints
  observed. gap_ev DISCONNECT->start_adv now runs (was dead code).
- LE gate NOT in blob ADV path: natural ADV dies at first TOG-clear/
  adv-stop; only probe TOG-set/REKICK re-armed it. Fix: `gate_set()`
  (bit8 MMIO) inside `start_adv()` -- every host (re)start re-arms.
- Serial INPUT is dead (Arduino owns USB CDC; stdin never arrives) AND
  IDF `usb_serial_jtag_read_bytes` HANGS the app loop (PC pins inside
  it, console silent -- diagnosed via JTAG PC resolve to
  `usb_serial_jtag_read_bytes+0x14`). Reverted to stdin path. RX state
  via passive `HB heap=%u rx=%lu` only. CYCLE gate therefore
  unreachable at runtime (cycle runs; phase-model discipline stands).
- CoC STATUS: GAP connects (held BTSess keeps BlueZ link),
  `COC accept/open status=0/slot`, ESP->laptop DATA PROVEN (729 B
  received, ATX frames on air). laptop->ESP data SYSTEMATICALLY LOST:
  PDU confirmed on air (btmon dlen 204, 1 credit), ESP
  `bytes=0/sdus=0`, no `RX sdu`, no credit updates, single-PDU sends
  clean (rc=0), multi-frame sends get ESP-initiated Disconnect
  (CID 65, 30 ms after 2nd PDU). Credit math sane (MTU512/MPS248 ->
  initial 3; recv_ready tops up per mbuf). No `COC nombuf` ever.
  Verdict: controller-side ACL-U RX pool never delivers (drop before
  host). `r_lld_update_rxbuf`/ISR/handler (log level raised to 5 via
  JTAG, readback-verified) NEVER print across boot/ambient/connect/
  send: the data-RX programmer is inert in all observed states.
  Live ip_funcs slots = ROM addrs (lld.o copies dormant).
  OPEN: who programs the NB<=9 data pool, and what recycles it
  (312d4.bit15 path), and whether ambient ADV-RX shares/drains it.
  Next: sub-MTU (50 B) probe, e0-descriptor-while-connected dump,
  NimBLE `disable_auto_credit_update`/SDU_BUFF_COUNT review.
- Rig mechanics: `reset halt` + single-core resume STRANDS cpu0 (app
  never boots; only ROM/PSRAM prints). Always plain `reset`.
  Post-flash silence needs one JTAG reset (esptool hard-reset leaves it
  needing a kick). pkill -f with the openocd cmdline MATCHES YOUR OWN
  SHELL (self-kill); use `pkill -x openocd`. USB re-enumeration moves
  ACM0->ACM1 (all scripts must take the node as a parameter -- TODO).
  `targets` state display unreliable; serial HBs + memory = truth.
  Single-word mdw while running now refused ("target not halted") --
  halt even for singles. Halt budget ~6-8 cpu1 halts per wedge; reset
  revives. FreeRTOS tick verified 110 Hz (healthy); slow serial =
  CDC-TX backpressure (printf-blocked loop), NOT slow clocks.
  `BTLIV` state to re-verify every boot: EM base, CS base (per-build
  ...674), mbuf addr, gate, ESFOC on air.

## 8. Session log 2026-09-19 (CoC-RX root cause: laptop framing)

- Direction-convention correction: in btmon `<` = HOST->controller
  (outgoing over air), `>` = controller->host (incoming). All prior
  "ESP-initiated disconnect" readings were INVERTED: every close was
  the laptop's own socket close (kernel Disconnect Request), ESP
  answers with Response. No spurious ESP kills, ever.
- JTAG channel-pool snapshot (pool @ per-build addr from `nm
  firmware.elf ble_l2cap_chan_mem`; entry 0x4C by next-chain;
  scid+8/mps+A/psm+1C/mtu+28/credits+2A/data_offset+2C verified
  against live values) after 1x50B send: credits 3->2 (PDU REACHED
  the host), data_offset=0x0100=256 = sdu_len parsed from pattern
  bytes `00 01`. Mechanism: kernel sends BASIC-style frames (no
  2-byte SDU length) -> host waits forever for 256B. Controller,
  NimBLE host, app all innocent.
- Why: coc.py never binds; kernel auto-transport still signals LE CoC
  but frames TX as BASIC. l2test (reference) frames correctly (wire
  `len 52 sdu 50`, header `32 00` prepended). BIND WITH LE TYPE FIXES
  IT: bind local `78:2B:46:BC:62:76` type LE_PUBLIC before connect ->
  kernel prepends SDU length. (`setsockopt L2CAP_MODE`: 0x80 had no
  effect on framing; 3=ERTM connects-but-dead; 4=STREAMING aborts.
  L2CAP_OPTIONS 11B struct -> EINVAL. l2test itself uses mode 0.)
- Constructive proof: `coc.py raw` with manual `3000`+48B -> ESP
  `RX sdu len=48`, `closed bytes=48 sdus=1`. Bidirectional CoC works;
  remaining work is laptop-side framing in coc.py (add LE bind).
- Rig: auto-cycle DEFAULT OFF now (`cycle_en=0`, serial dead so no
  runtime toggle) -> ADV stable across links. DEBUG host logs WEDGE
  the device (reverted; INFO is the max usable). xTickCount +
  chan-pool addrs MOVE EVERY BUILD (re-nm after each flash).
- RIG DOWN at close: app wedges ~50s after boot (tick frozen, 1 HB /
  3min, both cores report "running", JTAG reset ineffective).
  Documented recovery = PHYSICAL power cycle. JTAG halt budget +
  dual-core resume-order hazard suspected contributor (pool-dump
  halt preceded the wedge).

## 9. Session log 2026-09-19 p2 (CoC FULL DUPLEX proven)

- Laptop RX sweep (LE bind, FLASH3 RX-only build): 200 / 480 / 512 B
  all delivered (`RX sdu len=` each, multi-frame reassembly incl.
  MTU edge), FNV bit-exact vs laptop pattern (43cfa802../e2a6dd09../
  9432c614..). `coc.py` fixed in scratch: `l2bind()` (LE_PUBLIC
  source bind before connect) + LE_FLOWCTL note; `raw` mode kept for
  manual-framing probes (defaults BASIC).
- Full stack restore (FLASH4: `RX_ONLY_TEST 0` = PHY/DLE tune +
  auto-TX back, `cycle_en=0` kept): TX 8x480 = 3840 B FNV MATCH;
  DUPLEX on one channel: ESP->laptop 3840 B + laptop->ESP 3x200 =
  600 B sdus=3 interleaved in time (RX at 3-5 s inside ATX 8-15
  window), both FNV MATCH. CoC is FULLY FUNCTIONAL both directions,
  simultaneously, with tune enabled.
- Rig notes: flash USB-reset kills OpenOCD daemon (restart + JTAG
  reset needed post-flash); tick/chan-pool addrs move per build;
  physical reset recovered the ~50 s boot wedge; ADV stable with
  cycle off (no more TOG lottery).
