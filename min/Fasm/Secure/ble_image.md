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

## Tooling to install (not yet)

- PC: raw L2CAP sockets (`AF_BLUETOOTH`, `SOCK_SEQPACKET`,
  `BTPROTO_L2CAP` — stdlib, no `bleak`; bleak is GATT-only and
  can't do CoC) + `btmgmt`/`bluetoothctl` for adapter setup.
- Heltec: NimBLE-Arduino or Bluedroid L2CAP CoC APIs (server
  endpoint + credits — verify exact API surface at build time;
  this is the one integration risk, flagged now); new sketch
  (separate from espfs — display + BLE roles differ).
