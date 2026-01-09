#!/usr/bin/env python3
"""
Quantum Secret Sharing Experiment Analysis
Analyzes results from QNE experiments and generates research outputs
"""

import json
import sys
from pathlib import Path

def load_results(results_file):
    """Load experiment results from JSON file"""
    with open(results_file, 'r') as f:
        return json.load(f)

def analyze_single_experiment(results):
    """Analyze a single experiment's results"""
    
    # Extract data from the first round
    round_data = results[0]['round_result'][0]
    
    alice_data = round_data['app_alice']
    bob_data = round_data['app_bob']
    charlie_data = round_data['app_charlie']
    
    # Basic statistics
    total_rounds = alice_data['total_rounds']
    valid_rounds = alice_data['valid_rounds']
    key_rate = alice_data['key_rate']
    
    print("=" * 70)
    print("QUANTUM SECRET SHARING EXPERIMENT ANALYSIS")
    print("=" * 70)
    print()
    
    # Section 1: Protocol Efficiency
    print("📊 PROTOCOL EFFICIENCY")
    print("-" * 70)
    print(f"Total rounds executed:        {total_rounds}")
    print(f"Valid rounds (even Y count):  {valid_rounds}")
    print(f"Invalid rounds discarded:     {total_rounds - valid_rounds}")
    print(f"Key generation rate:          {key_rate:.2%}")
    print(f"Expected theoretical rate:    ~50% (random bases)")
    print()
    
    # Section 2: Basis Distribution
    print("🎲 BASIS SELECTION ANALYSIS")
    print("-" * 70)
    
    alice_bases = alice_data['sample_bases']
    bob_bases = bob_data['sample_bases']
    charlie_bases = charlie_data['sample_bases']
    
    for party, bases in [("Alice", alice_bases), ("Bob", bob_bases), ("Charlie", charlie_bases)]:
        x_count = bases.count('X')
        y_count = bases.count('Y')
        x_pct = x_count / len(bases) * 100
        y_pct = y_count / len(bases) * 100
        print(f"{party:8} | X: {x_count:2}/10 ({x_pct:5.1f}%)  |  Y: {y_count:2}/10 ({y_pct:5.1f}%)")
    
    print(f"\n{'Expected:':8} | X: ~50%  |  Y: ~50% (random selection)")
    print()
    
    # Section 3: Correlation Analysis (GHZ Property)
    print("🔗 GHZ CORRELATION VERIFICATION")
    print("-" * 70)
    
    alice_bits = alice_data['sample_bits']
    bob_bits = bob_data['sample_bits']
    charlie_bits = charlie_data['sample_bits']
    
    correlations = []
    valid_checks = []
    
    for i in range(len(alice_bases)):
        y_count = [alice_bases[i], bob_bases[i], charlie_bases[i]].count('Y')
        is_valid = (y_count % 2 == 0)
        
        if is_valid:
            # For valid rounds, check GHZ correlation: A ⊕ B ⊕ C = 0
            xor_result = alice_bits[i] ^ bob_bits[i] ^ charlie_bits[i]
            correlations.append(xor_result)
            valid_checks.append((i, alice_bases[i], bob_bases[i], charlie_bases[i], 
                               alice_bits[i], bob_bits[i], charlie_bits[i], xor_result))
    
    print("Round | Bases (A,B,C) | Results (A,B,C) | A⊕B⊕C | Expected")
    print("-" * 70)
    
    for check in valid_checks[:10]:  # Show first 10
        round_num, a_b, b_b, c_b, a_r, b_r, c_r, xor = check
        expected = "✓ 0" if xor == 0 else "✗ should be 0"
        status = "✓" if xor == 0 else "✗"
        print(f"  {round_num:2}  |  {a_b},{b_b},{c_b}     |   {a_r},{b_r},{c_r}      |   {xor}   | {status} {expected}")
    
    if len(correlations) > 0:
        correct_correlations = correlations.count(0)
        correlation_accuracy = correct_correlations / len(correlations)
        
        print()
        print(f"Valid rounds with correct correlation (XOR=0): {correct_correlations}/{len(correlations)}")
        print(f"Correlation accuracy: {correlation_accuracy:.2%}")
        print(f"Expected for ideal GHZ state: 100%")
        print(f"Deviation indicates: noise, decoherence, or implementation issues")
    
    print()
    
    # Section 4: Secret Recovery Simulation
    print("🔐 SECRET RECOVERY DEMONSTRATION")
    print("-" * 70)
    print("Demonstrating that Bob & Charlie can recover Alice's secret:")
    print()
    
    recovery_success = 0
    for i in range(len(valid_checks)):
        round_num, a_b, b_b, c_b, a_r, b_r, c_r, xor = valid_checks[i]
        
        # Bob and Charlie recover Alice's bit: alice = bob ⊕ charlie (when XOR=0)
        recovered = b_r ^ c_r
        matches = (recovered == a_r)
        recovery_success += matches
        
        if i < 5:  # Show first 5
            status = "✓" if matches else "✗"
            print(f"Round {round_num}: Bob={b_r}, Charlie={c_r} → Recovered={recovered} | Alice={a_r} {status}")
    
    recovery_rate = recovery_success / len(valid_checks) if valid_checks else 0
    print()
    print(f"Recovery success rate: {recovery_success}/{len(valid_checks)} ({recovery_rate:.2%})")
    print()
    
    # Section 5: Research Insights
    print("🔬 RESEARCH INSIGHTS")
    print("-" * 70)
    
    # Insight 1: Key rate analysis
    deviation = abs(key_rate - 0.5)
    if deviation < 0.05:
        print("✓ Key rate close to theoretical 50% - good random basis selection")
    else:
        print(f"⚠ Key rate deviates by {deviation:.1%} from expected 50%")
    
    # Insight 2: Correlation accuracy
    if len(correlations) > 0:
        if correlation_accuracy > 0.95:
            print("✓ High correlation accuracy - GHZ state well-preserved")
        elif correlation_accuracy > 0.85:
            print("⚠ Moderate correlation accuracy - some noise present")
        else:
            print("✗ Low correlation accuracy - significant noise or errors")
        
        # Estimate noise level from correlation errors
        error_rate = 1 - correlation_accuracy
        print(f"  Estimated error rate: {error_rate:.2%}")
    
    # Insight 3: Basis randomness
    all_bases = alice_bases + bob_bases + charlie_bases
    x_total = all_bases.count('X')
    total_bases = len(all_bases)
    x_ratio = x_total / total_bases
    
    if 0.45 < x_ratio < 0.55:
        print("✓ Basis selection appears random (X/Y ratio close to 50/50)")
    else:
        print(f"⚠ Basis selection may be biased (X ratio: {x_ratio:.2%})")
    
    print()
    
    # Section 6: What's Missing
    print("❌ LIMITATIONS OF CURRENT IMPLEMENTATION")
    print("-" * 70)
    print("This simplified version does NOT include:")
    print("  1. True GHZ entanglement distribution between nodes")
    print("  2. Realistic quantum channel noise")
    print("  3. Eavesdropper (Eve) simulation")
    print("  4. Fidelity measurements")
    print("  5. Error rate vs. noise level analysis")
    print("  6. Comparison across different parameters")
    print()
    print("For a complete research project, you need:")
    print("  - Multiple experiments with varying noise levels")
    print("  - Eavesdropper detection experiments")
    print("  - Fidelity vs. success rate analysis")
    print("  - Comparison plots")
    print()
    
    return {
        'total_rounds': total_rounds,
        'valid_rounds': valid_rounds,
        'key_rate': key_rate,
        'correlation_accuracy': correlation_accuracy if len(correlations) > 0 else 0,
        'recovery_success_rate': recovery_rate
    }

def compare_experiments(experiment_files):
    """Compare multiple experiments"""
    
    print("\n")
    print("=" * 70)
    print("MULTI-EXPERIMENT COMPARISON")
    print("=" * 70)
    print()
    
    results = []
    for exp_file in experiment_files:
        exp_name = Path(exp_file).parent.name
        data = load_results(exp_file)
        
        # Quick analysis
        round_data = data[0]['round_result'][0]
        alice_data = round_data['app_alice']
        
        results.append({
            'name': exp_name,
            'key_rate': alice_data['key_rate'],
            'valid_rounds': alice_data['valid_rounds']
        })
    
    print(f"{'Experiment':<20} | Key Rate | Valid Rounds")
    print("-" * 70)
    for r in results:
        print(f"{r['name']:<20} | {r['key_rate']:7.2%} | {r['valid_rounds']:4d}/100")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python qss_analysis.py <results_file.json>")
        print("   or: python qss_analysis.py exp1/results.json exp2/results.json ...")
        sys.exit(1)
    
    # Analyze first experiment in detail
    results_file = sys.argv[1]
    print(f"\nAnalyzing: {results_file}\n")
    
    results_data = load_results(results_file)
    metrics = analyze_single_experiment(results_data)
    
    # If multiple experiments provided, compare them
    if len(sys.argv) > 2:
        compare_experiments(sys.argv[1:])
    
    print("=" * 70)
    print("Analysis complete!")
    print("=" * 70)
