#!/usr/bin/env python3
"""flux_loop.py — Stage 2: closed flux-tube (Isgur-Paton) glueballs.

A glueball as a closed loop of color flux with string tension
sigma.  sigma = 0.185 GeV^2 (sqrt(sigma) = 430 MeV, the standard
Sommer-scale string tension; INPUT, swept +/-10%, never fitted).

Three documented prescriptions (we report all, no cherry-pick):

  (a) Intercept-free (Isgur-Paton's large-loop form, the standard):
        E^2 = 4 pi sigma n,   n = 1, 2, ...
      n = 1 phonon  -> 0++ and 2++ (degenerate)
      n = 2 phonons -> 0-+ , 2-+ , 1-+  (odd parity appears here)

  (b) Arvis/Casimir in squared form:
        E^2 = 4 pi sigma (n - (D-2)/24),  D = 4
      i.e. E^2 = 4 pi sigma (n - 1/12).

  (c) Casimir-corrected length form, minimized over loop length L:
        E_n(L) = sigma L + (4 pi n - pi/3)/L
        E_min = 2 sqrt(sigma (4 pi n - pi/3))
      (the -pi/(3L) term is the closed-string vacuum energy
      -(D-2)pi/(24L) for left+right movers; at these small L the
      loop self-intersects, which is exactly why (a) is the standard
      physical prescription — documented, not hidden.)

Oracles: ordering 0++ < 2++ (degenerate in a pure string) < 0-+ ;
levels vs LQCD (0++ 1.6-1.7, 2++ 2.2-2.4, 0-+ 2.3-2.6 GeV);
sigma sensitivity as a sweep, not a fit.

Determinism: pure arithmetic; run twice, byte-identical.
"""

import math

SIGMA = 0.185  # GeV^2, input (430 MeV)^2-ish standard string tension
D = 4

STATES = {
    1: "0++ / 2++ (n=1 phonon)",
    2: "0-+ / 2-+ / 1-+ (n=2 phonons)",
}


def e_intercept_free(sig, n):
    return math.sqrt(4.0 * math.pi * sig * n)


def e_arvis(sig, n):
    return math.sqrt(4.0 * math.pi * sig * (n - (D - 2) / 24.0))


def e_casimir_minL(sig, n):
    return 2.0 * math.sqrt(sig * (4.0 * math.pi * n - math.pi / 3.0))


def main():
    print("=" * 66)
    print("STAGE 2 — CLOSED FLUX-TUBE (ISGUR-PATON) GLUEBALLS")
    print("=" * 66)
    print(f"\n[input] sigma = {SIGMA} GeV^2 "
          f"(sqrt = {math.sqrt(SIGMA) * 1000:.1f} MeV), swept +/-10%")

    print("\n[levels at central sigma]")
    for n in (1, 2):
        ea = e_intercept_free(SIGMA, n)
        eb = e_arvis(SIGMA, n)
        ec = e_casimir_minL(SIGMA, n)
        print(f"  n={n}  ({STATES[n]}):")
        print(f"    (a) E^2 = 4 pi sigma n          : {ea:.4f} GeV")
        print(f"    (b) E^2 = 4 pi sigma (n - 1/12) : {eb:.4f} GeV")
        print(f"    (c) min_L [sigma L + (4 pi n - pi/3)/L] : "
              f"{ec:.4f} GeV")

    print("\n[sigma sweep, prescription (a)]")
    for ds in (-0.10, 0.0, 0.10):
        s = SIGMA * (1.0 + ds)
        e1 = e_intercept_free(s, 1)
        e2 = e_intercept_free(s, 2)
        print(f"  sigma = {s:.4f} ({ds:+.0%}): "
              f"n=1 {e1:.4f} GeV, n=2 {e2:.4f} GeV")
    print("  (E ~ sqrt(sigma): a +/-10% tension sweep moves masses +/-5%)")

    print("\n[ordering verdict vs LQCD oracle]")
    print("  LQCD: 0++ ~1.6-1.7 < 2++ ~2.2-2.4 < 0-+ ~2.3-2.6 GeV")
    print("  BESIII X(2370): 2395 +/- 11(stat) +26/-94(syst) MeV, 0-+")
    ea1, ea2 = e_intercept_free(SIGMA, 1), e_intercept_free(SIGMA, 2)
    print(f"  (a) standard: 0++ = 2++ = {ea1:.3f}, 0-+ = {ea2:.3f} GeV")
    print("    -> ordering 0++ ~ 2++ < 0-+ PRESERVED")
    print(f"    -> 0++ {ea1:.3f} vs 1.6-1.7: "
          f"{100 * (ea1 - 1.65) / 1.65:+.1f}% vs mid")
    print(f"    -> 0-+ {ea2:.3f} vs 2.3-2.6: below window by "
          f"{100 * (2.3 - ea2) / 2.3:.1f}% (string too light or")
    print(f"       phonon picture too simple; residual, not fitted)")
    eb1, eb2 = e_arvis(SIGMA, 1), e_arvis(SIGMA, 2)
    print(f"  (b) Arvis:    0++ = 2++ = {eb1:.3f}, 0-+ = {eb2:.3f} GeV")
    print("    -> same ordering; Casimir shifts everything down ~4%")
    ec1, ec2 = e_casimir_minL(SIGMA, 1), e_casimir_minL(SIGMA, 2)
    print(f"  (c) min-L:    0++ = 2++ = {ec1:.3f}, 0-+ = {ec2:.3f} GeV")
    print("    -> ordering preserved but ~2x too heavy: at the L where")
    print("       the Casimir term binds, the loop self-intersects —")
    print("       this is why Isgur-Paton use (a); documented here as")
    print("       the failure mode of the naive Casimir closure.")


if __name__ == "__main__":
    main()
