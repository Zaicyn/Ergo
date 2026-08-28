#!/usr/bin/env python3
"""retemplate.py — splice the NEW unified pair-force physics (GPU
segmented-reduction form) into an already-generated waveform .ergo
file, without needing its original json/pdb inputs.

The new sections are read from the NEW template (single source of
truth: min/ribosome/waveform_template.ergo). Everything else in the
target file (INIT_CHAIN / INIT_NATIVE data, parameters, recipe) is
preserved byte-for-byte.

Usage: python3 min/ribosome/retemplate.py <in.ergo> <out.ergo>
"""

import re
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "waveform_template.ergo")


def read_lines(path):
    with open(path) as f:
        return f.read().splitlines()


def section(lines, start_pred, end_pred, include_end=False):
    """Extract [start, end) lines where start_pred matches the first
    line and end_pred the line AFTER the section (or the last line of
    the section when include_end)."""
    i0 = next(i for i, ln in enumerate(lines) if start_pred(ln))
    i1 = next(i for i, ln in enumerate(lines)
              if i > i0 and end_pred(ln))
    return lines[i0:i1 + (1 if include_end else 0)]


def main():
    src_path, dst_path = sys.argv[1], sys.argv[2]
    tpl = read_lines(TEMPLATE)
    tgt = read_lines(src_path)

    nres = int(re.search(r'PARAMETER INTEGER :: NRES = (\d+)',
                         "\n".join(tgt)).group(1))
    pseg = 256 * max(1, -(-(nres - 3) // 256))
    nslot = nres * pseg

    # ── extract new-template sections ──
    params = section(tpl,
                     lambda ln: ln.startswith('! ── Packed pair-slot'),
                     lambda ln: ln.startswith('PARAMETER INTEGER :: NSLOT'),
                     include_end=True)
    arrays = section(tpl,
                     lambda ln: ln.startswith('! ── Unified pair-slot tables'),
                     lambda ln: ln.startswith('STATIC REAL :: WCO_J'),
                     include_end=True)
    scalars = section(tpl,
                      lambda ln: ln.startswith('! pair-kernel working scalars'),
                      lambda ln: ln.startswith('STATIC REAL :: DD,'),
                      include_end=True)
    initb = section(tpl,
                    lambda ln: ln.startswith('! ── Build the unified pair-slot'),
                    lambda ln: ln.startswith('! ═══'))
    kernels = section(tpl,
                      lambda ln: ln.startswith('  ! Dock gate mask'),
                      lambda ln: ln.startswith('  ! __AROM_LOOP__'))

    params = [re.sub(r'PSEG = \d+', f'PSEG = {pseg}', ln) for ln in params]
    params = [re.sub(r'NSLOT = \d+', f'NSLOT = {nslot}', ln) for ln in params]
    arrays = [re.sub(r'\(5120\)', f'({nslot})', ln) for ln in arrays]

    out = []
    i = 0
    n = len(tgt)
    while i < n:
        ln = tgt[i]
        # 1. params after PHOS_LAM
        out.append(ln)
        if re.match(r'PARAMETER REAL :: PHOS_LAM = ', ln):
            out.append('')
            out.extend(params)
        # 2. arrays after NATIVE_R0 decl
        if re.match(r'STATIC REAL :: NATIVE_R0\(', ln):
            out.append('')
            out.extend(arrays)
        # 3. scalars after NSUB, SUB
        if re.match(r'STATIC INTEGER :: NSUB, SUB', ln):
            out.extend(scalars)
        # 4. init block before the main loop
        if re.match(r'DO FRAME = 1, MAXFRAME', ln):
            out.extend(initb)
            out.append('')
        # 5. replace the four N^2 force blocks
        if ln.startswith('  ! Steric repulsion (|i-j| >= 4, not H-bonded)'):
            # the new section brings its own DOCKM + DO SUB line;
            # drop the target's original '  DO SUB = 1, NSUB' (out[-1]
            # is the just-appended steric comment — remove it first)
            out.pop()
            while out and not out[-1].strip():
                out.pop()
            if out and out[-1].strip() == 'DO SUB = 1, NSUB':
                out.pop()
            # find the end: the '  ! Breakable cystine restraints' line;
            # the old force blocks end at the '  ENDDO' just before it
            # (allowing blank lines / arom code in between, preserved).
            j = next(k for k in range(i, n)
                     if tgt[k].startswith('  ! Breakable cystine'))
            span = tgt[i:j]
            # find last '  ENDDO' in span (end of contact block)
            last_enddo = max(k for k, s in enumerate(span)
                             if s == '  ENDDO')
            preserve = [s for s in span[last_enddo + 1:]
                        if s.strip() and not s.strip().startswith('!')]
            out.extend(kernels)
            if preserve:
                out.append('')
                out.append('  ! preserved aromatic loop (retemplate)')
                out.extend(preserve)
            out.append('')
            i = j
            continue
        i += 1

    with open(dst_path, 'w') as f:
        f.write("\n".join(out) + "\n")
    print(f"{dst_path}: NRES={nres} PSEG={pseg} NSLOT={nslot}")


if __name__ == "__main__":
    main()
