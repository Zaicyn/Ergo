"""XXZ spin-1/2 chain plugin.

H = sum_i (Sx_i Sx_{i+1} + Sy_i Sy_{i+1} + Delta Sz_i Sz_{i+1}) + h sum_i Sz_i
periodic, S = 1/2. params: {"Delta": anisotropy, "h": field}.

SxSx + SySy = (1/2)(S+_i S-_{i+1} + S-_i S+_{i+1}): off-diagonal 1/2 between
anti-aligned neighbors. Sz|up> = +1/2, Sz|down> = -1/2 (bit 0 = down, 1 = up).

Built as a sparse matrix (2^N <= 2^14 is small); make_matvec wraps it,
make_dense emits it directly.
"""

import numpy as np
import scipy.sparse as sp

from .base import ModelBase


class XXZModel(ModelBase):
    name = "xxz"
    d_site = 2

    def _build_sparse(self, N, Delta, h):
        dim = 2 ** N
        idx = np.arange(dim, dtype=np.int64)
        diag = np.zeros(dim)
        rows, cols, vals = [], [], []
        for i in range(N):
            j = (i + 1) % N
            bi = (idx >> i) & 1
            bj = (idx >> j) & 1
            szi = bi.astype(float) - 0.5
            szj = bj.astype(float) - 0.5
            diag += Delta * szi * szj
            # flip-flop where anti-aligned
            flip = bi != bj
            src = idx[flip]
            dst = src ^ ((1 << i) | (1 << j))
            rows.append(dst)
            cols.append(src)
            vals.append(np.full(len(src), 0.5))
            if h != 0.0:
                diag += h * szi
        H = sp.coo_matrix(
            (np.concatenate(vals),
             (np.concatenate(rows), np.concatenate(cols))),
            shape=(dim, dim)).tocsr()
        H = H + sp.diags(diag)
        return H

    def make_matvec(self, N, params):
        H = self._build_sparse(N, params["Delta"], params.get("h", 0.0))
        return H.dot

    def make_dense(self, N, params):
        H = self._build_sparse(N, params["Delta"], params.get("h", 0.0))
        dim = 2 ** N
        if dim > 8000:
            raise ValueError(f"dim {dim} too large for dense emission")
        return H.toarray()

    def native_grid(self):
        return [{"Delta": round(-0.5 + 0.25 * k, 2), "h": 0.0}
                for k in range(11)]

    def validation_target(self):
        return {
            "ll_gap_closure": {"Delta": 0.5, "h": 0.0,
                               "Ns": [8, 10, 12, 14],
                               "expect": "gap ~ 1/N -> 0"},
            "ll_central_charge": {"Delta": 0.5, "h": 0.0, "Ns": [12, 14],
                                  "expect": "c = 1 +/- 0.05"},
            "ising_gapped": {"Delta": 2.0, "h": 0.0, "Ns": [8, 10, 12, 14],
                             "expect": "gap finite, does not close with N"},
        }

    def raise_lower(self):
        Sp = np.array([[0, 1], [0, 0]], dtype=complex)  # S+ |down> = |up>
        return Sp, Sp.T.copy()
