#!/usr/bin/env python3
"""wigner_mirror_w3.py -- Stage W3 mirror: Dirac-Fock radial Wigner maps.

Hydrogenic Dirac orbitals (point nucleus), half-line Wigner in both
coordinates:
  r-map: W(r,p)  = (1/pi) int_{-r}^{r} dy e^{2ipy} rho(r-y, r+y),  uniform r
  t-map: W(t,q)  = (1/pi) int      du e^{2iqu} rho_t(t-u, t+u),    t = log r
with rho(r,r') = sum_a occ_a [F_a(r)F_a(r') + G_a(r)G_a(r')].

Orbitals: eigenvalue from the closed Dirac-Coulomb form
  E = c^2 [1 + (Z/c)^2/(n_r + gam)^2]^-1/2,  gam = sqrt(kappa^2-(Z/c)^2)
then ONE outward IVP (solve_ivp) in t = log r with the df_radial-certified
series start F = r^gam, G = q0 r^gam, q0 = c(gam+kappa)/Z. Normalized
int (F^2+G^2) dr = 1. No shooting, no hypergeometrics.

WNORM oracle: dr*dp*sum W = occ (dp = pi/(NP*dr), full Nyquist), and the
same with (dt, dq) for the t-map. Exact discrete sums, mirror-defined.

Usage:
  python wigner_mirror_w3.py oracles            # He + Ne, both c scales
  python wigner_mirror_w3.py map Z cscale coord > map.txt
       coord = r | t ; rows: x  p  W  (x = r or t)

Deterministic: fixed grids, closed-form eigenvalues, fixed IVP tolerance.
"""
import sys
import numpy as np
from scipy.integrate import solve_ivp

C0 = 137.035999084

# grids (mirror-defined; the engine must match these constants)
RMIN, RMAX, NR = 1.0e-6, 12.0, 2048      # uniform-r map grid (cell-centered)
TMIN, TMAX, NT = np.log(RMIN), np.log(RMAX), 20000   # native t grid (IVP)
NTM = 1024                                # t-map grid (decimated from IVP)
NP = 4096                                 # momentum samples (full Nyquist: NP >= NR)


def dirac_orbital(Z, n, kappa, c):
    """Hydrogenic Dirac (F,G) on the native t grid. Returns t, r, F, G, eps."""
    gam = np.sqrt(kappa**2 - (Z / c)**2)
    nr = n - abs(kappa)
    E = c**2 / np.sqrt(1.0 + (Z / (c * (nr + gam)))**2)
    eps = E - c**2
    q0 = c * (gam + kappa) / Z
    t = np.linspace(TMIN, TMAX, NT)
    r = np.exp(t)

    def rhs(tt, y):
        rr = np.exp(tt)
        F, G = y
        V = -Z / rr
        dF = -kappa * F + rr * (E - V + c**2) * G / c
        dG = kappa * G - rr * (E - c**2 - V) * F / c
        return [dF, dG]

    # inward integration of the decaying branch (outward is unstable:
    # the growing mode contaminates at ~e^{2 lambda r}). Decaying start:
    # F = e^-lam r, G = qinf e^-lam r, qinf = -lam c/(2c^2+eps).
    lam = np.sqrt(-eps * (2.0 * c**2 + eps)) / c
    qinf = -lam * c / (2.0 * c**2 + eps)
    y0 = [np.exp(-lam * RMAX), qinf * np.exp(-lam * RMAX)]
    sol = solve_ivp(rhs, [TMAX, TMIN], y0, t_eval=t[::-1],
                    rtol=1e-10, atol=1e-40, method="DOP853")
    F, G = sol.y[0, ::-1], sol.y[1, ::-1]
    i_pk = np.argmax(np.abs(F[:NT // 4]))
    if F[i_pk] < 0:
        F, G = -F, -G
    nrm = np.sqrt(np.trapezoid(F**2 + G**2, r))
    return t, r, F / nrm, G / nrm, eps


def resample(t, F, G):
    """(F,G) from the native t grid onto the uniform-r grid (cell-centered)."""
    rr = RMIN + (np.arange(NR) + 0.5) * ((RMAX - RMIN) / NR)
    return rr, np.interp(rr, np.exp(t), F), np.interp(rr, np.exp(t), G)


def wigner_halfline(xg, rho_orb, occ):
    """rho_orb: list of (occ, A) with A the radial amplitude pair summed as
    rho(i,j) = sum occ*(F_i F_j + G_i G_j) precomputed as a matrix.
    Direct DFT, full Nyquist: p_j = pi*j/(NP*dx), j = 0..NP-1."""
    nx = rho_orb.shape[0]
    dx = xg[1] - xg[0]
    p = np.pi * np.arange(NP) / (NP * dx)
    W = np.zeros((nx, NP))
    for i in range(nx):
        m = min(i, nx - 1 - i)
        ry = rho_orb[np.arange(i - m, i + m + 1),
                     np.arange(i + m, i - m - 1, -1)]
        # k = -m..m ascending; twiddle exp(2 pi i k j / NP) = FFT with
        # negative-k part wrapped to the end of the buffer
        buf = np.zeros(NP)
        buf[0:m + 1] = ry[m:]
        buf[NP - m:] = ry[:m]
        W[i] = np.real(np.fft.fft(buf)) * dx / np.pi
    dp = np.pi / (NP * dx)
    wnorm = dx * dp * W.sum()
    return W, p, wnorm


def atom(Z, occs, c):
    """occs: list of (n, kappa, occ). Returns per-coord rho matrices."""
    t = r = None
    rho_t = None
    rr = Fr = None
    rho_r = None
    eps_out = []
    for (n, kap, occ) in occs:
        t, r, F, G, eps = dirac_orbital(Z, n, kap, c)
        eps_out.append(eps)
        # native-t coherence matrix (decimated to the t-map grid)
        idx = np.linspace(0, NT - 1, NTM).astype(int)
        t_dec, Fm, Gm = t[idx], F[idx], G[idx]
        coh_t = occ * (np.outer(Fm, Fm) + np.outer(Gm, Gm))
        rho_t = coh_t if rho_t is None else rho_t + coh_t
        # uniform-r coherence matrix
        rr, Fr_, Gr_ = resample(t, F, G)
        coh_r = occ * (np.outer(Fr_, Fr_) + np.outer(Gr_, Gr_))
        rho_r = coh_r if rho_r is None else rho_r + coh_r
    return eps_out, (rr, rho_r), (np.linspace(TMIN, TMAX, NTM), rho_t)


HE = [(1, -1, 2)]
NE = [(1, -1, 2), (2, -1, 2), (2, 1, 2), (2, -2, 4)]


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "oracles":
        print("atom  cscale   eps_1s(Ha)      WNORM_r        WNORM_t"
              "   Wr(x0,p=0)    Wr(x0,p*)     Wt(tc,p=0)    Wt(tc,q*)"
              "   (* = j NP/2)")
        for name, Z, occs in [("He", 2.0, HE), ("Ne", 10.0, NE)]:
            for cs in (100.0, 1.0):
                c = C0 * cs
                eps, (rr, rho_r), (t, rho_t) = atom(Z, occs, c)
                Wr, pr, nr_ = wigner_halfline(rr, rho_r, None)
                Wt, qt, nt_ = wigner_halfline(t, rho_t, None)
                print(f"{name}  x{cs:5.1f}  {eps[0]:+.10e}  {nr_:+.12e}"
                      f"  {nt_:+.12e}"
                      f"  {Wr[0, 0]:+.10e}  {Wr[0, NP//2]:+.10e}"
                      f"  {Wt[NTM//2, 0]:+.10e}  {Wt[NTM//2, NP//2]:+.10e}")
        return
    if len(sys.argv) >= 5 and sys.argv[1] == "map":
        Z, cs, coord = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        occs = HE if abs(Z - 2.0) < 1e-9 else NE
        eps, (rr, rho_r), (t, rho_t) = atom(Z, occs, C0 * cs)
        if coord == "r":
            W, p, _ = wigner_halfline(rr, rho_r, None)
            xg = rr
        else:
            W, p, _ = wigner_halfline(t, rho_t, None)
            xg = t
        for i in range(len(xg)):
            for j in range(NP):
                print(f"{xg[i]:.6e} {p[j]:.6e} {W[i, j]:.10e}")
        return
    if len(sys.argv) >= 6 and sys.argv[1] == "compare":
        # engine rows: ('W3MAP Z cscale coord x p W'), coord 0=r 1=t
        path, Z, cs, coord = sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
        occs = HE if abs(Z - 2.0) < 1e-9 else NE
        eps, (rr, rho_r), (tt, rho_t) = atom(Z, occs, C0 * cs)
        if coord == 0:
            W, p, _ = wigner_halfline(rr, rho_r, None)
            xg = rr
        else:
            W, p, _ = wigner_halfline(tt, rho_t, None)
            xg = tt
        worst, n = 0.0, 0
        for line in open(path):
            line = line.strip().strip("()").replace("'", " ")
            f = line.split()
            if len(f) != 7 or f[0] != "W3MAP":
                continue
            if (abs(float(f[1]) - Z) > 1e-9 or abs(float(f[2]) - cs) > 1e-9
                    or int(f[3]) != coord):
                continue
            x_e, p_e, w_e = float(f[4]), float(f[5]), float(f[6])
            ix = np.argmin(np.abs(xg - x_e))
            ip = np.argmin(np.abs(p - p_e))
            worst = max(worst, abs(W[ix, ip] - w_e))
            n += 1
        print(f"compared {n} W3MAP rows, max abs diff = {worst:.6e}")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
