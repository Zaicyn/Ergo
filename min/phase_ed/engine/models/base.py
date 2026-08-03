"""Plugin interface for 1D local Hamiltonian models (phase-engine).

A model plugin supplies:
  name                str
  d_site              int, local Hilbert space dimension
  make_matvec(N, params) -> callable(v) -> H v   (LinearOperator-compatible)
  make_dense(N, params) -> ndarray               (only required for dim <= ~8000;
                                                  used by GPU-batched dense ED later)
  native_grid()       list of param dicts for a standard sweep
  validation_target() dict describing known-answer checks
  gauge_phases(N)     optional: per-flat-index phases of the on-site diagonal
                      gauge unitary used inside make_matvec (rotor uses a
                      twisted gauge); analysis untwists before correlators.
  raise_lower()       optional: (raise_op, lower_op) d_site x d_site arrays
                      for the correlator C(r) = <raise_i lower_j>.
"""

import numpy as np


class ModelBase:
    name = "base"
    d_site = 0

    def make_matvec(self, N, params):
        raise NotImplementedError

    def make_dense(self, N, params):
        mv = self.make_matvec(N, params)
        dim = self.d_site ** N
        if dim > 8000:
            raise ValueError(f"dim {dim} too large for dense emission")
        cols = [mv(np.eye(1, dim, k).ravel().astype(complex)).copy()
                for k in range(dim)]
        return np.column_stack(cols)

    def native_grid(self):
        raise NotImplementedError

    def validation_target(self):
        raise NotImplementedError

    def gauge_phases(self, N):
        return np.zeros(self.d_site ** N)

    def raise_lower(self):
        raise NotImplementedError
