#!/usr/bin/env python3
"""run_stream.py — the .esf / file-I/O test suite (data-flow campaign,
deliverable D3). Six tests:

  1. round-trip   4-channel .esf from esf_oracle.ergo, read back
                  byte-exact against the regenerated payload rule
  2. skew         per-channel max inter-arrival gap vs the scatter
                  bound (period 32), measured for C = 1..8
  3. corruption   single-byte flips over the whole summed region
                  (must all be caught — floor |d| >= 1) + 1000 random
                  region flips (the v4 1000-direction mirror)
  4. determinism  the oracle program run twice: .txt and .esf both
                  byte-identical
  5. overhead     .esf write throughput vs raw-record fwrite of the
                  same bytes (measured, reported — not promised)
  6. language     the oracle's formatted text file, byte-exact
                  against the expected content

Run from repo root:  python3 tests/stream/run_stream.py
Deterministic report except the throughput numbers (measurements).
Exit 0 = suite ran; read the table for the verdicts (FAIL lines are
the alarm).
"""

import os
import random
import struct
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, REPO)

import esf_ref

OUT = os.path.join(HERE, "out")
ROWS = []


def report(test, status, note=""):
    ROWS.append((test, status, note))


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, timeout=kw.pop(
        "timeout", 300), cwd=REPO, **kw)


def build(src, out):
    r = sh(["python", "-m", "core", src, "-o", out])
    if r.returncode != 0:
        report(os.path.basename(src), "FAIL",
               "build: " + r.stderr.decode(errors="replace")
               .strip().splitlines()[-1][:70])
        return None
    return out


def expected_channels():
    """Regenerate the oracle payload rule: channel ch, per-channel
    sequence s -> n = 4*(1 + s%3) ints, BUF(j) = ch*100000 + s*10 + j.
    Returns per-channel concatenated payload bytes."""
    cnt = [0, 0, 0, 0]
    chans = [bytearray() for _ in range(4)]
    for k in range(96):
        ch = esf_ref.scheduled(k, 4)
        s = cnt[ch]
        n = 4 * (1 + s % 3)
        chans[ch] += struct.pack(
            f"<{n}i", *[ch * 100000 + s * 10 + j
                        for j in range(1, n + 1)])
        cnt[ch] += 1
    return [bytes(c) for c in chans]


EXPECTED_TXT = ("('HEADER 7 0.125')\n"
                "('LINE 1')\n"
                "('LINE 2')\n").encode()


def main():
    os.makedirs(OUT, exist_ok=True)

    # ── build + run the oracle (feeds tests 1, 4, 6) ──
    oracle = build("tests/stream/esf_oracle.ergo", "/tmp/stream_oracle")
    esf_path = os.path.join(OUT, "oracle.esf")
    txt_path = os.path.join(OUT, "oracle.txt")
    esf_data = None
    if oracle:
        r = sh([oracle])
        if r.returncode != 0:
            report("oracle-run", "FAIL", r.stderr.decode()[-70:])
        else:
            with open(esf_path, "rb") as f:
                esf_data = f.read()

    # ── test 1: round-trip byte-exact ──
    if esf_data is not None:
        try:
            got = esf_ref.read_stream(esf_data, 4)
            want = expected_channels()
            if got == want:
                report("1 round-trip", "PASS",
                       f"4 channels, {len(esf_data)//4096} frames, "
                       "byte-exact")
            else:
                report("1 round-trip", "FAIL",
                       "channel payloads differ")
        except esf_ref.ESFError as e:
            report("1 round-trip", "FAIL", str(e)[:70])

    # ── test 2: skew bound (schedule geometry, all C) ──
    worst = []
    ok = True
    for c in range(1, 9):
        gaps = esf_ref.max_gaps(c, 32 * 1000)
        gmax = max(gaps)
        worst.append(f"C{c}:{gmax}")
        if gmax >= 32:
            ok = False
    report("2 skew", "PASS" if ok else "FAIL",
           "max gap " + " ".join(worst) + " (bound <32)")

    # ── test 3: corruption ──
    if esf_data is not None:
        # 3a: single-byte flips across every covered offset of the
        # first frames (magic, header, integrity words, payload).
        frames = [bytearray(esf_data[i * 4096:(i + 1) * 4096])
                  for i in range(3)]
        caught = missed = blind = 0
        for fr in frames:
            L = struct.unpack("<H", fr[10:12])[0]
            for o in range(4096):
                orig = fr[o]
                fr[o] = orig ^ 0x5A
                try:
                    esf_ref.read_stream(bytes(fr), 4)
                    if 28 + L <= o:
                        blind += 1     # zero-fill: documented blind
                    else:
                        missed += 1    # summed-region escape: FAILURE
                except esf_ref.ESFError:
                    caught += 1
                fr[o] = orig
        st = "PASS" if missed == 0 else "FAIL"
        report("3a corruption-1B", st,
               f"{caught} caught, {missed} escaped, "
               f"{blind} zero-fill (documented blind)")
        # 3b: 1000 random region flips inside the summed region of a
        # random frame (v4 1000-direction mirror; zero-fill is never
        # interpreted, so corruption is injected where the reader
        # looks — the blind region is covered by 3a accounting).
        rng = random.Random(20260823)
        nfr = len(esf_data) // 4096
        det = 0
        for _ in range(1000):
            d = bytearray(esf_data)
            f = rng.randrange(nfr)
            L = struct.unpack(
                "<H", d[f * 4096 + 10:f * 4096 + 12])[0]
            live = 28 + L          # interpreted bytes per frame
            o = f * 4096 + rng.randrange(0, live)
            ln = rng.randrange(1, 65)
            for j in range(o, min(o + ln, f * 4096 + live)):
                d[j] ^= rng.randrange(1, 256)
            try:
                esf_ref.read_stream(bytes(d), 4)
            except esf_ref.ESFError:
                det += 1
        st = "PASS" if det == 1000 else "FAIL"
        report("3b corruption-region", st,
               f"{det}/1000 random region flips detected")

    # ── test 4: determinism ──
    if oracle:
        with open(esf_path, "rb") as f:
            esf1 = f.read()
        with open(txt_path, "rb") as f:
            txt1 = f.read()
        r = sh([oracle])
        with open(esf_path, "rb") as f:
            esf2 = f.read()
        with open(txt_path, "rb") as f:
            txt2 = f.read()
        same = esf1 == esf2 and txt1 == txt2 and r.returncode == 0
        report("4 determinism", "PASS" if same else "FAIL",
               f".esf {len(esf1)} B, .txt {len(txt1)} B, "
               "two runs byte-identical" if same else "runs differ")

    # ── test 5: overhead (measured) ──
    b_esf = build("tests/stream/esf_bench_esf.ergo", "/tmp/stream_besf")
    b_raw = build("tests/stream/esf_bench_raw.ergo", "/tmp/stream_braw")
    if b_esf and b_raw:
        t0 = time.perf_counter()
        sh([b_esf])
        t1 = time.perf_counter()
        sh([b_raw])
        t2 = time.perf_counter()
        nbytes = 20000 * 1017 * 4
        v_esf = nbytes / (t1 - t0) / 1e6
        v_raw = nbytes / (t2 - t1) / 1e6
        report("5 overhead", "MEASURED",
               f".esf {v_esf:.0f} MB/s vs raw {v_raw:.0f} MB/s "
               f"(x{v_raw / max(v_esf, 1e-9):.2f})")

    # ── test 6: language oracle (formatted file, byte-exact) ──
    if os.path.exists(txt_path):
        with open(txt_path, "rb") as f:
            txt = f.read()
        report("6 language-oracle", "PASS" if txt == EXPECTED_TXT
               else "FAIL", "formatted file byte-exact"
               if txt == EXPECTED_TXT else f"got {txt[:40]!r}")

    print("=" * 68)
    print("STREAM SUITE — file I/O (Part 10) + .esf framed stream")
    print("=" * 68)
    for test, status, note in ROWS:
        print(f"  {status:9s} {test:22s} {note}")
    n_fail = sum(1 for r in ROWS if r[1] == "FAIL")
    print("-" * 68)
    print(f"  {len(ROWS) - n_fail} ok, {n_fail} FAIL (of {len(ROWS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
