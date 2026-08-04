#!/usr/bin/env python3
"""v4_check.py — validate the v4 allocator ports against the audit
metrics plus the two fix-specific oracles.

  Fix 1 (8-bin scatter): SCATLT regenerates from
    sq2_viviani_scatter_full(id, 52) at HOPFQ=1.97 (float32), uses all
    8 bins, and the zone states ACTIVE/OVERDRIVE/DIVIDE are reachable
    (fill+replicate cycles in both ports). Separation tradeoff reported
    against the v2/v3 LUT (audit L3a metric).
  Fix 2 (3-axis residual): SQ4RES gives exactly 0 unperturbed, responds
    ~3e-3 to eps=1e-3 along each axis, sqrt(3)*e-3 along the diagonal
    (the floor case), and a 1000-random-direction sweep confirms the
    analytic floor max_a 3*|d.a| >= sqrt(3)*|d|.

Cross-port: F77 v4 vs Ergo v4 must agree on the scatter sequence, the
state hash, the fill-cycle occupancies/zones, and the full TINVAR dump
(bit-exact integer invariants). Residuals agree to 1e-9 (F77 gate is
REAL*4, Ergo REAL is f64 — last-bit differences expected, measured).

Determinism: every driver run twice, byte-identical. Regression: the
v2/v3 audit (tuning_check.py) must still pass unchanged.

Run from repo root:  python allocator/v4_check.py
"""
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tuning_check import (gen_scatlt, gen_floww, torus_dd, separations,
                          action, simulate_state, state_hash, sh,
                          run_twice, parse_f77_table, parse_ergo_table)

OLD_LUT = [6, 4, 6, 2, 7, 4, 3, 0, 2, 0, 3, 4, 7, 2, 6, 4] * 2
NEW_LUT = gen_scatlt(hopfq=1.97, total=52)
SQRT3 = np.sqrt(3.0)

F77V4_DRIVER = r"""
      PROGRAM SQ4DRV
      IMPLICIT NONE
      INTEGER I, ERR, NCOPY
      INTEGER SQ4SCT, SQ4ZON
      REAL*8 SQ4RES
      REAL    GATES(3,12,32,8,2)
      INTEGER TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ4TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
      INTEGER HASH, HI, HJ, HK
      REAL VTX(3,12)
      REAL*8 R
      CALL SQ4TIN
      ERR = 0
      DO 10 I = 1, 400
        CALL SQ4FAL(I, ERR)
   10 CONTINUE
      WRITE(*,'(A,I8)') 'TTOTAL ', TTOTAL
      WRITE(*,'(A,I4)') 'ZONE ', SQ4ZON(TTOTAL)
      HASH = 166136261
      DO 50 HK = 1, 2
        DO 45 HJ = 1, 8
          HASH = IEOR(HASH, TWHEAD(HJ,HK))
          HASH = IEOR(ISHFT(HASH,13), ISHFT(HASH,-19))
          HASH = IEOR(HASH, TLEN(HJ,HK))
          HASH = IEOR(ISHFT(HASH,13), ISHFT(HASH,-19))
          HASH = IEOR(HASH, TALLOC(HJ,HK))
          HASH = IEOR(ISHFT(HASH,13), ISHFT(HASH,-19))
          DO 40 HI = 1, 32
            HASH = IEOR(HASH, TOCC(HI,HJ,HK))
            HASH = IEOR(ISHFT(HASH,13), ISHFT(HASH,-19))
            HASH = IEOR(HASH, TFROZ(HI,HJ,HK))
            HASH = IEOR(ISHFT(HASH,13), ISHFT(HASH,-19))
   40     CONTINUE
   45   CONTINUE
   50 CONTINUE
      HASH = IEOR(HASH, TTOTAL)
      HASH = IEOR(ISHFT(HASH,13), ISHFT(HASH,-19))
      WRITE(*,'(A,I12)') 'HASH ', HASH
      DO 60 I = 1, 32
        WRITE(*,'(A,I4,A,I4)') 'SCT ', I, ' ', SQ4SCT(I)
   60 CONTINUE
      CALL SQ4INI(VTX, 1.0)
      R = SQ4RES(VTX, 1.0)
      WRITE(*,'(A,E24.17)') 'RES_ZERO ', R
      VTX(1,1) = VTX(1,1) + 0.001
      R = SQ4RES(VTX, 1.0)
      WRITE(*,'(A,E24.17)') 'RES_X ', R
      CALL SQ4INI(VTX, 1.0)
      VTX(2,1) = VTX(2,1) + 0.001
      R = SQ4RES(VTX, 1.0)
      WRITE(*,'(A,E24.17)') 'RES_Y ', R
      CALL SQ4INI(VTX, 1.0)
      VTX(3,1) = VTX(3,1) + 0.001
      R = SQ4RES(VTX, 1.0)
      WRITE(*,'(A,E24.17)') 'RES_Z ', R
      CALL SQ4INI(VTX, 1.0)
      VTX(1,1) = VTX(1,1) + 0.0005773502691896258
      VTX(2,1) = VTX(2,1) + 0.0005773502691896258
      VTX(3,1) = VTX(3,1) + 0.0005773502691896258
      R = SQ4RES(VTX, 1.0)
      WRITE(*,'(A,E24.17)') 'RES_DIAG ', R
      CALL SQ4TIN
      DO 70 I = 1, 220
        CALL SQ4FAL(I, ERR)
   70 CONTINUE
      CALL SQ4REP(NCOPY)
      WRITE(*,'(A,I8,A,I4,A,I8)') 'CYC1 ', TTOTAL, ' ',
     &  SQ4ZON(TTOTAL), ' ', NCOPY
      CALL SQ4TIN
      DO 80 I = 1, 400
        CALL SQ4FAL(I, ERR)
   80 CONTINUE
      CALL SQ4REP(NCOPY)
      WRITE(*,'(A,I8,A,I4,A,I8)') 'CYC2 ', TTOTAL, ' ',
     &  SQ4ZON(TTOTAL), ' ', NCOPY
      CALL SQ4TIN
      DO 90 I = 1, 470
        CALL SQ4FAL(I, ERR)
   90 CONTINUE
      CALL SQ4REP(NCOPY)
      WRITE(*,'(A,I8,A,I4,A,I8)') 'CYC3 ', TTOTAL, ' ',
     &  SQ4ZON(TTOTAL), ' ', NCOPY
      DO 120 HK = 1, 2
        DO 110 HJ = 1, 8
          DO 100 HI = 1, 32
            WRITE(*,'(A,I4,A,I4,A,I4,A,I12)') 'TINV ', HI, ' ',
     &        HJ, ' ', HK, ' ', TINVAR(HI,HJ,HK)
  100     CONTINUE
  110   CONTINUE
  120 CONTINUE
      END
"""


def run_f77v4():
    with open("/tmp/sq4drv.f", "w") as f:
        f.write(F77V4_DRIVER)
    sh("gfortran -std=legacy -O2 allocator/sq4core.f /tmp/sq4drv.f "
       "-o /tmp/sq4drv")
    return run_twice("/tmp/sq4drv")


def run_ergov4():
    sh([sys.executable, "-m", "core", "tests/sq4core.ergo", "-o",
        "/tmp/sq4audit"])
    return run_twice("/tmp/sq4audit")


# ---- Python replica of SQ4RES (f64, same op order) ----
SEED = []
_s = 0.7071067811865475
for t in [(_s, _s, 0), (_s, -_s, 0), (-_s, _s, 0), (-_s, -_s, 0),
          (_s, 0, _s), (_s, 0, -_s), (-_s, 0, _s), (-_s, 0, -_s),
          (0, _s, _s), (0, _s, -_s), (0, -_s, _s), (0, -_s, -_s)]:
    SEED.append(t)


def res3_axes(vtx, scale=1.0):
    """Per-axis residuals (x, y, z frames), same op order as the ports."""
    c120, s120 = -0.5, 0.8660254037844386
    out = []
    for ax in range(3):
        sx = sy = sz = 0.0
        for (x, y, z) in vtx:
            if ax == 0:
                x1, y1, z1 = x, c120 * y - s120 * z, s120 * y + c120 * z
                x2, y2, z2 = x, c120 * y + s120 * z, -s120 * y + c120 * z
            elif ax == 1:
                x1, y1, z1 = c120 * x + s120 * z, y, -s120 * x + c120 * z
                x2, y2, z2 = c120 * x - s120 * z, y, s120 * x + c120 * z
            else:
                x1, y1, z1 = c120 * x - s120 * y, s120 * x + c120 * y, z
                x2, y2, z2 = c120 * x + s120 * y, -s120 * x + c120 * y, z
            sx += x + x1 + x2
            sy += y + y1 + y2
            sz += z + z1 + z2
        out.append(np.sqrt(sx * sx + sy * sy + sz * sz) / scale)
    return out


def main():
    lvl = print
    lvl("[v4] determinism / builds")
    f77, f77_det = run_f77v4()
    ergo, ergo_det = run_ergov4()
    lvl(f"  F77 v4 twice byte-identical: {f77_det}; "
        f"Ergo v4: {ergo_det}")

    # ---- Fix 1 oracle: LUT regeneration + coverage ----
    lvl("\n[fix1] SCATLT regeneration (scatter_full(id,52), HOPFQ=1.97)")
    with open("allocator/sq4core.f") as f:
        f77_text = f.read()
    with open("tests/sq4core.ergo") as f:
        ergo_text = f.read()
    bf = parse_f77_table(f77_text, "SCATLT", 32)
    be = parse_ergo_table(ergo_text, "SCATLT", 32)
    lvl(f"  regen==baked-F77: {list(map(int, bf)) == NEW_LUT}; "
        f"regen==baked-ergo: {list(map(int, be)) == NEW_LUT}")
    hist = np.bincount(NEW_LUT, minlength=8)
    lvl(f"  histogram per 32 IDs: {hist.tolist()} "
        f"(all 8 bins live: {hist.min() > 0})")
    lvl(f"  new LUT: {NEW_LUT}")

    # ---- metrics continuity (audit L3a/L2) ----
    DD = torus_dd(gen_floww())
    for name, s in (("old(total=32)", OLD_LUT), ("new(total=52)", NEW_LUT)):
        d = separations(s, DD)
        e, dsum = action(s, DD)
        lvl(f"  {name}: sep min={d.min():.4f} p5={np.percentile(d,5):.4f}"
            f" mean={d.mean():.4f} | L2 E={e:.4f} DSUM={dsum:.2f}")

    # ---- Fix 1 oracle: state reachability, cross-port ----
    lvl("\n[fix1] threshold-state reachability (fill + replicate)")
    def cycs(out):
        return [(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                for m in re.finditer(r"CYC(\d)\s+(-?\d+)\s+(\d+)\s+(\d+)",
                                     out)]
    # careful: CYCn label index is group1 of CYC line; reparse per line
    def cyc_rows(out):
        rows = {}
        for line in out.splitlines():
            m = re.match(r"CYC(\d)\s+(-?\d+)\s+(\d+)\s+(\d+)", line)
            if m:
                rows[int(m.group(1))] = (int(m.group(2)), int(m.group(3)),
                                         int(m.group(4)))
        return rows
    f_cyc, e_cyc = cyc_rows(f77), cyc_rows(ergo)
    lvl(f"  F77:  {f_cyc}")
    lvl(f"  Ergo: {e_cyc}")
    lvl(f"  cross-port cycles agree: {f_cyc == e_cyc}")
    zones = sorted({v[1] for v in f_cyc.values()})
    lvl(f"  zones reached: {zones} "
        f"(ACTIVE=2, OVERDRIVE=3, DIVIDE=4 all reachable: "
        f"{zones == [2, 3, 4]})")

    # ---- cross-port sequences / hash / invariants ----
    lvl("\n[cross-port] sequences, hash, invariants")
    f_sct = [int(m.group(2)) - 1
             for m in re.finditer(r"SCT\s+(\d+)\s+(\d+)", f77)]
    e_sct = [int(m.group(2)) - 1
             for m in re.finditer(r"SCT (\d+) (\d+)", ergo)]
    lvl(f"  F77 SQ4SCT == Ergo SQ4SCT == regen LUT: "
        f"{f_sct == NEW_LUT and e_sct == NEW_LUT}")
    f_hash = int(re.search(r"HASH\s+(-?\d+)", f77).group(1))
    e_hash = int(ergo.split()[3])
    py_hash = state_hash(simulate_state(NEW_LUT))
    lvl(f"  HASH: F77={f_hash} ergo={e_hash} py-model={py_hash} -> "
        f"{'AGREE' if f_hash == e_hash == py_hash else 'DISAGREE'}")
    f_tt = int(re.search(r"TTOTAL\s+(\d+)", f77).group(1))
    e_tt = int(ergo.split()[0])
    lvl(f"  TTOTAL after 400 FAL: F77={f_tt} ergo={e_tt} py="
        f"{simulate_state(NEW_LUT)[5]}")
    f_tinv = [int(m.group(4))
              for m in re.finditer(r"TINV\s+(\d+)\s+(\d+)\s+(\d+)\s+(-?\d+)",
                                   f77)]
    e_tinv = [int(m.group(4))
              for m in re.finditer(r"TINV (\d+) (\d+) (\d+) (-?\d+)", ergo)]
    lvl(f"  TINVAR dump (512 slots, post-cycle-3): equal: "
        f"{f_tinv == e_tinv}; nonzero slots: "
        f"{sum(1 for v in f_tinv if v != 0)}")

    # ---- Fix 2 oracle: residual floor ----
    lvl("\n[fix2] 3-axis corruption residual")
    def resvals(out):
        return {m.group(1): float(m.group(2))
                for m in re.finditer(r"RES_(\w+)\s+(\S+)", out)}
    fr, er = resvals(f77), resvals(ergo)
    lvl(f"  unperturbed: F77={fr['ZERO']:.3e} ergo={er['ZERO']:.3e} "
        f"(exact zero both: {fr['ZERO'] == 0.0 and er['ZERO'] == 0.0})")
    for k in ("X", "Y", "Z", "DIAG"):
        lvl(f"  RES_{k}: F77={fr[k]:.17e} ergo={er[k]:.17e} "
            f"|diff|={abs(fr[k] - er[k]):.2e}")
    lvl(f"  expected: axis 3e-3, diag sqrt(3)e-3={SQRT3 * 1e-3:.17e}")
    # python replica: unperturbed + floor sweep
    z = res3_axes(SEED)
    lvl(f"  python replica unperturbed per-axis: "
        f"{[f'{v:.3e}' for v in z]} (max {max(z):.3e})")
    rng = np.random.default_rng(20260805)
    eps = 1e-3
    floor = SQRT3 * eps
    worst = np.inf
    worst_ax = None
    for t in range(1000):
        d = rng.standard_normal(3)
        d = d / np.linalg.norm(d) * eps
        vtx = [(x + (d[0] if i == 0 else 0),
                y + (d[1] if i == 0 else 0),
                z + (d[2] if i == 0 else 0)) for i, (x, y, z) in enumerate(SEED)]
        ax = res3_axes(vtx)
        r = max(ax)
        if r < worst:
            worst = r
            worst_ax = ax
    lvl(f"  1000 random dirs, eps=1e-3 single-vertex: min response "
        f"{worst:.17e}")
    lvl(f"  analytic floor sqrt(3)*eps = {floor:.17e}; "
        f"min/floor = {worst / floor:.12f} (>=1: {worst >= floor * (1 - 1e-12)})")
    lvl(f"  per-axis at the worst draw: {[f'{v:.6e}' for v in worst_ax]}")

    # ---- regression: v2/v3 audit still passes ----
    lvl("\n[regression] v2/v3 audit (tuning_check.py)")
    r = subprocess.run([sys.executable, "allocator/tuning_check.py"],
                       capture_output=True, text=True)
    ok = (r.returncode == 0 and "AGREE" in r.stdout
          and "MISMATCH" not in r.stdout)
    lvl(f"  tuning_check.py exit={r.returncode}, hash AGREE present, "
        f"no MISMATCH -> {'PASS' if ok else 'FAIL'}")


if __name__ == "__main__":
    main()
