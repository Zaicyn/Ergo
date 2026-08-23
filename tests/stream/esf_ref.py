#!/usr/bin/env python3
"""esf_ref.py — Python reference reader for the .esf framed stream
format (Spec/Ergo_Stream_Format.md). Shared by the tests in this
directory; imported, not run.

Every frame check is computed (magic equality, direct-addressed
schedule, per-channel sequence, weighted integrity syndromes) —
nothing is searched.

ESF2: the three stored words are weighted syndromes S0 = Σb,
S1 = Σb·idx, S2 = Σb·idx² (mod 2^32) over the fixed region
[4,16) ∪ [28,4096) with 1-based contiguous idx (spec §3). Detection
floor |d| ≥ 1; single-byte corruption is repaired exactly (position
by division — no wrap in range — value from ΔS0, gated by the S2
consistency equation and a full re-verify). Anything failing the
gate is detected and refused, never miscorrected.
"""

import struct

SCATLT = (6, 5, 4, 0, 2, 3, 4, 7, 4, 6, 3, 0, 1, 2, 1, 0,
          3, 6, 4, 7, 4, 3, 2, 0, 4, 5, 6, 5, 4, 0, 2, 3)

FRAME = 4096
MAXPAY = 4068
MAGIC = b"ESF2"
M32 = 0xFFFFFFFF

# contiguous 1-based index of a covered file offset (spec §3)
#   o in [4,16)    -> idx 1..12
#   o in [28,4096) -> idx 13..4080
def _idx(o):
    return o - 3 if o < 16 else o - 15


class ESFError(Exception):
    pass


class ESFRefused(ESFError):
    """Corruption detected but not single-byte-repairable (multi-byte
    damage, integrity-word damage, or magic damage)."""
    pass


def scheduled(k, nch):
    """Channel of frame k — direct addressing, never searched."""
    return SCATLT[k % 32] % nch


def syndromes(frame):
    """(S0, S1, S2) over the fixed region [4,16) ∪ [28,4096)."""
    s0 = s1 = s2 = 0
    for o in range(4, 16):
        b = frame[o]
        i = o - 3
        s0 += b
        s1 += b * i
        s2 += b * i * i
    for o in range(28, FRAME):
        b = frame[o]
        i = o - 15
        s0 += b
        s1 += b * i
        s2 += b * i * i
    return (s0 & M32, s1 & M32, s2 & M32)


def _repair(fr, stored):
    """Attempt single-byte repair of frame `fr` (a bytearray) against
    the stored syndrome triple. Returns the index repaired.
    Raises ESFRefused if no consistent single-byte hypothesis exists
    (multi-byte or integrity-word damage)."""
    comp = syndromes(fr)
    d0 = (comp[0] - stored[0]) & M32
    d1 = (comp[1] - stored[1]) & M32
    d2 = (comp[2] - stored[2]) & M32
    # d as a signed byte change: |d| in [1,255]
    if 1 <= d0 <= 255:
        d = d0
    elif d0 >= (1 << 32) - 255:
        d = d0 - (1 << 32)
    else:
        raise ESFRefused("ΔS0 out of single-byte range")
    # position: d·p == ΔS1 exactly (no wrap: |d·p| <= 255·4080 < 2^32)
    num = d1 if d > 0 else d1 - (1 << 32)
    if num % d != 0:
        raise ESFRefused("no exact position solution")
    p = num // d
    if not (1 <= p <= 4080):
        raise ESFRefused("position out of range")
    # consistency gate: d·p² ≡ ΔS2 (mod 2^32)
    if (d * p * p) & M32 != d2:
        raise ESFRefused("S2 consistency gate failed")
    # apply and re-verify exactly
    o = p + 3 if p <= 12 else p + 15
    fr[o] = (fr[o] - d) & 0xFF
    if syndromes(fr) != stored:
        raise ESFRefused("post-repair verification failed")
    return p


def check_frame(fr, k, nch, cseq, repair=True):
    """Verify one frame (bytearray, 4096 bytes) with frame ordinal k;
    cseq is the per-channel expected sequence array (mutated on
    success). Returns (channel, payload-bytes, repaired-index-or-None).
    Raises ESFError/ESFRefused on failure."""
    if len(fr) != FRAME:
        raise ESFError(f"frame {k}: bad size {len(fr)}")
    if fr[:4] != MAGIC:
        raise ESFRefused(f"frame {k}: bad magic (not repairable)")
    stored = struct.unpack("<III", fr[16:28])
    fixed = None
    if syndromes(fr) != stored:
        if not repair:
            raise ESFError(f"frame {k}: integrity residual nonzero")
        fixed = _repair(fr, stored)
    # structural checks on the (repaired) frame — fields are read
    # AFTER any repair, since repair may have restored them
    kk, = struct.unpack("<I", fr[4:8])
    ch, L = struct.unpack("<HH", fr[8:12])
    seq, = struct.unpack("<I", fr[12:16])
    if kk != k:
        raise ESFError(f"frame {k}: index field {kk}")
    if ch >= nch:
        raise ESFError(f"frame {k}: channel {ch} >= nch {nch}")
    if ch != scheduled(k, nch):
        raise ESFError(
            f"frame {k}: channel {ch} off schedule {scheduled(k, nch)}")
    if L > MAXPAY:
        raise ESFError(f"frame {k}: length {L} > {MAXPAY}")
    if seq != cseq[ch]:
        raise ESFError(
            f"frame {k}: channel {ch} seq {seq} != {cseq[ch]}")
    cseq[ch] += 1
    return ch, bytes(fr[28:28 + L]), fixed


def read_stream(data, nch, repair=False):
    """Verify and decode one .esf byte string. Returns a list of
    per-channel payload byte strings. Strict by default (repair=False):
    any corruption raises. With repair=True, consistent single-byte
    damage is fixed in the decoded view (use repair_stream to get the
    repaired file bytes)."""
    payloads, _, _ = _walk(data, nch, repair)
    return payloads


def repair_stream(data, nch):
    """Verify and REPAIR one .esf byte string. Returns
    (repaired_bytes, n_repaired, payloads). Raises ESFRefused on
    damage that is detected but not single-byte-repairable, ESFError
    on structural failure."""
    out = bytearray(data)
    if len(out) % FRAME != 0:
        raise ESFError(f"length {len(out)} not a multiple of {FRAME}")
    cseq = [0] * nch
    payloads = [bytearray() for _ in range(nch)]
    n_rep = 0
    for k in range(len(out) // FRAME):
        fr = out[k * FRAME:(k + 1) * FRAME]
        if fr[:4] != MAGIC:
            raise ESFRefused(f"frame {k}: bad magic (not repairable)")
        stored = struct.unpack("<III", fr[16:28])
        fixed = None
        if syndromes(fr) != stored:
            w = bytearray(fr)
            fixed = _repair(w, stored)
            out[k * FRAME:(k + 1) * FRAME] = w
            fr = w
            n_rep += 1
        ch, pay, _ = check_frame(fr, k, nch, cseq, repair=False)
        payloads[ch] += pay
    return bytes(out), n_rep, [bytes(p) for p in payloads]


def _walk(data, nch, repair):
    if len(data) % FRAME != 0:
        raise ESFError(f"length {len(data)} not a multiple of {FRAME}")
    if not 1 <= nch <= 8:
        raise ESFError(f"nch {nch} out of range")
    cseq = [0] * nch
    payloads = [bytearray() for _ in range(nch)]
    n_rep = 0
    fixes = []
    for k in range(len(data) // FRAME):
        fr = bytearray(data[k * FRAME:(k + 1) * FRAME])
        ch, pay, fixed = check_frame(fr, k, nch, cseq, repair=repair)
        if fixed is not None:
            n_rep += 1
            fixes.append((k, fixed))
        payloads[ch] += pay
    return [bytes(p) for p in payloads], n_rep, fixes


def max_gaps(nch, nframes):
    """Per-channel max inter-arrival gap of the schedule over
    nframes frames (gap measured in frames between consecutive
    arrivals of the same channel; the leading gap counts from 0)."""
    last = [-1] * nch
    gap = [0] * nch
    for k in range(nframes):
        c = scheduled(k, nch)
        gap[c] = max(gap[c], k - last[c])
        last[c] = k
    return gap
