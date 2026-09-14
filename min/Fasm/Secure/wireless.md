# Wireless: FFT-OFDM vs DWT-OFDM for this stack

Which physical layer should carry these frames over the air? Measured
answer from `phy_ofdm.py` (N=64 carriers, QPSK, commit `d414ed7`):
it depends on what hurts you — bursts or tones — and the two schemes
trade them off almost exactly.

## Summary

All three modems (FFT with cyclic prefix, Haar-wavelet, db4-wavelet)
are identical on clean channels — as orthonormality demands. They
diverge the moment the channel gets hostile, in opposite directions:
DWT contains impulse bursts in time; FFT quarantines narrowband
tones in frequency. Neither wins everywhere. db4 sits in the middle
on both axes and is the sane default if you must pick one blind.

## Pros and cons

**FFT-OFDM (the incumbent).**
Pro: exact subcarrier grid quarantines a jammed tone to ~1/64th of
symbols (measured floor 0.008–0.013 vs 0.06–0.12 for wavelets);
decades of hardware, silicon, and driver support; simplest DSP.
Con: pays 25% cyclic-prefix airtime on every frame (640 samples per
512 symbols — pure overhead DWT doesn't spend); smears every impulse
burst across all subcarriers (~2.4× the BER of Haar under bursts,
with bad-byte runs up to 170 vs ~20).

**Haar DWT-OFDM (the specialist).**
Pro: best burst containment measured (0.108 vs FFT's 0.255 at 6 dB,
64-sample bursts); simplest wavelet (2-tap filters, cheapest DSP);
no cyclic prefix. Con: worst tone behavior (0.118 — a boxcar in time
is a wide sinc in frequency, so one tone leaks everywhere); blocky
spectral edges need filtering for regulatory masks.

**db4 DWT-OFDM (the compromise).**
Pro: second-best on both axes (bursts 0.134, tone 0.063); smooth
enough spectrally to transmit legally without heroic filtering; no
cyclic prefix. Con: best at nothing — loses to Haar on bursts, to
FFT on tones; 8-tap filters cost ~4× Haar's multiply budget
(still trivial next to an FFT at these sizes).

**Recommendation by environment:** fading + impulse noise
(industrial, automotive, powerline-adjacent) → db4, Haar if tones
are known-absent. Jammed or crowded spectrum (a tone squatting your
band) → FFT. Clean lab link → identical, pick by silicon cost, and
pocket DWT's 25% airtime saving.

## What this means for our layer

Our codec eats byte-error *shapes*, and the PHY decides the shape.
Byte-mapped at 6 dB, 64-sample bursts: FFT leaves 3416/4096 bytes
bad in runs up to 170 (unrecoverable, resend territory); db4 leaves
2530 bad in runs up to 23 (partial credit still meaningful).
Tone at 8 dB: FFT 254 bad bytes in runs of 5 (SEC-fixable!); Haar
810 (struggling). Replay traces live in `traces/` (git-ignored by
repo convention — regenerate byte-identically with `python3
phy_ofdm.py`, fixed seed). Feeding them through `packetbench` gives
the full PHY→link goodput number; not yet wired, traces are ready.

## Hardware notes

- **Heltec WiFi LoRa 32 (V3) + open firmware: yes, for OUR layer.**
  Correction to an earlier version of this note: the firmware
  ecosystem is fully open (Meshtastic GPL, Arduino/PlatformIO/
  ESP-IDF/CircuitPython, Heltec libs, RadioLib for the SX1262) —
  only the *modulation* is fixed-function (LoRa CSS + (G)FSK in
  SX1262 silicon; no driver can make it emit OFDM). That boundary
  still rules out DWT-vs-FFT over these radios, but the openness
  buys four real experiments, cheapest first:
  1. **Link-characterization sweep** (two boards, PlatformIO +
     RadioLib): sweep spreading factor (SF7–12), bandwidth, coding
     rate; log PER/RSSI/SNR per setting. Maps straight onto our
     SP/BU/LO cells with real RF numbers.
  2. **CSS vs FSK on the same link.** The SX1262 does both —
     an honest modem comparison this hardware *can* run.
  3. **Meshtastic as carrier.** Open mesh + telemetry + Python/MQTT
     API: plug our parity/commitment in as a module and test
     multi-hop repair with real interference.
  4. **Embedded pktcore port.** Our C codec is plain C99 — port to
     ESP-IDF/Arduino (swap sockets for RadioLib send/recv +
     timers) for a true field test of handshake/tiers/codec.
- **Real comparison needs SDR:** one ADALM-Pluto (~$150–200,
  full-duplex loopback) for BER-vs-SNR, two units or Pluto+HackRF
  for two-node over-the-air with our stack on top. Sim first (done),
  Pluto if the sim margins justify it — the burst margin does, the
  tone margin says bring FFT firmware too.

## Technical breakdown

Setup: 64 bands × 8 symbols/frame (512 samples, 1024 bits QPSK);
flat Rayleigh fading with perfect-CSI one-tap EQ (exact for both
under flat fading); SNR = mean TX-sample power / noise-sample power
(CP overhead counted against FFT fairly); bursts = 10×-power noise
over L contiguous samples every frame; NBI = one tone at subcarrier
10, 4× signal power. DWT via circular Mallat trees as explicit
512×512 synthesis matrices, SVD-orthogonalized (raw db4 accumulates
~5e-7 fp error over 6 levels; orthogonalized to ~1e-15, documented
in-script). Gates: PR exact algebraically; noiseless BER = 0 on all
three modems or abort.

BER (rows: SNR 0/6/12 dB):

| channel | FFT | Haar | db4 |
|---|---|---|---|
| AWGN 0/6/12 | .159/.023/.000 | .158/.023/.000 | .158/.023/.000 |
| Rayleigh | .218/.093/.023 | .209/.099/.025 | .212/.102/.030 |
| burst16 | .288/.137/.024 | .195/.070/.028 | .217/.085/.028 |
| burst64 | .369/.255/.116 | .228/.108/.064 | .258/.134/.071 |
| NBI tone | .164/.031/.007 | .227/.128/.116 | .192/.079/.055 |

Byte maps (bad/4096, max run): burst16@6dB FFT 2662/69 vs db4
1921/15; burst64 FFT 3416/170 vs db4 2531/23; NBI@8dB FFT 254/5 vs
db4 810/5. Note FFT's NBI floor ≈ 1/64 × ½ (exactly the dead
subcarrier — theory and measurement agreeing to the third decimal).
