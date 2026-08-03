"""12-site spin-1 rotor chain (many-body counterpart of the bias sweep).

H = sum_i p_i^2/(2I) - K_PHASE sum_i cos(phi_i - ref_i)
    - B*K_BIAS sum_i cos(phi_i - ref_i - pi) + (K_DRIFT/3) sum_i cos(3 phi_i)
    - J sum_i cos(phi_i - phi_{i+1})   (periodic)

Truncated basis m_i in {-1, 0, 1}: dim = 3^12 = 531441.
NOTE: cos(3 phi_i) has zero matrix elements in this truncation (m+-3 lies
outside the basis), so the drift term is identically absent from the chain.

Matrix-free LinearOperator: the vector is reshaped to a (3,)*12 tensor and
all terms are applied as small (3x3) tensor operations. No dense/sparse
matrix is ever built.

Validation: at J=0 the chain must factor into 12 independent Lmax=1 rotors:
E0_chain = 12*E0_single and w_chain = w_single (ref-independent at Lmax=1,
since cos(3phi) is gone and the ref-dependence is a pure gauge).
"""

import json
import sys
import time

import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh

from rotor_single import (
    K_PHASE, K_BIAS, N_NODES, REFS, forbidden_projector, sweep as single_sweep,
)

I = 1.0
D = 3
N = N_NODES
DIM = D ** N
B_VALUES = np.round(np.arange(0.0, 1.0001, 0.1), 2)
J_VALUES = [0.0, 0.5]

# Single-site operators in the m = (-1, 0, 1) basis.
C = np.array([[0.0, 0.5, 0.0], [0.5, 0.0, 0.5], [0.0, 0.5, 0.0]])          # cos phi
S = np.array([[0.0, 0.5j, 0.0], [-0.5j, 0.0, 0.5j], [0.0, -0.5j, 0.0]])    # sin phi
EIPHI = C + 1j * S                                                          # e^{i phi}
M2 = np.array([1.0, 0.0, 1.0])                                              # m^2


def cos_minus(a):
    """3x3 matrix of cos(phi - a) = cos a cos phi + sin a sin phi."""
    return np.cos(a) * C + np.sin(a) * S


def apply_site(t, O, i):
    """Apply single-site operator O (3x3) on site i of tensor t ((3,)*N)."""
    tm = np.moveaxis(t, i, 0)
    tm = np.tensordot(O, tm, axes=([1], [0]))
    return np.moveaxis(tm, 0, i)


# Kinetic diagonal: sum_i m_i^2 / (2I) over the flat basis index.
idx = np.arange(DIM)
DIAG = np.zeros(DIM)
for i in range(N):
    mi = (idx // D ** i) % D - 1
    DIAG += (mi * mi) / (2.0 * I)


def make_matvec(B, J):
    site_ops = [
        -K_PHASE * cos_minus(REFS[i]) - B * K_BIAS * cos_minus(REFS[i] + np.pi)
        for i in range(N)
    ]
    # (K_DRIFT/3) cos(3 phi_i): all matrix elements vanish for m in {-1,0,1}.

    def matvec(v):
        t = v.reshape((D,) * N)
        out = (DIAG * v).reshape((D,) * N)
        for i in range(N):
            out = out + apply_site(t, site_ops[i], i)
        if J != 0.0:
            for i in range(N):
                j = (i + 1) % N
                bond = apply_site(apply_site(t, C, i), C, j) + apply_site(
                    apply_site(t, S, i), S, j
                )
                out = out - J * bond
        return out.ravel()

    return matvec


def site_expect(psi, O, i):
    t = psi.reshape((D,) * N)
    return np.vdot(t.ravel(), apply_site(t, O, i).ravel())


def run_point(B, J, tol=1e-12):
    t0 = time.time()
    A = LinearOperator((DIM, DIM), matvec=make_matvec(B, J), dtype=complex)
    evals, evecs = eigsh(A, k=4, which="SA", tol=tol, maxiter=10000)
    order = np.argsort(evals)
    evals = evals[order]
    psi = evecs[:, order[0]]
    w = float(np.mean([site_expect(psi, forbidden_projector(1, REFS[i]), i).real
                       for i in range(N)]))
    r = float(np.mean([abs(site_expect(psi, EIPHI, i)) for i in range(N)]))
    return {
        "B": float(B), "J": J,
        "E0": float(evals[0]),
        "gap": float(evals[1] - evals[0]),
        "w": w, "r": r,
        "seconds": time.time() - t0,
    }


def main():
    results = {"params": {
        "N": N, "D_per_site": D, "dim": DIM, "I": I,
        "K_PHASE": K_PHASE, "K_BIAS": K_BIAS,
        "note": "cos(3phi) drift term vanishes identically in the m={-1,0,1} basis",
        "B_values": list(map(float, B_VALUES)), "J_values": J_VALUES,
    }}

    # Single-rotor Lmax=1 reference for validation and truncation estimates.
    single = {o["B"]: o for o in single_sweep(1, I=1.0, b_values=B_VALUES)}

    validation = {"checks": []}
    for B in B_VALUES:
        pt = run_point(float(B), J=0.0)
        s = single[float(B)]
        dE = abs(pt["E0"] - N * s["E0"])
        dw = abs(pt["w"] - s["w"])
        validation["checks"].append({
            "B": pt["B"], "E0_chain": pt["E0"], "12xE0_single": N * s["E0"],
            "dE": dE, "w_chain": pt["w"], "w_single": s["w"], "dw": dw,
        })
        print(f"J=0 B={B:.2f} E0={pt['E0']:.10f} dE={dE:.2e} dw={dw:.2e} "
              f"({pt['seconds']:.1f}s)", flush=True)
    validation["max_dE"] = max(c["dE"] for c in validation["checks"])
    validation["max_dw"] = max(c["dw"] for c in validation["checks"])
    validation["passed"] = validation["max_dE"] < 1e-9 and validation["max_dw"] < 1e-9
    results["validation_J0"] = validation

    sweeps = {}
    for J in J_VALUES:
        pts = []
        for B in B_VALUES:
            pt = run_point(float(B), J)
            pts.append(pt)
            print(f"J={J} B={B:.2f} E0={pt['E0']:.6f} gap={pt['gap']:.6f} "
                  f"w={pt['w']:.6f} r={pt['r']:.6f} ({pt['seconds']:.1f}s)",
                  flush=True)
        sweeps[str(J)] = pts
    results["sweeps"] = sweeps

    with open("results_chain.json", "w") as f:
        json.dump(results, f, indent=1)
    print("wrote results_chain.json; validation passed:", validation["passed"])


if __name__ == "__main__":
    sys.exit(main())
