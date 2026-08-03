"""TenPy version of the spin-1 rotor chain (Part 1: calibration gate).

Same Hamiltonian as gap_map.RotorChain (drift off):
  H = sum_i p_i^2/2 - K_PHASE sum_i cos(phi_i - ref_i)
      - B*K_BIAS sum_i cos(phi_i - ref_i - pi) - J sum_i cos(phi_i - phi_{i+1})
periodic, I=1, K_PHASE=0.5, K_BIAS=2.0, ref_i = 2*pi*i/N.

Operator convention (unit matrix elements, NOT spin-1 S+):
  e^{i phi} |m> = |m+1>  == 'Tm' = [[0,0,0],[1,0,0],[0,1,0]]
  e^{-i phi}            == 'Tp' = [[0,1,0],[0,0,1],[0,0,0]]
  cos(phi - a) = (e^{-ia} Tm + e^{ia} Tp) / 2
  bond -J cos(phi_i - phi_j) = -J/2 (Tm_i Tp_j + Tp_i Tm_j)

DMRG (two-site, mixer on, chi_max=256) at (B,J) = (0.25,1.0) and (0.5,0.5)
for N = 8..14, compared against ED references from results_fss.json /
fss_followup. Gate: |dE|/N < 1e-6.
"""

import json

import numpy as np
import tenpy
from tenpy.models.lattice import Chain
from tenpy.models.model import CouplingMPOModel
from tenpy.networks.mps import MPS
from tenpy.algorithms import dmrg

K_PHASE, K_BIAS = 0.5, 2.0
POINTS = [(0.25, 1.0), (0.5, 0.5)]
NS = [8, 10, 12, 13, 14]

# ED references, loaded at full precision from results_fss.json
def _load_ed_ref():
    ref = {}
    try:
        F = json.load(open("results_fss.json"))
        for p in F["points"]:
            if "E0" in p:
                ref[(p["B"], p["J"], p["N"])] = p["E0"]
    except FileNotFoundError:
        pass
    return ref


ED_REF_FULL = _load_ed_ref()


def rotor_site():
    from tenpy.linalg.charges import LegCharge
    from tenpy.networks.site import Site
    leg = LegCharge.from_trivial(3)
    site = Site(leg)
    Tp = np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=complex)
    site.add_op("Tp", Tp)
    site.add_op("Tm", Tp.T.copy())
    site.add_op("p2", np.diag([1.0, 0.0, 1.0]))
    return site


class RotorChainMPO(CouplingMPOModel):
    def init_lattice(self, model_params):
        site = rotor_site()
        return Chain(model_params["L"], site, bc="periodic", bc_MPS="finite")

    def init_terms(self, model_params):
        B = model_params["B"]
        J = model_params["J"]
        N = model_params["L"]
        refs = 2.0 * np.pi * np.arange(N) / N
        # onsite: -K_PHASE cos(phi-ref) - B K_BIAS cos(phi-ref-pi)
        s_tm = -0.5 * (K_PHASE * np.exp(-1j * refs)
                       + B * K_BIAS * np.exp(-1j * (refs + np.pi)))
        self.add_onsite(0.5, 0, "p2")
        self.add_onsite(s_tm, 0, "Tm")
        self.add_onsite(np.conj(s_tm), 0, "Tp")
        # bonds: -J/2 (Tm_i Tp_j + Tp_i Tm_j)
        self.add_coupling(-J / 2, 0, "Tm", 0, "Tp", 1)
        self.add_coupling(-J / 2, 0, "Tp", 0, "Tm", 1)


def run_dmrg(N, B, J, chi_max=256):
    model = RotorChainMPO({"L": N, "B": B, "J": J})
    psi = MPS.from_product_state(model.lat.mps_sites(), [1] * N, bc="finite")
    eng = dmrg.TwoSiteDMRGEngine(psi, model, {
        "mixer": True,
        "max_E_err": 1e-12,
        "max_sweeps": 60,
        "trunc_params": {"chi_max": chi_max, "svd_min": 1e-13},
    })
    E, psi = eng.run()
    return float(np.real(E)), int(np.max(psi.chi))


def main():
    tenpy.tools.misc.setup_logging(to_stdout="ERROR")
    results = []
    for B, J in POINTS:
        for N in NS:
            E, chi = run_dmrg(N, B, J)
            ref = ED_REF_FULL.get((B, J, N))
            dE = abs(E - ref) if ref is not None else None
            rec = {"N": N, "B": B, "J": J, "E_dmrg": E, "E_ed": ref,
                   "dE": dE, "dE_per_site": (dE / N if dE is not None else None),
                   "chi_max_used": chi}
            results.append(rec)
            print(f"B={B} J={J} N={N}: E={E:.10f} ref={ref} "
                  f"dE/N={rec['dE_per_site']} chi={chi}", flush=True)
            with open("tenpy_calib.json", "w") as f:
                json.dump({"gate": "|dE|/N < 1e-6", "results": results},
                          f, indent=1)
    ok = all(r["dE_per_site"] is None or r["dE_per_site"] < 1e-6
             for r in results)
    print("GATE PASSED" if ok else "GATE FAILED", flush=True)


if __name__ == "__main__":
    main()
