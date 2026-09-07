#!/usr/bin/env python3
"""Latency-kernel validation: pulse releases at engine release sites on logged
geometries; measure capture probability at each sink vs latency.
Engine targets: rho_b(<=5k)=0.442 (barbed-born -> barbed), rho_p=0.059 (pointed-born -> pointed),
cross p->b ~0.036 (phi2). usage: run_kernel.py LOG OUT [NSNAP]"""
import sys, json, time
import importlib.util
spec=importlib.util.spec_from_file_location("torc","/mnt/agents/output/actin_phasespace/transport_oracle.py")
torc=importlib.util.module_from_spec(spec); sys.modules['torc']=torc; spec.loader.exec_module(torc)
import numpy as np, scipy.sparse as sp

LOG=sys.argv[1]; OUT=sys.argv[2]
NSNAP=int(sys.argv[3]) if len(sys.argv)>3 else 10
BETAB=0.3; BETAP=2.5e-3
DT=2.0; TMAX=20000
CHECKS=[1000,5000,20000]

def kernel(snap, src_pos, sig=0.35):
    """returns dict: capture prob at sinkB/sinkP within each checkpoint latency"""
    bound,ib,ip=torc.identify_ends(snap['mons'],snap['tips'])
    th,tp=snap['tips']
    body=torc.body_mask(snap['mons'])
    sinkB=(torc.ball_mask(th,torc.RCAP)&~body).astype(float)
    sinkP=(torc.ball_mask(tp,torc.RCAP)&~body).astype(float)
    Lf=torc.fluid_laplacian(body)
    src=torc.gauss_blob(src_pos,sig)
    idx=np.where(~body.ravel())[0]
    A=(torc.kd*Lf).tocsr()[idx][:,idx]
    sB=(BETAB*sinkB).ravel()[idx]; sP=(BETAP*sinkP).ravel()[idx]
    c=src.ravel()[idx].copy()
    nsteps=int(TMAX/DT)
    out={('B',cp):0.0 for cp in CHECKS}; out.update({('P',cp):0.0 for cp in CHECKS})
    ci=0
    for i in range(nsteps):
        t=(i+1)*DT
        outB=DT*(sB*c).sum(); outP=DT*(sP*c).sum()
        c=c+DT*(A@c)-DT*(sB+sP)*c
        while ci<len(CHECKS) and t>=CHECKS[ci]-1e-9:
            ci+=1
        for cp in CHECKS:
            if abs(t-cp)<DT/2:
                pass
        # accumulate
        for cp in CHECKS:
            if t<=cp:
                out[('B',cp)]+=outB; out[('P',cp)]+=outP
    return {f"{e}_{cp}":v for (e,cp),v in out.items()}

def release_points(snap):
    bound,ib,ip=torc.identify_ends(snap['mons'],snap['tips'])
    hb,ab=bound[ib]; hp,ap=bound[ip]
    tb=hb-torc.R0*ab
    cand=[(h,a) for j,(h,a) in enumerate(bound) if j!=ib]
    qb=min(cand,key=lambda ha: np.linalg.norm(ha[0]-tb))
    cand2=[(h,a) for j,(h,a) in enumerate(bound) if j!=ip]
    qp=min(cand2,key=lambda ha: np.linalg.norm((ha[0]-torc.R0*ha[1])-hp))
    srcB_pos=qb[0]+1.65*qb[1]
    srcP_pos=(qp[0]-torc.R0*qp[1])-3.0*qp[1]
    return srcB_pos, srcP_pos

snaps,_=torc.parse_full(LOG)
stat=[x for x in snaps if x['step']>150500 and 15<=x['mlen']<=36]
sel=stat[::max(1,len(stat)//NSNAP)][:NSNAP]
res=[]
t0=time.time()
for i,s in enumerate(sel):
    pB,pP=release_points(s)
    kB=kernel(s,pB)   # barbed-born pulse
    kP=kernel(s,pP)   # pointed-born pulse
    res.append(dict(step=s['step'],n=s['mlen'],barbed_born=kB,pointed_born=kP))
    print(f"{i+1}/{len(sel)} {time.time()-t0:.0f}s",flush=True)
json.dump(dict(log=LOG,res=res),open(OUT,'w'))
print("wrote",OUT,f"{time.time()-t0:.0f}s")
