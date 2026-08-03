"""Time-slit analysis: spectral fringes from two pulses separated by DT.

Reads timeslit.out (cols: SC T U). Scenarios: DT in {64,96,128} x rise
time TW in {80,40,20,10}.

Method:
  - S(omega) = FFT of probe series U(t); the two-pulse comb
    |S| = 2|S0| |cos(omega*DT/2)| has fringe period 2*pi/DT.
  - Fringe period is measured in the dual domain (Wiener-Khinchin):
    R = IFFT(|S|^2) is the autocorrelation; the comb's fringe period
    2*pi/DT <=> side peak of R at lag DT. Peak-pick R in [30,200]
    with parabolic refinement -> DT_rec (oracle: 5%).
  - Visibility: x = |S|/trend - 1 in the pulse band (S > 2% max,
    trend = 0.12 rad moving average); least-squares amplitude of
    cos(omega*DT_rec)/sin(omega*DT_rec) at the recovered period.
    V = 1 for a perfect comb (fringes to zero), V ~ 0 for merged
    pulses. Trend oracle: V rises as pulses sharpen (smaller TW).
"""
import numpy as np
from scipy.signal import hilbert, find_peaks

DTAB = [64, 96, 128] * 4
TWAB = [80] * 3 + [40] * 3 + [20] * 3 + [10] * 3
NFFT = 16384

rows = {}
for line in open("timeslit.out"):
    if line.startswith("#"):
        continue
    sc, t, u = line.split()
    rows.setdefault(int(sc), []).append(float(u))

print(f"{'SC':>2} {'DT':>4} {'TW':>3} {'DT_rec':>7} {'delta':>6} {'V':>6}  verdict")
results = []
for sc in sorted(rows):
    u = np.array(rows[sc])
    u = u - u.mean()
    dt_true, tw = DTAB[sc - 1], TWAB[sc - 1]
    S = np.fft.rfft(u, NFFT)
    mag = np.abs(S)
    freqs = np.fft.rfftfreq(NFFT, d=1.0) * 2 * np.pi
    domega = freqs[1] - freqs[0]

    # --- fringe period via envelope autocorrelation side peak ---
    # envelope removes carrier wiggles; R_env = 2R0 + R0(t-DT) + R0(t+DT)
    env = np.abs(hilbert(u))
    env = env - env.mean()
    R = np.fft.irfft(np.abs(np.fft.rfft(env, NFFT)) ** 2, NFFT)
    lo, hi = 30, 200
    peaks, props = find_peaks(R[lo:hi], prominence=0.005 * R[0])
    if len(peaks):
        pk = lo + peaks[int(np.argmax(props["prominences"]))]
        a, b, c = R[pk - 1], R[pk], R[pk + 1]
        denom = a - 2 * b + c
        dpk = 0.5 * (a - c) / denom if abs(denom) > 1e-30 else 0.0
        dt_rec = pk + dpk
        prom = props["prominences"].max() / R[0]
    else:
        dt_rec, prom = float("nan"), 0.0

    # --- visibility: comb contrast at theoretical max/min frequencies ---
    # |S| = E(w)|cos(w*DT/2)|: maxima at 2n*pi/DT, zeros at (2n+1)*pi/DT.
    # Compare S/E at the comb max nearest the spectral centroid vs the
    # nearest comb zero; fringes are "resolved" only if that zero lies
    # inside the significant band (S > 2% max) — else V = 0 by
    # construction (fewer than one fringe period in the pulse band).
    # --- visibility: envelope-normalized comb contrast in FWHM ---
    # Envelope E(w) is Gaussian with sigma_w = sqrt(2)/TW (exact for the
    # Gaussian source). At comb maxima w_n = 2*pi*n/DT, |cos|=1 so
    # |S(w_n)| = 2*E(w_n): fitting a parabola to log|S| at the maxima
    # (curvature fixed by sigma_w) recovers E's amplitude and center
    # without any smoothing-window bias. Then V = (p95-p5)/(p95+p5) of
    # |S|/E over E's FWHM: if the FWHM covers comb zeros, V -> 1; if the
    # pulse band is narrower than a fringe period, V -> small.
    sig_w = np.sqrt(2.0) / tw
    n_lo = int(np.ceil(0.06 * dt_true / (2 * np.pi)))
    n_hi = int(np.floor(0.34 * dt_true / (2 * np.pi)))
    wn = 2 * np.pi * np.arange(n_lo, n_hi + 1) / dt_true
    idx = np.round(wn / domega).astype(int)
    idx = idx[idx < len(mag)]
    wn = wn[: len(idx)]
    yn = np.log(mag[idx] + 1e-30)
    c_fix = -1.0 / (2 * sig_w ** 2)
    # y - c*w^2 = a + b*w  ->  linear fit for (a, b)
    G = np.column_stack([np.ones_like(wn), wn])
    ab, *_ = np.linalg.lstsq(G, yn - c_fix * wn ** 2, rcond=None)
    a_fit, b_fit = ab
    E = np.exp(a_fit + b_fit * freqs + c_fix * freqs ** 2)
    fwhm = (E > 0.5 * E.max()) & (freqs > 0.02)
    if fwhm.sum() > 10:
        norm = mag[fwhm] / (E[fwhm] + 1e-30)
        p95, p5 = np.percentile(norm, 95), np.percentile(norm, 5)
        V = float(max(0.0, min(1.0, (p95 - p5) / (p95 + p5 + 1e-30))))
    else:
        V = 0.0

    delta = abs(dt_rec - dt_true) / dt_true * 100
    verdict = "PASS" if delta <= 5 else "FAIL"
    results.append((sc, dt_true, tw, dt_rec, delta, V, prom, verdict))
    print(f"{sc:>2} {dt_true:>4} {tw:>3} {dt_rec:>7.2f} {delta:>5.1f}% {V:>6.3f}  {verdict}"
          f"   (side-peak prominence {prom:.3f})")

print("\nvisibility trend (V vs TW per DT):")
for dt in (64, 96, 128):
    vs = [(tw, V) for _, d, tw, _, _, V, _, _ in results if d == dt]
    print(f"  DT={dt:>3}: " + "  ".join(f"TW={tw}: V={V:.3f}" for tw, V in vs))
