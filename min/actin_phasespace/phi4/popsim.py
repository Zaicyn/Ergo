"""popsim.py — φ4 sandbox: pool-coupled Gillespie multi-filament engine.

All rates generated from certified rung tables. Zero geometry.
Time unit = 1 engine step. State: filaments (deque of nucleotide bits,
barbed end = right) + pool m. Conservation: m + sum(len) = N_tot.
"""
import random
from collections import deque

# --- certified constants ---
SMOL = 0.01759            # 4π·D·RCAP, D per step (transport rung)
V = 1728.0                # box volume
DT = 0.005                # engine timestep (φ3: KHYD·DT = 1.5e-4)
KHYD = 0.03 * DT          # per-step hydrolysis flip prob per bound monomer
KOFFB = {1: 0.045 * DT, 0: 0.18 * DT}   # barbed unbind by tip bit (φ3)
KOFFP = {1: 0.05 * DT, 0: 0.10 * DT}    # pointed unbind by tip bit (φ3)
PSPLIT = 0.47             # pointed/barbed effective on-ratio (from split 0.68;
                          # flagged assumption: pointed recycling tracks barbed's)

# certified E(n) all-rw (KONB_LAW_RESULTS.md); flat extrapolation documented
_EBINS = [(3, 7, 0.90), (8, 11, 0.951), (12, 15, 1.153), (16, 19, 1.215),
          (20, 23, 1.468), (24, 27, 1.492), (28, 32, 1.579), (33, 37, 1.934),
          (38, 44, 1.680), (45, 200, 1.80)]

def Eof(n):
    for lo, hi, e in _EBINS:
        if lo <= n <= hi:
            return e
    return 1.80

class Fil:
    __slots__ = ('bits',)
    def __init__(self, n=3):
        self.bits = deque([1] * n)   # all ATP at birth


def run(N_tot=60, k_nuc=0.0, t_max=300000, seed=77031, n_max_fil=64,
         niche_cap=None, record_every=5000, t_burn=150000, dissolve=False,
         max_len=200, chemostat_c=None, init_n=3, niche_soft=None):
    """Gillespie engine. niche_cap: hard exclusion on filament number (C battery).
    Returns dict of stationary-half observables + trajectories."""
    rng = random.Random(seed)
    m = N_tot
    fils = []
    if k_nuc == 0.0:
        fils.append(Fil(init_n)); m -= init_n   # φ1 seed (mirror/chemostat mode)
    t = 0.0
    # accumulators (stationary half only)
    rec = dict(n_sum=0, c_sum=0, tj=0.0, bb=0, bp=0, ub=0, up=0,
               atp_b_sum=0, atp_p_sum=0, tipw=0.0, nf_sum=0,
               births=0, deaths=0, ncount={})
    nuc_waits = []          # C battery: nucleation waiting times
    last_nuc_t = None
    traj = []

    def rates():
        c = chemostat_c if chemostat_c is not None else m / V
        ev = []   # (rate, kind, fil_index)
        for i, f in enumerate(fils):
            n = len(f.bits)
            if n < max_len:          # engine NMAX cap: binds blocked at cap
                kon = Eof(n) * SMOL * c
                ev.append((kon, 'bb', i))
                ev.append((PSPLIT * kon, 'bp', i))
            if n > 3 or dissolve:      # φ1 reflecting floor (mirror mode)
                ev.append((KOFFB[f.bits[-1]], 'ub', i))
                ev.append((KOFFP[f.bits[0]], 'up', i))
            ev.append((n * KHYD, 'hy', i))
        if k_nuc > 0.0 and m >= 3 and len(fils) < n_max_fil:
            if niche_cap is not None and len(fils) >= niche_cap:
                pass                     # C-hard: attempts deleted outright
            elif niche_soft is not None:
                ev.append((k_nuc * c * max(0.0, 1.0 - len(fils) / niche_soft), 'nu', -1))
            else:
                ev.append((k_nuc * c, 'nu', -1))
        return ev

    while t < t_max:
        ev = rates()
        R = sum(r for r, _, _ in ev)
        if R <= 0.0:
            break
        t += rng.expovariate(R)
        x = rng.random() * R
        acc = 0.0
        for r, kind, i in ev:
            acc += r
            if x <= acc:
                break
        stat = t > t_burn
        if stat:
            w = 1.0 / R   # expected dwell — weight observables by dwell
        # fire
        if kind == 'bb':
            fils[i].bits.append(1); m -= 1
            if stat: rec['bb'] += 1
        elif kind == 'bp':
            fils[i].bits.appendleft(1); m -= 1
            if stat: rec['bp'] += 1
        elif kind == 'ub':
            f = fils[i]; m += 1
            if stat: rec['ub'] += 1
            f.bits.pop()
            if len(f.bits) < 3:
                m += len(f.bits); fils.pop(i)
                if stat: rec['deaths'] += 1
        elif kind == 'up':
            f = fils[i]; m += 1
            if stat: rec['up'] += 1
            f.bits.popleft()
            if len(f.bits) < 3:
                m += len(f.bits); fils.pop(i)
                if stat: rec['deaths'] += 1
        elif kind == 'hy':
            b = fils[i].bits
            j = rng.randrange(len(b))
            b[j] = 0
        elif kind == 'nu':
            fils.append(Fil(3)); m -= 3
            if stat:
                rec['births'] += 1
                if last_nuc_t is not None:
                    nuc_waits.append(t - last_nuc_t)
                last_nuc_t = t
        if stat:
            ns = [len(f.bits) for f in fils]
            rec['n_sum'] += sum(ns) * w
            rec['nf_sum'] += len(ns) * w
            rec['c_sum'] += (m / V) * w
            rec['tj'] += w
            for n in ns:
                rec['ncount'][n] = rec['ncount'].get(n, 0) + w
            for f in fils:
                rec['atp_b_sum'] += f.bits[-1] * w
                rec['atp_p_sum'] += f.bits[0] * w
                rec['tipw'] += w
            if t // record_every != (t - 1) // record_every:
                traj.append((t, len(fils), sum(ns), m))
    T = rec['tj']
    out = dict(
        Nf=rec['nf_sum'] / T if T else 0.0,
        nbar=rec['n_sum'] / rec['nf_sum'] if rec['nf_sum'] else 0.0,
        c=rec['c_sum'] / T if T else 0.0,
        split=rec['bb'] / (rec['bb'] + rec['bp']) if rec['bb'] + rec['bp'] else 0.0,
        jb=(rec['bb'] - rec['ub']) / (T * max(rec['nf_sum'] / T, 1e-12)) if T else 0.0,
        aB=rec['atp_b_sum'] / rec['tipw'] if rec['tipw'] else 0.0,
        aP=rec['atp_p_sum'] / rec['tipw'] if rec['tipw'] else 0.0,
        births=rec['births'], deaths=rec['deaths'],
        ncount=rec['ncount'], nuc_waits=nuc_waits, traj=traj,
        t_end=t)
    return out
