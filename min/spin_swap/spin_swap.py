"""Swap test: spin-1/2 XY chain with site-dependent transverse field patterns.

Hamiltonian: H = -J sum_<ij> (Sx_i Sx_j + Sy_i Sy_j) - h sum_i n_i . S_i
J=200, h=1, periodic chain. Measures per-site m_i . n_i and its variance.

Fields: viviani, circle, trefoil, random
"""
import sys
import time
import logging
import numpy as np

logging.disable(logging.WARNING)

from tenpy.models.model import CouplingMPOModel
from tenpy.networks.site import SpinHalfSite
from tenpy.networks.mps import MPS
from tenpy.algorithms import dmrg
from tenpy.models.lattice import Chain


def make_field(field, N):
    if field == 'viviani':
        t = 4.0 * np.pi * np.arange(N) / N
        n = np.stack([np.sin(t) - 0.5 * np.sin(3 * t),
                      -np.cos(t) + 0.5 * np.cos(3 * t),
                      np.cos(t) * np.cos(3 * t)], axis=1)
    elif field == 'circle':
        t = 4.0 * np.pi * np.arange(N) / N
        n = np.stack([np.cos(t), np.sin(t), np.zeros(N)], axis=1)
    elif field == 'trefoil':
        t = 2.0 * np.pi * np.arange(N) / N
        n = np.stack([np.sin(t) + 2.0 * np.sin(2 * t),
                      np.cos(t) - 2.0 * np.cos(2 * t),
                      -np.sin(3 * t)], axis=1)
    elif field == 'random':
        n = np.random.default_rng(42).normal(size=(N, 3))
    else:
        raise ValueError(field)
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    return n


class FieldXY(CouplingMPOModel):
    def init_sites(self, model_params):
        return SpinHalfSite(conserve=None)

    def init_lattice(self, model_params):
        L = model_params.get('L', 50)
        site = self.init_sites(model_params)
        return Chain(L, site, bc='periodic')

    def init_terms(self, model_params):
        J = model_params.get('J', 200.0)
        h = 1.0
        pin = model_params.get('pin', 0.0)
        n = model_params['field']  # (L, 3) unit vectors
        L = self.lat.N_sites
        self.add_coupling(-0.5 * J, 0, 'Sx', 0, 'Sx', 1, plus_hc=True)
        self.add_coupling(-0.5 * J, 0, 'Sy', 0, 'Sy', 1, plus_hc=True)
        for i in range(L):
            self.add_onsite(-h * n[i, 0], 0, 'Sx')
            self.add_onsite(-h * n[i, 1], 0, 'Sy')
            self.add_onsite(-h * n[i, 2], 0, 'Sz')
        if abs(pin) > 1e-12:
            self.add_onsite(-pin, 0, 'Sy')
        self.n_local = n


def run_one(field, N, chi_max=256, max_sweeps=40):
    n = make_field(field, N)
    model = FieldXY({'L': N, 'J': 200.0, 'field': n, 'pin': 0.0005})
    # alternating up/down product state
    product_state = ['up' if i % 2 == 0 else 'down' for i in range(N)]
    psi = MPS.from_product_state(model.lat.mps_sites(), product_state,
                                 bc=model.lat.bc_MPS)
    dmrg_params = {
        'mixer': True,
        'max_sweeps': max_sweeps,
        'max_E_err': 1.e-13,
        'max_S_err': 1.e-10,
        'trunc_params': {'chi_max': chi_max, 'svd_min': 1.e-12},
        'verbose': 0,
    }
    info = dmrg.run(psi, model, dmrg_params)
    m = np.stack([psi.expectation_value('Sx'),
                  psi.expectation_value('Sy'),
                  psi.expectation_value('Sz')], axis=1)  # (N, 3)
    mn = np.sum(m * n, axis=1)
    max_chi = int(max(psi.chi))
    return float(np.mean(mn)), float(np.var(mn)), max_chi, info['E'], mn


def main():
    # usage: spin_swap.py FIELD N1,N2,... [chi_max max_sweeps]
    field = sys.argv[1]
    Ns = [int(x) for x in sys.argv[2].split(',')]
    chi_max = int(sys.argv[3]) if len(sys.argv) > 3 else 128
    max_sweeps = int(sys.argv[4]) if len(sys.argv) > 4 else 25
    out = open(f'results_{field}.dat', 'a')
    for N in Ns:
        t0 = time.time()
        mean_mn, var_mn, max_chi, E, mn = run_one(field, N, chi_max, max_sweeps)
        dt = time.time() - t0
        out.write(f'{field} {N} {mean_mn:.16e} {var_mn:.16e} {max_chi}\n')
        out.flush()
        print(f'{field:8s} N={N:2d} var={var_mn:.3e} mean={mean_mn:.6f} '
              f'chi={max_chi} E={E:.6f} t={dt:.1f}s', flush=True)
    out.close()


if __name__ == '__main__':
    main()
