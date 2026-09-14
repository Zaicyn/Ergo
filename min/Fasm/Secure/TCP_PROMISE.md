# TCP Promise — parity-on-demand stream recovery without resend

Status: prototyped + measured (C sims). No FASM mirror yet.

## Problem

Data streams (unlike auth) can take partial credit: recover as much as
possible in place instead of paying a full round trip to resend. Goal:
0-RTT repair of everything below a measured boundary, resend only
above it.

## Packing: the 1460 B segment

- Unit = 512 B. 1460/512 = **2.85 units/segment**: 2 full units
  (1024 B) + 436 B spare.
- One 4096 B frame = 8 units rides in **4 segments** (always-send) or
  **3 segments** (on-demand routine: 4096 + 256 metadata = 4352 ≤ 4380).
- 4×436 = 1744 B of spare funds P+Q parities (2×512) + 8×16 B
  syndromes = 1152 B overhead, 592 B left (deliberately unsent).

## Wire format

- **Depth-8 byte interleave.** Unit u holds frame bytes {u+8k}. A
  channel burst contiguous on the wire of length L≤8 lands 1 byte each
  in L distinct units → per-unit SEC fixes all of them.
- **Per-unit S0..S3** (idx 1..512) + gated single-byte SEC per packet.
- **P = row XOR, Q = GF(256) weighted sum** (coeffs 3^u — note: 2 has
  order 51 in the AES field and silently aliases log/exp tables; 3 is
  primitive, order 255, verified). Any 1–2 whole-unit losses solve
  exactly. No search, no gates, no refuse cases.
- **Order (measured, not assumed): SEC survivors → rebuild from clean
  data → reverify.** Rebuilding from dirty survivors transplants their
  errors into the fresh packet (mixed cell went 0/200 → 162/200 on
  flipping the order; v2: 176/200).

## On-demand protocol ("256 + a promise")

- Routine: 3 segments carrying frame + 256 B metadata = 128 B
  syndromes + 64 B parity commitment (keyed tag over P+Q) + 64 B
  stream authenticator (bond tag).
- Sender retains P+Q per unacked frame (1 KB × window; 64 KB nominal).
- Receiver: SEC from syndromes → clean = done, 0 RTT. Hurt beyond
  SEC → fetch parity (+1088 B, +1 RTT), rebuild, check commitment.
  Commitment mismatch (liar/broken sender) or still dirty → resend
  fallback (+4096 B, +1 RTT).

## Measured (NTR=200/cell, deterministic; NSIM=2000/point)

packetbench v2 (full recovery / mean bytes-correct of 4096):

| cell | full | mean | note |
|---|---|---|---|
| spread n=1 | 200 | 4096.0 | always |
| spread n=2/4/8 | 173/86/0 | 4095.7/4094.7/4091.2 | graceful, partial credit high |
| burst L=4,8 (interleaved) | 200/200 | 4096.0 | wall moved 1→8 |
| burst L=16/64/256 | 0 | 4080/4032/3840 | cliff at depth+1, resend |
| burst L=64, non-interleaved control | 0 | 4032.0 | interleave is the whole gain |
| loss d=1 / d=2 | 200/200 | 4096.0 | exact algebra |
| mixed 1loss+2err / 2loss+2err | 176/177 | 4095.5/4095.3 | |
| 1460 B wire-interval erasure | 0 | 2641.4 | **the boundary**: ~182 B gone from every unit at once; 2 equations can't cover 8 simultaneous erasures per offset |

demandbench (bytes/frame, RTT/frame vs damaged-frame fraction f):

| f | on-demand B | on-demand RTT | always-send B | always-send RTT | TCP B | TCP RTT |
|---|---|---|---|---|---|---|
| 0.00 | 4352 | 0.000 | 5248 | 0.000 | 4352 | 0.000 |
| 0.01 | 4360 | 0.003 | 5256 | 0.002 | 4385 | 0.008 |
| 0.10 | 4476 | 0.051 | 5332 | 0.021 | 4725 | 0.091 |
| 0.50 | 4962 | 0.272 | 5676 | 0.104 | 6380 | 0.495 |
| 0.80 | 5385 | 0.448 | 6014 | 0.187 | 7649 | 0.805 |

Fetch guard (measured improvement over the table's first cut): the
receiver knows the missing-unit count before fetching, and parity
solves erasures only — so fetch fires iff 1–2 units are actually
missing. Pure-error damage skips the fetch (straight to
resend-fallback accounting); pure loss always fetches. The table
above includes the guard.

Readings: on-demand wins bytes at every f (fetch fires only when
SEC-alone fails — a fraction of damaged frames, hence better than the
f<0.8 analytic breakeven). Real trade is RTT-vs-bytes against
always-send (negligible below f≈0.1). TCP frame-resend loses on both
axes everywhere (frame-level accounting = TCP's upper bound; SACK
narrows the byte gap but not the 0-RTT repair advantage).

## Structural result: losses are inert (grid test)

Claim: full-recovery rate is a function of error count alone for
losses ≤ 2. Tested with forced exact-error placement (errors only in
surviving units, distinct positions — no skip-mixture confound),
4×3 grid (loss D=0..2 × errors E=0..3, NTR=200), plus per-trial
effective-error-count collapse buckets across all spread cells.
RNG stream is continuous (never reseeded) → trials independent.

GRID full/200:

| D\E | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| 0 | 200 | 200 | 181 | 133 |
| 1 | 200 | 200 | 167 | 128 |
| 2 | 200 | 200 | 165 | 113 |

COLLAPSE rate(full | effective errors): 0→1.000, 1→1.000,
2→0.864, 3→0.623, 4→0.430. Single curve to first order.

Verdict: refined, not dead. The erasure algebra contributes zero
failures (LO d=1,2 = 200/200; grid E=0 column 200/200 at every D).
But loss is not *perfectly* inert: D=0→D=2 costs 16–20 counts at
fixed E (~2–2.5σ, same sign in both rows). Mechanism, quantitative:
losses shrink the surviving-unit pool (8→6), concentrating errors
into fewer units and raising same-unit collisions (which SEC
refuses). Predicted collision delta at E=3 is 10% ≈ 20 counts;
observed 133→113 = 20. Exact match. So: rate = f(error count,
pool size) via collision probability + SEC gate rate; the algebra
itself never fails. SP n=2 (173) sits in the same bucket as MX/MX2
(184/167) as predicted.

- Rebuild-before-repair transplants errors (0/200 → 176/200).
- GF(256) generator 2 has order 51, not 255 — log/exp division
  silently garbage (LO d=2: 0/200 → 200/200 on switching to 3).
- Finite-field code fails silently and exactly: verify exhaustively.

## Boundaries (resend above these, same as TCP would)

- Bursts longer than interleave depth (L>8 at depth 8).
- Whole-segment (1460 B) wire erasure.
- 3+ whole-unit losses (Q covers 2).

## Socket validation (`sockbench.c`)

Real loopback sockets (UDP datagrams + TCP streams, sender →
fault-injecting proxy → receiver, fetch round trip genuine). NTR=50,
identical draws both modes. Recovery matches the sims; compute is
3–106 µs/frame, loopback fetch RTT 1–7 µs (TCP_NODELAY set — Nagle
stalled the 11 B req to ~1.5 ms before that).

| cell | UDP | TCP |
|---|---|---|
| clean / SP1 / BUI8 | 50/50, 0 fetch | 50/50, 0 fetch |
| SP4 | 29/50, 0 fetch (guard) | 29/50, 0 fetch |
| BUI64 | 0/50, 0 fetch (guard) | 0/50, 0 fetch |
| LO1 / LO2 | 50/50, fetch | 50/50, fetch |
| MX | 49/50, fetch | 49/50, fetch |

Bugs the sockets caught (all in harness, none in the math):
stale length header on hand-rolled fetch replies (shipped 1-byte
"parities", commitment caught it); SO_RCVTIMEO {0,0} means BLOCK
not poll (drain via select() instead); missing SO_REUSEADDR hung
setup on reruns (TIME_WAIT); missing TCP_NODELAY stalled fetches.

## Euler runs (`eulerbench.c`)

Q: is units/packet ~= e (1460/512 = 2.85) a feature? A: coincidence —
but three optimizations were run to check where e really governs.
- Unit size (calculus): wire(u) = F+16F/u+2u -> u* = sqrt(8F) = 181;
  realizable 128/256 tie at wire 4864 (vs 512 now at 5248, rating
  8 vs 16/32, same 4 segments). e-tuned u=537 (1460/e) is worse on
  every axis (wire 5292, rating 7.6). Inherited 512 is 384 B
  overweight at half-or-quarter the burst rating; counterweight is
  loss-exposure (more units = more loss targets; Q covers any 2).
  Balanced pick pending loss-rate data: u=256 (16 units).
- Geometric bursts (e VERIFIED): L ~ Geometric(mean mu) ->
  recovery = P(L<=depth) = 1-(mu/(mu+1))^8 ~= 1-e^(-8/mu). Measured
  7 points track prediction within noise (mu=2: 0.960/0.961;
  mu=8: 0.620/0.610; mu=32: 0.195/0.218). Euler's number governs
  the burst-rating curve, by derivation and measurement.
- Fetch-retry backoff (e loses honestly): q=0.25/attempt, K=4,
  RTT=10ft: b=1.5 wins (0.927ft), then 2.0, e (1.185), 3.0, 4.0.
  Cheap retries -> aggressive (small) base; e carries pedigree,
  not victory, under these constants.

## Bursts: occupancy model + use cases

Multi-burst cells (NTR=200, independent random starts): 2xL2 127
(occupancy predicts 5/8=125), 2xL4 21 (predict 1/8=25), 3xL2 39,
2xL8 0 (structural: two full coverages = 2 bytes/unit everywhere).
Burst + 1 unit loss (L4+LO1): 200/200 — structural full (burst
contributes <=1 byte/unit, losses solve exactly, lost unit absorbs
burst bytes for free). Sub-wall bursts are phase-invariant by
construction (contiguous L<=8 always hits distinct units).
Use cases, mapped: wireless fading/interference (1-2 fades/frame =
the 2xL2-L4 regime, 60-100% at 0 RTT; interleave is time diversity,
anti-jam heritage); storage partial-sector defects (sub-sector run
= burst, whole dead sector = unit loss = parity); stream dropouts
(audio/video concealment analog: even L=64 keeps 4032/4096 bytes);
narrow jammer (absorbed; wide jam = SEG = resend, honestly kept).

## Transport interop (`pktcore.inc` + `udp_node.asm`)

Modular split: `pktcore.inc` holds the whole codec core (both
protocols include it; neither carries the other), `udp_node.asm` is
the UDP shell (role via argv: send|recv), `udp_cpeer.c` the C peer,
`udp_proxy.c` the fixed-plan fault proxy. Fixed vectors, so verdicts
must be byte-identical across languages and directions:

| direction | clean | drop=3 | drop=1,5 | flip=2:100 |
|---|---|---|---|---|
| asm->C | 9/0/0/1 | 8/1/1/1 | 7/2/1/1 | - |
| C->asm | 9/0/0/1 | 8/1/1/1 | - | 9/0/0/1 |
| asm->asm | 9/0/0/1 | - | 7/2/1/1 | - |

(columns: got/lost/fetch/full). All green, incl. Q-solve over the
wire (drop=1,5) and the fetch handshake both ways.
Bugs the matrix caught: asm sender stamped idx=0 on all units
(`al` held low(u*512), always 0 — receivers deduped 7 units);
receiver scored against a zero oracle (bku never built — full=1 on
empty air); startup races (ready-probe ports before sending);
`restore`/`used`/`LDS` reserved words; post-include segment reset
(pitfall #16, entry landed in readable).

## Files / reproduce

- `min/Fasm/Secure/packetbench.c` — wire format + recovery cells.
- `min/Fasm/Secure/demandbench.c` — on-demand protocol sim.
- `gcc -O2 -march=native -std=c11 -D_GNU_SOURCE -o /tmp/opencode/pb
  min/Fasm/Secure/packetbench.c && /tmp/opencode/pb`
- Same shape for `demandbench.c`.
- Next: FASM bare-metal mirror (pattern: `rgba_hs.asm`/`rgba_hs.c`).
