#!/usr/bin/env python3
"""fn_analyze.py — Stage 3 driver: Faddeev-Niemi Hopf soliton.

Builds two grid variants of min/glueball/fn_soliton.ergo via sed
(NX=128 BOX=4.0 and NX=160 BOX=5.0, same dx=0.0625, LAM=1.0 both,
tau=0.5), runs each twice (determinism, byte-identical via cmp),
parses STATE/ENERGY lines, and prints the oracle summary.

GRID/TAU DEVIATION (documented in the engine header too): the
campaign-suggested dx=0.125 grids fail oracle 1 — the virial
contraction drives the soliton core through the lattice topology
barrier and the texture unwinds (Q -> 0 at tau ~ 0.2 for dx=0.125,
~ 0.4 for dx=0.083, ~ 0.55 for dx=0.071, ~ 0.6 for dx=0.0625
BOX=4, ~ 0.65 for dx=0.0625 BOX=5; all verified with an
independent numpy replica of the engine).  The continuum virial
minimum is below the lattice topology barrier at every affordable
spacing, so production stops at tau=0.5, before the slip, with
Q ~ 0.98 preserved; the virial oracle E2=E4 is NOT met (E2/E4 ~ 2)
and is reported honestly as such.

  1. Derrick/finite-size: energy settles at a finite-size minimum
     (no collapse to boundary, no blow-up).
  2. Virial: E2/E4 at the relaxed minimum (should be ~1).
  3. Energy vs literature: (2*E2 + E4)/(32 pi^2) vs 1.232
     (hep-th/0107187: E_FS(Q=1) = 1.232 x 32 pi^2).
  4. Hopf charge Q at tau = 0 / mid / end.
  5. Grid convergence: both spacings side by side.
  6. Determinism: no RNG; two runs byte-identical.
  7. Mass calibration (report only): kappa/e = 1650 MeV / epsilon,
     epsilon = E in engine units; normalized epsilon_norm =
     (2E2+E4)/(32 pi^2); cross-check vs Amari et al. PLB 869 (2025)
     139805 (3.40 MeV via f0(1500), 6.31 MeV via f0(1710)) — their
     normalization differs, so this is model-unit physics, no forced
     agreement.

Run from repo root:  python min/glueball/fn_analyze.py
"""

import math
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO, "min", "glueball", "fn_soliton.ergo")

GRIDS = {
    "fn128": {"NX": 128, "BOX": "4.0", "NSTEPS": 1250,
              "half": 4.0, "dx": 0.0625},
    "fn160": {"NX": 160, "BOX": "5.0", "NSTEPS": 1250,
              "half": 5.0, "dx": 0.0625},
}


def build(tag, nx, box, nsteps):
    """sed-variant source into /tmp, compile to /tmp/<tag>."""
    dst = f"/tmp/{tag}.ergo"
    with open(SRC) as f:
        src = f.read()
    src = src.replace("INTEGER, PARAMETER :: NX = 128",
                      f"INTEGER, PARAMETER :: NX = {nx}", 1)
    src = src.replace("REAL, PARAMETER :: BOX = 4.0",
                      f"REAL, PARAMETER :: BOX = {box}", 1)
    src = src.replace("INTEGER, PARAMETER :: NSTEPS = 1250",
                      f"INTEGER, PARAMETER :: NSTEPS = {nsteps}", 1)
    with open(dst, "w") as f:
        f.write(src)
    subprocess.run([sys.executable, "-m", "core", dst, "-o", f"/tmp/{tag}"],
                   cwd=REPO, check=True, capture_output=True, text=True)
    return f"/tmp/{tag}"

PI2_32 = 32.0 * math.pi * math.pi
E_LIT = 1.232  # (2E2+E4)/(32 pi^2) literature value, hep-th/0107187


def run(binary, out):
    with open(out, "w") as f:
        subprocess.run([binary], stdout=f, check=True)


def parse(path):
    states = {}
    energies = []
    for line in open(path):
        m = re.match(r"STATE (\d+) (\S+) (\S+) (\S+) (\S+) (\S+)", line)
        if m:
            t = int(m.group(1))
            states[t] = tuple(float(v) for v in m.groups()[1:])
            continue
        m = re.match(r"ENERGY (\d+) (\S+) (\S+) (\S+)", line)
        if m:
            energies.append((int(m.group(1)), float(m.group(2)),
                             float(m.group(3)), float(m.group(4))))
    return states, energies


def oracle_block(tag, states, energies, half):
    ts = sorted(states)
    t0, tend = ts[0], ts[-1]
    tmid = ts[len(ts) // 2] if len(ts) > 2 else None
    e0 = states[t0]
    ee = states[tend]
    E, E2, E4, Q, rms = ee
    comb = (2.0 * E2 + E4) / PI2_32
    print(f"\n[{tag}]")
    print(f"  tau=0   : E={e0[0]:.4f} E2={e0[1]:.4f} E4={e0[2]:.4f} "
          f"Q={e0[3]:.4f} rms={e0[4]:.4f}")
    if tmid is not None:
        em = states[tmid]
        print(f"  tau=mid : E={em[0]:.4f} E2={em[1]:.4f} E4={em[2]:.4f} "
              f"Q={em[3]:.4f} rms={em[4]:.4f}")
    print(f"  tau=end : E={E:.4f} E2={E2:.4f} E4={E4:.4f} "
          f"Q={Q:.4f} rms={rms:.4f}")
    print(f"  virial E2/E4 = {E2 / E4:.4f}  (oracle: ~1 at the minimum)")
    print(f"  (2E2+E4)/(32 pi^2) = {comb:.4f}  vs literature {E_LIT} "
          f"({100.0 * (comb - E_LIT) / E_LIT:+.1f}%)")
    print(f"  E (raw engine units) = {E:.4f}")
    print(f"  Hopf Q start/mid/end = {e0[3]:.4f} / "
          f"{states[tmid][3] if tmid is not None else float('nan'):.4f}"
          f" / {Q:.4f}")
    # convergence: energy change over last 20% of steps
    if len(energies) >= 5:
        t_end, E_end = energies[-1][0], energies[-1][1]
        t_ref = None
        for t, Et, _, _ in energies:
            if t <= 0.8 * t_end:
                t_ref = (t, Et)
        if t_ref:
            dE = abs(E_end - t_ref[1]) / E_end
            print(f"  convergence: |E(last)-E(t=0.8*T)|/E = {dE:.3e} "
                  f"over last 20% of steps")
    # Derrick oracle: energy fell to a finite minimum, texture compact
    collapsed = rms > 0.8 * half
    blew = E > e0[0] * 1.001
    print(f"  Derrick: E {e0[0]:.1f} -> {E:.1f}, rms {e0[4]:.2f} -> "
          f"{rms:.2f} (box half-width {half}): "
          f"{'FAIL collapse/blow-up' if (collapsed or blew) else 'OK finite size'}")
    return {"E": E, "E2": E2, "E4": E4, "Q": Q, "rms": rms, "comb": comb}


def main():
    print("=" * 66)
    print("STAGE 3 — FADDEEV-NIEMI HOPF-CHARGE-1 SOLITON (GLUEBALL)")
    print("=" * 66)

    results = {}
    for tag, g in GRIDS.items():
        print(f"\n[build] {tag}: NX={g['NX']} BOX={g['BOX']} "
              f"NSTEPS={g['NSTEPS']}")
        binary = build(tag, g["NX"], g["BOX"], g["NSTEPS"])
        out1, out2 = f"/tmp/{tag}.run1.log", f"/tmp/{tag}.run2.log"
        print(f"[run] {tag} run 1/2 ...", flush=True)
        run(binary, out1)
        print(f"[run] {tag} run 2/2 ...", flush=True)
        run(binary, out2)
        same = subprocess.run(["cmp", "-s", out1, out2]).returncode == 0
        print(f"[determinism] {tag}: two runs "
              f"{'BYTE-IDENTICAL' if same else 'DIFFER — FAIL'}")
        states, energies = parse(out1)
        results[tag] = oracle_block(tag, states, energies, g["half"])
        results[tag]["det"] = same

    print("\n" + "=" * 66)
    print("ORACLE SUMMARY")
    print("=" * 66)
    tags = list(GRIDS)
    a, b = results[tags[0]], results[tags[1]]
    print("\n(5) grid convergence (LAM=1.0 both; "
          f"{tags[0]}: dx={GRIDS[tags[0]]['dx']}, "
          f"{tags[1]}: dx={GRIDS[tags[1]]['dx']})")
    print(f"  {'':10s}{tags[0]:>16s}{tags[1]:>16s}")
    for k, lbl in (("E", "E"), ("E2", "E2"), ("E4", "E4"),
                   ("Q", "Q"), ("rms", "rms"), ("comb", "(2E2+E4)/32pi^2")):
        print(f"  {lbl:16s}{a[k]:16.4f}{b[k]:16.4f}")
    print(f"  energy difference: {100.0 * abs(a['E'] - b['E']) / b['E']:.2f}%")

    print("\n(3) energy vs literature 1.232 (tol ~10% coarse, better fine)")
    for tag in tags:
        r = results[tag]
        ok = "OK" if abs(r["comb"] - E_LIT) / E_LIT < 0.10 else "outside 10%"
        print(f"  {tag}: {r['comb']:.4f} ({100.0 * (r['comb'] - E_LIT) / E_LIT:+.1f}%) {ok}")

    print("\n(6) determinism")
    print("  " + "; ".join(f"{t}: {'byte-identical' if results[t]['det'] else 'DIFFERS'}"
                            for t in tags))

    print("\n(7) mass calibration (report, not tuned)")
    for tag in tags:
        r = results[tag]
        ke = 1650.0 / r["E"]
        ken = 1650.0 / r["comb"]
        print(f"  {tag}: epsilon = E = {r['E']:.2f} engine units -> "
              f"kappa/e = 1650 MeV / eps = {ke:.3f} MeV")
        print(f"         epsilon_norm = (2E2+E4)/32pi^2 = {r['comb']:.4f} "
              f"-> kappa/e = {ken:.1f} MeV")
    print("  Amari et al. (PLB 869 (2025) 139805): kappa/e = 3.40 MeV")
    print("  identifying Q=1 with f0(1500), 6.31 MeV with f0(1710).")
    print("  Their static mass M_cl = (kappa/e) * epsilon_their with a")
    print("  DIFFERENT energy normalization, so only the model-unit")
    print("  statement is honest; no agreement forced.")

    print("\n(1,2,4) Derrick/virial/Hopf per-grid lines above.")


if __name__ == "__main__":
    main()
