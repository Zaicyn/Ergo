#!/usr/bin/env python3
"""Two-population latency kernel: fresh (axis memory, gate alphaF) aging to aged (gate 1)
at rate gamma. Fit alphaF against engine rho_b(5k)=0.442, rho_p(5k)=0.059.
usage: run_kernel2.py LOG OUT ALPHA_F [NSNAP]"""
import sys, json, time
import importlib.util
spec=importlib.util.spec_from_file_location("torc","/mnt/agents/output/actin_phasespace/transport_oracle.py")
torc=importlib.util.module_from_spec(spec); sys.modules['torc']=torc; spec.loader.exec_module(torc)
import numpy as np

LOG=sys.argv[1]; OUT=sys.argv[2]
ALPHAF=float(sys.argv[3]); NSNAP=int(sys.argv[4]) if len(sys.argv)>4 else 5
BETAB=0.3; BETAP=2.5e-3
DT=2.0; TMAX=20000; GAMMA=1/125.0
CHECKS=[1000,5000,20000]
DV=torc.dV

def kernel2(snap, src_pos, sig=0.35):
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
    F=src.ravel()[idx].copy(); Ag=np.zeros_like(F)
    nsteps=int(TMAX/DT)
    out={('B',cp):0.0 for cp in CHECKS}; out.update({('P',cp):0.0 for cp in CHECKS})
    for i in range(nsteps):
        t=(i+1)*DT
        capB=DT*(sB*(ALPHAF*F+Ag)).sum()*DV
        capP=DT*(sP*(ALPHAF*F+Ag)).sum()*DV
        for cp in CHECKS:
            if t<=cp:
                out[('B',cp)]+=capB; out[('P',cp)]+=capP
        Fnew=F+DT*(A@F)-DT*(ALPHAF*(sB+sP)+GAMMA)*F
        Ag=Ag+DT*(A@Ag)-DT*(sB+sP)*Ag+DT*GAMMA*F
        F=Fnew
    return {f"{e}_{cp}":v for (e,cp),v in out.items()}

def release_points(snap):
    bound,ib,ip=torc.identify_ends(snap['mons'],snap['tips'])
    hb,ab=bound[ib]; hp,ap=bound[ip]
    tb=hb-torc.R0*ab
    cand=[(h,a) for j,(h,a) in enumerate(bound) if j!=ib]
    qb=min(cand,key=lambda ha: np.linalg.norm(ha[0]-tb))
    cand2=[(h,a) for j,(h,a) in enumerate(bound) if j!=ip]
    qp=min(cand2,key=lambda ha: np.linalg.norm((ha[0]-torc.R0*ha[1])-hp))
    return qb[0]+1.65*qb[1], (qp[0]-torc.R0*qp[1])-3.0*qp[1]

snaps,_=torc.parse_full(LOG)
stat=[x for x in snaps if x['step']>150500 and 15<=x['mlen']<=36]
sel=stat[::max(1,len(stat)//NSNAP)][:NSNAP]
res=[]; t0=time.time()
for i,s in enumerate(sel):
    pB,pP=release_points(s)
    res.append(dict(step=s['step'],n=s['mlen'],barbed_born=kernel2(s,pB),pointed_born=kernel2(s,pP)))
    print(f"{i+1}/{len(sel)} {time.time()-t0:.0f}s",flush=True)
json.dump(dict(log=LOG,alphaF=ALPHAF,res=res),open(OUT,'w'))
print("wrote",OUT,f"{time.time()-t0:.0f}s")
