#!/usr/bin/env python3
"""rotor_tower.py — Stage 1: rotor-chain Casimir + LL excitation tower.

Model: ternary rotor chain on the competition line B = 0.25
(K_PHASE = 0.5, K_BIAS = 2.0 -> V = K_PHASE - B*K_BIAS = 0 identically),
deep in the critical phase at J = 1.5:

  H = sum_i m_i^2 / 2  -  J sum_i cos(phi_i - phi_{i+1})   (periodic)

the pure quantum phase model (first harmonic cancels; cos(3phi) has no
matrix elements at Lmax=1). Real matrix-free numba matvec (same operator
as min/phase_ed/ed_ref.py, halfJ = J/2). ED via scipy eigsh, k = 8,
deterministic ARPACK start vector (the campaign seed
v0(x) = 0.5 + (x % 9973)*1e-4 — same as the GPU engine).

Quantum numbers per eigenstate: total rotor charge M = sum_i m_i
(exact, diagonal) and lattice momentum p from the translation operator
(digit rotation x' = 3*(x mod 3^(N-1)) + x div 3^(N-1)).

Oracles (min/FINDINGS.md section 3):
  (a) E0(N) = eps_inf*N - b/N with b = pi*v*c/6: c from this Casimir
      fit must agree with the entanglement route (c = 1, 1.044 +/- 0.010
      at J=1.5 N=12 ED; DMRG 1.00) — cross-method agreement required.
      v from the p = +-2pi/N, M = 0 descendant pair (x = 1).
  (b) tower x_n = dE_n*N/(2*pi*v): LL integers 1, 2 within a few %,
      plus the winding sector at x = 1/(4K).
  (c) K three-way: winding x_w -> K = 1/(4 x_w) vs eta-route 1.8-2.2
      vs BKT universal 2. Disagreement is the headline.

Determinism: fixed start vector, fixed tolerances; run twice,
byte-identical.
"""

import sys
import time

import numpy as np
from numba import njit, prange
from scipy.sparse.linalg import LinearOperator, eigsh

J = 1.5
HALFJ = J / 2.0
NS = (8, 10, 12, 14)
K_EIG = 8
TOL = 1e-12


@njit(parallel=True, cache=False)
def _matvec(v, out, p3, halfJ, N):
    dim = v.shape[0]
    for x in prange(dim):
        digits = np.empty(N, np.int64)
        dg = 0
        for i in range(N):
            d = (x // p3[i]) % 3
            digits[i] = d
            m = d - 1
            dg += m * m
        acc = (dg / 2.0) * v[x]
        for i in range(N):
            j = i + 1
            if j == N:
                j = 0
            di = digits[i]
            dj = digits[j]
            if di >= 1 and dj <= 1:
                acc -= halfJ * v[x - p3[i] + p3[j]]
            if di <= 1 and dj >= 1:
                acc -= halfJ * v[x + p3[i] - p3[j]]
        out[x] = acc


def sectors(N):
    """Diagonal M per flat index and the translation permutation."""
    dim = 3 ** N
    p3 = (3 ** np.arange(N)).astype(np.int64)
    idx = np.arange(dim, dtype=np.int64)
    M = np.zeros(dim, dtype=np.int64)
    for i in range(N):
        M += (idx // p3[i]) % 3 - 1
    # translation by one site: d'_i = d_{i-1}
    top = 3 ** (N - 1)
    perm = 3 * (idx % top) + idx // top
    return dim, p3, M, perm


def run_N(N):
    dim, p3, M, perm = sectors(N)
    out = np.empty(dim)
    p3c = np.ascontiguousarray(p3)

    def mv(v):
        _matvec(v, out, p3c, HALFJ, N)
        return out

    A = LinearOperator((dim, dim), matvec=mv, dtype=np.float64)
    v0 = 0.5 + (np.arange(1, dim + 1, dtype=np.int64) % 9973) * 0.0001
    t0 = time.time()
    evals, evecs = eigsh(A, k=K_EIG, which="SA", tol=TOL, v0=v0,
                         maxiter=100000)
    order = np.argsort(evals)
    Es = [float(evals[o]) for o in order]
    Ps = [evecs[:, o] for o in order]
    # resolve M and momentum inside degenerate clusters (ARPACK returns
    # arbitrary rotations of exactly-degenerate pairs, e.g. M=+-1)
    rows = []
    i = 0
    while i < len(Es):
        j = i
        while j + 1 < len(Es) and abs(Es[j + 1] - Es[i]) < 1e-7:
            j += 1
        C = np.stack(Ps[i:j + 1], axis=1)
        Mc = C.conj().T @ (M[:, None] * C)
        w, U = np.linalg.eigh(Mc)
        C2 = C @ U
        k = 0
        while k < len(w):
            l = k
            while l + 1 < len(w) and abs(w[l + 1] - w[k]) < 1e-6:
                l += 1
            C3 = C2[:, k:l + 1]
            Tc = C3.conj().T @ C3[perm, :]
            wt = np.linalg.eigvals(Tc)
            for qq in range(C3.shape[1]):
                rows.append({"E": Es[i], "M": float(w[k]),
                             "p": float(-np.angle(wt[qq]))})
            k = l + 1
        i = j + 1
    rows.sort(key=lambda r: (r["E"], r["M"], r["p"]))
    return rows, time.time() - t0


def main():
    print("=" * 70)
    print("STAGE 1 — ROTOR CHAIN CASIMIR + LL TOWER (B=0.25, J=1.5)")
    print("=" * 70)

    all_rows = {}
    for N in NS:
        rows, secs = run_N(N)
        all_rows[N] = rows
        print(f"\n[N={N}] dim=3^{N}")
        print(f"  E0 = {rows[0]['E']:.12f}")
        for n, r in enumerate(rows):
            print(f"  E{n} = {r['E']:.10f}  dE = {r['E'] - rows[0]['E']:.10f}"
                  f"  M = {r['M']:+.6f}  p = {r['p']:+.6f}"
                  f"  (|p|N/2pi = {abs(r['p']) * N / (2 * np.pi):.3f})")

    # (a) Casimir: E0(N) = eps*N - b/N
    Ns = np.array(NS, dtype=float)
    E0s = np.array([all_rows[int(n)][0]["E"] for n in Ns])
    X = np.stack([Ns, 1.0 / Ns], axis=1)
    (eps, mb), *_ = np.linalg.lstsq(X, E0s, rcond=None)
    b = -mb
    resid = X @ [eps, mb] - E0s
    print(f"\n[casimir] E0(N) = eps*N - b/N:")
    print(f"  eps_inf = {eps:.10f}  b = {b:.10f}  "
          f"max|resid| = {np.max(np.abs(resid)):.2e}")

    # velocity: the M=0, |p| = 2pi/N pair (first phonon descendant, x=1)
    print("\n[velocity] M=0, |p|N/2pi = 1 pair:")
    vs = []
    for N in NS:
        rows = all_rows[N]
        E0 = rows[0]["E"]
        pair = [r for r in rows[1:]
                if abs(r["M"]) < 0.01
                and abs(abs(r["p"]) - 2 * np.pi / N) < 0.3 * 2 * np.pi / N]
        if len(pair) < 2:
            print(f"  N={N}: PAIR NOT FOUND — STOP, diagnose")
            sys.exit(1)
        dE = np.mean([r["E"] for r in pair]) - E0
        v_n = dE * N / (2 * np.pi)  # = v * x, with x expected 1
        vs.append(v_n)
        print(f"  N={N}: {len(pair)} states, dE*N/2pi = {v_n:.6f}")
    v = float(np.mean(vs))
    print(f"  v (= mean dE*N/2pi, x=1 assumed) = {v:.6f} "
          f"(spread {max(vs) - min(vs):.2e})")

    c = 6.0 * b / (np.pi * v)
    print(f"\n[casimir c] c = 6b/(pi v) = {c:.4f}")
    print(f"  oracle: c = 1; entanglement route at J=1.5: "
          f"1.044+/-0.010 (N=12 ED), 1.034+/-0.008 (N=16 ED), "
          f"~1.00 DMRG")
    print(f"  cross-method agreement: "
          f"{'YES' if abs(c - 1.0) < 0.06 else 'NO — STOP, diagnose'}")

    # (b) tower in LL units
    print("\n[tower] x_n = dE*N/(2 pi v) per N:")
    for N in NS:
        rows = all_rows[N]
        E0 = rows[0]["E"]
        parts = []
        for r in rows[1:]:
            x = (r["E"] - E0) * N / (2 * np.pi * v)
            parts.append(f"x={x:.3f}(M={r['M']:+.0f},"
                         f"|p|n={abs(r['p']) * N / (2 * np.pi):.2f})")
        print(f"  N={N}: " + " ".join(parts))

    # (c) K from the winding sector (M=+-1, p=0)
    print("\n[K three-way]")
    xws = []
    for N in NS:
        rows = all_rows[N]
        E0 = rows[0]["E"]
        wind = [r for r in rows[1:]
                if abs(abs(r["M"]) - 1.0) < 0.01 and abs(r["p"]) < 0.3]
        if not wind:
            print(f"  N={N}: WINDING SECTOR NOT FOUND — STOP, diagnose")
            sys.exit(1)
        xw = np.mean([(r["E"] - E0) for r in wind]) * N / (2 * np.pi * v)
        xws.append(xw)
        print(f"  N={N}: x_wind = {xw:.4f} -> K = {1.0 / (4 * xw):.4f}")
    xw = float(np.mean(xws))
    K = 1.0 / (4 * xw)
    print(f"  winding route: K = {K:.3f} (x_wind mean {xw:.4f})")
    print(f"  eta route (FINDINGS 3.5): K = 1/(2 eta) = 1.8-2.2")
    print(f"  BKT universal: K = 2")
    ok = 1.8 - 0.25 <= K <= 2.2 + 0.25
    print(f"  three-way agreement within tolerance: "
          f"{'YES' if ok else 'NO — headline disagreement'}")

    import json
    out = {"J": J, "eps_inf": float(eps), "b": float(b), "v": v,
           "c_casimir": float(c), "x_wind": xw, "K_wind": float(K),
           "levels": {str(N): all_rows[N] for N in NS}}
    with open("min/llstring/tower_results.json", "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print("\nwrote min/llstring/tower_results.json")


if __name__ == "__main__":
    main()
