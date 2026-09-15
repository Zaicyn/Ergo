# BLOBS — binary-object inventory (checkable, not vibes)

Policy: every precompiled object in our binaries is listed here with
what pulls it in, whether it is needed, and the path to removing it.
A blob appearing here that no feature needs is a bug. Regenerate with
the commands at the bottom; do it per release build.

Status of 2026-09-15 (`esfnode` skeleton, ESP-IDF 5.5, S3):

## Linked into our binary today

| object | members linked | pulled by | needed? | basis / removal |
|---|---|---|---|---|
| `esp_coex/.../libcoexist.a` | 601 | BT enabled (auto) | MAYBE NOT | Apache-2.0 framework grant, used unmodified. Attempt removal: disable coexistence (no WiFi in our config to arbitrate) and re-verify link. Open item. |
| `xtensa/.../libxt_hal.a` | 11 | toolchain HAL | yes (for now) | Compiler/HAL adjacent; open equivalent exists upstream. Watch item, not alarm. |
| `libgcc.a` | 212 | compiler runtime | yes | Standard toolchain runtime. |

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
