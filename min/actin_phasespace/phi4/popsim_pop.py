"""popsim_pop.py — φ4 population oracle: popsim + per-filament life history.
Pre-registered corner predictions in POP_ORACLE.md. N_tot=60, V=1728,
dissolve always (homogeneous population). Corner ν = NU0*(c/C0)**PNU.
"""
import random
from collections import deque
from popsim import SMOL, V, DT, KHYD, KOFFB, KOFFP, PSPLIT, Eof

NU0  = 4.86e-4     # measured corner nucleation rate (NUCLEATION_LAW.md)
C0   = 0.0212      # concentration the corner was measured at
PNU  = 2.6         # effective exponent of nu(c) (measured 2.3-2.9)
KNUC_LIN = NU0 / C0

class FilP:
    __slots__ = ('bits','born_t','max_n')
    def __init__(self, n, t):
        self.bits = deque([1]*n); self.born_t = t; self.max_n = n


def run_pop(N_tot=60, t_max=2000000, seed=77031, t_burn=400000,
             nuc_law=('linear', KNUC_LIN), record_every=25000):
    """Population oracle with life-history. dissolve=True always (homogeneous)."""
    rng = random.Random(seed)
    m = N_tot; fils = []; t = 0.0
    rec = dict(n_sum=0., c_sum=0., tj=0., bb=0, bp=0, ub=0, up=0,
               atp_b_sum=0., atp_p_sum=0., tipw=0., nf_sum=0.,
               births=0, deaths=0, ncount={}, nfcount={})
    nuc_times=[]; death_log=[]; last_nuc_t=None
    def nuc_rate(c):
        kind, par = nuc_law
        if kind=='linear': return par*c
        return par*(c/C0)**PNU if c>0 else 0.0   # ('corner', NU0)
    while t < t_max:
        c = m/V
        ev=[]
        for i,f in enumerate(fils):
            n=len(f.bits)
            kon = Eof(n)*SMOL*c
            ev.append((kon,'bb',i)); ev.append((PSPLIT*kon,'bp',i))
            ev.append((KOFFB[f.bits[-1]],'ub',i)); ev.append((KOFFP[f.bits[0]],'up',i))
            ev.append((n*KHYD,'hy',i))
        if m>=3: ev.append((nuc_rate(c),'nu',-1))
        R=sum(r for r,_,_ in ev)
        if R<=0: break
        t += rng.expovariate(R); x=rng.random()*R; acc=0.
        for r,kind,i in ev:
            acc+=r
            if x<=acc: break
        stat = t>t_burn
        w = 1.0/R if stat else 0.0
        if kind=='bb':
            fils[i].bits.append(1); m-=1
            fils[i].max_n=max(fils[i].max_n,len(fils[i].bits))
            if stat: rec['bb']+=1
        elif kind=='bp':
            fils[i].bits.appendleft(1); m-=1
            fils[i].max_n=max(fils[i].max_n,len(fils[i].bits))
            if stat: rec['bp']+=1
        elif kind=='ub':
            f=fils[i]; m+=1
            if stat: rec['ub']+=1
            f.bits.pop()
            if len(f.bits)<3:
                m+=len(f.bits); fils.pop(i)
                if stat: rec['deaths']+=1
                death_log.append((f.born_t,t,f.max_n))
        elif kind=='up':
            f=fils[i]; m+=1
            if stat: rec['up']+=1
            f.bits.popleft()
            if len(f.bits)<3:
                m+=len(f.bits); fils.pop(i)
                if stat: rec['deaths']+=1
                death_log.append((f.born_t,t,f.max_n))
        elif kind=='hy':
            b=fils[i].bits; b[rng.randrange(len(b))]=0
        elif kind=='nu':
            fils.append(FilP(3,t)); m-=3
            if stat: rec['births']+=1
            nuc_times.append(t)
        if stat:
            ns=[len(f.bits) for f in fils]
            rec['n_sum']+=sum(ns)*w; rec['nf_sum']+=len(ns)*w
            rec['c_sum']+=c*w; rec['tj']+=w
            rec['nfcount'][len(ns)]=rec['nfcount'].get(len(ns),0)+w
            for n in ns: rec['ncount'][n]=rec['ncount'].get(n,0)+w
            for f in fils:
                rec['atp_b_sum']+=f.bits[-1]*w; rec['atp_p_sum']+=f.bits[0]*w; rec['tipw']+=w
    T=rec['tj']
    return dict(Nf=rec['nf_sum']/T if T else 0, nbar=rec['n_sum']/rec['nf_sum'] if rec['nf_sum'] else 0,
                c=rec['c_sum']/T if T else 0, split=rec['bb']/(rec['bb']+rec['bp']) if rec['bb']+rec['bp'] else 0,
                aB=rec['atp_b_sum']/rec['tipw'] if rec['tipw'] else 0, aP=rec['atp_p_sum']/rec['tipw'] if rec['tipw'] else 0,
                births=rec['births'], deaths=rec['deaths'], ncount=rec['ncount'], nfcount=rec['nfcount'],
                nuc_times=nuc_times, death_log=death_log, t_end=t, Tstat=T)
