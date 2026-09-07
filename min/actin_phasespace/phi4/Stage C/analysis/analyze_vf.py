#!/usr/bin/env python3
"""v(F) analysis for runs18 hold-release ensemble.

Protocol: piston pinned at XP0=9.0 until PREL=300000, then released.
Fit window: steps in (PREL+100k, t_clamp) where t_clamp = first step with
xp >= CLAMP_GUARD (sustained clamp riding contaminates drift).
Estimator: binned OLS slope of xp(t) + Theil-Sen cross-check.
"""
import sys, glob, os, re
import numpy as np

PREL = 300000
DISCARD = 100000
XPHI = 11.4
CLAMP_GUARD = 11.35      # exclude/runcate once plane reaches this
BIN = 20000
DIR = "/mnt/agents/output/actin_phasespace/phi4/runs18"

def parse(path):
    xs, fr = [], []
    ps = []  # (step, fmean, neng)
    with open(path, errors="replace") as f:
        for line in f:
            if line.startswith("xpt "):
                p = line.split()
                xs.append((int(p[1]), float(p[2])))
                fr.append(float(p[3]))
            elif line.startswith("pstn "):
                p = line.split()
                ps.append((int(p[1]), float(p[4]), float(p[10])))
    return np.array(xs), np.array(fr), np.array(ps) if ps else np.zeros((0,3))

def theilsen(t, y):
    # subsample for speed
    n = len(t)
    idx = np.linspace(0, n-1, min(n, 400)).astype(int)
    tt, yy = t[idx], y[idx]
    sl = []
    for i in range(len(tt)):
        d = tt[i+1:] - tt[i]
        m = d != 0
        sl.extend(((yy[i+1:] - yy[i])[m]) / d[m])
    return float(np.median(sl)) if sl else float("nan")

def analyze(path):
    xs, fr, ps = parse(path)
    t, xp = xs[:,0], xs[:,1]
    w = t > PREL + DISCARD
    t, xp, fr = t[w], xp[w], fr[w]
    # clamp truncation
    hit = np.nonzero(xp >= CLAMP_GUARD)[0]
    t_clamp = t[hit[0]] if len(hit) else None
    if t_clamp is not None:
        keep = t < t_clamp
        tf, xpf = t[keep], xp[keep]
    else:
        tf, xpf = t, xp
    # binned OLS
    v_ols = float("nan"); nb = 0
    if len(tf) > 10:
        edges = np.arange(tf[0], tf[-1] + BIN, BIN)
        bc, bm = [], []
        for a, b in zip(edges[:-1], edges[1:]):
            m = (tf >= a) & (tf < b)
            if m.sum() >= 5:
                bc.append(0.5*(a+b)); bm.append(xpf[m].mean())
        bc, bm = np.array(bc), np.array(bm)
        nb = len(bc)
        if nb >= 3:
            A = np.vstack([bc, np.ones(nb)]).T
            v_ols = float(np.linalg.lstsq(A, bm, rcond=None)[0][0])
    v_ts = theilsen(tf, xpf) if len(tf) > 10 else float("nan")
    # clamp occupancy over full post-release window
    occ_clamp = float((xp >= XPHI - 1e-9).mean())
    xmin = float(xp.min())
    # pstn windowed stats post-release, excluding clamp-riding samples
    if len(ps):
        m = (ps[:,0] > PREL + DISCARD)
        fmean = ps[m,1]; neng = ps[m,2]
        fmean_all = float(fmean.mean()); neng_all = float(neng.mean())
    else:
        fmean_all = neng_all = float("nan")
    return dict(v_ols=v_ols, v_ts=v_ts, nbins=nb, t_clamp=t_clamp,
                occ_clamp=occ_clamp, xmin=xmin, fmean=fmean_all, neng=neng_all)

rows = []
for path in sorted(glob.glob(os.path.join(DIR, "rel2_*.log"))):
    name = os.path.basename(path)[:-4]
    m = re.match(r"rel2_f([\d.]+)_s(\d+)", name)
    if not m: continue
    F, S = float(m.group(1)), int(m.group(2))
    r = analyze(path)
    r.update(F=F, seed=S, name=name)
    rows.append(r)

print(f"{'run':22s} {'v_ols(σ/st)':>12s} {'v_TS(σ/st)':>12s} {'bins':>4s} {'t_clamp':>8s} {'occHI':>6s} {'xpmin':>6s} {'<f>':>6s} {'<neng>':>6s}")
for r in rows:
    tc = f"{r['t_clamp']:8d}" if r['t_clamp'] else "     ---"
    print(f"{r['name']:22s} {r['v_ols']:12.3e} {r['v_ts']:12.3e} {r['nbins']:4d} {tc} {r['occ_clamp']:6.3f} {r['xmin']:6.2f} {r['fmean']:6.2f} {r['neng']:6.2f}")

print("\n== v(F) summary (mean over seeds, σ/step) ==")
Fs = sorted(set(r['F'] for r in rows))
for F in Fs:
    vs = [r['v_ols'] for r in rows if r['F']==F and not np.isnan(r['v_ols'])]
    vt = [r['v_ts'] for r in rows if r['F']==F and not np.isnan(r['v_ts'])]
    if vs:
        print(f"F={F:4.1f}  v_ols={np.mean(vs): .3e} (n={len(vs)})  v_TS={np.mean(vt): .3e}")
