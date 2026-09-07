# Calibrate pointed-sink reactivity betaP for the brush regime.
# Target: engine's measured capture split binds/(binds+bindp) from the same run.
# Method: bisection on betaP per snapshot, CG warm-started (M4C-style measured
# renormalization, documented as a ratio vs the geo-lineage nominal 2.5e-3).
import os, sys, math, subprocess
os.environ['TORC_N'] = '48'
sys.path.insert(0, '/mnt/agents/output/actin_phasespace')
import numpy as np
import scipy.sparse as sp, scipy.sparse.linalg as sla
import transport_oracle as TO

LOG = '/tmp/bra_geo.log'
raw = subprocess.run(['tr','-d','\\0'], stdin=open(LOG,'rb'), capture_output=True).stdout.decode('utf-8','ignore')

snaps = {}; order = []; cur = None
for l in raw.splitlines():
    if l.startswith('census '):
        cur = int(l.split()[1]); snaps[cur] = dict(gm=[], ftd={}); order.append(cur)
    elif l.startswith('gm ') and cur is not None:
        f = l.split()
        snaps[cur]['gm'].append((int(f[2]), np.array([float(f[3]),float(f[4]),float(f[5])]),
                                 np.array([float(f[6]),float(f[7]),float(f[8])])))
    elif l.startswith('ftd ') and cur is not None:
        f = l.split()
        snaps[cur]['ftd'][int(f[2])] = dict(barb=np.array([float(f[3]),float(f[4]),float(f[5])]),
                                    ba=np.array([float(f[6]),float(f[7]),float(f[8])]),
                                    pnt=np.array([float(f[9]),float(f[10]),float(f[11])]),
                                    ln=int(f[12]))
    elif l.startswith('pstn '):
        f = l.split(); st = int(f[1])
        if st in snaps: snaps[st]['xp'] = float(f[3])

for l in raw.splitlines():
    if l.startswith('FINAL '):
        f = l.split()
        binds, unb, bindp, unbp = int(f[12]), int(f[14]), int(f[16]), int(f[18])
T = 400000.0
uB_tot, uP_tot = unb/T, unbp/T
TARGET = binds/(binds+bindp)
print('target split %.4f  (binds %.2e bindp %.2e per step)' % (TARGET, binds/T, bindp/T))

WALL = TO.WALLLAYER; RCAP = 1.4

XG, YG, ZG = TO.X, TO.Y, TO.Z
def hemi_ball(c, a, R):
    # cells within R of c, on the REAR side (-a hemisphere), vectorized
    r2 = (XG-c[0])**2 + (YG-c[1])**2 + (ZG-c[2])**2
    rear = ((XG-c[0])*a[0] + (YG-c[1])*a[1] + (ZG-c[2])*a[2]) < 0
    return (r2 < R*R) & rear

def build(snap):
    gm = snap['gm']; ftd = snap['ftd']
    body = TO.body_mask(gm) | WALL
    nf = len(ftd)
    uB, uP = uB_tot/max(1,nf), uP_tot/max(1,nf)
    sinkB = np.zeros(body.shape); sinkP = np.zeros(body.shape); src = np.zeros(body.shape)
    for F, d in ftd.items():
        sinkB += (TO.ball_mask(d['barb'], RCAP) & ~body).astype(float)
        sinkP += (hemi_ball(d['pnt'], d['ba'], RCAP) & ~body).astype(float)
        src += uB * TO.gauss_blob(d['barb'] + 1.65*d['ba'], 0.35)
        src += uP * TO.gauss_blob(d['pnt'] - 2.5*d['ba'], 0.35)
    Lf = TO.fluid_laplacian(body)
    return body, sinkB, sinkP, src.ravel(), Lf

def solve_split(pre, betaP, x0=None, betaB=0.57):
    body, sinkB, sinkP, srcv, Lf = pre
    beta = (betaB*sinkB + betaP*sinkP)*(~body)
    fluid = ~body.ravel()
    import scipy.sparse.csgraph as csg
    Lsym = (Lf != 0).astype(np.int8).tocsr()
    ncomp, labels = csg.connected_components(Lsym, directed=False)
    active = (beta.ravel() > 0) | (srcv > 0)
    good = np.zeros(len(labels), bool)
    for ci in range(ncomp):
        cells = labels == ci
        if (active & cells & fluid).any(): good |= cells
    idx = np.where(fluid & good)[0]
    A = (TO.kd*Lf - sp.diags(beta.ravel()) - 1e-12*sp.eye(TO.N**3)).tocsr()[idx][:,idx]
    x = x0[idx] if x0 is not None else None
    c, info = sla.cg(A, -srcv[idx], rtol=1e-9, maxiter=9000, x0=x)
    assert info == 0, info
    cf = np.zeros(TO.N**3); cf[idx] = c; c = cf.reshape(body.shape)
    JB = float(betaB*(sinkB*c).sum()*TO.dV); JP = float(betaP*(sinkP*c).sum()*TO.dV)
    cglob = float(c.sum()*TO.dV/1728.0)
    return JB/(JB+JP), cglob, cf

steps = [s for s in order if s > 200000][::50][:4]
import statistics as stt
res = []
for s in steps:
    snap = snaps[s]
    if 'xp' not in snap or not snap['ftd']: continue
    pre = build(snap)
    lo, hi = 2.5e-3, 2.5e0
    x0 = None
    for it in range(16):
        mid = math.sqrt(lo*hi)
        split, cg, x0 = solve_split(pre, mid, x0)
        if split > TARGET: lo = mid   # stronger pointed sink -> smaller barbed share
        else: hi = mid
    split, cg, _ = solve_split(pre, mid, x0)
    res.append((s, mid, split, cg))
    print('step %d: betaP_eff = %.4f (%.0fx nominal)  split %.3f  pool %.4f (engine 0.0174)' %
          (s, mid, mid/2.5e-3, split, cg), flush=True)

print('\nbetaP_eff: mean %.4f  ratio vs geo nominal 2.5e-3: %.1fx  spread %.1f-%.1f' % (
    stt.mean(r[1] for r in res), stt.mean(r[1] for r in res)/2.5e-3,
    min(r[1] for r in res)/2.5e-3, max(r[1] for r in res)/2.5e-3))
print('pool at calibration: %.4f (engine 0.0174)' % stt.mean(r[3] for r in res))
