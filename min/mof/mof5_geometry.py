#!/usr/bin/env python3
"""mof5_geometry.py — Stage 3: MOF-5 geometric model.

Zn4O(BDC)3, cubic Fm-3m, pcu topology: Zn4O cluster centroids are the
nodes, BDC linkers the edges. Two nearest-neighbor nodes span half the
conventional cell edge (the F-centered cell holds 8 formula units).

All quantities are derived from standard bond lengths/angles
(documented per line); the oracle numbers from literature:
  a ~ 25.7-25.92 A, density ~0.59 g/cm^3, aperture ~8 A,
  Langmuir surface area ~2900 m^2/g.

Bond/angle assumptions (typical Zn-carboxylate/BDC values):
  Zn-O(oxo)      1.92 A     (Zn4O core)
  Zn-O(carb)     1.97 A
  O-C(carb)      1.28 A, Zn-O-C angle 130 deg (folds back)
  C-C(carb-ipso) 1.49 A
  ring para span 2.78 A     (2 x 1.39)
  vdW radius C/H ~1.7/1.2 A

Determinism: pure arithmetic, no RNG; run twice byte-identical.
"""
import numpy as np

NA = 6.02214076e23

# --- components (angstrom) ---
D_ZNO_CORE = 1.92
D_ZNO_CARB = 1.97
D_OC = 1.28
ANG_ZOC = np.radians(130.0)
D_CCARB = 1.49
RING_PARA = 2.78
VDW_C = 1.7
VDW_H = 1.2


def main():
    print("=" * 66)
    print("MOF-5 GEOMETRY — geometric model vs literature")
    print("=" * 66)

    # --- lattice parameter ---
    # node -> carboxylate-C: the Zn-O-C arm has length
    #   L_arm = r_nodeZn + Zn-O + O-C*cos(50 deg)  (130 deg bend)
    # but its direction vs the pcu edge is the model's angle input.
    # Presented three ways (honest bracket, no tuning):
    L_arm = (D_ZNO_CORE + D_ZNO_CARB
             + D_OC * np.cos(np.pi - ANG_ZOC))
    half_link = D_CCARB + RING_PARA / 2.0
    # (i) naive collinear (arm along the edge)
    a1 = 2.0 * (2.0 * L_arm + 2.0 * half_link)
    # (ii) arm along the tetrahedral (111) axis: projection x 1/sqrt(3)
    a2 = 2.0 * (2.0 * L_arm / np.sqrt(3.0) + 2.0 * half_link)
    # (iii) arm angle from the measured structure's centroid-to-C
    # distance 3.4 A (this one number taken from the reported
    # structure, labeled; rest derived)
    r_node_C = 3.4
    theta = np.degrees(np.arccos(r_node_C / L_arm))
    node_node = 2.0 * r_node_C + 2.0 * half_link
    a_model = 2.0 * node_node
    print(f"\n[lattice parameter]")
    print(f"  arm length L_arm = {L_arm:.3f} A "
          f"(Zn-O(oxo) {D_ZNO_CORE} + Zn-O(carb) {D_ZNO_CARB} "
          f"+ O-C proj {D_OC * np.cos(np.pi - ANG_ZOC):.2f})")
    print(f"  (i)   collinear arm:       a = {a1:.2f} A "
          f"({100 * (a1 / 25.8 - 1):+.1f}% vs 25.669-25.92)")
    print(f"  (ii)  arm along (111):     a = {a2:.2f} A "
          f"({100 * (a2 / 25.8 - 1):+.1f}%)")
    print(f"  (iii) arm angle {theta:.1f} deg from the measured "
          f"centroid->C = 3.4 A: a = {a_model:.2f} A "
          f"({100 * (a_model / 25.8 - 1):+.1f}%)")
    print(f"  -> the geometry brackets the literature value; the arm "
          f"angle is the one structural input")

    # --- density ---
    M_fu = 4 * 65.38 + 16.00 + 3 * (8 * 12.011 + 4 * 1.008 + 4 * 15.999)
    a_lit = 25.669e-8        # cm
    for a_use, tag in ((a_model, "model"), (25.669, "literature")):
        V = (a_use * 1e-8) ** 3
        rho = 8 * M_fu / NA / V
        print(f"  density ({tag} a={a_use:.3f}): {rho:.4f} g/cm^3 "
              f"vs ~0.59 literature (dev "
              f"{100 * abs(rho - 0.59) / 0.59:.1f}%)")

    # --- pore aperture ---
    # large-cavity window: bottleneck between two nearest SBUs along
    # the edge: free opening = node-node minus 2 x (node->linker vdW
    # surface). Model the linker as a rod of vdW radius ~1.7 A and the
    # SBU carboxylate shell at r_node-C + vdW_C.
    # aperture: the window into the large cavity is the square opening
    # whose four sides are BDC linkers spanning the SBU-SBU gap;
    # free diameter = side length minus the rod vdW thicknesses
    ap2 = node_node - 2.0 * (VDW_C + VDW_H)
    print(f"\n[pore aperture] square-window (4 BDC rods, side = "
          f"node-node): {ap2:.2f} A (literature ~8 A, "
          f"{100 * (ap2 / 8.0 - 1):+.0f}%)")

    # --- surface area (geometric, order-of-magnitude) ---
    # per conventional cell: 8 SBUs, 24 BDC linkers (8 nodes x 6
    # edges / 2 shared)
    A_bdc = 2.0 * (RING_PARA + 2 * D_CCARB) * 4.6   # two faces of the
                                                    # aryl slab (w~4.6)
    A_sbu = 4.0 * np.pi * 3.5 ** 2                  # sphere r=3.5 A
    A_cell = 24 * A_bdc + 8 * A_sbu                 # A^2 per cell
    M_cell = 8 * M_fu                                # g/mol per cell
    sa = A_cell * 1e-20 * NA / M_cell                # m^2/g
    print(f"\n[surface area] geometric model: {sa:.0f} m^2/g "
          f"(literature Langmuir ~2900; BET range 800-3800)")
    print(f"  per-cell contributions: 24 BDC faces {24 * A_bdc:.0f} A^2 "
          f"+ 8 SBU spheres {8 * A_sbu:.0f} A^2")
    print(f"  gap note: geometric estimates undercount the Langmuir "
          f"area because the Langmuir monolayer follows the corrugated")
    print(f"  vdW surface at sub-angstrom detail; our flat-slab slabs "
          f"understate the ring/carboxylate corrugation. Documented,")
    print(f"  not tuned.")

    # --- cavity sizes (bonus geometry) ---
    print(f"\n[cavities] large-cavity estimate ~{node_node + 2 * 1.2:.1f} A "
          f"(lit ~15 A); small ~{node_node - 2 * 1.5:.1f} A (lit ~11 A)")


if __name__ == "__main__":
    main()
