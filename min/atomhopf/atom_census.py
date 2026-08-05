#!/usr/bin/env python3
"""atom_census.py — how many of the 118 ground-state configurations does
the hopfion/Fock map reproduce?

Three orderings, Z = 1..118:
  (a) hydrogenic (pure geometry): fill by n, then l_sub increasing
  (b) Madelung (n+l, then n): the interaction-patched order
  (c) measured ground states: Madelung sequence + curated anomaly
      overrides (baked, citations in comments)

The curated anomaly list (the error-prone part) — the standard
NIST-based tabulation (same list as the IUPAC/Wikipedia ground-state
configuration table, which is built from NIST ASD level assignments):

  d-block (one 4s/5s/6s electron promoted into the d shell):
    Cr 3d5 4s1   Cu 3d10 4s1   Nb 4d4 5s1   Mo 4d5 5s1
    Ru 4d7 5s1   Rh 4d8 5s1    Pd 4d10 5s0  Ag 4d10 5s1
    Pt 5d9 6s1   Au 5d10 6s1
  f-block (deferred f occupancy at the series starts; half-filled-shell
    Gd/Cm):
    La 4f0 5d1   Ce 4f1 5d1    Gd 4f7 5d1
    Ac 5f0 6d1   Th 5f0 6d2    Pa 5f2 6d1   U 5f3 6d1
    Np 5f4 6d1   Cm 5f7 6d1
  plus:
    Lr 5f14 7s2 7p1 (Madelung predicts 6d1; the 7p1 assignment is the
    relativistic-calculation consensus, supported by the 2015+ ionization
    measurements — labeled accordingly)

Z >= 103 caveat: no measured ground configurations exist for the
superheavies; reference configs there are relativistic Dirac-Fock
predictions that mostly FOLLOW Madelung, so a (b)-vs-(c) match for
Z=103..118 is partly circular. The census reports Z=1..102 (measured)
and Z=103..118 (predicted) separately.

Determinism: no RNG, no web access; run twice, byte-identical.
"""
from math import sqrt

SYMBOLS = (
    "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca "
    "Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr "
    "Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe "
    "Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu "
    "Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn "
    "Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr "
    "Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og"
).split()
assert len(SYMBOLS) == 118

CAP = {"s": 2, "p": 6, "d": 10, "f": 14, "g": 18}

ORDER_MADELUNG = []
for s in range(1, 12):
    for n in range(1, s + 1):
        l = s - n
        if 0 <= l < n and l <= 4:   # subshells exist only for l < n
            ORDER_MADELUNG.append((n, l))
# dedupe while keeping order (the (n+l, then n) walk hits each once)
_seen = set()
ORDER_MADELUNG = [x for x in ORDER_MADELUNG
                  if not (x in _seen or _seen.add(x))]

ORDER_HYDRO = []
for n in range(1, 10):
    for l in range(n):
        ORDER_HYDRO.append((n, l))

LSYM = "spdfg"


def fill(order, Z):
    cfg = {}
    left = Z
    for n, l in order:
        if left <= 0:
            break
        take = min(left, CAP[LSYM[l]])
        cfg[f"{n}{LSYM[l]}"] = take
        left -= take
    assert left == 0
    return cfg


# Curated anomaly overrides: final occupancy of the affected subshells
# (all other subshells follow the Madelung sequence). Electron-count
# conservation asserted per element below.
ANOM = {
    "Cr": {"3d": 5, "4s": 1},
    "Cu": {"3d": 10, "4s": 1},
    "Nb": {"4d": 4, "5s": 1},
    "Mo": {"4d": 5, "5s": 1},
    "Ru": {"4d": 7, "5s": 1},
    "Rh": {"4d": 8, "5s": 1},
    "Pd": {"4d": 10, "5s": 0},
    "Ag": {"4d": 10, "5s": 1},
    "Pt": {"5d": 9, "6s": 1},
    "Au": {"5d": 10, "6s": 1},
    "La": {"4f": 0, "5d": 1, "6s": 2},
    "Ce": {"4f": 1, "5d": 1, "6s": 2},
    "Gd": {"4f": 7, "5d": 1, "6s": 2},
    "Ac": {"5f": 0, "6d": 1, "7s": 2},
    "Th": {"5f": 0, "6d": 2, "7s": 2},
    "Pa": {"5f": 2, "6d": 1, "7s": 2},
    "U":  {"5f": 3, "6d": 1, "7s": 2},
    "Np": {"5f": 4, "6d": 1, "7s": 2},
    "Cm": {"5f": 7, "6d": 1, "7s": 2},
    "Lr": {"6d": 0, "7p": 1},
}


def actual(Z):
    sym = SYMBOLS[Z - 1]
    cfg = fill(ORDER_MADELUNG, Z)
    if sym in ANOM:
        for sub, cnt in ANOM[sym].items():
            if cnt == 0:
                cfg.pop(sub, None)
            else:
                cfg[sub] = cnt
        assert sum(cfg.values()) == Z, f"electron count broken for {sym}"
    return cfg


def cfg_str(cfg):
    return " ".join(f"{k}{v}" for k, v in cfg.items())


def main():
    hyd = {Z: fill(ORDER_HYDRO, Z) for Z in range(1, 119)}
    mad = {Z: fill(ORDER_MADELUNG, Z) for Z in range(1, 119)}
    act = {Z: actual(Z) for Z in range(1, 119)}

    # sanity: the anomaly overrides must actually DEVIATE from Madelung
    for sym, ov in ANOM.items():
        Z = SYMBOLS.index(sym) + 1
        assert mad[Z] != act[Z], f"{sym} override is not an anomaly"
    # ... and every non-override element must match Madelung by
    # construction (the curated claim being tested is the override list)
    n_anom = sum(1 for Z in range(1, 119) if mad[Z] != act[Z])

    hyd_match = [Z for Z in range(1, 119) if hyd[Z] == act[Z]]
    mad_match = [Z for Z in range(1, 119) if mad[Z] == act[Z]]
    hyd_mis = [Z for Z in range(1, 119) if hyd[Z] != act[Z]]
    mad_mis = [Z for Z in range(1, 119) if mad[Z] != act[Z]]

    print("=" * 66)
    print("ATOM CENSUS — 118 ground-state configurations, three orderings")
    print("=" * 66)
    print(f"hydrogenic (pure geometry) matches: {len(hyd_match)}/118")
    print(f"Madelung (interaction patch) matches: {len(mad_match)}/118")
    print(f"anomalies (Madelung resisters): {n_anom}")
    print()
    mm = [Z for Z in range(1, 103) if mad[Z] == act[Z]]
    print(f"measured range Z=1..102: Madelung {len(mm)}/102; "
          f"Z=103..118 are Dirac-Fock predictions following Madelung "
          f"(partly circular: {len(mad_match) - len(mm)}/16 there)")
    print()
    print("anomaly list (the Madelung resisters):")
    for Z in mad_mis:
        sym = SYMBOLS[Z - 1]
        diff = {k: (mad[Z].get(k, 0), act[Z].get(k, 0))
                for k in sorted(set(mad[Z]) | set(act[Z]))
                if mad[Z].get(k, 0) != act[Z].get(k, 0)}
        txt = ", ".join(f"{k}: {a}->{b}" for k, (a, b) in diff.items())
        print(f"  Z={Z:>3} {sym:>2}: {txt}")
    print()
    print("hydrogenic matches (pure geometry, no interaction patch):")
    print("  " + " ".join(f"{SYMBOLS[Z-1]}({Z})" for Z in hyd_match))
    print()
    print("hydrogenic mismatches (first 12 shown with configs):")
    for Z in hyd_mis[:12]:
        print(f"  Z={Z:>3} {SYMBOLS[Z-1]:>2}: geom {cfg_str(hyd[Z])}  vs "
              f"actual {cfg_str(act[Z])}")
    print(f"  ... total {len(hyd_mis)} mismatches")
    print()

    # one-electron-ion ceiling: (Z alpha)^2 correction to Ly-alpha > 1%
    alpha = 1.0 / 137.035999084
    zc = 0.1 / alpha
    print(f"one-electron-ion ceiling: (Z*alpha)^2 > 1% at Z > "
          f"{zc:.1f} -> exact map holds nonrelativistically through")
    print(f"  Z={int(zc)} ({SYMBOLS[int(zc)-1]}); at Z={int(zc)+1} "
          f"({SYMBOLS[int(zc)]}) the Dirac/fine-structure correction to "
          f"Ly-a passes 1%.")
    print(f"  (using (Z/137.036)^2 = 0.01; the detailed Dirac Ly-a "
          f"prefactor shifts this by O(1) in Z)")


if __name__ == "__main__":
    main()
