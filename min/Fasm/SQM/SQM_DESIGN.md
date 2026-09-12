# SQM — moment-Merkle minimal-read writes

2026-08-27. User prompt: "Look at how ESF handles its data integrity
checks. We could basically make an almost constant time version by
minimal reads couldn't we? Sort of like hamming or reed codes. We
don't need to read everything. Just confirm at the start if something
is different, where its different, and write only there. Do the
read/write batches in tile/slices."

SQM is that idea carried all the way: the ESF moment checksums are
not just integrity tags — run backwards, they are *write addresses*.
Files: `sqm_core.h` (the cell), `bench_sqm.c` (mutation sweep),
`sqm_cert.c` (certification driver).

## 1. The core observation

A payload's power moments

```
s_k = Σ_i b_i · x_i^k      (x_i = 1-based position, k = 0..3)
```

computed over **incoming** data in one pass, answer three questions
without ever reading the stored payload:

- *Is anything different?* — compare against the stored journal
  (root moments of the last accepted write).
- *Where is it different?* — the delta moments D = incoming − journal
  are exactly the moments of the *change*, and the moments of a
  1- or 2-point change determine the positions and deltas exactly.
- *What do we write?* — only the solved positions.

One pass over data we already hold (the caller's buffer) replaces the
read-everything-compare-everything cycle. That is the "almost
constant time" the user asked for: stored-side traffic is O(diff),
not O(payload).

## 2. Why moments and not hashes (the Hamming/Reed-Solomon lineage)

A hash says *that* something changed; an error-correcting code's
syndrome says *where*. Moments are the syndrome of a Reed-Solomon
code over the position field — the Vandermonde structure is the same
one RS decoders invert. The design simply stops the RS construction
at k=4 and uses it as a write-path differ instead of a decoder.
Hamming's principle is honored literally: the confirm-read touches
only the bytes the syndrome indicted.

## 3. Exactness is a theorem here, not a hope

Modular moment schemes (SQ5's mod-2³² journals) have aliasing blind
spots — the 4-point 3rd-difference quads, mapped and documented in
the SQ5 certification. SQM runs at PAY=64 with **u64 exact integer
moments**:

```
s3 ≤ 255 · Σ x³  ≤ 255 · 2080² < 2³²   (x ≤ 64... bounded, exact)
```

Every moment fits exactly; the delta solve is exact integer
arithmetic with zero modular ambiguity. Consequence, certified:

- the 4-point quads blind to every 3-moment scheme are **caught
  2000/2000** (s3 sees them — their 4th finite difference of a cubic
  is nonzero);
- blindness retreats one order to the 5-point pents (1,−4,6,−4,1),
  2000/2000 blind, documented exclusion. Each added moment provably
  pushes the blind class one point further out.

The SSE4.1 fast path (4 lanes × u32) inherits the same bound: worst
lane = 16 terms × 255·64³ ≈ 1.07e9 < 2³² — provably no lane
overflow, checked by proof not by testing.

## 4. The write path

```
sqm_write(id, incoming):
    mi = moments(incoming)                    # ONE pass, SSE4.1
    if slot known && mi == root[slot]:
        return                                # SKIP: 0 rd, 0 wr
    if first write:
        memcpy 64B; journals = mi + halves; return
    D = mi − root[slot]
    solve(D) → 1-pt or 2-pt exact integer Vandermonde
    if solved:
        confirm-read ONLY the solved bytes    # 1–2 stored bytes
        if stored + d == incoming there:
            write only those bytes
            root = mi                         # linearity: free
            halves += pointwise d·x, d·x², d·x³   # no extra pass
            return                            # 1B path: 1 rd, 1 wr
        else:
            escalate (confirm_escalations++)  # free tripwire
    # slice path
    halves(incoming)                          # lazy: only now
        half-1 local moments by binomial shift from globals:
        s1' = g1 − H·s0
        s2' = g2 − 2H·g1 + H²·s0
        s3' = g3 − 3H·g2 + 3H²·g1 − H³·s0     # NO third pass
    dirty half? → read 32B, write-diff only changed bytes
    both dirty? → full 64B rewrite
    journals = incoming moments               # always free
```

Three design decisions worth writing down:

1. **Journals are never recomputed from stored data.** Linearity
   means the incoming moments *are* the new journal. The solve adds
   one more gift: half journals update pointwise (d·x^k at the
   solved position), so the 1-byte hot path is exactly one pass over
   incoming + 1 byte read + 1 byte written. Halves are computed
   lazily — only on first write or the slice path.

2. **The confirm-read is a tripwire, not just a check.** If the
   solved positions don't hold stored + d == incoming, the stored
   payload changed since the last journal — corruption between
   sweeps. Escalation is counted and loud; the solve can never
   produce a wrong repair because the confirm gates every minimal
   write.

3. **Tiles/slices as the degradation ladder** (the user's "read/
   write batches in tile/slices"): solve (1–2 B) → half-slice
   write-diff (≤32 B) → full rewrite (64 B). Cost tracks the true
   diff size; no path ever writes an unchanged byte.

## 5. Measured (400 rounds × 256 items, byte-deterministic)

| mutations/rewrite | ns/item | stored rd B/write | stored wr B/write | path |
|---|---|---|---|---|
| 0 (pure skip) | ~40 | 0.00 | 0.16 | 100% skip |
| 1 | ~82 | 1.00 | 1.16 | 100% solve |
| 2 | ~152 | 2.11 | 2.23 | solve + rare slice |
| 8 | ~132 | 63.75 | 63.72 | slice write-diff |
| 64 (full rewrite) | ~309 | 64.0 | 64.2 | full |

A full-copy design moves 64 stored bytes per write. SQM at one
mutation moves ~1.1 — a ~55× traffic reduction — and a skip moves
**zero**. The skip/solve costs are dominated by the single incoming
pass, which scales with payload; the stored-side traffic does not.
At ESF-frame payload sizes the win grows proportionally (1-byte
patch: still 1 byte read + 1 written, against frames of kilobytes).

## 6. The honest tradeoff: the skip window (O6)

Minimal reads mean exactly that — a pure skip reads *nothing*. So a
stored corruption that lands after a journal-matching state and is
followed only by skips is **invisible until the next sweep**
(certified: 200/200 stale-after-skip; every one closed by the sweep,
none propagated silently).

Detection is sweep-scheduled, not write-scheduled. This is the
deliberate design point requested: we traded per-write stored-side
reads for traffic. If a deployment needs per-write detection of
stored corruption, that is a different (read-heavier) point on the
spectrum — SQ2B's duplex proofread lives there. The sweep cadence is
the knob that bounds the window, and it is now a documented,
measured parameter rather than an implicit assumption.

## 7. Certification (pre-registered oracles, byte-deterministic double-run)

```
SQMOR O1_skip_exact    256/256   skip → 0 rd, 0 wr                  PASS
SQMOR O2_diff_correct  1000/1000 content + journal closure          PASS
SQMOR O3_amplification 1B: 1.00 rd 1.00 wr | 2B: 2.04 rd 1.98 wr    PASS
SQMOR O4_sweep_det     1000/1000 counting                           PASS
SQMOR O4_sweep_rep     1000/1000 measurement (vs snapshot truth)    PASS
SQMOR O4_unresolved    0                                            PASS
SQMOR O5_quad_caught   2000/2000 (SQ5's blind class, caught by s3)  PASS
SQMOR O5_pent_blind    2000/2000 documented-exclusion               PASS
SQMOR O6_skip_window   200/200 stale-after-skip, closed by sweep    documented
```

One harness-class artifact recorded: early O4 scoring compared
repaired content against the fill pattern, though O2 mutations had
legitimately changed content — truth is the pre-event snapshot
(csnap). Fixed; repair scored against snapshot. (The canary protocol
applies to harnesses too.)

## 8. Boundaries, stated once

- Blind to coordinated 5-point pents (mapped, excluded).
- Skip window as above (O6).
- First write is a full 64 B write — nothing to diff against.
- Solve handles ≤2 changed positions exactly; wider diffs degrade to
  slice/full by construction — never to a wrong minimal write
  (confirm-read gates it).
- Root/half journals are exact-detect fields: any hit to them
  mismatches at the next write/sweep and routes to repair. No
  silent check-field class exists in this design.

**Status.** Certified at prototype level. The design question it
answers: moments are write addresses, and the minimal-read allocator
is the moment equations run backwards.
