#!/usr/bin/env python3
# crosslink_mirror.py - M4d mirror: transient crosslinking (fascin-like).
# Oracle for crosslink.ergo: --fd, --cert, --cal, --run N SEED [KLINKF].
# Physics must match the engine exactly; RNG streams are independent
# (engine hash RNG vs numpy) - only STATISTICS are compared.
import numpy as np, sys

# ---- parameters (must match crosslink.ergo) ----
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
RCROSS = 0.1
SIG    = 0.5
C216   = 2.0 ** (1.0 / 6.0)
RCAP   = 1.4
QMIN   = 0.0
KON    = 500.0
KOFF   = 0.09
KSEED  = 5.0
NSEED  = 3
NFIL   = 2
YSEEDA = 5.0
YSEEDB = 6.5
# crosslinks
KLINK  = 20.0
L0     = 0.7
RLINK  = 1.0
KLINKF = 0.3
KLINKB = 3.0
MAXL   = 64
LOOPMIN = 6
# run
NMONO  = 96
SEED   = 77031
PHI_G  = 2.39996322972865332
WCUT   = C216 * SIG
CERTDY = 0.85

def head(m): return 2 * m
def tail(m): return 2 * m + 1

class Topo:
    def __init__(self, cap):
        self.state = np.zeros(cap, dtype=bool)
        self.prev  = np.full(cap, -1, dtype=int)
        self.next  = np.full(cap, -1, dtype=int)
        self.filid = np.zeros(cap, dtype=int)     # 0 free, 1/2 filament
        self.posi  = np.zeros(cap, dtype=int)     # contour index (0 free)
        self.barbed = np.full(NFIL, -1, dtype=int)
        self.headm  = np.full(NFIL, -1, dtype=int)
        self.mle    = np.zeros(NFIL, dtype=int)
        self.bonds = []          # junction springs (a, b, rest)
        self.excl = None         # static exclusion (intra + junction) ONLY
        # link slots
        self.li = np.full(MAXL, -1, dtype=int)
        self.lj = np.full(MAXL, -1, dtype=int)
        self.lact = np.zeros(MAXL, dtype=bool)
        self.lborn = np.zeros(MAXL, dtype=int)
        self.lmask = None        # (nb, nb) bool: pair already linked

    @property
    def mlen(self):
        return int(self.mle.sum())

def rebuild_bonds(tp, nb):
    tp.bonds = []
    tp.excl = np.zeros((nb, nb), dtype=bool)
    tp.posi[:] = 0
    for m in range(nb // 2):
        tp.excl[head(m), tail(m)] = True
        tp.excl[tail(m), head(m)] = True
    for m0 in range(nb // 2):
        if tp.state[m0] and tp.prev[m0] == -1:
            q = m0
            tp.posi[q] = 1
            p = 1
            while tp.next[q] != -1:
                i = q; q = tp.next[q]; p += 1
                tp.posi[q] = p
                tp.bonds.append((head(i), head(q), PITCH))
                tp.bonds.append((tail(i), tail(q), PITCH))
                tp.bonds.append((head(i), tail(q), RCROSS))
                for a, b in [(head(i), head(q)), (tail(i), tail(q)), (head(i), tail(q))]:
                    tp.excl[a, b] = True; tp.excl[b, a] = True
    if tp.bonds:
        tp.ba = np.array([b[0] for b in tp.bonds])
        tp.bb = np.array([b[1] for b in tp.bonds])
        tp.br0 = np.array([b[2] for b in tp.bonds])
    else:
        tp.ba = np.zeros(0, dtype=int); tp.bb = np.zeros(0, dtype=int)
        tp.br0 = np.zeros(0)

def forces(X, tp, anch, anch_idx, energy=False, Dd=None):
    nb = X.shape[0]
    F = np.zeros_like(X)
    if Dd is None:
        D = X[:, None, :] - X[None, :, :]
        d2 = np.einsum('ijk,ijk->ij', D, D)
        d = np.sqrt(np.maximum(d2, 1e-32))
    else:
        D, d = Dd
    up = np.triu_indices(nb, 1)
    pair = ~tp.excl[up]
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
    ha = np.arange(0, nb, 2); ta = ha + 1
    drb = X[ha] - X[ta]
    ddb = np.maximum(np.linalg.norm(drb, axis=1), 1e-16)
    fb = 2.0 * KBOND * (ddb - R0) / ddb
    np.add.at(F, ha, -fb[:, None] * drb)
    np.add.at(F, ta, fb[:, None] * drb)
    ebond = float(np.sum(KBOND * (ddb - R0) ** 2)) if energy else 0.0
    efil = 0.0
    if tp.ba.size:
        drf = X[tp.ba] - X[tp.bb]
        ddf = np.maximum(np.linalg.norm(drf, axis=1), 1e-16)
        ff = 2.0 * KFIL * (ddf - tp.br0) / ddf
        np.add.at(F, tp.ba, -ff[:, None] * drf)
        np.add.at(F, tp.bb, ff[:, None] * drf)
        if energy: efil = float(np.sum(KFIL * (ddf - tp.br0) ** 2))
    elink = 0.0
    act = np.nonzero(tp.lact)[0]
    if act.size:
        la = tp.li[act]; lb = tp.lj[act]
        drl = X[la] - X[lb]
        ddl = np.maximum(np.linalg.norm(drl, axis=1), 1e-16)
        fl = 2.0 * KLINK * (ddl - L0) / ddl
        np.add.at(F, la, -fl[:, None] * drl)
        np.add.at(F, lb, fl[:, None] * drl)
        if energy: elink = float(np.sum(KLINK * (ddl - L0) ** 2))
    eanch = 0.0
    for k, b in enumerate(anch_idx):
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
        return F, (ewca, ebond, efil, elink, eanch, ewall)
    return F

def axes_of(X, nmono):
    ax = np.zeros((nmono, 3)); cen = np.zeros((nmono, 3))
    for m in range(nmono):
        dr = X[head(m)] - X[tail(m)]
        n = max(float(np.linalg.norm(dr)), 1e-16)
        ax[m] = dr / n; cen[m] = 0.5 * (X[head(m)] + X[tail(m)])
    return ax, cen

def jitter(b):
    return 0.02 * np.array([np.sin(b * 1.7), np.cos(b * 2.3), np.sin(b * 0.9 + 1.0)])

# ---- cert config: hexamer arc (chain A) + tetramer (chain B) at CERTDY
#      + 3 static links + 10 spiral + close pair ----
def cert_config():
    nm = 22
    X = np.zeros((2 * nm, 3))
    c = LBOX / 2.0
    th = 0.03
    pos = np.array([c, c, c])
    ax = np.array([1.0, 0.0, 0.0])
    for i in range(6):
        if i > 0:
            phi = th * i
            ax = np.array([np.cos(phi), np.sin(phi), 0.0])
            pos = pos + PITCH * np.array([np.cos(phi - th), np.sin(phi - th), 0.0])
        X[head(i)] = pos + 0.25 * ax
        X[tail(i)] = pos - 0.25 * ax
    for k in range(4):                       # chain B: monomers 6..9 (0-based)
        m = 6 + k
        cen = np.array([c + k * PITCH, c - CERTDY, c])
        X[head(m)] = cen + [0.25, 0, 0]
        X[tail(m)] = cen - [0.25, 0, 0]
    for k in range(10):                      # free spiral: monomers 10..19
        m = 10 + k
        phi = k * PHI_G
        pk = np.array([c + 4.5 * np.cos(phi), c + 4.5 * np.sin(phi), c - 1.5 + 3.0 * (k % 2)])
        ak = np.array([np.cos(phi + 1.0), np.sin(phi + 1.0), 0.5])
        ak = ak / np.linalg.norm(ak)
        X[head(m)] = pk + 0.25 * ak
        X[tail(m)] = pk - 0.25 * ak
    pA = np.array([c + 3.0, c - 3.0, c]); pB = pA + np.array([0.0, 0.55, 0.0])
    for m, p in ((20, pA), (21, pB)):        # close pair
        X[head(m)] = p + [0.25, 0, 0]
        X[tail(m)] = p - [0.25, 0, 0]
    # anchors: first monomer of each chain (beads 0,1 and 12,13)
    anch_idx = [0, 1, head(6), tail(6)]
    anch_pos = np.array([X[b].copy() for b in anch_idx])
    for b in range(2 * nm):
        X[b] = X[b] + jitter(b)
    tp = Topo(nm)
    for i in range(6):
        tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1; tp.filid[i] = 1
    for i in range(6, 10):
        tp.state[i] = True; tp.prev[i] = i - 1; tp.next[i] = i + 1; tp.filid[i] = 2
    tp.prev[0] = -1; tp.next[5] = -1
    tp.prev[6] = -1; tp.next[9] = -1
    tp.headm = np.array([0, 6]); tp.barbed = np.array([5, 9])
    tp.mle = np.array([6, 4])
    rebuild_bonds(tp, 2 * nm)
    # 3 static links: (head0,head6), (head1,head7), (tail2,tail8) 0-based
    links = [(head(0), head(6)), (head(1), head(7)), (tail(2), tail(8))]
    for L, (a, b) in enumerate(links):
        tp.lact[L] = True; tp.li[L] = a; tp.lj[L] = b; tp.lborn[L] = 0
    sync_lmask(tp)
    return X, tp, anch_pos, anch_idx

def sync_lmask(tp):
    nb = tp.excl.shape[0]
    tp.lmask = np.zeros((nb, nb), dtype=bool)
    for L in range(MAXL):
        if tp.lact[L]:
            tp.lmask[tp.li[L], tp.lj[L]] = True
            tp.lmask[tp.lj[L], tp.li[L]] = True

def fd_check():
    X, tp, anch, aidx = cert_config()
    rng = np.random.default_rng(12345)
    X = X + rng.normal(scale=0.03, size=X.shape)
    F, _ = forces(X, tp, anch, aidx, energy=True)
    # report link strains to prove links loaded, uncapped
    for L in range(MAXL):
        if tp.lact[L]:
            dd = float(np.linalg.norm(X[tp.li[L]] - X[tp.lj[L]]))
            print('link %d pair (%d,%d) d=%.4f strain=%.4f force=%.3f' %
                  (L, tp.li[L], tp.lj[L], dd, dd - L0, 2 * KLINK * abs(dd - L0)))
    h = 1e-6
    worst = 0.0; worst_abs = 0.0; wb = -1; wax = -1
    for b in range(X.shape[0]):
        for a in range(3):
            Xp = X.copy(); Xp[b, a] += h
            Xm = X.copy(); Xm[b, a] -= h
            _, ep = forces(Xp, tp, anch, aidx, energy=True)
            _, em = forces(Xm, tp, anch, aidx, energy=True)
            fd = -(sum(ep) - sum(em)) / (2 * h)
            an = F[b, a]
            rel = abs(fd - an) / max(abs(an), 1.0)
            if rel > worst:
                worst = rel; wb = b; wax = a
            worst_abs = max(worst_abs, abs(fd - an))
    print('FD check: max_rel_vs_1 %.3e (bead %d ax %d)  max_abs %.3e' %
          (worst, wb, wax, worst_abs))
    return worst

def cert(out='/tmp/m4d/m4d_cert'):
    X, tp, anch, aidx = cert_config()
    F, (ew, eb, ef, el, ea, ewl) = forces(X, tp, anch, aidx, energy=True)
    with open(out + '_config.txt', 'w') as f:
        f.write('# MIRROR_DUMP nmono 22 mlen 10 nlink 3\n')
        for b in range(X.shape[0]):
            f.write('%.17e %.17e %.17e\n' % tuple(X[b]))
    with open(out + '_forces.txt', 'w') as f:
        for b in range(X.shape[0]):
            f.write('%.17e %.17e %.17e\n' % tuple(F[b]))
    print('CERT ewca %.17e ebond %.17e efil %.17e elink %.17e eanch %.17e ewall %.17e'
          % (ew, eb, ef, el, ea, ewl))
    print('wrote %s_{config,forces}.txt' % out)

# ============================ dynamics ============================

def dyn_init(nmono, rng):
    X = np.zeros((2 * nmono, 3))
    c = LBOX / 2.0
    tp = Topo(nmono)
    for f in range(NFIL):
        y = YSEEDA if f == 0 else YSEEDB
        for i in range(NSEED):
            m = f * NSEED + i
            cen = np.array([c + (i - 1.0) * PITCH, y, c])
            X[head(m)] = cen + [0.25, 0, 0]
            X[tail(m)] = cen - [0.25, 0, 0]
            tp.state[m] = True; tp.prev[m] = m - 1; tp.next[m] = m + 1
            tp.filid[m] = f + 1
        tp.prev[f * NSEED] = -1; tp.next[f * NSEED + NSEED - 1] = -1
        tp.headm[f] = f * NSEED
        tp.barbed[f] = f * NSEED + NSEED - 1
        tp.mle[f] = NSEED
    placed = [X[b].copy() for m in range(2 * NSEED) for b in (head(m), tail(m))]
    for m in range(2 * NSEED, nmono):
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
    sync_lmask(tp)
    anch_idx = [0, 1, head(NSEED), tail(NSEED)]     # beads 0,1 and 6,7
    anch = np.array([X[b].copy() for b in anch_idx])
    return X, tp, anch, anch_idx

def kinetics(X, tp, nmono, rng, ctr, allow_poly=True):
    """Per-filament barbed-end bind/unbind; unbind strips links."""
    if not allow_poly:
        return
    ax, _ = axes_of(X, nmono)
    for f in range(NFIL):
        u_on = rng.random(); u_off = rng.random()
        barb = tp.barbed[f]
        hb = X[head(barb)]
        ab = ax[barb]
        for m in range(nmono):
            if tp.state[m]:
                continue
            if np.linalg.norm(X[tail(m)] - hb) < RCAP and float(ax[m] @ ab) > QMIN:
                if u_on < min(1.0, KON * DT):
                    X[tail(m)] = hb + RCROSS * ab
                    X[head(m)] = X[tail(m)] + R0 * ab
                    tp.state[m] = True
                    tp.prev[m] = barb; tp.next[barb] = m
                    tp.next[m] = -1; tp.barbed[f] = m
                    tp.mle[f] += 1; tp.filid[m] = f + 1
                    rebuild_bonds(tp, 2 * nmono)
                    ctr['binds'] += 1
                break
        if tp.mle[f] > NSEED and u_off < KOFF * DT:
            m = tp.barbed[f]; p = tp.prev[m]
            tp.next[p] = -1; tp.barbed[f] = p
            tp.state[m] = False; tp.prev[m] = -1
            tp.mle[f] -= 1; tp.filid[m] = 0
            hm, tm = head(m), tail(m)
            for L in range(MAXL):                # strip links touching m
                if tp.lact[L] and (tp.li[L] in (hm, tm) or tp.lj[L] in (hm, tm)):
                    tp.lact[L] = False
                    tp.lmask[tp.li[L], tp.lj[L]] = False
                    tp.lmask[tp.lj[L], tp.li[L]] = False
                    ctr['lstrips'] += 1
            ab = ax[p]
            hb2 = X[head(p)]
            X[tail(m)] = hb2 + (RCAP + 0.25) * ab
            X[head(m)] = X[tail(m)] + R0 * ab
            rebuild_bonds(tp, 2 * nmono)
            ctr['unbinds'] += 1

def candidates(X, tp, nmono, d=None):
    """Unlinked eligible pairs (i<j): both bound, not statically excluded,
    d<=RLINK, same-filament pairs need |dpos|>=LOOPMIN. Lexicographic order."""
    if d is None:
        D = X[:, None, :] - X[None, :, :]
        d = np.sqrt(np.maximum(np.einsum('ijk,ijk->ij', D, D), 1e-32))
    bmon = np.repeat(tp.state, 2)                    # bead bound mask
    ok = bmon[:, None] & bmon[None, :]
    ok &= ~tp.excl
    ok &= ~tp.lmask
    ok &= (d <= RLINK)
    fm = np.repeat(tp.filid, 2); pm = np.repeat(tp.posi, 2)
    loopok = (fm[:, None] != fm[None, :]) | (np.abs(pm[:, None] - pm[None, :]) >= LOOPMIN)
    ok &= loopok
    ok = np.triu(ok, 1)
    ii, jj = np.nonzero(ok)
    return list(zip(ii.tolist(), jj.tolist()))

def link_bd(X, tp, nmono, rng, ctr, step, allow_birth=True, allow_death=True):
    """Birth: per-candidate draw P=KLINKF*DT. Death: per-link P=KLINKB*DT."""
    if allow_birth:
        cand = candidates(X, tp, nmono)
        ctr['cand'] += len(cand)
        ctr['cand_steps'] += 1
        if tp.lact.sum() < MAXL:
            ctr['cand_elig'] += len(cand)
        if cand and KLINKF > 0:
            us = rng.random(len(cand))
            for (a, b), u in zip(cand, us):
                if u < KLINKF * DT and tp.lact.sum() < MAXL:
                    L = int(np.argmax(~tp.lact))     # first free slot
                    tp.lact[L] = True; tp.li[L] = a; tp.lj[L] = b
                    tp.lborn[L] = step
                    tp.lmask[a, b] = True; tp.lmask[b, a] = True
                    ctr['lbirths'] += 1
    if allow_death:
        for L in range(MAXL):
            if tp.lact[L]:
                if rng.random() < KLINKB * DT:
                    tp.lact[L] = False
                    tp.lmask[tp.li[L], tp.lj[L]] = False
                    tp.lmask[tp.lj[L], tp.li[L]] = False
                    ctr['ldeaths'] += 1
                    ctr['ltsum'] += step - tp.lborn[L]
                    ctr['ltcnt'] += 1
                ctr['link_steps'] += 1

def bundle_obs(X, tp, nmono):
    """(alignment, separation, nlink_inter, ee1, ee2) diagnostics."""
    ax, cen = axes_of(X, nmono)
    al = 0.0; sep = 0.0; nli = 0; ee = [0.0, 0.0]
    m1 = np.nonzero(tp.state & (tp.filid == 1))[0]
    m2 = np.nonzero(tp.state & (tp.filid == 2))[0]
    if len(m1) and len(m2):
        a1 = ax[m1].mean(0); a2 = ax[m2].mean(0)
        n1 = np.linalg.norm(a1); n2 = np.linalg.norm(a2)
        if n1 > 1e-12 and n2 > 1e-12:
            al = float(a1 @ a2 / (n1 * n2))
        sep = float(np.min(np.linalg.norm(
            cen[m2][:, None, :] - cen[m1][None, :, :], axis=-1), axis=1).mean())
    for L in range(MAXL):
        if tp.lact[L]:
            fi = tp.filid[tp.li[L] // 2]; fj = tp.filid[tp.lj[L] // 2]
            if fi > 0 and fj > 0 and fi != fj:
                nli += 1
    for f in range(NFIL):
        ee[f] = float(np.linalg.norm(cen[tp.barbed[f]] - cen[tp.headm[f]]))
    return al, sep, nli, ee[0], ee[1]

def integrate_run(X, V, tp, anch, anch_idx, nmono, nsteps, rng, ndiag=500,
                  label='run', allow_poly=True, allow_birth=True,
                  allow_death=True, quiet=False):
    ctr = dict(binds=0, unbinds=0, lbirths=0, ldeaths=0, lstrips=0,
               ltsum=0, ltcnt=0, cand=0, cand_steps=0, cand_elig=0,
               link_steps=0)
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    half = dict(l=0.0, nl=0.0, nli=0.0, nc=0.0, al=0.0, sep=0.0,
                ee1=0.0, ee2=0.0, kt=0.0, n=0)
    cand_half = None
    for step in range(1, nsteps + 1):
        F = forces(X, tp, anch, anch_idx)
        V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
        X = X + V * DT
        kinetics(X, tp, nmono, rng, ctr, allow_poly)
        link_bd(X, tp, nmono, rng, ctr, step, allow_birth, allow_death)
        if step == nsteps // 2:
            cand_half = ctr['cand']
        if step % ndiag == 0:
            al, sep, nli, ee1, ee2 = bundle_obs(X, tp, nmono)
            kt = float((V ** 2).sum() / (3 * X.shape[0]))
            nlink = int(tp.lact.sum())
            if step > nsteps // 2:
                half['l'] += tp.mlen; half['nl'] += nlink; half['nli'] += nli
                half['nc'] += 0  # ncand mean filled below from ctr
                half['al'] += al; half['sep'] += sep
                half['ee1'] += ee1; half['ee2'] += ee2; half['kt'] += kt
                half['n'] += 1
            if not quiet:
                print('%s step %6d kt %.3f len1 %d len2 %d nlink %d nli %d '
                      'binds %d unb %d lb %d ld %d ls %d al %.3f sep %.3f '
                      'ee1 %.2f ee2 %.2f' %
                      (label, step, kt, tp.mle[0], tp.mle[1], nlink, nli,
                       ctr['binds'], ctr['unbinds'], ctr['lbirths'],
                       ctr['ldeaths'], ctr['lstrips'], al, sep, ee1, ee2),
                      flush=True)
    n = max(half['n'], 1)
    # candidate mean over second half: recompute not possible; report totals
    if cand_half is not None:
        cmean = (ctr['cand'] - cand_half) / float(nsteps - nsteps // 2)
    else:
        cmean = ctr['cand'] / max(ctr['cand_steps'], 1)
    print('%s FINAL lmean %.3f len1 %d len2 %d nlmean %.3f nlimean %.3f '
          'candmean %.2f almean %.3f sepmean %.3f ee1mean %.3f ee2mean %.3f '
          'ktmean %.3f' %
          (label, half['l'] / n, tp.mle[0], tp.mle[1], half['nl'] / n,
           half['nli'] / n, cmean, half['al'] / n, half['sep'] / n,
           half['ee1'] / n, half['ee2'] / n, half['kt'] / n), flush=True)
    print('%s FINAL_L lbirths %d ldeaths %d lstrips %d binds %d unbinds %d '
          'lifemean %.2f lifenom %.2f' %
          (label, ctr['lbirths'], ctr['ldeaths'], ctr['lstrips'], ctr['binds'],
           ctr['unbinds'], ctr['ltsum'] / max(ctr['ltcnt'], 1),
           1.0 / (KLINKB * DT)), flush=True)
    return half, ctr

# ============================ calibration ============================

def cal_config(nfil_mers=8):
    """Two short parallel filaments at lateral gap 0.8, no gas."""
    nmono = 2 * nfil_mers
    X = np.zeros((2 * nmono, 3))
    c = LBOX / 2.0
    tp = Topo(nmono)
    for f in range(NFIL):
        y = c - 0.4 if f == 0 else c + 0.4
        for i in range(nfil_mers):
            m = f * nfil_mers + i
            cen = np.array([c + (i - nfil_mers / 2.0) * PITCH, y, c])
            X[head(m)] = cen + [0.25, 0, 0]
            X[tail(m)] = cen - [0.25, 0, 0]
            tp.state[m] = True; tp.prev[m] = m - 1; tp.next[m] = m + 1
            tp.filid[m] = f + 1
        tp.prev[f * nfil_mers] = -1; tp.next[f * nfil_mers + nfil_mers - 1] = -1
        tp.headm[f] = f * nfil_mers
        tp.barbed[f] = f * nfil_mers + nfil_mers - 1
        tp.mle[f] = nfil_mers
    rebuild_bonds(tp, 2 * nmono)
    sync_lmask(tp)
    anch_idx = [0, 1]
    anch = np.array([X[0].copy(), X[1].copy()])
    return X, tp, anch, anch_idx, nmono

def calibrate(nsteps=40000, burn=2000):
    """Single steady-state run (two 8-mers at gap 0.8, no polymerization,
    births+deaths on). Rates per ELIGIBLE step: births per candidate-pair-
    step (steps with a free link slot), deaths per link-step. Link
    lifetime from the same run. Poisson errors reported."""
    import time
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    X, tp, anch, anch_idx, nmono = cal_config()
    V = np.zeros_like(X)
    na = np.sqrt(12.0 * KT * (1.0 - (1.0 - GAMMA * DT) ** 2))
    ctr = dict(binds=0, unbinds=0, lbirths=0, ldeaths=0, lstrips=0,
               ltsum=0, ltcnt=0, cand=0, cand_steps=0, cand_elig=0,
               link_steps=0)
    nl_sum = 0.0; nl_cnt = 0
    for step in range(1, nsteps + 1):
        F = forces(X, tp, anch, anch_idx)
        V = V * (1.0 - GAMMA * DT) + F * DT + na * (rng.random(X.shape) - 0.5)
        X = X + V * DT
        link_bd(X, tp, nmono, rng, ctr, step)
        if step == burn:                       # reset counters after burn-in
            for k in ctr: ctr[k] = 0
        if step > burn:
            nl_sum += tp.lact.sum(); nl_cnt += 1
    kb = ctr['lbirths'] / max(ctr['cand_elig'], 1)
    kd = ctr['ldeaths'] / max(ctr['link_steps'], 1)
    nb = ctr['lbirths']; nd = ctr['ldeaths']
    print('== link rate calibration: two 8-mers, gap 0.8, steady state ==')
    print('burn %d steps, measure %d steps, mean nlink %.2f' %
          (burn, nsteps - burn, nl_sum / max(nl_cnt, 1)))
    print('BIRTH: %d births / %d eligible candidate-pair-steps' % (nb, ctr['cand_elig']))
    print('  k_birth = %.6e /pair/step (nominal %.6e, ratio %.3f, poisson +-%.1f%%)'
          % (kb, KLINKF * DT, kb / (KLINKF * DT), 100.0 / max(nb, 1) ** 0.5))
    print('DEATH: %d deaths / %d link-steps' % (nd, ctr['link_steps']))
    print('  k_death = %.6e /link/step (nominal %.6e, ratio %.3f, poisson +-%.1f%%)'
          % (kd, KLINKB * DT, kd / (KLINKB * DT), 100.0 / max(nd, 1) ** 0.5))
    print('  mean lifetime %.2f steps (nominal 1/(KLINKB*DT) = %.2f)' %
          (ctr['ltsum'] / max(ctr['ltcnt'], 1), 1.0 / (KLINKB * DT)))
    print('mean-field: L* = k_birth*Cbar/k_death = (KLINKF/KLINKB)*Cbar '
          'with Cbar = second-half candidate mean of dynamic runs')
    print('cal elapsed %.1f s' % (time.time() - t0))

# ============================ run ============================

def run(nsteps=150000, seed=SEED, klinkf=None, label='mir'):
    global KLINKF
    if klinkf is not None:
        KLINKF = klinkf
    rng = np.random.default_rng(seed)
    X, tp, anch, anch_idx = dyn_init(NMONO, rng)
    V = np.zeros_like(X)
    print('# %s N=%d seed=%d KLINKF=%.3f KLINKB=%.3f KLINK=%.1f L0=%.2f RLINK=%.2f'
          % (label, NMONO, seed, KLINKF, KLINKB, KLINK, L0, RLINK), flush=True)
    import time
    t0 = time.time()
    half, ctr = integrate_run(X, V, tp, anch, anch_idx, NMONO, nsteps, rng,
                              label=label)
    print('# %s elapsed %.1f s' % (label, time.time() - t0), flush=True)

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] == '--fd':
        fd_check()
    elif args[0] == '--cert':
        cert()
    elif args[0] == '--cal':
        calibrate(int(args[1]) if len(args) > 1 else 40000)
    elif args[0] == '--run':
        nsteps = int(args[1]) if len(args) > 1 else 150000
        seed = int(args[2]) if len(args) > 2 else SEED
        kf = float(args[3]) if len(args) > 3 else None
        run(nsteps, seed, kf, label='mir%d' % seed)
