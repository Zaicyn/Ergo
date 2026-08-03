"""Sparse Fourier recovery of the double-slit screen profile.

Takes the validated 512-point screen intensity profile (slit_1d.out,
scene 2, lambda=16) and asks: from only K sampled points, can a sparse
Fourier fit recover the fringe spacing to 5%?

Preprocessing (same as the validated extraction): smooth (sigma=3),
crop to the central region rows 101..412, subtract a broad baseline
(sigma=25) -> oscillation osc(x), x = 0..311 (N=312). The oscillation
is Fresnel-chirped (spacing ~65 at center widening outward), so its
dominant Fourier period is the FULL-DATA reference, not the far-field
oracle: K=512 recovery defines the target; the far-field oracle 65.0
cells applies to the central fringes (65.5 validated, see
fdtd_check.md).

Method: orthogonal matching pursuit (OMP) over a fine grid of complex
exponentials (4096 frequencies in (0, 0.5) cycles/cell), k = 3 atoms
with least-squares refit on the K samples after each pick; the fringe
atom is the strongest atom in the physical band [1/120, 1/30]; its
frequency is refined by parabolic interpolation of the projection.

Sampling: uniform stride and seeded random draws (8 trials, median).
K in {312, 256, 128, 64, 48, 32, 24, 16}. Compressed-sensing ballpark:
K ~ k log2 N ~ 3 * 8 = 24 (N=312, k=3 significant components).
"""
import numpy as np

prof = np.zeros(512)
for line in open("slit_1d.out"):
    if line.startswith("#"):
        continue
    sc, j, v = line.split()
    if int(sc) == 2:
        prof[int(j) - 1] = float(v)


def gsmooth(y, s):
    k = int(np.ceil(4 * s))
    x = np.arange(-k, k + 1)
    g = np.exp(-0.5 * (x / s) ** 2)
    g /= g.sum()
    return np.convolve(y, g, mode="same")


sm = gsmooth(prof, 3.0)
core = sm[100:412]
osc = core - gsmooth(core, 25.0)
N = len(osc)
x_all = np.arange(N)
ORACLE = 65.0
FRANGE = (1 / 120, 1 / 30)
K_ATOMS = 3
NGRID = 4096
FREQS = np.linspace(1e-4, 0.5 - 1e-4, NGRID)


def fringe_spacing(idx, y):
    E = np.exp(2j * np.pi * np.outer(idx, FREQS))
    chosen = []
    r = y.astype(complex).copy()
    for _ in range(K_ATOMS):
        proj = np.abs(E.conj().T @ r)
        for c in chosen:
            proj[c] = 0
        f_new = int(np.argmax(proj))
        chosen.append(f_new)
        A = E[:, chosen]
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        r = y - A @ coef
    A = E[:, chosen]
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    band = [(f, abs(c)) for f, c in zip(chosen, coef) if FRANGE[0] <= FREQS[f] <= FRANGE[1]]
    if not band:
        return float("nan")
    f_star, _ = max(band, key=lambda t: t[1])
    # parabolic refine of the projection at f_star against the full residual
    r_star = y - A @ coef + np.outer(E[:, f_star], [coef[chosen.index(f_star)]])[0] * 0  # residual without f_star
    r_star = y - (A @ coef - E[:, f_star] * coef[chosen.index(f_star)])
    p = np.abs(E[:, max(0, f_star - 1):f_star + 2].conj().T @ r_star)
    if len(p) == 3 and f_star + 1 < NGRID:
        a, b, c = p
        denom = a - 2 * b + c
        df = 0.5 * (a - c) / denom if abs(denom) > 1e-30 else 0.0
    else:
        df = 0.0
    f_ref = FREQS[f_star] + df * (FREQS[1] - FREQS[0])
    return 1.0 / f_ref


# full-data reference
REF = fringe_spacing(x_all, osc)
print(f"N={N}, full-data dominant fringe period: {REF:.2f} cells "
      f"(far-field oracle for central fringes: {ORACLE}; 5% window on reference: "
      f"[{0.95*REF:.2f}, {1.05*REF:.2f}])\n")

Ks = [312, 256, 128, 64, 48, 32, 24, 16]
print(f"{'K':>4} {'uniform':>9} {'ok':>3} {'random(med)':>12} {'ok/8':>5}")
rng = np.random.default_rng(20260723)
for K in Ks:
    idx_u = np.linspace(0, N - 1, K).round().astype(int)
    sp_u = fringe_spacing(idx_u, osc[idx_u])
    ok_u = abs(sp_u - REF) / REF <= 0.05
    sps, oks = [], 0
    for _ in range(8):
        idx_r = np.sort(rng.choice(N, K, replace=False))
        sp_r = fringe_spacing(idx_r, osc[idx_r])
        sps.append(sp_r)
        oks += abs(sp_r - REF) / REF <= 0.05
    sp_med = float(np.nanmedian(sps))
    print(f"{K:>4} {sp_u:>9.2f} {'Y' if ok_u else 'n':>3} {sp_med:>12.2f} {oks:>4}/8"
          f"   (draws: {', '.join(f'{s:.1f}' for s in sps)})")

print(f"\nballpark: K ~ k log2 N = 3 * {np.log2(N):.1f} = {3*np.log2(N):.0f}")
