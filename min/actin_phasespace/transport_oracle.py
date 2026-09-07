# TRANSPORT_ORACLE — screened-Poisson halo solver on engine geometries
# Lock-step oracle for the kon_b law rung: computes the barbed capture rate E(n),
# cloud share, latency kernel, and wall shadow from pure scalar diffusion on
# logged engine coil geometries. No orientations (radiation BC), no particles.
#
# Physics mapping (certified in KONB_LAW_RESULTS.md):
#   QQ>0 gate, axes decorrelate in ~125 steps << transit ~2000 steps
#     -> Collins-Kimball radiation sink, beta calibrated to >100k channel (0.0064/c)
#   filament body -> impenetrable WCA capsules (radius RB) = the "shadow"
#   releases -> deterministic teleport blobs (barbed: head(Q)+1.65a; pointed: tail(Q)-2.5a)
#   walls -> Neumann; box [0,12]^3.
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla
import math, glob, re, os

L=12.0; N=int(os.environ.get('TORC_N','64')); dx=L/N; dV=dx**3; D=1e-3; kd=D/dx**2
RCAP=1.4; R0=0.5; RB=0.55; SMOL=4*math.pi*D*RCAP
xg=(np.arange(N)+0.5)*dx
X,Y,Z=np.meshgrid(xg,xg,xg,indexing='ij')

# ---------- grid operators ----------
def build_laplacian():
    def d2(N):
        main=-2*np.ones(N); off=np.ones(N-1)
        m=sp.diags([off,main,off],[-1,0,1],shape=(N,N)).tolil()
        m[0,0]=-1.0; m[-1,-1]=-1.0
        return m.tocsr()
    D2=d2(N); I=sp.eye(N)
    return (sp.kron(sp.kron(D2,I),I)+sp.kron(sp.kron(I,D2),I)+sp.kron(sp.kron(I,I),D2)).tocsr()
LP=build_laplacian()

def ball_mask(p,R):
    return ((X-p[0])**2+(Y-p[1])**2+(Z-p[2])**2 < R**2)

def capsule_mask(p,q,R):
    """cells within R of segment p->q (vectorized coarse+refine)"""
    p=np.array(p); q=np.array(q); d=q-p; L2=d@d
    if L2<1e-12: return ball_mask(p,R)
    t=((X-p[0])*d[0]+(Y-p[1])*d[1]+(Z-p[2])*d[2])/L2
    t=np.clip(t,0,1)
    dx2=X-(p[0]+t*d[0]); dy2=Y-(p[1]+t*d[1]); dz2=Z-(p[2]+t*d[2])
    return (dx2**2+dy2**2+dz2**2) < R**2

def body_mask(monomers):
    """monomers: list of (state, head(np3), axis(np3)). Bound -> capsule tail->head, radius RB."""
    m=np.zeros((N,N,N),bool)
    for st,h,a in monomers:
        if st!=1: continue
        t=h-R0*a
        m |= capsule_mask(t,h,RB)
    return m

def gauss_blob(c,sig=0.35):
    g=np.exp(-((X-c[0])**2+(Y-c[1])**2+(Z-c[2])**2)/(2*sig**2))
    return g/(g.sum()*dV)

# ---------- steady solve ----------
def fluid_laplacian(body):
    """Neumann-folded Laplacian restricted to fluid cells (links into body dropped,
    diagonal adjusted -> no-flux at body surface)."""
    Lc=LP.tocoo()
    keep=~(body.ravel()[Lc.row]|body.ravel()[Lc.col])
    rows=Lc.row[keep]; cols=Lc.col[keep]; data=Lc.data[keep].astype(float)
    Lf=sp.coo_matrix((data,(rows,cols)),shape=LP.shape).tolil()
    off=np.asarray(Lf.sum(axis=1)).ravel()-Lf.diagonal()
    Lf.setdiag(-off)
    return Lf.tocsr()

def steady_solve(sinkB, betaB, sinkP, betaP, srcB, srcP, uB, uP, body, Lf=None):
    """sinks: bool masks; srcs: density blobs; u: source strengths (per step).
    Returns c field, J_barbed, J_pointed. Solves on fluid cells only."""
    if Lf is None: Lf=fluid_laplacian(body)
    beta=(betaB*sinkB.astype(float)+betaP*sinkP.astype(float))*(~body)
    idx=np.where(~body.ravel())[0]
    A=(kd*Lf - sp.diags(beta.ravel())).tocsr()[idx][:,idx]
    src=(uB*srcB+uP*srcP).ravel()[idx]
    c,info=sla.cg(A,-src,rtol=1e-10,maxiter=6000)
    assert info==0,info
    cf=np.zeros(N**3); cf[idx]=c; c=cf.reshape(N,N,N)
    JB=betaB*(sinkB*c).sum()*dV
    JP=betaP*(sinkP*c).sum()*dV
    return c,JB,JP

# ---------- calibration ----------
def calibrate(beta_target_fn, target, lo=1e-5, hi=0.05):
    for _ in range(30):
        mid=math.sqrt(lo*hi)
        v=beta_target_fn(mid)
        if v<target: lo=mid
        else: hi=mid
    return math.sqrt(lo*hi)

def empty_box_rate(beta,R=RCAP):
    S=ball_mask((6,6,6),R).astype(float)
    p=1e-6
    A=(kd*LP - beta*sp.diags(S.ravel())).tocsr()
    c,info=sla.cg(A,-p*np.ones(N**3),rtol=1e-10,maxiter=4000)
    c=c.reshape(N,N,N)
    J=beta*(S*c).sum()*dV
    r2=(X-6)**2+(Y-6)**2+(Z-6)**2
    cfar=c[(r2>4.5**2)&(r2<5.5**2)].mean()
    return J/cfar

# ---------- latency kernel (explicit Euler on masked operator) ----------
def latency_kernel(sinkB, betaB, src_blob, body, tmax=100000, dt=5.0, checkpoints=(1000,5000,20000,100000)):
    """pulse of unit mass at src_blob; capture flux at sinkB vs time.
    Explicit Euler, body cells reflecting (links removed)."""
    # build masked laplacian: remove links into body cells
    A=kd*LP.tolil()
    bi=np.where(body.ravel())[0]
    bset=set(bi.tolist())
    # crude: zero rows/cols for body (dirichlet c=0 inside body ~ reflecting for exterior gradient? )
    # reflecting: flux into body = 0 -> for exterior cell adjacent to body, drop that link
    # implement via: for each body-adjacent pair, remove the link weight (add back to diagonal)
    Lc=LP.tocoo()
    keep=~(body.ravel()[Lc.row]|body.ravel()[Lc.col])  # links with both ends fluid
    # build fluid-only laplacian with dropped links (Neumann at body surface)
    rows=Lc.row[keep]; cols=Lc.col[keep]; data=Lc.data[keep].astype(float)
    # diagonal correction: each fluid cell's diagonal should be -(sum of kept off-diag weights)
    Lf=sp.coo_matrix((data,(rows,cols)),shape=LP.shape).tolil()
    # recompute diagonal
    off=np.asarray(Lf.sum(axis=1)).ravel()-Lf.diagonal()
    Lf.setdiag(-off)
    Am=(kd*Lf).tocsr()
    sinkflat=(betaB*sinkB.astype(float)).ravel()
    n=N**3
    fluid=~body.ravel()
    idx=np.where(fluid)[0]
    Ared=Am[idx][:,idx]
    sred=sinkflat[idx]
    c=src_blob.ravel()[idx].copy()
    nsteps=int(tmax/dt)
    stab=dt*kd*6
    assert stab<1.0, f"explicit unstable {stab}"
    flux=np.zeros(nsteps)
    for i in range(nsteps):
        absorb=dt*sred*c
        flux[i]=absorb.sum()
        c=c+dt*(Ared@c)-absorb
    cps=np.array(checkpoints)/dt
    cum=np.cumsum(flux)
    out={cp: cum[min(int(cps[j])-1,nsteps-1)] for j,cp in enumerate(checkpoints)}
    return out, cum*1.0  # cumulative capture probability vs step index (dt units)

# ---------- geometry parsing ----------
def parse_geo(path):
    """yields per-DIAG: dict(step, mlen, monomers=[(st,head,axis)], barb, pnt)"""
    snaps=[]; cur=None
    tips={}
    for line in open(path):
        f=line.split()
        if line.startswith('geo '):
            cur=dict(step=int(f[1]),mlen=int(f[2]),mons=[])
            snaps.append(cur)
        elif line.startswith('gm ') and cur is not None:
            st=int(f[2]); h=np.array([float(f[3]),float(f[4]),float(f[5])])
            a=np.array([float(f[6]),float(f[7]),float(f[8])])
            cur['mons'].append((st,h,a))
        elif line.startswith('tips '):
            tips[int(f[0:0] or 0)]=None  # placeholder
    return snaps

if __name__=='__main__':
    print("grid",N,"kd",kd,"stab dt<",1/(6*kd))
    b=calibrate(empty_box_rate,0.0064)
    print("beta_barbed calibrated:",b,"check:",empty_box_rate(b))


# ---------- two-population (axis-memory) solver ----------
GAMMA_AX=1/125.0

def identify_ends(mons, tips):
    th,tp=tips
    bound=[(h,a) for st,h,a in mons if st==1]
    ib=int(np.argmin([np.linalg.norm(h-th) for h,a in bound]))
    ip=int(np.argmin([np.linalg.norm((h-R0*a)-tp) for h,a in bound]))
    return bound,ib,ip

def screened_solve(Lf, body, diag_field, src_field):
    idx=np.where(~body.ravel())[0]
    A=(kd*Lf - sp.diags(diag_field.ravel())).tocsr()[idx][:,idx]
    rhs=-src_field.ravel()[idx]
    c,info=sla.cg(A,rhs,rtol=1e-10,maxiter=8000)
    assert info==0,info
    cf=np.zeros(N**3); cf[idx]=c
    return cf.reshape(N,N,N)

def solve_snap_2pop(snap, betaB, betaP, alpha=2.8, kfp=0.0, gamma=GAMMA_AX, uB=3.49e-4, uP=3.52e-4):
    bound,ib,ip=identify_ends(snap['mons'],snap['tips'])
    th,tp=snap['tips']
    hb,ab=bound[ib]; hp,ap=bound[ip]
    tb=hb-R0*ab
    cand=[(h,a) for j,(h,a) in enumerate(bound) if j!=ib]
    qb=min(cand,key=lambda ha: np.linalg.norm(ha[0]-tb))
    cand2=[(h,a) for j,(h,a) in enumerate(bound) if j!=ip]
    qp=min(cand2,key=lambda ha: np.linalg.norm((ha[0]-R0*ha[1])-hp))
    srcB_pos=qb[0]+1.65*qb[1]
    srcP_pos=(qp[0]-R0*qp[1])-3.0*qp[1]
    body=body_mask(snap['mons'])
    sinkB=(ball_mask(th,RCAP)&~body).astype(float)
    sinkP=(ball_mask(tp,RCAP)&~body).astype(float)
    srcB=gauss_blob(srcB_pos,0.35); srcP=gauss_blob(srcP_pos,0.35)
    Lf=fluid_laplacian(body)
    src=uB*srcB+uP*srcP
    diagF=gamma + betaB*alpha*sinkB + betaP*kfp*sinkP
    F=screened_solve(Lf,body,diagF,src)
    diagA=betaB*sinkB+betaP*sinkP
    A=screened_solve(Lf,body,diagA,gamma*F)
    c=F+A
    JB=betaB*(sinkB*(alpha*F+A)).sum()*dV
    JP=betaP*(sinkP*(kfp*F+A)).sum()*dV
    cglob=c.sum()*dV/1728
    E=JB/(cglob*SMOL)
    return dict(E=float(E),JB=float(JB),JP=float(JP),split=float(JB/(JB+JP)),cglob=float(cglob),
                n=snap['mlen'],step=snap['step'],ee=float(np.linalg.norm(th-tp)),
                res=float(cglob*1728/(uB+uP)))

def parse_full(path):
    snaps=[]; cur=None; rels=[]
    for line in open(path):
        f=line.split()
        if line.startswith('geo '):
            cur=dict(step=int(f[1]),mlen=int(f[2]),mons=[]); snaps.append(cur)
        elif line.startswith('gm ') and cur is not None:
            cur['mons'].append((int(f[2]), np.array([float(f[3]),float(f[4]),float(f[5])]),
                                np.array([float(f[6]),float(f[7]),float(f[8])])))
        elif line.startswith('tips ') and snaps:
            snaps[-1]['tips']=(np.array([float(f[1]),float(f[2]),float(f[3])]),
                               np.array([float(f[4]),float(f[5]),float(f[6])]))
        elif line.startswith('rel '):
            rels.append(dict(step=int(f[1]),m=int(f[2]),end=int(f[3]),
                             pos=np.array([float(f[4]),float(f[5]),float(f[6])]),
                             ax=np.array([float(f[7]),float(f[8]),float(f[9])])))
    return snaps, rels

def _worker(args):
    snap,betaB,betaP,alpha,kfp,gamma=args
    return solve_snap_2pop(snap,betaB,betaP,alpha,kfp,gamma)

def batch(snaps, betaB, betaP, alpha=2.8, kfp=0.0, gamma=GAMMA_AX, workers=3):
    import concurrent.futures as cf
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_worker, [(s,betaB,betaP,alpha,kfp,gamma) for s in snaps]))


def solve_snap_1pop(snap, betaB, betaP, uB=3.49e-4, uP=3.52e-4):
    """single-population: barbed = perfect absorber (saturated acceptance + axis
    redraws every ~125 steps << dwell), pointed = chemistry-limited KONP*DT*0.5."""
    bound,ib,ip=identify_ends(snap['mons'],snap['tips'])
    th,tp=snap['tips']
    hb,ab=bound[ib]; hp,ap=bound[ip]
    tb=hb-R0*ab
    cand=[(h,a) for j,(h,a) in enumerate(bound) if j!=ib]
    qb=min(cand,key=lambda ha: np.linalg.norm(ha[0]-tb))
    cand2=[(h,a) for j,(h,a) in enumerate(bound) if j!=ip]
    qp=min(cand2,key=lambda ha: np.linalg.norm((ha[0]-R0*ha[1])-hp))
    srcB_pos=qb[0]+1.65*qb[1]
    srcP_pos=(qp[0]-R0*qp[1])-3.0*qp[1]
    body=body_mask(snap['mons'])
    sinkB=(ball_mask(th,RCAP)&~body).astype(float)
    sinkP=(ball_mask(tp,RCAP)&~body).astype(float)
    srcB=gauss_blob(srcB_pos,0.35); srcP=gauss_blob(srcP_pos,0.35)
    Lf=fluid_laplacian(body)
    src=uB*srcB+uP*srcP
    c=screened_solve(Lf,body,betaB*sinkB+betaP*sinkP,src)
    JB=betaB*(sinkB*c).sum()*dV
    JP=betaP*(sinkP*c).sum()*dV
    cglob=c.sum()*dV/1728
    return dict(E=float(JB/(cglob*SMOL)),JB=float(JB),JP=float(JP),
                split=float(JB/(JB+JP)),cglob=float(cglob),n=snap['mlen'],step=snap['step'],
                res=float(cglob*1728/(uB+uP)),ee=float(np.linalg.norm(th-tp)))

def _worker1(args):
    snap,betaB,betaP=args
    return solve_snap_1pop(snap,betaB,betaP)


# ---------- final calibrated version ----------
# WCA walls exclude bead centers ~0.55 from the box faces; grid Dirichlet staircase
# at N=48+wall-layer lands on the continuum perfect-absorber rate WITH D_rel tip
# motion (empty-box: 0.02484 vs 4*pi*1.42e-3*1.4=0.02498). betaB=1.0, R_sink=RCAP.
WALLLAYER=(X<0.55)|(X>11.45)|(Y<0.55)|(Y>11.45)|(Z<0.55)|(Z>11.45)

def solve_snap_final(snap, betaB=1.0, betaP=2.5e-3, uB=3.49e-4, uP=3.52e-4):
    bound,ib,ip=identify_ends(snap['mons'],snap['tips'])
    th,tp=snap['tips']
    hb,ab=bound[ib]; hp,ap=bound[ip]
    tb=hb-R0*ab
    cand=[(h,a) for j,(h,a) in enumerate(bound) if j!=ib]
    qb=min(cand,key=lambda ha: np.linalg.norm(ha[0]-tb))
    cand2=[(h,a) for j,(h,a) in enumerate(bound) if j!=ip]
    qp=min(cand2,key=lambda ha: np.linalg.norm((ha[0]-R0*ha[1])-hp))
    srcB_pos=qb[0]+1.65*qb[1]
    srcP_pos=(qp[0]-R0*qp[1])-3.0*qp[1]
    body=body_mask(snap['mons'])|WALLLAYER
    sinkB=(ball_mask(th,RCAP)&~body).astype(float)
    sinkP=(ball_mask(tp,RCAP)&~body).astype(float)
    srcB=gauss_blob(srcB_pos,0.35); srcP=gauss_blob(srcP_pos,0.35)
    Lf=fluid_laplacian(body)
    src=uB*srcB+uP*srcP
    c=screened_solve(Lf,body,betaB*sinkB+betaP*sinkP,src)
    JB=betaB*(sinkB*c).sum()*dV
    JP=betaP*(sinkP*c).sum()*dV
    cglob=c.sum()*dV/1728
    return dict(E=float(JB/(cglob*SMOL)),JB=float(JB),JP=float(JP),
                split=float(JB/(JB+JP)),cglob=float(cglob),n=snap['mlen'],step=snap['step'],
                res=float(cglob*1728/(uB+uP)),ee=float(np.linalg.norm(th-tp)))

def _workerF(args):
    snap=args
    return solve_snap_final(snap)
