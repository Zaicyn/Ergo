# Secure — file integrity on torus geometry (ESF campaign)

Goal: (A) multi-bit correction using the torus layout, (B) measured
choice of hash for this use. Specs: `Spec/Ergo_Stream_Format.md` (ESF2
frames + single-byte syndrome repair), `Spec/ESF_Slot_Pool_Brief.md`
(v4 squaragon as frame pool), `Spec/Hash_Strengthening_Proposal.md`
(FNV-1a 64 vs xorshift paths).

## Key observation: the math already exists in-tree

ESF §3's `(S0, S1, S2) = (Σb, Σb·idx, Σb·idx²)` with single-byte repair
(`d = ΔS0`, `p = ΔS1/d` exact division, S2 gate, re-verify) is the same
object as SQ5's flux triple (`s0/s1/s2` per bin-shell) and SQ5's
`sq5_try_sec` (`d = ds0`, `p = ds1/d`, `expect2 == ds2` gate).
Multi-bit correction is therefore a composition problem, not a new
primitive: more equations from more geometry.

## A. Multi-bit correction capacity (torus layout)

One frame with 3 global syndromes repairs exactly 1 byte (ESF §3
proof: no wrap since `|d·p| < 2^32`, uniqueness exact). The torus
adds independent equation sets:

1. **Bin partition (8 bins):** per-bin triples (sq5 flux does this
   today) make each bin independently single-byte-repairable → up to
   8 correctable bytes per frame-group when spread ≤ 1 per bin.
2. **Duplex shells (2 views):** 6 equations per bin solve same-bin
   2-byte errors (4 unknowns `d1,p1,d2,p2` + 2 gates); shell
   disagreement alone is a free detector (`duplex_mismatch` pattern
   from Sq2B/SQW).
3. **Journal reference (sq5 `jr`):** stored per-bin moments turn
   detection into O(1) residual checks per bin (rescan only to repair).
4. **Product layer (optional):** column moments across bins locate
   errors at row×column intersections when bin-local solve is
   ambiguous (clustered multi-byte).

Capacity summary: 1-byte anywhere (proven); up to 8-byte spread
(1/bin); 2-byte same-bin via duplex; beyond that detection-only.
Every repair stays gated; a 4th moment S3 = Σb·idx³ closes the
soundness hole the prototype found (post-fix re-verify is vacuous
by linearity — S3 makes spurious solutions fail a fresh 2^−32
gate). Syndrome cost with S3: 272 B per 4 KB frame (6.6%).
See PLAN.md Results for the measured table (misc 0/6000×2).

Geometry note (exact, no padding): one SQ5 bin = 32 gens × 2 shells
× 64 B = 4096 B = one ESF frame. So frame `k` ↔ bin `k mod 8`,
slots within the bin = 64 chunks of 64 B, shells = dual views.
Index bases differ today (ESF 1-based over 4080 region vs flux
`g*64+i+1`) — align on one convention in the prototype. ESF stores
S-words in-frame; the torus keeps journals separately — keep both,
compare cost.

## B. Hash choice for this use

Contenders: FNV-1a 64 (proposal Path A, canonical, GPU-side uses it),
splitmix64-block-stream (HashKit extension, Stafford finalizer =
designed avalanche), ad-hoc XOR-shift (control, expected to lose).
xoshiro256** is a PRNG, not a hash — excluded except as control.

Metrics (all measured, none promised): (1) avalanche — flip sampled
input bits, mean output Hamming distance (want ≈ 32) + distribution;
(2) speed — ns/byte on 4 KB frames; (3) detection — N random
multi-byte corruptions all detected (expect 100% everywhere; the
differentiator is (1)+(2)). Prediction: splitmix wins avalanche,
FNV-1a wins simplicity/canonicity — report both margins, recommend
by measurement.

## Allocator roles for this test

| Role | Allocator | Reason |
|---|---|---|
| Syndrome/repair engine | SQ5 | bin×shell triples + journals + SEC/tier2/resync tiers already exist; flux just vectorized 5.9× |
| Frame pool | SQ4 | slot-pool brief names v4 squaragon literally; SCATLT claim order = ESF schedule geometry; zone watermarks |
| Duplex redundancy pattern | Sq2B / SQW | two-shell views, transcribe/pay_ok verify shapes (reference only) |
| Hash candidates | HashKit + new FNV-1a 64 | shootout (B) |
| Audit/log | trit / RLE / int_codec + emit | poison records, repair logs |

Out of scope: V8 (fold checksums don't fit frame semantics), V22
(superseded), SQM/SQFH (moment/float machinery not needed here).

## Prototype plan

1. `hashshoot` (B, ~1 session, self-contained): FNV-1a 64 (new impl)
   vs splitmix-stream vs ad-hoc on 4 KB frames — avalanche histogram
   + GB/s + detection trial. Uses `hash_rng.inc`.
2. `torusecc` (A, bigger): 8-bin frame model with per-bin S0/S1/S2 +
   dual shells; inject k = 1,2,3,4,6,8 byte errors, spread vs
   clustered, N trials each; repair via bin-local SEC + duplex
   2-byte solve; report correction rate vs k/pattern + miscorrections
   (expect 0).

## hashshoot results (DONE 2026-09-13)

`hashshoot.asm` (+ `hashshoot.c` mirror): 4 KB frames, full 32768-bit
avalanche, best-of-5 ns/frame over 5000 iters, 2000-trial 2–8 byte
detection. C mirror-clean (digests + avalanche + detection match),
deterministic across runs.

| hash | digest | ns/4 KB | aval mean | min–max | miss/2000 |
|---|---|---|---|---|---|
| FNV-1a 64 | ef98fd1c3b78d3d9 | 4162 | 30.71 | 7–48 | 0 |
| splitmix-stream | 25c6260cb17903ef | 1680 | 32.02 | 16–49 | 0 |
| ad-hoc | 76ca09756b57a177 | 399 | 1.68 | 0–4 | 0 |

Verdict: splitmix-stream wins on both axes — avalanche 32.02 with a
tight binomial-like spread vs FNV-1a's 30.71 (real bias, ~60σ) and
weak-bit tail (min 7); 2.5× faster (0.41 vs 1.02 ns/B). Ad-hoc is
disqualified (mean 1.68: single-bit flips nearly invisible). All
three detect 2000/2000 multi-byte corruptions — detection is not the
differentiator at this size. Recommendation: splitmix-stream for the
integrity hash; keep FNV-1a as the canonical cross-context fallback
(proposal Trigger 3: CPU/GPU agreement).
---

# Part II — from frames to the wire (handshake, tiers, codec, transport)

Repair data streams in place instead of resending them. A 4096-byte
frame travels as 8 packets with enough redundancy to fix random
damage on arrival — no round trip — and a handshake decides who gets
to see how much of it.

Status: researched, prototyped, measured, and ported to bare-metal
FASM with C mirrors. Every claim below has a bench behind it; see
`TCP_PROMISE.md` for numbers, `AUDIT.md` for everything that broke
along the way.

## How it works (the whole path in one page)

**Handshake.** Two parties hold a secret each (a 4-byte color plus a
magnitude lane). A Diffie–Hellman-style exchange over a small group
produces a shared bond both sides compute independently
(`rgba_dh.c`, `rgba_hs.asm`). The bond becomes a transient session
key: it encrypts the frame and signs an 8-byte tag per piece. Wrong
secret → different bond → garbage plus a failed tag. Verified both
directions, tamper-tested.

**Tiers.** Trust is not all-or-nothing. The frame's four 1024-byte
slices unlock progressively: strangers see only the "safe" slice,
higher trust unlocks more (`tierbench.c`, 4-tier demo in `rgba_hs`).
More tiers cost essentially nothing (~6 ns each through 64 tested) —
pick the count by trust granularity, not performance. Four maps
naturally onto the frame's four channels.

**Codec.** The frame is byte-interleaved across 8×512-byte units
(unit u holds every 8th byte). Each unit carries four running
checksums (S0–S3); a gated single-byte solver (SEC) fixes one damaged
byte per unit or provably refuses. Two extra parity units (P = plain
XOR, Q = weighted sum over GF(256)) rebuild any one or two *lost*
units exactly. A keyed commitment over the parities lets a receiver
trust fetched parity without trusting the sender blindly
(`pktcodec.asm` / `pktcore.inc`).

**Wire.** Routine transmission is 3×1460-byte segments: 4096 bytes of
frame + 256 bytes of metadata (128 checksums + 64 parity commitment +
64 stream tag). Parities wait at the sender and are fetched only when
damage exceeds what the checksums can fix — the "promise" design
(`demandbench.c`, `TCP_PROMISE.md`). Recovery order matters: repair
survivors first, rebuild from clean data, reverify (rebuilding first
transplants errors into the fresh packet — measured 0/200 → 176/200
on fixing the order).

**Transport.** `udp_node.asm` and `tcp_node.asm` speak the protocol
over real loopback sockets from one shared core (`pktcore.inc`, no
libc, static binaries ~24 KB). Proven by interop: asm↔asm, asm↔C,
C↔asm, all directions byte-identical verdicts through a
fault-injecting proxy.

## Measured behavior (not marketing)

| damage | result, 0 RTT |
|---|---|
| 1 random byte error | always fixed (200/200) |
| n spread errors | graceful: n=2 → ~88%, n=8 → ~0% full but ~4091/4096 bytes right |
| burst ≤ 8 (interleaved) | always fixed (200/200) |
| burst > 8 | refused, needs resend (cliff, not slope) |
| 1–2 whole packets lost | rebuilt exactly (200/200) |
| 1 loss + 2 errors | ~88% full (162–184/200) |
| whole 1460 B segment eaten | unrecoverable — resend |

On-demand vs always-send-parity vs TCP-resend was simulated across
damage rates: on-demand wins on bytes at every rate and on round
trips against TCP everywhere; against always-send it trades a little
RTT for fewer bytes and one less segment per frame.

## Use cases — pros and cons

**Live streams over lossy links (wireless, sensor feeds, voice/video
adjacent).** Pro: most damage repairs with no round trip, and partial
recovery degrades gracefully (a bad burst costs bytes, not the
frame). Con: damage past the boundary still resends; ~16–28% wire
overhead depending on layout.

**Cluster interconnect with bursty loss.** Pro: avoids retransmit
storms for the common small-damage cases. Con: real engineering cost
vs "TCP already works" — worth it only where tail latency matters.

**Storage with sector defects.** Pro: the damage shapes map exactly —
partial-sector damage is a burst, a dead sector is a unit loss, and
each meets its matched defender. Con: needs layout integration; the
overhead only pays if defects are common enough.

**Hostile or jammed links.** Pro: narrow interference is absorbed as
bursts (interleaving is time diversity, Cold War-approved). Con: a
wide jammer just forces resends; and this is resilience, not
identity — the keyed tags authenticate *within* a bonded session but
there is no public-key infrastructure here.

**Not for:** bulk reliable transfer where TCP is fine (don't pay
complexity for nothing), tiny messages (fixed overhead dominates),
damage beyond two lost units without a resend path, or anyone needing
formal security proofs (this is measured engineering: 200-trial
cells, not theorems).

## Files

- `rgba_dh.c`, `rgba_hs.asm/.c` — handshake + disclosure
- `tierbench.c` — tier scaling, tag choice, disclosure demo
- `pktcodec.asm/.c`, `pktcore.inc` — codec core + shared include
- `packetbench.c`, `demandbench.c`, `sockbench.c` — recovery cells,
  on-demand sim, socket validation
- `udp_node.asm`, `udp_cpeer.c`, `udp_proxy.c` — UDP shell + peers
- `tcp_node.asm`, `tcp_cpeer.c`, `tcp_proxy.c` — TCP shell + peers
- `eulerbench.c` — unit-size optimum, burst e-curve, backoff sweep
- `TCP_PROMISE.md` — design + full measurement tables
- `PLAN.md`, `PHASEMAP.md` — campaign plan, tier map
- `AUDIT.md` — every fixed issue with its commit
