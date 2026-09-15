# BLOBS — binary-object inventory (checkable, not vibes)

Policy: the end state is ZERO precompiled objects. Blobs are
unacceptable and tolerated only where no open path exists yet;
every entry below is either eliminated, scheduled for elimination
with a named mechanism, or the single documented exception under
active replacement. A blob appearing here that no feature needs
is a bug. Regenerate with the commands at the bottom; do it per
release build.

Status of 2026-09-15 (`esfnode` skeleton, ESP-IDF 5.5, S3):

## Eliminated

| object | how |
|---|---|
| `esp_coex/.../libcoexist.a` (was: 601 objects) | `# CONFIG_ESP_COEX_SW_COEXIST_ENABLE is not set` in `esfnode/sdkconfig.defaults` (+ board-specific copy — PIO prioritizes `sdkconfig.<env>`). Nothing to arbitrate with no WiFi. Rebuilt, relinked, map shows zero references; device boots clean with identical heap/PSRAM numbers. |

Caveat: BT stack not started yet in the skeleton — if NimBLE
bring-up proves to need coexistence symbols, this row moves back
with the error attached. Verify at radio_if bring-up, not assumed.

## Linked into our binary today (BT active, CoC verified)

| object | members linked | pulled by | needed? | basis / removal |
|---|---|---|---|---|
| `bt/controller/.../libbtdm_app.a` | 7242 | NimBLE controller (radio_if bring-up) | **THE documented exception** | Closed; framework grant, used unmodified, drives RF silicon only. Replacement path: nRF+Zephyr coprocessor behind the same `radio_if.h`. |
| `esp_phy/.../libphy.a`, `libbtbb.a` | 1164 + 101 | RF calibration at BT bring-up | same exception | Same basis; arrived together as predicted, nothing else did. |
| `xtensa/.../libxt_hal.a` | 11 | toolchain HAL | yes (for now) | Next candidate after radio settles. |
| `libgcc.a` | 212 | compiler runtime | yes | Standard. |

Still absent (re-verified this build): `libcoexist.a` (stays out —
BT works without it), all WiFi libs, mesh, OpenThread.

## Arriving with next features (declared in advance)

| object | arrives when | basis |
|---|---|---|
| `bt/controller/.../libbtdm_app.a` (+ `_flash`) | first NimBLE use (radio_if bring-up) | **The single documented exception.** Closed controller blob; framework grant covers redistribution unmodified. Never modified, never linked statically into our logic — it drives RF silicon behind `radio_if`. |
| `esp_phy/.../libphy.a`, `libbtbb.a` | RF calibration at BT bring-up | Same basis as above; verify they stay the only additions. |

## Never linked (verified absent from our map)

`libpp.a`, `libnet80211.a`, `libcore.a`, `libmesh.a`, `libespnow.a`,
`libsmartconfig.a`, `libwapi.a`, `libble_mesh.a`, `libopenthread_*`
— no WiFi, no mesh stack, no OpenThread. If any appears in a future
map, something enabled WiFi by accident; kill it.

## Clean paths (no blobs at all)

- **SX1262 LoRa via RadioLib**: register-configured silicon, open
  drivers. Blob-free today; the no-compromise bearer.
- **nRF52811/52840 + Zephyr**: fully open BLE stack (Apache-2.0),
  zero blobs, behind the same `radio_if.h`. The clean-room
  replacement if the documented exception ever becomes
  unacceptable. No application code changes by design.
- **NimBLE host itself**: Apache 2.0, builds from source
  (re-verify on each version bump; it arrived via Arduino package
  manager, so pin the version in-tree when vendored).

## Regenerate this file

```
# from the esfnode build dir:
grep -oE "lib[a-z_]+\.a\([a-zA-Z0-9_]+\.o[a-z]*\)" esfnode.map \
  | sed 's/(.*//' | sort | uniq -c | sort -rn
# any NEW precompiled archive vs the table above = stop and explain
```

License note (honest scope): ESP-IDF ships Apache-2.0; the BT
controller objects ship inside that distribution used unmodified.
That reading covers development and documented evaluation. Before
anything product-shaped ships, re-verify the exact grant text
against a release checklist — this file tracks *what* is linked so
that check is mechanical, not archaeological.
