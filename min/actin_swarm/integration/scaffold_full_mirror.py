#!/usr/bin/env python3
# scaffold_full_mirror.py - M4i integration mirror: full-scaffold oracle.
# Merge of the four certified mirrors onto the M4C multi-chain base:
#   M4C structural base (multi-chain, branch springs, 62.5-deg build angle)
#   M4B pointed kinetics on seed chain 0 (anchor transfer, release 2.5)
#   M4H hydrolysis (NUC state, KHYD, state-dependent KOFFB/KOFFP)
#   M4D transient crosslinks (KLINK/L0 fixed rest, birth/death, LOOPMIN)
# Modes: --fd, --cert, --cal {hyd,branch,link,all}, --run N SEED, --full N SEED.
# Physics matches scaffold_full.ergo exactly; RNG streams independent.
import numpy as np, sys

# ---- parameters (must match scaffold_full.ergo) ----
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
KON    = 500.0          # barbed bind (saturated window rule)
KONP   = 1.0            # pointed bind (chain 0), P = KONP*DT chemistry-limited
KOFFB_T = 0.045         # barbed unbind, ATP terminal
KOFFB_A = 0.18          # barbed unbind, ADP terminal
KOFFP_T = 0.05          # pointed unbind, ATP terminal
KOFFP_A = 0.10          # pointed unbind, ADP terminal
KHYD   = 0.03           # hydrolysis P = KHYD*DT per bound ATP monomer
KBR    = 0.02           # branch prob/monomer/step
C70    = 0.46174861323503386   # cos(62.5 deg) build angle
S70    = 0.88701083317822171   # sin(62.5 deg)
BLAT   = 0.9
BAX    = -0.2
BRB    = [0.68139666108583519, 1.1705816660755957, 0.95017156014555315,
          1.4600468667073012, 1.5627249250101813, 2.0777203167506473,
          1.9970415052495438, 2.4871546250964522]
# crosslinks (M4D exact)
KLINK  = 20.0
L0     = 0.7
RLINK  = 1.0
KLINKF = 0.3
KLINKB = 3.0
MAXL   = 64
MAXCB  = 1200
LOOPMIN = 6
KSEED  = 5.0
SEED   = 77031
NMONO  = 90
NFMAX  = 8
NSEED  = 3
PHI_G  = 2.39996322972865332
CERTDZ = 0.85
WCUT   = C216 * SIG     # 0.5612
DEG    = 57.29577951308232
# feature flags (cal legs override)
DOPOINTED = 1
DOHYD     = 1
DOBRANCH  = 1
DOLINK    = 1

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
        self.nuc    = np.ones(cap, dtype=bool)   # True=ATP, False=ADP
        self.posi   = np.zeros(cap, dtype=int)   # contour index (0=free)
        self.cpoint = np.zeros(NFMAX, dtype=int)
        self.cbarb  = np.zeros(NFMAX, dtype=int)
        self.cmlen  = np.zeros(NFMAX, dtype=int)
        self.clive  = np.zeros(NFMAX, dtype=bool)
        self.chost  = np.zeros(NFMAX, dtype=int)
        self.cn     = np.zeros(NFMAX, dtype=int)
        self.cn2    = np.zeros(NFMAX, dtype=int)
        self.cn3    = np.zeros(NFMAX, dtype=int)
        self.anchm  = 0                          # anchored monomer, chain 0
        self.lact   = np.zeros(MAXL, dtype=bool)
        self.li     = np.zeros(MAXL, dtype=int)
        self.lj     = np.zeros(MAXL, dtype=int)
        self.lborn  = np.zeros(MAXL, dtype=int)
        self.lmask  = set()
        self.nlink  = 0
        self.bonds = []          # (a, b, rest): ladders then branch springs
        self.excl = None

def strip_links(tp, m, counters):
    hb, tb = head(m), tail(m)
    for l in range(MAXL):
        if tp.lact[l] and (tp.li[l] in (hb, tb) or tp.lj[l] in (hb, tb)):
            tp.lact[l] = False
            tp.lmask.discard((min(tp.li[l], tp.lj[l]), max(tp.li[l], tp.lj[l])))
            tp.nlink -= 1
            counters['lstrips'] += 1

def rebuild_bonds(tp, nb):
    tp.bonds = []
    tp.excl = np.zeros((nb, nb), dtype=bool)
    tp.posi[:] = 0
    for m in range(nb // 2):
        tp.excl[head(m), tail(m)] = True
        tp.excl[tail(m), head(m)] = True
    # chain ladders, chains ascending, pointed->barbed (engine order)
    for f in range(NFMAX):
        if not tp.clive[f]:
            continue
        m = tp.cpoint[f]
        tp.posi[m] = 1
        t = 1
        for _ in range(nb // 2):
            q = tp.next[m]
            if q == -1:
                break
            t += 1
            tp.posi[q] = t
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

def forces(X, tp, anch, amask, mask_active, energy=False):
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
    # crosslinks (M4D): linked pairs are NOT WCA-excluded; L0 > WCUT
    elink = 0.0
    for l in range(MAXL):
        if not tp.lact[l]:
            continue
        a, b = int(tp.li[l]), int(tp.lj[l])
        dr = X[a] - X[b]
        dd = max(float(np.linalg.norm(dr)), 1e-16)
        f = 2.0 * KLINK * (dd - L0) / dd
        F[a] -= f * dr; F[b] += f * dr
        if energy: elink += KLINK * (dd - L0) ** 2
    eanch = 0.0
    for b in np.where(amask)[0]:
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
        return F, (ewca, ebond, efil, elink, eanch, ewall)
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

# ---- composed cert config: mother hexamer on arc + branch trimer on
#      monomer 3 + straight tetramer chain B at z-offset CERTDZ carrying 3
#      static links + NUC pattern + 10 spiral + close pair. Formula-
#      identical to engine INIT_CERT. 0-based monomers: 0..5 mother,
#      6..8 branch (host=2), 9..12 chain B, 13..22 spiral, 23..24 close.
def cert_config():
    nm = 25
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
    # branch trimer (monomers 6,7,8; host = monomer 2)
    p = np.array([hax[1], -hax[0], 0.0])
    b = C70 * hax + S70 * p
    cd = hpos + BLAT * p + BAX * hax
    for k in range(3):
        m = 6 + k
        cen = cd + k * PITCH * b
        X[head(m)] = cen + 0.25 * b
        X[tail(m)] = cen - 0.25 * b
    # chain B: straight tetramer along +x at z = c - CERTDZ (monomers 9..12)
    for k in range(4):
        m = 9 + k
        cen = np.array([c + k * PITCH, c, c - CERTDZ])
        X[head(m)] = cen + [0.25, 0, 0]
        X[tail(m)] = cen - [0.25, 0, 0]
    for k in range(10):                          # free spiral (monomers 13..22)
        m = 13 + k
        phi = k * PHI_G
        pk = np.array([c + 4.5 * np.cos(phi), c + 4.5 * np.sin(phi), c - 1.5 + 3.0 * (k % 2)])
        ak = np.array([np.cos(phi + 1.0), np.sin(phi + 1.0), 0.5])
        ak = ak / np.linalg.norm(ak)
        X[head(m)] = pk + 0.25 * ak
        X[tail(m)] = pk - 0.25 * ak
    # close pair (monomers 23, 24)
    pA = np.array([c + 3.0, c - 3.0, c]); pB = pA + np.array([0.0, 0.55, 0.0])
    for m, pp in ((23, pA), (24, pB)):
        X[head(m)] = pp + [0.25, 0, 0]
        X[tail(m)] = pp - [0.25, 0, 0]
    anch = X[:2].copy()                          # un-jittered anchor targets
    amask = np.zeros(2 * nm, dtype=bool)
    for b_ in range(2 * nm):
        X[b_] = X[b_] + jitter(b_)
    amask[0] = True; amask[1] = True
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
    # chain B topology (chain index 2)
    for i in range(9, 13):
        tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1; tp.mchain[i] = 2
    tp.prev[9] = -1; tp.next[12] = -1
    tp.clive[2] = True; tp.cpoint[2] = 9; tp.cbarb[2] = 12; tp.cmlen[2] = 4
    # NUC pattern: ADP at monomers 1, 3, 10 (0-based) == engine 2, 4, 11
    tp.nuc[1] = False; tp.nuc[3] = False; tp.nuc[10] = False
    # 3 static crosslinks mother<->chain B (engine beads 1-19, 3-21, 6-24)
    for l, (a, bb) in enumerate([(0, 18), (2, 20), (5, 23)]):
        tp.lact[l] = True; tp.li[l] = a; tp.lj[l] = bb
        tp.lmask.add((min(a, bb), max(a, bb)))
    tp.nlink = 3
    tp.anchm = 0
    rebuild_bonds(tp, 2 * nm)
    return X, tp, anch, amask

def fd_check():
    X, tp, anch, amask = cert_config()
    rng = np.random.default_rng(12345)
    X = X + rng.normal(scale=0.03, size=X.shape)
    mask = np.ones(X.shape[0], dtype=bool)
    F, _ = forces(X, tp, anch, amask, mask, energy=True)
    h = 1e-6
    worst = 0.0; worst_abs = 0.0
    for b in range(X.shape[0]):
        for ax in range(3):
            Xp = X.copy(); Xp[b, ax] += h
            Xm = X.copy(); Xm[b, ax] -= h
            _, ep = forces(Xp, tp, anch, amask, mask, energy=True)
            _, em = forces(Xm, tp, anch, amask, mask, energy=True)
            fd = -(sum(ep) - sum(em)) / (2 * h)
            an = F[b, ax]
            rel = abs(fd - an) / max(abs(an), 1.0)
            worst = max(worst, rel); worst_abs = max(worst_abs, abs(fd - an))
    print('FD check: max_rel_vs_1 %.3e  max_abs %.3e' % (worst, worst_abs))
    return worst

def cert(outdir='/tmp/m4i'):
    X, tp, anch, amask = cert_config()
    mask = np.ones(X.shape[0], dtype=bool)
    F, (ew, eb, ef, el, ea, ewl) = forces(X, tp, anch, amask, mask, energy=True)
    with open(outdir + '/scaffold_cert_config.txt', 'w') as f:
        f.write('# MIRROR_DUMP nmono 25 mtot 13 nfil 3 nlink 3\n')
        for b in range(X.shape[0]):
            f.write('%.17e %.17e %.17e\n' % tuple(X[b]))
    with open(outdir + '/scaffold_cert_forces.txt', 'w') as f:
        for b in range(X.shape[0]):
            f.write('%.17e %.17e %.17e\n' % tuple(F[b]))
    with open(outdir + '/scaffold_cert_nuc.txt', 'w') as f:
        for m in range(25):
            f.write('NUC %d %d\n' % (m + 1, 1 if tp.nuc[m] else 0))
    print('CERT ewca %.17e ebond %.17e efil %.17e elink %.17e eanch %.17e ewall %.17e'
          % (ew, eb, ef, el, ea, ewl))
    print('wrote %s/scaffold_cert_{config,forces,nuc}.txt' % outdir)

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
    amask = np.zeros(2 * nmono, dtype=bool)
    amask[0] = True; amask[1] = True
    tp.anchm = 0
    return X, tp, anch, amask

# ---- link candidate pass (M4D): full-matrix, engine-statistical match ----
def candidates(X, tp):
    nb = X.shape[0]
    up = np.triu_indices(nb, 1)
    D = X[:, None, :] - X[None, :, :]
    dd = np.sqrt(np.maximum(np.einsum('ijk,ijk->ij', D, D), 1e-32))[up]
    iu, ju = up
    mi, mj = iu // 2, ju // 2
    st = tp.state
    ok = (~tp.excl[up]) & (dd <= RLINK) & st[mi] & st[mj]
    same = tp.mchain[mi] == tp.mchain[mj]
    ok &= (~same) | (np.abs(tp.posi[mi] - tp.posi[mj]) >= LOOPMIN)
    idx = np.where(ok)[0]
    out = []
    for k in idx:
        a, b = int(iu[k]), int(ju[k])
        if (a, b) not in tp.lmask:
            out.append((a, b))
    return out

def link_bd(X, tp, rng, counters, step):
    if not DOLINK:
        return
    cand = candidates(X, tp)
    counters['celsum'] += len(cand)
    # births: one draw per candidate, capped at MAXCB (engine slot discipline)
    us = rng.random(min(len(cand), MAXCB))
    for k in range(len(us)):
        if us[k] < KLINKF * DT and tp.nlink < MAXL:
            free = np.where(~tp.lact)[0]
            if len(free) == 0:
                break
            l = int(free[0])
            a, b = cand[k]
            tp.lact[l] = True; tp.li[l] = a; tp.lj[l] = b; tp.lborn[l] = step
            tp.lmask.add((min(a, b), max(a, b)))
            tp.nlink += 1
            counters['lbirths'] += 1
    if len(cand) > MAXCB:
        counters['ncskip'] += len(cand) - MAXCB
    # deaths: one draw per active link, slot order
    counters['lsteps'] += tp.nlink
    for l in range(MAXL):
        if not tp.lact[l]:
            continue
        if rng.random() < KLINKB * DT:
            tp.lact[l] = False
            tp.lmask.discard((min(tp.li[l], tp.lj[l]), max(tp.li[l], tp.lj[l])))
            tp.nlink -= 1
            counters['ldeaths'] += 1
            counters['ltsum'] += step - tp.lborn[l]
            counters['ltcnt'] += 1

# ---- merged kinetics: hydrolysis -> tallies -> barbed binds -> barbed
# unbinds (NUC-dependent, strip links) -> pointed chain 0 (bind, unbind,
# anchor transfer, far release) -> branch event. Mirrors engine order.
def kinetics(X, tp, nmono, rng, counters, allow_on=True, allow_off=True,
             allow_pointed=True, allow_branch=True, allow_hyd=True,
             log=None, step=0, tally=False):
    ax, cen = axes_of(X, nmono)
    dirty = False
    # hydrolysis (M4H): bound ATP monomer flips at P = KHYD*DT
    if DOHYD and allow_hyd:
        for m in range(nmono):
            if tp.state[m] and tp.nuc[m]:
                counters['hydsum'] += 1
                if rng.random() < KHYD * DT:
                    tp.nuc[m] = False
                    counters['nhyd'] += 1
    # 2nd-half-style tallies when requested (cal / run counters)
    if tally:
        for f in range(NFMAX):
            if tp.clive[f] and tp.cmlen[f] > NSEED and tp.hprot[tp.cbarb[f]] == 0:
                counters['elt2'] += 1
                if tp.nuc[tp.cbarb[f]]:
                    counters['eat2'] += 1
        if DOPOINTED and tp.clive[0] and tp.cmlen[0] > NSEED and tp.hprot[tp.cpoint[0]] == 0:
            counters['elsp2'] += 1
    u_on = rng.random(NFMAX); u_off = rng.random(NFMAX)
    u_onp = rng.random(); u_offp = rng.random()
    u_fire = rng.random(); u_host = rng.random()
    # ---- barbed binds: one attempt per live chain ----
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
                        tp.nuc[m] = True
                        tp.prev[m] = barb; tp.next[barb] = m
                        tp.next[m] = -1; tp.cbarb[f] = m; tp.cmlen[f] += 1
                        tp.mchain[m] = f
                        counters['nbind'] += 1
                        dirty = True
                    break
    # ---- barbed unbinds: NUC-dependent rate (M4H), strip links (M4D) ----
    if allow_off:
        for f in range(NFMAX):
            if tp.clive[f] and tp.cmlen[f] > NSEED and tp.hprot[tp.cbarb[f]] == 0:
                rk = KOFFB_T if tp.nuc[tp.cbarb[f]] else KOFFB_A
                if u_off[f] < rk * DT:
                    m = tp.cbarb[f]; p = tp.prev[m]
                    tp.next[p] = -1; tp.cbarb[f] = p
                    tp.state[m] = False; tp.prev[m] = -1; tp.mchain[m] = 0
                    tp.cmlen[f] -= 1
                    counters['nunbind'] += 1
                    if tally:
                        counters['nub2'] += 1
                        if tp.nuc[m]:
                            counters['uat2'] += 1
                        else:
                            counters['uad2'] += 1
                    tp.nuc[m] = True
                    if DOLINK:
                        strip_links(tp, m, counters)
                    ab = ax[p]
                    hb2 = X[head(p)]
                    X[tail(m)] = hb2 + (RCAP + 0.25) * ab
                    X[head(m)] = X[tail(m)] + R0 * ab
                    dirty = True
    # ---- pointed end, seed chain 0 only (M4B) ----
    if DOPOINTED and allow_pointed and tp.clive[0]:
        pnt = tp.cpoint[0]
        tpnt = X[tail(pnt)]
        for m in range(nmono):
            if tp.state[m]:
                continue
            d = np.linalg.norm(X[head(m)] - tpnt)
            if d < RCAP and float(ax[m] @ ax[pnt]) > QMIN:
                if allow_on and u_onp < min(1.0, KONP * DT):
                    ab = ax[pnt]
                    X[head(m)] = tpnt - RCROSS * ab
                    X[tail(m)] = X[head(m)] - R0 * ab
                    tp.state[m] = True
                    tp.nuc[m] = True
                    tp.next[m] = pnt; tp.prev[pnt] = m
                    tp.prev[m] = -1
                    tp.cpoint[0] = m
                    tp.cmlen[0] += 1
                    tp.mchain[m] = 0
                    counters['nbindp'] += 1
                    dirty = True
                break
        # pointed unbind gated by allow_pointed only (engine: independent of barbed gate)
        if tp.cmlen[0] > NSEED and tp.hprot[tp.cpoint[0]] == 0:
            rk = KOFFP_T if tp.nuc[tp.cpoint[0]] else KOFFP_A
            if u_offp < rk * DT:
                m = tp.cpoint[0]
                q = tp.next[m]
                tp.prev[q] = -1
                tp.cpoint[0] = q
                tp.state[m] = False; tp.next[m] = -1; tp.mchain[m] = 0
                tp.cmlen[0] -= 1
                counters['nunbindp'] += 1
                if tally:
                    counters['nup2'] += 1
                tp.nuc[m] = True
                # anchor transfer: NPF re-grips the new pointed monomer
                if m == tp.anchm:
                    amask = counters['_amask']
                    anch = counters['_anch']
                    amask[head(m)] = False; amask[tail(m)] = False
                    tp.anchm = q
                    counters['ratch'] += 1
                    amask[head(q)] = True; amask[tail(q)] = True
                    anch[head(q)] = X[head(q)].copy()
                    anch[tail(q)] = X[tail(q)].copy()
                if DOLINK:
                    strip_links(tp, m, counters)
                # far release at RCAP+1.1 = 2.5 (M4B trap fix)
                ab = ax[q]
                X[head(m)] = X[tail(q)] - (RCAP + 1.1) * ab
                X[tail(m)] = X[head(m)] - R0 * ab
                dirty = True
    # ---- branch event (M4C exact) ----
    nelig = 0
    helig = np.zeros(nmono, dtype=bool)
    if DOBRANCH and allow_branch:
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

def new_counters():
    return dict(nbind=0, nunbind=0, nbindp=0, nunbindp=0, ratch=0, nbr=0,
                nhyd=0, hydsum=0, elsum=0.0, elcnt=0,
                elt2=0, eat2=0, uat2=0, uad2=0, nub2=0, elsp2=0, nup2=0,
                lbirths=0, ldeaths=0, lstrips=0, ltsum=0, ltcnt=0,
                celsum=0, lsteps=0, ncskip=0)

def run(nsteps=300000, seed=SEED, out='/tmp/m4i', label=None, ndiag=500):
    rng = np.random.default_rng(seed)
    X, tp, anch, amask = dyn_init(NMONO, rng)
    V = np.zeros_like(X)
    mask = np.ones(2 * NMONO, dtype=bool)
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    counters = new_counters()
    counters['_amask'] = amask; counters['_anch'] = anch
    label = label or ('run%d' % seed)
    log = open('%s/branches_%s.txt' % (out, label), 'w')
    lsum = 0.0; lcnt = 0
    natpsum = 0.0; shnl = 0.0; shnli = 0.0; shnc = 0.0; shcnt = 0
    capsum = np.zeros(NMONO); capcnt = np.zeros(NMONO)
    ang1 = []; ang2 = []
    for step in range(1, nsteps + 1):
        F = forces(X, tp, anch, amask, mask)
        V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
        X = X + V * DT
        ncand0 = len(candidates(X, tp)) if DOLINK else 0
        tally = step > nsteps // 2
        kinetics(X, tp, NMONO, rng, counters, tally=tally, log=log, step=step)
        link_bd(X, tp, rng, counters, step)
        if step % ndiag == 0:
            mtot = int(tp.cmlen[tp.clive].sum())
            nfil = int(tp.clive.sum())
            natp = int(np.sum(tp.state & tp.nuc))
            nli = 0
            for l in range(MAXL):
                if tp.lact[l]:
                    a, b = tp.li[l] // 2, tp.lj[l] // 2
                    if tp.mchain[a] != tp.mchain[b]:
                        nli += 1
            kt = float(np.sum(V * V)) / (3.0 * 2 * NMONO)
            if tally:
                lsum += mtot; lcnt += 1
                natpsum += natp; shnl += tp.nlink; shnli += nli
                shnc += ncand0; shcnt += 1
                if tp.clive[0]:
                    m = tp.cbarb[0]; depth = 0
                    while m != -1 and depth < NMONO:
                        capcnt[depth] += 1
                        capsum[depth] += 1.0 if tp.nuc[m] else 0.0
                        m = tp.prev[m]; depth += 1
                ax, cen = axes_of(X, NMONO)
                for f, a1, a2 in branch_angles(X, tp, ax, cen):
                    ang1.append(a1); ang2.append(a2)
            lens = ' '.join(str(int(tp.cmlen[f])) for f in range(NFMAX))
            Fd, (ew, eb, ef, el, ea, ewl) = forces(X, tp, anch, amask, mask, energy=True)
            fmax = float(np.max(np.sqrt(np.sum(Fd ** 2, axis=1))))
            print('%s step %d kt %.4f ewca %.6e efil %.6e elink %.6e eanch %.6e '
                  'mtot %d nfree %d nfil %d nbr %d binds %d unbinds %d bindp %d unbindp %d '
                  'ratch %d nhyd %d natp %d nlink %d nli %d ncand %d lb %d ld %d ls %d '
                  'fmax %.4e lens %s'
                  % (label, step, kt, ew, ef, el, ea, mtot, NMONO - mtot, nfil,
                     counters['nbr'], counters['nbind'], counters['nunbind'],
                     counters['nbindp'], counters['nunbindp'], counters['ratch'],
                     counters['nhyd'], natp, tp.nlink, nli, ncand0,
                     counters['lbirths'], counters['ldeaths'], counters['lstrips'],
                     fmax, lens), flush=True)
    lmean = lsum / max(lcnt, 1)
    a1m = float(np.mean(ang1)) if ang1 else -1.0
    a2m = float(np.mean(ang2)) if ang2 else -1.0
    print('%s FINAL mtmean %.4f nfil %d nbr %d angmean %.4f angn %d ang2mean %.4f '
          'binds %d unbinds %d bindp %d unbindp %d ratch %d nhyd %d'
          % (label, lmean, int(tp.clive.sum()), counters['nbr'], a1m, len(ang1), a2m,
             counters['nbind'], counters['nunbind'], counters['nbindp'],
             counters['nunbindp'], counters['ratch'], counters['nhyd']), flush=True)
    print('%s FINLENS %s' % (label, ' '.join(str(int(tp.cmlen[f])) for f in range(NFMAX))))
    print('%s FINELSUM %.4f elcnt %d' % (label, counters['elsum'], counters['elcnt']))
    print('%s FINKOFF elt2 %d eat2 %d uat2 %d uad2 %d nub2 %d elsp2 %d nup2 %d hydsum %d'
          % (label, counters['elt2'], counters['eat2'], counters['uat2'], counters['uad2'],
             counters['nub2'], counters['elsp2'], counters['nup2'], counters['hydsum']))
    lifem = counters['ltsum'] / max(counters['ltcnt'], 1)
    print('%s FINLINK lbirths %d ldeaths %d lstrips %d nlmean %.4f nlimean %.4f '
          'ncmean %.4f celsum %d lsteps %d lifemean %.4f ncskip %d'
          % (label, counters['lbirths'], counters['ldeaths'], counters['lstrips'],
             shnl / max(shcnt, 1), shnli / max(shcnt, 1), shnc / max(shcnt, 1),
             counters['celsum'], counters['lsteps'], lifem, counters['ncskip']))
    print('%s FINNATP natpmean %.4f' % (label, natpsum / max(shcnt, 1)))
    for d in range(NMONO):
        if capcnt[d] > 0:
            print('%s CAP %d %.6f %.0f' % (label, d, capsum[d] / capcnt[d], capcnt[d]))
    log.close()
    return lmean, counters

# ================= isolated rate re-calibration legs =================
def straight_filament(nmono, nfil):
    """straight nfil-mer as chain 0 at box center; rest = far gas."""
    X = np.zeros((2 * nmono, 3))
    c = LBOX / 2.0
    tp = Topo(nmono)
    for i in range(nfil):
        cen = np.array([c + (i - (nfil - 1) / 2.0) * PITCH, c, c])
        X[head(i)] = cen + [0.25, 0, 0]; X[tail(i)] = cen - [0.25, 0, 0]
        tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1; tp.mchain[i] = 0
    tp.prev[0] = -1; tp.next[nfil - 1] = -1
    tp.clive[0] = True; tp.cpoint[0] = 0; tp.cbarb[0] = nfil - 1; tp.cmlen[0] = nfil
    for m in range(nfil, nmono):
        X[head(m)] = [1.0, 1.0 + 0.3 * (m - nfil), 1.0]
        X[tail(m)] = [1.0, 1.0 + 0.3 * (m - nfil), 0.5]
    rebuild_bonds(tp, 2 * nmono)
    anch = X[:2].copy()
    amask = np.zeros(2 * nmono, dtype=bool)
    amask[0] = True; amask[1] = True
    tp.anchm = 0
    return X, tp, anch, amask

def unbind_leg(which, atp, nepochs=1000, nsteps=400):
    """forced-state unbind calibration. which='barbed'|'pointed'.
    Each epoch: fresh straight 15-mer with all-bound-ATP or all-ADP,
    binds off; count unbinds and eligible steps; return-capture-free."""
    global DOHYD
    sav = DOHYD; DOHYD = 0          # no hydrolysis during forced-state legs
    nmono = 30; nfil = 15
    ev = 0; elig = 0
    rng = np.random.default_rng(SEED + (11 if which == 'barbed' else 13) + (0 if atp else 100))
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    for ep in range(nepochs):
        X, tp, anch, amask = straight_filament(nmono, nfil)
        tp.nuc[:] = True
        for m in range(nfil):
            tp.nuc[m] = atp
        counters = new_counters(); counters['_amask'] = amask; counters['_anch'] = anch
        V = np.zeros_like(X)
        for step in range(1, nsteps + 1):
            F = forces(X, tp, anch, amask, np.ones(2 * nmono, dtype=bool))
            V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
            X = X + V * DT
            if which == 'barbed':
                if tp.clive[0] and tp.cmlen[0] > NSEED and tp.hprot[tp.cbarb[0]] == 0:
                    elig += 1
                kinetics(X, tp, nmono, rng, counters, allow_on=False, allow_off=True,
                         allow_pointed=False, allow_branch=False, allow_hyd=False)
            else:
                if tp.clive[0] and tp.cmlen[0] > NSEED and tp.hprot[tp.cpoint[0]] == 0:
                    elig += 1
                kinetics(X, tp, nmono, rng, counters, allow_on=False, allow_off=False,
                         allow_pointed=True, allow_branch=False, allow_hyd=False)
        ev += counters['nunbind'] if which == 'barbed' else counters['nunbindp']
    DOHYD = sav
    rate = ev / max(elig, 1)
    nom = (KOFFB_T if atp else KOFFB_A) if which == 'barbed' else (KOFFP_T if atp else KOFFP_A)
    print('  %s %s: rate %.6e /step (%d events, %d eligible) nominal %.6e ratio %.3f'
          % (which, 'ATP' if atp else 'ADP', rate, ev, elig, nom * DT, rate / (nom * DT)),
          flush=True)
    return rate / (nom * DT)

def hyd_leg(nepochs=40, nsteps=20000):
    """khyd: fresh all-ATP 15-mer each epoch (depletes within ~7k steps);
    pooled flips / ATP-monomer-steps. No bind/unbind/branch/link."""
    nmono = 30; nfil = 15
    rng = np.random.default_rng(SEED + 17)
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    flips = 0; draws = 0
    for ep in range(nepochs):
        X, tp, anch, amask = straight_filament(nmono, nfil)
        counters = new_counters(); counters['_amask'] = amask; counters['_anch'] = anch
        V = np.zeros_like(X)
        for step in range(1, nsteps + 1):
            F = forces(X, tp, anch, amask, np.ones(2 * nmono, dtype=bool))
            V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
            X = X + V * DT
            kinetics(X, tp, nmono, rng, counters, allow_on=False, allow_off=False,
                     allow_pointed=False, allow_branch=False, allow_hyd=True)
        flips += counters['nhyd']; draws += counters['hydsum']
    rate = flips / max(draws, 1)
    print('  khyd: rate %.6e /monomer/step (%d flips, %d ATP-monomer-steps) nominal %.6e ratio %.3f'
          % (rate, flips, draws, KHYD * DT, rate / (KHYD * DT)), flush=True)
    return rate / (KHYD * DT)

def cal_hyd():
    print('== merged isolated leg: hydrolysis / state-dependent koff (M4H) + pointed (M4B) ==')
    unbind_leg('barbed', True)
    unbind_leg('barbed', False)
    unbind_leg('pointed', True)
    unbind_leg('pointed', False)
    hyd_leg()

def cal_branch(nseeds=6, nsteps=40000):
    global KBR, DOHYD, DOPOINTED, DOLINK
    sav = (KBR, DOHYD, DOPOINTED, DOLINK)
    KBR = 0.20; DOHYD = 0; DOPOINTED = 0; DOLINK = 0
    print('== merged isolated leg: KBR branch rate (30-mer, no bind/unbind/hyd/link) ==')
    ev_tot = 0; el_tot = 0.0
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    for sd in range(nseeds):
        rng = np.random.default_rng(SEED + 1000 * sd)
        nmono = 54
        X, tp, anch, amask = dyn_init(nmono, rng, nseed0=30)
        V = np.zeros_like(X)
        counters = new_counters(); counters['_amask'] = amask; counters['_anch'] = anch
        for step in range(1, nsteps + 1):
            F = forces(X, tp, anch, amask, np.ones(2 * nmono, dtype=bool))
            V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
            X = X + V * DT
            kinetics(X, tp, nmono, rng, counters, allow_on=False, allow_off=False,
                     allow_pointed=False, allow_branch=True, allow_hyd=False)
        ev_tot += counters['nbr']; el_tot += counters['elsum']
        print('  seed %d: branches %d elsum %.1f' % (sd, counters['nbr'], counters['elsum']),
              flush=True)
    kbr_eff = ev_tot / max(el_tot, 1.0)
    print('  KBR_eff = %.6e /monomer/step (%d events, elsum %.0f) nominal %.6e ratio %.3f'
          % (kbr_eff, ev_tot, el_tot, KBR * DT, kbr_eff / (KBR * DT)), flush=True)
    KBR, DOHYD, DOPOINTED, DOLINK = sav
    return kbr_eff / (KBR * DT)

def cal_link(nsteps=80000):
    """link birth/death in isolation: two live 8-mers at gap 0.8, poly off."""
    global DOHYD, DOPOINTED, DOBRANCH
    sav = (DOHYD, DOPOINTED, DOBRANCH)
    DOHYD = 0; DOPOINTED = 0; DOBRANCH = 0
    print('== merged isolated leg: link birth/death (two 8-mers, gap 0.8, steady) ==')
    nmono = 16
    X = np.zeros((2 * nmono, 3))
    tp = Topo(nmono)
    for f, y in ((0, 5.0), (1, 5.8)):
        for i in range(8):
            m = 8 * f + i
            cen = np.array([3.0 + i * PITCH, y, LBOX / 2.0])
            X[head(m)] = cen + [0.25, 0, 0]; X[tail(m)] = cen - [0.25, 0, 0]
            tp.state[m] = True; tp.prev[m] = m - 1; tp.next[m] = m + 1; tp.mchain[m] = f
        tp.prev[8 * f] = -1; tp.next[8 * f + 7] = -1
        tp.clive[f] = True; tp.cpoint[f] = 8 * f; tp.cbarb[f] = 8 * f + 7; tp.cmlen[f] = 8
    rebuild_bonds(tp, 2 * nmono)
    anch = np.zeros((2 * nmono, 3)); amask = np.zeros(2 * nmono, dtype=bool)
    for f in (0, 1):
        anch[head(8 * f)] = X[head(8 * f)].copy(); anch[tail(8 * f)] = X[tail(8 * f)].copy()
        amask[head(8 * f)] = True; amask[tail(8 * f)] = True
    tp.anchm = 0
    rng = np.random.default_rng(SEED + 23)
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    counters = new_counters(); counters['_amask'] = amask; counters['_anch'] = anch
    V = np.zeros_like(X)
    half = nsteps // 2
    cb = 0; cd_ = 0; cs = 0; ls2 = 0
    for step in range(1, nsteps + 1):
        F = forces(X, tp, anch, amask, np.ones(2 * nmono, dtype=bool))
        V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
        X = X + V * DT
        pre = (counters['lbirths'], counters['ldeaths'], counters['lsteps'])
        nc0 = len(candidates(X, tp))
        link_bd(X, tp, rng, counters, step)
        if step > half:
            cb += counters['lbirths'] - pre[0]
            cd_ += counters['ldeaths'] - pre[1]
            ls2 += counters['lsteps'] - pre[2]
            if tp.nlink < MAXL:
                cs += nc0
    birth = cb / max(cs, 1)
    death = cd_ / max(ls2, 1)
    print('  (second-half) births %d over %d candidate-slots -> kf %.6e nominal %.6e ratio %.3f'
          % (cb, cs, birth, KLINKF * DT, birth / (KLINKF * DT)), flush=True)
    print('  (second-half) deaths %d over %d link-steps -> kb %.6e nominal %.6e ratio %.3f'
          % (cd_, ls2, death, KLINKB * DT, death / (KLINKB * DT)), flush=True)
    DOHYD, DOPOINTED, DOBRANCH = sav
    return birth / (KLINKF * DT), death / (KLINKB * DT)

def main():
    args = sys.argv[1:]
    if not args or args[0] == '--fd':
        fd_check()
    elif args[0] == '--cert':
        cert()
    elif args[0] == '--cal':
        which = args[1] if len(args) > 1 else 'all'
        if which in ('hyd', 'all'):
            cal_hyd()
        if which in ('branch', 'all'):
            cal_branch()
        if which in ('link', 'all'):
            cal_link()
    elif args[0] in ('--run', '--full'):
        nsteps = int(args[1]) if len(args) > 1 else 300000
        seed = int(args[2]) if len(args) > 2 else SEED
        out = args[3] if len(args) > 3 else '/tmp/m4i'
        run(nsteps, seed, out)

if __name__ == '__main__':
    main()
