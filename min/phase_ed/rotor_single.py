"""Single-rotor exact diagonalization: quantum analog of one classical
phase-oscillator particle on the 12-node ring.

H = p^2/(2I) - K_PHASE cos(phi-ref) - B*K_BIAS cos(phi-ref-pi) + (K_DRIFT/3) cos(3phi)

Basis |m>, m = -Lmax..Lmax, p|m> = m|m>.
  <m+-1|cos(phi-a)|m> = (1/2) e^{-+ia}
  <m+-3|cos(3phi)|m>  = 1/2

Observables per bias B:
  E0, gap E1-E0,
  w(B) = <P_forbidden>, P projects onto |phi-ref| > pi/2,
  r(B) = |<e^{i(phi-ref)}>|,
  |psi(phi)|^2 on a grid for selected B.

w and r are computed for each of the 12 node reference phases and averaged
(the classical w averages over particles sitting on all 12 nodes).
"""

import json
import numpy as np

K_PHASE = 0.5
K_BIAS = 2.0
K_DRIFT = 0.1
N_NODES = 12
REFS = 2.0 * np.pi * np.arange(N_NODES) / N_NODES
B_VALUES = np.round(np.arange(0.0, 1.0001, 0.05), 2)


def build_hamiltonian(Lmax, B, ref, I=1.0):
    n = 2 * Lmax + 1
    m = np.arange(-Lmax, Lmax + 1, dtype=float)
    H = np.diag(m**2 / (2.0 * I)).astype(complex)
    # -V cos(phi - a): <m+1|cos(phi-a)|m> = (1/2) e^{-ia}  (subdiagonal),
    # hence the superdiagonal element <m|cos(phi-a)|m+1> = (1/2) e^{+ia}.
    for V, a in ((K_PHASE, ref), (B * K_BIAS, ref + np.pi)):
        sub = -V * 0.5 * np.exp(-1j * a)
        H += np.diag(sub * np.ones(n - 1), -1)
        H += np.diag(np.conj(sub) * np.ones(n - 1), 1)
    # +(K_DRIFT/3) cos(3phi): <m+-3|cos(3phi)|m> = 1/2  (real)
    if Lmax >= 3:
        off3 = (K_DRIFT / 3.0) * 0.5
        H += np.diag(off3 * np.ones(n - 3), 3)
        H += np.diag(off3 * np.ones(n - 3), -3)
    return H


def forbidden_projector(Lmax, ref):
    """<m|P|m'> = (1/2pi) int_{ref+pi/2}^{ref+3pi/2} e^{i(m'-m)phi} dphi."""
    n = 2 * Lmax + 1
    m = np.arange(-Lmax, Lmax + 1)
    a = ref + np.pi / 2.0
    b = ref + 3.0 * np.pi / 2.0
    dm = m[None, :] - m[:, None]  # dm[row, col] = m' - m
    P = np.empty((n, n), dtype=complex)
    nz = dm != 0
    P[nz] = (np.exp(1j * dm[nz] * b) - np.exp(1j * dm[nz] * a)) / (
        2.0 * np.pi * 1j * dm[nz]
    )
    P[~nz] = (b - a) / (2.0 * np.pi)  # = 1/2
    return P


def eiphi_matrix(Lmax):
    """e^{i phi} |m> = |m+1>."""
    n = 2 * Lmax + 1
    E = np.zeros((n, n), dtype=complex)
    E[np.arange(1, n), np.arange(0, n - 1)] = 1.0
    return E


def ground_state(Lmax, B, ref, I=1.0):
    H = build_hamiltonian(Lmax, B, ref, I)
    evals, evecs = np.linalg.eigh(H)
    return evals, evecs[:, 0]


def observables(Lmax, B, ref, I=1.0):
    evals, psi = ground_state(Lmax, B, ref, I)
    P = forbidden_projector(Lmax, ref)
    E = eiphi_matrix(Lmax)
    w = np.vdot(psi, P @ psi).real
    r = abs(np.vdot(psi, E @ psi))  # |<e^{i(phi-ref)}>| = |<e^{iphi}>|
    return {
        "E0": float(evals[0]),
        "gap": float(evals[1] - evals[0]),
        "w": float(w),
        "r": float(r),
    }


def psi_squared_grid(Lmax, B, ref, I=1.0, nphi=256):
    _, psi = ground_state(Lmax, B, ref, I)
    m = np.arange(-Lmax, Lmax + 1)
    phi = np.linspace(0.0, 2.0 * np.pi, nphi, endpoint=False)
    wf = np.exp(1j * np.outer(phi, m)) @ psi / np.sqrt(2.0 * np.pi)
    return phi, np.abs(wf) ** 2


def sweep(Lmax, I=1.0, b_values=B_VALUES):
    """Sweep B; return per-B observables averaged over the 12 refs."""
    out = []
    for B in b_values:
        per_ref = [observables(Lmax, float(B), ref, I) for ref in REFS]
        out.append(
            {
                "B": float(B),
                "E0": float(np.mean([o["E0"] for o in per_ref])),
                "gap": float(np.mean([o["gap"] for o in per_ref])),
                "w": float(np.mean([o["w"] for o in per_ref])),
                "w_std": float(np.std([o["w"] for o in per_ref])),
                "r": float(np.mean([o["r"] for o in per_ref])),
                "w_per_ref": [o["w"] for o in per_ref],
                "r_per_ref": [o["r"] for o in per_ref],
            }
        )
    return out


def main():
    results = {"params": {
        "K_PHASE": K_PHASE, "K_BIAS": K_BIAS, "K_DRIFT": K_DRIFT,
        "N_NODES": N_NODES, "B_values": list(map(float, B_VALUES)),
    }}

    # Main sweep, Lmax=20, I=1
    results["Lmax20_I1"] = sweep(20, I=1.0)
    # Truncation comparison, Lmax=1
    results["Lmax1_I1"] = sweep(1, I=1.0)
    # Convergence spot-check, Lmax=30
    results["Lmax30_I1"] = sweep(30, I=1.0,
                                 b_values=np.array([0.0, 0.25, 0.5, 1.0]))

    # Inertia sensitivity at a few B points
    sens = {}
    for I in (0.5, 2.0):
        sens[str(I)] = sweep(20, I=I, b_values=np.array([0.0, 0.25, 0.5, 1.0]))
    results["I_sensitivity_Lmax20"] = sens

    # Fine scan around B = 0.25 for structure (gap min, r min)
    fine_B = np.round(np.arange(0.10, 0.4001, 0.01), 2)
    results["fine_scan_Lmax20_I1"] = [
        {"B": o["B"], "gap": o["gap"], "r": o["r"], "w": o["w"]}
        for o in sweep(20, I=1.0, b_values=fine_B)
    ]

    # |psi(phi)|^2 at selected B (ref = 0)
    psi2 = {}
    for B in (0.0, 0.25, 0.5, 1.0):
        phi, p2 = psi_squared_grid(20, B, ref=0.0, I=1.0)
        psi2[str(B)] = {"phi": phi.tolist(), "psi2": p2.tolist()}
    results["psi2_grids"] = psi2

    # Truncation error estimate: |w(Lmax=20) - w(Lmax=1)|
    trunc = [
        {"B": a["B"], "dw": abs(a["w"] - b["w"])}
        for a, b in zip(results["Lmax20_I1"], results["Lmax1_I1"])
    ]
    results["truncation_dw_Lmax20_vs_Lmax1"] = trunc

    with open("results_single.json", "w") as f:
        json.dump(results, f, indent=1)
    print("wrote results_single.json")

    # Console summary
    print(f"{'B':>5} {'w20':>7} {'w1':>7} {'r20':>7} {'gap20':>7}")
    for a, b in zip(results["Lmax20_I1"], results["Lmax1_I1"]):
        print(f"{a['B']:5.2f} {a['w']:7.4f} {b['w']:7.4f} {a['r']:7.4f} {a['gap']:7.4f}")


if __name__ == "__main__":
    main()
