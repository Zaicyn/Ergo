#!/usr/bin/env python3
"""Driver: run single-population transport oracle on logged geometries, dump JSON.
usage: run_oracle_batch.py LOG OUT [NSNAP]"""
import sys, json, time
import importlib.util
spec=importlib.util.spec_from_file_location("torc","/mnt/agents/output/actin_phasespace/transport_oracle.py")
torc=importlib.util.module_from_spec(spec); sys.modules['torc']=torc; spec.loader.exec_module(torc)
import numpy as np

LOG=sys.argv[1]
OUT=sys.argv[2]
NSNAP=int(sys.argv[3]) if len(sys.argv)>3 else 24
BETAB=0.3
BETAP=2.5e-3   # KONP*DT * hemisphere factor, first principles

snaps,rels=torc.parse_full(LOG)
stat=[x for x in snaps if x['step']>150500 and x['mlen']>=6]
sel=stat[::max(1,len(stat)//NSNAP)][:NSNAP]
res=[]
t0=time.time()
for i,s in enumerate(sel):
    try:
        res.append(torc.solve_snap_1pop(s, betaB=BETAB, betaP=BETAP))  # config A (certified); solve_snap_final = rejected config B wall-layer
    except Exception as e:
        print("fail",s['step'],repr(e),flush=True)
    if i%10==0: print(f"{i}/{len(sel)} {time.time()-t0:.0f}s",flush=True)
json.dump(dict(log=LOG,betaB=BETAB,betaP=BETAP,res=res),open(OUT,'w'))
print("wrote",OUT,len(res),"results",f"{time.time()-t0:.0f}s total")
