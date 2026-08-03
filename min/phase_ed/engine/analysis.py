"""Shared analysis protocol for engine plugins.

Given (model, N, params): E0, gap, ground vector, S(ell) + Calabrese-Cardy
fit for c, correlator C(r) = <raise_i lower_j> + algebraic/oscillatory fits
(eta, q). Cut convention: ell = 1..N//2 (matches earlier ED analyses).
"""

import numpy as np
from scipy.optimize import curve_fit
from scipy.sparse.linalg import LinearOperator, eigsh


def ground_state(model, N, params, k=2, tol=1e-12, ncv=None, maxiter=8000):
    dim = model.d_site ** N
    mv = model.make_matvec(N, params)
    A = LinearOperator((dim, dim), matvec=mv, dtype=complex)
    kw = dict(k=k, which="SA", tol=tol, maxiter=maxiter)
    if ncv is not None:
        kw["ncv"] = ncv
    evals, evecs = eigsh(A, **kw)
    order = np.argsort(evals)
    psi = evecs[:, order[0]].copy()
    res = float(np.linalg.norm(mv(psi) - evals[order[0]] * psi))
    return {"E0": float(evals[order[0]]),
            "gap": float(evals[order[1]] - evals[order[0]]),
            "residual": res, "psi": psi}


def entropy_cc(psi, N, d):
    t = psi.reshape((d,) * N)
    S = {}
    for ell in range(1, N // 2 + 1):
        s = np.linalg.svd(t.reshape(d ** ell, d ** (N - ell)),
                          compute_uv=False)
        p = s ** 2
        p = p[p > 1e-15]
        S[ell] = float(-np.sum(p * np.log(p)))
    ells = np.array(sorted(S), dtype=float)
    x = np.log((N / np.pi) * np.sin(np.pi * ells / N))
    y = np.array([S[int(e)] for e in ells])
    A = np.vstack([x, np.ones_like(x)]).T
    (c3, const), *_ = np.linalg.lstsq(A, y, rcond=None)
    rms = float(np.sqrt(np.mean((y - A @ [c3, const]) ** 2)))
    dof = max(len(x) - 2, 1)
    cov = np.sum((y - A @ [c3, const]) ** 2) / dof * np.linalg.inv(A.T @ A)[0, 0]
    return {"S": S, "c": float(3 * c3), "c_err": float(3 * np.sqrt(cov)),
            "rms": rms}


def _shift(t, ax, N, direction):
    """direction=+1: raise (out[m]=t[m-1], zero at m=0);
    direction=-1: lower (out[m]=t[m+1], zero at top)."""
    d = t.shape[ax]
    out = np.zeros_like(t)
    dst = [slice(None)] * N
    src = [slice(None)] * N
    if direction > 0:
        dst[ax], src[ax] = slice(1, d), slice(0, d - 1)
    else:
        dst[ax], src[ax] = slice(0, d - 1), slice(1, d)
    out[tuple(dst)] = t[tuple(src)]
    return out


def correlator(model, psi_flat, N):
    """C(r) = <raise_i lower_j>, averaged over cyclic pairs, r = 1..N/2."""
    psi = (np.exp(-1j * model.gauge_phases(N)) * psi_flat).reshape(
        (model.d_site,) * N)
    C = np.zeros(N // 2 + 1)
    C[0] = 1.0
    for r in range(1, N // 2 + 1):
        acc = 0.0
        for i in range(N):
            j = (i + r) % N
            acc += np.vdot(psi, _shift(_shift(psi, j, N, -1), i, N, +1))
        C[r] = np.real(acc) / N
    rs = np.arange(1, N // 2 + 1, dtype=float)
    return {"C": C, "fits": _fit_forms(rs, C[1:])}


def _fit_forms(rs, C):
    out = {}

    def alg(r, A, eta):
        return A / r ** eta

    def osc(r, A, q, delta, eta):
        return A * np.cos(q * r + delta) / r ** eta

    try:
        p, _ = curve_fit(alg, rs, C, p0=[C[0], 0.5], maxfev=20000)
        out["alg"] = {"A": float(p[0]), "eta": float(p[1]),
                      "rms": float(np.sqrt(np.mean((alg(rs, *p) - C) ** 2)))}
    except Exception as e:
        out["alg"] = {"error": str(e)}
    qmin = np.pi / rs[-1]
    best = None
    for q0 in (qmin, 0.5, 1.0, 2.0, 3.0):
        try:
            p, _ = curve_fit(osc, rs, C, p0=[C[0], max(q0, qmin), 0.0, 0.5],
                             bounds=([-np.inf, qmin, -np.pi, 0],
                                     [np.inf, np.pi, np.pi, 5]), maxfev=40000)
            rms = float(np.sqrt(np.mean((osc(rs, *p) - C) ** 2)))
            if best is None or rms < best[0]:
                best = (rms, p)
        except Exception:
            continue
    if best is not None:
        rms, p = best
        out["osc"] = {"q": float(p[1]), "eta": float(p[3]), "rms": rms}
    out["sign_changes"] = int(np.sum(np.diff(np.sign(C)) != 0))
    out["monotone"] = bool(np.all(np.diff(C) <= 1e-12))
    return out


def analyze(model, N, params, tol=1e-12, ncv=None):
    gs = ground_state(model, N, params, tol=tol, ncv=ncv)
    ent = entropy_cc(gs["psi"], N, model.d_site)
    cor = correlator(model, gs["psi"], N)
    return {"N": N, "params": {k: v for k, v in params.items()
                               if isinstance(v, (int, float))},
            "E0": gs["E0"], "gap": gs["gap"], "residual": gs["residual"],
            "c": ent["c"], "c_err": ent["c_err"], "cc_rms": ent["rms"],
            "S": {str(k): v for k, v in ent["S"].items()},
            "C": cor["C"].tolist(), "fits": cor["fits"]}
