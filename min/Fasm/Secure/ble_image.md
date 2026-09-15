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

Direction v1 is PC→Heltec, so PC writes CTRL and consumes STAT
while Heltec notifies DATA... note the inversion: DATA flows
PC→Heltec, which over BLE means Heltec must *receive* — use CTRL
writes carrying chunk payloads for v1 (write-without-response,
221 B ATT payloads), and reserve notify-DATA for the Heltec→PC
direction. Simpler alternative if write throughput disappoints:
L2CAP CoC (credited stream, both directions symmetric). Decide by
measurement; spec both, implement writes first.

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

- PC: `bleak` (pip) for GATT scripting.
- Heltec: NimBLE-Arduino (PlatformIO lib) or Bluedroid; new
  sketch (separate from espfs — display + BLE roles differ).
