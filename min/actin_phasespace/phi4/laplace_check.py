# LAPLACE QUICK-CHECK on branched-brush geometries (brush_bra, F=0.1 arm)
# Multi-filament driver for the certified transport oracle machinery:
# per snapshot: N_f barbed Dirichlet sinks + N_f pointed radiation sinks,
# teleport-blob sources at certified release sites, wall layer, then
# per-tip flux split (engaged vs behind) + pool + supply-side v ceiling.
import os, sys, math, subprocess
os.environ['TORC_N'] = '48'
sys.path.insert(0, '/mnt/agents/output/actin_phasespace')
import numpy as np
import transport_oracle as TO

LOG = '/tmp/bra_geo.log'
raw = subprocess.run(['tr','-d','\\0'], stdin=open(LOG,'rb'), capture_output=True).stdout.decode('utf-8','ignore')

# ---- parse snapshots ----
snaps = {}   # step -> dict(gm=[], ftd={}, xp=None)
order = []
cur = None
for l in raw.splitlines():
    if l.startswith('census '):
        cur = int(l.split()[1]); snaps[cur] = dict(gm=[], ftd={}); order.append(cur)
    elif l.startswith('gm ') and cur is not None:
        f = l.split()
        snaps[cur]['gm'].append((int(f[2]), np.array([float(f[3]),float(f[4]),float(f[5])]),
                                 np.array([float(f[6]),float(f[7]),float(f[8])])))
    elif l.startswith('ftd ') and cur is not None:
        f = l.split()
        F = int(f[2])
        snaps[cur]['ftd'][F] = dict(barb=np.array([float(f[3]),float(f[4]),float(f[5])]),
                                    ba=np.array([float(f[6]),float(f[7]),float(f[8])]),
                                    pnt=np.array([float(f[9]),float(f[10]),float(f[11])]),
                                    ln=int(f[12]))
    elif l.startswith('pstn '):
        f = l.split(); st = int(f[1])
        if st in snaps: snaps[st]['xp'] = float(f[3])

# engine rates from this run's FINAL line
for l in raw.splitlines():
    if l.startswith('FINAL '):
        f = l.split()
        binds, unb, bindp, unbp = int(f[12]), int(f[14]), int(f[16]), int(f[18])
T = 400000.0
uB_tot, uP_tot = unb/T, unbp/T
bB_tot = binds/T
cen2 = [l for l in raw.splitlines() if l.startswith('census ') and int(l.split()[1]) > 200000]
NFREE_ENGINE = sum(int(l.split()[7]) for l in cen2)/len(cen2)/1728.0
print('engine rates/step: barbed unbind %.2e  pointed unbind %.2e  barbed bind %.2e' % (uB_tot, uP_tot, bB_tot))

WALL = TO.WALLLAYER
RCAP, R0 = 1.4, 0.5

def solve_snap(snap, Dscale=1.0):
    gm = snap['gm']; ftd = snap['ftd']; xp = snap.get('xp', 11.3)
    body = TO.body_mask(gm) | WALL
    nf = len(ftd)
    uB, uP = uB_tot/max(1,nf), uP_tot/max(1,nf)
    sinkB = np.zeros(body.shape); sinkP = np.zeros(body.shape)
    src = np.zeros(body.shape)
    for F, d in ftd.items():
        sb = TO.ball_mask(d['barb'], RCAP) & ~body
        sp_ = TO.ball_mask(d['pnt'], RCAP) & ~body
        sinkB += sb.astype(float); sinkP += sp_.astype(float)
        src += uB * TO.gauss_blob(d['barb'] + 1.65*d['ba'], 0.35)
        src += uP * TO.gauss_blob(d['pnt'] - 2.5*d['ba'], 0.35)
    # Dscale: rebuild masked laplacian with scaled kd
    Lf = TO.fluid_laplacian(body)
    kd = TO.kd * Dscale
    beta = (1.0*sinkB + 2.5e-3*sinkP)*(~body)
    import scipy.sparse as sp, scipy.sparse.linalg as sla
    import scipy.sparse.csgraph as csg
    srcv = src.ravel()
    active = (beta.ravel() > 0) | (srcv > 0)
    fluid = ~body.ravel()
    keep = fluid.copy()
    # connected components of the fluid graph; drop sealed pockets
    Lsym = (Lf != 0).astype(np.int8).tocsr()
    ncomp, labels = csg.connected_components(Lsym, directed=False)
    good = np.zeros(len(labels), bool)
    for ci in range(ncomp):
        cells = labels == ci
        if (active & cells & fluid).any():
            good |= cells
    keep = fluid & good
    idx = np.where(keep)[0]
    A = (kd*Lf - sp.diags(beta.ravel()) - 1e-12*sp.eye(TO.N**3)).tocsr()[idx][:,idx]
    c, info = sla.cg(A, -srcv[idx], rtol=1e-9, maxiter=9000)
    assert info == 0, ('CG failed', info)
    cf = np.zeros(TO.N**3); cf[idx] = c; c = cf.reshape(body.shape)
    # per-tip flux
    out = []
    for F, d in ftd.items():
        sb = TO.ball_mask(d['barb'], RCAP) & ~body
        J = float(1.0*(sb*c).sum()*TO.dV)
        out.append((F, J, d['barb'][0], d['ln'], d['ba'][0], d['barb'][0] > xp - 1.0))
    cglob = float(c.sum()*TO.dV/1728.0)
    JB = float((sinkB*c).sum()*TO.dV); JP = float(2.5e-3*(sinkP*c).sum()*TO.dV)
    return out, cglob, JB, JP, xp

steps = [s for s in order if s > 200000][::50]
print('snapshots:', len(steps))
import statistics as stt
rows = {1.0: [], 1.5: []}
pool = {1.0: [], 1.5: []}
jb = {1.0: [], 1.5: []}
for s in steps:
    snap = snaps[s]
    if 'xp' not in snap or not snap['ftd']: continue
    for ds in (1.0, 1.5):
        out, cglob, JB, JP, xp = solve_snap(snap, ds)
        pool[ds].append(cglob); jb[ds].append(JB/(JB+JP))
        for F, J, bx, ln, ax, eng in out:
            rows[ds].append((J, eng, ln, ax, bx, s))

for ds in (1.0, 1.5):
    r = rows[ds]
    eng = [x for x in r if x[1]]; non = [x for x in r if not x[1]]
    print('\n== D scale %.1f (kT_eff=%.1f)' % (ds, 0.4*ds))
    print('  pool c = %.5f  (engine nfree/V = %.5f stationary half)' % (stt.mean(pool[ds]), NFREE_ENGINE))
    print('  barbed flux split JB/(JB+JP) = %.3f' % stt.mean(jb[ds]))
    if eng and non:
        print('  J per ENGAGED tip: %.3e (n=%d)   J per behind tip: %.3e (n=%d)   ratio %.2f'
              % (stt.mean(x[0] for x in eng), len(eng), stt.mean(x[0] for x in non), len(non),
                 stt.mean(x[0] for x in eng)/stt.mean(x[0] for x in non)))
        print('  engaged-tip mean len %.1f  mean a_x %.3f' % (stt.mean(x[2] for x in eng), stt.mean(x[3] for x in eng)))
    # length-resolved supply
    for lo, hi in [(3,8),(8,12),(12,16),(16,22),(22,40)]:
        sel = [x[0] for x in r if lo <= x[2] < hi]
        if sel: print('  J(n %2d-%2d): %.3e (n=%d tips)' % (lo, hi, stt.mean(sel), len(sel)))
np.save('/tmp/r17/laplace_rows.npy', rows, allow_pickle=True)
print('\nsaved /tmp/r17/laplace_rows.npy')
