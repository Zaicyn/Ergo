#!/usr/bin/env python3
# hydrolysis_mirror.py - M4H mirror: ATP hydrolysis + nucleotide-state kinetics,
# barbed end only. FD cert, static cert oracle (CFG/FRC/NUC/CERT), rate
# calibration (koff forced-ATP / forced-ADP, k_hyd, kon slope), mean-field
# cap model, independent dynamics with cap-profile + terminal-state stats.
# Pure python+numpy, deterministic. Params overridable via env vars.
import numpy as np, sys, os

# ---- parameters (must match hydrolysis.ergo) ----
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
KOFF_T = float(os.environ.get('KOFF_T', 0.045))   # barbed unbind, ATP terminal
KOFF_A = float(os.environ.get('KOFF_A', 0.18))    # barbed unbind, ADP terminal
KHYD   = float(os.environ.get('KHYD', 0.03))      # ATP->ADP, P = KHYD*DT/bound monomer
KSEED  = 5.0
SEED   = int(os.environ.get('SEED', 77031))
NMONO  = int(os.environ.get('NMONO', 60))
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
    # nucleotide state: free pool ATP; bound hexamer carries an ADP pattern
    tp.nuc[:] = 1
    tp.nuc[1] = 0      # engine monomer 2
    tp.nuc[3] = 0      # engine monomer 4
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
    outdir = os.environ.get('CERT_DIR', '/tmp/m4h')
    with open(os.path.join(outdir, 'hydro_cert_config.txt'), 'w') as f:
        f.write('# MIRROR_DUMP nmono 18 mlen 6\n')
        for b in range(X.shape[0]):
            f.write('%.17e %.17e %.17e\n' % tuple(X[b]))
    with open(os.path.join(outdir, 'hydro_cert_forces.txt'), 'w') as f:
        for b in range(X.shape[0]):
            f.write('%.17e %.17e %.17e\n' % tuple(F[b]))
    with open(os.path.join(outdir, 'hydro_cert_nuc.txt'), 'w') as f:
        for m in range(18):
            f.write('NUC %d %d\n' % (m + 1, tp.nuc[m]))
    print('CERT ewca %.17e ebond %.17e efil %.17e eanch %.17e ewall %.17e' % (ew, eb, ef, ea, ewl))
    print('wrote hydro_cert_{config,forces,nuc}.txt to %s' % outdir)

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

def kinetics(X, tp, anch, nmono, rng, ctr, allow_on=True, allow_off=True,
             allow_hyd=True, step=0, half=False):
    """Draws/step: u_on, u_off, uh[nmono] (unconditional). Order: hydrolysis,
    terminal occupancy tally, barbed bind (NUC<-ATP), barbed unbind
    (rate by terminal NUC, release at RCAP+0.25, NUC<-ATP)."""
    ax, _ = axes_of(X, nmono)
    u_on = rng.random(); u_off = rng.random()
    uh = rng.random(nmono)
    if allow_hyd:
        for mm in range(nmono):
            if tp.state[mm] and tp.nuc[mm] == 1 and uh[mm] < KHYD * DT:
                tp.nuc[mm] = 0; ctr['nhyd'] += 1
    if tp.mlen > NSEED and half:
        ctr['elt2'] += 1
        if tp.nuc[tp.barbed] == 1:
            ctr['eat2'] += 1
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
                    tp.nuc[mm] = 1
                    tp.prev[mm] = tp.barbed; tp.next[tp.barbed] = mm
                    tp.next[mm] = -1; tp.barbed = mm; tp.mlen += 1
                    rebuild_bonds(tp, 2 * nmono)
                    ctr['nb'] += 1
                break
    if allow_off and tp.mlen > NSEED:
        rk = KOFF_T if tp.nuc[tp.barbed] == 1 else KOFF_A
        if u_off < rk * DT:
            mm = tp.barbed; p = tp.prev[mm]
            if half:
                if tp.nuc[mm] == 1: ctr['uat2'] += 1
                else:               ctr['uad2'] += 1
            tp.next[p] = -1; tp.barbed = p
            tp.state[mm] = False; tp.prev[mm] = -1; tp.mlen -= 1
            tp.nuc[mm] = 1
            ab = ax[p]
            hb2 = X[head(p)]
            X[tail(mm)] = hb2 + (RCAP + 0.25) * ab
            X[head(mm)] = X[tail(mm)] + R0 * ab
            rebuild_bonds(tp, 2 * nmono)
            ctr['nu'] += 1

def integrate_run(X, V, tp, anch, nmono, nsteps, rng, allow_on=True,
                  allow_off=True, allow_hyd=True, ndiag=500, label='run'):
    mask = np.ones(2 * nmono, dtype=bool)
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    ctr = dict(nb=0, nu=0, nhyd=0, elt2=0, eat2=0, uat2=0, uad2=0)
    lsum = 0.0; lsq = 0.0; lcnt = 0
    capsum = np.zeros(nmono); capcnt = np.zeros(nmono)
    lens = []
    for step in range(1, nsteps + 1):
        F = forces(X, tp, anch, mask)
        V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
        X = X + V * DT
        half = step > nsteps // 2
        kinetics(X, tp, anch, nmono, rng, ctr, allow_on, allow_off, allow_hyd,
                 step, half)
        if step % ndiag == 0:
            if half:
                lsum += tp.mlen; lsq += tp.mlen * tp.mlen; lcnt += 1
                # cap profile: walk from barbed tip
                m = tp.barbed; d = 0
                while m != -1:
                    capcnt[d] += 1; capsum[d] += tp.nuc[m]
                    m = tp.prev[m]; d += 1
                lens.append(tp.mlen)
            natp = int(sum(tp.nuc[mm] for mm in range(nmono) if tp.state[mm]))
            kt2 = float(np.sum(V * V)) / (3.0 * 2 * nmono)
            print('%s step %6d kt %.4f lenfil %3d nfree %3d natp %2d nuct %d binds %4d unbinds %4d nhyd %d' %
                  (label, step, kt2, tp.mlen, nmono - tp.mlen, natp,
                   tp.nuc[tp.barbed], ctr['nb'], ctr['nu'], ctr['nhyd']), flush=True)
    lmean = lsum / max(lcnt, 1)
    lvar = lsq / max(lcnt, 1) - lmean * lmean
    print('%s FINAL lenfil %d lmean %.4f lvar %.4f nfree %d natp %d binds %d unbinds %d nhyd %d' %
          (label, tp.mlen, lmean, lvar, nmono - tp.mlen,
           int(sum(tp.nuc[mm] for mm in range(nmono) if tp.state[mm])),
           ctr['nb'], ctr['nu'], ctr['nhyd']), flush=True)
    koff_eff = (ctr['uat2'] + ctr['uad2']) / max(ctr['elt2'], 1)
    print('%s TERMSTATS elig %d atpterm %d unb_atp %d unb_adp %d koff_eff %.6e' %
          (label, ctr['elt2'], ctr['eat2'], ctr['uat2'], ctr['uad2'], koff_eff), flush=True)
    for d in range(nmono):
        if capcnt[d] > 0:
            print('%s CAP %d %d %.6f' % (label, d, int(capcnt[d]), capsum[d] / capcnt[d]), flush=True)
    return lmean, lvar, np.array(lens)

def straight_filament(nmono):
    X = np.zeros((2 * nmono, 3)); c = LBOX / 2.0
    for i in range(nmono):
        cen = np.array([c + (i - (nmono - 1) / 2.0) * PITCH, c, c])
        X[head(i)] = cen + [0.25, 0, 0]; X[tail(i)] = cen - [0.25, 0, 0]
    tp = Topo(nmono)
    for i in range(nmono):
        tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1
    tp.prev[0] = -1; tp.next[nmono - 1] = -1
    tp.barbed = nmono - 1; tp.pointed = 0; tp.anchm = 0; tp.mlen = nmono
    rebuild_bonds(tp, 2 * nmono)
    anch = X[:2].copy()
    return X, tp, anch

def calibrate():
    """M4H rate ladder: barbed koff forced-ATP, forced-ADP; k_hyd; kon slope.
    Then self-consistent mean-field cap model."""
    print('== k_off calibration: 15-mer epochs, no pool, kinetics=unbind only ==')
    koff = {}
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    for tag, nucval in (('ATP', 1), ('ADP', 0)):
        rng = np.random.default_rng(SEED)
        nev = 0; nelig = 0
        for epoch in range(40):
            X, tp, anch = straight_filament(15)
            tp.nuc[:] = nucval
            V = np.zeros_like(X)
            ctr = dict(nb=0, nu=0, nhyd=0, elt2=0, eat2=0, uat2=0, uad2=0)
            for step in range(1, 30001):
                if tp.mlen <= NSEED:
                    break          # decayed to floor: restart epoch
                F = forces(X, tp, anch, np.ones(2 * 15, dtype=bool))
                V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
                X = X + V * DT
                nelig += 1
                kinetics(X, tp, anch, 15, rng, ctr, allow_on=False,
                         allow_off=True, allow_hyd=False)
                tp.nuc[:] = nucval     # pin nucleotide state (no recharge drift)
            nev += ctr['nu']
        k = nev / max(nelig, 1)
        nom = (KOFF_T if nucval == 1 else KOFF_A) * DT
        err = np.sqrt(nev) / max(nelig, 1)
        print('k_off_%s_eff = %.6e +- %.1e /step  (%d events in %d eligible steps, nominal %.3e, ratio %.3f)' %
              (tag, k, err, nev, nelig, nom, k / nom), flush=True)
        koff[tag] = k

    print('== k_hyd calibration: 15-mer all-ATP epochs, bind/unbind off ==')
    rng = np.random.default_rng(SEED + 9)
    nhyd = 0; bsteps = 0
    for epoch in range(20):
        X, tp, anch = straight_filament(15)
        tp.nuc[:] = 1
        V = np.zeros_like(X)
        ctr = dict(nb=0, nu=0, nhyd=0, elt2=0, eat2=0, uat2=0, uad2=0)
        for step in range(1, 30001):
            F = forces(X, tp, anch, np.ones(2 * 15, dtype=bool))
            V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
            X = X + V * DT
            bsteps += sum(1 for mm in range(15) if tp.state[mm] and tp.nuc[mm] == 1)
            kinetics(X, tp, anch, 15, rng, ctr, allow_on=False,
                     allow_off=False, allow_hyd=True)
        nhyd += ctr['nhyd']
    kh = nhyd / max(bsteps, 1)
    err = np.sqrt(nhyd) / max(bsteps, 1)
    print('k_hyd_eff = %.6e +- %.1e /step/monomer  (%d events, %d ATP-monomer-steps, nominal %.3e, ratio %.3f)' %
          (kh, err, nhyd, bsteps, KHYD * DT, kh / (KHYD * DT)), flush=True)

    print('== k_on calibration: trimer + fixed pool (unbind off), barbed only ==')
    slopes_b = []
    for npool in (20, 40, 60):
        rng = np.random.default_rng(SEED + npool)
        nmono = NSEED + npool
        X, tp, anch = dyn_init(nmono, rng)
        V = np.zeros_like(X)
        na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
        nsteps = 40000
        ctr = dict(nb=0, nu=0, nhyd=0, elt2=0, eat2=0, uat2=0, uad2=0)
        for step in range(1, nsteps + 1):
            F = forces(X, tp, anch, np.ones(2 * nmono, dtype=bool))
            V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
            X = X + V * DT
            kinetics(X, tp, anch, nmono, rng, ctr, allow_on=True,
                     allow_off=False, allow_hyd=False)
        c = npool / LBOX ** 3
        slopes_b.append((c, ctr['nb'] / nsteps))
        print('  pool %3d  c = %.6f  binds %4d (%.3e /step)' %
              (npool, c, ctr['nb'], ctr['nb'] / nsteps))
    cs = np.array([s[0] for s in slopes_b]); rs = np.array([s[1] for s in slopes_b])
    A = np.vstack([cs, np.ones_like(cs)]).T
    kon_b, _ = np.linalg.lstsq(A, rs, rcond=None)[0]
    print('k_on_b slope = %.6e /step/conc' % kon_b)

    # ---- self-consistent mean-field cap model ----
    # gross on-rate v = kon*c; terminal ATP prob p = v/(v+h) (age ~ Exp(v));
    # koff_eff(v) = p*koffT + (1-p)*koffA; steady state v = rcap_fac*koff_eff(v)
    # with rcap_fac=0.8 the documented dynamic return-capture factor (M4a).
    h = KHYD * DT; kT_s = KOFF_T * DT; kA_s = KOFF_A * DT
    for fac, tag in ((1.0, 'nominal (lower bound on L*)'), (0.8, '0.8x return-capture (dynamic)')):
        vs = np.linspace(1e-6, 2e-3, 20000)
        p = vs / (vs + h)
        keff = p * kT_s + (1.0 - p) * kA_s
        resid = vs - fac * keff
        i = int(np.argmin(np.abs(resid)))
        v = vs[i]
        c = v / kon_b
        L = NMONO - c * LBOX ** 3
        cap = v / h
        print('MF[%s]: v* = %.3e/step, p(ATP term) = %.3f, koff_eff = %.3e/step, c* = %.5f, L* = %.1f, cap = v/h = %.2f monomers' %
              (tag, v, v / (v + h), fac * (v / (v + h) * kT_s + h / (v + h) * kA_s), c, L, cap))
    return kon_b, koff['ATP'], koff['ADP'], kh

def run(nsteps=150000):
    rng = np.random.default_rng(SEED)
    X, tp, anch = dyn_init(NMONO, rng)
    V = np.zeros_like(X)
    print('# HYDROLYSIS mirror M4H NMONO=%d KOFF_T=%f KOFF_A=%f KHYD=%f KT=%f SEED=%d nsteps=%d' %
          (NMONO, KOFF_T, KOFF_A, KHYD, KT, SEED, nsteps), flush=True)
    lmean, lvar, lens = integrate_run(X, V, tp, anch, NMONO, nsteps, rng)
    return lmean, lvar, lens

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] == '--fd':
        fd_check()
    elif args[0] == '--cert':
        cert()
    elif args[0] == '--cal':
        calibrate()
    elif args[0] == '--run':
        nsteps = int(args[1]) if len(args) > 1 else 150000
        run(nsteps)
    elif args[0] == '--full':
        fd_check(); cert(); calibrate(); run(150000)
