"""Merge results_<field>.dat files into results.dat and print variance table."""
import glob
import numpy as np

rows = []
for f in sorted(glob.glob('results_*.dat')):
    if 'ed' in f:
        continue
    for line in open(f):
        if line.startswith('#') or not line.strip():
            continue
        field, N, mean_mn, var_mn, max_chi = line.split()
        rows.append((field, int(N), float(mean_mn), float(var_mn), int(max_chi)))

# dedupe (reruns append): keep last occurrence per (field, N)
best = {}
for r in rows:
    best[(r[0], r[1])] = r
rows = [best[k] for k in sorted(best)]

with open('results.dat', 'w') as out:
    out.write('# field N mean_mn var_mn max_chi\n')
    for r in rows:
        out.write(f'{r[0]} {r[1]} {r[2]:.16e} {r[3]:.16e} {r[4]}\n')

fields = ['viviani', 'circle', 'trefoil', 'random']
Ns = sorted({r[1] for r in rows})
data = {(r[0], r[1]): r for r in rows}

print(f'{"N":>4} ' + ' '.join(f'{f:>12}' for f in fields) + '   (var of m.n)')
for N in Ns:
    cells = []
    for f in fields:
        r = data.get((f, N))
        cells.append(f'{r[3]:12.3e}' if r else f'{"--":>12}')
    print(f'{N:>4} ' + ' '.join(cells) + ('   N%4==0' if N % 4 == 0 else ''))

print(f'\n{"N":>4} ' + ' '.join(f'{f:>12}' for f in fields) + '   (max_chi; 128=saturated)')
for N in Ns:
    cells = []
    for f in fields:
        r = data.get((f, N))
        cells.append(f'{r[4]:12d}' if r else f'{"--":>12}')
    print(f'{N:>4} ' + ' '.join(cells))

print(f'\n{"N":>4} ' + ' '.join(f'{f:>12}' for f in fields) + '   (mean m.n)')
for N in Ns:
    cells = []
    for f in fields:
        r = data.get((f, N))
        cells.append(f'{r[2]:12.4e}' if r else f'{"--":>12}')
    print(f'{N:>4} ' + ' '.join(cells))
