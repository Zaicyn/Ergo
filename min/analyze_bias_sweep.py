#!/usr/bin/env python3
"""
Redirect Bias Sweep Analysis — Deepseek Protocol Tests 2 + 4

Reads redirect_bias_sweep.log (one line per bias step:
  bias w_base w_peak current coherence_peak w_final coherence_final)

Test 2: Does w-accumulation correlate with the NDC regime?
  - NDC regime = bias range past the current peak where dI/dBias < 0
  - Theory: steepest w accumulation happens inside the NDC regime

Test 4: Does phase coherence predict redirect reversibility?
  - returned fraction = (w_peak - w_final) / w_peak
    (fraction of the forbidden population that flows back on release)
  - Theory: reversibility correlates with coherence at release
"""

import sys
import json


def main():
    filename = "redirect_bias_sweep.log"

    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        sys.exit(1)

    steps = []
    for line in lines:
        parts = line.split()
        if len(parts) != 7:
            continue
        try:
            vals = [float(p) for p in parts]
        except ValueError:
            continue
        steps.append({
            'bias': vals[0],
            'w_base': vals[1],
            'w_peak': vals[2],
            'current': vals[3],
            'coherence_peak': vals[4],
            'w_final': vals[5],
            'coherence_final': vals[6],
        })

    if len(steps) < 5:
        print(f"Not enough sweep steps parsed ({len(steps)}) in {filename}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("REDIRECT BIAS SWEEP ANALYSIS (Tests 2 + 4)")
    print("=" * 70)

    print(f"\nSweep steps parsed: {len(steps)}")
    print(f"Bias range: {steps[0]['bias']:.2f} .. {steps[-1]['bias']:.2f}")

    # ─────────────────────────────────────────────────────────────
    # Sanity: does w accumulate at all?
    # ─────────────────────────────────────────────────────────────

    w_first = steps[0]['w_peak']
    w_last = steps[-1]['w_peak']
    print(f"\nw accumulation: w_peak goes {w_first:.4f} (bias={steps[0]['bias']:.2f})"
          f" -> {w_last:.4f} (bias={steps[-1]['bias']:.2f})")

    # ─────────────────────────────────────────────────────────────
    # Test 2: w-accumulation vs NDC regime
    # ─────────────────────────────────────────────────────────────

    # Current peak = onset of NDC (past this, dI/dBias < 0)
    i_peak_idx = max(range(len(steps)), key=lambda i: steps[i]['current'])
    i_peak_bias = steps[i_peak_idx]['bias']
    i_min_idx = min(range(i_peak_idx, len(steps)),
                    key=lambda i: steps[i]['current'])
    i_min_bias = steps[i_min_idx]['bias']

    # Steepest w rise between consecutive steps
    w_slopes = [steps[i + 1]['w_peak'] - steps[i]['w_peak']
                for i in range(len(steps) - 1)]
    steep_idx = max(range(len(w_slopes)), key=lambda i: w_slopes[i])
    steep_bias = steps[steep_idx + 1]['bias']

    print(f"\nTest 2 — w-accumulation vs NDC:")
    print(f"  Current peak (NDC onset): bias = {i_peak_bias:.2f}"
          f"  (I = {steps[i_peak_idx]['current']:.4f})")
    print(f"  Current minimum after peak: bias = {i_min_bias:.2f}"
          f"  (I = {steps[i_min_idx]['current']:.4f})")
    print(f"  Steepest w rise: bias = {steep_bias:.2f}"
          f"  (dw = {w_slopes[steep_idx]:.4f}/step)")

    ndc_exists = 0 < i_peak_idx < len(steps) - 1
    w_accumulates = w_last > w_first + 0.2
    w_steepest_in_ndc = steep_bias >= i_peak_bias - 1e-9

    # ─────────────────────────────────────────────────────────────
    # Test 4: coherence vs reversibility
    # ─────────────────────────────────────────────────────────────

    returned = []
    coherences = []
    for s in steps:
        if s['w_peak'] < 1e-6:
            continue
        frac = (s['w_peak'] - s['w_final']) / s['w_peak']
        returned.append(frac)
        coherences.append(s['coherence_peak'])

    r_pearson = _pearson(coherences, returned) if len(returned) > 2 else 0.0

    # Median split for a robust read
    med_coh = sorted(coherences)[len(coherences) // 2]
    hi = [f for c, f in zip(coherences, returned) if c >= med_coh]
    lo = [f for c, f in zip(coherences, returned) if c < med_coh]
    hi_mean = sum(hi) / len(hi) if hi else 0.0
    lo_mean = sum(lo) / len(lo) if lo else 0.0

    print(f"\nTest 4 — coherence vs reversibility:")
    print(f"  Returned fraction = (w_peak - w_final)/w_peak:")
    print(f"    {'bias':>6} {'w_peak':>8} {'w_final':>8} {'coh':>6} {'returned':>9}")
    for s in steps:
        frac = (s['w_peak'] - s['w_final']) / s['w_peak'] if s['w_peak'] > 1e-6 else float('nan')
        print(f"    {s['bias']:6.2f} {s['w_peak']:8.4f} {s['w_final']:8.4f}"
              f" {s['coherence_peak']:6.3f} {frac:9.3f}")
    print(f"\n  Pearson r (coherence, returned) = {r_pearson:+.3f}")
    print(f"  Median split: high-coherence mean returned = {hi_mean:.3f},"
          f" low-coherence = {lo_mean:.3f}")

    coherence_correlates = abs(r_pearson) > 0.5

    # ─────────────────────────────────────────────────────────────
    # Verdicts
    # ─────────────────────────────────────────────────────────────

    tests = {
        "W accumulates under bias": w_accumulates,
        "NDC regime exists (interior current peak)": ndc_exists,
        "Test 2: steepest w rise inside NDC regime": w_steepest_in_ndc,
        "Test 4: coherence correlates with reversibility (|r| > 0.5)":
            coherence_correlates,
    }

    print(f"\n" + "=" * 70)
    print("THEORY TEST RESULTS")
    print("=" * 70)
    for name, result in tests.items():
        print(f"{'✓ PASS' if result else '✗ FAIL'}: {name}")

    print(f"\n{'=' * 70}")
    if all(tests.values()):
        print("THEORY SUPPORTED: w-accumulation tracks NDC, coherence predicts reversal")
    else:
        print("THEORY UNCERTAIN: Some criteria not met; see details above")
    print("=" * 70 + "\n")

    summary = {
        'n_steps': len(steps),
        'w_first': w_first,
        'w_last': w_last,
        'ndc_onset_bias': i_peak_bias,
        'ndc_min_bias': i_min_bias,
        'steepest_w_rise_bias': steep_bias,
        'coherence_reversibility_pearson_r': r_pearson,
        'returned_high_coherence_mean': hi_mean,
        'returned_low_coherence_mean': lo_mean,
        'theory_tests': tests,
        'all_pass': all(tests.values()),
        'steps': steps,
    }
    with open('redirect_bias_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("Summary saved to redirect_bias_summary.json")


def _pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return 0.0
    return cov / (vx * vy) ** 0.5


if __name__ == '__main__':
    main()
