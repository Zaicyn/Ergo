#!/usr/bin/env python3
"""ed_ref.py — reference for the Inc-2B matrix-free Ergo ED matvec.

Original-gauge spin-1 rotor chain (the stage0 form — NOT the gauge-folded
matvec_fast.py version; spectra coincide, vectors don't):

  H = sum_i m_i^2/2  - V sum_i cos(phi_i)  - J sum_i cos(phi_i - phi_{i+1})

with V = K_PHASE - B*K_BIAS = 0 at the B=0.25 oracle point. Matvec in
base-3 digit form (d_i = (x // 3^i) % 3, m_i = d_i - 1):

  out[x] = (diag[x] - SHIFT) v[x]
           - halfV sum_i [v[x-3^i] (d_i>=1) + v[x+3^i] (d_i<=1)]
           - halfJ sum_i [v[x-3^i+3^j] (d_i>=1, d_j<=1)
                        + v[x+3^i-3^j] (d_i<=1, d_j>=1)],  j = i+1 mod N

Seed must match the Ergo program exactly:
  V(X) := 0.5 + REAL(MOD(X, 9973)) * 0.0001   (1-based X)

Outputs (JSON): per N, matvec checksums/probes at the seed and E0 from
scipy eigsh on the same matvec.
"""
import json
import sys
import numpy as np
from numba import njit, prange

K_PHASE, K_BIAS = 0.5, 2.0
B, J = 0.25, 1.0

def SHIFT(N):
    return 2.0 * N


@njit(parallel=True, cache=True)
def _matvec(v, out, p3, diag, halfV, halfJ, SH, N):
    dim = v.shape[0]
    for x in prange(dim):
        acc = (diag[x] - SH) * v[x]
        digits = np.empty(N, np.int64)
        for i in range(N):
            pi = p3[i]
            d = (x // pi) % 3
            digits[i] = d
            if d >= 1:
                acc -= halfV * v[x - pi]
            if d <= 1:
                acc -= halfV * v[x + pi]
        for i in range(N):
            j = i + 1
            if j == N:
                j = 0
            di = digits[i]
            dj = digits[j]
            if di >= 1 and dj <= 1:
                acc -= halfJ * v[x - p3[i] + p3[j]]
            if di <= 1 and dj >= 1:
                acc -= halfJ * v[x + p3[i] - p3[j]]
        out[x] = acc


def make(N):
    dim = 3 ** N
    p3 = (3 ** np.arange(N)).astype(np.int64)
    idx = np.arange(dim, dtype=np.int64)
    diag = np.zeros(dim)
    for i in range(N):
        mi = (idx // p3[i]) % 3 - 1
        diag += (mi * mi) / 2.0
    V = K_PHASE - B * K_BIAS
    return dim, p3, diag, V / 2.0, J / 2.0


def seed(dim):
    x = np.arange(1, dim + 1, dtype=np.int64)
    return 0.5 + (x % 9973).astype(np.float64) * 0.0001


def matvec(N, v):
    dim, p3, diag, halfV, halfJ = make(N)
    out = np.empty(dim)
    _matvec(v, out, p3, diag, halfV, halfJ, SHIFT(N), N)
    return out


def checksums(w):
    x = np.arange(w.shape[0], dtype=np.int64)
    return {
        "c1": float(w.sum()),
        "c2": float((w * (1 + (x + 1) % 7)).sum()),
        "w0": float(w[0]),
        "wmid": float(w[w.shape[0] // 2]),
        "wlast": float(w[-1]),
    }


def e0(N):
    dim, p3, diag, halfV, halfJ = make(N)
    from scipy.sparse.linalg import LinearOperator, eigsh
    def mv(v):
        out = np.empty(dim)
        _matvec(v, out, p3, diag, halfV, halfJ, SHIFT(N), N)
        return out
    A = LinearOperator((dim, dim), matvec=mv, dtype=np.float64)
    ev = eigsh(A, k=1, which="SA", tol=1e-12, maxiter=5000,
               v0=seed(dim))[0]
    # mv above INCLUDES the -SHIFT shift (power-iteration
    # form); the physical E0 adds SHIFT back.
    return float(ev[0] + SHIFT(N))


def main():
    rep = {}
    for N in (8, 14):
        v = seed(3 ** N)
        w = matvec(N, v)
        rep[f"N{N}_matvec"] = checksums(w)
        print(f"N={N} matvec: {rep[f'N{N}_matvec']}", flush=True)
    for N in (8, 14, 16):
        e = e0(N)
        rep[f"N{N}_E0"] = e
        print(f"N={N}: E0 = {e:.12f}", flush=True)
    with open("min/phase_ed/ed_ref_report.json", "w") as f:
        json.dump(rep, f, indent=1)
    print("wrote min/phase_ed/ed_ref_report.json", flush=True)


if __name__ == "__main__":
    main()


def e0_power(N, niter=3000, tol=1e-12):
    """Memory-safe reference E0: plain power iteration on H~ = H - 2N*I
    (two vectors only — NO scipy eigsh; its default ncv=20 Krylov
    workspace is 20 x dim x 16 bytes and OOMed the host at N=17).
    Same algorithm/shift as the Ergo binary, deterministic seed."""
    dim, p3, diag, halfV, halfJ = make(N)
    sh = SHIFT(N)
    v = seed(dim)
    w = matvec(N, v)
    nrm = np.linalg.norm(w)
    v = w / nrm
    rho_old = 0.0
    rho = 0.0
    used = niter
    for it in range(1, niter + 1):
        out = np.empty(dim)
        _matvec(v, out, p3, diag, halfV, halfJ, sh, N)
        rho = float(v @ out)
        nrm = np.linalg.norm(out)
        v = out / nrm
        if abs(rho - rho_old) < tol:
            used = it
            break
        rho_old = rho
    return rho + sh, used


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "power":
    N = int(sys.argv[2])
    e, it = e0_power(N)
    print(f"N={N} power: E0 = {e:.12f}  iters {it}", flush=True)
    rep = {}
    import os
    if os.path.exists("min/phase_ed/ed_ref_report.json"):
        rep = json.load(open("min/phase_ed/ed_ref_report.json"))
    rep[f"N{N}_E0_power"] = e
    json.dump(rep, open("min/phase_ed/ed_ref_report.json", "w"), indent=1)
    print("updated ed_ref_report.json", flush=True)
