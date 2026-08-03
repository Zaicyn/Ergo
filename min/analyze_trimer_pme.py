#!/usr/bin/env python3
"""
Trimer PME Analysis — Li/Pokorný replication checks

Reads trimer_pme.log with two sections:
  # POSITION_SCAN — tip scan at Vs=790 mV: x I_tip Q w_singlet w_doublet w_other
  # BIAS_SWEEP    — Vs sweep at trimer center

Checks, mapped to the paper's claims:
  1. Discharge sequence: Q goes 2 -> 1 as tip crosses the cluster
  2. Trapped manifold: singly-occupied states dominate after threshold
     (this is their non-equilibrium occupancy = redirect "w component")
  3. NDC: |I| drops with increasing Vs at the discharge threshold
  4. Suppression tracks trapping: |I| anti-correlates with w_singlet
  5. Far-site trapping: current suppression where the occupied site
     is far from the tip (their Fig. 3 mechanism)
"""

import sys
import json


def parse_log(filename):
    sections = {}
    current = None
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                if 'POSITION_SCAN' in line:
                    current = 'scan'
                    sections[current] = []
                elif 'BIAS_SWEEP' in line:
                    current = 'sweep'
                    sections[current] = []
                elif 'POROSITY' in line:
                    # "# POROSITY G_HOP=1.0E-04  cols: ..."
                    tag = [p for p in line.split() if p.startswith('G_HOP=')]
                    g = float(tag[0].split('=')[1]) if tag else 0.0
                    current = f'porosity:{g}'
                    sections[current] = []
                elif 'TEMP_SWEEP' in line or 'TEMP_SCAN' in line:
                    # "# TEMP_SWEEP KT=0.2200  cols: ..."
                    kind = 'temp_sweep' if 'TEMP_SWEEP' in line else 'temp_scan'
                    tag = [p for p in line.split() if p.startswith('KT=')]
                    kt = float(tag[0].split('=')[1]) if tag else 0.0
                    current = f'{kind}:{kt}'
                    sections[current] = []
                else:
                    current = None
                continue
            if current is None:
                continue
            parts = line.split()
            if len(parts) not in (6, 7):
                continue
            try:
                v = [float(p) for p in parts]
            except ValueError:
                continue
            sections[current].append({
                'x': v[0], 'i_tip': v[1], 'q': v[2],
                'w_sing': v[3], 'w_dbl': v[4], 'w_other': v[5],
                'hole_near': v[6] if len(v) == 7 else None,
            })
    return sections


def main():
    filename = "trimer_pme.log"
    try:
        sections = parse_log(filename)
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        sys.exit(1)

    scan = sections.get('scan', [])
    sweep = sections.get('sweep', [])
    if len(scan) < 10 or len(sweep) < 5:
        print(f"Insufficient data: scan={len(scan)} rows, sweep={len(sweep)} rows")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("TRIMER PME ANALYSIS — Li/Pokorný replication")
    print("=" * 70)

    # ── 1. Discharge sequence along position scan ────────────────
    q_start = scan[0]['q']
    q_min = min(s['q'] for s in scan)
    discharge = q_start > 1.9 and q_min < 1.1

    print(f"\n1. Discharge sequence (position scan, Vs=790 mV):")
    print(f"   Q: {q_start:.3f} (far) -> {q_min:.3f} (min)")
    print(f"   Paper: Q = 2 far from tip, -> 1 near center at high Vs")

    # ── 2. Trapped singlet manifold ──────────────────────────────
    w_sing_max = max(s['w_sing'] for s in scan)
    x_at_max = max(scan, key=lambda s: s['w_sing'])['x']
    trapped = w_sing_max > 0.9

    print(f"\n2. Non-equilibrium occupancy of singlet manifold:")
    print(f"   w_singlet max = {w_sing_max:.4f} at x = {x_at_max:.2f} nm")
    print(f"   Paper: population trapped in |100>,|010>,|001> after threshold")

    # ── 3. NDC in bias sweep ─────────────────────────────────────
    ndc_points = []
    for i in range(1, len(sweep)):
        di = abs(sweep[i]['i_tip']) - abs(sweep[i - 1]['i_tip'])
        dv = sweep[i]['x'] - sweep[i - 1]['x']
        if di < -0.1 * abs(sweep[i - 1]['i_tip']):  # >10% drop
            ndc_points.append((sweep[i - 1]['x'], sweep[i]['x'], di))

    ndc_exists = len(ndc_points) > 0
    print(f"\n3. NDC (bias sweep at center):")
    if ndc_points:
        for v0, v1, di in ndc_points:
            print(f"   |I| drops {di:+.4f} between {v0:.0f} and {v1:.0f} mV")
    else:
        print("   No significant |I| drop found")
    print(f"   Paper: NDC dip near Vs = 760 mV at center")

    # Threshold voltage (Q crosses 1.5)
    thresh = None
    for i in range(1, len(sweep)):
        if sweep[i - 1]['q'] > 1.5 >= sweep[i]['q']:
            thresh = (sweep[i - 1]['x'] + sweep[i]['x']) / 2
    if thresh:
        print(f"   Discharge threshold: Vs ≈ {thresh:.0f} mV (paper: ~590 mV at center)")

    # ── 4. Suppression tracks trapping ───────────────────────────
    i_abs = [abs(s['i_tip']) for s in sweep]
    w_sing = [s['w_sing'] for s in sweep]
    r_iw = _pearson(i_abs, w_sing)
    suppression_tracks = r_iw < -0.5

    print(f"\n4. Current suppression vs trapped population (sweep):")
    print(f"   Pearson r(|I|, w_singlet) = {r_iw:+.3f}")
    print(f"   Claim: as w (trapped) rises, current falls")

    # ── 5. Far-site trapping signature in scan ───────────────────
    # Local minimum of |I| past the center where singlet pins at far site
    i_scan = [abs(s['i_tip']) for s in scan]
    xs = [s['x'] for s in scan]
    dips = []
    for i in range(1, len(scan) - 1):
        if i_scan[i] < i_scan[i - 1] * 0.85 and i_scan[i] < i_scan[i + 1]:
            dips.append(xs[i])
    far_site_signature = len(dips) > 0

    print(f"\n5. Far-site trapping (position scan):")
    if dips:
        print(f"   Current suppression dips at x = {['%.2f' % d for d in dips]} nm")
    else:
        print("   No localized suppression dip found")
    print(f"   Paper: current suppressed where empty/occupied site is far from tip")

    # ── 6. Porosity ablation ─────────────────────────────────────
    # Per G_HOP: mean |I| and w_singlet in the trapped region
    # (x in [0.8, 1.1], Q ~ 1), plus a control region (x in [0.2, 0.5]).
    porosity = {float(k.split(':')[1]): v
                for k, v in sections.items() if k.startswith('porosity:')}
    porosity_results = []
    if porosity:
        print(f"\n6. Porosity ablation (position scans at Vs=790 mV):")
        print(f"   {'G_HOP':>10} {'|I| trapped':>12} {'w_sing':>8}"
              f" {'Q trapped':>10} {'|I| control':>12}")
        for g in sorted(porosity):
            rows = porosity[g]
            trapped_rows = [r for r in rows if 0.8 <= r['x'] <= 1.1]
            control_rows = [r for r in rows if 0.2 <= r['x'] <= 0.5]
            i_tr = sum(abs(r['i_tip']) for r in trapped_rows) / max(len(trapped_rows), 1)
            w_tr = sum(r['w_sing'] for r in trapped_rows) / max(len(trapped_rows), 1)
            q_tr = sum(r['q'] for r in trapped_rows) / max(len(trapped_rows), 1)
            i_ct = sum(abs(r['i_tip']) for r in control_rows) / max(len(control_rows), 1)
            porosity_results.append({
                'g_hop': g, 'i_trapped': i_tr, 'w_sing_trapped': w_tr,
                'q_trapped': q_tr, 'i_control': i_ct,
            })
            print(f"   {g:10.1E} {i_tr:12.6f} {w_tr:8.4f}"
                  f" {q_tr:10.4f} {i_ct:12.6f}")

    # ── 7. Temperature sweep — wall solidity ─────────────────────
    # Per KT: NDC depth (center bias sweep) and trapped w / |I|
    # (position scan region x in [0.8, 1.1]).
    temp_sweeps = {float(k.split(':')[1]): v
                   for k, v in sections.items() if k.startswith('temp_sweep:')}
    temp_scans = {float(k.split(':')[1]): v
                  for k, v in sections.items() if k.startswith('temp_scan:')}
    temp_results = []
    if temp_sweeps:
        print(f"\n7. Temperature sweep — wall solidity:")
        print(f"   {'KT':>8} {'NDC depth':>10} {'w_plateau':>10}"
              f" {'w_trapped':>10} {'|I| trapped':>12}")
        for kt in sorted(temp_sweeps):
            rows = temp_sweeps[kt]
            # NDC depth: largest consecutive |I| drop
            ndc_depth = 0.0
            for i in range(1, len(rows)):
                drop = abs(rows[i - 1]['i_tip']) - abs(rows[i]['i_tip'])
                ndc_depth = max(ndc_depth, drop)
            w_plateau = rows[-1]['w_sing']
            tr = [r for r in temp_scans.get(kt, []) if 0.8 <= r['x'] <= 1.1]
            w_tr = sum(r['w_sing'] for r in tr) / max(len(tr), 1)
            i_tr = sum(abs(r['i_tip']) for r in tr) / max(len(tr), 1)
            temp_results.append({
                'kt': kt, 'ndc_depth': ndc_depth, 'w_plateau': w_plateau,
                'w_trapped': w_tr, 'i_trapped': i_tr,
            })
            print(f"   {kt:8.4f} {ndc_depth:10.6f} {w_plateau:10.4f}"
                  f" {w_tr:10.4f} {i_tr:12.6f}")

    # ── Verdicts ─────────────────────────────────────────────────
    tests = {
        "Discharge sequence Q: 2 -> 1": discharge,
        "Singlet (trapped) manifold dominates post-threshold": trapped,
        "NDC: |I| drops at discharge threshold": ndc_exists,
        "Suppression tracks trapped population (r < -0.5)": suppression_tracks,
        "Far-site trapping signature in scan": far_site_signature,
    }

    if len(porosity_results) >= 2:
        first, last = porosity_results[0], porosity_results[-1]
        releases_current = last['i_trapped'] > 1.5 * first['i_trapped']
        drains_trap = first['w_sing_trapped'] - last['w_sing_trapped'] > 0.2
        control_stable = abs(last['i_control'] - first['i_control']) \
            < 0.15 * first['i_control']
        tests["Porosity releases suppressed current (trapped region)"] = releases_current
        tests["Porosity drains trapped population"] = drains_trap
        tests["Control region unaffected by porosity"] = control_stable

    if len(temp_results) >= 2:
        base, hot = temp_results[0], temp_results[-1]
        ndc_melts = hot['ndc_depth'] < 0.3 * base['ndc_depth']
        trap_melts = base['w_trapped'] - hot['w_trapped'] > 0.2
        tests["Walls melt with temperature (NDC depth collapses)"] = ndc_melts
        tests["Walls melt with temperature (trapped w drains)"] = trap_melts

    print(f"\n" + "=" * 70)
    print("REPLICATION CHECKS")
    print("=" * 70)
    for name, result in tests.items():
        print(f"{'✓ PASS' if result else '✗ FAIL'}: {name}")

    print(f"\n{'=' * 70}")
    if all(tests.values()):
        print("MODEL REPLICATES PAPER MECHANISMS")
    else:
        print("PARTIAL REPLICATION: see details above")
    print("=" * 70 + "\n")

    summary = {
        'q_far': q_start, 'q_min': q_min,
        'w_singlet_max': w_sing_max, 'w_singlet_max_x': x_at_max,
        'ndc_points': ndc_points,
        'discharge_threshold_mv': thresh,
        'pearson_i_vs_w_singlet': r_iw,
        'far_site_dips_nm': dips,
        'porosity_ablation': porosity_results,
        'temperature_sweep': temp_results,
        'checks': tests,
        'all_pass': all(tests.values()),
    }
    with open('trimer_pme_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("Summary saved to trimer_pme_summary.json")


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
