# BLE image forwarding — spec (STATUS: SPEC, unbuilt)

Ship LFC-compressed images PC ↔ Heltec over BLE, reusing the
transport stack (codec units, parity, commitment, fetch) with a
smaller MTU. No new math; new bearer + framing.

## Endpoints (verified present)

- **PC:** `hci0`, Bluetooth 5.1 (HCI ver 11), LE + advertising +
  secure-conn supported, BlueZ 5.87. Acts as GATT central (connects
  to the Heltec). Scripting via `bleak` (to install). Datastreams:
  yes — BlueZ management + GATT client + our Python harnesses.
- **Heltec V3:** ESP32-S3 BLE 5.0 peripheral (advertises). No
  Classic/A2DP/SPP in silicon — GATT notifications (≈244 B with
  MTU/DLE) or L2CAP CoC. Firmware: NimBLE-Arduino or Bluedroid
  `BLEDevice`, new sketch (not espfs — separate role).
- Direction v1: PC → Heltec (forward image to the device; display
  on OLED or store to LittleFS). Heltec → PC later (same protocol,
  roles flipped per characteristic).

## Size math (measured LFC files, not estimates)

| image | raw | LFC file | ratio |
|---|---|---|---|
| 800×800 test 1 | 1.92 MB | 334 KB | 5.7× |
| 800×800 test 2 | 142 KB file | 142 KB | 13.5× |
| 480p start target | 1.23 MB | ~90–215 KB (projected) | — |
| OLED frame 128×64 mono | 1 KB | ~1 KB | — |

At 100–300 kbps real BLE throughput: OLED frame = fractions of a
second; 480p LFC = ~4–20 s per frame. Start at OLED size for the
loopback proofs, then 480p. 720p when 480p is boring.

## Pipeline (unchanged parts stay unchanged)

```
LFC file → 512 B codec units + P+Q parity (pktcore, as-is)
         → sub-chunk to ~220 B BLE payloads
         → GATT notify stream → reassemble → repair → OLED/LittleFS
```

Loss mapping (already measured): one lost notification ≈ a 220 B
hole ≈ a burst inside a 512 B unit → our BU cells apply directly.
Missing-chunk re-request is the parity-fetch handshake with a
smaller MTU. Commitment (`ktag` over P+Q) rides in META, unchanged.

## GATT layout (custom 128-bit service, v1)

Base UUID pattern `E5F5xxxx-....` (document exact on implement):
- `META` (read): frame descriptor — magic, W×H, LFC version,
  total units, total chunks, commitment (64 B tag over P+Q).
- `CTRL` (write, central→peripheral): `START`, `FETCH <bitmap of
  missing chunk idx>`, `ABORT`. Responses as notifications on STAT.
- `DATA` (notify, peripheral→central or reverse by direction):
  `[frame u16][chunk u16][total u16][payload ≤220 B]`.
- `STAT` (notify): `GOT <bitmap-ish range>`, `DONE`, `ERR <code>`.

## Transport: L2CAP Credit-Based CoC (primary)

Mode support (checked): PC hci0 is BT 5.1, Heltec BLE 5.0 — both
clear the BT 4.1 bar for basic LE Credit-Based CoC; neither reaches
5.2, so ECFC (multi-channel/QoS) is out. Common denominator is one
basic LE CoC channel per direction, which is all v1 needs.

Why CoC over GATT writes/notifications here:

- **Headroom:** no ATT framing per packet (no opcode/UUID/length
  tax), larger SDUs with segmentation handled below us — typically
  20–50% more goodput than notifications in practice.
- **Control:** credit-based flow control is receiver-paced
  backpressure for free. The Heltec has iffy-hundred-KB RAM; credits
  mean the sender *cannot* overrun it, where blind writes would need
  an app-level throttle we then have to debug.
- **Symmetry:** bidirectional channels kill the direction problem —
  image bytes one way, FETCH bitmaps back the other, no role swap,
  no primitive change between v1 (PC→Heltec) and reverse.
- **Loss model change (honest):** a CoC channel is reliable +
  in-order (link-layer retransmits), so losses become *stalls*,
  not holes — our parity drops to second line of defense and the
  FETCH path fires rarely. Keep both: stalls cost latency (still
  measured), and residual corruption still lands as erasures.

Keep one minimal GATT service anyway: advertising + discovery +
PSM exchange + META read (parameters and commitment are small,
infrequent, and GATT-shaped). Bulk bytes ride CoC; everything
else stays where it is. GATT writes remain the fallback if CoC
proves painful (documented, not deleted).

Framing over the SDU stream (same headers, bigger payloads):
`[frame u16][chunk u16][total u16][payload ≤ 480 B]`, chunks
numbered so reassembly is order-independent anyway (cheap
insurance against channel weirdness).

## Transfer protocol (mirrors the promise design)

1. Central reads META (frame parameters + commitment).
2. Central streams chunks (write-without-response or CoC).
3. Peripheral reassembles units, runs SEC per unit, notes missing.
4. Peripheral requests missing chunks via STAT/FETCH (bitmap).
5. Central re-sends; peripheral rebuilds via P+Q if erasures ≤ 2,
   else requests again (bounded retries, then FAIL).
6. Commitment verified over rebuilt parities; `DONE` iff frame
   byte-exact (known-answer check against LFC header/trailer).
7. Render to OLED (128×64 path) or store to LittleFS (full frames).

## Test plan (in order, each gates the next)

1. **Host-side loopback:** LFC file → chunk → simulated BLE loss
   (drop 1–5% notifications) → reassemble → repair. Pure Python,
   no hardware. Asserts full recovery + byte-exactness.
2. **OLED-size over air:** 1 KB frame PC→Heltec, display it.
   Photograph the screen. Proves the whole path end-to-end.
3. **480p over air:** ~90–215 KB, timed; measure goodput vs loss
   rate, compare against the demand-model predictions.
4. **Reverse + larger:** Heltec→PC, then 720p.

## Measured: CoC bring-up (2026-09-15, loopback bench)

- Firmware: NimBLE-Arduino 2.5.1, `NimBLEDevice::createL2CAPServer()`,
  PSM `0x81`, MTU 512, `COC-SRV-OK` on boot. Requires
  `-DCONFIG_BT_NIMBLE_L2CAP_COC_MAX_NUM=4` (default 0 = compiled
  out — silent, no error). API notes: server callbacks take
  `(NimBLEServer*, NimBLEConnInfo&[, int])`; never block in
  `onRead` (it runs in the NimBLE task — a blocking echo deadlocks
  the stack; count in the callback, report from `loop()`).
- PC: hci0 (BT 5.1) + BlueZ 5.87. Python stdlib sockets **cannot**
  open LE CoC (no address-type field — always EHOSTDOWN);
  `l2test -V le_public -P 129` is the tool (`-V` is mandatory,
  and `-N` is frame count while `-n` is a *mode* — that typo cost
  an hour). Python can still drive `l2test`/raw-HCI later; stdlib
  alone cannot.
- Results: channel opens first try thereafter; MTU 512 negotiated
  both ways; **100/100 SDUs delivered (22000 B, zero loss)**;
  ~35–60 kbps with untouched connection parameters.
- Tuning round (measured, no gain): peripheral requested 2M/2M PHY,
  251-octet data length, 15–30 ms interval — all calls returned 0
  (HCI accepted locally) but **no completion events ever arrived**
  (no CONN_UPDATE / PHY_UPDATE / DATA_LEN completions in the GAP
  event log). Throughput unchanged at ~50–55 kbps. Reading: the
  central (BlueZ, no root here) never completes peripheral-
  initiated PHY/interval/datalen procedures, so requests are
  sent-and-ignored. Unblocks, in order: (1) central-side setup
  (`btmgmt phy`, conn-interval policy — needs root/CAP_NET_ADMIN,
  unavailable in this environment); (2) verify our GAP event
  callback isn't shadowed by NimBLE-Arduino's internal dispatcher
  (raw `ble_gap_set_event_cb` may conflict — untested);
  (3) 480 B SDUs measured identical rate (42–55 kbps), ruling out
  per-SDU overhead as the binding constraint — the binding
  constraint is per-connection-event airtime, i.e. interval+PHY,
  i.e. items (1–2). Log silencing (`CORE_DEBUG_LEVEL=0`) kept
  (correct hygiene, no measurable gain at these rates).
- Interval note (external reference + our probe): a published
  analysis hits ~1400 kbps with 247 B payloads, DLE, 2M PHY, and a
  400 ms interval — the interval cancels in their math *if* the
  sender saturates every event (287 packets/event amortizes IFS).
  We probed flat-400 ms: no GAP completion (ungranted, as above)
  and slightly worse numbers (27–89 kbps, volatile) — expected if
  granted, since our sparse test pattern would leave 400 ms of dead
  air between small bursts. Long intervals reward saturated senders
  and punish sparse ones; tuning blind to saturation is futile.
  Restored 15–30 ms request as default. Separate cost to log: long
  intervals also inflate round-trip latency, which our fetch
  handshake pays per round — throughput and latency want opposite
  intervals here, another reason to keep the default until the
  sender saturates.
- SDU-size sweep at fixed count (all byte-exact): 100 B at 35 kbps,
  220 B at 45, 480 B at 49, 512 B at 44. Larger SDUs help modestly
  (+40% to 480 B) then plateau at the MTU edge — consistent with
  per-event airtime binding, not per-SDU overhead. 480 B is the
  working size until parameters move.
- GATT side note: reads, notifications, discovery, and connect all
  work; GATT *write-request* fails `NotSupported` against this
  stack (flags+permissions set correctly — root cause not chased,
  since CoC supersedes writes in this design; GATT stays for
  META/discovery only).

## Measured: first image over CoC (2026-09-15, file framing)

Framed-stream protocol (v1, implemented + verified): 20 B header
`[magic "ESIMG0" (6)][total_len u32 LE][expected FNV-1a64][rsv 2]`
then raw payload SDUs. Parser is restart-safe (header re-arms a new
transfer; state survives across CoC connections, reset only by a new
valid header). No reassembly buffer: payload streams straight to a
LittleFS file with a running FNV; completion declared when bytes
reach total, verified against the header hash (`match=1` iff
byte-exact).
- **OLED frame (1024 B): `match=1`, both FNV halves exact.** First
  image over BLE, end to end.
- `l2test -B` sends a whole file as ONE SDU: anything over the 512
  MTU dies at the first SDU (observed: header parses, then silence).
  Application chunking is mandatory — 480 B SDUs verified working.
- Per-connection state reset is a bug, not a feature: clearing
  parser state on CoC open breaks multi-connection transfers
  (`bad-header` on chunk 2+). State belongs to the transfer
  (header), not the connection.
- Arduino cannot see PSRAM on this board (`getPsramSize()=0` —
  board JSON lacks `memory_type`, so sdkconfig leaves SPIRAM off).
  Streaming-to-LittleFS adopted instead of buffering; revisit under
  ESP-IDF where octal PSRAM is explicit. (480p framebuffer at 1.2 MB
  wants real PSRAM — one more reason for the ESP-IDF move below.)
- OPEN, unsolved: custom C sender (`SOCK_SEQPACKET` + correct LE
  address type in `sockaddr_l2`) connects cleanly and `send()`
  succeeds, but zero bytes arrive; `l2test` on the same channel
  delivers. Not MTU, pacing, staleness, or TUNE interference
  (all eliminated). Suspect: socket options BlueZ sets implicitly
  (credits/MPS negotiation path) — needs `strace`/source read of
  `l2test -s` to close. 480p transfer waits on this or on
  chunk-per-`l2test`-invocation (too slow: ~3 s setup each).

## Tooling (measured path, updated)

- PC: `l2test -V le_public` for manual transfers (stdlib sockets
  cannot address LE CoC); `bluetoothctl` scripted for scan/connect;
  `btmgmt` needs root (unavailable — D-Bus paths only).
- Heltec: NimBLE-Arduino 2.5.1, verified API surface
  (`createL2CAPServer`, `createService(psm, mtu, cb)`,
  `onRead`/`onConnect`/`onDisconnect`, `COC_MAX_NUM` define).
  New sketch per role (separate from espfs).
