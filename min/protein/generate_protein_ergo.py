#!/usr/bin/env python3
"""generate_protein_ergo.py

Generate a protein-folding .ergo variant from a Cα-only template.

Usage example:
  python3 tests/generate_protein_ergo.py \
      --name chignolin \
      --json pdb/1UAO_ca.json \
      --pdb pdb/1UAO.pdb \
      --chain A \
      --output tests/waveform_chignolin.ergo
"""

import argparse
import json
import numpy as np
import math
import os
import re
import sys


# ── residue mapping ──────────────────────────────────────────────────
HYDRO = {
    'A': 0.5, 'C': 0.0, 'D': 0.0, 'E': 0.0, 'F': 1.0,
    'G': 0.0, 'H': 0.0, 'I': 0.7, 'K': 0.0, 'L': 0.8,
    'M': 0.6, 'N': 0.0, 'P': 0.6, 'Q': 0.0, 'R': 0.0,
    'S': 0.0, 'T': 0.0, 'V': 0.7, 'W': 1.0, 'Y': 1.0,
    # non-standard / D-amino acids commonly treated as their parent
    'DPR': 0.6,  # D-proline
    'DVA': 0.7,  # D-valine (just in case)
}

def one_letter(resname: str) -> str:
    """Return a 1-character code for hydrophobic lookup."""
    r = resname.strip().upper()
    if r in HYDRO:
        return r
    table = {
        'ALA': 'A', 'CYS': 'C', 'ASP': 'D', 'GLU': 'E', 'PHE': 'F',
        'GLY': 'G', 'HIS': 'H', 'ILE': 'I', 'LYS': 'K', 'LEU': 'L',
        'MET': 'M', 'ASN': 'N', 'PRO': 'P', 'GLN': 'Q', 'ARG': 'R',
        'SER': 'S', 'THR': 'T', 'VAL': 'V', 'TRP': 'W', 'TYR': 'Y',
    }
    return table.get(r, r)


def parse_ca_json(path: str):
    """Read the Cα/Cβ JSON produced by the extraction step."""
    with open(path) as f:
        data = json.load(f)
    coords = []
    for row in data['coords']:
        # row: [seq_index, pdb_resnum, ca_x, ca_y, ca_z]
        coords.append({
            'seq': int(row[0]),
            'pdb_res': int(row[1]),
            'x': float(row[2]),
            'y': float(row[3]),
            'z': float(row[4]),
        })
    coords.sort(key=lambda c: c['seq'])
    cb_coords = data.get('cb_coords', None)
    res_names = data.get('res_names', None)
    return coords, data.get('mean_ca_ca', None), cb_coords, res_names


def parse_pdb_sequence(pdb_path: str, chain: str, pdb_resnums: list):
    """Return residue names in the same order as the JSON coords."""
    seq_map = {}
    with open(pdb_path) as f:
        for line in f:
            if not (line.startswith('ATOM') or line.startswith('HETATM')):
                continue
            atom_name = line[12:16].strip()
            res_name = line[17:20].strip()
            ch = line[21]
            try:
                res_seq = int(line[22:26].strip())
            except ValueError:
                continue
            if ch != chain:
                continue
            if atom_name != 'CA':
                continue
            seq_map[res_seq] = res_name
    return [seq_map.get(r, 'UNK') for r in pdb_resnums]


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

def vec_len(v):
    return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])

def vec_dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def vec_cross(a, b):
    return (a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])


def native_angle(r1, r2, r3):
    """Cα-Cα-Cα angle at r2 (radians)."""
    b1 = vec_sub(r1, r2)
    b2 = vec_sub(r3, r2)
    l1 = vec_len(b1)
    l2 = vec_len(b2)
    if l1 == 0.0 or l2 == 0.0:
        return 0.0
    c = max(-1.0, min(1.0, vec_dot(b1, b2) / (l1 * l2)))
    return math.acos(c)


def native_dihedral(r1, r2, r3, r4):
    """Signed Cα-Cα-Cα-Cα dihedral using the same BIO convention as the .ergo code."""
    b1 = vec_sub(r2, r1)
    b2 = vec_sub(r3, r2)
    b3 = vec_sub(r4, r3)
    n1 = vec_cross(b1, b2)
    n2 = vec_cross(b2, b3)
    n1n2 = vec_dot(n1, n2)
    b2len = vec_len(b2)
    b1n2 = vec_dot(b1, n2)
    if b2len == 0.0:
        return 0.0
    return math.atan2(b2len * b1n2, n1n2)


def scale_and_geometry(coords, mean_ca_ca, cb_coords=None):
    """Scale to model units where the average native Cα-Cα bond is BACKBONE_R0."""
    scale = 1.52 / mean_ca_ca
    scaled = []
    for c in coords:
        scaled.append((c['x'] * scale, c['y'] * scale, c['z'] * scale))
    scaled_cb = None
    if cb_coords is not None:
        scaled_cb = [(x * scale, y * scale, z * scale) for x, y, z in cb_coords]
    return scale, scaled, scaled_cb


def compute_native_contacts(scaled, nres, min_sep, phys_cutoff_ang, scale):
    """Return list of (i,j,model_distance) for native contacts."""
    contacts = []
    cutoff_model = phys_cutoff_ang * scale
    for i in range(1, nres + 1):
        for j in range(i + 1, nres + 1):
            sep = j - i
            if sep < min_sep:
                continue
            d = vec_len(vec_sub(scaled[i-1], scaled[j-1]))
            if d <= cutoff_model:
                contacts.append((i, j, d))
    return contacts, cutoff_model


def compute_register_torsions(scaled, contacts, nres, max_s=2):
    """Return cross-strand register torsions for native contacts.

    For each native contact (i,j) and step s=1,2, if (i±s, j∓s) is also a native
    contact, define a 4-atom torsion (i, i±s, j∓s, j) with its native dihedral target.
    """
    contact_set = set()
    for i, j, _ in contacts:
        if i < j:
            contact_set.add((i, j))
        else:
            contact_set.add((j, i))
    entries = []
    for i, j in sorted(contact_set):
        for s in range(1, max_s + 1):
            b1 = i + s
            c1 = j - s
            if b1 <= nres and c1 >= 1 and (b1, c1) in contact_set:
                p0 = native_dihedral(scaled[i-1], scaled[b1-1], scaled[c1-1], scaled[j-1])
                entries.append((i, b1, c1, j, p0))
            b2 = i - s
            c2 = j + s
            if b2 >= 1 and c2 <= nres and (b2, c2) in contact_set:
                p0 = native_dihedral(scaled[i-1], scaled[b2-1], scaled[c2-1], scaled[j-1])
                entries.append((i, b2, c2, j, p0))
    return entries


# ── template generation helpers ──────────────────────────────────────
def f_arr_1d(name, values, fmt="%.6f"):
    lines = [f"  {name}({i+1}) := {fmt % v}" for i, v in enumerate(values)]
    return "\n".join(lines)


def gen_init_chain(nres, seq, hydro_values, ang_t0, tors_p0, tors_k=0.6000,
                     cb_offsets=None, aromatic_mult=None, domain_anchors=None):
    """Produce the full INIT_CHAIN subroutine body for the new protein."""
    lines = ["SUBROUTINE INIT_CHAIN()",
             "  INTEGER :: I, ATT, J2, OK",
             "  REAL :: TH0, OM0, R",
             "  REAL :: U1, U2, COSTH, SINTH, PHI2, UX, UY, UZ, CANDX, CANDY, CANDZ, DD",
             "",
             "  ! Self-avoiding random walk coil (denatured start)"]
    if domain_anchors and 1 in domain_anchors:
        ax = domain_anchors[1]
        lines += ["  ! Axial init: domain 1 anchored at its native COM",
                  f"  RES_X(1) := {ax[0]:.6f}",
                  f"  RES_Y(1) := {ax[1]:.6f}",
                  f"  RES_Z(1) := {ax[2]:.6f}"]
    else:
        lines += ["  RES_X(1) := 10.0",
                  "  RES_Y(1) := 10.0",
                  "  RES_Z(1) := 10.0"]
    lines += ["  DO I = 2, NRES"]
    lines += ["    OK := 0",
             "    ATT := 0"]
    if domain_anchors:
        for s_res in sorted(domain_anchors):
            if s_res == 1:
                continue
            ax = domain_anchors[s_res]
            lines += ["    ! Axial init: domain-start anchor at native COM;",
                      "    ! ATT := 20 pre-expires the random walk for this residue",
                      f"    IF I = {s_res} THEN",
                      f"      CANDX := {ax[0]:.6f}",
                      f"      CANDY := {ax[1]:.6f}",
                      f"      CANDZ := {ax[2]:.6f}",
                      f"      ATT := 20",
                      f"    ENDIF"]
    lines += ["    DO WHILE ATT < 20",
             "      ATT := ATT + 1",
             "      U1 := MOD(ABS(SIN(REAL(I) * 12.9898 + REAL(ATT) * 3.7 + SEED) * 43758.5453), 1.0)",
             "      U2 := MOD(ABS(SIN(REAL(I) * 78.2330 + REAL(ATT) * 1.3 + SEED) * 12543.1230), 1.0)",
             "      COSTH := 2.0 * U1 - 1.0",
             "      SINTH := SQRT(1.0 - COSTH * COSTH)",
             "      PHI2 := 2.0 * 3.14159265 * U2",
             "      UX := SINTH * COS(PHI2)",
             "      UY := SINTH * SIN(PHI2)",
             "      UZ := COSTH",
             "      CANDX := RES_X(I - 1) + UX * BACKBONE_R0",
             "      CANDY := RES_Y(I - 1) + UY * BACKBONE_R0",
             "      CANDZ := RES_Z(I - 1) + UZ * BACKBONE_R0",
             "      OK := 1",
             "      IF I ≥ 5 THEN",
             "        DO J2 = 1, I - 4",
             "          DD := SQRT((CANDX - RES_X(J2))**2 + (CANDY - RES_Y(J2))**2 + (CANDZ - RES_Z(J2))**2)",
             "          IF DD < 1.55 THEN",
             "            OK := 0",
             "          ENDIF",
             "        ENDDO",
             "      ENDIF",
             "      IF OK = 1 THEN",
             "        ATT := 20",
             "      ENDIF",
             "    ENDDO",
             "    RES_X(I) := CANDX",
             "    RES_Y(I) := CANDY",
             "    RES_Z(I) := CANDZ",
             "  ENDDO",
             "",
             "  ! Phases from position hash; zero velocities",
             "  DO I = 1, NRES",
             "    RES_THETA(I) := 0.3 * RES_X(I) + 0.5 * RES_Y(I) + 0.7 * RES_Z(I) + SEED",
             "    RES_OMEGA(I) := BASE_OMEGA + 0.5 * SIN(RES_THETA(I))",
             "    RES_VX(I) := 0.0",
             "    RES_VY(I) := 0.0",
             "    RES_VZ(I) := 0.0",
             "  ENDDO",
             "",
             "  ! Sequence design: native angle targets and native torsion targets",
             "  DO I = 1, NRES",
             "    RES_ANGK(I) := 0.3000",
             f"    RES_TORSK(I) := {tors_k:.4f}",
             "  ENDDO",
             ""]
    # angle targets
    lines.append("  ! Native Cα-Cα-Cα angle targets")
    for i, v in enumerate(ang_t0):
        lines.append(f"  RES_ANGT0({i+1}) := {v:.6f}")
    lines.append("")
    # torsion targets
    lines.append("  ! Native Cα-Cα-Cα-Cα dihedral targets")
    for i, v in enumerate(tors_p0):
        lines.append(f"  RES_TORSP0({i+1}) := {v:.6f}")
    lines.append("")
    # hydrophobic weights
    lines.append("  ! Hydrophobic weights from residue type")
    for i, (s, h) in enumerate(zip(seq, hydro_values), start=1):
        lines.append(f"  RES_HYDRO({i}) := {h:.1f}   ! {s}")
    lines.append("")
    if cb_offsets is not None:
        # CB offsets relative to CA (native geometry, moves with CA)
        lines.append("  ! Cβ offsets relative to Cα (from native structure)")
        for i, (ox, oy, oz) in enumerate(cb_offsets, start=1):
            lines.append(f"  CB_OFF_X({i}) := {ox:.6f}")
            lines.append(f"  CB_OFF_Y({i}) := {oy:.6f}")
            lines.append(f"  CB_OFF_Z({i}) := {oz:.6f}")
        lines.append("")
    if aromatic_mult is not None:
        lines.append("  ! Aromatic side-chain multipliers (Phe=0.5, Tyr=0.7, Trp=1.0)")
        for i, m in enumerate(aromatic_mult, start=1):
            lines.append(f"  AROMATIC_MULT({i}) := {m:.2f}")
        lines.append("")
    lines.append("  RETURN")
    lines.append("END")
    return "\n".join(lines)


def parse_domains_arg(arg, nres):
    """Parse --domains: either '1-98,99-136' or a JSON file {'D1': [1, 98], ...}.

    Returns a list of (start, end) 1-based inclusive intervals, or None.
    """
    if arg is None:
        return None
    if arg.endswith('.json') or os.path.exists(arg):
        with open(arg) as f:
            data = json.load(f)
        return sorted((int(v[0]), int(v[1])) for v in data.values())
    intervals = []
    for part in arg.split(','):
        a, b = part.split('-')
        intervals.append((int(a), int(b)))
    for s, e in intervals:
        if not (1 <= s <= e <= nres):
            raise ValueError(f"domain {s}-{e} outside 1..{nres}")
    return sorted(intervals)


def domain_of(resi, intervals):
    """1-based residue -> domain index, or None."""
    for k, (s, e) in enumerate(intervals):
        if s <= resi <= e:
            return k
    return None


def _frame_quat(t_, n_, b_):
    """Quaternion (w,x,y,z) of rotation matrix with columns [t n b], Shepperd's method."""
    m00, m01, m02 = t_[0], n_[0], b_[0]
    m10, m11, m12 = t_[1], n_[1], b_[1]
    m20, m21, m22 = t_[2], n_[2], b_[2]
    tr = m00 + m11 + m22
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        return np.array([0.25*s, (m21-m12)/s, (m02-m20)/s, (m10-m01)/s])
    if m00 > m11 and m00 > m22:
        s = np.sqrt(1.0 + m00 - m11 - m22) * 2
        return np.array([(m21-m12)/s, 0.25*s, (m01+m10)/s, (m02+m20)/s])
    if m11 > m22:
        s = np.sqrt(1.0 + m11 - m00 - m22) * 2
        return np.array([(m02-m20)/s, (m01+m10)/s, 0.25*s, (m12+m21)/s])
    s = np.sqrt(1.0 + m22 - m00 - m11) * 2
    return np.array([(m10-m01)/s, (m02+m20)/s, (m12+m21)/s, 0.25*s])


def _quat_rot(q, v):
    """R(q) v — same formula as the ergo template."""
    w, x, y, z = q
    R = np.array([
        [w*w+x*x-y*y-z*z, 2*(x*y-w*z),     2*(x*z+w*y)],
        [2*(x*y+w*z),     w*w-x*x+y*y-z*z, 2*(y*z-w*x)],
        [2*(x*z-w*y),     2*(y*z+w*x),     w*w-x*x-y*y+z*z]])
    return R @ np.asarray(v)


def native_frames(scaled, breaks=None):
    """Per-residue Frenet frames from native C-alpha geometry.
    Returns (quats[N,4], bondvecs[N,3]) in model units.
    breaks: 1-based indices that END a chain segment (break after that residue);
    frames are computed per segment and concatenated."""
    if breaks:
        cuts = sorted(set(breaks))
        bounds = [0] + cuts + [len(scaled)]
        quats, bondvecs = [], []
        for a, b in zip(bounds[:-1], bounds[1:]):
            q_seg, bv_seg = native_frames(scaled[a:b])
            quats.extend(q_seg)
            bondvecs.extend(bv_seg)
        return quats, bondvecs
    p = [np.array(c, float) for c in scaled]
    n = len(p)
    quats = []
    for i in range(n):
        lo = max(0, i-1); hi = min(n-1, i+1)
        b1 = p[i] - p[lo]; b2 = p[hi] - p[i]
        if np.linalg.norm(b1) < 1e-12 or np.linalg.norm(b2) < 1e-12 or np.linalg.norm(np.cross(b1, b2)) < 1e-12:
            quats.append(quats[-1] if quats else np.array([1.0, 0, 0, 0]))
            continue
        t_ = (b1/np.linalg.norm(b1) + b2/np.linalg.norm(b2))
        t_ = t_/np.linalg.norm(t_)
        n_ = np.cross(b1, b2); n_ = n_/np.linalg.norm(n_)
        b_ = np.cross(t_, n_)
        quats.append(_frame_quat(t_, n_, b_))
    # sign continuity (q and -q are the same rotation)
    for i in range(1, n):
        if np.dot(quats[i], quats[i-1]) < 0:
            quats[i] = -quats[i]
    bondvecs = []
    for i in range(n):
        if i < n-1:
            bondvecs.append(_quat_rot([quats[i][0], -quats[i][1], -quats[i][2], -quats[i][3]], p[i+1]-p[i]))
        else:
            bondvecs.append(np.zeros(3))
    return quats, bondvecs


def parse_pair_list_arg(s):
    """Parse '71-76,72-7' into a list of (i, j) 1-based index tuples."""
    if s is None:
        return None
    pairs = []
    for part in s.split(','):
        a, b = part.strip().split('-')
        pairs.append((int(a), int(b)))
    return pairs


def parse_mispair_arg(s):
    """Parse '7-76,7-158:0.5' into (i, j, k-or-None) tuples (1-based)."""
    if s is None:
        return None
    out = []
    for part in s.split(','):
        part = part.strip()
        if ':' in part:
            pr, k = part.split(':')
            a, b = pr.split('-')
            out.append((int(a), int(b), float(k)))
        else:
            a, b = part.split('-')
            out.append((int(a), int(b), None))
    return out


def gen_init_native(nres, scaled_coords, contacts, scale, cutoff_model, register_entries=None, register_k=0.5,
                    domains=None, cystine=None, mispair=None, chain_break=None):
    """Produce the full INIT_NATIVE subroutine body for the new protein."""
    lines = ["SUBROUTINE INIT_NATIVE()",
             "  INTEGER :: I, J",
             "",
             f"  ! Native Cα coordinates, scaled by factor {scale:.6f}",
             ""]
    for i, (x, y, z) in enumerate(scaled_coords, start=1):
        lines.append(f"  NATIVE_X({i}) := {x:.6f}")
        lines.append(f"  NATIVE_Y({i}) := {y:.6f}")
        lines.append(f"  NATIVE_Z({i}) := {z:.6f}")
    lines.append("")
    if chain_break is None:
        _breaks = None
    elif isinstance(chain_break, (list, tuple)):
        _breaks = list(chain_break)
    else:
        _breaks = [chain_break]
    quats, bondvecs = native_frames(scaled_coords, breaks=_breaks)
    lines.append("")
    lines.append("  ! Native per-residue frames (Frenet) as quaternions, and")
    lines.append("  ! native bond vectors in the local frame (oriented-ribbon dynamics)")
    for i, (q, bv) in enumerate(zip(quats, bondvecs), start=1):
        lines.append(f"  NATIVE_Q0({i}) := {q[0]:.6f}")
        lines.append(f"  NATIVE_Q1({i}) := {q[1]:.6f}")
        lines.append(f"  NATIVE_Q2({i}) := {q[2]:.6f}")
        lines.append(f"  NATIVE_Q3({i}) := {q[3]:.6f}")
        lines.append(f"  NATIVE_BVX({i}) := {bv[0]:.6f}")
        lines.append(f"  NATIVE_BVY({i}) := {bv[1]:.6f}")
        lines.append(f"  NATIVE_BVZ({i}) := {bv[2]:.6f}")
    lines.append("")
    lines.append("  ! Initialize native contact matrix")
    lines.append("  DO I = 1, NRES")
    lines.append("    DO J = 1, NRES")
    lines.append("      NATIVE_CONTACT(I, J) := 0")
    lines.append("      CONTACT_INTER(I, J) := 0")
    lines.append("      NATIVE_R0(I, J) := 0.0")
    lines.append("    ENDDO")
    lines.append("  ENDDO")
    lines.append("")
    n_inter = 0
    if contacts:
        lines.append(f"  ! Go-like contacts (|i-j| >= MIN_SEP, native Cα-Cα < {cutoff_model:.6f} model units)")
        for i, j, d in contacts:
            lines.append(f"  NATIVE_CONTACT({i}, {j}) := 1")
            lines.append(f"  NATIVE_R0({i}, {j}) := {d:.6f}")
            lines.append(f"  NATIVE_CONTACT({j}, {i}) := 1")
            lines.append(f"  NATIVE_R0({j}, {i}) := {d:.6f}")
            if domains is not None:
                di = domain_of(i, domains)
                dj = domain_of(j, domains)
                if di is not None and dj is not None and di != dj:
                    lines.append(f"  CONTACT_INTER({i}, {j}) := 1")
                    lines.append(f"  CONTACT_INTER({j}, {i}) := 1")
                    n_inter += 1
    if domains is not None:
        lines.append("")
        lines.append(f"  ! Fold-then-dock: {n_inter} inter-domain contacts gated until DOCK_FROM")
    if register_entries:
        lines.append("")
        lines.append(f"  ! Cross-strand register torsions (k = {register_k:.4f})")
        for idx, (a, b, c, d, p0) in enumerate(register_entries, start=1):
            lines.append(f"  REG_A({idx}) := {a}")
            lines.append(f"  REG_B({idx}) := {b}")
            lines.append(f"  REG_C({idx}) := {c}")
            lines.append(f"  REG_D({idx}) := {d}")
            lines.append(f"  REG_K({idx}) := {register_k:.4f}")
            lines.append(f"  REG_P0({idx}) := {p0:.6f}")
    if cystine:
        lines.append("")
        lines.append("  ! Breakable cystine restraints (CYS_ON=0 = deleted disulfide)")
        for idx, (ci, cj, r0, on) in enumerate(cystine, start=1):
            lines.append(f"  CYS_I({idx}) := {ci}")
            lines.append(f"  CYS_J({idx}) := {cj}")
            lines.append(f"  CYS_R0({idx}) := {r0:.6f}")
            lines.append(f"  CYS_ON({idx}) := {on}")
    if mispair:
        lines.append("")
        lines.append("  ! Non-native disulfide mispairing restraints (per-pair K)")
        for idx, (mi, mj, r0, mk) in enumerate(mispair, start=1):
            lines.append(f"  MIS_I({idx}) := {mi}")
            lines.append(f"  MIS_J({idx}) := {mj}")
            lines.append(f"  MIS_R0({idx}) := {r0:.6f}")
            lines.append(f"  MIS_KK({idx}) := {mk:.4f}")
    lines.append("")
    lines.append("  RETURN")
    lines.append("END")
    return "\n".join(lines)


# ── register torsion loop generator ──────────────────────────────────
def gen_register_torsion_loop():
    """Return the inline register-torsion force loop for the main dynamics block."""
    return '''
  ! Cross-strand register torsions (chirality of native sheet packing)
  IF FRAME > EXTRA_TORSIONS_FROM THEN
    DO K = 1, NREG
      IA := REG_A(K)
      IB := REG_B(K)
      IC := REG_C(K)
      ID := REG_D(K)

      B1X := RES_X(IB) - RES_X(IA)
      B1Y := RES_Y(IB) - RES_Y(IA)
      B1Z := RES_Z(IB) - RES_Z(IA)
      B2X := RES_X(IC) - RES_X(IB)
      B2Y := RES_Y(IC) - RES_Y(IB)
      B2Z := RES_Z(IC) - RES_Z(IB)
      B3X := RES_X(ID) - RES_X(IC)
      B3Y := RES_Y(ID) - RES_Y(IC)
      B3Z := RES_Z(ID) - RES_Z(IC)

      N1X := B1Y*B2Z - B1Z*B2Y
      N1Y := B1Z*B2X - B1X*B2Z
      N1Z := B1X*B2Y - B1Y*B2X
      N2X := B2Y*B3Z - B2Z*B3Y
      N2Y := B2Z*B3X - B2X*B3Z
      N2Z := B2X*B3Y - B2Y*B3X

      N1MAG2 := N1X*N1X + N1Y*N1Y + N1Z*N1Z
      N2MAG2 := N2X*N2X + N2Y*N2Y + N2Z*N2Z
      B2MAG := SQRT(B2X*B2X + B2Y*B2Y + B2Z*B2Z)

      IF N1MAG2 > 1.0E-12 .AND. N2MAG2 > 1.0E-12 .AND. B2MAG > 1.0E-12 THEN
        N1MAG := SQRT(N1MAG2)
        N2MAG := SQRT(N2MAG2)
        PHI := ATAN2(B2MAG*(B1X*N2X + B1Y*N2Y + B1Z*N2Z), N1X*N2X + N1Y*N2Y + N1Z*N2Z)
        F := -2.0 * REG_K(K) * SIN(PHI - REG_P0(K))

        DPHI_DR1X := -B2MAG / N1MAG2 * N1X
        DPHI_DR1Y := -B2MAG / N1MAG2 * N1Y
        DPHI_DR1Z := -B2MAG / N1MAG2 * N1Z

        DPHI_DR4X := B2MAG / N2MAG2 * N2X
        DPHI_DR4Y := B2MAG / N2MAG2 * N2Y
        DPHI_DR4Z := B2MAG / N2MAG2 * N2Z

        B1DOT := B1X*B2X + B1Y*B2Y + B1Z*B2Z
        B3DOT := B3X*B2X + B3Y*B2Y + B3Z*B2Z
        SCALE_B2 := 1.0 / (B2MAG * B2MAG)
        SCALE_B1 := B1DOT * SCALE_B2
        SCALE_B3 := B3DOT * SCALE_B2

        DPHI_DR2X := -(1.0 + SCALE_B1) * DPHI_DR1X + SCALE_B3 * DPHI_DR4X
        DPHI_DR2Y := -(1.0 + SCALE_B1) * DPHI_DR1Y + SCALE_B3 * DPHI_DR4Y
        DPHI_DR2Z := -(1.0 + SCALE_B1) * DPHI_DR1Z + SCALE_B3 * DPHI_DR4Z

        DPHI_DR3X := -(DPHI_DR1X + DPHI_DR2X + DPHI_DR4X)
        DPHI_DR3Y := -(DPHI_DR1Y + DPHI_DR2Y + DPHI_DR4Y)
        DPHI_DR3Z := -(DPHI_DR1Z + DPHI_DR2Z + DPHI_DR4Z)

        RES_VX(IA) := RES_VX(IA) + F * DPHI_DR1X * DT * FORCE_SCALE
        RES_VY(IA) := RES_VY(IA) + F * DPHI_DR1Y * DT * FORCE_SCALE
        RES_VZ(IA) := RES_VZ(IA) + F * DPHI_DR1Z * DT * FORCE_SCALE

        RES_VX(IB) := RES_VX(IB) + F * DPHI_DR2X * DT * FORCE_SCALE
        RES_VY(IB) := RES_VY(IB) + F * DPHI_DR2Y * DT * FORCE_SCALE
        RES_VZ(IB) := RES_VZ(IB) + F * DPHI_DR2Z * DT * FORCE_SCALE

        RES_VX(IC) := RES_VX(IC) + F * DPHI_DR3X * DT * FORCE_SCALE
        RES_VY(IC) := RES_VY(IC) + F * DPHI_DR3Y * DT * FORCE_SCALE
        RES_VZ(IC) := RES_VZ(IC) + F * DPHI_DR3Z * DT * FORCE_SCALE

        RES_VX(ID) := RES_VX(ID) + F * DPHI_DR4X * DT * FORCE_SCALE
        RES_VY(ID) := RES_VY(ID) + F * DPHI_DR4Y * DT * FORCE_SCALE
        RES_VZ(ID) := RES_VZ(ID) + F * DPHI_DR4Z * DT * FORCE_SCALE
      ENDIF
    ENDDO
  ENDIF
'''


def gen_aromatic_loop():
    """Return the inline aromatic packing force loop.

    The Cβ positions are derived from current Cα plus a fixed native offset.
    The optimal CB-CB distance for each pair is the native CB-CB distance,
    so the force reinforces native packing. Aromatic strength is residue-type
    dependent (Phe < Tyr < Trp) to distinguish side-chain mutations.
    """
    return '''
  ! Aromatic packing (Cβ-derived side-chain centers)
  DO I = 1, NRES-4
    IF AROMATIC_MULT(I) > 0.0 THEN
      CBIX := RES_X(I) + CB_OFF_X(I)
      CBIY := RES_Y(I) + CB_OFF_Y(I)
      CBIZ := RES_Z(I) + CB_OFF_Z(I)
      NBIX := NATIVE_X(I) + CB_OFF_X(I)
      NBIY := NATIVE_Y(I) + CB_OFF_Y(I)
      NBIZ := NATIVE_Z(I) + CB_OFF_Z(I)
      DO J = I+4, NRES
        CBJX := RES_X(J) + CB_OFF_X(J)
        CBJY := RES_Y(J) + CB_OFF_Y(J)
        CBJZ := RES_Z(J) + CB_OFF_Z(J)
        NBJX := NATIVE_X(J) + CB_OFF_X(J)
        NBJY := NATIVE_Y(J) + CB_OFF_Y(J)
        NBJZ := NATIVE_Z(J) + CB_OFF_Z(J)
        DX := CBIX - CBJX
        DY := CBIY - CBJY
        DZ := CBIZ - CBJZ
        D := SQRT(DX*DX + DY*DY + DZ*DZ)
        D0X := NBIX - NBJX
        D0Y := NBIY - NBJY
        D0Z := NBIZ - NBJZ
        D0 := SQRT(D0X*D0X + D0Y*D0Y + D0Z*D0Z)
        IF D > 0.0 .AND. D0 > 0.0 .AND. D < 8.0 THEN
          IF AROMATIC_MULT(J) > 0.0 THEN
            MULT := AROMATIC_MULT(I) * AROMATIC_MULT(J)
          ELSEIF RES_HYDRO(J) > 0.5 THEN
            MULT := 0.3 * AROMATIC_MULT(I)
          ELSE
            MULT := 0.0
          ENDIF
          IF MULT > 0.0 THEN
            FM := -AROM_STRENGTH * MULT * EXP(-AROM_ALPHA * (D - D0)**2)
            RES_VX(I) := RES_VX(I) + FM * DX / D * DT * FORCE_SCALE
            RES_VY(I) := RES_VY(I) + FM * DY / D * DT * FORCE_SCALE
            RES_VZ(I) := RES_VZ(I) + FM * DZ / D * DT * FORCE_SCALE
            RES_VX(J) := RES_VX(J) - FM * DX / D * DT * FORCE_SCALE
            RES_VY(J) := RES_VY(J) - FM * DY / D * DT * FORCE_SCALE
            RES_VZ(J) := RES_VZ(J) - FM * DZ / D * DT * FORCE_SCALE
          ENDIF
        ENDIF
      ENDDO
    ENDIF
  ENDDO
'''


# ── patch the Trp-cage template ────────────────────────────────────
def patch_template(template_path, nres, init_chain, init_native, cutoff_model, name,
                   hb_cap=2, hydro_strength=None, native_k=None, tors_k=None, maxframe=4000,
                   register_torsions=True, register_from=1200, register_k=0.5,
                   register_entries=None, quench_frame=None, seed=None,
                   cb_offsets=None, aromatic_mult=None, dock_from=None,
                   scaled_schedule=False, pulse_amp=None, pulse_omega=None,
                   mc_every=None, mc_angle=None, mc_trans=None, mc_temp=None, domains=None,
                   frame_k=None, frame_pos_k=None, css_k=None, ncyspair=None,
                   mis_k=None, nmispair=None, chain_break=None, chain_break2=None, chain_break3=None,
                   vmax=None, thermal_floor=None):
    with open(template_path) as f:
        src = f.read()

    # 1. NRES parameter
    src = re.sub(r'PARAMETER INTEGER :: NRES = \d+',
                 f'PARAMETER INTEGER :: NRES = {nres}',
                 src)

    # 2. Static array sizes
    def repl_size(m):
        full = m.group(0)
        prefix = full.split('(')[0]
        # Keep HB_I/HB_J/MAXHB etc. untouched.
        if prefix in ('HB_I', 'HB_J', 'N44'):
            return full
        if prefix in ('NATIVE_CONTACT', 'NATIVE_R0', 'HBOND_MATRIX', 'CONTACT_INTER'):
            return f'{prefix}({nres}, {nres})'
        return f'{prefix}({nres})'

    src = re.sub(r'RES_(X|Y|Z|VX|VY|VZ|THETA|OMEGA|ANGK|ANGT0|TORSK|TORSP0|HYDRO|Q0|Q1|Q2|Q3|WX|WY|WZ)\(\d+\)',
                 repl_size, src)
    src = re.sub(r'CB_OFF_(X|Y|Z)\(\d+\)', repl_size, src)
    src = re.sub(r'AROMATIC_MULT\(\d+\)', repl_size, src)
    src = re.sub(r'MC_O(X|Y|Z)\(\d+\)', repl_size, src)
    src = re.sub(r'NATIVE_(X|Y|Z)\(\d+\)', repl_size, src)
    src = re.sub(r'NATIVE_(Q0|Q1|Q2|Q3)\(\d+\)', repl_size, src)
    src = re.sub(r'NATIVE_BV(X|Y|Z)\(\d+\)', repl_size, src)
    src = re.sub(r'(NATIVE_CONTACT)\(\d+, \d+\)', repl_size, src)
    src = re.sub(r'(CONTACT_INTER)\(\d+, \d+\)', repl_size, src)
    src = re.sub(r'(NATIVE_R0)\(\d+, \d+\)', repl_size, src)
    src = re.sub(r'(HBOND_MATRIX)\(\d+, \d+\)', repl_size, src)

    # 3. NATIVE_CUTOFF parameter (informational)
    src = re.sub(r'PARAMETER REAL :: NATIVE_CUTOFF = [0-9.eE\-]+',
                 f'PARAMETER REAL :: NATIVE_CUTOFF = {cutoff_model:.6f}',
                 src)

    # 4. Optional parameter overrides
    if hb_cap != 2:
        src = re.sub(r'PARAMETER INTEGER :: HB_CAP = \d+',
                     f'PARAMETER INTEGER :: HB_CAP = {hb_cap}', src)
    if hydro_strength is not None:
        src = re.sub(r'PARAMETER REAL :: HYDRO_STRENGTH = [0-9.eE\-]+',
                     f'PARAMETER REAL :: HYDRO_STRENGTH = {hydro_strength:.4f}', src)
    if native_k is not None:
        src = re.sub(r'PARAMETER REAL :: NATIVE_K = [0-9.eE\-]+',
                     f'PARAMETER REAL :: NATIVE_K = {native_k:.4f}', src)
    if tors_k is not None:
        src = re.sub(r'RES_TORSK\(I\) := 0.6000',
                     f'RES_TORSK(I) := {tors_k:.4f}', src)
    if seed is not None:
        src = re.sub(r'PARAMETER REAL :: SEED = [0-9.eE\-]+',
                     f'PARAMETER REAL :: SEED = {seed:.1f}', src)
    if css_k is not None:
        src = re.sub(r'PARAMETER REAL :: CSS_K = [0-9.eE\-]+',
                     f'PARAMETER REAL :: CSS_K = {css_k:.4f}', src)
    if ncyspair is not None:
        src = re.sub(r'PARAMETER INTEGER :: NCYSPAIR = \d+',
                     f'PARAMETER INTEGER :: NCYSPAIR = {ncyspair}', src)
    if mis_k is not None:
        src = re.sub(r'PARAMETER REAL :: MIS_K = [0-9.eE\-]+',
                     f'PARAMETER REAL :: MIS_K = {mis_k:.4f}', src)
    if nmispair is not None:
        src = re.sub(r'PARAMETER INTEGER :: NMISPAIR = \d+',
                     f'PARAMETER INTEGER :: NMISPAIR = {nmispair}', src)
    if chain_break is not None:
        src = re.sub(r'PARAMETER INTEGER :: CHAIN_BREAK = \d+',
                     f'PARAMETER INTEGER :: CHAIN_BREAK = {chain_break}', src)
    if chain_break2 is not None:
        src = re.sub(r'PARAMETER INTEGER :: CHAIN_BREAK2 = \d+',
                     f'PARAMETER INTEGER :: CHAIN_BREAK2 = {chain_break2}', src)
    if chain_break3 is not None:
        src = re.sub(r'PARAMETER INTEGER :: CHAIN_BREAK3 = \d+',
                     f'PARAMETER INTEGER :: CHAIN_BREAK3 = {chain_break3}', src)
    if vmax is not None:
        src = re.sub(r'PARAMETER REAL :: VMAX = [0-9.eE\-]+',
                     f'PARAMETER REAL :: VMAX = {vmax:.4f}', src)

    if maxframe != 4000:
        src = re.sub(r'PARAMETER INTEGER :: MAXFRAME = \d+',
                     f'PARAMETER INTEGER :: MAXFRAME = {maxframe}', src)

    # 4a. Ultrasonic pulse (mechanical trap rescue)
    if pulse_amp is not None:
        src = re.sub(r'PARAMETER REAL :: PULSE_AMP = [0-9.eE\-]+',
                     f'PARAMETER REAL :: PULSE_AMP = {pulse_amp}', src)
    if pulse_omega is not None:
        src = re.sub(r'PARAMETER REAL :: PULSE_OMEGA = [0-9.eE\-]+',
                     f'PARAMETER REAL :: PULSE_OMEGA = {pulse_omega}', src)

    # 4a2. Domain rigid-body quaternion MC
    if mc_every is not None:
        src = re.sub(r'PARAMETER INTEGER :: MC_EVERY = \d+',
                     f'PARAMETER INTEGER :: MC_EVERY = {mc_every}', src)
        if mc_angle is not None:
            src = re.sub(r'PARAMETER REAL :: MC_ANGLE = [0-9.eE\-]+',
                         f'PARAMETER REAL :: MC_ANGLE = {mc_angle}', src)
        if mc_temp is not None:
            src = re.sub(r'PARAMETER REAL :: MC_TEMP = [0-9.eE\-]+',
                         f'PARAMETER REAL :: MC_TEMP = {mc_temp}', src)
        if mc_trans is not None:
            src = re.sub(r'PARAMETER REAL :: MC_TRANS = [0-9.eE\-]+',
                         f'PARAMETER REAL :: MC_TRANS = {mc_trans}', src)
    if domains is not None:
        src = re.sub(r'PARAMETER INTEGER :: NDOM = \d+',
                     f'PARAMETER INTEGER :: NDOM = {len(domains)}', src)
        dom_lines = ["  ! Domain table for rigid-body MC"]
        for k, (a, b) in enumerate(domains, start=1):
            dom_lines.append(f"  DOM_BEG({k}) := {a}")
            dom_lines.append(f"  DOM_END({k}) := {b}")
    else:
        dom_lines = ["  ! Single domain: MC move is inert (whole-chain rotation)",
                     "  DOM_BEG(1) := 1",
                     "  DOM_END(1) := NRES"]
    src = src.replace('! __MC_DOMAIN_INIT__', "\n".join(dom_lines))

    # 4a3. Oriented-ribbon dynamics
    if frame_k is not None:
        src = re.sub(r'PARAMETER REAL :: FRAME_K = [0-9.eE\-]+',
                     f'PARAMETER REAL :: FRAME_K = {frame_k}', src)
    if frame_pos_k is not None:
        src = re.sub(r'PARAMETER REAL :: FRAME_POS_K = [0-9.eE\-]+',
                     f'PARAMETER REAL :: FRAME_POS_K = {frame_pos_k}', src)

    # 4b. Fold-then-dock staging
    if dock_from is not None:
        src = re.sub(r'PARAMETER INTEGER :: DOCK_FROM = \d+',
                     f'PARAMETER INTEGER :: DOCK_FROM = {dock_from}', src)

    # 4c. Scaled thermal schedule (cycles span first half of MAXFRAME)
    if scaled_schedule:
        src = re.sub(r'PARAMETER INTEGER :: SCHEDULE_SCALED = \d+',
                     'PARAMETER INTEGER :: SCHEDULE_SCALED = 1', src)

    # 5. Register torsion infrastructure
    nreg = len(register_entries) if register_entries else 0
    if register_torsions and nreg > 0:
        maxreg = max(nreg, 1)
        reg_params = [
            "",
            "! ── Cross-strand register torsion (β-sheet chirality) ─────────",
            f"PARAMETER INTEGER :: MAXREG = {maxreg}",
            f"PARAMETER INTEGER :: NREG = {nreg}",
            f"PARAMETER INTEGER :: EXTRA_TORSIONS_FROM = {register_from}",
            "",
        ]
        reg_decls = [
            "",
            "STATIC INTEGER :: REG_A(MAXREG)",
            "STATIC INTEGER :: REG_B(MAXREG)",
            "STATIC INTEGER :: REG_C(MAXREG)",
            "STATIC INTEGER :: REG_D(MAXREG)",
            "STATIC REAL :: REG_K(MAXREG)",
            "STATIC REAL :: REG_P0(MAXREG)",
            "STATIC INTEGER :: IA, IB, IC, ID",
            "",
        ]
        src = src.replace('! __REG_TORSION_PARAMS__', "\n".join(reg_params))
        src = src.replace('! __REG_TORSION_DECLS__', "\n".join(reg_decls))
        src = src.replace('! __REG_TORSION_INIT__', "  ! Register torsions initialized in INIT_NATIVE\n")
        src = src.replace('! __REG_TORSION_LOOP__', gen_register_torsion_loop())
    else:
        src = src.replace('! __REG_TORSION_PARAMS__', "")
        src = src.replace('! __REG_TORSION_DECLS__', "")
        src = src.replace('! __REG_TORSION_INIT__', "")
        src = src.replace('! __REG_TORSION_LOOP__', "")

    # 5b. Cβ / aromatic side-chain infrastructure
    use_cb = cb_offsets is not None and aromatic_mult is not None
    if use_cb:
        cb_params = [
            "",
            "! ── Aromatic packing (Cβ-derived side-chain centers) ─────────",
            "PARAMETER REAL :: AROM_STRENGTH = 0.05",
            "PARAMETER REAL :: AROM_ALPHA = 0.5",
            "",
        ]
        cb_decls = [
            "",
            "STATIC REAL :: CB_OFF_X(36)",
            "STATIC REAL :: CB_OFF_Y(36)",
            "STATIC REAL :: CB_OFF_Z(36)",
            "STATIC REAL :: AROMATIC_MULT(36)",
            "STATIC REAL :: CBIX, CBIY, CBIZ, CBJX, CBJY, CBJZ",
            "STATIC REAL :: NBIX, NBIY, NBIZ, NBJX, NBJY, NBJZ",
            "STATIC REAL :: D0X, D0Y, D0Z, D0, MULT",
            "",
        ]
        src = src.replace('! __CB_PARAMS__', "\n".join(cb_params))
        src = src.replace('! __CB_DECLS__', "\n".join(cb_decls))
        src = src.replace('! __AROM_LOOP__', gen_aromatic_loop())
        # Array declarations inserted above carry the literal placeholder size 36;
        # resize them to the actual NRES.
        src = re.sub(r'CB_OFF_(X|Y|Z)\(\d+\)', repl_size, src)
        src = re.sub(r'AROMATIC_MULT\(\d+\)', repl_size, src)
    else:
        src = src.replace('! __CB_PARAMS__', "")
        src = src.replace('! __CB_DECLS__', "")
        src = src.replace('! __AROM_LOOP__', "")

    # 6. Quench tail
    if thermal_floor is not None and quench_frame is not None:
        quench_code = [
            f"  ! Sustained thermal floor: hold noise at {thermal_floor} after frame {quench_frame}",
            f"  IF FRAME > {quench_frame} THEN",
            f"    THERMAL_CURRENT := {thermal_floor}",
            "  ENDIF",
        ]
        src = src.replace('! __QUENCH__', "\n".join(quench_code))
    elif quench_frame is not None:
        quench_code = [
            "",
            f"  ! Quench tail: zero thermal noise after frame {quench_frame}",
            f"  IF FRAME > {quench_frame} THEN",
            "    THERMAL_CURRENT := 0.0",
            "  ENDIF",
            "",
        ]
        src = src.replace('! __QUENCH__', "\n".join(quench_code))
    else:
        src = src.replace('! __QUENCH__', "")

    # 7. Header comment
    src = re.sub(r'! WAVEFORM_TRPCAGE - Trp-cage miniprotein \(PDB 1L2Y\) with native RMSD',
                 f'! WAVEFORM_{name.upper()} - {name} protein variant with native RMSD',
                 src)
    src = re.sub(r'! 20-residue protein:.*',
                 f'! {nres}-residue protein variant',
                 src)

    # 8. Replace INIT_CHAIN subroutine
    src = re.sub(r'SUBROUTINE INIT_CHAIN\(\).*?END\s*\n(?=SUBROUTINE INIT_NATIVE)',
                 init_chain + '\n', src, flags=re.DOTALL)

    # 9. Replace INIT_NATIVE subroutine
    src = re.sub(r'SUBROUTINE INIT_NATIVE\(\).*?END\s*\n(?=SUBROUTINE UPDATE_THERMAL)',
                 init_native + '\n', src, flags=re.DOTALL)

    return src


# ── main driver ─────────────────────────────────────────────────────
def generate_variant(name, json_path, pdb_path, chain, output_path,
                     template_path, min_sep=4, phys_cutoff=6.5,
                     hb_cap=2, hydro_strength=None, native_k=None, tors_k=None, maxframe=4000,
                     register_torsions=True, register_from=1200, register_k=0.5,
                     quench_frame=None, seed=None, use_cb=False,
                     domains=None, dock_from=None, scaled_schedule=False,
                     pulse_amp=None, pulse_omega=None,
                     mc_every=None, mc_angle=None, mc_trans=None, mc_temp=None, axial_init=False,
                     frame_k=None, frame_pos_k=None,
                     cystine=None, cystine_off=None, css_k=None, mutate=None,
                     mispair=None, mis_k=None, mis_r0=None, chain_break=None, chain_sep=None,
                     vmax=None, thermal_floor=None):
    coords, mean_ca_ca, cb_coords, res_names = parse_ca_json(json_path)
    if mean_ca_ca is None:
        # Compute from the JSON coordinates if not present
        dsum = 0.0
        for i in range(len(coords) - 1):
            p = (coords[i]['x'], coords[i]['y'], coords[i]['z'])
            q = (coords[i+1]['x'], coords[i+1]['y'], coords[i+1]['z'])
            dsum += vec_len(vec_sub(q, p))
        mean_ca_ca = dsum / (len(coords) - 1)

    nres = len(coords)
    pdb_resnums = [c['pdb_res'] for c in coords]
    seq3 = parse_pdb_sequence(pdb_path, chain, pdb_resnums)
    seq1 = [one_letter(s) for s in seq3]

    # Point mutations: "72:Y" (1-based chain index). Geometry/contacts unchanged
    # (Go map is native-derived); only sequence-dependent terms (hydrophobicity) change.
    if mutate:
        for mut in mutate.split(','):
            pos_s, aa = mut.strip().split(':')
            pos = int(pos_s)
            if not (1 <= pos <= len(seq1)):
                raise ValueError(f"--mutate position {pos} out of range 1..{len(seq1)}")
            seq1[pos - 1] = aa.upper()

    hydro_values = [HYDRO.get(s, 0.0) for s in seq1]

    scale, scaled, scaled_cb = scale_and_geometry(coords, mean_ca_ca, cb_coords)

    # Breakable cystine restraints: R0 = scaled native Cα–Cα distance
    cystine_data = None
    if cystine:
        off = set(parse_pair_list_arg(cystine_off) or [])
        cystine_data = []
        for (ci, cj) in cystine:
            if not (1 <= ci <= nres and 1 <= cj <= nres):
                raise ValueError(f"--cystine pair {ci}-{cj} out of range 1..{nres}")
            r0 = vec_len(vec_sub(scaled[ci - 1], scaled[cj - 1]))
            on = 0 if (ci, cj) in off or (cj, ci) in off else 1
            cystine_data.append((ci, cj, r0, on))
        if css_k is None:
            css_k = 0.5

    # Mispairing restraints: uniform R0 (generic disulfide Cα–Cα distance), per-pair K
    mispair_data = None
    if mispair:
        r0m = mis_r0 if mis_r0 is not None else 2.0
        k_default = mis_k if mis_k is not None else 0.25
        mispair_data = []
        for entry in mispair:
            mi, mj = entry[0], entry[1]
            mk = entry[2] if entry[2] is not None else k_default
            if not (1 <= mi <= nres and 1 <= mj <= nres):
                raise ValueError(f"--mispair pair {mi}-{mj} out of range 1..{nres}")
            mispair_data.append((mi, mj, r0m, mk))

    # Native angle targets
    ang_t0 = [0.0] * nres
    for i in range(1, nres - 1):
        ang_t0[i] = native_angle(scaled[i-1], scaled[i], scaled[i+1])

    # Native torsion targets
    tors_p0 = [0.0] * nres
    for i in range(1, nres - 2):
        tors_p0[i] = native_dihedral(scaled[i-1], scaled[i], scaled[i+1], scaled[i+2])

    contacts, cutoff_model = compute_native_contacts(scaled, nres, min_sep, phys_cutoff, scale)

    # Multi-chain: no Go contacts across any break (quaternary placement is arbitrary),
    # neutral backbone targets at each junction (template loops skip these indices anyway)
    breaks = []
    if chain_break is not None:
        breaks = list(chain_break) if isinstance(chain_break, (list, tuple)) else [chain_break]
    for cb in breaks:
        if not (1 <= cb < nres):
            raise ValueError(f"--chain-break {cb} out of range 1..{nres-1}")
        contacts = [(i, j, d) for (i, j, d) in contacts
                    if not (i <= cb < j)]
        ang_t0[cb - 1] = 0.0   # angle at CB (0-based index CB-1)
        ang_t0[cb] = 0.0       # angle at CB+1
        for ti in (cb - 2, cb - 1, cb):
            if 1 <= ti + 1 <= nres - 2:
                tors_p0[ti] = 0.0

    domain_intervals = parse_domains_arg(domains, nres)
    if domain_intervals is not None and dock_from is None:
        dock_from = int(0.5 * maxframe)
    if dock_from is not None and domain_intervals is None:
        raise ValueError("--dock-from requires --domains")

    if register_torsions:
        register_entries = compute_register_torsions(scaled, contacts, nres)
    else:
        register_entries = []

    # Cβ offsets and aromatic multipliers
    cb_offsets = None
    aromatic_mult = None
    if use_cb and scaled_cb is not None and res_names is not None:
        cb_offsets = []
        aromatic_mult = []
        for i in range(nres):
            ca = scaled[i]
            cb = scaled_cb[i]
            cb_offsets.append((cb[0] - ca[0], cb[1] - ca[1], cb[2] - ca[2]))
        for rn in res_names:
            r = rn.strip().upper()
            if r == 'PHE':
                aromatic_mult.append(0.2)
            elif r == 'TYR':
                aromatic_mult.append(0.5)
            elif r == 'TRP':
                aromatic_mult.append(1.0)
            else:
                aromatic_mult.append(0.0)

    domain_anchors = None
    if breaks:
        # each additional chain starts at a separated point, not continuous with
        # the previous chain's tail; chains 2/3 placed on a triangle of side `sep`
        sep = chain_sep if chain_sep is not None else 12.0
        anchor_pts = [(10.0 + sep, 10.0, 10.0),
                      (10.0 + sep / 2.0, 10.0 + 0.8660254 * sep, 10.0),
                      (10.0 + sep / 2.0, 10.0 + 0.2886751 * sep, 10.0 + 0.8164966 * sep)]
        domain_anchors = {}
        for k, cb in enumerate(breaks):
            domain_anchors[cb + 1] = anchor_pts[k % len(anchor_pts)]
    if axial_init:
        if domain_intervals is None:
            raise ValueError("--axial-init requires --domains")
        domain_anchors = {}
        for a, b in domain_intervals:
            seg = scaled[a-1:b]
            domain_anchors[a] = (sum(c[0] for c in seg)/len(seg),
                                 sum(c[1] for c in seg)/len(seg),
                                 sum(c[2] for c in seg)/len(seg))
    init_chain = gen_init_chain(nres, seq1, hydro_values, ang_t0, tors_p0, tors_k=tors_k if tors_k is not None else 0.6000,
                                cb_offsets=cb_offsets, aromatic_mult=aromatic_mult,
                                domain_anchors=domain_anchors)
    init_native = gen_init_native(nres, scaled, contacts, scale, cutoff_model,
                                register_entries=register_entries, register_k=register_k,
                                domains=domain_intervals, cystine=cystine_data,
                                mispair=mispair_data, chain_break=breaks if breaks else None)

    if quench_frame is None:
        quench_frame = int(0.8 * maxframe)

    src = patch_template(template_path, nres, init_chain, init_native, cutoff_model, name,
                         hb_cap=hb_cap, hydro_strength=hydro_strength,
                         native_k=native_k, tors_k=tors_k, maxframe=maxframe,
                         register_torsions=register_torsions, register_from=register_from,
                         register_k=register_k, register_entries=register_entries,
                         quench_frame=quench_frame, seed=seed,
                         cb_offsets=cb_offsets, aromatic_mult=aromatic_mult,
                         dock_from=dock_from, scaled_schedule=scaled_schedule,
                         pulse_amp=pulse_amp, pulse_omega=pulse_omega,
                         mc_every=mc_every, mc_angle=mc_angle, mc_trans=mc_trans, mc_temp=mc_temp, domains=domain_intervals,
                         frame_k=frame_k, frame_pos_k=frame_pos_k,
                         css_k=css_k, ncyspair=len(cystine_data) if cystine_data else None,
                         mis_k=mis_k, nmispair=len(mispair_data) if mispair_data else None,
                         chain_break=breaks[0] if breaks else None,
                         chain_break2=breaks[1] if len(breaks) > 1 else None,
                         chain_break3=breaks[2] if len(breaks) > 2 else None,
                         vmax=vmax, thermal_floor=thermal_floor)

    with open(output_path, 'w') as f:
        f.write(src)

    n_inter = 0
    if domain_intervals is not None:
        for i, j, _ in contacts:
            di, dj = domain_of(i, domain_intervals), domain_of(j, domain_intervals)
            if di is not None and dj is not None and di != dj:
                n_inter += 1

    print(f"Generated {output_path}: {nres} residues, scale={scale:.6f}, "
          f"contacts={len(contacts)}, register_torsions={len(register_entries)}, cutoff={cutoff_model:.6f} model units"
          + (f", cb_offsets={len(cb_offsets)}" if cb_offsets else "")
          + (f", domains={domain_intervals}, inter_contacts={n_inter}, dock_from={dock_from}"
             if domain_intervals is not None else ""))
    return {
        'name': name, 'nres': nres, 'scale': scale,
        'contacts': contacts, 'cutoff_model': cutoff_model,
        'seq1': seq1, 'register_entries': register_entries,
        'domains': domain_intervals, 'dock_from': dock_from, 'inter_contacts': n_inter,
    }


def main():
    parser = argparse.ArgumentParser(description='Generate protein .ergo variants from Trp-cage template')
    parser.add_argument('--name', required=True)
    parser.add_argument('--json', required=True)
    parser.add_argument('--pdb', required=True)
    parser.add_argument('--chain', default='A')
    parser.add_argument('--output', required=True)
    parser.add_argument('--template',
                        default=os.path.join(os.path.dirname(__file__),
                                             'waveform_template.ergo'))
    parser.add_argument('--min-sep', type=int, default=4)
    parser.add_argument('--cutoff', type=float, default=6.5)
    parser.add_argument('--hb-cap', type=int, default=2)
    parser.add_argument('--hydro-strength', type=float, default=None)
    parser.add_argument('--native-k', type=float, default=None)
    parser.add_argument('--tors-k', type=float, default=None)
    parser.add_argument('--maxframe', type=int, default=4000)
    parser.add_argument('--no-register', action='store_true', help='Disable cross-strand register torsions')
    parser.add_argument('--register-from', type=int, default=1200)
    parser.add_argument('--register-k', type=float, default=0.5)
    parser.add_argument('--quench-frame', type=int, default=None)
    parser.add_argument('--seed', type=float, default=None, help='Override SEED parameter')
    parser.add_argument('--use-cb', action='store_true', help='Enable Cβ offsets and aromatic packing term')
    parser.add_argument('--domains', default=None,
                        help="Domain boundaries: '1-98,99-136' or JSON from detect_domains.py. "
                             "Inter-domain Go contacts are gated until --dock-from.")
    parser.add_argument('--dock-from', type=int, default=None,
                        help='Frame at which inter-domain contacts activate (default 0.5*maxframe '
                             'when --domains is given)')
    parser.add_argument('--scaled-schedule', action='store_true',
                        help='Thermal cycles span first half of MAXFRAME instead of frames 0-1200')
    parser.add_argument('--pulse-amp', type=float, default=None,
                        help='Ultrasonic pulse amplitude (0/absent = off; certified: 0.05)')
    parser.add_argument('--pulse-omega', type=float, default=None,
                        help='Ultrasonic pulse frequency (certified: 0.002, period ~3100 frames)')
    parser.add_argument('--mc-every', type=int, default=None,
                        help='Domain rigid-body quaternion MC move every N frames (requires --domains)')
    parser.add_argument('--mc-angle', type=float, default=None,
                        help='MC max rotation angle in radians (default template 0.08)')
    parser.add_argument('--mc-trans', type=float, default=None,
                        help='MC max translation per axis in model units (default template 0.3)')
    parser.add_argument('--mc-temp', type=float, default=None,
                        help='Metropolis temperature for MC moves (anneals to 0 by quench; 0 = greedy)')
    parser.add_argument('--axial-init', action='store_true',
                        help='Anchor each domain start at its native COM (requires --domains)')
    parser.add_argument('--frame-k', type=float, default=None,
                        help='Orientation alignment torque strength (Cosserat ribbon; 0 = off)')
    parser.add_argument('--frame-pos-k', type=float, default=None,
                        help='Orientation-to-position coupling strength (0 = off)')
    parser.add_argument('--cystine', default=None,
                        help="Breakable cystine pairs, 1-based chain indices: '71-76,72-7,85-19'. "
                             "R0 taken from scaled native geometry; enables CSS_K (default 0.5).")
    parser.add_argument('--cystine-off', default=None,
                        help="Pairs to delete (CYS_ON=0), e.g. '72-7' for Akita CysA7Tyr")
    parser.add_argument('--css-k', type=float, default=None,
                        help='Cystine harmonic strength (default 0.5 when --cystine given)')
    parser.add_argument('--mutate', default=None,
                        help="Point mutations, e.g. '72:Y'. Sequence-dependent terms only.")
    parser.add_argument('--mispair', default=None,
                        help="Non-native disulfide pairs competing with native: '7-76,7-85'")
    parser.add_argument('--mis-k', type=float, default=None,
                        help='Mispairing harmonic strength (default 0.25 when --mispair given)')
    parser.add_argument('--mis-r0', type=float, default=None,
                        help='Mispairing target distance, model units (default 2.0)')
    parser.add_argument('--chain-break', default=None,
                        help="Residue(s) ending each chain: '86' (dimer) or '86,172' (trimer). "
                             'Each additional chain starts at a separated point')
    parser.add_argument('--chain-sep', type=float, default=None,
                        help='Chain 2 start separation in model units (default 12.0)')
    parser.add_argument('--thermal-floor', type=float, default=None,
                        help='Sustained thermal noise floor after quench frame (default: quench to 0.0)')
    parser.add_argument('--vmax', type=float, default=None,
                        help='Velocity CFL bound: per-residue speed limit (certified 25.0; 0/absent = off)')
    args = parser.parse_args()
    if args.mc_every is not None and args.domains is None:
        parser.error('--mc-every requires --domains')
    generate_variant(args.name, args.json, args.pdb, args.chain, args.output,
                     args.template, args.min_sep, args.cutoff,
                     hb_cap=args.hb_cap,
                     hydro_strength=args.hydro_strength,
                     native_k=args.native_k,
                     tors_k=args.tors_k,
                     maxframe=args.maxframe,
                     register_torsions=not args.no_register,
                     register_from=args.register_from,
                     register_k=args.register_k,
                     quench_frame=args.quench_frame,
                     seed=args.seed,
                     use_cb=args.use_cb,
                     domains=args.domains,
                     dock_from=args.dock_from,
                     scaled_schedule=args.scaled_schedule,
                     pulse_amp=args.pulse_amp,
                     pulse_omega=args.pulse_omega,
                     mc_every=args.mc_every,
                     mc_angle=args.mc_angle,
                     mc_trans=args.mc_trans,
                     mc_temp=args.mc_temp,
                     axial_init=args.axial_init,
                     frame_k=args.frame_k, frame_pos_k=args.frame_pos_k,
                     cystine=parse_pair_list_arg(args.cystine),
                     cystine_off=args.cystine_off,
                     css_k=args.css_k,
                     mutate=args.mutate,
                     mispair=parse_mispair_arg(args.mispair),
                     mis_k=args.mis_k,
                     mis_r0=args.mis_r0,
                     chain_break=[int(x) for x in args.chain_break.split(',')] if args.chain_break else None,
                     chain_sep=args.chain_sep,
                     vmax=args.vmax, thermal_floor=args.thermal_floor)


if __name__ == '__main__':
    main()
