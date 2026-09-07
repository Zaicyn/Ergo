#!/usr/bin/env python3
"""R11-c analyzer: O-S7 books battery (SEVSTEP-parameterized re-derivation
of sf_books.py) + O-S2..O-S6 measurements for the 1M stress-fiber runs.

Usage: r11c_analyze.py <log> <sevstep>
"""
import sys

NM = 400
MAXMYO = 8
NHF = 3
NDIAG = 500
NETF_TOL = 5e-7
XSFM = 5.5
POST = 4000  # post-assembly analysis start (registered)

path = sys.argv[1]
SEVSTEP = int(sys.argv[2])

raw = open(path, "rb").read()
nul = raw.count(b"\x00")
fails = []


def fail(m):
    fails.append(m)


live_my = {}
cum_mya = cum_myr = 0
live_xl = {}
cum_xla = cum_xlr = 0
live_adh = {}          # F -> (born, monomer)
adh_transfers = []     # (sevstep, F, G, M) reg-8 R6 transfers (no event)
cum_adha = cum_adhr = 0
live_sfa = {}   # F -> (born, end)
n_myost = 0
netf_max = 0.0
n_census = 0
final = False
pending = None
fil_by_step = {}
sev_events = []
census_series = []     # (step, nfil, npoly-ish via nbound)
fib_series = []        # (step,nfil,npoly,tipxL,tipxR,flen,ten,nmyo,nxl)
sfas_series = []       # (step,end,nb,trx,try,trz,fmag,arate,rrate)
sfa_events = []        # (step, F, end)
sfr_events = []        # (step, F, lifetime, cause, end)
myor_causes = {}
xlkr_causes = {}
myoa_steps = []
xlka_steps = []
xlkr_steps = []
myor_steps = []
sfr_steps = []
myost_sign = {"L_ok": 0, "L_bad": 0, "R_ok": 0, "R_bad": 0}
prev_nfil = None
nfil_jumps = []
# O-S4 data: fib at step S precedes the gm lines of census S; grips are
# captured at fib time and resolved to positions when the NEXT census
# header arrives (gm of S then complete).
gm_cur = None
pend_os4 = None        # (step, [(M1,M2,F1,F2)], [(M1,M2)])
xl_at_census = []      # (step, [(x1,x2,F1,F2)])
myo_at_census = []     # (step, [(x1,x2)])
same_half_xl = 0
bpol_bad = 0
pend_xlka = None

for line in raw.decode("utf-8", "replace").splitlines():
    q = line.split()
    if not q:
        continue
    tag = q[0]
    if tag == "census":
        if pend_os4 is not None and gm_cur:
            stp, xl_g, my_g = pend_os4
            xl_at_census.append((stp, [(gm_cur.get(a), gm_cur.get(b), F1, F2)
                                       for (a, b, F1, F2) in xl_g]))
            myo_at_census.append((stp, [(gm_cur.get(a), gm_cur.get(b))
                                        for (a, b) in my_g]))
            pend_os4 = None
        if pending is not None:
            if pending["ngm"] != NM:
                fail(f"gm count {pending['ngm']} != {NM} at step {pending['step']}")
            st = pending["states"]
            if st.get(1, 0) != pending["nbound"] or st.get(0, 0) != pending["nfree"]:
                fail(f"ghost/state mismatch at step {pending['step']}")
            if pending["nbound"] + pending["nfree"] + 2 * pending["ndim"] != NM:
                fail(f"conservation fail at step {pending['step']}")
            if pending["step"] == SEVSTEP and sev_events:
                fmap = fil_by_step.get(SEVSTEP, {})
                for (st2, F, G, svold, svlen) in sev_events:
                    if fmap.get(F) != svold:
                        fail(f"post-sev len(F{F})={fmap.get(F)} != SVOLD={svold}")
                    if fmap.get(G) != svlen:
                        fail(f"post-sev len(G{G})={fmap.get(G)} != SVLEN={svlen}")
        kv = dict(zip(q[2::2], q[3::2]))
        step = int(q[1])
        nfil = int(kv["nfil"])
        if prev_nfil is not None and abs(nfil - prev_nfil) > 2 * NHF:
            nfil_jumps.append((step, prev_nfil, nfil))
        prev_nfil = nfil
        census_series.append((step, nfil, int(kv["nbound"])))
        pending = dict(step=step, nfil=nfil, nbound=int(kv["nbound"]),
                       nfree=int(kv["nfree"]), ndim=int(kv["ndim"]),
                       states={}, ngm=0)
        n_census += 1
        # O-S4 snapshot at this census (uses gm collected AFTER this header;
        # handled by storing refs and filling on 'gm' lines)
        gm_cur = {}
        gm_step = step
    elif tag == "gm" and pending is not None:
        m = int(q[1])
        s = int(q[2])
        pending["states"][s] = pending["states"].get(s, 0) + 1
        pending["ngm"] += 1
        if s == 1:
            gm_cur[m] = float(q[3])
    elif tag == "fil":
        fil_by_step.setdefault(int(q[1]), {})[int(q[2])] = int(q[4])
    elif tag == "myoa":
        step, L = int(q[1]), int(q[2])
        if L in live_my:
            fail(f"myoa on live slot {L} at step {step}")
        live_my[L] = dict(F1=int(q[3]), M1=int(q[4]), F2=int(q[5]), M2=int(q[6]), born=step)
        cum_mya += 1
        myoa_steps.append(step)
        if len(live_my) > MAXMYO:
            fail(f"nmyo > MAXMYO at step {step}")
    elif tag == "myor":
        step, L = int(q[1]), int(q[2])
        if L not in live_my:
            fail(f"myor on dead slot {L} at step {step}")
            continue
        a = live_my.pop(L)
        if (int(q[3]), int(q[4]), int(q[5]), int(q[6])) != (a["F1"], a["M1"], a["F2"], a["M2"]):
            fail(f"myor endpoint mismatch slot {L} at step {step}")
        if int(q[7]) != step - a["born"]:
            fail(f"myor lifetime mismatch slot {L} at step {step}")
        c = int(q[11])
        if c not in (1, 2, 3, 4, 5, 6):
            fail(f"myor bad cause {c} at step {step}")
        myor_causes[c] = myor_causes.get(c, 0) + 1
        myor_steps.append(step)
        cum_myr += 1
    elif tag == "myost":
        step, L, hd = int(q[1]), int(q[2]), int(q[3])
        mold, mnew, dx = int(q[4]), int(q[5]), float(q[6])
        n_myost += 1
        if L not in live_my:
            fail(f"myost on dead slot {L} at step {step}")
            continue
        a = live_my[L]
        if mnew == mold:
            fail(f"myost null step slot {L} step {step}")
        if hd == 1:
            if mold != a["M1"]:
                fail(f"myost head1 stale grip slot {L} step {step}")
            a["M1"] = mnew
            hf = a["F1"]
        else:
            if mold != a["M2"]:
                fail(f"myost head2 stale grip slot {L} step {step}")
            a["M2"] = mnew
            hf = a["F2"]
        # sign spot-check (range, not gate): left-half head should step -x
        if hf <= NHF:
            k = "L_ok" if dx < 0 else "L_bad"
        else:
            k = "R_ok" if dx > 0 else "R_bad"
        myost_sign[k] += 1
    elif tag == "myos":
        step, nmyo = int(q[1]), int(q[2])
        if nmyo != cum_mya - cum_myr or nmyo != len(live_my):
            fail(f"motor inventory fail at step {step}")
        nf = max(abs(float(q[5])), abs(float(q[6])), abs(float(q[7])))
        netf_max = max(netf_max, nf)
    elif tag == "xlka":
        step, L = int(q[1]), int(q[2])
        if L in live_xl:
            fail(f"xlka on live slot {L} at step {step}")
        live_xl[L] = dict(F1=int(q[3]), M1=int(q[4]), F2=int(q[5]), M2=int(q[6]), born=step)
        cum_xla += 1
        xlka_steps.append(step)
        # informational: same-half links (buckled local axes let the
        # certified PBUND=2 gate accept these; gate proof = bpol record)
        f1, f2 = int(q[3]), int(q[5])
        if (f1 <= NHF) == (f2 <= NHF) and f1 <= 2 * NHF and f2 <= 2 * NHF:
            same_half_xl += 1
        pend_xlka = (step, int(q[4]), int(q[6]))
    elif tag == "bpol":
        # PBUND=2 gate spot-check: cos must be <= -COSB (printed 6 dp)
        if pend_xlka is not None:
            stp, m1, m2 = pend_xlka
            if int(q[1]) == stp and (int(q[2]), int(q[3])) == (m1, m2):
                if float(q[4]) > -0.4999995:
                    bpol_bad += 1
                    fail(f"bpol cos={q[4]} > -COSB at step {stp} (PBUND=2 gate)")
            pend_xlka = None
    elif tag == "xlkr":
        step, L = int(q[1]), int(q[2])
        if L not in live_xl:
            fail(f"xlkr on dead slot {L} at step {step}")
            continue
        a = live_xl.pop(L)
        if (int(q[3]), int(q[4]), int(q[5]), int(q[6])) != (a["F1"], a["M1"], a["F2"], a["M2"]):
            fail(f"xlkr endpoint mismatch slot {L} at step {step}")
        if int(q[7]) != step - a["born"]:
            fail(f"xlkr lifetime mismatch slot {L} at step {step}")
        c = int(q[11])
        if c not in (1, 2, 3, 4, 5):
            fail(f"xlkr bad cause {c} at step {step}")
        xlkr_causes[c] = xlkr_causes.get(c, 0) + 1
        xlkr_steps.append(step)
        cum_xlr += 1
    elif tag == "xlks":
        step, nxl = int(q[1]), int(q[2])
        if nxl != cum_xla - cum_xlr or nxl != len(live_xl):
            fail(f"xl inventory fail at step {step}")
        nf = max(abs(float(q[5])), abs(float(q[6])), abs(float(q[7])))
        netf_max = max(netf_max, nf)
    elif tag == "adha":
        step, F = int(q[1]), int(q[2])
        if F in live_adh:
            fail(f"adha on bonded filament {F} at step {step}")
        live_adh[F] = (step, int(q[3]))   # (born, gripped monomer)
        cum_adha += 1
    elif tag == "adhr":
        step, F, M = int(q[1]), int(q[2]), int(q[3])
        if F not in live_adh:
            # reg. 8: an R6 bond whose gripped monomer moved to a sever
            # remnant TRANSFERS to the new slot with no event; recognize
            # the transfer by (remnant slot, same monomer) and re-key.
            ok = False
            for (ss, sF, sG, svold, svlen) in sev_events:
                if sG == F and sF in live_adh and live_adh[sF][1] == M:
                    live_adh[F] = live_adh.pop(sF)
                    adh_transfers.append((ss, sF, sG, M))
                    ok = True
                    break
            if not ok:
                fail(f"adhr on unbonded filament {F} at step {step}")
                continue
        born = live_adh.pop(F)[0]
        if int(q[4]) != step - born:
            fail(f"adhr lifetime mismatch F{F} at step {step}")
        if int(q[8]) not in (1, 2, 3, 4):
            fail(f"adhr bad cause {q[8]} at step {step}")
        cum_adhr += 1
    elif tag == "adhs":
        step, nadh = int(q[1]), int(q[2])
        if nadh != cum_adha - cum_adhr or nadh != len(live_adh):
            fail(f"adh inventory fail at step {step}")
    elif tag == "sfa":
        step, F = int(q[1]), int(q[2])
        if F in live_sfa:
            fail(f"sfa on bonded filament {F} at step {step}")
        e = int(q[8])
        live_sfa[F] = (step, e)
        sfa_events.append((step, F, e))
    elif tag == "sfr":
        step, F = int(q[1]), int(q[2])
        if F not in live_sfa:
            fail(f"sfr on unbonded filament {F} at step {step}")
            continue
        born, e = live_sfa.pop(F)
        if int(q[4]) != step - born:
            fail(f"sfr lifetime mismatch F{F} at step {step}")
        if int(q[8]) not in (1, 2, 3, 4):
            fail(f"sfr bad cause {q[8]} at step {step}")
        if int(q[9]) != e:
            fail(f"sfr end mismatch F{F} at step {step}")
        sfr_events.append((step, F, step - born, int(q[8]), e))
        sfr_steps.append(step)
    elif tag == "sfas":
        step, e, nb = int(q[1]), int(q[2]), int(q[3])
        want = sum(1 for (b, ee) in live_sfa.values() if ee == e)
        if nb != want:
            fail(f"SF per-end inventory fail at step {step} end {e}: nb={nb} live={want}")
        sfas_series.append((step, e, nb, float(q[4]), float(q[5]), float(q[6]),
                            float(q[7]), float(q[8]), float(q[9])))
    elif tag == "fib":
        step = int(q[1])
        fmap = fil_by_step.get(step, {})
        nfil6 = sum(1 for F in fmap if F <= 2 * NHF)
        npoly6 = sum(l for F, l in fmap.items() if F <= 2 * NHF)
        if fmap and (int(q[2]) != nfil6 or int(q[3]) != npoly6):
            fail(f"fib census mismatch at step {step}")
        fib_series.append((step, int(q[2]), int(q[3]), float(q[4]), float(q[5]),
                           float(q[6]), float(q[7]), int(q[8]), int(q[9])))
        # O-S4: capture live grips; positions resolved at next census
        pend_os4 = (step,
                    [(v["M1"], v["M2"], v["F1"], v["F2"]) for v in live_xl.values()],
                    [(v["M1"], v["M2"]) for v in live_my.values()])
    elif tag == "sev":
        step, F, G = int(q[1]), int(q[2]), int(q[3])
        if step != SEVSTEP:
            fail(f"sev at step {step} != SEVSTEP={SEVSTEP}")
        pre = fil_by_step.get(step - NDIAG, {})
        if G in pre:
            fail(f"sev target slot G={G} already active before sever")
        sev_events.append((step, F, G, int(q[6]), int(q[7])))
    elif tag == "FINAL":
        final = True

# flush pending O-S4 snapshot (gm of last census complete)
if pend_os4 is not None and gm_cur:
    stp, xl_g, my_g = pend_os4
    xl_at_census.append((stp, [(gm_cur.get(a), gm_cur.get(b), F1, F2)
                               for (a, b, F1, F2) in xl_g]))
    myo_at_census.append((stp, [(gm_cur.get(a), gm_cur.get(b))
                                for (a, b) in my_g]))
# flush last census
if pending is not None:
    if pending["ngm"] != NM:
        fail(f"gm count {pending['ngm']} != {NM} at final census")
    st = pending["states"]
    if st.get(1, 0) != pending["nbound"] or st.get(0, 0) != pending["nfree"]:
        fail("ghost/state mismatch at final census")
    if pending["nbound"] + pending["nfree"] + 2 * pending["ndim"] != NM:
        fail("conservation fail at final census")

if not final:
    fail("FINAL missing")
if nul != 0:
    fail(f"NUL={nul}")

# ---------- stats helpers ----------
def qs(v):
    v = sorted(v)
    n = len(v)
    if n == 0:
        return None
    def q(p):
        i = min(n - 1, max(0, int(p * n)))
        return v[i]
    return dict(n=n, mean=sum(v) / n, med=q(.5), q10=q(.1), q90=q(.9),
                lo=v[0], hi=v[-1])

print(f"== {path.split('/')[-1]} SEVSTEP={SEVSTEP}")
print(f"BOOKS: censuses={n_census} myoa={cum_mya} myor={cum_myr} myost={n_myost} "
      f"xlka={cum_xla} xlkr={cum_xlr} adha={cum_adha} adhr={cum_adhr} "
      f"sfa={len(sfa_events)} sfr={len(sfr_events)} sev={len(sev_events)} "
      f"netf_max={netf_max:.3e} NUL={nul} FINAL={final}")
print(f"  myor causes={dict(sorted(myor_causes.items()))} "
      f"xlkr causes={dict(sorted(xlkr_causes.items()))}")
print(f"  myost sign (range): {myost_sign}  nfil_big_jumps={nfil_jumps[:5]}")
print(f"  nfil: first={census_series[0][1] if census_series else '?'} "
      f"last={census_series[-1][1] if census_series else '?'} "
      f"min={min(c[1] for c in census_series)} max={max(c[1] for c in census_series)}")

# ---------- O-S3 ----------
for e in (0, 1):
    rows = [r for r in sfas_series if r[1] == e]
    post = [r for r in rows if r[0] >= POST]
    allw = [r[3] for r in post]
    bw = [r for r in post if r[2] > 0]
    btrx = [r[3] for r in bw]
    # event-based duty: merge attach/rupture in time order per end
    evs = [(s, 1, F) for (s, F, ee) in sfa_events if ee == e] + \
          [(s, -1, F) for (s, F, lt, c, ee) in sfr_events if ee == e]
    evs.sort()
    iv = []
    live = {}
    for (s, d, F) in evs:
        if d == 1:
            live[F] = s
        elif F in live:
            iv.append((live.pop(F), s))
    laststep = sfas_series[-1][0] if sfas_series else 0
    for F, st in live.items():
        iv.append((st, laststep))
    duty_steps = sum(max(0, b - max(a, POST)) for a, b in iv if b >= POST)
    nbstat = qs([r[2] for r in post])
    print(f"O-S3 end{e}: post(>={POST}) windows={len(post)} "
          f"bonded_windows={len(bw)} ({100.0*len(bw)/max(1,len(post)):.1f}%) "
          f"event_duty={duty_steps/max(1,laststep-POST):.3f} "
          f"nb_mean={nbstat['mean']:.2f}" if nbstat else "")
    s = qs(allw)
    if s:
        print(f"  trx all windows: mean={s['mean']:.3f} med={s['med']:.3f} "
              f"[{s['q10']:.3f},{s['q90']:.3f}]")
    s = qs(btrx)
    if s:
        print(f"  trx bonded windows: n={s['n']} mean={s['mean']:.3f} med={s['med']:.3f} "
              f"[{s['q10']:.3f},{s['q90']:.3f}]")
    # fmag while bonded
    fm = qs([r[6] for r in bw])
    if fm:
        print(f"  fmag bonded: mean={fm['mean']:.3f} med={fm['med']:.3f}")

ten_post = [f[6] for f in fib_series if f[0] >= POST]
flen_post = [f[5] for f in fib_series if f[0] >= POST]
s = qs(ten_post)
if s:
    print(f"O-S3 tension post: mean={s['mean']:.3f} med={s['med']:.3f} "
          f"[{s['q10']:.3f},{s['q90']:.3f}] min={s['lo']:.3f} max={s['hi']:.3f} "
          f"(note: includes erratum-5 0.42/motor preload, ~2.5 total at 3 motors)")
npos = sum(1 for t in ten_post if t > 0)
print(f"  tension>0 fraction: {npos}/{len(ten_post)}")

# ---------- O-S2 ----------
# (a) first window both ends event-bonded within window + ten>0
sfa_by_e = {0: sorted(s for s, F, e in sfa_events if e == 0),
            1: sorted(s for s, F, e in sfa_events if e == 1)}
sfr_by_e = {0: sorted(s for s, F, lt, c, e in sfr_events if e == 0),
            1: sorted(s for s, F, lt, c, e in sfr_events if e == 1)}
def bonded_in_window(e, w0, w1):
    # any attach before w1 that ruptures after w0 (or never)
    for (st, F, ee) in sfa_events:
        if ee != e or st >= w1:
            continue
        rel = next((r for r in sfr_events if r[1] == F and r[0] >= st), None)
        if rel is None or rel[0] >= w0:
            return True
    return False
os2a = None
for f in fib_series:
    w0, w1 = f[0] - NDIAG, f[0]
    if bonded_in_window(0, w0, w1) and bonded_in_window(1, w0, w1) and f[6] > 0:
        os2a = f[0]
        break
os2b = None
run = 0
for f in fib_series:
    if abs(f[5]) < 1.0:
        run += 1
        if run >= 3:
            os2b = f[0] - 2 * NDIAG
            break
    else:
        run = 0
print(f"O-S2: (a) bond-assembly latency = {os2a} (window end step); "
      f"(b) contractile equilibration (flen<1.0 x3 windows) = {os2b}")

# ---------- O-S4 ----------
DMY0 = 1.5
in_len = out_len = 0.0
in_n = out_n = 0
for (step, links) in xl_at_census:
    if step < POST:
        continue
    motors = dict(myo_at_census).get(step, [])
    mxs = [x for pair in motors for x in pair if x is not None]
    lxs = [x for l in links for x in l[:2] if x is not None]
    if not mxs or not lxs:
        continue
    mlo, mhi = min(mxs) - DMY0, max(mxs) + DMY0
    flo, fhi = min(lxs + mxs), max(lxs + mxs)
    for (x1, x2, F1, F2) in links:
        xm = None
        xs = [x for x in (x1, x2) if x is not None]
        if not xs:
            continue
        xm = sum(xs) / len(xs)
        if mlo <= xm <= mhi:
            in_n += 1
        else:
            out_n += 1
    in_len += max(0.0, min(mhi, fhi) - max(mlo, flo))
    out_len += max(0.0, (fhi - flo) - max(0.0, min(mhi, fhi) - max(mlo, flo)))
print(f"O-S4: post windows w/ links+motors: xl_in_myo_region={in_n} "
      f"xl_outside={out_n}; mean region x-len={in_len:.1f} outside={out_len:.1f}; "
      f"density in={in_n/max(1e-9,in_len):.3f} out={out_n/max(1e-9,out_len):.3f} "
      f"(links/unit-x); same-half links (buckled local-axis accepts)={same_half_xl}; "
      f"bpol gate violations={bpol_bad}")

# ---------- O-S5 ----------
s = qs(flen_post)
if s:
    print(f"O-S5 flen post: mean={s['mean']:.3f} med={s['med']:.3f} "
          f"[{s['q10']:.3f},{s['q90']:.3f}] range=[{s['lo']:.3f},{s['hi']:.3f}]")
h = len(ten_post) // 2
if h > 0:
    print(f"O-S5 drift: tension mean first-half={sum(ten_post[:h])/h:.3f} "
          f"second-half={sum(ten_post[h:])/max(1,len(ten_post)-h):.3f}; "
          f"flen first-half={sum(flen_post[:h])/h:.3f} "
          f"second-half={sum(flen_post[h:])/max(1,len(flen_post)-h):.3f}")
laststep = fib_series[-1][0] if fib_series else 1
span_k = (laststep - POST) / 1000.0
def rate(v):
    return sum(1 for s in v if s >= POST) / max(1e-9, span_k)
print(f"O-S5 turnover per 1k steps (post): myosin={(rate(myoa_steps)+rate(myor_steps))/2:.2f} "
      f"xlink={(rate(xlka_steps)+rate(xlkr_steps))/2:.2f} "
      f"sfadh={(rate([s for s,F,e in sfa_events])+rate(sfr_steps))/2:.2f}")
nb_series = [c[2] for c in census_series if c[0] >= POST]
s = qs(nb_series)
if s:
    print(f"O-S5 nbound post: mean={s['mean']:.1f} [{s['q10']},{s['q90']}] "
          f"range=[{s['lo']},{s['hi']}] (npoly drift proxy)")

# ---------- O-S6 ----------
if sev_events:
    print(f"O-S6: sev events={[(s, F, G, o, l) for (s, F, G, o, l) in sev_events]}")
    print(f"  reg-8 R6 transfers (no event, re-keyed): {adh_transfers}")
    print(f"  cause-5 coverage: myor5={myor_causes.get(5,0)} xlkr5={xlkr_causes.get(5,0)} "
          f"total={myor_causes.get(5,0)+xlkr_causes.get(5,0)}")
    # post-sever tension/traction recovery
    tpre = [f for f in fib_series if f[0] <= SEVSTEP]
    tpost = [f for f in fib_series if f[0] > SEVSTEP]
    if tpre and tpost:
        print(f"  tension last pre-sev={tpre[-1][6]:.3f}; first 5 post: "
              f"{[round(f[6],2) for f in tpost[:5]]}")
        # sustained recovery: >=10 consecutive windows ten>0
        rec = None
        run = 0
        for f in tpost:
            if f[6] > 0:
                run += 1
                if run >= 10:
                    rec = f[0] - 9 * NDIAG
                    break
            else:
                run = 0
        print(f"  sustained tension>0 (>=10 windows) resumes at: {rec}")
    for e in (0, 1):
        pre = [r for r in sfas_series if r[1] == e and r[0] <= SEVSTEP and r[2] > 0]
        post = [r for r in sfas_series if r[1] == e and r[0] > SEVSTEP]
        pb = [r for r in post if r[2] > 0]
        print(f"  end{e}: bonded windows post-sever={len(pb)}/{len(post)}"
              + (f" first={pb[0][0]} trx_mean={sum(r[3] for r in pb)/len(pb):.3f}" if pb else ""))
    # remnant fate: G slots
    gslots = sorted(set(G for (s, F, G, o, l) in sev_events))
    for G in gslots:
        lens = [(st, m[G]) for st, m in sorted(fil_by_step.items()) if G in m]
        if lens:
            print(f"  remnant G{G}: first_len={lens[0][1]} last_len={lens[-1][1]} "
                  f"at step {lens[-1][0]} n_windows={len(lens)}")
else:
    print("O-S6: no sever (main arm)")

if fails:
    print("BOOKS FAIL:")
    for f in fails[:25]:
        print("  ", f)
    sys.exit(1)
print("BOOKS PASS")
