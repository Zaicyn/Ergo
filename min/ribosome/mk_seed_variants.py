#!/usr/bin/env python3
"""mk_seed_variants.py — Phase-2 best-of-N variant builder.

Retemplates a delivered waveform .ergo (old physics) to the new GPU
pair-kernel form, then stamps out N seed variants by patching the
SEED parameter (0.0 .. N-1.0, the campaign's seed convention).

Usage:
  python3 min/ribosome/mk_seed_variants.py <base.ergo> <outdir> <prefix> <nseeds>
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    base, outdir, prefix, nseeds = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    os.makedirs(outdir, exist_ok=True)
    tmp = os.path.join(outdir, f"{prefix}_retpl.ergo")
    subprocess.run([sys.executable, os.path.join(HERE, "retemplate.py"),
                    base, tmp], check=True)
    src = open(tmp).read()
    os.unlink(tmp)
    for s in range(nseeds):
        v = re.sub(r'PARAMETER REAL :: SEED = [0-9.eE\-]+',
                   f'PARAMETER REAL :: SEED = {float(s):.1f}', src)
        dst = os.path.join(outdir, f"{prefix}_{s}.ergo")
        with open(dst, 'w') as f:
            f.write(v)
    print(f"{nseeds} seed variants in {outdir} (prefix {prefix})")


if __name__ == "__main__":
    main()
