#!/usr/bin/env python3
"""m2_mirror.py — M2 mirror: the buc op chain re-implemented in python,
fed the MEASURED mesh(t) series from a cell_unit ELEC trace, verifying
the count-space pool port tick-for-tick (mirror-in-the-loop; the buc
chain itself was already validated exact against the F77 harness:
-246.4392/0.8777 at tick 10000).

Usage: python3 min/cell/m2_mirror.py <cell_unit_log>
Prints final mirror PSI/ATP/dP and the diff vs the log's ELEC_FINAL,
plus the count-conservation drift for BATH=0 logs.
"""
import math
import sys

path = sys.argv[1]
mesh_series = []
final = None
closure = None
for line in open(path):
    if line.startswith("CLOSURE "):
        closure = line.split()
    elif line.startswith("ELEC "):
        p = line.split()
        mesh_series.append((int(p[1]), float(p[8])))
    elif line.startswith("ELEC_FINAL "):
        final = line.split()
assert closure and final, "log missing CLOSURE/ELEC_FINAL"
# CLOSURE nclosed 1 hits 162 vin <v> vout <v> vr <v> cmean <v> cref <v>
vin = float(closure[6])
vr = float(closure[10])
f = {final[i]: final[i + 1] for i in range(1, len(final) - 1, 2)}
bath = int(f["bath"])
nt = mesh_series[-1][0]


def mesh_at(t):
    if t <= mesh_series[0][0]:
        return mesh_series[0][1]
    for (t0, m0), (t1, m1) in zip(mesh_series, mesh_series[1:]):
        if t0 <= t <= t1:
            return m0 + (m1 - m0) * (t - t0) / (t1 - t0)
    return mesh_series[-1][1]


PSI, ATP = -150.0, 0.8
HIN, KIN = 3.16e-5, 200.0
# bath-on: external pool is clamped at HOUT0 = the (constant) hout field;
# bath-off: hout drifts, so the initial value is the pH-4 default 1e-4
# (the only bath-off arm run).
HOUT = float(f["hout"]) if bath == 1 else 1.0e-4
KOUT = 5.0
DP = PSI

for it in range(1, nt + 1):
    MSH = mesh_at(it)
    EK = 61.5*math.log10(KOUT/KIN) if KIN > 1e-10 and KOUT > 1e-10 else 0.0
    EH = 61.5*math.log10(HOUT/HIN) if HIN > 1e-15 and HOUT > 1e-15 else 0.0
    GK = 0.008*(1-0.95*MSH)
    GH = 0.002*(1-0.95*MSH)
    IK = GK*(PSI-EK)
    IH = GH*(PSI-EH)
    PRATE = 0.05*ATP/(ATP+0.3) if ATP > 0.001 else 0.0
    DN = min(PRATE*2e-5, max(HIN-1e-8, 0.0))
    HIN -= DN
    if bath == 0:
        HOUT += DN*vr
    ATP = max(ATP-0.008*PRATE, 0.0)
    if HIN > 1e-15 and HOUT > 1e-15:
        DP = PSI-60.0*math.log10(HIN/HOUT)
    else:
        DP = PSI
    if DP < -80.0 and PSI < -100.0:
        EX = abs(DP)-80.0
        VP = min(1.0, (abs(PSI)-100.0)/50.0)
        SR = 0.08*EX*EX/(EX*EX+6400.0)*VP
        ATP = min(ATP+0.005*SR, 1.0)
        HIN += 5e-7*SR
        if bath == 0:
            HOUT -= 5e-7*SR*vr
    ATP = max(ATP-0.00005, 0.0)
    PSI = max(-300.0, min(50.0, PSI-(IK+IH+2.0*PRATE)/0.02))
    dK = IK*0.05
    dH = IH*5e-5
    KIN = min(500.0, max(0.1, KIN-dK))
    HIN = min(1e-2, max(1e-8, HIN-dH))
    if bath == 0:
        KOUT += dK*vr
        HOUT += dH*vr

e_psi, e_atp, e_dp = float(f["psi"]), float(f["atp"]), float(f["dp"])
print(f"mirror : PSI {PSI:.4f}  ATP {ATP:.6f}  dP {DP:.4f}  "
      f"HIN {HIN:.6e}  HOUT {HOUT:.6e}  KIN {KIN:.4f}  KOUT {KOUT:.4f}")
print(f"ergo   : PSI {e_psi:.4f}  ATP {e_atp:.6f}  dP {e_dp:.4f}  "
      f"HIN {float(f['hin']):.6e}  HOUT {float(f['hout']):.6e}  "
      f"KIN {float(f['kin']):.4f}  KOUT {float(f['kout']):.4f}")
print(f"diff   : dPSI {PSI-e_psi:+.4f} mV  dATP {ATP-e_atp:+.6f}  "
      f"ddP {DP-e_dp:+.4f}")
if bath == 0:
    ntot = float(f["nhi"]) + float(f["nho"])
    ntot0 = 3.16e-5*vin*1e7 + 1.0e-4*(46656.0-vin)*1e7
    print(f"H-count conservation: final {ntot:.1f} vs initial "
          f"{ntot0:.1f}  rel drift {(ntot-ntot0)/ntot0:+.2e}")
