"""Phase-phase correlator C(r) = <e^{i(phi_i - phi_{i+r})}> and q extraction.

ED vectors (twisted gauge): rotate back with U^dagger = exp(-i sum ref_i p_i)
(diagonal phases), reshape to (3,)*N, and evaluate
  C(i,j) = <psi| Tm_i Tp_j |psi>
via masked tensor shifts (Tm = unit raise, Tp = unit lower), averaged over
all cyclic pairs with separation r = 1..N/2. Tensor axis k is ring site
N-1-k; reversal is a ring symmetry and does not affect the averaged |C|.

DMRG checkpoints: hdf5_io.load -> dict with 'psi' (MPS, original gauge),
psi.correlation_function('Tm', 'Tp') -> pairs; average over linear distance
r (wrap pairs appear as distance N-r).

Fits per (J, N): (a) A/r^eta, (b) A cos(q r + delta)/r^eta; report rms, q, eta.
"""

import json

import numpy as np
from scipy.optimize import curve_fit

B = 0.25
OUT = "results_correlator.json"


# ---------- ED correlator --------------------------------------------------

def gauge_phases(N):
    idx = np.arange(3 ** N)
    ph = np.zeros(3 ** N)
    for i in range(N):
        mi = (idx // 3 ** i) % 3 - 1
        ph += (2.0 * np.pi * i / N) * mi
    return ph


def _lower(t, ax, N):
    out = np.zeros_like(t)
    d = [slice(None)] * N
    s = [slice(None)] * N
    d[ax] = slice(0, 2)
    s[ax] = slice(1, 3)
    out[tuple(d)] = t[tuple(s)]
    return out


def _raise(t, ax, N):
    out = np.zeros_like(t)
    d = [slice(None)] * N
    s = [slice(None)] * N
    d[ax] = slice(1, 3)
    s[ax] = slice(0, 2)
    out[tuple(d)] = t[tuple(s)]
    return out


def correlator_ed(psi_flat, N):
    """C(r) for r = 1..N//2, averaged over all cyclic pairs."""
    psi = (np.exp(-1j * gauge_phases(N)) * psi_flat).reshape((3,) * N)
    C = np.zeros(N // 2 + 1)
    C[0] = 1.0
    for r in range(1, N // 2 + 1):
        acc = 0.0
        for i in range(N):
            j = (i + r) % N
            acc += np.vdot(psi, _raise(_lower(psi, j, N), i, N))
        C[r] = np.real(acc) / N
    return C


# ---------- DMRG correlator ------------------------------------------------

def correlator_dmrg(N, J):
    from tenpy.tools import hdf5_io
    st = hdf5_io.load(f"checkpoints/ckpt_N{N}_B{B}_J{J}.h5")
    psi = st["psi"]
    CF = psi.correlation_function("Tm", "Tp")  # [i, j], j > i
    C = np.zeros(N // 2 + 1)
    C[0] = 1.0
    for r in range(1, N // 2 + 1):
        vals = [CF[i, i + r] for i in range(N - r)]
        C[r] = np.real(np.mean(vals))
    return C


# ---------- fits ------------------------------------------------------------

def fit_forms(rs, C):
    out = {}

    def alg(r, A, eta):
        return A / r ** eta

    def osc(r, A, q, delta, eta):
        return A * np.cos(q * r + delta) / r ** eta

    try:
        p, _ = curve_fit(alg, rs, C, p0=[C[1], 0.5], maxfev=20000)
        rms = float(np.sqrt(np.mean((alg(rs, *p) - C) ** 2)))
        out["alg"] = {"A": float(p[0]), "eta": float(p[1]), "rms": rms}
    except Exception as e:
        out["alg"] = {"error": str(e)}
    best = None
    qmin = 2.0 * np.pi / rs[-1] / 2  # one full oscillation over the range
    for q0 in (qmin, 0.2, 0.5, 1.0, 2.0, 3.0):
        q0 = max(q0, qmin)
        try:
            p, _ = curve_fit(osc, rs, C, p0=[C[1], q0, 0.0, 0.5],
                             bounds=([-np.inf, qmin, -np.pi, 0],
                                     [np.inf, np.pi, np.pi, 5]),
                             maxfev=40000)
            rms = float(np.sqrt(np.mean((osc(rs, *p) - C) ** 2)))
            if best is None or rms < best[0]:
                best = (rms, p)
        except Exception:
            continue
    if best is not None:
        rms, p = best
        out["osc"] = {"A": float(p[0]), "q": float(p[1]),
                      "delta": float(p[2]), "eta": float(p[3]), "rms": rms}
    else:
        out["osc"] = {"error": "all starts failed"}
    out["sign_changes"] = int(np.sum(np.diff(np.sign(C)) != 0))
    out["min_C"] = float(np.min(C))
    out["monotone"] = bool(np.all(np.diff(C) <= 1e-12))
    return out


def main():
    results = {"ed": [], "dmrg": []}
    # ED: N=12 (all J on disk), N=16 (all J on disk after fill run)
    import os
    for N in (12, 16):
        for J in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0):
            f = f"psi_N{N}_J{J}.npy"
            if not os.path.exists(f):
                print(f"[skip] {f} missing", flush=True)
                continue
            psi = np.load(f)
            C = correlator_ed(psi, N)
            rs = np.arange(1, N // 2 + 1, dtype=float)
            rec = {"N": N, "J": J, "C": C.tolist(),
                   "fits": fit_forms(rs, C[1:])}
            results["ed"].append(rec)
            q = rec["fits"].get("osc", {}).get("q")
            print(f"[ed] N={N} J={J}: |C|(1..{N//2})="
                  f"{np.round(np.abs(C[1:]), 4)} q={q}", flush=True)
            json.dump(results, open(OUT, "w"), indent=1)
    # DMRG checkpoints
    import os
    for N in (18, 24, 32, 48):
        for J in (0.5, 1.5):
            if not os.path.exists(f"checkpoints/ckpt_N{N}_B{B}_J{J}.h5"):
                continue
            try:
                C = correlator_dmrg(N, J)
            except Exception as e:
                print(f"[dmrg] N={N} J={J} failed: {e}", flush=True)
                continue
            rs = np.arange(1, N // 2 + 1, dtype=float)
            rec = {"N": N, "J": J, "C": C.tolist(),
                   "fits": fit_forms(rs, C[1:])}
            results["dmrg"].append(rec)
            q = rec["fits"].get("osc", {}).get("q")
            print(f"[dmrg] N={N} J={J}: C(1..6)={np.round(C[1:7], 4)} q={q}",
                  flush=True)
            json.dump(results, open(OUT, "w"), indent=1)
    print("done", flush=True)


if __name__ == "__main__":
    main()
