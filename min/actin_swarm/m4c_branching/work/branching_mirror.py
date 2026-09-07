#!/usr/bin/env python3
# branching_mirror.py - M4c mirror: FD cert, static cert oracle, rate calibration
# (KBR branch rate in isolation, multi-chain kon/koff), multi-chain ODE oracle,
# independent dynamics. Pure python+numpy, deterministic.
# Multi-filament refactor of the certified M4a mirror: NFMAX chains, per-chain
# (pointed, barbed, mlen, live, host); Arp2/3-like branch events spawning a
# daughter trimer at a 62.5-deg build angle (relaxed mean 70 deg) held by 8
# branch springs to host + 3 barbed-side neighbor monomers (BRB1..BRB8).
import numpy as np, sys

# ---- parameters (must match branching.ergo) ----
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
KBR    = 0.02
C70    = 0.46174861323503386   # cos(62.5 deg) build angle
S70    = 0.88701083317822171   # sin(62.5 deg)
BLAT   = 0.9
BAX    = -0.2
BRB    = [0.68139666108583519, 1.1705816660755957, 0.95017156014555315,
          1.4600468667073012, 1.5627249250101813, 2.0777203167506473,
          1.9970415052495438, 2.4871546250964522]
KSEED  = 5.0
SEED   = 77031
NMONO  = 90
NFMAX  = 8
NSEED  = 3
PHI_G  = 2.39996322972865332
WCUT   = C216 * SIG     # 0.5612
DEG    = 57.29577951308232

def head(m): return 2 * m
def tail(m): return 2 * m + 1

class Topo:
    def __init__(self, cap):
        self.state  = np.zeros(cap, dtype=bool)
        self.prev   = np.full(cap, -1, dtype=int)
        self.next   = np.full(cap, -1, dtype=int)
        self.mchain = np.zeros(cap, dtype=int)
        self.hostof = np.zeros(cap, dtype=int)   # chain hosted at monomer
        self.hprot  = np.zeros(cap, dtype=int)   # branch anchor (unbind-blocked)
        self.cpoint = np.zeros(NFMAX, dtype=int)
        self.cbarb  = np.zeros(NFMAX, dtype=int)
        self.cmlen  = np.zeros(NFMAX, dtype=int)
        self.clive  = np.zeros(NFMAX, dtype=bool)
        self.chost  = np.zeros(NFMAX, dtype=int)
        self.cn     = np.zeros(NFMAX, dtype=int)
        self.cn2    = np.zeros(NFMAX, dtype=int)
        self.cn3    = np.zeros(NFMAX, dtype=int)
        self.bonds = []          # (a, b, rest): ladders then branch springs
        self.excl = None

def rebuild_bonds(tp, nb):
    tp.bonds = []
    tp.excl = np.zeros((nb, nb), dtype=bool)
    for m in range(nb // 2):
        tp.excl[head(m), tail(m)] = True
        tp.excl[tail(m), head(m)] = True
    # chain ladders, chains ascending, pointed->barbed (engine order)
    for f in range(NFMAX):
        if not tp.clive[f]:
            continue
        m = tp.cpoint[f]
        for _ in range(nb // 2):
            q = tp.next[m]
            if q == -1:
                break
            tp.bonds.append((head(m), head(q), PITCH))
            tp.bonds.append((tail(m), tail(q), PITCH))
            tp.bonds.append((head(m), tail(q), RCROSS))
            for a, b in [(head(m), head(q)), (tail(m), tail(q)), (head(m), tail(q))]:
                tp.excl[a, b] = True; tp.excl[b, a] = True
            m = q
    # branch springs, chains ascending: BRB1..BRB8 in engine order
    for f in range(NFMAX):
        if not (tp.clive[f] and tp.chost[f] > 0):
            continue
        d1 = tp.cpoint[f]; d2 = tp.next[d1]
        h = tp.chost[f]; n = tp.cn[f]; n2 = tp.cn2[f]; n3 = tp.cn3[f]
        pairs = [(tail(d1), tail(h)), (head(d1), head(h)),
                 (tail(d1), tail(n)), (head(d1), head(n)),
                 (tail(d2), tail(n2)), (head(d2), head(n2)),
                 (tail(d2), tail(n3)), (head(d2), head(n3))]
        for (a, b), r in zip(pairs, BRB):
            tp.bonds.append((a, b, r))
            tp.excl[a, b] = True; tp.excl[b, a] = True

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

# ---- branch placement (identical formula to engine KINETICS spawn) ----
def branch_place(host_cen, host_ax):
    """return daughter axis b and d1 center for a host monomer."""
    a = host_ax
    p = np.array([a[1], -a[0], 0.0])          # cross(a, ez)
    n = np.linalg.norm(p)
    if n < 0.1:
        p = np.array([-a[2], 0.0, a[0]])      # cross(a, ey)
        n = np.linalg.norm(p)
    p = p / n
    b = C70 * a + S70 * p
    cd = host_cen + BLAT * p + BAX * a
    return b, cd

# ---- cert config: hexamer on arc + branch trimer @build angle on monomer 3
#      + 10 spiral + 2 close-pair. Formula-identical to engine INIT_CERT ----
def cert_config():
    nm = 21
    X = np.zeros((2 * nm, 3))
    c = LBOX / 2.0
    th = 0.03
    pos = np.array([c, c, c])
    ax = np.array([1.0, 0.0, 0.0])
    hpos = pos.copy(); hax = ax.copy()
    for i in range(6):
        if i > 0:
            phi = th * i
            ax = np.array([np.cos(phi), np.sin(phi), 0.0])
            pos = pos + PITCH * np.array([np.cos(phi - th), np.sin(phi - th), 0.0])
        if i == 2:
            hpos = pos.copy(); hax = ax.copy()
        X[head(i)] = pos + 0.25 * ax
        X[tail(i)] = pos - 0.25 * ax
    # branch trimer (monomers 6,7,8 0-based; host = monomer 3 0-based idx 2)
    p = np.array([hax[1], -hax[0], 0.0])
    b = C70 * hax + S70 * p
    cd = hpos + BLAT * p + BAX * hax
    for k in range(3):
        m = 6 + k
        cen = cd + k * PITCH * b
        X[head(m)] = cen + 0.25 * b
        X[tail(m)] = cen - 0.25 * b
    for k in range(10):                          # free spiral (monomers 9..18)
        m = 9 + k
        phi = k * PHI_G
        pk = np.array([c + 4.5 * np.cos(phi), c + 4.5 * np.sin(phi), c - 1.5 + 3.0 * (k % 2)])
        ak = np.array([np.cos(phi + 1.0), np.sin(phi + 1.0), 0.5])
        ak = ak / np.linalg.norm(ak)
        X[head(m)] = pk + 0.25 * ak
        X[tail(m)] = pk - 0.25 * ak
    # close pair (monomers 19, 20)
    pA = np.array([c + 3.0, c - 3.0, c]); pB = pA + np.array([0.0, 0.55, 0.0])
    for m, pp in ((19, pA), (20, pB)):
        X[head(m)] = pp + [0.25, 0, 0]
        X[tail(m)] = pp - [0.25, 0, 0]
    anch = X[:2].copy()                          # un-jittered anchor targets
    for b_ in range(2 * nm):
        X[b_] = X[b_] + jitter(b_)
    tp = Topo(nm)
    for i in range(6):
        tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1; tp.mchain[i] = 0
    tp.prev[0] = -1; tp.next[5] = -1
    tp.clive[0] = True; tp.cpoint[0] = 0; tp.cbarb[0] = 5; tp.cmlen[0] = 6
    for i in range(6, 9):
        tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1; tp.mchain[i] = 1
    tp.prev[6] = -1; tp.next[8] = -1
    tp.clive[1] = True; tp.cpoint[1] = 6; tp.cbarb[1] = 8; tp.cmlen[1] = 3
    tp.chost[1] = 2; tp.hostof[2] = 1
    tp.cn[1] = 3; tp.cn2[1] = 4; tp.cn3[1] = 5
    tp.hprot[2] = 1; tp.hprot[3] = 1; tp.hprot[4] = 1; tp.hprot[5] = 1
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

def cert(outdir='/tmp/m4c'):
    X, tp, anch = cert_config()
    mask = np.ones(X.shape[0], dtype=bool)
    F, (ew, eb, ef, ea, ewl) = forces(X, tp, anch, mask, energy=True)
    with open(outdir + '/branch_cert_config.txt', 'w') as f:
        f.write('# MIRROR_DUMP nmono 21 mtot 9 nfil 2\n')
        for b in range(X.shape[0]):
            f.write('%.17e %.17e %.17e\n' % tuple(X[b]))
    with open(outdir + '/branch_cert_forces.txt', 'w') as f:
        for b in range(X.shape[0]):
            f.write('%.17e %.17e %.17e\n' % tuple(F[b]))
    print('CERT ewca %.17e ebond %.17e efil %.17e eanch %.17e ewall %.17e' % (ew, eb, ef, ea, ewl))
    print('wrote %s/branch_cert_{config,forces}.txt' % outdir)

# ---- dynamic init: seed filament (nseed0 monomers) + random gas ----
def dyn_init(nmono, rng, nseed0=NSEED):
    X = np.zeros((2 * nmono, 3))
    c = LBOX / 2.0
    for i in range(nseed0):
        cen = np.array([c + (i - 1.0) * PITCH, c, c])
        X[head(i)] = cen + [0.25, 0, 0]
        X[tail(i)] = cen - [0.25, 0, 0]
    tp = Topo(nmono)
    for i in range(nseed0):
        tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1; tp.mchain[i] = 0
    tp.prev[0] = -1; tp.next[nseed0 - 1] = -1
    tp.clive[0] = True; tp.cpoint[0] = 0; tp.cbarb[0] = nseed0 - 1; tp.cmlen[0] = nseed0
    placed = [X[b].copy() for i in range(nseed0) for b in (head(i), tail(i))]
    for m in range(nseed0, nmono):
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

# ---- multi-chain kinetics: per-chain bind/unbind (M4a rules) + branch ----
# Draw order per step (mirrors engine slot discipline): u_bind[f] f=0..7,
# u_off[f] f=0..7, u_fire, u_host. Draws consumed every step regardless.
def kinetics(X, tp, nmono, rng, counters, allow_on=True, allow_off=True,
             allow_branch=True, log=None, step=0):
    ax, cen = axes_of(X, nmono)
    u_on = rng.random(NFMAX); u_off = rng.random(NFMAX)
    u_fire = rng.random(); u_host = rng.random()
    dirty = False
    if allow_on:
        for f in range(NFMAX):
            if not tp.clive[f]:
                continue
            barb = tp.cbarb[f]
            hb = X[head(barb)]
            ab = ax[barb]
            for m in range(nmono):
                if tp.state[m]:
                    continue
                if np.linalg.norm(X[tail(m)] - hb) < RCAP and float(ax[m] @ ab) > QMIN:
                    if u_on[f] < min(1.0, KON * DT):
                        X[tail(m)] = hb + RCROSS * ab
                        X[head(m)] = X[tail(m)] + R0 * ab
                        tp.state[m] = True
                        tp.prev[m] = barb; tp.next[barb] = m
                        tp.next[m] = -1; tp.cbarb[f] = m; tp.cmlen[f] += 1
                        tp.mchain[m] = f
                        counters['nbind'] += 1
                        dirty = True
                    break
    if allow_off:
        for f in range(NFMAX):
            if tp.clive[f] and tp.cmlen[f] > NSEED and tp.hprot[tp.cbarb[f]] == 0:
                if u_off[f] < KOFF * DT:
                    m = tp.cbarb[f]; p = tp.prev[m]
                    tp.next[p] = -1; tp.cbarb[f] = p
                    tp.state[m] = False; tp.prev[m] = -1; tp.mchain[m] = 0
                    tp.cmlen[f] -= 1
                    ab = ax[p]
                    hb2 = X[head(p)]
                    X[tail(m)] = hb2 + (RCAP + 0.25) * ab
                    X[head(m)] = X[tail(m)] + R0 * ab
                    counters['nunbind'] += 1
                    dirty = True
    # ---- branch event ----
    nelig = 0
    helig = np.zeros(nmono, dtype=bool)
    for m in range(nmono):
        if not tp.state[m]:
            continue
        f = tp.mchain[m]
        if m == tp.cbarb[f] or tp.hprot[m] > 0:
            continue
        if tp.chost[f] > 0 and (m == tp.cpoint[f] or m == tp.next[tp.cpoint[f]]):
            continue
        n1 = tp.next[m]
        if n1 == -1 or tp.hprot[n1] > 0:
            continue
        n2 = tp.next[n1]
        if n2 == -1 or tp.hprot[n2] > 0:
            continue
        n3 = tp.next[n2]
        if n3 == -1 or tp.hprot[n3] > 0:
            continue
        helig[m] = True; nelig += 1
    fs = -1
    for f in range(NFMAX):
        if not tp.clive[f]:
            fs = f; break
    nfree = int(np.sum(~tp.state))
    if fs >= 0 and nfree >= 3:
        counters['elsum'] += nelig
        counters['elcnt'] += 1
        if nelig > 0 and u_fire < min(1.0, KBR * DT * nelig):
            tsel = int(u_host * nelig)
            elig = [m for m in range(nmono) if helig[m]]
            h = elig[min(tsel, nelig - 1)]
            free = [m for m in range(nmono) if not tp.state[m]]
            d1, d2, d3 = free[0], free[1], free[2]
            n1 = tp.next[h]; n2 = tp.next[n1]; n3 = tp.next[n2]
            b, cd = branch_place(cen[h], ax[h])
            for k, dm in enumerate((d1, d2, d3)):
                cc = cd + k * PITCH * b
                X[head(dm)] = cc + 0.25 * b
                X[tail(dm)] = cc - 0.25 * b
            tp.clive[fs] = True
            tp.cpoint[fs] = d1; tp.cbarb[fs] = d3; tp.cmlen[fs] = 3
            tp.chost[fs] = h
            tp.cn[fs] = n1; tp.cn2[fs] = n2; tp.cn3[fs] = n3
            tp.hostof[h] = fs + 1
            tp.hprot[h] = 1; tp.hprot[n1] = 1; tp.hprot[n2] = 1; tp.hprot[n3] = 1
            tp.state[d1] = True; tp.prev[d1] = -1; tp.next[d1] = d2; tp.mchain[d1] = fs
            tp.state[d2] = True; tp.prev[d2] = d1; tp.next[d2] = d3; tp.mchain[d2] = fs
            tp.state[d3] = True; tp.prev[d3] = d2; tp.next[d3] = -1; tp.mchain[d3] = fs
            counters['nbr'] += 1
            dirty = True
            if log is not None:
                ah = ax[h]
                angh = np.degrees(np.arccos(np.clip(float(b @ ah), -1.0, 1.0)))
                log.write('BRANCH step %d slot %d host %d d1 %d d2 %d d3 %d nelig %d angh %.2f\n'
                          % (step, fs + 1, h + 1, d1 + 1, d2 + 1, d3 + 1, nelig, angh))
    if dirty:
        rebuild_bonds(tp, 2 * nmono)
    return nelig

def branch_angles(X, tp, ax, cen):
    """per live branch: (angle vs host axis, angle vs h->n3 tangent), degrees"""
    out = []
    for f in range(NFMAX):
        if tp.clive[f] and tp.chost[f] > 0:
            d1 = tp.cpoint[f]; d2 = tp.next[d1]; h = tp.chost[f]
            base = cen[d2] - cen[d1]
            nb = np.linalg.norm(base)
            if nb < 1e-12:
                continue
            base = base / nb
            ah = ax[h]
            a1 = np.degrees(np.arccos(np.clip(float(base @ ah), -1.0, 1.0)))
            tg = cen[tp.cn3[f]] - cen[h]
            tg = tg / max(np.linalg.norm(tg), 1e-12)
            a2 = np.degrees(np.arccos(np.clip(float(base @ tg), -1.0, 1.0)))
            out.append((f, a1, a2))
    return out

def integrate_run(X, V, tp, anch, nmono, nsteps, rng, label='run', ndiag=500,
                  allow_on=True, allow_off=True, allow_branch=True,
                  angfile=None, logfile=None):
    mask = np.ones(2 * nmono, dtype=bool)
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    counters = dict(nbind=0, nunbind=0, nbr=0, elsum=0.0, elcnt=0)
    lsum = 0.0; lcnt = 0
    ang1 = []; ang2 = []
    log = open(logfile, 'w') if logfile else None
    af = open(angfile, 'w') if angfile else None
    for step in range(1, nsteps + 1):
        F = forces(X, tp, anch, mask)
        V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
        X = X + V * DT
        kinetics(X, tp, nmono, rng, counters, allow_on, allow_off, allow_branch,
                 log=log, step=step)
        if step % ndiag == 0:
            mtot = int(tp.cmlen[tp.clive].sum())
            nfil = int(tp.clive.sum())
            if step > nsteps // 2:
                lsum += mtot; lcnt += 1
                ax, cen = axes_of(X, nmono)
                for f, a1, a2 in branch_angles(X, tp, ax, cen):
                    ang1.append(a1); ang2.append(a2)
                    if af:
                        af.write('%d %d %.4f %.4f\n' % (step, f + 1, a1, a2))
            lens = ' '.join(str(int(tp.cmlen[f])) for f in range(NFMAX))
            kt = float(np.sum(V * V)) / (3.0 * 2 * nmono)
            print('%s step %d kt %.4f mtot %d nfree %d nfil %d nbr %d binds %d unbinds %d lens %s'
                  % (label, step, kt, mtot, nmono - mtot, nfil, counters['nbr'],
                     counters['nbind'], counters['nunbind'], lens), flush=True)
    lmean = lsum / max(lcnt, 1)
    a1m = float(np.mean(ang1)) if ang1 else -1.0
    a2m = float(np.mean(ang2)) if ang2 else -1.0
    print('%s FINAL mtmean %.4f nfil %d nbr %d angmean %.4f (n=%d) ang2mean %.4f binds %d unbinds %d elsum %.1f'
          % (label, lmean, int(tp.clive.sum()), counters['nbr'], a1m, len(ang1), a2m,
             counters['nbind'], counters['nunbind'], counters['elsum']), flush=True)
    if log: log.close()
    if af: af.close()
    return lmean, counters

def calibrate(nleg1=10, do23=True):
    global KON, KOFF, KBR
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))

    print('== leg 1: KBR branch-rate calibration (fixed 30-mer, no bind/unbind) ==')
    sav = (KON, KOFF, KBR)
    KON = 0.0; KOFF = 0.0; KBR = 0.20
    ev_tot = 0; el_tot = 0.0
    nseeds = nleg1
    for sd in range(nseeds):
        rng = np.random.default_rng(SEED + 1000 * sd)
        nmono = 30 + 24
        X, tp, anch = dyn_init(nmono, rng, nseed0=30)
        V = np.zeros_like(X)
        counters = dict(nbind=0, nunbind=0, nbr=0, elsum=0.0, elcnt=0)
        for step in range(1, 40001):
            F = forces(X, tp, anch, np.ones(2 * nmono, dtype=bool))
            V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
            X = X + V * DT
            kinetics(X, tp, nmono, rng, counters, False, False, True)
        ev_tot += counters['nbr']; el_tot += counters['elsum']
        print('  seed %d: branches %d elsum %.1f' % (sd, counters['nbr'], counters['elsum']), flush=True)
    kbr_eff = ev_tot / max(el_tot, 1.0)
    print('KBR_eff = %.6e /monomer/step (%d events, elsum %.0f)  nominal %.6e  ratio %.3f'
          % (kbr_eff, ev_tot, el_tot, KBR * DT, kbr_eff / (KBR * DT)))
    KON, KOFF, KBR = sav

    if not do23:
        return
    print('== leg 2: k_on with multiple live chains (mother trimer + branch trimer) ==')
    for npool in (20, 40):
        rng = np.random.default_rng(SEED + npool)
        nmono = 6 + npool
        X, tp, anch = dyn_init(nmono, rng, nseed0=3)
        # pre-spawn branch trimer on monomer 2 (0-based 1): needs n1..n3 -> only 3-mer, no room
        # instead branch on a fresh 6-mer: rebuild as 6-mer mother
        tp = Topo(nmono)
        for i in range(6):
            tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1; tp.mchain[i] = 0
            cen = np.array([LBOX / 2.0 + (i - 1.0) * PITCH, LBOX / 2.0, LBOX / 2.0])
            X[head(i)] = cen + [0.25, 0, 0]; X[tail(i)] = cen - [0.25, 0, 0]
        tp.prev[0] = -1; tp.next[5] = -1
        tp.clive[0] = True; tp.cpoint[0] = 0; tp.cbarb[0] = 5; tp.cmlen[0] = 6
        # branch trimer from monomers 6,7,8 at host 2 (0-based)
        ax, cen = axes_of(X, nmono)
        b, cd = branch_place(cen[2], ax[2])
        for k, dm in enumerate((6, 7, 8)):
            cc = cd + k * PITCH * b
            X[head(dm)] = cc + 0.25 * b; X[tail(dm)] = cc - 0.25 * b
            tp.state[dm] = True; tp.mchain[dm] = 1
        tp.prev[6] = -1; tp.next[6] = 7; tp.prev[7] = 6; tp.next[7] = 8
        tp.prev[8] = 7; tp.next[8] = -1
        tp.clive[1] = True; tp.cpoint[1] = 6; tp.cbarb[1] = 8; tp.cmlen[1] = 3
        tp.chost[1] = 2; tp.hostof[2] = 1
        tp.cn[1] = 3; tp.cn2[1] = 4; tp.cn3[1] = 5
        tp.hprot[2:6] = 1
        rebuild_bonds(tp, 2 * nmono)
        V = np.zeros_like(X)
        nsteps = 40000
        counters = dict(nbind=0, nunbind=0, nbr=0, elsum=0.0, elcnt=0)
        for step in range(1, nsteps + 1):
            F = forces(X, tp, anch, np.ones(2 * nmono, dtype=bool))
            V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
            X = X + V * DT
            kinetics(X, tp, nmono, rng, counters, True, False, False)
        c = npool / LBOX ** 3
        rate = counters['nbind'] / nsteps
        print('  pool %3d c = %.6f  binds %4d  rate %.6e /step  (2 live chains: per-chain %.6e)'
              % (npool, c, counters['nbind'], rate, rate / 2.0), flush=True)

    print('== leg 3: k_off multi-chain (mother 8-mer + branch trimer, bind off) ==')
    rng = np.random.default_rng(SEED + 77)
    nmono = 11 + 9
    X = np.zeros((2 * nmono, 3))
    c = LBOX / 2.0
    tp = Topo(nmono)
    for i in range(8):
        cen = np.array([c + (i - 2.0) * PITCH, c, c])
        X[head(i)] = cen + [0.25, 0, 0]; X[tail(i)] = cen - [0.25, 0, 0]
        tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1; tp.mchain[i] = 0
    tp.prev[0] = -1; tp.next[7] = -1
    tp.clive[0] = True; tp.cpoint[0] = 0; tp.cbarb[0] = 7; tp.cmlen[0] = 8
    axm, cenm = axes_of(X, nmono)
    b, cd = branch_place(cenm[2], axm[2])
    for k, dm in enumerate((8, 9, 10)):
        cc = cd + k * PITCH * b
        X[head(dm)] = cc + 0.25 * b; X[tail(dm)] = cc - 0.25 * b
        tp.state[dm] = True; tp.mchain[dm] = 1
    tp.prev[8] = -1; tp.next[8] = 9; tp.prev[9] = 8; tp.next[9] = 10
    tp.prev[10] = 9; tp.next[10] = -1
    tp.clive[1] = True; tp.cpoint[1] = 8; tp.cbarb[1] = 10; tp.cmlen[1] = 3
    tp.chost[1] = 2; tp.hostof[2] = 1
    tp.cn[1] = 3; tp.cn2[1] = 4; tp.cn3[1] = 5
    tp.hprot[2:6] = 1
    # remaining monomers 11..19 as gas far away
    for m in range(11, nmono):
        X[head(m)] = [2.0, 2.0 + 0.7 * (m - 11), 2.0]
        X[tail(m)] = [2.0, 2.0 + 0.7 * (m - 11), 1.5]
    rebuild_bonds(tp, 2 * nmono)
    anch = X[:2].copy(); V = np.zeros_like(X)
    nsteps = 30000
    counters = dict(nbind=0, nunbind=0, nbr=0, elsum=0.0, elcnt=0)
    nelig_steps = 0
    for step in range(1, nsteps + 1):
        F = forces(X, tp, anch, np.ones(2 * nmono, dtype=bool))
        V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
        X = X + V * DT
        # eligible chain-steps BEFORE kinetics
        for f in range(NFMAX):
            if tp.clive[f] and tp.cmlen[f] > NSEED and tp.hprot[tp.cbarb[f]] == 0:
                nelig_steps += 1
        kinetics(X, tp, nmono, rng, counters, False, True, False)
    koff = counters['nunbind'] / max(nelig_steps, 1)
    print('k_off_eff = %.6e /chain/step  (%d unbinds in %d eligible chain-steps, nominal %.3e, ratio %.3f)'
          % (koff, counters['nunbind'], nelig_steps, KOFF * DT, koff / (KOFF * DT)))

def run(nsteps=150000, seed=SEED, out='/tmp/m4c'):
    rng = np.random.default_rng(seed)
    X, tp, anch = dyn_init(NMONO, rng)
    V = np.zeros_like(X)
    lmean, counters = integrate_run(X, V, tp, anch, NMONO, nsteps, rng,
                                    label='run%d' % seed,
                                    angfile='%s/ang_%d.txt' % (out, seed),
                                    logfile='%s/branches_%d.txt' % (out, seed))
    return lmean, counters

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] == '--fd':
        fd_check()
    elif args[0] == '--cert':
        cert()
    elif args[0] == '--cal':
        calibrate()
    elif args[0] == '--cal23':
        calibrate(nleg1=0) if False else None
        # legs 2+3 only
        import types
        calibrate.__globals__['KBR'] = KBR
        # call with nleg1=0 would run leg1 loop 0 times then legs 2,3:
        calibrate(nleg1=0, do23=True)
    elif args[0] == '--kbr1':
        sd = int(args[1]); nsteps = int(args[2]) if len(args) > 2 else 4000
        rng = np.random.default_rng(SEED + 1000 * sd)
        sav = (KON, KOFF, KBR); KON = 0.0; KOFF = 0.0; KBR = 0.20
        na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
        X, tp, anch = dyn_init(54, rng, nseed0=30)
        V = np.zeros_like(X)
        counters = dict(nbind=0, nunbind=0, nbr=0, elsum=0.0, elcnt=0)
        for step in range(1, nsteps + 1):
            F = forces(X, tp, anch, np.ones(108, dtype=bool))
            V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
            X = X + V * DT
            kinetics(X, tp, 54, rng, counters, False, False, True)
        print('KBR1 seed %d branches %d elsum %.1f ratio %.3f'
              % (sd, counters['nbr'], counters['elsum'],
                 counters['nbr'] / max(counters['elsum'], 1.0) / 1e-3), flush=True)
        KON, KOFF, KBR = sav
    elif args[0] == '--run':
        nsteps = int(args[1]) if len(args) > 1 else 150000
        seed = int(args[2]) if len(args) > 2 else SEED
        run(nsteps, seed)
