# Blob-free beacon: EM control structure + trigger + RAM-steered TX

Board: Heltec WiFi LoRa 32 V4 (PIO target `heltec_wifi_lora_32_V3`), ESP32-S3.
Method: OpenOCD (espusbjtag caps_descriptor 0x2000, PID 1001) + PIO xtensa GDB
with `firmware.elf` symbols to disassemble BT-controller ROM + HW breakpoints
on REKICK-driven `adv_start`. All addresses verified live on silicon.

## 1. ADV control structure (instance 0)

CPU-visible DRAM @ `0x3FCAE664` (= EM base `0x3FCAE518` + `0x14C`), 90 B/instance.
Region reg `0x60031208` inverts to the same base. Contents (u16, live dump):

```
+0x00 0404  CNTL (SW-written by set_cs)
+0x02 0800  ?
+0x04 0000  ?
+0x06 e53a 699a 9070  BDADDR (air order 3A:E5:9A:69:70:90)
+0x0C bed6 8e89  access address 8E89BED6
+0x10 5555 0055  CRCINIT 555555
+0x14 0041  ?
+0x16 8027  ? (SW-written by adv_start)
+0x18 000b  TX-event count (HW-advanced; seen 0x000b)
+0x1A 0000
+0x1C 1400  ?
+0x1E 0000
+0x20 0008  ?
rest zero
```

## 2. Trigger sequence (GDB-trapped, PCs in ROM)

`r_lld_adv_start` (veneer `0x400040ec` -> real `0x400190b0`) and
`r_lld_adv_start_set_cs` (veneer `0x40005178` -> real `0x40018a18`):

| PC         | Store                  | Meaning              |
|------------|------------------------|----------------------|
| `0x40018b11` | `[CS+0x00] := 0x0404`  | CNTL (set_cs)        |
| `0x4001914c` | `[CS+0x16] := 0x8027`  | ? (adv_start)        |
| `0x40019190` | `[CS+0x18] := 0x0000`  | clear TX count       |

adv_start then programs the whole CS (BDADDR/AA/CRCINIT words observed:
`0xFFFFBED6`/`0xFFFF8E89`/`0x5555` literals) plus `ke_msg`-style task calls.
No absolute-MMIO doorbell exists in the ADV path: all programming is
shared-memory (CPU DRAM) + task messages.

ADV TX header pool @ `0x3FCAEDE8` (region `0x60031214`): `[+2] := 0x1020`
(PDU hdr: type + total len 16), `[+4] := len`. Trapped at `0x400169e4`
in real `r_lld_adv_adv_data_set` (`0x40016954`, via `ip_funcs` slot 95 ->
Espressif hack `r_lld_adv_adv_data_set_hack @0x40378e5c`).

## 3. Dead-vs-live register diff (kill = clear bit8 @ 0x60031000)

Idle (gate off) values revert to init; live values are written per adv_start:

```
0x60031090: 0020040d -> 00200408
0x60031094: 0002060f -> 00020407
0x60031098: 0f02060f -> 0f020407
0x6003109c: 0f02000f -> 0a020008
0x600310e0: 01be00fa -> 0190012c
0x60011050: 711e0320 -> 711e02d0
(0x6003101c differs: free-running timer, not causal)
```

Full v3 resume set (JTAG): gate `0x0010030f`, CS `0404/8027/0000`,
the six reg writes above. v1 (CS x3 only) verified INSUFFICIENT (no return).

## 4. RAM-steered TX (proven on air, btmon byte-exact)

- Single `mwb` to host ADV mbuf (`02 01 06 06 09 ESFOC`): `C->X`, `->Z`,
  `->W`, `->Q`, `->V`, `->U`, `->T`, `->S`, `->R`, `->L` all observed on air.
  The modem reads payload bytes from the host DRAM buffer (only copy in
  480 KB DRAM sweep); no EM payload copy exists.
- Full blob-free beacon: kill (clear bit8, BlueZ `DEL` observed) ->
  poke marker `ESFOL` into fresh mbuf (found while halted) -> v3 writes ->
  `NEW Device 90:70:69:9A:E5:3A ESFOL` on air with no blob phase
  (no REKICK/RES/ADV-start on serial) in the window. The blob can only
  emit `ESFOC`, so the marker return excludes blob involvement.
- REKICK (every ~64 s) reallocates the mbuf from the flash `"ESFOC"`
  literal (`start_adv()` in `esfnode.c`), ending any poke. Operational
  loop: after each `ADV start rc=0`, re-scan DRAM for `02 01 06 06 09`,
  re-poke. mbuf alternates between a few heap addresses.
- CS BDADDR poke (`0x90->0x91`): no on-air effect, reverted next adv_start
  (per-cycle copy from transient mbuf @`0x3FCAE240`, trapped at `0x4001937d`).
  Persistent AdvA spoof needs the efuse-shadow source (open).

## 5. Ablation: two redundant arming paths (COMPLETE, reset-controlled)

Method (hard-won): every trial = halt, force ALL of {gate,E0,90s,11050}
to idle with readbacks, drain, write ONLY the trial subset with
readbacks, resume, fresh BlueZ scan (neighbors as scanner control),
post-hoc audit (mbuf addr/content + reg readbacks detect RES/REKICK
intrusion; intruded trials are void, retried). APP loop phases
(TOG/RES/REKICK) are the confound: RES resets E0+90s+11050 to idle,
REKICK reallocates the mbuf + restarts via blob, TOG-RMW preserves.
Early trials without idle-forcing inherited unknown leftovers; only
the reset-controlled matrix below is trustworthy.

Matrix (gate SET in every row; CS/pool/mbuf always intact):

| E0        | 90s  | 11050 | result |
|-----------|------|-------|--------|
| idle      | idle | idle  | dead (C0 control) |
| full      | idle | idle  | dead (frozen trial, audited) |
| full      | live | idle  | dead (AF frozen + audited) |
| full      | idle | live  | ALIVE (B, phase-model clean) |
| full      | live | live  | ALIVE (v3 control) |
| idle      | live | live  | ALIVE (I: NEW 5 s post-stores) |
| idle      | idle | live  | ALIVE (J3: full readbacks + audit) |
| bit0-only | idle | idle  | ALIVE (K: full readbacks + audit) |

Reading: 11050-live alone suffices (J3); E0.bit0 alone suffices (K);
E0-full alone fails; E0-full+90s fails; 90s never help nor are needed.
**Gate + 11050-live and gate + E0.bit0 are two REDUNDANT arming paths**
(OR-gate). The 90-group is pure don't-care. CS necessity untested
(CS was never broken; zeroing it is future destructive work).

Minimal resume, either (from full idle):

```
mww 0x60031000 0x0010030f   (gate bit8)
mww 0x60011050 0x711e02d0   (path B; idle/init 0x711e0320)
```
or
```
mww 0x60031000 0x0010030f   (gate bit8)
mww 0x600310E0 <idle | 0x01>  (path A; E0 bit0, readback sticks)
```

Notes: the baseline "armed" E0 (`0x0190012c`, bit0 CLEAR) works only via
path-B leftovers in old trials; under reset-control full-E0 never
resumed anything by itself. E0.bit0=1 with everything else idle resumes
(K), so bit0 is the true E0 trigger, not a leftover artifact. E0 has no
read side-effects (readback-verified throughout). 0x60011050 is a BT
baseband reg (init programs `...0320`); its live `...02d0` bits TBD.

Bit-narrowing history (how bit0 was found; early rows predate
reset-control, superseded by the matrix where they conflict): C0
(gate+E0:=idle) dead; H (high half `0x019000fa`) dead; L (low half
`0x01be012c`) RETURN (with live leftovers); L1 (idle+bits{0,2}) RETURN
(same caveat); B2 (bit2 alone) dead; B0R/K (bit0 alone) RETURN, K under
full reset-control with audit. Lesson learned mid-battery: a dropped
kill/idle readback voids a trial (two redos); phase-model + post-hoc
audits arbitrate every verdict.

Ops note: repeated JTAG halt/resume skewed the app loop ~10x slow
(HB cadence degraded, tick-skew suspected) starting ~02:05. Harmless for
JTAG-driven trials (fewer phase confounds); REKICK still fires.
If the loop wedges fully, the BOOT+RST dance in the brief applies.

## 6. Instance-1 mapping + body-link verdict (MAPPING COMPLETE)

Instance model (from ROM disasm + live traps): CS array stride 90 B
(`F()+90*idx`, F = call `[ENV+188]` = `0x3FCAE664` for idx0), adv-data
pool stride 126 B (pool0 @ `0x3FCAEDE8` = region `0x60031214`).

Read-only recon, all verified on silicon:
- CS1 @ `0x3FCAE6BE`: zeros except `+0x02=0x0001`, `+0x5C=0x0002`.
  CS0 `+0x5C=0x0001`: **+0x5C is the instance index** (init-tagged).
- pool1 @ `0x3FCAEE66` (`0x3FCAEDE8+126`): all zeros.
- `lld_adv_env @0x3FCEFCB0`: only slot0 (`0x3fcebc68`); no idx1 struct.
- inst0 @`0x3fcebc68`: flags `[+116]=0x0013`, fn ptrs (`0x40004038`,
  `0x40379148`), misc params. Reference for crafting idx1 params.
- `ip_funcs` slots: frm_cbk `0x1B4`->veneer `0x4000405c` (ROM),
  frm_isr `0x1B8`->`r_lld_adv_frm_isr_eco @0x4037917c` (IRAM override).
  ECO ISR disassembled: per-event bookkeeping + callback dispatch only
  (tolerates NULL instance: `beq` skips), NO DMA programming.

Body-link verdict: the CURRENT host mbuf address (`0x3FCB09F0`) appears
in NO dump (EM/CS/pools/inst/host-heap, exhaustive LE-u32 search).
No static CPU-visible pointer to the TX body exists. The modem DMAs the
body straight from the host mbuf; the address travels per-event via the
task/ISR path into modem-private state. Consequence: instance 1 cannot
reuse "the host mbuf mechanism" (no mbuf will ever exist for handle 1);
live instance-1 TX needs the per-event DMA linkage first.
Side finding: EM+0x000 16-entry table (w1 ~0xCC stride, churning,
w2 0x3a->0x4d over 7 min) reads as the RX descriptor ring
(16 RX buffers, recycled on SCAN_REQ RX; N=16 matches
"EM DATA RX BUFFER[%d]"). Medium confidence, untested.

Proposed next: trap ROM `frm_cbk` per-event (resolve veneer `0x4000405c`
first) to find the DMA/body programming, then attempt live instance-1
TX (CS1 + pool1 + gate/E0 trigger, second name/address on air).

## 7. Body-link mechanism: T1 confirmed (modem reads host mbuf live)

Two theories: (T1) modem DMAs the host mbuf per event/continuously;
(T2) modem reads a per-REKICK-filled FIFO, pokes working only via the
next REKICK's copy. Discriminator: poke marker `ESFOJ` at `0x3FCB6E8C`,
sight on air (`NEW ... ESFOJ`), then re-read the mbuf. Result: mbuf
STILL HOLDS the poked bytes (`...4a 4f`). REKICK always reallocates +
recopies `ESFOC` from flash (10+ observations), so an intact poked mbuf
proves NO REKICK ran between poke and sighting. The modem transmitted
the poked bytes with zero fields-set/HCI traffic. **T1 CONFIRMED, T2 dead.**
Consequence stands: control mbuf bytes -> control air bytes, no blob,
no REKICK needed (re-poke per cycle as the mbuf reallocates).

frm_cbk (veneer `0x4000405c` -> ROM `0x4001828c`): pure dispatcher
(switch on event type -> `ip_funcs` slots `0x1B8/0x1BC`/ENV+12 calls).
NO DMA/body programming. `lld_adv_end_ind_handler_hack @0x4202dfac`:
event reporting to host, also no MMIO. The body fetch is fully
modem-autonomous; no per-event or per-REKICK CPU body programming
exists anywhere in the ADV path (adv_start, adv_data_set, frm_cbk,
frm_isr ECO, end_ind all disassembled and clean).

## 8. Ops: wedges, slow loop, JTAG reset recovery

- After ~40 halt/resume cycles + a B-12 pool clobber (byte-exact restored)
  the rig degraded on three axes at once: app loop ~10x slow then silent,
  serial CDC silent (host `select` empty, no error), BT scans deaf. JTAG
  (same USB device) stayed fully functional throughout -> wedge was NOT
  the USB device as a whole.
- Serial silence with PC=idle (scheduler alive) + no HBs = app task
  blocked/starved, not a halt. Likely contributors: tick-skew from
  repeated halts, red-zone state from the clobber window.
- Recovery: OpenOCD `reset` (soft reset, both CPUs) + `resume` boots the
  app cleanly from flash (ESP-ROM banner, same heap 2341776, ADV back in
  seconds). This also cleared the CDC wedge and the slow loop. No BOOT+RST
  dance needed (that is only for post-flash stub stranding).
- Lesson: always verify kill by gate readback; never split scan+poke
  across running windows (parse while halted); background serial readers
  die in this environment (use foreground reads); distrust empty scans
  without neighbor sightings as control.

## 9. Scan-rsp recon: dormant, mbuf-gated (RECON COMPLETE)

Baseline: modem auto-responds to SCAN_REQ with SCAN_RSP, Data length 0
(btmon-verified). `[inst+128]` (scan tracking, @`0x3FCEBCE8`) reads 0;
firmware never sets scan-rsp (start_adv sets adv fields only).
ROM `r_lld_adv_scan_rsp_data_set` (`0x40016BE8`, via hack `0x40378ec8`)
mirrors adv_data_set (header word with PDU-type nibble `|4`, len store);
instance struct holds separate adv (`+126`) and scan (`+128`) fields.

Live tests (all reverted afterward, rig pristine):
- `[inst+128] := 10` alone: SCAN_RSP still length 0 (len not from inst).
- Full scan record (PDU `0x1024`, len 10, AdvA + ESFO2 AD record) at
  pool1 (`0x3FCAEE68`, zeros, safe): SCAN_RSP still length 0.
- Full scan record at B-12 (`0x3FCAEDDC`): COLLIDED with adv pool header
  (`B+0..B+7`), ADV broke; restored byte-exact from pre-write dump,
  ADV verified back. (B-12 is NOT a separate scan slot.)
Verdict: scan body is mbuf-gated exactly like adv (no scan mbuf exists
-> pool writes ignored, len stays 0). Second payload via scan-rsp needs
the same modem-private latch as instance-1. Time-slicing the single
adv mbuf remains the bounded second-payload path.
