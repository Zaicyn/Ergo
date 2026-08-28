#!/usr/bin/env python3
"""assimilation_gradient.py — test the HGT assimilation prediction:
fresh mobile genes should be dialect-neutral (z~0); long-resident ones should
approach host userspace z. Age proxy = codon-usage anomaly (chi2 distance to
host 64-codon frequency) and GC3 deviation (two independent proxies).
Reads {prefix}_codons.bin / {prefix}_genes.tab from output/ then upload/.
Verified: pooled z reproduces the 10-genome Tier-2 panel."""
import numpy as np, os, re
from collections import defaultdict
from scipy.stats import spearmanr

UP='/mnt/agents/upload'; OUT='/mnt/agents/output'
BASES='ATGC'
CODONS=[a+b+c for a in BASES for b in BASES for c in BASES]
_std = {
 'TTT':'F','TTC':'F','TTA':'L','TTG':'L','CTT':'L','CTC':'L','CTA':'L','CTG':'L',
 'ATT':'I','ATC':'I','ATA':'I','ATG':'M','GTT':'V','GTC':'V','GTA':'V','GTG':'V',
 'TCT':'S','TCC':'S','TCA':'S','TCG':'S','CCT':'P','CCC':'P','CCA':'P','CCG':'P',
 'ACT':'T','ACC':'T','ACA':'T','ACG':'T','GCT':'A','GCC':'A','GCA':'A','GCG':'A',
 'TAT':'Y','TAC':'Y','TAA':'*','TAG':'*','CAT':'H','CAC':'H','CAA':'Q','CAG':'Q',
 'AAT':'N','AAC':'N','AAA':'K','AAG':'K','GAT':'D','GAC':'D','GAA':'E','GAG':'E',
 'TGT':'C','TGC':'C','TGA':'*','TGG':'W','CGT':'R','CGC':'R','CGA':'R','CGG':'R',
 'AGT':'S','AGC':'S','AGA':'R','AGG':'R','GGT':'G','GGC':'G','GGA':'G','GGG':'G'}
AA=dict(_std); AA4=dict(_std); AA4['TGA']='W'
W={i:(1/3)*np.sin(5*2*np.pi*(i%32)/32)*(1 if i//32==0 else -1) for i in range(64)}
COMP=np.array([1,0,3,2])  # A<->T, G<->C
MOB=re.compile(r'transposase|integrase|resolvase|insertion sequence|IS[0-9]'
               r'|phage|prophage|invertase|recombinase',re.I)

def find(prefix, kind):
    for d in (OUT, UP):
        for f in os.listdir(d):
            if f.startswith(f"{prefix}_{kind}"): return os.path.join(d,f)
    return None

def revcomp_idx(idx):
    b1=(idx//16)%4; b2=(idx//4)%4; b3=idx%4
    return ((COMP[b3]*4+COMP[b2])*4+COMP[b1])

def base_at(stream,p):
    b=stream[p//3]; d=2-(p%3)
    return (b//(4**d))%4

def gene_codons_bp(stream,s1,e1,strand):
    s,e=s1-1,e1-1
    idx=[base_at(stream,t)*16+base_at(stream,t+1)*4+base_at(stream,t+2)
         for t in range(s,e-1,3)]
    if strand=='-': idx=[revcomp_idx(i) for i in idx[::-1]]
    return np.array(idx,dtype=np.uint8)

def families(aa_map):
    fam=defaultdict(list)
    for c in CODONS: fam[aa_map[c]].append(c)
    return fam

def clean(seg,aa_map):
    if len(seg)<10: return False
    aas=[aa_map[CODONS[i]] for i in seg]
    return aas[0]=='M' and aas[-1]=='*' and '*' not in aas[:-1]

def gene_z(seg,aa_map,fams):
    obs=mu=var=0.0
    counts=defaultdict(int)
    for i in seg: counts[CODONS[i]]+=1
    for c,n in counts.items():
        aa=aa_map[c]
        if aa=='*': continue
        fw=[W[CODONS.index(x)] for x in fams[aa]]
        obs+=n*W[CODONS.index(c)]; mu+=n*np.mean(fw); var+=n*np.var(fw)
    return None if var<=0 else (obs-mu)/np.sqrt(var)

def analyze(prefix,table4=False):
    bp,tp=find(prefix,'codons'),find(prefix,'genes')
    if not bp or not tp: return None
    stream=np.fromfile(bp,dtype=np.uint8)
    rows=[ln.rstrip('\n').split('\t') for ln in open(tp)]
    aa_map=AA4 if table4 else AA; fams=families(aa_map)
    genes=[]; host_counts=np.zeros(64)
    for p in rows[2:]:
        if len(p)<8: continue
        seg=gene_codons_bp(stream,int(p[1]),int(p[2]),p[3])
        if not clean(seg,aa_map): continue
        z=gene_z(seg,aa_map,fams)
        if z is None: continue
        for i in seg: host_counts[i]+=1
        genes.append(dict(name=p[6],prod=p[7],seg=seg,z=z,
                          mobile=bool(MOB.search(p[7]))))
    return genes,host_counts

def run(prefix,table4=False):
    r=analyze(prefix,table4)
    if not r: return None
    genes,hc=r; hf=hc/hc.sum()
    mob=[g for g in genes if g['mobile']]
    user=[g for g in genes if not g['mobile']]
    if len(mob)<9: return None
    allc=np.concatenate([g['seg'] for g in genes])
    host_gc3=float(np.mean([(i%4)>=2 for i in allc]))
    uz=float(np.mean([g['z'] for g in user])); sgn=np.sign(uz)
    out={'n_mob':len(mob),'user_z':uz}
    for proxy in ('chi2','gc3'):
        for g in mob:
            c=np.zeros(64)
            for i in g['seg']: c[i]+=1
            f=c/c.sum()
            g['chi2']=float(np.sum((f-hf)**2/(hf+1e-12)))
            g['gc3']=float(np.mean([(i%4)>=2 for i in g['seg']]))
        x=np.array([g['chi2'] if proxy=='chi2' else abs(g['gc3']-host_gc3) for g in mob])
        y=np.array([sgn*g['z'] for g in mob])
        rho,p=spearmanr(x,y)
        mob_s=sorted(mob,key=lambda g:-(g['chi2'] if proxy=='chi2'
                                        else abs(g['gc3']-host_gc3)))
        k=max(1,len(mob_s)//3)
        bins=[mob_s[:k],mob_s[k:2*k],mob_s[2*k:]]
        out[proxy]={'rho':float(rho),'p':float(p),
                    'terciles':[float(np.mean([g['z'] for g in b])) for b in bins]}
    return out

if __name__=='__main__':
    panel=[('buc',0),('eco',0),('syn3',1),('strep',0),('pseudo',0),
           ('mja',0),('sso',0),('hvo',0),('pfu',0),('tth',0)]
    for pre,t4 in panel:
        r=run(pre,t4)
        if not r:
            print(f"{pre:7s} insufficient mobile genes"); continue
        print(f"{pre:7s} n={r['n_mob']:3d} userspace_z={r['user_z']:+.2f}")
        for proxy in ('chi2','gc3'):
            d=r[proxy]
            t=d['terciles']
            print(f"  {proxy:5s} terciles(fresh->old): {t[0]:+.2f} {t[1]:+.2f} "
                  f"{t[2]:+.2f}   rho={d['rho']:+.3f} p={d['p']:.3g}")
