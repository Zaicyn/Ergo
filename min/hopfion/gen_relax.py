#!/usr/bin/env python3
"""gen_relax.py — emit hopfion_relax_<tag>.ergo (Jacobi-metric graph
geodesic) for a baked point set.

Usage: python3 gen_relax.py <points.txt|grid:N> <tag>
  points.txt: "x y" rows (planar, any sign of y — we shift y up so depth
  below the start level is positive; shift documented in the header).
  "grid:N" synthesizes an NxN regular grid baseline.

The emitted Ergo program computes the discrete geodesic A -> B on the
symmetric kNN graph (k = min(32, max(8, n/8)); see the anisotropy note
below) under the brachistochrone Jacobi metric
edge cost = exact integral of ds/sqrt(depth) along the straight edge
with depth linear between endpoints:
  int_0^1 |e| / sqrt(d0 + (d1-d0) t) dt = 2 |e| / (sqrt(d0) + sqrt(d1)),
depth = YTOP - y, YTOP = 1 + 1e-6 (offset avoids a singular edge along
the top row). Geodesics of ds/sqrt(depth) are cycloids with a cusp at
A — the analytic oracle used by analyze_cycloid.py.

Structure of the emitted program:
  1. O(N^2) Dijkstra over the baked graph -> globally optimal discrete
     path (prints "init cost").
  2. Local-move relaxation sweeps (swap to a common neighbor of both
     path-neighbors, delete a node whose neighbors are adjacent, insert
     a common neighbor on an edge; strict cost decrease only) — serves as
     an independent checker: starting from the Dijkstra optimum it must
     not improve the cost (prints "cost" and "converged at sweep").
  3. PATH dump.

History / traps documented for the oracle record:
  - The first version used cost sqrt(y_mid)*dist. Beltrami on that
    integrand gives y = C^2 (1 + y'^2), a PARABOLA — not the cycloid.
    The flat-grid oracle exposed it.
  - Midpoint-rule edge cost dist/sqrt(YTOP - y_mid) biases the discrete
    optimum toward over-sagging (1/sqrt(d) is convex, so the midpoint
    underestimates steep edges): on grids the path hugged the bottom row
    early and the curve-shape error did not shrink from grid30 to grid60
    even though the cost did. Replaced by the exact linear-depth edge
    integral above, after which shape and cost converge together.
  - BFS shortest-hop init + local moves only traps in poor local optima
    (on grid60 the relaxed path stayed nearly straight, ~8% mean curve
    error, no improvement over grid30): developing the cycloid sag from
    a straight path needs a coordinated multi-node move. Replaced by the
    Dijkstra geodesic, which is the object the physics question asks
    about anyway.
  - On a regular grid a kNN graph with k=8 is the king-move (Moore)
    graph: only 8 edge directions exist, so discrete geodesics converge
    to the geodesics of an ANISOTROPIC chamfer norm, not the Euclidean
    one (the digital-staircase paradox) — cost error stuck at ~2.5% from
    grid30 to grid60 with a systematic over-sagging shape. Irregular
    point sets (the Hopf bases) have arbitrary edge directions and no
    such artifact. k = min(32, max(8, n/8)) gives grids enough
    directions (k=32: cost error ~0.3%, shape error ~0.5% and shrinking)
    without trivializing small sets.
"""
import sys
import numpy as np

YTOP = 1.0 + 1.0e-6
R_TARGET = 1.43   # target dx/depth for B, matches a mid-range cycloid arch


def load_points(spec):
    if spec.startswith("grid:"):
        n = int(spec.split(":")[1])
        xs = np.linspace(0.0, 1.0, n)
        P = np.array([(x, y) for x in xs for y in xs])
        return P, f"regular grid {n}x{n}"
    P = np.loadtxt(spec)
    return P, spec


def build_graph(P, k):
    """Symmetric k-NN graph (robust for any point set; Delaunay would
    also work but kNN needs no scipy). Asserts connectivity."""
    n = len(P)
    D = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=-1)
    np.fill_diagonal(D, np.inf)
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in np.argsort(D[i])[:k]:
            adj[i].add(int(j))
            adj[int(j)].add(i)
    seen = {0}
    stack = [0]
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    assert len(seen) == n, f"kNN graph disconnected: {len(seen)}/{n}"
    deg = [len(a) for a in adj]
    kmax = max(deg)
    ADJ = np.zeros((n, kmax), dtype=int)
    for i in range(n):
        for t, j in enumerate(sorted(adj[i])):
            ADJ[i, t] = j + 1  # 1-based, 0-padded
    return ADJ, deg, kmax


def pick_endpoints(P):
    """A = highest point. B = point at least ~half the depth range down
    whose dx/depth is closest to R_TARGET (keeps the cycloid arch shape
    comparable across cases; wide tie-break)."""
    a = int(np.argmax(P[:, 1]))
    depth = 1.0 - P[:, 1]
    cand = np.where(depth >= 0.45 * depth.max())[0]
    cand = cand[cand != a]
    dx = np.abs(P[cand, 0] - P[a, 0])
    r = dx / depth[cand]
    score = np.abs(r - R_TARGET) - 0.01 * dx
    b = int(cand[np.argmin(score)])
    return a, b


def emit(P, tag, note):
    # normalize: x to [0,1], y to [0.25,1] (depth = 1 - y in [0, 0.75])
    P = P.copy()
    P[:, 0] -= P[:, 0].min()
    spanx = P[:, 0].max()
    P[:, 0] /= spanx
    P[:, 1] -= P[:, 1].min()
    P[:, 1] /= P[:, 1].max()
    P[:, 1] = 0.25 + 0.75 * P[:, 1]
    n = len(P)
    # adaptive degree: grids need many edge directions to suppress king-move
    # lattice anisotropy (see docstring); irregular sets need few; tiny sets
    # must not trivialize to a complete graph
    k = min(32, max(8, n // 8))
    ADJ, deg, kmax = build_graph(P, k)
    a, b = pick_endpoints(P)

    def data1d(name, vals, fmt="{:.12g}"):
        per = 10 if fmt == "%d" else 6
        lines = [f"DATA {name} / &"]
        chunks = [vals[i:i + per] for i in range(0, len(vals), per)]
        for ci, ch in enumerate(chunks):
            end = " /" if ci == len(chunks) - 1 else ", &"
            if fmt == "%d":
                body = ", ".join(str(int(v)) for v in ch)
            else:
                body = ", ".join(fmt.format(v) for v in ch)
            lines.append("  " + body + end)
        return lines

    L = []
    L.append(f"! hopfion_relax_{tag}.ergo — GENERATED by gen_relax.py "
             f"(do not edit)")
    L.append(f"! source: {note}")
    L.append(f"! {n} points, kNN k={k} graph (k=min(32,max(8,n/8))), "
             f"edge cost 2*dist/(sqrt(d0)+sqrt(d1)) "
             f"(exact ds/sqrt(depth) edge integral), d=YTOP-y, YTOP=1+1e-6; "
             f"y shifted to [0.25,1].")
    L.append(f"! A={a + 1} (highest y), B={b + 1} (dx/depth near {R_TARGET}); "
             f"Dijkstra geodesic + local-move polish.")
    L.append("IMPLICIT NONE")
    L.append(f"INTEGER, PARAMETER :: NP = {n}, KMAX = {kmax}, MP = {n}")
    L.append(f"INTEGER, PARAMETER :: NA = {a + 1}, NB = {b + 1}, NSWEEP = 600")
    L.append("REAL, PARAMETER :: YTOP = 1.0 + 1.0e-6")
    L.append("STATIC REAL :: PX(NP), PY(NP), DIST(NP)")
    L.append("STATIC INTEGER :: ADJ(NP, KMAX), DEG(NP)")
    L.append("STATIC INTEGER :: PTH(MP), PREV(NP), VIS(NP), TMP(NP)")
    L += data1d("PX", P[:, 0], "{:.12g}")
    L += data1d("PY", P[:, 1], "{:.12g}")
    L += data1d("DEG", deg, "%d")
    L += data1d("ADJ", ADJ.flatten(order="F"), "%d")  # column-major!
    L.append("REAL :: C0, C1, C2, CB, COST, DB")
    L.append("INTEGER :: I, J, T, M, CHANGED, C, CC, OK, KM1, KP1, MV, T2, U")
    L.append("")
    # ---- Dijkstra: global discrete geodesic NA -> NB ----
    L.append("DO I = 1, NP")
    L.append("  DIST(I) := 1.0e30")
    L.append("  PREV(I) := 0")
    L.append("  VIS(I) := 0")
    L.append("ENDDO")
    L.append("DIST(NA) := 0.0")
    L.append("DO T = 1, NP")
    L.append("  U := 0")
    L.append("  DB := 1.0e29")
    L.append("  DO I = 1, NP")
    L.append("    IF (VIS(I) == 0) THEN")
    L.append("      IF (DIST(I) < DB) THEN")
    L.append("        DB := DIST(I)")
    L.append("        U := I")
    L.append("      ENDIF")
    L.append("    ENDIF")
    L.append("  ENDDO")
    L.append("  IF (U > 0) THEN")
    L.append("    VIS(U) := 1")
    L.append("    DO J = 1, DEG(U)")
    L.append("      C := ADJ(U, J)")
    L.append("      IF (C > 0) THEN")
    L.append("        C1 := 2.0 * SQRT((PX(U) - PX(C)) ** 2 &")
    L.append("          + (PY(U) - PY(C)) ** 2) / (SQRT(YTOP - PY(U)) &")
    L.append("          + SQRT(YTOP - PY(C)))")
    L.append("        IF (DIST(U) + C1 < DIST(C)) THEN")
    L.append("          DIST(C) := DIST(U) + C1")
    L.append("          PREV(C) := U")
    L.append("        ENDIF")
    L.append("      ENDIF")
    L.append("    ENDDO")
    L.append("  ENDIF")
    L.append("ENDDO")
    L.append('WRITE(*, "init cost %.12e") DIST(NB)')
    # ---- reconstruct path B -> A via PREV, then reverse ----
    L.append("M := 0")
    L.append("C := NB")
    L.append("DO WHILE (C > 0)")
    L.append("  M := M + 1")
    L.append("  TMP(M) := C")
    L.append("  C := PREV(C)")
    L.append("ENDDO")
    L.append("DO I = 1, M")
    L.append("  PTH(I) := TMP(M + 1 - I)")
    L.append("ENDDO")
    L.append("")
    # ---- local-move relaxation (independent optimality checker) ----
    L.append("DO T = 1, NSWEEP")
    L.append("  CHANGED := 0")
    L.append("  DO I = 2, M - 1")
    L.append("    KM1 := PTH(I - 1)")
    L.append("    KP1 := PTH(I + 1)")
    L.append("    ! current two-edge cost")
    L.append("    C1 := 2.0 * SQRT((PX(KM1) - PX(PTH(I))) ** 2 &")
    L.append("      + (PY(KM1) - PY(PTH(I))) ** 2) / (SQRT(YTOP - PY(KM1)) &")
    L.append("      + SQRT(YTOP - PY(PTH(I))))")
    L.append("    C2 := 2.0 * SQRT((PX(PTH(I)) - PX(KP1)) ** 2 &")
    L.append("      + (PY(PTH(I)) - PY(KP1)) ** 2) / (SQRT(YTOP - PY(PTH(I))) &")
    L.append("      + SQRT(YTOP - PY(KP1)))")
    L.append("    C0 := C1 + C2")
    L.append("    MV := 0")
    L.append("    CB := C0")
    L.append("    CC := PTH(I)")
    L.append("    ! (a) swap to a node adjacent to both path neighbors")
    L.append("    DO J = 1, DEG(KM1)")
    L.append("      C := ADJ(KM1, J)")
    L.append("      IF (C > 0) THEN")
    L.append("        IF (C /= KM1) THEN")
    L.append("          IF (C /= KP1) THEN")
    L.append("            OK := 0")
    L.append("            DO T2 = 1, DEG(KP1)")
    L.append("              IF (ADJ(KP1, T2) == C) THEN")
    L.append("                OK := 1")
    L.append("              ENDIF")
    L.append("            ENDDO")
    L.append("            DO T2 = 1, M")
    L.append("              IF (PTH(T2) == C) THEN")
    L.append("                OK := 0")
    L.append("              ENDIF")
    L.append("            ENDDO")
    L.append("            IF (OK == 1) THEN")
    L.append("              C1 := 2.0 * SQRT((PX(KM1) - PX(C)) ** 2 &")
    L.append("                + (PY(KM1) - PY(C)) ** 2) / (SQRT(YTOP - PY(KM1)) &")
    L.append("                + SQRT(YTOP - PY(C)))")
    L.append("              C2 := 2.0 * SQRT((PX(C) - PX(KP1)) ** 2 &")
    L.append("                + (PY(C) - PY(KP1)) ** 2) / (SQRT(YTOP - PY(C)) &")
    L.append("                + SQRT(YTOP - PY(KP1)))")
    L.append("              IF (C1 + C2 < CB - 1.0e-12) THEN")
    L.append("                CB := C1 + C2")
    L.append("                CC := C")
    L.append("                MV := 1")
    L.append("              ENDIF")
    L.append("            ENDIF")
    L.append("          ENDIF")
    L.append("        ENDIF")
    L.append("      ENDIF")
    L.append("    ENDDO")
    L.append("    ! (b) delete node if its neighbors are adjacent")
    L.append("    OK := 0")
    L.append("    DO J = 1, DEG(KM1)")
    L.append("      IF (ADJ(KM1, J) == KP1) THEN")
    L.append("        OK := 1")
    L.append("      ENDIF")
    L.append("    ENDDO")
    L.append("    IF (OK == 1) THEN")
    L.append("      C1 := 2.0 * SQRT((PX(KM1) - PX(KP1)) ** 2 &")
    L.append("        + (PY(KM1) - PY(KP1)) ** 2) / (SQRT(YTOP - PY(KM1)) &")
    L.append("        + SQRT(YTOP - PY(KP1)))")
    L.append("      IF (C1 < CB - 1.0e-12) THEN")
    L.append("        CB := C1")
    L.append("        MV := 2")
    L.append("      ENDIF")
    L.append("    ENDIF")
    L.append("    IF (MV == 1) THEN")
    L.append("      PTH(I) := CC")
    L.append("      CHANGED := 1")
    L.append("    ENDIF")
    L.append("    IF (MV == 2) THEN")
    L.append("      DO J = I, M - 1")
    L.append("        PTH(J) := PTH(J + 1)")
    L.append("      ENDDO")
    L.append("      M := M - 1")
    L.append("      CHANGED := 1")
    L.append("    ENDIF")
    L.append("  ENDDO")
    L.append("  ! (c) insert a common neighbor on an edge when it lowers cost")
    L.append("  I := 1")
    L.append("  DO WHILE (I < M)")
    L.append("    KM1 := PTH(I)")
    L.append("    KP1 := PTH(I + 1)")
    L.append("    C0 := 2.0 * SQRT((PX(KM1) - PX(KP1)) ** 2 &")
    L.append("      + (PY(KM1) - PY(KP1)) ** 2) / (SQRT(YTOP - PY(KM1)) &")
    L.append("      + SQRT(YTOP - PY(KP1)))")
    L.append("    CB := C0")
    L.append("    CC := 0")
    L.append("    DO J = 1, DEG(KM1)")
    L.append("      C := ADJ(KM1, J)")
    L.append("      IF (C > 0) THEN")
    L.append("        OK := 0")
    L.append("        DO T2 = 1, DEG(KP1)")
    L.append("          IF (ADJ(KP1, T2) == C) THEN")
    L.append("            OK := 1")
    L.append("          ENDIF")
    L.append("        ENDDO")
    L.append("        DO T2 = 1, M")
    L.append("          IF (PTH(T2) == C) THEN")
    L.append("            OK := 0")
    L.append("          ENDIF")
    L.append("        ENDDO")
    L.append("        IF (OK == 1) THEN")
    L.append("          C1 := 2.0 * SQRT((PX(KM1) - PX(C)) ** 2 &")
    L.append("            + (PY(KM1) - PY(C)) ** 2) / (SQRT(YTOP - PY(KM1)) &")
    L.append("            + SQRT(YTOP - PY(C)))")
    L.append("          C2 := 2.0 * SQRT((PX(C) - PX(KP1)) ** 2 &")
    L.append("            + (PY(C) - PY(KP1)) ** 2) / (SQRT(YTOP - PY(C)) &")
    L.append("            + SQRT(YTOP - PY(KP1)))")
    L.append("          IF (C1 + C2 < CB - 1.0e-12) THEN")
    L.append("            CB := C1 + C2")
    L.append("            CC := C")
    L.append("          ENDIF")
    L.append("        ENDIF")
    L.append("      ENDIF")
    L.append("    ENDDO")
    L.append("    IF (CC > 0) THEN")
    L.append("      DO J = M, I + 1, -1")
    L.append("        PTH(J + 1) := PTH(J)")
    L.append("      ENDDO")
    L.append("      PTH(I + 1) := CC")
    L.append("      M := M + 1")
    L.append("      CHANGED := 1")
    L.append("    ENDIF")
    L.append("    I := I + 1")
    L.append("  ENDDO")
    L.append("  IF (CHANGED == 0) THEN")
    L.append('    WRITE(*, "converged at sweep %d") T')
    L.append("    T := NSWEEP")
    L.append("  ENDIF")
    L.append("ENDDO")
    L.append("")
    L.append("COST := 0.0")
    L.append("DO I = 1, M - 1")
    L.append("  KM1 := PTH(I)")
    L.append("  KP1 := PTH(I + 1)")
    L.append("  COST := COST + 2.0 * SQRT((PX(KM1) - PX(KP1)) ** 2 &")
    L.append("    + (PY(KM1) - PY(KP1)) ** 2) / (SQRT(YTOP - PY(KM1)) &")
    L.append("    + SQRT(YTOP - PY(KP1)))")
    L.append("ENDDO")
    L.append('WRITE(*, "cost %.12e") COST')
    L.append("DO I = 1, M")
    L.append('  WRITE(*, "PATH %d %.12e %.12e") I, PX(PTH(I)), PY(PTH(I))')
    L.append("ENDDO")
    L.append('WRITE(*, "done nodes %d") M')
    return "\n".join(L) + "\n"


def main():
    spec, tag = sys.argv[1], sys.argv[2]
    P, note = load_points(spec)
    out = emit(P, tag, note)
    path = f"min/hopfion/hopfion_relax_{tag}.ergo"
    with open(path, "w") as f:
        f.write(out)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
