"""Gap phase diagram gap(J, B) for the quantum rotor chain.

Stage 1: 12-site spin-1 chain (m in {-1,0,1}, dim 3^12), grid
  B in [0.10, 0.40] step 0.05,  J in [0.0, 1.5] step 0.25,
plus J = 1.75, 2.0 at B = 0.25. Uses v0 continuation along J for speed.

Stage 2: truncation robustness — Lmax=2 rotors (5 states/site) on an 8-site
ring (dim 5^8 = 390625) at key points, with and without the cos(3phi) drift
term (which is identically zero in the spin-1 basis but not for Lmax=2).

Matrix-free LinearOperator throughout (reshape to (D,)*N tensor, np.tensordot
for site ops). eigsh k=4, which='SA', tol=1e-12. Results written
incrementally to results_gap_map.json.
"""

import json
import time

import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh

from rotor_single import K_PHASE, K_BIAS, K_DRIFT, forbidden_projector

I = 1.0
B_GRID = np.round(np.arange(0.10, 0.4001, 0.05), 2)
J_GRID = np.round(np.arange(0.0, 1.5001, 0.25), 2)
EXTRA_J = [1.75, 2.0]  # at B = 0.25 only

OUT = "results_gap_map.json"


class RotorChain:
    """N-site ring, D = 2*Lmax+1 states per site, matrix-free."""

    def __init__(self, N, Lmax, drift=True):
        self.N, self.Lmax, self.D = N, Lmax, 2 * Lmax + 1
        self.DIM = self.D ** N
        self.refs = 2.0 * np.pi * np.arange(N) / N
        self.drift = drift
        L = Lmax
        m = np.arange(-L, L + 1)
        n = self.D
        # cos phi, sin phi
        c = np.zeros((n, n))
        c[np.arange(1, n), np.arange(n - 1)] = 0.5
        c += c.T
        s = np.zeros((n, n), dtype=complex)
        s[np.arange(1, n), np.arange(n - 1)] = -0.5j  # <m+1|sin phi|m>
        s += s.conj().T
        self.C, self.S = c, s
        self.EIPHI = c + 1j * s
        # cos(3 phi): <m+-3|cos3phi|m> = 1/2
        g3 = np.zeros((n, n))
        for a, b in zip(m, m + 3):
            if -L <= b <= L:
                g3[b + L, a + L] = 0.5
                g3[a + L, b + L] = 0.5
        self.G3 = g3
        # kinetic diagonal
        idx = np.arange(self.DIM)
        diag = np.zeros(self.DIM)
        for i in range(N):
            mi = (idx // self.D ** i) % self.D - L
            diag += (mi * mi) / (2.0 * I)
        self.DIAG = diag
        self.P = [forbidden_projector(Lmax, r) for r in self.refs]

    def cos_minus(self, a):
        return np.cos(a) * self.C + np.sin(a) * self.S

    def apply_site(self, t, O, i):
        tm = np.moveaxis(t, i, 0)
        tm = np.tensordot(O, tm, axes=([1], [0]))
        return np.moveaxis(tm, 0, i)

    def make_matvec(self, B, J):
        D, N = self.D, self.N
        site_ops = []
        for i in range(N):
            O = (-K_PHASE * self.cos_minus(self.refs[i])
                 - B * K_BIAS * self.cos_minus(self.refs[i] + np.pi))
            if self.drift:
                O = O + (K_DRIFT / 3.0) * self.G3
            site_ops.append(O)
        C, S, DIAG = self.C, self.S, self.DIAG

        def matvec(v):
            t = v.reshape((D,) * N)
            out = (DIAG * v).reshape((D,) * N)
            for i in range(N):
                out = out + self.apply_site(t, site_ops[i], i)
            if J != 0.0:
                for i in range(N):
                    j = (i + 1) % N
                    out = out - J * (self.apply_site(self.apply_site(t, C, i), C, j)
                                     + self.apply_site(self.apply_site(t, S, i), S, j))
            return out.ravel()

        return matvec

    def site_expect(self, psi, O, i):
        t = psi.reshape((self.D,) * self.N)
        return np.vdot(t.ravel(), self.apply_site(t, O, i).ravel())

    def run_point(self, B, J, v0=None):
        t0 = time.time()
        A = LinearOperator((self.DIM, self.DIM), matvec=self.make_matvec(B, J),
                           dtype=complex)
        evals, evecs = eigsh(A, k=4, which="SA", tol=1e-12, maxiter=20000, v0=v0)
        order = np.argsort(evals)
        evals = evals[order]
        psi = evecs[:, order[0]]
        w = float(np.mean([self.site_expect(psi, self.P[i], i).real
                           for i in range(self.N)]))
        r = float(np.mean([abs(self.site_expect(psi, self.EIPHI, i))
                           for i in range(self.N)]))
        return ({
            "B": float(B), "J": float(J),
            "E0": float(evals[0]), "gap": float(evals[1] - evals[0]),
            "w": w, "r": r, "seconds": time.time() - t0,
        }, psi)


def save(results):
    with open(OUT, "w") as f:
        json.dump(results, f, indent=1)


def main():
    results = {"params": {
        "K_PHASE": K_PHASE, "K_BIAS": K_BIAS, "K_DRIFT": K_DRIFT, "I": I,
        "B_grid": list(map(float, B_GRID)), "J_grid": list(map(float, J_GRID)),
    }}

    # ---- Stage 1: 12-site spin-1 grid -------------------------------------
    chain = RotorChain(12, 1, drift=True)  # drift is a no-op at Lmax=1
    pts = []
    for B in B_GRID:
        v0 = None
        for J in J_GRID:
            pt, psi = chain.run_point(float(B), float(J), v0=v0)
            v0 = psi  # continuation along J
            pts.append(pt)
            print(f"[grid] B={B:.2f} J={J:.2f} E0={pt['E0']:.6f} "
                  f"gap={pt['gap']:.6f} w={pt['w']:.6f} r={pt['r']:.6f} "
                  f"({pt['seconds']:.1f}s)", flush=True)
            results["grid"] = pts
            save(results)

    extra = []
    for J in EXTRA_J:
        pt, _ = chain.run_point(0.25, float(J))
        extra.append(pt)
        print(f"[extra] B=0.25 J={J:.2f} gap={pt['gap']:.6f} "
              f"({pt['seconds']:.1f}s)", flush=True)
        results["extra_J_at_B0.25"] = extra
        save(results)

    # J=0 column validation against 12 independent Lmax=1 rotors
    from rotor_single import sweep as single_sweep
    single = {o["B"]: o for o in single_sweep(1, I=1.0, b_values=B_GRID)}
    checks = []
    for pt in pts:
        if pt["J"] == 0.0:
            s = single[round(pt["B"], 2)]
            checks.append({
                "B": pt["B"],
                "dE": abs(pt["E0"] - 12 * s["E0"]),
                "dw": abs(pt["w"] - s["w"]),
            })
    results["validation_J0"] = {
        "max_dE": max(c["dE"] for c in checks),
        "max_dw": max(c["dw"] for c in checks),
        "checks": checks,
    }
    save(results)
    print("[validation]", results["validation_J0"]["max_dE"],
          results["validation_J0"]["max_dw"], flush=True)

    # ---- Stage 2: Lmax=2, 8-site ring --------------------------------------
    lmax2 = []
    chain2d = RotorChain(8, 2, drift=True)
    chain2n = RotorChain(8, 2, drift=False)
    for B, J in [(0.25, 0.0), (0.25, 0.5), (0.25, 1.0), (0.5, 0.5)]:
        pt, _ = chain2d.run_point(B, J)
        pt["drift"] = True
        lmax2.append(pt)
        print(f"[Lmax2] B={B} J={J} drift=1 gap={pt['gap']:.6f} w={pt['w']:.6f} "
              f"({pt['seconds']:.1f}s)", flush=True)
        results["lmax2_N8"] = lmax2
        save(results)
    pt, _ = chain2n.run_point(0.25, 0.5)
    pt["drift"] = False
    lmax2.append(pt)
    print(f"[Lmax2] B=0.25 J=0.5 drift=0 gap={pt['gap']:.6f} w={pt['w']:.6f} "
          f"({pt['seconds']:.1f}s)", flush=True)
    results["lmax2_N8"] = lmax2
    save(results)

    print("done ->", OUT, flush=True)


if __name__ == "__main__":
    main()
