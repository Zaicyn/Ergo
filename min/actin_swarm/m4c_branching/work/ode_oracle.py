#!/usr/bin/env python3
# ode_oracle.py - M4c multi-chain mean-field oracle + run analysis.
# ODE (calibrated rates, exact event bookkeeping from logs):
#   dM/dt = (kon_eff*c(t) - koff_eff) * NF(t) + 3 * dB/dt
#   dB/dt = KBR_eff * NELIG(M,B) * [slots free] * [pool>=3]
#   c = (N - M)/V ; NF = 1 + B ; NELIG ~ max(0, M - NF - 6B) (regressed from log)
import numpy as np, sys, re

LBOX = 12.0; V = LBOX ** 3
N = 90; NFMAX = 8
DT = 0.005

def parse_engine_log(path):
    rows = []
    for l in open(path):
        if l.startswith('step '):
            f = l.split()
            d = dict(step=int(f[1]), kt=float(f[3]),
                     mtot=int(f[f.index('mtot')+1]), nfree=int(f[f.index('nfree')+1]),
                     nfil=int(f[f.index('nfil')+1]), nbr=int(f[f.index('nbr')+1]),
                     binds=int(f[f.index('binds')+1]), unbinds=int(f[f.index('unbinds')+1]))
            d['nelig'] = int(f[f.index('nelig')+1]) if 'nelig' in f else 0
            rows.append(d)
    return rows

def parse_mirror_log(path):
    rows = []
    for l in open(path):
        if l.startswith('run') and ' step ' in l:
            f = l.split()
            rows.append(dict(step=int(f[2]), mtot=int(f[6]), nfil=int(f[10]),
                             nbr=int(f[12]), binds=int(f[14]), unbinds=int(f[16])))
    return rows

def parse_angles(path):
    a1, a2 = [], []
    for l in open(path):
        f = l.split()
        a1.append(float(f[2])); a2.append(float(f[3]))
    return np.array(a1), np.array(a2)

if __name__ == '__main__':
    eng = parse_engine_log(sys.argv[1])
    t = np.array([r['step'] for r in eng], float)
    M = np.array([r['mtot'] for r in eng], float)
    NF = np.array([r['nfil'] for r in eng], float)
    B = np.array([r['nbr'] for r in eng], float)
    NE = np.array([r.get('nelig', 0) for r in eng], float)
    binds = eng[-1]['binds']; unbinds = eng[-1]['unbinds']
    ndiag = t[1] - t[0]
    # calibrate effective rates from event counts (mid-run window, NF>0)
    c = (N - M) / V
    kon_eff = binds / (np.sum(c * NF) * ndiag)
    koff_eff = unbinds / (np.sum(NF) * ndiag)   # approx: all live chains eligible
    print('calibrated from log: kon_eff = %.5e /step/conc, koff_eff = %.5e /step'
          % (kon_eff, koff_eff))
    # regress NELIG = a*(M - NF) + b*B  (least squares on rows with slots free)
    X = np.stack([np.maximum(M - NF, 0), B], axis=1)
    coef, *_ = np.linalg.lstsq(X, NE, rcond=None)
    print('NELIG regression: %.3f*(M-NF) %+.3f*B   (r2=%.3f)'
          % (coef[0], coef[1], 1 - np.var(NE - X @ coef) / np.var(NE)))
    # integrate ODE
    kbr_eff = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0e-3
    Mo = np.zeros_like(t); Bo = np.zeros_like(t)
    Mo[0] = M[0]; Bo[0] = 0
    for i in range(1, len(t)):
        nstep = ndiag
        M_, B_ = Mo[i-1], Bo[i-1]
        for _ in range(int(nstep)):
            nf = 1 + B_
            cc = (N - M_) / V
            nel = max(0.0, coef[0] * (M_ - nf) + coef[1] * B_)
            if B_ >= NFMAX - 1 or (N - M_) < 3:
                nel = 0.0
            db = kbr_eff * nel
            B_ += db
            M_ += (kon_eff * cc - koff_eff) * nf + 3.0 * db
        Mo[i], Bo[i] = M_, B_
    print('ODE vs engine: M(end) ode %.1f eng %.1f | B(end) ode %.2f eng %.1f'
          % (Mo[-1], M[-1], Bo[-1], B[-1]))
    w = t > t[-1] / 2
    print('second-half means: ODE M %.2f B %.2f | engine M %.2f B %.2f'
          % (Mo[w].mean(), Bo[w].mean(), M[w].mean(), B[w].mean()))
