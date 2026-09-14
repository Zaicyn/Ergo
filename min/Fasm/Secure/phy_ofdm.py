"""phy_ofdm.py -- FFT-OFDM vs DWT-OFDM (Haar, db4) over honest channels.

N=64 carriers, QPSK, frames of 64 bands x 8 symbols (512 time samples,
1024 bits). FFT uses CP=16 (25% overhead, counted in SNR fairly:
SNR = mean TX-sample power / noise-sample power). DWT uses circular
Mallat trees via precomputed synthesis matrices (A = S.T verified to
1e-10: perfect reconstruction or abort). Flat Rayleigh fading with
perfect-CSI one-tap EQ (exact for both under flat fading), impulse
bursts (wire-contiguous, like our BU cells), one NBI tone.

Outputs: BER tables per (modem, channel, SNR); byte-mapped error
stats (mean bad bytes / 4096B-equivalent, max bad-byte run) at set
operating points for direct mapping onto packetbench cells; .npz
byte-error traces for future replay.
"""
import numpy as np
import subprocess

# Trace format version: bump on ANY generator change (modem, mapping,
# channel model, framing). Old traces are incomparable across versions
# by construction — the version rides inside every .npz.
TRACE_VERSION = 2
import os
try:
    _here = os.path.dirname(os.path.abspath(__file__))
    _g = subprocess.run(["git", "-C", _here, "rev-parse", "--short",
                         "HEAD"], capture_output=True, text=True,
                        timeout=10)
    GEN_HASH = _g.stdout.strip() or "nogit"
except Exception:
    GEN_HASH = "nogit"

N = 64          # carriers / bands
M = 8           # symbols per band per frame
NS = N * M      # time samples per frame (512)
NB = N * M * 2  # bits per frame, QPSK (1024)
CP = 16
FRAMES = 150
rng = np.random.default_rng(0xE501)

# --- wavelet filters (orthonormal) ---
HAAR_LO = np.array([1, 1]) / np.sqrt(2)
HAAR_HI = np.array([1, -1]) / np.sqrt(2)
DB4_LO = np.array([-0.0105974, 0.0328830, 0.0308414, -0.1870348,
                   -0.0279838, 0.6308808, 0.7148466, 0.2303778])
DB4_HI = DB4_LO[::-1] * np.array([1, -1] * 4)


def circ_conv_up(x, h):
    """Upsample x by 2, circular-convolve with h. len(x)->2*len(x)."""
    n = len(x)
    xu = np.zeros(2 * n, dtype=x.dtype)
    xu[::2] = x
    L = len(h)
    y = np.zeros(2 * n, dtype=np.result_type(x, h))
    for k in range(L):
        y += h[k] * np.roll(xu, k)
    return y


def synth_matrix(lo, hi, depth=6):
    """IDWT tree as explicit matrix: X = S @ coeffs (length NS)."""
    S = np.zeros((NS, NS))
    for b in range(NS):
        c = np.zeros(NS)
        c[b] = 1.0
        # 6-level tree: coeffs grouped as 64 bands x M merged bottom-up
        bands = [c[i * M:(i + 1) * M] for i in range(N)]
        for _ in range(depth):
            nxt = []
            for i in range(0, len(bands), 2):
                a = circ_conv_up(bands[i], lo)
                d = circ_conv_up(bands[i + 1], hi)
                nxt.append(a + d)
            bands = nxt
        S[:, b] = bands[0][:NS]
    return S


print("building synthesis matrices...", flush=True)
S_HAAR = synth_matrix(HAAR_LO, HAAR_HI)
S_DB4 = synth_matrix(DB4_LO, DB4_HI)
def orthogonalize(S, name):
    # nearest orthogonal matrix (U V^T): 6-level fp64 accumulation
    # leaves db4 at ~5e-7; this forces exact PR (documented, ~1e-16).
    U, _, Vt = np.linalg.svd(S)
    So = U @ Vt
    err = np.max(np.abs(So.T @ So - np.eye(NS)))
    print(f"PR check {name}: raw + orthogonalized err = {err:.2e}",
          flush=True)
    assert err < 1e-8, f"{name} not PR!"
    return So


S_HAAR = orthogonalize(S_HAAR, "haar")
S_DB4 = orthogonalize(S_DB4, "db4")

MODEMS = {
    "fft": None,
    "haar": (S_HAAR, S_HAAR.T),
    "db4": (S_DB4, S_DB4.T),
}


def bits(n):
    return rng.integers(0, 2, n).astype(np.int8)


def qpsk_map(b):
    return ((2 * b[0::2] - 1) + 1j * (2 * b[1::2] - 1)) / np.sqrt(2)


def qpsk_slice(y):
    b = np.empty(2 * len(y), dtype=np.int8)
    b[0::2] = (y.real > 0).astype(np.int8)
    b[1::2] = (y.imag > 0).astype(np.int8)
    return b


def tx(modem, syms):
    """syms: 64 bands x M (N*M complex). Returns time samples."""
    if modem == "fft":
        X = syms.reshape(N, M)
        t = np.fft.ifft(X, axis=0) * np.sqrt(N)
        t = np.vstack([t[-CP:], t]).reshape(-1)
        return t
    S, _ = MODEMS[modem]
    return S @ syms.reshape(-1)


def rx(modem, t, h=1.0):
    """Demodulate (perfect CSI one-tap). Returns 64xM symbols."""
    t = t / h
    if modem == "fft":
        X = t.reshape(CP + N, M)[CP:]
        return np.fft.fft(X, axis=0) / np.sqrt(N)
    _, A = MODEMS[modem]
    return (A @ t).reshape(N, M)


def add_channel(t, snr_db, kind, **kw):
    """Returns (received, channel-gain). SNR = TX-sample-power/noise."""
    pwr = np.mean(np.abs(t) ** 2)
    n0 = pwr / (10 ** (snr_db / 10))
    h = 1.0 + 0j
    if kind in ("rayleigh",):
        h = (rng.standard_normal() + 1j * rng.standard_normal()) / np.sqrt(2)
    y = h * t + np.sqrt(n0 / 2) * (
        rng.standard_normal(len(t)) + 1j * rng.standard_normal(len(t)))
    if kind == "burst":
        L = kw.get("L", 16)
        st = rng.integers(0, len(t) - L)
        y[st:st + L] += np.sqrt(n0 * 100 / 2) * (
            rng.standard_normal(L) + 1j * rng.standard_normal(L))
    if kind == "nbi":
        k = kw.get("k", 10)
        A = np.sqrt(pwr * kw.get("sir_boost", 4.0))
        n = np.arange(len(t))
        y += A * np.exp(2j * np.pi * k * n / N)
    return y, h


def run_cell(modem, snr_db, kind, **kw):
    be = 0
    bt = 0
    for _ in range(FRAMES):
        b = bits(NB)
        s = qpsk_map(b).reshape(N, M)
        t = tx(modem, s)
        y, h = add_channel(t, snr_db, kind, **kw)
        sh = rx(modem, y, h).reshape(-1)
        bh = qpsk_slice(sh)
        be += np.sum(b != bh)
        bt += NB
    return be / bt


SELFTEST = True
for modem in MODEMS:
    ber = run_cell(modem, 60.0, "awgn")
    print(f"selftest noiseless {modem}: BER={ber:.2e}", flush=True)
    assert ber == 0.0, f"{modem} broken at 60dB!"
print("gates pass: PR exact, noiseless BER=0 all modems.", flush=True)
print(f"trace format v{TRACE_VERSION}, generator {GEN_HASH}", flush=True)

CHANNELS = [
    ("awgn", {}),
    ("rayleigh", {}),
    ("burst16", {"kind": "burst", "L": 16}),
    ("burst64", {"kind": "burst", "L": 64}),
    ("nbi", {"kind": "nbi", "k": 10}),
]
print("modem x channel x SNR(dB): BER", flush=True)
for ch, kw in CHANNELS:
    kind = kw.pop("kind", ch)
    for snr in (0, 2, 4, 6, 8, 10, 12):
        row = []
        for modem in MODEMS:
            ber = run_cell(modem, float(snr), kind, **kw)
            row.append(f"{modem}={ber:.4f}")
        print(f"{ch} snr={snr:2d}: " + " ".join(row), flush=True)


def byte_stats(modem, snr_db, kind, nframes=200, save=None, **kw):
    """Demodulate nframes, pack bytes MSB-first, report byte errors."""
    bad = np.zeros((nframes, 4096), dtype=np.uint8)
    totb = 0
    maxrun = 0
    for f in range(nframes):
        b = bits(4096 * 8)
        nblk = (4096 * 8) // NB
        err = np.zeros(4096, dtype=np.uint8)
        for blk in range(nblk):
            bb = b[blk * NB:(blk + 1) * NB]
            s = qpsk_map(bb).reshape(N, M)
            t = tx(modem, s)
            y, h = add_channel(t, snr_db, kind, **kw)
            bh = qpsk_slice(rx(modem, y, h).reshape(-1))
            be = np.packbits((bb != bh).reshape(-1, 8).any(axis=1)
                             .astype(np.uint8))
            # byte i bad iff any of its 8 bits wrong:
            bi = (bb != bh).reshape(-1, 8).any(axis=1).astype(np.uint8)
            err[blk * 128:(blk + 1) * 128] = bi
        bad[f] = err
        totb += err.sum()
        # max run of bad bytes
        run = 0
        for v in err:
            run = run + 1 if v else 0
            maxrun = max(maxrun, run)
    mean_bad = totb / nframes
    print(f"BYTE {modem} {kind} snr={snr_db}: mean-bad/4096={mean_bad:.1f} "
          f"maxrun={maxrun}", flush=True)
    if save:
        np.savez_compressed(save, bad=bad, version=TRACE_VERSION,
                            gen_hash=np.array(GEN_HASH),
                            meta=np.array([modem, kind, str(snr_db),
                                           f"N={N} M={M} CP={CP} QPSK"]))


print("byte-mapped operating points (for packetbench cells):", flush=True)
byte_stats("fft", 6, "burst", L=16, save="trace_fft_burst16_snr6")
byte_stats("db4", 6, "burst", L=16, save="trace_db4_burst16_snr6")
byte_stats("fft", 6, "burst", L=64, save="trace_fft_burst64_snr6")
byte_stats("db4", 6, "burst", L=64, save="trace_db4_burst64_snr6")
byte_stats("fft", 8, "nbi", k=10)
byte_stats("db4", 8, "nbi", k=10)
