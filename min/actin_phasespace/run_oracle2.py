#!/usr/bin/env python3
"""Driver: two-population steady oracle. barbed sink = perfect absorber (betaB=0.3),
pointed = KONP*DT*0.5 = 2.5e-3. Fresh population (axis memory, tau=125) sees sinks
through gate alphaF; aged population gate=1.
usage: run_oracle2.py LOG OUT ALPHA_F [NSNAP]"""
import sys, json, time
import importlib.util, os
spec=importlib.util.spec_from_file_location("torc","/mnt/agents/output/actin_phasespace/transport_oracle.py")
torc=importlib.util.module_from_spec(spec); sys.modules['torc']=torc; spec.loader.exec_module(torc)
import numpy as np

LOG=sys.argv[1]; OUT=sys.argv[2]
ALPHAF=float(sys.argv[3]); NSNAP=int(sys.argv[4]) if len(sys.argv)>4 else 24
BETAB=0.3; BETAP=2.5e-3; GAMMA=1/125.0

snaps,rels=torc.parse_full(LOG)
stat=[x for x in snaps if x['step']>150500 and x['mlen']>=6]
sel=stat[::max(1,len(stat)//NSNAP)][:NSNAP]
res=[]; t0=time.time()
for i,s in enumerate(sel):
    try:
        res.append(torc.solve_snap_2pop(s,BETAB,BETAP,alpha=ALPHAF,kfp=ALPHAF,gamma=GAMMA))
    except Exception as e:
        print("fail",s['step'],repr(e),flush=True)
    if i%8==0: print(f"{i}/{len(sel)} {time.time()-t0:.0f}s",flush=True)
json.dump(dict(log=LOG,betaB=BETAB,betaP=BETAP,alphaF=ALPHAF,res=res),open(OUT,'w'))
print("wrote",OUT,len(res),f"{time.time()-t0:.0f}s")
