import numpy as np
from analyze import parse_log
print('%-24s %8s %8s %8s %8s %8s' % ('run','dL_skew','maxdrop','maxrise','bigdrop','ndrop500'))
for name, path, kind in [
    ('eng_hyd_s77031','eng_hyd300_s77031.log','engine'),
    ('eng_hyd_s123457','eng_hyd300_s123457.log','engine'),
    ('mir_hyd_s77031','mir_hyd300_s77031.log','mirror'),
    ('mir_hyd_s123457','mir_hyd300_s123457.log','mirror'),
    ('eng_ctrl_s77031','eng_ctrl82_s77031.log','engine'),
    ('eng_ctrl_s123457','eng_ctrl82_s123457.log','engine'),
    ('mir_ctrl_s77031','mir_ctrl82_s77031.log','mirror'),
    ('mir_ctrl_s123457','mir_ctrl82_s123457.log','mirror'),
    ('eng_hyd_s888811','eng_hyd300_s888811.log','engine'),
    ('mir_hyd_s888811','mir_hyd300_s888811.log','mirror'),
    ('eng_ctrl_s888811','eng_ctrl82_s888811.log','engine'),
    ('mir_ctrl_s888811','mir_ctrl82_s888811.log','mirror'),
]:
    r = parse_log(path, kind)
    half = r['steps'] > 150000
    L = r['lens'][half]
    dL = np.diff(L)
    sk = float(((dL-dL.mean())**3).mean()/ max(dL.std(),1e-9)**3)
    # catastrophe episodes: runs of consecutive shrinking 500-step intervals
    drops = dL[dL<0]
    print('%-24s %8.3f %8d %8d %8d %8d' % (name, sk, dL.min(), dL.max(),
          int((dL<=-3).sum()), len(drops)))
