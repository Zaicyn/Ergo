#!/usr/bin/env python3
"""analyze.py - M4b treadmilling cert metrics from engine/mirror logs.
Usage: python3 analyze.py log1 [log2 ...]
Computes per-log: second-half lmean, net fluxes per end, flux imbalance,
anchor-ratchet rate, tip drift along stable EE axis, anchor-target drift.
"""
import numpy as np, sys

def parse(path):
    d = dict(steps=[], kt=[], ln=[], nf=[], b=[], u=[], bp=[], up=[],
             tips=[], anch=[])
    for line in open(path):
        v = line.split()
        if line.startswith('step ') and 'lenfil' in v:
            kv = {v[i]: v[i+1] for i in range(0, len(v)-1, 2)}
            d['steps'].append(int(kv['step'])); d['kt'].append(float(kv['kt']))
            d['ln'].append(int(kv['lenfil'])); d['nf'].append(int(kv['nfree']))
            d['b'].append(int(kv['binds'])); d['u'].append(int(kv['unbinds']))
            d['bp'].append(int(kv['bindp'])); d['up'].append(int(kv['unbindp']))
        elif v and v[0] == 'run' and v[1] == 'step':   # mirror format
            kv = {v[i]: v[i+1] for i in range(1, len(v)-1, 2)}
            d['steps'].append(int(kv['step'])); d['kt'].append(float('nan'))
            d['ln'].append(int(kv['len'])); d['nf'].append(int(kv['nfree']))
            d['b'].append(int(kv['binds'])); d['u'].append(int(kv['unbinds']))
            d['bp'].append(int(kv['bindp'])); d['up'].append(int(kv['unbindp']))
        elif line.startswith('tips '):
            d['tips'].append([float(x) for x in v[1:]])
        elif line.startswith('anch '):
            d['anch'].append([float(v[1]), float(v[2]), float(v[3]), float(v[4])])
    for k in d: d[k] = np.array(d[k]) if k != 'tips' and k != 'anch' else np.array(d[k])
    return d

def metrics(d, label, frac=0.5):
    s = d['steps']; n = s[-1]
    i0 = np.searchsorted(s, frac*n)
    l2 = d['ln'][i0:]
    ns = n - s[i0]
    Tb = (d['b'][-1]-d['b'][i0])/ns
    Tp = (d['bp'][-1]-d['up'][-1])/ns
    # length trend within second half (slope per 25k chunk)
    A = np.vstack([s[i0:]-s[i0], np.ones(len(s)-i0)]).T
    lsl, _ = np.linalg.lstsq(A, l2, rcond=None)[0]
    out = dict(label=label, lmean=l2.mean(), lsem=l2.std()/np.sqrt(len(l2)/8.),
               lslope=lsl*25000, Tb=Tb, Tp=Tp)
    # tips / anchor analysis
    if len(d['tips']) and len(d['anch']):
        tips = d['tips']; anch = d['anch']
        hb = tips[:, 0:3]; tp = tips[:, 3:6]
        axyz = anch[:, 0:3]; ratch = anch[:, 3]
        # EE axis from mean over second half (stable, per run-9 observation)
        ee = hb - tp
        een = ee/np.linalg.norm(ee, axis=1, keepdims=True)
        axm = een[i0:].mean(axis=0); axm /= np.linalg.norm(axm)
        # net displacement along mean axis over second half
        dhb = (hb[-1]-hb[i0]) @ axm; dtp = (tp[-1]-tp[i0]) @ axm
        dan = (axyz[-1]-axyz[i0]) @ axm
        # ratchet rate (2nd half)
        rrate = (ratch[-1]-ratch[i0])/ns
        out.update(drift_b=dhb, drift_p=dtp, drift_a=dan, rrate=rrate,
                   span=(s[-1]-s[i0]), cos_axis=np.sum(een[1:]*een[:-1],axis=1)[i0:].mean())
    return out

if __name__ == '__main__':
    for path in sys.argv[1:]:
        d = parse(path)
        m = metrics(d, path.split('/')[-1])
        print("=== %s" % m['label'])
        print("  2nd-half lmean %.2f +- %.2f  trend %+.2f monomers/25k" % (m['lmean'], m['lsem'], m['lslope']))
        print("  net_b %+.3e  net_p %+.3e  imbalance %+.2e  (T~%g)" % (m['Tb'], m['Tp'], m['Tb']+m['Tp'], 0.5*(m['Tb']-m['Tp'])))
        if 'rrate' in m:
            print("  tip displacement along mean EE axis over %d steps: barbed %+.2f pointed %+.2f anchor-target %+.2f units"
                  % (m['span'], m['drift_b'], m['drift_p'], m['drift_a']))
            print("  anchor ratchet rate %.3e/step (PITCH drift %.3e/step)  axis stability cos %.3f"
                  % (m['rrate'], m['rrate']*0.6, m['cos_axis']))
