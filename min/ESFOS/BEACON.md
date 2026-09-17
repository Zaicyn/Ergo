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

## 5. Ablation status

v3 = gate + CSx3 + {90,94,98,9C} + E0 + 11050. Load-bearing subset TBD
(group trials: timer-reg group vs E0 vs 11050). BlueZ NEW/DEL + serial
phase audit per trial; any blob restart leaves a serial fingerprint.
