#!/usr/bin/env python3
"""Stage C law table from the runs17 clamped arms (brush_bra, S4 anchored
branching). Stationary statistics from log tails (25/26 logs are tails from
~885k due to the NUL-sparse incident; full-run counters not used).

Per run:
  neng, fmean, P(bare)=frac(pstn windows with ncon==0)     [pstn]
  nfil, nbound, nfree, ndim, nbar=nbound/nfil              [census]
  lifetime, maxn (over fdeath events)                      [fdeath]
  branch share of births = fbr / (fbr + fbirth)            [fbr, fbirth]
  blk:bind ratio                                           [bblk, bbind]
  per-tip barbed capture = bbind / (neng_mean * steps_obs) [bbind + pstn]
"""
import numpy as np, glob, os, re

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "runs17")

def analyze(path):
    neng_w, fmean_w, ncon_w = [], [], []
    nfil, nbound, nfree, ndim = [], [], [], []
    lif, mx = [], []
    n_fbr = n_fbirth = n_bbind = n_bblk = 0
    fin_binds = fin_nblk_last = None
    nblk_last = None
    tmin, tmax = None, 0
    for line in open(path, errors="replace"):
        if line.startswith("FINAL "):
            p = line.split()
            fin_binds = int(p[p.index("binds") + 1])
        elif line.startswith("pstn "):
            p = line.split()
            neng_w.append(float(p[11])); fmean_w.append(float(p[5]))
            ncon_w.append(int(p[7]))
            nblk_last = int(p[9])          # NBLK is CUMULATIVE, not windowed
            t = int(p[1]); tmax = max(tmax, t); tmin = t if tmin is None else min(tmin, t)
        elif line.startswith("census "):
            p = line.split()
            nfil.append(int(p[3])); nbound.append(int(p[5]))
            nfree.append(int(p[7])); ndim.append(int(p[9]))
        elif line.startswith("fdeath "):
            p = line.split()
            lif.append(int(p[6])); mx.append(int(p[8]))
        elif line.startswith("fbr "):
            n_fbr += 1
        elif line.startswith("fbirth "):
            n_fbirth += 1
        elif line.startswith("bbind "):
            n_bbind += 1
        elif line.startswith("bblk "):
            n_bblk += 1
    steps_obs = (tmax - tmin) if tmin is not None else 0
    ne = float(np.mean(neng_w)) if neng_w else float("nan")
    return dict(
        neng=ne, fmean=float(np.mean(fmean_w)),
        pbare=float(np.mean([c == 0 for c in ncon_w])) if ncon_w else float("nan"),
        nfil=float(np.mean(nfil)), nbound=float(np.mean(nbound)),
        nfree=float(np.mean(nfree)), ndim=float(np.mean(ndim)),
        nbar=float(np.mean(nbound) / max(np.mean(nfil), 1e-9)),
        lif=float(np.mean(lif)) if lif else float("nan"),
        maxn=float(np.mean(mx)) if mx else float("nan"),
        brshare=n_fbr / max(n_fbr + n_fbirth, 1),
        blkbind=n_bblk / max(n_bbind, 1),
        capt=n_bbind / max(ne * steps_obs, 1e-9),
        span=steps_obs,
        # full-run cross-check: cumulative NBLK (last pstn) / FINAL binds
        blkbind_cum=(nblk_last / fin_binds) if (nblk_last and fin_binds) else float("nan"))

rows = []
for path in sorted(glob.glob(os.path.join(DIR, "cla_*.log"))):
    name = os.path.basename(path)[:-4]
    m = re.match(r"cla_f([\d.]+)_s(\d+)", name)
    if not m:
        continue
    r = analyze(path); r.update(F=float(m.group(1)), seed=int(m.group(2)), name=name)
    rows.append(r)

hdr = ("run", "F", "neng", "fmean", "P(bare)", "nfil", "nbar", "nfree",
       "ndim", "lif", "maxn", "brshare", "blk:bind", "capt/tip/st", "span")
print("%-18s %4s %6s %6s %8s %6s %6s %6s %5s %7s %6s %8s %9s %11s %8s" % hdr)
for r in rows:
    print("%-18s %4.1f %6.2f %6.2f %8.4f %6.1f %6.2f %6.1f %5.1f %7.0f %6.2f %8.3f %9.1f %11.2e %8d" % (
        r['name'], r['F'], r['neng'], r['fmean'], r['pbare'], r['nfil'],
        r['nbar'], r['nfree'], r['ndim'], r['lif'], r['maxn'], r['brshare'],
        r['blkbind'], r['capt'], r['span']))

print("\n== per-load means ==")
for F in sorted(set(r['F'] for r in rows)):
    rs = [r for r in rows if r['F'] == F]
    bc = [r['blkbind_cum'] for r in rs if not np.isnan(r['blkbind_cum'])]
    print("F=%4.1f  neng=%.2f  fmean=%.2f  P(bare)=%.4f  nfil=%.1f  nbar=%.2f  "
          "lif=%.0f  maxn=%.2f  brshare=%.3f  blk:bind=%.1f  blk:bind_cum=%.1f  capt=%.2e" % (
              F, np.mean([r['neng'] for r in rs]), np.mean([r['fmean'] for r in rs]),
              np.mean([r['pbare'] for r in rs]), np.mean([r['nfil'] for r in rs]),
              np.mean([r['nbar'] for r in rs]), np.mean([r['lif'] for r in rs]),
              np.mean([r['maxn'] for r in rs]), np.mean([r['brshare'] for r in rs]),
              np.mean([r['blkbind'] for r in rs]),
              np.mean(bc) if bc else float("nan"),
              np.mean([r['capt'] for r in rs])))
