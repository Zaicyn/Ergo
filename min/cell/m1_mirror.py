#!/usr/bin/env python3
"""m1_mirror.py — M1 certification mirror: independent Python
reimplementation of the vesicle_asm.ergo force set, diffed against the
engine's dumped step-1 forces at f64.

Reads /tmp/m1_config.txt (positions) and /tmp/m1_forces.txt (engine
forces) produced by the MIRROR=1 build of min/cell/vesicle_asm.ergo.
Recomputes the full force (pair classes + bonds + bending) by brute
force (N^2, index-order summation — the engine sums in cell-list slot
order, so the expected residual is float-summation-order noise only).

Force set (must match vesicle_asm.ergo exactly):
  TAIL-TAIL: full LJ (sig=1, eps=1), force cutoff RCTT=2.6
  HEAD-HEAD: WCA, sig=1.05, cutoff 2^(1/6)*1.05
  HEAD-TAIL: WCA, sig=0.95, cutoff 2^(1/6)*0.95
  bond:      harmonic K_B=100, r0=0.5 (head 2i-1, tail 2i)
  bending:   E = -KAL (A_i . A_j), KAL=1.5, center pairs within RB=2.6;
             F_d = KAL/L_i [A_j - (A_i.A_j) A_i], +F_d head, -F_d tail
  PURETAIL control: every bead a free TAIL (full LJ only).
"""

import math
import sys

SIG, SHH, SHT = 1.0, 1.05, 0.95
RCTT = 2.6
CWHH = 2.0 ** (1.0 / 6.0) * SHH
CWHT = 2.0 ** (1.0 / 6.0) * SHT
KBOND, R0, KAL, RB = 100.0, 0.5, 1.5, 2.6
FCAP = 500.0


def lj_f(sr6, d):
    return 24.0 * (2.0 * sr6 * sr6 - sr6) / (d * d)


def main():
    cfg = open("/tmp/m1_config.txt").read().split()
    namph, puretail = int(cfg[0]), int(cfg[1])
    nb = 2 * namph
    pos = [tuple(map(float, cfg[2 + 3 * i:5 + 3 * i])) for i in range(nb)]
    eng = open("/tmp/m1_forces.txt").read().split()
    f_eng = [tuple(map(float, eng[3 * i:3 + 3 * i])) for i in range(nb)]

    fx = [0.0] * nb
    fy = [0.0] * nb
    fz = [0.0] * nb

    # pair forces, brute N^2, ordered pairs (i, j) like the engine's
    # full neighbor list
    for i in range(nb):
        xi, yi, zi = pos[i]
        i_tail = (i % 2 == 1) or puretail  # bead index i+1 even = tail
        for j in range(nb):
            if j == i:
                continue
            if not puretail and (i // 2) == (j // 2):
                continue  # bonded partner excluded (engine NBR_BUILD)
            dx = xi - pos[j][0]
            dy = yi - pos[j][1]
            dz = zi - pos[j][2]
            d = math.sqrt(dx * dx + dy * dy + dz * dz)
            if d <= 1.0e-12:
                continue
            j_tail = (j % 2 == 1) or puretail
            if i_tail and j_tail:
                if d >= RCTT:
                    continue
                sr = SIG / d
            elif (not i_tail) and (not j_tail):
                if d >= CWHH:
                    continue
                sr = SHH / d
            else:
                if d >= CWHT:
                    continue
                sr = SHT / d
            sr6 = sr ** 6
            fm = lj_f(sr6, d)
            if fm != 0.0:  # pair-force cap (engine: FM * MIN(1, FCAP/|FM|))
                fm = fm * min(1.0, FCAP / abs(fm))
            fx[i] += fm * dx
            fy[i] += fm * dy
            fz[i] += fm * dz

    if not puretail:
        # axes
        ax = [0.0] * namph
        ay = [0.0] * namph
        az = [0.0] * namph
        alen = [0.0] * namph
        for a in range(namph):
            h, t = 2 * a, 2 * a + 1
            bx = pos[h][0] - pos[t][0]
            by = pos[h][1] - pos[t][1]
            bz = pos[h][2] - pos[t][2]
            L = max(math.sqrt(bx * bx + by * by + bz * bz), 1.0e-16)
            ax[a], ay[a], az[a], alen[a] = bx / L, by / L, bz / L, L
            # bond force: on head -2*KB*(L-r0)*u, on tail opposite
            fb = 2.0 * KBOND * (L - R0) / L
            fx[h] += -fb * bx
            fy[h] += -fb * by
            fz[h] += -fb * bz
            fx[t] += fb * bx
            fy[t] += fb * by
            fz[t] += fb * bz
        # bending: center pairs within RB, ordered
        cen = [((pos[2 * a][0] + pos[2 * a + 1][0]) * 0.5,
                (pos[2 * a][1] + pos[2 * a + 1][1]) * 0.5,
                (pos[2 * a][2] + pos[2 * a + 1][2]) * 0.5)
               for a in range(namph)]
        for i in range(namph):
            sx = sy = sz = 0.0
            for j in range(namph):
                if j == i:
                    continue
                dx = cen[i][0] - cen[j][0]
                dy = cen[i][1] - cen[j][1]
                dz = cen[i][2] - cen[j][2]
                dc = math.sqrt(dx * dx + dy * dy + dz * dz)
                if dc >= RB:
                    continue
                dot = ax[i] * ax[j] + ay[i] * ay[j] + az[i] * az[j]
                sx += ax[j] - dot * ax[i]
                sy += ay[j] - dot * ay[i]
                sz += az[j] - dot * az[i]
            h, t = 2 * i, 2 * i + 1
            fx[h] += KAL * sx / alen[i]
            fy[h] += KAL * sy / alen[i]
            fz[h] += KAL * sz / alen[i]
            fx[t] -= KAL * sx / alen[i]
            fy[t] -= KAL * sy / alen[i]
            fz[t] -= KAL * sz / alen[i]

    maxabs = 0.0
    maxrel = 0.0
    for i in range(nb):
        for c, fm in enumerate((fx, fy, fz)):
            d = abs(fm[i] - f_eng[i][c])
            maxabs = max(maxabs, d)
            m = max(abs(f_eng[i][c]), 1.0)
            maxrel = max(maxrel, d / m)
    print(f"mirror: N={namph} puretail={puretail} "
          f"max|dF|={maxabs:.6e} max_rel={maxrel:.6e}")
    ok = maxrel < 1.0e-9
    print("MIRROR PASS" if ok else "MIRROR FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
