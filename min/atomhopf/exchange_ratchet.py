#!/usr/bin/env python3
"""exchange_ratchet.py — the ratchet test: how much of the 20-element
anomaly census is internal (exchange stabilization, born from fermionic
antisymmetry) vs external (correlation/relativity)?

Minimal effective model per element Z:
  - candidates: the Madelung config plus every config reachable by
    moving <= 2 electrons among the frontier subshells
    {ns, (n-1)d, (n-2)f, (n+1)p} (capacities respected);
  - spin maximized per subshell (Hund's first rule):
    n_up = min(n_i, cap_i/2), n_dn = n_i - n_up;
  - E = sum n_i eps_i  - K * sum_i [C(n_up,2) + C(n_dn,2)]
                       + P * (paired orbitals = sum n_dn)
  - eps: s = 0, f = Delta - Delta_fd, d = Delta, p = 2*Delta
    (Madelung ordering by construction => K=P=0 reproduces the 98/118
    baseline exactly).
  - predicted ground = argmin E (exact ties break toward Madelung).

Sweep: K, P in units of Delta (fixed 1), Delta_fd/Delta in a small set.
Metrics per grid point: predicted anomaly set vs the curated real set
(20 elements, from atom_census.py — reused, not rebuilt); precision,
recall, matches/118.

Slater scale (oracle 3): F^k radial integrals for Slater 3d (Fe,
Z_eff=6.25, n*=3) and 4f (Gd, Z_eff=7.9, n*=3.7) orbitals; exchange per
same-spin pair J_bar from numerically exact angular factors
(Gaunt-reduced 1D quadrature, no memorized coefficients).

Determinism: no RNG, sorted iteration; run twice byte-identical,
PYTHONHASHSEED-invariant.
"""
import itertools
import numpy as np

from atom_census import SYMBOLS, ORDER_MADELUNG, fill, actual, LSYM, CAP

C2 = lambda n: n * (n - 1) // 2
N_REAL = None  # set in main

# real anomaly set from the curated table
def real_anomalies():
    return {Z for Z in range(1, 119)
            if fill(ORDER_MADELUNG, Z) != actual(Z)}


# ----------------------------------------------------------------------
# candidate enumeration + model energy
# ----------------------------------------------------------------------

def period_of(Z):
    return max(int(k[0]) for k in fill(ORDER_MADELUNG, Z))


def frontier(Z):
    n = period_of(Z)
    subs = []
    for name, l in ((f"{n}s", 0), (f"{n - 1}d", 2), (f"{n - 2}f", 3),
                    (f"{n + 1}p", 1)):
        nsub = int(name[:-1])
        if nsub >= 1 and l < nsub:   # subshell must exist (l < its n)
            subs.append((name, l))
    return subs  # [(name, l), ...]


def candidates(Z):
    """Madelung config + all <=2-electron moves along the measured
    anomaly channels: ns <-> (n-1)d and (n-2)f <-> (n-1)d.

    Channel note (disclosed modeling choice): the ns -> (n-2)f channel
    is excluded. With it, the model floods lanthanide false positives
    (e.g. Pr -> 4f^5 6s^0) because the ratchet always gains by filling
    toward the f^7 half-shell — no measured ground state uses that
    channel. The f shell is inner/core-like; its frontier competition
    is with (n-1)d. This restriction IS part of the model's content:
    the ratchet operates between the d subshell and its s/f frontier
    partners."""
    base = fill(ORDER_MADELUNG, Z)
    n = period_of(Z)
    s, d, f = f"{n}s", f"{n - 1}d", f"{n - 2}f"
    subs = [s for s, _ in frontier(Z)]
    chan = [(s, d), (d, s), (f, d), (d, f)]
    cands = {tuple(sorted(base.items()))}
    for src, dst in chan:
        if src not in subs or dst not in subs:
            continue
        if base.get(src, 0) <= 0:
            continue
        for nmove in (1, 2):
            c = dict(base)
            if c.get(src, 0) < nmove:
                continue
            l = LSYM.index(dst[-1])
            if c.get(dst, 0) + nmove > CAP[dst[-1]]:
                continue
            c[src] -= nmove
            if c[src] == 0:
                del c[src]
            c[dst] = c.get(dst, 0) + nmove
            cands.add(tuple(sorted(c.items())))
    return [dict(c) for c in cands]


def energy(cfg, eps, K, P):
    e = 0.0
    for sub, n in cfg.items():
        l = sub[-1]
        e += n * eps[l]
        orb = 2 * LSYM.index(l) + 1          # orbitals in the subshell
        up = min(n, orb)
        dn = n - up
        e += -K * (C2(up) + C2(dn)) + P * dn
    return e


def eps_uniform(Z, prm):
    K, P, dfd = prm
    return {"s": 0.0, "f": 1.0 - dfd, "d": 1.0, "p": 2.0}


def eps_series(Z, prm):
    """Variant B: per-series s-d gaps (4d smallest, 5d largest — the
    relativistic s-stabilization trend). prm = (K, P, dfd, D3, D4, D5)."""
    K, P, dfd, D3, D4, D5 = prm
    n = period_of(Z)
    D = {4: D3, 5: D4}.get(n, D5)
    return {"s": 0.0, "f": D - dfd, "d": D, "p": 2.0 * D}


def predict(Z, eps, K, P, mad):
    best = None
    bestE = None
    for c in candidates(Z):
        E = energy(c, eps, K, P)
        if bestE is None or E < bestE - 1e-12:
            bestE = E
            best = c
    # exact-tie policy: if Madelung is within 1e-12 of the best, keep it
    if energy(mad, eps, K, P) <= bestE + 1e-12:
        return mad
    return best


def run_sweep(eps_fn, grid):
    """grid: list of prm tuples. Returns list of
    (prm, precision, recall, matches, pred_set)."""
    real = real_anomalies()
    out = []
    for prm in grid:
        pred = set()
        matches = 0
        for Z in range(1, 119):
            mad = fill(ORDER_MADELUNG, Z)
            eps = eps_fn(Z, prm)
            p = predict(Z, eps, prm[0], prm[1], mad)
            if p == actual(Z):
                matches += 1
            if p != mad:
                pred.add(Z)
        tp = len(pred & real)
        prec = tp / len(pred) if pred else 1.0
        rec = tp / len(real)
        out.append((prm, prec, rec, matches, frozenset(pred)))
    return real, out


def report_block(tag, real, results, prm_fmt):
    def f1(r):
        p, c = r[1], r[2]
        return 2 * p * c / (p + c) if p + c else 0
    perfect = [r for r in results if r[1] == 1.0 and r[2] > 0]
    if perfect:
        best_rec = max(r[2] for r in perfect)
        best = [r for r in perfect if r[2] == best_rec]
        caught = set()
        for r in best:
            caught |= (r[4] & real)
        print(f"[{tag}] precision-1 cells with recall>0: {len(perfect)}; "
              f"best recall {best_rec:.2f} "
              f"({int(round(best_rec*20))}/20)")
        print(f"  caught: {' '.join(sorted(SYMBOLS[Z-1] for Z in caught))}")
        print(f"  example cell: {prm_fmt(best[0][0])}")
        # union over ALL precision-1 cells (any recall>0)
        allcaught = set()
        for r in perfect:
            allcaught |= (r[4] & real)
        print(f"  caught in ANY precision-1 cell: "
              f"{' '.join(sorted(SYMBOLS[Z-1] for Z in allcaught))}")
    else:
        allcaught = set()
        print(f"[{tag}] NO precision-1 cell with recall>0 "
              f"(uniform-gap model cannot be exact)")
    b = max(results, key=f1)
    print(f"[{tag}] best-F1 cell {prm_fmt(b[0])}: precision {b[1]:.3f} "
          f"recall {b[2]:.3f} matches {b[3]}/118")
    print(f"  predicted: {' '.join(sorted(SYMBOLS[Z-1] for Z in b[4]))}")
    print(f"  false positives: "
          f"{' '.join(sorted(SYMBOLS[Z-1] for Z in b[4] - real))}")
    return allcaught


# ----------------------------------------------------------------------
# candidate enumeration + model energy
# ----------------------------------------------------------------------

def period_of(Z):
    return max(int(k[0]) for k in fill(ORDER_MADELUNG, Z))


def frontier(Z):
    n = period_of(Z)
    subs = []
    for name, l in ((f"{n}s", 0), (f"{n - 1}d", 2), (f"{n - 2}f", 3),
                    (f"{n + 1}p", 1)):
        nsub = int(name[:-1])
        if nsub >= 1 and l < nsub:   # subshell must exist (l < its n)
            subs.append((name, l))
    return subs  # [(name, l), ...]


def candidates(Z):
    """Madelung config + all <=2-electron moves along the measured
    anomaly channels: ns <-> (n-1)d and (n-2)f <-> (n-1)d.

    Channel note (disclosed modeling choice): the ns -> (n-2)f channel
    is excluded. With it, the model floods lanthanide false positives
    (e.g. Pr -> 4f^5 6s^0) because the ratchet always gains by filling
    toward the f^7 half-shell — no measured ground state uses that
    channel. The f shell is inner/core-like; its frontier competition
    is with (n-1)d. This restriction IS part of the model's content:
    the ratchet operates between the d subshell and its s/f frontier
    partners."""
    base = fill(ORDER_MADELUNG, Z)
    n = period_of(Z)
    s, d, f = f"{n}s", f"{n - 1}d", f"{n - 2}f"
    subs = [s for s, _ in frontier(Z)]
    chan = [(s, d), (d, s), (f, d), (d, f)]
    cands = {tuple(sorted(base.items()))}
    for src, dst in chan:
        if src not in subs or dst not in subs:
            continue
        if base.get(src, 0) <= 0:
            continue
        for nmove in (1, 2):
            c = dict(base)
            if c.get(src, 0) < nmove:
                continue
            l = LSYM.index(dst[-1])
            if c.get(dst, 0) + nmove > CAP[dst[-1]]:
                continue
            c[src] -= nmove
            if c[src] == 0:
                del c[src]
            c[dst] = c.get(dst, 0) + nmove
            cands.add(tuple(sorted(c.items())))
    return [dict(c) for c in cands]


def energy(cfg, eps, K, P):
    e = 0.0
    for sub, n in cfg.items():
        l = sub[-1]
        e += n * eps[l]
        orb = 2 * LSYM.index(l) + 1          # orbitals in the subshell
        up = min(n, orb)
        dn = n - up
        e += -K * (C2(up) + C2(dn)) + P * dn
    return e


def eps_uniform(Z, prm):
    K, P, dfd = prm
    return {"s": 0.0, "f": 1.0 - dfd, "d": 1.0, "p": 2.0}


def eps_series(Z, prm):
    """Variant B: per-series s-d gaps (4d smallest, 5d largest — the
    relativistic s-stabilization trend). prm = (K, P, dfd, D3, D4, D5)."""
    K, P, dfd, D3, D4, D5 = prm
    n = period_of(Z)
    D = {4: D3, 5: D4}.get(n, D5)
    return {"s": 0.0, "f": D - dfd, "d": D, "p": 2.0 * D}


def predict(Z, eps, K, P, mad):
    best = None
    bestE = None
    for c in candidates(Z):
        E = energy(c, eps, K, P)
        if bestE is None or E < bestE - 1e-12:
            bestE = E
            best = c
    # exact-tie policy: if Madelung is within 1e-12 of the best, keep it
    if energy(mad, eps, K, P) <= bestE + 1e-12:
        return mad
    return best


def run_sweep(eps_fn, grid):
    """grid: list of prm tuples. Returns list of
    (prm, precision, recall, matches, pred_set)."""
    real = real_anomalies()
    out = []
    for prm in grid:
        pred = set()
        matches = 0
        for Z in range(1, 119):
            mad = fill(ORDER_MADELUNG, Z)
            eps = eps_fn(Z, prm)
            p = predict(Z, eps, prm[0], prm[1], mad)
            if p == actual(Z):
                matches += 1
            if p != mad:
                pred.add(Z)
        tp = len(pred & real)
        prec = tp / len(pred) if pred else 1.0
        rec = tp / len(real)
        out.append((prm, prec, rec, matches, frozenset(pred)))
    return real, out


def sweep():
    real = real_anomalies()
    eps_sets = {
        0.3: {"s": 0.0, "f": 0.7, "d": 1.0, "p": 2.0},
        0.6: {"s": 0.0, "f": 0.4, "d": 1.0, "p": 2.0},
        1.0: {"s": 0.0, "f": 0.0, "d": 1.0, "p": 2.0},
    }
    Ks = np.arange(0.0, 1.2001, 0.02)
    Ps = np.arange(0.0, 0.8001, 0.04)
    results = []
    for dfd, eps in eps_sets.items():
        for K in Ks:
            for P in Ps:
                pred = set()
                matches = 0
                for Z in range(1, 119):
                    mad = fill(ORDER_MADELUNG, Z)
                    p = predict(Z, eps, K, P, mad)
                    if p == actual(Z):
                        matches += 1
                    if p != mad:
                        pred.add(Z)
                tp = len(pred & real)
                prec = tp / len(pred) if pred else 1.0
                rec = tp / len(real)
                results.append((dfd, K, P, prec, rec, matches,
                                frozenset(pred)))
    return real, results


# ----------------------------------------------------------------------
# Slater exchange scale (oracle 3)
# ----------------------------------------------------------------------

def slater_radial_F(zeta, nstar, l, ks):
    """Slater-Condon F^k for a Slater orbital R ~ r^{n*-1} e^{-zeta r/n*}.

    Exact 1D quadrature via the cumulative formulation, in Hartree.
    """
    from numpy.polynomial.legendre import leggauss
    # grid on x = zeta r (dimensionless); F^k scales linearly in zeta
    xg, wg = leggauss(400)
    # map [0,inf) via x = t/(1-t), t in (0,1)
    t = 0.5 * (xg + 1.0)
    x = t / (1.0 - t)
    w = wg / (1.0 - t) ** 2
    R2 = x ** (2 * nstar - 2) * np.exp(-2 * x / nstar)
    norm = (R2 * w).sum()
    R2 /= norm
    out = {}
    for k in ks:
        # F^k = 2 int_{x1<x2} R2(x1) R2(x2) x1^k / x2^{k+1} w1 w2
        inner_le = np.cumsum(R2 * x ** k * w)
        F = 2.0 * (R2 * w * (inner_le - R2 * x ** k * w)
                   / x ** (k + 1)).sum()
        out[k] = F * zeta  # back to Hartree
    return out


def _legendre_all(lmax, x):
    """All associated P_l^m(x), m >= 0, l <= lmax (Condon-Shortley)."""
    P = {(0, 0): np.ones_like(x)}
    for m in range(1, lmax + 1):
        P[(m, m)] = -(2 * m - 1) * np.sqrt(1 - x * x) * P[(m - 1, m - 1)]
    for m in range(0, lmax):
        P[(m + 1, m)] = (2 * m + 1) * x * P[(m, m)]
    for m in range(0, lmax + 1):
        for ll in range(m + 2, lmax + 1):
            P[(ll, m)] = ((2 * ll - 1) * x * P[(ll - 1, m)]
                          - (ll + m - 1) * P[(ll - 2, m)]) / (ll - m)
    return P


def _ylm(l, m, x, phi):
    """Spherical harmonic Y_lm(x=cos theta, phi), Condon-Shortley."""
    from math import factorial
    am = abs(m)
    pmm = np.ones_like(x)
    if am > 0:
        somx2 = np.sqrt(1 - x * x)
        fact = 1.0
        for _ in range(1, am + 1):
            pmm = -pmm * fact * somx2
            fact += 2.0
    if l == am:
        P = pmm
    else:
        pmmp1 = x * (2 * am + 1) * pmm
        if l == am + 1:
            P = pmmp1
        else:
            P = None
            for ll in range(am + 2, l + 1):
                P = ((2 * ll - 1) * x * pmmp1 - (ll + am - 1) * pmm) / (ll - am)
                pmm, pmmp1 = pmmp1, P
    norm = np.sqrt((2 * l + 1) / (4 * np.pi)
                   * factorial(l - am) / factorial(l + am))
    Y = norm * P
    if m < 0:
        Y = Y * ((-1) ** am)
    return Y * np.exp(1j * m * phi) * ((-1) ** 0)


def exchange_pair_avg(l, F):
    """Mean same-spin pair exchange for the half-filled l subshell.

    J_ex(mm') = sum_{k even <= 2l} (4pi/(2k+1)) |G|^2 F^k with the
    Gaunt integral G = int Y*_lm Y_kq Y_lm' dOmega (q = m - m'),
    evaluated by direct (theta, phi) quadrature — no memorized
    coefficients. Validated against p^3 4S: total exchange
    -(3/5) F^2 (Racah), i.e. 0.2 F^2 per pair.
    """
    from numpy.polynomial.legendre import leggauss
    nx = 240
    xg, wg = leggauss(nx)
    ph = np.linspace(0, 2 * np.pi, 48, endpoint=False)
    wp = ph[1] - ph[0]
    X, PH = np.meshgrid(xg, ph, indexing="ij")
    W = wg[:, None] * wp
    ms = list(range(-l, l + 1))
    Y = {m: _ylm(l, m, X, PH) for m in ms}
    Yk = {}
    for k in range(0, 2 * l + 1, 2):
        for q in range(-k, k + 1):
            Yk[(k, q)] = _ylm(k, q, X, PH)
    J = {}
    for m1, m2 in itertools.combinations(ms, 2):
        val = 0.0
        for k in range(0, 2 * l + 1, 2):
            q = m1 - m2
            if abs(q) > k:
                continue
            G = (np.conj(Y[m1]) * Yk[(k, q)] * Y[m2] * W).sum()
            val += (4 * np.pi / (2 * k + 1)) * abs(G) ** 2 * F.get(k, 0.0)
        J[(m1, m2)] = val
    return float(np.mean(list(J.values()))), J


def slater_section(K_work_ratio, Delta_eV=1.5):
    print()
    print("=" * 66)
    print("ORACLE 3 — Slater-orbital exchange scale")
    print("=" * 66)
    # 3d (Fe): Slater's rules: 18 core x1.00 + 5 same-group x0.35
    zeff_3d = 26 - 18 * 1.0 - 5 * 0.35
    F3 = slater_radial_F(zeff_3d, 3.0, 2, ks=(0, 2, 4))
    Jd, _ = exchange_pair_avg(2, F3)
    print(f"  3d (Fe, Z_eff={zeff_3d}, n*=3): "
          f"F2={F3[2]:.3f} Ha={F3[2]*27.2114:.2f} eV, "
          f"F4={F3[4]:.3f} Ha={F3[4]*27.2114:.2f} eV")
    print(f"    mean same-spin pair exchange J_bar(3d) = "
          f"{Jd*27.2114:.3f} eV")
    # 4f (Gd): 54 core x1.00 + 6 same-group x0.35
    zeff_4f = 64 - 54 * 1.0 - 6 * 0.35
    F4 = slater_radial_F(zeff_4f, 3.7, 3, ks=(0, 2, 4, 6))
    Jf, _ = exchange_pair_avg(3, F4)
    print(f"  4f (Gd, Z_eff={zeff_4f}, n*=3.7): "
          f"F2={F4[2]*27.2114:.2f} eV, F4={F4[4]*27.2114:.2f} eV, "
          f"F6={F4[6]*27.2114:.2f} eV")
    print(f"    mean same-spin pair exchange J_bar(4f) = "
          f"{Jf*27.2114:.3f} eV")
    K_work_eV = K_work_ratio * Delta_eV
    print(f"  working K = {K_work_ratio:.3f} x Delta; with the 4s/3d gap "
          f"Delta ~ {Delta_eV} eV -> K_work ~ {K_work_eV:.3f} eV")
    print(f"  K_work / J_bar(3d) = {K_work_eV / Jd / 27.2114:.3f} "
          f"(order-of-magnitude agreement: "
          f"{0.2 < K_work_eV / (Jd * 27.2114) < 5})")


# ----------------------------------------------------------------------

def main():
    real = real_anomalies()
    print("=" * 66)
    print("RATCHET TEST — exchange stabilization vs the 20 anomalies")
    print("=" * 66)
    print(f"real anomaly set ({len(real)}): "
          + " ".join(sorted(SYMBOLS[Z - 1] for Z in real)))

    # baseline oracle: K=P=0 must reproduce Madelung exactly
    Z_mad = sum(1 for Z in range(1, 119)
                if predict(Z, eps_uniform(Z, (0.0, 0.0, 0.6)), 0.0, 0.0,
                           fill(ORDER_MADELUNG, Z)) == actual(Z))
    print(f"\nK=0,P=0 baseline: {Z_mad}/118 matches "
          f"(Madelung reproduction gate: {Z_mad == 98})")

    # ── Variant A: uniform gap (the plan's Delta x K sweep) ──
    Ks = np.arange(0.0, 0.8001, 0.02)
    Ps = np.arange(0.0, 0.6001, 0.05)
    dfds = (0.3, 0.6)
    gridA = [(K, P, dfd) for dfd in dfds for K in Ks for P in Ps]
    realA, resA = run_sweep(eps_uniform, gridA)
    print(f"\nvariant A (uniform gap; {len(gridA)} cells):")
    caughtA = report_block("A-uniform", realA, resA,
                           lambda p: f"K={p[0]:.2f} P={p[1]:.2f} "
                                     f"dfd={p[2]:.1f}")
    # robust region extent for the best precision-1 recall in A
    pa = [r for r in resA if r[1] == 1.0 and r[2] > 0]
    if pa:
        br = max(r[2] for r in pa)
        Ks_r = sorted({r[0][0] for r in pa if r[2] == br})
        Ps_r = sorted({r[0][1] for r in pa if r[2] == br})
        print(f"  A robust extent at recall {br:.2f}: K/Delta "
              f"[{Ks_r[0]:.2f},{Ks_r[-1]:.2f}], P/Delta "
              f"[{Ps_r[0]:.2f},{Ps_r[-1]:.2f}]")

    # ── Variant B: per-series gaps (4d smallest, 5d largest) ──
    KsB = np.arange(0.05, 0.6001, 0.025)
    PsB = np.arange(0.0, 0.5001, 0.05)
    gridB = [(K, P, dfd, D3, D4, D5)
             for dfd in (0.3, 0.6)
             for D3 in (0.9, 1.1)
             for D4 in (0.6, 0.8)
             for D5 in (1.2, 1.5)
             for K in KsB for P in PsB]
    realB, resB = run_sweep(eps_series, gridB)
    print(f"\nvariant B (series gaps; {len(gridB)} cells):")
    caughtB = report_block(
        "B-series", realB, resB,
        lambda p: f"K={p[0]:.3f} P={p[1]:.2f} dfd={p[2]:.1f} "
                  f"D3={p[3]:.1f} D4={p[4]:.1f} D5={p[5]:.1f}")
    pb = [r for r in resB if r[1] == 1.0 and r[2] > 0]
    if pb:
        br = max(r[2] for r in pb)
        cells = [r for r in pb if r[2] == br]
        Ks_r = sorted({r[0][0] for r in cells})
        Ps_r = sorted({r[0][1] for r in cells})
        D4s = sorted({r[0][4] for r in cells})
        D5s = sorted({r[0][5] for r in cells})
        print(f"  B robust extent at recall {br:.2f}: K "
              f"[{Ks_r[0]:.3f},{Ks_r[-1]:.3f}] P [{Ps_r[0]:.2f},"
              f"{Ps_r[-1]:.2f}] D4 {D4s} D5 {D5s}; "
              f"{len(cells)} cells")
        Kw = 0.5 * (Ks_r[0] + Ks_r[-1])
        print(f"  working K (center of best region): {Kw:.3f} x gap")

    # residuals: never caught at precision 1 in either variant
    resid = real - (caughtA | caughtB)
    print(f"\nresidual anomalies (never caught at precision 1, "
          f"A or B): {' '.join(sorted(SYMBOLS[Z - 1] for Z in resid))}")

    # ── P-channel probe: Gd/Cm need P > Delta_fd; does any cell catch
    # them WITHOUT the Tb/Bk false positives?  (Tb/Bk flip via the
    # double f->d move, gaining 2P whenever Gd gains P — so P > dfd
    # for Gd implies 2P > 2 dfd for Tb. Structural, verified by sweep.)
    print("\nP-channel probe (Gd/Cm half-filled-f^7 ratchet):")
    best_gd = None
    for dfd in (0.2, 0.3, 0.45, 0.6):
        for K in np.arange(0.05, 0.4001, 0.025):
            for P in np.arange(0.0, 0.6001, 0.05):
                prm = (round(K, 3), round(P, 2), dfd, 0.9, 0.8, 1.2)
                pred = set()
                fps = 0
                for Z in range(1, 119):
                    mad = fill(ORDER_MADELUNG, Z)
                    eps = eps_series(Z, prm)
                    p = predict(Z, eps, prm[0], prm[1], mad)
                    if p != mad:
                        pred.add(Z)
                        if p != actual(Z):
                            fps += 1
                if {64, 96} <= (pred & real) and fps <= 2:
                    c = len(pred & real)
                    if best_gd is None or c > best_gd[2]:
                        best_gd = (prm, fps, c, pred)
    if best_gd:
        prm, fps, _c, pred = best_gd
        caught = sorted(SYMBOLS[Z - 1] for Z in (pred & real))
        fpz = sorted(SYMBOLS[Z - 1] for Z in pred - real)
        print(f"  best cell catching Gd+Cm: K={prm[0]} P={prm[1]} "
              f"dfd={prm[2]} -> caught {caught}")
        print(f"    false positives: {fpz} (Tb/Bk always accompany "
              f"the P channel: the same 2P that empties pairs in "
              f"f^8 (Gd) empties them in f^9 (Tb) via double moves)")
        print(f"    precision {len(pred & real)}/{len(pred)} = "
              f"{len(pred & real) / len(pred):.3f}, recall "
              f"{len(pred & real)}/20 = {len(pred & real) / 20:.2f}")
    else:
        print("  no cell catches Gd+Cm")

    # Slater scale vs working K
    Kwork = 0.5 * (Ks_r[0] + Ks_r[-1]) if pb else 0.25
    slater_section(Kwork, Delta_eV=1.0)


if __name__ == "__main__":
    main()
