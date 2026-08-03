"""Central charge from bipartite entanglement entropy (universality check).

Ground states at B=0.25, J in {0.5 (gapped control), 1.0, 1.5, 2.0}:
  N=12: complex128, tol=1e-12;  N=16: complex64, k=2, ncv=8, tol=1e-6.
Per point: Lanczos residual ||H v - E v|| + converged flag (> 1e-5 =
questionable), eigenvector saved to psi_N{N}_J{J}.npy.

Entropy: reshape to (3,)*N, cut ell=1..N/2, SVD, S = -sum p log p.
Tensor axis k corresponds to ring site N-1-k (C-order vs base-3 digits);
cuts are still contiguous ring segments, and S(ell) is reflection symmetric.

GAUGE CHECK: N=16 machinery uses the twisted gauge H' = U H U+,
U = exp(i sum ref_i p_i) (on-site diagonal). Entanglement must be identical;
verified explicitly at N=12 (S in twisted gauge vs after U+) and reported.

Fit: S(ell) = (c/3) log[(N/pi) sin(pi ell/N)] + const, ell = 1..N/2.
"""

import json
import time

import numpy as np

from matvec_fast import FastChain, eigsh_fc

B = 0.25
JS_N16 = [0.5, 1.5, 1.0, 2.0]      # priority order
JS_N12 = [0.5, 1.0, 1.5, 2.0]
OUT = "results_entanglement.json"


def entropy_profile(psi, N):
    t = psi.reshape((3,) * N)
    S = {}
    for ell in range(1, N // 2 + 1):
        M = t.reshape(3 ** ell, 3 ** (N - ell))
        s = np.linalg.svd(M, compute_uv=False)
        p = s ** 2
        p = p[p > 1e-15]
        S[ell] = float(-np.sum(p * np.log(p)))
    return S


def gauge_phases(N):
    idx = np.arange(3 ** N)
    ph = np.zeros(3 ** N)
    for i in range(N):
        mi = (idx // 3 ** i) % 3 - 1
        ph += (2.0 * np.pi * i / N) * mi
    return ph


def fit_cc(S, N):
    ells = np.array(sorted(S), dtype=float)
    x = np.log((N / np.pi) * np.sin(np.pi * ells / N))
    y = np.array([S[int(e)] for e in ells])
    A = np.vstack([x, np.ones_like(x)]).T
    (c3, const), res, *_ = np.linalg.lstsq(A, y, rcond=None)
    yfit = A @ [c3, const]
    rms = float(np.sqrt(np.mean((y - yfit) ** 2)))
    # 1-sigma error on slope from residuals
    dof = max(len(x) - 2, 1)
    cov = np.sum((y - yfit) ** 2) / dof * np.linalg.inv(A.T @ A)[0, 0]
    return {"c": float(3 * c3), "c_err": float(3 * np.sqrt(cov)),
            "const": float(const), "rms": rms}


def run_point(N, J, c128):
    fc = FastChain(N, B, J, cdtype=np.complex128 if c128 else np.complex64)
    t0 = time.time()
    evals, evecs = eigsh_fc(fc, k=2, tol=1e-12 if c128 else 1e-6,
                            ncv=None if c128 else 8, maxiter=8000)
    psi = evecs[:, 0].copy()
    E0 = float(evals[0])
    gap = float(evals[1] - evals[0])
    res = float(np.linalg.norm(fc.matvec(psi).copy() - E0 * psi))
    np.save(f"psi_N{N}_J{J}.npy", psi)
    S = entropy_profile(psi, N)
    rec = {"N": N, "B": B, "J": J, "E0": E0, "gap": gap,
           "residual": res, "converged": bool(res <= 1e-5),
           "seconds": time.time() - t0, "S": S, "fit": fit_cc(S, N)}
    print(f"[pt] N={N} J={J} E0={E0:.6f} gap={gap:.6f} res={res:.2e} "
          f"c={rec['fit']['c']:.3f}+-{rec['fit']['c_err']:.3f} "
          f"rms={rec['fit']['rms']:.2e} ({rec['seconds']:.0f}s)", flush=True)
    return rec


def main():
    results = {"points": []}
    # gauge check at N=12 (twisted vs U^dagger-rotated)
    N = 12
    fc = FastChain(N, B, 1.0)
    evals, evecs = eigsh_fc(fc, k=2, tol=1e-12, maxiter=8000)
    psi_tw = evecs[:, 0].copy()
    Udag = np.exp(-1j * gauge_phases(N))
    psi_un = Udag * psi_tw
    dS = max(abs(a - b) for a, b in zip(
        entropy_profile(psi_tw, N).values(),
        entropy_profile(psi_un, N).values()))
    results["gauge_check_N12_max_dS"] = dS
    print(f"[gauge] max |dS| twisted vs U+ rotated at N=12: {dS:.2e}",
          flush=True)
    with open(OUT, "w") as f:
        json.dump(results, f, indent=1)

    for J in JS_N12:
        results["points"].append(run_point(12, J, c128=True))
        with open(OUT, "w") as f:
            json.dump(results, f, indent=1)
    for J in JS_N16:
        results["points"].append(run_point(16, J, c128=False))
        with open(OUT, "w") as f:
            json.dump(results, f, indent=1)
    print("done", flush=True)


if __name__ == "__main__":
    main()
