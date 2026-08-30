#!/usr/bin/env python3
"""rail_analysis.py — gate-vs-formation timing + inter-domain rotation
for the ul18_stag5_rail runs (min/ribosome/RAIL_MAP.md's instrument).

Reads a rail-run stdout file:
  RAILGATES,<n>
  RC,<frame>,<I>,<J>,<D>      (gated-contact distance, gate windows)
  RB,<frame>,<I>,<x>,<y>,<z>  (per-bead coords, gate windows)
  FF,<I>,<J>,<gateT>,<firstF> (first-formation table at end)

Analysis:
  1. per-seam formation timing: first-formed frame vs gate frame per
     contact (lag distribution), and fraction-formed curves (t50).
  2. inter-domain rotation: per dump in each gate window, Kabsch/SVD
     (numpy, the certified recipe — RIBOSOME_FINDINGS ERRATA retired the
     hand-rolled one) aligns each domain's beads to that domain's
     reference frame at (gate - 3000); relative rotation across the
     seam = R_up @ R_down^T; angle in degrees.  Control window
     (100000-108000, post-gates) gives the noise floor.
  3. ratchet-step test: angle jump across the gate vs baseline drift.

Usage: python3 min/ribosome/rail_analysis.py /tmp/rail_run1.txt
"""
import sys
import os
from collections import defaultdict

import numpy as np

# domain map (CODON_FINDINGS phase-0 table): D1 1-63 ... D5 253-293
DOM = [(1, 63), (64, 126), (127, 189), (190, 252), (253, 293)]
GATES = [24000, 48000, 72000]
# seam definitions: (label, upstream domains, downstream domains, gate)
SEAMS = [
    ("D1|D2 @24k", [0], [1], 24000),
    ("D1|D3 @48k", [0], [2], 48000),
    ("D2|D3 @48k", [1], [2], 48000),
    ("D2|D4 @72k", [1], [3], 72000),
    ("D3|D4 @72k", [2], [3], 72000),
]
WINDOWS = {24000: (20000, 28000), 48000: (44000, 52000),
           72000: (68000, 76000)}
CONTROL_WINDOW = (100000, 108000)
NATIVE_CUTOFF = 2.6


def parse(path):
    rc = []          # (frame, i, j, D)
    rb = defaultdict(dict)   # frame -> {i: (x,y,z)}
    ff = []          # (i, j, gateT, firstF)
    for ln in open(path):
        p = ln.strip().split(",")
        if p[0] == "RC":
            rc.append((int(p[1]), int(p[2]), int(p[3]), float(p[4])))
        elif p[0] == "RB":
            rb[int(p[1])][int(p[2])] = (float(p[3]), float(p[4]),
                                        float(p[5]))
        elif p[0] == "FF":
            ff.append((int(p[1]), int(p[2]), int(p[3]), int(p[4])))
    return rc, rb, ff


def kabsch_rot(cur, ref):
    """proper rotation aligning cur onto ref (SVD; certified recipe —
    RIBOSOME_FINDINGS ERRATA retired the hand-rolled one).  Returns
    (R, residual_rmsd) — the residual is the internal-deformation
    confound check."""
    c = cur - cur.mean(axis=0)
    r = ref - ref.mean(axis=0)
    H = c.T @ r
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U))
    D = np.diag([1.0, 1.0, d])
    R = Vt.T @ D @ U.T
    resid = float(np.sqrt(((c @ R - r) ** 2).sum() / len(c)))
    return R, resid


def rot_angle_deg(R):
    c = (np.trace(R) - 1.0) / 2.0
    return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))


def dom_beads(rbframe, dlist):
    pts = []
    for d in dlist:
        lo, hi = DOM[d]
        for i in range(lo, hi + 1):
            pts.append(rbframe[i])
    return np.array(pts)


def main():
    rc, rb, ff = parse(sys.argv[1])
    frames = sorted(rb)
    print(f"parsed: {len(rc)} RC rows, {len(frames)} RB frames, "
          f"{len(ff)} FF rows")

    # ---- 1. formation timing ----
    print("\n== formation timing (first crossing of D < 2.6, vs gate) ==")
    by_gate = defaultdict(list)
    for i, j, gt, fv in ff:
        by_gate[gt].append(fv - gt)     # lag: + = after gate
    for gt in sorted(by_gate):
        lags = by_gate[gt]
        formed = [x for x in lags if x != -1 - gt]  # -1 = never formed
        never = len(lags) - len(formed)
        import numpy as np
        a = np.array(formed)
        print(f"gate {gt}: n={len(lags)} never-formed={never}  "
              f"lag(formed-first): min={a.min()} p25={np.percentile(a,25):.0f} "
              f"median={np.median(a):.0f} p75={np.percentile(a,75):.0f} "
              f"max={a.max()}")
    # fraction-formed curves from RC
    print("\n== fraction formed over time (per gate, RC series) ==")
    series = defaultdict(lambda: defaultdict(list))
    tot = defaultdict(int)
    ffmap = {(i, j): gt for i, j, gt, _ in ff}
    for f, i, j, d in rc:
        series[gate_of(i, j, ffmap)][f].append(d < NATIVE_CUTOFF)
    for gt in sorted(series):
        fs = sorted(series[gt].items())
        t50 = next((f for f, v in fs
                    if sum(v) / max(len(v), 1) >= 0.5), None)
        pts = [(f, sum(v) / len(v)) for f, v in fs if len(v)]
        print(f"gate {gt}: t50={t50}  curve: " +
              " ".join(f"{f}:{v:.2f}" for f, v in pts[::40]))

    # ---- 2. rotation ----
    print("\n== inter-domain rotation (deg, Kabsch/SVD frames) ==")
    os.makedirs("min/ribosome/rail_series", exist_ok=True)
    tag = os.path.basename(sys.argv[1]).replace(".txt", "")
    for label, ups, downs, gt in SEAMS:
        lo, hi = WINDOWS[gt]
        win = [f for f in frames if lo <= f <= hi]
        if not win:
            continue
        tref = max(f for f in win if f <= gt - 3000)
        refU = dom_beads(rb[tref], ups)
        refD = dom_beads(rb[tref], downs)
        rows = []
        resU, resD = [], []
        for f in win:
            RU, ru = kabsch_rot(dom_beads(rb[f], ups), refU)
            RD, rd = kabsch_rot(dom_beads(rb[f], downs), refD)
            rows.append((f, rot_angle_deg(RU @ RD.T)))
            resU.append(ru)
            resD.append(rd)
        arr = np.array([a for _, a in rows])
        pre = [a for f, a in rows if f < gt]
        post = [a for f, a in rows if f > gt]
        print(f"{label}: ref@{tref}  pre-gate mean {np.mean(pre):.3f} "
              f"post-gate mean {np.mean(post):.3f}  max {arr.max():.3f}  "
              f"end {arr[-1]:.3f}  step@(gate±500) "
              f"{step_at(rows, gt):.3f}  kabsch-resid U/D "
              f"{np.mean(resU):.3f}/{np.mean(resD):.3f}")
        # save the series for the findings doc
        with open(f"min/ribosome/rail_series/{tag}_{label.replace(' ', '_').replace('|', '-')}.csv", "w") as fh:
            fh.write("frame,angle_deg\n")
            for f, a in rows:
                fh.write(f"{f},{a:.4f}\n")
    # control window noise floor (no gate): use seam D1|D2
    ctrl = [f for f in frames
            if CONTROL_WINDOW[0] <= f <= CONTROL_WINDOW[1]]
    if ctrl:
        tref = ctrl[0]
        refU = dom_beads(rb[tref], [0])
        refD = dom_beads(rb[tref], [1])
        angs = []
        for f in ctrl:
            RU, _ = kabsch_rot(dom_beads(rb[f], [0]), refU)
            RD, _ = kabsch_rot(dom_beads(rb[f], [1]), refD)
            angs.append(rot_angle_deg(RU @ RD.T))
        print(f"control (100-108k, no gate): D1|D2 drift mean "
              f"{np.mean(angs):.3f} max {np.max(angs):.3f} deg "
              f"(per-3000-frame pre-gate drifts above are the other floor)")


def gate_of(i, j, ffmap):
    return ffmap.get((i, j), -1)


def step_at(rows, gt):
    pre = [a for f, a in rows if gt - 500 <= f < gt]
    post = [a for f, a in rows if gt < f <= gt + 500]
    if not pre or not post:
        return float("nan")
    return float(np.mean(post) - np.mean(pre))


if __name__ == "__main__":
    main()
