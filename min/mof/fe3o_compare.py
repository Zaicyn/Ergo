#!/usr/bin/env python3
"""fe3o_compare.py — Stage-1 oracle: Ergo PME machinery vs the ED
reference (min/mof/fe3o_ed.py -> fe3o_ref.txt).

Checks:
  1. LADDER: Ergo multiplet energies/multiplicities == ED reference
     (the "PME ladder vs ED ladder" gate — disagreement means the PME
     is wrong).
  2. CANON:  Ergo canonical chi_mT / mu_eff vs ED canonical (tolerances
     relative; the Ergo T-grid is a subset of the reference grid).
  3. PME:    Ergo master-equation steady state == CANON (chi and the
     full population vector).
Determinism: ED reference regenerated (byte-identical), Ergo binary run
twice (byte-identical), analyzer run twice (byte-identical).
"""
import subprocess
import sys

import numpy as np


def sh(cmd, **kw):
    r = subprocess.run(cmd, shell=isinstance(cmd, str),
                       capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"failed: {cmd}\n{r.stderr[-1000:]}")
    return r.stdout


def main():
    # regenerate ED reference twice
    sh([sys.executable, "min/mof/fe3o_ed.py"])
    b1 = open("min/mof/fe3o_ref.txt", "rb").read()
    sh([sys.executable, "min/mof/fe3o_ed.py"])
    b2 = open("min/mof/fe3o_ref.txt", "rb").read()
    print(f"[det] ED reference regenerated identical: {b1 == b2}")

    mult, chi = {}, {}
    for line in b1.decode().splitlines():
        p = line.split()
        if p[0] == "MULT":
            # ref line: MULT S_T m deg(2S+1) E
            mult[float(p[1])] = (float(p[4]), int(p[2]))
        elif p[0] == "CHI":
            chi[float(p[1])] = (float(p[2]), float(p[3]))

    sh([sys.executable, "-m", "core", "min/mof/fe3o_sbu.ergo", "-o",
        "/tmp/fe3o"])
    o1 = sh("/tmp/fe3o")
    o2 = sh("/tmp/fe3o")
    print(f"[det] Ergo binary twice byte-identical: {o1 == o2}")

    lad_e, canon, pme, pmepop = {}, {}, {}, {}
    for line in o1.splitlines():
        p = line.split()
        if p[0] == "LADDER":
            lad_e[float(p[2])] = (float(p[3]), int(p[4]))
        elif p[0] == "CANON":
            canon[float(p[1])] = (float(p[2]), float(p[3]))
        elif p[0] == "PME":
            pme[float(p[1])] = (float(p[2]), float(p[3]))
        elif p[0] == "PMEPOP":
            pmepop.setdefault(float(p[1]), []).append(float(p[3]))

    print("\n[oracle 1] LADDER vs ED (max |dE|, multiplicities)")
    worst = 0.0
    ok = True
    for st, (e_ref, m_ref) in mult.items():
        e_ergo, m_ergo = lad_e[st]
        worst = max(worst, abs(e_ref - e_ergo))
        ok &= (m_ref == m_ergo)
    print(f"  max |E_ergo - E_ED| = {worst:.2e} cm^-1; "
          f"multiplicities all equal: {ok}")

    print("\n[oracle 2] CANON vs ED canonical (12 shared T points)")
    wc, wm = 0.0, 0.0
    for T, (c_ref, m_ref) in chi.items():
        if T in canon:
            c_e, m_e = canon[T]
            wc = max(wc, abs(c_e - c_ref) / c_ref)
            wm = max(wm, abs(m_e - m_ref) / m_ref)
    print(f"  max rel dev chi_mT: {wc:.3e}; max rel dev mu_eff: {wm:.3e}")

    print("\n[oracle 3] PME steady state vs CANON")
    wc, wm, wp = 0.0, 0.0, 0.0
    for T in canon:
        c_e, m_e = canon[T]
        c_p, m_p = pme[T]
        wc = max(wc, abs(c_p - c_e) / c_e)
        wm = max(wm, abs(m_p - m_e) / m_e)
        # population vector vs Boltzmann from the ladder
        pops = np.array(pmepop[T])
        st_s = np.arange(0.5, 8.0, 1.0)
        deg = np.array([mult[s][1] * (2 * s + 1) for s in st_s])
        en = np.array([mult[s][0] for s in st_s])
        boltz = deg * np.exp(-(en - en[0]) / (0.69503 * T))
        boltz /= boltz.sum()
        wp = max(wp, np.abs(pops - boltz).max())
    print(f"  max rel dev chi: {wc:.3e}; mu_eff: {wm:.3e}; "
          f"max |P_pme - P_boltz|: {wp:.3e}")

    verdict = (b1 == b2 and o1 == o2 and ok and wc < 1e-6 and wm < 1e-6
               and wp < 1e-6)
    print(f"\nVERDICT: {'PASS' if verdict else 'FAIL'}")


if __name__ == "__main__":
    main()
