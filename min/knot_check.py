#!/usr/bin/env python3
"""
Knot check for the user's 3D curve:

    x = sin(t) - 0.5 sin(3t)
    y = -cos(t) + 0.5 cos(3t)
    z = cos(t) cos(3t)

Questions:
  1. Is the curve embedded (no self-intersections)? Viviani's curve
     has a double point; if this perturbation still does, it is not
     a knot at all.
  2. If embedded: is it the trefoil? Test via Fox 3-coloring of a
     projected diagram (unknot: 3 colorings; trefoil: 9) plus the
     diagram crossing number.
"""

import numpy as np

TWO_PI = 2.0 * np.pi


def curve(t):
    x = np.sin(t) - 0.5 * np.sin(3.0 * t)
    y = -np.cos(t) + 0.5 * np.cos(3.0 * t)
    z = np.cos(t) * np.cos(3.0 * t)
    return np.stack([x, y, z], axis=-1)


# ── 1. Embeddedness ──────────────────────────────────────────────

def min_nonlocal_distance(N=4000, exclude_frac=0.02):
    """Minimum 3D distance between points whose parameter separation
    exceeds exclude_frac of the period (both directions)."""
    t = np.linspace(0.0, TWO_PI, N, endpoint=False)
    pts = curve(t)
    best = np.inf
    best_pair = None
    for i in range(N):
        # parameter-circular distance
        d_ij = np.minimum((np.arange(N) - i) % N, (i - np.arange(N)) % N)
        mask = d_ij > N * exclude_frac
        if not np.any(mask):
            continue
        d = np.linalg.norm(pts[mask] - pts[i], axis=1)
        j = np.argmin(d)
        if d[j] < best:
            best = d[j]
            best_pair = (t[i], t[np.arange(N)[mask][j]])
    return best, best_pair


# ── 2. Projection and crossings ──────────────────────────────────

def project(pts, direction):
    """Project onto plane perpendicular to direction; return 2D coords
    and heights along direction."""
    d = direction / np.linalg.norm(direction)
    h = pts @ d
    # orthonormal basis for the plane
    a = np.array([1.0, 0.0, 0.0])
    if abs(a @ d) > 0.9:
        a = np.array([0.0, 1.0, 0.0])
    e1 = a - d * (a @ d)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(d, e1)
    return np.stack([pts @ e1, pts @ e2], axis=-1), h


def seg_intersect(p1, p2, p3, p4):
    """2D segment intersection; return (s, t) parameters or None."""
    r = p2 - p1
    s = p4 - p3
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-14:
        return None
    q = p3 - p1
    ts = (q[0] * s[1] - q[1] * s[0]) / den
    tt = (q[0] * r[1] - q[1] * r[0]) / den
    if 1e-12 < ts < 1.0 - 1e-12 and 1e-12 < tt < 1.0 - 1e-12:
        return ts, tt
    return None


def find_crossings(pts2d, heights):
    """All crossings of the closed polygon with itself.
    Returns list of (theta_over, theta_under) in curve-parameter units."""
    N = len(pts2d)
    crossings = []
    for i in range(N):
        p1, p2 = pts2d[i], pts2d[(i + 1) % N]
        for j in range(i + 1, N):
            # skip adjacent segments (incl. wrap-around)
            if j == i or j == i + 1 or (i == 0 and j == N - 1):
                continue
            hit = seg_intersect(p1, p2, pts2d[j], pts2d[(j + 1) % N])
            if hit is None:
                continue
            s, tt = hit
            hi = heights[i] + s * (heights[(i + 1) % N] - heights[i])
            hj = heights[j] + tt * (heights[(j + 1) % N] - heights[j])
            t_i = (i + s) / N * TWO_PI
            t_j = (j + tt) / N * TWO_PI
            if abs(hi - hj) < 1e-9:
                continue  # degenerate (projection artifact)
            if hi > hj:
                crossings.append((t_i, t_j))   # i passes over j
            else:
                crossings.append((t_j, t_i))   # j passes over i
    return crossings


# ── 3. Fox 3-coloring ────────────────────────────────────────────

def tricolor_count(crossings):
    """Number of valid Fox 3-colorings = 3^(nullity of coloring matrix).
    Unknot: 3. Trefoil: 9."""
    if not crossings:
        return 3  # no crossings -> unknot

    # Arcs: curve pieces between consecutive UNDER-crossings
    unders = sorted(set(t_u for _, t_u in crossings))
    n_arcs = len(unders)

    def arc_of(theta):
        # arc index: interval [unders[k], unders[k+1]) containing theta
        for k in range(n_arcs):
            lo = unders[k]
            hi = unders[(k + 1) % n_arcs]
            if lo <= theta < hi:
                return k
            if lo > hi and (theta >= lo or theta < hi):  # wrap
                return k
        return n_arcs - 1

    # Coloring matrix over GF(3): at each crossing, 2*over - u1 - u2 = 0
    M = np.zeros((len(crossings), n_arcs), dtype=int)
    for r, (t_o, t_u) in enumerate(crossings):
        # the under-pass at t_u separates two arcs
        idx = unders.index(t_u)
        u1, u2 = idx, (idx - 1) % n_arcs
        M[r, arc_of(t_o)] = 2 % 3
        M[r, u1] = (M[r, u1] - 1) % 3
        M[r, u2] = (M[r, u2] - 1) % 3

    # GF(3) Gaussian elimination -> nullity
    A = M.copy() % 3
    rows, cols = A.shape
    rank = 0
    for c in range(cols):
        piv = None
        for r in range(rank, rows):
            if A[r, c] != 0:
                piv = r
                break
        if piv is None:
            continue
        A[[rank, piv]] = A[[piv, rank]]
        inv = 1 if A[rank, c] == 1 else 2  # inverse mod 3
        A[rank] = (A[rank] * inv) % 3
        for r in range(rows):
            if r != rank and A[r, c] != 0:
                A[r] = (A[r] - A[r, c] * A[rank]) % 3
        rank += 1
    nullity = cols - rank
    return 3 ** nullity


def main():
    print("=" * 64)
    print("KNOT CHECK: x=sin t - .5 sin 3t, y=-cos t + .5 cos 3t,")
    print("            z=cos t cos 3t")
    print("=" * 64)

    # 1. Embeddedness
    dmin, pair = min_nonlocal_distance()
    print(f"\n1. Embeddedness:")
    print(f"   min non-adjacent distance = {dmin:.6f}")
    print(f"   nearest pair at t = {pair[0]:.4f}, {pair[1]:.4f}")
    embedded = dmin > 1e-3
    print(f"   -> {'EMBEDDED (a genuine closed loop)' if embedded else 'SELF-INTERSECTING (not a knot)'}")

    if not embedded:
        return

    # 2. Diagrams from several projection directions
    N = 800
    t = np.linspace(0.0, TWO_PI, N, endpoint=False)
    pts = curve(t)
    directions = {
        'z-axis': np.array([0.0, 0.0, 1.0]),
        'x-axis': np.array([1.0, 0.0, 0.0]),
        'y-axis': np.array([0.0, 1.0, 0.0]),
        '(1,1,1)': np.array([1.0, 1.0, 1.0]),
        '(1,2,3)': np.array([1.0, 2.0, 3.0]),
    }
    print(f"\n2. Projections (N={N} samples):")
    best = None
    for name, d in directions.items():
        pts2d, h = project(pts, d)
        cr = find_crossings(pts2d, h)
        tri = tricolor_count(cr)
        print(f"   {name:8s}: {len(cr)} crossings, 3-colorings = {tri}")
        if best is None or len(cr) < best[1]:
            best = (name, len(cr), tri, cr)

    name, ncross, tri, cr = best
    print(f"\n3. Verdict (best projection: {name}, {ncross} crossings):")
    if ncross == 0:
        print("   No crossings in any diagram -> UNKNOT")
    elif tri == 9 and ncross <= 4:
        print("   9 three-colorings (nontrivially tricolorable) with")
        print(f"   a {ncross}-crossing diagram -> TREFOIL")
        print("   (only the trefoil has crossing number 3; unknot and")
        print("   figure-eight are not tricolorable)")
    elif tri == 9:
        print(f"   Tricolorable (9 colorings) but diagram has {ncross} crossings;")
        print("   consistent with trefoil drawn non-minimally, or another")
        print("   tricolorable knot (e.g. 6_1, 7_4) — needs Jones polynomial")
    else:
        print(f"   3-colorings = {tri} -> NOT the trefoil")
        print("   (trefoil is nontrivially tricolorable; this rules it out)")


if __name__ == '__main__':
    main()
