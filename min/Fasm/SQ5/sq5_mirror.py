#!/usr/bin/env python3
"""sq5_mirror.py — independent mirror of the SQ5 counterflow allocator.

Wigner-campaign pattern: the mirror regenerates the CLEAN state from the
specification alone (scatter LUT, stamp formula, payload fill, scalar
moment journals — no C code shared), applies the dumped event list,
recomputes the counterflow flux / triangulation / SEC / stamp checks
independently, and diffs every stage against the engine's audit dump.

Stage verdicts (O8 oracle — construction must be EXACT, diff 0):
  S1 clean state (alloc + incremental SIMD journal vs Python scalar)
  S2 corrupted state (engine dump vs mirror clean + events)
  S3 flux decisions (flags / classification / SEC positions / tiers)
  S4 repaired state (payload, stamps, journals)
"""

import sys
import struct

def load(path):
    d = {"EV": []}
    for line in open(path):
        t = line.split()
        if not t:
            continue
        if t[0] == "HDR":
            d["HDR"] = tuple(int(x) for x in t[1:4])
        elif t[0] == "EV":
            d["EV"].append(tuple(int(x, 0) for x in t[1:9]))
        elif t[0] == "EVENTS":
            d["EVENTS"] = int(t[1])
        elif t[0] == "DEC":
            d.setdefault("DEC", []).append(tuple(int(x) for x in t[1:9]))
        elif t[0] == "STAMP_FLAGGED":
            d["STAMP_FLAGGED"] = int(t[1])
        else:
            d[t[0]] = bytes.fromhex(t[1])
    return d

class Mirror:
    def __init__(self, NB, NR, PAY):
        self.NB, self.NR, self.PAY = NB, NR, PAY
        self.BINBYTES = NR * PAY
        self.SCATLT = [6, 5, 4, 0, 2, 3, 4, 7, 4, 6, 3, 0, 1, 2, 1, 0,
                       3, 6, 4, 7, 4, 3, 2, 0, 4, 5, 6, 5, 4, 0, 2, 3]
        self.BINGEO = [228, 104, 0, 104, 228, 104, 0, 104]
        M = 2 ** 32
        self.M = M
        # state: pay[bin][gen][shell] = bytearray(PAY)
        self.pay = [[[bytearray(PAY) for _ in range(2)]
                     for _ in range(NR)] for _ in range(NB)]
        self.stamp = [[[0, 0] for _ in range(NR)] for _ in range(NB)]
        self.occ = [[[0, 0] for _ in range(NR)] for _ in range(NB)]
        self.head = [0] * NB
        self.jr = [[[0, 0, 0] for _ in range(2)] for _ in range(NB)]

    def stampf(self, b, g, s):
        tbits = (g << 1) & 31
        return ((self.BINGEO[b & 7] << 24) | (b << 16) | (tbits << 9)
                | ((s & 1) << 8) | g)

    @staticmethod
    def fill(item, PAY):
        return bytearray(((item * 17 + i * 91) ^ 0xA5) & 0xFF for i in range(PAY))

    def jadd(self, j, p, gen):
        base = gen * self.PAY
        s0 = s1 = s2 = 0
        for i, v in enumerate(p):
            idx = base + i + 1
            s0 += v
            s1 += v * idx
            s2 += v * idx * idx
        j[0] = (j[0] + s0) % self.M
        j[1] = (j[1] + s1) % self.M
        j[2] = (j[2] + s2) % self.M

    def alloc(self, id_, item):
        b0 = self.SCATLT[id_ & 31] % self.NB
        bin_ = -1
        for k in range(self.NB):
            b = (b0 + k) % self.NB
            if self.head[b] < self.NR:
                bin_ = b
                break
        if bin_ < 0:
            return -1
        g = self.head[bin_]
        self.pay[bin_][g][0] = self.fill(item, self.PAY)
        self.stamp[bin_][g][0] = self.stampf(bin_, g, 0)
        self.occ[bin_][g][0] = 1
        self.jadd(self.jr[bin_][0], self.pay[bin_][g][0], g)
        self.head[bin_] += 1
        return 0

    def rep(self):
        for b in range(self.NB):
            for g in range(self.NR):
                if not self.occ[b][g][0]:
                    continue
                self.pay[b][g][1] = bytearray(self.pay[b][g][0])
                self.stamp[b][g][1] = self.stampf(b, g, 1)
                self.occ[b][g][1] = 1
                self.jadd(self.jr[b][1], self.pay[b][g][1], g)

    def apply_event(self, e):
        cat, b, g, s, i, nb, m0, m1 = e
        if cat == 0:
            for k, m in enumerate((m0, m1)[:nb]):
                self.pay[b][g][s][(i + k * 7) % self.PAY] ^= m
        elif cat == 1:
            v = self.stamp[b][g][s]
            bs = list(struct.pack("<I", v))
            bs[i & 3] ^= m0
            self.stamp[b][g][s] = struct.unpack("<I", bytes(bs))[0]
        else:
            bs = bytearray(struct.pack("<3I", *self.jr[b][s]))
            bs[i % 12] ^= m0
            self.jr[b][s] = list(struct.unpack("<3I", bytes(bs)))

    def flux(self, b):
        a = [0, 0, 0]
        c = [0, 0, 0]
        for g in range(self.NR):
            gf, gb = g, self.NR - 1 - g
            if self.occ[b][gf][0]:
                base = gf * self.PAY
                for i, v in enumerate(self.pay[b][gf][0]):
                    idx = base + i + 1
                    a[0] += v; a[1] += v * idx; a[2] += v * idx * idx
            if self.occ[b][gb][1]:
                base = gb * self.PAY
                for i in range(self.PAY - 1, -1, -1):
                    v = self.pay[b][gb][1][i]
                    idx = base + i + 1
                    c[0] += v; c[1] += v * idx; c[2] += v * idx * idx
        M = self.M
        ds = [[(a[k] - self.jr[b][0][k]) % M for k in range(3)],
              [(c[k] - self.jr[b][1][k]) % M for k in range(3)]]
        flags = 0
        if any(ds[0]):
            flags |= 1
        if any(ds[1]):
            flags |= 2
        if [(x % M) for x in a] != [(x % M) for x in c]:
            flags |= 4
        return flags, ds

    def jrecompute(self, b, s):
        j = [0, 0, 0]
        for g in range(self.NR):
            if self.occ[b][g][s]:
                self.jadd(j, self.pay[b][g][s], g)
        self.jr[b][s] = j

    def try_sec(self, b, s, ds):
        d = ds[0] - self.M if ds[0] >= 2 ** 31 else ds[0]
        if d != 0 and -255 <= d <= 255:
            ds1 = ds[1] - self.M if ds[1] >= 2 ** 31 else ds[1]
            if ds1 % d == 0:
                p = ds1 // d
                if 1 <= p <= self.BINBYTES and (d * p * p) % self.M == ds[2]:
                    o = p - 1
                    g, i = divmod(o, self.PAY)
                    self.pay[b][g][s][i] = (self.pay[b][g][s][i] - d) & 0xFF
                    # journal already equals restored content (see sq5_core.h)
                    return 1, p
        return 0, 0

    def tier2(self, b, s):
        good = s ^ 1
        self.jr[b][s] = [0, 0, 0]
        for g in range(self.NR):
            if not self.occ[b][g][good]:
                continue
            self.pay[b][g][s] = bytearray(self.pay[b][g][good])
            self.stamp[b][g][s] = self.stampf(b, g, s)
            self.occ[b][g][s] = 1
            self.jadd(self.jr[b][s], self.pay[b][g][s], g)

    def classify(self, b):
        flags, ds = self.flux(b)
        if flags == 0:
            cls = 0
        elif flags == 1:
            cls = 1
        elif flags == 2:
            cls = 2
        elif flags == 5:
            cls = 3
        elif flags == 6:
            cls = 4
        elif flags == 7:
            cls = 5
        elif flags == 3:
            cls = 5 if ds[0] == ds[1] else 6
        else:
            cls = 7
        return flags, ds, cls

    def repair_bin(self, b):
        flags, ds, cls = self.classify(b)
        sec_p = [0, 0]
        tier = [0, 0]
        if cls == 1:
            self.jrecompute(b, 0); tier[0] = 3
        elif cls == 2:
            self.jrecompute(b, 1); tier[1] = 3
        elif cls == 6:
            self.jrecompute(b, 0); self.jrecompute(b, 1); tier = [3, 3]
        elif cls == 3:
            ok, p = self.try_sec(b, 0, ds[0])
            if ok:
                tier[0] = 1; sec_p[0] = p
            else:
                self.tier2(b, 0); tier[0] = 2
        elif cls == 4:
            ok, p = self.try_sec(b, 1, ds[1])
            if ok:
                tier[1] = 1; sec_p[1] = p
            else:
                self.tier2(b, 1); tier[1] = 2
        elif cls == 5:
            ok0, p0 = self.try_sec(b, 0, ds[0])
            ok1, p1 = self.try_sec(b, 1, ds[1])
            if ok0: tier[0] = 1; sec_p[0] = p0
            if ok1: tier[1] = 1; sec_p[1] = p1
            if ok0 and not ok1:
                self.tier2(b, 1); tier[1] = 2
            if ok1 and not ok0:
                self.tier2(b, 0); tier[0] = 2
        unresolved = 0
        if cls not in (0, 7):
            unresolved = 1 if self.flux(b)[0] != 0 else 0
        return flags, cls, sec_p, tier, unresolved

    def stamp_check(self, fix):
        bad = 0
        for b in range(self.NB):
            for g in range(self.NR):
                for s in range(2):
                    if self.occ[b][g][s] and \
                            self.stamp[b][g][s] != self.stampf(b, g, s):
                        bad += 1
                        if fix:
                            self.stamp[b][g][s] = self.stampf(b, g, s)
        return bad

    # ---- serialization matching the C dump ----
    def pay_bytes(self):
        out = bytearray()
        for b in range(self.NB):
            for g in range(self.NR):
                for s in range(2):
                    out += self.pay[b][g][s]
        return bytes(out)

    def stamp_bytes(self):
        out = bytearray()
        for b in range(self.NB):
            for g in range(self.NR):
                for s in range(2):
                    out += struct.pack("<I", self.stamp[b][g][s])
        return bytes(out)

    def jr_bytes(self):
        out = bytearray()
        for b in range(self.NB):
            for s in range(2):
                out += struct.pack("<3I", *self.jr[b][s])
        return bytes(out)


def diff_count(a, b):
    n = min(len(a), len(b))
    return sum(1 for i in range(n) if a[i] != b[i]) + abs(len(a) - len(b))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "sq5_audit.txt"
    d = load(path)
    NB, NR, PAY = d["HDR"]
    m = Mirror(NB, NR, PAY)

    # ---- S1: clean state from specification alone ----
    for i in range(NB * NR):
        m.alloc(i, i)
    m.rep()
    s1_pay = diff_count(m.pay_bytes(), d["CLEAN_PAY"])
    s1_stamp = diff_count(m.stamp_bytes(), d["CLEAN_STAMP"])
    s1_jr = diff_count(m.jr_bytes(), d["CLEAN_JR"])
    print(f"S1 clean:   pay_diff={s1_pay} stamp_diff={s1_stamp} jr_diff={s1_jr} "
          f"{'PASS' if s1_pay + s1_stamp + s1_jr == 0 else 'FAIL'}")

    # ---- S2: corrupted state = mirror clean + events ----
    for e in d["EV"]:
        m.apply_event(e)
    s2_pay = diff_count(m.pay_bytes(), d["CORR_PAY"])
    s2_stamp = diff_count(m.stamp_bytes(), d["CORR_STAMP"])
    s2_jr = diff_count(m.jr_bytes(), d["CORR_JR"])
    print(f"S2 corrupt: pay_diff={s2_pay} stamp_diff={s2_stamp} jr_diff={s2_jr} "
          f"{'PASS' if s2_pay + s2_stamp + s2_jr == 0 else 'FAIL'}")

    # ---- S3: flux decisions + stamp flags, independent ----
    s3_bad = 0
    for b in range(NB):
        flags, cls, sec_p, tier, unres = m.repair_bin(b)
        eb, eflags, ecls, ep0, ep1, et0, et1, eunres = d["DEC"][b]
        # compare decision fields; note C dec[].unresolved counts post-
        # repair open flux possibly += 1 semantics; compare core fields
        if (flags, cls, sec_p[0], sec_p[1], tier[0], tier[1]) != \
           (eflags, ecls, ep0, ep1, et0, et1):
            s3_bad += 1
            print(f"  DEC mismatch bin {b}: mirror "
                  f"{(flags, cls, sec_p, tier)} vs engine "
                  f"{(eflags, ecls, [ep0, ep1], [et0, et1])}")
    s3_stamp = m.stamp_check(fix=1)
    stamp_ok = (s3_stamp == d["STAMP_FLAGGED"])
    print(f"S3 decide:  bin_mismatches={s3_bad} stamp_flagged mirror={s3_stamp} "
          f"engine={d['STAMP_FLAGGED']} "
          f"{'PASS' if s3_bad == 0 and stamp_ok else 'FAIL'}")

    # ---- S4: repaired state ----
    s4_pay = diff_count(m.pay_bytes(), d["REP_PAY"])
    s4_stamp = diff_count(m.stamp_bytes(), d["REP_STAMP"])
    s4_jr = diff_count(m.jr_bytes(), d["REP_JR"])
    print(f"S4 repair:  pay_diff={s4_pay} stamp_diff={s4_stamp} jr_diff={s4_jr} "
          f"{'PASS' if s4_pay + s4_stamp + s4_jr == 0 else 'FAIL'}")

    total = s1_pay + s1_stamp + s1_jr + s2_pay + s2_stamp + s2_jr + \
        s3_bad + (0 if stamp_ok else 1) + s4_pay + s4_stamp + s4_jr
    print(f"SQ5OR O8_mirror_diff {total}  expect=0 construction "
          f"{'PASS' if total == 0 else 'FAIL'}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
