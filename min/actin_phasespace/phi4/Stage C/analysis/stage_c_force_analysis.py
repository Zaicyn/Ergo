#!/usr/bin/env python3
"""Stage C force-form O-R5 analysis over the runs18 hold-release grid.

Protocol (see RELEASE_PROTOCOL.md): brush_bra_r.ergo, PREL=300000,
XP0=9.0, XPLO=1.5, XPHI=11.4, 1M steps, F x {77031, 84950}.

Outputs:
  - stationary post-release (t>400k) force balance per run: fmean, neng,
    clamp occupancy, xp mean/min
  - hold-phase (200-300k) pinned-plane stall force (thin brush)
  - stall extrapolation from margin(F) = fmean - F
  - post-release crossing (ride) slopes -- shown to be transient-dominated,
    retained for the record only.
"""
import numpy as np, glob, os, re

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "runs18")
XPHI = 11.4

def load_xpt(path):
    t, x, f = [], [], []
    for line in open(path, errors="replace"):
        if line.startswith("xpt "):
            p = line.split()
            t.append(int(p[1])); x.append(float(p[2])); f.append(float(p[3]))
    return np.array(t), np.array(x), np.array(f)

def load_pstn(path):
    t, fm, nc, ne = [], [], [], []
    for line in open(path, errors="replace"):
        if line.startswith("pstn "):
            p = line.split()
            t.append(int(p[1])); fm.append(float(p[5]))
            nc.append(int(p[7]));  ne.append(float(p[11]))
    return np.array(t), np.array(fm), np.array(nc), np.array(ne)

rows = {}
for path in sorted(glob.glob(os.path.join(DIR, "rel2_*.log"))):
    name = os.path.basename(path)[:-4]
    m = re.match(r"rel2_f([\d.]+)_s(\d+)", name)
    if not m:
        continue
    F, S = float(m.group(1)), int(m.group(2))
    t, fm, nc, ne = load_pstn(path)
    tx, xx, fx = load_xpt(path)
    w  = t > 400000
    h  = (t > 200000) & (t <= 300000)
    wx = tx > 400000
    rows[(F, S)] = dict(
        fm=fm[w].mean(), fm_sd=fm[w].std(), ne=ne[w].mean(),
        occ=float((xx[wx] >= XPHI - 0.05).mean()),
        xm=xx[wx].mean(), xmin=xx[wx].min(),
        holdF=fm[h].mean(), holdN=ne[h].mean())

print(f"{'run':22s} {'<fmean>':>8s} {'sd':>6s} {'<neng>':>6s} {'occHI':>6s} "
      f"{'xpmean':>7s} {'xpmin':>6s} {'holdF':>6s} {'holdN':>6s}")
for (F, S), g in sorted(rows.items()):
    print(f"rel2_f{F}_s{S:<8d}      {g['fm']:8.2f} {g['fm_sd']:6.2f} {g['ne']:6.2f} "
          f"{g['occ']:6.2f} {g['xm']:7.2f} {g['xmin']:6.2f} {g['holdF']:6.2f} {g['holdN']:6.2f}")

Fs = sorted(set(F for F, _ in rows))
margin = []
print("\n== stall bracket (margin = fmean - F; >0 => brush holds plane at tip field) ==")
for F in Fs:
    fms = [rows[(F, S)]['fm'] for S in (77031, 84950) if (F, S) in rows]
    occ = [rows[(F, S)]['occ'] for S in (77031, 84950) if (F, S) in rows]
    m_m = float(np.mean(fms) - F)
    margin.append(m_m)
    print(f"F={F:4.1f}: fmean={np.mean(fms):5.2f}  margin={m_m:+5.2f}  clampOcc={np.mean(occ):.2f}")

Fs_a, mg = np.array(Fs), np.array(margin)
sl, ic = np.linalg.lstsq(np.vstack([Fs_a, np.ones(len(Fs_a))]).T, mg, rcond=None)[0]
print(f"\nmargin(F) = {ic:.2f} {sl:+.3f}*F  ->  extrapolated stall F* = {-ic/sl:.1f}")
print("thin-brush pinned stall (hold phase): "
      f"{np.mean([g['holdF'] for g in rows.values()]):.1f} +/- "
      f"{np.std([g['holdF'] for g in rows.values()]):.1f}")
print("certified unbranched fixed-slab stall: 2.5-3")
