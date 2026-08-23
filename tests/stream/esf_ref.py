#!/usr/bin/env python3
"""esf_ref.py — Python reference reader for the .esf framed stream
format (Spec/Ergo_Stream_Format.md). Shared by the tests in this
directory; imported, not run.

Every frame check is computed (magic equality, direct-addressed
schedule, per-channel sequence, 3-axis integrity residual) — nothing
is searched.
"""

import struct

SCATLT = (6, 5, 4, 0, 2, 3, 4, 7, 4, 6, 3, 0, 1, 2, 1, 0,
          3, 6, 4, 7, 4, 3, 2, 0, 4, 5, 6, 5, 4, 0, 2, 3)

FRAME = 4096
MAXPAY = 4068


class ESFError(Exception):
    pass


def scheduled(k, nch):
    """Channel of frame k — direct addressing, never searched."""
    return SCATLT[k % 32] % nch


def integrity(frame, L):
    """3 rotated projections over [4,16) ∪ [28, 28+L)."""
    s = [0, 0, 0]
    for o in range(4, 16):
        s[(o - 4) % 3] = (s[(o - 4) % 3] + frame[o]) & 0xFFFFFFFF
    for o in range(28, 28 + L):
        s[(o - 4) % 3] = (s[(o - 4) % 3] + frame[o]) & 0xFFFFFFFF
    return tuple(s)


def read_stream(data, nch):
    """Verify and decode one .esf byte string. Returns a list of
    per-channel payload byte strings (concatenated, in channel
    sequence order). Raises ESFError on the first failed check."""
    if len(data) % FRAME != 0:
        raise ESFError(f"length {len(data)} not a multiple of {FRAME}")
    if not 1 <= nch <= 8:
        raise ESFError(f"nch {nch} out of range")
    payloads = [bytearray() for _ in range(nch)]
    cseq = [0] * nch
    for k in range(len(data) // FRAME):
        fr = data[k * FRAME:(k + 1) * FRAME]
        if fr[:4] != b"ESF1":
            raise ESFError(f"frame {k}: bad magic")
        kk, = struct.unpack("<I", fr[4:8])
        ch, L = struct.unpack("<HH", fr[8:12])
        seq, = struct.unpack("<I", fr[12:16])
        stored = struct.unpack("<III", fr[16:28])
        if kk != k:
            raise ESFError(f"frame {k}: index field {kk}")
        if ch >= nch:
            raise ESFError(f"frame {k}: channel {ch} >= nch {nch}")
        if ch != scheduled(k, nch):
            raise ESFError(
                f"frame {k}: channel {ch} off schedule "
                f"{scheduled(k, nch)}")
        if L > MAXPAY:
            raise ESFError(f"frame {k}: length {L} > {MAXPAY}")
        if seq != cseq[ch]:
            raise ESFError(
                f"frame {k}: channel {ch} seq {seq} != {cseq[ch]}")
        if integrity(fr, L) != stored:
            raise ESFError(f"frame {k}: integrity residual nonzero")
        payloads[ch] += fr[28:28 + L]
        cseq[ch] += 1
    return [bytes(p) for p in payloads]


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
