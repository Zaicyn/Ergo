import numpy as np, re, sys
eng = open('engine_cert_dump.txt').read().splitlines()
cfg_e = np.array([[float(x) for x in l.split()[1:]] for l in eng if l.startswith('CFG ')])
frc_e = np.array([[float(x) for x in l.split()[1:]] for l in eng if l.startswith('FRC ')])
nuc_e = [l.strip() for l in eng if l.startswith('NUC ')]
cert_e = [l for l in eng if l.startswith('CERT ')][0]
cfg_m = np.loadtxt('hydro_cert_config.txt', comments='#')
frc_m = np.loadtxt('hydro_cert_forces.txt')
nuc_m = open('hydro_cert_nuc.txt').read().splitlines()
print('CFG shape', cfg_e.shape, cfg_m.shape)
print('max abs CFG diff: %.3e' % np.max(np.abs(cfg_e - cfg_m)))
print('max abs FRC diff: %.3e' % np.max(np.abs(frc_e - frc_m)))
print('NUC rows identical:', nuc_e == nuc_m)
print('engine:', cert_e)
