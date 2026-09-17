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
