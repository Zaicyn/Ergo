#!/usr/bin/env python3
# compare engine cert dump (cert_engine.log) vs mirror oracle dumps
import sys, numpy as np

eng_log = sys.argv[1] if len(sys.argv) > 1 else '/tmp/m4d/cert_engine.log'
mir_cfg = sys.argv[2] if len(sys.argv) > 2 else '/tmp/m4d/m4d_cert_config.txt'
mir_frc = sys.argv[3] if len(sys.argv) > 3 else '/tmp/m4d/m4d_cert_forces.txt'

cfg_e, frc_e, cert_e = [], [], None
for line in open(eng_log):
    t = line.split()
    if not t:
        continue
    if t[0] == 'CFG':
        cfg_e.append([float(x) for x in t[1:4]])
    elif t[0] == 'FRC':
        frc_e.append([float(x) for x in t[1:4]])
    elif t[0] == 'CERT':
        cert_e = line.strip()

cfg_m = [list(map(float, l.split())) for l in open(mir_cfg) if not l.startswith('#')]
frc_m = [list(map(float, l.split())) for l in open(mir_frc) if not l.startswith('#')]
cfg_e = np.array(cfg_e); cfg_m = np.array(cfg_m)
frc_e = np.array(frc_e); frc_m = np.array(frc_m)
print('n beads engine %d mirror %d' % (cfg_e.shape[0], cfg_m.shape[0]))
dcfg = np.abs(cfg_e - cfg_m).max()
dfrc = np.abs(frc_e - frc_m).max()
print('max |dCFG| = %.3e' % dcfg)
print('max |dFRC| = %.3e' % dfrc)
ib = np.unravel_index(np.argmax(np.abs(frc_e - frc_m)), frc_e.shape)
print('worst FRC bead %d ax %d: engine %.17e mirror %.17e' %
      (ib[0], ib[1], frc_e[ib], frc_m[ib]))
print('engine:', cert_e)
# mirror cert energy line recompute from forces module is printed to stdout
print('PASS' if max(dcfg, dfrc) <= 1e-11 else 'FAIL', '(tol 1e-11)')
