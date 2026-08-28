#!/usr/bin/env python3
"""build_d5_variants.py — Phase-3 variant builder (28S Domain-V region,
hierarchical fold-then-dock vs monolithic).

Inputs: the /tmp/d5seg_*.json segments from extract_28s_d5.py.
Steps per segment:
  1. WC pairs: all C1'-C1' pairs 9.8-11.5 A (canonical WC window),
     greedy unique assignment by distance (rung-0 procedure).
  2. generate_protein_ergo.py with the certified RNA recipe:
     css-k 0.5, no register, hb-cap 0, PHOS 0.05/8.0, ribbon 0.1/0.1,
     maxframe 96000, seed 0.0.
  3. Monolithic: full region as one chain.
     Hierarchical: full region as 5 chains (--domains + --dock-from
     48000 + --keep-inter-contacts), WC pairs INTRA-sub-domain only —
     cross-boundary assembly is driven by gated inter-domain Go
     contacts (the certified fold-then-dock pattern).

Outputs in the given outdir: <name>.ergo files ready to compile.
"""

import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "generate_protein_ergo.py")

RECIPE = ["--css-k", "0.5", "--hb-cap", "0",
          "--phos-eps", "0.05", "--phos-lam", "8.0",
          "--frame-k", "0.1", "--frame-pos-k", "0.1",
          "--maxframe", "96000", "--seed", "0.0", "--no-register"]


def wc_pairs(coords, lo=9.8, hi=11.5):
    cand = []
    n = len(coords)
    for i in range(n):
        xi, yi, zi = coords[i][2], coords[i][3], coords[i][4]
        for j in range(i + 4, n):
            xj, yj, zj = coords[j][2], coords[j][3], coords[j][4]
            d = math.sqrt((xi-xj)**2 + (yi-yj)**2 + (zi-zj)**2)
            if lo <= d <= hi:
                cand.append((d, i + 1, j + 1))
    cand.sort()
    used = set()
    pairs = []
    for d, i, j in cand:
        if i in used or j in used:
            continue
        used.add(i)
        used.add(j)
        pairs.append((i, j))
    pairs.sort()
    return pairs


def load(path):
    d = json.load(open(path))
    return d["coords"], d.get("res_names")


def write_pdb(path, coords, res_names):
    """Minimal PDB: one C1' ATOM record per residue, chain A."""
    with open(path, "w") as f:
        for i, c in enumerate(coords, 1):
            rn = res_names[i - 1] if res_names else "N"
            if len(rn) > 3:
                rn = rn[:3]
            f.write(
                f"ATOM  {i:5d}  C1' {rn:>3s} A{c[1]:4d}    "
                f"{c[2]:8.3f}{c[3]:8.3f}{c[4]:8.3f}  1.00  0.00           C\n")
        f.write("END\n")


def gen(json_path, name, outdir, extra, pdb=None):
    cmd = ["python3", GEN, "--json", json_path, "--name", name,
           "--output", os.path.join(outdir, name + ".ergo")] + RECIPE + extra
    if pdb:
        cmd += ["--pdb", pdb, "--chain", "A"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"GEN-FAIL {name}: {r.stderr[-200:]}")
        return False
    print(f"built {name}.ergo")
    return True


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/d5var"
    os.makedirs(outdir, exist_ok=True)
    segs = sorted(p for p in os.listdir("/tmp")
                  if p.startswith("d5seg_") and p.endswith(".json")
                  and "full" not in p)
    full = "/tmp/d5seg_full.json"
    assert segs and os.path.exists(full), "run extract_28s_d5.py first"

    # 1. sub-domain solos (packed-batch fold happens in the assembly
    #    run; these solo variants are the per-subdomain quality oracles)
    for s in segs:
        coords, rnames = load(os.path.join("/tmp", s))
        pairs = wc_pairs(coords)
        name = s.replace(".json", "")
        pdb_path = os.path.join("/tmp", name + ".pdb")
        write_pdb(pdb_path, coords, rnames)
        extra = ["--pdb", pdb_path, "--chain", "A"]
        if pairs:
            extra += ["--cystine", ",".join(f"{i}-{j}" for i, j in pairs)]
        print(f"{name}: {len(coords)} nt, {len(pairs)} WC pairs")
        gen(os.path.join("/tmp", s), name, outdir, extra)

    # 2. monolithic baseline (full region, one chain)
    coords, rnames = load(full)
    pairs = wc_pairs(coords)
    write_pdb("/tmp/d5seg_full.pdb", coords, rnames)
    print(f"monolithic: {len(coords)} nt, {len(pairs)} WC pairs")
    gen(full, "d5_mono", outdir,
        ["--pdb", "/tmp/d5seg_full.pdb", "--chain", "A",
         "--cystine", ",".join(f"{i}-{j}" for i, j in pairs)])

    # 3. hierarchical assembly (5 chains, dock-from 50%)
    #    boundaries from the segment files (consecutive ranges)
    bounds = []
    off = 0
    for s in segs:
        coords_s, _ = load(os.path.join("/tmp", s))
        off += len(coords_s)
        bounds.append(off)
    doms = []
    lo = 1
    for hi in bounds:
        doms.append(f"{lo}-{hi}")
        lo = hi + 1
    # intra-only WC pairs: pairs from each segment, offset-adjusted
    allpairs = []
    off = 0
    for s in segs:
        coords_s, _ = load(os.path.join("/tmp", s))
        for i, j in wc_pairs(coords_s):
            allpairs.append((i + off, j + off))
        off += len(coords_s)
    print(f"hierarchical: domains {','.join(doms)}, "
          f"{len(allpairs)} intra WC pairs")
    gen(full, "d5_hier", outdir,
        ["--pdb", "/tmp/d5seg_full.pdb", "--chain", "A",
         "--domains", ",".join(doms), "--dock-from", "48000",
         "--keep-inter-contacts",
         "--cystine", ",".join(f"{i}-{j}" for i, j in allpairs)])


if __name__ == "__main__":
    main()
