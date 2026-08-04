#!/usr/bin/env python3
"""spectral_ref.py — independent exact spectral reference for the free
particle on S^3 (R=m=1, dimensionless Tt = hbar T / 2).

K_spec(Theta, Tt) = (1/2pi^2) sum_{l=0}^{Lmax} (l+1) sin((l+1)Theta)/sin(Theta)
                    * exp(-i l(l+2) Tc),   Tc = Tt - i*eps

Both the spectral sum and the winding sum are conditionally convergent
at real time (terms do not decay); the Feynman iepsilon prescription
(Tt -> Tt - i*eps, eps > 0) makes both absolutely convergent and is the
standard distributional definition of the real-time propagator. The
Poisson/Jacobi identity relating the two sides holds exactly for every
eps > 0, so comparisons are made at fixed eps; an eps-sequence documents
the approach to real time.

Lmax convergence: double until the grid max |K(L) - K(L/2)| / max|K|
is below TOL (reported by analyze_prop.py).

Usage: python spectral_ref.py   (writes spec_ref.txt to this dir)
"""
import numpy as np

TTS = (0.1, 0.25, 0.5)
EPS = 0.01          # Feynman damping (complex time Tc = Tt - i*EPS)
NGRID = 2000
TH_LO, TH_HI = 0.05, 2.0 * np.pi - 0.05
TOL = 1e-10
LSTART = 250
LMAX_CAP = 2_000_000


def theta_grid():
    return TH_LO + np.arange(NGRID) * (TH_HI - TH_LO) / (NGRID - 1)


def k_spec(theta, Tt, Lmax, eps=EPS):
    """Vectorized over theta (scalar or array)."""
    Tc = Tt - 1j * eps
    th = np.asarray(theta, dtype=float)
    l = np.arange(0, Lmax + 1)
    amp = (l + 1) * np.exp(-1j * l * (l + 2) * Tc)
    # (l+1) sin((l+1)th) / sin(th), summed over l
    S = np.sin(np.outer(l + 1, th)) / np.sin(th)
    return (S * amp[:, None]).sum(axis=0) / (2.0 * np.pi ** 2)


def converge(theta, Tt, eps=EPS, tol=TOL, lstart=LSTART):
    """Double Lmax until stable. Returns (K, Lmax, rel_change)."""
    th = np.asarray(theta, dtype=float)
    L = lstart
    Kprev = k_spec(th, Tt, L, eps)
    while True:
        L *= 2
        K = k_spec(th, Tt, L, eps)
        scale = np.abs(K).max()
        change = np.abs(K - Kprev).max() / scale
        if change < tol or L >= LMAX_CAP:
            return K, L, change
        Kprev = K


def main():
    th = theta_grid()
    with open("min/quaternion/spec_ref.txt", "w") as f:
        f.write(f"# spectral reference: EPS={EPS} NGRID={NGRID} "
                f"range=({TH_LO},{TH_HI})\n")
        for Tt in TTS:
            K, L, ch = converge(th, Tt)
            f.write(f"# Tt={Tt} Lmax={L} rel_change={ch:.3e}\n")
            for i in range(NGRID):
                f.write(f"SPEC {Tt} {i} {K[i].real:.17e} {K[i].imag:.17e}\n")
    print("wrote min/quaternion/spec_ref.txt")


if __name__ == "__main__":
    main()
