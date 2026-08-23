#!/usr/bin/env python3
"""run_stream.py — the .esf / file-I/O test suite (data-flow campaign,
deliverable D3; ESF2 repair extension). Tests:

  1. round-trip   4-channel .esf from esf_oracle.ergo, read back
                  byte-exact against the regenerated payload rule
  2. skew         per-channel max inter-arrival gap vs the scatter
                  bound (period 32), measured for C = 1..8
  3. corruption   3a: single-byte flips at every offset, strict
                  reader — detection floor |d| >= 1, zero escapes
                  (ESF2 covers zero-fill too; magic by equality)
                  3b: 1000 random multi-byte region flips (the v4
                  1000-direction mirror) — detected-and-refused,
                  miscorrections asserted 0 (bound ~2^-32, spec §3)
                  3c: 1500 single-byte corruptions — all repaired
                  byte-exactly; integrity-word/magic damage refused
  4. determinism  writer twice byte-identical; reader repair twice
                  identical
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
        # expected per-channel sequence at each frame ordinal
        nfr = len(esf_data) // 4096
        expseq = []
        seen = [0] * 4
        for k in range(nfr):
            c = esf_ref.scheduled(k, 4)
            expseq.append(seen[c])
            seen[c] += 1

        # 3a: single-byte flips at EVERY offset of the first frames,
        # strict reader (repair off) — every offset in [4,4096) is
        # syndrome-covered in ESF2 (zero-fill included); the magic
        # [0,4) is caught by equality. Nothing may escape.
        caught = missed = 0
        for k in range(3):
            fr = bytearray(esf_data[k * 4096:(k + 1) * 4096])
            for o in range(4096):
                orig = fr[o]
                fr[o] = orig ^ 0x5A
                cseq = [0] * 4
                cseq[esf_ref.scheduled(k, 4)] = expseq[k]
                try:
                    esf_ref.check_frame(fr, k, 4, cseq, repair=False)
                    missed += 1        # escape: FAILURE
                except esf_ref.ESFError:
                    caught += 1
                fr[o] = orig
        st = "PASS" if missed == 0 else "FAIL"
        report("3a corruption-1B", st,
               f"{caught} caught, {missed} escaped "
               f"(magic by equality, all else by syndromes)")

        # 3b: 1000 random region flips inside one random frame (v4
        # 1000-direction mirror), reader in repair mode: multi-byte
        # damage must be detected-and-refused; a "repair" that does
        # not restore the clean frame is a MISCORRECTION (assert 0,
        # bound ~2^-32 documented in the spec §3).
        rng = random.Random(20260823)
        det = rep_ok = miscorr = escaped = 0
        for _ in range(1000):
            f = rng.randrange(nfr)
            clean = esf_data[f * 4096:(f + 1) * 4096]
            L = struct.unpack("<H", clean[10:12])[0]
            live = 28 + L
            fr = bytearray(clean)
            o = rng.randrange(0, live)
            ln = rng.randrange(1, 65)
            for j in range(o, min(o + ln, live)):
                fr[j] ^= rng.randrange(1, 256)
            cseq = [0] * 4
            cseq[esf_ref.scheduled(f, 4)] = expseq[f]
            try:
                _, _, fixed = esf_ref.check_frame(
                    fr, f, 4, cseq, repair=True)
                if fixed is None:
                    escaped += 1        # silent accept: FAILURE
                elif bytes(fr) == clean:
                    rep_ok += 1         # degenerate 1-byte region
                else:
                    miscorr += 1        # miscorrection: FAILURE
            except esf_ref.ESFError:
                det += 1                # detected (refused/structural)
        st = "PASS" if escaped == 0 and miscorr == 0 else "FAIL"
        report("3b corruption-region", st,
               f"{det} detected-refused, {rep_ok} exact-repaired, "
               f"{miscorr} miscorrected, {escaped} escaped (of 1000)")

        # 3c: single-byte REPAIR — 1500 random (frame, offset, value)
        # over all covered offsets [4,4096) (header, payload, and the
        # ESF1-blind zero-fill). Every one must restore the frame
        # byte-exactly. Integrity-word offsets [16,28) and magic
        # [0,4) must be detected-and-refused (never miscorrected).
        rep = refused_ok = bad = 0
        for _ in range(1500):
            f = rng.randrange(nfr)
            clean = esf_data[f * 4096:(f + 1) * 4096]
            o = rng.randrange(4, 4096)
            fr = bytearray(clean)
            fr[o] = fr[o] ^ rng.randrange(1, 256)
            cseq = [0] * 4
            cseq[esf_ref.scheduled(f, 4)] = expseq[f]
            try:
                _, _, fixed = esf_ref.check_frame(
                    fr, f, 4, cseq, repair=True)
                if fixed is not None and bytes(fr) == clean:
                    rep += 1
                else:
                    bad += 1            # wrong repair: FAILURE
            except esf_ref.ESFRefused:
                if 16 <= o < 28:
                    refused_ok += 1     # integrity word: refuse is
                                        # the designed answer
                else:
                    bad += 1            # refused a repairable byte
            except esf_ref.ESFError:
                bad += 1
        # magic bytes: detected, refused, never miscorrected
        for o in range(4):
            fr = bytearray(esf_data[0:4096])
            fr[o] ^= 0x01
            try:
                esf_ref.check_frame(fr, 0, 4, [0, 0, 0, 0],
                                    repair=True)
                bad += 1
            except esf_ref.ESFError:
                refused_ok += 1
        st = "PASS" if bad == 0 else "FAIL"
        report("3c repair-1B", st,
               f"{rep} repaired byte-exact, {refused_ok} designed "
               f"refusals (integrity words + magic), {bad} wrong")

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
        # reader-side: repair pass is deterministic too — a fixed
        # corrupted file repaired twice gives identical bytes
        if esf_data is not None:
            d = bytearray(esf_data)
            d[4096 + 100] ^= 0x40
            d[3 * 4096 + 3000] ^= 0x81
            rb1 = esf_ref.repair_stream(bytes(d), 4)
            rb2 = esf_ref.repair_stream(bytes(d), 4)
            rd = rb1[0] == rb2[0] == esf_data and rb1[1] == rb2[1] == 2
        else:
            rd = False
        report("4 determinism", "PASS" if same and rd else "FAIL",
               f".esf {len(esf1)} B, .txt {len(txt1)} B, writer twice "
               "byte-identical; reader repair twice identical"
               if same and rd else "runs differ")

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
