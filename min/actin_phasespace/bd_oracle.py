#!/usr/bin/env python3
"""bd_oracle.py — phi-1 exact oracle: birth-death chain for the M4a single
filament with pool-depletion feedback.

State n = filament length in {FLOOR..N}; FLOOR=3 (seeded-assay MLEN floor,
unbind blocked). Per-step birth b(n) = KAPPA*(N-n)/V (density-dependent,
V = LBOX^3 = 1728); per-step death d(n) = koff for n > FLOOR (reflecting
floor). Effective death d_eff = KOFF*DT*(1 - P_fast) absorbs fast
return-capture (released monomer rebinds within ~1k steps), which the
chain cannot resolve spatially. P_fast is a MEASURED oracle input
(engine RET counters), not a fit.

Certified regime (phi-1): straight filament, contour < LBOX (n <~ 20).
Beyond that, conformational feedback (coil concentrates gas at the tip)
raises b by ~1.7-1.9x — a hidden second coordinate. See PHI1_RESULTS.md.
"""
import numpy as np

N, V, FLOOR = 60, 1728.0, 3
KAPPA   = 1.73e-2     # /step/conc, isolated calibration (noisy, +-30%)
KOFF    = 0.09        # nominal; per-step draw = KOFF*DT
DT      = 0.005
KOFF_STEP = KOFF*DT   # 4.5e-4


def rates(koff, kappa=KAPPA, N=N):
    ns = np.arange(FLOOR, N+1)
    b = kappa*(N-ns)/V
    d = np.where(ns == FLOOR, 0.0, koff)
    return ns, b, d


def stationary(koff, **kw):
    """Exact stationary distribution; returns (ns, p, mean, var)."""
    ns, b, d = rates(koff, **kw)
    pi = np.ones(len(ns))
    for i in range(1, len(ns)):
        pi[i] = pi[i-1]*b[i-1]/d[i]
    p = pi/pi.sum()
    m = (ns*p).sum()
    return ns, p, m, ((ns-m)**2*p).sum()


def mfpt(koff, start, target, **kw):
    """Exact mean first passage start -> target (steps), floor reflecting."""
    ns, b, d = rates(koff, **kw)
    pi = np.ones(len(ns))
    for i in range(1, len(ns)):
        pi[i] = pi[i-1]*b[i-1]/d[i]
    T = 0.0
    for k in range(start-FLOOR, target-FLOOR):
        T += pi[:k+1].sum()/(b[k]*pi[k])
    return T


def ruin_prob(koff, start, target, **kw):
    """P(hit FLOOR before target | start) — gambler's ruin, state-dependent."""
    ns, b, d = rates(koff, **kw)
    gam = [1.0]
    for k in range(1, target-FLOOR):
        gam.append(gam[-1]*d[k]/b[k])
    gam = np.array(gam)
    return 1.0 - gam[:start-FLOOR].sum()/gam.sum()


def fpt_survival(koff, start, target, tgrid, **kw):
    """Exact first-passage survival S(t) = P(T > t) via DTMC eigendecomposition
    on the transient subspace {FLOOR..target-1}. Row-convention correct:
    S(t) = (1^T V) diag(lam^t) (V^{-1} e_start)."""
    K = target - FLOOR
    ns = np.arange(FLOOR, target)
    b = KAPPA*(N-ns)/V if 'kappa' not in kw else kw['kappa']*(N-ns)/V
    d = np.where(ns == FLOOR, 0.0, koff)
    Q = np.zeros((K, K))
    for i in range(K):
        Q[i, i] = 1.0-b[i]-d[i]
        if i+1 < K:
            Q[i, i+1] = b[i]
        if i-1 >= 0:
            Q[i, i-1] = d[i]
    lam, VV = np.linalg.eig(Q.T)
    e = np.zeros(K)
    e[start-FLOOR] = 1.0
    coef = (np.ones(K) @ VV) * np.linalg.solve(VV, e)
    return np.array([np.sum(coef*lam**t).real for t in tgrid])


def simulate(koff, nsim, nsteps, ndiag=500, seed=42, **kw):
    """DTMC simulation of the chain through the engine's observation protocol
    (NDIAG sampling). Use for protocol-matched comparisons — the stationary
    sd is strongly window-biased because tau_corr ~ 1/(KAPPA/V) ~ 100k steps."""
    rng = np.random.default_rng(seed)
    n = np.full(nsim, FLOOR, dtype=np.int64)
    sam = np.arange(ndiag, nsteps+1, ndiag)
    rec = np.zeros((nsim, len(sam)), dtype=np.int64)
    si = 0
    for t in range(1, nsteps+1):
        b = KAPPA*(N-n)/V if 'kappa' not in kw else kw['kappa']*(N-n)/V
        d = np.where(n > FLOOR, koff, 0.0)
        up = rng.random(nsim) < b
        dn = rng.random(nsim) < d
        n = np.clip(n + up.astype(np.int64) - dn.astype(np.int64), FLOOR, N)
        if si < len(sam) and t == sam[si]:
            rec[:, si] = n
            si += 1
    return sam, rec


if __name__ == "__main__":
    # phi-1 reference numbers (64-run engine ensemble gates)
    P_FAST = 0.364                       # measured, engine RET counters
    D_EFF = KOFF_STEP*(1.0-P_FAST)       # 2.86e-4
    ns, p, m, v = stationary(D_EFF)
    print(f"d_eff={D_EFF:.3e}  stationary mean={m:.2f} sd={np.sqrt(v):.2f} Fano={v/m:.2f}")
    for s, t in [(3, 10), (3, 15), (3, 20), (10, 15), (15, 20)]:
        print(f"MFPT {s}->{t}: {mfpt(D_EFF, s, t):10.0f} steps")
    tg = np.arange(0, 200001, 500)
    for s, t in [(10, 15), (15, 20)]:
        S = fpt_survival(D_EFF, s, t, tg)
        cdf = 1-S
        print(f"FPT {s}->{t}: median={tg[np.searchsorted(cdf,.5)]/1000:.1f}k")
