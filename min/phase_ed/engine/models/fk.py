"""Quantum Frenkel-Kontorova plugin (pendulum form).

H = sum_i p_i^2/(2I) - J sum_i cos(phi_{i+1} - phi_i) - V sum_i cos(q phi_i)
spin-1 rotors, I = 1. This is the coupled-pendula (quantum sine-Gordon)
form of the Frenkel-Kontorova model: structurally the rotor chain with a
UNIFORM q-fold substrate field instead of the rotor plugin's helical
single-harmonic drive. No gauge twist is needed (onsite field is uniform).

Native params: V (substrate depth), J (coupling), q (commensuration, int).
NOTE (basis truncation): <m+-q|cos(q phi)|m> needs |m+-q| <= 1, so the
substrate term is nonzero only for q = 1 (m<->m±1) and q = 2 (m=-1<->m=+1);
for q >= 3 it vanishes identically in the spin-1 basis (like the rotor
cos(3phi) drift). q >= 3 is accepted but flagged in validation_target.
"""

import numpy as np
from numba import njit, prange

from .base import ModelBase


@njit(parallel=True, cache=True)
def _fk_kernel(v, out, diag, p3, halfV1, halfV2, halfJ, N):
    dim = v.shape[0]
    for x in prange(dim):
        acc = diag[x] * v[x]
        digits = np.empty(N, np.int64)
        for i in range(N):
            pi = p3[i]
            d = (x // pi) % 3
            digits[i] = d
            # -V cos(phi_i) (q=1): <m+-1|cos phi|m> = 1/2
            if halfV1 != 0.0:
                if d >= 1:
                    acc -= halfV1 * v[x - pi]
                if d <= 1:
                    acc -= halfV1 * v[x + pi]
            # -V cos(2 phi_i) (q=2): <m+-2|cos 2phi|m> = 1/2 (m=-1 <-> m=+1)
            if halfV2 != 0.0:
                if d == 0:
                    acc -= halfV2 * v[x + 2 * pi]
                if d == 2:
                    acc -= halfV2 * v[x - 2 * pi]
        for i in range(N):
            j = i + 1
            if j == N:
                j = 0
            di = digits[i]
            dj = digits[j]
            # -J cos(phi_i - phi_j) = -(J/2)(Tm_i Tp_j + Tp_i Tm_j), real
            if di >= 1 and dj <= 1:
                acc -= halfJ * v[x - p3[i] + p3[j]]
            if di <= 1 and dj >= 1:
                acc -= halfJ * v[x + p3[i] - p3[j]]
        out[x] = acc


class FKModel(ModelBase):
    name = "fk_pendulum"
    d_site = 3

    def make_matvec(self, N, params):
        V, J, q = params["V"], params["J"], int(params.get("q", 1))
        # arena matvec is the engine default; roll-decode fallback below.
        if params.get("impl", "arena") == "arena" and q in (1, 2):
            from index_arena import ArenaMatvec
            return ArenaMatvec(N, J=J, mode=q, V=V).matvec
        dim = 3 ** N
        p3 = (3 ** np.arange(N)).astype(np.int64)
        idx = np.arange(dim, dtype=np.int64)
        diag = np.zeros(dim)
        for i in range(N):
            mi = (idx // p3[i]) % 3 - 1
            diag += (mi * mi) / 2.0
        buf = np.empty(dim, dtype=np.complex128)
        halfV1 = V / 2.0 if q == 1 else 0.0
        halfV2 = V / 2.0 if q == 2 else 0.0
        halfJ = J / 2.0

        def matvec(vec):
            _fk_kernel(vec, buf, diag, p3, halfV1, halfV2, halfJ, N)
            return buf

        return matvec

    def native_grid(self):
        return [{"V": round(0.25 * k, 2), "J": 1.0, "q": 1}
                for k in range(9)]

    def validation_target(self):
        return {"gate": "q=1, I=1, J=1: V=0 closes as 1/N (free-rotor LL); "
                        "V=2 pinned, gap does not close (N=8,10,12)",
                "q_ge_3_caveat": "substrate term vanishes in spin-1 basis "
                                 "for q >= 3"}

    def raise_lower(self):
        Tp = np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=complex)
        return Tp.T.copy(), Tp
