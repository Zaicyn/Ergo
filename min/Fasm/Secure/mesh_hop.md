# Mesh-hop relay decomposition (instrument sketch)

Future Meshtastic-scale experiments. Transplant of the KonB-law
method (`min/actin_phasespace/KONB_LAW_RESULTS.md` §2): decompose
what a node receives into fresh vs relayed, measure the return
structure directly, and let the aggregate ratio be a *measurement*,
never a constant.

## Structural prediction (falsifiable)

Effective delivery at a node = bare link rate × [1 + G(mesh)],
where G is the relay-loop gain: the share of arrivals that are
re-presentations (relayed), not fresh originations. Predicted:
G grows with mesh density/size (more neighbors = more paths back),
and any "magic" delivery ratio at one density moves when density
moves — no thresholds, no numerology. If a fixed ratio survives a
density sweep, the prediction is wrong; say so.

## Instrument (per node, per packet)

Log row per arrival: `{frame_id, origin_id, first_seen_here (bool),
hop_count, rx_time, rssi, snr, verdict}` where verdict ∈
{clean, sec-fixed, parity-rebuilt, dropped}. `frame_id` = origin +
sequence (Meshtastic packet IDs already supply this — reuse them,
don't invent a header). `first_seen_here` comes from a local
seen-cache (fixed ring, 512 entries is plenty).

From the log, per node:

| channel | definition | analog |
|---|---|---|
| direct | hop_count == 1 (heard from origin) | direct cloud |
| local relay | 1st re-presentation, hop 2–3, short latency | local recycling |
| long relay | hop ≥ 4 or latency > mixing scale | long-latency returns |
| fully-mixed | seen-cache saturated, path untraceable | bath capture |

Mixing scale for the mesh = typical flood diameter in hops ×
per-hop airtime (measure, don't assume — the analog of their 24k
box-mixing calibration). Shares must sum to 1; publish the table,
not just the ratio.

## Topologies (sweep density deliberately)

Line (min relay) → grid → dense cluster (max relay), 3–8 Heltec
boards, fixed TX cadence from one origin. Same frame content our
codec already uses (known-answer scoring survives the trip).
Record RSSI/SNR per arrival for the link-quality covariate.

## Codec interaction (the interesting part)

Two repair placements, measure both: **end-to-end** (relays forward
bytes untouched, only the destination repairs — relay stream keeps
its damage shape) vs **per-hop repair** (each relay SEC-fixes before
forwarding — the relay stream gets *cleaned in transit*, so
downstream sees a different error shape than the air produced).
Prediction: per-hop repair raises effective delivery beyond what
end-to-end achieves at the same density, at the cost of per-hop
compute. This is a real design decision with a measured answer,
not a philosophy.

## Anti-numerology rules (imported)

- Sweep the parameter any claimed constant doesn't depend on
  (density, size, TX rate). A pinned ratio that moves is a curve.
- Integer-resolution check where cheap (hop counts are already
  integers — no binning excuses).
- Publish shares with uncertainties, not point ratios.
- Old traces incomparable across generator changes (trace-format
  versioning discipline from `phy_ofdm.py` applies to mesh logs
  too — version the log schema from day one).
