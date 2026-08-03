#!/usr/bin/env python3
"""
Redirect Topology Analysis — Minimal Version

Reads redirect_transitions.log from the sim and tests whether the theory holds:
  1. Are redirects consistent (internal rearrangements > charge transfers)?
  2. Does w-accumulation (orthogonal rise) happen on >90% of redirects?
  3. What's the redirect topology?
"""

import sys
import json
from collections import defaultdict

def main():
    filename = "redirect_transitions.log"
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        sys.exit(1)

    # Parse log
    transitions = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('!'):
            continue
        
        parts = line.split()
        if len(parts) < 7:
            continue
        
        try:
            trans = {
                'frame': int(parts[0]),
                'node': int(parts[1]),
                'from_state': int(parts[2]),
                'to_state': int(parts[3]),
                'phase_spread': float(parts[4]),
                'w_rise': float(parts[5]),
                'trans_type': int(parts[6])
            }
            transitions.append(trans)
        except (ValueError, IndexError):
            continue

    if not transitions:
        print(f"No transitions found in {filename}")
        sys.exit(1)

    # ─────────────────────────────────────────────────────────────
    # Classify transitions
    # ─────────────────────────────────────────────────────────────

    internal_rearrangements = [t for t in transitions if t['trans_type'] == 1]
    charge_adds = [t for t in transitions if t['trans_type'] == 2]
    charge_removes = [t for t in transitions if t['trans_type'] == 3]

    # ─────────────────────────────────────────────────────────────
    # Build redirect topology matrix
    # ─────────────────────────────────────────────────────────────

    redirect_matrix = defaultdict(int)
    redirect_stats = defaultdict(lambda: {
        'count': 0,
        'w_rises': [],
        'phase_spreads': []
    })

    for trans in transitions:
        from_state = trans['from_state']
        to_state = trans['to_state']
        key = f"|{from_state}⟩ → |{to_state}⟩"
        
        redirect_matrix[key] += 1
        redirect_stats[key]['count'] += 1
        redirect_stats[key]['w_rises'].append(trans['w_rise'])
        redirect_stats[key]['phase_spreads'].append(trans['phase_spread'])

    # ─────────────────────────────────────────────────────────────
    # Statistics
    # ─────────────────────────────────────────────────────────────

    all_w_rises = [t['w_rise'] for t in transitions]
    
    print("\n" + "="*70)
    print("REDIRECT TOPOLOGY ANALYSIS")
    print("="*70)

    print(f"\nTotal transitions: {len(transitions)}")
    print(f"  Internal rearrangements: {len(internal_rearrangements)}")
    print(f"  Charge additions: {len(charge_adds)}")
    print(f"  Charge removals: {len(charge_removes)}")
    print(f"  Ratio (internal/charge): {len(internal_rearrangements)/max(len(charge_adds)+len(charge_removes), 1):.2f}")

    print(f"\nOrthogonal (w) component rise:")
    print(f"  Mean: {sum(all_w_rises)/len(all_w_rises):.4f}")
    print(f"  Std:  {_std(all_w_rises):.4f}")
    print(f"  Min:  {min(all_w_rises):.4f}")
    print(f"  Max:  {max(all_w_rises):.4f}")
    print(f"  % > 0.05: {100*sum(1 for x in all_w_rises if x > 0.05)/len(all_w_rises):.1f}%")
    print(f"  % > 0.10: {100*sum(1 for x in all_w_rises if x > 0.10)/len(all_w_rises):.1f}%")

    print(f"\nTop 10 redirect types:")
    for key, count in sorted(redirect_matrix.items(), key=lambda x: -x[1])[:10]:
        stats = redirect_stats[key]
        w_values = stats['w_rises']
        mean_w = sum(w_values) / len(w_values) if w_values else 0
        std_w = _std(w_values) if len(w_values) > 1 else 0
        pct_above_005 = 100 * sum(1 for v in w_values if v > 0.05) / len(w_values) if w_values else 0
        
        print(f"  {key:20s}  count={count:6d}  w_mean={mean_w:.4f}±{std_w:.4f}  %>0.05={pct_above_005:5.1f}%")

    # ─────────────────────────────────────────────────────────────
    # Test criteria
    # ─────────────────────────────────────────────────────────────

    print(f"\n" + "="*70)
    print("THEORY TEST RESULTS")
    print("="*70)

    tests = {
        "Internal redirects >> charge transfers": 
            len(internal_rearrangements) > 3 * (len(charge_adds) + len(charge_removes)),
        "W-component rises on >90% of redirects": 
            100*sum(1 for x in all_w_rises if x > 0.05)/len(all_w_rises) > 90,
        "W-rise mean > 0.05":
            sum(all_w_rises)/len(all_w_rises) > 0.05,
        "Redirects show consistent patterns":
            len(redirect_matrix) > 3 and len(redirect_matrix) < 20,
    }

    for test_name, result in tests.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_pass = all(tests.values())
    print(f"\n{'='*70}")
    if all_pass:
        print("THEORY SUPPORTED: Redirects are topological, w-accumulation is real")
    else:
        print("THEORY UNCERTAIN: Some criteria not met; see details above")
    print("="*70 + "\n")

    # ─────────────────────────────────────────────────────────────
    # Save summary JSON
    # ─────────────────────────────────────────────────────────────

    summary = {
        'total_transitions': len(transitions),
        'internal_rearrangements': len(internal_rearrangements),
        'charge_additions': len(charge_adds),
        'charge_removals': len(charge_removes),
        'orthogonal_stats': {
            'mean': sum(all_w_rises)/len(all_w_rises),
            'std': _std(all_w_rises),
            'min': min(all_w_rises),
            'max': max(all_w_rises),
            'pct_above_005': 100*sum(1 for x in all_w_rises if x > 0.05)/len(all_w_rises),
            'pct_above_010': 100*sum(1 for x in all_w_rises if x > 0.10)/len(all_w_rises),
        },
        'redirect_matrix': dict(redirect_matrix),
        'theory_tests': tests,
        'all_pass': all_pass
    }

    with open('redirect_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print("Summary saved to redirect_summary.json")

def _std(values):
    """Compute standard deviation"""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    var = sum((x - mean)**2 for x in values) / len(values)
    return var ** 0.5

if __name__ == '__main__':
    main()
