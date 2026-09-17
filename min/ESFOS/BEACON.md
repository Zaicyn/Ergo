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

## 5. Ablation: the load-bearing write is E0 (COMPLETE)

Kill = clear bit8 (BlueZ `DEL` observed 2x, gate readback-verified each
trial). Trials (kill -> 8 s drain -> subset stores -> 20 s BlueZ scan;
slow app loop ~10 min/phase at the time => no blob phase fits in a trial;
any blob restart would print REKICK/RES/ADV-start on serial):

- v1 (gate + CSx3): NO return (2x).
- T2 (gate + CSx3 + 90/94/98/9C): NO return (2x, second with serial audit).
- T3 (gate + CSx3 + E0): RETURN (2x, second with serial audit).
- M1 (gate + E0, NO CS stores): RETURN, serial shows only HB + periodic
  REG dump (no restart fingerprint).

Pattern: E0 absent -> dead; E0 present -> alive. Minimal resume set:

```
mww 0x60031000 0x0010030f   (gate bit8)
mww 0x600310E0 0x0190012c   (event arming; idle/init value 0x01be00fa)
```

TWO WRITES. The CS stores were belt-and-braces (CS is never broken by
the kill). 90/94/98/9C and 11050 differ dead-vs-live but are NOT needed
to resume (likely HW-updated consequences, or reprogrammed lazily).

## 6. E0 bit ablation: bit0 is the arming bit (COMPLETE)

Idle `0x01be00fa` vs armed `0x0190012c`: 10 differing bits
{1,2,4,6,7,8,17,18,19,21}. Every trial kill-verified by gate readback
(a dropped readback once voided two trials; redone properly):

- C0 (gate + E0:=idle): dead (control).
- H (high half `0x019000fa`): dead.
- L (low half `0x01be012c`): RETURN.
- L1 (idle + bits{0,2} = `0x01be00ff`): RETURN.
- B2 (bit2 alone = `0x01be00fe`): dead.
- B0R (bit0 alone = `0x01be00fb`): RETURN, with BlueZ `DEL` then `NEW`
  inside one scan and HB-only serial (no blob fingerprint).

Minimal resume, final form:

```
mww 0x60031000 0x0010030f   (gate bit8)
mww 0x600310E0 <idle | 0x01>  (set E0 bit0; readback sticks, level arm)
```

E0 bit0 alone is sufficient; the other 9 differing bits, the CS words,
and the 90-group/11050 are all don't-care for resume. Note the baseline
armed value has bit0 CLEAR yet also resumes, so bit0 is one sufficient
arming path, not the exclusive one; E0 has no read side-effects observed
(readback-verified after every write).

Ops note: repeated JTAG halt/resume skewed the app loop ~10x slow
(HB cadence degraded, tick-skew suspected) starting ~02:05. Harmless for
JTAG-driven trials (fewer phase confounds); REKICK still fires.
If the loop wedges fully, the BOOT+RST dance in the brief applies.

## 7. Instance-1 mapping + body-link verdict (MAPPING COMPLETE)

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

## 8. Body-link mechanism: T1 confirmed (modem reads host mbuf live)

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
