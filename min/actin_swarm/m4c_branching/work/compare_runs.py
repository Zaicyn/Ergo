#!/usr/bin/env python3
# compare_runs.py - engine vs mirror 2-sigma comparison: total bound M,
# per-chain length distribution, branch count, angle distributions.
import numpy as np, sys

def parse_engine(path):
    rows = [l.split() for l in open(path) if l.startswith('step ')]
    t = np.array([int(r[1]) for r in rows])
    def col(k): return np.array([int(r[r.index(k) + 1]) for r in rows], float)
    M, NF, B = col('mtot'), col('nfil'), col('nbr')
    lens = [list(map(int, l.split()[4:12])) for l in open(path) if l.startswith('CHL')]
    angs = []
    for l in open(path):
        if l.startswith('ANG '):
            f = l.split()
            for v in f[4:12]:
                x = float(v)
                if x > 0:
                    angs.append(x)
    return t, M, NF, B, np.array(lens), np.array(angs)

def parse_mirror(path):
    rows = []
    for l in open(path):
        if l.startswith('run') and ' step ' in l:
            f = l.split()
            li = f.index('lens')
            rows.append((int(f[2]), int(f[f.index('mtot') + 1]), int(f[f.index('nfil') + 1]),
                         int(f[f.index('nbr') + 1]), list(map(int, f[li + 1:li + 9]))))
    t = np.array([r[0] for r in rows], float)
    M = np.array([r[1] for r in rows], float)
    NF = np.array([r[2] for r in rows], float)
    B = np.array([r[3] for r in rows], float)
    lens = np.array([r[4] for r in rows])
    return t, M, NF, B, lens

def second_half(t, x):
    w = t > t[-1] / 2
    return x[w]

def report(tag, eng_logs, mir_logs, ang_files):
    eM, eB, eL, eA = [], [], [], []
    for p in eng_logs:
        t, M, NF, B, L, A = parse_engine(p)
        eM.append(second_half(t, M)); eB.append(second_half(t, B))
        eL.append(second_half(t, L.astype(float)).reshape(-1))
        eA.append(A[A > 0])
    mM, mB, mL = [], [], []
    for p in mir_logs:
        t, M, NF, B, L = parse_mirror(p)
        mM.append(second_half(t, M)); mB.append(second_half(t, B))
        mL.append(second_half(t, L.astype(float)).reshape(-1))
    mA = []
    for p in ang_files:
        a = np.loadtxt(p)
        a = np.atleast_2d(a)
        w = a[:, 0] > a[:, 0].max() / 2
        mA.append(a[w, 2])
    eM = np.concatenate(eM); mM = np.concatenate(mM)
    eB = np.concatenate(eB); mB = np.concatenate(mB)
    eL = np.concatenate(eL); mL = np.concatenate(mL)
    eL = eL[eL > 0]; mL = mL[mL > 0]
    eA = np.concatenate(eA); mA = np.concatenate(mA)
    nE, nM = len(eng_logs), len(mir_logs)
    print('== %s: engine (%d seeds) vs mirror (%d seeds), second half of 150k ==' % (tag, nE, nM))
    def cmp(name, e, m):
        em, mm = e.mean(), m.mean()
        # per-seed SEMs -> combined; conservative: use global std/sqrt(nseeds)
        se = e.std() / np.sqrt(nE); sm = m.std() / np.sqrt(nM)
        diff = abs(em - mm); tol = 2 * np.sqrt(se ** 2 + sm ** 2)
        print('%-28s engine %8.3f (sd %6.3f) | mirror %8.3f (sd %6.3f) | diff %6.3f vs 2sig %6.3f  %s'
              % (name, em, e.std(), mm, m.std(), diff, tol, 'PASS' if diff < tol else 'FAIL'))
    cmp('total bound M', eM, mM)
    cmp('branch count B', eB, mB)
    cmp('per-chain length (all)', eL, mL)
    cmp('angle vs host axis (deg)', eA, mA)
    print('angle engine: mean %.1f sd %.1f (n=%d); mirror: mean %.1f sd %.1f (n=%d)'
          % (eA.mean(), eA.std(), len(eA), mA.mean(), mA.std(), len(mA)))
    print('chain length hist engine:', np.histogram(eL, bins=np.arange(0, 25))[0])
    print('chain length hist mirror:', np.histogram(mL, bins=np.arange(0, 25))[0])

if __name__ == '__main__':
    report('M4c branching 150k',
           ['/tmp/m4c/run_engine_77031.log', '/tmp/m4c/run_engine_88051.log'],
           ['/tmp/m4c/run_mirror_77031.log', '/tmp/m4c/run_mirror_88051.log'],
           ['/tmp/m4c/ang_77031.txt', '/tmp/m4c/ang_88051.txt'])
