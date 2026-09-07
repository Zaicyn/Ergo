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
KONP     = 25.0     # pointed bind: P = KONP*DT (chemistry-limited)
KOFFB_T  = 0.015    # barbed unbind, ATP terminal
KOFFB_A  = 0.03     # barbed unbind, ADP terminal
KOFFP_T  = 0.03     # pointed unbind, ATP terminal
KOFFP_A  = 0.06     # pointed unbind, ADP terminal
KHYD     = 0.2      # ATP->ADP hydrolysis P = KHYD*DT per bound monomer
DOPOINTED = 1
DOHYD     = 1
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
        self.pointed = -1
        self.anchm = 0
        self.nuc = np.ones(cap, dtype=int)   # 1 = ATP, 0 = ADP
        self.mlen = 0
        self.bonds = []          # junction springs (a, b, rest)
        self.excl = None

def rebuild_bonds(tp, nb):
    tp.bonds = []
    tp.excl = np.zeros((nb, nb), dtype=bool)
    for m in range(nb // 2):
        tp.excl[head(m), tail(m)] = True
        tp.excl[tail(m), head(m)] = True
    m = tp.pointed
    while m != -1 and tp.next[m] != -1:
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
    for k, b in enumerate((head(tp.anchm), tail(tp.anchm))):
        dr = anch[k] - X[b]
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
    tp.prev[0] = -1; tp.next[5] = -1; tp.barbed = 5
    tp.pointed = 0; tp.anchm = 0; tp.mlen = 6
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
    tp.prev[0] = -1; tp.next[NSEED - 1] = -1; tp.barbed = NSEED - 1; tp.pointed = 0; tp.anchm = 0; tp.mlen = NSEED
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

def kinetics(X, tp, anch, nmono, rng, nb, nu, nbp, nup, nhyd,
             allow_on=True, allow_off=True):
    ax, _ = axes_of(X, nmono)
    u_on = rng.random(); u_off = rng.random()
    u_onp = rng.random(); u_offp = rng.random()
    if DOHYD:
        uh = rng.random(nmono)
        for mm in range(nmono):
            if tp.state[mm] and tp.nuc[mm] == 1 and uh[mm] < KHYD * DT:
                tp.nuc[mm] = 0; nhyd += 1
    if allow_on:
        hb = X[head(tp.barbed)]
        ab = ax[tp.barbed]
        for mm in range(nmono):
            if tp.state[mm]:
                continue
            if np.linalg.norm(X[tail(mm)] - hb) < RCAP and float(ax[mm] @ ab) > QMIN:
                if u_on < min(1.0, KON * DT):
                    X[tail(mm)] = hb + RCROSS * ab
                    X[head(mm)] = X[tail(mm)] + R0 * ab
                    tp.state[mm] = True
                    tp.prev[mm] = tp.barbed; tp.next[tp.barbed] = mm
                    tp.next[mm] = -1; tp.barbed = mm; tp.mlen += 1
                    rebuild_bonds(tp, 2 * nmono)
                    nb += 1
                break
    if allow_off and tp.mlen > NSEED:
        rk = KOFFB_T if (DOHYD and tp.nuc[tp.barbed] == 1) else KOFFB_A
        if u_off < rk * DT:
            mm = tp.barbed; p = tp.prev[mm]
            tp.next[p] = -1; tp.barbed = p
            tp.state[mm] = False; tp.prev[mm] = -1; tp.mlen -= 1
            tp.nuc[mm] = 1
            ab = ax[p]
            hb2 = X[head(p)]
            X[tail(mm)] = hb2 + (RCAP + 0.25) * ab
            X[head(mm)] = X[tail(mm)] + R0 * ab
            rebuild_bonds(tp, 2 * nmono)
            nu += 1
    if DOPOINTED:
        if allow_on:
            tb = X[tail(tp.pointed)]
            ap = ax[tp.pointed]
            for mm in range(nmono):
                if tp.state[mm]:
                    continue
                if np.linalg.norm(X[head(mm)] - tb) < RCAP and float(ax[mm] @ ap) > QMIN:
                    if u_onp < min(1.0, KONP * DT):
                        X[head(mm)] = tb - RCROSS * ap
                        X[tail(mm)] = X[head(mm)] - R0 * ap
                        tp.state[mm] = True
                        tp.next[mm] = tp.pointed; tp.prev[tp.pointed] = mm
                        tp.prev[mm] = -1; tp.pointed = mm; tp.mlen += 1
                        rebuild_bonds(tp, 2 * nmono)
                        nbp += 1
                    break
        if allow_off and tp.mlen > NSEED:
            rk = KOFFP_T if (DOHYD and tp.nuc[tp.pointed] == 1) else KOFFP_A
            if u_offp < rk * DT:
                mm = tp.pointed; q = tp.next[mm]
                tp.prev[q] = -1; tp.pointed = q
                tp.state[mm] = False; tp.next[mm] = -1; tp.mlen -= 1
                tp.nuc[mm] = 1
                if mm == tp.anchm:
                    # NPF re-grips the new pointed monomer in place
                    tp.anchm = q
                    anch[0][:] = X[head(q)]
                    anch[1][:] = X[tail(q)]
                aq = ax[q]
                X[head(mm)] = X[tail(q)] - (RCAP + 0.25) * aq
                X[tail(mm)] = X[head(mm)] - R0 * aq
                rebuild_bonds(tp, 2 * nmono)
                nup += 1
    return nb, nu, nbp, nup, nhyd

def integrate_run(X, V, tp, anch, nmono, nsteps, rng, allow_on=True,
                  allow_off=True, ndiag=500, label='run', half_window=True):
    mask = np.ones(2 * nmono, dtype=bool)
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    nb = 0; nu = 0; nbp = 0; nup = 0; nhyd = 0
    lsum = 0.0; lcnt = 0
    tips = []
    for step in range(1, nsteps + 1):
        F = forces(X, tp, anch, mask)
        V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
        X = X + V * DT
        nb, nu, nbp, nup, nhyd = kinetics(X, tp, anch, nmono, rng,
                                          nb, nu, nbp, nup, nhyd,
                                          allow_on, allow_off)
        if step % ndiag == 0:
            if half_window and step > nsteps // 2:
                lsum += tp.mlen; lcnt += 1
            natp = int(sum(tp.nuc[mm] for mm in range(nmono) if tp.state[mm]))
            tips.append((step, X[head(tp.barbed)].copy(), X[tail(tp.pointed)].copy()))
            print('%s step %6d len %3d nfree %3d natp %2d binds %4d unbinds %4d bindp %4d unbindp %4d nhyd %d' %
                  (label, step, tp.mlen, nmono - tp.mlen, natp, nb, nu, nbp, nup, nhyd), flush=True)
    lmean = lsum / max(lcnt, 1)
    print('%s FINAL lmean %.3f len %d nfree %d binds %d unbinds %d bindp %d unbindp %d nhyd %d' %
          (label, lmean, tp.mlen, nmono - tp.mlen, nb, nu, nbp, nup, nhyd), flush=True)
    return lmean, tips

def calibrate():
    """M4b rate ladder: per-end koff (forced ADP), per-end kon slope,
    k_hyd. Mean-field two-end prediction incl. treadmilling flux."""
    global DOHYD
    mask15 = None

    def koff_leg(end):
        # 15-mer, no pool, only this end unbinds, hydrolysis off (all ADP)
        global DOHYD
        sv = DOHYD; DOHYD = 0
        rng = np.random.default_rng(SEED)
        nmono = 15
        X = np.zeros((2 * nmono, 3)); c = LBOX / 2.0
        for i in range(nmono):
            cen = np.array([c + (i - 7.0) * PITCH, c, c])
            X[head(i)] = cen + [0.25, 0, 0]; X[tail(i)] = cen - [0.25, 0, 0]
        tp = Topo(nmono)
        for i in range(nmono):
            tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1
        tp.prev[0] = -1; tp.next[nmono - 1] = -1
        tp.barbed = nmono - 1; tp.pointed = 0; tp.anchm = 0; tp.mlen = nmono
        tp.nuc[:] = 0
        rebuild_bonds(tp, 2 * nmono)
        anch = X[:2].copy(); V = np.zeros_like(X)
        na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
        nsteps = 30000
        nb = nu = nbp = nup = nhyd = 0; nelig = 0
        svdp = globals()['DOPOINTED']
        if end == 'barbed':
            globals()['DOPOINTED'] = 0
        for step in range(1, nsteps + 1):
            F = forces(X, tp, anch, np.ones(2 * nmono, dtype=bool))
            V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
            X = X + V * DT
            if tp.mlen > NSEED:
                nelig += 1
            if end == 'barbed':
                nb, nu, nbp, nup, nhyd = kinetics(X, tp, anch, nmono, rng,
                                                  nb, nu, nbp, nup, nhyd,
                                                  allow_on=False, allow_off=True)
            else:
                nb, nu, nbp, nup, nhyd = kinetics(X, tp, anch, nmono, rng,
                                                  nb, nu, nbp, nup, nhyd,
                                                  allow_on=False, allow_off=True)
        globals()['DOPOINTED'] = svdp
        DOHYD = sv
        n = nu if end == 'barbed' else nup
        k = n / max(nelig, 1)
        nom = (KOFFB_A if end == 'barbed' else KOFFP_A) * DT
        print('k_off_%s_eff = %.6e /step  (%d events in %d eligible steps, nominal %.3e)' %
              (end, k, n, nelig, nom))
        return k

    print('== k_off calibration (ADP terminals, single end live) ==')
    kb = koff_leg('barbed')
    kp = koff_leg('pointed')

    print('== k_hyd calibration: 15-mer, kinetics off, hydrolysis on ==')
    rng = np.random.default_rng(SEED + 9)
    nmono = 15
    X = np.zeros((2 * nmono, 3)); c = LBOX / 2.0
    for i in range(nmono):
        cen = np.array([c + (i - 7.0) * PITCH, c, c])
        X[head(i)] = cen + [0.25, 0, 0]; X[tail(i)] = cen - [0.25, 0, 0]
    tp = Topo(nmono)
    for i in range(nmono):
        tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1
    tp.prev[0] = -1; tp.next[nmono - 1] = -1
    tp.barbed = nmono - 1; tp.pointed = 0; tp.anchm = 0; tp.mlen = nmono
    rebuild_bonds(tp, 2 * nmono)
    anch = X[:2].copy(); V = np.zeros_like(X)
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    nsteps = 20000
    nb = nu = nbp = nup = nhyd = 0; bsteps = 0
    for step in range(1, nsteps + 1):
        F = forces(X, tp, anch, np.ones(2 * nmono, dtype=bool))
        V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
        X = X + V * DT
        bsteps += sum(1 for mm in range(nmono) if tp.state[mm] and tp.nuc[mm] == 1)
        nb, nu, nbp, nup, nhyd = kinetics(X, tp, anch, nmono, rng,
                                          nb, nu, nbp, nup, nhyd,
                                          allow_on=False, allow_off=False)
    kh = nhyd / max(bsteps, 1)
    print('k_hyd_eff = %.6e /step/monomer  (%d events, %d ATP-monomer-steps, nominal %.3e)' %
          (kh, nhyd, bsteps, KHYD * DT))

    print('== k_on calibration: trimer + fixed pool (unbind off), both ends ==')
    slopes_b = []; slopes_p = []
    for npool in (20, 40, 60):
        rng = np.random.default_rng(SEED + npool)
        nmono = NSEED + npool
        X, tp, anch = dyn_init(nmono, rng)
        V = np.zeros_like(X)
        na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
        nsteps = 40000; nb = nu = nbp = nup = nhyd = 0
        for step in range(1, nsteps + 1):
            F = forces(X, tp, anch, np.ones(2 * nmono, dtype=bool))
            V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
            X = X + V * DT
            nb, nu, nbp, nup, nhyd = kinetics(X, tp, anch, nmono, rng,
                                              nb, nu, nbp, nup, nhyd,
                                              allow_on=True, allow_off=False)
        c = npool / LBOX ** 3
        slopes_b.append((c, nb / nsteps)); slopes_p.append((c, nbp / nsteps))
        print('  pool %3d  c = %.6f  binds_b %4d (%.3e)  binds_p %4d (%.3e)' %
              (npool, c, nb, nb / nsteps, nbp, nbp / nsteps))
    def slope(sl):
        cs = np.array([s[0] for s in sl]); rs = np.array([s[1] for s in sl])
        A = np.vstack([cs, np.ones_like(cs)]).T
        return np.linalg.lstsq(A, rs, rcond=None)[0]
    kon_b, _ = slope(slopes_b); kon_p, _ = slope(slopes_p)
    print('k_on_b slope = %.6e   k_on_p slope = %.6e /step/conc' % (kon_b, kon_p))
    Vvol = LBOX ** 3
    css = (kb + kp) / (kon_b + kon_p)
    lstar = NMONO - css * Vvol
    flux = kon_b * css - kb
    print('PREDICTION: c** = %.6f -> L* = %.2f monomers; treadmilling flux T = %.3e/step (%.1f monomers/150k)' %
          (css, lstar, flux, flux * 150000))
    return kon_b, kon_p, kb, kp, kh

def run(nsteps=60000, pred=None):
    rng = np.random.default_rng(SEED)
    X, tp, anch = dyn_init(NMONO, rng)
    V = np.zeros_like(X)
    lmean, tips = integrate_run(X, V, tp, anch, NMONO, nsteps, rng)
    if pred is not None:
        kon_b, kon_p, kb, kp = pred
        Vvol = LBOX ** 3
        css = (kb + kp) / (kon_b + kon_p)
        L = float(NSEED); t = []
        for step in range(nsteps // 500):
            for _ in range(500):
                L += (kon_b + kon_p) * (NMONO - L) / Vvol - (kb + kp)
            t.append(L)
        print('ODE steady L* = %.2f   ODE L(end) = %.2f   mirror lmean = %.2f' %
              (NMONO - css * Vvol, t[-1], lmean))
    return tips

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
        pred = calibrate()
        run(60000, pred[:4])
