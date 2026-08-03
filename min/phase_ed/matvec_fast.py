"""Optimized matvec for the spin-1 rotor chain (Part 2).

Gauge folding: U = exp(i sum_i ref_i p_i), ref_i = 2 pi i / N, transforms
  -K_PHASE cos(phi_i - ref_i) - B K_BIAS cos(phi_i - ref_i - pi)
    -> -V cos(phi_i),   V = K_PHASE - B*K_BIAS   (uniform, real)
  -J cos(phi_i - phi_{i+1})
    -> -(J/2)( e^{-i d} Tm_i Tp_{i+1} + e^{i d} Tp_i Tm_{i+1} ),  d = 2 pi/N
i.e. a uniform-field chain with a twisted bond. Unitarily equivalent, so the
spectrum is unchanged; validated below against gap_map.RotorChain at N=8,10.

Numba matvec over the base-3 digit representation of the flat index:
  out[x] = diag[x] v[x]
           - (V/2) sum_i [v[x-3^i] (d_i>=1) + v[x+3^i] (d_i<=1)]
           - (J/2) sum_bonds(i,j) [ e^{-id} v[x-3^i+3^j] (d_i>=1, d_j<=1)
                                    + e^{id} v[x+3^i-3^j] (d_i<=1, d_j>=1) ]
Preallocated out buffer; works for complex128 and complex64 inputs.
"""

import json
import time

import numpy as np
from numba import njit, prange

K_PHASE, K_BIAS = 0.5, 2.0


@njit(parallel=True, cache=True)
def _matvec_kernel(v, out, diag, p3, halfV, halfJc, halfJs, N):
    # bond coefficients: -(J/2) e^{-i d} = halfJc - i halfJs (and conjugate)
    dim = v.shape[0]
    for x in prange(dim):
        acc = diag[x] * v[x]
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
                acc += (-halfJc + 1j * halfJs) * v[x - p3[i] + p3[j]]
            if di <= 1 and dj >= 1:
                acc += (-halfJc - 1j * halfJs) * v[x + p3[i] - p3[j]]
        out[x] = acc


class FastChain:
    """Gauge-folded rotor chain with a numba matvec."""

    def __init__(self, N, B, J, cdtype=np.complex128):
        self.N, self.B, self.J = N, B, J
        self.DIM = 3 ** N
        self.cdtype = cdtype
        V = K_PHASE - B * K_BIAS
        delta = 2.0 * np.pi / N
        self.halfV = V / 2.0
        self.halfJc = (J / 2.0) * np.cos(delta)
        self.halfJs = (J / 2.0) * np.sin(delta)
        self.p3 = (3 ** np.arange(N)).astype(np.int64)
        # kinetic diagonal sum_i m_i^2 / 2
        idx = np.arange(self.DIM, dtype=np.int64)
        diag = np.zeros(self.DIM)
        for i in range(N):
            mi = (idx // self.p3[i]) % 3 - 1
            diag += (mi * mi) / 2.0
        self.diag = diag
        self.buf = np.empty(self.DIM, dtype=cdtype)

    def matvec(self, v):
        out = self.buf
        _matvec_kernel(v, out, self.diag, self.p3, self.halfV,
                       self.halfJc, self.halfJs, self.N)
        return out


def eigsh_fc(fc, k=4, tol=1e-12, v0=None, ncv=None, maxiter=20000):
    from scipy.sparse.linalg import LinearOperator, eigsh
    kw = dict(k=k, which="SA", tol=tol, maxiter=maxiter, v0=v0)
    if ncv is not None:
        kw["ncv"] = ncv
    A = LinearOperator((fc.DIM, fc.DIM), matvec=fc.matvec, dtype=fc.cdtype)
    evals, evecs = eigsh(A, **kw)
    order = np.argsort(evals)
    return evals[order], evecs[:, order]


def main():
    from gap_map import RotorChain
    from scipy.sparse.linalg import LinearOperator, eigsh
    rep = {}

    # --- gauge-folding spectrum check vs original Hamiltonian --------------
    for N in (8, 10):
        for B, J in [(0.25, 1.0), (0.5, 0.5)]:
            old = RotorChain(N, 1, drift=False)
            A_old = LinearOperator((old.DIM, old.DIM),
                                   matvec=old.make_matvec(B, J), dtype=complex)
            ev_old = np.sort(eigsh(A_old, k=4, which="SA", tol=1e-12,
                                   maxiter=5000)[0])
            ev_new, _ = eigsh_fc(FastChain(N, B, J), k=4, tol=1e-12)
            d = float(np.max(np.abs(ev_old - ev_new)))
            rep[f"gauge_N{N}_B{B}_J{J}"] = d
            print(f"gauge check N={N} B={B} J={J}: max|dE|={d:.2e}",
                  flush=True)

    # --- benchmark: old python-tensor matvec vs numba ----------------------
    for N in (12, 14):
        fc = FastChain(N, 0.25, 1.0)
        v = np.random.default_rng(0).standard_normal(fc.DIM) + 0j
        # numba warm
        fc.matvec(v); fc.matvec(v)
        reps = 20 if N == 12 else 5
        t0 = time.time()
        for _ in range(reps):
            fc.matvec(v)
        t_new = (time.time() - t0) / reps
        old = RotorChain(N, 1, drift=False)
        mv_old = old.make_matvec(0.25, 1.0)
        mv_old(v)
        t0 = time.time()
        mv_old(v)
        t_old = time.time() - t0
        rep[f"bench_N{N}"] = {"old_s": t_old, "new_s": t_new,
                              "old_mv_per_s": 1 / t_old,
                              "new_mv_per_s": 1 / t_new,
                              "speedup": t_old / t_new}
        print(f"N={N}: old {1/t_old:.2f} mv/s, numba {1/t_new:.2f} mv/s "
              f"({t_old/t_new:.1f}x)", flush=True)

    # --- eigsh validation at N=12 vs old path ------------------------------
    ev_old = np.sort(eigsh(LinearOperator(
        (3 ** 12, 3 ** 12),
        matvec=RotorChain(12, 1, drift=False).make_matvec(0.25, 1.0),
        dtype=complex), k=4, which="SA", tol=1e-12, maxiter=5000)[0])
    ev_new, _ = eigsh_fc(FastChain(12, 0.25, 1.0), k=4, tol=1e-12)
    rep["eigsh_val_N12_dE0"] = float(abs(ev_old[0] - ev_new[0]))
    rep["eigsh_val_N12_dgap"] = float(abs((ev_old[1] - ev_old[0])
                                          - (ev_new[1] - ev_new[0])))
    print("N=12 eigsh: dE0=%.2e dgap=%.2e" % (rep["eigsh_val_N12_dE0"],
                                              rep["eigsh_val_N12_dgap"]),
          flush=True)

    # --- complex64 precision check at N=12 ---------------------------------
    fc64 = FastChain(12, 0.25, 1.0, cdtype=np.complex64)
    ev64, _ = eigsh_fc(fc64, k=2, tol=1e-7, ncv=12)
    gap128 = ev_new[1] - ev_new[0]
    gap64 = ev64[1] - ev64[0]
    rep["c64_gap_err_N12"] = float(abs(gap64 - gap128))
    rep["c64_E0_err_N12"] = float(abs(ev64[0] - ev_new[0]))
    rep["c64_pass"] = bool(abs(gap64 - gap128) < 1e-6)
    print("complex64 N=12: gap err=%.2e E0 err=%.2e pass=%s"
          % (rep["c64_gap_err_N12"], rep["c64_E0_err_N12"], rep["c64_pass"]),
          flush=True)

    # --- memory footprints -------------------------------------------------
    for N in (16, 18):
        dim = 3 ** N
        rep[f"mem_N{N}"] = {
            "states": dim,
            "vec_complex128_GB": dim * 16 / 1e9,
            "vec_complex64_GB": dim * 8 / 1e9,
            "krylov20_c128_GB": dim * 16 * 20 / 1e9,
            "krylov8_c64_GB": dim * 8 * 8 / 1e9,
        }
        print(f"N={N}: {dim} states, c128 vec "
              f"{dim*16/1e9:.2f} GB, c64 vec {dim*8/1e9:.2f} GB", flush=True)

    with open("matvec_fast_report.json", "w") as f:
        json.dump(rep, f, indent=1)
    print("wrote matvec_fast_report.json", flush=True)


if __name__ == "__main__":
    main()


@njit(parallel=True, cache=True)
def _dense_kernel(H, diag, p3, halfV, halfJc, halfJs, N):
    dim = diag.shape[0]
    for x in prange(dim):
        H[x, x] += diag[x]
        for i in range(N):
            pi = p3[i]
            d = (x // pi) % 3
            if d >= 1:
                H[x, x - pi] -= halfV
            if d <= 1:
                H[x, x + pi] -= halfV
        for i in range(N):
            j = i + 1
            if j == N:
                j = 0
            di = (x // p3[i]) % 3
            dj = (x // p3[j]) % 3
            if di >= 1 and dj <= 1:
                H[x, x - p3[i] + p3[j]] += (-halfJc + 1j * halfJs)
            if di <= 1 and dj >= 1:
                H[x, x + p3[i] - p3[j]] += (-halfJc - 1j * halfJs)


def fastchain_to_dense(fc):
    """Dense gauge-folded Hamiltonian in one O(dim*N) pass (numba)."""
    H = np.zeros((fc.DIM, fc.DIM), dtype=np.complex128)
    _dense_kernel(H, fc.diag, fc.p3, fc.halfV, fc.halfJc, fc.halfJs, fc.N)
    return H
