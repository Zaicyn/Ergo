#!/usr/bin/env python3
"""hyd_oracle.py — phi-3 oracle: hydrolysis + age coordinate on the two-end
treadmilling chain. Closes the causal loop:

    depletion sets c  ->  rates set T  ->  T sets the age shear
    ->  hydrolysis converts the shear into the cap comb
    ->  the comb sets the effective off-rates  ->  which feed back into T

Machinery (all mean-field, zero fitted parameters — every input is either a
locked engine rate or a phi-2 MEASURED return probability):

  Tip state (renewal competition, per end):
    a = P(tip ATP). The tip is refreshed to ATP by binds (rate b_end) and by
    unbinds that EXPOSE a younger monomer (rate u_state, exposed monomer is
    ATP w.p. P_expose); it decays to ADP by hydrolysis (p_h) and by unbinds
    that expose an ADP monomer.
      a * [p_h + u_T*(1-P_expose)] = (1-a) * [b + u_A*P_expose]
    Exposure memory differs by end (this is the whole treadmill geometry):
      barbed : the monomer beneath the tip is ~1/T old   -> P2b=(1-p_h)^(1/T)
      pointed: the monomer beneath the tip transited the whole filament,
               age ~ (n-2)/T                             -> P2p=(1-p_h)^((n-2)/T) ~ 0

  Effective off-rates (state-averaged, return-corrected with phi-2 rho):
      u_B_eff = [a_B*u_BT + (1-a_B)*u_BA] * (1-RHO_B)
      u_P_eff = [a_P*u_PT + (1-a_P)*u_PA] * (1-RHO_P)

  Fixed point (through-current state, inherits phi-2 closure form):
      T = KONB*c - u_B_eff = u_P_eff - KONP*c ,   n = N - c*V

  Comb (cap profile vs depth d from barbed tip, d=0 IS the tip):
    A buried monomer's depth performs a drifted random walk: +1 per barbed
    bind (gross rate b), -1 per barbed unbind (gross rate u). Its AGE given
    depth d is the first-passage time of that walk to net displacement d, so
      P_ATP(d) = [ L(p_h; b, u) ]^d ,  d >= 1
    where L(s; b, u) = [(b+u+s) - sqrt((b+u+s)^2 - 4bu)] / (2u)  is the FPT
    Laplace transform (u L^2 - (b+u+s) L + b = 0, root with L(0)=1).
    This replaces the naive (1-p_h)^(d/T): hydrolysis samples the heavy tail
    of the age distribution (backward fluctuations linger and survive), which
    is why the measured comb is far shallower than exp(-p_h*d/T). GROSS rates
    here — returns are part of the walk. d=0 (tip) is the renewal state a_B.

  T_comb estimator (independent current meter — reads T off the age
  structure instead of the event stream):
      fit r = per-depth survival from measured comb depths 2..kmax,
      T_comb = ln(1-p_h) / ln(r)

  Starvation brake (dynamic instability in the length coordinate):
      as n grows, c falls, b_B falls, the barbed tip ages (a_B drops through
      the renewal balance), so the effective barbed death rate RISES with n —
      the chain's d(n) is no longer flat. Full n-dependent rates below feed
      the exact stationary distribution.
"""
import numpy as np

# ---- locked engine parameters (M4H hyd_fpt.ergo) ----
N, V, FLOOR = 60, 1728.0, 3
KONB, KONP = 1.8e-2, 1.0e-2          # /step/conc
DT = 0.005
KHYD = 0.03
P_H = KHYD * DT                      # 1.5e-4 per-step hydrolysis draw
KOFFB_T, KOFFB_A = 0.045, 0.18
KOFFP_T, KOFFP_A = 0.05, 0.10
U_BT, U_BA = KOFFB_T * DT, KOFFB_A * DT   # 2.25e-4, 9.0e-4
U_PT, U_PA = KOFFP_T * DT, KOFFP_A * DT   # 2.5e-4, 5.0e-4
# phi-2 measured returns (64-run ensemble)
RHO_B, RHO_P = 0.442, 0.059


def fpt_laplace(s, b, u):
    """L(s) = E[exp(-s * FPT to +1)] for a birth-death walk, rates b fwd, u bwd."""
    disc = (b + u + s) ** 2 - 4 * b * u
    return ((b + u + s) - np.sqrt(disc)) / (2 * u)


def tip_atp(b, u_t, u_a, p_expose):
    """Stationary P(tip ATP) from the renewal balance."""
    gain = b + u_a * p_expose
    loss = P_H + u_t * (1.0 - p_expose)
    return gain / (gain + loss)


def solve_fixed_point(tol=1e-13, maxit=3000):
    """Self-consistent (c, T). Returns dict with the full state."""
    c = 0.017     # phi-2-ish start
    T = 2.4e-4
    for _ in range(maxit):
        n = N - c * V
        b_b, b_p = KONB * c, KONP * c
        # barbed exposure: monomer beneath tip is one depth-step old,
        # P2b = L(p_h) with current gross rates (iterate on u_gross too)
        u_gb = U_BA   # first pass: mostly-ADP guess for the walk
        for _ in range(50):
            p2b = fpt_laplace(P_H, b_b, u_gb)
            a_b = tip_atp(b_b, U_BT, U_BA, p2b)
            u_gb_new = a_b * U_BT + (1 - a_b) * U_BA
            if abs(u_gb_new - u_gb) < 1e-12:
                u_gb = u_gb_new
                break
            u_gb = u_gb_new
        p2p = (1 - P_H) ** (max(n - 2.0, 1.0) / T)   # pointed: full transit, ~0
        a_p = tip_atp(b_p, U_PT, U_PA, p2p)
        u_gp = a_p * U_PT + (1 - a_p) * U_PA
        ub = u_gb * (1 - RHO_B)
        up = u_gp * (1 - RHO_P)
        T_new = b_b - ub
        c_new = (ub + up) / (KONB + KONP)
        if abs(T_new - T) < tol and abs(c_new - c) < tol * 1e2:
            T, c = T_new, c_new
            break
        T, c = T_new, c_new
    n = N - c * V
    return dict(c=c, T=T, n=n, a_b=a_b, a_p=a_p, p2b=p2b, p2p=p2p,
                u_gb=u_gb, u_gp=u_gp,
                ub_eff=ub, up_eff=up,
                closure=abs((KONB*c - ub) - (up - KONP*c)))


def comb(d, fp):
    """Predicted P_ATP at assay depth d (d=0 = barbed tip)."""
    d = np.asarray(d, dtype=float)
    L = fpt_laplace(P_H, KONB * fp['c'], fp['u_gb'])
    out = L ** d
    out[d == 0] = fp['a_b']
    return out


def t_comb(depths, p_atp, b_gross):
    """Independent current meter. Fit geometric ratio r from the measured
    comb (d>=1), invert the FPT Laplace law for the implied gross unbind u
    given the measured gross bind rate b, then T_comb = b - u.
    Inversion: r = L(p_h;b,u)  <=>  u r^2 - (b+u+p_h) r + b = 0
    =>  u = (b - r*(b+p_h)) / (r - r^2)  [solve: u r^2 - u r = r(b+p_h) - b]."""
    d = np.asarray(depths, dtype=float)
    p = np.asarray(p_atp, dtype=float)
    m = (d >= 1) & (p > 0)
    slope = np.sum(d[m] * np.log(p[m])) / np.sum(d[m]**2)
    r = np.exp(slope)
    u = (b_gross - r * (b_gross + P_H)) / (r - r ** 2)
    return b_gross - u, r


def rates_n(T):
    """n-dependent chain rates with the starvation brake built in.
    b(n) = (KONB+KONP)(N-n)/V ; d(n) = uB_eff(n) + uP_eff(n) with
    a_B(n), a_P(n) from the renewal balance at that n (T held at its
    fixed-point value — the shear is set globally, the tip state locally).
    Barbed exposure uses the FPT-Laplace P2 (self-consistent in u_gross)."""
    ns = np.arange(FLOOR, N + 1)
    c = (N - ns) / V
    b_b, b_p = KONB * c, KONP * c
    u_gb = np.full(len(ns), U_BA)
    for _ in range(60):
        p2b = fpt_laplace(P_H, b_b, u_gb)
        a_b = tip_atp(b_b, U_BT, U_BA, p2b)
        u_gb_new = a_b * U_BT + (1 - a_b) * U_BA
        if np.max(np.abs(u_gb_new - u_gb)) < 1e-12:
            u_gb = u_gb_new
            break
        u_gb = u_gb_new
    p2p = (1 - P_H) ** (np.maximum(ns - 2.0, 1.0) / T)
    a_p = tip_atp(b_p, U_PT, U_PA, p2p)
    ub = u_gb * (1 - RHO_B)
    up = (a_p * U_PT + (1 - a_p) * U_PA) * (1 - RHO_P)
    d = ub + up
    d[ns == FLOOR] = 0.0
    return ns, (KONB + KONP) * c, d, a_b, a_p


def reduced_engine(nsteps=3_000_000, ndiag=500, seed=1, floor=3, K=16,
                   ret=True):
    """phi-3 exact 1D reduction of the full engine, simulated directly.

    String of bind-times (back = barbed tip, front = pointed tip) with:
      - depletion feedback: b_end(n) = KON_end * (N-n)/V
      - state-dependent tip unbinds (U_BT/U_BA barbed, U_PT/U_PA pointed)
      - hydrolysis p_h per bound monomer per step, lazily realized at
        exposure (survival (1-p_h)^age exact) with PERSISTENT realization
        (re-exposed monomers keep and keep decaying from their state)
      - returns = cap recycling: w.p. RHO_end an unbind is followed by
        immediate recapture of the same (recharged, ATP) monomer: no depth
        change, tip NUC reset — the channel that keeps caps young
      - comb measured with the engine's estimator (Bernoulli per monomer at
        DIAG, live tip state at d=0)
    Validated against the per-step explicit toy to <1 sigma, and against the
    64-run engine ensemble in PHI3_RESULTS.md."""
    rng = np.random.default_rng(seed)
    bt = [0, 0, 0]; rz = [None, None, None]
    tipB = True; tipP = None
    ca = np.zeros(K); cc = np.zeros(K)
    nb = nu = nbp = nup = nrb = nrp = nd = 0; sB = sP = 0
    lsum = 0; omp = 1 - P_H
    for t in range(1, nsteps + 1):
        n = len(bt); c = (N - n) / V
        if tipB and rng.random() < P_H: tipB = False; rz[-1] = [False, t]
        if tipP and rng.random() < P_H: tipP = False; rz[0] = [False, t]
        if rng.random() < KONB * c:
            bt.append(t); rz.append([True, t]); tipB = True; nb += 1
        if rng.random() < KONP * c:
            bt.insert(0, t); rz.insert(0, [True, t]); tipP = True; nbp += 1
        u = U_BT if tipB else U_BA
        if len(bt) > floor and rng.random() < u:
            nu += 1
            if ret and rng.random() < RHO_B:
                bt[-1] = t; rz[-1] = [True, t]; tipB = True; nrb += 1
            else:
                bt.pop(); rz.pop()
                e = rz[-1]
                if e is None: tipB = rng.random() < omp ** (t - bt[-1]); rz[-1] = [tipB, t]
                elif e[0]:    tipB = rng.random() < omp ** (t - e[1]); e[0] = tipB; e[1] = t
                else:         tipB = False
        u = U_PT if tipP else U_PA
        if len(bt) > floor and rng.random() < u:
            nup += 1
            if ret and rng.random() < RHO_P:
                bt[0] = t; rz[0] = [True, t]; tipP = True; nrp += 1
            else:
                bt.pop(0); rz.pop(0)
                e = rz[0]
                if e is None: tipP = rng.random() < omp ** (t - bt[0]); rz[0] = [tipP, t]
                elif e[0]:    tipP = rng.random() < omp ** (t - e[1]); e[0] = tipP; e[1] = t
                else:         tipP = False
        if t > nsteps // 2:
            lsum += len(bt)
            if t % ndiag == 0:
                nd += 1; sB += tipB; sP += (tipP is True)
                for d in range(min(K, len(bt))):
                    if d == 0: p = 1.0 if tipB else 0.0
                    else:
                        e = rz[-1 - d]
                        if e is None: p = omp ** (t - bt[-1 - d])
                        elif e[0]:    p = omp ** (t - e[1])
                        else:         p = 0.0
                    cc[d] += 1; ca[d] += (rng.random() < p)
    win = nsteps // 2
    return dict(comb=ca / np.maximum(cc, 1), tipB=sB / nd, tipP=sP / nd,
                b_gross=(nb + nrb) / nsteps, u_gross=nu / nsteps,
                bp_gross=(nbp + nrp) / nsteps, up_gross=nup / nsteps,
                Tb=(nb - (nu - nrb)) / nsteps, Tp=((nup - nrp) - nbp) / nsteps,
                lmean=lsum / win)


def stationary_n(T):
    ns, b, d, _, _ = rates_n(T)
    pi = np.ones(len(ns))
    for i in range(1, len(ns)):
        pi[i] = pi[i-1] * b[i-1] / d[i]
    p = pi / pi.sum()
    m = (ns * p).sum()
    return ns, p, m, np.sqrt(((ns - m)**2 * p).sum())


if __name__ == "__main__":
    fp = solve_fixed_point()
    print("=== phi-3 fixed point ===")
    print(f"c* = {fp['c']:.5f}   n* = {fp['n']:.1f}   T = {fp['T']:.3e}/step")
    print(f"a_B (barbed tip ATP)  = {fp['a_b']:.3f}   (phi-2 engine: ~0.80)")
    print(f"a_P (pointed tip ATP) = {fp['a_p']:.3f}   (phi-2 engine: ~0.27)")
    print(f"u_B_eff = {fp['ub_eff']:.3e}   u_P_eff = {fp['up_eff']:.3e}")
    print(f"closure residual = {fp['closure']:.2e}")
    print(f"comb depths 0..8: {np.round(comb(np.arange(0,9), fp),3)}")
    print(f"  (engine 16-seed means: tip 0.82, d1 0.52, d2 0.37, d3 0.24)")
    ns, p, m, sd = stationary_n(fp['T'])
    print(f"stationary length (braked chain): mean={m:.2f} sd={sd:.2f}")
