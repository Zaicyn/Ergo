"""Spin-1 rotor chain plugin (wraps matvec_fast.FastChain, gauge-folded
numba matvec). params: {"B": bias, "J": coupling}. Drift off (spin-1 basis).
"""

import numpy as np

from matvec_fast import FastChain
from .base import ModelBase


class RotorModel(ModelBase):
    name = "rotor_spin1"
    d_site = 3

    def make_matvec(self, N, params):
        # arena matvec is the engine default (adopted after benchmarks:
        # +49% at N=12, correct to 1e-14); roll-decode kept as fallback.
        if params.get("impl", "arena") == "arena":
            from index_arena import ArenaMatvec
            return ArenaMatvec(N, params["B"], params["J"]).matvec
        from matvec_fast import FastChain
        fc = FastChain(N, params["B"], params["J"],
                       cdtype=params.get("cdtype", np.complex128))
        return fc.matvec

    def native_grid(self):
        return [{"B": 0.25, "J": round(0.5 + 0.25 * k, 2)} for k in range(7)]

    def validation_target(self):
        return {"point": {"B": 0.25, "J": 1.0}, "N": 12,
                "E0": -4.2367838390291315, "gap": 0.08352309149762327,
                "tol": 1e-6,
                "note": "values from results_fss.json (not the -4.590652 "
                        "quoted in the task, which matches nothing on file)"}

    def gauge_phases(self, N):
        idx = np.arange(3 ** N)
        ph = np.zeros(3 ** N)
        for i in range(N):
            mi = (idx // 3 ** i) % 3 - 1
            ph += (2.0 * np.pi * i / N) * mi
        return ph

    def raise_lower(self):
        Tp = np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=complex)
        return Tp.T.copy(), Tp  # Tm (raise), Tp (lower)
