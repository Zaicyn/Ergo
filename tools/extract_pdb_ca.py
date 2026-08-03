#!/usr/bin/env python3
"""extract_pdb_ca.py

Extract C-alpha and C-beta coordinates from a PDB file and emit the JSON
format used by generate_protein_ergo.py.

Usage:
    python3 tools/extract_pdb_ca.py pdb/1L2Y.pdb --chain A -o pdb/1L2Y_ca.json

For NMR entries with multiple models, only the first model is used.
"""

import argparse
import json
import math
import sys


def extract_residue_atoms(pdb_path, chain_id):
    """Return dict mapping (ch, res_seq) -> {atom_name: (x,y,z), res_name}."""
    residues = {}
    in_model = True
    model_count = 0

    with open(pdb_path) as f:
        for line in f:
            if line.startswith('MODEL'):
                model_count += 1
                if model_count > 1:
                    in_model = False
                continue
            if line.startswith('ENDMDL'):
                in_model = False
                continue
            if not in_model:
                continue
            if not (line.startswith('ATOM') or line.startswith('HETATM')):
                continue
            atom = line[12:16].strip()
            ch = line[21]
            if chain_id and ch != chain_id:
                continue
            res_name = line[17:20].strip()
            try:
                res_seq = int(line[22:26].strip())
            except ValueError:
                continue
            try:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
            except ValueError:
                continue
            key = (ch, res_seq)
            if key not in residues:
                residues[key] = {'res_name': res_name, 'atoms': {}}
            # Keep first occurrence of each atom name
            if atom not in residues[key]['atoms']:
                residues[key]['atoms'][atom] = (x, y, z)

    return residues


def vec_sub(a, b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])


def vec_len(v):
    return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])


def vec_cross(a, b):
    return (a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])


def vec_scale(v, s):
    return (v[0]*s, v[1]*s, v[2]*s)


def vec_add(a, b):
    return (a[0]+b[0], a[1]+b[1], a[2]+b[2])


def estimate_cb(ca, n, c):
    """Estimate a CB position from CA, N, C using the CHARMM-consistent
    pseudo-CB construction: CB is roughly perpendicular to the N-CA-C plane,
    ~1.5 Å from CA, on the side opposite to the backbone carbonyl."""
    a = vec_sub(n, ca)
    b = vec_sub(c, ca)
    la = vec_len(a)
    lb = vec_len(b)
    if la == 0.0 or lb == 0.0:
        return ca
    a = vec_scale(a, 1.0 / la)
    b = vec_scale(b, 1.0 / lb)
    perp = vec_cross(a, b)
    lp = vec_len(perp)
    if lp == 0.0:
        return ca
    perp = vec_scale(perp, 1.0 / lp)
    # Put CB in the plane opposite the carbonyl direction, ~1.5 Å from CA
    return vec_add(ca, vec_scale(perp, 1.5))


def extract_ca_cb(pdb_path, chain_id):
    """Return ordered list of (seq_index, pdb_resnum, res_name, ca, cb),
    where ca and cb are (x,y,z) tuples."""
    residues = extract_residue_atoms(pdb_path, chain_id)
    rows = []
    for (ch, res_seq), data in sorted(residues.items(), key=lambda kv: kv[0][1]):
        atoms = data['atoms']
        res_name = data['res_name']
        if 'CA' not in atoms:
            continue
        ca = atoms['CA']
        if 'CB' in atoms:
            cb = atoms['CB']
        elif res_name == 'GLY':
            cb = ca
        else:
            # Missing CB: estimate from backbone if N and C are present
            n = atoms.get('N', ca)
            c = atoms.get('C', ca)
            cb = estimate_cb(ca, n, c)
        rows.append((len(rows) + 1, res_seq, res_name, ca, cb))
    return rows


def mean_ca_ca_dist(coords):
    """Average distance between consecutive C-alpha coordinates."""
    if len(coords) < 2:
        return 0.0
    total = 0.0
    for i in range(len(coords) - 1):
        dx = coords[i+1][0] - coords[i][0]
        dy = coords[i+1][1] - coords[i][1]
        dz = coords[i+1][2] - coords[i][2]
        total += math.sqrt(dx*dx + dy*dy + dz*dz)
    return total / (len(coords) - 1)


def main():
    parser = argparse.ArgumentParser(description='Extract C-alpha and C-beta coordinates from PDB')
    parser.add_argument('pdb', help='Input PDB file')
    parser.add_argument('--chain', default='A', help='Chain ID to extract (default: A)')
    parser.add_argument('--name', default=None, help='Protein name for JSON (default: PDB basename)')
    parser.add_argument('-o', '--output', required=True, help='Output JSON file')
    args = parser.parse_args()

    rows = extract_ca_cb(args.pdb, args.chain)
    if not rows:
        print(f"No C-alpha atoms found for chain {args.chain} in {args.pdb}", file=sys.stderr)
        sys.exit(1)

    name = args.name
    if name is None:
        name = args.pdb.split('/')[-1].split('.')[0].upper()

    coords = [[seq, pdb_res, ca[0], ca[1], ca[2]] for seq, pdb_res, res_name, ca, cb in rows]
    cb_coords = [[cb[0], cb[1], cb[2]] for seq, pdb_res, res_name, ca, cb in rows]
    res_names = [res_name for seq, pdb_res, res_name, ca, cb in rows]
    mean_d = mean_ca_ca_dist([(ca[0], ca[1], ca[2]) for _, _, _, ca, cb in rows])

    data = {
        "name": name,
        "residues": len(rows),
        "coords": coords,
        "cb_coords": cb_coords,
        "res_names": res_names,
        "mean_ca_ca": mean_d,
    }

    with open(args.output, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Wrote {len(rows)} C-alpha + C-beta coordinates to {args.output} (mean Cα-Cα = {mean_d:.4f} Å)")


if __name__ == '__main__':
    main()
