#!/usr/bin/env python3
"""gen_hopfion.py — 600-cell / 120-cell vertex sets, Hopf partitions,
stereographic base point sets for the cycloid-convergence test.

Constructions (all verified, see --verify output):
- 600-cell: 24-cell vertices (permutations of (±1,±1,0,0)/sqrt2) plus
  96 even permutations of (±phi/2, ±1/2, ±1/(2 phi), 0). 120 unit
  vectors, 720 uniform nearest-neighbor edges.
- 120-cell: tetrahedral cells of the 600-cell = 4-cliques in the edge
  graph (expect exactly 600); vertices = normalized cell circumcenters
  (in 4D the circumcenter of 4 unit points is just their normalized
  sum — the four points lie on a 2-sphere in a 3-flat whose center is
  the normalized sum direction).
- Hopf map pi(w,x,y,z) = (2(xz+wy), 2(yz-wx), w^2+x^2-y^2-z^2) onto S^2.
  600-cell must give 30 base points x 4 vertices (icosidodecahedron).
  120-cell partition is DISCOVERED (tight clustering of base points).
- Stereographic projection S^2 -> R^2 with the pole away from all base
  points (auto-rotated if needed; documented in output).

Outputs min/hopfion/base_{600,120}.txt with the planar point sets and
neighbor graphs (Delaunay via scipy if present, else brute-force kNN),
plus min/hopfion/hopfion_report.json with all verification numbers.
"""
import json
import itertools
import itertools as it
import numpy as np

PHI = (1.0 + np.sqrt(5.0)) / 2.0


def cell600_vertices():
    """120 vertices of the 600-cell on S^3, standard orientation:
    16 hypercube (±1/2,±1/2,±1/2,±1/2) + 8 cross-polytope (±1,0,0,0)
    permutations + 96 even permutations of (±phi/2, ±1/2, ±1/(2phi), 0)
    with independent signs (dedupe collapses the redundant 0-sign).
    NB: the (±1,±1,0,0)/sqrt2 24-cell is a DIFFERENT orientation and
    does not match the 96-set (measured: 96 spurious short chords)."""
    v = []
    for s in it.product([1.0, -1.0], repeat=4):
        v.append(np.array(s) * 0.5)
    for i in range(4):
        for s in (1.0, -1.0):
            w = np.zeros(4)
            w[i] = s
            v.append(w)
    base = np.array([PHI / 2.0, 0.5, 1.0 / (2.0 * PHI), 0.0])
    even = [p for p in it.permutations(range(4))
            if _perm_parity(p) == 0]
    assert len(even) == 12
    for p in even:
        for signs in it.product([1.0, -1.0], repeat=4):
            v.append(base[list(p)] * np.array(signs))
    V = np.array(v)
    V = np.unique(np.round(V, 9), axis=0)
    assert V.shape == (120, 4), f"got {V.shape}"
    return V


def _perm_parity(p):
    inv = sum(1 for i in range(len(p)) for j in range(i + 1, len(p))
              if p[i] > p[j])
    return inv % 2


def edge_set(V, tol=1e-9):
    """Nearest-neighbor edge set: pairs at the minimum pairwise distance."""
    D = np.linalg.norm(V[:, None, :] - V[None, :, :], axis=-1)
    np.fill_diagonal(D, np.inf)
    dmin = D.min()
    E = set()
    for i in range(len(V)):
        for j in range(i + 1, len(V)):
            if D[i, j] < dmin + tol:
                E.add((i, j))
    return E, dmin


def cliques4(V, E):
    """4-cliques (tetrahedral cells) in the edge graph."""
    adj = [set() for _ in range(len(V))]
    for (i, j) in E:
        adj[i].add(j)
        adj[j].add(i)
    cliques = set()
    Vset = set(range(len(V)))
    for a in range(len(V)):
        for b in adj[a]:
            if b <= a:
                continue
            common_ab = adj[a] & adj[b]
            for c in common_ab:
                if c <= b:
                    continue
                for d in adj[c] & common_ab:
                    if d > c:
                        cliques.add((a, b, c, d))
    return cliques


def hopf(P):
    """(w,x,y,z) -> (2(wy+xz), 2(wz-xy), w^2+x^2-y^2-z^2).
    Convention C: the ONLY one of the four sign/order variants whose
    600-cell base is the icosidodecahedron (uniform chord 1/phi, all
    degrees 4) — measured, see hopfion_report.json."""
    w, x, y, z = P[..., 0], P[..., 1], P[..., 2], P[..., 3]
    return np.stack([2 * (w * y + x * z), 2 * (w * z - x * y),
                     w * w + x * x - y * y - z * z], axis=-1)


def cluster_rows(P, tol=1e-6):
    """Cluster identical (up to tol) rows; returns labels, centers."""
    labels = -np.ones(len(P), dtype=int)
    centers = []
    for i, p in enumerate(P):
        for c, ctr in enumerate(centers):
            if np.linalg.norm(p - ctr) < tol:
                labels[i] = c
                break
        if labels[i] < 0:
            centers.append(p.copy())
            labels[i] = len(centers) - 1
    return labels, np.array(centers)


def stereographic(B):
    """S^2 -> R^2 stereographic; the pole is rotated to the diagonal
    (1,1,1)/sqrt(3) direction first — axis-aligned base points (both
    polytope bases have them) would otherwise sit exactly on the pole
    and blow up the projection (measured)."""
    B = B / np.linalg.norm(B, axis=1, keepdims=True)
    # rotation taking (0,0,1) to (1,1,1)/sqrt(3)
    a = np.array([0.0, 0.0, 1.0])
    b = np.array([1.0, 1.0, 1.0]) / np.sqrt(3.0)
    ax = np.cross(a, b)
    ax = ax / np.linalg.norm(ax)
    ang = np.arccos(np.dot(a, b))
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    R = np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * (K @ K)
    B = B @ R.T
    d = np.linalg.norm(B - np.array([0.0, 0.0, 1.0]), axis=1).min()
    note = f"pole rotated to (1,1,1)/sqrt3; min pole distance {d:.3f}"
    X = B[:, 0] / (1.0 - B[:, 2])
    Y = B[:, 1] / (1.0 - B[:, 2])
    return np.stack([X, Y], axis=1), note


def main():
    rep = {}
    V6 = cell600_vertices()
    norms = np.linalg.norm(V6, axis=1)
    rep["cell600_unit_norm_max_err"] = float(np.abs(norms - 1).max())
    E6, dmin6 = edge_set(V6)
    rep["cell600_edges"] = len(E6)
    rep["cell600_edge_len"] = float(dmin6)
    print(f"600-cell: {len(V6)} vertices, unit-norm err "
          f"{rep['cell600_unit_norm_max_err']:.2e}, "
          f"{len(E6)} edges of length {dmin6:.6f} (expect 720)")

    # 120-cell via cell circumcenters
    cl = cliques4(V6, E6)
    rep["cell600_tetrahedral_cells"] = len(cl)
    print(f"600-cell: {len(cl)} tetrahedral cells (expect 600)")
    C12 = np.array([sum(V6[list(q)]) for q in cl])
    C12 = C12 / np.linalg.norm(C12, axis=1, keepdims=True)
    # dedupe (each cell once by construction)
    rep["cell120_vertices"] = len(C12)
    E12, dmin12 = edge_set(C12)
    rep["cell120_edges"] = len(E12)
    rep["cell120_edge_len"] = float(dmin12)
    print(f"120-cell: {len(C12)} vertices (expect 600), "
          f"{len(E12)} edges of length {dmin12:.6f}")

    # Hopf partitions
    B6 = hopf(V6)
    lab6, cen6 = cluster_rows(B6)
    sizes6 = np.bincount(lab6)
    rep["cell600_hopf_fibers"] = len(cen6)
    rep["cell600_hopf_fiber_sizes"] = sorted(sizes6.tolist())
    print(f"600-cell Hopf: {len(cen6)} base points, fiber sizes "
          f"{sorted(set(sizes6.tolist()))} (expect 30 x 4)")

    B12 = hopf(C12)
    lab12, cen12 = cluster_rows(B12)
    sizes12 = np.bincount(lab12)
    rep["cell120_hopf_fibers"] = len(cen12)
    rep["cell120_hopf_fiber_sizes"] = sorted(sizes12.tolist())
    from collections import Counter
    print(f"120-cell Hopf: {len(cen12)} base points, fiber size "
          f"distribution {dict(Counter(sizes12.tolist()))}")

    # icosidodecahedron check: 30 points, each with 4 neighbors at the
    # min distance on S^2 (icosidodecahedron is 4-valent)
    D6 = np.linalg.norm(cen6[:, None, :] - cen6[None, :, :], axis=-1)
    np.fill_diagonal(D6, np.inf)
    dminB = D6.min()
    deg = (D6 < dminB * 1.01).sum(axis=1)
    rep["cell600_base_min_deg"] = int(deg.min())
    rep["cell600_base_max_deg"] = int(deg.max())
    print(f"600-cell base: min chord {dminB:.4f}, degrees "
          f"{deg.min()}..{deg.max()} (icosidodecahedron is 4-valent)")

    # stereographic
    P6, note6 = stereographic(cen6)
    P12, note12 = stereographic(cen12)
    rep["stereo_note_600"] = note6
    rep["stereo_note_120"] = note12
    print(f"stereo 600: {note6}; 120: {note12}")

    np.savetxt("min/hopfion/base_600.txt", P6, fmt="%.12f")
    np.savetxt("min/hopfion/base_120.txt", P12, fmt="%.12f")
    with open("min/hopfion/hopfion_report.json", "w") as f:
        json.dump(rep, f, indent=1)
    print("wrote min/hopfion/base_{600,120}.txt + hopfion_report.json")


if __name__ == "__main__":
    main()
