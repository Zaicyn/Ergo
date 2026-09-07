#!/usr/bin/env python3
# actin_mirror.py - M4a mirror: FD cert, static cert oracle, rate calibration,
# mean-field ODE oracle, independent dynamics. Pure python+numpy, deterministic.
import numpy as np, sys

# ---- parameters (must match actin_filament.ergo) ----
LBOX   = 12.0
XWALL  = 0.5
KWALL  = 100.0
DT     = 0.005
KT     = 0.4
GAMMA  = 2.0
FCAP   = 500.0
KBOND  = 100.0
R0     = 0.5
KFIL   = 100.0
PITCH  = 0.6
RCROSS = 0.1            # PITCH - R0
SIG    = 0.5            # bead WCA sigma
C216   = 2.0 ** (1.0 / 6.0)
RCAP   = 1.4
QMIN   = 0.0
KON    = 500.0
KOFF   = 0.09
KSEED  = 5.0
SEED   = 77031
NMONO  = 60
NSEED  = 3
PHI_G  = 2.39996322972865332
WCUT   = C216 * SIG     # 0.5612

def head(m): return 2 * m
def tail(m): return 2 * m + 1

class Topo:
    def __init__(self, cap):
        self.state = np.zeros(cap, dtype=bool)
        self.prev  = np.full(cap, -1, dtype=int)
        self.next  = np.full(cap, -1, dtype=int)
        self.barbed = -1
        self.mlen = 0
        self.bonds = []          # junction springs (a, b, rest)
        self.excl = None

def rebuild_bonds(tp, nb):
    tp.bonds = []
    tp.excl = np.zeros((nb, nb), dtype=bool)
    for m in range(nb // 2):
        tp.excl[head(m), tail(m)] = True
        tp.excl[tail(m), head(m)] = True
    m = 0
    while tp.next[m] != -1:
        q = tp.next[m]
        tp.bonds.append((head(m), head(q), PITCH))
        tp.bonds.append((tail(m), tail(q), PITCH))
        tp.bonds.append((head(m), tail(q), RCROSS))
        for a, b in [(head(m), head(q)), (tail(m), tail(q)), (head(m), tail(q))]:
            tp.excl[a, b] = True; tp.excl[b, a] = True
        m = q

def forces(X, tp, anch, mask_active, energy=False):
    nb = X.shape[0]
    F = np.zeros_like(X)
    D = X[:, None, :] - X[None, :, :]
    d2 = np.einsum('ijk,ijk->ij', D, D)
    d = np.sqrt(np.maximum(d2, 1e-32))
    up = np.triu_indices(nb, 1)
    act = mask_active[:, None] & mask_active[None, :]
    pair = act[up] & (~tp.excl[up])
    dd = d[up]
    pair &= (dd >= 1e-12) & (dd < WCUT)
    b6 = np.zeros_like(dd); b6[pair] = (SIG / dd[pair]) ** 6
    fm = np.zeros_like(dd)
    fm[pair] = 24.0 * (2.0 * b6[pair] ** 2 - b6[pair]) / (dd[pair] ** 2)
    fm *= np.minimum(1.0, FCAP / np.maximum(np.abs(fm) * dd, 1e-16))
    ewca = float(np.sum(4.0 * (b6[pair] ** 2 - b6[pair]))) if energy else 0.0
    iu, ju = up
    fpair = (fm * pair)[:, None] * D[up]
    np.add.at(F, iu, fpair); np.add.at(F, ju, -fpair)
    ebond = 0.0
    for m in range(nb // 2):
        if not mask_active[head(m)]:
            continue
        dr = X[head(m)] - X[tail(m)]
        dd = max(float(np.linalg.norm(dr)), 1e-16)
        f = 2.0 * KBOND * (dd - R0) / dd
        F[head(m)] -= f * dr; F[tail(m)] += f * dr
        if energy: ebond += KBOND * (dd - R0) ** 2
    efil = 0.0
    for a, b, r0 in tp.bonds:
        dr = X[a] - X[b]
        dd = max(float(np.linalg.norm(dr)), 1e-16)
        f = 2.0 * KFIL * (dd - r0) / dd
        F[a] -= f * dr; F[b] += f * dr
        if energy: efil += KFIL * (dd - r0) ** 2
    eanch = 0.0
    for b in range(2):
        dr = anch[b] - X[b]
        F[b] += 2.0 * KSEED * dr
        if energy: eanch += KSEED * float(dr @ dr)
    ewall = 0.0
    for ax in range(3):
        lo = X[:, ax] < XWALL
        hi = X[:, ax] > LBOX - XWALL
        F[lo, ax] += 2.0 * KWALL * (XWALL - X[lo, ax])
        F[hi, ax] -= 2.0 * KWALL * (X[hi, ax] - (LBOX - XWALL))
        if energy:
            ewall += KWALL * float(np.sum((XWALL - X[lo, ax]) ** 2))
            ewall += KWALL * float(np.sum((X[hi, ax] - (LBOX - XWALL)) ** 2))
    if energy:
        return F, (ewca, ebond, efil, eanch, ewall)
    return F

def axes_of(X, nmono):
    ax = np.zeros((nmono, 3)); cen = np.zeros((nmono, 3))
    for m in range(nmono):
        dr = X[head(m)] - X[tail(m)]
        n = max(float(np.linalg.norm(dr)), 1e-16)
        ax[m] = dr / n; cen[m] = 0.5 * (X[head(m)] + X[tail(m)])
    return ax, cen

# deterministic per-bead jitter, identical formula both sides
def jitter(b):
    return 0.02 * np.array([np.sin(b * 1.7), np.cos(b * 2.3), np.sin(b * 0.9 + 1.0)])

# ---- cert config: hexamer on shallow arc + 10 spiral + 2 close-pair ----
def cert_config():
    nm = 18
    X = np.zeros((2 * nm, 3))
    c = LBOX / 2.0
    th = 0.03                                    # bend per junction
    cen = np.array([c, c, c])
    ax = np.array([1.0, 0.0, 0.0])
    pos = cen.copy()
    for i in range(6):
        if i > 0:
            phi = th * i
            ax = np.array([np.cos(phi), np.sin(phi), 0.0])
            pos = pos + PITCH * np.array([np.cos(phi - th), np.sin(phi - th), 0.0])
        X[head(i)] = pos + 0.25 * ax
        X[tail(i)] = pos - 0.25 * ax
    for k in range(10):                          # free spiral
        m = 6 + k
        phi = k * PHI_G
        pk = np.array([c + 4.5 * np.cos(phi), c + 4.5 * np.sin(phi), c - 1.5 + 3.0 * (k % 2)])
        ak = np.array([np.cos(phi + 1.0), np.sin(phi + 1.0), 0.5])
        ak = ak / np.linalg.norm(ak)
        X[head(m)] = pk + 0.25 * ak
        X[tail(m)] = pk - 0.25 * ak
    # close pair: centers 0.55 apart along y, axes along x (one WCA contact)
    pA = np.array([c + 3.0, c - 3.0, c]); pB = pA + np.array([0.0, 0.55, 0.0])
    for m, p in ((16, pA), (17, pB)):
        X[head(m)] = p + [0.25, 0, 0]
        X[tail(m)] = p - [0.25, 0, 0]
    anch = X[:2].copy()                          # un-jittered anchor targets
    for b in range(2 * nm):
        X[b] = X[b] + jitter(b)
    tp = Topo(nm)
    for i in range(6):
        tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1
    tp.prev[0] = -1; tp.next[5] = -1; tp.barbed = 5; tp.mlen = 6
    rebuild_bonds(tp, 2 * nm)
    return X, tp, anch

def fd_check():
    X, tp, anch = cert_config()
    rng = np.random.default_rng(12345)
    X = X + rng.normal(scale=0.03, size=X.shape)
    mask = np.ones(X.shape[0], dtype=bool)
    F, _ = forces(X, tp, anch, mask, energy=True)
    h = 1e-6
    worst = 0.0; worst_abs = 0.0
    for b in range(X.shape[0]):
        for ax in range(3):
            Xp = X.copy(); Xp[b, ax] += h
            Xm = X.copy(); Xm[b, ax] -= h
            _, ep = forces(Xp, tp, anch, mask, energy=True)
            _, em = forces(Xm, tp, anch, mask, energy=True)
            fd = -(sum(ep) - sum(em)) / (2 * h)
            an = F[b, ax]
            rel = abs(fd - an) / max(abs(an), 1.0)
            worst = max(worst, rel); worst_abs = max(worst_abs, abs(fd - an))
    print('FD check: max_rel_vs_1 %.3e  max_abs %.3e' % (worst, worst_abs))
    return worst

def cert():
    X, tp, anch = cert_config()
    mask = np.ones(X.shape[0], dtype=bool)
    F, (ew, eb, ef, ea, ewl) = forces(X, tp, anch, mask, energy=True)
    with open('/tmp/actin_cert_config.txt', 'w') as f:
        f.write('# MIRROR_DUMP nmono 18 mlen 6\n')
        for b in range(X.shape[0]):
            f.write('%.17e %.17e %.17e\n' % tuple(X[b]))
    with open('/tmp/actin_cert_forces.txt', 'w') as f:
        for b in range(X.shape[0]):
            f.write('%.17e %.17e %.17e\n' % tuple(F[b]))
    print('CERT ewca %.17e ebond %.17e efil %.17e eanch %.17e ewall %.17e' % (ew, eb, ef, ea, ewl))
    print('wrote /tmp/actin_cert_{config,forces}.txt')

def dyn_init(nmono, rng):
    X = np.zeros((2 * nmono, 3))
    c = LBOX / 2.0
    for i in range(NSEED):
        cen = np.array([c + (i - 1.0) * PITCH, c, c])
        X[head(i)] = cen + [0.25, 0, 0]
        X[tail(i)] = cen - [0.25, 0, 0]
    tp = Topo(nmono)
    for i in range(NSEED):
        tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1
    tp.prev[0] = -1; tp.next[NSEED - 1] = -1; tp.barbed = NSEED - 1; tp.mlen = NSEED
    placed = [X[b].copy() for i in range(NSEED) for b in (head(i), tail(i))]
    for m in range(NSEED, nmono):
        ok = False
        for _try in range(60):
            cen = 2.0 + (LBOX - 4.0) * rng.random(3)
            z = 2.0 * rng.random() - 1.0
            th = 2.0 * np.pi * rng.random()
            s = np.sqrt(max(0.0, 1.0 - z * z))
            ax = np.array([s * np.cos(th), s * np.sin(th), z])
            hb, tb = cen + 0.25 * ax, cen - 0.25 * ax
            if all(np.linalg.norm(hb - p) > 0.62 and np.linalg.norm(tb - p) > 0.62 for p in placed):
                X[head(m)] = hb; X[tail(m)] = tb
                placed += [hb.copy(), tb.copy()]
                ok = True; break
        if not ok:
            X[head(m)] = hb; X[tail(m)] = tb
            placed += [hb.copy(), tb.copy()]
    rebuild_bonds(tp, 2 * nmono)
    anch = X[:2].copy()
    return X, tp, anch

def kinetics(X, tp, nmono, rng, nbind, nunbind, allow_on=True, allow_off=True):
    ax, _ = axes_of(X, nmono)
    u_on = rng.random(); u_off = rng.random()
    if allow_on:
        hb = X[head(tp.barbed)]
        ab = ax[tp.barbed]
        for m in range(nmono):
            if tp.state[m]:
                continue
            if np.linalg.norm(X[tail(m)] - hb) < RCAP and float(ax[m] @ ab) > QMIN:
                if u_on < min(1.0, KON * DT):
                    # teleport to register on the barbed end
                    X[tail(m)] = hb + RCROSS * ab
                    X[head(m)] = X[tail(m)] + R0 * ab
                    tp.state[m] = True
                    tp.prev[m] = tp.barbed; tp.next[tp.barbed] = m
                    tp.next[m] = -1; tp.barbed = m; tp.mlen += 1
                    rebuild_bonds(tp, 2 * nmono)
                    nbind += 1
                break
    if allow_off and tp.mlen > NSEED:
        if u_off < KOFF * DT:
            m = tp.barbed; p = tp.prev[m]
            tp.next[p] = -1; tp.barbed = p
            tp.state[m] = False; tp.prev[m] = -1; tp.mlen -= 1
            # release-clear teleport: freed monomer must leave the capture window.
            # RCROSS+0.55 (0.65) is force-free but still < RCAP and aligned ->
            # instant-rebind trap (unbind becomes a no-op). Park it just OUTSIDE
            # the window at RCAP+0.25 = 1.65: force-free, not a candidate.
            ab = ax[p]
            hb2 = X[head(p)]
            X[tail(m)] = hb2 + (RCAP + 0.25) * ab
            X[head(m)] = X[tail(m)] + R0 * ab
            rebuild_bonds(tp, 2 * nmono)
            nunbind += 1
    return nbind, nunbind

def integrate_run(X, V, tp, anch, nmono, nsteps, rng, allow_on=True,
                  allow_off=True, ndiag=500, label='run', half_window=True):
    mask = np.ones(2 * nmono, dtype=bool)
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    nbind = 0; nunbind = 0
    lsum = 0.0; lcnt = 0
    for step in range(1, nsteps + 1):
        F = forces(X, tp, anch, mask)
        V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
        X = X + V * DT
        nbind, nunbind = kinetics(X, tp, nmono, rng, nbind, nunbind, allow_on, allow_off)
        if step % ndiag == 0:
            if half_window and step > nsteps // 2:
                lsum += tp.mlen; lcnt += 1
            print('%s step %6d len %3d nfree %3d binds %4d unbinds %4d' %
                  (label, step, tp.mlen, nmono - tp.mlen, nbind, nunbind), flush=True)
    lmean = lsum / max(lcnt, 1)
    print('%s FINAL lmean %.3f len %d nfree %d binds %d unbinds %d' %
          (label, lmean, tp.mlen, nmono - tp.mlen, nbind, nunbind), flush=True)
    return lmean

def calibrate():
    print('== k_off calibration: 15-mer, no pool, unbind only ==')
    rng = np.random.default_rng(SEED)
    nmono = 15
    X = np.zeros((2 * nmono, 3)); c = LBOX / 2.0
    for i in range(nmono):
        cen = np.array([c + (i - 7.0) * PITCH, c, c])
        X[head(i)] = cen + [0.25, 0, 0]; X[tail(i)] = cen - [0.25, 0, 0]
    tp = Topo(nmono)
    for i in range(nmono):
        tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1
    tp.prev[0] = -1; tp.next[nmono - 1] = -1; tp.barbed = nmono - 1; tp.mlen = nmono
    rebuild_bonds(tp, 2 * nmono)
    anch = X[:2].copy(); V = np.zeros_like(X)
    nsteps = 30000
    nbind = 0; nunbind = 0; nelig = 0
    mask = np.ones(2 * nmono, dtype=bool)
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    for step in range(1, nsteps + 1):
        F = forces(X, tp, anch, mask)
        V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
        X = X + V * DT
        if tp.mlen > NSEED:
            nelig += 1
        nbind, nunbind = kinetics(X, tp, nmono, rng, nbind, nunbind,
                                  allow_on=False, allow_off=True)
    koff = nunbind / max(nelig, 1)
    print('k_off_eff = %.6e /step  (%d unbinds in %d eligible steps, nominal %.3e)' %
          (koff, nunbind, nelig, KOFF * DT))

    print('== k_on calibration: trimer + fixed pool (unbind off) ==')
    slopes = []
    for npool in (20, 40, 60):
        rng = np.random.default_rng(SEED + npool)
        nmono = NSEED + npool
        X, tp, anch = dyn_init(nmono, rng)
        V = np.zeros_like(X)
        nsteps = 40000; nbind = 0; nunbind = 0
        for step in range(1, nsteps + 1):
            F = forces(X, tp, anch, np.ones(2 * nmono, dtype=bool))
            V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
            X = X + V * DT
            nbind, nunbind = kinetics(X, tp, nmono, rng, nbind, nunbind,
                                      allow_on=True, allow_off=False)
        c = npool / LBOX ** 3
        rate = nbind / nsteps
        slopes.append((c, rate))
        print('  pool %3d  c = %.6f  binds %4d  rate %.6e /step' % (npool, c, nbind, rate))
    cs = np.array([s[0] for s in slopes]); rs = np.array([s[1] for s in slopes])
    A = np.vstack([cs, np.ones_like(cs)]).T
    kon, r0 = np.linalg.lstsq(A, rs, rcond=None)[0]
    print('k_on slope = %.6e /step/conc (intercept %.3e)' % (kon, r0))
    cstar = koff / kon
    lstar = NMONO - cstar * LBOX ** 3
    print('PREDICTION: c* = %.6f  ->  L* = %.2f monomers (N=%d, V=%.0f)' %
          (cstar, lstar, NMONO, LBOX ** 3))
    return kon, koff

def run(nsteps=60000, kon=None, koff=None):
    rng = np.random.default_rng(SEED)
    X, tp, anch = dyn_init(NMONO, rng)
    V = np.zeros_like(X)
    lmean = integrate_run(X, V, tp, anch, NMONO, nsteps, rng)
    if kon is not None and koff is not None:
        Vvol = LBOX ** 3
        L = float(NSEED); t = []
        for step in range(nsteps // 500):
            for _ in range(500):
                L += kon * (NMONO - L) / Vvol - koff
            t.append(L)
        print('ODE steady L* = %.2f   ODE L(end) = %.2f   mirror lmean = %.2f' %
              (NMONO - (koff / kon) * Vvol, t[-1], lmean))

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] == '--fd':
        fd_check()
    elif args[0] == '--cert':
        cert()
    elif args[0] == '--cal':
        calibrate()
    elif args[0] == '--run':
        nsteps = int(args[1]) if len(args) > 1 else 60000
        run(nsteps)
    elif args[0] == '--full':
        # fd + cert + cal + run with oracle comparison
        fd_check(); cert()
        kon, koff = calibrate()
        run(60000, kon, koff)
