#!/usr/bin/env python3
"""two_end_oracle.py — phi-2 exact oracle: two-end (treadmilling) birth-death
chain for the M4b single filament.

State n = filament length in {3..N}. Both ends live:
  birth  b(n) = (KONB + KONP) * (N-n)/V     (summed capture slopes)
  death  d(n) = KB*(1-rho_b) + KP*(1-rho_p)  for n > 3   (measured returns)
The length coordinate sees only the SUMS. The treadmill current does not
enter the length chain at all — it is the imbalance-free through-current
  T = KONB*c* - KB*(1-rho_b) = -(KONP*c* - KP*(1-rho_p))
evaluated at the fixed point c* — the current-carrying stationary state.

All return probabilities (rho_b, rho_p) are MEASURED inputs (engine RET
counters), not fits. Certified against a 64 x 300k-step engine ensemble in
PHI2_RESULTS.md.
"""
import numpy as np

N, V, FLOOR = 60, 1728.0, 3
# M4b locked rates
KONB, KONP = 1.8e-2, 1.0e-2          # /step/conc (engine A/B, M4B cert)
KB, KP     = 3.3e-4, 5.0e-4          # per-step draws (KOFFB/KOFFP * DT)
# phi-2 measured returns (64-run ensemble, 5k window)
RHO_B, RHO_P = 0.442, 0.059

KBE, KPE = KB*(1-RHO_B), KP*(1-RHO_P)
KSUM = KONB + KONP
DSUM = KBE + KPE


def rates2(ksum=KSUM, dsum=DSUM):
    ns = np.arange(FLOOR, N+1)
    return ns, ksum*(N-ns)/V, np.where(ns == FLOOR, 0.0, dsum)


def stationary(ksum=KSUM, dsum=DSUM):
    ns, b, d = rates2(ksum, dsum)
    pi = np.ones(len(ns))
    for i in range(1, len(ns)):
        pi[i] = pi[i-1]*b[i-1]/d[i]
    p = pi/pi.sum()
    m = (ns*p).sum()
    return ns, p, m, ((ns-m)**2*p).sum()


def fixed_point():
    c = DSUM/KSUM
    return c, N - c*V


def treadmill_current():
    """T at the fixed point — three equivalent forms as a consistency check."""
    c, _ = fixed_point()
    Tb = KONB*c - KBE
    Tp = -(KONP*c - KPE)
    return c, Tb, Tp


def simulate(nsim, nsteps, ndiag=500, seed=7, ksum=KSUM, dsum=DSUM):
    """DTMC through the engine observation protocol (protocol-matching:
    tau_corr is huge — residual current ~2e-5/step — so never compare
    windowed engine stats against stationary analytics directly)."""
    rng = np.random.default_rng(seed)
    n = np.full(nsim, FLOOR, dtype=np.int64)
    sam = np.arange(ndiag, nsteps+1, ndiag)
    rec = np.zeros((nsim, len(sam)), dtype=np.int64)
    si = 0
    for t in range(1, nsteps+1):
        b = ksum*(N-n)/V
        d = np.where(n > FLOOR, dsum, 0.0)
        n = np.clip(n + (rng.random(nsim) < b) - (rng.random(nsim) < d), FLOOR, N)
        if si < len(sam) and t == sam[si]:
            rec[:, si] = n
            si += 1
    return sam, rec


if __name__ == "__main__":
    ns, p, m, v = stationary()
    c, Tb, Tp = treadmill_current()
    print(f"c** = {c:.4f}   L*(mean-field) = {N-c*V:.1f}")
    print(f"stationary chain: mean={m:.2f} sd={np.sqrt(v):.2f}")
    print(f"T barbed = {Tb:.3e}/step   T pointed = {Tp:.3e}/step (must agree: closure)")
    sam, rec = simulate(64, 300_000)
    win = rec[:, sam > 150_000]
    print(f"protocol-matched (64x300k): lmean={win.mean():.2f} final={rec[:,-1].mean():.1f}")
