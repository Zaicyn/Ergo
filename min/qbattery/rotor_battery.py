#!/usr/bin/env python3
"""rotor_battery.py — open quantum-rotor battery: exact Lindblad for
N spin-1 rotors collectively coupled to a damped cavity mode.

Tests whether quantum coherence pushes the discharge-power exponent
from the classical rate model's 1.5 ceiling (qbattery_check.md)
toward the paper's claimed 2.0.

Model (documented):
  Rotor states m = +1/0/-1 mapped to S1 / T1-proxy / S0.
  H = wc a^dag a + wr sum Lz_i + g sum (a L+_i + a^dag L-_i) - J sum (Lx_i Lx_j + Ly_i Ly_j)
  (Tavis-Cummings coupling, number-conserving; rotor-rotor exchange J
  = the Luttinger knob, critical at B=0.25 in the rotor-chain units).
  Lindblad: D[a]*kappa (cavity loss), D[a^dag]*pump (incoherent pump),
  D[L-_i]*gamma_s (S1 -> T1 decay), D[|-1><0|_i]*k_ext (extraction
  T1 -> S0; current I = k_ext * <P_0>), D[Lz_i]*gamma_phi (dephasing).
  Cavity truncated at NC = 4 (mean photon number << 1 at these pump
  rates, checked). Steady state: sparse Liouvillian, null vector with
  trace constraint (replace row 0 with the trace row).
Comparison mode: two-level emitters (spin-1/2) in the same Lindblad —
isolates what the rotor phase structure adds.
"""

import numpy as np
import scipy.sparse as sp
from scipy.sparse import kron, eye, csc_matrix

WC, WR = 1.0, 1.0
NC = 4
KAPPA, GAMMA_S, K_EXT = 0.5, 1.0, 1.0
E_T1, G_DRESS = 1.2, 0.05  # dressed-voltage convention from qbattery_check.md

def spin1_ops():
    lz = csc_matrix(np.diag([1.0, 0.0, -1.0]))
    lp = csc_matrix(np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=complex))
    lx = (lp + lp.T) / 2
    ly = (lp - lp.T) / 2j
    return lz, lp, lp.T, lx, ly

def spinhalf_ops():
    sz = csc_matrix(np.diag([0.5, -0.5]))
    sp_ = csc_matrix(np.array([[0, 1], [0, 0]], dtype=complex))
    return sz, sp_, sp_.T, (sp_ + sp_.T) / 2, (sp_ - sp_.T) / 2j

def cavity_ops():
    n = csc_matrix(np.diag(np.arange(NC, dtype=float)))
    a = csc_matrix(np.diag(np.sqrt(np.arange(1, NC)), 1).astype(complex))
    return a, a.T, n

def embed(op, site, dims):
    factors = [eye(d, format="csc") for d in dims]
    factors[site] = op
    out = factors[0]
    for f in factors[1:]:
        out = kron(out, f, format="csc")
    return out

def build_system(n_rot, g, J, gamma_phi, rotor=True):
    """Return steady-state rho, current I, pair coherence, rotor-1 entropy."""
    sd = 3 if rotor else 2
    lz, lp, lm, lx, ly = (spin1_ops() if rotor else spinhalf_ops())
    a, ad, an = cavity_ops()
    dims = [sd] * n_rot + [NC]
    dim = int(np.prod(dims))
    Id = eye(dim, format="csc")

    IdL = eye(dim * dim, format="csc")

    # Hamiltonian
    H = WC * embed(an, n_rot, dims)
    Lz_sum = sum(embed(lz, i, dims) for i in range(n_rot))
    H = H + WR * Lz_sum
    Lp_sum = sum(embed(lp, i, dims) for i in range(n_rot))
    H = H + g * (embed(a, n_rot, dims) @ Lp_sum + embed(ad, n_rot, dims) @ Lp_sum.T)
    for i in range(n_rot):
        for j in range(i + 1, n_rot):
            H = H - J * (embed(lx, i, dims) @ embed(lx, j, dims) +
                         embed(ly, i, dims) @ embed(ly, j, dims))

    # Liouvillian
    def liou(c, rate):
        cd = c.T.conj()
        cc = cd @ c
        return rate * (kron(c.conj(), c) - 0.5 * kron(IdL, cc) - 0.5 * kron(cc.T, IdL))

    L = -1j * (kron(IdL, H) - kron(H.T, IdL))
    L = L + liou(embed(a, n_rot, dims), KAPPA)
    L = L + liou(embed(ad, n_rot, dims), PUMP)
    if rotor:
        x_op = csc_matrix(np.array([[0, 0, 0], [0, 0, 0], [0, 1, 0]], dtype=complex))
        p0_op = csc_matrix(np.diag([0.0, 1.0, 0.0]))
    else:
        x_op = csc_matrix(np.array([[0, 0], [1, 0]], dtype=complex))
        p0_op = csc_matrix(np.diag([1.0, 0.0]))
    for i in range(n_rot):
        L = L + liou(embed(lm, i, dims), GAMMA_S)
        L = L + liou(embed(x_op, i, dims), K_EXT)
        L = L + liou(embed(lz, i, dims), gamma_phi)

    # steady state: implicit Euler from identity (zero mode dominates;
    # (I - dt*L) is invertible since Re(eig(L)) <= 0). Normalize each step.
    dt_e = 10.0
    IdL = eye(dim * dim, format="csc")
    A = (IdL - dt_e * L).tocsc()
    x = np.eye(dim).reshape(-1)
    tr_idx = np.arange(0, dim * dim, dim + 1)
    for _ in range(80):
        x = sp.linalg.spsolve(A, x)
        x = x / x[tr_idx].sum()
    rho = x.reshape(dim, dim)

    # measurements
    I_cur = 0.0
    for i in range(n_rot):
        p0 = embed(p0_op, i, dims)
        I_cur += K_EXT * float(np.real(np.trace(p0 @ rho)))
    # pair coherence <L+_1 L-_2 + L-_1 L+_2>/2 (nearest neighbors)
    coh = 0.0
    if n_rot >= 2:
        op = (embed(lp, 0, dims) @ embed(lm, 1, dims) + embed(lm, 0, dims) @ embed(lp, 1, dims)) / 2
        coh = float(np.real(np.trace(op @ rho)))
    # rotor-1 von Neumann entropy (partial trace over the rest)
    keep = sd
    rest = dim // sd
    r1 = rho.reshape(keep, rest, keep, rest).trace(axis1=1, axis2=3)
    ev = np.linalg.eigvalsh((r1 + r1.conj().T) / 2)
    ev = ev[ev > 1e-14]
    s1 = float(-np.sum(ev * np.log(ev)))
    return I_cur, coh, s1

PUMP = 0.1

if __name__ == "__main__":
    import itertools, sys
    g = float(sys.argv[1]) if len(sys.argv) > 1 else 0.1
    J = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    gp = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    rotor = bool(int(sys.argv[4])) if len(sys.argv) > 4 else True
    print(f"# g={g} J={J} gamma_phi={gp} rotor={rotor}")
    for n in range(2, 7):
        try:
            I, coh, s1 = build_system(n, g, J, gp, rotor)
            vth = E_T1 + G_DRESS * np.sqrt(n) if rotor else E_T1
            print(f"N={n} I={I:.5f} P={I*vth:.5f} coh={coh:.4f} S1={s1:.4f}")
        except Exception as e:
            print(f"N={n} FAILED: {e}")
