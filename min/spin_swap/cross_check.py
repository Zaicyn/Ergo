import numpy as np
import logging
logging.disable(logging.WARNING)
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from tenpy.networks.mps import MPS
from tenpy.algorithms import dmrg
from spin_swap import FieldXY, make_field

N = 12
n = make_field('viviani', N)
model = FieldXY({'L': N, 'J': 200.0, 'field': n, 'pin': 0.0005})

init = ['up' if i % 2 == 0 else 'down' for i in range(N)]
psi = MPS.from_product_state(model.lat.mps_sites(), init, bc=model.lat.bc_MPS)
info = dmrg.run(psi, model, {'mixer': True, 'max_sweeps': 60, 'max_E_err': 1e-13,
                             'trunc_params': {'chi_max': 256, 'svd_min': 1e-12},
                             'verbose': 0})
print(f"DMRG energy (TenPy MPO): {info['E']:.8f}")

# Contract MPS to full wavefunction
B = psi.get_B(0)  # (vL, vR, d)
wf = B[0]  # (vR, d)
for i in range(1, N):
    Bi = psi.get_B(i)
    wf = np.tensordot(wf, Bi, axes=([-1], [0]))
wf = wf.reshape(-1)
wf = wf / np.linalg.norm(wf)
print("wavefunction size:", wf.size)

# Build sparse ED Hamiltonian (identical construction as before, no pin)
sx = sp.csr_matrix([[0, 0.5], [0.5, 0]], dtype=complex)
sy = sp.csr_matrix([[0, -0.5j], [0.5j, 0]], dtype=complex)
sz = sp.csr_matrix([[0.5, 0], [0, -0.5]], dtype=complex)
id2 = sp.eye(2)

def op_on_site(op, i):
    out = sp.csr_matrix(1, dtype=complex)
    for s in range(N):
        out = sp.kron(out, op if s == i else id2, format='csr')
    return out

Sxs = [op_on_site(sx, i) for i in range(N)]
Sys = [op_on_site(sy, i) for i in range(N)]
Szs = [op_on_site(sz, i) for i in range(N)]
H = sp.csr_matrix((2**N, 2**N), dtype=complex)
for i in range(N):
    j = (i + 1) % N
    H = H - 200.0 * (Sxs[i] @ Sxs[j] + Sys[i] @ Sys[j])
for i in range(N):
    H = H - (n[i,0]*Sxs[i] + n[i,1]*Sys[i] + n[i,2]*Szs[i])

w, v = spl.eigsh(H, k=1, which='SA', tol=1e-13)
print(f"sparse ED ground energy: {w[0]:.8f}")
print(f"<psi_DMRG|H_ED|psi_DMRG> = {np.vdot(wf, H @ wf).real:.8f}")

# also energy of ED ground state under TenPy MPO? approximate via overlap:
ov = abs(np.vdot(v[:,0], wf))**2
print(f"|<psi_ED|psi_DMRG>|^2 = {ov:.6f}")
