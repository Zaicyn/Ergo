#!/usr/bin/env python3
"""gen_sdrd_ca.py — calcium site stabilization for SdrD (white bath).

Coordination spheres extracted from pdb/10PS.pdb (protein atoms within
3.0 A of each of the 9 Ca2+; distances in ANGSTROM, scaled x0.399853
to model units by the generator):

  site 1 Ca801, host B1: E652(O,2.24) D655(OD1,2.45) N657(OD1,2.23) S672(O,2.41)
  site 2 Ca802, host B1: N574(OD1,2.27) L671(O,2.26) D674(OD1/OD2,2.55/2.39)
  site 3 Ca803, host B1: D579 D581 N583 V585(O) E587(OE1) E590 (6 coordinators)
  site 4 Ca804, host B2: I762(O) D765 N767 T782(O)
  site 5 Ca805, host B2: D686 M781(O) D784
  site 6 Ca806, host B2: D691 N693 N695 I697(O) D699 E702 (6 coordinators)
  site 7 Ca807, host A2: D363 only (single contact - weak site, documented)
  site 8 Ca808, hosts A2+A3: D363 D365 (A2) D481 (A3) — CROSS-DOMAIN,
         excluded from per-domain runs (no file has both domains)
  site 9 Ca809, host A2: D261 D263 S265 T267 D273

Model (the amide-bead pattern, documented): one dynamic pseudo-atom per
site, initialized at the centroid of its coordinators' C-alpha (per
block, at init), integrated with the same white-hash kicks and damping
as residues. Each coordinator's C-alpha is tethered to its Ca bead by a
harmonic bond FM = -2*K_CA*(D - R0) at the crystal C-alpha->Ca distance
(x0.399853). K_CA = 1.0 default (Go-contact strength; bracket 0.5/2.0
on B1 as sensitivity).
"""

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PM = ROOT / "min" / "pmargin"
SCALE = 0.399853

# (domain, ca_serial, [(crystal_resnum, Calpha-Ca dist A), ...])
SITES = {
    "A2": [
        (1, [(363, 5.49)]),  # Ca807 (single contact — weak site)
        (2, [(261, 4.43), (263, 5.02), (265, 4.44), (267, 4.51), (273, 5.12)]),  # Ca809
    ],
    "A3": [],  # site 8 is cross-domain (A2 coordinators + A3 D481) — excluded, documented
    "B1": [
        (1, [(652, 3.99), (655, 5.01), (657, 4.88), (672, 4.25)]),  # Ca801
        (2, [(574, 4.63), (671, 4.54), (674, 5.20)]),  # Ca802
        (3, [(579, 4.60), (581, 5.20), (583, 4.98), (585, 4.33), (587, 5.08), (590, 6.84)]),  # Ca803
    ],
    "B2": [
        (1, [(762, 3.99), (765, 4.99), (767, 5.07), (782, 4.29)]),  # Ca804
        (2, [(686, 4.79), (781, 4.60), (784, 5.19)]),  # Ca805
        (3, [(691, 4.36), (693, 5.02), (695, 4.97), (697, 4.46), (699, 4.94), (702, 6.63)]),  # Ca806
    ],
}
DOM_OFFSET = {"A2": 242, "A3": 394, "B1": 568, "B2": 680}
K_CA = 1.0

DECLS = """! ── Calcium pseudo-atoms (amide-bead pattern) ──────────────────────
PARAMETER INTEGER :: NCA = __NCA__
PARAMETER REAL :: K_CA = __KCA__
STATIC REAL :: CA_X(3), CA_Y(3), CA_Z(3)
STATIC REAL :: CA_VX(3), CA_VY(3), CA_VZ(3)
STATIC INTEGER :: CT_A(32), CT_B(32)
STATIC REAL :: CT_R0(32)
STATIC INTEGER :: NCT, M
"""

CA_SECTION_A = """    ! Calcium tethers (harmonic staples, crystal C-alpha->Ca distances)
    DO M = 1, NCT
      IA := OFF + CT_A(M)
      IB := CT_B(M)
      DX := RES_X(IA) - CA_X(IB)
      DY := RES_Y(IA) - CA_Y(IB)
      DZ := RES_Z(IA) - CA_Z(IB)
      D := SQRT(DX*DX + DY*DY + DZ*DZ)
      IF D > 0.0 THEN
        FM := -2.0 * K_CA * (D - CT_R0(M))
        RES_VX(IA) := RES_VX(IA) + FM * DX / D * DT * FORCE_SCALE
        RES_VY(IA) := RES_VY(IA) + FM * DY / D * DT * FORCE_SCALE
        RES_VZ(IA) := RES_VZ(IA) + FM * DZ / D * DT * FORCE_SCALE
        CA_VX(IB) := CA_VX(IB) - FM * DX / D * DT * FORCE_SCALE
        CA_VY(IB) := CA_VY(IB) - FM * DY / D * DT * FORCE_SCALE
        CA_VZ(IB) := CA_VZ(IB) - FM * DZ / D * DT * FORCE_SCALE
      ENDIF
    ENDDO

    ! Ca pseudo-atom kicks (white hash, same bath as residues)
    DO K = 1, NCA
      H := IEOR((OFF + NRES + K) * 2654435761, FRAME * 40503)
      H := IEOR(H, ISHFT(H, -30))
      H := H * 6364136223846793005
      H := IEOR(H, ISHFT(H, -27))
      H := H * 6364136223846793005
      H := IEOR(H, ISHFT(H, -31))
      CA_VX(K) := CA_VX(K) + THERMAL_CURRENT * 2.449 * (REAL(IAND(H, 65535)) / 65535.0 - 0.5)
      H := IEOR(H, ISHFT(H, -17))
      CA_VY(K) := CA_VY(K) + THERMAL_CURRENT * 2.449 * (REAL(IAND(H, 65535)) / 65535.0 - 0.5)
      H := IEOR(H, ISHFT(H, -7))
      CA_VZ(K) := CA_VZ(K) + THERMAL_CURRENT * 2.449 * (REAL(IAND(H, 65535)) / 65535.0 - 0.5)
    ENDDO
"""

CA_SECTION_B = """    ! Ca pseudo-atom damping + position update
    DO K = 1, NCA
      CA_VX(K) := CA_VX(K) * VELOCITY_DAMP
      CA_VY(K) := CA_VY(K) * VELOCITY_DAMP
      CA_VZ(K) := CA_VZ(K) * VELOCITY_DAMP
      CA_X(K) := CA_X(K) + CA_VX(K) * DT
      CA_Y(K) := CA_Y(K) + CA_VY(K) * DT
      CA_Z(K) := CA_Z(K) + CA_VZ(K) * DT
    ENDDO
"""

LOOPA_ANCHOR = "  ! Morse bonds (backbone)"
LOOPB_ANCHOR = "    ! Velocity damping"


def build(dom, kca, suffix=""):
    src = (PM / f"sdrd_white_{dom}.ergo").read_text()
    sites = SITES[dom]
    nca = len(sites)
    # tether table: local residue index in the domain file
    teth = []
    m = 0
    for si, (_, coords) in enumerate(sites, 1):
        for resnum, dist in coords:
            m += 1
            local = resnum - DOM_OFFSET[dom]
            teth.append((local, si, dist * SCALE))
    decls = (DECLS.replace("__NCA__", str(nca)).replace("__KCA__", f"{kca}")
             .replace("CA_X(3)", f"CA_X({max(nca,1)})")
             .replace("CA_Y(3)", f"CA_Y({max(nca,1)})")
             .replace("CA_Z(3)", f"CA_Z({max(nca,1)})")
             .replace("CA_VX(3)", f"CA_VX({max(nca,1)})")
             .replace("CA_VY(3)", f"CA_VY({max(nca,1)})")
             .replace("CA_VZ(3)", f"CA_VZ({max(nca,1)})"))
    s = src
    anchor = "DATA SEED_TAB / 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0 /"
    assert anchor in s
    s = s.replace(anchor, anchor + "\n" + decls, 1)
    if nca > 0:
        assert LOOPA_ANCHOR in s
        s = s.replace(LOOPA_ANCHOR, CA_SECTION_A + "\n" + LOOPA_ANCHOR, 1)
        assert LOOPB_ANCHOR in s
        s = s.replace(LOOPB_ANCHOR, CA_SECTION_B + "\n" + LOOPB_ANCHOR, 1)
    # init: tether table + bead init at coordinator centroid per block
    init = ["  NCT := %d" % len(teth)]
    for m2, (local, si, r0) in enumerate(teth, 1):
        init.append(f"  CT_A({m2}) := {local}")
        init.append(f"  CT_B({m2}) := {si}")
        init.append(f"  CT_R0({m2}) := {r0:.4f}")
    # per-block bead init: centroid of coordinator Calphas; zero velocity
    init.append("  DO B = 1, NBLK")
    init.append("    OFF := (B - 1) * NRES")
    for si, (_, coords) in enumerate(sites, 1):
        locals_ = [r - DOM_OFFSET[dom] for r, _ in coords]
        for comp in "XYZ":
            terms = " + ".join(f"RES_{comp}(OFF + {l})" for l in locals_)
            init.append(f"    CA_{comp}({si}) := ({terms}) / {len(locals_)}.0")
        init.append(f"    CA_VX({si}) := 0.0")
        init.append(f"    CA_VY({si}) := 0.0")
        init.append(f"    CA_VZ({si}) := 0.0")
    init.append("  ENDDO")
    # insert init right after INIT_TABLES() call (tables/coils already set)
    a2 = "CALL INIT_TABLES()\n"
    assert a2 in s
    s = s.replace(a2, a2 + "\n" + "\n".join(init) + "\n", 1)
    s = s.replace("! PACKED_SDRD_" + dom.upper() + "_WHITE",
                  f"! PACKED_SDRD_{dom.upper()}_CA — white bath + calcium staples (K_CA={kca}, {nca} sites)")
    out = PM / f"sdrd_ca_{dom}{suffix}.ergo"
    out.write_text(s)
    print(f"wrote {out} (NCA={nca}, {len(teth)} tethers, K_CA={kca})")


for dom in ("A2", "A3", "B1", "B2"):
    build(dom, 1.0)
build("B1", 0.5, "_k05")
build("B1", 2.0, "_k20")
