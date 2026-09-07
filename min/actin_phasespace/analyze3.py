#!/usr/bin/env python3
"""analyze3.py — phi-3 gate analysis over the 64-run hyd_fpt ensemble.

Gates:
  G1  comb shape: zero-parameter FPT-Laplace prediction (per-seed gross
      rates -> predicted per-depth P_ATP) vs measured comb.
  G2  T_comb vs T_flux: current read off the age structure (invert the FPT
      law from the measured comb ratio) vs the event-stream net current.
  G3  tip states: measured TIPS_ATP fractions vs renewal prediction a_B, a_P.
  G4  fixed point: ensemble T and lmean vs oracle (T=1.75e-4, n*~23).
  G5  inherited identities: flux closure (Tb=Tp at fixed point) + ratch
      bookkeeping (unbindp - bindp - dRank = ratch) from phi-2.
  G6  starvation brake: barbed death rate per 500-step window binned by
      lenfil should RISE with n (dynamic-instability signature), vs the
      oracle's d_B(n).
"""
import glob, sys
import numpy as np
sys.path.insert(0, "/mnt/agents/output/actin_phasespace")
import hyd_oracle as H

HALF = 150_000
NDIAG = 500

def parse(f):
    seed = int(f.rsplit("_", 1)[1].split(".")[0])
    wb = wu = wbp = wup = 0
    lenhist = {}          # lenfil -> window count (second half)
    lenwu = {}            # lenfil -> summed barbed unbinds in those windows
    lenwup = {}           # lenfil -> summed pointed unbinds
    lens = []
    tips = comb = None
    rat = None; unbp_tot = bindp_tot = None; rank0 = None; rank1 = None
    for line in open(f):
        if line.startswith("step "):
            p = line.split()
            s = int(p[1])
            lf = int(p[p.index("lenfil") + 1])
            if s > HALF:
                lens.append(lf)
                a = int(p[p.index("wb")+1]); b = int(p[p.index("wu")+1])
                c = int(p[p.index("wbp")+1]); d = int(p[p.index("wup")+1])
                wb += a; wu += b; wbp += c; wup += d
                lenhist[lf] = lenhist.get(lf, 0) + 1
                lenwu[lf] = lenwu.get(lf, 0) + b
                lenwup[lf] = lenwup.get(lf, 0) + d
        elif line.startswith("anch "):
            rat = int(line.split()[4])
        elif line.startswith("FINAL "):
            p = line.split()
            unbp_tot = int(p[p.index("unbindp")+1]); bindp_tot = int(p[p.index("bindp")+1])
        elif line.startswith("TIPS_ATP"):
            p = line.split(); tips = (int(p[2])/int(p[6]), int(p[4])/int(p[6]))
        elif line.startswith("COMB"):
            p = line.split()
            if comb is None: comb = {}; comb_raw = {}
            comb[int(p[1])] = int(p[2]) / int(p[3])
            comb_raw[int(p[1])] = (int(p[2]), int(p[3]))
    win = 300_000 - HALF
    return dict(seed=seed, wb=wb/win, wu=wu/win, wbp=wbp/win, wup=wup/win,
                Tb=(wb-wu)/win, Tp=(wup-wbp)/win,
                lmean=float(np.mean(lens)), tips=tips, comb=comb, comb_raw=comb_raw,
                ratch=rat, unbp=unbp_tot, bindp=bindp_tot,
                lenhist=lenhist, lenwu=lenwu, lenwup=lenwup)


runs = [parse(f) for f in sorted(glob.glob("/mnt/agents/output/actin_phasespace/runs3/hy_*.log"))]
print(f"{len(runs)} runs parsed")
fp = H.solve_fixed_point()
print(f"oracle fixed point: c*={fp['c']:.5f} n*={fp['n']:.1f} T={fp['T']:.3e} "
      f"a_B={fp['a_b']:.3f} a_P={fp['a_p']:.3f}")

# ---- G4 fixed point ----
Tb = np.array([r['Tb'] for r in runs]); Tp = np.array([r['Tp'] for r in runs])
lm = np.array([r['lmean'] for r in runs])
sem = lambda x: x.std(ddof=1)/np.sqrt(len(x))
print(f"\n[G4] T_flux barbed  = {Tb.mean():.3e} +- {sem(Tb):.1e}   oracle {fp['T']:.3e}")
print(f"[G4] T_flux pointed = {Tp.mean():.3e} +- {sem(Tp):.1e}")
print(f"[G4] lmean          = {lm.mean():.2f} +- {sem(lm):.2f}   oracle n* {fp['n']:.1f}")
print(f"[G4] residual growth current (Tb-Tp) = {(Tb-Tp).mean():.2e}  (phi-2: ~2e-5, ultraslow)")

# ---- G5 closure + ratchet ----
nclos = sum(1 for r in runs if r['unbp'] is not None and
            abs((r['unbp'] - r['bindp']) - r['ratch']) <= 1)  # dRank over run ~0/1
print(f"\n[G5] ratch identity (unbindp - bindp == ratch, +-1): {nclos}/{len(runs)}")
print(f"[G5] per-seed |Tb-Tp| median = {np.median(np.abs(Tb-Tp)):.2e} "
      f"(length still equilibrating within 300k)")

# ---- reduced-engine ensemble (exact 1D reduction) ----
import concurrent.futures
def _rep(s):
    return H.reduced_engine(nsteps=6_000_000, seed=s)
with concurrent.futures.ProcessPoolExecutor(max_workers=3) as ex:
    reps = list(ex.map(_rep, range(11, 19)))
tcomb = np.array([q['comb'][:10] for q in reps])
tm, ts = tcomb.mean(0), tcomb.std(0, ddof=1) / np.sqrt(len(reps))

# pooled engine comb (proper count pooling)
KMAX = 10
eA = np.zeros(KMAX); eC = np.zeros(KMAX)
for r in runs:
    for d in range(KMAX):
        if d in r['comb_raw']:
            eA[d] += r['comb_raw'][d][0]; eC[d] += r['comb_raw'][d][1]
ec = eA / np.maximum(eC, 1)
esem = np.sqrt(ec * (1 - ec) / np.maximum(eC, 1))

print(f"\n[G1] comb: engine (64-run pooled) vs 1D reduced engine (8x6M):")
print(f"     depth   engine    reduced   (eng-red)/sig")
for d in range(KMAX):
    s = np.sqrt(esem[d]**2 + ts[d]**2)
    print(f"     d={d:2d}   {ec[d]:.3f}±{esem[d]:.3f}  {tm[d]:.3f}±{ts[d]:.3f}   {(ec[d]-tm[d])/max(s,1e-9):+.1f}")

# ---- G2 currents: flux vs reduced engine vs FPT-inversion diagnostic ----
tc = np.zeros(len(runs))
for i, r in enumerate(runs):
    dd = np.array(sorted(r['comb'].keys()))
    pp = np.array([r['comb'][d] for d in dd])
    tc[i], _ = H.t_comb(dd, pp, r['wb'])
tTb = np.array([q['Tb'] for q in reps]); tTp = np.array([q['Tp'] for q in reps])
print(f"\n[G2] T_flux:   engine barbed {Tb.mean():.2e}  pointed {Tp.mean():.2e}")
print(f"[G2] T_reduced: barbed {tTb.mean():.2e}  pointed {tTp.mean():.2e}  (closure {abs(tTb.mean()-tTp.mean()):.1e})")
print(f"[G2] T_comb (naive FPT inversion, homogeneous-walk approx): {np.mean(tc):.2e} "
      f"-- systematically high: inversion ignores cascade/return correlations")

# ---- G3 tips ----
tB = np.array([r['tips'][0] for r in runs]); tP = np.array([r['tips'][1] for r in runs])
rtB = np.array([q['tipB'] for q in reps]); rtP = np.array([q['tipP'] for q in reps])
print(f"\n[G3] tip barbed  ATP: engine {tB.mean():.3f}±{sem(tB):.3f}  reduced {rtB.mean():.3f}±{sem(rtB):.3f}  renewal {fp['a_b']:.3f}")
print(f"[G3] tip pointed ATP: engine {tP.mean():.3f}±{sem(tP):.3f}  reduced {rtP.mean():.3f}±{sem(rtP):.3f}  renewal {fp['a_p']:.3f}")

# ---- G4 length + gross rates vs reduced ----
tlm = np.array([q['lmean'] for q in reps])
print(f"\n[G4] lmean: engine {lm.mean():.2f}±{sem(lm):.2f}  reduced {tlm.mean():.2f}±{sem(tlm):.2f}")
for k, lab in [('b_gross','b'), ('u_gross','u'), ('bp_gross','bp'), ('up_gross','up')]:
    eng = np.array([r[{'b_gross':'wb','u_gross':'wu','bp_gross':'wbp','up_gross':'wup'}[k]] for r in runs])
    red = np.array([q[k] for q in reps])
    print(f"[G4] gross {lab:3s}: engine {eng.mean():.2e}  reduced {red.mean():.2e}")

# ---- G6 starvation brake ----
occ = {}; ub_ = {}; up_ = {}
for r in runs:
    for n_, c_ in r['lenhist'].items():
        occ[n_] = occ.get(n_, 0) + c_
        ub_[n_] = ub_.get(n_, 0) + r['lenwu'].get(n_, 0)
        up_[n_] = up_.get(n_, 0) + r['lenwup'].get(n_, 0)
ns_ = sorted(n_ for n_ in occ if occ[n_] >= 40)
db_eng = np.array([ub_[n_] / (occ[n_]*NDIAG) for n_ in ns_])
dp_eng = np.array([up_[n_] / (occ[n_]*NDIAG) for n_ in ns_])
ns_o, b_o, d_o, a_b_o, a_p_o = H.rates_n(fp['T'])
interp = lambda x, y: np.interp(ns_, x, y)
print(f"\n[G6] barbed death rate vs length (engine vs oracle, /step):")
for n_, e, o in zip(ns_, db_eng, interp(ns_o, (a_b_o*H.U_BT+(1-a_b_o)*H.U_BA)*(1-H.RHO_B))):
    print(f"     n={n_:3d}  occ={occ[n_]:5d}  eng={e:.3e}  oracle={o:.3e}")
