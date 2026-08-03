"""Milestone A: allocator-inspired matvec optimizations (CPU, numba).

A1: INDEX-MAP ARENA. Per (model, N) precompute a gather formulation of the
matvec: out[x] = diag[x] v[x] + sum_t lut[cid[x,t]] * v[src[x,t]].
All source indices live in ONE contiguous int32 arena (dim x T, T = 6N
padded, -1 = absent), coefficient IDs (uint8) index a small LUT (V22
pattern: coefficients precomputed, never rebuilt). One arena allocation,
zero per-term allocations.

A2: Z-ORDER BASIS LAYOUT. Site trit at significance sigma(i) with sigma a
Morton-style interleave of the ring index; the arena is built directly in
the permuted labeling, so a fully-permuted workflow (eigsh internal to the
permutation) costs zero extra per matvec. Eigenvalues are
permutation-invariant; correctness gate vs the natural-order path.

Benchmarks in bench_alloc.py.
"""

import numpy as np
from numba import njit, prange

from matvec_fast import FastChain

T_PER_X = 6  # max terms per site (2 onsite + 4 bond-partner)


@njit(parallel=True, cache=True)
def _arena_build(src, cid, p3, N, T, mode):
    """mode 0: rotor (onsite +-1 trit cid=1, bonds cid=2/3 complex pair)
    mode 1: FK q=1 (onsite +-1 cid=1, bonds real cid=2)
    mode 2: FK q=2 (onsite +-2 trits cid=1, bonds real cid=2)"""
    dim = src.shape[0]
    for x in prange(dim):
        t = 0
        digits = np.empty(N, np.int64)
        for i in range(N):
            pi = p3[i]
            d = (x // pi) % 3
            digits[i] = d
            if mode == 2:
                if d == 0:
                    src[x, t] = x + 2 * pi
                    cid[x, t] = 1
                    t += 1
                if d == 2:
                    src[x, t] = x - 2 * pi
                    cid[x, t] = 1
                    t += 1
            else:
                if d >= 1:
                    src[x, t] = x - pi
                    cid[x, t] = 1
                    t += 1
                if d <= 1:
                    src[x, t] = x + pi
                    cid[x, t] = 1
                    t += 1
        for i in range(N):
            j = i + 1
            if j == N:
                j = 0
            di = digits[i]
            dj = digits[j]
            if mode == 0:
                if di >= 1 and dj <= 1:
                    src[x, t] = x - p3[i] + p3[j]
                    cid[x, t] = 2
                    t += 1
                if di <= 1 and dj >= 1:
                    src[x, t] = x + p3[i] - p3[j]
                    cid[x, t] = 3
                    t += 1
            else:
                if di >= 1 and dj <= 1:
                    src[x, t] = x - p3[i] + p3[j]
                    cid[x, t] = 2
                    t += 1
                if di <= 1 and dj >= 1:
                    src[x, t] = x + p3[i] - p3[j]
                    cid[x, t] = 2
                    t += 1
        # remaining slots stay -1 / 0 (sentinel: lut[0] = 0)


@njit(parallel=True, cache=True)
def _arena_mv(v, out, src, cid, lut, diag):
    dim, T = src.shape
    for x in prange(dim):
        acc = diag[x] * v[x]
        for t in range(T):
            s = src[x, t]
            if s >= 0:
                acc += lut[cid[x, t]] * v[s]
        out[x] = acc


def morton_sigma(N):
    """Z-curve significance assignment for the ring: interleave the two
    halves so adjacent sites tend to adjacent significances on both ends.
    sigma[i] = significance of site i in the permuted labeling."""
    order = []
    lo, hi = 0, N - 1
    while lo <= hi:
        order.append(lo)
        lo += 1
        if lo <= hi:
            order.append(hi)
            hi -= 1
    sigma = np.empty(N, dtype=np.int64)
    for sig, site in enumerate(order):
        sigma[site] = sig
    return sigma


class ArenaMatvec:
    """Gather-arena matvec for the gauge-folded rotor chain (mode=0) and
    the FK pendulum chain (mode=1 for q=1, mode=2 for q=2)."""

    def __init__(self, N, B=0.25, J=1.0, sigma=None, mode=0, V=None):
        self.N = N
        self.mode = mode
        T = T_PER_X * N
        p3 = (3 ** np.arange(N)).astype(np.int64)
        idx = np.arange(3 ** N, dtype=np.int64)
        self.DIM = 3 ** N
        diag = np.zeros(self.DIM)
        if sigma is not None:
            p3 = (3 ** sigma).astype(np.int64)
        for i in range(N):
            mi = (idx // p3[i]) % 3 - 1
            diag += (mi * mi) / 2.0
        self.diag = diag
        src = np.full((self.DIM, T), -1, dtype=np.int32)
        cid = np.zeros((self.DIM, T), dtype=np.uint8)
        _arena_build(src, cid, p3, N, T, mode)
        self.arena = np.ascontiguousarray(src)
        self.cid = np.ascontiguousarray(cid)
        self.offsets = np.arange(self.DIM + 1, dtype=np.int64) * T
        if mode == 0:
            fc = FastChain(N, B, J)
            self.lut = np.array(
                [0j, -fc.halfV, -fc.halfJc + 1j * fc.halfJs,
                 -fc.halfJc - 1j * fc.halfJs], dtype=np.complex128)
        else:
            self.lut = np.array([0j, -(V / 2.0), -(J / 2.0), 0j],
                                dtype=np.complex128)
        self.buf = np.empty(self.DIM, dtype=np.complex128)

    def matvec(self, v):
        _arena_mv(v, self.buf, self.arena, self.cid, self.lut, self.diag)
        return self.buf
