#!/usr/bin/env python3
# angle_oracle.py - controlled branch-angle certification: frozen STRAIGHT
# 12-mer mother, daughter trimer free (8 branch springs BRB1..8 + ladder +
# WCA vs mother, Langevin kT=0.4). Measures the relaxed equilibrium angle of
# the daughter base (cen d2 - cen d1) vs the mother axis. Isolates the
# junction geometry from mother-filament conformational fluctuation.
import numpy as np, sys

PITCH = 0.6; R0 = 0.5; RCROSS = 0.1; KFIL = 100.0; KBOND = 100.0
SIG = 0.5; WCUT = 2.0 ** (1.0 / 6.0) * SIG
DT = 0.005; GAMMA = 2.0; KT = 0.4
CB = 0.46174861323503386   # cos(62.5) build angle
SB = 0.88701083317822171   # sin(62.5)
BLAT = 0.9; BAX = -0.2

def run(build_deg=62.5, nsteps=60000, seed=1, wca=True):
    a = np.array([1.0, 0, 0]); p = np.array([0.0, -1, 0])
    mb = np.concatenate([np.stack([m * PITCH * a + 0.25 * a, m * PITCH * a - 0.25 * a])
                         for m in range(12)])          # frozen mother beads
    tail = lambda m: mb[2 * m - 1]; head = lambda m: mb[2 * m - 2]
    h, n, n2, n3 = 3, 4, 5, 6
    anch = np.array([tail(h), head(h), tail(n), head(n),
                     tail(n2), head(n2), tail(n3), head(n3)])
    cb, sb = np.cos(np.radians(build_deg)), np.sin(np.radians(build_deg))
    b = cb * a + sb * p
    cd = 3 * PITCH * a + BLAT * p + BAX * a
    X = np.array([cd + k * PITCH * b + 0.25 * b for k in range(3)] +
                 [cd + k * PITCH * b - 0.25 * b for k in range(3)])
    d1t, d1h = cd - 0.25 * b, cd + 0.25 * b
    d2t, d2h = cd + 0.35 * b, cd + 0.85 * b
    BRB = [np.linalg.norm(d1t - tail(h)), np.linalg.norm(d1h - head(h)),
           np.linalg.norm(d1t - tail(n)), np.linalg.norm(d1h - head(n)),
           np.linalg.norm(d2t - tail(n2)), np.linalg.norm(d2h - head(n2)),
           np.linalg.norm(d2t - tail(n3)), np.linalg.norm(d2h - head(n3))]
    ASP = [(3, 0), (0, 1), (3, 2), (0, 3), (4, 4), (1, 5), (4, 6), (1, 7)]  # anchor-indexed
    sp = []
    for i in range(3): sp.append((i, i + 3, R0, KBOND, 'd'))
    for i, j in [(0, 1), (1, 2)]:
        sp += [(i, j, PITCH, KFIL, 'd'), (i + 3, j + 3, PITCH, KFIL, 'd'), (i, j + 3, RCROSS, KFIL, 'd')]
    for (xi, ai), r in zip(ASP, BRB):
        sp.append((xi, ai, r, KFIL, 'a'))
    MBI = [5, 4, 7, 6, 9, 8, 11, 10]  # mb bead index of each anchor slot
    bmask = np.ones((6, 24), bool)
    for i, j in ASP:
        bmask[i, MBI[j]] = False
    def forces(X):
        F = np.zeros_like(X)
        for aa, bb, r, K, kind in sp:
            pa = X[aa]; pb = anch[bb] if kind == 'a' else X[bb]
            d = pa - pb; dd = max(np.linalg.norm(d), 1e-16); f = 2 * K * (dd - r) / dd
            F[aa] -= f * d
            if kind != 'a':
                F[bb] += f * d
        if wca:
            d = X[:, None, :] - mb[None, :, :]
            dd = np.linalg.norm(d, axis=-1); dd = np.maximum(dd, 1e-16)
            act = (dd < WCUT) & bmask
            br = SIG / dd; b6 = br ** 6
            fm = 24 * (2 * b6 * b6 - b6) / (dd * dd) * act
            F += np.sum(fm[..., None] * d, axis=1)
        return F
    rng = np.random.default_rng(seed)
    V = np.zeros_like(X); angs = []
    NA = np.sqrt(12 * KT * (1 - (1 - GAMMA * DT) ** 2))
    for it in range(nsteps):
        F = forces(X)
        V = V * (1 - GAMMA * DT) + F * DT + NA * (rng.random(X.shape) - 0.5)
        X = X + V * DT
        if it % 200 == 0 and it > nsteps // 3:
            d1c = 0.5 * (X[0] + X[3]); d2c = 0.5 * (X[1] + X[4])
            bb = (d2c - d1c) / np.linalg.norm(d2c - d1c)
            angs.append(np.degrees(np.arccos(np.clip(bb @ a, -1, 1))))
    return np.array(angs)

if __name__ == '__main__':
    nsteps = int(sys.argv[1]) if len(sys.argv) > 1 else 60000
    an = run(62.5, nsteps)
    print('frozen straight mother, build 62.5 deg: relaxed angle mean %.2f std %.2f, q05/50/95 %s (n=%d)'
          % (an.mean(), an.std(), np.round(np.percentile(an, [5, 50, 95]), 1), len(an)))
