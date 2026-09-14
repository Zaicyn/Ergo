# ESFOS v1 — filesystem layout draft (STATUS: DRAFT, unimplemented)

A from-scratch filesystem for the Heltec-class boards, built from our
allocation schemes. No third-party FS. Flat namespace, fixed pools,
append-mostly workload. Flash driver (raw read/page-write/sector-erase
primitives) is the one allowed external dependency.

## Flash physics assumed (driver contract)

- Read: byte-addressable, arbitrary length.
- Write: bits go 1→0 only, 256 B pages (write must not cross pages
  without care; driver handles alignment, FS aligns to pages).
- Erase: 4 KB sectors, resets to 0xFF. ~100k endurance per sector.
- Power loss at any instruction boundary is possible (the emulator
  will cut there).

## Regions (offsets in sectors, 4 KB each)

```
0            superblock (redundant copy at 1)
2 .. 3       slot pool: metadata/inodes (SQ4 geometry, fixed slots)
4 .. 5       journal ring (append-only intent records)
6 .. 9       audit log file (hash-chained, append-only)
10 .. N      data extents (file contents, extent lists in slots)
N+1 .. N+2   spares (bad-sector replacement + tombstone overflow)
```

Sizes are v1 placeholders for ≤ 1 MB partitions; scale by geometry,
not by code changes (all region bounds live in the superblock).

## Superblock (sector 0, copy at 1)

Magic `0x45534653` ("ESFS"), version u16, geometry (region bounds,
slot count, sector size), journal head offset, root generation
counter, splitmix64 checksum over the preceding words. Mount reads
both copies, takes the higher valid generation (ties → sector 0).
A superblock with a bad checksum is treated as unwritten, never as
data — same rule as torus validation (recompute-and-compare).

## Slot pool (inodes are slots)

SQ4 geometry transplanted 1:1: bins × ring, per-bin head pointers,
SCATLT scatter on hot-bin overflow with cold-probe recovery,
tombstone magic on delete, frozen flags reserved. Slot content:

```
offset  size  field
0       4     invariant: pack(bin, gen, type) — position stamp
4       4     size_bytes (file length, data region)
8       4     extent_head (index into extent table / first extent)
12      4     journal_seq (last intent touching this slot)
16      4     flags (tombstone / frozen / reserved bits)
20      12    name (11 chars + NUL; flat namespace, v1)
32      ...   pad to slot stride (64 B slots: 2 per 128 B row)
```

Detection is trivially perfect on stored metadata (same argument as
bench_sq4.c: stamps are recomputed from coordinates). Scrub =
recompute-and-compare over all slots at mount (fast: pool is small).

## Data extents

Per-slot extent list (v1: up to 4 extents inline in an extension
slot chained from extent_head; files are small — scripts and logs).
Each extent: `(start_sector, sector_count)`. Free space is a
free-extent ring (LIFO stack of reclaimed runs + a bump pointer
into never-written space; coalesce on free — v1 may skip coalescing
and note fragmentation, since our files are append-only and few).
Claim path mirrors `sq4_fal` (hint → head → cold probe).

## Journal (write-ahead intents)

Record: `[seq u32][op u8][slot u16][len u16][payload][crc32-ish S0/S1]`.
Ops: `INTENT_WRITE` (file bytes staged), `COMMIT` (extents linked
into the slot), `INTENT_DELETE`/`COMMIT_DELETE`. Mount replay: scan
from journal head; intents without commits are rolled back (their
staged bytes are simply unlinked — nothing ever overwrote live
data, because staging writes go to fresh sectors first). Journal
ring rotates, which distributes wear across its sectors for free.

## Audit log

Append-only file with per-line `seq` + `prev_hash` (splitmix64
keyed tag over previous line hash, same primitive as the keyed
transport tags). Verification replays the chain; first break marks
the tamper point exactly. Written by the dispatcher on every
mutating op and every repair event.

## Wear policy (workload-matched, not general)

- Journal + audit + logs rotate through rings (wear spreads by use).
- Scripts/config (write-rarely) sit static — no wear concern.
- No general wear leveling in v1: stated scope cut. The emulator
  counts erases per sector so skew is measured, not assumed.
- Bad sectors: detected by failed erase/verify → tombstoned into
  the spare region, remapped once (no second chances at this size).

## Explicitly out of scope (v1)

Directories (flat `/s`-style namespace), POSIX semantics, general
fragmentation GC, adversarial wear leveling, files > extent-list
capacity, multi-writer concurrency (single dispatcher owns the FS).

## Test plan (mirror discipline)

1. Portable C implementation against a RAM-backed fake flash with
   power-cut fault injection (cut at random instruction points in
   mutating ops; mount must always recover to a valid state).
2. Host-side exhaustive verification first; device port second.
3. Differential runs against LittleFS (same op scripts, compare
   observable behavior, not internals).
