#!/usr/bin/env python3
# analyze.py - parse engine + mirror logs, compute phenomenon statistics.
import numpy as np, glob, re, sys

def parse_log(path, kind):
    """kind: 'engine' or 'mirror'. Returns dict of stats."""
    steps, lens, natps, kts, nucts = [], [], [], [], []
    final = {}; term = {}; caps = {}
    for line in open(path):
        t = line.split()
        if not t: continue
        if t[0] == 'step' or (t[0] == 'run' and t[1] == 'step'):
            if kind == 'engine':
                # step N kt X ewca .. ebond .. efil .. lenfil L nfree F natp A nuct U ...
                steps.append(int(t[1]))
                kts.append(float(t[3]))
                lens.append(int(t[11]))
                natps.append(int(t[15]))
                nucts.append(int(t[17]))
            else:
                # run step N kt X lenfil L nfree F natp A nuct U ...
                steps.append(int(t[2]))
                kts.append(float(t[4]))
                lens.append(int(t[6]))
                natps.append(int(t[10]))
                nucts.append(int(t[12]))
        elif t[0] == 'FINAL' or (t[0] == 'run' and t[1] == 'FINAL'):
            d = dict(zip(t[1::2], t[2::2]))
            final = d
        elif t[0] == 'TERMSTATS' or (t[0] == 'run' and t[1] == 'TERMSTATS'):
            d = dict(zip(t[2::2], t[3::2])) if t[0] == 'run' else dict(zip(t[1::2], t[2::2]))
            term = d
        elif t[0] == 'CAP' or (t[0] == 'run' and t[1] == 'CAP'):
            off = 1 if t[0] == 'run' else 0
            caps[int(t[off+1])] = (int(t[off+2]), float(t[off+3]))
    steps = np.array(steps); lens = np.array(lens); natps = np.array(natps)
    kts = np.array(kts); nucts = np.array(nucts)
    return dict(steps=steps, lens=lens, natps=natps, kts=kts, nucts=nucts,
                final=final, term=term, caps=caps)

def dwell_times(steps, lens):
    """mean dwell (in steps) per visit to a length level before leaving it."""
    dwells = []
    if len(lens) == 0: return 0.0, 0
    run = 1
    for i in range(1, len(lens)):
        if lens[i] == lens[i-1]:
            run += 1
        else:
            dwells.append(run); run = 1
    dwells.append(run)
    dwells = np.array(dwells)
    dstep = steps[1] - steps[0] if len(steps) > 1 else 500
    return float(np.mean(dwells) * dstep), len(dwells)

def report(name, r, nsteps):
    half = r['steps'] > nsteps // 2
    L = r['lens'][half]; A = r['natps'][half]; KT = r['kts'][half]
    nuct = r['nucts'][half]
    lm = float(np.mean(L)); lv = float(np.var(L))
    dw, ndw = dwell_times(r['steps'][half], r['lens'][half])
    tm = r['term']
    elig = float(tm.get('elig', 1)); atpterm = float(tm.get('atpterm', 0))
    uat = float(tm.get('unb_atp', 0)); uad = float(tm.get('unb_adp', 0))
    patp = atpterm / max(elig, 1)
    keff = (uat + uad) / max(elig, 1)
    kt_nom, ka_nom, h_nom = 0.045*0.005, 0.18*0.005, 0.03*0.005
    keff_nom = patp * kt_nom + (1 - patp) * ka_nom
    r_atp = uat / max(atpterm, 1); r_adp = uad / max(elig - atpterm, 1)
    captot = sum(f for d, (c, f) in sorted(r['caps'].items()))
    print('%-28s lmean %6.2f  lvar %6.2f  CV %.3f  natp %.2f  cap %.2f  P(atpterm) %.3f  koff_eff %.2e (mix-nom %.2e, ratio %.2f)  r_atp %.2e r_adp %.2e  dwell %7.0f (%d)  kt %.3f' %
          (name, lm, lv, np.sqrt(lv)/lm, float(np.mean(A)), captot, patp,
           keff, keff_nom, keff/max(keff_nom,1e-30), r_atp, r_adp, dw, ndw,
           float(np.mean(KT))))
    return dict(lmean=lm, lvar=lv, natp=float(np.mean(A)), cap=captot,
                patp=patp, keff=keff, dwell=dw, kt=float(np.mean(KT)))

if __name__ == '__main__':
    NST = 300000
    out = {}
    for name, path, kind in [
        ('eng_hyd_s77031',  'eng_hyd300_s77031.log',  'engine'),
        ('eng_hyd_s123457', 'eng_hyd300_s123457.log', 'engine'),
        ('eng_ctrl_s77031', 'eng_ctrl82_s77031.log', 'engine'),
        ('eng_ctrl_s123457','eng_ctrl82_s123457.log','engine'),
        ('mir_hyd_s77031',  'mir_hyd300_s77031.log',  'mirror'),
        ('mir_hyd_s123457', 'mir_hyd300_s123457.log', 'mirror'),
        ('mir_ctrl_s77031', 'mir_ctrl82_s77031.log', 'mirror'),
        ('mir_ctrl_s123457','mir_ctrl82_s123457.log','mirror'),
    ]:
        try:
            r = parse_log(path, kind)
            out[name] = (report(name, r, NST), r)
        except FileNotFoundError:
            print(name, 'MISSING')
    # cap profiles side by side
    print('\ncap profiles (ATP fraction vs depth from barbed):')
    hs = [out[n][1]['caps'] for n in ('eng_hyd_s77031','eng_hyd_s123457','mir_hyd_s77031','mir_hyd_s123457') if n in out]
    names = [n for n in ('eng_hyd_s77031','eng_hyd_s123457','mir_hyd_s77031','mir_hyd_s123457') if n in out]
    print('depth ' + ' '.join('%12s' % n for n in names))
    for d in range(8):
        row = [('%5d %.3f' % (c[d][0], c[d][1]) if d in c else '-') for c in hs]
        print('%5d ' % d + ' '.join('%12s' % x for x in row))
