"""Polarized-start DMRG test: N=12 viviani field.
Compare against exact ED ground energy E0 = -772.75183167.
If the 'protection' is real, a converged state from a polarized start
should show mean(m.n) ~ 0 with var ~ 1e-24 at the ED energy.
If it's an artifact, polarized start converges to mean ~ 1.86e-3, var ~ 1.3e-7.
"""
import numpy as np
import logging
logging.disable(logging.WARNING)
from tenpy.networks.mps import MPS
from tenpy.algorithms import dmrg
from spin_swap import FieldXY, make_field

E_ED = -772.75183167
N = 12
n = make_field('viviani', N)
model = FieldXY({'L': N, 'J': 200.0, 'field': n, 'pin': 0.0005})

def polarized_state(n):
    """Each spin pointing along its local field direction n_i."""
    states = []
    for i in range(len(n)):
        nx, ny, nz = n[i]
        theta = np.arccos(np.clip(nz, -1, 1))
        phi = np.arctan2(ny, nx)
        up = np.cos(theta / 2)
        down = np.exp(1j * phi) * np.sin(theta / 2)
        states.append(np.array([up, down]))
    return states

def measure(psi, n):
    sx = psi.expectation_value('Sx')
    sy = psi.expectation_value('Sy')
    sz = psi.expectation_value('Sz')
    m = np.stack([sx, sy, sz], axis=1)
    vals = np.einsum('ij,ij->i', m, n)
    return vals.mean(), vals.var()

for tag, init in (('polarized', polarized_state(n)),
                  ('alternating', ['up' if i % 2 == 0 else 'down' for i in range(N)])):
    psi = MPS.from_product_state(model.lat.mps_sites(), init, bc=model.lat.bc_MPS)
    info = dmrg.run(psi, model, {
        'mixer': True, 'max_sweeps': 60,
        'max_E_err': 1e-13,
        'trunc_params': {'chi_max': 256, 'svd_min': 1e-12},
        'verbose': 0,
    })
    E = info['E']
    mean_mn, var_mn = measure(psi, n)
    print(f"{tag:12s}: E={E:.8f}  E-E_ED={E-E_ED:+.2e}  "
          f"mean(m.n)={mean_mn:+.6e}  var(m.n)={var_mn:.3e}  chi={max(psi.chi)}")
