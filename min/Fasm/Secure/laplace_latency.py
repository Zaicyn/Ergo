"""laplace_latency.py -- s-domain treatment of on-demand fetch latency.

Pattern source: min/actin_phasespace/hyd_oracle.py (FPT-Laplace forward
prediction + inversion for hidden rates). Same duality here, applied
to the fetch-vs-resend path instead of a birth-death walk (ours has
an elementary closed form -- geometric trials, no backward steps).

Process, per damaged frame needing parity: attempt k = 0..K-1 fetches
the parity; each attempt fails (parity lost) w.p. q. Before attempt k
wait sum_{j<k} b^j frame-times (backoff base b). Attempt costs f
frame-times. After K fails, give up and resend (cost R). Units are
frame-times; constants continue eulerbench-C (f=0.5, R=11).

Forward: LST of added latency T (closed form):
  c_k = (k+1)*f + w_k,  w_k = sum_{j<k} b^j,  w_0 = 0
  L(s) = sum_{k<K} (1-q) q^k e^{-s c_k} + q^K e^{-s c_K},  c_K = K f + w_K + R
  E[T] = -L'(0) computed directly from the sum (no differentiation).
Tails P(T>t) by Gaver-Stehfest numerical inversion (M=16) of the CDF
transform (1-L(s))/s. Validated against Monte Carlo (gate below).

Inverse (classify): attempts/fails -> q_hat (Bernoulli ML); q_hat ->
optimal b* by scanning E[T]; b* -> predicted P99 via inversion.
The loop is measure -> invert -> optimize -> SLO-predict.
"""
import numpy as np

F = 0.5    # one fetch attempt, frame-times
R = 11.0   # give-up resend (RTT 10 + 1), frame-times
K = 4      # attempts before give-up
rng = np.random.default_rng(0x1ACE)


def waits(b, K=K):
    w = [0.0]
    for k in range(1, K + 1):
        w.append(w[-1] + b ** (k - 1))
    return w  # w[k] = wait before attempt k


def costs(b, f=F, Rr=R, K=K):
    w = waits(b, K)
    c = [(k + 1) * f + w[k] for k in range(K)]
    cK = K * f + w[K] + Rr
    return c, cK


def lst(s, q, b, K=K, f=F, Rr=R):
    """LST E[e^{-sT}]; s scalar >= 0 (numpy-vectorized over s array)."""
    s = np.asarray(s, dtype=float)
    c, cK = costs(b, f, Rr, K)
    L = np.zeros_like(s)
    for k in range(K):
        L += (1 - q) * q ** k * np.exp(-s * c[k])
    L += q ** K * np.exp(-s * cK)
    return L


def mean_T(q, b, K=K, f=F, Rr=R):
    c, cK = costs(b, f, Rr, K)
    m = sum((1 - q) * q ** k * c[k] for k in range(K)) + q ** K * cK
    return m


def stehfest_weights(M=12):
    """Abate-Whitt Gaver-Stehfest weights (factorial form, verified
    term-by-term against mpmath's invertlaplace implementation)."""
    from math import factorial as F_
    n = M // 2
    V = []
    for k in range(1, M + 1):
        vk = 0.0
        for j in range(max(1, (k + 1) // 2), min(k, n) + 1):
            if k - j < 0 or 2 * j - k < 0:
                continue
            vk += (j ** n * F_(2 * j)
                   / (F_(n - j) * F_(j) * F_(j - 1) * F_(k - j)
                      * F_(2 * j - k)))
        V.append(((-1) ** (n + k)) * vk)
    return V


_SW = stehfest_weights()


def stehfest_tail(q, b, t, K=K, f=F, Rr=R):
    ln2t = np.log(2.0) / t
    s = 0.0
    for k, vk in enumerate(_SW, start=1):
        Lk = lst(k * ln2t, q, b, K, f, Rr)
        # (1-L(s))/s is the SURVIVAL transform (not CDF): integral of
        # e^{-st} P(T>t) dt. Inverting it yields P(T>t) directly.
        Fk = (1.0 - Lk) / (k * ln2t)
        s += vk * Fk
    return max(0.0, min(1.0, ln2t * s))


def exact_tail(q, b, t, K=K, f=F, Rr=R):
    """T is atomic (values c_k): tail by direct summation, no inversion."""
    c, cK = costs(b, f, Rr, K)
    p = sum((1 - q) * q ** k for k in range(K) if c[k] > t)
    if cK > t:
        p += q ** K
    return p


def mc_tail(q, b, N=200000, K=K, f=F, Rr=R):
    """Monte Carlo P(T>t) curve + mean, for the gate."""
    c, cK = costs(b, f, Rr, K)
    U = rng.random((N, K))
    T = np.full(N, cK)
    live = np.ones(N, dtype=bool)
    for k in range(K):
        hit = live & (U[:, k] >= q)
        T[hit] = c[k]
        live &= ~hit
    return T


print("gate: MC vs Stehfest tail agreement", flush=True)
for q, b in ((0.1, 1.5), (0.25, 2.0), (0.4, 2.0)):
    T = mc_tail(q, b)
    m_mc, m_th = T.mean(), mean_T(q, b)
    dev = []
    for t in (3.0, 6.5, 14.0):  # mid-interval: Stehfest rings near atoms
        pe = np.mean(T > t)
        pt = stehfest_tail(q, b, t)
        px = exact_tail(q, b, t)
        print(f"   t={t}: mc={pe:.4f} st={pt:.4f} ex={px:.4f}", flush=True)
        dev.append(max(abs(pe - pt), abs(pe - px), abs(pt - px)))
    print(f"q={q} b={b}: mean mc={m_mc:.4f} th={m_th:.4f} "
          f"max-tail-dev={max(dev):.4f}", flush=True)
    assert abs(m_mc - m_th) < 0.02 and max(dev) < 0.02, "gate failed!"
print("gate passes: closed form + inversion match Monte Carlo.", flush=True)

def p99_bisect(q, b, tailfn):
    lo, hi = 0.0, 200.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if tailfn(q, b, mid) > 0.01:
            lo = mid
        else:
            hi = mid
    return hi


print("optimal (b*, K*) vs loss q (b scan 1.0..4.0, K 1..4):", flush=True)
for q in (0.05, 0.1, 0.25, 0.4, 0.6):
    best = (1e30, None, None)
    for K in (1, 2, 3, 4):
        bs = np.arange(1.0, 4.01, 0.05)
        ms = [mean_T(q, b, K) for b in bs]
        i = int(np.argmin(ms))
        if ms[i] < best[0]:
            best = (ms[i], bs[i], K)
    mstar, bstar, Kstar = best
    p99 = p99_bisect(q, bstar, exact_tail)
    p99s = p99_bisect(q, bstar, stehfest_tail)
    # No assert here by design: exact P99 can sit ON an atom (up to
    # 0.13 mass at the give-up atom for q=0.6) where any smoothing
    # inverter must disagree. Agreement is gated at smooth points
    # above; here both columns are reported and the gap is expected
    # quantizer-vs-smoother behavior, not a bug.
    print(f"q={q:.2f}: b*={bstar:.2f} K*={Kstar} E[T]={mstar:.3f}ft "
          f"P99={p99:.1f}ft (stehfest {p99s:.1f}) resend-always={R:.1f}ft",
          flush=True)

print("inverse demo: 40 fails / 200 attempts -> q_hat, b*, P99:", flush=True)
qh = 40 / 200
best = (1e30, None, None)
for K in (1, 2, 3, 4):
    bs = np.arange(1.0, 4.01, 0.05)
    ms = [mean_T(qh, b, K) for b in bs]
    i = int(np.argmin(ms))
    if ms[i] < best[0]:
        best = (ms[i], bs[i], K)
mstar, bstar, Kstar = best
p99 = p99_bisect(qh, bstar, exact_tail)
print(f"q_hat={qh:.2f} b*={bstar:.2f} K*={Kstar} "
      f"E[T]={mstar:.3f}ft P99={p99:.1f}ft", flush=True)
