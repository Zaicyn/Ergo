"""Exact-diagonalization cross-check of the DMRG swap test.

H = -J sum_i (Sx_i Sx_{i+1} + Sy_i Sy_{i+1}) - h sum_i n_i.S_i, periodic.
Spin-1/2, J=200, h=1. Ground state via scipy eigsh (complex Hermitian).
"""
import sys
import time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import eigsh

from spin_swap import make_field

J = 200.0
h = 1.0


def build_H(n):
    N = len(n)
    dim = 1 << N
    rows, cols, vals = [], [], []
    # diagonal: -h * nz_i * Sz_i
    diag = np.zeros(dim)
    for s in range(dim):
        e = 0.0
        for i in range(N):
            sz = 0.5 if (s >> i) & 1 else -0.5
            e -= h * n[i, 2] * sz
        diag[s] = e
    # off-diagonal
    for s in range(dim):
        for i in range(N):
            # field x/y: -h (nx Sx + ny Sy), flips spin i
            t = s ^ (1 << i)
            up = (s >> i) & 1  # 1 = up
            # Sx amplitude 1/2; Sy: up->down +i/2, down->up -i/2
            amp = -h * (n[i, 0] * 0.5 + (1j * n[i, 1] * 0.5 if up else -1j * n[i, 1] * 0.5))
            # H[s,t] = <s|H|t> = conj(<t|H|s>) = conj(amp)
            rows.append(s); cols.append(t); vals.append(np.conj(amp))
            # exchange: -(J/2)(S+_i S-_j + S-_i S+_j), j = (i+1) % N
            j = (i + 1) % N
            if ((s >> i) & 1) != ((s >> j) & 1):
                t = s ^ (1 << i) ^ (1 << j)
                rows.append(s); cols.append(t); vals.append(-J / 2.0)
    H = coo_matrix((vals, (rows, cols)), shape=(dim, dim)).tocsr()
    H = H + coo_matrix((diag, (np.arange(dim), np.arange(dim))), shape=(dim, dim)).tocsr()
    return H


def ground_state(H, dim):
    # shift-invert not needed; smallest algebraic eigenvalue
    k = 4 if dim > 8 else dim - 1
    evals, evecs = eigsh(H, k=k, which='SA', tol=1e-12, maxiter=10000)
    order = np.argsort(evals)
    return evals[order], evecs[:, order]


def measure_mn(psi, n):
    N = len(n)
    dim = 1 << N
    m = np.zeros((N, 3))
    prob = np.abs(psi) ** 2
    for i in range(N):
        bit = 1 << i
        sz = np.where((np.arange(dim) & bit) != 0, 0.5, -0.5)
        m[i, 2] = np.sum(prob * sz)
        # <Sx>, <Sy> from coherences between s and s^bit
        idx = np.arange(dim)
        flipped = idx ^ bit
        coh = np.conj(psi) * psi[flipped]
        m[i, 0] = np.real(np.sum(coh * 0.5))  # Sx: 1/2 flip
        # Sy: <s|Sy|s^i> = -i/2 (up->down... use matrix elements)
        # Sy|up> = i/2|down>, Sy|down> = -i/2|up>
        # Sy|up> = i/2|down>, Sy|down> = -i/2|up>
        # <up|Sy|down> = -i/2, <down|Sy|up> = +i/2
        sy_elem = np.where((idx & bit) != 0, -0.5j, 0.5j)
        m[i, 1] = np.real(np.sum(coh * sy_elem))
    mn = np.sum(m * n, axis=1)
    return mn, m


def run(field, N):
    n = make_field(field, N)
    H = build_H(n)
    dim = 1 << N
    evals, evecs = ground_state(H, dim)
    gap = evals[1] - evals[0]
    psi = evecs[:, 0]
    mn, m = measure_mn(psi, n)
    return evals[0], gap, float(np.mean(mn)), float(np.var(mn)), mn


if __name__ == '__main__':
    Ns = [int(x) for x in sys.argv[1].split(',')] if len(sys.argv) > 1 else [12, 13, 14, 15, 16]
    out = open('results_ed.dat', 'a')
    for field in ['viviani', 'circle', 'trefoil', 'random']:
        for N in Ns:
            t0 = time.time()
            E, gap, mean_mn, var_mn, mn = run(field, N)
            dt = time.time() - t0
            out.write(f'{field} {N} {E:.10f} {gap:.3e} {mean_mn:.16e} {var_mn:.16e}\n')
            out.flush()
            print(f'ED {field:8s} N={N:2d} E={E:.6f} gap={gap:.2e} '
                  f'mean={mean_mn:.4e} var={var_mn:.3e} t={dt:.1f}s', flush=True)
    out.close()
