# FASM math — shared formulas and per-component differences

Reference for tuning. Everything here is copied from the sources, not
from memory; file:line pointers are given where the formula lives.
Conventions: all integer sums wrap mod 2^32 (32-bit regs) or mod 2^64
unless noted; `idx` is 1-based (`i+1`) everywhere unless noted.

## 1. Shared includes (`min/Fasm/*.inc`, `Secure/pktcore.inc`)

### `rng.inc` — xoshiro256\*\* + seeding + draws

State: 4 qwords `s[0..3]`. One step (`xoshiro_ss`):

```
out    = rotl(s[0] + s[3], 17)
t      = s[1] << 17
s[2]  ^= s[0];  s[3] ^= s[1];  s[1] ^= s[2];  s[0] ^= s[3]
s[2]  ^= t
s[3]   = rotl(s[3], 45)
return out                        # rotl(x,k) = (x<<k)|(x>>(64-k))
```

Seeding (`seed_rng`, from scalar `s`): four words derived by
`+`/`xor` with `0x9E3779B97F4A7C15`, `0xBF58476D1CE4E5B9`,
`0x94D049BB133111EB`, `0xF0BA35E12960E9E7`, then **10 warmup draws**
(discarded). Draws: `rand_u32` = low 32 bits (C-cast truncation);
`rand01` = `(x >> 11) * 2^-53` with `2^-53 = 0x3CA0000000000000`
(exact in binary64). **Contract: draw order and draw counts are the
oracle** — adding or removing one draw changes every downstream
number (`rng.inc:1-100`).

### `hash_rng.inc` — splitmix64-Stafford (debug kit, not oracles)

Pure function, no state: `H(seed) = mix(seed + 0x9E3779B97F4A7C15)`:

```
z = seed + GOLDEN
z = (z ^ (z>>30)) * 0xBF58476D1CE4E5B9
z = (z ^ (z>>27)) * 0x94D049BB133111EB
H = z ^ (z>>31)
```

`hash_u32` = `H >> 33` (top 31 bits, Ergo HASH semantics);
`hash_u01` = `(H >> 11) * 2^-53` (Ergo RAND semantics). Counter-mode:
event *k* recomputable without replaying `0..k-1`. Explicitly NOT a
replacement for `rng.inc` streams in ports (`hash_rng.inc:1-10`).

### `sqb_cell.inc` — duplex bio cell (Sq2B oracle-proven)

Geometry: 8 bins × 32 gens, codon 168 B (`CODON_SZ`), payload 152 B
(`SQB_PAY`), cell 86336 B; `codon_ptr = ((b*32 + g)*2 + strand) *
168 + cell`. Stored tombstone `0xDEAD5EED`; strand complement
`COMPLEMENT = 0x55`.

Syndromes (`syn`, 152 B, idx 1-based): `S0 = Σv`, `S1 = Σv·idx`,
mod 2^32. Scalar loop plus an AVX2 form (19×8 B lanes,
`vpmovzxbd`/`vpmulld`, idx vectors `[1..8]+8k`, horizontal add —
`syn_inline` is the fused sweep variant; ymm7 reloaded per duplex,
never hoisted across `vzeroupper`). `duplex_mismatch` counts bytes
where `(c0 ^ c1 ^ 0x55) != 0` (AVX2 `vpcmpeqb`+`popcnt`, scalar
tail). Payload pattern (`sqb_fill`/`pay_ok`): `byte[i] = (i*91 +
item*17) ^ 0xA5`, verified lane-wise in AVX2. Slot search starts
from the `SCATLT` table (`id % 32` entry, then `div`-free bin walk).
Sweep policy: healthy iff duplex agrees and both strand syndromes
match; else excise (rebuild bad strand from good) or tombstone.

### `trit/trit_codec.inc` — base-3 groups

5 trits → 1 byte, Horner form, each trit validated `< 3`:

```
b = ((((t4*3 + t3)*3 + t2)*3 + t1)*3 + t0)     # t4 = [rdi+4] … t0 = [rdi]
```

### `trit/rle_pack.inc` — RLE + 2-bit pack

Locked format: `[count:u8][value:u8]` pairs, count 1..255.
`pack2`: 256 entries in `0..3` → 64 bytes, validated per group.

### `trit/int_codec.inc` — zigzag + varints

`zz_enc(e) = (e<<1) ^ (e>>31)` (branchless; `e≥0 → 2e`,
`e<0 → −2e−1`, mod 2^32 exact); `zz_dec(s)`: `(-(s&1)) ^ (s>>1)`.
Plus 1..8-byte little-endian put/get.

### `emit.inc` — formatting only, no math

`emit_u64` (decimal), `emit_f6`/`emit_fdec` (correctly rounded,
round-half-even, exact for the benign ratios printed here),
`ratio_fx` (single division = identical to a C decimal literal),
`atoi`, `wallns`/`cycles` timers.

### `Secure/pktcore.inc` — repair codec core

Moment residuals (`triple4`, 512 B, idx 1-based, mod 2^32):

```
S_k = Σ v·idx^k,  k = 0..3;    e_k = S_k − ref_k
```

Single-byte solve (`sec_pkt`): `d = e0` must satisfy `±1..255`;
`e1/d` must divide exactly with quotient `q ∈ [1,512]`; S2 gate
`(int64)d·q·q == (int32)e2`; S3 gate `(uint32)(d·q³) == e3`; apply
`p[q−1] −= (uint8)d`; reverify all four residuals are zero, else
refuse. Erasures are solved, not searched: P = row XOR rebuilds one
loss; Q = GF(256) weighted sum (`0x11B` field, generator 3 —
**not** 2, whose order is 51) with coefficients `3^p` rebuilds two
(`Ua = (Q′ ^ cb·P′)/(ca ^ cb)`, `Ub = P′ ^ Ua`). Keyed tag absorbs
`ct + C + (h≪6) + (h≫2) + i` per byte with a Stafford mix every 64
B. Handshake toy group `p = 1543`, `g = 5` (primitive); private
scalar from color‖magnitude; bond `S = g^ab`. Wire interleave:
unit *u* holds frame bytes `{u + 8k}` (depth 8 = burst rating).

## 2. Where each allocator/codec differs

| component | RNG | uniform double | checksum / syndrome | hash | payload pattern |
|---|---|---|---|---|---|
| Sq2B | xoshiro256\*\* | `(x>>11)·2⁻⁵³` | syn S0/S1, 152 B, idx 1-based | — | `(i·91+item·17)^0xA5` |
| SQM | xoshiro256\*\* | same | **mom S0..S3**, base-relative `x = base+i+1`, u64 lanes | — | own fill |
| SQW | xoshiro256\*\* | same | transcribe/pay verify shapes | **sqw_hash**: FNV-1a accumulation (prime `0x100000001B3`) over 19 qwords from golden-ratio IV + Stafford-style final mix (`>>29`, `×0xBF…`, `>>32`); cold per-alloc | same pattern family |
| SQ5 | xoshiro256\*\* **starstar** + `rand01`, seed `0xCE27` | same | **flux triples per bin×shell** + `sq5_try_sec` (S0–S3 ladder + gates) + resync tiers | — | pay_ok (shared shape) |
| SQFH | **xorshift64** (`x^=x<<13; x^=x>>7; x^=x<<17`), seed `0x51F15EED1234567` | `frnd`: same `(x>>11)·2⁻⁵³` | — (owns f64 trig instead) | — | own fill |
| SQ4 | xoshiro256\*\* | same | slot-pool watermarks (SCATLT geometry) | — | — |
| V8 | (invariant checker) | — | AVX2 fold checksum | — | — |
| V22 | bug characterized, left open (superseded by Sq2B) | — | — | — | — |
| trit | xoshiro256\*\* (ports) | same | base-3/RLE/int codecs above, digest-gated | — | — |
| Secure | xorshift64 test draws; splitmix64 KDF/stream | `(H>>11)·2⁻⁵³` (hash_u01) | triple4 S0..S3, 512 B (above) | splitmix-stream house hash (1680 ns/4 KB, aval 32.02); FNV-1a 64 canonical fallback | RGBA channel tint + index (handshake units) |

One family, four coverages: the power-sum moments
`Σv·idx^k` appear as syn (k=0..1, 152 B), mom (k=0..3,
base-relative), flux (per bin×shell), triple4 (k=0..3, 512 B).
Solvability grows with independent equations: 1 unknown byte needs
S0+S1+gates; same-bin 2-byte needs the duplex's 6; erasures need
only P (+Q). Index base and coverage are the tuning knobs — the
algebra is shared.

## 3. Tuning knobs (what to change for what effect)

- **Seeds / draw counts**: change every number downstream (oracle!).
  Never "just one more draw."
- **Index base / coverage / moment count**: more moments = harder
  faults solvable; wider coverage = fewer syndrome bytes per data
  byte. S3 is what makes refusal sound (gated, not hoped).
- **Gate strictness**: S2/S3 exactness is the miscorrection dial;
  loosening buys fixes at the price of miscs — measure, don't guess.
- **Interleave depth = burst rating** (depth 8 ⇒ L≤8 fully
  recoverable); multi-burst recovery is occupancy combinatorics.
- **Parity count**: P covers 1 erasure, +Q covers 2; spares fund
  each additional parity one at a time.
- **Unit size**: wire-optimal `u* = √(8F)` (≈181 for 4 KB frames;
  realizable 128/256 tie) — bytes say small, loss-exposure says
  large; 256 is the balanced pick pending loss data.
- **Retry backoff base**: cost-ratio-driven (≈1.5 wins when retries
  are cheap); no universal constant.
- **Modem**: bursts → DWT (time containment), tones → FFT
  (frequency quarantine); db4 default. See `Secure/wireless.md`.
