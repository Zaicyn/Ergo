"""Rydberg chain plugin with blockade constraint.

H = (Omega/2) sum_i sx_i - delta sum_i n_i + V sum_i n_i n_{i+1},  periodic,
in the blockade-constrained Hilbert space: binary strings with no adjacent
excitations (n_i n_{i+1} = 0 everywhere, including the wrap bond). Basis
dimension is the Lucas number L_N (322 at N=12, 843 at N=14, 2207 at N=16).

HONEST NOTE: with the strict blockade imposed, n_i n_{i+1} = 0 on every
basis state, so the V term vanishes identically in this sector — the model
reduces to the detuned PXP form (Omega/2) sum sx - delta sum n. V is kept
as a native parameter (it matters if the constraint is relaxed), but does
nothing here. Omega = 1 fixed; native params: delta (detuning), V.
"""

import itertools
from functools import lru_cache

import numpy as np

from .base import ModelBase


@lru_cache(maxsize=None)
def constrained_states(N):
    """Periodic binary strings with no adjacent 1s (incl. wrap)."""
    states = []
    for bits in itertools.product((0, 1), repeat=N):
        ok = True
        for i in range(N):
            if bits[i] and bits[(i + 1) % N]:
                ok = False
                break
        if ok:
            x = 0
            for i, b in enumerate(bits):
                x |= b << i
            states.append(x)
    return states


class RydbergModel(ModelBase):
    name = "rydberg_blockade"
    d_site = 2  # constrained space is smaller; d_site used only for reshape
                  # analyses that need (d,)*N -- see constrained note below

    def basis(self, N):
        return constrained_states(N)

    def make_matvec(self, N, params):
        delta, V = params["Delta"], params.get("V", 1.0)
        Omega = params.get("Omega", 1.0)
        st = self.basis(N)
        index = {x: k for k, x in enumerate(st)}
        dim = len(st)
        diag = np.zeros(dim)
        rows, cols, vals = [], [], []
        for k, x in enumerate(st):
            n = bin(x).count("1")
            diag[k] = -delta * n
            # V * sum n_i n_{i+1}: identically 0 on the constrained basis
            for i in range(N):
                y = x ^ (1 << i)
                k2 = index.get(y)
                if k2 is not None:
                    rows.append(k2)
                    cols.append(k)
                    vals.append(Omega / 2.0)
        import scipy.sparse as sp
        H = sp.coo_matrix((vals, (rows, cols)), shape=(dim, dim)).tocsr()
        H = H + sp.diags(diag)
        return H.dot

    def make_dense(self, N, params):
        import scipy.sparse.linalg  # noqa
        mv = self.make_matvec(N, params)
        dim = len(self.basis(N))
        cols = [mv(np.eye(1, dim, k).ravel()).copy() for k in range(dim)]
        return np.column_stack(cols)

    def native_grid(self):
        return [{"Delta": round(0.25 * k, 2), "V": 1.0} for k in range(13)]

    def validation_target(self):
        return {"gate": "V=1, Omega=1, delta in [0,3] at N=12,14,16: locate "
                        "Z2-ordered region (large delta), find transition, "
                        "c ~ 0.5 there (Ising), c ~ 1 only if an "
                        "intermediate LL resolves",
                "must_not": "report c=1 everywhere"}

    def embed(self, psi, N):
        """Lift a constrained-space vector into the full 2^N product space
        (zeros on excluded strings) so tensor-reshape analyses apply."""
        full = np.zeros(2 ** N, dtype=complex)
        for k, x in enumerate(self.basis(N)):
            full[x] = psi[k]
        return full

    def staggered_occupation(self, psi, N):
        """Z2 order parameter m_s = |1/N sum_i (-1)^i <n_i>|."""
        st = self.basis(N)
        p2 = np.abs(psi) ** 2
        ms = 0.0
        for k, x in enumerate(st):
            s = 0.0
            for i in range(N):
                s += ((-1) ** i) * ((x >> i) & 1)
            ms += p2[k] * s
        return float(abs(ms) / N)

    def raise_lower(self):
        Sp = np.array([[0, 1], [0, 0]], dtype=complex)
        return Sp, Sp.T.copy()
